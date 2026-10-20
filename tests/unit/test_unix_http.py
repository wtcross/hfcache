"""Unix-only API transport closes descriptors on refusal and streaming exit (119)."""

import errno
import gc
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import httpcore
import httpx
import pytest

from hfcache.http_transport import create_http_client
from hfcache.unix_http import UnixBackend, UnixHTTPTransport, UnixStream


def _descriptors():
    return len(tuple(Path("/proc/self/fd").iterdir()))


@pytest.mark.parametrize("code", [errno.EMFILE, errno.EACCES])
def test_socket_creation_failure_is_a_transport_failure(tmp_path, monkeypatch, code):
    def unavailable(*_args):
        raise OSError(code, "injected socket creation failure")

    # Replace only this module's reference, never the global socket module/factory.
    monkeypatch.setattr(
        "hfcache.unix_http.socket",
        SimpleNamespace(AF_UNIX=socket.AF_UNIX, SOCK_STREAM=socket.SOCK_STREAM, socket=unavailable),
    )
    with (
        create_http_client(unix_socket=tmp_path / "api.sock") as client,
        pytest.raises(httpx.ConnectError),
    ):
        client.get("http://localhost/api/v1/status")


@pytest.mark.parametrize("kind", ["missing", "refused", "long-path", "bad-option"])
def test_failed_unix_connect_closes_descriptor_even_while_traceback_survives(tmp_path, kind):
    path = tmp_path / "api.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as inactive:
        inactive.bind(str(path))
        if kind == "missing":
            path = tmp_path / "missing.sock"
        elif kind == "long-path":
            path = tmp_path / ("x" * 120)
        options = [(socket.SOL_SOCKET, -1, 1)] if kind == "bad-option" else None
        before = _descriptors()
        failures = []
        for _ in range(10):
            try:
                UnixBackend().connect_unix_socket(str(path), timeout=0.01, socket_options=options)
            except httpcore.ConnectError as error:
                failures.append(error)
        assert len(failures) == 10
        assert _descriptors() == before
        failures.clear()
        gc.collect()
        assert _descriptors() == before


def test_full_unix_listen_backlog_closes_failed_connection(tmp_path):
    path = tmp_path / "busy.sock"
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener,
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as queued,
    ):
        listener.bind(str(path))
        listener.listen(0)
        queued.connect(str(path))
        before = _descriptors()
        with pytest.raises(httpcore.ConnectError):
            UnixBackend().connect_unix_socket(str(path), timeout=0.01)
        assert _descriptors() == before


def test_socket_setup_timeout_closes_descriptor_before_exception_is_released(tmp_path):
    class TimedOutOptions:
        def __iter__(self):
            raise TimeoutError

    before = _descriptors()
    with pytest.raises(httpcore.ConnectTimeout):
        UnixBackend().connect_unix_socket(
            str(tmp_path / "absent.sock"), timeout=0.01, socket_options=TimedOutOptions()
        )
    assert _descriptors() == before


@pytest.mark.parametrize("failure", ["missing", "refused"])
def test_real_factory_unavailable_unix_socket_has_no_delayed_resource_warning(tmp_path, failure):
    path = tmp_path / "api.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as inactive:
        if failure == "refused":
            inactive.bind(str(path))
        before = _descriptors()
        failures = []
        with create_http_client(unix_socket=path) as client:
            for _ in range(5):
                try:
                    client.get("http://localhost/api/v1/status")
                except httpx.ConnectError as error:
                    failures.append(error)
        assert len(failures) == 5
        assert _descriptors() == before
        failures.clear()
        gc.collect()
        assert _descriptors() == before


def test_unix_backend_never_falls_back_to_tcp_or_tls(tmp_path):
    with pytest.raises(httpcore.ConnectError):
        UnixBackend().connect_tcp("127.0.0.1", 1)
    with (
        UnixHTTPTransport(tmp_path / "absent.sock", limits=httpx.Limits()) as transport,
        pytest.raises(httpx.UnsupportedProtocol),
    ):
        transport.handle_request(httpx.Request("GET", "https://localhost/api/v1/status"))
    first, second = socket.socketpair()
    with second:
        stream = UnixStream(first)
        with pytest.raises(httpcore.UnsupportedProtocol):
            stream.start_tls(ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
        assert first.fileno() == -1


@pytest.mark.parametrize("kind", ["read-timeout", "read-error", "write-error"])
def test_connected_stream_closes_on_io_failure(kind):
    channel, peer = socket.socketpair()
    with peer:
        stream = UnixStream(channel)
        if kind == "write-error":
            peer.close()
            with pytest.raises(httpcore.WriteError):
                stream.write(b"request", timeout=0.01)
        elif kind == "read-error":
            channel.shutdown(socket.SHUT_RD)
            channel.close()
            with pytest.raises(httpcore.ReadError):
                stream.read(10, timeout=0.01)
        else:
            with pytest.raises(httpcore.ReadTimeout):
                stream.read(10, timeout=0.01)
        assert channel.fileno() == -1
        assert stream.get_extra_info("is_readable") is True


@pytest.mark.parametrize("mode", ["complete", "early-close", "truncated", "timeout"])
def test_real_unix_response_stream_releases_pool_and_connection(tmp_path, mode):
    path = tmp_path / "api.sock"
    release, disconnected = Event(), Event()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        listener.listen(1)
        listener.settimeout(5)

        def server():
            channel, _ = listener.accept()
            with channel:
                channel.settimeout(5)
                request = b""
                while b"\r\n\r\n" not in request:
                    part = channel.recv(4096)
                    assert part
                    request += part
                length = 3 if mode == "complete" else 30
                channel.sendall(
                    f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\n\r\n".encode() + b"abc"
                )
                if mode == "truncated":
                    return
                if mode == "timeout":
                    assert release.wait(5)
                assert channel.recv(1) == b""
                disconnected.set()

        with ThreadPoolExecutor(max_workers=1) as executor:
            work = executor.submit(server)
            try:
                with (
                    create_http_client(unix_socket=path) as client,
                    client.stream("GET", "http://localhost/", timeout=0.05) as response,
                ):
                    chunks = response.iter_bytes()
                    assert next(chunks) == b"abc"
                    if mode == "truncated":
                        with pytest.raises(httpx.RemoteProtocolError):
                            next(chunks)
                    elif mode == "timeout":
                        with pytest.raises(httpx.ReadTimeout):
                            next(chunks)
                    elif mode == "complete":
                        assert list(chunks) == []
                release.set()
                work.result(timeout=5)
            finally:
                release.set()
        if mode != "truncated":
            assert disconnected.is_set()


@pytest.mark.parametrize("truncated", [False, True])
def test_empty_request_body_does_not_discard_an_already_sent_unix_response(
    tmp_path, monkeypatch, truncated
):
    path = tmp_path / "api.sock"
    peer_closed = Event()
    original_write = UnixStream.write
    streams = []

    def write_after_peer_closes(self, buffer, timeout=None):
        if not buffer:
            assert peer_closed.wait(5)
            streams.append(self)
        original_write(self, buffer, timeout)

    monkeypatch.setattr(UnixStream, "write", write_after_peer_closes)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        listener.listen(1)
        listener.settimeout(5)

        def server():
            channel, _ = listener.accept()
            with channel:
                channel.settimeout(5)
                request = b""
                while b"\r\n\r\n" not in request:
                    part = channel.recv(4096)
                    assert part
                    request += part
                length = 30 if truncated else 3
                channel.sendall(
                    f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\n\r\n".encode() + b"abc"
                )
            peer_closed.set()

        before = _descriptors()
        with ThreadPoolExecutor(max_workers=1) as executor:
            work = executor.submit(server)
            try:
                with (
                    create_http_client(unix_socket=path) as client,
                    client.stream("GET", "http://localhost/", timeout=5) as response,
                ):
                    assert response.status_code == 200
                    chunks = response.iter_bytes()
                    assert next(chunks) == b"abc"
                    if truncated:
                        with pytest.raises(httpx.RemoteProtocolError):
                            next(chunks)
                    else:
                        assert list(chunks) == []
            finally:
                work.result(timeout=5)
        assert streams
        assert all(stream.channel.fileno() == -1 for stream in streams)
        assert _descriptors() == before
