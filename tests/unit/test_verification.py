"""Reading the archive back — plan §16, `docs/schemas.md` §7.

Every archive here is built by publishing through the real code path, never by
writing files that look like a publication's output. That matters more for
verification than anywhere else: a fixture that fabricated a published tree would
let these tests pass against a layout the publisher does not produce, which is
precisely the failure verification exists to catch.

Damage is then done to that real archive — a byte flipped, a file truncated, a
path removed, something planted — and what is asserted is the finding it produces
and the fact that the archive is unchanged afterwards.
"""

import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Literal, get_args

import pytest

from hfcache.archive import initialize_archive
from hfcache.errors import ConfigurationError, HfcacheError
from hfcache.hub import TreeEntry
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    new_publication_id,
    new_run_id,
    new_transaction_id,
)
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import create_staging, next_generation, read_reference
from hfcache.reporting import Finding, RepositoryRunResult, RunReport
from hfcache.storage import parse_mount_table, write_model
from hfcache.sync import Timeline, build_manifest, hash_snapshot, publish_revision
from hfcache.transactions import open_transaction
from hfcache.verification import (
    FINDING_CODES,
    INTRODUCING_STATUSES,
    ReadSet,
    Resolved,
    build_report,
    require_retained,
    resolve_repository,
    resolve_revision,
    resolve_run,
    verify_target,
    verify_targets,
)

if TYPE_CHECKING:
    from hfcache.sync import PublicationOutcome

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
FINGERPRINT = "b" * 64

MODEL = RepositoryIdentity.of("model", "organization/model-name")
DATASET = RepositoryIdentity.of("dataset", "organization/dataset-name")

SHA_A = "1111111111111111111111111111111111111111"
SHA_B = "2222222222222222222222222222222222222222"

NOW = datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC)
TIMELINE = Timeline(
    first_observed_at=NOW,
    download_started_at=NOW,
    download_completed_at=NOW,
    verified_at=NOW,
    published_at=NOW,
)

CONFIG_BYTES = b'{"name": "tiny"}'
WEIGHTS_BYTES = b"weights, and a good few of them" * 4

FILES = {
    "config.json": CONFIG_BYTES,
    "nested/weights.bin": WEIGHTS_BYTES,
}
TREE = tuple(TreeEntry(path=path, size=len(payload)) for path, payload in sorted(FILES.items()))

ENVELOPE = {
    "application_version": "0.1.0",
    "archive_id": ARCHIVE_ID,
    "config_fingerprint": FINGERPRINT,
    "hostname": "writer.example",
    "huggingface_hub_version": "1.24.0",
    "invocation_mode": "interactive",
    "python_version": "3.14.6",
}


def nfs_line(root: str) -> str:
    return f"457 47 0:68 / {root} rw,relatime shared:488 - nfs4 nas:/mnt/tank/hf rw,vers=4.2\n"


@pytest.fixture
def layout(tmp_path: Path) -> ArchiveLayout:
    """A real initialized archive on a temporary directory."""
    root = tmp_path / "archive"
    root.mkdir()
    built = ArchiveLayout(root=root)
    initialize_archive(
        built, archive_id=ARCHIVE_ID, table=parse_mount_table(nfs_line(os.path.realpath(root)))
    )
    return built


def snapshot_for(layout: ArchiveLayout, identity: RepositoryIdentity, commit_sha: str) -> Path:
    """A downloaded snapshot in the private cache, laid out the way one is.

    One directory per repository per revision, reaching content through symlinks
    into a shared `blobs/`, which is the shape `huggingface_hub` produces. The
    sharing is the point: two revisions of one repository hardlink to the same
    objects when they are published, which is what makes the read-once property
    observable rather than theoretical.
    """
    path = layout.hub_cache / f"{identity.type}s--{identity.id.replace('/', '--')}" / commit_sha
    for name, payload in FILES.items():
        blob = layout.hub_cache / "blobs" / f"{len(payload)}-{name.replace('/', '-')}"
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(payload)
        link = path / name
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(blob)
    return path


def publish(
    layout: ArchiveLayout,
    *,
    identity: RepositoryIdentity = MODEL,
    commit_sha: str = SHA_A,
    publication_mode: Literal["hardlink", "copy"] = "hardlink",
) -> PublicationOutcome:
    """Publish one revision through the real §7.3 sequence."""
    snapshot = snapshot_for(layout, identity, commit_sha)
    transaction_id = new_transaction_id()
    transaction = open_transaction(
        layout,
        transaction_id=transaction_id,
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=FINGERPRINT,
        repository_id=identity.id,
        repository_type=identity.type,
    )
    staging = create_staging(layout, transaction_id)
    transaction.checkpoint(
        "staging_created", staging_path=str(layout.archive_relative(staging.directory))
    )
    transaction.checkpoint("download_completed", cache_revision=commit_sha)
    hashed = hash_snapshot(snapshot, TREE, identity=identity)
    transaction.checkpoint("content_hashed", hashed_objects=hashed.hashed_objects)
    manifest = build_manifest(
        identity=identity,
        requested_revision="main",
        commit_sha=CommitSha(commit_sha),
        publication_id=new_publication_id(),
        publication_generation=next_generation(layout, identity),
        publication_mode=publication_mode,
        tree=TREE,
        hashed=hashed,
        layout=RepositoryLayout(archive=layout, identity=identity),
        hub_endpoint="https://huggingface.co",
        timeline=TIMELINE,
    )
    outcome = publish_revision(
        layout,
        transaction,
        identity=identity,
        snapshot=snapshot,
        manifest=manifest,
        staging=staging,
        publication_mode=publication_mode,
        cache_root=layout.hub_cache,
    )
    transaction.checkpoint("publication_committed", state="committed")
    transaction.commit()
    return outcome


def tree_of(layout: ArchiveLayout, outcome: PublicationOutcome, identity=MODEL) -> Path:
    """Where one published instance's files live."""
    return RepositoryLayout(archive=layout, identity=identity).instance(
        CommitSha(outcome.commit_sha), PublicationId(outcome.publication_id)
    )


def run(resolved) -> tuple[Finding, ...]:
    """Verify a resolution set and return its findings."""
    return verify_targets(resolved, started_at=NOW, now=NOW).findings


def kinds(findings) -> list[str]:
    return [finding.kind for finding in findings]


# --------------------------------------------------------------------------- #
# The code table
# --------------------------------------------------------------------------- #


def test_every_finding_kind_has_a_code_and_every_code_has_a_kind():
    """`FINDING_CODES` covers `Finding.kind` exactly, in both directions."""
    declared = set(get_args(Finding.model_fields["kind"].annotation))
    assert set(FINDING_CODES) == declared


def test_the_codes_are_exactly_the_integrity_family_docs_cli_publishes():
    """Parsed out of `docs/cli.md` §5.4, so the table cannot drift from the contract."""
    text = Path("docs/cli.md").read_text(encoding="utf-8")
    section = text.split("### 5.4 Integrity")[1].split("### 5.5")[0]
    published = set(re.findall(r"`(HFVER\d{3})`", section))
    assert set(FINDING_CODES.values()) == published


def test_only_the_two_statuses_that_published_something_are_verified_by_new():
    """`--new` reads what a run introduced, which is what publishing means."""
    declared = set(get_args(RepositoryRunResult.model_fields["status"].annotation))
    assert declared > INTRODUCING_STATUSES
    assert sorted(INTRODUCING_STATUSES) == ["completed_with_warnings", "published"]


# --------------------------------------------------------------------------- #
# A clean archive
# --------------------------------------------------------------------------- #


def test_a_freshly_published_revision_verifies_clean(layout):
    publish(layout)
    outcome = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    assert outcome.findings == ()
    assert outcome.outcome == "clean"
    assert outcome.repositories == 1
    assert outcome.revisions == 1
    assert outcome.objects_read == len(FILES)
    assert outcome.bytes_read == sum(len(payload) for payload in FILES.values())


def test_verification_reads_and_writes_nothing(layout):
    """Plan §16.1: a verification never rewrites the evidence it is reading."""
    publish(layout)
    before = {
        path: path.read_bytes()
        for path in sorted(layout.published.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }
    run(resolve_repository(layout, MODEL))
    after = {
        path: path.read_bytes()
        for path in sorted(layout.published.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }
    assert before == after


# --------------------------------------------------------------------------- #
# The read set (plan §16.2 item 4)
# --------------------------------------------------------------------------- #


def test_a_blob_shared_by_two_revisions_is_read_once(layout):
    """Two hardlinked trees, one physical object, one read."""
    publish(layout, commit_sha=SHA_A)
    publish(layout, commit_sha=SHA_B)
    outcome = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    assert outcome.findings == ()
    assert outcome.revisions == 2
    assert outcome.objects_read == len(FILES)
    assert outcome.bytes_read == sum(len(payload) for payload in FILES.values())


def test_copy_mode_files_are_each_read_even_when_the_digests_match(layout):
    """`docs/schemas.md` §7: identical expected digests in two copy-mode trees
    are different physical objects, so one read proves nothing about the other."""
    publish(layout, commit_sha=SHA_A, publication_mode="copy")
    publish(layout, commit_sha=SHA_B, publication_mode="copy")
    outcome = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    assert outcome.findings == ()
    assert outcome.objects_read == 2 * len(FILES)
    assert outcome.bytes_read == 2 * sum(len(payload) for payload in FILES.values())


def test_the_read_set_reuses_a_confirmed_hardlink(tmp_path):
    original = tmp_path / "a"
    original.write_bytes(b"shared bytes")
    twin = tmp_path / "b"
    os.link(original, twin)

    reads = ReadSet()
    first = reads.digest_of(original, share=True)
    second = reads.digest_of(twin, share=True)

    assert first == second
    assert reads.objects_read == 1
    assert reads.bytes_read == len(b"shared bytes")


def test_the_read_set_reads_again_when_the_recorded_path_is_gone(tmp_path):
    """An inode number is reused after deletion, so the tuple alone is not proof.

    `samefile` is what confirms it, and here the confirmation fails because the
    path the earlier read came from has been unlinked — the object is read again,
    which is the answer that cannot be wrong.
    """
    original = tmp_path / "a"
    original.write_bytes(b"shared bytes")
    twin = tmp_path / "b"
    os.link(original, twin)

    reads = ReadSet()
    reads.digest_of(original, share=True)
    original.unlink()
    reads.digest_of(twin, share=True)

    assert reads.objects_read == 2


def test_the_read_set_never_shares_when_sharing_is_off(tmp_path):
    original = tmp_path / "a"
    original.write_bytes(b"shared bytes")
    twin = tmp_path / "b"
    os.link(original, twin)

    reads = ReadSet()
    reads.digest_of(original, share=False)
    reads.digest_of(twin, share=False)

    assert reads.objects_read == 2


# --------------------------------------------------------------------------- #
# Damage (`docs/schemas.md` §7's kinds)
# --------------------------------------------------------------------------- #


def test_a_removed_file_is_missing(layout):
    outcome = publish(layout)
    (tree_of(layout, outcome) / "config.json").unlink()
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["missing"]
    assert findings[0].path == "config.json"
    assert findings[0].publication_id == outcome.publication_id


def test_a_planted_file_is_extra(layout):
    outcome = publish(layout)
    (tree_of(layout, outcome) / "planted.txt").write_bytes(b"not ours")
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["extra"]
    assert findings[0].path == "planted.txt"


def test_a_planted_directory_is_reported_once_and_not_descended(layout):
    outcome = publish(layout)
    intruder = tree_of(layout, outcome) / "intruder"
    intruder.mkdir()
    (intruder / "one").write_bytes(b"1")
    (intruder / "two").write_bytes(b"2")
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["extra"]
    assert findings[0].path == "intruder"


def test_a_planted_name_the_grammar_refuses_is_still_reported(layout):
    """A backslash is a legal Linux filename and a path separator on a consumer
    platform, so it can never be a `path` field — it is reported all the same."""
    outcome = publish(layout)
    (tree_of(layout, outcome) / "escape\\..\\..\\etc").write_bytes(b"planted")
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["extra"]
    assert findings[0].path is None
    assert "could have published" in (findings[0].observed or "")


def test_a_truncated_file_is_a_size_mismatch_and_is_not_hashed(layout):
    outcome = publish(layout)
    path = tree_of(layout, outcome) / "config.json"
    path.unlink()
    path.write_bytes(CONFIG_BYTES[:4])
    result = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    assert kinds(result.findings) == ["size_mismatch"]
    assert result.findings[0].expected == str(len(CONFIG_BYTES))
    assert result.findings[0].observed == "4"
    # The other file was read; the truncated one was not.
    assert result.objects_read == len(FILES) - 1


def test_a_flipped_byte_is_a_digest_mismatch(layout):
    outcome = publish(layout)
    path = tree_of(layout, outcome) / "config.json"
    replacement = bytearray(CONFIG_BYTES)
    replacement[0] ^= 0xFF
    path.unlink()
    path.write_bytes(bytes(replacement))
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["digest_mismatch"]
    assert findings[0].expected != findings[0].observed


def test_a_directory_where_a_file_belongs_is_not_regular(layout):
    outcome = publish(layout)
    path = tree_of(layout, outcome) / "config.json"
    path.unlink()
    path.mkdir()
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["not_regular"]
    assert findings[0].observed == "directory"


def test_a_symlink_where_a_file_belongs_is_not_regular(layout, tmp_path):
    """Publication never creates a symlink (`AD-10`), so one in a tree was planted.

    `lstat` is what sees it: the link resolves to a perfectly good file, so
    anything following it would report the revision as sound.
    """
    outcome = publish(layout)
    elsewhere = tmp_path / "decoy"
    elsewhere.write_bytes(CONFIG_BYTES)
    path = tree_of(layout, outcome) / "config.json"
    path.unlink()
    path.symlink_to(elsewhere)
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["not_regular"]
    assert findings[0].observed == "symbolic link"


def test_a_fifo_where_a_file_belongs_is_not_regular(layout):
    outcome = publish(layout)
    path = tree_of(layout, outcome) / "config.json"
    path.unlink()
    os.mkfifo(path)
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["not_regular"]
    assert findings[0].observed == "FIFO"


def test_an_unreadable_object_is_reported_rather_than_hashed(layout):
    outcome = publish(layout)
    path = tree_of(layout, outcome) / "config.json"
    path.chmod(0o000)
    try:
        findings = run(resolve_repository(layout, MODEL))
    finally:
        path.chmod(0o640)
    assert kinds(findings) == ["unreadable"]


def test_a_path_that_cannot_be_stat_ed_is_unreadable(layout):
    """A parent directory with no search permission fails `lstat` with `EACCES`,
    which is not the same condition as a file that is not there."""
    outcome = publish(layout)
    nested = tree_of(layout, outcome) / "nested"
    nested.chmod(0o000)
    try:
        findings = run(resolve_repository(layout, MODEL))
    finally:
        nested.chmod(0o2750)
    assert kinds(findings) == ["unreadable"]
    assert findings[0].path == "nested/weights.bin"


# --------------------------------------------------------------------------- #
# Damaged references and manifests
# --------------------------------------------------------------------------- #


def test_an_unparseable_reference_is_a_ref_invalid_finding_with_no_instance(layout):
    outcome = publish(layout)
    reference = RepositoryLayout(archive=layout, identity=MODEL).revision_ref(
        CommitSha(outcome.commit_sha)
    )
    reference.write_text("{ not json", encoding="utf-8")
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["ref_invalid"]
    assert findings[0].publication_id is None
    assert findings[0].commit_sha == outcome.commit_sha


def test_a_reference_naming_a_tree_that_is_not_there_is_ref_invalid(layout):
    outcome = publish(layout)
    tree = tree_of(layout, outcome)
    for path in sorted(tree.rglob("*"), reverse=True):
        path.rmdir() if path.is_dir() else path.unlink()
    tree.rmdir()
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["ref_invalid"]
    assert findings[0].publication_id == outcome.publication_id


def test_an_unreadable_manifest_is_manifest_invalid(layout):
    outcome = publish(layout)
    manifest = RepositoryLayout(archive=layout, identity=MODEL).manifest(
        CommitSha(outcome.commit_sha), PublicationId(outcome.publication_id)
    )
    manifest.write_text("{}", encoding="utf-8")
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["manifest_invalid"]


def test_a_manifest_that_describes_another_instance_is_manifest_invalid(layout):
    """A manifest filed under one SHA that describes another is refused wholesale.

    Comparing every file against the wrong expectation would produce a page of
    mismatches for one misfiled artifact.
    """
    first = publish(layout, commit_sha=SHA_A)
    second = publish(layout, commit_sha=SHA_B)
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    target = repository.manifest(CommitSha(first.commit_sha), PublicationId(first.publication_id))
    source = repository.manifest(CommitSha(second.commit_sha), PublicationId(second.publication_id))
    target.write_bytes(source.read_bytes())
    findings = [
        finding
        for finding in run(resolve_repository(layout, MODEL))
        if finding.commit_sha == first.commit_sha
    ]
    assert kinds(findings) == ["manifest_invalid"]
    assert "commit_sha" in (findings[0].observed or "")


def test_a_manifest_naming_another_repository_is_manifest_invalid(layout):
    model = publish(layout, identity=MODEL, commit_sha=SHA_A)
    dataset = publish(layout, identity=DATASET, commit_sha=SHA_A)
    target = RepositoryLayout(archive=layout, identity=MODEL).manifest(
        CommitSha(model.commit_sha), PublicationId(model.publication_id)
    )
    source = RepositoryLayout(archive=layout, identity=DATASET).manifest(
        CommitSha(dataset.commit_sha), PublicationId(dataset.publication_id)
    )
    target.write_bytes(source.read_bytes())
    findings = run(resolve_repository(layout, MODEL))
    assert kinds(findings) == ["manifest_invalid"]
    assert "repository_id" in (findings[0].observed or "")
    assert "repository_type" in (findings[0].observed or "")


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #


def test_a_sha_the_archive_does_not_retain_resolves_to_nothing(layout):
    publish(layout)
    assert resolve_revision(layout, MODEL, CommitSha(SHA_B)) == Resolved()


def test_a_file_in_refs_revisions_that_is_not_a_sha_is_left_alone(layout):
    publish(layout)
    refs = RepositoryLayout(archive=layout, identity=MODEL).refs / "revisions"
    (refs / "notes.json").write_text("{}", encoding="utf-8")
    assert len(resolve_repository(layout, MODEL)) == 1
    assert run(resolve_repository(layout, MODEL)) == ()


def test_require_retained_refuses_a_revision_the_archive_does_not_hold(layout):
    publish(layout)
    with pytest.raises(ConfigurationError) as caught:
        require_retained(layout, MODEL, CommitSha(SHA_B))
    assert [problem.code for problem in caught.value.problems] == ["HFARG004"]


def test_require_retained_returns_the_revision_it_holds(layout):
    outcome = publish(layout)
    resolved = require_retained(layout, MODEL, CommitSha(outcome.commit_sha))
    assert resolved.target is not None
    assert resolved.target.manifest.publication_id == outcome.publication_id


def test_require_retained_still_returns_a_damaged_revision(layout):
    """A damaged reference is a finding, not a missing revision — the operator
    asked about that SHA and it is there, in a state worth reporting."""
    outcome = publish(layout)
    RepositoryLayout(archive=layout, identity=MODEL).revision_ref(
        CommitSha(outcome.commit_sha)
    ).write_text("{ not json", encoding="utf-8")
    resolved = require_retained(layout, MODEL, CommitSha(outcome.commit_sha))
    assert resolved.target is None
    assert kinds(resolved.findings) == ["ref_invalid"]


def test_resolve_run_covers_only_what_the_run_introduced(layout):
    published = publish(layout, identity=MODEL, commit_sha=SHA_A)
    publish(layout, identity=DATASET, commit_sha=SHA_A)
    report = RunReport.model_validate(
        dict(ENVELOPE)
        | {
            "command": "sync",
            "completed_at": NOW,
            "exit_code": 0,
            "outcome": "success",
            "run_id": new_run_id(),
            "started_at": NOW,
            "repositories": [
                {
                    "repository_id": DATASET.id,
                    "repository_type": DATASET.type,
                    "requested_revision": "main",
                    "resolved_commit_sha": SHA_A,
                    "status": "skipped",
                },
                {
                    "repository_id": MODEL.id,
                    "repository_type": MODEL.type,
                    "requested_revision": "main",
                    "resolved_commit_sha": published.commit_sha,
                    "publication_id": published.publication_id,
                    "publication_generation": 1,
                    "status": "published",
                },
            ],
        }
    )
    resolved = resolve_run(layout, report)
    assert len(resolved) == 1
    assert resolved[0].target is not None
    assert resolved[0].target.identity == MODEL


def test_resolve_run_skips_a_revision_a_later_prune_rotated_out(layout):
    """Resolution goes through the references, which describe the archive as it
    is — a SHA nothing retains has nothing to verify."""
    report = RunReport.model_validate(
        dict(ENVELOPE)
        | {
            "command": "sync",
            "completed_at": NOW,
            "exit_code": 0,
            "outcome": "success",
            "run_id": new_run_id(),
            "started_at": NOW,
            "repositories": [
                {
                    "repository_id": MODEL.id,
                    "repository_type": MODEL.type,
                    "requested_revision": "main",
                    "resolved_commit_sha": SHA_A,
                    "publication_id": new_publication_id(),
                    "publication_generation": 1,
                    "status": "published",
                }
            ],
        }
    )
    outcome = verify_targets(resolve_run(layout, report), started_at=NOW, now=NOW)
    assert outcome.findings == ()
    assert outcome.revisions == 0
    assert outcome.repositories == 0


# --------------------------------------------------------------------------- #
# The outcome and the report
# --------------------------------------------------------------------------- #


def test_the_scope_counts_repositories_and_revisions_separately(layout):
    publish(layout, identity=MODEL, commit_sha=SHA_A)
    publish(layout, identity=MODEL, commit_sha=SHA_B)
    publish(layout, identity=DATASET, commit_sha=SHA_A)
    resolved = (*resolve_repository(layout, MODEL), *resolve_repository(layout, DATASET))
    outcome = verify_targets(resolved, started_at=NOW, now=NOW)
    assert outcome.repositories == 2
    assert outcome.revisions == 3


def test_a_revision_that_never_resolved_still_counts_toward_the_scope(layout):
    outcome = publish(layout)
    RepositoryLayout(archive=layout, identity=MODEL).revision_ref(
        CommitSha(outcome.commit_sha)
    ).write_text("{ not json", encoding="utf-8")
    result = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    assert result.revisions == 1
    assert result.repositories == 1
    assert result.outcome == "failed"


def test_throughput_is_measured_when_bytes_were_read(layout):
    publish(layout)
    result = verify_targets(
        resolve_repository(layout, MODEL), started_at=NOW, now=NOW + timedelta(seconds=2)
    )
    assert result.duration_seconds == 2.0
    assert result.throughput_bytes_per_second == result.bytes_read / 2.0


def test_throughput_is_zero_when_no_time_passed(layout):
    publish(layout)
    result = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    assert result.bytes_read > 0
    assert result.throughput_bytes_per_second == 0.0


def test_throughput_is_zero_when_nothing_was_read(layout):
    result = verify_targets((), started_at=NOW, now=NOW + timedelta(seconds=2))
    assert result.bytes_read == 0
    assert result.throughput_bytes_per_second == 0.0


def test_a_clean_report_carries_no_findings_and_exits_zero(layout):
    publish(layout)
    result = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    report = build_report(
        result, envelope=ENVELOPE, command="verify --new", mode="new", run_id=new_run_id()
    )
    assert report.verification_outcome == "clean"
    assert report.exit_code == 0
    assert report.outcome == "success"
    assert report.errors == ()
    assert report.scope.unique_objects_read == len(FILES)


def test_a_failed_report_exits_forty_and_names_every_code_it_found(layout):
    outcome = publish(layout)
    tree = tree_of(layout, outcome)
    (tree / "config.json").unlink()
    (tree / "planted.txt").write_bytes(b"not ours")
    result = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    report = build_report(
        result, envelope=ENVELOPE, command="verify --new", mode="new", run_id=new_run_id()
    )
    assert report.verification_outcome == "failed"
    assert report.exit_code == 40
    assert report.outcome == "failed"
    assert set(report.errors) == {"HFVER003", "HFVER004"}


def test_findings_are_sorted_the_way_the_schema_requires(layout):
    publish(layout, identity=DATASET, commit_sha=SHA_A)
    model = publish(layout, identity=MODEL, commit_sha=SHA_A)
    for identity, published in ((MODEL, model),):
        tree = RepositoryLayout(archive=layout, identity=identity).instance(
            CommitSha(published.commit_sha), PublicationId(published.publication_id)
        )
        (tree / "config.json").unlink()
        (tree / "nested" / "weights.bin").unlink()
    dataset_tree = RepositoryLayout(archive=layout, identity=DATASET).revision_ref(CommitSha(SHA_A))
    dataset_tree.write_text("{ not json", encoding="utf-8")
    resolved = (*resolve_repository(layout, DATASET), *resolve_repository(layout, MODEL))
    result = verify_targets(resolved, started_at=NOW, now=NOW)
    assert [finding.sort_key for finding in result.findings] == sorted(
        finding.sort_key for finding in result.findings
    )


def test_a_verified_target_can_be_checked_on_its_own(layout):
    """`verify_target` is the unit `verify_targets` composes, and is usable alone."""
    publish(layout)
    resolved = resolve_repository(layout, MODEL)
    assert resolved[0].target is not None
    assert verify_target(resolved[0].target, ReadSet()) == ()


def test_a_repair_instance_inside_its_grace_period_is_not_verified(layout):
    """Only what a reference names is retained (`FS-11`). A superseded instance
    left at its original locator is evidence, not a revision."""
    outcome = publish(layout)
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    retired = repository.instance(CommitSha(outcome.commit_sha), PublicationId("f" * 32))
    retired.mkdir(parents=True)
    (retired / "config.json").write_bytes(b"whatever a retired instance holds")
    assert run(resolve_repository(layout, MODEL)) == ()


def test_the_verification_state_of_a_copy_mode_tree_is_read_per_file(layout):
    publish(layout, publication_mode="copy")
    resolved = resolve_repository(layout, MODEL)
    assert resolved[0].target is not None
    assert resolved[0].target.share_reads is False


def test_the_verification_state_of_a_hardlink_tree_shares_reads(layout):
    publish(layout)
    resolved = resolve_repository(layout, MODEL)
    assert resolved[0].target is not None
    assert resolved[0].target.share_reads is True


def test_the_reference_and_the_published_tree_agree_after_a_clean_run(layout):
    """A sanity check on the fixture itself: the archive it builds is the archive
    the publisher produces, reference and all."""
    outcome = publish(layout)
    reference = read_reference(
        layout,
        RepositoryLayout(archive=layout, identity=MODEL).revision_ref(
            CommitSha(outcome.commit_sha)
        ),
    )
    assert reference.publication_id == outcome.publication_id
    assert layout.published / reference.tree == tree_of(layout, outcome)


def test_a_run_report_round_trips_through_the_archive(layout, tmp_path):
    """`write_model` is what `--new` reads back, so the fixture uses it."""
    path = layout.run_report(NOW, new_run_id())
    path.parent.mkdir(parents=True, exist_ok=True)
    report = RunReport.model_validate(
        dict(ENVELOPE)
        | {
            "command": "sync",
            "completed_at": NOW,
            "exit_code": 0,
            "outcome": "success",
            "run_id": new_run_id(),
            "started_at": NOW,
        }
    )
    write_model(path, report, mode=0o600, code="HFVER007")
    assert path.is_file()
    assert resolve_run(layout, report) == ()


def test_nothing_here_raises_on_an_archive_with_no_published_content(layout):
    assert resolve_repository(layout, MODEL) == ()
    result = verify_targets(resolve_repository(layout, MODEL), started_at=NOW, now=NOW)
    assert result.outcome == "clean"


def test_a_finding_from_a_damaged_reference_still_names_its_repository(layout):
    outcome = publish(layout)
    RepositoryLayout(archive=layout, identity=MODEL).revision_ref(
        CommitSha(outcome.commit_sha)
    ).write_text("{ not json", encoding="utf-8")
    findings = run(resolve_repository(layout, MODEL))
    assert findings[0].repository_id == MODEL.id
    assert findings[0].repository_type == MODEL.type


def test_an_error_from_reading_a_manifest_is_reported_not_raised(layout):
    """Every artifact read here can fail, and none of those failures escape."""
    outcome = publish(layout)
    manifest = RepositoryLayout(archive=layout, identity=MODEL).manifest(
        CommitSha(outcome.commit_sha), PublicationId(outcome.publication_id)
    )
    manifest.unlink()
    try:
        findings = run(resolve_repository(layout, MODEL))
    except HfcacheError:  # pragma: no cover - the assertion below is the point
        pytest.fail("a damaged manifest must be a finding, never an exception")
    assert kinds(findings) == ["manifest_invalid"]
