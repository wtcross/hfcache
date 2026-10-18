"""The `verify` command — `docs/cli.md` §2, exit `0` clean and `40` on a finding.

What is asserted here is the *command*: which run it decides to check, the
envelope it emits, the exit code a scheduler will see, and that a finding leaves
the archive exactly as it was. The checking itself is
`tests/unit/test_verification.py`'s.
"""

import hashlib
import json
import os
import shutil
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 - fixtures take and return one at run time

import pytest
from typer.testing import CliRunner

from hfcache import verification as verification_module
from hfcache.archive import initialize_archive
from hfcache.cli import app
from hfcache.errors import ExitCode
from hfcache.hub import OFFLINE_VARIABLE, networking_disabled
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, new_run_id
from hfcache.locking import exclusive_lock, lock_path
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import (
    VerificationStates,
    publish_verification_catalog,
    read_verification_catalog,
    rebuild_catalog,
)
from hfcache.reporting import FullVerificationSummary, RunReport, VerificationCatalog
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

    monkeypatch.setattr("hfcache.services.commands.networking_disabled", recording)
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

    monkeypatch.setattr("hfcache.services.commands.HubClient", Refuses)
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


# --------------------------------------------------------------------------- #
# `--revision` (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


def test_revision_verifies_exactly_one_revision(config_path, archive):
    publish(archive, commit_sha=SHA_A)
    publish(archive, commit_sha=SHA_B)
    envelope = envelope_of(invoke(config_path, "--revision", f"{MODEL.selector}@{SHA_A}"))
    assert envelope["command"] == "verify --revision"
    assert envelope["data"]["mode"] == "revision"
    assert envelope["data"]["scope"]["revisions"] == 1
    assert envelope["data"]["scope"]["repositories"] == 1


def test_revision_reports_the_damage_in_the_revision_it_was_given(config_path, archive):
    published = publish(archive, commit_sha=SHA_A)
    publish(archive, commit_sha=SHA_B)
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()

    clean = invoke(config_path, "--revision", f"{MODEL.selector}@{SHA_B}")
    assert clean.exit_code == ExitCode.SUCCESS

    damaged = invoke(config_path, "--revision", f"{MODEL.selector}@{SHA_A}")
    assert damaged.exit_code == ExitCode.INTEGRITY
    assert [problem["code"] for problem in envelope_of(damaged)["errors"]] == ["HFVER003"]


def test_revision_verifies_a_repository_that_is_not_configured(config_path, archive):
    """`AD-06`: an unmanaged repository's data is still the archive's, and a
    revision under investigation is often one whose repository was removed."""
    publish(archive, identity=DATASET, commit_sha=SHA_A)
    assert DATASET.id not in config_path.read_text(encoding="utf-8")
    result = invoke(config_path, "--revision", f"{DATASET.selector}@{SHA_A}")
    assert result.exit_code == ExitCode.SUCCESS
    assert envelope_of(result)["data"]["scope"]["revisions"] == 1


def test_revision_without_a_sha_is_refused(config_path, archive):
    """Defaulting to the current revision would answer a question nobody asked,
    and would report clean while the suspect revision sat unexamined."""
    publish(archive)
    result = invoke(config_path, "--revision", MODEL.selector)
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG001"]


def test_revision_with_an_abbreviated_sha_is_refused(config_path, archive):
    publish(archive)
    result = invoke(config_path, "--revision", f"{MODEL.selector}@1111111")
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG001"]


def test_a_sha_the_archive_does_not_retain_is_an_invocation_error(config_path, archive):
    """Exit `40` would tell a scheduler the archive is corrupt because somebody
    typed one wrong character."""
    publish(archive, commit_sha=SHA_A)
    result = invoke(config_path, "--revision", f"{MODEL.selector}@{SHA_B}")
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG004"]


def test_revision_and_full_together_are_refused(config_path):
    result = invoke(config_path, "--full", "--revision", f"{MODEL.selector}@{SHA_A}")
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG002"]


def test_a_refusal_still_names_the_mode_it_refused(config_path):
    """`command` in the envelope says which invocation failed, even when the
    invocation was the thing that was wrong."""
    result = invoke(config_path, "--revision", "not-a-selector")
    assert envelope_of(result)["command"] == "verify --revision"
    result = invoke(config_path)
    assert envelope_of(result)["command"] == "verify --new"


# --------------------------------------------------------------------------- #
# `--estimate` (plan §16.4)
# --------------------------------------------------------------------------- #


def test_estimate_reports_what_full_would_read(config_path, archive):
    publish(archive, commit_sha=SHA_A)
    publish(archive, commit_sha=SHA_B)
    publish(archive, identity=DATASET, commit_sha=SHA_A)
    result = invoke(config_path, "--estimate")
    assert result.exit_code == ExitCode.SUCCESS
    data = envelope_of(result)["data"]
    assert data["mode"] == "estimate"
    assert data["repositories"] == 2
    assert data["revisions"] == 3
    # Two hardlinked revisions of the model share their objects; the dataset's
    # are the same blobs again, because the fixture publishes identical content.
    assert data["unique_objects"] == len(FILES)
    assert data["unique_bytes"] == sum(len(payload) for payload in FILES.values())


def test_estimate_counts_copy_mode_files_individually(config_path, archive):
    publish(archive, commit_sha=SHA_A, publication_mode="copy")
    publish(archive, commit_sha=SHA_B, publication_mode="copy")
    data = envelope_of(invoke(config_path, "--estimate"))["data"]
    assert data["unique_objects"] == 2 * len(FILES)
    assert data["unique_bytes"] == 2 * sum(len(payload) for payload in FILES.values())


def test_estimate_has_no_duration_before_a_full_verification_has_run(config_path, archive):
    """A number derived from a rate nobody measured is a guess wearing a
    decimal point, and this is the operator sizing a maintenance window."""
    publish(archive)
    data = envelope_of(invoke(config_path, "--estimate"))["data"]
    assert data["measured_throughput_bytes_per_second"] is None
    assert data["estimated_duration_seconds"] is None


def test_estimate_uses_the_last_measured_throughput_when_there_is_one(config_path, archive):
    publish(archive)
    publish_verification_catalog(
        archive,
        VerificationCatalog(
            generated_at=NOW,
            last_full_verification=FullVerificationSummary(
                completed_at=NOW,
                duration_seconds=2.0,
                outcome="clean",
                report="runs/20260726T120000Z-" + "0" * 32 + ".json",
                started_at=NOW,
                throughput_bytes_per_second=100.0,
                unique_bytes=200,
                unique_objects=2,
            ),
        ),
    )
    data = envelope_of(invoke(config_path, "--estimate"))["data"]
    assert data["measured_throughput_bytes_per_second"] == 100.0
    assert data["estimated_duration_seconds"] == data["unique_bytes"] / 100.0


def test_a_catalog_that_will_not_load_is_treated_as_never_measured(config_path, archive):
    """Derived state never raises the confidence level (`FS-16`)."""
    publish(archive)
    archive.verification_catalog.parent.mkdir(parents=True, exist_ok=True)
    archive.verification_catalog.write_text("{ not json", encoding="utf-8")
    data = envelope_of(invoke(config_path, "--estimate"))["data"]
    assert data["measured_throughput_bytes_per_second"] is None


def test_estimate_reports_storage_maintenance_as_undetectable(config_path, archive):
    """Decision 50: the writer has no supported channel to observe NAS
    maintenance, and saying so beats reporting a clear window it cannot see."""
    publish(archive)
    assert envelope_of(invoke(config_path, "--estimate"))["data"]["storage_maintenance"] == (
        "undetectable"
    )


def test_estimate_counts_a_path_it_cannot_stat_without_charging_for_it(config_path, archive):
    published = publish(archive)
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()
    data = envelope_of(invoke(config_path, "--estimate"))["data"]
    assert data["unreadable_objects"] == 1
    assert data["unique_bytes"] == len(FILES["nested/weights.bin"])


def test_estimate_exits_zero_on_a_damaged_archive(config_path, archive):
    """Nothing was read, so nothing can have been found wrong; an estimator that
    could report `40` would confuse a scheduling question with an answer."""
    published = publish(archive)
    reference = RepositoryLayout(archive=archive, identity=MODEL).revision_ref(
        CommitSha(published.commit_sha)
    )
    reference.write_text("{ not json", encoding="utf-8")
    result = invoke(config_path, "--estimate")
    assert result.exit_code == ExitCode.SUCCESS
    data = envelope_of(result)["data"]
    assert data["revisions"] == 1
    assert data["repositories"] == 1
    assert data["unique_objects"] == 0


def test_estimate_hashes_nothing_and_takes_no_lock(config_path, archive):
    """It is a planning command, so it answers while a sync holds the lock."""
    publish(archive)
    with exclusive_lock(lock_path(), command="sync", wait_seconds=0):
        result = invoke(config_path, "--estimate")
    assert result.exit_code == ExitCode.SUCCESS


def test_estimate_answers_on_an_archive_with_nothing_published(config_path, archive):
    data = envelope_of(invoke(config_path, "--estimate"))["data"]
    assert data == {
        "estimated_duration_seconds": None,
        "measured_throughput_bytes_per_second": None,
        "mode": "estimate",
        "repositories": 0,
        "revisions": 0,
        "storage_maintenance": "undetectable",
        "unique_bytes": 0,
        "unique_objects": 0,
        "unreadable_objects": 0,
    }


def test_the_human_estimate_names_the_unknown_duration(config_path, archive):
    publish(archive)
    result = runner.invoke(app, ["--config", str(config_path), "verify", "--estimate"])
    assert result.exit_code == ExitCode.SUCCESS
    assert "never measured" in result.stdout


def test_estimate_and_new_together_are_refused(config_path):
    result = invoke(config_path, "--new", "--estimate")
    assert result.exit_code == ExitCode.CONFIGURATION
    assert [problem["code"] for problem in envelope_of(result)["errors"]] == ["HFARG002"]


# --------------------------------------------------------------------------- #
# Persistence and health (plan §16.2 items 8 and 9)
# --------------------------------------------------------------------------- #


def reports_in(layout: ArchiveLayout) -> list[Path]:
    return sorted(layout.runs.glob("*.json"))


def test_a_verification_writes_a_durable_report(config_path, archive):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    before = reports_in(archive)
    envelope = envelope_of(invoke(config_path, "--new"))

    written = [path for path in reports_in(archive) if path not in before]
    assert len(written) == 1
    assert envelope["data"]["report"] == f"runs/{written[0].name}"
    persisted = json.loads(written[0].read_text(encoding="utf-8"))
    assert persisted["run_id"] == envelope["run_id"]
    assert persisted["command"] == "verify --new"
    assert persisted["verification_outcome"] == "clean"
    assert written[0].stat().st_mode & 0o777 == 0o600


def test_a_failing_verification_writes_its_report_too(config_path, archive):
    """The evidence is the point: a run that found something must leave a record."""
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()
    before = reports_in(archive)

    result = invoke(config_path, "--new")
    assert result.exit_code == ExitCode.INTEGRITY

    written = [path for path in reports_in(archive) if path not in before]
    persisted = json.loads(written[0].read_text(encoding="utf-8"))
    assert persisted["verification_outcome"] == "failed"
    assert persisted["findings"][0]["kind"] == "missing"


class InterruptedRunError(RuntimeError):
    """Stands in for the writer losing power partway through a verification."""


def fingerprint(layout: ArchiveLayout) -> dict[str, str]:
    """Every published byte, keyed by path — what must not change."""
    return {
        str(path.relative_to(layout.published)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(layout.published.rglob("*"))
        if path.is_file()
    }


def test_a_verification_interrupted_leaves_the_archive_exactly_as_it_was(
    config_path, archive, monkeypatch
):
    """§26.6's last row: inject failure *during* the quarterly verification.

    Verification only reads. Its report and its catalog entry are each replaced
    by a single atomic rename, so an interruption can leave a partial neither,
    and no retained revision is touched by the run that was checking it. The run
    after it still reports clean, which is the property that matters: an
    interrupted verification costs time, not evidence.
    """
    publish(archive, commit_sha=SHA_A)
    publish(archive, commit_sha=SHA_B)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS

    before_catalog = read_verification_catalog(archive)
    before_reports = reports_in(archive)
    before_content = fingerprint(archive)

    real = verification_module.verify_target
    calls: list[int] = []

    def failing(target, reads):
        calls.append(1)
        # After the first revision has been read, so the crash lands mid-run
        # rather than before it started.
        if len(calls) == 2:
            raise InterruptedRunError
        return real(target, reads)

    monkeypatch.setattr(verification_module, "verify_target", failing)
    result = invoke(config_path, "--full")
    # Restore this one attribute rather than `monkeypatch.undo()`, which would
    # also revert the `archive` fixture's mount table and lock directory and send
    # the next invocation at the real `/run/hfcache`.
    monkeypatch.setattr(verification_module, "verify_target", real)

    assert isinstance(result.exception, InterruptedRunError)
    assert fingerprint(archive) == before_content, "verification changed published bytes"
    assert reports_in(archive) == before_reports, "a partial report was left behind"
    after_catalog = read_verification_catalog(archive)
    assert after_catalog is not None
    assert before_catalog is not None
    assert after_catalog.last_full_verification == before_catalog.last_full_verification
    assert not after_catalog.is_degraded

    # And the next run is clean, having lost nothing but the time.
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS


def test_a_full_verification_updates_the_catalog(config_path, archive):
    published = publish(archive)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.outstanding_failures == ()
    assert catalog.last_full_verification is not None
    assert catalog.last_full_verification.outcome == "clean"
    assert catalog.last_full_verification.report.startswith("runs/")
    assert (archive.root / catalog.last_full_verification.report).is_file()
    (entry,) = catalog.repositories
    assert entry.repository_id == MODEL.id
    assert [revision.commit_sha for revision in entry.revisions] == [published.commit_sha]
    assert entry.revisions[0].outcome == "clean"


def test_findings_become_outstanding_failures(config_path, archive):
    published = publish(archive)
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.is_degraded
    (failure,) = catalog.outstanding_failures
    assert failure.kind == "missing"
    assert failure.path == "config.json"
    assert catalog.repositories[0].revisions[0].outcome == "failed"


def test_a_narrow_run_never_clears_a_failure_it_did_not_look_at(config_path, archive):
    """`docs/schemas.md` §5.2: an entry is cleared only by a verification that
    re-reads the object, never by one that simply did not check it."""
    damaged = publish(archive, commit_sha=SHA_A)
    publish(archive, commit_sha=SHA_B)
    (tree_of(archive, damaged.commit_sha, damaged.publication_id) / "config.json").unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    healthy = invoke(config_path, "--revision", f"{MODEL.selector}@{SHA_B}")
    assert healthy.exit_code == ExitCode.SUCCESS

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.is_degraded
    assert [failure.commit_sha for failure in catalog.outstanding_failures] == [SHA_A]
    assert catalog.repositories[0].revisions[1].outcome == "clean"


def test_re_reading_a_repaired_object_clears_its_failure(config_path, archive):
    published = publish(archive)
    path = tree_of(archive, published.commit_sha, published.publication_id) / "config.json"
    payload = path.read_bytes()
    path.unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    path.write_bytes(payload)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.outstanding_failures == ()
    assert not catalog.is_degraded


def test_first_seen_at_survives_a_second_report_of_the_same_failure(config_path, archive):
    """An operator has to be able to tell last night's fault from a quarter-old one."""
    published = publish(archive)
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY
    first = read_verification_catalog(archive)
    assert first is not None

    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY
    second = read_verification_catalog(archive)
    assert second is not None

    assert second.outstanding_failures[0].first_seen_at == (
        first.outstanding_failures[0].first_seen_at
    )
    assert second.generated_at > first.generated_at


def test_a_revision_that_is_no_longer_retained_leaves_the_catalog(config_path, archive):
    """A pruned revision does not exist, and reporting the archive permanently
    degraded over content it no longer holds is a signal nobody can clear."""
    published = publish(archive, commit_sha=SHA_A)
    publish(archive, commit_sha=SHA_B)
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    RepositoryLayout(archive=archive, identity=MODEL).revision_ref(CommitSha(SHA_A)).unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.outstanding_failures == ()
    assert [revision.commit_sha for revision in catalog.repositories[0].revisions] == [SHA_B]


def test_a_narrow_run_does_not_replace_the_last_full_verification(config_path, archive):
    """A `--new` run measures a handful of objects; letting its throughput stand
    as the measured rate would give the estimator the wrong workload."""
    published = publish(archive)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS
    after_full = read_verification_catalog(archive)
    assert after_full is not None

    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    assert invoke(config_path, "--new").exit_code == ExitCode.SUCCESS

    after_new = read_verification_catalog(archive)
    assert after_new is not None
    assert after_new.last_full_verification == after_full.last_full_verification


def test_an_unreadable_reference_is_recorded_without_naming_an_instance(config_path, archive):
    published = publish(archive)
    RepositoryLayout(archive=archive, identity=MODEL).revision_ref(
        CommitSha(published.commit_sha)
    ).write_text("{ not json", encoding="utf-8")
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.outstanding_failures[0].publication_id is None
    assert catalog.repositories[0].revisions[0].publication_id is None
    assert catalog.repositories[0].revisions[0].outcome == "failed"


# --------------------------------------------------------------------------- #
# An unparseable current reference (`VER-009`)
# --------------------------------------------------------------------------- #


def current_ref_path(layout: ArchiveLayout) -> Path:
    return RepositoryLayout(archive=layout, identity=MODEL).current_ref


def test_an_unparseable_current_ref_is_hfver008_at_exit_40(config_path, archive):
    """`VER-009`, closing decision 73's documented limit.

    The one file a consumer must read will not parse, and the run now says so
    durably: exit `40`, exactly one finding, attributed to no revision and no
    instance because the damage is the pointer itself.
    """
    publish(archive)
    current_ref_path(archive).write_text("{ truncated", encoding="utf-8")

    result = invoke(config_path, "--full")

    assert result.exit_code == ExitCode.INTEGRITY
    envelope = envelope_of(result)
    assert [problem["code"] for problem in envelope["errors"]] == ["HFVER008"]
    (finding,) = envelope["data"]["findings"]
    assert finding["kind"] == "ref_invalid"
    assert finding["commit_sha"] is None
    assert finding["publication_id"] is None


def test_a_schema_invalid_current_ref_is_the_same_finding_at_exit_40(config_path, archive):
    """Valid JSON that is not a valid reference is equally unreadable."""
    publish(archive)
    current_ref_path(archive).write_text(json.dumps({"commit_sha": "not a sha"}), encoding="utf-8")

    result = invoke(config_path, "--full")

    assert result.exit_code == ExitCode.INTEGRITY
    (finding,) = envelope_of(result)["data"]["findings"]
    assert finding["kind"] == "ref_invalid"
    assert finding["commit_sha"] is None


def test_a_null_sha_failure_is_outstanding_and_never_a_revision_entry(config_path, archive):
    """`docs/schemas.md` §5.2: the failure lands in `outstanding_failures[]` and
    the sound revision it pointed at stays clean in `repositories[].revisions[]`."""
    published = publish(archive)
    current_ref_path(archive).write_text("{ truncated", encoding="utf-8")

    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.is_degraded
    (failure,) = catalog.outstanding_failures
    assert failure.commit_sha is None
    assert failure.publication_id is None
    assert failure.kind == "ref_invalid"
    (entry,) = catalog.repositories
    assert [revision.commit_sha for revision in entry.revisions] == [published.commit_sha]
    assert entry.revisions[0].outcome == "clean"


def test_a_narrow_run_carries_a_null_sha_failure_forward(config_path, archive):
    """§5.2's rule holds for the entry the retained-key rule cannot see.

    A null-SHA failure matches no retained revision key, so the ordinary
    clearing rule would silently drop it on the next narrow run — a `--revision`
    that never re-read the current reference would then appear to have fixed it.
    It is carried forward instead: only `--full` re-checks the reference today.
    """
    published = publish(archive)
    current_ref_path(archive).write_text("{ truncated", encoding="utf-8")
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    healthy = invoke(config_path, "--revision", f"{MODEL.selector}@{published.commit_sha}")
    assert healthy.exit_code == ExitCode.SUCCESS

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.is_degraded
    (failure,) = catalog.outstanding_failures
    assert failure.commit_sha is None


def test_a_clean_full_run_clears_a_null_sha_failure(config_path, archive):
    published = publish(archive)
    reference = current_ref_path(archive).read_bytes()
    current_ref_path(archive).write_bytes(b"{ truncated")
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    current_ref_path(archive).write_bytes(reference)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.outstanding_failures == ()
    assert not catalog.is_degraded
    assert published.commit_sha  # the revision came through it all retained


def test_a_still_broken_full_run_preserves_a_null_sha_first_seen_at(config_path, archive):
    """A `--full` re-reads the reference, so it drops and re-adds the entry —
    and the re-add must not reset the clock an operator reads."""
    publish(archive)
    current_ref_path(archive).write_text("{ truncated", encoding="utf-8")
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY
    first = read_verification_catalog(archive)
    assert first is not None

    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY
    second = read_verification_catalog(archive)
    assert second is not None

    (failure,) = second.outstanding_failures
    assert failure.first_seen_at == first.outstanding_failures[0].first_seen_at
    assert second.generated_at > first.generated_at


def test_a_null_sha_failure_leaves_when_its_repository_leaves_published(tmp_path, archive):
    """The health signal follows the content: a repository removed from
    `published/` has no current reference to repair, and a degraded flag nobody
    can clear is the same defect the retained-set rule closes for revisions."""
    published = publish(archive)
    dataset = publish(archive, identity=DATASET, commit_sha=SHA_B)
    both = tmp_path / "both.toml"
    both.write_text(
        config_for(archive.root)
        + f"""
[[repositories]]
id = "{DATASET.id}"
type = "{DATASET.type}"
""",
        encoding="utf-8",
    )
    current_ref_path(archive).write_text("{ truncated", encoding="utf-8")
    assert invoke(both, "--full").exit_code == ExitCode.INTEGRITY

    shutil.rmtree(RepositoryLayout(archive=archive, identity=MODEL).directory)
    healthy = invoke(both, "--revision", f"{DATASET.selector}@{dataset.commit_sha}")
    assert healthy.exit_code == ExitCode.SUCCESS

    catalog = read_verification_catalog(archive)
    assert catalog is not None
    assert catalog.outstanding_failures == ()
    assert not catalog.is_degraded
    assert published.commit_sha  # the model's revision existed until the removal


def test_status_reports_degraded_over_a_null_sha_failure(config_path, archive):
    publish(archive)
    current_ref_path(archive).write_text("{ truncated", encoding="utf-8")
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    health = status_of(config_path)["archive"]["verification"]
    assert health["degraded"] is True
    assert health["outstanding_failures"] == 1


def test_verification_states_are_untouched_by_a_null_sha_failure(config_path, archive):
    """`repositories[].revisions[]` never carries a null SHA, so every consumer
    of `VerificationStates` reads exactly what it read before: the revision was
    re-read clean in the same run that reported the reference unreadable."""
    published = publish(archive)
    current_ref_path(archive).write_text("{ truncated", encoding="utf-8")
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    states = VerificationStates.of(archive)
    assert states.state_of(MODEL, published.commit_sha, published.publication_id) == "verified"


def test_a_report_that_cannot_be_written_is_reported(config_path, archive, monkeypatch):
    published = publish(archive)
    write_run_report(
        archive, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    archive.runs.chmod(0o500)
    try:
        result = invoke(config_path, "--new")
    finally:
        archive.runs.chmod(0o700)
    assert result.exit_code == ExitCode.INTEGRITY
    # The verification itself still reached a verdict, and it is in the payload.
    assert envelope_of(result)["data"]["verification_outcome"] == "clean"


# --------------------------------------------------------------------------- #
# `verification_state` has one source of truth (decision 51)
# --------------------------------------------------------------------------- #


def status_of(config_path: Path) -> dict:
    result = runner.invoke(app, ["--config", str(config_path), "--json", "status"])
    return json.loads(result.stdout)["data"]


def listed(config_path: Path) -> dict:
    result = runner.invoke(app, ["--config", str(config_path), "--json", "list", "--revisions"])
    return json.loads(result.stdout)["data"]


def test_a_published_revision_is_unverified_until_something_verifies_it(config_path, archive):
    """Ingestion hashing read the Hub cache before the tree existed; `verify` is
    what reads the tree (decision 51)."""
    publish(archive)
    assert status_of(config_path)["repositories"][0]["verification_state"] == "unverified"
    assert listed(config_path)["repositories"][0]["revisions"][0]["verification_state"] == (
        "unverified"
    )


def test_a_verified_revision_reads_verified_everywhere(config_path, archive):
    publish(archive)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS
    assert status_of(config_path)["repositories"][0]["verification_state"] == "verified"
    assert listed(config_path)["repositories"][0]["revisions"][0]["verification_state"] == (
        "verified"
    )
    catalog = rebuild_catalog(archive, generated_at=NOW)
    assert catalog.repositories[0].revisions[0].verification_state == "verified"


def test_a_new_instance_of_a_verified_sha_reads_unverified(config_path, archive):
    """Decision 62. A verification re-reads the bytes of one published
    *instance*, and two instances of the same SHA are different bytes in
    different places — a repair replaces one, and a prune followed by a later
    republication of the same SHA produces another.

    Found on the live archive: a revision that had been pruned and re-synced read
    `verified` on the strength of a verification of the instance the prune
    removed, which is `verified` for content nothing had ever re-read.
    """
    first = publish(archive)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS
    assert status_of(config_path)["repositories"][0]["verification_state"] == "verified"

    # The cache snapshot is what a download produces; clear it so the second
    # publication builds its own, exactly as a re-sync after a prune does.
    shutil.rmtree(archive.hub_cache / f"{MODEL.type}s--{MODEL.id.replace('/', '--')}")
    second = publish(archive)

    assert second.publication_id != first.publication_id
    assert second.commit_sha == first.commit_sha
    assert status_of(config_path)["repositories"][0]["verification_state"] == "unverified"
    assert listed(config_path)["repositories"][0]["revisions"][0]["verification_state"] == (
        "unverified"
    )
    catalog = rebuild_catalog(archive, generated_at=NOW)
    assert catalog.repositories[0].revisions[0].verification_state == "unverified"

    # And verifying again makes it true again, of the instance that now exists.
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS
    assert status_of(config_path)["repositories"][0]["verification_state"] == "verified"


def test_a_catalog_entry_naming_no_instance_reads_unverified(config_path, archive):
    """The optional `publication_id` case. A verification that could not name an
    instance (decision 49) cannot be attributed to anything on disk, so the
    conservative answer to "was this instance re-read?" is no."""
    published = publish(archive)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS
    catalog = VerificationCatalog.model_validate_json(
        archive.verification_catalog.read_text(encoding="utf-8")
    )
    payload = catalog.model_dump(mode="json")
    payload["repositories"][0]["revisions"][0]["publication_id"] = None
    archive.verification_catalog.write_text(json.dumps(payload), encoding="utf-8")

    assert published.publication_id
    assert status_of(config_path)["repositories"][0]["verification_state"] == "unverified"


def test_a_failed_revision_reads_failed_everywhere(config_path, archive):
    """`failed` was unreachable while the state was hardcoded; it is not now."""
    published = publish(archive)
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY
    assert status_of(config_path)["repositories"][0]["verification_state"] == "failed"
    assert listed(config_path)["repositories"][0]["revisions"][0]["verification_state"] == "failed"
    catalog = rebuild_catalog(archive, generated_at=NOW)
    assert catalog.repositories[0].revisions[0].verification_state == "failed"


def test_status_reports_the_archive_as_degraded_until_it_is_cleared(config_path, archive):
    published = publish(archive)
    path = tree_of(archive, published.commit_sha, published.publication_id) / "config.json"
    payload = path.read_bytes()
    path.unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY

    health = status_of(config_path)["archive"]["verification"]
    assert health["degraded"] is True
    assert health["outstanding_failures"] == 1
    assert health["last_full_verification"]["outcome"] == "failed"

    path.write_bytes(payload)
    assert invoke(config_path, "--full").exit_code == ExitCode.SUCCESS
    assert status_of(config_path)["archive"]["verification"]["degraded"] is False


def test_the_human_status_says_the_archive_is_degraded(config_path, archive):
    published = publish(archive)
    (tree_of(archive, published.commit_sha, published.publication_id) / "config.json").unlink()
    assert invoke(config_path, "--full").exit_code == ExitCode.INTEGRITY
    result = runner.invoke(app, ["--config", str(config_path), "status"])
    assert result.exit_code == ExitCode.SUCCESS
    assert "archive degraded" in result.output
    assert "failed" in result.output
