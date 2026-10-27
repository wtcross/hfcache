"""Strict host DTOs prove bounded evidence, not native systemd acceptance."""

import json

import pytest
from pydantic import ValidationError

from hfcache.host_actions_models import (
    HostJournalEntry,
    HostJournalPage,
    HostObserverStatus,
    JournalQuery,
    ObserverExpected,
    ObserverStopOutcome,
    ObserverStopRequest,
    ScheduleChangeOutcome,
    ScheduleChangeRequest,
    ScheduleValidation,
    ScheduleValidationRequest,
)

ARCHIVE = "66cebdbf-a04b-4a55-bf19-010de9a2eb51"
EXPECTED = {"boot_id": ARCHIVE, "invocation_id": "1" * 32, "main_pid": 432, "start_ticks": 1234}
IDENTITY = {
    "schema_version": 1,
    "archive_id": ARCHIVE,
    "operation_id": "2" * 32,
    "request_digest": "3" * 64,
}
BINDING = {
    "deployment_sha256": "4" * 64,
    "policy_sha256": "5" * 64,
    "release_version": "0.2.2",
    "source_commit": "6" * 40,
    "source_snapshot_sha256": "7" * 64,
    "source_dirty": False,
    "archive_id": ARCHIVE,
    "archive_root": "/srv/hfcache",
}


def observer_status():
    return {
        "schema_version": 1,
        "archive_id": ARCHIVE,
        "profile": "native",
        "host_binding": BINDING,
        "permissions": {"schedule": True, "observer": True},
        "permission_reasons": {"schedule": "granted", "observer": "granted"},
        "state": "observed",
        "reason": None,
        "unit": "hfcache-sync.service",
        "expected": EXPECTED,
    }


def schedule_outcome():
    return IDENTITY | {
        "state": "confirmed",
        "pending": False,
        "action": "replace",
        "expected_revision": "8" * 64,
        "stored_revision": "9" * 64,
        "file_state": "installed",
        "manager_state": "reload_acknowledged",
        "timer_was_active": False,
        "timer_is_active": False,
    }


def journal_page():
    return {
        "schema_version": 1,
        "archive_id": ARCHIVE,
        "source": "sync-observer",
        "entries": [
            {
                "at": "2026-10-27T04:00:00Z",
                "message": "event=run.started level=info run_id=" + "a" * 32,
            }
        ],
        "next_cursor": None,
        "gap": False,
        "truncated": False,
    }


@pytest.mark.parametrize("action", ["pause", "resume", "reset"])
def test_nonreplacement_has_exact_original_two_field_body(action):
    body = {"action": action, "expected_revision": "a" * 64}
    assert ScheduleChangeRequest.model_validate(body).canonical_body() == body
    with pytest.raises(ValidationError):
        ScheduleChangeRequest.model_validate(body | {"on_calendar": None})
    with pytest.raises(ValidationError):
        ScheduleChangeRequest.model_validate(body | {"randomized_delay_sec": None})


def test_replace_preserves_required_null_and_never_accepts_omitted_calendar_or_delay():
    body = {
        "action": "replace",
        "expected_revision": "a" * 64,
        "on_calendar": "daily",
        "randomized_delay_sec": None,
    }
    assert ScheduleChangeRequest.model_validate(body).canonical_body() == body
    for field in ("on_calendar", "randomized_delay_sec"):
        with pytest.raises(ValidationError):
            ScheduleChangeRequest.model_validate({k: v for k, v in body.items() if k != field})
    with pytest.raises(ValidationError):
        ScheduleChangeRequest.model_validate(body | {"unit": "hfcache.target"})


@pytest.mark.parametrize(
    "value", ["", "  ", "daily\n[Service]", "daily\\x", "x\0", "雪", "x" * 4097]
)
def test_unsafe_or_unbounded_calendar_is_refused_before_tool(value):
    with pytest.raises(ValidationError):
        ScheduleValidationRequest(on_calendar=value, randomized_delay_sec=None)


def test_validation_bounds_and_delay_normalization_remain_actual_separate_evidence():
    request = ScheduleValidationRequest(on_calendar="x" * 4096, randomized_delay_sec="x" * 256)
    assert len(request.on_calendar) == 4096
    body = {
        "schema_version": 1,
        "archive_id": ARCHIVE,
        "on_calendar": "daily",
        "randomized_delay_sec": None,
        "normalized_on_calendar": "*-*-* 00:00:00",
        "normalized_randomized_delay_sec": None,
        "next_elapse": None,
    }
    assert ScheduleValidation.model_validate(body).normalized_on_calendar == "*-*-* 00:00:00"
    with pytest.raises(ValidationError):
        ScheduleValidation.model_validate(body | {"normalized_randomized_delay_sec": "1s"})
    with pytest.raises(ValidationError):
        ScheduleValidationRequest(on_calendar="daily", randomized_delay_sec="x" * 257)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("main_pid", True),
        ("main_pid", 1),
        ("start_ticks", 0),
        ("start_ticks", 9007199254740992),
        ("boot_id", ARCHIVE.upper()),
    ],
)
def test_original_observer_tuple_has_strict_safe_identity(field, value):
    with pytest.raises(ValidationError):
        ObserverExpected.model_validate(EXPECTED | {field: value})


def test_observer_request_has_only_expected_tuple_and_no_process_or_manager_selector():
    assert ObserverStopRequest(
        expected=ObserverExpected.model_validate(EXPECTED)
    ).canonical_body() == {"expected": EXPECTED}
    for extra in ({"pid": 432}, {"unit": "hfcache-sync.service"}, {"manager": "user"}):
        with pytest.raises(ValidationError):
            ObserverStopRequest.model_validate({"expected": EXPECTED} | extra)


def test_new_observer_authority_keeps_inactive_and_guarded_rootless_honest():
    value = observer_status()
    assert HostObserverStatus.model_validate(value).expected is not None
    assert (
        HostObserverStatus.model_validate(value | {"state": "inactive", "expected": None}).expected
        is None
    )
    rootless = value | {
        "profile": "rootless",
        "state": "unavailable",
        "reason": "profile-unproved",
        "expected": None,
        "permissions": {"schedule": False, "observer": False},
        "permission_reasons": {"schedule": "profile-unproved", "observer": "profile-unproved"},
    }
    assert HostObserverStatus.model_validate(rootless).host_binding is not None
    with pytest.raises(ValidationError):
        HostObserverStatus.model_validate(
            rootless | {"permissions": {"schedule": True, "observer": False}}
        )


@pytest.mark.parametrize(
    "change",
    [
        {"state": "inactive"},
        {"reason": "facts-unavailable"},
        {"profile": None},
        {"host_binding": BINDING | {"archive_id": "00000000-0000-0000-0000-000000000000"}},
        {"permissions": {"schedule": False, "observer": True}},
        {"unit": "hfcache.target"},
    ],
)
def test_partial_or_conflicting_observer_authority_never_grants(change):
    with pytest.raises(ValidationError):
        HostObserverStatus.model_validate(observer_status() | change)


def test_schedule_confirmation_separates_file_publication_and_manager_acknowledgement():
    body = schedule_outcome()
    assert ScheduleChangeOutcome.model_validate(body).manager_state == "reload_acknowledged"
    assert ScheduleChangeOutcome.model_validate(body | {"pending": True}).pending is True
    with pytest.raises(ValidationError):
        ScheduleChangeOutcome.model_validate(body | {"manager_state": "not_sent"})
    with pytest.raises(ValidationError):
        ScheduleChangeOutcome.model_validate(body | {"timer_is_active": True})
    active = body | {
        "manager_state": "timer_acknowledged",
        "timer_was_active": True,
        "timer_is_active": True,
    }
    assert ScheduleChangeOutcome.model_validate(active).timer_is_active
    with pytest.raises(ValidationError):
        ScheduleChangeOutcome.model_validate(active | {"manager_state": "reload_acknowledged"})


@pytest.mark.parametrize(("action", "active"), [("pause", False), ("resume", True)])
def test_activation_only_confirmation_cannot_claim_changed_schedule_file(action, active):
    body = schedule_outcome() | {
        "action": action,
        "stored_revision": "8" * 64,
        "file_state": "unchanged",
        "manager_state": "timer_acknowledged",
        "timer_is_active": active,
    }
    assert ScheduleChangeOutcome.model_validate(body).action == action
    for change in (
        {"stored_revision": "9" * 64},
        {"file_state": "installed"},
        {"timer_is_active": not active},
    ):
        with pytest.raises(ValidationError):
            ScheduleChangeOutcome.model_validate(body | change)


def test_unknown_and_prepared_schedule_outcomes_never_fabricate_confirmation():
    unknown = IDENTITY | {
        "state": "unknown",
        "pending": False,
        "action": None,
        "expected_revision": None,
        "stored_revision": None,
        "file_state": "unknown",
        "manager_state": "unknown",
        "timer_was_active": None,
        "timer_is_active": None,
    }
    assert ScheduleChangeOutcome.model_validate(unknown).action is None
    with pytest.raises(ValidationError):
        ScheduleChangeOutcome.model_validate(unknown | {"state": "confirmed"})
    prepared = schedule_outcome() | {
        "state": "prepared",
        "pending": True,
        "file_state": "unchanged",
        "stored_revision": "8" * 64,
        "manager_state": "not_sent",
    }
    assert ScheduleChangeOutcome.model_validate(prepared).state == "prepared"
    with pytest.raises(ValidationError):
        ScheduleChangeOutcome.model_validate(prepared | {"pending": False})


def test_stale_revision_refusal_can_record_known_no_effect_without_claiming_original_file():
    unchanged = schedule_outcome() | {
        "state": "unchanged",
        "pending": False,
        "file_state": "unchanged",
        "manager_state": "not_sent",
        "stored_revision": "9" * 64,
    }
    assert ScheduleChangeOutcome.model_validate(unchanged).stored_revision == "9" * 64
    for patch in (
        {"pending": True},
        {"timer_is_active": True},
        {"timer_was_active": None},
        {"manager_state": "reload_acknowledged"},
    ):
        with pytest.raises(ValidationError):
            ScheduleChangeOutcome.model_validate(unchanged | patch)


def test_observer_signal_acknowledgement_is_distinct_from_original_exit():
    body = IDENTITY | {
        "state": "effect_unconfirmed",
        "pending": True,
        "expected": EXPECTED,
        "stop_state": "acknowledged",
    }
    assert ObserverStopOutcome.model_validate(body).stop_state == "acknowledged"
    with pytest.raises(ValidationError):
        ObserverStopOutcome.model_validate(body | {"state": "confirmed"})
    assert ObserverStopOutcome.model_validate(
        body | {"state": "confirmed", "stop_state": "exit_confirmed"}
    ).pending
    with pytest.raises(ValidationError):
        ObserverStopOutcome.model_validate(body | {"state": "unchanged"})


def test_journal_is_closed_projection_not_free_message_or_a_result():
    page = HostJournalPage.model_validate(journal_page())
    assert len(page.entries) == 1
    assert HostJournalPage.model_validate_json(page.model_dump_json()) == page
    prefix = "event=run.started level=info run_id=" + "a" * 32
    for value in (
        prefix + " token=secret",
        prefix + "\n",
        prefix.replace("run.started", "unknown.event"),
        "password=secret",
        prefix.replace("info", "notice"),
    ):
        with pytest.raises(ValidationError):
            HostJournalEntry(at=None, message=value)
    with pytest.raises(ValidationError):
        HostJournalPage.model_validate(journal_page() | {"source": "api"})


def test_journal_cursor_and_cardinality_are_finite_and_explicitly_gapped():
    assert JournalQuery(source="sync-observer").model_dump() == {
        "source": "sync-observer",
        "cursor": None,
        "limit": 80,
    }
    assert len(JournalQuery(source="sync-observer", cursor="a" * 2048).cursor or "") == 2048
    for changes in (
        {"cursor": "a" * 2049},
        {"limit": True},
        {"limit": 81},
        {"limit": 0},
        {"unit": "hfcache-sync.service"},
    ):
        with pytest.raises(ValidationError):
            JournalQuery.model_validate({"source": "sync-observer"} | changes)
    with pytest.raises(ValidationError):
        HostJournalPage.model_validate(journal_page() | {"entries": journal_page()["entries"] * 81})
    page = HostJournalPage.model_validate(journal_page() | {"gap": True, "truncated": True})
    assert page.gap
    assert page.truncated
    assert len(json.dumps(page.model_dump(mode="json")).encode()) < 524288
