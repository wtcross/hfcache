"""Hermetic private-executor protocol, restart and real guarded-service coverage."""

import json
import os
import socket
import struct
import subprocess
import sys
import threading
import time
from contextlib import contextmanager

import pytest
from pydantic import ValidationError

from hfcache import locking, storage
from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.operations import OperationStore
from hfcache.api.runner import OperationRunner
from hfcache.archive import initialize_archive
from hfcache.errors import ConfigurationError, OperationError, RequestError
from hfcache.identity import new_run_id
from hfcache.paths import ArchiveLayout
from hfcache.server_config import InstalledPolicy, validate_server_config_mapping
from hfcache.services.commands import VerificationRequest
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.storage import parse_mount_table
from hfcache.verification_executor import VerificationWorker, serve_worker, validate_listener
from hfcache.verification_protocol import (
    ROUTE,
    VerificationClient,
    VerificationScope,
    WorkerReply,
    WorkerRequest,
    check_peer,
    connect_private,
    receive_frame,
    send_frame,
)
from tests.unit.test_verification import ARCHIVE_ID, MODEL, SHA_A, nfs_line, publish
from tests.unit.test_verify_command import config_for, write_run_report


@pytest.fixture
def policy(tmp_path, monkeypatch):
    root = tmp_path / "archive"
    root.mkdir()
    path = tmp_path / "config.toml"
    path.write_text(config_for(root))
    mount = tmp_path / "mountinfo"
    mount.write_text(nfs_line(str(root)))
    monkeypatch.setattr(storage, "MOUNT_TABLE", mount)
    monkeypatch.setattr(locking, "LOCK_DIRECTORY", tmp_path / "run")
    initialize_archive(
        ArchiveLayout(root), archive_id=ARCHIVE_ID, table=parse_mount_table(nfs_line(str(root)))
    )
    return InstalledPolicy(path, root, ARCHIVE_ID)


@contextmanager
def listening(tmp_path, worker):
    directory = tmp_path / "sockets"
    directory.mkdir(mode=0o700)
    path = directory / "verify.sock"
    stop = threading.Event()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        path.chmod(0o600)
        listener.listen(8)
        validate_listener(listener, path)
        thread = threading.Thread(
            target=serve_worker,
            args=(listener, worker),
            kwargs={"expected_uid": os.geteuid(), "stop": stop, "timeout_seconds": 0.1},
        )
        thread.start()
        try:
            yield VerificationClient(path, timeout_seconds=1, poll_seconds=0.01), stop
        finally:
            stop.set()
            thread.join(10)
            assert not thread.is_alive()


def submission(policy, operation_id=None, **options):
    return WorkerRequest(
        schema_version=1,
        action="submit",
        operation_id=operation_id or new_run_id(),
        config_fingerprint=policy.snapshot().fingerprint,
        scope=VerificationScope(mode="full"),
        lock_deadline=time.monotonic() + 10,
        **options,
    )


@contextmanager
def pair():
    first, second = socket.socketpair()
    with first, second:
        yield first, second


@pytest.mark.parametrize("mode", ["new", "full", "revision"])
def test_real_worker_delegates_all_modes_through_guarded_service(
    policy, tmp_path, monkeypatch, mode
):
    layout = ArchiveLayout(policy.root)
    published = publish(layout)
    _, run_id = write_run_report(
        layout, commit_sha=published.commit_sha, publication_id=published.publication_id
    )

    def forbidden(*args, **kwargs):
        pytest.fail("isolated verification loaded a credential or constructed a Hub client")

    monkeypatch.setattr("hfcache.services.commands.resolve_token", forbidden)
    monkeypatch.setattr("hfcache.services.commands.HubClient", forbidden)
    request = VerificationRequest(
        new=mode == "new",
        full=mode == "full",
        revision=f"{MODEL.selector}@{SHA_A}" if mode == "revision" else None,
        run_id=run_id if mode == "new" else None,
    )
    with OperationStore(tmp_path / "worker-state") as store:
        worker = VerificationWorker(policy, store)
        with listening(tmp_path, worker) as (client, _):
            client.check_available()
            operation_id = new_run_id()
            result = client.execute(operation_id, request, policy.snapshot().fingerprint, 10)
            assert result.exit_code == 0
            assert result.data["mode"] == mode
            terminal = store.get(operation_id)
            assert terminal.state == "succeeded"
            assert terminal.domain_run_id == result.run_id
            assert store.result(operation_id) == result
            assert client.status(operation_id, terminal.config_fingerprint).envelope == result
            assert (layout.root / result.data["report"]).is_file()


def test_real_worker_preserves_integrity_exit_and_exact_result(policy, tmp_path):
    layout = ArchiveLayout(policy.root)
    reference = publish(layout)
    tree = layout.published / reference.tree
    next(path for path in tree.rglob("*") if path.is_file()).write_bytes(b"damaged")
    with (
        OperationStore(tmp_path / "worker-state") as store,
        listening(tmp_path, VerificationWorker(policy, store)) as (client, _),
    ):
        operation_id = new_run_id()
        result = client.execute(
            operation_id, VerificationRequest(full=True), policy.snapshot().fingerprint, 10
        )
        assert result.exit_code == 40
        assert store.get(operation_id).state == "failed"
        assert client.status(operation_id, policy.snapshot().fingerprint).envelope == result


def test_missing_status_never_admits_or_executes(policy, tmp_path):
    with OperationStore(tmp_path / "worker-state") as store:
        worker = VerificationWorker(policy, store, execute=lambda *_: pytest.fail("executed"))
        with listening(tmp_path, worker) as (client, _):
            assert client.status(new_run_id(), policy.snapshot().fingerprint).outcome == "missing"
            assert store.list() == ()


def test_duplicate_submit_and_conflict_keep_one_exact_worker(policy, tmp_path):
    entered, release = threading.Event(), threading.Event()
    calls = []

    def execute(snapshot, context, request):
        with locking.exclusive_lock(locking.lock_path(), command=request.command, wait_seconds=0):
            calls.append(context.operation_id)
            entered.set()
            assert release.wait(5)
            return ServiceResult(request.command, {})

    with OperationStore(tmp_path / "worker-state") as store:
        worker = VerificationWorker(policy, store, execute=execute)
        request = submission(policy)
        try:
            first = worker.handle(request)
            assert entered.wait(5)
            second = worker.handle(request)
            assert first.receipt is not None
            assert second.receipt is not None
            assert first.receipt.operation_id == second.receipt.operation_id
            conflict = request.model_copy(update={"scope": VerificationScope(mode="new")})
            with pytest.raises(RequestError, match="HFAPI012"):
                worker.handle(conflict)
            with pytest.raises(OperationError):
                worker.handle(submission(policy))
        finally:
            release.set()
            worker.close()
        assert calls == [request.operation_id]


def test_worker_restart_never_replays_old_queued_scope(policy, tmp_path):
    operation_id = new_run_id()
    with OperationStore(tmp_path / "worker-state") as store:
        request = submission(policy, operation_id)
        assert request.scope is not None
        store.admit(
            Principal(CredentialClass.REST_WRITER),
            operation_id,
            ROUTE,
            request.scope.canonical() | {"config_fingerprint": request.config_fingerprint},
            policy.snapshot,
            operation_id=operation_id,
        )
        worker = VerificationWorker(policy, store, execute=lambda *_: pytest.fail("replayed"))
        try:
            reply = worker.handle(request)
            assert reply.receipt is not None
            assert reply.receipt.state == "interrupted"
            with pytest.raises(OperationError):
                store.result(operation_id)
        finally:
            worker.close()


@pytest.mark.parametrize("already_terminal", [False, True])
def test_dropped_submit_client_and_api_restart_import_exact_existing_result(
    policy, tmp_path, already_terminal
):
    entered, release = threading.Event(), threading.Event()
    calls = []

    def execute(snapshot, context, request):
        with locking.exclusive_lock(locking.lock_path(), command=request.command, wait_seconds=0):
            calls.append(context.operation_id)
            entered.set()
            assert release.wait(5)
            return ServiceResult(request.command, {"verified": True})

    with (
        OperationStore(tmp_path / "worker-state") as worker_store,
        OperationStore(tmp_path / "api-state") as api_store,
    ):
        parent = api_store.admit(
            Principal(CredentialClass.REST_WRITER),
            "parent-key",
            ROUTE,
            {"mode": "full"},
            policy.snapshot,
        ).receipt
        worker = VerificationWorker(policy, worker_store, execute=execute)
        with listening(tmp_path, worker) as (client, _):
            request = submission(policy, parent.operation_id)
            with connect_private(
                client.path, expected_uid=os.geteuid(), timeout_seconds=1
            ) as connection:
                send_frame(connection, request)
                # Lose the acknowledgement. Closing this observer cannot cancel
                # the worker, and startup must never submit the request again.
            assert entered.wait(5)
            if already_terminal:
                release.set()
                worker.close()
            runner = OperationRunner(api_store, policy)
            try:
                runner.start(reconcile=client.reconcile)
                if not already_terminal:
                    assert runner.active_operation_id == parent.operation_id
                release.set()
                result = runner.wait(parent.operation_id, timeout=5)
                assert result == worker_store.result(parent.operation_id)
                assert result.data == {"verified": True}
                assert calls == [parent.operation_id]
            finally:
                release.set()
                runner.close()


@pytest.mark.parametrize("try_lock", [False, True])
def test_expired_positive_deadline_and_zero_wait_single_attempt(policy, tmp_path, try_lock):
    calls = []

    def execute(snapshot, context, request):
        with locking.exclusive_lock(locking.lock_path(), command=request.command, wait_seconds=0):
            calls.append(context.operation_id)
            return ServiceResult(request.command, {})

    with OperationStore(tmp_path / "worker-state") as store:
        worker = VerificationWorker(policy, store, execute=execute)
        request = submission(policy).model_copy(
            update={"lock_deadline": time.monotonic() - 1, "try_lock": try_lock}
        )
        worker.handle(request)
        worker.close()
        assert request.operation_id is not None
        result = store.result(request.operation_id)
        assert result.exit_code == (0 if try_lock else 20)
        assert len(calls) == int(try_lock)


def test_nonterminal_label_without_owned_thread_is_not_surviving_worker_proof(policy, tmp_path):
    with OperationStore(tmp_path / "worker-state") as store:
        worker = VerificationWorker(policy, store)
        operation_id = new_run_id()
        record = store.admit(
            Principal(CredentialClass.REST_WRITER),
            operation_id,
            ROUTE,
            {},
            policy.snapshot,
            operation_id=operation_id,
        ).receipt
        with pytest.raises(OperationError, match="HFAPI016"):
            worker.handle(
                WorkerRequest(
                    schema_version=1,
                    action="status",
                    operation_id=operation_id,
                    config_fingerprint=record.config_fingerprint,
                )
            )
        worker.close()
        assert store.get(operation_id).state == "queued"


def test_wrong_archive_status_closes_reconciliation_before_progress(policy, tmp_path, monkeypatch):
    with OperationStore(tmp_path / "worker-state") as store:
        worker = VerificationWorker(policy, store)
        parent = store.admit(
            Principal(CredentialClass.REST_WRITER), "parent", ROUTE, {}, policy.snapshot
        ).receipt
        wrong = parent.model_copy(update={"archive_id": "00000000-0000-4000-8000-000000000001"})
        monkeypatch.setattr(
            worker,
            "handle",
            lambda _: WorkerReply(schema_version=1, outcome="found", receipt=wrong),
        )
        progress = []
        with listening(tmp_path, worker) as (client, _):
            client.expected_archive_id = parent.archive_id
            client.progress = progress.append
            with pytest.raises(OperationError, match="HFAPI016"):
                client.status(parent.operation_id, parent.config_fingerprint)
            assert progress == []
            client.expected_archive_id = None
            client.progress = None
            with pytest.raises(OperationError, match="HFAPI016"):
                client.reconcile(parent)
        assert store.get(parent.operation_id) == parent


def test_terminal_worker_reply_must_match_durable_result_digest(policy, tmp_path):
    with OperationStore(tmp_path / "worker-state") as store:
        receipt = store.admit(
            Principal(CredentialClass.REST_WRITER), "parent", ROUTE, {}, policy.snapshot
        ).receipt
        store.transition(receipt.operation_id, "running")
        envelope = ServiceResult("verify --full", {"verified": True}).envelope(
            ExecutionContext.create()
        )
        terminal = store.transition(receipt.operation_id, "succeeded", envelope=envelope)
        with pytest.raises(ValidationError, match="durably referenced"):
            WorkerReply(
                schema_version=1,
                outcome="found",
                receipt=terminal,
                envelope=envelope.model_copy(update={"data": {"verified": False}}),
            )


@pytest.mark.parametrize(
    "body", [b"{}", b"", b'{"action":"probe","action":"status"}', b"[", b"\xff"]
)
def test_frames_refuse_malformed_or_duplicate_objects(body):
    with pair() as (sender, receiver):
        sender.sendall(struct.pack("!I", len(body)) + body)
        sender.shutdown(socket.SHUT_WR)
        with pytest.raises((OperationError, ValidationError)):
            WorkerRequest.model_validate(receive_frame(receiver))


@pytest.mark.parametrize("length", [0, 1, 16777217, 4294967295])
def test_frame_length_refused_before_payload(length):
    with pair() as (sender, receiver):
        sender.sendall(struct.pack("!I", length))
        with pytest.raises(OperationError):
            receive_frame(receiver)


def test_frame_roundtrip_and_truncation():
    with pair() as (sender, receiver):
        request = WorkerRequest(schema_version=1, action="probe")
        send_frame(sender, request)
        assert WorkerRequest.model_validate(receive_frame(receiver)) == request
        sender.sendall(struct.pack("!I", 10) + b"{}")
        sender.shutdown(socket.SHUT_WR)
        with pytest.raises(OperationError):
            receive_frame(receiver)


@pytest.mark.parametrize("mode", [0o666, 0o644, 0o777])
def test_unsafe_socket_modes_refused(tmp_path, mode):
    path = tmp_path / "verify.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        path.chmod(mode)
        listener.listen(1)
        with pytest.raises(OperationError):
            connect_private(path, expected_uid=os.geteuid(), timeout_seconds=0.1)


def test_symlink_socket_and_writable_parent_refused(tmp_path):
    safe = tmp_path / "safe"
    safe.mkdir(mode=0o700)
    path = safe / "verify.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        path.chmod(0o600)
        listener.listen(1)
        alias = safe / "alias.sock"
        alias.symlink_to(path)
        with pytest.raises(OperationError):
            connect_private(alias, expected_uid=os.geteuid(), timeout_seconds=0.1)
        safe.chmod(0o777)
        with pytest.raises(OperationError):
            connect_private(path, expected_uid=os.geteuid(), timeout_seconds=0.1)


def test_peer_uid_refused_and_correct_uid_accepted():
    with pair() as (first, second):
        check_peer(first, os.geteuid())
        with pytest.raises(OperationError):
            check_peer(second, os.geteuid() + 1)


@pytest.mark.parametrize(
    "scope",
    [
        {"mode": "estimate"},
        {"mode": "full", "run_id": "a" * 32},
        {"mode": "revision"},
        {"mode": "new", "revision": f"{MODEL.selector}@{SHA_A}"},
        {"mode": "revision", "revision": MODEL.selector},
        {"mode": "full", "config": "/tmp/x"},
    ],
)
def test_only_narrow_valid_verification_scopes(scope):
    with pytest.raises(ValidationError):
        VerificationScope.model_validate(scope)


def test_unavailable_worker_has_no_in_process_fallback(tmp_path):
    client = VerificationClient(tmp_path / "missing.sock")
    with pytest.raises(OperationError) as failed:
        client.check_available()
    assert failed.value.problems[0].code == "HFAPI016"
    with pytest.raises(OperationError):
        client.execute(new_run_id(), VerificationRequest(full=True), "a" * 64, 1)
    assert list(tmp_path.iterdir()) == []


def test_bootstrap_import_is_cold_and_standalone_refuses(tmp_path):
    source = (
        "import sys,os,json; import hfcache.verification_worker; "
        "print(json.dumps({'hub':'huggingface_hub' in sys.modules,"
        "'commands':'hfcache.services.commands' in sys.modules,"
        "'offline':os.getenv('HF_HUB_OFFLINE')}))"
    )
    environment = dict(os.environ)
    environment.pop("HF_HUB_OFFLINE", None)
    result = subprocess.run(
        [sys.executable, "-c", source], capture_output=True, text=True, check=True, env=environment
    )
    assert json.loads(result.stdout) == {"hub": False, "commands": False, "offline": None}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hfcache.verification_worker",
            "--config",
            str(tmp_path / "missing"),
            "--state-directory",
            str(tmp_path / "state"),
            "--socket",
            str(tmp_path / "socket"),
            "--api-uid",
            str(os.geteuid()),
        ],
        capture_output=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 20
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("extra_descriptor", [False, True])
def test_activated_worker_entrypoint(tmp_path, extra_descriptor):
    config = tmp_path / "config.toml"
    archive = tmp_path / "archive"
    config.write_text(
        f'schema_version=1\n[storage]\narchive_root="{archive}"\narchive_id="{ARCHIVE_ID}"\n'
    )
    credential = tmp_path / "synthetic-credential"
    credential.write_bytes(b"synthetic test file")
    address = tmp_path / "v.sock"
    trampoline = (
        "import os,sys; fd=int(sys.argv[1]); os.dup2(fd,3); os.set_inheritable(3,True); "
        "(os.close(fd) if fd!=3 else None); os.environ['LISTEN_PID']=str(os.getpid()); "
        "os.execv(sys.executable,[sys.executable,'-m','hfcache.verification_worker',*sys.argv[2:]])"
    )
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener,
        credential.open("rb") as extra,
    ):
        listener.bind(str(address))
        address.chmod(0o600)
        listener.listen(8)
        descriptors = (
            (listener.fileno(), extra.fileno()) if extra_descriptor else (listener.fileno(),)
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                trampoline,
                str(listener.fileno()),
                "--config",
                str(config),
                "--state-directory",
                str(tmp_path / "state"),
                "--socket",
                str(address),
                "--api-uid",
                str(os.geteuid()),
            ],
            pass_fds=descriptors,
            env={"PATH": os.environ["PATH"], "LISTEN_FDS": "1", "LANG": "C.UTF-8"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            if extra_descriptor:
                process.communicate(timeout=5)
                assert process.returncode == 20
                assert not (tmp_path / "state").exists()
            else:
                client = VerificationClient(address, timeout_seconds=0.1)
                deadline = time.monotonic() + 5
                while True:
                    try:
                        client.check_available()
                        break
                    except OperationError:
                        if process.poll() is not None or time.monotonic() >= deadline:
                            pytest.fail("activated verifier did not become available")
                        time.sleep(0.02)
                process.terminate()
                process.communicate(timeout=5)
                assert process.returncode == 0
                assert [path.name for path in (tmp_path / "state").iterdir()] == [".lock"]
            assert not archive.exists()
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()


@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("unix_socket", "relative"),
        ("expected_peer_uid", -1),
        ("timeout_seconds", 0),
        ("poll_seconds", float("nan")),
        ("max_frame_bytes", 16777217),
        ("command", "sync"),
    ],
)
def test_verifier_settings_are_strict(setting, value):
    with pytest.raises(ConfigurationError) as failed:
        validate_server_config_mapping(
            {
                "schema_version": 1,
                "credentials": {"writer": {"file": "/tmp/credential"}},
                "verification": {setting: value},
            }
        )
    assert "HFCFG" in str(failed.value)
