"""Decision150 pinned host endpoint and independent bounded client execution.

Only protected startup facts establish an endpoint. A reply, overflow UID or a
file learned from an untrusted listener cannot establish its own provenance.
This module and host_protocol use only the standard library on Python3.12.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
import re
import secrets
import socket
import stat
import threading
import time
import uuid
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, cast

from hfcache.host_protocol import (
    CLIENT_SECONDS,
    MAX_EXCHANGES,
    HostProtocolError,
    HostRequest,
    LivePeer,
    PeerCredentials,
    client_exchange,
    decode_object,
    encode_object,
    remaining,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

_PARENT = Path("/run/hfcache-host-helper/api")
_SOCKET = "helper.sock"
_BINDING = "binding.json"
_ENVIRONMENT = "HFCACHE_HOST_HELPER_PARENT"
_MAX_BINDING = 4096
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_HEX32 = re.compile(r"[0-9a-f]{32}\Z")
_PROJECTED_UID = 65534
_PROJECTED_GID = 981
_DEPLOYMENT = "deployment-unverified"
_UNAVAILABLE = "facts-unavailable"
_TIMEOUT = "timeout"
_BUSY = "busy"
_INVALID = "invalid-request"
_BINDING_MODE = 0o440
_SOCKET_MODE = 0o660
_DIRECTORY_MODE = 0o750


def _request_body(operation: str, body: dict[str, object]) -> dict[str, object]:
    """Freeze bounded caller data before reserving or queueing a worker."""
    request = HostRequest("0" * 32, operation, body)
    return HostRequest.parse(decode_object(encode_object(request.wire()))).body


def _need(condition: object) -> None:
    if not condition:
        raise HostProtocolError(_DEPLOYMENT)


def _number(value: object, *, minimum: int = 0) -> int:
    _need(type(value) is int and value >= minimum)
    return cast("int", value)


def _digest(value: object) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None)
    return cast("str", value)


def _boot(value: object) -> str:
    _need(type(value) is str)
    try:
        _need(str(uuid.UUID(cast("str", value))) == value)
    except (ValueError, AttributeError):
        raise HostProtocolError(_DEPLOYMENT) from None
    return cast("str", value)


def _record(value: object) -> dict[str, object]:
    _need(type(value) is dict)
    return cast("dict[str, object]", value)


def _metadata(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_uid,
        info.st_gid,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _directory(info: os.stat_result, *, uid: int, gid: int | None = None) -> None:
    _need(stat.S_ISDIR(info.st_mode) and info.st_uid == uid)
    _need(not stat.S_IMODE(info.st_mode) & 0o022)
    if gid is not None:
        _need(info.st_gid == gid and stat.S_IMODE(info.st_mode) == _DIRECTORY_MODE)


def _open_parent(profile: str, api_host_gid: int) -> int:
    descriptor = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        _directory(os.fstat(descriptor), uid=0)
        components = _PARENT.parts[1:]
        for index, component in enumerate(components):
            child = os.open(
                component,
                os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
            if index == len(components) - 1:
                _directory(
                    os.fstat(descriptor),
                    uid=_PROJECTED_UID if profile == "rootless" else 0,
                    gid=_PROJECTED_GID if profile == "rootless" else api_host_gid,
                )
            else:
                _directory(os.fstat(descriptor), uid=0)
    except BaseException:
        os.close(descriptor)
        raise
    else:
        return descriptor


class EndpointBinding:
    """An API-lifetime pinned directory established before any helper request."""

    def __init__(
        self,
        *,
        profile: str,
        deployment_sha256: str | None = None,
        api_host_gid: int,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._parent = -1
        _need(profile in {"native", "rootless"})
        self.profile = profile
        expected_deployment = None if deployment_sha256 is None else _digest(deployment_sha256)
        self.api_host_gid = _number(api_host_gid, minimum=1)
        source = os.environ if environment is None else environment
        attestation: dict[str, object] | None = None
        if profile == "rootless":
            raw = source.get(_ENVIRONMENT)
            _need(type(raw) is str)
            try:
                attestation = decode_object(cast("str", raw).encode("utf-8"), maximum=_MAX_BINDING)
            except (HostProtocolError, UnicodeError):
                raise HostProtocolError(_DEPLOYMENT) from None
            attested_deployment = _digest(attestation.get("deployment_sha256"))
            self.deployment_sha256 = expected_deployment or attested_deployment
            self._validate_attestation(attestation)
        else:
            _need(_ENVIRONMENT not in source)
        try:
            self._parent = _open_parent(profile, api_host_gid)
            info = os.fstat(self._parent)
            self.parent_identity = (info.st_dev, info.st_ino)
            if attestation is not None:
                parent = _record(attestation["parent"])
                _need((parent["device"], parent["inode"]) == self.parent_identity)
                self.boot_id = _boot(attestation["boot_id"])
            else:
                # The API's ProcSubset hides /proc/sys; only this independently
                # root-protected current-/run startup binding supplies its boot.
                startup = self._read_binding()
                self.boot_id = _boot(startup["boot_id"])
                self.deployment_sha256 = expected_deployment or _digest(
                    startup["deployment_sha256"]
                )
            self._runtime_binding()
        except BaseException:
            self.close()
            raise

    @classmethod
    def from_startup(
        cls,
        *,
        profile: str,
        deployment_sha256: str | None = None,
        api_host_gid: int,
        environment: Mapping[str, str] | None = None,
    ) -> EndpointBinding:
        return cls(
            profile=profile,
            deployment_sha256=deployment_sha256,
            api_host_gid=api_host_gid,
            environment=environment,
        )

    def _validate_attestation(self, value: dict[str, object]) -> None:
        _need(
            set(value)
            == {"schema_version", "profile", "deployment_sha256", "boot_id", "parent", "peer"}
        )
        _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
        _need(
            value["profile"] == "rootless" and value["deployment_sha256"] == self.deployment_sha256
        )
        _boot(value["boot_id"])
        parent = _record(value["parent"])
        _need(type(parent) is dict and set(parent) == {"device", "inode", "uid", "gid", "mode"})
        _number(parent["device"], minimum=1)
        _number(parent["inode"], minimum=1)
        _need(
            parent["uid"] == _PROJECTED_UID
            and parent["gid"] == _PROJECTED_GID
            and parent["mode"] == _DIRECTORY_MODE
            and all(type(parent[key]) is int for key in ("uid", "gid", "mode"))
        )
        peer = _record(value["peer"])
        _need(type(peer) is dict and set(peer) == {"pid", "uid", "gid"})
        _need(peer == {"pid": 0, "uid": _PROJECTED_UID, "gid": _PROJECTED_UID})
        _need(all(type(number) is int for number in peer.values()))

    def _read_binding(self) -> dict[str, object]:
        descriptor = os.open(
            _BINDING,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=self._parent,
        )
        try:
            before = os.fstat(descriptor)
            _need(
                stat.S_ISREG(before.st_mode)
                and before.st_nlink == 1
                and before.st_uid == (_PROJECTED_UID if self.profile == "rootless" else 0)
                and before.st_gid
                == (_PROJECTED_GID if self.profile == "rootless" else self.api_host_gid)
                and stat.S_IMODE(before.st_mode) == _BINDING_MODE
                and 1 <= before.st_size <= _MAX_BINDING
            )
            data = os.read(descriptor, _MAX_BINDING + 1)
            _need(
                len(data) == before.st_size and _metadata(os.fstat(descriptor)) == _metadata(before)
            )
            current = os.stat(_BINDING, dir_fd=self._parent, follow_symlinks=False)
            _need(_metadata(current) == _metadata(before))
            return decode_object(data, maximum=_MAX_BINDING)
        finally:
            os.close(descriptor)

    def _runtime_binding(self) -> dict[str, object]:
        value = self._read_binding()
        _need(
            set(value)
            == {
                "schema_version",
                "boot_id",
                "helper_generation",
                "deployment_sha256",
                "policy_sha256",
                "parent",
                "helper",
            }
        )
        _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
        _need(_boot(value["boot_id"]) == self.boot_id)
        _need(value["deployment_sha256"] == self.deployment_sha256)
        _digest(value["policy_sha256"])
        generation = value["helper_generation"]
        _need(type(generation) is str and _HEX32.fullmatch(generation) is not None)
        parent = _record(value["parent"])
        _need(type(parent) is dict and set(parent) == {"device", "inode", "uid", "gid", "mode"})
        _need(all(type(number) is int for number in parent.values()))
        _need(
            (parent["device"], parent["inode"]) == self.parent_identity
            and parent["uid"] == 0
            and parent["gid"] == self.api_host_gid
            and parent["mode"] == _DIRECTORY_MODE
        )
        helper = _record(value["helper"])
        _need(type(helper) is dict and set(helper) == {"pid", "start_ticks", "uid", "gid"})
        _number(helper["pid"], minimum=2)
        _number(helper["start_ticks"], minimum=1)
        _need(type(helper["uid"]) is int and helper["uid"] == 0)
        _need(type(helper["gid"]) is int and helper["gid"] == 0)
        return value

    def connect(
        self, *, deadline: float, own_socket: Callable[[socket.socket], None]
    ) -> tuple[socket.socket, LivePeer | None, PeerCredentials]:
        """Check both fixed pathname reachability and pinned-FD identity each time."""
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        peer: LivePeer | None = None
        try:
            own_socket(connection)
            connection.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
            parent = _open_parent(self.profile, self.api_host_gid)
            try:
                current = os.fstat(parent)
                _need((current.st_dev, current.st_ino) == self.parent_identity)
            finally:
                os.close(parent)
            _need(self._parent >= 0)
            pinned = os.fstat(self._parent)
            _need((pinned.st_dev, pinned.st_ino) == self.parent_identity)
            binding = self._runtime_binding()
            before = os.stat(_SOCKET, dir_fd=self._parent, follow_symlinks=False)
            expected_uid = _PROJECTED_UID if self.profile == "rootless" else 0
            expected_gid = _PROJECTED_GID if self.profile == "rootless" else self.api_host_gid
            _need(
                stat.S_ISSOCK(before.st_mode)
                and before.st_uid == expected_uid
                and before.st_gid == expected_gid
                and stat.S_IMODE(before.st_mode) == _SOCKET_MODE
                and before.st_nlink == 1
            )
            connection.settimeout(remaining(deadline))
            connection.connect(f"/proc/self/fd/{self._parent}/{_SOCKET}")
            after = os.stat(_SOCKET, dir_fd=self._parent, follow_symlinks=False)
            _need(_metadata(before) == _metadata(after))
            _need(binding == self._runtime_binding())
            credentials = PeerCredentials.from_socket(connection)
            if self.profile == "rootless":
                _need(credentials == PeerCredentials(0, _PROJECTED_UID, _PROJECTED_UID))
                peer = LivePeer(connection, allow_projected_root=True)
            else:
                helper = _record(binding["helper"])
                _need(credentials == PeerCredentials(_number(helper["pid"], minimum=2), 0, 0))
                peer = LivePeer(connection)
                peer.check()
            remaining(deadline)
        except BaseException:
            if peer is not None:
                peer.close()
            connection.close()
            raise
        else:
            return connection, peer, credentials

    def close(self) -> None:
        if self._parent >= 0:
            descriptor, self._parent = self._parent, -1
            os.close(descriptor)


class _Job:
    def __init__(self) -> None:
        self.deadline = time.monotonic() + CLIENT_SECONDS
        self.lock = threading.Lock()
        self.cancelled = False
        self.connection: socket.socket | None = None

    def own_socket(self, connection: socket.socket) -> None:
        with self.lock:
            if self.cancelled:
                connection.close()
                raise HostProtocolError(_UNAVAILABLE)
            self.connection = connection

    def cancel(self) -> None:
        with self.lock:
            self.cancelled = True
            if self.connection is not None:
                with suppress(OSError):
                    self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()


class HostHelperClient:
    """Eight owned exchanges, no retry, no default-executor or metadata jobs."""

    def __init__(self, binding: EndpointBinding, *, deployment_sha256: str | None = None) -> None:
        if deployment_sha256 is not None:
            _need(binding.deployment_sha256 == _digest(deployment_sha256))
        _digest(binding.deployment_sha256)
        self.binding = binding
        self._condition = threading.Condition()
        self._jobs: set[_Job] = set()
        self._workers: set[threading.Thread] = set()
        self._closed = False
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_EXCHANGES,
            thread_name_prefix="hfcache-host-client",
            initializer=self._register_worker,
        )

    def _register_worker(self) -> None:
        with self._condition:
            self._workers.add(threading.current_thread())

    def _reserve(self) -> _Job:
        with self._condition:
            if self._closed:
                raise HostProtocolError(_UNAVAILABLE)
            if len(self._jobs) >= MAX_EXCHANGES:
                raise HostProtocolError(_BUSY)
            job = _Job()
            self._jobs.add(job)
            return job

    def _release(self, job: _Job) -> None:
        with self._condition:
            self._jobs.discard(job)
            self._condition.notify_all()

    def _execute(
        self, job: _Job, operation: str, body: dict[str, object] | None = None
    ) -> dict[str, object]:
        peer: LivePeer | None = None
        try:
            request = HostRequest(secrets.token_hex(16), operation, body or {})
            connection, peer, credentials = self.binding.connect(
                deadline=job.deadline, own_socket=job.own_socket
            )
            with connection:
                result = client_exchange(
                    connection, request, deadline=job.deadline, expected=credentials
                )
                if peer is not None:
                    peer.check()
                remaining(job.deadline)
                return result
        except HostProtocolError:
            raise
        except TimeoutError:
            raise HostProtocolError(_TIMEOUT) from None
        except (OSError, ValueError):
            raise HostProtocolError(_UNAVAILABLE) from None
        finally:
            if peer is not None:
                peer.close()
            self._release(job)

    def status(self) -> dict[str, object]:
        return self._execute(self._reserve(), "status")

    def config_read(self) -> dict[str, object]:
        return self._execute(self._reserve(), "config-read")

    def config_prepare(self, body: dict[str, object]) -> dict[str, object]:
        incoming = _request_body("config-prepare", body)
        return self._execute(self._reserve(), "config-prepare", incoming)

    def config_apply(self, body: dict[str, object]) -> dict[str, object]:
        """Transmit once; uncertainty is observed through config_outcome, never replayed."""
        incoming = _request_body("config-apply", body)
        return self._execute(self._reserve(), "config-apply", incoming)

    def config_outcome(self, body: dict[str, object]) -> dict[str, object]:
        incoming = _request_body("config-outcome", body)
        return self._execute(self._reserve(), "config-outcome", incoming)

    async def _async(
        self, operation: str, body: dict[str, object] | None = None
    ) -> dict[str, object]:
        job = self._reserve()
        try:
            submitted = self._executor.submit(self._execute, job, operation, body)
        except RuntimeError:
            self._release(job)
            raise HostProtocolError(_UNAVAILABLE) from None
        wrapped = asyncio.wrap_future(submitted)
        try:
            return await asyncio.shield(wrapped)
        except asyncio.CancelledError:
            job.cancel()
            # Shield preserves the actual owned job and its slot. Retrieve its
            # eventual exception even after the original asyncio caller leaves.
            wrapped.add_done_callback(
                lambda result: result.exception() if not result.cancelled() else None
            )
            raise

    async def async_status(self) -> dict[str, object]:
        return await self._async("status")

    async def async_config_read(self) -> dict[str, object]:
        return await self._async("config-read")

    async def async_config_prepare(self, body: dict[str, object]) -> dict[str, object]:
        return await self._async("config-prepare", _request_body("config-prepare", body))

    async def async_config_apply(self, body: dict[str, object]) -> dict[str, object]:
        return await self._async("config-apply", _request_body("config-apply", body))

    async def async_config_outcome(self, body: dict[str, object]) -> dict[str, object]:
        return await self._async("config-outcome", _request_body("config-outcome", body))

    def close(self, *, timeout: float = 24.0) -> bool:
        """Stop admission, close owned sockets, and report actual joined workers."""
        if not math_is_positive(timeout):
            raise HostProtocolError(_INVALID)
        deadline = time.monotonic() + timeout
        with self._condition:
            self._closed = True
            jobs = tuple(self._jobs)
        for job in jobs:
            job.cancel()
        self._executor.shutdown(wait=False, cancel_futures=False)
        with self._condition:
            while self._jobs:
                available = deadline - time.monotonic()
                if available <= 0:
                    return False
                self._condition.wait(available)
            workers = tuple(self._workers)
        for worker in workers:
            if worker is threading.current_thread():
                return False
            worker.join(max(0.0, deadline - time.monotonic()))
            if worker.is_alive():
                return False
        self.binding.close()
        return True


def math_is_positive(value: float) -> bool:
    return type(value) in (int, float) and 0 < value < float("inf")
