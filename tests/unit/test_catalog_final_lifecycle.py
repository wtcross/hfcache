"""V51: real sync/repair/prune/purge cannot revive inert supplemental evidence."""

from dataclasses import replace

import pytest

from hfcache.catalog_query_models import CatalogQuery
from hfcache.errors import RequestError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.models import dump
from hfcache.services.catalog_queries import CatalogQueries
from hfcache.services.context import ExecutionContext
from hfcache.services.requests import CatalogRefreshRequest, MaintenanceRequest, RepairRequest
from tests.fixtures.gguf import gguf
from tests.unit import test_catalog_lifecycle as lifecycle
from tests.unit import test_catalog_queries as domain
from tests.unit.test_synchronize import MODEL, SHA_A, SHA_B

_local_lock = lifecycle._local_lock
config = lifecycle.config
hub = lifecycle.hub
client = lifecycle.client
layout = lifecycle.layout
service = lifecycle.service


def fresh(service, config=None):
    return replace(service, config=config or service.config, context=ExecutionContext.create())


def test_config_disable_removal_readd_noop_and_exact_repair_discovery(service, layout, hub):
    assert service.synchronize().exit_code == 0
    original = lifecycle.reference(layout)
    repository = layout.repository(MODEL)
    old_observation = repository.observation(
        CommitSha(SHA_A), PublicationId(original.publication_id)
    )
    old_bytes = old_observation.read_bytes()
    original_downloads = list(hub.downloads)
    disabled = lifecycle.curated(service.config, ("edited",), enabled=False)
    entry = CatalogQueries(disabled).detail(MODEL).result.data["entry"]
    assert entry["tags"] == ["edited"]
    assert entry["enabled"] is False
    removed = service.config.model_copy(update={"repositories": ()})
    entry = CatalogQueries(removed).detail(MODEL).result.data["entry"]
    assert entry["tag_origin"] == "last_observed"
    assert entry["tags"] == ["original"]
    refresh = fresh(service, removed).refresh_catalog(CatalogRefreshRequest(technical=False))
    assert refresh.exit_code == 0
    assert CatalogQueries(removed).detail(MODEL).result.data["entry"]["tags"] == ["original"]
    empty = lifecycle.curated(service.config, ())
    assert CatalogQueries(empty).detail(MODEL).result.data["entry"]["tags"] == []
    assert fresh(service, empty).synchronize().exit_code == 0
    assert lifecycle.reference(layout) == original
    assert hub.downloads == original_downloads
    old_bytes = old_observation.read_bytes()
    tree = repository.instance(CommitSha(SHA_A), PublicationId(original.publication_id))
    member = tree / "model.gguf"
    body = member.read_bytes()
    member.unlink()
    member.write_bytes(b"broken" + body[6:])
    repaired = fresh(service, empty).repair(
        RepairRequest(f"{MODEL.selector}@{SHA_A}", reason="fixture damage")
    )
    assert repaired.exit_code == 0
    current = lifecycle.reference(layout)
    assert current.publication_id != original.publication_id
    assert old_observation.read_bytes() == old_bytes
    data = CatalogQueries(empty).search(CatalogQuery(format="gguf")).result.data
    representative = data["entries"][0]["representative_variant"]
    assert representative["publication_id"] == current.publication_id
    assert data["coverage"]["publications"] == 1
    with pytest.raises(RequestError) as failure:
        CatalogQueries(empty).detail(
            MODEL, commit_sha=SHA_A, publication_id=original.publication_id
        )
    assert failure.value.status_code == 404


def test_real_prune_and_unmanaged_purge_preserve_but_never_search_orphan_metadata(
    service, layout, hub
):
    for sha in (SHA_A, SHA_B, "3" * 40, "4" * 40):
        hub.heads[MODEL.selector] = sha
        hub.revisions[sha] = {"model.gguf": gguf()[0]}
        assert fresh(service).synchronize().exit_code == 0
    repository = layout.repository(MODEL)
    first_ref = lifecycle.reference(layout)
    orphan = repository.observation(CommitSha(SHA_A), PublicationId(first_ref.publication_id))
    old_bytes = orphan.read_bytes()
    limited = service.config.model_copy(
        update={"storage": service.config.storage.model_copy(update={"maximum_revisions": 3})}
    )
    result = fresh(service, limited).prune(MaintenanceRequest(apply=True))
    assert result.exit_code == 0
    data = CatalogQueries(limited).variants(MODEL, revision_scope="retained").result.data
    assert len(data["entries"]) == 3
    assert SHA_A not in {row["commit_sha"] for row in data["entries"]}
    assert orphan.read_bytes() == old_bytes
    before = {str(p): p.read_bytes() for p in layout.metadata.rglob("*.json")}
    unmanaged = limited.model_copy(update={"repositories": ()})
    result = fresh(service, unmanaged).purge(
        MaintenanceRequest(selectors=(MODEL.selector,), apply=True)
    )
    assert result.exit_code == 0
    assert CatalogQueries(unmanaged).search(CatalogQuery(scope="all")).result.data["entries"] == []
    assert CatalogQueries(unmanaged).facets("tag").result.data["entries"] == []
    assert before == {str(p): p.read_bytes() for p in layout.metadata.rglob("*.json")}
    assert fresh(service, unmanaged).refresh_catalog(CatalogRefreshRequest()).exit_code == 0
    assert CatalogQueries(unmanaged).search().result.data["entries"] == []


@pytest.mark.parametrize(
    "change", ["repair_identity", "prune", "current", "enrichment", "coverage"]
)
def test_catalog_cursor_refuses_publication_and_coverage_changes(config, layout, change):
    record = domain.publish(layout)
    domain.publish(layout, RepositoryIdentity.of("model", "zz/other"))
    domain.publish(layout, sha="2" * 40, publication="e" * 32, generation=2)
    query = CatalogQuery(revision_scope="current" if change == "current" else "retained", limit=1)
    first = CatalogQueries(config).search(query)
    assert first.next_cursor is not None
    repository = layout.repository(domain.MODEL)
    observation = repository.observation(
        CommitSha(record.commit_sha), PublicationId(record.publication_id)
    )
    if change == "repair_identity":
        domain.publish(layout, publication="f" * 32)
    elif change == "prune":
        repository.revision_ref(CommitSha(record.commit_sha)).unlink()
    elif change == "current":
        repository.current_ref.write_bytes(
            repository.revision_ref(CommitSha(record.commit_sha)).read_bytes()
        )
    elif change == "enrichment":
        observation.write_bytes(dump(record.model_copy(update={"diagnostics": ("reviewed",)})))
    else:
        observation.unlink()
    with pytest.raises(RequestError) as failure:
        CatalogQueries(config).search(query.with_cursor(first.next_cursor))
    assert failure.value.status_code == 409
    assert failure.value.problems[0].code == "HFAPI007"
