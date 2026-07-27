"""The Typer entry point, global options, and the `version` command."""

import json

from typer.testing import CliRunner

from hfcache.cli import DEFAULT_CONFIG_PATH, app
from hfcache.errors import ExitCode

runner = CliRunner()


def test_help_lists_the_global_options():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == ExitCode.SUCCESS
    for option in ("--config", "--json", "--verbose", "--quiet", "--no-color", "--token-file"):
        assert option in result.output


def test_bare_invocation_shows_help_rather_than_failing_silently():
    result = runner.invoke(app, [])
    assert "Usage:" in result.output


def test_version_reports_the_stack():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == ExitCode.SUCCESS
    for field in ("application", "huggingface hub", "python", "transfer backend"):
        assert field in result.output


def test_an_unreadable_configuration_is_exit_ten_and_not_a_usage_error(tmp_path):
    """Decision 57. `ExitCode` reserves `1` and `2` for a malformed command line
    precisely so a scheduler can tell one from an application outcome, and typer's
    Path type checks readability at parse time by default — which turned the
    deployed `0640 root:hfcache` configuration into exit `2` for every identity
    but two, including for commands that never open it."""
    path = tmp_path / "config.toml"
    path.write_text("schema_version = 1\n", encoding="utf-8")
    path.chmod(0o000)

    unreadable = runner.invoke(app, ["--json", "--config", str(path), "status"])
    assert unreadable.exit_code == ExitCode.CONFIGURATION
    assert [error["code"] for error in json.loads(unreadable.stdout)["errors"]] == ["HFCFG001"]

    # And a command that needs no configuration answers regardless.
    assert runner.invoke(app, ["--config", str(path), "version"]).exit_code == ExitCode.SUCCESS


def test_version_json_envelope_matches_the_contract():
    result = runner.invoke(app, ["--json", "version"])
    assert result.exit_code == ExitCode.SUCCESS

    # docs/schemas.md §1: exactly one trailing newline.
    assert result.output.endswith("\n")
    assert not result.output.rstrip("\n").endswith("\n")

    envelope = json.loads(result.stdout)
    assert set(envelope) == {
        "command",
        "completed_at",
        "data",
        "errors",
        "exit_code",
        "outcome",
        "run_id",
        "schema_version",
        "started_at",
        "warnings",
    }
    assert envelope["command"] == "version"
    assert envelope["schema_version"] == 1
    assert envelope["exit_code"] == ExitCode.SUCCESS
    assert envelope["outcome"] == "success"
    assert envelope["errors"] == []
    assert envelope["warnings"] == []
    assert set(envelope["data"]) == {
        "application",
        "huggingface_hub",
        "python",
        "transfer_backend",
    }


def test_version_json_envelope_keys_are_sorted():
    result = runner.invoke(app, ["--json", "version"])
    body = result.output.rstrip("\n")
    parsed = json.loads(body)
    assert body == json.dumps(parsed, sort_keys=True, ensure_ascii=False, separators=(",", ": "))


def test_envelope_timestamps_are_utc_with_microseconds():
    envelope = json.loads(runner.invoke(app, ["--json", "version"]).output)
    for field in ("started_at", "completed_at"):
        value = envelope[field]
        assert value.endswith("Z"), value
        # 2026-07-24T21:31:07.963096Z
        assert len(value) == 27, value
    assert envelope["started_at"] <= envelope["completed_at"]


def test_run_id_is_opaque_and_unique():
    first = json.loads(runner.invoke(app, ["--json", "version"]).output)["run_id"]
    second = json.loads(runner.invoke(app, ["--json", "version"]).output)["run_id"]
    assert len(first) == 32
    assert int(first, 16) >= 0  # 32 lowercase hex characters
    assert first != second


def test_default_config_path_matches_the_systemd_invocation():
    assert str(DEFAULT_CONFIG_PATH) == "/etc/hfcache/config.toml"


def test_exit_codes_avoid_typer_usage_codes():
    # docs/cli.md §3: 1 and 2 are reserved by Typer for usage errors.
    values = {code.value for code in ExitCode}
    assert values == {0, 10, 20, 30, 40, 50}
    assert not values & {1, 2}
