"""Real API/operation store with an owned configuration-effect adapter.

Host confinement/atomicity are tested by the real host writer and installed
functional suites. This adapter isolates API admission, original handles and
loss-of-response behavior; it establishes no installed acceptance.
"""

import asyncio
import threading

import httpx
import pytest

from hfcache.api.app import create_app
from hfcache.config import load_config
from hfcache.errors import OperationError
from hfcache.services.commands import CommandServices
from hfcache.services.context import ServiceResult
from tests.unit.test_api_managed_configuration import ConfigurationAdapter, _settings
from tests.unit.test_host_action_routes import ORIGIN
from tests.unit.test_host_action_routes import (
    administrator as administrator,  # noqa: PLC0414 - shared fixture
)
from tests.unit.test_host_action_routes import (
    configured as configured,  # noqa: PLC0414 - shared fixture
)
from tests.unit.test_host_authorization import status

ROUTE = "/api/v1/config/applications"


class EffectAdapter(ConfigurationAdapter):
    def __init__(self, path, monkeypatch):
        super().__init__(path, monkeypatch)
        self.effects = []
        self.outcomes = {}
        self.store = None
        self.lose_response = False
        self.outcome_calls = 0

    def config_apply(self, body):
        identifier = body["operation_id"]
        assert self.store is not None
        receipt = self.store.get(identifier)
        assert receipt.request_digest == body["request_digest"]
        assert any(event.kind == "configuration.transmission" for event in receipt.events)
        assert identifier not in self.outcomes, "API replayed an original apply"
        prepared = self.config_prepare(body["managed"])
        assert prepared["candidate_revision"] == body["candidate_revision"]
        assert prepared["required_selectors"] == body["required_selectors"]
        candidate = self.path.with_name(".adapter-candidate")
        candidate.write_text(prepared["candidate"])
        candidate.replace(self.path)
        assert load_config(self.path).fingerprint() == body["config_fingerprint"]
        outcome = {
            "schema_version": 1,
            "archive_id": receipt.archive_id,
            "operation_id": identifier,
            "request_digest": receipt.request_digest,
            "base_revision": body["managed"]["base_revision"],
            "candidate_revision": body["candidate_revision"],
            "config_fingerprint": body["config_fingerprint"],
            "state": "confirmed",
            "pending": False,
        }
        self.outcomes[identifier] = outcome
        self.effects.append(identifier)
        if self.lose_response:
            message = "private helper transport diagnostic"
            raise OSError(message)
        return outcome

    def config_outcome(self, body):
        self.outcome_calls += 1
        outcome = self.outcomes[body["operation_id"]]
        assert outcome["request_digest"] == body["request_digest"]
        return outcome


async def _preview(client, headers, managed, app, *, key="original-managed-preview"):
    accepted = await client.post(
        "/api/v1/plans", json=managed, headers=headers | {"Idempotency-Key": key}
    )
    assert accepted.status_code == 202, accepted.text
    identifier = accepted.json()["operation"]["operation_id"]
    result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
    assert result.exit_code == 0
    return {"operation_id": identifier, "key": key}


def test_apply_requires_exact_preview_and_duplicate_never_reprepares_changed_base(
    configured, monkeypatch
):
    server, lock, headers, _, executed = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            helper.store = app.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                base = read.json()["envelope"]["data"]["base_revision"]
                managed = _settings(base)
                preview = await _preview(client, headers, managed, app)
                body = managed | {"preview": preview}
                keyed = headers | {"Idempotency-Key": "original-application"}
                accepted = await client.post(ROUTE, json=body, headers=keyed)
                assert accepted.status_code == 202, accepted.text
                identifier = accepted.json()["operation"]["operation_id"]
                result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                assert result.exit_code == 0
                assert result.data["state"] == "confirmed"
                assert load_config(server.archive_config).sync.max_workers == 3
                before = helper.prepare_calls
                duplicate = await client.post(ROUTE, json=body, headers=keyed)
                assert duplicate.status_code == 202, duplicate.text
                assert duplicate.json()["created"] is False
                assert duplicate.json()["operation"]["operation_id"] == identifier
                assert helper.prepare_calls == before
                assert helper.effects == [identifier]
                conflict = await client.post(
                    ROUTE, json=_settings(base, workers=5) | {"preview": preview}, headers=keyed
                )
                assert conflict.status_code == 409
                helper.value = status(denied={"configuration", "hub"})
                observed = await client.get(ROUTE + "/" + identifier, headers=keyed)
                assert observed.status_code == 200
                assert observed.json()["envelope"]["data"]["state"] == "confirmed"
                wrong = await client.get(
                    ROUTE + "/" + identifier,
                    headers=headers | {"Idempotency-Key": preview["key"]},
                )
                assert wrong.status_code == 409
                assert executed == []
                text = "".join(
                    path.read_text() for path in app.state.operations.root.glob("*.json")
                )
                assert preview["key"] not in text
                assert "max_workers" not in text
                assert "schema_version =" not in text

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "fault", ["different-edit", "wrong-preview-id", "wrong-preview-key", "old-plan"]
)
def test_invalid_preview_never_reaches_effect(configured, monkeypatch, fault):
    server, lock, headers, _, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            helper.store = app.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                base = (await client.get("/api/v1/config", headers=headers)).json()["envelope"][
                    "data"
                ]["base_revision"]
                managed = _settings(base)
                preview = await _preview(client, headers, managed, app)
                if fault == "different-edit":
                    managed = _settings(base, workers=5)
                elif fault == "wrong-preview-id":
                    preview["operation_id"] = "f" * 32
                elif fault == "wrong-preview-key":
                    preview["key"] = "missing-preview-key"
                else:
                    preview = await _preview(client, headers, {}, app, key="old-installed-plan")
                before = server.archive_config.read_bytes()
                response = await client.post(
                    ROUTE,
                    json=managed | {"preview": preview},
                    headers=headers | {"Idempotency-Key": "refused-application"},
                )
                assert response.status_code in {404, 409}
                assert server.archive_config.read_bytes() == before
                assert helper.effects == []
                assert all(receipt.route != ROUTE for receipt in app.state.operations.list())

    asyncio.run(exercise())


def test_lost_helper_ack_and_api_restart_only_observe_original(configured, monkeypatch):
    server, lock, headers, _, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)
    helper.lose_response = True

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            helper.store = app.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                base = (await client.get("/api/v1/config", headers=headers)).json()["envelope"][
                    "data"
                ]["base_revision"]
                managed = _settings(base)
                body = managed | {"preview": await _preview(client, headers, managed, app)}
                keyed = headers | {"Idempotency-Key": "lost-application-ack"}
                accepted = await client.post(ROUTE, json=body, headers=keyed)
                assert accepted.status_code == 202
                identifier = accepted.json()["operation"]["operation_id"]
                with pytest.raises(OperationError):
                    await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                assert app.state.operations.get(identifier).state == "interrupted"
                assert helper.effects == [identifier]
                assert load_config(server.archive_config).sync.max_workers == 3
        restarted = create_app(server, instance_lock_path=lock)
        async with restarted.router.lifespan_context(restarted):
            restarted.state.host_helper = helper
            helper.store = restarted.state.operations
            helper.value = status(denied={"configuration", "hub"})
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(restarted), base_url=ORIGIN
            ) as client:
                observation = await client.get(ROUTE + "/" + identifier, headers=keyed)
                assert observation.status_code == 200, observation.text
                assert observation.json()["envelope"]["data"]["state"] == "confirmed"
                assert restarted.state.operations.get(identifier).state == "interrupted"
                assert helper.effects == [identifier]
                assert helper.outcome_calls == 1

    asyncio.run(exercise())


@pytest.mark.parametrize("body", [{}, {"managed": None}, {"private": "marker"}])
def test_old_bearer_refused_before_application_body_validation(configured, monkeypatch, body):
    server, lock, _, token, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                response = await client.post(
                    ROUTE,
                    json=body,
                    headers={"Authorization": "Bearer " + token, "Idempotency-Key": "no-admin"},
                )
                assert response.status_code == 403
                assert helper.read_calls == helper.prepare_calls == helper.async_calls == 0
                assert app.state.operations.list() == ()

    asyncio.run(exercise())


@pytest.mark.parametrize("drift", ["full-base", "logical-fingerprint", "permission"])
def test_queued_apply_rechecks_before_transmission(configured, monkeypatch, drift):
    server, lock, headers, _, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)
    entered, release = threading.Event(), threading.Event()

    def held_plan(*_args):
        entered.set()
        if not release.wait(timeout=5):
            raise TimeoutError
        return ServiceResult("plan", {})

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            helper.store = app.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                managed = _settings(read.json()["envelope"]["data"]["base_revision"])
                body = managed | {"preview": await _preview(client, headers, managed, app)}
                monkeypatch.setattr(CommandServices, "plan_sync", held_plan)
                held = await client.post(
                    "/api/v1/plans",
                    json={},
                    headers=headers | {"Idempotency-Key": "holding-original-plan"},
                )
                assert held.status_code == 202
                assert await asyncio.to_thread(entered.wait, 3)
                try:
                    accepted = await client.post(
                        ROUTE,
                        json=body,
                        headers=headers | {"Idempotency-Key": "queued-application"},
                    )
                    assert accepted.status_code == 202, accepted.text
                    identifier = accepted.json()["operation"]["operation_id"]
                    if drift == "permission":
                        helper.value = status(denied={"configuration"})
                    elif drift == "full-base":
                        server.archive_config.write_bytes(
                            server.archive_config.read_bytes() + b"\n# concurrent full-byte edit\n"
                        )
                    else:
                        server.archive_config.write_text(
                            server.archive_config.read_text() + "\n[sync]\nmax_workers=8\n"
                        )
                finally:
                    release.set()
                outcome = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                assert outcome.exit_code != 0
                assert helper.effects == []
                assert not any(
                    event.kind == "configuration.transmission"
                    for event in app.state.operations.get(identifier).events
                )

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "fault", ["archive", "operation", "digest", "candidate", "null-identities", "pending", "state"]
)
def test_malformed_helper_success_after_effect_stays_interrupted(configured, monkeypatch, fault):
    server, lock, headers, _, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)
    actual_apply = helper.config_apply

    def altered(body):
        outcome = dict(actual_apply(body))
        if fault == "archive":
            outcome["archive_id"] = "f40a6db6-8509-4a36-8523-97f980d06e7d"
        elif fault == "operation":
            outcome["operation_id"] = "f" * 32
        elif fault == "digest":
            outcome["request_digest"] = "f" * 64
        elif fault == "candidate":
            outcome["candidate_revision"] = "f" * 64
        elif fault == "null-identities":
            for name in ("base_revision", "candidate_revision", "config_fingerprint"):
                outcome[name] = None
        elif fault == "pending":
            outcome["pending"] = True
        else:
            outcome["state"] = "installed_unconfirmed"
        return outcome

    monkeypatch.setattr(helper, "config_apply", altered)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            helper.store = app.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                managed = _settings(read.json()["envelope"]["data"]["base_revision"])
                body = managed | {"preview": await _preview(client, headers, managed, app)}
                keyed = headers | {"Idempotency-Key": "malformed-original-application"}
                accepted = await client.post(ROUTE, json=body, headers=keyed)
                assert accepted.status_code == 202
                identifier = accepted.json()["operation"]["operation_id"]
                with pytest.raises(OperationError):
                    await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                receipt = app.state.operations.get(identifier)
                assert receipt.state == "interrupted"
                assert receipt.result is None
                assert load_config(server.archive_config).sync.max_workers == 3
                observed = await client.get(ROUTE + "/" + identifier, headers=keyed)
                assert observed.status_code == 200
                assert observed.json()["envelope"]["data"]["state"] == "confirmed"
                assert helper.effects == [identifier]

    asyncio.run(exercise())


def test_preview_reference_is_not_transferable_between_basic_subjects(
    configured, administrator, monkeypatch
):
    server, lock, headers, _, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                managed = _settings(read.json()["envelope"]["data"]["base_revision"])
                body = managed | {"preview": await _preview(client, headers, managed, app)}
        assert server.basic is not None
        path = server.basic.administrator.file
        assert path is not None
        original, _password = administrator
        replacement = original.model_copy(update={"subject": "replacement-admin"})
        path.write_text(replacement.model_dump_json())
        restarted = create_app(server, instance_lock_path=lock)
        async with restarted.router.lifespan_context(restarted):
            restarted.state.host_helper = helper
            helper.store = restarted.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(restarted), base_url=ORIGIN
            ) as client:
                response = await client.post(
                    ROUTE,
                    json=body,
                    headers=headers | {"Idempotency-Key": "different-subject-application"},
                )
                assert response.status_code == 404
                assert helper.effects == []
                assert all(record.route != ROUTE for record in restarted.state.operations.list())

    asyncio.run(exercise())


@pytest.mark.parametrize("prior", ["unknown", "pending", "missing", "confirmed"])
def test_new_apply_requires_resolved_original_host_history(configured, monkeypatch, prior):
    server, lock, headers, _, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)
    helper.lose_response = True

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            helper.store = app.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                managed = _settings(read.json()["envelope"]["data"]["base_revision"])
                body = managed | {"preview": await _preview(client, headers, managed, app)}
                accepted = await client.post(
                    ROUTE,
                    json=body,
                    headers=headers | {"Idempotency-Key": "interrupted-original-history"},
                )
                identifier = accepted.json()["operation"]["operation_id"]
                with pytest.raises(OperationError):
                    await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
        if prior == "missing":
            del helper.outcomes[identifier]
        elif prior == "pending":
            helper.outcomes[identifier]["pending"] = True
        elif prior == "unknown":
            helper.outcomes[identifier]["state"] = "unknown"
        helper.lose_response = False
        restored = create_app(server, instance_lock_path=lock)
        async with restored.router.lifespan_context(restored):
            restored.state.host_helper = helper
            helper.store = restored.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(restored), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                managed = _settings(read.json()["envelope"]["data"]["base_revision"], workers=5)
                body = managed | {
                    "preview": await _preview(
                        client, headers, managed, restored, key="fresh-preview"
                    )
                }
                response = await client.post(
                    ROUTE,
                    json=body,
                    headers=headers | {"Idempotency-Key": "fresh-application-after-restart"},
                )
                if prior == "confirmed":
                    assert response.status_code == 202, response.text
                    original = response.json()["operation"]["operation_id"]
                    result = await asyncio.to_thread(
                        restored.state.runner.wait, original, timeout=3
                    )
                    assert result.exit_code == 0
                    assert len(helper.effects) == 2
                else:
                    assert response.status_code == (503 if prior == "missing" else 409)
                    assert helper.effects == [identifier]
                    assert sum(r.route == ROUTE for r in restored.state.operations.list()) == 1
                assert helper.outcome_calls == 1

    asyncio.run(exercise())


def test_active_application_blocks_second_apply_without_holding_store_lock(configured, monkeypatch):
    server, lock, headers, _, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    actual_apply = helper.config_apply

    def held(body):
        entered.set()
        if not release.wait(timeout=5):
            raise TimeoutError
        return actual_apply(body)

    monkeypatch.setattr(helper, "config_apply", held)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            helper.store = app.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                managed = _settings(read.json()["envelope"]["data"]["base_revision"])
                body = managed | {"preview": await _preview(client, headers, managed, app)}
                first = await client.post(
                    ROUTE, json=body, headers=headers | {"Idempotency-Key": "active-first-apply"}
                )
                assert first.status_code == 202
                identifier = first.json()["operation"]["operation_id"]
                assert await asyncio.to_thread(entered.wait, 3)
                try:
                    refused = await client.post(
                        ROUTE,
                        json=body,
                        headers=headers | {"Idempotency-Key": "active-second-apply"},
                    )
                    assert refused.status_code == 409
                    assert helper.outcome_calls == 0
                finally:
                    release.set()
                result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                assert result.exit_code == 0
                assert helper.effects == [identifier]

    asyncio.run(exercise())


@pytest.mark.parametrize("fault", ["schema", "archive", "operation", "digest", "transport"])
def test_original_outcome_read_refuses_private_corruption_without_echo(
    configured, monkeypatch, fault
):
    server, lock, headers, _, _ = configured
    helper = EffectAdapter(server.archive_config, monkeypatch)
    actual_outcome = helper.config_outcome
    private = "private-unregistered-helper-outcome-detail"

    def altered(body):
        if fault == "transport":
            raise OSError(private)
        outcome = dict(actual_outcome(body))
        if fault == "schema":
            outcome["private"] = private
        elif fault == "archive":
            outcome["archive_id"] = "f40a6db6-8509-4a36-8523-97f980d06e7d"
        elif fault == "operation":
            outcome["operation_id"] = "f" * 32
        else:
            outcome["request_digest"] = "f" * 64
        return outcome

    monkeypatch.setattr(helper, "config_outcome", altered)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            helper.store = app.state.operations
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url=ORIGIN
            ) as client:
                read = await client.get("/api/v1/config", headers=headers)
                managed = _settings(read.json()["envelope"]["data"]["base_revision"])
                body = managed | {"preview": await _preview(client, headers, managed, app)}
                keyed = headers | {"Idempotency-Key": "read-private-original"}
                accepted = await client.post(ROUTE, json=body, headers=keyed)
                identifier = accepted.json()["operation"]["operation_id"]
                result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                assert result.exit_code == 0
                observed = await client.get(ROUTE + "/" + identifier, headers=keyed)
                assert observed.status_code == 503
                assert private not in observed.text
                assert helper.effects == [identifier]

    asyncio.run(exercise())
