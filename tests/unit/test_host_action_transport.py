"""INV022 fixed private grammar and journal subcapacity on actual Unix exchanges."""

import asyncio
import copy
import threading

import pytest

from hfcache.host_helper_client import HostHelperClient
from hfcache.host_protocol import HostProtocolError, HostRequest
from tests.unit.test_host_helper_client import DEPLOYMENT, UnixTestBinding, unix_service

ID = "1" * 32
DIGEST = "a" * 64
EXPECTED = {
    "boot_id": "cf68ba1d-153b-41bc-8f0b-b0414512dc03",
    "invocation_id": ID,
    "main_pid": 123,
    "start_ticks": 456,
}


def parse(operation, body):
    return HostRequest.parse(
        {"schema_version": 1, "request_id": ID, "operation": operation, "body": body}
    )


@pytest.mark.parametrize(
    ("operation", "body"),
    [
        ("observer-status", {}),
        ("schedule-validate", {"on_calendar": "daily", "randomized_delay_sec": None}),
        *[
            (
                "schedule-change",
                {
                    "operation_id": ID,
                    "request_digest": DIGEST,
                    "request": {"action": action, "expected_revision": DIGEST},
                },
            )
            for action in ("pause", "resume", "reset")
        ],
        (
            "schedule-change",
            {
                "operation_id": ID,
                "request_digest": DIGEST,
                "request": {
                    "action": "replace",
                    "expected_revision": DIGEST,
                    "on_calendar": "daily",
                    "randomized_delay_sec": "5m",
                },
            },
        ),
        (
            "observer-stop",
            {"operation_id": ID, "request_digest": DIGEST, "request": {"expected": EXPECTED}},
        ),
        ("schedule-outcome", {"operation_id": ID, "request_digest": DIGEST}),
        ("observer-outcome", {"operation_id": ID, "request_digest": DIGEST}),
        ("journal-read", {"source": "sync-observer", "cursor": None, "limit": 80}),
    ],
)
def test_fixed_private_request_shapes_roundtrip_without_selector_authority(operation, body):
    request = parse(operation, body)
    assert request.operation == operation
    assert request.body == body
    assert parse(operation, copy.deepcopy(body)).wire() == request.wire()


@pytest.mark.parametrize(
    ("operation", "body"),
    [
        ("observer-status", {"unit": "hfcache.target"}),
        (
            "observer-stop",
            {
                "operation_id": ID,
                "request_digest": DIGEST,
                "request": {"expected": EXPECTED, "manager": "user"},
            },
        ),
        (
            "observer-stop",
            {
                "operation_id": ID,
                "request_digest": DIGEST,
                "request": {"expected": dict(EXPECTED, main_pid=True)},
            },
        ),
        (
            "observer-stop",
            {
                "operation_id": ID,
                "request_digest": DIGEST,
                "request": {"expected": dict(EXPECTED, start_ticks=0)},
            },
        ),
        (
            "observer-stop",
            {
                "operation_id": ID,
                "request_digest": DIGEST,
                "request": {"expected": dict(EXPECTED, uid=0)},
            },
        ),
        (
            "schedule-change",
            {
                "operation_id": ID,
                "request_digest": DIGEST,
                "request": {"action": "enable", "expected_revision": DIGEST},
            },
        ),
        (
            "schedule-change",
            {
                "operation_id": ID,
                "request_digest": DIGEST,
                "request": {"action": "pause", "expected_revision": DIGEST, "on_calendar": "daily"},
            },
        ),
        (
            "schedule-outcome",
            {"operation_id": ID, "request_digest": DIGEST, "request": {"action": "resume"}},
        ),
        ("schedule-validate", {"on_calendar": "daily\n[Service]", "randomized_delay_sec": None}),
        ("schedule-validate", {"on_calendar": "daily\\", "randomized_delay_sec": None}),
        ("schedule-validate", {"on_calendar": "x" * 4097, "randomized_delay_sec": None}),
        ("schedule-validate", {"on_calendar": "daily", "randomized_delay_sec": " "}),
        ("journal-read", {"source": ["sync-observer"], "cursor": None, "limit": 80}),
        ("journal-read", {"source": "hfcache.target", "cursor": None, "limit": 80}),
        ("journal-read", {"source": "sync-observer", "cursor": None, "limit": True}),
        ("journal-read", {"source": "sync-observer", "cursor": None, "limit": 81}),
        ("journal-read", {"source": "sync-observer", "cursor": "x" * 2049, "limit": 80}),
        (
            "journal-read",
            {"source": "sync-observer", "cursor": None, "limit": 80, "path": "/srv/hfcache"},
        ),
    ],
)
def test_effect_and_diagnostic_grammar_refuses_injection_extra_fields_and_coercion(operation, body):
    with pytest.raises(HostProtocolError, match="invalid-request"):
        parse(operation, body)


def test_journal_has_only_two_slots_and_cancellation_retains_the_original_owned_work(tmp_path):
    stalled = threading.Event()
    with unix_service(tmp_path) as (path, accepted, _errors):
        binding = UnixTestBinding(path, stall=stalled)
        client = HostHelperClient(binding, deployment_sha256=DEPLOYMENT)
        query: dict[str, object] = {"source": "sync-observer", "cursor": None, "limit": 80}

        async def run():
            journals = [asyncio.create_task(client.async_journal_read(query)) for _ in range(2)]
            for _ in range(100):
                if len(client._jobs) == 2 and len(client._workers) == 2:
                    break
                await asyncio.sleep(0.005)
            assert len(client._jobs) == 2
            with pytest.raises(HostProtocolError, match="busy"):
                await client.async_journal_read(query)
            status = asyncio.create_task(client.async_status())
            for _ in range(100):
                if len(client._jobs) == 3:
                    break
                await asyncio.sleep(0.005)
            assert len(client._jobs) == 3
            journals[0].cancel()
            with pytest.raises(asyncio.CancelledError):
                await journals[0]
            assert sum(job.journal for job in client._jobs) == 2
            assert not accepted
            stalled.set()
            assert await journals[1] == {"status": "observed"}
            assert await status == {"status": "observed"}

        try:
            asyncio.run(run())
        finally:
            stalled.set()
            assert client.close(timeout=3)
        assert len(accepted) == 2
        assert not client._jobs
        assert all(not worker.is_alive() for worker in client._workers)


def test_invalid_effect_body_never_reserves_a_client_slot_or_connects(tmp_path):
    binding = UnixTestBinding(tmp_path / "must-not-connect.sock")
    client = HostHelperClient(binding, deployment_sha256=DEPLOYMENT)
    try:
        for method in (
            client.schedule_validate,
            client.schedule_change,
            client.observer_stop,
            client.schedule_outcome,
            client.observer_outcome,
            client.journal_read,
        ):
            with pytest.raises(HostProtocolError, match="invalid-request"):
                method({"unit": "hfcache.target"})
        assert not binding.entered.is_set()
        assert not client._jobs
        assert not client._workers
    finally:
        assert client.close(timeout=3)
