"""Exclusive retirement uses real stores/worker and bounded adapter proof seams."""

import fcntl
import json
import os
import threading
import time
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from starlette.requests import Request

from hfcache import locking
from hfcache.api.intent_routes import _retire
from hfcache.api.intents import IntentInterlock, unavailable
from hfcache.api.runner import OperationRunner
from hfcache.errors import HfcacheError, OperationError
from hfcache.locking import exclusive_lock
from hfcache.models import TransactionJournal
from hfcache.paths import ArchiveLayout
from hfcache.services.context import ServiceResult
from hfcache.verification_executor import VerificationWorker
from hfcache.verification_protocol import VerificationScope, WorkerRequest
from tests.intent_fixtures import OperationStore
from tests.unit.test_intent_dispositions import BASIC, refused
from tests.unit.test_verification_executor import (
    policy as policy,  # noqa: PLC0414 - owned archive fixture
)


@pytest.fixture
def review_context(tmp_path, policy):
    path = locking.lock_path()
    path.parent.mkdir(exist_ok=True)
    path.touch(mode=0o600)
    with (
        OperationStore(tmp_path / "api") as store,
        OperationStore(tmp_path / "worker", private=True) as private,
    ):
        worker = VerificationWorker(policy, private)
        runner = OperationRunner(store, policy)
        host = OperationRunner(store, policy, max_pending=1, host_actions=True)
        runner.start()
        host.start()

        class Verifier:
            def intent_review(self, *, deadline):
                return worker.handle(WorkerRequest(schema_version=1, action="intent-review")).review

        state = SimpleNamespace(
            operations=store,
            policy=policy,
            runner=runner,
            host_runner=host,
            verifier=Verifier(),
            instance_id="f" * 32,
        )

        class Helper:
            calls = 0

            def intent_review_identity(self):
                return {
                    "deployment_sha256": "a" * 64,
                    "policy_sha256": "b" * 64,
                    "helper": {"pid": os.getpid(), "start_ticks": 1},
                    "helper_generation": "f" * 32,
                }

            def intent_review(self, *, deadline):
                self.calls += 1
                # An independent original flock succeeds here: no helper IPC is
                # occurring under the archive or store lock.

                for target in (path, store.root / ".lock"):
                    descriptor = os.open(target, os.O_RDONLY)
                    try:
                        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    finally:
                        os.close(descriptor)
                assert not cast("Any", runner._condition)._is_owned()
                assert runner.interlock is not None
                info = path.stat()
                return {
                    "schema_version": 1,
                    "archive_id": policy.archive_id,
                    "deployment_sha256": "a" * 64,
                    "policy_sha256": "b" * 64,
                    "effects_sha256": "c" * 64,
                    "helper_instance": {"pid": os.getpid(), "start_ticks": 1},
                    "intent_lock": runner.interlock.identity.model_dump(),
                    "archive_lock": {"device": info.st_dev, "inode": info.st_ino},
                }

        helper = Helper()
        state.host_helper = helper
        request = Request(
            {"type": "http", "app": SimpleNamespace(state=state), "state": {"principal": BASIC}}
        )
        try:
            yield request, worker, helper, private
        finally:
            runner.close()
            host.close()
            worker.close()


def test_unknown_retirement_needs_no_action_or_host_read_grants_and_never_replays(review_context):
    request, _, helper, _ = review_context
    assert BASIC.admin_capabilities == frozenset()
    response = json.loads(bytes(_retire(request, "historical").body))
    assert response["state"] == "retired_unknown"
    assert response["operation"] is None
    assert helper.calls == 1
    assert request.app.state.operations.list() == ()
    assert json.loads(bytes(_retire(request, "historical").body)) == response
    assert helper.calls == 1


def test_existing_refusal_takes_full_review_and_retains_original_evidence(review_context):
    request, _, helper, _ = review_context
    original = refused(request.app.state.operations)[1]
    response = json.loads(bytes(_retire(request, "original").body))
    assert helper.calls == 1
    assert response["state"] == "retired_unknown"
    enriched = request.app.state.operations.intent(
        BASIC, "original", request.app.state.policy.archive_id
    )[1]
    assert enriched.model_dump(exclude={"review"}) == original.model_dump(exclude={"review"})


def test_unresolved_whole_worker_store_refuses_missing_original_review(review_context):
    request, _, helper, private = review_context
    snapshot = request.app.state.policy.snapshot()
    receipt = private.admit(
        BASIC, "unrelated", "/api/v1/verifications", {}, lambda: snapshot
    ).receipt
    private.transition(receipt.operation_id, "interrupted")
    with pytest.raises(OperationError, match="Private worker"):
        _retire(request, "historical")
    assert helper.calls == 0
    assert request.app.state.operations.intent(
        BASIC, "historical", snapshot.config.storage.archive_id
    ) == (None, None)


def test_unknown_helper_effect_or_unclassified_archive_journal_preserves_unknown(
    review_context, monkeypatch
):
    request, _, helper, _ = review_context
    with monkeypatch.context() as patch:

        def pending(**_):
            message = "pending protected effect"
            raise unavailable(message)

        patch.setattr(helper, "intent_review", pending)
        with pytest.raises(OperationError, match="Protected executor"):
            _retire(request, "historical")
    layout = ArchiveLayout(request.app.state.policy.root)
    (layout.transactions / "unclassified").write_bytes(b"preserved evidence")
    with pytest.raises(OperationError, match="Unclassified archive journal"):
        _retire(request, "historical")
    assert request.app.state.operations.list() == ()


def test_worker_handoff_independent_shared_lease_spans_result(tmp_path, policy):
    reached, finish = threading.Event(), threading.Event()
    path = locking.lock_path()
    path.parent.mkdir(exist_ok=True)
    path.touch(mode=0o600)

    def execute(snapshot, context, request):
        with exclusive_lock(path, command="verify", wait_seconds=1):
            reached.set()
            assert finish.wait(5)
            return ServiceResult("verify --new", {})

    with OperationStore(tmp_path / "worker", private=True) as private:
        worker = VerificationWorker(policy, private, execute=execute)
        interlock = IntentInterlock(private.intent_lock_path)
        parent = interlock.acquire()
        snapshot = policy.snapshot()

        worker.handle(
            WorkerRequest(
                schema_version=1,
                action="submit",
                operation_id="a" * 32,
                config_fingerprint=snapshot.fingerprint,
                scope=VerificationScope(mode="new"),
                lock_deadline=time.monotonic() + 5,
            )
        )
        assert reached.wait(5)
        parent.close()
        try:
            with pytest.raises(OperationError):
                interlock.acquire(exclusive=True)
        finally:
            finish.set()
            worker.close()
        assert private.get("a" * 32).state == "succeeded"
        with interlock.acquire(exclusive=True):
            pass


def test_failed_enqueue_keeps_lease_until_interrupted_receipt_and_never_runs(
    review_context, monkeypatch
):
    from collections import deque  # noqa: PLC0415 - injected queue boundary

    request, _, _, _ = review_context
    runner = request.app.state.runner

    class FailedQueue(deque):
        def append(self, item):
            super().append(item)
            message = "injected enqueue failure"
            raise RuntimeError(message)

    monkeypatch.setattr(runner, "_queue", FailedQueue())
    executed = []
    with pytest.raises(RuntimeError, match="enqueue failure"):
        runner.submit(
            BASIC,
            "enqueue",
            "/api/v1/diagnostics",
            {},
            command="doctor",
            execute=lambda *_: executed.append(True),
            wait_seconds=1,
            requires_lock=False,
        )
    receipts = request.app.state.operations.list()
    assert len(receipts) == 1
    assert receipts[0].state == "interrupted"
    assert not runner._queue
    assert executed == []
    assert runner.interlock is not None
    with runner.interlock.acquire(exclusive=True):
        pass


def _review_journals(request: Request, count: int, *, padding: int = 0) -> dict[str, bytes]:
    layout = ArchiveLayout(request.app.state.policy.root)
    snapshot = request.app.state.policy.snapshot()
    original = {}
    for index in range(count):
        journal = TransactionJournal(
            schema_version=1,
            archive_id=request.app.state.policy.archive_id,
            config_fingerprint=snapshot.fingerprint,
            created_at=datetime(2026, 11, 5, tzinfo=UTC),
            operation="sync",
            run_id="a" * 32,
            state="committed",
            transaction_id=f"{index:032x}",
        )
        body = json.dumps(journal.model_dump(mode="json")).encode()
        body += b" " * max(0, padding - len(body))
        path = layout.transactions / f"{index:032x}.json"
        path.write_bytes(body)
        original[str(path)] = body
    return original


@pytest.mark.parametrize("count", [621, 1024])
def test_whole_journal_retirement_counts_enumeration_and_reads_separately(review_context, count):
    request, _, helper, _ = review_context
    original = _review_journals(request, count)
    response = json.loads(bytes(_retire(request, "historical").body))
    assert response["state"] == "retired_unknown"
    assert response["operation"] is None
    assert helper.calls == 1
    assert request.app.state.operations.list() == ()
    for name, body in original.items():
        assert request.app.state.policy.root.joinpath(name).read_bytes() == body


def test_excess_journal_history_refuses_without_retiring_or_changing_it(review_context):
    request, _, _, _ = review_context
    original = _review_journals(request, 1025)
    with pytest.raises(HfcacheError):
        _retire(request, "historical")
    assert request.app.state.operations.intent(
        BASIC, "historical", request.app.state.policy.archive_id
    ) == (None, None)
    for name, body in original.items():
        assert request.app.state.policy.root.joinpath(name).read_bytes() == body


def test_unfinished_final_journal_still_blocks_a_large_history(review_context):
    request, _, _, _ = review_context
    original = _review_journals(request, 621)
    last = request.app.state.policy.root.joinpath(sorted(original)[-1])
    content = json.loads(last.read_bytes())
    content["state"] = "needs_operator"
    last.write_text(json.dumps(content))
    with pytest.raises(OperationError, match="Unfinished archive journal"):
        _retire(request, "historical")
    assert request.app.state.operations.intent(
        BASIC, "historical", request.app.state.policy.archive_id
    ) == (None, None)


@pytest.mark.parametrize(("count", "padding"), [(1, 1048577), (129, 65536)])
def test_journal_byte_ceilings_still_refuse_without_retiring(review_context, count, padding):
    request, _, _, _ = review_context
    original = _review_journals(request, count, padding=padding)
    with pytest.raises(HfcacheError):
        _retire(request, "historical")
    assert request.app.state.operations.intent(
        BASIC, "historical", request.app.state.policy.archive_id
    ) == (None, None)
    for name, body in original.items():
        assert request.app.state.policy.root.joinpath(name).read_bytes() == body
