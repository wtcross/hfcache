"""Command admission rejects hostile HTTP before execution (INV-013/014)."""

import asyncio
import json
from threading import Event

import httpx
import pytest

from hfcache import locking
from hfcache.api.app import create_app
from hfcache.errors import OperationError, SafetyError
from hfcache.logging import reset
from hfcache.paths import RepositoryLayout
from hfcache.publication import read_reference
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.commands import CommandServices
from hfcache.services.context import ExecutionContext, ServiceResult
from tests.fixtures import examples
from tests.unit.test_api_commands import (
    configured as command_archive,  # noqa: F401 - shared fixture
)
from tests.unit.test_synchronize import MODEL, SHA_A

WRITER = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
READER = "reader_9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVU"
MCP = "mcp_reader_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabc"
OPAQUE = "untrusted-sensitive-request-value"
WRITE_ROUTES = ("/api/v1/syncs", "/api/v1/verifications")
POST_ROUTES = (*WRITE_ROUTES, "/api/v1/plans", "/api/v1/diagnostics", "/api/v1/config/validate")


class _Verifier:
    def __init__(self):
        self.available = True
        self.probes = 0
        self.calls = []
        self.entered = Event()
        self.release = Event()
        self.release.set()

    def check_available(self):
        self.probes += 1
        if not self.available:
            raise OperationError(code="HFAPI016")

    def reconcile(self, receipt):
        return None

    def execute(self, operation_id, request, expected_fingerprint, remaining_wait_seconds):
        self.calls.append((operation_id, request, expected_fingerprint))
        self.entered.set()
        assert self.release.wait(10)
        context = ExecutionContext.create(operation_id=operation_id)
        return ServiceResult(request.command, {"delegated": True}).envelope(context)


@pytest.fixture
def verifier():
    return _Verifier()


@pytest.fixture(autouse=True)
def isolate_logging():
    reset()
    yield
    reset()


@pytest.fixture
def configured(tmp_path, verifier):
    archive = tmp_path / "archive"
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{archive}"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n[hub]\ntoken_mode="disabled"\n'
    )
    credentials = {}
    for name, value in (("writer", WRITER), ("reader", READER), ("mcp_reader", MCP)):
        path = tmp_path / name
        path.write_text(value, encoding="ascii")
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(policy),
            "state_directory": str(tmp_path / "state"),
            "credentials": credentials,
            "listener": {"allowed_hosts": ["testserver"]},
            "limits": {"max_request_bytes": 1024},
        }
    )
    app = create_app(
        server,
        instance_lock_path=tmp_path / "daemon.lock",
        verification_executor=verifier,
    )
    return app, policy, archive


async def _raw(  # noqa: PLR0913 - independent hostile HTTP transport dimensions
    app,
    route,
    *,
    token=WRITER,
    body=b"{}",
    headers=(),
    chunks=None,
    content_type=b"application/json",
):
    messages = []
    received = 0
    pieces = iter(chunks if chunks is not None else [body])
    buffered = list(pieces)

    async def receive():
        nonlocal received
        received += 1
        if received <= len(buffered):
            return {
                "type": "http.request",
                "body": buffered[received - 1],
                "more_body": received < len(buffered),
            }
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    fields = [(b"host", b"testserver")]
    if content_type is not None:
        fields.append((b"content-type", content_type))
    if token is not None:
        fields.append((b"authorization", f"Bearer {token}".encode("ascii")))
    fields.extend(headers)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": route,
        "raw_path": route.encode("ascii"),
        "root_path": "",
        "query_string": b"",
        "headers": fields,
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }
    async with app.router.lifespan_context(app):
        await app(scope, receive, send)
    started = next(message for message in messages if message["type"] == "http.response.start")
    payload = b"".join(
        message.get("body", b"") for message in messages if message["type"] == "http.response.body"
    )
    return started["status"], json.loads(payload), received


@pytest.mark.parametrize("route", POST_ROUTES)
@pytest.mark.parametrize("token", [None, MCP, "unknown_" + "a" * 40])
def test_post_authentication_precedes_body_receive(configured, route, token):
    app, _, archive = configured

    status, payload, received = asyncio.run(
        _raw(app, route, token=token, body=OPAQUE.encode() * 200)
    )

    assert status == 401
    assert payload["code"] == "HFAPI001"
    assert received == 0
    assert OPAQUE not in json.dumps(payload)
    assert not archive.exists()
    assert app.state.operations.root.is_dir()


@pytest.mark.parametrize("route", WRITE_ROUTES)
def test_known_writer_only_route_refuses_reader_before_body_receive(configured, route):
    app, _, archive = configured

    status, payload, received = asyncio.run(
        _raw(app, route, token=READER, body=OPAQUE.encode() * 200)
    )

    assert status == 403
    assert payload["code"] == "HFAPI002"
    assert received == 0
    assert not archive.exists()


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"null",
        b"[]",
        b"true",
        b"1",
        b'"' + OPAQUE.encode() + b'"',
        b'{"selectors":[],"selectors":[]}',
        b'{"nested":{"x":1,"x":2}}',
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":-Infinity}',
        b'{"value":1e999}',
        b'{"value":"\\ud800"}',
        b'{"value":' + b"[" * 33 + b"0" + b"]" * 33 + b"}",
        b'{"value":"\xff"}',
        b'{"value":"\x00"}',
        b"{" + OPAQUE.encode(),
    ],
)
def test_post_requires_nonempty_strict_json_object_without_echo(configured, body):
    app, _, archive = configured

    status, payload, _ = asyncio.run(_raw(app, "/api/v1/syncs", body=body))

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert OPAQUE not in json.dumps(payload)
    assert not archive.exists()


def test_chunked_post_bound_counts_actual_received_bytes(configured):
    app, _, archive = configured

    status, payload, received = asyncio.run(
        _raw(
            app,
            "/api/v1/syncs",
            chunks=[b'{"selectors":["', OPAQUE.encode() * 40, b'"]}'],
        )
    )

    assert status == 413
    assert payload["code"] == "HFAPI006"
    assert received == 2
    assert OPAQUE not in json.dumps(payload)
    assert not archive.exists()


@pytest.mark.parametrize(
    "content_type",
    [
        None,
        b"text/plain",
        b"application/octet-stream",
        b"application/problem+json",
        b"application/json; charset=latin-1",
        b"application/json; charset=utf-8; charset=utf-8",
        b"application/json; boundary=unexpected",
    ],
)
def test_post_refuses_missing_or_unsupported_content_type(configured, content_type):
    app, _, archive = configured

    status, payload, received = asyncio.run(_raw(app, "/api/v1/syncs", content_type=content_type))

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert received == 0
    assert not archive.exists()


@pytest.mark.parametrize(
    "headers",
    [
        [(b"content-type", b"application/json")],
        [(b"content-encoding", b"gzip")],
        [(b"content-encoding", b"identity")],
    ],
)
def test_duplicate_media_or_encoded_post_is_refused_before_receive(configured, headers):
    app, _, archive = configured

    status, payload, received = asyncio.run(_raw(app, "/api/v1/syncs", headers=headers))

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert received == 0
    assert not archive.exists()


@pytest.mark.parametrize("route", ["/api/v1/plans", "/api/v1/config/validate"])
def test_candidate_presence_requires_writer_before_dto_validation(configured, route):
    app, _, archive = configured

    status, payload, _ = asyncio.run(_raw(app, route, token=READER, body=b'{"candidate":null}'))

    assert status == 403
    assert payload["code"] == "HFAPI002"
    assert not archive.exists()


@pytest.mark.parametrize("route", ["/api/v1/plans", "/api/v1/config/validate"])
def test_explicit_null_candidate_is_refused_without_echo_or_admission(configured, route):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(
            app,
            route,
            body=json.dumps({"candidate": None}).encode(),
            headers=[(b"idempotency-key", b"candidate-reserved")],
        )
    )

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert OPAQUE not in json.dumps(payload)
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize("read_only", [None, False, 0, 1, "true", [], {}])
def test_only_literal_true_diagnostics_is_reader_authorized(configured, read_only):
    app, _, archive = configured
    body = {} if read_only is None else {"read_only": read_only}

    status, payload, _ = asyncio.run(
        _raw(app, "/api/v1/diagnostics", token=READER, body=json.dumps(body).encode())
    )

    assert status == 403
    assert payload["code"] == "HFAPI002"
    assert not archive.exists()


@pytest.mark.parametrize("route", POST_ROUTES)
@pytest.mark.parametrize("field", ["config_path", "archive_root", "token_file", "hub_endpoint"])
def test_no_command_accepts_request_selected_server_path_or_credential(configured, route, field):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(
            app,
            route,
            body=json.dumps({field: OPAQUE}).encode(),
            headers=[(b"idempotency-key", b"invalid-path")],
        )
    )

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert OPAQUE not in json.dumps(payload)
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({}, "HFAPI006"),
        ({"mode": "estimate"}, "HFAPI006"),
        ({"mode": "full", "revision": "model:org/repo@" + "a" * 40}, "HFAPI006"),
        ({"mode": "full", "run_id": "a" * 32}, "HFAPI006"),
        ({"mode": "new", "run_id": "../" + OPAQUE}, "HFAPI006"),
        ({"mode": "new", "run_id": "A" * 32}, "HFAPI006"),
        ({"mode": "revision"}, "HFAPI006"),
        ({"mode": "revision", "revision": "model:org/repo"}, "HFAPI006"),
        ({"mode": "revision", "revision": "model:org/repo@main"}, "HFARG001"),
        ({"mode": "revision", "revision": "model:org/repo@" + "A" * 40}, "HFARG001"),
        ({"mode": True}, "HFAPI006"),
        ({"mode": ["new", "full"]}, "HFAPI006"),
        ({"mode": "new", "estimate": True}, "HFAPI006"),
    ],
)
def test_verification_invalid_modes_and_selectors_never_admit(configured, body, code):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(
            app,
            "/api/v1/verifications",
            body=json.dumps(body).encode(),
            headers=[(b"idempotency-key", b"invalid-mode")],
        )
    )

    assert status == 422
    assert payload["code"] == code
    assert OPAQUE not in json.dumps(payload)
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize("route", ["/api/v1/syncs", "/api/v1/plans"])
@pytest.mark.parametrize(
    ("selectors", "code"),
    [
        (None, "HFAPI006"),
        ("model:org/repo", "HFAPI006"),
        ([1], "HFAPI006"),
        (["../bad"], "HFARG001"),
        (["model:org/repo@main"], "HFARG001"),
    ],
)
def test_selection_requires_array_of_domain_selectors(configured, route, selectors, code):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(
            app,
            route,
            body=json.dumps({"selectors": selectors}).encode(),
            headers=[(b"idempotency-key", b"invalid-selection")],
        )
    )

    assert status == 422
    assert payload["code"] == code
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [(b"idempotency-key", b"")],
        [(b"idempotency-key", b"white space")],
        [(b"idempotency-key", b"a" * 129)],
        [(b"idempotency-key", b"first"), (b"idempotency-key", b"second")],
    ],
)
def test_invalid_submission_key_refuses_before_verification_probe(configured, verifier, headers):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(app, "/api/v1/verifications", body=b'{"mode":"full"}', headers=headers)
    )

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert verifier.probes == 0
    assert verifier.calls == []
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


def test_verification_retry_precedes_unavailable_probe_changed_policy_and_conflict(
    configured, verifier
):
    app, policy, archive = configured

    async def scenario():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            headers = {"Authorization": f"Bearer {WRITER}", "Idempotency-Key": "known-request"}
            verifier.available = False
            unavailable = await client.post(
                "/api/v1/verifications", json={"mode": "full"}, headers=headers
            )
            assert unavailable.status_code == 503
            assert unavailable.json()["code"] == "HFAPI016"
            assert app.state.operations.list() == ()
            verifier.available = True
            verifier.release.clear()
            try:
                first = await client.post(
                    "/api/v1/verifications", json={"mode": "full"}, headers=headers
                )
                assert first.status_code == 202
                identifier = first.json()["operation"]["operation_id"]
                assert await asyncio.to_thread(verifier.entered.wait, 5)
                verifier.available = False
                policy.write_text("invalid = [")
                retry = await client.post(
                    "/api/v1/verifications",
                    json={"mode": "full", "revision": None, "run_id": None},
                    headers=headers,
                )
                assert retry.status_code == 202
                assert retry.json()["operation"]["operation_id"] == identifier
                assert retry.json()["created"] is False
                assert verifier.probes == 2
                conflict = await client.post(
                    "/api/v1/verifications", json={"mode": "new"}, headers=headers
                )
                assert conflict.status_code == 409
                assert conflict.json()["code"] == "HFAPI012"
                assert verifier.probes == 2
                fresh = await client.post(
                    "/api/v1/verifications",
                    json={"mode": "full"},
                    headers=headers | {"Idempotency-Key": "fresh-request"},
                )
                assert fresh.status_code == 503
                assert fresh.json()["code"] == "HFAPI016"
                assert len(app.state.operations.list()) == 1
                assert len(verifier.calls) == 1
            finally:
                verifier.release.set()

    asyncio.run(scenario())
    assert not archive.exists()


def test_simultaneous_semantically_identical_posts_have_one_durable_admission(configured, verifier):
    app, _, archive = configured

    async def scenario():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            headers = {"Authorization": f"Bearer {WRITER}", "Idempotency-Key": "simultaneous"}
            bodies = ({"mode": "full"}, {"run_id": None, "revision": None, "mode": "full"})
            replies = await asyncio.gather(
                *[
                    client.post("/api/v1/verifications", json=bodies[index % 2], headers=headers)
                    for index in range(16)
                ]
            )
            assert {response.status_code for response in replies} == {202}
            payloads = [response.json() for response in replies]
            identifiers = {payload["operation"]["operation_id"] for payload in payloads}
            assert len(identifiers) == 1
            identifier = identifiers.pop()
            assert sum(payload["created"] for payload in payloads) == 1
            assert len(app.state.operations.list()) == 1
            assert verifier.probes == 1
            result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=5)
            assert result.exit_code == 0
            assert [entry[0] for entry in verifier.calls] == [identifier]
            for response, payload in zip(replies, payloads, strict=True):
                assert response.headers["location"] == f"/api/v1/operations/{identifier}"
                assert payload["links"]["status"] == response.headers["location"]
                assert payload["links"]["result"] == response.headers["location"] + "/result"
            conflict = await client.post("/api/v1/plans", json={}, headers=headers)
            assert conflict.status_code == 409
            assert conflict.json()["code"] == "HFAPI012"
            assert len(app.state.operations.list()) == 1

    asyncio.run(scenario())
    assert not archive.exists()


def test_plan_selector_normalization_and_caller_class_namespace(configured, monkeypatch):
    app, _, archive = configured
    called = []

    def plan(self, request):
        called.append(request.selectors)
        return ServiceResult("plan", {"repositories": []})

    monkeypatch.setattr(CommandServices, "plan_sync", plan)

    async def scenario():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            writer_headers = {"Authorization": f"Bearer {WRITER}", "Idempotency-Key": "same-key"}
            selected = ["model:org/first", "dataset:org/second"]
            first = await client.post(
                "/api/v1/plans", json={"selectors": selected}, headers=writer_headers
            )
            assert first.status_code == 202
            retry = await client.post(
                "/api/v1/plans",
                json={"selectors": [selected[1], selected[0], selected[1]]},
                headers=writer_headers,
            )
            assert retry.status_code == 202
            first_id = first.json()["operation"]["operation_id"]
            assert retry.json()["operation"]["operation_id"] == first_id
            reader = await client.post(
                "/api/v1/plans",
                json={"selectors": selected},
                headers={"Authorization": f"Bearer {READER}", "Idempotency-Key": "same-key"},
            )
            assert reader.status_code == 202
            reader_id = reader.json()["operation"]["operation_id"]
            assert reader_id != first_id
            for identifier in (first_id, reader_id):
                result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=5)
                assert result.exit_code == 0
            assert called == [tuple(sorted(selected)), tuple(sorted(selected))]
            assert len(app.state.operations.list()) == 2

    asyncio.run(scenario())
    assert not archive.exists()


def test_snapshot_zero_wait_policy_refuses_pending_work_but_keeps_reads_responsive(
    configured, monkeypatch
):
    app, policy, archive = configured
    policy.write_text(policy.read_text() + "\n[sync]\nlock_wait_seconds=0\n")
    entered, release = Event(), Event()

    def plan(self, request):
        entered.set()
        assert release.wait(10)
        return ServiceResult("plan", {"repositories": []})

    monkeypatch.setattr(CommandServices, "plan_sync", plan)

    async def scenario():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            headers = {"Authorization": f"Bearer {READER}", "Idempotency-Key": "active-plan"}
            try:
                first = await client.post("/api/v1/plans", json={}, headers=headers)
                assert first.status_code == 202
                assert await asyncio.to_thread(entered.wait, 5)
                pending = await client.post(
                    "/api/v1/plans",
                    json={},
                    headers=headers | {"Idempotency-Key": "no-pending-with-zero"},
                )
                assert pending.status_code == 503
                assert pending.json()["code"] == "HFAPI009"
                assert len(app.state.operations.list()) == 1
                version = await asyncio.wait_for(
                    client.get("/api/v1/version", headers=headers), timeout=1
                )
                assert version.status_code == 200
                assert app.state.runner.pending == 0
            finally:
                release.set()

    asyncio.run(scenario())
    assert not archive.exists()


def test_lost_http_acknowledgement_does_not_cancel_real_sync(  # noqa: PLR0915 - full ownership boundary
    request, monkeypatch
):
    server, layout, hub, lock = request.getfixturevalue("command_archive")
    app = create_app(server, instance_lock_path=lock)
    entered, release = Event(), Event()
    original = hub.snapshot_download

    def download(*args, **kwargs):
        if not kwargs.get("dry_run"):
            entered.set()
            assert release.wait(10)
        return original(*args, **kwargs)

    monkeypatch.setattr(hub, "snapshot_download", download)

    async def scenario():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            body = json.dumps({"selectors": [MODEL.selector]}).encode()
            headers = {
                "Authorization": f"Bearer {WRITER}",
                "Idempotency-Key": "lost-sync-acknowledgement",
            }
            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/api/v1/syncs",
                "raw_path": b"/api/v1/syncs",
                "root_path": "",
                "query_string": b"",
                "headers": [
                    (b"host", b"testserver"),
                    (b"content-type", b"application/json"),
                    *[(key.lower().encode(), value.encode()) for key, value in headers.items()],
                ],
                "client": ("127.0.0.1", 1234),
                "server": ("testserver", 80),
            }
            acknowledged = []

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            async def lost_observer(message):
                if message["type"] == "http.response.start":
                    acknowledged.append(message["status"])
                    message = "synthetic disconnected HTTP observer"
                    raise ConnectionResetError(message)
                pytest.fail("disconnected HTTP observer received a body")

            try:
                await app(scope, receive, lost_observer)
                assert acknowledged == [202]
                assert await asyncio.to_thread(entered.wait, 5)
                records = app.state.operations.list()
                assert len(records) == 1
                identifier = records[0].operation_id
                assert records[0].state == "running"
                assert app.state.runner.active_operation_id == identifier
                with (
                    pytest.raises(SafetyError),
                    locking.exclusive_lock(
                        locking.lock_path(), command="competing after client loss", wait_seconds=0
                    ),
                ):
                    pytest.fail("disconnect released the actual sync writer lock")
                lookup = await client.get("/api/v1/operations/lookup", headers=headers)
                assert lookup.status_code == 200
                assert lookup.json()["envelope"]["data"]["operation"]["operation_id"] == identifier
                version = await client.get("/api/v1/version", headers=headers)
                assert version.status_code == 200
                release.set()
                completed = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=10)
                assert completed.exit_code == 0
                observed = await client.get(
                    f"/api/v1/operations/{identifier}/result", headers=headers
                )
                assert observed.status_code == 200
                assert observed.json()["envelope"] == completed.to_payload()
                reference = read_reference(layout, RepositoryLayout(layout, MODEL).current_ref)
                assert reference.commit_sha == SHA_A
                retry = await client.post(
                    "/api/v1/syncs", json={"selectors": [MODEL.selector]}, headers=headers
                )
                assert retry.status_code == 202
                assert retry.json()["operation"]["operation_id"] == identifier
                assert retry.json()["created"] is False
                assert len(hub.downloads) == 1
            finally:
                release.set()

    asyncio.run(scenario())
