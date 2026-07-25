"""What the transaction areas hold, and why none of it is removed here.

Every test that puts something in one of these areas also asserts it is still
there afterwards. That is the point of the module: `FS-19` says the application
reports and preserves, and plan §13.3 allows reclamation only once a journal
exists to say what a staging directory holds — which is `STO-010` and `STO-011`,
not this package.

Ages are injected rather than waited for. `now` is a parameter precisely so a
test can describe a directory as a week old without the suite taking a week.
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path  # noqa: TC003 - `aged` takes and returns one at run time

import pytest

from hfcache.archive import initialize_archive
from hfcache.config import StorageConfig
from hfcache.paths import ArchiveLayout
from hfcache.recovery import measure_health, reconcile_storage
from hfcache.storage import parse_mount_table

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"

TRANSACTION = "0123456789abcdef0123456789abcdef"
OTHER_TRANSACTION = "fedcba9876543210fedcba9876543210"

NOW = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


def nfs_line(mount_point: str) -> str:
    return (
        f"457 47 0:68 / {mount_point} rw,nosuid,nodev,relatime shared:488 "
        f"- nfs4 nas.lab.cross.solutions:/mnt/tank/hf rw,vers=4.2"
    )


@pytest.fixture
def layout(tmp_path: Path) -> ArchiveLayout:
    root = tmp_path / "archive"
    root.mkdir()
    built = ArchiveLayout(root=root)
    initialize_archive(
        built, archive_id=ARCHIVE_ID, table=parse_mount_table(nfs_line(os.path.realpath(root)))
    )
    return built


def storage_config(**overrides) -> StorageConfig:
    return StorageConfig.model_validate(
        {
            "archive_root": "/srv/hfcache",
            "archive_id": ARCHIVE_ID,
            "minimum_free_space_gib": 0,
            "minimum_free_space_percent": 0,
            **overrides,
        }
    )


def aged(directory: Path, *, hours: float) -> Path:
    """Create a directory and backdate it, so age is stated rather than waited for."""
    directory.mkdir(parents=True)
    when = (NOW - timedelta(hours=hours)).timestamp()
    os.utime(directory, (when, when))
    return directory


def reconcile(layout: ArchiveLayout, *, hours: int = 24):
    return reconcile_storage(layout, stale_staging_age_hours=hours, now=NOW)


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


# --------------------------------------------------------------------------- #
# Nothing outstanding
# --------------------------------------------------------------------------- #


def test_a_clean_archive_has_nothing_to_report(layout: ArchiveLayout):
    result = reconcile(layout)

    assert result.findings == ()
    assert result.unknown == ()
    assert result.warnings == ()


def test_an_archive_without_the_areas_yet_is_not_a_finding(tmp_path: Path):
    # An uninitialized archive has not reached this state; that is `doctor`'s
    # sentinel check to report, not a reconciliation finding.
    assert reconcile(ArchiveLayout(root=tmp_path)).findings == ()


# --------------------------------------------------------------------------- #
# Staging (`HFWRN004`)
# --------------------------------------------------------------------------- #


def test_recent_staging_is_reported_without_a_warning(layout: ArchiveLayout):
    # A sync that is running right now owns this directory.
    aged(layout.staging / TRANSACTION, hours=1)

    result = reconcile(layout, hours=24)

    assert [finding.transaction_id for finding in result.findings] == [TRANSACTION]
    assert not result.findings[0].stale
    assert result.warnings == ()


def test_staging_past_the_configured_age_is_hfwrn004(layout: ArchiveLayout):
    staging = aged(layout.staging / TRANSACTION, hours=48)

    result = reconcile(layout, hours=24)

    assert result.findings[0].stale
    assert codes(result.warnings) == ["HFWRN004"]
    assert staging.is_dir(), "reported and preserved; reclamation needs the journal"


def test_the_age_that_makes_staging_stale_is_configurable(layout: ArchiveLayout):
    aged(layout.staging / TRANSACTION, hours=48)

    assert reconcile(layout, hours=72).warnings == ()
    assert codes(reconcile(layout, hours=12).warnings) == ["HFWRN004"]


def test_the_warning_says_why_it_is_not_simply_removed(layout: ArchiveLayout):
    aged(layout.staging / TRANSACTION, hours=48)

    assert "journal" in reconcile(layout, hours=24).warnings[0].message


def test_every_stale_area_is_warned_about(layout: ArchiveLayout):
    aged(layout.staging / TRANSACTION, hours=48)
    aged(layout.staging / OTHER_TRANSACTION, hours=100)

    assert codes(reconcile(layout, hours=24).warnings) == ["HFWRN004", "HFWRN004"]


def test_a_repair_cache_is_unfinished_work_too(layout: ArchiveLayout):
    # `.store/repair/<transaction-id>` is transaction-scoped scratch that is
    # removed once its bytes are durable, so a leftover is a run that did not
    # finish.
    aged(layout.repair_caches / TRANSACTION, hours=1)

    result = reconcile(layout)

    assert len(result.unfinished) == 1
    assert result.unfinished[0].area == ".store/repair"


# --------------------------------------------------------------------------- #
# Trash and quarantine
# --------------------------------------------------------------------------- #


def test_a_tombstone_is_deferred_cleanup_not_stale_staging(layout: ArchiveLayout):
    tombstone = aged(layout.trash / TRANSACTION, hours=200)

    result = reconcile(layout)

    assert codes(result.warnings) == ["HFWRN002"]
    assert len(result.deferred_cleanup) == 1
    assert not result.findings[0].stale, "trash has no staleness rule; it is committed work"
    assert tombstone.is_dir()


def test_quarantine_is_reported_and_never_warned_about(layout: ArchiveLayout):
    # Quarantined evidence is retained until an operator confirms and explicitly
    # approves cleanup (plan §16.5), so age says nothing about it.
    evidence = aged(layout.quarantine / TRANSACTION, hours=5000)

    result = reconcile(layout)

    assert [finding.area for finding in result.findings] == [".store/quarantine"]
    assert result.warnings == ()
    assert evidence.is_dir()


# --------------------------------------------------------------------------- #
# Unknown entries (`HFWRN003`)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "name",
    [
        "somebody-elses-directory",
        "0123456789abcdef",
        "0123456789ABCDEF0123456789ABCDEF",
        "0123456789abcdef0123456789abcdeff",
        "gggggggggggggggggggggggggggggggg",
    ],
)
def test_a_name_that_is_not_a_transaction_id_is_unknown(layout: ArchiveLayout, name):
    stranger = layout.staging / name
    stranger.mkdir()

    result = reconcile(layout)

    assert result.unknown == (f".store/staging/{name}",)
    assert codes(result.warnings) == ["HFWRN003"]
    assert stranger.is_dir(), "nothing unrecognized is ever removed"


def test_an_unknown_file_is_reported_as_well_as_an_unknown_directory(layout: ArchiveLayout):
    (layout.trash / "notes.txt").write_text("an operator left this", encoding="utf-8")

    result = reconcile(layout)

    assert result.unknown == (".store/trash/notes.txt",)


def test_every_unknown_entry_is_named_in_one_warning(layout: ArchiveLayout):
    (layout.staging / "one").mkdir()
    (layout.trash / "two").mkdir()

    result = reconcile(layout)

    assert codes(result.warnings) == ["HFWRN003"]
    assert result.warnings[0].context["entries"] == [".store/staging/one", ".store/trash/two"]


def test_findings_render_for_the_envelope(layout: ArchiveLayout):
    aged(layout.staging / TRANSACTION, hours=48)

    payload = reconcile(layout, hours=24).as_payload()

    assert payload["unfinished_transactions"] == 1
    assert payload["deferred_cleanup"] == 0
    assert payload["findings"][0]["transaction_id"] == TRANSACTION
    assert payload["findings"][0]["stale"] is True


# --------------------------------------------------------------------------- #
# The health block `status` reports
# --------------------------------------------------------------------------- #


def test_health_measures_free_space_against_the_reserve(layout: ArchiveLayout):
    health = measure_health(layout, storage_config(), stale_staging_age_hours=24, now=NOW)

    assert health.total_bytes > 0
    assert health.reserve_bytes == 0
    assert health.headroom_bytes == health.available_bytes


def test_health_reports_a_breached_reserve_as_negative_headroom(layout: ArchiveLayout):
    # A reserve of the whole filesystem cannot be met, which is the portable way
    # to observe the breached case.
    health = measure_health(
        layout,
        storage_config(minimum_free_space_percent=100),
        stale_staging_age_hours=24,
        now=NOW,
    )

    assert health.headroom_bytes < 0


def test_health_carries_the_reconciliation_with_it(layout: ArchiveLayout):
    aged(layout.staging / TRANSACTION, hours=48)

    health = measure_health(layout, storage_config(), stale_staging_age_hours=24, now=NOW)

    assert codes(health.reconciliation.warnings) == ["HFWRN004"]
    assert health.as_payload()["unfinished_transactions"] == 1


def test_health_reads_the_clock_when_no_moment_is_given(layout: ArchiveLayout):
    aged(layout.staging / TRANSACTION, hours=0)

    health = measure_health(layout, storage_config(), stale_staging_age_hours=24)

    assert len(health.reconciliation.findings) == 1
