"""Real Basic verifier plus outer ASGI ordering/CSRF/lifecycle (decision146).

Password bytes are generated only in memory; the owned protected test record
contains a salted hash. These source tests do not establish browser/Caddy proof.
"""

import asyncio
import base64
import secrets
import threading

import httpx
import pytest

from hfcache.api import app as application_module
from hfcache.api.auth import AuthenticationMethod, CredentialClass
from hfcache.api.basic import BasicProvider, create_administrator_record, load_basic_provider
from hfcache.errors import AuthenticationCapacityError, AuthenticationError, ConfigurationError
from hfcache.logging import reset
from hfcache.server_config import validate_server_config_mapping
from hfcache.taxonomy import classify
from tests.fixtures import examples
from tests.intent_fixtures import create_app

WRITER = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
READER = "reader_9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVU"
ORIGIN = "https://testserver"


@pytest.fixture(autouse=True)
def isolated_logging():
    reset()
    yield
    reset()


@pytest.fixture(scope="module")
def in_memory_administrator():
    password = secrets.token_urlsafe(32).encode("ascii")
    record = create_administrator_record("boundary-administrator-v1", "administrator", password)
    return record, password


@pytest.fixture
def configured(tmp_path, in_memory_administrator):
    record, password = in_memory_administrator
    record_path = tmp_path / "administrator.json"
    record_path.write_text(record.model_dump_json())
    record_path.chmod(0o600)
    credentials = {}
    for name, value in (("writer", WRITER), ("reader", READER)):
        path = tmp_path / name
        path.write_text(value)
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n'
    )
    mapping = {
        "schema_version": 1,
        "archive_config": str(policy),
        "state_directory": str(tmp_path / "operations"),
        "credentials": credentials,
        "listener": {"allowed_hosts": ["testserver"], "allowed_origins": [ORIGIN]},
        "basic": {"origin": ORIGIN, "administrator": {"file": str(record_path)}},
    }
    return validate_server_config_mapping(mapping), password, tmp_path / "daemon.lock"


def authorization(password, username=b"administrator"):
    return "Basic " + base64.b64encode(username + b":" + password).decode("ascii")


async def raw(  # noqa: PLR0913 - explicit independent ASGI transport evidence
    app,
    *,
    headers,
    method="POST",
    path="/not-a-route",
    scheme="https",
    client=("127.0.0.1", 49152),
    server=("testserver", 443),
):
    called = 0
    messages = []

    async def receive():
        nonlocal called
        called += 1
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "scheme": scheme,
        "method": method,
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"testserver"), *headers],
        "server": server,
        "client": client,
    }
    await app(scope, receive, send)
    started = next(message for message in messages if message["type"] == "http.response.start")
    return started, called


def test_real_basic_login_projects_legacy_class_without_new_wire_grants(configured):
    server, password, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            provider = app.state.basic_provider
            principal = await provider.authenticate(authorization(password))
            assert principal.authentication_method is AuthenticationMethod.BASIC
            assert principal.credential_class is CredentialClass.REST_WRITER
            assert principal.subject == "boundary-administrator-v1"
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=ORIGIN
            ) as client:
                response = await client.get(
                    "/api/v1/capabilities", headers={"Authorization": authorization(password)}
                )
                assert response.status_code == 200
                payload = response.json()["envelope"]["data"]
                assert payload["credential_class"] == "rest-writer"
                assert payload["capabilities"] == ["read", "write"]
                assert "admin_capabilities" not in payload
        assert not provider.stats.accepting
        assert provider.stats.active == provider.stats.waiting == provider.stats.reservations == 0
        assert app.state.basic_provider is None

    asyncio.run(exercise())


def test_authenticated_openapi_declares_typed_authentication_capacity_response(configured):
    server, password, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client,
        ):
            response = await client.get(
                "/api/v1/openapi.json", headers={"Authorization": authorization(password)}
            )
            assert response.status_code == 200
            documented = response.json()["paths"]["/api/v1/status"]["get"]["responses"]
            assert documented["429"]["content"]["application/json"]["schema"] == {
                "$ref": "#/components/schemas/ApiProblem"
            }

    asyncio.run(exercise())


@pytest.mark.parametrize("enabled", [False, True])
def test_openapi_describes_optional_basic_as_an_alternative_without_changing_outer_authentication(
    configured, enabled
):
    server, _, lock = configured
    if not enabled:
        server = server.model_copy(update={"basic": None})
    else:
        password = ("non-ASCII-\u00e9-" + secrets.token_urlsafe(32)).encode("utf-8")
        username = "op\u00e9rateur"
        record = create_administrator_record("spec-administrator", username, password)
        server.basic.administrator.file.write_text(record.model_dump_json())
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client,
        ):
            assert (await client.get("/api/v1/openapi.json")).status_code == 401
            authorization_value = (
                authorization(password, username.encode("utf-8")) if enabled else f"Bearer {READER}"
            )
            response = await client.get(
                "/api/v1/openapi.json", headers={"Authorization": authorization_value}
            )
            assert response.status_code == 200
            schema = response.json()
            schemes = schema["components"]["securitySchemes"]
            expected = [{"hfcacheBearer": []}]
            if enabled:
                assert schemes["hfcacheBasic"] == {"type": "http", "scheme": "basic"}
                expected.append({"hfcacheBasic": []})
            assert set(schemes) == (set().union(*(set(item) for item in expected)))
            for path in schema["paths"].values():
                for operation in path.values():
                    assert operation["security"] == expected
            assert "/mcp" not in schema["paths"]
            assert "/mcp/" not in schema["paths"]

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"]
)
@pytest.mark.parametrize(
    "case",
    [
        "missing-origin",
        "null-origin",
        "foreign-origin",
        "duplicate-origin",
        "missing-intent",
        "duplicate-intent",
        "wrong-intent",
        "form",
        "duplicate-type",
        "encoding",
    ],
)
def test_every_unsafe_basic_method_rejects_csrf_before_receiving_any_body(configured, method, case):
    server, password, lock = configured
    app = create_app(server, instance_lock_path=lock)
    headers = [
        (b"authorization", authorization(password).encode()),
        (b"origin", ORIGIN.encode()),
        (b"content-type", b"application/json"),
        (b"x-hfcache-request", b"1"),
    ]
    if case == "missing-origin":
        headers = [item for item in headers if item[0] != b"origin"]
    elif case in {"null-origin", "foreign-origin"}:
        headers = [
            (
                name,
                (b"null" if case == "null-origin" else b"https://foreign.invalid")
                if name == b"origin"
                else value,
            )
            for name, value in headers
        ]
    elif case == "duplicate-origin":
        headers.append((b"origin", ORIGIN.encode()))
    elif case == "missing-intent":
        headers = [item for item in headers if item[0] != b"x-hfcache-request"]
    elif case == "duplicate-intent":
        headers.append((b"x-hfcache-request", b"1"))
    elif case == "wrong-intent":
        headers = [
            (name, b"0" if name == b"x-hfcache-request" else value) for name, value in headers
        ]
    elif case == "form":
        headers = [
            (name, b"application/x-www-form-urlencoded" if name == b"content-type" else value)
            for name, value in headers
        ]
    elif case == "duplicate-type":
        headers.append((b"content-type", b"application/json"))
    else:
        headers.append((b"content-encoding", b"gzip"))

    async def exercise():
        async with app.router.lifespan_context(app):
            started, called = await raw(app, headers=headers, method=method)
            assert started["status"] == 403
            assert called == 0

    asyncio.run(exercise())


def test_wrong_basic_credentials_still_authenticate_before_ordinary_csrf_or_host_errors(configured):
    server, _, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            for username in (b"administrator", b"wrong-user"):
                header = authorization(secrets.token_urlsafe(24).encode(), username)
                started, called = await raw(
                    app,
                    headers=[
                        (b"authorization", header.encode()),
                        (b"origin", b"https://foreign.invalid"),
                    ],
                )
                assert started["status"] == 401
                assert (
                    dict(started["headers"])[b"www-authenticate"]
                    == b'Basic realm="hfcache", charset="UTF-8"'
                )
                assert called == 0

    asyncio.run(exercise())


def test_basic_same_origin_json_and_legacy_no_origin_bearer_can_validate_configuration(configured):
    server, password, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client,
        ):
            for headers in (
                {
                    "Authorization": authorization(password),
                    "Origin": ORIGIN,
                    "X-Hfcache-Request": "1",
                },
                {"Authorization": "Bearer " + WRITER},
            ):
                response = await client.post("/api/v1/config/validate", json={}, headers=headers)
                assert response.status_code == 200
                assert response.json()["envelope"]["command"] == "config validate"

    asyncio.run(exercise())


def test_capacity_refusal_is_bounded_problem_without_password_retry_challenge(
    configured, monkeypatch
):
    server, password, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):

            async def full(_authorization):
                raise AuthenticationCapacityError

            monkeypatch.setattr(app.state.basic_provider, "authenticate", full)
            started, called = await raw(
                app, headers=[(b"authorization", authorization(password).encode())], method="GET"
            )
            assert started["status"] == 429
            assert b"www-authenticate" not in dict(started["headers"])
            assert called == 0

    asyncio.run(exercise())


def test_challenge_dispatch_never_falls_back_and_preserves_bearer_compatibility(configured):
    server, password, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client,
        ):
            missing = await client.get("/api/v1/version")
            assert missing.status_code == 401
            assert (
                missing.headers["www-authenticate"]
                == 'Basic realm="hfcache", charset="UTF-8", Bearer realm="hfcache"'
            )
            for header, expected in (
                ("Bearer invalid", 'Bearer realm="hfcache"'),
                ("Basic invalid", 'Basic realm="hfcache", charset="UTF-8"'),
            ):
                response = await client.get("/not-a-route", headers={"Authorization": header})
                assert response.status_code == 401
                assert response.headers["www-authenticate"] == expected
            response = await client.get(
                "/api/v1/version", headers={"Authorization": "Bearer " + READER}
            )
            assert response.status_code == 200
            valid = await client.get(
                "/not-a-route", headers={"Authorization": authorization(password)}
            )
            assert valid.status_code == 404

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "headers",
    [
        [(b"authorization", b"Basic x"), (b"authorization", b"Basic y")],
        [(b"authorization", b"Basic " + b"x" * 8192)],
        [(b"authorization", b"Basic x"), (b"x-large", b"x" * 32768)],
        [(b"authorization", b"Basic x"), (b"content-length", b"99999999999")],
    ],
)
def test_cheap_duplicate_and_work_limits_never_dispatch_the_hash_provider(
    configured, monkeypatch, headers
):
    server, _, lock = configured
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):

            async def forbidden(_header):
                pytest.fail("malformed bounded input invoked password verification")

            monkeypatch.setattr(app.state.basic_provider, "authenticate", forbidden)
            started, called = await raw(app, headers=headers)
            assert started["status"] in {401, 413}
            assert called == 0

    asyncio.run(exercise())


@pytest.mark.parametrize("configured_basic", [False, True])
def test_legacy_missing_or_bearer_authentication_precedes_declared_work_limits(
    configured, monkeypatch, configured_basic
):
    server, _, lock = configured
    if not configured_basic:
        server = server.model_copy(update={"basic": None})
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            if configured_basic:

                async def forbidden(_header):
                    pytest.fail("oversized Basic request reached password verification")

                monkeypatch.setattr(app.state.basic_provider, "authenticate", forbidden)
            for header, expected in (
                (None, 401),
                (b"Bearer invalid", 401),
                (("Bearer " + READER).encode(), 413),
                (b"Basic invalid", 413 if configured_basic else 401),
            ):
                headers = [(b"content-length", b"99999999999")]
                if header is not None:
                    headers.append((b"authorization", header))
                started, called = await raw(app, headers=headers, method="GET")
                assert started["status"] == expected
                assert called == 0
                if expected == 401 and not configured_basic:
                    assert (
                        dict(started["headers"])[b"www-authenticate"] == b'Bearer realm="hfcache"'
                    )

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "channel", ["loopback", "tls", "native", "uncorroborated-unix", "remote-http"]
)
def test_basic_transport_proof_uses_actual_scope_not_caller_headers(configured, channel):
    server, password, lock = configured
    app = create_app(server, instance_lock_path=lock)
    options = {"scheme": "http", "client": ("127.0.0.1", 49152), "server": ("testserver", 80)}
    if channel == "tls":
        options |= {"scheme": "https", "client": ("192.0.2.10", 49152)}
    elif channel in {"native", "uncorroborated-unix"}:
        options |= {
            "client": None,
            "server": ("/owned-fixture/api.sock", None)
            if channel == "native"
            else ("testserver", 80),
        }
    elif channel == "remote-http":
        options |= {"client": ("192.0.2.10", 49152)}

    async def exercise():
        async with app.router.lifespan_context(app):
            started, called = await raw(
                app,
                headers=[
                    (b"authorization", authorization(password).encode()),
                    (b"x-forwarded-proto", b"https"),
                ],
                method="GET",
                path="/not-a-route",
                **options,
            )
            assert started["status"] == (
                403 if channel in {"remote-http", "uncorroborated-unix"} else 404
            )
            assert called == (0 if channel in {"remote-http", "uncorroborated-unix"} else 1)

    asyncio.run(exercise())


def test_partial_startup_failure_drains_new_provider_and_clears_credentials(
    configured, monkeypatch
):
    server, _, lock = configured
    provider = load_basic_provider(server.basic)
    monkeypatch.setattr(application_module, "load_basic_provider", lambda _: provider)
    monkeypatch.setattr(
        application_module,
        "query_version",
        lambda: (_ for _ in ()).throw(RuntimeError("owned startup injection")),
    )
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        with pytest.raises(RuntimeError, match="owned startup injection"):
            async with app.router.lifespan_context(app):
                pytest.fail("partial startup was incorrectly accepted")
        assert provider is not None
        assert not provider.stats.accepting
        assert app.state.pool.closed
        assert app.state.credentials is None
        assert app.state.basic_provider is None

    asyncio.run(exercise())


def blocked_provider(record):
    entered, release = threading.Event(), threading.Event()

    def blocked_verifier(_password):
        entered.set()
        if not release.wait(10):
            message = "owned lifecycle verifier was not released"
            raise RuntimeError(message)
        return True

    # Only the verifier result is injected here; executor, admission, cancellation
    # and full application teardown follow the actual source paths.
    return BasicProvider(record, verify=blocked_verifier), entered, release


def test_cancelled_lifespan_drains_exact_accepted_auth_worker_before_propagating(
    configured, in_memory_administrator, monkeypatch
):
    server, password, lock = configured
    record, _ = in_memory_administrator
    provider, entered, release = blocked_provider(record)
    monkeypatch.setattr(application_module, "load_basic_provider", lambda _: provider)
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        ready = asyncio.Event()

        async def own_lifespan():
            async with app.router.lifespan_context(app):
                ready.set()
                await asyncio.Future()

        lifetime = asyncio.create_task(own_lifespan())
        authentication = None
        try:
            await asyncio.wait_for(ready.wait(), timeout=5)
            authentication = asyncio.create_task(provider.authenticate(authorization(password)))
            assert await asyncio.to_thread(entered.wait, 5)
            workers = tuple(provider._executor._threads)
            assert workers
            authentication.cancel()
            with pytest.raises(asyncio.CancelledError):
                await authentication
            assert provider.stats.active == 1
            lifetime.cancel()
            for _ in range(500):
                if not provider.stats.accepting:
                    break
                await asyncio.sleep(0.01)
            assert not provider.stats.accepting
            lifetime.cancel()
            await asyncio.sleep(0.02)
            assert not lifetime.done()
            assert any(worker.is_alive() for worker in workers)
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(lifetime, timeout=5)
            assert all(not worker.is_alive() for worker in workers)
            assert (
                provider.stats.active == provider.stats.waiting == provider.stats.reservations == 0
            )
            assert app.state.credentials is None
            assert app.state.basic_provider is None
        finally:
            release.set()
            if authentication is not None:
                authentication.cancel()
                await asyncio.gather(authentication, return_exceptions=True)
            if not lifetime.done():
                lifetime.cancel()
            await asyncio.gather(lifetime, return_exceptions=True)

    asyncio.run(exercise())


def test_bad_basic_source_refuses_startup_without_legacy_source_fallback(configured):
    server, _, lock = configured
    server.basic.administrator.file.write_bytes(b"{}")
    app = create_app(server, instance_lock_path=lock)

    async def exercise():
        with pytest.raises(ConfigurationError) as failure:
            async with app.router.lifespan_context(app):
                pytest.fail("bad Basic source was ignored")
        assert failure.value.problems[0].code == "HFAPI003"
        assert app.state.credentials is None

    asyncio.run(exercise())


def test_capacity_error_and_existing_authentication_error_keep_distinct_taxonomy():
    error = AuthenticationCapacityError()
    assert error.status_code == 429
    assert int(error.exit_code) == int(classify("HFAPI021")) == 20
    assert error.problems[0].code == "HFAPI021"
    assert AuthenticationError().headers["WWW-Authenticate"] == 'Bearer realm="hfcache"'
