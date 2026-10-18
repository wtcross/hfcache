"""Authenticated bounded query and command adapters; importing creates no listener.

Decisions 113-117 and docs/api.md and docs/server.md keep archive authority behind typed services,
durable admission, and the shared guarded execution lane.
"""

import asyncio
import base64
import hashlib
import ipaddress
import json
import logging
import math
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.security import HTTPBearer
from pydantic import ValidationError
from starlette.exceptions import HTTPException

from hfcache.api.auth import Capability, CredentialRegistry, load_credentials, require_capability
from hfcache.api.commands import install_command_routes
from hfcache.api.lifecycle import MetadataPool, instance_lock
from hfcache.api.maintenance import install_maintenance_routes
from hfcache.api.models import ApiProblem, OperationView, PageQuery, ReadResponse
from hfcache.api.operations import OperationLimits, OperationReceipt, OperationStore
from hfcache.api.runner import OperationRunner
from hfcache.errors import (
    AuthorizationError,
    CodedError,
    ConfigurationError,
    HfcacheError,
    OperationError,
    RequestError,
    SafetyError,
)
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, RunId
from hfcache.logging import configure_daemon
from hfcache.metadata import QueryBounds
from hfcache.redaction import sanitize
from hfcache.reporting import Envelope
from hfcache.server_config import InstalledPolicy, PolicySnapshot, ServerConfig
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.services.queries import LocalQueries, PublicationQuery, RepositoryQuery, query_version
from hfcache.verification_protocol import VerificationClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Coroutine, Iterator

    from starlette.types import ASGIApp, Message, Receive, Scope, Send

    from hfcache.api.auth import Principal
    from hfcache.config import ApplicationConfig
    from hfcache.services.queries import MetadataQueries
    from hfcache.verification_protocol import VerificationDelegate

PREFIX = "/api/v1"
_CHUNK = 8192
_MAX_QUERY_BYTES = 8192
_MAX_HEADER_BYTES = 32768
_MAX_LIMIT_DIGITS = 5
_MAX_SELECTORS = 100
_MAX_SELECTOR_BYTES = 256
_MAX_OFFSET_DIGITS = 10
_MAX_JSON_DEPTH = 32


def _unique_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in items:
        if key in result:
            raise RequestError
        result[key] = value
    return result


def _invalid_constant(_: str) -> None:
    raise RequestError


def _check_json_strings(value: object, depth: int = 0) -> None:
    if depth > _MAX_JSON_DEPTH:
        raise RequestError
    if isinstance(value, str):
        value.encode("utf-8")
    elif isinstance(value, float) and not math.isfinite(value):
        raise RequestError
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_json_strings(key, depth + 1)
            _check_json_strings(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _check_json_strings(item, depth + 1)


async def _json_body(
    receive: Receive, maximum: int, headers: list[tuple[bytes, bytes]]
) -> bytes | None:
    types = [value for key, value in headers if key.lower() == b"content-type"]
    if len(types) != 1 or any(key.lower() == b"content-encoding" for key, _ in headers):
        raise RequestError
    parts = [part.strip().lower() for part in types[0].decode("latin1").split(";")]
    if parts[0] != "application/json" or (
        len(parts) > 1 and parts[1:] not in (["charset=utf-8"], ['charset="utf-8"'])
    ):
        raise RequestError
    body = bytearray()
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return None
        part = message.get("body", b"")
        if len(body) + len(part) > maximum:
            raise RequestError(status_code=413)
        body.extend(part)
        if not message.get("more_body", False):
            return bytes(body)


def _parse_object(body: bytes) -> dict[str, Any]:
    try:
        value = json.loads(
            body.decode("utf-8"), object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant
        )
        _check_json_strings(value)
    except ValueError, UnicodeError, RecursionError:
        raise RequestError from None
    if not isinstance(value, dict):
        raise RequestError
    return value


async def _empty_body(receive: Receive, maximum: int) -> bool:
    size = 0
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return False
        size += len(message.get("body", b""))
        if size > maximum:
            raise RequestError(status_code=413)
        if not message.get("more_body", False):
            break
    if size:
        raise RequestError
    return True


async def _finish_owned(work: Coroutine[Any, Any, None]) -> None:
    """Delay lifespan cancellation until owned domain and metadata work has joined."""
    joining = asyncio.create_task(work)
    cancelled = False
    while not joining.done():
        try:
            await asyncio.shield(joining)
        except asyncio.CancelledError:
            cancelled = True
    joining.result()
    if cancelled:
        raise asyncio.CancelledError


def _problem(context: ExecutionContext, error: HfcacheError) -> JSONResponse:
    problem = error.problems[0]
    status = getattr(error, "status_code", None)
    if status is None:
        status = {
            "HFAPI005": 503,
            "HFAPI007": 404,
            "HFAPI008": 500,
            "HFAPI009": 503,
            "HFAPI011": 503,
            "HFARG004": 404,
            "HFARG001": 422,
            "HFARG002": 422,
        }.get(problem.code)
    if status is None:
        status = 409 if problem.code.startswith("HFVER") else 503
    # An artifact's message/context may contain attacker-controlled strings;
    # transport errors expose stable shape only, not domain input or tracebacks.
    messages = {
        401: "Not authenticated",
        403: "Forbidden",
        404: "Not found",
        409: "Metadata is stale or inconsistent",
        413: "Request or response exceeds its limit",
        422: "Invalid request",
        500: "Internal server error",
        503: "Service unavailable",
    }
    payload = ApiProblem(
        request_id=context.request_id or "",
        code=problem.code,
        message={
            "HFAPI013": "Operation history is missing or expired; execution is unknown",
            "HFAPI014": "Operation history is unavailable or full",
            "HFAPI015": "Operation state is incomplete or uncertain",
        }.get(problem.code, messages.get(status, "Invalid request")),
        exit_code=int(error.exit_code),
    )
    return JSONResponse(
        payload.model_dump(), status_code=status, headers=dict(getattr(error, "headers", {}))
    )


def _native_unix(scope: Scope) -> bool:
    """Corroborate the supported Uvicorn Unix scope without caller headers."""
    local = scope.get("server")
    if scope.get("client") is not None or not isinstance(local, tuple):
        return False
    match local:
        case (str() as pathname, None):
            return (
                pathname.startswith("/")
                and pathname != "/"
                and all(character.isprintable() for character in pathname)
            )
        case _:
            return False


class Boundary:
    """Authenticate before routing/validation and contain every HTTP error surface."""

    def __init__(self, app: ASGIApp, *, owner: FastAPI, server: ServerConfig) -> None:
        self.app, self.owner, self.server = app, owner, server

    def project_path(self, scope: Scope) -> tuple[str, str]:
        """Resolve public/native spellings even when a prefix overlaps an interface."""
        path, public_root = scope["path"], self.server.listener.root_path

        def interface(value: str) -> bool:
            return (
                value == PREFIX
                or value.startswith(PREFIX + "/")
                or (value == "/mcp" or value.startswith("/mcp/"))
            )

        prefixed = bool(public_root and path.startswith(public_root + "/"))
        public_path = path[len(public_root) :] if prefixed else path
        if prefixed and interface(public_path):
            return public_path, public_root
        if _native_unix(scope) and interface(path):
            return path, ""
        return (public_path, public_root) if prefixed else (path, "")

    def is_mcp(self, scope: Scope) -> bool:
        path, _ = self.project_path(scope)
        return self.server.mcp_enabled and (path == "/mcp" or path.startswith("/mcp/"))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:  # noqa: PLR0912, PLR0915 - one authenticated request/lease lifetime
        if scope["type"] != "http":
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
                return
            await self.app(scope, receive, send)
            return
        context = ExecutionContext.new_request()
        state = scope.setdefault("state", {})
        state["execution_context"], state["metadata_leases"] = context, []
        started = False
        mcp_lease = None

        async def safe_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                headers = list(message.get("headers", []))
                headers.extend(
                    (
                        (b"x-request-id", (context.request_id or "").encode()),
                        (b"cache-control", b"no-store"),
                        (b"x-content-type-options", b"nosniff"),
                        (b"content-security-policy", b"frame-ancestors 'none'"),
                    )
                )
                message = dict(message) | {"headers": headers}
            await send(message)

        with context.activate():
            try:
                principal = self.authenticate(scope)
                mcp = self.is_mcp(scope)
                require_capability(principal, Capability.MCP_READ if mcp else Capability.READ)
                state["principal"] = principal
                if mcp:
                    transport = self.owner.state.mcp_transport
                    transport.acquire()
                    mcp_lease = state["mcp_transport_lease"] = transport
                body = await self.request_body(scope, receive, principal)
                if body is None:
                    return
                if mcp and self.project_path(scope)[0] == "/mcp":
                    # A relative, trusted location preserves TLS and never reflects
                    # a caller Host, query, forwarding header or bearer value.
                    response = RedirectResponse(scope["root_path"] + "/mcp/", status_code=307)
                    await response(scope, receive, safe_send)
                    return

                delivered = False

                async def replay() -> Message:
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": body, "more_body": False}
                    return await receive()

                await self.app(scope, replay, safe_send)
            except HfcacheError as exc:
                if not started:
                    await _problem(context, exc)(scope, receive, safe_send)
            except CodedError as exc:
                if not started:
                    await _problem(context, RequestError(code=exc.code))(scope, receive, safe_send)
            except Exception:  # noqa: BLE001 - outer transport boundary never returns raw tracebacks
                if not started:
                    error = SafetyError.single("unexpected API failure", code="HFAPI008")
                    await _problem(context, error)(scope, receive, safe_send)
            finally:
                for lease in state.pop("metadata_leases", ()):
                    lease.finish_request()
                if mcp_lease is not None:
                    state.pop("mcp_transport_lease", None)
                    mcp_lease.release()

    async def request_body(
        self, scope: Scope, receive: Receive, principal: Principal
    ) -> bytes | None:
        path, _ = self.project_path(scope)
        command = scope["method"] == "POST" and path in getattr(
            self.owner.state, "command_routes", ()
        )
        if command and path in getattr(
            self.owner.state, "writer_routes", {PREFIX + "/syncs", PREFIX + "/verifications"}
        ):
            require_capability(principal, Capability.WRITE)
        if (
            command
            and path == PREFIX + "/archive/initializations"
            and not self.server.maintenance_enabled
        ):
            raise AuthorizationError
        self.validate_transport(scope)
        if self.is_mcp(scope):
            if scope.get("query_string"):
                raise RequestError
            if scope["method"] == "POST":
                body = await _json_body(
                    receive, self.server.limits.max_request_bytes, scope["headers"]
                )
                if body is not None:
                    _parse_object(body)
                return body
            return b"" if await _empty_body(receive, self.server.limits.max_request_bytes) else None
        if not command:
            return b"" if await _empty_body(receive, self.server.limits.max_request_bytes) else None
        body = await _json_body(receive, self.server.limits.max_request_bytes, scope["headers"])
        if body is None:
            return None
        submitted = _parse_object(body)
        scope["state"]["json_body"] = submitted
        if "candidate" in submitted or (
            path == PREFIX + "/diagnostics" and submitted.get("read_only") is not True
        ):
            require_capability(principal, Capability.WRITE)
        return body

    def authenticate(self, scope: Scope) -> Any:  # noqa: ANN401 - Starlette application state
        registry = getattr(self.owner.state, "credentials", None)
        if registry is None:
            message = "service is not started"
            raise SafetyError.single(message, code="HFAPI009")
        values = [
            value.decode("latin1")
            for key, value in scope["headers"]
            if key.lower() == b"authorization"
        ]
        return registry.authenticate(
            values[0] if len(values) == 1 else None,
            interface="mcp" if self.is_mcp(scope) else "rest",
        )

    def validate_root_path(self, scope: Scope) -> None:
        public_root = self.server.listener.root_path
        _, effective_root = self.project_path(scope)
        if public_root and not effective_root and not _native_unix(scope):
            raise RequestError(code="HFAPI007", status_code=404)
        # Decision 123: corroborated native clients need no public proxy prefix.
        # Never derive this trust or emitted links from forwarding headers.
        scope["root_path"] = effective_root

    def validate_transport(self, scope: Scope) -> None:  # noqa: PLR0912 - coupled pre-routing security checks
        headers = scope["headers"]
        if sum(len(key) + len(value) for key, value in headers) > _MAX_HEADER_BYTES:
            raise RequestError(status_code=413)
        values = {key.lower(): value.decode("latin1") for key, value in headers}
        hosts = [value for key, value in headers if key.lower() == b"host"]
        if len(hosts) != 1:
            raise RequestError(code="HFAPI010", status_code=400)
        host = hosts[0].decode("latin1")
        if any(character in host for character in "/\\@?#") or any(
            not character.isprintable() or character.isspace() for character in host
        ):
            raise RequestError(code="HFAPI010", status_code=400)
        try:
            parsed = urlsplit("//" + host)
            port = parsed.port
        except ValueError:
            raise RequestError(code="HFAPI010", status_code=400) from None
        if (
            not parsed.hostname
            or host.endswith(":")
            or (host.count(":") > 1 and not host.startswith("["))
            or (port is not None and port < 1)
        ):
            raise RequestError(code="HFAPI010", status_code=400)
        name = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
        if name.lower() not in {item.lower() for item in self.server.listener.allowed_hosts}:
            raise RequestError(code="HFAPI010", status_code=400)
        origins = [value for key, value in headers if key.lower() == b"origin"]
        if len(origins) > 1:
            raise RequestError(code="HFAPI010", status_code=403)
        origin = values.get(b"origin")
        if origin is not None and origin not in self.server.listener.allowed_origins:
            raise RequestError(code="HFAPI010", status_code=403)
        query = scope.get("query_string", b"")
        if len(query) > _MAX_QUERY_BYTES:
            raise RequestError(status_code=413)
        self.validate_root_path(scope)
        if self.server.listener.proxy_tls and not _native_unix(scope):
            client = scope.get("client")
            try:
                peer = ipaddress.ip_address(client[0]) if client else None
            except ValueError:
                raise RequestError(code="HFAPI010", status_code=403) from None
            trusted = peer is not None and any(
                peer in ipaddress.ip_network(network)
                for network in self.server.listener.trusted_proxies
            )
            if not trusted or values.get(b"x-forwarded-proto") != "https":
                raise RequestError(code="HFAPI010", status_code=403)
        length = values.get(b"content-length")
        if sum(key.lower() == b"content-length" for key, _ in headers) > 1:
            raise RequestError
        if length is not None and (not length.isascii() or not length.isdigit()):
            raise RequestError
        if length is not None and len(length) > _MAX_OFFSET_DIGITS:
            raise RequestError(status_code=413)
        if length is not None and int(length) > self.server.limits.max_request_bytes:
            raise RequestError(status_code=413)


def _page_query(request: Request, server: ServerConfig, *, repositories: bool) -> PageQuery:
    allowed = {"limit", "cursor"} | ({"selector", "type"} if repositories else set())
    if set(request.query_params) - allowed:
        raise RequestError
    for key in allowed - {"selector"}:
        if len(request.query_params.getlist(key)) > 1:
            raise RequestError
    limit = request.query_params.get("limit", str(min(100, server.limits.max_page_size)))
    if not limit.isascii() or not limit.isdecimal() or len(limit) > _MAX_LIMIT_DIGITS:
        raise RequestError
    selectors = tuple(request.query_params.getlist("selector"))
    if len(selectors) > _MAX_SELECTORS or any(
        len(value) > _MAX_SELECTOR_BYTES for value in selectors
    ):
        raise RequestError
    try:
        page = PageQuery.model_validate(
            {
                "limit": int(limit),
                "cursor": request.query_params.get("cursor"),
                "selectors": selectors,
                "repository_type": request.query_params.get("type"),
            }
        )
    except ValidationError:
        raise RequestError from None
    if page.limit > server.limits.max_page_size:
        raise RequestError
    return page


def _no_query(request: Request) -> None:
    if request.query_params:
        raise RequestError


def _paginate(items: list[Any], page: PageQuery, *, key: str) -> tuple[list[Any], str | None]:
    digest = hashlib.sha256(key.encode())
    for chunk in _encoded(cast("dict[str, Any]", sanitize({"items": items}))):
        digest.update(chunk)
    scope = digest.hexdigest()[:24]
    offset = 0
    if page.cursor:
        try:
            decoded = base64.b64decode(page.cursor, altchars=b"-_", validate=True).decode("ascii")
            found, raw_offset = decoded.split(":")
            if not raw_offset.isdecimal() or len(raw_offset) > _MAX_OFFSET_DIGITS:
                raise RequestError
            offset = int(raw_offset)
        except ValueError, UnicodeError:
            raise RequestError from None
        if found != scope:
            raise RequestError(code="HFAPI007", status_code=409)
        if offset > len(items):
            raise RequestError(code="HFAPI007", status_code=409)
    end = offset + page.limit
    cursor = (
        base64.urlsafe_b64encode(f"{scope}:{end}".encode()).decode() if end < len(items) else None
    )
    return items[offset:end], cursor


def _encoded(payload: dict[str, Any]) -> Iterator[bytes]:
    buffer = bytearray()
    for piece in json.JSONEncoder(
        sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")
    ).iterencode(payload):
        for offset in range(0, len(piece), _CHUNK):
            raw = piece[offset : offset + _CHUNK].encode("ascii")
            capacity = _CHUNK - len(buffer)
            buffer.extend(raw[:capacity])
            if len(buffer) == _CHUNK:
                yield bytes(buffer)
                buffer.clear()
            buffer.extend(raw[capacity:])
    if buffer:
        yield bytes(buffer)


def create_app(  # noqa: PLR0913, PLR0915 - one injectable application factory
    server: ServerConfig,
    *,
    credentials: CredentialRegistry | None = None,
    policy: InstalledPolicy | None = None,
    query_factory: Callable[[ApplicationConfig], MetadataQueries] | None = None,
    instance_lock_path: Path | None = None,
    operation_store: OperationStore | None = None,
    verification_executor: VerificationDelegate | None = None,
    hub_token_file: Path | None = None,
) -> FastAPI:
    """Create routes only; lifespan owns all filesystem/startup effects."""

    def factory(config: ApplicationConfig) -> MetadataQueries:
        if query_factory is not None:
            return query_factory(config)
        return LocalQueries(
            config,
            bounds=QueryBounds(
                maximum_entries=server.limits.max_scan_entries,
                maximum_artifact_bytes=server.limits.max_artifact_bytes,
                maximum_total_bytes=server.limits.max_artifact_bytes,
            ),
        )

    @asynccontextmanager
    async def rest_lifespan(application: FastAPI) -> AsyncIterator[None]:
        with instance_lock(instance_lock_path or Path("/run/hfcache/api.lock")):
            configure_daemon(level=getattr(logging, server.log_level.upper()))
            application.state.credentials = credentials or load_credentials(server)
            application.state.policy = policy or InstalledPolicy.open(server)
            application.state.hub_token_file = hub_token_file
            state_root = operation_store.root if operation_store else server.state_directory
            archive_root = application.state.policy.root
            if state_root.is_relative_to(archive_root) or archive_root.is_relative_to(state_root):
                message = "operation state and archive storage must not overlap"
                raise ConfigurationError.single(message, code="HFCFG005")
            limits = server.limits
            with operation_store or OperationStore(
                server.state_directory,
                limits=OperationLimits(
                    max_records=limits.retained_terminal_operations,
                    max_receipt_bytes=limits.operation_max_receipt_bytes,
                    max_result_bytes=limits.operation_max_result_bytes,
                    max_events=limits.operation_max_events,
                    max_event_bytes=limits.operation_max_event_bytes,
                    max_store_bytes=limits.operation_max_store_bytes,
                    retention_days=limits.operation_retention_days,
                ),
            ) as store:
                application.state.operations = store
                application.state.pool = MetadataPool(
                    workers=limits.metadata_workers, pending=limits.metadata_queue
                )
                settings = server.verification

                def worker_progress(receipt: OperationReceipt) -> None:
                    if receipt.state == "running":
                        application.state.runner.mark_running(
                            receipt.operation_id, receipt.domain_run_id
                        )

                application.state.verifier = verification_executor or VerificationClient(
                    settings.unix_socket,
                    expected_uid=settings.expected_peer_uid,
                    timeout_seconds=settings.timeout_seconds,
                    poll_seconds=settings.poll_seconds,
                    max_frame_bytes=settings.max_frame_bytes,
                    progress=worker_progress,
                    expected_archive_id=application.state.policy.archive_id,
                )
                application.state.runner = OperationRunner(
                    store,
                    application.state.policy,
                    max_pending=limits.max_queued_operations,
                    check_verification_available=application.state.verifier.check_available,
                )
                application.state.instance_id = ExecutionContext.create().run_id
                application.state.version = query_version()
                try:
                    try:
                        await asyncio.to_thread(
                            application.state.runner.start,
                            reconcile=application.state.verifier.reconcile,
                        )
                    except OperationError:
                        # Unsafe history disables admission, while healthy exact
                        # observations and metadata remain available for diagnosis.
                        application.state.runner.stop_admission()
                    yield
                finally:
                    application.state.runner.stop_admission()

                    async def drain() -> None:
                        await asyncio.to_thread(application.state.runner.drain)
                        await application.state.pool.close()
                        application.state.credentials = None

                    await _finish_owned(drain())

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        try:
            async with rest_lifespan(application):
                if server.mcp_enabled:
                    from hfcache.mcp import mcp_diagnostics  # noqa: PLC0415 - optional startup only

                    with mcp_diagnostics():
                        async with application.state.mcp_app.lifespan(application.state.mcp_app):
                            yield
                else:
                    yield
        finally:
            application.state.credentials = None

    app = FastAPI(
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        root_path=server.listener.root_path,
        redirect_slashes=False,
        servers=[{"url": server.listener.root_path or "/"}],
        dependencies=[Depends(HTTPBearer(auto_error=False, scheme_name="hfcacheBearer"))],
        responses={
            status: {"model": ApiProblem} for status in (401, 403, 404, 409, 413, 422, 500, 503)
        },
    )
    app.add_middleware(Boundary, owner=app, server=server)
    if server.mcp_enabled:
        # Optional import is deliberately below the enabled branch: base/server
        # installations and disabled credentials have no MCP dependency.
        try:
            from fastmcp.server.dependencies import (  # noqa: PLC0415 - optional extra
                get_http_request,
            )

            from hfcache.api.mcp_reads import (  # noqa: PLC0415 - optional adapter
                MetadataReadAdapter,
            )
            from hfcache.mcp import (  # noqa: PLC0415 - optional extra
                BoundedMCPTransport,
                create_mcp_app,
            )
            from hfcache.services.mcp_queries import (  # noqa: PLC0415 - optional read projection
                MetadataRead,
                MetadataReadQueries,
                QueryPage,
            )
        except ImportError:
            message = "MCP is enabled but its optional runtime is unavailable"
            raise ConfigurationError.single(message, code="HFCFG005") from None

        async def execute_mcp(
            read: Callable[[MetadataReadQueries], QueryPage],
        ) -> MetadataRead:
            pool = getattr(app.state, "pool", None)
            if pool is None or pool.closed:
                message = "metadata service is not started or is draining"
                raise SafetyError.single(message, code="HFAPI009")
            request = get_http_request()
            context = request.state.execution_context

            def work() -> MetadataRead:
                snapshot = app.state.policy.snapshot()
                page = read(
                    MetadataReadQueries(
                        factory(snapshot.config),
                        fingerprint=snapshot.fingerprint,
                        max_page_size=server.limits.max_page_size,
                    )
                )
                return MetadataRead(
                    request_id=context.request_id,
                    archive_id=snapshot.config.storage.archive_id,
                    config_fingerprint=snapshot.fingerprint,
                    envelope=page.result.envelope(context),
                    next_cursor=page.next_cursor,
                )

            lease = pool.submit(work)
            request.state.metadata_leases.append(lease)
            return await lease.future

        app.state.mcp_app = create_mcp_app(
            lambda: getattr(app.state, "credentials", None),
            MetadataReadAdapter(execute_mcp),
            max_page_size=server.limits.max_page_size,
        )
        app.state.mcp_server = app.state.mcp_app.state.fastmcp_server
        app.state.mcp_transport = BoundedMCPTransport(
            app.state.mcp_app,
            capacity=server.limits.metadata_workers + server.limits.metadata_queue,
            maximum=server.limits.max_response_bytes,
        )
        app.mount("/mcp", app.state.mcp_transport, name="mcp")

    def bounded_static(response: Response) -> Response:
        if len(response.body) > server.limits.max_response_bytes:
            raise RequestError(status_code=413)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation(request: Request, _: RequestValidationError) -> Response:
        return _problem(request.state.execution_context, RequestError())

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException) -> Response:
        code = "HFAPI007" if error.status_code in {404, 405} else "HFAPI006"
        return _problem(
            request.state.execution_context, RequestError(code=code, status_code=error.status_code)
        )

    def render(  # noqa: PLR0913 - wire identity for metadata or an exact stored result
        request: Request,
        result: ServiceResult | Envelope,
        *,
        snapshot: PolicySnapshot | None = None,
        cursor: str | None = None,
        large: bool = False,
        receipt: OperationReceipt | None = None,
    ) -> Response:
        context = request.state.execution_context
        payload = ReadResponse(
            request_id=context.request_id or "",
            archive_id=receipt.archive_id
            if receipt
            else (snapshot.config.storage.archive_id if snapshot else app.state.policy.archive_id),
            config_fingerprint=receipt.config_fingerprint
            if receipt
            else (snapshot.fingerprint if snapshot else None),
            envelope=result.to_payload()
            if isinstance(result, Envelope)
            else result.envelope(context).to_payload(),
            next_cursor=cursor,
        ).model_dump()
        payload = cast("dict[str, Any]", sanitize(payload))
        maximum = (
            server.limits.max_artifact_bytes * 8 if large else server.limits.max_response_bytes
        )
        if sum(len(chunk) for chunk in _encoded(payload)) > maximum:
            raise RequestError(status_code=413)
        if large:
            return StreamingResponse(_encoded(payload), media_type="application/json")
        return JSONResponse(payload)

    async def execute(
        request: Request,
        operation: Callable[[MetadataQueries, PolicySnapshot], tuple[ServiceResult, str | None]],
        *,
        large: bool = False,
    ) -> Response:
        def work() -> Response:
            snapshot = app.state.policy.snapshot()
            result, cursor = operation(factory(snapshot.config), snapshot)
            return render(request, result, snapshot=snapshot, cursor=cursor, large=large)

        lease = app.state.pool.submit(work)
        request.state.metadata_leases.append(lease)
        return await lease.future

    @app.get(PREFIX + "/version", response_model=ReadResponse)
    async def version(request: Request) -> Response:
        _no_query(request)
        return render(request, app.state.version)

    @app.get(PREFIX + "/capabilities", response_model=ReadResponse)
    async def capabilities(request: Request) -> Response:
        _no_query(request)
        return render(
            request,
            ServiceResult(
                "capabilities",
                {
                    "api_version": 1,
                    "credential_class": request.state.principal.credential_class.value,
                    "capabilities": sorted(
                        item.value for item in request.state.principal.capabilities
                    ),
                    "instance_id": app.state.instance_id,
                    "reads": True,
                    "operations": True,
                    "operation_history": True,
                    "mcp": server.mcp_enabled,
                    "maintenance_enabled": server.maintenance_enabled,
                    "max_page_size": server.limits.max_page_size,
                },
            ),
        )

    @app.get(PREFIX + "/health", response_model=ReadResponse)
    async def health(request: Request) -> Response:
        _no_query(request)
        try:
            return await execute(
                request,
                lambda queries, _: (
                    ServiceResult(
                        "health",
                        {
                            "ready": True,
                            "policy_valid": True,
                            "archive": queries.inspect_archive().as_payload(),
                        },
                    ),
                    None,
                ),
            )
        except HfcacheError as exc:
            if any(problem.code == "HFAPI005" for problem in exc.problems):
                raise
            return render(
                request,
                ServiceResult(
                    "health",
                    {
                        "ready": True,
                        "policy_valid": None
                        if app.state.pool.inflight >= app.state.pool.capacity
                        else False,
                        "archive": None,
                    },
                ),
            )

    @app.get(PREFIX + "/archive/inspection", response_model=ReadResponse)
    async def inspection(request: Request) -> Response:
        _no_query(request)

        def read(queries: MetadataQueries, _: PolicySnapshot) -> tuple[ServiceResult, None]:
            inspected = queries.inspect_archive()
            return ServiceResult(
                "archive init",
                inspected.as_payload(),
                errors=inspected.problems,
                exit_code=20 if inspected.problems else 0,
            ), None

        return await execute(request, read)

    async def inventory(request: Request, *, mode: str) -> Response:
        page = _page_query(request, server, repositories=True)

        def read(
            queries: MetadataQueries, snapshot: PolicySnapshot
        ) -> tuple[ServiceResult, str | None]:
            query = RepositoryQuery(
                page.selectors, page.repository_type, revisions=mode == "revisions"
            )
            result = (
                queries.archive_status(query)
                if mode == "status"
                else queries.list_repositories(query)
            )
            data = result.data
            field = "repositories"
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
                field = "revisions"
            data[field], cursor = _paginate(
                data[field],
                page,
                key=f"{mode}:{snapshot.fingerprint}:{page.selectors}:{page.repository_type}",
            )
            return ServiceResult(
                result.command, data, result.warnings, result.errors, result.exit_code
            ), cursor

        return await execute(request, read)

    @app.get(PREFIX + "/status", response_model=ReadResponse)
    async def status(request: Request) -> Response:
        return await inventory(request, mode="status")

    @app.get(PREFIX + "/repositories", response_model=ReadResponse)
    async def repositories(request: Request) -> Response:
        return await inventory(request, mode="repositories")

    @app.get(PREFIX + "/repositories/revisions", response_model=ReadResponse)
    async def revisions(request: Request) -> Response:
        return await inventory(request, mode="revisions")

    @app.get(PREFIX + "/verification/estimate", response_model=ReadResponse)
    async def estimate(request: Request) -> Response:
        _no_query(request)
        return await execute(request, lambda queries, _: (queries.estimate_verification(), None))

    @app.get(PREFIX + "/runs", response_model=ReadResponse)
    async def runs(request: Request) -> Response:
        page = _page_query(request, server, repositories=False)

        def read(
            queries: MetadataQueries, snapshot: PolicySnapshot
        ) -> tuple[ServiceResult, str | None]:
            items, cursor = _paginate(
                list(queries.list_reports()), page, key=f"runs:{snapshot.fingerprint}"
            )
            return ServiceResult("runs", {"runs": items}), cursor

        return await execute(request, read)

    @app.get(PREFIX + "/runs/{run_id}", response_model=ReadResponse)
    async def report(request: Request, run_id: str) -> Response:
        _no_query(request)

        def read(queries: MetadataQueries, _: PolicySnapshot) -> tuple[ServiceResult, None]:
            found = queries.read_report(run_id)
            return ServiceResult(
                "runs read", {"report": found.model_dump(mode="json")}, run_id=RunId(found.run_id)
            ), None

        return await execute(request, read, large=True)

    @app.get(
        PREFIX + "/repositories/{repository_type}/{namespace}/{name}/references/{revision}",
        response_model=ReadResponse,
    )
    async def reference(
        request: Request, repository_type: str, namespace: str, name: str, revision: str
    ) -> Response:
        _no_query(request)

        def read(queries: MetadataQueries, _: PolicySnapshot) -> tuple[ServiceResult, None]:
            identity = RepositoryIdentity.of(repository_type, f"{namespace}/{name}")
            found = queries.read_reference(identity, None if revision == "current" else revision)
            return ServiceResult(
                "reference read",
                {"locator_base": "published/", "reference": found.model_dump(mode="json")},
            ), None

        return await execute(request, read)

    @app.get(
        PREFIX
        + "/repositories/{repository_type}/{namespace}/{name}"
        + "/manifests/{commit_sha}/{publication_id}",
        response_model=ReadResponse,
    )
    async def manifest(  # noqa: PLR0913 - explicit path components are FastAPI route parameters
        request: Request,
        *,
        repository_type: str,
        namespace: str,
        name: str,
        commit_sha: str,
        publication_id: str,
    ) -> Response:
        _no_query(request)

        def read(queries: MetadataQueries, _: PolicySnapshot) -> tuple[ServiceResult, None]:
            identity = RepositoryIdentity.of(repository_type, f"{namespace}/{name}")
            found = queries.read_manifest(
                PublicationQuery(identity, CommitSha(commit_sha), PublicationId(publication_id))
            )
            return ServiceResult(
                "manifest read",
                {"manifest": found.model_dump(mode="json"), "tree_base": "archive-root/"},
            ), None

        return await execute(request, read, large=True)

    def public_operation(receipt: OperationReceipt) -> dict[str, Any]:
        payload = receipt.model_dump(mode="json")
        public = {key: value for key, value in payload.items() if key in OperationView.model_fields}
        return OperationView.model_validate(
            public | {"result_recorded": receipt.result is not None}
        ).model_dump()

    async def observe(request: Request, work: Callable[[], Response]) -> Response:
        # History remains observable without loading a changed/invalid archive
        # policy. This pool still bounds reads and slow result observers.
        lease = app.state.pool.submit(work)
        request.state.metadata_leases.append(lease)
        return await lease.future

    @app.get(PREFIX + "/operations", response_model=ReadResponse)
    async def operations(request: Request) -> Response:
        page = _page_query(request, server, repositories=False)

        def read() -> Response:
            held = app.state.operations.list()
            by_id = {item.operation_id: item for item in held}
            identifiers, cursor = _paginate(
                list(by_id), page, key=f"operations:{app.state.instance_id}"
            )
            return render(
                request,
                ServiceResult(
                    "operations list",
                    {
                        "operations": [
                            public_operation(by_id[identifier]) for identifier in identifiers
                        ]
                    },
                ),
                cursor=cursor,
            )

        return await observe(request, read)

    @app.get(PREFIX + "/operations/lookup", response_model=ReadResponse)
    async def lookup_operation(request: Request) -> Response:
        _no_query(request)
        keys = request.headers.getlist("idempotency-key")
        if len(keys) != 1:
            raise RequestError

        def read() -> Response:
            receipt = app.state.operations.lookup(request.state.principal, keys[0])
            return render(
                request,
                ServiceResult("operations lookup", {"operation": public_operation(receipt)}),
                receipt=receipt,
            )

        return await observe(request, read)

    @app.get(PREFIX + "/operations/{operation_id}", response_model=ReadResponse)
    async def show_operation(request: Request, operation_id: str) -> Response:
        _no_query(request)

        def read() -> Response:
            receipt = app.state.operations.get(operation_id)
            return render(
                request,
                ServiceResult("operations show", {"operation": public_operation(receipt)}),
                receipt=receipt,
            )

        return await observe(request, read)

    @app.get(PREFIX + "/operations/{operation_id}/result", response_model=ReadResponse)
    async def operation_result(request: Request, operation_id: str) -> Response:
        _no_query(request)

        def read() -> Response:
            receipt = app.state.operations.get(operation_id)
            result = app.state.operations.result(operation_id)
            return render(request, result, receipt=receipt, large=True)

        return await observe(request, read)

    @app.get(PREFIX + "/operations/{operation_id}/events", response_model=ReadResponse)
    async def operation_events(request: Request, operation_id: str) -> Response:
        if set(request.query_params) - {"after", "limit"}:
            raise RequestError
        converted = {}
        for field, default in (
            ("after", 0),
            ("limit", min(100, server.limits.max_page_size, server.limits.operation_max_events)),
        ):
            if len(request.query_params.getlist(field)) > 1:
                raise RequestError
            value = request.query_params.get(field, str(default))
            if not value.isascii() or not value.isdecimal() or len(value) > _MAX_OFFSET_DIGITS:
                raise RequestError
            converted[field] = int(value)
        if not 1 <= converted["limit"] <= server.limits.max_page_size:
            raise RequestError

        def read() -> Response:
            receipt = app.state.operations.get(operation_id)
            page = app.state.operations.events(operation_id, **converted)
            return render(
                request,
                ServiceResult(
                    "operations events",
                    {
                        "operation_id": operation_id,
                        "events": [event.model_dump(mode="json") for event in page.events],
                        "next_cursor": page.next_cursor,
                        "oldest_sequence": page.oldest_sequence,
                        "truncated": page.truncated,
                    },
                ),
                receipt=receipt,
            )

        return await observe(request, read)

    @app.get(PREFIX + "/openapi.json", include_in_schema=False)
    async def schema(request: Request) -> Response:
        _no_query(request)
        # The cached public schema is deterministic across requests/apps. A
        # native Unix response gets an independent local server-base view.
        view = app.openapi() | {"servers": [{"url": request.scope.get("root_path") or "/"}]}
        return bounded_static(JSONResponse(view))

    if server.interactive_docs:

        @app.get(PREFIX + "/docs", include_in_schema=False)
        async def docs(request: Request) -> Response:
            _no_query(request)
            return bounded_static(
                get_swagger_ui_html(
                    openapi_url=request.scope.get("root_path", "") + PREFIX + "/openapi.json",
                    title="hfcache API",
                    swagger_ui_parameters={"persistAuthorization": False},
                )
            )

    install_command_routes(app, server, render)
    install_maintenance_routes(app, server)
    return app
