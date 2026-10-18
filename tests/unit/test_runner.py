"""One admitted waiting budget and command-owned policy revalidation (API-008)."""

import fcntl
import os
import subprocess
import sys
import threading

import pytest

from hfcache import locking
from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.operations import OperationStore
from hfcache.api.runner import OperationRunner
from hfcache.errors import OperationError, SafetyError
from hfcache.locking import CommandLockControl, exclusive_lock, scoped_command_lock
from hfcache.reporting import Envelope
from hfcache.server_config import InstalledPolicy
from hfcache.services import commands
from hfcache.services.context import ServiceResult
from tests.fixtures import examples

WRITER = Principal(CredentialClass.REST_WRITER)


@pytest.fixture
def configured(tmp_path, monkeypatch):
    root = tmp_path / "archive"
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{root}"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n[sync]\nlock_wait_seconds=100\n'
    )
    installed = InstalledPolicy(policy, root, examples.ARCHIVE_ID)
    monkeypatch.setattr(locking, "LOCK_DIRECTORY", tmp_path / "run")
    monkeypatch.setattr(commands, "hub_checks", lambda *_: [])
    with OperationStore(tmp_path / "state") as store:
        yield installed, store


def submit(runner, key, execute, *, wait=10, requires_lock=True):
    return runner.submit(
        WRITER,
        key,
        "/api/v1/diagnostics",
        {},
        command="doctor",
        execute=execute,
        wait_seconds=wait,
        requires_lock=requires_lock,
    ).receipt


def doctor(snapshot, context):
    return commands.CommandServices(snapshot.config, context).diagnose(commands.DoctorRequest())


def test_policy_is_revalidated_under_cross_process_flock_before_probe(configured, monkeypatch):
    policy, store = configured
    probes = []
    monkeypatch.setattr(commands, "storage_checks", lambda *_a, **_kw: probes.append(True) or [])
    path = locking.lock_path()
    path.parent.mkdir()
    code = (
        "import fcntl,sys; f=open(sys.argv[1],'w'); fcntl.flock(f,fcntl.LOCK_EX); "
        "print('ready',flush=True); sys.stdin.readline()"
    )
    with subprocess.Popen(
        [sys.executable, "-c", code, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    ) as holder:
        assert holder.stdout is not None
        assert holder.stdin is not None
        assert holder.stdout.readline().strip() == "ready"
        runner = OperationRunner(store, policy)
        runner.start()
        try:
            receipt = submit(runner, "stale", doctor)
            # A callback installed on the condition-free store read proves the
            # operation reached lock waiting while another process owns it.
            for _ in range(5000):
                if store.get(receipt.operation_id).state != "queued":
                    break
                threading.Event().wait(0.001)
            else:
                pytest.fail("command never reached lock acquisition")
            policy.path.write_text(policy.path.read_text() + "max_workers=7\n")
            holder.stdin.write("\n")
            holder.stdin.flush()
            holder.wait(timeout=5)
            outcome = runner.wait(receipt.operation_id, timeout=5)
            assert outcome.exit_code == 10
            assert outcome.errors[0].code == "HFAPI007"
            assert probes == []
        finally:
            if holder.poll() is None:
                holder.stdin.write("\n")
                holder.stdin.flush()
            runner.close()
    with exclusive_lock(path, command="after stale refusal", wait_seconds=0):
        pass


def test_queue_time_is_deducted_from_same_absolute_lock_deadline(configured, monkeypatch):
    policy, store = configured
    clock = [1000.0]
    entered = threading.Event()
    release = threading.Event()
    slept = []
    probes = []
    monkeypatch.setattr(commands, "storage_checks", lambda *_a, **_kw: probes.append(True) or [])

    def sleep(seconds):
        slept.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr(locking.time, "sleep", sleep)
    path = locking.lock_path()
    path.parent.mkdir()
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX)

    def blocker(_snapshot, _context):
        entered.set()
        assert release.wait(5)
        return ServiceResult("plan", {})

    runner = OperationRunner(store, policy, max_pending=1, monotonic=lambda: clock[0])
    runner.start()
    try:
        first = submit(runner, "first", blocker, requires_lock=False)
        assert entered.wait(5)
        second = submit(runner, "second", doctor, wait=3)
        clock[0] += 2
        release.set()
        assert runner.wait(first.operation_id, timeout=5).exit_code == 0
        outcome = runner.wait(second.operation_id, timeout=5)
        assert outcome.exit_code == 20
        assert outcome.errors[0].code == "HFMNT010"
        assert slept == [1.0]
        assert probes == []
    finally:
        release.set()
        runner.close()
        os.close(descriptor)


def test_delegate_scope_forbids_parent_archive_lock(configured):
    policy, store = configured

    def insecure(_snapshot, _context):
        with exclusive_lock(locking.lock_path(), command="wrong parent", wait_seconds=0):
            pytest.fail("delegation acquired parent lock")

    runner = OperationRunner(store, policy, check_verification_available=lambda: None)
    runner.start()
    try:
        receipt = runner.submit(
            WRITER,
            "key",
            "/api/v1/verifications",
            {},
            command="verify",
            execute=insecure,
            wait_seconds=5,
            delegated=True,
        ).receipt
        with pytest.raises(OperationError) as caught:
            runner.wait(receipt.operation_id, timeout=5)
        assert caught.value.problems[0].code == "HFAPI015"
        assert store.get(receipt.operation_id).state == "waiting_lock"
        assert not locking.lock_path().exists()
    finally:
        runner.close()


def test_result_persistence_failure_does_not_overwrite_domain_success(configured, monkeypatch):
    policy, store = configured
    original = store._save

    def refuse_terminal(record):
        if record.state == "succeeded":
            raise OperationError
        return original(record)

    monkeypatch.setattr(store, "_save", refuse_terminal)
    runner = OperationRunner(store, policy)
    runner.start()
    try:
        receipt = submit(
            runner, "key", lambda _s, _c: ServiceResult("plan", {"done": True}), requires_lock=False
        )
        with pytest.raises(OperationError) as caught:
            runner.wait(receipt.operation_id, timeout=5)
        assert caught.value.problems[0].code == "HFAPI015"
        result_path = store.root / (receipt.operation_id + ".result.json")
        saved = Envelope.model_validate_json(result_path.read_bytes())
        assert saved.exit_code == 0
        assert saved.data == {"done": True}
        assert store.get(receipt.operation_id).state == "interrupted"
        with pytest.raises(SafetyError):
            submit(runner, "another", lambda _s, _c: ServiceResult("plan", {}), requires_lock=False)
    finally:
        runner.close()


def test_nested_controlled_acquisition_is_refused_and_scope_restores(tmp_path):
    path = tmp_path / "lock"
    control = CommandLockControl(deadline=None, revalidate=lambda: None)
    with (
        scoped_command_lock(control),
        exclusive_lock(path, command="outer", wait_seconds=0),
        pytest.raises(OperationError),
        exclusive_lock(path, command="nested", wait_seconds=0),
    ):
        pytest.fail("nested lock acquired")
    with exclusive_lock(path, command="after", wait_seconds=0):
        pass


def test_lock_does_not_acquire_after_poll_sleep_overshoots_deadline(tmp_path, monkeypatch):
    path = tmp_path / "lock"
    held = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(held, fcntl.LOCK_EX)
    clock = [1.0]
    checks = []

    def oversleep(_):
        clock[0] = 3.0
        fcntl.flock(held, fcntl.LOCK_UN)

    monkeypatch.setattr(locking.time, "sleep", oversleep)
    control = CommandLockControl(
        deadline=2.0, revalidate=lambda: checks.append(True), clock=lambda: clock[0]
    )
    try:
        with (
            scoped_command_lock(control),
            pytest.raises(SafetyError),
            exclusive_lock(path, command="expired", wait_seconds=100),
        ):
            pytest.fail("command acquired the lock after its deadline")
        assert checks == []
    finally:
        os.close(held)


def test_nonblocking_control_refuses_busy_lock_with_future_deadline(tmp_path, monkeypatch):
    path = tmp_path / "lock"
    held = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(held, fcntl.LOCK_EX)

    def sleep(_):
        pytest.fail("nonblocking control waited for the archive lock")

    monkeypatch.setattr(locking.time, "sleep", sleep)
    control = CommandLockControl(deadline=999999999999.0, revalidate=lambda: None, nonblocking=True)
    try:
        with (
            scoped_command_lock(control),
            pytest.raises(SafetyError),
            exclusive_lock(path, command="nonblocking", wait_seconds=100),
        ):
            pytest.fail("busy nonblocking lock was acquired")
    finally:
        os.close(held)


def test_delegation_availability_is_fresh_only_and_retry_precedes_probe(configured):
    policy, store = configured
    probes = []
    entered = threading.Event()
    release = threading.Event()

    def available():
        probes.append(True)
        if len(probes) > 1:
            raise OperationError(code="HFAPI016")

    def execute(_snapshot, _context):
        entered.set()
        assert release.wait(5)
        return ServiceResult("verify --full", {})

    runner = OperationRunner(store, policy, check_verification_available=available)
    runner.start()
    try:
        first = runner.submit(
            WRITER,
            "key",
            "/api/v1/verifications",
            {},
            command="verify",
            execute=execute,
            wait_seconds=5,
            delegated=True,
        )
        assert entered.wait(5)
        retry = runner.submit(
            WRITER,
            "key",
            "/api/v1/verifications",
            {},
            command="verify",
            execute=execute,
            wait_seconds=5,
            delegated=True,
        )
        assert retry.receipt.operation_id == first.receipt.operation_id
        assert not retry.created
        assert len(probes) == 1
        with pytest.raises(OperationError) as caught:
            runner.submit(
                WRITER,
                "another",
                "/api/v1/verifications",
                {},
                command="verify",
                execute=execute,
                wait_seconds=5,
                delegated=True,
            )
        assert caught.value.problems[0].code == "HFAPI016"
        assert len(store.list()) == 1
        release.set()
        assert runner.wait(first.receipt.operation_id, timeout=5).exit_code == 0
    finally:
        release.set()
        runner.close()


def test_unknown_verifier_startup_keeps_durable_admission_barrier_across_restarts(configured):
    policy, store = configured
    receipt = store.admit(WRITER, "old", "/api/v1/verifications", {}, policy.snapshot).receipt

    def unavailable(_receipt):
        raise OperationError(code="HFAPI016")

    for _ in range(2):
        runner = OperationRunner(store, policy)
        try:
            with pytest.raises(OperationError) as caught:
                runner.start(reconcile=unavailable)
            assert caught.value.problems[0].code == "HFAPI016"
            assert store.get(receipt.operation_id).state == "queued"
            with pytest.raises(SafetyError):
                submit(runner, "new", lambda _s, _c: ServiceResult("plan", {}), requires_lock=False)
            assert len(store.list()) == 1
        finally:
            runner.close()


def test_active_delegate_status_loss_preserves_barrier_and_never_replays(configured):
    policy, store = configured
    entered = threading.Event()
    release = threading.Event()
    pending_calls = []

    def unavailable(_receipt):
        raise OperationError(code="HFAPI016")

    def lost_ack(_snapshot, _context):
        entered.set()
        assert release.wait(5)
        raise OperationError(code="HFAPI016")

    def pending(_snapshot, _context):
        pending_calls.append(True)
        return ServiceResult("plan", {})

    runner = OperationRunner(store, policy, check_verification_available=lambda: None)
    runner.start(reconcile=unavailable)
    try:
        receipt = runner.submit(
            WRITER,
            "verify",
            "/api/v1/verifications",
            {},
            command="verify",
            execute=lost_ack,
            wait_seconds=5,
            delegated=True,
        ).receipt
        assert entered.wait(5)
        untouched = submit(runner, "pending", pending, requires_lock=False)
        release.set()
        with pytest.raises(OperationError):
            runner.wait(receipt.operation_id, timeout=5)
        runner.drain()
        assert store.get(receipt.operation_id).state == "waiting_lock"
        assert store.get(untouched.operation_id).state == "interrupted"
        assert pending_calls == []
    finally:
        release.set()
        runner.close()
    restarted = OperationRunner(store, policy)
    try:
        with pytest.raises(OperationError):
            restarted.start(reconcile=unavailable)
        assert store.get(receipt.operation_id).state == "waiting_lock"
    finally:
        restarted.close()
