"""`doctor`, `plan`, and `status` — the portions that need no archive or Hub.

Phase 2 gives these commands their invocation surface: configuration loading,
credential resolution, selector resolution, and the documented envelope shapes.
The storage probes belong to `STO-009` and revision resolution to `HUB-003`; what
is asserted here is everything that is decidable before either exists, including
that none of it touches the archive root.
"""

import json
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from hfcache.cli import UNPROVABLE_READ_ONLY, app
from hfcache.errors import ExitCode

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"

CONFIG = f"""
schema_version = 1

[storage]
archive_root = "/nonexistent/archive/root"
archive_id = "{ARCHIVE_ID}"

[[repositories]]
id = "zeta/last-in-file"
type = "model"
revision = "v2.0"

[[repositories]]
id = "alpha/first-in-file"
type = "dataset"

[[repositories]]
id = "organization/turned-off"
type = "model"
enabled = false
"""


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(CONFIG, encoding="utf-8")
    return path


def invoke(config_file: Path, *arguments: str):
    return runner.invoke(app, ["--json", "--config", str(config_file), *arguments])


def data_of(result) -> dict:
    return json.loads(result.output)["data"]


# --------------------------------------------------------------------------- #
# doctor
# --------------------------------------------------------------------------- #


def test_doctor_reports_checks_in_execution_order(config_file: Path):
    result = invoke(config_file, "doctor")

    checks = data_of(result)["checks"]
    assert [check["name"] for check in checks] == [
        "configuration",
        "credential",
        "hub_endpoint",
    ]
    assert {check["outcome"] for check in checks} == {"pass"}
    assert all(set(check) == {"detail", "name", "outcome"} for check in checks)


def test_doctor_exits_zero_when_everything_it_can_check_passes(config_file: Path):
    assert invoke(config_file, "doctor").exit_code == ExitCode.SUCCESS


def test_read_only_says_what_it_cannot_prove(config_file: Path):
    # `docs/cli.md` §2: these are reported as unproven rather than passed. A
    # capability is only demonstrated by exercising it, and a mount that must not
    # be touched is one where it is unknown.
    checks = {
        check["name"]: check
        for check in data_of(invoke(config_file, "doctor", "--read-only"))["checks"]
    }

    for name in UNPROVABLE_READ_ONLY:
        assert checks[name]["outcome"] == "skipped"
        assert "read-only" in checks[name]["detail"]


def test_read_only_never_reports_a_capability_as_passing(config_file: Path):
    checks = data_of(invoke(config_file, "doctor", "--read-only"))["checks"]

    passing = {check["name"] for check in checks if check["outcome"] == "pass"}
    assert not passing & set(UNPROVABLE_READ_ONLY)


def test_doctor_does_not_report_capabilities_it_did_not_probe(config_file: Path):
    # Without --read-only the storage probes are absent rather than fabricated;
    # they arrive with STO-009.
    names = {check["name"] for check in data_of(invoke(config_file, "doctor"))["checks"]}

    assert not names & set(UNPROVABLE_READ_ONLY)


def test_doctor_reports_the_credential_source_never_the_value(config_file: Path, tmp_path: Path):
    token = tmp_path / "token"
    token.write_text("hf_doctorMustNotEchoThis\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--json", "--config", str(config_file), "--token-file", str(token), "doctor"],
    )

    assert "hf_doctorMustNotEchoThis" not in result.output
    credential = next(check for check in data_of(result)["checks"] if check["name"] == "credential")
    assert "token-file" in credential["detail"]


def test_doctor_fails_on_bad_configuration_before_probing(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(CONFIG.replace("schema_version = 1", "schema_version = 99"), encoding="utf-8")

    result = invoke(path, "doctor")

    envelope = json.loads(result.output)
    assert result.exit_code == ExitCode.CONFIGURATION
    assert envelope["data"] == {}, "no check ran, so none is reported"
    assert envelope["errors"][0]["code"] == "HFCFG004"


def test_doctor_prints_a_readable_table_without_json(config_file: Path):
    result = runner.invoke(app, ["--config", str(config_file), "doctor"])

    assert "pass" in result.output
    assert "configuration" in result.output


# --------------------------------------------------------------------------- #
# plan
# --------------------------------------------------------------------------- #


def test_plan_covers_only_enabled_repositories(config_file: Path):
    entries = data_of(invoke(config_file, "plan"))["repositories"]

    assert [entry["repository_id"] for entry in entries] == [
        "zeta/last-in-file",
        "alpha/first-in-file",
    ]
    assert all(entry["enabled"] for entry in entries)


def test_plan_reports_the_configured_reference_verbatim(config_file: Path):
    entries = data_of(invoke(config_file, "plan"))["repositories"]

    assert entries[0]["requested_revision"] == "v2.0"
    assert entries[1]["requested_revision"] == "main"


def test_plan_keeps_configuration_order_not_selector_order(config_file: Path):
    # Two invocations naming the same set must behave identically, so the order
    # is the file's rather than the command line's.
    forwards = invoke(config_file, "plan", "model:zeta/last-in-file", "dataset:alpha/first-in-file")
    backwards = invoke(
        config_file, "plan", "dataset:alpha/first-in-file", "model:zeta/last-in-file"
    )

    assert data_of(forwards) == data_of(backwards)


def test_plan_takes_no_lock_and_reads_no_archive(config_file: Path):
    # `storage.archive_root` is a path that does not exist. `plan` mutates
    # nothing and takes no lock (`docs/cli.md` §2), so this still succeeds.
    assert invoke(config_file, "plan").exit_code == ExitCode.SUCCESS


# --------------------------------------------------------------------------- #
# status
# --------------------------------------------------------------------------- #


def test_status_reports_every_configured_repository_including_disabled(config_file: Path):
    entries = data_of(invoke(config_file, "status"))["repositories"]

    assert len(entries) == 3
    assert [entry["enabled"] for entry in entries] == [True, True, False]
    assert all(entry["managed"] for entry in entries)


def test_status_marks_upstream_unknown_rather_than_contacting_the_hub(config_file: Path):
    # `docs/cli.md` §2: status never fails merely because the Hub is
    # unreachable. It reports local truth and marks upstream `unknown`.
    entries = data_of(invoke(config_file, "status"))["repositories"]

    assert {entry["upstream_state"] for entry in entries} == {"unknown"}


def test_status_reports_the_archive_it_is_configured_for(config_file: Path):
    archive = data_of(invoke(config_file, "status"))["archive"]

    assert archive == {"archive_id": ARCHIVE_ID, "root": "/nonexistent/archive/root"}


def test_status_answers_when_the_archive_is_absent(config_file: Path):
    assert invoke(config_file, "status").exit_code == ExitCode.SUCCESS


def test_status_needs_no_credential(config_file: Path, tmp_path: Path):
    # status resolves no token: it makes no Hub call, so an unusable credential
    # must not stop an operator from reading local state.
    empty = tmp_path / "token"
    empty.write_text("", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--json", "--config", str(config_file), "--token-file", str(empty), "status"],
    )

    assert result.exit_code == ExitCode.SUCCESS


# --------------------------------------------------------------------------- #
# Selectors (`docs/cli.md` §1.1)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("command", ["plan", "status"])
def test_a_selector_restricts_the_command(config_file: Path, command):
    entries = data_of(invoke(config_file, command, "dataset:alpha/first-in-file"))["repositories"]

    assert [entry["repository_id"] for entry in entries] == ["alpha/first-in-file"]


@pytest.mark.parametrize("command", ["plan", "status"])
def test_a_malformed_selector_is_hfarg001(config_file: Path, command):
    result = invoke(config_file, command, "not-a-selector")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert json.loads(result.output)["errors"][0]["code"] == "HFARG001"


@pytest.mark.parametrize("command", ["plan", "status"])
def test_an_abbreviated_sha_in_a_selector_is_hfarg001(config_file: Path, command):
    result = invoke(config_file, command, "model:zeta/last-in-file@0123456")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert json.loads(result.output)["errors"][0]["code"] == "HFARG001"


@pytest.mark.parametrize("command", ["plan", "status"])
def test_an_unconfigured_selector_is_hfarg004(config_file: Path, command):
    result = invoke(config_file, command, "model:absent/repository")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert json.loads(result.output)["errors"][0]["code"] == "HFARG004"


def test_every_unconfigured_selector_is_reported_at_once(config_file: Path):
    result = invoke(config_file, "plan", "model:absent/one", "model:absent/two")

    errors = json.loads(result.output)["errors"]
    assert [error["code"] for error in errors] == ["HFARG004", "HFARG004"]
    assert {error["context"]["location"] for error in errors} == {
        "model:absent/one",
        "model:absent/two",
    }


def test_the_type_is_part_of_the_selector_match(config_file: Path):
    # `alpha/first-in-file` is a dataset. Naming it as a model selects nothing.
    result = invoke(config_file, "status", "model:alpha/first-in-file")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert json.loads(result.output)["errors"][0]["code"] == "HFARG004"


def test_a_disabled_repository_can_still_be_selected_by_status(config_file: Path):
    entries = data_of(invoke(config_file, "status", "model:organization/turned-off"))[
        "repositories"
    ]

    assert [entry["enabled"] for entry in entries] == [False]


def test_selecting_only_a_disabled_repository_gives_plan_nothing_to_do(config_file: Path):
    result = invoke(config_file, "plan", "model:organization/turned-off")

    assert result.exit_code == ExitCode.SUCCESS
    assert data_of(result)["repositories"] == []


# --------------------------------------------------------------------------- #
# Human-readable output
# --------------------------------------------------------------------------- #


def test_plan_prints_selectors_an_operator_can_paste_back(config_file: Path):
    result = runner.invoke(app, ["--config", str(config_file), "plan"])

    assert result.exit_code == ExitCode.SUCCESS
    assert "model:zeta/last-in-file@v2.0" in result.output
    assert "dataset:alpha/first-in-file@main" in result.output
    assert "organization/turned-off" not in result.output


def test_status_prints_each_repository_with_its_state(config_file: Path):
    result = runner.invoke(app, ["--config", str(config_file), "status"])

    assert "model:zeta/last-in-file  enabled" in result.output
    assert "model:organization/turned-off  disabled" in result.output


@pytest.mark.parametrize("command", ["doctor", "plan", "status"])
def test_quiet_suppresses_the_human_summary(config_file: Path, command):
    result = runner.invoke(app, ["--quiet", "--config", str(config_file), command])

    assert result.exit_code == ExitCode.SUCCESS
    assert result.output == ""
