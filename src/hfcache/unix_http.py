"""Own Unix socket lifetimes through public HTTPX/HTTPCore interfaces (decision 119).

HTTPCore 1.0.9's synchronous Unix backend does not close failed connections.
Keep HTTP parsing/pooling in HTTPCore while making every socket transfer explicit;
the independent TCP/TLS transport continues to use HTTPX's implementation.
"""

import select
import socket
from contextlib import contextmanager
from typing import TYPE_CHECKING

import httpcore
import httpx

if TYPE_CHECKING:
    import ssl
    from collections.abc import Iterable, Iterator
    from pathlib import Path

_ERRORS = {
    httpcore.ConnectTimeout: httpx.ConnectTimeout,
    httpcore.ReadTimeout: httpx.ReadTimeout,
    httpcore.WriteTimeout: httpx.WriteTimeout,
    httpcore.PoolTimeout: httpx.PoolTimeout,
    httpcore.ConnectError: httpx.ConnectError,
    httpcore.ReadError: httpx.ReadError,
    httpcore.WriteError: httpx.WriteError,
    httpcore.LocalProtocolError: httpx.LocalProtocolError,
    httpcore.RemoteProtocolError: httpx.RemoteProtocolError,
    httpcore.UnsupportedProtocol: httpx.UnsupportedProtocol,
    httpcore.TimeoutException: httpx.TimeoutException,
    httpcore.NetworkError: httpx.NetworkError,
    httpcore.ProtocolError: httpx.ProtocolError,
}


@contextmanager
def _mapped_errors() -> Iterator[None]:
    try:
        yield
    except tuple(_ERRORS) as error:
        mapped = next(value for key, value in _ERRORS.items() if isinstance(error, key))
        message = "Unix API transport failed"
        raise mapped(message) from error


class UnixStream(httpcore.NetworkStream):
    """A connected, plaintext-only descriptor, owned until explicitly closed."""

    def __init__(self, channel: socket.socket) -> None:
        self.channel = channel

    def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        try:
            self.channel.settimeout(timeout)
            return self.channel.recv(max_bytes)
        except TimeoutError as error:
            self.close()
            raise httpcore.ReadTimeout from error
        except OSError as error:
            self.close()
            raise httpcore.ReadError from error
        except BaseException:
            self.close()
            raise

    def write(self, buffer: bytes, timeout: float | None = None) -> None:
        try:
            self.channel.settimeout(timeout)
            self.channel.sendall(buffer)
        except TimeoutError as error:
            self.close()
            raise httpcore.WriteTimeout from error
        except OSError as error:
            self.close()
            raise httpcore.WriteError from error
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        self.channel.close()

    def start_tls(
        self,
        ssl_context: ssl.SSLContext,
        server_hostname: str | None = None,
        timeout: float | None = None,
    ) -> httpcore.NetworkStream:
        del ssl_context, server_hostname, timeout
        self.close()
        message = "Unix API transport permits plaintext local sockets only"
        raise httpcore.UnsupportedProtocol(message)

    def get_extra_info(self, info: str) -> object:
        if info == "socket":
            return self.channel
        if info == "is_readable":
            if self.channel.fileno() < 0:
                return True
            return bool(select.select([self.channel], [], [], 0)[0])
        return None


class UnixBackend(httpcore.NetworkBackend):
    """Connect only to the selected local socket, with no IP fallback."""

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.NetworkStream:
        del host, port, timeout, local_address, socket_options
        message = "Unix API transport cannot connect to an IP endpoint"
        raise httpcore.ConnectError(message)

    def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.NetworkStream:
        channel = None
        try:
            channel = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            for option in socket_options or ():
                channel.setsockopt(*option)
            channel.settimeout(timeout)
            channel.connect(path)
            return UnixStream(channel)
        except TimeoutError as error:
            if channel is not None:
                channel.close()
            raise httpcore.ConnectTimeout from error
        except OSError as error:
            if channel is not None:
                channel.close()
            raise httpcore.ConnectError from error
        except BaseException:
            if channel is not None:
                channel.close()
            raise


class _ResponseStream(httpx.SyncByteStream):
    def __init__(self, response: httpcore.Response) -> None:
        self.response = response

    def __iter__(self) -> Iterator[bytes]:
        try:
            with _mapped_errors():
                yield from self.response.iter_stream()
        finally:
            self.close()

    def close(self) -> None:
        with _mapped_errors():
            self.response.close()


class UnixHTTPTransport(httpx.BaseTransport):
    """Adapt public streaming models; HTTPCore owns connection reuse and HTTP/1.1."""

    def __init__(self, path: Path, *, limits: httpx.Limits) -> None:
        self.pool = httpcore.ConnectionPool(
            uds=str(path),
            network_backend=UnixBackend(),
            max_connections=limits.max_connections,
            max_keepalive_connections=limits.max_keepalive_connections,
            keepalive_expiry=limits.keepalive_expiry,
            retries=0,
            http1=True,
            http2=False,
        )

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if request.url.raw_scheme != b"http":
            message = "Unix API transport permits plaintext local sockets only"
            raise httpx.UnsupportedProtocol(message)
        outgoing = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )
        with _mapped_errors():
            incoming = self.pool.handle_request(outgoing)
        try:
            return httpx.Response(
                incoming.status,
                headers=incoming.headers,
                stream=_ResponseStream(incoming),
                extensions=incoming.extensions,
            )
        except BaseException:
            incoming.close()
            raise

    def close(self) -> None:
        with _mapped_errors():
            self.pool.close()
