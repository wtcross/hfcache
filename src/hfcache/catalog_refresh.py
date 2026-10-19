"""Typed bounded offline refresh; only independently atomic adjunct writes (INV-018)."""

import json
from typing import TYPE_CHECKING

from hfcache.catalog_capture import CatalogCapture, capture_warning
from hfcache.catalog_inventory import CatalogInventory
from hfcache.catalog_refresh_models import (
    MAX_REFRESH_PUBLICATIONS,
    MAX_REFRESH_REPOSITORIES,
    MAX_REFRESH_RESULT_BYTES,
    CatalogRefreshResult,
    PublicationRefresh,
    RefreshCounts,
    RepositoryRefresh,
    refresh_counts,
    refresh_state,
)
from hfcache.errors import ConfigurationError, HfcacheError, IntegrityError, Problem
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.metadata import QueryLimitError

if TYPE_CHECKING:
    from hfcache.models import Reference
    from hfcache.services.requests import CatalogRefreshRequest

__all__ = [
    "MAX_REFRESH_PUBLICATIONS",
    "MAX_REFRESH_REPOSITORIES",
    "MAX_REFRESH_RESULT_BYTES",
    "CatalogRefreshResult",
    "PublicationRefresh",
    "RefreshCounts",
    "RepositoryRefresh",
    "refresh_catalog",
]

RESULT_UNIT_BYTES = 1536


def _limit() -> QueryLimitError:
    return QueryLimitError.single(
        "Catalog refresh scope or result budget exceeded", code="HFAPI005"
    )


def _scope(
    capture: CatalogCapture, request: CatalogRefreshRequest
) -> dict[RepositoryIdentity, tuple[Reference, ...]]:
    if capture.writer is None or capture.curation is None:
        msg = "Catalog refresh requires validated current curation and writer guards"
        raise RuntimeError(msg)
    inventory = CatalogInventory(capture.layout, capture.writer.reader)
    configured = capture.curation.tags
    if request.selectors:
        found = {}
        for selector in request.selectors:
            kind, identifier = selector.split(":", 1)
            identity = RepositoryIdentity.of(kind, identifier)
            references = inventory.retained(identity)
            if identity not in configured and not references:
                msg = "Catalog refresh selector is absent from current configuration and archive"
                raise ConfigurationError.single(msg, code="HFARG004", repository=identity.selector)
            found[identity] = references
    else:
        found = inventory.archived()
        for identity in configured:
            found.setdefault(identity, ())
    if len(found) > MAX_REFRESH_REPOSITORIES:
        raise _limit()
    result = {}
    for identity in sorted(found, key=lambda item: item.sort_key):
        refs = found[identity]
        if request.technical and request.revision_scope == "current":
            current = inventory.current(identity)
            if refs and current is None:
                msg = "Retained repository has no valid current reference"
                raise IntegrityError.single(msg, code="HFVER008", repository=identity.selector)
            refs = (current,) if current is not None else ()
        result[identity] = refs if request.technical else ()
    publications = sum(len(refs) for refs in result.values())
    # Reserve the complete bounded result before the first record write, never truncate after work.
    if publications > MAX_REFRESH_PUBLICATIONS or (
        (len(result) + publications) * RESULT_UNIT_BYTES
        + sum(len(str(ref.publication_generation)) for refs in result.values() for ref in refs)
        + 4096
        > MAX_REFRESH_RESULT_BYTES
    ):
        raise _limit()
    return result


def _publication(
    capture: CatalogCapture, identity: RepositoryIdentity, ref: Reference
) -> PublicationRefresh:
    common = {
        "commit_sha": ref.commit_sha,
        "publication_id": ref.publication_id,
        "publication_generation": ref.publication_generation,
    }
    try:
        record = capture.publication_record(
            identity, CommitSha(ref.commit_sha), PublicationId(ref.publication_id)
        )
        failures = capture.write_record(record)
        if failures:
            return PublicationRefresh(**common, write_status="failed", error_code=failures[0])
        return PublicationRefresh(
            **common,
            write_status="written",
            observation_status=record.status,
            observed_at=record.observed_at,
            manifest_digest=record.manifest_digest,
        )
    except HfcacheError as exc:
        return PublicationRefresh(**common, write_status="failed", error_code=exc.problems[0].code)
    except Exception:  # noqa: BLE001 - isolate only the optional exact record attempt
        return PublicationRefresh(**common, write_status="failed", error_code="HFVER007")


def refresh_catalog(
    capture: CatalogCapture, request: CatalogRefreshRequest
) -> tuple[CatalogRefreshResult, tuple[Problem, ...], tuple[Problem, ...]]:
    """Caller owns the only lock/preflight; refuse pending work without applying recovery."""
    capture.begin(required_curation=True)
    selected = _scope(capture, request)
    curation = capture.curation
    if curation is None:
        msg = "Catalog refresh lost its validated curation source"
        raise RuntimeError(msg)
    rows = []
    warnings, errors = [], []
    for identity, references in selected.items():
        capture.capacity_warnings.clear()
        warning_codes, error_codes = set(), set()
        tag_status = "not_requested"
        if request.tags:
            record, suppressed = capture.tag_record(identity)
            tag_status = "skipped_unconfigured"
            if record is not None:
                failures = capture.write_record(record)
                error_codes.update(failures)
                tag_status = "failed" if failures else "captured"
            if suppressed:
                warning_codes.add("HFWRN011")
        publications = tuple(_publication(capture, identity, ref) for ref in references)
        error_codes.update(pub.error_code for pub in publications if pub.error_code is not None)
        incomplete = any(pub.observation_status != "complete" for pub in publications)
        if incomplete or error_codes:
            warning_codes.add("HFWRN011")
        warning_codes.update(capture.capacity_warnings)
        technical_status = "not_requested"
        if request.technical:
            technical_status = "skipped_unpublished" if not references else "complete"
            if incomplete:
                technical_status = (
                    "incomplete"
                    if any(pub.write_status == "written" for pub in publications)
                    else "failed"
                )
        row = RepositoryRefresh(
            repository_type=identity.type,
            repository_id=identity.id,
            tag_status=tag_status,
            technical_status=technical_status,
            publications=publications,
            warnings=tuple(sorted(warning_codes)),
            errors=tuple(sorted(error_codes)),
        )
        rows.append(row)
        if "HFWRN011" in warning_codes:
            warnings.extend(capture_warning(identity))
        warnings.extend(
            Problem(
                code=code,
                message="Supplemental write is close to the capacity reserve",
                repository=identity.selector,
            )
            for code in sorted(warning_codes - {"HFWRN011"})
        )
        errors.extend(
            Problem(
                code=code,
                message="Supplemental record refresh failed",
                repository=identity.selector,
            )
            for code in sorted(error_codes)
        )
    counts = refresh_counts(tuple(rows))
    result = CatalogRefreshResult(
        state=refresh_state(tuple(rows), counts),
        archive_id=capture.config.storage.archive_id,
        revision_scope=request.revision_scope,
        tags=request.tags,
        technical=request.technical,
        curation_fingerprint=curation.fingerprint,
        curation_observed_at=curation.observed_at,
        counts=counts,
        repositories=tuple(rows),
    )
    if len(json.dumps(result.to_payload(), ensure_ascii=False).encode()) > MAX_REFRESH_RESULT_BYTES:
        # A programming/schema sizing defect must never turn into a truncated successful result.
        raise _limit()
    return result, tuple(warnings), tuple(errors)
