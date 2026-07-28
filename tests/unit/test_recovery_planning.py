"""Deciding what a crashed run left, and finishing it — or refusing to.

Recovery is the part of the design where being wrong is expensive, so almost
every test here is about a refusal: a journal recovery may not act on, a state
two valid executions could both have produced, or staging too young to be
certainly abandoned.

The one remedy this package can actually perform is rolling back a publication
that stopped before anything was published: the staging tree is *quarantined*,
never deleted, because it is evidence of what a crashed run had built (§7.8).
Every test that provokes it asserts the bytes are still on the dataset.

`--apply` is asserted to be idempotent by running it twice, which is the
property `TX-04` exists to guarantee.
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path  # noqa: TC003 - `aged` takes and returns one at run time

import pytest

from hfcache.archive import initialize_archive
from hfcache.errors import ExitCode, RetentionError, SafetyError
from hfcache.identity import TransactionId, new_run_id, new_transaction_id
from hfcache.paths import ArchiveLayout
from hfcache.publication import create_staging
from hfcache.recovery import apply_recovery, plan_recovery
from hfcache.reporting import RecoveryReport
from hfcache.storage import parse_mount_table, read_model
from hfcache.transactions import CHECKPOINTS, open_transaction, read_journal

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
FINGERPRINT = "a" * 64

NOW = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

ENVELOPE = {
    "application_version": "0.1.0",
    "archive_id": ARCHIVE_ID,
    "config_fingerprint": FINGERPRINT,
    "hostname": "writer",
    "huggingface_hub_version": "1.24.0",
    "invocation_mode": "interactive",
    "python_version": "3.14.6",
}


def nfs_line(mount_point: str) -> str:
    return (
        f"457 47 0:68 / {mount_point} rw,nosuid,nodev,relatime shared:488 "
        f"- nfs4 nas.lab.example.com:/mnt/tank/hf rw,vers=4.2"
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


def begin(layout: ArchiveLayout, operation: str = "publication"):
    return open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation=operation,
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=FINGERPRINT,
    )


def abandoned_publication(layout: ArchiveLayout, *, hours: float = 48):
    """A publication that opened a journal, built staging, and then died."""
    transaction = begin(layout)
    identifier = TransactionId(transaction.journal.transaction_id)
    paths = create_staging(layout, identifier)
    (paths.tree / "half-a-revision").write_text("bytes", encoding="utf-8")
    transaction.checkpoint("staging_created", staging_path=f".store/staging/{identifier}")
    when = (NOW - timedelta(hours=hours)).timestamp()
    os.utime(paths.directory, (when, when))
    return transaction, paths


def plan(layout: ArchiveLayout, *, hours: int = 24):
    return plan_recovery(layout, stale_staging_age_hours=hours, now=NOW)


def apply(layout: ArchiveLayout, prepared):
    return apply_recovery(layout, prepared, envelope=ENVELOPE, started_at=NOW)


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


# --------------------------------------------------------------------------- #
# Planning
# --------------------------------------------------------------------------- #


def test_a_clean_archive_needs_no_recovery(layout: ArchiveLayout):
    prepared = plan(layout)

    assert prepared.remediations == ()
    assert prepared.actionable == ()
    assert prepared.blocked == ()


def test_a_publication_that_stopped_before_publishing_rolls_back(layout: ArchiveLayout):
    # §7.3 crash matrix, "Before 5": nothing published changed, so rolling back
    # is always the correct resolution.
    abandoned_publication(layout)

    (entry,) = plan(layout).remediations

    assert entry.remedy == "quarantine_staging"
    assert entry.last_checkpoint == "staging_created"


def test_staging_too_young_to_be_abandoned_is_left_alone(layout: ArchiveLayout):
    # §7.8 requires all three of name, journal, and age before anything is acted
    # on, and "recently" is not evidence of abandonment.
    abandoned_publication(layout, hours=1)

    (entry,) = plan(layout, hours=24).remediations

    assert entry.remedy == "wait"
    assert plan(layout, hours=24).actionable == ()


def test_a_journal_whose_staging_is_already_gone_only_needs_closing(layout: ArchiveLayout):
    transaction = begin(layout)
    transaction.checkpoint("staging_created")

    (entry,) = plan(layout).remediations

    assert entry.remedy == "close_journal"


def test_a_transaction_that_finished_everything_but_the_journal_is_closed(layout: ArchiveLayout):
    # §7.3, "After 9, before 10": everything is published and no filesystem
    # change is needed.
    transaction = begin(layout)
    for name in CHECKPOINTS["publication"]:
        transaction.checkpoint(name)

    (entry,) = plan(layout).remediations

    assert entry.remedy == "close_journal"


def test_a_journal_that_asked_for_an_operator_is_never_resolved(layout: ArchiveLayout):
    begin(layout).needs_operator("HFTXN004", "two equally valid resolutions")

    prepared = plan(layout)

    assert prepared.blocked
    assert codes(prepared.problems) == ["HFTXN004"]


def test_a_journal_that_contradicts_the_filesystem_is_blocked(layout: ArchiveLayout):
    # `HFTXN003`: a journal that disagrees with the archive cannot be used to
    # decide anything about it.
    transaction = begin(layout)
    transaction.checkpoint("staging_created", staging_path=".store/staging/never-existed")

    prepared = plan(layout)

    assert codes(prepared.problems) == ["HFTXN003"]


def test_a_published_tree_with_no_surviving_manifest_is_quarantined(layout: ArchiveLayout):
    # §7.3, "After 5, before 6": roll forward *if the staged manifest survives*.
    # This journal has no manifest anywhere, so the tree cannot be validated and
    # the row's own caveat applies — never publish an unvalidated tree.
    transaction = begin(layout)
    for name in CHECKPOINTS["publication"][:5]:
        transaction.checkpoint(name)

    prepared = plan(layout)

    assert not prepared.blocked
    assert prepared.remediations[0].remedy == "quarantine_tree"


def test_a_plan_renders_for_the_envelope(layout: ArchiveLayout):
    abandoned_publication(layout)

    payload = plan(layout).as_payload()

    assert payload["actionable"] == 1
    assert payload["blocked"] == 0
    assert payload["plan"][0]["remedy"] == "quarantine_staging"


# --------------------------------------------------------------------------- #
# Applying
# --------------------------------------------------------------------------- #


def test_applying_quarantines_rather_than_deletes(layout: ArchiveLayout):
    transaction, paths = abandoned_publication(layout)

    apply(layout, plan(layout))

    quarantined = layout.quarantine_for(TransactionId(transaction.journal.transaction_id))
    assert not paths.directory.exists()
    assert (quarantined / "tree" / "half-a-revision").read_text(encoding="utf-8") == "bytes"


def test_applying_closes_the_journal_it_resolved(layout: ArchiveLayout):
    transaction, _ = abandoned_publication(layout)

    apply(layout, plan(layout))

    reopened = read_journal(layout, transaction.path)
    assert reopened.journal.state == "failed"
    assert reopened.journal.is_resolved


def test_applying_closes_a_transaction_that_only_had_its_journal_open(layout: ArchiveLayout):
    # §7.3, "After 9, before 10": everything is published, so the journal is
    # closed as committed rather than failed — nothing was rolled back.
    transaction = begin(layout)
    for name in CHECKPOINTS["publication"]:
        transaction.checkpoint(name)

    _, applied = apply(layout, plan(layout))

    assert read_journal(layout, transaction.path).journal.state == "committed"
    assert applied[0].remedy == "close_journal"
    assert applied[0].evidence == {}


def test_applying_twice_is_harmless(layout: ArchiveLayout):
    # `TX-04`. The first run resolves the journal, so the second finds nothing —
    # which is what makes `recover --apply` safe to repeat after a partial run.
    abandoned_publication(layout)

    apply(layout, plan(layout))
    second = plan(layout)

    assert second.remediations == ()
    _, applied = apply(layout, second)
    assert applied == ()


def test_applying_records_one_checkpoint_per_remediation(layout: ArchiveLayout):
    abandoned_publication(layout)

    apply(layout, plan(layout))

    (journal,) = [
        read_journal(layout, path).journal
        for path in sorted(layout.transactions.iterdir())
        if read_journal(layout, path).journal.operation == "recovery"
    ]
    assert [checkpoint.name for checkpoint in journal.checkpoints] == [
        "quarantine_staging",
        "recovery_report_written",
        "recovery_completed",
    ]
    assert journal.state == "committed"


def test_applying_writes_a_durable_report(layout: ArchiveLayout):
    transaction, _ = abandoned_publication(layout)

    report_path, applied = apply(layout, plan(layout))

    report = read_model(report_path, RecoveryReport, error=SafetyError, code="HFTXN001")
    assert report.command == "recover --apply"
    assert [entry.transaction_id for entry in report.remediations] == [
        transaction.journal.transaction_id
    ]
    assert applied[0].outcome == "applied"


def test_the_report_records_the_evidence_it_observed(layout: ArchiveLayout):
    transaction, _ = abandoned_publication(layout)

    _, applied = apply(layout, plan(layout))

    identifier = transaction.journal.transaction_id
    assert applied[0].evidence["quarantine_path"] == f".store/quarantine/{identifier}"
    assert applied[0].evidence["staging_absent"] == f".store/staging/{identifier}"


def test_a_blocked_plan_is_refused_before_anything_is_performed(layout: ArchiveLayout):
    # A partially recovered archive with an unresolved transaction still in it is
    # harder to reason about than the state it started in.
    _, paths = abandoned_publication(layout)
    begin(layout).needs_operator("HFTXN004", "two equally valid resolutions")

    with pytest.raises(SafetyError) as caught:
        apply(layout, plan(layout))

    assert caught.value.exit_code == ExitCode.SAFETY
    assert paths.directory.is_dir(), "nothing was performed"


def test_a_remediation_left_pending_is_reported_but_not_performed(layout: ArchiveLayout):
    _, paths = abandoned_publication(layout, hours=1)

    _, applied = apply(layout, plan(layout, hours=24))

    assert applied[0].outcome == "pending"
    assert paths.directory.is_dir()


def test_quarantining_that_fails_is_reported_rather_than_half_done(layout: ArchiveLayout):
    abandoned_publication(layout)
    layout.quarantine.chmod(0o500)
    try:
        with pytest.raises(RetentionError) as caught:
            apply(layout, plan(layout))
    finally:
        layout.quarantine.chmod(0o700)

    assert codes(caught.value.problems) == ["HFRET010"]


# --------------------------------------------------------------------------- #
# The durable report (`docs/schemas.md` §12)
# --------------------------------------------------------------------------- #


def report_payload(**overrides):
    return (
        ENVELOPE
        | {
            "command": "recover --apply",
            "completed_at": NOW,
            "exit_code": 0,
            "outcome": "success",
            "run_id": new_run_id(),
            "started_at": NOW,
        }
        | overrides
    )


def remediation(transaction_id: str) -> dict:
    return {
        "outcome": "applied",
        "reason": "rolled back",
        "remedy": "quarantine_staging",
        "transaction_id": transaction_id,
    }


def test_a_report_lists_each_transaction_once():
    with pytest.raises(ValueError, match="at most once"):
        RecoveryReport.model_validate(
            report_payload(remediations=[remediation("a" * 32), remediation("a" * 32)])
        )


def test_a_report_is_sorted_by_transaction_id():
    # `docs/architecture.md` §5.3: every generated array is deterministically
    # ordered, so two runs that did the same work produce the same bytes.
    with pytest.raises(ValueError, match="sorted"):
        RecoveryReport.model_validate(
            report_payload(remediations=[remediation("b" * 32), remediation("a" * 32)])
        )
