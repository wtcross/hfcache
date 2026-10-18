"""Mounted MCP HTTP authentication and lifecycle, without in-memory shortcuts."""

import asyncio
import json
import socket
from typing import TYPE_CHECKING

import httpx2
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.utilities.asgi_transport import StreamingASGITransport, run_asgi_lifespan

from hfcache.api.app import create_app
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping
from tests.unit.test_server_bootstrap import (
    TOKEN,
    exercise,
    isolate_logging,  # noqa: F401 - autouse fixture
)
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture

if TYPE_CHECKING:
    from starlette.types import Message, Scope

MCP = "mcp-reader-" + "M" * 48
READER = "rest-reader-" + "R" * 48
UNKNOWN = "unknown-" + "U" * 48
ACCEPT = "application/json, text/event-stream"
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-11-25",
        "capabilities": {},
        "clientInfo": {"name": "hfcache-transport-fixture", "version": "1"},
    },
}


@pytest.fixture
def policy(request, tmp_path):
    base = request.getfixturevalue("socket_policy")
    sources = base.credentials.model_dump(mode="json")
    for name, token in (("reader", READER), ("mcp_reader", MCP)):
        path = tmp_path / (name + ".token")
        path.write_text(token)
        path.chmod(0o600)
        sources[name] = {"file": str(path)}
    return validate_server_config_mapping(
        base.model_dump(mode="json") | {"credentials": sources, "mcp_enabled": True}
    )


def headers(token=MCP):
    return {"Authorization": "Bearer " + token, "Accept": ACCEPT}


def streaming_client(app, **options):
    return httpx2.AsyncClient(
        transport=StreamingASGITransport(app),
        base_url="http://localhost",
        trust_env=False,
        timeout=3,
        follow_redirects=False,
        **options,
    )


def protocol_response(response):
    assert response.status_code == 200, response.text
    if response.headers["content-type"].startswith("application/json"):
        return response.json()
    assert response.headers["content-type"].startswith("text/event-stream")
    messages = [
        json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")
    ]
    return next(message for message in messages if message.get("id") == 1)


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_supported_streaming_http_client_negotiates_actual_mounted_empty_server(
    policy, tmp_path, mode
):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        def factory(
            headers: dict[str, str] | None = None,
            timeout: httpx2.Timeout | None = None,
            auth: httpx2.Auth | None = None,
            **options,
        ):
            return httpx2.AsyncClient(
                transport=StreamingASGITransport(app),
                trust_env=False,
                headers=headers,
                timeout=timeout or httpx2.Timeout(3),
                auth=auth,
                **options,
            )

        transport = StreamableHttpTransport(
            "http://localhost/mcp/", auth=MCP, httpx_client_factory=factory
        )
        async with run_asgi_lifespan(app):
            async with Client(transport, mode=mode, timeout=3, init_timeout=3) as client:
                assert client.is_connected()
                # MCP-001 supplies only protocol transport; MCP-002 owns tools.
                assert await client.list_tools() == []
                assert await client.list_resources() == []
                assert await client.list_prompts() == []
                assert transport.get_session_id() is None
                assert app.state.operations.list() == ()
            async with streaming_client(app) as rest:
                response = await rest.get("/api/v1/capabilities", headers=headers(TOKEN))
                assert response.status_code == 200
                assert response.json()["envelope"]["data"]["mcp"] is True
            assert not (tmp_path / "archive").exists()
        assert app.state.credentials is None

    asyncio.run(request())


@pytest.mark.parametrize("method", ["GET", "POST", "DELETE", "OPTIONS", "HEAD", "PUT"])
@pytest.mark.parametrize("token", [None, TOKEN, READER, UNKNOWN])
def test_every_mounted_method_authenticates_before_protocol_or_session_use(
    policy, tmp_path, method, token
):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            supplied = {"Accept": ACCEPT, "Mcp-Session-Id": "forged-session"}
            if token is not None:
                supplied["Authorization"] = "Bearer " + token
            response = await client.request(
                method, "/mcp/", headers=supplied, content=b"invalid JSON"
            )
            assert response.status_code == 401
            assert response.headers["www-authenticate"].startswith("Bearer")
            for secret in (MCP, TOKEN, READER, UNKNOWN):
                assert secret not in response.text
            assert app.state.operations.list() == ()
            assert not (tmp_path / "archive").exists()

    asyncio.run(request())


@pytest.mark.parametrize("path", ["/mcp", "/mcp/", "/mcp/unknown"])
@pytest.mark.parametrize("token", [None, TOKEN, READER])
def test_rejected_mcp_bearer_never_receives_body_even_on_alias_and_unknown_child(
    policy, tmp_path, path, token
):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        reads = 0
        sent: list[Message] = []

        async def receive() -> Message:
            nonlocal reads
            reads += 1
            return {"type": "http.request", "body": b"malformed", "more_body": False}

        async def send(message: Message):
            sent.append(message)

        supplied = [
            (b"host", b"localhost"),
            (b"content-type", b"application/json"),
            (b"content-length", b"999999999"),
        ]
        if token is not None:
            supplied.append((b"authorization", ("Bearer " + token).encode()))
        scope: Scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": supplied,
            "client": ("127.0.0.1", 19000),
            "server": ("localhost", 80),
        }
        async with run_asgi_lifespan(app):
            await app(scope, receive, send)
            assert (
                next(
                    message["status"]
                    for message in sent
                    if message["type"] == "http.response.start"
                )
                == 401
            )
            assert reads == 0
            assert app.state.operations.list() == ()

    asyncio.run(request())


def test_mcp_token_cannot_authenticate_any_rest_operation_or_unknown_route(policy, tmp_path):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            for method, path in (
                ("GET", "/api/v1/version"),
                ("GET", "/api/v1/operations"),
                ("POST", "/api/v1/syncs"),
                ("POST", "/api/v1/verifications"),
                ("GET", "/mcp-not-a-resource"),
            ):
                response = await client.request(method, path, headers=headers(), content=b"invalid")
                assert response.status_code == 401
            assert app.state.operations.list() == ()

    asyncio.run(request())


@pytest.mark.parametrize(
    ("extra", "status"),
    [({"Host": "attacker.invalid"}, 400), ({"Origin": "https://attacker.invalid"}, 403)],
)
def test_mounted_handshake_retains_host_origin_checks_before_protocol(
    policy, tmp_path, extra, status
):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            response = await client.post("/mcp/", headers=headers() | extra, json=INITIALIZE)
            assert response.status_code == status
            assert "attacker.invalid" not in response.text
            assert app.state.operations.list() == ()

    asyncio.run(request())


def test_disabled_mcp_neither_reads_inert_credential_nor_mounts_endpoint(policy, tmp_path):
    missing = tmp_path / "intentionally-missing-mcp-credential"
    disabled = validate_server_config_mapping(
        policy.model_dump(mode="json")
        | {
            "mcp_enabled": False,
            "credentials": policy.credentials.model_dump(mode="json")
            | {"mcp_reader": {"file": str(missing)}},
        }
    )
    app = create_app(disabled, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            response = await client.get("/mcp/", headers=headers(TOKEN))
            assert response.status_code == 404
            response = await client.get("/api/v1/capabilities", headers=headers(TOKEN))
            assert response.status_code == 200
            assert response.json()["envelope"]["data"]["mcp"] is False
            assert not missing.exists()
            assert app.state.operations.list() == ()

    asyncio.run(request())


@pytest.mark.parametrize("public", ["/management", "/m", "/mcp", "/api"])
def test_real_unix_native_and_tcp_public_mcp_share_one_authenticated_lifespan(
    policy, tmp_path, public
):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    configured = validate_server_config_mapping(
        policy.model_dump(mode="json")
        | {
            "listener": policy.listener.model_dump(mode="json")
            | {
                "root_path": public,
                "tcp_enabled": True,
                "tcp_port": port,
                "proxy_tls": True,
                "trusted_proxies": ["127.0.0.1/32"],
            }
        }
    )
    app = create_app(configured, instance_lock_path=tmp_path / "daemon.lock")
    server = build_server(app, configured)

    async def request(port):
        async with (
            httpx2.AsyncClient(
                transport=httpx2.AsyncHTTPTransport(uds=str(configured.listener.unix_socket)),
                base_url="http://localhost",
                trust_env=False,
                follow_redirects=False,
                timeout=3,
            ) as unix,
            httpx2.AsyncClient(
                base_url=f"http://127.0.0.1:{port}",
                trust_env=False,
                follow_redirects=False,
                timeout=3,
            ) as tcp,
        ):
            for path in ("/mcp/", public + "/mcp/"):
                accepted = await unix.post(path, headers=headers(), json=INITIALIZE)
                assert protocol_response(accepted)["result"]["protocolVersion"] == "2025-11-25"
                for rest_token in (TOKEN, READER):
                    refused = await unix.post(path, headers=headers(rest_token), json=INITIALIZE)
                    assert refused.status_code == 401
            for root in ("", public):
                alias = await unix.post(root + "/mcp", headers=headers(), json=INITIALIZE)
                assert alias.status_code == 307
                assert alias.headers["location"] == root + "/mcp/"
                for rest_token in (TOKEN, READER):
                    rest = await unix.get(root + "/api/v1/version", headers=headers(rest_token))
                    assert rest.status_code == 200, rest.text
                refused = await unix.get(root + "/api/v1/status", headers=headers())
                assert refused.status_code == 401
            assert (await tcp.post("/mcp/", headers=headers(), json=INITIALIZE)).status_code in {
                401,
                404,
            }
            refused = await tcp.post(public + "/mcp/", headers=headers(), json=INITIALIZE)
            assert refused.status_code == 403
            proxy = headers() | {"x-forwarded-proto": "https", "x-forwarded-prefix": "/attacker"}
            accepted = await tcp.post(public + "/mcp/", headers=proxy, json=INITIALIZE)
            assert protocol_response(accepted)["result"]["protocolVersion"] == "2025-11-25"
            for rest_token in (TOKEN, READER):
                refused = await tcp.post(
                    public + "/mcp/",
                    headers=headers(rest_token) | {"x-forwarded-proto": "https"},
                    json=INITIALIZE,
                )
                assert refused.status_code == 401
                rest = await tcp.get(
                    public + "/api/v1/status",
                    headers=headers(rest_token) | {"x-forwarded-proto": "https"},
                )
                assert rest.status_code == 200, rest.text
            refused = await tcp.get(public + "/api/v1/status", headers=proxy)
            assert refused.status_code == 401
            forged = await tcp.post("/attacker/mcp/", headers=proxy, json=INITIALIZE)
            assert forged.status_code in {401, 404}
            rest = await tcp.get(
                public + "/api/v1/version",
                headers=headers(TOKEN) | {"x-forwarded-proto": "https"},
            )
            assert rest.status_code == 200
            assert app.state.operations.list() == ()

    with listeners(configured.listener) as channels:
        asyncio.run(exercise(server, channels, lambda: request(port)))
    assert app.state.credentials is None
    assert not configured.listener.unix_socket.exists()
    assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize("enabled", [False, True])
def test_mounted_lifespan_teardown_releases_rest_instance_ownership_for_restart(
    policy, tmp_path, enabled
):
    configured = policy.model_copy(update={"mcp_enabled": enabled})
    lock = tmp_path / "daemon.lock"

    async def request():
        instance_ids = []
        for _ in range(2):
            app = create_app(configured, instance_lock_path=lock)
            async with run_asgi_lifespan(app), streaming_client(app) as client:
                response = await client.get("/api/v1/capabilities", headers=headers(TOKEN))
                assert response.status_code == 200
                instance_ids.append(response.json()["envelope"]["data"]["instance_id"])
                if enabled:
                    accepted = await client.post("/mcp/", headers=headers(), json=INITIALIZE)
                    assert protocol_response(accepted)["result"]["serverInfo"]["name"]
                assert app.state.operations.list() == ()
            assert app.state.credentials is None
        assert len(set(instance_ids)) == 2

    asyncio.run(request())


def test_stateless_handshake_issues_no_session_authority_and_every_followup_reauthenticates(
    policy, tmp_path
):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            initialized = await client.post("/mcp/", headers=headers(), json=INITIALIZE)
            assert protocol_response(initialized)["result"]["protocolVersion"] == "2025-11-25"
            assert "mcp-session-id" not in initialized.headers
            followup = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
            session = {
                "Mcp-Session-Id": "copied-or-invented-id",
                "MCP-Protocol-Version": "2025-11-25",
            }
            for authorization in (
                {},
                {"Authorization": "Bearer " + TOKEN},
                {"Authorization": "Bearer " + READER},
            ):
                refused = await client.post(
                    "/mcp/", headers={"Accept": ACCEPT} | session | authorization, json=followup
                )
                assert refused.status_code == 401
            accepted = await client.post("/mcp/", headers=headers() | session, json=followup)
            assert protocol_response(accepted)["result"] == {"tools": []}
            assert "mcp-session-id" not in accepted.headers
            assert app.state.operations.list() == ()

    asyncio.run(request())


def test_slash_alias_is_authenticated_and_cannot_reflect_query_or_proxy_prefix(policy, tmp_path):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            anonymous = await client.post("/mcp", json=INITIALIZE)
            assert anonymous.status_code == 401
            redirected = await client.post(
                "/mcp", headers=headers() | {"x-forwarded-prefix": "/attacker"}, json=INITIALIZE
            )
            assert redirected.status_code == 307
            assert redirected.headers["location"] == "/mcp/"
            query = await client.post(
                "/mcp?token=unregistered-opaque-query-secret", headers=headers(), json=INITIALIZE
            )
            assert query.status_code == 422
            assert "location" not in query.headers
            assert "unregistered-opaque-query-secret" not in query.text
            for path in ("/mcp//", "/mcp///"):
                malformed = await client.post(path, headers=headers(), json=INITIALIZE)
                assert malformed.status_code == 404
                assert "location" not in malformed.headers

    asyncio.run(request())


@pytest.mark.parametrize("boundary", ["request", "response"])
def test_actual_mounted_protocol_enforces_byte_budgets_and_recovers_capacity(
    policy, tmp_path, boundary
):
    configured = validate_server_config_mapping(
        policy.model_dump(mode="json")
        | {
            "limits": policy.limits.model_dump(mode="json")
            | {"max_request_bytes": 1024, "max_response_bytes": 1024}
        }
    )
    app = create_app(configured, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            body = INITIALIZE
            if boundary == "request":
                body = INITIALIZE | {"fixture": "unregistered-private-input" * 100}
            else:
                # Public SDK setting, changed only on this disposable test server.
                app.state.mcp_server.instructions = "large-fixture-instructions" * 100
            refused = await client.post("/mcp/", headers=headers(), json=body)
            assert refused.status_code == 413, refused.text
            assert len(refused.content) <= 1024
            assert "unregistered-private-input" not in refused.text
            assert "large-fixture-instructions" not in refused.text
            app.state.mcp_server.instructions = "Transport fixture"
            accepted = await client.post("/mcp/", headers=headers(), json=INITIALIZE)
            assert protocol_response(accepted)["result"]["serverInfo"]["name"]
            assert app.state.operations.list() == ()

    asyncio.run(request())


def test_registered_bearers_are_sanitized_in_protocol_output_and_diagnostics(
    policy, tmp_path, capfd
):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            app.state.mcp_server.instructions = "private fixture " + MCP + " " + TOKEN
            response = await client.post("/mcp/", headers=headers(), json=INITIALIZE)
            payload = protocol_response(response)
            assert isinstance(payload["result"]["instructions"], str)
            for secret in (MCP, TOKEN, READER):
                assert secret not in response.text
            assert "private fixture" in response.text
            assert app.state.operations.list() == ()

    asyncio.run(request())
    captured = capfd.readouterr()
    for secret in (MCP, TOKEN, READER):
        assert secret not in captured.out
        assert secret not in captured.err


def test_malformed_protocol_does_not_echo_rejected_values_in_output_or_diagnostics(
    policy, tmp_path, capfd
):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")
    private_value = "unregistered-private-protocol-value"

    async def request():
        async with run_asgi_lifespan(app), streaming_client(app) as client:
            response = await client.post(
                "/mcp/", headers=headers(), json=INITIALIZE | {"jsonrpc": private_value}
            )
            assert response.status_code == 400
            assert private_value not in response.text
            assert app.state.operations.list() == ()

    asyncio.run(request())
    captured = capfd.readouterr()
    assert private_value not in captured.out
    assert private_value not in captured.err
