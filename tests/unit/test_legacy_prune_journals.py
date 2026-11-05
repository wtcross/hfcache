"""Preserve valid completed prune evidence from before container cleanup existed."""

from contextlib import contextmanager

import pytest

from hfcache.archive import initialize_archive
from hfcache.catalog_storage import CatalogWriter, read_tag_snapshot
from hfcache.config import StorageConfig
from hfcache.errors import IntegrityError, SafetyError
from hfcache.identity import RepositoryIdentity, new_run_id, new_transaction_id
from hfcache.locking import exclusive_lock
from hfcache.metadata import MetadataReader
from hfcache.models import TransactionJournal, dump
from hfcache.paths import ArchiveLayout
from hfcache.storage import parse_mount_table
from hfcache.transactions import checkpoint_order_problems, open_transaction
from tests.fixtures import examples

# Exact producer sequence in 5dc8d0a^, before 2026-07-27 added containers_removed.
LEGACY_PRUNE = (
    "plan_persisted",
    "cache_revision_deleted",
    "revision_ref_removed",
    "tree_tombstoned",
    "manifest_tombstoned",
    "catalog_published",
    "prune_logically_committed",
    "audit_record_written",
    "trash_removed",
    "prune_completed",
)


def legacy(*, state="committed", names=LEGACY_PRUNE, completed=True, error=False, early=False):
    at = "2026-07-26T20:25:31Z"
    payload = examples.journal().model_dump(mode="json")
    payload.update(
        operation="prune",
        state=state,
        completed_at=("2026-07-26T20:25:30Z" if early else at)
        if completed and state != "open"
        else None,
        created_at="2026-07-26T20:25:30Z",
        last_checkpoint_at=at,
        checkpoints=[
            {"sequence": i, "name": name, "recorded_at": at, "evidence": {}}
            for i, name in enumerate(names, 1)
        ],
        error={"at": at, "code": "HFTXN002", "message": "failed"} if error else None,
    )
    return TransactionJournal.model_validate(payload)


@pytest.fixture
def archive(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    layout = ArchiveLayout(root)
    table = parse_mount_table(f"457 47 0:68 / {root} rw - nfs4 nas:/fixture rw,vers=4.2\n")
    initialize_archive(layout, archive_id=examples.ARCHIVE_ID, table=table)
    storage = StorageConfig.model_validate(
        {
            "archive_root": str(root),
            "archive_id": examples.ARCHIVE_ID,
            "minimum_free_space_gib": 0,
            "minimum_free_space_percent": 0,
        }
    )
    return layout, storage, table


@contextmanager
def writer(archive):
    layout, storage, table = archive
    with exclusive_lock(
        layout.root.parent / "locks/hfcache.lock", command="catalog refresh", wait_seconds=0
    ):
        yield CatalogWriter(layout, storage=storage, table=table)


def test_exact_completed_original_prune_sequence_is_compatible():
    assert checkpoint_order_problems(legacy()) == []


@pytest.mark.parametrize(
    "change",
    [
        {"state": "open"},
        {"state": "failed"},
        {"state": "needs_operator"},
        {"completed": False},
        {"early": True},
        {"error": True},
        {"names": LEGACY_PRUNE[:-2] + LEGACY_PRUNE[-1:]},
        {"names": (*LEGACY_PRUNE[:2], "unknown", *LEGACY_PRUNE[2:])},
        {"names": LEGACY_PRUNE[:2] + LEGACY_PRUNE[3:4] + LEGACY_PRUNE[2:3] + LEGACY_PRUNE[4:]},
    ],
)
def test_legacy_exception_never_accepts_other_incomplete_or_unknown_evidence(change):
    assert [p.code for p in checkpoint_order_problems(legacy(**change))] == ["HFTXN002"]


def test_current_writer_cannot_skip_new_container_cleanup_checkpoint(archive):
    layout, _, _ = archive
    tx = open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="prune",
        run_id=new_run_id(),
        archive_id=examples.ARCHIVE_ID,
        config_fingerprint=examples.FINGERPRINT,
    )
    for name in LEGACY_PRUNE[:-1]:
        tx.checkpoint(name)
    before = tx.path.read_bytes()
    with pytest.raises(SafetyError):
        tx.checkpoint("prune_completed")
    assert tx.path.read_bytes() == before


def test_supplemental_capture_accepts_and_preserves_original_legacy_journal(archive):
    layout, _, _ = archive
    journal = legacy()
    path = layout.transactions / f"{journal.transaction_id}.json"
    original = dump(journal)
    path.write_bytes(original)
    with writer(archive) as capture:
        capture.write(examples.tag_snapshot())
    assert path.read_bytes() == original
    record = read_tag_snapshot(
        layout,
        RepositoryIdentity.of(
            examples.tag_snapshot().repository_type, examples.tag_snapshot().repository_id
        ),
        examples.ARCHIVE_ID,
        reader=MetadataReader(layout.root),
    )
    assert record == examples.tag_snapshot()


def test_unrelated_impossible_committed_sequence_still_refuses_and_preserves(archive):
    layout, _, _ = archive
    journal = legacy(names=LEGACY_PRUNE[:-2] + LEGACY_PRUNE[-1:])
    path = layout.transactions / f"{journal.transaction_id}.json"
    original = dump(journal)
    path.write_bytes(original)
    with pytest.raises(IntegrityError), writer(archive):
        pytest.fail("unknown committed checkpoint sequence bypassed adjunct guard")
    assert path.read_bytes() == original
