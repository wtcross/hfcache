"""Actual ASGI/store/runner host boundaries with a declared helper-source fixture.

These are API integration checks, not privileged helper/Caddy/platform acceptance.
"""

import asyncio
import copy

import httpx
import pytest

from hfcache.api.host_routes import OBSERVER_STOPS, SCHEDULE_CHANGES
from hfcache.errors import OperationError
from hfcache.host_actions_models import HostObserverStatus, ScheduleChangeOutcome
from tests.fixtures.examples import ARCHIVE_ID
from tests.fixtures.host_examples import host_status
from tests.intent_fixtures import create_app

pytest_plugins = ("tests.unit.test_host_action_routes",)
EXPECTED = {
    "boot_id": "cf68ba1d-153b-41bc-8f0b-b0414512dc03",
    "invocation_id": "1" * 32,
    "main_pid": 123,
    "start_ticks": 456,
}
REVISION = "a" * 64


class SourceHelper:
    """Only the external helper boundary is supplied; API authority is genuine."""

    def __init__(self, *, lose_reply=False, stale=False, revoke_dispatch=False):
        self.lose_reply = lose_reply
        self.stale = stale
        self.revoke_dispatch = revoke_dispatch
        self.allowed = True
        self.effects = []
        self.observations = []
        self.outcomes = {}
        self.closed = False

    def observer_status(self):
        source_binding = host_status().binding
        assert source_binding is not None
        binding = source_binding.model_dump(mode="json")
        binding["archive_id"] = ARCHIVE_ID
        allowed = self.allowed and not self.revoke_dispatch
        return HostObserverStatus.model_validate(
            {
                "schema_version": 1,
                "archive_id": ARCHIVE_ID,
                "profile": "native",
                "host_binding": binding,
                "permissions": {"schedule": allowed, "observer": allowed},
                "permission_reasons": {
                    "schedule": "granted" if allowed else "policy-denied",
                    "observer": "granted" if allowed else "policy-denied",
                },
                "state": "observed",
                "reason": None,
                "unit": "hfcache-sync.service",
                "expected": EXPECTED,
            }
        ).model_dump(mode="json")

    async def async_observer_status(self):
        revoke = self.revoke_dispatch
        self.revoke_dispatch = False
        try:
            return self.observer_status()
        finally:
            self.revoke_dispatch = revoke

    def schedule_change(self, frame):
        self.effects.append(copy.deepcopy(frame))
        result = {
            "schema_version": 1,
            "archive_id": ARCHIVE_ID,
            "operation_id": frame["operation_id"],
            "request_digest": frame["request_digest"],
            "state": "unchanged" if self.stale else "confirmed",
            "pending": False,
            "action": "pause",
            "expected_revision": REVISION,
            "stored_revision": "b" * 64 if self.stale else REVISION,
            "file_state": "unchanged",
            "manager_state": "not_sent" if self.stale else "timer_acknowledged",
            "timer_was_active": True,
            "timer_is_active": bool(self.stale),
        }
        self.outcomes[frame["operation_id"]] = result
        if self.lose_reply:
            message = "owned helper reply lost after original effect"
            raise OSError(message)
        return copy.deepcopy(result)

    def schedule_outcome(self, frame):
        self.observations.append(copy.deepcopy(frame))
        return copy.deepcopy(self.outcomes[frame["operation_id"]])

    def close(self, *, timeout=24):
        self.closed = True
        return True


def exercise(configured, helper, callback):
    server, lock, headers, token, _ = configured

    async def run():
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            await callback(app, client, headers, token)

    asyncio.run(run())
    assert helper.closed


def test_host_admin_authentication_precedes_body_decode_or_helper_work(configured):
    helper = SourceHelper()

    async def run(app, client, headers, token):
        for route in (SCHEDULE_CHANGES, OBSERVER_STOPS, "/api/v1/host/sync-schedule/validations"):
            response = await client.post(
                route,
                content=b"not-json",
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            )
            assert response.status_code == 403
        assert helper.effects == []
        assert app.state.operations.list() == ()
        response = await client.get("/api/v1/host/sync-observer", headers=headers)
        assert response.status_code == 200
        assert response.json()["config_fingerprint"] is None
        expected = HostObserverStatus.model_validate(response.json()["envelope"]["data"]).expected
        assert expected is not None
        assert expected.main_pid == EXPECTED["main_pid"]

    exercise(configured, helper, run)


def test_exact_duplicate_is_observe_only_and_original_outcome_read_needs_no_effect_grant(
    configured,
):
    helper = SourceHelper()

    async def run(app, client, headers, _token):
        keyed = headers | {"Idempotency-Key": "original-schedule"}
        submitted = await client.post(
            SCHEDULE_CHANGES, json={"action": "pause", "expected_revision": REVISION}, headers=keyed
        )
        assert submitted.status_code == 202
        identifier = submitted.json()["operation"]["operation_id"]
        result = await asyncio.to_thread(app.state.host_runner.wait, identifier, timeout=5)
        assert result.exit_code == 0
        duplicate = await client.post(
            SCHEDULE_CHANGES, json={"action": "pause", "expected_revision": REVISION}, headers=keyed
        )
        assert duplicate.status_code == 202
        assert duplicate.json()["created"] is False
        assert len(helper.effects) == 1
        helper.allowed = False
        outcome = await client.get(SCHEDULE_CHANGES + "/" + identifier, headers=keyed)
        assert outcome.status_code == 200
        assert (
            ScheduleChangeOutcome.model_validate(outcome.json()["envelope"]["data"]).state
            == "confirmed"
        )
        assert len(helper.effects) == 1
        assert len(helper.observations) == 1
        wrong = await client.get(
            SCHEDULE_CHANGES + "/" + identifier,
            headers=headers | {"Idempotency-Key": "another-key"},
        )
        assert wrong.status_code == 404
        assert len(helper.observations) == 1

    exercise(configured, helper, run)


def test_lost_helper_reply_keeps_original_interrupted_and_gets_confirmed_without_replay(configured):
    helper = SourceHelper(lose_reply=True)

    async def run(app, client, headers, _token):
        keyed = headers | {"Idempotency-Key": "original-lost-host"}
        submitted = await client.post(
            SCHEDULE_CHANGES, json={"action": "pause", "expected_revision": REVISION}, headers=keyed
        )
        assert submitted.status_code == 202
        identifier = submitted.json()["operation"]["operation_id"]
        with pytest.raises(OperationError):
            await asyncio.to_thread(app.state.host_runner.wait, identifier, timeout=5)
        assert app.state.operations.get(identifier).state == "interrupted"
        outcome = await client.get(SCHEDULE_CHANGES + "/" + identifier, headers=keyed)
        assert outcome.status_code == 200
        assert outcome.json()["envelope"]["data"]["state"] == "confirmed"
        duplicate = await client.post(
            SCHEDULE_CHANGES, json={"action": "pause", "expected_revision": REVISION}, headers=keyed
        )
        assert duplicate.status_code == 202
        assert duplicate.json()["created"] is False
        assert len(helper.effects) == 1
        assert app.state.operations.get(identifier).state == "interrupted"
        assert app.state.runner._accepting

    exercise(configured, helper, run)


def test_known_stale_refusal_retains_actual_revision_and_does_not_poison_host_lane(configured):
    helper = SourceHelper(stale=True)

    async def run(app, client, headers, _token):
        submitted = await client.post(
            SCHEDULE_CHANGES,
            json={"action": "pause", "expected_revision": REVISION},
            headers=headers | {"Idempotency-Key": "stale-known"},
        )
        assert submitted.status_code == 202
        identifier = submitted.json()["operation"]["operation_id"]
        result = await asyncio.to_thread(app.state.host_runner.wait, identifier, timeout=5)
        assert result.exit_code == 10
        outcome = ScheduleChangeOutcome.model_validate(result.data)
        assert outcome.state == "unchanged"
        assert outcome.stored_revision != outcome.expected_revision
        assert outcome.manager_state == "not_sent"
        assert app.state.operations.get(identifier).state == "failed"
        assert app.state.host_runner._accepting

    exercise(configured, helper, run)


def test_revoked_dispatch_grant_refuses_before_transmission_and_original_tuple_is_required(
    configured,
):
    helper = SourceHelper(revoke_dispatch=True)

    async def run(app, client, headers, _token):
        submitted = await client.post(
            SCHEDULE_CHANGES,
            json={"action": "pause", "expected_revision": REVISION},
            headers=headers | {"Idempotency-Key": "fresh-dispatch-refusal"},
        )
        assert submitted.status_code == 202
        identifier = submitted.json()["operation"]["operation_id"]
        result = await asyncio.to_thread(app.state.host_runner.wait, identifier, timeout=5)
        assert result.exit_code != 0
        assert helper.effects == []
        assert "host.transmission" not in {
            event.kind for event in app.state.operations.get(identifier).events
        }
        helper.revoke_dispatch = False
        stale = dict(EXPECTED, invocation_id="2" * 32)
        refused = await client.post(
            OBSERVER_STOPS,
            json={"expected": stale},
            headers=headers | {"Idempotency-Key": "wrong-invocation"},
        )
        assert refused.status_code == 409
        assert len(app.state.operations.list()) == 1
        assert helper.effects == []

    exercise(configured, helper, run)
