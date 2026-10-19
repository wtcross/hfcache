"""Candidate responses and keys preserve legacy intent without storing content."""

import json

import httpx
import pytest

from hfcache.api.auth import authenticate_bearer, load_credentials
from hfcache.api.command_models import PlanSubmission, VerificationSubmission
from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.errors import HfcacheError
from hfcache.services.candidates import parse_candidate
from tests.unit.test_api_candidates_adversarial import READER, _post, _result
from tests.unit.test_api_candidates_adversarial import (
    configured as configured,  # noqa: PLC0414 - shared pytest fixture
)
from tests.unit.test_api_client_adversarial import BASE, _accepted, _read, _response


def test_new_optional_plan_field_preserves_old_canonical_identity_and_verification_nulls():
    assert PlanSubmission.model_validate({}).canonical_body() == {"selectors": []}
    candidate = PlanSubmission(candidate="schema_version=1").canonical_body()
    assert candidate == {"selectors": [], "candidate": "schema_version=1"}
    assert VerificationSubmission(mode="new").canonical_body() == {
        "mode": "new",
        "revision": None,
        "run_id": None,
    }


def test_historical_installed_plan_binding_is_returned_before_new_policy_load(configured):
    principal = authenticate_bearer(load_credentials(configured.server), "Bearer " + READER)
    old = configured.app.state.operations.admit(
        principal,
        "historical-plan",
        "/api/v1/plans",
        {"selectors": []},
        configured.app.state.policy.snapshot,
    )
    configured.policy.write_text("invalid installed policy [")

    retry = _post(configured, "/plans", {}, key="historical-plan", token=READER)

    assert retry.status_code == 202, retry.text
    assert retry.json()["created"] is False
    assert retry.json()["operation"]["operation_id"] == old.receipt.operation_id
    assert configured.calls == []
    assert len(configured.app.state.operations.list()) == 1


def test_candidate_validation_keeps_useful_legacy_fields_separate_from_authority(configured):
    installed = _post(configured, "/config/validate", {}, token=READER).json()["envelope"]
    assert set(installed["data"]) == {
        "config_fingerprint",
        "enabled_repositories",
        "repositories",
        "token_source",
    }
    candidate = configured.policy.read_text() + (
        '\n[[repositories]]\ntype="dataset"\nid="candidate/disabled"\nenabled=false\n'
    )
    validated = _post(configured, "/config/validate", {"candidate": candidate}).json()["envelope"]

    assert validated["exit_code"] == 0
    data = validated["data"]
    assert data["repositories"] == 2
    assert data["enabled_repositories"] == 1
    assert data["token_source"] == "not-resolved"
    assert data["valid"]
    assert data["syntax_valid"]
    assert data["authority_compatible"]
    assert data["authority_mismatches"] == []
    assert data["config_fingerprint"] != installed["data"]["config_fingerprint"]
    assert configured.calls == []


def test_every_candidate_problem_is_reported_without_persisting_raw_rejected_values(configured):
    marker = "opaqueUnregisteredCandidateMarker"
    candidate = (
        f'schema_version=1\n{marker}="privateValueMustNotEscape"\n'
        '[storage]\narchive_root="relative"\narchive_id="malformed-secret-like-value"\n'
    )
    with pytest.raises(HfcacheError) as caught:
        parse_candidate(candidate)
    expected = [problem.code for problem in caught.value.problems]

    validated = _post(configured, "/config/validate", {"candidate": candidate}).json()["envelope"]
    planned = _result(configured, _post(configured, "/plans", {"candidate": candidate}))

    assert [item["code"] for item in validated["errors"]] == expected
    assert [item["code"] for item in planned["errors"]] == expected
    assert validated["data"]["valid"] is False
    assert validated["data"]["syntax_valid"] is False
    assert validated["data"]["authority_compatible"] is None
    assert configured.calls == []
    encoded = json.dumps((validated, planned)) + "".join(
        path.read_text() for path in configured.app.state.operations.root.glob("*.json")
    )
    for value in (marker, "privateValueMustNotEscape", "malformed-secret-like-value", candidate):
        assert value not in encoded


def test_client_candidate_methods_send_content_without_resolving_archive_policy(monkeypatch):
    monkeypatch.setattr(
        "hfcache.client.resolve_api_token", lambda _: "explicitApiCredentialForClientFixture"
    )
    requests = []
    candidate = "schema_version=1\n# bounded content, never a server-selected file\n"

    def respond(request):
        requests.append(request)
        if request.url.path.endswith("/config/validate"):
            payload = _read(data={"valid": True, "syntax_valid": True})
            payload["envelope"]["command"] = "config validate"
            return _response(payload)
        payload = _accepted()
        payload["operation"]["route"] = "/api/v1/plans"
        return _response(payload, status=202, headers={"Location": payload["links"]["status"]})

    with ApiClient(
        ClientConfig(schema_version=1, api_url=BASE), transport=httpx.MockTransport(respond)
    ) as client:
        assert client.validate_candidate(candidate).envelope.data["syntax_valid"] is True
        admission = client.plan_candidate(
            candidate, ["model:example/model"], key="candidate-client"
        )

    assert admission.key == "candidate-client"
    assert json.loads(requests[0].content) == {"candidate": candidate}
    assert json.loads(requests[1].content) == {
        "candidate": candidate,
        "selectors": ["model:example/model"],
    }
    assert "idempotency-key" not in requests[0].headers
    assert requests[1].headers["idempotency-key"] == "candidate-client"


@pytest.mark.parametrize("route", ["/config/validate", "/plans"])
def test_deep_toml_is_a_safe_domain_refusal_instead_of_parser_failure(configured, route):
    candidate = "entry=" + "{nested=" * 1200 + "0" + "}" * 1200
    response = _post(configured, route, {"candidate": candidate})
    envelope = _result(configured, response) if route == "/plans" else response.json()["envelope"]
    assert envelope["exit_code"] == 10
    assert [problem["code"] for problem in envelope["errors"]] == ["HFCFG002"]
    assert configured.calls == []


def test_tag_only_candidates_keep_policy_identity_but_conflict_under_same_key(configured):
    first = configured.policy.read_text() + '\ntags=["coding"]\n'
    second = configured.policy.read_text() + '\ntags=["vision"]\n'
    assert parse_candidate(first).fingerprint() == parse_candidate(second).fingerprint()
    assert (
        parse_candidate(first).curation_fingerprint()
        != parse_candidate(second).curation_fingerprint()
    )
    admitted = _post(configured, "/plans", {"candidate": first}, key="tag-change")
    assert admitted.status_code == 202
    conflict = _post(configured, "/plans", {"candidate": second}, key="tag-change")
    assert conflict.status_code == 409
    assert len(configured.app.state.operations.list()) == 1
