"""Pure catalog query intent and strict schema-1 projections (discovery, schemas §17.2)."""

import re
from dataclasses import dataclass
from typing import Annotated, Literal, Self

from pydantic import BeforeValidator, Field, TypeAdapter, field_validator, model_validator

from hfcache.catalog_models import (
    Diagnostics,
    Formats,
    Identifier,
    ModelVariant,
    SourceObservation,
)
from hfcache.errors import ConfigurationError
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
from hfcache.tags import normalize_tags

MAX_QUERY_TEXT = 256
MAX_PAGE_ENTRIES = 10_000
MAX_COUNT = 2**63 - 1
_IDENTIFIER = TypeAdapter(Identifier)
_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
_UPPER = str.maketrans("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
Count = Annotated[int, Field(ge=0, le=MAX_COUNT)]
Facet = Literal["tag", "format", "quantization_method", "quantization"]


def _invalid_query(*, cursor: bool = False) -> ConfigurationError:
    return ConfigurationError.single(
        "Invalid catalog cursor" if cursor else "Invalid catalog query filters",
        code="HFARG001" if cursor else "HFARG002",
    )


def _choice(value: object, choices: set[str]) -> bool:
    return type(value) is str and value in choices


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return value is None or (type(value) is int and minimum <= value <= maximum)


def _technical(value: object, *, upper: bool = False) -> str | None:
    if value is None:
        return None
    return _IDENTIFIER.validate_python(value).translate(_UPPER if upper else _LOWER)


@dataclass(frozen=True, slots=True)
class CatalogQuery:
    """Normalized immutable intent; construction grants no filesystem or transport capability."""

    repository_type: Literal["model", "dataset"] | None = None
    q: str | None = None
    tags_all: tuple[str, ...] = ()
    tags_any: tuple[str, ...] = ()
    tag_source: Literal["current_or_last_observed", "current_only"] = "current_or_last_observed"
    scope: Literal["archived", "configured", "all"] = "archived"
    revision_scope: Literal["current", "retained"] = "current"
    format: str | None = None
    quantization: str | None = None
    quantization_method: str | None = None
    bits: int | None = None
    max_variant_bytes: int | None = None
    limit: int | None = None
    cursor: str | None = None

    def __post_init__(self) -> None:
        if (
            (
                self.repository_type is not None
                and not _choice(self.repository_type, {"model", "dataset"})
            )
            or not _choice(self.tag_source, {"current_or_last_observed", "current_only"})
            or not _choice(self.scope, {"archived", "configured", "all"})
            or not _choice(self.revision_scope, {"current", "retained"})
            or not _integer(self.bits, 1, 64)
            or not _integer(self.max_variant_bytes, 0, MAX_COUNT)
            or not _integer(self.limit, 1, MAX_PAGE_ENTRIES)
        ):
            raise _invalid_query()
        if self.q is not None and (not isinstance(self.q, str) or len(self.q) > MAX_QUERY_TEXT):
            raise _invalid_query()
        if self.cursor is not None and (
            not isinstance(self.cursor, str)
            or len(self.cursor) > MAX_QUERY_TEXT
            or not self.cursor.isascii()
        ):
            raise _invalid_query(cursor=True)
        try:
            if self.q is not None:
                self.q.encode("utf-8")
            object.__setattr__(self, "q", self.q.casefold() if self.q else None)
            object.__setattr__(self, "tags_all", normalize_tags(self.tags_all))
            object.__setattr__(self, "tags_any", normalize_tags(self.tags_any))
            object.__setattr__(self, "format", _technical(self.format))
            object.__setattr__(self, "quantization", _technical(self.quantization, upper=True))
            object.__setattr__(self, "quantization_method", _technical(self.quantization_method))
        except ValueError:
            raise _invalid_query() from None
        if self.model_only:
            if self.repository_type == "dataset":
                raise _invalid_query()
            object.__setattr__(self, "repository_type", "model")

    @property
    def model_only(self) -> bool:
        """Whether a predicate requires an eligible model variant."""
        return any(
            value is not None
            for value in (
                self.quantization,
                self.quantization_method,
                self.bits,
                self.max_variant_bytes,
            )
        )

    @property
    def technical_required(self) -> bool:
        """Whether unknown technical observations can affect the answer."""
        return self.format is not None or self.model_only

    def canonical_filters(self) -> dict[str, object]:
        """JSON-compatible semantic identity; page size and continuation are independent."""
        return {
            "repository_type": self.repository_type,
            "q": self.q,
            "tags_all": list(self.tags_all),
            "tags_any": list(self.tags_any),
            "tag_source": self.tag_source,
            "scope": self.scope,
            "revision_scope": self.revision_scope,
            "format": self.format,
            "quantization": self.quantization,
            "quantization_method": self.quantization_method,
            "bits": self.bits,
            "max_variant_bytes": self.max_variant_bytes,
        }


def _ordered(values: tuple[str, ...]) -> None:
    if values != tuple(sorted(set(values))):
        msg = "Catalog arrays must be sorted and unique"
        raise ValueError(msg)


def _canonical_tags(value: object) -> tuple[str, ...]:
    canonical = normalize_tags(value)
    if not isinstance(value, (tuple, list)) or tuple(value) != canonical:
        msg = "Catalog tags must already be canonical"
        raise ValueError(msg)
    return canonical


CanonicalTags = Annotated[tuple[str, ...], BeforeValidator(_canonical_tags), Field(max_length=64)]


class CatalogCoverage(DurableModel):
    """Whole scoped coverage, independent of pages and the core's incompleteness policy."""

    repositories: Count
    tags_known: Count
    tags_unknown: Count
    publications: Count
    usable: Count
    partial: Count
    unsupported: Count
    failed: Count
    missing: Count
    technical_required: bool
    incomplete: bool

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        if self.tags_known + self.tags_unknown != self.repositories or (
            self.usable + self.partial + self.unsupported + self.failed + self.missing
            != self.publications
        ):
            msg = "Catalog coverage counts must partition scoped repositories and publications"
            raise ValueError(msg)
        return self


class QualifiedVariant(DurableModel):
    """Variant identity is qualified by its exact retained publication."""

    commit_sha: CommitShaField
    publication_id: PublicationIdField
    publication_generation: Generation
    variant: ModelVariant


class CatalogEntry(DurableModel):
    """One repository's bounded summary, including current or observed tag provenance."""

    repository_type: RepositoryTypeField
    repository_id: RepositoryIdField
    tags: CanonicalTags
    tag_origin: Literal["configured", "last_observed", "unknown"]
    tag_observed_at: Timestamp | None
    curation_fingerprint: Sha256 | None
    configured: bool
    enabled: bool | None
    archived: bool
    matching_variant_count: Count
    representative_variant: QualifiedVariant | None
    dataset_formats: Formats

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        _ordered(self.dataset_formats)
        if any(value != value.translate(_LOWER) for value in self.dataset_formats):
            msg = "Catalog formats must use canonical lowercase identifiers"
            raise ValueError(msg)
        if self.configured != (self.enabled is not None):
            msg = "Only configured catalog entries have an enabled state"
            raise ValueError(msg)
        if (self.tag_origin == "configured") != self.configured:
            msg = "Current tag provenance must agree with configured state"
            raise ValueError(msg)
        if self.tag_origin == "unknown" and (
            self.tags or self.tag_observed_at is not None or self.curation_fingerprint is not None
        ):
            msg = "Unknown tags cannot carry invented labels or observation provenance"
            raise ValueError(msg)
        if self.repository_type == "dataset" and (
            self.matching_variant_count or self.representative_variant is not None
        ):
            msg = "Dataset entries cannot report model variants"
            raise ValueError(msg)
        if self.repository_type == "model" and self.dataset_formats:
            msg = "Model entries cannot report dataset formats"
            raise ValueError(msg)
        if self.representative_variant is not None and not self.matching_variant_count:
            msg = "A representative requires a matching variant"
            raise ValueError(msg)
        if not self.archived and (self.matching_variant_count or self.representative_variant):
            msg = "Unarchived entries cannot report retained model variants"
            raise ValueError(msg)
        return self


class ObservationSummary(DurableModel):
    """Bounded attributed declarations without a nested model-variant collection."""

    commit_sha: CommitShaField
    publication_id: PublicationIdField
    publication_generation: Generation
    extractor_version: Identifier
    observed_at: Timestamp
    status: Literal["complete", "partial", "unsupported", "failed"]
    sources: Annotated[
        tuple[SourceObservation, ...], BeforeValidator(as_tuple), Field(max_length=4096)
    ]
    dataset_formats: Formats
    diagnostics: Diagnostics

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        keys = tuple((source.path, source.field, source.evidence) for source in self.sources)
        if keys != tuple(sorted(set(keys))):
            msg = "Observation sources must be sorted and unique"
            raise ValueError(msg)
        _ordered(self.dataset_formats)
        _ordered(self.diagnostics)
        return self


class CatalogPayload(DurableModel):
    """Independent strict schema 1 inside the existing unmodified read/result wrappers."""

    schema_version: Literal[1] = 1
    catalog_identity: Sha256
    coverage: CatalogCoverage

    @field_validator("schema_version", mode="before")
    @classmethod
    def _version(cls, value: object) -> object:
        if type(value) is not int or value != 1:
            msg = "Unsupported catalog payload schema"
            raise ValueError(msg)
        return value


class CatalogSearchPayload(CatalogPayload):
    total_matches: Count
    entries: Annotated[
        tuple[CatalogEntry, ...], BeforeValidator(as_tuple), Field(max_length=MAX_PAGE_ENTRIES)
    ]

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        keys = tuple((entry.repository_type, entry.repository_id) for entry in self.entries)
        if (
            keys != tuple(sorted(set(keys)))
            or len(self.entries) > self.total_matches
            or self.total_matches > self.coverage.repositories
        ):
            msg = "Catalog search entries disagree with ordering or scoped match counts"
            raise ValueError(msg)
        return self


class CatalogDetailPayload(CatalogPayload):
    entry: CatalogEntry
    observations: Annotated[
        tuple[ObservationSummary, ...], BeforeValidator(as_tuple), Field(max_length=64)
    ]

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        keys = tuple((item.commit_sha, item.publication_id) for item in self.observations)
        if len(keys) != len(set(keys)):
            msg = "Catalog observation summaries must identify distinct publications"
            raise ValueError(msg)
        return self


class CatalogVariantsPayload(CatalogPayload):
    total_matches: Count
    entries: Annotated[
        tuple[QualifiedVariant, ...], BeforeValidator(as_tuple), Field(max_length=MAX_PAGE_ENTRIES)
    ]

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        keys = tuple(
            (item.commit_sha, item.publication_id, item.variant.variant_id) for item in self.entries
        )
        if len(keys) != len(set(keys)) or len(self.entries) > self.total_matches:
            msg = "Catalog variant entries must be distinct and fit the known match count"
            raise ValueError(msg)
        return self


class CatalogFacetValue(DurableModel):
    value: Annotated[str, Field(min_length=1, max_length=64)]
    repository_count: Count

    @field_validator("value")
    @classmethod
    def _safe_value(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,63}", value):
            msg = "Invalid catalog facet value"
            raise ValueError(msg)
        return value


class CatalogFacetPayload(CatalogPayload):
    facet: Facet
    total_matches: Count
    entries: Annotated[
        tuple[CatalogFacetValue, ...], BeforeValidator(as_tuple), Field(max_length=MAX_PAGE_ENTRIES)
    ]

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        values = tuple(entry.value for entry in self.entries)
        _ordered(values)
        if len(self.entries) > self.total_matches or any(
            entry.repository_count > self.coverage.repositories for entry in self.entries
        ):
            msg = "Catalog facet counts exceed the scoped known values or repositories"
            raise ValueError(msg)
        for value in values:
            if self.facet == "tag":
                _canonical_tags((value,))
            elif _technical(value, upper=self.facet == "quantization") != value:
                msg = "Catalog technical facets must use canonical identifiers"
                raise ValueError(msg)
        return self
