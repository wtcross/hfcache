"""Nine explicit metadata adapters; this module receives read methods only.

No ASGI request, SDK context, command service, Hub client, credential resolver or
writable storage object is passed to a tool function. Annotations are hints;
the named read port and the installed boundary enforce the capability.
"""

import re
from typing import TYPE_CHECKING, Annotated, Literal, Protocol

from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from hfcache.errors import HfcacheError
from hfcache.services.mcp_queries import (
    MetadataRead,  # noqa: TC001 - output schema uses runtime model
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from fastmcp import FastMCP

TOOL_NAMES = frozenset(
    {
        "get_archive_status",
        "list_repositories",
        "list_revisions",
        "get_current_reference",
        "get_revision_manifest",
        "list_run_reports",
        "get_run_report",
        "get_verification_report",
        "estimate_verification",
    }
)

RepositoryType = Literal["model", "dataset"]
ManifestCollection = Literal["files", "dependencies"]
Identifier = Annotated[str, Field(min_length=1, max_length=256)]
Selectors = Annotated[list[Identifier], Field(max_length=64)]
Cursor = Annotated[str, Field(min_length=1, max_length=256)]
_CODE = re.compile(r"HF(?:CFG|ARG|API|MNT|TXN|HUB|SYN|VER|RET|WRN|DEP)[0-9]{3}")


class MetadataReadPort(Protocol):
    """Only nine async reads, with no generic dispatch or execution authority."""

    async def get_archive_status(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead: ...

    async def list_repositories(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead: ...

    async def list_revisions(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead: ...

    async def get_current_reference(
        self,
        repository_type: RepositoryType,
        repository_id: str,
    ) -> MetadataRead: ...

    async def get_revision_manifest(  # noqa: PLR0913, PLR0917 - exact publication and page fields
        self,
        repository_type: RepositoryType,
        repository_id: str,
        commit_sha: str,
        publication_id: str,
        collection: ManifestCollection = "files",
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead: ...

    async def list_run_reports(
        self,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead: ...

    async def get_run_report(
        self,
        run_id: str,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead: ...

    async def get_verification_report(
        self,
        run_id: str,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> MetadataRead: ...

    async def estimate_verification(self) -> MetadataRead: ...


async def _read(work: Awaitable[MetadataRead]) -> MetadataRead:
    try:
        return await work
    except HfcacheError as error:
        codes = dict.fromkeys(
            problem.code for problem in error.problems if _CODE.fullmatch(problem.code)
        )
        message = ",".join(codes or {"HFAPI008": None}) + ": metadata query failed"
        raise ToolError(message) from None


def install_read_tools(server: FastMCP, reads: MetadataReadPort, *, max_page_size: int) -> None:
    """Register a closed allowlist with strict schemas and explicit safe hints."""
    hints = ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    )

    @server.tool(annotations=hints, task=False)
    async def get_archive_status(
        selectors: Selectors | None = None,
        repository_type: RepositoryType | None = None,
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """Read archive state and a bounded repository page; unknown confidence stays unknown."""
        return await _read(reads.get_archive_status(selectors, repository_type, limit, cursor))

    @server.tool(annotations=hints, task=False)
    async def list_repositories(
        selectors: Selectors | None = None,
        repository_type: RepositoryType | None = None,
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """List a canonical published inventory page, including unmanaged repositories."""
        return await _read(reads.list_repositories(selectors, repository_type, limit, cursor))

    @server.tool(annotations=hints, task=False)
    async def list_revisions(
        selectors: Selectors | None = None,
        repository_type: RepositoryType | None = None,
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """List a bounded canonical page of exact retained publication identities and confidence."""
        return await _read(reads.list_revisions(selectors, repository_type, limit, cursor))

    @server.tool(annotations=hints, task=False)
    async def get_current_reference(
        repository_type: RepositoryType,
        repository_id: Identifier,
    ) -> MetadataRead:
        """Read and pin the current exact publication; locators are relative to published/."""
        return await _read(reads.get_current_reference(repository_type, repository_id))

    @server.tool(annotations=hints, task=False)
    async def get_revision_manifest(  # noqa: PLR0913, PLR0917 - exact publication and page fields
        repository_type: RepositoryType,
        repository_id: Identifier,
        commit_sha: Identifier,
        publication_id: Identifier,
        collection: ManifestCollection = "files",
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """Read a pinned manifest header and file/dependency page; never substitute an instance."""
        return await _read(
            reads.get_revision_manifest(
                repository_type,
                repository_id,
                commit_sha,
                publication_id,
                collection,
                limit,
                cursor,
            )
        )

    @server.tool(annotations=hints, task=False)
    async def list_run_reports(
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """List a bounded page of existing report IDs; no run is executed or evidence rebuilt."""
        return await _read(reads.list_run_reports(limit, cursor))

    @server.tool(annotations=hints, task=False)
    async def get_run_report(
        run_id: Identifier,
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """Read an existing run, recovery or verification report header and primary records page."""
        return await _read(reads.get_run_report(run_id, limit, cursor))

    @server.tool(annotations=hints, task=False)
    async def get_verification_report(
        run_id: Identifier,
        limit: Annotated[int, Field(ge=1, le=max_page_size)] | None = None,
        cursor: Cursor | None = None,
    ) -> MetadataRead:
        """Read verification evidence by run ID; never hash files or persist verification."""
        return await _read(reads.get_verification_report(run_id, limit, cursor))

    @server.tool(annotations=hints, task=False)
    async def estimate_verification() -> MetadataRead:
        """Estimate verification cost from metadata/stat reads; no hashing, Hub or writes."""
        return await _read(reads.estimate_verification())
