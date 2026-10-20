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
from pathlib import Path, PurePosixPath

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

# ADR135: this inspection is separate from every container/service role. These
# paths are fixed host policy/accounting, never caller-selected routing.
INSPECTION_PREFIX = Path("/opt/hfcache")
INSPECTION_POLICY = Path("/etc/hfcache/cockpit-policy.json")
INSPECTION_MOUNTS = Path("/proc/1/mountinfo")
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
INSPECTION_ACTIONS = {"archive", "hub", "control", "schedule", "configuration", "observer"}
_INSPECTION_MAX_ACCOUNTING = 1048576
_INSPECTION_MAX_POLICY = 4096
_INSPECTION_MAX_ARTIFACT = 16777216
_INSPECTION_MAX_COMMAND = 16384
_INSPECTION_MAX_FILES = 1000
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
    message = "read-only Cockpit inspection refused"
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


def _inspection_mounts():
    rows = []
    for line in _inspection_accounting(INSPECTION_MOUNTS).splitlines():
        left, separator, right = line.partition(" - ")
        before, after = left.split(), right.split()
        if not separator or len(before) < 6 or len(after) < 3:  # noqa: PLR2004 - mountinfo grammar
            _inspection_refuse()
        raw = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), before[4])
        path = Path(raw)
        if not path.is_absolute() or str(path) != raw or ".." in path.parts:
            _inspection_refuse()
        rows.append((path, after[0], set(before[5].split(",")), set(after[2].split(","))))
    if not rows:
        _inspection_refuse()
    return rows


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


def _inspection_selector(rows):
    parent = _inspection_parent(INSPECTION_PREFIX / "current", rows)
    try:
        info = os.stat("current", dir_fd=parent, follow_symlinks=False)
        target = os.readlink("current", dir_fd=parent)
        if (
            not stat.S_ISLNK(info.st_mode)
            or info.st_uid != INSPECTION_OWNER
            or not re.fullmatch(r"releases/[0-9]+\.[0-9]+\.[0-9]+", target)
        ):
            _inspection_refuse()
        return target, tuple(getattr(info, key) for key in _INSPECTION_METADATA)
    finally:
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
    namespace = {"__file__": str(selected / name), "__name__": "hfcache_inspection_verifier"}
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


def inspect_cockpit():  # noqa: PLR0911, PLR0912 - retain distinct failure stages without partial authority
    """ADR135: permission to submit is distinct from archive writability."""

    def unknown(reason):
        return {"schema_version": 1, "state": "unknown", "reason": reason}

    if os.geteuid() != 0:
        return unknown("privilege-required")
    try:
        rows = _inspection_mounts()
    except Exception:  # noqa: BLE001 - inspection failure never grants authority
        return unknown("facts-unavailable")
    try:
        policy_body = _inspection_read(INSPECTION_POLICY, rows, maximum=_INSPECTION_MAX_POLICY)
        policy = _inspection_json(policy_body)
        if (
            not isinstance(policy, dict)
            or set(policy) != {"schema_version", "source_commit", "index_sha256", "permissions"}
            or type(policy["schema_version"]) is not int
            or policy["schema_version"] != 1
            or not isinstance(policy["source_commit"], str)
            or not re.fullmatch(r"[0-9a-f]{40}", policy["source_commit"])
            or not isinstance(policy["index_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", policy["index_sha256"])
            or not isinstance(policy["permissions"], dict)
            or set(policy["permissions"]) != INSPECTION_ACTIONS
            or any(type(value) is not bool for value in policy["permissions"].values())
        ):
            _inspection_refuse()
    except FileNotFoundError:
        return unknown("policy-missing")
    except Exception:  # noqa: BLE001 - untrusted policy gets no partial permissions
        return unknown("policy-invalid")
    try:
        selector = _inspection_selector(rows)
        selected = INSPECTION_PREFIX / selector[0]
        if selected != RELEASE_ROOT or any(
            where.is_relative_to(selected) and kind not in _INSPECTION_LOCAL_FS
            for where, kind, _, _ in rows
        ):
            _inspection_refuse()
        index_body = _inspection_read(
            selected / "artifact-index.json", rows, maximum=_INSPECTION_MAX_ACCOUNTING
        )
        index = _inspection_json(index_body)
        if (
            hashlib.sha256(index_body).hexdigest() != policy["index_sha256"]
            or not isinstance(index, dict)
            or set(index) != {"schema_version", "files"}
            or type(index["schema_version"]) is not int
            or index["schema_version"] != 1
            or not isinstance(index["files"], dict)
            or not 0 < len(index["files"]) <= _INSPECTION_MAX_FILES
        ):
            _inspection_refuse()
        verifier = _inspection_verifier(selected, rows, index)
        release = verifier["_verify_stage"](selected)
        if (
            release["source_commit"] != policy["source_commit"]
            or release["version"] != PurePosixPath(selector[0]).name
        ):
            _inspection_refuse()
        verifier["_verify_bindings"]()
    except Exception:  # noqa: BLE001 - absent/old/mixed/drifted deployments fail closed
        return unknown("deployment-unverified")
    try:
        guard = _inspection_guard(rows, release)
        mount = _inspection_archive_mount(rows)
        units = {}
        for unit in INSPECTION_UNITS:
            facts = _inspection_system_show(unit)
            units[unit] = {
                "load": facts["LoadState"],
                "active": facts["ActiveState"],
                "unit_file": facts["UnitFileState"],
            }
        if (
            _inspection_selector(rows) != selector
            or _inspection_guard(rows, release) != guard
            or _inspection_mounts() != rows
            or _inspection_read(INSPECTION_POLICY, rows, maximum=_INSPECTION_MAX_POLICY)
            != policy_body
            or _inspection_read(
                selected / "artifact-index.json", rows, maximum=_INSPECTION_MAX_ACCOUNTING
            )
            != index_body
        ):
            _inspection_refuse()
    except Exception:  # noqa: BLE001 - stale/unknown facts cannot enable a mutation
        return unknown("facts-unavailable")
    permissions = {**policy["permissions"]}
    if guard == "held":
        permissions["archive"] = False
    # The nine rootless bindings do not select system scheduled observers. The
    # native .venv scheduled-client unit is not proof for this profile. No new
    # scheduler or substitute client is installed to manufacture that authority.
    permissions["schedule"] = permissions["observer"] = False
    return {
        "schema_version": 1,
        "state": "guarded" if guard == "held" else "permitted",
        "deployment": "rootless",
        "source_commit": release["source_commit"],
        "index_sha256": policy["index_sha256"],
        "image": release["app_image"],
        "policy_sha256": hashlib.sha256(policy_body).hexdigest(),
        "permissions": permissions,
        "facts": {"guard": guard, "archive_mount": mount, "units": units},
    }


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


def command(profile, role, arguments=()):  # noqa: PLR0912, PLR0915 - one closed role/mount allowlist
    if role not in {*NAMES, "client"} or (role != "client" and arguments):
        msg = "unknown fixed container role"
        raise ValueError(msg)
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
    invocation = os.environ.get("INVOCATION_ID", "")
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
        argv += volume("/run/hfcache/hfcache.lock", writable=True, shared=True)
    if role in {"api", "client", "caddy"}:
        argv += volume("/run/hfcache/api", writable=role == "api", shared=True)
    if role in {"api", "worker"}:
        argv += volume("/run/hfcache/verification", writable=role == "worker", shared=True)
    if role == "api":
        argv += volume("/run/hfcache/api.lock", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/api", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/hf-home", writable=True, shared=True)
        argv += volume("/var/cache/hfcache", writable=True, shared=True)
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
            "api|worker|caddy|client CLI_ARGS...|stop api|worker|caddy|inspect-cockpit\n"
            "Rootless user-manager launcher; fixed local /usr/bin/podman. "
            "Reads protected rendered/runtime.json from its physical release. "
            "Podman mounts role-specific secrets; worker receives none. "
            "Starts role containers or drains an owned executor without killing. "
            "Root-only inspect-cockpit reports read-only pinned host permission facts; "
            "it starts no container and reads no archive contents or credentials. "
            "No engine/executable override; no dry-run. Help reads no profile."
        )
        return 0
    if sys.argv[1:] == ["inspect-cockpit"]:
        print(json.dumps(inspect_cockpit(), sort_keys=True, separators=(",", ":")))
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
        argv = command(profile, role, sys.argv[2:])
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
