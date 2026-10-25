"""Fresh Basic action authority outside API/domain locks (INV-013/014, decision150)."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import ValidationError

from hfcache.api.auth import AuthenticationMethod
from hfcache.api.command_models import DiagnosticsSubmission
from hfcache.errors import AuthorizationError, HostAdministrationUnavailableError
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
    request: Request, actions: frozenset[HostAction] | None
) -> ActionAuthorization | None:
    """Freshly authorize every Basic POST, including exact duplicate keys."""
    if request.state.principal.authentication_method is not AuthenticationMethod.BASIC:
        return None
    if not actions or not actions <= frozenset(HOST_ACTIONS):
        raise AuthorizationError
    client = getattr(request.app.state, "host_helper", None)
    if client is None:
        raise HostAdministrationUnavailableError
    try:
        status = _status(await client.async_status(), actions)
    except HostProtocolError, OSError, ValueError, TypeError:
        raise HostAdministrationUnavailableError from None
    binding, profile = status.binding, status.profile
    if binding is None or profile is None:
        raise HostAdministrationUnavailableError
    # Exact duplicates bypass the store snapshot callback, so compare the
    # lifespan's immutable archive authority before metadata offload as well.
    policy = request.app.state.policy
    _archive(binding, policy.archive_id, str(policy.root))
    return ActionAuthorization(actions, binding, profile, client)


def require_admission(
    request: Request,
    route: str,
    body: CommandModel,
    authorization: ActionAuthorization | None,
) -> None:
    """An omitted hook on a future Basic route cannot silently grant authority."""
    if request.state.principal.authentication_method is AuthenticationMethod.BASIC and (
        authorization is None or authorization.actions != required_actions(route, body)
    ):
        raise AuthorizationError
