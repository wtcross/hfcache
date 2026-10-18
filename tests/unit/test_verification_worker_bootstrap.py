"""Worker activation resolves account peers before credential-free offline startup."""

import os
import pwd
import signal
import socket
import subprocess
import sys
import time

import pytest

from hfcache.api.lifecycle import instance_lock
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


# This fixture substitutes only the PID-namespace precondition. Everything after
# that check is the real entrypoint, Unix kernel I/O, store and notification. It
# is not proof of PID1/SELinux; actual container proof belongs to REL-013.
_OWNED_DRIVER = """
import os,signal,stat,sys
import hfcache.verification_worker as bootstrap
case=sys.argv.pop(1)
original_check=bootstrap._valid_bootstrap
def namespace_precondition(options):
 original_pid=os.getpid
 os.getpid=lambda:1
 try: return original_check(options)
 finally: os.getpid=original_pid
bootstrap._valid_bootstrap=namespace_precondition
if case in {'nss','stop-during-nss'}:
 original_nss=bootstrap.pwd.getpwnam
 def nss(name):
  assert stat.S_ISSOCK(os.fstat(3).st_mode)
  descriptor=os.open('/dev/null',os.O_RDONLY)
  assert descriptor>3
  os.close(descriptor)
  if case=='stop-during-nss': os.kill(os.getpid(),signal.SIGTERM)
  return original_nss(name)
 bootstrap.pwd.getpwnam=nss
if case in {'stop-during-init','fail-init'}:
 original_run=bootstrap._run
 def run(*arguments):
  assert os.environ['HF_HUB_OFFLINE']=='1'
  import hfcache.verification_executor as executor
  original_worker=executor.VerificationWorker
  class Worker(original_worker):
   def __init__(self,*args,**kwargs):
    super().__init__(*args,**kwargs)
    if case=='stop-during-init': os.kill(os.getpid(),signal.SIGTERM)
    else: raise OSError
  executor.VerificationWorker=Worker
  return original_run(*arguments)
 bootstrap._run=run
raise SystemExit(bootstrap.main())
"""


@pytest.fixture
def owned_worker(tmp_path):
    config = tmp_path / "owned.toml"
    config.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{ARCHIVE_ID}"\n'
    )
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    path = private / "owned.sock"
    arguments = [
        "--container-listener",
        "--config",
        str(config),
        "--state-directory",
        str(tmp_path / "state"),
        "--socket",
        str(path),
    ]
    return arguments, path


def _owned_process(arguments, address, *, case="normal", environment=None, descriptors=()):
    return subprocess.Popen(
        [sys.executable, "-c", _OWNED_DRIVER, case, *arguments],
        env={"PATH": os.environ["PATH"], "LANG": "C.UTF-8", "NOTIFY_SOCKET": str(address)}
        | (environment or {}),
        pass_fds=descriptors,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@pytest.mark.parametrize("case", ["normal", "nss"])
@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_owned_entrypoint_after_namespace_precondition_is_ready_then_cleans_exact_socket(
    owned_worker, tmp_path, case, signum
):
    arguments, path = owned_worker
    if case == "nss":
        arguments += ["--api-user", pwd.getpwuid(os.geteuid()).pw_name]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notify:
        notify.bind(str(tmp_path / "notify"))
        notify.settimeout(10)
        process = _owned_process(arguments, tmp_path / "notify", case=case)
        try:
            assert notify.recv(128) == b"READY=1"
            client = VerificationClient(path, timeout_seconds=0.5, expected_archive_id=ARCHIVE_ID)
            client.check_available()
            assert [entry.name for entry in (tmp_path / "state").iterdir()] == [".lock"]
            assert (tmp_path / "state.instance.lock").exists()
            process.send_signal(signum)
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0
            assert stdout == stderr == b""
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)
    assert not path.exists()
    assert path.parent.is_dir()
    assert not (tmp_path / "archive").exists()
    assert (tmp_path / "state.instance.lock").exists()


def test_owned_entrypoint_refuses_real_non_pid1_without_any_bootstrap_side_effects(
    owned_worker, tmp_path
):
    arguments, path = owned_worker
    process = subprocess.run(
        [sys.executable, "-m", "hfcache.verification_worker", *arguments],
        env={"PATH": os.environ["PATH"], "LANG": "C.UTF-8"},
        capture_output=True,
        check=False,
    )
    assert process.returncode == 20
    assert process.stdout == process.stderr == b""
    assert not path.exists()
    assert not (tmp_path / "state").exists()


def test_owned_stop_during_nss_never_becomes_late_readiness(owned_worker, tmp_path):
    arguments, path = owned_worker
    arguments += ["--api-user", pwd.getpwuid(os.geteuid()).pw_name]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notify:
        notify.bind(str(tmp_path / "notify"))
        notify.settimeout(0.1)
        process = _owned_process(arguments, tmp_path / "notify", case="stop-during-nss")
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0
        assert stdout == stderr == b""
        with pytest.raises(TimeoutError):
            notify.recv(128)
    assert not path.exists()


@pytest.mark.parametrize(
    "name", ["LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES", "LISTEN_PIDFDID", "LISTEN_UNRECOGNIZED"]
)
def test_owned_mode_rejects_every_activation_field_before_new_resources(
    owned_worker, tmp_path, name
):
    arguments, path = owned_worker
    process = _owned_process(arguments, tmp_path / "unused", environment={name: "private-value"})
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 20
    assert stdout == stderr == b""
    assert not path.exists()
    assert not (tmp_path / "state").exists()


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
def test_owned_mode_rejects_ambient_credentials_before_new_resources(owned_worker, tmp_path, name):
    arguments, path = owned_worker
    process = _owned_process(arguments, tmp_path / "unused", environment={name: "private-value"})
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 20
    assert stdout == stderr == b""
    assert not path.exists()
    assert not (tmp_path / "state").exists()


def test_owned_mode_refuses_inherited_file_before_binding_or_state(owned_worker, tmp_path):
    arguments, path = owned_worker
    evidence = tmp_path / "credential-evidence"
    evidence.write_bytes(b"unexplained inherited bytes")
    with evidence.open("rb") as descriptor:
        process = _owned_process(arguments, tmp_path / "unused", descriptors=(descriptor.fileno(),))
        stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 20
    assert stdout == stderr == b""
    assert evidence.read_bytes() == b"unexplained inherited bytes"
    assert not path.exists()
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize("where", ["inside", "same", "ancestor"])
def test_owned_socket_archive_overlap_refuses_before_instance_state_or_parent_open(
    owned_worker, tmp_path, where
):
    arguments, _path = owned_worker
    target = (
        tmp_path / "archive" / "unsafe.sock"
        if where == "inside"
        else (tmp_path / "archive" if where == "same" else tmp_path)
    )
    arguments[arguments.index("--socket") + 1] = str(target)
    process = _owned_process(arguments, tmp_path / "unused")
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 20
    assert stdout == stderr == b""
    assert not (tmp_path / "state").exists()
    assert not (tmp_path / "state.instance.lock").exists()
    assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize("case", ["stop-during-init", "fail-init"])
def test_readiness_never_precedes_worker_initialization_or_follows_shutdown(
    owned_worker, tmp_path, case
):
    arguments, path = owned_worker
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notify:
        notify.bind(str(tmp_path / "notify"))
        notify.settimeout(0.1)
        process = _owned_process(arguments, tmp_path / "notify", case=case)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == (0 if case == "stop-during-init" else 20)
        assert stdout == stderr == b""
        with pytest.raises(TimeoutError):
            notify.recv(128)
    assert not path.exists()
    assert (tmp_path / "state.instance.lock").exists()
    assert [entry.name for entry in (tmp_path / "state").iterdir()] == [".lock"]


def test_owned_notification_failure_cleans_new_socket_but_preserves_local_state(
    owned_worker, tmp_path
):
    arguments, path = owned_worker
    process = _owned_process(arguments, tmp_path / "missing-notify")
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 20
    assert stdout == stderr == b""
    assert not path.exists()
    assert (tmp_path / "state.instance.lock").exists()
    assert [entry.name for entry in (tmp_path / "state").iterdir()] == [".lock"]


def test_busy_instance_refuses_before_owned_path_creation(owned_worker, tmp_path):
    arguments, path = owned_worker
    instance = tmp_path / "state.instance.lock"
    with instance_lock(instance):
        inode = instance.stat().st_ino
        process = _owned_process(arguments, tmp_path / "unused")
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 20
        assert stdout == stderr == b""
        assert instance.stat().st_ino == inode
    assert not path.exists()
    assert not (tmp_path / "state").exists()


def test_crash_keeps_owned_socket_and_restart_refuses_it_without_cleanup(owned_worker, tmp_path):
    arguments, path = owned_worker
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notify:
        notify.bind(str(tmp_path / "notify"))
        notify.settimeout(10)
        process = _owned_process(arguments, tmp_path / "notify")
        try:
            assert notify.recv(128) == b"READY=1"
            inode = path.stat().st_ino
            process.kill()  # Explicit crash of a disposable worker with no admitted work.
            process.communicate(timeout=10)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)
        assert path.stat().st_ino == inode
        restarted = _owned_process(arguments, tmp_path / "notify")
        stdout, stderr = restarted.communicate(timeout=10)
        assert restarted.returncode == 20
        assert stdout == stderr == b""
        assert path.stat().st_ino == inode
    assert [entry.name for entry in (tmp_path / "state").iterdir()] == [".lock"]
