"""Read-only probe planning and isolated credential assertions (API-014)."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts/check-hardening.sh"
FORBIDDEN = (
    "CREDENTIALS_DIRECTORY",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "HUGGINGFACEHUB_API_TOKEN",
    "HF_TOKEN_PATH",
    "HFCACHE_API_TOKEN",
    "HFCACHE_MCP_TOKEN",
)


@pytest.mark.parametrize("unit", ["hfcache-api.service", "hfcache-verification.service"])
def test_dry_run_reads_actual_executor_properties_without_host_operations(unit):
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--dry-run",
            "--unit-directory",
            str(ROOT / "packaging/systemd"),
            unit,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert unit in result.stdout
    assert "NoNewPrivileges" in result.stdout
    assert "RuntimeDirectoryPreserve" in result.stdout
    assert "ExecStart" not in result.stdout
    assert "dry run: no transient unit" in result.stdout


@pytest.mark.parametrize("unit", ["hfcache-sync.service", "hfcache-verify.service"])
def test_client_wrapper_cannot_be_mistaken_for_executor_evidence(unit):
    result = subprocess.run(
        ["bash", str(WRAPPER), "--dry-run", unit],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "actual API or verification executor" in result.stderr


def test_property_diagnostics_never_echo_values_or_run_hooks(tmp_path):
    marker = tmp_path / "hook-ran"
    (tmp_path / "hfcache-api.service").write_text(
        "[Service]\nNoNewPrivileges=true\nEnvironment=HF_TOKEN=fixture-secret-value\n"
        f"ExecStartPre=/usr/bin/touch {marker}\nRestart=on-failure\n"
        "Sockets=production.socket\n"
    )
    result = subprocess.run(
        ["bash", str(WRAPPER), "--dry-run", "--unit-directory", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Environment" in result.stdout
    assert "fixture-secret-value" not in result.stdout
    assert "ExecStartPre" not in result.stdout
    assert "Restart" not in result.stdout
    assert "Sockets" not in result.stdout
    assert not marker.exists()


def test_installed_dropins_are_included_through_manager_cat(tmp_path):
    manager = tmp_path / "systemctl"
    manager.write_text(
        '#!/bin/sh\n[ "$1" = cat ] || exit 1\n'
        "printf '[Service]\\nNoNewPrivileges=true\\n[Service]\\nProtectClock=true\\n'\n"
    )
    manager.chmod(0o755)
    result = subprocess.run(
        ["bash", str(WRAPPER), "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        env=dict(os.environ) | {"PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]},
    )
    assert result.returncode == 0, result.stderr
    assert "NoNewPrivileges" in result.stdout
    assert "ProtectClock" in result.stdout


@pytest.fixture
def credential_check(monkeypatch, tmp_path):
    # Importing the full operator probe would intentionally exercise a live
    # sandbox/archive. Compile only this repository-owned pure assertion body.
    source = ast.parse((ROOT / "scripts/hardening-probe.py").read_text())
    function = next(
        item
        for item in source.body
        if isinstance(item, ast.FunctionDef) and item.name == "_executor_credentials"
    )
    function.decorator_list = []
    scope = {"os": os, "OFFLINE": True}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "credential-probe", "exec"), scope)
    for name in FORBIDDEN:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("HFCACHE_PROBE_CREDENTIAL", str(tmp_path / "synthetic-source"))
    return scope["_executor_credentials"]


@pytest.mark.parametrize("name", FORBIDDEN)
def test_worker_probe_rejects_every_credential_environment_source(
    credential_check, monkeypatch, name
):
    monkeypatch.setenv(name, "fixture-value")
    with pytest.raises(AssertionError, match="credential environment"):
        credential_check()


def test_worker_probe_requires_startup_library_offline_flag(credential_check, monkeypatch):
    monkeypatch.delenv("HF_HUB_OFFLINE")
    with pytest.raises(AssertionError, match="offline flag"):
        credential_check()


def test_worker_probe_checks_open_permission_without_reading_secret_bytes(
    credential_check, tmp_path
):
    path = tmp_path / "synthetic-source"
    path.write_bytes(b"fixture-value-never-read")
    with pytest.raises(AssertionError, match="source is accessible") as error:
        credential_check()
    assert "fixture-value-never-read" not in str(error.value)


@pytest.mark.parametrize("failure", [FileNotFoundError, PermissionError])
def test_root_verified_source_hidden_by_sandbox_is_accepted(credential_check, monkeypatch, failure):
    def refuse(*args, **kwargs):
        raise failure

    monkeypatch.setattr(os, "open", refuse)
    assert "inaccessible" in credential_check()


def test_unexpected_source_io_failure_is_not_isolation_proof(credential_check, monkeypatch):
    def refuse(*args, **kwargs):
        message = "synthetic IO failure"
        raise OSError(message)

    monkeypatch.setattr(os, "open", refuse)
    with pytest.raises(OSError, match="synthetic IO"):
        credential_check()


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "//",
        "/tmp/..",
        "/srv/hfcache/../..",
        "/tmp/./archive",
        "/tmp//archive",
        "/tmp/archive/",
        "relative",
    ],
)
def test_noncanonical_probe_archive_refuses_before_service_access(path):
    result = subprocess.run(
        ["bash", str(WRAPPER), "--dry-run", "--archive-root", path],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "absolute non-root path" in result.stderr


def test_probe_uses_actual_systemd_managed_paths_for_each_executor(monkeypatch, tmp_path):
    paths = [tmp_path / name for name in ("archive", "state", "worker-cache", "runtime")]
    for path in paths:
        path.mkdir()
    for name, path in zip(
        ("STATE_DIRECTORY", "CACHE_DIRECTORY", "RUNTIME_DIRECTORY"), paths[1:], strict=True
    ):
        monkeypatch.setenv(name, str(path))
    source = ast.parse((ROOT / "scripts/hardening-probe.py").read_text())
    function = next(
        item
        for item in source.body
        if isinstance(item, ast.FunctionDef) and item.name == "_writable_paths"
    )
    function.decorator_list = []
    scope: dict[str, object] = {"os": os, "Path": Path, "ARCHIVE": paths[0]}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "writable-probe", "exec"), scope)
    check_paths = scope["_writable_paths"]
    assert callable(check_paths)
    result = check_paths()
    assert isinstance(result, str)
    assert all(str(path) in result for path in paths)
    assert all(list(path.iterdir()) == [] for path in paths)


def test_direct_probe_invocation_stops_before_any_sandbox_or_archive_work(tmp_path):
    environment = dict(os.environ)
    environment.pop("HFCACHE_PROBE_EXECUTOR", None)
    archive = tmp_path / "never-created"
    environment["HFCACHE_PROBE_ARCHIVE"] = str(archive)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/hardening-probe.py")],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 2
    assert "check-hardening.sh wrapper" in result.stderr
    assert not archive.exists()
