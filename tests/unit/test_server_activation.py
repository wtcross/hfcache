"""Named inherited listeners share one app without path ownership (decision 121)."""

import signal
import socket
import ssl
import stat
import subprocess
import time
from contextlib import contextmanager

import httpx
import pytest

from hfcache.server_config import validate_server_config_mapping
from hfcache.unix_http import UnixHTTPTransport
from tests.socket_activation import activated_process
from tests.unit.test_server_bootstrap import TOKEN
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture

_DRIVER = """
import sys
from pathlib import Path
from hfcache import server
from hfcache.errors import HfcacheError
original = server.create_app
server.create_app = lambda policy, **options: original(
    policy, instance_lock_path=Path(sys.argv[1]).parent/'daemon.lock', **options
)
try:
    server.run(Path(sys.argv[1]))
except HfcacheError as error:
    sys.stderr.write(error.problems[0].code)
    raise SystemExit(int(error.exit_code))
"""


@pytest.fixture
def policy(request):
    return request.getfixturevalue("socket_policy")


@contextmanager
def _bound(policy, *, unix=True, tcp=True):
    channels = []
    try:
        if unix:
            channel = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            channels.append(channel)
            channel.bind(str(policy.listener.unix_socket))
            policy.listener.unix_socket.chmod(policy.listener.socket_mode)
            channel.listen(8)
        port = 8787
        if tcp:
            channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            channels.append(channel)
            channel.bind(("127.0.0.1", 0))
            channel.listen(8)
            port = channel.getsockname()[1]
        configured = validate_server_config_mapping(
            policy.model_dump(mode="json")
            | {
                "listener": policy.listener.model_dump(mode="json")
                | {"unix_enabled": unix, "tcp_enabled": tcp, "tcp_port": port}
            }
        )
        yield configured, channels
    finally:
        for channel in channels:
            channel.close()


def _settings(policy):
    path = policy.archive_config.parent / "server.toml"
    tls = policy.listener.tls
    text = (
        f'schema_version=1\narchive_config="{policy.archive_config}"\n'
        f'state_directory="{policy.state_directory}"\n'
        f'[credentials.writer]\nfile="{policy.credentials.writer.file}"\n'
        f'[listener]\nunix_socket="{policy.listener.unix_socket}"\n'
        f"unix_enabled={str(policy.listener.unix_enabled).lower()}\n"
        f"tcp_enabled={str(policy.listener.tcp_enabled).lower()}\n"
        f'tcp_host="{policy.listener.tcp_host}"\ntcp_port={policy.listener.tcp_port}\n'
    )
    if tls:
        text += (
            f'[listener.tls]\ncertificate="{tls.certificate}"\nprivate_key="{tls.private_key}"\n'
        )
    path.write_text(text)
    return path


def _environment(count):
    return {"LISTEN_FDS": str(count), "LISTEN_FDNAMES": ":".join(["hfcache-api"] * count)}


def _ready(process, client):
    deadline = time.monotonic() + 10
    while True:
        try:
            response = client.get(
                "/api/v1/capabilities", headers={"Authorization": "Bearer " + TOKEN}
            )
            response.raise_for_status()
            return response.json()["envelope"]["data"]["instance_id"]
        except httpx.HTTPError:
            if process.poll() is not None or time.monotonic() >= deadline:
                process.terminate()
                stdout, stderr = process.communicate(timeout=10)
                pytest.fail(f"activated API did not start: {stdout!r} {stderr!r}")
            time.sleep(0.02)


@pytest.mark.parametrize("mode", ["unix", "tcp", "both", "reverse", "tls", "pidfd"])
def test_actual_activation_uses_exact_sockets_one_lifespan_and_preserves_manager_names(
    policy, tmp_path, mode
):
    with _bound(policy, unix=mode != "tcp", tcp=mode != "unix") as (base, channels):
        configured = base
        if mode == "tls":
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
            configured = validate_server_config_mapping(
                configured.model_dump(mode="json")
                | {
                    "listener": configured.listener.model_dump(mode="json")
                    | {"tls": {"certificate": str(certificate), "private_key": str(key)}}
                }
            )
        descriptors = [channel.fileno() for channel in channels]
        if mode == "reverse":
            descriptors.reverse()
        environment = _environment(len(descriptors))
        if mode == "pidfd":
            environment["ACTIVATION_TEST_PIDFD"] = "valid"
        before = (
            configured.listener.unix_socket.stat() if configured.listener.unix_enabled else None
        )
        with activated_process(
            ["-c", _DRIVER, str(_settings(configured))], descriptors, environment=environment
        ) as process:
            instances = []
            if configured.listener.unix_enabled:
                with httpx.Client(
                    transport=UnixHTTPTransport(
                        configured.listener.unix_socket,
                        limits=httpx.Limits(max_connections=2, max_keepalive_connections=1),
                    ),
                    base_url="http://localhost",
                    timeout=0.2,
                    trust_env=False,
                ) as client:
                    instances.append(_ready(process, client))
            if configured.listener.tcp_enabled:
                tls = configured.listener.tls
                verify = ssl.create_default_context(cafile=tls.certificate) if tls else True
                scheme = "https" if tls else "http"
                with httpx.Client(
                    base_url=f"{scheme}://127.0.0.1:{configured.listener.tcp_port}",
                    timeout=0.2,
                    trust_env=False,
                    verify=verify,
                ) as client:
                    instances.append(_ready(process, client))
            assert len(set(instances)) == 1
            process.terminate()
            stdout, stderr = process.communicate(timeout=10)
            # Uvicorn restores/replays SIGTERM after its lifespan drains. Systemd
            # treats this signal as a clean service stop (decision 121).
            assert process.returncode in {0, -signal.SIGTERM}
            assert TOKEN.encode() not in stdout + stderr
        # The manager still has listening copies and retains the Unix inode.
        assert all(
            channel.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) for channel in channels
        )
        if before is not None:
            after = configured.listener.unix_socket.stat()
            assert (after.st_dev, after.st_ino, after.st_mode) == (
                before.st_dev,
                before.st_ino,
                before.st_mode,
            )
        assert not (tmp_path / "archive").exists()
        assert [path.name for path in configured.state_directory.iterdir()] == [".lock"]


@pytest.mark.parametrize(
    "override",
    [
        {"ACTIVATION_TEST_PID": "0"},
        {"ACTIVATION_TEST_PID": "missing"},
        {"LISTEN_FDS": "0"},
        {"LISTEN_FDS": "2"},
        {"LISTEN_FDS": "01"},
        {"LISTEN_FDS": "999999999999999999999999"},
        {"LISTEN_FDNAMES": ""},
        {"LISTEN_FDNAMES": "wrong"},
        {"LISTEN_FDNAMES": "hfcache-api:hfcache-api"},
        {"ACTIVATION_TEST_PIDFD": "invalid"},
    ],
)
def test_partial_or_wrong_activation_never_falls_back_to_rebinding(policy, tmp_path, override):
    with _bound(policy, tcp=False) as (configured, channels):
        inode = configured.listener.unix_socket.stat().st_ino
        with activated_process(
            ["-c", _DRIVER, str(_settings(configured))],
            [channel.fileno() for channel in channels],
            environment=_environment(1) | override,
        ) as process:
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 20
            assert stderr == b"HFAPI009"
            assert stdout == b""
        assert configured.listener.unix_socket.stat().st_ino == inode
        assert not configured.state_directory.exists()
        assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize("fault", ["mode", "wrong-path", "wrong-port", "duplicate"])
def test_descriptor_address_identity_and_permissions_are_checked_before_startup(policy, fault):
    with _bound(policy) as (base, channels):
        configured = base
        descriptors = [channel.fileno() for channel in channels]
        if fault == "mode":
            configured.listener.unix_socket.chmod(0o666)
        elif fault == "wrong-path":
            configured = configured.model_copy(
                update={
                    "listener": configured.listener.model_copy(
                        update={
                            "unix_socket": configured.listener.unix_socket.with_name("other.sock")
                        }
                    )
                }
            )
        elif fault == "wrong-port":
            configured = configured.model_copy(
                update={
                    "listener": configured.listener.model_copy(
                        update={"tcp_port": configured.listener.tcp_port - 1}
                    )
                }
            )
        else:
            descriptors = [channels[0].fileno()] * 2
        with activated_process(
            ["-c", _DRIVER, str(_settings(configured))],
            descriptors,
            environment=_environment(2),
        ) as process:
            _, stderr = process.communicate(timeout=10)
            assert process.returncode == 20
            assert stderr == b"HFAPI009"
        assert not configured.state_directory.exists()


@pytest.mark.parametrize("kind", ["datagram", "connected", "file"])
def test_activation_requires_listening_stream_descriptors_without_deleting_evidence(policy, kind):
    channels = []
    evidence_handle = None
    evidence = policy.listener.unix_socket
    try:
        if kind == "datagram":
            channel = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            channels.append(channel)
            channel.bind(str(evidence))
            evidence.chmod(0o660)
            descriptor = channel.fileno()
        elif kind == "connected":
            channels.extend(socket.socketpair())
            descriptor = channels[0].fileno()
        else:
            evidence.write_text("unexplained evidence")
            evidence_handle = evidence.open("rb")
            descriptor = evidence_handle.fileno()
        with activated_process(
            ["-c", _DRIVER, str(_settings(policy))], [descriptor], environment=_environment(1)
        ) as process:
            _, stderr = process.communicate(timeout=10)
            assert process.returncode == 20
            assert stderr == b"HFAPI009"
        if kind == "file":
            assert evidence.read_text() == "unexplained evidence"
        elif kind == "datagram":
            assert stat.S_ISSOCK(evidence.stat().st_mode)
        assert not policy.state_directory.exists()
    finally:
        if evidence_handle is not None:
            evidence_handle.close()
        for channel in channels:
            channel.close()
