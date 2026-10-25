"""Credential ACL exception regressions using only newly owned synthetic files.

The ACL xattrs, descriptors, modes, contents, and timestamps are real. Root file
ownership and the service UID/GID/groups are explicitly modeled: an ordinary
login cannot create a root-owned delivery. CI running as root uses the same
non-root subject model, so membership in GID 0 cannot bypass the ACL exception.
An isolated native systemd comparison supplies the separate real ownership and
service-identity proof; this module does not claim to simulate systemd delivery.
"""

import errno
import os
import stat
import struct
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from hfcache.api import credential_sources
from hfcache.errors import ConfigurationError

ACL_ATTRIBUTE = "system.posix_acl_access"
SYNTHETIC = b"A" * 53
STAT_FIELDS = (
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


def delivery_acl(uid, **changes):
    named = changes.get("named", 4)
    group = changes.get("group", 0)
    mask = changes.get("mask", 4)
    other = changes.get("other", 0)
    extra = changes.get("extra", ())
    entries = [
        (1, 4, 0xFFFFFFFF),
        (2, named, uid),
        (4, group, 0xFFFFFFFF),
        (16, mask, 0xFFFFFFFF),
        (32, other, 0xFFFFFFFF),
        *extra,
    ]
    entries.sort(key=lambda entry: (entry[0], entry[2]))
    return struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *entry) for entry in entries)


def open_fds():
    result = set()
    for path in Path("/proc/self/fd").iterdir():
        try:
            os.fstat(int(path.name))
        except OSError as error:
            if error.errno != errno.EBADF:
                raise
        else:
            result.add(int(path.name))
    return result


@pytest.fixture
def delivery(tmp_path, monkeypatch):
    uid = os.geteuid() if os.geteuid() != 0 else 65534
    gid = os.getegid() if os.getegid() != 0 else 65534
    path = tmp_path / "synthetic-credential"
    path.write_bytes(SYNTHETIC)
    path.chmod(0o400)
    value = delivery_acl(uid)
    os.setxattr(path, ACL_ATTRIBUTE, value)
    assert os.getxattr(path, ACL_ATTRIBUTE) == value
    actual = path.stat()
    assert stat.S_IMODE(actual.st_mode) == 0o440
    platform = SimpleNamespace(**vars(os))
    platform.geteuid = lambda: uid
    platform.getegid = lambda: gid
    platform.getgroups = lambda: [gid]
    assert 0 not in {platform.getegid(), *platform.getgroups()}
    ownership = {"st_uid": 0, "st_gid": 0}

    def fstat(descriptor):
        status = os.fstat(descriptor)
        if (status.st_dev, status.st_ino) != (actual.st_dev, actual.st_ino):
            return status
        fields = {name: getattr(status, name) for name in STAT_FIELDS}
        fields.update(ownership)
        return SimpleNamespace(**fields)

    platform.fstat = fstat
    monkeypatch.setattr(credential_sources, "os", platform)
    return SimpleNamespace(path=path, uid=uid, gid=gid, platform=platform, ownership=ownership)


def read(delivery):
    return credential_sources.read_protected_bytes(delivery.path, 8192)


def test_real_search_only_parent_needs_no_directory_read():
    """Use real DAC permissions; a root runner delegates only this owned read."""
    with tempfile.TemporaryDirectory(prefix="hfcache-credential-search-", dir="/tmp") as work:
        parent = Path(work)
        directory = parent / "protected"
        directory.mkdir()
        credential = directory / "credential"
        credential.write_bytes(SYNTHETIC)
        credential.chmod(0o400)
        parent.chmod(0o711)
        directory.chmod(0o111)

        def check():
            try:
                descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            except PermissionError:
                pass
            else:
                os.close(descriptor)
                pytest.fail("search-only parent unexpectedly permits a directory read open")
            assert credential_sources.read_protected_bytes(credential, 8192) == SYNTHETIC

        try:
            if os.geteuid() != 0:
                check()
            else:
                os.chown(credential, 65534, 65534)
                child = os.fork()
                if child == 0:
                    try:
                        os.setgroups([])
                        os.setresgid(65534, 65534, 65534)
                        os.setresuid(65534, 65534, 65534)
                        check()
                    except BaseException:  # noqa: BLE001 - child exits without pytest teardown
                        os._exit(1)
                    os._exit(0)
                assert os.waitpid(child, 0) == (child, 0)
        finally:
            directory.chmod(0o700)
            parent.chmod(0o700)


def refused_without_fd_leak(delivery):
    before = open_fds()
    with pytest.raises(ConfigurationError) as caught:
        read(delivery)
    assert caught.value.problems[0].code == "HFAPI003"
    assert SYNTHETIC.decode() not in str(caught.value)
    assert open_fds() == before


def test_canonical_named_user_acl_accepts_checked_delivery(delivery):
    before = open_fds()
    assert read(delivery) == SYNTHETIC
    assert open_fds() == before


@pytest.mark.parametrize(
    "variant",
    [
        "wrong-user",
        "extra-user",
        "extra-group",
        "named-write",
        "base-group-read",
        "mask-write",
        "other-read",
    ],
)
def test_noncanonical_acl_refuses_before_bytes(delivery, variant):
    changes = {
        "wrong-user": {"uid": delivery.uid + 1},
        "extra-user": {"extra": ((2, 4, delivery.uid + 1),)},
        "extra-group": {"extra": ((8, 4, delivery.gid),)},
        "named-write": {"named": 6},
        "base-group-read": {"group": 4},
        "mask-write": {"mask": 6},
        "other-read": {"other": 4},
    }[variant]
    parameters = {"uid": delivery.uid} | changes
    os.setxattr(delivery.path, ACL_ATTRIBUTE, delivery_acl(**parameters))
    delivery.platform.read = lambda *_: pytest.fail("unsafe ACL reached credential bytes")
    refused_without_fd_leak(delivery)


def test_missing_acl_does_not_authorize_root_group(delivery):
    os.removexattr(delivery.path, ACL_ATTRIBUTE)
    delivery.platform.read = lambda *_: pytest.fail("missing ACL reached credential bytes")
    refused_without_fd_leak(delivery)


@pytest.mark.parametrize("change", ["owner", "group", "mode"])
def test_acl_exception_is_limited_to_root_root_0440(delivery, change):
    if change == "owner":
        delivery.ownership["st_uid"] = delivery.uid
    elif change == "group":
        delivery.ownership["st_gid"] = delivery.gid + 1
    else:
        delivery.path.chmod(0o640)
    delivery.platform.read = lambda *_: pytest.fail("wrong delivery metadata reached bytes")
    refused_without_fd_leak(delivery)


def test_acl_and_metadata_enclose_read_without_changing_leaf_open(delivery):
    platform = delivery.platform
    fstat, getxattr, original_read, original_open = (
        platform.fstat,
        platform.getxattr,
        platform.read,
        platform.open,
    )
    events, opens = [], []
    platform.fstat = lambda fd: events.append("metadata") or fstat(fd)
    platform.getxattr = lambda *args: events.append("acl") or getxattr(*args)
    platform.read = lambda *args: events.append("read") or original_read(*args)

    def checked_open(path, flags, *args, **kwargs):
        opens.append((path, flags))
        return original_open(path, flags, *args, **kwargs)

    platform.open = checked_open
    assert read(delivery) == SYNTHETIC
    assert events[0:2] == ["metadata", "acl"]
    assert events[-2:] == ["acl", "metadata"]
    assert all(event == "read" for event in events[2:-2])
    leaf = [flags for name, flags in opens if name == delivery.path.name]
    assert len(leaf) == 1
    assert leaf[0] & os.O_ACCMODE == os.O_RDONLY
    assert leaf[0] & os.O_NOFOLLOW
    assert not leaf[0] & os.O_PATH
    directories = [flags for name, flags in opens if name != delivery.path.name]
    assert directories
    assert all(flags & os.O_PATH and flags & os.O_DIRECTORY for flags in directories)
    assert all(flags & os.O_NOFOLLOW and flags & os.O_CLOEXEC for flags in directories)


@pytest.mark.parametrize("restore", [False, True])
def test_acl_change_during_read_refuses_even_when_acl_is_restored(delivery, restore):
    original_read = delivery.platform.read
    original_acl = os.getxattr(delivery.path, ACL_ATTRIBUTE)
    before = delivery.path.stat()
    changed = False

    def change_after_read(descriptor, count):
        nonlocal changed
        value = original_read(descriptor, count)
        if not changed:
            os.setxattr(descriptor, ACL_ATTRIBUTE, delivery_acl(delivery.uid + 1))
            if restore:
                os.setxattr(descriptor, ACL_ATTRIBUTE, original_acl)
            changed = True
        return value

    delivery.platform.read = change_after_read
    refused_without_fd_leak(delivery)
    assert changed
    assert delivery.path.stat().st_ctime_ns != before.st_ctime_ns
    if restore:
        assert os.getxattr(delivery.path, ACL_ATTRIBUTE) == original_acl


def test_final_acl_observation_failure_refuses_and_closes(delivery):
    getxattr = delivery.platform.getxattr
    observations = 0

    def fail_final(*args):
        nonlocal observations
        observations += 1
        if observations == 2:
            raise OSError(errno.EIO, "synthetic ACL observation refusal")
        return getxattr(*args)

    delivery.platform.getxattr = fail_final
    refused_without_fd_leak(delivery)
    assert observations == 2


def test_legacy_authorized_group_does_not_require_acl_exception(delivery):
    os.removexattr(delivery.path, ACL_ATTRIBUTE)
    delivery.path.chmod(0o440)
    delivery.ownership["st_gid"] = delivery.gid
    delivery.platform.getxattr = lambda *_: pytest.fail("legacy group requested ACL exception")
    assert read(delivery) == SYNTHETIC
