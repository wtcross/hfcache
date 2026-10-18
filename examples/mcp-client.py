#!/usr/bin/env python3
"""Read bounded MCP discovery metadata with a provisioned protected bearer.

Requires the locked hfcache server+MCP environment. This is discovery, not a
consumer copy or integrity verification. Read current once and retain its exact
publication identity while walking both manifest collections.
No token belongs in an argument, URL, environment variable or committed config.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import math
import ssl
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NoReturn, Protocol, Self

import httpx2
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from hfcache.api.auth import read_protected_token
from hfcache.client_config import ClientConfig
from hfcache.client_models import ClientRead, exact_version
from hfcache.identity import RepositoryIdentity
from hfcache.models import Reference
from hfcache.redaction import redact_text, register_secret

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator
    from types import TracebackType

MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAXIMUM_COUNT = 10000
MAXIMUM_SECONDS = 300
MAXIMUM_LENGTH_DIGITS = 10
FAILURE = "MCP discovery failed; check the protected credential, endpoint, policy and limits."


class ExampleError(Exception):
    """Only a fixed diagnostic crosses this example's public error boundary."""

    def __init__(self) -> None:
        super().__init__(FAILURE)


@dataclass(frozen=True, slots=True)
class Settings:
    endpoint: str
    token_file: Path
    ca_file: Path | None = None
    expected_archive_id: str | None = None
    page_size: int = 100
    max_pages: int = 1000
    timeout_seconds: float = 30.0
    mode: Literal["auto", "legacy"] = "auto"
    repository_type: Literal["model", "dataset"] | None = None
    repository_id: str | None = None

    def __post_init__(self) -> None:
        try:
            # Reuse the reader's independent origin/CA/path/UUID policy. No
            # archive config, ambient credential discovery or SDK inference.
            policy = ClientConfig(
                schema_version=1,
                api_url=self.endpoint,
                api_token_file=self.token_file,
                ca_file=self.ca_file,
                expected_archive_id=self.expected_archive_id,
            )
            if (
                not self.endpoint.endswith("/mcp/")
                or policy.url + "/" != self.endpoint
                or type(self.page_size) is not int
                or not 1 <= self.page_size <= MAXIMUM_COUNT
                or type(self.max_pages) is not int
                or not 1 <= self.max_pages <= MAXIMUM_COUNT
                or type(self.timeout_seconds) not in {int, float}
                or not math.isfinite(self.timeout_seconds)
                or not 0 < self.timeout_seconds <= MAXIMUM_SECONDS
                or self.mode not in {"auto", "legacy"}
                or (self.repository_type is None) != (self.repository_id is None)
            ):
                raise ExampleError  # noqa: TRY301 - one fixed example boundary
            if self.repository_id is not None:
                RepositoryIdentity.of(self.repository_type, self.repository_id)
        except Exception:  # noqa: BLE001 - fixed public diagnostic, no rejected values
            raise ExampleError from None


class ToolResult(Protocol):
    @property
    def is_error(self) -> bool: ...

    @property
    def structured_content(self) -> dict[str, object] | None: ...


class ToolClient(Protocol):
    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> None: ...

    async def call_tool(
        self, name: str, arguments: dict[str, object], *, raise_on_error: bool
    ) -> ToolResult: ...


class _BoundedStream(httpx2.AsyncByteStream):
    def __init__(self, stream: httpx2.AsyncByteStream, deadline: float) -> None:
        self.stream = stream
        self.deadline = deadline

    async def __aiter__(self) -> AsyncIterator[bytes]:
        size = 0
        async for chunk in self.stream:
            size += len(chunk)
            if size > MAX_RESPONSE_BYTES or time.monotonic() >= self.deadline:
                raise ExampleError
            yield chunk

    async def aclose(self) -> None:
        await self.stream.aclose()


def make_client(settings: Settings, token: str) -> Client[StreamableHttpTransport]:
    """Explicit HTTP only; the inspectable factory cannot inherit SDK redirects."""
    try:
        register_secret(token)
        if redact_text(settings.endpoint) != settings.endpoint:
            raise ExampleError  # noqa: TRY301 - fixed public diagnostic
        return _make_client(settings, token)
    except Exception:  # noqa: BLE001 - CA/SDK errors can contain untrusted values
        raise ExampleError from None


def _make_client(settings: Settings, token: str) -> Client[StreamableHttpTransport]:
    deadline = time.monotonic() + settings.timeout_seconds
    context = ssl.create_default_context()
    if settings.ca_file is not None:
        context.load_verify_locations(settings.ca_file)

    async def bounded(response: httpx2.Response) -> None:
        encoding = response.headers.get("content-encoding", "identity").lower()
        size = response.headers.get("content-length")
        if (
            encoding != "identity"
            or response.is_redirect
            or (size is not None and (not size.isdecimal() or len(size) > MAXIMUM_LENGTH_DIGITS))
            or (size is not None and int(size) > MAX_RESPONSE_BYTES)
            or (
                response.status_code == httpx2.codes.OK
                and response.headers.get("content-type", "").split(";", 1)[0].lower()
                != "application/json"
            )
        ):
            raise ExampleError
        if not isinstance(response.stream, httpx2.AsyncByteStream):
            raise ExampleError
        response.stream = _BoundedStream(response.stream, deadline)

    def factory(
        headers: dict[str, str] | None = None,
        timeout: httpx2.Timeout | None = None,
        auth: httpx2.Auth | None = None,
        *,
        follow_redirects: bool = False,
    ) -> httpx2.AsyncClient:
        # FastMCP 4.1.1 passes follow_redirects=True. Consume it deliberately;
        # never combine it with **kwargs or delegate a bearer across a redirect.
        del follow_redirects, timeout
        return httpx2.AsyncClient(
            headers=(headers or {}) | {"Accept-Encoding": "identity"},
            auth=auth,
            verify=context,
            trust_env=False,
            follow_redirects=False,
            timeout=httpx2.Timeout(settings.timeout_seconds),
            event_hooks={"response": [bounded]},
        )

    transport = StreamableHttpTransport(settings.endpoint, auth=token, httpx_client_factory=factory)
    return Client(
        transport,
        mode=settings.mode,
        timeout=settings.timeout_seconds,
        init_timeout=settings.timeout_seconds,
        cache=False,
        extensions=[],
    )


@contextlib.contextmanager
def _quiet_diagnostics() -> Iterator[None]:
    # This standalone example cannot safely print arbitrary server/SDK errors.
    # Restore embedding callers' logger state rather than configure root logging.
    names = ("fastmcp", "mcp", "httpx2", "httpcore2")
    loggers = [logging.getLogger(name) for name in names]
    saved = [(logger, logger.disabled) for logger in loggers]

    class SafeOnly(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return not any(
                record.name == name or record.name.startswith(name + ".") for name in names
            )

    # Logger.disabled does not apply to propagated descendant records. Filter
    # receiving handlers as well, without formatting an untrusted SDK record.
    handlers = set(logging.getLogger().handlers)
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            handlers.update(logger.handlers)
    if logging.lastResort is not None:
        handlers.add(logging.lastResort)
    guard = SafeOnly()
    try:
        for handler in handlers:
            handler.addFilter(guard)
        for logger in loggers:
            logger.disabled = True
        yield
    finally:
        for handler in handlers:
            handler.removeFilter(guard)
        for logger, disabled in saved:
            logger.disabled = disabled


async def run(
    settings: Settings,
    *,
    client_factory: Callable[[Settings, str], ToolClient] = make_client,
    on_page: Callable[[str, ClientRead], None] | None = None,
) -> dict[str, int | str]:
    """Walk repositories and optionally one exact publication; retain counts only."""
    try:
        with _quiet_diagnostics():
            async with asyncio.timeout(settings.timeout_seconds):
                token = read_protected_token(settings.token_file)
                if redact_text(settings.endpoint) != settings.endpoint:
                    raise ExampleError  # noqa: TRY301 - fixed public diagnostic
                async with client_factory(settings, token) as client:
                    return await _walk(client, settings, on_page)
    except Exception:  # noqa: BLE001 - never disclose arbitrary SDK/server errors
        raise ExampleError from None


async def _walk(  # noqa: PLR0915 - one bounded demonstration, not a client framework
    client: ToolClient, settings: Settings, on_page: Callable[[str, ClientRead], None] | None
) -> dict[str, int | str]:
    identity: tuple[str, str] | None = None
    pages = 0

    async def read(name: str, arguments: dict[str, object]) -> ClientRead:
        nonlocal identity, pages
        pages += 1
        if pages > settings.max_pages:
            raise ExampleError
        result = await client.call_tool(name, arguments, raise_on_error=False)
        if result.is_error or result.structured_content is None:
            raise ExampleError
        frame = ClientRead.model_validate(result.structured_content)
        current = (frame.archive_id, frame.config_fingerprint)
        if (
            frame.archive_id is None
            or frame.config_fingerprint is None
            or frame.envelope.exit_code != 0
            or frame.envelope.command
            != {
                "list_repositories": "list",
                "get_current_reference": "reference read",
                "get_revision_manifest": "manifest read",
            }[name]
            or (identity is not None and current != identity)
            or (
                settings.expected_archive_id is not None
                and frame.archive_id != settings.expected_archive_id
            )
        ):
            raise ExampleError
        identity = (frame.archive_id, frame.config_fingerprint)
        if on_page is not None:
            on_page(name, frame)
        return frame

    async def collection(
        name: str, arguments: dict[str, object], field: str
    ) -> tuple[int, dict[str, object]]:
        count = 0
        seen: set[str] = set()
        cursor: str | None = None
        header: dict[str, object] | None = None
        previous_row: tuple[str, ...] | None = None
        while True:
            frame = await read(name, arguments | {"limit": settings.page_size, "cursor": cursor})
            data = frame.envelope.data
            entries = data.get(field)
            if not isinstance(entries, list) or len(entries) > settings.page_size:
                raise ExampleError
            for entry in entries:
                fields = (
                    ("repository_type", "repository_id")
                    if name == "list_repositories"
                    else (
                        ("path",)
                        if arguments.get("collection") == "files"
                        else ("source_file", "source_field", "detected_id")
                    )
                )
                if not isinstance(entry, dict) or any(
                    not isinstance(entry.get(key), str) for key in fields
                ):
                    raise ExampleError
                row = tuple(entry[key] for key in fields)
                duplicate_allowed = arguments.get("collection") == "dependencies"
                if previous_row is not None and (
                    row < previous_row or (row == previous_row and not duplicate_allowed)
                ):
                    raise ExampleError
                previous_row = row
            if name == "get_revision_manifest":
                stable = {key: value for key, value in data.items() if key != "entries"}
                if header is not None and stable != header:
                    raise ExampleError
                header = stable
            count += len(entries)
            cursor = frame.next_cursor
            if cursor is None:
                return count, header or {}
            if cursor in seen or redact_text(cursor) != cursor or not entries:
                raise ExampleError
            seen.add(cursor)

    repositories, _ = await collection("list_repositories", {}, "repositories")
    summary: dict[str, int | str] = {"repository_count": repositories}
    if settings.repository_id is not None:
        scope: dict[str, object] = {
            "repository_type": settings.repository_type,
            "repository_id": settings.repository_id,
        }
        current = await read("get_current_reference", scope)
        if (
            current.next_cursor is not None
            or current.envelope.data.get("locator_base") != "published/"
        ):
            raise ExampleError
        reference = current.envelope.data.get("reference")
        if not isinstance(reference, dict):
            raise ExampleError
        exact_version(reference.get("schema_version"))
        validated = Reference.model_validate(reference)
        if (
            validated.repository_type != settings.repository_type
            or validated.repository_id != settings.repository_id
        ):
            raise ExampleError
        exact = scope | {
            "commit_sha": validated.commit_sha,
            "publication_id": validated.publication_id,
        }
        files, file_header = await collection(
            "get_revision_manifest", exact | {"collection": "files"}, "entries"
        )
        dependencies, dependency_header = await collection(
            "get_revision_manifest", exact | {"collection": "dependencies"}, "entries"
        )
        manifest = file_header.get("manifest")
        if isinstance(manifest, dict):
            exact_version(manifest.get("schema_version"))
        if (
            not isinstance(manifest, dict)
            or manifest != dependency_header.get("manifest")
            or manifest.get("commit_sha") != exact["commit_sha"]
            or manifest.get("publication_id") != exact["publication_id"]
            or manifest.get("repository_type") != settings.repository_type
            or manifest.get("repository_id") != settings.repository_id
            or manifest.get("publication_generation") != validated.publication_generation
            or type(manifest.get("publication_generation")) is not int
            or manifest.get("file_count") != files
            or type(manifest.get("file_count")) is not int
            or type(manifest.get("total_bytes")) is not int
            or manifest["total_bytes"] < 0
            or manifest.get("tree") != "published/" + validated.tree
            or file_header.get("projection") is not True
            or dependency_header.get("projection") is not True
            or file_header.get("collection") != "files"
            or dependency_header.get("collection") != "dependencies"
            or file_header.get("tree_base") != "archive-root/"
            or dependency_header.get("tree_base") != "archive-root/"
            or file_header.get("total_entries") != files
            or dependency_header.get("total_entries") != dependencies
            or type(file_header.get("total_entries")) is not int
            or type(dependency_header.get("total_entries")) is not int
        ):
            raise ExampleError
        summary |= {"manifest_files": files, "manifest_dependencies": dependencies}
    summary["metadata_pages"] = pages
    return summary


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ExampleError


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description=__doc__)
    parser.add_argument(
        "--url", required=True, help="Canonical /mcp/ HTTPS endpoint, including any public prefix."
    )
    parser.add_argument(
        "--token-file",
        type=Path,
        required=True,
        help="Absolute protected MCP-reader token pathname; never a literal token.",
    )
    parser.add_argument(
        "--ca-file", type=Path, help="CA certificate file; system trust is used when omitted."
    )
    parser.add_argument("--expected-archive-id", help="Expected canonical archive UUID.")
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Entries per page (default: 100; server maximum applies).",
    )
    parser.add_argument(
        "--max-pages", type=int, default=1000, help="Total metadata-call budget (default: 1000)."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Overall deadline in seconds (default: 30; at most 300).",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "legacy"),
        default="auto",
        help="Negotiation mode: modern auto or explicit legacy initialize.",
    )
    parser.add_argument(
        "--type",
        choices=("model", "dataset"),
        dest="repository_type",
        help="Repository type; requires --repository.",
    )
    parser.add_argument(
        "--repository",
        dest="repository_id",
        help="Repository ID for exact publication discovery; requires --type.",
    )
    try:
        args = vars(parser.parse_args(argv))
        args["endpoint"] = args.pop("url")
        args["timeout_seconds"] = args.pop("timeout")
        summary = asyncio.run(run(Settings(**args)))
    except Exception, KeyboardInterrupt:  # noqa: BLE001 - command line fixed diagnostic
        print(FAILURE, file=sys.stderr)
        return 1
    print(json.dumps({"kind": "discovery_summary", **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
