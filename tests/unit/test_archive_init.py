"""`archive init` — the command surface of the one irreversible action.

`storage.py`'s own tests cover what initialization does to a filesystem. What is
asserted here is everything between the operator and that: which invocations are
refused before anything is read, what the envelope says when the command
declines, and that a refusal still reports the target it found rather than only
the reason it stopped.

The mount table is a fixture file with `hfcache.storage.MOUNT_TABLE` pointed at
it, which is what lets a temporary directory stand in for the NFS archive. That
is the only piece of the environment these tests fake; configuration loading,
option checking, and the storage layer are the real ones.
"""

import json
import stat
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from hfcache.cli import app
from hfcache.errors import ExitCode

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
OTHER_ARCHIVE_ID = "11111111-2222-3333-4444-555555555555"


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    root = tmp_path / "archive"
    root.mkdir()
    return root


@pytest.fixture
def mounted(archive_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Present the temporary archive root as an NFSv4 mount."""
    table = tmp_path / "mountinfo"
    table.write_text(
        f"457 47 0:68 / {archive_root.resolve()} rw,nosuid,nodev,relatime shared:488 "
        f"- nfs4 nas.lab.example.com:/mnt/tank/hf rw,vers=4.2\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", table)
    return archive_root


@pytest.fixture
def config_file(tmp_path: Path, archive_root: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
schema_version = 1

[storage]
archive_root = "{archive_root}"
archive_id = "{ARCHIVE_ID}"
""",
        encoding="utf-8",
    )
    return path


def invoke(config_file: Path, *arguments: str):
    return runner.invoke(app, ["--json", "--config", str(config_file), *arguments])


def init(config_file: Path, root: Path, *arguments: str):
    return invoke(config_file, "archive", "init", "--archive-root", str(root), *arguments)


def envelope(result) -> dict:
    return json.loads(result.stdout)


def error_codes(result) -> list[str]:
    return [problem["code"] for problem in envelope(result)["errors"]]


# --------------------------------------------------------------------------- #
# Invocation guards
# --------------------------------------------------------------------------- #


def test_archive_root_is_required(config_file: Path):
    # Typer's own usage error, deliberately code 2, so a scheduler can tell a
    # malformed command line from an application outcome (`docs/cli.md` §3).
    result = invoke(config_file, "archive", "init")

    assert result.exit_code == 2


def test_confirm_and_inspect_together_are_hfarg002(config_file: Path, mounted: Path):
    result = init(config_file, mounted, "--confirm", "--inspect")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert error_codes(result) == ["HFARG002"]


def test_an_archive_root_that_disagrees_with_configuration_is_hfarg002(
    config_file: Path, mounted: Path, tmp_path: Path
):
    # Stating the target twice is the point: initialization does not take the
    # one irreversible decision from a file alone (`docs/cli.md` §2).
    result = init(config_file, tmp_path / "somewhere-else", "--confirm")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert error_codes(result) == ["HFARG002"]
    assert not (tmp_path / "somewhere-else").exists()


def test_an_archive_id_that_disagrees_with_configuration_is_hfarg002(
    config_file: Path, mounted: Path
):
    result = init(config_file, mounted, "--archive-id", OTHER_ARCHIVE_ID, "--confirm")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert error_codes(result) == ["HFARG002"]
    assert list(mounted.iterdir()) == [], "nothing is created when the options disagree"


def test_a_matching_archive_id_is_accepted(config_file: Path, mounted: Path):
    result = init(config_file, mounted, "--archive-id", ARCHIVE_ID, "--confirm")

    assert result.exit_code == ExitCode.SUCCESS
    assert envelope(result)["data"]["archive_id"] == ARCHIVE_ID


def test_bad_configuration_stops_before_the_archive_is_read(
    tmp_path: Path, mounted: Path, config_file: Path
):
    config_file.write_text("schema_version = 99\n", encoding="utf-8")

    result = init(config_file, mounted, "--confirm")

    assert result.exit_code == ExitCode.CONFIGURATION
    assert envelope(result)["data"] == {}
    assert list(mounted.iterdir()) == []


# --------------------------------------------------------------------------- #
# Without --confirm
# --------------------------------------------------------------------------- #


def test_without_confirm_the_command_explains_and_exits_ten(config_file: Path, mounted: Path):
    result = init(config_file, mounted)

    assert result.exit_code == ExitCode.CONFIGURATION
    assert error_codes(result) == ["HFARG003"]


def test_without_confirm_nothing_is_created(config_file: Path, mounted: Path):
    init(config_file, mounted)

    assert list(mounted.iterdir()) == []


def test_a_refusal_still_reports_what_it_found(config_file: Path, mounted: Path):
    # The reason it stopped and the state it would have acted on are both useful,
    # and an operator should not have to run a second command for the second one.
    data = envelope(init(config_file, mounted))["data"]

    assert data["state"] == "uninitialized"
    assert data["initializable"] is True
    assert data["mount"]["filesystem_type"] == "nfs4"


# --------------------------------------------------------------------------- #
# --inspect
# --------------------------------------------------------------------------- #


def test_inspect_describes_a_clean_target_and_exits_zero(config_file: Path, mounted: Path):
    result = init(config_file, mounted, "--inspect")

    assert result.exit_code == ExitCode.SUCCESS
    assert envelope(result)["data"]["state"] == "uninitialized"


def test_inspect_mutates_nothing(config_file: Path, mounted: Path):
    init(config_file, mounted, "--inspect")

    assert list(mounted.iterdir()) == []


def test_inspect_reports_an_adoptable_published(config_file: Path, mounted: Path):
    published = mounted / "published"
    published.mkdir()
    published.chmod(0o2750)

    data = envelope(init(config_file, mounted, "--inspect"))["data"]

    assert data["adopted_published"] is True
    assert data["state"] == "uninitialized"


def test_inspect_exits_zero_for_an_already_initialized_archive(config_file: Path, mounted: Path):
    # Not initializable, but perfectly healthy. Exiting 20 here would make
    # `--inspect` useless as a routine check.
    init(config_file, mounted, "--confirm")

    result = init(config_file, mounted, "--inspect")

    assert result.exit_code == ExitCode.SUCCESS
    data = envelope(result)["data"]
    assert data["state"] == "initialized"
    assert data["initializable"] is False
    assert data["archive_id"] == ARCHIVE_ID


def test_inspect_exits_twenty_when_the_target_is_neither(config_file: Path, mounted: Path):
    (mounted / "somebody-elses-file").write_text("x", encoding="utf-8")

    result = init(config_file, mounted, "--inspect")

    assert result.exit_code == ExitCode.SAFETY
    assert error_codes(result) == ["HFMNT014"]
    assert envelope(result)["data"]["state"] == "unusable"


def test_inspect_reports_a_sentinel_that_disagrees_with_configuration(
    config_file: Path, mounted: Path, tmp_path: Path
):
    init(config_file, mounted, "--confirm")
    config_file.write_text(
        config_file.read_text(encoding="utf-8").replace(ARCHIVE_ID, OTHER_ARCHIVE_ID),
        encoding="utf-8",
    )

    result = init(config_file, mounted, "--inspect")

    assert result.exit_code == ExitCode.SAFETY
    assert error_codes(result) == ["HFMNT007"]


# --------------------------------------------------------------------------- #
# Mount safety
# --------------------------------------------------------------------------- #


def test_an_unmounted_target_is_refused_before_anything_is_created(
    config_file: Path, archive_root: Path
):
    # No `mounted` fixture: the real mount table is read and does not name a
    # temporary directory. This is the failure mode the whole check exists for —
    # a missing NAS must not cause the archive to be written to local disk.
    result = init(config_file, archive_root, "--confirm")

    assert result.exit_code == ExitCode.SAFETY
    assert error_codes(result) == ["HFMNT002"]
    assert list(archive_root.iterdir()) == []


def test_a_missing_archive_root_is_hfmnt001(config_file: Path, archive_root: Path):
    archive_root.rmdir()

    result = init(config_file, archive_root, "--confirm")

    assert result.exit_code == ExitCode.SAFETY
    assert error_codes(result) == ["HFMNT001"]


def test_a_read_only_mount_is_refused(
    config_file: Path, archive_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    table = tmp_path / "mountinfo"
    table.write_text(
        f"457 47 0:68 / {archive_root.resolve()} ro,relatime - nfs4 nas:/export ro,vers=4.2\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", table)

    result = init(config_file, archive_root, "--confirm")

    assert result.exit_code == ExitCode.SAFETY
    assert error_codes(result) == ["HFMNT004"]


# --------------------------------------------------------------------------- #
# --confirm
# --------------------------------------------------------------------------- #


def test_confirm_creates_the_archive(config_file: Path, mounted: Path):
    result = init(config_file, mounted, "--confirm")

    assert result.exit_code == ExitCode.SUCCESS
    assert (mounted / ".hfcache-root").is_file()
    assert (mounted / "published" / "repos").is_dir()


def test_the_created_archive_reports_its_paths_and_identity(config_file: Path, mounted: Path):
    data = envelope(init(config_file, mounted, "--confirm"))["data"]

    assert data["archive_id"] == ARCHIVE_ID
    assert data["archive_root"] == str(mounted)
    assert data["sentinel"] == ".hfcache-root"
    assert ".store/hub" in data["created_directories"]
    assert data["adopted_published"] is False


def test_confirm_adopts_a_pre_existing_published(config_file: Path, mounted: Path):
    published = mounted / "published"
    published.mkdir()
    published.chmod(0o2750)

    data = envelope(init(config_file, mounted, "--confirm"))["data"]

    assert data["adopted_published"] is True
    assert "published" not in data["created_directories"]
    assert stat.S_IMODE(published.stat().st_mode) == 0o2750


def test_initializing_a_second_time_is_hfmnt014(config_file: Path, mounted: Path):
    init(config_file, mounted, "--confirm")

    result = init(config_file, mounted, "--confirm")

    assert result.exit_code == ExitCode.SAFETY
    assert error_codes(result) == ["HFMNT014"]


def test_unknown_content_is_refused_and_preserved(config_file: Path, mounted: Path):
    stranger = mounted / "somebody-elses-file"
    stranger.write_text("keep me", encoding="utf-8")

    result = init(config_file, mounted, "--confirm")

    assert result.exit_code == ExitCode.SAFETY
    assert error_codes(result) == ["HFMNT014"]
    assert stranger.read_text(encoding="utf-8") == "keep me"
    assert not (mounted / ".hfcache-root").exists()


def test_a_write_failure_after_the_checks_is_exit_twenty_not_a_traceback(
    config_file: Path, mounted: Path
):
    # Everything `archive init` proves beforehand is a read. A server-side
    # read-only export or a reached quota is only discovered by writing, and it
    # must still reach the operator as a code.
    mounted.chmod(0o500)
    try:
        result = init(config_file, mounted, "--confirm")
    finally:
        mounted.chmod(0o750)

    assert result.exit_code == ExitCode.SAFETY
    assert error_codes(result) == ["HFMNT008"]


def test_a_failed_initialization_can_be_retried_after_the_obstacle_is_removed(
    config_file: Path, mounted: Path
):
    stranger = mounted / "somebody-elses-file"
    stranger.write_text("x", encoding="utf-8")
    assert init(config_file, mounted, "--confirm").exit_code == ExitCode.SAFETY

    stranger.unlink()

    assert init(config_file, mounted, "--confirm").exit_code == ExitCode.SUCCESS


# --------------------------------------------------------------------------- #
# Human-readable output
# --------------------------------------------------------------------------- #


def test_the_human_summary_names_the_archive_it_created(config_file: Path, mounted: Path):
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_file),
            "archive",
            "init",
            "--archive-root",
            str(mounted),
            "--confirm",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert ARCHIVE_ID in result.output
    assert str(mounted) in result.output


def test_the_human_summary_of_an_inspection_names_the_state(config_file: Path, mounted: Path):
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_file),
            "archive",
            "init",
            "--archive-root",
            str(mounted),
            "--inspect",
        ],
    )

    assert "uninitialized" in result.output
    assert "nfs4" in result.output


def test_quiet_suppresses_the_summary_but_not_the_work(config_file: Path, mounted: Path):
    result = runner.invoke(
        app,
        [
            "--quiet",
            "--config",
            str(config_file),
            "archive",
            "init",
            "--archive-root",
            str(mounted),
            "--confirm",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert result.output == ""
    assert (mounted / ".hfcache-root").is_file()


def test_a_refusal_is_readable_without_json(config_file: Path, mounted: Path):
    (mounted / "somebody-elses-file").write_text("x", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "--config",
            str(config_file),
            "archive",
            "init",
            "--archive-root",
            str(mounted),
            "--confirm",
        ],
    )

    assert result.exit_code == ExitCode.SAFETY
    assert "HFMNT014" in result.output
