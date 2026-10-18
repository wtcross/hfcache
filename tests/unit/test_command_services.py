"""Typed commands preserve explicit guards, refusal payloads and execution identity."""

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hfcache import locking, storage
from hfcache.archive import initialize_archive
from hfcache.cli import app
from hfcache.config import ApplicationConfig
from hfcache.errors import ExitCode, IntegrityError
from hfcache.reporting import RecoveryReport
from hfcache.services import commands
from hfcache.services.context import ExecutionContext
from hfcache.storage import parse_mount_table, read_model
from tests.unit.test_command_locking import _assert_lock_owned
from tests.unit.test_verification import ARCHIVE_ID, MODEL, SHA_A, nfs_line, publish


@pytest.fixture
def service(tmp_path, monkeypatch):
    root = tmp_path / "archive"
    root.mkdir()
    mount_table = tmp_path / "mountinfo"
    mount_table.write_text(nfs_line(str(root)), encoding="utf-8")
    monkeypatch.setattr(storage, "MOUNT_TABLE", mount_table)
    monkeypatch.setattr(locking, "LOCK_DIRECTORY", tmp_path / "run")
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {
                "archive_root": str(root),
                "archive_id": ARCHIVE_ID,
                "minimum_free_space_gib": 0,
                "minimum_free_space_percent": 0,
            },
            "sync": {"lock_wait_seconds": 0},
            "verification": {"lock_wait_seconds": 0},
        }
    )
    return commands.CommandServices(config, ExecutionContext.create())


def _initialize(service):
    initialize_archive(
        service.layout,
        archive_id=ARCHIVE_ID,
        table=parse_mount_table(nfs_line(str(service.layout.root))),
    )


def test_initialization_owns_one_common_lock_before_inspection_and_creation(service, monkeypatch):
    original_inspect = commands.LocalQueries.inspect_archive
    original_initialize = commands.initialize_archive
    observed = []

    def inspect(self):
        _assert_lock_owned(locking.lock_path())
        observed.append("inspection")
        return original_inspect(self)

    def initialize(*args, **kwargs):
        _assert_lock_owned(locking.lock_path())
        observed.append("initialization")
        return original_initialize(*args, **kwargs)

    monkeypatch.setattr(commands.LocalQueries, "inspect_archive", inspect)
    monkeypatch.setattr(commands, "initialize_archive", initialize)
    result = service.initialize_archive(
        commands.InitializationRequest(service.layout.root, confirm=True)
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert observed == ["inspection", "initialization"]
    assert service.layout.sentinel.is_file()
    with locking.exclusive_lock(locking.lock_path(), command="after init", wait_seconds=0):
        pass


def test_initialization_refuses_busy_writer_but_inspection_remains_available(service):
    with locking.exclusive_lock(locking.lock_path(), command="another writer", wait_seconds=0):
        result = service.initialize_archive(
            commands.InitializationRequest(service.layout.root, confirm=True)
        )
        inspected = service.initialize_archive(
            commands.InitializationRequest(service.layout.root, inspect=True)
        )

    assert result.exit_code == ExitCode.SAFETY
    assert [problem.code for problem in result.errors] == ["HFMNT010"]
    assert inspected.exit_code == ExitCode.SUCCESS
    assert inspected.data["initializable"]
    assert not service.layout.sentinel.exists()


def test_probing_doctor_locks_without_requiring_a_sentinel(service, monkeypatch):
    original = commands.storage_checks
    observed = []

    def probe(*args, **kwargs):
        _assert_lock_owned(locking.lock_path())
        observed.append("storage checks")
        return original(*args, **kwargs)

    monkeypatch.setattr(commands, "storage_checks", probe)
    monkeypatch.setattr(commands, "hub_checks", lambda *_args: [])
    result = service.diagnose(commands.DoctorRequest())

    assert result.exit_code == ExitCode.SUCCESS
    assert observed == ["storage checks"]
    sentinel = next(check for check in result.data["checks"] if check["name"] == "sentinel")
    assert sentinel["outcome"] == "skipped"
    assert not service.layout.sentinel.exists()


def test_doctor_readonly_ignores_held_lock_and_probing_doctor_refuses_it(service, monkeypatch):
    _initialize(service)
    monkeypatch.setattr(commands, "hub_checks", lambda *_args: [])
    with locking.exclusive_lock(locking.lock_path(), command="sync", wait_seconds=0):
        readonly = service.diagnose(commands.DoctorRequest(read_only=True))
        probing = service.diagnose(commands.DoctorRequest())

    assert readonly.exit_code == ExitCode.SUCCESS
    assert readonly.data["checks"]
    assert probing.exit_code == ExitCode.SAFETY
    assert [problem.code for problem in probing.errors] == ["HFMNT010"]
    assert list(service.layout.health.iterdir()) == []


def test_recovery_result_carries_the_exact_durable_report_identity(service):
    _initialize(service)
    result = service.recover(commands.MaintenanceRequest(apply=True))

    assert result.exit_code == ExitCode.SUCCESS
    report = read_model(
        service.layout.root / result.data["report"],
        RecoveryReport,
        error=IntegrityError,
        code="HFVER007",
    )
    assert result.run_id == report.run_id == service.context.run_id
    assert result.envelope(service.context).run_id == report.run_id


@pytest.mark.parametrize("selector", ["not-a-selector", MODEL.selector])
def test_malformed_repair_refusal_precedes_missing_configuration(tmp_path, selector):
    result = CliRunner().invoke(
        app, ["--json", "--config", str(tmp_path / "absent.toml"), "repair", selector]
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG001"


@pytest.mark.parametrize("json_output", [False, True])
def test_verification_persistence_failure_preserves_partial_payload_and_quiet_error(
    service, tmp_path, monkeypatch, json_output
):
    _initialize(service)
    publish(service.layout)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'schema_version = 1\n[storage]\narchive_root = "{service.layout.root}"\n'
        f'archive_id = "{ARCHIVE_ID}"\n'
        "minimum_free_space_gib = 0\nminimum_free_space_percent = 0\n",
        encoding="utf-8",
    )

    def refuse(*args, **kwargs):
        message = "verification report could not be persisted"
        raise IntegrityError.single(message, code="HFVER007")

    monkeypatch.setattr(commands, "persist_verification", refuse)
    arguments = ["--quiet", "--config", str(config_path)]
    if json_output:
        arguments.append("--json")
    result = CliRunner().invoke(
        app, [*arguments, "verify", "--revision", f"{MODEL.selector}@{SHA_A}"]
    )

    assert result.exit_code == ExitCode.INTEGRITY
    if json_output:
        envelope = json.loads(result.stdout)
        assert envelope["data"]["verification_outcome"] == "clean"
        assert "report" not in envelope["data"]
        assert envelope["errors"][0]["code"] == "HFVER007"
    else:
        assert "HFVER007" in result.stderr
        assert "could not be persisted" in result.stderr
    with locking.exclusive_lock(locking.lock_path(), command="after failure", wait_seconds=0):
        pass


def test_cli_imports_only_service_or_bootstrap_interfaces():
    tree = ast.parse((Path(__file__).parents[2] / "src" / "hfcache" / "cli.py").read_text())
    forbidden = {
        "archive",
        "sync",
        "verification",
        "retention",
        "purge",
        "recovery",
        "repair",
        "quarantine",
        "transactions",
        "locking",
        "hub",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("hfcache."):
            assert (node.module or "").split(".")[1] not in forbidden
