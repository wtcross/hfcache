"""Scheduled observers preserve exact terminal outcomes without replay (ADR121)."""

import json
import os
import signal
import socketserver
import stat
import subprocess
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, Thread

import httpx
import pytest

from hfcache import scheduled_client
from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.client_errors import RemoteApiError
from hfcache.errors import HfcacheError, SafetyError
from hfcache.hub import HubClient
from hfcache.models import serialize
from hfcache.scheduled_client import ObservationFile, ScheduledObservation, run_scheduled
from tests.api_cli import api_cli
from tests.fixtures import examples
from tests.unit.test_api_client_adversarial import (
    BASE,
    OPERATION,
    RUN,
    TOKEN,
    _accepted,
    _operation,
    _read,
    _response,
)
from tests.unit.test_api_commands import (
    configured as installed_archive,  # noqa: F401 - fixture
)


class CrashError(RuntimeError):
    pass


class Writer:
    """Real strict ApiClient talks to bounded synthetic HTTP responses."""

    def __init__(self, config, *, command="sync", fail=0, pending=0, lost_ack=False):
        self.config = config
        self.command = command
        self.fail = fail
        self.pending = pending
        self.lost_ack = lost_ack
        self.requests = []
        self.admitted = False
        self.key = None
        self.clock = 0.0
        self.windows = 0
        self.principal = "rest-writer"
        self.identifier = OPERATION
        self.receipt_archive = examples.ARCHIVE_ID
        self.result = None
        self.before_post = None

    @property
    def route(self):
        return "/api/v1/syncs" if self.command == "sync" else "/api/v1/verifications"

    def sleep(self, duration):
        self.clock += duration

    def receipt(self, state="succeeded"):
        value = _operation(state=state, identifier=self.identifier)
        value.update(route=self.route, archive_id=self.receipt_archive, principal=self.principal)
        return value

    def response(self, request):
        self.requests.append(request)
        if request.url.path.endswith("/capabilities"):
            return _response(
                _read(
                    data={
                        "api_version": 1,
                        "credential_class": self.principal,
                        "capabilities": ["read", "write"]
                        if self.principal == "rest-writer"
                        else ["read"],
                        "instance_id": "e" * 32,
                        "reads": True,
                        "operations": True,
                        "operation_history": True,
                        "mcp": False,
                        "maintenance_enabled": False,
                        "max_page_size": 1000,
                    }
                )
            )
        if request.method == "POST":
            if self.before_post:
                self.before_post(request)
            assert request.url.path.endswith(self.route)
            assert json.loads(request.content) == (
                {} if self.command == "sync" else {"mode": "full"}
            )
            self.key = request.headers["idempotency-key"]
            self.admitted = True
            if self.lost_ack:
                self.lost_ack = False
                message = "synthetic lost accepted acknowledgment"
                raise httpx.ReadError(message)
            value = _accepted()
            value["operation"] = self.receipt("queued")
            return _response(value, status=202, headers={"location": value["links"]["status"]})
        if request.url.path.endswith("/lookup"):
            if not self.admitted:
                return _response(
                    {
                        "request_id": "a" * 32,
                        "code": "HFAPI013",
                        "message": "Operation history is unavailable",
                        "exit_code": 20,
                    },
                    status=404,
                )
            assert request.headers["idempotency-key"] == self.key
            return _response(_read(data={"operation": self.receipt()}))
        if request.url.path.endswith("/result"):
            value = _read(data={"exact_terminal": True})
            value["envelope"]["command"] = "sync" if self.command == "sync" else "verify --full"
            if self.fail:
                value["envelope"].update(
                    exit_code=self.fail,
                    outcome="failed",
                    errors=[
                        {
                            "code": "HFVER001" if self.fail == 40 else "HFSYN001",
                            "message": "domain finding",
                            "repository": None,
                            "context": {},
                        }
                    ],
                )
            self.result = value["envelope"]
            return _response(value)
        self.pending -= 1
        state = "running" if self.pending >= 0 else ("failed" if self.fail else "succeeded")
        return _response(_read(data={"operation": self.receipt(state)}))

    def factory(self, config):
        owner = self

        class Client(ApiClient):
            def observe(self, *args, **kwargs):
                owner.windows += 1
                return super().observe(*args, **kwargs)

        return Client(
            config,
            transport=httpx.MockTransport(self.response),
            sleep=self.sleep,
            monotonic=lambda: self.clock,
        )


@pytest.fixture
def configured(tmp_path):
    token = tmp_path / "token"
    token.write_text(TOKEN)
    token.chmod(0o600)
    return ClientConfig(
        schema_version=1,
        api_url=BASE,
        api_token_file=token,
        expected_archive_id=examples.ARCHIVE_ID,
        read_retries=0,
        wait_timeout=0.5,
    )


@pytest.fixture
def api_archive(request):
    return request.getfixturevalue("installed_archive")


def install_handle(directory, config, *, operation_id=OPERATION, **changes):
    handle = ScheduledObservation(
        schema_version=1,
        command="sync",
        endpoint=config.url,
        archive_id=examples.ARCHIVE_ID,
        principal="rest-writer",
        idempotency_key="a" * 32,
        operation_id=operation_id,
    ).model_copy(update=changes)
    with ObservationFile(directory) as store:
        assert store.read() is None
        store.write(handle)
    return handle


def test_independent_schema_one_golden_round_trip():
    path = Path(__file__).parents[1] / "fixtures/schemas/private/scheduled-observation.json"
    assert path.read_text() == serialize(examples.scheduled_observation().model_dump(mode="json"))
    assert (
        ScheduledObservation.model_validate_json(path.read_text())
        == examples.scheduled_observation()
    )


@pytest.mark.parametrize(("command", "exit_code"), [("sync", 0), ("sync", 30), ("verify-full", 40)])
def test_scheduled_job_returns_exact_typed_terminal_result(
    configured, tmp_path, command, exit_code
):
    writer = Writer(configured, command=command, fail=exit_code)
    state = tmp_path / "state"
    result = run_scheduled(configured, command, state, client_factory=writer.factory)
    assert result.to_payload() == writer.result
    assert result.exit_code == exit_code
    assert result.run_id == RUN
    assert not (state / "pending.json").exists()
    assert [path.name for path in state.iterdir()] == [".lock"]
    assert sum(request.method == "POST" for request in writer.requests) == 1


def test_key_is_durable_before_the_only_post(configured, tmp_path):
    writer = Writer(configured)
    state = tmp_path / "state"
    checkpoints = []

    def before_post(request):
        assert checkpoints[-1] == "after_directory_fsync"
        payload = json.loads((state / "pending.json").read_text())
        assert payload["idempotency_key"] == request.headers["idempotency-key"]
        assert payload["operation_id"] is None
        assert set(payload) == {
            "schema_version",
            "command",
            "endpoint",
            "archive_id",
            "principal",
            "idempotency_key",
            "operation_id",
        }
        assert TOKEN not in (state / "pending.json").read_text()
        assert stat.S_IMODE(state.stat().st_mode) == 0o700
        assert stat.S_IMODE((state / "pending.json").stat().st_mode) == 0o600

    writer.before_post = before_post
    run_scheduled(
        configured, "sync", state, client_factory=writer.factory, checkpoint=checkpoints.append
    )


def test_finite_windows_keep_observing_without_posting_again(configured, tmp_path):
    writer = Writer(configured, pending=12)
    result = run_scheduled(
        configured, "sync", tmp_path / "state", client_factory=writer.factory, sleep=writer.sleep
    )
    assert result.exit_code == 0
    assert writer.windows >= 3
    assert writer.clock > configured.wait_timeout * 3
    assert sum(request.method == "POST" for request in writer.requests) == 1


def test_lost_ack_is_recovered_by_the_durable_key_without_retry(configured, tmp_path):
    writer = Writer(configured, lost_ack=True)
    assert (
        run_scheduled(
            configured, "sync", tmp_path / "state", client_factory=writer.factory
        ).exit_code
        == 0
    )
    assert sum(request.method == "POST" for request in writer.requests) == 1
    assert sum(request.url.path.endswith("/lookup") for request in writer.requests) == 1


@pytest.mark.parametrize("operation_id", [None, OPERATION])
def test_existing_handle_is_lookup_only_and_supports_same_class_token_rotation(
    configured, tmp_path, operation_id
):
    state = tmp_path / "state"
    handle = install_handle(state, configured, operation_id=operation_id)
    rotated = "rotated_" + "Q" * 48
    configured.api_token_file.write_text(rotated)
    writer = Writer(configured)
    writer.admitted, writer.key = True, handle.idempotency_key
    assert run_scheduled(configured, "sync", state, client_factory=writer.factory).exit_code == 0
    assert all(request.method == "GET" for request in writer.requests)
    assert all(
        request.headers["authorization"] == "Bearer " + rotated for request in writer.requests
    )


def test_unknown_history_is_preserved_and_never_replayed(configured, tmp_path):
    state = tmp_path / "state"
    install_handle(state, configured, operation_id=None)
    before = (state / "pending.json").read_bytes()
    writer = Writer(configured)
    with pytest.raises(RemoteApiError) as caught:
        run_scheduled(configured, "sync", state, client_factory=writer.factory)
    assert caught.value.code == "HFAPI013"
    assert caught.value.exit_code == 20
    assert (state / "pending.json").read_bytes() == before
    assert all(request.method == "GET" for request in writer.requests)


@pytest.mark.parametrize(
    "stage",
    [
        "before_write",
        "before_file_fsync",
        "after_file_fsync",
        "before_rename",
        "after_rename",
        "before_directory_fsync",
        "after_directory_fsync",
    ],
)
def test_pre_post_crash_boundaries_never_create_replay_authority(configured, tmp_path, stage):
    state = tmp_path / "state"
    writer = Writer(configured)

    def fail(name):
        if name == stage:
            raise CrashError(name)

    with pytest.raises(CrashError):
        run_scheduled(configured, "sync", state, client_factory=writer.factory, checkpoint=fail)
    assert all(request.method == "GET" for request in writer.requests)
    if stage == "before_write":
        assert not (state / "pending.json").exists()
        return
    evidence = {path.name: path.read_bytes() for path in state.iterdir()}
    writer.requests.clear()
    with pytest.raises(HfcacheError) as caught:
        run_scheduled(configured, "sync", state, client_factory=writer.factory)
    assert caught.value.exit_code == 20
    assert evidence == {path.name: path.read_bytes() for path in state.iterdir()}
    assert all(request.method == "GET" for request in writer.requests)


@pytest.mark.parametrize("stage", ["before_unlink", "after_unlink", "after_completion_fsync"])
def test_terminal_handoff_crashes_preserve_only_terminal_cleanup_authority(
    configured, tmp_path, stage
):
    state = tmp_path / "state"
    writer = Writer(configured)

    def fail(name):
        if name == stage:
            raise CrashError(name)

    with pytest.raises(CrashError):
        run_scheduled(configured, "sync", state, client_factory=writer.factory, checkpoint=fail)
    assert writer.result is not None
    assert sum(request.method == "POST" for request in writer.requests) == 1
    if stage == "before_unlink":
        writer.requests.clear()
        assert (
            run_scheduled(configured, "sync", state, client_factory=writer.factory).exit_code == 0
        )
        assert all(request.method == "GET" for request in writer.requests)
    else:
        assert not (state / "pending.json").exists()
    assert (state / ".lock").exists()


@pytest.mark.parametrize("version", [None, True, False, 1.0, "1", 0, 2])
def test_unknown_or_missing_version_is_preserved_without_http(configured, tmp_path, version):
    state = tmp_path / "state"
    install_handle(state, configured)
    payload = json.loads((state / "pending.json").read_text())
    if version is None:
        payload.pop("schema_version")
    else:
        payload["schema_version"] = version
    (state / "pending.json").write_text(json.dumps(payload))
    original = (state / "pending.json").read_bytes()
    writer = Writer(configured)
    with pytest.raises(SafetyError) as caught:
        run_scheduled(configured, "sync", state, client_factory=writer.factory)
    assert caught.value.problems[0].code == "HFAPI014"
    assert (state / "pending.json").read_bytes() == original
    assert writer.requests == []


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"{",
        b"x" * 4097,
        b"\xff",
        b"[]",
        b'{"schema_version":1,"schema_version":1}',
        b'{"schema_version":1,"request_body":{}}',
    ],
)
def test_malformed_bounded_history_is_preserved(configured, tmp_path, raw):
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    record = state / "pending.json"
    record.write_bytes(raw)
    record.chmod(0o600)
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert record.read_bytes() == raw


@pytest.mark.parametrize(
    "changes",
    [
        {"command": "verify-full"},
        {"endpoint": "https://other.example"},
        {"archive_id": "00000000-0000-0000-0000-000000000001"},
        {"principal": "rest-reader"},
        {"operation_id": "../escape"},
        {"extra": True},
    ],
)
def test_changed_or_invalid_binding_cannot_authorize_a_submission(configured, tmp_path, changes):
    state = tmp_path / "state"
    install_handle(state, configured)
    record = state / "pending.json"
    payload = json.loads(record.read_text()) | changes
    record.write_text(json.dumps(payload))
    before = record.read_bytes()
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert record.read_bytes() == before


def test_missing_expected_archive_identity_refuses_before_allocating_state(configured, tmp_path):
    settings = configured.model_copy(update={"expected_archive_id": None})
    state = tmp_path / "state"
    with pytest.raises(SafetyError):
        run_scheduled(settings, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert not state.exists()


@pytest.mark.parametrize("target", ["directory", "record", "lock", "parent"])
def test_symlink_components_are_preserved_and_never_followed(configured, tmp_path, target):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    state = tmp_path / "state"
    if target == "directory":
        state.symlink_to(real, target_is_directory=True)
    elif target == "parent":
        state.symlink_to(real, target_is_directory=True)
        state = state / "child"
    else:
        state.mkdir(mode=0o700)
        (state / ("pending.json" if target == "record" else ".lock")).symlink_to(real / "evidence")
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert list(real.iterdir()) == []


@pytest.mark.parametrize(
    ("target", "mode"), [("directory", 0o750), ("record", 0o640), ("lock", 0o644)]
)
def test_unsafe_permissions_are_not_repaired_or_removed(configured, tmp_path, target, mode):
    state = tmp_path / "state"
    install_handle(state, configured)
    path = (
        state
        if target == "directory"
        else state / ("pending.json" if target == "record" else ".lock")
    )
    path.chmod(mode)
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert stat.S_IMODE(path.stat().st_mode) == mode


def test_unknown_file_and_hardlinked_record_are_preserved(configured, tmp_path):
    state = tmp_path / "state"
    install_handle(state, configured)
    evidence = state / ".pending-unexplained.tmp"
    evidence.write_text("preserve")
    evidence.chmod(0o600)
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert evidence.read_text() == "preserve"
    evidence.unlink()
    os.link(state / "pending.json", tmp_path / "linked")
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert (tmp_path / "linked").read_bytes() == (state / "pending.json").read_bytes()


def test_concurrent_observer_and_replaced_lock_never_create_a_second_lock_domain(tmp_path):
    state = tmp_path / "state"
    with ObservationFile(state) as first:
        with pytest.raises(SafetyError), ObservationFile(state):
            pytest.fail("second observer admitted")
        (state / ".lock").rename(state / "old.lock")
        (state / ".lock").touch(mode=0o600)
        with pytest.raises(SafetyError):
            first.read()
        assert (state / "old.lock").exists()


def test_actual_api_work_survives_observer_restart_without_another_submission(
    api_archive, tmp_path, monkeypatch
):
    server, _, hub, _ = api_archive
    entered, release = Event(), Event()
    original = HubClient.download

    def download(self, *args, **kwargs):
        entered.set()
        assert release.wait(10)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(HubClient, "download", download)
    state = tmp_path / "scheduled"
    try:
        with api_cli(server.archive_config) as remote:
            settings = ClientConfig(
                schema_version=1,
                api_url="http://localhost",
                api_token_file=remote.token,
                expected_archive_id=remote.application.state.policy.archive_id,
            )
            requests = []

            class Transport(httpx.BaseTransport):
                def handle_request(self, request):
                    requests.append(request)
                    return remote.web._transport.handle_request(request)

            class DepartingClient(ApiClient):
                def observe(self, *args, **kwargs):
                    assert entered.wait(5)
                    raise CrashError

            with pytest.raises(CrashError):
                run_scheduled(
                    settings,
                    "sync",
                    state,
                    client_factory=lambda config: DepartingClient(
                        config,
                        transport=Transport(),
                    ),
                )
            try:
                handle = json.loads((state / "pending.json").read_text())
                receipt = remote.application.state.operations.get(handle["operation_id"])
            finally:
                release.set()
            assert receipt.state == "running"
            assert sum(request.method == "POST" for request in requests) == 1
            release.set()
            result = run_scheduled(
                settings,
                "sync",
                state,
                client_factory=lambda config: ApiClient(
                    config,
                    transport=Transport(),
                ),
            )
            assert result.exit_code == 0
            assert result.run_id != receipt.operation_id
            assert len(remote.application.state.operations.list()) == 1
            assert len(hub.downloads) == 2
            assert sum(request.method == "POST" for request in requests) == 1
            assert not (state / "pending.json").exists()
    finally:
        release.set()


@pytest.mark.parametrize(
    "stage",
    [
        "before_write",
        "before_file_fsync",
        "after_file_fsync",
        "before_rename",
        "after_rename",
        "before_directory_fsync",
        "after_directory_fsync",
    ],
)
def test_acknowledged_id_persistence_crashes_never_authorize_another_post(
    configured, tmp_path, stage
):
    state = tmp_path / "state"
    writer = Writer(configured)
    writes, accepted = [0], []

    def checkpoint(name):
        if name == "before_write":
            writes[0] += 1
        if writes[0] == 2 and name == stage:
            raise CrashError(name)

    with pytest.raises(CrashError):
        run_scheduled(
            configured,
            "sync",
            state,
            client_factory=writer.factory,
            checkpoint=checkpoint,
            on_accepted=accepted.append,
        )
    assert accepted == [OPERATION]
    assert sum(request.method == "POST" for request in writer.requests) == 1
    writer.requests.clear()
    if any(path.suffix == ".tmp" for path in state.iterdir()):
        before = {path.name: path.read_bytes() for path in state.iterdir()}
        with pytest.raises(SafetyError):
            run_scheduled(configured, "sync", state, client_factory=writer.factory)
        assert before == {path.name: path.read_bytes() for path in state.iterdir()}
    else:
        assert (
            run_scheduled(configured, "sync", state, client_factory=writer.factory).exit_code == 0
        )
    assert all(request.method == "GET" for request in writer.requests)


@pytest.mark.parametrize("recovered", [False, True])
def test_notifications_use_validated_handles_and_precede_observation(
    configured, tmp_path, recovered
):
    state = tmp_path / "state"
    writer = Writer(configured)
    if recovered:
        handle = install_handle(state, configured)
        writer.key, writer.admitted = handle.idempotency_key, True
    notices = []

    def key(value):
        notices.append(("key", value))
        assert json.loads((state / "pending.json").read_text())["idempotency_key"] == value
        assert all(request.method == "GET" for request in writer.requests)
        if recovered:
            assert writer.requests[-1].url.path.endswith("/lookup")

    def accepted(value):
        notices.append(("accepted", value))

    run_scheduled(
        configured, "sync", state, client_factory=writer.factory, on_key=key, on_accepted=accepted
    )
    assert notices == [("key", writer.key), ("accepted", OPERATION)]


def test_key_equal_to_the_selected_bearer_is_never_disclosed_or_sent_for_lookup(
    configured, tmp_path
):
    state = tmp_path / "state"
    malicious_key = "1234567890abcdef1234567890abcdef"
    install_handle(state, configured, idempotency_key=malicious_key)
    configured.api_token_file.write_text(malicious_key)
    writer, notices = Writer(configured), []
    with pytest.raises(SafetyError) as caught:
        run_scheduled(
            configured,
            "sync",
            state,
            client_factory=writer.factory,
            on_key=notices.append,
            on_accepted=notices.append,
        )
    assert caught.value.problems[0].code == "HFAPI014"
    assert malicious_key not in str(caught.value)
    assert notices == []
    assert not any(request.url.path.endswith("/lookup") for request in writer.requests)
    assert json.loads((state / "pending.json").read_text())["idempotency_key"] == malicious_key


@pytest.mark.parametrize("target", ["record", "lock"])
def test_special_files_are_rejected_without_blocking_or_replacing_them(
    configured, tmp_path, target
):
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    path = state / ("pending.json" if target == "record" else ".lock")
    os.mkfifo(path, mode=0o600)
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert stat.S_ISFIFO(path.stat().st_mode)


def test_changed_pending_evidence_cannot_be_removed_by_terminal_cleanup(configured, tmp_path):
    state, writer = tmp_path / "state", Writer(configured)

    def change(name):
        if name == "before_unlink":
            (state / "pending.json").write_text("preserve changed evidence")

    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=writer.factory, checkpoint=change)
    assert writer.result is not None
    assert (state / "pending.json").read_text() == "preserve changed evidence"


def invoke_main(monkeypatch, configured, state, writer):
    monkeypatch.setattr(scheduled_client, "resolve_client_config", lambda _: configured)
    monkeypatch.setattr(
        scheduled_client,
        "ApiClient",
        lambda config, **_options: writer.factory(config),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "scheduled_client",
            "--client-config",
            "/fixture.toml",
            "--state-directory",
            str(state),
            writer.command,
        ],
    )
    previous = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
    try:
        return scheduled_client.main()
    finally:
        assert all(signal.getsignal(number) == handler for number, handler in previous.items())


def test_main_preserves_exact_nonzero_domain_result_and_journal_safety_handles(
    configured, tmp_path, monkeypatch, capsys
):
    writer = Writer(configured, command="verify-full", fail=40)
    assert invoke_main(monkeypatch, configured, tmp_path / "state", writer) == 40
    output = capsys.readouterr()
    assert json.loads(output.out) == writer.result
    assert output.err.splitlines() == [
        f"Idempotency key: {writer.key}",
        f"Accepted operation: {OPERATION}",
    ]


def test_main_interrupt_preserves_handles_and_reports_recovery_without_terminal_output(
    configured, tmp_path, monkeypatch, capsys
):
    writer, state = Writer(configured), tmp_path / "state"
    original = writer.factory

    def factory(config):
        client = original(config)

        def interrupt(*args, **kwargs):
            raise KeyboardInterrupt

        client.observe = interrupt
        return client

    writer.factory = factory
    assert invoke_main(monkeypatch, configured, state, writer) == 20
    output = capsys.readouterr()
    assert output.out == ""
    assert f"Idempotency key: {writer.key}" in output.err
    assert f"Accepted operation: {OPERATION}" in output.err
    assert "Accepted work may continue" in output.err
    assert str(state) in output.err
    assert (state / "pending.json").is_file()


def test_untrusted_parent_permissions_cannot_redirect_the_private_state(configured, tmp_path):
    parent = tmp_path / "untrusted"
    parent.mkdir(mode=0o777)
    parent.chmod(0o777)
    state = parent / "state"
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert not state.exists()
    assert stat.S_IMODE(parent.stat().st_mode) == 0o777


def test_wrong_owner_is_refused_without_repairing_existing_evidence(
    configured, tmp_path, monkeypatch
):
    state = tmp_path / "state"
    install_handle(state, configured)
    before = (state / "pending.json").read_bytes()
    owner = os.geteuid()
    monkeypatch.setattr(scheduled_client.os, "geteuid", lambda: owner + 1)
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert (state / "pending.json").read_bytes() == before
    assert state.stat().st_uid == owner


def test_pending_file_vanishing_after_inventory_is_uncertainty_not_a_fresh_submission(
    configured, tmp_path, monkeypatch
):
    state = tmp_path / "state"
    install_handle(state, configured)
    original, calls = ObservationFile.check, [0]

    def vanish(self):
        present = original(self)
        calls[0] += 1
        if calls[0] == 2:
            (state / "pending.json").rename(tmp_path / "vanished-evidence.json")
        return present

    monkeypatch.setattr(ObservationFile, "check", vanish)
    with pytest.raises(SafetyError):
        run_scheduled(configured, "sync", state, client_factory=lambda _: pytest.fail("HTTP"))
    assert (tmp_path / "vanished-evidence.json").exists()
    assert not (state / "pending.json").exists()


@pytest.mark.parametrize("stop_signal", [signal.SIGTERM, signal.SIGINT])
def test_real_signal_classifies_stop_without_losing_or_replaying_existing_work(stop_signal):
    with TemporaryDirectory(prefix="hfcache-observer-") as temporary:
        root = Path(temporary)
        channel, token, settings, state = (
            root / "api.sock",
            root / "token",
            root / "client.toml",
            root / "state",
        )
        token.write_text(TOKEN)
        token.chmod(0o600)
        settings.write_text(
            f'schema_version=1\napi_socket="{channel}"\napi_token_file="{token}"\n'
            f'expected_archive_id="{examples.ARCHIVE_ID}"\n'
        )
        config = ClientConfig(
            schema_version=1,
            api_socket=channel,
            api_token_file=token,
            expected_archive_id=examples.ARCHIVE_ID,
        )
        with ObservationFile(state) as store:
            store.read()
            store.write(
                ScheduledObservation(
                    schema_version=1,
                    command="sync",
                    endpoint="unix:" + str(channel),
                    archive_id=examples.ARCHIVE_ID,
                    principal="rest-writer",
                    idempotency_key="a" * 32,
                    operation_id=OPERATION,
                )
            )
        original, entered, methods = (state / "pending.json").read_bytes(), Event(), []
        writer = Writer(config)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                methods.append("GET")
                if self.path.endswith("/capabilities"):
                    response = writer.response(httpx.Request("GET", "http://localhost" + self.path))
                    payload = response.json()
                else:
                    payload = _read(data={"operation": _operation(state="running")})
                raw = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                self.wfile.flush()
                if self.path.endswith(OPERATION):
                    entered.set()

            def do_POST(self):
                methods.append("POST")
                self.send_error(500)

            def log_message(self, format, *args):  # noqa: A002 - stdlib named parameter
                pass

        with socketserver.ThreadingUnixStreamServer(str(channel), Handler) as server:
            channel.chmod(0o600)
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
            thread.start()
            code = (
                "import signal,sys; "
                "before={n:signal.getsignal(n) for n in (signal.SIGINT,signal.SIGTERM)}; "
                "from hfcache.scheduled_client import main; "
                "assert all(signal.getsignal(n)==v for n,v in before.items()); "
                "outcome=main(); assert all(signal.getsignal(n)==v for n,v in before.items()); "
                "sys.exit(outcome)"
            )
            try:
                with subprocess.Popen(
                    [
                        sys.executable,
                        "-c",
                        code,
                        "--client-config",
                        str(settings),
                        "--state-directory",
                        str(state),
                        "sync",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                ) as process:
                    try:
                        assert entered.wait(10)
                        with pytest.raises(SafetyError), ObservationFile(state):
                            pytest.fail("subprocess did not retain exclusive observer ownership")
                        process.send_signal(stop_signal)
                        output, errors = process.communicate(timeout=10)
                    finally:
                        if process.poll() is None:
                            process.kill()
                            process.communicate(timeout=5)
                assert process.returncode == 20, errors
                assert output == ""
                assert "HFAPI019" in errors
                assert "Accepted work may continue" in errors
                assert str(state) in errors
                assert "Idempotency key: " + "a" * 32 in errors
                assert "Accepted operation: " + OPERATION in errors
                assert TOKEN not in errors
            finally:
                server.shutdown()
                thread.join(5)
        assert not thread.is_alive()
        assert set(methods) == {"GET"}
        assert (state / "pending.json").read_bytes() == original
        with ObservationFile(state) as released:
            retained = released.read()
            assert retained is not None
            assert retained.operation_id == OPERATION
