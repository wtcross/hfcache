"""Nine bounded metadata projections over the read capability (decision 125).

This backend has no transport, command, credential or writable-store authority.
Durable models are fully validated by MetadataQueries before explicit paging;
fragments never masquerade as complete durable artifacts (FS-12, INV-016).
"""

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict

from hfcache.errors import CodedError, ConfigurationError, RequestError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, RunId, parse_selector
from hfcache.redaction import redact_text, sanitize
from hfcache.reporting import Envelope, RecoveryReport, VerificationReport
from hfcache.services.context import ServiceResult
from hfcache.services.queries import PublicationQuery, RepositoryQuery

if TYPE_CHECKING:
    from hfcache.services.queries import MetadataQueries

RepositoryType = Literal["model", "dataset"]
ManifestCollection = Literal["files", "dependencies"]
MAXIMUM_PAGE_SIZE = 10000
MAXIMUM_CURSOR_LENGTH = 256
MAXIMUM_OFFSET_DIGITS = 12
MAXIMUM_SELECTORS = 64
MAXIMUM_SELECTOR_LENGTH = 256


class MetadataRead(BaseModel):
    """A typed metadata response, separate from durable schemas and admissions."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    schema_version: Literal[1] = 1
    request_id: str
    archive_id: str
    config_fingerprint: str
    envelope: Envelope
    next_cursor: str | None = None


@dataclass(frozen=True, slots=True)
class QueryPage:
    result: ServiceResult
    next_cursor: str | None = None


@dataclass(frozen=True, slots=True)
class MetadataReadQueries:
    """Projection policy plus a narrow existing reader, never an application."""

    queries: MetadataQueries
    fingerprint: str
    max_page_size: int

    def _page(  # noqa: PLR0913 - fixed page policy, identity and full source binding
        self,
        items: list[Any],
        *,
        limit: int | None,
        cursor: str | None,
        tool: str,
        scope: object,
        source: object,
    ) -> tuple[list[Any], str | None]:
        maximum = self.max_page_size
        if type(maximum) is not int or not 1 <= maximum <= MAXIMUM_PAGE_SIZE:
            raise RequestError
        size = min(100, maximum) if limit is None else limit
        if type(size) is not int or not 1 <= size <= min(MAXIMUM_PAGE_SIZE, maximum):
            raise RequestError
        if cursor is not None and (
            not isinstance(cursor, str)
            or not cursor.isascii()
            or len(cursor) > MAXIMUM_CURSOR_LENGTH
        ):
            raise RequestError
        digest = hashlib.sha256()
        encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=True, allow_nan=False)
        # Bind complete source content, including unreturned artifact headers and
        # collections; offsets alone cannot establish continuation consistency.
        for piece in encoder.iterencode(sanitize((tool, self.fingerprint, scope, source))):
            # Scalar numeric values can themselves equal a registered opaque
            # secret. Cursors must not become secret-derived fingerprints.
            digest.update(redact_text(piece).encode("ascii"))
        identity = digest.hexdigest()[:24]
        offset = 0
        if cursor is not None:
            try:
                decoded = base64.b64decode(cursor, altchars=b"-_", validate=True).decode("ascii")
                held, spelling = decoded.split(":")
                if not spelling.isdecimal() or len(spelling) > MAXIMUM_OFFSET_DIGITS:
                    raise ValueError  # noqa: TRY301 - one sanitized cursor parser
                offset = int(spelling)
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
        return items[offset:end], following

    def _inventory(
        self,
        mode: Literal["status", "repositories", "revisions"],
        *,
        selectors: list[str] | None,
        repository_type: RepositoryType | None,
        limit: int | None,
        cursor: str | None,
    ) -> QueryPage:
        if selectors is not None and (
            not isinstance(selectors, list)
            or len(selectors) > MAXIMUM_SELECTORS
            or any(
                not isinstance(value, str) or len(value) > MAXIMUM_SELECTOR_LENGTH
                for value in selectors
            )
        ):
            raise RequestError
        try:
            query = RepositoryQuery(tuple(selectors or ()), repository_type, mode == "revisions")
            normalized = tuple(
                sorted({parse_selector(value).identity.selector for value in query.selectors})
            )
        except CodedError as error:
            raise RequestError(code=error.code) from None
        found = (
            self.queries.archive_status(query)
            if mode == "status"
            else self.queries.list_repositories(query)
        )
        data = found.data
        if mode == "revisions":
            data = {
                "revisions": [
                    {
                        "repository_type": repository["repository_type"],
                        "repository_id": repository["repository_id"],
                        **revision,
                    }
                    for repository in data["repositories"]
                    for revision in repository["revisions"]
                ]
            }
        field = "revisions" if mode == "revisions" else "repositories"
        rows, following = self._page(
            data[field],
            limit=limit,
            cursor=cursor,
            tool={
                "status": "get_archive_status",
                "repositories": "list_repositories",
                "revisions": "list_revisions",
            }[mode],
            scope=(normalized, repository_type),
            # Capacity/headline observations can change independently of rows.
            # As with REST, inventory continuation binds the complete row set;
            # immutable artifact pages below additionally bind their headers.
            source=data[field],
        )
        return QueryPage(
            ServiceResult(
                found.command,
                data | {field: rows},
                found.warnings,
                found.errors,
                found.exit_code,
                found.run_id,
            ),
            following,
        )

    def get_archive_status(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> QueryPage:
        return self._inventory(
            "status",
            selectors=selectors,
            repository_type=repository_type,
            limit=limit,
            cursor=cursor,
        )

    def list_repositories(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> QueryPage:
        return self._inventory(
            "repositories",
            selectors=selectors,
            repository_type=repository_type,
            limit=limit,
            cursor=cursor,
        )

    def list_revisions(
        self,
        selectors: list[str] | None = None,
        repository_type: RepositoryType | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> QueryPage:
        return self._inventory(
            "revisions",
            selectors=selectors,
            repository_type=repository_type,
            limit=limit,
            cursor=cursor,
        )

    def get_current_reference(
        self, repository_type: RepositoryType, repository_id: str
    ) -> QueryPage:
        found = self.queries.read_reference(_identity(repository_type, repository_id))
        return QueryPage(
            ServiceResult(
                "reference read",
                {"locator_base": "published/", "reference": found.model_dump(mode="json")},
            )
        )

    def get_revision_manifest(  # noqa: PLR0913, PLR0917 - fixed read protocol identity/page fields
        self,
        repository_type: RepositoryType,
        repository_id: str,
        commit_sha: str,
        publication_id: str,
        collection: ManifestCollection = "files",
        limit: int | None = None,
        cursor: str | None = None,
    ) -> QueryPage:
        if collection not in {"files", "dependencies"}:
            raise RequestError
        request = PublicationQuery(
            _identity(repository_type, repository_id),
            CommitSha(commit_sha),
            PublicationId(publication_id),
        )
        found = self.queries.read_manifest(request).model_dump(mode="json")
        entries, following = self._page(
            found[collection],
            limit=limit,
            cursor=cursor,
            tool="get_revision_manifest",
            scope=(repository_type, repository_id, commit_sha, publication_id, collection),
            source=found,
        )
        return QueryPage(
            ServiceResult(
                "manifest read",
                {
                    "projection": True,
                    "manifest": {
                        key: value
                        for key, value in found.items()
                        if key not in {"files", "dependencies"}
                    },
                    "collection": collection,
                    "entries": entries,
                    "total_entries": len(found[collection]),
                    "tree_base": "archive-root/",
                },
            ),
            following,
        )

    def list_run_reports(self, limit: int | None = None, cursor: str | None = None) -> QueryPage:
        runs = list(self.queries.list_reports())
        entries, following = self._page(
            runs, limit=limit, cursor=cursor, tool="list_run_reports", scope=(), source=runs
        )
        return QueryPage(ServiceResult("runs", {"runs": entries}), following)

    def _report(
        self, run_id: str, limit: int | None, cursor: str | None, *, verification_only: bool
    ) -> QueryPage:
        report = self.queries.read_report(run_id)
        if verification_only and not isinstance(report, VerificationReport):
            message = "requested evidence is not a verification report"
            raise ConfigurationError.single(message, code="HFARG004")
        if isinstance(report, VerificationReport):
            kind, collection = "verification", "findings"
        elif isinstance(report, RecoveryReport):
            kind, collection = "recovery", "remediations"
        else:
            kind, collection = "run", "repositories"
        source = report.model_dump(mode="json")
        entries, following = self._page(
            source[collection],
            limit=limit,
            cursor=cursor,
            tool="get_verification_report" if verification_only else "get_run_report",
            scope=run_id,
            source=source,
        )
        return QueryPage(
            ServiceResult(
                "runs read",
                {
                    "projection": True,
                    "report_type": kind,
                    "report": {key: value for key, value in source.items() if key != collection},
                    "collection": collection,
                    "entries": entries,
                    "total_entries": len(source[collection]),
                },
                run_id=RunId(report.run_id),
            ),
            following,
        )

    def get_run_report(
        self, run_id: str, limit: int | None = None, cursor: str | None = None
    ) -> QueryPage:
        return self._report(run_id, limit, cursor, verification_only=False)

    def get_verification_report(
        self, run_id: str, limit: int | None = None, cursor: str | None = None
    ) -> QueryPage:
        return self._report(run_id, limit, cursor, verification_only=True)

    def estimate_verification(self) -> QueryPage:
        return QueryPage(self.queries.estimate_verification())


def _identity(repository_type: RepositoryType, repository_id: str) -> RepositoryIdentity:
    try:
        return RepositoryIdentity.of(repository_type, repository_id)
    except CodedError as error:
        raise RequestError(code=error.code) from None
