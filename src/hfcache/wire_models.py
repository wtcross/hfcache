"""Precise existing REST payload projections (decision 145; INV-005/006).

These models describe existing dictionaries; they neither change their serializers
nor acquire policy, archive, credentials or optional transport capabilities.
"""

from typing import Annotated, Literal

from pydantic import BeforeValidator, Field

from hfcache.client_models import (
    ClientOperation,  # noqa: TC001 - Pydantic resolves fields at runtime
)
from hfcache.manifests import RevisionManifest  # noqa: TC001 - Pydantic resolves fields at runtime
from hfcache.models import (
    ArchiveIdField,
    ArchivePath,
    ByteCount,
    CommitShaField,
    Count,
    DurableModel,
    Generation,
    PrunedRevisionRecord,
    PrunePlan,
    PublicationIdField,
    PurgePlan,
    Reference,
    RepositoryIdField,
    RepositoryTypeField,
    RunIdField,
    Sha256,
    TransactionIdField,
    as_tuple,
)
from hfcache.reporting import (  # noqa: TC001 - Pydantic resolves fields at runtime
    FullVerificationSummary,
    RecoveryReport,
    RunReport,
    VerificationReport,
)

Strings = Annotated[tuple[str, ...], BeforeValidator(as_tuple)]
VerificationState = Literal["verified", "unverified", "failed"]


class EmptyPayload(DurableModel):
    """An exact empty failure document, never arbitrary data."""


class VersionPayload(DurableModel):
    application: str
    huggingface_hub: str
    python: str
    transfer_backend: str


class MountPayload(DurableModel):
    exists: bool
    filesystem_type: str | None
    is_mount_point: bool
    read_only: bool | None
    source: str | None


class InspectionPayload(DurableModel):
    adopted_published: bool
    archive_id: ArchiveIdField | None
    archive_root: str
    existing_directories: Strings
    initializable: bool
    leftover_temporaries: Strings
    missing_directories: Strings
    mount: MountPayload
    state: Literal["uninitialized", "partially_initialized", "initialized", "unusable"]
    unknown_entries: Strings
    unknown_entry_count: Count


class ReadyHealthPayload(DurableModel):
    ready: Literal[True]
    policy_valid: Literal[True]
    archive: InspectionPayload


class UnavailableHealthPayload(DurableModel):
    ready: Literal[True]
    policy_valid: Literal[False] | None
    archive: None


class VerificationHealthPayload(DurableModel):
    degraded: bool
    last_full_verification: FullVerificationSummary | None
    outstanding_failures: Count


class AreaFindingPayload(DurableModel):
    age_hours: float
    area: str
    path: str
    stale: bool
    transaction_id: str


class UnreachableArchivePayload(DurableModel):
    archive_id: ArchiveIdField
    root: str
    reachable: Literal[False]
    verification: VerificationHealthPayload


class ReachableArchivePayload(DurableModel):
    archive_id: ArchiveIdField
    root: str
    reachable: Literal[True]
    verification: VerificationHealthPayload
    available_bytes: ByteCount
    available_gib: float
    headroom_bytes: int
    reserve_bytes: ByteCount
    total_bytes: ByteCount
    deferred_cleanup: Count
    findings: Annotated[tuple[AreaFindingPayload, ...], BeforeValidator(as_tuple)]
    unfinished_transactions: Count
    unknown_entries: Strings
    quarantined_bytes: ByteCount


class RepositoryStatusPayload(DurableModel):
    current_commit_sha: CommitShaField | None
    current_publication_generation: Generation | None
    enabled: bool | None
    last_run_status: str | None
    managed: bool
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    requested_revision: str | None
    retained_generations: Annotated[tuple[Generation, ...], BeforeValidator(as_tuple)]
    retained_revisions: Count
    upstream_state: Literal["unknown"]
    verification_state: VerificationState


class StatusPayload(DurableModel):
    archive: ReachableArchivePayload | UnreachableArchivePayload
    repositories: Annotated[tuple[RepositoryStatusPayload, ...], BeforeValidator(as_tuple)]


class RepositoryPayload(DurableModel):
    current_commit_sha: CommitShaField | None
    current_publication_id: PublicationIdField | None
    enabled: bool | None
    managed: bool
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    retained_revisions: Count


class RepositoriesPayload(DurableModel):
    repositories: Annotated[tuple[RepositoryPayload, ...], BeforeValidator(as_tuple)]


class RevisionPayload(DurableModel):
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    commit_sha: CommitShaField
    file_count: Count
    publication_generation: Generation
    publication_id: PublicationIdField
    published_at: str
    total_bytes: ByteCount
    verification_state: VerificationState


class RevisionsPayload(DurableModel):
    revisions: Annotated[tuple[RevisionPayload, ...], BeforeValidator(as_tuple)]


class EstimatePayload(DurableModel):
    estimated_duration_seconds: Annotated[float, Field(ge=0)] | None
    measured_throughput_bytes_per_second: Annotated[float, Field(ge=0)] | None
    mode: Literal["estimate"]
    repositories: Count
    revisions: Count
    storage_maintenance: Literal["undetectable"]
    unique_bytes: ByteCount
    unique_objects: Count
    unreadable_objects: Count


class RunsPayload(DurableModel):
    runs: Annotated[tuple[RunIdField, ...], BeforeValidator(as_tuple)]


class ReportPayload(DurableModel):
    report: RunReport | RecoveryReport | VerificationReport


class ReferencePayload(DurableModel):
    locator_base: Literal["published/"]
    reference: Reference


class ManifestPayload(DurableModel):
    manifest: RevisionManifest
    tree_base: Literal["archive-root/"]


class OperationsPayload(DurableModel):
    operations: Annotated[tuple[ClientOperation, ...], BeforeValidator(as_tuple)]


class OperationPayload(DurableModel):
    operation: ClientOperation


class InstalledValidationPayload(DurableModel):
    config_fingerprint: Sha256
    enabled_repositories: Count
    repositories: Count
    token_source: str


class CandidateValidPayload(InstalledValidationPayload):
    valid: Literal[True]
    syntax_valid: Literal[True]
    authority_compatible: bool | None
    authority_mismatches: Strings
    installed_policy_valid: bool


class CandidateInvalidPayload(DurableModel):
    valid: Literal[False]
    syntax_valid: Literal[False]
    authority_compatible: None
    authority_mismatches: Annotated[tuple[str, ...], BeforeValidator(as_tuple), Field(max_length=0)]
    installed_policy_valid: bool


class PlannedRepositoryPayload(DurableModel):
    enabled: bool
    estimated_new_bytes: ByteCount | None
    file_count: Count | None
    logical_bytes: ByteCount | None
    projected_publication_bytes: ByteCount | None
    publication_mode: Literal["hardlink", "copy"]
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    requested_revision: str
    resolved_commit_sha: CommitShaField | None
    upstream_state: Literal[
        "unknown", "available", "missing", "forbidden", "refused", "unresolvable", "unreachable"
    ]


class PlanPayload(DurableModel):
    repositories: Annotated[tuple[PlannedRepositoryPayload, ...], BeforeValidator(as_tuple)]


class DiagnosticCheckPayload(DurableModel):
    detail: str
    name: str
    outcome: Literal["pass", "fail", "skipped"]


class DiagnosticsPayload(DurableModel):
    checks: Annotated[tuple[DiagnosticCheckPayload, ...], BeforeValidator(as_tuple)]


class PrunePayload(DurableModel):
    plans: Annotated[tuple[PrunePlan, ...], BeforeValidator(as_tuple)]
    applied: Annotated[tuple[PrunedRevisionRecord, ...], BeforeValidator(as_tuple)]


class PurgePayload(DurableModel):
    plans: Annotated[tuple[PurgePlan, ...], BeforeValidator(as_tuple)]
    applied: Annotated[tuple[PrunedRevisionRecord, ...], BeforeValidator(as_tuple)]


class RemediationPayload(DurableModel):
    last_checkpoint: str | None
    operation: str
    reason: str
    remedy: str
    state: str
    transaction_id: TransactionIdField


class RecoveryPlanPayload(DurableModel):
    actionable: Count
    blocked: Count
    plan: Annotated[tuple[RemediationPayload, ...], BeforeValidator(as_tuple)]


class RecoveryAppliedPayload(RecoveryPlanPayload):
    applied: Count
    report: ArchivePath


class QuarantineFilePayload(DurableModel):
    path: str
    size: ByteCount
    sha256: Sha256
    retained_path: ArchivePath


class QuarantinePlanPayload(DurableModel):
    transaction_id: TransactionIdField
    repository: str
    quarantine_path: ArchivePath
    recovery_transaction_id: TransactionIdField
    files: Annotated[tuple[QuarantineFilePayload, ...], BeforeValidator(as_tuple)]
    directories: Strings
    logical_bytes: ByteCount
    already_absent: bool


class QuarantineAppliedPayload(QuarantinePlanPayload):
    removed_files: Count
    removed_directories: Count
    removed_logical_bytes: ByteCount


class QuarantinePayload(DurableModel):
    plans: Annotated[tuple[QuarantinePlanPayload, ...], BeforeValidator(as_tuple)]
    applied: Annotated[tuple[QuarantineAppliedPayload, ...], BeforeValidator(as_tuple)]


class RepairPayload(DurableModel):
    commit_sha: CommitShaField
    grace_expires_at: str
    replacement_publication_id: PublicationIdField
    retired_publication_id: PublicationIdField
    retirement_record: ArchivePath
    transaction_id: TransactionIdField
    verified: Literal[True]


class InitializationPayload(DurableModel):
    adopted_published: bool
    archive_id: ArchiveIdField
    archive_root: str
    created_directories: Strings
    removed_temporaries: Strings
    sentinel: ArchivePath
