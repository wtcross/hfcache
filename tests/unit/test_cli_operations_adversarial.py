"""CLI observation loss preserves one admitted writer operation (decision 120)."""

import json
import signal
from threading import Event

import httpx
import pytest

from hfcache.client import ApiClient
from hfcache.hub import HubClient
from hfcache.paths import RepositoryLayout
from hfcache.publication import read_reference
from tests.api_cli import api_cli
from tests.unit.test_api_commands import (
    configured as command_archive,  # noqa: F401 - fixture
)
from tests.unit.test_synchronize import MODEL, SHA_A


@pytest.fixture
def api_archive(request):
    return request.getfixturevalue("command_archive")


class ObservedTransport(httpx.BaseTransport):
    def __init__(self, delegate, *, lose_ack=False, interrupt_status=False, entered=None):
        self.delegate = delegate
        self.lose_ack = lose_ack
        self.interrupt_status = interrupt_status
        self.entered = entered
        self.requests = []

    def handle_request(self, request):
        self.requests.append((request.method, request.url.path, dict(request.url.params)))
        response = self.delegate.handle_request(request)
        if self.lose_ack and request.method == "POST" and request.url.path.endswith("/syncs"):
            mode = self.lose_ack
            self.lose_ack = False
            payload = json.loads(response.read())
            response.close()
            if mode == "server-error":
                return httpx.Response(
                    500,
                    json={
                        "request_id": payload["request_id"],
                        "code": "HFAPI008",
                        "message": "Internal server error",
                        "exit_code": 20,
                    },
                )
            message = "synthetic lost durable acknowledgment"
            raise httpx.ReadError(message)
        if (
            self.interrupt_status
            and request.method == "GET"
            and "/operations/" in request.url.path
            and not request.url.path.endswith(("/events", "/result", "/lookup"))
        ):
            self.interrupt_status = False
            if self.entered is not None:
                assert self.entered.wait(5)
            response.close()
            signal.raise_signal(signal.SIGINT)
        return response


def _transport(monkeypatch, remote, **options):
    transport = ObservedTransport(remote.web._transport, **options)
    monkeypatch.setattr(
        "hfcache.cli_client.ApiClient", lambda settings: ApiClient(settings, transport=transport)
    )
    return transport


def _operation(result):
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)["data"]["operation"]


@pytest.fixture
def blocked_download(monkeypatch):
    entered, release = Event(), Event()
    original = HubClient.download

    def download(self, *args, **kwargs):
        entered.set()
        assert release.wait(10)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(HubClient, "download", download)
    try:
        yield entered, release
    finally:
        release.set()


@pytest.mark.parametrize("fault", ["lost-ack", "server-error"])
def test_lost_post_ack_recovers_by_printed_key_and_retry_never_resubmits(
    api_archive, monkeypatch, fault
):
    server, layout, hub, _ = api_archive
    key = "lost-cli-ack"
    with api_cli(server.archive_config) as remote:
        transport = _transport(monkeypatch, remote, lose_ack=fault)
        lost = remote.invoke(["--idempotency-key", key, "sync", MODEL.selector])

        assert lost.exit_code == 20
        failure = json.loads(lost.stdout)
        expected = "HFAPI008" if fault == "server-error" else "HFAPI020"
        assert failure["errors"][0]["code"] == expected
        assert failure["data"]["idempotency_key"] == key
        assert failure["data"]["work_may_continue"] is True
        assert key in lost.stderr
        assert "continue" in lost.stderr.lower()
        found = _operation(remote.invoke(["operations", "lookup", key]))
        identifier = found["operation_id"]
        completed = remote.invoke(["operations", "wait", identifier])
        assert completed.exit_code == 0, completed.output
        original = json.loads(completed.stdout)
        again = remote.invoke(["--idempotency-key", key, "sync", MODEL.selector])

        assert again.exit_code == 0, again.output
        assert json.loads(again.stdout) == original
        assert identifier in again.stderr
        assert len(remote.application.state.operations.list()) == 1
        # One explicit initial POST plus one deliberate same-key retry; no hidden retry.
        assert sum(method == "POST" for method, _, _ in transport.requests) == 2
        assert len(hub.downloads) == 1
        reference = read_reference(layout, RepositoryLayout(layout, MODEL).current_ref)
        assert reference.commit_sha == SHA_A
        assert original == remote.application.state.operations.result(identifier).to_payload()


def test_sigint_wait_keeps_active_sync_and_exact_later_wait(
    api_archive, blocked_download, monkeypatch
):
    server, _, hub, _ = api_archive
    entered, release = blocked_download
    key = "sigint-cli-observer"
    with api_cli(server.archive_config) as remote:
        transport = _transport(monkeypatch, remote, interrupt_status=True, entered=entered)
        try:
            interrupted = remote.invoke(["--idempotency-key", key, "sync", MODEL.selector])

            assert interrupted.exit_code == 20, interrupted.output
            failure = json.loads(interrupted.stdout)
            assert failure["errors"][0]["code"] == "HFAPI019"
            assert failure["data"]["idempotency_key"] == key
            identifier = failure["data"]["operation_id"]
            assert key in interrupted.stderr
            assert identifier in interrupted.stderr
            assert "continue" in interrupted.stderr.lower()
            assert entered.is_set()
            assert remote.application.state.operations.get(identifier).state == "running"
            assert len(hub.downloads) == 0
        finally:
            release.set()
        completed = remote.invoke(["operations", "wait", identifier])

        assert completed.exit_code == 0, completed.output
        assert len(hub.downloads) == 1
        assert len(remote.application.state.operations.list()) == 1
        assert sum(method == "POST" for method, _, _ in transport.requests) == 1


def test_detach_returns_admission_while_sync_is_still_active_and_quiet_keeps_handles(
    api_archive, blocked_download, monkeypatch
):
    server, _, hub, _ = api_archive
    entered, release = blocked_download
    key = "detached-cli-sync"
    with api_cli(server.archive_config) as remote:
        transport = _transport(monkeypatch, remote)
        try:
            detached = remote.invoke(
                ["--quiet", "--detach", "--idempotency-key", key, "sync", MODEL.selector]
            )

            assert detached.exit_code == 0, detached.output
            admission = json.loads(detached.stdout)
            assert admission["schema_version"] == 1
            assert admission["kind"] == "operation_admission"
            assert admission["idempotency_key"] == key
            assert "outcome" not in admission
            assert "exit_code" not in admission
            identifier = admission["acceptance"]["operation"]["operation_id"]
            assert key in detached.stderr
            assert identifier in detached.stderr
            assert entered.wait(5)
            assert remote.application.state.operations.get(identifier).state == "running"
            assert len(hub.downloads) == 0
            assert not any("/operations/" in path for _, path, _ in transport.requests)
        finally:
            release.set()
        completed = remote.invoke(["operations", "wait", identifier])

        assert completed.exit_code == 0
        assert len(hub.downloads) == 1


def test_observation_timeout_preserves_handles_and_never_changes_execution_budget(
    api_archive, blocked_download, monkeypatch
):
    server, _, hub, _ = api_archive
    _, release = blocked_download
    key = "observer-deadline"
    with api_cli(server.archive_config) as remote:
        transport = _transport(monkeypatch, remote)
        try:
            timed_out = remote.invoke(
                ["--wait-timeout", "0.02", "--idempotency-key", key, "sync", MODEL.selector]
            )

            assert timed_out.exit_code == 20, timed_out.output
            failure = json.loads(timed_out.stdout)
            assert failure["errors"][0]["code"] == "HFAPI019"
            assert failure["data"]["idempotency_key"] == key
            identifier = failure["data"]["operation_id"]
            assert identifier in timed_out.stderr
            assert "continue" in timed_out.stderr.lower()
        finally:
            release.set()
        completed = remote.invoke(["operations", "wait", identifier])

        assert completed.exit_code == 0
        assert len(hub.downloads) == 1
        assert sum(method == "POST" for method, _, _ in transport.requests) == 1


def test_unknown_operation_wait_never_creates_or_replays_work(api_archive, monkeypatch):
    server, _, hub, _ = api_archive
    with api_cli(server.archive_config) as remote:
        transport = _transport(monkeypatch, remote)

        missing = remote.invoke(["operations", "wait", "9" * 32])

        assert missing.exit_code == 20
        assert json.loads(missing.stdout)["errors"][0]["code"] == "HFAPI013"
        assert not any(method == "POST" for method, _, _ in transport.requests)
        assert remote.application.state.operations.list() == ()
        assert not hub.downloads


def test_api_credential_cannot_be_printed_as_idempotency_key(api_archive, monkeypatch):
    server, _, _, _ = api_archive
    with api_cli(server.archive_config) as remote:
        transport = _transport(monkeypatch, remote)
        credential = remote.token.read_text()

        refused = remote.invoke(["--idempotency-key", credential, "sync", MODEL.selector])

        assert refused.exit_code == 10
        assert credential not in refused.output
        assert not any(method == "POST" for method, _, _ in transport.requests)
        assert remote.application.state.operations.list() == ()


def test_operations_wait_resumes_event_cursor_and_returns_exact_terminal_envelope(
    api_archive, blocked_download, monkeypatch
):
    server, _, _, _ = api_archive
    entered, release = blocked_download
    with api_cli(server.archive_config) as remote:
        transport = _transport(monkeypatch, remote)
        try:
            detached = remote.invoke(["--detach", "sync", MODEL.selector])
            assert detached.exit_code == 0, detached.output
            assert entered.wait(5)
            store = remote.application.state.operations
            (receipt,) = store.list()
            store.append_event(receipt.operation_id, "progress", "already-observed-progress")
            after = store.events(receipt.operation_id).next_cursor
            store.append_event(
                receipt.operation_id, "progress", "newly-observed-progress\n\x1b[31mspoofed"
            )
            transport.requests.clear()
        finally:
            release.set()

        resumed = remote.invoke(["operations", "wait", receipt.operation_id, "--after", str(after)])

        assert resumed.exit_code == 0, resumed.output
        assert json.loads(resumed.stdout) == store.result(receipt.operation_id).to_payload()
        assert "already-observed-progress" not in resumed.stderr
        assert "newly-observed-progress" in resumed.stderr
        assert "\x1b" not in resumed.stderr
        progress = next(
            line for line in resumed.stderr.splitlines() if "newly-observed-progress" in line
        )
        assert "spoofed" in progress
        events = [params for _, path, params in transport.requests if path.endswith("/events")]
        assert events
        assert events[0]["after"] == str(after)
        assert not any(method == "POST" for method, _, _ in transport.requests)
