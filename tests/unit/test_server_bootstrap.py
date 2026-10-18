"""Real local sockets exercise one daemon, authenticated UDS and verified TLS."""

import asyncio
import json
import logging
import socket
import ssl
import stat
import subprocess

import httpx
import pytest
from typer.testing import CliRunner

from hfcache import server as bootstrap
from hfcache.api.app import create_app
from hfcache.cli import app as cli
from hfcache.errors import HfcacheError
from hfcache.logging import reset
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping

TOKEN = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"


@pytest.fixture(autouse=True)
def isolate_logging():
    reset()
    names = ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi")
    before = {
        name: (logging.getLogger(name).level, logging.getLogger(name).disabled) for name in names
    }
    yield
    reset()
    for name, (level, disabled) in before.items():
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.disabled = disabled


@pytest.fixture
def policy(tmp_path):
    token = tmp_path / "writer.token"
    token.write_text(TOKEN, encoding="ascii")
    token.chmod(0o600)
    archive_config = tmp_path / "archive.toml"
    archive_config.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{ARCHIVE_ID}"\n',
        encoding="utf-8",
    )
    return validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(archive_config),
            "state_directory": str(tmp_path / "api-state"),
            "credentials": {"writer": {"file": str(token)}},
            "listener": {"unix_socket": str(tmp_path / "api.sock"), "tcp_enabled": False},
        }
    )


async def exercise(server, channels, callback):
    task = asyncio.create_task(server.serve(sockets=channels))
    try:
        async with asyncio.timeout(5):
            while not server.started:
                if task.done():
                    await task
                    pytest.fail("server exited before its local listener was ready")
                await asyncio.sleep(0.01)
        await callback()
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=10)


@pytest.mark.parametrize("tls", [False, True])
def test_one_lifespan_accepts_local_unix_and_tcp_with_tls_only_on_tcp(policy, tmp_path, tls):
    if tls:
        certificate = tmp_path / "certificate.pem"
        key = tmp_path / "private-key.pem"
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-subj",
                "/CN=localhost",
                "-addext",
                "subjectAltName=IP:127.0.0.1,DNS:localhost",
                "-keyout",
                str(key),
                "-out",
                str(certificate),
            ],
            check=True,
            capture_output=True,
        )
        policy = validate_server_config_mapping(
            policy.model_dump(mode="json")
            | {
                "listener": policy.listener.model_dump(mode="json")
                | {
                    "tls": {"certificate": str(certificate), "private_key": str(key)},
                },
            }
        )
    application = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")
    server = build_server(application, policy)
    with listeners(policy.listener) as channels, socket.socket() as tcp:
        tcp.bind(("127.0.0.1", 0))
        address = tcp.getsockname()

        async def request():
            unix_transport = httpx.AsyncHTTPTransport(uds=str(policy.listener.unix_socket))
            async with httpx.AsyncClient(
                transport=unix_transport, base_url="http://localhost", trust_env=False
            ) as unix:
                assert (await unix.get("/api/v1/version")).status_code == 401
                local = await unix.get(
                    "/api/v1/capabilities", headers={"Authorization": f"Bearer {TOKEN}"}
                )
                assert local.status_code == 200
                local_instance = local.json()["envelope"]["data"]["instance_id"]
            verify = ssl.create_default_context(cafile=certificate) if tls else True
            scheme = "https" if tls else "http"
            async with httpx.AsyncClient(
                verify=verify, trust_env=False, base_url=f"{scheme}://127.0.0.1:{address[1]}"
            ) as client:
                remote = await client.get(
                    "/api/v1/capabilities", headers={"Authorization": f"Bearer {TOKEN}"}
                )
                assert remote.status_code == 200
                assert remote.json()["envelope"]["data"]["instance_id"] == local_instance
            if tls:
                async with httpx.AsyncClient(trust_env=False) as untrusted:
                    with pytest.raises(httpx.ConnectError, match="CERTIFICATE_VERIFY_FAILED"):
                        await untrusted.get(f"https://127.0.0.1:{address[1]}/api/v1/version")

        asyncio.run(exercise(server, [*channels, tcp], request))
    assert not (tmp_path / "archive").exists()
    assert not policy.listener.unix_socket.exists()
    assert (tmp_path / "daemon.lock").is_file()


def test_socket_cleanup_retains_a_replaced_name(policy):
    with listeners(policy.listener):
        assert stat.S_IMODE(policy.listener.unix_socket.stat().st_mode) == 0o660
        policy.listener.unix_socket.unlink()
        policy.listener.unix_socket.write_text("unrelated replacement", encoding="utf-8")
    assert policy.listener.unix_socket.read_text(encoding="utf-8") == "unrelated replacement"


def test_startup_never_unlinks_or_adopts_an_existing_socket_path(policy):
    policy.listener.unix_socket.write_text("unrelated", encoding="utf-8")
    with pytest.raises(OSError, match="Address already in use"), listeners(policy.listener):
        pytest.fail("an existing path was adopted")
    assert policy.listener.unix_socket.read_text(encoding="utf-8") == "unrelated"


def test_socket_parent_symlink_is_refused_without_creation(policy, tmp_path):
    alias = tmp_path / "alias"
    outside = tmp_path / "outside"
    outside.mkdir()
    alias.symlink_to(outside, target_is_directory=True)
    listener = validate_server_config_mapping(
        policy.model_dump(mode="json")
        | {
            "listener": {"unix_socket": str(alias / "api.sock"), "tcp_enabled": False},
        }
    ).listener
    with pytest.raises(NotADirectoryError), listeners(listener):
        pytest.fail("a symlinked runtime parent was accepted")
    assert not (outside / "api.sock").exists()


def test_serve_bootstrap_help_and_config_errors_do_not_read_archive(policy, tmp_path):
    result = CliRunner().invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "--server-config" in result.output
    assert "--hub-token-file" in result.output
    result = CliRunner().invoke(
        cli, ["--json", "serve", "--server-config", str(tmp_path / "absent")]
    )
    assert result.exit_code == 10
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFCFG001"
    assert not (tmp_path / "archive").exists()


def test_serve_rejects_ambiguous_archive_and_hub_flags_before_import_or_bind(tmp_path):
    result = CliRunner().invoke(cli, ["--token-file", str(tmp_path / "unknown"), "serve"])
    assert result.exit_code == 10
    assert "HFARG002" in result.output


def test_serve_uses_only_explicit_startup_hub_file(tmp_path, monkeypatch):
    observed = []

    def run(path, *, hub_token_file):
        observed.append((path, hub_token_file))

    monkeypatch.setattr(bootstrap, "run", run)
    policy_path, token_path = tmp_path / "server.toml", tmp_path / "hub-credential"
    result = CliRunner().invoke(
        cli, ["serve", "--server-config", str(policy_path), "--hub-token-file", str(token_path)]
    )
    assert result.exit_code == 0
    assert observed == [(policy_path, token_path)]
    assert not token_path.exists()
    assert result.stdout == ""


@pytest.mark.parametrize("failure", ["credentials", "policy"])
def test_foreground_bootstrap_preserves_typed_lifespan_startup_failures(
    policy, tmp_path, monkeypatch, failure
):
    expected = "HFAPI003" if failure == "credentials" else "HFCFG002"
    if failure == "credentials":
        policy.credentials.writer.file.unlink()
    else:
        policy.archive_config.write_text("broken = [", encoding="utf-8")
    path = tmp_path / "server.toml"
    path.write_text(
        f'schema_version=1\narchive_config="{policy.archive_config}"\n'
        f'state_directory="{policy.state_directory}"\n'
        f'[credentials.writer]\nfile="{policy.credentials.writer.file}"\n'
        f'[listener]\nunix_socket="{policy.listener.unix_socket}"\ntcp_enabled=false\n',
        encoding="utf-8",
    )
    original = bootstrap.create_app
    monkeypatch.setattr(
        bootstrap,
        "create_app",
        lambda config, **options: original(
            config, instance_lock_path=tmp_path / "daemon.lock", **options
        ),
    )
    with pytest.raises(HfcacheError) as result:
        bootstrap.run(path)
    assert result.value.problems[0].code == expected
    assert result.value.exit_code == 10
    assert not policy.listener.unix_socket.exists()
    assert not (tmp_path / "archive").exists()
