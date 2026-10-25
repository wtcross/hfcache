"""Owned FD/modeled-label checks; no installed SHM or SELinux acceptance."""

import json
import os
import stat
import time
from types import SimpleNamespace

import pytest

from hfcache import host_peer as module
from hfcache import host_policy as policy

UID = GID = 983
CONTEXT = b"unconfined_u:object_r:hfcache_host_helper_engine_shm_t:s0"


def budget(files=1024, size=65536, seconds=5):
    return module._Budget(time.monotonic() + seconds, files, size)


@pytest.fixture
def segment(tmp_path, monkeypatch):
    root = tmp_path / "owned-root"
    directory = root / "dev/shm"
    directory.mkdir(parents=True)
    directory.chmod(0o1777)
    leaf = directory / "libpod_rootless_lock_983"
    leaf.write_bytes(b"\0" * 82488)
    leaf.chmod(0o600)
    os.setxattr(leaf, "user.web006_context", CONTEXT)
    original = SimpleNamespace(**{k: getattr(os, k) for k in dir(os)})
    proxy = SimpleNamespace(**{k: getattr(os, k) for k in dir(os)})
    leaf_inodes = {leaf.stat().st_ino}
    parent_inode = directory.stat().st_ino
    opened, events = set(), []
    owner, group, parent_owner, parent_group = [UID], [GID], [0], [0]
    hook = [lambda _descriptor: None]

    def modeled(info):
        values = {k: getattr(info, k) for k in dir(info) if k.startswith("st_")}
        values["st_uid"] = (
            owner[0]
            if info.st_ino in leaf_inodes
            else (parent_owner[0] if info.st_ino == parent_inode else 0)
        )
        values["st_gid"] = (
            group[0]
            if info.st_ino in leaf_inodes
            else (parent_group[0] if info.st_ino == parent_inode else 0)
        )
        return SimpleNamespace(**values)

    def open_owned(path, flags, *args, **kwargs):
        fd = original.open(root if path == "/" else path, flags, *args, **kwargs)
        opened.add(fd)
        events.append((str(path), flags))
        return fd

    def close_owned(fd):
        opened.remove(fd)
        original.close(fd)

    def xattr(path, name):
        assert name == "security.selinux"
        fd = int(str(path).removeprefix("/proc/self/fd/"))
        assert fd in opened
        assert stat.S_ISREG(original.fstat(fd).st_mode)
        hook[0](fd)
        return original.getxattr(path, "user.web006_context")

    proxy.open, proxy.close, proxy.getxattr = open_owned, close_owned, xattr
    proxy.fstat = lambda fd: modeled(original.fstat(fd))
    proxy.stat = lambda *a, **kw: modeled(original.stat(*a, **kw))
    proxy.read = lambda *_a: pytest.fail("shared-memory body read")
    monkeypatch.setattr(module, "os", proxy)
    yield SimpleNamespace(
        root=root,
        directory=directory,
        leaf=leaf,
        original=original,
        opened=opened,
        events=events,
        hook=hook,
        owner=owner,
        group=group,
        parent_owner=parent_owner,
        parent_group=parent_group,
        leaf_inodes=leaf_inodes,
    )
    assert not opened


def capture():
    return module._engine_shared_memory(UID, GID, budget())


def test_exact_existing_segment_uses_only_metadata_and_held_descriptors(segment):
    record = capture()
    assert record["path"] == "/dev/shm/libpod_rootless_lock_983"
    assert record["identity"]["bytes"] == 82488
    assert record["context"] == CONTEXT.decode()
    assert len(record["ancestors"]) == 3
    assert all(flags & os.O_PATH for _name, flags in segment.events)
    assert all(not flags & (os.O_CREAT | os.O_TRUNC) for _name, flags in segment.events)
    assert "mtime_ns" not in record["identity"]
    assert "ctime_ns" not in record["identity"]
    assert policy.SELINUX_LABELS["engine_shared_memory"] == module._ENGINE_SHM_TYPE


@pytest.mark.parametrize("mode", [0o777, 0o1770, 0o700, 0o3777])
def test_only_exact_sticky_root_1777_directory_is_exception(segment, mode):
    segment.directory.chmod(mode)
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("which", ["parent_owner", "parent_group"])
def test_sticky_parent_must_still_be_root_owned(segment, which):
    getattr(segment, which)[0] = UID
    with pytest.raises(module.PeerError):
        capture()


def test_no_other_world_writable_ancestor_is_accepted(segment):
    (segment.root / "dev").chmod(0o777)
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("mode", [0o400, 0o644, 0o660, 0o1600])
def test_unexpected_segment_mode_refuses(segment, mode):
    segment.leaf.chmod(mode)
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("size", [0, 82487, 82489])
def test_only_measured_stock_segment_size_is_supported(segment, size):
    segment.leaf.write_bytes(b"n" * size)
    with pytest.raises(module.PeerError):
        capture()


@pytest.mark.parametrize("which", ["owner", "group"])
def test_wrong_segment_principal_refuses(segment, which):
    getattr(segment, which)[0] = 0
    with pytest.raises(module.PeerError):
        capture()


def test_absent_segment_is_not_created(segment):
    segment.leaf.unlink()
    with pytest.raises(FileNotFoundError):
        capture()
    assert not segment.leaf.exists()


def test_hardlink_refuses(segment):
    segment.original.link(segment.leaf, segment.leaf.with_name("other"))
    with pytest.raises(module.PeerError):
        capture()


def test_leaf_symlink_refuses(segment):
    segment.leaf.rename(segment.leaf.with_name("retained"))
    segment.leaf.symlink_to("retained")
    with pytest.raises(module.PeerError):
        capture()


def test_parent_symlink_refuses(segment):
    segment.directory.rename(segment.directory.with_name("retained"))
    segment.directory.symlink_to("retained")
    with pytest.raises(NotADirectoryError):
        capture()


@pytest.mark.parametrize(
    "context",
    [
        b"x:object_r:container_runtime_tmpfs_t:s0",
        b"x:object_r:hfcache_host_helper_engine_lock_t:s0",
        CONTEXT + b":c1",
        CONTEXT + b"\n",
        CONTEXT + b"\0\0",
        b"x" * 4097,
    ],
)
def test_wrong_recreated_or_malformed_type_refuses(segment, context):
    segment.original.setxattr(segment.leaf, "user.web006_context", context)
    with pytest.raises(module.PeerError):
        capture()


def test_single_optional_terminal_nul_is_accepted(segment):
    segment.original.setxattr(segment.leaf, "user.web006_context", CONTEXT + b"\0")
    assert capture()["context"] == CONTEXT.decode()


def test_replacement_during_capture_refuses(segment):
    def swap(_fd):
        segment.leaf.rename(segment.leaf.with_name("retained"))
        segment.leaf.write_bytes(b"x" * 82488)
        segment.leaf.chmod(0o600)
        segment.hook[0] = lambda _fd: None

    segment.hook[0] = swap
    with pytest.raises(module.PeerError):
        capture()


def test_ancestor_replacement_during_capture_refuses(segment):
    def swap(_fd):
        segment.directory.rename(segment.directory.with_name("retained"))
        segment.directory.symlink_to("retained")
        segment.hook[0] = lambda _fd: None

    segment.hook[0] = swap
    with pytest.raises(NotADirectoryError):
        capture()


def test_timestamp_drift_within_capture_is_not_ignored(segment):
    def change(_fd):
        before = segment.leaf.stat()
        segment.original.utime(segment.leaf, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
        segment.hook[0] = lambda _fd: None

    segment.hook[0] = change
    with pytest.raises(module.PeerError):
        capture()


def test_coordination_timestamp_changes_between_captures_do_not_claim_integrity(segment):
    before = capture()
    info = segment.leaf.stat()
    segment.original.utime(segment.leaf, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
    after = capture()
    assert segment.leaf.stat().st_mtime_ns != info.st_mtime_ns
    assert before == after


@pytest.mark.parametrize("limit", [1, 2, 3, 4, 5, 6])
def test_partial_file_budget_refusal_closes_every_owned_fd(segment, limit):
    with pytest.raises(module.PeerError):
        module._engine_shared_memory(UID, GID, budget(files=limit))
    assert not segment.opened


@pytest.mark.parametrize("limits", [{"size": 0}, {"seconds": -1}])
def test_shared_time_and_byte_budget_refusals_close_fds(segment, limits):
    with pytest.raises(module.PeerError):
        module._engine_shared_memory(UID, GID, budget(**limits))


@pytest.mark.parametrize("uid", [True, 0, -1, 2**32, "983", None])
def test_uid_is_protected_integer_not_path_selector(segment, uid):
    with pytest.raises(module.PeerError):
        module._engine_shared_memory(uid, GID, budget())
    assert not segment.events


def test_native_has_no_shared_memory_prerequisite(monkeypatch):
    monkeypatch.setattr(module, "_engine_shared_memory", lambda *_a: pytest.fail("native SHM IO"))
    with pytest.raises(module.PeerError):
        module._engine_prepare({"profile": "native"}, budget())


def test_receipt_role_is_closed_without_any_host_io():
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
        "labels": {**policy.SELINUX_LABELS, "archive": "nfs_t"},
    }
    assert len(value["labels"]) == 12
    assert policy._selinux_installation(json.dumps(value).encode(), "a" * 64) == value
    del value["labels"]["engine_shared_memory"]
    with pytest.raises(policy.InspectionError):
        policy._selinux_installation(json.dumps(value).encode(), "a" * 64)
    value["labels"]["engine_shared_memory"] = "container_runtime_tmpfs_t"
    with pytest.raises(policy.InspectionError):
        policy._selinux_installation(json.dumps(value).encode(), "a" * 64)
