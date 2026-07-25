"""`doctor`, `plan`, and `status` — the read-only command surface.

What is asserted here is the *command*: the envelope it emits, the order it
emits checks in, the exit code it reports, and that `plan` and `status` still
answer when there is no archive at all. The checks themselves are
`tests/unit/test_preflight.py`'s, and the primitives beneath them are
`tests/unit/test_storage.py`'s.

`doctor` needs a mount to report on, so the archive here is a temporary
directory plus a mountinfo file that describes it as NFSv4. That is the same
substitution `test_storage.py` makes, moved one level up: it is what lets the
whole command be exercised, including the probe that writes, without mounting
anything.
"""

import fcntl
import json
import os
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from hfcache.archive import initialize_archive
from hfcache.cli import UNPROVABLE_READ_ONLY, app
from hfcache.errors import ExitCode
from hfcache.identity import new_run_id, new_transaction_id
from hfcache.paths import ArchiveLayout
from hfcache.transactions import open_transaction

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"

ABSENT_ROOT = "/nonexistent/archive/root"

REPOSITORIES = """
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


def config_for(archive_root: str, *, reserve_gib: int = 0, reserve_percent: int = 0) -> str:
    # The reserve defaults to nothing here, not to the schema's 100 GiB / 10%:
    # the archive under test is a directory on whatever filesystem `/tmp` is, so
    # the real defaults would make `free_space` pass or fail according to how
    # full this host happens to be. The capacity tests set it explicitly.
    return f"""
schema_version = 1

[storage]
archive_root = "{archive_root}"
archive_id = "{ARCHIVE_ID}"
minimum_free_space_gib = {reserve_gib}
minimum_free_space_percent = {reserve_percent}

[sync]
# Zero, so a test that holds the lock observes the refusal instead of waiting
# out the hour a scheduled sync is configured for.
lock_wait_seconds = 0
{REPOSITORIES}"""


CONFIG = config_for(ABSENT_ROOT)

# `docs/cli.md` §2 rows 2-8, which are what `STO-001` and `STO-002` implement.
MOUNT_CHECKS = ("archive_root", "mount_point", "filesystem_type", "mount_writable")
STORAGE_CHECKS = (
    *MOUNT_CHECKS,
    "sentinel",
    "directory_writability",
    "staging_filesystem",
    "hardlink_capability",
    "atomic_directory_rename",
    "reference_replacement",
    "free_space",
)

# Rows 9-11: capabilities `--read-only` reports as unproven, whose own checks
# arrive with `STO-007` and `STO-009`.
UNIMPLEMENTED_CAPABILITIES = tuple(
    name for name in UNPROVABLE_READ_ONLY if name not in STORAGE_CHECKS
)


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(CONFIG, encoding="utf-8")
    return path


@pytest.fixture
def mounted_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A temporary directory the application sees as the read/write NFSv4 archive."""
    root = tmp_path / "archive"
    root.mkdir(mode=0o750)
    real = os.path.realpath(root)
    table = tmp_path / "mountinfo"
    table.write_text(
        f"457 47 0:68 / {real} rw,relatime shared:488 - nfs4 nas:/mnt/tank/hf rw,vers=4.2\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", table)
    return root


@pytest.fixture
def mounted_config(tmp_path: Path, mounted_root: Path) -> Path:
    """Configuration for a mounted but *uninitialized* archive."""
    path = tmp_path / "mounted.toml"
    path.write_text(config_for(str(mounted_root)), encoding="utf-8")
    return path


@pytest.fixture
def initialized_config(mounted_config: Path, mounted_root: Path) -> Path:
    """Configuration for an archive that has been initialized on that mount."""
    initialize_archive(ArchiveLayout(root=mounted_root), archive_id=ARCHIVE_ID)
    return mounted_config


def invoke(config_file: Path, *arguments: str):
    return runner.invoke(app, ["--json", "--config", str(config_file), *arguments])


def data_of(result) -> dict:
    return json.loads(result.output)["data"]


def checks_of(result) -> dict[str, dict]:
    return {check["name"]: check for check in data_of(result)["checks"]}


# --------------------------------------------------------------------------- #
# doctor
# --------------------------------------------------------------------------- #


def test_doctor_reports_checks_in_the_normative_order(initialized_config: Path):
    result = invoke(initialized_config, "doctor")

    checks = data_of(result)["checks"]
    assert [check["name"] for check in checks] == [
        "configuration",
        *STORAGE_CHECKS,
        "credential",
        "hub_endpoint",
    ]
    assert {check["outcome"] for check in checks} == {"pass"}
    assert all(set(check) == {"detail", "name", "outcome"} for check in checks)


def test_doctor_exits_zero_when_every_check_that_ran_passed(initialized_config: Path):
    assert invoke(initialized_config, "doctor").exit_code == ExitCode.SUCCESS


def test_doctor_exits_twenty_when_any_check_failed(config_file: Path):
    # `storage.archive_root` names a path that does not exist.
    result = invoke(config_file, "doctor")

    assert result.exit_code == ExitCode.SAFETY
    envelope = json.loads(result.output)
    assert envelope["outcome"] == "failed"
    assert [error["code"] for error in envelope["errors"]] == ["HFMNT001"]


def test_a_failing_check_still_reports_every_other_check(config_file: Path):
    # The output is a record of what was proven, not of where the command
    # stopped, so a failure does not truncate the report.
    checks = checks_of(invoke(config_file, "doctor"))

    assert checks["archive_root"]["outcome"] == "fail"
    assert checks["configuration"]["outcome"] == "pass"
    assert checks["hub_endpoint"]["outcome"] == "pass"


def test_checks_that_could_not_be_reached_are_skipped_rather_than_passed(config_file: Path):
    # Nothing can be said about the filesystem type of a path that is not there,
    # and "pass" would be the one answer that is wrong.
    checks = checks_of(invoke(config_file, "doctor"))

    for name in MOUNT_CHECKS[1:]:
        assert checks[name]["outcome"] == "skipped", name


def test_checks_needing_an_initialized_archive_report_that_as_the_reason(mounted_config: Path):
    # `docs/cli.md` §2: against a target with no initialized archive these report
    # `skipped`, which is operator state rather than development state.
    result = invoke(mounted_config, "doctor")
    checks = checks_of(result)

    assert result.exit_code == ExitCode.SUCCESS, "an uninitialized archive is not a failure"
    for name in STORAGE_CHECKS[len(MOUNT_CHECKS) :]:
        if name == "free_space":
            continue
        assert checks[name]["outcome"] == "skipped"
        assert "not initialized" in checks[name]["detail"]
    for name in (*MOUNT_CHECKS, "free_space"):
        assert checks[name]["outcome"] == "pass", name


def test_the_writability_probe_leaves_nothing_behind(initialized_config: Path, mounted_root: Path):
    # `docs/cli.md` §2: every probe artifact is removed before the command
    # returns. A leftover would be refused as unknown content by the next
    # inspection.
    assert invoke(initialized_config, "doctor").exit_code == ExitCode.SUCCESS

    assert list((mounted_root / ".store" / "health").iterdir()) == []


def test_doctor_fails_when_free_space_is_below_the_reserve(tmp_path: Path, mounted_root: Path):
    # A reserve of the whole filesystem cannot be met by definition, which is the
    # portable way to provoke this without filling a disk.
    path = tmp_path / "reserved.toml"
    path.write_text(config_for(str(mounted_root), reserve_percent=100), encoding="utf-8")

    result = invoke(path, "doctor")

    assert result.exit_code == ExitCode.SAFETY
    assert [error["code"] for error in json.loads(result.output)["errors"]] == ["HFMNT011"]


def test_doctor_warns_without_failing_when_free_space_approaches_the_reserve(
    initialized_config: Path, monkeypatch: pytest.MonkeyPatch
):
    # `HFWRN005` never changes a `0` exit on its own (`docs/cli.md` §5.6). The
    # filesystem is fabricated because a temporary directory's real headroom is
    # whatever this host happens to have.
    def measured(_path):
        block = 4096
        total, available = 100 * (1024**3), 21 * (1024**3)
        return os.statvfs_result(
            (block, block, total // block, available // block, available // block, 0, 0, 0, 0, 255)
        )

    monkeypatch.setattr("hfcache.storage.os.statvfs", measured)
    path = initialized_config
    path.write_text(config_for(str(path.parent / "archive"), reserve_percent=20), encoding="utf-8")

    result = invoke(path, "doctor")
    envelope = json.loads(result.output)

    assert result.exit_code == ExitCode.SUCCESS
    assert envelope["outcome"] == "success_with_warnings"
    assert [warning["code"] for warning in envelope["warnings"]] == ["HFWRN005"]
    assert checks_of(result)["free_space"]["outcome"] == "pass"


def test_read_only_says_what_it_cannot_prove(initialized_config: Path):
    # `docs/cli.md` §2: these are reported as unproven rather than passed. A
    # capability is only demonstrated by exercising it, and a mount that must not
    # be touched is one where it is unknown.
    checks = checks_of(invoke(initialized_config, "doctor", "--read-only"))

    for name in UNPROVABLE_READ_ONLY:
        assert checks[name]["outcome"] == "skipped"
        assert "read-only" in checks[name]["detail"]


def test_read_only_writes_nothing_even_where_it_could(initialized_config: Path, mounted_root: Path):
    result = invoke(initialized_config, "doctor", "--read-only")

    assert checks_of(result)["directory_writability"]["outcome"] == "skipped"
    assert list((mounted_root / ".store" / "health").iterdir()) == []


def test_read_only_still_proves_everything_that_only_reads(initialized_config: Path):
    checks = checks_of(invoke(initialized_config, "doctor", "--read-only"))

    for name in (*MOUNT_CHECKS, "staging_filesystem"):
        assert checks[name]["outcome"] == "pass", name


def test_read_only_never_reports_a_capability_as_passing(config_file: Path):
    checks = data_of(invoke(config_file, "doctor", "--read-only"))["checks"]

    passing = {check["name"] for check in checks if check["outcome"] == "pass"}
    assert not passing & set(UNPROVABLE_READ_ONLY)


def test_every_documented_capability_is_now_probed(initialized_config: Path):
    # `STO-007` landed the last three, so nothing in the table is absent for
    # want of an implementation any more except the Hub checks.
    names = {check["name"] for check in data_of(invoke(initialized_config, "doctor"))["checks"]}

    assert UNIMPLEMENTED_CAPABILITIES == ()
    assert set(UNPROVABLE_READ_ONLY) <= names


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

    assert archive == {
        "archive_id": ARCHIVE_ID,
        "reachable": False,
        "root": "/nonexistent/archive/root",
    }


def test_status_reports_health_when_the_archive_can_be_measured(initialized_config: Path):
    archive = data_of(invoke(initialized_config, "status"))["archive"]

    assert archive["reachable"]
    assert archive["available_bytes"] > 0
    assert archive["unfinished_transactions"] == 0
    assert archive["deferred_cleanup"] == 0
    assert archive["unknown_entries"] == []


def test_status_surfaces_what_the_transaction_areas_hold(
    initialized_config: Path, mounted_root: Path
):
    # A crashed run leaves staging behind; `status` is where an operator sees it.
    (mounted_root / ".store" / "staging" / ("a" * 32)).mkdir()
    (mounted_root / ".store" / "trash" / ("b" * 32)).mkdir()

    result = invoke(initialized_config, "status")
    archive = data_of(result)["archive"]

    assert archive["unfinished_transactions"] == 1
    assert archive["deferred_cleanup"] == 1
    assert [warning["code"] for warning in json.loads(result.output)["warnings"]] == ["HFWRN002"]
    assert result.exit_code == ExitCode.SUCCESS, "a warning never changes a 0 exit on its own"


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


def test_status_prints_its_warnings_where_a_pipe_will_not_swallow_them(
    initialized_config: Path, mounted_root: Path
):
    # Warnings go to stderr so `hfcache status | ...` stays a clean repository
    # list while an operator watching the terminal still sees them.
    (mounted_root / ".store" / "trash" / ("b" * 32)).mkdir()

    result = runner.invoke(app, ["--config", str(initialized_config), "status"])

    assert result.exit_code == ExitCode.SUCCESS
    assert "HFWRN002" not in result.stdout
    assert "HFWRN002" in result.stderr


def test_status_prints_each_repository_with_its_state(config_file: Path):
    result = runner.invoke(app, ["--config", str(config_file), "status"])

    assert "model:zeta/last-in-file  enabled" in result.output
    assert "model:organization/turned-off  disabled" in result.output


@pytest.mark.parametrize("command", ["plan", "status"])
def test_quiet_suppresses_the_human_summary(config_file: Path, command):
    result = runner.invoke(app, ["--quiet", "--config", str(config_file), command])

    assert result.exit_code == ExitCode.SUCCESS
    assert result.output == ""


def test_quiet_suppresses_the_doctor_table(initialized_config: Path):
    result = runner.invoke(app, ["--quiet", "--config", str(initialized_config), "doctor"])

    assert result.exit_code == ExitCode.SUCCESS
    assert result.output == ""


# --------------------------------------------------------------------------- #
# recover
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("arguments", [(), ("--dry-run", "--apply")])
def test_recover_requires_exactly_one_mode(config_file: Path, arguments):
    # Neither is a safe default: one describes what would happen and the other
    # performs it.
    result = invoke(config_file, "recover", *arguments)

    assert result.exit_code == ExitCode.CONFIGURATION
    assert json.loads(result.output)["errors"][0]["code"] == "HFARG002"


def test_recover_dry_run_describes_a_clean_archive(initialized_config: Path):
    result = invoke(initialized_config, "recover", "--dry-run")

    assert result.exit_code == ExitCode.SUCCESS
    assert data_of(result) == {"actionable": 0, "blocked": 0, "plan": []}


def test_recover_dry_run_mutates_nothing(initialized_config: Path, mounted_root: Path):
    before = sorted(path.name for path in (mounted_root / ".store" / "transactions").iterdir())

    invoke(initialized_config, "recover", "--dry-run")

    after = sorted(path.name for path in (mounted_root / ".store" / "transactions").iterdir())
    assert after == before


def test_recover_apply_takes_the_lock_and_runs_the_preflight(
    initialized_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # `--apply` mutates, so it is a mutating command in every sense.
    monkeypatch.setattr("hfcache.locking.LOCK_DIRECTORY", tmp_path / "run")

    result = invoke(initialized_config, "recover", "--apply")

    assert result.exit_code == ExitCode.SUCCESS
    assert data_of(result)["applied"] == 0


def test_recover_apply_refuses_when_the_lock_is_held(
    initialized_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    run_directory = tmp_path / "run"
    run_directory.mkdir()
    monkeypatch.setattr("hfcache.locking.LOCK_DIRECTORY", run_directory)
    descriptor = os.open(run_directory / "hfcache.lock", os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        result = invoke(initialized_config, "recover", "--apply")
    finally:
        os.close(descriptor)

    assert result.exit_code == ExitCode.SAFETY
    assert json.loads(result.output)["errors"][0]["code"] == "HFMNT010"


def test_recover_reports_a_state_it_may_not_resolve(
    initialized_config: Path, mounted_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("hfcache.locking.LOCK_DIRECTORY", tmp_path / "run")
    layout = ArchiveLayout(root=mounted_root)
    open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint="a" * 64,
    ).needs_operator("HFTXN004", "two equally valid resolutions")

    result = invoke(initialized_config, "recover", "--dry-run")

    assert result.exit_code == ExitCode.SAFETY
    assert json.loads(result.output)["errors"][0]["code"] == "HFTXN004"
    assert data_of(result)["blocked"] == 1, "the plan is reported alongside the refusal"


def test_recover_apply_performs_nothing_when_the_plan_is_blocked(
    initialized_config: Path, mounted_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # A partially recovered archive with an unresolved transaction still in it is
    # harder to reason about than the state it started in.
    monkeypatch.setattr("hfcache.locking.LOCK_DIRECTORY", tmp_path / "run")
    layout = ArchiveLayout(root=mounted_root)
    open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint="a" * 64,
    ).needs_operator("HFTXN004", "two equally valid resolutions")

    result = invoke(initialized_config, "recover", "--apply")

    assert result.exit_code == ExitCode.SAFETY
    assert "applied" not in data_of(result)
    assert list((mounted_root / "runs").iterdir()) == [], "no report was written"


def test_recover_prints_a_readable_summary_without_json(initialized_config: Path):
    result = runner.invoke(app, ["--config", str(initialized_config), "recover", "--dry-run"])

    assert result.exit_code == ExitCode.SUCCESS
    assert "actionable" in result.output
