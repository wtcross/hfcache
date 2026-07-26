"""Publishing a revision, and the derived view it produces — plan §13.2, §7.3.

This is the transaction the whole design is arranged around, so what is asserted
here is mostly *ordering*: that each atomic act is followed by the checkpoint
naming it, in the sequence §7.3 fixes, and that at every point between them the
archive is in a state §7.3's crash matrix has a resolution for.

The revisions here are published by calling `publish_revision` itself rather than
by writing files that look like its output. That is deliberate — a fixture that
fabricated a published tree would let the catalog tests pass against a layout the
publisher never produces.
"""

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from hfcache.archive import initialize_archive
from hfcache.config import RepositoryConfig
from hfcache.errors import SynchronizationError
from hfcache.hub import TreeEntry
from hfcache.identity import (
    CommitSha,
    RepositoryIdentity,
    new_publication_id,
    new_run_id,
    new_transaction_id,
)
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import (
    create_staging,
    discard_staging,
    next_generation,
    publish_catalog,
    published_repositories,
    read_reference,
    rebuild_catalog,
    retained_references,
)
from hfcache.reporting import RepositoriesCatalog
from hfcache.storage import parse_mount_table
from hfcache.sync import (
    Timeline,
    build_manifest,
    hash_snapshot,
    publish_revision,
    snapshot_paths,
)
from hfcache.transactions import open_transaction

if TYPE_CHECKING:
    from pathlib import Path

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
FINGERPRINT = "b" * 64

MODEL = RepositoryIdentity.of("model", "organization/model-name")
DATASET = RepositoryIdentity.of("dataset", "organization/dataset-name")

SHA_A = "1111111111111111111111111111111111111111"
SHA_B = "2222222222222222222222222222222222222222"
SHA_C = "3333333333333333333333333333333333333333"

NOW = datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC)
TIMELINE = Timeline(
    first_observed_at=NOW,
    download_started_at=NOW,
    download_completed_at=NOW,
    verified_at=NOW,
    published_at=NOW,
)

PAYLOAD = b"the bytes of one repository file"
TREE = (TreeEntry(path="config.json", size=len(PAYLOAD)),)


def nfs_line(root: str) -> str:
    return f"457 47 0:68 / {root} rw,relatime shared:488 - nfs4 nas:/mnt/tank/hf rw,vers=4.2\n"


@pytest.fixture
def layout(tmp_path: Path) -> ArchiveLayout:
    """A real initialized archive on a temporary directory."""
    root = tmp_path / "archive"
    root.mkdir()
    built = ArchiveLayout(root=root)
    initialize_archive(
        built, archive_id=ARCHIVE_ID, table=parse_mount_table(nfs_line(os.path.realpath(root)))
    )
    return built


@pytest.fixture
def snapshot(layout: ArchiveLayout) -> Path:
    """A downloaded snapshot in the private cache, laid out the way one is."""
    blob = layout.hub_cache / "blobs" / "abcdef"
    blob.parent.mkdir(parents=True)
    blob.write_bytes(PAYLOAD)
    path = layout.hub_cache / "snapshots" / SHA_A
    path.mkdir(parents=True)
    (path / "config.json").symlink_to(blob)
    return path


def publish(  # noqa: PLR0913 - a test helper standing in for the caller `SYNC-001` will be
    layout: ArchiveLayout,
    snapshot: Path,
    *,
    identity: RepositoryIdentity = MODEL,
    commit_sha: str = SHA_A,
    generation: int | None = None,
    configured=None,
):
    """Publish one revision through the real code path, and return its outcome."""
    transaction_id = new_transaction_id()
    transaction = open_transaction(
        layout,
        transaction_id=transaction_id,
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=FINGERPRINT,
        repository_id=identity.id,
        repository_type=identity.type,
    )
    staging = create_staging(layout, transaction_id)
    transaction.checkpoint(
        "staging_created", staging_path=str(layout.archive_relative(staging.directory))
    )
    transaction.checkpoint("download_completed", cache_revision=commit_sha)
    hashed = hash_snapshot(snapshot, TREE, identity=identity)
    transaction.checkpoint("content_hashed", hashed_objects=hashed.hashed_objects)

    repository = RepositoryLayout(archive=layout, identity=identity)
    manifest = build_manifest(
        identity=identity,
        requested_revision="main",
        commit_sha=CommitSha(commit_sha),
        publication_id=new_publication_id(),
        publication_generation=(
            generation if generation is not None else next_generation(layout, identity)
        ),
        publication_mode="hardlink",
        tree=TREE,
        hashed=hashed,
        layout=repository,
        hub_endpoint="https://huggingface.co",
        timeline=TIMELINE,
    )
    outcome = publish_revision(
        layout,
        transaction,
        identity=identity,
        snapshot=snapshot,
        manifest=manifest,
        staging=staging,
        publication_mode="hardlink",
        cache_root=layout.hub_cache,
        configured=configured or {},
    )
    # Checkpoint 10's act and then the checkpoint, exactly as `sync._ingest`
    # does it (decision 56).
    discard_staging(layout, transaction_id)
    transaction.checkpoint(
        "publication_committed",
        state="committed",
        staging_absent=str(layout.archive_relative(staging.directory)),
    )
    transaction.commit()
    return outcome, transaction


def names(transaction) -> list[str]:
    return [checkpoint.name for checkpoint in transaction.journal.checkpoints]


# --------------------------------------------------------------------------- #
# The publication transaction (§7.3)
# --------------------------------------------------------------------------- #


def test_a_published_revision_is_a_tree_a_manifest_and_two_references(layout, snapshot):
    outcome, _ = publish(layout, snapshot)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert (outcome.tree / "config.json").read_bytes() == PAYLOAD
    assert repository.manifest(outcome.commit_sha, outcome.publication_id).is_file()
    assert repository.revision_ref(outcome.commit_sha).is_file()
    assert repository.current_ref.is_file()


def test_the_checkpoints_are_recorded_in_the_order_7_3_fixes(layout, snapshot):
    _, transaction = publish(layout, snapshot)

    assert names(transaction) == [
        "staging_created",
        "download_completed",
        "content_hashed",
        "staging_built",
        "revision_tree_renamed",
        "manifest_published",
        "revision_ref_published",
        "current_ref_replaced",
        "catalog_rebuilt",
        "publication_committed",
    ]
    assert transaction.journal.state == "committed"


def test_the_published_file_is_the_same_inode_as_the_cache_blob(layout, snapshot):
    # Hardlink publication: no second physical copy (`AD-11`), which is what
    # makes `projected_publication_bytes` zero in this mode.
    outcome, _ = publish(layout, snapshot)

    assert (outcome.tree / "config.json").samefile(snapshot / "config.json")


def test_the_manifest_waits_in_staging_before_the_tree_is_renamed(layout, snapshot):
    # §7.3's reason a crash between checkpoints 5 and 6 is recoverable: the
    # published tree can be validated against a manifest that already exists.
    _, transaction = publish(layout, snapshot)

    built = next(c for c in transaction.journal.checkpoints if c.name == "staging_built")
    renamed = next(c for c in transaction.journal.checkpoints if c.name == "revision_tree_renamed")
    assert built.sequence < renamed.sequence
    # No `_path` suffix: checkpoint 10 discards the staging area, so the key is
    # re-observable by a person and not asserted to still exist (decision 56).
    assert "pending_manifest" in built.evidence


def test_staging_is_discarded_when_the_publication_commits(layout, snapshot):
    """Decision 56. A directory under `.store/staging` is how
    `reconcile_storage` recognises unfinished work, so one left behind by a
    committed publication reports a finished revision as outstanding — and warns
    `HFWRN004` about it once it ages past the configured staleness."""
    outcome, transaction = publish(layout, snapshot)

    assert list(layout.staging.iterdir()) == []
    assert outcome.tree.is_dir(), "the tree it published is untouched"
    committed = next(
        c for c in transaction.journal.checkpoints if c.name == "publication_committed"
    )
    assert committed.evidence["staging_absent"].startswith(".store/staging/")


def test_each_checkpoint_carries_the_evidence_7_3_names(layout, snapshot):
    _, transaction = publish(layout, snapshot)

    evidence = {c.name: c.evidence for c in transaction.journal.checkpoints}
    assert evidence["revision_tree_renamed"]["file_count"] == 1
    assert evidence["manifest_published"]["manifest_sha256"]
    assert evidence["revision_ref_published"]["publication_id"]
    assert evidence["catalog_rebuilt"]["catalog_sha256"]


def test_the_first_publication_records_that_there_was_no_previous_current(layout, snapshot):
    _, transaction = publish(layout, snapshot)

    switch = next(c for c in transaction.journal.checkpoints if c.name == "current_ref_replaced")
    assert switch.evidence["previous"] is None
    assert switch.evidence["new"][0] == SHA_A


def test_a_later_publication_records_the_pair_it_replaced(layout, snapshot):
    # So recovery can tell a completed switch from one that never happened.
    first, _ = publish(layout, snapshot)
    second, transaction = publish(layout, snapshot, commit_sha=SHA_B)

    switch = next(c for c in transaction.journal.checkpoints if c.name == "current_ref_replaced")
    assert switch.evidence["previous"] == [first.commit_sha, first.publication_id]
    assert switch.evidence["new"] == [second.commit_sha, second.publication_id]


def test_the_references_resolve_to_what_they_name(layout, snapshot):
    # `FS-10`, enforced at the point of each write: a reference whose tree or
    # manifest is not durable is refused rather than published.
    publish(layout, snapshot)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.current_ref)
    assert (layout.published / str(reference.tree)).is_dir()
    assert (layout.published / str(reference.manifest)).is_file()


def test_the_published_tree_contains_exactly_what_the_manifest_lists(layout, snapshot):
    outcome, _ = publish(layout, snapshot)

    assert list(snapshot_paths(outcome.tree)) == [entry.path for entry in outcome.manifest.files]


def test_a_second_revision_leaves_the_first_published(layout, snapshot):
    # Nothing about publishing a newer revision removes an older one; that is
    # retention's job, and only after a successful publication (§15.1).
    first, _ = publish(layout, snapshot)

    second, _ = publish(layout, snapshot, commit_sha=SHA_B)

    assert first.tree.is_dir()
    assert second.tree.is_dir()
    assert len(retained_references(layout, MODEL)) == 2


def test_publishing_the_same_instance_twice_is_refused(layout, snapshot):
    # `FS-05`: a published instance directory is immutable. `promote_staging`
    # refuses an existing destination explicitly rather than trusting
    # `rename(2)`, which replaces an *empty* directory silently.
    outcome, _ = publish(layout, snapshot)
    transaction_id = new_transaction_id()
    transaction = open_transaction(
        layout,
        transaction_id=transaction_id,
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=FINGERPRINT,
    )
    staging = create_staging(layout, transaction_id)
    transaction.checkpoint("staging_created", staging_path="x")
    transaction.checkpoint("download_completed", cache_revision=SHA_A)
    transaction.checkpoint("content_hashed", hashed_objects=1)

    with pytest.raises(SynchronizationError):
        publish_revision(
            layout,
            transaction,
            identity=MODEL,
            snapshot=snapshot,
            manifest=outcome.manifest,
            staging=staging,
            publication_mode="hardlink",
            cache_root=layout.hub_cache,
        )


# --------------------------------------------------------------------------- #
# Generations (plan §13.2 step 11, §15.1)
# --------------------------------------------------------------------------- #


def test_the_first_generation_is_one(layout):
    assert next_generation(layout, MODEL) == 1


def test_the_next_generation_is_one_past_the_highest_not_one_past_the_count(layout, snapshot):
    # A prune removes the oldest revision and its reference, so counting would
    # reissue a generation a pruned revision already held.
    publish(layout, snapshot, generation=4)
    publish(layout, snapshot, commit_sha=SHA_B, generation=9)

    assert next_generation(layout, MODEL) == 10


def test_generations_are_assigned_in_publication_order(layout, snapshot):
    publish(layout, snapshot)
    publish(layout, snapshot, commit_sha=SHA_B)
    publish(layout, snapshot, commit_sha=SHA_C)

    references = retained_references(layout, MODEL)
    assert [reference.publication_generation for reference in references] == [1, 2, 3]
    assert [reference.commit_sha for reference in references] == [SHA_A, SHA_B, SHA_C]


def test_generations_are_per_repository(layout, snapshot):
    publish(layout, snapshot)
    publish(layout, snapshot, identity=DATASET)

    assert next_generation(layout, DATASET) == 2
    assert retained_references(layout, DATASET)[0].publication_generation == 1


# --------------------------------------------------------------------------- #
# The derived catalog (`FS-16`, plan §13.2 step 19)
# --------------------------------------------------------------------------- #


def test_published_repositories_are_discovered_from_disk(layout, snapshot):
    # Removing a repository from configuration never deletes its archive
    # (`AD-06`), so the published set and the configured set are different sets.
    publish(layout, snapshot)
    publish(layout, snapshot, identity=DATASET)

    assert published_repositories(layout) == (DATASET, MODEL)


def test_a_directory_that_is_not_a_repository_name_is_skipped(layout):
    (layout.repos / "models" / "not a namespace" / "name").mkdir(parents=True)

    assert published_repositories(layout) == ()


def test_an_archive_with_nothing_published_has_no_repositories(layout):
    assert published_repositories(layout) == ()


def test_the_catalog_is_derived_from_manifests_and_references(layout, snapshot):
    outcome, _ = publish(layout, snapshot)

    catalog = rebuild_catalog(layout, generated_at=NOW)

    entry = catalog.repositories[0]
    assert entry.repository_id == MODEL.id
    assert [revision.commit_sha for revision in entry.revisions] == [SHA_A]
    assert entry.revisions[0].file_count == outcome.manifest.file_count
    assert entry.revisions[0].total_bytes == outcome.manifest.total_bytes
    assert entry.current is not None
    assert entry.current.commit_sha == SHA_A


def test_the_catalog_is_rebuilt_by_every_publication(layout, snapshot):
    publish(layout, snapshot)

    publish(layout, snapshot, commit_sha=SHA_B)

    catalog = RepositoriesCatalog.model_validate_json(
        layout.repositories_catalog.read_text(encoding="utf-8")
    )
    entry = catalog.repositories[0]
    assert [revision.commit_sha for revision in entry.revisions] == [SHA_A, SHA_B]
    assert entry.current is not None
    assert entry.current.commit_sha == SHA_B


def test_a_repository_no_longer_configured_is_unmanaged_and_kept(layout, snapshot):
    # `AD-06`: removing an entry from a file is not a request to delete data.
    publish(layout, snapshot)

    entry = rebuild_catalog(layout, generated_at=NOW).repositories[0]

    assert entry.managed is False
    assert entry.enabled is None
    assert entry.revisions


def test_a_configured_repository_carries_its_configured_state(layout, snapshot):
    configured = {MODEL.selector: RepositoryConfig(id=MODEL.id, type="model", revision="v2.0")}
    publish(layout, snapshot, configured=configured)

    entry = rebuild_catalog(layout, configured=configured, generated_at=NOW).repositories[0]

    assert entry.managed is True
    assert entry.enabled is True
    assert entry.requested_revision == "v2.0"


def test_the_catalog_is_sorted_by_type_then_id(layout, snapshot):
    publish(layout, snapshot)
    publish(layout, snapshot, identity=DATASET)

    catalog = rebuild_catalog(layout, generated_at=NOW)

    assert [(e.repository_type, e.repository_id) for e in catalog.repositories] == [
        ("dataset", DATASET.id),
        ("model", MODEL.id),
    ]


def test_the_catalog_is_replaced_atomically_and_reads_back(layout, snapshot):
    publish(layout, snapshot)
    catalog = rebuild_catalog(layout, generated_at=NOW)

    path = publish_catalog(layout, catalog)

    assert path == layout.repositories_catalog
    assert RepositoriesCatalog.model_validate_json(path.read_text(encoding="utf-8")) == catalog


def test_a_retained_revision_with_no_current_ref_is_still_catalogued(layout, snapshot):
    # §7.3's "after 7, before 8": the revision is retained and discoverable but
    # not current. The catalog has to describe that rather than refuse it, since
    # recovery reads the catalog while deciding how to finish the switch.
    publish(layout, snapshot)
    RepositoryLayout(archive=layout, identity=MODEL).current_ref.unlink()

    entry = rebuild_catalog(layout, generated_at=NOW).repositories[0]

    assert entry.current is None
    assert [revision.commit_sha for revision in entry.revisions] == [SHA_A]


def test_the_catalog_can_always_be_rebuilt_after_being_destroyed(layout, snapshot):
    # `FS-16`: derived state, never authority. Deleting it loses nothing.
    publish(layout, snapshot)
    before = rebuild_catalog(layout, generated_at=NOW)
    layout.repositories_catalog.unlink()

    assert rebuild_catalog(layout, generated_at=NOW) == before
