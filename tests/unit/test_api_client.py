"""Core transport ownership, bounded retries and exact observation (API-011)."""

import json

import httpx
import pytest

from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.client_errors import ClientConnectionError, ClientProtocolError
from hfcache.errors import ConfigurationError
from tests.unit.test_api_client_adversarial import (
    BASE,
    OPERATION,
    RUN,
    TOKEN,
    _accepted,
    _operation,
    _read,
    _response,
)


@pytest.fixture
def configured(tmp_path):
    token = tmp_path / "api-token"
    token.write_text(TOKEN)
    token.chmod(0o600)
    return ClientConfig(schema_version=1, api_url=BASE, api_token_file=token, read_retries=2)


def test_constructor_does_not_negotiate_and_context_closes_transport(configured):
    class Transport(httpx.BaseTransport):
        closed = False

        def handle_request(self, request):
            pytest.fail("constructor performed an implicit request")

        def close(self):
            self.closed = True

    transport = Transport()
    with ApiClient(configured, transport=transport):
        assert not transport.closed
    assert transport.closed


def test_get_retries_are_bounded_and_retain_explicit_authority(configured):
    sent, pauses = [], []

    def respond(request):
        sent.append(request)
        if len(sent) < 3:
            message = "synthetic stream loss"
            raise httpx.ReadError(message, request=request)
        return _response(_read(data={"ok": True}))

    with ApiClient(
        configured, transport=httpx.MockTransport(respond), sleep=pauses.append
    ) as client:
        assert client.read("/api/v1/status").envelope.data == {"ok": True}
    assert len(sent) == 3
    assert pauses == [configured.poll_interval] * 2
    assert all(request.headers["authorization"] == "Bearer " + TOKEN for request in sent)
    assert all(request.headers["accept-encoding"] == "identity" for request in sent)
    assert all(str(request.url) == BASE + "/api/v1/status" for request in sent)


def test_exhausted_read_retries_sanitize_transport_diagnostics(configured):
    sent = []

    def unavailable(request):
        sent.append(request)
        raise httpx.ConnectError(TOKEN + " private diagnostic", request=request)

    with (
        ApiClient(
            configured, transport=httpx.MockTransport(unavailable), sleep=lambda _: None
        ) as client,
        pytest.raises(ClientConnectionError) as caught,
    ):
        client.version()
    assert len(sent) == 3
    assert TOKEN not in str(caught.value)


def test_post_freezes_body_and_exposes_key_before_transmission(configured):
    body, keys, sent = {"selectors": []}, [], []

    def emit(key):
        keys.append(key)
        body["selectors"].append("model:changed/after-freeze")

    def respond(request):
        sent.append(request)
        assert keys == [request.headers["idempotency-key"]]
        assert json.loads(request.content) == {"selectors": []}
        accepted = _accepted()
        return _response(accepted, status=202, headers={"Location": accepted["links"]["status"]})

    with ApiClient(configured, transport=httpx.MockTransport(respond)) as client:
        first = client.submit("/api/v1/syncs", body, on_key=emit)
    assert first.key == keys[0]
    assert first.acceptance.operation.operation_id == OPERATION
    assert len(sent) == 1


def test_before_send_callback_failure_leaves_server_untouched(configured):
    sent = []

    def unexpected(request):
        sent.append(request)
        pytest.fail("callback refusal transmitted a request")

    def abort(_key):
        raise KeyboardInterrupt

    with (
        ApiClient(configured, transport=httpx.MockTransport(unexpected)) as client,
        pytest.raises(KeyboardInterrupt),
    ):
        client.submit("/api/v1/syncs", {}, on_key=abort)
    assert sent == []


def test_bad_request_body_is_refused_before_callback_or_transmission(configured):
    keys, sent = [], []

    def unexpected(request):
        sent.append(request)
        pytest.fail("invalid local body transmitted a request")

    with (
        ApiClient(configured, transport=httpx.MockTransport(unexpected)) as client,
        pytest.raises(ClientProtocolError),
    ):
        client.submit("/api/v1/syncs", {"bad": object()}, on_key=keys.append)
    assert keys == sent == []


def test_poll_observes_exact_operation_and_preserves_domain_identity(configured):
    paths, pauses = [], []
    states = iter(["queued", "running", "succeeded"])

    def respond(request):
        paths.append(request.url.path)
        payload = (
            _read(data={"done": True})
            if request.url.path.endswith("/result")
            else _read(data={"operation": _operation(state=next(states))})
        )
        return _response(payload)

    with ApiClient(
        configured, transport=httpx.MockTransport(respond), sleep=pauses.append
    ) as client:
        completed = client.poll(OPERATION)
    assert completed.envelope.run_id == RUN
    assert completed.envelope.run_id != OPERATION
    assert pauses == [configured.poll_interval] * 2
    assert paths == ["/management/api/v1/operations/" + OPERATION] * 3 + [
        "/management/api/v1/operations/" + OPERATION + "/result"
    ]


def test_standalone_result_binds_exact_receipt_before_envelope(configured):
    paths = []

    def respond(request):
        paths.append(request.url.path)
        data = (
            {"done": True}
            if request.url.path.endswith("/result")
            else {"operation": _operation(state="succeeded")}
        )
        return _response(_read(data=data))

    with ApiClient(configured, transport=httpx.MockTransport(respond)) as client:
        assert client.result(OPERATION).envelope.data == {"done": True}
    assert [path.rsplit("/", 1)[-1] for path in paths] == [OPERATION, "result"]


def test_poll_timeout_stops_observation_without_cancel_or_replay(configured):
    clock, methods = [0.0], []

    def sleep(seconds):
        clock[0] += seconds

    def respond(request):
        methods.append(request.method)
        return _response(_read(data={"operation": _operation()}))

    with (
        ApiClient(
            configured,
            transport=httpx.MockTransport(respond),
            sleep=sleep,
            monotonic=lambda: clock[0],
        ) as client,
        pytest.raises(ClientConnectionError),
    ):
        client.poll(OPERATION, timeout=0.5)
    assert methods == ["GET"] * 3
    assert clock[0] == 0.5


def test_cookie_response_never_becomes_an_ambient_credential(configured):
    sent = []

    def respond(request):
        sent.append(request)
        return _response(_read(), headers={"Set-Cookie": "session=untrusted"})

    with ApiClient(configured, transport=httpx.MockTransport(respond)) as client:
        client.version()
        client.version()
    assert all("cookie" not in request.headers for request in sent)


def test_closed_client_classifies_observation_as_unavailable(configured):
    client = ApiClient(configured, transport=httpx.MockTransport(lambda _: _response(_read())))
    client.close()
    with pytest.raises(ClientConnectionError):
        client.version()


def test_poll_returns_exact_failed_domain_envelope_instead_of_transport_success(configured):
    methods = []

    def respond(request):
        methods.append(request.method)
        if not request.url.path.endswith("/result"):
            return _response(_read(data={"operation": _operation(state="failed")}))
        payload = _read(data={"partial_findings": 2})
        payload["envelope"].update(
            exit_code=40,
            outcome="failed",
            errors=[
                {
                    "code": "HFVER001",
                    "message": "integrity finding",
                    "context": {},
                    "repository": None,
                }
            ],
        )
        return _response(payload)

    with ApiClient(configured, transport=httpx.MockTransport(respond)) as client:
        outcome = client.poll(OPERATION)
    assert outcome.envelope.exit_code == 40
    assert outcome.envelope.data == {"partial_findings": 2}
    assert outcome.envelope.run_id == RUN
    assert methods == ["GET", "GET"]


def test_invalid_local_ca_configuration_is_sanitized_without_fallback(configured, monkeypatch):
    def invalid_ca(**_options):
        raise OSError(TOKEN)

    monkeypatch.setattr("hfcache.client.create_http_client", invalid_ca)
    with pytest.raises(ConfigurationError) as caught:
        ApiClient(configured)
    assert caught.value.problems[0].code == "HFAPI017"
    assert TOKEN not in str(caught.value)


def test_resolved_bearer_in_configured_url_prefix_is_never_transmitted(configured):
    poisoned = configured.model_copy(update={"api_url": BASE + "/" + TOKEN})
    with pytest.raises(ConfigurationError) as caught:
        ApiClient(
            poisoned, transport=httpx.MockTransport(lambda _: pytest.fail("credential URL sent"))
        )
    assert caught.value.problems[0].code == "HFAPI017"
    assert TOKEN not in str(caught.value)
