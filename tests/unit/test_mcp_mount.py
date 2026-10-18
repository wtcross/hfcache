"""Production verifier, composed ownership and finite MCP transport bounds."""

import asyncio
import builtins
import importlib
import json
import logging
from contextlib import asynccontextmanager

import pytest

from hfcache.api.app import create_app
from hfcache.api.auth import Capability, load_credentials
from hfcache.api.lifecycle import instance_lock
from hfcache.errors import ConfigurationError, RequestError, SafetyError
from hfcache.logging import reset
from hfcache.mcp import (
    BoundedMCPTransport,
    OpaqueTokenVerifier,
    create_mcp_app,
    mcp_diagnostics,
)
from hfcache.redaction import register_secret
from hfcache.server_config import validate_server_config_mapping
from tests.fixtures.examples import ARCHIVE_ID

WRITER = "mount-writer-" + "W" * 40
READER = "mount-reader-" + "R" * 40
MCP = "mount-mcp-" + "M" * 40


@pytest.fixture
def configured(tmp_path):
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{ARCHIVE_ID}"\n[hub]\ntoken_mode="disabled"\n'
    )
    sources = {}
    for name, token in (("writer", WRITER), ("reader", READER), ("mcp_reader", MCP)):
        path = tmp_path / name
        path.write_text(token)
        path.chmod(0o600)
        sources[name] = {"file": str(path)}
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(policy),
            "state_directory": str(tmp_path / "state"),
            "credentials": sources,
            "mcp_enabled": True,
        }
    )
    reset()
    yield server
    reset()


def test_production_verifier_accepts_only_active_mcp_class_with_stable_nonsecret_identity(
    configured,
):
    registry = load_credentials(configured)
    verifier = OpaqueTokenVerifier(lambda: registry)

    async def verify():
        token = await verifier.verify_token(MCP)
        assert token is not None
        assert token.client_id == "hfcache-mcp-reader"
        assert token.subject == "mcp-reader"
        assert token.claims == {"iss": "urn:hfcache:mcp"}
        assert token.scopes == [Capability.MCP_READ.value]
        assert token.expires_at is None
        for invalid in (WRITER, READER, "unknown", "", MCP + " " + MCP):
            assert await verifier.verify_token(invalid) is None
        assert await OpaqueTokenVerifier(lambda: None).verify_token(MCP) is None

    asyncio.run(verify())
    assert verifier.get_routes(mcp_path="/mcp/") == []


def test_disabled_mcp_source_is_inert_but_active_classes_must_be_distinct(configured):
    sources = configured.credentials.model_dump(mode="json")
    sources["mcp_reader"] = sources["writer"]
    disabled = validate_server_config_mapping(
        configured.model_dump(mode="json") | {"mcp_enabled": False, "credentials": sources}
    )
    assert load_credentials(disabled).authenticate("Bearer " + WRITER)
    enabled = disabled.model_copy(update={"mcp_enabled": True})
    with pytest.raises(ConfigurationError) as failure:
        load_credentials(enabled)
    assert failure.value.problems[0].code == "HFAPI004"


def test_optional_dependency_failure_is_classified_without_original_import_text(
    configured, monkeypatch
):
    original = builtins.__import__

    def unavailable(name, *args, **kwargs):
        if name == "hfcache.mcp":
            message = "untrusted import failure " + MCP
            raise ImportError(message)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", unavailable)
    with pytest.raises(ConfigurationError) as failure:
        create_app(configured)
    assert failure.value.problems[0].code == "HFCFG005"
    assert MCP not in str(failure.value)


@pytest.mark.parametrize("startup_failure", [False, True])
def test_composed_lifespan_enters_rest_first_exits_mcp_first_and_unwinds_failure(
    configured, tmp_path, startup_failure
):
    lock = tmp_path / "instance.lock"
    app = create_app(configured, instance_lock_path=lock)
    events = []

    @asynccontextmanager
    async def child(_):
        events.append("mcp.enter")
        assert app.state.credentials is not None
        assert not app.state.pool.closed
        assert app.state.operations.list() == ()
        if startup_failure:
            message = "injected MCP startup failure"
            raise RuntimeError(message)
        try:
            yield
        finally:
            assert not app.state.pool.closed
            assert app.state.credentials is not None
            events.append("mcp.exit")

    app.state.mcp_app.router.lifespan_context = child

    async def run():
        if startup_failure:
            with pytest.raises(RuntimeError, match="injected MCP startup failure"):
                async with app.router.lifespan_context(app):
                    pytest.fail("failed startup cannot yield")
        else:
            async with app.router.lifespan_context(app):
                events.append("application.ready")
        assert app.state.pool.closed
        assert app.state.credentials is None
        with instance_lock(lock):
            pass

    asyncio.run(run())
    assert events == (
        ["mcp.enter"] if startup_failure else ["mcp.enter", "application.ready", "mcp.exit"]
    )


def test_explicit_server_policy_overrides_ambient_fastmcp_defaults(monkeypatch):
    fastmcp = importlib.import_module("fastmcp")
    monkeypatch.setattr(fastmcp.settings, "debug", True)
    monkeypatch.setattr(fastmcp.settings, "mask_error_details", False)
    monkeypatch.setattr(fastmcp.settings, "strict_input_validation", False)
    monkeypatch.setattr(fastmcp.settings, "stateless_http", False)
    application = create_mcp_app(lambda: None)
    server = application.state.fastmcp_server
    assert application.debug is False
    assert server.strict_input_validation is True
    assert isinstance(application.state.fastmcp_auth, OpaqueTokenVerifier)


async def noop_receive():
    return {"type": "http.disconnect"}


def test_bounded_transport_scrubs_sdk_json_and_corrects_content_length():
    register_secret(MCP)
    supplied = json.dumps({"id": MCP, "error": {"message": "unknown " + MCP}}).encode()

    async def child(_, __, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(supplied)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": supplied[:20], "more_body": True})
        await send({"type": "http.response.body", "body": supplied[20:]})

    async def run():
        sent = []

        async def send(message):
            sent.append(message)

        transport = BoundedMCPTransport(child, capacity=1, maximum=1024)
        await transport({"type": "http"}, noop_receive, send)
        body = sent[1]["body"]
        assert MCP.encode() not in body
        assert json.loads(body)["id"] == "[redacted]"
        assert dict(sent[0]["headers"])[b"content-length"] == str(len(body)).encode()
        assert transport.inflight == 0

    asyncio.run(run())


@pytest.mark.parametrize("shape", ["overflow", "numeric-secret"])
def test_unsafe_sdk_response_refuses_before_headers_and_releases_capacity(shape):
    numeric = "12345678901234567890123456789012"
    register_secret(numeric)
    supplied = (
        b" " * 1025
        if shape == "overflow"
        else json.dumps({"jsonrpc": "2.0", "id": int(numeric), "result": {}}).encode()
    )

    async def child(_, __, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": supplied})

    async def run():
        sent = []

        async def send(message):
            sent.append(message)

        transport = BoundedMCPTransport(child, capacity=1, maximum=1024)
        error = RequestError if shape == "overflow" else SafetyError
        with pytest.raises(error):
            await transport({"type": "http"}, noop_receive, send)
        assert sent == []
        assert transport.inflight == 0

    asyncio.run(run())


def test_transport_capacity_refuses_without_waiting_and_retains_active_ownership():
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()

        async def child(_, __, send):
            entered.set()
            await release.wait()
            await send({"type": "http.response.start", "status": 202, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        async def send(_):
            pass

        transport = BoundedMCPTransport(child, capacity=1, maximum=1024)
        active = asyncio.create_task(transport({"type": "http"}, noop_receive, send))
        await entered.wait()
        with pytest.raises(SafetyError) as failure:
            await transport({"type": "http"}, noop_receive, send)
        assert failure.value.problems[0].code == "HFAPI009"
        assert transport.inflight == 1
        release.set()
        await active
        assert transport.inflight == 0

    asyncio.run(run())


def test_mounted_capacity_is_reserved_before_reading_slow_bodies(configured, tmp_path):
    settings = configured.model_copy(
        update={
            "limits": configured.limits.model_copy(
                update={"metadata_workers": 1, "metadata_queue": 1}
            )
        }
    )
    app = create_app(settings, instance_lock_path=tmp_path / "instance.lock")

    async def run():
        reads, release = asyncio.Queue(), asyncio.Event()

        async def receive():
            await reads.put(None)
            await release.wait()
            return {"type": "http.disconnect"}

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/mcp/",
            "raw_path": b"/mcp/",
            "query_string": b"",
            "root_path": "",
            "headers": [
                (b"host", b"localhost"),
                (b"authorization", ("Bearer " + MCP).encode()),
                (b"content-type", b"application/json"),
            ],
            "client": ("127.0.0.1", 19000),
            "server": ("127.0.0.1", 80),
        }

        async def send(_):
            pass

        async with app.router.lifespan_context(app):
            first = asyncio.create_task(app(scope.copy(), receive, send))
            second = asyncio.create_task(app(scope.copy(), receive, send))
            await reads.get()
            await reads.get()
            assert app.state.mcp_transport.inflight == 2
            sent = []

            async def collect(message):
                sent.append(message)

            async def untouched():
                pytest.fail("over-capacity request body must not be read")

            await app(scope.copy(), untouched, collect)
            assert sent[0]["status"] == 503
            assert json.loads(sent[1]["body"])["code"] == "HFAPI009"
            release.set()
            await asyncio.gather(first, second)
            assert app.state.mcp_transport.inflight == 0

    asyncio.run(run())


def test_sdk_diagnostics_scrub_messages_and_exceptions_then_restore_handlers(caplog):
    register_secret(MCP)
    sdk = logging.getLogger("mcp.server.fixture")
    original = sdk.handlers[:], sdk.propagate
    with caplog.at_level(logging.WARNING, logger="hfcache"), mcp_diagnostics():
        try:
            raise ValueError(MCP)  # noqa: TRY301 - exercise SDK exception diagnostic path
        except ValueError:
            sdk.exception("rejected %s", MCP)
        assert MCP not in caplog.text
        assert caplog.records[-1].fields["diagnostic"] == "MCP SDK reported a request diagnostic"
        assert MCP not in repr(caplog.records[-1].__dict__)
    assert (sdk.handlers, sdk.propagate) == original
