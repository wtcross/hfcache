"""Mount proof, durable writes, and the one command that creates an archive.

`archive init` is irreversible and runs against the live NAS exactly once, so
almost every test here is about a *refusal*: what the command declines to touch,
and why. The mount table is supplied as a fixture rather than read from `/proc`,
which is what lets a temporary directory stand in for the NFS archive without
mounting anything.

Ownership rules are exercised through `published_adoption_problems`, which takes
`os.stat_result` values instead of paths. That is deliberate: the Mapall export
presents NAS-side ids that this host has no account for and `tyler` cannot
`chown` to, so the policy is tested for identities the test process could never
create on disk.
"""

import json
import os
import stat
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from hfcache.errors import ExitCode, SafetyError
from hfcache.identity import ProbeId
from hfcache.models import SCHEMA_VERSION, ArchiveSentinel, Provenance, dump
from hfcache.paths import ArchiveLayout
from hfcache.storage import (
    MountEntry,
    MountFacts,
    _exercise_probe,
    _remove_probe,
    atomic_write_bytes,
    describe_mount,
    device_problems,
    fsync_directory,
    initialize_archive,
    inspect_archive,
    is_initialized,
    is_temporary_sibling,
    mount_problems,
    parse_mount_table,
    probe_writability,
    publication_destinations,
    published_adoption_problems,
    read_mount_table,
    same_filesystem_problems,
    temporary_sibling,
)

if TYPE_CHECKING:
    from pathlib import Path

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
OTHER_ARCHIVE_ID = "11111111-2222-3333-4444-555555555555"

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


def inspect(layout: ArchiveLayout, table: tuple[MountEntry, ...], *, archive_id: str = ARCHIVE_ID):
    return inspect_archive(layout, archive_id=archive_id, table=table)


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

    problems = _exercise_probe(directory, "probe")

    assert codes(problems) == ["HFMNT008"]
    assert "read back" in problems[0].message


def test_a_probe_that_cannot_write_at_all_is_hfmnt008(tmp_path: Path):
    problems = _exercise_probe(tmp_path / "absent", "probe")

    assert codes(problems) == ["HFMNT008"]


def test_an_artifact_the_probe_cannot_remove_is_reported_not_ignored(tmp_path: Path):
    # A probe creates files only. Anything else there is reported rather than
    # removed, which keeps the one deletion this command performs inside `FS-19`.
    directory = tmp_path / "probe"
    (directory / "not-a-probe-file").mkdir(parents=True)

    problems = _remove_probe(directory, "probe")

    assert codes(problems) == ["HFMNT008"]
    assert directory.is_dir(), "nothing unrecognized is removed to make the probe tidy"


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
# Adopting a pre-existing published/
# --------------------------------------------------------------------------- #


def status(mode: int, uid: int, gid: int) -> os.stat_result:
    """A stat result carrying only the fields the adoption rule reads."""
    return os.stat_result((stat.S_IFDIR | mode, 1, 1, 1, uid, gid, 0, 0, 0, 0))


def test_published_is_adopted_when_owner_and_mode_already_match():
    root = status(0o750, 3001, 3002)
    published = status(PUBLISHED_MODE, 3001, 3002)

    assert published_adoption_problems(root, published, mode=PUBLISHED_MODE, location="p") == []


def test_a_wrongly_moded_published_is_refused_rather_than_fixed():
    root = status(0o750, 3001, 3002)
    published = status(0o755, 3001, 3002)

    problems = published_adoption_problems(root, published, mode=PUBLISHED_MODE, location="p")

    assert codes(problems) == ["HFMNT014"]
    assert "2750" in problems[0].message


def test_ownership_is_compared_against_the_root_not_against_a_local_uid():
    # Under the Mapall writer export both carry NAS-side ids with no local
    # account, so "the same identity owns both" is the only checkable form of
    # the ownership rule (`docs/plan.md` §35.3).
    root = status(0o750, 3001, 3002)

    assert (
        published_adoption_problems(
            root, status(PUBLISHED_MODE, 3001, 3002), mode=0o2750, location="p"
        )
        == []
    )
    assert codes(
        published_adoption_problems(
            root, status(PUBLISHED_MODE, 0, 3002), mode=0o2750, location="p"
        )
    ) == ["HFMNT014"]
    assert codes(
        published_adoption_problems(
            root, status(PUBLISHED_MODE, 3001, 0), mode=0o2750, location="p"
        )
    ) == ["HFMNT014"]


def test_both_adoption_failures_are_reported_at_once():
    problems = published_adoption_problems(
        status(0o750, 3001, 3002), status(0o755, 0, 0), mode=PUBLISHED_MODE, location="p"
    )

    assert codes(problems) == ["HFMNT014", "HFMNT014"]


# --------------------------------------------------------------------------- #
# Inspection
# --------------------------------------------------------------------------- #


def test_an_empty_mounted_root_is_uninitialized_and_initializable(layout, table):
    inspection = inspect(layout, table)

    assert inspection.state == "uninitialized"
    assert inspection.initializable
    assert inspection.problems == ()
    assert inspection.existing_directories == ()
    assert ".store/hub" in inspection.missing_directories


def test_a_pre_existing_empty_published_is_adopted(layout, table):
    layout.published.mkdir()
    layout.published.chmod(PUBLISHED_MODE)

    inspection = inspect(layout, table)

    assert inspection.state == "uninitialized", "TrueNAS creating it is not work we started"
    assert inspection.adopted_published
    assert inspection.existing_directories == ("published",)
    assert inspection.problems == ()


def test_a_non_empty_published_is_refused(layout, table):
    layout.published.mkdir()
    layout.published.chmod(PUBLISHED_MODE)
    (layout.published / "somebody-elses-data").write_text("x", encoding="utf-8")

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT014"]
    assert inspection.unknown_entries == ("published/somebody-elses-data",)


def test_a_wrongly_moded_published_makes_the_target_unusable(layout, table):
    layout.published.mkdir()
    layout.published.chmod(0o755)

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT014"]


def test_unknown_content_refuses_initialization_and_is_never_removed(layout, table):
    stranger = layout.root / "somebody-elses-file"
    stranger.write_text("keep me", encoding="utf-8")

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT014"]
    assert stranger.read_text(encoding="utf-8") == "keep me"


def test_an_unknown_directory_is_reported_but_not_descended(layout, table):
    populated = layout.root / "someones-home"
    (populated / "deep" / "deeper").mkdir(parents=True)
    for index in range(50):
        (populated / f"file-{index}").write_text("x", encoding="utf-8")

    inspection = inspect(layout, table)

    assert inspection.unknown_entries == ("someones-home",)
    assert inspection.unknown_entry_count == 1


def test_the_enumeration_of_unknown_entries_is_bounded_but_the_count_is_exact(layout, table):
    for index in range(40):
        (layout.root / f"file-{index:02d}").write_text("x", encoding="utf-8")

    inspection = inspect(layout, table)

    assert inspection.unknown_entry_count == 40
    assert len(inspection.unknown_entries) == 20
    assert inspection.unknown_entries == tuple(f"file-{index:02d}" for index in range(20))


def test_a_symlink_anywhere_in_the_layout_is_refused(layout, table, tmp_path: Path):
    (layout.root / "link").symlink_to(tmp_path)

    inspection = inspect(layout, table)

    assert codes(inspection.problems) == ["HFMNT015"]


def test_a_symlink_inside_a_layout_directory_is_refused(layout, table, tmp_path: Path):
    layout.store.mkdir()
    layout.store.chmod(STORE_MODE)
    (layout.store / "hub").symlink_to(tmp_path)

    inspection = inspect(layout, table)

    assert codes(inspection.problems) == ["HFMNT015"]
    assert inspection.problems[0].location == ".store/hub"


def test_a_partial_layout_without_a_sentinel_is_retryable(layout, table):
    layout.store.mkdir()
    layout.store.chmod(STORE_MODE)
    layout.staging.mkdir()
    layout.staging.chmod(STORE_MODE)

    inspection = inspect(layout, table)

    assert inspection.state == "partially_initialized"
    assert inspection.initializable
    assert inspection.problems == ()
    assert inspection.existing_directories == (".store", ".store/staging")


def test_a_leftover_sentinel_temporary_is_part_of_the_known_layout(layout, table):
    leftover = temporary_sibling(layout.sentinel)
    leftover.write_bytes(b"half a sentinel")

    inspection = inspect(layout, table)

    assert inspection.problems == ()
    assert inspection.leftover_temporaries == (leftover.name,)
    assert inspection.unknown_entry_count == 0


def test_a_directory_named_like_a_temporary_is_still_unknown(layout, table):
    temporary_sibling(layout.sentinel).mkdir()

    inspection = inspect(layout, table)

    assert codes(inspection.problems) == ["HFMNT014"]


def test_an_unreadable_layout_directory_is_reported(layout, table):
    layout.store.mkdir()
    layout.store.chmod(0o000)
    try:
        inspection = inspect(layout, table)
    finally:
        layout.store.chmod(STORE_MODE)

    assert codes(inspection.problems) == ["HFMNT008"]


def test_an_unusable_mount_stops_before_the_tree_is_walked(layout):
    (layout.root / "unknown").write_text("x", encoding="utf-8")

    inspection = inspect(layout, ())

    assert codes(inspection.problems) == ["HFMNT002"]
    assert inspection.unknown_entries == (), "nothing is claimed about a tree that was not read"


def test_a_full_layout_with_a_matching_sentinel_is_initialized(layout, table):
    initialize(layout, table)

    inspection = inspect(layout, table)

    assert inspection.state == "initialized"
    assert not inspection.initializable
    assert inspection.problems == ()
    assert inspection.sentinel is not None
    assert inspection.sentinel.archive_id == ARCHIVE_ID


def test_a_sentinel_that_disagrees_with_configuration_is_hfmnt007(layout, table):
    initialize(layout, table)

    inspection = inspect(layout, table, archive_id=OTHER_ARCHIVE_ID)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT007"]


def test_a_malformed_sentinel_is_hfmnt006(layout, table):
    initialize(layout, table)
    layout.sentinel.write_text("{ not json", encoding="utf-8")

    with pytest.raises(SafetyError) as caught:
        inspect(layout, table)

    assert codes(caught.value.problems) == ["HFMNT006"]


def test_a_sentinel_from_a_newer_release_is_refused_rather_than_read(layout, table):
    initialize(layout, table)
    payload = json.loads(layout.sentinel.read_text(encoding="utf-8"))
    payload["schema_version"] = SCHEMA_VERSION + 1
    layout.sentinel.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SafetyError) as caught:
        inspect(layout, table)

    assert codes(caught.value.problems) == ["HFMNT006"]
    assert "newer" in caught.value.problems[0].message


def test_an_unreadable_sentinel_is_hfmnt006(layout, table):
    initialize(layout, table)
    layout.sentinel.chmod(0o000)
    try:
        with pytest.raises(SafetyError) as caught:
            inspect(layout, table)
    finally:
        layout.sentinel.chmod(SENTINEL_MODE)

    assert codes(caught.value.problems) == ["HFMNT006"]


def test_a_sentinel_without_the_layout_beneath_it_is_hfmnt008(layout, table):
    # The sentinel is written last (`FS-23`), so this combination cannot come
    # from initialization and must not be treated as a healthy archive.
    sentinel = ArchiveSentinel(
        archive_id=ARCHIVE_ID,
        created_at=datetime(2026, 7, 25, tzinfo=UTC),
        created_by=Provenance(application_version="0.1.0", hostname="writer"),
    )
    atomic_write_bytes(layout.sentinel, dump(sentinel), mode=SENTINEL_MODE)

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT008"]


def test_an_inspection_renders_for_the_envelope(layout, table):
    payload = inspect(layout, table).as_payload()

    assert set(payload) == {
        "adopted_published",
        "archive_id",
        "archive_root",
        "existing_directories",
        "initializable",
        "leftover_temporaries",
        "missing_directories",
        "mount",
        "state",
        "unknown_entries",
        "unknown_entry_count",
    }
    assert payload["archive_id"] is None, "no sentinel means no archive id to report"
    assert payload["archive_root"] == str(layout.root)


def test_generated_arrays_are_sorted(layout, table):
    payload = inspect(layout, table).as_payload()

    assert payload["missing_directories"] == sorted(payload["missing_directories"])


def test_inspection_reads_the_system_mount_table_when_none_is_given(
    layout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake = tmp_path / "mountinfo"
    fake.write_text(nfs_line(os.path.realpath(layout.root)), encoding="utf-8")
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", fake)

    assert inspect_archive(layout, archive_id=ARCHIVE_ID).state == "uninitialized"


# --------------------------------------------------------------------------- #
# Initialization
# --------------------------------------------------------------------------- #


def test_initialization_creates_the_whole_layout(layout, table):
    result = initialize(layout, table)

    for spec in layout.required_directories():
        assert spec.path.is_dir()
    assert len(result.created_directories) == len(layout.required_directories())


def test_every_directory_gets_the_mode_section_5_2_requires(layout, table):
    initialize(layout, table)

    for spec in layout.required_directories():
        assert stat.S_IMODE(spec.path.stat().st_mode) == spec.mode, spec.path


def test_the_published_subtree_is_setgid_and_group_traversable(layout, table):
    initialize(layout, table)

    for path in (layout.published, layout.repos, layout.manifests, layout.catalog):
        assert stat.S_IMODE(path.stat().st_mode) == PUBLISHED_MODE


def test_private_areas_are_not_group_readable(layout, table):
    initialize(layout, table)

    for path in (layout.store, layout.audit, layout.runs, layout.hub_cache):
        assert stat.S_IMODE(path.stat().st_mode) == STORE_MODE


def test_the_umask_does_not_reach_the_created_modes(layout, table):
    original = os.umask(0o077)
    try:
        initialize(layout, table)
    finally:
        os.umask(original)

    assert stat.S_IMODE(layout.published.stat().st_mode) == PUBLISHED_MODE


def test_the_sentinel_is_written_with_the_configured_archive_id(layout, table):
    result = initialize(layout, table)

    written = json.loads(layout.sentinel.read_text(encoding="utf-8"))
    assert written["archive_id"] == ARCHIVE_ID == result.sentinel.archive_id
    assert written["layout_version"] == 1
    assert written["schema_version"] == SCHEMA_VERSION


def test_the_sentinel_records_which_build_created_the_archive(layout, table):
    result = initialize(layout, table)

    assert result.sentinel.created_by.application_version
    assert result.sentinel.created_by.hostname


def test_the_sentinel_is_readable_to_the_group_and_writable_only_by_the_writer(layout, table):
    initialize(layout, table)

    assert stat.S_IMODE(layout.sentinel.stat().st_mode) == SENTINEL_MODE


def test_initialization_adopts_a_pre_existing_published(layout, table):
    layout.published.mkdir()
    layout.published.chmod(PUBLISHED_MODE)

    result = initialize(layout, table)

    assert result.adopted_published
    assert "published" not in result.created_directories
    assert layout.repos.is_dir()


def test_initialization_completes_a_partial_layout(layout, table):
    layout.store.mkdir()
    layout.store.chmod(STORE_MODE)

    result = initialize(layout, table)

    assert ".store" not in result.created_directories
    assert ".store/hub" in result.created_directories
    assert inspect(layout, table).state == "initialized"


def test_a_partial_directory_with_the_wrong_mode_is_corrected_on_retry(layout, table):
    # A crash between mkdir and chmod leaves a directory of ours at the umask's
    # mode. It is application-owned and empty, so a retry restates the mode.
    layout.store.mkdir(mode=0o755)
    layout.store.chmod(0o755)

    initialize(layout, table)

    assert stat.S_IMODE(layout.store.stat().st_mode) == STORE_MODE


def test_a_leftover_sentinel_temporary_is_removed_by_the_retry(layout, table):
    leftover = temporary_sibling(layout.sentinel)
    leftover.write_bytes(b"half a sentinel")

    result = initialize(layout, table)

    assert result.removed_temporaries == (leftover.name,)
    assert not leftover.exists()
    assert layout.sentinel.is_file()


def test_initializing_twice_is_refused(layout, table):
    initialize(layout, table)

    with pytest.raises(SafetyError) as caught:
        initialize(layout, table)

    assert codes(caught.value.problems) == ["HFMNT014"]


def test_initialization_re_inspects_rather_than_trusting_a_caller(layout, table):
    (layout.root / "appeared-after-the-report").write_text("x", encoding="utf-8")

    with pytest.raises(SafetyError) as caught:
        initialize(layout, table)

    assert codes(caught.value.problems) == ["HFMNT014"]


def test_a_write_that_fails_after_every_check_passed_is_a_coded_failure(layout, table):
    # Every check reads; a server-side read-only export, a reached quota, or the
    # NAS going away are all only discovered by writing. That must be exit `20`
    # with a code, not a traceback out of the middle of the layout.
    layout.root.chmod(0o500)
    try:
        with pytest.raises(SafetyError) as caught:
            initialize(layout, table)
    finally:
        layout.root.chmod(0o750)

    assert codes(caught.value.problems) == ["HFMNT008"]
    assert "--inspect" in caught.value.problems[0].message


def test_a_half_finished_attempt_is_still_recognised_as_retryable(layout, table):
    layout.root.chmod(0o500)
    try:
        with pytest.raises(SafetyError):
            initialize(layout, table)
    finally:
        layout.root.chmod(0o750)

    assert inspect(layout, table).initializable
    assert initialize(layout, table).sentinel.archive_id == ARCHIVE_ID


def test_nothing_is_created_when_the_mount_is_wrong(layout):
    with pytest.raises(SafetyError) as caught:
        initialize_archive(layout, archive_id=ARCHIVE_ID, table=())

    assert codes(caught.value.problems) == ["HFMNT002"]
    assert list(layout.root.iterdir()) == []


def test_the_result_renders_for_the_envelope(layout, table):
    payload = initialize(layout, table).as_payload()

    assert set(payload) == {
        "adopted_published",
        "archive_id",
        "archive_root",
        "created_directories",
        "removed_temporaries",
        "sentinel",
    }
    assert payload["sentinel"] == ".hfcache-root"
    assert payload["created_directories"] == sorted(payload["created_directories"])
