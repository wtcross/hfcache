"""Captured host authority and bounded read inspection (INV-020, decision150).

This standard-library-only module also runs as a protected standalone bootstrap
copy. It never imports the application, reads archive contents, opens credentials,
creates locks, or changes a unit. docs/host-administration.md owns its contract.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import pwd
import re
import selectors
import stat
import subprocess
import sys
import time
import tomllib
import uuid
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator
    from typing import Self

PREFIX = Path("/opt/hfcache")
POLICY = Path("/etc/hfcache/host-helper-policy.json")
DEPLOYMENT = Path("/etc/hfcache/host-helper-deployment.json")
CONFIGURATION = Path("/etc/hfcache/config.toml")
REVISION_KEY = Path("/etc/hfcache/host-helper.key")
SELINUX_INSTALLATION = Path("/etc/hfcache/host-helper-selinux.json")
SELINUX_CONTEXT = "system_u:system_r:hfcache_host_helper_t:s0"
SYNC_OBSERVER_CONTEXT = "system_u:system_r:hfcache_sync_observer_t:s0"
SYNC_OBSERVER_CREDENTIAL_MOUNT = Path("/run/credentials/hfcache-sync.service")
SYNC_OBSERVER_STATE_TYPE = "hfcache_sync_observer_state_t"
SYNC_OBSERVER_STATE = Path("/var/lib/hfcache/scheduled/sync")
SYNC_OBSERVER_DROP_IN = Path("/etc/systemd/system/hfcache-sync.service.d/50-hfcache-observer.conf")
SYNC_OBSERVER_RELATIVE = "packaging/systemd/hfcache-sync.service.d/50-hfcache-observer.conf"
SYNC_OBSERVER_BINDING = "sync_observer_context"
SYNC_OBSERVER_DIRECTORY_MODE = 0o700
SYSTEMD_DROP_IN_DIRECTORY_MODE = 0o755
MAX_SELINUX_INSTALLATION = 16384
MAX_SELINUX_CONTEXT = 4096
SELINUX_CONTEXT_FIELDS = 4
SELINUX_MODULE_PRIORITY = 400
SELINUX_LABELS = {
    "helper_exec": "hfcache_host_helper_exec_t",
    "helper_code": "hfcache_host_helper_code_t",
    "configuration": "hfcache_host_helper_conf_t",
    "application_config": "hfcache_host_helper_application_conf_t",
    "configuration_directory": "hfcache_host_helper_configuration_dir_t",
    "application_state": "hfcache_host_helper_application_state_t",
    "configuration_guard": "hfcache_host_helper_configuration_guard_t",
    "runtime": "hfcache_host_helper_runtime_t",
    "api_credentials": "hfcache_host_helper_secret_t",
    "hub_home": "hfcache_host_helper_hub_state_t",
    "hub_cache": "hfcache_host_helper_hub_state_t",
    "container_secrets": "hfcache_host_helper_secret_t",
    "engine_locks": "hfcache_host_helper_engine_lock_t",
    "engine_shared_memory": "hfcache_host_helper_engine_shm_t",
}
MOUNTINFO = Path("/proc/1/mountinfo")
LOCKS = Path("/proc/locks")
LOCK = Path("/run/hfcache/hfcache.lock")
ARCHIVE_LOCK_TYPE = "hfcache_host_helper_archive_lock_t"
SCHEDULE_DIRECTORY = Path("/etc/systemd/system/hfcache-sync.timer.d")
SCHEDULE = SCHEDULE_DIRECTORY / "50-cockpit.conf"
OWNER = 0
OWNER_GID = 0
MAX_PATH_LENGTH = 4096
MAX_PATH_DEPTH = 32
MAX_METADATA_BYTES = 1048576
MOUNT_FIELDS = 6
MOUNT_TRAILING_FIELDS = 3
MAX_COMMAND_BYTES = 16384
MAX_MOUNT_ROWS = 16384
MAX_FILES = 1024
MAX_WORK_FILES = 4096
MAX_BYTES = 64 * 1024 * 1024
MAX_INSPECTION_NS = 15_000_000_000
MAX_INSPECTION_SECONDS = 15.0
MAX_COMMAND_SECONDS = 5.0
GUARD_HELPER = "/usr/local/libexec/hfcache-host-helper"
MAX_GUARD_INPUT = 4096
MAX_GUARD_OUTPUT = 16384
MAX_ID = (1 << 32) - 2
UNMAPPED_ID = 65534
MAX_AUTHORITY_BYTES = 16777216
MODE_BITS = 0o777
ASCII_MIN = 32
ASCII_MAX = 126
MAX_DELAY_CHARS = 256
KEY_BYTES = 32
START_TICKS_FIELD = 19
LOCK_MODE = 0o600
SCHEDULE_HISTORY_MODE = 0o700
ACTIONS = ("archive", "hub", "control", "schedule", "configuration", "observer")
UNITS = (
    "hfcache-sync.service",
    "hfcache-verify.service",
    "hfcache-sync.timer",
    "hfcache-verify.timer",
)
GUARD = "hfcache-readonly-guard.service"
LOCAL_FILESYSTEMS = frozenset({"xfs", "ext4", "ext3", "ext2", "btrfs", "tmpfs", "overlay"})
METADATA = (
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
PARENT_METADATA = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid")
HEX = re.compile(r"[a-f0-9]{64}\Z")
COMMIT = re.compile(r"[a-f0-9]{40}\Z")
NATIVE_VERSION = re.compile(r"[0-9][A-Za-z0-9.+-]{0,127}\Z")
ROOTLESS_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
UNIT_FILES = frozenset(
    {
        "enabled",
        "enabled-runtime",
        "disabled",
        "static",
        "linked",
        "linked-runtime",
        "masked",
        "masked-runtime",
        "not-found",
    }
)
ROOTLESS_BINDINGS = {
    "container_launcher": (
        Path("/usr/local/libexec/hfcache-container-service"),
        "scripts/container-service.py",
    ),
    "client_launcher": (Path("/usr/local/libexec/hfcache-client"), "scripts/hfcache-client"),
    "system_target": (
        Path("/etc/systemd/system/hfcache.target"),
        "packaging/systemd/hfcache.target",
    ),
    "container_bridge": (
        Path("/etc/systemd/system/hfcache-containers.service"),
        "rendered/hfcache-containers.service",
    ),
    "user_target": (Path("/etc/systemd/user/hfcache.target"), "rendered/hfcache.target"),
    "api_service": (Path("/etc/systemd/user/hfcache-api.service"), "rendered/hfcache-api.service"),
    "caddy_service": (
        Path("/etc/systemd/user/hfcache-caddy.service"),
        "rendered/hfcache-caddy.service",
    ),
    "verification_service": (
        Path("/etc/systemd/user/hfcache-verification.service"),
        "rendered/hfcache-verification.service",
    ),
    "verification_socket": (
        Path("/etc/systemd/user/hfcache-verification.socket"),
        "rendered/hfcache-verification.socket",
    ),
}
NATIVE_BINDINGS = {
    "system_target": (
        Path("/etc/systemd/system/hfcache.target"),
        "packaging/systemd/hfcache.target",
    ),
    **{
        name.replace("-", "_").replace(".", "_").removeprefix("hfcache_"): (
            Path("/etc/systemd/system") / name,
            "packaging/systemd/" + name,
        )
        for name in (
            "hfcache-api.service",
            "hfcache-api.socket",
            "hfcache-verification.service",
            "hfcache-verification.socket",
            "hfcache-sync.service",
            "hfcache-verify.service",
            "hfcache-sync.timer",
            "hfcache-verify.timer",
        )
    },
}


class InspectionError(ValueError):
    """A fixed safe reason; no partial authority or raw diagnostic accompanies it."""

    def __init__(self, reason: str) -> None:
        super().__init__("protected host inspection refused")
        self.reason = reason


INSPECTION_ERRORS = (InspectionError, TimeoutError)


def _need(value: object, reason: str = "deployment-unverified") -> None:
    if not value:
        raise InspectionError(reason)


def _identity(info: os.stat_result, fields: tuple[str, ...] = METADATA) -> tuple[int, ...]:
    return tuple(getattr(info, key) for key in fields)


def _object(value: object, keys: set[str]) -> dict[str, Any]:
    _need(type(value) is dict and set(value) == keys)
    return value  # type: ignore[return-value]


def _digest(value: object) -> str:
    _need(type(value) is str and HEX.fullmatch(value) is not None)
    return value  # type: ignore[return-value]


def _relative(value: object) -> str:
    _need(type(value) is str and 0 < len(value) <= MAX_PATH_LENGTH)
    path = PurePosixPath(value)  # type: ignore[arg-type]
    _need(path.parts and not path.is_absolute() and str(path) == value and ".." not in path.parts)
    _need(len(path.parts) <= MAX_PATH_DEPTH and "\x00" not in value)  # type: ignore[operator]
    return value  # type: ignore[return-value]


def _json(body: bytes) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            _need(key not in result)
            result[key] = value
        return result

    def nonfinite(_value: str) -> None:
        msg = "deployment-unverified"
        raise InspectionError(msg)

    value = json.loads(body.decode("utf-8"), object_pairs_hook=unique, parse_constant=nonfinite)
    _need(type(value) is dict)
    return value


def binding_paths(profile: str, *, observer_context: bool = False) -> dict[str, tuple[Path, str]]:
    """Closed packaging names; this is not a caller-selected path interface."""
    _need(profile in {"native", "rootless"})
    _need(type(observer_context) is bool and (not observer_context or profile == "native"))
    ordinary = "host-helper/" if profile == "rootless" else "src/hfcache/"
    paths = dict(ROOTLESS_BINDINGS if profile == "rootless" else NATIVE_BINDINGS)
    paths.update(
        {
            "helper_daemon": (
                Path("/usr/local/libexec/hfcache-host-helper"),
                "host-helper/host-helper.py" if profile == "rootless" else "scripts/host-helper.py",
            ),
            "helper_unit": (
                Path("/etc/systemd/system/hfcache-host-helper.service"),
                "host-helper/hfcache-host-helper.service"
                if profile == "rootless"
                else "packaging/systemd/hfcache-host-helper.service",
            ),
            "helper_policy_module": (
                Path("/usr/local/lib/hfcache-host-helper/host_policy.py"),
                ordinary + "host_policy.py",
            ),
            "helper_protocol_module": (
                Path("/usr/local/lib/hfcache-host-helper/host_protocol.py"),
                ordinary + "host_protocol.py",
            ),
            "helper_configuration_module": (
                Path("/usr/local/lib/hfcache-host-helper/host_configuration.py"),
                ordinary + "host_configuration.py",
            ),
            "helper_actions_module": (
                Path("/usr/local/lib/hfcache-host-helper/host_actions.py"),
                ordinary + "host_actions.py",
            ),
            "helper_selinux_module": (
                Path("/usr/local/lib/hfcache-host-helper/host_selinux.py"),
                ordinary + "host_selinux.py",
            ),
            "helper_peer_module": (
                Path("/usr/local/lib/hfcache-host-helper/host_peer.py"),
                ordinary + "host_peer.py",
            ),
            "helper_selinux_policy": (
                Path("/usr/local/lib/hfcache-host-helper/hfcache-host-helper.cil"),
                "host-helper/hfcache-host-helper.cil"
                if profile == "rootless"
                else "packaging/selinux/hfcache-host-helper.cil",
            ),
        }
    )
    if observer_context:
        paths[SYNC_OBSERVER_BINDING] = (SYNC_OBSERVER_DROP_IN, SYNC_OBSERVER_RELATIVE)
    return paths


@dataclass
class InspectionBudget:
    """One aggregate request budget, shared by initial inspection and rechecks."""

    deadline_ns: int = field(default_factory=lambda: time.monotonic_ns() + MAX_INSPECTION_NS)
    maximum_files: int = MAX_WORK_FILES
    maximum_bytes: int = MAX_BYTES
    files: int = 0
    bytes: int = 0

    def __post_init__(self) -> None:
        _need(type(self.deadline_ns) is int)
        _need(type(self.maximum_files) is int and 0 < self.maximum_files <= MAX_WORK_FILES)
        _need(type(self.maximum_bytes) is int and 0 < self.maximum_bytes <= MAX_BYTES)
        _need(type(self.files) is int and self.files == 0)
        _need(type(self.bytes) is int and self.bytes == 0)
        self.deadline_ns = min(self.deadline_ns, time.monotonic_ns() + MAX_INSPECTION_NS)

    def remaining(self, limit: float = MAX_COMMAND_SECONDS) -> float:
        _need(0 < limit <= MAX_INSPECTION_SECONDS, "facts-unavailable")
        remaining = (self.deadline_ns - time.monotonic_ns()) / 1_000_000_000
        if remaining <= 0:
            msg = "protected host inspection deadline exhausted"
            raise TimeoutError(msg)
        return min(limit, remaining)

    def consume(self, *, files: int = 0, size: int = 0) -> None:
        _need(type(files) is int and files >= 0 and type(size) is int and size >= 0)
        self.remaining()
        self.files += files
        self.bytes += size
        _need(
            self.files <= self.maximum_files and self.bytes <= self.maximum_bytes,
            "facts-unavailable",
        )


class _Capture:
    def __init__(self, budget: InspectionBudget) -> None:
        self.budget = budget
        self.parents: dict[Path, tuple[int, ...]] = {}
        self.files: dict[Path, tuple[int, ...]] = {}
        self.links: dict[Path, tuple[tuple[int, ...], str]] = {}
        self.absent: set[Path] = set()
        self.labels: dict[Path, tuple[tuple[int, ...], str, str]] = {}
        self.mounts: list[tuple[Path, str, set[str], set[str]]] = []
        self.observer_principal: tuple[int, int] | None = None

    def accounting(self, path: Path) -> str:
        _need(path in {MOUNTINFO, LOCKS}, "facts-unavailable")
        self.budget.consume(files=1)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            data = bytearray()
            while True:
                self.budget.remaining()
                part = os.read(fd, min(65536, 1048577 - len(data)))
                if not part:
                    break
                self.budget.consume(size=len(part))
                data.extend(part)
                _need(len(data) <= MAX_METADATA_BYTES, "facts-unavailable")
            return bytes(data).decode("utf-8")
        finally:
            os.close(fd)

    def mount_table(self) -> tuple[list[tuple[Path, str, set[str], set[str]]], str | None]:
        rows = []
        credential = None
        for line in self.accounting(MOUNTINFO).splitlines():
            left, separator, right = line.partition(" - ")
            before, after = left.split(), right.split()
            _need(
                separator and len(before) >= MOUNT_FIELDS and len(after) >= MOUNT_TRAILING_FIELDS,
                "facts-unavailable",
            )
            raw = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), before[4])
            path = Path(raw)
            _need(path.is_absolute() and str(path) == raw and ".." not in path.parts)
            flags = set(before[5].split(","))
            rows.append((path, after[0], flags, set(after[2].split(","))))
            if path == SYNC_OBSERVER_CREDENTIAL_MOUNT:
                _need(
                    credential is None
                    and re.fullmatch(r"[1-9][0-9]*", before[0])
                    and re.fullmatch(r"0|[1-9][0-9]*", before[1])
                    and re.fullmatch(r"(?:0|[1-9][0-9]*):(?:0|[1-9][0-9]*)", before[2])
                    and before[3] == "/"
                    and len(after) == MOUNT_TRAILING_FIELDS
                    and after[0] == after[1] == "tmpfs"
                    and {"ro", "nosuid", "nodev", "noexec"} <= flags
                    and "rw" not in flags,
                    "facts-unavailable",
                )
                credential = line
            _need(len(rows) <= MAX_MOUNT_ROWS, "facts-unavailable")
        _need(rows, "facts-unavailable")
        return rows, credential

    def mount_rows(self) -> list[tuple[Path, str, set[str], set[str]]]:
        return self.mount_table()[0]

    def local(self, path: Path) -> None:
        _need(path.is_absolute() and ".." not in path.parts and not path.is_relative_to("/srv"))
        matches = [(len(p.parts), fs) for p, fs, _, _ in self.mounts if p in (path, *path.parents)]
        depth = max((item[0] for item in matches), default=-1)
        _need(matches and all(fs in LOCAL_FILESYSTEMS for d, fs in matches if d == depth))

    def parent(self, path: Path, *, owners: set[int] | None = None) -> int:
        self.budget.remaining()
        self.local(path)
        allowed = owners or {OWNER}
        current = Path("/")
        fd = os.open(current, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            for part in (*path.parent.parts[1:], None):
                info = os.fstat(fd)
                _need(info.st_uid in allowed or info.st_uid == 0)
                _need(
                    not info.st_mode & 0o022 or (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)
                )
                ident = _identity(info, PARENT_METADATA)
                _need(current not in self.parents or self.parents[current] == ident)
                self.parents[current] = ident
                if part is not None:
                    child = os.open(
                        part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd
                    )
                    os.close(fd)
                    fd = child
                    current /= part
            return fd  # noqa: TRY300 - descriptor ownership transfers only here
        except BaseException:
            os.close(fd)
            raise

    def read(
        self,
        path: Path,
        *,
        maximum: int = 16777216,
        mode: int | None = None,
        gid: int | None = None,
    ) -> bytes:
        self.budget.consume(files=1)
        parent = self.parent(path)
        fd = -1
        try:
            fd = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent
            )
            before = os.fstat(fd)
            _need(stat.S_ISREG(before.st_mode) and before.st_uid == OWNER and before.st_nlink == 1)
            _need(not before.st_mode & 0o022 and 0 <= before.st_size <= maximum)
            _need(mode is None or stat.S_IMODE(before.st_mode) == mode)
            _need(gid is None or before.st_gid == gid)
            data = bytearray()
            while True:
                self.budget.remaining()
                part = os.read(fd, min(65536, maximum + 1 - len(data)))
                if not part:
                    break
                self.budget.consume(size=len(part))
                data.extend(part)
                _need(len(data) <= maximum)
            after = os.fstat(fd)
            linked = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            ident = _identity(before)
            _need(len(data) == before.st_size and ident == _identity(after) == _identity(linked))
            _need(path not in self.files or self.files[path] == ident)
            self.files[path] = ident
            return bytes(data)
        finally:
            if fd >= 0:
                os.close(fd)
            os.close(parent)

    def link(self, path: Path, expected: str) -> None:
        self.budget.consume(files=1)
        parent = self.parent(path)
        try:
            before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            target = os.readlink(path.name, dir_fd=parent)
            after = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            _need(stat.S_ISLNK(before.st_mode) and before.st_uid == OWNER and target == expected)
            value = (_identity(before), target)
            _need(
                _identity(before) == _identity(after)
                and (path not in self.links or self.links[path] == value)
            )
            self.links[path] = value
        finally:
            os.close(parent)

    def entries(self, path: Path) -> list[tuple[str, os.stat_result]]:
        """A bounded descriptor-relative directory snapshot, never a global hook."""
        descriptor = self.parent(path / ".tree-probe")
        try:
            before = os.fstat(descriptor)
            result = []
            with os.scandir(descriptor) as children:
                for entry in children:
                    self.budget.remaining()
                    _need(len(result) < MAX_FILES, "facts-unavailable")
                    result.append((entry.name, entry.stat(follow_symlinks=False)))
            _need(_identity(before) == _identity(os.fstat(descriptor)), "facts-unavailable")
            return result
        finally:
            os.close(descriptor)

    def walk(
        self, root: Path, *, followlinks: bool = False
    ) -> Iterator[tuple[str, list[str], list[str]]]:
        """Read adapter for the captured installer's original tree predicates."""
        _need(followlinks is False)
        entries = 0
        pending = [root]
        while pending:
            self.budget.remaining()
            path = pending.pop()
            _need(len(path.relative_to(root).parts) <= MAX_PATH_DEPTH)
            directories, leaves = [], []
            for name, info in self.entries(path):
                entries += 1
                _need(entries <= MAX_FILES, "facts-unavailable")
                _need(info.st_uid == OWNER and not info.st_mode & 0o022)
                _need(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))
                if stat.S_ISDIR(info.st_mode):
                    directories.append(name)
                else:
                    leaves.append(name)
            yield str(path), directories, leaves
            pending.extend(path / name for name in reversed(directories))

    def tree(self, root: Path) -> set[str]:
        return {
            (Path(directory) / name).relative_to(root).as_posix()
            for directory, _names, leaves in self.walk(root)
            for name in leaves
        }

    def label(
        self, path: Path, expected_type: str, *, owner: tuple[int, int] | None = None
    ) -> None:
        """Capture visible fixed-object label metadata without reading its body."""
        self.budget.consume(files=1)
        observer_state = path == SYNC_OBSERVER_STATE and expected_type == SYNC_OBSERVER_STATE_TYPE
        _need(owner is None or (observer_state and owner == self.observer_principal))
        if observer_state:
            _need(self.observer_principal is not None)
        principal = self.observer_principal if observer_state else None
        parent = self.parent(path, owners={OWNER, principal[0]} if principal else None)
        try:
            before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            _need(stat.S_ISREG(before.st_mode) or stat.S_ISDIR(before.st_mode))
            if principal is None:
                _need(before.st_uid == OWNER and not before.st_mode & 0o022)
            else:
                _need(
                    (before.st_uid, before.st_gid) == principal
                    and stat.S_IMODE(before.st_mode) == SYNC_OBSERVER_DIRECTORY_MODE
                )
            value = os.getxattr(path, "security.selinux", follow_symlinks=False)
            self.budget.consume(size=len(value))
            _need(0 < len(value) <= MAX_SELINUX_CONTEXT)
            context = value.removesuffix(b"\0").decode("ascii")
            fields = context.split(":", 3)
            _need(
                len(fields) == SELINUX_CONTEXT_FIELDS
                and fields[1] == "object_r"
                and fields[2] == expected_type
                and fields[3] == "s0"
            )
            # ADR154: fixed-name publication intentionally changes this directory's
            # entry timestamps/link count; its identity, ownership/mode and full SID
            # stay pinned. All file labels retain the complete metadata comparison.
            mutable_directory = (
                observer_state
                or (
                    path == CONFIGURATION.parent
                    and expected_type == SELINUX_LABELS["configuration_directory"]
                )
                or (
                    path
                    in {
                        SCHEDULE_DIRECTORY,
                        SCHEDULE_DIRECTORY / ".hfcache-actions",
                        CONFIGURATION.parent / ".host-actions",
                    }
                    and expected_type
                    in {
                        "hfcache_host_helper_schedule_dir_t",
                        "hfcache_host_helper_host_action_state_t",
                    }
                )
            )
            if mutable_directory:
                _need(stat.S_ISDIR(before.st_mode))
            metadata = PARENT_METADATA if mutable_directory else METADATA
            identity = _identity(before, metadata)
            _need(
                _identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False), metadata)
                == identity
            )
            record = (identity, expected_type, context)
            _need(path not in self.labels or self.labels[path] == record)
            self.labels[path] = record
        finally:
            os.close(parent)

    def path_type(self) -> type[Path]:
        capture = self

        class BoundedPath(Path):
            def iterdir(self) -> Generator[Self, None, None]:
                for name, _info in capture.entries(self):
                    yield self / name

        return BoundedPath

    def revalidate(self) -> None:
        self.budget.remaining()
        for path, expected in self.parents.items():
            self.budget.remaining()
            _need(_identity(path.lstat(), PARENT_METADATA) == expected)
        for path, expected in self.files.items():
            self.budget.remaining()
            _need(_identity(path.lstat()) == expected)
        for path, (_identity_before, label, _context_before) in tuple(self.labels.items()):
            self.label(path, label)
        for path, expected in self.links.items():
            self.budget.remaining()
            _need((_identity(path.lstat()), os.readlink(path)) == expected)  # noqa: PTH115 - exact raw spelling
        for path in self.absent:
            self.budget.remaining()
            try:
                path.lstat()
            except FileNotFoundError:
                continue
            reason = "deployment-unverified"
            raise InspectionError(reason)
        self.budget.remaining()


def fixed_interpreter(capture: _Capture, selected: Path, pin: str) -> tuple[Path, set[str]]:
    """Capture only the original fixed uv aliases; never resolve arbitrary links."""
    _need(type(pin) is str and re.fullmatch(r"3\.[0-9]+(?:\.[0-9]+)?", pin))
    minor = ".".join(pin.split(".")[:2])
    primary = selected / ".venv/bin/python"
    parent = capture.parent(primary)
    try:
        raw = os.readlink(primary.name, dir_fd=parent)
    finally:
        os.close(parent)
    capture.link(primary, raw)
    target = Path(raw)
    _need(target.is_absolute() and str(target) == raw and ".." not in target.parts)
    _need(target.is_relative_to(PREFIX / "python"))
    relative = target.relative_to(PREFIX / "python")
    machine = os.uname().machine
    _need(re.fullmatch(r"[a-zA-Z0-9_]+", machine))
    selector = f"cpython-{minor}-linux-{machine}-gnu"
    if relative.parts and relative.parts[0] == selector:
        _need(relative.parts == (selector, "bin", f"python{minor}"))
        link = PREFIX / "python" / selector
        parent = capture.parent(link)
        try:
            raw_directory = os.readlink(link.name, dir_fd=parent)
        finally:
            os.close(parent)
        directory = Path(raw_directory)
        _need(directory.parent == PREFIX / "python" and str(directory) == raw_directory)
        version = re.fullmatch(
            rf"cpython-({re.escape(minor)}\.[0-9]+)-linux-{re.escape(machine)}-gnu", directory.name
        )
        _need(version is not None and (pin == minor or version[1] == pin))
        capture.link(link, raw_directory)
        target = directory / "bin" / f"python{minor}"
    names = {"python"}
    for name in ("python3", f"python{minor}"):
        alias = primary.parent / name
        parent = capture.parent(alias)
        try:
            try:
                os.stat(alias.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                capture.absent.add(alias)
                continue
        finally:
            os.close(parent)
        capture.link(alias, "python")
        names.add(name)
    return target, names


def native_web_files(capture: _Capture, selected: Path) -> set[str]:
    """Capture an optional installed web closure without widening helper budgets."""
    index = selected / "web-release.json"
    entries = dict(capture.entries(selected))
    if index.name not in entries:
        capture.absent.add(index)
        return set()
    _need(index not in capture.absent)
    _need(stat.S_ISREG(entries[index.name].st_mode))
    return {
        index.name,
        *("ui/" + name for name in capture.tree(selected / "ui")),
        *("host-helper/" + name for name in capture.tree(selected / "host-helper")),
    }


def _policy(body: bytes) -> dict[str, Any]:
    value = _object(_json(body), {"schema_version", "deployment_sha256", "permissions"})
    _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
    _digest(value["deployment_sha256"])
    permissions = _object(value["permissions"], set(ACTIONS))
    _need(all(type(item) is bool for item in permissions.values()))
    return value


def _selinux_installation(
    body: bytes, source_sha256: str, host_labels: object | None = None
) -> dict[str, Any]:
    """Root provisioning attestation; never accept paths or runtime policy grants."""
    _need(0 < len(body) <= MAX_SELINUX_INSTALLATION)
    value = _object(
        _json(body), {"schema_version", "module", "domain", "kernel_policy_sha256", "labels"}
    )
    _need(type(value["schema_version"]) is int and value["schema_version"] in {1, 2})
    _need(value["domain"] == SELINUX_CONTEXT)
    _digest(value["kernel_policy_sha256"])
    module = _object(
        value["module"], {"name", "version", "priority", "source_sha256", "loaded_sha256"}
    )
    _need(module["name"] == "hfcache_host_helper")
    _need(type(module["version"]) is int and module["version"] == 1)
    _need(type(module["priority"]) is int and module["priority"] == SELINUX_MODULE_PRIORITY)
    _need(_digest(module["source_sha256"]) == _digest(source_sha256))
    _digest(module["loaded_sha256"])
    if host_labels is not None:
        cast("Any", host_labels).installation_labels(
            value["schema_version"], value["labels"], SELINUX_LABELS, _need
        )
    else:
        _need(value["schema_version"] == 1)
        labels = _object(value["labels"], {*SELINUX_LABELS, "archive"})
        _need(all(labels[role] == expected for role, expected in SELINUX_LABELS.items()))
        _need(
            type(labels["archive"]) is str and labels["archive"] in {"nfs_t", "hfcache_archive_t"}
        )
    return value


def _selinux_state(budget: InspectionBudget, *, require_domain: bool = True) -> None:
    """Fixed kernel facts; administrator preparation is outside the service domain."""
    paths: list[tuple[Path, tuple[bytes, ...]]] = [
        (Path("/sys/fs/selinux/enforce"), (b"1", b"1\n"))
    ]
    if require_domain:
        context = SELINUX_CONTEXT.encode("ascii")
        paths.append(
            (Path(f"/proc/{os.getpid()}/attr/current"), (context, context + b"\0", context + b"\n"))
        )
    for path, expected in paths:
        budget.consume(files=1)
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            value = os.read(descriptor, MAX_SELINUX_CONTEXT + 1)
            budget.consume(size=len(value))
            _need(len(value) <= MAX_SELINUX_CONTEXT and value in expected)
        finally:
            os.close(descriptor)


def _deployment(body: bytes) -> dict[str, Any]:
    value = _object(
        _json(body),
        {
            "schema_version",
            "profile",
            "release",
            "source",
            "api_principal",
            "bindings",
            "authority_files",
            "profile_evidence",
            "selinux_installation_sha256",
        },
    )
    _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
    _digest(value["selinux_installation_sha256"])
    profile = value["profile"]
    _need(type(profile) is str and profile in {"native", "rootless"})
    release = _object(value["release"], {"version", "selector_target"})
    grammar = NATIVE_VERSION if profile == "native" else ROOTLESS_VERSION
    _need(type(release["version"]) is str and grammar.fullmatch(release["version"]) is not None)
    _need(release["selector_target"] == "releases/" + release["version"])
    source = _object(value["source"], {"parent_commit", "snapshot_sha256", "dirty"})
    _need(
        type(source["parent_commit"]) is str
        and COMMIT.fullmatch(source["parent_commit"]) is not None
    )
    _digest(source["snapshot_sha256"])
    _need(type(source["dirty"]) is bool)
    principal = _object(value["api_principal"], {"host_uid", "host_gid"})
    _need(all(type(x) is int and 0 < x <= MAX_ID and x != UNMAPPED_ID for x in principal.values()))
    _need(type(value["bindings"]) is dict)
    optional_observer = SYNC_OBSERVER_BINDING in value["bindings"]
    paths = (
        binding_paths(profile, observer_context=True)
        if optional_observer
        else binding_paths(profile)
    )
    bindings = _object(value["bindings"], set(paths))
    for item in bindings.values():
        _digest(item)
    files = value["authority_files"]
    _need(type(files) is dict and 0 < len(files) <= MAX_FILES)
    for name, item in files.items():
        _relative(name)
        _need(
            not set(PurePosixPath(name).parts)
            & {"archive", ".hfcache", "secrets", "credentials", "state"}
        )
        record = _object(item, {"sha256", "bytes", "mode"})
        _digest(record["sha256"])
        _need(type(record["bytes"]) is int and 0 <= record["bytes"] <= MAX_AUTHORITY_BYTES)
        _need(
            type(record["mode"]) is int
            and 0 <= record["mode"] <= MODE_BITS
            and not record["mode"] & 0o022
        )
    for name, (_host, relative) in paths.items():
        _need(relative in files and files[relative]["sha256"] == bindings[name])
    if profile == "native":
        evidence = _object(
            value["profile_evidence"],
            {
                "package_root_relative",
                "python_link_relative",
                "python_target_relative",
                "python_target_sha256",
            },
        )
        _need(
            type(evidence["package_root_relative"]) is str
            and re.fullmatch(
                r"\.venv/lib/python3\.[0-9]+/site-packages/hfcache",
                evidence["package_root_relative"],
            )
            is not None
        )
        _need(evidence["python_link_relative"] == ".venv/bin/python")
        _relative(evidence["python_target_relative"])
        _digest(evidence["python_target_sha256"])
    else:
        raw_evidence = value["profile_evidence"]
        _need(type(raw_evidence) is dict)
        home_field = {"account_home"} if "account_home" in raw_evidence else set()
        evidence = _object(
            raw_evidence,
            {
                "artifact_index_sha256",
                "runtime_profile_sha256",
                "app_image_sha256",
                "caddy_image_sha256",
            }
            | home_field,
        )
        home = evidence.get("account_home", "/var/lib/hfcache")
        _need(type(home) is str and home in {"/var/lib/hfcache", "/var/lib/hfcache/container-home"})
        for name, item in evidence.items():
            if name != "account_home":
                _digest(item)
    return value


@dataclass(frozen=True)
class AuthoritySnapshot:
    """Private captured generation; returned dictionaries are independent copies."""

    profile: str
    selected_release: Path
    deployment_sha256: str
    policy_sha256: str
    api_principal: tuple[int, int]
    archive_id: str
    base_revision: str
    _deployment_body: bytes = field(repr=False)
    _status_body: bytes = field(repr=False)
    _inspection: Any = field(repr=False, compare=False)

    @property
    def deployment(self) -> dict[str, Any]:
        return _json(self._deployment_body)

    @property
    def budget(self) -> InspectionBudget:
        return self._inspection.capture.budget

    def host_action_status(self) -> dict[str, Any]:
        """Dedicated authority; internal transient states never widen HostStatus1."""
        value = _json(self._status_body)
        if self.profile == "native" and any(
            value["permissions"][action] for action in ("schedule", "observer")
        ):
            try:
                require_host_actions(self)
            except (InspectionError, OSError, ValueError, TimeoutError):
                for action in ("schedule", "observer"):
                    if value["permissions"][action]:
                        value["permissions"][action] = False
                        value["permission_reasons"][action] = "authority-unknown"
            if value["permissions"]["observer"]:
                try:
                    observed = require_sync_observer_context(self)
                    pid = int(observed["MainPID"])
                    _need(
                        pid == 0
                        or observer_process_context(pid, self.budget) == SYNC_OBSERVER_CONTEXT
                    )
                except (InspectionError, OSError, ValueError, TimeoutError):
                    value["permissions"]["observer"] = False
                    value["permission_reasons"]["observer"] = "profile-unproved"
        return value

    def status(self) -> dict[str, Any]:
        """Keep the original public enum closed while a oneshot is starting."""
        value = self.host_action_status()
        if any(
            unit["active"] not in {"active", "inactive", "failed"}
            for unit in value["facts"]["units"].values()
        ):
            return {
                "schema_version": 1,
                "state": "unavailable",
                "reason": "facts-unavailable",
                "profile": None,
                "binding": None,
                "facts": None,
                "permissions": dict.fromkeys(ACTIONS, False),
                "permission_reasons": dict.fromkeys(ACTIONS, "helper-unavailable"),
            }
        return value


def _show(  # noqa: PLR0915 - one closed manager query and its owned-child drain
    unit: str,
    budget: InspectionBudget,
    *,
    include_invocation: bool = False,
    include_observer_context: bool = False,
) -> dict[str, str]:
    _need(unit in {*UNITS, GUARD}, "facts-unavailable")
    _need(not include_invocation or unit in {GUARD, "hfcache-sync.service"}, "facts-unavailable")
    _need(not include_observer_context or unit == "hfcache-sync.service", "facts-unavailable")
    timer = unit.endswith(".timer")
    properties = ["Id", "LoadState", "ActiveState", "SubState", "UnitFileState"]
    if not timer:
        properties.append("MainPID")
    if include_observer_context:
        properties.extend(("SELinuxContext", "DropInPaths"))
    if include_invocation:
        properties.append("InvocationID")
    argv = [
        "/usr/bin/systemctl",
        "--system",
        "show",
        unit,
        "--no-pager",
        "--property=" + ",".join(properties),
    ]
    environment = {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "SYSTEMD_COLORS": "0",
    }
    deadline = time.monotonic() + budget.remaining()
    with subprocess.Popen(  # noqa: S603 - closed fixed manager read, never unit mutation
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=environment,
        cwd="/",
    ) as process:
        try:
            stream = process.stdout
            if stream is None:
                msg = "facts-unavailable"
                raise InspectionError(msg)  # noqa: TRY301 - owned-query finally must drain
            data = bytearray()
            with selectors.DefaultSelector() as selector:
                selector.register(stream, selectors.EVENT_READ)
                while True:
                    remaining = min(budget.remaining(), deadline - time.monotonic())
                    if remaining <= 0 or not selector.select(remaining):
                        msg = "fixed host manager query timed out"
                        raise TimeoutError(msg)  # noqa: TRY301 - finally drains exact owned query
                    part = os.read(stream.fileno(), min(4096, 16385 - len(data)))
                    if not part:
                        break
                    budget.consume(size=len(part))
                    data.extend(part)
                    _need(len(data) <= MAX_COMMAND_BYTES, "facts-unavailable")
            _need(
                process.wait(
                    timeout=max(0.001, min(budget.remaining(), deadline - time.monotonic()))
                )
                == 0,
                "facts-unavailable",
            )
        except BaseException:
            # This is only the exact owned read-command process, never its unit.
            if process.poll() is None:
                process.kill()
            process.wait()
            raise
    result: dict[str, str] = {}
    for line in data.decode("utf-8").splitlines():
        key, separator, value = line.partition("=")
        _need(separator and key not in result, "facts-unavailable")
        result[key] = value
    _need(set(result) == set(properties) and result["Id"] == unit, "facts-unavailable")
    if timer:
        result["MainPID"] = "0"
    _need(
        result["LoadState"] in {"loaded", "masked", "not-found"}
        and result["ActiveState"] in {"active", "inactive", "failed", "activating", "deactivating"},
        "facts-unavailable",
    )
    _need(re.fullmatch(r"[0-9]+", result["MainPID"]) is not None, "facts-unavailable")
    if result["UnitFileState"] == "" and result["LoadState"] == "not-found":
        result["UnitFileState"] = "not-found"
    _need(result["UnitFileState"] in UNIT_FILES, "facts-unavailable")
    return result


def _process_start(pid: int, budget: InspectionBudget) -> int:
    _need(type(pid) is int and pid > 1, "facts-unavailable")
    budget.consume(files=1)
    descriptor = os.open(
        f"/proc/{pid}/stat", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    )
    try:
        body = bytearray()
        while len(body) <= MAX_GUARD_INPUT:
            budget.remaining()
            part = os.read(descriptor, min(MAX_GUARD_INPUT + 1 - len(body), MAX_GUARD_INPUT))
            if not part:
                break
            budget.consume(size=len(part))
            body.extend(part)
        _need(len(body) <= MAX_GUARD_INPUT, "facts-unavailable")
        text = body.decode("ascii")
        _need(text.startswith(str(pid) + " ("), "facts-unavailable")
        fields = text.rpartition(") ")[2].split()
        _need(
            len(fields) > START_TICKS_FIELD and fields[START_TICKS_FIELD].isdigit(),
            "facts-unavailable",
        )
        start = int(fields[START_TICKS_FIELD])
        _need(start > 0, "facts-unavailable")
        return start
    finally:
        os.close(descriptor)


def _guard_unit(budget: InspectionBudget) -> dict[str, str]:
    value = _show(GUARD, budget, include_invocation=True)
    _need(
        set(value)
        == {
            "Id",
            "LoadState",
            "ActiveState",
            "SubState",
            "UnitFileState",
            "MainPID",
            "InvocationID",
        },
        "facts-unavailable",
    )
    return value


def _guard_child(budget: InspectionBudget) -> dict[str, Any]:
    """An expired read child remains owned until it actually exits; never signal."""
    seconds = budget.remaining(MAX_COMMAND_SECONDS)
    request = json.dumps(
        {
            "schema_version": 1,
            "remaining_seconds": seconds,
            "maximum_files": budget.maximum_files - budget.files,
            "maximum_bytes": budget.maximum_bytes - budget.bytes,
        }
    ).encode()
    budget.consume(size=len(request))
    deadline = time.monotonic() + seconds
    environment = {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    with subprocess.Popen(  # noqa: S603 - one fixed protected read-only internal role
        [GUARD_HELPER, "observe-guard"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd="/",
        env=environment,
    ) as process:
        try:
            incoming, outgoing = process.stdout, process.stdin
            if incoming is None or outgoing is None:
                msg = "facts-unavailable"
                raise InspectionError(msg)  # noqa: TRY301 - finally retains actual child drain
            outgoing.write(request)
            outgoing.close()
            body = bytearray()
            with selectors.DefaultSelector() as selector:
                selector.register(incoming, selectors.EVENT_READ)
                while True:
                    remaining = min(budget.remaining(), deadline - time.monotonic())
                    if remaining <= 0 or not selector.select(remaining):
                        msg = "guard observer deadline exhausted"
                        raise TimeoutError(msg)  # noqa: TRY301 - finally retains actual child drain
                    part = os.read(incoming.fileno(), min(4096, MAX_GUARD_OUTPUT + 1 - len(body)))
                    if not part:
                        break
                    budget.consume(size=len(part))
                    body.extend(part)
                    _need(len(body) <= MAX_GUARD_OUTPUT, "facts-unavailable")
            _need(process.wait() == 0 and time.monotonic() <= deadline, "facts-unavailable")
            budget.remaining()
        except BaseException:
            # Deadline/error is not kernel read drainage. Keep this request's
            # worker slot until the sole owned inspector has really exited.
            process.wait()
            raise
    return _json(bytes(body))


class _Inspection:
    def __init__(self, budget: InspectionBudget, host_labels: object | None = None) -> None:
        self.host_labels = cast("Any", host_labels)
        self.capture = _Capture(budget)
        self.capture.mounts, self.observer_credential_mount = self.capture.mount_table()
        self.policy_body = b""
        self.deployment_body = b""
        self.config_body = b""
        self.key = b""
        self.policy: dict[str, Any] = {}
        self.deployment: dict[str, Any] = {}
        self.selected = PREFIX
        self.legacy: dict[str, Any] = {}
        self.guard = ""
        self.schedule_files: tuple[bytes, bytes | None] | None = None
        self.package_files: set[str] | None = None
        self.unit_states: dict[str, dict[str, str]] = {}
        self.observer_configuration: dict[str, str] | None = None
        self.observer_loaded_dropins: str | None = None

    def authority_read(self, path: Path, maximum: int = 16777216) -> bytes:
        relative = path.relative_to(self.selected).as_posix()
        expected = self.deployment["authority_files"].get(relative)
        _need(expected is not None)
        body = self.capture.read(path, maximum=maximum, mode=expected["mode"])
        _need(
            len(body) == expected["bytes"]
            and hashlib.sha256(body).hexdigest() == expected["sha256"]
        )
        return body

    def load(self) -> None:
        try:
            self.policy_body = self.capture.read(POLICY, maximum=4096, mode=0o600, gid=OWNER_GID)
            self.policy = _policy(self.policy_body)
        except FileNotFoundError:
            msg = "policy-missing"
            raise InspectionError(msg) from None
        except TimeoutError:
            raise
        except Exception:  # noqa: BLE001 - fixed unavailable reason, never a partial grant
            msg = "policy-invalid"
            raise InspectionError(msg) from None
        self.deployment_body = self.capture.read(
            DEPLOYMENT, maximum=1048576, mode=0o644, gid=OWNER_GID
        )
        _need(hashlib.sha256(self.deployment_body).hexdigest() == self.policy["deployment_sha256"])
        self.deployment = _deployment(self.deployment_body)
        self.selected = PREFIX / self.deployment["release"]["selector_target"]
        self.capture.link(PREFIX / "current", self.deployment["release"]["selector_target"])
        parent = self.capture.parent(self.selected / ".authority-probe")
        os.close(parent)
        _need(
            not any(
                p.is_relative_to(self.selected) and fs not in LOCAL_FILESYSTEMS
                for p, fs, _, _ in self.capture.mounts
            )
        )
        for name in self.deployment["authority_files"]:
            self.authority_read(self.selected / name)
        self.bindings()
        self.selinux()
        self.legacy = self.legacy_namespace()
        if self.deployment["profile"] == "native":
            self.native()
        else:
            self.rootless()
        self.configuration()

    def bindings(self) -> None:
        profile = self.deployment["profile"]
        principal = self.deployment["api_principal"]
        self.capture.observer_principal = (principal["host_uid"], principal["host_gid"])
        paths = (
            binding_paths(profile, observer_context=True)
            if SYNC_OBSERVER_BINDING in self.deployment["bindings"]
            else binding_paths(profile)
        )
        for name, (host, relative) in paths.items():
            expected = self.deployment["bindings"][name]
            _need(expected == self.deployment["authority_files"][relative]["sha256"])
            if (profile == "rootless" and name in ROOTLESS_BINDINGS) or (
                stat.S_ISLNK(host.lstat().st_mode)
                and not name.startswith("helper_")
                and name != SYNC_OBSERVER_BINDING
            ):
                self.capture.link(host, str(PREFIX / "current" / relative))
            else:
                mode = 0o755 if name == "helper_daemon" else 0o644
                body = self.capture.read(host, mode=mode, gid=OWNER_GID)
                _need(hashlib.sha256(body).hexdigest() == expected)

    def observer_dropins(self) -> None:
        """Do not let a schedule reload adopt an unindexed service override."""
        optional = SYNC_OBSERVER_BINDING in self.deployment["bindings"]
        loaded = _show("hfcache-sync.service", self.capture.budget, include_observer_context=True)[
            "DropInPaths"
        ]
        _need(loaded == (str(SYNC_OBSERVER_DROP_IN) if optional else ""))
        _need(self.observer_loaded_dropins is None or self.observer_loaded_dropins == loaded)
        self.observer_loaded_dropins = loaded
        directory = SYNC_OBSERVER_DROP_IN.parent
        parent = self.capture.parent(directory)
        try:
            try:
                os.stat(directory.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                _need(not optional and directory not in self.capture.labels)
                self.capture.absent.add(directory)
                return
        finally:
            os.close(parent)
        _need(directory not in self.capture.absent)
        self.capture.label(directory, "systemd_unit_file_t")
        info = directory.lstat()
        _need(
            stat.S_IMODE(info.st_mode) == SYSTEMD_DROP_IN_DIRECTORY_MODE
            and info.st_gid == OWNER_GID
        )
        names = [name for name, _info in self.capture.entries(directory)]
        _need(names == ([SYNC_OBSERVER_DROP_IN.name] if optional else []))
        if optional:
            body = self.authority_read(self.selected / SYNC_OBSERVER_RELATIVE, 4096)
            _need(body == ("[Service]\nSELinuxContext=" + SYNC_OBSERVER_CONTEXT + "\n").encode())
            _need(
                self.capture.read(SYNC_OBSERVER_DROP_IN, maximum=4096, mode=0o644, gid=OWNER_GID)
                == body
            )
            self.capture.label(SYNC_OBSERVER_DROP_IN, "systemd_unit_file_t")

    def selinux(self) -> None:
        """Bind visible labels and the independent hidden-object provisioning receipt.

        InaccessiblePaths hides the original archive/secret labels. Their labels
        are the root provisioning attestation, never a claim from a placeholder
        or a proc-root bypass. The receipt's kernel digest is historical evidence.
        """
        _selinux_state(self.capture.budget)
        body = self.capture.read(
            SELINUX_INSTALLATION, maximum=MAX_SELINUX_INSTALLATION, mode=0o644, gid=OWNER_GID
        )
        _need(hashlib.sha256(body).hexdigest() == self.deployment["selinux_installation_sha256"])
        _selinux_installation(
            body, self.deployment["bindings"]["helper_selinux_policy"], self.host_labels
        )
        paths = binding_paths(self.deployment["profile"])
        self.capture.label(paths["helper_daemon"][0], SELINUX_LABELS["helper_exec"])
        library = paths["helper_policy_module"][0].parent
        self.capture.label(library, SELINUX_LABELS["helper_code"])
        for role in (
            "helper_policy_module",
            "helper_protocol_module",
            "helper_peer_module",
            "helper_configuration_module",
            "helper_actions_module",
            "helper_selinux_module",
            "helper_selinux_policy",
        ):
            self.capture.label(paths[role][0], SELINUX_LABELS["helper_code"])
        for path in (POLICY, DEPLOYMENT, REVISION_KEY, SELINUX_INSTALLATION):
            self.capture.label(path, SELINUX_LABELS["configuration"])
        self.capture.label(CONFIGURATION.parent, SELINUX_LABELS["configuration_directory"])
        self.capture.label(CONFIGURATION, SELINUX_LABELS["application_config"])
        self.capture.label(Path("/run/hfcache-host-helper"), SELINUX_LABELS["runtime"])
        self.capture.label(Path("/run/hfcache-host-helper/api"), SELINUX_LABELS["runtime"])

    def legacy_namespace(self) -> dict[str, Any]:
        name = self.selected / "scripts/container-service.py"
        source = self.authority_read(name)
        namespace: dict[str, Any] = {
            "__file__": str(name),
            "__name__": "protected_host_inspection_primitives",
        }
        exec(compile(source, str(name), "exec"), namespace)  # noqa: S102 - captured indexed administrator authority
        namespace.update(
            INSPECTION_PREFIX=PREFIX,
            INSPECTION_OWNER=OWNER,
            INSPECTION_LOCK=LOCK,
            INSPECTION_LOCKS=LOCKS,
            INSPECTION_BINDINGS=dict(ROOTLESS_BINDINGS.values()),
            _inspection_accounting=self.capture.accounting,
            _inspection_parent=lambda path, _rows, *, owners=None: self.capture.parent(
                path, owners=owners
            ),
            _inspection_read=lambda path, _rows, *, maximum: self.capture.read(
                path, maximum=maximum
            ),
            _inspection_system_show=lambda unit: _show(unit, self.capture.budget),
        )
        return namespace

    def native(self) -> None:
        evidence = self.deployment["profile_evidence"]
        required = {
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            ".venv/pyvenv.cfg",
            ".venv/bin/hfcache",
            "scripts/release-profile.py",
            "src/hfcache/__init__.py",
            "src/hfcache/cli.py",
        }
        _need(required <= set(self.deployment["authority_files"]))
        web_files = native_web_files(self.capture, self.selected)
        _need(web_files <= set(self.deployment["authority_files"]))
        web_index = (
            _json(self.authority_read(self.selected / "web-release.json", 2097152))
            if web_files
            else None
        )
        _need(web_index is None or type(web_index.get("files")) is dict)
        pin = self.authority_read(self.selected / ".python-version").decode("ascii").strip()
        _need(re.fullmatch(r"3\.[0-9]+(?:\.[0-9]+)?", pin) is not None)
        minor = ".".join(pin.split(".")[:2])
        _need(evidence["package_root_relative"] == f".venv/lib/python{minor}/site-packages/hfcache")
        package = self.selected / evidence["package_root_relative"]
        parent = self.capture.parent(package / ".package-probe")
        os.close(parent)
        self.package_files = self.capture.tree(package)
        indexed = {
            Path(n).relative_to(evidence["package_root_relative"]).as_posix()
            for n in self.deployment["authority_files"]
            if Path(n).is_relative_to(evidence["package_root_relative"])
        }
        _need(self.package_files and self.package_files == indexed)
        target, names = fixed_interpreter(self.capture, self.selected, pin)
        _need(target == PREFIX / "python" / evidence["python_target_relative"])
        runtime = self.capture.read(target, maximum=MAX_BYTES)
        _need(
            hashlib.sha256(runtime).hexdigest() == evidence["python_target_sha256"]
            and target.stat().st_mode & 0o111
        )
        entry = self.authority_read(self.selected / ".venv/bin/hfcache")
        _need(
            entry.splitlines()[0]
            in {b"#!" + str(self.selected / ".venv/bin" / name).encode() for name in names}
        )
        classifier = self.selected / "scripts/release-profile.py"
        namespace: dict[str, Any] = {
            "__file__": str(classifier),
            "__name__": "protected_native_layout",
        }
        exec(compile(self.authority_read(classifier), str(classifier), "exec"), namespace)  # noqa: S102 - captured indexed classifier, never selected executable

        def read_metadata(
            path: Path, *, binary: bool = False, maximum: int = 4194304
        ) -> bytes | str:
            _need(type(binary) is bool)
            body = self.authority_read(path, maximum)
            relative = path.relative_to(self.selected).as_posix()
            _need(
                body
                or (
                    binary
                    and relative.startswith("ui/")
                    and web_index is not None
                    and relative in web_index["files"]
                )
            )
            return body if binary else body.decode("utf-8")

        namespace["read_metadata"] = read_metadata
        bounded_path = self.capture.path_type()
        namespace["Path"] = bounded_path
        namespace["os"] = SimpleNamespace(**(vars(os) | {"walk": self.capture.walk}))
        _need(
            namespace["native_layout"](
                bounded_path(self.selected),
                installed=True,
                version=self.deployment["release"]["version"],
            )
            == self.deployment["release"]["version"]
        )
        _need(
            web_index is None
            or web_index["source_commit"] == self.deployment["source"]["parent_commit"]
        )

    def rootless(self) -> None:
        evidence = self.deployment["profile_evidence"]
        principal = self.deployment["api_principal"]
        expected_account = (
            principal["host_uid"],
            principal["host_gid"],
            evidence.get("account_home", "/var/lib/hfcache"),
        )
        account = pwd.getpwnam("hfcache")
        _need((account.pw_uid, account.pw_gid, account.pw_dir) == expected_account)
        raw = self.authority_read(self.selected / "artifact-index.json", 1048576)
        _need(hashlib.sha256(raw).hexdigest() == evidence["artifact_index_sha256"])
        index = _json(raw)
        _need(
            set(index) == {"schema_version", "files"}
            and type(index["schema_version"]) is int
            and index["schema_version"] == 1
            and type(index["files"]) is dict
        )
        _need(set(index["files"]) <= set(self.deployment["authority_files"]))
        self.capture.tree(self.selected)
        verifier = self.legacy["_inspection_verifier"](self.selected, self.capture.mounts, index)

        def verified_read(
            path: Path,
            *,
            protected: bool = False,
            maximum: int = MAX_AUTHORITY_BYTES,
            allow_empty: bool = False,
        ) -> bytes:
            _need(protected or path.is_relative_to(self.selected))
            relative = path.relative_to(self.selected).as_posix()
            _need(type(allow_empty) is bool)
            _need(
                not allow_empty
                or (
                    relative.startswith("ui/")
                    and relative in index["files"]
                    and relative in self.deployment["authority_files"]
                )
            )
            body = self.authority_read(path, maximum)
            _need(allow_empty or bool(body))
            return body

        def web_module(module: SimpleNamespace) -> None:
            source = self.selected / "scripts/web-release.py"
            module.__dict__.update(__file__=str(source), __name__="protected_web_release")
            exec(  # noqa: S102 - captured indexed installation authority, never pathname import
                compile(self.authority_read(source), str(source), "exec"), module.__dict__
            )
            parse_assets = module.parse_assets

            def captured_assets(
                root: Path,
                expected: str,
                **constraints: Any,  # noqa: ANN401 - captured parser ABI
            ) -> tuple[dict[str, Any], dict[str, bytes]]:
                _need(root == self.selected / "ui")
                raw_manifest = verified_read(root / "manifest.json", maximum=2097152)
                manifest, members = parse_assets(raw_manifest, expected, **constraints)
                names = {"ui/manifest.json", *("ui/" + name for name in members)}
                _need({name for name in index["files"] if name.startswith("ui/")} == names)
                files = {"manifest.json": raw_manifest}
                for name, member in members.items():
                    body = verified_read(root / name, maximum=member["bytes"], allow_empty=True)
                    _need(
                        len(body) == member["bytes"]
                        and hashlib.sha256(body).hexdigest() == member["sha256"]
                    )
                    files[name] = body
                return manifest, files

            module.load_assets = captured_assets

        def web_spec(name: str, source: Path) -> SimpleNamespace:
            _need(
                name == "hfcache_web_release" and source == self.selected / "scripts/web-release.py"
            )
            return SimpleNamespace(loader=SimpleNamespace(exec_module=web_module))

        verifier["read_file"] = verified_read
        # The installer keeps its own strict web opt-in grammar. Only its fixed
        # sibling loader is adapted: captured code reuses the pure manifest
        # authority while all asset reads retain this inspection's shared budget.
        verifier["importlib"] = SimpleNamespace(
            util=SimpleNamespace(
                spec_from_file_location=web_spec, module_from_spec=lambda _spec: SimpleNamespace()
            )
        )
        # Only this captured namespace sees the adapters. Shared os/pathlib
        # modules remain unchanged when helper exchanges run concurrently.
        verifier["os"] = SimpleNamespace(**(vars(os) | {"walk": self.capture.walk}))
        verifier["Path"] = self.capture.path_type()
        release = verifier["_verify_stage"](self.selected)
        verifier["_verify_bindings"]()
        _need(
            release["version"] == self.deployment["release"]["version"]
            and release["source_commit"] == self.deployment["source"]["parent_commit"]
        )
        _need(
            (release["service_uid"], release["service_gid"])
            == (
                self.deployment["api_principal"]["host_uid"],
                self.deployment["api_principal"]["host_gid"],
            )
        )
        _need(
            release["app_image"] == "sha256:" + evidence["app_image_sha256"]
            and release["caddy_image"] == "sha256:" + evidence["caddy_image_sha256"]
        )
        _need(
            hashlib.sha256(self.authority_read(self.selected / "rendered/runtime.json")).hexdigest()
            == evidence["runtime_profile_sha256"]
        )
        account = pwd.getpwnam("hfcache")
        _need((account.pw_uid, account.pw_gid, account.pw_dir) == expected_account)

    def configuration(self) -> None:
        try:
            self.config_body = self.capture.read(
                CONFIGURATION,
                maximum=1048576,
                mode=0o640,
                gid=self.deployment["api_principal"]["host_gid"],
            )
            value = tomllib.loads(self.config_body.decode("utf-8"))
            _need(type(value.get("schema_version")) is int and value["schema_version"] == 1)
            _need(value["storage"]["archive_root"] == "/srv/hfcache")
            archive_id = value["storage"]["archive_id"]
            _need(type(archive_id) is str and str(uuid.UUID(archive_id)) == archive_id)
            self.archive_id = archive_id
        except TimeoutError:
            raise
        except Exception:  # noqa: BLE001 - fixed unavailable reason, never a partial grant
            msg = "config-unavailable"
            raise InspectionError(msg) from None
        try:
            self.key = self.capture.read(REVISION_KEY, maximum=32, mode=0o600, gid=OWNER_GID)
            _need(len(self.key) == KEY_BYTES)
        except FileNotFoundError:
            msg = "key-missing"
            raise InspectionError(msg) from None
        except TimeoutError:
            raise
        except Exception:  # noqa: BLE001 - fixed unavailable reason, never a partial grant
            msg = "key-invalid"
            raise InspectionError(msg) from None

    def revision(self, domain: bytes, *bodies: bytes) -> str:
        digest = hmac.new(self.key, digestmod=hashlib.sha256)
        for body in (domain, self.deployment_body, self.policy_body, *bodies):
            digest.update(len(body).to_bytes(8, "big"))
            digest.update(body)
        return digest.hexdigest()

    def facts(self) -> dict[str, Any]:
        self.guard = self.guard_state()
        if self.deployment["profile"] == "rootless":
            mount = self.legacy["_inspection_archive_mount"](self.capture.mounts)
        else:
            rows = [
                (kind, flags)
                for path, kind, flags, _ in self.capture.mounts
                if path == Path("/srv/hfcache") and kind != "autofs"
            ]
            _need(len(rows) <= 1, "facts-unavailable")
            mount = "absent"
            if rows:
                kind, flags = rows[0]
                _need(("ro" in flags) != ("rw" in flags), "facts-unavailable")
                _need(kind in LOCAL_FILESYSTEMS | {"nfs", "nfs4"}, "facts-unavailable")
                mount = ("nfs-" if kind in {"nfs", "nfs4"} else "local-") + (
                    "ro" if "ro" in flags else "rw"
                )
        units = {}
        for unit in UNITS:
            value = _show(unit, self.capture.budget)
            self.unit_states[unit] = value.copy()
            units[unit] = {
                "load": value["LoadState"],
                "active": value["ActiveState"],
                "unit_file": value["UnitFileState"],
            }
        return {
            "guard": self.guard,
            "archive_mount": mount,
            "units": units,
            "sync_schedule": self.schedule(),
        }

    def guard_state(self) -> str:
        budget = self.capture.budget
        before = _guard_unit(budget)
        pid = int(before["MainPID"])
        if before["ActiveState"] in {"inactive", "failed"} and pid == 0:
            state = "absent" if before["LoadState"] == "not-found" else "inactive"
            _need(
                self.legacy["_inspection_guard"](self.capture.mounts, {}) == state,
                "facts-unavailable",
            )
            return state
        _need(
            before["LoadState"] == "loaded"
            and before["ActiveState"] == "active"
            and before["SubState"] == "running"
            and pid > 1
            and re.fullmatch(r"[0-9a-f]{32}", before["InvocationID"]),
            "facts-unavailable",
        )
        start = _process_start(pid, budget)
        result = _object(
            _guard_child(budget),
            {"schema_version", "deployment_sha256", "guard", "unit", "start_ticks", "lock", "work"},
        )
        _need(
            type(result["schema_version"]) is int
            and result["schema_version"] == 1
            and result["deployment_sha256"] == hashlib.sha256(self.deployment_body).hexdigest()
            and result["guard"] == "held"
            and result["unit"] == before
            and type(result["start_ticks"]) is int
            and result["start_ticks"] == start,
            "facts-unavailable",
        )
        lock = _object(result["lock"], {"device", "inode", "uid", "gid", "mode"})
        principal = self.deployment["api_principal"]
        _need(
            all(type(number) is int for number in lock.values())
            and lock["device"] > 0
            and lock["inode"] > 0
            and lock["uid"] == principal["host_uid"]
            and lock["gid"] == principal["host_gid"]
            and lock["mode"] == LOCK_MODE,
            "facts-unavailable",
        )
        work = _object(result["work"], {"files", "bytes"})
        budget.consume(files=work["files"], size=work["bytes"])
        _need(
            _process_start(pid, budget) == start and _guard_unit(budget) == before,
            "facts-unavailable",
        )
        return "held"

    @staticmethod
    def timer_fields(body: bytes, *, managed: bool) -> tuple[str | None, str | None]:
        section = ""
        calendar = delay = None
        for raw in body.decode("utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith(("#", ";")):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                _need(not managed or section == "Timer", "facts-unavailable")
                continue
            if section != "Timer":
                _need(not managed, "facts-unavailable")
                continue
            key, separator, value = line.partition("=")
            _need(separator, "facts-unavailable")
            if key == "OnCalendar":
                if value:
                    _need(
                        len(value) <= MAX_PATH_LENGTH
                        and "\\" not in value
                        and all(ASCII_MIN <= ord(c) <= ASCII_MAX for c in value),
                        "facts-unavailable",
                    )
                    calendar = value
                else:
                    calendar = None
            elif key == "RandomizedDelaySec":
                _need(
                    len(value) <= MAX_DELAY_CHARS
                    and "\\" not in value
                    and all(ASCII_MIN <= ord(c) <= ASCII_MAX for c in value),
                    "facts-unavailable",
                )
                delay = value or None
            else:
                _need(not managed, "facts-unavailable")
        return calendar, delay

    def schedule(self) -> dict[str, Any]:
        if self.deployment["profile"] == "rootless":
            return {
                "state": "unavailable",
                "reason": "profile-unproved",
                "revision": None,
                "source": None,
                "on_calendar": None,
                "randomized_delay_sec": None,
            }
        default = self.authority_read(self.selected / NATIVE_BINDINGS["sync_timer"][1])
        calendar, delay = self.timer_fields(default, managed=False)
        managed = None
        if SCHEDULE_DIRECTORY.exists() or SCHEDULE_DIRECTORY.is_symlink():
            parent = self.capture.parent(SCHEDULE_DIRECTORY / ".schedule-probe")
            os.close(parent)
            entries = self.schedule_entries()
            _need(
                len(entries) <= 1 and all(path == SCHEDULE for path in entries), "facts-unavailable"
            )
            if entries:
                managed = self.capture.read(SCHEDULE, maximum=16384, mode=0o644, gid=OWNER_GID)
                calendar, selected_delay = self.timer_fields(managed, managed=True)
                delay = selected_delay if selected_delay is not None else delay
        _need(calendar is not None, "facts-unavailable")
        self.schedule_files = (default, managed)
        return {
            "state": "observed",
            "reason": None,
            "revision": self.revision(
                b"host-schedule-v1", default, b"0" if managed is None else b"1", managed or b""
            ),
            "source": "default" if managed is None else "managed",
            "on_calendar": calendar,
            "randomized_delay_sec": delay,
        }

    def schedule_entries(self) -> list[Path]:
        entries = []
        with os.scandir(SCHEDULE_DIRECTORY) as children:
            for child in children:
                self.capture.budget.remaining()
                path = SCHEDULE_DIRECTORY / child.name
                if child.name == ".hfcache-actions":
                    _need(self.host_labels is not None, "facts-unavailable")
                    self.capture.label(path, "hfcache_host_helper_host_action_state_t")
                    _need(
                        stat.S_IMODE(path.lstat().st_mode) == SCHEDULE_HISTORY_MODE,
                        "facts-unavailable",
                    )
                    continue
                entries.append(path)
                _need(len(entries) <= 1, "facts-unavailable")
        return entries

    def validate(self, *, observer_exited: bool = False) -> None:
        self.capture.budget.remaining()
        if self.deployment["profile"] == "rootless":
            principal = self.deployment["api_principal"]
            account = pwd.getpwnam("hfcache")
            _need(
                (account.pw_uid, account.pw_gid, account.pw_dir)
                == (
                    principal["host_uid"],
                    principal["host_gid"],
                    self.deployment["profile_evidence"].get("account_home", "/var/lib/hfcache"),
                )
            )
        self.selinux()
        _need(
            self.capture.read(POLICY, maximum=4096, mode=0o600, gid=OWNER_GID) == self.policy_body
        )
        _need(
            self.capture.read(DEPLOYMENT, maximum=1048576, mode=0o644, gid=OWNER_GID)
            == self.deployment_body
        )
        _need(
            self.capture.read(
                CONFIGURATION,
                maximum=1048576,
                mode=0o640,
                gid=self.deployment["api_principal"]["host_gid"],
            )
            == self.config_body,
            "config-unavailable",
        )
        _need(
            self.capture.read(REVISION_KEY, maximum=32, mode=0o600, gid=OWNER_GID) == self.key,
            "key-invalid",
        )
        self.capture.link(PREFIX / "current", self.deployment["release"]["selector_target"])
        mounts, credential = self.capture.mount_table()
        if observer_exited and self.observer_credential_mount is not None and credential is None:
            retained = [
                row for row in self.capture.mounts if row[0] != SYNC_OBSERVER_CREDENTIAL_MOUNT
            ]
            _need(mounts == retained, "facts-unavailable")
            self.capture.mounts = retained
            self.observer_credential_mount = None
        _need(
            mounts == self.capture.mounts and credential == self.observer_credential_mount,
            "facts-unavailable",
        )
        _need(
            self.guard_state() == self.guard,
            "facts-unavailable",
        )
        for unit, expected in self.unit_states.items():
            _need(_show(unit, self.capture.budget) == expected, "facts-unavailable")
        if self.package_files is not None:
            package = self.selected / self.deployment["profile_evidence"]["package_root_relative"]
            _need(self.capture.tree(package) == self.package_files)
        if self.schedule_files is not None:
            entries = self.schedule_entries() if SCHEDULE_DIRECTORY.exists() else []
            _need(
                len(entries) <= 1 and all(path == SCHEDULE for path in entries), "facts-unavailable"
            )
            expected = self.schedule_files[1]
            _need(bool(entries) == (expected is not None), "facts-unavailable")
            if expected is not None:
                _need(
                    self.capture.read(SCHEDULE, maximum=16384, mode=0o644, gid=OWNER_GID)
                    == expected,
                    "facts-unavailable",
                )
        if self.observer_loaded_dropins is not None:
            observed = _show(
                "hfcache-sync.service", self.capture.budget, include_observer_context=True
            )
            _need(
                observed["DropInPaths"] == self.observer_loaded_dropins,
                "facts-unavailable",
            )
        if self.observer_configuration is not None:
            _need(
                [name for name, _info in self.capture.entries(SYNC_OBSERVER_DROP_IN.parent)]
                == [SYNC_OBSERVER_DROP_IN.name],
                "facts-unavailable",
            )
            observed = _show(
                "hfcache-sync.service", self.capture.budget, include_observer_context=True
            )
            _need(
                {name: observed[name] for name in ("SELinuxContext", "DropInPaths")}
                == self.observer_configuration,
                "facts-unavailable",
            )
        self.capture.revalidate()

    def snapshot(self) -> AuthoritySnapshot:
        try:
            facts = self.facts()
        except TimeoutError:
            raise
        except Exception:  # noqa: BLE001 - fixed unavailable reason, never a partial grant
            msg = "facts-unavailable"
            raise InspectionError(msg) from None
        self.validate()
        permissions = dict(self.policy["permissions"])
        reasons = {name: "granted" if permissions[name] else "policy-denied" for name in ACTIONS}
        if self.guard == "held":
            permissions["archive"] = False
            reasons["archive"] = "guard-held"
        if self.deployment["profile"] == "rootless":
            for name in ("schedule", "observer"):
                permissions[name] = False
                reasons[name] = "profile-unproved"
        source = self.deployment["source"]
        policy_digest = hashlib.sha256(self.policy_body).hexdigest()
        deployment_digest = hashlib.sha256(self.deployment_body).hexdigest()
        status = {
            "schema_version": 1,
            "state": "guarded" if self.guard == "held" else "supported",
            "reason": None,
            "profile": self.deployment["profile"],
            "binding": {
                "deployment_sha256": deployment_digest,
                "policy_sha256": policy_digest,
                "release_version": self.deployment["release"]["version"],
                "source_commit": source["parent_commit"],
                "source_snapshot_sha256": source["snapshot_sha256"],
                "source_dirty": source["dirty"],
                "archive_id": self.archive_id,
                "archive_root": "/srv/hfcache",
            },
            "permissions": permissions,
            "permission_reasons": reasons,
            "facts": facts,
        }
        return AuthoritySnapshot(
            self.deployment["profile"],
            self.selected,
            deployment_digest,
            policy_digest,
            (
                self.deployment["api_principal"]["host_uid"],
                self.deployment["api_principal"]["host_gid"],
            ),
            self.archive_id,
            self.revision(b"host-config-base-v1", self.config_body),
            self.deployment_body,
            json.dumps(status, sort_keys=True).encode(),
            self,
        )


def inspect_authority(
    *, budget: InspectionBudget | None = None, host_labels: object | None = None
) -> AuthoritySnapshot:
    """Inspect fixed administrator authority; absence/uncertainty never grants."""
    _need(os.geteuid() == OWNER, "deployment-unverified")
    try:
        inspection = _Inspection(budget if budget is not None else InspectionBudget(), host_labels)
        inspection.load()
        return inspection.snapshot()
    except INSPECTION_ERRORS:
        raise
    except Exception:  # noqa: BLE001 - fixed unavailable reason, never a partial grant
        msg = "deployment-unverified"
        raise InspectionError(msg) from None


def _archive_lock_context(capture: _Capture, uid: int, gid: int) -> tuple[tuple[int, ...], bytes]:
    """Observe the fixed service-owned lock without opening or locking its body."""
    capture.budget.consume(files=1)
    parent = capture.parent(LOCK, owners={OWNER, uid})
    try:
        before = os.stat(LOCK.name, dir_fd=parent, follow_symlinks=False)
        _need(
            stat.S_ISREG(before.st_mode)
            and (before.st_uid, before.st_gid) == (uid, gid)
            and stat.S_IMODE(before.st_mode) == LOCK_MODE
            and before.st_nlink == 1,
            "facts-unavailable",
        )
        context = os.getxattr(LOCK, "security.selinux", follow_symlinks=False)
        capture.budget.consume(size=len(context))
        _need(
            0 < len(context) <= MAX_SELINUX_CONTEXT
            and re.fullmatch(
                rb"[A-Za-z0-9_]+:object_r:" + ARCHIVE_LOCK_TYPE.encode() + rb":s0\0?", context
            ),
            "facts-unavailable",
        )
        identity = _identity(before)
        _need(
            _identity(os.stat(LOCK.name, dir_fd=parent, follow_symlinks=False)) == identity,
            "facts-unavailable",
        )
        return identity, context
    finally:
        os.close(parent)


def observe_guard(
    *, bootstrap_work: dict[str, int] | None = None, started_at: float | None = None
) -> dict[str, Any]:
    """Fixed CLI child only: original predicate under protected mixed credentials."""
    _need(os.getresuid() == (0, 0, 0) and os.getresgid() == (0, 0, 0), "facts-unavailable")
    raw = sys.stdin.buffer.read(MAX_GUARD_INPUT + 1)
    _need(len(raw) <= MAX_GUARD_INPUT, "facts-unavailable")
    request = _object(
        _json(raw), {"schema_version", "remaining_seconds", "maximum_files", "maximum_bytes"}
    )
    seconds = request["remaining_seconds"]
    _need(
        type(request["schema_version"]) is int
        and request["schema_version"] == 1
        and type(seconds) is float
        and math.isfinite(seconds)
        and 0 < seconds <= MAX_COMMAND_SECONDS,
        "facts-unavailable",
    )
    started = time.monotonic() if started_at is None else started_at
    _need(type(started) in {float, int} and math.isfinite(started), "facts-unavailable")
    budget = InspectionBudget(
        deadline_ns=int((started + seconds) * 1_000_000_000),
        maximum_files=request["maximum_files"],
        maximum_bytes=request["maximum_bytes"],
    )
    work = (
        {"files": 0, "bytes": 0}
        if bootstrap_work is None
        else _object(bootstrap_work, {"files", "bytes"})
    )
    _need(all(type(number) is int and number >= 0 for number in work.values()), "facts-unavailable")
    budget.consume(files=work["files"], size=work["bytes"] + len(raw))
    inspection = _Inspection(budget)
    body = inspection.capture.read(
        DEPLOYMENT, maximum=MAX_METADATA_BYTES, mode=0o644, gid=OWNER_GID
    )
    inspection.deployment_body = body
    inspection.deployment = _deployment(body)
    inspection.selected = PREFIX / inspection.deployment["release"]["selector_target"]
    inspection.capture.link(PREFIX / "current", inspection.deployment["release"]["selector_target"])
    inspection.legacy = inspection.legacy_namespace()
    principal = inspection.deployment["api_principal"]
    uid, gid = principal["host_uid"], principal["host_gid"]
    account = pwd.getpwnam("hfcache")
    expected_home = (
        inspection.deployment["profile_evidence"].get("account_home", "/var/lib/hfcache")
        if inspection.deployment["profile"] == "rootless"
        else "/var/lib/hfcache"
    )
    _need(
        (account.pw_uid, account.pw_gid, account.pw_dir) == (uid, gid, expected_home),
        "facts-unavailable",
    )
    unit = _guard_unit(budget)
    _need(
        unit["LoadState"] == "loaded"
        and unit["ActiveState"] == "active"
        and unit["SubState"] == "running"
        and int(unit["MainPID"]) > 1
        and re.fullmatch(r"[0-9a-f]{32}", unit["InvocationID"]),
        "facts-unavailable",
    )
    start = _process_start(int(unit["MainPID"]), budget)
    groups = os.getgroups()
    os.setgroups([])
    try:
        os.setresgid(0, gid, 0)
        os.setresuid(0, uid, 0)
        _need(os.getresuid() == (0, uid, 0) and os.getresgid() == (0, gid, 0), "facts-unavailable")
        before = LOCK.lstat()
        lock_context = (
            _archive_lock_context(inspection.capture, uid, gid)
            if inspection.deployment["profile"] == "rootless"
            else None
        )
        release = {"service_uid": uid, "service_gid": gid}
        _need(
            inspection.legacy["_inspection_guard"](inspection.capture.mounts, release) == "held",
            "facts-unavailable",
        )
        _need(_identity(LOCK.lstat()) == _identity(before), "facts-unavailable")
        if lock_context is not None:
            _need(
                _archive_lock_context(inspection.capture, uid, gid) == lock_context,
                "facts-unavailable",
            )
        inspection.capture.revalidate()
    finally:
        os.setresuid(0, 0, 0)
        os.setresgid(0, 0, 0)
        os.setgroups(groups)
    _need(
        _guard_unit(budget) == unit and _process_start(int(unit["MainPID"]), budget) == start,
        "facts-unavailable",
    )
    budget.remaining()
    return {
        "schema_version": 1,
        "deployment_sha256": hashlib.sha256(body).hexdigest(),
        "guard": "held",
        "unit": unit,
        "start_ticks": start,
        "lock": {
            "device": before.st_dev,
            "inode": before.st_ino,
            "uid": before.st_uid,
            "gid": before.st_gid,
            "mode": stat.S_IMODE(before.st_mode),
        },
        "work": {"files": budget.files, "bytes": budget.bytes},
    }


def revalidate(snapshot: AuthoritySnapshot) -> None:
    """Recheck the same captured generation within its original request budget."""
    _need(type(snapshot) is AuthoritySnapshot)
    try:
        snapshot._inspection.validate()  # noqa: SLF001 - module-private immutable capture
    except INSPECTION_ERRORS:
        raise
    except Exception:  # noqa: BLE001 - fixed unavailable reason, never a partial grant
        msg = "facts-unavailable"
        raise InspectionError(msg) from None


def confirm_configuration(
    snapshot: AuthoritySnapshot,
    candidate: bytes,
    identity: tuple[int, ...],
    context: str,
) -> None:
    """Revalidate the original authority with only its installed config leaf replaced."""
    _need(type(snapshot) is AuthoritySnapshot)
    _need(type(candidate) is bytes and len(candidate) <= MAX_CONFIGURATION_BYTES)
    _need(len(identity) == len(METADATA) and all(type(item) is int for item in identity))
    _need(type(context) is str)
    original = snapshot._inspection  # noqa: SLF001 - module-private immutable capture
    inspection = copy(original)
    capture = copy(original.capture)
    inspection.capture = capture
    # Rechecks may extend these maps. Keep the supplied pre-effect capture exact,
    # including its original config inode; only the work budget remains shared.
    capture.parents = original.capture.parents.copy()
    capture.files = original.capture.files.copy()
    capture.links = original.capture.links.copy()
    capture.absent = original.capture.absent.copy()
    capture.labels = original.capture.labels.copy()
    capture.mounts = original.capture.mounts.copy()
    capture.files[CONFIGURATION] = identity
    capture.labels.pop(CONFIGURATION, None)
    inspection.config_body = candidate
    try:
        capture.label(CONFIGURATION, SELINUX_LABELS["application_config"])
        _need(
            capture.labels[CONFIGURATION]
            == (identity, SELINUX_LABELS["application_config"], context),
            "config-unavailable",
        )
        # The captured verifier's adapters close over its capture. Recreate that
        # small indexed namespace for this copy, without reloading the package or
        # hashing the native interpreter a second time.
        inspection.legacy = inspection.legacy_namespace()
        inspection.validate()
    except INSPECTION_ERRORS:
        raise
    except Exception:  # noqa: BLE001 - fixed refusal without a partial confirmation
        msg = "facts-unavailable"
        raise InspectionError(msg) from None


def read_config_base(
    snapshot: AuthoritySnapshot, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """CONFIG-01: projection and opaque revision describe the same private capture."""
    _need(type(body) is dict or body is None, "invalid-request")
    if body:
        _need(set(body) == {"expected_archive_id", "expected_archive_root"}, "invalid-request")
        identifier, root = body["expected_archive_id"], body["expected_archive_root"]
        _need(
            type(identifier) is str
            and re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", identifier) is not None
            and type(root) is str
            and 0 < len(root) <= MAX_PATH_LENGTH
            and root.startswith("/")
            and root.isprintable(),
            "invalid-request",
        )
    revalidate(snapshot)
    status = snapshot.status()
    if body:
        _need(
            type(status) is dict
            and type(status.get("schema_version")) is int
            and status["schema_version"] == 1
            and status.get("state") in {"supported", "guarded"}
            and type(status.get("binding")) is dict
            and type(status.get("permissions")) is dict
            and type(status["permissions"].get("configuration")) is bool,
            "config-unavailable",
        )
    _need(status["permissions"]["configuration"], "operation-denied")
    if body:
        # Decision153: compare the API's lifespan tuple; never open its supplied root.
        binding = status["binding"]
        _need(
            status["profile"] in {"native", "rootless"}
            and binding["archive_id"] == body["expected_archive_id"]
            and binding["archive_root"] == body["expected_archive_root"],
            "config-unavailable",
        )
    document = parse_configuration(snapshot._inspection.config_body)  # noqa: SLF001 - same captured bytes
    result = {
        "schema_version": 1,
        "archive_id": snapshot.archive_id,
        "base_revision": snapshot.base_revision,
        "editable": editable_configuration(document),
        "editable_fields": list(EDITABLE_FIELDS),
        "protected_fields": [
            {"field": name, "description": description} for name, description in PROTECTED_FIELDS
        ],
    }
    _configuration_reply_limit(result, "config-read")
    revalidate(snapshot)
    return result


# Decision153 intentionally keeps this closed schema in the stdlib bootstrap.
# Parity tests compare its grammar/defaults with the application models.
MAX_CONFIGURATION_BYTES = 1048576
MAX_CONFIGURATION_EDITS = 256
MAX_CONFIGURATION_REPLY = 2 * 1048576
_CONFIG_SEGMENT_LENGTH = 96
_CONFIG_ID_SEGMENTS = 2
_CONFIG_ID_MINIMUM = 3
_CONFIG_ID_MAXIMUM = 193
_CONFIG_REVISION_LENGTH = 255
_CONFIG_TAGS = 64
_CONFIG_TAG_LENGTH = 128
_SURROGATE_MINIMUM = 0xD800
_SURROGATE_MAXIMUM = 0xDFFF
EDITABLE_FIELDS = (
    "storage.publication_mode",
    "storage.minimum_free_space_gib",
    "storage.minimum_free_space_percent",
    "storage.maximum_revisions",
    "sync.max_workers",
    "sync.lock_wait_seconds",
    "sync.continue_on_repository_error",
    "sync.dependency_policy",
    "sync.stale_staging_age_hours",
    "verification.lock_wait_seconds",
    "repair.retired_instance_grace_hours",
    "repositories",
)
PROTECTED_FIELDS = (
    ("storage.archive_root", "Archive root is fixed by installed deployment authority."),
    ("storage.archive_id", "Archive identity is fixed by installed deployment authority."),
    ("hub", "Hub endpoint and credential authority are preserved privately."),
    ("verification.algorithm", "The verification algorithm is fixed."),
    ("verification.hash_new_content", "Hashing new content is required."),
    ("server", "Server policy and credentials are managed outside archive configuration."),
)
_CONFIG_DEFAULTS = {
    "hub": {
        "endpoint": "https://huggingface.co",
        "expected_account": "",
        "token_mode": "optional",
        "credential_name": "hf-token",
    },
    "storage": {
        "archive_root": None,
        "archive_id": None,
        "publication_mode": "hardlink",
        "minimum_free_space_gib": 100,
        "minimum_free_space_percent": 10,
        "maximum_revisions": 3,
    },
    "sync": {
        "max_workers": 4,
        "lock_wait_seconds": 3600,
        "continue_on_repository_error": True,
        "dependency_policy": "warn",
        "stale_staging_age_hours": 24,
    },
    "verification": {"algorithm": "sha256", "hash_new_content": True, "lock_wait_seconds": 86400},
    "repair": {"retired_instance_grace_hours": 168},
}
_CONFIG_REPOSITORY_DEFAULTS = {
    "id": None,
    "type": None,
    "revision": "main",
    "enabled": True,
    "tags": [],
    "declared_dependencies": [],
}
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
_CONFIGURATION_INVALID = "invalid-request"


def _config_need(value: object) -> None:
    _need(value, _CONFIGURATION_INVALID)


def _configuration_table(value: object, defaults: dict[str, Any]) -> dict[str, Any]:
    _config_need(type(value) is dict and set(value) <= set(defaults))  # type: ignore[arg-type]
    return {**defaults, **value}  # type: ignore[dict-item]


def _config_integer(value: object, lower: int, upper: int) -> None:
    _config_need(type(value) is int and lower <= value <= upper)  # type: ignore[operator]


def _config_choice(value: object, choices: tuple[str, ...]) -> None:
    _config_need(type(value) is str and value in choices)


def _configuration_repository_id(value: object) -> str:
    _config_need(type(value) is str and _CONFIG_ID_MINIMUM <= len(value) <= _CONFIG_ID_MAXIMUM)  # type: ignore[arg-type]
    segments = value.split("/")  # type: ignore[union-attr]
    _config_need(len(segments) == _CONFIG_ID_SEGMENTS)
    _config_need(
        all(
            1 <= len(part) <= _CONFIG_SEGMENT_LENGTH
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", part)
            for part in segments
        )
    )
    return value  # type: ignore[return-value]


def _configuration_revision(value: object) -> None:
    _config_need(type(value) is str and 1 <= len(value) <= _CONFIG_REVISION_LENGTH)  # type: ignore[arg-type]
    _config_need(re.fullmatch(r"[A-Za-z0-9._/-]+", value) is not None)  # type: ignore[arg-type]
    _config_need(not value.startswith(("-", "/")) and not value.endswith(("/", ".lock")))  # type: ignore[union-attr]
    _config_need("//" not in value and ".." not in value)  # type: ignore[operator]
    _config_need(re.fullmatch(r"[0-9a-fA-F]{4,39}", value) is None)  # type: ignore[arg-type]
    if re.fullmatch(r"[0-9a-fA-F]{40}", value):  # type: ignore[arg-type]
        _config_need(re.fullmatch(r"[0-9a-f]{40}", value) is not None)  # type: ignore[arg-type]


def _configuration_repository(value: object) -> dict[str, Any]:
    row = _configuration_table(value, _CONFIG_REPOSITORY_DEFAULTS)
    _configuration_repository_id(row["id"])
    _config_choice(row["type"], ("model", "dataset"))
    _configuration_revision(row["revision"])
    _config_need(type(row["enabled"]) is bool)
    tags = row["tags"]
    _config_need(type(tags) is list and len(tags) <= _CONFIG_TAGS)
    normalized = set()
    for raw in tags:
        _config_need(type(raw) is str and len(raw) <= _CONFIG_TAG_LENGTH)
        tag = raw.strip(" ").translate(_ASCII_LOWER)
        _config_need(re.fullmatch(r"[a-z0-9][a-z0-9._:/-]{0,63}", tag) is not None)
        normalized.add(tag)
    row["tags"] = sorted(normalized)
    dependencies = row["declared_dependencies"]
    _config_need(type(dependencies) is list)
    row["declared_dependencies"] = [_configuration_repository_id(item) for item in dependencies]
    _config_need(len(set(row["declared_dependencies"])) == len(dependencies))
    return row


def _configuration_values(document: dict[str, Any]) -> None:
    hub, storage = document["hub"], document["storage"]
    endpoint = hub["endpoint"]
    _config_need(type(endpoint) is str and endpoint.startswith("https://"))
    remainder = endpoint.removeprefix("https://")
    _config_need(
        remainder and not remainder.endswith("/") and "/" not in remainder and "?" not in remainder
    )
    account = hub["expected_account"]
    _config_need(
        type(account) is str
        and (not account or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", account))
    )
    _config_choice(hub["token_mode"], ("disabled", "optional", "required"))
    credential = hub["credential_name"]
    _config_need(
        type(credential) is str
        and credential not in {".", ".."}
        and re.fullmatch(r"[A-Za-z0-9._-]{1,64}", credential)
    )
    root = storage["archive_root"]
    _config_need(type(root) is str)
    path = PurePosixPath(root)
    _config_need(path.is_absolute() and str(path) == root and not ({".", ".."} & set(path.parts)))
    archive = storage["archive_id"]
    _config_need(type(archive) is str and str(uuid.UUID(archive)) == archive)
    _config_choice(storage["publication_mode"], ("hardlink", "copy"))
    _config_integer(storage["minimum_free_space_gib"], 0, 1048576)
    _config_integer(storage["minimum_free_space_percent"], 0, 100)
    _config_need(
        type(storage["maximum_revisions"]) is int and storage["maximum_revisions"] in {3, 5}
    )
    sync = document["sync"]
    _config_integer(sync["max_workers"], 1, 32)
    _config_integer(sync["lock_wait_seconds"], 0, 86400)
    _config_need(type(sync["continue_on_repository_error"]) is bool)
    _config_choice(sync["dependency_policy"], ("warn",))
    _config_integer(sync["stale_staging_age_hours"], 1, 8760)
    verification = document["verification"]
    _config_choice(verification["algorithm"], ("sha256",))
    _config_need(
        type(verification["hash_new_content"]) is bool and verification["hash_new_content"]
    )
    _config_integer(verification["lock_wait_seconds"], 0, 604800)
    _config_integer(document["repair"]["retired_instance_grace_hours"], 168, 8760)


def parse_configuration(body: bytes) -> dict[str, Any]:
    """Validate the entire finite schema before projecting or reconstructing it."""
    _need(type(body) is bytes and 0 < len(body) <= MAX_CONFIGURATION_BYTES, "config-unavailable")
    try:
        mapping = tomllib.loads(body.decode("utf-8"))
        _config_need(set(mapping) <= {"schema_version", "repositories", *_CONFIG_DEFAULTS})
        _config_need(type(mapping.get("schema_version")) is int and mapping["schema_version"] == 1)
        document: dict[str, Any] = {"schema_version": 1}
        for table, defaults in _CONFIG_DEFAULTS.items():
            document[table] = _configuration_table(mapping.get(table, {}), defaults)
        _configuration_values(document)
        repositories = mapping.get("repositories", [])
        _config_need(type(repositories) is list)
        document["repositories"] = [_configuration_repository(row) for row in repositories]
        keys = [(row["type"], row["id"]) for row in document["repositories"]]
        _config_need(len(set(keys)) == len(keys))
    except (InspectionError, ValueError, UnicodeError, TypeError, RecursionError):
        reason = "config-unavailable"
        raise InspectionError(reason) from None
    return document


def editable_configuration(document: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for table in ("storage", "sync", "verification", "repair"):
        result[table] = {
            path.split(".")[1]: document[table][path.split(".")[1]]
            for path in EDITABLE_FIELDS
            if path.startswith(table + ".")
        }
    result["repositories"] = [
        {
            **row,
            "tags": list(row["tags"]),
            "declared_dependencies": list(row["declared_dependencies"]),
        }
        for row in document["repositories"]
    ]
    return result


class _ConfigurationWriter:
    """A charged writer for this schema only, not a generic TOML serializer."""

    def __init__(self) -> None:
        self.parts: list[bytes] = []
        self.size = 0

    def append(self, text: str) -> None:
        _config_need(len(text) <= MAX_CONFIGURATION_BYTES - self.size)
        count = 0
        for char in text:
            number = ord(char)
            _config_need(not _SURROGATE_MINIMUM <= number <= _SURROGATE_MAXIMUM)
            count += len(char.encode("utf-8"))
        _config_need(count <= MAX_CONFIGURATION_BYTES - self.size)
        self.size += count
        self.parts.append(text.encode("utf-8"))

    def string(self, value: str) -> None:
        self.append('"')
        start = 0
        for index, char in enumerate(value):
            if char in {'"', "\\"} or ord(char) < ASCII_MIN or ord(char) == ASCII_MAX + 1:
                self.append(value[start:index])
                self.append(
                    "\\" + char if char in {'"', "\\"} else "\\u" + format(ord(char), "04x")
                )
                start = index + 1
        self.append(value[start:])
        self.append('"')

    def value(self, *, value: str | bool | int | list[str]) -> None:
        if type(value) is str:
            self.string(value)
        elif type(value) is bool:
            self.append("true" if value else "false")
        elif type(value) is int:
            self.append(str(value))
        elif type(value) is list:
            self.append("[")
            for index, item in enumerate(value):
                _config_need(type(item) is str)
                if index:
                    self.append(", ")
                self.string(item)
            self.append("]")
        else:
            raise InspectionError(_CONFIGURATION_INVALID)


def render_configuration(document: dict[str, Any]) -> bytes:
    writer = _ConfigurationWriter()
    writer.append("schema_version = 1\n")
    for table, defaults in _CONFIG_DEFAULTS.items():
        writer.append("\n[" + table + "]\n")
        for key in defaults:
            writer.append(key + " = ")
            writer.value(value=document[table][key])
            writer.append("\n")
    for repository in document["repositories"]:
        writer.append("\n[[repositories]]\n")
        for key in _CONFIG_REPOSITORY_DEFAULTS:
            writer.append(key + " = ")
            writer.value(value=repository[key])
            writer.append("\n")
    return b"".join(writer.parts)


def _managed_edits(document: dict[str, Any], managed: object) -> tuple[dict[str, Any], list[str]]:
    _config_need(type(managed) is dict and set(managed) == {"base_revision", "edits"})  # type: ignore[arg-type]
    edits = managed["edits"]  # type: ignore[index]
    _config_need(type(edits) is list and len(edits) <= MAX_CONFIGURATION_EDITS)
    repositories = {(row["type"], row["id"]): row for row in document["repositories"]}
    before = dict(repositories)
    touched = set()
    settings = False
    for edit in edits:
        _config_need(type(edit) is dict and type(edit.get("kind")) is str)
        kind = edit["kind"]
        row: dict[str, Any] = {}
        if kind == "settings-replace":
            _config_need(set(edit) == {"kind", "settings"} and not settings)
            settings = True
            replacement = edit["settings"]
            _config_need(
                type(replacement) is dict
                and replacement
                and set(replacement) <= {"storage", "sync", "verification", "repair"}
            )
            for table, values in replacement.items():
                allowed = {
                    path.split(".")[1] for path in EDITABLE_FIELDS if path.startswith(table + ".")
                }
                _config_need(type(values) is dict and values and set(values) <= allowed)
                document[table].update(values)
            continue
        if kind == "repository-upsert":
            _config_need(set(edit) == {"kind", "repository"})
            row = _configuration_repository(edit["repository"])
            key = (row["type"], row["id"])
        else:
            _config_need(
                kind == "repository-remove"
                and set(edit) == {"kind", "repository_type", "repository_id"}
            )
            _config_choice(edit["repository_type"], ("model", "dataset"))
            key = (edit["repository_type"], _configuration_repository_id(edit["repository_id"]))
        _config_need(key not in touched)
        touched.add(key)
        if kind == "repository-upsert":
            repositories[key] = row
        else:
            _config_need(key in repositories)
            del repositories[key]
    _configuration_values(document)
    document["repositories"] = list(repositories.values())
    selectors = sorted(
        kind + ":" + identifier
        for (kind, identifier), row in repositories.items()
        if row["enabled"]
        and (
            (kind, identifier) not in before
            or not before[kind, identifier]["enabled"]
            or before[kind, identifier]["revision"] != row["revision"]
        )
    )
    return document, selectors


def _configuration_reply_limit(value: dict[str, Any], operation: str) -> None:
    size = 0
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    frame = {
        "schema_version": 1,
        "request_id": "0" * 32,
        "operation": operation,
        "outcome": "ok",
        "body": value,
        "reason": None,
    }
    for piece in encoder.iterencode(frame):
        size += len(piece.encode("utf-8"))
        _config_need(size <= MAX_CONFIGURATION_REPLY)


def _prepare_configuration(snapshot: AuthoritySnapshot, managed: object) -> dict[str, Any]:
    """Decision154: pure captured reconstruction; the caller owns authority rechecks."""
    _config_need(type(managed) is dict and set(managed) == {"base_revision", "edits"})  # type: ignore[arg-type]
    base = managed["base_revision"]  # type: ignore[index]
    _config_need(type(base) is str and HEX.fullmatch(base))
    _need(hmac.compare_digest(base, snapshot.base_revision), "config-conflict")
    document = parse_configuration(snapshot._inspection.config_body)  # noqa: SLF001 - no second capture
    document, selectors = _managed_edits(document, managed)
    candidate = render_configuration(document)
    result = {
        "schema_version": 1,
        "archive_id": snapshot.archive_id,
        "base_revision": snapshot.base_revision,
        "candidate_revision": snapshot._inspection.revision(  # noqa: SLF001 - original protected key
            b"host-config-candidate-v1", base.encode("ascii"), candidate
        ),
        "candidate": candidate.decode("utf-8"),
        "editable": editable_configuration(document),
        "required_selectors": selectors,
    }
    _configuration_reply_limit(result, "config-prepare")
    return result


def prepare_configuration(snapshot: AuthoritySnapshot, managed: object) -> dict[str, Any]:
    """CONFIG-02/03: exact non-installing reconstruction under the original HMAC base."""
    revalidate(snapshot)
    _need(snapshot.status()["permissions"]["configuration"], "operation-denied")
    result = _prepare_configuration(snapshot, managed)
    revalidate(snapshot)
    return result


def require_host_actions(snapshot: AuthoritySnapshot) -> None:
    """Optional v2 provisioning is independently necessary, never a policy grant."""
    inspection = snapshot._inspection  # noqa: SLF001 - same protected capture
    _need(snapshot.profile == "native" and inspection.host_labels is not None, "operation-denied")
    receipt = _json(
        inspection.capture.read(
            SELINUX_INSTALLATION, maximum=MAX_SELINUX_INSTALLATION, mode=0o644, gid=OWNER_GID
        )
    )
    inspection.host_labels.host_action_labels(inspection, receipt, _need)
    inspection.observer_dropins()


def observer_process_context(pid: int, budget: InspectionBudget) -> str:
    """Bounded original-process SID observation; this grants no signal authority."""
    _need(type(pid) is int and 1 < pid <= MAX_ID)
    budget.consume(files=1)
    descriptor = os.open(
        Path("/proc") / str(pid) / "attr/current",
        os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
    )
    try:
        raw = os.read(descriptor, MAX_SELINUX_CONTEXT + 1)
        budget.consume(size=len(raw))
        _need(0 < len(raw) <= MAX_SELINUX_CONTEXT)
        context = raw.removesuffix(b"\0").removesuffix(b"\n").decode("ascii")
        _need(
            re.fullmatch(
                r"[A-Za-z0-9_]+:[A-Za-z0-9_]+:[A-Za-z0-9_]+:s[0-9]+[A-Za-z0-9_:.,-]*",
                context,
            )
        )
        _need(raw in {context.encode(), context.encode() + b"\0", context.encode() + b"\n"})
        return context
    finally:
        os.close(descriptor)


def require_sync_observer_context(snapshot: AuthoritySnapshot) -> dict[str, str]:
    """Optional native stop eligibility; base read/schedule profiles remain valid."""
    inspection = snapshot._inspection  # noqa: SLF001 - original protected capture
    _need(
        snapshot.profile == "native"
        and SYNC_OBSERVER_BINDING in inspection.deployment["bindings"]
        and inspection.host_labels is not None,
        "operation-denied",
    )
    receipt = _json(
        inspection.capture.read(
            SELINUX_INSTALLATION, maximum=MAX_SELINUX_INSTALLATION, mode=0o644, gid=OWNER_GID
        )
    )
    inspection.host_labels.observer_state_labels(inspection, receipt, _need)
    inspection.observer_dropins()
    observed = _show("hfcache-sync.service", snapshot.budget, include_observer_context=True)
    configured = {name: observed[name] for name in ("SELinuxContext", "DropInPaths")}
    _need(
        configured
        == {"SELinuxContext": SYNC_OBSERVER_CONTEXT, "DropInPaths": str(SYNC_OBSERVER_DROP_IN)}
    )
    _need(
        inspection.observer_configuration is None or inspection.observer_configuration == configured
    )
    inspection.observer_configuration = configured
    return observed


def confirm_schedule(
    snapshot: AuthoritySnapshot,
    managed: bytes | None,
    *,
    action: str,
    timer_was_active: bool | None = None,
) -> None:
    """Rebase only this operation's verified fixed leaf and timer/observer observations."""
    _need(
        type(snapshot) is AuthoritySnapshot
        and action in {"pause", "resume", "replace", "reset", "observer"}
    )
    original = snapshot._inspection  # noqa: SLF001 - same protected capture
    inspection, capture = copy(original), copy(original.capture)
    inspection.capture = capture
    for name in ("parents", "files", "links", "labels"):
        setattr(capture, name, getattr(original.capture, name).copy())
    capture.absent = original.capture.absent.copy()
    capture.mounts = original.capture.mounts.copy()
    inspection.unit_states = original.unit_states.copy()
    if action == "observer":
        # ADR156: the sole observer caller has observed the retained original
        # pidfd exit. The clone's final mount read handles its credential teardown.
        _need(snapshot.profile == "native", "facts-unavailable")
    else:
        capture.files.pop(SCHEDULE, None)
        capture.labels.pop(SCHEDULE, None)
        capture.absent.discard(SCHEDULE)
        if managed is None:
            _need(not os.path.lexists(SCHEDULE), "facts-unavailable")
            capture.absent.add(SCHEDULE)
        else:
            _need(capture.read(SCHEDULE, maximum=16384, mode=0o644, gid=OWNER_GID) == managed)
            capture.label(SCHEDULE, "hfcache_host_helper_schedule_file_t")
        inspection.schedule_files = (original.schedule_files[0], managed)
        timer = _show("hfcache-sync.timer", capture.budget)
        expected = action == "resume" if action in {"pause", "resume"} else timer_was_active
        _need(timer["ActiveState"] == ("active" if expected else "inactive"), "facts-unavailable")
        inspection.unit_states["hfcache-sync.timer"] = timer
    inspection.unit_states["hfcache-sync.service"] = _show("hfcache-sync.service", capture.budget)
    inspection.legacy = inspection.legacy_namespace()
    inspection.validate(observer_exited=action == "observer")


def review_intent_locks(snapshot: AuthoritySnapshot, pid: int) -> dict[str, Any]:
    """Metadata-only companion proof: actual authenticated API owns EX flock."""
    capture = snapshot._inspection.capture  # noqa: SLF001 - shared protected snapshot
    path = LOCK.with_name(LOCK.name + ".intent")
    uid, gid = snapshot.api_principal
    parent = capture.parent(path, owners={OWNER, uid})
    try:
        before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        _need(
            stat.S_ISREG(before.st_mode)
            and before.st_uid == uid
            and before.st_gid == gid
            and before.st_nlink == 1
            and stat.S_IMODE(before.st_mode) == LOCK_MODE,
            "facts-unavailable",
        )
        capture.label(path, ARCHIVE_LOCK_TYPE)
        device = (os.major(before.st_dev), os.minor(before.st_dev), before.st_ino)
        matches = 0
        for line in capture.accounting(LOCKS).splitlines():
            fields = line.split()
            if (
                len(fields) == 8  # noqa: PLR2004 - exact proc locks fields
                and fields[1:4] == ["FLOCK", "ADVISORY", "WRITE"]
                and fields[4] == str(pid)
                and fields[6:] == ["0", "EOF"]
            ):
                parts = fields[5].split(":")
                if (
                    len(parts) == len(device)
                    and (int(parts[0], 16), int(parts[1], 16), int(parts[2])) == device
                ):
                    matches += 1
        after = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        _need(matches == 1 and _identity(before) == _identity(after), "facts-unavailable")
    finally:
        os.close(parent)
    original, _ = _archive_lock_context(capture, uid, gid)
    return {
        "intent_lock": {"device": before.st_dev, "inode": before.st_ino},
        "archive_lock": {"device": original[0], "inode": original[1]},
    }
