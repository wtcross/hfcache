"""Fixed host effects and original-key observation (INV-022, decision156).

Only the protected helper acts on the host. API transmission uncertainty never
becomes a normal failed result or another executable request.
"""

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NoReturn, Protocol, cast

from fastapi import Request  # noqa: TC002 - FastAPI resolves endpoint annotations
from pydantic import ValidationError
from starlette.responses import Response  # noqa: TC002 - FastAPI resolves endpoint annotations

from hfcache.api.auth import AdminCapability, require_admin_capability
from hfcache.api.command_models import AcceptanceResponse
from hfcache.api.commands import Render, _accepted, _key, offload_command
from hfcache.api.host_routes import HOST_EFFECT_ROUTES, OBSERVER_STOPS, SCHEDULE_CHANGES
from hfcache.api.models import ReadResponse
from hfcache.api.operations import Admission, request_digest
from hfcache.errors import (
    AuthorizationError,
    HostAdministrationUnavailableError,
    OperationError,
    RequestError,
)
from hfcache.host_actions_models import (
    HostActionRequest,
    HostJournalPage,
    HostObserverStatus,
    JournalQuery,
    ObserverExpected,
    ObserverStopOutcome,
    ObserverStopRequest,
    ScheduleChangeOutcome,
    ScheduleChangeRequest,
    ScheduleValidation,
    ScheduleValidationRequest,
)
from hfcache.host_protocol import HostProtocolError
from hfcache.services.context import ExecutionContext, ServiceResult

if TYPE_CHECKING:
    from fastapi import FastAPI

    from hfcache.host_models import HostBinding
    from hfcache.server_config import PolicySnapshot, ServerConfig

VALIDATIONS = "/api/v1/host/sync-schedule/validations"
_OBSERVER = "/api/v1/host/sync-observer"
_JOURNAL = "/api/v1/host/journal"
_TRANSMISSION = "host.transmission"


class HostActionClient(Protocol):
    def observer_status(self) -> dict[str, Any]: ...
    async def async_observer_status(self) -> dict[str, Any]: ...
    async def async_schedule_validate(self, body: dict[str, Any]) -> dict[str, Any]: ...
    async def async_journal_read(self, body: dict[str, Any]) -> dict[str, Any]: ...
    def schedule_change(self, body: dict[str, Any]) -> dict[str, Any]: ...
    def observer_stop(self, body: dict[str, Any]) -> dict[str, Any]: ...
    def schedule_outcome(self, body: dict[str, Any]) -> dict[str, Any]: ...
    def observer_outcome(self, body: dict[str, Any]) -> dict[str, Any]: ...


class _HostActionUncertainError(RuntimeError):
    """Possible helper transmission; preserve interruption and halt this lane."""


def _uncertain() -> NoReturn:
    raise _HostActionUncertainError


def _helper(request: Request) -> HostActionClient:
    return cast("HostActionClient", request.app.state.host_helper)


def _no_query(request: Request) -> None:
    if request.query_params:
        raise RequestError


def _failure(error: Exception) -> NoReturn:
    if isinstance(error, HostProtocolError):
        if error.reason == "operation-denied":
            raise AuthorizationError from None
        if error.reason in {"invalid-request", "host-conflict"}:
            raise RequestError(
                code="HFAPI007",
                status_code=409 if error.reason == "host-conflict" else 400,
                message="Host action input or expected evidence was refused",
            ) from None
    raise HostAdministrationUnavailableError from None


def _archive(request: Request, identifier: str) -> None:
    if identifier != request.app.state.policy.archive_id:
        raise HostAdministrationUnavailableError


def _binding(status: HostObserverStatus, action: str) -> HostBinding:
    if status.host_binding is None or status.profile is None:
        raise HostAdministrationUnavailableError
    reason = getattr(status.permission_reasons, action)
    if not getattr(status.permissions, action):
        if reason in {"policy-denied", "profile-unproved", "guard-held"}:
            raise AuthorizationError
        raise HostAdministrationUnavailableError
    if status.profile != "native" or status.state not in {"observed", "inactive"}:
        raise HostAdministrationUnavailableError
    return status.host_binding


def _check_archive(binding: HostBinding, identifier: str, root: str) -> None:
    if binding.archive_id != identifier or binding.archive_root != root:
        raise HostAdministrationUnavailableError


@dataclass(frozen=True, slots=True)
class HostActionAuthorization:
    action: str
    binding: HostBinding
    client: HostActionClient = field(repr=False, compare=False)
    expected: ObserverExpected | None = None

    def check_snapshot(self, snapshot: PolicySnapshot) -> None:
        _check_archive(
            self.binding,
            snapshot.config.storage.archive_id,
            str(snapshot.config.storage.archive_root),
        )

    def recheck(self, snapshot: PolicySnapshot) -> None:
        try:
            status = HostObserverStatus.model_validate(self.client.observer_status())
        except Exception as error:  # noqa: BLE001 - untrusted helper boundary; fixed refusal only
            _failure(error)
        current = _binding(status, self.action)
        if current.deployment_sha256 != self.binding.deployment_sha256:
            raise HostAdministrationUnavailableError
        _check_archive(
            current, snapshot.config.storage.archive_id, str(snapshot.config.storage.archive_root)
        )


async def _authorize(request: Request, action: str) -> HostActionAuthorization:
    try:
        status = HostObserverStatus.model_validate(await _helper(request).async_observer_status())
    except Exception as error:  # noqa: BLE001 - untrusted helper boundary; fixed refusal only
        _failure(error)
    binding = _binding(status, action)
    _check_archive(binding, request.app.state.policy.archive_id, str(request.app.state.policy.root))
    return HostActionAuthorization(action, binding, _helper(request), status.expected)


def _outcome(
    request: Request, route: str, identifier: str, digest: str
) -> ScheduleChangeOutcome | ObserverStopOutcome:
    outcome: ScheduleChangeOutcome | ObserverStopOutcome
    try:
        body = {"operation_id": identifier, "request_digest": digest}
        if route == SCHEDULE_CHANGES:
            outcome = ScheduleChangeOutcome.model_validate(_helper(request).schedule_outcome(body))
        else:
            outcome = ObserverStopOutcome.model_validate(_helper(request).observer_outcome(body))
    except Exception as error:  # noqa: BLE001 - untrusted helper boundary; fixed refusal only
        _failure(error)
    _archive(request, outcome.archive_id)
    if outcome.operation_id != identifier or outcome.request_digest != digest:
        raise HostAdministrationUnavailableError
    return outcome


def _unresolved(request: Request) -> None:
    # No API lock spans this helper I/O. The helper independently locks effects.
    for receipt in request.app.state.operations.list():
        if receipt.route not in HOST_EFFECT_ROUTES or receipt.state == "succeeded":
            continue
        if receipt.state in {"queued", "waiting_lock", "running"}:
            raise RequestError(
                code="HFAPI007", status_code=409, message="Another host action is active"
            )
        if _TRANSMISSION not in {event.kind for event in receipt.events}:
            continue
        outcome = _outcome(request, receipt.route, receipt.operation_id, receipt.request_digest)
        if outcome.state not in {"confirmed", "unchanged"} or outcome.pending:
            raise RequestError(
                code="HFAPI007",
                status_code=409,
                message="An earlier host action requires original-handle reconciliation",
            )


def _execute(
    request: Request, route: str, body: HostActionRequest, context: ExecutionContext
) -> ServiceResult:
    identifier = context.operation_id
    if identifier is None:
        raise OperationError
    receipt = request.app.state.operations.get(identifier)
    request.app.state.operations.append_event(identifier, _TRANSMISSION, "Host handoff intended")
    frame = {
        "operation_id": identifier,
        "request_digest": receipt.request_digest,
        "request": body.canonical_body(),
    }
    outcome: ScheduleChangeOutcome | ObserverStopOutcome
    try:
        if route == SCHEDULE_CHANGES:
            raw = _helper(request).schedule_change(frame)
            outcome = ScheduleChangeOutcome.model_validate(raw)
            if (
                not isinstance(body, ScheduleChangeRequest)
                or outcome.action != body.action
                or outcome.expected_revision != body.expected_revision
            ):
                _uncertain()
        else:
            raw = _helper(request).observer_stop(frame)
            outcome = ObserverStopOutcome.model_validate(raw)
            if not isinstance(body, ObserverStopRequest) or outcome.expected != body.expected:
                _uncertain()
        _archive(request, outcome.archive_id)
        if (
            outcome.operation_id != identifier
            or outcome.request_digest != receipt.request_digest
            or outcome.state not in {"confirmed", "unchanged"}
            or outcome.pending
        ):
            _uncertain()
    except Exception:  # noqa: BLE001 - possible transmission or malformed observation remains unknown
        # Includes invalid replies and apparent denial after transmission. Only
        # durable original helper evidence can classify that uncertain exchange.
        raise _HostActionUncertainError from None
    command = "host schedule change" if route == SCHEDULE_CHANGES else "host observer stop"
    if outcome.state == "unchanged":
        error = RequestError(
            code="HFAPI007",
            status_code=409,
            message="Expected host evidence changed; no host effect was sent",
        )
        return ServiceResult(
            command,
            outcome.model_dump(mode="json"),
            errors=error.problems,
            exit_code=int(error.exit_code),
        )
    return ServiceResult(command, outcome.model_dump(mode="json"))


async def _apply(
    request: Request, body: HostActionRequest, route: str, server: ServerConfig
) -> Response:
    _no_query(request)
    schedule = route == SCHEDULE_CHANGES
    require_admin_capability(
        request.state.principal,
        AdminCapability.SCHEDULE_WRITE if schedule else AdminCapability.OBSERVER_STOP,
    )
    authorization = await _authorize(request, "schedule" if schedule else "observer")
    if isinstance(body, ObserverStopRequest) and authorization.expected != body.expected:
        raise RequestError(
            code="HFAPI007",
            status_code=409,
            message="The original scheduled observer invocation changed before admission",
        )
    key = _key(request)
    digest = request_digest(route, body.canonical_body())

    def work() -> Response:
        try:
            previous = request.app.state.operations.lookup(request.state.principal, key)
        except OperationError as error:
            if error.status_code != HTTPStatus.NOT_FOUND:
                raise
        else:
            if previous.route != route or previous.request_digest != digest:
                raise RequestError(
                    code="HFAPI012",
                    status_code=409,
                    message="Idempotency key conflicts with its admitted request",
                )
            return _accepted(request, Admission(previous, created=False), server)
        _unresolved(request)

        def budget(snapshot: PolicySnapshot) -> float:
            authorization.check_snapshot(snapshot)
            return snapshot.config.sync.lock_wait_seconds

        admission = request.app.state.host_runner.submit(
            request.state.principal,
            key,
            route,
            body.canonical_body(),
            command="host schedule change" if schedule else "host observer stop",
            execute=lambda _snapshot, context: _execute(request, route, body, context),
            wait_seconds=budget,
            requires_lock=False,
            context=request.state.execution_context,
            authorize=authorization.recheck,
        )
        return _accepted(request, admission, server)

    return await offload_command(request, work)


async def _observe(request: Request, route: str, identifier: str, render: Render) -> Response:
    _no_query(request)
    require_admin_capability(request.state.principal, AdminCapability.HOST_READ)
    key = _key(request)

    def work() -> Response:
        receipt = request.app.state.operations.lookup(request.state.principal, key)
        if receipt.route != route or receipt.operation_id != identifier:
            raise RequestError(
                code="HFAPI007",
                status_code=409,
                message="Original host action key and identity must match",
            )
        outcome = _outcome(request, route, identifier, receipt.request_digest)
        command = "host schedule outcome" if route == SCHEDULE_CHANGES else "host observer outcome"
        return render(request, ServiceResult(command, outcome.model_dump(mode="json")))

    return await offload_command(request, work)


def install_host_action_routes(app: FastAPI, render: Render, server: ServerConfig) -> None:
    app.state.command_routes = (
        frozenset(getattr(app.state, "command_routes", ())) | HOST_EFFECT_ROUTES | {VALIDATIONS}
    )

    @app.get(_OBSERVER, response_model=ReadResponse)
    async def observer_status(request: Request) -> Response:
        _no_query(request)
        require_admin_capability(request.state.principal, AdminCapability.HOST_READ)
        try:
            status = HostObserverStatus.model_validate(
                await _helper(request).async_observer_status()
            )
            _archive(request, status.archive_id)
        except Exception:  # noqa: BLE001 - possible transmission or malformed observation remains unknown
            status = HostObserverStatus.model_validate(
                {
                    "schema_version": 1,
                    "archive_id": request.app.state.policy.archive_id,
                    "profile": None,
                    "host_binding": None,
                    "permissions": {"schedule": False, "observer": False},
                    "permission_reasons": {
                        "schedule": "helper-unavailable",
                        "observer": "helper-unavailable",
                    },
                    "state": "unavailable",
                    "reason": "helper-unavailable",
                    "unit": "hfcache-sync.service",
                    "expected": None,
                }
            )
        return render(
            request, ServiceResult("host observer status", status.model_dump(mode="json"))
        )

    @app.post(VALIDATIONS, response_model=ReadResponse)
    async def validate_schedule(request: Request, body: ScheduleValidationRequest) -> Response:
        _no_query(request)
        require_admin_capability(request.state.principal, AdminCapability.SCHEDULE_WRITE)
        await _authorize(request, "schedule")
        try:
            result = ScheduleValidation.model_validate(
                await _helper(request).async_schedule_validate(body.canonical_body())
            )
        except Exception as error:  # noqa: BLE001 - untrusted helper boundary; fixed refusal only
            _failure(error)
        _archive(request, result.archive_id)
        if (
            result.on_calendar != body.on_calendar
            or result.randomized_delay_sec != body.randomized_delay_sec
        ):
            raise HostAdministrationUnavailableError
        return render(
            request, ServiceResult("host schedule validate", result.model_dump(mode="json"))
        )

    @app.post(SCHEDULE_CHANGES, response_model=AcceptanceResponse, status_code=202)
    async def change_schedule(request: Request, body: ScheduleChangeRequest) -> Response:
        return await _apply(request, body, SCHEDULE_CHANGES, server)

    @app.post(OBSERVER_STOPS, response_model=AcceptanceResponse, status_code=202)
    async def stop_observer(request: Request, body: ObserverStopRequest) -> Response:
        return await _apply(request, body, OBSERVER_STOPS, server)

    @app.get(SCHEDULE_CHANGES + "/{operation_id}", response_model=ReadResponse)
    async def schedule_outcome(request: Request, operation_id: str) -> Response:
        return await _observe(request, SCHEDULE_CHANGES, operation_id, render)

    @app.get(OBSERVER_STOPS + "/{operation_id}", response_model=ReadResponse)
    async def observer_outcome(request: Request, operation_id: str) -> Response:
        return await _observe(request, OBSERVER_STOPS, operation_id, render)

    @app.get(_JOURNAL, response_model=ReadResponse)
    async def journal(request: Request) -> Response:
        require_admin_capability(request.state.principal, AdminCapability.HOST_READ)
        query = request.query_params
        if set(query) - {"source", "cursor", "limit"} or any(
            len(query.getlist(key)) != 1 for key in query
        ):
            raise RequestError
        try:
            limit = query.get("limit", "80")
            if not limit.isascii() or not limit.isdecimal() or str(int(limit)) != limit:
                raise RequestError
            body = JournalQuery.model_validate(
                {"source": query.get("source"), "cursor": query.get("cursor"), "limit": int(limit)}
            )
        except ValueError, ValidationError:
            raise RequestError from None
        try:
            result = HostJournalPage.model_validate(
                await _helper(request).async_journal_read(body.model_dump(mode="json"))
            )
        except Exception as error:  # noqa: BLE001 - untrusted helper boundary; fixed refusal only
            _failure(error)
        _archive(request, result.archive_id)
        if result.source != body.source or len(result.entries) > body.limit:
            raise HostAdministrationUnavailableError
        return render(request, ServiceResult("host journal", result.model_dump(mode="json")))
