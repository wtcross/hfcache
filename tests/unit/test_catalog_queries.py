"""V29-35: exact variants, coverage, bounded read-only projection and private cursors."""

import hashlib
import json
from dataclasses import replace

import pytest

from hfcache.catalog_models import ModelVariant, VariantMember, variant_identity
from hfcache.catalog_query_models import CatalogQuery
from hfcache.catalog_storage import CatalogWriter
from hfcache.config import RepositoryConfig
from hfcache.errors import HfcacheError, RequestError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.metadata import QueryBounds, QueryLimitError
from hfcache.models import dump
from hfcache.redaction import register_secret
from hfcache.services.catalog_queries import CatalogQueries
from tests.fixtures import examples
from tests.unit import test_synchronize as fixtures

layout = fixtures.layout
config = fixtures.config
MODEL = RepositoryIdentity.of("model", examples.REPOSITORY_ID)


def publish(  # noqa: PLR0913 - synthetic exact publication fixture
    layout,
    identity=MODEL,
    *,
    sha=examples.SHA,
    publication=examples.PUBLICATION,
    generation=1,
    variants=None,
    status="complete",
    extractor="static-1",
):
    repository = layout.repository(identity)
    manifest = examples.manifest()
    if variants is None:
        variants = (
            (
                variant("small.gguf", 4_000_000_000, "Q4_0", 4),
                variant("large.gguf", 8_000_000_000, "Q8_0", 8),
            )
            if identity.type == "model"
            else ()
        )
    files = {item.path: item for item in manifest.files}
    for value in variants:
        for member in value.members:
            files[member.path] = manifest.files[0].model_copy(
                update={"path": member.path, "size": member.size_bytes}
            )
    manifest = manifest.model_copy(
        update={
            "repository_type": identity.type,
            "repository_id": identity.id,
            "commit_sha": sha,
            "publication_id": publication,
            "publication_generation": generation,
            "tree": str(repository.manifest_tree_field(CommitSha(sha), PublicationId(publication))),
            "files": tuple(files[key] for key in sorted(files)),
            "file_count": len(files),
            "total_bytes": sum(value.size for value in files.values()),
        }
    )
    path = repository.manifest(CommitSha(sha), PublicationId(publication))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dump(manifest))
    ref = examples.reference().model_copy(
        update={
            "repository_type": identity.type,
            "repository_id": identity.id,
            "commit_sha": sha,
            "publication_id": publication,
            "publication_generation": generation,
            "tree": str(repository.tree_reference(CommitSha(sha), PublicationId(publication))),
            "manifest": str(
                repository.manifest_reference(CommitSha(sha), PublicationId(publication))
            ),
        }
    )
    retained = repository.revision_ref(CommitSha(sha))
    retained.parent.mkdir(parents=True, exist_ok=True)
    retained.write_bytes(dump(ref))
    repository.current_ref.write_bytes(dump(ref))
    observation = examples.publication_observation().model_copy(
        update={
            "repository_type": identity.type,
            "repository_id": identity.id,
            "commit_sha": sha,
            "publication_id": publication,
            "publication_generation": generation,
            "manifest_path": str(layout.archive_relative(path)),
            "manifest_digest": hashlib.sha256(path.read_bytes()).hexdigest(),
            "variants": tuple(sorted(variants, key=lambda v: v.variant_id)),
            "status": status,
            "extractor_version": extractor,
            "dataset_formats": ("csv", "parquet") if identity.type == "dataset" else (),
        }
    )
    if extractor != "static-1":
        observation = observation.model_copy(
            update={
                "variants": tuple(
                    value.model_copy(
                        update={"variant_id": variant_identity(value.members, extractor)}
                    )
                    for value in observation.variants
                )
            }
        )
        observation = observation.model_copy(
            update={"variants": tuple(sorted(observation.variants, key=lambda v: v.variant_id))}
        )
    target = repository.observation(CommitSha(sha), PublicationId(publication))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(dump(observation))
    return observation


def variant(path, size, scheme="Q4_0", bits=4, **updates):
    members = (VariantMember(path=path, size_bytes=size),)
    return ModelVariant(
        variant_id=variant_identity(members),
        format="gguf",
        encoding=scheme,
        quantization=scheme,
        quantization_method="ggml",
        bits=bits,
        role="primary",
        members=members,
        total_bytes=size,
        completeness="complete",
        evidence="header",
        source_paths=(path,),
    ).model_copy(update=updates)


def tagged(config, *entries):
    return config.model_copy(
        update={
            "repositories": tuple(
                RepositoryConfig.model_validate(
                    {
                        "type": kind,
                        "id": name,
                        "tags": tags,
                        "enabled": enabled,
                    }
                )
                for kind, name, tags, enabled in entries
            )
        }
    )


def search(config, **filters):
    return CatalogQueries(config).search(CatalogQuery(**filters))


def test_same_variant_conjunction_and_truthful_representative(config, layout):
    publish(layout)
    config = tagged(config, ("model", MODEL.id, ("coding",), True))
    assert (
        search(config, quantization="Q8_0", max_variant_bytes=5_000_000_000).result.data[
            "total_matches"
        ]
        == 0
    )
    data = search(config, quantization="Q4_0", max_variant_bytes=5_000_000_000).result.data
    assert data["entries"][0]["matching_variant_count"] == 1
    assert data["entries"][0]["representative_variant"]["variant"]["quantization"] == "Q4_0"
    assert data["coverage"]["usable"] == 1
    assert search(config).result.data["entries"][0]["matching_variant_count"] == 2


def test_configured_disabled_unpublished_and_same_id_different_type(config, layout):
    dataset = RepositoryIdentity.of("dataset", MODEL.id)
    publish(layout)
    publish(layout, dataset)
    config = tagged(
        config,
        ("model", MODEL.id, (), False),
        ("dataset", MODEL.id, ("science",), True),
        ("model", "org/unpublished", ("coding",), False),
    )
    data = search(config, scope="all").result.data
    assert [(item["repository_type"], item["repository_id"]) for item in data["entries"]] == [
        ("dataset", MODEL.id),
        ("model", "org/unpublished"),
        ("model", MODEL.id),
    ]
    assert data["entries"][2]["tags"] == []
    assert data["entries"][1]["enabled"] is False
    assert data["entries"][1]["archived"] is False
    assert (
        search(config, scope="configured", tags_all=("coding",)).result.data["total_matches"] == 1
    )
    assert (
        search(config, format="parquet").result.data["entries"][0]["repository_type"] == "dataset"
    )


def test_last_observed_tags_only_actual_snapshot_and_current_empty_overrides(config, layout):
    publish(layout)
    repository = layout.repository(MODEL)
    repository.tag_snapshot.parent.mkdir(parents=True)
    repository.tag_snapshot.write_bytes(dump(examples.tag_snapshot()))
    unmanaged = tagged(config)
    assert search(unmanaged, tags_all=("coding",)).result.data["total_matches"] == 1
    assert (
        search(unmanaged, tags_all=("coding",), tag_source="current_only").result.data[
            "total_matches"
        ]
        == 0
    )
    assert (
        CatalogQueries(unmanaged).detail(MODEL).result.data["entry"]["tag_origin"]
        == "last_observed"
    )
    empty = tagged(config, ("model", MODEL.id, (), False))
    assert search(empty, tags_any=("coding",)).result.data["total_matches"] == 0
    repository.tag_snapshot.unlink()
    assert search(unmanaged).result.data["coverage"]["tags_unknown"] == 1


def test_current_is_explicit_no_cross_revision_matching_or_retired_fallback(config, layout):
    old = publish(layout, variants=(variant("old.gguf", 8_000_000_000, "Q8_0", 8),))
    publish(
        layout,
        sha=examples.OTHER_SHA,
        publication=examples.REPLACEMENT,
        generation=2,
        variants=(variant("new.gguf", 4_000_000_000),),
    )
    repository = layout.repository(MODEL)
    repository.current_ref.write_bytes(
        repository.revision_ref(CommitSha(examples.SHA)).read_bytes()
    )
    assert search(config, quantization="Q4_0").result.data["total_matches"] == 0
    assert (
        search(config, quantization="Q4_0", revision_scope="retained").result.data["total_matches"]
        == 1
    )
    assert (
        search(
            config, quantization="Q8_0", max_variant_bytes=5_000_000_000, revision_scope="retained"
        ).result.data["total_matches"]
        == 0
    )
    queries = CatalogQueries(config)
    exact = queries.detail(
        MODEL, commit_sha=examples.OTHER_SHA, publication_id=examples.REPLACEMENT
    )
    assert exact.result.data["observations"][0]["publication_generation"] == 2
    with pytest.raises(RequestError):
        queries.detail(MODEL, commit_sha=old.commit_sha)
    repository.revision_ref(CommitSha(examples.SHA)).unlink()
    with pytest.raises(HfcacheError):
        queries.detail(MODEL, commit_sha=old.commit_sha, publication_id=old.publication_id)


@pytest.mark.parametrize(
    "updates",
    [
        {"role": "adapter"},
        {"role": "projector"},
        {"completeness": "incomplete"},
        {"completeness": "unknown"},
        {"evidence": "filename"},
        {"encoding": "unknown", "quantization": "UNKNOWN"},
    ],
)
def test_noneligible_candidates_remain_inspectable_but_never_positive(config, layout, updates):
    publish(layout, variants=(variant("candidate.gguf", 128, **updates),))
    assert search(config, format="gguf").result.data["total_matches"] == 0
    assert CatalogQueries(config).variants(MODEL).result.data["total_matches"] == 1


@pytest.mark.parametrize(
    ("status", "extractor", "field"),
    [
        ("partial", "static-1", "partial"),
        ("failed", "static-1", "failed"),
        ("unsupported", "static-1", "unsupported"),
        ("complete", "future-2", "unsupported"),
    ],
)
def test_incomplete_parent_and_unknown_extractors_are_truthful(
    config, layout, status, extractor, field
):
    publish(layout, status=status, extractor=extractor)
    page = search(config, format="gguf")
    assert page.result.data["coverage"][field] == 1
    assert page.result.data["coverage"]["incomplete"] is True
    assert page.result.warnings[0].code == "HFWRN011"
    assert page.result.data["total_matches"] == (1 if status == "partial" else 0)


def test_filtered_facets_count_repositories_from_only_matching_variants(config, layout):
    publish(layout)
    publish(layout, RepositoryIdentity.of("model", "org/second"))
    queries = CatalogQueries(config)
    data = queries.facets("quantization", CatalogQuery(max_variant_bytes=5_000_000_000)).result.data
    assert data["entries"] == [{"value": "Q4_0", "repository_count": 2}]
    dataset = RepositoryIdentity.of("dataset", "org/data")
    publish(layout, dataset)
    assert queries.facets(
        "format", CatalogQuery(repository_type="dataset", format="csv")
    ).result.data["entries"] == [{"value": "csv", "repository_count": 1}]


def test_page_counts_coverage_and_stale_visible_curation(config, layout):
    publish(layout)
    publish(layout, RepositoryIdentity.of("model", "org/second"))
    page = search(config, limit=1)
    assert page.next_cursor
    assert page.result.data["total_matches"] == 2
    assert page.result.data["coverage"]["publications"] == 2
    second = search(config, limit=1, cursor=page.next_cursor)
    assert second.result.data["entries"] != page.result.data["entries"]
    changed = tagged(config, ("model", MODEL.id, ("changed",), True))
    with pytest.raises(RequestError) as stale:
        search(changed, cursor=page.next_cursor)
    assert stale.value.status_code == 409
    variants = CatalogQueries(config).variants(MODEL, limit=1)
    assert variants.next_cursor
    assert (
        CatalogQueries(config)
        .variants(MODEL, limit=1, cursor=variants.next_cursor)
        .result.data["entries"]
        != variants.result.data["entries"]
    )


def test_orphan_metadata_never_resurrects_inventory(config, layout):
    record = publish(layout)
    repository = layout.repository(MODEL)
    repository.revision_ref(CommitSha(record.commit_sha)).unlink()
    repository.current_ref.unlink()
    assert search(tagged(config)).result.data["total_matches"] == 0
    with pytest.raises(RequestError):
        CatalogQueries(tagged(config)).detail(MODEL)


def test_missing_vs_corrupt_selected_records_and_full_scan_bounds(config, layout):
    record = publish(layout)
    path = layout.repository(MODEL).observation(
        CommitSha(record.commit_sha), PublicationId(record.publication_id)
    )
    raw = path.read_bytes()
    path.unlink()
    data = search(config, format="gguf").result.data
    assert data["total_matches"] == 0
    assert data["coverage"]["missing"] == 1
    path.write_bytes(raw.replace(b'"schema_version": 1', b'"schema_version": 2'))
    # dump uses stable indentation; use a parsed future payload for certainty.
    payload = json.loads(raw)
    payload["schema_version"] = 2
    path.write_text(json.dumps(payload))
    with pytest.raises(HfcacheError):
        search(config, limit=1)
    path.write_bytes(raw)
    with pytest.raises(QueryLimitError):
        CatalogQueries(config, bounds=QueryBounds(1, 1024, 1024)).search(CatalogQuery(limit=1))
    with pytest.raises(QueryLimitError):
        replace(CatalogQueries(config), max_response_bytes=1024).detail(MODEL)


def test_secret_substitution_cannot_change_matching_facets_counts_or_catalog_identity(
    config, layout
):
    publish(layout)
    register_secret("hidden-one")
    register_secret("hidden-two")
    first = tagged(config, ("model", MODEL.id, ("coding", "hidden-one"), True))
    second = tagged(config, ("model", MODEL.id, ("coding", "hidden-two"), True))
    assert search(first).result.data == search(second).result.data
    assert (
        CatalogQueries(first).facets("tag").result.data
        == CatalogQueries(second).facets("tag").result.data
    )
    assert search(first, tags_all=("hidden-one",)).result.data["total_matches"] == 0
    assert "hidden-one" not in json.dumps(search(first).result.data)
    register_secret("8")
    assert search(first, bits=8).result.data["total_matches"] == 0


def test_query_has_no_writer_network_credentials_hashes_or_payload_capability(
    config, layout, monkeypatch
):
    publish(layout)

    def forbidden(*args, **kwargs):
        pytest.fail("read query acquired a forbidden capability")

    monkeypatch.setattr(CatalogWriter, "__init__", forbidden)
    monkeypatch.setattr("hfcache.locking.exclusive_lock", forbidden)
    monkeypatch.setattr("hfcache.credentials.resolve_token", forbidden)
    monkeypatch.setattr("hfcache.hashing.sha256_file", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)
    assert search(config, format="gguf").result.data["total_matches"] == 1
    assert (
        not layout.repository(MODEL)
        .instance(CommitSha(examples.SHA), PublicationId(examples.PUBLICATION))
        .exists()
    )


def test_hidden_source_path_and_fingerprint_substitution_leave_cursor_unchanged(config, layout):
    register_secret("private-one")
    register_secret("private-two")
    publish(layout, RepositoryIdentity.of("model", "org/second"))

    def install(hidden):
        record = publish(layout, variants=(variant(hidden + ".gguf", 4096),))
        repository = layout.repository(MODEL)
        snapshot = examples.tag_snapshot().model_copy(
            update={
                "tags": (hidden,),
                "curation_fingerprint": hashlib.sha256(hidden.encode()).hexdigest(),
            }
        )
        repository.tag_snapshot.parent.mkdir(parents=True, exist_ok=True)
        repository.tag_snapshot.write_bytes(dump(snapshot))
        return record

    install("private-one")
    first = search(tagged(config), limit=1)
    install("private-two")
    second = search(tagged(config), limit=1)
    assert first.result.data == second.result.data
    assert first.next_cursor == second.next_cursor
    assert first.result.data["coverage"]["partial"] == 1


def test_corrupt_later_repository_and_unsafe_namespace_refuse_even_with_one_row(config, layout):
    publish(layout)
    other = RepositoryIdentity.of("model", "zz/last")
    record = publish(layout, other)
    target = layout.repository(other).observation(
        CommitSha(record.commit_sha), PublicationId(record.publication_id)
    )
    raw = target.read_bytes()
    target.write_bytes(b"corrupt")
    with pytest.raises(HfcacheError):
        search(config, limit=1)
    target.write_bytes(raw)
    unknown = layout.metadata / "unknown"
    unknown.mkdir()
    with pytest.raises(HfcacheError):
        search(config, limit=1)


def test_cursor_binds_exact_scope_and_canonical_filters(config, layout):
    publish(layout)
    config = tagged(config, ("model", MODEL.id, ("coding",), True))
    publish(layout, RepositoryIdentity.of("model", "org/second"))
    queries = CatalogQueries(config)
    first = queries.variants(MODEL, limit=1)
    assert first.next_cursor
    with pytest.raises(RequestError) as caught:
        queries.variants(
            MODEL,
            limit=1,
            cursor=first.next_cursor,
            commit_sha=examples.SHA,
            publication_id=examples.PUBLICATION,
        )
    assert caught.value.status_code == 409
    assert (
        search(config, tags_all=(" coding ", "CODING")).result.data
        == search(config, tags_all=("coding",)).result.data
    )


def test_model_variants_refuse_dataset_identity_and_unknown_format_stays_unknown(config, layout):
    identity = RepositoryIdentity.of("dataset", "org/data")
    record = publish(layout, identity)
    with pytest.raises(RequestError):
        CatalogQueries(config).variants(identity)
    path = layout.repository(identity).observation(
        CommitSha(record.commit_sha), PublicationId(record.publication_id)
    )
    path.write_bytes(dump(record.model_copy(update={"dataset_formats": ("CSV",)})))
    data = search(config, repository_type="dataset", format="csv").result.data
    assert data["total_matches"] == 0
    assert data["coverage"]["partial"] == 1


def test_hidden_exact_identity_cannot_reveal_membership(config, layout):
    identity = RepositoryIdentity.of("model", "org/private-one")
    publish(layout, identity)
    register_secret("private-one")
    register_secret("private-two")
    for selected in (identity, RepositoryIdentity.of("model", "org/private-two")):
        for method in (CatalogQueries(config).detail, CatalogQueries(config).variants):
            with pytest.raises(RequestError) as caught:
                method(selected)
            assert caught.value.status_code == 404
            assert caught.value.problems[0].code == "HFAPI007"
