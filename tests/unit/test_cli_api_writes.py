"""Writer CLI commands preserve actual authenticated operation results (API-013)."""

import json
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from hfcache import cli
from hfcache.errors import IntegrityError
from hfcache.hub import HubClient
from hfcache.paths import RepositoryLayout
from hfcache.publication import read_reference
from tests.api_cli import api_cli
from tests.unit.test_api_commands import configured as command_archive  # noqa: F401 - fixture
from tests.unit.test_synchronize import CONTENT, DATASET, MODEL, SHA_A


@pytest.fixture
def configured(request):
    return request.getfixturevalue("command_archive")


@pytest.mark.parametrize(
    ("arguments", "route"),
    [
        (["sync", MODEL.selector], "syncs"),
        (["verify", "--full"], "verifications"),
        (["verify", "--new"], "verifications"),
        (["verify", "--revision", f"{MODEL.selector}@{SHA_A}"], "verifications"),
        (["doctor"], "diagnostics"),
        (["prune", "--dry-run"], "prune-plans"),
        (["prune", "--apply"], "prunes"),
        (["purge", "--dry-run", "--all-unmanaged"], "purge-plans"),
        (["purge", "--apply", "--all-unmanaged"], "purges"),
        (["recover", "--dry-run"], "recovery-plans"),
        (["recover", "--apply"], "recoveries"),
        (["quarantine", "--dry-run", "a" * 32], "quarantine-plans"),
        (["quarantine", "--apply", "a" * 32], "quarantine-cleanups"),
        (["repair", f"{MODEL.selector}@{SHA_A}"], "repairs"),
    ],
)
def test_writer_cli_emits_exact_real_terminal_result(configured, arguments, route):
    policy, _, _, _ = configured
    with api_cli(policy.archive_config) as remote:
        result = remote.invoke(["--quiet", "--idempotency-key", "writer-route", *arguments])
        (receipt,) = remote.application.state.operations.list()
        assert receipt.route == "/api/v1/" + route
        terminal = remote.application.state.operations.result(receipt.operation_id)
        assert result.exit_code == terminal.exit_code, result.output
        assert json.loads(result.stdout) == terminal.to_payload()
        assert len(result.stdout.splitlines()) == 1
        assert "Idempotency key: writer-route" in result.stderr
        assert f"Operation: {receipt.operation_id}" in result.stderr
        assert "event=" not in result.stderr


@pytest.mark.parametrize("mode", ["--dry-run", "--apply"])
def test_explicit_unmanaged_purge_cli_scope_keeps_configured_repository(
    configured, monkeypatch, mode
):
    policy, layout, _, _ = configured
    monkeypatch.setattr("hfcache.purge.delete_cache_revisions", lambda *_args: 0)
    with api_cli(policy.archive_config) as remote:
        assert remote.invoke(["sync"]).exit_code == 0
        policy.archive_config.write_text(
            policy.archive_config.read_text().replace(
                '[[repositories]]\nid = "organization/model-name"\ntype = "model"\n', ""
            )
        )
        result = remote.invoke(["purge", mode, MODEL.selector])
        assert result.exit_code == 0, result.output
        envelope = json.loads(result.stdout)
        if mode == "--dry-run":
            assert [row["repository_id"] for row in envelope["data"]["plans"]] == [MODEL.id]
            assert RepositoryLayout(layout, MODEL).current_ref.is_file()
        else:
            assert not RepositoryLayout(layout, MODEL).directory.exists()
        assert RepositoryLayout(layout, DATASET).current_ref.is_file()
        receipt = next(
            row
            for row in remote.application.state.operations.list()
            if row.domain_run_id == envelope["run_id"]
        )
        assert receipt.route == ("/api/v1/purge-plans" if mode == "--dry-run" else "/api/v1/purges")
        assert (
            remote.application.state.operations.result(receipt.operation_id).to_payload()
            == envelope
        )


def test_repair_reason_cli_is_persisted_with_exact_terminal_identity(configured):
    policy, layout, _, _ = configured
    reason = "REST parity reviewed replacement"
    with api_cli(policy.archive_config) as remote:
        assert remote.invoke(["sync", MODEL.selector]).exit_code == 0
        repository = RepositoryLayout(layout, MODEL)
        original = read_reference(layout, repository.current_ref)
        (layout.published / original.tree / "weights.bin").write_bytes(b"damaged parity fixture")
        result = remote.invoke(["repair", f"{MODEL.selector}@{SHA_A}", "--reason", reason])
        assert result.exit_code == 0, result.output
        envelope = json.loads(result.stdout)
        retirement = json.loads((layout.root / envelope["data"]["retirement_record"]).read_text())
        assert retirement["reason"] == reason
        replacement = read_reference(layout, repository.current_ref)
        assert replacement.publication_id != original.publication_id
        assert (layout.published / replacement.tree / "weights.bin").read_bytes() == CONTENT[
            "weights.bin"
        ]
        assert (
            layout.published / original.tree / "weights.bin"
        ).read_bytes() == b"damaged parity fixture"
        receipt = next(
            row
            for row in remote.application.state.operations.list()
            if row.domain_run_id == envelope["run_id"]
        )
        assert receipt.route == "/api/v1/repairs"
        assert (
            remote.application.state.operations.result(receipt.operation_id).to_payload()
            == envelope
        )


def test_sync_cli_keeps_failure_aggregation_priority_and_report_identity(configured, monkeypatch):
    policy, layout, hub, _ = configured
    del hub.heads[MODEL.selector]

    def integrity_failure(*_args, **_kwargs):
        message = "synthetic unusable manifest"
        raise IntegrityError.single(message, code="HFVER007")

    monkeypatch.setattr(HubClient, "verify_local", integrity_failure)
    with api_cli(policy.archive_config) as remote:
        result = remote.invoke(["sync"])
        assert result.exit_code == 40, result.output
        envelope = json.loads(result.stdout)
        assert {row["status"] for row in envelope["data"]["repositories"]} == {"failed"}
        codes = {problem["code"] for problem in envelope["errors"]}
        assert any(code.startswith("HFHUB") for code in codes)
        assert "HFVER007" in codes
        report = json.loads((layout.root / envelope["data"]["report"]).read_text())
        assert report["run_id"] == envelope["run_id"]
        assert report["exit_code"] == 40
        assert set(report["errors"]) == codes
        (receipt,) = remote.application.state.operations.list()
        assert (
            remote.application.state.operations.result(receipt.operation_id).to_payload()
            == envelope
        )


def test_cli_module_and_operational_help_do_not_import_mutation_backends():
    source = """
import sys
from typer.testing import CliRunner
from hfcache.cli import app
result = CliRunner().invoke(app, ["sync", "--help"])
assert result.exit_code == 0, result.output
for name in ("hfcache.services.commands", "hfcache.archive", "hfcache.storage",
             "hfcache.hub", "huggingface_hub", "hfcache.verification_executor"):
    assert name not in sys.modules, name
"""
    subprocess.run([sys.executable, "-c", source], capture_output=True, text=True, check=True)


@pytest.mark.parametrize(
    "arguments",
    [
        ["status"],
        ["version"],
        ["config", "validate", "--local"],
        ["verify", "--estimate"],
        ["operations", "show", "a" * 32],
    ],
)
@pytest.mark.parametrize(
    "flags", [["--detach"], ["--idempotency-key", "key"], ["--wait-timeout", "5"]]
)
def test_job_flags_refuse_on_non_submitting_commands_before_access(tmp_path, arguments, flags):
    result = CliRunner().invoke(
        cli.app, ["--json", "--client-config", str(tmp_path / "missing"), *flags, *arguments]
    )
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG002"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf", "86401"])
def test_invalid_observation_deadline_refuses_before_client_settings(tmp_path, timeout):
    result = CliRunner().invoke(
        cli.app,
        ["--json", "--client-config", str(tmp_path / "missing"), "--wait-timeout", timeout, "sync"],
    )
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG002"


def test_initialization_gate_remains_legible_and_never_submits(configured):
    policy, layout, _, _ = configured
    with api_cli(policy.archive_config) as remote:
        result = remote.invoke(["archive", "init", "--archive-root", str(layout.root), "--confirm"])
        assert result.exit_code == 10
        payload = json.loads(result.stdout)
        assert "maintenance" in payload["errors"][0]["message"].lower()
        assert remote.application.state.operations.list() == ()


@pytest.mark.parametrize(
    "arguments",
    [
        ["sync"],
        ["verify", "--full"],
        ["doctor"],
        ["prune", "--apply"],
        ["purge", "--apply", "--all-unmanaged"],
        ["recover", "--apply"],
        ["quarantine", "--apply", "a" * 32],
        ["repair", f"{MODEL.selector}@{SHA_A}"],
    ],
)
def test_unavailable_writer_never_falls_back_to_local_execution(tmp_path, monkeypatch, arguments):
    def forbidden(*args, **kwargs):
        pytest.fail("Unavailable API attempted local archive policy access")

    monkeypatch.setattr(cli, "load_config", forbidden)
    token = tmp_path / "token"
    token.write_text("writer-" + "T" * 40)
    token.chmod(0o600)
    settings = tmp_path / "client.toml"
    settings.write_text("schema_version=1\nread_retries=0\n")
    before = sorted(path.name for path in tmp_path.iterdir())
    result = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--client-config",
            str(settings),
            "--api-token-file",
            str(token),
            "--api-socket",
            str(tmp_path / "absent.sock"),
            *arguments,
        ],
    )
    assert result.exit_code == 20, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI019"
    assert sorted(path.name for path in tmp_path.iterdir()) == before
