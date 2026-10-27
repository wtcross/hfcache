"""Fixed host effects and original evidence (ADR156); trusted Python3.12/stdlib only."""

# Protected Python3.12 uses captured module objects rather than application imports.
# ruff: noqa: ANN401, SLF001
from __future__ import annotations

import base64
import ctypes
import fcntl
import hashlib
import hmac
import json
import os
import pwd
import re
import select
import selectors
import signal
import stat
import subprocess
import sys
import threading
import time
import uuid
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Generator

ROOT = Path("/etc/hfcache/.host-actions")
LOCK = Path("/etc/hfcache/.host-actions.lock")
PENDING = Path("/etc/hfcache/.host-actions.pending")
SCHEDULE_DIRECTORY = Path("/etc/systemd/system/hfcache-sync.timer.d")
SCHEDULE = SCHEDULE_DIRECTORY / "50-cockpit.conf"
BACKUPS = SCHEDULE_DIRECTORY / ".hfcache-actions"
HELPER = Path("/usr/local/libexec/hfcache-host-helper")
OWNER = OWNER_GID = 0
GUARD_MODE = 0o600
GUARD_TYPE = "hfcache_host_helper_configuration_guard_t"
STATE_TYPE = "hfcache_host_helper_host_action_state_t"
SCHEDULE_TYPE = "hfcache_host_helper_schedule_file_t"
SCHEDULE_DIRECTORY_TYPE = "hfcache_host_helper_schedule_dir_t"
MAX_RECORDS = 128
MAX_PRIVATE_BYTES = 8 * 1024 * 1024
MAX_STATE = 128 * 1024
MAX_DOCUMENT = 16384
KEY_BYTES = 32
MAX_CHILD_REPLY = 4096
MAX_PROC_BYTES = 8192
MAX_PROC_STATUS = 65536
MAX_CURSOR_CHARS = 2048
MAX_PID = 2147483647
MAX_TICKS = 9007199254740991
MIN_PID = 2
PRIVATE_MODE = 0o700
ASCII_MIN = 32
ASCII_MAX = 126
CONTEXT_FIELDS = 4
MIN_PIDFD = 3
MAX_TIMESTAMP_CHARS = 16
MAX_JOURNAL_ENTRIES = 80
MAX_JOURNAL_TEXT = 65536
IDENTITY_FIELDS = 9
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C", "SYSTEMD_COLORS": "0"}
SOURCES = {"sync-observer": "hfcache-sync.service", "verify-observer": "hfcache-verify.service"}
JOURNAL_CAPACITY = threading.BoundedSemaphore(2)
SYNC_OBSERVER_CONTEXT = "system_u:system_r:hfcache_sync_observer_t:s0"
SYNC_OBSERVER_BINDING = "sync_observer_context"
SYNC_OBSERVER_DROP_IN = "/etc/systemd/system/hfcache-sync.service.d/50-hfcache-observer.conf"


def checkpoint(_name: str) -> None:
    """Named syscall boundaries for actual-filesystem crash tests."""


def _need(value: object) -> None:
    if not value:
        msg = "protected host action refused"
        raise ValueError(msg)


def _encoded(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    ).encode()


def _identity(info: os.stat_result) -> list[int]:
    return [
        getattr(info, k)
        for k in (
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
    ]


def _context(path: Path | int) -> str:
    return os.getxattr(path, "security.selinux").rstrip(b"\0").decode("ascii")


def _type(context: str, expected: str) -> None:
    parts = context.split(":", 3)
    _need(
        len(parts) == CONTEXT_FIELDS and parts[1:3] == ["object_r", expected] and parts[3] == "s0"
    )


def _seal(key: bytes, value: object, domain: bytes) -> str:
    return hmac.new(key, domain + b"\0" + _encoded(value), hashlib.sha256).hexdigest()


def _invalid(policy: Any, condition: object) -> None:
    if not condition:
        msg = "invalid-request"
        raise policy.InspectionError(msg)


def _text(value: object, maximum: int) -> bool:
    return (
        type(value) is str
        and 1 <= len(value) <= maximum
        and bool(value.strip())
        and "\\" not in value
        and all(ASCII_MIN <= ord(c) <= ASCII_MAX for c in value)
    )


def _expected(policy: Any, value: object) -> dict[str, Any]:
    value = cast("dict[str, Any]", value)
    _invalid(
        policy,
        type(value) is dict
        and set(value) == {"boot_id", "invocation_id", "main_pid", "start_ticks"},
    )
    _invalid(
        policy,
        type(value["boot_id"]) is str and str(uuid.UUID(value["boot_id"])) == value["boot_id"],
    )
    _invalid(
        policy, type(value["invocation_id"]) is str and HEX32.fullmatch(value["invocation_id"])
    )
    _invalid(
        policy,
        type(value["main_pid"]) is int
        and MIN_PID <= value["main_pid"] <= MAX_PID
        and type(value["start_ticks"]) is int
        and 1 <= value["start_ticks"] <= MAX_TICKS,
    )
    return dict(value)


def _request(policy: Any, body: object, kind: str, *, effect: bool = False) -> dict[str, Any]:
    _invalid(policy, type(body) is dict)
    body = cast("dict[str, Any]", body)
    if effect:
        _invalid(policy, set(body) == {"operation_id", "request_digest", "request"})
        _invalid(
            policy,
            type(body["operation_id"]) is str
            and HEX32.fullmatch(body["operation_id"])
            and type(body["request_digest"]) is str
            and HEX64.fullmatch(body["request_digest"]),
        )
        _request(policy, body["request"], kind)
    elif kind == "schedule":
        _invalid(policy, body.get("action") in {"pause", "resume", "replace", "reset"})
        names = {"action", "expected_revision"} | (
            {"on_calendar", "randomized_delay_sec"} if body["action"] == "replace" else set()
        )
        _invalid(
            policy,
            set(body) == names
            and type(body["expected_revision"]) is str
            and HEX64.fullmatch(body["expected_revision"]),
        )
        if body["action"] == "replace":
            _request(
                policy, {k: body[k] for k in ("on_calendar", "randomized_delay_sec")}, "validate"
            )
    elif kind == "validate":
        _invalid(
            policy,
            set(body) == {"on_calendar", "randomized_delay_sec"}
            and _text(body["on_calendar"], 4096)
            and (body["randomized_delay_sec"] is None or _text(body["randomized_delay_sec"], 256)),
        )
    elif kind == "observer":
        _invalid(policy, set(body) == {"expected"})
        _expected(policy, body["expected"])
    else:
        _invalid(
            policy,
            set(body) == {"operation_id", "request_digest"}
            and type(body["operation_id"]) is str
            and HEX32.fullmatch(body["operation_id"])
            and type(body["request_digest"]) is str
            and HEX64.fullmatch(body["request_digest"]),
        )
    return dict(body)


class _Files:
    """The proven descriptor-relative configuration filesystem pattern, separate authority."""

    def __init__(self, policy: Any, snapshot: Any) -> None:
        self.policy, self.snapshot = policy, snapshot
        self.budget = snapshot.budget
        self.key = snapshot._inspection.key
        _need(type(self.key) is bytes and len(self.key) == KEY_BYTES)
        self.parents: dict[Path, tuple[int, ...]] = {}

    def parent(self, path: Path) -> int:
        self.snapshot._inspection.capture.local(path)
        current = Path("/")
        descriptor = os.open(current, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            for part in (*path.parent.parts[1:], None):
                info = os.fstat(descriptor)
                _need(info.st_uid in {0, OWNER} and stat.S_ISDIR(info.st_mode))
                _need(
                    not info.st_mode & 0o022 or (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)
                )
                parent_identity = tuple(
                    getattr(info, name)
                    for name in ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid")
                )
                _need(current not in self.parents or self.parents[current] == parent_identity)
                self.parents[current] = parent_identity
                self.budget.remaining()
                if part is not None:
                    child = os.open(
                        part,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                        dir_fd=descriptor,
                    )
                    os.close(descriptor)
                    descriptor = child
                    current /= part
            return descriptor  # noqa: TRY300 - descriptor ownership transfers here
        except BaseException:
            os.close(descriptor)
            raise

    def read(
        self,
        path: Path,
        *,
        mode: int,
        kind: str,
        maximum: int = MAX_DOCUMENT,
        gid: int | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        self.budget.consume(files=1)
        parent = self.parent(path)
        descriptor = -1
        try:
            descriptor = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent
            )
            info = os.fstat(descriptor)
            _need(stat.S_ISREG(info.st_mode) and info.st_uid == OWNER and info.st_nlink == 1)
            _need(stat.S_IMODE(info.st_mode) == mode and 0 <= info.st_size <= maximum)
            _need(gid is None or info.st_gid == gid)
            context = _context(descriptor)
            _type(context, kind)
            output = bytearray()
            while True:
                self.budget.remaining()
                chunk = os.read(descriptor, min(65536, maximum + 1 - len(output)))
                if not chunk:
                    break
                output.extend(chunk)
                self.budget.consume(size=len(chunk))
                _need(len(output) <= maximum)
            _need(len(output) == info.st_size)
            _need(
                _identity(info)
                == _identity(os.fstat(descriptor))
                == _identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
            )
            _need(_context(descriptor) == context)
            body = bytes(output)
            return body, {
                "identity": _identity(info),
                "context": context,
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            os.close(parent)

    def sync(self, path: Path, label: str) -> None:
        descriptor = self.parent(path)
        try:
            checkpoint(label + ":before_directory_fsync")
            os.fsync(descriptor)
            checkpoint(label + ":after_directory_fsync")
        finally:
            os.close(descriptor)

    def write(self, path: Path, body: bytes, *, mode: int, gid: int, kind: str, label: str) -> None:  # noqa: PLR0913 - explicit file metadata
        self.budget.consume(files=1, size=len(body))
        parent = self.parent(path)
        descriptor = -1
        try:
            checkpoint(label + ":before_write")
            descriptor = os.open(
                path.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                mode,
                dir_fd=parent,
            )
            os.fchown(descriptor, OWNER, gid)
            os.fchmod(descriptor, mode)
            _type(_context(descriptor), kind)
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(body)
                stream.flush()
                checkpoint(label + ":before_file_fsync")
                os.fsync(descriptor)
                checkpoint(label + ":after_file_fsync")
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            os.close(parent)
        self.sync(path, label)

    def rename(self, source: Path, target: Path, *, flags: int, label: str) -> None:
        source_parent, target_parent = self.parent(source), -1
        try:
            target_parent = self.parent(target)
            library = ctypes.CDLL(None, use_errno=True)
            library.renameat2.argtypes = (
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_uint,
            )
            library.renameat2.restype = ctypes.c_int
            checkpoint(label + ":before_rename")
            if (
                library.renameat2(
                    source_parent,
                    os.fsencode(source.name),
                    target_parent,
                    os.fsencode(target.name),
                    flags,
                )
                != 0
            ):
                raise OSError(ctypes.get_errno(), "protected configuration rename refused")
            checkpoint(label + ":after_rename")
        finally:
            if target_parent >= 0:
                os.close(target_parent)
            os.close(source_parent)
        self.sync(source, label + ":source")
        self.sync(target, label + ":target")

    @contextmanager
    def locked(self) -> Generator[None, None, None]:
        parent = self.parent(LOCK)
        descriptor = -1
        try:
            descriptor = os.open(LOCK.name, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
            info = os.fstat(descriptor)
            _need(stat.S_ISREG(info.st_mode) and info.st_uid == OWNER and info.st_nlink == 1)
            _need(stat.S_IMODE(info.st_mode) == GUARD_MODE and info.st_gid == OWNER_GID)
            _type(_context(descriptor), GUARD_TYPE)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _need(
                _identity(info)
                == _identity(os.stat(LOCK.name, dir_fd=parent, follow_symlinks=False))
            )
            yield
            _need(
                _identity(info)
                == _identity(os.fstat(descriptor))
                == _identity(os.stat(LOCK.name, dir_fd=parent, follow_symlinks=False))
            )
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            os.close(parent)

    def directory(self, path: Path, *, create: bool = False, kind: str = STATE_TYPE) -> None:
        parent = self.parent(path)
        try:
            if create:
                checkpoint("directory:before_mkdir")
                os.mkdir(path.name, 0o700, dir_fd=parent)
                os.fsync(parent)
                checkpoint("directory:after_directory_fsync")
            descriptor = os.open(
                path.name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent,
            )
            try:
                info = os.fstat(descriptor)
                _need(
                    info.st_uid == OWNER
                    and info.st_gid == OWNER_GID
                    and stat.S_IMODE(info.st_mode) == PRIVATE_MODE
                )
                _type(_context(descriptor), kind)
                identity = tuple(
                    getattr(info, name)
                    for name in ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid")
                )
                _need(path not in self.parents or self.parents[path] == identity)
                self.parents[path] = identity
                _need(
                    _identity(info)
                    == _identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
                )
            finally:
                os.close(descriptor)
        finally:
            os.close(parent)

    def authenticated(self, path: Path, domain: bytes) -> dict[str, Any]:
        raw, _ = self.read(
            path,
            mode=0o600,
            kind=GUARD_TYPE if path == PENDING else STATE_TYPE,
            maximum=MAX_STATE,
            gid=OWNER_GID,
        )
        value = self.policy._json(raw)
        _need(set(value) == {"record", "authentication"} and type(value["record"]) is dict)
        _need(
            type(value["authentication"]) is str
            and hmac.compare_digest(
                value["authentication"], _seal(self.key, value["record"], domain)
            )
        )
        return value["record"]

    def save(self, record: dict[str, Any]) -> None:
        path = ROOT / record["operation_id"]
        target = path / "record.json"
        if os.path.lexists(target):
            old = self.authenticated(target, b"host-action-record-v1")
            _need(
                old["operation_id"] == record["operation_id"]
                and old["request_digest"] == record["request_digest"]
            )
        body = _encoded(
            {"record": record, "authentication": _seal(self.key, record, b"host-action-record-v1")}
        )
        _need(len(body) <= MAX_STATE)
        temporary = path / ".record.tmp"
        self.write(
            temporary,
            body,
            mode=0o600,
            gid=OWNER_GID,
            kind=STATE_TYPE,
            label=record["outcome"]["state"],
        )
        self.rename(temporary, target, flags=0, label="record")


def _authority(policy: Any, snapshot: Any, permission: str | None = None) -> dict[str, Any]:
    policy.revalidate(snapshot)
    status = snapshot.host_action_status()
    if permission is not None:
        policy.require_host_actions(snapshot)
        if snapshot.profile != "native" or not status["permissions"][permission]:
            msg = "operation-denied"
            raise policy.InspectionError(msg)
    return status


def _outcome(snapshot: Any, body: dict[str, Any], kind: str) -> dict[str, Any]:
    value = {
        "schema_version": 1,
        "archive_id": snapshot.archive_id,
        "operation_id": body["operation_id"],
        "request_digest": body["request_digest"],
        "state": "unknown",
        "pending": os.path.lexists(PENDING),
    }
    if kind == "schedule":
        value.update(
            action=None,
            expected_revision=None,
            stored_revision=None,
            file_state="unknown",
            manager_state="unknown",
            timer_was_active=None,
            timer_is_active=None,
        )
    else:
        value.update(expected=None, stop_state="unknown")
    return value


def _load(  # noqa: PLR0912 - keep both closed durable outcome variants beside their bindings
    files: _Files, body: dict[str, Any], kind: str
) -> dict[str, Any] | None:
    path = ROOT / body["operation_id"]
    if not os.path.lexists(path):
        return None
    files.directory(path)
    _need({p.name for p in _entries(path, 1)} == {"record.json"})
    value = files.authenticated(path / "record.json", b"host-action-record-v1")
    _need(
        set(value)
        == {
            "schema_version",
            "kind",
            "operation_id",
            "request_digest",
            "archive_id",
            "request",
            "outcome",
            "predecessor",
        }
    )
    _need(
        type(value["schema_version"]) is int
        and value["schema_version"] == 1
        and value["kind"] == kind
        and value["operation_id"] == body["operation_id"]
        and value["archive_id"] == files.snapshot.archive_id
    )
    if not hmac.compare_digest(value["request_digest"], body["request_digest"]):
        msg = "config-conflict"
        raise files.policy.InspectionError(msg)
    _request(files.policy, value["request"], kind)
    result = value["outcome"]
    _need(
        type(result) is dict
        and result["operation_id"] == body["operation_id"]
        and result["request_digest"] == body["request_digest"]
        and result["archive_id"] == value["archive_id"]
    )
    common = {"schema_version", "archive_id", "operation_id", "request_digest", "state", "pending"}
    _need(type(result["schema_version"]) is int and result["schema_version"] == 1)
    _need(type(result["pending"]) is bool)
    _need(
        result["state"] in {"prepared", "effect_unconfirmed", "confirmed", "unchanged", "unknown"}
    )
    if kind == "observer":
        _need(set(result) == common | {"expected", "stop_state"})
        _need(result["expected"] == value["request"]["expected"])
        _need(result["stop_state"] in {"not_sent", "acknowledged", "exit_confirmed", "unknown"})
        _need(value["predecessor"] is None)
        if result["state"] == "confirmed":
            _need(result["stop_state"] == "exit_confirmed")
        if result["state"] in {"prepared", "unchanged"}:
            _need(result["stop_state"] == "not_sent")
    else:
        _need(
            set(result)
            == common
            | {
                "action",
                "expected_revision",
                "stored_revision",
                "file_state",
                "manager_state",
                "timer_was_active",
                "timer_is_active",
            }
        )
        _need(
            result["action"] == value["request"]["action"]
            and result["expected_revision"] == value["request"]["expected_revision"]
            and type(result["stored_revision"]) is str
            and HEX64.fullmatch(result["stored_revision"])
            and type(result["timer_was_active"]) is bool
            and type(result["timer_is_active"]) is bool
            and result["file_state"] in {"unchanged", "installed", "removed", "unknown"}
            and result["manager_state"]
            in {"not_sent", "reload_acknowledged", "timer_acknowledged", "unknown"}
        )
        if result["state"] in {"prepared", "unchanged"}:
            _need(result["file_state"] == "unchanged" and result["manager_state"] == "not_sent")
            if result["state"] == "prepared":
                _need(result["expected_revision"] == result["stored_revision"])
            else:
                _need(result["timer_was_active"] == result["timer_is_active"])
        if result["state"] == "confirmed":
            if result["action"] in {"pause", "resume"}:
                _need(
                    result["file_state"] == "unchanged"
                    and result["expected_revision"] == result["stored_revision"]
                    and result["manager_state"] == "timer_acknowledged"
                    and result["timer_is_active"] == (result["action"] == "resume")
                )
            else:
                _need(
                    result["file_state"]
                    in (
                        {"installed"} if result["action"] == "replace" else {"removed", "unchanged"}
                    )
                    and result["timer_is_active"] == result["timer_was_active"]
                    and result["manager_state"]
                    == (
                        "timer_acknowledged"
                        if result["timer_was_active"]
                        else "reload_acknowledged"
                    )
                )
        predecessor = value["predecessor"]
        if predecessor is not None:
            _need(
                type(predecessor) is dict
                and set(predecessor) == {"identity", "context", "sha256"}
                and type(predecessor["identity"]) is list
                and len(predecessor["identity"]) == IDENTITY_FIELDS
                and all(type(field) is int and field >= 0 for field in predecessor["identity"])
                and type(predecessor["context"]) is str
                and type(predecessor["sha256"]) is str
                and HEX64.fullmatch(predecessor["sha256"])
            )
    if result["state"] == "prepared":
        _need(result["pending"])
    if result["state"] == "unchanged":
        _need(not result["pending"])
    return value


def _pending(files: _Files) -> dict[str, Any] | None:
    if not os.path.lexists(PENDING):
        return None
    value = files.authenticated(PENDING, b"host-action-pending-v1")
    _request(files.policy, {k: value.get(k) for k in ("operation_id", "request_digest")}, "outcome")
    _need(
        set(value) == {"operation_id", "request_digest", "kind"}
        and value["kind"] in {"schedule", "observer"}
    )
    return value


def _observe(files: _Files, body: dict[str, Any], kind: str) -> dict[str, Any]:
    pending = _pending(files)
    if (
        pending
        and pending["operation_id"] == body["operation_id"]
        and pending["request_digest"] != body["request_digest"]
    ):
        msg = "config-conflict"
        raise files.policy.InspectionError(msg)
    _need(
        pending is None
        or pending["operation_id"] != body["operation_id"]
        or pending["kind"] == kind
    )
    try:
        record = _load(files, body, kind)
    except files.policy.InspectionError:
        raise
    except (OSError, ValueError, KeyError, TypeError):
        return _outcome(files.snapshot, body, kind)
    if record is None:
        return _outcome(files.snapshot, body, kind)
    result = dict(record["outcome"])
    result["pending"] = pending is not None
    if pending is not None and result["state"] == "unchanged":
        result["state"] = "unknown"
    return result


def _read_outcome(policy: Any, snapshot: Any, body: object, kind: str) -> dict[str, Any]:
    request = _request(policy, body, "outcome")
    policy.revalidate(snapshot)
    files = _Files(policy, snapshot)
    try:
        with files.locked():
            result = _observe(files, request, kind)
            policy.revalidate(snapshot)
            return result
    except policy.InspectionError:
        raise
    except (OSError, ValueError, KeyError, TypeError):
        return _outcome(snapshot, request, kind)


def read_schedule_outcome(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:
    return _read_outcome(policy, snapshot, body, "schedule")


def read_observer_outcome(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:
    return _read_outcome(policy, snapshot, body, "observer")


def _entries(path: Path, maximum: int) -> list[Path]:
    paths = []
    with os.scandir(path) as entries:
        for entry in entries:
            _need(len(paths) < maximum)
            paths.append(path / entry.name)
    return paths


def _retained(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    _need(
        actual["identity"][:-1] == expected["identity"][:-1]
        and actual["context"] == expected["context"]
        and actual["sha256"] == expected["sha256"]
    )


def _history(files: _Files) -> None:
    files.directory(ROOT)
    paths = _entries(ROOT, MAX_RECORDS)
    _need(len(paths) < MAX_RECORDS)
    used = 0
    records = {}
    for path in paths:
        _need(HEX32.fullmatch(path.name))
        files.directory(path)
        record = files.authenticated(path / "record.json", b"host-action-record-v1")
        _need(
            record["operation_id"] == path.name
            and record["outcome"]["state"] in {"confirmed", "unchanged"}
        )
        _load(
            files,
            {"operation_id": path.name, "request_digest": record["request_digest"]},
            record["kind"],
        )
        records[path.name] = record
        used += (path / "record.json").stat().st_size
    files.directory(BACKUPS)
    retained = set()
    for path in _entries(BACKUPS, MAX_RECORDS):
        _need(HEX32.fullmatch(path.name) and path.name in records)
        record = records[path.name]
        _need(
            record["kind"] == "schedule"
            and record["request"]["action"] in {"replace", "reset"}
            and record["outcome"]["state"] == "confirmed"
        )
        retained.add(path.name)
        files.directory(path)
        children = _entries(path, 1)
        predecessor = record["predecessor"]
        _need({p.name for p in children} == ({"predecessor.conf"} if predecessor else set()))
        for child in children:
            data, actual = files.read(child, mode=0o644, kind=SCHEDULE_TYPE, gid=OWNER_GID)
            _retained(actual, predecessor)
            used += len(data)
    _need(
        retained
        == {
            operation_id
            for operation_id, record in records.items()
            if record["kind"] == "schedule"
            and record["request"]["action"] in {"replace", "reset"}
            and record["outcome"]["state"] == "confirmed"
        }
    )
    _need(used + MAX_STATE * 2 + MAX_DOCUMENT * 2 <= MAX_PRIVATE_BYTES)


def _begin(
    files: _Files,
    request: dict[str, Any],
    kind: str,
    outcome: dict[str, Any],
    predecessor: Any = None,
) -> dict[str, Any]:
    _need(_pending(files) is None)
    _history(files)
    intent = {k: request[k] for k in ("operation_id", "request_digest")}
    intent["kind"] = kind
    files.write(
        PENDING,
        _encoded(
            {
                "record": intent,
                "authentication": _seal(files.key, intent, b"host-action-pending-v1"),
            }
        ),
        mode=0o600,
        gid=OWNER_GID,
        kind=GUARD_TYPE,
        label="pending",
    )
    files.directory(ROOT / request["operation_id"], create=True)
    record = {
        "schema_version": 1,
        "kind": kind,
        "operation_id": request["operation_id"],
        "request_digest": request["request_digest"],
        "archive_id": files.snapshot.archive_id,
        "request": request["request"],
        "outcome": outcome,
        "predecessor": predecessor,
    }
    files.save(record)
    return record


def _finish(files: _Files, record: dict[str, Any], *, state: str = "confirmed") -> dict[str, Any]:
    record["outcome"]["state"] = state
    files.save(record)
    value = _pending(files)
    _need(value == {k: record[k] for k in ("operation_id", "request_digest", "kind")})
    checkpoint("pending:before_unlink")
    PENDING.unlink()
    checkpoint("pending:after_unlink")
    files.sync(PENDING, "pending-clear")
    result = dict(record["outcome"])
    result["pending"] = False
    return result


def _tool(  # noqa: PLR0913 - fixed child limits and inherited fd
    argv: list[str],
    budget: Any,
    *,
    seconds: float = 2.0,
    maximum: int = 16384,
    body: bytes | None = None,
    pass_fds: tuple[int, ...] = (),
    truncate: bool = False,
) -> bytes:
    deadline = time.monotonic() + budget.remaining(seconds)
    process = subprocess.Popen(  # noqa: S603 - fixed caller executable, no shell
        argv,
        stdin=subprocess.PIPE if body is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=ENV,
        cwd="/",
        pass_fds=pass_fds,
    )
    try:
        stream = process.stdout
        if stream is None:
            message = "fixed child output unavailable"
            raise ValueError(message)
        if body is not None:
            if process.stdin is None:
                message = "fixed child input unavailable"
                raise ValueError(message)
            process.stdin.write(body)
            process.stdin.close()
        data = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(stream, selectors.EVENT_READ)
            while True:
                remaining = min(budget.remaining(seconds), deadline - time.monotonic())
                if remaining <= 0 or not selector.select(remaining):
                    msg = "fixed host child deadline"
                    raise TimeoutError(msg)
                part = os.read(stream.fileno(), min(4096, maximum + 1 - len(data)))
                if not part:
                    break
                data.extend(part)
                budget.consume(size=len(part))
                if len(data) > maximum:
                    if truncate:
                        return bytes(data[:maximum])
                    _need(False)  # noqa: FBT003 - explicit protected refusal
        _need(process.wait(timeout=max(0.001, deadline - time.monotonic())) == 0)
        return bytes(data)
    finally:
        if process.poll() is None:
            with suppress(PermissionError):
                process.kill()
        process.wait()
        if process.stdout is not None:
            process.stdout.close()


def validate_schedule(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:
    request = _request(policy, body, "validate")
    _authority(policy, snapshot, "schedule")
    try:
        output = _tool(
            [
                "/usr/bin/systemd-analyze",
                "calendar",
                "--iterations=1",
                "--",
                request["on_calendar"],
            ],
            snapshot.budget,
        ).decode("utf-8")
        lines = {
            k.strip(): v.strip()
            for line in output.splitlines()
            if (parts := line.partition(":"))[1]
            for k, v in [(parts[0], parts[2])]
        }
        normalized = lines.get("Normalized form")
        _need(_text(normalized, 4096))
        delay = None
        if request["randomized_delay_sec"] is not None:
            output = _tool(
                ["/usr/bin/systemd-analyze", "timespan", "--", request["randomized_delay_sec"]],
                snapshot.budget,
            ).decode("utf-8")
            delay = next(
                (
                    line.partition(":")[2].strip()
                    for line in output.splitlines()
                    if line.strip().startswith("Human:")
                ),
                None,
            )
            _need(_text(delay, 256))
        next_elapse = lines.get("Next elapse")
        _need(next_elapse is None or _text(next_elapse, 512))
    except (ValueError, UnicodeError):
        msg = "invalid-request"
        raise policy.InspectionError(msg) from None
    return {
        "schema_version": 1,
        "archive_id": snapshot.archive_id,
        **request,
        "normalized_on_calendar": normalized,
        "normalized_randomized_delay_sec": delay,
        "next_elapse": next_elapse,
    }


def _manager(action: str, snapshot: Any) -> None:
    _need(action in {"daemon-reload", "restart", "stop", "start"})
    argv = ["/usr/bin/systemctl", "--system", action]
    if action != "daemon-reload":
        argv.append("hfcache-sync.timer")
    checkpoint("manager:" + action + ":before_send")
    _tool(argv, snapshot.budget)
    checkpoint("manager:" + action + ":after_ack")


def change_schedule(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:  # noqa: PLR0915 - one visible fixed transaction
    request = _request(policy, body, "schedule", effect=True)
    files = _Files(policy, snapshot)
    desired = request["request"]
    with files.locked():
        if os.path.lexists(ROOT / request["operation_id"]) or os.path.lexists(PENDING):
            if (
                os.path.lexists(ROOT / request["operation_id"])
                or (_pending(files) or {}).get("operation_id") == request["operation_id"]
            ):
                return _observe(files, request, "schedule")
            _need(False)  # noqa: FBT003 - explicit protected refusal
        authority = _authority(policy, snapshot)
        policy.require_host_actions(snapshot)
        original = snapshot._inspection.schedule()
        timer = policy._show("hfcache-sync.timer", snapshot.budget)
        _need(timer["ActiveState"] in {"active", "inactive"})
        active = timer["ActiveState"] == "active"
        if (
            original["revision"] != desired["expected_revision"]
            or not authority["permissions"]["schedule"]
        ):
            refused = _outcome(snapshot, request, "schedule")
            refused.update(
                state="unchanged",
                pending=False,
                action=desired["action"],
                expected_revision=desired["expected_revision"],
                stored_revision=original["revision"],
                file_state="unchanged",
                manager_state="not_sent",
                timer_was_active=active,
                timer_is_active=active,
            )
            record = _begin(files, request, "schedule", refused)
            return _finish(files, record, state="unchanged")
        default, managed = snapshot._inspection.schedule_files
        candidate = managed
        if desired["action"] == "replace":
            validate_schedule(
                policy, snapshot, {k: desired[k] for k in ("on_calendar", "randomized_delay_sec")}
            )
            candidate = (
                "[Timer]\nOnCalendar=\nOnCalendar="
                + desired["on_calendar"]
                + "\n"
                + (
                    "RandomizedDelaySec=" + desired["randomized_delay_sec"] + "\n"
                    if desired["randomized_delay_sec"] is not None
                    else ""
                )
            ).encode()
        if desired["action"] == "reset":
            candidate = None
        revision = snapshot._inspection.revision(
            b"host-schedule-v1", default, b"0" if candidate is None else b"1", candidate or b""
        )
        outcome = _outcome(snapshot, request, "schedule")
        outcome.update(
            state="prepared",
            pending=True,
            action=desired["action"],
            expected_revision=original["revision"],
            stored_revision=original["revision"],
            file_state="unchanged",
            manager_state="not_sent",
            timer_was_active=active,
            timer_is_active=active,
        )
        predecessor = (
            files.read(SCHEDULE, mode=0o644, kind=SCHEDULE_TYPE, gid=OWNER_GID)[1]
            if managed is not None
            else None
        )
        policy.revalidate(snapshot)
        record = _begin(files, request, "schedule", outcome, predecessor)
        _authority(policy, snapshot, "schedule")
        outcome.update(
            state="effect_unconfirmed",
            stored_revision=revision,
            file_state="unknown" if desired["action"] in {"replace", "reset"} else "unchanged",
        )
        files.save(record)
        if desired["action"] in {"replace", "reset"}:
            directory = BACKUPS / request["operation_id"]
            files.directory(directory, create=True)
            staged = None
            if candidate is not None:
                files.write(
                    directory / "staged.conf",
                    candidate,
                    mode=0o644,
                    gid=OWNER_GID,
                    kind=SCHEDULE_TYPE,
                    label="staged",
                )
                data, staged = files.read(
                    directory / "staged.conf", mode=0o644, kind=SCHEDULE_TYPE, gid=OWNER_GID
                )
                _need(data == candidate)
            if predecessor is not None:
                actual = files.read(SCHEDULE, mode=0o644, kind=SCHEDULE_TYPE, gid=OWNER_GID)[1]
                _need(actual == predecessor)
                files.rename(SCHEDULE, directory / "predecessor.conf", flags=1, label="predecessor")
                _retained(
                    files.read(
                        directory / "predecessor.conf",
                        mode=0o644,
                        kind=SCHEDULE_TYPE,
                        gid=OWNER_GID,
                    )[1],
                    predecessor,
                )
            else:
                _need(not os.path.lexists(SCHEDULE))
            if candidate is not None:
                files.rename(directory / "staged.conf", SCHEDULE, flags=1, label="installed")
                _need(staged is not None)
                _retained(
                    files.read(SCHEDULE, mode=0o644, kind=SCHEDULE_TYPE, gid=OWNER_GID)[1],
                    cast("dict[str, Any]", staged),
                )
            outcome["file_state"] = (
                "installed"
                if candidate is not None
                else ("removed" if predecessor else "unchanged")
            )
            files.save(record)
            outcome["manager_state"] = "unknown"
            files.save(record)
            _manager("daemon-reload", snapshot)
            outcome["manager_state"] = "reload_acknowledged"
            files.save(record)
            if active:
                _manager("restart", snapshot)
                outcome["manager_state"] = "timer_acknowledged"
        else:
            outcome["manager_state"] = "unknown"
            files.save(record)
            _manager("stop" if desired["action"] == "pause" else "start", snapshot)
            outcome["manager_state"] = "timer_acknowledged"
        final = policy._show("hfcache-sync.timer", snapshot.budget)
        outcome["timer_is_active"] = final["ActiveState"] == "active"
        policy.confirm_schedule(
            snapshot, candidate, action=desired["action"], timer_was_active=active
        )
        return _finish(files, record)


JOURNAL_EVENTS = frozenset(
    (
        "run.started",
        "preflight.failed",
        "repository.resolved",
        "repository.queued",
        "repository.skipped",
        "download.started",
        "download.completed",
        "hash.started",
        "hash.completed",
        "verification.completed",
        "dependency.undeclared",
        "publication.completed",
        "retention.pruned",
        "retention.deferred",
        "quarantine.cleaned",
        "repository.failed",
        "run.completed",
        "mcp.diagnostic",
        "catalog.capture_incomplete",
    )
)


def _boot() -> str:
    raw = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    _need(str(uuid.UUID(raw)) == raw)
    return raw


def _manager_observer(snapshot: Any) -> dict[str, str]:
    names = {
        "Id",
        "LoadState",
        "ActiveState",
        "SubState",
        "MainPID",
        "InvocationID",
        "FragmentPath",
        "DropInPaths",
        "User",
        "Group",
        "Type",
        "SELinuxContext",
    }
    output = _tool(
        [
            "/usr/bin/systemctl",
            "--system",
            "show",
            "hfcache-sync.service",
            "--no-pager",
            "--property=" + ",".join(sorted(names)),
        ],
        snapshot.budget,
    )
    fields = {}
    for line in output.decode().splitlines():
        key, sep, value = line.partition("=")
        _need(sep and key not in fields)
        fields[key] = value
    dropins = {""}
    if SYNC_OBSERVER_BINDING in snapshot.deployment["bindings"]:
        dropins.add(SYNC_OBSERVER_DROP_IN)
    _need(
        set(fields) == names
        and fields["Id"] == "hfcache-sync.service"
        and fields["LoadState"] == "loaded"
    )
    _need(
        fields["FragmentPath"]
        in {
            "/etc/systemd/system/hfcache-sync.service",
            str(snapshot.selected_release / "packaging/systemd/hfcache-sync.service"),
        }
        and fields["DropInPaths"] in dropins
    )
    _need(fields["Type"] == "oneshot" and fields["User"] == fields["Group"] == "hfcache")
    _need(fields["MainPID"].isascii() and fields["MainPID"].isdecimal())
    return fields


def _proc_start(pid: int) -> int:
    path = Path("/proc") / str(pid) / "stat"
    raw = path.read_bytes()
    _need(len(raw) <= MAX_PROC_BYTES)
    return int(raw.rpartition(b") ")[2].split()[19])


def _live(descriptor: int) -> bool:
    poll = select.poll()
    poll.register(descriptor, select.POLLIN)
    return not poll.poll(0)


def _child(
    policy: Any, snapshot: Any, expected: dict[str, Any], descriptor: int, *, send: bool
) -> None:
    body = {
        "schema_version": 1,
        "expected": expected,
        "uid": snapshot.api_principal[0],
        "gid": snapshot.api_principal[1],
        "pidfd": descriptor,
        "selected_release": str(snapshot.selected_release),
        "signal": send,
        "deadline_ns": snapshot.budget.deadline_ns,
        "expected_context": policy.observer_process_context(expected["main_pid"], snapshot.budget),
    }
    _need(not send or body["expected_context"] == SYNC_OBSERVER_CONTEXT)
    raw = _encoded(body)
    _need(len(raw) <= MAX_CHILD_REPLY)
    output = _tool(
        [str(HELPER), "--observer-stop-child"],
        snapshot.budget,
        seconds=15.0,
        maximum=4096,
        body=raw,
        pass_fds=(descriptor,),
    )
    result = policy._json(output)
    _need(result == {"schema_version": 1, "expected": expected, "signalled": send})


def _capture_observer(policy: Any, snapshot: Any) -> tuple[dict[str, Any] | None, int | None]:
    fields = _manager_observer(snapshot)
    pid = int(fields["MainPID"])
    if fields["ActiveState"] in {"inactive", "failed"} and pid == 0:
        return None, None
    _need(
        (fields["ActiveState"], fields["SubState"])
        in {("activating", "start"), ("active", "running")}
        and pid > 1
        and HEX32.fullmatch(fields["InvocationID"])
    )
    start = _proc_start(pid)
    context = policy.observer_process_context(pid, snapshot.budget)
    descriptor = os.pidfd_open(pid, 0)
    try:
        expected = {
            "boot_id": _boot(),
            "invocation_id": fields["InvocationID"],
            "main_pid": pid,
            "start_ticks": start,
        }
        _need(_live(descriptor) and _proc_start(pid) == start)
        _child(policy, snapshot, expected, descriptor, send=False)
        _need(
            _manager_observer(snapshot) == fields
            and _live(descriptor)
            and _proc_start(pid) == start
            and policy.observer_process_context(pid, snapshot.budget) == context
        )
        return expected, descriptor  # noqa: TRY300 - transfer descriptor ownership
    except BaseException:
        os.close(descriptor)
        raise


def read_sync_observer(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:
    _invalid(policy, type(body) is dict and not body)
    status = _authority(policy, snapshot)
    result = {
        "schema_version": 1,
        "archive_id": snapshot.archive_id,
        "profile": snapshot.profile,
        "host_binding": status["binding"],
        "permissions": {k: status["permissions"][k] for k in ("schedule", "observer")},
        "permission_reasons": {
            k: status["permission_reasons"][k] for k in ("schedule", "observer")
        },
        "state": "unavailable",
        "reason": "profile-unproved",
        "unit": "hfcache-sync.service",
        "expected": None,
    }
    if snapshot.profile != "native":
        return result
    expected, descriptor = _capture_observer(policy, snapshot)
    if descriptor is not None:
        os.close(descriptor)
    return dict(
        result, state="observed" if expected else "inactive", reason=None, expected=expected
    )


def stop_sync_observer(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:
    request = _request(policy, body, "observer", effect=True)
    files = _Files(policy, snapshot)
    with files.locked():
        if os.path.lexists(ROOT / request["operation_id"]) or os.path.lexists(PENDING):
            if (
                os.path.lexists(ROOT / request["operation_id"])
                or (_pending(files) or {}).get("operation_id") == request["operation_id"]
            ):
                return _observe(files, request, "observer")
            _need(False)  # noqa: FBT003 - explicit protected refusal
        authority = _authority(policy, snapshot)
        policy.require_host_actions(snapshot)
        if not authority["permissions"]["observer"]:
            refused = _outcome(snapshot, request, "observer")
            refused.update(
                state="unchanged",
                pending=False,
                expected=request["request"]["expected"],
                stop_state="not_sent",
            )
            record = _begin(files, request, "observer", refused)
            return _finish(files, record, state="unchanged")
        expected, descriptor = _capture_observer(policy, snapshot)
        try:
            if expected != request["request"]["expected"] or descriptor is None:
                refused = _outcome(snapshot, request, "observer")
                refused.update(
                    state="unchanged",
                    pending=False,
                    expected=request["request"]["expected"],
                    stop_state="not_sent",
                )
                record = _begin(files, request, "observer", refused)
                return _finish(files, record, state="unchanged")
            if expected is None or descriptor is None:
                message = "original observer proof unavailable"
                raise ValueError(message)
            outcome = _outcome(snapshot, request, "observer")
            outcome.update(state="prepared", pending=True, expected=expected, stop_state="not_sent")
            record = _begin(files, request, "observer", outcome)
            _authority(policy, snapshot, "observer")
            current = _manager_observer(snapshot)
            _need(
                int(current["MainPID"]) == expected["main_pid"]
                and current["InvocationID"] == expected["invocation_id"]
                and _boot() == expected["boot_id"]
                and _proc_start(expected["main_pid"]) == expected["start_ticks"]
                and _live(descriptor)
            )
            outcome.update(state="effect_unconfirmed", stop_state="unknown")
            files.save(record)
            checkpoint("observer:before_signal")
            _child(policy, snapshot, expected, descriptor, send=True)
            checkpoint("observer:after_signal")
            outcome["stop_state"] = "acknowledged"
            files.save(record)
            poll = select.poll()
            poll.register(descriptor, select.POLLIN)
            if not poll.poll(max(1, int(snapshot.budget.remaining() * 1000))):
                return dict(outcome, pending=True)
            outcome["stop_state"] = "exit_confirmed"
            policy.confirm_schedule(
                snapshot, snapshot._inspection.schedule_files[1], action="observer"
            )
            return _finish(files, record)
        finally:
            if descriptor is not None:
                os.close(descriptor)


def observer_signal_child(  # noqa: PLR0915 - keep permanent privilege-drop proof visibly ordered
    policy: Any,
    *,
    host_labels: Any = None,
    bootstrap_work: dict[str, int] | None = None,
    bootstrap_hashes: dict[str, str] | None = None,
    started_at: float | None = None,
) -> dict[str, Any]:
    _need(os.getuid() == os.geteuid() == 0 and os.getgid() == os.getegid() == 0)
    raw = sys.stdin.buffer.read(16385)
    _need(0 < len(raw) <= MAX_DOCUMENT)
    body = policy._json(raw)
    _need(
        set(body)
        == {
            "schema_version",
            "expected",
            "uid",
            "gid",
            "pidfd",
            "selected_release",
            "signal",
            "deadline_ns",
            "expected_context",
        }
        and type(body["schema_version"]) is int
        and body["schema_version"] == 1
        and type(body["signal"]) is bool
    )
    expected = _expected(policy, body["expected"])
    _need(_text(body["expected_context"], 4096))
    _need(
        type(body["deadline_ns"]) is int
        and time.monotonic_ns() < body["deadline_ns"] <= time.monotonic_ns() + 15_000_000_000
    )
    deadline = body["deadline_ns"]
    if started_at is not None:
        deadline = min(deadline, int((started_at + 15.0) * 1_000_000_000))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, (deadline - time.monotonic_ns()) / 1e9))
    budget = policy.InspectionBudget(deadline_ns=deadline)
    if bootstrap_work is not None:
        budget.consume(files=bootstrap_work["files"], size=bootstrap_work["bytes"] + len(raw))
    snapshot = policy.inspect_authority(budget=budget, host_labels=host_labels)
    roles = {
        "host_protocol": "helper_protocol_module",
        "host_policy": "helper_policy_module",
        "host_peer": "helper_peer_module",
        "host_configuration": "helper_configuration_module",
        "host_actions": "helper_actions_module",
        "host_selinux": "helper_selinux_module",
        "helper_daemon": "helper_daemon",
    }
    _need(bootstrap_hashes is not None and set(bootstrap_hashes) == set(roles))
    bootstrap_hashes = cast("dict[str, str]", bootstrap_hashes)
    _need(
        all(
            bootstrap_hashes[name] == snapshot.deployment["bindings"][role]
            for name, role in roles.items()
        )
    )
    if body["signal"]:
        _authority(policy, snapshot, "observer")
        _need(body["expected_context"] == SYNC_OBSERVER_CONTEXT)
    _need(
        snapshot.profile == "native"
        and str(snapshot.selected_release) == body["selected_release"]
        and tuple(snapshot.api_principal) == (body["uid"], body["gid"])
    )
    uid, gid = body["uid"], body["gid"]
    _need(type(uid) is int and type(gid) is int and uid > 0 and gid > 0)
    account = pwd.getpwnam("hfcache")
    _need((account.pw_uid, account.pw_gid) == (uid, gid))
    descriptor = body["pidfd"]
    _need(type(descriptor) is int and descriptor >= MIN_PIDFD)
    for path in Path("/proc/self/fd").iterdir():
        opened = int(path.name)
        try:
            os.fstat(opened)
        except OSError:
            continue  # The transient proc-directory descriptor has already closed.
        _need(opened in {0, 1, 2, descriptor})
    _need(Path(f"/proc/self/fd/{descriptor}").readlink() == Path("anon_inode:[pidfd]"))
    fdinfo = Path(f"/proc/self/fdinfo/{descriptor}").read_text()
    _need(
        len(fdinfo) <= MAX_PROC_BYTES
        and f"Pid:\t{expected['main_pid']}\n" in fdinfo
        and _live(descriptor)
    )
    _need(
        _boot() == expected["boot_id"]
        and _proc_start(expected["main_pid"]) == expected["start_ticks"]
        and policy.observer_process_context(expected["main_pid"], budget)
        == body["expected_context"]
    )
    executable, _ = policy.fixed_interpreter(
        snapshot._inspection.capture,
        snapshot.selected_release,
        snapshot._inspection.authority_read(snapshot.selected_release / ".python-version")
        .decode()
        .strip(),
    )
    os.setgroups([])
    os.setresgid(gid, gid, gid)
    os.setresuid(uid, uid, uid)
    _need(
        os.getresuid() == (uid, uid, uid)
        and os.getresgid() == (gid, gid, gid)
        and os.getgroups() == []
    )
    self_status = Path("/proc/self/status").read_text()
    _need(
        all(
            re.search(r"^" + name + r":\s+0+$", self_status, re.M)
            for name in ("CapEff", "CapPrm", "CapAmb", "CapInh")
        )
    )
    proc = Path("/proc") / str(expected["main_pid"])
    _need(policy.observer_process_context(expected["main_pid"], budget) == body["expected_context"])
    status = (proc / "status").read_text()
    _need(len(status) <= MAX_PROC_STATUS)
    for name, value in (("Uid", uid), ("Gid", gid)):
        row = re.search(
            r"^" + name + r":\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)$", status, re.M
        )
        _need(row and all(int(v) == value for v in row.groups()))
    command = (proc / "cmdline").read_bytes()
    _need(len(command) <= MAX_PROC_BYTES and command.endswith(b"\0"))
    argv = [v.decode("ascii") for v in command[:-1].split(b"\0")]
    _need(
        argv[0]
        in {
            str(snapshot.selected_release / ".venv/bin/python"),
            "/opt/hfcache/current/.venv/bin/python",
        }
        and argv[1:]
        == [
            "-m",
            "hfcache.scheduled_client",
            "--client-config",
            "/etc/hfcache/scheduled-client.toml",
            "--state-directory",
            "/var/lib/hfcache/scheduled/sync",
            "sync",
        ]
    )
    _need(
        (proc / "exe").readlink() == executable
        and (proc / "cgroup").read_text().strip() == "0::/system.slice/hfcache-sync.service"
    )
    _need(
        _proc_start(expected["main_pid"]) == expected["start_ticks"]
        and _live(descriptor)
        and policy.observer_process_context(expected["main_pid"], budget)
        == body["expected_context"]
    )
    if body["signal"]:
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    return {"schema_version": 1, "expected": expected, "signalled": body["signal"]}


def _cursor(snapshot: Any, source: str, raw_cursor: str) -> str:
    value = {
        "schema_version": 1,
        "source": source,
        "boot_id": _boot(),
        "archive_id": snapshot.archive_id,
        "deployment_sha256": snapshot.deployment_sha256,
        "expires": int(time.time()) + 300,
        "cursor": raw_cursor,
    }
    result = (
        base64.urlsafe_b64encode(
            _encoded(
                {
                    "record": value,
                    "authentication": _seal(
                        snapshot._inspection.key, value, b"host-journal-cursor-v1"
                    ),
                }
            )
        )
        .rstrip(b"=")
        .decode()
    )
    _need(len(result) <= MAX_CURSOR_CHARS)
    return result


def _decode_cursor(policy: Any, snapshot: Any, source: str, cursor: str) -> tuple[str | None, bool]:
    try:
        _need(
            type(cursor) is str
            and 1 <= len(cursor) <= MAX_CURSOR_CHARS
            and re.fullmatch(r"[A-Za-z0-9_-]+", cursor)
        )
        value = policy._json(
            base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
        )
        _need(set(value) == {"record", "authentication"})
        record = value["record"]
        _need(
            type(record) is dict
            and set(record)
            == {
                "schema_version",
                "source",
                "boot_id",
                "archive_id",
                "deployment_sha256",
                "expires",
                "cursor",
            }
        )
        _need(
            type(value["authentication"]) is str
            and hmac.compare_digest(
                value["authentication"],
                _seal(snapshot._inspection.key, record, b"host-journal-cursor-v1"),
            )
        )
        _need(
            record["schema_version"] == 1
            and type(record["schema_version"]) is int
            and record["source"] == source
            and record["archive_id"] == snapshot.archive_id
            and record["deployment_sha256"] == snapshot.deployment_sha256
            and type(record["expires"]) is int
            and _text(record["cursor"], 1024)
        )
        if record["boot_id"] != _boot() or record["expires"] < time.time():
            return None, True
        return record["cursor"], False
    except (ValueError, KeyError, TypeError, UnicodeError):
        msg = "invalid-request"
        raise policy.InspectionError(msg) from None


def read_journal(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:  # noqa: PLR0912, PLR0915 - one bounded stream/cursor pass
    body = cast("dict[str, Any]", body)
    _invalid(
        policy,
        type(body) is dict
        and set(body) == {"source", "cursor", "limit"}
        and body["source"] in SOURCES
        and type(body["limit"]) is int
        and 1 <= body["limit"] <= MAX_JOURNAL_ENTRIES
        and (body["cursor"] is None or _text(body["cursor"], 2048)),
    )
    _authority(policy, snapshot)
    if not JOURNAL_CAPACITY.acquire(blocking=False):
        msg = "busy"
        raise policy.InspectionError(msg)
    try:
        raw_cursor = None
        gap = False
        if body["cursor"] is not None:
            raw_cursor, gap = _decode_cursor(policy, snapshot, body["source"], body["cursor"])
        argv = [
            "/usr/bin/journalctl",
            "--system",
            "--no-pager",
            "--output=json",
            "--reverse",
            "--boot=" + _boot().replace("-", ""),
            "--unit=" + SOURCES[body["source"]],
            "--lines=" + str(body["limit"] + 1),
        ]
        if raw_cursor is not None:
            argv.append("--cursor=" + raw_cursor)
        try:
            raw = _tool(argv, snapshot.budget, seconds=4.0, maximum=256 * 1024, truncate=True)
        except ValueError:
            if raw_cursor is None:
                raise
            return {
                "schema_version": 1,
                "archive_id": snapshot.archive_id,
                "source": body["source"],
                "entries": [],
                "next_cursor": None,
                "gap": True,
                "truncated": False,
            }
        entries = []
        last = None
        truncated = len(raw) == 256 * 1024
        total = 0
        rows = raw.splitlines()
        for index, line in enumerate(rows):
            if len(entries) == body["limit"]:
                truncated = True
                break
            if len(line) > MAX_PROC_BYTES:
                truncated = True
                continue
            try:
                record = policy._json(line)
            except (ValueError, UnicodeError):
                truncated = True
                continue
            cursor = record.get("__CURSOR")
            _need(_text(cursor, 1024))
            if index == 0 and raw_cursor is not None:
                if cursor == raw_cursor:
                    continue
                gap = True
            last = cursor
            message = record.get("MESSAGE")
            if type(message) is not str:
                truncated = True
                continue
            match = re.match(
                r"^event=([a-z][a-z0-9_.-]{0,63}) "
                r"level=(debug|info|warning|error|critical) run_id=([0-9a-f]{32})(?: |$)",
                message,
            )
            if match is None or match[1] not in JOURNAL_EVENTS:
                truncated = True
                continue
            projected = f"event={match[1]} level={match[2]} run_id={match[3]}"
            at = None
            stamp = record.get("__REALTIME_TIMESTAMP")
            if (
                type(stamp) is str
                and stamp.isascii()
                and stamp.isdecimal()
                and len(stamp) <= MAX_TIMESTAMP_CHARS
            ):
                try:
                    at = (
                        datetime.fromtimestamp(int(stamp) / 1e6, UTC)
                        .isoformat(timespec="microseconds")
                        .replace("+00:00", "Z")
                    )
                except (ValueError, OverflowError, OSError):
                    truncated = True
            if len(entries) == body["limit"] or total + len(projected.encode()) > MAX_JOURNAL_TEXT:
                truncated = True
                break
            total += len(projected.encode())
            entries.append({"at": at, "message": projected})
        policy.revalidate(snapshot)
        return {
            "schema_version": 1,
            "archive_id": snapshot.archive_id,
            "source": body["source"],
            "entries": entries,
            "next_cursor": _cursor(snapshot, body["source"], last)
            if last is not None and len(rows) >= body["limit"]
            else None,
            "gap": gap,
            "truncated": truncated,
        }
    finally:
        JOURNAL_CAPACITY.release()
