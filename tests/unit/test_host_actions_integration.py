"""Actual credential-framed Unix exchange -> original durable host-action writer.

Protected installed capture/SID and the fixed manager use owned external
adapters. Files, framing, peer credentials, disconnects and fsyncs are real;
this does not qualify native MAC or installed-profile effects.
"""

import socket
import threading
from contextlib import contextmanager

import pytest

from hfcache import host_actions as actions
from hfcache import host_protocol
from hfcache.host_actions_models import ScheduleChangeOutcome
from hfcache.host_helper_client import HostHelperClient
from tests.unit.test_host_actions import _tree
from tests.unit.test_host_actions import (
    writer as writer,  # noqa: PLC0414 - shared filesystem fixture
)
from tests.unit.test_host_helper_client import DEPLOYMENT, UnixTestBinding


@contextmanager
def _writer_socket(tmp_path, writer, *, disconnect):
    path = tmp_path / "host-action.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    host_protocol.configure_listener(listener)
    listener.bind(str(path))
    listener.listen(8)
    listener.settimeout(0.05)
    stopped = threading.Event()
    calls, errors = [], []

    def serve():
        while not stopped.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            with connection:
                try:
                    with host_protocol.receive_exchange(
                        connection, lambda _peer, _seconds: writer.snapshot()
                    ) as exchange:

                        def dispatch(request, captured, _seconds):
                            calls.append(request.operation)
                            if request.operation == "schedule-change":
                                if disconnect == "before":
                                    return None
                                return actions.change_schedule(
                                    writer.policy, captured, request.body
                                )
                            assert request.operation == "schedule-outcome"
                            return actions.read_schedule_outcome(
                                writer.policy, captured, request.body
                            )

                        result = exchange.dispatch(dispatch)
                        if disconnect and exchange.request.operation == "schedule-change":
                            continue  # Owned EOF, without fabricated receipt or writer response.
                        assert isinstance(result, dict)
                        exchange.respond(outcome="ok", body=result)
                except BaseException as error:  # noqa: BLE001 - preserve failures from owned thread
                    errors.append(error)

    server = threading.Thread(target=serve, name="owned-host-action-helper")
    server.start()
    try:
        yield path, calls
    finally:
        stopped.set()
        server.join(3)
        assert not server.is_alive()
        listener.close()
        path.unlink()
        assert not errors


@pytest.mark.parametrize("disconnect", [None, "before", "after"])
def test_real_unix_effect_loss_recovers_original_without_retransmission(
    writer, tmp_path, disconnect
):
    writer.apply(writer.request(operation_id="c" * 32))
    predecessor_bytes = actions.SCHEDULE.read_bytes()
    predecessor_inode = actions.SCHEDULE.stat().st_ino
    lock_inode = actions.LOCK.stat().st_ino
    request = writer.request()
    expected = "unknown" if disconnect == "before" else "confirmed"
    with _writer_socket(tmp_path, writer, disconnect=disconnect) as (path, calls):
        original = HostHelperClient(UnixTestBinding(path), deployment_sha256=DEPLOYMENT)
        try:
            if disconnect:
                with pytest.raises(host_protocol.HostProtocolError):
                    original.schedule_change(request)
            else:
                assert original.schedule_change(request)["state"] == expected
        finally:
            assert original.close(timeout=2)
        before = _tree(writer.root)
        commands = list(writer.state.calls)
        writer.state.permissions["schedule"] = False
        # A fresh process/client generation only reads original authenticated
        # evidence, including after the current write grant has been revoked.
        restored = HostHelperClient(UnixTestBinding(path), deployment_sha256=DEPLOYMENT)
        try:
            outcome = restored.schedule_outcome(
                {key: request[key] for key in ("operation_id", "request_digest")}
            )
            ScheduleChangeOutcome.model_validate(outcome)
            assert outcome["state"] == expected
            assert not outcome["pending"]
        finally:
            assert restored.close(timeout=2)
        assert calls == ["schedule-change", "schedule-outcome"]
        assert writer.state.calls == commands
        assert _tree(writer.root) == before
        assert actions.LOCK.stat().st_ino == lock_inode
        predecessor = (
            actions.SCHEDULE
            if disconnect == "before"
            else actions.BACKUPS / request["operation_id"] / "predecessor.conf"
        )
        assert predecessor.stat().st_ino == predecessor_inode
        assert predecessor.read_bytes() == predecessor_bytes
