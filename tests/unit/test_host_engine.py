"""Engine proof adversaries; root ownership/IDs are modeled around real owned files.

No local capability or namespace mutation establishes installed acceptance here.
The real fixed Podman read and isolation proof live in the disposable guest lane.
"""

import ctypes
import hashlib
import io
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from hfcache import host_peer as module

STOCK_SHA = "322dffd5a543bb9e1ca9c67cc56999c62b746118674d004180fe60dddfc21979"
STOCK = "/usr/share/containers/storage.conf"
UID = GID = 983
EXPECTED_OVERRIDES = {
    "/etc/containers/storage.conf",
    "/var/lib/hfcache/.config/containers/storage.conf",
    "/var/lib/hfcache/.config/containers/storage.conf.d",
    "/etc/containers/storage.conf.d",
    "/etc/containers/storage.rootless.conf.d",
    "/etc/containers/storage.rootless.conf.d/983",
    "/usr/share/containers/storage.conf.d",
    "/usr/share/containers/storage.rootless.conf.d",
    "/usr/share/containers/storage.rootless.conf.d/983",
}

VENDOR_DROPINS = {
    "/usr/share/containers/storage.conf.d": (
        "00-vendor.conf",
        b'[storage]\ndriver = "overlay"\n',
    ),
    "/usr/share/containers/storage.rootless.conf.d": (
        "00-vendor-rootless.conf",
        (
            b"[storage.options.overlay]\n"
            b"# mountopt specifies comma separated list of extra mount options\n"
            b"# Note unlike the rootful config we cannot use metacopy=on as rootless user\n"
            b'mountopt = "nodev"\n'
        ),
    ),
}


def budget(*, files=1024, size=64 * 1024 * 1024, seconds=2):
    return module._Budget(time.monotonic() + seconds, files, size)


def modeled_root(info):
    return SimpleNamespace(
        **{
            name: 0 if name in {"st_uid", "st_gid"} else getattr(info, name)
            for name in dir(info)
            if name.startswith("st_")
        }
    )


@pytest.fixture
def storage(tmp_path, monkeypatch):
    root = tmp_path / "owned-root"
    root.mkdir()
    leaf = root / STOCK.removeprefix("/")
    leaf.parent.mkdir(parents=True)
    body = b'[storage.options.overlay]\nmountopt = "nodev"\n'
    leaf.write_bytes(body)
    leaf.chmod(0o644)
    for path, (name, contents) in VENDOR_DROPINS.items():
        directory = root / path.removeprefix("/")
        directory.mkdir(mode=0o755)
        target = directory / name
        target.write_bytes(contents)
        target.chmod(0o644)
    opened = set()
    events = []
    original = SimpleNamespace(**{name: getattr(os, name) for name in dir(os)})
    proxy = SimpleNamespace(**{name: getattr(os, name) for name in dir(os)})

    def open_owned(path, flags, *args, **kwargs):
        actual = root if path == "/" else path
        descriptor = original.open(actual, flags, *args, **kwargs)
        opened.add(descriptor)
        events.append(("open", str(path)))
        return descriptor

    def close_owned(descriptor):
        opened.remove(descriptor)
        return original.close(descriptor)

    proxy.open = open_owned
    proxy.close = close_owned
    proxy.fstat = lambda descriptor: modeled_root(original.fstat(descriptor))
    proxy.stat = lambda *args, **kwargs: modeled_root(original.stat(*args, **kwargs))
    proxy.getresuid = lambda: (UID,) * 3
    proxy.getresgid = lambda: (GID,) * 3
    proxy.getgroups = list
    monkeypatch.setattr(module, "os", proxy)
    # A synthetic file exercises capture and race checks; installed acceptance
    # separately requires the real fixed stock digest, asserted below.
    monkeypatch.setattr(module, "_ENGINE_STORAGE_CONFIG_SHA", hashlib.sha256(body).hexdigest())
    yield SimpleNamespace(
        root=root,
        leaf=leaf,
        body=body,
        opened=opened,
        events=events,
        original=original,
        proxy=proxy,
    )
    assert opened == set()


def test_production_stock_digest_and_exact_fixed_override_search_paths():
    assert module._ENGINE_STORAGE_CONFIG_SHA == STOCK_SHA
    assert str(module._ENGINE_STORAGE_CONFIG) == STOCK
    assert {str(path) for path in module._engine_storage_override_paths(UID)} == EXPECTED_OVERRIDES
    for invalid in (0, -1, True, "983", 2**32):
        with pytest.raises(module.PeerError):
            module._engine_storage_override_paths(cast("Any", invalid))


def test_real_owned_stock_capture_is_stable_closed_json_and_charges_shared_budget(storage):
    work = budget()
    first = module._engine_storage_config(UID, GID, work)
    second = module._engine_storage_config(UID, GID, budget())
    assert first == second
    assert json.loads(json.dumps(first)) == first
    assert set(first) == {"schema_version", "stock", "overrides", "original_options"}
    assert first["schema_version"] == 1
    assert first["stock"]["sha256"] == hashlib.sha256(storage.body).hexdigest()
    assert first["original_options"] == ["overlay.mountopt=nodev"]
    assert {item["path"] for item in first["overrides"]} == EXPECTED_OVERRIDES
    absent = [item for item in first["overrides"] if item["state"] == "absent"]
    assert len(absent) == 7
    assert all(type(item["missing_component"]) is int for item in absent)
    vendor = [item for item in first["overrides"] if item["state"] == "stock-directory"]
    assert {item["path"] for item in vendor} == set(VENDOR_DROPINS)
    assert work.files == 12
    assert work.bytes == len(storage.body) + sum(len(row[1]) for row in VENDOR_DROPINS.values())
    assert storage.opened == set()


@pytest.mark.parametrize("path", sorted(EXPECTED_OVERRIDES - VENDOR_DROPINS.keys()))
def test_any_existing_nonvendor_main_override_or_dropin_directory_refuses_including_empty(
    storage, path
):
    target = storage.root / path.removeprefix("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.endswith("storage.conf"):
        target.write_bytes(b"")
    else:
        target.mkdir()
    with pytest.raises(module.PeerError):
        module._engine_storage_config(UID, GID, budget())
    assert storage.opened == set()


def test_override_ancestor_symlink_is_not_followed(storage):
    home = storage.root / "var/lib/hfcache"
    home.mkdir(parents=True)
    outside = storage.root / "outside"
    outside.mkdir()
    (home / ".config").symlink_to(outside, target_is_directory=True)
    with pytest.raises(module.PeerError):
        module._engine_storage_config(UID, GID, budget())
    assert storage.opened == set()
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize(
    "kind", ["wrong-digest", "group-write", "wrong-gid", "hardlink", "symlink", "empty", "oversize"]
)
def test_stock_type_mode_identity_and_byte_pin_refuse_without_loosening_profile(storage, kind):
    if kind == "wrong-digest":
        storage.leaf.write_bytes(b"different stock bytes")
    elif kind == "group-write":
        storage.leaf.chmod(0o664)
    elif kind == "wrong-gid":
        inode = storage.leaf.stat().st_ino

        def changed(descriptor):
            info = modeled_root(storage.original.fstat(descriptor))
            if info.st_ino == inode:
                info.st_gid = GID
            return info

        storage.proxy.fstat = changed
    elif kind == "hardlink":
        os.link(storage.leaf, storage.leaf.with_name("second-link"))
    elif kind == "symlink":
        target = storage.leaf.with_name("ordinary-target")
        storage.leaf.rename(target)
        storage.leaf.symlink_to(target)
    elif kind == "empty":
        storage.leaf.write_bytes(b"")
    elif kind == "oversize":
        storage.leaf.write_bytes(b"x" * (module._ENGINE_STORAGE_MAX + 1))
    with pytest.raises((module.PeerError, OSError)):
        module._engine_storage_config(UID, GID, budget())
    assert storage.opened == set()


def test_stock_replacement_during_actual_fd_read_refuses_even_with_same_bytes(storage):
    original_read = storage.original.read
    replaced = False

    def swapped(descriptor, maximum):
        nonlocal replaced
        body = original_read(descriptor, maximum)
        if body and not replaced:
            replacement = storage.leaf.with_name("replacement")
            replacement.write_bytes(storage.body)
            replacement.chmod(0o644)
            replacement.replace(storage.leaf)
            replaced = True
        return body

    storage.proxy.read = swapped
    with pytest.raises(module.PeerError):
        module._engine_storage_config(UID, GID, budget())
    assert replaced
    assert storage.opened == set()


def test_absence_record_detects_real_parent_metadata_change_between_reads(storage):
    parent = storage.root / "etc/containers"
    parent.mkdir(parents=True)
    first = module._engine_storage_config(UID, GID, budget())
    (parent / "unrelated-owned-marker").write_bytes(b"x")
    second = module._engine_storage_config(UID, GID, budget())
    assert first != second
    assert len([item for item in second["overrides"] if item["state"] == "absent"]) == 7
    assert [item for item in first["overrides"] if item["state"] == "stock-directory"] == [
        item for item in second["overrides"] if item["state"] == "stock-directory"
    ]


@pytest.mark.parametrize(
    "work", [lambda: budget(files=11), lambda: budget(size=1), lambda: budget(seconds=-1)]
)
def test_storage_proof_never_resets_or_exceeds_shared_file_byte_or_time_budget(storage, work):
    with pytest.raises(module.PeerError):
        module._engine_storage_config(UID, GID, work())
    assert storage.opened == set()


@pytest.mark.parametrize(
    ("uid", "gid"), [(0, GID), (UID, 0), (True, GID), (UID, "983"), (UID + 1, GID)]
)
def test_unproved_or_selected_uid_gid_refuse_before_any_file_access(storage, uid, gid):
    with pytest.raises(module.PeerError):
        module._engine_storage_config(uid, gid, budget())
    assert storage.events == []


def test_fixed_engine_environment_has_no_effective_storage_or_xdg_override():
    environment = module._environment(UID)
    overrides = {
        "CONTAINERS_STORAGE_CONF",
        "CONTAINERS_STORAGE_CONF_OVERRIDE",
        "STORAGE_OPTS",
        "STORAGE_DRIVER",
        "XDG_CONFIG_HOME",
        "XDG_CONFIG_DIRS",
        "XDG_DATA_HOME",
    }
    assert not overrides & environment.keys()
    assert environment["HOME"] == "/var/lib/hfcache"
    assert environment["XDG_RUNTIME_DIR"] == "/run/user/983"


def test_real_self_status_capture_uses_numeric_pid_and_never_relaxes_ancestor_nofollow(monkeypatch):
    original_read = module._read
    paths = []

    def observed(path, work, *, maximum, protected=False):
        paths.append(str(path))
        assert str(path) == f"/proc/{os.getpid()}/status"
        body = original_read(path, work, maximum=maximum, protected=protected)
        # Only security-state values are modeled; the actual self-proc open and
        # bounded nofollow walker run unprivileged in the owned test process.
        lines = []
        for line in body.splitlines():
            key = line.partition(b":")[0]
            rendered = line
            if key in {b"NoNewPrivs", b"Seccomp", b"Seccomp_filters"}:
                value = b"2" if key == b"Seccomp" else b"1"
                rendered = key + b":\t" + value
            lines.append(rendered)
        return b"\n".join(lines) + b"\n"

    monkeypatch.setattr(module, "_read", observed)
    value = module._engine_status(budget())
    assert value["NoNewPrivs"] == 1
    assert value["Seccomp"] == 2
    assert paths == [f"/proc/{os.getpid()}/status"]


def test_fixed_inspection_argv_has_no_info_or_mutation_or_resource_selector():
    assert module._engine_argv() == [
        "/usr/bin/podman",
        "--remote=false",
        "--storage-opt=overlay.mountopt=nodev",
        "--storage-opt=overlay.skip_mount_home=true",
        "container",
        "inspect",
        "hfcache-api",
    ]
    assert "info" not in module._engine_argv()


class CapabilityKernel:
    def __init__(self, *, extra_readback=None, missing_readback=None):
        self.events = []
        self.words = None
        self.extra_readback = extra_readback
        self.missing_readback = missing_readback

    def prctl(self, operation, argument, *remaining):
        assert remaining == (0, 0, 0)
        self.events.append(("prctl", operation, argument))
        if operation == 23:
            return int(
                argument in {2, 21, self.extra_readback} and argument != self.missing_readback
            )
        if operation == 27:
            return 0xCE
        return 0

    def capset(self, _header, data):
        self.words = list(ctypes.cast(data, ctypes.POINTER(ctypes.c_uint32 * 6)).contents)
        self.events.append(("capset",))
        return 0


@pytest.mark.parametrize("last", [21, 40, 63])
def test_simulated_namespace_capabilities_drop_every_other_bit_and_lock_exact_exec_state(last):
    kernel = CapabilityKernel()
    module._engine_capabilities(cast("Any", kernel), last)
    dropped = [("prctl", 24, value) for value in range(last + 1) if value not in {2, 21}]
    boundary = len(dropped) + last + 1
    assert kernel.events[: len(dropped)] == dropped
    assert kernel.events[len(dropped) : boundary] == [
        ("prctl", 23, value) for value in range(last + 1)
    ]
    assert kernel.events[boundary:] == [
        ("prctl", 47, 4),
        ("prctl", 28, 0xCE),
        ("capset",),
        ("prctl", 27, 0),
    ]
    assert kernel.words == [0x200004, 0x200004, 0, 0, 0, 0]


@pytest.mark.parametrize("last", [0, 20, 64])
def test_unsupported_kernel_capability_limit_refuses_without_changing_bits(last):
    kernel = CapabilityKernel()
    with pytest.raises(module.PeerError):
        module._engine_capabilities(cast("Any", kernel), last)
    assert kernel.events == []


def test_nonzero_other_bounding_readback_refuses_before_capset():
    kernel = CapabilityKernel(extra_readback=8)
    with pytest.raises(module.PeerError):
        module._engine_capabilities(cast("Any", kernel), 40)
    assert kernel.words is None
    assert ("prctl", 28, 0xCE) not in kernel.events


@pytest.fixture
def entered_engine(monkeypatch):
    original_namespaces = {name: index + 100 for index, name in enumerate(module._NAMESPACES)}
    expected_namespaces = original_namespaces | {"user": 500}
    state = {
        "CapEff": 0x200004,
        "CapPrm": 0x200004,
        "CapBnd": 0x200004,
        "CapInh": 0,
        "CapAmb": 0,
        "NoNewPrivs": 1,
        "Seccomp": 2,
        "Seccomp_filters": 24,
    }
    prepared = {
        "keeper": {"user_inode": 500},
        "namespaces": original_namespaces,
        "seccomp_filters": 24,
    }
    events: list[tuple[Any, ...]] = []

    class Kernel:
        refused_join = False

        def setns(self, fd, flags):
            events.append(("setns", fd, flags))
            if fd == 123:
                assert flags == 0x10000000
                return -1 if self.refused_join else 0
            assert fd == -1
            assert flags in {0, 0x20000}
            ctypes.set_errno(1)
            return -1

        def unshare(self, flags):
            events.append(("unshare", flags))
            assert flags == 0x20000
            ctypes.set_errno(1)
            return -1

    kernel = Kernel()
    proxy = SimpleNamespace(**{name: getattr(os, name) for name in dir(os)})
    proxy.getresuid = lambda: (0, 0, 0)
    proxy.getresgid = lambda: (0, 0, 0)
    proxy.getgroups = list
    proxy.close = lambda fd: events.append(("close", fd))
    monkeypatch.setattr(module, "os", proxy)
    monkeypatch.setattr(module.ctypes, "CDLL", lambda *_args, **_kwargs: kernel)
    monkeypatch.setattr(
        module,
        "_read",
        lambda path, *_args, **_kwargs: (
            b"40\n" if str(path) == "/proc/sys/kernel/cap_last_cap" else b""
        ),
    )
    monkeypatch.setattr(module, "_engine_user_fd", lambda *_args: 123)
    monkeypatch.setattr(
        module, "_engine_capabilities", lambda _libc, last: events.append(("capabilities", last))
    )
    monkeypatch.setattr(module, "_engine_namespaces", lambda *_args: expected_namespaces)
    monkeypatch.setattr(module, "_engine_status", lambda *_args: state)
    return SimpleNamespace(
        prepared=prepared, namespaces=expected_namespaces, state=state, events=events, kernel=kernel
    )


def test_simulated_typed_entry_closes_user_fd_and_retains_every_other_namespace(entered_engine):
    result = module._engine_enter(entered_engine.prepared, budget())
    assert entered_engine.events[:3] == [
        ("setns", 123, 0x10000000),
        ("close", 123),
        ("capabilities", 40),
    ]
    assert result["namespaces"] == entered_engine.namespaces
    assert result["mount_transitions_denied"] is True
    assert entered_engine.events[-3:] == [
        ("unshare", 0x20000),
        ("setns", -1, 0x20000),
        ("setns", -1, 0),
    ]


@pytest.mark.parametrize("failure", ["join", "mnt", "capabilities", "filters"])
def test_simulated_entry_refuses_changed_join_mount_capability_or_filter_state(
    entered_engine, failure
):
    if failure == "join":
        entered_engine.kernel.refused_join = True
    elif failure == "mnt":
        entered_engine.namespaces["mnt"] += 1
    elif failure == "capabilities":
        entered_engine.state["CapEff"] |= 1 << 7
    else:
        entered_engine.state["Seccomp_filters"] -= 1
    with pytest.raises(module.PeerError):
        module._engine_enter(entered_engine.prepared, budget())
    assert ("close", 123) in entered_engine.events
    assert not any(event[0] == "unshare" for event in entered_engine.events)


def owned_elf(storage):
    path = storage.root / "usr/bin/podman"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x7fELFowned synthetic executable header only")
    path.chmod(0o755)
    return path


def test_real_owned_binary_capture_pins_fd_without_hashing_large_binary(storage):
    path = owned_elf(storage)
    work = budget()
    descriptor, identity = module._engine_binary(work)
    try:
        assert identity["inode"] == path.stat().st_ino
        assert identity["bytes"] == path.stat().st_size
        assert not os.get_inheritable(descriptor)
        assert work.bytes == 4
        assert descriptor in storage.opened
    finally:
        module.os.close(descriptor)
    assert storage.opened == set()


@pytest.mark.parametrize(
    "failure", ["nonelf", "setuid", "setgid", "writable", "filecap", "unknown-xattr"]
)
def test_binary_refuses_unproved_elf_mode_or_filecap_without_fd_leak(storage, failure):
    path = owned_elf(storage)
    if failure == "nonelf":
        path.write_bytes(b"not an ELF file")
    elif failure == "setuid":
        path.chmod(0o4755)
    elif failure == "setgid":
        path.chmod(0o2755)
    elif failure == "writable":
        path.chmod(0o775)
    elif failure == "filecap":
        storage.proxy.getxattr = lambda *_args: b"modeled file capability"
    else:

        def unsupported(*_args):
            raise OSError(95, "modeled unsupported xattr")

        storage.proxy.getxattr = unsupported
    with pytest.raises(module.PeerError):
        module._engine_binary(budget())
    assert storage.opened == set()


class ReachedFixedExecError(Exception):
    pass


def configure_engine_exec(storage, monkeypatch, case):
    path = owned_elf(storage)
    descriptor, identity = module._engine_binary(budget())
    module.os.close(descriptor)
    deployment = {"profile": "rootless", "api_principal": {"host_uid": UID, "host_gid": GID}}
    deployment_body = json.dumps(deployment).encode()
    prepared = {"binary": identity, "account_home": "/var/lib/hfcache"}
    entered = False
    reads = 0
    calls = []
    output = io.BytesIO()
    original_fstat = storage.proxy.fstat

    def projected(descriptor):
        info = original_fstat(descriptor)
        if entered and info.st_ino == path.stat().st_ino:
            info.st_uid = info.st_gid = 0 if case == "unexpected-owner" else 65534
            if case == "inode-swap":
                info.st_ino += 1
        return info

    storage.proxy.fstat = projected

    def execute(descriptor, argv, environment):
        calls.append((descriptor, argv, environment))
        raise ReachedFixedExecError

    storage.proxy.execve = execute
    storage.proxy.supports_fd = {execute}

    def read(path, *_args, **_kwargs):
        nonlocal reads
        if path == module.DEPLOYMENT:
            reads += 1
            return deployment_body + (b" " if case == "deployment-swap" and reads > 1 else b"")
        assert str(path) == f"/proc/{os.getpid()}/stat"
        return Path(f"/proc/{os.getpid()}/stat").read_bytes()

    def enter(*_args):
        nonlocal entered
        entered = True
        return {"simulated_transition": True}

    monkeypatch.setattr(module, "_read", read)
    monkeypatch.setattr(module, "_engine_prepare", lambda *_args: prepared)
    monkeypatch.setattr(module, "_engine_enter", enter)
    monkeypatch.setattr(
        module,
        "sys",
        SimpleNamespace(
            stdin=SimpleNamespace(
                buffer=io.BytesIO(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "remaining_seconds": 1.0,
                            "maximum_files": 1024,
                            "maximum_bytes": 64 * 1024 * 1024,
                        }
                    ).encode()
                )
            ),
            stdout=SimpleNamespace(buffer=output),
        ),
    )
    monkeypatch.setattr(
        module,
        "signal",
        SimpleNamespace(
            SIGALRM=14, ITIMER_REAL=0, signal=lambda *_args: None, setitimer=lambda *_args: None
        ),
    )
    return SimpleNamespace(calls=calls, output=output, identity=identity)


@pytest.mark.parametrize(
    "case", ["translated", "inode-swap", "unexpected-owner", "deployment-swap"]
)
def test_engine_exec_closes_fd_and_preserves_stable_identity_across_modeled_uid_projection(
    storage, monkeypatch, case
):
    configured = configure_engine_exec(storage, monkeypatch, case)
    expected_error = ReachedFixedExecError if case == "translated" else module.PeerError
    with pytest.raises(expected_error):
        module.observe_engine()
    assert storage.opened == set()
    if case == "translated":
        assert len(configured.calls) == 1
        _, argv, environment = configured.calls[0]
        assert argv == module._engine_argv()
        assert "info" not in argv
        assert environment == module._environment(UID) | {
            "_CONTAINERS_USERNS_CONFIGURED": "done",
            "_CONTAINERS_ROOTLESS_UID": "983",
            "_CONTAINERS_ROOTLESS_GID": "983",
        }
        preamble = json.loads(configured.output.getvalue())
        assert preamble["process"]["pid"] == os.getpid()
        assert preamble["process"]["start_ticks"] > 0
        assert preamble["prepared"]["binary"] == configured.identity
    else:
        assert configured.calls == []
        assert configured.output.getvalue() == b""


@pytest.mark.parametrize("missing", [2, 21])
def test_missing_required_namespace_bounding_bit_refuses_before_capset(missing):
    kernel = CapabilityKernel(missing_readback=missing)
    with pytest.raises(module.PeerError):
        module._engine_capabilities(cast("Any", kernel), 40)
    assert kernel.words is None
    assert ("prctl", 28, 0xCE) not in kernel.events


@pytest.mark.parametrize("field", ["CapEff", "CapPrm", "CapBnd"])
@pytest.mark.parametrize("wrong", [0, 4, 1 << 21, 0x200005, 0xC0, True])
def test_typed_entry_requires_exact_two_namespace_bits(entered_engine, field, wrong):
    entered_engine.state[field] = wrong
    with pytest.raises(module.PeerError):
        module._engine_enter(entered_engine.prepared, budget())
    assert ("close", 123) in entered_engine.events
    assert not any(event[0] == "unshare" for event in entered_engine.events)
