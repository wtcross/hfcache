"""Decision150 real Unix framing, original-peer and descriptor ownership tests."""

import array
import io
import json
import os
import socket
import struct
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import pytest

from hfcache import host_protocol as protocol


@contextmanager
def channels():
    first, second = socket.socketpair()
    protocol.configure_listener(first)
    protocol.configure_listener(second)
    try:
        yield first, second
    finally:
        first.close()
        second.close()


def frame(value):
    body = json.dumps(value).encode()
    return struct.pack("!I", len(body)) + body


def request():
    return protocol.HostRequest("a" * 32, "status")


def fd_count():
    return len(list(Path("/proc/self/fd").iterdir()))


def test_real_exchange_reauthenticates_same_original_peer_and_exact_reply():
    observed = []
    with channels() as (server, client):
        client.sendall(frame(request().wire()))
        client.shutdown(socket.SHUT_WR)

        def authenticate(peer, seconds):
            assert peer.credentials == protocol.PeerCredentials(
                os.getpid(), os.getuid(), os.getgid()
            )
            assert not os.get_inheritable(peer.pidfd)
            peer.check()
            observed.append(seconds)
            return len(observed)

        before = fd_count()
        with protocol.receive_exchange(server, authenticate) as exchange:
            assert exchange.dispatch(lambda _req, authority, _left: authority) == 2
            exchange.respond(outcome="ok", body={"actual": True})
        reply = protocol.receive_frame(
            client,
            deadline=time.monotonic() + 1,
            expected=protocol.PeerCredentials.from_socket(client),
        )
        assert protocol.reply_body(reply, request()) == {"actual": True}
        assert len(observed) == 2
        assert 0 < observed[1] <= observed[0] <= 15
        assert fd_count() == before


@pytest.mark.parametrize(
    "body",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e9999}',
        b'{"x":9223372036854775808}',
        b'{"x":-9223372036854775809}',
        b'{"x":' + b"1" * 129 + b"}",
        b'{"x":"\\ud800"}',
        b'{"x":"\xff"}',
        b"[]",
        b"null",
        b'{"x":' + b"[" * 32 + b"0" + b"]" * 32 + b"}",
        b'{"x":[' + b"0," * 100000 + b"0]}",
    ],
)
def test_strict_json_rejects_before_model_validation(body):
    with pytest.raises(protocol.HostProtocolError, match="invalid-request"):
        protocol.decode_object(body)


def test_json_limits_preserve_finite_values_and_unicode():
    value: dict[str, object] = {"x": [-(2**63), 2**63 - 1, 1.25, True, None, "é💾"]}
    assert protocol.decode_object(protocol.encode_object(value)) == value


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": True},
        {"request_id": "A" * 32},
        {"operation": "schedule-change"},
        {"operation": "config-apply"},
        {"body": {"path": "/etc/passwd"}},
        {"extra": None},
    ],
)
def test_request_is_closed_and_only_two_read_operations(change):
    with pytest.raises(protocol.HostProtocolError):
        protocol.HostRequest.parse(request().wire() | change)


@pytest.mark.parametrize("wire", [b"", b"\x00\x00", b"\x00\x00\x00\x00", b"\x00\x20\x00\x01"])
def test_early_eof_and_invalid_length_refuse_without_dispatch(wire):
    with channels() as (server, client):
        client.sendall(wire)
        client.shutdown(socket.SHUT_WR)
        baseline = fd_count()
        with pytest.raises(protocol.HostProtocolError):
            protocol.receive_exchange(server, lambda _peer, _seconds: None)
        assert fd_count() == baseline


def test_trailing_frame_refuses_before_second_auth_or_dispatch():
    authenticated = []
    with channels() as (server, client):
        client.sendall(frame(request().wire()) * 2)
        client.shutdown(socket.SHUT_WR)
        with pytest.raises(protocol.HostProtocolError):
            protocol.receive_exchange(server, lambda peer, _seconds: authenticated.append(peer))
    assert len(authenticated) == 1


def test_inherited_socket_writer_is_not_original_peer():
    with channels() as (server, client):
        code = (
            "import socket,os; s=socket.socket(fileno=int(os.environ['OWNED_FD']));"
            "s.sendall(bytes.fromhex(os.environ['OWNED_FRAME'])); s.shutdown(socket.SHUT_WR)"
        )
        completed = subprocess.run(
            [sys.executable, "-I", "-c", code],
            pass_fds=(client.fileno(),),
            env={"OWNED_FD": str(client.fileno()), "OWNED_FRAME": frame(request().wire()).hex()},
            capture_output=True,
            timeout=3,
            check=False,
        )
        assert completed.returncode == 0
        with pytest.raises(protocol.HostProtocolError, match="peer-refused"):
            protocol.receive_exchange(server, lambda _peer, _seconds: None)


def test_rights_are_closed_on_real_recvmsg_refusal(tmp_path):
    with channels() as (server, client), (tmp_path / "owned").open("wb") as owned:
        descriptors = array.array("i", [owned.fileno()])
        baseline = fd_count()
        client.sendmsg(
            [frame(request().wire())], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, descriptors)]
        )
        client.shutdown(socket.SHUT_WR)
        with pytest.raises(protocol.HostProtocolError, match="peer-refused"):
            protocol.receive_exchange(server, lambda _peer, _seconds: None)
        assert fd_count() == baseline
        os.fstat(owned.fileno())


def test_all_known_descriptors_closed_before_unknown_control_refusal(tmp_path):
    original = os.open(tmp_path / "owned", os.O_CREAT | os.O_WRONLY, 0o600)
    first, second = os.dup(original), os.dup(original)
    try:
        controls = [
            (socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [first]).tobytes()),
            (socket.SOL_SOCKET, 9999, array.array("i", [original]).tobytes()),
            (socket.SOL_SOCKET, protocol.SCM_PIDFD, array.array("i", [second]).tobytes()),
        ]
        with pytest.raises(protocol.HostProtocolError):
            protocol._ancillary(controls, socket.MSG_CTRUNC)
        for closed in (first, second):
            with pytest.raises(OSError, match="Bad file descriptor"):
                os.fstat(closed)
        os.fstat(original)  # Unknown bytes must never be interpreted as an FD.
    finally:
        os.close(original)


def test_eof_synthetic_credentials_do_not_authenticate_a_writer():
    empty_cookie = [
        (socket.SOL_SOCKET, socket.SCM_CREDENTIALS, struct.pack("=iII", 0, 65534, 65534))
    ]
    assert protocol._ancillary(empty_cookie, 0) == [protocol.PeerCredentials(0, 65534, 65534)]
    with channels() as (server, client):
        client.sendall(frame(request().wire()))
        client.shutdown(socket.SHUT_WR)
        assert (
            protocol.receive_frame(
                server,
                deadline=time.monotonic() + 1,
                expected=protocol.PeerCredentials.from_socket(server),
            )
            == request().wire()
        )


def test_receive_budget_is_absolute_across_fragments():
    failures = []
    with channels() as (server, client):

        def read():
            try:
                protocol.receive_frame(
                    server,
                    deadline=time.monotonic() + 0.08,
                    expected=protocol.PeerCredentials.from_socket(server),
                )
            except protocol.HostProtocolError as error:
                failures.append(error.reason)

        reader = threading.Thread(target=read)
        reader.start()
        for piece in (b"\x00", b"\x00", b"\x00"):
            client.sendall(piece)
            time.sleep(0.035)
        reader.join(timeout=1)
        assert not reader.is_alive()
        assert failures == ["timeout"]


def test_authentication_and_dispatch_share_one_inspection_budget(monkeypatch):
    monkeypatch.setattr(protocol, "INSPECTION_SECONDS", 0.06)
    calls = []
    with channels() as (server, client):
        client.sendall(frame(request().wire()))
        client.shutdown(socket.SHUT_WR)

        def authenticate(peer, seconds):
            calls.append(seconds)
            time.sleep(0.035)

        with (
            protocol.receive_exchange(server, authenticate) as exchange,
            pytest.raises(protocol.HostProtocolError, match="timeout"),
        ):
            exchange.dispatch(lambda *_: pytest.fail("inspection overrun must not dispatch"))
    assert len(calls) == 2
    assert calls[1] < calls[0]


def test_original_peer_pidfd_zero_is_owned_and_closed():
    code = """
import os,socket
from hfcache.host_protocol import LivePeer
a,b=socket.socketpair()
os.close(0)
p=LivePeer(a)
if p.pidfd != 0 or os.get_inheritable(0): raise RuntimeError('owned pidfd')
p.close()
try: os.fstat(0)
except OSError: pass
else: raise RuntimeError('pidfd leaked')
a.close();b.close()
"""
    completed = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, check=False, timeout=3
    )
    assert completed.returncode == 0, completed.stderr.decode()


@pytest.mark.parametrize(
    "change", [{"request_id": "b" * 32}, {"operation": "config-read"}, {"extra": 1}]
)
def test_response_identity_and_closed_envelope(change):
    reply = request().wire() | {"outcome": "ok", "reason": None}
    with pytest.raises(protocol.HostProtocolError):
        protocol.reply_body(reply | change, request())


def test_denial_retains_fixed_reason_without_raw_message():
    reply = request().wire() | {"outcome": "denied", "reason": "operation-denied"}
    with pytest.raises(protocol.HostProtocolError, match=r"^operation-denied$"):
        protocol.reply_body(reply, request())


def test_original_peer_exit_invalidates_retained_pidfd(tmp_path):
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    protocol.configure_listener(listener)
    path = tmp_path / "peer.sock"
    listener.bind(str(path))
    listener.listen(1)
    listener.settimeout(3)
    code = (
        "import socket,sys; s=socket.socket(socket.AF_UNIX);"
        "s.connect(sys.argv[1]);sys.stdin.buffer.read()"
    )
    with subprocess.Popen(
        [sys.executable, "-I", "-c", code, str(path)], stdin=subprocess.PIPE
    ) as child:
        connection, _ = listener.accept()
        try:
            peer = protocol.LivePeer(connection)
            assert peer.credentials.pid == child.pid
            assert child.stdin is not None
            child.stdin.close()
            assert child.wait(timeout=3) == 0
            with pytest.raises(protocol.HostProtocolError, match="peer-refused"):
                peer.check()
            peer.close()
        finally:
            connection.close()
            listener.close()


def test_unsupported_peerpidfd_refuses_without_numeric_pid_fallback():
    class Unsupported:
        def getsockopt(self, level, option, size=None):
            if option == protocol.SO_PEERPIDFD:
                message = "unsupported kernel unit case"
                raise OSError(message)
            return struct.pack("=iII", os.getpid(), os.getuid(), os.getgid())

    baseline = fd_count()
    with pytest.raises(protocol.HostProtocolError, match="peer-refused"):
        protocol.LivePeer(cast("socket.socket", Unsupported()))
    assert fd_count() == baseline


def test_ok_reply_requires_completed_reauthenticated_dispatch():
    with channels() as (server, client):
        client.sendall(frame(request().wire()))
        client.shutdown(socket.SHUT_WR)
        with protocol.receive_exchange(server, lambda *_: None) as exchange:
            with pytest.raises(protocol.HostProtocolError, match="invalid-request"):
                exchange.respond(outcome="ok", body={})

            def failed_dispatch(*_):
                reason = "policy-invalid"
                raise protocol.HostProtocolError(reason)

            with pytest.raises(protocol.HostProtocolError, match="policy-invalid"):
                exchange.dispatch(failed_dispatch)
            with pytest.raises(protocol.HostProtocolError, match="invalid-request"):
                exchange.respond(outcome="ok", body={})
            exchange.respond(outcome="denied", body={}, reason="policy-invalid")


def test_client_requires_final_eof_within_original_deadline():
    with channels() as (server, client):
        # A complete valid reply is insufficient while the server keeps writing open.
        protocol.send_frame(
            server,
            request().wire() | {"outcome": "ok", "reason": None},
            deadline=time.monotonic() + 1,
        )
        with pytest.raises(protocol.HostProtocolError, match="timeout"):
            protocol.client_exchange(
                client,
                request(),
                deadline=time.monotonic() + 0.03,
                expected=protocol.PeerCredentials.from_socket(client),
            )


def test_decode_cannot_return_after_receive_deadline(monkeypatch):
    original_decode = protocol.decode_object
    late = False

    def delayed_decode(data):
        nonlocal late
        value = original_decode(data)
        late = True
        return value

    monkeypatch.setattr(protocol, "decode_object", delayed_decode)
    monkeypatch.setattr(protocol.time, "monotonic", lambda: 101.0 if late else 100.0)
    with channels() as (server, client):
        client.sendall(frame(request().wire()))
        client.shutdown(socket.SHUT_WR)
        with pytest.raises(protocol.HostProtocolError, match="timeout"):
            protocol.receive_frame(
                server, deadline=100.5, expected=protocol.PeerCredentials.from_socket(server)
            )


def test_projected_root_pidfd_is_explicit_consistency_not_server_identity(monkeypatch):
    """Real original pidfd/poll, projected namespace metadata unit seam only."""
    monkeypatch.setattr(
        protocol.PeerCredentials,
        "from_socket",
        classmethod(lambda _cls, _socket: protocol.PeerCredentials(0, 65534, 65534)),
    )
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: io.BytesIO(b"Pid:\t0\n"))
    with channels() as (server, _):
        with pytest.raises(protocol.HostProtocolError, match="peer-refused"):
            protocol.LivePeer(server)
        peer = protocol.LivePeer(server, allow_projected_root=True)
        try:
            peer.check()
            assert not os.get_inheritable(peer.pidfd)
        finally:
            peer.close()


@pytest.mark.parametrize("peer", [(1, 65534, 65534), (0, 0, 0), (0, 65534, 981)])
def test_projected_pidfd_mode_has_no_uid_or_pid_wildcard(monkeypatch, peer):
    monkeypatch.setattr(
        protocol.PeerCredentials,
        "from_socket",
        classmethod(lambda _cls, _socket: protocol.PeerCredentials(*peer)),
    )
    with channels() as (server, _), pytest.raises(protocol.HostProtocolError, match="peer-refused"):
        protocol.LivePeer(server, allow_projected_root=True)
