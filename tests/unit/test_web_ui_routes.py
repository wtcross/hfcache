"""Actual source ASGI/auth/capture routes; installed shared-Caddy proof is separate."""

import asyncio
import base64
import os

import httpx
import pytest
from starlette.routing import Route

from hfcache import wire_schema
from hfcache.api import app as application_module
from hfcache.api.app import create_app
from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.ui_serving import UI_CSP, UiResponse, bootstrap_bytes
from hfcache.errors import ConfigurationError, SafetyError
from hfcache.logging import reset
from hfcache.server_config import WebConfig
from hfcache.url_paths import uri_path
from tests.fixtures.web_ui import WIRE_DIGEST, WRITER, make_profile


@pytest.fixture(autouse=True)
def context_digest_and_logging(monkeypatch):
    # This synthetic source fixture binds a known digest. Independent generated
    # authority checks and installed functional fixtures use the real exporter.
    monkeypatch.setattr(wire_schema, "installed_source_digest", lambda: WIRE_DIGEST)
    reset()
    yield
    reset()


def basic(profile):
    return "Basic " + base64.b64encode(b"human:" + profile.password).decode()


@pytest.mark.parametrize("prefix", ["", "/management", "/ui", "/api/v1", "/mcp", "/管理'quoted"])
def test_actual_bootstrap_navigation_alias_assets_and_exact_headers(prefix):
    profile = make_profile(prefix=prefix)
    app = create_app(profile.server, instance_lock_path=profile.lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            capture = app.state.ui_capture
            fd = capture.root_descriptor
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="https://testserver",
                headers={"Authorization": basic(profile)},
            ) as client:
                alias = await client.get(uri_path(prefix + "/ui"))
                assert alias.status_code == 307
                assert alias.headers["location"] == uri_path(prefix + "/ui/")
                response = await client.get(uri_path(prefix + "/ui/bootstrap.json"))
                assert response.status_code == 200
                payload = response.json()
                assert payload["kind"] == "hfcache_ui_bootstrap"
                assert "envelope" not in payload
                assert payload["configured_archive_id"] == profile.policy.archive_id
                assert payload["archive_identity_source"] == "installed_policy"
                assert payload["config_fingerprint"] is None
                assert payload["paths"]["effective_prefix"] == prefix
                assert payload["paths"]["ui_base"] == uri_path(prefix + "/ui/")
                assert all(
                    not item["effective"] and item["reason"] == "feature_unavailable"
                    for item in payload["user"]["admin_permissions"]
                )
                assert not profile.policy.root.exists()
                for path in (
                    "/ui/",
                    "/ui/library",
                    "/ui/operations",
                    "/ui/maintenance",
                    "/ui/administration",
                ):
                    document = await client.get(uri_path(prefix + path))
                    assert document.status_code == 200
                    assert "__HFCACHE_" not in document.text
                    assert "Reload interface" in document.text
                    for name, value in (
                        ("cache-control", "no-store"),
                        ("content-security-policy", UI_CSP),
                        ("x-content-type-options", "nosniff"),
                        ("referrer-policy", "no-referrer"),
                    ):
                        assert document.headers.get_list(name) == [value]
                resource = uri_path(prefix + "/ui/assets/main-AbCd1234.js")
                asset = await client.get(resource)
                assert asset.content == profile.bodies["assets/main-AbCd1234.js"]
                assert asset.headers.get_list("cache-control") == [
                    "private, max-age=3600, immutable"
                ]
                head = await client.head(resource)
                assert head.status_code == 200
                assert not head.content
                assert head.headers["content-length"] == str(len(asset.content))
                assert app.state.ui_streams.active == 0
            assert not app.state.operations.list()
        assert app.state.ui_capture is None
        assert app.state.ui_streams is None
        with pytest.raises(OSError, match="Bad file descriptor"):
            os.fstat(fd)

    asyncio.run(exercise())


def test_enabled_namespace_is_basic_only_and_errors_never_inherit_asset_cache():
    profile = make_profile()
    app = create_app(profile.server, instance_lock_path=profile.lock)

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            for headers in ({}, {"Authorization": "Bearer " + WRITER}):
                denied = await client.head("/ui/not-a-file.js", headers=headers)
                assert denied.status_code == 401
                assert not denied.content
                assert denied.headers["www-authenticate"].startswith("Basic ")
                assert denied.headers.get_list("cache-control") == ["no-store"]
                assert int(denied.headers["content-length"]) > 0
            client.headers["Authorization"] = basic(profile)
            for path in ("/ui/assets/missing.js", "/ui/not-a-route", "/api/v1/not-a-route"):
                missing = await client.get(path)
                assert missing.status_code == 404
                assert "text/html" not in missing.headers["content-type"]
            query = await client.get("/ui/?unexpected=1")
            assert query.status_code >= 400
            assert "text/html" not in query.headers["content-type"]
            ranges = await client.get("/ui/assets/main-AbCd1234.js", headers={"Range": "bytes=0-1"})
            assert ranges.status_code >= 400
            leases = [app.state.ui_streams.acquire() for _ in range(16)]
            try:
                full = await client.get("/ui/assets/main-AbCd1234.js")
                assert full.status_code == 503
                assert full.headers.get_list("cache-control") == ["no-store"]
                head = await client.head("/ui/assets/main-AbCd1234.js")
                assert head.status_code == 200
                rest = await client.get(
                    "/api/v1/version", headers={"Authorization": "Bearer " + WRITER}
                )
                assert rest.status_code == 200
                assert rest.json()["envelope"]["exit_code"] == 0
            finally:
                for lease in leases:
                    lease.release()

    asyncio.run(exercise())


@pytest.mark.parametrize("basic_enabled", [False, True])
@pytest.mark.parametrize("method", ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"])
def test_disabled_ui_retains_bearer404_and_never_loads_installed_ui_contract(
    monkeypatch, basic_enabled, method
):
    profile = make_profile()
    profile.server = profile.server.model_copy(
        update={
            "web": WebConfig.model_validate(
                {
                    "enabled": False,
                    "asset_root": str(profile.assets / "disabled-never-opened"),
                    "manifest_sha256": "f" * 64,
                }
            ),
            "basic": profile.server.basic if basic_enabled else None,
        }
    )
    monkeypatch.setattr(
        wire_schema, "installed_source_digest", lambda: pytest.fail("disabled UI digest access")
    )
    monkeypatch.setattr(
        application_module, "capture_assets", lambda *_a, **_kw: pytest.fail("disabled UI capture")
    )
    app = create_app(profile.server, instance_lock_path=profile.lock)
    for route in app.routes:
        assert isinstance(route, Route)
        assert route.path != "/ui"
        assert not route.path.startswith("/ui/")

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="https://testserver",
                headers={"Authorization": "Bearer " + WRITER},
            ) as client,
        ):
            for path in (
                "/ui",
                "/ui/",
                "/ui/assets/main-AbCd1234.js",
                "/ui/library",
                "/ui/unknown/deep",
            ):
                response = await client.request(method, path)
                assert response.status_code == 404, (method, path, response.text)
                assert response.headers["content-type"] == "application/json"
                assert response.headers.get_list("content-security-policy") == [
                    "frame-ancestors 'none'"
                ]
                assert response.headers.get_list("cache-control") == ["no-store"]
                if method == "HEAD":
                    assert response.content == b""
                    assert int(response.headers["content-length"]) > 0
                else:
                    assert response.json()["code"] == "HFAPI007"

    asyncio.run(exercise())


def test_invalid_capture_precedes_store_construction_or_runner_admission(monkeypatch):
    profile = make_profile()
    (profile.assets / "index.html").write_bytes(b"changed artifact")
    monkeypatch.setattr(
        application_module,
        "OperationStore",
        lambda *_a, **_kw: pytest.fail("store constructed before capture"),
    )
    app = create_app(profile.server, instance_lock_path=profile.lock)

    async def exercise():
        with pytest.raises(ConfigurationError, match="enabled UI artifact"):
            async with app.router.lifespan_context(app):
                pytest.fail("invalid capture started")
        assert app.state.ui_capture is None
        assert app.state.credentials is None
        assert not profile.server.state_directory.exists()

    asyncio.run(exercise())


def test_later_store_failure_closes_the_captured_root_and_clears_state(monkeypatch):
    profile = make_profile()
    captured = []
    original = application_module.capture_assets

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        assert result is not None
        captured.append(result.root_descriptor)
        return result

    def failed_store(*_a, **_kw):
        message = "owned store startup failure"
        raise RuntimeError(message)

    monkeypatch.setattr(application_module, "capture_assets", capture)
    monkeypatch.setattr(application_module, "OperationStore", failed_store)
    app = create_app(profile.server, instance_lock_path=profile.lock)

    async def exercise():
        with pytest.raises(RuntimeError, match="owned store startup failure"):
            async with app.router.lifespan_context(app):
                pytest.fail("store failure started")
        assert app.state.ui_capture is None
        assert app.state.basic_provider is None
        with pytest.raises(OSError, match="Bad file descriptor"):
            os.fstat(captured[0])

    asyncio.run(exercise())


def test_head_errors_preserve_get_status_headers_and_length_without_body():
    profile = make_profile()
    app = create_app(profile.server, instance_lock_path=profile.lock)

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="https://testserver",
                headers={"Authorization": basic(profile)},
            ) as client,
        ):
            for path in ("/ui/not-found.js", "/ui/index.html", "/ui/?unexpected=yes"):
                get = await client.get(path)
                head = await client.head(path)
                assert head.status_code == get.status_code
                assert not head.content
                assert head.headers["content-length"] == str(len(get.content))
                for header in (
                    "content-type",
                    "cache-control",
                    "content-security-policy",
                    "x-content-type-options",
                    "referrer-policy",
                    "permissions-policy",
                ):
                    assert head.headers.get_list(header) == get.headers.get_list(header)
            app.state.ui_streams.stop_admission()
            get = await client.get("/ui/assets/main-AbCd1234.js")
            head = await client.head("/ui/assets/main-AbCd1234.js")
            assert get.status_code == head.status_code == 503
            assert not head.content
            assert head.headers["content-length"] == str(len(get.content))
            assert head.headers.get_list("cache-control") == ["no-store"]

    asyncio.run(exercise())


def test_cancelled_lifespan_waits_for_actual_ui_tasks_before_closing_capture():
    profile = make_profile()
    app = create_app(profile.server, instance_lock_path=profile.lock)

    async def exercise():
        lifespan = app.router.lifespan_context(app)
        await lifespan.__aenter__()
        capture = app.state.ui_capture
        streams = app.state.ui_streams
        descriptor = capture.root_descriptor
        entered = asyncio.Event()
        released = asyncio.Event()
        disconnected = asyncio.Event()

        async def send(_message):
            entered.set()
            await released.wait()

        async def receive():
            await disconnected.wait()
            return {"type": "http.disconnect"}

        response = UiResponse(
            b"held response", mime="text/html", policy="ui_document", streams=streams
        )
        request = asyncio.create_task(response({"method": "GET"}, receive, send))
        await asyncio.wait_for(entered.wait(), 2)
        closing = asyncio.create_task(lifespan.__aexit__(None, None, None))
        await asyncio.sleep(0.05)
        closing.cancel()
        await asyncio.sleep(0.01)
        assert not closing.done()
        assert streams.active == 1
        assert len(streams.tasks) == 2
        assert os.fstat(descriptor).st_ino == profile.assets.stat().st_ino
        disconnected.set()
        await asyncio.wait_for(request, 2)
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(closing, 2)
        assert streams.active == 0
        assert not streams.tasks
        assert not streams.accepting
        assert capture.root_descriptor == -1
        assert app.state.ui_capture is None
        assert app.state.basic_provider is None
        assert app.state.pool.closed
        assert app.state.pool.inflight == 0
        assert not app.state.runner._thread.is_alive()

    asyncio.run(exercise())


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_refused_small_ui_response_headers_have_a_finite_send_deadline(monkeypatch, method):
    profile = make_profile()
    app = create_app(profile.server, instance_lock_path=profile.lock)
    monkeypatch.setattr(application_module, "STREAM_DEADLINE_SECONDS", 0.02)

    async def exercise():
        async with app.router.lifespan_context(app):
            blocked = asyncio.Event()
            messages = []

            async def send(message):
                messages.append(message)
                await blocked.wait()

            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "scheme": "https",
                "method": method,
                "root_path": "",
                "path": "/ui/missing.js",
                "raw_path": b"/ui/missing.js",
                "query_string": b"",
                "headers": [(b"host", b"testserver")],
                "server": ("testserver", 443),
                "client": ("127.0.0.1", 50000),
            }
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(app(scope, receive, send), 1)
            assert messages[0]["type"] == "http.response.start"
            assert messages[0]["status"] == 401
            assert app.state.ui_streams.active == 0
            assert not app.state.ui_streams.tasks

    asyncio.run(exercise())


def test_bootstrap_projection_cannot_label_a_bearer_as_the_human_administrator():
    profile = make_profile()
    app = create_app(profile.server, instance_lock_path=profile.lock)

    async def exercise():
        async with app.router.lifespan_context(app):
            with pytest.raises(SafetyError):
                bootstrap_bytes(
                    app.state.ui_capture,
                    profile.server,
                    profile.policy,
                    Principal(CredentialClass.REST_WRITER),
                    instance_id=app.state.instance_id,
                    effective_prefix="",
                )

    asyncio.run(exercise())
