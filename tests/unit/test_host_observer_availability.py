"""Independent host capabilities at model, protected-reader and actual ASGI seams.

The helper and manager inputs are declared unit fixtures. These checks do not
establish that an installed native observer has the required MAC confinement.
"""

import asyncio
import copy

import pytest

from hfcache import host_policy
from hfcache.api.host_routes import OBSERVER_STOPS, SCHEDULE_CHANGES
from hfcache.host_actions_models import HostObserverStatus, ScheduleValidation
from hfcache.host_models import HostStatus
from tests.fixtures.examples import ARCHIVE_ID
from tests.unit.test_host_fixed_routes import EXPECTED, REVISION, SourceHelper, exercise
from tests.unit.test_host_policy import native as native  # noqa: PLC0414 - protected-tree fixture

pytest_plugins = ("tests.unit.test_host_action_routes",)


class ScheduleOnlyHelper(SourceHelper):
    """Identity observation succeeds; the optional stop authority is unproved."""

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.validations = []
        self.stops = []

    def observer_status(self):
        value = super().observer_status()
        value.update(state=self.state, expected=EXPECTED if self.state == "observed" else None)
        value["permissions"]["observer"] = False
        value["permission_reasons"]["observer"] = "profile-unproved"
        return HostObserverStatus.model_validate(value).model_dump(mode="json")

    async def async_schedule_validate(self, body):
        self.validations.append(copy.deepcopy(body))
        return ScheduleValidation.model_validate(
            {
                "schema_version": 1,
                "archive_id": ARCHIVE_ID,
                **body,
                "normalized_on_calendar": "*-*-* 00:00:00",
                "normalized_randomized_delay_sec": "1s",
                "next_elapse": None,
            }
        ).model_dump(mode="json")

    def observer_stop(self, frame):
        self.stops.append(copy.deepcopy(frame))
        pytest.fail("observer-denied action reached the external helper")


@pytest.mark.parametrize("state", ["observed", "inactive"])
def test_observer_identity_and_schedule_grant_do_not_require_stop_authority(state):
    value = HostObserverStatus.model_validate(ScheduleOnlyHelper(state).observer_status())
    assert value.state == state
    assert value.reason is None
    assert (value.expected is not None) == (state == "observed")
    assert value.permissions.schedule
    assert not value.permissions.observer
    assert value.permission_reasons.schedule == "granted"
    assert value.permission_reasons.observer == "profile-unproved"


@pytest.mark.parametrize("state", ["observed", "inactive"])
def test_asgi_schedule_remains_usable_but_unproved_stop_has_no_admission_or_transmission(
    configured, state
):
    helper = ScheduleOnlyHelper(state)

    async def run(app, client, headers, _token):
        observed = await client.get("/api/v1/host/sync-observer", headers=headers)
        assert observed.status_code == 200
        status = HostObserverStatus.model_validate(observed.json()["envelope"]["data"])
        assert status.state == state
        assert status.permissions.schedule
        assert not status.permissions.observer

        denied = await client.post(
            OBSERVER_STOPS,
            json={"expected": EXPECTED},
            headers=headers | {"Idempotency-Key": "unproved-observer-stop"},
        )
        assert denied.status_code == 403
        assert denied.json()["code"] == "HFAPI002"
        assert app.state.operations.list() == ()
        assert helper.stops == []

        body = {"on_calendar": "daily", "randomized_delay_sec": "1s"}
        validated = await client.post(
            "/api/v1/host/sync-schedule/validations", json=body, headers=headers
        )
        assert validated.status_code == 200
        assert validated.json()["config_fingerprint"] is None
        assert validated.json()["envelope"]["data"]["normalized_randomized_delay_sec"] == "1s"
        assert helper.validations == [body]
        assert app.state.operations.list() == ()

        accepted = await client.post(
            SCHEDULE_CHANGES,
            json={"action": "pause", "expected_revision": REVISION},
            headers=headers | {"Idempotency-Key": "independent-schedule"},
        )
        assert accepted.status_code == 202
        identifier = accepted.json()["operation"]["operation_id"]
        result = await asyncio.to_thread(app.state.host_runner.wait, identifier, timeout=5)
        assert result.exit_code == 0
        assert result.data["state"] == "confirmed"
        assert len(helper.effects) == 1
        assert helper.effects[0]["operation_id"] == identifier
        assert helper.stops == []
        assert {row.route for row in app.state.operations.list()} == {SCHEDULE_CHANGES}

    exercise(configured, helper, run)


def test_legacy_status_keeps_schedule_available_but_denies_observer_without_optional_context(
    native, monkeypatch
):
    # Isolate the new independent observer proof from the host-actions receipt
    # proof. The optional indexed context binding is genuinely absent from this
    # original protected-tree fixture; no live MAC condition is simulated.
    snapshot = host_policy.inspect_authority()
    assert host_policy.SYNC_OBSERVER_BINDING not in snapshot.deployment["bindings"]
    monkeypatch.setattr(host_policy, "require_host_actions", lambda _snapshot: None)
    value = HostStatus.model_validate(snapshot.status())
    assert value.state == "supported"
    assert value.permissions.schedule
    assert not value.permissions.observer
    assert value.permission_reasons.observer == "profile-unproved"
    assert value.permissions.configuration
