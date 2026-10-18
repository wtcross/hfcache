"""Runtime for the separately started, credential-free verification executor.

The ASGI process imports only verification_protocol. The entry point initializes
offline mode before importing this module; API-014 owns OS sandbox enforcement.
"""

import os
import socket
import stat
import threading
import time
from typing import TYPE_CHECKING

from pydantic import ValidationError

from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.lifecycle import open_directory
from hfcache.errors import HfcacheError, OperationError
from hfcache.locking import CommandLockControl, scoped_command_lock
from hfcache.services.commands import CommandServices, VerificationRequest
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.verification_listener import DIRECTORY_MODE, SOCKET_MODE
from hfcache.verification_protocol import (
    MAX_FRAME_BYTES,
    ROUTE,
    WorkerReply,
    WorkerRequest,
    check_peer,
    receive_frame,
    send_frame,
    unavailable,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from hfcache.api.operations import OperationStore
    from hfcache.server_config import InstalledPolicy, PolicySnapshot

_PRINCIPAL = Principal(CredentialClass.REST_WRITER)


class VerificationWorker:
    """One non-resuming worker with durable exact-ID bindings and terminal results."""

    def __init__(
        self,
        policy: InstalledPolicy,
        store: OperationStore,
        *,
        execute: Callable[[PolicySnapshot, ExecutionContext, VerificationRequest], ServiceResult]
        | None = None,
    ) -> None:
        if store.root.is_relative_to(policy.root) or policy.root.is_relative_to(store.root):
            raise unavailable()
        self.policy, self.store = policy, store
        self._execute = execute or (
            lambda snapshot, context, request: CommandServices(snapshot.config, context).verify(
                request
            )
        )
        self._mutex = threading.RLock()
        self._active: threading.Thread | None = None
        self._active_operation_id: str | None = None
        self._closing = False
        # A newly started executor cannot be the previous live executor. The
        # entry point's instance lock excludes that case before opening state.
        self.store.interrupt_unfinished()

    def _status(self, request: WorkerRequest) -> WorkerReply:
        if request.operation_id is None:
            raise unavailable()
        try:
            receipt = self.store.get(request.operation_id)
        except OperationError as error:
            if error.problems[0].code == "HFAPI013":
                return WorkerReply(schema_version=1, outcome="missing")
            raise
        if receipt.config_fingerprint != request.config_fingerprint or receipt.route != ROUTE:
            return WorkerReply(schema_version=1, outcome="conflict")
        if receipt.state in {"queued", "waiting_lock", "running"} and (
            self._active is None
            or not self._active.is_alive()
            or self._active_operation_id != request.operation_id
        ):
            raise unavailable()
        result = (
            self.store.result(receipt.operation_id)
            if receipt.state in {"succeeded", "failed"}
            else None
        )
        return WorkerReply(schema_version=1, outcome="found", receipt=receipt, envelope=result)

    def handle(self, request: WorkerRequest) -> WorkerReply:
        with self._mutex:
            if request.action == "status":
                return self._status(request)
            if self._closing:
                raise unavailable()
            if request.action == "probe":
                return WorkerReply(schema_version=1, outcome="available")
            if request.scope is None or request.operation_id is None:
                raise unavailable()
            frozen: list[PolicySnapshot] = []

            def capacity() -> None:
                if self._active is not None and self._active.is_alive():
                    raise unavailable()

            def snapshot() -> PolicySnapshot:
                policy = self.policy.snapshot()
                if policy.fingerprint != request.config_fingerprint:
                    raise unavailable()
                frozen.append(policy)
                return policy

            admission = self.store.admit(
                _PRINCIPAL,
                request.operation_id,
                ROUTE,
                request.scope.canonical() | {"config_fingerprint": request.config_fingerprint},
                snapshot,
                operation_id=request.operation_id,
                before_admit=capacity,
            )
            if admission.created:
                self._active_operation_id = request.operation_id
                self._active = threading.Thread(
                    target=self._run,
                    args=(request, frozen[0]),
                    name="hfcache-isolated-verification",
                    daemon=False,
                )
                try:
                    self._active.start()
                except RuntimeError:
                    self.store.transition(request.operation_id, "interrupted")
                    raise unavailable() from None
            return self._status(request)

    def _run(self, request: WorkerRequest, snapshot: PolicySnapshot) -> None:
        operation_id, scope = request.operation_id, request.scope
        if operation_id is None or scope is None or request.lock_deadline is None:
            return
        context = ExecutionContext.create(operation_id=operation_id)

        def revalidate() -> None:
            if self.policy.snapshot().fingerprint != snapshot.fingerprint:
                raise unavailable()

        def waiting() -> None:
            self.store.transition(operation_id, "waiting_lock")

        def acquired() -> None:
            self.store.transition(operation_id, "running", domain_run_id=context.run_id)

        deadline = min(
            request.lock_deadline,
            time.monotonic() + snapshot.config.verification.lock_wait_seconds,
        )
        control = CommandLockControl(
            deadline=deadline,
            revalidate=revalidate,
            waiting=waiting,
            acquired=acquired,
            nonblocking=request.try_lock or snapshot.config.verification.lock_wait_seconds == 0,
        )
        verification = VerificationRequest(
            new=scope.mode == "new",
            full=scope.mode == "full",
            revision=scope.revision,
            run_id=scope.run_id,
        )
        try:
            with context.activate(), scoped_command_lock(control):
                _require_budget(request.lock_deadline, try_lock=request.try_lock)
                result = self._execute(snapshot, context, verification).envelope(context)
        except HfcacheError as error:
            result = ServiceResult(
                verification.command, {}, errors=error.problems, exit_code=error.exit_code
            ).envelope(context)
        except Exception:  # noqa: BLE001 - unexplained outcome never becomes fabricated success
            self._interrupt(operation_id)
            return
        try:
            self.store.transition(
                operation_id,
                "succeeded" if result.exit_code == 0 else "failed",
                envelope=result,
            )
        except HfcacheError:
            self._interrupt(operation_id)

    def _interrupt(self, operation_id: str) -> None:
        try:
            if self.store.get(operation_id).state not in {"succeeded", "failed", "interrupted"}:
                self.store.transition(operation_id, "interrupted")
        except HfcacheError:
            pass  # Preserve original durable evidence when even classification cannot be written.

    def close(self) -> None:
        with self._mutex:
            self._closing = True
            active = self._active
        if active is not None:
            active.join()


def validate_listener(
    listener: socket.socket,
    path: Path,
    *,
    bound_address: str | None = None,
    owned_identity: tuple[int, int] | None = None,
) -> None:
    """Keep native canonical checks; owned mode also proves its created inode."""
    parent = -1
    try:
        parent = open_directory(path.parent)
        directory = os.fstat(parent)
        info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        owned = bound_address is not None
        if (
            owned != (owned_identity is not None)
            or (
                owned
                and (
                    (info.st_dev, info.st_ino) != owned_identity
                    or info.st_gid != os.getegid()
                    or stat.S_IMODE(info.st_mode) != SOCKET_MODE
                    or directory.st_uid != os.geteuid()
                    or directory.st_gid != os.getegid()
                    or stat.S_IMODE(directory.st_mode) != DIRECTORY_MODE
                )
            )
            or listener.family != socket.AF_UNIX
            or listener.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_STREAM
            or not listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN)
            or listener.getsockname() != (bound_address if owned else str(path))
            or not stat.S_ISSOCK(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) not in {0o600, 0o660}
            or directory.st_uid not in {0, os.geteuid()}
            or stat.S_IMODE(directory.st_mode) & 0o022
        ):
            raise unavailable()
    except OSError, ValueError:
        raise unavailable() from None
    finally:
        if parent >= 0:
            os.close(parent)


def _require_budget(deadline: float, *, try_lock: bool) -> None:
    if not try_lock and time.monotonic() >= deadline:
        raise unavailable()


def serve_worker(  # noqa: PLR0913 - explicit IPC resource limits and lifecycle ownership
    listener: socket.socket,
    worker: VerificationWorker,
    *,
    expected_uid: int,
    stop: threading.Event,
    timeout_seconds: float = 5.0,
    max_frame_bytes: int = MAX_FRAME_BYTES,
) -> None:
    """Serve one bounded control frame per connection while domain work is joined."""
    listener.settimeout(0.2)
    try:
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            with connection:
                connection.settimeout(timeout_seconds)
                try:
                    check_peer(connection, expected_uid)
                    request = WorkerRequest.model_validate(
                        receive_frame(connection, max_frame_bytes)
                    )
                    reply = worker.handle(request)
                    send_frame(connection, reply, max_frame_bytes)
                except OSError, ValueError, ValidationError, HfcacheError:
                    # Do not echo malformed frames, credentials or raw exceptions.
                    # A disconnect never cancels the already admitted worker.
                    continue
    finally:
        worker.close()
