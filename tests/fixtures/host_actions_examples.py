"""Inert original-model host evidence; never a manager or installed grant."""

from hfcache.host_actions_models import (
    HostJournalPage,
    HostObserverStatus,
    ObserverStopOutcome,
    ScheduleChangeOutcome,
    ScheduleValidation,
)
from tests.fixtures.host_examples import host_status

ARCHIVE = "01234567-89ab-cdef-0123-456789abcdef"
EXPECTED = {
    "boot_id": ARCHIVE,
    "invocation_id": "a" * 32,
    "main_pid": 1234,
    "start_ticks": 4567,
}


def host_action_examples():
    binding = host_status().binding
    assert binding is not None
    common = {
        "schema_version": 1,
        "archive_id": ARCHIVE,
        "operation_id": "a" * 32,
        "request_digest": "b" * 64,
        "state": "confirmed",
        "pending": False,
    }
    return (
        HostObserverStatus.model_validate(
            {
                "schema_version": 1,
                "archive_id": ARCHIVE,
                "profile": "native",
                "host_binding": binding,
                "permissions": {"schedule": True, "observer": True},
                "permission_reasons": {"schedule": "granted", "observer": "granted"},
                "state": "observed",
                "reason": None,
                "unit": "hfcache-sync.service",
                "expected": EXPECTED,
            }
        ),
        ScheduleValidation.model_validate(
            {
                "schema_version": 1,
                "archive_id": ARCHIVE,
                "on_calendar": "daily",
                "randomized_delay_sec": None,
                "normalized_on_calendar": "*-*-* 00:00:00",
                "normalized_randomized_delay_sec": None,
                "next_elapse": None,
            }
        ),
        ScheduleChangeOutcome.model_validate(
            common
            | {
                "action": "replace",
                "expected_revision": "c" * 64,
                "stored_revision": "d" * 64,
                "file_state": "installed",
                "manager_state": "reload_acknowledged",
                "timer_was_active": False,
                "timer_is_active": False,
            }
        ),
        ObserverStopOutcome.model_validate(
            common
            | {
                "expected": EXPECTED,
                "stop_state": "exit_confirmed",
            }
        ),
        HostJournalPage.model_validate(
            {
                "schema_version": 1,
                "archive_id": ARCHIVE,
                "source": "sync-observer",
                "entries": [
                    {
                        "at": "2026-10-27T12:00:00Z",
                        "message": "event=run.completed level=info run_id=" + "a" * 32,
                    }
                ],
                "next_cursor": None,
                "gap": False,
                "truncated": False,
            }
        ),
    )
