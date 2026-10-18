"""Worker activation resolves account peers before credential-free offline startup."""

import os
import pwd
import socket
import time

import pytest

from hfcache.errors import OperationError
from hfcache.verification_protocol import VerificationClient
from tests.socket_activation import activated_process
from tests.unit.test_verification_executor import ARCHIVE_ID


@pytest.fixture
def worker(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{ARCHIVE_ID}"\n'
    )
    address = tmp_path / "verify.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(address))
        address.chmod(0o600)
        listener.listen(8)
        arguments = [
            "-m",
            "hfcache.verification_worker",
            "--config",
            str(config),
            "--state-directory",
            str(tmp_path / "state"),
            "--socket",
            str(address),
        ]
        yield arguments, address, listener


def _environment():
    return {"LISTEN_FDS": "1", "LISTEN_FDNAMES": "hfcache-verification"}


@pytest.mark.parametrize("identity", ["default", "user", "uid", "pidfd"])
def test_worker_accepts_account_or_default_euid_with_named_activation(worker, tmp_path, identity):
    arguments, address, listener = worker
    environment = _environment()
    if identity == "user":
        arguments += ["--api-user", pwd.getpwuid(os.geteuid()).pw_name]
    elif identity == "uid":
        arguments += ["--api-uid", str(os.geteuid())]
    elif identity == "pidfd":
        environment["ACTIVATION_TEST_PIDFD"] = "valid"
    inode = address.stat().st_ino
    with activated_process(arguments, [listener.fileno()], environment=environment) as process:
        client = VerificationClient(address, timeout_seconds=0.1, expected_archive_id=ARCHIVE_ID)
        deadline = time.monotonic() + 10
        while True:
            try:
                client.check_available()
                break
            except OperationError:
                if process.poll() is not None or time.monotonic() >= deadline:
                    process.terminate()
                    stdout, stderr = process.communicate(timeout=10)
                    pytest.fail(f"activated worker did not start: {stdout!r} {stderr!r}")
                time.sleep(0.02)
        process.terminate()
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0
        assert stdout == stderr == b""
    assert listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1
    assert address.stat().st_ino == inode
    assert [path.name for path in (tmp_path / "state").iterdir()] == [".lock"]
    assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize(
    "name",
    [
        "HF_TOKEN",
        "HUGGING_FACE_HUB_TOKEN",
        "HUGGINGFACE_HUB_TOKEN",
        "HUGGINGFACEHUB_API_TOKEN",
        "CREDENTIALS_DIRECTORY",
        "HF_TOKEN_PATH",
        "HFCACHE_API_TOKEN",
        "HFCACHE_MCP_TOKEN",
    ],
)
def test_worker_refuses_every_supported_ambient_credential_before_policy_or_state(
    worker, tmp_path, name
):
    arguments, address, listener = worker
    secret = "synthetic-credential-that-must-not-appear"
    with activated_process(
        arguments, [listener.fileno()], environment=_environment() | {name: secret}
    ) as process:
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 20
        assert secret.encode() not in stdout + stderr
    assert address.exists()
    assert not (tmp_path / "state").exists()
    assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize(
    "override",
    [
        {"ACTIVATION_TEST_PID": "0"},
        {"ACTIVATION_TEST_PID": "missing"},
        {"LISTEN_FDS": "2"},
        {"LISTEN_FDNAMES": ""},
        {"LISTEN_FDNAMES": "hfcache-api"},
        {"ACTIVATION_TEST_PIDFD": "invalid"},
    ],
)
def test_worker_refuses_wrong_activation_identity_before_creating_state(worker, tmp_path, override):
    arguments, _, listener = worker
    with activated_process(
        arguments, [listener.fileno()], environment=_environment() | override
    ) as process:
        process.communicate(timeout=10)
        assert process.returncode == 20
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize(
    "flags", [["--api-user", "nonexistent-hfcache-fixture-account"], ["--api-uid", "-1"]]
)
def test_invalid_peer_identity_is_refused_without_runtime_state(worker, tmp_path, flags):
    arguments, _, listener = worker
    with activated_process(
        [*arguments, *flags], [listener.fileno()], environment=_environment()
    ) as process:
        process.communicate(timeout=10)
        assert process.returncode == 20
    assert not (tmp_path / "state").exists()


def test_peer_user_and_uid_flags_are_mutually_exclusive(worker, tmp_path):
    arguments, _, listener = worker
    with activated_process(
        [
            *arguments,
            "--api-uid",
            str(os.geteuid()),
            "--api-user",
            pwd.getpwuid(os.geteuid()).pw_name,
        ],
        [listener.fileno()],
        environment=_environment(),
    ) as process:
        process.communicate(timeout=10)
        assert process.returncode == 2
    assert not (tmp_path / "state").exists()
