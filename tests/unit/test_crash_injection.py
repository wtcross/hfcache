"""Crash injection for publication, prune, repair, and recovery.

Every interruption here is provoked rather than fabricated: a step is made to
fail, the transaction stops where it stopped, and `recover` is asked what to do
about the state that actually resulted. `tests/unit/test_failure_matrix.py`
maps these injections onto docs/development.md test contract's points.

The repair half additionally circles `AD-13` (`docs/architecture.md` §7.5, docs/cli.md
verification contract): repair must not be able to launder corrupt bytes into the expected
value. So the archive is built by publishing for real, damaged for real, and
the repair is run through `repair_revision` — and what is asserted afterwards
is that the *original* manifest is unchanged, that the retired instance is
still readable, and that a download which does not match is refused outright.
"""

import json
import os
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path  # noqa: TC003 - fixtures take and return one at run time
from typing import TYPE_CHECKING, Any

import pytest

from hfcache import recovery as recovery_module
from hfcache import repair as repair_module
from hfcache import retention as retention_module
from hfcache import sync as sync_module
from hfcache.archive import initialize_archive
from hfcache.config import ApplicationConfig, load_config
from hfcache.credentials import ResolvedToken, TokenSource
from hfcache.errors import ExitCode, RetentionError, SafetyError
from hfcache.hub import HubClient
from hfcache.identity import (
    CommitSha,
    PublicationId,
    TransactionId,
    new_run_id,
    new_transaction_id,
)
from hfcache.locking import exclusive_lock, lock_path
from hfcache.manifests import RevisionManifest
from hfcache.models import RepairCleanup, RepairRetirementRecord
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import read_reference, retained_references
from hfcache.recovery import apply_recovery, plan_recovery
from hfcache.repair import (
    cleanup_warnings,
    due_cleanups,
    finish_cleanup,
    pending_cleanups,
    repair_revision,
)
from hfcache.storage import parse_mount_table, read_model
from hfcache.sync import synchronize
from hfcache.transactions import Transaction, open_journals, open_transaction, read_journal
from tests.api_cli import api_cli
from tests.unit.test_synchronize import (
    ARCHIVE_ID,
    CONFIG,
    CONTENT,
    MODEL,
    SHA_A,
    SHA_B,
    FakeHub,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def invoke_api(config_path, arguments, *, json_output=True):
    with api_cli(config_path) as remote:
        return remote.invoke(arguments, json_output=json_output)


NOW = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)
GRACE_HOURS = 168


@pytest.fixture(autouse=True)
def _local_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Take the lock somewhere this test user owns; the `flock(2)` is still real."""
    run_directory = tmp_path / "run"
    run_directory.mkdir()
    monkeypatch.setattr("hfcache.locking.LOCK_DIRECTORY", run_directory)


@pytest.fixture
def layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ArchiveLayout:
    root = tmp_path / "archive"
    root.mkdir(mode=0o750)
    real = os.path.realpath(root)
    line = f"457 47 0:68 / {real} rw,relatime shared:488 - nfs4 nas:/x rw,vers=4.2\n"
    table = tmp_path / "mountinfo"
    table.write_text(line, encoding="utf-8")
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", table)
    built = ArchiveLayout(root=root)
    initialize_archive(built, archive_id=ARCHIVE_ID, table=parse_mount_table(line))
    return built


@pytest.fixture
def config_path(tmp_path: Path, layout: ArchiveLayout) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0), encoding="utf-8"
    )
    return path


@pytest.fixture
def config(config_path: Path) -> ApplicationConfig:
    return load_config(config_path)


@pytest.fixture
def hub() -> FakeHub:
    return FakeHub(
        revisions={SHA_A: dict(CONTENT), SHA_B: {**CONTENT, "extra.txt": b"a newer revision"}},
        heads={MODEL.selector: SHA_A, "dataset:organization/dataset-name": SHA_A},
    )


@pytest.fixture
def client(hub: FakeHub) -> HubClient:
    return HubClient(api=hub, token=ResolvedToken(source=TokenSource.NONE))


def envelope(config: ApplicationConfig) -> dict[str, Any]:
    return {
        "application_version": "0.1.0",
        "archive_id": config.storage.archive_id,
        "config_fingerprint": config.fingerprint(),
        "hostname": "writer",
        "huggingface_hub_version": "1.24.0",
        "invocation_mode": "interactive",
        "python_version": "3.14.6",
    }


def sync(client: HubClient, layout: ArchiveLayout, config: ApplicationConfig, selected=None):
    """A whole run, journal and all — see `test_synchronize.run_transaction`."""
    run_id = new_run_id()
    transaction = open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="sync",
        run_id=run_id,
        archive_id=config.storage.archive_id,
        config_fingerprint=config.fingerprint(),
    )
    transaction.checkpoint("run_started", run_id=run_id)
    transaction.checkpoint("preflight_passed", checks=[])
    transaction.checkpoint("journals_reconciled", reconciled_transaction_ids=[])
    return synchronize(
        client,
        layout,
        config,
        transaction,
        selected=selected if selected is not None else config.repositories,
        envelope=envelope(config),
        run_id=run_id,
        started_at=datetime.now(UTC),
    )


def only_model(config: ApplicationConfig) -> Sequence[Any]:
    return [repository for repository in config.repositories if repository.type == "model"]


def instance_of(layout: ArchiveLayout, commit_sha: str) -> Path:
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.revision_ref(CommitSha(commit_sha)))
    return repository.instance(CommitSha(commit_sha), PublicationId(reference.publication_id))


def manifest_of(layout: ArchiveLayout, commit_sha: str) -> RevisionManifest:
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.revision_ref(CommitSha(commit_sha)))
    return read_model(
        repository.manifest(CommitSha(commit_sha), PublicationId(reference.publication_id)),
        RevisionManifest,
        error=RetentionError,
        code="HFRET007",
    )


def damage(layout: ArchiveLayout, commit_sha: str, name: str = "config.json") -> None:
    """Flip a byte in a published file, the way a bad sector would."""
    path = instance_of(layout, commit_sha) / name
    payload = bytearray(path.read_bytes())
    payload[0] ^= 0xFF
    path.unlink()
    path.write_bytes(bytes(payload))


def repair(  # noqa: PLR0913 - a test helper mirroring `repair_revision`'s inputs
    client: HubClient,
    layout: ArchiveLayout,
    config: ApplicationConfig,
    *,
    commit_sha: str = SHA_A,
    reason: str = "checksum_error",
    now: datetime | None = None,
):
    return repair_revision(
        client,
        layout,
        config,
        identity=MODEL,
        commit_sha=CommitSha(commit_sha),
        reason=reason,
        envelope=envelope(config),
        run_id=new_run_id(),
        now=now,
    )


def names(layout: ArchiveLayout, transaction_id: str) -> list[str]:
    journal = read_journal(layout, layout.journal(TransactionId(transaction_id))).journal
    return [checkpoint.name for checkpoint in journal.checkpoints]


# --------------------------------------------------------------------------- #
# The repair transaction (§7.5 checkpoints 1-15)
# --------------------------------------------------------------------------- #


def test_a_repair_publishes_a_new_instance_of_the_same_revision(client, layout, config):
    sync(client, layout, config, only_model(config))
    before = manifest_of(layout, SHA_A)
    damage(layout, SHA_A)

    outcome = repair(client, layout, config)

    after = manifest_of(layout, SHA_A)
    assert outcome.retired_publication_id == before.publication_id
    assert outcome.replacement_publication_id == after.publication_id
    assert after.publication_id != before.publication_id
    assert after.commit_sha == before.commit_sha


def test_the_replacement_keeps_the_revisions_publication_generation(client, layout, config):
    """`AD-05`: retention order is the generation, so a repair that reissued one
    would move the revision in the prune queue for having been fixed."""
    sync(client, layout, config, only_model(config))
    before = manifest_of(layout, SHA_A)
    damage(layout, SHA_A)

    repair(client, layout, config)

    assert manifest_of(layout, SHA_A).publication_generation == before.publication_generation


def test_the_original_manifest_is_never_rewritten(client, layout, config):
    """`FS-06`: the original is the evidence of what was published."""
    sync(client, layout, config, only_model(config))
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    original_reference = read_reference(layout, repository.revision_ref(CommitSha(SHA_A)))
    original_path = repository.manifest(
        CommitSha(SHA_A), PublicationId(original_reference.publication_id)
    )
    before = original_path.read_bytes()
    damage(layout, SHA_A)

    repair(client, layout, config)

    assert original_path.read_bytes() == before


def test_the_replacement_manifest_copies_the_original_expectations_exactly(client, layout, config):
    """`docs/schemas.md` §3.5, and `AD-18` at the same time: every digest is
    identical to the original's *and* every one was read from disk this run."""
    sync(client, layout, config, only_model(config))
    before = manifest_of(layout, SHA_A)
    damage(layout, SHA_A)

    repair(client, layout, config)

    after = manifest_of(layout, SHA_A)
    assert [(e.path, e.size, e.sha256) for e in after.files] == [
        (e.path, e.size, e.sha256) for e in before.files
    ]
    assert all(entry.provenance.hashed for entry in after.files)
    assert all(entry.provenance.cache_root == "repair" for entry in after.files)
    assert all(entry.provenance.source == "repair_download" for entry in after.files)


def test_the_replacement_records_what_it_replaced(client, layout, config):
    sync(client, layout, config, only_model(config))
    before = manifest_of(layout, SHA_A)
    damage(layout, SHA_A)

    outcome = repair(client, layout, config, reason="zfs_checksum_error")

    after = manifest_of(layout, SHA_A)
    assert after.repair is not None
    assert after.repair.repair_of == before.publication_id
    assert after.repair.reason == "zfs_checksum_error"
    assert after.repair.transaction_id == outcome.transaction_id
    assert after.is_repair


def test_the_repaired_revision_verifies_clean(client, layout, config, config_path):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)

    repair(client, layout, config)

    result = invoke_api(config_path, ["verify", "--full"])
    assert result.exit_code == ExitCode.SUCCESS


def test_the_references_switch_to_the_replacement(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)

    outcome = repair(client, layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    revision_ref = read_reference(layout, repository.revision_ref(CommitSha(SHA_A)))
    current = read_reference(layout, repository.current_ref)
    assert revision_ref.publication_id == outcome.replacement_publication_id
    assert current.publication_id == outcome.replacement_publication_id


def test_a_repair_of_a_revision_that_is_not_current_leaves_current_alone(
    client, hub, layout, config
):
    sync(client, layout, config, only_model(config))
    hub.heads[MODEL.selector] = SHA_B
    sync(client, layout, config, only_model(config))
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert read_reference(layout, repository.current_ref).commit_sha == SHA_B
    damage(layout, SHA_A)

    outcome = repair(client, layout, config, commit_sha=SHA_A)

    current = read_reference(layout, repository.current_ref)
    assert current.commit_sha == SHA_B
    assert current.publication_id != outcome.replacement_publication_id
    switched = [
        checkpoint
        for checkpoint in read_journal(
            layout, layout.journal(_txn(outcome.transaction_id))
        ).journal.checkpoints
        if checkpoint.name == "current_ref_switched"
    ]
    assert switched[0].evidence["switched"] is False


def _txn(value: str) -> TransactionId:
    return TransactionId(value)


def test_the_retired_instance_stays_readable_for_its_grace_period(client, layout, config):
    """`AD-13`: an in-flight consumer copy that resolved the old reference has to
    be able to finish."""
    sync(client, layout, config, only_model(config))
    retired = instance_of(layout, SHA_A)
    damage(layout, SHA_A)

    outcome = repair(client, layout, config)

    assert retired.is_dir()
    assert (retired / "weights.bin").is_file()
    assert outcome.retired_publication_id in str(retired)


def test_the_retirement_record_names_the_grace_expiry(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)

    outcome = repair(client, layout, config, now=NOW)

    (pending,) = pending_cleanups(layout)
    assert pending.record.grace_expires_at == NOW + timedelta(hours=GRACE_HOURS)
    assert pending.record.cleanup.state == "pending"
    assert pending.record.reason == "checksum_error"
    assert outcome.grace_expires_at == pending.record.grace_expires_at
    assert str(layout.archive_relative(pending.path)) == outcome.retirement_record


def test_the_checkpoints_are_recorded_in_the_order_7_5_fixes(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)

    outcome = repair(client, layout, config)

    assert names(layout, outcome.transaction_id) == [
        "evidence_preserved",
        "isolated_cache_created",
        "isolated_download_completed",
        "verified_against_original_manifest",
        "staging_built",
        "replacement_tree_renamed",
        "replacement_manifest_published",
        "replacement_reverified",
        "revision_ref_switched",
        "current_ref_switched",
        "catalog_rebuilt",
        "retirement_record_written",
        "implicated_cache_revision_deleted",
        "isolated_cache_removed",
        "repair_committed",
    ]


def test_the_journal_stays_open_for_the_cleanup_that_follows(client, layout, config):
    """Checkpoints 16-18 belong to this transaction, and an open journal is the
    only durable record `recover` can find on its own."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)

    outcome = repair(client, layout, config)

    (journal,) = open_journals(layout)
    assert journal.journal.transaction_id == outcome.transaction_id
    assert journal.journal.state == "open"


def test_the_isolated_cache_is_removed_and_never_the_canonical_one(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)

    outcome = repair(client, layout, config)

    assert not (layout.repair_caches / outcome.transaction_id).exists()
    assert layout.hub_cache.is_dir()


def test_the_download_never_touches_the_canonical_cache(client, layout, config, monkeypatch):
    """`FS-14`'s single exception: the canonical cache may hold the very blob
    under suspicion, so a repair download must not be able to reuse it."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    seen: list[str] = []
    real = FakeHub.snapshot_download

    def recording(self, repo_id, **arguments):
        if not arguments.get("dry_run"):
            seen.append(arguments["cache_dir"])
        return real(self, repo_id, **arguments)

    monkeypatch.setattr(FakeHub, "snapshot_download", recording)
    outcome = repair(client, layout, config)

    assert seen
    assert all(outcome.transaction_id in where for where in seen)
    assert all(str(layout.hub_cache) != where for where in seen)


# --------------------------------------------------------------------------- #
# Checkpoint 4, the gate (`AD-13`)
# --------------------------------------------------------------------------- #


def test_a_download_that_does_not_match_the_original_manifest_is_refused(
    client, hub, layout, config
):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    # Upstream now serves different bytes at the same SHA — which cannot happen
    # honestly, and is exactly the case `AD-13` exists for.
    hub.revisions[SHA_A] = {**CONTENT, "config.json": b'{"model_type": "tampered"}'}
    shutil.rmtree(layout.hub_cache / f"models--{MODEL.id.replace('/', '--')}")
    before = manifest_of(layout, SHA_A)

    with pytest.raises(RetentionError) as caught:
        repair(client, layout, config)

    assert [problem.code for problem in caught.value.problems] == ["HFRET006"]
    assert caught.value.exit_code == ExitCode.RETENTION
    after = manifest_of(layout, SHA_A)
    assert after.publication_id == before.publication_id
    assert pending_cleanups(layout) == ()


def test_a_refused_repair_leaves_the_published_revision_exactly_as_it_was(
    client, hub, layout, config
):
    sync(client, layout, config, only_model(config))
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference_before = repository.revision_ref(CommitSha(SHA_A)).read_bytes()
    damage(layout, SHA_A)
    hub.revisions[SHA_A] = {**CONTENT, "config.json": b"tampered"}
    shutil.rmtree(layout.hub_cache / f"models--{MODEL.id.replace('/', '--')}")

    with pytest.raises(RetentionError):
        repair(client, layout, config)

    assert repository.revision_ref(CommitSha(SHA_A)).read_bytes() == reference_before


def test_a_download_missing_a_manifest_path_is_refused(client, hub, layout, config):
    sync(client, layout, config, only_model(config))
    hub.revisions[SHA_A] = {"config.json": CONTENT["config.json"]}
    shutil.rmtree(layout.hub_cache / f"models--{MODEL.id.replace('/', '--')}")

    with pytest.raises(RetentionError) as caught:
        repair(client, layout, config)

    assert [problem.code for problem in caught.value.problems] == ["HFRET006"]


# --------------------------------------------------------------------------- #
# The post-grace cleanup (§7.5 checkpoints 16-18)
# --------------------------------------------------------------------------- #


def plan(layout: ArchiveLayout, *, now: datetime | None = None):
    return plan_recovery(layout, stale_staging_age_hours=24, now=now)


def apply(layout: ArchiveLayout, config: ApplicationConfig, *, now: datetime | None = None):
    prepared = plan(layout, now=now)
    return apply_recovery(layout, prepared, envelope=envelope(config), started_at=datetime.now(UTC))


def remedy_for(prepared, operation: str) -> str:
    """The remedy proposed for the one journal of this operation.

    A crash inside a run leaves *two* open journals now (§7.6): the
    per-repository one that was mid-flight and the run journal wrapping it. Both
    are real and both get a remedy, so a test that asks about a publication has
    to say so rather than take whichever the directory listed first.
    """
    (entry,) = [item for item in prepared.remediations if item.operation == operation]
    return entry.remedy


def open_journal_for(layout: ArchiveLayout, operation: str):
    """The one open journal of this operation, for the same reason."""
    (found,) = [
        journal for journal in open_journals(layout) if journal.journal.operation == operation
    ]
    return found


def test_inside_the_grace_period_recovery_waits(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)

    prepared = plan(layout, now=NOW + timedelta(hours=1))

    assert not prepared.blocked
    assert prepared.remediations[0].remedy == "wait"
    assert prepared.actionable == ()


def test_a_waiting_repair_never_stops_another_command(client, layout, config):
    """An open repair journal is normal for a week; it must not read as damage."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)

    prepared = plan(layout, now=NOW + timedelta(hours=1))

    assert prepared.problems == ()
    assert prepared.as_payload()["blocked"] == 0


def test_past_the_grace_period_the_retired_instance_is_quarantined(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    outcome = repair(client, layout, config, now=NOW)
    retired = layout.root / manifest_of(layout, SHA_A).repair.repair_of_manifest  # type: ignore[union-attr]
    retired_tree = layout.published / str(
        read_reference(
            layout, RepositoryLayout(archive=layout, identity=MODEL).revision_ref(CommitSha(SHA_A))
        ).tree
    )
    assert retired_tree.is_dir()

    later = NOW + timedelta(hours=GRACE_HOURS + 1)
    _, applied = apply(layout, config, now=later)

    quarantine = layout.quarantine_for(_txn(outcome.transaction_id))
    assert quarantine.is_dir()
    assert (quarantine / "weights.bin").is_file(), "quarantined, never deleted"
    assert applied[0].remedy == "finish_repair_cleanup"
    assert not retired.is_file(), "the original manifest moved into audit/"


def test_the_cleanup_archives_the_original_manifest_byte_for_byte(client, layout, config):
    sync(client, layout, config, only_model(config))
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    original_reference = read_reference(layout, repository.revision_ref(CommitSha(SHA_A)))
    retired_id = PublicationId(original_reference.publication_id)
    original_bytes = repository.manifest(CommitSha(SHA_A), retired_id).read_bytes()
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)

    apply(layout, config, now=NOW + timedelta(hours=GRACE_HOURS + 1))

    archived = repository.retired_manifest(CommitSha(SHA_A), retired_id)
    assert archived.read_bytes() == original_bytes


def test_the_cleanup_marks_the_retirement_record_complete_and_closes_the_journal(
    client, layout, config
):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    outcome = repair(client, layout, config, now=NOW)

    apply(layout, config, now=NOW + timedelta(hours=GRACE_HOURS + 1))

    (record,) = [
        read_model(path, RepairRetirementRecord, error=RetentionError, code="HFRET009")
        for path in sorted(layout.repair_audit.rglob("*.retirement.json"))
    ]
    assert record.cleanup.state == "completed"
    assert record.cleanup.quarantine_path is not None
    assert pending_cleanups(layout) == ()
    journal = read_journal(layout, layout.journal(_txn(outcome.transaction_id))).journal
    assert journal.state == "committed"
    assert [checkpoint.name for checkpoint in journal.checkpoints][-3:] == [
        "retired_tree_quarantined",
        "retired_manifest_archived",
        "repair_cleanup_completed",
    ]


def test_the_cleanup_is_idempotent(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)
    later = NOW + timedelta(hours=GRACE_HOURS + 1)
    apply(layout, config, now=later)

    _, second = apply(layout, config, now=later)

    assert second == ()
    assert open_journals(layout) == ()


def test_a_due_cleanup_is_warned_about(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)

    assert cleanup_warnings(layout, now=NOW + timedelta(hours=1)) == []
    warnings = cleanup_warnings(layout, now=NOW + timedelta(hours=GRACE_HOURS + 1))
    assert [warning.code for warning in warnings] == ["HFWRN008"]
    assert due_cleanups(layout, now=NOW + timedelta(hours=GRACE_HOURS + 1))


def test_status_surfaces_the_due_cleanup(client, layout, config, config_path):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=datetime.now(UTC) - timedelta(hours=GRACE_HOURS + 1))

    with api_cli(config_path) as remote:
        result = remote.invoke(["status"])
    envelope_body = json.loads(result.stdout)

    assert [warning["code"] for warning in envelope_body["warnings"]] == ["HFWRN008"]
    assert envelope_body["exit_code"] == ExitCode.SUCCESS


def test_status_reports_what_quarantine_is_holding(client, layout, config, config_path):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)
    apply(layout, config, now=NOW + timedelta(hours=GRACE_HOURS + 1))

    with api_cli(config_path) as remote:
        result = remote.invoke(["status"])
    archive = json.loads(result.stdout)["data"]["archive"]

    assert archive["quarantined_bytes"] == sum(len(payload) for payload in CONTENT.values())


# --------------------------------------------------------------------------- #
# The `repair` command
# --------------------------------------------------------------------------- #


def test_the_repair_command_replaces_the_instance(client, layout, config, config_path, monkeypatch):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    monkeypatch.setattr("hfcache.services.commands.HubClient", _client_factory(client))

    result = invoke_api(config_path, ["repair", f"{MODEL.selector}@{SHA_A}"])

    assert result.exit_code == ExitCode.SUCCESS
    data = json.loads(result.stdout)["data"]
    assert data["commit_sha"] == SHA_A
    assert data["verified"] is True
    assert data["replacement_publication_id"] != data["retired_publication_id"]
    assert manifest_of(layout, SHA_A).publication_id == data["replacement_publication_id"]


def test_the_repair_command_reports_a_refused_download(  # noqa: PLR0913, PLR0917 - six fixtures
    client, hub, layout, config, config_path, monkeypatch
):
    sync(client, layout, config, only_model(config))
    hub.revisions[SHA_A] = {**CONTENT, "config.json": b"tampered"}
    shutil.rmtree(layout.hub_cache / f"models--{MODEL.id.replace('/', '--')}")
    monkeypatch.setattr("hfcache.services.commands.HubClient", _client_factory(client))

    result = invoke_api(config_path, ["repair", f"{MODEL.selector}@{SHA_A}"])

    assert result.exit_code == ExitCode.RETENTION
    assert [p["code"] for p in json.loads(result.stdout)["errors"]] == ["HFRET006"]


def test_the_repair_command_requires_a_full_sha(config_path):
    result = invoke_api(config_path, ["repair", MODEL.selector])

    assert result.exit_code == ExitCode.CONFIGURATION
    assert [p["code"] for p in json.loads(result.stdout)["errors"]] == ["HFARG001"]


def test_a_repair_discards_its_staging_when_it_commits(client, layout, config):
    """Decision 56, on the side where it matters more: a repair journal stays
    open for the whole retirement grace, so staging it left behind would report
    a committed repair as unfinished work for seven days."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)

    outcome = repair(client, layout, config)

    assert list(layout.staging.iterdir()) == []
    journal = read_journal(layout, layout.journal(_txn(outcome.transaction_id))).journal
    committed = next(c for c in journal.checkpoints if c.name == "repair_committed")
    assert committed.evidence["staging_absent"].startswith(".store/staging/")
    # And the journal still says nothing false about the filesystem, which is
    # what every `recover` in that window checks.
    assert not plan(layout, now=NOW).blocked


def test_the_repair_command_stops_on_a_journal_that_asked_for_an_operator(
    client, layout, config, config_path
):
    """`TX-07` applies to every mutating command, and repair is one. It re-reads
    the original manifest and the published instance to decide what the
    replacement must be, and both are what an unfinished transaction is still in
    the middle of changing."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint="0" * 64,
        repository_id=MODEL.id,
        repository_type=MODEL.type,
    ).needs_operator("HFTXN004", "two equally valid resolutions")

    result = invoke_api(config_path, ["repair", f"{MODEL.selector}@{SHA_A}"])

    assert result.exit_code == ExitCode.SAFETY
    assert [p["code"] for p in json.loads(result.stdout)["errors"]] == ["HFTXN004"]
    assert list(layout.repair_caches.iterdir()) == [], "no isolated download was started"


def test_the_repair_command_takes_the_exclusive_lock(client, layout, config, config_path):
    sync(client, layout, config, only_model(config))
    with exclusive_lock(lock_path(), command="sync", wait_seconds=0):
        result = invoke_api(config_path, ["repair", f"{MODEL.selector}@{SHA_A}"])

    assert result.exit_code == ExitCode.SAFETY
    assert [p["code"] for p in json.loads(result.stdout)["errors"]] == ["HFMNT010"]


def _client_factory(client: HubClient):
    class Factory:
        @staticmethod
        def of(*_arguments: Any, **_keywords: Any) -> HubClient:
            return client

    return Factory


# --------------------------------------------------------------------------- #
# Rolling a publication forward (§7.3 crash matrix)
# --------------------------------------------------------------------------- #


class CrashError(RuntimeError):
    """Kills the process the way a power loss would: no handler, no cleanup.

    Raising an `HfcacheError` would not do. Every mutating command catches those
    and closes its journal as `failed`, which is correct behaviour and leaves
    nothing for recovery to find. Only an exception nothing handles reproduces
    the state `TX-01` exists for: a journal that stops mid-sequence because the
    writer stopped existing.
    """


def crash_at(monkeypatch: pytest.MonkeyPatch, module, name: str, *, on_call: int = 1):
    """Make the nth call to `module.name` kill the run, then restore it."""
    real = getattr(module, name)
    calls: list[int] = []

    def failing(*arguments: Any, **keywords: Any):
        calls.append(1)
        if len(calls) == on_call:
            raise CrashError
        return real(*arguments, **keywords)

    monkeypatch.setattr(module, name, failing)
    return lambda: monkeypatch.setattr(module, name, real)


def test_a_publication_interrupted_after_the_rename_rolls_forward(
    client, layout, config, monkeypatch
):
    """§7.3, "After 5, before 6": the staged manifest survives, so the tree can
    be validated and the publication continued."""
    restore = crash_at(monkeypatch, sync_module, "write_model", on_call=2)
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()

    prepared = plan(layout)
    assert remedy_for(prepared, "publication") == "complete_publication"

    apply(layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.revision_ref(CommitSha(SHA_A)))
    assert reference.commit_sha == SHA_A
    assert repository.current_ref.is_file()
    assert read_reference(layout, repository.current_ref).commit_sha == SHA_A
    assert open_journals(layout) == ()


def crash_at_checkpoint(monkeypatch: pytest.MonkeyPatch, operation: str, *, after: int):
    """Kill a transaction once it has recorded its nth checkpoint.

    Some §7 boundaries have no function call between two checkpoints to hang a
    `crash_at` on — §7.4's commit point is `catalog_published` immediately
    followed by `prune_logically_committed` — so the only way to stop between
    them is to count the checkpoints themselves. The kill happens *after* the
    real append, so the journal a crash leaves holds exactly `after` of them.
    """
    real = Transaction.checkpoint
    seen = {"count": 0}

    def failing(self, name: str, **evidence: Any):
        recorded = real(self, name, **evidence)
        if self.journal.operation == operation:
            seen["count"] += 1
            if seen["count"] == after:
                raise CrashError
        return recorded

    monkeypatch.setattr(Transaction, "checkpoint", failing)
    return lambda: monkeypatch.setattr(Transaction, "checkpoint", real)


def test_a_publication_interrupted_before_the_current_ref_rolls_forward(
    client, hub, layout, config, monkeypatch
):
    """§7.3, "After 7, before 8": retained and discoverable, but not yet current.

    the development failure-injection matrix's `revision_ref_published` row. The condition
    function has its own test
    (`test_an_older_revision_rolled_forward_does_not_become_current`); this is the
    boundary reached by an actual crash, which is what the matrix asks for.
    """
    sync(client, layout, config, only_model(config))
    hub.heads[MODEL.selector] = SHA_B
    restore = crash_at(monkeypatch, sync_module, "publish_current_reference")
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    # The new revision is retained; the previous one is still what consumers get.
    assert read_reference(layout, repository.revision_ref(CommitSha(SHA_B))).commit_sha == SHA_B
    assert read_reference(layout, repository.current_ref).commit_sha == SHA_A
    prepared = plan(layout)
    assert remedy_for(prepared, "publication") == "complete_publication"

    apply(layout, config)

    assert read_reference(layout, repository.current_ref).commit_sha == SHA_B
    assert open_journals(layout) == ()


def test_a_publication_interrupted_before_the_catalog_rolls_forward(
    client, layout, config, monkeypatch
):
    """§7.3, "After 8, before 9": current, with a stale catalog.

    The catalog is derived and always reconstructible (`FS-16`), so the whole
    resolution is to rebuild it.
    """
    restore = crash_at(monkeypatch, sync_module, "publish_catalog")
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert read_reference(layout, repository.current_ref).commit_sha == SHA_A
    prepared = plan(layout)
    assert remedy_for(prepared, "publication") == "complete_publication"

    apply(layout, config)

    catalog = layout.catalog / "repositories.json"
    assert catalog.is_file()
    assert SHA_A in catalog.read_text(encoding="utf-8")
    assert open_journals(layout) == ()


def test_a_prune_interrupted_at_its_commit_point_rolls_back(
    client, hub, layout, config, monkeypatch
):
    """§7.4's last rollback-able state: checkpoint 6 recorded, 7 not.

    The catalog already names five revisions, but `prune_logically_committed` is
    absent — so the archive has not decided, and `TX-06` says put the sixth back.
    This is the boundary immediately before the commit point, and it is the one
    row of §7.4 that neither of the other two prune crash tests reaches: they
    stop during checkpoint 6 and during checkpoint 8 respectively.
    """
    restore = crash_at_checkpoint(monkeypatch, "prune", after=6)
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()

    journal = next(
        read_journal(layout, path).journal
        for path in sorted(layout.transactions.glob("*.json"))
        if read_journal(layout, path).journal.operation == "prune"
    )
    assert [checkpoint.name for checkpoint in journal.checkpoints][-1] == "catalog_published"
    assert "prune_logically_committed" not in [c.name for c in journal.checkpoints]
    prepared = plan(layout)
    assert remedy_for(prepared, "prune") == "rollback_prune"

    apply(layout, config)

    assert len(retained_references(layout, MODEL)) == 6, "the sixth came back"
    assert open_journals(layout) == ()


def test_a_publication_interrupted_before_the_reference_rolls_forward(
    client, layout, config, monkeypatch
):
    """§7.3, "After 6, before 7": tree and manifest published, no reference."""
    restore = crash_at(monkeypatch, sync_module, "publish_revision_reference")
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()

    prepared = plan(layout)
    assert remedy_for(prepared, "publication") == "complete_publication"

    apply(layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).commit_sha == SHA_A
    assert read_reference(layout, repository.current_ref).commit_sha == SHA_A


def test_a_tree_that_cannot_be_validated_is_quarantined_not_published(
    client, layout, config, monkeypatch
):
    """§7.3's caveat: never publish an unvalidated tree."""
    restore = crash_at(monkeypatch, sync_module, "write_model", on_call=2)
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()
    # The staged manifest is what makes validation possible. Corrupted rather
    # than removed, because removing it would make the journal's own evidence
    # contradict the filesystem, which is `HFTXN003` and stops the machine — a
    # different condition with a different answer (see the test below).
    for staged in layout.staging.rglob("manifest.json"):
        staged.write_text("{ not json", encoding="utf-8")

    prepared = plan(layout)
    assert remedy_for(prepared, "publication") == "quarantine_tree"

    apply(layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert not repository.revision_ref(CommitSha(SHA_A)).exists()
    assert list(layout.quarantine.iterdir()), "the tree is preserved as evidence"


def test_a_staged_manifest_that_vanished_is_quarantined_not_published(
    client, layout, config, monkeypatch
):
    """A vanished staged manifest and a corrupt one have the same answer: the
    tree cannot be validated, so §7.3 preserves it as evidence.

    It is not `HFTXN003`. Checkpoint 4 records the pending manifest without a
    `_path` suffix (decision 56), because checkpoint 10 discards the staging area
    — so its absence never means the journal is lying about what happened.
    """
    restore = crash_at(monkeypatch, sync_module, "write_model", on_call=2)
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()
    for staged in layout.staging.rglob("manifest.json"):
        staged.unlink()

    prepared = plan(layout)

    assert not prepared.blocked
    assert remedy_for(prepared, "publication") == "quarantine_tree"


def test_a_journal_that_contradicts_the_filesystem_stops_the_machine(
    client, layout, config, monkeypatch
):
    """`TX-03`: checkpoint 5 said the published tree was durable, and it is gone.
    A journal that contradicts the filesystem is `HFTXN003` and an operator's
    decision, not a state recovery may resolve on its own (§7.9)."""
    restore = crash_at(monkeypatch, sync_module, "publish_revision_reference")
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()
    instance = next(iter(layout.repos.rglob("config.json"))).parent
    shutil.rmtree(instance)

    prepared = plan(layout)

    assert prepared.blocked
    assert [problem.code for problem in prepared.problems] == ["HFTXN003"]


def test_a_published_tree_that_does_not_match_its_manifest_is_never_referenced(
    client, layout, config, monkeypatch
):
    restore = crash_at(monkeypatch, sync_module, "write_model", on_call=2)
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()
    published = next(iter(layout.repos.rglob("config.json")))
    published.unlink()

    with pytest.raises(Exception, match="does not match its manifest"):
        apply(layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert not repository.revision_ref(CommitSha(SHA_A)).exists()


# --------------------------------------------------------------------------- #
# Rolling a prune back and forward (§7.4)
# --------------------------------------------------------------------------- #


def six_revisions(client, hub, layout, config) -> None:
    """Publish six unique revisions of the model, which is what triggers a prune."""
    for index in range(6):
        sha = f"{index + 1}" * 40
        hub.revisions[sha] = {**CONTENT, "config.json": f'{{"n": {index}}}'.encode()}
        hub.heads[MODEL.selector] = sha
        sync(client, layout, config, only_model(config))


def test_a_prune_interrupted_before_its_commit_point_rolls_back(
    client, hub, layout, config, monkeypatch
):
    """§7.4: over-retention is reportable and a deletion is not reversible."""
    restore = crash_at(monkeypatch, retention_module, "publish_catalog")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()

    assert len(retained_references(layout, MODEL)) == 5, "the sixth was tombstoned"
    prepared = plan(layout)
    assert remedy_for(prepared, "prune") == "rollback_prune"

    apply(layout, config)

    assert len(retained_references(layout, MODEL)) == 6
    assert open_journals(layout) == ()


def test_a_prune_interrupted_after_its_commit_point_rolls_forward(
    client, hub, layout, config, monkeypatch
):
    """§7.4: at or after checkpoint 7 the five revisions stand; only cleanup runs."""
    # Checkpoint 8 is the first act after the commit point, so a crash in the
    # audit write leaves the transaction on the far side of it.
    restore = crash_at(monkeypatch, retention_module, "write_model")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()

    assert len(retained_references(layout, MODEL)) == 5
    assert list(layout.trash.iterdir()), "the tombstone is still there"
    prepared = plan(layout)
    assert remedy_for(prepared, "prune") == "complete_prune"

    apply(layout, config)

    assert len(retained_references(layout, MODEL)) == 5, "never republished"
    assert list(layout.trash.iterdir()) == []
    assert list(layout.pruned_audit.rglob("*.manifest.json")), "the evidence is archived"
    assert open_journals(layout) == ()


def test_a_prune_interrupted_before_its_containers_are_removed_is_completed(
    client, hub, layout, config, monkeypatch
):
    """§7.4 checkpoint 10 — the boundary `RET-008` added.

    Past the commit point, so the five consumer-visible revisions stand and are
    never republished; what is left outstanding is the pair of emptied `<sha>/`
    containers, and finishing them is exactly the post-commit cleanup this remedy
    is for.
    """
    restore = crash_at(monkeypatch, retention_module, "remove_empty_containers")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    pruned = CommitSha("1" * 40)
    # This is the state the crash leaves, and the state RET-008 exists to end:
    # the instance is gone, the container that held it is not.
    assert repository.revision(pruned).is_dir()
    assert not any(repository.revision(pruned).iterdir()), "emptied, not removed"
    prepared = plan(layout)
    assert remedy_for(prepared, "prune") == "complete_prune"

    apply(layout, config)

    assert not repository.revision(pruned).exists()
    assert not repository.revision_manifests(pruned).exists()
    assert len(retained_references(layout, MODEL)) == 5, "never republished"
    assert open_journals(layout) == ()


def test_completing_a_prune_removes_containers_a_second_time_without_error(
    client, hub, layout, config, monkeypatch
):
    """The same remedy runs after a prune that already removed them (`TX-04`)."""
    restore = crash_at(monkeypatch, retention_module, "write_model")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()

    apply(layout, config)
    apply(layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert not repository.revision(CommitSha("1" * 40)).exists()
    assert len(retained_references(layout, MODEL)) == 5


# --------------------------------------------------------------------------- #
# Finishing an interrupted repair (§7.5, the crash between 9 and 10)
# --------------------------------------------------------------------------- #


def test_a_repair_interrupted_between_the_two_ref_switches_is_completed(
    client, layout, config, monkeypatch
):
    """§7.5's interesting case. The per-SHA reference names the new instance and
    `current.json` still names the old one; both trees exist, so `FS-10` holds
    and no consumer sees a dangling reference."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    restore = crash_at(monkeypatch, repair_module, "publish_current_reference")
    with pytest.raises(CrashError):
        repair(client, layout, config)
    restore()

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    switched = read_reference(layout, repository.revision_ref(CommitSha(SHA_A)))
    current = read_reference(layout, repository.current_ref)
    assert switched.publication_id != current.publication_id
    assert (layout.published / str(current.tree)).is_dir(), "the old tree is still there"

    prepared = plan(layout)
    assert prepared.remediations[0].remedy == "complete_repair"

    apply(layout, config)

    assert read_reference(layout, repository.current_ref).publication_id == switched.publication_id
    assert read_journal(layout, layout.journal(_txn(prepared.remediations[0].transaction_id)))
    assert open_journals(layout) == ()


def test_an_interrupted_repair_whose_replacement_is_damaged_switches_nothing(
    client, layout, config, monkeypatch
):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    restore = crash_at(monkeypatch, repair_module, "publish_revision_reference")
    with pytest.raises(CrashError):
        repair(client, layout, config)
    restore()
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    before = read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).publication_id
    replacement = next(
        path for path in repository.revision(CommitSha(SHA_A)).iterdir() if path.name != before
    )
    (replacement / "config.json").unlink()

    with pytest.raises(Exception, match="fails verification"):
        apply(layout, config)

    assert (
        read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).publication_id == before
    )


def test_a_repair_interrupted_before_the_rename_changes_nothing_and_rolls_back(
    client, layout, config, monkeypatch
):
    """Nothing published changed: the revision is still the instance it was, and
    the isolated download and staging are the only artifacts. That is §7.3's
    "before 5" shape, and it takes §7.3's answer."""
    sync(client, layout, config, only_model(config))
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    before = read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).publication_id
    damage(layout, SHA_A)
    restore = crash_at(monkeypatch, repair_module, "promote_staging")
    with pytest.raises(CrashError):
        repair(client, layout, config)
    restore()

    prepared = plan(layout)
    assert prepared.remediations[0].remedy == "quarantine_staging"

    apply(layout, config)

    assert (
        read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).publication_id == before
    )
    assert list(layout.quarantine.iterdir()), "the staged replacement is preserved"


def test_a_repair_whose_cleanup_already_ran_only_needs_its_journal_closed(client, layout, config):
    """A previous cleanup got as far as marking the record complete and then
    stopped; there is nothing left to move."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    outcome = repair(client, layout, config, now=NOW)
    (pending,) = pending_cleanups(layout)
    completed = pending.record.model_dump(mode="json")
    completed["cleanup"] = {
        "completed_at": NOW.isoformat().replace("+00:00", "Z"),
        "quarantine_path": ".store/quarantine/" + outcome.transaction_id,
        "state": "completed",
    }
    pending.path.write_text(json.dumps(completed), encoding="utf-8")

    prepared = plan(layout, now=NOW + timedelta(hours=GRACE_HOURS + 1))
    assert prepared.remediations[0].remedy == "close_journal"

    apply(layout, config, now=NOW + timedelta(hours=GRACE_HOURS + 1))

    assert read_journal(layout, layout.journal(_txn(outcome.transaction_id))).journal.state == (
        "committed"
    )


def test_a_retirement_record_that_will_not_load_blocks_rather_than_closing(
    client, hub, layout, config
):
    """`REP-001`: absent and unreadable are not the same answer.

    `pending_cleanups` skips a record it cannot parse, deliberately, so one
    damaged record does not hide the others. A caller that turns "no pending
    cleanup" into a *decision* must not read that skip as "the cleanup is done" —
    which is what `_repair_remediation` did. It closed the repair journal, and
    that journal is the only thing making the post-grace cleanup reachable from
    `recover`, while `status` went on citing `recover --apply` as the remedy
    (`HFWRN008`). The retired instance was stranded with nothing able to finish
    it. Found by `OPS-003`'s drill on a throwaway archive.
    """
    sync(client, layout, config, only_model(config))
    repair(client, layout, config, commit_sha=SHA_A)
    (record,) = pending_cleanups(layout)
    record.path.write_text("{ not a retirement record", encoding="utf-8")

    prepared = plan(layout)

    entry = next(item for item in prepared.remediations if item.operation == "repair")
    assert entry.remedy == recovery_module.BLOCKED, "an unreadable record must stop, not close"
    assert [problem.code for problem in entry.problems] == ["HFTXN003"]
    # And applying refuses the whole plan rather than performing the rest of it.
    with pytest.raises(SafetyError):
        apply(layout, config)


def test_a_repair_whose_cleanup_really_did_complete_still_closes(client, layout, config):
    """The other half of `REP-001`: a *readable* record marked complete is the
    case `close_journal` is actually for, and it still works."""
    sync(client, layout, config, only_model(config))
    repair(client, layout, config, commit_sha=SHA_A)
    (pending,) = pending_cleanups(layout)
    completed = pending.record.model_copy(
        update={
            "cleanup": RepairCleanup(
                completed_at=datetime.now(UTC),
                quarantine_path=".store/quarantine/x",
                state="completed",
            )
        }
    )
    pending.path.write_text(completed.model_dump_json(), encoding="utf-8")

    prepared = plan(layout)

    entry = next(item for item in prepared.remediations if item.operation == "repair")
    assert entry.remedy == "close_journal"


def test_a_retirement_record_that_will_not_load_never_hides_the_others(client, layout, config):
    """One unreadable record must not make a scheduling question unanswerable."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)
    (layout.repair_audit / "stray.retirement.json").write_text("{ not json", encoding="utf-8")

    assert len(pending_cleanups(layout)) == 1


def test_a_repair_with_no_recorded_findings_still_runs(client, layout, config):
    """docs/cli.md verification contract lists a scrub error and a restore as reasons to repair, and
    neither requires this archive to have verified the instance first."""
    sync(client, layout, config, only_model(config))
    assert not layout.verification_catalog.exists()

    outcome = repair(client, layout, config, reason="restored_from_snapshot")

    (pending,) = pending_cleanups(layout)
    assert pending.record.evidence == ()
    assert outcome.replacement_publication_id


def test_a_cleanup_that_cannot_move_the_retired_tree_is_hfret009(client, layout, config):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)
    layout.quarantine.chmod(0o500)
    try:
        with pytest.raises(RetentionError) as caught:
            apply(layout, config, now=NOW + timedelta(hours=GRACE_HOURS + 1))
    finally:
        layout.quarantine.chmod(0o700)

    assert [problem.code for problem in caught.value.problems] == ["HFRET009"]


def test_a_rollback_that_cannot_restore_the_tree_is_hfret005(
    client, hub, layout, config, monkeypatch
):
    """§7.4's third row: a rollback that itself fails stops and preserves."""
    restore = crash_at(monkeypatch, retention_module, "publish_catalog")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()
    oldest = RepositoryLayout(archive=layout, identity=MODEL).revision(CommitSha("1" * 40))
    oldest.chmod(0o500)
    try:
        with pytest.raises(RetentionError) as caught:
            apply(layout, config)
    finally:
        oldest.chmod(0o2750)

    assert [problem.code for problem in caught.value.problems] == ["HFRET005"]


def test_a_prune_interrupted_before_its_audit_copy_still_archives_the_manifest(
    client, hub, layout, config, monkeypatch
):
    """Checkpoint 8 writes two files; a crash in the first leaves neither, and
    rolling forward writes both."""
    restore = crash_at(monkeypatch, retention_module, "atomic_write_bytes")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()
    assert not list(layout.pruned_audit.rglob("*.manifest.json"))

    apply(layout, config)

    assert list(layout.pruned_audit.rglob("*.manifest.json"))
    assert list(layout.pruned_audit.rglob("*.prune.json"))
    assert list(layout.trash.iterdir()) == []


def test_a_tree_that_cannot_be_quarantined_is_hfret010(client, layout, config, monkeypatch):
    restore = crash_at(monkeypatch, sync_module, "write_model", on_call=2)
    with pytest.raises(CrashError):
        sync(client, layout, config, only_model(config))
    restore()
    for staged in layout.staging.rglob("manifest.json"):
        staged.write_text("{ not json", encoding="utf-8")
    layout.quarantine.chmod(0o500)
    try:
        with pytest.raises(RetentionError) as caught:
            apply(layout, config)
    finally:
        layout.quarantine.chmod(0o700)

    assert [problem.code for problem in caught.value.problems] == ["HFRET010"]


def test_an_operation_with_no_documented_resolution_is_an_operators_decision(layout, config):
    """A recovery that itself crashed: §7.7 gives no resolution for one, and
    recovery says so rather than guessing (§7.9)."""
    open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="recovery",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=config.fingerprint(),
    ).checkpoint("close_journal", resolved_transaction_id=new_transaction_id())

    prepared = plan(layout)

    assert prepared.blocked
    assert [problem.code for problem in prepared.problems] == ["HFTXN004"]


def test_a_run_journal_a_crash_left_open_is_closed_and_nothing_else(layout, config):
    """§7.6: the run journal correlates the per-repository journals and owns no
    filesystem state, so there is nothing to roll forward — whatever it got to."""
    open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="sync",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=config.fingerprint(),
    ).checkpoint("run_started", run_id=new_run_id())

    prepared = plan(layout)

    assert not prepared.blocked
    assert remedy_for(prepared, "sync") == "close_journal"

    apply(layout, config)

    assert open_journals(layout) == ()


def test_an_interrupted_repair_whose_manifest_will_not_load_stops_the_machine(
    client, layout, config, monkeypatch
):
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    restore = crash_at(monkeypatch, repair_module, "publish_revision_reference")
    with pytest.raises(CrashError):
        repair(client, layout, config)
    restore()
    for staged in layout.staging.rglob("manifest.json"):
        staged.write_text("{ not json", encoding="utf-8")
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    retained = read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).publication_id
    for path in repository.revision_manifests(CommitSha(SHA_A)).glob("*.json"):
        if path.stem != retained:
            path.write_text("{ not json", encoding="utf-8")

    with pytest.raises(Exception, match="published no replacement manifest"):
        apply(layout, config)

    assert read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).publication_id == (
        retained
    )


def test_two_repairs_are_each_matched_to_their_own_retirement_record(client, hub, layout, config):
    """`_pending_for` has to pick the record its own transaction wrote."""
    sync(client, layout, config, only_model(config))
    hub.heads[MODEL.selector] = SHA_B
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    damage(layout, SHA_B)

    first = repair(client, layout, config, commit_sha=SHA_A, now=NOW)
    second = repair(client, layout, config, commit_sha=SHA_B, now=NOW)

    prepared = plan(layout, now=NOW + timedelta(hours=GRACE_HOURS + 1))
    assert {entry.transaction_id for entry in prepared.remediations} == {
        first.transaction_id,
        second.transaction_id,
    }
    assert {entry.remedy for entry in prepared.remediations} == {"finish_repair_cleanup"}

    apply(layout, config, now=NOW + timedelta(hours=GRACE_HOURS + 1))

    assert pending_cleanups(layout) == ()
    assert len(list(layout.quarantine.iterdir())) == 2


# --------------------------------------------------------------------------- #
# Idempotence (`TX-04`)
# --------------------------------------------------------------------------- #


def test_rolling_a_prune_back_twice_is_the_same_as_once(client, hub, layout, config, monkeypatch):
    restore = crash_at(monkeypatch, retention_module, "publish_catalog")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()
    identifier = _txn(open_journal_for(layout, "prune").journal.transaction_id)

    recovery_module._rollback_prune(layout, identifier)
    recovery_module._rollback_prune(layout, identifier)

    assert len(retained_references(layout, MODEL)) == 6


def test_completing_a_prune_twice_is_the_same_as_once(client, hub, layout, config, monkeypatch):
    restore = crash_at(monkeypatch, retention_module, "write_model")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()
    identifier = _txn(open_journal_for(layout, "prune").journal.transaction_id)

    recovery_module._complete_prune(layout, identifier)
    recovery_module._complete_prune(layout, identifier)

    assert len(retained_references(layout, MODEL)) == 5
    assert list(layout.trash.iterdir()) == []
    assert len(list(layout.pruned_audit.rglob("*.manifest.json"))) == 1


def test_a_prune_that_crashed_before_the_tombstone_rolls_back_with_no_trash(
    client, hub, layout, config, monkeypatch
):
    """A rollback from checkpoint 2 finds the tree still published and does
    nothing to it; cache deletion having happened is harmless (`§7.4`)."""
    restore = crash_at(monkeypatch, retention_module, "delete_cache_revision")
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()
    assert len(retained_references(layout, MODEL)) == 6

    apply(layout, config)

    assert len(retained_references(layout, MODEL)) == 6
    assert list(layout.trash.iterdir()) == []


def test_a_prune_whose_audit_records_landed_only_needs_its_trash_removed(
    client, hub, layout, config, monkeypatch
):
    # The fourth `fsync_directory` in `apply_prune` is the one after the audit
    # records, so a crash there leaves checkpoint 7 recorded and both files
    # written — the case where roll-forward has only the tombstone left to move.
    restore = crash_at(monkeypatch, retention_module, "fsync_directory", on_call=4)
    with pytest.raises(CrashError):
        six_revisions(client, hub, layout, config)
    restore()
    assert list(layout.pruned_audit.rglob("*.prune.json"))

    apply(layout, config)

    assert list(layout.trash.iterdir()) == []
    assert len(list(layout.pruned_audit.rglob("*.prune.json"))) == 1


def test_a_move_that_already_happened_is_a_no_op_rather_than_an_error(tmp_path):
    """`TX-04`: the honest way to make a rename idempotent is to notice the
    source is already gone, not to re-create it."""
    destination = tmp_path / "moved" / "tree"
    source = tmp_path / "tree"
    source.mkdir()
    (source / "file").write_text("evidence", encoding="utf-8")

    repair_module._rename_once(source, destination, mode=0o700)
    repair_module._rename_once(source, destination, mode=0o700)

    assert (destination / "file").read_text(encoding="utf-8") == "evidence"
    assert not source.exists()


def test_a_second_cleanup_of_the_same_transaction_is_refused_by_its_journal(client, layout, config):
    """The renames are idempotent; recording them twice is not a state any valid
    execution produces, and `HFTXN002` says so."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    repair(client, layout, config, now=NOW)
    apply(layout, config, now=NOW + timedelta(hours=GRACE_HOURS + 1))
    (record,) = sorted(layout.repair_audit.rglob("*.retirement.json"))
    stored = read_model(record, RepairRetirementRecord, error=RetentionError, code="HFRET009")
    identifier = _txn(stored.transaction_id)

    with pytest.raises(SafetyError) as caught:
        finish_cleanup(
            layout,
            Transaction(layout=layout, file=read_journal(layout, layout.journal(identifier))),
            repair_module.PendingCleanup(record=stored, path=record),
        )

    assert [problem.code for problem in caught.value.problems] == ["HFTXN002"]


def test_an_older_revision_rolled_forward_does_not_become_current(client, hub, layout, config):
    """§7.3 row 4's condition, on its own: retained and discoverable without
    becoming what consumers are pointed at."""
    sync(client, layout, config, only_model(config))
    hub.heads[MODEL.selector] = SHA_B
    sync(client, layout, config, only_model(config))
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    older = read_reference(layout, repository.revision_ref(CommitSha(SHA_A)))
    current_before = read_reference(layout, repository.current_ref).commit_sha

    assert recovery_module.publish_current_if_newest(layout, MODEL, older) is False

    assert read_reference(layout, repository.current_ref).commit_sha == current_before


def test_a_repair_of_a_non_current_revision_completes_without_moving_current(
    client, hub, layout, config, monkeypatch
):
    sync(client, layout, config, only_model(config))
    hub.heads[MODEL.selector] = SHA_B
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    restore = crash_at(monkeypatch, repair_module, "publish_catalog")
    with pytest.raises(CrashError):
        repair(client, layout, config, commit_sha=SHA_A)
    restore()

    apply(layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert read_reference(layout, repository.current_ref).commit_sha == SHA_B


def test_the_repair_records_the_findings_it_is_answering(client, layout, config, config_path):
    """docs/cli.md verification contract: the mismatch report is preserved as evidence, read
    from the catalog rather than by re-reading bytes that are unstable."""
    sync(client, layout, config, only_model(config))
    damage(layout, SHA_A)
    assert invoke_api(config_path, ["verify", "--full"]).exit_code == ExitCode.INTEGRITY

    repair(client, layout, config)

    (pending,) = pending_cleanups(layout)
    assert pending.record.evidence == ("digest_mismatch:config.json",)


def test_a_replacement_lost_between_the_rename_and_the_re_read_switches_nothing(
    client, layout, config, monkeypatch
):
    """Checkpoint 8 is the second gate: a reference only ever switches to an
    instance verified where it now lives."""
    sync(client, layout, config, only_model(config))
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    before = read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).publication_id
    damage(layout, SHA_A)
    real = repair_module.promote_staging

    def losing(layout_argument, staging, destination):
        real(layout_argument, staging, destination)
        (destination / "config.json").unlink()

    monkeypatch.setattr(repair_module, "promote_staging", losing)

    with pytest.raises(RetentionError) as caught:
        repair(client, layout, config)

    assert [problem.code for problem in caught.value.problems] == ["HFRET007"]
    assert (
        read_reference(layout, repository.revision_ref(CommitSha(SHA_A))).publication_id == before
    )
