"""REST gate: one real Unix/TCP lifespan retains trusted prefix/link authority."""

import asyncio
import json
import socket
from typing import TYPE_CHECKING

import httpx
import pytest

from hfcache.api.app import create_app
from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping
from hfcache.unix_http import UnixHTTPTransport
from tests.unit.test_server_bootstrap import (
    ARCHIVE_ID,
    TOKEN,
    exercise,
    isolate_logging,  # noqa: F401 - autouse fixture
)
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

PUBLIC = "/management"
PREFIX = "/api/v1"
AUTH = {"authorization": f"Bearer {TOKEN}"}


@pytest.fixture
def policy(request):
    base = request.getfixturevalue("socket_policy")
    return validate_server_config_mapping(
        base.model_dump(mode="json")
        | {
            "interactive_docs": True,
            "listener": base.listener.model_dump(mode="json")
            | {
                "tcp_enabled": True,
                "root_path": PUBLIC,
                "proxy_tls": True,
                "trusted_proxies": ["127.0.0.1/32"],
            },
        }
    )


def canonical_schema(app):
    return json.dumps(app.openapi(), sort_keys=True, separators=(",", ":"))


def test_real_unix_native_and_public_paths_share_one_registry_without_proxy_header_authority(  # noqa: PLR0915 - one lifecycle spans all real transports
    policy, tmp_path
):
    # Bind an ephemeral configured TCP port, never the deployed/default socket.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    policy = validate_server_config_mapping(
        policy.model_dump(mode="json")
        | {"listener": policy.listener.model_dump(mode="json") | {"tcp_port": port}}
    )
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")
    observations = []

    class RecordPeers:
        def __init__(self, app: ASGIApp):
            self.app = app

        async def __call__(self, scope: Scope, receive: Receive, send: Send):
            if scope["type"] == "http":
                observations.append((scope.get("client"), scope.get("server")))
            await self.app(scope, receive, send)

    app.add_middleware(RecordPeers)
    initial_schema = canonical_schema(app)
    native_ids = []

    def local_requests():
        config = ClientConfig(
            schema_version=1,
            api_socket=policy.listener.unix_socket,
            api_token_file=policy.credentials.writer.file,
            expected_archive_id=ARCHIVE_ID,
            read_retries=0,
        )
        with ApiClient(config) as client:
            local_instance = client.capabilities().instance_id
            assert client.read(PREFIX + "/status").envelope.exit_code == 0
            admission = client.submit(PREFIX + "/plans", {}, key="same-native-public")
            operation_id = admission.acceptance.operation.operation_id
            native_ids.append(operation_id)
            expected = PREFIX + "/operations/" + operation_id
            assert admission.acceptance.links.status == expected
            assert admission.acceptance.links.result == expected + "/result"
            assert admission.acceptance.links.events == expected + "/events"
            assert client.observe(operation_id, timeout=5).envelope.command == "plan"

        with httpx.Client(
            transport=UnixHTTPTransport(policy.listener.unix_socket, limits=httpx.Limits()),
            base_url="http://localhost",
            headers=AUTH,
            trust_env=False,
            follow_redirects=False,
        ) as unix:
            for root in ("", PUBLIC):
                caps = unix.get(root + PREFIX + "/capabilities")
                assert caps.status_code == 200, caps.text
                assert caps.json()["envelope"]["data"]["instance_id"] == local_instance
                schema = unix.get(root + PREFIX + "/openapi.json")
                assert schema.status_code == 200
                assert schema.json()["servers"] == [{"url": root or "/"}]
                assert unix.get(root + PREFIX + "/openapi.json").content == schema.content
                docs = unix.get(root + PREFIX + "/docs")
                assert docs.status_code == 200
                assert f"url: '{root + PREFIX}/openapi.json'" in docs.text
                retry = unix.post(
                    root + PREFIX + "/plans",
                    json={},
                    headers={"idempotency-key": "same-native-public"},
                )
                assert retry.status_code == 202, retry.text
                held = retry.json()
                assert held["created"] is False
                assert held["operation"]["operation_id"] == operation_id
                link = root + PREFIX + "/operations/" + operation_id
                assert retry.headers["location"] == held["links"]["status"] == link
                assert unix.get(held["links"]["result"]).status_code == 200
                assert unix.get(held["links"]["events"]).status_code == 200
            ignored = unix.get(
                PREFIX + "/capabilities",
                headers={"x-forwarded-prefix": "/attacker", "x-forwarded-proto": "http"},
            )
            assert ignored.status_code == 200
            assert unix.get("/attacker" + PREFIX + "/version").status_code == 404

        with httpx.Client(
            base_url=f"http://127.0.0.1:{port}", headers=AUTH, trust_env=False
        ) as tcp:
            assert tcp.get(PUBLIC + PREFIX + "/version").status_code == 403
            assert (
                tcp.get(
                    PUBLIC + PREFIX + "/version", headers={"x-forwarded-proto": "http"}
                ).status_code
                == 403
            )
            proxy = {
                "x-forwarded-proto": "https",
                "x-forwarded-prefix": "/attacker",
                "x-forwarded-host": "attacker.invalid",
            }
            assert tcp.get(PREFIX + "/version", headers=proxy).status_code == 404
            remote = tcp.get(PUBLIC + PREFIX + "/capabilities", headers=proxy)
            assert remote.status_code == 200
            assert remote.json()["envelope"]["data"]["instance_id"] == local_instance
            retry = tcp.post(
                PUBLIC + PREFIX + "/plans",
                json={},
                headers=proxy | {"idempotency-key": "same-native-public"},
            )
            assert retry.status_code == 202
            assert retry.json()["created"] is False
            assert retry.headers["location"] == PUBLIC + PREFIX + "/operations/" + operation_id
            for field in ("status", "events", "result"):
                assert tcp.get(retry.json()["links"][field], headers=proxy).status_code == 200
            schema = tcp.get(PUBLIC + PREFIX + "/openapi.json", headers=proxy)
            assert schema.json()["servers"] == [{"url": PUBLIC}]

    server = build_server(app, policy)
    with listeners(policy.listener) as channels:
        unix_name = next(
            channel.getsockname() for channel in channels if channel.family == socket.AF_UNIX
        )

        async def request():
            await asyncio.to_thread(local_requests)

        asyncio.run(exercise(server, channels, request))

    assert canonical_schema(app) == initial_schema
    assert len(native_ids) == 1
    assert not (tmp_path / "archive").exists()
    # Locked Uvicorn's actual Unix getpeername is not an IP tuple. No caller
    # header participates in the trust distinction exercised above.
    assert any(peer is None and local == (unix_name, None) for peer, local in observations)
    assert any(peer is not None and peer[0] == "127.0.0.1" for peer, _ in observations)


def test_openapi_is_deterministic_across_apps_and_repeated_native_public_views(policy, tmp_path):
    first = create_app(policy, instance_lock_path=tmp_path / "first.lock")
    second = create_app(policy, instance_lock_path=tmp_path / "second.lock")
    expected = canonical_schema(first)
    assert canonical_schema(first) == canonical_schema(second) == expected
    schema = first.openapi()
    assert schema["servers"] == [{"url": PUBLIC}]
    operation_ids = [
        operation["operationId"]
        for methods in schema["paths"].values()
        for operation in methods.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operation_ids) == len(set(operation_ids))
    assert schema["components"]["securitySchemes"]["hfcacheBearer"]["scheme"] == "bearer"
    assert all(
        {"hfcacheBearer": []} in operation["security"]
        for methods in schema["paths"].values()
        for operation in methods.values()
        if isinstance(operation, dict) and "operationId" in operation
    )
    assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize(
    ("peer", "local"),
    [
        (None, None),
        (None, ("127.0.0.1", 8787)),
        (None, ("relative.sock", None)),
        (None, ("", None)),
        (None, ("/", None)),
        (None, ("/tmp/unsafe\x00.sock", None)),
        (None, ("/tmp/api.sock", 0)),
        (None, ("/tmp/api.sock", "8787")),
        (None, ("/tmp/api.sock", None, "unexpected")),
        (None, "/tmp/api.sock"),
        (("127.0.0.1", 5678), ("/tmp/api.sock", None)),
    ],
)
def test_missing_or_malformed_native_scope_cannot_bypass_prefix_or_proxy_tls(
    policy, tmp_path, peer, local
):
    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")

    async def missing_evidence(scope, receive, send):
        if scope["type"] == "http":
            scope = scope | {"client": peer, "server": local}
        await app(scope, receive, send)

    async def request():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=missing_evidence),
                base_url="http://localhost",
                headers=AUTH,
            ) as client,
        ):
            forged = {"x-forwarded-prefix": PUBLIC, "x-forwarded-for": "unix"}
            assert (await client.get(PREFIX + "/version", headers=forged)).status_code == 404
            assert (
                await client.get(PUBLIC + PREFIX + "/version", headers=forged)
            ).status_code == 403

    asyncio.run(request())
    assert not (tmp_path / "archive").exists()
