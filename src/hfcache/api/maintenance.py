"""Explicit keyed preview/apply adapters preserve domain safety (decision 117)."""

from typing import TYPE_CHECKING

from fastapi import Request  # noqa: TC002 - FastAPI resolves endpoint annotations at runtime
from starlette.responses import Response  # noqa: TC002 - FastAPI resolves return annotations

from hfcache.api.auth import Capability, require_capability
from hfcache.api.command_models import AcceptanceResponse
from hfcache.api.commands import PREFIX, admit_command, command_service, offload_command
from hfcache.api.maintenance_models import (
    InitializationSubmission,  # noqa: TC001 - FastAPI resolves DTOs at runtime
    PruneSubmission,  # noqa: TC001 - FastAPI resolves DTOs at runtime
    PurgeSubmission,  # noqa: TC001 - FastAPI resolves DTOs at runtime
    QuarantineSubmission,  # noqa: TC001 - FastAPI resolves DTOs at runtime
    RecoverySubmission,  # noqa: TC001 - FastAPI resolves DTOs at runtime
    RepairSubmission,  # noqa: TC001 - FastAPI resolves DTOs at runtime
)
from hfcache.errors import AuthorizationError
from hfcache.services.commands import InitializationRequest, MaintenanceRequest, QuarantineRequest

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI

    from hfcache.api.command_models import CommandModel
    from hfcache.server_config import ServerConfig
    from hfcache.services.commands import CommandServices
    from hfcache.services.context import ServiceResult

PREVIEW_ROUTES = frozenset(
    PREFIX + suffix
    for suffix in ("/prune-plans", "/purge-plans", "/recovery-plans", "/quarantine-plans")
)
WRITER_ROUTES = frozenset(
    PREFIX + suffix
    for suffix in (
        "/prunes",
        "/purges",
        "/recoveries",
        "/quarantine-cleanups",
        "/repairs",
        "/archive/initializations",
    )
)
COMMAND_ROUTES = PREVIEW_ROUTES | WRITER_ROUTES


def install_maintenance_routes(app: FastAPI, server: ServerConfig) -> None:
    """Register fixed URLs; a preview document is never deletion authority."""
    app.state.command_routes = frozenset(getattr(app.state, "command_routes", ())) | COMMAND_ROUTES
    app.state.writer_routes = frozenset(getattr(app.state, "writer_routes", ())) | WRITER_ROUTES

    async def job(
        request: Request,
        body: CommandModel,
        *,
        command: str,
        mutates: bool,
        execute: Callable[[CommandServices], ServiceResult],
    ) -> Response:
        require_capability(
            request.state.principal, Capability.WRITE if mutates else Capability.READ
        )
        return await offload_command(
            request,
            lambda: admit_command(
                request,
                body,
                server,
                route=request.scope["route"].path,
                command=command,
                requires_lock=mutates,
                execute=lambda snapshot, context: execute(
                    command_service(request, snapshot, context)
                ),
            ),
        )

    @app.post(PREFIX + "/prune-plans", response_model=AcceptanceResponse, status_code=202)
    async def preview_prune(request: Request, body: PruneSubmission) -> Response:
        return await job(
            request,
            body,
            command="prune --dry-run",
            mutates=False,
            execute=lambda service: service.prune(MaintenanceRequest(body.selectors, dry_run=True)),
        )

    @app.post(PREFIX + "/prunes", response_model=AcceptanceResponse, status_code=202)
    async def apply_prune(request: Request, body: PruneSubmission) -> Response:
        return await job(
            request,
            body,
            command="prune --apply",
            mutates=True,
            execute=lambda service: service.prune(MaintenanceRequest(body.selectors, apply=True)),
        )

    @app.post(PREFIX + "/purge-plans", response_model=AcceptanceResponse, status_code=202)
    async def preview_purge(request: Request, body: PurgeSubmission) -> Response:
        return await job(
            request,
            body,
            command="purge --dry-run",
            mutates=False,
            execute=lambda service: service.purge(
                MaintenanceRequest(body.selectors, dry_run=True, all_unmanaged=body.all_unmanaged)
            ),
        )

    @app.post(PREFIX + "/purges", response_model=AcceptanceResponse, status_code=202)
    async def apply_purge(request: Request, body: PurgeSubmission) -> Response:
        return await job(
            request,
            body,
            command="purge --apply",
            mutates=True,
            execute=lambda service: service.purge(
                MaintenanceRequest(body.selectors, apply=True, all_unmanaged=body.all_unmanaged)
            ),
        )

    @app.post(PREFIX + "/recovery-plans", response_model=AcceptanceResponse, status_code=202)
    async def preview_recovery(request: Request, body: RecoverySubmission) -> Response:
        return await job(
            request,
            body,
            command="recover --dry-run",
            mutates=False,
            execute=lambda service: service.recover(MaintenanceRequest(dry_run=True)),
        )

    @app.post(PREFIX + "/recoveries", response_model=AcceptanceResponse, status_code=202)
    async def apply_recovery(request: Request, body: RecoverySubmission) -> Response:
        return await job(
            request,
            body,
            command="recover --apply",
            mutates=True,
            execute=lambda service: service.recover(MaintenanceRequest(apply=True)),
        )

    @app.post(PREFIX + "/quarantine-plans", response_model=AcceptanceResponse, status_code=202)
    async def preview_quarantine(request: Request, body: QuarantineSubmission) -> Response:
        return await job(
            request,
            body,
            command="quarantine --dry-run",
            mutates=False,
            execute=lambda service: service.quarantine(
                QuarantineRequest(body.transaction_ids, dry_run=True)
            ),
        )

    @app.post(PREFIX + "/quarantine-cleanups", response_model=AcceptanceResponse, status_code=202)
    async def apply_quarantine(request: Request, body: QuarantineSubmission) -> Response:
        return await job(
            request,
            body,
            command="quarantine --apply",
            mutates=True,
            execute=lambda service: service.quarantine(
                QuarantineRequest(body.transaction_ids, apply=True)
            ),
        )

    @app.post(PREFIX + "/repairs", response_model=AcceptanceResponse, status_code=202)
    async def repair(request: Request, body: RepairSubmission) -> Response:
        return await job(
            request,
            body,
            command="repair",
            mutates=True,
            execute=lambda service: service.repair(body.service_request()),
        )

    @app.post(
        PREFIX + "/archive/initializations", response_model=AcceptanceResponse, status_code=202
    )
    async def initialize(request: Request, body: InitializationSubmission) -> Response:
        require_capability(request.state.principal, Capability.WRITE)
        if not server.maintenance_enabled:
            raise AuthorizationError
        return await job(
            request,
            body,
            command="archive init",
            mutates=True,
            execute=lambda service: service.initialize_archive(
                InitializationRequest(body.archive_root, body.archive_id, confirm=True)
            ),
        )
