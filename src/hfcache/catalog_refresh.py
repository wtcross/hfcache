"""Typed bounded offline refresh; only independently atomic adjunct writes (INV-018)."""

import json
from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import BeforeValidator, Field, field_validator, model_validator

from hfcache.catalog_capture import CatalogCapture, capture_warning
from hfcache.catalog_inventory import CatalogInventory
from hfcache.catalog_models import CatalogRecord
from hfcache.config import ArchiveId  # noqa: TC001 - runtime model annotation
from hfcache.errors import ConfigurationError, HfcacheError, IntegrityError, Problem
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.metadata import QueryLimitError
from hfcache.models import (
    CommitShaField,
    DurableModel,
    Generation,
    PublicationIdField,
    RepositoryIdField,
    RepositoryTypeField,
    Sha256,
    Timestamp,
    as_tuple,
)

if TYPE_CHECKING:
    from hfcache.models import Reference
    from hfcache.services.requests import CatalogRefreshRequest

MAX_REFRESH_REPOSITORIES = 256
MAX_REFRESH_PUBLICATIONS = 512
MAX_REFRESH_RESULT_BYTES = 1024 * 1024
RESULT_UNIT_BYTES = 1536
Code = Annotated[str, Field(pattern=r"^HF[A-Z]{2,6}[0-9]{3}$", max_length=32)]
Codes = Annotated[tuple[Code, ...], BeforeValidator(as_tuple), Field(max_length=8)]


class PublicationRefresh(DurableModel):
    """Written record identity is present only after its independent write succeeds."""

    commit_sha: CommitShaField
    publication_id: PublicationIdField
    publication_generation: Generation
    write_status: Literal["written", "failed"]
    observation_status: Literal["complete", "partial", "unsupported", "failed"] | None = None
    observed_at: Timestamp | None = None
    manifest_digest: Sha256 | None = None
    error_code: Code | None = None

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        observed = (self.observation_status, self.observed_at, self.manifest_digest)
        if (
            self.write_status == "written" and (None in observed or self.error_code is not None)
        ) or (
            self.write_status == "failed"
            and (any(value is not None for value in observed) or self.error_code is None)
        ):
            msg = "Refresh write outcome disagrees with recorded observation identity"
            raise ValueError(msg)
        return self


class RepositoryRefresh(DurableModel):
    """Intentional skips, atomic progress and incomplete interpretation remain distinct."""

    repository_type: RepositoryTypeField
    repository_id: RepositoryIdField
    tag_status: Literal["captured", "not_requested", "skipped_unconfigured", "failed"]
    technical_status: Literal[
        "complete", "incomplete", "failed", "not_requested", "skipped_unpublished"
    ]
    publications: Annotated[
        tuple[PublicationRefresh, ...],
        BeforeValidator(as_tuple),
        Field(max_length=MAX_REFRESH_PUBLICATIONS),
    ] = ()
    warnings: Codes = ()
    errors: Codes = ()

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        if any(tuple(sorted(set(codes))) != codes for codes in (self.warnings, self.errors)):
            msg = "Refresh problem codes must be sorted and unique"
            raise ValueError(msg)
        if self.technical_status in {"not_requested", "skipped_unpublished"} and self.publications:
            msg = "Skipped technical work cannot report publication attempts"
            raise ValueError(msg)
        keys = tuple((pub.publication_generation, pub.commit_sha) for pub in self.publications)
        if keys != tuple(sorted(set(keys))):
            msg = "Refresh publication attempts must be unique and ordered"
            raise ValueError(msg)
        if self.technical_status not in {"not_requested", "skipped_unpublished"}:
            expected = "complete"
            if not self.publications:
                msg = "Technical refresh progress requires publication attempts"
                raise ValueError(msg)
            if any(pub.observation_status != "complete" for pub in self.publications):
                expected = (
                    "incomplete"
                    if any(pub.write_status == "written" for pub in self.publications)
                    else "failed"
                )
            if expected != self.technical_status:
                msg = "Technical refresh status disagrees with exact publication attempts"
                raise ValueError(msg)
        if not {pub.error_code for pub in self.publications if pub.error_code}.issubset(
            self.errors
        ):
            msg = "Publication write failures must remain visible at repository scope"
            raise ValueError(msg)
        if self.tag_status == "failed" and not self.errors:
            msg = "Failed tag capture requires an explicit error"
            raise ValueError(msg)
        if (
            self.errors or self.technical_status in {"incomplete", "failed"}
        ) and "HFWRN011" not in self.warnings:
            msg = "Incomplete refresh must retain its supplemental warning"
            raise ValueError(msg)
        return self


class RefreshCounts(DurableModel):
    repositories: Annotated[int, Field(ge=0, le=MAX_REFRESH_REPOSITORIES)]
    snapshots_written: Annotated[int, Field(ge=0, le=MAX_REFRESH_REPOSITORIES)]
    observations_written: Annotated[int, Field(ge=0, le=MAX_REFRESH_PUBLICATIONS)]
    records_failed: Annotated[
        int, Field(ge=0, le=MAX_REFRESH_PUBLICATIONS + MAX_REFRESH_REPOSITORIES)
    ]
    technical_incomplete: Annotated[int, Field(ge=0, le=MAX_REFRESH_PUBLICATIONS)]
    technical_skipped: Annotated[int, Field(ge=0, le=MAX_REFRESH_REPOSITORIES)]


class CatalogRefreshResult(CatalogRecord):
    """Schema-1 service payload; keyed operation observation is its transport owner."""

    state: Literal["complete", "partial", "failed"]
    archive_id: ArchiveId
    revision_scope: Literal["current", "retained"]
    tags: bool
    technical: bool
    curation_fingerprint: Sha256
    curation_observed_at: Timestamp
    counts: RefreshCounts
    repositories: Annotated[
        tuple[RepositoryRefresh, ...],
        BeforeValidator(as_tuple),
        Field(max_length=MAX_REFRESH_REPOSITORIES),
    ]

    @field_validator("schema_version", mode="before")
    @classmethod
    def _strict_version(cls, value: object) -> object:
        if type(value) is not int or value != 1:
            msg = "Unsupported catalog refresh schema"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        keys = tuple((row.repository_type, row.repository_id) for row in self.repositories)
        if keys != tuple(sorted(set(keys))) or not (self.tags or self.technical):
            msg = "Refresh rows or requested outputs are inconsistent"
            raise ValueError(msg)
        expected = _counts(self.repositories)
        if self.counts != expected:
            msg = "Refresh counts disagree with exact per-record progress"
            raise ValueError(msg)
        if self.state != _state(self.repositories, expected):
            msg = "Refresh completion state disagrees with per-record progress"
            raise ValueError(msg)
        if any(
            (not self.tags and row.tag_status != "not_requested")
            or (self.tags and row.tag_status == "not_requested")
            or (not self.technical and row.technical_status != "not_requested")
            or (self.technical and row.technical_status == "not_requested")
            for row in self.repositories
        ):
            msg = "Refresh progress disagrees with the enabled outputs"
            raise ValueError(msg)
        return self


def _counts(rows: tuple[RepositoryRefresh, ...]) -> RefreshCounts:
    return RefreshCounts(
        repositories=len(rows),
        snapshots_written=sum(row.tag_status == "captured" for row in rows),
        observations_written=sum(
            pub.write_status == "written" for row in rows for pub in row.publications
        ),
        records_failed=sum(row.tag_status == "failed" for row in rows)
        + sum(pub.write_status == "failed" for row in rows for pub in row.publications),
        technical_incomplete=sum(
            pub.observation_status != "complete" for row in rows for pub in row.publications
        ),
        technical_skipped=sum(row.technical_status == "skipped_unpublished" for row in rows),
    )


def _state(
    rows: tuple[RepositoryRefresh, ...], counts: RefreshCounts
) -> Literal["complete", "partial", "failed"]:
    if not any(row.warnings or row.errors for row in rows):
        return "complete"
    return "partial" if counts.snapshots_written + counts.observations_written else "failed"


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
    counts = _counts(tuple(rows))
    result = CatalogRefreshResult(
        state=_state(tuple(rows), counts),
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
