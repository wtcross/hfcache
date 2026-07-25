"""Run reports, verification reports, and the derived catalog.

`docs/schemas.md` §5, §6, and §7. These are the artifacts an operator reads to
answer "what happened" and "is the archive healthy", so the models here carry the
consistency rules that make those answers trustworthy — an `outcome` always
agrees with its `exit_code`, and a report that claims success while listing
errors cannot be constructed.

The catalog is derived state (`FS-16`). It can always be rebuilt from immutable
manifests plus references, and where it disagrees with them, they win. Nothing
here treats it as authority; it exists so `status` and `list` answer without
walking the whole archive.
"""

from typing import Annotated, Literal, Self, final

from pydantic import BeforeValidator, Field, model_validator

from hfcache.errors import ExitCode
from hfcache.models import (
    ArchivePath,
    ByteCount,
    CommitShaField,
    Count,
    DurableModel,
    Generation,
    PublicationIdField,
    RepositoryIdField,
    RepositoryPath,
    RepositoryTypeField,
    RunIdField,
    Sha256,
    Timestamp,
    VersionedModel,
    as_tuple,
)

__all__ = [
    "CatalogRevision",
    "CurrentRevision",
    "Finding",
    "FullVerificationSummary",
    "OutstandingFailure",
    "PrunedRevision",
    "RepositoriesCatalog",
    "RepositoryCatalogEntry",
    "RepositoryRunResult",
    "RepositoryVerificationEntry",
    "RunReport",
    "RunTotals",
    "VerificationCatalog",
    "VerificationReport",
    "VerificationRevisionEntry",
]

Seconds = Annotated[float, Field(ge=0.0)]
Rate = Annotated[float, Field(ge=0.0)]

_SUCCESSFUL_OUTCOMES = frozenset({"success", "success_with_warnings"})


# --------------------------------------------------------------------------- #
# §6 Run report
# --------------------------------------------------------------------------- #


@final
class PrunedRevision(DurableModel):
    """The revision a successful publication rotated out, if any."""

    commit_sha: CommitShaField
    logical_bytes: ByteCount
    publication_generation: Generation


@final
class RepositoryRunResult(DurableModel):
    """What one run did to one repository.

    `status` distinguishes outcomes that look alike from outside but mean
    different things to an operator. `skipped` means upstream had not moved;
    `ref_moved_to_retained_revision` means it moved back to something already
    held, so no bytes were fetched but the current pointer changed.
    """

    downloaded_bytes: ByteCount = 0
    duration_seconds: Seconds = 0.0
    errors: Annotated[tuple[str, ...], BeforeValidator(as_tuple)] = ()
    file_count: Count = 0
    hashed_bytes: ByteCount = 0
    publication_generation: Generation | None = None
    publication_id: PublicationIdField | None = None
    pruned: PrunedRevision | None = None
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    requested_revision: str
    resolved_commit_sha: CommitShaField | None = None
    reused_bytes: ByteCount = 0
    status: Literal[
        "skipped",
        "ref_moved_to_retained_revision",
        "published",
        "completed_with_warnings",
        "failed",
        "disabled",
    ]
    warnings: Annotated[tuple[str, ...], BeforeValidator(as_tuple)] = ()

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.status == "published" and self.publication_id is None:
            message = "a published repository names the instance it published"
            raise ValueError(message)
        if self.status == "failed" and not self.errors:
            message = "a failed repository records at least one error code"
            raise ValueError(message)
        if self.status == "completed_with_warnings" and not self.warnings:
            message = "completed_with_warnings records at least one warning code"
            raise ValueError(message)
        return self


@final
class RunTotals(DurableModel):
    """Byte counters for the whole run.

    `xet_cache_peak_bytes` is a **writer-local disk** measurement, reported here
    because that cache is bounded by the writer's root filesystem rather than by
    the archive dataset — a distinct failure mode from the archive filling up.
    """

    downloaded_bytes: ByteCount = 0
    hashed_bytes: ByteCount = 0
    published_bytes: ByteCount = 0
    pruned_logical_bytes: ByteCount = 0
    reused_bytes: ByteCount = 0
    xet_cache_peak_bytes: ByteCount = 0


class RunEnvelope(VersionedModel):
    """Fields every report carries, whether it came from `sync` or `verify`.

    A verification report is a run report with verification-specific fields
    added (`docs/schemas.md` §7), and both are written to the same `runs/` path,
    so the shared part is one class rather than two that drift.
    """

    application_version: str
    archive_id: str
    command: str
    completed_at: Timestamp
    config_fingerprint: Sha256
    errors: Annotated[tuple[str, ...], BeforeValidator(as_tuple)] = ()
    exit_code: int
    hostname: str
    huggingface_hub_version: str
    invocation_mode: Literal["systemd", "interactive"]
    outcome: Literal["success", "success_with_warnings", "failed"]
    python_version: str
    run_id: RunIdField
    started_at: Timestamp
    warnings: Annotated[tuple[str, ...], BeforeValidator(as_tuple)] = ()

    @model_validator(mode="after")
    def _check_envelope(self) -> Self:
        if self.completed_at < self.started_at:
            message = "completed_at is before started_at"
            raise ValueError(message)
        if self.exit_code not in set(ExitCode):
            message = f"exit_code {self.exit_code} is not one of {sorted(int(c) for c in ExitCode)}"
            raise ValueError(message)
        succeeded = self.exit_code == ExitCode.SUCCESS
        if succeeded != (self.outcome in _SUCCESSFUL_OUTCOMES):
            message = (
                f"outcome {self.outcome!r} contradicts exit_code {self.exit_code}; the two are "
                f"the same statement in two forms and automation reads both"
            )
            raise ValueError(message)
        if (self.outcome == "success_with_warnings") != bool(self.warnings):
            message = "success_with_warnings is reported exactly when warnings were recorded"
            raise ValueError(message)
        return self

    @property
    def duration_seconds(self) -> float:
        """How long the run took, from the report's own timestamps."""
        return (self.completed_at - self.started_at).total_seconds()


@final
class RunReport(RunEnvelope):
    """`runs/<YYYYMMDD>T<HHMMSS>Z-<run-id>.json` for a mutating command (§6)."""

    repositories: Annotated[tuple[RepositoryRunResult, ...], BeforeValidator(as_tuple)] = ()
    totals: RunTotals = RunTotals()

    @model_validator(mode="after")
    def _check(self) -> Self:
        seen = {(result.repository_type, result.repository_id) for result in self.repositories}
        if len(seen) != len(self.repositories):
            message = "a repository appears at most once in a run report"
            raise ValueError(message)
        ordered = sorted(self.repositories, key=lambda r: (r.repository_type, r.repository_id))
        if list(self.repositories) != ordered:
            message = "repositories must be sorted by (repository_type, repository_id)"
            raise ValueError(message)
        return self


# --------------------------------------------------------------------------- #
# §7 Verification report
# --------------------------------------------------------------------------- #


@final
class Finding(DurableModel):
    """One thing verification found wrong.

    A finding never causes a rewrite, a prune, or a re-download over the
    evidence (`AD-13`, `AD-18`). It is recorded, surfaced, and exits `40`.
    """

    commit_sha: CommitShaField
    expected: str | None = None
    kind: Literal[
        "missing",
        "extra",
        "size_mismatch",
        "digest_mismatch",
        "not_regular",
        "unreadable",
        "ref_invalid",
        "manifest_invalid",
    ]
    observed: str | None = None
    path: RepositoryPath | None = None
    publication_id: PublicationIdField
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField

    @property
    def sort_key(self) -> tuple[str, str, str, str, str]:
        """Deterministic ordering for the findings array."""
        return (
            self.repository_type,
            self.repository_id,
            self.commit_sha,
            self.path or "",
            self.kind,
        )


@final
class VerificationScope(DurableModel):
    """What a verification run actually covered."""

    repositories: Count = 0
    revisions: Count = 0
    unique_bytes_read: ByteCount = 0
    unique_objects_read: Count = 0


@final
class VerificationReport(RunEnvelope):
    """A run report plus what `verify` found (`docs/schemas.md` §7)."""

    findings: Annotated[tuple[Finding, ...], BeforeValidator(as_tuple)] = ()
    mode: Literal["new", "full", "revision"]
    scope: VerificationScope = VerificationScope()
    throughput_bytes_per_second: Rate = 0.0
    verification_outcome: Literal["clean", "failed"]

    @model_validator(mode="after")
    def _check(self) -> Self:
        if (self.verification_outcome == "failed") != bool(self.findings):
            message = (
                "verification_outcome and findings must agree; a clean run has no findings, and "
                "findings that changed no outcome would be findings nobody acts on"
            )
            raise ValueError(message)
        ordered = sorted(self.findings, key=lambda finding: finding.sort_key)
        if list(self.findings) != ordered:
            message = "findings must be sorted by (type, id, sha, path, kind)"
            raise ValueError(message)
        return self


# --------------------------------------------------------------------------- #
# §5 Catalog — derived state (`FS-16`)
# --------------------------------------------------------------------------- #


@final
class CurrentRevision(DurableModel):
    """Which revision consumers are being pointed at."""

    commit_sha: CommitShaField
    publication_generation: Generation
    publication_id: PublicationIdField


@final
class CatalogRevision(DurableModel):
    """One retained revision as the catalog summarizes it."""

    commit_sha: CommitShaField
    file_count: Count
    publication_generation: Generation
    publication_id: PublicationIdField
    published_at: Timestamp
    total_bytes: ByteCount
    verification_state: Literal["verified", "unverified", "failed"]


@final
class RepositoryCatalogEntry(DurableModel):
    """One repository's retained state.

    `managed = false` is a repository that was removed from configuration. Its
    data stays and it keeps appearing here, because removing an entry from a
    file is not a request to delete an archive (`AD-06`). `upstream_state` is
    reported for the same reason and is never a reason to delete anything.
    """

    current: CurrentRevision | None = None
    enabled: bool | None = None
    first_published_at: Timestamp | None = None
    last_published_at: Timestamp | None = None
    last_run_status: str | None = None
    last_seen_at: Timestamp | None = None
    managed: bool
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    requested_revision: str | None = None
    revisions: Annotated[tuple[CatalogRevision, ...], BeforeValidator(as_tuple)] = ()
    upstream_state: Literal["ok", "not_found", "forbidden", "unreachable", "unknown"] = "unknown"
    warnings: Annotated[tuple[str, ...], BeforeValidator(as_tuple)] = ()

    @model_validator(mode="after")
    def _check(self) -> Self:
        if not self.managed and self.enabled is not None:
            message = "enabled is null for a repository that is no longer configured"
            raise ValueError(message)
        generations = [revision.publication_generation for revision in self.revisions]
        if generations != sorted(generations):
            message = "revisions must be sorted ascending by publication_generation (`AD-05`)"
            raise ValueError(message)
        if len(set(generations)) != len(generations):
            message = "each retained revision has its own publication generation (`FS-20`)"
            raise ValueError(message)
        if self.current is not None and self.current.commit_sha not in {
            revision.commit_sha for revision in self.revisions
        }:
            message = "current names a revision this repository does not retain (`FS-11`)"
            raise ValueError(message)
        return self


@final
class RepositoriesCatalog(VersionedModel):
    """`published/catalog/repositories.json` — derived, never authoritative."""

    generated_at: Timestamp
    repositories: Annotated[tuple[RepositoryCatalogEntry, ...], BeforeValidator(as_tuple)] = ()

    @model_validator(mode="after")
    def _check(self) -> Self:
        ordered = sorted(self.repositories, key=lambda r: (r.repository_type, r.repository_id))
        if list(self.repositories) != ordered:
            message = "repositories must be sorted by (repository_type, repository_id)"
            raise ValueError(message)
        return self


@final
class FullVerificationSummary(DurableModel):
    """The last full verification, as `status` reports it."""

    completed_at: Timestamp
    duration_seconds: Seconds
    outcome: Literal["clean", "failed"]
    report: ArchivePath
    started_at: Timestamp
    throughput_bytes_per_second: Rate
    unique_bytes: ByteCount
    unique_objects: Count


@final
class OutstandingFailure(DurableModel):
    """A finding that no later verification or repair has cleared.

    Entries are never cleared by a run that simply does not re-check the same
    object — only by one that re-reads it successfully, or by a completed
    repair. That is what stops a narrow `verify --new` from appearing to fix a
    problem it never looked at.
    """

    commit_sha: CommitShaField
    first_seen_at: Timestamp
    kind: str
    path: RepositoryPath | None = None
    publication_id: PublicationIdField
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField


@final
class VerificationRevisionEntry(DurableModel):
    """One revision's most recent verification outcome."""

    commit_sha: CommitShaField
    outcome: Literal["clean", "failed"]
    publication_id: PublicationIdField
    verified_at: Timestamp


@final
class RepositoryVerificationEntry(DurableModel):
    """One repository's verification state."""

    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    revisions: Annotated[tuple[VerificationRevisionEntry, ...], BeforeValidator(as_tuple)] = ()


@final
class VerificationCatalog(VersionedModel):
    """`published/catalog/verification.json` — the archive's health headline.

    A non-empty `outstanding_failures` means `hfcache status` reports the archive
    as degraded until an operator resolves it.
    """

    generated_at: Timestamp
    last_full_verification: FullVerificationSummary | None = None
    outstanding_failures: Annotated[tuple[OutstandingFailure, ...], BeforeValidator(as_tuple)] = ()
    repositories: Annotated[tuple[RepositoryVerificationEntry, ...], BeforeValidator(as_tuple)] = ()

    @model_validator(mode="after")
    def _check(self) -> Self:
        ordered = sorted(self.repositories, key=lambda r: (r.repository_type, r.repository_id))
        if list(self.repositories) != ordered:
            message = "repositories must be sorted by (repository_type, repository_id)"
            raise ValueError(message)
        return self

    @property
    def is_degraded(self) -> bool:
        """Whether `status` should report the archive as degraded."""
        return bool(self.outstanding_failures)
