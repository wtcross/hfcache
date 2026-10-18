"""Authenticated bounded read application; importing creates no app or listener.

Decision 113 and plan §§3-4 keep metadata behind typed services. No admission,
writer command, credential resolver or Hub client is exposed as a route.
"""

import base64
import hashlib
import ipaddress
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.security import HTTPBearer
from pydantic import ValidationError
from starlette.exceptions import HTTPException

from hfcache.api.auth import Capability, CredentialRegistry, load_credentials, require_capability
from hfcache.api.lifecycle import MetadataPool, instance_lock
from hfcache.api.models import ApiProblem, OperationView, PageQuery, ReadResponse
from hfcache.api.operations import OperationLimits, OperationReceipt, OperationStore
from hfcache.errors import (
    CodedError,
    ConfigurationError,
    HfcacheError,
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

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from starlette.types import ASGIApp, Message, Receive, Scope, Send

    from hfcache.config import ApplicationConfig
    from hfcache.services.queries import MetadataQueries

PREFIX = "/api/v1"
_CHUNK = 8192
_MAX_QUERY_BYTES = 8192
_MAX_HEADER_BYTES = 32768
_MAX_LIMIT_DIGITS = 5
_MAX_SELECTORS = 100
_MAX_SELECTOR_BYTES = 256
_MAX_OFFSET_DIGITS = 10


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


class Boundary:
    """Authenticate before routing/validation and contain every HTTP error surface."""

    def __init__(self, app: ASGIApp, *, owner: FastAPI, server: ServerConfig) -> None:
        self.app, self.owner, self.server = app, owner, server

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
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
                require_capability(principal, Capability.READ)
                state["principal"] = principal
                self.validate_transport(scope)
                if not await _empty_body(receive, self.server.limits.max_request_bytes):
                    return

                delivered = False

                async def replay() -> Message:
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": b"", "more_body": False}
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
        return registry.authenticate(values[0] if len(values) == 1 else None)

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
        if self.server.listener.root_path and not scope["path"].startswith(
            self.server.listener.root_path + "/"
        ):
            raise RequestError(code="HFAPI007", status_code=404)
        if self.server.listener.proxy_tls and scope.get("client") is not None:
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
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        if server.mcp_enabled:
            message = "MCP is unavailable until its acceptance gate"
            raise RequestError(message=message)
        with instance_lock(instance_lock_path or Path("/run/hfcache/api.lock")):
            configure_daemon(level=getattr(logging, server.log_level.upper()))
            application.state.credentials = credentials or load_credentials(server)
            application.state.policy = policy or InstalledPolicy.open(server)
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
                application.state.instance_id = ExecutionContext.create().run_id
                application.state.version = query_version()
                try:
                    yield
                finally:
                    await application.state.pool.close()
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
                    "operations": False,
                    "operation_history": True,
                    "mcp": False,
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
                "archive init --inspect",
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
        return bounded_static(JSONResponse(app.openapi()))

    if server.interactive_docs:

        @app.get(PREFIX + "/docs", include_in_schema=False)
        async def docs(request: Request) -> Response:
            _no_query(request)
            return bounded_static(
                get_swagger_ui_html(
                    openapi_url=server.listener.root_path + PREFIX + "/openapi.json",
                    title="hfcache API",
                    swagger_ui_parameters={"persistAuthorization": False},
                )
            )

    return app
