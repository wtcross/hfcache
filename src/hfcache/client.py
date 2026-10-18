"""Bounded synchronous REST client with non-replaying submissions (decision 118)."""

import hashlib
import json
import math
import re
import time
from http import HTTPStatus
from itertools import pairwise
from typing import TYPE_CHECKING, Any, Self
from uuid import uuid4

import httpx
from pydantic import ValidationError

from hfcache.client_config import resolve_api_token
from hfcache.client_errors import (
    ClientConnectionError,
    ClientProtocolError,
    RemoteApiError,
    UncertainSubmission,
)
from hfcache.client_models import (
    JOB_ROUTES,
    Acceptance,
    Capabilities,
    ClientEvents,
    ClientOperation,
    ClientProblem,
    ClientRead,
    Submission,
)
from hfcache.errors import ConfigurationError, HfcacheError
from hfcache.http_transport import create_http_client
from hfcache.identity import parse_run_id
from hfcache.redaction import redact_text
from hfcache.taxonomy import classify

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from hfcache.client_config import ClientConfig

_KEY = re.compile(r"[A-Za-z0-9._~+-]{1,128}")
_PATH = re.compile(r"/api/v1(?:/[A-Za-z0-9_-][A-Za-z0-9._-]*)+")
_MAX_DEPTH = 32
_MAX_HEADER_BYTES = 32768
_MAX_LENGTH_DIGITS = 20
_MAX_EVENT_PAGE = 10000
_MAX_CACHED_OPERATIONS = 128
_PAGE_ROUTES = frozenset(
    {
        "/api/v1/status",
        "/api/v1/repositories",
        "/api/v1/repositories/revisions",
        "/api/v1/runs",
        "/api/v1/operations",
    }
)


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in items:
        if key in result:
            raise ClientProtocolError
        result[key] = value
    return result


def _constant(_: str) -> None:
    raise ClientProtocolError


def _json_values(value: object, depth: int = 0) -> None:
    if depth > _MAX_DEPTH:
        raise ClientProtocolError
    if isinstance(value, str):
        value.encode("utf-8")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ClientProtocolError
            _json_values(key, depth + 1)
            _json_values(item, depth + 1)
    elif isinstance(value, list | tuple):
        for item in value:
            _json_values(item, depth + 1)
    elif (isinstance(value, float) and not math.isfinite(value)) or (
        value is not None and not isinstance(value, bool | int | float)
    ):
        raise ClientProtocolError


def _key(value: str) -> str:
    if not isinstance(value, str) or not _KEY.fullmatch(value) or redact_text(value) != value:
        raise ClientProtocolError
    return value


def _row_digest(row: object) -> bytes:
    projection = row
    if isinstance(row, dict):
        if "operation_id" in row or "run_id" in row:
            projection = {key: row[key] for key in ("operation_id", "run_id") if key in row}
        elif "repository_id" in row:
            projection = {
                key: row[key]
                for key in ("repository_type", "repository_id", "commit_sha", "publication_id")
                if key in row
            }
    return hashlib.sha256(json.dumps(projection, sort_keys=True).encode()).digest()


class ApiClient:
    """One explicit credential/endpoint; response loss never creates another key."""

    def __init__(
        self,
        config: ClientConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config, self.sleep, self.monotonic = config, sleep, monotonic
        self._secret = resolve_api_token(config)
        if redact_text(config.url) != config.url:
            message = "API endpoint contains credential material"
            raise ConfigurationError.single(message, code="HFAPI017")
        try:
            self._http = (
                create_http_client(unix_socket=config.socket, ca_file=config.ca_file)
                if transport is None
                else httpx.Client(transport=transport, trust_env=False, follow_redirects=False)
            )
        except OSError, ValueError:
            message = "API TLS/client transport configuration is invalid"
            raise ConfigurationError.single(message, code="HFAPI017") from None
        self._http.timeout = httpx.Timeout(
            connect=config.connect_timeout,
            read=config.read_timeout,
            write=config.read_timeout,
            pool=config.connect_timeout,
        )
        self._archive_id = config.expected_archive_id
        self._capabilities: Capabilities | None = None
        self._operations: dict[str, ClientOperation] = {}
        self._operation_requests: dict[str, str] = {}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _url(self, path: str) -> str:
        if (
            not isinstance(path, str)
            or not _PATH.fullmatch(path)
            or redact_text(path) != path
            or any(part in {".", ".."} for part in path.split("/"))
        ):
            raise ClientProtocolError
        url = self.config.url.rstrip("/") + path
        if redact_text(url) != url:
            raise ClientProtocolError
        return url

    def _identity(self, archive_id: str | None) -> None:
        if self._archive_id is not None and archive_id != self._archive_id:
            raise ClientProtocolError
        if archive_id is not None:
            self._archive_id = archive_id

    def _payload(  # noqa: PLR0912 - one bounded frame validation boundary
        self, response: httpx.Response, deadline: float | None = None
    ) -> dict[str, Any]:
        headers = response.headers
        if sum(len(key) + len(value) for key, value in headers.raw) > _MAX_HEADER_BYTES:
            raise ClientProtocolError
        types = headers.get_list("content-type")
        if len(types) != 1:
            raise ClientProtocolError
        media = [part.strip().lower() for part in types[0].split(";")]
        if media[0] != "application/json" or (
            len(media) > 1 and media[1:] not in (["charset=utf-8"], ['charset="utf-8"'])
        ):
            raise ClientProtocolError
        if headers.get_list("content-encoding") not in ([], ["identity"]):
            raise ClientProtocolError
        lengths = headers.get_list("content-length")
        length = None
        if lengths:
            if (
                len(lengths) != 1
                or not lengths[0].isascii()
                or not lengths[0].isdecimal()
                or len(lengths[0]) > _MAX_LENGTH_DIGITS
                or "transfer-encoding" in headers
            ):
                raise ClientProtocolError
            length = int(lengths[0])
            if length > self.config.max_response_bytes:
                raise ClientProtocolError
        body = bytearray()
        for part in response.iter_bytes():
            if deadline is not None and self.monotonic() >= deadline:
                raise ClientConnectionError
            if len(body) + len(part) > self.config.max_response_bytes:
                raise ClientProtocolError
            body.extend(part)
        if length is not None and len(body) != length:
            raise ClientProtocolError
        if deadline is not None and self.monotonic() >= deadline:
            raise ClientConnectionError
        try:
            payload = json.loads(
                body.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant
            )
            _json_values(payload)
        except ValueError, UnicodeError, RecursionError:
            raise ClientProtocolError from None
        if not isinstance(payload, dict):
            raise ClientProtocolError
        return payload

    def _encode_body(self, body: Mapping[str, Any]) -> bytes:
        try:
            _json_values(dict(body))
            content = json.dumps(body, allow_nan=False, ensure_ascii=False).encode("utf-8")
        except ValueError, UnicodeError, TypeError, RecursionError:
            raise ClientProtocolError from None
        if len(content) > self.config.max_response_bytes:
            raise ClientProtocolError
        return content

    def _exchange(  # noqa: PLR0912, PLR0913 - one bounded request/response ownership boundary
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | bytes | None = None,
        key: str | None = None,
        deadline: float | None = None,
    ) -> tuple[dict[str, Any], httpx.Headers]:
        if self._http.is_closed:
            raise ClientConnectionError
        url = self._url(path)
        content = (
            body
            if isinstance(body, bytes)
            else (self._encode_body(body) if body is not None else None)
        )
        headers = {
            "Authorization": "Bearer " + self._secret,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        }
        if content is not None:
            headers["Content-Type"] = "application/json"
        if key is not None:
            headers["Idempotency-Key"] = _key(key)
        for attempt in range(self.config.read_retries + 1 if method == "GET" else 1):
            remaining = None if deadline is None else deadline - self.monotonic()
            if remaining is not None and remaining <= 0:
                raise ClientConnectionError
            timeout = (
                self._http.timeout
                if remaining is None
                else httpx.Timeout(
                    connect=min(self.config.connect_timeout, remaining),
                    read=min(self.config.read_timeout, remaining),
                    write=min(self.config.read_timeout, remaining),
                    pool=min(self.config.connect_timeout, remaining),
                )
            )
            try:
                self._http.cookies.clear()
                with self._http.stream(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    content=content,
                    timeout=timeout,
                    follow_redirects=False,
                ) as response:
                    if response.is_redirect:
                        raise ClientProtocolError  # noqa: TRY301 - classified after transmission
                    payload = self._payload(response, deadline)
                    if response.status_code >= HTTPStatus.BAD_REQUEST:
                        self._remote_error(response.status_code, payload)
                    if response.status_code != (202 if method == "POST" and key else 200):
                        raise ClientProtocolError  # noqa: TRY301 - classified after transmission
                    return payload, response.headers
            except ClientProtocolError, httpx.DecodingError:
                if method == "POST" and key is not None:
                    raise UncertainSubmission(key, path) from None
                raise ClientProtocolError from None
            except RemoteApiError as error:
                if method == "POST" and key is not None:
                    error.key, error.route = key, path
                raise
            except httpx.InvalidURL:
                raise ClientProtocolError from None
            except httpx.TransportError:
                if method == "POST" and key is not None:
                    raise UncertainSubmission(key, path) from None
                if attempt == self.config.read_retries or method != "GET":
                    raise ClientConnectionError from None
                pause = self.config.poll_interval
                if deadline is not None:
                    pause = min(pause, max(0.0, deadline - self.monotonic()))
                self.sleep(pause)
            finally:
                self._http.cookies.clear()
        raise ClientConnectionError

    @staticmethod
    def _remote_error(status: int, payload: dict[str, Any]) -> None:
        try:
            problem = ClientProblem.model_validate(payload)
            if int(classify(problem.code)) != problem.exit_code or problem.exit_code == 0:
                raise ClientProtocolError
        except ValueError, ValidationError:
            raise ClientProtocolError from None
        raise RemoteApiError(
            code=problem.code,
            exit_code=problem.exit_code,
            status_code=status,
            request_id=problem.request_id,
        )

    def read(
        self, path: str, params: Mapping[str, Any] | None = None, *, _deadline: float | None = None
    ) -> ClientRead:
        if params is not None and any(
            key not in {"limit", "cursor", "selector", "type", "after"}
            or redact_text(str(value)) != str(value)
            for key, value in params.items()
        ):
            raise ClientProtocolError
        payload, _ = self._exchange("GET", path, params=params, deadline=_deadline)
        try:
            result = ClientRead.model_validate(payload)
        except ValueError, HfcacheError:
            raise ClientProtocolError from None
        self._identity(result.archive_id)
        if path not in _PAGE_ROUTES and result.next_cursor is not None:
            raise ClientProtocolError
        if _deadline is not None and self.monotonic() >= _deadline:
            raise ClientConnectionError
        return result

    def capabilities(self) -> Capabilities:
        result = self.read("/api/v1/capabilities")
        if result.envelope.exit_code != 0:
            raise ClientProtocolError
        try:
            capabilities = Capabilities.model_validate(result.envelope.data)
        except ValueError:
            raise ClientProtocolError from None
        self._capabilities = capabilities
        return capabilities

    def require_capabilities(self, *names: str) -> Capabilities:
        capabilities = self._capabilities or self.capabilities()
        for name in names:
            if name in {"read", "write"}:
                allowed = name in capabilities.capabilities
            elif name in {"reads", "operations", "operation_history", "maintenance_enabled"}:
                allowed = getattr(capabilities, name)
            else:
                raise ClientProtocolError
            if not allowed:
                raise ClientProtocolError
        return capabilities

    def iter_pages(
        self, path: str, field: str, params: Mapping[str, Any] | None = None
    ) -> Iterator[ClientRead]:
        if path not in _PAGE_ROUTES:
            raise ClientProtocolError
        query = dict(params or {})
        seen = {query["cursor"]} if "cursor" in query else set()
        rows_seen: set[bytes] = set()
        identity = None
        for _ in range(self.config.max_pages):
            page = self.read(path, query)
            current = (page.archive_id, page.config_fingerprint, page.envelope.command)
            if identity is None:
                identity = current
            if page.envelope.exit_code != 0:
                if current != identity or page.next_cursor is not None:
                    raise ClientProtocolError
                yield page
                return
            if current != identity or not isinstance(page.envelope.data.get(field), list):
                raise ClientProtocolError
            for row in page.envelope.data[field]:
                digest = _row_digest(row)
                if (
                    digest in rows_seen
                    or len(rows_seen) * len(digest) >= self.config.max_response_bytes
                ):
                    raise ClientProtocolError
                rows_seen.add(digest)
            cursor = page.next_cursor
            if cursor is not None and (cursor in seen or redact_text(cursor) != cursor):
                raise ClientProtocolError
            if cursor is not None:
                seen.add(cursor)
            yield page
            if cursor is None:
                return
            query["cursor"] = cursor
        raise ClientProtocolError

    def submit(
        self,
        path: str,
        body: Mapping[str, Any],
        *,
        key: str | None = None,
        on_key: Callable[[str], None] | None = None,
    ) -> Submission:
        if path not in JOB_ROUTES:
            raise ClientProtocolError
        retained = _key(uuid4().hex if key is None else key)
        content = self._encode_body(body)
        self._url(path)
        if on_key is not None:
            on_key(retained)
        payload, headers = self._exchange("POST", path, body=content, key=retained)
        try:
            accepted = Acceptance.model_validate(payload)
        except ValueError, HfcacheError:
            raise UncertainSubmission(retained, path) from None
        operation = accepted.operation
        expected = (
            httpx.URL(self.config.url).path.rstrip("/")
            + "/api/v1/operations/"
            + operation.operation_id
        )
        if (
            operation.route != path
            or accepted.links.status != expected
            or accepted.links.result != expected + "/result"
            or accepted.links.events != expected + "/events"
            or headers.get_list("location") != [expected]
        ):
            raise UncertainSubmission(retained, path)
        try:
            self._identity(accepted.archive_id)
            self._remember(operation)
        except ClientProtocolError:
            raise UncertainSubmission(retained, path) from None
        return Submission(retained, accepted)

    def _remember(self, operation: ClientOperation) -> ClientOperation:
        old = self._operations.get(operation.operation_id)
        if old is not None and (
            (old.archive_id, old.config_fingerprint, old.route, old.principal)
            != (
                operation.archive_id,
                operation.config_fingerprint,
                operation.route,
                operation.principal,
            )
            or (old.domain_run_id is not None and old.domain_run_id != operation.domain_run_id)
            or operation.transaction_ids[: len(old.transaction_ids)] != old.transaction_ids
            or (old.state in {"succeeded", "failed", "interrupted"} and operation != old)
        ):
            raise ClientProtocolError
        self._operations[operation.operation_id] = operation
        if len(self._operations) > _MAX_CACHED_OPERATIONS:
            oldest = next(iter(self._operations))
            self._operations.pop(oldest)
            self._operation_requests.pop(oldest, None)
        return operation

    def _operation(self, result: ClientRead, expected: str | None = None) -> ClientOperation:
        try:
            if result.envelope.exit_code != 0 or set(result.envelope.data) != {"operation"}:
                raise ClientProtocolError
            operation = ClientOperation.model_validate(result.envelope.data["operation"])
        except ValueError, HfcacheError:
            raise ClientProtocolError from None
        if (
            (expected is not None and operation.operation_id != expected)
            or result.archive_id != operation.archive_id
            or result.config_fingerprint != operation.config_fingerprint
        ):
            raise ClientProtocolError
        remembered = self._remember(operation)
        self._operation_requests[operation.operation_id] = result.request_id
        return remembered

    def lookup(self, key: str) -> ClientOperation:
        payload, _ = self._exchange("GET", "/api/v1/operations/lookup", key=_key(key))
        try:
            result = ClientRead.model_validate(payload)
        except ValueError, HfcacheError:
            raise ClientProtocolError from None
        self._identity(result.archive_id)
        if result.next_cursor is not None:
            raise ClientProtocolError
        return self._operation(result)

    def operation(self, operation_id: str, *, _deadline: float | None = None) -> ClientOperation:
        identifier = self._identifier(operation_id)
        return self._operation(
            self.read("/api/v1/operations/" + identifier, _deadline=_deadline), identifier
        )

    @staticmethod
    def _identifier(value: str) -> str:
        try:
            return parse_run_id(value)
        except ValueError:
            raise ClientProtocolError from None

    def result(self, operation_id: str, *, _deadline: float | None = None) -> ClientRead:
        identifier = self._identifier(operation_id)
        known = self._operations.get(identifier)
        if known is None or known.state in {"queued", "waiting_lock", "running"}:
            known = self.operation(identifier, _deadline=_deadline)
        result = self.read("/api/v1/operations/" + identifier + "/result", _deadline=_deadline)
        if (
            known.state not in {"succeeded", "failed"}
            or (result.archive_id, result.config_fingerprint, result.envelope.run_id)
            != (known.archive_id, known.config_fingerprint, known.domain_run_id)
            or (known.state == "succeeded") != (result.envelope.exit_code == 0)
        ):
            raise ClientProtocolError
        return result

    def events(self, operation_id: str, after: int = 0, limit: int = 100) -> ClientEvents:
        identifier = self._identifier(operation_id)
        if (
            type(after) is not int
            or after < 0
            or type(limit) is not int
            or not 1 <= limit <= _MAX_EVENT_PAGE
        ):
            raise ClientProtocolError
        known = self._operations.get(identifier)
        if known is None:
            known = self.operation(identifier)
        result = self.read(
            "/api/v1/operations/" + identifier + "/events", {"after": after, "limit": limit}
        )
        try:
            page = ClientEvents.model_validate(result.envelope.data)
        except ValueError:
            raise ClientProtocolError from None
        sequences = [event.sequence for event in page.events]
        if (
            page.operation_id != identifier
            or len(sequences) > limit
            or sequences != sorted(set(sequences))
            or any(number <= after for number in sequences)
            or page.next_cursor != (sequences[-1] if sequences else after)
            or (sequences and sequences[0] != max(after + 1, page.oldest_sequence))
            or any(right != left + 1 for left, right in pairwise(sequences))
            or page.truncated != (after < page.oldest_sequence - 1)
            or (
                (result.archive_id, result.config_fingerprint)
                != (known.archive_id, known.config_fingerprint)
            )
        ):
            raise ClientProtocolError
        return page

    def poll(self, operation_id: str, *, timeout: float | None = None) -> ClientRead:
        duration = self.config.wait_timeout if timeout is None else timeout
        if (
            isinstance(duration, bool)
            or not isinstance(duration, int | float)
            or not math.isfinite(duration)
            or duration <= 0
        ):
            raise ClientProtocolError
        deadline = self.monotonic() + duration
        while True:
            operation = self.operation(operation_id, _deadline=deadline)
            if operation.state in {"succeeded", "failed"}:
                return self.result(operation_id, _deadline=deadline)
            if operation.state == "interrupted":
                raise RemoteApiError(
                    code="HFAPI015",
                    exit_code=20,
                    status_code=409,
                    request_id=self._operation_requests[operation.operation_id],
                )
            remaining = deadline - self.monotonic()
            if remaining <= 0:
                raise ClientConnectionError
            self.sleep(min(self.config.poll_interval, remaining))

    def version(self) -> ClientRead:
        return self.read("/api/v1/version")

    def health(self) -> ClientRead:
        return self.read("/api/v1/health")

    def validate_installed(self) -> ClientRead:
        payload, _ = self._exchange("POST", "/api/v1/config/validate", body={})
        try:
            result = ClientRead.model_validate(payload)
        except ValueError, HfcacheError:
            raise ClientProtocolError from None
        self._identity(result.archive_id)
        if result.next_cursor is not None:
            raise ClientProtocolError
        return result
