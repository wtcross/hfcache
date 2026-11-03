"""Real TLS/TCP and Unix requests exercise the source application's Basic boundary."""

from __future__ import annotations

import asyncio
import base64
import json
import secrets
import socket
import ssl
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from hfcache.api.basic import create_administrator_record
from hfcache.server import build_server
from hfcache.server_config import validate_server_config_mapping
from tests.intent_fixtures import create_app
from tests.unit.test_server_bootstrap import isolate_logging  # noqa: F401 - autouse fixture

if TYPE_CHECKING:
    from pathlib import Path

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"


@dataclass(repr=False)
class MemoryCredentials:
    password: bytes = field(repr=False)
    username: str = "independent-operator"
    subject: str = "independent-stable-subject"
    tokens: dict[str, str] = field(default_factory=dict, repr=False)

    def basic(self, *, username: str | None = None, password: bytes | None = None) -> str:
        encoded = (self.username if username is None else username).encode() + b":"
        encoded += self.password if password is None else password
        return "Basic " + base64.b64encode(encoded).decode("ascii")


@pytest.fixture(scope="module")
def memory_credentials():
    """Passwords exist only in test-process memory; only the derived PHC is written."""
    return MemoryCredentials(
        secrets.token_urlsafe(36).encode(),
        tokens={name: secrets.token_urlsafe(48) for name in ("writer", "reader", "mcp_reader")},
    )


@pytest.fixture(scope="module")
def tls_identity(tmp_path_factory):
    root = tmp_path_factory.mktemp("basic-tls")
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "owned-basic-fixture")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    cert_path, key_path = root / "certificate.pem", root / "private-key.pem"
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    key_path.chmod(0o600)
    return cert_path, key_path


@asynccontextmanager
async def running(profile: Path, credentials: MemoryCredentials, tls, *, prefix="", mcp=False):
    """No policy/archive discovery; the exact real lifespan owns all three pools."""
    profile.mkdir(mode=0o700)
    policy_path = profile / "archive.toml"
    policy_path.write_text(
        "schema_version=1\n[storage]\narchive_root="
        + json.dumps(str(profile / "absent-archive"))
        + '\narchive_id="'
        + ARCHIVE_ID
        + '"\n'
    )
    record = create_administrator_record(
        credentials.subject, credentials.username, credentials.password
    )
    record_path = profile / "administrator.json"
    record_path.write_text(record.model_dump_json())
    record_path.chmod(0o600)
    sources = {}
    for name, value in credentials.tokens.items():
        path = profile / (name + ".token")
        path.write_text(value)
        path.chmod(0o600)
        sources[name] = {"file": str(path)}
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("127.0.0.1", 0))
    port = tcp.getsockname()[1]
    origin = f"https://localhost:{port}"
    unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    unix_path = profile / "api.sock"
    unix.bind(str(unix_path))
    unix_path.chmod(0o600)
    settings = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(policy_path),
            "state_directory": str(profile / "state"),
            "credentials": sources,
            "mcp_enabled": mcp,
            "basic": {"origin": origin, "administrator": {"file": str(record_path)}},
            "listener": {
                "unix_socket": str(unix_path),
                "tcp_host": "127.0.0.1",
                "tcp_port": port,
                "root_path": prefix,
                "allowed_origins": [origin],
                "tls": {"certificate": str(tls[0]), "private_key": str(tls[1])},
            },
        }
    )
    app = create_app(settings, instance_lock_path=profile / "instance.lock")
    server = build_server(app, settings)
    task = asyncio.create_task(server.serve(sockets=[tcp, unix]))
    provider = None
    try:
        async with asyncio.timeout(15):
            while not server.started:
                if task.done():
                    await task
                    pytest.fail("owned Basic API did not start")
                await asyncio.sleep(0.005)
        provider = app.state.basic_provider
        yield {
            "app": app,
            "provider": provider,
            "origin": origin,
            "prefix": prefix,
            "profile": profile,
            "settings": settings,
            "unix_path": unix_path,
            "tls": ssl.create_default_context(cafile=tls[0]),
        }
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=15)
        tcp.close()
        unix.close()
        if provider is not None:
            assert provider.stats.active == 0
            assert provider.stats.waiting == 0
            assert not provider.stats.accepting
        assert task.done()
        assert not (profile / "absent-archive").exists()


@asynccontextmanager
async def client_for(harness, transport):
    options: dict[str, Any] = {"trust_env": False, "timeout": 10}
    if transport == "unix":
        options |= {
            "transport": httpx.AsyncHTTPTransport(uds=str(harness["unix_path"])),
            "base_url": "http://localhost",
        }
    else:
        options |= {"verify": harness["tls"], "base_url": harness["origin"]}
    async with httpx.AsyncClient(**options) as client:
        yield client


@pytest.mark.parametrize("prefix", ["", "/management"])
@pytest.mark.parametrize("transport", ["tls", "unix"])
def test_actual_basic_and_bearer_classes_keep_old_wire_and_no_origin_reads(
    tmp_path_factory, memory_credentials, tls_identity, prefix, transport
):
    profile = tmp_path_factory.mktemp("basic-profile") / "owned"

    async def exercise():
        async with (
            running(profile, memory_credentials, tls_identity, prefix=prefix) as harness,
            client_for(harness, transport) as client,
        ):
            path = prefix + "/api/v1/capabilities"
            anonymous = await client.get(path)
            assert anonymous.status_code == 401
            assert "Basic" in anonymous.headers["www-authenticate"]
            for authorization, expected in (
                (memory_credentials.basic(), "rest-writer"),
                ("Bearer " + memory_credentials.tokens["writer"], "rest-writer"),
                ("Bearer " + memory_credentials.tokens["reader"], "rest-reader"),
            ):
                response = await client.get(path, headers={"Authorization": authorization})
                assert response.status_code == 200
                payload = response.json()["envelope"]["data"]
                assert payload["credential_class"] == expected
                assert set(payload["capabilities"]) == (
                    {"read", "write"} if expected == "rest-writer" else {"read"}
                )
                assert "subject" not in payload
            wrong_interface = await client.get(
                path,
                headers={"Authorization": "Bearer " + memory_credentials.tokens["mcp_reader"]},
            )
            assert wrong_interface.status_code == 401
            assert wrong_interface.headers["www-authenticate"].startswith("Bearer ")
            spellings = [path] if transport == "tls" else [path, "/api/v1/capabilities"]
            for spelling in spellings:
                assert (
                    await client.get(
                        spelling, headers={"Authorization": memory_credentials.basic()}
                    )
                ).status_code == 200

    asyncio.run(exercise())


def test_bad_password_flood_does_not_starve_original_bearer_operation_observation(
    tmp_path_factory, memory_credentials, tls_identity
):
    profile = tmp_path_factory.mktemp("basic-flood") / "owned"
    before = {thread.ident for thread in threading.enumerate()}
    owned_workers = set()

    async def exercise():
        async with running(profile, memory_credentials, tls_identity) as harness:
            writer = {"Authorization": "Bearer " + memory_credentials.tokens["writer"]}
            async with client_for(harness, "tls") as observations:
                accepted = await observations.post(
                    "/api/v1/plans",
                    json={},
                    headers=writer | {"Idempotency-Key": "original-flood-observation"},
                )
                assert accepted.status_code == 202
                operation_id = accepted.json()["operation"]["operation_id"]
                operation_path = "/api/v1/operations/" + operation_id
                wrong = memory_credentials.basic(password=secrets.token_urlsafe(32).encode())
                async with httpx.AsyncClient(
                    base_url=harness["origin"],
                    verify=harness["tls"],
                    trust_env=False,
                    timeout=15,
                    limits=httpx.Limits(max_connections=20),
                ) as attacks:
                    requests = [
                        asyncio.create_task(
                            attacks.get("/api/v1/version", headers={"Authorization": wrong})
                        )
                        for _ in range(14)
                    ]
                    latencies = []
                    maximum_active = 0
                    maximum_waiting = 0
                    for _ in range(5):
                        owned_workers.update(
                            thread.ident
                            for thread in threading.enumerate()
                            if thread.name.startswith("hfcache-auth") and thread.ident not in before
                        )
                        started = time.monotonic()
                        response = await observations.get(operation_path, headers=writer)
                        latencies.append(time.monotonic() - started)
                        assert response.status_code == 200
                        assert (
                            response.json()["envelope"]["data"]["operation"]["operation_id"]
                            == operation_id
                        )
                        maximum_active = max(maximum_active, harness["provider"].stats.active)
                        maximum_waiting = max(maximum_waiting, harness["provider"].stats.waiting)
                    replies = await asyncio.gather(*requests)
                    assert all(reply.status_code in {401, 429} for reply in replies)
                    assert any(reply.status_code == 429 for reply in replies)
                    for reply in replies:
                        if reply.status_code == 429:
                            assert reply.json()["code"] == "HFAPI021"
                            assert reply.json()["exit_code"] == 20
                    assert maximum_active == 2
                    assert maximum_waiting <= 8
                    assert len(owned_workers) == 2
                    assert max(latencies) < 5
                result = await observations.get(operation_path + "/result", headers=writer)
                assert result.status_code == 200
                assert result.json()["envelope"]["command"] == "plan"
                events = await observations.get(operation_path + "/events", headers=writer)
                assert events.status_code == 200
                assert events.json()["envelope"]["data"]["operation_id"] == operation_id

    asyncio.run(exercise())
    # The actual lifespan has joined its workers, not merely freed request slots.
    after = {thread.ident for thread in threading.enumerate()}
    assert owned_workers.isdisjoint(after)


@pytest.mark.parametrize("prefix", ["", "/management"])
@pytest.mark.parametrize("transport", ["tls", "unix"])
def test_real_mcp_listener_remains_bearer_only(
    tmp_path_factory, memory_credentials, tls_identity, prefix, transport
):
    profile = tmp_path_factory.mktemp("basic-mcp") / "owned"

    async def exercise():
        async with (
            running(profile, memory_credentials, tls_identity, prefix=prefix, mcp=True) as harness,
            client_for(harness, transport) as client,
        ):
            path = prefix + "/mcp/"
            headers = {"Accept": "application/json, text/event-stream"}
            for authorization in (
                memory_credentials.basic(),
                memory_credentials.basic(password=secrets.token_urlsafe(32).encode()),
                "Bearer " + memory_credentials.tokens["writer"],
                "Bearer " + memory_credentials.tokens["reader"],
            ):
                response = await client.post(
                    path,
                    headers=headers | {"Authorization": authorization},
                    content=b"this is deliberately not JSON",
                )
                assert response.status_code == 401
                assert response.headers["www-authenticate"].startswith("Bearer ")
                assert response.json()["code"] == "HFAPI001"
            response = await client.post(
                path,
                headers=headers
                | {"Authorization": "Bearer " + memory_credentials.tokens["mcp_reader"]},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "independent-socket-fixture", "version": "1"},
                    },
                },
            )
            assert response.status_code == 200
            assert '"protocolVersion"' in response.text
            assert harness["provider"].stats.failures == 0

    asyncio.run(exercise())


def test_disconnected_real_clients_do_not_retire_running_hash_workers_before_shutdown(
    tmp_path_factory, memory_credentials, tls_identity
):
    profile = tmp_path_factory.mktemp("basic-disconnect") / "owned"
    before = {thread.ident for thread in threading.enumerate()}
    owned_workers = set()
    provider = None

    async def exercise():
        nonlocal provider
        async with running(profile, memory_credentials, tls_identity) as harness:
            provider = harness["provider"]
            wrong = memory_credentials.basic(password=secrets.token_urlsafe(32).encode())
            connections = []
            try:
                # Complete TLS ownership before starting hash work. Cancelling
                # HTTPX during pool/handshake acquisition does not provide an
                # exact socket handle whose closure this test can verify.
                for _ in range(10):
                    connections.append(  # noqa: PERF401 - retain every acquired stream if a later handshake fails
                        await asyncio.open_connection(
                            "127.0.0.1",
                            harness["settings"].listener.tcp_port,
                            ssl=harness["tls"],
                            server_hostname="localhost",
                        )
                    )
                request = (
                    "GET /api/v1/version HTTP/1.1\r\nHost: localhost\r\nAuthorization: "
                    + wrong
                    + "\r\nConnection: close\r\n\r\n"
                ).encode()
                for _, writer in connections:
                    writer.write(request)
                await asyncio.gather(*(writer.drain() for _, writer in connections))
                async with asyncio.timeout(5):
                    while provider.stats.active != 2 or provider.stats.waiting != 8:
                        await asyncio.sleep(0.001)
                owned_workers.update(
                    thread.ident
                    for thread in threading.enumerate()
                    if thread.name.startswith("hfcache-auth") and thread.ident not in before
                )
                assert len(owned_workers) == 2
                for _, writer in connections:
                    writer.transport.abort()
                await asyncio.gather(*(writer.wait_closed() for _, writer in connections))
                assert all(writer.is_closing() for _, writer in connections)
                # A real client disconnect is not evidence that its admitted
                # Argon work or queue reservation has completed.
                assert provider.stats.active + provider.stats.waiting > 0
            finally:
                for _, writer in connections:
                    writer.transport.abort()
                await asyncio.gather(*(writer.wait_closed() for _, writer in connections))

    asyncio.run(exercise())
    assert provider is not None
    assert provider.stats.failures == 10
    assert provider.stats.active == provider.stats.waiting == 0
    assert not provider.stats.accepting
    assert owned_workers.isdisjoint({thread.ident for thread in threading.enumerate()})
