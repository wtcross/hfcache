"""MCP-004: optional tools preserve REST execution, roles and packaged isolation."""

import asyncio
import json
import tomllib

import httpx
import httpx2
import pytest
from fastmcp.utilities.asgi_transport import StreamingASGITransport, run_asgi_lifespan

from hfcache.api.app import create_app
from hfcache.client_models import ClientRead
from hfcache.server_config import validate_server_config_mapping
from tests.unit.test_api_commands import configured as configured  # noqa: PLC0414 - fixture
from tests.unit.test_api_commands import result, submit
from tests.unit.test_api_operations import READER, READER_HEADERS, WRITER, WRITER_HEADERS
from tests.unit.test_mcp_tools import MCP, snapshot
from tests.unit.test_mcp_tools import archive as archive  # noqa: PLC0414 - shared fixture
from tests.unit.test_mcp_transport import INITIALIZE
from tests.unit.test_rest_security_gate import ROUTES, WRITER_POSTS, concrete, raw_request
from tests.unit.test_server_bootstrap import isolate_logging  # noqa: F401 - autouse fixture
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture
from tests.unit.test_synchronize import MODEL
from tests.unit.test_systemd_units import CLIENTS, PACKAGING, TOKEN_ENV, fields

ROTATED = "rotated-mcp-reader-" + "Z" * 48


def settings(server, tmp_path, *, enabled):
    token_file = tmp_path / "mcp-reader.token"
    token_file.write_text(MCP, encoding="ascii")
    token_file.chmod(0o600)
    return validate_server_config_mapping(
        server.model_dump(mode="json")
        | {
            "mcp_enabled": enabled,
            "interactive_docs": True,
            "maintenance_enabled": True,
            "credentials": server.credentials.model_dump(mode="json")
            | {"mcp_reader": {"file": str(token_file)}},
        }
    )


def test_optional_mcp_keeps_exact_rest_openapi_and_authentication_scheme(configured, tmp_path):
    base, _, _, lock = configured
    disabled = create_app(settings(base, tmp_path, enabled=False), instance_lock_path=lock)
    enabled = create_app(settings(base, tmp_path, enabled=True), instance_lock_path=lock)
    assert disabled.openapi() == enabled.openapi()
    schema = enabled.openapi()
    assert set(schema["components"]["securitySchemes"]) == {"hfcacheBearer"}
    assert "/mcp" not in schema["paths"]
    assert "/mcp/" not in schema["paths"]
    assert not lock.exists()


@pytest.mark.parametrize("enabled", [False, True], ids=["rest-alone", "rest-and-mcp"])
def test_every_rest_role_and_real_command_remains_identical_with_optional_mcp(
    configured, tmp_path, enabled
):
    base, layout, hub, lock = configured
    server = settings(base, tmp_path, enabled=enabled)
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with (
            run_asgi_lifespan(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                trust_env=False,
            ) as client,
        ):
            for method, path in ROUTES:
                status, payload, received, _ = await raw_request(
                    app, method, concrete(path), (f"Bearer {MCP}".encode(),), body=b"malformed"
                )
                assert status == 401, (method, path, payload)
                assert received == 0
                for token in (READER, WRITER):
                    status, payload, received, _ = await raw_request(
                        app,
                        method,
                        concrete(path),
                        (f"Bearer {token}".encode(),),
                        body=b"{" if method == "POST" else b"",
                    )
                    if method == "POST":
                        writer_only = path.removeprefix("/api/v1") in WRITER_POSTS
                        denied = token == READER and writer_only
                        assert status == (403 if denied else 422), (path, payload)
                        assert received == (0 if denied else 1)
                    else:
                        assert status not in {401, 403, 405}, (path, payload)
                    assert token not in payload
            assert app.state.operations.list() == ()
            capabilities = await client.get("/api/v1/capabilities", headers=READER_HEADERS)
            assert capabilities.status_code == 200
            body = ClientRead.model_validate(capabilities.json())
            assert body.envelope.data["mcp"] is enabled
            inventory = await client.get("/api/v1/status", headers=READER_HEADERS)
            body = ClientRead.model_validate(inventory.json())
            assert body.envelope.command == "status"
            assert len(body.envelope.data["repositories"]) == 2
            archive_before = snapshot(layout.root)
            planned = await submit(
                client, "/api/v1/plans", {}, "reader-plan", headers=READER_HEADERS
            )
            terminal = await result(client, planned)
            assert terminal["command"] == "plan"
            assert terminal["exit_code"] == 0
            assert len(terminal["data"]["repositories"]) == 2
            assert snapshot(layout.root) == archive_before
            accepted = await submit(
                client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, "sync"
            )
            terminal = await result(client, accepted)
            assert terminal["command"] == "sync"
            assert terminal["exit_code"] == 0
            assert terminal["data"]["repositories"][0]["status"] == "published"
            assert (layout.root / terminal["data"]["report"]).is_file()
            assert len(hub.downloads) == 1
            response = await client.get("/api/v1/operations", headers=READER_HEADERS)
            history = ClientRead.model_validate(response.json()).envelope.data["operations"]
            assert len(history) == 2
            assert {row["state"] for row in history} == {"succeeded"}
        assert app.state.credentials is None

    asyncio.run(exercise())


def test_protected_file_rotation_takes_effect_only_after_restart_and_keeps_rest_authority(
    archive, tmp_path, capfd
):
    credential = archive.server.credentials.mcp_reader.file
    assert credential is not None

    async def probe(app, expected):
        async with httpx2.AsyncClient(
            transport=StreamingASGITransport(app), base_url="http://localhost", trust_env=False
        ) as client:
            for token, status in expected:
                before = snapshot(archive.queries.layout.root, archive.server.state_directory)
                response = await client.post(
                    "/mcp/",
                    json=INITIALIZE,
                    headers={
                        "authorization": "Bearer " + token,
                        "accept": "application/json, text/event-stream",
                    },
                )
                assert response.status_code == status
                assert (
                    snapshot(archive.queries.layout.root, archive.server.state_directory) == before
                )
                assert token not in response.text
            rest = await client.get("/api/v1/version", headers=WRITER_HEADERS)
            assert rest.status_code == 200
            assert ClientRead.model_validate(rest.json()).envelope.exit_code == 0
            assert app.state.operations.list() == ()

    async def exercise():
        async with run_asgi_lifespan(archive.app):
            first_id = archive.app.state.instance_id
            await probe(archive.app, ((MCP, 200), (ROTATED, 401)))
            credential.write_text(ROTATED, encoding="ascii")
            await probe(archive.app, ((MCP, 200), (ROTATED, 401)))
        assert archive.app.state.credentials is None
        restarted = create_app(archive.server, instance_lock_path=tmp_path / "daemon.lock")
        async with run_asgi_lifespan(restarted):
            assert restarted.state.instance_id != first_id
            await probe(restarted, ((MCP, 401), (ROTATED, 200)))
        assert restarted.state.credentials is None

    asyncio.run(exercise())
    captured = capfd.readouterr()
    for token in (MCP, ROTATED, WRITER):
        assert token not in captured.out + captured.err


def test_packaged_optional_mcp_never_changes_worker_credentials_egress_or_timer_clients():
    server = validate_server_config_mapping(tomllib.loads((PACKAGING / "server.toml").read_text()))
    assert server.mcp_enabled is False
    assert server.credentials.mcp_reader is None
    api = fields("hfcache-api.service", "Service")
    assert api["ImportCredential"] == ["hf-token"]
    assert api["LoadCredentialEncrypted"] == ["hfcache.api:/etc/credstore.encrypted/hfcache.api"]
    worker = fields("hfcache-verification.service", "Service")
    assert not any("Credential" in key for key in worker)
    assert worker["IPAddressDeny"] == ["any"]
    assert TOKEN_ENV | {"CREDENTIALS_DIRECTORY"} <= set(
        " ".join(worker["UnsetEnvironment"]).split()
    )
    assert "-/run/credentials" in " ".join(worker["InaccessiblePaths"]).split()
    for name in CLIENTS:
        observer = fields(name, "Service")
        assert observer["LoadCredentialEncrypted"] == api["LoadCredentialEncrypted"]
        assert "ImportCredential" not in observer
        assert "hfcache.scheduled_client" in observer["ExecStart"][0]
        assert "mcp" not in observer["ExecStart"][0]
        assert observer["TimeoutStartSec"] == ["infinity"]
    for name in ("hfcache-sync.timer", "hfcache-verify.timer"):
        timer = fields(name, "Timer")
        assert timer["Persistent"] == ["true"]
    assert "fastmcp" not in json.dumps(server.model_dump(mode="json"))
