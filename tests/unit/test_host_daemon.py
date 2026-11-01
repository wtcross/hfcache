"""Decision150 daemon lifecycle/framing; root metadata is explicitly simulated.

Real socketpair/kernel credentials establish local transport behavior here.
Installed root/native/container separation requires the disposable guest proof.
"""

import ast
import hashlib
import importlib.util
import json
import os
import socket
import stat
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from hfcache import host_protocol as protocol
from hfcache.host_policy import InspectionError

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts/host-helper.py"
SPEC = importlib.util.spec_from_file_location("protected_host_daemon", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
daemon = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(daemon)


@pytest.fixture
def protected_metadata(monkeypatch):
    """Emulate root protection around actual owned local filesystem syscalls."""
    original_stat, original_fstat = os.stat, os.fstat

    def root_facts(facts):
        fields = {
            key: getattr(facts, key)
            for key in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_uid",
                "st_gid",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        }
        fields["st_uid"] = 0
        if stat.S_ISDIR(facts.st_mode):
            fields["st_mode"] &= ~0o022
        return SimpleNamespace(**fields)

    monkeypatch.setattr(daemon.os, "fstat", lambda fd: root_facts(original_fstat(fd)))
    monkeypatch.setattr(
        daemon.os, "stat", lambda *args, **kwargs: root_facts(original_stat(*args, **kwargs))
    )


def fd_count():
    return len(list(Path("/proc/self/fd").iterdir()))


def test_protected_capture_reads_exact_bytes_and_closes_fds(tmp_path, protected_metadata):
    leaf = tmp_path / "module.py"
    leaf.write_bytes(b"ordinary protected bytes\n")
    leaf.chmod(0o644)
    before = fd_count()
    assert daemon.trusted_read(leaf) == b"ordinary protected bytes\n"
    assert fd_count() == before


@pytest.mark.parametrize(
    "kind", ["symlink", "fifo", "directory", "hardlink", "writable", "large", "empty"]
)
def test_unsafe_bootstrap_evidence_refuses_without_replacement(tmp_path, protected_metadata, kind):
    leaf = tmp_path / "module.py"
    leaf.write_bytes(b"captured evidence")
    leaf.chmod(0o644)
    if kind == "symlink":
        other = tmp_path / "original.py"
        leaf.rename(other)
        leaf.symlink_to(other)
    elif kind == "fifo":
        leaf.unlink()
        os.mkfifo(leaf)
    elif kind == "directory":
        leaf.unlink()
        leaf.mkdir()
    elif kind == "hardlink":
        (tmp_path / "original.py").hardlink_to(leaf)
    elif kind == "writable":
        leaf.chmod(0o666)
    elif kind == "large":
        leaf.write_bytes(b"x" * 33)
    else:
        leaf.write_bytes(b"")
    identity = leaf.lstat().st_ino
    before = fd_count()
    with pytest.raises((OSError, ValueError)):
        daemon.trusted_read(leaf, maximum=32)
    assert leaf.lstat().st_ino == identity
    assert fd_count() == before


def test_bootstrap_path_replacement_is_not_a_valid_capture(
    tmp_path, protected_metadata, monkeypatch
):
    leaf = tmp_path / "module.py"
    leaf.write_bytes(b"original")
    original = daemon.os.stat

    def changed(*args, **kwargs):
        facts = original(*args, **kwargs)
        facts.st_ino += 1
        return facts

    monkeypatch.setattr(daemon.os, "stat", changed)
    with pytest.raises(ValueError, match="refused"):
        daemon.trusted_read(leaf)
    assert leaf.read_bytes() == b"original"


def test_cleanup_preserves_substituted_and_missing_nodes(tmp_path):
    leaf = tmp_path / "helper.sock"
    leaf.write_bytes(b"old")
    identity = (leaf.stat().st_dev, leaf.stat().st_ino)
    original = tmp_path / "retained"
    leaf.rename(original)
    leaf.write_bytes(b"replacement")
    parent = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        daemon.remove_owned(parent, leaf.name, identity)
        assert leaf.read_bytes() == b"replacement"
        daemon.remove_owned(parent, "absent", identity)
        daemon.remove_owned(parent, leaf.name, None)
        actual = leaf.stat()
        daemon.remove_owned(parent, leaf.name, (actual.st_dev, actual.st_ino))
        assert not leaf.exists()
        assert original.read_bytes() == b"old"
    finally:
        os.close(parent)


def test_notify_is_one_real_unix_datagram_and_invalid_address_refuses(tmp_path, monkeypatch):
    path = str(tmp_path / "ready")
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as receiver:
        receiver.bind(path)
        receiver.settimeout(1)
        monkeypatch.setenv("NOTIFY_SOCKET", path)
        daemon.notify_ready()
        assert receiver.recv(100) == b"READY=1"
    monkeypatch.setenv("NOTIFY_SOCKET", "https://not-an-endpoint")
    with pytest.raises(ValueError, match="refused"):
        daemon.notify_ready()


@pytest.fixture
def inspector():
    calls = []
    hashes = {
        key: hashlib.sha256(key.encode()).hexdigest()
        for key in (
            "helper_daemon",
            "host_policy",
            "host_protocol",
            "host_peer",
            "host_configuration",
            "host_actions",
            "host_selinux",
        )
    }
    bindings = {
        role: hashes[key]
        for key, role in (
            ("helper_daemon", "helper_daemon"),
            ("host_policy", "helper_policy_module"),
            ("host_protocol", "helper_protocol_module"),
            ("host_peer", "helper_peer_module"),
            ("host_configuration", "helper_configuration_module"),
            ("host_actions", "helper_actions_module"),
            ("host_selinux", "helper_selinux_module"),
        )
    }
    budget = SimpleNamespace(
        deadline_ns=time.monotonic_ns() + 15_000_000_000, remaining=lambda maximum: maximum
    )
    authority = SimpleNamespace(
        deployment_sha256="a" * 64, deployment={"bindings": bindings}, budget=budget
    )

    def inspect_authority(**kwargs):
        calls.append("inspect")
        assert kwargs["host_labels"] is labels
        authority.budget = kwargs["budget"]
        return authority

    def revalidate(value):
        assert value is authority
        calls.append("revalidate")

    def status():
        calls.append("status")
        return {"observed": True}

    def authenticate(value, peer, *, remaining_seconds):
        assert value is authority
        assert peer.credentials.pid == os.getpid()
        assert 0 < remaining_seconds <= 15
        calls.append("peer-first")
        return peer

    def peer_again(proof, value, peer, *, remaining_seconds):
        assert proof is peer
        assert value is authority
        assert 0 < remaining_seconds <= 15
        calls.append("peer-again")

    authority.status = status
    policy = SimpleNamespace(
        InspectionError=InspectionError,
        InspectionBudget=lambda **values: SimpleNamespace(
            **values, remaining=lambda _maximum: (values["deadline_ns"] - time.monotonic_ns()) / 1e9
        ),
        inspect_authority=inspect_authority,
        revalidate=revalidate,
        read_config_base=lambda _value, _body=None: {"base_revision": "b" * 64},
    )
    peers = SimpleNamespace(authenticate=authenticate, revalidate=peer_again)

    def forbidden(*_args, **_kwargs):
        pytest.fail("a different protected operation was dispatched")

    labels = SimpleNamespace()
    actions = SimpleNamespace(
        **dict.fromkeys(
            (
                "read_sync_observer",
                "validate_schedule",
                "change_schedule",
                "read_schedule_outcome",
                "stop_sync_observer",
                "read_observer_outcome",
                "read_journal",
            ),
            forbidden,
        )
    )
    instance = daemon.HostDaemon(
        {
            "host_protocol": protocol,
            "host_policy": policy,
            "host_peer": peers,
            "host_configuration": SimpleNamespace(
                apply_configuration=forbidden, read_configuration_outcome=forbidden
            ),
            "host_actions": actions,
            "host_selinux": labels,
        },
        hashes,
    )
    instance.deployment_sha256 = authority.deployment_sha256
    try:
        yield instance, calls, authority
    finally:
        instance.executor.shutdown(wait=True)


def run_exchange(instance, wire):
    server, client = socket.socketpair()
    protocol.configure_listener(server)
    protocol.configure_listener(client)
    assert instance.capacity.acquire(blocking=False)
    worker = threading.Thread(target=instance.exchange, args=(server,))
    try:
        encoded = protocol.encode_object(wire)
        client.sendall(len(encoded).to_bytes(4, "big") + encoded)
        client.shutdown(socket.SHUT_WR)
        worker.start()
        body = bytearray()
        client.settimeout(3)
        try:
            while part := client.recv(65536):
                body.extend(part)
        except ConnectionResetError:
            # Refusal before request consumption can produce a kernel reset.
            assert not body
        return bytes(body)
    finally:
        client.close()
        worker.join(4)
        assert not worker.is_alive()


def test_daemon_real_exchange_revalidates_before_read_and_releases_capacity(inspector):
    instance, calls, _ = inspector
    request = protocol.HostRequest("c" * 32, "status")
    raw = run_exchange(instance, request.wire())
    assert int.from_bytes(raw[:4], "big") == len(raw[4:])
    assert protocol.reply_body(protocol.decode_object(raw[4:]), request) == {"observed": True}
    assert calls == ["inspect", "peer-first", "revalidate", "peer-again", "revalidate", "status"]
    assert instance.capacity.acquire(blocking=False)
    instance.capacity.release()


@pytest.mark.parametrize("operation", ["config-apply", "config-outcome"])
def test_daemon_application_dispatch_uses_indexed_writer_after_original_peer_proof(
    inspector, operation
):
    instance, calls, authority = inspector
    body: dict[str, object] = {"operation_id": "b" * 32, "request_digest": "c" * 64}
    if operation == "config-apply":
        body |= {
            "managed": {"base_revision": "d" * 64, "edits": []},
            "candidate_revision": "e" * 64,
            "config_fingerprint": "f" * 64,
            "preview_operation_id": "a" * 32,
            "required_selectors": [],
        }

    def dispatch(policy, snapshot, incoming):
        assert policy is instance.policy
        assert snapshot is authority
        assert incoming == body
        calls.append(operation)
        return {"state": "confirmed"}

    instance.configuration.apply_configuration = dispatch
    instance.configuration.read_configuration_outcome = dispatch
    request = protocol.HostRequest("c" * 32, operation, body)
    raw = run_exchange(instance, request.wire())
    assert protocol.reply_body(protocol.decode_object(raw[4:]), request) == {"state": "confirmed"}
    assert calls == ["inspect", "peer-first", "revalidate", "peer-again", "revalidate", operation]


@pytest.mark.parametrize(
    ("operation", "method", "body"),
    [
        ("observer-status", "read_sync_observer", {}),
        (
            "schedule-validate",
            "validate_schedule",
            {"on_calendar": "daily", "randomized_delay_sec": None},
        ),
        (
            "schedule-change",
            "change_schedule",
            {
                "operation_id": "b" * 32,
                "request_digest": "c" * 64,
                "request": {"action": "pause", "expected_revision": "d" * 64},
            },
        ),
        (
            "schedule-outcome",
            "read_schedule_outcome",
            {"operation_id": "b" * 32, "request_digest": "c" * 64},
        ),
        (
            "observer-stop",
            "stop_sync_observer",
            {
                "operation_id": "b" * 32,
                "request_digest": "c" * 64,
                "request": {
                    "expected": {
                        "boot_id": "cf68ba1d-153b-41bc-8f0b-b0414512dc03",
                        "invocation_id": "1" * 32,
                        "main_pid": 123,
                        "start_ticks": 456,
                    }
                },
            },
        ),
        (
            "observer-outcome",
            "read_observer_outcome",
            {"operation_id": "b" * 32, "request_digest": "c" * 64},
        ),
        ("journal-read", "read_journal", {"source": "sync-observer", "cursor": None, "limit": 80}),
    ],
)
def test_new_host_operations_dispatch_only_after_original_peer_and_bootstrap_revalidation(
    inspector, operation, method, body
):
    instance, calls, authority = inspector

    def dispatch(policy, snapshot, incoming):
        assert policy is instance.policy
        assert snapshot is authority
        assert incoming == body
        calls.append(operation)
        return {"observed": operation}

    setattr(instance.actions, method, dispatch)
    request = protocol.HostRequest("c" * 32, operation, body)
    raw = run_exchange(instance, request.wire())
    assert protocol.reply_body(protocol.decode_object(raw[4:]), request) == {"observed": operation}
    assert calls == ["inspect", "peer-first", "revalidate", "peer-again", "revalidate", operation]


def test_journal_subquota_leaves_other_helper_exchanges_available(inspector):
    instance, calls, _authority = inspector
    assert instance.journal_capacity.acquire(blocking=False)
    assert instance.journal_capacity.acquire(blocking=False)
    try:
        request = protocol.HostRequest(
            "c" * 32, "journal-read", {"source": "sync-observer", "cursor": None, "limit": 80}
        )
        response = protocol.decode_object(run_exchange(instance, request.wire())[4:])
        assert response["outcome"] == "unavailable"
        assert response["reason"] == "busy"
        calls.clear()
        status = protocol.HostRequest("d" * 32, "status")
        raw = run_exchange(instance, status.wire())
        assert protocol.reply_body(protocol.decode_object(raw[4:]), status) == {"observed": True}
        assert calls[-1] == "status"
    finally:
        instance.journal_capacity.release()
        instance.journal_capacity.release()


@pytest.mark.parametrize(
    "role",
    [
        "helper_daemon",
        "helper_policy_module",
        "helper_protocol_module",
        "helper_peer_module",
        "helper_configuration_module",
        "helper_actions_module",
        "helper_selinux_module",
    ],
)
def test_every_protected_bootstrap_hash_is_checked_before_peer_or_dispatch(inspector, role):
    instance, calls, authority = inspector
    authority.deployment["bindings"][role] = "0" * 64
    assert run_exchange(instance, protocol.HostRequest("e" * 32, "status").wire()) == b""
    assert calls == ["inspect"]


def test_fixed_loader_captures_exact_six_modules_and_daemon_without_discovering_code(
    tmp_path, protected_metadata, monkeypatch
):
    names = (
        "host_protocol",
        "host_selinux",
        "host_policy",
        "host_peer",
        "host_configuration",
        "host_actions",
    )
    expected = {}
    for name in names:
        path = tmp_path / (name + ".py")
        body = f"CAPTURED_NAME = {name!r}\n".encode()
        path.write_bytes(body)
        path.chmod(0o644)
        expected[name] = hashlib.sha256(body).hexdigest()
    (tmp_path / "unindexed.py").write_bytes(b"raise AssertionError('unindexed module executed')\n")
    monkeypatch.setattr(daemon, "LIBRARY", tmp_path)
    before = fd_count()
    modules, hashes, work = daemon.load_modules()
    assert tuple(modules) == names
    assert {name: value.CAPTURED_NAME for name, value in modules.items()} == {
        name: name for name in names
    }
    assert hashes == expected | {"helper_daemon": hashlib.sha256(SCRIPT.read_bytes()).hexdigest()}
    assert work["files"] == 7
    assert (
        work["bytes"]
        == sum((tmp_path / (name + ".py")).stat().st_size for name in names) + SCRIPT.stat().st_size
    )
    assert fd_count() == before


@pytest.mark.parametrize(
    "change", [{"operation": "config-apply"}, {"body": {"path": "/etc/passwd"}}]
)
def test_daemon_invalid_requests_never_dispatch(inspector, change, capsys):
    instance, calls, _ = inspector
    assert run_exchange(instance, protocol.HostRequest("d" * 32, "status").wire() | change) == b""
    assert "status" not in calls
    assert "peer-again" not in calls
    assert capsys.readouterr().err == ""


def test_daemon_deployment_drift_refuses_before_peer_and_dispatch(inspector):
    instance, calls, authority = inspector
    authority.deployment_sha256 = "f" * 64
    assert run_exchange(instance, protocol.HostRequest("e" * 32, "status").wire()) == b""
    assert calls == ["inspect"]


def test_config_base_policy_denial_is_typed_after_fresh_peer_proof(inspector, capsys):
    instance, calls, _ = inspector

    def denied(_authority, _body=None):
        calls.append("config-denied")
        reason = "operation-denied"
        raise InspectionError(reason)

    instance.policy.read_config_base = denied
    request = protocol.HostRequest("f" * 32, "config-read")
    raw = run_exchange(instance, request.wire())
    response = protocol.decode_object(raw[4:])
    assert response == {
        **request.wire(),
        "outcome": "denied",
        "body": {},
        "reason": "operation-denied",
    }
    assert calls == [
        "inspect",
        "peer-first",
        "revalidate",
        "peer-again",
        "revalidate",
        "config-denied",
    ]
    with pytest.raises(protocol.HostProtocolError, match="operation-denied"):
        protocol.reply_body(response, request)
    assert capsys.readouterr().err == ""


def test_bound_config_read_dispatch_keeps_both_peer_proofs(inspector):
    instance, calls, authority = inspector
    body: dict[str, object] = {
        "expected_archive_id": "6ce912b6-141f-4bd2-a871-c19625c86aa9",
        "expected_archive_root": "/comparison-only",
    }

    def read(snapshot, supplied):
        assert snapshot is authority
        assert supplied == body
        calls.append("bound-config-read")
        return {"base_revision": "b" * 64}

    instance.policy.read_config_base = read
    request = protocol.HostRequest("f" * 32, "config-read", body)
    raw = run_exchange(instance, request.wire())
    assert protocol.reply_body(protocol.decode_object(raw[4:]), request) == {
        "base_revision": "b" * 64
    }
    assert calls == [
        "inspect",
        "peer-first",
        "revalidate",
        "peer-again",
        "revalidate",
        "bound-config-read",
    ]


def test_host_python_312_syntax_and_fixed_unit_boundary():
    ast.parse(SCRIPT.read_text(), feature_version=(3, 12))
    unit = (ROOT / "packaging/systemd/hfcache-host-helper.service").read_text()
    assert "CapabilityBoundingSet=CAP_SETUID CAP_SETGID\n" in unit
    assert "AmbientCapabilities=CAP_SETUID\n" in unit
    assert "RestrictNamespaces=user\n" in unit
    assert "RestrictAddressFamilies=AF_UNIX\n" in unit
    assert "TimeoutStopSec=infinity\n" in unit
    assert "InaccessiblePaths=-/srv/hfcache " in unit
    assert "--config" not in unit
    assert "CAP_SYS_PTRACE" not in unit
    assert "CAP_DAC_OVERRIDE" not in unit


@pytest.mark.parametrize(
    ("failure", "expected_class"),
    [
        (RuntimeError, "RuntimeError"),
        (InspectionError, "ValueError"),
        (protocol.HostProtocolError, "Exception"),
    ],
)
def test_unexpected_writer_exchange_failure_logs_only_protected_metadata(
    inspector, capsys, failure, expected_class
):
    instance, calls, _authority = inspector
    hostile = "Authorization: Bearer private-token; request body and private TOML must stay hidden"
    namespace = {"hostile": hostile, "failure": failure}
    exec(
        compile(
            "def apply_configuration(policy, authority, body):\n"
            "    try:\n"
            "        raise OSError(5, hostile, '/run/secrets/private-input')\n"
            "    except OSError:\n"
            "        raise failure('facts-unavailable') from None\n",
            str(daemon.LIBRARY / "host_configuration.py"),
            "exec",
        ),
        namespace,
    )
    instance.configuration.apply_configuration = namespace["apply_configuration"]
    request = protocol.HostRequest(
        "c" * 32,
        "config-apply",
        {
            "operation_id": "b" * 32,
            "request_digest": "c" * 64,
            "managed": {"base_revision": "d" * 64, "edits": []},
            "candidate_revision": "e" * 64,
            "config_fingerprint": "f" * 64,
            "preview_operation_id": "a" * 32,
            "required_selectors": [],
        },
    )
    before = fd_count()
    assert run_exchange(instance, request.wire()) == b""
    assert fd_count() == before
    assert calls == ["inspect", "peer-first", "revalidate", "peer-again", "revalidate"]
    diagnostic = capsys.readouterr().err
    assert hostile not in diagnostic
    assert "/run/secrets/private-input" not in diagnostic
    assert "base_revision" not in diagnostic
    assert request.body["request_digest"] not in diagnostic
    assert len(diagnostic) <= daemon.MAX_FAILURE_BYTES + 200
    prefix, body = diagnostic.split("protected host helper failure ", 1)
    assert (
        prefix
        == "protected host helper unavailable; preserve state and inspect fixed prerequisites\n"
    )
    metadata = json.loads(body)
    assert metadata["operation"] == "serve"
    assert [row["error_class"] for row in metadata["errors"]] == [expected_class, "OSError"]
    assert [row["errno"] for row in metadata["errors"]] == [None, 5]
    frames = [frame for row in metadata["errors"] for frame in row["frames"]]
    assert any(
        frame["module"] == "host_configuration" and frame["function"] == "apply_configuration"
        for frame in frames
    )
    assert any(
        frame["module"] == "host-helper" and frame["function"] == "exchange" for frame in frames
    )
    assert all(set(frame) == {"module", "function", "line"} for frame in frames)
