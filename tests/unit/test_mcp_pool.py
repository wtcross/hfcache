"""Mounted MCP metadata shares bounded worker ownership with REST reads."""

import asyncio
from threading import Event

import httpx2
import pytest
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import MiddlewareContext
from fastmcp.utilities.asgi_transport import StreamingASGITransport
from mcp.types import CallToolRequestParams

from hfcache.api.app import create_app
from hfcache.mcp import SafeToolErrors
from hfcache.services.context import ServiceResult
from hfcache.services.queries import LocalQueries
from tests.unit.test_mcp_mount import MCP, WRITER
from tests.unit.test_mcp_mount import configured as configured  # noqa: PLC0414 - pytest fixture


@pytest.mark.parametrize("name", ["sync", "a" * 64 + "_get_archive_status"])
def test_unapproved_tool_spelling_never_reaches_sdk_lookup_or_tracing(name):
    context = MiddlewareContext(
        message=CallToolRequestParams(name=name, arguments={}),
        method="tools/call",
        type="request",
        source="client",
    )

    async def lookup(context):
        del context
        pytest.fail("unapproved names cannot reach SDK lookup/tracing")

    async def run():
        with pytest.raises(ToolError, match=r"^HFAPI007: unknown metadata tool$"):
            await SafeToolErrors().on_call_tool(context, lookup)

    asyncio.run(run())


def test_blocked_estimator_uses_shared_pool_without_blocking_metadata_or_leaking_slots(
    configured, tmp_path
):
    entered, release = Event(), Event()

    class BlockingQueries(LocalQueries):
        def estimate_verification(self):
            entered.set()
            assert release.wait(10)
            return ServiceResult("verify --estimate", {"estimate": {"bytes": 0}})

    settings = configured.model_copy(
        update={
            "limits": configured.limits.model_copy(
                update={"metadata_workers": 1, "metadata_queue": 1}
            )
        }
    )
    app = create_app(
        settings, instance_lock_path=tmp_path / "instance.lock", query_factory=BlockingQueries
    )
    mcp_headers = {
        "authorization": "Bearer " + MCP,
        "accept": "application/json, text/event-stream",
        "mcp-protocol-version": "2025-11-25",
    }
    rest_headers = {"authorization": "Bearer " + WRITER}
    rpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "estimate_verification", "arguments": {}},
    }

    async def run():
        async with (
            app.router.lifespan_context(app),
            httpx2.AsyncClient(
                transport=StreamingASGITransport(app),
                base_url="http://localhost",
                trust_env=False,
                follow_redirects=False,
            ) as client,
        ):
            active = asyncio.create_task(client.post("/mcp/", headers=mcp_headers, json=rpc))
            queued = None
            try:
                assert await asyncio.to_thread(entered.wait, 5)
                queued = asyncio.create_task(client.get("/api/v1/status", headers=rest_headers))
                for _ in range(1000):
                    if app.state.pool.inflight == 2:
                        break
                    await asyncio.sleep(0)
                assert app.state.pool.inflight == 2
                refused = await client.post("/mcp/", headers=mcp_headers, json=rpc)
                assert refused.status_code == 200
                assert refused.json()["result"]["isError"] is True
                assert "HFAPI009" in refused.text
                version = await asyncio.wait_for(
                    client.get("/api/v1/version", headers=rest_headers), 2
                )
                assert version.status_code == 200
            finally:
                release.set()
                result = await active
                if queued is not None:
                    await queued
            assert result.status_code == 200
            assert result.json()["result"]["structuredContent"]["envelope"]["exit_code"] == 0
            assert app.state.pool.inflight == 0
            assert app.state.mcp_transport.inflight == 0
            assert app.state.operations.list() == ()
            assert not (tmp_path / "archive").exists()

    asyncio.run(run())
