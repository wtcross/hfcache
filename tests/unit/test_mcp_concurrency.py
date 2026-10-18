"""Real mounted reads retain identity and ownership beside accepted REST work."""

import asyncio
from threading import Event

import httpx2
import pytest
from fastmcp.utilities.asgi_transport import StreamingASGITransport

from hfcache import locking
from hfcache.api.app import create_app
from hfcache.api.lifecycle import instance_lock
from hfcache.errors import SafetyError
from hfcache.hub import HubClient
from hfcache.logging import current_correlation
from hfcache.server_config import validate_server_config_mapping
from hfcache.services import commands
from hfcache.services.context import ServiceResult
from hfcache.services.queries import LocalQueries
from tests.api_cli import private_verifier
from tests.unit.test_api_commands import configured as archive_base  # noqa: F401 - fixture
from tests.unit.test_api_commands import result, submit
from tests.unit.test_mcp_mount import MCP, WRITER
from tests.unit.test_mcp_mount import configured as read_base  # noqa: F401 - fixture
from tests.unit.test_mcp_tools import snapshot
from tests.unit.test_synchronize import MODEL

MCP_HEADERS = {
    "authorization": "Bearer " + MCP,
    "accept": "application/json, text/event-stream",
    "mcp-protocol-version": "2025-11-25",
    "x-request-id": "f" * 32,
}
READ_HEADERS = {"authorization": "Bearer " + WRITER}


def rpc(name, identifier=1):
    return {
        "jsonrpc": "2.0",
        "id": identifier,
        "method": "tools/call",
        "params": {"name": name, "arguments": {}},
    }


def reader(app):
    return httpx2.AsyncClient(
        transport=StreamingASGITransport(app),
        base_url="http://testserver",
        trust_env=False,
        follow_redirects=False,
    )


def frame(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["result"].get("isError", False) is False, payload
    output = payload["result"]["structuredContent"]
    assert output["request_id"] == response.headers["x-request-id"]
    assert MCP not in response.text
    return output


async def settled(app):
    """The supported streaming bridge may deliver body bytes before ASGI finally."""

    async def idle():
        while app.state.pool.inflight or app.state.mcp_transport.inflight:
            await asyncio.sleep(0)

    await asyncio.wait_for(idle(), 2)


@pytest.fixture
def read_configured(request):
    return request.getfixturevalue("read_base")


@pytest.fixture
def mixed(request, tmp_path):
    server, layout, hub, lock = request.getfixturevalue("archive_base")
    source = tmp_path / "mcp-reader"
    source.write_text(MCP)
    source.chmod(0o600)
    configured = validate_server_config_mapping(
        server.model_dump(mode="json")
        | {
            "mcp_enabled": True,
            "credentials": server.credentials.model_dump(mode="json")
            | {"mcp_reader": {"file": str(source)}},
        }
    )
    return configured, layout, hub, lock


@pytest.mark.parametrize("mode", ["sync", "verification"])
def test_parallel_mcp_reads_during_rest_sync_and_verification_keep_ids_and_authority(  # noqa: PLR0915 - one attribution/identity scenario
    mixed, monkeypatch, mode
):
    server, layout, hub, lock = mixed
    entered, release = Event(), Event()
    domain_contexts, query_contexts, token_calls, verification_calls = [], [], [], []
    original_download = HubClient.download
    original_verify = commands.verify_targets
    original_token = commands.resolve_token
    original_estimate = LocalQueries.estimate_verification

    def resolve(*args, **kwargs):
        token_calls.append(True)
        return original_token(*args, **kwargs)

    def download(self, *args, **kwargs):
        if mode == "sync":
            domain_contexts.append(current_correlation())
            entered.set()
            assert release.wait(10)
        return original_download(self, *args, **kwargs)

    def verify(*args, **kwargs):
        verification_calls.append(True)
        domain_contexts.append(current_correlation())
        entered.set()
        assert release.wait(10)
        return original_verify(*args, **kwargs)

    def estimate(self):
        query_contexts.append(current_correlation())
        return original_estimate(self)

    monkeypatch.setattr(commands, "resolve_token", resolve)
    monkeypatch.setattr(commands, "verify_targets", verify)
    monkeypatch.setattr(HubClient, "download", download)
    monkeypatch.setattr(LocalQueries, "estimate_verification", estimate)

    with private_verifier(server) as verifier:
        app = create_app(server, instance_lock_path=lock, verification_executor=verifier)

        async def run():
            async with app.router.lifespan_context(app), reader(app) as client:
                if mode == "verification":
                    seed = await submit(
                        client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, "seed"
                    )
                    assert (await result(client, seed))["exit_code"] == 0
                path = "/api/v1/syncs" if mode == "sync" else "/api/v1/verifications"
                body = {"selectors": [MODEL.selector]} if mode == "sync" else {"mode": "full"}
                accepted = await submit(client, path, body, "long-" + mode)
                try:
                    assert await asyncio.to_thread(entered.wait, 5)

                    with (
                        pytest.raises(SafetyError),
                        locking.exclusive_lock(
                            locking.lock_path(), command="proof", wait_seconds=0
                        ),
                    ):
                        pytest.fail("active REST work must retain the common archive lock")
                    before = len(hub.downloads), len(token_calls), len(verification_calls)
                    operations = {record.operation_id for record in app.state.operations.list()}
                    roots = layout.root, server.state_directory, verifier.path.parent / "state"
                    original = snapshot(*roots)
                    calls = [
                        "get_archive_status",
                        "list_repositories",
                        "list_revisions",
                        "list_run_reports",
                        "estimate_verification",
                    ]
                    responses = await asyncio.wait_for(
                        asyncio.gather(
                            *(
                                client.post("/mcp/", headers=MCP_HEADERS, json=rpc(name, index + 1))
                                for index, name in enumerate(calls)
                            )
                        ),
                        3,
                    )
                    frames = [frame(response) for response in responses]
                    assert snapshot(*roots) == original
                    identifiers = {item["request_id"] for item in frames}
                    run_ids = {item["envelope"]["run_id"] for item in frames}
                    operation_id = accepted["operation"]["operation_id"]
                    assert len(identifiers) == len(calls)
                    assert len(run_ids) == len(calls)
                    assert identifiers.isdisjoint(run_ids | {operation_id, "f" * 32})
                    assert run_ids.isdisjoint({operation_id})
                    assert len({item["config_fingerprint"] for item in frames}) == 1
                    confidence = frames[0]["envelope"]["data"]["archive"]["verification"]
                    assert confidence == {
                        "degraded": False,
                        "last_full_verification": None,
                        "outstanding_failures": 0,
                    }
                    assert {
                        item["verification_state"]
                        for item in frames[2]["envelope"]["data"]["revisions"]
                    } <= {"unverified"}
                    assert (len(hub.downloads), len(token_calls), len(verification_calls)) == before
                    assert {
                        record.operation_id for record in app.state.operations.list()
                    } == operations
                    assert query_contexts[-1].request_id == frames[-1]["request_id"]
                    assert query_contexts[-1].run_id == frames[-1]["envelope"]["run_id"]
                    assert query_contexts[-1].operation_id is None
                    assert domain_contexts[0].operation_id == operation_id
                    assert domain_contexts[0].request_id not in identifiers
                    assert domain_contexts[0].run_id not in run_ids
                    assert current_correlation().request_id is None
                finally:
                    release.set()
                completed = await result(client, accepted)
                assert completed["exit_code"] == 0
                assert completed["run_id"] == domain_contexts[0].run_id
                assert len(hub.downloads) == 1
                await settled(app)
                assert app.state.pool.inflight == app.state.mcp_transport.inflight == 0
                assert list(layout.runs.glob("*.json"))

        asyncio.run(run())


def blocking_application(configured, tmp_path):
    entered, release = Event(), Event()
    contexts = []

    class Blocking(LocalQueries):
        def estimate_verification(self):
            contexts.append(current_correlation())
            entered.set()
            assert release.wait(10)
            return ServiceResult("verify --estimate", {"estimate": {"bytes": 0}})

    server = configured.model_copy(
        update={
            "listener": configured.listener.model_copy(update={"allowed_hosts": ("testserver",)}),
            "limits": configured.limits.model_copy(
                update={"metadata_workers": 1, "metadata_queue": 1}
            ),
        }
    )
    lock = tmp_path / "instance.lock"
    return (
        create_app(server, instance_lock_path=lock, query_factory=Blocking),
        lock,
        entered,
        release,
        contexts,
    )


def test_cancelled_mcp_observer_keeps_metadata_lease_until_worker_finishes(
    read_configured, tmp_path
):
    app, _, entered, release, contexts = blocking_application(read_configured, tmp_path)

    async def run():
        async with app.router.lifespan_context(app), reader(app) as client:
            original = snapshot(tmp_path / "archive", read_configured.state_directory)
            active = asyncio.create_task(
                client.post("/mcp/", headers=MCP_HEADERS, json=rpc("estimate_verification"))
            )
            try:
                assert await asyncio.to_thread(entered.wait, 5)
                active.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await active
                assert app.state.pool.inflight == 1
                # The streaming transport detaches this observer while the
                # server still owns its finite request and underlying worker.
                assert app.state.mcp_transport.inflight == 1
                assert not app.state.pool.closed
                version = await asyncio.wait_for(
                    client.get("/api/v1/version", headers=READ_HEADERS), 2
                )
                assert version.status_code == 200
                assert snapshot(tmp_path / "archive", read_configured.state_directory) == original
            finally:
                release.set()
            recovered = frame(
                await client.post(
                    "/mcp/", headers=MCP_HEADERS, json=rpc("estimate_verification", 2)
                )
            )
            assert recovered["request_id"] != contexts[0].request_id
            assert recovered["envelope"]["run_id"] != contexts[0].run_id
            assert contexts[-1].request_id == recovered["request_id"]
            raw = await asyncio.wrap_future(app.state.pool.executor.submit(current_correlation))
            assert raw.request_id is raw.operation_id is raw.run_id is None
            await settled(app)
            assert app.state.pool.inflight == app.state.mcp_transport.inflight == 0
            assert app.state.operations.list() == ()
            assert not (tmp_path / "archive").exists()
            assert snapshot(tmp_path / "archive", read_configured.state_directory) == original

    asyncio.run(run())


def test_shutdown_after_cancelled_mcp_read_waits_for_worker_and_instance_ownership(
    read_configured, tmp_path
):
    app, lock, entered, release, _ = blocking_application(read_configured, tmp_path)

    async def run():
        ready, stop, stopping = asyncio.Event(), asyncio.Event(), asyncio.Event()

        async def owner():
            # AnyIO lifespan cancellation scopes enter/exit on their owner task.
            async with app.router.lifespan_context(app):
                ready.set()
                await stop.wait()
                stopping.set()

        closing = asyncio.create_task(owner())
        await ready.wait()
        original = snapshot(tmp_path / "archive", read_configured.state_directory)
        try:
            async with reader(app) as client:
                active = asyncio.create_task(
                    client.post("/mcp/", headers=MCP_HEADERS, json=rpc("estimate_verification"))
                )
                assert await asyncio.to_thread(entered.wait, 5)
                active.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await active
                stop.set()
                await stopping.wait()
                # MCP closes before REST's pool; either layer may still be
                # joining this same live worker at this point.
                assert not closing.done()
                assert app.state.pool.inflight == 1
                assert app.state.credentials is not None
                assert app.state.operations.list() == ()
                with pytest.raises(SafetyError), instance_lock(lock):
                    pytest.fail("shutdown must retain daemon ownership while a read worker lives")
                assert lock.exists()
                assert snapshot(tmp_path / "archive", read_configured.state_directory) == original
                release.set()
                await closing
        finally:
            release.set()
            stop.set()
            await closing
        assert app.state.credentials is None
        assert app.state.pool.inflight == app.state.mcp_transport.inflight == 0
        with instance_lock(lock):
            pass
        assert not (tmp_path / "archive").exists()
        assert snapshot(tmp_path / "archive", read_configured.state_directory) == original

    asyncio.run(run())
