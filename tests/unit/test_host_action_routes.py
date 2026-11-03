"""Actual Basic HTTP admission with unit helper status fakes (decision150).

No archive filesystem, Hub, privileged helper or installed support is exercised.
"""

import asyncio
import base64
import secrets

import httpx
import pytest

from hfcache.api.basic import create_administrator_record
from hfcache.logging import reset as reset_logging
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.commands import CommandServices
from hfcache.services.context import ServiceResult
from tests.fixtures import examples
from tests.intent_fixtures import create_app
from tests.unit.test_host_authorization import StatusClient, status

ORIGIN = "https://testserver"


@pytest.fixture(scope="module")
def administrator():
    password = secrets.token_urlsafe(32).encode()
    return create_administrator_record("host-admin", "administrator", password), password


@pytest.fixture
def configured(tmp_path, administrator, monkeypatch):
    # A test's ASGI daemon configures process-wide logging for its lifetime.
    # Isolate the shared fixture so later CLI help invocations remain separate
    # process-startup simulations; the daemon's reconfiguration guard stays real.
    reset_logging()
    record, password = administrator
    account = tmp_path / "administrator.json"
    account.write_text(record.model_dump_json())
    account.chmod(0o600)
    writer = tmp_path / "writer"
    token = secrets.token_urlsafe(48)
    writer.write_text(token)
    writer.chmod(0o600)
    policy = tmp_path / "archive.toml"
    policy.write_text(
        'schema_version=1\n[storage]\narchive_root="/srv/hfcache"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n'
    )
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(policy),
            "state_directory": str(tmp_path / "operations"),
            "credentials": {"writer": {"file": str(writer)}},
            "listener": {"allowed_hosts": ["testserver"], "allowed_origins": [ORIGIN]},
            "basic": {"origin": ORIGIN, "administrator": {"file": str(account)}},
        }
    )
    executed = []

    def plan(*_):
        executed.append(True)
        return ServiceResult("plan", {})

    monkeypatch.setattr(CommandServices, "plan_sync", plan)
    authorization = "Basic " + base64.b64encode(b"administrator:" + password).decode()
    headers = {"Authorization": authorization, "Origin": ORIGIN, "X-Hfcache-Request": "1"}
    yield server, tmp_path / "daemon.lock", headers, token, executed
    reset_logging()


def test_basic_http_duplicate_preserves_original_admission_and_lookup_result(configured):
    server, lock, headers, _, executed = configured
    helper = StatusClient()

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=ORIGIN
            ) as client:
                keyed = headers | {"Idempotency-Key": "retained-basic-operation"}
                first = await client.post("/api/v1/plans", json={}, headers=keyed)
                assert first.status_code == 202
                identity = first.json()["operation"]["operation_id"]
                await asyncio.to_thread(app.state.runner.wait, identity, timeout=3)
                duplicate = await client.post("/api/v1/plans", json={}, headers=keyed)
                assert duplicate.status_code == 202
                assert duplicate.json()["created"] is False
                helper.value = status(denied={"hub"})
                denied = await client.post("/api/v1/plans", json={}, headers=keyed)
                assert denied.status_code == 202
                assert denied.json()["operation"]["operation_id"] == identity
                assert helper.async_calls == 1
                assert executed == [True]
                helper.value = OSError("unit-only unavailable detail")
                unavailable = await client.post("/api/v1/plans", json={}, headers=keyed)
                assert unavailable.status_code == 202
                assert unavailable.json()["operation"]["operation_id"] == identity
                assert "unit-only" not in unavailable.text
                for path in (
                    "/api/v1/operations/lookup",
                    f"/api/v1/operations/{identity}",
                    f"/api/v1/operations/{identity}/result",
                ):
                    observed = await client.get(path, headers=keyed)
                    assert observed.status_code == 200
                assert helper.async_calls == 1

    asyncio.run(exercise())


def test_helper_wait_charges_intent_metadata_before_atomic_receipt(configured):
    server, lock, headers, _, executed = configured

    async def exercise():
        entered, release = asyncio.Event(), asyncio.Event()

        class BlockingStatus(StatusClient):
            async def async_status(self):
                entered.set()
                await release.wait()
                return await super().async_status()

        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = BlockingStatus()
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=ORIGIN
            ) as client:
                pending = asyncio.create_task(
                    client.post(
                        "/api/v1/plans",
                        json={},
                        headers=headers | {"Idempotency-Key": "blocked-admission"},
                    )
                )
                try:
                    await asyncio.wait_for(entered.wait(), timeout=3)
                    assert app.state.pool.inflight == 1
                    assert app.state.operations.list() == ()
                    assert executed == []
                    read = await client.get("/api/v1/capabilities", headers=headers)
                    assert read.status_code == 200
                finally:
                    release.set()
                accepted = await pending
                assert accepted.status_code == 202

    asyncio.run(exercise())


def test_bearer_post_keeps_existing_workflow_with_helper_unavailable(configured):
    server, lock, _, token, executed = configured
    helper = StatusClient(RuntimeError("bearer must never consult helper"))

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=ORIGIN
            ) as client:
                first = await client.post(
                    "/api/v1/plans",
                    json={},
                    headers={"Authorization": "Bearer " + token, "Idempotency-Key": "old-bearer"},
                )
                assert first.status_code == 202
                await asyncio.to_thread(
                    app.state.runner.wait, first.json()["operation"]["operation_id"], timeout=3
                )
                assert executed == [True]
                assert helper.async_calls == helper.sync_calls == 0

    asyncio.run(exercise())


def test_every_basic_keyed_route_denies_before_domain_work_and_persists_fence(
    configured, monkeypatch
):
    server, lock, headers, _, _ = configured
    server = server.model_copy(update={"maintenance_enabled": True})
    helper = StatusClient(status(denied={"archive", "hub", "control"}))

    def forbidden(*_args, **_kwargs):
        pytest.fail("denied action reached domain or verifier work")

    for name in (
        "plan_sync",
        "synchronize",
        "diagnose",
        "prune",
        "purge",
        "recover",
        "quarantine",
        "repair",
        "initialize_archive",
        "refresh_catalog",
    ):
        monkeypatch.setattr(CommandServices, name, forbidden)

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            monkeypatch.setattr(app.state.verifier, "check_available", forbidden)
            monkeypatch.setattr(app.state.verifier, "execute", forbidden)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=ORIGIN
            ) as client:
                rows = [
                    ("plans", {}),
                    ("syncs", {}),
                    ("verifications", {"mode": "full"}),
                    ("diagnostics", {"read_only": True}),
                    ("diagnostics", {"read_only": False}),
                    ("repairs", {"revision": "model:org/model@" + "a" * 40}),
                    ("prune-plans", {}),
                    ("prunes", {}),
                    ("purge-plans", {"all_unmanaged": True}),
                    ("purges", {"all_unmanaged": True}),
                    ("recovery-plans", {}),
                    ("recoveries", {}),
                    ("quarantine-plans", {"transaction_ids": ["a" * 32]}),
                    ("quarantine-cleanups", {"transaction_ids": ["a" * 32]}),
                    ("catalog/refreshes", {}),
                    (
                        "archive/initializations",
                        {
                            "archive_root": "/srv/hfcache",
                            "archive_id": examples.ARCHIVE_ID,
                            "confirm": True,
                        },
                    ),
                ]
                for index, (route, body) in enumerate(rows):
                    response = await client.post(
                        "/api/v1/" + route,
                        json=body,
                        headers=headers | {"Idempotency-Key": f"denied-{index}"},
                    )
                    assert response.status_code == 403, (route, response.text)
                assert app.state.operations.list() == ()
                assert len(app.state.operations._intents().entries) == len(rows)
                assert helper.async_calls == len(rows) - 1
                assert helper.sync_calls == 0

    asyncio.run(exercise())


def test_basic_synchronous_configuration_validation_stays_distinct(configured):
    server, lock, headers, _, _ = configured
    helper = StatusClient(RuntimeError("configuration validation must not call helper"))

    async def exercise():
        app = create_app(server, instance_lock_path=lock)
        async with app.router.lifespan_context(app):
            app.state.host_helper = helper
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=ORIGIN
            ) as client:
                response = await client.post("/api/v1/config/validate", json={}, headers=headers)
                assert response.status_code == 200
                assert helper.async_calls == helper.sync_calls == 0
                assert app.state.operations.list() == ()

    asyncio.run(exercise())
