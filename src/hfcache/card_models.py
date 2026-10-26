"""ADR142: independently strict exact-publication card read projection (schema18.1)."""

import json
from typing import Annotated, Literal, Self

from pydantic import BeforeValidator, Field, field_validator, model_validator

from hfcache.catalog_models import (
    MAXIMUM_CARD_PRESENTATION_BYTES,
    MAXIMUM_CARD_RECORD_BYTES,
    CardDiagnostic,
    CardState,
)
from hfcache.models import (
    ArchiveIdField,
    ArchivePath,
    CommitShaField,
    DurableModel,
    Generation,
    PublicationIdField,
    RepositoryIdField,
    RepositoryTypeField,
    Sha256,
    Timestamp,
    as_tuple,
    dump,
)


class RepositoryCardRead(DurableModel):
    """Safe capture or explicit missing adjunct; never invent a capture or publication."""

    schema_version: Literal[1]
    kind: Literal["repository_card"]
    archive_id: ArchiveIdField
    repository_type: RepositoryTypeField
    repository_id: RepositoryIdField
    commit_sha: CommitShaField
    publication_id: PublicationIdField
    publication_generation: Generation
    manifest_path: ArchivePath
    manifest_digest: Sha256
    source_path: Literal["README.md"] | None
    expected_source_sha256: Sha256 | None
    captured_at: Timestamp | None
    presentation_version: Literal["markdown-1"] | None
    state: CardState | Literal["not_captured"]
    markdown: Annotated[str, Field(max_length=MAXIMUM_CARD_PRESENTATION_BYTES)] | None
    presentation_sha256: Sha256 | None
    diagnostics: Annotated[
        tuple[CardDiagnostic, ...], BeforeValidator(as_tuple), Field(max_length=11)
    ]

    @field_validator("schema_version", mode="before")
    @classmethod
    def strict_version(cls, value: object) -> object:
        if type(value) is not int or value != 1:
            msg = "Unsupported repository card read schema"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if tuple(sorted(set(self.diagnostics))) != self.diagnostics:
            msg = "Card read diagnostics must be sorted and unique"
            raise ValueError(msg)
        if (self.source_path is None) != (self.expected_source_sha256 is None):
            msg = "Card read source path and digest must be known together"
            raise ValueError(msg)
        if self.state == "not_captured":
            if (
                any(
                    value is not None
                    for value in (
                        self.captured_at,
                        self.presentation_version,
                        self.markdown,
                        self.presentation_sha256,
                    )
                )
                or self.diagnostics
            ):
                msg = "Missing card capture cannot invent presentation or capture metadata"
                raise ValueError(msg)
        else:
            if self.captured_at is None or self.presentation_version is None:
                msg = "Captured card states require capture time and presentation version"
                raise ValueError(msg)
            if (self.state == "absent") != (self.source_path is None):
                msg = "Only absent or not-captured cards may have no source identity"
                raise ValueError(msg)
            if self.state == "present":
                if self.markdown is None or self.presentation_sha256 is None:
                    msg = "Present cards require presentation and its digest"
                    raise ValueError(msg)
                if (
                    len(self.markdown.encode("utf-8")) > MAXIMUM_CARD_PRESENTATION_BYTES
                    or len(json.dumps(self.markdown, ensure_ascii=False).encode("utf-8"))
                    > MAXIMUM_CARD_PRESENTATION_BYTES
                ):
                    msg = "Card read presentation exceeds its independent byte bounds"
                    raise ValueError(msg)
            elif self.markdown is not None or self.presentation_sha256 is not None:
                msg = "Non-present cards must withhold presentation and its digest"
                raise ValueError(msg)
        if len(dump(self)) > MAXIMUM_CARD_RECORD_BYTES:
            msg = "Card read projection exceeds its whole-record byte bound"
            raise ValueError(msg)
        return self
