"""MCP-003: hostile stored evidence stays read-only and cannot expose credentials."""

import asyncio
import json

import httpx2
import pytest
from fastmcp.utilities.asgi_transport import StreamingASGITransport, run_asgi_lifespan

from hfcache.identity import RunId
from hfcache.redaction import register_secret
from hfcache.reporting import RecoveryReport
from hfcache.services.mcp_queries import MetadataReadQueries
from hfcache.services.queries import LocalQueries
from tests.unit.test_mcp_tools import (
    MCP,
    PRIVATE_INPUT,
    call,
    error_text,
    forbid_effects,
    mounted,
    snapshot,
    write,
)
from tests.unit.test_mcp_tools import archive as archive  # noqa: PLC0414 - shared fixture
from tests.unit.test_server_bootstrap import isolate_logging  # noqa: F401 - autouse fixture
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture


@pytest.mark.parametrize("index", [0, 1, 2], ids=["run", "recovery", "verification"])
@pytest.mark.parametrize(
    "damage", ["json", "future", "run", "archive", "timestamp", "symlink", "duplicate"]
)
def test_corrupt_original_reports_refuse_without_repair_or_diagnostic_echo(
    archive, monkeypatch, capfd, index, damage
):
    report = archive.reports[index]
    path = archive.queries.layout.run_report(report.started_at, RunId(report.run_id))
    source = report.model_dump(mode="json")
    if damage == "json":
        path.write_text('{"private": "' + PRIVATE_INPUT, encoding="utf-8")
    elif damage == "symlink":
        target = path.with_suffix(".held")
        path.rename(target)
        path.symlink_to(target.name)
    elif damage == "duplicate":
        # A second valid report filename must claim the exact same run ID.
        duplicate = path.with_name(path.name.replace("2026", "2025", 1))
        assert duplicate != path
        duplicate.write_text(report.to_json(), encoding="utf-8")
    else:
        key, value = {
            "future": ("schema_version", 2),
            "run": ("run_id", "f" * 32),
            "archive": ("archive_id", "ffffffff-ffff-4fff-8fff-ffffffffffff"),
            "timestamp": ("started_at", "2024-01-01T00:00:00Z"),
        }[damage]
        path.write_text(json.dumps(source | {key: value}), encoding="utf-8")
    forbid_effects(monkeypatch)

    async def check():
        async with mounted(archive) as client:
            for tool in (
                ("get_run_report", "get_verification_report") if index == 2 else ("get_run_report",)
            ):
                result = await call(client, archive, tool, {"run_id": report.run_id})
                assert result.is_error
                assert "HFVER007" in error_text(result)
                assert PRIVATE_INPUT not in error_text(result)
                assert str(path) not in error_text(result)

    asyncio.run(check())
    captured = capfd.readouterr()
    assert PRIVATE_INPUT not in captured.out + captured.err


def test_numeric_registered_secret_changes_do_not_fingerprint_report_cursors(archive):
    """INV-002/016: bind public evidence, including when hidden values are JSON integers."""
    report = archive.reports[1]
    assert isinstance(report, RecoveryReport)
    path = archive.queries.layout.run_report(report.started_at, RunId(report.run_id))
    first_secret, second_secret = "7" * 48, "8" * 48
    backend = MetadataReadQueries(archive.queries, archive.queries.config.fingerprint(), 100)
    cursors = []
    for secret in (first_secret, second_secret):
        register_secret(secret)
        source = report.model_dump(mode="json")
        source["remediations"][0]["evidence"] = {"inert_number": int(secret)}
        write(path, RecoveryReport.model_validate(source))
        before = snapshot(archive.queries.layout.root, archive.server.state_directory)
        first = backend.get_run_report(report.run_id, limit=1)
        assert snapshot(archive.queries.layout.root, archive.server.state_directory) == before
        assert first.next_cursor is not None
        cursors.append(first.next_cursor)
    assert cursors[0] == cursors[1]
    continued = backend.get_run_report(report.run_id, limit=1, cursor=cursors[0])
    assert continued.result.data["entries"][0]["transaction_id"] == "0" * 31 + "2"


@pytest.mark.parametrize("numeric", [False, True], ids=["string-redacted", "number-refused"])
def test_registered_secret_in_actual_report_response_is_redacted_or_refused(
    archive, monkeypatch, capfd, numeric
):
    secret = "6" * 48 if numeric else "private-evidence-" + "p" * 48
    register_secret(secret)
    report = archive.reports[1]
    source = report.model_dump(mode="json")
    source["remediations"][0]["evidence"] = {"untrusted_value": int(secret) if numeric else secret}
    path = archive.queries.layout.run_report(report.started_at, RunId(report.run_id))
    write(path, RecoveryReport.model_validate(source))
    forbid_effects(monkeypatch)

    async def check():
        async with (
            run_asgi_lifespan(archive.app),
            httpx2.AsyncClient(
                transport=StreamingASGITransport(archive.app),
                base_url="http://localhost",
                trust_env=False,
                follow_redirects=False,
            ) as client,
        ):
            before = snapshot(archive.queries.layout.root, archive.server.state_directory)
            response = await client.post(
                "/mcp/",
                headers={
                    "authorization": "Bearer " + MCP,
                    "accept": "application/json, text/event-stream",
                    "mcp-protocol-version": "2025-11-25",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "get_run_report", "arguments": {"run_id": report.run_id}},
                },
            )
            assert snapshot(archive.queries.layout.root, archive.server.state_directory) == before
            assert archive.app.state.operations.list() == ()
            assert secret not in response.text
            if numeric:
                assert response.status_code == 500
                assert "HFAPI008" in response.text
            else:
                assert response.status_code == 200
                data = response.json()["result"]["structuredContent"]["envelope"]["data"]
                assert data["entries"][0]["evidence"]["untrusted_value"] == "[redacted]"

    asyncio.run(check())
    captured = capfd.readouterr()
    assert secret not in captured.out + captured.err


def test_unexpected_reader_exception_is_masked_over_actual_http_and_in_diagnostics(
    archive, monkeypatch, capfd
):
    def fail(self, run_id):
        del self, run_id
        raise RuntimeError(PRIVATE_INPUT + " " + MCP)

    monkeypatch.setattr(LocalQueries, "read_report", fail)
    forbid_effects(monkeypatch)

    async def check():
        async with mounted(archive) as client:
            result = await call(client, archive, "get_run_report", archive.calls["get_run_report"])
            assert result.is_error
            for value in (PRIVATE_INPUT, MCP):
                assert value not in error_text(result)

    asyncio.run(check())
    captured = capfd.readouterr()
    for value in (PRIVATE_INPUT, MCP):
        assert value not in captured.out + captured.err
