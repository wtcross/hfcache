"""MCP-003: mounted protocol/argument attacks cannot expand read authority."""

import asyncio
import json

import httpx2
import pytest
from fastmcp.utilities.asgi_transport import StreamingASGITransport, run_asgi_lifespan

from hfcache.services.mcp_queries import MetadataRead
from tests.unit.test_mcp_tools import (
    MCP,
    PRIVATE_INPUT,
    TOOLS,
    call,
    error_text,
    forbid_effects,
    mounted,
    snapshot,
    wire,
)
from tests.unit.test_mcp_tools import archive as archive  # noqa: PLC0414 - shared fixture
from tests.unit.test_server_bootstrap import isolate_logging  # noqa: F401 - autouse fixture
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture

MUTATIONS = (
    {"apply": True},
    {"dry_run": False},
    {"preview": False},
    {"command": "sync"},
    {"mode": "full"},
    {"operation_id": "a" * 32},
    {"idempotency_key": PRIVATE_INPUT},
    {"candidate": "schema_version=1\n[hub]\ncredential_name='" + PRIVATE_INPUT + "'"},
    {"archive_root": "/" + PRIVATE_INPUT},
    {"config": "/" + PRIVATE_INPUT},
    {"path": "../../" + PRIVATE_INPUT},
    {"url": "https://" + PRIVATE_INPUT + ".invalid/"},
    {"token_file": "/" + PRIVATE_INPUT},
    {"token": MCP},
    {"credential_name": PRIVATE_INPUT},
    {"transaction_ids": ["b" * 32]},
    {"reason": PRIVATE_INPUT, "repair": True},
)
WRITER_NAMES = (
    "sync",
    "verify",
    "verify --new",
    "verify --full",
    "verify --revision",
    "verify --estimate",
    "doctor",
    "doctor --read-only",
    "recover",
    "recover --dry-run",
    "recover --apply",
    "archive init",
    "prune",
    "prune --dry-run",
    "prune --apply",
    "purge",
    "purge --dry-run",
    "purge --apply",
    "quarantine",
    "quarantine --list",
    "quarantine --delete",
    "quarantine --dry-run",
    "quarantine --apply",
    "repair",
    "repair --dry-run",
    "repair --apply",
    "plan",
    "config validate",
    "submit",
    "execute",
    "invoke",
    "run",
    "call",
    "dispatch",
    "fetch_url",
    "read_file",
    "read_path",
    "api_v1_syncs_post",
    "post_api_v1_syncs",
    "post_api_v1_verifications",
    "/api/v1/syncs",
    "/api/v1/diagnostics",
    "hfcache.sync",
    "get_archive_status@12345678",
    "list_repositories@12345678",
)
HEADERS = {
    "authorization": "Bearer " + MCP,
    "accept": "application/json, text/event-stream",
    "mcp-protocol-version": "2025-11-25",
}


def forbid_writers(monkeypatch, archive):
    forbid_effects(monkeypatch)

    def forbidden(*_args, **_kwargs):
        pytest.fail("MCP reached durable operation admission")

    monkeypatch.setattr(archive.app.state.operations, "admit", forbidden)


async def rpc(client, archive, tmp_path, method, params):
    """Snapshot the entire fixture parent, including runtime/config/credential siblings."""
    before = snapshot(tmp_path)
    receipts = archive.app.state.operations.list()
    response = await client.post(
        "/mcp/",
        headers=HEADERS,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
    )
    assert snapshot(tmp_path) == before
    assert archive.app.state.operations.list() == receipts == ()
    assert PRIVATE_INPUT not in response.text
    assert MCP not in response.text
    assert "Traceback" not in response.text
    assert str(tmp_path) not in response.text
    assert response.status_code == 200, response.text
    return response.json()


def refused(payload):
    if "error" in payload:
        assert type(payload["error"]["code"]) is int
        assert "data" not in payload["error"]
        return
    assert payload["result"]["isError"] is True
    assert "structuredContent" not in payload["result"]


@pytest.mark.parametrize("tool", tuple(TOOLS))
def test_every_tool_rejects_mutation_fields_without_archive_or_control_writes(
    archive, monkeypatch, tmp_path, capfd, tool
):
    async def check():
        async with mounted(archive) as client:
            forbid_writers(monkeypatch, archive)
            for mutation in MUTATIONS:
                before = snapshot(tmp_path)
                result = await call(client, archive, tool, archive.calls[tool] | mutation)
                text = error_text(result)
                assert "HFAPI006" in text
                assert PRIVATE_INPUT not in text
                assert MCP not in text
                assert snapshot(tmp_path) == before

    asyncio.run(check())
    captured = capfd.readouterr()
    for secret in (PRIVATE_INPUT, MCP):
        assert secret not in captured.out + captured.err


def test_all_writer_command_names_and_generic_dispatch_aliases_are_unknown(
    archive, monkeypatch, tmp_path, capfd
):
    async def check():
        async with (
            run_asgi_lifespan(archive.app),
            httpx2.AsyncClient(
                transport=StreamingASGITransport(archive.app),
                base_url="http://localhost",
                trust_env=False,
            ) as client,
        ):
            forbid_writers(monkeypatch, archive)
            for name in WRITER_NAMES:
                payload = await rpc(
                    client,
                    archive,
                    tmp_path,
                    "tools/call",
                    {
                        "name": name,
                        "arguments": {
                            "command": "sync",
                            "apply": True,
                            "path": "/" + PRIVATE_INPUT,
                            "token": MCP,
                        },
                    },
                )
                refused(payload)
                assert "HFAPI007" in json.dumps(payload)

    asyncio.run(check())
    captured = capfd.readouterr()
    for secret in (PRIVATE_INPUT, MCP):
        assert secret not in captured.out + captured.err


def test_resources_prompts_and_background_tasks_cannot_expand_the_registry(
    archive, monkeypatch, tmp_path, capfd
):
    async def check():
        async with (
            run_asgi_lifespan(archive.app),
            httpx2.AsyncClient(
                transport=StreamingASGITransport(archive.app),
                base_url="http://localhost",
                trust_env=False,
            ) as client,
        ):
            forbid_writers(monkeypatch, archive)
            for method, field in (
                ("resources/list", "resources"),
                ("resources/templates/list", "resourceTemplates"),
                ("prompts/list", "prompts"),
            ):
                payload = await rpc(client, archive, tmp_path, method, {})
                assert payload["result"][field] == []
            for method, params in (
                ("resources/read", {"uri": "file:///" + PRIVATE_INPUT}),
                ("resources/read", {"uri": "https://" + PRIVATE_INPUT + ".invalid/"}),
                ("resources/read", {"uri": "hfcache://sync/" + PRIVATE_INPUT}),
                ("prompts/get", {"name": "sync", "arguments": {"command": PRIVATE_INPUT}}),
                (
                    "prompts/get",
                    {"name": "get_archive_status", "arguments": {"path": PRIVATE_INPUT}},
                ),
                ("tasks/list", {}),
                ("tasks/get", {"taskId": PRIVATE_INPUT}),
                ("tasks/result", {"taskId": PRIVATE_INPUT}),
                ("tasks/cancel", {"taskId": PRIVATE_INPUT}),
                ("tools/execute", {"name": "sync"}),
                ("hfcache/run", {"command": "sync"}),
                ("invoke", {"name": "sync"}),
            ):
                refused(await rpc(client, archive, tmp_path, method, params))
            # The disabled SDK task extension may ignore a legacy hint and run
            # the same finite read; it must never mint background authority.
            ordinary = await rpc(
                client,
                archive,
                tmp_path,
                "tools/call",
                {
                    "name": "estimate_verification",
                    "arguments": {},
                },
            )
            payload = await rpc(
                client,
                archive,
                tmp_path,
                "tools/call",
                {
                    "name": "estimate_verification",
                    "arguments": {},
                    "task": {"ttl": 1000},
                },
            )
            result = payload["result"]
            assert result["isError"] is False
            assert "task" not in result
            assert "taskId" not in json.dumps(payload)
            body = MetadataRead.model_validate(result["structuredContent"])
            expected = MetadataRead.model_validate(ordinary["result"]["structuredContent"])
            assert body.envelope.data == expected.envelope.data
            assert body.envelope.command == expected.envelope.command == "verify --estimate"
            assert body.envelope.exit_code == expected.envelope.exit_code == 0
            assert body.next_cursor is None
            refused(await rpc(client, archive, tmp_path, "tasks/list", {}))

    asyncio.run(check())
    captured = capfd.readouterr()
    for secret in (PRIVATE_INPUT, MCP):
        assert secret not in captured.out + captured.err


def test_exact_registry_and_valid_reads_preserve_archive_control_and_runtime_directories(
    archive, monkeypatch, tmp_path, capfd
):
    async def check():
        async with mounted(archive) as client:
            forbid_writers(monkeypatch, archive)
            before = snapshot(tmp_path)
            tools = await client.list_tools()
            assert {tool.name for tool in tools} == TOOLS.keys()
            assert all(
                tool.execution is None or tool.execution.task_support == "forbidden"
                for tool in tools
            )
            assert await client.list_resources() == []
            assert await client.list_resource_templates() == []
            assert await client.list_prompts() == []
            assert snapshot(tmp_path) == before
            for name, arguments in archive.calls.items():
                before = snapshot(tmp_path)
                result = await call(client, archive, name, arguments)
                wire(result, archive)
                assert MCP not in json.dumps(result.structured_content) + str(result.content)
                assert snapshot(tmp_path) == before

    asyncio.run(check())
    captured = capfd.readouterr()
    assert MCP not in captured.out + captured.err
