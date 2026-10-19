"""CAT-010: shared normalization and strict bounded catalog projections (schemas §17.2)."""

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from hfcache.catalog_query_models import (
    CatalogCoverage,
    CatalogDetailPayload,
    CatalogEntry,
    CatalogFacetPayload,
    CatalogFacetValue,
    CatalogQuery,
    CatalogSearchPayload,
    CatalogVariantsPayload,
    ObservationSummary,
    QualifiedVariant,
)
from hfcache.errors import ConfigurationError
from tests.fixtures import examples


def coverage_payload():
    return {
        "repositories": 1,
        "tags_known": 1,
        "tags_unknown": 0,
        "publications": 1,
        "usable": 1,
        "partial": 0,
        "unsupported": 0,
        "failed": 0,
        "missing": 0,
        "technical_required": False,
        "incomplete": False,
    }


def entry_payload(repository_type="model"):
    return {
        "repository_type": repository_type,
        "repository_id": examples.REPOSITORY_ID,
        "tags": ["coding", "project:assistant"],
        "tag_origin": "configured",
        "tag_observed_at": None,
        "curation_fingerprint": None,
        "configured": True,
        "enabled": False,
        "archived": True,
        "matching_variant_count": 0,
        "representative_variant": None,
        "dataset_formats": ["csv", "parquet"] if repository_type == "dataset" else [],
    }


def qualified_payload():
    observation = examples.publication_observation()
    return {
        "commit_sha": observation.commit_sha,
        "publication_id": observation.publication_id,
        "publication_generation": observation.publication_generation,
        "variant": observation.variants[0].to_payload(),
    }


def summary_payload():
    observation = examples.publication_observation().to_payload()
    return {
        name: observation[name]
        for name in (
            "commit_sha",
            "publication_id",
            "publication_generation",
            "extractor_version",
            "observed_at",
            "status",
            "sources",
            "dataset_formats",
            "diagnostics",
        )
    }


def payload(model):
    common = {"catalog_identity": "a" * 64, "coverage": coverage_payload()}
    if model is CatalogSearchPayload:
        return common | {"total_matches": 1, "entries": [entry_payload()]}
    if model is CatalogDetailPayload:
        return common | {"entry": entry_payload(), "observations": [summary_payload()]}
    if model is CatalogVariantsPayload:
        return common | {"total_matches": 1, "entries": [qualified_payload()]}
    return common | {
        "facet": "tag",
        "total_matches": 1,
        "entries": [{"value": "project:assistant", "repository_count": 1}],
    }


PAYLOADS = (
    CatalogSearchPayload,
    CatalogDetailPayload,
    CatalogVariantsPayload,
    CatalogFacetPayload,
)


def query_from_values(**options):
    return CatalogQuery(**options)


def assign(instance, name, *, value):
    setattr(instance, name, value)


def test_query_normalizes_literal_text_tags_and_ascii_technical_names():
    query = query_from_values(
        q=" Straße ",
        tags_all=[" Coding ", "project:ASSISTANT", "coding"],
        tags_any=["A", "a"],
        format="GGUF",
        quantization="q4_k_m",
        quantization_method="GgMl",
        bits=4,
        max_variant_bytes=0,
    )
    assert query.repository_type == "model"
    assert query.q == " strasse "
    assert query.tags_all == ("coding", "project:assistant")
    assert query.tags_any == ("a",)
    assert (query.format, query.quantization, query.quantization_method) == (
        "gguf",
        "Q4_K_M",
        "ggml",
    )
    assert query.model_only
    assert query.technical_required
    assert CatalogQuery(q="").q is None
    assert CatalogQuery(q="  ").q == "  "
    assert not CatalogQuery(tags_all=("coding",)).technical_required
    assert not CatalogQuery(format="parquet").model_only


def test_filter_identity_excludes_page_controls_and_equates_normalized_intent():
    first = query_from_values(tags_all=["B", " a ", "a"], format="GGUF", limit=1, cursor="one")
    second = CatalogQuery(tags_all=("a", "b"), format="gguf", limit=10_000, cursor="two")
    assert first.canonical_filters() == second.canonical_filters()
    assert first.canonical_filters()["tags_all"] == ["a", "b"]
    assert "limit" not in first.canonical_filters()
    assert "cursor" not in first.canonical_filters()
    assert CatalogQuery(q=" a ").canonical_filters() != CatalogQuery(q="a").canonical_filters()
    with pytest.raises(FrozenInstanceError):
        assign(first, "q", value="changed")


@pytest.mark.parametrize(
    "options",
    [
        {"repository_type": []},
        {"repository_type": "models"},
        {"q": 1},
        {"q": "private-marker" * 30},
        {"q": "\ud800"},
        {"tags_all": None},
        {"tags_all": ["a"] * 65},
        {"tags_any": ["private-marker invalid"]},
        {"tag_source": []},
        {"tag_source": "last_observed"},
        {"scope": "other"},
        {"revision_scope": "latest"},
        {"format": ""},
        {"format": "é"},
        {"quantization": "a" * 65},
        {"quantization_method": "private-marker invalid"},
        {"bits": True},
        {"bits": "4"},
        {"bits": 4.0},
        {"bits": 0},
        {"bits": 65},
        {"max_variant_bytes": False},
        {"max_variant_bytes": -1},
        {"max_variant_bytes": 2**63},
        {"limit": False},
        {"limit": "1"},
        {"limit": 0},
        {"limit": 10_001},
    ],
)
def test_bad_filters_have_bounded_fixed_diagnostics_without_input_echo(options):
    with pytest.raises(ConfigurationError) as error:
        CatalogQuery(**options)
    assert error.value.problems[0].code == "HFARG002"
    assert error.value.problems[0].message == "Invalid catalog query filters"
    assert error.value.problems[0].location is None
    assert "private-marker" not in str(error.value)


@pytest.mark.parametrize("cursor", [False, [], "é", "private-marker" * 30])
def test_cursor_has_a_separate_bounded_ascii_error(cursor):
    with pytest.raises(ConfigurationError) as error:
        CatalogQuery(cursor=cursor)
    assert error.value.problems[0].code == "HFARG001"
    assert error.value.problems[0].message == "Invalid catalog cursor"


@pytest.mark.parametrize(
    "options",
    [
        {"quantization": "future_scheme"},
        {"quantization_method": "future-method"},
        {"bits": 64},
        {"max_variant_bytes": 2**63 - 1},
    ],
)
def test_model_only_filters_select_models_and_reject_explicit_datasets(options):
    assert CatalogQuery(**options).repository_type == "model"
    with pytest.raises(ConfigurationError):
        CatalogQuery(repository_type="dataset", **options)


def test_unknown_valid_technical_identifiers_are_accepted_without_semantic_guessing():
    query = CatalogQuery(format="Future.Format/V2", quantization_method="UNKNOWN_Method")
    assert query.format == "future.format/v2"
    assert query.quantization_method == "unknown_method"
    dataset = CatalogQuery(repository_type="dataset", format="future_format")
    assert dataset.repository_type == "dataset"
    assert dataset.technical_required
    assert not dataset.model_only


@pytest.mark.parametrize("field", list(coverage_payload())[:9])
@pytest.mark.parametrize("value", [True, "1", -1, 2**63])
def test_coverage_counts_reject_coercions_and_unbounded_values(field, value):
    raw = coverage_payload()
    raw[field] = value
    with pytest.raises(ValidationError):
        CatalogCoverage.model_validate(raw)


@pytest.mark.parametrize("field", ["tags_known", "usable"])
def test_coverage_counts_partition_the_scoped_candidate_set(field):
    raw = coverage_payload()
    raw[field] = 0
    with pytest.raises(ValidationError):
        CatalogCoverage.model_validate(raw)


def test_coverage_incompleteness_remains_explicit_core_policy():
    raw = coverage_payload() | {
        "tags_known": 0,
        "tags_unknown": 1,
        "usable": 0,
        "missing": 1,
        "technical_required": True,
        "incomplete": False,
    }
    coverage = CatalogCoverage.model_validate(raw)
    assert not coverage.incomplete
    with pytest.raises(ValidationError):
        assign(coverage, "incomplete", value=True)


def test_entry_preserves_empty_current_disabled_and_unmanaged_unknown_states():
    configured = CatalogEntry.model_validate(entry_payload() | {"tags": []})
    assert configured.tags == ()
    assert configured.configured
    assert configured.enabled is False
    assert configured.tag_observed_at is None
    historical = CatalogEntry.model_validate(
        entry_payload()
        | {
            "configured": False,
            "enabled": None,
            "tag_origin": "last_observed",
            "tag_observed_at": examples.tag_snapshot().to_payload()["observed_at"],
        }
    )
    assert historical.tag_origin == "last_observed"
    unknown = CatalogEntry.model_validate(
        historical.to_payload() | {"tags": [], "tag_origin": "unknown", "tag_observed_at": None}
    )
    assert unknown.tags == ()
    assert unknown.curation_fingerprint is None


@pytest.mark.parametrize(
    "changes",
    [
        {"tags": ["Coding"]},
        {"tags": ["a", "a"]},
        {"tags": ["b", "a"]},
        {"enabled": None},
        {"configured": False},
        {"matching_variant_count": True},
        {"matching_variant_count": -1},
        {"matching_variant_count": 2**63},
        {"representative_variant": qualified_payload()},
        {"dataset_formats": ["parquet"]},
        {"quantization": "Q4_K_M"},
    ],
)
def test_entry_rejects_invented_provenance_variants_or_model_dataset_fields(changes):
    with pytest.raises(ValidationError):
        CatalogEntry.model_validate(entry_payload() | changes)


def test_dataset_entry_has_no_fabricated_model_variant_fields():
    raw = entry_payload("dataset")
    dataset = CatalogEntry.model_validate(raw)
    assert dataset.matching_variant_count == 0
    assert dataset.representative_variant is None
    assert dataset.dataset_formats == ("csv", "parquet")
    for changes in (
        {"matching_variant_count": 1},
        {"representative_variant": qualified_payload()},
        {"dataset_formats": ["CSV"]},
        {"dataset_formats": ["parquet", "csv"]},
        {"dataset_formats": ["csv", "csv"]},
    ):
        with pytest.raises(ValidationError):
            CatalogEntry.model_validate(raw | changes)


def test_qualified_variant_and_summary_keep_exact_publication_identity_without_nested_variants():
    variant = QualifiedVariant.model_validate(qualified_payload())
    assert variant.publication_generation == 1
    assert variant.variant.quantization_method == "awq"
    summary = ObservationSummary.model_validate(summary_payload())
    assert summary.commit_sha == variant.commit_sha
    assert "variants" not in summary.to_payload()
    with pytest.raises(ValidationError):
        ObservationSummary.model_validate(summary_payload() | {"variants": []})
    with pytest.raises(ValidationError):
        QualifiedVariant.model_validate(qualified_payload() | {"publication_generation": True})


@pytest.mark.parametrize("model", PAYLOADS)
@pytest.mark.parametrize("version", [True, "1", 0, 2])
def test_payload_versions_are_strict_independent_schema_one(model, version):
    with pytest.raises(ValidationError):
        model.model_validate(payload(model) | {"schema_version": version})


@pytest.mark.parametrize("model", PAYLOADS)
def test_payloads_round_trip_as_frozen_strict_objects(model):
    result = model.model_validate(payload(model))
    assert model.model_validate(result.to_payload()) == result
    assert result.schema_version == 1
    with pytest.raises(ValidationError):
        result.catalog_identity = "b" * 64
    with pytest.raises(ValidationError):
        model.model_validate(payload(model) | {"extra": True})
    with pytest.raises(ValidationError):
        model.model_validate(payload(model) | {"catalog_identity": "not-a-digest"})


@pytest.mark.parametrize(
    "model", [CatalogSearchPayload, CatalogVariantsPayload, CatalogFacetPayload]
)
@pytest.mark.parametrize("count", [True, "1", -1, 2**63])
def test_page_totals_are_bounded_strict_counts(model, count):
    with pytest.raises(ValidationError):
        model.model_validate(payload(model) | {"total_matches": count})


@pytest.mark.parametrize(
    "model", [CatalogSearchPayload, CatalogVariantsPayload, CatalogFacetPayload]
)
def test_pages_refuse_impossible_totals_and_raw_array_overflow(model):
    raw = payload(model)
    with pytest.raises(ValidationError):
        model.model_validate(raw | {"total_matches": 0})
    with pytest.raises(ValidationError) as error:
        model.model_validate(raw | {"total_matches": 10_001, "entries": raw["entries"] * 10_001})
    assert any(detail["type"] == "too_long" for detail in error.value.errors())


def test_detail_refuses_more_than_64_raw_observations_and_duplicate_publications():
    raw = payload(CatalogDetailPayload)
    with pytest.raises(ValidationError):
        CatalogDetailPayload.model_validate(raw | {"observations": raw["observations"] * 2})
    with pytest.raises(ValidationError) as error:
        CatalogDetailPayload.model_validate(raw | {"observations": raw["observations"] * 65})
    assert any(detail["type"] == "too_long" for detail in error.value.errors())


@pytest.mark.parametrize(
    "model", [CatalogSearchPayload, CatalogVariantsPayload, CatalogFacetPayload]
)
def test_pages_cannot_duplicate_entries_to_inflate_known_matches(model):
    raw = payload(model)
    raw["coverage"] = coverage_payload() | {"repositories": 2, "tags_known": 2}
    raw["total_matches"] = 2
    raw["entries"] *= 2
    with pytest.raises(ValidationError):
        model.model_validate(raw)


@pytest.mark.parametrize(
    ("facet", "value"),
    [
        ("tag", "project:assistant"),
        ("format", "gguf"),
        ("quantization", "Q4_K_M"),
        ("quantization_method", "awq"),
    ],
)
def test_facet_values_use_exact_tag_or_technical_canonical_forms(facet, value):
    raw = payload(CatalogFacetPayload) | {
        "facet": facet,
        "entries": [{"value": value, "repository_count": 1}],
    }
    assert CatalogFacetPayload.model_validate(raw).entries[0].value == value
    wrong = value.upper() if facet != "quantization" else value.lower()
    with pytest.raises(ValidationError):
        CatalogFacetPayload.model_validate(
            raw | {"entries": [{"value": wrong, "repository_count": 1}]}
        )


@pytest.mark.parametrize("count", [True, "1", -1, 2**63])
def test_facet_repository_counts_are_strict_and_bounded(count):
    with pytest.raises(ValidationError):
        CatalogFacetValue(value="coding", repository_count=count)
