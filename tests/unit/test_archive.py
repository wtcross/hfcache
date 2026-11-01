"""Inspecting a target, and creating an archive on it exactly once.

`archive init` is irreversible and runs against the live NAS exactly once, so
almost every test here is about a *refusal*: what the command declines to touch,
and why. The mount table is supplied as a fixture rather than read from `/proc`,
which is what lets a temporary directory stand in for the NFS archive without
mounting anything.

Ownership rules are exercised through `published_adoption_problems`, which takes
`os.stat_result` values instead of paths. That is deliberate: the Mapall export
presents NAS-side ids that this host has no account for and `<operator>` cannot
`chown` to, so the policy is tested for identities the test process could never
create on disk.

The `archive init` *command* — its options, its envelope, and the `--confirm`
gate — is `tests/unit/test_archive_init.py`.
"""

import json
import os
import stat
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from hfcache.archive import (
    initialize_archive,
    inspect_archive,
    published_adoption_problems,
)
from hfcache.errors import SafetyError
from hfcache.hashing import FileDigest
from hfcache.hub import TreeEntry
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    RunId,
    new_publication_id,
    new_run_id,
    new_transaction_id,
)
from hfcache.metadata import MetadataReader, QueryBounds, QueryLimitError
from hfcache.models import SCHEMA_VERSION, ArchiveSentinel, Provenance, Reference, dump
from hfcache.paths import ArchiveLayout
from hfcache.publication import (
    create_staging,
    discard_staging,
    promote_staging,
    publish_catalog,
    publish_current_reference,
    publish_revision_reference,
    rebuild_catalog,
    stage_file,
)
from hfcache.storage import (
    MountEntry,
    atomic_write_bytes,
    parse_mount_table,
    temporary_sibling,
    write_model,
)
from hfcache.sync import Timeline, build_manifest, hash_snapshot
from hfcache.transactions import CHECKPOINTS, open_transaction
from tests.fixtures import examples

if TYPE_CHECKING:
    from pathlib import Path

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
OTHER_ARCHIVE_ID = "11111111-2222-3333-4444-555555555555"

STORE_MODE = 0o700
PUBLISHED_MODE = 0o2750
SENTINEL_MODE = 0o640


def nfs_line(mount_point: str, *, filesystem: str = "nfs4", options: str = "rw") -> str:
    """One mountinfo line for `mount_point`, in the kernel's field order."""
    return (
        f"457 47 0:68 / {mount_point} {options},nosuid,nodev,relatime shared:488 "
        f"- {filesystem} nas.lab.example.com:/mnt/tank/hf rw,vers=4.2"
    )


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    root = tmp_path / "archive"
    root.mkdir()
    return root


@pytest.fixture
def layout(archive_root: Path) -> ArchiveLayout:
    return ArchiveLayout(root=archive_root)


@pytest.fixture
def table(archive_root: Path) -> tuple[MountEntry, ...]:
    """A mount table in which the temporary archive root is an NFSv4 mount.

    Two entries, because that is what the writer really has: the systemd
    automount and the NFS mount stacked on top of it at the same path.
    """
    real = os.path.realpath(archive_root)
    return parse_mount_table(
        f"47 68 0:34 / {real} rw,relatime shared:43 - autofs systemd-1 rw,fd=51\n{nfs_line(real)}\n"
    )


def initialize(layout: ArchiveLayout, table: tuple[MountEntry, ...]):
    return initialize_archive(layout, archive_id=ARCHIVE_ID, table=table)


def inspect(
    layout: ArchiveLayout,
    table: tuple[MountEntry, ...],
    *,
    archive_id: str = ARCHIVE_ID,
    bounded_reader: bool = False,
):
    return inspect_archive(
        layout,
        archive_id=archive_id,
        table=table,
        reader=MetadataReader(layout.root) if bounded_reader else None,
    )


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


# --------------------------------------------------------------------------- #
# Adopting a pre-existing published/
# --------------------------------------------------------------------------- #


def status(mode: int, uid: int, gid: int) -> os.stat_result:
    """A stat result carrying only the fields the adoption rule reads."""
    return os.stat_result((stat.S_IFDIR | mode, 1, 1, 1, uid, gid, 0, 0, 0, 0))


def test_published_is_adopted_when_owner_and_mode_already_match():
    root = status(0o750, 3001, 3002)
    published = status(PUBLISHED_MODE, 3001, 3002)

    assert published_adoption_problems(root, published, mode=PUBLISHED_MODE, location="p") == []


def test_a_wrongly_moded_published_is_refused_rather_than_fixed():
    root = status(0o750, 3001, 3002)
    published = status(0o755, 3001, 3002)

    problems = published_adoption_problems(root, published, mode=PUBLISHED_MODE, location="p")

    assert codes(problems) == ["HFMNT014"]
    assert "2750" in problems[0].message


def test_ownership_is_compared_against_the_root_not_against_a_local_uid():
    # Under the Mapall writer export both carry NAS-side ids with no local
    # account, so "the same identity owns both" is the only checkable form of
    # the ownership rule (docs/storage-requirements.md effective writability).
    root = status(0o750, 3001, 3002)

    assert (
        published_adoption_problems(
            root, status(PUBLISHED_MODE, 3001, 3002), mode=0o2750, location="p"
        )
        == []
    )
    assert codes(
        published_adoption_problems(
            root, status(PUBLISHED_MODE, 0, 3002), mode=0o2750, location="p"
        )
    ) == ["HFMNT014"]
    assert codes(
        published_adoption_problems(
            root, status(PUBLISHED_MODE, 3001, 0), mode=0o2750, location="p"
        )
    ) == ["HFMNT014"]


def test_both_adoption_failures_are_reported_at_once():
    problems = published_adoption_problems(
        status(0o750, 3001, 3002), status(0o755, 0, 0), mode=PUBLISHED_MODE, location="p"
    )

    assert codes(problems) == ["HFMNT014", "HFMNT014"]


# --------------------------------------------------------------------------- #
# Inspection
# --------------------------------------------------------------------------- #


def test_an_empty_mounted_root_is_uninitialized_and_initializable(layout, table):
    inspection = inspect(layout, table)

    assert inspection.state == "uninitialized"
    assert inspection.initializable
    assert inspection.problems == ()
    assert inspection.existing_directories == ()
    assert ".store/hub" in inspection.missing_directories


def test_a_pre_existing_empty_published_is_adopted(layout, table):
    layout.published.mkdir()
    layout.published.chmod(PUBLISHED_MODE)

    inspection = inspect(layout, table)

    assert inspection.state == "uninitialized", "TrueNAS creating it is not work we started"
    assert inspection.adopted_published
    assert inspection.existing_directories == ("published",)
    assert inspection.problems == ()


def test_a_non_empty_published_is_refused(layout, table):
    layout.published.mkdir()
    layout.published.chmod(PUBLISHED_MODE)
    (layout.published / "somebody-elses-data").write_text("x", encoding="utf-8")

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT014"]
    assert inspection.unknown_entries == ("published/somebody-elses-data",)


def test_a_wrongly_moded_published_makes_the_target_unusable(layout, table):
    layout.published.mkdir()
    layout.published.chmod(0o755)

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT014"]


def test_unknown_content_refuses_initialization_and_is_never_removed(layout, table):
    stranger = layout.root / "somebody-elses-file"
    stranger.write_text("keep me", encoding="utf-8")

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT014"]
    assert stranger.read_text(encoding="utf-8") == "keep me"


def test_an_unknown_directory_is_reported_but_not_descended(layout, table):
    populated = layout.root / "someones-home"
    (populated / "deep" / "deeper").mkdir(parents=True)
    for index in range(50):
        (populated / f"file-{index}").write_text("x", encoding="utf-8")

    inspection = inspect(layout, table)

    assert inspection.unknown_entries == ("someones-home",)
    assert inspection.unknown_entry_count == 1


def test_the_enumeration_of_unknown_entries_is_bounded_but_the_count_is_exact(layout, table):
    for index in range(40):
        (layout.root / f"file-{index:02d}").write_text("x", encoding="utf-8")

    inspection = inspect(layout, table)

    assert inspection.unknown_entry_count == 40
    assert len(inspection.unknown_entries) == 20
    assert inspection.unknown_entries == tuple(f"file-{index:02d}" for index in range(20))


def test_a_symlink_anywhere_in_the_layout_is_refused(layout, table, tmp_path: Path):
    (layout.root / "link").symlink_to(tmp_path)

    inspection = inspect(layout, table)

    assert codes(inspection.problems) == ["HFMNT015"]


def test_a_symlink_inside_a_layout_directory_is_refused(layout, table, tmp_path: Path):
    layout.store.mkdir()
    layout.store.chmod(STORE_MODE)
    (layout.store / "hub").symlink_to(tmp_path)

    inspection = inspect(layout, table)

    assert codes(inspection.problems) == ["HFMNT015"]
    assert inspection.problems[0].location == ".store/hub"


def test_a_partial_layout_without_a_sentinel_is_retryable(layout, table):
    layout.store.mkdir()
    layout.store.chmod(STORE_MODE)
    layout.staging.mkdir()
    layout.staging.chmod(STORE_MODE)

    inspection = inspect(layout, table)

    assert inspection.state == "partially_initialized"
    assert inspection.initializable
    assert inspection.problems == ()
    assert inspection.existing_directories == (".store", ".store/staging")


def test_a_leftover_sentinel_temporary_is_part_of_the_known_layout(layout, table):
    leftover = temporary_sibling(layout.sentinel)
    leftover.write_bytes(b"half a sentinel")

    inspection = inspect(layout, table)

    assert inspection.problems == ()
    assert inspection.leftover_temporaries == (leftover.name,)
    assert inspection.unknown_entry_count == 0


def test_a_directory_named_like_a_temporary_is_still_unknown(layout, table):
    temporary_sibling(layout.sentinel).mkdir()

    inspection = inspect(layout, table)

    assert codes(inspection.problems) == ["HFMNT014"]


def test_an_unreadable_layout_directory_is_reported(layout, table):
    layout.store.mkdir()
    layout.store.chmod(0o000)
    try:
        inspection = inspect(layout, table)
    finally:
        layout.store.chmod(STORE_MODE)

    assert codes(inspection.problems) == ["HFMNT008"]


def test_an_unusable_mount_stops_before_the_tree_is_walked(layout):
    (layout.root / "unknown").write_text("x", encoding="utf-8")

    inspection = inspect(layout, ())

    assert codes(inspection.problems) == ["HFMNT002"]
    assert inspection.unknown_entries == (), "nothing is claimed about a tree that was not read"


def test_a_full_layout_with_a_matching_sentinel_is_initialized(layout, table):
    initialize(layout, table)

    inspection = inspect(layout, table)

    assert inspection.state == "initialized"
    assert not inspection.initializable
    assert inspection.problems == ()
    assert inspection.sentinel is not None
    assert inspection.sentinel.archive_id == ARCHIVE_ID


@pytest.mark.parametrize("bounded_reader", [False, True])
def test_model_and_dataset_publications_do_not_make_archive_layout_unusable(
    layout, table, tmp_path: Path, *, bounded_reader: bool
):
    """FS-21/AD-10: normal publication adds namespaces, not an invalid init layout."""
    initialize(layout, table)
    snapshot = tmp_path / "download"
    snapshot.mkdir()
    payload = b"a published model or dataset file"
    (snapshot / "config.json").write_bytes(payload)
    tree = (TreeEntry(path="config.json", size=len(payload)),)
    now = datetime(2026, 10, 28, tzinfo=UTC)
    timeline = Timeline(now, now, now, now, now)
    sha = CommitSha("a" * 40)
    for kind in ("model", "dataset"):
        identity = RepositoryIdentity.of(kind, "organization/repository")
        repository = layout.repository(identity)
        publication = new_publication_id()
        transaction = new_transaction_id()
        staging = create_staging(layout, transaction)
        hashed = hash_snapshot(snapshot, tree, identity=identity)
        entry = hashed.files[0]
        stage_file(
            snapshot / "config.json",
            staging.tree / "config.json",
            publication_mode="copy",
            cache_root=snapshot,
            expected=FileDigest(digest=entry.sha256, size=entry.size),
            expected_identity=entry.object_identity,
        )
        manifest = build_manifest(
            identity=identity,
            requested_revision="main",
            commit_sha=sha,
            publication_id=publication,
            publication_generation=1,
            publication_mode="copy",
            tree=tree,
            hashed=hashed,
            layout=repository,
            hub_endpoint="https://huggingface.co",
            timeline=timeline,
        )
        promote_staging(layout, staging, repository.instance(sha, publication))
        manifest_path = repository.manifest(sha, publication)
        manifest_path.parent.mkdir(parents=True)
        write_model(manifest_path, manifest, mode=0o640, code="HFMNT008")
        reference = Reference(
            commit_sha=sha,
            manifest=str(repository.manifest_reference(sha, publication)),
            publication_generation=1,
            publication_id=publication,
            repository_id=identity.id,
            repository_type=identity.type,
            tree=str(repository.tree_reference(sha, publication)),
            updated_at=now,
        )
        publish_revision_reference(layout, reference)
        publish_current_reference(layout, reference)
        discard_staging(layout, transaction)

    # FS-16/17 and decision029: ordinary writer history does not undo init.
    publish_catalog(layout, rebuild_catalog(layout, generated_at=now))
    write_model(
        layout.verification_catalog, examples.verification_catalog(), mode=0o640, code="HFMNT008"
    )
    for original in (examples.run_report(), examples.verification_report()):
        report = original.model_copy(update={"run_id": new_run_id()})
        write_model(
            layout.run_report(report.started_at, RunId(report.run_id)),
            report,
            mode=0o600,
            code="HFMNT008",
        )
    journal = open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint=examples.FINGERPRINT,
        repository_type=identity.type,
        repository_id=identity.id,
        commit_sha=sha,
        publication_id=publication,
    )
    for checkpoint in CHECKPOINTS["publication"]:
        journal.checkpoint(checkpoint)
    journal.commit()
    before = {
        path: (path.read_bytes(), path.stat().st_ino, path.stat().st_mode, path.stat().st_mtime_ns)
        for path in layout.root.rglob("*")
        if path.is_file()
    }
    inspection = inspect_archive(
        layout,
        archive_id=ARCHIVE_ID,
        table=table,
        reader=MetadataReader(layout.root) if bounded_reader else None,
    )

    assert inspection.state == "initialized"
    assert inspection.problems == ()
    assert inspection.unknown_entries == ()
    assert inspection.missing_directories == ()
    assert before == {
        path: (path.read_bytes(), path.stat().st_ino, path.stat().st_mode, path.stat().st_mtime_ns)
        for path in before
    }


@pytest.mark.parametrize("bounded_reader", [False, True])
def test_initialized_working_containers_and_audit_records_are_known_without_payload_walks(
    layout, table, *, bounded_reader: bool
):
    """FS-13/18/20: original engines own cache, transaction payload and audit validity."""
    initialize(layout, table)
    staging = create_staging(layout, new_transaction_id())
    (staging.tree / "payload.bin").write_bytes(b"ordinary staged payload")
    trash = layout.trash_for(new_transaction_id()).directory
    # Purge tombstones have a different shape from publication staging.
    for name in ("refs", "revisions", "manifests"):
        (trash / name).mkdir(parents=True)
    quarantined = layout.quarantine_for(new_transaction_id())
    quarantined.mkdir()
    (quarantined / "README.md").write_text("retired publication payload", encoding="utf-8")
    for cache in (layout.hub_cache, layout.repair_cache_for(new_transaction_id())):
        repository = cache / "models--organization--repository"
        blob = repository / "blobs" / ("a" * 40)
        blob.parent.mkdir(parents=True)
        blob.write_bytes(b"SDK-owned blob")
        snapshot = repository / "snapshots" / ("b" * 40)
        snapshot.mkdir(parents=True)
        (snapshot / "config.json").symlink_to("../../blobs/" + "a" * 40)

    repository = layout.repository(RepositoryIdentity.of("model", examples.REPOSITORY_ID))
    publication = PublicationId(examples.PUBLICATION)
    records = (
        (repository.pruned_manifest(CommitSha(examples.SHA), publication), examples.manifest()),
        (repository.prune_record(CommitSha(examples.SHA), publication), examples.pruned_record()),
        (repository.retired_manifest(CommitSha(examples.SHA), publication), examples.manifest()),
        (
            repository.retirement_record(CommitSha(examples.SHA), publication),
            examples.repair_retirement(),
        ),
    )
    for path, model in records:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_model(path, model, mode=0o600, code="HFMNT008")
    temporary = temporary_sibling(records[-1][0])
    temporary.write_bytes(b"an interrupted ordinary atomic write")

    inspection = inspect(layout, table, bounded_reader=bounded_reader)

    assert inspection.state == "initialized"
    assert inspection.problems == ()
    assert inspection.unknown_entries == ()
    assert inspection.leftover_temporaries == (str(layout.archive_relative(temporary)),)
    assert (snapshot / "config.json").is_symlink()
    assert blob.read_bytes() == b"SDK-owned blob"


@pytest.mark.parametrize("bounded_reader", [False, True])
@pytest.mark.parametrize(
    ("relative", "directory"),
    [
        ("published/catalog/repositories.json", False),
        ("published/catalog/verification.json", False),
        (".store/transactions/" + "1" * 32 + ".json", False),
        ("runs/20261030T120000Z-" + "2" * 32 + ".json", False),
        ("audit/pruned/models/org/repo/" + "a" * 40 + "/" + "3" * 32 + ".prune.json", False),
        (".store/staging/" + "4" * 32, True),
        (".store/trash/" + "5" * 32, True),
        (".store/quarantine/" + "6" * 32, True),
        (".store/repair/" + "7" * 32, True),
        (".store/hub", True),
    ],
)
@pytest.mark.parametrize("entry", ["wrong_type", "fifo", "symlink"])
def test_initialized_managed_names_refuse_unsafe_types_without_following_or_rewriting(  # noqa: PLR0913 - independent type and reader refusal matrix
    layout,
    table,
    tmp_path: Path,
    relative: str,
    *,
    directory: bool,
    entry: str,
    bounded_reader: bool,
):
    """FS-19: a recognized name grants neither arbitrary type nor deletion authority."""
    initialize(layout, table)
    child = layout.root / relative
    if child.exists():
        child.rmdir()  # Only the newly initialized empty SDK cache root.
    child.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    if entry == "symlink":
        outside.write_bytes(b"must not be followed")
        child.symlink_to(outside)
    elif entry == "fifo":
        os.mkfifo(child)
    elif directory:
        child.write_bytes(b"not a directory")
    else:
        child.mkdir()
    original = child.lstat()

    inspection = inspect(layout, table, bounded_reader=bounded_reader)

    assert inspection.state == "unusable"
    assert ("HFMNT015" if entry == "symlink" else "HFMNT014") in codes(inspection.problems)
    assert (child.lstat().st_ino, child.lstat().st_mode) == (original.st_ino, original.st_mode)
    if entry == "symlink":
        assert outside.read_bytes() == b"must not be followed"


@pytest.mark.parametrize("bounded_reader", [False, True])
@pytest.mark.parametrize(
    "relative",
    [
        "published/catalog/unknown.json",
        ".store/transactions/not-a-transaction.json",
        "runs/not-a-run.json",
        "audit/pruned/unknown",
        "audit/repairs/models/org/repo/" + "a" * 40 + "/" + "1" * 32 + ".prune.json",
        ".store/staging/not-a-transaction",
        ".store/trash/not-a-transaction",
        ".store/quarantine/not-a-transaction",
        ".store/repair/not-a-transaction",
        ".store/health/probe-" + "1" * 16,
    ],
)
def test_initialized_layout_keeps_unknown_siblings_and_probe_leftovers_refused(
    layout, table, relative: str, *, bounded_reader: bool
):
    """FS-19 and the probe contract: normal content is no license to accept unknowns."""
    initialize(layout, table)
    child = layout.root / relative
    child.parent.mkdir(parents=True, exist_ok=True)
    if child.parent == layout.health:
        child.mkdir()
        payload = child / "probe.json"
    else:
        payload = child
    payload.write_bytes(b"preserved unknown entry")

    inspection = inspect(layout, table, bounded_reader=bounded_reader)

    assert inspection.state == "unusable"
    assert relative in inspection.unknown_entries
    assert payload.read_bytes() == b"preserved unknown entry"


@pytest.mark.parametrize("bounded_reader", [False, True])
def test_normal_post_init_content_is_not_adopted_without_the_sentinel(
    layout, table, *, bounded_reader: bool
):
    """FS-22/23: post-init recognition cannot authorize initialization or a retry."""
    initialize(layout, table)
    layout.sentinel.unlink()
    layout.repositories_catalog.write_bytes(b"{}")
    (layout.hub_cache / "models--org--repo").mkdir()
    layout.staging_for(new_transaction_id()).directory.mkdir()

    inspection = inspect(layout, table, bounded_reader=bounded_reader)

    assert inspection.state == "unusable"
    assert not inspection.initializable
    assert inspection.unknown_entries
    assert not layout.sentinel.exists()


def test_post_init_metadata_keeps_the_existing_reader_entry_budget(layout, table):
    """The new recognition still enumerates through the one bounded reader."""
    initialize(layout, table)
    for _ in range(40):
        layout.journal(new_transaction_id()).write_bytes(b"ordinary journal metadata")
    reader = MetadataReader(layout.root, QueryBounds(maximum_entries=32))

    with pytest.raises(QueryLimitError):
        inspect_archive(layout, archive_id=ARCHIVE_ID, table=table, reader=reader)


@pytest.mark.parametrize("parent", ["repos", "manifests"])
@pytest.mark.parametrize("entry", ["unknown", "file", "symlink"])
def test_initialized_publication_namespaces_still_refuse_unexplained_entries(
    layout, table, tmp_path: Path, parent: str, entry: str
):
    initialize(layout, table)
    directory = getattr(layout, parent)
    child = directory / ("stranger" if entry == "unknown" else "models")
    if entry == "unknown":
        child.mkdir()
    elif entry == "file":
        child.write_text("not a publication directory", encoding="utf-8")
    else:
        child.symlink_to(tmp_path, target_is_directory=True)

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT015" if entry == "symlink" else "HFMNT014"]


def test_publication_namespaces_are_not_adopted_before_initialization(layout, table):
    (layout.repos / "models").mkdir(parents=True)

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert inspection.unknown_entries == ("published/repos/models",)


def test_a_sentinel_that_disagrees_with_configuration_is_hfmnt007(layout, table):
    initialize(layout, table)

    inspection = inspect(layout, table, archive_id=OTHER_ARCHIVE_ID)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT007"]


def test_a_malformed_sentinel_is_hfmnt006(layout, table):
    initialize(layout, table)
    layout.sentinel.write_text("{ not json", encoding="utf-8")

    with pytest.raises(SafetyError) as caught:
        inspect(layout, table)

    assert codes(caught.value.problems) == ["HFMNT006"]


def test_a_sentinel_from_a_newer_release_is_refused_rather_than_read(layout, table):
    initialize(layout, table)
    payload = json.loads(layout.sentinel.read_text(encoding="utf-8"))
    payload["schema_version"] = SCHEMA_VERSION + 1
    layout.sentinel.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SafetyError) as caught:
        inspect(layout, table)

    assert codes(caught.value.problems) == ["HFMNT006"]
    assert "newer" in caught.value.problems[0].message


def test_an_unreadable_sentinel_is_hfmnt006(layout, table):
    initialize(layout, table)
    layout.sentinel.chmod(0o000)
    try:
        with pytest.raises(SafetyError) as caught:
            inspect(layout, table)
    finally:
        layout.sentinel.chmod(SENTINEL_MODE)

    assert codes(caught.value.problems) == ["HFMNT006"]


def test_a_sentinel_without_the_layout_beneath_it_is_hfmnt008(layout, table):
    # The sentinel is written last (`FS-23`), so this combination cannot come
    # from initialization and must not be treated as a healthy archive.
    sentinel = ArchiveSentinel(
        archive_id=ARCHIVE_ID,
        created_at=datetime(2026, 7, 25, tzinfo=UTC),
        created_by=Provenance(application_version="0.1.0", hostname="writer"),
    )
    atomic_write_bytes(layout.sentinel, dump(sentinel), mode=SENTINEL_MODE)

    inspection = inspect(layout, table)

    assert inspection.state == "unusable"
    assert codes(inspection.problems) == ["HFMNT008"]


def test_an_inspection_renders_for_the_envelope(layout, table):
    payload = inspect(layout, table).as_payload()

    assert set(payload) == {
        "adopted_published",
        "archive_id",
        "archive_root",
        "existing_directories",
        "initializable",
        "leftover_temporaries",
        "missing_directories",
        "mount",
        "state",
        "unknown_entries",
        "unknown_entry_count",
    }
    assert payload["archive_id"] is None, "no sentinel means no archive id to report"
    assert payload["archive_root"] == str(layout.root)


def test_generated_arrays_are_sorted(layout, table):
    payload = inspect(layout, table).as_payload()

    assert payload["missing_directories"] == sorted(payload["missing_directories"])


def test_inspection_reads_the_system_mount_table_when_none_is_given(
    layout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    fake = tmp_path / "mountinfo"
    fake.write_text(nfs_line(os.path.realpath(layout.root)), encoding="utf-8")
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", fake)

    assert inspect_archive(layout, archive_id=ARCHIVE_ID).state == "uninitialized"


# --------------------------------------------------------------------------- #
# Initialization
# --------------------------------------------------------------------------- #


def test_initialization_creates_the_whole_layout(layout, table):
    result = initialize(layout, table)

    for spec in layout.required_directories():
        assert spec.path.is_dir()
    assert len(result.created_directories) == len(layout.required_directories())


def test_every_directory_gets_the_mode_section_5_2_requires(layout, table):
    initialize(layout, table)

    for spec in layout.required_directories():
        assert stat.S_IMODE(spec.path.stat().st_mode) == spec.mode, spec.path


def test_the_published_subtree_is_setgid_and_group_traversable(layout, table):
    initialize(layout, table)

    for path in (layout.published, layout.repos, layout.manifests, layout.catalog):
        assert stat.S_IMODE(path.stat().st_mode) == PUBLISHED_MODE


def test_private_areas_are_not_group_readable(layout, table):
    initialize(layout, table)

    for path in (layout.store, layout.audit, layout.runs, layout.hub_cache):
        assert stat.S_IMODE(path.stat().st_mode) == STORE_MODE


def test_the_umask_does_not_reach_the_created_modes(layout, table):
    original = os.umask(0o077)
    try:
        initialize(layout, table)
    finally:
        os.umask(original)

    assert stat.S_IMODE(layout.published.stat().st_mode) == PUBLISHED_MODE


def test_the_sentinel_is_written_with_the_configured_archive_id(layout, table):
    result = initialize(layout, table)

    written = json.loads(layout.sentinel.read_text(encoding="utf-8"))
    assert written["archive_id"] == ARCHIVE_ID == result.sentinel.archive_id
    assert written["layout_version"] == 1
    assert written["schema_version"] == SCHEMA_VERSION


def test_the_sentinel_records_which_build_created_the_archive(layout, table):
    result = initialize(layout, table)

    assert result.sentinel.created_by.application_version
    assert result.sentinel.created_by.hostname


def test_the_sentinel_is_readable_to_the_group_and_writable_only_by_the_writer(layout, table):
    initialize(layout, table)

    assert stat.S_IMODE(layout.sentinel.stat().st_mode) == SENTINEL_MODE


def test_initialization_adopts_a_pre_existing_published(layout, table):
    layout.published.mkdir()
    layout.published.chmod(PUBLISHED_MODE)

    result = initialize(layout, table)

    assert result.adopted_published
    assert "published" not in result.created_directories
    assert layout.repos.is_dir()


def test_initialization_completes_a_partial_layout(layout, table):
    layout.store.mkdir()
    layout.store.chmod(STORE_MODE)

    result = initialize(layout, table)

    assert ".store" not in result.created_directories
    assert ".store/hub" in result.created_directories
    assert inspect(layout, table).state == "initialized"


def test_a_partial_directory_with_the_wrong_mode_is_corrected_on_retry(layout, table):
    # A crash between mkdir and chmod leaves a directory of ours at the umask's
    # mode. It is application-owned and empty, so a retry restates the mode.
    layout.store.mkdir(mode=0o755)
    layout.store.chmod(0o755)

    initialize(layout, table)

    assert stat.S_IMODE(layout.store.stat().st_mode) == STORE_MODE


def test_a_leftover_sentinel_temporary_is_removed_by_the_retry(layout, table):
    leftover = temporary_sibling(layout.sentinel)
    leftover.write_bytes(b"half a sentinel")

    result = initialize(layout, table)

    assert result.removed_temporaries == (leftover.name,)
    assert not leftover.exists()
    assert layout.sentinel.is_file()


def test_initializing_twice_is_refused(layout, table):
    initialize(layout, table)

    with pytest.raises(SafetyError) as caught:
        initialize(layout, table)

    assert codes(caught.value.problems) == ["HFMNT014"]


def test_initialization_re_inspects_rather_than_trusting_a_caller(layout, table):
    (layout.root / "appeared-after-the-report").write_text("x", encoding="utf-8")

    with pytest.raises(SafetyError) as caught:
        initialize(layout, table)

    assert codes(caught.value.problems) == ["HFMNT014"]


def test_a_write_that_fails_after_every_check_passed_is_a_coded_failure(layout, table):
    # Every check reads; a server-side read-only export, a reached quota, or the
    # NAS going away are all only discovered by writing. That must be exit `20`
    # with a code, not a traceback out of the middle of the layout.
    layout.root.chmod(0o500)
    try:
        with pytest.raises(SafetyError) as caught:
            initialize(layout, table)
    finally:
        layout.root.chmod(0o750)

    assert codes(caught.value.problems) == ["HFMNT008"]
    assert "--inspect" in caught.value.problems[0].message


def test_a_half_finished_attempt_is_still_recognised_as_retryable(layout, table):
    layout.root.chmod(0o500)
    try:
        with pytest.raises(SafetyError):
            initialize(layout, table)
    finally:
        layout.root.chmod(0o750)

    assert inspect(layout, table).initializable
    assert initialize(layout, table).sentinel.archive_id == ARCHIVE_ID


def test_nothing_is_created_when_the_mount_is_wrong(layout):
    with pytest.raises(SafetyError) as caught:
        initialize_archive(layout, archive_id=ARCHIVE_ID, table=())

    assert codes(caught.value.problems) == ["HFMNT002"]
    assert list(layout.root.iterdir()) == []


def test_the_result_renders_for_the_envelope(layout, table):
    payload = initialize(layout, table).as_payload()

    assert set(payload) == {
        "adopted_published",
        "archive_id",
        "archive_root",
        "created_directories",
        "removed_temporaries",
        "sentinel",
    }
    assert payload["sentinel"] == ".hfcache-root"
    assert payload["created_directories"] == sorted(payload["created_directories"])
