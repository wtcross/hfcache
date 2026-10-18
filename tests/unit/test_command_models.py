"""Strict canonical commands and reserved candidate authority are transport boundaries."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hfcache.api.command_models import (
    AcceptanceResponse,
    CandidatePayload,
    DiagnosticsSubmission,
    InstalledValidationSubmission,
    PlanSubmission,
    SyncSubmission,
    VerificationSubmission,
)
from hfcache.config import validate_config_mapping
from hfcache.errors import HfcacheError, RequestError
from hfcache.services.candidates import (
    MAXIMUM_CANDIDATE_BYTES,
    assess_candidate,
    authority_mismatches,
    require_compatible_authority,
)
from tests.fixtures import examples

SELECTOR = "model:organization/model-name"
CANDIDATE = (
    'schema_version=1\n[storage]\narchive_root="/tmp/synthetic-archive"\n'
    f'archive_id="{examples.ARCHIVE_ID}"\n'
)


@pytest.mark.parametrize("model", [SyncSubmission, PlanSubmission])
def test_selection_is_immutable_canonical_identity_not_requested_revision(model):
    original = [SELECTOR + "@" + examples.SHA, "dataset:organization/data", SELECTOR]
    parsed = model.model_validate({"selectors": original})
    original.clear()
    assert parsed.selectors == ("dataset:organization/data", SELECTOR)
    assert model.model_validate({}).selectors == ()
    assert parsed.canonical_body() == {"selectors": ["dataset:organization/data", SELECTOR]}


@pytest.mark.parametrize("value", [1, True, None, {}, [], 1.25])
def test_selector_items_never_coerce_or_raise_unclassified_attribute_errors(value):
    with pytest.raises(ValidationError):
        SyncSubmission.model_validate({"selectors": [value]})


@pytest.mark.parametrize("value", ["model/organization/name", SELECTOR + "@abc123", "../escape"])
def test_malformed_selector_is_refused(value):
    with pytest.raises((ValidationError, HfcacheError)):
        SyncSubmission.model_validate({"selectors": [value]})


@pytest.mark.parametrize("payload", [{"selectors": SELECTOR}, {"selectors": [SELECTOR] * 101}])
def test_selector_input_is_bounded_array(payload):
    with pytest.raises(ValidationError):
        SyncSubmission.model_validate(payload)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"mode": "estimate"},
        {"mode": "full", "run_id": examples.RUN},
        {"mode": "new", "revision": SELECTOR + "@" + examples.SHA},
        {"mode": "revision"},
        {"mode": "revision", "revision": SELECTOR},
        {"mode": "revision", "revision": 1},
        {"mode": "new", "run_id": 1},
        {"mode": "full", "estimate": True},
    ],
)
def test_verification_modes_have_exact_nonoverlapping_scope(body):
    with pytest.raises((ValidationError, HfcacheError)):
        VerificationSubmission.model_validate(body)


@pytest.mark.parametrize(
    ("body", "mode", "revision", "run_id"),
    [
        ({"mode": "full"}, "full", None, None),
        ({"mode": "new", "run_id": examples.RUN}, "new", None, examples.RUN),
        (
            {"mode": "revision", "revision": SELECTOR + "@" + examples.SHA},
            "revision",
            SELECTOR + "@" + examples.SHA,
            None,
        ),
    ],
)
def test_verification_dto_projects_shared_request_without_losing_scope(
    body, mode, revision, run_id
):
    request = VerificationSubmission.model_validate(body).service_request()
    assert request.mode == mode
    assert request.revision == revision
    assert request.run_id == run_id


@pytest.mark.parametrize("body", [{}, {"read_only": "true"}, {"read_only": 1}, {"read_only": None}])
def test_diagnostics_requires_explicit_strict_effect_choice(body):
    with pytest.raises(ValidationError):
        DiagnosticsSubmission.model_validate(body)


@pytest.mark.parametrize("model", [InstalledValidationSubmission])
def test_candidate_or_server_path_is_not_an_implemented_http_command(model):
    for body in ({"candidate": CANDIDATE}, {"config": "/tmp/arbitrary.toml"}):
        with pytest.raises(ValidationError):
            model.model_validate(body)


def test_plan_accepts_candidate_content_but_never_a_server_path():
    assert PlanSubmission(candidate=CANDIDATE).candidate == CANDIDATE
    for body in ({"candidate": None}, {"config": "/tmp/arbitrary.toml"}):
        with pytest.raises(ValidationError):
            PlanSubmission.model_validate(body)


def test_response_schema_resolves_nested_receipt_and_candidate_hook_is_content_only():
    schema = AcceptanceResponse.model_json_schema()
    assert "OperationView" in schema["$defs"]
    assert set(schema["properties"]) == {
        "schema_version",
        "request_id",
        "archive_id",
        "config_fingerprint",
        "operation",
        "created",
        "links",
    }
    assert CandidatePayload(candidate=CANDIDATE).candidate == CANDIDATE
    with pytest.raises(ValidationError):
        CandidatePayload.model_validate({"path": "/tmp/candidate.toml"})


def installed():
    return validate_config_mapping(
        {
            "schema_version": 1,
            "storage": {
                "archive_root": "/tmp/synthetic-archive",
                "archive_id": examples.ARCHIVE_ID,
            },
        }
    )


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("storage", "archive_root", Path("/tmp/other-archive")),
        ("storage", "archive_id", "e046da76-d3cb-460a-a655-fd31bd9d0503"),
        ("hub", "endpoint", "https://other.example"),
        ("hub", "token_mode", "required"),
        ("hub", "credential_name", "other-token"),
        ("hub", "expected_account", "other-account"),
    ],
)
def test_candidate_cannot_change_any_installed_authority_field(section, field, value):
    current = installed()
    changed = getattr(current, section).model_copy(update={field: value})
    proposed = current.model_copy(update={section: changed})
    assert authority_mismatches(proposed, current) == (f"{section}.{field}",)
    with pytest.raises(RequestError) as caught:
        require_compatible_authority(proposed, current)
    assert caught.value.status_code == 409
    assert str(value) not in str(caught.value)


def test_candidate_assessment_changes_policy_without_reading_files_or_resolving_credentials(
    monkeypatch,
):
    def forbidden(*_args, **_kwargs):
        pytest.fail("pure candidate assessment performed an authority action")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr("hfcache.credentials.resolve_token", forbidden)
    monkeypatch.setattr("hfcache.hub.HubClient.of", forbidden)
    assessment = assess_candidate(
        CANDIDATE + '[[repositories]]\nid="organization/model-name"\ntype="model"\n', installed()
    )
    assert assessment.authority_compatible
    assert assessment.config.repositories[0].id == "organization/model-name"
    require_compatible_authority(assessment.config, installed())


@pytest.mark.parametrize("candidate", ["", "x" * (MAXIMUM_CANDIDATE_BYTES + 1), "\ud800"])
def test_candidate_hook_bounds_bytes_before_parsing(candidate):
    with pytest.raises(RequestError):
        assess_candidate(candidate, installed())


def test_candidate_syntax_error_does_not_echo_content():
    secret = "opaque-candidate-do-not-disclose"
    with pytest.raises(HfcacheError) as caught:
        assess_candidate('secret = ["' + secret, installed())
    assert secret not in str(caught.value)
    assert secret not in json.dumps([problem.message for problem in caught.value.problems])
