"""Joined writer-owned capture, independently atomic and nonfatal to publication."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from hfcache.catalog_extractors import (
    EXTRACTION_WARNING_CODE,
    ExtractionBudget,
    ExtractionResult,
    SourceAccess,
    extract_static,
)
from hfcache.catalog_gguf import extract_gguf
from hfcache.catalog_models import PublicationObservation, RepositoryTagSnapshot
from hfcache.catalog_parsing import ExtractionError
from hfcache.catalog_storage import CatalogWriter, publication_binding
from hfcache.catalog_weights import extract_weights
from hfcache.errors import ConfigurationError, HfcacheError, Problem
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.locking import require_archive_lock
from hfcache.logging import emit
from hfcache.models import dump
from hfcache.preflight import require_capacity
from hfcache.redaction import redact_text

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from hfcache.config import ApplicationConfig
    from hfcache.manifests import RevisionManifest
    from hfcache.models import TransactionJournal
    from hfcache.paths import ArchiveLayout
    from hfcache.preflight import Check
    from hfcache.reporting import RepositoryRunResult

DIRECTORY_ALLOWANCE = 64 * 1024
MAX_CAPTURE_RECORDS = 4096
MAX_CAPTURE_BYTES = 128 * 1024 * 1024
MAX_CURATION_REPOSITORIES = 100_000


def capture_warning(identity: RepositoryIdentity) -> tuple[Problem, ...]:
    """Bounded public evidence; optional failures never expose parser exceptions."""
    emit("catalog.capture_incomplete", repository=identity.selector, code=EXTRACTION_WARNING_CODE)
    return (
        Problem(
            code=EXTRACTION_WARNING_CODE,
            message=(
                "Supplemental metadata capture is incomplete; publication integrity is unchanged"
            ),
            repository=identity.selector,
        ),
    )


def extract_publication(access: SourceAccess) -> ExtractionResult:
    """One finite invocation budget shared by every static parser/header source."""
    parts = (extract_static(access), extract_gguf(access), extract_weights(access))
    sources = tuple(
        sorted(
            (source for part in parts for source in part.sources),
            key=lambda source: (source.path, source.field, source.evidence),
        )
    )
    variants = tuple(
        sorted(
            (variant for part in parts for variant in part.variants),
            key=lambda variant: variant.variant_id,
        )
    )
    formats = tuple(sorted({fmt for part in parts for fmt in part.dataset_formats}))
    diagnostics = {diagnostic for part in parts for diagnostic in part.diagnostics}
    useful = bool(sources or formats or any(v.completeness == "complete" for v in variants))
    failed = any(part.status == "failed" for part in parts)
    incomplete = any(part.status != "complete" for part in parts)
    if access.manifest.repository_type == "model" and not variants:
        incomplete = True
        diagnostics.add("no_model_weight_observation")
    if access.manifest.repository_type == "dataset" and not sources and not formats:
        incomplete = True
        diagnostics.add("no_dataset_observation")
    status = (
        "complete"
        if not incomplete
        else ("partial" if useful else ("failed" if failed else "unsupported"))
    )
    return ExtractionResult(status, sources, variants, formats, tuple(sorted(diagnostics)))


@dataclass(frozen=True, slots=True)
class ObservedCuration:
    """Only actual source identity/tags/fingerprint/time, never replacement execution policy."""

    tags: dict[RepositoryIdentity, tuple[str, ...]]
    fingerprint: str
    observed_at: datetime


class CatalogCapture:
    """An original-lock capability, invoked after producers join, never in a background task."""

    def __init__(
        self,
        layout: ArchiveLayout,
        config: ApplicationConfig,
        checks: Sequence[Check],
        *,
        curation_source: Callable[[], ApplicationConfig] | None = None,
    ) -> None:
        self.ownership = require_archive_lock()
        self.layout, self.config = layout, config
        self.checks = tuple(checks)
        self.curation_source = curation_source
        self.budget = ExtractionBudget()
        self.writer: CatalogWriter | None = None
        self.curation: ObservedCuration | None = None
        self.curation_failed = False
        self.records_attempted = 0
        self.bytes_attempted = 0
        self.capacity_warnings: dict[str, Problem] = {}

    def begin(
        self, active_sync: TransactionJournal | None = None, *, required_curation: bool = False
    ) -> None:
        require_archive_lock(expected=self.ownership)
        self.writer = None
        self.curation = None
        self.curation_failed = False
        self.writer = CatalogWriter(
            self.layout, storage=self.config.storage, checks=self.checks, active_sync=active_sync
        )
        try:
            current = self.curation_source() if self.curation_source is not None else self.config
            if (current.storage.archive_root, current.storage.archive_id) != (
                self.config.storage.archive_root,
                self.config.storage.archive_id,
            ):
                msg = "curation source archive authority changed"
                raise ValueError(msg)  # noqa: TRY301 - optional curation authority refusal
            if len(current.repositories) > MAX_CURATION_REPOSITORIES:
                msg = "curation inventory exceeds the capture budget"
                raise ValueError(msg)  # noqa: TRY301 - refuse before projection/hash allocation
            self.curation = ObservedCuration(
                {
                    RepositoryIdentity.from_config(repository): repository.tags
                    for repository in current.repositories
                },
                current.curation_fingerprint(),
                datetime.now(UTC),
            )
        except Exception:  # noqa: BLE001 - isolate only the optional fresh curation source
            self.curation_failed = True
            if required_curation:
                msg = "Current installed curation is unavailable or incompatible"
                raise ConfigurationError.single(msg, code="HFCFG001") from None

    def write_record(
        self, record: RepositoryTagSnapshot | PublicationObservation
    ) -> tuple[str, ...]:
        """Independent write outcome; fixed codes distinguish explicit partial refresh progress."""
        require_archive_lock(expected=self.ownership)
        if self.writer is None:
            return (EXTRACTION_WARNING_CODE,)
        try:
            size = len(dump(record))
            self.records_attempted += 1
            self.bytes_attempted += size
            if (
                self.records_attempted > MAX_CAPTURE_RECORDS
                or self.bytes_attempted > MAX_CAPTURE_BYTES
            ):
                return ("HFAPI005",)
            warnings = require_capacity(
                self.layout,
                self.config.storage,
                needed_bytes=size + DIRECTORY_ALLOWANCE,
            )
            self.capacity_warnings.update((warning.code, warning) for warning in warnings)
            self.writer.write(record)
        except HfcacheError as exc:
            return (exc.problems[0].code,)
        except Exception:  # noqa: BLE001 - this independently atomic adjunct cannot roll back publication
            return ("HFVER007",)
        return ()

    def _write(self, record: RepositoryTagSnapshot | PublicationObservation) -> bool:
        return not self.write_record(record)

    def tag_record(self, identity: RepositoryIdentity) -> tuple[RepositoryTagSnapshot | None, bool]:
        """Actual curation only; removal preserves history and secret suppression is visible."""
        require_archive_lock(expected=self.ownership)
        if self.curation is None or identity not in self.curation.tags:
            return None, self.curation_failed
        tags = self.curation.tags[identity]
        safe_tags = tuple(tag for tag in tags if redact_text(tag) == tag)
        return RepositoryTagSnapshot(
            archive_id=self.config.storage.archive_id,
            repository_type=identity.type,
            repository_id=identity.id,
            tags=safe_tags,
            observed_at=self.curation.observed_at,
            curation_fingerprint=self.curation.fingerprint,
        ), tags != safe_tags

    def _capture(
        self, identity: RepositoryIdentity, sha: str | None, publication: str | None
    ) -> bool:
        """True means incomplete adjunct work; no exception from optional work escapes."""
        require_archive_lock(expected=self.ownership)
        snapshot, incomplete = self.tag_record(identity)
        if snapshot is not None:
            incomplete |= not self._write(snapshot)
        if sha is None or publication is None or self.writer is None:
            return incomplete
        try:
            record = self.publication_record(identity, CommitSha(sha), PublicationId(publication))
        except Exception:  # noqa: BLE001 - failure to bind optional evidence never reclassifies publication
            return True
        return (not self._write(record)) or record.status != "complete" or incomplete

    def publication_record(
        self, identity: RepositoryIdentity, sha: CommitSha, publication: PublicationId
    ) -> PublicationObservation:
        """Bind exact retained evidence before extraction; failed interpretation stays recorded."""
        require_archive_lock(expected=self.ownership)
        if self.writer is None:
            msg = "Catalog capture has not begun"
            raise RuntimeError(msg)
        manifest, digest = publication_binding(
            self.layout, identity, sha, publication, reader=self.writer.reader
        )
        try:
            result = extract_publication(SourceAccess(self.layout, manifest, budget=self.budget))
            record = self._record(manifest, digest, result)
        except ExtractionError as exc:
            result = ExtractionResult("failed", diagnostics=(exc.reason,))
            record = self._record(manifest, digest, result)
        except Exception:  # noqa: BLE001 - preserve a truthful failed observation for an extractor defect
            result = ExtractionResult("failed", diagnostics=("extractor_failure",))
            record = self._record(manifest, digest, result)
        return record

    def _record(
        self, manifest: RevisionManifest, digest: str, result: ExtractionResult
    ) -> PublicationObservation:
        identity = manifest.identity
        sha, publication = CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id)
        return PublicationObservation(
            archive_id=self.config.storage.archive_id,
            repository_type=identity.type,
            repository_id=identity.id,
            commit_sha=sha,
            publication_id=publication,
            publication_generation=manifest.publication_generation,
            manifest_path=str(
                self.layout.archive_relative(
                    self.layout.repository(identity).manifest(
                        CommitSha(sha), PublicationId(publication)
                    )
                )
            ),
            manifest_digest=digest,
            observed_at=datetime.now(UTC),
            status=result.status,
            sources=result.sources,
            variants=result.variants,
            dataset_formats=result.dataset_formats,
            diagnostics=result.diagnostics,
        )

    def _safe_capture(
        self, identity: RepositoryIdentity, sha: str | None, publication: str | None
    ) -> tuple[Problem, ...]:
        self.capacity_warnings.clear()
        try:
            incomplete = self._capture(identity, sha, publication)
        except Exception:  # noqa: BLE001 - only optional supplemental work is inside this boundary
            incomplete = True
        warnings = tuple(self.capacity_warnings[code] for code in sorted(self.capacity_warnings))
        return (*warnings, *capture_warning(identity)) if incomplete else warnings

    def sync(
        self, results: Sequence[RepositoryRunResult], active_sync: TransactionJournal
    ) -> list[RepositoryRunResult]:
        try:
            self.begin(active_sync)
        except Exception:  # noqa: BLE001 - optional namespace/guard refusal cannot change archive outcomes
            self.curation_failed = True
        updated = []
        for result in results:
            identity = RepositoryIdentity.of(result.repository_type, result.repository_id)
            warnings = self._safe_capture(
                identity, result.resolved_commit_sha, result.publication_id
            )
            if not warnings:
                updated.append(result)
                continue
            updated.append(
                result.model_copy(
                    update={
                        "warnings": tuple(
                            sorted(set(result.warnings) | {w.code for w in warnings})
                        ),
                        "status": "completed_with_warnings"
                        if result.status == "published"
                        else result.status,
                    }
                )
            )
        return updated

    def repair(
        self, identity: RepositoryIdentity, sha: str, publication: str
    ) -> tuple[Problem, ...]:
        try:
            self.begin()
        except Exception:  # noqa: BLE001 - optional capture cannot invalidate a committed repair
            self.curation_failed = True
        return self._safe_capture(identity, sha, publication)
