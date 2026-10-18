"""Single-process Unix/TCP bootstrap; optional server dependencies stay lazy.

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


@contextmanager
def listeners(policy: ListenerConfig) -> Iterator[list[socket.socket]]:
    """Bind configured addresses without adopting or unlinking an existing path.

    A pinned parent fd protects the socket path from ancestor swaps. Cleanup is
    limited to the exact socket inode created here; a replaced name is retained.
    Runtime directories are provisioned by the operator, never by archive init.
    """
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


def run(path: Path) -> None:
    """Serve an explicitly configured daemon; no archive mutation at startup."""
    policy = load_server_config(path)
    try:
        server = build_server(create_app(policy), policy)
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
