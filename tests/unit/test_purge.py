"""Explicit unmanaged-repository purge (`AD-20`, `PUR-001`)."""

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

import hfcache.purge as purge_module
from hfcache.archive import initialize_archive
from hfcache.errors import RetentionError
from hfcache.hub import delete_cache_revisions
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    TransactionId,
    new_publication_id,
    new_run_id,
    new_transaction_id,
)
from hfcache.models import Reference
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import (
    publish_catalog,
    publish_current_reference,
    publish_revision_reference,
    rebuild_catalog,
)
from hfcache.purge import apply_purge, complete_purge, plan_purge, rollback_purge
from hfcache.recovery import apply_recovery, plan_recovery
from hfcache.storage import parse_mount_table
from hfcache.transactions import open_transaction, read_journal
from tests.fixtures import examples

if TYPE_CHECKING:
    from pathlib import Path

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
FINGERPRINT = "0" * 64
NOW = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)
MODEL = RepositoryIdentity.of("model", "organization/model-name")


def sha(generation: int) -> str:
    return f"{generation:040d}"


@pytest.fixture
def layout(tmp_path: Path) -> ArchiveLayout:
    root = tmp_path / "archive"
    root.mkdir(mode=0o750)
    built = ArchiveLayout(root=root)
    table = parse_mount_table(
        f"457 47 0:68 / {os.path.realpath(root)} rw - nfs4 server:/archive rw\n"
    )
    initialize_archive(built, archive_id=ARCHIVE_ID, table=table)
    return built


def place(layout: ArchiveLayout, generation: int) -> Reference:
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    commit = CommitSha(sha(generation))
    publication = PublicationId(new_publication_id())
    tree = repository.instance(commit, publication)
    tree.mkdir(parents=True)
    manifest = examples.manifest().model_copy(
        update={
            "commit_sha": commit,
            "publication_generation": generation,
            "publication_id": publication,
            "repository_id": MODEL.id,
            "repository_type": MODEL.type,
            "tree": str(layout.archive_relative(tree)),
        }
    )
    manifest_path = repository.manifest(commit, publication)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest.to_json(), encoding="utf-8")
    reference = Reference(
        commit_sha=commit,
        manifest=str(repository.manifest_reference(commit, publication)),
        publication_generation=generation,
        publication_id=publication,
        repository_id=MODEL.id,
        repository_type=MODEL.type,
        tree=str(repository.tree_reference(commit, publication)),
        updated_at=NOW,
    )
    publish_revision_reference(layout, reference)
    publish_current_reference(layout, reference)
    return reference


def prepared(layout: ArchiveLayout):
    place(layout, 1)
    place(layout, 2)
    plan = plan_purge(layout, MODEL, generated_at=NOW)
    assert plan is not None
    return plan


def envelope() -> dict[str, str]:
    return {
        "application_version": "0.1.0",
        "archive_id": ARCHIVE_ID,
        "config_fingerprint": FINGERPRINT,
        "hostname": "writer",
        "huggingface_hub_version": "1.24.0",
        "invocation_mode": "interactive",
        "python_version": "3.14.6",
        "run_id": "1" * 32,
    }


def tombstone(layout: ArchiveLayout, transaction_id: TransactionId) -> None:
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    trash = purge_module._trash(layout, transaction_id)
    trash.directory.mkdir(mode=0o700, parents=True)
    repository.refs.rename(trash.refs)
    repository.revisions.rename(trash.revisions)
    repository.manifests.rename(trash.manifests)
    repository.directory.rmdir()


def interrupted(layout: ArchiveLayout, plan, *, committed: bool):
    transaction_id = TransactionId(new_transaction_id())
    transaction = open_transaction(
        layout,
        transaction_id=transaction_id,
        operation="prune",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=FINGERPRINT,
        repository_id=MODEL.id,
        repository_type=MODEL.type,
        commit_sha=plan.current.commit_sha,
    )
    transaction.checkpoint("plan_persisted", plan=plan.model_dump(mode="json"))
    transaction.checkpoint(
        "cache_revision_deleted",
        commit_shas=list(plan.cache_revisions_to_delete),
        expected_freed_bytes=0,
    )
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    trash = purge_module._trash(layout, transaction_id)
    trash.directory.mkdir(mode=0o700, parents=True)
    repository.refs.rename(trash.refs)
    transaction.checkpoint(
        "revision_ref_removed",
        references_absent=str(layout.archive_relative(repository.refs)),
    )
    repository.revisions.rename(trash.revisions)
    transaction.checkpoint(
        "tree_tombstoned",
        tombstoned_tree=str(layout.archive_relative(trash.revisions)),
    )
    repository.manifests.rename(trash.manifests)
    transaction.checkpoint(
        "manifest_tombstoned",
        tombstoned_manifest=str(layout.archive_relative(trash.manifests)),
    )
    repository.directory.rmdir()
    transaction.checkpoint(
        "repository_container_removed",
        repository_absent=str(layout.archive_relative(repository.directory)),
    )
    if committed:
        catalog = publish_catalog(layout, rebuild_catalog(layout, generated_at=NOW))
        transaction.checkpoint(
            "catalog_published", catalog_path=str(layout.archive_relative(catalog))
        )
        transaction.checkpoint("prune_logically_committed", retained=0)
    return transaction


def test_plan_names_every_revision_in_generation_order(layout: ArchiveLayout):
    plan = prepared(layout)

    assert [revision.publication_generation for revision in plan.revisions] == [1, 2]
    assert plan.current.commit_sha == sha(2)
    assert plan.cache_revisions_to_delete == (sha(1), sha(2))
    assert plan.unique_bytes_released_estimate == sum(
        revision.logical_bytes for revision in plan.revisions
    )


def test_plan_refuses_an_unrecognized_repository_entry(layout: ArchiveLayout):
    prepared(layout)
    unknown = RepositoryLayout(archive=layout, identity=MODEL).directory / "operator-note"
    unknown.write_text("preserve me", encoding="utf-8")

    with pytest.raises(RetentionError) as caught:
        plan_purge(layout, MODEL, generated_at=NOW)

    assert [problem.code for problem in caught.value.problems] == ["HFRET001"]
    assert unknown.read_text(encoding="utf-8") == "preserve me"


def test_cache_removal_uses_one_supported_multi_revision_strategy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    calls: list[object] = []

    class Strategy:
        expected_freed_size = 123

        def execute(self):
            calls.append("execute")

    class Cache:
        def delete_revisions(self, *commits):
            calls.append(commits)
            return Strategy()

    monkeypatch.setattr("huggingface_hub.scan_cache_dir", lambda _path: Cache())

    freed = delete_cache_revisions(
        tmp_path,
        (CommitSha(sha(1)), CommitSha(sha(2))),
    )

    assert freed == 123
    assert calls == [(sha(1), sha(2)), "execute"]


def test_apply_removes_publication_and_preserves_audit(
    layout: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    plan = prepared(layout)
    monkeypatch.setattr(purge_module, "delete_cache_revisions", lambda *_args: 0)

    records = apply_purge(layout, plan, envelope=envelope(), now=NOW)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert not repository.directory.exists()
    assert not repository.manifests.exists()
    assert len(records) == 2
    assert {record.reason for record in records} == {"operator_requested_repository_purge"}
    for revision in plan.revisions:
        commit = CommitSha(revision.commit_sha)
        publication = PublicationId(revision.publication_id)
        assert repository.pruned_manifest(commit, publication).is_file()
        assert repository.prune_record(commit, publication).is_file()
    assert list(layout.trash.iterdir()) == []
    journal = next(
        read_journal(layout, path).journal
        for path in layout.transactions.glob("*.json")
        if read_journal(layout, path).journal.operation == "prune"
    )
    assert journal.state == "committed"
    assert [checkpoint.name for checkpoint in journal.checkpoints] == [
        "plan_persisted",
        "cache_revision_deleted",
        "revision_ref_removed",
        "tree_tombstoned",
        "manifest_tombstoned",
        "repository_container_removed",
        "catalog_published",
        "prune_logically_committed",
        "audit_record_written",
        "trash_removed",
        "containers_removed",
        "prune_completed",
    ]


def test_precommit_rollback_restores_every_reference_last(layout: ArchiveLayout):
    plan = prepared(layout)
    transaction_id = TransactionId(new_transaction_id())
    tombstone(layout, transaction_id)

    result = rollback_purge(layout, plan, transaction_id)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert result["restored_revisions"] == 2
    assert repository.current_ref.is_file()
    assert len(list((repository.refs / "revisions").glob("*.json"))) == 2
    assert len(list(repository.revisions.glob("*/*"))) == 2
    assert len(list(repository.manifests.glob("*/*.json"))) == 2
    assert not layout.trash_for(transaction_id).directory.exists()


def test_postcommit_completion_never_republishes(layout: ArchiveLayout):
    plan = prepared(layout)
    transaction_id = TransactionId(new_transaction_id())
    tombstone(layout, transaction_id)

    result = complete_purge(layout, plan, transaction_id)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert result["purged_revisions"] == 2
    assert not repository.directory.exists()
    assert not repository.manifests.exists()
    assert not layout.trash_for(transaction_id).directory.exists()
    for revision in plan.revisions:
        commit = CommitSha(revision.commit_sha)
        publication = PublicationId(revision.publication_id)
        assert repository.pruned_manifest(commit, publication).is_file()


def test_recovery_rolls_an_interrupted_precommit_purge_back(layout: ArchiveLayout):
    purge_plan = prepared(layout)
    interrupted(layout, purge_plan, committed=False)

    recovery = plan_recovery(layout, stale_staging_age_hours=24, now=NOW)
    assert [item.remedy for item in recovery.remediations] == ["rollback_prune"]
    apply_recovery(layout, recovery, envelope=envelope(), started_at=NOW)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert repository.current_ref.is_file()
    assert len(list((repository.refs / "revisions").glob("*.json"))) == 2


def test_recovery_finishes_an_interrupted_postcommit_purge(layout: ArchiveLayout):
    purge_plan = prepared(layout)
    interrupted(layout, purge_plan, committed=True)

    recovery = plan_recovery(layout, stale_staging_age_hours=24, now=NOW)
    assert [item.remedy for item in recovery.remediations] == ["complete_prune"]
    apply_recovery(layout, recovery, envelope=envelope(), started_at=NOW)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert not repository.directory.exists()
    assert not repository.manifests.exists()
    for revision in purge_plan.revisions:
        assert repository.pruned_manifest(
            CommitSha(revision.commit_sha), PublicationId(revision.publication_id)
        ).is_file()
