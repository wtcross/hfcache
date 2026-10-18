"""Untrusted replies never redirect authority or replay submissions (INV-002/014)."""

import copy
import json
import time

import httpx
import pytest

from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.client_errors import (
    ClientConnectionError,
    ClientProtocolError,
    RemoteApiError,
    UncertainSubmission,
)
from tests.fixtures import examples

TOKEN = "reader_9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVU"
REQUEST = "a" * 32
RUN = "b" * 32
OPERATION = "c" * 32
FINGERPRINT = "d" * 64
TIME = "2026-10-17T12:00:00.000000Z"
BASE = "https://archive.example/management"
STATUS = "/api/v1/status"
SUBMIT = "/api/v1/syncs"


def _envelope(*, data=None, run_id=RUN):
    return {
        "schema_version": 1,
        "command": "status",
        "started_at": TIME,
        "completed_at": TIME,
        "run_id": run_id,
        "exit_code": 0,
        "outcome": "success",
        "warnings": [],
        "errors": [],
        "data": data if data is not None else {"repositories": []},
    }


def _read(*, data=None, cursor=None, request_id=REQUEST, run_id=RUN):
    return {
        "schema_version": 1,
        "request_id": request_id,
        "archive_id": examples.ARCHIVE_ID,
        "config_fingerprint": FINGERPRINT,
        "envelope": _envelope(data=data, run_id=run_id),
        "next_cursor": cursor,
    }


def _operation(*, state="queued", identifier=OPERATION):
    terminal = state in {"succeeded", "failed"}
    return {
        "schema_version": 1,
        "operation_id": identifier,
        "principal": "rest-writer",
        "route": SUBMIT,
        "archive_id": examples.ARCHIVE_ID,
        "config_fingerprint": FINGERPRINT,
        "state": state,
        "created_at": TIME,
        "updated_at": TIME,
        "completed_at": TIME if terminal or state == "interrupted" else None,
        "domain_run_id": RUN if terminal or state == "running" else None,
        "transaction_ids": [],
        "next_event_sequence": 1,
        "result_recorded": terminal,
    }


def _accepted():
    location = f"/management/api/v1/operations/{OPERATION}"
    return {
        "schema_version": 1,
        "request_id": REQUEST,
        "archive_id": examples.ARCHIVE_ID,
        "config_fingerprint": FINGERPRINT,
        "operation": _operation(),
        "created": True,
        "links": {
            "status": location,
            "result": location + "/result",
            "events": location + "/events",
        },
    }


def _response(payload, *, status=200, headers=None):
    fields = {"x-request-id": payload.get("request_id", REQUEST)} | (headers or {})
    return httpx.Response(status, json=payload, headers=fields)


def _event_responder(payload):
    def respond(request):
        if request.url.path.endswith("/events"):
            return _response(payload)
        shown = _read(data={"operation": _operation(state="running")})
        shown["envelope"]["command"] = "operations show"
        return _response(shown)

    return respond


@pytest.fixture
def client_factory(tmp_path):
    token = tmp_path / "api-token"
    token.write_text(TOKEN, encoding="ascii")
    token.chmod(0o600)

    def create(handler, *, clock=time.monotonic, **options):
        config = ClientConfig(
            schema_version=1,
            api_url=BASE,
            api_token_file=token,
            read_retries=0,
            **options,
        )
        return ApiClient(
            config, transport=httpx.MockTransport(handler), sleep=lambda _: None, monotonic=clock
        )

    return create


@pytest.mark.parametrize("version", [None, True, False, 1.0, "1", 0, 2])
@pytest.mark.parametrize("scope", ["wrapper", "envelope"])
def test_read_requires_explicit_integer_versions_at_every_layer(client_factory, scope, version):
    payload = _read()
    target = payload if scope == "wrapper" else payload["envelope"]
    if version is None:
        del target["schema_version"]
    else:
        target["schema_version"] = version

    with client_factory(lambda _: _response(payload)) as client, pytest.raises(ClientProtocolError):
        client.read(STATUS)


@pytest.mark.parametrize("version", [None, True, 1.0, "1", 2])
@pytest.mark.parametrize("scope", ["wrapper", "operation"])
def test_acceptance_requires_explicit_integer_versions(client_factory, scope, version):
    payload = _accepted()
    target = payload if scope == "wrapper" else payload["operation"]
    if version is None:
        del target["schema_version"]
    else:
        target["schema_version"] = version
    location = payload["links"]["status"]

    with (
        client_factory(
            lambda _: _response(payload, status=202, headers={"location": location})
        ) as client,
        pytest.raises(UncertainSubmission),
    ):
        client.submit(SUBMIT, {}, key="known-submission")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("outcome", "failed"),
        ("exit_code", 99),
        ("exit_code", True),
        ("run_id", "../outside"),
        ("errors", [{"code": "HFHUB004", "message": "failure", "context": {}, "repository": None}]),
        (
            "warnings",
            [{"code": "HFWRN001", "message": "warning", "context": {}, "repository": None}],
        ),
    ],
)
def test_nested_envelope_cannot_claim_contradictory_success(client_factory, field, value):
    payload = _read()
    payload["envelope"][field] = value

    with client_factory(lambda _: _response(payload)) as client, pytest.raises(ClientProtocolError):
        client.read(STATUS)


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"{",
        b"null",
        b"[]",
        b'{"schema_version":1,"schema_version":1}',
        b'{"value":NaN}',
        b'{"value":1e999}',
        b'{"value":"\xff"}',
        b'{"value":"\\ud800"}',
        b'{"value":' + b"[" * 40 + b"0" + b"]" * 40 + b"}",
    ],
)
def test_malformed_json_is_classified_without_echoing_response_content(client_factory, body):
    with (
        client_factory(
            lambda _: httpx.Response(
                200, content=body, headers={"content-type": "application/json"}
            )
        ) as client,
        pytest.raises(ClientProtocolError) as caught,
    ):
        client.read(STATUS)

    assert TOKEN not in str(caught.value)
    assert BASE not in str(caught.value)


class _Chunks(httpx.SyncByteStream):
    def __init__(self, chunks, error=None):
        self.chunks = chunks
        self.error = error
        self.closed = False

    def __iter__(self):
        yield from self.chunks
        if self.error is not None:
            raise self.error

    def close(self):
        self.closed = True


def test_actual_streamed_bytes_bound_and_close_even_with_lying_length(client_factory):
    stream = _Chunks([b"x" * 700] * 4)

    def reply(_):
        return httpx.Response(
            200,
            stream=stream,
            headers={"content-type": "application/json", "content-length": "1"},
        )

    with (
        client_factory(reply, max_response_bytes=1024) as client,
        pytest.raises(ClientProtocolError),
    ):
        client.read(STATUS)
    assert stream.closed


@pytest.mark.parametrize("encoding", ["gzip", "br", "deflate"])
def test_encoded_reply_cannot_bypass_decoded_response_bounds(client_factory, encoding):
    def respond(_):
        return httpx.Response(
            200,
            stream=_Chunks([json.dumps(_read()).encode()]),
            headers={"content-type": "application/json", "content-encoding": encoding},
        )

    with (
        client_factory(respond) as client,
        pytest.raises(ClientProtocolError),
    ):
        client.read(STATUS)


@pytest.mark.parametrize(
    "fault",
    ["duplicate-root", "duplicate-data", "nan", "infinity", "overflow", "surrogate", "depth"],
)
def test_otherwise_valid_wrapper_rejects_hostile_json_syntax(client_factory, fault):
    payload = json.dumps(_read(data={"value": 0}), separators=(",", ":")).encode()
    if fault == "duplicate-root":
        body = payload.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1', 1)
    elif fault == "duplicate-data":
        body = payload.replace(b'"value":0', b'"value":0,"value":0')
    else:
        replacement = {
            "nan": b"NaN",
            "infinity": b"Infinity",
            "overflow": b"1e999",
            "surrogate": b'"\\ud800"',
            "depth": b"[" * 40 + b"0" + b"]" * 40,
        }[fault]
        body = payload.replace(b'"value":0', b'"value":' + replacement)

    with (
        client_factory(
            lambda _: httpx.Response(
                200, content=body, headers={"content-type": "application/json"}
            )
        ) as client,
        pytest.raises(ClientProtocolError),
    ):
        client.read(STATUS)


def test_stream_failure_never_returns_partial_success_and_closes_response(client_factory):
    message = f"upstream failed with {TOKEN} at {BASE}"
    stream = _Chunks([b'{"schema_version":1,'], error=httpx.ReadError(message))

    with (
        client_factory(
            lambda _: httpx.Response(
                200, stream=stream, headers={"content-type": "application/json"}
            )
        ) as client,
        pytest.raises(ClientConnectionError) as caught,
    ):
        client.read(STATUS)

    assert stream.closed
    assert TOKEN not in str(caught.value)
    assert BASE not in str(caught.value)


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirect_is_never_followed_with_api_bearer(client_factory, status):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(status, headers={"location": "https://attacker.invalid/collect"})

    with client_factory(respond) as client, pytest.raises(ClientProtocolError):
        client.read(STATUS)

    assert len(requests) == 1
    assert requests[0].url.host == "archive.example"


@pytest.mark.parametrize(
    "target",
    [
        "https://attacker.invalid/api/v1/operations/" + OPERATION,
        "//attacker.invalid/collect",
        "/api/v1/operations/" + OPERATION,
        "/management/../api/v1/operations/" + OPERATION,
        "/management/%2e%2e/api/v1/operations/" + OPERATION,
        "/management/api/v1/operations/" + "e" * 32,
        f"/management/api/v1/operations/{OPERATION}?token=do-not-send",
        f"/management/api/v1/operations/{OPERATION}#fragment",
    ],
)
def test_acceptance_links_cannot_change_origin_prefix_or_operation(client_factory, target):
    payload = _accepted()
    payload["links"]["status"] = target
    calls = []

    def respond(request):
        calls.append(request)
        return _response(payload, status=202, headers={"location": target})

    with (
        client_factory(respond) as client,
        pytest.raises(UncertainSubmission),
    ):
        client.submit(SUBMIT, {}, key="bound-to-original-request")
    assert len(calls) == 1
    assert calls[0].url.path == "/management/api/v1/syncs"


def test_pagination_allows_new_request_and_run_ids_but_preserves_archive_policy(client_factory):
    pages = [
        _read(data={"repositories": [{"name": "first"}]}, cursor="next"),
        _read(data={"repositories": [{"name": "second"}]}, request_id="e" * 32, run_id="f" * 32),
    ]
    requests = []

    def respond(request):
        requests.append(request)
        return _response(pages[len(requests) - 1])

    with client_factory(respond) as client:
        parsed = list(client.iter_pages(STATUS, "repositories"))
    assert [page.envelope.data["repositories"][0]["name"] for page in parsed] == ["first", "second"]
    assert parsed[0].envelope.run_id == RUN
    assert parsed[1].envelope.run_id == "f" * 32
    assert requests[1].url.params["cursor"] == "next"


@pytest.mark.parametrize("changed", ["archive", "fingerprint", "command", "cycle"])
def test_page_identity_change_or_cursor_cycle_never_silently_truncates(client_factory, changed):
    first = _read(data={"repositories": [{"name": "first"}]}, cursor="again")
    second = _read(data={"repositories": [{"name": "second"}]})
    if changed == "archive":
        second["archive_id"] = "00000000-0000-4000-8000-000000000001"
    elif changed == "fingerprint":
        second["config_fingerprint"] = "f" * 64
    elif changed == "command":
        second["envelope"]["command"] = "version"
    else:
        second["next_cursor"] = "again"
    replies = iter([first, second])

    with (
        client_factory(lambda _: _response(next(replies))) as client,
        pytest.raises(ClientProtocolError),
    ):
        list(client.iter_pages(STATUS, "repositories"))


def test_lost_post_retains_original_key_and_route_without_transparent_replay(client_factory):
    requests = []
    emitted = []

    def lost_reply(request):
        requests.append(request)
        assert emitted == ["known-before-transmission"]
        message = f"sensitive upstream failure {TOKEN} {BASE}"
        raise httpx.ReadError(message, request=request)

    with client_factory(lost_reply) as client, pytest.raises(UncertainSubmission) as caught:
        client.submit(SUBMIT, {}, key="known-before-transmission", on_key=emitted.append)

    assert len(requests) == 1
    assert caught.value.key == "known-before-transmission"
    assert caught.value.route == SUBMIT
    assert requests[0].headers["idempotency-key"] == caught.value.key
    assert TOKEN not in str(caught.value)
    assert BASE not in str(caught.value)
    assert TOKEN not in repr(caught.value)


def test_generated_submission_key_is_published_before_lost_transmission(client_factory):
    emitted = []
    requests = []

    def lost_reply(request):
        requests.append(request)
        assert len(emitted) == 1
        assert request.headers["idempotency-key"] == emitted[0]
        message = "synthetic lost submission"
        raise httpx.WriteError(message, request=request)

    with client_factory(lost_reply) as client, pytest.raises(UncertainSubmission) as caught:
        client.submit(SUBMIT, {}, on_key=emitted.append)

    assert caught.value.key == emitted[0]
    assert len(requests) == 1


def test_expected_archive_rejects_other_valid_writer_identity(client_factory):
    payload = _read()
    payload["archive_id"] = "00000000-0000-4000-8000-000000000001"

    with (
        client_factory(
            lambda _: _response(payload), expected_archive_id=examples.ARCHIVE_ID
        ) as client,
        pytest.raises(ClientProtocolError),
    ):
        client.read(STATUS)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("request_id", "caller-selected"),
        ("archive_id", "not-an-archive"),
        ("config_fingerprint", "wrong-fingerprint"),
        ("server_debug", "untrusted-server-content"),
    ],
)
def test_malformed_wrapper_identity_or_unknown_field_is_protocol_failure(
    client_factory, field, value
):
    payload = copy.deepcopy(_read())
    payload[field] = value

    with client_factory(lambda _: _response(payload)) as client, pytest.raises(ClientProtocolError):
        client.read(STATUS)


@pytest.mark.parametrize(
    "headers",
    [
        {"content-type": "text/html"},
        {"content-type": "application/json; charset=latin-1"},
        {"content-type": "application/problem+json"},
        {"content-type": "application/json, application/json"},
    ],
)
def test_response_media_type_is_not_guessed_from_body(client_factory, headers):
    with (
        client_factory(lambda _: _response(_read(), headers=headers)) as client,
        pytest.raises(ClientProtocolError),
    ):
        client.read(STATUS)


def test_missing_lookup_history_is_unknown_execution_and_never_submits(client_factory):
    requests = []

    def respond(request):
        requests.append(request)
        return _response(
            {
                "request_id": REQUEST,
                "code": "HFAPI013",
                "message": f"untrusted error body {TOKEN} {BASE}",
                "exit_code": 20,
            },
            status=404,
        )

    with client_factory(respond) as client, pytest.raises(RemoteApiError) as caught:
        client.lookup("lost-mutation-key")

    assert caught.value.code == "HFAPI013"
    assert caught.value.exit_code == 20
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/management/api/v1/operations/lookup"
    assert requests[0].headers["idempotency-key"] == "lost-mutation-key"
    assert not requests[0].url.query
    assert TOKEN not in str(caught.value)
    assert BASE not in str(caught.value)
    assert "untrusted error body" not in str(caught.value)


def test_interrupted_poll_never_fetches_result_or_replays_command(client_factory):
    requests = []
    payload = _read(data={"operation": _operation(state="interrupted")})
    payload["envelope"]["command"] = "operations show"

    def respond(request):
        requests.append(request)
        return _response(payload)

    with client_factory(respond) as client, pytest.raises(RemoteApiError) as caught:
        client.poll(OPERATION)

    assert caught.value.code == "HFAPI015"
    assert caught.value.exit_code == 20
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == f"/management/api/v1/operations/{OPERATION}"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("completed_at", None),
        ("domain_run_id", None),
        ("result_recorded", False),
        ("route", "https://attacker.invalid/run"),
        ("updated_at", "not-a-timestamp"),
    ],
)
def test_terminal_operation_requires_coherent_public_evidence(client_factory, field, value):
    receipt = _operation(state="succeeded")
    receipt[field] = value
    payload = _read(data={"operation": receipt})
    payload["envelope"]["command"] = "operations show"

    with client_factory(lambda _: _response(payload)) as client, pytest.raises(ClientProtocolError):
        client.operation(OPERATION)


@pytest.mark.parametrize("version", [None, True, "1", 2])
def test_event_items_require_their_independent_schema_version(client_factory, version):
    event = {"sequence": 1, "at": TIME, "kind": "operation.queued", "message": "queued"}
    if version is not None:
        event["schema_version"] = version
    payload = _read(
        data={
            "operation_id": OPERATION,
            "events": [event],
            "next_cursor": 1,
            "oldest_sequence": 1,
            "truncated": False,
        }
    )
    payload["envelope"]["command"] = "operations events"

    with client_factory(_event_responder(payload)) as client, pytest.raises(ClientProtocolError):
        client.events(OPERATION)


def test_valid_event_page_matches_actual_server_projection(client_factory):
    payload = _read(
        data={
            "operation_id": OPERATION,
            "events": [
                {
                    "schema_version": 1,
                    "sequence": 1,
                    "at": TIME,
                    "kind": "operation.queued",
                    "message": "queued",
                }
            ],
            "next_cursor": 1,
            "oldest_sequence": 1,
            "truncated": False,
        }
    )
    payload["envelope"]["command"] = "operations events"

    with client_factory(_event_responder(payload)) as client:
        page = client.events(OPERATION)

    assert page.operation_id == OPERATION
    assert page.events[0].sequence == 1


def test_error_json_and_request_reprs_never_echo_registered_api_token(client_factory):
    content = json.dumps({"unexpected": TOKEN, "url": BASE}).encode()

    with (
        client_factory(
            lambda _: httpx.Response(
                503, content=content, headers={"content-type": "application/json"}
            )
        ) as client,
        pytest.raises(ClientProtocolError) as caught,
    ):
        client.read(STATUS)

    assert TOKEN not in str(caught.value)
    assert TOKEN not in repr(caught.value)
    assert BASE not in str(caught.value)


def test_inventory_uses_actual_repeated_selector_and_type_wire_parameters(client_factory):
    requests = []

    def respond(request):
        requests.append(request)
        return _response(_read())

    selected = ["model:org/first", "model:org/second"]
    with client_factory(respond) as client:
        client.read(STATUS, {"selector": selected, "type": "model"})

    assert len(requests) == 1
    assert requests[0].url.params.get_list("selector") == selected
    assert requests[0].url.params["type"] == "model"
    assert "selectors" not in requests[0].url.params
    assert "repository_type" not in requests[0].url.params


def test_server_cursor_cannot_put_resolved_bearer_in_followup_url(client_factory):
    requests = []

    def respond(request):
        requests.append(request)
        return _response(_read(data={"repositories": []}, cursor=TOKEN))

    with client_factory(respond) as client, pytest.raises(ClientProtocolError):
        list(client.iter_pages(STATUS, "repositories"))

    assert len(requests) == 1
    assert TOKEN not in str(requests[0].url)


def test_generated_key_survives_valid_remote_failure_after_transmission(client_factory):
    requests = []

    def respond(request):
        requests.append(request)
        return _response(
            {
                "request_id": REQUEST,
                "code": "HFAPI008",
                "message": "Internal server error",
                "exit_code": 20,
            },
            status=500,
        )

    with client_factory(respond) as client, pytest.raises(RemoteApiError) as caught:
        client.submit(SUBMIT, {})

    assert caught.value.code == "HFAPI008"
    assert caught.value.exit_code == 20
    assert caught.value.route == SUBMIT
    assert caught.value.key == requests[0].headers["idempotency-key"]
    assert len(requests) == 1
    assert requests[0].method == "POST"


@pytest.mark.parametrize("fault", ["internal-gap", "hidden-retention", "wrong-oldest"])
def test_event_pages_expose_retention_gaps_and_never_invent_continuity(client_factory, fault):
    sequences, oldest, truncated = [1, 3], 1, False
    if fault == "hidden-retention":
        sequences, oldest, truncated = [5, 6], 5, False
    elif fault == "wrong-oldest":
        sequences, oldest, truncated = [5, 6], 6, True
    payload = _read(
        data={
            "operation_id": OPERATION,
            "events": [
                {
                    "schema_version": 1,
                    "sequence": number,
                    "at": TIME,
                    "kind": "operation.queued",
                    "message": "queued",
                }
                for number in sequences
            ],
            "next_cursor": sequences[-1],
            "oldest_sequence": oldest,
            "truncated": truncated,
        }
    )
    payload["envelope"]["command"] = "operations events"

    with client_factory(_event_responder(payload)) as client, pytest.raises(ClientProtocolError):
        client.events(OPERATION)


def test_valid_retained_event_gap_remains_explicit_for_the_caller(client_factory):
    payload = _read(
        data={
            "operation_id": OPERATION,
            "events": [
                {
                    "schema_version": 1,
                    "sequence": number,
                    "at": TIME,
                    "kind": "operation.queued",
                    "message": "queued",
                }
                for number in (5, 6)
            ],
            "next_cursor": 6,
            "oldest_sequence": 5,
            "truncated": True,
        }
    )
    payload["envelope"]["command"] = "operations events"

    with client_factory(_event_responder(payload)) as client:
        page = client.events(OPERATION)

    assert page.truncated is True
    assert page.oldest_sequence == 5
    assert [event.sequence for event in page.events] == [5, 6]


def test_known_operation_fingerprint_cannot_change_on_event_reads(client_factory):
    shown = _read(data={"operation": _operation(state="running")})
    shown["envelope"]["command"] = "operations show"
    events = _read(
        data={
            "operation_id": OPERATION,
            "events": [],
            "next_cursor": 0,
            "oldest_sequence": 1,
            "truncated": False,
        }
    )
    events["envelope"]["command"] = "operations events"
    events["config_fingerprint"] = "f" * 64
    replies = iter([shown, events])

    with client_factory(lambda _: _response(next(replies))) as client:
        client.operation(OPERATION)
        with pytest.raises(ClientProtocolError):
            client.events(OPERATION)


def test_trickling_chunks_cannot_extend_the_absolute_observation_deadline(client_factory):
    clock = [0.0]
    consumed = []

    class Trickle(httpx.SyncByteStream):
        def __iter__(self):
            for number in range(100):
                consumed.append(number)
                clock[0] += 0.25
                assert len(consumed) <= 5, "client buffered past the absolute poll deadline"
                yield b" "

    stream = Trickle()
    with (
        client_factory(
            lambda _: httpx.Response(
                200, stream=stream, headers={"content-type": "application/json"}
            ),
            clock=lambda: clock[0],
        ) as client,
        pytest.raises(ClientConnectionError),
    ):
        client.poll(OPERATION, timeout=1)

    assert len(consumed) <= 4


def _capabilities():
    result = _read(
        data={
            "api_version": 1,
            "credential_class": "rest-reader",
            "capabilities": ["read"],
            "instance_id": "e" * 32,
            "reads": True,
            "operations": True,
            "operation_history": True,
            "mcp": False,
            "maintenance_enabled": False,
            "max_page_size": 1000,
        }
    )
    result["envelope"]["command"] = "capabilities"
    return result


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("api_version", None),
        ("api_version", True),
        ("api_version", "1"),
        ("api_version", 2),
        ("reads", "true"),
        ("capabilities", ["read", "write"]),
        ("credential_class", "mcp-reader"),
        ("generic_exec", True),
    ],
)
def test_capabilities_never_coerce_or_guess_unknown_authority(client_factory, field, value):
    payload = _capabilities()
    payload["envelope"]["data"][field] = value

    with client_factory(lambda _: _response(payload)) as client, pytest.raises(ClientProtocolError):
        client.require_capabilities("reads")


def test_failed_capability_envelope_cannot_authorize_from_partial_data(client_factory):
    payload = _capabilities()
    payload["envelope"] |= {
        "exit_code": 20,
        "outcome": "failed",
        "errors": [
            {"code": "HFMNT002", "message": "fixture failure", "context": {}, "repository": None}
        ],
    }

    with client_factory(lambda _: _response(payload)) as client, pytest.raises(ClientProtocolError):
        client.require_capabilities("operations")


def test_unknown_required_capability_refuses_without_submitting(client_factory):
    requests = []

    def respond(request):
        requests.append(request)
        return _response(_capabilities())

    with client_factory(respond) as client, pytest.raises(ClientProtocolError):
        client.require_capabilities("generic_exec")

    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/management/api/v1/capabilities"
