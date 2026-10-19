"""Pure independently strict offline refresh results (schemas §17.3, INV-018)."""

from typing import Annotated, Literal, Self

from pydantic import BeforeValidator, Field, field_validator, model_validator

from hfcache.catalog_models import CatalogRecord
from hfcache.models import (
    ArchiveIdField,
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

MAX_REFRESH_REPOSITORIES = 256
MAX_REFRESH_PUBLICATIONS = 512
MAX_REFRESH_RESULT_BYTES = 1024 * 1024
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
    archive_id: ArchiveIdField
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
        expected = refresh_counts(self.repositories)
        if self.counts != expected:
            msg = "Refresh counts disagree with exact per-record progress"
            raise ValueError(msg)
        if self.state != refresh_state(self.repositories, expected):
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


def refresh_counts(rows: tuple[RepositoryRefresh, ...]) -> RefreshCounts:
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


def refresh_state(
    rows: tuple[RepositoryRefresh, ...], counts: RefreshCounts
) -> Literal["complete", "partial", "failed"]:
    if not any(row.warnings or row.errors for row in rows):
        return "complete"
    return "partial" if counts.snapshots_written + counts.observations_written else "failed"
