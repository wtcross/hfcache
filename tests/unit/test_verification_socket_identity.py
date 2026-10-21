"""Decision148: independent file-owner/kernel-peer checks on real owned sockets.

These hermetic checks preserve legacy behavior and exercise original clients;
native system-manager/FD3 installed acceptance remains a separate fixture.
"""

import asyncio
import os
import socket

import pytest

from hfcache.api.app import create_app
from hfcache.api.operations import OperationStore
from hfcache.errors import ConfigurationError, OperationError
from hfcache.server_config import validate_server_config_mapping
from hfcache.verification_executor import VerificationWorker
from hfcache.verification_protocol import VerificationClient, connect_private
from tests.unit.test_api_reads import configured as configured  # noqa: PLC0414 - pytest fixture
from tests.unit.test_verification_executor import listening
from tests.unit.test_verification_executor import policy as policy  # noqa: PLC0414 - pytest fixture


@pytest.fixture
def owned_listener(tmp_path):
    parent = tmp_path / "private"
    parent.mkdir(mode=0o700)
    path = parent / "verification.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        path.chmod(0o600)
        listener.listen(8)
        listener.settimeout(0.1)
        yield path, listener


def test_explicit_wrong_file_owner_refuses_before_connection(owned_listener):
    path, listener = owned_listener
    with pytest.raises(OperationError):
        connect_private(
            path,
            expected_uid=os.geteuid(),
            expected_socket_owner_uid=os.geteuid() + 1,
            timeout_seconds=0.1,
        )
    with pytest.raises(TimeoutError):
        listener.accept()


def test_correct_file_owner_still_refuses_wrong_actual_kernel_peer(owned_listener):
    path, listener = owned_listener
    with pytest.raises(OperationError):
        connect_private(
            path,
            expected_uid=os.geteuid() + 1,
            expected_socket_owner_uid=os.geteuid(),
            timeout_seconds=0.1,
        )
    # The real connect occurred after file-owner validation, then peer validation
    # refused it. A correct owner cannot grant an alternate acceptable peer UID.
    with listener.accept()[0] as accepted:
        assert accepted.recv(1) == b""


@pytest.mark.parametrize("explicit_owner", [False, True])
def test_real_equal_identity_connection_preserves_legacy_calls(owned_listener, explicit_owner):
    path, listener = owned_listener
    options = {"expected_socket_owner_uid": os.geteuid()} if explicit_owner else {}
    with (
        connect_private(path, expected_uid=os.geteuid(), timeout_seconds=0.1, **options),
        listener.accept()[0],
    ):
        pass


def test_omitted_owner_retains_resolved_peer_owner_before_connect(owned_listener):
    path, listener = owned_listener
    with pytest.raises(OperationError):
        connect_private(path, expected_uid=os.geteuid() + 1, timeout_seconds=0.1)
    with pytest.raises(TimeoutError):
        listener.accept()


@pytest.mark.parametrize("mode", [0o666, 0o644, 0o777])
def test_explicit_owner_cannot_relax_socket_mode(owned_listener, mode):
    path, _listener = owned_listener
    path.chmod(mode)
    with pytest.raises(OperationError):
        connect_private(
            path,
            expected_uid=os.geteuid(),
            expected_socket_owner_uid=os.geteuid(),
            timeout_seconds=0.1,
        )


def test_explicit_owner_cannot_relax_nofollow_or_parent_permissions(owned_listener):
    path, _listener = owned_listener
    alias = path.with_name("alias.sock")
    alias.symlink_to(path)
    for selected in (alias, path):
        if selected == path:
            path.parent.chmod(0o777)
        with pytest.raises(OperationError):
            connect_private(
                selected,
                expected_uid=os.geteuid(),
                expected_socket_owner_uid=os.geteuid(),
                timeout_seconds=0.1,
            )


@pytest.mark.parametrize("peer", [None, 0, 4242])
def test_client_omitted_owner_uses_exact_legacy_resolved_peer(tmp_path, peer):
    client = VerificationClient(tmp_path / "verification.sock", expected_uid=peer)
    expected = os.geteuid() if peer is None else peer
    assert client.expected_uid == expected
    assert client.expected_socket_owner_uid == expected


def test_real_worker_client_forwards_explicit_owner_and_preserves_peer_checks(policy, tmp_path):
    with OperationStore(tmp_path / "worker-state") as store:
        worker = VerificationWorker(policy, store)
        try:
            with listening(tmp_path, worker) as (original, _stop):
                original.check_available()
                explicit = VerificationClient(
                    original.path,
                    expected_uid=os.geteuid(),
                    expected_socket_owner_uid=os.geteuid(),
                    timeout_seconds=0.1,
                )
                explicit.check_available()
                for peer, owner in (
                    (os.geteuid(), os.geteuid() + 1),
                    (os.geteuid() + 1, os.geteuid()),
                ):
                    refused = VerificationClient(
                        original.path,
                        expected_uid=peer,
                        expected_socket_owner_uid=owner,
                        timeout_seconds=0.1,
                    )
                    with pytest.raises(OperationError):
                        refused.check_available()
                explicit.check_available()
        finally:
            worker.close()


@pytest.mark.parametrize("value", [-1, True, False, 981.0, "981", [], {}])
def test_owner_uid_is_strict_in_configuration_client_and_direct_connector(tmp_path, value):
    with pytest.raises(ConfigurationError):
        validate_server_config_mapping(
            {
                "schema_version": 1,
                "credentials": {"writer": {"file": str(tmp_path / "credential")}},
                "verification": {"expected_socket_owner_uid": value},
            }
        )
    with pytest.raises(OperationError):
        VerificationClient(tmp_path / "verification.sock", expected_socket_owner_uid=value)
    with pytest.raises(OperationError):
        connect_private(
            tmp_path / "verification.sock",
            expected_uid=os.geteuid(),
            expected_socket_owner_uid=value,
            timeout_seconds=0.1,
        )


@pytest.mark.parametrize("owner", [None, 0, 981])
def test_api_lifespan_constructs_original_client_with_separate_owner(configured, owner):
    data, _policy, archive, lock = configured
    data["verification"] = {"expected_peer_uid": 0, "expected_socket_owner_uid": owner}
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def inspect():
        async with app.router.lifespan_context(app):
            client = app.state.verifier
            assert isinstance(client, VerificationClient)
            assert client.expected_uid == 0
            assert client.expected_socket_owner_uid == (0 if owner is None else owner)
            assert not archive.exists()

    asyncio.run(inspect())
