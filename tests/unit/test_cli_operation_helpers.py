"""Operation observation preserves authority and handles without replay (API-013)."""

import json
import subprocess
import sys

import httpx
import pytest

from hfcache import cli_client
from hfcache.cli import GlobalOptions
from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.client_errors import ClientConnectionError, ClientProtocolError, UncertainSubmission
from hfcache.client_models import Submission
from hfcache.errors import ConfigurationError
from hfcache.services import commands, requests
from tests.unit.test_api_client_adversarial import (
    BASE,
    OPERATION,
    RUN,
    TIME,
    TOKEN,
    _accepted,
    _operation,
    _read,
    _response,
)


@pytest.fixture
def settings(tmp_path):
    token = tmp_path / "token"
    token.write_text(TOKEN)
    token.chmod(0o600)
    return ClientConfig(
        schema_version=1, api_url=BASE, api_token_file=token, read_retries=0, poll_interval=0.1
    )


def _events(numbers, *, oldest=1, truncated=False, after=0):
    return _read(
        data={
            "operation_id": OPERATION,
            "events": [
                {
                    "schema_version": 1,
                    "sequence": number,
                    "at": TIME,
                    "kind": "operation.progress",
                    "message": "safe progress",
                }
                for number in numbers
            ],
            "next_cursor": numbers[-1] if numbers else after,
            "oldest_sequence": oldest,
            "truncated": truncated,
        }
    )


def test_request_import_is_independent_and_legacy_service_exports_are_identical():
    code = """
import sys
from hfcache.services.requests import ALL_CONFIGURED, READ_ONLY, VerificationRequest
assert VerificationRequest(full=True).mode == 'full'
assert ALL_CONFIGURED.selectors == () and READ_ONLY
assert not set(sys.modules) & {
    'hfcache.config', 'hfcache.credentials', 'hfcache.hub', 'huggingface_hub',
    'hfcache.storage', 'hfcache.services.commands', 'hfcache.preflight',
    'hfcache.api.verification_worker', 'fastapi', 'uvicorn'
}
"""
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
    for name in (
        "ALL_CONFIGURED",
        "DoctorRequest",
        "InitializationRequest",
        "MaintenanceRequest",
        "QuarantineRequest",
        "RepairRequest",
        "SelectionRequest",
        "VerificationRequest",
        "_chosen_modes",
        "_mode_option",
        "_verification_mode",
    ):
        assert getattr(commands, name) is getattr(requests, name)


@pytest.mark.parametrize(
    ("intent", "code"),
    [
        ({}, "HFARG003"),
        ({"new": True, "full": True}, "HFARG002"),
        ({"full": True, "run_id": RUN}, "HFARG002"),
    ],
)
def test_pure_verification_mode_keeps_existing_refusal_taxonomy(intent, code):
    with pytest.raises(ConfigurationError) as caught:
        _ = requests.VerificationRequest(**intent).mode
    assert [problem.code for problem in caught.value.problems] == [code]


@pytest.mark.parametrize(
    ("revision", "location"),
    [
        ("model:org/model", "--revision"),
        ("model:org/model@abcdef0", "model:org/model@abcdef0"),
        ("not-a-selector", "not-a-selector"),
    ],
)
def test_revision_scope_grammar_is_a_pure_pre_submission_refusal(revision, location):
    request = requests.VerificationRequest(revision=revision)
    assert request.mode == "revision"
    with pytest.raises(ConfigurationError) as caught:
        request.validate_scope()
    assert caught.value.problems[0].code == "HFARG001"
    assert caught.value.problems[0].location == location


def test_run_scope_validation_does_not_change_mode_ordering():
    request = requests.VerificationRequest(new=True, run_id="not-a-run")
    assert request.mode == "new"
    with pytest.raises(ConfigurationError) as caught:
        request.validate_scope()
    assert caught.value.problems[0].code == "HFARG001"
    assert caught.value.problems[0].location == "--run-id"
    requests.VerificationRequest(new=True, run_id=RUN).validate_scope()
    requests.VerificationRequest(revision="model:org/model@" + "a" * 40).validate_scope()


def test_quarantine_scope_checks_only_transaction_grammar_before_submission():
    requests.QuarantineRequest(("a" * 32,), apply=True).validate_scope()
    with pytest.raises(ConfigurationError) as caught:
        requests.QuarantineRequest(("not-a-transaction",), apply=True).validate_scope()
    assert caught.value.problems[0].code == "HFARG001"


def test_submit_callbacks_precede_transmission_and_wait_and_detach_is_not_an_envelope(settings):
    order = []

    def respond(request):
        order.append("POST")
        assert request.method == "POST"
        assert order == ["key", "POST"]
        accepted = _accepted()
        return _response(accepted, status=202, headers={"Location": accepted["links"]["status"]})

    with ApiClient(settings, transport=httpx.MockTransport(respond)) as client:
        detached = cli_client.submit_job(
            client,
            "/api/v1/syncs",
            {"selectors": []},
            key="original-key",
            detach=True,
            on_key=lambda _key: order.append("key"),
            on_accepted=lambda _accepted: order.append("accepted"),
        )
    assert order == ["key", "POST", "accepted"]
    assert isinstance(detached, Submission)
    payload = cli_client.admission_payload(detached)
    assert payload == {
        "schema_version": 1,
        "kind": "operation_admission",
        "idempotency_key": "original-key",
        "acceptance": detached.acceptance.model_dump(mode="json"),
    }
    assert not {"envelope", "outcome", "exit_code"} & payload.keys()


def test_default_submit_returns_exact_failed_domain_envelope_after_progress(settings):
    order = []
    failed = _read(data={"preserved": ["partial", "evidence"]})
    failed["envelope"].update(
        command="sync",
        exit_code=40,
        outcome="failed",
        errors=[{"code": "HFVER004", "message": "finding", "repository": None, "context": {}}],
    )

    def respond(request):
        if request.method == "POST":
            order.append("POST")
            accepted = _accepted()
            return _response(
                accepted, status=202, headers={"Location": accepted["links"]["status"]}
            )
        if request.url.path.endswith("/events"):
            order.append("events")
            assert "limit" not in request.url.params
            after = int(request.url.params["after"])
            page = _events([1] if after == 0 else [], after=after)
            return _response(page)
        if request.url.path.endswith("/result"):
            order.append("result")
            return _response(failed)
        order.append("status")
        return _response(_read(data={"operation": _operation(state="failed")}))

    with ApiClient(settings, transport=httpx.MockTransport(respond)) as client:
        result = cli_client.submit_job(
            client,
            "/api/v1/syncs",
            {},
            on_key=lambda _key: order.append("key"),
            on_accepted=lambda _accepted: order.append("accepted"),
            on_event=lambda _events: order.append("progress"),
        )
    assert not isinstance(result, Submission)
    assert result.to_payload() == failed["envelope"]
    assert result.run_id == RUN
    assert result.run_id != OPERATION
    assert order == ["key", "POST", "accepted", "status", "events", "progress", "events", "result"]


def test_terminal_resume_fetches_retained_events_after_cursor_and_redacts_messages(settings):
    seen, pages = [], []
    event_payload = _events([5, 6], oldest=5, truncated=True)
    event_payload["envelope"]["data"]["events"][0]["message"] = "value=" + TOKEN

    def respond(request):
        seen.append(request)
        if request.url.path.endswith("/events"):
            assert "limit" not in request.url.params
            after = int(request.url.params["after"])
            if after == 2:
                return _response(event_payload)
            assert after == 6
            page = _events([], oldest=5, after=after)
            return _response(page)
        if request.url.path.endswith("/result"):
            return _response(_read(data={"done": True}))
        return _response(_read(data={"operation": _operation(state="succeeded")}))

    with ApiClient(settings, transport=httpx.MockTransport(respond)) as client:
        result = cli_client.observe_operation(client, OPERATION, on_event=pages.append, after=2)
    assert result.data == {"done": True}
    assert len(pages) == 1
    assert pages[0].truncated
    assert pages[0].oldest_sequence == 5
    assert pages[0].next_cursor == 6
    assert TOKEN not in repr(pages)
    assert all(request.method == "GET" for request in seen)


def test_one_deadline_includes_native_event_chunks_and_retains_operation(settings):
    clock, seen = [0.0], []

    class Trickle(httpx.SyncByteStream):
        def __iter__(self):
            body = json.dumps(_events([1])).encode()
            clock[0] += 0.6
            yield body[:20]
            clock[0] += 0.6
            yield body[20:]

    def respond(request):
        seen.append(request)
        if request.url.path.endswith("/events"):
            assert request.extensions["timeout"]["read"] <= 1
            return httpx.Response(
                200, stream=Trickle(), headers={"content-type": "application/json"}
            )
        return _response(_read(data={"operation": _operation(state="running")}))

    with (
        ApiClient(
            settings, transport=httpx.MockTransport(respond), monotonic=lambda: clock[0]
        ) as client,
        pytest.raises(ClientConnectionError) as caught,
    ):
        cli_client.observe_operation(client, OPERATION, timeout=1, on_event=lambda _page: None)
    assert caught.value.operation_id == OPERATION
    assert caught.value.route == "/api/v1/syncs"
    assert [request.method for request in seen] == ["GET", "GET"]
    assert seen[-1].url.path.endswith("/events")


@pytest.mark.parametrize("budget", ["pages", "deadline"])
def test_final_adaptive_empty_drain_uses_existing_page_and_deadline_budgets(settings, budget):
    clock, seen = [0.0], []
    settings = settings.model_copy(update={"max_pages": 1 if budget == "pages" else 10000})

    def respond(request):
        seen.append(request)
        if request.url.path.endswith("/events"):
            assert "limit" not in request.url.params
            after = int(request.url.params["after"])
            page = _events([1] if after == 0 else [], after=after)
            if after:
                clock[0] = 1.1
            return _response(page)
        assert not request.url.path.endswith(("/result", "/capabilities"))
        return _response(_read(data={"operation": _operation(state="succeeded")}))

    expected = ClientProtocolError if budget == "pages" else ClientConnectionError
    with (
        ApiClient(
            settings, transport=httpx.MockTransport(respond), monotonic=lambda: clock[0]
        ) as client,
        pytest.raises(expected) as caught,
    ):
        cli_client.observe_operation(client, OPERATION, timeout=1, on_event=lambda _page: None)
    assert caught.value.operation_id == OPERATION
    assert caught.value.route == "/api/v1/syncs"
    assert len(seen) == (2 if budget == "pages" else 3)


@pytest.mark.parametrize("limit", [None, 101])
def test_default_event_page_remains_bounded_while_explicit_limit_retains_its_contract(
    settings, limit
):
    def respond(request):
        if request.url.path.endswith("/events"):
            assert request.url.params.get("limit") == (None if limit is None else "101")
            return _response(_events(list(range(1, 102))))
        return _response(_read(data={"operation": _operation(state="succeeded")}))

    with ApiClient(settings, transport=httpx.MockTransport(respond)) as client:
        if limit is None:
            with pytest.raises(ClientProtocolError):
                client.events(OPERATION)
        else:
            assert len(client.events(OPERATION, limit=limit).events) == limit


@pytest.mark.parametrize("interrupted", [False, True])
def test_wait_failure_retains_original_key_id_and_route_without_replay(settings, interrupted):
    seen, clock = [], [0.0]

    def respond(request):
        seen.append(request)
        if request.method == "POST":
            accepted = _accepted()
            return _response(
                accepted, status=202, headers={"Location": accepted["links"]["status"]}
            )
        if interrupted:
            raise KeyboardInterrupt
        return _response(_read(data={"operation": _operation(state="running")}))

    def sleep(seconds):
        clock[0] += seconds

    with (
        ApiClient(
            settings,
            transport=httpx.MockTransport(respond),
            monotonic=lambda: clock[0],
            sleep=sleep,
        ) as client,
        pytest.raises(ClientConnectionError) as caught,
    ):
        cli_client.submit_job(client, "/api/v1/syncs", {}, key="retained-key", timeout=0.2)
    assert caught.value.problems[0].code == "HFAPI019"
    assert caught.value.key == "retained-key"
    assert caught.value.operation_id == OPERATION
    assert caught.value.route == "/api/v1/syncs"
    assert [request.method for request in seen].count("POST") == 1
    assert all(request.method in {"POST", "GET"} for request in seen)


def test_interrupt_before_usable_ack_keeps_original_key_uncertain(settings):
    seen = []

    def respond(request):
        seen.append(request)
        raise KeyboardInterrupt

    with (
        ApiClient(settings, transport=httpx.MockTransport(respond)) as client,
        pytest.raises(UncertainSubmission) as caught,
    ):
        cli_client.submit_job(client, "/api/v1/syncs", {}, key="same-key")
    assert caught.value.key == "same-key"
    assert caught.value.route == "/api/v1/syncs"
    assert getattr(caught.value, "operation_id", None) is None
    assert len(seen) == 1


def test_show_and_lookup_preserve_server_envelope_metadata(settings):
    payload = _read(data={"operation": _operation(state="succeeded")})
    payload["envelope"]["command"] = "operations show"
    with ApiClient(settings, transport=httpx.MockTransport(lambda _: _response(payload))) as client:
        assert client.operation_response(OPERATION).envelope.to_payload() == payload["envelope"]
        payload["envelope"]["command"] = "operations lookup"
        assert client.lookup_response("same-key").envelope.to_payload() == payload["envelope"]


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), 86401])
def test_invalid_cli_wait_budget_is_refused_before_client_settings(tmp_path, timeout):
    options = GlobalOptions(
        config_path=tmp_path / "unused",
        json_output=False,
        verbose=0,
        quiet=False,
        token_file=None,
        wait_timeout=timeout,
    )
    with pytest.raises(ConfigurationError) as caught:
        cli_client.check_job_options(options, submitting=True)
    assert caught.value.problems[0].code == "HFARG002"


@pytest.mark.parametrize("flags", [{"detach": True}, {"idempotency_key": "key"}])
def test_only_submissions_accept_detach_or_key(tmp_path, flags):
    options = GlobalOptions(
        config_path=tmp_path / "unused",
        json_output=False,
        verbose=0,
        quiet=False,
        token_file=None,
        **flags,
    )
    with pytest.raises(ConfigurationError):
        cli_client.check_job_options(options, observing=True)
    cli_client.check_job_options(options, submitting=True)


def test_wait_budget_is_rejected_on_metadata_reads_but_allowed_on_existing_wait(tmp_path):
    options = GlobalOptions(
        config_path=tmp_path / "unused",
        json_output=False,
        verbose=0,
        quiet=False,
        token_file=None,
        wait_timeout=1,
    )
    with pytest.raises(ConfigurationError):
        cli_client.check_job_options(options)
    cli_client.check_job_options(options, observing=True)


def test_invalid_operation_never_becomes_a_retained_unvalidated_handle(settings):
    with (
        ApiClient(
            settings,
            transport=httpx.MockTransport(lambda _: pytest.fail("invalid ID sent a request")),
        ) as client,
        pytest.raises(ClientProtocolError) as caught,
    ):
        cli_client.observe_operation(client, TOKEN)
    assert getattr(caught.value, "operation_id", None) is None
    assert TOKEN not in str(caught.value)
