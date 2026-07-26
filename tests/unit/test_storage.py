"""Proving the mount, writing durably to it, and the two preflight primitives.

The mount table is supplied as a fixture rather than read from `/proc`, which is
what lets a temporary directory stand in for the NFS archive without mounting
anything. One test deliberately does not substitute: the parser has to cope with
this host's actual `/proc` contents, because a parser that only agrees with a
line this repository wrote proves nothing.

A second-filesystem failure is exercised through `device_problems`, which takes
device numbers instead of paths, for the same reason `published_adoption_problems`
takes `os.stat_result` values: the policy is then testable for a filesystem this
host cannot mount.

Inspection and initialization are `tests/unit/test_archive.py`; the ordered
checks built on these primitives are `tests/unit/test_preflight.py`.
"""

import ast
import os
import shutil
import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hfcache.archive import initialize_archive
from hfcache.errors import (
    ConfigurationError,
    ExitCode,
    IntegrityError,
    RetentionError,
    SafetyError,
    SynchronizationError,
)
from hfcache.identity import ProbeId
from hfcache.models import ArchiveSentinel, Provenance
from hfcache.paths import ArchiveLayout
from hfcache.storage import (
    BYTES_PER_GIB,
    CapacityFacts,
    MountEntry,
    MountFacts,
    _exercise_writability,
    _remove_probe,
    atomic_write_bytes,
    capacity_problems,
    capacity_warnings,
    describe_capacity,
    describe_mount,
    device_problems,
    effective_reserve,
    fsync_directory,
    is_initialized,
    is_temporary_sibling,
    mount_problems,
    parse_mount_table,
    probe_directory_rename,
    probe_hardlink,
    probe_reference_replacement,
    probe_writability,
    publication_destinations,
    read_mount_table,
    same_filesystem_problems,
    temporary_sibling,
    write_model,
)
from hfcache.taxonomy import classify

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"

STORE_MODE = 0o700
PUBLISHED_MODE = 0o2750
SENTINEL_MODE = 0o640


def nfs_line(mount_point: str, *, filesystem: str = "nfs4", options: str = "rw") -> str:
    """One mountinfo line for `mount_point`, in the kernel's field order."""
    return (
        f"457 47 0:68 / {mount_point} {options},nosuid,nodev,relatime shared:488 "
        f"- {filesystem} nas.lab.cross.solutions:/mnt/tank/hf rw,vers=4.2"
    )


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    root = tmp_path / "archive"
    root.mkdir()
    return root


@pytest.fixture
def layout(archive_root: Path) -> ArchiveLayout:
    return ArchiveLayout(root=archive_root)


@pytest.fixture
def table(archive_root: Path) -> tuple[MountEntry, ...]:
    """A mount table in which the temporary archive root is an NFSv4 mount.

    Two entries, because that is what the writer really has: the systemd
    automount and the NFS mount stacked on top of it at the same path.
    """
    real = os.path.realpath(archive_root)
    return parse_mount_table(
        f"47 68 0:34 / {real} rw,relatime shared:43 - autofs systemd-1 rw,fd=51\n{nfs_line(real)}\n"
    )


def initialize(layout: ArchiveLayout, table: tuple[MountEntry, ...]):
    return initialize_archive(layout, archive_id=ARCHIVE_ID, table=table)


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


# --------------------------------------------------------------------------- #
# Parsing the mount table
# --------------------------------------------------------------------------- #


def test_a_mount_entry_is_parsed_into_its_documented_fields():
    (entry,) = parse_mount_table(nfs_line("/srv/hfcache"))

    assert str(entry.mount_point) == "/srv/hfcache"
    assert entry.filesystem_type == "nfs4"
    assert entry.source == "nas.lab.cross.solutions:/mnt/tank/hf"
    assert "nosuid" in entry.options
    assert "vers=4.2" in entry.super_options


def test_optional_fields_do_not_shift_the_filesystem_type():
    # The optional-field run between the options and the '-' is variable length;
    # a parser that counted fields instead of finding the separator would read
    # 'shared:488' as the filesystem type.
    without = parse_mount_table(
        "457 47 0:68 / /srv/hfcache rw - nfs4 nas:/export rw",
    )
    with_optional = parse_mount_table(
        "457 47 0:68 / /srv/hfcache rw shared:488 master:12 - nfs4 nas:/export rw",
    )

    assert without[0].filesystem_type == with_optional[0].filesystem_type == "nfs4"


def test_a_mount_point_containing_a_space_is_unescaped():
    (entry,) = parse_mount_table(nfs_line(r"/srv/hf\040cache"))

    assert str(entry.mount_point) == "/srv/hf cache"


@pytest.mark.parametrize(
    ("escaped", "expected"),
    [
        (r"/a\040b", "/a b"),
        (r"/a\011b", "/a\tb"),
        (r"/a\134b", "/a\\b"),
        (r"/a\999b", r"/a\999b"),
        (r"/trailing\13", r"/trailing\13"),
    ],
)
def test_every_documented_escape_is_decoded_and_nothing_else_is(escaped, expected):
    # An unrecognized escape is left alone rather than dropped: mangling a name
    # would make the mount-point comparison silently fail to match.
    (entry,) = parse_mount_table(nfs_line(escaped))

    assert str(entry.mount_point) == expected


def test_a_newline_escape_survives_the_line_split():
    # splitlines() would break a raw newline into two lines; the kernel escapes
    # it precisely so it does not.
    (entry,) = parse_mount_table(nfs_line(r"/srv/hf\012cache"))

    assert str(entry.mount_point) == "/srv/hf\ncache"


@pytest.mark.parametrize(
    "line",
    [
        "",
        "457 47 0:68 / /srv/hfcache rw",
        "457 47 0:68 / /srv/hfcache rw shared:488",
        "457 47 0:68 / /srv/hfcache rw - nfs4",
        "- - - - - - -",
    ],
)
def test_a_line_that_is_not_a_mount_entry_is_skipped_not_guessed_at(line):
    assert parse_mount_table(line) == ()


def test_super_options_may_be_absent():
    (entry,) = parse_mount_table("457 47 0:68 / /srv/hfcache rw - nfs4 nas:/export")

    assert entry.super_options == ()
    assert not entry.read_only


def test_reading_an_absent_mount_table_is_hfmnt003(tmp_path: Path):
    # Without the table the filesystem type is unknown, and an unknown type is
    # not NFS. Nothing may be written on that basis.
    with pytest.raises(SafetyError) as caught:
        read_mount_table(tmp_path / "no-such-mountinfo")

    assert codes(caught.value.problems) == ["HFMNT003"]
    assert caught.value.exit_code == ExitCode.SAFETY


def test_the_real_mount_table_parses():
    # Not a mock: the parser must cope with this host's actual /proc contents,
    # which is where the autofs/nfs4 stack and every option spelling come from.
    entries = read_mount_table()

    assert entries
    assert all(str(entry.mount_point).startswith("/") for entry in entries)


# --------------------------------------------------------------------------- #
# Describing the archive root
# --------------------------------------------------------------------------- #


def test_the_topmost_mount_wins_when_mounts_stack(archive_root: Path, table):
    # On the writer the NFS mount sits on top of the x-systemd.automount autofs
    # mount at the same path. A process sees the top one.
    facts = describe_mount(archive_root, table=table)

    assert facts.entry is not None
    assert facts.entry.filesystem_type == "nfs4"


def test_a_missing_root_is_reported_as_absent(tmp_path: Path, table):
    facts = describe_mount(tmp_path / "absent", table=table)

    assert not facts.exists
    assert codes(mount_problems(facts)) == ["HFMNT001"]


def test_a_symlinked_root_is_refused_without_being_followed(tmp_path: Path, archive_root, table):
    link = tmp_path / "link"
    link.symlink_to(archive_root)

    facts = describe_mount(link, table=table)

    assert facts.is_symlink
    assert not facts.is_directory
    assert codes(mount_problems(facts)) == ["HFMNT015"]


def test_a_root_that_is_a_regular_file_is_refused(tmp_path: Path, table):
    path = tmp_path / "file"
    path.write_text("", encoding="utf-8")

    assert codes(mount_problems(describe_mount(path, table=table))) == ["HFMNT015"]


def test_a_directory_that_is_not_a_mount_point_is_hfmnt002(archive_root: Path):
    facts = describe_mount(archive_root, table=())

    assert not facts.is_mount_point
    assert codes(mount_problems(facts)) == ["HFMNT002"]


def test_a_non_nfs_mount_is_hfmnt003(archive_root: Path):
    table = parse_mount_table(nfs_line(os.path.realpath(archive_root), filesystem="ext4"))

    assert codes(mount_problems(describe_mount(archive_root, table=table))) == ["HFMNT003"]


@pytest.mark.parametrize("filesystem", ["nfs", "nfs4"])
def test_both_nfs_flavours_are_accepted(archive_root: Path, filesystem):
    table = parse_mount_table(nfs_line(os.path.realpath(archive_root), filesystem=filesystem))

    assert mount_problems(describe_mount(archive_root, table=table)) == []


def test_a_read_only_mount_is_hfmnt004(archive_root: Path):
    table = parse_mount_table(nfs_line(os.path.realpath(archive_root), options="ro"))

    assert codes(mount_problems(describe_mount(archive_root, table=table))) == ["HFMNT004"]


def test_a_server_side_read_only_export_is_seen_in_the_superblock_options():
    # A read-only NFS export can present rw per-mount options and ro superblock
    # options. Reading only the first field would call it writable.
    (entry,) = parse_mount_table("457 47 0:68 / /srv/hfcache rw - nfs4 nas:/export ro,vers=4.2")

    assert entry.read_only


def test_both_ways_of_failing_are_reported_together(archive_root: Path):
    table = parse_mount_table(
        nfs_line(os.path.realpath(archive_root), filesystem="ext4", options="ro")
    )

    assert codes(mount_problems(describe_mount(archive_root, table=table))) == [
        "HFMNT003",
        "HFMNT004",
    ]


def test_describe_mount_reads_the_system_table_when_none_is_given(
    archive_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake = tmp_path / "mountinfo"
    fake.write_text(nfs_line(os.path.realpath(archive_root)), encoding="utf-8")
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", fake)

    assert describe_mount(archive_root).entry is not None


def test_mount_facts_render_for_the_envelope(archive_root: Path, table):
    payload = describe_mount(archive_root, table=table).as_payload()

    assert payload == {
        "exists": True,
        "filesystem_type": "nfs4",
        "is_mount_point": True,
        "read_only": False,
        "source": "nas.lab.cross.solutions:/mnt/tank/hf",
    }


def test_an_absent_root_renders_nulls_rather_than_omitting_keys(tmp_path: Path):
    payload = MountFacts(
        path=tmp_path, exists=False, is_directory=False, is_symlink=False, entry=None
    ).as_payload()

    assert payload["filesystem_type"] is None
    assert payload["read_only"] is None
    assert payload["source"] is None


# --------------------------------------------------------------------------- #
# Durable writes
# --------------------------------------------------------------------------- #


def test_a_temporary_sibling_stays_in_the_same_directory(tmp_path: Path):
    target = tmp_path / "nested" / "current.json"

    temporary = temporary_sibling(target)

    assert temporary.parent == target.parent
    assert temporary != target


def test_a_temporary_sibling_is_recognisable_as_ours(tmp_path: Path):
    assert is_temporary_sibling(temporary_sibling(tmp_path / ".hfcache-root").name)


@pytest.mark.parametrize(
    "name",
    [
        ".hfcache-root",
        ".tmp-0123456789abcdef",
        "current.json.tmp-0123456789abcde",
        "current.json.tmp-0123456789abcdeff",
        "current.json.tmp-0123456789ABCDEF",
        "current.json.tmp-0123456789abcdef\n",
    ],
)
def test_only_the_exact_temporary_grammar_is_recognised(name):
    # The last case is why the pattern is matched with fullmatch: an anchored
    # '$' would also match before a trailing newline, and a file whose name ends
    # in one is not a file this application wrote.
    assert not is_temporary_sibling(name)


def test_an_atomic_write_lands_with_its_content_and_mode(tmp_path: Path):
    target = tmp_path / "current.json"

    atomic_write_bytes(target, b"payload\n", mode=0o640)

    assert target.read_bytes() == b"payload\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640


def test_an_atomic_write_replaces_an_existing_file(tmp_path: Path):
    target = tmp_path / "current.json"
    target.write_bytes(b"old")

    atomic_write_bytes(target, b"new", mode=0o640)

    assert target.read_bytes() == b"new"


def test_an_atomic_write_leaves_no_temporary_behind(tmp_path: Path):
    atomic_write_bytes(tmp_path / "current.json", b"payload\n", mode=0o640)

    assert [path.name for path in tmp_path.iterdir()] == ["current.json"]


def test_the_mode_is_not_left_to_the_process_umask(tmp_path: Path):
    target = tmp_path / "sentinel"
    original = os.umask(0o077)
    try:
        atomic_write_bytes(target, b"x", mode=0o640)
    finally:
        os.umask(original)

    assert stat.S_IMODE(target.stat().st_mode) == 0o640


def test_a_failed_rename_removes_the_temporary_it_created(tmp_path: Path):
    # An interrupted durable write must not leave a partial file behind for the
    # next inspection to find and refuse.
    target = tmp_path / "current.json"
    target.mkdir()

    with pytest.raises(IsADirectoryError):
        atomic_write_bytes(target, b"payload", mode=0o640)

    assert [path.name for path in tmp_path.iterdir()] == ["current.json"]
    assert target.is_dir(), "the existing target is left exactly as it was"


def test_a_write_that_cannot_start_leaves_nothing_behind(tmp_path: Path):
    target = tmp_path / "absent-directory" / "current.json"

    with pytest.raises(FileNotFoundError):
        atomic_write_bytes(target, b"payload", mode=0o640)

    assert not target.parent.exists()


def test_fsync_of_a_directory_succeeds_on_this_filesystem(tmp_path: Path):
    # Publication durability depends on it: fsyncing a file makes its contents
    # durable, not the parent's reference to it.
    fsync_directory(tmp_path)


# --------------------------------------------------------------------------- #
# The writability probe
# --------------------------------------------------------------------------- #

PROBE_ID = ProbeId("0123456789abcdef")


@pytest.fixture
def initialized(layout: ArchiveLayout, table) -> ArchiveLayout:
    initialize(layout, table)
    return layout


def test_an_archive_is_initialized_exactly_when_its_sentinel_is_there(layout, table):
    # The sentinel is written last (`FS-23`), so its presence is what proves the
    # layout beneath it.
    assert not is_initialized(layout)

    initialize(layout, table)

    assert is_initialized(layout)


def test_a_probe_proves_create_fsync_rename_and_delete(initialized: ArchiveLayout):
    assert probe_writability(initialized) == []


def test_a_probe_removes_every_artifact_it_made(initialized: ArchiveLayout):
    probe_writability(initialized, probe_id=PROBE_ID)

    assert list(initialized.health.iterdir()) == []
    assert not initialized.probe(PROBE_ID).exists()


def test_a_probe_writes_under_the_documented_path(initialized: ArchiveLayout, monkeypatch):
    # `.store/health/probe-<probe-id>`, per `docs/architecture.md` §5.1. Captured
    # rather than inferred, because the directory is gone by the time the probe
    # returns.
    seen: list[Path] = []
    real = fsync_directory
    monkeypatch.setattr(
        "hfcache.storage.fsync_directory", lambda path: (seen.append(path), real(path))[1]
    )

    probe_writability(initialized, probe_id=PROBE_ID)

    assert initialized.probe(PROBE_ID) in seen
    assert str(initialized.archive_relative(initialized.probe(PROBE_ID))) == (
        f".store/health/probe-{PROBE_ID}"
    )


def test_a_probe_that_cannot_create_its_directory_is_hfmnt008(initialized: ArchiveLayout):
    initialized.health.chmod(0o500)
    try:
        problems = probe_writability(initialized)
    finally:
        initialized.health.chmod(0o700)

    assert codes(problems) == ["HFMNT008"]
    assert list(initialized.health.iterdir()) == []


def test_a_failed_probe_still_removes_what_it_made(
    initialized: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    # The requirement is "including after a failed probe": a leftover would be
    # found by the next inspection and refused as content nobody recognises.
    def refuse(path: Path, payload: bytes, *, mode: int) -> None:
        raise OSError(13, "Permission denied", str(path))

    monkeypatch.setattr("hfcache.storage.atomic_write_bytes", refuse)

    problems = probe_writability(initialized, probe_id=PROBE_ID)

    assert codes(problems) == ["HFMNT008"]
    assert list(initialized.health.iterdir()) == []


def test_a_probe_whose_bytes_do_not_come_back_is_hfmnt008(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # An export that accepts a write and holds something else is not writable in
    # any sense that matters. Injected, because no local filesystem does it.
    def lose_the_payload(path: Path, payload: bytes, *, mode: int) -> None:
        path.write_bytes(b"not what was written")

    directory = tmp_path / "probe"
    directory.mkdir()
    monkeypatch.setattr("hfcache.storage.atomic_write_bytes", lose_the_payload)

    problems = _exercise_writability(directory, "probe", "HFMNT008")

    assert codes(problems) == ["HFMNT008"]
    assert "read back" in problems[0].message


def test_a_probe_that_cannot_write_at_all_is_hfmnt008(tmp_path: Path):
    problems = _exercise_writability(tmp_path / "absent", "probe", "HFMNT008")

    assert codes(problems) == ["HFMNT008"]


def test_a_probe_area_is_removed_wholesale_including_its_subdirectories(tmp_path: Path):
    # The capability probes build directories inside the probe area, and the
    # area is named `probe-<16 random hex>` by this process moments earlier, so
    # it cannot hold anything the application did not put there.
    directory = tmp_path / "probe"
    (directory / "cache" / "nested").mkdir(parents=True)
    (directory / "cache" / "nested" / "blob").write_text("x", encoding="utf-8")

    assert _remove_probe(directory, "probe", "HFMNT008") == []
    assert not directory.exists()


def test_a_probe_area_that_cannot_be_removed_is_reported(tmp_path: Path):
    # An artifact left behind is what the next inspection would refuse, so a
    # failed cleanup is reported rather than passed over.
    directory = tmp_path / "probe"
    (directory / "nested").mkdir(parents=True)
    tmp_path.chmod(0o500)
    try:
        problems = _remove_probe(directory, "probe", "HFMNT008")
    finally:
        tmp_path.chmod(0o700)

    assert codes(problems) == ["HFMNT008"]


# --------------------------------------------------------------------------- #
# One filesystem (`FS-04`)
# --------------------------------------------------------------------------- #


def test_every_publication_destination_is_named(layout: ArchiveLayout):
    # A destination missing from this list is a destination the same-filesystem
    # proof never covers, so the list is asserted rather than assumed.
    assert set(publication_destinations(layout)) == {
        layout.published,
        layout.repos,
        layout.manifests,
        layout.catalog,
        layout.trash,
        layout.quarantine,
    }


def test_one_filesystem_is_no_problem():
    assert device_problems({"published": 64, ".store/staging": 64}, root_device=64) == []


def test_a_destination_on_another_filesystem_is_hfmnt009():
    problems = device_problems(
        {"published": 65, ".store/staging": 64, ".store/trash": 66}, root_device=64
    )

    assert codes(problems) == ["HFMNT009", "HFMNT009"]
    assert [problem.location for problem in problems] == [".store/trash", "published"]


def test_staging_and_every_destination_share_the_archive_filesystem(initialized: ArchiveLayout):
    assert same_filesystem_problems(initialized) == []


def test_a_destination_that_is_missing_is_hfmnt008(initialized: ArchiveLayout):
    initialized.trash.rmdir()

    problems = same_filesystem_problems(initialized)

    assert codes(problems) == ["HFMNT008"]
    assert problems[0].location == ".store/trash"


def test_an_archive_root_that_cannot_be_examined_is_hfmnt008(tmp_path: Path):
    problems = same_filesystem_problems(ArchiveLayout(root=tmp_path / "absent"))

    assert codes(problems) == ["HFMNT008"]


# --------------------------------------------------------------------------- #
# Capacity
# --------------------------------------------------------------------------- #

GIB = BYTES_PER_GIB


def statvfs_result(*, total_bytes: int, available_bytes: int, free_bytes: int | None = None):
    """A `statvfs` answer with only the fields `describe_capacity` reads set."""
    block = 4096
    free = available_bytes if free_bytes is None else free_bytes
    return os.statvfs_result(
        (
            block,
            block,
            total_bytes // block,
            free // block,
            available_bytes // block,
            0,
            0,
            0,
            0,
            255,
        )
    )


def facts(*, total: int, available: int) -> CapacityFacts:
    return CapacityFacts(path=Path("/srv/hfcache"), total_bytes=total, available_bytes=available)


def test_capacity_is_measured_from_the_filesystem(tmp_path: Path):
    measured = describe_capacity(tmp_path)

    assert measured.total_bytes > 0
    assert 0 <= measured.available_bytes <= measured.total_bytes


def test_available_space_is_what_this_identity_can_use_not_what_root_can(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # `f_bfree` includes the root-reserved portion and the writer is not root on
    # this filesystem, so reading it would overstate the headroom.
    def measured(_path):
        return statvfs_result(total_bytes=100 * GIB, available_bytes=20 * GIB, free_bytes=30 * GIB)

    monkeypatch.setattr("hfcache.storage.os.statvfs", measured)

    assert describe_capacity(tmp_path).available_bytes == 20 * GIB


def test_a_filesystem_that_cannot_be_measured_is_hfmnt008(tmp_path: Path):
    # Unknown capacity is a different statement from insufficient capacity, and
    # only the second one may be reported as `HFMNT011`.
    with pytest.raises(SafetyError) as caught:
        describe_capacity(tmp_path / "absent")

    assert codes(caught.value.problems) == ["HFMNT008"]


def test_capacity_facts_render_for_a_payload():
    assert facts(total=100, available=40).as_payload() == {
        "available_bytes": 40,
        "total_bytes": 100,
    }


@pytest.mark.parametrize(
    ("total", "gib", "percent", "expected"),
    [
        # The absolute floor binds on a small dataset...
        (200 * GIB, 100, 10, 100 * GIB),
        # ...and the proportional rule on a large one.
        (10_000 * GIB, 100, 10, 1_000 * GIB),
        # Either may be switched off alone.
        (200 * GIB, 0, 10, 20 * GIB),
        (200 * GIB, 100, 0, 100 * GIB),
        # Both off means no reserve at all, which is a choice an operator may make.
        (200 * GIB, 0, 0, 0),
    ],
)
def test_the_reserve_is_whichever_minimum_binds_harder(total, gib, percent, expected):
    assert effective_reserve(total, minimum_gib=gib, minimum_percent=percent) == expected


def test_capacity_above_the_reserve_is_no_problem():
    assert (
        capacity_problems(facts(total=100 * GIB, available=50 * GIB), reserve_bytes=10 * GIB) == []
    )


def test_capacity_below_the_reserve_is_hfmnt011():
    problems = capacity_problems(facts(total=100 * GIB, available=5 * GIB), reserve_bytes=10 * GIB)

    assert codes(problems) == ["HFMNT011"]
    assert problems[0].context["required_bytes"] == 10 * GIB


def test_the_need_is_counted_on_top_of_the_reserve():
    # Plan §19 item 9: free capacity must exceed the estimated download, plus the
    # publication bytes in copy mode, plus the reserve — not the largest of them.
    room = facts(total=100 * GIB, available=15 * GIB)

    assert capacity_problems(room, reserve_bytes=10 * GIB, needed_bytes=4 * GIB) == []
    assert codes(capacity_problems(room, reserve_bytes=10 * GIB, needed_bytes=6 * GIB)) == [
        "HFMNT011"
    ]


def test_exactly_meeting_the_requirement_is_not_a_failure():
    assert (
        capacity_problems(facts(total=100 * GIB, available=10 * GIB), reserve_bytes=10 * GIB) == []
    )


def test_ample_headroom_raises_no_warning():
    assert (
        capacity_warnings(facts(total=100 * GIB, available=50 * GIB), reserve_bytes=10 * GIB) == []
    )


def test_headroom_within_a_tenth_of_the_reserve_is_hfwrn005():
    # 10 GiB reserved, 10.5 GiB free: the run succeeds, and the operator should
    # hear about it before the one that does not.
    warnings = capacity_warnings(
        facts(total=100 * GIB, available=10 * GIB + GIB // 2), reserve_bytes=10 * GIB
    )

    assert codes(warnings) == ["HFWRN005"]
    assert warnings[0].context["headroom_bytes"] == GIB // 2


def test_a_reserve_of_zero_never_warns():
    # An operator who configured no reserve asked for no warning about it.
    assert capacity_warnings(facts(total=100 * GIB, available=0), reserve_bytes=0) == []


def test_the_warning_accounts_for_the_run_as_well_as_the_reserve():
    room = facts(total=100 * GIB, available=20 * GIB)

    assert capacity_warnings(room, reserve_bytes=10 * GIB) == []
    assert codes(capacity_warnings(room, reserve_bytes=10 * GIB, needed_bytes=10 * GIB)) == [
        "HFWRN005"
    ]


# --------------------------------------------------------------------------- #
# The capability probes (plan §14.2, `doctor` checks 9-11)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "probe",
    [probe_hardlink, probe_directory_rename, probe_reference_replacement],
)
def test_every_capability_is_proven_on_this_filesystem(initialized: ArchiveLayout, probe):
    assert probe(initialized) == []


@pytest.mark.parametrize(
    "probe",
    [probe_hardlink, probe_directory_rename, probe_reference_replacement],
)
def test_every_capability_probe_removes_what_it_made(initialized: ArchiveLayout, probe):
    probe(initialized, probe_id=PROBE_ID)

    assert list(initialized.health.iterdir()) == []


@pytest.mark.parametrize(
    ("probe", "code"),
    [
        (probe_hardlink, "HFMNT012"),
        (probe_directory_rename, "HFMNT013"),
        (probe_reference_replacement, "HFMNT013"),
    ],
)
def test_every_capability_probe_reports_its_documented_code(
    initialized: ArchiveLayout, monkeypatch: pytest.MonkeyPatch, probe, code
):
    # Injected rather than provoked: this host's filesystem supports all three,
    # which is the point of the probes but leaves no way to observe a failure.
    def refuse(*args, **kwargs):
        raise OSError(95, "Operation not supported")

    monkeypatch.setattr("hfcache.storage.atomic_write_bytes", refuse)

    assert codes(probe(initialized)) == [code]


def test_a_probe_directory_that_cannot_be_created_is_hfmnt008(initialized: ArchiveLayout):
    # Reported under `HFMNT008` whatever the probe was for: the archive is not
    # writable, which is a different finding from the capability being absent.
    initialized.health.chmod(0o500)
    try:
        problems = probe_hardlink(initialized)
    finally:
        initialized.health.chmod(0o700)

    assert codes(problems) == ["HFMNT008"]


def test_a_hardlink_that_is_really_a_copy_is_hfmnt012(
    initialized: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    # A destination with one link is a second inode, so publication would
    # silently consume twice the planned space.
    monkeypatch.setattr("hfcache.storage.os.link", shutil.copyfile)

    problems = probe_hardlink(initialized)

    assert codes(problems) == ["HFMNT012"]
    assert "twice the planned space" in problems[0].message


def test_a_rename_that_leaves_the_original_behind_is_hfmnt013(
    initialized: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    def copy_instead(self, target):
        shutil.copytree(self, target)

    monkeypatch.setattr(Path, "rename", copy_instead)

    problems = probe_directory_rename(initialized)

    assert codes(problems) == ["HFMNT013"]
    assert "wholesale" in problems[0].message


def test_a_hardlink_that_does_not_read_back_its_bytes_is_hfmnt012(
    initialized: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    # A "link" that is neither the same inode nor the same content fails both
    # halves of what check 9 proves, and both are reported.
    def diverge(source, destination):
        Path(destination).write_bytes(b"different bytes entirely")

    monkeypatch.setattr("hfcache.storage.os.link", diverge)

    problems = probe_hardlink(initialized)

    assert codes(problems) == ["HFMNT012", "HFMNT012"]
    assert "read back" in problems[1].message


def test_a_replacement_that_does_not_take_effect_is_hfmnt013(
    initialized: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    # A filesystem where the second write does not win would leave a consumer
    # reading the previous revision forever.
    def ignore_the_second(path, payload, *, mode):
        if not path.exists():
            path.write_bytes(payload)
            path.chmod(mode)

    monkeypatch.setattr("hfcache.storage.atomic_write_bytes", ignore_the_second)

    problems = probe_reference_replacement(initialized)

    assert codes(problems) == ["HFMNT013"]
    assert "new contents" in problems[0].message


def test_a_replacement_that_leaves_a_temporary_behind_is_hfmnt013(
    initialized: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    # The replacement is a rename over the original, so a surviving sibling means
    # the durable write is not what it claims to be.
    def leave_a_sibling(path, payload, *, mode):
        path.write_bytes(payload)
        path.chmod(mode)
        temporary_sibling(path).write_bytes(b"partial")

    monkeypatch.setattr("hfcache.storage.atomic_write_bytes", leave_a_sibling)

    problems = probe_reference_replacement(initialized)

    assert codes(problems) == ["HFMNT013"]
    assert "may survive it" in problems[0].message


# --------------------------------------------------------------------------- #
# `write_model` pairs its code with its error class (decision 52)
# --------------------------------------------------------------------------- #


def test_a_write_failure_raises_the_class_the_caller_paired_with_its_code(tmp_path: Path):
    directory = tmp_path / "read-only"
    directory.mkdir()
    directory.chmod(0o500)
    try:
        with pytest.raises(IntegrityError) as caught:
            write_model(
                directory / "report.json",
                _sentinel(),
                mode=0o600,
                code="HFVER007",
                error=IntegrityError,
            )
    finally:
        directory.chmod(0o700)
    assert caught.value.exit_code == classify("HFVER007") == ExitCode.INTEGRITY


def test_every_write_model_call_site_pairs_its_code_with_the_taxonomy(tmp_path: Path):
    """Scanned out of `src/`, so a new call site is checked the moment it lands.

    The exit an error carries comes from its class; the classification
    `docs/cli.md` §5 publishes comes from the code's family. A prune audit record
    written with `SafetyError` and an `HFRET` code would exit `20` for a
    condition the taxonomy calls `50`, which is the wrong instruction to a
    scheduler in the middle of an incident.
    """
    classes = {
        "ConfigurationError": ConfigurationError,
        "IntegrityError": IntegrityError,
        "RetentionError": RetentionError,
        "SafetyError": SafetyError,
        "SynchronizationError": SynchronizationError,
    }
    pairings: list[tuple[str, str, str]] = []
    for source in sorted(Path("src/hfcache").glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Name) and node.func.id == "write_model"):
                continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            code = keywords.get("code")
            if not isinstance(code, ast.Constant):
                continue
            error = keywords.get("error")
            name = error.id if isinstance(error, ast.Name) else "SafetyError"
            pairings.append((source.name, str(code.value), name))

    assert pairings, "no write_model call sites were found; the scan is broken"
    mismatched = [
        (where, code, name)
        for where, code, name in pairings
        if classes[name].exit_code != classify(code)
    ]
    assert mismatched == []


def _sentinel() -> ArchiveSentinel:
    """Any small durable model; what is under test is the failure, not the shape."""
    return ArchiveSentinel(
        archive_id=ARCHIVE_ID,
        created_at=datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC),
        created_by=Provenance(application_version="0.1.0", hostname="writer.example"),
    )
