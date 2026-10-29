"""Fresh authority/accounting with bounded exact-byte parsing reuse (FS-09/FS-15).

Parsed models never substitute for a fresh anchored read or a publication join.
"""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

import hfcache.catalog_storage as storage
from hfcache.errors import HfcacheError, IntegrityError
from hfcache.identity import CommitSha, PublicationId
from hfcache.metadata import MetadataReader, QueryBounds, QueryLimitError
from hfcache.models import Reference, TransactionJournal, dump
from hfcache.paths import ArchiveLayout
from tests.fixtures import examples


@pytest.fixture
def authority_parser():
    caches = (storage._cached_manifest, storage._cached_reference)
    for cache in caches:
        cache.cache_clear()

    def info():
        return {
            "manifest": storage._cached_manifest.cache_info()._asdict(),
            "reference": storage._cached_reference.cache_info()._asdict(),
        }

    yield storage.read_authority, info
    for cache in caches:
        cache.cache_clear()
    assert info()["reference"]["currsize"] == info()["manifest"]["currsize"] == 0


def raw_record(model, *, size=None, generation=1):
    record = (examples.reference() if model is Reference else examples.manifest()).model_copy(
        update={"publication_generation": generation}
    )
    raw = dump(record)
    if size is not None:
        assert size >= len(raw)
        raw += b" " * (size - len(raw))
    return raw


def write_record(tmp_path, model, *, size=None, generation=1, name="authority.json"):
    path = tmp_path / name
    raw = raw_record(model, size=size, generation=generation)
    path.write_bytes(raw)
    return path, raw


def observed(read, path, model, reader, **kwargs):
    try:
        value, digest = read(path, model, reader, **kwargs)
    except HfcacheError as exc:
        return type(exc).__name__, tuple((p.code, p.message, p.location) for p in exc.problems)
    except FileNotFoundError:
        return ("FileNotFoundError",)
    return "success", value.to_payload(), digest


@pytest.mark.parametrize("model", [Reference, storage.RevisionManifest])
def test_warm_fresh_reads_charge_each_query_and_return_exact_raw_digest(
    authority_parser, tmp_path, model
):
    read, info = authority_parser
    path, raw = write_record(tmp_path, model, size=65536 if model is not Reference else None)
    first, digest = read(path, model, MetadataReader(tmp_path))
    assert first.to_payload() == json.loads(raw)
    reader = MetadataReader(
        tmp_path, QueryBounds(maximum_entries=2, maximum_total_bytes=2 * len(raw))
    )
    for _ in range(2):
        value, current_digest = read(path, model, reader)
        assert value.to_payload() == first.to_payload()
        assert current_digest == digest == hashlib.sha256(raw).hexdigest()
    assert reader._entries == 2
    assert reader._bytes == 2 * len(raw)
    family = "reference" if model is Reference else "manifest"
    assert info()[family]["hits"] >= 2
    with pytest.raises(QueryLimitError):
        read(path, model, reader)
    # The same cached bytes in a fresh query are charged anew and remain valid.
    fresh = MetadataReader(tmp_path, QueryBounds(maximum_entries=1, maximum_total_bytes=len(raw)))
    assert read(path, model, fresh)[1] == digest
    assert fresh._entries == 1
    assert fresh._bytes == len(raw)


@pytest.mark.parametrize("model", [Reference, storage.RevisionManifest])
def test_atomic_equal_size_equal_mtime_replacement_is_fresh_authority(
    authority_parser, tmp_path, model
):
    read, _ = authority_parser
    size = 65536 if model is not Reference else 4096
    path, raw = write_record(tmp_path, model, size=size)
    old, digest = read(path, model, MetadataReader(tmp_path))
    before = path.stat()
    replacement, new_raw = write_record(
        tmp_path, model, size=size, generation=2, name="replacement.json"
    )
    os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
    replacement.replace(path)
    after = path.stat()
    assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)
    assert after.st_ino != before.st_ino
    assert new_raw != raw
    current, current_digest = read(path, model, MetadataReader(tmp_path))
    assert current.publication_generation == 2
    assert old.publication_generation == 1
    assert current_digest == hashlib.sha256(new_raw).hexdigest() != digest
    assert current.to_payload() == json.loads(new_raw)


@pytest.mark.parametrize("model", [Reference, storage.RevisionManifest])
@pytest.mark.parametrize(
    "damage",
    ["invalid-json", "future-schema", "invalid-field", "missing", "leaf-symlink", "parent-symlink"],
)
def test_warm_cache_never_resurrects_damaged_or_removed_authority(
    authority_parser, tmp_path, model, damage
):
    read, _ = authority_parser
    archive = tmp_path / "archive"
    archive.mkdir()
    nested = archive / "nested"
    nested.mkdir()
    path, raw = write_record(nested, model, size=65536 if model is not Reference else None)
    read(path, model, MetadataReader(archive))
    if damage == "invalid-json":
        path.write_bytes(b"not JSON" + b" " * (len(raw) - 8))
    elif damage in {"future-schema", "invalid-field"}:
        payload = json.loads(raw)
        payload["schema_version" if damage == "future-schema" else "publication_generation"] = (
            2 if damage == "future-schema" else "2"
        )
        path.write_text(json.dumps(payload))
    elif damage == "missing":
        path.unlink()
    elif damage == "leaf-symlink":
        external = tmp_path / "external-valid.json"
        external.write_bytes(raw)
        path.unlink()
        path.symlink_to(external)
    else:
        retained = tmp_path / "retained-real-directory"
        nested.rename(retained)
        nested.symlink_to(retained, target_is_directory=True)
    actual = observed(read, path, model, MetadataReader(archive))
    assert actual[0] == "IntegrityError"
    assert all(problem[0] == "HFVER007" for problem in actual[1])
    if damage == "missing":
        assert observed(read, path, model, MetadataReader(archive), missing_ok=True) == (
            "FileNotFoundError",
        )


@pytest.mark.parametrize("model", [Reference, storage.RevisionManifest])
@pytest.mark.parametrize("bound", ["artifact", "total", "entries"])
def test_cached_value_does_not_bypass_per_query_caps(authority_parser, tmp_path, model, bound):
    read, _ = authority_parser
    path, raw = write_record(tmp_path, model, size=65536 if model is not Reference else None)
    read(path, model, MetadataReader(tmp_path))
    if bound == "artifact":
        bounds = QueryBounds(maximum_artifact_bytes=len(raw) - 1)
        reader = MetadataReader(tmp_path, bounds)
    elif bound == "total":
        bounds = QueryBounds(maximum_total_bytes=2 * len(raw) - 1)
        reader = MetadataReader(tmp_path, bounds)
        read(path, model, reader)
    else:
        bounds = QueryBounds(maximum_entries=1)
        reader = MetadataReader(tmp_path, bounds)
        # A real directory traversal consumes the shared entry before the read.
        assert len(reader.entries(tmp_path)) == 1
    with pytest.raises(QueryLimitError) as refusal:
        read(path, model, reader)
    assert refusal.value.problems[0].code == "HFAPI005"
    assert path.read_bytes() == raw


@pytest.mark.parametrize("model", [Reference, storage.RevisionManifest])
@pytest.mark.parametrize("limit", ["MAXIMUM_JSON_DEPTH", "MAXIMUM_JSON_NODES"])
def test_structural_limit_changes_revalidate_warm_bytes(
    authority_parser, tmp_path, monkeypatch, model, limit
):
    read, info = authority_parser
    path, raw = write_record(tmp_path, model, size=65536 if model is not Reference else None)
    read(path, model, MetadataReader(tmp_path))
    original_limit = getattr(storage, limit)
    monkeypatch.setattr(storage, limit, 1)
    before = info()
    actual = observed(read, path, model, MetadataReader(tmp_path))
    family = "reference" if model is Reference else "manifest"
    assert info()[family]["misses"] == before[family]["misses"] + 1
    # A flat Reference still fits depth1; manifests have real nested containers.
    # The node1 budget rejects both families without using an old validated object.
    assert actual[0] == (
        "success" if model is Reference and limit == "MAXIMUM_JSON_DEPTH" else "IntegrityError"
    )
    monkeypatch.setattr(storage, limit, original_limit)
    assert read(path, model, MetadataReader(tmp_path))[1] == hashlib.sha256(raw).hexdigest()


def test_uncached_journal_mutable_evidence_cannot_contaminate_the_next_read(
    authority_parser, tmp_path
):
    read, info = authority_parser
    path = tmp_path / "journal.json"
    raw = dump(examples.journal())
    path.write_bytes(raw)
    before = info()
    first, digest = read(path, TransactionJournal, MetadataReader(tmp_path))
    first.checkpoints[0].evidence["file_count"] = "poisoned process-only mutation"
    second, second_digest = read(path, TransactionJournal, MetadataReader(tmp_path))
    assert second.checkpoints[0].evidence["file_count"] == 2
    assert first is not second
    assert first.checkpoints[0].evidence is not second.checkpoints[0].evidence
    assert digest == second_digest == hashlib.sha256(raw).hexdigest()
    assert info() == before
    assert path.read_bytes() == raw


@pytest.mark.parametrize("model", [Reference, storage.RevisionManifest])
def test_cached_families_reject_normal_top_level_and_nested_mutation(
    authority_parser, tmp_path, model
):
    read, _ = authority_parser
    path, raw = write_record(tmp_path, model, size=65536 if model is not Reference else None)
    value, _ = read(path, model, MetadataReader(tmp_path))
    expected = value.to_payload()
    with pytest.raises(ValidationError):
        value.publication_generation = 999
    if model is storage.RevisionManifest:
        with pytest.raises(TypeError):
            value.files[0] = value.files[1]
        with pytest.raises(ValidationError):
            value.files[0].provenance.hashed = False
        with pytest.raises(ValidationError):
            value.files[0].upstream.git_oid = "changed"
        with pytest.raises(ValidationError):
            value.files[1].provenance.hash_reused_from.commit_sha = "f" * 40
        with pytest.raises(ValidationError):
            value.dependencies[0].detected_id = "changed"
        with pytest.raises(ValidationError):
            value.verification.hashed_bytes = 999
    assert read(path, model, MetadataReader(tmp_path))[0].to_payload() == expected
    assert path.read_bytes() == raw


@pytest.mark.parametrize(
    ("model", "size"),
    [
        (Reference, 4096),
        (Reference, 4097),
        (storage.RevisionManifest, 65535),
        (storage.RevisionManifest, 65536),
        (storage.RevisionManifest, 8 * 1024 * 1024),
        (storage.RevisionManifest, 8 * 1024 * 1024 + 1),
    ],
)
def test_valid_byte_size_boundaries_select_only_declared_cache_families(
    authority_parser, tmp_path, model, size
):
    read, info = authority_parser
    path, raw = write_record(tmp_path, model, size=size)
    before = info()
    expected = "success", json.loads(raw), hashlib.sha256(raw).hexdigest()
    assert observed(read, path, model, MetadataReader(tmp_path)) == expected
    assert observed(read, path, model, MetadataReader(tmp_path)) == expected
    eligible = size <= 4096 if model is Reference else 65536 <= size <= 8 * 1024 * 1024
    family = "reference" if model is Reference else "manifest"
    assert info()[family]["currsize"] == int(eligible)
    assert info()[family]["hits"] - before[family]["hits"] == int(eligible)
    assert path.read_bytes() == raw


def test_internal_record_ceiling_still_applies_with_unbounded_reader(authority_parser, tmp_path):
    read, _ = authority_parser
    path, _raw = write_record(tmp_path, storage.RevisionManifest, size=65536)
    read(path, storage.RevisionManifest, MetadataReader(tmp_path))
    with path.open("r+b") as output:
        output.truncate(storage.MAXIMUM_RECORD_BYTES + 1)
    with pytest.raises(QueryLimitError) as refusal:
        read(path, storage.RevisionManifest, MetadataReader(tmp_path))
    assert refusal.value.problems[0].code == "HFAPI005"


@pytest.mark.parametrize("model", [Reference, storage.RevisionManifest])
def test_parse_failure_is_not_retained_and_a_repaired_file_is_read_fresh(
    authority_parser, tmp_path, model
):
    read, info = authority_parser
    size = 65536 if model is not Reference else 4096
    path, raw = write_record(tmp_path, model, size=size)
    first, digest = read(path, model, MetadataReader(tmp_path))
    family = "reference" if model is Reference else "manifest"
    before = info()[family].copy()
    for version in range(2, 6):
        payload = json.loads(raw)
        payload["schema_version"] = version
        damaged = json.dumps(payload).encode()
        damaged += b" " * (size - len(damaged))
        path.write_bytes(damaged)
        for _ in range(2):
            with pytest.raises(IntegrityError):
                read(path, model, MetadataReader(tmp_path))
        assert info()[family]["currsize"] == before["currsize"]
    assert info()[family]["misses"] == before["misses"] + 8
    path.write_bytes(raw)
    fresh = MetadataReader(tmp_path, QueryBounds(maximum_entries=1, maximum_total_bytes=size))
    restored, restored_digest = read(path, model, fresh)
    assert restored == first
    assert restored_digest == digest
    assert fresh._entries == 1
    assert fresh._bytes == size


def test_reference_eviction_stays_bounded_and_evicted_bytes_reparse(authority_parser, tmp_path):
    read, info = authority_parser
    path, first = write_record(tmp_path, Reference, size=4096)
    first_value, first_digest = read(path, Reference, MetadataReader(tmp_path))
    for generation in range(2, 515):
        path.write_bytes(raw_record(Reference, size=4096, generation=generation))
        value, _ = read(path, Reference, MetadataReader(tmp_path))
        assert value.publication_generation == generation
        assert info()["reference"]["currsize"] <= 512
    assert info()["reference"]["currsize"] == 512
    before = info()["reference"].copy()
    path.write_bytes(first)
    restored, digest = read(path, Reference, MetadataReader(tmp_path))
    assert restored == first_value
    assert digest == first_digest
    assert restored is not first_value
    assert info()["reference"]["misses"] == before["misses"] + 1
    large, _ = write_record(
        tmp_path, storage.RevisionManifest, size=8 * 1024 * 1024, name="maximum.json"
    )
    read(large, storage.RevisionManifest, MetadataReader(tmp_path))
    assert info()["manifest"]["currsize"] == 1
    assert info()["reference"]["currsize"] == 512
    # Maximum-size admitted keys occupy both families together. This is an
    # encoded-key bound; decoded models, live readers and heap have other costs.
    assert info()["reference"]["maxsize"] == 512
    assert info()["manifest"]["maxsize"] == 1


@pytest.mark.parametrize(
    "damage", ["reference-generation", "reference-tree", "manifest-generation", "manifest-identity"]
)
def test_publication_binding_rechecks_join_context_around_cached_models(
    authority_parser, tmp_path, damage
):
    read, _ = authority_parser
    layout = ArchiveLayout(tmp_path)
    manifest = examples.manifest()
    repository = layout.repository(manifest.identity)
    sha, publication = CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id)
    manifest_path = repository.manifest(sha, publication)
    reference_path = repository.revision_ref(sha)
    manifest_path.parent.mkdir(parents=True)
    reference_path.parent.mkdir(parents=True)
    manifest_path.write_bytes(raw_record(storage.RevisionManifest, size=65536))
    reference_path.write_bytes(raw_record(Reference))
    original = storage.publication_binding(
        layout, manifest.identity, sha, publication, reader=MetadataReader(tmp_path)
    )
    assert (
        storage.publication_binding(
            layout, manifest.identity, sha, publication, reader=MetadataReader(tmp_path)
        )
        == original
    )
    if damage.startswith("reference"):
        payload = json.loads(reference_path.read_bytes())
        payload["publication_generation" if damage.endswith("generation") else "tree"] = (
            2 if damage.endswith("generation") else "repos/models/foreign/model/tree"
        )
        reference_path.write_text(json.dumps(payload))
    else:
        payload = json.loads(manifest_path.read_bytes())
        payload["publication_generation" if damage.endswith("generation") else "repository_id"] = (
            2 if damage.endswith("generation") else "foreign/model"
        )
        manifest_path.write_text(json.dumps(payload))
    # Both independent models remain valid; only their publication context no
    # longer agrees, so the real binding layer must still reject the pair.
    read(reference_path, Reference, MetadataReader(tmp_path))
    read(manifest_path, storage.RevisionManifest, MetadataReader(tmp_path))
    with pytest.raises(IntegrityError) as refusal:
        storage.publication_binding(
            layout, manifest.identity, sha, publication, reader=MetadataReader(tmp_path)
        )
    assert all(problem.code == "HFVER007" for problem in refusal.value.problems)


def test_one_large_manifest_retained_and_small_records_do_not_evict_it(authority_parser, tmp_path):
    read, info = authority_parser
    large, raw = write_record(tmp_path, storage.RevisionManifest, size=65536, name="large.json")
    first, _ = read(large, storage.RevisionManifest, MetadataReader(tmp_path))
    small = tmp_path / "small.json"
    for generation in range(2, 12):
        small.write_bytes(raw_record(storage.RevisionManifest, generation=generation))
        assert (
            read(small, storage.RevisionManifest, MetadataReader(tmp_path))[
                0
            ].publication_generation
            == generation
        )
        assert info()["manifest"]["currsize"] == 1
    before = info()["manifest"].copy()
    again, _ = read(large, storage.RevisionManifest, MetadataReader(tmp_path))
    assert again is first
    assert info()["manifest"]["hits"] == before["hits"] + 1
    second = tmp_path / "second-large.json"
    second.write_bytes(raw_record(storage.RevisionManifest, size=65537, generation=2))
    read(second, storage.RevisionManifest, MetadataReader(tmp_path))
    assert info()["manifest"]["currsize"] == 1
    assert read(large, storage.RevisionManifest, MetadataReader(tmp_path))[0] == first
    assert large.read_bytes() == raw


def test_concurrent_fresh_file_reads_preserve_results_and_finite_cache(authority_parser, tmp_path):
    read, info = authority_parser
    paths = [
        write_record(tmp_path, Reference, generation=n + 1, name=f"ref-{n}.json")[0]
        for n in range(8)
    ]

    def query(index):
        path = paths[index % len(paths)]
        reader = MetadataReader(tmp_path, QueryBounds(maximum_entries=1, maximum_total_bytes=4096))
        value, digest = read(path, Reference, reader)
        assert value.publication_generation == index % len(paths) + 1
        assert reader._entries == 1
        assert reader._bytes == len(path.read_bytes())
        return digest

    with ThreadPoolExecutor(max_workers=8) as workers:
        results = list(workers.map(query, range(128)))
    assert len(results) == 128
    assert len(set(results)) == 8
    assert info()["reference"]["currsize"] <= 8
    assert info()["manifest"]["currsize"] == 0


@pytest.mark.parametrize(
    ("model", "size"),
    [
        (Reference, 4097),
        (storage.RevisionManifest, 65535),
        (storage.RevisionManifest, 8 * 1024 * 1024 + 1),
    ],
)
def test_private_cache_helpers_reject_valid_records_outside_their_admission_size(
    authority_parser, tmp_path, model, size
):
    read, info = authority_parser
    path, raw = write_record(tmp_path, model, size=size)
    expected = "success", json.loads(raw), hashlib.sha256(raw).hexdigest()
    assert observed(read, path, model, MetadataReader(tmp_path)) == expected
    before = info()
    helper = storage._cached_reference if model is Reference else storage._cached_manifest
    with pytest.raises(IntegrityError) as refusal:
        helper(raw, (storage.MAXIMUM_JSON_DEPTH, storage.MAXIMUM_JSON_NODES))
    assert all(problem.code == "HFVER007" for problem in refusal.value.problems)
    assert info()["reference"]["currsize"] == before["reference"]["currsize"]
    assert info()["manifest"]["currsize"] == before["manifest"]["currsize"]


def test_other_frozen_model_families_are_uncached(authority_parser, tmp_path):
    read, info = authority_parser
    path = tmp_path / "sentinel.json"
    raw = dump(examples.sentinel())
    path.write_bytes(raw)
    before = info()
    first, digest = read(path, storage.ArchiveSentinel, MetadataReader(tmp_path))
    second, second_digest = read(path, storage.ArchiveSentinel, MetadataReader(tmp_path))
    assert first is not second
    assert first.to_payload() == second.to_payload() == json.loads(raw)
    assert digest == second_digest == hashlib.sha256(raw).hexdigest()
    assert info() == before


@pytest.mark.parametrize("model", [Reference, storage.RevisionManifest])
def test_cached_bytes_cannot_be_reused_for_a_different_model_family(
    authority_parser, tmp_path, model
):
    read, info = authority_parser
    path, _ = write_record(tmp_path, model, size=65536 if model is not Reference else 4096)
    read(path, model, MetadataReader(tmp_path))
    before = info()
    other = storage.RevisionManifest if model is Reference else Reference
    reader = MetadataReader(tmp_path)
    with pytest.raises(IntegrityError):
        read(path, other, reader)
    assert reader._entries == 1
    assert reader._bytes == path.stat().st_size
    assert info()["manifest"]["hits"] == before["manifest"]["hits"]
    assert info()["reference"]["hits"] == before["reference"]["hits"]


def test_cached_repair_provenance_is_frozen(authority_parser, tmp_path):
    read, _ = authority_parser
    expected = examples.repair_manifest()
    raw = dump(expected)
    raw += b" " * (65536 - len(raw))
    path = tmp_path / "repair.json"
    path.write_bytes(raw)
    manifest, _ = read(path, storage.RevisionManifest, MetadataReader(tmp_path))
    with pytest.raises(ValidationError):
        manifest.repair.reason = "process mutation"
    assert read(path, storage.RevisionManifest, MetadataReader(tmp_path))[0] == expected
