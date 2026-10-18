"""Private bounded verification IPC; this module never executes archive work.

Only the separately sandboxed executor imports the command implementation.
Socket ownership and Linux peer credentials authenticate this local boundary.
"""

import hashlib
import json
import math
import os
import socket
import stat
import struct
import time
from typing import TYPE_CHECKING, Annotated, Literal, Protocol, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

from hfcache.api.lifecycle import open_directory
from hfcache.api.operations import OperationReceipt  # noqa: TC001 - Pydantic runtime field
from hfcache.errors import OperationError
from hfcache.identity import parse_selector
from hfcache.models import RunIdField, Sha256, dump
from hfcache.reporting import Envelope  # noqa: TC001 - Pydantic runtime field

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from hfcache.services.commands import VerificationRequest

ROUTE = "/api/v1/verifications"
MAX_FRAME_BYTES = 16777216
_HEADER = struct.Struct("!I")
_PEER = struct.Struct("3i")
_MIN_FRAME_BYTES = 2
_MIN_FRAME_LIMIT = 1024
_MAX_TIMEOUT = 60


def unavailable() -> OperationError:
    return OperationError(
        code="HFAPI016", message="Isolated verification executor is unavailable or untrusted"
    )


class _Wire(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)


class VerificationScope(_Wire):
    mode: Literal["new", "full", "revision"]
    revision: str | None = Field(default=None, max_length=256)
    run_id: RunIdField | None = None

    @model_validator(mode="after")
    def valid_scope(self) -> Self:
        if (self.mode == "revision") != (self.revision is not None) or (
            self.run_id is not None and self.mode != "new"
        ):
            message = "verification scope contradicts mode"
            raise ValueError(message)
        if self.revision is not None and parse_selector(self.revision).commit_sha is None:
            message = "verification revision requires an immutable SHA"
            raise ValueError(message)
        return self

    def canonical(self) -> dict[str, object]:
        return self.model_dump(exclude_none=True)


def _version(value: object) -> object:
    if type(value) is not int or value != 1:
        message = "unsupported private protocol version"
        raise ValueError(message)
    return value


class WorkerRequest(_Wire):
    schema_version: Annotated[Literal[1], BeforeValidator(_version)]
    action: Literal["probe", "submit", "status"]
    operation_id: RunIdField | None = None
    config_fingerprint: Sha256 | None = None
    scope: VerificationScope | None = None
    lock_deadline: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    try_lock: bool = False

    @model_validator(mode="after")
    def valid_action(self) -> Self:
        identified = self.operation_id is not None and self.config_fingerprint is not None
        if self.action == "probe":
            valid = (
                all(
                    value is None
                    for value in (
                        self.operation_id,
                        self.config_fingerprint,
                        self.scope,
                        self.lock_deadline,
                    )
                )
                and not self.try_lock
            )
        elif self.action == "submit":
            valid = identified and self.scope is not None and self.lock_deadline is not None
        else:
            valid = (
                identified
                and self.scope is None
                and self.lock_deadline is None
                and not self.try_lock
            )
        if not valid:
            message = "invalid verification protocol action"
            raise ValueError(message)
        return self


class WorkerReply(_Wire):
    schema_version: Annotated[Literal[1], BeforeValidator(_version)]
    outcome: Literal["available", "found", "missing", "unavailable", "conflict"]
    receipt: OperationReceipt | None = None
    envelope: Envelope | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if (self.outcome == "found") != (self.receipt is not None):
            message = "worker reply lacks exact identity"
            raise ValueError(message)
        terminal = self.receipt is not None and self.receipt.state in {"succeeded", "failed"}
        if terminal != (self.envelope is not None):
            message = "worker terminal reply lacks exact result"
            raise ValueError(message)
        if (
            self.envelope is not None
            and self.receipt is not None
            and (
                self.envelope.run_id != self.receipt.domain_run_id
                or (self.envelope.exit_code == 0) != (self.receipt.state == "succeeded")
            )
        ):
            message = "worker result contradicts receipt"
            raise ValueError(message)
        if self.envelope is not None and self.receipt is not None:
            body = dump(self.envelope)
            reference = self.receipt.result
            if reference is None or (
                hashlib.sha256(body).hexdigest() != reference.sha256 or len(body) != reference.bytes
            ):
                message = "worker reply is not the durably referenced result"
                raise ValueError(message)
        return self


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise unavailable()
        result[key] = value
    return result


def _read_exact(connection: socket.socket, count: int) -> bytes:
    body = bytearray()
    while len(body) < count:
        chunk = connection.recv(min(65536, count - len(body)))
        if not chunk:
            raise unavailable()
        body.extend(chunk)
    return bytes(body)


def receive_frame(connection: socket.socket, maximum: int = MAX_FRAME_BYTES) -> object:
    size = _HEADER.unpack(_read_exact(connection, _HEADER.size))[0]
    if size < _MIN_FRAME_BYTES or size > maximum:
        raise unavailable()
    try:
        return json.loads(_read_exact(connection, size), object_pairs_hook=_pairs)
    except ValueError, UnicodeError, RecursionError:
        raise unavailable() from None


def send_frame(
    connection: socket.socket, payload: BaseModel, maximum: int = MAX_FRAME_BYTES
) -> None:
    body = payload.model_dump_json().encode("utf-8")
    if len(body) > maximum:
        raise unavailable()
    connection.sendall(_HEADER.pack(len(body)) + body)


def check_peer(connection: socket.socket, expected_uid: int) -> None:
    try:
        _, uid, _ = _PEER.unpack(
            connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, _PEER.size)
        )
    except OSError, struct.error:
        raise unavailable() from None
    if uid != expected_uid:
        raise unavailable()


def connect_private(path: Path, *, expected_uid: int, timeout_seconds: float) -> socket.socket:
    """Connect through a pinned protected parent, then prove the kernel peer."""
    parent = -1
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        parent = open_directory(path.parent)
        directory = os.fstat(parent)
        info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if (
            directory.st_uid not in {0, os.geteuid()}
            or stat.S_IMODE(directory.st_mode) & 0o022
            or not stat.S_ISSOCK(info.st_mode)
            or info.st_uid != expected_uid
            or stat.S_IMODE(info.st_mode) not in {0o600, 0o660}
        ):
            raise unavailable()
        connection.settimeout(timeout_seconds)
        connection.connect(f"/proc/self/fd/{parent}/{path.name}")
        check_peer(connection, expected_uid)
        current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
            raise unavailable()
    except OSError, ValueError, OperationError:
        connection.close()
        raise unavailable() from None
    else:
        return connection
    finally:
        if parent >= 0:
            os.close(parent)


class VerificationDelegate(Protocol):
    def check_available(self) -> None: ...
    def reconcile(self, receipt: OperationReceipt) -> Envelope | Callable[[], Envelope] | None: ...
    def execute(
        self,
        operation_id: str,
        request: VerificationRequest,
        expected_fingerprint: str,
        remaining_wait_seconds: float,
    ) -> Envelope: ...


class VerificationClient:
    """Injectable client; never spawns a process or falls back to local execution."""

    def __init__(  # noqa: PLR0913 - explicit transport limits and trusted progress observer
        self,
        path: Path,
        *,
        expected_uid: int | None = None,
        timeout_seconds: float = 5.0,
        poll_seconds: float = 0.2,
        max_frame_bytes: int = MAX_FRAME_BYTES,
        progress: Callable[[OperationReceipt], None] | None = None,
        expected_archive_id: str | None = None,
    ) -> None:
        if (
            not path.is_absolute()
            or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= _MAX_TIMEOUT
            or not math.isfinite(poll_seconds)
            or not 0 < poll_seconds <= _MAX_TIMEOUT
            or not _MIN_FRAME_LIMIT <= max_frame_bytes <= MAX_FRAME_BYTES
            or (expected_uid is not None and (type(expected_uid) is not int or expected_uid < 0))
        ):
            raise unavailable()
        self.path = path
        self.expected_uid = os.geteuid() if expected_uid is None else expected_uid
        self.timeout_seconds, self.poll_seconds = timeout_seconds, poll_seconds
        self.max_frame_bytes = max_frame_bytes
        self.progress = progress
        self.expected_archive_id = expected_archive_id

    def exchange(self, request: WorkerRequest) -> WorkerReply:
        try:
            with connect_private(
                self.path, expected_uid=self.expected_uid, timeout_seconds=self.timeout_seconds
            ) as connection:
                send_frame(connection, request, self.max_frame_bytes)
                reply = WorkerReply.model_validate(receive_frame(connection, self.max_frame_bytes))
        except OSError, ValueError, ValidationError, OperationError:
            raise unavailable() from None
        if reply.outcome in {"unavailable", "conflict"}:
            raise unavailable()
        expected = {"probe": {"available"}, "status": {"found", "missing"}, "submit": {"found"}}
        if reply.outcome not in expected[request.action]:
            raise unavailable()
        if reply.receipt is not None and (
            reply.receipt.operation_id != request.operation_id
            or reply.receipt.config_fingerprint != request.config_fingerprint
            or reply.receipt.route != ROUTE
            or (
                self.expected_archive_id is not None
                and reply.receipt.archive_id != self.expected_archive_id
            )
        ):
            raise unavailable()
        if reply.receipt is not None and self.progress is not None:
            self.progress(reply.receipt)
        return reply

    def check_available(self) -> None:
        if self.exchange(WorkerRequest(schema_version=1, action="probe")).outcome != "available":
            raise unavailable()

    def status(self, operation_id: str, expected_fingerprint: str) -> WorkerReply:
        return self.exchange(
            WorkerRequest(
                schema_version=1,
                action="status",
                operation_id=operation_id,
                config_fingerprint=expected_fingerprint,
            )
        )

    def wait_existing(self, operation_id: str, expected_fingerprint: str) -> Envelope:
        while True:
            reply = self.status(operation_id, expected_fingerprint)
            if reply.envelope is not None:
                return reply.envelope
            if reply.receipt is None or reply.receipt.state == "interrupted":
                raise unavailable()
            time.sleep(self.poll_seconds)

    def reconcile(self, receipt: OperationReceipt) -> Envelope | Callable[[], Envelope] | None:
        if receipt.route != ROUTE:
            return None
        reply = self.status(receipt.operation_id, receipt.config_fingerprint)
        if reply.receipt is None:
            return None
        if reply.receipt.archive_id != receipt.archive_id:
            raise unavailable()
        if reply.envelope is not None:
            return reply.envelope
        if reply.receipt.state == "interrupted":
            return None
        return lambda: self.wait_existing(receipt.operation_id, receipt.config_fingerprint)

    def execute(
        self,
        operation_id: str,
        request: VerificationRequest,
        expected_fingerprint: str,
        remaining_wait_seconds: float,
    ) -> Envelope:
        deadline = time.monotonic() + remaining_wait_seconds
        if request.estimate:
            raise unavailable()
        scope = VerificationScope(
            mode="full" if request.full else "revision" if request.revision is not None else "new",
            revision=request.revision,
            run_id=request.run_id,
        )
        if sum((request.full, request.new, request.revision is not None)) != 1:
            raise unavailable()
        reply = self.exchange(
            WorkerRequest(
                schema_version=1,
                action="submit",
                operation_id=operation_id,
                config_fingerprint=expected_fingerprint,
                scope=scope,
                lock_deadline=deadline,
                try_lock=remaining_wait_seconds == 0,
            )
        )
        if reply.receipt is None:
            raise unavailable()
        return reply.envelope or self.wait_existing(operation_id, expected_fingerprint)
