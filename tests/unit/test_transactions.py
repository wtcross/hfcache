"""Journals that record what happened, and refuse to describe what did not.

Three things are asserted here that the rest of the design leans on.

A journal is durable *before* the first mutation (`TX-01`) and each checkpoint
is written *after* the act it names (`TX-02`), so every test that records one
reads the file back rather than trusting the object in memory.

A checkpoint sequence that no valid execution produces is `HFTXN002`. The
documented sequences in `docs/architecture.md` §7.3-§7.7 are parsed out of the
document and asserted against `CHECKPOINTS`, in both directions, so a table in a
module and a table in a document cannot drift.

Evidence is re-observable (`TX-03`). Recovery confirms a checkpoint by looking
at the archive, so the tests move and remove the things evidence names and check
that the disagreement is reported as `HFTXN003`.
"""

import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from hfcache.archive import initialize_archive
from hfcache.errors import ExitCode, SafetyError
from hfcache.identity import new_run_id, new_transaction_id
from hfcache.models import SCHEMA_VERSION
from hfcache.paths import ArchiveLayout
from hfcache.storage import parse_mount_table
from hfcache.transactions import (
    CHECKPOINTS,
    JOURNAL_MODE,
    checkpoint_order_problems,
    evidence_problems,
    open_journals,
    open_transaction,
    read_journal,
)

if TYPE_CHECKING:
    from hfcache.transactions import Transaction

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
FINGERPRINT = "0123456789abcdef"

ARCHITECTURE = Path(__file__).resolve().parents[2] / "docs" / "architecture.md"

_ROW = re.compile(r"^\|\s*\d+\s*\|\s*`(\w+)`\s*\|")


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


def begin(layout: ArchiveLayout, operation: str = "publication", **scope) -> Transaction:
    return open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation=operation,
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=FINGERPRINT,
        **scope,
    )


def on_disk(transaction: Transaction) -> dict:
    return json.loads(transaction.path.read_text(encoding="utf-8"))


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


# --------------------------------------------------------------------------- #
# The sequences are the document's
# --------------------------------------------------------------------------- #


def documented_checkpoints(heading: str) -> list[str]:
    """Read one §7 checkpoint table out of `docs/architecture.md`."""
    lines = ARCHITECTURE.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(heading))
    names: list[str] = []
    for line in lines[start:]:
        if matched := _ROW.match(line):
            names.append(matched.group(1))
        elif names and line.startswith("###"):
            break
    return names


@pytest.mark.parametrize(
    ("heading", "operation"),
    [
        ("### 7.3 Publication transaction", "publication"),
        ("### 7.4 Prune transaction", "prune"),
        ("### 7.5 Repair transaction", "repair"),
        ("### 7.6 Sync run transaction", "sync"),
    ],
)
def test_the_documented_sequence_is_the_implemented_sequence(heading, operation):
    # A table in a document and a tuple in a module drift the moment someone
    # edits one, so neither is written twice.
    assert documented_checkpoints(heading) == list(CHECKPOINTS[operation])


def test_recovery_has_no_fixed_sequence():
    # §7.7 records one checkpoint per remediation, so its length is whatever it
    # found and cannot be enumerated.
    assert "recovery" not in CHECKPOINTS


# --------------------------------------------------------------------------- #
# Opening (`TX-01`)
# --------------------------------------------------------------------------- #


def test_a_journal_is_durable_before_the_first_mutation(layout: ArchiveLayout):
    transaction = begin(layout)

    assert transaction.path.is_file()
    assert on_disk(transaction)["state"] == "open"
    assert on_disk(transaction)["schema_version"] == SCHEMA_VERSION


def test_a_journal_is_private_to_the_writer(layout: ArchiveLayout):
    transaction = begin(layout)

    assert transaction.path.stat().st_mode & 0o777 == JOURNAL_MODE


def test_a_journal_records_the_configuration_it_was_opened_under(layout: ArchiveLayout):
    transaction = begin(layout)

    assert on_disk(transaction)["archive_id"] == ARCHIVE_ID
    assert on_disk(transaction)["config_fingerprint"] == FINGERPRINT


def test_a_journal_can_be_narrowed_to_one_repository_and_revision(layout: ArchiveLayout):
    transaction = begin(
        layout,
        repository_id="organization/model-name",
        repository_type="model",
        commit_sha="0" * 40,
    )

    assert on_disk(transaction)["repository_id"] == "organization/model-name"
    assert on_disk(transaction)["commit_sha"] == "0" * 40


def test_a_journal_that_cannot_be_written_is_hftxn001(layout: ArchiveLayout):
    layout.transactions.chmod(0o500)
    try:
        with pytest.raises(SafetyError) as caught:
            begin(layout)
    finally:
        layout.transactions.chmod(0o700)

    assert codes(caught.value.problems) == ["HFTXN001"]
    assert caught.value.exit_code == ExitCode.SAFETY


# --------------------------------------------------------------------------- #
# Checkpointing (`TX-02`, `TX-03`)
# --------------------------------------------------------------------------- #


def test_a_checkpoint_is_durable_when_it_returns(layout: ArchiveLayout):
    transaction = begin(layout)

    transaction.checkpoint("staging_created", staging_path=".store/staging/x")

    (recorded,) = on_disk(transaction)["checkpoints"]
    assert recorded["name"] == "staging_created"
    assert recorded["sequence"] == 1
    assert recorded["evidence"]["staging_path"] == ".store/staging/x"


def test_checkpoints_are_appended_with_increasing_sequence(layout: ArchiveLayout):
    transaction = begin(layout)

    for name in CHECKPOINTS["publication"][:4]:
        transaction.checkpoint(name)

    recorded = on_disk(transaction)["checkpoints"]
    assert [entry["sequence"] for entry in recorded] == [1, 2, 3, 4]
    assert [entry["name"] for entry in recorded] == list(CHECKPOINTS["publication"][:4])


def test_the_last_checkpoint_time_tracks_the_last_checkpoint(layout: ArchiveLayout):
    transaction = begin(layout)

    assert on_disk(transaction)["last_checkpoint_at"] is None

    transaction.checkpoint("staging_created")

    assert on_disk(transaction)["last_checkpoint_at"] is not None


def test_a_checkpoint_out_of_order_is_hftxn002(layout: ArchiveLayout):
    transaction = begin(layout)
    transaction.checkpoint("staging_created")

    with pytest.raises(SafetyError) as caught:
        transaction.checkpoint("current_ref_replaced")

    assert codes(caught.value.problems) == ["HFTXN002"]
    assert len(on_disk(transaction)["checkpoints"]) == 1, "the refusal wrote nothing"


def test_a_checkpoint_from_another_operation_is_hftxn002(layout: ArchiveLayout):
    transaction = begin(layout, "prune")

    with pytest.raises(SafetyError) as caught:
        transaction.checkpoint("staging_created")

    assert codes(caught.value.problems) == ["HFTXN002"]


def test_a_cleanup_deferred_checkpoint_on_a_prune_is_refused(layout: ArchiveLayout):
    # RET-009: §7.4 once named this checkpoint, but no execution records one —
    # a post-commit failure leaves the journal open at its last checkpoint, and
    # that is what makes the cleanup reachable from `recover`. A journal
    # carrying it was therefore written by no valid execution.
    transaction = begin(layout, "prune")
    for name in CHECKPOINTS["prune"][:7]:
        transaction.checkpoint(name)

    with pytest.raises(SafetyError) as caught:
        transaction.checkpoint("cleanup_deferred")

    assert codes(caught.value.problems) == ["HFTXN002"]
    assert len(on_disk(transaction)["checkpoints"]) == 7, "the refusal wrote nothing"


def test_a_recovery_journal_records_one_checkpoint_per_remediation(layout: ArchiveLayout):
    transaction = begin(layout, "recovery")

    transaction.checkpoint("staging_quarantined", transaction_id="a" * 32)
    transaction.checkpoint("reference_repaired", transaction_id="b" * 32)
    transaction.checkpoint("recovery_report_written")
    transaction.checkpoint("recovery_completed")

    assert len(on_disk(transaction)["checkpoints"]) == 4


def test_a_recovery_journal_that_closes_out_of_order_is_hftxn002(layout: ArchiveLayout):
    # The report is written before the run is called complete, so recording the
    # completion first is refused on the spot.
    transaction = begin(layout, "recovery")
    transaction.checkpoint("staging_quarantined", transaction_id="a" * 32)

    with pytest.raises(SafetyError) as caught:
        transaction.checkpoint("recovery_completed")

    assert codes(caught.value.problems) == ["HFTXN002"]
    assert len(on_disk(transaction)["checkpoints"]) == 1


def test_a_recovery_journal_with_work_after_its_close_is_hftxn002(layout: ArchiveLayout):
    transaction = begin(layout, "recovery")
    transaction.checkpoint("recovery_report_written")
    transaction.checkpoint("recovery_completed")

    with pytest.raises(SafetyError) as caught:
        transaction.checkpoint("staging_quarantined")

    assert codes(caught.value.problems) == ["HFTXN002"]


# --------------------------------------------------------------------------- #
# Closing
# --------------------------------------------------------------------------- #


def test_committing_closes_the_journal(layout: ArchiveLayout):
    transaction = begin(layout)

    transaction.commit()

    assert on_disk(transaction)["state"] == "committed"
    assert on_disk(transaction)["completed_at"] is not None
    assert transaction.journal.is_resolved


def test_failing_records_why_without_stopping_the_archive(layout: ArchiveLayout):
    transaction = begin(layout)

    transaction.fail("HFSYN006", "publication rename failed")

    recorded = on_disk(transaction)
    assert recorded["state"] == "failed"
    assert recorded["error"]["code"] == "HFSYN006"
    assert transaction.journal.is_resolved


def test_needing_an_operator_is_not_resolved(layout: ArchiveLayout):
    # §7.9: this is precisely what must stop the next run, so reconciliation
    # still has to see it.
    transaction = begin(layout)

    transaction.needs_operator("HFTXN004", "two equally valid resolutions")

    assert on_disk(transaction)["state"] == "needs_operator"
    assert not transaction.journal.is_resolved


# --------------------------------------------------------------------------- #
# Reading one back
# --------------------------------------------------------------------------- #


def test_a_journal_round_trips(layout: ArchiveLayout):
    transaction = begin(layout)
    transaction.checkpoint("staging_created", staging_path=".store/staging/x")

    file = read_journal(layout, transaction.path)

    assert file.journal == transaction.journal
    assert file.unknown == {}


def test_an_unreadable_journal_is_hftxn001(layout: ArchiveLayout):
    with pytest.raises(SafetyError) as caught:
        read_journal(layout, layout.transactions / "absent.json")

    assert codes(caught.value.problems) == ["HFTXN001"]


@pytest.mark.parametrize("content", ["{ not json", "[1, 2, 3]", '"a string"'])
def test_a_journal_that_is_not_an_object_is_hftxn001(layout: ArchiveLayout, content):
    path = layout.transactions / "broken.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(SafetyError) as caught:
        read_journal(layout, path)

    assert codes(caught.value.problems) == ["HFTXN001"]


def test_a_journal_from_a_newer_release_is_refused_rather_than_read(layout: ArchiveLayout):
    # §7.9's first stopping condition: recovery never acts on a journal it
    # cannot fully read.
    transaction = begin(layout)
    payload = on_disk(transaction) | {"schema_version": SCHEMA_VERSION + 1}
    transaction.path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SafetyError) as caught:
        read_journal(layout, transaction.path)

    assert codes(caught.value.problems) == ["HFTXN001"]
    assert "newer" in caught.value.problems[0].message


def test_an_unknown_key_is_preserved_across_a_rewrite(layout: ArchiveLayout):
    # `docs/schemas.md` §1.1: the journal is the only artifact ever read,
    # modified, and written back, so it is the only one where a key could be
    # destroyed (decision 20).
    transaction = begin(layout)
    payload = on_disk(transaction) | {"a_key_from_a_later_release": {"kept": True}}
    transaction.path.write_text(json.dumps(payload), encoding="utf-8")

    reopened = read_journal(layout, transaction.path)
    assert reopened.unknown == {"a_key_from_a_later_release": {"kept": True}}

    transaction.file = reopened
    transaction.checkpoint("staging_created")

    assert on_disk(transaction)["a_key_from_a_later_release"] == {"kept": True}
    assert on_disk(transaction)["checkpoints"][0]["name"] == "staging_created"


# --------------------------------------------------------------------------- #
# Reconciliation (`TX-07`)
# --------------------------------------------------------------------------- #


def test_a_clean_archive_has_no_journals_to_reconcile(layout: ArchiveLayout):
    assert open_journals(layout) == ()


def test_a_resolved_journal_is_left_alone(layout: ArchiveLayout):
    begin(layout).commit()
    begin(layout).fail("HFSYN006", "publication rename failed")

    assert open_journals(layout) == ()


def test_an_open_journal_must_be_reconciled(layout: ArchiveLayout):
    transaction = begin(layout)

    (found,) = open_journals(layout)

    assert found.journal.transaction_id == transaction.journal.transaction_id


def test_a_journal_needing_an_operator_must_be_reconciled(layout: ArchiveLayout):
    begin(layout).needs_operator("HFTXN004", "two equally valid resolutions")

    assert len(open_journals(layout)) == 1


def test_an_archive_without_a_transactions_directory_has_none(tmp_path: Path):
    assert open_journals(ArchiveLayout(root=tmp_path)) == ()


def test_a_file_that_is_not_a_journal_is_not_read(layout: ArchiveLayout):
    (layout.transactions / "notes.txt").write_text("an operator left this", encoding="utf-8")

    assert open_journals(layout) == ()


# --------------------------------------------------------------------------- #
# Evidence (`TX-03`, `HFTXN003`)
# --------------------------------------------------------------------------- #


def test_evidence_that_still_holds_is_no_problem(layout: ArchiveLayout):
    staging = layout.staging / ("a" * 32)
    staging.mkdir()
    transaction = begin(layout)
    transaction.checkpoint("staging_created", staging_path=f".store/staging/{'a' * 32}")

    assert evidence_problems(layout, transaction.journal) == []


def test_a_path_that_has_gone_is_hftxn003(layout: ArchiveLayout):
    staging = layout.staging / ("a" * 32)
    staging.mkdir()
    transaction = begin(layout)
    transaction.checkpoint("staging_created", staging_path=f".store/staging/{'a' * 32}")
    staging.rmdir()

    problems = evidence_problems(layout, transaction.journal)

    assert codes(problems) == ["HFTXN003"]
    assert "disagree" in problems[0].message


def test_a_list_of_paths_is_checked_entry_by_entry(layout: ArchiveLayout):
    (layout.staging / "one").mkdir()
    transaction = begin(layout)
    transaction.checkpoint(
        "staging_created", staged_paths=[".store/staging/one", ".store/staging/two"]
    )

    assert codes(evidence_problems(layout, transaction.journal)) == ["HFTXN003"]


def test_evidence_that_something_is_absent_is_checked_too(layout: ArchiveLayout):
    # A prune records that a per-SHA reference is gone; if it is back, the
    # journal and the archive disagree.
    transaction = begin(layout, "prune")
    for name in CHECKPOINTS["prune"][:2]:
        transaction.checkpoint(name)
    transaction.checkpoint("revision_ref_removed", reference_absent="published/repos/x.json")

    assert evidence_problems(layout, transaction.journal) == []

    restored = layout.published / "repos" / "x.json"
    restored.write_text("{}", encoding="utf-8")

    assert codes(evidence_problems(layout, transaction.journal)) == ["HFTXN003"]


def test_evidence_that_is_not_a_path_is_left_to_the_package_that_understands_it(
    layout: ArchiveLayout,
):
    # Counts and digests are checked by the code that knows how to interpret
    # them; only the key naming convention is mechanical here.
    transaction = begin(layout)
    transaction.checkpoint("staging_created")
    transaction.checkpoint("download_completed", file_count=42, digest="0" * 64)

    assert evidence_problems(layout, transaction.journal) == []


def test_a_path_that_could_escape_the_archive_is_hftxn003(layout: ArchiveLayout):
    transaction = begin(layout)
    transaction.checkpoint("staging_created", staging_path="../../etc/passwd")

    problems = evidence_problems(layout, transaction.journal)

    assert codes(problems) == ["HFTXN003"]
    assert "unusable" in problems[0].message


def test_order_problems_are_reported_for_a_journal_read_from_disk(layout: ArchiveLayout):
    # A journal corrupted in a way that still parses is exactly what this
    # catches, so it is checked on read as well as on append.
    transaction = begin(layout)
    transaction.checkpoint("staging_created")
    payload = on_disk(transaction)
    payload["checkpoints"][0]["name"] = "not_a_publication_checkpoint"
    transaction.path.write_text(json.dumps(payload), encoding="utf-8")

    file = read_journal(layout, transaction.path)

    assert codes(checkpoint_order_problems(file.journal)) == ["HFTXN002"]
