"""Real reader-client TCP/Unix/TLS requests against one disposable API lifespan."""

import asyncio
import socket
import subprocess
import sys

import pytest

from hfcache.api.app import create_app
from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.client_errors import ClientConnectionError, ClientProtocolError, RemoteApiError
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping
from tests.unit.test_server_bootstrap import (
    ARCHIVE_ID,
    exercise,
    isolate_logging,  # noqa: F401 - autouse fixture
)
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture


@pytest.fixture
def policy(request):
    return request.getfixturevalue("socket_policy")


@pytest.mark.parametrize("tls", [False, True])
def test_reader_client_uses_real_unix_tcp_and_verified_tls(policy, tmp_path, monkeypatch, tls):
    # Ambient proxy/netrc discovery must not change either selected transport.
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("NO_PROXY", "")
    certificate = None
    if tls:
        certificate, key = tmp_path / "certificate.pem", tmp_path / "private-key.pem"
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
                | {"tls": {"certificate": str(certificate), "private_key": str(key)}}
            }
        )
    application = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")
    server = build_server(application, policy)
    wrong_token = tmp_path / "wrong.token"
    wrong_token.write_text("wrong-reader-" + "W" * 40)
    wrong_token.chmod(0o600)
    with listeners(policy.listener) as channels, socket.socket() as tcp:
        tcp.bind(("127.0.0.1", 0))
        port = tcp.getsockname()[1]

        def read_all():
            common = {
                "schema_version": 1,
                "api_token_file": policy.credentials.writer.file,
                "expected_archive_id": ARCHIVE_ID,
                "read_retries": 0,
            }

            def settings(**overrides):
                return ClientConfig.model_validate(common | overrides)

            with ApiClient(settings(api_socket=policy.listener.unix_socket)) as client:
                local = client.capabilities()
                assert set(local.capabilities) == {"read", "write"}
                assert client.read("/api/v1/version").envelope.exit_code == 0
            scheme = "https" if tls else "http"
            url = f"{scheme}://127.0.0.1:{port}"
            with ApiClient(settings(api_url=url, ca_file=certificate)) as client:
                assert client.capabilities().instance_id == local.instance_id
                assert client.read("/api/v1/version").envelope.exit_code == 0
            if tls:
                with (
                    ApiClient(settings(api_url=url)) as client,
                    pytest.raises(ClientConnectionError, match="HFAPI019"),
                ):
                    client.read("/api/v1/version")
            with ApiClient(
                settings(
                    api_token_file=wrong_token,
                    api_socket=policy.listener.unix_socket,
                )
            ) as client:
                with pytest.raises(RemoteApiError, match="HFAPI001") as failure:
                    client.capabilities()
                assert failure.value.exit_code == 10
                assert failure.value.status_code == 401
            other_id = "ad7bd2f4-f3f6-4d15-94a5-c468e10c3d18"
            with (
                ApiClient(
                    settings(
                        expected_archive_id=other_id,
                        api_socket=policy.listener.unix_socket,
                    )
                ) as client,
                pytest.raises(ClientProtocolError, match="HFAPI018"),
            ):
                client.read("/api/v1/version")

        async def request():
            await asyncio.to_thread(read_all)

        asyncio.run(exercise(server, [*channels, tcp], request))
    # The bootstrap fixture intentionally points to a missing synthetic archive.
    assert not (tmp_path / "archive").exists()
    assert not policy.listener.unix_socket.exists()


def test_client_import_never_loads_writer_or_optional_frameworks():
    code = (
        "import sys; import hfcache.client,hfcache.client_config; "
        "forbidden=('hfcache.config','hfcache.server','hfcache.services.commands',"
        "'hfcache.credentials','huggingface_hub','fastapi','uvicorn','fastmcp'); "
        "assert not any(name in sys.modules for name in forbidden), "
        "[name for name in forbidden if name in sys.modules]"
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
