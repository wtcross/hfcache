"""Non-installing managed configuration reads/assessments (decision153, INV-001)."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NoReturn, Protocol, cast

from fastapi import Request  # noqa: TC002 - FastAPI resolves route annotations
from pydantic import ValidationError
from starlette.responses import Response  # noqa: TC002 - FastAPI resolves route annotations

from hfcache.api.auth import AdminCapability, require_admin_capability
from hfcache.api.commands import _accepted, _key, _no_query, offload_command
from hfcache.api.host_authorization import authorize_request
from hfcache.api.models import ReadResponse
from hfcache.config_models import (
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


def install_configuration_route(app: FastAPI, render: Render) -> None:
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
