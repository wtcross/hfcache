"""Owned WEB-022 fixture closure; local effects are not NFS/installed acceptance."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hfcache.catalog_capture import extract_publication
from hfcache.catalog_cards import capture_repository_card
from hfcache.catalog_extractors import SourceAccess
from hfcache.catalog_storage import read_publication_observation, read_repository_card
from hfcache.config import load_config
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, TransactionId, new_run_id
from hfcache.models import ArchiveSentinel, Reference
from hfcache.purge import apply_purge, plan_purge
from hfcache.quarantine import apply_quarantine_cleanup, plan_quarantine_cleanup
from hfcache.recovery import apply_recovery, plan_recovery
from hfcache.retention import apply_prune, ordered_revisions, plan_prune
from hfcache.services.queries import LocalQueries
from hfcache.verification import resolve_archive, verify_targets
from tests.fixtures import examples
from tests.web_functional_fixture import BROWSER_READMES, HOSTILE_README, seed_archive, snapshot

MODEL = RepositoryIdentity.of("model", "fixture/model")
UNMANAGED = RepositoryIdentity.of("dataset", "fixture/unmanaged")


@pytest.fixture
def rich(tmp_path):
    workspace = tmp_path / "fresh-owned"
    workspace.mkdir(mode=0o700)
    fixture = seed_archive(workspace, fixture_root=tmp_path, rich=True)
    queries = LocalQueries(load_config(Path(fixture["archive_config"])))
    return workspace, fixture, queries


def envelope(fixture, queries):
    original = examples.run_report().model_dump(mode="json")
    return {
        name: original[name]
        for name in (
            "application_version",
            "hostname",
            "huggingface_hub_version",
            "invocation_mode",
            "python_version",
        )
    } | {
        "archive_id": fixture["archive_id"],
        "config_fingerprint": queries.config.fingerprint(),
        "run_id": new_run_id(),
    }


def test_rich_seed_has_exact_manifest_bytes_current_and_uncaptured_inert_card(rich, tmp_path):
    workspace, fixture, queries = rich
    layout = queries.layout
    before = snapshot(workspace, fixture_root=tmp_path)
    # Unchanged full-read engine used by CommandServices.verify. No mount,
    # preflight, lock or persisted report is simulated by this local check.
    full = verify_targets(resolve_archive(layout), started_at=datetime.now(UTC))
    assert full.outcome == "clean"
    assert full.findings == ()
    assert full.repositories == 3
    assert full.revisions == 7
    assert full.objects_read == 12
    assert full.bytes_read > 0
    assert fixture["archive_id"] != examples.ARCHIVE_ID
    assert (
        ArchiveSentinel.model_validate_json(layout.sentinel.read_bytes()).archive_id
        == fixture["archive_id"]
    )
    assert queries.config.storage.maximum_revisions == 3
    assert {entry.id for entry in queries.config.repositories} == {"fixture/model", "fixture/data"}
    revisions = ordered_revisions(layout, MODEL)
    assert [item.publication_generation for item in revisions] == [1, 2, 3, 4, 5]
    current = revisions[-1]
    repository = layout.repository(MODEL)
    assert Reference.model_validate_json(repository.current_ref.read_bytes()) == current.reference
    assert current.commit_sha == fixture["rich"]["current_commit_sha"]
    for revision in revisions:
        manifest = revision.manifest
        tree = layout.root / manifest.tree
        assert {item.path for item in manifest.files} == {"README.md", "model-Q4_K_M.gguf"}
        assert manifest.file_count == 2
        assert manifest.total_bytes == sum(item.size for item in manifest.files)
        for item in manifest.files:
            raw = (tree / item.path).read_bytes()
            assert item.size == len(raw)
            assert item.sha256 == hashlib.sha256(raw).hexdigest()
        assert (tree / "README.md").read_bytes() == HOSTILE_README
        assert (
            read_repository_card(
                layout,
                MODEL,
                CommitSha(manifest.commit_sha),
                PublicationId(manifest.publication_id),
                fixture["archive_id"],
            )
            is None
        )
    # Exercise the real parser without writing an adjunct or declaring an
    # installed capture/rendering success in fixture metadata (ADR142).
    technical = extract_publication(SourceAccess(layout, current.manifest))
    assert technical.status == "complete"
    assert len(technical.variants) == 1
    card = capture_repository_card(
        SourceAccess(layout, current.manifest),
        hashlib.sha256(
            repository.manifest(
                CommitSha(current.commit_sha), PublicationId(current.reference.publication_id)
            ).read_bytes()
        ).hexdigest(),
        archive_id=fixture["archive_id"],
    )
    assert card.state == "present"
    assert card.expected_source_sha256 == fixture["rich"]["readme_sha256"]
    assert card.markdown is not None
    assert "<script>" in card.markdown
    assert r"\[image omitted\]" in card.markdown
    assert "tracker.svg" not in card.markdown
    assert snapshot(workspace, fixture_root=tmp_path) == before


def test_browser_current_model_extracts_six_real_variant_roles_without_changing_corpus_counts(
    tmp_path,
):
    workspace = tmp_path / "browser-owned"
    workspace.mkdir(mode=0o700)
    fixture = seed_archive(workspace, fixture_root=tmp_path, rich=True, browser_reads=True)
    queries = LocalQueries(load_config(Path(fixture["archive_config"])))
    layout = queries.layout
    current = ordered_revisions(layout, MODEL)[-1]
    manifest = current.manifest
    tree = layout.root / manifest.tree
    assert len(queries.config.repositories) == 28
    assert fixture["browser_reads"]["repository_union_count"] == 29
    assert len(list(layout.manifests.rglob("*.json"))) == 7
    assert manifest.file_count == 8
    assert manifest.total_bytes == 6777
    assert (tree / "README.md").read_bytes() == BROWSER_READMES[15]
    for item in manifest.files:
        raw = (tree / item.path).read_bytes()
        assert len(raw) == item.size
        assert hashlib.sha256(raw).hexdigest() == item.sha256
    extracted = extract_publication(SourceAccess(layout, manifest))
    assert extracted.status == "partial"
    expected = {
        "primary-q4.gguf": ("primary", "complete", "gguf", "ggml", "Q4_0", 4, 1184),
        "gptq/config.json": ("primary", "complete", "safetensors", "gptq", None, 8, 84),
        "adapter-q8.gguf": ("adapter", "complete", "gguf", "ggml", "Q8_0", 8, 1216),
        "mmproj-q4.gguf": ("projector", "complete", "gguf", "ggml", "Q4_1", 4, 1216),
        "future-q5.gguf": ("unknown", "complete", "gguf", "ggml", "Q5_0", 5, 1184),
        "split-q2-00001-of-00002.gguf": (
            "primary",
            "incomplete",
            "gguf",
            "ggml",
            "Q2_K",
            None,
            1248,
        ),
    }
    assert {
        variant.source_paths[0]: (
            variant.role,
            variant.completeness,
            variant.format,
            variant.quantization_method,
            variant.quantization,
            variant.bits,
            variant.total_bytes,
        )
        for variant in extracted.variants
    } == expected
    observation = read_publication_observation(
        layout,
        MODEL,
        CommitSha(current.commit_sha),
        PublicationId(current.reference.publication_id),
        fixture["archive_id"],
    )
    assert observation is not None
    assert observation.status == extracted.status
    assert observation.variants == extracted.variants
    card = read_repository_card(
        layout,
        MODEL,
        CommitSha(current.commit_sha),
        PublicationId(current.reference.publication_id),
        fixture["archive_id"],
    )
    assert card is not None
    assert card.state == "present"
    assert card.expected_source_sha256 == hashlib.sha256(BROWSER_READMES[15]).hexdigest()


def test_rich_upstream_git_objects_match_independent_git_hash_object_audit(rich):
    _workspace, _fixture, queries = rich
    # Independently obtained with git hash-object on the fixture source files;
    # this checks transport provenance separately from strong SHA-256 verification.
    expected = {
        "README.md": "fa414b4869b8d68dbcdf85bc4cfb35300b8822b2",
        "model-Q4_K_M.gguf": "b7dbc9b706ae7b511ea2d72471902d16c04c837a",
        "data.json": "4d8345651cdb2f6c1987b4868bcf18cd0fe11880",
    }
    entries = [
        entry
        for identity in (MODEL, RepositoryIdentity.of("dataset", "fixture/data"), UNMANAGED)
        for revision in ordered_revisions(queries.layout, identity)
        for entry in revision.manifest.files
    ]
    assert len(entries) == 12
    for entry in entries:
        assert entry.upstream.git_oid == expected[entry.path]
        assert entry.upstream.lfs_sha256 is None
        assert entry.upstream.xet_hash is None


def test_rich_recovery_quarantine_prune_and_purge_use_original_effects(rich, tmp_path):
    workspace, fixture, queries = rich
    layout = queries.layout
    details = fixture["rich"]
    stamp = datetime.now(UTC)
    before = snapshot(workspace, fixture_root=tmp_path)
    recovery = plan_recovery(layout, stale_staging_age_hours=24, now=stamp)
    assert not recovery.blocked
    assert len(recovery.actionable) == 1
    assert recovery.actionable[0].transaction_id == details["pending_recovery_transaction_id"]
    assert recovery.actionable[0].remedy == "quarantine_staging"
    assert snapshot(workspace, fixture_root=tmp_path) == before
    apply_recovery(layout, recovery, envelope=envelope(fixture, queries), started_at=stamp)
    assert not plan_recovery(layout, stale_staging_age_hours=24, now=stamp).actionable

    unknown = {
        relative: (layout.root / relative).read_bytes() for relative in details["unknown_files"]
    }
    current = layout.repository(MODEL).current_ref.read_bytes()
    retained = {
        str(path.relative_to(layout.root)): path.read_bytes()
        for path in layout.repository(MODEL).manifests.glob("*/*.json")
    }
    before_plans = snapshot(workspace, fixture_root=tmp_path)
    quarantine = plan_quarantine_cleanup(
        layout, TransactionId(details["completed_quarantine_transaction_id"])
    )
    prune = plan_prune(layout, MODEL, maximum=3, generated_at=stamp)
    purge = plan_purge(layout, UNMANAGED, generated_at=stamp)
    assert snapshot(workspace, fixture_root=tmp_path) == before_plans
    assert quarantine.logical_bytes > 0
    assert len(quarantine.files) == 1
    assert prune is not None
    assert prune.selected.commit_sha == details["prune_candidate_commit_sha"]
    assert prune.selected.commit_sha != details["current_commit_sha"]
    assert purge is not None
    assert len(purge.revisions) == 1
    result = apply_quarantine_cleanup(layout, quarantine)
    assert result["removed_files"] == 1
    assert result["removed_logical_bytes"] > 0
    apply_prune(layout, prune, envelope=envelope(fixture, queries), now=stamp)
    records = apply_purge(layout, purge, envelope=envelope(fixture, queries), now=stamp)
    assert len(records) == 1
    assert len(ordered_revisions(layout, MODEL)) == 4  # One round, not bulk retention.
    assert layout.repository(MODEL).current_ref.read_bytes() == current
    assert not layout.repository(UNMANAGED).directory.exists()
    assert not layout.repository(UNMANAGED).manifests.exists()
    for relative, raw in retained.items():
        path = layout.root / relative
        if path.exists():
            assert path.read_bytes() == raw
    removed = prune.selected
    archived = layout.repository(MODEL).pruned_manifest(
        CommitSha(removed.commit_sha), PublicationId(removed.publication_id)
    )
    assert archived.read_bytes() == retained[removed.manifest]
    for relative, raw in unknown.items():
        assert (layout.root / relative).read_bytes() == raw


def test_seed_refuses_parent_alias_before_writing(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir(mode=0o700)
    workspace = actual / "fresh"
    workspace.mkdir(mode=0o700)
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError, match="descendant"):
        seed_archive(alias / "fresh", fixture_root=tmp_path, rich=True)
    assert list(workspace.iterdir()) == []
