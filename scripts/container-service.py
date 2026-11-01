#!/usr/bin/python3
"""Fixed rootless container roles and non-killing executor drain.

This host orchestrator imports no application code. Secret values never enter
argv, environment or the protected profile; Podman supplies explicit file mounts.
"""

import hashlib
import json
import os
import re
import selectors
import stat
import subprocess
import sys
import time
import tomllib
import uuid
from pathlib import Path
from typing import Any

RELEASE_ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIRECTORY = RELEASE_ROOT / "rendered"
PROFILE = PROFILE_DIRECTORY / "runtime.json"
PODMAN = "/usr/bin/podman"
ENGINE = [PODMAN, "--remote=false"]
CONTAINER_UID = 981
NAMES = {"api": "hfcache-api", "worker": "hfcache-verification", "caddy": "hfcache-caddy"}
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}")
MAX_PROFILE_BYTES = 16384
MIN_MOUNT_FIELDS = 6
HOST_HELPER_PREFIX = Path("/opt/hfcache")
HOST_HELPER_DEPLOYMENT = Path("/etc/hfcache/host-helper-deployment.json")
HOST_HELPER_PARENT = Path("/run/hfcache-host-helper/api")
HOST_HELPER_BOOT = Path("/proc/sys/kernel/random/boot_id")
HOST_HELPER_OWNER = 0
HOST_HELPER_MAX_INDEX = 1048576
HOST_HELPER_MAX_BINDING = 4096
HOST_HELPER_PARENT_MODE = 0o750
HOST_HELPER_BINDING_MODE = 0o440
HOST_HELPER_OVERFLOW = 65534
HOST_HELPER_ARCHIVE_LOCK = Path("/run/hfcache/hfcache.lock")
HOST_HELPER_ARCHIVE_LOCK_TYPE = "hfcache_host_helper_archive_lock_t"
HOST_HELPER_MAX_CONTEXT = 4096

# Shared protected-host inspection primitives. These fixed paths and bounded
# readers are captured by host_policy; no command exposes inspection authority.
INSPECTION_PREFIX = Path("/opt/hfcache")
INSPECTION_LOCKS = Path("/proc/locks")
INSPECTION_LOCK = Path("/run/hfcache/hfcache.lock")
INSPECTION_OWNER = 0
INSPECTION_BINDINGS = {
    Path("/usr/local/libexec/hfcache-container-service"): "scripts/container-service.py",
    Path("/usr/local/libexec/hfcache-client"): "scripts/hfcache-client",
    Path("/etc/systemd/system/hfcache.target"): "packaging/systemd/hfcache.target",
    Path("/etc/systemd/system/hfcache-containers.service"): "rendered/hfcache-containers.service",
    **{
        Path("/etc/systemd/user") / name: "rendered/" + name
        for name in (
            "hfcache.target",
            "hfcache-api.service",
            "hfcache-caddy.service",
            "hfcache-verification.service",
            "hfcache-verification.socket",
        )
    },
}
INSPECTION_UNITS = (
    "hfcache-sync.service",
    "hfcache-verify.service",
    "hfcache-sync.timer",
    "hfcache-verify.timer",
)
INSPECTION_GUARD = "hfcache-readonly-guard.service"
_INSPECTION_MAX_ACCOUNTING = 1048576
_INSPECTION_MAX_ARTIFACT = 16777216
_INSPECTION_MAX_COMMAND = 16384
_INSPECTION_LOCK_MODE = 0o600
_INSPECTION_METADATA = (
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
_INSPECTION_LOCAL_FS = {"xfs", "ext4", "ext3", "ext2", "btrfs", "tmpfs", "overlay"}
_INSPECTION_UNIT_FILES = {
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


def _inspection_refuse():
    message = "read-only host inspection refused"
    raise ValueError(message)


def _inspection_json(body):
    def nonfinite(_value):
        _inspection_refuse()

    return json.loads(body, object_pairs_hook=profile_pairs, parse_constant=nonfinite)


def _inspection_accounting(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        body = bytearray()
        while len(body) <= _INSPECTION_MAX_ACCOUNTING:
            part = os.read(descriptor, min(65536, _INSPECTION_MAX_ACCOUNTING + 1 - len(body)))
            if not part:
                return bytes(body).decode()
            body.extend(part)
        _inspection_refuse()
    finally:
        os.close(descriptor)


def _inspection_local(path, rows):
    if not path.is_absolute() or ".." in path.parts or Path("/srv") in (path, *path.parents):
        _inspection_refuse()
    matches = [
        (len(where.parts), kind) for where, kind, _, _ in rows if where in (path, *path.parents)
    ]
    deepest = max((depth for depth, _ in matches), default=-1)
    if not matches or any(
        kind not in _INSPECTION_LOCAL_FS for depth, kind in matches if depth == deepest
    ):
        _inspection_refuse()


def _inspection_parent(path, rows, *, owners=None):
    _inspection_local(path, rows)
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in (*path.parent.parts[1:], None):
            info = os.fstat(parent)
            if info.st_uid not in (owners or {0, INSPECTION_OWNER}) or (
                info.st_mode & 0o022 and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)
            ):
                _inspection_refuse()
            if part is not None:
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
                )
                os.close(parent)
                parent = child
    except BaseException:
        os.close(parent)
        raise
    else:
        return parent


def _inspection_read(path, rows, *, maximum):
    parent = _inspection_parent(path, rows)
    descriptor = -1
    try:
        descriptor = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent
        )
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != INSPECTION_OWNER
            or before.st_mode & 0o022
            or before.st_nlink != 1
            or not 0 < before.st_size <= maximum
        ):
            _inspection_refuse()
        body = bytearray()
        while len(body) <= maximum:
            part = os.read(descriptor, min(65536, maximum + 1 - len(body)))
            if not part:
                break
            body.extend(part)
        after = os.fstat(descriptor)
        if len(body) != before.st_size or any(
            getattr(before, key) != getattr(after, key) for key in _INSPECTION_METADATA
        ):
            _inspection_refuse()
        return bytes(body)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def _inspection_verifier(selected, rows, index):
    """Execute only captured, policy-index-authenticated fixed installer code."""
    name = "scripts/install-container-release.py"
    digest = index["files"].get(name)
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        _inspection_refuse()
    body = _inspection_read(selected / name, rows, maximum=_INSPECTION_MAX_ARTIFACT)
    if hashlib.sha256(body).hexdigest() != digest:
        _inspection_refuse()
    namespace: dict[str, Any] = {
        "__file__": str(selected / name),
        "__name__": "hfcache_inspection_verifier",
    }
    # Fixed reviewed installer code is bundled release evidence, never browser
    # text or a selected executable. Captured bytes avoid a second path read.
    exec(compile(body, str(selected / name), "exec"), namespace)  # noqa: S102
    namespace.update(
        PREFIX=INSPECTION_PREFIX,
        OWNER_UID=INSPECTION_OWNER,
        BINDINGS=INSPECTION_BINDINGS,
        mount_rows=lambda: rows,
    )
    return namespace


def _inspection_system_show(unit):  # noqa: PLR0912 - bounded fixed-manager process and strict result validation
    if unit not in {*INSPECTION_UNITS, INSPECTION_GUARD}:
        _inspection_refuse()
    timer = unit in {"hfcache-sync.timer", "hfcache-verify.timer"}
    properties = ["Id", "LoadState", "ActiveState", "SubState", "UnitFileState"]
    if not timer:
        properties.append("MainPID")
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
    with subprocess.Popen(  # noqa: S603 - closed argv, fixed manager and clean environment
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=environment,
        cwd="/",
    ) as process:
        try:
            if process.stdout is None:
                _inspection_refuse()
            deadline = time.monotonic() + 5
            body = bytearray()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        _inspection_refuse()
                    part = os.read(
                        process.stdout.fileno(), min(4096, _INSPECTION_MAX_COMMAND + 1 - len(body))
                    )
                    if not part:
                        break
                    body.extend(part)
                    if len(body) > _INSPECTION_MAX_COMMAND:
                        _inspection_refuse()
            if process.wait(timeout=max(0.001, deadline - time.monotonic())) != 0:
                _inspection_refuse()
        except BaseException:
            if process.poll() is None:
                process.kill()
            process.wait()
            raise
    fields = {}
    for line in bytes(body).decode().splitlines():
        key, separator, value = line.partition("=")
        if not separator or key in fields:
            _inspection_refuse()
        fields[key] = value
    if set(fields) != set(properties) or fields["Id"] != unit:
        _inspection_refuse()
    # Timers expose scheduling state, not a process. Only these exact timers use
    # an internal zero; services and the independent guard require real MainPID.
    if timer:
        fields["MainPID"] = "0"
    if (
        fields["LoadState"] not in {"loaded", "masked", "not-found"}
        or fields["ActiveState"] not in {"active", "inactive", "failed"}
        or not re.fullmatch(r"[0-9]+", fields["MainPID"])
    ):
        _inspection_refuse()
    if fields["UnitFileState"] == "" and fields["LoadState"] == "not-found":
        fields["UnitFileState"] = "not-found"
    if fields["UnitFileState"] not in _INSPECTION_UNIT_FILES:
        _inspection_refuse()
    return fields


def _inspection_guard(rows, release):
    guard = _inspection_system_show(INSPECTION_GUARD)
    pid = int(guard["MainPID"])
    if guard["ActiveState"] in {"inactive", "failed"} and pid == 0:
        return "absent" if guard["LoadState"] == "not-found" else "inactive"
    if (
        guard["LoadState"] != "loaded"
        or guard["ActiveState"] != "active"
        or guard["SubState"] != "running"
        or pid <= 0
    ):
        _inspection_refuse()
    parent = _inspection_parent(
        INSPECTION_LOCK, rows, owners={0, INSPECTION_OWNER, release["service_uid"]}
    )
    try:
        before = os.stat(INSPECTION_LOCK.name, dir_fd=parent, follow_symlinks=False)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != release["service_uid"]
            or before.st_gid != release["service_gid"]
            or stat.S_IMODE(before.st_mode) != _INSPECTION_LOCK_MODE
            or before.st_nlink != 1
        ):
            _inspection_refuse()
        device = (os.major(before.st_dev), os.minor(before.st_dev), before.st_ino)
        matches = 0
        for line in _inspection_accounting(INSPECTION_LOCKS).splitlines():
            fields = line.split()
            if len(fields) != 8 or fields[1:4] != ["FLOCK", "ADVISORY", "WRITE"]:  # noqa: PLR2004
                continue
            parts = fields[5].split(":")
            if (
                len(parts) == 3  # noqa: PLR2004 - kernel major:minor:inode grammar
                and fields[4] == str(pid)
                and fields[6:] == ["0", "EOF"]
                and (int(parts[0], 16), int(parts[1], 16), int(parts[2])) == device
            ):
                matches += 1
        after = os.stat(INSPECTION_LOCK.name, dir_fd=parent, follow_symlinks=False)
        if matches != 1 or any(
            getattr(before, key) != getattr(after, key) for key in _INSPECTION_METADATA
        ):
            _inspection_refuse()
    finally:
        os.close(parent)
    if _inspection_system_show(INSPECTION_GUARD) != guard:
        _inspection_refuse()
    return "held"


def _inspection_archive_mount(rows):
    mounts = [
        (kind, flags)
        for path, kind, flags, _ in rows
        if path == Path("/srv/hfcache") and kind != "autofs"
    ]
    if not mounts:
        return "absent"
    if len(mounts) != 1:
        _inspection_refuse()
    kind, flags = mounts[0]
    if ("ro" in flags) == ("rw" in flags):
        _inspection_refuse()
    if kind in {"nfs", "nfs4"} and "ro" in flags:
        return "nfs-ro"
    if kind in _INSPECTION_LOCAL_FS:
        return "local-ro" if "ro" in flags else "local-rw"
    return _inspection_refuse()


def profile_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            msg = "duplicate container profile field"
            raise ValueError(msg)
        result[key] = value
    return result


def load_profile(path=PROFILE):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != 0
            or info.st_mode & 0o022
            or info.st_nlink != 1
            or not 0 < info.st_size <= MAX_PROFILE_BYTES
        ):
            msg = "unsafe container profile"
            raise ValueError(msg)
        raw = os.read(descriptor, MAX_PROFILE_BYTES + 1)
        after = os.fstat(descriptor)
        if any(
            getattr(after, key) != getattr(info, key)
            for key in (
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
        ):
            msg = "container profile changed"
            raise ValueError(msg)
    finally:
        os.close(descriptor)
    profile = json.loads(raw, object_pairs_hook=profile_pairs)
    if (
        set(profile) != {"schema_version", "service_uid", "service_gid", "app_image", "caddy_image"}
        or type(profile["schema_version"]) is not int
        or profile["schema_version"] != 1
        or any(
            type(profile[key]) is not int or profile[key] < 1
            for key in ("service_uid", "service_gid")
        )
        or any(
            not isinstance(profile[key], str) or not IMAGE_ID.fullmatch(profile[key])
            for key in ("app_image", "caddy_image")
        )
        or (os.geteuid(), os.getegid()) != (profile["service_uid"], profile["service_gid"])
        or os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{profile['service_uid']}")
        != f"/run/user/{profile['service_uid']}"
    ):
        msg = "container profile or service identity mismatch"
        raise ValueError(msg)
    os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{profile['service_uid']}"
    return profile


def secret(name):
    return ["--secret", f"{name},type=mount,target={name},uid=981,gid=981,mode=0400"]


def volume(source, target=None, *, writable=False, shared=False):
    options = "rw" if writable else "ro"
    if shared:
        options += ",z"  # Only reviewed LOCAL paths; never call this for NAS.
    return ["--volume", f"{source}:{target or source}:{options}"]


def _helper_need(value):
    if not value:
        msg = "protected host helper projection refused"
        raise ValueError(msg)


def _helper_object(value, keys):
    _helper_need(type(value) is dict and set(value) == set(keys))
    return value


def _helper_digest(value):
    _helper_need(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value))
    return value


def _helper_uuid(value):
    _helper_need(type(value) is str and str(uuid.UUID(value)) == value)
    return value


def _helper_projection(value):
    _helper_object(
        value, {"schema_version", "profile", "deployment_sha256", "boot_id", "parent", "peer"}
    )
    _helper_need(type(value["schema_version"]) is int and value["schema_version"] == 1)
    _helper_need(value["profile"] == "rootless")
    _helper_digest(value["deployment_sha256"])
    _helper_uuid(value["boot_id"])
    parent = _helper_object(value["parent"], {"device", "inode", "uid", "gid", "mode"})
    _helper_need(all(type(number) is int for number in parent.values()))
    _helper_need(parent["device"] > 0 and parent["inode"] > 0)
    _helper_need(
        (parent["uid"], parent["gid"], parent["mode"])
        == (HOST_HELPER_OVERFLOW, CONTAINER_UID, HOST_HELPER_PARENT_MODE)
    )
    peer = _helper_object(value["peer"], {"pid", "uid", "gid"})
    _helper_need(all(type(number) is int for number in peer.values()))
    _helper_need(peer == {"pid": 0, "uid": HOST_HELPER_OVERFLOW, "gid": HOST_HELPER_OVERFLOW})
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def helper_parent_projection(deployment_sha256, boot_id, device, inode):
    """Pure fixed projection; arguments must come from protected host captures."""
    projection = {
        "schema_version": 1,
        "profile": "rootless",
        "deployment_sha256": deployment_sha256,
        "boot_id": boot_id,
        "parent": {
            "device": device,
            "inode": inode,
            "uid": HOST_HELPER_OVERFLOW,
            "gid": CONTAINER_UID,
            "mode": HOST_HELPER_PARENT_MODE,
        },
        "peer": {"pid": 0, "uid": HOST_HELPER_OVERFLOW, "gid": HOST_HELPER_OVERFLOW},
    }
    _helper_projection(projection)
    return projection


class _HelperProjectionRead:
    """A few fixed no-follow reads; never imports application or policy code."""

    def __init__(self):
        self.parents = {}
        self.leaves = {}

    def parent(self, path, *, archive_owner=None):
        _helper_need(path.is_absolute() and ".." not in path.parts)
        _helper_need(
            archive_owner is None
            or (path == HOST_HELPER_ARCHIVE_LOCK and type(archive_owner) is int)
        )
        owners = {0, HOST_HELPER_OWNER}
        if archive_owner is not None:
            owners.add(archive_owner)
        descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        current = Path("/")
        try:
            for part in (*path.parent.parts[1:], None):
                info = os.fstat(descriptor)
                _helper_need(
                    info.st_uid in owners
                    and (
                        not info.st_mode & 0o022
                        or (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)
                    )
                )
                identity = (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)
                _helper_need(current not in self.parents or self.parents[current] == identity)
                self.parents[current] = identity
                if part is not None:
                    child = os.open(
                        part,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                        dir_fd=descriptor,
                    )
                    os.close(descriptor)
                    descriptor = child
                    current /= part
            return descriptor  # noqa: TRY300 - transfer this pinned descriptor only on success
        except BaseException:
            os.close(descriptor)
            raise

    def read(self, path, maximum, *, mode=None, gid=None, virtual=False):
        _helper_need(not virtual or path == HOST_HELPER_BOOT)
        parent = self.parent(path)
        descriptor = -1
        try:
            descriptor = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent
            )
            before = os.fstat(descriptor)
            _helper_need(
                stat.S_ISREG(before.st_mode)
                and before.st_uid == HOST_HELPER_OWNER
                and before.st_nlink == 1
            )
            _helper_need(not before.st_mode & 0o022 and 0 <= before.st_size <= maximum)
            _helper_need(mode is None or stat.S_IMODE(before.st_mode) == mode)
            _helper_need(gid is None or before.st_gid == gid)
            body = bytearray()
            while len(body) <= maximum:
                part = os.read(descriptor, min(65536, maximum + 1 - len(body)))
                if not part:
                    break
                body.extend(part)
            after = os.fstat(descriptor)
            linked = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            identity = tuple(getattr(before, name) for name in _INSPECTION_METADATA)
            _helper_need(len(body) <= maximum and (virtual or len(body) == before.st_size))
            _helper_need(
                identity
                == tuple(getattr(after, name) for name in _INSPECTION_METADATA)
                == tuple(getattr(linked, name) for name in _INSPECTION_METADATA)
            )
            _helper_need(path not in self.leaves or self.leaves[path] == identity)
            self.leaves[path] = identity
            return bytes(body)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            os.close(parent)

    def revalidate(self):
        for path, expected in self.parents.items():
            info = path.lstat()
            _helper_need(
                (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid) == expected
            )
        for path, expected in self.leaves.items():
            _helper_need(
                tuple(getattr(path.lstat(), name) for name in _INSPECTION_METADATA) == expected
            )


def _host_helper_configuration(profile, capture):
    configuration = tomllib.loads(
        capture.read(PROFILE_DIRECTORY / "server.toml", MAX_PROFILE_BYTES).decode("utf-8")
    )
    helper = configuration.get("host_helper")
    if helper is None:
        return None
    _helper_need(type(helper) is dict and type(helper.get("enabled", False)) is bool)
    if not helper.get("enabled", False):
        _helper_need(set(helper) <= {"enabled"})
        return None
    _helper_need(
        set(helper)
        in (
            {"enabled", "profile", "api_host_gid"},
            {"enabled", "profile", "api_host_gid", "deployment_sha256"},
        )
    )
    _helper_need(
        helper["profile"] == "rootless"
        and type(helper["api_host_gid"]) is int
        and helper["api_host_gid"] == profile["service_gid"]
    )
    if "deployment_sha256" in helper:
        _helper_digest(helper["deployment_sha256"])
    return helper


def host_helper_enabled(profile):
    """Worker reads only the existing protected opt-in, never helper authority."""
    capture = _HelperProjectionRead()
    enabled = _host_helper_configuration(profile, capture) is not None
    capture.revalidate()
    return enabled


def host_helper_archive_lock(profile):
    """Observe only the fixed existing coordination inode and its full context."""
    capture = _HelperProjectionRead()
    parent = capture.parent(HOST_HELPER_ARCHIVE_LOCK, archive_owner=profile["service_uid"])
    try:
        before = os.stat(HOST_HELPER_ARCHIVE_LOCK.name, dir_fd=parent, follow_symlinks=False)
        _helper_need(
            stat.S_ISREG(before.st_mode)
            and (before.st_uid, before.st_gid) == (profile["service_uid"], profile["service_gid"])
            and stat.S_IMODE(before.st_mode) == _INSPECTION_LOCK_MODE
            and before.st_nlink == 1
        )
        context = os.getxattr(HOST_HELPER_ARCHIVE_LOCK, "security.selinux", follow_symlinks=False)
        _helper_need(
            0 < len(context) <= HOST_HELPER_MAX_CONTEXT
            and re.fullmatch(
                rb"[A-Za-z0-9_]+:object_r:" + HOST_HELPER_ARCHIVE_LOCK_TYPE.encode() + rb":s0\0?",
                context,
            )
        )
        after = os.stat(HOST_HELPER_ARCHIVE_LOCK.name, dir_fd=parent, follow_symlinks=False)
        _helper_need(
            tuple(getattr(before, name) for name in _INSPECTION_METADATA)
            == tuple(getattr(after, name) for name in _INSPECTION_METADATA)
        )
        capture.revalidate()
    finally:
        os.close(parent)


def host_helper_projection(profile):  # noqa: PLR0915 - one fixed protected startup authority join
    """Only main's API branch calls this explicit fixed helper opt-in loader."""
    capture = _HelperProjectionRead()
    helper = _host_helper_configuration(profile, capture)
    if helper is None:
        capture.revalidate()
        return None
    raw = capture.read(
        HOST_HELPER_DEPLOYMENT, HOST_HELPER_MAX_INDEX, mode=0o644, gid=HOST_HELPER_OWNER
    )
    deployment = _helper_object(
        _inspection_json(raw),
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
    _helper_need(
        type(deployment["schema_version"]) is int
        and deployment["schema_version"] == 1
        and deployment["profile"] == "rootless"
    )
    _helper_digest(deployment["selinux_installation_sha256"])
    release = _helper_object(deployment["release"], {"version", "selector_target"})
    _helper_need(
        type(release["version"]) is str
        and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", release["version"])
    )
    _helper_need(release["selector_target"] == "releases/" + release["version"])
    _helper_need(HOST_HELPER_PREFIX / release["selector_target"] == RELEASE_ROOT)
    selector = HOST_HELPER_PREFIX / "current"
    selector_parent = capture.parent(selector)
    try:
        before = os.stat(selector.name, dir_fd=selector_parent, follow_symlinks=False)
        _helper_need(stat.S_ISLNK(before.st_mode) and before.st_uid == HOST_HELPER_OWNER)
        _helper_need(
            os.readlink(selector.name, dir_fd=selector_parent) == release["selector_target"]
        )
        selector_identity = tuple(getattr(before, name) for name in _INSPECTION_METADATA)
        after = os.stat(selector.name, dir_fd=selector_parent, follow_symlinks=False)
        _helper_need(
            tuple(getattr(after, name) for name in _INSPECTION_METADATA) == selector_identity
        )
    finally:
        os.close(selector_parent)
    principal = _helper_object(deployment["api_principal"], {"host_uid", "host_gid"})
    _helper_need(all(type(value) is int for value in principal.values()))
    _helper_need(
        principal == {"host_uid": profile["service_uid"], "host_gid": profile["service_gid"]}
    )
    evidence = _helper_object(
        deployment["profile_evidence"],
        {
            "artifact_index_sha256",
            "runtime_profile_sha256",
            "app_image_sha256",
            "caddy_image_sha256",
        },
    )
    for value in evidence.values():
        _helper_digest(value)
    runtime = capture.read(PROFILE_DIRECTORY / "runtime.json", MAX_PROFILE_BYTES)
    _helper_need(
        _inspection_json(runtime) == profile
        and hashlib.sha256(runtime).hexdigest() == evidence["runtime_profile_sha256"]
    )
    _helper_need(
        hashlib.sha256(
            capture.read(RELEASE_ROOT / "artifact-index.json", HOST_HELPER_MAX_INDEX)
        ).hexdigest()
        == evidence["artifact_index_sha256"]
    )
    _helper_need(
        profile["app_image"] == "sha256:" + evidence["app_image_sha256"]
        and profile["caddy_image"] == "sha256:" + evidence["caddy_image_sha256"]
    )
    parent_fd = capture.parent(HOST_HELPER_PARENT / "binding.json")
    try:
        parent = os.fstat(parent_fd)
        _helper_need(
            parent.st_uid == HOST_HELPER_OWNER
            and parent.st_gid == profile["service_gid"]
            and stat.S_IMODE(parent.st_mode) == HOST_HELPER_PARENT_MODE
        )
    finally:
        os.close(parent_fd)
    binding = _helper_object(
        _inspection_json(
            capture.read(
                HOST_HELPER_PARENT / "binding.json",
                HOST_HELPER_MAX_BINDING,
                mode=HOST_HELPER_BINDING_MODE,
                gid=profile["service_gid"],
            )
        ),
        {
            "schema_version",
            "boot_id",
            "helper_generation",
            "deployment_sha256",
            "policy_sha256",
            "parent",
            "helper",
        },
    )
    _helper_need(type(binding["schema_version"]) is int and binding["schema_version"] == 1)
    deployment_sha256 = hashlib.sha256(raw).hexdigest()
    _helper_need(binding["deployment_sha256"] == deployment_sha256)
    if "deployment_sha256" in helper:
        _helper_need(_helper_digest(helper["deployment_sha256"]) == deployment_sha256)
    _helper_digest(binding["policy_sha256"])
    _helper_need(
        type(binding["helper_generation"]) is str
        and re.fullmatch(r"[0-9a-f]{32}", binding["helper_generation"])
    )
    boot_id = _helper_uuid(capture.read(HOST_HELPER_BOOT, 64, virtual=True).decode("ascii").strip())
    _helper_need(binding["boot_id"] == boot_id)
    identity = _helper_object(binding["parent"], {"device", "inode", "uid", "gid", "mode"})
    _helper_need(all(type(number) is int for number in identity.values()))
    _helper_need(
        identity
        == {
            "device": parent.st_dev,
            "inode": parent.st_ino,
            "uid": 0,
            "gid": profile["service_gid"],
            "mode": HOST_HELPER_PARENT_MODE,
        }
    )
    process = _helper_object(binding["helper"], {"pid", "start_ticks", "uid", "gid"})
    _helper_need(
        all(type(number) is int for number in process.values())
        and process["pid"] > 1
        and process["start_ticks"] > 0
        and process["uid"] == process["gid"] == 0
    )
    capture.revalidate()
    _helper_need(
        tuple(getattr(selector.lstat(), name) for name in _INSPECTION_METADATA) == selector_identity
        and selector.readlink().as_posix() == release["selector_target"]
    )
    return helper_parent_projection(deployment_sha256, boot_id, parent.st_dev, parent.st_ino)


def command(  # noqa: PLR0912, PLR0913, PLR0915 - one closed role/mount allowlist
    profile,
    role,
    arguments=(),
    *,
    invocation_id=None,
    helper_projection=None,
    preserve_archive_lock=False,
):
    if role not in {*NAMES, "client"} or (role != "client" and arguments):
        msg = "unknown fixed container role"
        raise ValueError(msg)
    projected_environment = ""
    if helper_projection is not None:
        _helper_need(role == "api")
        projected_environment = _helper_projection(helper_projection)
    _helper_need(
        type(preserve_archive_lock) is bool
        and (not preserve_archive_lock or role in {"api", "worker"})
    )
    preserve_archive_lock = preserve_archive_lock or helper_projection is not None
    argv = [
        *ENGINE,
        "run",
        "--pull=never",
        "--http-proxy=false",
        "--sig-proxy=false",
        "--userns=keep-id:uid=981,gid=981",
        "--user=981:981",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--read-only",
        "--read-only-tmpfs=false",
        "--tmpfs=/tmp:rw,nosuid,nodev,noexec,mode=1777",
        "--pids-limit=512",
        "--label=io.hfcache.stack=rootless",
        f"--label=io.hfcache.role={role}",
    ]
    if role == "client":
        # An observer exiting never stops the API or cancels an admitted job.
        argv += ["--rm", "--network=none"]
    else:
        argv += ["--name", NAMES[role]]
        argv += ["--network=none" if role == "worker" else "--network=pasta"]
    argv += ["--cgroup-conf=memory.high=" + ("536870912" if role == "caddy" else "4294967296")]
    invocation = os.environ.get("INVOCATION_ID", "") if invocation_id is None else invocation_id
    _helper_need(type(invocation) is str)
    if role in {"api", "worker"} and re.fullmatch(r"[0-9a-f]{32}", invocation):
        # Nonsecret actual-unit evidence, never a submitted caller/timer claim.
        argv += ["--env=INVOCATION_ID=" + invocation]
    if role in {"api", "worker", "client"}:
        # Directory bind intentionally observes atomic config replacement.
        argv += volume("/etc/hfcache")
        # Pin release-owned profiles to the same physical tree as this helper.
        # The host targets are regular placeholders, never external symlinks.
        argv += volume(PROFILE_DIRECTORY, "/etc/hfcache/containers")
        if role == "client":
            argv += volume(PROFILE_DIRECTORY / "client.toml", "/etc/hfcache/client.toml")
    if role in {"worker", "client"}:
        for hidden in (
            "/run/credentials",
            "/etc/credstore",
            "/etc/credstore.encrypted",
            "/etc/hfcache/credentials",
        ):
            argv += [f"--tmpfs={hidden}:ro,nosuid,nodev,noexec,mode=000"]
    if role in {"api", "worker"}:
        argv += volume("/srv/hfcache")  # No relabel/chown/copyup option, ever.
        argv += volume("/run/hfcache/hfcache.lock", writable=True, shared=not preserve_archive_lock)
    if role in {"api", "client", "caddy"}:
        argv += volume("/run/hfcache/api", writable=role == "api", shared=True)
    if role in {"api", "worker"}:
        argv += volume("/run/hfcache/verification", writable=role == "worker", shared=True)
    if role == "api":
        if helper_projection is not None:
            argv += volume(HOST_HELPER_PARENT, "/run/hfcache-host-helper/api")
            argv += ["--env=HFCACHE_HOST_HELPER_PARENT=" + projected_environment]
        argv += volume("/run/hfcache/api.lock", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/api", writable=True, shared=True)
        # ADR150: the enabled helper's Hub payload labels must survive Podman.
        argv += volume("/var/lib/hfcache/hf-home", writable=True, shared=helper_projection is None)
        argv += volume("/var/cache/hfcache", writable=True, shared=helper_projection is None)
        argv += [
            "--env=HF_HOME=/var/lib/hfcache/hf-home",
            "--env=HF_XET_CACHE=/var/cache/hfcache/xet",
        ]
        for name in ("hfcache.api", "hfcache.api-reader", "hfcache.mcp-reader", "hf-token"):
            argv += secret(name)
        argv += [
            profile["app_image"],
            "/opt/hfcache/.venv/bin/hfcache",
            "serve",
            "--server-config",
            "/etc/hfcache/containers/server.toml",
            "--hub-token-file",
            "/run/secrets/hf-token",
        ]
    elif role == "worker":
        argv += ["--sdnotify=container"]
        argv += [f"--security-opt=seccomp={PROFILE_DIRECTORY}/worker-seccomp.json"]
        argv += volume("/var/lib/hfcache/verification", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/verification.instance.lock", writable=True, shared=True)
        argv += [
            "--env=HF_HUB_OFFLINE=1",
            "--env=HF_DATASETS_OFFLINE=1",
            "--env=HF_HUB_DISABLE_TELEMETRY=1",
            "--env=HF_HOME=/tmp/hf-home",
            "--env=HF_XET_CACHE=/tmp/xet",
        ]
        argv += [
            profile["app_image"],
            "/opt/hfcache/.venv/bin/python",
            "-m",
            "hfcache.verification_worker",
            "--container-listener",
            "--config",
            "/etc/hfcache/config.toml",
            "--state-directory",
            "/var/lib/hfcache/verification",
            "--socket",
            "/run/hfcache/verification/verification.sock",
            "--api-uid",
            "981",
        ]
    elif role == "caddy":
        argv += ["--publish=0.0.0.0:8443:8443"]
        argv += volume(PROFILE_DIRECTORY / "Caddyfile", "/etc/caddy/Caddyfile")
        argv += volume("/var/lib/hfcache/caddy-data", "/data", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/caddy-config", "/config", writable=True, shared=True)
        argv += secret("hfcache.tls-cert") + secret("hfcache.tls-key")
        argv += [
            "--entrypoint=/usr/bin/caddy",
            profile["caddy_image"],
            "run",
            "--config",
            "/etc/caddy/Caddyfile",
            "--adapter",
            "caddyfile",
        ]
    else:
        argv += secret("hfcache.api")
        argv += [profile["app_image"], "/opt/hfcache/.venv/bin/hfcache", *arguments]
    return argv


def inspect_container(name):
    result = subprocess.run(  # noqa: S603 - fixed local engine and fixed role name
        [*ENGINE, "container", "inspect", name], capture_output=True, check=False, text=True
    )
    if result.returncode:
        # Only Podman's explicit absence code is safe; engine errors are unknown.
        exists = subprocess.run([*ENGINE, "container", "exists", name], check=False)  # noqa: S603
        if exists.returncode == 1:
            return None
        msg = "container state unavailable"
        raise TypeError(msg)
    values = json.loads(result.stdout)
    if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], dict):
        msg = "container state malformed"
        raise RuntimeError(msg)
    return values[0]


def owned_container(profile, role):
    info = inspect_container(NAMES[role])
    if info is None:
        return None
    config, state = info.get("Config"), info.get("State")
    if not isinstance(config, dict) or not isinstance(state, dict):
        msg = "unknown container metadata preserved"
        raise TypeError(msg)
    labels = config.get("Labels")
    if (
        not isinstance(labels, dict)
        or not isinstance(info.get("Id"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", info["Id"])
    ):
        msg = "unknown container identity preserved"
        raise RuntimeError(msg)
    expected = profile["caddy_image" if role == "caddy" else "app_image"]
    observed_image = info.get("Image")
    if isinstance(observed_image, str) and re.fullmatch(r"[0-9a-f]{64}", observed_image):
        observed_image = "sha256:" + observed_image
    if (
        observed_image != expected
        or labels.get("io.hfcache.role") != role
        or labels.get("io.hfcache.stack") != "rootless"
    ):
        msg = "unknown existing container preserved"
        raise RuntimeError(msg)
    if (
        type(state.get("Running")) is not bool
        or type(state.get("Pid")) is not int
        or state["Pid"] < 0
        or (state["Running"] and state["Pid"] == 0)
    ):
        msg = "unknown executor state preserved"
        raise RuntimeError(msg)
    return info


def prepare_start(profile, role):
    info = owned_container(profile, role)
    if info is not None:
        if info["State"]["Running"] or info["State"]["Pid"] != 0:
            msg = "existing executor preserved; drain explicitly"
            raise RuntimeError(msg)
        subprocess.run([*ENGINE, "rm", info["Id"]], check=True)  # noqa: S603


def archive_readonly(table=None):
    """Inspect local kernel mount information, never a live archive pathname."""
    body = Path("/proc/self/mountinfo").read_text() if table is None else table
    matches = []
    for line in body.splitlines():
        left, _, right = line.partition(" - ")
        fields = left.split()
        if len(fields) >= MIN_MOUNT_FIELDS and fields[4] == "/srv/hfcache" and right:
            matches.append((fields[5].split(","), right.split()[0]))
    # autofs plus its mounted NFS tree is expected; only NFS counts here.
    nfs = [(options, kind) for options, kind in matches if kind in {"nfs", "nfs4"}]
    if len(nfs) != 1 or "ro" not in nfs[0][0] or "rw" in nfs[0][0]:
        msg = "read-only NAS mount barrier unavailable"
        raise RuntimeError(msg)


def drain(profile, role):
    info = owned_container(profile, role)
    if info is None:
        return
    if info["State"]["Running"]:
        subprocess.run([*ENGINE, "stop", "--time", "-1", info["Id"]], check=True)  # noqa: S603
    stopped = owned_container(profile, role)
    if stopped is not None:
        if stopped["Id"] != info["Id"]:
            msg = "executor identity changed during drain; replacement preserved"
            raise RuntimeError(msg)
        if stopped["State"]["Running"] or stopped["State"]["Pid"] != 0:
            msg = "executor has not drained"
            raise RuntimeError(msg)
        subprocess.run([*ENGINE, "rm", stopped["Id"]], check=True)  # noqa: S603


def main():
    # Preserve original operation handles after the CLI end-of-options marker.
    help_arguments = sys.argv[1:]
    if "--" in help_arguments:
        help_arguments = help_arguments[: help_arguments.index("--")]
    if any(argument in {"--help", "-h"} for argument in help_arguments):
        print(
            "Usage: /usr/local/libexec/hfcache-container-service "
            "api|worker|caddy|client CLI_ARGS...|stop api|worker|caddy\n"
            "Rootless user-manager launcher; fixed local /usr/bin/podman. "
            "Reads protected rendered/runtime.json from its physical release. "
            "Podman mounts role-specific secrets; worker receives none. "
            "Starts role containers or drains an owned executor without killing. "
            "No engine/executable override; no dry-run. Help reads no profile."
        )
        return 0
    stopping = len(sys.argv) == 3 and sys.argv[1] == "stop" and sys.argv[2] in NAMES  # noqa: PLR2004 - fixed stop grammar
    if not stopping and (
        len(sys.argv) < 2  # noqa: PLR2004 - fixed role grammar
        or sys.argv[1] not in {*NAMES, "client"}
        or (sys.argv[1] != "client" and len(sys.argv) != 2)  # noqa: PLR2004 - fixed role grammar
    ):
        sys.stderr.write("container launcher requires a fixed role; use --help\n")
        return 20
    try:
        profile = load_profile()
        if stopping:
            drain(profile, sys.argv[2])
            return 0
        role = sys.argv[1] if len(sys.argv) > 1 else ""
        projection = host_helper_projection(profile) if role == "api" else None
        preserve_lock = projection is not None or (
            role == "worker" and host_helper_enabled(profile)
        )
        if preserve_lock:
            host_helper_archive_lock(profile)
        argv = command(
            profile,
            role,
            sys.argv[2:],
            invocation_id=os.environ.get("INVOCATION_ID", ""),
            helper_projection=projection,
            preserve_archive_lock=preserve_lock,
        )
        if role in {"api", "worker"}:
            archive_readonly()
        if role != "client":
            prepare_start(profile, role)
        # exec retains the manager's notify proxy; the confined worker owns FD3.
        os.execv(PODMAN, argv)  # noqa: S606
    except Exception:  # noqa: BLE001 - unknown stop errors must never reach fallback termination
        sys.stderr.write("hfcache container boundary refused; retained state requires inspection\n")
        if stopping:
            # Never return into systemd's fallback termination of an unknown job.
            while True:
                time.sleep(30)
        return 20
    return 20


if __name__ == "__main__":
    raise SystemExit(main())
