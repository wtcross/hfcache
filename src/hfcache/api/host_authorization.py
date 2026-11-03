"""Fresh Basic action authority outside API/domain locks (INV-013/014, decision150)."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import ValidationError

from hfcache.api.auth import AuthenticationMethod
from hfcache.api.command_models import DiagnosticsSubmission
from hfcache.api.intents import IntentRefusalError
from hfcache.api.operations import request_digest
from hfcache.errors import AuthorizationError, HfcacheError, HostAdministrationUnavailableError
from hfcache.host_models import HOST_ACTIONS, HostAction, HostBinding, HostProfile, HostStatus
from hfcache.host_protocol import HostProtocolError

if TYPE_CHECKING:
    from fastapi import Request

    from hfcache.api.command_models import CommandModel
    from hfcache.server_config import PolicySnapshot

_ARCHIVE: frozenset[HostAction] = frozenset({"archive"})
_HUB: frozenset[HostAction] = frozenset({"hub"})
_CONTROL: frozenset[HostAction] = frozenset({"control"})
_ROUTES = {
    "/api/v1/plans": _HUB,
    "/api/v1/syncs": _ARCHIVE,
    "/api/v1/verifications": _ARCHIVE,
    "/api/v1/repairs": _ARCHIVE,
    "/api/v1/prune-plans": _CONTROL,
    "/api/v1/recovery-plans": _CONTROL,
    "/api/v1/purge-plans": _CONTROL,
    "/api/v1/quarantine-plans": _CONTROL,
    "/api/v1/prunes": _ARCHIVE,
    "/api/v1/recoveries": _ARCHIVE,
    "/api/v1/purges": _ARCHIVE,
    "/api/v1/quarantine-cleanups": _ARCHIVE,
    "/api/v1/catalog/refreshes": _ARCHIVE,
}


class HostStatusClient(Protocol):
    def status(self) -> dict[str, Any]: ...

    async def async_status(self) -> dict[str, Any]: ...


def required_actions(route: str, body: CommandModel) -> frozenset[HostAction] | None:
    """Use registered route identity and the validated doctor discriminator only."""
    if route == "/api/v1/diagnostics":
        if not isinstance(body, DiagnosticsSubmission):
            return None
        return _HUB if body.read_only else _HUB | _ARCHIVE
    # Initialization and every future unmapped effect are denied for Basic.
    return _ROUTES.get(route)


def _status(value: object, actions: frozenset[HostAction]) -> HostStatus:
    try:
        status = HostStatus.model_validate(value)
    except ValidationError:
        raise HostAdministrationUnavailableError from None
    if status.state not in {"supported", "guarded"} or status.binding is None:
        raise HostAdministrationUnavailableError
    if any(not getattr(status.permissions, action) for action in actions):
        raise AuthorizationError
    return status


def _archive(binding: HostBinding, archive_id: str, archive_root: str) -> None:
    if binding.archive_id != archive_id or binding.archive_root != archive_root:
        raise HostAdministrationUnavailableError


@dataclass(frozen=True, slots=True)
class ActionAuthorization:
    """Retain immutable admitted scope; permission booleans are never reused."""

    actions: frozenset[HostAction]
    binding: HostBinding
    profile: HostProfile
    client: HostStatusClient = field(repr=False, compare=False)

    def check_snapshot(self, snapshot: PolicySnapshot) -> None:
        """Pure comparison: this callback may run under store/runner locks."""
        _archive(
            self.binding,
            snapshot.config.storage.archive_id,
            str(snapshot.config.storage.archive_root),
        )

    def recheck(self, snapshot: PolicySnapshot) -> None:
        """New helper exchange before execution, never inside a domain lock."""
        try:
            status = _status(self.client.status(), self.actions)
        except HostProtocolError, OSError, ValueError, TypeError:
            raise HostAdministrationUnavailableError from None
        binding = status.binding
        if (
            binding is None
            or status.profile != self.profile
            or binding.deployment_sha256 != self.binding.deployment_sha256
        ):
            raise HostAdministrationUnavailableError
        _archive(
            binding, snapshot.config.storage.archive_id, str(snapshot.config.storage.archive_root)
        )


async def authorize_request(
    request: Request, actions: frozenset[HostAction] | None, *, body: CommandModel | None = None
) -> ActionAuthorization | None:
    """Observe an exact original admission before obtaining fresh action authority."""
    from hfcache.api.commands import offload_command  # noqa: PLC0415 - shared bounded pool

    key = None
    route = request.scope["route"].path if body is not None else ""
    if body is not None:
        from hfcache.api.commands import (  # noqa: PLC0415 - shared strict header grammar
            _key,
            _no_query,
        )

        _no_query(request)
        key = _key(request)
        store = request.app.state.operations
        record, disposition = await offload_command(
            request,
            lambda: store.intent(request.state.principal, key, request.app.state.policy.archive_id),
        )
        if record is not None:
            store._same_request(record, route, request_digest(route, body.canonical_body()))  # noqa: SLF001 - shared canonical binding
            request.state.original_admission = record
            return None
        if disposition is not None:
            from hfcache.api.intents import unavailable  # noqa: PLC0415

            msg = "Original key is closed; reconcile original intent"
            raise unavailable(msg)
    try:
        if request.state.principal.authentication_method is not AuthenticationMethod.BASIC:
            return None
        if not actions or not actions <= frozenset(HOST_ACTIONS):
            raise AuthorizationError
        client = getattr(request.app.state, "host_helper", None)
        if client is None:
            raise HostAdministrationUnavailableError
        try:
            status = _status(await client.async_status(), actions)
            if (
                "archive" in actions
                and status.facts is not None
                and status.facts.archive_mount in {"nfs-ro", "local-ro"}
            ):
                message = "Archive storage is read-only; no operation was admitted"
                raise IntentRefusalError(reason="storage_read_only", message=message)
        except HostProtocolError, OSError, ValueError, TypeError:
            raise HostAdministrationUnavailableError from None
        binding, profile = status.binding, status.profile
        if binding is None or profile is None:
            raise HostAdministrationUnavailableError
        policy = request.app.state.policy
        _archive(binding, policy.archive_id, str(policy.root))
        return ActionAuthorization(actions, binding, profile, client)
    except HfcacheError as error:
        if key is not None and body is not None:
            reason = (
                "permission_denied"
                if isinstance(error, AuthorizationError)
                else error.reason
                if isinstance(error, IntentRefusalError)
                else "executor_unavailable"
            )
            record, _ = await offload_command(
                request,
                lambda: request.app.state.operations.refuse(
                    request.state.principal,
                    key,
                    route,
                    body.canonical_body(),
                    request.app.state.policy.archive_id,
                    reason,
                ),
            )
            if record is not None:
                request.state.original_admission = record
                return None
            error.headers = MappingProxyType({"Hfcache-Intent": "closed"})
        raise


def require_admission(
    request: Request,
    route: str,
    body: CommandModel,
    authorization: ActionAuthorization | None,
) -> None:
    """An omitted hook on a future Basic route cannot silently grant authority."""
    if getattr(request.state, "original_admission", None) is not None:
        return
    if request.state.principal.authentication_method is AuthenticationMethod.BASIC and (
        authorization is None or authorization.actions != required_actions(route, body)
    ):
        raise AuthorizationError
