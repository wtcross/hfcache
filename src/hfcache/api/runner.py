"""One bounded, non-resuming heavyweight lane (INV-014/015, decision 115).

Only newly durable admissions become runnable. Existing receipts are observed or
reattached to exact worker status, never reconstructed into executable requests.
"""

import contextlib
import math
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from hfcache.api.host_routes import HOST_EFFECT_ROUTES
from hfcache.api.intents import IntentInterlock, IntentLease
from hfcache.api.lifecycle import unavailable
from hfcache.api.operations import Admission, OperationReceipt, OperationStore
from hfcache.errors import HfcacheError, OperationError, RequestError
from hfcache.locking import CommandLockControl, scoped_command_lock
from hfcache.reporting import Envelope
from hfcache.server_config import InstalledPolicy, PolicySnapshot
from hfcache.services.context import ExecutionContext, ServiceResult

if TYPE_CHECKING:
    from hfcache.api.auth import Principal

Execute = Callable[[PolicySnapshot, ExecutionContext], ServiceResult | Envelope]
Authorize = Callable[[PolicySnapshot], None]
Monitor = Callable[[], Envelope]
Reconcile = Callable[[OperationReceipt], Envelope | Monitor | None]
_ACTIVE_STATES = frozenset({"queued", "waiting_lock", "running"})
_MAX_PENDING = 64


@dataclass(frozen=True, slots=True)
class _Work:
    receipt: OperationReceipt
    snapshot: PolicySnapshot | None
    context: ExecutionContext
    command: str
    execute: Execute | None
    deadline: float | None
    nonblocking: bool = False
    delegated: bool = False
    requires_lock: bool = True
    monitor: Monitor | None = None
    authorize: Authorize | None = None
    intent_lease: IntentLease | None = None


class OperationRunner:
    """Lifespan-owned thread; closing observers never cancel accepted work.

    All queue mutations take the condition before the store lock. The worker
    never holds the store lock while waiting for that condition (AD-17).
    """

    def __init__(  # noqa: PLR0913 - fixed lane policy and existing lifecycle seams
        self,
        store: OperationStore,
        policy: InstalledPolicy,
        *,
        max_pending: int = 16,
        monotonic: Callable[[], float] = time.monotonic,
        check_verification_available: Callable[[], None] | None = None,
        host_actions: bool = False,
    ) -> None:
        if type(max_pending) is not int or not 0 <= max_pending <= _MAX_PENDING:
            message = "pending capacity must be an integer from zero to 64"
            raise ValueError(message)
        if type(host_actions) is not bool or (host_actions and max_pending != 1):
            message = "the fixed host-action lane has exactly one pending slot"
            raise ValueError(message)
        self.store = store
        self.interlock: IntentInterlock | None = None
        self.policy = policy
        self.max_pending = max_pending
        self.monotonic = monotonic
        self.check_verification_available = check_verification_available
        self.host_actions = host_actions
        self._condition = threading.Condition(threading.RLock())
        self._queue: deque[_Work] = deque()
        self._thread: threading.Thread | None = None
        self._executing = False
        self._active_id: str | None = None
        self._accepting = False
        self._closing = False
        self._broken = False
        self._reviewing = False
        self._reconcile: Reconcile | None = None

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def active_operation_id(self) -> str | None:
        with self._condition:
            return self._active_id

    @property
    def pending(self) -> int:
        with self._condition:
            return max(0, len(self._queue) - (not self._executing and bool(self._queue)))

    def start(self, *, reconcile: Reconcile | None = None) -> None:
        """Reconcile exact verifier identity first, interrupt everything else; no replay."""
        from hfcache.locking import lock_path  # noqa: PLC0415 - respects configured runtime

        self.interlock = IntentInterlock(
            getattr(
                self.store, "intent_lock_path", lock_path().with_name(lock_path().name + ".intent")
            )
        )
        if self._thread is not None or self._closing:
            raise unavailable()
        self._reconcile = reconcile
        for receipt in reversed(self.store.list()):
            if not self._owns(receipt.route):
                continue
            if receipt.state not in _ACTIVE_STATES:
                continue
            recovered = None
            if receipt.route == "/api/v1/verifications" and reconcile is not None:
                recovered = reconcile(receipt)
            elif receipt.route == "/api/v1/verifications":
                raise OperationError(
                    code="HFAPI016",
                    message="Verification status must be reconciled before admission",
                )
            if isinstance(recovered, Envelope):
                self._complete(receipt.operation_id, recovered)
            elif callable(recovered):
                context = ExecutionContext.create(operation_id=receipt.operation_id)
                self._queue.append(
                    _Work(
                        receipt,
                        None,
                        context,
                        "verify",
                        None,
                        None,
                        delegated=True,
                        monitor=recovered,
                        intent_lease=self.interlock.acquire(),
                    )
                )
            else:
                self.store.transition(receipt.operation_id, "interrupted")
        if self._queue:
            self._active_id = self._queue[0].receipt.operation_id
        name = "hfcache-host-action" if self.host_actions else "hfcache-command"
        self._thread = threading.Thread(target=self._loop, name=name, daemon=False)
        self._accepting = True
        self._thread.start()

    def _owns(self, route: str) -> bool:
        """Fixed disjoint ownership, including restart; never claim another lane."""
        return (route in HOST_EFFECT_ROUTES) == self.host_actions

    def submit(self, *args: Any, **kwargs: Any) -> Admission:  # noqa: ANN401 - forwards typed admission interface
        if not self._owns(args[2]) or (
            self.host_actions
            and (kwargs.get("requires_lock", True) or kwargs.get("delegated", False))
        ):
            raise RequestError
        with self._condition:
            if self._reviewing:
                raise unavailable()
        if self.interlock is None:
            raise unavailable()
        lease = self.interlock.acquire()
        try:
            if kwargs.get("delegated"):
                try:
                    self.store.lookup(args[0], args[1])
                except OperationError as error:
                    if error.problems[0].code != "HFAPI013":
                        raise
                    if self.check_verification_available is None:
                        raise OperationError(
                            code="HFAPI016", message="Verification executor is unavailable"
                        ) from None
                    self.check_verification_available()
            admission = self._submit(*args, **kwargs, intent_lease=lease)
            if not admission.created:
                lease.close()
        except BaseException:
            lease.close()
            raise
        else:
            return admission

    def _submit(  # noqa: PLR0913 - trusted lane policy is separate from canonical request data
        self,
        principal: Principal,
        key: str,
        route: str,
        request: Mapping[str, Any],
        *,
        command: str,
        execute: Execute,
        wait_seconds: float | Callable[[PolicySnapshot], float],
        delegated: bool = False,
        requires_lock: bool = True,
        context: ExecutionContext | None = None,
        authorize: Authorize | None = None,
        intent_lease: IntentLease,
    ) -> Admission:
        if not self._owns(route) or (self.host_actions and (requires_lock or delegated)):
            raise RequestError

        def validate_budget(value: float) -> float:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise RequestError
            return value

        if not callable(wait_seconds):
            validate_budget(wait_seconds)
        snapshots = []
        budgets = []
        admitted_at = self.monotonic()

        def capacity() -> None:
            outstanding = len(self._queue) + self._executing
            if (
                not self._accepting
                or self._reviewing
                or self._broken
                or outstanding >= self.max_pending + 1
                or (wait_seconds == 0 and outstanding)
            ):
                raise unavailable()

        def snapshot() -> PolicySnapshot:
            frozen = self.policy.snapshot()
            budget = validate_budget(
                wait_seconds(frozen) if callable(wait_seconds) else wait_seconds
            )
            if budget == 0 and (self._queue or self._executing):
                raise unavailable()
            snapshots.append(frozen)
            budgets.append(budget)
            return frozen

        with self._condition:
            admission = self.store.admit(
                principal, key, route, request, snapshot, before_admit=capacity
            )
            if not admission.created:
                return admission
            work = None
            try:
                execution = ExecutionContext.create(
                    request_id=context.request_id if context is not None else None,
                    operation_id=admission.receipt.operation_id,
                )
                work = _Work(
                    admission.receipt,
                    snapshots[0],
                    execution,
                    command,
                    execute,
                    admitted_at + budgets[0],
                    nonblocking=budgets[0] == 0,
                    delegated=delegated,
                    requires_lock=requires_lock,
                    authorize=authorize,
                    intent_lease=intent_lease,
                )
                self._queue.append(work)
                if self._active_id is None:
                    self._active_id = work.receipt.operation_id
                self._condition.notify_all()
            except BaseException:
                if work is not None and work in self._queue:
                    self._queue.remove(work)
                if self._active_id == admission.receipt.operation_id:
                    self._active_id = self._queue[0].receipt.operation_id if self._queue else None
                self._broken = True
                self._accepting = False
                with contextlib.suppress(HfcacheError):
                    self.store.transition(admission.receipt.operation_id, "interrupted")
                raise
            else:
                return admission

    @contextlib.contextmanager
    def review_barrier(self) -> Iterator[None]:
        """Stop local submissions while an external exclusive lease is obtained."""
        with self._condition:
            if self._reviewing:
                raise unavailable()
            self._reviewing = True
        try:
            yield
        finally:
            with self._condition:
                self._reviewing = False
                self._condition.notify_all()

    def stop_admission(self) -> None:
        with self._condition:
            self._accepting = False

    def drain(self) -> None:
        """Stop admission, finish queued work within its budgets, and join the lane."""
        with self._condition:
            self._accepting = False
            self._closing = True
            self._condition.notify_all()
            thread = self._thread
        if thread is not None:
            if threading.current_thread() is thread:
                raise OperationError
            thread.join()

    def close(self) -> None:
        self.drain()

    def wait(self, operation_id: str, *, timeout: float | None = None) -> Envelope:
        """Observe only; a timeout never cancels, requeues or creates work."""
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._condition:
            while True:
                receipt = self.store.get(operation_id)
                if receipt.state in {"succeeded", "failed"}:
                    return self.store.result(operation_id)
                if receipt.state == "interrupted":
                    raise OperationError(
                        code="HFAPI015",
                        status_code=409,
                        message="Operation outcome is interrupted or uncertain",
                    )
                if self._broken:
                    raise OperationError(
                        code="HFAPI015",
                        status_code=409,
                        message="Operation execution is unavailable or uncertain",
                    )
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError
                self._condition.wait(timeout=remaining)

    def mark_running(self, operation_id: str, domain_run_id: str | None = None) -> None:
        """Trusted exact worker progress, never caller-provided execution evidence."""
        receipt = self.store.get(operation_id)
        if receipt.state in {"queued", "waiting_lock"}:
            self.store.transition(operation_id, "running", domain_run_id=domain_run_id)

    def _waiting(self, operation_id: str) -> None:
        if self.store.get(operation_id).state == "queued":
            self.store.transition(operation_id, "waiting_lock")

    def _validate_policy(self, work: _Work) -> None:
        current = self.policy.snapshot()
        if work.snapshot is None or current.fingerprint != work.snapshot.fingerprint:
            raise RequestError(
                code="HFAPI007",
                status_code=409,
                message="Installed policy changed after operation admission",
            )

    def _complete(self, operation_id: str, envelope: Envelope) -> None:
        receipt = self.store.get(operation_id)
        if receipt.state in {"queued", "waiting_lock"} and envelope.exit_code == 0:
            self.store.transition(operation_id, "running")
        self.store.transition(
            operation_id, "succeeded" if envelope.exit_code == 0 else "failed", envelope=envelope
        )

    def _interrupted(self, work: _Work) -> None:
        if self.store.get(work.receipt.operation_id).state in _ACTIVE_STATES:
            self.store.transition(work.receipt.operation_id, "interrupted")

    def _run(self, work: _Work) -> None:
        identifier = work.receipt.operation_id
        with work.context.activate():
            if work.monitor is not None:
                self._complete(identifier, work.monitor())
                return
            if not self._authorize(work):
                return
            try:
                if work.execute is None or work.snapshot is None:
                    raise OperationError
                control = self._control(work)
                with scoped_command_lock(control):
                    outcome = work.execute(work.snapshot, work.context)
                envelope = (
                    outcome.envelope(work.context)
                    if isinstance(outcome, ServiceResult)
                    else outcome
                )
                if not isinstance(envelope, Envelope):
                    raise OperationError
                # A successful locking task must prove it actually used the
                # service-owned guard; arbitrary unlocked callbacks cannot opt out.
                if (
                    not work.delegated
                    and work.requires_lock
                    and self.store.get(identifier).state != "running"
                    and envelope.exit_code == 0
                ):
                    raise OperationError
            except HfcacheError as error:
                if work.delegated:
                    if self._reconcile is None:
                        raise
                    recovered = self._reconcile(self.store.get(identifier))
                    if callable(recovered):
                        self._complete(identifier, recovered())
                        return
                    if isinstance(recovered, Envelope):
                        self._complete(identifier, recovered)
                        return
                    self._interrupted(work)
                    return
                envelope = ServiceResult(
                    work.command, {}, errors=error.problems, exit_code=int(error.exit_code)
                ).envelope(work.context)
            # Persistence failure cannot rewrite a completed domain outcome into
            # a different failed envelope; the loop preserves interruption instead.
            self._complete(identifier, envelope)

    def _authorize(self, work: _Work) -> bool:
        if work.authorize is None:
            return True
        # A fresh Basic refusal proves no handoff occurred. Keep it outside
        # delegated reconciliation and every domain/store lock (decision150).
        try:
            self._check_deadline(work)
            if work.snapshot is None:
                raise OperationError
            work.authorize(work.snapshot)
            self._validate_policy(work)
            self._check_deadline(work)
        except HfcacheError as error:
            envelope = ServiceResult(
                work.command, {}, errors=error.problems, exit_code=int(error.exit_code)
            ).envelope(work.context)
            self._complete(work.receipt.operation_id, envelope)
            return False
        return True

    def _control(self, work: _Work) -> CommandLockControl:
        identifier = work.receipt.operation_id
        if work.authorize is None:
            self._check_deadline(work)
        control = CommandLockControl(
            deadline=work.deadline,
            revalidate=lambda: self._validate_policy(work),
            waiting=lambda: self._waiting(identifier),
            acquired=lambda: self.mark_running(identifier, work.context.run_id),
            nonblocking=work.nonblocking,
            allow_lock=not work.delegated,
            clock=self.monotonic,
        )
        if work.delegated:
            if work.authorize is None:
                self._validate_policy(work)
            self._waiting(identifier)
        elif not work.requires_lock:
            self._validate_policy(work)
            self.mark_running(identifier, work.context.run_id)
        return control

    def _check_deadline(self, work: _Work) -> None:
        if not work.nonblocking and work.deadline is not None and self.monotonic() >= work.deadline:
            raise OperationError(
                code="HFAPI015",
                status_code=409,
                message="Operation waiting budget expired before execution",
            )

    def _loop(self) -> None:
        while True:
            with self._condition:
                while not self._queue and not self._closing:
                    self._condition.wait()
                if not self._queue:
                    self._active_id = None
                    self._condition.notify_all()
                    return
                work = self._queue.popleft()
                self._active_id = work.receipt.operation_id
                self._executing = True
            try:
                self._run(work)
            except BaseException:  # noqa: BLE001 - halt the lane on unclassified execution failure
                # No invented result after an unclassified execution/persistence
                # failure. Preserve evidence and halt new domain work (AD-16).
                if not work.delegated:
                    with contextlib.suppress(HfcacheError):
                        self._interrupted(work)
                with self._condition:
                    self._broken = True
                    self._accepting = False
                    self._closing = True
                    abandoned = tuple(self._queue)
                    self._queue.clear()
                for pending in abandoned:
                    try:
                        if pending.monitor is None:
                            with contextlib.suppress(HfcacheError):
                                self._interrupted(pending)
                    finally:
                        if pending.intent_lease is not None:
                            pending.intent_lease.close()
            finally:
                if work.intent_lease is not None:
                    work.intent_lease.close()
                with self._condition:
                    self._executing = False
                    self._active_id = self._queue[0].receipt.operation_id if self._queue else None
                    self._condition.notify_all()
