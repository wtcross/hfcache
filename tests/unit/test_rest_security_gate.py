"""Route-complete REST authentication/role acceptance before MCP (API-016)."""

import asyncio
import json

import pytest
from starlette.routing import Route

from hfcache.api.app import create_app
from hfcache.logging import reset
from hfcache.server_config import validate_server_config_mapping
from tests.fixtures.examples import ARCHIVE_ID

WRITER = "acceptance-writer-" + "W" * 40
READER = "acceptance-reader-" + "R" * 40
MCP = "acceptance-other-interface-" + "M" * 40
OPAQUE = "untrusted-request-content-must-not-be-reflected"
PREFIX = "/api/v1"

# Independent of app decorators and the semantic parity matrix: adding any HTTP
# surface requires its exact method/path to join this adversarial inventory.
READ_PATHS = (
    "/version",
    "/capabilities",
    "/health",
    "/archive/inspection",
    "/status",
    "/repositories",
    "/repositories/revisions",
    "/verification/estimate",
    "/runs",
    "/runs/{run_id}",
    "/repositories/{repository_type}/{namespace}/{name}/references/{revision}",
    "/repositories/{repository_type}/{namespace}/{name}/manifests/{commit_sha}/{publication_id}",
    "/operations",
    "/operations/lookup",
    "/operations/{operation_id}",
    "/operations/{operation_id}/result",
    "/operations/{operation_id}/events",
    "/openapi.json",
    "/docs",
)
READER_POSTS = (
    "/config/validate",
    "/plans",
    "/diagnostics",
    "/prune-plans",
    "/purge-plans",
    "/recovery-plans",
    "/quarantine-plans",
)
WRITER_POSTS = (
    "/syncs",
    "/verifications",
    "/prunes",
    "/purges",
    "/recoveries",
    "/quarantine-cleanups",
    "/repairs",
    "/archive/initializations",
)
ROUTES = tuple(("GET", PREFIX + path) for path in READ_PATHS) + tuple(
    ("POST", PREFIX + path) for path in (*READER_POSTS, *WRITER_POSTS)
)


@pytest.fixture
def configured(tmp_path):
    archive = tmp_path / "archive-must-not-be-created"
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{archive}"\n'
        f'archive_id="{ARCHIVE_ID}"\n[hub]\ntoken_mode="disabled"\n'
    )
    credentials = {}
    for name, token in (("writer", WRITER), ("reader", READER), ("mcp_reader", MCP)):
        path = tmp_path / name
        path.write_text(token)
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(policy),
            "state_directory": str(tmp_path / "state"),
            "credentials": credentials,
            "maintenance_enabled": True,
            "interactive_docs": True,
            "listener": {"allowed_hosts": ["testserver"]},
        }
    )
    reset()
    try:
        yield server, archive, tmp_path / "instance.lock"
    finally:
        reset()


def concrete(path):
    return path.format(
        repository_type="model",
        namespace="org",
        name="repository",
        revision="current",
        commit_sha="a" * 40,
        publication_id="b" * 32,
        run_id="c" * 32,
        operation_id="d" * 32,
    )


async def raw_request(  # noqa: PLR0913 - independent HTTP authentication/body dimensions
    app, method, path, authorization, *, body=b"", extra=()
):
    received = 0
    messages = []

    async def receive():
        nonlocal received
        received += 1
        if received == 1:
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    headers = [(b"host", b"testserver"), (b"content-type", b"application/json")]
    headers.extend((b"authorization", value) for value in authorization)
    headers.extend(extra)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }
    await app(scope, receive, send)
    start = next(message for message in messages if message["type"] == "http.response.start")
    payload = b"".join(
        message.get("body", b"") for message in messages if message["type"] == "http.response.body"
    )
    return start["status"], payload.decode(), received, dict(start["headers"])


@pytest.mark.parametrize("docs_enabled", [False, True])
def test_every_registered_rest_method_has_an_independent_security_case(configured, docs_enabled):
    server, archive, lock = configured
    server = server.model_copy(update={"interactive_docs": docs_enabled})
    app = create_app(server, instance_lock_path=lock)
    actual = set()
    for route in app.routes:
        assert isinstance(route, Route)
        assert route.methods is not None
        actual.update((method, route.path) for method in route.methods)
    expected = set(ROUTES)
    if not docs_enabled:
        expected.remove(("GET", PREFIX + "/docs"))
    assert actual == expected
    assert len(actual) == (34 if docs_enabled else 33)
    assert not archive.exists()
    assert not lock.exists()


@pytest.mark.parametrize(
    "authorization",
    [
        (),
        (b"Basic ignored",),
        (b"Bearer unknown-" + b"x" * 40,),
        (f"Bearer {MCP}".encode(),),
        (f"Bearer {READER}".encode(), f"Bearer {WRITER}".encode()),
        (f"Bearer {READER} ".encode(),),
    ],
    ids=["absent", "basic", "unknown", "other-interface", "duplicate", "malformed"],
)
def test_all_actual_routes_reject_bad_bearers_before_receiving_any_body(configured, authorization):
    server, archive, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            for method, path in ROUTES:
                status, payload, received, headers = await raw_request(
                    app, method, concrete(path), authorization, body=OPAQUE.encode() * 100
                )
                assert status == 401, (method, path, payload)
                assert received == 0, (method, path)
                assert json.loads(payload)["code"] == "HFAPI001"
                assert headers[b"www-authenticate"].startswith(b"Bearer")
                assert all(value not in payload for value in (WRITER, READER, MCP, OPAQUE))
            assert app.state.operations.list() == ()

    asyncio.run(exercise())
    assert not archive.exists()


def test_reader_writer_roles_cover_all_routes_without_admission_or_hub_access(configured):
    server, archive, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            for token in (READER, WRITER):
                authorization = (f"Bearer {token}".encode(),)
                for method, path in ROUTES:
                    # Invalid POST syntax proves access to body validation,
                    # without creating a job, resolving Hub authority or probing.
                    status, payload, received, _ = await raw_request(
                        app,
                        method,
                        concrete(path),
                        authorization,
                        body=b"{" if method == "POST" else b"",
                        extra=((b"idempotency-key", b"role-audit"),),
                    )
                    if method == "POST":
                        refused = token == READER and path.removeprefix(PREFIX) in WRITER_POSTS
                        assert status == (403 if refused else 422), (token, path, payload)
                        assert received == (0 if refused else 1), (token, path)
                    else:
                        assert status not in {401, 403, 405}, (path, payload)
                    assert all(value not in payload for value in (WRITER, READER, MCP))
            assert app.state.operations.list() == ()

    asyncio.run(exercise())
    assert not archive.exists()


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/config/validate", {"candidate": None}),
        ("/plans", {"candidate": "schema_version=1"}),
        ("/diagnostics", {"read_only": False}),
    ],
)
def test_mixed_post_roles_refuse_reader_content_before_dto_or_admission(configured, path, body):
    server, archive, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            status, payload, received, _ = await raw_request(
                app,
                "POST",
                PREFIX + path,
                (f"Bearer {READER}".encode(),),
                body=json.dumps(body).encode(),
            )
            assert status == 403
            assert json.loads(payload)["code"] == "HFAPI002"
            assert received == 1
            assert app.state.operations.list() == ()

    asyncio.run(exercise())
    assert not archive.exists()
