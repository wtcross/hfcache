"""Bounded administrative observation, separate from archive reads (decision150)."""

from typing import TYPE_CHECKING, Any, Protocol

from fastapi import Request  # noqa: TC002 - runtime endpoint annotation
from pydantic import ValidationError
from starlette.responses import (
    Response,  # noqa: TC002 - FastAPI resolves endpoint return annotations
)

from hfcache.api.auth import AdminCapability, require_admin_capability
from hfcache.api.models import ReadResponse
from hfcache.host_models import HostReason, HostStatus, unavailable_host_status
from hfcache.host_protocol import HostProtocolError
from hfcache.services.context import ServiceResult

if TYPE_CHECKING:
    from fastapi import FastAPI

    from hfcache.api.commands import Render
    from hfcache.server_config import ServerConfig


class HostHelper(Protocol):
    def status(self) -> dict[str, Any]: ...
    async def async_status(self) -> dict[str, Any]: ...
    def close(self, *, timeout: float = 24) -> bool: ...


class UnavailableHostHelper:
    """No socket, filesystem, archive or worker access when explicitly disabled."""

    def __init__(self, reason: HostReason = "helper-disabled") -> None:
        self.reason = reason

    def status(self) -> dict[str, Any]:
        return unavailable_host_status(self.reason).model_dump(mode="json")

    async def async_status(self) -> dict[str, Any]:
        return self.status()

    def close(self, *, timeout: float = 24) -> bool:  # noqa: ARG002 - common owned-client lifecycle
        return True


def open_host_helper(server: ServerConfig) -> HostHelper:
    """Pin the protected endpoint only at explicit enabled startup; never fallback."""
    settings = server.host_helper
    if not settings.enabled:
        return UnavailableHostHelper()
    # Optional startup-only fixed endpoint work; base/server imports create no IPC.
    from hfcache.host_helper_client import EndpointBinding, HostHelperClient  # noqa: PLC0415

    if settings.profile is None or settings.api_host_gid is None:
        return UnavailableHostHelper("helper-refused")
    try:
        binding = EndpointBinding.from_startup(
            profile=settings.profile,
            deployment_sha256=settings.deployment_sha256,
            api_host_gid=settings.api_host_gid,
        )
        return HostHelperClient(binding, deployment_sha256=binding.deployment_sha256)
    except HostProtocolError, OSError, ValueError:
        return UnavailableHostHelper("helper-refused")


async def read_host_status(request: Request) -> HostStatus:
    """An unknown helper cannot manufacture a crash, healthy state or permission."""
    helper: HostHelper = request.app.state.host_helper
    try:
        status = HostStatus.model_validate(await helper.async_status())
    except HostProtocolError as error:
        reason: HostReason = "helper-refused"
        if error.reason == "timeout":
            reason = "helper-timeout"
        elif error.reason == "busy":
            reason = "helper-busy"
        return unavailable_host_status(reason)
    except ValidationError:
        return unavailable_host_status("helper-refused")
    except Exception:  # noqa: BLE001 - every unknown helper boundary failure denies; never expose text
        return unavailable_host_status()
    binding = status.binding
    policy = request.app.state.policy
    if binding is not None and (
        binding.archive_id != policy.archive_id or binding.archive_root != str(policy.root)
    ):
        return unavailable_host_status("deployment-unverified")
    return status


def install_host_status_route(app: FastAPI, render: Render) -> None:
    @app.get("/api/v1/host/status", response_model=ReadResponse)
    async def host_status(request: Request) -> Response:
        require_admin_capability(request.state.principal, AdminCapability.HOST_READ)
        if request.query_params:
            from hfcache.errors import RequestError  # noqa: PLC0415 - safe query refusal

            raise RequestError
        status = await read_host_status(request)
        return render(request, ServiceResult("host status", status.model_dump(mode="json")))
