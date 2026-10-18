"""Decision 128's owned listener uses kernel paths, identities and bounded readiness.

These local kernel/process fixtures do not claim container PID1, SELinux access
or OS egress enforcement. The actual image/user-manager proof is separate.
"""

import fcntl
import json
import os
import socket
import stat
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from typing import cast

import pytest

from hfcache import verification_listener
from hfcache.api.lifecycle import instance_lock
from hfcache.api.operations import OperationStore
from hfcache.config import load_config
from hfcache.errors import OperationError
from hfcache.identity import new_run_id
from hfcache.locking import exclusive_lock
from hfcache.paths import ArchiveLayout
from hfcache.server_config import InstalledPolicy
from hfcache.services.context import ServiceResult
from hfcache.services.requests import VerificationRequest
from hfcache.verification_executor import VerificationWorker, serve_worker, validate_listener
from hfcache.verification_listener import notify_ready, owned_listener
from hfcache.verification_protocol import VerificationClient, VerificationScope, WorkerRequest
from tests.unit.test_verification import MODEL, SHA_A, publish
from tests.unit.test_verification_executor import policy as archive_policy  # noqa: F401
from tests.unit.test_verify_command import write_run_report

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"


@pytest.fixture
def address(tmp_path):
    parent = tmp_path / "private"
    parent.mkdir(mode=0o700)
    return parent / "worker.sock"


def test_owned_kernel_listener_is_private_pinned_validated_and_exactly_removed(address):
    before = os.umask(0)
    try:
        with (
            socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
            owned_listener(channel, address) as owned,
        ):
            assert stat.S_IMODE(address.stat().st_mode) == 0o600
            assert (address.stat().st_uid, address.stat().st_gid) == (
                os.geteuid(),
                os.getegid(),
            )
            assert (address.stat().st_dev, address.stat().st_ino) == owned.identity
            assert channel.getsockname() == owned.bound_address
            assert owned.bound_address.startswith("/proc/self/fd/")
            assert channel.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1
            validate_listener(
                channel,
                address,
                bound_address=owned.bound_address,
                owned_identity=owned.identity,
            )
            with pytest.raises(OperationError):
                validate_listener(channel, address)  # Native canonical proof is unchanged.
        assert not address.exists()
        assert address.parent.is_dir()
    finally:
        assert os.umask(before) == 0


@pytest.mark.parametrize("mode", [0o755, 0o770, 0o707, 0o2700])
def test_owned_parent_requires_exact_private_mode_without_changing_it(address, mode):
    address.parent.chmod(mode)
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
        pytest.raises(OSError, match="bootstrap refused"),
        owned_listener(channel, address),
    ):
        pytest.fail("unprotected parent accepted")
    assert stat.S_IMODE(address.parent.stat().st_mode) == mode
    assert not address.exists()


@pytest.mark.parametrize("identity", ["uid", "gid"])
def test_owned_parent_requires_effective_uid_and_gid(address, monkeypatch, identity):
    actual = os.geteuid() if identity == "uid" else os.getegid()
    monkeypatch.setattr(os, "geteuid" if identity == "uid" else "getegid", lambda: actual + 1)
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
        pytest.raises(OSError, match="bootstrap refused"),
        owned_listener(channel, address),
    ):
        pytest.fail("untrusted parent accepted")
    assert not address.exists()


@pytest.mark.parametrize("kind", ["file", "hardlink", "fifo", "directory", "symlink", "socket"])
def test_every_existing_path_is_preserved_including_stale_socket(address, kind):
    if kind == "file":
        address.write_bytes(b"unexplained evidence")
    elif kind == "hardlink":
        source = address.parent / "evidence"
        source.write_bytes(b"unexplained evidence")
        address.hardlink_to(source)
    elif kind == "fifo":
        os.mkfifo(address)
    elif kind == "directory":
        address.mkdir()
    elif kind == "symlink":
        address.symlink_to(address.parent / "absent-target")
    else:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stale:
            stale.bind(str(address))
    before = address.lstat()
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
        pytest.raises(OSError, match="bootstrap refused"),
        owned_listener(channel, address),
    ):
        pytest.fail("existing path accepted")
    after = address.lstat()
    assert (before.st_dev, before.st_ino, before.st_mode) == (
        after.st_dev,
        after.st_ino,
        after.st_mode,
    )


def test_parent_symlink_is_refused_without_following(address):
    alias = address.parent.parent / "alias"
    alias.symlink_to(address.parent, target_is_directory=True)
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
        pytest.raises(NotADirectoryError),
        owned_listener(channel, alias / address.name),
    ):
        pytest.fail("parent alias followed")
    assert list(address.parent.iterdir()) == []


@pytest.mark.parametrize("kind", ["nfs", "nfs4", "autofs", "cifs", "unknown"])
def test_network_or_unknown_parent_filesystem_refuses_before_directory_open(
    address, tmp_path, monkeypatch, kind
):
    table = tmp_path / "mountinfo"
    table.write_text(
        f"1 0 0:1 / / rw - ext4 /dev/local rw\n2 1 0:2 / {address.parent} rw - {kind} fixture rw\n"
    )
    monkeypatch.setattr(verification_listener, "MOUNTINFO", table)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:

        def forbidden(*_args, **_kwargs):
            pytest.fail("unproven IPC parent was opened")

        with monkeypatch.context() as context:
            context.setattr(os, "open", forbidden)
            with (
                pytest.raises(OSError, match="bootstrap refused"),
                owned_listener(channel, address),
            ):
                pytest.fail("unproven parent accepted")
    assert not address.exists()


@pytest.mark.parametrize("body", [b"", b"malformed\n", b"\xff", b"x" * 1048577])
def test_missing_malformed_or_oversized_mount_accounting_refuses(
    address, tmp_path, monkeypatch, body
):
    table = tmp_path / "mountinfo"
    table.write_bytes(body)
    monkeypatch.setattr(verification_listener, "MOUNTINFO", table)
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
        pytest.raises((OSError, UnicodeError)),
        owned_listener(channel, address),
    ):
        pytest.fail("unproven accounting accepted")
    assert not address.exists()


def test_escaped_mountpoint_is_decoded_before_filesystem_selection(address, tmp_path, monkeypatch):
    parent = tmp_path / "private directory"
    parent.mkdir(mode=0o700)
    table = tmp_path / "mountinfo"
    escaped = str(parent).replace(" ", r"\040")
    table.write_text(
        f"1 0 0:1 / / rw - ext4 /dev/local rw\n2 1 0:2 / {escaped} rw - nfs4 fixture rw\n"
    )
    monkeypatch.setattr(verification_listener, "MOUNTINFO", table)
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
        pytest.raises(OSError, match="bootstrap refused"),
        owned_listener(channel, parent / address.name),
    ):
        pytest.fail("escaped network parent accepted")
    assert list(parent.iterdir()) == []


@pytest.mark.parametrize("replacement", ["file", "socket"])
def test_replacement_identity_survives_validation_and_cleanup(address, replacement):
    displaced = address.with_suffix(".displaced")
    other = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        with (
            socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
            owned_listener(channel, address) as owned,
        ):
            address.rename(displaced)
            if replacement == "file":
                address.write_bytes(b"replacement evidence")
            else:
                other.bind(str(address))
            replacement_inode = address.lstat().st_ino
            with pytest.raises(OperationError):
                validate_listener(
                    channel,
                    address,
                    bound_address=owned.bound_address,
                    owned_identity=owned.identity,
                )
        assert address.lstat().st_ino == replacement_inode
        assert displaced.is_socket()
        if replacement == "file":
            assert address.read_bytes() == b"replacement evidence"
    finally:
        other.close()


def test_owned_bound_spelling_and_inode_must_be_supplied_together(address):
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
        owned_listener(channel, address) as owned,
    ):
        with pytest.raises(OperationError):
            validate_listener(channel, address, bound_address=owned.bound_address)
        with pytest.raises(OperationError):
            validate_listener(channel, address, owned_identity=owned.identity)
        with pytest.raises(OperationError):
            validate_listener(
                channel, address, bound_address=str(address), owned_identity=owned.identity
            )


def test_listen_failure_cleans_only_its_new_inode_and_restores_umask(address):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:

        def fail(_backlog):
            message = "synthetic listen failure"
            raise OSError(message)

        proxy = SimpleNamespace(bind=channel.bind, close=channel.close, listen=fail)
        previous = os.umask(0o027)
        try:
            with (
                pytest.raises(OSError, match="synthetic listen failure"),
                owned_listener(cast("socket.socket", proxy), address),
            ):
                pytest.fail("listen failure lost")
            assert not address.exists()
            assert os.umask(0o027) == 0o027
        finally:
            os.umask(previous)


@pytest.mark.parametrize("abstract", [False, True])
def test_readiness_uses_actual_unix_datagram_and_stops_before_notification(
    tmp_path, monkeypatch, abstract
):
    name = f"hfcache-notify-{new_run_id()}" if abstract else str(tmp_path / "notify")
    address = "\0" + name if abstract else name
    setting = "@" + name if abstract else name
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as receiver:
        receiver.bind(address)
        receiver.settimeout(0.05)
        monkeypatch.setenv("NOTIFY_SOCKET", setting)
        stop = threading.Event()
        assert notify_ready(stop)
        assert receiver.recv(128) == b"READY=1"
        stop.set()
        assert not notify_ready(stop)
        with pytest.raises(TimeoutError):
            receiver.recv(128)


@pytest.mark.parametrize(
    "setting", [None, "", "relative", "http://remote/", "/bad\0socket", "@" + "x" * 108]
)
def test_unusable_notification_refuses_without_rejected_value_echo(monkeypatch, setting):
    if setting is None:
        monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    else:
        monkeypatch.setenv(
            "NOTIFY_SOCKET", setting
        ) if "\0" not in setting else monkeypatch.setattr(os, "environ", {"NOTIFY_SOCKET": setting})
    with pytest.raises(OSError, match="private listener bootstrap refused"):
        notify_ready(threading.Event())


def test_real_child_reserves_fd3_without_inheriting_or_importing_backend():
    code = """
import json,os,sys
from hfcache.verification_listener import reserve_listener
with reserve_listener() as listener:
 print(json.dumps({'fd':listener.fileno(),'inheritable':os.get_inheritable(3),
  'backend':any(name.startswith(('huggingface_hub','hfcache.services','hfcache.api'))
                for name in sys.modules)}))
"""
    process = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert json.loads(process.stdout) == {"fd": 3, "inheritable": False, "backend": False}
    assert process.stderr == ""


def test_fd3_reservation_never_clobbers_an_unexplained_open_file(tmp_path):
    path = tmp_path / "evidence"
    path.write_bytes(b"preserved descriptor bytes")
    code = """
import os,sys
from hfcache.verification_listener import reserve_listener
fd=os.open(sys.argv[1],os.O_RDONLY)
if fd!=3: os.dup2(fd,3); os.close(fd)
before=os.fstat(3)
try: reserve_listener()
except OSError: pass
else: raise AssertionError('unexpected descriptor authority')
assert os.fstat(3).st_ino==before.st_ino
assert os.read(3,128)==b'preserved descriptor bytes'
"""
    process = subprocess.run(
        [sys.executable, "-c", code, str(path)], capture_output=True, check=False
    )
    assert process.returncode == 0
    assert process.stdout == process.stderr == b""
    assert path.read_bytes() == b"preserved descriptor bytes"


def test_joined_work_retains_socket_store_and_instance_lock_until_actual_completion(
    tmp_path, address
):
    path = tmp_path / "policy.toml"
    path.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{ARCHIVE_ID}"\n'
    )
    config = load_config(path)
    policy = InstalledPolicy(path, config.storage.archive_root, config.storage.archive_id)
    entered, release, stop, finished = (threading.Event() for _ in range(4))
    instance = tmp_path / "worker.instance.lock"
    store_path = tmp_path / "state"
    result_id = new_run_id()

    def execute(_snapshot, _context, _request):
        with exclusive_lock(tmp_path / "domain.lock", command="verify", wait_seconds=30):
            entered.set()
            assert release.wait(timeout=10)
            return ServiceResult("verify --full", {"synthetic": True})

    def run():
        with instance_lock(instance), OperationStore(store_path) as store:
            worker = VerificationWorker(policy, store, execute=execute)
            with (
                socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
                owned_listener(channel, address),
            ):
                worker.handle(
                    WorkerRequest(
                        schema_version=1,
                        action="submit",
                        operation_id=result_id,
                        config_fingerprint=policy.snapshot().fingerprint,
                        scope=VerificationScope(mode="full"),
                        lock_deadline=time.monotonic() + 30,
                    )
                )
                serve_worker(channel, worker, expected_uid=os.geteuid(), stop=stop)
        finished.set()

    thread = threading.Thread(target=run)
    thread.start()
    try:
        assert entered.wait(timeout=10)
        inode = address.stat().st_ino
        stop.set()
        assert not finished.wait(timeout=0.1)
        assert address.stat().st_ino == inode
        with instance.open("rb") as contender, pytest.raises(BlockingIOError):
            fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        release.set()
        thread.join(timeout=10)
    assert not thread.is_alive()
    assert finished.is_set()
    assert not address.exists()
    assert instance.exists()
    with OperationStore(store_path) as store:
        assert store.result(result_id).data == {"synthetic": True}


@pytest.mark.parametrize("mode", ["new", "full", "revision"])
def test_owned_listener_runs_complete_guarded_verification_modes_without_hub(
    request, tmp_path, address, monkeypatch, mode
):
    policy = request.getfixturevalue("archive_policy")
    layout = ArchiveLayout(policy.root)
    published = publish(layout)
    _, run_id = write_run_report(
        layout, commit_sha=published.commit_sha, publication_id=published.publication_id
    )

    def forbidden(*_args, **_kwargs):
        pytest.fail("owned listener verification touched Hub or credentials")

    monkeypatch.setattr("hfcache.services.commands.resolve_token", forbidden)
    monkeypatch.setattr("hfcache.services.commands.HubClient", forbidden)
    scope = VerificationRequest(
        new=mode == "new",
        full=mode == "full",
        revision=f"{MODEL.selector}@{SHA_A}" if mode == "revision" else None,
        run_id=run_id if mode == "new" else None,
    )
    stop = threading.Event()
    with (
        instance_lock(tmp_path / "worker.instance.lock"),
        OperationStore(tmp_path / "worker") as store,
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel,
        owned_listener(channel, address) as owned,
    ):
        validate_listener(
            channel, address, bound_address=owned.bound_address, owned_identity=owned.identity
        )
        thread = threading.Thread(
            target=serve_worker,
            args=(channel, VerificationWorker(policy, store)),
            kwargs={"expected_uid": os.geteuid(), "stop": stop, "timeout_seconds": 0.2},
        )
        thread.start()
        try:
            client = VerificationClient(address, timeout_seconds=1, poll_seconds=0.01)
            client.check_available()
            operation_id = new_run_id()
            result = client.execute(operation_id, scope, policy.snapshot().fingerprint, 10)
            assert result.exit_code == 0
            assert result.data["mode"] == mode
            receipt = store.get(operation_id)
            assert receipt.domain_run_id == result.run_id
            assert store.result(operation_id) == result
            assert client.status(operation_id, receipt.config_fingerprint).envelope == result
            assert (layout.root / result.data["report"]).is_file()
        finally:
            stop.set()
            thread.join(timeout=10)
            assert not thread.is_alive()
    assert not address.exists()
