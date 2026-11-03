"""Real API lane/store -> credential-framed Unix socket -> actual file writer.

Only protected installed capture and kernel SID provenance use the explicit
owned fixture adapter. This proves transport/filesystem integration, not MAC or
installed native/rootless acceptance.
"""

import asyncio
import copy
import socket
import threading
from contextlib import contextmanager

import httpx
import pytest

from hfcache import host_configuration as configuration
from hfcache import host_policy, host_protocol
from hfcache.config import load_config
from hfcache.errors import OperationError
from hfcache.host_helper_client import HostHelperClient
from tests.intent_fixtures import create_app
from tests.unit.test_api_configuration_applications import ROUTE, _preview
from tests.unit.test_api_managed_configuration import _settings
from tests.unit.test_host_action_routes import ORIGIN
from tests.unit.test_host_action_routes import (
    administrator as administrator,  # noqa: PLC0414 - shared fixture
)
from tests.unit.test_host_action_routes import (
    configured as configured,  # noqa: PLC0414 - shared fixture
)
from tests.unit.test_host_authorization import status
from tests.unit.test_host_configuration import writer as writer  # noqa: PLC0414 - shared fixture
from tests.unit.test_host_helper_client import DEPLOYMENT, UnixTestBinding


class _DisconnectBeforeWriterError(Exception):
    """Owned transport loss after the original authenticated frame, before any effect."""


@contextmanager
def _writer_socket(tmp_path, writer, *, disconnect_after_effect, disconnect_before_effect=False):
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    host_protocol.configure_listener(listener)
    path = tmp_path / "actual-writer.sock"
    listener.bind(str(path))
    listener.listen(8)
    listener.settimeout(0.05)
    stopped = threading.Event()
    calls, errors = [], []
    grant = copy.deepcopy(status())
    grant["binding"]["archive_id"] = writer.snapshot().archive_id

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

                        def dispatch(request, snapshot, _seconds):
                            calls.append(request.operation)
                            if request.operation == "status":
                                return copy.deepcopy(grant)
                            if request.operation == "config-read":
                                return host_policy.read_config_base(snapshot)
                            if request.operation == "config-prepare":
                                return host_policy.prepare_configuration(snapshot, request.body)
                            if request.operation == "config-apply":
                                if disconnect_before_effect:
                                    raise _DisconnectBeforeWriterError  # noqa: TRY301 - explicit owned transport fault
                                return configuration.apply_configuration(
                                    writer.policy, snapshot, request.body
                                )
                            assert request.operation == "config-outcome"
                            return configuration.read_configuration_outcome(
                                writer.policy, snapshot, request.body
                            )

                        result = exchange.dispatch(dispatch)
                        assert isinstance(result, dict)
                        if disconnect_after_effect and exchange.request.operation == "config-apply":
                            continue  # Real socket loss after the actual durable installation.
                        exchange.respond(outcome="ok", body=result)
                except _DisconnectBeforeWriterError:
                    continue  # Actual EOF after framing/peer proof; the writer was never called.
                except BaseException as error:  # noqa: BLE001 - retain failures across test thread
                    errors.append(error)

    server = threading.Thread(target=serve, name="owned-configuration-helper")
    server.start()
    try:
        yield path, calls, grant
    finally:
        stopped.set()
        server.join(3)
        assert not server.is_alive()
        listener.close()
        path.unlink()
        assert errors == []


def _fail_application_result(monkeypatch, store):
    transition = store.transition

    def unavailable(identifier, state, **kwargs):
        receipt = store.get(identifier)
        if receipt.route == ROUTE and state == "succeeded":
            message = "injected API result persistence failure"
            raise OSError(message)
        return transition(identifier, state, **kwargs)

    monkeypatch.setattr(store, "transition", unavailable)


@pytest.mark.parametrize("fault", ["none", "disconnect", "result-persistence"])
def test_api_unix_writer_exact_install_and_original_recovery(
    configured, writer, tmp_path, monkeypatch, fault
):
    server, lock, headers, _, _ = configured
    server = server.model_copy(update={"archive_config": configuration.CONFIGURATION})
    predecessor_inode = configuration.CONFIGURATION.stat().st_ino
    lock_inode = configuration.LOCK.stat().st_ino

    with _writer_socket(tmp_path, writer, disconnect_after_effect=fault == "disconnect") as (
        socket_path,
        calls,
        grant,
    ):

        def application():
            client = HostHelperClient(UnixTestBinding(socket_path), deployment_sha256=DEPLOYMENT)
            return create_app(server, instance_lock_path=lock, host_helper=client)

        async def exercise():
            app = application()
            async with (
                app.router.lifespan_context(app),
                httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url=ORIGIN) as client,
            ):
                read = await client.get("/api/v1/config", headers=headers)
                assert read.status_code == 200, read.text
                managed = _settings(read.json()["envelope"]["data"]["base_revision"])
                body = managed | {"preview": await _preview(client, headers, managed, app)}
                if fault == "result-persistence":
                    _fail_application_result(monkeypatch, app.state.operations)
                keyed = headers | {"Idempotency-Key": "original-real-unix-install"}
                accepted = await client.post(ROUTE, json=body, headers=keyed)
                assert accepted.status_code == 202, accepted.text
                identifier = accepted.json()["operation"]["operation_id"]
                if fault != "none":
                    with pytest.raises(OperationError):
                        await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                    assert app.state.operations.get(identifier).state == "interrupted"
                else:
                    result = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                    assert result.exit_code == 0
                    assert result.data["state"] == "confirmed"
                assert load_config(configuration.CONFIGURATION).sync.max_workers == 3
                assert configuration.LOCK.stat().st_ino == lock_inode
                predecessor = configuration.APPLICATIONS / identifier / "predecessor.toml"
                assert predecessor.read_bytes() == writer.original
                assert predecessor.stat().st_ino == predecessor_inode
                assert configuration.BACKUP.read_bytes() == writer.original
                assert not configuration.PENDING.exists()
            # Restart both the online lane and the client; the host's durable
            # outcome and installed/predecessor files stay exactly where they are.
            grant["permissions"]["configuration"] = False
            grant["permission_reasons"]["configuration"] = "policy-denied"
            restored = application()
            async with (
                restored.router.lifespan_context(restored),
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(restored), base_url=ORIGIN
                ) as client,
            ):
                observed = await client.get(ROUTE + "/" + identifier, headers=keyed)
                assert observed.status_code == 200, observed.text
                outcome = observed.json()["envelope"]["data"]
                assert outcome["state"] == "confirmed"
                assert (
                    outcome["config_fingerprint"]
                    == load_config(configuration.CONFIGURATION).fingerprint()
                )
                assert calls.count("config-apply") == 1
                assert calls[-1] == "config-outcome"
                duplicate = await client.post(ROUTE, json=body, headers=keyed)
                assert duplicate.status_code == 403
                assert calls.count("config-apply") == 1

        asyncio.run(exercise())


def test_original_key_never_retransmits_after_real_unix_loss_before_writer_intent(  # noqa: PLR0915 - one visible request/restart/original-key sequence
    configured, writer, tmp_path
):
    server, lock, headers, _, _ = configured
    server = server.model_copy(update={"archive_config": configuration.CONFIGURATION})
    original_files = {
        str(path): (configuration._identity(path.lstat()), path.read_bytes())
        for path in writer.root.rglob("*")
        if path.is_file()
    }
    original_key = writer.state.key
    with _writer_socket(
        tmp_path, writer, disconnect_after_effect=False, disconnect_before_effect=True
    ) as (socket_path, calls, grant):

        def application():
            helper = HostHelperClient(UnixTestBinding(socket_path), deployment_sha256=DEPLOYMENT)
            return create_app(server, instance_lock_path=lock, host_helper=helper)

        def unchanged_files():
            assert {
                str(path): (configuration._identity(path.lstat()), path.read_bytes())
                for path in writer.root.rglob("*")
                if path.is_file()
            } == original_files
            assert writer.state.key == original_key
            assert not configuration.APPLICATIONS.exists()
            assert not configuration.PENDING.exists()
            assert not configuration.CANDIDATE.exists()
            assert not configuration.BACKUP.exists()

        async def exercise():
            app = application()
            async with (
                app.router.lifespan_context(app),
                httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url=ORIGIN) as client,
            ):
                read = await client.get("/api/v1/config", headers=headers)
                assert read.status_code == 200, read.text
                managed = _settings(read.json()["envelope"]["data"]["base_revision"])
                body = managed | {"preview": await _preview(client, headers, managed, app)}
                keyed = headers | {"Idempotency-Key": "original-before-helper-intent"}
                accepted = await client.post(ROUTE, json=body, headers=keyed)
                assert accepted.status_code == 202, accepted.text
                identifier = accepted.json()["operation"]["operation_id"]
                with pytest.raises(OperationError):
                    await asyncio.to_thread(app.state.runner.wait, identifier, timeout=3)
                receipt = app.state.operations.get(identifier)
                assert receipt.state == "interrupted"
                assert (
                    sum(event.kind == "configuration.transmission" for event in receipt.events) == 1
                )
                assert calls.count("config-apply") == 1
                unchanged_files()
            # Admission/history survive an API restart. Permission remains granted
            # so the duplicate reaches the original-key gate, rather than 403.
            assert grant["permissions"]["configuration"] is True
            restored = application()
            async with (
                restored.router.lifespan_context(restored),
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(restored), base_url=ORIGIN
                ) as client,
            ):
                observed = await client.get(ROUTE + "/" + identifier, headers=keyed)
                assert observed.status_code == 200, observed.text
                outcome = observed.json()["envelope"]["data"]
                assert outcome["state"] == "unknown"
                assert outcome["pending"] is False
                prepares = calls.count("config-prepare")
                duplicate = await client.post(ROUTE, json=body, headers=keyed)
                assert duplicate.status_code == 202, duplicate.text
                assert duplicate.json()["created"] is False
                assert duplicate.json()["operation"]["operation_id"] == identifier
                assert duplicate.json()["operation"]["state"] == "interrupted"
                assert calls.count("config-prepare") == prepares
                assert calls.count("config-apply") == 1
                fresh = await client.post(
                    ROUTE,
                    json=body,
                    headers=headers | {"Idempotency-Key": "replacement-before-intent"},
                )
                assert fresh.status_code == 409, fresh.text
                assert calls.count("config-apply") == 1
                assert restored.state.operations.get(identifier).state == "interrupted"
                unchanged_files()

        asyncio.run(exercise())
