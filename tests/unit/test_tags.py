"""Strict shared curation grammar and unchanged operational identity (INV-018, V01-04)."""

import copy
import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hfcache.config import RepositoryConfig, validate_config_mapping
from hfcache.errors import ConfigurationError
from hfcache.services.candidates import assess_candidate, candidate_problems, validate_candidate
from hfcache.tags import normalize_tags
from tests.unit.test_config import base_mapping

CASES = json.loads((Path(__file__).parents[1] / "fixtures/tags.json").read_text())


@pytest.mark.parametrize("case", CASES["valid"])
def test_shared_normalization_goldens(case):
    assert normalize_tags(case["input"]) == tuple(case["expected"])
    assert normalize_tags(tuple(case["input"])) == tuple(case["expected"])


@pytest.mark.parametrize("value", CASES["invalid"] + [["a" * 65], [" " * 128 + "a"], ["a"] * 65])
def test_invalid_inputs_refuse_without_values(value):
    with pytest.raises(ValueError, match="tag"):
        normalize_tags(value)


@given(st.lists(st.from_regex(r"[a-z0-9][a-z0-9._:/-]{0,63}", fullmatch=True), max_size=64))
def test_normalization_is_idempotent(tags):
    canonical = normalize_tags(tags)
    assert normalize_tags(canonical) == canonical


def test_tag_limits_are_checked_before_deduplication():
    assert normalize_tags(["a"] * 64) == ("a",)
    assert normalize_tags([" " * 64 + "a" * 64]) == ("a" * 64,)
    with pytest.raises(ValueError, match="tag"):
        normalize_tags(["a"] * 65)


def test_omitted_and_explicit_empty_tags_preserve_pre_feature_policy_golden():
    mapping = base_mapping()
    old = validate_config_mapping(mapping)
    mapping["repositories"][0]["tags"] = []
    explicit = validate_config_mapping(mapping)
    assert old == explicit
    assert old.repositories[0].tags == ()
    assert old.fingerprint() == "17eaec3cdae605106a2d2b50fa606f0beb23bbfb9909f7d7188b26d451bddbab"
    assert explicit.fingerprint() == old.fingerprint()
    assert explicit.curation_fingerprint() == old.curation_fingerprint()
    assert (
        old.curation_fingerprint()
        == "d3bec9cc8bf0d56a2bb8a4fff5e3a3069edd8ca0734d2379799eda38e62a7a68"
    )


def test_curation_changes_without_changing_policy_or_other_fields():
    mapping = base_mapping()
    before = validate_config_mapping(mapping)
    mapping["repositories"][0]["tags"] = [" Coding ", "coding"]
    tagged = validate_config_mapping(mapping)
    assert tagged.fingerprint() == before.fingerprint()
    assert tagged.curation_fingerprint() != before.curation_fingerprint()
    assert tagged.repositories[0].tags == ("coding",)
    mapping["repositories"][0]["enabled"] = False
    disabled = validate_config_mapping(mapping)
    assert disabled.curation_fingerprint() == tagged.curation_fingerprint()
    assert disabled.fingerprint() != tagged.fingerprint()
    mapping["repositories"].append({"type": "dataset", "id": "org/empty", "tags": []})
    assert (
        validate_config_mapping(mapping).curation_fingerprint() != disabled.curation_fingerprint()
    )
    assert tagged.model_dump(exclude={"repositories"}) == before.model_dump(
        exclude={"repositories"}
    )


def test_curation_identity_is_sorted_includes_disabled_and_excludes_authority():
    mapping = base_mapping()
    mapping["repositories"].append(
        {"id": "org/data", "type": "dataset", "enabled": False, "tags": ["z"]}
    )
    before = validate_config_mapping(mapping)
    mapping["repositories"].reverse()
    mapping["hub"] = {"endpoint": "https://hub.example.com", "credential_name": "other"}
    mapping["storage"]["archive_root"] = "/other"
    assert validate_config_mapping(mapping).curation_fingerprint() == before.curation_fingerprint()
    changed = copy.deepcopy(mapping)
    changed["repositories"][0]["tags"] = []
    assert validate_config_mapping(changed).curation_fingerprint() != before.curation_fingerprint()
    changed["repositories"].pop(0)
    assert validate_config_mapping(changed).curation_fingerprint() != before.curation_fingerprint()


def test_bad_tag_error_is_located_without_rejected_secret():
    mapping = base_mapping()
    secret = "registered secret\nvalue"
    mapping["repositories"][0]["tags"] = [secret]
    with pytest.raises(ConfigurationError) as caught:
        validate_config_mapping(mapping)
    problem = caught.value.problems[0]
    assert problem.location == "repositories[0].tags"
    assert problem.code == "HFCFG005"
    assert secret not in problem.message
    safe = candidate_problems(caught.value)[0]
    assert safe.location == problem.location
    assert secret not in safe.message


def test_candidate_tags_do_not_change_authority_or_old_validation_dto():
    config = validate_config_mapping(base_mapping())
    text = """schema_version = 1
[storage]
archive_root = "/srv/hfcache"
archive_id = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
[[repositories]]
id = "organization/model-name"
type = "model"
tags = ["Coding"]
"""
    assessment = assess_candidate(text, config)
    assert assessment.authority_compatible
    assert assessment.config.repositories[0].tags == ("coding",)
    result = validate_candidate(text, config)
    assert result.exit_code == 0
    assert result.data["config_fingerprint"] == config.fingerprint()
    incompatible = text.replace('"/srv/hfcache"', '"/elsewhere"')
    assert assess_candidate(incompatible, config).mismatches == ("storage.archive_root",)


@pytest.mark.parametrize("field", ["categories", "groups", "use_cases", "expected_variants"])
def test_other_operator_fields_remain_unknown(field):
    with pytest.raises(ValueError, match="Extra inputs"):
        RepositoryConfig.model_validate({"id": "org/model", "type": "model", field: []})
