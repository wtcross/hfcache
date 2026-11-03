"""INV022: fixed host effects cannot wait for or reconcile archive execution."""

import fcntl
import os
import threading
from datetime import UTC, datetime, timedelta

import pytest

from hfcache import locking
from hfcache.api.host_routes import OBSERVER_STOPS, SCHEDULE_CHANGES
from hfcache.api.runner import OperationRunner
from hfcache.errors import OperationError, RequestError, SafetyError
from hfcache.locking import exclusive_lock
from hfcache.services.context import ExecutionContext, ServiceResult
from tests.intent_fixtures import OperationStore
from tests.unit.test_runner import WRITER
from tests.unit.test_runner import configured as configured  # noqa: PLC0414 - shared fixture


def host_submit(runner, key, execute):
    return runner.submit(
        WRITER,
        key,
        OBSERVER_STOPS,
        {},
        command="host observer stop",
        execute=execute,
        wait_seconds=10,
        requires_lock=False,
    ).receipt


def test_host_action_finishes_while_original_domain_work_still_holds_archive_flock(configured):
    policy, store = configured
    entered = threading.Event()
    release = threading.Event()
    host_entered = threading.Event()
    domain = OperationRunner(store, policy)
    host = OperationRunner(store, policy, max_pending=1, host_actions=True)
    domain.start()
    host.start()

    def backend(_snapshot, _context):
        with exclusive_lock(locking.lock_path(), command="doctor", wait_seconds=0):
            entered.set()
            assert release.wait(10)
            return ServiceResult("doctor", {})

    try:
        original = domain.submit(
            WRITER,
            "original-domain",
            "/api/v1/diagnostics",
            {},
            command="doctor",
            execute=backend,
            wait_seconds=10,
        ).receipt
        assert entered.wait(5)

        def stop_only_observer(_snapshot, _context):
            assert store.get(original.operation_id).state == "running"
            host_entered.set()
            return ServiceResult("host observer stop", {})

        stopped = host_submit(host, "stop-original-observer", stop_only_observer)
        assert host.wait(stopped.operation_id, timeout=5).exit_code == 0
        assert host_entered.is_set()
        assert not release.is_set()
        assert store.get(original.operation_id).state == "running"
        descriptor = os.open(locking.lock_path(), os.O_RDWR)
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(descriptor)
        release.set()
        assert domain.wait(original.operation_id, timeout=5).exit_code == 0
    finally:
        release.set()
        host.close()
        domain.close()


def test_startup_interrupts_only_its_original_routes_without_reconstructing_work(configured):
    policy, store = configured
    ordinary = store.admit(
        WRITER, "domain-before-restart", "/api/v1/diagnostics", {}, policy.snapshot
    ).receipt
    fixed = store.admit(
        WRITER, "host-before-restart", SCHEDULE_CHANGES, {}, policy.snapshot
    ).receipt
    domain = OperationRunner(store, policy)
    host = OperationRunner(store, policy, max_pending=1, host_actions=True)
    domain.start()
    try:
        assert store.get(ordinary.operation_id).state == "interrupted"
        assert store.get(fixed.operation_id).state == "queued"
        host.start()
        try:
            assert store.get(fixed.operation_id).state == "interrupted"
            assert store.get(ordinary.operation_id).state == "interrupted"
            assert domain.active_operation_id is host.active_operation_id is None
        finally:
            host.close()
    finally:
        domain.close()


def test_unknown_host_effect_halts_only_host_lane_and_does_not_disable_domain_work(configured):
    policy, store = configured
    domain = OperationRunner(store, policy)
    host = OperationRunner(store, policy, max_pending=1, host_actions=True)
    domain.start()
    host.start()

    def uncertain(_snapshot, _context):
        message = "owned possible transmission"
        raise RuntimeError(message)

    try:
        original = host_submit(host, "original-unknown", uncertain)
        with pytest.raises(OperationError):
            host.wait(original.operation_id, timeout=5)
        assert store.get(original.operation_id).state == "interrupted"
        ordinary = domain.submit(
            WRITER,
            "domain-still-available",
            "/api/v1/diagnostics",
            {},
            command="doctor",
            execute=lambda *_: ServiceResult("doctor", {}),
            wait_seconds=10,
            requires_lock=False,
        ).receipt
        assert domain.wait(ordinary.operation_id, timeout=5).exit_code == 0
        with pytest.raises(SafetyError):
            host_submit(
                host,
                "never-admitted-after-uncertainty",
                lambda *_: ServiceResult("host observer stop", {}),
            )
    finally:
        host.close()
        domain.close()


@pytest.mark.parametrize(
    ("host_actions", "route", "requires_lock", "delegated"),
    [
        (True, "/api/v1/syncs", False, False),
        (False, OBSERVER_STOPS, False, False),
        (True, OBSERVER_STOPS, True, False),
        (True, OBSERVER_STOPS, False, True),
    ],
)
def test_fixed_lane_refuses_wrong_route_or_archive_execution_before_admission(
    configured, host_actions, route, requires_lock, delegated
):
    policy, store = configured
    runner = OperationRunner(store, policy, max_pending=1, host_actions=host_actions)
    with runner, pytest.raises(RequestError):
        runner.submit(
            WRITER,
            "refused-before-admit",
            route,
            {},
            command="wrong",
            execute=lambda *_: ServiceResult("wrong", {}),
            wait_seconds=10,
            requires_lock=requires_lock,
            delegated=delegated,
        )
    assert store.list() == ()


@pytest.mark.parametrize("route", [SCHEDULE_CHANGES, OBSERVER_STOPS])
@pytest.mark.parametrize("state", ["succeeded", "failed"])
def test_host_original_receipt_and_result_survive_normal_expiry_for_helper_reconciliation(
    configured, tmp_path, route, state
):
    policy, _unused = configured
    now = [datetime(2026, 10, 27, tzinfo=UTC)]
    root = tmp_path / "host-retention"
    with OperationStore(root, clock=lambda: now[0]) as store:
        original = store.admit(WRITER, "retained-host", route, {}, policy.snapshot).receipt
        context = ExecutionContext.create(operation_id=original.operation_id)
        store.transition(original.operation_id, "running", domain_run_id=context.run_id)
        error = RequestError()
        result = ServiceResult(
            "host schedule change" if route == SCHEDULE_CHANGES else "host observer stop",
            {},
            errors=error.problems if state == "failed" else (),
            exit_code=10 if state == "failed" else 0,
        ).envelope(context)
        store.transition(original.operation_id, state, envelope=result)
        ordinary = store.admit(
            WRITER, "ordinary-expirable", "/api/v1/syncs", {}, policy.snapshot
        ).receipt
        store.transition(ordinary.operation_id, "running")
        store.transition(
            ordinary.operation_id,
            "succeeded",
            envelope=ServiceResult("sync", {"repositories": []}).envelope(
                ExecutionContext.create()
            ),
        )
        before = {
            p.name: (p.stat().st_ino, p.read_bytes())
            for p in root.glob(original.operation_id + "*")
        }
        assert len(before) == 2
        now[0] += timedelta(days=31)
        assert store.expire() == (ordinary.operation_id,)
        assert {
            p.name: (p.stat().st_ino, p.read_bytes())
            for p in root.glob(original.operation_id + "*")
        } == before
    with OperationStore(root, clock=lambda: now[0]) as reopened:
        assert reopened.lookup(WRITER, "retained-host").operation_id == original.operation_id
        assert reopened.get(original.operation_id).state == state
        assert reopened.result(original.operation_id) == result
