"""Inspecting a target, and creating an archive on it exactly once.

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

The `archive init` *command* — its options, its envelope, and the `--confirm`
gate — is `tests/unit/test_archive_init.py`.
"""

import json
import os
import stat
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from hfcache.archive import (
    initialize_archive,
    inspect_archive,
    published_adoption_problems,
)
from hfcache.errors import SafetyError
from hfcache.models import SCHEMA_VERSION, ArchiveSentinel, Provenance, dump
from hfcache.paths import ArchiveLayout
from hfcache.storage import MountEntry, atomic_write_bytes, parse_mount_table, temporary_sibling

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
