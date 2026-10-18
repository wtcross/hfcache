"""Explicit hardening inventory and owned disposable workloads (docs/security.md).

Import, default invocation, help and dry-run perform no probes. A transient
native process cannot certify installed container PID1/cgroup/peer controls.
No check changes kernel settings or writes a system-directory scratch file.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import logging
import os
import pwd
import secrets
import socket
import ssl
import stat
import subprocess
import sys
from contextlib import ExitStack, contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from uuid import UUID

NATIVE_PYTHON = "/opt/hfcache/current/.venv/bin/python"
MAX_RESULTS = 32
MAX_SENTINEL_BYTES = 65536
PRIVATE_DIRECTORY_MODE = 0o700
PUBLISHED_DIRECTORY_MODE = 0o2750

PERMISSION_DENIALS = frozenset({errno.EACCES, errno.EPERM})
LOCAL_FILESYSTEMS = frozenset({"tmpfs", "ext4", "xfs", "btrfs", "overlay", "zfs"})
PROFILES = ("native", "rootless", "guarded-readonly")
UNITS = ("hfcache-api.service", "hfcache-verification.service")
FORBIDDEN_CREDENTIAL_ENV = (
    "CREDENTIALS_DIRECTORY",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "HUGGINGFACEHUB_API_TOKEN",
    "HF_TOKEN_PATH",
    "HFCACHE_API_TOKEN",
    "HFCACHE_MCP_TOKEN",
)
# Copy only sandbox policy, never lifecycle hooks, credentials, environment,
# production writable paths or managed directories.
SANDBOX_PROPERTIES = frozenset(
    {
        "User",
        "Group",
        "UMask",
        "NoNewPrivileges",
        "ProtectSystem",
        "ProtectHome",
        "PrivateTmp",
        "PrivateDevices",
        "ProtectKernelTunables",
        "ProtectKernelModules",
        "ProtectKernelLogs",
        "ProtectControlGroups",
        "ProtectClock",
        "ProtectHostname",
        "ProtectProc",
        "ProcSubset",
        "RestrictAddressFamilies",
        "RestrictNamespaces",
        "RestrictSUIDSGID",
        "CapabilityBoundingSet",
        "AmbientCapabilities",
        "SystemCallArchitectures",
        "SystemCallFilter",
        "LockPersonality",
        "MemoryDenyWriteExecute",
        "IPAddressDeny",
        "IPAddressAllow",
        "InaccessiblePaths",
        "ReadOnlyPaths",
    }
)


class RefusedError(Exception):
    """Fixed, secret-free refusal. Dependency exception text is never rendered."""


def reject(message):
    raise RefusedError(message)


class SafeParser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "hardening-probe: invalid arguments; use --help\n")


@dataclass(frozen=True)
class Result:
    name: str
    state: str
    detail: str


class DiscardOutput:
    encoding = "utf-8"

    @property
    def buffer(self):
        return self

    def isatty(self):
        return False

    def fileno(self):
        return 2  # Both descriptors point at /dev/null during the capture scope.

    def write(self, text):
        return len(text)

    def flush(self):
        pass


@contextmanager
def quiet_output():
    previous = logging.root.manager.disable
    with ExitStack() as stack:
        saved_stdout = os.dup(1)
        stack.callback(os.close, saved_stdout)
        saved_stderr = os.dup(2)
        stack.callback(os.close, saved_stderr)
        null = os.open("/dev/null", os.O_WRONLY)
        stack.callback(os.close, null)
        os.dup2(null, 1)
        stack.callback(os.dup2, saved_stdout, 1)
        os.dup2(null, 2)
        stack.callback(os.dup2, saved_stderr, 2)
        logging.disable(logging.CRITICAL)
        stack.callback(logging.disable, previous)
        with redirect_stdout(DiscardOutput()), redirect_stderr(DiscardOutput()):
            yield


def check(name, action, *, denied=False):
    try:
        with quiet_output():
            return action_result(name, action, denied=denied)
    except Exception:  # noqa: BLE001 - capture setup is a prerequisite, never action-denial proof
        return Result(name, "not_proven", "diagnostic capture prerequisite failed")


def action_result(name, action, *, denied=False):
    try:
        detail = action()
    except OSError as error:
        if denied and error.errno in PERMISSION_DENIALS:
            return Result(name, "pass", "action denied; enforcing control not attributed")
        return Result(name, "not_proven", "I/O or network prerequisite failed")
    except ImportError:
        return Result(name, "not_proven", "dependency prerequisite failed")
    except RefusedError:
        return Result(name, "fail", "required condition was not satisfied")
    except Exception:  # noqa: BLE001 - fixed diagnostics, never raw dependency errors
        return Result(name, "not_proven", "unexpected prerequisite or diagnostic failure")
    return Result(
        name, "fail" if denied else "pass", "attempted action permitted" if denied else detail
    )


def canonical_path(value):
    path = PurePosixPath(value)
    if (
        not value.startswith("/")
        or value.startswith("//")
        or value == "/"
        or str(path) != value
        or ".." in path.parts
        or "\\" in value
        or any(not c.isprintable() or c.isspace() or c in "\"'%" for c in value)
    ):
        reject("absolute canonical non-root path required")
    return path


def mount_rows(text):
    rows = []
    for line in text.splitlines():
        fields = line.split()
        separator = fields.index("-")
        point = fields[4]
        for encoded, decoded in (("\\040", " "), ("\\011", "\t"), ("\\134", "\\")):
            point = point.replace(encoded, decoded)
        rows.append(
            (
                PurePosixPath(point),
                fields[separator + 1],
                fields[separator + 2],
                fields[5] + "," + fields[separator + 3],
                fields[2],
                fields[3],
            )
        )
    return rows


def covering_mount(path, rows):
    matches = [row for row in rows if path == row[0] or row[0] in path.parents]
    if not matches:
        reject("filesystem locality unproven")
    return max(enumerate(matches), key=lambda item: (len(item[1][0].parts), item[0]))[1]


def prove_locality(target, lock, kind, rows):
    production_path = PurePosixPath("/srv/hfcache")
    if target == production_path or production_path in target.parents:
        reject("production archive forbidden")
    selected = covering_mount(target, rows)
    production = [row for row in rows if row[0] == production_path]
    if selected[1] in {"nfs", "nfs4"} and production:
        # Mount source spellings and addresses can alias. No NFS workload is
        # permitted on a host carrying the production mount, even if a different
        # superblock or source spelling makes exact alias comparison inconclusive.
        reject("NFS workload forbidden while production mount exists")
    # Refuse hidden submounts and remote traversal prefixes before opening the
    # archive/health paths; a local mount can otherwise hide a remote ancestor.
    if any(target in row[0].parents for row in rows):
        reject("archive contains unexplained submounts")
    for ancestor in (*target.parents, *lock.parents):
        if covering_mount(ancestor, rows)[1] not in LOCAL_FILESYSTEMS:
            reject("path traversal crosses an unproven local filesystem")
    if kind == "local":
        if selected[1] not in LOCAL_FILESYSTEMS:
            reject("fixture filesystem not proven local")
    elif selected[0] != target or selected[1] not in {"nfs", "nfs4"}:
        reject("target not an exact disposable NFS mount")
    if "ro" in selected[3].split(","):
        reject("read-only target refuses workloads")
    if target == lock or target in lock.parents:
        reject("lock must be outside archive")
    if covering_mount(lock, rows)[1] not in LOCAL_FILESYSTEMS:
        reject("lock locality unproven")


def open_directory(path, stack):
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    stack.callback(os.close, descriptor)
    for part in path.parts[1:]:
        descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
        stack.callback(os.close, descriptor)
    return descriptor


def identity(descriptor):
    status = os.fstat(descriptor)
    return status.st_dev, status.st_ino


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            reject("duplicate sentinel field")
        result[key] = value
    return result


def read_identity(root, expected):
    sys.dont_write_bytecode = True
    from hfcache.errors import SafetyError
    from hfcache.models import ArchiveSentinel, load

    descriptor = os.open(".hfcache-root", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root)
    try:
        status = os.fstat(descriptor)
        if not stat.S_ISREG(status.st_mode) or status.st_size > MAX_SENTINEL_BYTES:
            reject("sentinel not a bounded ordinary file")
        if status.st_uid != os.fstat(root).st_uid or status.st_mode & 0o022 or status.st_nlink != 1:
            reject("sentinel ownership or mode is unsafe")
        raw = os.read(descriptor, MAX_SENTINEL_BYTES + 1)
        document = json.loads(raw, object_pairs_hook=unique_pairs)
        if set(document) != {
            "schema_version",
            "layout_version",
            "archive_id",
            "created_at",
            "created_by",
        }:
            reject("sentinel fields are incomplete or unsupported")
        sentinel = load(ArchiveSentinel, raw, error=SafetyError, code="HFMNT006")
        if sentinel.archive_id != expected:
            reject("archive identity mismatch")
        return identity(descriptor), hashlib.sha256(raw).digest()
    finally:
        os.close(descriptor)


def validate_health(root, store, health, uid, kind):
    root_status = os.fstat(root)
    if kind == "local" and uid >= 0 and root_status.st_uid != uid:
        reject("fixture not owned by executor")
    for descriptor in (root, store, health):
        status = os.fstat(descriptor)
        if status.st_dev != root_status.st_dev or status.st_uid != root_status.st_uid:
            reject("health ownership or filesystem differs")
        if status.st_mode & 0o022:
            reject("archive directories allow unrelated writes")
    if stat.S_IMODE(os.fstat(health).st_mode) != PRIVATE_DIRECTORY_MODE:
        reject("health must be private")


def prove_mount_device(root, target, rows):
    mount = covering_mount(target, rows)
    device = os.fstat(root).st_dev
    if mount[4] != f"{os.major(device)}:{os.minor(device)}":
        reject("mount identity changed before opening target")


def validate_lock(lock, parent, uid, lock_path, rows):
    parent_status = os.fstat(parent)
    status = os.fstat(lock)
    if parent_status.st_mode & 0o022 or (uid >= 0 and parent_status.st_uid != uid):
        reject("lock parent ownership or mode unsafe")
    if (
        not stat.S_ISREG(status.st_mode)
        or status.st_nlink != 1
        or (uid >= 0 and status.st_uid != uid)
        or status.st_mode & 0o027
    ):
        reject("existing lock not safely owned")
    prove_mount_device(parent, lock_path.parent, rows)
    prove_mount_device(lock, lock_path, rows)
    if status.st_dev != parent_status.st_dev:
        reject("lock is not on the proven parent filesystem")


@contextmanager
def target_scope(options, *, mount_text=None, owner_uid=None):
    """Prove target and acquire an existing local lock before the first write."""
    if options.profile != "native" or not options.acknowledge_disposable:
        reject("explicit native disposable authorization required")
    target = canonical_path(options.archive_root or "")
    lock_path = canonical_path(options.lock_file or "")
    if str(UUID(options.archive_id)) != options.archive_id:
        reject("expected archive UUID required")
    production = PurePosixPath("/srv/hfcache")
    if target == production or production in target.parents:
        reject("production archive forbidden")
    rows = mount_rows(
        Path("/proc/self/mountinfo").read_text() if mount_text is None else mount_text
    )
    prove_locality(target, lock_path, options.target_kind, rows)
    uid = os.getuid() if owner_uid is None else owner_uid
    with ExitStack() as stack:
        root = open_directory(target, stack)
        store = os.open(".store", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root)
        stack.callback(os.close, store)
        health = os.open("health", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=store)
        stack.callback(os.close, health)
        validate_health(root, store, health, uid, options.target_kind)
        prove_mount_device(root, target, rows)
        sentinel_identity = read_identity(root, options.archive_id)
        lock_parent = open_directory(lock_path.parent, stack)
        lock = os.open(
            lock_path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=lock_parent
        )
        stack.callback(os.close, lock)
        validate_lock(lock, lock_parent, uid, lock_path, rows)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = os.stat(lock_path.name, dir_fd=lock_parent, follow_symlinks=False)
        if identity(lock) != (current.st_dev, current.st_ino):
            reject("lock identity changed")
        if read_identity(root, options.archive_id) != sentinel_identity:
            reject("sentinel changed under lock")
        if identity(open_directory(target, stack)) != identity(root):
            reject("target changed under lock")
        checked_store = os.open(".store", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root)
        stack.callback(os.close, checked_store)
        checked_health = os.open(
            "health", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=checked_store
        )
        stack.callback(os.close, checked_health)
        if identity(checked_store) != identity(store) or identity(checked_health) != identity(
            health
        ):
            reject("health path changed under lock")
        validate_health(root, checked_store, checked_health, uid, options.target_kind)
        validate_lock(lock, lock_parent, uid, lock_path, rows)
        if identity(open_directory(lock_path.parent, stack)) != identity(lock_parent):
            reject("lock parent changed under lock")
        yield health


def same_entry(parent, name, expected):
    try:
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return (current.st_dev, current.st_ino) == expected


@contextmanager
def owned_health_directory(health):
    name = "hardening-" + secrets.token_hex(16)
    os.mkdir(name, 0o700, dir_fd=health)
    descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=health)
    expected = identity(descriptor)
    try:
        yield descriptor
    finally:
        empty = not os.listdir(descriptor)  # noqa: PTH208 - descriptor-pinned enumeration
        os.close(descriptor)
        if not empty or not same_entry(health, name, expected):
            reject("probe directory changed; evidence preserved")
        os.rmdir(name, dir_fd=health)


def file_workload(directory):
    """Exercise publication syscalls and clean only exact owned inodes."""
    owned = {}
    try:
        descriptor = os.open(
            "source", os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY, 0o600, dir_fd=directory
        )
        owned["source"] = identity(descriptor)
        try:
            os.write(descriptor, b"hfcache disposable hardening probe")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.link(
            "source", "linked", src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False
        )
        owned["linked"] = owned["source"]
        if not same_entry(directory, "linked", owned["source"]):
            reject("hardlink identity differs")
        reservation = os.open(
            "renamed", os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY, 0o600, dir_fd=directory
        )
        owned["renamed"] = identity(reservation)
        os.close(reservation)
        if not same_entry(directory, "renamed", owned["renamed"]) or not same_entry(
            directory, "source", owned["source"]
        ):
            reject("rename destination changed")
        os.rename("source", "renamed", src_dir_fd=directory, dst_dir_fd=directory)
        owned["renamed"] = owned.pop("source")
        reader = os.open("renamed", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            if identity(reader) != owned["renamed"]:
                reject("read target changed")
            payload = os.read(reader, 128)
            expected = b"hfcache disposable hardening probe"
            if hashlib.sha256(payload).digest() != hashlib.sha256(expected).digest():
                reject("owned content digest mismatch")
        finally:
            os.close(reader)
        os.mkdir("setgid", 0o750, dir_fd=directory)
        child = os.open("setgid", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
        owned["setgid"] = identity(child)
        try:
            os.fchmod(child, 0o2750)
            if stat.S_IMODE(os.fstat(child).st_mode) != PUBLISHED_DIRECTORY_MODE:
                reject("setgid mode did not land")
        finally:
            os.close(child)
        os.fsync(directory)
        return "owned create/fsync/hardlink/rename/mkdir/chmod completed"
    finally:
        cleanup_owned(directory, owned)


def cleanup_owned(directory, owned):
    changed = False
    for name, expected in reversed(tuple(owned.items())):
        if not same_entry(directory, name, expected):
            changed = True
            continue
        if name == "setgid":
            os.rmdir(name, dir_fd=directory)
        else:
            os.unlink(name, dir_fd=directory)
    if changed:
        reject("probe entry changed; unexplained evidence preserved")


def status_observations():
    fields = dict(
        line.split(":", 1)
        for line in Path("/proc/self/status").read_text().splitlines()
        if ":" in line
    )
    results = []
    for name, field, expected in (
        ("NoNewPrivs observed", "NoNewPrivs", 1),
        ("effective capabilities empty", "CapEff", 0),
        ("bounding capabilities empty", "CapBnd", 0),
    ):
        value = int(fields[field].strip(), 16 if field.startswith("Cap") else 10)
        results.append(
            Result(name, "pass" if value == expected else "fail", "process status observed")
        )
    loaded = fields.get("Seccomp", "0").strip() == "2"
    results.append(
        Result(
            "seccomp filter loaded",
            "pass" if loaded else "fail",
            "filter presence only; individual syscall rules not established",
        )
    )
    rows = mount_rows(Path("/proc/self/mountinfo").read_text())
    for location in ("/usr", "/etc", "/opt"):
        readonly = "ro" in covering_mount(PurePosixPath(location), rows)[3].split(",")
        results.append(
            Result(
                f"system mount {location} read-only",
                "pass" if readonly else "not_proven",
                "mount observation only; no system file created",
            )
        )
    hidden = not Path("/proc/sys/vm/swappiness").exists()
    results.append(
        Result(
            "kernel tunable visibility",
            "pass" if hidden else "not_proven",
            "visibility only; no kernel setting opened for writing",
        )
    )
    return results


def credential_observation(path):
    if os.environ.get("HF_HUB_OFFLINE") != "1" or any(
        name in os.environ for name in FORBIDDEN_CREDENTIAL_ENV
    ):
        return Result(
            "verifier credential scope", "fail", "offline flag or credential scope invalid"
        )
    if not path:
        return Result(
            "verifier credential scope", "not_proven", "no known source baseline supplied"
        )
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        if error.errno in PERMISSION_DENIALS | {errno.ENOENT}:
            return Result(
                "verifier credential scope",
                "not_proven",
                "source inaccessible; ordinary DAC or absence may explain denial",
            )
        return Result("verifier credential scope", "not_proven", "source I/O prerequisite failed")
    else:
        os.close(descriptor)
        return Result("verifier credential scope", "fail", "source open succeeded; bytes not read")


def ip_action(family):
    with socket.socket(family, socket.SOCK_STREAM) as connection:
        connection.settimeout(2)
        connection.connect(("127.0.0.1" if family == socket.AF_INET else "::1", 9))
    return "IP connect completed"


def native_extensions():
    import hf_xet  # noqa: F401 - import success is the diagnostic
    import pydantic_core  # noqa: F401
    import yaml  # noqa: F401

    return "required native-extension imports succeeded"


def api_network_checks(cache):
    def dns():
        if not socket.getaddrinfo("huggingface.co", 443):
            reject("DNS returned no addresses")
        return "Hub DNS lookup completed"

    def tls():
        with socket.create_connection(("huggingface.co", 443), timeout=10) as raw:
            with ssl.create_default_context().wrap_socket(raw, server_hostname="huggingface.co"):
                return "verified Hub TLS connection completed"

    def hub():
        from huggingface_hub import HfApi

        if not HfApi().repo_info("hf-internal-testing/tiny-random-gpt2", token=False).sha:
            reject("Hub response omitted immutable identity")
        return "anonymous Hub metadata request completed"

    def download():
        from huggingface_hub import hf_hub_download

        hf_hub_download(
            "hf-internal-testing/tiny-random-gpt2",
            filename="config.json",
            cache_dir=cache,
            token=False,
        )
        return "small anonymous Hub download completed; Xet transfer not established"

    return [
        check("API DNS", dns),
        check("API TLS", tls),
        check("API Hub metadata", hub),
        check("API download", download),
    ]


def service_properties(content):
    properties = []
    inside = False
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("["):
            inside = line == "[Service]"
        elif inside and "=" in line and not line.startswith(("#", ";")):
            key, value = line.split("=", 1)
            if key in SANDBOX_PROPERTIES:
                properties.append((key, value))
    return properties


def parser():
    result = SafeParser(description=__doc__)
    result.add_argument("unit", nargs="?", choices=UNITS, default=UNITS[0])
    result.add_argument("--mode", choices=("plan", "inventory", "workload"), default="plan")
    result.add_argument("--profile", choices=PROFILES)
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--archive-root")
    result.add_argument("--archive-id")
    result.add_argument("--lock-file")
    result.add_argument("--target-kind", choices=("local", "nfs"), default="local")
    result.add_argument("--acknowledge-disposable", action="store_true")
    result.add_argument("--allow-network", action="store_true")
    result.add_argument("--credential-probe")
    result.add_argument("--unit-directory")
    result.add_argument("--wrapper", action="store_true", help=argparse.SUPPRESS)
    result.add_argument("--native-runtime", action="store_true", help=argparse.SUPPRESS)
    return result


def workload(options):
    with target_scope(options) as health:
        with owned_health_directory(health) as directory:
            results = [check("disposable publication syscalls", lambda: file_workload(directory))]
            results.extend(status_observations())
            results.append(check("native extensions", native_extensions))
            if options.unit == UNITS[1]:
                results.append(credential_observation(options.credential_probe))
                results.extend(
                    check(name, lambda f=family: ip_action(f), denied=True)
                    for name, family in (
                        ("verifier IPv4 action", socket.AF_INET),
                        ("verifier IPv6 action", socket.AF_INET6),
                    )
                )
            elif options.allow_network:
                import tempfile

                with tempfile.TemporaryDirectory(prefix="hfcache-probe-") as cache:
                    results.extend(api_network_checks(cache))
    return results


def wrapper_workload(options, properties):
    if os.geteuid() != 0 or options.unit_directory:
        reject("native transient workload requires root and installed properties")
    users = [value for key, value in properties if key == "User"]
    if not users or not users[-1]:
        reject("executor identity missing")
    uid = pwd.getpwnam(users[-1]).pw_uid
    if uid == 0:
        reject("executor must be unprivileged")
    # Before systemd can create even disposable state; child rechecks under lock.
    with target_scope(options, owner_uid=uid):
        pass
    command = ["systemd-run", "--pipe", "--wait", "--collect", "--quiet", "--property=Type=oneshot"]
    command.extend(f"--property={key}={value}" for key, value in properties)
    command.extend(
        [
            f"--property=ReadWritePaths={options.archive_root}/.store/health",
            "--property=PrivateTmp=true",
            "--setenv=HF_HUB_DISABLE_IMPLICIT_TOKEN=1",
            "--setenv=PYTHONDONTWRITEBYTECODE=1",
        ]
    )
    if options.unit == UNITS[1]:
        command.append("--setenv=HF_HUB_OFFLINE=1")
    command.extend(
        [
            "/opt/hfcache/current/.venv/bin/python",
            str(Path(__file__).resolve()),
            options.unit,
            "--mode=workload",
            "--profile=native",
            "--acknowledge-disposable",
            "--archive-root",
            options.archive_root,
            "--archive-id",
            options.archive_id,
            "--lock-file",
            options.lock_file,
            "--target-kind",
            options.target_kind,
        ]
    )
    if options.allow_network:
        command.append("--allow-network")
    if options.credential_probe:
        command.extend(["--credential-probe", options.credential_probe])
    print(
        "native transient diagnostic; credentials/lifecycle/shared state excluded; "
        "health/PrivateTmp overrides applied; not installed container acceptance"
    )
    completed = subprocess.run(command, check=False, capture_output=True, text=True)  # noqa: S603 - fixed manager argv and validated target
    return render_transient_result(
        completed, unit=options.unit, allow_network=options.allow_network
    )


def expected_result_names(unit, *, allow_network=False):
    names = {
        "disposable publication syscalls",
        "NoNewPrivs observed",
        "effective capabilities empty",
        "bounding capabilities empty",
        "seccomp filter loaded",
        "system mount /usr read-only",
        "system mount /etc read-only",
        "system mount /opt read-only",
        "kernel tunable visibility",
        "native extensions",
    }
    if unit == UNITS[1]:
        names.update({"verifier credential scope", "verifier IPv4 action", "verifier IPv6 action"})
    elif allow_network:
        names.update({"API DNS", "API TLS", "API Hub metadata", "API download"})
    return names


def render_transient_result(completed, *, unit=UNITS[0], allow_network=False):
    # Manager errors may echo a misconfigured property value. Never relay them.
    try:
        if len(completed.stdout.encode()) > MAX_SENTINEL_BYTES:
            reject("oversized diagnostic output")
        document = json.loads(completed.stdout, object_pairs_hook=unique_pairs)
        expected = expected_result_names(unit, allow_network=allow_network)
        if (
            set(document) != {"schema_version", "scope", "results"}
            or type(document["schema_version"]) is not int
            or document["schema_version"] != 1
        ):
            reject("invalid diagnostic response")
        if (
            document["scope"] != "current probe process only"
            or not document["results"]
            or len(document["results"]) > MAX_RESULTS
        ):
            reject("oversized diagnostic response")
        for row in document["results"]:
            if set(row) != {"name", "state", "detail"}:
                reject("invalid diagnostic row")
            if row["name"] not in expected or row["state"] not in {"pass", "fail", "not_proven"}:
                reject("unrecognized diagnostic response")
        names = [row["name"] for row in document["results"]]
        if len(names) != len(expected) or set(names) != expected:
            reject("incomplete or duplicate diagnostic results")
        for row in document["results"]:
            print(f"{row['state']}: {row['name']}")
    except Exception:  # noqa: BLE001 - hostile/manager output is never echoed
        print("not_proven: native transient result unavailable or invalid")
        return 2
    states = {row["state"] for row in document["results"]}
    if "fail" in states:
        return 1
    return 2 if "not_proven" in states or completed.returncode else 0


def validate_options(options):
    if options.profile is None:
        reject("explicit deployment profile required")
    if options.mode == "workload":
        if (
            options.profile != "native"
            or not options.acknowledge_disposable
            or not all((options.archive_root, options.archive_id, options.lock_file))
        ):
            reject("explicit native disposable target, UUID and lock required")
        target = canonical_path(options.archive_root)
        production = PurePosixPath("/srv/hfcache")
        if target == production or production in target.parents:
            reject("production archive forbidden")


def main(argv=None):
    options = parser().parse_args(argv)
    if options.mode == "plan" or options.dry_run:
        print(
            "plan only: select --profile and --mode inventory or workload explicitly; "
            "no manager, credential, archive or network access performed"
        )
        return 0
    try:
        validate_options(options)
        if options.wrapper and options.mode == "workload" and not options.native_runtime:
            arguments = sys.argv[1:] if argv is None else argv
            os.execv(  # noqa: S606 - fixed native interpreter after explicit mode/profile validation
                NATIVE_PYTHON,
                [
                    NATIVE_PYTHON,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--native-runtime",
                    *arguments,
                ],
            )
        if options.wrapper and options.mode == "workload":
            with target_scope(options, owner_uid=-1):
                pass
        if options.mode == "inventory" or options.wrapper:
            if options.unit_directory:
                content = (Path(options.unit_directory) / options.unit).read_text()
            else:
                command = ["systemctl"]
                if options.profile != "native":
                    command.append("--user")
                content = subprocess.run(  # noqa: S603 - fixed manager, unit allowlist
                    [*command, "cat", "--no-pager", options.unit],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout
            properties = service_properties(content)
            print("sandbox property inventory; values suppressed; no enforcement claim")
            for key, _ in properties:
                print(key)
            if options.mode == "inventory":
                return 0
            return wrapper_workload(options, properties)
        results = workload(options)
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "scope": "current probe process only",
                    "results": [vars(result) for result in results],
                }
            )
        )
        if any(result.state == "fail" for result in results):
            return 1
        return 2 if any(result.state == "not_proven" for result in results) else 0
    except Exception:  # noqa: BLE001 - never render raw input/dependency/secret exceptions
        print(
            "hardening-probe: refused or not proven; prerequisites/identity/ownership failed",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
