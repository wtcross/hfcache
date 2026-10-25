"""Decision150 client capacity/lifetime and protected-address refusal tests."""

import ast
import asyncio
import copy
import json
import os
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from hfcache import host_helper_client as client_module
from hfcache import host_protocol as protocol

DEPLOYMENT = "a" * 64
BOOT = "cf68ba1d-153b-41bc-8f0b-b0414512dc03"


class UnixTestBinding(client_module.EndpointBinding):
    """Actual Unix I/O seam, deliberately no claim of protected-root provenance."""

    def __init__(self, path, *, stall=None):
        self.path = path
        self.stall = stall
        self.entered = threading.Event()
        self.deployment_sha256 = DEPLOYMENT
        self.closed = False

    def connect(self, *, deadline, own_socket):
        self.entered.set()
        if self.stall is not None:
            self.stall.wait(2)
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        own_socket(connection)
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        connection.settimeout(protocol.remaining(deadline))
        connection.connect(str(self.path))
        return connection, None, protocol.PeerCredentials.from_socket(connection)

    def close(self):
        self.closed = True


@contextmanager
def unix_service(tmp_path, *, release=None, reply=None):
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    protocol.configure_listener(listener)
    path = tmp_path / "test-only.sock"
    listener.bind(str(path))
    listener.listen(8)
    listener.settimeout(0.05)
    stopped = threading.Event()
    accepted = []
    workers = []
    errors = []

    def handle(connection):
        with connection:
            try:
                with protocol.receive_exchange(
                    connection, lambda _peer, _seconds: None
                ) as exchange:
                    if release is not None:
                        release.wait(2)
                    exchange.dispatch(lambda *_: None)
                    exchange.respond(outcome="ok", body=reply or {"status": "observed"})
            except (protocol.HostProtocolError, OSError) as error:
                errors.append(type(error).__name__)

    def serve():
        while not stopped.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            accepted.append(connection)
            worker = threading.Thread(target=handle, args=(connection,))
            workers.append(worker)
            worker.start()

    server = threading.Thread(target=serve)
    server.start()
    try:
        yield path, accepted, errors
    finally:
        stopped.set()
        if release is not None:
            release.set()
        server.join(2)
        assert not server.is_alive()
        for worker in workers:
            worker.join(2)
            assert not worker.is_alive()
        listener.close()
        path.unlink()


def test_sync_and_async_status_use_real_single_exchange(tmp_path):
    with unix_service(tmp_path) as (path, accepted, _):
        binding = UnixTestBinding(path)
        client = client_module.HostHelperClient(binding, deployment_sha256=DEPLOYMENT)
        assert client.status() == {"status": "observed"}
        assert asyncio.run(client.async_status()) == {"status": "observed"}
        assert len(accepted) == 2
        assert client.close(timeout=2)
        assert binding.closed
        with pytest.raises(protocol.HostProtocolError, match="facts-unavailable"):
            client.status()


def test_eight_jobs_no_queue_and_cancellation_retains_slot_until_actual_exit(tmp_path):
    stall = threading.Event()
    binding = UnixTestBinding(tmp_path / "unused.sock", stall=stall)
    client = client_module.HostHelperClient(binding, deployment_sha256=DEPLOYMENT)

    async def exercise():
        jobs = [asyncio.create_task(client.async_status()) for _ in range(8)]
        for _ in range(100):
            if len(client._jobs) == 8 and len(client._workers) == 8:
                break
            await asyncio.sleep(0.005)
        assert len(client._jobs) == 8
        assert len(client._workers) == 8
        with pytest.raises(protocol.HostProtocolError, match="busy"):
            await client.async_status()
        jobs[0].cancel()
        with pytest.raises(asyncio.CancelledError):
            await jobs[0]
        assert len(client._jobs) == 8  # A nonpreemptible inspection still owns its slot.
        assert client.close(timeout=0.01) is False
        assert not binding.closed
        stall.set()
        await asyncio.gather(*jobs[1:], return_exceptions=True)

    try:
        asyncio.run(exercise())
    finally:
        stall.set()
        assert client.close(timeout=2)
    assert binding.closed
    assert not client._jobs
    assert all(not thread.is_alive() for thread in client._workers)


def test_async_cancel_shuts_down_exact_blocked_socket_promptly(tmp_path):
    release = threading.Event()
    with unix_service(tmp_path, release=release) as (path, accepted, _):
        client = client_module.HostHelperClient(UnixTestBinding(path), deployment_sha256=DEPLOYMENT)

        async def exercise():
            job = asyncio.create_task(client.async_status())
            for _ in range(100):
                if accepted:
                    break
                await asyncio.sleep(0.005)
            assert len(accepted) == 1
            job.cancel()
            with pytest.raises(asyncio.CancelledError):
                await job
            for _ in range(100):
                if not client._jobs:
                    break
                await asyncio.sleep(0.005)
            assert not client._jobs

        try:
            asyncio.run(exercise())
        finally:
            release.set()
            assert client.close(timeout=2)


def attestation() -> dict[str, object]:
    return {
        "schema_version": 1,
        "profile": "rootless",
        "deployment_sha256": DEPLOYMENT,
        "boot_id": BOOT,
        "parent": {"device": 1, "inode": 2, "uid": 65534, "gid": 981, "mode": 0o750},
        "peer": {"pid": 0, "uid": 65534, "gid": 65534},
    }


def test_rootless_without_independent_launcher_attestation_refuses_before_any_path(monkeypatch):
    monkeypatch.setattr(client_module, "_open_parent", lambda *_: pytest.fail("unattested path"))
    with pytest.raises(protocol.HostProtocolError, match="deployment-unverified"):
        client_module.EndpointBinding.from_startup(
            profile="rootless", deployment_sha256=DEPLOYMENT, api_host_gid=1234, environment={}
        )


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        (None, "schema_version", True),
        (None, "profile", "native"),
        (None, "deployment_sha256", "b" * 64),
        (None, "boot_id", "CF68BA1D-153B-41BC-8F0B-B0414512DC03"),
        (None, "extra", 1),
        ("parent", "device", True),
        ("parent", "inode", 0),
        ("parent", "uid", 0),
        ("parent", "gid", 65534),
        ("parent", "mode", 0o777),
        ("peer", "pid", 1),
        ("peer", "pid", False),
        ("peer", "uid", 0),
        ("peer", "gid", 981),
    ],
)
def test_rootless_attestation_closed_identity_shape(section, key, value):
    binding = object.__new__(client_module.EndpointBinding)
    binding.deployment_sha256 = DEPLOYMENT
    record = copy.deepcopy(attestation())
    target = cast("dict[str, object]", record[section]) if section else record
    target[key] = value
    with pytest.raises(protocol.HostProtocolError, match="deployment-unverified"):
        binding._validate_attestation(record)


def test_native_rejects_rootless_attestation_in_its_environment():
    with pytest.raises(protocol.HostProtocolError, match="deployment-unverified"):
        client_module.EndpointBinding.from_startup(
            profile="native",
            deployment_sha256=DEPLOYMENT,
            api_host_gid=os.getgid(),
            environment={"HFCACHE_HOST_HELPER_PARENT": json.dumps(attestation())},
        )


def test_fixed_parent_rejects_writable_ancestor_and_symlink(tmp_path, monkeypatch):
    parent = tmp_path / "api"
    parent.mkdir(mode=0o750)
    monkeypatch.setattr(client_module, "_PARENT", parent)
    with pytest.raises((protocol.HostProtocolError, OSError)):
        client_module.EndpointBinding.from_startup(
            profile="native", deployment_sha256=DEPLOYMENT, api_host_gid=981, environment={}
        )
    alias = tmp_path / "alias"
    alias.symlink_to(parent, target_is_directory=True)
    monkeypatch.setattr(client_module, "_PARENT", alias)
    with pytest.raises((protocol.HostProtocolError, OSError)):
        client_module._open_parent("native", 981)


@pytest.mark.parametrize("profile", ["native", "rootless"])
def test_parent_search_handles_support_relative_leaf_reads_without_directory_reads(
    tmp_path, monkeypatch, profile
):
    """Real descriptor I/O under a test-owned root; root/MAC proof is separate."""
    parent = tmp_path / "run" / "hfcache-host-helper" / "api"
    parent.mkdir(parents=True, mode=0o750)
    (parent / "binding.json").write_bytes(b"captured nonsecret binding")
    original_open = os.open
    original_directory = client_module._directory
    validations = []

    def search_only_open(path, flags, mode=0o777, *, dir_fd=None):
        if flags & os.O_DIRECTORY and not flags & os.O_PATH:
            raise PermissionError(13, "test search-only directory")
        return original_open(tmp_path if path == "/" else path, flags, mode, dir_fd=dir_fd)

    def test_owned_directory(info, *, uid, gid=None):
        validations.append((uid, gid))
        original_directory(info, uid=os.getuid(), gid=os.getgid() if gid is not None else None)

    monkeypatch.setattr(client_module.os, "open", search_only_open)
    monkeypatch.setattr(client_module, "_directory", test_owned_directory)
    descriptor = client_module._open_parent(profile, 983)
    try:
        assert os.fstat(descriptor).st_ino == parent.stat().st_ino
        leaf = os.open("binding.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptor)
        try:
            assert os.read(leaf, 4096) == b"captured nonsecret binding"
        finally:
            os.close(leaf)
    finally:
        os.close(descriptor)
    assert validations == [(0, None)] * 3 + [(65534, 981) if profile == "rootless" else (0, 983)]


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True])
def test_close_rejects_unbounded_timeout(tmp_path, timeout):
    client = client_module.HostHelperClient(
        UnixTestBinding(tmp_path / "unused"), deployment_sha256=DEPLOYMENT
    )
    try:
        with pytest.raises(protocol.HostProtocolError, match="invalid-request"):
            client.close(timeout=timeout)
    finally:
        assert client.close(timeout=2)


def runtime_binding() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "boot_id": BOOT,
        "helper_generation": "b" * 32,
        "deployment_sha256": DEPLOYMENT,
        "policy_sha256": "c" * 64,
        "parent": {"device": 1, "inode": 2, "uid": 0, "gid": 1234, "mode": 0o750},
        "helper": {"pid": 12345, "start_ticks": 98765, "uid": 0, "gid": 0},
    }


def unit_binding(record, monkeypatch):
    binding = object.__new__(client_module.EndpointBinding)
    binding.profile = "native"
    binding.boot_id = BOOT
    binding.api_host_gid = 1234
    binding.deployment_sha256 = DEPLOYMENT
    binding.parent_identity = (1, 2)
    monkeypatch.setattr(binding, "_read_binding", lambda: record)
    return binding


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        (None, "schema_version", True),
        (None, "boot_id", "8d70d379-c39a-4adc-a802-d52fc77d5658"),
        (None, "helper_generation", "C" * 32),
        (None, "deployment_sha256", "f" * 64),
        (None, "policy_sha256", "not-a-digest"),
        (None, "extra", 1),
        ("parent", "device", 3),
        ("parent", "inode", 3),
        ("parent", "uid", False),
        ("parent", "gid", 0),
        ("parent", "mode", 0o777),
        ("helper", "pid", 1),
        ("helper", "start_ticks", True),
        ("helper", "uid", False),
        ("helper", "gid", 1),
    ],
)
def test_runtime_binding_cannot_change_startup_authority(monkeypatch, section, key, value):
    record = runtime_binding()
    target = record[section] if section else record
    target[key] = value
    binding = unit_binding(record, monkeypatch)
    with pytest.raises(protocol.HostProtocolError, match="deployment-unverified"):
        binding._runtime_binding()


def test_helper_restart_and_policy_edit_keep_same_protected_parent(monkeypatch):
    record = runtime_binding()
    binding = unit_binding(record, monkeypatch)
    assert binding._runtime_binding() == record
    record["policy_sha256"] = "d" * 64
    record["helper_generation"] = "e" * 32
    record["helper"]["pid"] += 1
    record["helper"]["start_ticks"] += 1
    assert binding._runtime_binding() == record


def test_native_real_peer_pidfd_does_not_read_hidden_other_process_stat(tmp_path, monkeypatch):
    """Unit metadata projection plus real Unix peer/pidfd, no root-auth claim."""
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(tmp_path / "helper.sock"))
    listener.listen(1)
    (tmp_path / "helper.sock").chmod(0o660)
    parent = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    binding = object.__new__(client_module.EndpointBinding)
    binding.profile = "native"
    binding.api_host_gid = os.getgid()
    binding._parent = parent
    info = os.fstat(parent)
    binding.parent_identity = (info.st_dev, info.st_ino)
    record = runtime_binding()
    record["helper"]["pid"] = os.getpid()
    monkeypatch.setattr(binding, "_runtime_binding", lambda: record)
    monkeypatch.setattr(client_module, "_open_parent", lambda *_: os.dup(parent))
    original_stat = os.stat

    def projected_root_stat(path, *args, **kwargs):
        actual = original_stat(path, *args, **kwargs)
        if path == "helper.sock":
            fields = {name: getattr(actual, name) for name in dir(actual) if name.startswith("st_")}
            fields["st_uid"] = 0
            return SimpleNamespace(**fields)
        return actual

    monkeypatch.setattr(client_module.os, "stat", projected_root_stat)
    monkeypatch.setattr(
        protocol.PeerCredentials,
        "from_socket",
        classmethod(lambda _cls, _socket: protocol.PeerCredentials(os.getpid(), 0, 0)),
    )
    original_open = Path.open
    reads = []

    def hidden_other_process(path, *args, **kwargs):
        reads.append(str(path))
        if str(path).startswith("/proc/") and not str(path).startswith("/proc/self/fdinfo/"):
            message = "unit ProtectProc projection"
            raise PermissionError(message)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", hidden_other_process)
    try:
        connection, peer, _ = binding.connect(
            deadline=time.monotonic() + 1, own_socket=lambda _: None
        )
        connection.close()
        assert peer is not None
        peer.close()
        assert reads
        assert all(path.startswith("/proc/self/fdinfo/") for path in reads)
    finally:
        listener.close()
        binding.close()


def test_client_timeout_performs_one_attempt_without_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(client_module, "CLIENT_SECONDS", 0.03)
    release = threading.Event()
    with unix_service(tmp_path, release=release) as (path, accepted, _):
        client = client_module.HostHelperClient(UnixTestBinding(path), deployment_sha256=DEPLOYMENT)
        try:
            with pytest.raises(protocol.HostProtocolError, match="timeout"):
                client.status()
            assert len(accepted) == 1
            assert not client._jobs
        finally:
            release.set()
            assert client.close(timeout=2)


def test_fifo_binding_refuses_without_blocking_before_type_check(tmp_path):
    os.mkfifo(tmp_path / "binding.json", 0o440)
    code = """
import os,sys
from hfcache.host_helper_client import EndpointBinding
from hfcache.host_protocol import HostProtocolError
b=object.__new__(EndpointBinding)
b._parent=os.open(sys.argv[1],os.O_RDONLY|os.O_DIRECTORY)
b.profile='native';b.api_host_gid=981
try:
    try:b._read_binding()
    except HostProtocolError:pass
    else:raise RuntimeError('FIFO accepted')
finally:b.close()
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)], capture_output=True, timeout=2, check=False
    )
    assert result.returncode == 0, result.stderr.decode()


def test_client_final_deadline_includes_reply_and_peer_validation(tmp_path, monkeypatch):
    late = False

    def decoded_response(*_args, **_kwargs):
        nonlocal late
        late = True
        return {"status": "late"}

    with unix_service(tmp_path) as (path, _, _):
        monkeypatch.setattr(client_module, "client_exchange", decoded_response)
        monkeypatch.setattr(client_module.time, "monotonic", lambda: 123.0 if late else 100.0)
        client = client_module.HostHelperClient(UnixTestBinding(path), deployment_sha256=DEPLOYMENT)
        try:
            with pytest.raises(protocol.HostProtocolError, match="timeout"):
                client.status()
        finally:
            assert client.close(timeout=2)


@pytest.mark.parametrize("profile", ["native", "rootless"])
def test_optional_pin_uses_only_protected_profile_startup_authority(tmp_path, monkeypatch, profile):
    """Unit protected-metadata seam; no claim of actual projected ownership."""
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    info = os.fstat(descriptor)
    record = runtime_binding()
    record["parent"].update(device=info.st_dev, inode=info.st_ino)
    trusted_environment = attestation()
    cast("dict[str, object]", trusted_environment["parent"]).update(
        device=info.st_dev, inode=info.st_ino
    )
    monkeypatch.setattr(client_module, "_open_parent", lambda *_: os.dup(descriptor))
    monkeypatch.setattr(client_module.EndpointBinding, "_read_binding", lambda _: record)
    environment = (
        {"HFCACHE_HOST_HELPER_PARENT": json.dumps(trusted_environment)}
        if profile == "rootless"
        else {}
    )
    try:
        binding = client_module.EndpointBinding.from_startup(
            profile=profile, api_host_gid=1234, environment=environment
        )
        assert binding.deployment_sha256 == DEPLOYMENT
        binding.close()
        with pytest.raises(protocol.HostProtocolError, match="deployment-unverified"):
            client_module.EndpointBinding.from_startup(
                profile=profile,
                api_host_gid=1234,
                deployment_sha256="f" * 64,
                environment=environment,
            )
        if profile == "rootless":
            record["deployment_sha256"] = "f" * 64
            with pytest.raises(protocol.HostProtocolError, match="deployment-unverified"):
                client_module.EndpointBinding.from_startup(
                    profile=profile, api_host_gid=1234, environment=environment
                )
    finally:
        os.close(descriptor)


def test_transport_modules_remain_trusted_host_python312_syntax():
    for module in (protocol, client_module):
        ast.parse(Path(module.__file__).read_text(), feature_version=(3, 12))
