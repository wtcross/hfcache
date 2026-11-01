"""Real ASGI/receipt flow with owned helper adapter and original reconstruction.

The adapter simulates protected capture only. Separate real Unix/installed tests
own peer, policy and host confinement; these tests claim no installed acceptance.
"""

import asyncio
import copy
import hashlib
import hmac
import secrets
import threading
from dataclasses import replace
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import httpx
import pytest

from hfcache import host_policy
from hfcache.api.app import create_app
from hfcache.host_models import HostStatus, unavailable_host_status
from hfcache.host_protocol import HostProtocolError
from hfcache.hub import DownloadEstimate, RepositoryFacts, TreeEntry
from hfcache.identity import CommitSha
from hfcache.services.commands import CommandServices
from hfcache.services.context import ServiceResult
from tests.fixtures import examples
from tests.unit.test_host_action_routes import (
    ORIGIN,
)
from tests.unit.test_host_action_routes import (
    administrator as administrator,  # noqa: PLC0414 - shared pytest fixture
)
from tests.unit.test_host_action_routes import (
    configured as configured,  # noqa: PLC0414 - shared pytest fixture
)
from tests.unit.test_host_authorization import StatusClient, status

if TYPE_CHECKING:
    from pathlib import Path

REAL_PLAN_SYNC = CommandServices.plan_sync


class ConfigurationAdapter(StatusClient):
    def __init__(self, path: Path, monkeypatch):
        super().__init__()
        self.path = path
        self.key = secrets.token_bytes(32)
        self.prepare_calls = 0
        self.read_calls = 0
        self.read_requests = []

        def revalidate(snapshot):
            if self.path.read_bytes() != snapshot._inspection.config_body:
                reason = "config-conflict"
                raise host_policy.InspectionError(reason)

        monkeypatch.setattr(host_policy, "revalidate", revalidate)

    def snapshot(self):
        body = self.path.read_bytes()

        def revision(domain, *parts):
            digest = hmac.new(self.key, digestmod=hashlib.sha256)
            for part in (domain, *parts):
                digest.update(len(part).to_bytes(8, "big"))
                digest.update(part)
            return digest.hexdigest()

        return cast(
            "host_policy.AuthoritySnapshot",
            SimpleNamespace(
                archive_id=examples.ARCHIVE_ID,
                base_revision=revision(b"host-config-base-v1", body),
                _inspection=SimpleNamespace(config_body=body, revision=revision),
                status=lambda: copy.deepcopy(self.value),
            ),
        )

    async def async_config_read(self, body=None):
        self.read_calls += 1
        self.read_requests.append(copy.deepcopy(body))
        try:
            return host_policy.read_config_base(self.snapshot(), body)
        except host_policy.InspectionError as error:
            raise HostProtocolError(error.reason) from None

    def config_prepare(self, body):
        self.prepare_calls += 1
        try:
            return host_policy.prepare_configuration(self.snapshot(), body)
        except host_policy.InspectionError as error:
            raise HostProtocolError(error.reason) from None

    async def async_config_prepare(self, body):
        return self.config_prepare(body)


def _settings(base, *, workers=3):
    return {
        "managed": {
            "base_revision": base,
            "edits": [{"kind": "settings-replace", "settings": {"sync": {"max_workers": workers}}}],
        }
    }


def test_configuration_read_and_empty_scope_preview_never_install(configured, monkeypatch):
    server, lock, headers, _, executed = configured
    before = server.archive_config.read_bytes()
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                assert read.status_code == 200
                assert helper.async_calls == 0
                assert helper.read_calls == 1
                assert helper.read_requests == [
                    {
                        "expected_archive_id": app.state.policy.archive_id,
                        "expected_archive_root": str(app.state.policy.root),
                    }
                ]
                data = read.json()["envelope"]["data"]
                assert data["editable"]["sync"]["max_workers"] == 4
                assert "hub" not in data["editable"]
                assert "archive_root" not in data["editable"]["storage"]
                request = _settings(data["base_revision"])
                validated = await client.post(
                    "/api/v1/config/validate", json=request, headers=headers
                )
                assert validated.status_code == 200
                validation = validated.json()["envelope"]["data"]
                assert validation["valid"] is True
                assert validation["required_selectors"] == []
                assert "candidate" not in validation
                helper.value = status(denied={"hub"})
                accepted = await client.post(
                    "/api/v1/plans",
                    json=request,
                    headers=headers | {"Idempotency-Key": "managed-settings-preview"},
                )
                assert accepted.status_code == 202
                identifier = accepted.json()["operation"]["operation_id"]
                result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                assert result.exit_code == 0
                assert result.data["complete"] is True
                assert result.data["sizing"] is None
                assert result.data["candidate_revision"] == validation["candidate_revision"]
                duplicate = await client.post(
                    "/api/v1/plans",
                    json=request,
                    headers=headers | {"Idempotency-Key": "managed-settings-preview"},
                )
                assert duplicate.status_code == 202
                assert duplicate.json()["operation"]["operation_id"] == identifier
                assert duplicate.json()["created"] is False
                assert executed == []
                assert server.archive_config.read_bytes() == before
                assert not list(server.archive_config.parent.glob("*.candidate*"))

    asyncio.run(exercise())


@pytest.mark.parametrize("path", ["/api/v1/config", "/api/v1/config/validate", "/api/v1/plans"])
def test_old_writer_never_gains_configuration_admin(configured, monkeypatch, path):
    server, lock, _, token, _ = configured
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                auth = {"Authorization": "Bearer " + token, "Idempotency-Key": "no-admin-grant"}
                if path == "/api/v1/config":
                    response = await client.get(path, headers=auth)
                else:
                    response = await client.post(path, json=_settings("0" * 64), headers=auth)
                assert response.status_code == 403
                assert helper.read_calls == helper.prepare_calls == helper.async_calls == 0
                assert app.state.operations.list() == ()

    asyncio.run(exercise())


def test_comment_only_base_change_conflicts_without_policy_change(configured, monkeypatch):
    server, lock, headers, _, _ = configured
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                original = (await client.get("/api/v1/config", headers=headers)).json()["envelope"][
                    "data"
                ]
                fingerprint = app.state.policy.snapshot().fingerprint
                server.archive_config.write_bytes(
                    server.archive_config.read_bytes() + b"\n# concurrent edit\n"
                )
                assert app.state.policy.snapshot().fingerprint == fingerprint
                response = await client.post(
                    "/api/v1/config/validate",
                    json=_settings(original["base_revision"]),
                    headers=headers,
                )
                assert response.status_code == 409
                fresh = (await client.get("/api/v1/config", headers=headers)).json()["envelope"][
                    "data"
                ]
                assert fresh["base_revision"] != original["base_revision"]
                assert fresh["editable"] == original["editable"]

    asyncio.run(exercise())


def test_queued_preview_rechecks_full_base_and_original_handle_survives(configured, monkeypatch):
    server, lock, headers, _, _ = configured
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)
    entered, release = threading.Event(), threading.Event()

    def held_plan(*_args):
        entered.set()
        if not release.wait(timeout=5):
            raise TimeoutError
        return ServiceResult("plan", {})

    monkeypatch.setattr(CommandServices, "plan_sync", held_plan)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = (await client.get("/api/v1/config", headers=headers)).json()["envelope"][
                    "data"
                ]
                first = await client.post(
                    "/api/v1/plans", json={}, headers=headers | {"Idempotency-Key": "hold-first"}
                )
                assert first.status_code == 202
                assert await asyncio.to_thread(entered.wait, 3)
                try:
                    queued = await client.post(
                        "/api/v1/plans",
                        json=_settings(read["base_revision"]),
                        headers=headers | {"Idempotency-Key": "queued-managed"},
                    )
                    assert queued.status_code == 202
                    identifier = queued.json()["operation"]["operation_id"]
                    server.archive_config.write_bytes(
                        server.archive_config.read_bytes() + b"\n# changed while queued\n"
                    )
                finally:
                    release.set()
                result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                assert result.exit_code != 0
                assert result.errors[0].code == "HFAPI007"
                helper.value = status(denied={"configuration", "hub"})
                original = await client.get(
                    f"/api/v1/operations/{identifier}/result", headers=headers
                )
                assert original.status_code == 200
                assert original.json()["envelope"]["errors"][0]["code"] == "HFAPI007"
                assert len(app.state.operations.list()) == 2

    asyncio.run(exercise())


@pytest.mark.parametrize("hub_allowed", [False, True])
def test_nonempty_scope_needs_hub_grant_and_keeps_protected_values_private(
    configured, monkeypatch, hub_allowed
):
    """Original planning service uses an owned upstream adapter, not a replaced result."""
    server, lock, headers, _, _ = configured
    hidden = "private-unregistered-source-name"
    server.archive_config.write_text(
        server.archive_config.read_text() + f'\n[hub]\ncredential_name="{hidden}"\n'
    )
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)
    helper.value = status(denied=set() if hub_allowed else {"hub"})
    calls = []

    class Hub:
        def require_identity(self, account):
            assert account == ""

        def repository(self, identity, revision):
            assert revision == "main"
            return RepositoryFacts(
                identity=identity, commit_sha=CommitSha("1" * 40), private=False, gated=False
            )

        def tree(self, identity, commit_sha):
            return (TreeEntry(path="config.json", size=10),)

        def estimate(self, identity, commit_sha, *, cache_dir, max_workers):
            return DownloadEstimate(file_count=1, logical_bytes=10, new_bytes=10)

    monkeypatch.setattr("hfcache.services.commands.HubClient.of", lambda *_args, **_kw: Hub())

    def sized(service, request):
        calls.append((service.config.hub.credential_name, request.selectors))
        return REAL_PLAN_SYNC(service, request)

    monkeypatch.setattr(CommandServices, "plan_sync", sized)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                assert hidden not in read.text
                base = read.json()["envelope"]["data"]["base_revision"]
                body = {
                    "managed": {
                        "base_revision": base,
                        "edits": [
                            {
                                "kind": "repository-upsert",
                                "repository": {"id": "example/model", "type": "model"},
                            }
                        ],
                    }
                }
                accepted = await client.post(
                    "/api/v1/plans",
                    json=body,
                    headers=headers | {"Idempotency-Key": "sizing-requires-hub"},
                )
                if not hub_allowed:
                    assert accepted.status_code == 403
                    assert app.state.operations.list() == ()
                    assert calls == []
                    return
                assert accepted.status_code == 202
                identifier = accepted.json()["operation"]["operation_id"]
                result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                assert result.exit_code == 0
                assert result.data["complete"] is True
                assert result.data["required_selectors"] == ["model:example/model"]
                assert calls == [(hidden, ("model:example/model",))]
                for path in app.state.operations.root.glob("*.json"):
                    assert hidden not in path.read_text()

    asyncio.run(exercise())


def test_unknown_removal_is_classified_request_refusal(configured, monkeypatch):
    server, lock, headers, _, _ = configured
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                base = (await client.get("/api/v1/config", headers=headers)).json()["envelope"][
                    "data"
                ]["base_revision"]
                reply = await client.post(
                    "/api/v1/config/validate",
                    headers=headers,
                    json={
                        "managed": {
                            "base_revision": base,
                            "edits": [
                                {
                                    "kind": "repository-remove",
                                    "repository_type": "dataset",
                                    "repository_id": "example/missing",
                                }
                            ],
                        }
                    },
                )
                assert reply.status_code == 422
                assert app.state.operations.list() == ()

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "fault", ["transport", "archive", "base", "candidate", "projection", "scope", "read-schema"]
)
def test_malformed_private_helper_results_refuse_without_echo(configured, monkeypatch, fault):
    server, lock, headers, _, _ = configured
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)
    original = helper.config_prepare
    marker = "private-unregistered-configuration-marker"

    def altered(body):
        if fault == "transport":
            raise OSError(marker)
        result = original(body)
        if fault == "archive":
            result["archive_id"] = "f40a6db6-8509-4a36-8523-97f980d06e7d"
        elif fault == "base":
            result["base_revision"] = "f" * 64
        elif fault == "candidate":
            result["candidate"] = marker + " not valid TOML"
        elif fault == "projection":
            result["editable"]["sync"]["max_workers"] = 8
        elif fault == "scope":
            result["required_selectors"] = ["../" + marker]
        return result

    monkeypatch.setattr(helper, "config_prepare", altered)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                assert read.status_code == 200
                base = read.json()["envelope"]["data"]["base_revision"]
                if fault == "read-schema":

                    async def malformed_read(_body=None):
                        return {"unexpected": marker}

                    monkeypatch.setattr(helper, "async_config_read", malformed_read)
                    response = await client.get("/api/v1/config", headers=headers)
                else:
                    response = await client.post(
                        "/api/v1/config/validate", json=_settings(base), headers=headers
                    )
                assert response.status_code == 503
                assert marker not in response.text
                assert app.state.operations.list() == ()

    asyncio.run(exercise())


def test_configuration_permission_refusal_precedes_projection_in_bound_read(
    configured, monkeypatch
):
    server, lock, headers, _, _ = configured
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)
    helper.value = status(denied={"configuration"})
    monkeypatch.setattr(
        host_policy,
        "parse_configuration",
        lambda _body: pytest.fail("Denied configuration must not be projected"),
    )

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                response = await client.get("/api/v1/config", headers=headers)
                assert response.status_code == 403
                assert helper.read_calls == 1
                assert helper.prepare_calls == helper.async_calls == 0

    asyncio.run(exercise())


@pytest.mark.parametrize(
    ("fault", "denied", "expected"),
    [
        ("archive_id", False, 503),
        ("archive_id", True, 403),
        ("archive_root", False, 503),
        ("archive_root", True, 403),
        ("unavailable", True, 503),
    ],
)
def test_bound_configuration_read_preserves_authority_refusal_order(
    configured, monkeypatch, fault, denied, expected
):
    server, lock, headers, _, _ = configured
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)
    helper.value = cast("dict[str, Any]", status(denied={"configuration"} if denied else ()))
    if fault == "unavailable":
        helper.value = unavailable_host_status().model_dump(mode="json")
    HostStatus.model_validate(helper.value)
    monkeypatch.setattr(
        host_policy, "parse_configuration", lambda _body: pytest.fail("refused binding projected")
    )

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            # Keep helper status coherent; only the independent caller's expected tuple differs.
            if fault == "archive_id":
                app.state.policy = replace(
                    app.state.policy, archive_id="00000000-0000-0000-0000-000000000000"
                )
            elif fault == "archive_root":
                app.state.policy = replace(
                    app.state.policy,
                    root=app.state.policy.root.with_name("comparison-only-must-not-be-read"),
                )
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                response = await client.get("/api/v1/config", headers=headers)
                assert response.status_code == expected
                assert response.json()["code"] == ("HFAPI002" if expected == 403 else "HFAPI022")
                assert helper.read_calls == 1
                assert helper.async_calls == 0
                assert helper.read_requests == [
                    {
                        "expected_archive_id": app.state.policy.archive_id,
                        "expected_archive_root": str(app.state.policy.root),
                    }
                ]
                assert app.state.operations.list() == ()

    asyncio.run(exercise())


@pytest.mark.parametrize("value", [None, 7, {"private-marker": "invalid"}])
def test_managed_presence_requires_admin_before_typed_body(configured, monkeypatch, value):
    server, lock, _, token, _ = configured
    helper = ConfigurationAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                for route in ("/api/v1/plans", "/api/v1/config/validate"):
                    response = await client.post(
                        route,
                        json={"managed": value},
                        headers={"Authorization": "Bearer " + token},
                    )
                    assert response.status_code == 403
                    assert "private-marker" not in response.text
                assert helper.prepare_calls == helper.async_calls == 0

    asyncio.run(exercise())
