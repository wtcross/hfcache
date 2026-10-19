"""Five explicit catalog tools with only an async read capability."""

from typing import TYPE_CHECKING, Annotated, Literal, Protocol

from mcp.types import ToolAnnotations
from pydantic import Field

from hfcache.catalog_query_models import CatalogQuery
from hfcache.identity import RepositoryIdentity
from hfcache.mcp_tools import Cursor, Identifier, RepositoryType, read_metadata
from hfcache.services.mcp_queries import MetadataRead  # noqa: TC001 - output schema

if TYPE_CHECKING:
    from fastmcp import FastMCP

RevisionScope = Literal["current", "retained"]
Scope = Literal["archived", "configured", "all"]
TagSource = Literal["current_or_last_observed", "current_only"]
Facet = Literal["tag", "format", "quantization_method", "quantization"]
QueryText = Annotated[str, Field(max_length=256)]
Tag = Annotated[str, Field(max_length=128)]
Tags = Annotated[list[Tag], Field(max_length=64)]
Filter = Annotated[str, Field(min_length=1, max_length=64)]
Bits = Annotated[int, Field(ge=1, le=64)]
VariantBytes = Annotated[int, Field(ge=0, le=2**63 - 1)]


class CatalogReadPort(Protocol):
    """Five reads; no request, commands, credentials or writable storage."""

    async def search_models(self, query: CatalogQuery) -> MetadataRead: ...

    async def search_datasets(self, query: CatalogQuery) -> MetadataRead: ...

    async def get_catalog_entry(
        self,
        identity: RepositoryIdentity,
        revision_scope: RevisionScope,
        commit_sha: str | None,
        publication_id: str | None,
    ) -> MetadataRead: ...

    async def list_model_variants(  # noqa: PLR0913, PLR0917 - exact identity and page
        self,
        identity: RepositoryIdentity,
        revision_scope: RevisionScope,
        commit_sha: str | None,
        publication_id: str | None,
        limit: int | None,
        cursor: str | None,
    ) -> MetadataRead: ...

    async def get_catalog_facets(self, facet: Facet, query: CatalogQuery) -> MetadataRead: ...


def install_catalog_tools(server: FastMCP, reads: CatalogReadPort, *, max_page_size: int) -> None:
    """Register only reviewed named reads; strict schemas precede query intent."""
    hints = ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    )

    @server.tool(annotations=hints, task=False)
    async def search_models(  # noqa: PLR0913 - explicit bounded filter schema
        *,
        q: QueryText = "",
        tags_all: Tags | None = None,
        tags_any: Tags | None = None,
        tag_source: TagSource = "current_or_last_observed",
        scope: Scope = "archived",
        revision_scope: RevisionScope = "current",
        format: Filter | None = None,  # noqa: A002 - public catalog field
        quantization: Filter | None = None,
        quantization_method: Filter | None = None,
        bits: Bits | None = None,
        max_variant_bytes: VariantBytes | None = None,
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """Search local labels and one complete model variant; coverage stays explicit."""
        return await read_metadata(
            lambda: reads.search_models(
                CatalogQuery(
                    repository_type="model",
                    q=q,
                    tags_all=tuple(tags_all or ()),
                    tags_any=tuple(tags_any or ()),
                    tag_source=tag_source,
                    scope=scope,
                    revision_scope=revision_scope,
                    format=format,
                    quantization=quantization,
                    quantization_method=quantization_method,
                    bits=bits,
                    max_variant_bytes=max_variant_bytes,
                    limit=limit,
                    cursor=cursor,
                )
            )
        )

    @server.tool(annotations=hints, task=False)
    async def search_datasets(  # noqa: PLR0913 - explicit bounded dataset schema
        *,
        q: QueryText = "",
        tags_all: Tags | None = None,
        tags_any: Tags | None = None,
        tag_source: TagSource = "current_or_last_observed",
        scope: Scope = "archived",
        revision_scope: RevisionScope = "current",
        format: Filter | None = None,  # noqa: A002 - public catalog field
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """Search local dataset labels and attributed static formats; never execute a loader."""
        return await read_metadata(
            lambda: reads.search_datasets(
                CatalogQuery(
                    repository_type="dataset",
                    q=q,
                    tags_all=tuple(tags_all or ()),
                    tags_any=tuple(tags_any or ()),
                    tag_source=tag_source,
                    scope=scope,
                    revision_scope=revision_scope,
                    format=format,
                    limit=limit,
                    cursor=cursor,
                )
            )
        )

    @server.tool(annotations=hints, task=False)
    async def get_catalog_entry(
        repository_type: RepositoryType,
        repository_id: Identifier,
        *,
        revision_scope: RevisionScope = "current",
        commit_sha: Identifier | None = None,
        publication_id: Identifier | None = None,
    ) -> MetadataRead:
        """Read catalog provenance and coverage for one repository or exact paired publication."""
        return await read_metadata(
            lambda: reads.get_catalog_entry(
                RepositoryIdentity.of(repository_type, repository_id),
                revision_scope,
                commit_sha,
                publication_id,
            )
        )

    @server.tool(annotations=hints, task=False)
    async def list_model_variants(  # noqa: PLR0913 - exact publication and page schema
        repository_id: Identifier,
        *,
        revision_scope: RevisionScope = "current",
        commit_sha: Identifier | None = None,
        publication_id: Identifier | None = None,
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """List exact model variants with completeness and provenance; never read payloads."""
        return await read_metadata(
            lambda: reads.list_model_variants(
                RepositoryIdentity.of("model", repository_id),
                revision_scope,
                commit_sha,
                publication_id,
                limit,
                cursor,
            )
        )

    @server.tool(annotations=hints, task=False)
    async def get_catalog_facets(  # noqa: PLR0913 - explicit bounded facet schema
        facet: Facet,
        *,
        repository_type: RepositoryType | None = None,
        q: QueryText = "",
        tags_all: Tags | None = None,
        tags_any: Tags | None = None,
        tag_source: TagSource = "current_or_last_observed",
        scope: Scope = "archived",
        revision_scope: RevisionScope = "current",
        format: Filter | None = None,  # noqa: A002 - public catalog field
        quantization: Filter | None = None,
        quantization_method: Filter | None = None,
        bits: Bits | None = None,
        max_variant_bytes: VariantBytes | None = None,
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """Count distinct matching repositories by facet, preserving incomplete coverage."""
        return await read_metadata(
            lambda: reads.get_catalog_facets(
                facet,
                CatalogQuery(
                    repository_type=repository_type,
                    q=q,
                    tags_all=tuple(tags_all or ()),
                    tags_any=tuple(tags_any or ()),
                    tag_source=tag_source,
                    scope=scope,
                    revision_scope=revision_scope,
                    format=format,
                    quantization=quantization,
                    quantization_method=quantization_method,
                    bits=bits,
                    max_variant_bytes=max_variant_bytes,
                    limit=limit,
                    cursor=cursor,
                ),
            )
        )
