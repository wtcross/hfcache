"""Explicit release of proven redundant quarantine evidence (`FS-19`, `TX-04`).

Fixtures pass abandoned publications through real recovery, so deletion is
authorized by the durable history the deployed command actually writes.
"""

import fcntl
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import hfcache.quarantine as quarantine_module
from hfcache.archive import initialize_archive
from hfcache.errors import ExitCode, RetentionError
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    TransactionId,
    new_run_id,
    new_transaction_id,
)
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import (
    create_staging,
    publish_current_reference,
    publish_revision_reference,
)
from hfcache.quarantine import apply_quarantine_cleanup, plan_quarantine_cleanup
from hfcache.recovery import apply_recovery, plan_recovery, reconcile_storage
from hfcache.transactions import CHECKPOINTS, open_transaction, read_journal
from tests.api_cli import api_cli
from tests.fixtures import examples

NOW = datetime.now(UTC)
MODEL = RepositoryIdentity.of("model", examples.REPOSITORY_ID)


@pytest.fixture
def layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ArchiveLayout:
    root = tmp_path / "archive"
    root.mkdir(mode=0o750)
    table = tmp_path / "mountinfo"
    table.write_text(
        f"457 47 0:68 / {root.resolve()} rw - nfs4 server:/archive rw\n", encoding="utf-8"
    )
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", table)
    monkeypatch.setattr("hfcache.locking.LOCK_DIRECTORY", tmp_path / "run")
    built = ArchiveLayout(root=root)
    initialize_archive(built, archive_id=examples.ARCHIVE_ID)
    return built


@pytest.fixture
def config_file(layout: ArchiveLayout, tmp_path: Path) -> Path:
    config = tmp_path / "config.toml"
    config.write_text(
        f"""schema_version = 1
[storage]
archive_root = "{layout.root}"
archive_id = "{examples.ARCHIVE_ID}"
minimum_free_space_gib = 0
minimum_free_space_percent = 0
[sync]
lock_wait_seconds = 0
""",
        encoding="utf-8",
    )
    return config


def invoke(config: Path, *arguments: str):
    with api_cli(config) as remote:
        return remote.invoke(["quarantine", *arguments])


def begin(layout: ArchiveLayout, *, publication_id: str | None = examples.REPLACEMENT):
    return open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="publication",
        run_id=new_run_id(),
        archive_id=examples.ARCHIVE_ID,
        config_fingerprint=examples.FINGERPRINT,
        repository_id=MODEL.id,
        repository_type=MODEL.type,
        commit_sha=examples.OTHER_SHA,
        publication_id=publication_id,
    )


def abandoned(
    layout: ArchiveLayout,
    files: dict[str, bytes] | None = None,
    *,
    publication_id: str | None = examples.REPLACEMENT,
    last_checkpoint: str = "staging_created",
) -> TransactionId:
    transaction = begin(layout, publication_id=publication_id)
    identifier = TransactionId(transaction.journal.transaction_id)
    staging = create_staging(layout, identifier)
    for relative, content in (files or {}).items():
        path = staging.tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    transaction.checkpoint(
        "staging_created", staging_path=str(layout.archive_relative(staging.directory))
    )
    if last_checkpoint != "staging_created":
        transaction.checkpoint(
            "download_completed",
            commit_sha=examples.OTHER_SHA,
            downloaded_bytes=sum(map(len, (files or {}).values())),
        )
    if last_checkpoint == "content_hashed":
        transaction.checkpoint(
            "content_hashed",
            hashed_objects=len(files or {}),
            hashed_bytes=sum(map(len, (files or {}).values())),
            reused_digests=0,
        )
    old = (NOW - timedelta(hours=48)).timestamp()
    os.utime(staging.directory, (old, old))
    recovery = plan_recovery(layout, stale_staging_age_hours=24, now=NOW)
    assert len(recovery.actionable) == 1
    assert recovery.actionable[0].remedy == "quarantine_staging"
    apply_recovery(
        layout,
        recovery,
        envelope={
            "application_version": "0.1.0",
            "archive_id": examples.ARCHIVE_ID,
            "config_fingerprint": examples.FINGERPRINT,
            "hostname": "writer",
            "huggingface_hub_version": "1.24.0",
            "invocation_mode": "interactive",
            "python_version": "3.14.6",
        },
        started_at=NOW,
    )
    return identifier


def publish_current(layout: ArchiveLayout, files: dict[str, bytes]) -> RepositoryLayout:
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = examples.reference()
    commit = CommitSha(reference.commit_sha)
    publication = PublicationId(reference.publication_id)
    tree = repository.instance(commit, publication)
    tree.mkdir(parents=True)
    entries = []
    for relative, content in sorted(files.items()):
        path = tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        entries.append(
            examples.manifest()
            .files[0]
            .model_copy(
                update={
                    "path": relative,
                    "size": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
        )
    manifest = examples.manifest().model_copy(
        update={
            "files": tuple(entries),
            "file_count": len(entries),
            "total_bytes": sum(map(len, files.values())),
            "verification": examples.manifest().verification.model_copy(
                update={
                    "hashed_bytes": sum(map(len, files.values())),
                    "hashed_objects": len(entries),
                    "reused_digests": 0,
                }
            ),
        }
    )
    path = repository.manifest(commit, publication)
    path.parent.mkdir(parents=True)
    path.write_text(manifest.to_json(), encoding="utf-8")
    publish_revision_reference(layout, reference)
    publish_current_reference(layout, reference)
    return repository


def recovery_journal(layout: ArchiveLayout) -> Path:
    return next(
        path
        for path in layout.transactions.glob("*.json")
        if read_journal(layout, path).journal.operation == "recovery"
    )


def change_json(path: Path, change) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    change(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_empty_cleanup_preserves_all_journals_and_unselected_entries(layout: ArchiveLayout):
    identifier = abandoned(layout)
    other = abandoned(layout)
    target = layout.quarantine_for(identifier)
    (target / "tree" / ".cache" / "huggingface" / "download").mkdir(parents=True)
    before = {path: path.read_bytes() for path in layout.transactions.glob("*.json")}

    plan = plan_quarantine_cleanup(layout, identifier)
    assert plan.to_dict()["logical_bytes"] == 0
    assert target.is_dir(), "planning must preserve all evidence"
    result = apply_quarantine_cleanup(layout, plan)

    assert result["removed_files"] == 0
    assert not target.exists()
    assert layout.quarantine_for(other).is_dir()
    assert {path: path.read_bytes() for path in layout.transactions.glob("*.json")} == before
    findings = reconcile_storage(layout, stale_staging_age_hours=24).findings
    assert [finding.transaction_id for finding in findings] == [str(other)]


def test_unrelated_terminal_legacy_prune_does_not_block_cleanup(layout: ArchiveLayout):
    identifier = abandoned(layout)
    transaction = open_transaction(
        layout,
        operation="prune",
        transaction_id=new_transaction_id(),
        run_id=new_run_id(),
        archive_id=examples.ARCHIVE_ID,
        config_fingerprint=examples.FINGERPRINT,
    )
    for name in CHECKPOINTS["prune"]:
        transaction.checkpoint(name)
    transaction.commit()
    journal = layout.journal(TransactionId(transaction.journal.transaction_id))
    # The two real July 26 terminal prunes predate containers_removed. They
    # remain readable durable history, and confer no ownership of this target.
    change_json(
        journal,
        lambda data: data.update(
            checkpoints=[
                checkpoint | {"sequence": index}
                for index, checkpoint in enumerate(
                    (
                        checkpoint
                        for checkpoint in data["checkpoints"]
                        if checkpoint["name"] != "containers_removed"
                    ),
                    start=1,
                )
            ]
        ),
    )
    before = journal.read_bytes()

    plan = plan_quarantine_cleanup(layout, identifier)
    apply_quarantine_cleanup(layout, plan)

    assert not layout.quarantine_for(identifier).exists()
    assert journal.read_bytes() == before


@pytest.mark.parametrize("authority", ["source", "recovery"])
def test_cleanup_authority_still_requires_valid_checkpoint_order(
    layout: ArchiveLayout, authority: str
):
    identifier = abandoned(layout, last_checkpoint="download_completed")
    journal = layout.journal(identifier) if authority == "source" else recovery_journal(layout)

    def reorder(data):
        if authority == "source":
            data["checkpoints"][:2] = reversed(data["checkpoints"][:2])
            for index, checkpoint in enumerate(data["checkpoints"], start=1):
                checkpoint["sequence"] = index
        else:
            data["checkpoints"][0]["name"] = "recovery_completed"

    change_json(journal, reorder)

    with pytest.raises(RetentionError):
        plan_quarantine_cleanup(layout, identifier)
    assert layout.quarantine_for(identifier).is_dir()


def test_duplicate_cleanup_reads_and_preserves_current_bytes(layout: ArchiveLayout):
    files = {"README.md": b"safe duplicate", "nested/config.json": b"{}"}
    identifier = abandoned(layout, files)
    publish_current(layout, files)
    current = layout.published / examples.REFERENCE_TREE
    before = {path: path.read_bytes() for path in current.rglob("*") if path.is_file()}

    plan = plan_quarantine_cleanup(layout, identifier)
    assert plan.to_dict()["logical_bytes"] == sum(map(len, files.values()))
    assert len(plan.to_dict()["files"]) == 2
    result = apply_quarantine_cleanup(layout, plan)

    assert result["removed_files"] == 2
    assert result["removed_logical_bytes"] == sum(map(len, files.values()))
    assert not layout.quarantine_for(identifier).exists()
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize("shares_current", [False, True])
def test_duplicate_hardlink_aliases_survive_their_own_ctime_changes(
    layout: ArchiveLayout, *, shares_current: bool
):
    files = {"a.json": b"shared", "b.json": b"shared"}
    identifier = abandoned(layout, files)
    publish_current(layout, files)
    target = layout.quarantine_for(identifier) / "tree"
    current = layout.published / examples.REFERENCE_TREE
    (target / "b.json").unlink()
    if shares_current:
        (target / "a.json").unlink()
        os.link(current / "a.json", target / "a.json")
    os.link(target / "a.json", target / "b.json")
    plan = plan_quarantine_cleanup(layout, identifier)

    result = apply_quarantine_cleanup(layout, plan)

    assert result["removed_files"] == 2
    assert not layout.quarantine_for(identifier).exists()
    assert (current / "a.json").read_bytes() == b"shared"
    assert (current / "b.json").read_bytes() == b"shared"


def test_cli_cleans_hardlinks_shared_between_selected_targets(
    layout: ArchiveLayout, config_file: Path
):
    first = abandoned(layout, {"config.json": b"shared"})
    second = abandoned(layout, {"config.json": b"shared"})
    publish_current(layout, {"config.json": b"shared"})
    first_file = layout.quarantine_for(first) / "tree" / "config.json"
    second_file = layout.quarantine_for(second) / "tree" / "config.json"
    second_file.unlink()
    os.link(first_file, second_file)

    result = invoke(config_file, "--apply", first, second)

    assert result.exit_code == ExitCode.SUCCESS, result.output
    assert not layout.quarantine_for(first).exists()
    assert not layout.quarantine_for(second).exists()
    assert (layout.published / examples.REFERENCE_TREE / "config.json").read_bytes() == b"shared"


@pytest.mark.parametrize(
    "fault",
    [
        "missing_current",
        "different_quarantine",
        "corrupt_current",
        "unlisted_file",
        "wrong_reference",
    ],
)
def test_nonempty_cleanup_refuses_unproven_duplicates(layout: ArchiveLayout, fault: str):
    identifier = abandoned(layout, {"config.json": b"good"})
    target = layout.quarantine_for(identifier) / "tree" / "config.json"
    repository = publish_current(layout, {"config.json": b"good"})
    current_file = layout.published / examples.REFERENCE_TREE / "config.json"
    if fault == "missing_current":
        repository.current_ref.unlink()
    elif fault == "different_quarantine":
        target.write_bytes(b"evil")
    elif fault == "corrupt_current":
        current_file.write_bytes(b"evil")
    elif fault == "unlisted_file":
        target.rename(target.with_name("unique-evidence"))
    else:
        change_json(repository.current_ref, lambda data: data.update(publication_generation=2))

    with pytest.raises(RetentionError):
        plan_quarantine_cleanup(layout, identifier)

    assert layout.quarantine_for(identifier).is_dir()
    assert len(list(layout.quarantine_for(identifier).rglob("*"))) >= 2


@pytest.mark.parametrize(
    "fault",
    [
        "no_journal",
        "no_recovery",
        "wrong_recovery_path",
        "wrong_recovery_archive",
        "wrong_source_archive",
        "not_rollback",
        "unknown_journal_field",
    ],
)
def test_cleanup_requires_unambiguous_source_and_completed_recovery(
    layout: ArchiveLayout, fault: str
):
    identifier = abandoned(layout)
    source = layout.journal(identifier)
    recovered = recovery_journal(layout)
    if fault == "no_journal":
        source.unlink()
    elif fault == "no_recovery":
        recovered.unlink()
    elif fault == "wrong_recovery_path":

        def alter(data):
            for checkpoint in data["checkpoints"]:
                if checkpoint["name"] == "quarantine_staging":
                    checkpoint["evidence"]["quarantine_path"] = ".store/quarantine/" + "f" * 32

        change_json(recovered, alter)
    elif fault == "wrong_recovery_archive":
        change_json(
            recovered, lambda data: data.update(archive_id="00000000-0000-4000-8000-000000000000")
        )
    elif fault == "wrong_source_archive":
        change_json(
            source, lambda data: data.update(archive_id="00000000-0000-4000-8000-000000000000")
        )
    elif fault == "unknown_journal_field":
        change_json(source, lambda data: data.update(future_cleanup_contract="preserve"))
    else:
        change_json(source, lambda data: data["error"].update(message="ordinary failed sync"))

    with pytest.raises(RetentionError):
        plan_quarantine_cleanup(layout, identifier)

    assert layout.quarantine_for(identifier).is_dir()


@pytest.mark.parametrize("state", ["open", "needs_operator"])
def test_unresolved_transaction_anywhere_prevents_cleanup(layout: ArchiveLayout, state: str):
    identifier = abandoned(layout)
    transaction = begin(layout)
    if state == "needs_operator":
        transaction.needs_operator("HFTXN003", "operator must resolve this")

    with pytest.raises(RetentionError):
        plan_quarantine_cleanup(layout, identifier)

    assert layout.quarantine_for(identifier).is_dir()


@pytest.mark.parametrize(
    "kind", ["unknown_root", "root_file", "symlink_file", "symlink_directory", "fifo"]
)
def test_unknown_or_special_entries_are_preserved(layout: ArchiveLayout, tmp_path: Path, kind: str):
    identifier = abandoned(layout)
    target = layout.quarantine_for(identifier)
    outside = tmp_path / "outside"
    outside.mkdir()
    evidence = outside / "precious"
    evidence.write_bytes(b"keep me")
    if kind == "unknown_root":
        (target / "operator-directory").mkdir()
    elif kind == "root_file":
        (target / "manifest.json").write_bytes(b"{}")
    elif kind == "symlink_file":
        (target / "tree" / "config.json").symlink_to(evidence)
    elif kind == "symlink_directory":
        (target / "tree" / "nested").symlink_to(outside, target_is_directory=True)
    else:
        os.mkfifo(target / "tree" / "pipe")

    with pytest.raises(RetentionError):
        plan_quarantine_cleanup(layout, identifier)

    assert target.is_dir()
    assert evidence.read_bytes() == b"keep me"


@pytest.mark.parametrize("area", ["quarantine", "current_tree", "current_refs"])
def test_symlink_ancestors_are_refused(layout: ArchiveLayout, tmp_path: Path, area: str):
    identifier = abandoned(layout, {"config.json": b"data"})
    repository = publish_current(layout, {"config.json": b"data"})
    original = {
        "quarantine": layout.quarantine,
        "current_tree": repository.revisions,
        "current_refs": repository.refs,
    }[area]
    moved = tmp_path / "moved"
    original.rename(moved)
    original.symlink_to(moved, target_is_directory=True)

    with pytest.raises(RetentionError):
        plan_quarantine_cleanup(layout, identifier)

    assert original.is_symlink()
    assert layout.quarantine_for(identifier).is_dir()


@pytest.mark.parametrize(
    "changed", ["quarantine_bytes", "current_bytes", "current_reference", "added_entry", "journal"]
)
def test_apply_revalidates_every_proof_before_deletion(layout: ArchiveLayout, changed: str):
    identifier = abandoned(layout, {"config.json": b"good"})
    repository = publish_current(layout, {"config.json": b"good"})
    plan = plan_quarantine_cleanup(layout, identifier)
    target = layout.quarantine_for(identifier)
    if changed == "quarantine_bytes":
        (target / "tree" / "config.json").write_bytes(b"evil")
    elif changed == "current_bytes":
        (layout.published / examples.REFERENCE_TREE / "config.json").write_bytes(b"evil")
    elif changed == "current_reference":
        repository.current_ref.unlink()
    elif changed == "added_entry":
        (target / "operator-note").write_bytes(b"preserve")
    else:
        recovery_journal(layout).unlink()

    with pytest.raises(RetentionError):
        apply_quarantine_cleanup(layout, plan)

    assert (target / "tree" / "config.json").exists()


@pytest.mark.parametrize("changed", ["quarantine", "retained"])
def test_bytes_changing_after_replanning_are_preserved(
    layout: ArchiveLayout, monkeypatch: pytest.MonkeyPatch, changed: str
):
    identifier = abandoned(layout, {"config.json": b"good"})
    publish_current(layout, {"config.json": b"good"})
    target = layout.quarantine_for(identifier) / "tree" / "config.json"
    retained = layout.published / examples.REFERENCE_TREE / "config.json"
    plan = plan_quarantine_cleanup(layout, identifier)

    def replan_then_change(archive, transaction_id):
        fresh = plan_quarantine_cleanup(archive, transaction_id)
        (target if changed == "quarantine" else retained).write_bytes(b"evil")
        return fresh

    monkeypatch.setattr(quarantine_module, "plan_quarantine_cleanup", replan_then_change)

    with pytest.raises(RetentionError):
        apply_quarantine_cleanup(layout, plan)

    assert target.is_file()
    assert retained.is_file()


def test_new_file_in_empty_directory_is_never_recursively_deleted(
    layout: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    identifier = abandoned(layout)
    target = layout.quarantine_for(identifier)
    plan = plan_quarantine_cleanup(layout, identifier)

    def replan_then_add(archive, transaction_id):
        fresh = plan_quarantine_cleanup(archive, transaction_id)
        (target / "tree" / "new-evidence").write_bytes(b"preserve")
        return fresh

    monkeypatch.setattr(quarantine_module, "plan_quarantine_cleanup", replan_then_add)

    with pytest.raises(RetentionError):
        apply_quarantine_cleanup(layout, plan)

    assert (target / "tree" / "new-evidence").read_bytes() == b"preserve"


@pytest.mark.parametrize(
    "last_checkpoint", ["staging_created", "download_completed", "content_hashed"]
)
def test_recovered_download_without_publication_id_can_clean_empty_staging(
    layout: ArchiveLayout, last_checkpoint: str
):
    # SYNC-007 opens the download journal before a publication instance exists.
    # Real recovery supplies the terminal source and committed quarantine proof.
    identifier = abandoned(layout, publication_id=None, last_checkpoint=last_checkpoint)
    journal = layout.journal(identifier)
    before = journal.read_bytes()
    source = read_journal(layout, journal).journal
    assert source.publication_id is None
    assert source.state == "failed"
    assert source.checkpoints[-1].name == last_checkpoint

    plan = plan_quarantine_cleanup(layout, identifier)
    result = apply_quarantine_cleanup(layout, plan)

    assert result["removed_files"] == 0
    assert not layout.quarantine_for(identifier).exists()
    assert journal.read_bytes() == before


@pytest.mark.parametrize("publication_id", [None, examples.REPLACEMENT])
def test_a_publication_that_reached_rename_is_not_staging_cleanup(
    layout: ArchiveLayout, publication_id: str | None
):
    identifier = abandoned(layout, publication_id=publication_id)

    def add_published_checkpoints(data):
        first = data["checkpoints"][0]
        for name in (
            "download_completed",
            "content_hashed",
            "staging_built",
            "revision_tree_renamed",
        ):
            data["checkpoints"].append(
                dict(first, sequence=len(data["checkpoints"]) + 1, name=name, evidence={})
            )

    change_json(layout.journal(identifier), add_published_checkpoints)

    with pytest.raises(RetentionError):
        plan_quarantine_cleanup(layout, identifier)

    assert layout.quarantine_for(identifier).is_dir()


def test_staging_reappearing_invalidates_the_recovery_proof(layout: ArchiveLayout):
    identifier = abandoned(layout)
    staging = layout.staging_for(identifier).directory
    staging.mkdir()

    with pytest.raises(RetentionError):
        plan_quarantine_cleanup(layout, identifier)

    assert staging.is_dir()
    assert layout.quarantine_for(identifier).is_dir()


def test_interrupted_deletion_can_be_replanned_and_completed(
    layout: ArchiveLayout, monkeypatch: pytest.MonkeyPatch
):
    files = {"a.json": b"a", "b.json": b"b"}
    identifier = abandoned(layout, files)
    publish_current(layout, files)
    target = layout.quarantine_for(identifier)
    plan = plan_quarantine_cleanup(layout, identifier)
    original = os.unlink

    def interrupt(path, *args, **kwargs):
        if Path(path).name == "b.json":
            raise KeyboardInterrupt
        return original(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(quarantine_module.os, "unlink", interrupt)
        with pytest.raises(KeyboardInterrupt):
            apply_quarantine_cleanup(layout, plan)

    assert not (target / "tree" / "a.json").exists()
    assert (target / "tree" / "b.json").read_bytes() == b"b"
    resumed = plan_quarantine_cleanup(layout, identifier)
    apply_quarantine_cleanup(layout, resumed)
    assert not target.exists()
    absent = plan_quarantine_cleanup(layout, identifier)
    assert absent.to_dict()["already_absent"]
    assert apply_quarantine_cleanup(layout, absent)["removed_files"] == 0


def test_ancestor_swap_during_unlink_never_removes_external_file(
    layout: ArchiveLayout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    identifier = abandoned(layout, {"config.json": b"good"})
    publish_current(layout, {"config.json": b"good"})
    target = layout.quarantine_for(identifier)
    outside = tmp_path / "outside"
    outside.mkdir()
    precious = outside / "config.json"
    precious.write_bytes(b"external evidence")
    plan = plan_quarantine_cleanup(layout, identifier)
    original = os.unlink
    swapped = False

    def swap_then_unlink(path, *args, **kwargs):
        nonlocal swapped
        if Path(path).name == "config.json" and not swapped:
            swapped = True
            (target / "tree").rename(tmp_path / "detached")
            (target / "tree").symlink_to(outside, target_is_directory=True)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(quarantine_module.os, "unlink", swap_then_unlink)

    with pytest.raises(RetentionError):
        apply_quarantine_cleanup(layout, plan)

    assert swapped
    assert precious.read_bytes() == b"external evidence"
    assert (target / "tree").is_symlink()


def test_ancestor_swap_during_rmdir_never_removes_external_directory(
    layout: ArchiveLayout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    identifier = abandoned(layout)
    target = layout.quarantine_for(identifier)
    (target / "tree" / "nested").mkdir()
    outside = tmp_path / "outside"
    (outside / "nested").mkdir(parents=True)
    plan = plan_quarantine_cleanup(layout, identifier)
    original = os.rmdir
    swapped = False

    def swap_then_rmdir(path, *args, **kwargs):
        nonlocal swapped
        if Path(path).name == "nested" and not swapped:
            swapped = True
            (target / "tree").rename(tmp_path / "detached")
            (target / "tree").symlink_to(outside, target_is_directory=True)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(quarantine_module.os, "rmdir", swap_then_rmdir)

    with pytest.raises(RetentionError):
        apply_quarantine_cleanup(layout, plan)

    assert swapped
    assert (outside / "nested").is_dir()
    assert (target / "tree").is_symlink()


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["--dry-run", "--apply"],
        ["--dry-run"],
        ["--apply"],
        ["--all", "--apply"],
        ["--dry-run", "../unsafe"],
        ["--dry-run", "A" * 32],
    ],
)
def test_cli_requires_mode_and_explicit_valid_identifiers(config_file: Path, arguments: list[str]):
    result = invoke(config_file, *arguments)

    assert result.exit_code != ExitCode.SUCCESS


@pytest.mark.parametrize("modes", [[], ["--dry-run", "--apply"]])
def test_cli_requires_exactly_one_mode_for_a_valid_selection(
    layout: ArchiveLayout, config_file: Path, modes: list[str]
):
    identifier = abandoned(layout)

    result = invoke(config_file, *modes, identifier)

    assert result.exit_code == ExitCode.CONFIGURATION
    assert layout.quarantine_for(identifier).is_dir()


def test_cli_dry_run_and_apply_select_only_named_findings(layout: ArchiveLayout, config_file: Path):
    identifier = abandoned(layout)
    other = abandoned(layout)
    before = {path: path.stat().st_mtime_ns for path in layout.root.rglob("*")}

    dry_run = invoke(config_file, "--dry-run", identifier)
    assert dry_run.exit_code == ExitCode.SUCCESS, dry_run.output
    assert {path: path.stat().st_mtime_ns for path in layout.root.rglob("*")} == before
    applied = invoke(config_file, "--apply", identifier)

    assert applied.exit_code == ExitCode.SUCCESS, applied.output
    assert not layout.quarantine_for(identifier).exists()
    assert layout.quarantine_for(other).is_dir()
    assert json.loads(applied.stdout)["outcome"] == "success"


def test_cli_validates_entire_batch_before_deleting(layout: ArchiveLayout, config_file: Path):
    first = abandoned(layout)
    second = abandoned(layout)
    (layout.quarantine_for(second) / "unrecognized").mkdir()

    result = invoke(config_file, "--apply", first, second)

    assert result.exit_code == ExitCode.RETENTION, result.output
    assert layout.quarantine_for(first).is_dir()
    assert layout.quarantine_for(second).is_dir()


def test_cli_apply_requires_the_writer_lock(
    layout: ArchiveLayout, config_file: Path, tmp_path: Path
):
    identifier = abandoned(layout)
    run = tmp_path / "run"
    run.mkdir()
    with (run / "hfcache.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = invoke(config_file, "--apply", identifier)

    assert result.exit_code != ExitCode.SUCCESS
    assert layout.quarantine_for(identifier).is_dir()


def test_cli_apply_requires_storage_preflight(
    layout: ArchiveLayout, config_file: Path, tmp_path: Path
):
    identifier = abandoned(layout)
    (tmp_path / "mountinfo").write_text("", encoding="utf-8")

    result = invoke(config_file, "--apply", identifier)

    assert result.exit_code == ExitCode.SAFETY, result.output
    assert layout.quarantine_for(identifier).is_dir()
