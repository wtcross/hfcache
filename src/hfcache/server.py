"""Single-process activated or foreground Unix/TCP bootstrap (decision 121).

One Uvicorn instance and lifespan own both listeners. Its small startup override
applies direct TLS only to TCP; the local Unix socket never acquires IP egress.
No listener is opened by importing this module (decision 113).
"""

import asyncio
import logging
import os
import socket
import stat
from contextlib import contextmanager
from typing import TYPE_CHECKING, cast

import uvicorn

from hfcache.api.app import create_app
from hfcache.api.lifecycle import open_directory
from hfcache.errors import HfcacheError, SafetyError
from hfcache.server_config import load_server_config

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from fastapi import FastAPI
    from starlette.types import Receive, Scope, Send

    from hfcache.server_config import ListenerConfig, ServerConfig

_ACTIVATION_START = 3
_ACTIVATION_NAME = "hfcache-api"
_ACTIVATION_ENVIRONMENT = ("LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES", "LISTEN_PIDFDID")


def _activation_count(policy: ListenerConfig) -> int | None:
    """An incomplete activation never falls back to binding another listener."""
    if not any(name in os.environ for name in _ACTIVATION_ENVIRONMENT):
        return None
    count = int(policy.unix_address is not None) + int(policy.tcp_address is not None)
    if (
        os.environ.get("LISTEN_PID") != str(os.getpid())
        or os.environ.get("LISTEN_FDS") != str(count)
        or os.environ.get("LISTEN_FDNAMES") != ":".join([_ACTIVATION_NAME] * count)
    ):
        message = "socket activation does not match the configured listeners"
        raise ValueError(message)
    if (identity := os.environ.get("LISTEN_PIDFDID")) is not None:
        descriptor = os.pidfd_open(os.getpid())
        try:
            if identity != str(os.fstat(descriptor).st_ino):
                message = "socket activation does not identify this process"
                raise ValueError(message)
        finally:
            os.close(descriptor)
    return count


def _activated_unix(policy: ListenerConfig, channel: socket.socket) -> None:
    if policy.unix_address is None:
        message = "activated Unix listener is disabled by server policy"
        raise ValueError(message)
    parent = open_directory(policy.unix_socket.parent)
    try:
        directory = os.fstat(parent)
        info = os.stat(policy.unix_socket.name, dir_fd=parent, follow_symlinks=False)
        if (
            channel.getsockname() != str(policy.unix_socket)
            or not stat.S_ISSOCK(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_gid not in {os.getegid(), *os.getgroups()}
            or stat.S_IMODE(info.st_mode) != policy.socket_mode
            or directory.st_uid not in {0, os.geteuid()}
            or stat.S_IMODE(directory.st_mode) & 0o022
        ):
            message = "activated Unix listener does not match its protected configured path"
            raise ValueError(message)
    finally:
        os.close(parent)


def _activated_tcp(policy: ListenerConfig, channel: socket.socket) -> None:
    if policy.tcp_address is None:
        message = "activated TCP listener is disabled by server policy"
        raise ValueError(message)
    host, port = policy.tcp_address
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    expected = socket.getaddrinfo(
        host,
        port,
        family=family,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
        flags=socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
    )[0][4]
    if (
        channel.family != family
        or channel.getsockname() != expected
        or (
            family == socket.AF_INET6
            and channel.getsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY) != 1
        )
    ):
        message = "activated TCP listener does not match its configured address"
        raise ValueError(message)


@contextmanager
def _activated_listeners(policy: ListenerConfig, count: int) -> Iterator[list[socket.socket]]:
    """Adopt only declared listeners; the manager retains their path and lifetime."""
    opened: list[socket.socket] = []
    seen: set[str] = set()
    try:
        for descriptor in range(_ACTIVATION_START, _ACTIVATION_START + count):
            channel = socket.socket(fileno=descriptor)
            opened.append(channel)
            if channel.getsockopt(
                socket.SOL_SOCKET, socket.SO_TYPE
            ) != socket.SOCK_STREAM or not channel.getsockopt(
                socket.SOL_SOCKET, socket.SO_ACCEPTCONN
            ):
                message = "activation requires listening stream sockets"
                raise ValueError(message)
            if channel.family == socket.AF_UNIX:
                identity = "unix"
                _activated_unix(policy, channel)
            elif channel.family in {socket.AF_INET, socket.AF_INET6}:
                identity = "tcp"
                _activated_tcp(policy, channel)
            else:
                message = "activated socket family is unsupported"
                raise ValueError(message)
            if identity in seen:
                message = "activation contains a duplicate listener"
                raise ValueError(message)
            seen.add(identity)
            channel.set_inheritable(False)
            channel.setblocking(False)  # noqa: FBT003 - socket API has positional-only flag
        for name in _ACTIVATION_ENVIRONMENT:
            os.environ.pop(name, None)
        yield opened
    finally:
        # close(), never shutdown(): manager descriptors share the same sockets.
        for channel in opened:
            channel.close()


@contextmanager
def listeners(policy: ListenerConfig) -> Iterator[list[socket.socket]]:
    """Adopt manager sockets or explicitly bind foreground development listeners.

    Activation is all-or-nothing and never falls back to creating a listener.
    """
    if (count := _activation_count(policy)) is not None:
        with _activated_listeners(policy, count) as activated:
            yield activated
    else:
        with _foreground_listeners(policy) as opened:
            yield opened


@contextmanager
def _foreground_listeners(policy: ListenerConfig) -> Iterator[list[socket.socket]]:
    """Bind with pinned parents and clean only the exact inode created here."""
    opened: list[socket.socket] = []
    parent = None
    owned = None
    name = policy.unix_socket.name
    try:
        if policy.unix_address is not None:
            parent = open_directory(policy.unix_socket.parent)
            local = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            opened.append(local)
            # Startup precedes workers. Prevent any world-connectable bind window.
            previous = os.umask(0o177)
            try:
                local.bind(f"/proc/self/fd/{parent}/{name}")
            finally:
                os.umask(previous)
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            owned = (info.st_dev, info.st_ino)
            os.chmod(name, policy.socket_mode, dir_fd=parent, follow_symlinks=False)
            local.setblocking(False)  # noqa: FBT003 - socket API has positional-only flag
        if policy.tcp_address is not None:
            host, port = policy.tcp_address
            family = socket.AF_INET6 if ":" in host else socket.AF_INET
            tcp = socket.socket(family, socket.SOCK_STREAM)
            opened.append(tcp)
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if family == socket.AF_INET6:
                tcp.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            tcp.bind((host, port))
            tcp.setblocking(False)  # noqa: FBT003 - socket API has positional-only flag
        yield opened
    finally:
        for channel in opened:
            channel.close()
        if parent is not None:
            try:
                if owned is not None:
                    try:
                        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
                    except FileNotFoundError:
                        pass
                    else:
                        if stat.S_ISSOCK(info.st_mode) and (info.st_dev, info.st_ino) == owned:
                            os.unlink(name, dir_fd=parent)
            finally:
                os.close(parent)


class StartupErrors:
    """Keep typed lifespan failures that Uvicorn otherwise reports as a flag."""

    def __init__(self, application: FastAPI) -> None:
        self.application = application
        self.error: HfcacheError | None = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await self.application(scope, receive, send)
        except HfcacheError as error:
            if scope["type"] == "lifespan":
                self.error = error
            raise


class ListenerServer(uvicorn.Server):
    """Uvicorn 0.54 lifecycle with one TLS choice per prebound socket."""

    def __init__(self, config: uvicorn.Config, startup_errors: StartupErrors) -> None:
        super().__init__(config)
        self.startup_errors = startup_errors

    async def startup(self, sockets: list[socket.socket] | None = None) -> None:
        if not sockets:
            message = "server bootstrap requires explicit listeners"
            raise ValueError(message)
        self.servers = []
        await self.lifespan.startup()
        if self.lifespan.should_exit:
            self.should_exit = True
            return
        config = self.config

        def protocol() -> asyncio.Protocol:
            protocol_class = cast("Callable[..., asyncio.Protocol]", config.http_protocol_class)
            return protocol_class(
                config=config,
                server_state=self.server_state,
                app_state=self.lifespan.state,
            )

        try:
            for channel in sockets:
                self.servers.append(
                    await asyncio.get_running_loop().create_server(
                        protocol,
                        sock=channel,
                        ssl=None if channel.family == socket.AF_UNIX else config.ssl,
                        backlog=config.backlog,
                    )
                )
        except BaseException:
            for server in self.servers:
                server.close()
                await server.wait_closed()
            await self.lifespan.shutdown()
            raise
        self.started = True


def build_server(application: FastAPI, policy: ServerConfig) -> ListenerServer:
    """Configure a single worker with request-data-free framework diagnostics."""
    # Uvicorn protocol errors/access/trace logging can echo URLs or raw headers.
    # The application emits its own sanitized problems and correlation metadata.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi"):
        logger = logging.getLogger(name)
        logger.disabled = True
        logger.setLevel(logging.CRITICAL + 1)
    tls = policy.listener.tls
    startup_errors = StartupErrors(application)
    return ListenerServer(
        uvicorn.Config(
            startup_errors,
            workers=1,
            log_config=None,
            access_log=False,
            proxy_headers=False,
            server_header=False,
            ws="none",
            lifespan="on",
            http="h11",
            loop="asyncio",
            timeout_graceful_shutdown=policy.limits.shutdown_timeout_seconds,
            ssl_certfile=tls.certificate if tls is not None else None,
            ssl_keyfile=tls.private_key if tls is not None else None,
            h11_max_incomplete_event_size=32768,
            backlog=128,
        ),
        startup_errors,
    )


def run(path: Path, *, hub_token_file: Path | None = None) -> None:
    """Serve an explicitly configured daemon; no archive mutation at startup."""
    policy = load_server_config(path)
    try:
        server = build_server(create_app(policy, hub_token_file=hub_token_file), policy)
        with listeners(policy.listener) as channels:
            server.run(sockets=channels)
        if not server.started:
            if server.startup_errors.error is not None:
                raise server.startup_errors.error
            message = "server startup failed; check server policy, credentials and instance lock"
            raise SafetyError.single(message, code="HFAPI009")
    except (OSError, ValueError) as exc:
        message = "server listener or TLS setup failed"
        raise SafetyError.single(message, code="HFAPI009") from exc
