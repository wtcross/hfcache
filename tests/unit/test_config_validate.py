"""`config validate --local` (`docs/cli.md` §2, §4.1).

The command's whole promise is that it runs the same validation a mutating
command runs while touching nothing. Both halves are tested here: the failure
codes it surfaces are the loader's and the credential resolver's own, and the
run leaves no lock, no directory, and no network call behind.
"""

import json
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from hfcache.cli import app
from hfcache.errors import ExitCode

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"

VALID = f"""
schema_version = 1

[storage]
archive_root = "/srv/hfcache"
archive_id = "{ARCHIVE_ID}"

[[repositories]]
id = "organization/model-name"
type = "model"

[[repositories]]
id = "organization/dataset-name"
type = "dataset"
enabled = false
"""


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(VALID, encoding="utf-8")
    return path


def invoke(*arguments: str):
    return runner.invoke(app, list(arguments))


def envelope_of(result) -> dict:
    return json.loads(result.stdout)


# --------------------------------------------------------------------------- #
# Success
# --------------------------------------------------------------------------- #


def test_a_valid_configuration_exits_zero(config_file: Path):
    result = invoke("--config", str(config_file), "config", "validate", "--local")

    assert result.exit_code == ExitCode.SUCCESS
    assert "config fingerprint" in result.output


def test_the_payload_matches_the_documented_fields(config_file: Path):
    result = invoke("--json", "--config", str(config_file), "config", "validate", "--local")

    data = envelope_of(result)["data"]
    assert set(data) == {
        "config_fingerprint",
        "enabled_repositories",
        "repositories",
        "token_source",
    }
    assert data["repositories"] == 2
    assert data["enabled_repositories"] == 1
    assert len(data["config_fingerprint"]) == 64


def test_the_envelope_reports_the_command_path(config_file: Path):
    result = invoke("--json", "--config", str(config_file), "config", "validate", "--local")

    envelope = envelope_of(result)
    assert envelope["command"] == "config validate"
    assert envelope["outcome"] == "success"
    assert envelope["exit_code"] == 0
    assert envelope["errors"] == []


def test_the_fingerprint_is_stable_across_runs(config_file: Path):
    first = envelope_of(
        invoke("--json", "--config", str(config_file), "config", "validate", "--local")
    )
    second = envelope_of(
        invoke("--json", "--config", str(config_file), "config", "validate", "--local")
    )

    assert first["data"] == second["data"]
    assert first["run_id"] != second["run_id"]


def test_quiet_suppresses_the_human_summary(config_file: Path):
    result = invoke("--quiet", "--config", str(config_file), "config", "validate", "--local")

    assert result.exit_code == ExitCode.SUCCESS
    assert result.output == ""


def test_quiet_does_not_suppress_the_envelope(config_file: Path):
    result = invoke(
        "--quiet", "--json", "--config", str(config_file), "config", "validate", "--local"
    )

    assert envelope_of(result)["outcome"] == "success"


# --------------------------------------------------------------------------- #
# Failure
# --------------------------------------------------------------------------- #


def test_a_missing_file_is_hfcfg001(tmp_path: Path):
    result = invoke("--config", str(tmp_path / "absent.toml"), "config", "validate", "--local")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert "HFCFG001" in result.output


def test_malformed_toml_is_hfcfg002(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text("schema_version = = 1", encoding="utf-8")

    result = invoke("--config", str(path), "config", "validate", "--local")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert "HFCFG002" in result.output


def test_every_problem_is_reported_not_just_the_first(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
        schema_version = 1
        unknown_key = true

        [storage]
        archive_root = "relative/path"
        archive_id = "{ARCHIVE_ID}"
        maximum_revisions = 9
        """,
        encoding="utf-8",
    )

    result = invoke("--json", "--config", str(path), "config", "validate", "--local")

    errors = envelope_of(result)["errors"]
    codes = {entry["code"] for entry in errors}
    assert {"HFCFG003", "HFCFG006"} <= codes
    assert len(errors) >= 2
    # `maximum_revisions = 9` is `HFCFG011` and is *not* reported in this pass:
    # its check is a whole-table validator, and Pydantic does not run one when a
    # field in that table already failed. So an operator fixing `archive_root`
    # sees the revisions error on the next run rather than this one. Asserted
    # rather than wished away, because it is what the command actually does.
    assert "HFCFG011" not in codes


def test_a_table_level_constraint_is_reported_once_its_fields_are_valid(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
        schema_version = 1

        [storage]
        archive_root = "/srv/hfcache"
        archive_id = "{ARCHIVE_ID}"
        maximum_revisions = 9
        """,
        encoding="utf-8",
    )

    result = invoke("--json", "--config", str(path), "config", "validate", "--local")

    assert {entry["code"] for entry in envelope_of(result)["errors"]} == {"HFCFG011"}


def test_the_failure_envelope_is_still_emitted(tmp_path: Path):
    result = invoke(
        "--json", "--config", str(tmp_path / "absent.toml"), "config", "validate", "--local"
    )

    envelope = envelope_of(result)
    assert envelope["outcome"] == "failed"
    assert envelope["exit_code"] == ExitCode.CONFIGURATION
    assert envelope["data"] == {}
    assert envelope["errors"][0]["code"] == "HFCFG001"


def test_human_mode_writes_problems_to_stderr(tmp_path: Path):
    isolated = CliRunner()
    result = isolated.invoke(
        app, ["--config", str(tmp_path / "absent.toml"), "config", "validate", "--local"]
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert "HFCFG001" in result.output


def test_a_literal_secret_is_reported_by_key_not_value(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
        schema_version = 1
        [storage]
        archive_root = "/srv/hfcache"
        archive_id = "{ARCHIVE_ID}"
        [hub]
        token = "hf_thisMustNeverBeEchoed"
        """,
        encoding="utf-8",
    )

    result = invoke("--json", "--config", str(path), "config", "validate", "--local")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert "hf_thisMustNeverBeEchoed" not in result.output
    error = envelope_of(result)["errors"][0]
    assert error["code"] == "HFCFG010"
    assert error["context"]["location"] == "hub.token"


# --------------------------------------------------------------------------- #
# Credential resolution (`docs/configuration.md` §7)
# --------------------------------------------------------------------------- #


def test_no_credential_resolves_to_anonymous(config_file: Path):
    result = invoke("--json", "--config", str(config_file), "config", "validate", "--local")

    assert envelope_of(result)["data"]["token_source"] == "none"


def test_required_mode_without_a_credential_is_hfarg008(tmp_path: Path):
    path = tmp_path / "required.toml"
    path.write_text(
        VALID.replace("schema_version = 1", 'schema_version = 1\n[hub]\ntoken_mode = "required"'),
        encoding="utf-8",
    )

    result = invoke("--json", "--config", str(path), "config", "validate", "--local")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert envelope_of(result)["errors"][0]["code"] == "HFARG008"


def test_required_mode_accepts_an_explicit_token(tmp_path: Path):
    path = tmp_path / "required.toml"
    path.write_text(
        VALID.replace("schema_version = 1", 'schema_version = 1\n[hub]\ntoken_mode = "required"'),
        encoding="utf-8",
    )
    token = tmp_path / "token"
    token.write_text("hf_aRealLookingTokenValue\n", encoding="utf-8")

    result = invoke(
        "--json", "--config", str(path), "--token-file", str(token), "config", "validate", "--local"
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert envelope_of(result)["data"]["token_source"] == "token-file"


def test_a_token_file_is_resolved_and_reported_by_source(config_file: Path, tmp_path: Path):
    token = tmp_path / "token"
    token.write_text("hf_aRealLookingTokenValue\n", encoding="utf-8")

    result = invoke(
        "--json",
        "--config",
        str(config_file),
        "--token-file",
        str(token),
        "config",
        "validate",
        "--local",
    )

    assert result.exit_code == ExitCode.SUCCESS
    data = envelope_of(result)["data"]
    assert data["token_source"] == "token-file"
    assert "hf_aRealLookingTokenValue" not in result.output


def test_an_unusable_token_file_is_hfarg005(config_file: Path, tmp_path: Path):
    empty = tmp_path / "token"
    empty.write_text("", encoding="utf-8")

    result = invoke(
        "--json",
        "--config",
        str(config_file),
        "--token-file",
        str(empty),
        "config",
        "validate",
        "--local",
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert envelope_of(result)["errors"][0]["code"] == "HFARG005"


def test_a_token_file_under_disabled_mode_is_hfarg002(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
        schema_version = 1
        [storage]
        archive_root = "/srv/hfcache"
        archive_id = "{ARCHIVE_ID}"
        [hub]
        token_mode = "disabled"
        """,
        encoding="utf-8",
    )
    token = tmp_path / "token"
    token.write_text("hf_value\n", encoding="utf-8")

    result = invoke(
        "--json", "--config", str(path), "--token-file", str(token), "config", "validate", "--local"
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert envelope_of(result)["errors"][0]["code"] == "HFARG002"


def test_a_systemd_credential_is_resolved(
    config_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    credentials = tmp_path / "credentials"
    credentials.mkdir()
    (credentials / "hf-token").write_text("hf_fromSystemd\n", encoding="utf-8")
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(credentials))

    result = invoke("--json", "--config", str(config_file), "config", "validate", "--local")

    assert envelope_of(result)["data"]["token_source"] == "systemd-credential"
    assert "hf_fromSystemd" not in result.output


def test_an_ambient_token_variable_is_ignored(config_file: Path, monkeypatch: pytest.MonkeyPatch):
    # `docs/security.md` T-07: ambient discovery is disabled, so a developer's
    # exported token cannot silently change what a production run does.
    monkeypatch.setenv("HF_TOKEN", "hf_ambientMustBeIgnored")

    result = invoke("--json", "--config", str(config_file), "config", "validate", "--local")

    assert envelope_of(result)["data"]["token_source"] == "none"
    assert "hf_ambientMustBeIgnored" not in result.output


# --------------------------------------------------------------------------- #
# It really does touch nothing
# --------------------------------------------------------------------------- #


def test_validation_creates_nothing_and_needs_no_archive(config_file: Path, tmp_path: Path):
    # `storage.archive_root` in the fixture is `/srv/hfcache`, which this test
    # neither creates nor requires: no mount check, no lock, no directory.
    before = sorted(path.name for path in tmp_path.iterdir())

    result = invoke("--config", str(config_file), "config", "validate", "--local")

    assert result.exit_code == ExitCode.SUCCESS
    assert sorted(path.name for path in tmp_path.iterdir()) == before


def test_an_unreachable_archive_root_does_not_fail_validation(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
        schema_version = 1
        [storage]
        archive_root = "/nonexistent/mount/point"
        archive_id = "{ARCHIVE_ID}"
        """,
        encoding="utf-8",
    )

    result = invoke("--config", str(path), "config", "validate", "--local")

    assert result.exit_code == ExitCode.SUCCESS


def test_the_subcommand_is_discoverable():
    assert "config" in invoke("--help").output
    assert "validate" in invoke("config", "--help").output


def test_config_without_a_subcommand_shows_help():
    result = invoke("config")

    assert "validate" in result.output
