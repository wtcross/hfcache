"""App-owned catalog read facade with no generic public dispatcher."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from hfcache.catalog_query_models import CatalogQuery
    from hfcache.identity import RepositoryIdentity
    from hfcache.mcp_catalog_tools import Facet, RevisionScope
    from hfcache.services.catalog_queries import CatalogQueries
    from hfcache.services.mcp_queries import MetadataRead, QueryPage

    type ExecuteCatalog = Callable[[Callable[[CatalogQueries], QueryPage]], Awaitable[MetadataRead]]


class CatalogReadAdapter:
    """Only five named async reads reach tools; ownership remains in the app."""

    __slots__ = ("_execute",)

    def __init__(self, execute: ExecuteCatalog) -> None:
        self._execute = execute

    async def search_models(self, query: CatalogQuery) -> MetadataRead:
        return await self._execute(lambda reads: reads.search(query, route="search_models"))

    async def search_datasets(self, query: CatalogQuery) -> MetadataRead:
        return await self._execute(lambda reads: reads.search(query, route="search_datasets"))

    async def get_catalog_entry(
        self,
        identity: RepositoryIdentity,
        revision_scope: RevisionScope,
        commit_sha: str | None,
        publication_id: str | None,
    ) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.detail(
                identity,
                revision_scope=revision_scope,
                commit_sha=commit_sha,
                publication_id=publication_id,
                route="get_catalog_entry",
            )
        )

    async def list_model_variants(  # noqa: PLR0913, PLR0917 - exact publication and page
        self,
        identity: RepositoryIdentity,
        revision_scope: RevisionScope,
        commit_sha: str | None,
        publication_id: str | None,
        limit: int | None,
        cursor: str | None,
    ) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.variants(
                identity,
                revision_scope=revision_scope,
                commit_sha=commit_sha,
                publication_id=publication_id,
                limit=limit,
                cursor=cursor,
                route="list_model_variants",
            )
        )

    async def get_catalog_facets(self, facet: Facet, query: CatalogQuery) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.facets(facet, query, route="get_catalog_facets")
        )
