"""V26-V28: explicit offline refresh progress, bounded scope and actual historical capture."""

import json
from dataclasses import replace
from threading import Event, Thread, current_thread, main_thread

import pytest
from pydantic import ValidationError

from hfcache import catalog_capture, catalog_refresh, catalog_storage
from hfcache.catalog_refresh import CatalogRefreshResult
from hfcache.catalog_storage import CatalogWriter, read_tag_snapshot
from hfcache.errors import ConfigurationError
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    new_run_id,
    new_transaction_id,
)
from hfcache.locking import exclusive_lock, lock_path, require_archive_lock
from hfcache.metadata import QueryBounds
from hfcache.models import dump
from hfcache.publication import read_reference
from hfcache.services import commands
from hfcache.services.requests import CatalogRefreshRequest
from hfcache.transactions import open_transaction
from tests.fixtures import examples
from tests.fixtures.gguf import gguf
from tests.unit import test_catalog_lifecycle as lifecycle
from tests.unit import test_synchronize as sync_fixtures
from tests.unit.test_synchronize import ARCHIVE_ID, MODEL, SHA_A, SHA_B

_local_lock = lifecycle._local_lock
config = lifecycle.config
hub = lifecycle.hub
client = lifecycle.client
layout = lifecycle.layout
service = lifecycle.service


def refresh(service, **options):
    outcome = service.refresh_catalog(CatalogRefreshRequest(**options))
    assert outcome.payload, outcome.errors
    payload = CatalogRefreshResult.model_validate(outcome.data)
    return outcome, payload


def files(layout):
    return {
        str(path.relative_to(layout.root)): path.read_bytes()
        for path in layout.root.rglob("*")
        if path.is_file()
    }


def unchanged_authority(before, layout):
    after = files(layout)
    assert {
        key: value for key, value in before.items() if not key.startswith("published/metadata/")
    } == {key: value for key, value in after.items() if not key.startswith("published/metadata/")}


@pytest.mark.parametrize(
    "options",
    [
        {"selectors": "model:organization/model-name"},
        {"selectors": [None]},
        {"selectors": [MODEL.selector + "@" + SHA_A]},
        {"selectors": ["models:organization/model-name"]},
        {"selectors": ["/tmp/archive"]},
        {"selectors": [MODEL.selector] * 257},
        {"tags": 1},
        {"technical": "false"},
        {"tags": False, "technical": False},
        {"revision_scope": []},
        {"revision_scope": "latest"},
    ],
)
def test_refresh_request_is_strict_before_any_effect(options):
    with pytest.raises(ConfigurationError):
        CatalogRefreshRequest(**options)


def test_selectors_are_canonical_sorted_and_deduplicated():
    request = CatalogRefreshRequest(
        selectors=(MODEL.selector, sync_fixtures.DATASET.selector, MODEL.selector)
    )
    assert request.selectors == (sync_fixtures.DATASET.selector, MODEL.selector)


@pytest.mark.parametrize(
    "selector", ["private-refusal-marker" * 1000, "model:org/bad private-refusal-marker"]
)
def test_malformed_selector_diagnostic_is_bounded_and_never_echoes_private_input(selector):
    with pytest.raises(ConfigurationError) as caught:
        CatalogRefreshRequest(selectors=(selector,))
    assert "private-refusal-marker" not in str(caught.value)
    assert len(str(caught.value)) < 256
    assert caught.value.problems[0].location is None


def test_longest_canonical_whole_selector_remains_supported():
    selector = "dataset:" + "a" * 96 + "/" + "b" * 96
    assert CatalogRefreshRequest(selectors=(selector,)).selectors == (selector,)


def test_tag_only_unpublished_disabled_refresh_is_offline_and_adjunct_only(
    service, layout, monkeypatch
):
    service = replace(service, config=lifecycle.curated(service.config, (), enabled=False))
    before = files(layout)

    def forbidden(*_a, **_kw):
        pytest.fail("offline tag refresh attempted Hub, credentials, hashes or extraction")

    monkeypatch.setattr(commands, "resolve_token", forbidden)
    monkeypatch.setattr(commands.HubClient, "of", forbidden)
    monkeypatch.setattr("socket.getaddrinfo", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)
    monkeypatch.setattr(catalog_capture.CatalogCapture, "publication_record", forbidden)
    monkeypatch.setattr("hfcache.hashing.sha256_file", forbidden)
    outcome, result = refresh(service, technical=False)
    assert outcome.exit_code == 0
    assert result.state == "complete"
    assert result.counts.snapshots_written == 1
    assert result.counts.observations_written == 0
    assert result.repositories[0].technical_status == "not_requested"
    assert result.repositories[0].tag_status == "captured"
    snapshot = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
    assert snapshot is not None
    assert snapshot.tags == ()
    assert snapshot.curation_fingerprint == result.curation_fingerprint
    unchanged_authority(before, layout)


def test_unpublished_technical_work_is_explicitly_skipped(service, layout):
    outcome, result = refresh(service, tags=False)
    assert outcome.exit_code == 0
    assert result.repositories[0].technical_status == "skipped_unpublished"
    assert result.counts.technical_skipped == 1
    assert result.counts.observations_written == 0
    assert read_tag_snapshot(layout, MODEL, ARCHIVE_ID) is None


def test_technical_only_never_recaptures_changed_tags_or_hashes_payloads(
    service, layout, hub, monkeypatch
):
    assert service.synchronize().exit_code == 0
    snapshot = layout.repository(MODEL).tag_snapshot
    before = snapshot.read_bytes()
    downloads = tuple(hub.downloads)
    current = lifecycle.curated(service.config, ("new-uncaptured-tag",))
    service = replace(service, curation_source=lambda: current)

    def forbidden(*_a, **_kw):
        pytest.fail("offline technical refresh used Hub, credentials or payload integrity hashing")

    monkeypatch.setattr(commands, "resolve_token", forbidden)
    monkeypatch.setattr(commands.HubClient, "of", forbidden)
    monkeypatch.setattr("hfcache.hashing.sha256_file", forbidden)
    outcome, result = refresh(service, tags=False)
    assert outcome.exit_code == 0
    assert result.counts.snapshots_written == 0
    assert result.counts.observations_written == 1
    assert result.repositories[0].tag_status == "not_requested"
    assert result.repositories[0].publications[0].observation_status == "complete"
    assert snapshot.read_bytes() == before
    assert tuple(hub.downloads) == downloads


def test_current_is_explicit_and_retained_scope_refreshes_both_without_publication(
    service, layout, hub
):
    assert service.synchronize().exit_code == 0
    hub.revisions[SHA_B] = {"model.gguf": gguf()[0]}
    hub.heads[MODEL.selector] = SHA_B
    assert service.synchronize().exit_code == 0
    hub.heads[MODEL.selector] = SHA_A
    assert service.synchronize().exit_code == 0
    repository = layout.repository(MODEL)
    latest = read_reference(layout, repository.revision_ref(CommitSha(SHA_B)))
    latest_observation = repository.observation(
        CommitSha(SHA_B), PublicationId(latest.publication_id)
    )
    original = latest_observation.read_bytes()
    authority = files(layout)
    downloads = tuple(hub.downloads)
    outcome, result = refresh(service, revision_scope="current", tags=False)
    assert outcome.exit_code == 0
    assert [pub.commit_sha for pub in result.repositories[0].publications] == [SHA_A]
    assert latest_observation.read_bytes() == original
    outcome, result = refresh(service, tags=False)
    assert outcome.exit_code == 0
    assert [pub.commit_sha for pub in result.repositories[0].publications] == [SHA_A, SHA_B]
    assert result.counts.observations_written == 2
    assert tuple(hub.downloads) == downloads
    unchanged_authority(authority, layout)


@pytest.mark.parametrize("technical", [True, False])
def test_partial_version_refusal_preserves_bad_record_and_reports_independent_progress(
    service, layout, technical
):
    assert service.synchronize().exit_code == 0
    path = layout.repository(MODEL).tag_snapshot
    bad = json.loads(path.read_bytes())
    bad["schema_version"] = 2
    original = json.dumps(bad).encode()
    path.write_bytes(original)
    outcome, result = refresh(service, technical=technical)
    assert outcome.exit_code == 40
    assert result.state == ("partial" if technical else "failed")
    assert result.counts.records_failed == 1
    assert result.counts.observations_written == int(technical)
    assert result.counts.snapshots_written == 0
    assert result.repositories[0].tag_status == "failed"
    if technical:
        assert result.repositories[0].publications[0].write_status == "written"
    assert [problem.code for problem in outcome.errors] == ["HFVER007"]
    assert path.read_bytes() == original


def test_written_failed_observation_is_incomplete_coverage_not_a_write_failure(
    service, monkeypatch
):
    assert service.synchronize().exit_code == 0

    def failed(_access):
        msg = "private source failure"
        raise RuntimeError(msg)

    monkeypatch.setattr(catalog_capture, "extract_publication", failed)
    outcome, result = refresh(service, tags=False)
    assert outcome.exit_code == 0
    assert result.state == "partial"
    assert result.counts.records_failed == 0
    assert result.counts.technical_incomplete == 1
    assert result.counts.observations_written == 1
    assert result.repositories[0].publications[0].observation_status == "failed"
    assert [problem.code for problem in outcome.warnings] == ["HFWRN011"]
    assert "private source failure" not in str(outcome)


def test_removed_uncaptured_tags_are_never_invented_then_real_history_is_preserved(
    service, layout, client
):
    # Publish through the existing domain seam, without a writer curation capture.
    sync_fixtures.run(client, layout, service.config)
    unmanaged = replace(service, config=service.config.model_copy(update={"repositories": ()}))
    outcome, result = refresh(unmanaged)
    assert outcome.exit_code == 0
    assert result.repositories[0].tag_status == "skipped_unconfigured"
    assert read_tag_snapshot(layout, MODEL, ARCHIVE_ID) is None
    outcome, _ = refresh(service)
    assert outcome.exit_code == 0
    history = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
    assert history is not None
    assert history.tags == ("original",)
    assert refresh(unmanaged)[0].exit_code == 0
    assert read_tag_snapshot(layout, MODEL, ARCHIVE_ID) == history
    readded = replace(service, config=lifecycle.curated(service.config, ()))
    assert refresh(readded)[0].exit_code == 0
    actual = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
    assert actual is not None
    assert actual.tags == ()


@pytest.mark.parametrize("source", ["removed", "unavailable", "other_archive"])
def test_fresh_source_refusals_never_write_stale_tags(service, layout, source):
    def current():
        require_archive_lock()
        if source == "unavailable":
            msg = "private config failure"
            raise ValueError(msg)
        if source == "other_archive":
            return service.config.model_copy(
                update={
                    "storage": service.config.storage.model_copy(
                        update={"archive_id": "11111111-1111-4111-8111-111111111111"}
                    )
                }
            )
        return service.config.model_copy(update={"repositories": ()})

    service = replace(service, curation_source=current)
    outcome = service.refresh_catalog(
        CatalogRefreshRequest(selectors=(MODEL.selector,), technical=False)
    )
    assert outcome.exit_code == 10
    assert not layout.metadata.exists()
    assert "private config failure" not in str(outcome)


def test_waiting_refresh_reads_actual_curation_after_acquiring_the_only_lock(
    service, layout, monkeypatch
):
    current = [service.config]
    waiting = Event()
    service = replace(
        service,
        config=service.config.model_copy(
            update={"sync": service.config.sync.model_copy(update={"lock_wait_seconds": 3})}
        ),
        curation_source=lambda: current[0],
    )
    import fcntl  # noqa: PLC0415 - patch the real kernel lock only for this race fixture

    original = fcntl.flock

    def flock(fd, operation):
        if current_thread() is not main_thread():
            waiting.set()
        return original(fd, operation)

    monkeypatch.setattr(fcntl, "flock", flock)
    outcomes = []
    with exclusive_lock(lock_path(), command="hold fixture writer", wait_seconds=0):
        worker = Thread(target=lambda: outcomes.append(refresh(service, technical=False)))
        worker.start()
        assert waiting.wait(5)
        current[0] = lifecycle.curated(service.config, ("edited-while-waiting",))
    worker.join(10)
    assert not worker.is_alive()
    assert outcomes[0][0].exit_code == 0
    snapshot = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
    assert snapshot is not None
    assert snapshot.tags == ("edited-while-waiting",)


def test_unfinished_journal_refuses_without_recovery_repair_or_pruning(
    service, layout, monkeypatch
):
    with exclusive_lock(lock_path(), command="fixture unfinished writer", wait_seconds=0):
        transaction = open_transaction(
            layout,
            transaction_id=new_transaction_id(),
            operation="publication",
            run_id=new_run_id(),
            archive_id=ARCHIVE_ID,
            config_fingerprint=service.config.fingerprint(),
        )
        transaction.checkpoint(
            "staging_created", staging_path=f".store/staging/{transaction.journal.transaction_id}"
        )
    before = files(layout)

    def forbidden(*_a, **_kw):
        pytest.fail("refresh applied archive recovery, repair or pruning")

    monkeypatch.setattr(commands, "reconcile", forbidden)
    monkeypatch.setattr(commands, "apply_recovery", forbidden)
    monkeypatch.setattr(commands, "repair_revision", forbidden)
    monkeypatch.setattr(commands, "apply_prune", forbidden)
    outcome = service.refresh_catalog(CatalogRefreshRequest())
    assert outcome.exit_code == 20
    assert [error.code for error in outcome.errors] == ["HFTXN001"]
    assert files(layout) == before


@pytest.mark.parametrize(
    "limit", ["MAX_REFRESH_REPOSITORIES", "MAX_REFRESH_PUBLICATIONS", "MAX_REFRESH_RESULT_BYTES"]
)
def test_scope_and_result_limits_refuse_before_any_record_write(
    service, layout, monkeypatch, limit
):
    assert service.synchronize().exit_code == 0
    before = files(layout)
    monkeypatch.setattr(catalog_refresh, limit, 0)
    outcome = service.refresh_catalog(CatalogRefreshRequest())
    assert outcome.exit_code == 20
    assert [error.code for error in outcome.errors] == ["HFAPI005"]
    assert files(layout) == before


def test_metadata_snapshots_and_orphan_instances_cannot_create_refresh_scope(service, layout):
    orphan = RepositoryIdentity.of("model", "organization/orphan")
    repository = layout.repository(orphan)
    repository.instance(CommitSha(SHA_A), PublicationId("3" * 32)).mkdir(parents=True)
    with exclusive_lock(lock_path(), command="fixture historical snapshot", wait_seconds=0):
        CatalogWriter(layout, storage=service.config.storage).write(
            examples.tag_snapshot().model_copy(
                update={"repository_id": orphan.id, "archive_id": ARCHIVE_ID}
            )
        )
    outcome, result = refresh(service)
    assert outcome.exit_code == 0
    assert [row.repository_id for row in result.repositories] == [MODEL.id]
    assert (
        service.refresh_catalog(CatalogRefreshRequest(selectors=(orphan.selector,))).exit_code == 10
    )


@pytest.mark.parametrize("kind", ["entries", "bytes"])
def test_one_metadata_reader_budget_refuses_without_hidden_partial_work(
    service, layout, monkeypatch, kind
):
    assert service.synchronize().exit_code == 0
    original = files(layout)
    bounds = (
        QueryBounds(maximum_entries=1) if kind == "entries" else QueryBounds(maximum_total_bytes=1)
    )
    monkeypatch.setattr(catalog_storage, "RECORD_BOUNDS", bounds)
    outcome = service.refresh_catalog(CatalogRefreshRequest())
    assert outcome.exit_code == 20
    assert [problem.code for problem in outcome.errors] == ["HFAPI005"]
    assert files(layout) == original


def test_result_reservation_counts_actual_generation_width_before_writes(
    service, layout, monkeypatch
):
    assert service.synchronize().exit_code == 0
    path = layout.repository(MODEL).revision_ref(CommitSha(SHA_A))
    reference = read_reference(layout, path).model_copy(update={"publication_generation": 10**2000})
    path.write_bytes(dump(reference))
    original = files(layout)
    monkeypatch.setattr(catalog_refresh, "MAX_REFRESH_RESULT_BYTES", 8000)
    outcome = service.refresh_catalog(CatalogRefreshRequest())
    assert outcome.exit_code == 20
    assert [problem.code for problem in outcome.errors] == ["HFAPI005"]
    assert files(layout) == original


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(schema_version=True),
        lambda p: p.update(schema_version="1"),
        lambda p: p.update(schema_version=2),
        lambda p: p.update(state="partial"),
        lambda p: p.update(tags=False),
        lambda p: p["counts"].update(observations_written=2),
        lambda p: p["repositories"].append(p["repositories"][0]),
        lambda p: p["repositories"][0].update(technical_status="not_requested"),
        lambda p: p["repositories"][0]["publications"][0].update(error_code="HFVER007"),
        lambda p: p["repositories"][0]["publications"][0].update(observed_at=None),
        lambda p: p["repositories"][0]["publications"][0].update(write_status="failed"),
    ],
)
def test_refresh_result_rejects_false_counts_versions_and_recorded_identity(service, mutate):
    assert service.synchronize().exit_code == 0
    outcome, _ = refresh(service)
    payload = outcome.data
    mutate(payload)
    with pytest.raises(ValidationError):
        CatalogRefreshResult.model_validate(payload)


def test_refresh_budget_failure_keeps_written_tags_and_previous_observation(
    service, layout, monkeypatch
):
    assert service.synchronize().exit_code == 0
    ref = lifecycle.reference(layout)
    path = layout.repository(MODEL).observation(CommitSha(SHA_A), PublicationId(ref.publication_id))
    previous = path.read_bytes()
    monkeypatch.setattr(catalog_capture, "MAX_CAPTURE_RECORDS", 1)
    outcome, result = refresh(service)
    assert outcome.exit_code == 20
    assert result.state == "partial"
    assert result.counts.snapshots_written == 1
    assert result.counts.records_failed == 1
    assert result.counts.observations_written == 0
    assert result.repositories[0].publications[0].error_code == "HFAPI005"
    assert path.read_bytes() == previous


def test_refresh_capacity_warning_is_attributed_without_false_extraction_failure(
    service, monkeypatch
):
    monkeypatch.setattr(
        catalog_capture,
        "require_capacity",
        lambda *_a, **_kw: [
            catalog_capture.Problem(code="HFWRN005", message="fixture near reserve")
        ],
    )
    outcome, result = refresh(service, technical=False)
    assert outcome.exit_code == 0
    assert result.state == "partial"
    assert result.repositories[0].warnings == ("HFWRN005",)
    assert [warning.code for warning in outcome.warnings] == ["HFWRN005"]
