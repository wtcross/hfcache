"""Real non-echoing terminal provisioning and exclusive protected-file refusal."""

import errno
import importlib.util
import os
import pty
import runpy
import secrets
import select
import signal
import stat
import subprocess
import sys
import time
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

from hfcache.api.basic import ProtectedAdministratorRecord

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/provision-ui-administrator.py"


@pytest.fixture(scope="module")
def provisioner():
    spec = importlib.util.spec_from_file_location("owned_basic_provisioner", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def protected_tree():
    # Ordinary /tmp has writable ancestry and must refuse protected provisioning.
    scratch = ROOT / ".scratch"
    scratch.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="web-basic-provision-", dir=scratch) as temporary:
        yield Path(temporary)


def terminal_run(path, supplied):  # noqa: PLR0912 - bounded owned PTY read/exit/cleanup lifecycle
    pid, terminal = pty.fork()
    if pid == 0:
        os.execv(
            sys.executable,
            [sys.executable, str(SCRIPT), "human:terminal", "operator", "--output", str(path)],
        )
    transcript = bytearray()
    sent = 0
    deadline = time.monotonic() + 20
    finished = False
    status = 0
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([terminal], [], [], 0.05)
            if ready:
                try:
                    part = os.read(terminal, 65536)
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    break
                if not part:
                    break
                transcript.extend(part)
                if sent == 0 and b"Password: " in transcript:
                    os.write(terminal, supplied[0] + b"\n")
                    sent += 1
                if sent == 1 and b"Confirm password: " in transcript:
                    os.write(terminal, supplied[1] + b"\n")
                    sent += 1
        else:
            pytest.fail("owned provisioning terminal exceeded its deadline")
    finally:
        os.close(terminal)
        if not finished:
            while time.monotonic() < deadline:
                found, status = os.waitpid(pid, os.WNOHANG)
                if found:
                    finished = True
                    break
                time.sleep(0.005)
            if not finished:
                os.kill(pid, signal.SIGKILL)
                _, status = os.waitpid(pid, 0)
        if any(value and value in transcript for value in supplied):
            pytest.fail("provisioning terminal exposed password input")
    return os.waitstatus_to_exitcode(status), bytes(transcript), sent


def test_actual_tty_creates_exclusive0600_records_with_fresh_salts(protected_tree):
    password = secrets.token_urlsafe(32).encode()
    records = []
    for name in ("first.json", "second.json"):
        path = protected_tree / name
        code, output, sent = terminal_run(path, (password, password))
        assert code == 0
        assert sent == 2
        assert b"Created protected administrator record" in output
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert path.stat().st_nlink == 1
        assert path.stat().st_uid == os.geteuid()
        record = ProtectedAdministratorRecord.model_validate_json(path.read_text())
        assert record.subject == "human:terminal"
        assert record.username == "operator"
        Argon2id.verify_phc_encoded(password, record.password_hash)
        records.append(record)
    assert records[0].password_hash != records[1].password_hash


def test_actual_tty_mismatch_and_empty_input_never_create_a_file(protected_tree):
    password = secrets.token_urlsafe(32).encode()
    for name, values in (
        ("mismatch.json", (password, secrets.token_urlsafe(32).encode())),
        ("empty.json", (b"", b"")),
    ):
        path = protected_tree / name
        code, output, sent = terminal_run(path, values)
        assert code == 1
        assert sent == 2
        assert b"refused" in output
        assert not path.exists()


def test_non_tty_stdin_refuses_without_echo_or_creation(protected_tree):
    path = protected_tree / "nonterminal.json"
    password = secrets.token_urlsafe(32).encode()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "human:pipe", "operator", "--output", str(path)],
        input=password + b"\n" + password + b"\n",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert not path.exists()
    if password in result.stdout + result.stderr:
        pytest.fail("nonterminal refusal exposed password input")


@pytest.mark.parametrize("shape", ["existing", "symlink", "parent-symlink", "writable-ancestor"])
def test_terminal_refuses_existing_or_unsafe_targets_before_password_prompt(protected_tree, shape):
    original = protected_tree / "original"
    original.write_bytes(b"retained-original-evidence")
    path = protected_tree / "new.json"
    if shape == "existing":
        path = original
    elif shape == "symlink":
        path.symlink_to(original)
    elif shape == "parent-symlink":
        alias = protected_tree / "alias"
        alias.symlink_to(protected_tree, target_is_directory=True)
        path = alias / "new.json"
    else:
        writable = protected_tree / "writable"
        writable.mkdir(mode=0o770)
        writable.chmod(0o770)
        child = writable / "safe-child"
        child.mkdir(mode=0o700)
        path = child / "new.json"
    password = secrets.token_urlsafe(32).encode()
    code, output, sent = terminal_run(path, (password, password))
    assert code == 1
    assert sent == 0
    assert b"Password:" not in output
    assert original.read_bytes() == b"retained-original-evidence"
    if shape not in {"existing", "symlink"}:
        assert not path.exists()


@pytest.mark.parametrize(
    "value",
    [
        "relative.json",
        "/srv/hfcache/NEVER-PROVISION.json",
        "//host/share/record",
        "/owned/../record",
        "/owned/record\x00",
    ],
)
def test_lexical_or_nas_paths_refuse_before_target_traversal(provisioner, monkeypatch, value):
    def forbidden(*args, **kwargs):
        pytest.fail("unsafe output reached filesystem traversal")

    monkeypatch.setattr(provisioner, "protected_parent", forbidden)
    with pytest.raises(ValueError, match="refused"):
        provisioner.output_path(value)


def test_network_mount_is_refused_before_any_target_open(provisioner, monkeypatch):
    helper = runpy.run_path(str(ROOT / "scripts/fetch-container-python.py"))
    table = (
        "1 0 0:1 / / rw - xfs /dev/root rw\n2 1 0:2 / /owned/network rw - nfs4 server:/export rw\n"
    )

    def local_path(path):
        return helper["local_path"](path, mountinfo=table)

    monkeypatch.setattr(provisioner.runpy, "run_path", lambda _: {"local_path": local_path})
    with pytest.raises(ValueError, match="refused"):
        provisioner.output_path("/owned/network/record.json")


def test_getpass_warning_and_utf8_overflow_refuse_before_creation(provisioner, monkeypatch):
    monkeypatch.setattr(provisioner.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(provisioner.sys.stderr, "isatty", lambda: True)

    def fallback(*args, **kwargs):
        warnings.warn(
            "non-echoing terminal unavailable", provisioner.getpass.GetPassWarning, stacklevel=1
        )
        pytest.fail("getpass warning did not stop input")

    monkeypatch.setattr(provisioner.getpass, "getpass", fallback)
    with pytest.raises(provisioner.getpass.GetPassWarning):
        provisioner.password_input()
    values = iter(("\u00e9" * 513, "\u00e9" * 513))
    monkeypatch.setattr(provisioner.getpass, "getpass", lambda _: next(values))
    with pytest.raises(ValueError, match="refused"):
        provisioner.password_input()


def test_fsync_failure_retains_the_exclusively_created_evidence(
    provisioner, protected_tree, monkeypatch
):
    parent = provisioner.protected_parent(protected_tree / "retained.json")

    def failed_sync(descriptor):
        message = "owned fsync failure"
        raise OSError(message)

    monkeypatch.setattr(provisioner.os, "fsync", failed_sync)
    try:
        with pytest.raises(OSError, match="owned fsync failure"):
            provisioner.write_record(parent, "retained.json", b"retained-owned-write-evidence")
    finally:
        os.close(parent)
    retained = protected_tree / "retained.json"
    assert retained.read_bytes() == b"retained-owned-write-evidence"
    assert stat.S_IMODE(retained.stat().st_mode) == 0o600


def test_untrusted_ancestor_owner_refuses_without_creating_file(
    provisioner, protected_tree, monkeypatch
):
    original = provisioner.os.fstat
    identity = protected_tree.stat().st_ino

    def untrusted(descriptor):
        actual = original(descriptor)
        if actual.st_ino == identity:
            return SimpleNamespace(st_mode=actual.st_mode, st_uid=os.geteuid() + 100000)
        return actual

    with monkeypatch.context() as change:
        change.setattr(provisioner.os, "fstat", untrusted)
        with pytest.raises(ValueError, match="refused"):
            provisioner.protected_parent(protected_tree / "not-created.json")
    assert not (protected_tree / "not-created.json").exists()


def test_exclusive_creation_refuses_a_raced_existing_inode(
    provisioner, protected_tree, monkeypatch
):
    parent = provisioner.protected_parent(protected_tree / "raced.json")
    original = provisioner.os.open
    raced = False

    def race(name, flags, *args, **kwargs):
        nonlocal raced
        if name == "raced.json" and flags & os.O_CREAT and not raced:
            raced = True
            descriptor = original(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, **kwargs)
            try:
                os.write(descriptor, b"original-raced-evidence")
            finally:
                os.close(descriptor)
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(provisioner.os, "open", race)
    try:
        with pytest.raises(FileExistsError):
            provisioner.write_record(parent, "raced.json", b"must-not-replace")
    finally:
        os.close(parent)
    assert (protected_tree / "raced.json").read_bytes() == b"original-raced-evidence"


def test_success_syncs_the_file_then_its_pinned_parent(provisioner, protected_tree, monkeypatch):
    parent = provisioner.protected_parent(protected_tree / "synced.json")
    original = provisioner.os.fsync
    synchronized = []

    def observed_sync(descriptor):
        synchronized.append(stat.S_ISDIR(os.fstat(descriptor).st_mode))
        original(descriptor)

    monkeypatch.setattr(provisioner.os, "fsync", observed_sync)
    try:
        provisioner.write_record(parent, "synced.json", b"owned-sync-evidence")
    finally:
        os.close(parent)
    assert synchronized == [False, True]


def test_safe_help_is_stdlib_only_and_bad_argument_diagnostics_do_not_echo_values():
    result = subprocess.run(
        [sys.executable, "-S", str(SCRIPT), "--help"], capture_output=True, check=False
    )
    assert result.returncode == 0
    assert b"NEW absolute local file" in result.stdout
    marker = secrets.token_hex(24)
    result = subprocess.run(
        [sys.executable, "-S", str(SCRIPT), "--unknown", marker], capture_output=True, check=False
    )
    assert result.returncode == 2
    assert marker.encode() not in result.stdout + result.stderr
