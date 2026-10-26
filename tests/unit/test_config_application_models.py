"""Exact application intent and safe, independently versioned host outcomes."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from hfcache.config_models import (
    ConfigApplicationOutcome,
    ConfigApplicationSubmission,
    SettingsReplace,
)
from tests.fixtures.examples import ARCHIVE_ID


def application():
    return {
        "managed": {
            "base_revision": "a" * 64,
            "edits": [{"kind": "settings-replace", "settings": {"sync": {"max_workers": 2}}}],
        },
        "preview": {"operation_id": "b" * 32, "key": "owned.preview-1_~+"},
    }


def outcome():
    return {
        "schema_version": 1,
        "archive_id": ARCHIVE_ID,
        "operation_id": "c" * 32,
        "request_digest": "d" * 64,
        "base_revision": "a" * 64,
        "candidate_revision": "e" * 64,
        "config_fingerprint": "f" * 64,
        "state": "confirmed",
        "pending": False,
    }


def test_application_canonical_body_preserves_only_validated_intent_and_preview():
    body = application()
    parsed = ConfigApplicationSubmission.model_validate(body)
    assert parsed.canonical_body() == body
    body["managed"]["edits"][0]["settings"]["sync"]["max_workers"] = 3
    edit = parsed.managed.edits[0]
    assert isinstance(edit, SettingsReplace)
    assert edit.settings.sync is not None
    assert edit.settings.sync.max_workers == 2
    assert parsed.preview.operation_id == "b" * 32
    assert parsed.preview.key == "owned.preview-1_~+"
    assert "null" not in str(parsed.canonical_body())


@pytest.mark.parametrize("key", ["", "x" * 129, "secret/key", "x\n", 123, None])
def test_preview_reference_uses_existing_exact_key_grammar(key):
    body = application()
    body["preview"]["key"] = key
    with pytest.raises(ValidationError):
        ConfigApplicationSubmission.model_validate(body)


@pytest.mark.parametrize(
    ("field", "value"),
    [("operation_id", "b" * 31), ("operation_id", "B" * 32), ("key", True), ("extra", "hidden")],
)
def test_preview_reference_is_closed_and_strict(field, value):
    body = application()
    body["preview"][field] = value
    with pytest.raises(ValidationError):
        ConfigApplicationSubmission.model_validate(body)


@pytest.mark.parametrize(
    "change", [{"candidate": "private"}, {"selectors": []}, {"preview": None}, {"managed": None}]
)
def test_application_never_accepts_literal_candidate_or_mixed_forms(change):
    with pytest.raises(ValidationError):
        ConfigApplicationSubmission.model_validate(application() | change)


def test_outcome_preserves_unknown_and_pending_without_promoting_confirmation():
    unknown = outcome() | {
        "base_revision": None,
        "candidate_revision": None,
        "config_fingerprint": None,
        "state": "unknown",
        "pending": True,
    }
    assert ConfigApplicationOutcome.model_validate(unknown).model_dump(mode="json") == unknown
    confirmed = outcome() | {"pending": True}
    assert ConfigApplicationOutcome.model_validate(confirmed).state == "confirmed"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", True),
        ("pending", 1),
        ("state", "succeeded"),
        ("request_digest", "A" * 64),
        ("candidate_revision", "e" * 63),
        ("operation_id", "c" * 33),
        ("config_fingerprint", 123),
        ("candidate", "private"),
    ],
)
def test_outcome_is_typed_and_excludes_private_material(field, value):
    body = outcome()
    body[field] = value
    with pytest.raises(ValidationError):
        ConfigApplicationOutcome.model_validate(body)


def test_outcome_requires_explicit_nullable_fields():
    for field in outcome():
        body = deepcopy(outcome())
        del body[field]
        with pytest.raises(ValidationError):
            ConfigApplicationOutcome.model_validate(body)


@pytest.mark.parametrize(
    "state", ["staged", "unchanged", "installed_unconfirmed", "confirmed", "conflict", "unknown"]
)
def test_outcome_never_mixes_partial_configuration_identity(state):
    body = outcome() | {"state": state, "candidate_revision": None}
    with pytest.raises(ValidationError):
        ConfigApplicationOutcome.model_validate(body)
    body |= {"base_revision": None, "config_fingerprint": None}
    if state == "unknown":
        assert ConfigApplicationOutcome.model_validate(body).state == "unknown"
    else:
        with pytest.raises(ValidationError):
            ConfigApplicationOutcome.model_validate(body)
