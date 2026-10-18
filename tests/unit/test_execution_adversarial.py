"""Bounded execution retains ownership and never replays history (INV-014/015)."""

import fcntl
import json
import os
import time
from threading import Event, Thread
from typing import Literal

import pytest
from pydantic import ValidationError

from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.operations import OperationStore
from hfcache.api.runner import OperationRunner
from hfcache.config import load_config
from hfcache.errors import HfcacheError
from hfcache.locking import exclusive_lock
from hfcache.server_config import InstalledPolicy
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.verification_executor import VerificationWorker
from hfcache.verification_protocol import VerificationScope, WorkerReply, WorkerRequest

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
WRITER = Principal(CredentialClass.REST_WRITER)
ROUTE = "/api/v1/plans"
VERIFY_ROUTE = "/api/v1/verifications"


@pytest.fixture
def policy(tmp_path):
    path = tmp_path / "archive.toml"
    path.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{ARCHIVE_ID}"\n'
    )
    config = load_config(path)
    return InstalledPolicy(path, config.storage.archive_root, config.storage.archive_id)


def _submit(runner, key, execute, *, wait=30):
    return runner.submit(
        WRITER,
        key,
        ROUTE,
        {"key_label": key},
        command="plan",
        execute=execute,
        wait_seconds=wait,
        requires_lock=False,
    )


def test_zero_pending_allows_one_active_slot_and_retries_even_while_draining(tmp_path, policy):
    entered, release = Event(), Event()
    calls = []

    def execute(snapshot, context):
        calls.append(context.operation_id)
        entered.set()
        assert release.wait(timeout=10)
        return ServiceResult("plan", {"ok": True})

    with OperationStore(tmp_path / "state") as store:
        runner = OperationRunner(store, policy, max_pending=0)
        runner.start()
        try:
            first = _submit(runner, "first", execute)
            assert entered.wait(timeout=10)
            with pytest.raises(HfcacheError):
                _submit(runner, "second", execute)
            assert runner.pending == 0
            assert len(store.list()) == 1
            runner.stop_admission()
            policy.path.write_text("malformed = [")
            repeated = _submit(runner, "first", execute)
            assert not repeated.created
            assert repeated.receipt.operation_id == first.receipt.operation_id
            with pytest.raises(HfcacheError):
                _submit(runner, "fresh-after-drain", execute)
            assert calls == [first.receipt.operation_id]
        finally:
            release.set()
            runner.drain()
        assert store.get(first.receipt.operation_id).state == "succeeded"


def test_pending_fifo_and_observer_timeout_do_not_cancel_accepted_work(tmp_path, policy):
    entered, release = Event(), Event()
    order = []

    def first_execute(snapshot, context):
        order.append("first")
        entered.set()
        assert release.wait(timeout=10)
        return ServiceResult("plan", {"ordinal": 1})

    def second_execute(snapshot, context):
        order.append("second")
        return ServiceResult("plan", {"ordinal": 2})

    with OperationStore(tmp_path / "state") as store:
        runner = OperationRunner(store, policy, max_pending=1)
        runner.start()
        try:
            first = _submit(runner, "first", first_execute)
            assert entered.wait(timeout=10)
            second = _submit(runner, "second", second_execute)
            with pytest.raises(TimeoutError):
                runner.wait(first.receipt.operation_id, timeout=0.01)
            with pytest.raises(HfcacheError):
                _submit(runner, "excess", second_execute)
            assert runner.pending == 1
            assert order == ["first"]
        finally:
            release.set()
            runner.drain()
        assert order == ["first", "second"]
        assert store.result(first.receipt.operation_id).data == {"ordinal": 1}
        assert store.result(second.receipt.operation_id).data == {"ordinal": 2}


def test_queue_expiry_spends_the_original_wait_budget_without_domain_invocation(tmp_path, policy):
    entered, release = Event(), Event()
    now = [100.0]
    expired_calls = []

    def active(snapshot, context):
        entered.set()
        assert release.wait(timeout=10)
        return ServiceResult("plan", {})

    def expired(snapshot, context):
        expired_calls.append(context.operation_id)
        return ServiceResult("plan", {})

    with OperationStore(tmp_path / "state") as store:
        runner = OperationRunner(store, policy, max_pending=1, monotonic=lambda: now[0])
        runner.start()
        try:
            _submit(runner, "active", active)
            assert entered.wait(timeout=10)
            queued = _submit(runner, "expires", expired, wait=2)
            now[0] = 103.0
        finally:
            release.set()
            runner.drain()
        assert expired_calls == []
        result = store.result(queued.receipt.operation_id)
        assert result.exit_code == 20
        assert result.outcome == "failed"


@pytest.mark.parametrize("old_state", ["queued", "waiting_lock", "running"])
def test_startup_never_reconstructs_old_nonverification_requests(tmp_path, policy, old_state):
    with OperationStore(tmp_path / "state") as store:
        receipt = store.admit(WRITER, "old", ROUTE, {}, policy.snapshot).receipt
        if old_state != "queued":
            store.transition(receipt.operation_id, old_state)

        def forbidden_reconcile(receipt):
            pytest.fail("nonverification history reached executable reconciliation")

        runner = OperationRunner(store, policy)
        runner.start(reconcile=forbidden_reconcile)
        runner.drain()
        assert store.get(receipt.operation_id).state == "interrupted"
        with pytest.raises(HfcacheError):
            store.result(receipt.operation_id)


def test_exact_surviving_verifier_occupies_lane_and_drain_joins_it(tmp_path, policy):
    entered, release, drained = Event(), Event(), Event()
    context = ExecutionContext.create()
    result = ServiceResult("verify --full", {"verified": True}).envelope(context)
    reconciled = []

    def monitor():
        entered.set()
        assert release.wait(timeout=10)
        return result

    with OperationStore(tmp_path / "state") as store:
        receipt = store.admit(WRITER, "old-verifier", VERIFY_ROUTE, {}, policy.snapshot).receipt
        store.transition(receipt.operation_id, "running", domain_run_id=context.run_id)

        def reconcile(found):
            reconciled.append(found.operation_id)
            assert found.operation_id == receipt.operation_id
            return monitor

        runner = OperationRunner(store, policy, max_pending=0)
        runner.start(reconcile=reconcile)

        def drain():
            runner.drain()
            drained.set()

        drainer = Thread(target=drain)
        try:
            assert entered.wait(timeout=10)
            with pytest.raises(HfcacheError):
                _submit(runner, "new", lambda *_: ServiceResult("plan", {}))
            drainer.start()
            assert not drained.wait(timeout=0.05)
            assert runner.active_operation_id == receipt.operation_id
            assert store.get(receipt.operation_id).state == "running"
        finally:
            release.set()
            if drainer.ident is not None:
                drainer.join(timeout=10)
            runner.close()
        assert drained.is_set()
        assert reconciled == [receipt.operation_id]
        assert store.result(receipt.operation_id) == result


def test_exact_worker_terminal_result_closes_api_receipt_without_resubmission(tmp_path, policy):
    result = ServiceResult("verify --full", {"verified": True}).envelope(ExecutionContext.create())
    calls = []
    with OperationStore(tmp_path / "state") as store:
        receipt = store.admit(WRITER, "completed-worker", VERIFY_ROUTE, {}, policy.snapshot).receipt
        store.transition(receipt.operation_id, "running", domain_run_id=result.run_id)

        def reconcile(found):
            calls.append(found.operation_id)
            return result

        runner = OperationRunner(store, policy)
        runner.start(reconcile=reconcile)
        runner.drain()
        assert calls == [receipt.operation_id]
        assert store.result(receipt.operation_id) == result


def test_terminal_persistence_failure_preserves_domain_success_and_halts_pending_work(
    tmp_path, policy
):
    entered, release = Event(), Event()
    armed = False
    writes = 0
    pending_calls = []

    def checkpoint(name):
        nonlocal writes
        if armed and name == "before_write":
            writes += 1
            if writes == 2:
                message = "injected terminal API receipt failure after durable domain result"
                raise OSError(message)

    def execute(snapshot, context):
        nonlocal armed
        entered.set()
        assert release.wait(timeout=10)
        armed = True
        return ServiceResult("plan", {"domain_success": True})

    def pending(snapshot, context):
        pending_calls.append(context.operation_id)
        return ServiceResult("plan", {})

    with OperationStore(tmp_path / "state", checkpoint=checkpoint) as store:
        runner = OperationRunner(store, policy)
        runner.start()
        try:
            completed = _submit(runner, "domain-completes", execute)
            assert entered.wait(timeout=10)
            queued = _submit(runner, "must-not-execute", pending)
        finally:
            release.set()
            runner.drain()
        raw = json.loads(
            (store.root / (completed.receipt.operation_id + ".result.json")).read_bytes()
        )
        assert raw["exit_code"] == 0
        assert raw["data"] == {"domain_success": True}
        assert store.get(completed.receipt.operation_id).state == "interrupted"
        assert store.get(queued.receipt.operation_id).state == "interrupted"
        assert pending_calls == []


@pytest.mark.parametrize("version", [None, True, False, 1.0, "1", 0, 2])
@pytest.mark.parametrize("wire", ["request", "reply"])
def test_private_protocol_requires_its_explicit_integer_schema_version(version, wire):
    payload = {"action": "probe"} if wire == "request" else {"outcome": "available"}
    if version is not None:
        payload["schema_version"] = version
    model = WorkerRequest if wire == "request" else WorkerReply

    with pytest.raises(ValidationError):
        model.model_validate(payload)


def _verification_request(
    policy, *, mode: Literal["full", "new"] = "full", action: Literal["submit", "status"] = "submit"
):
    return WorkerRequest(
        schema_version=1,
        action=action,
        operation_id="0123456789abcdef0123456789abcdef",
        config_fingerprint=policy.snapshot().fingerprint,
        scope=VerificationScope(mode=mode) if action == "submit" else None,
        lock_deadline=time.monotonic() + 30 if action == "submit" else None,
    )


def test_verifier_close_joins_active_work_before_releasing_archive_ownership(tmp_path, policy):
    entered, release, closed = Event(), Event(), Event()
    lock_path = tmp_path / "archive.lock"

    def execute(snapshot, context, request):
        with exclusive_lock(lock_path, command="verify", wait_seconds=30):
            entered.set()
            assert release.wait(timeout=10)
            return ServiceResult("verify --full", {"verified": True})

    with OperationStore(tmp_path / "worker") as store:
        worker = VerificationWorker(policy, store, execute=execute)
        request = _verification_request(policy)
        assert request.operation_id is not None
        worker.handle(request)

        def close():
            worker.close()
            closed.set()

        closer = Thread(target=close)
        try:
            assert entered.wait(timeout=10)
            closer.start()
            assert not closed.wait(timeout=0.05)
            descriptor = os.open(lock_path, os.O_RDONLY)
            try:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(descriptor)
        finally:
            release.set()
            if closer.ident is not None:
                closer.join(timeout=10)
            worker.close()
        assert closed.is_set()
        assert store.result(request.operation_id).data == {"verified": True}


def test_private_unknown_status_is_non_submitting_and_keeps_worker_state_unchanged(
    tmp_path, policy
):
    def forbidden(*args):
        pytest.fail("status request invoked verification")

    with OperationStore(tmp_path / "worker") as store:
        worker = VerificationWorker(policy, store, execute=forbidden)
        before = {path.name: path.read_bytes() for path in store.root.iterdir()}
        try:
            result = worker.handle(_verification_request(policy, action="status"))
            assert result.outcome == "missing"
            assert result.receipt is None
            assert before == {path.name: path.read_bytes() for path in store.root.iterdir()}
        finally:
            worker.close()


def test_verifier_exact_operation_cannot_be_rebound_to_another_mode(tmp_path, policy):
    calls = []

    def execute(snapshot, context, request):
        with exclusive_lock(tmp_path / "archive.lock", command="verify", wait_seconds=30):
            calls.append(request.mode)
            return ServiceResult("verify --full", {})

    with OperationStore(tmp_path / "worker") as store:
        worker = VerificationWorker(policy, store, execute=execute)
        request = _verification_request(policy)
        assert request.operation_id is not None
        try:
            worker.handle(request)
            worker.close()
            original = store.get(request.operation_id)
            # A new worker process observes terminal evidence; it never resumes
            # an already-known operation under a changed scope.
            reopened = VerificationWorker(policy, store, execute=execute)
            try:
                with pytest.raises(HfcacheError):
                    reopened.handle(_verification_request(policy, mode="new"))
                assert store.get(request.operation_id) == original
                assert calls == ["full"]
            finally:
                reopened.close()
        finally:
            worker.close()
