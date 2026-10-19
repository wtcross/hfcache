"""Writer-only keyed offline refresh through the existing guarded lane (INV-018)."""

from typing import TYPE_CHECKING

from fastapi import Request  # noqa: TC002 - FastAPI resolves route annotations
from starlette.responses import Response  # noqa: TC002 - FastAPI resolves return annotation

from hfcache.api.auth import Capability, require_capability
from hfcache.api.command_models import (
    AcceptanceResponse,
    CatalogRefreshSubmission,
)
from hfcache.api.commands import PREFIX, admit_command, command_service, offload_command

if TYPE_CHECKING:
    from fastapi import FastAPI

    from hfcache.server_config import ServerConfig

ROUTE = PREFIX + "/catalog/refreshes"


def install_catalog_refresh_route(app: FastAPI, server: ServerConfig) -> None:
    app.state.command_routes = frozenset(getattr(app.state, "command_routes", ())) | {ROUTE}
    app.state.writer_routes = frozenset(getattr(app.state, "writer_routes", ())) | {ROUTE}

    @app.post(ROUTE, response_model=AcceptanceResponse, status_code=202)
    async def refresh(request: Request, body: CatalogRefreshSubmission) -> Response:
        require_capability(request.state.principal, Capability.WRITE)
        intent = body.service_request()
        return await offload_command(
            request,
            lambda: admit_command(
                request,
                body,
                server,
                route=ROUTE,
                command="catalog refresh",
                requires_lock=True,
                execute=lambda snapshot, context: command_service(
                    request,
                    snapshot,
                    context,
                ).refresh_catalog(intent),
            ),
        )
