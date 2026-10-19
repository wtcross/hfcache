"""Exact supplemental authority, no-follow paths and atomic adjunct failure states (V08-11)."""

import contextvars
import json
from contextlib import contextmanager

import pytest

from hfcache.archive import initialize_archive, inspect_archive
from hfcache.catalog_models import (
    PublicationObservation,
    RepositoryTagSnapshot,
    VariantMember,
    variant_identity,
)
from hfcache.catalog_storage import (
    CatalogWriter,
    parse_record,
    read_publication_observation,
    read_tag_snapshot,
)
from hfcache.config import StorageConfig
from hfcache.errors import HfcacheError, IntegrityError, SafetyError
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    new_run_id,
    new_transaction_id,
)
from hfcache.locking import exclusive_lock, require_archive_lock
from hfcache.metadata import MetadataReader, QueryLimitError
from hfcache.models import dump
from hfcache.paths import ArchiveLayout
from hfcache.preflight import CHECK_ORDER, Check
from hfcache.storage import parse_mount_table
from hfcache.transactions import open_transaction
from tests.fixtures import examples


@pytest.fixture
def archive(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    layout = ArchiveLayout(root)
    table = parse_mount_table(f"457 47 0:68 / {root} rw - nfs4 nas:/fixture rw,vers=4.2\n")
    initialize_archive(layout, archive_id=examples.ARCHIVE_ID, table=table)
    storage = StorageConfig.model_validate(
        {
            "archive_root": str(root),
            "archive_id": examples.ARCHIVE_ID,
            "minimum_free_space_gib": 0,
            "minimum_free_space_percent": 0,
        }
    )
    return layout, storage, table


@contextmanager
def writer(archive):
    layout, storage, table = archive
    with exclusive_lock(
        layout.root.parent / "locks/hfcache.lock", command="catalog refresh", wait_seconds=0
    ):
        yield CatalogWriter(layout, storage=storage, table=table)


def published(archive):
    layout, _, _ = archive
    manifest = examples.manifest()
    repository = layout.repository(manifest.identity)
    manifest_path = repository.manifest(
        CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id)
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_bytes(dump(manifest))
    reference = repository.revision_ref(CommitSha(manifest.commit_sha))
    reference.parent.mkdir(parents=True)
    reference.write_bytes(dump(examples.reference()))
    return manifest


def test_adjuncts_exempt_only_exact_active_sync_after_reconciliation(archive):
    layout, storage, table = archive
    with exclusive_lock(layout.root.parent / "locks/hfcache.lock", command="sync", wait_seconds=0):
        transaction = open_transaction(
            layout,
            transaction_id=new_transaction_id(),
            operation="sync",
            run_id=new_run_id(),
            archive_id=examples.ARCHIVE_ID,
            config_fingerprint="0" * 64,
        )
        transaction.checkpoint("run_started")
        transaction.checkpoint("preflight_passed")
        with pytest.raises(SafetyError):
            CatalogWriter(layout, storage=storage, table=table, active_sync=transaction.journal)
        transaction.checkpoint("journals_reconciled")
        with pytest.raises(SafetyError):
            CatalogWriter(layout, storage=storage, table=table)
        with pytest.raises(SafetyError):
            CatalogWriter(
                layout,
                storage=storage,
                table=table,
                active_sync=transaction.journal.model_copy(update={"run_id": new_run_id()}),
            )
        CatalogWriter(layout, storage=storage, table=table, active_sync=transaction.journal).write(
            examples.tag_snapshot()
        )


def test_resolved_but_impossible_journal_preserves_and_refuses(archive):
    layout, _, _ = archive
    journal = examples.journal().model_copy(update={"state": "committed"})
    path = layout.transactions / f"{journal.transaction_id}.json"
    original = dump(journal)
    path.write_bytes(original)
    with pytest.raises(IntegrityError), writer(archive):
        pytest.fail("impossible checkpoint order passed adjunct guard")
    assert path.read_bytes() == original


def test_round_trip_whole_records_and_original_evidence_unchanged(archive):
    layout, _, _ = archive
    manifest = published(archive)
    sentinel = layout.sentinel.read_bytes()
    path = layout.repository(manifest.identity).manifest(
        CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id)
    )
    original = path.read_bytes()
    snapshot, observation = examples.tag_snapshot(), examples.publication_observation()
    with writer(archive) as store:
        store.write(snapshot)
        store.write(observation)
    assert read_tag_snapshot(layout, manifest.identity, examples.ARCHIVE_ID) == snapshot
    assert (
        read_publication_observation(
            layout,
            manifest.identity,
            CommitSha(manifest.commit_sha),
            PublicationId(manifest.publication_id),
            examples.ARCHIVE_ID,
        )
        == observation
    )
    assert path.read_bytes() == original
    assert layout.sentinel.read_bytes() == sentinel
    assert not tuple(layout.transactions.iterdir()), "adjuncts do not invent transaction journals"


@pytest.mark.parametrize(
    ("model", "factory"),
    [
        (RepositoryTagSnapshot, examples.tag_snapshot),
        (PublicationObservation, examples.publication_observation),
    ],
)
@pytest.mark.parametrize("version", [None, True, "1", 0, 2])
def test_explicit_independent_schema_versions(model, factory, version):
    payload = factory().to_payload()
    payload["schema_version"] = version
    with pytest.raises(IntegrityError):
        parse_record(model, json.dumps(payload).encode())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(tags=["Coding"]),
        lambda p: p.update(tags=["z", "a"]),
        lambda p: p.update(tags=["a", "a"]),
        lambda p: p.update(tags=[1]),
        lambda p: p.update(extra="unknown"),
        lambda p: p.pop("kind"),
    ],
)
def test_tag_record_is_strict_canonical_not_a_normalizing_cache(mutate):
    payload = examples.tag_snapshot().to_payload()
    mutate(payload)
    with pytest.raises(IntegrityError):
        parse_record(RepositoryTagSnapshot, json.dumps(payload).encode())


@pytest.mark.parametrize(
    "raw",
    [b'{"schema_version":1,"schema_version":1}', b'{"x":NaN}', b"\xff", b"[" * 2000 + b"]" * 2000],
)
def test_ambiguous_or_unbounded_json_refuses(raw):
    with pytest.raises(IntegrityError):
        parse_record(RepositoryTagSnapshot, raw)


@pytest.mark.parametrize("kind", ["future", "corrupt", "symlink", "wrong_archive"])
def test_unsupported_prior_record_is_preserved_before_replacement(archive, kind):
    layout, _, _ = archive
    record = examples.tag_snapshot()
    with writer(archive) as store:
        path = store.write(record)
    if kind == "symlink":
        evidence = layout.root.parent / "evidence"
        evidence.write_text("unrecognized evidence")
        path.unlink()
        path.symlink_to(evidence)
        before = evidence.read_bytes()
    else:
        payload = record.to_payload()
        if kind == "future":
            payload["schema_version"] = 2
        if kind == "wrong_archive":
            payload["archive_id"] = "11111111-1111-4111-8111-111111111111"
        before = b"not JSON" if kind == "corrupt" else json.dumps(payload).encode()
        path.write_bytes(before)
    with pytest.raises(HfcacheError), writer(archive) as store:
        store.write(record)
    assert path.read_bytes() == before
    if kind == "symlink":
        assert path.is_symlink()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("archive_id", "11111111-1111-4111-8111-111111111111"),
        ("repository_id", "other/model"),
        ("commit_sha", "b" * 40),
        ("publication_id", "b" * 32),
        ("publication_generation", 2),
        ("manifest_path", "published/wrong.json"),
        ("manifest_digest", "b" * 64),
    ],
)
def test_observation_identity_must_agree_with_exact_authority(archive, field, value):
    published(archive)
    payload = examples.publication_observation().to_payload()
    payload[field] = value
    changed = PublicationObservation.model_validate(payload)
    with pytest.raises(HfcacheError), writer(archive) as store:
        store.write(changed)


@pytest.mark.parametrize("change", ["source", "source_digest", "member_size", "source_path"])
def test_sources_and_members_belong_to_authoritative_manifest(archive, change):
    published(archive)
    payload = examples.publication_observation().to_payload()
    if change == "source":
        payload["sources"][0]["path"] = "absent.json"
    elif change == "source_digest":
        payload["sources"][0]["sha256"] = "c" * 64
    elif change == "source_path":
        payload["variants"][0]["source_paths"] = ["absent.json"]
    else:
        payload["variants"][0]["members"][0]["size_bytes"] += 1
        payload["variants"][0]["total_bytes"] += 1

        payload["variants"][0]["variant_id"] = variant_identity(
            [VariantMember.model_validate(payload["variants"][0]["members"][0])]
        )
    with pytest.raises(HfcacheError), writer(archive) as store:
        store.write(PublicationObservation.model_validate(payload))


class CrashError(RuntimeError):
    pass


@pytest.mark.parametrize(
    ("point", "new_visible"),
    [
        ("before_file_fsync", False),
        ("after_file_fsync", False),
        ("before_rename", False),
        ("after_rename", True),
        ("before_directory_fsync", True),
        ("after_directory_fsync", True),
    ],
)
def test_crash_boundaries_expose_only_whole_old_or_new_record(archive, point, new_visible):
    old = examples.tag_snapshot()
    new = old.model_copy(update={"tags": ("vision",)})

    def crash(name):
        if name == point:
            raise CrashError

    with writer(archive) as store:
        path = store.write(old)
        with pytest.raises(CrashError):
            store.write(new, checkpoint=crash)
    assert path.read_bytes() == dump(new if new_visible else old)
    assert parse_record(RepositoryTagSnapshot, path.read_bytes()).tags == (
        ("vision",) if new_visible else old.tags
    )
    # Ambiguous temporary siblings survive; readers use only canonical whole records.
    assert (
        read_tag_snapshot(
            archive[0], RepositoryIdentity.of("model", old.repository_id), old.archive_id
        )
        is not None
    )


def test_two_record_updates_have_no_cross_file_atomicity_promise(archive):
    first = examples.tag_snapshot()
    second = first.model_copy(update={"repository_id": "other/model"})
    with writer(archive) as store:
        one, two = store.write(first), store.write(second)
        store.write(first.model_copy(update={"tags": ("new",)}))
    assert parse_record(RepositoryTagSnapshot, one.read_bytes()).tags == ("new",)
    assert parse_record(RepositoryTagSnapshot, two.read_bytes()) == second


def test_store_requires_live_caller_owned_lock_and_no_nested_acquisition(archive):
    layout, storage, table = archive
    with pytest.raises(SafetyError):
        CatalogWriter(layout, storage=storage, table=table)
    with writer(archive) as store:
        copied = contextvars.copy_context()
        store.write(examples.tag_snapshot())
    with pytest.raises(SafetyError):
        store.write(examples.tag_snapshot())
    with pytest.raises(SafetyError):
        copied.run(require_archive_lock)


@pytest.mark.parametrize(
    "condition", ["missing", "wrong", "local_fallback", "symlink_parent", "unknown_namespace"]
)
def test_initialized_archive_and_approved_namespace_only(archive, condition):
    layout, storage, table = archive
    original = layout.sentinel.read_bytes()
    if condition == "missing":
        layout.sentinel.unlink()
    elif condition == "wrong":
        layout.sentinel.write_bytes(
            original.replace(examples.ARCHIVE_ID.encode(), b"11111111-1111-4111-8111-111111111111")
        )
    elif condition == "local_fallback":
        table = ()
    elif condition == "symlink_parent":
        layout.metadata.symlink_to(layout.root.parent, target_is_directory=True)
    else:
        layout.metadata.mkdir()
        (layout.metadata / "unknown").mkdir()
    before = layout.sentinel.read_bytes() if layout.sentinel.exists() else None
    with (
        exclusive_lock(layout.root.parent / "lock", command="test", wait_seconds=0),
        pytest.raises(HfcacheError),
    ):
        CatalogWriter(layout, storage=storage, table=table)
    assert (layout.sentinel.read_bytes() if layout.sentinel.exists() else None) == before


def test_optional_extension_does_not_become_required_or_authorize_initialization(archive):
    layout, storage, table = archive
    initial = inspect_archive(layout, archive_id=storage.archive_id, table=table)
    assert initial.state == "initialized"
    with writer(archive) as store:
        store.write(examples.tag_snapshot())
    extended = inspect_archive(layout, archive_id=storage.archive_id, table=table)
    assert extended.state == "initialized"
    assert extended.missing_directories == ()
    (layout.published / "unknown").mkdir()
    assert inspect_archive(layout, archive_id=storage.archive_id, table=table).state == "unusable"
    (layout.published / "unknown").rmdir()
    layout.sentinel.unlink()
    assert inspect_archive(layout, archive_id=storage.archive_id, table=table).state == "unusable"


def test_writer_cannot_borrow_a_new_lock_lifetime(archive):
    layout, _, _ = archive
    with writer(archive) as store:
        store.write(examples.tag_snapshot())
    with (
        exclusive_lock(layout.root.parent / "new-lock", command="different", wait_seconds=0),
        pytest.raises(SafetyError),
    ):
        store.write(examples.tag_snapshot())


def test_skipped_preflight_evidence_does_not_grant_write_authority(archive):
    layout, storage, _ = archive
    checks = tuple(Check.skipped(name, "not proven") for name in CHECK_ORDER[1:12])
    with (
        exclusive_lock(layout.root.parent / "lock", command="test", wait_seconds=0),
        pytest.raises(SafetyError),
    ):
        CatalogWriter(layout, storage=storage, checks=checks)
    assert not layout.metadata.exists()


def test_unrelated_published_sibling_refuses_new_namespace(archive):
    layout, _, _ = archive
    unknown = layout.published / "unknown"
    unknown.mkdir()
    with pytest.raises(IntegrityError), writer(archive):
        pass
    assert unknown.is_dir()
    assert not layout.metadata.exists()


def test_supplied_unbounded_reader_cannot_bypass_record_byte_limit(archive):
    layout, _, _ = archive
    identity = RepositoryIdentity.of("model", examples.REPOSITORY_ID)
    with writer(archive) as store:
        path = store.write(examples.tag_snapshot())
    with path.open("wb") as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    with pytest.raises(QueryLimitError):
        read_tag_snapshot(layout, identity, examples.ARCHIVE_ID, reader=MetadataReader(layout.root))


def test_metadata_unknown_temp_names_refuse_and_supported_ones_remain(archive):
    with writer(archive) as store:
        path = store.write(examples.tag_snapshot())
    temporary = path.with_name(path.name + ".tmp-" + "a" * 16)
    temporary.write_bytes(b"ambiguous incomplete write")
    with writer(archive) as store:
        store.write(examples.tag_snapshot())
    assert temporary.read_bytes() == b"ambiguous incomplete write"
    unknown = path.with_name(path.name + ".tmp-unknown")
    unknown.write_bytes(b"unknown evidence")
    with pytest.raises(IntegrityError), writer(archive):
        pass
    assert unknown.read_bytes() == b"unknown evidence"


def test_copy_mode_retains_its_documented_hardlink_probe_exception(archive):
    layout, storage, table = archive
    with writer((layout, storage.model_copy(update={"publication_mode": "copy"}), table)) as store:
        store.write(examples.tag_snapshot())


@pytest.mark.parametrize("raw", [b"[" * 33 + b"]" * 33, b"[" + b"null," * 100001 + b"null]"])
def test_structure_is_bounded_before_json_container_allocation(monkeypatch, raw):
    def decoder_forbidden(*args, **kwargs):
        pytest.fail("over-budget JSON reached the container allocator")

    monkeypatch.setattr("hfcache.catalog_storage.json.loads", decoder_forbidden)
    with pytest.raises(IntegrityError):
        parse_record(RepositoryTagSnapshot, raw)
