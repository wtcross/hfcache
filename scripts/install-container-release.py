#!/usr/bin/python3
"""Immutable local staging and guarded rootless release selection.

No pulls, secrets, service activation or NAS file I/O. Unknown artifacts/process
state are preserved and refuse selection. Only a noncreating domain flock guards
the atomic current link; normal runtime startup remains a separate operation.
"""

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath

REPOSITORY = Path(__file__).resolve().parents[1]
PREFIX = Path("/opt/hfcache")
LOCK_PATH = Path("/run/hfcache/hfcache.lock")
BINDINGS = {
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
OWNER_UID = 0
CGROUP_ROOT = Path("/sys/fs/cgroup")
MOUNTINFO = Path("/proc/self/mountinfo")
IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
HOSTNAME = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?\Z")
REQUIRED = {
    "scripts/container-service.py",
    "scripts/hfcache-client",
    "packaging/systemd/hfcache.target",
    "packaging/containers/hfcache.target",
    "packaging/containers/hfcache-api.service",
    "packaging/containers/hfcache-caddy.service",
    "packaging/containers/hfcache-verification.service",
    "packaging/containers/hfcache-verification.socket",
    "packaging/containers/hfcache-containers.service.in",
    "packaging/containers/Caddyfile.in",
    "packaging/containers/server.toml.in",
    "packaging/containers/client.toml",
}
_LOCAL_FS = {"xfs", "ext4", "ext3", "ext2", "btrfs", "tmpfs", "overlay"}
_MAX_ARTIFACT = 16777216
_MAX_MANIFEST = 1048576
_MAX_SOURCE_FILES = 1000
_MOUNT_FIELDS = 6
_MOUNT_TRAILING_FIELDS = 3
_LOCK_MODE = 0o600
_INSTALL_ERRORS = (OSError, ValueError, TypeError, RecursionError, subprocess.SubprocessError)
_METADATA = (
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
_INDEX = "artifact-index.json"
_RELEASE = "container-release.json"
_DERIVED = {
    "runtime.json",
    "default-seccomp.json",
    "worker-seccomp.json",
    "seccomp-provenance.json",
}


def refuse(message):
    raise ValueError(message)


def mount_rows():
    rows = []
    for line in MOUNTINFO.read_text().splitlines():
        left, separator, right = line.partition(" - ")
        before, after = left.split(), right.split()
        if not separator or len(before) < _MOUNT_FIELDS or len(after) < _MOUNT_TRAILING_FIELDS:
            refuse("mount accounting unavailable")
        path = Path(re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), before[4]))
        rows.append((path, after[0], set(before[5].split(",")), set(after[2].split(","))))
    return rows


def local(path):
    """Reject NAS paths/aliases before opening any deployment artifact."""
    path = Path(os.path.abspath(path))  # noqa: PTH100 - lexical normalization must not follow NAS aliases
    if Path("/srv") in (path, *path.parents):
        refuse("deployment paths must be local")
    matches = [
        (len(where.parts), kind)
        for where, kind, _, _ in mount_rows()
        if where in (path, *path.parents)
    ]
    deepest = max((depth for depth, _ in matches), default=-1)
    if not matches or any(kind not in _LOCAL_FS for depth, kind in matches if depth == deepest):
        refuse("deployment path is not proven local")
    current = Path("/")
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(info.st_mode):
            refuse("deployment path follows a symlink")
    return path


def _trusted_directory(info, owners):
    if info.st_uid not in owners or (
        info.st_mode & 0o022 and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)
    ):
        refuse("untrusted deployment parent")


def _parent(path, *, protected=False, owners=None):
    path = local(path.parent) / path.name
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parent.parts[1:]:
            if protected:
                _trusted_directory(os.fstat(descriptor), owners or {0, OWNER_UID})
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=descriptor
            )
            os.close(descriptor)
            descriptor = child
        if protected:
            _trusted_directory(os.fstat(descriptor), owners or {0, OWNER_UID})
    except BaseException:
        os.close(descriptor)
        raise
    else:
        return descriptor


def read_file(path, *, protected=False, maximum=_MAX_ARTIFACT):
    """Bound descriptor-pinned reads; atime is deliberately absent from stability."""
    parent = _parent(path, protected=protected)
    descriptor = -1
    try:
        descriptor = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent
        )
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or not 0 < before.st_size <= maximum
        ):
            refuse("invalid bounded release artifact")
        if protected and (before.st_uid != OWNER_UID or before.st_mode & 0o022):
            refuse("unprotected release artifact")
        body = bytearray()
        while len(body) <= maximum:
            chunk = os.read(descriptor, min(65536, maximum + 1 - len(body)))
            if not chunk:
                break
            body.extend(chunk)
        after = os.fstat(descriptor)
        if len(body) != before.st_size or any(
            getattr(before, name) != getattr(after, name) for name in _METADATA
        ):
            refuse("release artifact changed")
        return bytes(body)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            refuse("duplicate artifact field")
        result[key] = value
    return result


def decode(body):
    return json.loads(
        body,
        object_pairs_hook=_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite artifact field")),
    )


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def _relative(name):
    if (
        not isinstance(name, str)
        or not name
        or any(not character.isprintable() for character in name)
        or "\\" in name
    ):
        refuse("unsafe release source path")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or str(path) != name:
        refuse("unsafe release source path")
    return path


def manifest(value):
    fields = {
        "schema_version",
        "version",
        "hostname",
        "service_uid",
        "service_gid",
        "app_image",
        "caddy_image",
        "source_commit",
        "wheel_sha256",
        "files",
    }
    if not isinstance(value, dict) or set(value) != fields:
        refuse("unknown release manifest")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        refuse("unknown release manifest schema")
    if any(
        type(value[key]) is not int or value[key] <= 0 for key in ("service_uid", "service_gid")
    ):
        refuse("invalid service identity")
    for key, pattern in (
        ("version", VERSION),
        ("hostname", HOSTNAME),
        ("app_image", IMAGE),
        ("caddy_image", IMAGE),
        ("source_commit", re.compile(r"[0-9a-f]{40}\Z")),
        ("wheel_sha256", HEX),
    ):
        if not isinstance(value[key], str) or not pattern.fullmatch(value[key]):
            refuse("invalid release identity")
    files = value["files"]
    if (
        not isinstance(files, dict)
        or not files.keys() >= REQUIRED
        or len(files) > _MAX_SOURCE_FILES
    ):
        refuse("missing release source identities")
    for name, digest in files.items():
        path = _relative(name)
        if (
            path.parts[0] in {"rendered", _INDEX, _RELEASE}
            or not isinstance(digest, str)
            or not HEX.fullmatch(digest)
        ):
            refuse("invalid release source identity")
    return value


def protected_json(path):
    return manifest(decode(read_file(path, protected=True, maximum=_MAX_MANIFEST)))


def worker_seccomp(base):
    """Narrow the default policy to native AF_UNIX socket creation only."""
    if (
        not isinstance(base, dict)
        or base.get("defaultAction") != "SCMP_ACT_ERRNO"
        or not isinstance(base.get("syscalls"), list)
    ):
        refuse("unrecognized default seccomp policy")
    result = json.loads(json.dumps(base))
    # Locked payload images are Linux/amd64. Native-only execution avoids
    # libseccomp's compat socketcall expansion colliding with native socket
    # restrictions, and preserves the predecessor's native-architecture guard.
    result.pop("architectures", None)
    result["archMap"] = [{"architecture": "SCMP_ARCH_X86_64", "subArchitectures": []}]
    rules = []
    native_socket_allowed = False
    for rule in result["syscalls"]:
        if (
            not isinstance(rule, dict)
            or not isinstance(rule.get("names"), list)
            or not rule["names"]
            or not all(isinstance(name, str) for name in rule["names"])
            or not isinstance(rule.get("action"), str)
        ):
            refuse("unrecognized default seccomp syscall rule")
        if rule["action"] == "SCMP_ACT_ALLOW":
            if "socket" in rule["names"] and not any(
                rule.get(key) for key in ("args", "includes", "excludes")
            ):
                native_socket_allowed = True
            rule["names"] = [name for name in rule["names"] if name not in {"socket", "socketcall"}]
        if rule["names"]:
            rules.append(rule)
    if not native_socket_allowed:
        refuse("default native socket permission is not proven")
    rules.append(
        {
            "names": ["socket"],
            "action": "SCMP_ACT_ALLOW",
            "args": [{"index": 0, "value": 1, "op": "SCMP_CMP_EQ"}],
        }
    )
    result["syscalls"] = rules
    return result


def _template_names(release):
    return sorted(
        name
        for name in release["files"]
        if PurePosixPath(name).parent == PurePosixPath("packaging/containers")
        and (
            PurePosixPath(name).suffix in {".service", ".socket", ".target", ".in"}
            or PurePosixPath(name).name == "client.toml"
        )
    )


def _rendered(source, release, base):
    output = {}
    for name in _template_names(release):
        body = (
            read_file(source / name)
            .decode()
            .replace("@SERVICE_UID@", str(release["service_uid"]))
            .replace("@HOSTNAME@", release["hostname"])
            .replace(
                "@ALLOWED_HOSTS@",
                json.dumps(list(dict.fromkeys([release["hostname"], "localhost", "127.0.0.1"]))),
            )
        )
        if re.search(r"@[A-Z_]+@", body):
            refuse("unresolved profile placeholder")
        target = PurePosixPath(name).name.removesuffix(".in")
        if target in output or target in _DERIVED:
            refuse("colliding rendered artifact")
        output[target] = body.encode()
    output["runtime.json"] = encoded(
        {
            key: release[key]
            for key in ("schema_version", "service_uid", "service_gid", "app_image", "caddy_image")
        }
    )
    output["default-seccomp.json"] = base
    output["worker-seccomp.json"] = encoded(worker_seccomp(decode(base)))
    output["seccomp-provenance.json"] = encoded(
        {
            "default_sha256": hashlib.sha256(base).hexdigest(),
            "derived_sha256": hashlib.sha256(output["worker-seccomp.json"]).hexdigest(),
        }
    )
    return output


def write_file(path, body, *, mode=0o644):
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, mode
    )
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(body)
            stream.flush()
            os.fchmod(descriptor, mode)
            os.fsync(descriptor)
    finally:
        os.close(descriptor)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def render(source, target, release, default_seccomp):
    source, target = local(source), local(target)
    manifest(release)
    output = _rendered(source, release, read_file(local(default_seccomp)))
    target.mkdir(mode=0o755)
    for name, body in output.items():
        write_file(target / name, body)
    sync_directory(target)


def _tree_files(root, expected):
    files = set()
    directories = {
        parent.as_posix()
        for name in expected
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    for directory, names, leaves in os.walk(root, followlinks=False):
        for name in names:
            path = Path(directory) / name
            if (
                stat.S_ISLNK(path.lstat().st_mode)
                or path.relative_to(root).as_posix() not in directories
            ):
                refuse("unexplained release directory preserved")
        for name in leaves:
            path = Path(directory) / name
            if not stat.S_ISREG(path.lstat().st_mode):
                refuse("unexplained release artifact preserved")
            files.add(path.relative_to(root).as_posix())
    return files


def _expected_files(release):
    rendered = {
        PurePosixPath(name).name.removesuffix(".in") for name in _template_names(release)
    } | _DERIVED
    return set(release["files"]) | {_RELEASE} | {"rendered/" + name for name in rendered}


def _verify_stage(destination):
    release = protected_json(destination / _RELEASE)
    index = decode(read_file(destination / _INDEX, protected=True, maximum=_MAX_MANIFEST))
    expected = _expected_files(release)
    if (
        not isinstance(index, dict)
        or set(index) != {"schema_version", "files"}
        or type(index["schema_version"]) is not int
        or index["schema_version"] != 1
        or not isinstance(index["files"], dict)
        or set(index["files"]) != expected
    ):
        refuse("unknown staged artifact index")
    if _tree_files(destination, expected) != expected | {_INDEX}:
        refuse("unexplained staged artifacts preserved")
    for name, digest in index["files"].items():
        _relative(name)
        if not isinstance(digest, str) or not HEX.fullmatch(digest):
            refuse("invalid staged artifact digest")
        actual = hashlib.sha256(read_file(destination / name, protected=True)).hexdigest()
        if actual != digest or (name in release["files"] and actual != release["files"][name]):
            refuse("staged release artifact changed")
    base = read_file(destination / "rendered/default-seccomp.json", protected=True)
    for name, expected_body in _rendered(destination, release, base).items():
        if read_file(destination / "rendered" / name, protected=True) != expected_body:
            refuse("rendered policy or provenance changed")
    return release


def stage(source, release, default_seccomp):
    source = local(source)
    manifest(release)
    destination = local(PREFIX / "releases" / release["version"])
    staging = local(PREFIX / "releases" / (".container-stage-" + release["version"]))
    parent = _parent(staging, protected=True)
    try:
        for name in (destination.name, staging.name):
            try:
                os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                continue
            refuse("existing release or staging evidence preserved")
        os.mkdir(staging.name, mode=0o755, dir_fd=parent)
        sync_directory(staging.parent)
        for name, expected in release["files"].items():
            body = read_file(source / name)
            if hashlib.sha256(body).hexdigest() != expected:
                refuse("source artifact changed")
            output = staging / name
            output.parent.mkdir(parents=True, exist_ok=True)
            write_file(output, body, mode=0o755 if name.startswith("scripts/") else 0o644)
        render(staging, staging / "rendered", release, default_seccomp)
        write_file(staging / _RELEASE, encoded(release))
        files = _expected_files(release)
        write_file(
            staging / _INDEX,
            encoded(
                {
                    "schema_version": 1,
                    "files": {
                        name: hashlib.sha256(read_file(staging / name, protected=True)).hexdigest()
                        for name in sorted(files)
                    },
                }
            ),
        )
        _verify_stage(staging)
        for directory, _, _ in os.walk(staging, topdown=False):
            sync_directory(Path(directory))
        os.rename(staging.name, destination.name, src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    return destination


def system_show(unit, *, user=False, uid=None):
    argv = ["/usr/bin/systemctl"]
    if user:
        argv = [
            "/usr/sbin/runuser",
            "-u",
            "hfcache",
            "--",
            "/usr/bin/env",
            f"XDG_RUNTIME_DIR=/run/user/{uid}",
            "/usr/bin/systemctl",
            "--user",
        ]
    result = subprocess.run(  # noqa: S603 - fixed manager commands and validated numeric identity
        [
            *argv,
            "show",
            unit,
            "--no-pager",
            "--property=LoadState,ActiveState,MainPID,ControlPID,TasksCurrent,ControlGroup",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)


def _empty_cgroup(path):
    if (
        not isinstance(path, str)
        or not path.startswith("/")
        or str(PurePosixPath(path)) != path
        or ".." in PurePosixPath(path).parts
    ):
        refuse("unknown executor cgroup")
    root = CGROUP_ROOT / path.lstrip("/")
    if not root.is_dir() or root.is_symlink():
        refuse("executor cgroup accounting unavailable")
    for directory, names, _ in os.walk(root, followlinks=False):
        if any((Path(directory) / name).is_symlink() for name in names):
            refuse("unsafe executor cgroup accounting")
        if (Path(directory) / "cgroup.procs").read_text().strip():
            refuse("surviving actual executor preserved")


def _quiescent_unit(unit, state):
    load, active = state.get("LoadState"), state.get("ActiveState")
    if load not in {"loaded", "masked", "not-found"} or active not in {"inactive", "failed"}:
        refuse("executor state is active or unknown")
    if load == "loaded" and unit.endswith(".service"):
        if (
            state.get("MainPID") != "0"
            or state.get("ControlPID") != "0"
            or "ControlGroup" not in state
        ):
            refuse("executor PID accounting unavailable")
        tasks, group = state.get("TasksCurrent"), state["ControlGroup"]
        if tasks != "0" and not (tasks == "[not set]" and group == ""):
            refuse("executor task accounting unavailable")
        if group:
            _empty_cgroup(group)
    elif any(state.get(name, "0") != "0" for name in ("MainPID", "ControlPID")) or state.get(
        "ControlGroup"
    ):
        refuse("unloaded executor retains unknown process state")


def quiescent(release):
    for unit in (
        "hfcache-sync.timer",
        "hfcache-verify.timer",
        "hfcache-sync.service",
        "hfcache-verify.service",
        "hfcache-api.service",
        "hfcache-api.socket",
        "hfcache-verification.service",
        "hfcache-verification.socket",
        "hfcache-containers.service",
    ):
        _quiescent_unit(unit, system_show(unit))
    manager = subprocess.run(  # noqa: S603 - fixed local manager and validated numeric identity
        ["/usr/bin/systemctl", "is-active", f"user@{release['service_uid']}.service"],
        capture_output=True,
        check=False,
        text=True,
    )
    state = manager.stdout.strip()
    if (manager.returncode, state) not in {(0, "active"), (3, "inactive"), (3, "failed")}:
        refuse("user manager accounting unavailable")
    if manager.returncode == 0:
        for unit in (
            "hfcache-api.service",
            "hfcache-caddy.service",
            "hfcache-verification.service",
            "hfcache-verification.socket",
        ):
            _quiescent_unit(unit, system_show(unit, user=True, uid=release["service_uid"]))
    result = subprocess.run(  # noqa: S603 - explicit local engine and fixed account/arguments
        [
            "/usr/sbin/runuser",
            "-u",
            "hfcache",
            "--",
            "/usr/bin/env",
            f"XDG_RUNTIME_DIR=/run/user/{release['service_uid']}",
            "/usr/bin/podman",
            "--remote=false",
            "ps",
            "--format=json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if decode(result.stdout) != []:
        refuse("surviving rootless executor preserved")
    mounts = [row for row in mount_rows() if row[0] == Path("/srv/hfcache") and row[1] != "autofs"]
    if (
        len(mounts) != 1
        or mounts[0][1] not in {"nfs", "nfs4"}
        or "ro" not in mounts[0][2]
        or "rw" in mounts[0][2]
    ):
        refuse("read-only NAS barrier is not established")
    scopes = CGROUP_ROOT / f"user.slice/user-{release['service_uid']}.slice"
    for group in scopes.glob("**/libpod*.scope"):
        _empty_cgroup("/" + group.relative_to(CGROUP_ROOT).as_posix())


def _previous_selector(parent):
    try:
        info = os.stat("current", dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return
    if not stat.S_ISLNK(info.st_mode):
        refuse("unexpected current selector preserved")
    value = os.readlink("current", dir_fd=parent)
    prefix = "releases/"
    if not value.startswith(prefix) or not VERSION.fullmatch(value[len(prefix) :]):
        refuse("unreviewed previous selector preserved")
    target = local(PREFIX / value)
    descriptor = _parent(target / ".selector-check", protected=True)
    os.close(descriptor)


def _verify_bindings():
    """Only exact reviewed links may dispatch through the atomic selector."""
    for installed, relative in BINDINGS.items():
        parent = _parent(installed, protected=True)
        try:
            info = os.stat(installed.name, dir_fd=parent, follow_symlinks=False)
            if (
                not stat.S_ISLNK(info.st_mode)
                or info.st_uid != OWNER_UID
                or os.readlink(installed.name, dir_fd=parent) != str(PREFIX / "current" / relative)
            ):
                refuse("installed release binding is missing or unreviewed")
        finally:
            os.close(parent)


def switch(version):
    if not VERSION.fullmatch(version):
        refuse("invalid release version")
    destination = local(PREFIX / "releases" / version)
    release = protected_json(destination / _RELEASE)
    lock_parent = _parent(LOCK_PATH, protected=True, owners={0, OWNER_UID, release["service_uid"]})
    descriptor = prefix = -1
    try:
        descriptor = os.open(
            LOCK_PATH.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=lock_parent
        )
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != release["service_uid"]
            or stat.S_IMODE(info.st_mode) != _LOCK_MODE
            or info.st_nlink != 1
        ):
            refuse("unsafe existing archive lock")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        linked = os.stat(LOCK_PATH.name, dir_fd=lock_parent, follow_symlinks=False)
        if (linked.st_dev, linked.st_ino) != (info.st_dev, info.st_ino):
            refuse("existing archive lock changed")
        quiescent(release)
        actual = _verify_stage(destination)
        if actual != release or release["version"] != version:
            refuse("release identity changed")
        _verify_bindings()
        prefix = _parent(PREFIX / "current", protected=True)
        _previous_selector(prefix)
        temporary = ".current-container-next"
        os.symlink("releases/" + version, temporary, dir_fd=prefix)
        os.replace(temporary, "current", src_dir_fd=prefix, dst_dir_fd=prefix)
        os.fsync(prefix)
    finally:
        if prefix >= 0:
            os.close(prefix)
        if descriptor >= 0:
            os.close(descriptor)
        os.close(lock_parent)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("render", "stage", "switch"),
        help="render: new local artifact tree; stage: protected immutable release; "
        "switch: inspect system/user managers and local Podman, retain original lock, "
        "then atomically select; no activation or credential delivery",
    )
    parser.add_argument("--manifest", type=Path, help="explicit immutable image/source manifest")
    parser.add_argument(
        "--source", type=Path, default=REPOSITORY, help="reviewed local source artifacts"
    )
    parser.add_argument("--output", type=Path, help="new local render directory (render only)")
    parser.add_argument("--version", help="staged version to select (switch only)")
    parser.add_argument(
        "--default-seccomp", type=Path, default=Path("/usr/share/containers/seccomp.json")
    )
    options = parser.parse_args()
    if options.mode != "render" and os.geteuid() != 0:
        parser.error("stage/switch require root")
    try:
        if options.mode == "switch":
            if not options.version:
                refuse("switch requires version")
            destination = switch(options.version)
        else:
            if options.manifest is None:
                refuse("explicit manifest required")
            release = (
                protected_json(options.manifest)
                if options.mode == "stage"
                else manifest(decode(read_file(local(options.manifest), maximum=_MAX_MANIFEST)))
            )
            if options.mode == "stage":
                destination = stage(options.source, release, options.default_seccomp)
            else:
                if options.output is None:
                    refuse("render requires a new local output directory")
                render(options.source, options.output, release, options.default_seccomp)
                destination = options.output
    except _INSTALL_ERRORS:
        print(
            "container release refused; previous artifacts/state and failed staging are preserved"
        )
        return 20
    print(
        f"container release {options.mode}: {destination}; "
        "no service activation or archive file I/O"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
