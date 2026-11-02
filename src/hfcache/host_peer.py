"""Decision150 fixed API process proof for the protected host helper.

The native observer remains root; rootless uses the indexed engine account.
Neither receives effective initial-USER CAP_SYS_PTRACE. The rootless engine
owner remains trusted within its existing USER namespace. Only fixed API facts
are returned.
The privileged caller joins those facts to its retained original socket pidfd.
This bootstrap module supports Python3.12 and imports only the standard library.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import math
import os
import pwd
import re
import select
import selectors
import signal
import stat
import subprocess
import sys
import time
import types
import uuid
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from hfcache.host_policy import AuthoritySnapshot
    from hfcache.host_protocol import LivePeer

DEPLOYMENT = Path("/etc/hfcache/host-helper-deployment.json")
PREFIX = Path("/opt/hfcache")
OBSERVER = "/usr/local/libexec/hfcache-host-helper"
API_UNIT = "hfcache-api.service"
API_CONTAINER = "hfcache-api"
HELPER_PARENT = "/run/hfcache-host-helper/api"
MAX_OUTPUT = 262144
MAX_READ = 1048576
MAX_PROC = 65536
MAX_COMMAND = 1048576
MAX_OBSERVER_SECONDS = 10.0
_HEX32 = re.compile(r"[0-9a-f]{32}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_NAMESPACE = re.compile(r"[a-z]+:\[([1-9][0-9]*)\]\Z")
_VERSION = re.compile(r"[0-9][A-Za-z0-9.+-]{0,127}\Z")
_NAMESPACES = ("mnt", "pid", "user", "net", "ipc", "uts", "cgroup")
_NATIVE_HARDENING = {
    "Type": "simple",
    "NoNewPrivileges": "yes",
    "PrivateTmp": "yes",
    "PrivateDevices": "yes",
    "ProtectSystem": "strict",
    "ProtectHome": "yes",
    "ProtectKernelTunables": "yes",
    "ProtectKernelModules": "yes",
    "ProtectKernelLogs": "yes",
    "ProtectControlGroups": "yes",
    "ProtectClock": "yes",
    "ProtectHostname": "yes",
    "ProtectProc": "invisible",
    "ProcSubset": "pid",
    "RestrictNamespaces": "yes",
    "LockPersonality": "yes",
    "CapabilityBoundingSet": "",
    "AmbientCapabilities": "",
    "PrivateUsers": "no",
    "RootDirectory": "",
    "RootImage": "",
    "DynamicUser": "no",
    "MemoryHigh": "4294967296",
    "TimeoutStopUSec": "infinity",
    "UMask": "0027",
}
_ROOTLESS_MANAGER = {
    "Type": "exec",
    "MemoryHigh": "4294967296",
    "TimeoutStopUSec": "infinity",
    "SendSIGKILL": "no",
    "UMask": "0077",
    "RootDirectory": "",
    "RootImage": "",
    "DynamicUser": "no",
}
_BASE_PROPERTIES = (
    "Id",
    "LoadState",
    "ActiveState",
    "SubState",
    "MainPID",
    "InvocationID",
    "ControlGroup",
    "FragmentPath",
    "DropInPaths",
    "ExecStart",
    "User",
    "Group",
)
_EXPANDED_CAP_DROP = {
    "CAP_CHOWN",
    "CAP_DAC_OVERRIDE",
    "CAP_FOWNER",
    "CAP_FSETID",
    "CAP_KILL",
    "CAP_NET_BIND_SERVICE",
    "CAP_SETFCAP",
    "CAP_SETGID",
    "CAP_SETPCAP",
    "CAP_SETUID",
    "CAP_SYS_CHROOT",
}
_STAT_FIELDS = 20
_MAX_MAPS = 8
_MAP_FIELDS = 3
_CREDENTIAL_FIELDS = 4
_PARENT_MODE = 0o750
_BINDING_MODE = 0o440
_MAX_MOUNTS = 64
_MOUNT_FIELDS = 6
_MOUNT_TRAILING = 3
_MAX_TEXT = 128
_MAX_WORK_FILES = 4096
_CATCH = (OSError, ValueError, KeyError, IndexError, TypeError)


class PeerError(ValueError):
    """Safe refusal only; never include proc data, engine output or stderr."""

    reason = "peer-refused"

    def __init__(self) -> None:
        super().__init__("fixed API peer proof refused")


def _need(value: object) -> None:
    if not value:
        raise PeerError


def _json(body: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            _need(key not in result)
            result[key] = value
        return result

    result = json.loads(body.decode("utf-8"), object_pairs_hook=pairs)
    _need(type(result) is dict)
    return result


@dataclass
class _Budget:
    deadline: float
    maximum_files: int
    maximum_bytes: int
    files: int = 0
    bytes: int = 0

    def remaining(self) -> float:
        result = self.deadline - time.monotonic()
        _need(result > 0)
        return result

    def consume(self, *, size: int = 0, files: int | None = None) -> None:
        self.remaining()
        _need(type(size) is int and size >= 0)
        _need(files is None or (type(files) is int and files >= 0))
        self.bytes += size
        self.files += int(size == 0) if files is None else files
        _need(self.files <= self.maximum_files and self.bytes <= self.maximum_bytes)


def _read(path: Path, budget: _Budget, *, maximum: int, protected: bool = False) -> bytes:
    budget.consume()
    descriptor = -1
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parent.parts[1:]:
            info = os.fstat(parent)
            if protected:
                _need(info.st_uid == 0 and not info.st_mode & 0o022)
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
            )
            os.close(parent)
            parent = child
        if protected:
            info = os.fstat(parent)
            _need(info.st_uid == 0 and not info.st_mode & 0o022)
        descriptor = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent
        )
        before = os.fstat(descriptor)
        _need(stat.S_ISREG(before.st_mode))
        if protected:
            _need(before.st_uid == 0 and before.st_nlink == 1 and not before.st_mode & 0o022)
            _need(before.st_size <= maximum)
        body = bytearray()
        while True:
            budget.remaining()
            part = os.read(descriptor, min(65536, maximum + 1 - len(body)))
            if not part:
                break
            budget.consume(size=len(part))
            body.extend(part)
            _need(len(body) <= maximum)
        if protected:
            fields = (
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
            expected = tuple(getattr(before, key) for key in fields)
            _need(tuple(getattr(os.fstat(descriptor), key) for key in fields) == expected)
            _need(
                tuple(
                    getattr(os.stat(path.name, dir_fd=parent, follow_symlinks=False), key)
                    for key in fields
                )
                == expected
            )
            _need(len(body) == before.st_size)
        return bytes(body)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


_DEFAULT_ACCOUNT_HOME = "/var/lib/hfcache"
_ROOTLESS_ACCOUNT_HOMES = frozenset({_DEFAULT_ACCOUNT_HOME, "/var/lib/hfcache/container-home"})


def _account_home(deployment: dict[str, Any]) -> str:
    """Choose one protected fixed account home; never discover an engine store."""
    profile = deployment["profile"]
    _need(profile in {"native", "rootless"})
    principal = deployment["api_principal"]
    uid, gid = principal["host_uid"], principal["host_gid"]
    home = (
        deployment.get("profile_evidence", {}).get("account_home", _DEFAULT_ACCOUNT_HOME)
        if profile == "rootless"
        else _DEFAULT_ACCOUNT_HOME
    )
    _need(type(home) is str and home in _ROOTLESS_ACCOUNT_HOMES)
    account = pwd.getpwnam("hfcache")
    _need((account.pw_uid, account.pw_gid, account.pw_dir) == (uid, gid, home))
    return home


def _environment(uid: int, *, home: str = _DEFAULT_ACCOUNT_HOME) -> dict[str, str]:
    _need(type(home) is str and home in _ROOTLESS_ACCOUNT_HOMES)
    _need(uid != 0 or home == _DEFAULT_ACCOUNT_HOME)
    environment = {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "SYSTEMD_COLORS": "0",
        "HOME": home,
        "XDG_RUNTIME_DIR": f"/run/user/{uid}",
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{uid}/bus",
    }
    if uid > 0:
        # systemctl show otherwise bypasses the configured session bus.
        environment["SYSTEMCTL_FORCE_BUS"] = "1"
    return environment


def _command(
    argv: list[str], budget: _Budget, *, uid: int, home: str = _DEFAULT_ACCOUNT_HOME
) -> bytes:
    """The fixed observer owns and reaps its same-identity read-only CLI."""
    _need(os.getuid() == os.geteuid() == uid and uid >= 0)
    deadline = min(budget.deadline, time.monotonic() + 5.0)
    body = bytearray()
    with subprocess.Popen(  # noqa: S603 - fixed manager/engine read, no shell
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=_environment(uid, home=home),
        cwd="/",
    ) as process:
        try:
            _need(process.stdout is not None)
            output = cast("IO[bytes]", process.stdout)
            with selectors.DefaultSelector() as selector:
                selector.register(output, selectors.EVENT_READ)
                while True:
                    left = deadline - time.monotonic()
                    _need(left > 0 and selector.select(left))
                    part = os.read(output.fileno(), min(65536, MAX_COMMAND + 1 - len(body)))
                    if not part:
                        break
                    budget.consume(size=len(part))
                    body.extend(part)
                    _need(len(body) <= MAX_COMMAND)
            _need(process.wait(timeout=max(0.001, deadline - time.monotonic())) == 0)
            _need(time.monotonic() < deadline)
            budget.remaining()
        except BaseException:
            # This is an exact owned read-only CLI, never an application unit,
            # container or a process selected by a request. Same UID permits it.
            if process.poll() is None:
                process.kill()
            process.wait()
            raise
    return bytes(body)


_ENGINE_STORAGE_CONFIG = Path("/usr/share/containers/storage.conf")
_ENGINE_STORAGE_CONFIG_SHA = "322dffd5a543bb9e1ca9c67cc56999c62b746118674d004180fe60dddfc21979"
_ENGINE_STORAGE_MAX = 65536
_ENGINE_STORAGE_MODE = 0o644
_ENGINE_OVERRIDE_COUNT = 9


def _engine_storage_identity(info: os.stat_result) -> dict[str, int]:
    return {
        "device": info.st_dev,
        "inode": info.st_ino,
        "mode": info.st_mode,
        "uid": info.st_uid,
        "gid": info.st_gid,
        "links": info.st_nlink,
        "bytes": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
    }


def _engine_storage_file(budget: _Budget) -> dict[str, Any]:
    budget.consume()
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    descriptor = -1
    try:
        for part in _ENGINE_STORAGE_CONFIG.parent.parts[1:]:
            budget.remaining()
            info = os.fstat(parent)
            _need(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022)
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
            )
            os.close(parent)
            parent = child
        info = os.fstat(parent)
        _need(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022)
        descriptor = os.open(
            _ENGINE_STORAGE_CONFIG.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=parent,
        )
        before = os.fstat(descriptor)
        _need(stat.S_ISREG(before.st_mode) and before.st_uid == before.st_gid == 0)
        _need(before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == _ENGINE_STORAGE_MODE)
        _need(0 < before.st_size <= _ENGINE_STORAGE_MAX)
        body = bytearray()
        while True:
            budget.remaining()
            part = os.read(descriptor, min(65536, _ENGINE_STORAGE_MAX + 1 - len(body)))
            if not part:
                break
            budget.consume(size=len(part))
            body.extend(part)
            _need(len(body) <= _ENGINE_STORAGE_MAX)
        captured = _engine_storage_identity(before)
        _need(len(body) == before.st_size)
        _need(_engine_storage_identity(os.fstat(descriptor)) == captured)
        _need(
            _engine_storage_identity(
                os.stat(_ENGINE_STORAGE_CONFIG.name, dir_fd=parent, follow_symlinks=False)
            )
            == captured
        )
        digest = hashlib.sha256(body).hexdigest()
        _need(digest == _ENGINE_STORAGE_CONFIG_SHA)
        return {"sha256": digest, "identity": captured}
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def _engine_storage_override_paths(uid: int, home: str = _DEFAULT_ACCOUNT_HOME) -> list[Path]:
    _need(type(home) is str and home in _ROOTLESS_ACCOUNT_HOMES)
    _need(type(uid) is int and 0 < uid < 2**32)
    result = [
        Path("/etc/containers/storage.conf"),
        Path(home) / ".config/containers/storage.conf",
        Path(home) / ".config/containers/storage.conf.d",
    ]
    for root in ("/etc/containers", "/usr/share/containers"):
        result.extend(
            [
                Path(root) / "storage.conf.d",
                Path(root) / "storage.rootless.conf.d",
                Path(root) / "storage.rootless.conf.d" / str(uid),
            ]
        )
    _need(len(result) == len(set(result)) == _ENGINE_OVERRIDE_COUNT)
    return result


def _engine_storage_absent(path: Path, budget: _Budget) -> dict[str, Any]:
    """Prove a fixed override is absent without following ancestor links.

    Any present object, including an empty directory, is unsupported initially.
    The missing component and retained parent identity make the record precise;
    its caller compares fresh records before/after the owned engine read.
    """
    budget.consume()
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for index, part in enumerate(path.parts[1:]):
            budget.remaining()
            before_parent = _engine_storage_identity(os.fstat(parent))
            try:
                info = os.stat(part, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                _need(_engine_storage_identity(os.fstat(parent)) == before_parent)
                return {
                    "path": str(path),
                    "state": "absent",
                    "missing_component": index,
                    "parent_identity": before_parent,
                }
            _need(index < len(path.parts) - 2 and stat.S_ISDIR(info.st_mode))
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
            )
            try:
                _need(_engine_storage_identity(os.fstat(child)) == _engine_storage_identity(info))
            except BaseException:
                os.close(child)
                raise
            os.close(parent)
            parent = child
        raise PeerError
    finally:
        os.close(parent)


_ENGINE_STORAGE_VENDOR_DIRECTORY_MODE = 0o755
_ENGINE_STORAGE_VENDOR_DROPINS = {
    Path("/usr/share/containers/storage.conf.d"): (
        "00-vendor.conf",
        29,
        "358b7ba3201aea7dba1d8e0e42c8a11e21acdff1b2ca71a4f8b826f41ae5bc80",
    ),
    Path("/usr/share/containers/storage.rootless.conf.d"): (
        "00-vendor-rootless.conf",
        186,
        "f346071a81b5fdb96796397b08f9dc40c9f450166c7f041ddcaa92f115e92ca8",
    ),
}


def _engine_storage_vendor_names(directory: int, expected: str, budget: _Budget) -> None:
    """One fixed entry, bounded even if an unsupported directory is very large."""
    budget.remaining()
    listing = os.open(
        ".", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory
    )
    try:
        _need(
            _engine_storage_identity(os.fstat(listing))
            == _engine_storage_identity(os.fstat(directory))
        )
        with os.scandir(listing) as entries:
            first = next(entries, None)
            _need(first is not None and first.name == expected)
            _need(next(entries, None) is None)
    finally:
        os.close(listing)


def _engine_storage_vendor_directory(path: Path, budget: _Budget) -> dict[str, Any]:
    """Capture only the two exact root-owned stock bundles, never arbitrary .d."""
    _need(path in _ENGINE_STORAGE_VENDOR_DROPINS)
    name, size, expected_sha256 = _ENGINE_STORAGE_VENDOR_DROPINS[path]
    budget.consume()
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    directory = descriptor = -1
    try:
        for part in path.parent.parts[1:]:
            budget.remaining()
            info = os.fstat(parent)
            _need(
                stat.S_ISDIR(info.st_mode)
                and info.st_uid == info.st_gid == 0
                and not info.st_mode & 0o022
            )
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent,
            )
            os.close(parent)
            parent = child
        parent_info = os.fstat(parent)
        _need(
            stat.S_ISDIR(parent_info.st_mode)
            and parent_info.st_uid == parent_info.st_gid == 0
            and not parent_info.st_mode & 0o022
        )
        directory = os.open(
            path.name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent,
        )
        before = os.fstat(directory)
        _need(
            stat.S_ISDIR(before.st_mode)
            and before.st_uid == before.st_gid == 0
            and stat.S_IMODE(before.st_mode) == _ENGINE_STORAGE_VENDOR_DIRECTORY_MODE
        )
        captured = _engine_storage_identity(before)
        _engine_storage_vendor_names(directory, name, budget)
        budget.consume()
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=directory,
        )
        leaf = os.fstat(descriptor)
        _need(
            stat.S_ISREG(leaf.st_mode)
            and leaf.st_uid == leaf.st_gid == 0
            and leaf.st_nlink == 1
            and stat.S_IMODE(leaf.st_mode) == _ENGINE_STORAGE_MODE
            and leaf.st_size == size
        )
        body = bytearray()
        while True:
            budget.remaining()
            part = os.read(descriptor, size + 1 - len(body))
            if not part:
                break
            budget.consume(size=len(part))
            body.extend(part)
            _need(len(body) <= size)
        leaf_identity = _engine_storage_identity(leaf)
        _need(len(body) == size and hashlib.sha256(body).hexdigest() == expected_sha256)
        _need(_engine_storage_identity(os.fstat(descriptor)) == leaf_identity)
        _need(
            _engine_storage_identity(os.stat(name, dir_fd=directory, follow_symlinks=False))
            == leaf_identity
        )
        _engine_storage_vendor_names(directory, name, budget)
        _need(_engine_storage_identity(os.fstat(directory)) == captured)
        _need(
            _engine_storage_identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
            == captured
        )
        return {
            "path": str(path),
            "state": "stock-directory",
            "identity": captured,
            "entries": [{"name": name, "sha256": expected_sha256, "identity": leaf_identity}],
        }
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if directory >= 0:
            os.close(directory)
        os.close(parent)


_ENGINE_LOCK_TYPE = "hfcache_host_helper_engine_lock_t"
_ENGINE_LOCK_MODE = 0o644
_ENGINE_LOCK_BYTES = 64
_ENGINE_RUNTIME_LOCK_BYTES = 0
_ENGINE_RUNTIME_ROOT = Path("/run/user")
_ENGINE_LOCK_CONTEXT_MAX = 4096
_ENGINE_LOCK_CONTEXT_FIELDS = 4
_ENGINE_LOCK_HOME = Path("/var/lib/hfcache")
_ENGINE_LOCK_PATHS = (
    _ENGINE_LOCK_HOME / ".local/share/containers/storage/overlay-images/images.lock",
    _ENGINE_LOCK_HOME / ".local/share/containers/storage/overlay-layers/layers.lock",
)


def _engine_lock_specs(uid: int, home: str = _DEFAULT_ACCOUNT_HOME) -> tuple[tuple[Path, int], ...]:
    """INV-020: two persistent locks and the stock alive/mountpoints locks."""
    _need(type(uid) is int and 0 < uid < 2**32)
    _need(type(home) is str and home in _ROOTLESS_ACCOUNT_HOMES)
    selected = tuple(
        Path(home) / path.relative_to(_ENGINE_LOCK_HOME) for path in _ENGINE_LOCK_PATHS
    )
    return (
        *((path, _ENGINE_LOCK_BYTES) for path in selected),
        (_ENGINE_RUNTIME_ROOT / str(uid) / "libpod/tmp/alive.lck", _ENGINE_RUNTIME_LOCK_BYTES),
        (
            _ENGINE_RUNTIME_ROOT / str(uid) / "containers/overlay-layers/mountpoints.lock",
            _ENGINE_LOCK_BYTES,
        ),
    )


def _engine_lock_parent(
    path: Path, uid: int, gid: int, budget: _Budget, home: str = _DEFAULT_ACCOUNT_HOME
) -> tuple[int, list[dict[str, int]]]:
    """Walk only a fixed lock path; never follow account-controlled aliases."""
    _need(path in {fixed for fixed, _size in _engine_lock_specs(uid, home)})
    budget.consume()
    parent = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    current = Path("/")
    records = []
    try:
        for part in path.parts[1:]:
            budget.remaining()
            info = os.fstat(parent)
            principal = current.is_relative_to(_ENGINE_LOCK_HOME) or current.is_relative_to(
                _ENGINE_RUNTIME_ROOT / str(uid)
            )
            _need(
                stat.S_ISDIR(info.st_mode)
                and not info.st_mode & 0o022
                and info.st_uid in ({0, uid} if principal else {0})
                and info.st_gid in ({0, gid} if principal else {0})
            )
            records.append(_engine_storage_identity(info))
            if part == path.name:
                return parent, records
            budget.consume()
            child = os.open(
                part,
                os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent,
            )
            os.close(parent)
            parent = child
            current /= part
    except BaseException:
        os.close(parent)
        raise
    os.close(parent)
    raise PeerError


def _engine_storage_locks(
    uid: int, gid: int, budget: _Budget, home: str = _DEFAULT_ACCOUNT_HOME
) -> list[dict[str, Any]]:
    """Capture four preprovisioned locks' metadata and labels, never bodies."""
    _need(type(uid) is int and type(gid) is int and 0 < uid < 2**32 and 0 < gid < 2**32)
    result = []
    for path, expected_size in _engine_lock_specs(uid, home):
        parent, ancestors = _engine_lock_parent(path, uid, gid, budget, home)
        descriptor = -1
        try:
            budget.consume()
            descriptor = os.open(path.name, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
            before = os.fstat(descriptor)
            _need(
                stat.S_ISREG(before.st_mode)
                and before.st_uid == uid
                and before.st_gid == gid
                and before.st_nlink == 1
                and stat.S_IMODE(before.st_mode) == _ENGINE_LOCK_MODE
                and before.st_size == expected_size
            )
            captured = _engine_storage_identity(before)
            raw = os.getxattr(f"/proc/self/fd/{descriptor}", "security.selinux")
            budget.consume(size=len(raw), files=0)
            _need(0 < len(raw) <= _ENGINE_LOCK_CONTEXT_MAX)
            context = raw.removesuffix(b"\0").decode("ascii")
            fields = context.split(":", 3)
            _need(
                len(fields) == _ENGINE_LOCK_CONTEXT_FIELDS
                and re.fullmatch(r"[A-Za-z0-9_]+", fields[0]) is not None
                and fields[1] == "object_r"
                and fields[2] == _ENGINE_LOCK_TYPE
                and fields[3] == "s0"
            )
            _need(_engine_storage_identity(os.fstat(descriptor)) == captured)
            current, fresh = _engine_lock_parent(path, uid, gid, budget, home)
            try:
                _need(fresh == ancestors)
                _need(
                    _engine_storage_identity(
                        os.stat(path.name, dir_fd=current, follow_symlinks=False)
                    )
                    == captured
                    == _engine_storage_identity(os.fstat(descriptor))
                )
            finally:
                os.close(current)
            result.append({"path": str(path), "identity": captured, "context": context})
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            os.close(parent)
    budget.remaining()
    return result


_ENGINE_SHM_TYPE = "hfcache_host_helper_engine_shm_t"
_ENGINE_SHM_DIRECTORY = Path("/dev/shm")  # noqa: S108 - fixed existing coordination object only
_ENGINE_SHM_BYTES = 82488
_ENGINE_SHM_MODE = 0o600
_ENGINE_SHM_PARENT_MODE = 0o1777


def _engine_shm_parent(budget: _Budget) -> tuple[int, list[dict[str, int]]]:
    """INV-020: only the exact root-owned sticky SHM directory may be writable."""
    budget.consume()
    descriptor = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    current = Path("/")
    ancestors = []
    try:
        for component in (*_ENGINE_SHM_DIRECTORY.parts[1:], None):
            budget.remaining()
            info = os.fstat(descriptor)
            _need(stat.S_ISDIR(info.st_mode) and info.st_uid == info.st_gid == 0)
            if current == _ENGINE_SHM_DIRECTORY:
                _need(stat.S_IMODE(info.st_mode) == _ENGINE_SHM_PARENT_MODE)
            else:
                _need(not info.st_mode & 0o022)
            ancestors.append(_engine_storage_identity(info))
            if component is None:
                return descriptor, ancestors
            budget.consume()
            child = os.open(
                component,
                os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
            current /= component
    except BaseException:
        os.close(descriptor)
        raise
    os.close(descriptor)
    raise PeerError


def _engine_shared_memory(uid: int, gid: int, budget: _Budget) -> dict[str, Any]:
    """Capture the fixed stock segment's label/metadata; never read or map its body."""
    _need(type(uid) is int and type(gid) is int and 0 < uid < 2**32 and 0 < gid < 2**32)
    name = f"libpod_rootless_lock_{uid}"
    parent, ancestors = _engine_shm_parent(budget)
    descriptor = -1
    try:
        budget.consume()
        descriptor = os.open(name, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
        info = os.fstat(descriptor)
        _need(
            stat.S_ISREG(info.st_mode)
            and info.st_uid == uid
            and info.st_gid == gid
            and info.st_nlink == 1
            and stat.S_IMODE(info.st_mode) == _ENGINE_SHM_MODE
            and info.st_size == _ENGINE_SHM_BYTES
        )
        before = _engine_storage_identity(info)
        raw = os.getxattr(f"/proc/self/fd/{descriptor}", "security.selinux")
        budget.consume(size=len(raw), files=0)
        _need(0 < len(raw) <= _ENGINE_LOCK_CONTEXT_MAX)
        context = raw.removesuffix(b"\0").decode("ascii")
        fields = context.split(":", 3)
        _need(
            len(fields) == _ENGINE_LOCK_CONTEXT_FIELDS
            and re.fullmatch(r"[A-Za-z0-9_]+", fields[0]) is not None
            and fields[1] == "object_r"
            and fields[2] == _ENGINE_SHM_TYPE
            and fields[3] == "s0"
        )
        _need(_engine_storage_identity(os.fstat(descriptor)) == before)
        fresh, current_ancestors = _engine_shm_parent(budget)
        try:
            _need(current_ancestors == ancestors)
            _need(
                _engine_storage_identity(os.stat(name, dir_fd=fresh, follow_symlinks=False))
                == before
                == _engine_storage_identity(os.fstat(descriptor))
            )
        finally:
            os.close(fresh)
        budget.remaining()

        # Shared mutex writes may change timestamps across the command. Capture
        # joins above remain strict; the command binds stable identity and label.
        def stable(row: dict[str, int]) -> dict[str, int]:
            return {k: v for k, v in row.items() if k not in {"mtime_ns", "ctime_ns"}}

        return {
            "path": str(_ENGINE_SHM_DIRECTORY / name),
            "identity": stable(before),
            "ancestors": [stable(row) for row in ancestors],
            "context": context,
        }
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def _engine_storage_config(
    uid: int, gid: int, budget: _Budget, home: str = _DEFAULT_ACCOUNT_HOME
) -> dict[str, Any]:
    """Pinned stock main plus both exact vendor bundles; seven overrides absent."""
    _need(type(uid) is int and type(gid) is int and 0 < uid < 2**32 and 0 < gid < 2**32)
    _need(
        os.getresuid() == (uid, uid, uid)
        and os.getresgid() == (gid, gid, gid)
        and not os.getgroups()
    )
    stock = _engine_storage_file(budget)
    overrides = [
        _engine_storage_vendor_directory(path, budget)
        if path in _ENGINE_STORAGE_VENDOR_DROPINS
        else _engine_storage_absent(path, budget)
        for path in _engine_storage_override_paths(uid, home)
    ]
    budget.remaining()
    return {
        "schema_version": 1,
        "stock": stock,
        "overrides": overrides,
        "original_options": ["overlay.mountopt=nodev"],
    }


_ENGINE = Path("/usr/bin/podman")
_ENGINE_SECONDS = 5.0
_ENGINE_KEEPER_MAX = 64
_ENGINE_ELF_HEADER = b"\x7fELF"
_ENGINE_CAP_LIMIT = 63
_ENGINE_ACCOUNT_CAPS = 0xC0
_ENGINE_INITIAL_MAP = [[0, 0, 4294967295]]
_ENGINE_SECCOMP_MODE = 2
_ENGINE_OVERFLOW_ID = 65534
_ENGINE_SUBID_MIN = 65536
_ENGINE_PREAMBLE_MAX = 16384
_ENGINE_SYS_ADMIN = 21
_ENGINE_SYS_ADMIN_MASK = 1 << _ENGINE_SYS_ADMIN
_ENGINE_DAC_READ_SEARCH = 2
_ENGINE_RETAINED_CAPS = frozenset({_ENGINE_SYS_ADMIN, _ENGINE_DAC_READ_SEARCH})
_ENGINE_RETAINED_MASK = _ENGINE_SYS_ADMIN_MASK | (1 << _ENGINE_DAC_READ_SEARCH)
_ENGINE_NEWUSER = 0x10000000
_ENGINE_NEWNS = 0x00020000
_ENGINE_SECUREBITS = 0xCE
_ENGINE_NS_GET_USERNS = 0xB701
_ENGINE_NS_GET_NSTYPE = 0xB703
_ENGINE_NS_GET_OWNER_UID = 0xB704


class _EngineCapHeader(ctypes.Structure):
    _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]


class _EngineCapData(ctypes.Structure):
    _fields_ = [
        ("effective", ctypes.c_uint32),
        ("permitted", ctypes.c_uint32),
        ("inheritable", ctypes.c_uint32),
    ]


def _engine_syscall(result: int) -> None:
    _need(result == 0)


def _engine_identity(path: Path, budget: _Budget, *, owner: int) -> tuple[bytes, dict[str, int]]:
    """Capture the one fixed keeper record, never a caller-selected path."""
    budget.consume()
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        _need(
            stat.S_ISREG(before.st_mode)
            and before.st_uid == before.st_gid == owner
            and before.st_nlink == 1
            and not before.st_mode & 0o022
            and before.st_size <= _ENGINE_KEEPER_MAX
        )
        body = os.read(descriptor, _ENGINE_KEEPER_MAX + 1)
        budget.consume(size=len(body), files=0)
        identity = _engine_storage_identity(before)
        _need(len(body) == before.st_size and len(body) <= _ENGINE_KEEPER_MAX)
        _need(_engine_storage_identity(os.fstat(descriptor)) == identity)
        _need(_engine_storage_identity(path.lstat()) == identity)
        return body, identity
    finally:
        os.close(descriptor)


def _engine_namespaces(budget: _Budget) -> dict[str, int]:
    result = {}
    for name in _NAMESPACES:
        budget.consume()
        target = str((Path("/proc/self/ns") / name).readlink())
        match = _NAMESPACE.fullmatch(target)
        _need(match is not None and target.startswith(name + ":["))
        result[name] = int(cast("re.Match[str]", match)[1])
    return result


def _engine_status(budget: _Budget) -> dict[str, int]:
    body = _read(Path(f"/proc/{os.getpid()}/status"), budget, maximum=MAX_PROC)
    names = {
        "CapEff",
        "CapPrm",
        "CapInh",
        "CapBnd",
        "CapAmb",
        "NoNewPrivs",
        "Seccomp",
        "Seccomp_filters",
    }
    result = {}
    for line in body.decode("ascii").splitlines():
        key, separator, value = line.partition(":")
        if separator and key in names:
            _need(key not in result)
            value = value.strip()
            pattern = r"[0-9a-f]{16}" if key.startswith("Cap") else r"[0-9]{1,10}"
            _need(re.fullmatch(pattern, value) is not None)
            result[key] = int(value, 16 if key.startswith("Cap") else 10)
    _need(set(result) == names)
    _need(
        result["NoNewPrivs"] == 1
        and result["Seccomp"] == _ENGINE_SECCOMP_MODE
        and result["Seccomp_filters"] > 0
    )
    return result


def _engine_expected_map(path: Path, uid: int, budget: _Budget) -> list[list[int]]:
    body = _read(path, budget, maximum=MAX_PROC, protected=True)
    values = []
    for line in body.decode("ascii").splitlines():
        fields = line.split(":")
        if fields[0] != "hfcache":
            continue
        _need(
            len(fields) == _MAP_FIELDS
            and all(re.fullmatch(r"[0-9]{1,10}", field) for field in fields[1:])
        )
        start, count = int(fields[1]), int(fields[2])
        _need(start > uid and count >= _ENGINE_SUBID_MIN and start + count < 2**32)
        values.append([[0, uid, 1], [1, start, count]])
    _need(len(values) == 1)
    return values[0]


def _engine_binary(budget: _Budget) -> tuple[int, dict[str, int]]:
    """Pin the fixed trusted OS ELF, without hashing its entire executable."""
    budget.consume()
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    descriptor = -1
    try:
        for part in _ENGINE.parent.parts[1:]:
            info = os.fstat(parent)
            _need(info.st_uid == 0 and not info.st_mode & 0o022)
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
            )
            os.close(parent)
            parent = child
        info = os.fstat(parent)
        _need(info.st_uid == 0 and not info.st_mode & 0o022)
        descriptor = os.open(
            _ENGINE.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent
        )
        before = os.fstat(descriptor)
        _need(
            stat.S_ISREG(before.st_mode)
            and before.st_uid == before.st_gid == 0
            and before.st_nlink == 1
            and before.st_size > len(_ENGINE_ELF_HEADER)
            and not before.st_mode & (0o022 | stat.S_ISUID | stat.S_ISGID)
            and before.st_mode & 0o111
        )
        header = os.read(descriptor, len(_ENGINE_ELF_HEADER))
        budget.consume(size=len(header), files=0)
        _need(header == _ENGINE_ELF_HEADER)
        try:
            os.getxattr(descriptor, "security.capability")
        except OSError as error:
            _need(error.errno == errno.ENODATA)
        else:
            raise PeerError
        identity = _engine_storage_identity(before)
        _need(_engine_storage_identity(os.fstat(descriptor)) == identity)
        _need(
            _engine_storage_identity(os.stat(_ENGINE.name, dir_fd=parent, follow_symlinks=False))
            == identity
        )
        result, descriptor = descriptor, -1
        return result, identity
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def _engine_pidfd(pid: int) -> int:
    descriptor = os.pidfd_open(pid, 0)
    try:
        os.set_inheritable(descriptor, False)  # noqa: FBT003 - close-on-exec required
        _engine_live(descriptor)
        return descriptor  # noqa: TRY300 - descriptor ownership transfer
    except BaseException:
        os.close(descriptor)
        raise


def _engine_live(descriptor: int) -> None:
    poller = select.poll()
    poller.register(descriptor, select.POLLIN)
    _need(not poller.poll(0))


def _engine_mount_owner(budget: _Budget) -> dict[str, int]:
    descriptors = []
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        for name in ("user", "mnt"):
            budget.consume()
            descriptors.append(os.open("/proc/self/ns/" + name, os.O_RDONLY | os.O_CLOEXEC))
        owner = libc.ioctl(descriptors[1], _ENGINE_NS_GET_USERNS)
        _need(owner >= 0)
        descriptors.append(owner)
        os.set_inheritable(owner, False)  # noqa: FBT003 - close-on-exec required
        actual, initial = os.fstat(owner), os.fstat(descriptors[0])
        _need((actual.st_dev, actual.st_ino) == (initial.st_dev, initial.st_ino))
        return {
            "user_device": initial.st_dev,
            "user_inode": initial.st_ino,
            "mount_inode": os.fstat(descriptors[1]).st_ino,
        }
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _engine_user_fd(keeper: dict[str, Any], budget: _Budget) -> int:
    budget.consume()
    descriptor = os.open(f"/proc/{keeper['pid']}/ns/user", os.O_RDONLY | os.O_CLOEXEC)
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        _need(libc.ioctl(descriptor, _ENGINE_NS_GET_NSTYPE) == _ENGINE_NEWUSER)
        owner = ctypes.c_uint32()
        _engine_syscall(libc.ioctl(descriptor, _ENGINE_NS_GET_OWNER_UID, ctypes.byref(owner)))
        _need(owner.value == keeper["uid"])
        info = os.fstat(descriptor)
        _need(info.st_ino == keeper["user_inode"])
        _need(str(Path(f"/proc/{keeper['pid']}/ns/user").readlink()) == f"user:[{info.st_ino}]")
        return descriptor  # noqa: TRY300 - descriptor ownership transfer
    except BaseException:
        os.close(descriptor)
        raise


def _engine_single_thread(budget: _Budget) -> None:
    budget.consume()
    with os.scandir("/proc/self/task") as entries:
        first = next(entries, None)
        _need(first is not None and first.name == str(os.getpid()))
        _need(next(entries, None) is None)


def _engine_prepare(deployment: dict[str, Any], budget: _Budget) -> dict[str, Any]:
    """Fresh fixed authority, captured in the original host USER and masked MNT."""
    _need(deployment["profile"] == "rootless")
    uid, gid = deployment["api_principal"]["host_uid"], deployment["api_principal"]["host_gid"]
    home = _account_home(deployment)
    _engine_single_thread(budget)
    storage = _engine_storage_config(uid, gid, budget, home)
    engine_locks = _engine_storage_locks(uid, gid, budget, home)
    engine_shared_memory = _engine_shared_memory(uid, gid, budget)
    state = _engine_status(budget)
    _need(all(state[key] == 0 for key in ("CapEff", "CapPrm", "CapInh", "CapAmb")))
    _need(state["CapBnd"] == _ENGINE_ACCOUNT_CAPS)
    _need(
        _maps(_read(Path(f"/proc/{os.getpid()}/uid_map"), budget, maximum=MAX_PROC))
        == _ENGINE_INITIAL_MAP
    )
    _need(
        _maps(_read(Path(f"/proc/{os.getpid()}/gid_map"), budget, maximum=MAX_PROC))
        == _ENGINE_INITIAL_MAP
    )
    expected_uid = _engine_expected_map(Path("/etc/subuid"), uid, budget)
    expected_gid = _engine_expected_map(Path("/etc/subgid"), gid, budget)
    pause = Path(f"/run/user/{uid}/libpod/tmp/pause.pid")
    body, identity = _engine_identity(pause, budget, owner=uid)
    _need(re.fullmatch(rb"[1-9][0-9]{0,9}\n?", body) is not None)
    pid = int(body)
    _need(pid > 1)
    start = _stat_identity(_read(Path(f"/proc/{pid}/stat"), budget, maximum=MAX_PROC), pid)
    status = _read(Path(f"/proc/{pid}/status"), budget, maximum=MAX_PROC)
    credentials = {}
    for line in status.decode("ascii").splitlines():
        key, _, value = line.partition(":")
        if key in {"Uid", "Gid"}:
            _need(key not in credentials)
            credentials[key] = [int(field) for field in value.split()]
    _need(credentials == {"Uid": [uid] * 4, "Gid": [gid] * 4})
    uid_map = _maps(_read(Path(f"/proc/{pid}/uid_map"), budget, maximum=MAX_PROC))
    gid_map = _maps(_read(Path(f"/proc/{pid}/gid_map"), budget, maximum=MAX_PROC))
    _need(uid_map == expected_uid and gid_map == expected_gid)
    budget.consume()
    match = _NAMESPACE.fullmatch(str(Path(f"/proc/{pid}/ns/user").readlink()))
    _need(match is not None)
    keeper = {
        "pid": pid,
        "start_ticks": start,
        "uid": uid,
        "gid": gid,
        "user_inode": int(cast("re.Match[str]", match)[1]),
        "record": identity,
        "uid_map": uid_map,
        "gid_map": gid_map,
    }
    descriptor = _engine_user_fd(keeper, budget)
    os.close(descriptor)
    pidfd = _engine_pidfd(pid)
    try:
        _need(
            _stat_identity(_read(Path(f"/proc/{pid}/stat"), budget, maximum=MAX_PROC), pid) == start
        )
        _need(_engine_identity(pause, budget, owner=uid) == (body, identity))
        _engine_live(pidfd)
    finally:
        os.close(pidfd)
    binary, binary_identity = _engine_binary(budget)
    os.close(binary)
    return {
        "schema_version": 1,
        "keeper": keeper,
        "account_home": home,
        "storage": storage,
        "engine_locks": engine_locks,
        "engine_shared_memory": engine_shared_memory,
        "namespaces": _engine_namespaces(budget),
        "mount_owner": _engine_mount_owner(budget),
        "binary": binary_identity,
        "seccomp_filters": state["Seccomp_filters"],
    }


def _engine_capabilities(libc: ctypes.CDLL, last: int) -> None:
    _need(_ENGINE_SYS_ADMIN <= last <= _ENGINE_CAP_LIMIT)
    for capability in range(last + 1):
        if capability not in _ENGINE_RETAINED_CAPS:
            _engine_syscall(libc.prctl(24, capability, 0, 0, 0))
    for capability in range(last + 1):
        _need(libc.prctl(23, capability, 0, 0, 0) == int(capability in _ENGINE_RETAINED_CAPS))
    _engine_syscall(libc.prctl(47, 4, 0, 0, 0))
    _engine_syscall(libc.prctl(28, _ENGINE_SECUREBITS, 0, 0, 0))
    header = _EngineCapHeader(0x20080522, 0)
    data = (_EngineCapData * 2)()
    data[0].effective = data[0].permitted = _ENGINE_RETAINED_MASK
    _engine_syscall(libc.capset(ctypes.byref(header), ctypes.byref(data)))
    _need(libc.prctl(27, 0, 0, 0, 0) == _ENGINE_SECUREBITS)


def _engine_enter(prepared: dict[str, Any], budget: _Budget) -> dict[str, Any]:
    """Enter only the verified existing engine USER; never its mount namespace."""
    _engine_single_thread(budget)
    limit = _read(Path("/proc/sys/kernel/cap_last_cap"), budget, maximum=64)
    _need(re.fullmatch(rb"[0-9]{1,2}\n?", limit) is not None)
    descriptor = _engine_user_fd(prepared["keeper"], budget)
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        _engine_syscall(libc.setns(descriptor, _ENGINE_NEWUSER))
    finally:
        os.close(descriptor)
    _need(os.getresuid() == (0, 0, 0) and os.getresgid() == (0, 0, 0) and not os.getgroups())
    _engine_capabilities(libc, int(limit))
    namespaces = _engine_namespaces(budget)
    _need(namespaces["user"] == prepared["keeper"]["user_inode"])
    _need(
        all(
            namespaces[key] == value
            for key, value in prepared["namespaces"].items()
            if key != "user"
        )
    )
    state = _engine_status(budget)
    _need(all(state[key] == _ENGINE_RETAINED_MASK for key in ("CapEff", "CapPrm", "CapBnd")))
    _need(state["CapInh"] == state["CapAmb"] == 0)
    _need(state["Seccomp_filters"] == prepared["seccomp_filters"])
    for call in (
        lambda: libc.unshare(_ENGINE_NEWNS),
        lambda: libc.setns(-1, _ENGINE_NEWNS),
        lambda: libc.setns(-1, 0),
    ):
        ctypes.set_errno(0)
        _need(call() == -1 and ctypes.get_errno() == errno.EPERM)
    return {
        "namespaces": namespaces,
        "capabilities": state,
        "securebits": _ENGINE_SECUREBITS,
        "mount_transitions_denied": True,
    }


def _engine_argv() -> list[str]:
    return [
        str(_ENGINE),
        "--remote=false",
        "--storage-opt=overlay.mountopt=nodev",
        "--storage-opt=overlay.skip_mount_home=true",
        "container",
        "inspect",
        API_CONTAINER,
    ]


def observe_engine(
    *, bootstrap_work: dict[str, int] | None = None, started_at: float | None = None
) -> None:
    """Fixed internal child: one bounded preamble then the unaltered inspect JSON."""
    request = _json(sys.stdin.buffer.read(4097))
    _need(
        type(request.get("remaining_seconds")) in (float, int)
        and request["remaining_seconds"] <= _ENGINE_SECONDS
    )
    budget = _observer_budget(request, bootstrap_work, started_at)
    signal.signal(signal.SIGALRM, lambda _signal, _frame: (_ for _ in ()).throw(PeerError()))
    signal.setitimer(signal.ITIMER_REAL, budget.remaining())
    deployment_body = _read(DEPLOYMENT, budget, maximum=MAX_READ, protected=True)
    deployment = _json(deployment_body)
    prepared = _engine_prepare(deployment, budget)
    binary, identity = _engine_binary(budget)
    try:
        _need(identity == prepared["binary"])
        _need(_read(DEPLOYMENT, budget, maximum=MAX_READ, protected=True) == deployment_body)
        state = _engine_enter(prepared, budget)
        # Every namespace/pidfd used for proof has been closed before the fixed
        # FD exec. Only its CLOEXEC executable descriptor survives to fexecve.
        projected = _engine_storage_identity(os.fstat(binary))
        _need(projected["uid"] == projected["gid"] == _ENGINE_OVERFLOW_ID)
        _need(projected | {"uid": 0, "gid": 0} == identity)
        pid = os.getpid()
        start = _stat_identity(
            _read(Path(f"/proc/{os.getpid()}/stat"), budget, maximum=MAX_PROC), pid
        )
        preamble = {
            "schema_version": 1,
            "deployment_sha256": hashlib.sha256(deployment_body).hexdigest(),
            "process": {"pid": pid, "start_ticks": start},
            "prepared": prepared,
            "entered": state,
            "work": {"files": budget.files, "bytes": budget.bytes},
        }
        body = (
            json.dumps(preamble, separators=(",", ":"), sort_keys=True, allow_nan=False).encode()
            + b"\n"
        )
        _need(len(body) <= _ENGINE_PREAMBLE_MAX and os.execve in os.supports_fd)
        budget.remaining()
        sys.stdout.buffer.write(body)
        sys.stdout.buffer.flush()
        uid = deployment["api_principal"]["host_uid"]
        gid = deployment["api_principal"]["host_gid"]
        environment = _environment(uid, home=prepared["account_home"]) | {
            "_CONTAINERS_USERNS_CONFIGURED": "done",
            "_CONTAINERS_ROOTLESS_UID": str(uid),
            "_CONTAINERS_ROOTLESS_GID": str(gid),
        }
        os.execve(binary, _engine_argv(), environment)  # noqa: S606 - fixed pinned ELF FD only
    finally:
        os.close(binary)


def _engine_inspect(deployment: dict[str, Any], budget: _Budget) -> bytes:  # noqa: PLR0915 - exact owned child and proof validation
    """Keep the original host observer separate from the typed engine child."""
    prepared = _engine_prepare(deployment, budget)
    keeperfd = _engine_pidfd(prepared["keeper"]["pid"])
    deadline = min(budget.deadline, time.monotonic() + _ENGINE_SECONDS)
    request = {
        "schema_version": 1,
        "remaining_seconds": deadline - time.monotonic(),
        "maximum_files": budget.maximum_files - budget.files,
        "maximum_bytes": budget.maximum_bytes - budget.bytes,
    }
    uid = deployment["api_principal"]["host_uid"]
    body = bytearray()
    try:
        with subprocess.Popen(  # noqa: S603 - fixed protected child, never a request selector
            [OBSERVER, "observe-engine"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=_environment(uid, home=prepared["account_home"]),
            cwd="/",
        ) as process:
            try:
                _need(process.stdin is not None and process.stdout is not None)
                child_start = _stat_identity(
                    _read(Path(f"/proc/{process.pid}/stat"), budget, maximum=MAX_PROC), process.pid
                )
                incoming = cast("IO[bytes]", process.stdin)
                incoming.write(json.dumps(request, separators=(",", ":")).encode())
                incoming.close()
                output = cast("IO[bytes]", process.stdout)
                with selectors.DefaultSelector() as selector:
                    selector.register(output, selectors.EVENT_READ)
                    while True:
                        remaining = deadline - time.monotonic()
                        _need(remaining > 0 and selector.select(remaining))
                        part = os.read(
                            output.fileno(),
                            min(65536, MAX_COMMAND + _ENGINE_PREAMBLE_MAX + 1 - len(body)),
                        )
                        if not part:
                            break
                        budget.consume(size=len(part), files=0)
                        body.extend(part)
                        _need(len(body) <= MAX_COMMAND + _ENGINE_PREAMBLE_MAX)
                _need(process.wait(timeout=max(0.001, deadline - time.monotonic())) == 0)
                _need(time.monotonic() < deadline)
            except BaseException:
                if process.stdin is not None:
                    process.stdin.close()
                if process.poll() is None:
                    process.kill()
                process.wait()
                raise
        head, separator, raw = bytes(body).partition(b"\n")
        _need(separator and len(head) <= _ENGINE_PREAMBLE_MAX and 0 < len(raw) <= MAX_COMMAND)
        value = _json(head)
        _need(
            set(value)
            == {"schema_version", "deployment_sha256", "process", "prepared", "entered", "work"}
        )
        _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
        _need(
            value["deployment_sha256"]
            == hashlib.sha256(
                _read(DEPLOYMENT, budget, maximum=MAX_READ, protected=True)
            ).hexdigest()
        )
        _need(
            set(value["process"]) == {"pid", "start_ticks"}
            and type(value["process"]["pid"]) is int
            and value["process"]["pid"] == process.pid
        )
        _need(
            type(value["process"]["start_ticks"]) is int
            and value["process"]["start_ticks"] == child_start
        )
        _need(
            json.dumps(value["prepared"], sort_keys=True, separators=(",", ":"), allow_nan=False)
            == json.dumps(prepared, sort_keys=True, separators=(",", ":"), allow_nan=False)
        )
        work = value["work"]
        _need(type(work) is dict and set(work) == {"files", "bytes"})
        _need(all(type(number) is int and number >= 0 for number in work.values()))
        budget.consume(files=work["files"], size=work["bytes"])
        entered = value["entered"]
        _need(
            set(entered) == {"namespaces", "capabilities", "securebits", "mount_transitions_denied"}
        )
        _need(
            type(entered["securebits"]) is int
            and entered["securebits"] == _ENGINE_SECUREBITS
            and entered["mount_transitions_denied"] is True
        )
        expected_namespaces = prepared["namespaces"] | {"user": prepared["keeper"]["user_inode"]}
        _need(
            type(entered["namespaces"]) is dict
            and all(type(number) is int for number in entered["namespaces"].values())
            and entered["namespaces"] == expected_namespaces
        )
        state = entered["capabilities"]
        expected = {
            "CapEff": _ENGINE_RETAINED_MASK,
            "CapPrm": _ENGINE_RETAINED_MASK,
            "CapBnd": _ENGINE_RETAINED_MASK,
            "CapInh": 0,
            "CapAmb": 0,
            "NoNewPrivs": 1,
            "Seccomp": 2,
            "Seccomp_filters": prepared["seccomp_filters"],
        }
        _need(state == expected and all(type(number) is int for number in state.values()))
        _engine_live(keeperfd)
        _need(_engine_prepare(deployment, budget) == prepared)
        budget.remaining()
        return raw
    finally:
        os.close(keeperfd)


def _show(
    profile: str, uid: int, budget: _Budget, *, home: str = _DEFAULT_ACCOUNT_HOME
) -> dict[str, str]:
    expected = _NATIVE_HARDENING if profile == "native" else _ROOTLESS_MANAGER
    properties = {*_BASE_PROPERTIES, *expected}
    if profile == "native":
        properties.update({"SystemCallArchitectures", "RestrictAddressFamilies", "ReadWritePaths"})
    body = _command(
        [
            "/usr/bin/systemctl",
            "--system" if profile == "native" else "--user",
            "show",
            API_UNIT,
            "--no-pager",
            "--property=" + ",".join(sorted(properties)),
        ],
        budget,
        uid=0 if profile == "native" else uid,
        home=home,
    )
    result = {}
    for line in body.decode("utf-8").splitlines():
        key, separator, value = line.partition("=")
        _need(separator and key not in result)
        result[key] = value
    _need(set(result) == properties)
    _need(result["Id"] == API_UNIT and result["LoadState"] == "loaded")
    _need(result["ActiveState"] == "active" and result["SubState"] == "running")
    _need(result["MainPID"].isdigit() and int(result["MainPID"]) > 1)
    _need(_HEX32.fullmatch(result["InvocationID"]) is not None)
    _need(result["ControlGroup"].startswith("/") and ".." not in result["ControlGroup"].split("/"))
    _need(not result["DropInPaths"])
    _need(all(result[key] == value for key, value in expected.items()))
    if profile == "native":
        _need(set(result["RestrictAddressFamilies"].split()) == {"AF_UNIX", "AF_INET", "AF_INET6"})
        _need(result["SystemCallArchitectures"].split() == ["native"])
        _need(result["ReadWritePaths"].split() == ["/srv/hfcache"])
    return result


def _stat_identity(body: bytes, pid: int) -> int:
    _need(body.startswith(f"{pid} (".encode()) and b") " in body)
    fields = body.rpartition(b") ")[2].split()
    _need(len(fields) >= _STAT_FIELDS and fields[0] not in {b"Z", b"X", b"x"})
    value = int(fields[19])
    _need(value > 0)
    return value


def _maps(body: bytes) -> list[list[int]]:
    rows = [[int(field) for field in line.split()] for line in body.splitlines()]
    _need(1 <= len(rows) <= _MAX_MAPS)
    _need(all(len(row) == _MAP_FIELDS and min(row) >= 0 and row[2] > 0 for row in rows))
    for offset in (0, 1):
        ordered = sorted(rows, key=lambda row: row[offset])
        _need(all(row[offset] + row[2] <= 2**32 for row in ordered))
        _need(
            all(first[offset] + first[2] <= second[offset] for first, second in pairwise(ordered))
        )
    return rows


def _mapped(rows: list[list[int]], inside: int) -> int:
    matches = [
        outer + inside - inner for inner, outer, count in rows if inner <= inside < inner + count
    ]
    _need(len(matches) == 1)
    return matches[0]


def _process(pid: int, budget: _Budget, *, namespaces: bool = True) -> dict[str, Any]:
    _need(type(pid) is int and pid > 1)
    base = Path(f"/proc/{pid}")
    start = _stat_identity(_read(base / "stat", budget, maximum=MAX_PROC), pid)
    values = {}
    for line in _read(base / "status", budget, maximum=MAX_PROC).decode().splitlines():
        key, separator, value = line.partition(":")
        _need(separator and key not in values)
        values[key] = value.strip()
    required = {
        "Uid",
        "Gid",
        "NSpid",
        "NoNewPrivs",
        "CapEff",
        "CapBnd",
        "CapPrm",
        "CapAmb",
        "Seccomp",
    }
    _need(required <= set(values))
    credentials = {
        key: [int(item) for item in values[key].split()] for key in ("Uid", "Gid", "NSpid")
    }
    _need(len(credentials["Uid"]) == len(credentials["Gid"]) == _CREDENTIAL_FIELDS)
    namespace_values = {}
    for name in _NAMESPACES if namespaces else ():
        budget.consume()
        raw = os.readlink(base / "ns" / name)  # noqa: PTH115 - preserve exact kernel namespace grammar
        match = _NAMESPACE.fullmatch(raw)
        _need(match is not None and raw.startswith(name + ":["))
        namespace_values[name] = int(cast("re.Match[str]", match)[1])
    cgroups = _read(base / "cgroup", budget, maximum=4096).decode().splitlines()
    _need(len(cgroups) == 1 and cgroups[0].startswith("0::/"))
    cgroup = cgroups[0][3:]
    _need(".." not in cgroup.split("/"))
    argv_body = _read(base / "cmdline", budget, maximum=MAX_PROC)
    _need(argv_body.endswith(b"\0"))
    argv = [item.decode("utf-8") for item in argv_body[:-1].split(b"\0")]
    uid_map = _maps(_read(base / "uid_map", budget, maximum=4096))
    gid_map = _maps(_read(base / "gid_map", budget, maximum=4096))
    _need(_stat_identity(_read(base / "stat", budget, maximum=MAX_PROC), pid) == start)
    return {
        "pid": pid,
        "start_ticks": start,
        "credentials": credentials,
        "security": {key: values[key] for key in required - {"Uid", "Gid", "NSpid"}},
        "namespaces": namespace_values,
        "cgroup": cgroup,
        "argv": argv,
        "uid_map": uid_map,
        "gid_map": gid_map,
    }


def _api_security(process: dict[str, Any], uid: int, gid: int) -> None:
    _need(process["credentials"]["Uid"] == [uid] * 4)
    _need(process["credentials"]["Gid"] == [gid] * 4)
    _need(process["security"]["NoNewPrivs"] == "1" and process["security"]["Seccomp"] == "2")
    _need(
        all(
            int(process["security"][name], 16) == 0
            for name in ("CapEff", "CapBnd", "CapPrm", "CapAmb")
        )
    )


def _selected(deployment: dict[str, Any]) -> Path:
    release = deployment["release"]
    version = release["version"]
    _need(type(version) is str and _VERSION.fullmatch(version) is not None)
    _need(release["selector_target"] == "releases/" + version)
    return PREFIX / "releases" / version


def _indexed(selected: Path, relative: str, deployment: dict[str, Any], budget: _Budget) -> bytes:
    record = deployment["authority_files"][relative]
    body = _read(selected / relative, budget, maximum=MAX_READ, protected=True)
    info = (selected / relative).lstat()
    _need(hashlib.sha256(body).hexdigest() == record["sha256"] and len(body) == record["bytes"])
    _need(stat.S_IMODE(info.st_mode) == record["mode"])
    return body


def _manager_source(manager: dict[str, str], deployment: dict[str, Any], budget: _Budget) -> None:
    profile = deployment["profile"]
    relative = (
        "packaging/systemd/hfcache-api.service"
        if profile == "native"
        else "rendered/hfcache-api.service"
    )
    selected = _selected(deployment)
    fixed = (
        "/etc/systemd/system/hfcache-api.service"
        if profile == "native"
        else "/etc/systemd/user/hfcache-api.service"
    )
    _need(
        manager["FragmentPath"]
        in {fixed, str(PREFIX / "current" / relative), str(selected / relative)}
    )
    body = _indexed(selected, relative, deployment, budget)
    _need(hashlib.sha256(body).hexdigest() == deployment["bindings"]["api_service"])


def _native_process(
    manager: dict[str, str], deployment: dict[str, Any], budget: _Budget
) -> dict[str, Any]:
    uid, gid = deployment["api_principal"]["host_uid"], deployment["api_principal"]["host_gid"]
    _need(manager["User"] in {"hfcache", str(uid)} and manager["Group"] in {"hfcache", str(gid)})
    pid = int(manager["MainPID"])
    # Root without CAP_SYS_PTRACE cannot dereference another UID's namespace
    # links. Native identity instead binds the root-observed manager/cgroup and
    # original live socket object; no namespace access fallback is attempted.
    process = _process(pid, budget, namespaces=False)
    _api_security(process, uid, gid)
    _need(process["cgroup"] == manager["ControlGroup"])
    _need(process["credentials"]["NSpid"] == [pid])
    _need(_mapped(process["uid_map"], uid) == uid and _mapped(process["gid_map"], gid) == gid)
    selected = _selected(deployment)
    entry_body = _indexed(selected, ".venv/bin/hfcache", deployment, budget)
    shebang = entry_body.splitlines()[0].decode()
    _need(shebang.startswith("#!") and " " not in shebang[2:])
    interpreter = shebang[2:]
    evidence = deployment["profile_evidence"]
    # The authority snapshot authenticates the indexed shebang and these fixed
    # optional aliases to the same protected managed interpreter. uv's actual
    # console script uses python3; do not substitute an arbitrary executable.
    virtual_names = ("python", "python3", "python3.14")
    _need(
        interpreter
        in {
            *(str(selected / ".venv/bin" / name) for name in virtual_names),
            *(str(PREFIX / "current/.venv/bin" / name) for name in virtual_names),
            str(PREFIX / "python" / evidence["python_target_relative"]),
        }
    )
    tail = ["serve", "--server-config", "/etc/hfcache/server.toml"]
    entries = [str(selected / ".venv/bin/hfcache"), str(PREFIX / "current/.venv/bin/hfcache")]
    _need(
        any(process["argv"] in ([entry, *tail], [interpreter, entry, *tail]) for entry in entries)
    )
    _need(
        any(
            manager["ExecStart"].startswith(
                "{ path="
                + entry
                + " ; argv[]="
                + " ".join([entry, *tail])
                + " ; ignore_errors=no ;"
            )
            for entry in entries
        )
    )
    _need(manager["ExecStart"].count("{ path=") == 1 and manager["ExecStart"].endswith("}"))
    return process


def _cap_drop(value: object) -> bool:
    return (
        type(value) is list
        and all(type(item) is str for item in value)
        and (
            value == ["ALL"]
            or (len(value) == len(_EXPANDED_CAP_DROP) and set(value) == _EXPANDED_CAP_DROP)
        )
    )


def _expected_container(
    manager: dict[str, str], deployment: dict[str, Any], budget: _Budget
) -> list[str]:
    """Execute only authenticated installed launcher code, as its ordinary owner."""
    selected = _selected(deployment)
    source = _indexed(selected, "scripts/container-service.py", deployment, budget)
    _need(hashlib.sha256(source).hexdigest() == deployment["bindings"]["container_launcher"])
    module = types.ModuleType("_hfcache_peer_indexed_launcher")
    module.__file__ = str(selected / "scripts/container-service.py")
    exec(compile(source, module.__file__, "exec"), module.__dict__)  # noqa: S102 - digest-verified selected code, unprivileged observer
    profile = _json(_indexed(selected, "rendered/runtime.json", deployment, budget))
    principal = deployment["api_principal"]
    _need(
        profile["service_uid"] == principal["host_uid"]
        and profile["service_gid"] == principal["host_gid"]
    )
    _need(profile["app_image"] == "sha256:" + deployment["profile_evidence"]["app_image_sha256"])
    projection = _helper_projection(deployment, budget)
    argv = module.command(
        profile, "api", invocation_id=manager["InvocationID"], helper_projection=projection
    )
    _need(type(argv) is list and all(type(item) is str for item in argv))
    _need(argv[:3] == ["/usr/bin/podman", "--remote=false", "run"])
    return argv


def _helper_projection(deployment: dict[str, Any], budget: _Budget) -> dict[str, Any]:
    parent = Path(HELPER_PARENT).lstat()
    gid = deployment["api_principal"]["host_gid"]
    _need(
        stat.S_ISDIR(parent.st_mode)
        and parent.st_uid == 0
        and parent.st_gid == gid
        and stat.S_IMODE(parent.st_mode) == _PARENT_MODE
    )
    binding_path = Path(HELPER_PARENT) / "binding.json"
    runtime = _json(_read(binding_path, budget, maximum=4096, protected=True))
    info = binding_path.lstat()
    _need(info.st_gid == gid and stat.S_IMODE(info.st_mode) == _BINDING_MODE)
    _need(
        set(runtime)
        == {
            "schema_version",
            "boot_id",
            "helper_generation",
            "deployment_sha256",
            "policy_sha256",
            "parent",
            "helper",
        }
    )
    _need(type(runtime["schema_version"]) is int and runtime["schema_version"] == 1)
    deployment_body = _read(DEPLOYMENT, budget, maximum=MAX_READ, protected=True)
    digest = hashlib.sha256(deployment_body).hexdigest()
    _need(_json(deployment_body) == deployment and runtime["deployment_sha256"] == digest)
    boot = _read(Path("/proc/sys/kernel/random/boot_id"), budget, maximum=128).decode().strip()
    _need(str(uuid.UUID(boot)) == boot and runtime["boot_id"] == boot)
    _need(
        runtime["parent"]
        == {"device": parent.st_dev, "inode": parent.st_ino, "uid": 0, "gid": gid, "mode": 0o750}
    )
    _need(
        type(runtime["helper_generation"]) is str
        and _HEX32.fullmatch(runtime["helper_generation"]) is not None
    )
    _need(
        type(runtime["policy_sha256"]) is str
        and _HEX64.fullmatch(runtime["policy_sha256"]) is not None
    )
    helper = runtime["helper"]
    _need(type(helper) is dict and set(helper) == {"pid", "start_ticks", "uid", "gid"})
    _need(all(type(item) is int for item in helper.values()))
    _need(helper["pid"] > 1 and helper["start_ticks"] > 0 and helper["uid"] == helper["gid"] == 0)
    return {
        "schema_version": 1,
        "profile": "rootless",
        "deployment_sha256": digest,
        "boot_id": boot,
        "parent": {
            "device": parent.st_dev,
            "inode": parent.st_ino,
            "uid": 65534,
            "gid": 981,
            "mode": 0o750,
        },
        "peer": {"pid": 0, "uid": 65534, "gid": 65534},
    }


def _container_binds(info: dict[str, Any], expected: list[str]) -> None:
    requested = {}
    secrets = set()
    for index, value in enumerate(expected):
        if value == "--volume":
            source, target, options = expected[index + 1].split(":")
            _need(target not in requested and options.split(",")[0] in {"ro", "rw"})
            requested[target] = (source, options.split(",")[0] == "rw")
        elif value == "--secret":
            fields = expected[index + 1].split(",")
            target = [
                field.removeprefix("target=") for field in fields if field.startswith("target=")
            ]
            _need(len(target) == 1 and "/" not in target[0])
            secrets.add("/run/secrets/" + target[0])
    _need(requested.get(HELPER_PARENT) == (HELPER_PARENT, False))
    mounts = info["Mounts"]
    _need(type(mounts) is list and len(mounts) <= _MAX_MOUNTS)
    observed = set()
    for mount in mounts:
        _need(type(mount) is dict and type(mount.get("RW")) is bool)
        target, kind = mount["Destination"], mount["Type"]
        _need(type(target) is str and target not in observed)
        observed.add(target)
        if target in requested:
            _need(kind == "bind" and (mount["Source"], mount["RW"]) == requested[target])
        elif target in secrets:
            _need(kind == "bind" and not mount["RW"])
        else:
            _need(kind == "tmpfs" and target == "/tmp")  # noqa: S108 - exact original private tmpfs
    _need(set(requested) <= observed)


def _helper_mount(pid: int, budget: _Budget) -> dict[str, Any]:
    rows = []
    for line in (
        _read(Path(f"/proc/{pid}/mountinfo"), budget, maximum=MAX_READ).decode().splitlines()
    ):
        before, separator, after = line.partition(" - ")
        fields, trailing = before.split(), after.split()
        _need(separator and len(fields) >= _MOUNT_FIELDS and len(trailing) >= _MOUNT_TRAILING)
        if fields[4] == HELPER_PARENT:
            _need("ro" in fields[5].split(",") and "rw" not in fields[5].split(","))
            _need(trailing[0] in {"tmpfs", "xfs", "ext4", "btrfs"})
            rows.append(
                {
                    "device": fields[2],
                    "root": fields[3],
                    "mountpoint": fields[4],
                    "filesystem": trailing[0],
                }
            )
    _need(len(rows) == 1)
    host = Path(HELPER_PARENT).lstat()
    _need(
        stat.S_ISDIR(host.st_mode)
        and host.st_uid == 0
        and stat.S_IMODE(host.st_mode) == _PARENT_MODE
    )
    _need(rows[0]["device"] == f"{os.major(host.st_dev)}:{os.minor(host.st_dev)}")
    return {
        "kernel_mount": rows[0],
        "parent_device": host.st_dev,
        "parent_inode": host.st_ino,
        "parent_gid": host.st_gid,
    }


def _container(
    manager: dict[str, str], deployment: dict[str, Any], budget: _Budget
) -> tuple[dict[str, Any], dict[str, Any]]:
    principal = deployment["api_principal"]
    uid, gid = principal["host_uid"], principal["host_gid"]
    raw = _engine_inspect(deployment, budget)
    values = json.loads(raw.decode("utf-8"))
    _need(type(values) is list and len(values) == 1 and type(values[0]) is dict)
    info = values[0]
    _need(type(info["Id"]) is str and _HEX64.fullmatch(info["Id"]) is not None)
    _need(info["Name"] in {API_CONTAINER, "/" + API_CONTAINER})
    image = deployment["profile_evidence"]["app_image_sha256"]
    _need(info["Image"] in {image, "sha256:" + image})
    state, config, host = info["State"], info["Config"], info["HostConfig"]
    _need(state["Running"] is True and state["Status"] == "running" and state["Paused"] is False)
    _need(type(state["Pid"]) is int and state["Pid"] > 1)
    _need(
        config["Labels"].get("io.hfcache.stack") == "rootless"
        and config["Labels"].get("io.hfcache.role") == "api"
    )
    _need(
        config["User"] == "981:981"
        and host["ReadonlyRootfs"] is True
        and host["Privileged"] is False
    )
    _need(host["CapAdd"] == [] and _cap_drop(host["CapDrop"]))
    _need(host["NetworkMode"] == "pasta" and host["PortBindings"] in ({}, None))
    _need(type(host["UsernsMode"]) is str and len(host["UsernsMode"]) <= _MAX_TEXT)
    options = host["SecurityOpt"]
    _need(
        type(options) is list
        and len(options) == 1
        and options[0] in {"no-new-privileges", "no-new-privileges=true"}
    )
    expected = _expected_container(manager, deployment, budget)
    _need(config["CreateCommand"] == expected)
    environment = config["Env"]
    _need(type(environment) is list and all(type(item) is str for item in environment))
    for flag in expected:
        if flag.startswith("--env="):
            assignment = flag.removeprefix("--env=")
            name = assignment.partition("=")[0]
            _need([item for item in environment if item.startswith(name + "=")] == [assignment])
    _container_binds(info, expected)
    manager_process = _process(int(manager["MainPID"]), budget)
    _need(
        manager_process["argv"] == expected and manager_process["cgroup"] == manager["ControlGroup"]
    )
    _need(
        manager_process["credentials"]["Uid"] == [uid] * 4
        and manager_process["credentials"]["Gid"] == [gid] * 4
    )
    process = _process(state["Pid"], budget)
    _api_security(process, uid, gid)
    image_position = expected.index("sha256:" + image)
    launched = expected[image_position + 1 :]
    _need(launched[:2] == ["/opt/hfcache/.venv/bin/hfcache", "serve"])
    _need(process["argv"] in (launched, ["/opt/hfcache/.venv/bin/python", *launched]))
    _need(process["pid"] != int(manager["MainPID"]))
    _need(
        process["credentials"]["NSpid"][0] == process["pid"]
        and process["credentials"]["NSpid"][-1] == 1
    )
    _need(_mapped(process["uid_map"], 981) == uid and _mapped(process["gid_map"], 981) == gid)
    _need(_mapped(process["uid_map"], 0) != uid and _mapped(process["gid_map"], 0) != gid)
    scope = "/libpod-" + info["Id"] + ".scope"
    _need(process["cgroup"].endswith((scope, scope + "/container")))
    for name in ("mnt", "pid", "user", "net", "ipc", "uts"):
        _need(
            str((Path("/proc/self/ns") / name).readlink())
            != f"{name}:[{process['namespaces'][name]}]"
        )
    _need(
        manager["ExecStart"].startswith(
            "{ path=/usr/local/libexec/hfcache-container-service ; "
            "argv[]=/usr/local/libexec/hfcache-container-service api ; ignore_errors=no ;"
        )
    )
    _need(manager["ExecStart"].count("{ path=") == 1 and manager["ExecStart"].endswith("}"))
    mount = _helper_mount(process["pid"], budget)
    _need(mount["parent_gid"] == gid)
    return process, {
        "cid": info["Id"],
        "image": info["Image"],
        "userns_mode": host["UsernsMode"],
        "manager_start_ticks": manager_process["start_ticks"],
        "manager_cgroup": manager_process["cgroup"],
        "create_argv_sha256": hashlib.sha256(
            json.dumps(expected, separators=(",", ":")).encode()
        ).hexdigest(),
        "helper_mount": mount,
    }


@dataclass(frozen=True)
class PeerProof:
    deployment_sha256: str
    profile: str
    pid: int
    start_ticks: int
    _facts: bytes


def authenticate(
    snapshot: AuthoritySnapshot, peer: LivePeer, *, remaining_seconds: float
) -> PeerProof:
    """Compare fixed-role facts to the socket's live original process object."""
    try:
        peer.check()
        uid, gid = snapshot.api_principal
        _need(
            (peer.credentials.uid, peer.credentials.gid) == (uid, gid) and peer.credentials.pid > 1
        )
        if snapshot.profile == "rootless":
            home = _account_home(snapshot.deployment)
        else:
            home = _DEFAULT_ACCOUNT_HOME
            account = pwd.getpwnam("hfcache")
            _need((account.pw_uid, account.pw_gid, account.pw_dir) == (uid, gid, home))
        budget = snapshot.budget
        available = min(
            remaining_seconds,
            MAX_OBSERVER_SECONDS,
            (budget.deadline_ns - time.monotonic_ns()) / 1e9,
        )
        _need(available > 0)
        request = {
            "schema_version": 1,
            "remaining_seconds": available,
            "maximum_files": budget.maximum_files - budget.files,
            "maximum_bytes": budget.maximum_bytes - budget.bytes,
        }
        body = _observe_as_account(request, uid, gid, profile=snapshot.profile, home=home)
        value = _json(body)
        _need(
            set(value)
            == {
                "schema_version",
                "deployment_sha256",
                "profile",
                "process",
                "manager",
                "container",
                "work",
            }
        )
        _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
        _need(
            value["deployment_sha256"] == snapshot.deployment_sha256
            and value["profile"] == snapshot.profile
        )
        work = value.pop("work")
        _need(
            set(work) == {"files", "bytes"}
            and all(type(number) is int and number >= 0 for number in work.values())
        )
        budget.consume(files=work["files"], size=work["bytes"])
        process = value["process"]
        _need(
            process["pid"] == peer.credentials.pid
            and type(process["start_ticks"]) is int
            and process["start_ticks"] > 0
        )
        _api_security(process, uid, gid)
        peer.check()
        if snapshot.profile == "rootless":
            _need(_account_home(snapshot.deployment) == home)
        budget.remaining()
        return PeerProof(
            snapshot.deployment_sha256,
            snapshot.profile,
            peer.credentials.pid,
            process["start_ticks"],
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode(),
        )
    except _CATCH:
        raise PeerError from None


def revalidate(
    proof: PeerProof, snapshot: AuthoritySnapshot, peer: LivePeer, *, remaining_seconds: float
) -> None:
    _need(type(proof) is PeerProof)
    _need(authenticate(snapshot, peer, remaining_seconds=remaining_seconds) == proof)


def _observer_budget(
    request: dict[str, Any], bootstrap_work: dict[str, int] | None, started_at: float | None
) -> _Budget:
    _need(set(request) == {"schema_version", "remaining_seconds", "maximum_files", "maximum_bytes"})
    _need(type(request["schema_version"]) is int and request["schema_version"] == 1)
    seconds = request["remaining_seconds"]
    _need(type(seconds) in (float, int) and 0 < seconds <= MAX_OBSERVER_SECONDS)
    files, size = request["maximum_files"], request["maximum_bytes"]
    _need(
        type(files) is int
        and 0 < files <= _MAX_WORK_FILES
        and type(size) is int
        and 0 < size <= 64 * 1024 * 1024
    )
    start = time.monotonic() if started_at is None else started_at
    _need(type(start) in (float, int) and math.isfinite(start) and 0 <= start <= time.monotonic())
    budget = _Budget(start + seconds, files, size)
    work = {"files": 0, "bytes": 0} if bootstrap_work is None else bootstrap_work
    _need(type(work) is dict and set(work) == {"files", "bytes"})
    _need(all(type(value) is int and value >= 0 for value in work.values()))
    budget.consume(files=work["files"], size=work["bytes"])
    return budget


def observe_peer(
    *, bootstrap_work: dict[str, int] | None = None, started_at: float | None = None
) -> dict[str, Any]:
    """Fixed unprivileged CLI branch; caller stdin never names a role or PID.

    The fixed daemon passes actual four-file bootstrap accounting and the clock
    captured before loading those files. A blocked bootstrap cannot be preempted
    by a timer not installed yet; its parent retains actual ownership on timeout.
    """
    request = _json(sys.stdin.buffer.read(4097))
    budget = _observer_budget(request, bootstrap_work, started_at)

    def expired(_signal: int, _frame: object) -> None:
        raise PeerError

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, budget.remaining())
    try:
        before = _read(DEPLOYMENT, budget, maximum=MAX_READ, protected=True)
        deployment = _json(before)
        _need(type(deployment["schema_version"]) is int and deployment["schema_version"] == 1)
        profile = deployment["profile"]
        _need(profile in {"native", "rootless"})
        uid, gid = deployment["api_principal"]["host_uid"], deployment["api_principal"]["host_gid"]
        _need(type(uid) is int and type(gid) is int and uid > 0 and gid > 0)
        observer_uid, observer_gid = (0, 0) if profile == "native" else (uid, gid)
        _need(
            os.getuid() == os.geteuid() == observer_uid
            and os.getgid() == os.getegid() == observer_gid
            and os.getgroups() == []
        )
        home = _account_home(deployment) if profile == "rootless" else _DEFAULT_ACCOUNT_HOME
        manager = _show(profile, uid, budget, home=home)
        _manager_source(manager, deployment, budget)
        if profile == "native":
            process, container = _native_process(manager, deployment, budget), None
        else:
            process, container = _container(manager, deployment, budget)
        _need(_show(profile, uid, budget, home=home) == manager)
        _need(_process(process["pid"], budget, namespaces=profile == "rootless") == process)
        _need(_read(DEPLOYMENT, budget, maximum=MAX_READ, protected=True) == before)
        if profile == "rootless":
            _need(_account_home(deployment) == home)
        budget.remaining()
        # An unrecognized argv is never serialized. The exact known argv is
        # represented only by its digest after all fixed-command checks pass.
        process["argv_sha256"] = hashlib.sha256(
            json.dumps(process.pop("argv"), separators=(",", ":")).encode()
        ).hexdigest()
        result = {
            "schema_version": 1,
            "deployment_sha256": hashlib.sha256(before).hexdigest(),
            "profile": profile,
            "process": process,
            "manager": manager,
            "container": container,
            "work": {"files": budget.files, "bytes": budget.bytes},
        }
        _need(len(json.dumps(result).encode()) <= MAX_OUTPUT)
    except _CATCH:
        raise PeerError from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    return result


def _drain_observer(
    process: subprocess.Popen[bytes], input_stream: IO[bytes], output: IO[bytes]
) -> None:
    """Discard an exact owned observer's output before its exceptional reap."""

    def close_channel(stream: IO[bytes]) -> None:
        while True:
            try:
                stream.close()
            except (InterruptedError, KeyboardInterrupt):
                continue
            except (OSError, ValueError):
                return
            else:
                return

    close_channel(input_stream)
    # A failed selector/read must not turn wait() into a full-pipe deadlock.
    # Read bounded chunks through actual EOF independently of that failed path.
    while True:
        try:
            if not output.read(65536):
                break
        except (InterruptedError, KeyboardInterrupt):
            continue
        except (OSError, ValueError):
            # An unusable owned reader cannot drain. Closing it lets a writer
            # observe the broken pipe before its actual reap.
            close_channel(output)
            break
    while True:
        try:
            process.wait()
        except (InterruptedError, KeyboardInterrupt):
            continue
        else:
            return


def _observe_as_account(
    request: dict[str, Any],
    uid: int,
    gid: int,
    *,
    profile: str,
    home: str = _DEFAULT_ACCOUNT_HOME,
) -> bytes:
    """A late observer retains this worker's slot until its actual normal reap."""
    _need(profile in {"native", "rootless"})
    observer_uid, observer_gid = (0, 0) if profile == "native" else (uid, gid)
    deadline = time.monotonic() + request["remaining_seconds"]
    body = bytearray()
    late = False
    with subprocess.Popen(  # noqa: S603 - protected fixed CLI, independently indexed account
        [OBSERVER, "observe-peer"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        # The protected entry emits only bounded failure metadata here. Keep it
        # in the helper's operator journal; fixed third-party CLI output remains
        # discarded by the observer's separate command/engine collectors.
        stderr=None,
        env=_environment(observer_uid, home=home),
        cwd="/",
        user=observer_uid,
        group=observer_gid,
        extra_groups=(),
    ) as process:
        _need(process.stdin is not None and process.stdout is not None)
        input_stream, output = cast("IO[bytes]", process.stdin), cast("IO[bytes]", process.stdout)
        try:
            input_stream.write(json.dumps(request, separators=(",", ":")).encode())
            input_stream.close()
            with selectors.DefaultSelector() as selector:
                selector.register(output, selectors.EVENT_READ)
                while True:
                    left = deadline - time.monotonic()
                    if left <= 0:
                        late = True
                    if not selector.select(max(0.001, left) if not late else 0.1):
                        continue
                    part = os.read(output.fileno(), 65536)
                    if not part:
                        break
                    if len(body) + len(part) <= MAX_OUTPUT:
                        body.extend(part)
                    else:
                        late = True
            # No CAP_KILL and no false timeout drain: the child's self-deadline
            # owns its same-UID read CLIs. If the kernel stalls, this job remains
            # owned/nonavailable until the exact child actually exits.
            status = process.wait()
        except BaseException:
            # An interruption before the drainer enters still owns this exact
            # child. Retry its drain/reap while preserving the first refusal.
            while True:
                try:
                    _drain_observer(process, input_stream, output)
                    break
                except BaseException:  # noqa: BLE001, S112 - defer until exact child drains/reaps
                    continue
            raise
    _need(not late and time.monotonic() < deadline and status == 0)
    return bytes(body)
