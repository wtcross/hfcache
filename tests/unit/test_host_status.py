"""Actual ASGI administrative read with classified source-only helper fixtures.

These tests establish API boundary/lifecycle behavior, never installed peer,
Caddy, container or storage conformance.
"""

import asyncio
import copy
import threading

import httpx
import pytest

from hfcache.api.host_status import UnavailableHostHelper, open_host_helper
from hfcache.errors import HostAdministrationUnavailableError
from hfcache.host_models import HostStatus
from hfcache.host_protocol import HostProtocolError
from tests.fixtures.examples import ARCHIVE_ID
from tests.fixtures.host_examples import host_status
from tests.intent_fixtures import create_app

pytest_plugins = ("tests.unit.test_host_action_routes",)


class ReadClient:
    def __init__(self, value=None, *, closed=True):
        self.value = value if value is not None else host_status().model_dump(mode="json")
        if isinstance(self.value, dict) and self.value.get("binding") is not None:
            self.value["binding"]["archive_id"] = ARCHIVE_ID
        self.calls = 0
        self.closes = 0
        self.closed = closed

    def status(self):
        self.calls += 1
        if isinstance(self.value, Exception):
            raise self.value
        return copy.deepcopy(self.value)

    async def async_status(self):
        return self.status()

    def close(self, *, timeout=24):
        self.closes += 1
        return self.closed


def exercise(configured, helper, action):
    server, lock, headers, token, _ = configured

    async def run():
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            await action(app, client, headers, token)
        assert app.state.host_helper is None

    asyncio.run(run())


def test_host_status_requires_admin_before_helper_and_preserves_old_bearer(configured):
    helper = ReadClient()

    async def action(app, client, headers, token):
        missing = await client.get("/api/v1/host/status")
        assert missing.status_code == 401
        bearer = await client.get(
            "/api/v1/host/status", headers={"Authorization": "Bearer " + token}
        )
        assert bearer.status_code == 403
        query = await client.get("/api/v1/host/status?unit=arbitrary.service", headers=headers)
        assert query.status_code == 422
        assert helper.calls == 0
        observed = await client.get("/api/v1/host/status", headers=headers)
        assert observed.status_code == 200
        body = observed.json()
        assert body["envelope"]["command"] == "host status"
        assert body["archive_id"] == ARCHIVE_ID
        assert body["config_fingerprint"] is None
        status = HostStatus.model_validate(body["envelope"]["data"])
        assert status.permissions.configuration is True
        assert not status.permissions.archive
        assert status.facts is not None
        assert status.facts.guard == "absent"
        assert helper.calls == 1
        assert app.state.pool.inflight == 0
        assert not app.state.operations.list()
        assert (
            await client.get("/api/v1/version", headers={"Authorization": "Bearer " + token})
        ).status_code == 200

    exercise(configured, helper, action)
    assert helper.closes == 1


@pytest.mark.parametrize(
    ("failure", "reason"),
    [
        (HostProtocolError("timeout"), "helper-timeout"),
        (HostProtocolError("busy"), "helper-busy"),
        (HostProtocolError("peer-refused"), "helper-refused"),
        (OSError("private unit-only exception sentinel"), "helper-unavailable"),
        (RuntimeError("private unit-only exception sentinel"), "helper-unavailable"),
        ({"schema_version": 2, "secret": "private unit-only exception sentinel"}, "helper-refused"),
    ],
)
def test_bad_helper_is_explicit_unavailable_and_never_claims_api_crash(configured, failure, reason):
    helper = ReadClient(failure)

    async def action(_app, client, headers, _token):
        result = await client.get("/api/v1/host/status", headers=headers)
        assert result.status_code == 200
        status = HostStatus.model_validate(result.json()["envelope"]["data"])
        assert status.state == "unavailable"
        assert status.reason == reason
        assert not any(status.permissions.model_dump().values())
        assert status.binding is status.facts is None
        assert "private unit-only" not in result.text
        assert (await client.get("/api/v1/version", headers=headers)).status_code == 200

    exercise(configured, helper, action)


def test_helper_archive_mismatch_cannot_change_api_authority(configured):
    helper = ReadClient()
    helper.value["binding"]["archive_id"] = "01234567-89ab-cdef-0123-456789abcdef"
    assert helper.value["binding"]["archive_id"] != ARCHIVE_ID

    async def action(_app, client, headers, _token):
        result = await client.get("/api/v1/host/status", headers=headers)
        status = HostStatus.model_validate(result.json()["envelope"]["data"])
        assert result.json()["archive_id"] == ARCHIVE_ID
        assert status.reason == "deployment-unverified"
        assert status.binding is None
        assert not any(status.permissions.model_dump().values())

    exercise(configured, helper, action)


def test_disabled_helper_has_no_endpoint_or_filesystem_work(configured, monkeypatch):
    server, _, _, _, _ = configured

    def forbidden(*_args, **_kwargs):
        pytest.fail("disabled helper touched endpoint")

    monkeypatch.setattr("hfcache.host_helper_client.EndpointBinding.from_startup", forbidden)
    helper = open_host_helper(server)
    assert isinstance(helper, UnavailableHostHelper)
    status = HostStatus.model_validate(helper.status())
    assert status.reason == "helper-disabled"
    assert helper.close() is True


def test_blocked_host_read_does_not_own_metadata_pool_store_or_runner(configured):
    helper = ReadClient()

    async def run():
        entered, release = asyncio.Event(), asyncio.Event()

        async def waiting():
            entered.set()
            await release.wait()
            return helper.status()

        helper.async_status = waiting
        server, lock, headers, _, _ = configured
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            pending = asyncio.create_task(client.get("/api/v1/host/status", headers=headers))
            try:
                await asyncio.wait_for(entered.wait(), timeout=3)
                assert app.state.pool.inflight == 0
                assert not app.state.operations.list()
                assert app.state.runner.active_operation_id is None
                assert (await client.get("/api/v1/operations", headers=headers)).status_code == 200
            finally:
                release.set()
            assert (await pending).status_code == 200

    asyncio.run(run())
    assert helper.closes == 1


def test_lifespan_cancellation_waits_for_actual_helper_close(configured):
    entered, release = threading.Event(), threading.Event()
    helper = ReadClient()

    def close(*, timeout=24):
        entered.set()
        assert release.wait(timeout)
        helper.closes += 1
        return True

    helper.close = close

    async def run():
        server, lock, _, _, _ = configured
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        started, leave = asyncio.Event(), asyncio.Event()

        async def owner():
            async with app.router.lifespan_context(app):
                started.set()
                await leave.wait()

        task = asyncio.create_task(owner())
        try:
            await asyncio.wait_for(started.wait(), timeout=3)
            leave.set()
            assert await asyncio.to_thread(entered.wait, 3)
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done()
            assert helper.closes == 0
        finally:
            release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert helper.closes == 1
        assert app.state.host_helper is helper

    asyncio.run(run())


def test_lifespan_unknown_helper_drain_is_not_reported_closed(configured):
    server, lock, _, _, _ = configured
    helper = ReadClient(closed=False)
    app = create_app(server, instance_lock_path=lock, host_helper=helper)

    async def run():
        with pytest.raises(HostAdministrationUnavailableError):
            async with app.router.lifespan_context(app):
                pass
        assert helper.closes == 1
        assert app.state.host_helper is helper

    asyncio.run(run())
