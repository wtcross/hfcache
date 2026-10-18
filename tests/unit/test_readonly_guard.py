"""Decisions126/127: real local flock/readiness without archive file I/O."""

import configparser
import fcntl
import importlib.util
import json
import os
import select
import signal
import socket
import stat
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts/hold-readonly-guard.py"
SPEC = importlib.util.spec_from_file_location("readonly_guard", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
HOST_ROOT = "1 0 0:1 / / rw - ext4 /dev/local rw\n"
READONLY = "2 1 0:2 / /srv/hfcache ro - nfs4 nas:/archive rw\n"
CHILD = """
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('readonly_guard', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.LOCK_PATH = Path(sys.argv[2])
module.MOUNTINFO = Path(sys.argv[3])
module.SERVICE_UID, module.SERVICE_GID = os.geteuid(), os.getegid()
sys.argv = [sys.argv[1]]
assert not any(name == 'hfcache' or name.startswith('hfcache.') for name in sys.modules)
raise SystemExit(module.main())
"""


@pytest.fixture
def local_guard(tmp_path, monkeypatch):
    lock = tmp_path / "original.lock"
    lock.write_bytes(b"original bytes\n")
    lock.chmod(0o600)
    mounts = tmp_path / "host-mountinfo"
    mounts.write_text(HOST_ROOT + READONLY)
    monkeypatch.setattr(guard, "LOCK_PATH", lock)
    monkeypatch.setattr(guard, "MOUNTINFO", mounts)
    monkeypatch.setattr(guard, "SERVICE_UID", os.geteuid())
    monkeypatch.setattr(guard, "SERVICE_GID", os.getegid())
    return SimpleNamespace(lock=lock, mounts=mounts)


def assert_available(path):
    with path.open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_original_lock_is_noncreating_held_exclusive_and_never_rewritten(local_guard):
    before = local_guard.lock.stat()
    with guard.hold_original_lock() as info:
        assert (info.st_dev, info.st_ino) == (before.st_dev, before.st_ino)
        with local_guard.lock.open("rb") as contender, pytest.raises(BlockingIOError):
            fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
    after = local_guard.lock.stat()
    assert (after.st_ino, after.st_mtime_ns, after.st_mode) == (
        before.st_ino,
        before.st_mtime_ns,
        before.st_mode,
    )
    assert local_guard.lock.read_bytes() == b"original bytes\n"
    assert_available(local_guard.lock)


@pytest.mark.parametrize("kind", ["missing", "symlink", "hardlink", "fifo", "directory"])
def test_missing_or_unsafe_lock_evidence_is_preserved(local_guard, kind):
    if kind == "missing":
        local_guard.lock.unlink()
    elif kind == "symlink":
        original = local_guard.lock.with_suffix(".preserved")
        local_guard.lock.rename(original)
        local_guard.lock.symlink_to(original)
    elif kind == "hardlink":
        local_guard.lock.with_suffix(".linked").hardlink_to(local_guard.lock)
    elif kind == "fifo":
        local_guard.lock.unlink()
        os.mkfifo(local_guard.lock)
    else:
        local_guard.lock.unlink()
        local_guard.lock.mkdir()
    before = None if kind == "missing" else local_guard.lock.lstat()
    with pytest.raises((OSError, ValueError)), guard.hold_original_lock():
        pytest.fail("unsafe lock admitted")
    if kind == "missing":
        assert not local_guard.lock.exists()
    else:
        assert before is not None
        assert local_guard.lock.lstat().st_ino == before.st_ino


@pytest.mark.parametrize("mode", [0o400, 0o640, 0o660, 0o700])
def test_exact_lock_permissions_are_required(local_guard, mode):
    local_guard.lock.chmod(mode)
    with pytest.raises(ValueError, match="unsafe"), guard.hold_original_lock():
        pytest.fail("unsafe mode admitted")
    assert stat.S_IMODE(local_guard.lock.stat().st_mode) == mode


@pytest.mark.parametrize("field", ["SERVICE_UID", "SERVICE_GID"])
def test_lock_owner_and_group_must_match_fixed_service_identity(local_guard, monkeypatch, field):
    monkeypatch.setattr(guard, field, getattr(guard, field) + 1)
    with pytest.raises(ValueError, match="unsafe"), guard.hold_original_lock():
        pytest.fail("wrong service identity admitted")
    assert_available(local_guard.lock)


def test_busy_original_lock_is_not_unlinked_or_replaced(local_guard):
    inode = local_guard.lock.stat().st_ino
    with local_guard.lock.open("rb") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError), guard.hold_original_lock():
            pytest.fail("busy original lock admitted")
    assert local_guard.lock.stat().st_ino == inode
    assert local_guard.lock.read_bytes() == b"original bytes\n"


def test_parent_symlink_is_refused_without_following(local_guard, monkeypatch):
    alias = local_guard.lock.parent / "alias"
    alias.symlink_to(local_guard.lock.parent, target_is_directory=True)
    monkeypatch.setattr(guard, "LOCK_PATH", alias / local_guard.lock.name)
    with pytest.raises(NotADirectoryError), guard.hold_original_lock():
        pytest.fail("symlink parent followed")
    assert_available(local_guard.lock)


def test_lock_substitution_after_flock_preserves_both_inodes(local_guard, monkeypatch):
    flock = fcntl.flock
    original = local_guard.lock.with_suffix(".original")

    def swapped(descriptor, operation):
        flock(descriptor, operation)
        local_guard.lock.rename(original)
        local_guard.lock.write_bytes(b"substitution")
        local_guard.lock.chmod(0o600)

    monkeypatch.setattr(
        guard, "fcntl", SimpleNamespace(flock=swapped, LOCK_EX=fcntl.LOCK_EX, LOCK_NB=fcntl.LOCK_NB)
    )
    with pytest.raises(ValueError, match="path changed"), guard.hold_original_lock():
        pytest.fail("substitution admitted")
    assert original.read_bytes() == b"original bytes\n"
    assert local_guard.lock.read_bytes() == b"substitution"
    assert_available(original)


@pytest.mark.parametrize(
    "row",
    [
        "",
        "malformed\n",
        "2 1 0:2 / /srv/hfcache rw - nfs4 nas:/archive rw\n",
        "2 1 0:2 / /srv/hfcache ro,rw - nfs4 nas:/archive rw\n",
        "2 1 0:2 / /srv/hfcache ro - ext4 /dev/local ro\n",
        READONLY + READONLY,
        READONLY + "3 1 0:3 / /srv/hfcache ro - tmpfs tmpfs ro\n",
    ],
)
def test_unknown_or_host_writable_mount_refuses_before_readiness(local_guard, row):
    local_guard.mounts.write_text(HOST_ROOT + row)
    with pytest.raises(ValueError, match=r"host"), guard.hold_original_lock():
        pytest.fail("unproven host mount admitted")
    assert_available(local_guard.lock)


def test_autofs_and_superblock_rw_do_not_hide_client_mount_ro(local_guard):
    local_guard.mounts.write_text(
        HOST_ROOT + "3 1 0:3 / /srv/hfcache rw - autofs systemd-1 rw\n" + READONLY
    )
    with guard.hold_original_lock():
        pass


def test_fixed_host_mount_source_is_not_the_sandbox_mount_table():
    assert Path("/proc/1/mountinfo") == guard.MOUNTINFO
    assert Path("/run/hfcache/hfcache.lock") == guard.LOCK_PATH
    assert guard.SERVICE_UID == guard.SERVICE_GID == 981


@pytest.mark.parametrize("address", [None, "", "relative", "http://127.0.0.1", "/bad\0path"])
def test_unavailable_notify_endpoint_refuses_without_address_echo(monkeypatch, address):
    if address is None:
        monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    else:
        monkeypatch.setattr(guard, "os", SimpleNamespace(environ={"NOTIFY_SOCKET": address}))
    with pytest.raises(ValueError, match="notification endpoint is unavailable"):
        guard.notify_ready()


def test_actual_system_python_notifies_only_while_original_inode_is_held_and_stops_cleanly(
    local_guard,
):
    with tempfile.TemporaryDirectory(prefix="hf-guard-") as directory:
        address = str(Path(directory) / "notify")
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as listener:
            listener.bind(address)
            listener.settimeout(5)
            process = subprocess.Popen(
                [
                    "/usr/bin/python3",
                    "-I",
                    "-B",
                    "-c",
                    CHILD,
                    str(SCRIPT),
                    str(local_guard.lock),
                    str(local_guard.mounts),
                ],
                env={"NOTIFY_SOCKET": address},
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                assert listener.recv(512).startswith(b"READY=1\n")
                with local_guard.lock.open("rb") as contender, pytest.raises(BlockingIOError):
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                assert process.stdout is not None
                assert select.select([process.stdout], [], [], 5)[0]
                held = json.loads(process.stdout.readline())
                assert held == {
                    "state": "readonly-guard-held",
                    "device": local_guard.lock.stat().st_dev,
                    "inode": local_guard.lock.stat().st_ino,
                    "uid": os.geteuid(),
                    "gid": os.getegid(),
                    "host_nfs_readonly": True,
                }
                process.send_signal(signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=5)
                assert process.returncode == 0
                assert stdout == stderr == ""
            finally:
                if process.poll() is None:
                    process.terminate()
                process.communicate(timeout=5)
    assert local_guard.lock.read_bytes() == b"original bytes\n"
    assert_available(local_guard.lock)


def test_host_rw_releases_lock_without_ready_or_private_data(local_guard):
    local_guard.mounts.write_text(HOST_ROOT + READONLY.replace("hfcache ro", "hfcache rw"))
    with tempfile.TemporaryDirectory(prefix="hf-guard-") as directory:
        address = str(Path(directory) / "notify")
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as listener:
            listener.bind(address)
            listener.settimeout(0.05)
            process = subprocess.run(
                [
                    "/usr/bin/python3",
                    "-I",
                    "-B",
                    "-c",
                    CHILD,
                    str(SCRIPT),
                    str(local_guard.lock),
                    str(local_guard.mounts),
                ],
                env={"NOTIFY_SOCKET": address},
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            assert process.returncode == 20
            assert process.stdout == ""
            assert process.stderr == "hfcache read-only guard refused; original state preserved\n"
            with pytest.raises(TimeoutError):
                listener.recv(512)
    assert_available(local_guard.lock)


def test_production_entrypoint_has_no_path_or_environment_override_cli():
    result = subprocess.run(
        ["/usr/bin/python3", "-I", "-B", str(SCRIPT), "--lock=/srv/hfcache/forbidden"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 20
    assert result.stdout == ""
    assert result.stderr == "hfcache read-only guard accepts no arguments\n"


def test_unit_keeps_host_pid1_view_and_notify_readiness_independent_of_current():
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(ROOT / "packaging/containers/hfcache-readonly-guard.service")
    unit, service = parser["Unit"], parser["Service"]
    assert set(unit["Requires"].split()) == {"srv-hfcache.mount", "systemd-tmpfiles-setup.service"}
    assert set(unit["After"].split()) == set(unit["Requires"].split())
    assert service["Type"] == "notify"
    assert service["NotifyAccess"] == "main"
    assert service["User"] == service["Group"] == "hfcache"
    assert service["ExecStart"] == "/usr/bin/python3 /usr/local/libexec/hfcache-readonly-guard"
    for option in ("NoNewPrivileges", "PrivateNetwork", "ProtectHome", "PrivateTmp"):
        assert service[option] == "yes"
    assert service["ProtectSystem"] == "strict"
    assert service["ReadOnlyPaths"] == "/run/hfcache"
    assert service["RestrictAddressFamilies"] == "AF_UNIX"
    assert service["CapabilityBoundingSet"] == service["AmbientCapabilities"] == ""
    assert service["TimeoutStartSec"] == "15"
    assert service["TimeoutStopSec"] == "infinity"
    assert service["SendSIGKILL"] == service["Restart"] == "no"
    assert not {
        "privatepids",
        "protectproc",
        "procsubset",
        "rootimage",
        "rootdirectory",
        "loadcredential",
        "loadcredentialencrypted",
    } & set(service)
    bridge = configparser.ConfigParser(interpolation=None)
    bridge.read_string(
        (ROOT / "packaging/containers/hfcache-readonly-bridge.conf.in")
        .read_text()
        .replace("@SERVICE_UID@", "981")
    )
    assert bridge["Unit"]["Requires"] == "hfcache-readonly-guard.service"
    assert bridge["Unit"]["After"] == "hfcache-readonly-guard.service"
    assert bridge["Service"]["Environment"] == "XDG_RUNTIME_DIR=/run/hfcache/user-manager"
    assert bridge["Service"]["BindReadOnlyPaths"] == (
        "/run/user/981/systemd/private:/run/hfcache/user-manager/systemd/private"
    )
    assert set(bridge["Service"]) == {"environment", "bindreadonlypaths"}


def test_tmpfiles_uses_only_fixed_local_nontruncating_boot_paths():
    lines = [
        line.split()
        for line in (ROOT / "packaging/containers/hfcache-rootless.conf").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    assert lines == [
        ["d", "/run/hfcache", "0700", "hfcache", "hfcache", "-"],
        ["d", "/run/hfcache/api", "0700", "hfcache", "hfcache", "-"],
        ["d", "/run/hfcache/verification", "0700", "hfcache", "hfcache", "-"],
        ["d", "/run/hfcache/user-manager", "0700", "hfcache", "hfcache", "-"],
        ["d", "/run/hfcache/user-manager/systemd", "0700", "hfcache", "hfcache", "-"],
        ["f", "/run/hfcache/hfcache.lock", "0600", "hfcache", "hfcache", "-"],
        ["f", "/run/hfcache/api.lock", "0600", "hfcache", "hfcache", "-"],
    ]


def test_actual_tmpfiles_boot_creation_is_idempotent_and_preserves_held_inode(tmp_path):
    config = tmp_path / "etc/tmpfiles.d/hfcache-rootless.conf"
    config.parent.mkdir(parents=True)
    rows = []
    for line in (ROOT / "packaging/containers/hfcache-rootless.conf").read_text().splitlines():
        if line and not line.startswith("#"):
            fields = line.split()
            fields[3:5] = [str(os.geteuid()), str(os.getegid())]
            rows.append(" ".join(fields))
    config.write_text("\n".join(rows) + "\n")
    argv = ["/usr/bin/systemd-tmpfiles", "--root=" + str(tmp_path), "--create", config.name]
    first = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=5)
    assert first.returncode == 0, first.stderr
    lock = tmp_path / "run/hfcache/hfcache.lock"
    lock.write_bytes(b"persistent original bytes")
    before = lock.stat()
    with lock.open("rb") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        second = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=5)
        assert second.returncode == 0, second.stderr
        with lock.open("rb") as contender, pytest.raises(BlockingIOError):
            fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert lock.stat().st_ino == before.st_ino
        assert lock.read_bytes() == b"persistent original bytes"
    assert stat.S_IMODE(lock.stat().st_mode) == 0o600
    for name in (
        "run/hfcache",
        "run/hfcache/api",
        "run/hfcache/verification",
        "run/hfcache/user-manager",
        "run/hfcache/user-manager/systemd",
    ):
        assert stat.S_IMODE((tmp_path / name).stat().st_mode) == 0o700
