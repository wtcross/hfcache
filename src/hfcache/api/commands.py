"""Typed command routes delegate to services and durable admission (decision 116)."""

import json
from contextlib import suppress
from typing import TYPE_CHECKING, Protocol

from fastapi import Request  # noqa: TC002 - FastAPI resolves endpoint annotations at runtime
from starlette.responses import Response

from hfcache.api.auth import Capability, require_capability
from hfcache.api.command_models import (
    AcceptanceResponse,
    DiagnosticsSubmission,
    OperationLinks,
    PlanSubmission,
    SyncSubmission,
    ValidationSubmission,
    VerificationSubmission,
)
from hfcache.api.models import OperationView, ReadResponse
from hfcache.credentials import resolve_token
from hfcache.errors import HfcacheError, RequestError
from hfcache.locking import remaining_wait_seconds
from hfcache.redaction import redact_text, sanitize
from hfcache.services.candidates import (
    CandidateAssessment,
    prepare_candidate_plan,
    require_compatible_authority,
    validate_candidate,
)
from hfcache.services.commands import CommandServices, DoctorRequest, SelectionRequest
from hfcache.services.context import ServiceResult
from hfcache.services.queries import validate_config

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI

    from hfcache.api.command_models import CommandModel
    from hfcache.api.operations import Admission, OperationReceipt
    from hfcache.reporting import Envelope
    from hfcache.server_config import PolicySnapshot, ServerConfig
    from hfcache.services.context import ExecutionContext

PREFIX = "/api/v1"
COMMAND_ROUTES = frozenset(
    PREFIX + suffix
    for suffix in ("/syncs", "/verifications", "/plans", "/diagnostics", "/config/validate")
)
WRITER_ROUTES = frozenset({PREFIX + "/syncs", PREFIX + "/verifications"})


class Render(Protocol):
    def __call__(  # noqa: PLR0913 - matches the existing bounded rendering interface
        self,
        request: Request,
        result: ServiceResult | Envelope,
        *,
        snapshot: PolicySnapshot | None = None,
        cursor: str | None = None,
        large: bool = False,
        receipt: OperationReceipt | None = None,
    ) -> Response: ...


def _key(request: Request) -> str:
    keys = request.headers.getlist("idempotency-key")
    if len(keys) != 1:
        raise RequestError
    return keys[0]


def _no_query(request: Request) -> None:
    if request.query_params:
        raise RequestError


def _accepted(request: Request, admission: Admission, server: ServerConfig) -> Response:
    receipt = admission.receipt
    metadata = receipt.model_dump(mode="json")
    view = OperationView.model_validate(
        {key: value for key, value in metadata.items() if key in OperationView.model_fields}
        | {"result_recorded": receipt.result is not None}
    )
    location = (
        request.scope.get("root_path", server.listener.root_path)
        + PREFIX
        + "/operations/"
        + receipt.operation_id
    )
    result = AcceptanceResponse(
        schema_version=1,
        request_id=request.state.execution_context.request_id or "",
        archive_id=receipt.archive_id,
        config_fingerprint=receipt.config_fingerprint,
        operation=view,
        created=admission.created,
        links=OperationLinks(
            status=location, result=location + "/result", events=location + "/events"
        ),
    )
    body = json.dumps(sanitize(result.model_dump(mode="json")), separators=(",", ":")).encode(
        "utf-8"
    )
    if len(body) > server.limits.max_response_bytes:
        raise RequestError(status_code=413)
    return Response(
        body,
        status_code=202,
        media_type="application/json",
        headers={"Location": redact_text(location)},
    )


async def offload_command(request: Request, work: Callable[[], Response]) -> Response:
    lease = request.app.state.pool.submit(work)
    request.state.metadata_leases.append(lease)
    return await lease.future


def command_service(
    request: Request, snapshot: PolicySnapshot, context: ExecutionContext
) -> CommandServices:
    """Use only the trusted lifespan credential path, never a request-selected file."""
    return CommandServices(
        snapshot.config,
        context,
        token_file=request.app.state.hub_token_file,
        curation_source=lambda: request.app.state.policy.snapshot().config,
    )


def admit_command(  # noqa: PLR0913 - explicit trusted route execution policy
    request: Request,
    body: CommandModel,
    server: ServerConfig,
    *,
    route: str,
    command: str,
    execute: Callable[[PolicySnapshot, ExecutionContext], ServiceResult | Envelope],
    requires_lock: bool,
    delegated: bool = False,
    prepare: Callable[[PolicySnapshot], None] | None = None,
) -> Response:
    """One durable keyed admission boundary shared by typed command adapters."""
    _no_query(request)
    key = _key(request)

    def budget(snapshot: PolicySnapshot) -> float:
        if prepare is not None:
            prepare(snapshot)
        return (
            snapshot.config.verification.lock_wait_seconds
            if delegated
            else snapshot.config.sync.lock_wait_seconds
        )

    admitted = request.app.state.runner.submit(
        request.state.principal,
        key,
        route,
        body.canonical_body(),
        command=command,
        execute=execute,
        wait_seconds=budget,
        requires_lock=requires_lock,
        delegated=delegated,
        context=request.state.execution_context,
    )
    return _accepted(request, admitted, server)


def install_command_routes(app: FastAPI, server: ServerConfig, render: Render) -> None:
    app.state.command_routes = frozenset(getattr(app.state, "command_routes", ())) | COMMAND_ROUTES
    app.state.writer_routes = frozenset(getattr(app.state, "writer_routes", ())) | WRITER_ROUTES

    @app.post(PREFIX + "/syncs", response_model=AcceptanceResponse, status_code=202)
    async def sync(request: Request, body: SyncSubmission) -> Response:
        require_capability(request.state.principal, Capability.WRITE)
        return await offload_command(
            request,
            lambda: admit_command(
                request,
                body,
                server,
                route=PREFIX + "/syncs",
                command="sync",
                requires_lock=True,
                execute=lambda snapshot, context: command_service(
                    request, snapshot, context
                ).synchronize(SelectionRequest(body.selectors)),
            ),
        )

    @app.post(PREFIX + "/plans", response_model=AcceptanceResponse, status_code=202)
    async def plan(request: Request, body: PlanSubmission) -> Response:
        require_capability(
            request.state.principal,
            Capability.WRITE if body.candidate is not None else Capability.READ,
        )
        prepared: list[CandidateAssessment | ServiceResult] = []

        def prepare(snapshot: PolicySnapshot) -> None:
            if body.candidate is not None:
                prepared.append(prepare_candidate_plan(body.candidate, snapshot.config))

        def execute(snapshot: PolicySnapshot, context: ExecutionContext) -> ServiceResult:
            if body.candidate is None:
                return command_service(request, snapshot, context).plan_sync(
                    SelectionRequest(body.selectors)
                )
            candidate = prepared[0]
            if isinstance(candidate, ServiceResult):
                return candidate
            # credential_name is deliberately absent from the policy fingerprint.
            # Recheck all six authority fields after waiting, before resolving any
            # installed credential or constructing the Hub adapter (decision 119).
            current = app.state.policy.snapshot()
            require_compatible_authority(candidate.config, current.config)
            policy = candidate.config.model_copy(update={"hub": current.config.hub})
            return CommandServices(policy, context, token_file=app.state.hub_token_file).plan_sync(
                SelectionRequest(body.selectors)
            )

        return await offload_command(
            request,
            lambda: admit_command(
                request,
                body,
                server,
                route=PREFIX + "/plans",
                command="plan",
                requires_lock=False,
                prepare=prepare,
                execute=execute,
            ),
        )

    @app.post(PREFIX + "/diagnostics", response_model=AcceptanceResponse, status_code=202)
    async def diagnose(request: Request, body: DiagnosticsSubmission) -> Response:
        require_capability(
            request.state.principal, Capability.READ if body.read_only else Capability.WRITE
        )
        return await offload_command(
            request,
            lambda: admit_command(
                request,
                body,
                server,
                route=PREFIX + "/diagnostics",
                command="doctor",
                requires_lock=not body.read_only,
                execute=lambda snapshot, context: command_service(
                    request, snapshot, context
                ).diagnose(DoctorRequest(read_only=body.read_only)),
            ),
        )

    @app.post(PREFIX + "/verifications", response_model=AcceptanceResponse, status_code=202)
    async def verify(request: Request, body: VerificationSubmission) -> Response:
        require_capability(request.state.principal, Capability.WRITE)
        verification = body.service_request()

        def execute(snapshot: PolicySnapshot, context: ExecutionContext) -> Envelope:
            if context.operation_id is None:
                raise RequestError
            return app.state.verifier.execute(
                context.operation_id,
                verification,
                snapshot.fingerprint,
                remaining_wait_seconds() or 0.0,
            )

        return await offload_command(
            request,
            lambda: admit_command(
                request,
                body,
                server,
                route=PREFIX + "/verifications",
                command=verification.command,
                requires_lock=False,
                delegated=True,
                execute=execute,
            ),
        )

    @app.post(PREFIX + "/config/validate", response_model=ReadResponse)
    async def installed_validation(request: Request, body: ValidationSubmission) -> Response:
        _no_query(request)
        require_capability(
            request.state.principal,
            Capability.WRITE if body.candidate is not None else Capability.READ,
        )

        def work() -> Response:
            snapshot = None
            if body.candidate is not None:
                with suppress(HfcacheError):
                    snapshot = app.state.policy.snapshot()
                result = validate_candidate(body.candidate, snapshot.config if snapshot else None)
                return render(request, result, snapshot=snapshot)
            try:
                snapshot = app.state.policy.snapshot()
                token = resolve_token(snapshot.config.hub, token_file=app.state.hub_token_file)
                result = validate_config(snapshot.config, token_source=token.source.value)
            except HfcacheError as error:
                result = ServiceResult(
                    "config validate", {}, errors=error.problems, exit_code=int(error.exit_code)
                )
            return render(request, result, snapshot=snapshot)

        return await offload_command(request, work)
