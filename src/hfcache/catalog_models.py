"""Strict supplemental record families, independent of archive evidence (schemas §17)."""

import hashlib
import json
import re
from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import BeforeValidator, Field, model_validator

from hfcache.models import (
    ArchiveIdField,
    ArchivePath,
    CommitShaField,
    DurableModel,
    Generation,
    PublicationIdField,
    RepositoryIdField,
    RepositoryPath,
    RepositoryTypeField,
    Sha256,
    Timestamp,
    as_tuple,
)
from hfcache.tags import normalize_tags

if TYPE_CHECKING:
    from collections.abc import Sequence

MAXIMUM_MEMBERS = 4096
MAXIMUM_RECORD_BYTES = 16 * 1024 * 1024
EXTRACTOR_VERSION = "static-1"


def _identifier(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,63}", value):
        msg = "metadata identifier has invalid syntax"
        raise ValueError(msg)
    return value


def _canonical_tags(value: object) -> tuple[str, ...]:
    canonical = normalize_tags(value)
    if not isinstance(value, (list, tuple)) or tuple(value) != canonical:
        msg = "stored tags must already be canonical, sorted and unique"
        raise ValueError(msg)
    return canonical


def _ordered(values: Sequence[str]) -> None:
    if list(values) != sorted(set(values)):
        msg = "metadata collection must be sorted and unique"
        raise ValueError(msg)


Identifier = Annotated[str, BeforeValidator(_identifier)]
LogicalBytes = Annotated[int, Field(ge=0, le=2**63 - 1)]
Diagnostic = Annotated[str, Field(max_length=512)]
Diagnostics = Annotated[tuple[Diagnostic, ...], BeforeValidator(as_tuple), Field(max_length=64)]
Formats = Annotated[tuple[Identifier, ...], BeforeValidator(as_tuple), Field(max_length=64)]


class CatalogRecord(DurableModel):
    """Independent schema 1; missing/unsupported versions refuse at the reader."""

    schema_version: Literal[1] = 1


class RepositoryTagSnapshot(CatalogRecord):
    """Only actual last writer-observed curation, never current config (INV-018)."""

    kind: Literal["repository_tag_snapshot"] = "repository_tag_snapshot"
    archive_id: ArchiveIdField
    repository_type: RepositoryTypeField
    repository_id: RepositoryIdField
    tags: Annotated[tuple[str, ...], BeforeValidator(_canonical_tags), Field(max_length=64)]
    observed_at: Timestamp
    curation_fingerprint: Sha256
    source: Literal["installed_config"] = "installed_config"


class SourceObservation(DurableModel):
    """Selected inert declarations with exact manifest source provenance."""

    path: RepositoryPath
    sha256: Sha256
    field: Literal[
        "task",
        "language",
        "license",
        "base_model",
        "upstream_tags",
        "dataset_config",
        "dataset_split",
        "dataset_feature",
        "format",
    ]
    values: Annotated[
        tuple[Annotated[str, Field(max_length=2048)], ...],
        BeforeValidator(as_tuple),
        Field(max_length=64),
    ]
    evidence: Literal["declaration", "header", "filename"]

    @model_validator(mode="after")
    def ordered(self) -> Self:
        _ordered(self.values)
        return self


class VariantMember(DurableModel):
    path: RepositoryPath
    size_bytes: LogicalBytes


class ModelVariant(DurableModel):
    """One logical member set; completeness is separate from loadability."""

    variant_id: Sha256
    format: Identifier
    encoding: Identifier | None = None
    quantization: Identifier | None = None
    quantization_method: Identifier | None = None
    bits: Annotated[int, Field(ge=1, le=64)] | None = None
    group_size: Annotated[int, Field(ge=1, le=2**63 - 1)] | None = None
    role: Literal["primary", "adapter", "projector", "auxiliary", "unknown"]
    members: Annotated[
        tuple[VariantMember, ...], BeforeValidator(as_tuple), Field(min_length=1, max_length=4096)
    ]
    total_bytes: LogicalBytes | None = None
    completeness: Literal["complete", "incomplete", "unknown"]
    evidence: Literal["header", "declaration", "filename"]
    source_paths: Annotated[
        tuple[RepositoryPath, ...], BeforeValidator(as_tuple), Field(min_length=1, max_length=64)
    ]
    diagnostics: Diagnostics = ()

    @model_validator(mode="after")
    def coherent(self) -> Self:
        _ordered([member.path for member in self.members])
        _ordered(self.source_paths)
        _ordered(self.diagnostics)
        if self.total_bytes is not None and self.total_bytes != sum(
            m.size_bytes for m in self.members
        ):
            msg = "variant bytes must equal its identified member bytes"
            raise ValueError(msg)
        if self.completeness == "complete" and self.total_bytes is None:
            msg = "complete variants require known identified member bytes"
            raise ValueError(msg)
        return self


def variant_identity(
    members: Sequence[VariantMember], extractor_version: str = EXTRACTOR_VERSION
) -> str:
    """Hash canonical logical membership and extractor identity within an exact publication."""
    payload = {
        "extractor_version": extractor_version,
        "members": [
            member.to_payload() for member in sorted(members, key=lambda member: member.path)
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


class PublicationObservation(CatalogRecord):
    """Rebuildable interpretation; manifest/ref authority and integrity remain separate."""

    kind: Literal["publication_observation"] = "publication_observation"
    archive_id: ArchiveIdField
    repository_type: RepositoryTypeField
    repository_id: RepositoryIdField
    commit_sha: CommitShaField
    publication_id: PublicationIdField
    publication_generation: Generation
    manifest_path: ArchivePath
    manifest_digest: Sha256
    extractor_version: Identifier = EXTRACTOR_VERSION
    observed_at: Timestamp
    status: Literal["complete", "partial", "unsupported", "failed"]
    sources: Annotated[
        tuple[SourceObservation, ...], BeforeValidator(as_tuple), Field(max_length=4096)
    ] = ()
    variants: Annotated[
        tuple[ModelVariant, ...], BeforeValidator(as_tuple), Field(max_length=4096)
    ] = ()
    dataset_formats: Formats = ()
    diagnostics: Diagnostics = ()

    @model_validator(mode="after")
    def coherent(self) -> Self:
        keys = [(source.path, source.field, source.evidence) for source in self.sources]
        if keys != sorted(set(keys)):
            msg = "sources must be sorted and unique by path, field and evidence"
            raise ValueError(msg)
        _ordered([variant.variant_id for variant in self.variants])
        _ordered(self.dataset_formats)
        _ordered(self.diagnostics)
        if sum(len(variant.members) for variant in self.variants) > MAXIMUM_MEMBERS:
            msg = "aggregate variant membership exceeds the observation work limit"
            raise ValueError(msg)
        if (self.repository_type == "model" and self.dataset_formats) or (
            self.repository_type == "dataset" and self.variants
        ):
            msg = "model variants and dataset declarations have distinct repository scopes"
            raise ValueError(msg)
        if any(
            v.variant_id != variant_identity(v.members, self.extractor_version)
            for v in self.variants
        ):
            msg = "variant identity does not match membership and extractor"
            raise ValueError(msg)
        return self
