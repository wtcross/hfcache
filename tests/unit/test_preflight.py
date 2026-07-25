"""The ordered checks, and the gate a mutating command has to get through.

Two properties are what this file exists for.

The first is that the check table is not restated anywhere. `docs/cli.md` §2 is
normative about the names, the order, and which checks write, so the table is
parsed out of the document and asserted against `CHECK_ORDER` in both
directions — the same technique `test_taxonomy.py` uses on the error taxonomy,
and for the same reason: a table in a document and a tuple in a module drift the
moment someone edits one.

The second is that one runner serves two callers with different rules. `doctor`
reports a skipped check and still exits `0`; the gate refuses, because a command
that is about to write may not assume a check would have passed. Both behaviours
are asserted here against the same runner.

The mount table is a fixture rather than `/proc`, which is what lets a temporary
directory stand in for the NFS archive without mounting anything.
"""

import inspect
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from hfcache.archive import initialize_archive
from hfcache.errors import ExitCode, SafetyError
from hfcache.paths import ArchiveLayout
from hfcache.preflight import (
    CHECK_ORDER,
    NOT_INITIALIZED,
    READ_ONLY,
    UNPROVABLE_READ_ONLY,
    Check,
    order_checks,
    require_storage_safety,
    storage_checks,
)
from hfcache.storage import MountEntry, parse_mount_table

if TYPE_CHECKING:
    from hfcache.errors import Problem

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
OTHER_ARCHIVE_ID = "11111111-2222-3333-4444-555555555555"

CLI_DOCUMENT = Path(__file__).resolve().parents[2] / "docs" / "cli.md"

TABLE_HEADER = "| # | `name` | Proves | Writes | Code on failure |"

_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*`(\w+)`\s*\|")


def nfs_line(mount_point: str, *, filesystem: str = "nfs4", options: str = "rw") -> str:
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
    return parse_mount_table(nfs_line(os.path.realpath(archive_root)))


@pytest.fixture
def initialized(layout: ArchiveLayout, table) -> ArchiveLayout:
    initialize_archive(layout, archive_id=ARCHIVE_ID, table=table)
    return layout


def named(checks) -> dict[str, Check]:
    return {check.name: check for check in checks}


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


def gate_problems(layout: ArchiveLayout, table) -> tuple[Problem, ...]:
    with pytest.raises(SafetyError) as caught:
        require_storage_safety(layout, archive_id=ARCHIVE_ID, table=table)
    return caught.value.problems


# --------------------------------------------------------------------------- #
# The check table is the document's
# --------------------------------------------------------------------------- #


def documented_rows() -> list[tuple[int, str, bool]]:
    """Parse `docs/cli.md` §2's `doctor` table into (number, name, writes)."""
    lines = CLI_DOCUMENT.read_text(encoding="utf-8").splitlines()
    start = lines.index(TABLE_HEADER) + 2
    rows: list[tuple[int, str, bool]] = []
    for line in lines[start:]:
        matched = _ROW.match(line)
        if matched is None:
            break
        cells = [cell.strip() for cell in line.split("|")]
        rows.append((int(matched.group(1)), matched.group(2), cells[4] == "**yes**"))
    return rows


def test_the_documented_table_was_found_and_is_completely_numbered():
    rows = documented_rows()

    assert len(rows) == 17
    assert [number for number, _, _ in rows] == list(range(1, len(rows) + 1))


def test_check_order_is_the_documented_order():
    # Names and sequence are both contract: automation keys on them and `status`
    # quotes them.
    assert [name for _, name, _ in documented_rows()] == list(CHECK_ORDER)


def test_read_only_skips_exactly_the_checks_the_table_marks_as_writing():
    assert tuple(name for _, name, writes in documented_rows() if writes) == UNPROVABLE_READ_ONLY


# --------------------------------------------------------------------------- #
# Ordering
# --------------------------------------------------------------------------- #


def test_checks_are_emitted_in_table_order_whatever_order_they_were_built_in():
    # `credential` and `hub_endpoint` were implemented first and belong at
    # positions 13 and 14; nothing had to move when the storage checks landed
    # between them.
    shuffled = [
        Check.passed("hub_endpoint", ""),
        Check.passed("archive_root", ""),
        Check.passed("credential", ""),
        Check.passed("configuration", ""),
    ]

    assert [check.name for check in order_checks(shuffled)] == [
        "configuration",
        "archive_root",
        "credential",
        "hub_endpoint",
    ]


def test_a_check_renders_in_the_documented_entry_shape():
    entry = Check.passed("archive_root", "/srv/hfcache exists").as_entry()

    assert entry == {
        "detail": "/srv/hfcache exists",
        "name": "archive_root",
        "outcome": "pass",
    }


def test_a_failed_check_reports_its_problems_as_its_detail(layout: ArchiveLayout):
    # The human table and the envelope's `errors` array then say the same thing
    # rather than two things.
    failed = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=()))["mount_point"]

    assert failed.outcome == "fail"
    assert failed.detail == "; ".join(problem.message for problem in failed.problems)


# --------------------------------------------------------------------------- #
# The mount checks (`docs/cli.md` §2 rows 2-5)
# --------------------------------------------------------------------------- #


def test_a_healthy_mount_passes_every_check_that_only_reads(layout: ArchiveLayout, table):
    checks = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=table))

    for name in ("archive_root", "mount_point", "filesystem_type", "mount_writable"):
        assert checks[name].outcome == "pass", name
    assert "nfs4" in checks["filesystem_type"].detail


def test_an_absent_root_fails_the_first_check_and_skips_the_rest(tmp_path: Path, table):
    checks = named(
        storage_checks(ArchiveLayout(root=tmp_path / "absent"), archive_id=ARCHIVE_ID, table=table)
    )

    assert codes(checks["archive_root"].problems) == ["HFMNT001"]
    for name in ("mount_point", "filesystem_type", "mount_writable"):
        assert checks[name].outcome == "skipped", name


def test_a_symlinked_root_fails_the_root_check_without_being_followed(
    tmp_path: Path, archive_root: Path, table
):
    link = tmp_path / "link"
    link.symlink_to(archive_root)

    checks = named(storage_checks(ArchiveLayout(root=link), archive_id=ARCHIVE_ID, table=table))

    assert codes(checks["archive_root"].problems) == ["HFMNT015"]


def test_a_directory_that_is_not_a_mount_point_fails_only_that_check(layout: ArchiveLayout):
    checks = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=()))

    assert checks["archive_root"].outcome == "pass"
    assert codes(checks["mount_point"].problems) == ["HFMNT002"]
    assert checks["filesystem_type"].outcome == "skipped"
    assert checks["mount_writable"].outcome == "skipped"


def test_a_non_nfs_mount_fails_only_the_type_check(archive_root: Path, layout: ArchiveLayout):
    table = parse_mount_table(nfs_line(os.path.realpath(archive_root), filesystem="ext4"))

    checks = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=table))

    assert codes(checks["filesystem_type"].problems) == ["HFMNT003"]
    assert checks["mount_writable"].outcome == "pass"


def test_a_read_only_mount_fails_only_the_writable_check(archive_root: Path, layout: ArchiveLayout):
    table = parse_mount_table(nfs_line(os.path.realpath(archive_root), options="ro"))

    checks = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=table))

    assert checks["filesystem_type"].outcome == "pass"
    assert codes(checks["mount_writable"].problems) == ["HFMNT004"]


def test_both_mount_failures_are_reported_as_their_own_checks(
    archive_root: Path, layout: ArchiveLayout
):
    table = parse_mount_table(
        nfs_line(os.path.realpath(archive_root), filesystem="ext4", options="ro")
    )

    checks = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=table))

    assert codes(checks["filesystem_type"].problems) == ["HFMNT003"]
    assert codes(checks["mount_writable"].problems) == ["HFMNT004"]


# --------------------------------------------------------------------------- #
# The sentinel (row 6)
# --------------------------------------------------------------------------- #


def test_a_matching_sentinel_passes_and_names_the_archive(initialized, table):
    check = named(storage_checks(initialized, archive_id=ARCHIVE_ID, table=table))["sentinel"]

    assert check.outcome == "pass"
    assert ARCHIVE_ID in check.detail


def test_a_sentinel_that_disagrees_with_configuration_is_hfmnt007(initialized, table):
    # `FS-03`: never repaired, never regenerated, never ignored.
    checks = named(storage_checks(initialized, archive_id=OTHER_ARCHIVE_ID, table=table))

    assert codes(checks["sentinel"].problems) == ["HFMNT007"]


def test_a_malformed_sentinel_is_hfmnt006(initialized, table):
    initialized.sentinel.write_text("{ not json", encoding="utf-8")

    checks = named(storage_checks(initialized, archive_id=ARCHIVE_ID, table=table))

    assert codes(checks["sentinel"].problems) == ["HFMNT006"]


def test_an_unreadable_sentinel_is_hfmnt006(initialized, table):
    initialized.sentinel.chmod(0o000)
    try:
        checks = named(storage_checks(initialized, archive_id=ARCHIVE_ID, table=table))
    finally:
        initialized.sentinel.chmod(0o640)

    assert codes(checks["sentinel"].problems) == ["HFMNT006"]


def test_a_bad_sentinel_does_not_stop_the_checks_below_it(initialized, table):
    # The report is a record of what was proven. A sentinel naming a different
    # archive says nothing about whether this mount is writable.
    checks = named(storage_checks(initialized, archive_id=OTHER_ARCHIVE_ID, table=table))

    assert checks["directory_writability"].outcome == "pass"
    assert checks["staging_filesystem"].outcome == "pass"


def test_the_gate_refuses_a_sentinel_that_names_another_archive(initialized, table):
    with pytest.raises(SafetyError) as caught:
        require_storage_safety(initialized, archive_id=OTHER_ARCHIVE_ID, table=table)

    assert codes(caught.value.problems) == ["HFMNT007"]


# --------------------------------------------------------------------------- #
# Writability and one filesystem (rows 7 and 8)
# --------------------------------------------------------------------------- #


def test_an_initialized_archive_proves_writability_and_one_filesystem(initialized, table):
    checks = named(storage_checks(initialized, archive_id=ARCHIVE_ID, table=table))

    assert checks["directory_writability"].outcome == "pass"
    assert checks["staging_filesystem"].outcome == "pass"
    assert list(initialized.health.iterdir()) == [], "no probe artifact survives the check"


def test_an_uninitialized_archive_reports_that_as_the_skip_reason(layout: ArchiveLayout, table):
    checks = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=table))

    for name in ("sentinel", "directory_writability", "staging_filesystem"):
        assert checks[name].outcome == "skipped"
        assert checks[name].detail == NOT_INITIALIZED


def test_only_the_sentinel_check_holds_an_uninitialized_archive_against_a_writer(
    layout: ArchiveLayout, table
):
    # One missing archive is one problem. The checks below the sentinel skip on
    # the same condition without reporting it a second and third time.
    checks = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=table))

    assert checks["sentinel"].blocking_code == "HFMNT005"
    assert checks["directory_writability"].blocking_code is None
    assert checks["staging_filesystem"].blocking_code is None


def test_read_only_skips_the_probe_and_says_so(initialized, table):
    checks = named(storage_checks(initialized, archive_id=ARCHIVE_ID, read_only=True, table=table))

    assert checks["directory_writability"].outcome == "skipped"
    assert checks["directory_writability"].detail == READ_ONLY
    assert list(initialized.health.iterdir()) == []


def test_read_only_still_proves_the_check_that_only_stats(initialized, table):
    checks = named(storage_checks(initialized, archive_id=ARCHIVE_ID, read_only=True, table=table))

    assert checks["staging_filesystem"].outcome == "pass"


def test_nothing_is_written_to_a_mount_that_was_not_proven(layout: ArchiveLayout):
    # The probe writes. It must never write to a target that failed the checks
    # whose whole purpose is to establish that it is the archive.
    checks = named(storage_checks(layout, archive_id=ARCHIVE_ID, table=()))

    assert checks["sentinel"].outcome == "skipped"
    assert checks["directory_writability"].outcome == "skipped"
    assert checks["staging_filesystem"].outcome == "skipped"
    assert list(layout.root.iterdir()) == []


def test_a_probe_that_fails_is_reported_as_a_failed_check(initialized, table):
    initialized.health.chmod(0o500)
    try:
        checks = named(storage_checks(initialized, archive_id=ARCHIVE_ID, table=table))
    finally:
        initialized.health.chmod(0o700)

    assert codes(checks["directory_writability"].problems) == ["HFMNT008"]


def test_a_missing_destination_is_reported_as_a_failed_check(initialized, table):
    initialized.trash.rmdir()

    checks = named(storage_checks(initialized, archive_id=ARCHIVE_ID, table=table))

    assert codes(checks["staging_filesystem"].problems) == ["HFMNT008"]


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #


def test_the_gate_returns_the_ordered_checks_when_everything_passes(initialized, table):
    checks = require_storage_safety(initialized, archive_id=ARCHIVE_ID, table=table)

    assert [check.name for check in checks] == [
        "archive_root",
        "mount_point",
        "filesystem_type",
        "mount_writable",
        "sentinel",
        "directory_writability",
        "staging_filesystem",
    ]


def test_the_gate_carries_every_problem_not_just_the_first(
    archive_root: Path, layout: ArchiveLayout
):
    table = parse_mount_table(
        nfs_line(os.path.realpath(archive_root), filesystem="ext4", options="ro")
    )

    problems = gate_problems(layout, table)

    assert codes(problems) == ["HFMNT003", "HFMNT004"]


def test_the_gate_exits_twenty(layout: ArchiveLayout):
    with pytest.raises(SafetyError) as caught:
        require_storage_safety(layout, archive_id=ARCHIVE_ID, table=())

    assert caught.value.exit_code == ExitCode.SAFETY


def test_the_gate_refuses_an_uninitialized_archive(layout: ArchiveLayout, table):
    # `doctor` reports this as skipped and still exits `0`; a command about to
    # write may not assume a check it never ran would have passed.
    problems = gate_problems(layout, table)

    assert codes(problems) == ["HFMNT005"]
    assert "not initialized" in problems[0].message


def test_the_gate_adds_nothing_for_a_check_an_earlier_failure_made_unreachable(
    tmp_path: Path, table
):
    # Three checks are skipped, but the failure that caused them is already in
    # the report; restating it three more times would be noise.
    problems = gate_problems(ArchiveLayout(root=tmp_path / "absent"), table)

    assert codes(problems) == ["HFMNT001"]


def test_the_gate_offers_no_read_only_mode():
    # A command that is about to write has no business asking for one, and an
    # option that silences a check is an option that lets one through.
    signature = inspect.signature(require_storage_safety, annotation_format=inspect.Format.STRING)

    assert "read_only" not in signature.parameters
