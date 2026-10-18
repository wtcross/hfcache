"""Owned fixtures prove probe refusal, identity ordering and honest evidence."""

import errno
import fcntl
import json
import logging
import os
import subprocess
import sys
import types
from pathlib import Path, PurePosixPath

import pytest

from hfcache.errors import HfcacheError
from tests.fixtures.examples import ARCHIVE_ID, sentinel

ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = ROOT / "scripts/hardening-probe.py"
WRAPPER = ROOT / "scripts/check-hardening.sh"
SECRET = "fixture-private-value-never-render"
BASE_CHECKS = (
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
)


def complete_document():
    return {
        "schema_version": 1,
        "scope": "current probe process only",
        "results": [{"name": name, "state": "pass", "detail": "fixed"} for name in BASE_CHECKS],
    }


@pytest.fixture
def probe(monkeypatch):
    monkeypatch.setattr(sys, "dont_write_bytecode", sys.dont_write_bytecode)
    module = types.ModuleType("hardening_probe_fixture")
    module.__file__ = str(PAYLOAD)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    exec(compile(PAYLOAD.read_text(), str(PAYLOAD), "exec"), module.__dict__)
    return module


@pytest.fixture
def target(tmp_path, probe):
    archive = tmp_path / "archive"
    health = archive / ".store/health"
    health.mkdir(parents=True, mode=0o700)
    archive.chmod(0o750)
    (archive / ".store").chmod(0o700)
    (archive / ".hfcache-root").write_text(sentinel().model_dump_json())
    lock = tmp_path / "probe.lock"
    lock.write_bytes(b"")
    lock.chmod(0o600)
    options = probe.parser().parse_args(
        [
            "--mode",
            "workload",
            "--profile",
            "native",
            "--acknowledge-disposable",
            "--archive-root",
            str(archive),
            "--archive-id",
            ARCHIVE_ID,
            "--lock-file",
            str(lock),
        ]
    )
    device = archive.stat().st_dev
    mount = f"1 0 {os.major(device)}:{os.minor(device)} / / rw - ext4 /dev/fixture rw\n"
    return options, archive, health, lock, mount


def forbid_effects(monkeypatch, probe):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail("effect attempted before explicit target proof")

    monkeypatch.setattr(probe.os, "open", forbidden)
    monkeypatch.setattr(probe.subprocess, "run", forbidden)
    monkeypatch.setattr(probe.socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    return calls


def test_import_has_no_probe_effects(monkeypatch, probe):
    source = PAYLOAD.read_text()
    calls = forbid_effects(monkeypatch, probe)
    exec(compile(source, "probe-import", "exec"), {"__name__": probe.__name__})
    assert not calls


@pytest.mark.parametrize(
    "arguments", [[], ["--dry-run"], ["--mode=workload", "--dry-run"], ["--help"]]
)
def test_default_help_and_dry_run_have_no_effects(monkeypatch, probe, arguments):
    calls = forbid_effects(monkeypatch, probe)
    if "--help" in arguments:
        with pytest.raises(SystemExit) as error:
            probe.main(arguments)
        assert error.value.code == 0
    else:
        assert probe.main(arguments) == 0
    assert not calls


@pytest.mark.parametrize(
    "arguments",
    [
        ["--mode=workload"],
        ["--mode=workload", "--profile=guarded-readonly"],
        ["--mode=workload", "--profile=rootless", "--acknowledge-disposable"],
        ["--mode=inventory"],
        [
            "--mode=workload",
            "--profile=native",
            "--acknowledge-disposable",
            "--archive-root=/srv/hfcache",
            "--archive-id=" + ARCHIVE_ID,
            "--lock-file=/run/lock",
        ],
    ],
)
def test_missing_or_readonly_authority_refuses_before_access(monkeypatch, probe, arguments):
    calls = forbid_effects(monkeypatch, probe)
    assert probe.main(["--wrapper", *arguments]) == 2
    assert not calls


@pytest.mark.parametrize(
    "arguments",
    [[], ["--help"], ["--dry-run"], ["--mode=workload", "--profile=native", "--dry-run"]],
)
def test_shell_static_entrypoints_do_not_call_manager_or_native_python(tmp_path, arguments):
    manager = tmp_path / "systemctl"
    marker = tmp_path / "manager-called"
    manager.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 99\n")
    manager.chmod(0o755)
    result = subprocess.run(
        ["bash", str(WRAPPER), *arguments],
        check=False,
        capture_output=True,
        text=True,
        env=dict(os.environ) | {"PATH": str(tmp_path) + ":" + os.environ["PATH"]},
    )
    assert result.returncode == 0, result.stderr
    assert not marker.exists()


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "//",
        "/tmp/..",
        "/tmp/./archive",
        "/tmp//archive",
        "/tmp/archive/",
        "relative",
        "/tmp/a%u",
        "/tmp/a b",
    ],
)
def test_noncanonical_or_unit_expanded_paths_refuse(probe, path):
    with pytest.raises(probe.RefusedError):
        probe.canonical_path(path)


def test_inventory_uses_installed_dropins_and_never_exposes_values(probe, monkeypatch, capsys):
    observed = []

    def manager(arguments, **kwargs):
        observed.append(arguments)
        return subprocess.CompletedProcess(
            arguments,
            0,
            "[Service]\nNoNewPrivileges=true\n"
            f"Environment=HF_TOKEN={SECRET}\nLoadCredential={SECRET}\n"
            "ExecStartPre=bad\nRestart=always\nStateDirectory=hfcache\n"
            "[Service]\nProtectClock=true\nInaccessiblePaths=/protected\n",
            "",
        )

    monkeypatch.setattr(probe.subprocess, "run", manager)
    assert probe.main(["--mode=inventory", "--profile=native"]) == 0
    output = capsys.readouterr().out
    assert observed == [["systemctl", "cat", "--no-pager", "hfcache-api.service"]]
    assert "NoNewPrivileges" in output
    assert "ProtectClock" in output
    assert "InaccessiblePaths" in output
    assert all(
        value not in output for value in (SECRET, "ExecStartPre", "Restart", "StateDirectory")
    )


@pytest.mark.parametrize(
    "failure",
    [
        ImportError(SECRET),
        TimeoutError(SECRET),
        OSError(errno.EIO, SECRET),
        OSError(errno.ENOENT, SECRET),
        OSError(errno.ECONNREFUSED, SECRET),
        OSError(errno.ETIMEDOUT, SECRET),
        RuntimeError(SECRET),
    ],
)
def test_unrelated_failures_never_certify_isolation(probe, failure):
    def action():
        raise failure

    result = probe.check("controlled fixture", action, denied=True)
    assert result.state == "not_proven"
    assert SECRET not in result.detail


@pytest.mark.parametrize("code", [errno.EACCES, errno.EPERM])
def test_only_expected_action_denials_pass_without_attributing_control(probe, code):
    def action():
        raise OSError(code, SECRET)

    result = probe.check("controlled fixture", action, denied=True)
    assert result.state == "pass"
    assert "not attributed" in result.detail
    assert SECRET not in result.detail


def test_capture_prerequisite_denial_is_not_action_denial(probe, monkeypatch):
    def refuse(*args, **kwargs):
        raise PermissionError(errno.EACCES, SECRET)

    monkeypatch.setattr(probe.os, "dup", refuse)
    assert probe.check("controlled fixture", lambda: None, denied=True).state == "not_proven"


def test_dependency_streams_native_stderr_and_logging_are_discarded(probe, capfd):
    def noisy():
        assert not sys.stderr.isatty()
        assert sys.stderr.encoding == "utf-8"
        assert sys.stderr.fileno() == 2
        sys.stderr.buffer.write(SECRET.encode())
        sys.stdout.write(SECRET)
        sys.stderr.write(SECRET)
        os.write(2, SECRET.encode())
        logging.getLogger("fixture-dependency").error(SECRET)
        raise ImportError(SECRET)

    assert probe.check("controlled fixture", noisy).state == "not_proven"
    captured = capfd.readouterr()
    assert SECRET not in captured.out + captured.err


def test_owned_workload_hashes_and_cleans_only_health_artifacts(probe, target):
    options, archive, health, lock, mount = target
    original = lock.stat().st_ino
    with (
        probe.target_scope(options, mount_text=mount) as descriptor,
        probe.owned_health_directory(descriptor) as owned,
    ):
        assert "completed" in probe.file_workload(owned)
    assert list(health.iterdir()) == []
    assert not (archive / ".hfcache-hardening-probe").exists()
    assert lock.stat().st_ino == original


@pytest.mark.parametrize("broken", ["missing", "malformed", "wrong-id", "future", "duplicate"])
def test_identity_failure_precedes_all_writes(probe, target, monkeypatch, broken):
    options, archive, health, _, mount = target
    path = archive / ".hfcache-root"
    if broken == "missing":
        path.unlink()
    elif broken == "malformed":
        path.write_text(SECRET)
    elif broken == "wrong-id":
        options.archive_id = "00000000-0000-4000-8000-000000000001"
    elif broken == "future":
        document = json.loads(path.read_text())
        document["schema_version"] = 999
        path.write_text(json.dumps(document))
    else:
        path.write_text(
            path.read_text().replace('"schema_version":1', '"schema_version":1,"schema_version":1')
        )
    writes = []
    monkeypatch.setattr(probe.os, "mkdir", lambda *a, **_kwargs: writes.append(a))
    with (
        pytest.raises((FileNotFoundError, json.JSONDecodeError, probe.RefusedError, HfcacheError)),
        probe.target_scope(options, mount_text=mount),
    ):
        pytest.fail("invalid identity permitted")
    assert not writes
    assert not list(health.iterdir())


@pytest.mark.parametrize("part", ["root", "store", "health", "sentinel", "lock"])
def test_symlink_components_refuse_before_writes(probe, target, part):
    options, archive, health, lock, mount = target
    path = {
        "root": archive,
        "store": archive / ".store",
        "health": health,
        "sentinel": archive / ".hfcache-root",
        "lock": lock,
    }[part]
    preserved = path.with_name(path.name + "-preserved")
    path.rename(preserved)
    path.symlink_to(preserved, target_is_directory=preserved.is_dir())
    with (
        pytest.raises(OSError, match=r"Too many levels|Not a directory"),
        probe.target_scope(options, mount_text=mount),
    ):
        pytest.fail("symlink accepted")


@pytest.mark.parametrize("part", ["sentinel", "lock"])
def test_fifo_cannot_hang_target_proof(target, part):
    options, archive, _, lock, _ = target
    path = archive / ".hfcache-root" if part == "sentinel" else lock
    path.unlink()
    os.mkfifo(path, 0o600)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(PAYLOAD),
            "--mode=workload",
            "--profile=native",
            "--acknowledge-disposable",
            "--archive-root",
            str(archive),
            "--archive-id",
            options.archive_id,
            "--lock-file",
            str(lock),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_held_lock_refuses_without_replacing_inode(probe, target):
    options, _, health, lock, mount = target
    with lock.open("rb") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError), probe.target_scope(options, mount_text=mount):
            pytest.fail("held lock accepted")
    assert not list(health.iterdir())


def test_same_inode_mode_change_is_revalidated_under_lock(probe, target, monkeypatch):
    options, _, health, _, mount = target
    original = fcntl.flock

    def changed(descriptor, flags):
        original(descriptor, flags)
        health.chmod(0o755)

    monkeypatch.setattr(probe.fcntl, "flock", changed)
    with (
        pytest.raises(probe.RefusedError, match="private"),
        probe.target_scope(options, mount_text=mount),
    ):
        pytest.fail("same inode mode drift accepted")
    assert not list(health.iterdir())


def test_replaced_lock_parent_is_not_a_valid_lock(probe, target, monkeypatch, tmp_path):
    options, _, health, lock, mount = target
    parent = tmp_path / "locks"
    parent.mkdir(mode=0o700)
    moved_lock = parent / lock.name
    lock.rename(moved_lock)
    options.lock_file = str(moved_lock)
    original = fcntl.flock

    def changed(descriptor, flags):
        original(descriptor, flags)
        parent.rename(tmp_path / "old-locks")
        parent.mkdir(mode=0o700)

    monkeypatch.setattr(probe.fcntl, "flock", changed)
    with (
        pytest.raises(probe.RefusedError, match="parent changed"),
        probe.target_scope(options, mount_text=mount),
    ):
        pytest.fail("replaced lock parent accepted")
    assert not list(health.iterdir())


def test_production_alias_and_remote_lock_refuse_without_io(probe):
    rows = probe.mount_rows(
        "1 0 8:1 / / rw - ext4 /dev/root rw\n"
        "2 1 0:50 / /srv/hfcache ro - nfs4 nas:/archive ro\n"
        "3 1 0:50 / /tmp/alias rw - nfs4 192.0.2.1:/alias rw\n"
    )
    assert rows[-1][4] == "0:50"
    with pytest.raises(probe.RefusedError, match="production mount"):
        probe.prove_locality(PurePosixPath("/tmp/alias"), PurePosixPath("/tmp/lock"), "nfs", rows)
    with pytest.raises(probe.RefusedError):
        probe.prove_locality(
            PurePosixPath("/tmp/local"), PurePosixPath("/tmp/alias/lock"), "local", rows
        )


def test_duplicate_and_replaced_entries_are_preserved(probe, tmp_path):
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        unknown = tmp_path / "source"
        unknown.write_text(SECRET)
        with pytest.raises(FileExistsError):
            probe.file_workload(descriptor)
        assert unknown.read_text() == SECRET
        expected = (unknown.stat().st_dev, unknown.stat().st_ino)
        unknown.rename(tmp_path / "preserved-source")
        unknown.write_text("replacement")
        with pytest.raises(probe.RefusedError, match="preserved"):
            probe.cleanup_owned(descriptor, {"source": expected})
        assert unknown.read_text() == "replacement"
    finally:
        os.close(descriptor)


@pytest.mark.parametrize(
    "name", ["HF_TOKEN", "CREDENTIALS_DIRECTORY", "HFCACHE_API_TOKEN", "HFCACHE_MCP_TOKEN"]
)
def test_verifier_environment_refuses_without_rendering_values(probe, monkeypatch, name):
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv(name, SECRET)
    result = probe.credential_observation(None)
    assert result.state == "fail"
    assert SECRET not in result.detail


def test_credential_open_never_reads_bytes_or_calls_dac_denial_mask_proof(
    probe, monkeypatch, tmp_path
):
    for name in probe.FORBIDDEN_CREDENTIAL_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    path = tmp_path / "synthetic-secret"
    path.write_text(SECRET)
    assert probe.credential_observation(str(path)).state == "fail"
    assert probe.credential_observation(str(tmp_path / "missing")).state == "not_proven"


def test_untrusted_transient_output_is_never_relayed(probe, capsys):
    completed = subprocess.CompletedProcess([], 1, SECRET, SECRET)
    assert probe.render_transient_result(completed) == 2
    assert SECRET not in capsys.readouterr().out


def test_target_proof_precedes_manager_and_safe_transient_properties(probe, target, monkeypatch):
    _options, archive, _, lock, mount = target
    calls = []
    original_scope = probe.target_scope

    def scope(current, **kwargs):
        calls.append("identity")
        return original_scope(current, mount_text=mount, **kwargs)

    def manager(arguments, **kwargs):
        calls.append(arguments)
        if arguments[0] == "systemctl":
            assert calls[0] == "identity"
            return subprocess.CompletedProcess(
                arguments,
                0,
                "[Service]\nUser=fixture\n"
                "ProtectSystem=strict\nInaccessiblePaths=/protected\n"
                f"Environment=HF_TOKEN={SECRET}\nLoadCredential={SECRET}\n"
                "ExecStartPre=bad\nStateDirectory=hfcache\nReadWritePaths=/production\n",
                "",
            )
        assert arguments[0] == "systemd-run"
        assert calls[-2] == "identity"
        joined = " ".join(arguments)
        assert SECRET not in joined
        assert "StateDirectory" not in joined
        assert "ExecStartPre" not in joined
        assert "/production" not in joined
        assert f"ReadWritePaths={archive}/.store/health" in joined
        assert "InaccessiblePaths=/protected" in joined
        assert "PYTHONDONTWRITEBYTECODE=1" in joined
        document = complete_document()
        return subprocess.CompletedProcess(arguments, 0, json.dumps(document), "")

    monkeypatch.setattr(probe, "target_scope", scope)
    monkeypatch.setattr(probe.os, "geteuid", lambda: 0)
    monkeypatch.setattr(probe.pwd, "getpwnam", lambda _: types.SimpleNamespace(pw_uid=os.getuid()))
    monkeypatch.setattr(probe.subprocess, "run", manager)
    assert (
        probe.main(
            [
                "--wrapper",
                "--native-runtime",
                "--mode=workload",
                "--profile=native",
                "--acknowledge-disposable",
                "--archive-root",
                str(archive),
                "--archive-id",
                ARCHIVE_ID,
                "--lock-file",
                str(lock),
            ]
        )
        == 0
    )


def test_invalid_target_never_reaches_manager(probe, target, monkeypatch):
    _, archive, _, lock, mount = target
    (archive / ".hfcache-root").unlink()
    original_scope = probe.target_scope
    monkeypatch.setattr(
        probe,
        "target_scope",
        lambda options, **kwargs: original_scope(options, mount_text=mount, **kwargs),
    )
    calls = []
    monkeypatch.setattr(probe.subprocess, "run", lambda *args, **_kwargs: calls.append(args))
    assert (
        probe.main(
            [
                "--wrapper",
                "--native-runtime",
                "--mode=workload",
                "--profile=native",
                "--acknowledge-disposable",
                "--archive-root",
                str(archive),
                "--archive-id",
                ARCHIVE_ID,
                "--lock-file",
                str(lock),
            ]
        )
        == 2
    )
    assert not calls


def test_transient_result_state_cannot_be_overridden_by_manager_success(probe, capsys):
    document = complete_document()
    document["results"][-1].update(state="fail", detail=SECRET)
    completed = subprocess.CompletedProcess([], 0, json.dumps(document), SECRET)
    assert probe.render_transient_result(completed) == 1
    assert SECRET not in capsys.readouterr().out


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "bool-version", "missing-verifier", "missing-network"]
)
def test_incomplete_or_ambiguous_transient_evidence_cannot_pass(probe, change):
    document = complete_document()
    options: dict[str, str | bool] = {}
    if change == "missing":
        document["results"].pop()
    elif change == "duplicate":
        document["results"].append(document["results"][0])
    elif change == "bool-version":
        document["schema_version"] = True
    elif change == "missing-verifier":
        options["unit"] = "hfcache-verification.service"
    else:
        options["allow_network"] = True
    completed = subprocess.CompletedProcess([], 0, json.dumps(document), "")
    assert probe.render_transient_result(completed, **options) == 2


def test_expected_checks_match_the_documented_base_role_and_network_scope(probe):
    assert probe.expected_result_names("hfcache-api.service") == set(BASE_CHECKS)
    assert probe.expected_result_names("hfcache-verification.service") == set(BASE_CHECKS) | {
        "verifier credential scope",
        "verifier IPv4 action",
        "verifier IPv6 action",
    }
    assert probe.expected_result_names("hfcache-api.service", allow_network=True) == set(
        BASE_CHECKS
    ) | {"API DNS", "API TLS", "API Hub metadata", "API download"}


def test_stale_lock_mount_evidence_refuses_before_writes(probe, target):
    options, _, health, lock, mount = target
    mount += f"2 1 250:99 / {lock} rw - ext4 /dev/stale rw\n"
    with (
        pytest.raises(probe.RefusedError, match="mount identity changed"),
        probe.target_scope(options, mount_text=mount),
    ):
        pytest.fail("stale lock locality accepted")
    assert not list(health.iterdir())


@pytest.mark.parametrize("location", ["health-submount", "remote-ancestor"])
def test_hidden_remote_mount_refuses_before_archive_metadata_access(
    probe, target, monkeypatch, location
):
    options, archive, health, _, mount = target
    if location == "health-submount":
        mount += f"2 1 0:50 / {health} rw - nfs4 nas:/unknown rw\n"
    else:
        parent = archive.parent
        mount += f"2 1 0:50 / {parent} rw - nfs4 nas:/unknown rw\n"
        device = archive.stat().st_dev
        mount += f"3 2 {os.major(device)}:{os.minor(device)} / {archive} rw - ext4 /dev/local rw\n"
    calls = []
    monkeypatch.setattr(probe.os, "open", lambda *args, **_kwargs: calls.append(args))
    with (
        pytest.raises(probe.RefusedError, match=r"submounts|traversal"),
        probe.target_scope(options, mount_text=mount),
    ):
        pytest.fail("remote path traversal permitted")
    assert not calls


def test_readonly_mount_refuses_before_opening_target(probe, target, monkeypatch):
    options, _, _, _, mount = target
    calls = []
    monkeypatch.setattr(probe.os, "open", lambda *args, **_kwargs: calls.append(args))
    with (
        pytest.raises(probe.RefusedError, match="read-only"),
        probe.target_scope(options, mount_text=mount.replace("/ rw -", "/ ro -")),
    ):
        pytest.fail("read-only target accepted")
    assert not calls


def test_oversized_sentinel_refuses_before_writes(probe, target):
    options, archive, health, _, mount = target
    (archive / ".hfcache-root").write_bytes(b"x" * (probe.MAX_SENTINEL_BYTES + 1))
    with (
        pytest.raises(probe.RefusedError, match="bounded"),
        probe.target_scope(options, mount_text=mount),
    ):
        pytest.fail("oversized sentinel accepted")
    assert not list(health.iterdir())


def test_same_inode_sentinel_content_change_is_revalidated(probe, target, monkeypatch):
    options, archive, health, _, mount = target
    original = fcntl.flock
    path = archive / ".hfcache-root"

    def changed(descriptor, flags):
        original(descriptor, flags)
        document = json.loads(path.read_text())
        document["created_by"]["hostname"] = "different-fixture-host"
        path.write_text(json.dumps(document))

    monkeypatch.setattr(probe.fcntl, "flock", changed)
    with (
        pytest.raises(probe.RefusedError, match="sentinel changed"),
        probe.target_scope(options, mount_text=mount),
    ):
        pytest.fail("same inode sentinel modification accepted")
    assert not list(health.iterdir())
