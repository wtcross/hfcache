"""Decision150 host-helper frames and live peer proof (host-administration.md).

This module is also loaded by trusted host Python3.12. Keep it standard-library
only; application DTOs, policy inspection and service selection belong outside
this transport. No received descriptor ever confers authority.
"""

from __future__ import annotations

import array
import json
import math
import os
import re
import select
import socket
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

MAX_FRAME_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 100000
MAX_NUMERIC_CHARS = 128
SERVER_SECONDS = 20.0
READ_SECONDS = 3.0
INSPECTION_SECONDS = 15.0
WRITE_SECONDS = 2.0
CLIENT_SECONDS = 22.0
MAX_EXCHANGES = 8
MAX_MANAGED_EDITS = 256
MAX_SELECTOR_CHARS = 256
MAX_ARCHIVE_ROOT_CHARS = 4096
SO_PEERPIDFD = 77
SCM_PIDFD = 4
_HEADER = struct.Struct("!I")
_CREDENTIALS = struct.Struct("=iII")
_HEX32 = re.compile(r"[0-9a-f]{32}\Z")
_PROC_BYTES = 4096
_SURROGATE_MIN = 0xD800
_SURROGATE_MAX = 0xDFFF
_INVALID = "invalid-request"
_PEER_REFUSED = "peer-refused"
_TIMEOUT = "timeout"
_UNAVAILABLE = "facts-unavailable"
_INT_MIN = -(2**63)
_INT_MAX = 2**63 - 1
_MIN_PROCESS_ID = 2
_MAX_PROCESS_ID = 2**31 - 1
_MAX_START_TICKS = 2**53 - 1
_MAX_CALENDAR_CHARS = 4096
_MAX_DELAY_CHARS = 256
_MAX_JOURNAL_CURSOR_CHARS = 2048
_MAX_JOURNAL_LINES = 80
_REASONS = frozenset(
    {
        "peer-refused",
        "invalid-request",
        "busy",
        "timeout",
        "policy-missing",
        "policy-invalid",
        "deployment-unverified",
        "facts-unavailable",
        "operation-denied",
        "config-unavailable",
        "config-conflict",
        "host-conflict",
        "internal-unavailable",
    }
)
_OPERATIONS = frozenset(
    {
        "status",
        "config-read",
        "config-prepare",
        "config-apply",
        "config-outcome",
        "schedule-validate",
        "schedule-change",
        "schedule-outcome",
        "observer-status",
        "observer-stop",
        "observer-outcome",
        "journal-read",
    }
)
# Linux limits one SCM_RIGHTS message to253 FDs. Leave room for credentials,
# all such FDs and an unexpected pidfd; MSG_CTRUNC still always refuses.
_ANCILLARY_BYTES = socket.CMSG_SPACE(_CREDENTIALS.size) + socket.CMSG_SPACE(254 * 4)


class HostProtocolError(Exception):
    """A fixed private reason, mapped to the application taxonomy by its caller."""

    def __init__(self, reason: str = "internal-unavailable") -> None:
        self.reason = reason if reason in _REASONS else "internal-unavailable"
        super().__init__(self.reason)


def _need(condition: object, reason: str = "invalid-request") -> None:
    if not condition:
        raise HostProtocolError(reason)


def _lexical_limits(text: str) -> None:  # noqa: PLR0912 - finite pre-decoder scanner
    """Bound containers/tokens before allocating the decoded object graph."""
    depth = nodes = index = 0
    while index < len(text):
        char = text[index]
        if char.isspace() or char in ",:":
            index += 1
            continue
        if char in "}]":
            depth -= 1
            _need(depth >= 0)
            index += 1
            continue
        nodes += 1
        _need(nodes <= MAX_JSON_NODES)
        if char in "{[":
            depth += 1
            _need(depth <= MAX_JSON_DEPTH)
            index += 1
            continue
        _need(depth + 1 <= MAX_JSON_DEPTH)
        start = index
        if char == '"':
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                elif text[index] == '"':
                    index += 1
                    break
                else:
                    index += 1
            else:
                raise HostProtocolError(_INVALID)
        else:
            while index < len(text) and text[index] not in " \t\r\n,]}:":
                index += 1
            _need(index > start)
            if char in "-0123456789":
                _need(index - start <= MAX_NUMERIC_CHARS)
    _need(depth == 0)


def _integer(text: str) -> int:
    _need(len(text) <= MAX_NUMERIC_CHARS)
    result = int(text)
    _need(_INT_MIN <= result <= _INT_MAX)
    return result


def _float(text: str) -> float:
    _need(len(text) <= MAX_NUMERIC_CHARS)
    result = float(text)
    _need(math.isfinite(result))
    return result


def _constant(_text: str) -> object:
    raise HostProtocolError(_INVALID)


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        _need(key not in result)
        result[key] = value
    return result


def _value_limits(value: object) -> None:
    nodes = 0
    stack = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        _need(nodes <= MAX_JSON_NODES and depth <= MAX_JSON_DEPTH)
        if type(item) is dict:
            _need(all(type(key) is str for key in item))
            stack.extend((key, depth + 1) for key in item)
            stack.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            stack.extend((child, depth + 1) for child in item)
        elif type(item) is str:
            _need(not any(_SURROGATE_MIN <= ord(char) <= _SURROGATE_MAX for char in item))
        elif type(item) is int:
            _need(_INT_MIN <= item <= _INT_MAX)
        elif type(item) is float:
            _need(math.isfinite(item))
        else:
            _need(item is None or type(item) is bool)


def decode_object(data: bytes, *, maximum: int = MAX_FRAME_BYTES) -> dict[str, object]:
    """Strict bounded JSON for frames and independently protected small records."""
    _need(1 <= len(data) <= maximum <= MAX_FRAME_BYTES)
    try:
        text = data.decode("utf-8", errors="strict")
        _lexical_limits(text)
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_int=_integer,
            parse_float=_float,
            parse_constant=_constant,
        )
        _need(type(value) is dict)
        _value_limits(value)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise HostProtocolError(_INVALID) from None
    return value


def encode_object(value: dict[str, object]) -> bytes:
    _need(type(value) is dict)
    _value_limits(value)
    try:
        result = json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8", errors="strict")
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise HostProtocolError(_INVALID) from None
    _need(1 <= len(result) <= MAX_FRAME_BYTES)
    return result


def _hex_field(value: object, width: int) -> None:
    _need(type(value) is str and re.fullmatch(r"[0-9a-f]{" + str(width) + "}", value))


def _managed_request(value: object) -> None:
    _need(type(value) is dict and set(value) == {"base_revision", "edits"})
    body = cast("dict[str, object]", value)
    _hex_field(body["base_revision"], 64)
    _need(type(body["edits"]) is list and len(body["edits"]) <= MAX_MANAGED_EDITS)


def _config_read_request(body: dict[str, object]) -> None:
    if not body:
        return
    _need(set(body) == {"expected_archive_id", "expected_archive_root"})
    identifier, root = body["expected_archive_id"], body["expected_archive_root"]
    _need(
        type(identifier) is str
        and re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", identifier) is not None
    )
    _need(
        type(root) is str
        and 0 < len(root) <= MAX_ARCHIVE_ROOT_CHARS
        and root.startswith("/")
        and root.isprintable()
    )


def _calendar_value(value: object, maximum: int) -> None:
    _need(
        type(value) is str
        and 1 <= len(value) <= maximum
        and bool(value.strip())
        and "\\" not in value
        and all(" " <= char <= "~" for char in value)
    )


def _schedule_values(body: dict[str, object]) -> None:
    _calendar_value(body["on_calendar"], _MAX_CALENDAR_CHARS)
    if body["randomized_delay_sec"] is not None:
        _calendar_value(body["randomized_delay_sec"], _MAX_DELAY_CHARS)


def _observer_request(value: object) -> None:
    _need(type(value) is dict and set(value) == {"expected"})
    value = cast("dict[str, object]", value)
    expected = value["expected"]
    _need(type(expected) is dict)
    expected = cast("dict[str, object]", expected)
    _need(set(expected) == {"boot_id", "invocation_id", "main_pid", "start_ticks"})
    boot = expected["boot_id"]
    _need(type(boot) is str and re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", boot))
    _hex_field(expected["invocation_id"], 32)
    _need(
        type(expected["main_pid"]) is int
        and _MIN_PROCESS_ID <= expected["main_pid"] <= _MAX_PROCESS_ID
    )
    _need(type(expected["start_ticks"]) is int and 1 <= expected["start_ticks"] <= _MAX_START_TICKS)


def _host_action_request(operation: str, body: dict[str, object]) -> None:
    if operation == "schedule-validate":
        _need(set(body) == {"on_calendar", "randomized_delay_sec"})
        _schedule_values(body)
    elif operation == "journal-read":
        _need(set(body) == {"source", "cursor", "limit"})
        _need(
            type(body["source"]) is str and body["source"] in {"sync-observer", "verify-observer"}
        )
        _need(type(body["limit"]) is int and 1 <= body["limit"] <= _MAX_JOURNAL_LINES)
        cursor = body["cursor"]
        _need(
            cursor is None
            or (
                type(cursor) is str
                and 1 <= len(cursor) <= _MAX_JOURNAL_CURSOR_CHARS
                and all(" " <= char <= "~" for char in cursor)
            )
        )
    elif operation == "observer-status":
        _need(not body)
    else:
        effect = operation in {"schedule-change", "observer-stop"}
        _need(
            set(body)
            == (
                {"operation_id", "request_digest", "request"}
                if effect
                else {"operation_id", "request_digest"}
            )
        )
        _hex_field(body["operation_id"], 32)
        _hex_field(body["request_digest"], 64)
        if not effect:
            return
        request = body["request"]
        if operation == "observer-stop":
            _observer_request(request)
            return
        _need(type(request) is dict)
        request = cast("dict[str, object]", request)
        _need(
            type(request.get("action")) is str
            and request["action"] in {"pause", "resume", "replace", "reset"}
        )
        fields = {"action", "expected_revision"}
        if request["action"] == "replace":
            fields |= {"on_calendar", "randomized_delay_sec"}
        _need(set(request) == fields)
        _hex_field(request["expected_revision"], 64)
        if request["action"] == "replace":
            _schedule_values(request)


@dataclass(frozen=True)
class HostRequest:
    request_id: str
    operation: str
    body: dict[str, object] = field(default_factory=dict)

    @classmethod
    def parse(cls, value: dict[str, object]) -> HostRequest:
        _need(set(value) == {"schema_version", "request_id", "operation", "body"})
        _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
        request_id, operation = value["request_id"], value["operation"]
        _need(type(request_id) is str and _HEX32.fullmatch(request_id) is not None)
        _need(type(operation) is str and operation in _OPERATIONS)
        body = value["body"]
        _need(type(body) is dict)
        body = cast("dict[str, object]", body)
        if operation in {
            "schedule-validate",
            "schedule-change",
            "schedule-outcome",
            "observer-status",
            "observer-stop",
            "observer-outcome",
            "journal-read",
        }:
            _host_action_request(operation, body)
        elif operation == "config-read":
            _config_read_request(body)
        elif operation == "config-prepare":
            _managed_request(body)
        elif operation in {"config-apply", "config-outcome"}:
            expected = {"operation_id", "request_digest"}
            if operation == "config-apply":
                expected |= {
                    "managed",
                    "candidate_revision",
                    "config_fingerprint",
                    "preview_operation_id",
                    "required_selectors",
                }
            _need(set(body) == expected)
            _hex_field(body["operation_id"], 32)
            _hex_field(body["request_digest"], 64)
            if operation == "config-apply":
                _managed_request(body["managed"])
                _hex_field(body["candidate_revision"], 64)
                _hex_field(body["config_fingerprint"], 64)
                _hex_field(body["preview_operation_id"], 32)
                selectors = body["required_selectors"]
                _need(type(selectors) is list and len(selectors) <= MAX_MANAGED_EDITS)
                selectors = cast("list[str]", selectors)
                _need(
                    all(
                        type(value) is str and 1 <= len(value) <= MAX_SELECTOR_CHARS
                        for value in selectors
                    )
                )
                _need(len(selectors) == len(set(selectors)))
        else:
            _need(not body)
        return cls(cast("str", request_id), cast("str", operation), cast("dict[str, object]", body))

    def wire(self) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": 1,
            "request_id": self.request_id,
            "operation": self.operation,
            "body": self.body,
        }
        self.parse(result)
        return result


def reply_body(value: dict[str, object], request: HostRequest) -> dict[str, object]:
    _need(set(value) == {"schema_version", "request_id", "operation", "outcome", "body", "reason"})
    _need(type(value["schema_version"]) is int and value["schema_version"] == 1)
    _need(value["request_id"] == request.request_id and value["operation"] == request.operation)
    _need(type(value["body"]) is dict)
    if value["outcome"] == "ok":
        _need(value["reason"] is None)
        return cast("dict[str, object]", value["body"])
    _need(value["outcome"] in ("denied", "unavailable") and not value["body"])
    _need(type(value["reason"]) is str and value["reason"] in _REASONS)
    raise HostProtocolError(cast("str", value["reason"]))


@dataclass(frozen=True)
class PeerCredentials:
    pid: int
    uid: int
    gid: int

    @classmethod
    def from_socket(cls, connection: socket.socket) -> PeerCredentials:
        try:
            values = _CREDENTIALS.unpack(
                connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, _CREDENTIALS.size)
            )
        except (OSError, struct.error):
            raise HostProtocolError(_PEER_REFUSED) from None
        return cls(*values)


class LivePeer:
    """Own only the socket's original peer pidfd, never a numeric-PID replacement."""

    def __init__(self, connection: socket.socket, *, allow_projected_root: bool = False) -> None:
        self.credentials = PeerCredentials.from_socket(connection)
        self.pidfd = -1
        try:
            if allow_projected_root:
                _need(self.credentials == PeerCredentials(0, 65534, 65534), "peer-refused")
            else:
                _need(self.credentials.pid > 0, "peer-refused")
            descriptor = connection.getsockopt(socket.SOL_SOCKET, SO_PEERPIDFD)
            _need(type(descriptor) is int and descriptor >= 0, "peer-refused")
            self.pidfd = descriptor
            os.set_inheritable(descriptor, False)  # noqa: FBT003 - positional-only OS primitive
            self.check()
        except (OSError, ValueError, HostProtocolError):
            self.close()
            raise HostProtocolError(_PEER_REFUSED) from None

    def check(self) -> None:
        _need(self.pidfd >= 0, "peer-refused")
        try:
            poller = select.poll()
            poller.register(self.pidfd, select.POLLIN)
            _need(not poller.poll(0), "peer-refused")
            with Path(f"/proc/self/fdinfo/{self.pidfd}").open("rb") as stream:
                data = stream.read(_PROC_BYTES + 1)
            _need(len(data) <= _PROC_BYTES, "peer-refused")
            pids = [line.split()[1:] for line in data.splitlines() if line.startswith(b"Pid:")]
            _need(len(pids) == 1 and len(pids[0]) == 1, "peer-refused")
            _need(int(pids[0][0]) == self.credentials.pid, "peer-refused")
        except (OSError, ValueError, IndexError):
            raise HostProtocolError(_PEER_REFUSED) from None

    def close(self) -> None:
        if self.pidfd >= 0:
            descriptor, self.pidfd = self.pidfd, -1
            os.close(descriptor)


def configure_listener(listener: socket.socket) -> None:
    """Call before accept; accepted sockets must inherit this kernel setting."""
    _need(listener.family == socket.AF_UNIX and listener.type == socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    _need(listener.getsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED) == 1, "peer-refused")


def _ancillary(controls: list[tuple[int, int, bytes]], flags: int) -> list[PeerCredentials]:
    credentials = []
    descriptors: set[int] = set()
    refused = bool(flags & (socket.MSG_CTRUNC | socket.MSG_TRUNC))
    for level, kind, data in controls:
        if level == socket.SOL_SOCKET and kind in (socket.SCM_RIGHTS, SCM_PIDFD):
            refused = True
            # Only known descriptor controls carry owned FD integers. Dispose
            # complete entries even when the enclosing control is malformed.
            values = array.array("i")
            values.frombytes(data[: len(data) - len(data) % values.itemsize])
            descriptors.update(value for value in values if value >= 0)
        elif level == socket.SOL_SOCKET and kind == socket.SCM_CREDENTIALS:
            if len(data) != _CREDENTIALS.size:
                refused = True
            else:
                credentials.append(PeerCredentials(*_CREDENTIALS.unpack(data)))
        else:
            refused = True
    for descriptor in descriptors:
        try:
            os.close(descriptor)
        except OSError:
            refused = True
    _need(not refused and len(credentials) <= 1, "peer-refused")
    return credentials


def remaining(deadline: float) -> float:
    result = deadline - time.monotonic()
    _need(result > 0, "timeout")
    return result


def _receive(
    connection: socket.socket, count: int, deadline: float, expected: PeerCredentials
) -> bytes:
    connection.settimeout(remaining(deadline))
    try:
        data, controls, flags, _ = connection.recvmsg(
            count, _ANCILLARY_BYTES, socket.MSG_CMSG_CLOEXEC
        )
    except TimeoutError:
        raise HostProtocolError(_TIMEOUT) from None
    except OSError:
        raise HostProtocolError(_PEER_REFUSED) from None
    credentials = _ancillary(controls, flags)
    if data:
        _need(credentials == [expected], "peer-refused")
    remaining(deadline)
    return data


def receive_frame(
    connection: socket.socket, *, deadline: float, expected: PeerCredentials
) -> dict[str, object]:
    """Read one frame and exact EOF, with credentials on every data fragment."""
    _need(connection.getsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED) == 1, "peer-refused")

    def exact(count: int) -> bytes:
        buffer = bytearray()
        while len(buffer) < count:
            data = _receive(connection, min(65536, count - len(buffer)), deadline, expected)
            _need(bool(data))
            buffer.extend(data)
        return bytes(buffer)

    length = _HEADER.unpack(exact(_HEADER.size))[0]
    _need(1 <= length <= MAX_FRAME_BYTES)
    body = exact(length)
    _need(not _receive(connection, 1, deadline, expected))
    result = decode_object(body)
    remaining(deadline)
    return result


def send_frame(connection: socket.socket, value: dict[str, object], *, deadline: float) -> None:
    body = encode_object(value)
    connection.settimeout(remaining(deadline))
    try:
        connection.sendall(_HEADER.pack(len(body)) + body)
    except TimeoutError:
        raise HostProtocolError(_TIMEOUT) from None
    except OSError:
        raise HostProtocolError(_UNAVAILABLE) from None
    remaining(deadline)


class ExchangeBudget:
    def __init__(self) -> None:
        self.deadline = time.monotonic() + SERVER_SECONDS
        self.inspection_used = 0.0

    def inspection_remaining(self) -> float:
        available = INSPECTION_SECONDS - self.inspection_used
        _need(available > 0, "timeout")
        return min(remaining(self.deadline), available)

    def inspect(self, callback: Callable[[float], object]) -> object:
        available = self.inspection_remaining()
        started = time.monotonic()
        try:
            result = callback(available)
        finally:
            self.inspection_used += time.monotonic() - started
        self.inspection_remaining()
        return result


class Exchange:
    """Retain the original peer through parsing, reauthentication and response."""

    def __init__(
        self,
        connection: socket.socket,
        authenticate: Callable[[LivePeer, float], object],
        budget: ExchangeBudget,
    ) -> None:
        self.connection, self.authenticate, self.budget = connection, authenticate, budget
        self.peer = LivePeer(connection)
        self.dispatched = self.responded = False
        self._dispatch_complete = False
        try:
            self.context = self._authenticate()
            deadline = min(self.budget.deadline, time.monotonic() + READ_SECONDS)
            self.request = HostRequest.parse(
                receive_frame(connection, deadline=deadline, expected=self.peer.credentials)
            )
        except BaseException:
            self.close()
            raise

    def _authenticate(self) -> object:
        self.peer.check()
        result = self.budget.inspect(lambda seconds: self.authenticate(self.peer, seconds))
        self.peer.check()
        return result

    def dispatch(self, callback: Callable[[HostRequest, object, float], object]) -> object:
        _need(not self.dispatched and not self.responded)
        self.dispatched = True
        self.context = self._authenticate()
        result = self.budget.inspect(lambda seconds: callback(self.request, self.context, seconds))
        self._dispatch_complete = True
        return result

    def respond(self, *, outcome: str, body: dict[str, object], reason: str | None = None) -> None:
        _need(not self.responded)
        _need(outcome != "ok" or self._dispatch_complete)
        value: dict[str, object] = {
            **self.request.wire(),
            "outcome": outcome,
            "body": body,
            "reason": reason,
        }
        try:
            reply_body(value, self.request)
        except HostProtocolError:
            _need(outcome in ("denied", "unavailable") and reason in _REASONS and not body)
        self.responded = True
        self.peer.check()
        send_frame(
            self.connection,
            value,
            deadline=min(self.budget.deadline, time.monotonic() + WRITE_SECONDS),
        )
        self.connection.shutdown(socket.SHUT_WR)

    def close(self) -> None:
        self.peer.close()

    def __enter__(self) -> Exchange:
        return self

    def __exit__(
        self,
        _kind: type[BaseException] | None,
        _error: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self.close()


def receive_exchange(
    connection: socket.socket,
    authenticate: Callable[[LivePeer, float], object],
    *,
    budget: ExchangeBudget | None = None,
) -> Exchange:
    return Exchange(connection, authenticate, budget or ExchangeBudget())


def client_exchange(
    connection: socket.socket,
    request: HostRequest,
    *,
    deadline: float,
    expected: PeerCredentials,
) -> dict[str, object]:
    """The caller independently authenticates the pinned endpoint before this."""
    send_frame(connection, request.wire(), deadline=deadline)
    connection.shutdown(socket.SHUT_WR)
    return reply_body(receive_frame(connection, deadline=deadline, expected=expected), request)
