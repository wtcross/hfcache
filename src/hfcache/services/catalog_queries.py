"""Bounded lock-free discovery over exact refs and inert adjuncts (INV-018)."""

import base64
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from hfcache.catalog_gguf import FILE_TYPES
from hfcache.catalog_inventory import CatalogInventory
from hfcache.catalog_models import EXTRACTOR_VERSION, ModelVariant, PublicationObservation
from hfcache.catalog_query_models import (
    CatalogCoverage,
    CatalogDetailPayload,
    CatalogEntry,
    CatalogFacetPayload,
    CatalogFacetValue,
    CatalogQuery,
    CatalogSearchPayload,
    CatalogVariantsPayload,
    Facet,
    ObservationSummary,
    QualifiedVariant,
)
from hfcache.catalog_storage import (
    RECORD_BOUNDS,
    check_namespace,
    publication_binding,
    read_authority,
    read_publication_observation,
    read_tag_snapshot,
)
from hfcache.errors import IntegrityError, Problem, RequestError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.metadata import MetadataReader, QueryBounds, QueryLimitError
from hfcache.models import ArchiveSentinel
from hfcache.paths import ArchiveLayout
from hfcache.redaction import redact_text, sanitize
from hfcache.services.context import ServiceResult
from hfcache.services.mcp_queries import QueryPage

if TYPE_CHECKING:
    from hfcache.config import ApplicationConfig, RepositoryConfig

MAXIMUM_PROJECTION_BYTES = 32 * 1024 * 1024
MAXIMUM_ROWS = 100_000
MAXIMUM_PAGE_SIZE = 10_000
MINIMUM_RESPONSE_BYTES = 1024
MAXIMUM_OFFSET_DIGITS = 12
MAXIMUM_SUMMARIES = 64
AWQ_BITS = 4
DEFAULT_QUERY = CatalogQuery()


def _safe(value: object) -> bool:
    return redact_text(str(value)) == str(value)


def _json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _limit() -> QueryLimitError:
    return QueryLimitError.single("Catalog query budget exceeded", code="HFAPI005")


def _digest(value: object) -> str:
    # Numeric scalars may themselves equal registered opaque secrets.
    return hashlib.sha256(redact_text(_json(sanitize(value)).decode()).encode()).hexdigest()


def _eligible(variant: ModelVariant) -> bool:
    if (
        variant.role != "primary"
        or variant.completeness != "complete"
        or variant.total_bytes is None
        or variant.evidence not in {"header", "declaration"}
    ):
        return False
    if variant.format == "gguf":
        return any(
            variant.encoding == encoding
            and variant.quantization == scheme
            and variant.quantization_method == ("ggml" if scheme else None)
            and (variant.bits is None or variant.bits == bits)
            for encoding, scheme, bits in FILE_TYPES.values()
        )
    return (
        variant.format in {"safetensors", "pytorch_bin"}
        and variant.quantization is None
        and (
            (variant.quantization_method == "awq" and variant.bits == AWQ_BITS)
            or (variant.quantization_method == "gptq" and variant.bits in {2, 3, 4, 8})
        )
    )


def _matches(variant: ModelVariant, query: CatalogQuery) -> bool:
    return (
        _eligible(variant)
        and all(
            requested is None or requested == actual
            for requested, actual in (
                (query.format, variant.format),
                (query.quantization, variant.quantization),
                (query.quantization_method, variant.quantization_method),
                (query.bits, variant.bits),
            )
        )
        and (
            query.max_variant_bytes is None
            or (variant.total_bytes is not None and variant.total_bytes <= query.max_variant_bytes)
        )
    )


def _variant(value: ModelVariant, *, supported: bool) -> ModelVariant | None:
    required = (
        value.format,
        value.role,
        value.completeness,
        value.evidence,
        *(member.path for member in value.members),
        *(member.size_bytes for member in value.members),
        *value.source_paths,
    )
    if not all(_safe(item) for item in required) or (
        value.total_bytes is not None and not _safe(value.total_bytes)
    ):
        return None
    updates: dict[str, Any] = {
        field: getattr(value, field) if _safe(getattr(value, field)) else None
        for field in ("encoding", "quantization", "quantization_method", "bits", "group_size")
    }
    updates["diagnostics"] = tuple(item for item in value.diagnostics if _safe(item))
    if not supported:
        updates["completeness"] = "unknown"
    if not _safe(value.variant_id):
        return None
    return value.model_copy(update=updates)


@dataclass(frozen=True, slots=True)
class _Row:
    entry: CatalogEntry
    effective_tags: tuple[str, ...]
    variants: tuple[QualifiedVariant, ...]
    observations: tuple[ObservationSummary, ...]
    states: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Snapshot:
    rows: tuple[_Row, ...]
    coverage: CatalogCoverage
    identity: str


@dataclass(frozen=True, slots=True)
class CatalogQueries:
    """Read-only finite capability; callers provide fresh validated installed config."""

    config: ApplicationConfig
    bounds: QueryBounds = RECORD_BOUNDS
    max_page_size: int = 1000
    max_response_bytes: int = 8 * 1024 * 1024

    def __post_init__(self) -> None:
        if (
            type(self.max_page_size) is not int
            or not 1 <= self.max_page_size <= MAXIMUM_PAGE_SIZE
            or type(self.max_response_bytes) is not int
            or self.max_response_bytes < MINIMUM_RESPONSE_BYTES
            or any(
                value is None
                for value in (
                    self.bounds.maximum_entries,
                    self.bounds.maximum_artifact_bytes,
                    self.bounds.maximum_total_bytes,
                )
            )
        ):
            raise _limit()

    def _observation(
        self,
        record: PublicationObservation,
    ) -> tuple[ObservationSummary, tuple[QualifiedVariant, ...], str]:
        supported = record.extractor_version == EXTRACTOR_VERSION
        usable = supported and record.status in {"complete", "partial"}
        variants = tuple(
            QualifiedVariant(
                commit_sha=record.commit_sha,
                publication_id=record.publication_id,
                publication_generation=record.publication_generation,
                variant=clean,
            )
            for value in record.variants
            if (clean := _variant(value, supported=usable)) is not None
        )
        sources = tuple(
            source.model_copy(update={"values": tuple(v for v in source.values if _safe(v))})
            for source in record.sources
            if all(_safe(v) for v in (source.path, source.sha256, source.field, source.evidence))
        )
        formats = (
            tuple(
                value for value in record.dataset_formats if _safe(value) and value == value.lower()
            )
            if usable
            else ()
        )
        state = record.status if supported else "unsupported"
        if state == "complete" and (
            len(variants) != len(record.variants)
            or sources != record.sources
            or formats != record.dataset_formats
            or any(a.variant != b for a, b in zip(variants, record.variants, strict=False))
        ):
            state = "partial"
        return (
            ObservationSummary(
                commit_sha=record.commit_sha,
                publication_id=record.publication_id,
                publication_generation=record.publication_generation,
                extractor_version=record.extractor_version
                if _safe(record.extractor_version)
                else "unknown",
                observed_at=record.observed_at,
                status=state,
                sources=sources,
                dataset_formats=formats,
                diagnostics=tuple(value for value in record.diagnostics if _safe(value)),
            ),
            variants,
            "usable" if state == "complete" else state,
        )

    def _row(  # noqa: PLR0913, PLR0917 - shared reader and exact scoped authority
        self,
        identity: RepositoryIdentity,
        configured: RepositoryConfig | None,
        refs: tuple[Any, ...],
        query: CatalogQuery,
        reader: MetadataReader,
        layout: ArchiveLayout,
    ) -> _Row:
        tag_snapshot = (
            None
            if configured
            else read_tag_snapshot(
                layout,
                identity,
                self.config.storage.archive_id,
                reader=reader,
            )
        )
        raw_tags = configured.tags if configured else (tag_snapshot.tags if tag_snapshot else ())
        tags = tuple(value for value in raw_tags if _safe(value))
        origin = "configured" if configured else ("last_observed" if tag_snapshot else "unknown")
        summaries, variants, states = [], [], []
        for ref in refs:
            sha, publication = CommitSha(ref.commit_sha), PublicationId(ref.publication_id)
            publication_binding(layout, identity, sha, publication, reader=reader)
            record = read_publication_observation(
                layout,
                identity,
                sha,
                publication,
                self.config.storage.archive_id,
                reader=reader,
            )
            if record is None:
                states.append("missing")
            elif not all(
                _safe(v)
                for v in (
                    ref.commit_sha,
                    ref.publication_id,
                    ref.publication_generation,
                    record.observed_at,
                )
            ):
                states.append("partial")
            else:
                summary, values, state = self._observation(record)
                summaries.append(summary)
                variants.extend(values)
                states.append(state)
        variants.sort(
            key=lambda v: (
                v.publication_generation,
                v.commit_sha,
                v.publication_id,
                v.variant.variant_id,
            )
        )
        eligible = [value for value in variants if _matches(value.variant, query)]
        formats = tuple(sorted({value for item in summaries for value in item.dataset_formats}))
        entry = CatalogEntry(
            repository_type=identity.type,
            repository_id=identity.id,
            tags=tags,
            tag_origin=origin,
            tag_observed_at=tag_snapshot.observed_at
            if tag_snapshot and _safe(tag_snapshot.observed_at)
            else None,
            curation_fingerprint=None,
            configured=configured is not None,
            enabled=configured.enabled if configured else None,
            archived=bool(refs),
            matching_variant_count=len(eligible),
            representative_variant=eligible[0] if eligible else None,
            dataset_formats=formats,
        )
        return _Row(
            entry,
            tags if configured or query.tag_source != "current_only" else (),
            tuple(variants),
            tuple(summaries),
            tuple(states),
        )

    def _snapshot(  # noqa: PLR0912, PLR0915 - bounded explicit selection branches
        self,
        query: CatalogQuery,
        *,
        identity: RepositoryIdentity | None = None,
        exact: tuple[str, str] | None = None,
    ) -> _Snapshot:
        if identity is not None and not _safe(identity.id):
            raise RequestError(code="HFAPI007", status_code=404)
        layout = ArchiveLayout(self.config.storage.archive_root)
        reader = MetadataReader(layout.root, self.bounds)
        sentinel, _ = read_authority(layout.sentinel, ArchiveSentinel, reader)
        if sentinel.archive_id != self.config.storage.archive_id:
            message = "Catalog archive identity mismatch"
            raise IntegrityError.single(message, code="HFVER007")
        if len(self.config.repositories) > MAXIMUM_ROWS:
            raise _limit()
        configured = {
            RepositoryIdentity.from_config(value): value for value in self.config.repositories
        }
        check_namespace(layout, reader)
        inventory = CatalogInventory(layout, reader)
        archived = (
            inventory.archived()
            if identity is None and query.scope != "configured"
            else {key: refs for key in configured if (refs := inventory.retained(key))}
            if identity is None
            else {identity: refs}
            if (refs := inventory.retained(identity))
            else {}
        )
        selected = (
            set(configured)
            if query.scope == "configured"
            else set(archived)
            if query.scope == "archived"
            else set(configured) | set(archived)
        )
        if identity is not None:
            selected &= {identity}
            if not selected:
                raise RequestError(code="HFAPI007", status_code=404, message="Catalog entry absent")
        if len(selected) > MAXIMUM_ROWS:
            raise _limit()
        rows = []
        projection_bytes = 0
        visible_refs = []
        for item in sorted(selected, key=lambda i: (i.type, i.id)):
            if not _safe(item.id) or (query.repository_type and item.type != query.repository_type):
                continue
            retained = archived.get(item, ())
            if exact is not None:
                refs = tuple(
                    ref for ref in retained if (ref.commit_sha, ref.publication_id) == exact
                )
                if not refs:
                    raise RequestError(
                        code="HFAPI007", status_code=404, message="Publication absent"
                    )
            elif query.revision_scope == "retained":
                refs = retained
            else:
                current = inventory.current(item)
                if retained and current is None:
                    message = "Current catalog reference absent"
                    raise IntegrityError.single(message, code="HFVER008")
                refs = (current,) if current else ()
            row = self._row(item, configured.get(item), refs, query, reader, layout)
            projection = (
                row.entry.model_dump(mode="json"),
                [v.model_dump(mode="json") for v in row.variants],
                [v.model_dump(mode="json") for v in row.observations],
                row.states,
            )
            projection_bytes += len(_json(projection))
            if projection_bytes > MAXIMUM_PROJECTION_BYTES:
                raise _limit()
            visible_refs.append(
                (
                    item.selector,
                    [
                        {
                            field: getattr(ref, field)
                            for field in (
                                "commit_sha",
                                "publication_id",
                                "publication_generation",
                            )
                            if _safe(getattr(ref, field))
                        }
                        for ref in refs
                    ],
                    projection,
                )
            )
            rows.append(row)
        states = Counter(state for row in rows for state in row.states)
        unknown = sum(row.entry.tag_origin == "unknown" for row in rows)
        coverage = CatalogCoverage(
            repositories=len(rows),
            tags_known=len(rows) - unknown,
            tags_unknown=unknown,
            publications=sum(states.values()),
            usable=states["usable"],
            partial=states["partial"],
            unsupported=states["unsupported"],
            failed=states["failed"],
            missing=states["missing"],
            technical_required=query.technical_required,
            incomplete=bool(sum(v for k, v in states.items() if k != "usable") or unknown),
        )
        # Opaque old fingerprints can hash hidden labels/paths. Bind only the
        # visible policy and projections; existing policy identities stay unchanged.
        policy = self.config.model_dump(mode="json", exclude={"repositories"})
        policy.get("hub", {}).pop("credential_name", None)
        visible_policy = [
            value.model_dump(mode="json", exclude={"tags"})
            | {"tags": [tag for tag in value.tags if _safe(tag)]}
            for value in self.config.repositories
            if _safe(value.id)
        ]
        digest = _digest(
            (
                sentinel.archive_id,
                identity.selector if identity else None,
                exact,
                policy,
                visible_policy,
                query.canonical_filters(),
                visible_refs,
                coverage.model_dump(mode="json"),
            )
        )
        return _Snapshot(tuple(rows), coverage, digest)

    @staticmethod
    def _match(row: _Row, query: CatalogQuery) -> bool:
        if not set(query.tags_all) <= set(row.effective_tags) or (
            query.tags_any and not set(query.tags_any) & set(row.effective_tags)
        ):
            return False
        if (
            query.q
            and query.q not in row.entry.repository_id.casefold()
            and not any(query.q in value.casefold() for value in row.effective_tags)
        ):
            return False
        if not query.technical_required:
            return True
        if row.entry.repository_type == "dataset":
            return query.format in row.entry.dataset_formats
        return bool(row.entry.matching_variant_count)

    def _page(
        self,
        items: list[Any],
        query: CatalogQuery,
        snapshot: _Snapshot,
        route: str,
        payload: type[Any],
        **fields: object,
    ) -> QueryPage:
        size = min(100, self.max_page_size) if query.limit is None else query.limit
        if size > self.max_page_size:
            raise RequestError
        identity = _digest((route, snapshot.identity, fields.get("facet")))
        offset = 0
        if query.cursor is not None:
            try:
                held, number = (
                    base64.b64decode(
                        query.cursor,
                        altchars=b"-_",
                        validate=True,
                    )
                    .decode("ascii")
                    .split(":")
                )
                if not number.isdecimal() or len(number) > MAXIMUM_OFFSET_DIGITS:
                    raise ValueError  # noqa: TRY301 - fixed cursor refusal
                offset = int(number)
            except ValueError, UnicodeError:
                raise RequestError from None
            if held != identity or offset > len(items):
                raise RequestError(code="HFAPI007", status_code=409)
        end = offset + size
        following = (
            base64.urlsafe_b64encode(f"{identity}:{end}".encode()).decode()
            if end < len(items)
            else None
        )
        data = payload(
            catalog_identity=snapshot.identity,
            coverage=snapshot.coverage,
            total_matches=len(items),
            entries=items[offset:end],
            **fields,
        ).model_dump(mode="json")
        return self._result(route, data, snapshot, following)

    def _result(
        self,
        route: str,
        data: dict[str, Any],
        snapshot: _Snapshot,
        following: str | None = None,
    ) -> QueryPage:
        if len(_json(data)) > self.max_response_bytes:
            raise _limit()
        warnings = (
            (Problem("HFWRN011", "Catalog coverage is incomplete"),)
            if snapshot.coverage.incomplete
            else ()
        )
        return QueryPage(ServiceResult(route, data, warnings), following)

    def search(
        self, query: CatalogQuery = DEFAULT_QUERY, *, route: str = "catalog.search"
    ) -> QueryPage:
        snapshot = self._snapshot(query)
        return self._page(
            [row.entry for row in snapshot.rows if self._match(row, query)],
            query,
            snapshot,
            route,
            CatalogSearchPayload,
        )

    def facets(
        self,
        facet: Facet,
        query: CatalogQuery = DEFAULT_QUERY,
        *,
        route: str = "catalog.facets",
    ) -> QueryPage:
        if facet not in {"tag", "format", "quantization_method", "quantization"}:
            raise RequestError
        snapshot = self._snapshot(query)
        counts: Counter[str] = Counter()
        for row in snapshot.rows:
            if not self._match(row, query):
                continue
            if facet == "tag":
                values = set(row.effective_tags)
            elif row.entry.repository_type == "dataset":
                values = (
                    {
                        v
                        for v in row.entry.dataset_formats
                        if query.format is None or v == query.format
                    }
                    if facet == "format"
                    else set()
                )
            else:
                values = {
                    value
                    for item in row.variants
                    if _matches(item.variant, query)
                    if (value := getattr(item.variant, facet)) is not None
                }
            counts.update(values)
        return self._page(
            [
                CatalogFacetValue(value=value, repository_count=counts[value])
                for value in sorted(counts)
            ],
            query,
            snapshot,
            route,
            CatalogFacetPayload,
            facet=facet,
        )

    @staticmethod
    def _exact(commit_sha: str | None, publication_id: str | None) -> tuple[str, str] | None:
        if (commit_sha is None) != (publication_id is None):
            raise RequestError
        if any(value is not None and not _safe(value) for value in (commit_sha, publication_id)):
            raise RequestError
        return (
            (CommitSha(commit_sha), PublicationId(publication_id))
            if commit_sha is not None and publication_id is not None
            else None
        )

    def detail(
        self,
        identity: RepositoryIdentity,
        *,
        revision_scope: Literal["current", "retained"] = "current",
        commit_sha: str | None = None,
        publication_id: str | None = None,
        route: str = "catalog.detail",
    ) -> QueryPage:
        query = CatalogQuery(scope="all", revision_scope=revision_scope)
        snapshot = self._snapshot(
            query, identity=identity, exact=self._exact(commit_sha, publication_id)
        )
        if not snapshot.rows:
            raise RequestError(code="HFAPI007", status_code=404)
        row = snapshot.rows[0]
        if len(row.observations) > MAXIMUM_SUMMARIES:
            raise _limit()
        data = CatalogDetailPayload(
            catalog_identity=snapshot.identity,
            coverage=snapshot.coverage,
            entry=row.entry,
            observations=row.observations,
        ).model_dump(mode="json")
        return self._result(route, data, snapshot)

    def variants(  # noqa: PLR0913 - exact optional publication selector and paging
        self,
        identity: RepositoryIdentity,
        *,
        revision_scope: Literal["current", "retained"] = "current",
        commit_sha: str | None = None,
        publication_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        route: str = "catalog.variants",
    ) -> QueryPage:
        if identity.type != "model":
            raise RequestError
        query = CatalogQuery(scope="all", revision_scope=revision_scope, limit=limit, cursor=cursor)
        snapshot = self._snapshot(
            query, identity=identity, exact=self._exact(commit_sha, publication_id)
        )
        return self._page(
            [value for row in snapshot.rows for value in row.variants],
            query,
            snapshot,
            route,
            CatalogVariantsPayload,
        )
