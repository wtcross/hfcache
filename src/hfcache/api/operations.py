"""Bounded, non-resuming filesystem admission authority (INV-014, decision 114).

Receipts bind keys before work is runnable. They never contain executable request
bodies, reconstruct domain outcomes, or authorize journal replay (FW-02/AD-16).
"""

import fcntl
import hashlib
import json
import os
import re
import secrets
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, Annotated, Any, Literal, Self

from pydantic import BeforeValidator, Field, ValidationError, model_validator

from hfcache.api.auth import Capability, CredentialClass, Principal, require_capability
from hfcache.api.lifecycle import open_directory
from hfcache.config import ArchiveId  # noqa: TC001 - runtime Pydantic field validation
from hfcache.errors import OperationError, RequestError
from hfcache.models import (
    DurableModel,
    RunIdField,
    Sha256,
    Timestamp,
    VersionedModel,
    as_tuple,
    dump,
    serialize,
)
from hfcache.redaction import redact_text, sanitize
from hfcache.reporting import Envelope
from hfcache.storage import atomic_write_bytes

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from hfcache.server_config import PolicySnapshot

OperationState = Literal["queued", "waiting_lock", "running", "succeeded", "failed", "interrupted"]
_TERMINAL = frozenset({"succeeded", "failed"})
_TRANSITIONS = {
    "queued": {"waiting_lock", "running", "failed", "interrupted"},
    "waiting_lock": {"running", "failed", "interrupted"},
    "running": {"succeeded", "failed", "interrupted"},
    "succeeded": set(),
    "failed": set(),
    "interrupted": set(),
}
_ID = re.compile(r"[a-f0-9]{32}")
_KEY = re.compile(r"[A-Za-z0-9._~+-]{1,128}")
_ROUTE = re.compile(r"/api/v1/[a-z0-9_/-]{1,200}")
_MAX_REQUEST_BYTES = 8388608
_KIND = re.compile(r"[a-z][a-z0-9_.-]{0,63}")


@dataclass(frozen=True, slots=True)
class OperationLimits:
    max_records: int = 1000
    max_receipt_bytes: int = 1048576
    max_result_bytes: int = 8388608
    max_events: int = 256
    max_event_bytes: int = 2048
    max_store_bytes: int = 268435456
    retention_days: int = 30

    def __post_init__(self) -> None:
        if any(type(value) is not int or value <= 0 for value in self.__dict_values()):
            msg = "operation limits must be positive integers"
            raise ValueError(msg)

    def __dict_values(self) -> tuple[int, ...]:
        return (
            self.max_records,
            self.max_receipt_bytes,
            self.max_result_bytes,
            self.max_events,
            self.max_event_bytes,
            self.max_store_bytes,
            self.retention_days,
        )


_DEFAULT_LIMITS = OperationLimits()


OPERATION_SCHEMA_VERSION = 1


class OperationModel(VersionedModel):
    schema_version: int = OPERATION_SCHEMA_VERSION

    @model_validator(mode="after")
    def _check_schema_version(self) -> Self:
        if self.schema_version != OPERATION_SCHEMA_VERSION:
            message = "unsupported operation record schema version"
            raise ValueError(message)
        return self


class OperationEvent(OperationModel):
    sequence: int = Field(ge=1)
    at: Timestamp
    kind: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")
    message: str


class ResultReference(OperationModel):
    operation_id: RunIdField
    sha256: Sha256
    bytes: int = Field(gt=0)


def _principal(value: object) -> CredentialClass:
    if not isinstance(value, str):
        message = "principal must name an authenticated credential class"
        raise ValueError(message)  # noqa: TRY004 - Pydantic collects ValueError only
    principal = CredentialClass(value)
    if principal is CredentialClass.MCP_READER:
        message = "operation receipts require a REST principal"
        raise ValueError(message)
    return principal


class OperationReceipt(OperationModel):
    operation_id: RunIdField
    principal: Annotated[CredentialClass, BeforeValidator(_principal)]
    key_digest: Sha256
    request_digest: Sha256
    route: str
    archive_id: ArchiveId
    config_fingerprint: Sha256
    state: OperationState
    created_at: Timestamp
    updated_at: Timestamp
    completed_at: Timestamp | None = None
    domain_run_id: RunIdField | None = None
    transaction_ids: Annotated[tuple[RunIdField, ...], BeforeValidator(as_tuple)] = ()
    result: ResultReference | None = None
    events: Annotated[tuple[OperationEvent, ...], BeforeValidator(as_tuple)] = ()
    next_event_sequence: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if not _ROUTE.fullmatch(self.route) or "//" in self.route:
            msg = "invalid canonical route"
            raise ValueError(msg)
        if self.updated_at < self.created_at or (
            self.completed_at is not None and self.completed_at != self.updated_at
        ):
            msg = "operation timestamps are inconsistent"
            raise ValueError(msg)
        if (self.state in _TERMINAL) != (self.result is not None):
            msg = "terminal success/failure requires an exact result"
            raise ValueError(msg)
        if self.state in _TERMINAL and self.domain_run_id is None:
            message = "terminal result must retain its domain run identity"
            raise ValueError(message)
        if (self.state in _TERMINAL or self.state == "interrupted") != (
            self.completed_at is not None
        ):
            msg = "completion timestamp contradicts state"
            raise ValueError(msg)
        if self.result is not None and self.result.operation_id != self.operation_id:
            msg = "result identity differs from receipt"
            raise ValueError(msg)
        sequences = tuple(event.sequence for event in self.events)
        if (
            sequences
            and (
                sequences[-1] + 1 != self.next_event_sequence
                or any(value != sequences[0] + index for index, value in enumerate(sequences))
            )
        ) or (not sequences and self.next_event_sequence != 1):
            message = "event sequence is inconsistent"
            raise ValueError(message)
        if len(set(self.transaction_ids)) != len(self.transaction_ids):
            message = "transaction identities must be distinct"
            raise ValueError(message)
        return self


@dataclass(frozen=True, slots=True)
class Admission:
    receipt: OperationReceipt
    created: bool


@dataclass(frozen=True, slots=True)
class EventPage:
    events: tuple[OperationEvent, ...]
    next_cursor: int
    oldest_sequence: int
    truncated: bool


def _missing() -> OperationError:
    return OperationError(
        code="HFAPI013",
        status_code=404,
        message="Operation history is missing or expired; execution is unknown",
    )


def _state_error() -> OperationError:
    return OperationError(
        code="HFAPI015",
        status_code=409,
        message="Operation state transition is invalid or uncertain",
    )


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise RequestError
    return value


def _key_digest(value: str) -> str:
    if not isinstance(value, str) or not _KEY.fullmatch(value):
        raise RequestError
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            message = "duplicate JSON field"
            raise ValueError(message)
        payload[key] = value
    return payload


def _decode[ModelT: DurableModel](model: type[ModelT], body: bytes) -> ModelT:
    try:
        payload = json.loads(body, object_pairs_hook=_unique_object)
        if (
            not isinstance(payload, dict)
            or type(payload.get("schema_version")) is not int
            or payload["schema_version"] != OPERATION_SCHEMA_VERSION
        ):
            raise OperationError
        return model.model_validate(payload)
    except ValueError, UnicodeError, RecursionError:
        raise OperationError from None


def request_digest(route: str, request: Mapping[str, Any]) -> str:
    """Hash validated JSON semantics, never persist the candidate request body."""
    if not isinstance(route, str) or not _ROUTE.fullmatch(route) or "//" in route:
        raise RequestError
    try:
        body = serialize({"route": route, "request": dict(request)}, indent=None).encode()
    except ValueError, TypeError, RecursionError:
        raise RequestError from None
    if len(body) > _MAX_REQUEST_BYTES:
        raise RequestError(status_code=413)
    return hashlib.sha256(body).hexdigest()


class OperationStore:
    """Pinned local state, independent of archive flock; no execution side effects.

    Use one lifespan-owned instance. A per-handle mutex plus a persistent flock
    serializes separate handles/processes. All filesystem acts use pinned fds.
    Unknown artifacts remain untouched and prevent fresh admission (AD-16).
    """

    def __init__(
        self,
        root: Path,
        *,
        limits: OperationLimits = _DEFAULT_LIMITS,
        clock: Callable[[], datetime] | None = None,
        checkpoint: Callable[[str], None] | None = None,
    ) -> None:
        self.root = root
        self.limits = limits
        self.clock = clock or (lambda: datetime.now(UTC))
        self.checkpoint = checkpoint
        self._mutex = RLock()
        self._fd = -1
        self._lock_fd = -1
        self._closed = False
        parent = -1
        try:
            parent = open_directory(root.parent)
            try:
                os.mkdir(root.name, mode=0o700, dir_fd=parent)
                os.fsync(parent)
            except FileExistsError:
                pass
            self._fd = os.open(
                root.name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent,
            )
            self._validate(os.fstat(self._fd), directory=True)
            self._lock_fd = os.open(
                ".lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                0o600,
                dir_fd=self._fd,
            )
            self._validate(os.fstat(self._lock_fd))
            os.fsync(self._fd)
        except OSError, ValueError, OperationError:
            self.close()
            raise OperationError from None
        finally:
            if parent >= 0:
                os.close(parent)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        with self._mutex:
            for name in ("_lock_fd", "_fd"):
                descriptor = getattr(self, name)
                if descriptor >= 0:
                    os.close(descriptor)
                    setattr(self, name, -1)
            self._closed = True

    @staticmethod
    def _validate(info: os.stat_result, *, directory: bool = False) -> None:
        if (
            info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != (0o700 if directory else 0o600)
            or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
            or (not directory and info.st_nlink != 1)
        ):
            raise OperationError

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._mutex:
            if self._closed:
                raise OperationError
            try:
                self._validate(os.fstat(self._fd), directory=True)
                self._validate(os.fstat(self._lock_fd))
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX)
                linked = os.stat(".lock", dir_fd=self._fd, follow_symlinks=False)
                held = os.fstat(self._lock_fd)
                if (linked.st_dev, linked.st_ino) != (held.st_dev, held.st_ino):
                    raise OperationError
                yield
            except OSError:
                raise OperationError from None
            finally:
                if not self._closed:
                    fcntl.flock(self._lock_fd, fcntl.LOCK_UN)

    def _read(self, name: str, maximum: int) -> bytes:
        descriptor = -1
        try:
            descriptor = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=self._fd
            )
            before = os.fstat(descriptor)
            self._validate(before)
            if before.st_size > maximum:
                raise OperationError
            body = bytearray()
            while len(body) <= maximum:
                chunk = os.read(descriptor, min(65536, maximum + 1 - len(body)))
                if not chunk:
                    break
                body.extend(chunk)
            after = os.fstat(descriptor)
            if (
                len(body) != before.st_size
                or len(body) > maximum
                or (
                    before.st_dev,
                    before.st_ino,
                    before.st_mode,
                    before.st_uid,
                    before.st_nlink,
                    before.st_size,
                    before.st_mtime_ns,
                    before.st_ctime_ns,
                )
                != (
                    after.st_dev,
                    after.st_ino,
                    after.st_mode,
                    after.st_uid,
                    after.st_nlink,
                    after.st_size,
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                )
            ):
                raise OperationError
            return bytes(body)
        except FileNotFoundError:
            raise _missing() from None
        except OSError:
            raise OperationError from None
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def _receipt(self, operation_id: str) -> OperationReceipt:
        body = self._read(_identifier(operation_id) + ".json", self.limits.max_receipt_bytes)
        try:
            receipt = _decode(OperationReceipt, body)
        except ValueError, ValidationError:
            raise OperationError from None
        if (
            receipt.operation_id != operation_id
            or len(receipt.events) > self.limits.max_events
            or any(len(dump(event)) > self.limits.max_event_bytes for event in receipt.events)
        ):
            raise OperationError
        return receipt

    def _scan(self) -> tuple[tuple[OperationReceipt, ...], int]:
        receipts = []
        names = []
        total = 0
        with os.scandir(self._fd) as entries:
            for entry in entries:
                if len(names) > self.limits.max_records * 2 + 1:
                    raise OperationError
                names.append(entry.name)
        for name in sorted(names):
            if name == ".lock":
                continue
            info = os.stat(name, dir_fd=self._fd, follow_symlinks=False)
            self._validate(info)
            total += info.st_size
            if total > self.limits.max_store_bytes:
                raise OperationError
            if name.endswith(".json") and _ID.fullmatch(name[:-5]):
                receipts.append(self._receipt(name[:-5]))
            elif not (name.endswith(".result.json") and _ID.fullmatch(name[:-12])):
                raise OperationError
        if len(receipts) > self.limits.max_records or total > self.limits.max_store_bytes:
            raise OperationError
        ids = {record.operation_id for record in receipts}
        if any(name.endswith(".result.json") and name[:-12] not in ids for name in names):
            raise OperationError
        for record in receipts:
            if record.state in _TERMINAL:
                self._result(record)
        bindings = [(record.principal, record.key_digest) for record in receipts]
        if len(set(bindings)) != len(bindings):
            raise OperationError
        return tuple(
            sorted(receipts, key=lambda record: (record.created_at, record.operation_id))
        ), total

    def _write(self, name: str, payload: bytes, maximum: int) -> None:
        if len(payload) > maximum:
            raise OperationError
        try:
            atomic_write_bytes(
                Path(name), payload, mode=0o600, dir_fd=self._fd, checkpoint=self.checkpoint
            )
        except OSError:
            raise OperationError from None

    def _save(self, record: OperationReceipt) -> OperationReceipt:
        self._write(record.operation_id + ".json", dump(record), self.limits.max_receipt_bytes)
        return record

    def _lookup(self, principal: Principal, digest: str) -> OperationReceipt | None:
        records, _ = self._scan()
        return next(
            (
                record
                for record in records
                if record.principal == principal.credential_class and record.key_digest == digest
            ),
            None,
        )

    def lookup(self, principal: Principal, key: str) -> OperationReceipt:
        require_capability(principal, Capability.READ)
        digest = _key_digest(key)
        with self._locked():
            record = self._lookup(principal, digest)
            if record is None:
                raise _missing()
            return record

    def get(self, operation_id: str) -> OperationReceipt:
        with self._locked():
            return self._receipt(operation_id)

    def list(self) -> tuple[OperationReceipt, ...]:
        with self._locked():
            records, _ = self._scan()
            return tuple(reversed(records))

    def admit(
        self,
        principal: Principal,
        key: str,
        route: str,
        request: Mapping[str, Any],
        snapshot: Callable[[], PolicySnapshot],
    ) -> Admission:
        require_capability(principal, Capability.READ)
        key_hash = _key_digest(key)
        digest = request_digest(route, request)
        with self._locked():
            records, total = self._scan()
            previous = next(
                (
                    record
                    for record in records
                    if record.principal == principal.credential_class
                    and record.key_digest == key_hash
                ),
                None,
            )
            if previous is not None:
                if previous.request_digest != digest or previous.route != route:
                    raise RequestError(
                        code="HFAPI012",
                        status_code=409,
                        message="Idempotency key conflicts with its admitted request",
                    )
                os.fsync(self._fd)
                return Admission(previous, created=False)
            reservation = self.limits.max_receipt_bytes + self.limits.max_result_bytes
            reserved = sum(reservation for record in records if record.state not in _TERMINAL)
            terminal_bytes = total - sum(
                os.stat(
                    record.operation_id + ".json", dir_fd=self._fd, follow_symlinks=False
                ).st_size
                for record in records
                if record.state not in _TERMINAL
            )
            if (
                len(records) >= self.limits.max_records
                or terminal_bytes + reserved + reservation > self.limits.max_store_bytes
            ):
                raise OperationError
            policy = snapshot()
            now = self.clock()
            operation_id = secrets.token_hex(16)
            if operation_id in {record.operation_id for record in records}:
                raise OperationError
            receipt = OperationReceipt(
                operation_id=operation_id,
                principal=principal.credential_class,
                key_digest=key_hash,
                request_digest=digest,
                route=route,
                archive_id=policy.config.storage.archive_id,
                config_fingerprint=policy.fingerprint,
                state="queued",
                created_at=now,
                updated_at=now,
            )
            self._save(receipt)
            return Admission(receipt, created=True)

    def transition(
        self,
        operation_id: str,
        state: OperationState,
        *,
        envelope: Envelope | None = None,
        domain_run_id: str | None = None,
        transaction_ids: tuple[str, ...] = (),
    ) -> OperationReceipt:
        with self._locked():
            record = self._receipt(operation_id)
            if state not in _TRANSITIONS[record.state]:
                raise _state_error()
            if (
                domain_run_id is not None
                and record.domain_run_id is not None
                and domain_run_id != record.domain_run_id
            ) or (
                transaction_ids
                and transaction_ids[: len(record.transaction_ids)] != record.transaction_ids
            ):
                raise _state_error()
            reference = None
            body = None
            if state in _TERMINAL:
                if (
                    not isinstance(envelope, Envelope)
                    or (state == "succeeded") != (envelope.exit_code == 0)
                    or (domain_run_id is not None and domain_run_id != envelope.run_id)
                    or (
                        record.domain_run_id is not None and record.domain_run_id != envelope.run_id
                    )
                ):
                    raise _state_error()
                try:
                    safe = Envelope.model_validate(sanitize(envelope.model_dump(mode="json")))
                except ValidationError:
                    raise OperationError from None
                body = dump(safe)
                reference = ResultReference(
                    operation_id=operation_id,
                    sha256=hashlib.sha256(body).hexdigest(),
                    bytes=len(body),
                )
                domain_run_id = domain_run_id or safe.run_id
            elif envelope is not None:
                raise _state_error()
            now = self.clock()
            try:
                updated = OperationReceipt.model_validate(
                    record.model_dump()
                    | {
                        "state": state,
                        "updated_at": now,
                        "completed_at": now
                        if state in _TERMINAL or state == "interrupted"
                        else None,
                        "result": reference,
                        "domain_run_id": domain_run_id or record.domain_run_id,
                        "transaction_ids": transaction_ids or record.transaction_ids,
                    }
                )
            except ValidationError:
                raise _state_error() from None
            if body is not None:
                self._write(operation_id + ".result.json", body, self.limits.max_result_bytes)
            return self._save(updated)

    def append_event(self, operation_id: str, kind: str, message: str) -> OperationReceipt:
        if not isinstance(kind, str) or not _KIND.fullmatch(kind) or not isinstance(message, str):
            raise RequestError
        with self._locked():
            record = self._receipt(operation_id)
            if record.state in _TERMINAL or record.state == "interrupted":
                raise _state_error()
            event = OperationEvent(
                sequence=record.next_event_sequence,
                at=self.clock(),
                kind=kind,
                message=redact_text(message),
            )
            if len(dump(event)) > self.limits.max_event_bytes:
                raise OperationError
            return self._save(
                OperationReceipt.model_validate(
                    record.model_dump()
                    | {
                        "events": (*record.events, event)[-self.limits.max_events :],
                        "next_event_sequence": record.next_event_sequence + 1,
                        "updated_at": event.at,
                    }
                )
            )

    def events(self, operation_id: str, *, after: int = 0, limit: int = 100) -> EventPage:
        if (
            type(after) is not int
            or after < 0
            or type(limit) is not int
            or not 1 <= limit <= self.limits.max_events
        ):
            raise RequestError
        record = self.get(operation_id)
        oldest = record.events[0].sequence if record.events else record.next_event_sequence
        events = tuple(event for event in record.events if event.sequence > after)[:limit]
        return EventPage(
            events, events[-1].sequence if events else after, oldest, after < oldest - 1
        )

    def _result(self, record: OperationReceipt) -> Envelope:
        if record.result is None:
            raise _state_error()
        body = self._read(record.operation_id + ".result.json", self.limits.max_result_bytes)
        if (
            len(body) != record.result.bytes
            or hashlib.sha256(body).hexdigest() != record.result.sha256
        ):
            raise OperationError
        try:
            result = _decode(Envelope, body)
            if result.run_id != record.domain_run_id or (record.state == "succeeded") != (
                result.exit_code == 0
            ):
                raise OperationError
            return Envelope.model_validate(sanitize(result.model_dump(mode="json")))
        except ValueError, ValidationError:
            raise OperationError from None

    def result(self, operation_id: str) -> Envelope:
        with self._locked():
            return self._result(self._receipt(operation_id))

    def interrupt_unfinished(self) -> tuple[str, ...]:
        """Explicit startup classification only; never enqueue or invoke domain code."""
        with self._locked():
            records, _ = self._scan()
            interrupted = []
            for record in records:
                if record.state in {"queued", "waiting_lock", "running"}:
                    now = self.clock()
                    self._save(
                        OperationReceipt.model_validate(
                            record.model_dump()
                            | {
                                "state": "interrupted",
                                "updated_at": now,
                                "completed_at": now,
                            }
                        )
                    )
                    interrupted.append(record.operation_id)
            return tuple(interrupted)

    def expire(self) -> tuple[str, ...]:
        """Only proven terminal success/failure plus exact result permits deletion."""
        with self._locked():
            records, _ = self._scan()
            cutoff = self.clock() - timedelta(days=self.limits.retention_days)
            expired = []
            for record in records:
                if (
                    record.state in _TERMINAL
                    and record.completed_at is not None
                    and record.completed_at <= cutoff
                ):
                    self._result(record)
                    # Remove authority first: a crash leaves an orphan result,
                    # which blocks new admission rather than losing a key silently.
                    os.unlink(record.operation_id + ".json", dir_fd=self._fd)
                    os.fsync(self._fd)
                    os.unlink(record.operation_id + ".result.json", dir_fd=self._fd)
                    os.fsync(self._fd)
                    expired.append(record.operation_id)
            return tuple(expired)
