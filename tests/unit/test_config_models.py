"""Managed configuration DTOs preserve authority and legacy bodies (decision153)."""

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from hfcache.api.command_models import PlanSubmission, ValidationSubmission
from hfcache.config import validate_config_mapping
from hfcache.config_models import (
    EDITABLE_FIELDS,
    PROTECTED_FIELDS,
    ConfigPrepared,
    ConfigRead,
    ManagedAssessment,
    ManagedEditRequest,
    ManagedValidation,
    RepositoryUpsert,
)
from tests.fixtures import examples

BASE = "a" * 64
CANDIDATE = "b" * 64
SELECTOR = "model:organization/model-name"


def editable():
    config = validate_config_mapping(
        {
            "schema_version": 1,
            "storage": {
                "archive_root": "/tmp/never-disclose-root",
                "archive_id": examples.ARCHIVE_ID,
            },
            "hub": {"credential_name": "never-disclose-credential"},
        }
    ).model_dump(mode="json")
    return {
        "storage": {
            name: config["storage"][name]
            for name in (
                "publication_mode",
                "minimum_free_space_gib",
                "minimum_free_space_percent",
                "maximum_revisions",
            )
        },
        "sync": config["sync"],
        "verification": {"lock_wait_seconds": config["verification"]["lock_wait_seconds"]},
        "repair": config["repair"],
        "repositories": [],
    }


def binding():
    return {
        "schema_version": 1,
        "archive_id": examples.ARCHIVE_ID,
        "base_revision": BASE,
        "candidate_revision": CANDIDATE,
        "required_selectors": [],
    }


def read_body():
    body = binding()
    del body["candidate_revision"], body["required_selectors"]
    return {
        **body,
        "editable": editable(),
        "editable_fields": list(EDITABLE_FIELDS),
        "protected_fields": [
            {"field": field, "description": description} for field, description in PROTECTED_FIELDS
        ],
    }


def removal(name="model-name", repository_type="model"):
    return {
        "kind": "repository-remove",
        "repository_type": repository_type,
        "repository_id": f"organization/{name}",
    }


def test_read_is_exact_complete_nonsecret_projection_and_independent_schema():
    body = read_body()
    parsed = ConfigRead.model_validate(body)
    assert parsed.model_dump(mode="json") == body
    assert "never-disclose" not in parsed.model_dump_json()
    assert len(parsed.editable_fields) == 12
    assert parsed.editable.repositories == ()
    body["editable"]["repositories"].append({"id": "organization/name", "type": "model"})
    assert parsed.editable.repositories == ()


@pytest.mark.parametrize("version", [True, 1.0, "1", 0, 2, None])
def test_projection_schema_version_never_coerces(version):
    body = read_body()
    body["schema_version"] = version
    with pytest.raises(ValidationError):
        ConfigRead.model_validate(body)


@pytest.mark.parametrize("revision", ["a" * 63, "A" * 64, BASE + "\n", 1, None])
def test_opaque_revisions_have_closed_bounded_grammar(revision):
    with pytest.raises(ValidationError):
        ManagedEditRequest.model_validate({"base_revision": revision, "edits": []})


@pytest.mark.parametrize("field", ["hub", "server", "archive_root", "archive_id"])
def test_read_projection_refuses_any_protected_value(field):
    body = read_body()
    body["editable"][field] = "private"
    with pytest.raises(ValidationError):
        ConfigRead.model_validate(body)


def test_read_metadata_cannot_include_values_unknown_descriptions_or_partial_fields():
    body = read_body()
    body["editable_fields"].pop()
    with pytest.raises(ValidationError):
        ConfigRead.model_validate(body)
    body = read_body()
    body["protected_fields"][0]["value"] = "private"
    with pytest.raises(ValidationError):
        ConfigRead.model_validate(body)
    body = read_body()
    body["protected_fields"][0]["description"] = "arbitrary private description"
    with pytest.raises(ValidationError):
        ConfigRead.model_validate(body)


def test_upsert_is_complete_replacement_with_existing_defaults_and_tag_normalization():
    request = ManagedEditRequest.model_validate(
        {
            "base_revision": BASE,
            "edits": [
                {
                    "kind": "repository-upsert",
                    "repository": {
                        "id": "organization/model-name",
                        "type": "model",
                        "tags": [" DATA ", "data", "Critical"],
                        "declared_dependencies": ["organization/base"],
                    },
                }
            ],
        }
    )
    edit = request.edits[0]
    assert isinstance(edit, RepositoryUpsert)
    repository = edit.repository
    assert repository.revision == "main"
    assert repository.enabled is True
    assert repository.tags == ("critical", "data")
    assert repository.declared_dependencies == ("organization/base",)


def test_edits_allow_same_name_different_repository_types_but_never_repeat_identity():
    accepted = {"base_revision": BASE, "edits": [removal(), removal(repository_type="dataset")]}
    assert len(ManagedEditRequest.model_validate(accepted).edits) == 2
    accepted["edits"][1] = {
        "kind": "repository-upsert",
        "repository": {"id": "organization/model-name", "type": "model"},
    }
    with pytest.raises(ValidationError):
        ManagedEditRequest.model_validate(accepted)


def test_edit_bound_is_enforced_before_any_deduplication():
    edits = [removal(f"repo-{index}") for index in range(256)]
    assert (
        len(ManagedEditRequest.model_validate({"base_revision": BASE, "edits": edits}).edits) == 256
    )
    with pytest.raises(ValidationError):
        ManagedEditRequest.model_validate({"base_revision": BASE, "edits": [*edits, removal()]})


@pytest.mark.parametrize(
    "edit",
    [
        {"kind": "unknown"},
        {"kind": "repository-remove", "repository_type": "model", "repository_id": None},
        {
            "kind": "repository-upsert",
            "repository": {"id": "organization/name", "type": "model", "enabled": 1},
        },
        {
            "kind": "repository-upsert",
            "repository": {"id": "organization/name", "type": "model", "revision": None},
        },
        {
            "kind": "repository-upsert",
            "repository": {"id": "organization/name", "type": "model", "token": "private"},
        },
        {
            "kind": "repository-remove",
            "repository_type": "model",
            "repository_id": "organization/name",
            "path": "/tmp/no",
        },
        {"kind": "settings-replace", "settings": {}},
        {"kind": "settings-replace", "settings": {"storage": {}}},
        {"kind": "settings-replace", "settings": {"sync": None}},
        {"kind": "settings-replace", "settings": {"sync": {"max_workers": None}}},
        {"kind": "settings-replace", "settings": {"storage": {"archive_root": "/tmp/no"}}},
        {"kind": "settings-replace", "settings": {"storage": {"archive_id": examples.ARCHIVE_ID}}},
        {"kind": "settings-replace", "settings": {"verification": {"algorithm": "sha256"}}},
        {"kind": "settings-replace", "settings": {"verification": {"hash_new_content": True}}},
        {"kind": "settings-replace", "settings": {"hub": {"token_mode": "optional"}}},
    ],
)
def test_edit_union_rejects_unknown_coercive_null_and_authority_forms(edit):
    with pytest.raises(ValidationError):
        ManagedEditRequest.model_validate({"base_revision": BASE, "edits": [edit]})


@pytest.mark.parametrize(
    ("section", "field", "valid", "invalid"),
    [
        ("storage", "publication_mode", "copy", "link"),
        ("storage", "minimum_free_space_gib", 0, -1),
        ("storage", "minimum_free_space_percent", 100, 101),
        ("storage", "maximum_revisions", 5, 4),
        ("sync", "max_workers", 32, 33),
        ("sync", "lock_wait_seconds", 0, 86401),
        ("sync", "continue_on_repository_error", False, 0),
        ("sync", "dependency_policy", "warn", "ignore"),
        ("sync", "stale_staging_age_hours", 8760, 0),
        ("verification", "lock_wait_seconds", 604800, 604801),
        ("repair", "retired_instance_grace_hours", 168, 167),
    ],
)
def test_all_eleven_global_fields_keep_existing_strict_constraints(section, field, valid, invalid):
    body = {
        "base_revision": BASE,
        "edits": [{"kind": "settings-replace", "settings": {section: {field: valid}}}],
    }
    assert ManagedEditRequest.model_validate(body).edits
    body["edits"][0]["settings"][section][field] = invalid
    with pytest.raises(ValidationError):
        ManagedEditRequest.model_validate(body)


def test_only_one_settings_replacement_is_permitted_even_for_distinct_tables():
    with pytest.raises(ValidationError):
        ManagedEditRequest.model_validate(
            {
                "base_revision": BASE,
                "edits": [
                    {"kind": "settings-replace", "settings": {"sync": {"max_workers": 2}}},
                    {"kind": "settings-replace", "settings": {"storage": {"maximum_revisions": 5}}},
                ],
            }
        )


@pytest.mark.parametrize("model", [ValidationSubmission, PlanSubmission])
def test_managed_forms_exclude_literal_forms_nulls_and_selector_subsets(model):
    managed = {"base_revision": BASE, "edits": []}
    assert model.model_validate({"managed": managed}).canonical_body() == {"managed": managed}
    for body in (
        {"managed": None},
        {"managed": managed, "candidate": "schema_version=1"},
        {"managed": managed, "candidate": None},
        {"managed": managed, "selectors": [SELECTOR]},
        {"managed": {"base_revision": BASE, "edits": None}},
        {"managed": {"base_revision": BASE, "edits": [], "token": "private"}},
    ):
        with pytest.raises(ValidationError):
            model.model_validate(body)
    if model is PlanSubmission:
        assert model.model_validate({"managed": managed, "selectors": []}).canonical_body() == {
            "managed": managed
        }


def test_legacy_canonical_bodies_are_exact_and_managed_sparse_values_remain_omitted():
    assert ValidationSubmission.model_validate({}).canonical_body() == {"candidate": None}
    assert PlanSubmission.model_validate({}).canonical_body() == {"selectors": []}
    literal = {"candidate": "schema_version=1"}
    assert ValidationSubmission.model_validate(literal).canonical_body() == literal
    assert PlanSubmission.model_validate(literal).canonical_body() == {"selectors": [], **literal}
    body = {
        "managed": {
            "base_revision": BASE,
            "edits": [
                {
                    "kind": "settings-replace",
                    "settings": {
                        "sync": {"continue_on_repository_error": False, "lock_wait_seconds": 0}
                    },
                }
            ],
        }
    }
    assert PlanSubmission.model_validate(body).canonical_body() == body


def test_private_preparation_is_bounded_and_public_validation_has_no_candidate_or_raw_hash():
    body = {**binding(), "candidate": "schema_version=1", "editable": editable()}
    assert ConfigPrepared.model_validate(body).candidate == "schema_version=1"
    for candidate in ("", "é" * 524289, "\ud800"):
        body["candidate"] = candidate
        with pytest.raises(ValidationError):
            ConfigPrepared.model_validate(body)
    public = {**binding(), "valid": True}
    assert ManagedValidation.model_validate(public).model_dump(mode="json") == public
    for extras in ({"candidate": "private"}, {"config_sha256": BASE}, {"valid": 1}):
        with pytest.raises(ValidationError):
            ManagedValidation.model_validate({**public, **extras})


def sizing() -> dict[str, Any]:
    return {
        "repositories": [
            {
                "enabled": True,
                "estimated_new_bytes": 0,
                "file_count": 1,
                "logical_bytes": 5,
                "projected_publication_bytes": 5,
                "publication_mode": "hardlink",
                "repository_id": "organization/model-name",
                "repository_type": "model",
                "requested_revision": "main",
                "resolved_commit_sha": examples.SHA,
                "upstream_state": "available",
            }
        ]
    }


def test_empty_scope_assessment_is_successful_without_hub_sizing_and_is_bound():
    body: dict[str, Any] = {**binding(), "complete": True, "sizing": None}
    assert ManagedAssessment.model_validate(body).model_dump(mode="json") == body
    body["sizing"] = {"repositories": []}
    with pytest.raises(ValidationError):
        ManagedAssessment.model_validate(body)


def test_nonempty_assessment_requires_exact_complete_sizing_not_a_caller_subset():
    body = {**binding(), "required_selectors": [SELECTOR], "complete": True, "sizing": sizing()}
    assert ManagedAssessment.model_validate(body).complete
    for scope in (
        [],
        [SELECTOR, SELECTOR],
        [SELECTOR + "@" + examples.SHA],
        ["dataset:organization/other"],
    ):
        with pytest.raises(ValidationError):
            ManagedAssessment.model_validate({**body, "required_selectors": scope})
    with pytest.raises(ValidationError):
        ManagedAssessment.model_validate({**body, "sizing": None})
    assert not ManagedAssessment.model_validate(
        {**body, "complete": False, "sizing": None}
    ).complete
    for field, value in (
        ("enabled", False),
        ("estimated_new_bytes", None),
        ("file_count", None),
        ("logical_bytes", None),
        ("projected_publication_bytes", None),
        ("resolved_commit_sha", None),
        ("upstream_state", "unreachable"),
    ):
        changed = deepcopy(body)
        changed["sizing"]["repositories"][0][field] = value
        with pytest.raises(ValidationError):
            ManagedAssessment.model_validate(changed)
        assert not ManagedAssessment.model_validate({**changed, "complete": False}).complete


@pytest.mark.parametrize("selector", ["bad", "model:../escape", "model:organization/name@abc", 123])
def test_malformed_helper_scope_is_a_collected_validation_error(selector):
    with pytest.raises(ValidationError):
        ManagedValidation.model_validate(
            {**binding(), "required_selectors": [selector], "valid": True}
        )
