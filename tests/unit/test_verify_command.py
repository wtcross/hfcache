"""The `verify` command — `docs/cli.md` §2, exit `0` clean and `40` on a finding.

What is asserted here is the *command*: which run it decides to check, the
envelope it emits, the exit code a scheduler will see, and that a finding leaves
the archive exactly as it was. The checking itself is
`tests/unit/test_verification.py`'s.
"""

import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 - fixtures take and return one at run time

import pytest
from typer.testing import CliRunner

from hfcache.archive import initialize_archive
from hfcache.cli import app
from hfcache.errors import ExitCode
from hfcache.hub import OFFLINE_VARIABLE, networking_disabled
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, new_run_id
from hfcache.locking import exclusive_lock, lock_path
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.reporting import RunReport
from hfcache.storage import parse_mount_table, write_model
from tests.unit.test_verification import (
    ARCHIVE_ID,
    DATASET,
    ENVELOPE,
    FILES,
    MODEL,
    NOW,
    SHA_A,
    SHA_B,
    nfs_line,
    publish,
)

runner = CliRunner()

REPORT_MODE = 0o600


def config_for(archive_root: Path) -> str:
    return f"""
schema_version = 1

[storage]
archive_root = "{archive_root}"
archive_id = "{ARCHIVE_ID}"
minimum_free_space_gib = 0
minimum_free_space_percent = 0

[sync]
# Zero, so a test that holds the lock observes the refusal rather than waiting
# out the hour a scheduled sync is configured for.
lock_wait_seconds = 0

[verification]
# Zero for the same reason; a scheduled full verification waits a day.
lock_wait_seconds = 0

[[repositories]]
id = "{MODEL.id}"
type = "{MODEL.type}"
"""


@pytest.fixture
def archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ArchiveLayout:
    """An initialized archive the application sees as a read/write NFSv4 mount.

    `--full` runs the §19 preflight, which reads the system mount table, so the
    table is substituted here the same way `tests/unit/test_readonly_commands.py`
    substitutes it — a real directory described as the mount it would be in
    production. The lock directory moves for the same reason: `/run/hfcache`
    belongs to the service identity, and a test suite has no business creating
    it.
    """
    root = tmp_path / "archive"
    root.mkdir()
    table = tmp_path / "mountinfo"
    table.write_text(nfs_line(os.path.realpath(root)), encoding="utf-8")
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", table)
    monkeypatch.setattr("hfcache.locking.LOCK_DIRECTORY", tmp_path / "run")
    layout = ArchiveLayout(root=root)
    initialize_archive(
        layout, archive_id=ARCHIVE_ID, table=parse_mount_table(nfs_line(os.path.realpath(root)))
    )
    return layout


@pytest.fixture
def config_path(tmp_path: Path, archive: ArchiveLayout) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(config_for(archive.root), encoding="utf-8")
    return path


def write_run_report(
    layout: ArchiveLayout,
    *,
    commit_sha: str,
    publication_id: str,
    started_at: datetime = NOW,
    status: str = "published",
) -> tuple[Path, str]:
    """Persist a run report describing one published revision."""
    run_id = new_run_id()
    report = RunReport.model_validate(
        dict(ENVELOPE)
        | {
            "command": "sync",
            "completed_at": started_at,
            "exit_code": 0,
            "outcome": "success",
            "run_id": run_id,
            "started_at": started_at,
            "repositories": [
                {
                    "publication_generation": 1,
                    "publication_id": publication_id,
                    "repository_id": MODEL.id,
                    "repository_type": MODEL.type,
                    "requested_revision": "main",
                    "resolved_commit_sha": commit_sha,
                    "status": status,
                }
            ],
        }
    )
    path = layout.run_report(started_at, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_model(path, report, mode=REPORT_MODE, code="HFVER007")
    return path, run_id


def invoke(config_path: Path, *arguments: str):
    return runner.invoke(app, ["--config", str(config_path), "--json", "verify", *arguments])


def envelope_of(result) -> dict:
    return json.loads(result.stdout)


def tree_of(layout: ArchiveLayout, commit_sha: str, publication_id: str) -> Path:
    return RepositoryLayout(archive=layout, identity=MODEL).instance(
        CommitSha(commit_sha), PublicationId(publication_id)
    )


# --------------------------------------------------------------------------- #
# Invocation
# --------------------------------------------------------------------------- #


def test_verify_without_a_mode_is_refused(config_path):
    result = invoke(config_path)
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG003"]


def test_verify_new_on_an_archive_with_no_run_reports_is_refused(config_path):
    result = invoke(config_path, "--new")
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG004"]


def test_a_run_id_naming_no_report_is_refused(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    result = invoke(config_path, "--new", "--run-id", "0" * 32)
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG004"]


def test_a_named_report_that_will_not_load_is_reported(config_path, archive):
    published = publish(archive)
    path, run_id = write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    path.write_text("{ not json", encoding="utf-8")
    result = invoke(config_path, "--new", "--run-id", run_id)
    assert result.exit_code == ExitCode.INTEGRITY
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFVER007"]


def test_a_damaged_newest_report_does_not_stop_the_default_search(config_path, archive):
    """An older readable run is a better answer than a refusal, and `--new` was
    not asked for a particular one."""
    published = publish(archive)
    older, older_id = write_run_report(
        archive,
        commit_sha=published.commit_sha,
        publication_id=published.publication_id,
        started_at=NOW,
    )
    newer, _ = write_run_report(
        archive,
        commit_sha=published.commit_sha,
        publication_id=published.publication_id,
        started_at=datetime(2026, 7, 27, 12, 0, 0, tzinfo=UTC),
    )
    newer.write_text("{ not json", encoding="utf-8")
    result = invoke(config_path, "--new")
    assert result.exit_code == ExitCode.SUCCESS
    assert older.is_file()
    assert older_id  # the readable one is what answered
    assert envelope_of(result)["data"]["scope"]["revisions"] == 1


# --------------------------------------------------------------------------- #
# A clean archive
# --------------------------------------------------------------------------- #


def test_a_clean_verification_exits_zero_and_reports_the_scope(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    result = invoke(config_path, "--new")
    assert result.exit_code == ExitCode.SUCCESS
    envelope = envelope_of(result)
    assert envelope["command"] == "verify --new"
    assert envelope["outcome"] == "success"
    assert envelope["errors"] == []
    assert envelope["data"]["verification_outcome"] == "clean"
    assert envelope["data"]["mode"] == "new"
    assert envelope["data"]["scope"]["repositories"] == 1
    assert envelope["data"]["scope"]["unique_objects_read"] == len(FILES)


def test_the_envelope_and_the_report_share_one_run_id(config_path, archive):
    """`docs/cli.md` §4: the envelope's run id correlates it with the report."""
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    envelope = envelope_of(invoke(config_path, "--new"))
    assert envelope["run_id"] == envelope["data"]["run_id"]


def test_a_run_that_published_nothing_verifies_nothing(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive,
        commit_sha=published.commit_sha,
        publication_id=published.publication_id,
        status="skipped",
    )
    result = invoke(config_path, "--new")
    assert result.exit_code == ExitCode.SUCCESS
    assert envelope_of(result)["data"]["scope"]["revisions"] == 0


# --------------------------------------------------------------------------- #
# A damaged archive
# --------------------------------------------------------------------------- #


def test_corrupted_content_exits_forty_and_names_the_repository(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    path = tree_of(archive, published.commit_sha, published.publication_id) / "config.json"
    payload = bytearray(path.read_bytes())
    payload[0] ^= 0xFF
    path.unlink()
    path.write_bytes(bytes(payload))

    result = invoke(config_path, "--new")
    assert result.exit_code == ExitCode.INTEGRITY
    envelope = envelope_of(result)
    assert envelope["outcome"] == "failed"
    assert [problem["code"] for problem in envelope["errors"]] == ["HFVER001"]
    assert envelope["errors"][0]["repository"] == f"{MODEL.type}:{MODEL.id}"
    assert envelope["errors"][0]["context"]["findings"] == 1
    assert envelope["data"]["verification_outcome"] == "failed"
    assert envelope["data"]["findings"][0]["kind"] == "digest_mismatch"


def test_findings_are_grouped_by_kind_and_repository(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    tree = tree_of(archive, published.commit_sha, published.publication_id)
    (tree / "config.json").unlink()
    (tree / "nested" / "weights.bin").unlink()
    (tree / "planted.txt").write_bytes(b"not ours")

    envelope = envelope_of(invoke(config_path, "--new"))
    grouped = {problem["code"]: problem["context"]["findings"] for problem in envelope["errors"]}
    assert grouped == {"HFVER003": 2, "HFVER004": 1}
    assert len(envelope["data"]["findings"]) == 3


def test_a_finding_changes_nothing_on_the_archive(config_path, archive):
    """Plan §16.1: a mismatch never rewrites a manifest, prunes, or re-downloads."""
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    tree = tree_of(archive, published.commit_sha, published.publication_id)
    (tree / "config.json").unlink()
    manifest_path = RepositoryLayout(archive=archive, identity=MODEL).manifest(
        CommitSha(published.commit_sha), PublicationId(published.publication_id)
    )
    reference_path = RepositoryLayout(archive=archive, identity=MODEL).revision_ref(
        CommitSha(published.commit_sha)
    )
    before = (manifest_path.read_bytes(), reference_path.read_bytes())

    assert invoke(config_path, "--new").exit_code == ExitCode.INTEGRITY

    assert (manifest_path.read_bytes(), reference_path.read_bytes()) == before
    assert reference_path.is_file()
    assert tree.is_dir()


# --------------------------------------------------------------------------- #
# Human output
# --------------------------------------------------------------------------- #


def test_the_human_summary_reports_what_was_read(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    result = runner.invoke(app, ["--config", str(config_path), "verify", "--new"])
    assert result.exit_code == ExitCode.SUCCESS
    assert "outcome" in result.stdout
    assert "clean" in result.stdout


def test_the_human_summary_prints_findings_on_stderr(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()
    result = runner.invoke(
        app, ["--config", str(config_path), "verify", "--new"], catch_exceptions=False
    )
    assert result.exit_code == ExitCode.INTEGRITY
    assert "HFVER003" in result.output


def test_quiet_suppresses_the_summary_but_not_the_exit_code(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    result = runner.invoke(app, ["--config", str(config_path), "--quiet", "verify", "--new"])
    assert result.exit_code == ExitCode.SUCCESS
    assert result.stdout == ""


def test_the_repository_identity_used_here_is_the_configured_one(config_path):
    """A guard on the fixture: the config and the fixtures name one repository."""
    assert RepositoryIdentity.of(MODEL.type, MODEL.id) == MODEL
    assert MODEL.id in config_path.read_text(encoding="utf-8")
    assert SHA_A  # the fixture's default revision, kept in one place


# --------------------------------------------------------------------------- #
# `--full` (plan §16.2)
# --------------------------------------------------------------------------- #


def test_full_covers_every_retained_revision_of_every_repository(config_path, archive):
    publish(archive, commit_sha=SHA_A)
    publish(archive, commit_sha=SHA_B)
    publish(archive, identity=DATASET, commit_sha=SHA_A)
    envelope = envelope_of(invoke(config_path, "--full"))
    assert envelope["data"]["mode"] == "full"
    assert envelope["data"]["scope"]["repositories"] == 2
    assert envelope["data"]["scope"]["revisions"] == 3


def test_full_covers_a_repository_that_is_no_longer_configured(config_path, archive):
    """`AD-06`: removing a repository from configuration never deletes its
    archive, so a quarterly job that skipped it would leave exactly the content
    nothing else touches unchecked."""
    publish(archive, identity=DATASET, commit_sha=SHA_A)
    assert DATASET.id not in config_path.read_text(encoding="utf-8")
    envelope = envelope_of(invoke(config_path, "--full"))
    assert envelope["data"]["scope"]["repositories"] == 1
    assert envelope["data"]["scope"]["revisions"] == 1


def test_full_reads_a_shared_blob_once_across_revisions(config_path, archive):
    """Plan §16.2 item 4: hardlinked content is one physical object, one read."""
    publish(archive, commit_sha=SHA_A)
    publish(archive, commit_sha=SHA_B)
    scope = envelope_of(invoke(config_path, "--full"))["data"]["scope"]
    assert scope["revisions"] == 2
    assert scope["unique_objects_read"] == len(FILES)
    assert scope["unique_bytes_read"] == sum(len(payload) for payload in FILES.values())


def test_full_exits_forty_on_corrupted_content(config_path, archive):
    published = publish(archive)
    path = tree_of(archive, published.commit_sha, published.publication_id) / "config.json"
    payload = bytearray(path.read_bytes())
    payload[0] ^= 0xFF
    path.unlink()
    path.write_bytes(bytes(payload))
    result = invoke(config_path, "--full")
    assert result.exit_code == ExitCode.INTEGRITY
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFVER001"]


def test_full_runs_with_hub_networking_disabled(config_path, archive, monkeypatch):
    """`docs/cli.md` §2. Observed from inside the run rather than inferred from
    the environment afterwards, which would look identical if it never ran."""
    publish(archive)
    observed: list[str | None] = []
    real = networking_disabled

    @contextmanager
    def recording():
        with real():
            observed.append(os.environ.get(OFFLINE_VARIABLE))
            yield

    monkeypatch.setattr("hfcache.cli.networking_disabled", recording)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS
    assert observed == ["1"]


def test_full_builds_no_hub_client(config_path, archive, monkeypatch):
    """The structural half of "networking disabled": there is nothing in the
    verification path that could make a request in the first place."""
    publish(archive)

    class Refuses:
        @staticmethod
        def of(*_arguments, **_keywords):
            message = "verify must never construct a Hub client"
            raise AssertionError(message)

    monkeypatch.setattr("hfcache.cli.HubClient", Refuses)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS


def test_full_is_refused_while_another_command_holds_the_lock(config_path, archive):
    """The verification lock is the global one (§22.3), which is what makes
    `--full` mutually exclusive with sync, prune, and repair."""
    publish(archive)
    with exclusive_lock(lock_path(), command="sync", wait_seconds=0):
        result = invoke(config_path, "--full")
    assert result.exit_code == ExitCode.SAFETY
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFMNT010"]


def test_full_refuses_an_archive_that_is_not_a_proven_mount(tmp_path, archive):
    """`--full` writes a report, so it passes the same §19 gate every other
    writing command does."""
    elsewhere = tmp_path / "not-a-mount"
    elsewhere.mkdir()
    path = tmp_path / "elsewhere.toml"
    path.write_text(config_for(elsewhere), encoding="utf-8")
    result = invoke(path, "--full")
    assert result.exit_code == ExitCode.SAFETY


def test_new_and_full_together_are_refused(config_path):
    result = invoke(config_path, "--new", "--full")
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG002"]


def test_run_id_without_new_is_refused(config_path):
    result = invoke(config_path, "--full", "--run-id", "0" * 32)
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG002"]


def test_full_takes_no_lock_it_does_not_release(config_path, archive):
    """Running it twice in a row proves the lock was released, and that a
    verification is repeatable because it changes nothing."""
    publish(archive)
    first = envelope_of(invoke(config_path, "--full"))["data"]
    second = envelope_of(invoke(config_path, "--full"))["data"]
    assert first["scope"] == second["scope"]
    assert first["verification_outcome"] == second["verification_outcome"] == "clean"
