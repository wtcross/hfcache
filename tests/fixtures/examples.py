"""One canonical instance of every durable format, built from the models.

These back the golden fixtures in `tests/fixtures/schemas/`. Values match the
worked examples in `docs/schemas.md` wherever that document has one, so a
fixture that stops matching the published example is a real drift and not a
cosmetic one.

Kept as functions rather than module constants so a test that mutates a returned
structure cannot affect another test, and so a model whose validators reject a
value fails inside the test that asked for it.
"""

from datetime import UTC, datetime

from hfcache.api.auth import CredentialClass
from hfcache.api.operations import OperationEvent, OperationReceipt, ResultReference
from hfcache.manifests import (
    DependencyObservation,
    FileEntry,
    FileProvenance,
    HashReuse,
    RepairProvenance,
    RevisionManifest,
    UpstreamIdentifiers,
    VerificationSummary,
)
from hfcache.models import (
    ArchiveSentinel,
    Checkpoint,
    Provenance,
    PrunedRevisionRecord,
    PrunePlan,
    PruneSelection,
    PurgePlan,
    Reference,
    RepairCleanup,
    RepairRetirementRecord,
    RevisionSummary,
    TransactionJournal,
)
from hfcache.reporting import (
    CatalogRevision,
    CurrentRevision,
    Finding,
    FullVerificationSummary,
    OutstandingFailure,
    RepositoriesCatalog,
    RepositoryCatalogEntry,
    RepositoryRunResult,
    RepositoryVerificationEntry,
    RunReport,
    RunTotals,
    VerificationCatalog,
    VerificationReport,
    VerificationRevisionEntry,
    VerificationScope,
)

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
SHA = "0123456789abcdef0123456789abcdef01234567"
OTHER_SHA = "fedcba9876543210fedcba9876543210fedcba98"
PUBLICATION = "9f14c0b7a2d4423fa0e6b1c8d95e3f27"
REPLACEMENT = "1a2b3c4d5e6f70819a2b3c4d5e6f7081"
TRANSACTION = "e5f60718293a4b5c6d7e8f90a1b2c3d4"
RUN = "4c1e8a55b0d24f1e9a3c7d2b6f80e114"
PLAN = "b71d0e4a3c8f42d190a6c5b3e7f18d24"
FINGERPRINT = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
DIGEST = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
OTHER_DIGEST = "5f2c8a1d0b7e4936ac5182d4e7f0913b6c8d5a2f1e0b9c8d7a6f5e4d3c2b1a09"
MANIFEST_DIGEST = "7d2b6f80e1144c1e8a55b0d24f1e9a3c7d2b6f80e1144c1e8a55b0d24f1e9a3c"

REPOSITORY_ID = "organization/model-name"
TREE = f"published/repos/models/{REPOSITORY_ID}/revisions/{SHA}/{PUBLICATION}"
MANIFEST_PATH = f"published/manifests/models/{REPOSITORY_ID}/{SHA}/{PUBLICATION}.json"
REFERENCE_TREE = f"repos/models/{REPOSITORY_ID}/revisions/{SHA}/{PUBLICATION}"
REFERENCE_MANIFEST = f"manifests/models/{REPOSITORY_ID}/{SHA}/{PUBLICATION}.json"


def at(text: str) -> datetime:
    """Parse a durable timestamp for use as a model input."""
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)


def sentinel() -> ArchiveSentinel:
    """`docs/schemas.md` §2."""
    return ArchiveSentinel(
        archive_id=ARCHIVE_ID,
        created_at=at("2026-07-24T20:57:31.123456Z"),
        created_by=Provenance(
            application_version="1.0.0", hostname="hfcachewriter.lab.example.com"
        ),
    )


def manifest() -> RevisionManifest:
    """`docs/schemas.md` §3, extended with a second file to exercise ordering."""
    return RevisionManifest(
        application_version="1.0.0",
        commit_sha=SHA,
        dependencies=(
            DependencyObservation(
                confidence="high",
                declared=False,
                detected_id="meta-llama/Llama-3.1-8B",
                managed=False,
                source_field="base_model",
                source_file="README.md",
            ),
        ),
        download_completed_at=at("2026-07-24T20:41:02.556000Z"),
        download_started_at=at("2026-07-24T20:38:17.004000Z"),
        file_count=2,
        files=(
            FileEntry(
                path="config.json",
                provenance=FileProvenance(
                    cache_root="canonical",
                    hash_reused_from=None,
                    hashed=True,
                    source="hub_download",
                ),
                sha256=DIGEST,
                size=812,
                upstream=UpstreamIdentifiers(
                    git_oid="b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0",
                    lfs_sha256=None,
                    xet_hash=None,
                ),
            ),
            FileEntry(
                path="model.safetensors",
                provenance=FileProvenance(
                    cache_root="canonical",
                    hash_reused_from=HashReuse(commit_sha=OTHER_SHA, publication_id=REPLACEMENT),
                    hashed=False,
                    source="cache_reuse",
                ),
                sha256=OTHER_DIGEST,
                size=486123092,
                upstream=UpstreamIdentifiers(
                    git_oid=None,
                    lfs_sha256=OTHER_DIGEST,
                    xet_hash=None,
                ),
            ),
        ),
        first_observed_at=at("2026-07-24T20:38:11.882000Z"),
        hub_endpoint="https://huggingface.co",
        huggingface_hub_version="1.24.0",
        publication_generation=1,
        publication_id=PUBLICATION,
        publication_mode="hardlink",
        published_at=at("2026-07-24T20:41:44.310000Z"),
        python_version="3.14.6",
        repair=None,
        repository_id=REPOSITORY_ID,
        repository_type="model",
        requested_revision="main",
        total_bytes=486123904,
        tree=TREE,
        verification=VerificationSummary(
            algorithm="sha256",
            completeness_checked=True,
            hashed_bytes=812,
            hashed_objects=1,
            outcome="verified",
            reused_digests=1,
            verified_at=at("2026-07-24T20:41:39.771000Z"),
        ),
        verified_at=at("2026-07-24T20:41:39.771000Z"),
    )


def repair_manifest() -> RevisionManifest:
    """A repair instance: same expected content, new publication id (`FS-07`)."""
    original = manifest()
    return original.model_copy(
        update={
            "publication_id": REPLACEMENT,
            "tree": TREE.replace(PUBLICATION, REPLACEMENT),
            "repair": RepairProvenance(
                reason="HFVER001 digest mismatch on model.safetensors",
                repair_of=PUBLICATION,
                repair_of_manifest=MANIFEST_PATH,
                repaired_at=at("2026-07-25T09:14:02.000000Z"),
                transaction_id=TRANSACTION,
            ),
        }
    )


def reference() -> Reference:
    """`docs/schemas.md` §4.1 — the only published-relative paths in the archive."""
    return Reference(
        commit_sha=SHA,
        manifest=REFERENCE_MANIFEST,
        publication_generation=1,
        publication_id=PUBLICATION,
        repository_id=REPOSITORY_ID,
        repository_type="model",
        tree=REFERENCE_TREE,
        updated_at=at("2026-07-24T20:41:44.902000Z"),
    )


def repositories_catalog() -> RepositoriesCatalog:
    """`docs/schemas.md` §5.1."""
    return RepositoriesCatalog(
        generated_at=at("2026-07-24T20:41:45.010000Z"),
        repositories=(
            RepositoryCatalogEntry(
                current=CurrentRevision(
                    commit_sha=SHA, publication_generation=1, publication_id=PUBLICATION
                ),
                enabled=True,
                first_published_at=at("2026-07-24T20:41:44.310000Z"),
                last_published_at=at("2026-07-24T20:41:44.310000Z"),
                last_run_status="published",
                last_seen_at=at("2026-07-24T20:41:44.310000Z"),
                managed=True,
                repository_id=REPOSITORY_ID,
                repository_type="model",
                requested_revision="main",
                revisions=(
                    CatalogRevision(
                        commit_sha=SHA,
                        file_count=2,
                        publication_generation=1,
                        publication_id=PUBLICATION,
                        published_at=at("2026-07-24T20:41:44.310000Z"),
                        total_bytes=486123904,
                        verification_state="verified",
                    ),
                ),
                upstream_state="ok",
                warnings=("HFDEP001",),
            ),
        ),
    )


def verification_catalog() -> VerificationCatalog:
    """`docs/schemas.md` §5.2."""
    return VerificationCatalog(
        generated_at=at("2026-07-24T21:10:03.400000Z"),
        last_full_verification=FullVerificationSummary(
            completed_at=at("2026-07-24T21:09:58.220000Z"),
            duration_seconds=612.4,
            outcome="clean",
            report=f"runs/20260724T205931Z-{RUN}.json",
            started_at=at("2026-07-24T20:59:45.800000Z"),
            throughput_bytes_per_second=794000000.0,
            unique_bytes=486123904,
            unique_objects=14,
        ),
        outstanding_failures=(),
        repositories=(
            RepositoryVerificationEntry(
                repository_id=REPOSITORY_ID,
                repository_type="model",
                revisions=(
                    VerificationRevisionEntry(
                        commit_sha=SHA,
                        outcome="clean",
                        publication_id=PUBLICATION,
                        verified_at=at("2026-07-24T21:09:58.220000Z"),
                    ),
                ),
            ),
        ),
    )


def degraded_verification_catalog() -> VerificationCatalog:
    """The same catalog once a finding is outstanding."""
    return verification_catalog().model_copy(
        update={
            "outstanding_failures": (
                OutstandingFailure(
                    commit_sha=SHA,
                    first_seen_at=at("2026-07-24T21:09:58.220000Z"),
                    kind="digest_mismatch",
                    path="model.safetensors",
                    publication_id=PUBLICATION,
                    repository_id=REPOSITORY_ID,
                    repository_type="model",
                ),
            )
        }
    )


def run_report() -> RunReport:
    """`docs/schemas.md` §6."""
    return RunReport(
        application_version="1.0.0",
        archive_id=ARCHIVE_ID,
        command="sync",
        completed_at=at("2026-07-24T20:41:46.002000Z"),
        config_fingerprint=FINGERPRINT,
        errors=(),
        exit_code=0,
        hostname="hfcachewriter.lab.example.com",
        huggingface_hub_version="1.24.0",
        invocation_mode="systemd",
        outcome="success",
        python_version="3.14.6",
        repositories=(
            RepositoryRunResult(
                downloaded_bytes=486123904,
                duration_seconds=207.3,
                errors=(),
                file_count=2,
                hashed_bytes=486123904,
                publication_generation=1,
                publication_id=PUBLICATION,
                pruned=None,
                repository_id=REPOSITORY_ID,
                repository_type="model",
                requested_revision="main",
                resolved_commit_sha=SHA,
                reused_bytes=0,
                status="published",
                warnings=(),
            ),
        ),
        run_id=RUN,
        started_at=at("2026-07-24T20:38:11.500000Z"),
        totals=RunTotals(
            downloaded_bytes=486123904,
            hashed_bytes=486123904,
            published_bytes=486123904,
            pruned_logical_bytes=0,
            reused_bytes=0,
            xet_cache_peak_bytes=12884901888,
        ),
        warnings=(),
    )


def verification_report() -> VerificationReport:
    """`docs/schemas.md` §7, in the failing state the example shows."""
    return VerificationReport(
        application_version="1.0.0",
        archive_id=ARCHIVE_ID,
        command="verify --full",
        completed_at=at("2026-07-24T21:09:58.220000Z"),
        config_fingerprint=FINGERPRINT,
        errors=("HFVER001",),
        exit_code=40,
        findings=(
            Finding(
                commit_sha=SHA,
                expected=DIGEST,
                kind="digest_mismatch",
                observed=OTHER_DIGEST,
                path="model.safetensors",
                publication_id=PUBLICATION,
                repository_id=REPOSITORY_ID,
                repository_type="model",
            ),
        ),
        hostname="hfcachewriter.lab.example.com",
        huggingface_hub_version="1.24.0",
        invocation_mode="interactive",
        mode="full",
        outcome="failed",
        python_version="3.14.6",
        run_id=RUN,
        scope=VerificationScope(
            repositories=2, revisions=7, unique_bytes_read=486123904, unique_objects_read=14
        ),
        started_at=at("2026-07-24T20:59:45.800000Z"),
        throughput_bytes_per_second=794000000.0,
        verification_outcome="failed",
        warnings=(),
    )


def prune_plan() -> PrunePlan:
    """`docs/schemas.md` §8: six retained, the lowest generation selected."""
    retained = tuple(
        RevisionSummary(commit_sha=sha, publication_generation=generation)
        for generation, sha in enumerate(
            (
                SHA,
                "1234567890abcdef1234567890abcdef12345678",
                "2345678901abcdef2345678901abcdef23456789",
                "3456789012abcdef3456789012abcdef3456789a",
                "456789013abcdef0456789013abcdef0456789ab",
                OTHER_SHA,
            ),
            start=1,
        )
    )
    return PrunePlan(
        cache_revisions_to_delete=(SHA,),
        current=RevisionSummary(commit_sha=OTHER_SHA, publication_generation=6),
        generated_at=at("2026-07-24T21:20:00.000000Z"),
        plan_id=PLAN,
        reason="sixth_unique_revision_published",
        repository_id=REPOSITORY_ID,
        repository_type="model",
        retained=retained,
        selected=PruneSelection(
            commit_sha=SHA,
            file_count=2,
            logical_bytes=486123904,
            manifest=MANIFEST_PATH,
            publication_generation=1,
            publication_id=PUBLICATION,
            tree=TREE,
        ),
        unique_bytes_released_estimate=486123904,
    )


def purge_plan() -> PurgePlan:
    """`docs/schemas.md` §8.1: one complete unmanaged repository."""
    selected = prune_plan().selected
    return PurgePlan(
        cache_revisions_to_delete=(selected.commit_sha,),
        current=RevisionSummary(
            commit_sha=selected.commit_sha,
            publication_generation=selected.publication_generation,
        ),
        generated_at=at("2026-08-15T21:00:00.000000Z"),
        plan_id=PLAN,
        reason="operator_requested_repository_purge",
        repository_id=REPOSITORY_ID,
        repository_type="model",
        revisions=(selected,),
        unique_bytes_released_estimate=selected.logical_bytes,
    )


def pruned_record() -> PrunedRevisionRecord:
    """`docs/schemas.md` §9.1."""
    plan = prune_plan()
    return PrunedRevisionRecord(
        commit_sha=SHA,
        file_count=2,
        logical_bytes=486123904,
        manifest_archived_at=at("2026-07-24T21:20:04.000000Z"),
        plan_id=PLAN,
        publication_generation=1,
        publication_id=PUBLICATION,
        pruned_at=at("2026-07-24T21:20:05.000000Z"),
        reason="sixth_unique_revision_published",
        repository_id=REPOSITORY_ID,
        repository_type="model",
        retained_after=plan.retained[1:],
        transaction_id=TRANSACTION,
        tree=TREE,
    )


def repair_retirement() -> RepairRetirementRecord:
    """`docs/schemas.md` §9.2."""
    return RepairRetirementRecord(
        cleanup=RepairCleanup(completed_at=None, quarantine_path=None, state="pending"),
        commit_sha=SHA,
        evidence=("HFVER001 model.safetensors",),
        grace_expires_at=at("2026-08-01T09:14:02.000000Z"),
        publication_generation=1,
        reason="HFVER001 digest mismatch on model.safetensors",
        replacement_publication_id=REPLACEMENT,
        replacement_tree=TREE.replace(PUBLICATION, REPLACEMENT),
        repository_id=REPOSITORY_ID,
        repository_type="model",
        retired_at=at("2026-07-25T09:14:02.000000Z"),
        retired_publication_id=PUBLICATION,
        retired_tree=TREE,
        transaction_id=TRANSACTION,
    )


def journal() -> TransactionJournal:
    """`docs/schemas.md` §10."""
    return TransactionJournal(
        archive_id=ARCHIVE_ID,
        checkpoints=(
            Checkpoint(
                evidence={"file_count": 2, "path": TREE},
                name="revision_tree_renamed",
                recorded_at=at("2026-07-24T20:41:44.310000Z"),
                sequence=1,
            ),
            Checkpoint(
                evidence={"path": MANIFEST_PATH, "sha256": MANIFEST_DIGEST},
                name="manifest_published",
                recorded_at=at("2026-07-24T20:41:44.610000Z"),
                sequence=2,
            ),
        ),
        commit_sha=SHA,
        completed_at=None,
        config_fingerprint=FINGERPRINT,
        created_at=at("2026-07-24T20:38:11.600000Z"),
        error=None,
        last_checkpoint_at=at("2026-07-24T20:41:44.610000Z"),
        operation="publication",
        publication_id=PUBLICATION,
        repository_id=REPOSITORY_ID,
        repository_type="model",
        run_id=RUN,
        state="open",
        transaction_id=TRANSACTION,
    )


def operation_event() -> OperationEvent:

    return OperationEvent(
        sequence=1,
        at=at("2026-10-17T12:00:00.000000Z"),
        kind="operation.admitted",
        message="Admission recorded",
    )


def operation_result_reference() -> ResultReference:

    return ResultReference(operation_id="a" * 32, sha256="b" * 64, bytes=512)


def operation_receipt() -> OperationReceipt:

    return OperationReceipt(
        operation_id="a" * 32,
        principal=CredentialClass.REST_WRITER,
        key_digest="c" * 64,
        request_digest="d" * 64,
        route="/api/v1/sync",
        archive_id=ARCHIVE_ID,
        config_fingerprint=FINGERPRINT,
        state="queued",
        created_at=at("2026-10-17T12:00:00.000000Z"),
        updated_at=at("2026-10-17T12:00:00.000000Z"),
        events=(operation_event(),),
        next_event_sequence=2,
    )


EXAMPLES = {
    "operation-event": operation_event,
    "operation-result-reference": operation_result_reference,
    "operation-receipt": operation_receipt,
    "journal": journal,
    "manifest": manifest,
    "prune-plan": prune_plan,
    "pruned-record": pruned_record,
    "purge-plan": purge_plan,
    "reference": reference,
    "repair-manifest": repair_manifest,
    "repair-retirement": repair_retirement,
    "repositories-catalog": repositories_catalog,
    "run-report": run_report,
    "sentinel": sentinel,
    "verification-catalog": verification_catalog,
    "verification-catalog-degraded": degraded_verification_catalog,
    "verification-report": verification_report,
}
"""Every durable format, by fixture name (`docs/schemas.md` §11)."""
