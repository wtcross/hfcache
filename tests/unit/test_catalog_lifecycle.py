"""V23-V25: joined optional capture preserves exact immutable publication authority."""

import hashlib
import json
from dataclasses import replace
from threading import Event, Thread

import pytest

from hfcache import catalog_capture
from hfcache.catalog_extractors import ExtractionBudget
from hfcache.catalog_models import PublicationObservation
from hfcache.catalog_storage import CatalogWriter, read_publication_observation, read_tag_snapshot
from hfcache.errors import IntegrityError, Problem, SafetyError
from hfcache.hub import HubClient
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.locking import exclusive_lock, lock_path, require_archive_lock
from hfcache.metadata import MetadataReader
from hfcache.publication import read_reference
from hfcache.services.commands import CommandServices, RepairRequest
from hfcache.services.context import ExecutionContext
from tests.fixtures.gguf import gguf
from tests.unit import test_synchronize as sync_fixtures
from tests.unit.test_synchronize import (
    ARCHIVE_ID,
    MODEL,
    SHA_A,
)

_local_lock = sync_fixtures._local_lock
config = sync_fixtures.config
hub = sync_fixtures.hub
client = sync_fixtures.client
layout = sync_fixtures.layout


def curated(config, tags, *, enabled=True):
    repository = config.repositories[0].model_copy(update={"tags": tags, "enabled": enabled})
    return config.model_copy(update={"repositories": (repository,)})


@pytest.fixture
def service(config, hub, client, monkeypatch):
    hub.revisions[SHA_A] = {"model.gguf": gguf()[0]}
    monkeypatch.setattr(HubClient, "of", lambda *_a, **_kw: client)
    return CommandServices(curated(config, ("original",)), ExecutionContext.create())


def reference(layout):
    return read_reference(layout, layout.repository(MODEL).revision_ref(CommitSha(SHA_A)))


def observation(layout):
    ref = reference(layout)
    return read_publication_observation(
        layout, MODEL, CommitSha(SHA_A), PublicationId(ref.publication_id), ARCHIVE_ID
    )


def test_sync_binds_exact_new_publication_without_changing_manifest(service, layout):
    result = service.synchronize()
    assert result.exit_code == 0
    assert result.payload["repositories"][0]["status"] == "published"
    ref = reference(layout)
    path = layout.repository(MODEL).manifest(CommitSha(SHA_A), PublicationId(ref.publication_id))
    before = path.read_bytes()
    record = observation(layout)
    assert isinstance(record, PublicationObservation)
    assert record.status == "complete"
    assert record.publication_id == ref.publication_id
    assert record.publication_generation == ref.publication_generation
    assert record.manifest_digest == hashlib.sha256(before).hexdigest()
    assert record.variants[0].quantization == "Q4_K_M"
    assert path.read_bytes() == before
    tags = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
    assert tags is not None
    assert tags.tags == ("original",)
    assert tags.curation_fingerprint == service.config.curation_fingerprint()


@pytest.mark.parametrize("tags", [(), ("changed",)])
@pytest.mark.parametrize("enabled", [True, False])
def test_retained_sync_captures_current_tags_without_download_or_generation(
    service, layout, hub, tags, enabled
):
    assert service.synchronize().exit_code == 0
    before = reference(layout)
    path = layout.repository(MODEL).manifest(CommitSha(SHA_A), PublicationId(before.publication_id))
    original = path.read_bytes()
    downloads = tuple(hub.downloads)
    current = curated(service.config, tags, enabled=enabled)
    service = replace(service, curation_source=lambda: current)
    result = service.synchronize()
    assert result.exit_code == 0
    assert result.payload["repositories"][0]["status"] == "skipped"
    assert tuple(hub.downloads) == downloads
    assert reference(layout) == before
    assert path.read_bytes() == original
    snapshot = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
    assert snapshot is not None
    assert snapshot.tags == tags
    assert snapshot.curation_fingerprint == current.curation_fingerprint()
    assert service.config.repositories[0].tags == ("original",)


def test_removed_entry_never_invents_or_erases_historical_tags(service, layout):
    service = replace(
        service, curation_source=lambda: service.config.model_copy(update={"repositories": ()})
    )
    assert service.synchronize().exit_code == 0
    assert read_tag_snapshot(layout, MODEL, ARCHIVE_ID) is None
    service = replace(service, curation_source=None)
    assert service.synchronize().exit_code == 0
    before = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
    service = replace(
        service, curation_source=lambda: service.config.model_copy(update={"repositories": ()})
    )
    assert service.synchronize().exit_code == 0
    assert read_tag_snapshot(layout, MODEL, ARCHIVE_ID) == before


def test_unavailable_current_curation_does_not_fall_back_or_block_technical_capture(
    service, layout
):
    def unavailable():
        msg = "private source failure"
        raise ValueError(msg)

    service = replace(service, curation_source=unavailable)
    result = service.synchronize()
    assert result.exit_code == 0
    assert [warning.code for warning in result.warnings] == ["HFWRN011"]
    assert read_tag_snapshot(layout, MODEL, ARCHIVE_ID) is None
    record = observation(layout)
    assert record is not None
    assert record.status == "complete"
    assert "private source failure" not in str(result)


def test_extractor_defect_records_failed_coverage_without_invalidating_publication(
    service, layout, monkeypatch
):
    def failed(_access):
        msg = "private parser input must not appear"
        raise RuntimeError(msg)

    monkeypatch.setattr(catalog_capture, "extract_publication", failed)
    result = service.synchronize()
    assert result.exit_code == 0
    assert result.payload["repositories"][0]["status"] == "completed_with_warnings"
    assert [warning.code for warning in result.warnings] == ["HFWRN011"]
    record = observation(layout)
    assert record is not None
    assert record.status == "failed"
    assert record.diagnostics == ("extractor_failure",)
    assert "private parser input" not in record.model_dump_json()
    assert (
        layout.repository(MODEL)
        .instance(CommitSha(SHA_A), PublicationId(record.publication_id))
        .is_dir()
    )


@pytest.mark.parametrize("failure", ["constructor", "write", "capacity", "records", "bytes"])
def test_optional_store_failures_preserve_success_and_valid_publication(
    service, layout, monkeypatch, failure
):
    def failed(*_a, **_kw):
        msg = "injected optional storage failure"
        raise OSError(msg)

    if failure == "constructor":
        monkeypatch.setattr(catalog_capture, "CatalogWriter", failed)
    elif failure == "write":
        monkeypatch.setattr(catalog_capture.CatalogWriter, "write", failed)
    elif failure == "capacity":
        monkeypatch.setattr(catalog_capture, "require_capacity", failed)
    elif failure == "records":
        monkeypatch.setattr(catalog_capture, "MAX_CAPTURE_RECORDS", 0)
    else:
        monkeypatch.setattr(catalog_capture, "MAX_CAPTURE_BYTES", 0)
    result = service.synchronize()
    assert result.exit_code == 0
    assert [warning.code for warning in result.warnings] == ["HFWRN011"]
    ref = reference(layout)
    assert (
        layout.repository(MODEL)
        .instance(CommitSha(SHA_A), PublicationId(ref.publication_id))
        .is_dir()
    )
    assert observation(layout) is None


def test_capacity_warning_remains_visible_without_claiming_metadata_failure(
    service, layout, monkeypatch
):
    monkeypatch.setattr(
        catalog_capture,
        "require_capacity",
        lambda *_a, **_kw: [Problem(code="HFWRN005", message="fixture near reserve")],
    )
    result = service.synchronize()
    assert result.exit_code == 0
    assert [warning.code for warning in result.warnings] == ["HFWRN005"]
    record = observation(layout)
    assert record is not None
    assert record.status == "complete"


def test_capture_runs_after_producer_join_under_original_lock(service, layout, monkeypatch):
    original = HubClient.download
    entered, release, captured = Event(), Event(), Event()
    current = [service.config]

    def curation_source():
        require_archive_lock()
        assert release.is_set()
        return current[0]

    service = replace(service, curation_source=curation_source)

    def download(self, *args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(self, *args, **kwargs)

    original_capture = catalog_capture.extract_publication

    def capture(access):
        require_archive_lock()
        assert release.is_set()
        captured.set()
        return original_capture(access)

    monkeypatch.setattr(HubClient, "download", download)
    monkeypatch.setattr(catalog_capture, "extract_publication", capture)
    outcomes = []
    worker = Thread(target=lambda: outcomes.append(service.synchronize()))
    worker.start()
    try:
        assert entered.wait(5)
        assert not captured.is_set()
        with (
            pytest.raises(SafetyError),
            exclusive_lock(lock_path(), command="compete", wait_seconds=0),
        ):
            pytest.fail("producer lost common lock")
        current[0] = curated(service.config, ("edited-during-download",))
    finally:
        release.set()
        worker.join(10)
    assert not worker.is_alive()
    assert captured.is_set()
    assert outcomes[0].exit_code == 0
    snapshot = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
    assert snapshot is not None
    assert snapshot.tags == ("edited-during-download",)
    assert snapshot.curation_fingerprint == current[0].curation_fingerprint()
    assert service.config.repositories[0].tags == ("original",)


def test_invocation_budget_is_shared_across_publications(service, hub, layout, monkeypatch):
    other = RepositoryIdentity.of("model", "organization/other-model")
    hub.heads[other.selector] = SHA_A
    config = service.config.model_copy(
        update={
            "repositories": (
                service.config.repositories[0],
                service.config.repositories[0].model_copy(update={"id": other.id}),
            )
        }
    )
    shared = ExtractionBudget(maximum_candidates=1)
    monkeypatch.setattr(catalog_capture, "ExtractionBudget", lambda: shared)
    result = replace(service, config=config).synchronize()
    assert result.exit_code == 0
    first = observation(layout)
    assert first is not None
    assert first.status == "complete"
    ref = read_reference(layout, layout.repository(other).revision_ref(CommitSha(SHA_A)))
    second = read_publication_observation(
        layout, other, CommitSha(SHA_A), PublicationId(ref.publication_id), ARCHIVE_ID
    )
    assert second is not None
    assert second.status == "failed"
    assert "candidate_limit" in second.diagnostics
    assert shared.candidates > shared.maximum_candidates


@pytest.mark.parametrize("corruption", ["path", "identity", "sha", "retired"])
def test_repair_observes_only_exact_replacement_and_preserves_old_manifest(
    service, layout, monkeypatch, corruption
):
    assert service.synchronize().exit_code == 0
    before = reference(layout)
    repository = layout.repository(MODEL)
    old_manifest = repository.manifest(CommitSha(SHA_A), PublicationId(before.publication_id))
    original = old_manifest.read_bytes()
    old_observation = observation(layout)
    assert old_observation is not None
    member = (
        repository.instance(CommitSha(SHA_A), PublicationId(before.publication_id)) / "model.gguf"
    )
    data = member.read_bytes()
    member.unlink()
    member.write_bytes(b"broken" + data[6:])
    result = service.repair(RepairRequest(f"{MODEL.selector}@{SHA_A}", reason="fixture damage"))
    assert result.exit_code == 0
    assert not result.warnings
    after = reference(layout)
    assert after.publication_id != before.publication_id
    assert after.publication_generation == before.publication_generation
    assert old_manifest.read_bytes() == original
    replacement = observation(layout)
    assert replacement is not None
    assert replacement.publication_id == after.publication_id
    assert replacement.status == "complete"
    old_path = repository.observation(CommitSha(SHA_A), PublicationId(before.publication_id))
    assert (
        json.loads(old_path.read_bytes())["observed_at"]
        == old_observation.to_payload()["observed_at"]
    )
    journals = [json.loads(path.read_bytes()) for path in layout.transactions.iterdir()]
    repair = next(journal for journal in journals if journal["operation"] == "repair")
    assert repair["state"] == "open"
    assert repair["checkpoints"][-1]["name"] == "repair_committed"
    # INV-018: corrupt journal evidence cannot redirect bounded metadata reads to payloads.
    checkpoint = next(
        cp for cp in repair["checkpoints"] if cp["name"] == "retirement_record_written"
    )
    if corruption == "path":
        checkpoint["evidence"]["retirement_record_path"] = str(layout.archive_relative(member))
        journal_path = layout.transactions / f"{repair['transaction_id']}.json"
        journal_path.write_text(json.dumps(repair))
    else:
        retirement_path = layout.root / checkpoint["evidence"]["retirement_record_path"]
        retirement = json.loads(retirement_path.read_bytes())
        field, value = {
            "identity": ("repository_id", "organization/other-name"),
            "sha": ("commit_sha", "2" * 40),
            "retired": ("retired_publication_id", "3" * 32),
        }[corruption]
        retirement[field] = value
        retirement_path.write_text(json.dumps(retirement))
    original_read = MetadataReader.read

    def read(self, path, **options):
        assert path != member, "guard opened payload before canonical retirement-path validation"
        return original_read(self, path, **options)

    monkeypatch.setattr(MetadataReader, "read", read)
    with (
        exclusive_lock(lock_path(), command="test adjunct guard", wait_seconds=0),
        pytest.raises(IntegrityError),
    ):
        CatalogWriter(layout, storage=service.config.storage)
