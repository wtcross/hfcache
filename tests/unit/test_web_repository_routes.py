"""WEB013 recognized shells: real source ASGI/auth, never archive membership."""

import asyncio
import base64

import httpx
import pytest

from hfcache import wire_schema
from hfcache.api.ui_serving import UI_CSP, is_repository_navigation
from hfcache.logging import reset
from hfcache.url_paths import uri_path
from tests.fixtures.web_ui import WIRE_DIGEST, WRITER, make_profile
from tests.intent_fixtures import create_app


@pytest.fixture(autouse=True)
def source_fixture_identity(monkeypatch):
    # Typed bootstrap/source coherence has independent real installed tests.
    monkeypatch.setattr(wire_schema, "installed_source_digest", lambda: WIRE_DIGEST)
    reset()
    yield
    reset()


def authorization(profile):
    return "Basic " + base64.b64encode(b"human:" + profile.password).decode()


@pytest.mark.parametrize("prefix", ["", "/management", "/ui", "/api/v1", "/管理'quoted"])
def test_recognized_repository_routes_share_authenticated_captured_shell_without_archive(prefix):
    profile = make_profile(prefix=prefix)
    app = create_app(profile.server, instance_lock_path=profile.lock)

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="https://testserver",
                headers={"Authorization": authorization(profile)},
            ) as client,
        ):
            expected = (await client.get(uri_path(prefix + "/ui/library"))).content
            for kind in ("model", "dataset"):
                for name in ("Name_v1.0", "a" * 96):
                    path = uri_path(prefix + f"/ui/repositories/{kind}/Owner-1/{name}")
                    response = await client.get(path)
                    assert response.status_code == 200
                    assert response.content == expected
                    assert response.headers.get_list("cache-control") == ["no-store"]
                    assert response.headers.get_list("content-security-policy") == [UI_CSP]
                    head = await client.head(path)
                    assert head.status_code == 200
                    assert head.content == b""
                    assert head.headers["content-length"] == str(len(expected))
            assert not profile.policy.root.exists()
            assert not app.state.operations.list()

    asyncio.run(exercise())


@pytest.mark.parametrize("prefix", ["", "/management"])
def test_repository_route_refusals_do_not_expand_spa_fallback_or_disclose_membership(prefix):
    profile = make_profile(prefix=prefix)
    app = create_app(profile.server, instance_lock_path=profile.lock)
    invalid = (
        "repositories",
        "repositories/models/owner/name",
        "repositories/MODEL/owner/name",
        "repositories/model/owner/name/extra",
        "repositories/model/owner/name/",
        "repositories/model//name",
        "repositories/model/_owner/name",
        "repositories/model/owner/.hidden",
        "repositories/model/owner/" + "a" * 97,
        "repositories/model/owner/name%2fextra",
        "repositories/model/owner%2fname",
        "repositories/%6dodel/owner/name",
        "repositories/model/%6fwner/name",
        "repositories/model/owner/name%2e",
        "repositories/model/owner/name%3fq=x",
        "repositories/model/%252f/name",
    )

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            valid = uri_path(prefix + "/ui/repositories/model/owner/name")
            for headers in ({}, {"Authorization": "Bearer " + WRITER}):
                for suffix in ("repositories/model/owner/name", invalid[1]):
                    response = await client.get(uri_path(prefix + "/ui/") + suffix, headers=headers)
                    assert response.status_code == 401
                    assert response.headers["www-authenticate"].startswith("Basic ")
            client.headers["Authorization"] = authorization(profile)
            for member in invalid:
                response = await client.get(uri_path(prefix + "/ui/") + member)
                assert response.status_code == 404, (member, response.status_code)
                assert response.json()["code"] == "HFAPI007"
                assert "text/html" not in response.headers["content-type"]
                assert response.headers.get_list("cache-control") == ["no-store"]
            queried = await client.get(valid + "?tab=files")
            assert queried.status_code == 422
            assert "text/html" not in queried.headers["content-type"]
            body = await client.request("GET", valid, content=b"unexpected")
            assert body.status_code >= 400
            assert "text/html" not in body.headers["content-type"]
            assert not profile.policy.root.exists()
            assert not app.state.operations.list()

    asyncio.run(exercise())


def test_repository_shell_requires_original_canonical_raw_path_proof():
    member = "repositories/model/owner/name"
    assert not is_repository_navigation(member, raw_path=None, effective_prefix="")
    assert not is_repository_navigation(
        member, raw_path=b"/ui/repositories/model/owner%2fname", effective_prefix=""
    )
    assert not is_repository_navigation(
        member, raw_path=b"/other/ui/repositories/model/owner/name", effective_prefix=""
    )
