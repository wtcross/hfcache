"""Exact managed configuration and non-replaying application (decisions153/154)."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NoReturn, Protocol, cast

from fastapi import Request  # noqa: TC002 - FastAPI resolves route annotations
from pydantic import ValidationError
from starlette.responses import Response  # noqa: TC002 - FastAPI resolves route annotations

from hfcache.api.auth import AdminCapability, require_admin_capability
from hfcache.api.command_models import AcceptanceResponse
from hfcache.api.commands import _accepted, _key, _no_query, offload_command
from hfcache.api.host_authorization import authorize_request
from hfcache.api.models import ReadResponse
from hfcache.api.operations import Admission, request_digest
from hfcache.config_models import (
    ConfigApplicationOutcome,
    ConfigApplicationSubmission,
    ConfigPrepared,
    ConfigRead,
    ManagedAssessment,
    ManagedEditRequest,
    ManagedValidation,
)
from hfcache.errors import (
    AuthorizationError,
    HfcacheError,
    HostAdministrationUnavailableError,
    OperationError,
    RequestError,
)
from hfcache.host_protocol import HostProtocolError
from hfcache.services.candidates import parse_candidate, require_compatible_authority
from hfcache.services.commands import CommandServices, SelectionRequest
from hfcache.services.context import ServiceResult
from hfcache.wire_models import PlanPayload

if TYPE_CHECKING:
    from fastapi import FastAPI

    from hfcache.api.command_models import PlanSubmission, ValidationSubmission
    from hfcache.api.commands import Render
    from hfcache.api.host_authorization import ActionAuthorization
    from hfcache.config import ApplicationConfig
    from hfcache.host_models import HostAction
    from hfcache.server_config import PolicySnapshot, ServerConfig
    from hfcache.services.context import ExecutionContext


class ConfigHelper(Protocol):
    async def async_config_read(self) -> dict[str, Any]: ...
    async def async_config_prepare(self, body: dict[str, Any]) -> dict[str, Any]: ...
    def config_prepare(self, body: dict[str, Any]) -> dict[str, Any]: ...
    def config_apply(self, body: dict[str, Any]) -> dict[str, Any]: ...
    def config_outcome(self, body: dict[str, Any]) -> dict[str, Any]: ...


def _helper(request: Request) -> ConfigHelper:
    return cast("ConfigHelper", request.app.state.host_helper)


def _failure(error: Exception) -> NoReturn:
    if isinstance(error, HostProtocolError) and error.reason == "config-conflict":
        raise RequestError(
            code="HFAPI007",
            status_code=409,
            message="Installed configuration changed; read a fresh base before editing",
        ) from None
    if isinstance(error, HostProtocolError) and error.reason == "operation-denied":
        raise AuthorizationError from None
    if isinstance(error, HostProtocolError) and error.reason == "invalid-request":
        raise RequestError from None
    raise HostAdministrationUnavailableError from None


def _archive(request: Request, archive_id: str) -> None:
    if archive_id != request.app.state.policy.archive_id:
        raise HostAdministrationUnavailableError


def _decode_prepared(
    request: Request, raw: dict[str, Any], managed: ManagedEditRequest
) -> ConfigPrepared:
    try:
        prepared = ConfigPrepared.model_validate(raw)
    except ValidationError:
        raise HostAdministrationUnavailableError from None
    _archive(request, prepared.archive_id)
    if prepared.base_revision != managed.base_revision:
        raise HostAdministrationUnavailableError
    return prepared


async def _prepare(request: Request, managed: ManagedEditRequest) -> ConfigPrepared:
    try:
        raw = await _helper(request).async_config_prepare(
            managed.model_dump(mode="json", exclude_none=True)
        )
    except Exception as error:  # noqa: BLE001 - unavailable fixed boundary, no external text
        _failure(error)
    return _decode_prepared(request, raw, managed)


@dataclass(frozen=True, slots=True)
class PreparedCandidate:
    """Private request-lifetime material; generic operation records contain no raw text."""

    reply: ConfigPrepared = field(repr=False)
    config: ApplicationConfig = field(repr=False)


def _checked(request: Request, reply: ConfigPrepared) -> PreparedCandidate:
    try:
        config = parse_candidate(reply.candidate)
        installed = request.app.state.policy.snapshot().config
    except HfcacheError:
        raise HostAdministrationUnavailableError from None
    require_compatible_authority(config, installed)
    # The helper projection and private TOML must describe exactly the same edit.
    complete = config.model_dump(mode="json")
    editable = reply.editable.model_dump(mode="json")
    expected = {
        table: (
            complete[table]
            if table == "repositories"
            else {key: complete[table][key] for key in values}
        )
        for table, values in editable.items()
    }
    if editable != expected:
        raise HostAdministrationUnavailableError
    return PreparedCandidate(reply, config)


def _validation(reply: ConfigPrepared) -> ManagedValidation:
    return ManagedValidation(
        schema_version=1,
        archive_id=reply.archive_id,
        base_revision=reply.base_revision,
        candidate_revision=reply.candidate_revision,
        required_selectors=reply.required_selectors,
        valid=True,
    )


async def managed_validation(
    request: Request, body: ValidationSubmission, render: Render
) -> Response:
    _no_query(request)
    require_admin_capability(request.state.principal, AdminCapability.CONFIG_WRITE)
    if body.managed is None:
        raise RequestError
    await authorize_request(request, frozenset({"configuration"}))
    reply = await _prepare(request, body.managed)

    def work() -> Response:
        _checked(request, reply)
        return render(
            request,
            ServiceResult("config validate", _validation(reply).model_dump(mode="json")),
        )

    return await offload_command(request, work)


def _assessment(
    reply: ConfigPrepared, *, complete: bool, sizing: PlanPayload | None
) -> ManagedAssessment:
    return ManagedAssessment(
        schema_version=1,
        archive_id=reply.archive_id,
        base_revision=reply.base_revision,
        candidate_revision=reply.candidate_revision,
        required_selectors=reply.required_selectors,
        complete=complete,
        sizing=sizing,
    )


def _execute(
    request: Request,
    managed: ManagedEditRequest,
    admitted: PreparedCandidate,
    snapshot: PolicySnapshot,
    context: ExecutionContext,
) -> ServiceResult:
    # This runs after durable admission and outside runner/store locks. Repeating
    # this read-only preparation is a fresh base check, never an installation replay.
    try:
        raw = _helper(request).config_prepare(managed.model_dump(mode="json", exclude_none=True))
    except Exception as error:  # noqa: BLE001 - preserve bounded helper failure classification
        _failure(error)
    current = _decode_prepared(request, raw, managed)
    if (
        current.candidate_revision != admitted.reply.candidate_revision
        or current.required_selectors != admitted.reply.required_selectors
        or current.candidate != admitted.reply.candidate
    ):
        raise HostAdministrationUnavailableError
    checked = _checked(request, current)
    require_compatible_authority(checked.config, snapshot.config)
    if not current.required_selectors:
        return ServiceResult(
            "plan", _assessment(current, complete=True, sizing=None).model_dump(mode="json")
        )
    result = CommandServices(
        checked.config, context, token_file=request.app.state.hub_token_file
    ).plan_sync(SelectionRequest(current.required_selectors))
    try:
        sizing = PlanPayload.model_validate(result.data)
    except ValidationError:
        sizing = None
    try:
        assessment = _assessment(current, complete=result.exit_code == 0, sizing=sizing)
    except ValidationError:
        # A service cannot turn partial/mismatched sizing into a successful preview.
        raise HostAdministrationUnavailableError from None
    return ServiceResult(
        "plan",
        assessment.model_dump(mode="json"),
        warnings=result.warnings,
        errors=result.errors,
        exit_code=result.exit_code,
    )


async def managed_plan(request: Request, body: PlanSubmission, server: ServerConfig) -> Response:
    _no_query(request)
    require_admin_capability(request.state.principal, AdminCapability.CONFIG_WRITE)
    if body.managed is None:
        raise RequestError
    # Permission precedes private configuration reads; sizing permission follows
    # the actual server-derived scope rather than browser selectors or guesses.
    await authorize_request(request, frozenset({"configuration"}))
    reply = await _prepare(request, body.managed)
    actions: frozenset[HostAction] = frozenset({"configuration"})
    if reply.required_selectors:
        actions = frozenset({"configuration", "hub"})
    authorization: ActionAuthorization | None = await authorize_request(request, actions)
    if authorization is None:
        raise HostAdministrationUnavailableError
    key = _key(request)
    managed = body.managed

    def work() -> Response:
        prepared = _checked(request, reply)

        def budget(snapshot: PolicySnapshot) -> float:
            # Pure checks only: the runner calls this under its admission lock.
            authorization.check_snapshot(snapshot)
            require_compatible_authority(prepared.config, snapshot.config)
            return snapshot.config.sync.lock_wait_seconds

        admission = request.app.state.runner.submit(
            request.state.principal,
            key,
            "/api/v1/plans",
            body.canonical_body(),
            command="plan",
            execute=lambda snapshot, context: _execute(
                request, managed, prepared, snapshot, context
            ),
            wait_seconds=budget,
            requires_lock=False,
            context=request.state.execution_context,
            authorize=authorization.recheck,
        )
        return _accepted(request, admission, server)

    return await offload_command(request, work)


_APPLICATIONS = "/api/v1/config/applications"


class _ApplicationUncertainError(RuntimeError):
    """Halt the lane after an unclassified handoff; original observation is read-only."""


def _conflict(message: str) -> NoReturn:
    raise RequestError(code="HFAPI007", status_code=409, message=message)


def _preview(
    request: Request, body: ConfigApplicationSubmission, prepared: ConfigPrepared
) -> ManagedAssessment:
    store = request.app.state.operations
    receipt = store.lookup(request.state.principal, body.preview.key)
    if (
        receipt.operation_id != body.preview.operation_id
        or receipt.route != "/api/v1/plans"
        or receipt.state != "succeeded"
        or receipt.archive_id != prepared.archive_id
    ):
        _conflict("Apply requires the original successful matching managed preview")
    result = store.result(receipt.operation_id)
    try:
        assessment = ManagedAssessment.model_validate(result.data)
    except ValidationError:
        _conflict("Apply requires a complete managed preview")
    if (
        result.exit_code != 0
        or not assessment.complete
        or assessment.archive_id != prepared.archive_id
        or assessment.base_revision != prepared.base_revision
        or assessment.candidate_revision != prepared.candidate_revision
        or assessment.required_selectors != prepared.required_selectors
    ):
        _conflict("Configuration or required scope differs from the original preview")
    return assessment


def _outcome(request: Request, identifier: str, digest: str) -> ConfigApplicationOutcome:
    try:
        raw = _helper(request).config_outcome(
            {"operation_id": identifier, "request_digest": digest}
        )
        outcome = ConfigApplicationOutcome.model_validate(raw)
    except Exception as error:  # noqa: BLE001 - fixed failure, never private diagnostic text
        _failure(error)
    _archive(request, outcome.archive_id)
    if outcome.operation_id != identifier or outcome.request_digest != digest:
        raise HostAdministrationUnavailableError
    return outcome


def _unresolved(request: Request) -> None:
    """No store/runner lock is held while authenticating previous host outcomes."""
    for receipt in request.app.state.operations.list():
        if receipt.route != _APPLICATIONS or receipt.state == "succeeded":
            continue
        if receipt.state in {"queued", "waiting_lock", "running"}:
            _conflict("Another configuration application is still active")
        kinds = {event.kind for event in receipt.events}
        if "configuration.transmission" not in kinds:
            continue
        outcome = _outcome(request, receipt.operation_id, receipt.request_digest)
        if outcome.state != "confirmed" or outcome.pending:
            _conflict(
                "An earlier configuration application requires original-handle reconciliation"
            )


def _execute_application(
    request: Request,
    body: ConfigApplicationSubmission,
    admitted: PreparedCandidate,
    snapshot: PolicySnapshot,
    context: ExecutionContext,
) -> ServiceResult:
    require_admin_capability(request.state.principal, AdminCapability.CONFIG_WRITE)
    try:
        raw = _helper(request).config_prepare(
            body.managed.model_dump(mode="json", exclude_none=True)
        )
    except Exception as error:  # noqa: BLE001 - refusal before effect transmission
        _failure(error)
    current = _decode_prepared(request, raw, body.managed)
    if (
        current.candidate_revision != admitted.reply.candidate_revision
        or current.required_selectors != admitted.reply.required_selectors
        or current.candidate != admitted.reply.candidate
    ):
        _conflict("Configuration changed before application execution")
    checked = _checked(request, current)
    require_compatible_authority(checked.config, snapshot.config)
    _preview(request, body, current)
    identifier = context.operation_id
    if identifier is None:
        raise OperationError
    store = request.app.state.operations
    receipt = store.get(identifier)
    # This durable event is the last API write before the single helper handoff.
    store.append_event(identifier, "configuration.transmission", "Configuration handoff intended")
    try:
        raw = _helper(request).config_apply(
            {
                "operation_id": identifier,
                "request_digest": receipt.request_digest,
                "managed": body.managed.model_dump(mode="json", exclude_none=True),
                "candidate_revision": current.candidate_revision,
                "config_fingerprint": checked.config.fingerprint(),
                "preview_operation_id": body.preview.operation_id,
                "required_selectors": list(current.required_selectors),
            }
        )
    except Exception:  # noqa: BLE001 - transmission outcome unknown, never retry or invent failure
        raise _ApplicationUncertainError from None
    try:
        outcome = ConfigApplicationOutcome.model_validate(raw)
        _archive(request, outcome.archive_id)
    except Exception:  # noqa: BLE001 - any invalid post-effect reply leaves outcome uncertain
        raise _ApplicationUncertainError from None
    if (
        outcome.operation_id != identifier
        or outcome.request_digest != receipt.request_digest
        or outcome.base_revision != current.base_revision
        or outcome.candidate_revision != current.candidate_revision
        or outcome.config_fingerprint != checked.config.fingerprint()
        or outcome.state != "confirmed"
        or outcome.pending
    ):
        raise _ApplicationUncertainError
    return ServiceResult("config apply", outcome.model_dump(mode="json"))


async def _apply(
    request: Request, body: ConfigApplicationSubmission, server: ServerConfig
) -> Response:
    _no_query(request)
    require_admin_capability(request.state.principal, AdminCapability.CONFIG_WRITE)
    await authorize_request(request, frozenset({"configuration"}))
    key = _key(request)
    digest = request_digest(_APPLICATIONS, body.canonical_body())

    def duplicate() -> Admission | None:
        try:
            previous = request.app.state.operations.lookup(request.state.principal, key)
        except OperationError as error:
            if error.status_code == 404:  # noqa: PLR2004 - classified missing original handle
                return None
            raise
        if previous.route != _APPLICATIONS or previous.request_digest != digest:
            raise RequestError(
                code="HFAPI012",
                status_code=409,
                message="Idempotency key conflicts with its admitted request",
            )
        return Admission(previous, created=False)

    previous = await offload_command(request, duplicate)
    if previous is not None:
        return _accepted(request, previous, server)
    reply = await _prepare(request, body.managed)
    actions: frozenset[HostAction] = frozenset({"configuration"})
    if reply.required_selectors:
        actions = frozenset({"configuration", "hub"})
    authorization = await authorize_request(request, actions)
    if authorization is None:
        raise HostAdministrationUnavailableError

    def work() -> Response:
        prepared = _checked(request, reply)
        _preview(request, body, reply)
        _unresolved(request)

        def budget(snapshot: PolicySnapshot) -> float:
            authorization.check_snapshot(snapshot)
            require_compatible_authority(prepared.config, snapshot.config)
            return snapshot.config.sync.lock_wait_seconds

        admission = request.app.state.runner.submit(
            request.state.principal,
            key,
            _APPLICATIONS,
            body.canonical_body(),
            command="config apply",
            execute=lambda snapshot, context: _execute_application(
                request, body, prepared, snapshot, context
            ),
            wait_seconds=budget,
            requires_lock=False,
            context=request.state.execution_context,
            authorize=authorization.recheck,
        )
        return _accepted(request, admission, server)

    return await offload_command(request, work)


def install_configuration_route(app: FastAPI, render: Render, server: ServerConfig) -> None:
    app.state.command_routes = frozenset(getattr(app.state, "command_routes", ())) | {_APPLICATIONS}

    @app.post(_APPLICATIONS, response_model=AcceptanceResponse, status_code=202)
    async def apply_configuration(request: Request, body: ConfigApplicationSubmission) -> Response:
        return await _apply(request, body, server)

    @app.get(_APPLICATIONS + "/{operation_id}", response_model=ReadResponse)
    async def observe_application(request: Request, operation_id: str) -> Response:
        _no_query(request)
        require_admin_capability(request.state.principal, AdminCapability.CONFIG_READ)
        key = _key(request)

        def work() -> Response:
            receipt = request.app.state.operations.lookup(request.state.principal, key)
            if receipt.route != _APPLICATIONS or receipt.operation_id != operation_id:
                _conflict("Original configuration application key and identity must match")
            outcome = _outcome(request, operation_id, receipt.request_digest)
            return render(request, ServiceResult("config outcome", outcome.model_dump(mode="json")))

        return await offload_command(request, work)

    @app.get("/api/v1/config", response_model=ReadResponse)
    async def read_configuration(request: Request) -> Response:
        _no_query(request)
        require_admin_capability(request.state.principal, AdminCapability.CONFIG_READ)
        await authorize_request(request, frozenset({"configuration"}))
        try:
            raw = await _helper(request).async_config_read()
        except Exception as error:  # noqa: BLE001 - no partial configuration or raw failures
            _failure(error)

        def work() -> Response:
            try:
                projection = ConfigRead.model_validate(raw)
            except ValidationError:
                raise HostAdministrationUnavailableError from None
            _archive(request, projection.archive_id)
            return render(request, ServiceResult("config read", projection.model_dump(mode="json")))

        return await offload_command(request, work)
