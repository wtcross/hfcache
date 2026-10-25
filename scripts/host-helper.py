#!/usr/bin/python3 -I
"""Decision150 fixed protected host reads; --help has no host effects.

This foreground service loads only root-protected standard-library bootstrap
copies. It never accepts a path, unit, manager, UID or executable from a request.
Every write opcode remains denied. Host Python3.12 is supported.
"""

from __future__ import annotations

import argparse
import builtins
import ctypes
import hashlib
import json
import os
import signal
import socket
import stat
import sys
import threading
import time
import types
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

LIBRARY = Path("/usr/local/lib/hfcache-host-helper")
PARENT = Path("/run/hfcache-host-helper/api")
SOCKET_NAME = "helper.sock"
BINDING_NAME = "binding.json"
MAX_MODULE_BYTES = 2 * 1024 * 1024
MAX_EXCHANGES = 8
PARENT_MODE = 0o750
BINDING_MODE = 0o440
MAX_BINDING_BYTES = 4096
MAX_NOTIFY_BYTES = 256
MAX_OBSERVER_BYTES = 1048576
MAX_STARTUP_STATUS_BYTES = 65536
MAX_FAILURE_BYTES = 8192
MAX_FAILURE_ERRORS = 4
MAX_FAILURE_FRAMES = 8
MAX_FAILURE_TRACEBACK = 64
MAX_FAILURE_FUNCTION = 64
MAX_FAILURE_LINE = 1000000
MAX_FAILURE_ERRNO = 4095
_ACCOUNT_CAPABILITIES = 0xC0
_CAPABILITY_HEX_WIDTH = 16
_STARTUP_INTEGER_WIDTH = 10
_SECCOMP_FILTER_MODE = 2
_OPERATION_DENIED = "operation-denied"


def refuse(condition, message="protected host helper refused"):
    if not condition:
        raise ValueError(message)


_STARTUP_SELINUX_CONTEXT = b"system_u:system_r:hfcache_host_helper_t:s0"
_STARTUP_SECURITY_MAX = 4096


def startup_security_read(path, *, owner):
    """Read only a fixed kernel SELinux attribute; no ordinary-file size assumption."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        refuse(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_uid in owner)
        body = os.read(descriptor, _STARTUP_SECURITY_MAX + 1)
        refuse(0 < len(body) <= _STARTUP_SECURITY_MAX)
        fields = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_nlink")
        expected = tuple(getattr(before, field) for field in fields)
        refuse(tuple(getattr(os.fstat(descriptor), field) for field in fields) == expected)
        refuse(tuple(getattr(path.lstat(), field) for field in fields) == expected)
        return body
    finally:
        os.close(descriptor)


def require_startup_domain():
    """Decision150 requires the confined domain from first fixed entry exec."""
    enforcing = startup_security_read(Path("/sys/fs/selinux/enforce"), owner={0})
    refuse(enforcing in {b"1", b"1\n"})
    context = startup_security_read(
        Path(f"/proc/{os.getpid()}/attr/current"), owner={0, os.getuid()}
    )
    # SELinux's procattr ABI may include one terminal NUL. Accept only the exact
    # canonical context and these single, explicit kernel/text terminators.
    refuse(context in {_STARTUP_SELINUX_CONTEXT + tail for tail in (b"", b"\x00", b"\n")})
    return {"files": 2, "bytes": len(enforcing) + len(context)}


def startup_status():
    """Bounded self-proc facts only; never open protected authority yet."""
    descriptor = os.open(
        "/proc/self/status", os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
    )
    body = bytearray()
    try:
        while len(body) <= MAX_STARTUP_STATUS_BYTES:
            part = os.read(descriptor, min(65536, MAX_STARTUP_STATUS_BYTES + 1 - len(body)))
            if not part:
                break
            body.extend(part)
        refuse(len(body) <= MAX_STARTUP_STATUS_BYTES)
    finally:
        os.close(descriptor)
    capabilities = {"CapEff", "CapPrm", "CapBnd", "CapInh", "CapAmb"}
    required = capabilities | {"NoNewPrivs", "Seccomp", "Seccomp_filters"}
    values = {}
    for line in body.decode("ascii").splitlines():
        key, separator, raw = line.partition(":")
        if key not in required:
            continue
        refuse(separator and key not in values)
        raw = raw.strip()
        if key in capabilities:
            refuse(
                len(raw) == _CAPABILITY_HEX_WIDTH
                and all(char in "0123456789abcdef" for char in raw)
            )
            values[key] = int(raw, 16)
        else:
            refuse(1 <= len(raw) <= _STARTUP_INTEGER_WIDTH and raw.isascii() and raw.isdecimal())
            values[key] = int(raw)
    refuse(set(values) == required)
    return values, len(body)


def startup_task():
    """Read at most two self-task entries; more than one refuses startup."""
    descriptor = os.open(
        "/proc/self/task", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    )
    try:
        with os.scandir(descriptor) as entries:
            first = next(entries, None)
            own_name = str(os.getpid())
            refuse(first is not None and first.name == own_name)
            refuse(next(entries, None) is None)
            return len(own_name.encode("ascii"))
    finally:
        os.close(descriptor)


def startup_principal():
    uid, gid = os.getresuid(), os.getresgid()
    if uid == (0, 0, 0):
        refuse(gid == (0, 0, 0) and all(group == 0 for group in os.getgroups()))
        return True
    refuse(
        uid[0] > 0
        and uid == (uid[0],) * 3
        and gid[0] > 0
        and gid == (gid[0],) * 3
        and not os.getgroups()
    )
    return False


def clear_startup_capabilities():
    """Erase temporary I/A before loading modules, threads or delegated code.

    Only the managed root branch may retain SETUID/SETGID in P/E. Delegated
    non-root observation retains neither; its indexed principal is checked by
    the existing observer after this common bootstrap. Initial I/A need not be
    the service's ambient SETUID request: legitimate children already have zero.
    """
    root = startup_principal()
    task_bytes = startup_task()
    before, before_bytes = startup_status()
    expected = _ACCOUNT_CAPABILITIES if root else 0
    refuse(
        before["CapEff"] == before["CapPrm"] == expected
        and before["CapBnd"] == _ACCOUNT_CAPABILITIES
        and before["NoNewPrivs"] == 1
        and before["Seccomp"] == _SECCOMP_FILTER_MODE
        and before["Seccomp_filters"] > 0
    )

    class Header(ctypes.Structure):
        _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]

    class Data(ctypes.Structure):
        _fields_ = [
            ("effective", ctypes.c_uint32),
            ("permitted", ctypes.c_uint32),
            ("inheritable", ctypes.c_uint32),
        ]

    libc = ctypes.CDLL(None, use_errno=True)
    header = Header(0x20080522, 0)
    data = (Data * 2)()
    refuse(libc.capget(ctypes.byref(header), ctypes.byref(data)) == 0)
    for field, key in (
        ("effective", "CapEff"),
        ("permitted", "CapPrm"),
        ("inheritable", "CapInh"),
    ):
        refuse(getattr(data[0], field) | (getattr(data[1], field) << 32) == before[key])
    refuse(libc.prctl(47, 4, 0, 0, 0) == 0)  # PR_CAP_AMBIENT_CLEAR_ALL
    data[0].inheritable = data[1].inheritable = 0
    refuse(libc.capset(ctypes.byref(header), ctypes.byref(data)) == 0)
    after, after_bytes = startup_status()
    refuse(startup_principal() == root)
    task_bytes += startup_task()
    refuse(after["CapInh"] == after["CapAmb"] == 0)
    refuse(
        all(after[key] == value for key, value in before.items() if key not in {"CapInh", "CapAmb"})
    )
    return {"files": 4, "bytes": before_bytes + after_bytes + task_bytes}


def trusted_read(path, maximum=MAX_MODULE_BYTES):
    """Capture one fixed ordinary root-owned leaf through protected parents."""
    refuse(path.is_absolute() and ".." not in path.parts)
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    descriptor = -1
    try:
        for part in path.parent.parts[1:]:
            facts = os.fstat(parent)
            refuse(facts.st_uid == 0 and not facts.st_mode & 0o022)
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
            )
            os.close(parent)
            parent = child
        facts = os.fstat(parent)
        refuse(facts.st_uid == 0 and not facts.st_mode & 0o022)
        descriptor = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent
        )
        before = os.fstat(descriptor)
        refuse(
            stat.S_ISREG(before.st_mode)
            and before.st_uid == 0
            and not before.st_mode & 0o022
            and before.st_nlink == 1
            and 0 < before.st_size <= maximum
        )
        body = bytearray()
        while len(body) <= maximum:
            part = os.read(descriptor, min(65536, maximum + 1 - len(body)))
            if not part:
                break
            body.extend(part)
        after = os.fstat(descriptor)
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
        refuse(
            len(body) == before.st_size
            and all(getattr(before, key) == getattr(after, key) for key in fields)
        )
        leaf = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        refuse((leaf.st_dev, leaf.st_ino) == (before.st_dev, before.st_ino))
        return bytes(body)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def load_modules():
    """Root protection precedes import; selected-index hashes precede admission."""
    modules, hashes = {}, {}
    work = {"files": 0, "bytes": 0}
    for name in ("host_protocol", "host_policy", "host_peer"):
        path = LIBRARY / (name + ".py")
        body = trusted_read(path)
        work["files"] += 1
        work["bytes"] += len(body)
        module = types.ModuleType("hfcache_protected_" + name)
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        exec(compile(body, str(path), "exec"), module.__dict__)  # noqa: S102 - captured protected fixed code
        modules[name] = module
        hashes[name] = hashlib.sha256(body).hexdigest()
    body = trusted_read(Path(__file__))
    work["files"] += 1
    work["bytes"] += len(body)
    hashes["helper_daemon"] = hashlib.sha256(body).hexdigest()
    return modules, hashes, work


def verify_bootstrap(snapshot, hashes):
    bindings = snapshot.deployment["bindings"]
    expected = {
        "helper_daemon": "helper_daemon",
        "host_policy": "helper_policy_module",
        "host_protocol": "helper_protocol_module",
        "host_peer": "helper_peer_module",
    }
    refuse(all(hashes[name] == bindings[role] for name, role in expected.items()))


def own_start_ticks():
    body = Path("/proc/self/stat").read_text()
    return int(body.rpartition(") ")[2].split()[19])


def current_boot():
    body = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    refuse(str(uuid.UUID(body)) == body)
    return body


def parent_descriptor(gid):
    """Create only our fixed empty parent; never replace an unexplained entry."""
    path = PARENT.parent
    outer = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            facts = os.fstat(outer)
            refuse(facts.st_uid == 0 and not facts.st_mode & 0o022)
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=outer
            )
            os.close(outer)
            outer = child
        facts = os.fstat(outer)
        refuse(facts.st_uid == 0 and not facts.st_mode & 0o022)
        try:
            facts = os.stat(PARENT.name, dir_fd=outer, follow_symlinks=False)
        except FileNotFoundError:
            original_gid = os.getegid()
            try:
                os.setegid(gid)
                os.mkdir(PARENT.name, PARENT_MODE, dir_fd=outer)
            finally:
                os.setegid(original_gid)
            os.chmod(PARENT.name, PARENT_MODE, dir_fd=outer, follow_symlinks=False)
            facts = os.stat(PARENT.name, dir_fd=outer, follow_symlinks=False)
        refuse(
            stat.S_ISDIR(facts.st_mode)
            and facts.st_uid == 0
            and facts.st_gid == gid
            and stat.S_IMODE(facts.st_mode) == PARENT_MODE
        )
        parent = os.open(
            PARENT.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=outer
        )
        try:
            opened = os.fstat(parent)
            refuse((opened.st_dev, opened.st_ino) == (facts.st_dev, facts.st_ino))
            with os.scandir(parent) as entries:
                refuse(next(entries, None) is None)
        except BaseException:
            os.close(parent)
            raise
        return parent
    finally:
        os.close(outer)


def write_binding(parent, binding, gid):
    raw = json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("ascii")
    refuse(len(raw) <= MAX_BINDING_BYTES)
    descriptor = -1
    original_gid = os.getegid()
    try:
        os.setegid(gid)
        descriptor = os.open(
            BINDING_NAME,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            BINDING_MODE,
            dir_fd=parent,
        )
    finally:
        os.setegid(original_gid)
    try:
        os.fchmod(descriptor, BINDING_MODE)
        offset = 0
        while offset < len(raw):
            wrote = os.write(descriptor, raw[offset:])
            refuse(wrote > 0)
            offset += wrote
        os.fsync(descriptor)
        facts = os.fstat(descriptor)
        refuse(
            facts.st_uid == 0
            and facts.st_gid == gid
            and stat.S_IMODE(facts.st_mode) == BINDING_MODE
        )
        os.fsync(parent)
        return (facts.st_dev, facts.st_ino)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def remove_owned(parent, name, identity):
    """A substituted or missing inode is preserved; absence is not ownership."""
    if identity is None:
        return
    try:
        facts = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return
    if (facts.st_dev, facts.st_ino) == identity:
        os.unlink(name, dir_fd=parent)
        os.fsync(parent)


def notify_ready():
    address = os.environ.get("NOTIFY_SOCKET")
    if address is None:
        return
    refuse(
        0 < len(address) <= MAX_NOTIFY_BYTES and "\0" not in address and address[0] in ("/", "@")
    )
    target = "\0" + address[1:] if address.startswith("@") else address
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notification:
        notification.settimeout(2)
        refuse(notification.sendto(b"READY=1", target) == len(b"READY=1"))


class HostDaemon:
    """Eight reserved exchanges, no queued inspection jobs or effect opcodes."""

    def __init__(self, modules, hashes):
        self.protocol = modules["host_protocol"]
        self.policy = modules["host_policy"]
        self.peers = modules["host_peer"]
        self.hashes = hashes
        self.stop = threading.Event()
        self.capacity = threading.BoundedSemaphore(MAX_EXCHANGES)
        self.executor = ThreadPoolExecutor(
            max_workers=MAX_EXCHANGES, thread_name_prefix="hfcache-host-read"
        )
        self.parent = -1
        self.deployment_sha256: str | None = None
        self.socket_identity: tuple[int, int] | None = None
        self.binding_identity: tuple[int, int] | None = None

    def exchange(self, connection):
        snapshot: Any = None
        first_peer: Any = None
        try:

            def authenticate(peer, seconds):
                nonlocal snapshot, first_peer
                if snapshot is None:
                    budget = self.policy.InspectionBudget(
                        deadline_ns=time.monotonic_ns() + int(seconds * 1_000_000_000)
                    )
                    snapshot = self.policy.inspect_authority(budget=budget)
                    refuse(snapshot.deployment_sha256 == self.deployment_sha256)
                    verify_bootstrap(snapshot, self.hashes)
                    first_peer = self.peers.authenticate(
                        snapshot,
                        peer,
                        remaining_seconds=min(seconds, snapshot.budget.remaining(15.0)),
                    )
                else:
                    snapshot.budget.deadline_ns = min(
                        snapshot.budget.deadline_ns,
                        time.monotonic_ns() + int(seconds * 1_000_000_000),
                    )
                    self.policy.revalidate(snapshot)
                    verify_bootstrap(snapshot, self.hashes)
                    self.peers.revalidate(
                        first_peer,
                        snapshot,
                        peer,
                        remaining_seconds=min(seconds, snapshot.budget.remaining(15.0)),
                    )
                return snapshot

            def dispatch(request, authority, seconds):
                authority.budget.deadline_ns = min(
                    authority.budget.deadline_ns, time.monotonic_ns() + int(seconds * 1_000_000_000)
                )
                self.policy.revalidate(authority)
                if request.operation == "status":
                    return authority.status()
                if request.operation == "config-read":
                    return self.policy.read_config_base(authority)
                raise self.protocol.HostProtocolError(_OPERATION_DENIED)  # noqa: TRY301 - closed dispatch boundary

            with connection:
                with self.protocol.receive_exchange(connection, authenticate) as exchange:
                    try:
                        body = exchange.dispatch(dispatch)
                    except self.policy.InspectionError as error:
                        if error.reason != _OPERATION_DENIED:
                            raise
                        exchange.respond(outcome="denied", body={}, reason=_OPERATION_DENIED)
                    else:
                        exchange.respond(outcome="ok", body=body)
        except Exception:  # noqa: BLE001 - refused/unknown input closes; never echo external errors
            return
        finally:
            connection.close()
            self.capacity.release()

    def serve(self):
        refuse(os.getuid() == os.geteuid() == 0 and os.getgid() == os.getegid() == 0)
        startup = self.policy.inspect_authority()
        verify_bootstrap(startup, self.hashes)
        self.deployment_sha256 = startup.deployment_sha256
        gid = startup.api_principal[1]
        self.parent = parent_descriptor(gid)
        parent = os.fstat(self.parent)
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.protocol.configure_listener(listener)
            original_gid = os.getegid()
            try:
                os.setegid(gid)
                listener.bind(f"/proc/self/fd/{self.parent}/{SOCKET_NAME}")
            finally:
                os.setegid(original_gid)
            facts = os.stat(SOCKET_NAME, dir_fd=self.parent, follow_symlinks=False)
            self.socket_identity = (facts.st_dev, facts.st_ino)
            refuse(stat.S_ISSOCK(facts.st_mode) and facts.st_uid == 0 and facts.st_gid == gid)
            os.chmod(SOCKET_NAME, 0o660, dir_fd=self.parent, follow_symlinks=False)
            binding = {
                "schema_version": 1,
                "boot_id": current_boot(),
                "helper_generation": uuid.uuid4().hex,
                "deployment_sha256": startup.deployment_sha256,
                "policy_sha256": startup.policy_sha256,
                "parent": {
                    "device": parent.st_dev,
                    "inode": parent.st_ino,
                    "uid": 0,
                    "gid": gid,
                    "mode": 0o750,
                },
                "helper": {
                    "pid": os.getpid(),
                    "start_ticks": own_start_ticks(),
                    "uid": 0,
                    "gid": 0,
                },
            }
            self.binding_identity = write_binding(self.parent, binding, gid)
            listener.listen(MAX_EXCHANGES)
            listener.settimeout(0.2)
            notify_ready()
            while not self.stop.is_set():
                try:
                    connection, _ = listener.accept()
                except TimeoutError:
                    continue
                if not self.capacity.acquire(blocking=False):
                    connection.close()
                    continue
                try:
                    self.executor.submit(self.exchange, connection)
                except BaseException:
                    self.capacity.release()
                    connection.close()
                    raise
        finally:
            listener.close()
            # Timeout is not drainage. Leave the process/slot owned until every
            # read inspector actually exits; the unit has no forced stop limit.
            self.executor.shutdown(wait=True, cancel_futures=False)
            remove_owned(self.parent, SOCKET_NAME, self.socket_identity)
            remove_owned(self.parent, BINDING_NAME, self.binding_identity)
            os.close(self.parent)
            self.parent = -1


def failure_metadata(error, operation):
    """Decision150: bounded code locations only, including suppressed contexts."""
    if operation not in {"serve", "observe-peer", "observe-guard", "observe-engine"}:
        operation = "unknown"
    protected = {str(Path(__file__)): "host-helper"}
    protected.update(
        {
            str(LIBRARY / (name + ".py")): name
            for name in ("host_peer", "host_policy", "host_protocol")
        }
    )
    classes = {
        kind: kind.__name__
        for kind in vars(builtins).values()
        if isinstance(kind, type) and issubclass(kind, Exception)
    }
    pending = [error]
    seen = set()
    records = []
    while pending and len(records) < MAX_FAILURE_ERRORS:
        current = pending.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        error_class = next(
            (classes[kind] for kind in type(current).__mro__ if kind in classes), "Exception"
        )
        number = current.errno if isinstance(current, OSError) else None
        if type(number) is not int or not 0 <= number <= MAX_FAILURE_ERRNO:
            number = None
        frames = []
        trace = current.__traceback__
        for _ in range(MAX_FAILURE_TRACEBACK):
            if trace is None:
                break
            code = trace.tb_frame.f_code
            module = protected.get(code.co_filename)
            name = code.co_name
            if (
                module is not None
                and len(frames) < MAX_FAILURE_FRAMES
                and (
                    name == "<module>"
                    or (
                        name.isascii() and name.isidentifier() and len(name) <= MAX_FAILURE_FUNCTION
                    )
                )
                and 0 < trace.tb_lineno <= MAX_FAILURE_LINE
            ):
                frames.append({"module": module, "function": name, "line": trace.tb_lineno})
            trace = trace.tb_next
        records.append({"error_class": error_class, "errno": number, "frames": frames})
        pending.extend(
            linked
            for linked in (current.__cause__, current.__context__)
            if isinstance(linked, BaseException)
        )
    return {"operation": operation, "errors": records}


def log_failure(error, operation):
    """Operator stderr only; logging must never replace the original exit status."""
    try:
        sys.stderr.write(
            "protected host helper unavailable; preserve state and inspect fixed prerequisites\n"
        )
        body = json.dumps(
            failure_metadata(error, operation), separators=(",", ":"), ensure_ascii=True
        )
        if len(body) <= MAX_FAILURE_BYTES:
            sys.stderr.write("protected host helper failure " + body + "\n")
    except Exception:  # noqa: BLE001 - unavailable stderr must not replace the original refusal
        return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=("serve", "observe-peer", "observe-guard", "observe-engine")
    )
    args = parser.parse_args()
    try:
        started_at = time.monotonic()
        if args.operation in {"serve", "observe-guard"}:
            refuse(os.getuid() == os.geteuid() == 0)
        security_work = require_startup_domain()
        startup_work = clear_startup_capabilities()
        for key in ("files", "bytes"):
            startup_work[key] += security_work[key]
        modules, hashes, bootstrap_work = load_modules()
        for key in ("files", "bytes"):
            bootstrap_work[key] += startup_work[key]
        if args.operation == "observe-engine":
            modules["host_peer"].observe_engine(
                bootstrap_work=bootstrap_work, started_at=started_at
            )
            refuse(False)  # noqa: FBT003 - a fixed exec must replace this child
        if args.operation in {"observe-peer", "observe-guard"}:
            observer = (
                modules["host_peer"].observe_peer
                if args.operation == "observe-peer"
                else modules["host_policy"].observe_guard
            )
            result = observer(bootstrap_work=bootstrap_work, started_at=started_at)
            body = modules["host_protocol"].encode_object(result)
            refuse(len(body) <= MAX_OBSERVER_BYTES)
            sys.stdout.buffer.write(body + b"\n")
            return 0
        daemon = HostDaemon(modules, hashes)
        signal.signal(signal.SIGTERM, lambda _signum, _frame: daemon.stop.set())
        signal.signal(signal.SIGINT, lambda _signum, _frame: daemon.stop.set())
        daemon.serve()
    except Exception as error:  # noqa: BLE001 - fixed redacted operator diagnostic only
        log_failure(error, args.operation)
        return 20
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
