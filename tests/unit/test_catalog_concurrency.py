"""V49: catalog MCP/REST work shares bounded leases after observer cancellation."""

import asyncio
from threading import Event

import httpx2
import pytest
from fastmcp.utilities.asgi_transport import StreamingASGITransport

from hfcache.api.app import create_app
from hfcache.catalog_query_models import CatalogQuery
from hfcache.services.catalog_queries import CatalogQueries
from tests.unit.test_mcp_catalog import archive as archive  # noqa: PLC0414 - fixture
from tests.unit.test_mcp_catalog import catalog as catalog  # noqa: PLC0414 - fixture
from tests.unit.test_mcp_concurrency import settled
from tests.unit.test_mcp_tools import MCP, snapshot
from tests.unit.test_server_bootstrap import (
    TOKEN,
    isolate_logging,  # noqa: F401 - fixture
)
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture


@pytest.mark.parametrize("cancel", [False, True])
def test_actual_catalog_worker_retains_shared_capacity_until_completion(  # noqa: PLR0915 - one lease lifecycle
    catalog, monkeypatch, tmp_path, cancel
):
    entered, release = Event(), Event()
    original = CatalogQueries.search

    def blocked(self, query=CatalogQuery(), **kwargs):  # noqa: B008 - immutable intent
        entered.set()
        assert release.wait(10)
        return original(self, query, **kwargs)

    monkeypatch.setattr(CatalogQueries, "search", blocked)
    server = catalog.server.model_copy(
        update={
            "limits": catalog.server.limits.model_copy(
                update={"metadata_workers": 1, "metadata_queue": 1}
            )
        }
    )
    app = create_app(server, instance_lock_path=tmp_path / "catalog-worker.lock")
    mcp_headers = {
        "authorization": "Bearer " + MCP,
        "accept": "application/json, text/event-stream",
        "mcp-protocol-version": "2025-11-25",
    }
    rest_headers = {"authorization": "Bearer " + TOKEN}
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "search_models", "arguments": {}},
    }

    async def check():
        async with (
            app.router.lifespan_context(app),
            httpx2.AsyncClient(
                transport=StreamingASGITransport(app),
                base_url="http://localhost",
                trust_env=False,
            ) as client,
        ):
            before = snapshot(catalog.queries.layout.root, server.state_directory)
            active = asyncio.create_task(client.post("/mcp/", headers=mcp_headers, json=request))
            queued = None
            try:
                assert await asyncio.to_thread(entered.wait, 5)
                if cancel:
                    active.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await active
                assert app.state.pool.inflight == 1
                assert app.state.mcp_transport.inflight == 1
                queued = asyncio.create_task(
                    client.get(
                        "/api/v1/catalog/search?type=dataset",
                        headers=rest_headers,
                    )
                )
                for _ in range(1000):
                    if app.state.pool.inflight == 2:
                        break
                    await asyncio.sleep(0)
                assert app.state.pool.inflight == 2
                refused = await client.post("/mcp/", headers=mcp_headers, json=request | {"id": 2})
                assert refused.status_code == 200
                assert refused.json()["result"]["isError"] is True
                assert "HFAPI009" in refused.text
                version = await asyncio.wait_for(
                    client.get("/api/v1/version", headers=rest_headers), 2
                )
                assert version.status_code == 200
                assert snapshot(catalog.queries.layout.root, server.state_directory) == before
            finally:
                release.set()
                if not cancel:
                    response = await active
                    assert (
                        response.json()["result"]["structuredContent"]["envelope"]["exit_code"] == 0
                    )
                if queued is not None:
                    response = await queued
                    assert response.status_code == 200
            await settled(app)
            recovered = await client.post("/mcp/", headers=mcp_headers, json=request | {"id": 3})
            assert recovered.json()["result"]["structuredContent"]["envelope"]["exit_code"] == 0
            await settled(app)
            assert app.state.pool.inflight == 0
            assert app.state.mcp_transport.inflight == 0
            assert app.state.operations.list() == ()
            assert snapshot(catalog.queries.layout.root, server.state_directory) == before

    asyncio.run(check())
