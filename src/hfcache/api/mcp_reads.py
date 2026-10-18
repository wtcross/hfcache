"""App-owned async facade over only named transport-neutral metadata reads."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from hfcache.mcp_tools import ManifestCollection, RepositoryType
    from hfcache.services.mcp_queries import MetadataRead, MetadataReadQueries, QueryPage

    type ExecuteRead = Callable[
        [Callable[[MetadataReadQueries], QueryPage]], Awaitable[MetadataRead]
    ]


class MetadataReadAdapter:
    """Expose no Request, app, command, Hub or writable storage attribute to tools."""

    __slots__ = ("_execute",)

    def __init__(self, execute: ExecuteRead) -> None:
        self._execute = execute

    async def get_archive_status(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.get_archive_status(selectors, repository_type, limit, cursor)
        )

    async def list_repositories(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.list_repositories(selectors, repository_type, limit, cursor)
        )

    async def list_revisions(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.list_revisions(selectors, repository_type, limit, cursor)
        )

    async def get_current_reference(
        self, repository_type: RepositoryType, repository_id: str
    ) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.get_current_reference(repository_type, repository_id)
        )

    async def get_revision_manifest(  # noqa: PLR0913, PLR0917 - exact publication and page fields
        self,
        repository_type: RepositoryType,
        repository_id: str,
        commit_sha: str,
        publication_id: str,
        collection: ManifestCollection = "files",
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.get_revision_manifest(
                repository_type,
                repository_id,
                commit_sha,
                publication_id,
                collection,
                limit,
                cursor,
            )
        )

    async def list_run_reports(
        self, limit: int | None = None, cursor: str | None = None
    ) -> MetadataRead:
        return await self._execute(lambda reads: reads.list_run_reports(limit, cursor))

    async def get_run_report(
        self, run_id: str, limit: int | None = None, cursor: str | None = None
    ) -> MetadataRead:
        return await self._execute(lambda reads: reads.get_run_report(run_id, limit, cursor))

    async def get_verification_report(
        self, run_id: str, limit: int | None = None, cursor: str | None = None
    ) -> MetadataRead:
        return await self._execute(
            lambda reads: reads.get_verification_report(run_id, limit, cursor)
        )

    async def estimate_verification(self) -> MetadataRead:
        return await self._execute(lambda reads: reads.estimate_verification())
