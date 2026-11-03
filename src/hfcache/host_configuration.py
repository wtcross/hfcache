"""Decision154: fixed configuration effects and authenticated observe-only outcomes.

Loaded as an indexed standard-library bootstrap, never through the application
package. The daemon supplies its already authenticated policy module/snapshot.
"""

from __future__ import annotations

import ctypes
import fcntl
import hashlib
import hmac
import json
import os
import re
import stat
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

CONFIGURATION = Path("/etc/hfcache/config.toml")
CANDIDATE = Path("/etc/hfcache/.candidate.toml")
BACKUP = Path("/etc/hfcache/config.toml.bak")
LOCK = Path("/etc/hfcache/.configuration.lock")
PENDING = Path("/etc/hfcache/.configuration.pending")
APPLICATIONS = Path("/etc/hfcache/.configuration-applications")
OWNER = 0
OWNER_GID = 0
MAX_RECORDS = 64
MAX_PRIVATE_BYTES = 16 * 1024 * 1024
MAX_DOCUMENT = 1024 * 1024
MAX_STATE = 128 * 1024
MAX_SELECTORS = 256
MAX_SELECTOR_BYTES = 202
KEY_BYTES = 32
SELINUX_FIELDS = 4
PRIVATE_MODE = 0o700
GUARD_MODE = 0o600
_INVALID = "invalid-request"
_CONFLICT = "config-conflict"
_DENIED = "operation-denied"
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
APPLICATION_TYPE = "hfcache_host_helper_application_conf_t"
STATE_TYPE = "hfcache_host_helper_application_state_t"
GUARD_TYPE = "hfcache_host_helper_configuration_guard_t"
DIRECTORY_TYPE = "hfcache_host_helper_configuration_dir_t"
PHASES = ("intent", "staged", "backup_ready", "install_intent", "installed", "confirmed")
MATERIAL = {"base.toml", "candidate.toml", "predecessor.toml", "previous-backup.toml"}
IDENTITY = (
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
FIELDS = {
    "schema_version",
    "operation_id",
    "request_digest",
    "archive_id",
    "target",
    "deployment_sha256",
    "policy_sha256",
    "base_revision",
    "candidate_revision",
    "config_fingerprint",
    "preview_operation_id",
    "required_selectors",
    "phase",
    "base",
    "candidate",
    "stage",
    "backup",
    "predecessor",
    "previous_backup",
}


def checkpoint(_name: str) -> None:
    """Fault-injection boundary; production has no callback or recovery action."""


def _need(condition: object) -> None:
    if not condition:
        message = "protected configuration application refused"
        raise ValueError(message)


def _encoded(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def _identity(info: os.stat_result) -> list[int]:
    return [getattr(info, name) for name in IDENTITY]


def _context(path: Path | int) -> str:
    return os.getxattr(path, "security.selinux").rstrip(b"\0").decode("ascii")


def _type(context: str, expected: str) -> None:
    fields = context.split(":")
    _need(len(fields) == SELINUX_FIELDS and fields[1:] == ["object_r", expected, "s0"])
    _need(re.fullmatch(r"[A-Za-z0-9_]+", fields[0]) is not None)


def _seal(key: bytes, value: object, domain: bytes) -> str:
    digest = hmac.new(key, digestmod=hashlib.sha256)
    for part in (domain, _encoded(value)):
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


def configuration_fingerprint(document: dict[str, Any]) -> str:
    """Mirror ApplicationConfig.fingerprint, including order and materialized defaults."""
    payload = {
        name: document[name]
        for name in ("schema_version", "storage", "sync", "verification", "repair")
    }
    payload["hub"] = {
        name: document["hub"][name] for name in ("endpoint", "expected_account", "token_mode")
    }
    payload["repositories"] = [
        {name: row[name] for name in ("declared_dependencies", "enabled", "id", "revision", "type")}
        for row in document["repositories"]
    ]
    return hashlib.sha256(_encoded(payload)).hexdigest()


def _request(policy: Any, body: object, *, effect: bool) -> dict[str, Any]:  # noqa: ANN401 - captured bootstrap module
    fields = {"operation_id", "request_digest"}
    if effect:
        fields |= {
            "managed",
            "candidate_revision",
            "config_fingerprint",
            "preview_operation_id",
            "required_selectors",
        }
    if type(body) is not dict or set(body) != fields:
        raise policy.InspectionError(_INVALID)
    valid = type(body["operation_id"]) is str and HEX32.fullmatch(body["operation_id"])
    valid = (
        valid and type(body["request_digest"]) is str and HEX64.fullmatch(body["request_digest"])
    )
    if effect:
        valid = valid and all(
            type(body[name]) is str and HEX64.fullmatch(body[name])
            for name in ("candidate_revision", "config_fingerprint")
        )
        valid = (
            valid
            and type(body["preview_operation_id"]) is str
            and HEX32.fullmatch(body["preview_operation_id"])
        )
        selectors = body["required_selectors"]
        valid = valid and type(selectors) is list and len(selectors) <= MAX_SELECTORS
        valid = valid and all(
            type(item) is str and len(item) <= MAX_SELECTOR_BYTES for item in selectors
        )
        valid = valid and len(set(selectors)) == len(selectors)
    if not valid:
        raise policy.InspectionError(_INVALID)
    return body


class _Store:
    def __init__(self, policy: Any, snapshot: Any) -> None:  # noqa: ANN401 - captured bootstrap objects
        self.policy, self.snapshot = policy, snapshot
        self.key = snapshot._inspection.key  # noqa: SLF001 - supplied protected capture
        _need(type(self.key) is bytes and len(self.key) == KEY_BYTES)
        self.gid = snapshot.api_principal[1]
        self.budget = snapshot.budget
        self.parents: dict[Path, tuple[int, ...]] = {}
        self.published: dict[Path, bytes] = {}
        parent = self.parent(CONFIGURATION)
        try:
            _type(_context(parent), DIRECTORY_TYPE)
        finally:
            os.close(parent)

    def parent(self, path: Path) -> int:
        self.snapshot._inspection.capture.local(path)  # noqa: SLF001 - same captured local-filesystem proof
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

    def directory(self, path: Path, *, create: bool = False) -> None:
        parent = self.parent(path)
        try:
            if create:
                os.mkdir(path.name, 0o700, dir_fd=parent)
                os.fsync(parent)
            descriptor = os.open(
                path.name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent,
            )
            try:
                info = os.fstat(descriptor)
                _need(info.st_uid == OWNER and stat.S_IMODE(info.st_mode) == PRIVATE_MODE)
                _type(_context(descriptor), STATE_TYPE)
                configuration_parent = self.parent(CONFIGURATION)
                try:
                    _need(info.st_dev == os.fstat(configuration_parent).st_dev)
                finally:
                    os.close(configuration_parent)
                _need(
                    (info.st_dev, info.st_ino)
                    == (
                        os.stat(path.name, dir_fd=parent, follow_symlinks=False).st_dev,
                        os.stat(path.name, dir_fd=parent, follow_symlinks=False).st_ino,
                    )
                )
            finally:
                os.close(descriptor)
        finally:
            os.close(parent)

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

    def write(self, path: Path, body: bytes, *, mode: int, gid: int, kind: str, label: str) -> None:  # noqa: PLR0913 - explicit fixed file metadata
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

    def state(self, path: Path, value: dict[str, Any]) -> None:
        payload = {
            "record": value,
            "authentication": _seal(self.key, value, b"host-config-outcome-v1"),
        }
        body = _encoded(payload)
        _need(len(body) <= MAX_STATE)
        destination = path / "outcome.json"
        if path in self.published:
            prior, _ = self.read(
                destination, mode=0o600, kind=STATE_TYPE, maximum=MAX_STATE, gid=OWNER_GID
            )
            _need(prior == self.published[path])
        else:
            _need(not os.path.lexists(destination))
        temporary = path / ".outcome.tmp"
        self.write(
            temporary, body, mode=0o600, gid=OWNER_GID, kind=STATE_TYPE, label=value["phase"]
        )
        self.rename(temporary, destination, flags=0, label=value["phase"])
        self.published[path] = body

    def load(self, path: Path) -> dict[str, Any]:
        self.directory(path)
        body, _ = self.read(
            path / "outcome.json", mode=0o600, kind=STATE_TYPE, maximum=MAX_STATE, gid=OWNER_GID
        )
        envelope = self.policy._json(body)  # noqa: SLF001 - shared duplicate-key refusal
        _need(set(envelope) == {"record", "authentication"})
        value = envelope["record"]
        _need(type(value) is dict and set(value) == FIELDS)
        _need(
            type(envelope["authentication"]) is str
            and hmac.compare_digest(
                envelope["authentication"], _seal(self.key, value, b"host-config-outcome-v1")
            )
        )
        _need(
            type(value["schema_version"]) is int
            and value["schema_version"] == 1
            and value["operation_id"] == path.name
        )
        _need(value["phase"] in PHASES and value["target"] == str(CONFIGURATION))
        _need(str(uuid.UUID(value["archive_id"])) == value["archive_id"])
        _need(
            all(
                type(value[name]) is str and HEX64.fullmatch(value[name])
                for name in (
                    "request_digest",
                    "deployment_sha256",
                    "policy_sha256",
                    "base_revision",
                    "candidate_revision",
                    "config_fingerprint",
                )
            )
        )
        _need(
            type(value["preview_operation_id"]) is str
            and HEX32.fullmatch(value["preview_operation_id"])
        )
        names = set()
        with os.scandir(path) as children:
            for child in children:
                _need(len(names) < len(MATERIAL) + 1)
                _need(child.name in {"outcome.json", *MATERIAL})
                names.add(child.name)
        _need(
            names <= {"outcome.json", *MATERIAL}
            and {"outcome.json", "base.toml", "candidate.toml"} <= names
        )
        for name, key in (("base.toml", "base"), ("candidate.toml", "candidate")):
            _, actual = self.read(path / name, mode=0o600, kind=STATE_TYPE, gid=OWNER_GID)
            _need(actual == value[key])
        if "predecessor.toml" in names:
            _, actual = self.read(
                path / "predecessor.toml",
                mode=0o640,
                kind=APPLICATION_TYPE,
                gid=value["predecessor"]["identity"][4],
            )
            _need(_moved(actual, value["predecessor"]))
        if "previous-backup.toml" in names:
            _, actual = self.read(
                path / "previous-backup.toml",
                mode=0o640,
                kind=APPLICATION_TYPE,
                gid=value["previous_backup"]["identity"][4],
            )
            _need(_moved(actual, value["previous_backup"]))
        return value

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


def _moved(actual: object, expected: object) -> bool:
    if type(actual) is not dict or type(expected) is not dict:
        return False
    return (
        actual.get("context") == expected.get("context")
        and actual.get("sha256") == expected.get("sha256")
        and actual.get("identity", [])[:-1] == expected.get("identity", [])[:-1]
    )


def _projection(
    snapshot: Any,  # noqa: ANN401 - supplied protected capture
    body: dict[str, Any],
    value: dict[str, Any] | None,
    state: str,
    *,
    pending: bool,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "archive_id": value["archive_id"] if value else snapshot.archive_id,
        "operation_id": body["operation_id"],
        "request_digest": body["request_digest"],
        "base_revision": value["base_revision"] if value else None,
        "candidate_revision": value["candidate_revision"] if value else None,
        "config_fingerprint": value["config_fingerprint"] if value else None,
        "state": state,
        "pending": pending,
    }


def _pending_record(store: _Store) -> dict[str, Any]:
    """Authenticate the minimal first intent without adopting or repairing it."""
    raw, _ = store.read(PENDING, mode=0o600, kind=GUARD_TYPE, maximum=MAX_STATE, gid=OWNER_GID)
    envelope = store.policy._json(raw)  # noqa: SLF001 - shared duplicate-key refusal
    _need(set(envelope) == {"record", "authentication"})
    record = envelope["record"]
    _need(type(record) is dict and set(record) == {"operation_id", "request_digest"})
    _need(type(record["operation_id"]) is str and HEX32.fullmatch(record["operation_id"]))
    _need(type(record["request_digest"]) is str and HEX64.fullmatch(record["request_digest"]))
    _need(
        type(envelope["authentication"]) is str
        and hmac.compare_digest(
            envelope["authentication"], _seal(store.key, record, b"host-config-pending-v1")
        )
    )
    return record


def _observe(store: _Store, body: dict[str, Any]) -> dict[str, Any]:
    pending = os.path.lexists(PENDING)
    try:
        value = store.load(APPLICATIONS / body["operation_id"])
    except (OSError, ValueError, KeyError, TypeError):
        if pending:
            try:
                first_intent = _pending_record(store)
            except (OSError, ValueError, KeyError, TypeError):
                first_intent = None
            if (
                first_intent is not None
                and first_intent["operation_id"] == body["operation_id"]
                and not hmac.compare_digest(first_intent["request_digest"], body["request_digest"])
            ):
                raise store.policy.InspectionError(_CONFLICT) from None
        return _projection(store.snapshot, body, None, "unknown", pending=pending)
    if not hmac.compare_digest(value["request_digest"], body["request_digest"]):
        raise store.policy.InspectionError(_CONFLICT) from None
    if value["phase"] == "confirmed":
        return _projection(store.snapshot, body, value, "confirmed", pending=pending)
    state = "unknown"
    try:
        _, current = store.read(CONFIGURATION, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid)
        base_body, _ = store.read(
            APPLICATIONS / body["operation_id"] / "base.toml",
            mode=0o600,
            kind=STATE_TYPE,
            gid=OWNER_GID,
        )
        if current["sha256"] == hashlib.sha256(base_body).hexdigest() and _moved(
            current, value["predecessor"]
        ):
            state = "unchanged"
            if value["stage"] is not None:
                _, stage = store.read(CANDIDATE, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid)
                state = "staged" if _moved(stage, value["stage"]) else "conflict"
        elif value["stage"] is not None and _moved(current, value["stage"]):
            original = APPLICATIONS / body["operation_id"] / "predecessor.toml"
            if not os.path.lexists(original):
                original = CANDIDATE
            original_body, original_record = store.read(
                original, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid
            )
            _need(original_body == base_body and _moved(original_record, value["predecessor"]))
            _, backup = store.read(BACKUP, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid)
            _need(backup == value["backup"])
            state = "installed_unconfirmed"
        else:
            state = "conflict"
    except (OSError, ValueError, KeyError, TypeError):
        state = "unknown"
    return _projection(store.snapshot, body, value, state, pending=pending)


def read_configuration_outcome(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:  # noqa: ANN401 - isolated bootstrap objects
    """Authenticate history without creating a lock/file or completing an effect."""
    request = _request(policy, body, effect=False)
    store = _Store(policy, snapshot)
    try:
        with store.locked():
            return _observe(store, request)
    except policy.InspectionError as error:
        if error.reason == _CONFLICT:
            raise
        return _projection(snapshot, request, None, "unknown", pending=os.path.lexists(PENDING))
    except (OSError, ValueError):
        return _projection(snapshot, request, None, "unknown", pending=os.path.lexists(PENDING))


def _history(store: _Store) -> tuple[list[dict[str, Any]], int]:
    if not os.path.lexists(APPLICATIONS):
        return [], 0
    store.directory(APPLICATIONS)
    records, size = [], 0
    for path in APPLICATIONS.iterdir():
        _need(len(records) < MAX_RECORDS and HEX32.fullmatch(path.name))
        try:
            value = store.load(path)
        except (OSError, ValueError, KeyError, TypeError):
            message = "protected configuration application refused"
            raise ValueError(message) from None
        _need(value["phase"] == "confirmed")
        records.append(value)
        for child in path.iterdir():
            info = child.lstat()
            _need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
            size += info.st_size
            _need(size <= MAX_PRIVATE_BYTES)
    return records, size


def apply_configuration(policy: Any, snapshot: Any, body: object) -> dict[str, Any]:  # noqa: ANN401, PLR0915 - one visible fixed transaction
    """Install a new operation once; an existing ID is strictly observe-only."""
    request = _request(policy, body, effect=True)
    store = _Store(policy, snapshot)
    with store.locked():
        path = APPLICATIONS / request["operation_id"]
        if os.path.lexists(path):
            return _observe(store, request)
        if os.path.lexists(PENDING):
            try:
                first_intent = _pending_record(store)
            except (OSError, ValueError, KeyError, TypeError):
                message = "protected configuration application refused"
                raise ValueError(message) from None
            _need(first_intent["operation_id"] == request["operation_id"])
            if not hmac.compare_digest(first_intent["request_digest"], request["request_digest"]):
                raise policy.InspectionError(_CONFLICT)
            return _observe(store, request)
        _need(not os.path.lexists(CANDIDATE))
        history, used = _history(store)
        # Decision154: the original flock and mutation-boundary rechecks bracket
        # this pure reconstruction; do not nest the read-only opcode's checks.
        prepared = policy._prepare_configuration(snapshot, request["managed"])  # noqa: SLF001 - fixed protected sibling module
        _need(prepared["candidate_revision"] == request["candidate_revision"])
        _need(prepared["required_selectors"] == request["required_selectors"])
        permissions = snapshot.status()["permissions"]
        if not permissions["configuration"] or (
            prepared["required_selectors"] and not permissions["hub"]
        ):
            raise policy.InspectionError(_DENIED)
        candidate = prepared["candidate"].encode("utf-8")
        _need(
            configuration_fingerprint(policy.parse_configuration(candidate))
            == request["config_fingerprint"]
        )
        base, source = store.read(CONFIGURATION, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid)
        _need(base == snapshot._inspection.config_body)  # noqa: SLF001 - exact supplied capture
        previous = None
        if os.path.lexists(BACKUP):
            _, previous = store.read(BACKUP, mode=0o640, kind=APPLICATION_TYPE)
            _need(any(value["backup"] == previous for value in history))
        reserve = len(base) * 2 + len(candidate) + MAX_STATE * 2
        if previous is not None:
            reserve += previous["identity"][6]
        _need(len(history) < MAX_RECORDS and used + reserve <= MAX_PRIVATE_BYTES)
        policy.revalidate(snapshot)
        pending = {
            "operation_id": request["operation_id"],
            "request_digest": request["request_digest"],
        }
        pending = {
            "record": pending,
            "authentication": _seal(store.key, pending, b"host-config-pending-v1"),
        }
        # The shared legacy guard sees this first durable operation intent even
        # if a crash leaves no workspace or full outcome record (decision154).
        store.write(
            PENDING, _encoded(pending), mode=0o600, gid=OWNER_GID, kind=GUARD_TYPE, label="pending"
        )
        _, pending_record = store.read(
            PENDING, mode=0o600, kind=GUARD_TYPE, maximum=MAX_STATE, gid=OWNER_GID
        )
        if not os.path.lexists(APPLICATIONS):
            store.directory(APPLICATIONS, create=True)
        store.directory(path, create=True)
        store.write(
            path / "base.toml", base, mode=0o600, gid=OWNER_GID, kind=STATE_TYPE, label="base"
        )
        store.write(
            path / "candidate.toml",
            candidate,
            mode=0o600,
            gid=OWNER_GID,
            kind=STATE_TYPE,
            label="candidate-material",
        )
        _, base_record = store.read(path / "base.toml", mode=0o600, kind=STATE_TYPE, gid=OWNER_GID)
        _, candidate_record = store.read(
            path / "candidate.toml", mode=0o600, kind=STATE_TYPE, gid=OWNER_GID
        )
        value: dict[str, Any] = {
            "schema_version": 1,
            "operation_id": request["operation_id"],
            "request_digest": request["request_digest"],
            "archive_id": snapshot.archive_id,
            "target": str(CONFIGURATION),
            "deployment_sha256": snapshot.deployment_sha256,
            "policy_sha256": snapshot.policy_sha256,
            "base_revision": prepared["base_revision"],
            "candidate_revision": prepared["candidate_revision"],
            "config_fingerprint": request["config_fingerprint"],
            "preview_operation_id": request["preview_operation_id"],
            "required_selectors": prepared["required_selectors"],
            "phase": "intent",
            "base": base_record,
            "candidate": candidate_record,
            "stage": None,
            "backup": None,
            "predecessor": source,
            "previous_backup": previous,
        }
        store.state(path, value)
        if previous is not None:
            _need(store.read(BACKUP, mode=0o640, kind=APPLICATION_TYPE)[1] == previous)
            store.rename(BACKUP, path / "previous-backup.toml", flags=1, label="previous-backup")
        store.write(
            CANDIDATE, candidate, mode=0o640, gid=store.gid, kind=APPLICATION_TYPE, label="stage"
        )
        _, value["stage"] = store.read(CANDIDATE, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid)
        value["phase"] = "staged"
        store.state(path, value)
        backup_temporary = CONFIGURATION.parent / ".configuration-backup.tmp"
        store.write(
            backup_temporary, base, mode=0o640, gid=store.gid, kind=APPLICATION_TYPE, label="backup"
        )
        store.rename(backup_temporary, BACKUP, flags=1, label="backup")
        _, value["backup"] = store.read(BACKUP, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid)
        value["phase"] = "backup_ready"
        store.state(path, value)
        policy.revalidate(snapshot)
        _need(
            store.read(CONFIGURATION, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid)[1] == source
        )
        value["phase"] = "install_intent"
        store.state(path, value)
        store.rename(CANDIDATE, CONFIGURATION, flags=2, label="exchange")
        store.rename(CANDIDATE, path / "predecessor.toml", flags=1, label="predecessor")
        predecessor_body, predecessor_record = store.read(
            path / "predecessor.toml", mode=0o640, kind=APPLICATION_TYPE, gid=store.gid
        )
        _need(predecessor_body == base and _moved(predecessor_record, source))
        value["phase"] = "installed"
        store.state(path, value)
        checkpoint("confirm:before_read")
        installed, actual = store.read(
            CONFIGURATION, mode=0o640, kind=APPLICATION_TYPE, gid=store.gid
        )
        _need(installed == candidate and _moved(actual, value["stage"]))
        _need(
            configuration_fingerprint(policy.parse_configuration(installed))
            == request["config_fingerprint"]
        )
        policy.confirm_configuration(
            snapshot, candidate, tuple(actual["identity"]), actual["context"]
        )
        value["phase"] = "confirmed"
        store.state(path, value)
        pending_body, actual_pending = store.read(
            PENDING, mode=0o600, kind=GUARD_TYPE, maximum=MAX_STATE, gid=OWNER_GID
        )
        _need(pending_body == _encoded(pending) and actual_pending == pending_record)
        checkpoint("pending:before_unlink")
        PENDING.unlink()
        checkpoint("pending:after_unlink")
        store.sync(PENDING, "pending-clear")
        return _projection(snapshot, request, value, "confirmed", pending=False)


def review_intent_history(policy: Any, snapshot: Any) -> str:  # noqa: ANN401 - fixed protected capture
    """Read-only confirmed-history proof under the original configuration guard."""
    store = _Store(policy, snapshot)
    with store.locked():
        _need(not os.path.lexists(PENDING))
        history, _ = _history(store)
        policy.revalidate(snapshot)
        return hashlib.sha256(_encoded(history)).hexdigest()
