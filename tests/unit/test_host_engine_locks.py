"""Owned FD and modeled-label checks; no guest or SELinux acceptance."""

import json
import os
import stat
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from hfcache import host_peer as module
from hfcache import host_policy as policy

UID = GID = 983
CONTEXT = b"unconfined_u:object_r:hfcache_host_helper_engine_lock_t:s0"


def budget(files=1024, size=65536, seconds=5):
    return module._Budget(time.monotonic() + seconds, files, size)


@pytest.fixture
def locks(tmp_path, monkeypatch):
    root = tmp_path / "owned-root"
    root.mkdir()
    originals = SimpleNamespace(**{name: getattr(os, name) for name in dir(os)})
    proxy = SimpleNamespace(**{name: getattr(os, name) for name in dir(os)})
    leaves = []
    for fixed, length in module._engine_lock_specs(UID):
        path = root / fixed.relative_to("/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"n" * length)
        path.chmod(0o644)
        originals.setxattr(path, "user.web006_context", CONTEXT)
        leaves.append(path)
    leaf_inodes = {path.stat().st_ino for path in leaves}
    runtime = root / "run/user" / str(UID)
    runtime_inodes = {runtime.stat().st_ino, *(p.stat().st_ino for p in runtime.rglob("*"))}
    for parent in (
        runtime,
        runtime / "libpod",
        runtime / "libpod/tmp",
        runtime / "containers",
        runtime / "containers/overlay-layers",
    ):
        parent.chmod(0o700)
    ancestor_owner, ancestor_group = [UID], [GID]
    owner, group = [UID], [GID]
    opened, events = set(), []
    hook = [lambda _descriptor: None]

    def modeled(info):
        values = {name: getattr(info, name) for name in dir(info) if name.startswith("st_")}
        values["st_uid"] = (
            owner[0]
            if info.st_ino in leaf_inodes
            else ancestor_owner[0]
            if info.st_ino in runtime_inodes
            else 0
        )
        values["st_gid"] = (
            group[0]
            if info.st_ino in leaf_inodes
            else ancestor_group[0]
            if info.st_ino in runtime_inodes
            else 0
        )
        return SimpleNamespace(**values)

    def open_owned(path, flags, *args, **kwargs):
        descriptor = originals.open(root if path == "/" else path, flags, *args, **kwargs)
        opened.add(descriptor)
        events.append((str(path), flags))
        return descriptor

    def close_owned(descriptor):
        opened.remove(descriptor)
        originals.close(descriptor)

    def xattr(path, name, **kwargs):
        assert name == "security.selinux"
        assert not kwargs
        assert str(path).startswith("/proc/self/fd/")
        descriptor = int(str(path).rpartition("/")[2])
        assert descriptor in opened
        assert stat.S_ISREG(originals.fstat(descriptor).st_mode)
        hook[0](descriptor)
        return originals.getxattr(path, "user.web006_context")

    proxy.open, proxy.close, proxy.getxattr = open_owned, close_owned, xattr
    proxy.fstat = lambda descriptor: modeled(originals.fstat(descriptor))
    proxy.stat = lambda *args, **kwargs: modeled(originals.stat(*args, **kwargs))
    proxy.read = lambda *_args: pytest.fail("lock body read")
    proxy.getresuid = lambda: (UID,) * 3
    proxy.getresgid = lambda: (GID,) * 3
    proxy.getgroups = list
    monkeypatch.setattr(module, "os", proxy)
    yield SimpleNamespace(
        root=root,
        leaves=leaves,
        original=originals,
        proxy=proxy,
        opened=opened,
        events=events,
        hook=hook,
        owner=owner,
        group=group,
        leaf_inodes=leaf_inodes,
        runtime_inodes=runtime_inodes,
        ancestor_owner=ancestor_owner,
        ancestor_group=ancestor_group,
    )
    assert not opened


def capture():
    return module._engine_storage_locks(UID, GID, budget())


def test_exact_four_locks_metadata_only_with_owned_descriptors(locks):
    result = capture()
    assert [item["path"] for item in result] == [
        str(p) for p, _size in module._engine_lock_specs(UID)
    ]
    assert all(item["context"] == CONTEXT.decode() for item in result)
    assert [item["identity"]["bytes"] for item in result] == [64, 64, 0, 64]
    assert all(flags & os.O_PATH for _, flags in locks.events)
    assert all(not flags & (os.O_CREAT | os.O_TRUNC) for _, flags in locks.events)
    assert policy.SELINUX_LABELS["engine_locks"] == module._ENGINE_LOCK_TYPE


@pytest.mark.parametrize("mode", [0o600, 0o664, 0o666, 0o4644])
def test_unexpected_mode_refuses(locks, mode):
    locks.leaves[0].chmod(mode)
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("length", [0, 63, 65])
def test_unexpected_lock_record_size_refuses(locks, length):
    locks.leaves[0].write_bytes(b"n" * length)
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("which", ["owner", "group"])
def test_wrong_principal_refuses(locks, which):
    getattr(locks, which)[0] = 0
    with pytest.raises(module.PeerError):
        capture()


def test_hardlink_refuses(locks):
    locks.original.link(locks.leaves[0], locks.leaves[0].with_name("alias"))
    with pytest.raises(module.PeerError):
        capture()


def test_absent_lock_is_not_created(locks):
    locks.leaves[0].unlink()
    with pytest.raises(FileNotFoundError):
        capture()
    assert not locks.leaves[0].exists()


def test_symlink_leaf_refuses(locks):
    leaf = locks.leaves[0]
    moved = leaf.with_name("retained")
    leaf.rename(moved)
    leaf.symlink_to(moved.name)
    with pytest.raises(module.PeerError):
        capture()


def test_symlink_ancestor_refuses(locks):
    parent = locks.leaves[0].parent
    moved = parent.with_name("retained")
    parent.rename(moved)
    parent.symlink_to(moved.name)
    with pytest.raises(NotADirectoryError):
        capture()


@pytest.mark.parametrize(
    "context",
    [
        b"unconfined_u:object_r:container_ro_file_t:s0",
        b"unconfined_u:object_r:hfcache_host_helper_engine_lock_t:s0:c1",
        CONTEXT + b"\n",
        CONTEXT + b"\0\0",
        b"x" * 4097,
    ],
)
def test_wrong_or_malformed_context_refuses(locks, context):
    locks.original.setxattr(locks.leaves[0], "user.web006_context", context)
    with pytest.raises(module.PeerError):
        capture()


def test_single_terminal_nul_context_accepts(locks):
    for leaf in locks.leaves:
        locks.original.setxattr(leaf, "user.web006_context", CONTEXT + b"\0")
    assert len(capture()) == 4


def test_leaf_replacement_during_label_capture_refuses(locks):
    def swap(_descriptor):
        leaf = locks.leaves[0]
        leaf.rename(leaf.with_name("retained"))
        leaf.write_bytes(b"r" * 64)
        leaf.chmod(0o644)
        locks.hook[0] = lambda _fd: None

    locks.hook[0] = swap
    with pytest.raises(module.PeerError):
        capture()
    assert locks.leaves[0].read_bytes() == b"r" * 64


def test_ancestor_replacement_during_label_capture_refuses(locks):
    def swap(_descriptor):
        parent = locks.leaves[0].parent
        moved = parent.with_name("retained")
        parent.rename(moved)
        parent.symlink_to(moved.name)
        locks.hook[0] = lambda _fd: None

    locks.hook[0] = swap
    with pytest.raises(NotADirectoryError):
        capture()


def test_original_inode_label_drift_refuses(locks):
    def change(descriptor):
        locks.original.setxattr(f"/proc/self/fd/{descriptor}", "user.changed", b"1")
        locks.hook[0] = lambda _fd: None

    locks.hook[0] = change
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("limits", [{"files": 0}, {"size": 0}, {"seconds": -1}])
def test_shared_budget_refusal_closes_owned_fds(locks, limits):
    with pytest.raises(module.PeerError):
        module._engine_storage_locks(UID, GID, budget(**limits))


def test_native_profile_does_not_reach_engine_lock_io(monkeypatch):
    monkeypatch.setattr(module, "_engine_storage_locks", lambda *_a: pytest.fail("native lock IO"))
    with pytest.raises(module.PeerError):
        module._engine_prepare({"profile": "native"}, budget())


def test_receipt_requires_exact_lock_role_without_any_io():
    labels: dict[str, str | None] = {**policy.SELINUX_LABELS, "archive": "nfs_t"}
    value = {
        "schema_version": 1,
        "module": {
            "name": "hfcache_host_helper",
            "version": 1,
            "priority": 400,
            "source_sha256": "a" * 64,
            "loaded_sha256": "b" * 64,
        },
        "domain": policy.SELINUX_CONTEXT,
        "kernel_policy_sha256": "c" * 64,
        "labels": labels,
    }
    assert policy._selinux_installation(json.dumps(value).encode(), "a" * 64) == value
    del labels["engine_locks"]
    with pytest.raises(policy.InspectionError):
        policy._selinux_installation(json.dumps(value).encode(), "a" * 64)
    for wrong in ("container_ro_file_t", "container_var_lib_t", None):
        labels["engine_locks"] = wrong
        with pytest.raises(policy.InspectionError):
            policy._selinux_installation(json.dumps(value).encode(), "a" * 64)


def test_same_type_replacement_predating_capture_has_no_historical_inode_pin(locks):
    leaf = locks.leaves[0]
    old_inode = leaf.stat().st_ino
    leaf.rename(leaf.with_name("retained-original"))
    leaf.write_bytes(b"r" * 64)
    leaf.chmod(0o644)
    locks.original.setxattr(leaf, "user.web006_context", CONTEXT)
    locks.leaf_inodes.add(leaf.stat().st_ino)
    result = capture()
    assert result[0]["identity"]["inode"] != old_inode
    # The closed receipt binds a type, not historical device/inode identity.
    assert result[0]["context"] == CONTEXT.decode()


def test_rootless_preparation_checks_four_locks_before_namespace_work(locks, monkeypatch):
    monkeypatch.setattr(
        module,
        "pwd",
        SimpleNamespace(
            getpwnam=lambda _name: SimpleNamespace(
                pw_uid=UID, pw_gid=GID, pw_dir="/var/lib/hfcache"
            )
        ),
    )
    monkeypatch.setattr(module, "_engine_single_thread", lambda _budget: None)
    monkeypatch.setattr(module, "_engine_storage_config", lambda *_args: {"schema_version": 1})
    monkeypatch.setattr(module, "_engine_shared_memory", lambda *_args: {"fixture": "separate-shm"})
    observed = []
    locks.hook[0] = lambda descriptor: observed.append(locks.original.fstat(descriptor).st_ino)

    class ReachedNextStageError(Exception):
        pass

    def status(_budget):
        assert len(observed) == 4
        assert not locks.opened
        raise ReachedNextStageError

    monkeypatch.setattr(module, "_engine_status", status)
    with pytest.raises(ReachedNextStageError):
        module._engine_prepare(
            {"profile": "rootless", "api_principal": {"host_uid": UID, "host_gid": GID}}, budget()
        )


def test_wrong_lock_type_stops_rootless_preparation_before_namespace_work(locks, monkeypatch):
    monkeypatch.setattr(
        module,
        "pwd",
        SimpleNamespace(
            getpwnam=lambda _name: SimpleNamespace(
                pw_uid=UID, pw_gid=GID, pw_dir="/var/lib/hfcache"
            )
        ),
    )
    monkeypatch.setattr(module, "_engine_single_thread", lambda _budget: None)
    monkeypatch.setattr(module, "_engine_storage_config", lambda *_args: {"schema_version": 1})
    monkeypatch.setattr(module, "_engine_shared_memory", lambda *_args: {"fixture": "separate-shm"})
    monkeypatch.setattr(module, "_engine_status", lambda *_args: pytest.fail("late namespace work"))
    locks.original.setxattr(
        locks.leaves[0], "user.web006_context", b"x:object_r:container_ro_file_t:s0"
    )
    with pytest.raises(module.PeerError):
        module._engine_prepare(
            {"profile": "rootless", "api_principal": {"host_uid": UID, "host_gid": GID}}, budget()
        )


@pytest.mark.parametrize("length", [1, 64])
def test_alive_lock_requires_zero_bytes(locks, length):
    locks.leaves[2].write_bytes(b"n" * length)
    with pytest.raises(module.PeerError):
        capture()


def test_missing_alive_lock_is_not_created(locks):
    locks.leaves[2].unlink()
    with pytest.raises(FileNotFoundError):
        capture()
    assert not locks.leaves[2].exists()


def test_default_type_recreated_alive_lock_refuses(locks):
    locks.original.setxattr(locks.leaves[2], "user.web006_context", b"x:object_r:user_tmp_t:s0")
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("which", ["ancestor_owner", "ancestor_group"])
def test_runtime_ancestor_wrong_account_refuses(locks, which):
    getattr(locks, which)[0] = UID + 1
    with pytest.raises(module.PeerError):
        capture()


def test_runtime_ancestor_group_writable_refuses(locks):
    locks.leaves[2].parent.chmod(0o770)
    with pytest.raises(module.PeerError):
        capture()


def test_runtime_ancestor_symlink_refuses(locks):
    parent = locks.leaves[2].parent
    parent.rename(parent.with_name("retained"))
    parent.symlink_to("retained")
    with pytest.raises(NotADirectoryError):
        capture()


def test_alive_lock_same_capture_replacement_refuses(locks):
    def swap(descriptor):
        if locks.original.fstat(descriptor).st_ino != locks.leaves[2].stat().st_ino:
            return
        leaf = locks.leaves[2]
        leaf.rename(leaf.with_name("retained"))
        leaf.write_bytes(b"")
        leaf.chmod(0o644)
        locks.hook[0] = lambda _fd: None

    locks.hook[0] = swap
    with pytest.raises(module.PeerError):
        capture()
    assert locks.leaves[2].read_bytes() == b""


@pytest.mark.parametrize("uid", [True, 0, -1, 2**32, "983", None])
def test_lock_specs_refuse_non_principal_uid(uid):
    with pytest.raises(module.PeerError):
        module._engine_lock_specs(uid)


def test_uid_derived_specs_have_no_arbitrary_runtime_selector():
    rows = module._engine_lock_specs(986)
    assert len(rows) == 4
    assert rows[:2] == tuple((path, 64) for path in module._ENGINE_LOCK_PATHS)
    assert str(rows[2][0]) == "/run/user/986/libpod/tmp/alive.lck"
    assert rows[2][1] == 0
    assert str(rows[3][0]) == "/run/user/986/containers/overlay-layers/mountpoints.lock"
    assert rows[3][1] == 64


def test_sibling_runtime_uid_path_refuses_before_any_open(locks):
    with pytest.raises(module.PeerError):
        module._engine_lock_parent(Path("/run/user/984/libpod/tmp/alive.lck"), UID, GID, budget())
    assert not locks.events


@pytest.mark.parametrize("files", [38, 40, 45])
def test_partial_runtime_budget_refusal_closes_all_fds(locks, files):
    value = budget(files=files)
    with pytest.raises(module.PeerError):
        module._engine_storage_locks(UID, GID, value)
    assert value.files == files + 1
    assert sum(name == "images.lock" for name, _flags in locks.events) == 1
    assert sum(name == "layers.lock" for name, _flags in locks.events) == 1
    assert not locks.opened


def test_existing_fixed_engine_argv_is_unchanged_without_false_tmpdir_guarantee():
    assert module._engine_argv() == [
        "/usr/bin/podman",
        "--remote=false",
        "--storage-opt=overlay.mountopt=nodev",
        "--storage-opt=overlay.skip_mount_home=true",
        "container",
        "inspect",
        "hfcache-api",
    ]


@pytest.mark.parametrize("length", [0, 63, 65])
def test_mountpoints_lock_requires_64_bytes(locks, length):
    locks.leaves[3].write_bytes(b"n" * length)
    with pytest.raises(module.PeerError):
        capture()


def test_missing_mountpoints_lock_is_not_created(locks):
    locks.leaves[3].unlink()
    with pytest.raises(FileNotFoundError):
        capture()
    assert not locks.leaves[3].exists()


def test_default_type_recreated_mountpoints_lock_refuses(locks):
    locks.original.setxattr(locks.leaves[3], "user.web006_context", b"x:object_r:user_tmp_t:s0")
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("mode", [0o600, 0o664, 0o4644])
def test_mountpoints_lock_mode_refuses(locks, mode):
    locks.leaves[3].chmod(mode)
    with pytest.raises(module.PeerError):
        capture()


def test_mountpoints_lock_hardlink_refuses(locks):
    leaf = locks.leaves[3]
    locks.original.link(leaf, leaf.with_name("alias"))
    with pytest.raises(module.PeerError):
        capture()


def test_mountpoints_lock_symlink_refuses(locks):
    leaf = locks.leaves[3]
    leaf.rename(leaf.with_name("retained"))
    leaf.symlink_to("retained")
    with pytest.raises(module.PeerError):
        capture()


def test_mountpoints_lock_same_capture_replacement_refuses(locks):
    expected = locks.leaves[3].stat().st_ino

    def swap(descriptor):
        if locks.original.fstat(descriptor).st_ino != expected:
            return
        leaf = locks.leaves[3]
        leaf.rename(leaf.with_name("retained"))
        leaf.write_bytes(b"r" * 64)
        leaf.chmod(0o644)
        locks.hook[0] = lambda _fd: None

    locks.hook[0] = swap
    with pytest.raises(module.PeerError):
        capture()
    assert locks.leaves[3].read_bytes() == b"r" * 64


def test_mountpoints_lock_ancestor_replacement_refuses(locks):
    expected = locks.leaves[3].stat().st_ino

    def swap(descriptor):
        if locks.original.fstat(descriptor).st_ino != expected:
            return
        parent = locks.leaves[3].parent
        parent.rename(parent.with_name("retained"))
        parent.symlink_to("retained")
        locks.hook[0] = lambda _fd: None

    locks.hook[0] = swap
    with pytest.raises(NotADirectoryError):
        capture()


def test_mountpoints_runtime_ancestor_writable_refuses(locks):
    locks.leaves[3].parent.chmod(0o770)
    with pytest.raises(module.PeerError):
        capture()


def test_mountpoints_sibling_uid_refuses_before_open(locks):
    with pytest.raises(module.PeerError):
        module._engine_lock_parent(
            Path("/run/user/984/containers/overlay-layers/mountpoints.lock"), UID, GID, budget()
        )
    assert not locks.events


@pytest.mark.parametrize("files", [55, 59, 62])
def test_partial_mountpoints_budget_refusal_closes_all_owned_fds(locks, files):
    value = budget(files=files)
    with pytest.raises(module.PeerError):
        module._engine_storage_locks(UID, GID, value)
    assert value.files == files + 1
    assert sum(name == "alive.lck" for name, _flags in locks.events) == 1
    assert not locks.opened
