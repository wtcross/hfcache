"""One-page authenticated run inventory and exact report reads (decision 136)."""

import json
import re
from typing import TYPE_CHECKING

from hfcache.client_errors import ClientProtocolError
from hfcache.client_models import Capabilities, ClientRead, exact_version
from hfcache.errors import ConfigurationError, HfcacheError
from hfcache.redaction import redact_text
from hfcache.reporting import RecoveryReport, RunReport, VerificationReport

if TYPE_CHECKING:
    from hfcache.client import ApiClient

_RUN_ID = re.compile(r"[a-f0-9]{32}")
_CURSOR = re.compile(r"[!-~]{1,256}")
_NOTICE = "Run read metadata: "
_MAX_PAGE_SIZE = 10000
_MAX_NOTICE_BYTES = 2048


def validate_report_run_id(run_id: str) -> str:
    """Refuse paths and option-like IDs before opening settings or credentials."""
    if not _RUN_ID.fullmatch(run_id) or redact_text(run_id) != run_id:
        message = "run ID must be exactly 32 lowercase hexadecimal characters"
        raise ConfigurationError.single(message, code="HFARG001")
    return run_id


def validate_run_page_arguments(limit: int | None, cursor: str | None) -> None:
    """An opaque cursor is query data, never a path or command-line option."""
    if limit is not None and (type(limit) is not int or not 1 <= limit <= _MAX_PAGE_SIZE):
        message = "run page limit must be between 1 and 10000"
        raise ConfigurationError.single(message, code="HFARG002")
    if cursor is not None and (not _CURSOR.fullmatch(cursor) or redact_text(cursor) != cursor):
        message = "run page cursor is not a safe bounded opaque token"
        raise ConfigurationError.single(message, code="HFARG002")


def _read_capabilities(client: ApiClient) -> Capabilities | ClientRead:
    response = client.read("/api/v1/capabilities")
    if response.envelope.exit_code:
        return response
    try:
        capabilities = Capabilities.model_validate(response.envelope.data)
    except ValueError:
        raise ClientProtocolError from None
    if response.envelope.command != "capabilities" or not capabilities.reads:
        raise ClientProtocolError
    return capabilities


def _successful_read(response: ClientRead, command: str) -> None:
    if (
        response.envelope.command != command
        or response.archive_id is None
        or response.config_fingerprint is None
    ):
        raise ClientProtocolError


def read_runs_page(
    client: ApiClient, *, limit: int | None = None, cursor: str | None = None
) -> ClientRead:
    """Return one original page; a failed capability/page Envelope stays intact."""
    validate_run_page_arguments(limit, cursor)
    capabilities = _read_capabilities(client)
    if isinstance(capabilities, ClientRead):
        return capabilities
    effective_limit = min(100, capabilities.max_page_size) if limit is None else limit
    if effective_limit > capabilities.max_page_size:
        message = "run page limit exceeds the authenticated server limit"
        raise ConfigurationError.single(message, code="HFARG002")
    query: dict[str, str | int] = {"limit": effective_limit}
    if cursor is not None:
        query["cursor"] = cursor
    response = client.read("/api/v1/runs", query)
    if response.envelope.exit_code:
        return response
    _successful_read(response, "runs")
    rows = response.envelope.data.get("runs")
    if (
        set(response.envelope.data) != {"runs"}
        or not isinstance(rows, list)
        or len(rows) > effective_limit
        or any(not isinstance(row, str) or not _RUN_ID.fullmatch(row) for row in rows)
        or len(set(rows)) != len(rows)
        or (response.next_cursor is not None and not rows)
        or (cursor is not None and response.next_cursor == cursor)
    ):
        raise ClientProtocolError
    run_read_metadata(response)
    return response


def read_run_report(client: ApiClient, run_id: str) -> ClientRead:
    """Bind requested, wrapper and durable identities without rewriting report data."""
    checked = validate_report_run_id(run_id)
    capabilities = _read_capabilities(client)
    if isinstance(capabilities, ClientRead):
        return capabilities
    response = client.read("/api/v1/runs/" + checked)
    if response.envelope.exit_code:
        return response
    _successful_read(response, "runs read")
    payload = response.envelope.data.get("report")
    if set(response.envelope.data) != {"report"} or not isinstance(payload, dict):
        raise ClientProtocolError
    model: type[RunReport] | type[RecoveryReport] | type[VerificationReport] = RunReport
    command = payload.get("command")
    if isinstance(command, str) and command.startswith("verify"):
        model = VerificationReport
    elif isinstance(command, str) and command.startswith("recover"):
        model = RecoveryReport
    try:
        exact_version(payload.get("schema_version"))
        report = model.model_validate(payload)
    except ValueError, HfcacheError:
        raise ClientProtocolError from None
    if (
        response.envelope.run_id != checked
        or report.run_id != checked
        or report.archive_id != response.archive_id
    ):
        raise ClientProtocolError
    run_read_metadata(response)
    return response


def run_read_metadata(response: ClientRead) -> str | None:
    """Render only bounded nonsecret read correlation, separate from the Envelope."""
    if response.envelope.exit_code:
        return None
    if response.envelope.command not in {"runs", "runs read"}:
        raise ClientProtocolError
    _successful_read(response, response.envelope.command)
    cursor = response.next_cursor
    if cursor is not None and not _CURSOR.fullmatch(cursor):
        raise ClientProtocolError
    if response.envelope.command == "runs read" and cursor is not None:
        raise ClientProtocolError
    metadata = {
        "schema_version": 1,
        "command": response.envelope.command,
        "run_id": response.envelope.run_id,
        "request_id": response.request_id,
        "archive_id": response.archive_id,
        "config_fingerprint": response.config_fingerprint,
        "next_cursor": cursor,
    }
    line = _NOTICE + json.dumps(metadata, separators=(",", ":"))
    if len(line.encode("utf-8")) > _MAX_NOTICE_BYTES or any(
        isinstance(value, str) and redact_text(value) != value for value in metadata.values()
    ):
        raise ClientProtocolError
    return line
