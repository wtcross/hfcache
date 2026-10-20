"""Actual run CLI processes use only authenticated private Unix reads (decision 136)."""

import asyncio
import json
import subprocess
import sys
from datetime import timedelta

import pytest

from hfcache.api.app import create_app
from hfcache.config import load_config
from hfcache.identity import RunId
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.queries import LocalQueries
from tests.fixtures import examples
from tests.unit.test_api_reads import write_model
from tests.unit.test_cli_runs import PREFIX
from tests.unit.test_server_bootstrap import (
    exercise,
    isolate_logging,  # noqa: F401 - autouse fixture
)
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture

_ISOLATED_CLI = """
import os, runpy, sys
blocked = (os.fsencode(sys.argv.pop(1)), b'/srv/hfcache', b'/etc/hfcache')
def audit(event, arguments):
    if event not in {'open', 'os.listdir', 'os.scandir'} or not arguments:
        return
    path = arguments[0]
    if isinstance(path, (str, bytes)):
        selected = os.fsencode(path)
        if any(selected == root or selected.startswith(root+b'/') for root in blocked):
            raise RuntimeError('CLI attempted forbidden local archive or writer-policy access')
sys.addaudithook(audit)
sys.argv[0] = 'hfcache'
runpy.run_module('hfcache', run_name='__main__')
"""


@pytest.fixture
def policy(request):
    return request.getfixturevalue("socket_policy")


def _process(selected, archive, *arguments):
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            _ISOLATED_CLI,
            str(archive),
            "--json",
            "--client-config",
            str(selected),
            *arguments,
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def _metadata(result):
    lines = [line for line in result.stderr.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1
    return json.loads(lines[0][len(PREFIX) :])


@pytest.mark.parametrize("role", ["reader", "writer", "wrong"])
def test_real_cli_private_socket_pages_reports_and_refusals_without_client_archive_access(  # noqa: PLR0915 - one actual daemon lifecycle
    policy, tmp_path, role
):
    token = policy.credentials.writer.file
    if role in {"reader", "wrong"}:
        token = tmp_path / (role + ".token")
        token.write_text("synthetic-run-reader-token-" + "R" * 40)
        token.chmod(0o600)
    overrides = {"limits": {"max_page_size": 1}}
    if role == "reader":
        overrides["credentials"] = policy.credentials.model_dump(mode="json") | {
            "reader": {"file": str(token)}
        }
    policy = validate_server_config_mapping(policy.model_dump(mode="json") | overrides)
    selected = tmp_path / "run-client.toml"
    selected.write_text(
        f'schema_version=1\napi_socket="{policy.listener.unix_socket}"\n'
        f'api_token_file="{token}"\nexpected_archive_id="{examples.ARCHIVE_ID}"\n'
        "read_retries=0\n"
    )
    queries = LocalQueries(load_config(policy.archive_config))
    application = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")
    observed, payloads = [], []

    @application.middleware("http")
    async def capture(request, call_next):
        observed.append((request.method, request.url.path))
        assert "idempotency-key" not in request.headers
        response = await call_next(request)
        original = response.body_iterator

        async def body():
            chunks = []
            async for chunk in original:
                chunks.append(chunk)
                yield chunk
            payloads.append(json.loads(b"".join(chunks)))

        response.body_iterator = body()
        return response

    async def request():  # noqa: PLR0915 - exercise exact wire through one private daemon
        async def invoke(*args):
            result = await asyncio.to_thread(_process, selected, queries.layout.root, *args)
            assert "forbidden local archive" not in result.stderr
            assert str(token) not in result.stdout
            assert token.read_text() not in result.stdout
            return result

        empty = await invoke("runs", "list")
        if role == "wrong":
            assert empty.returncode == 10, empty.stderr
            assert json.loads(empty.stdout)["errors"][0]["code"] == "HFAPI001"
            assert PREFIX not in empty.stderr
            return
        assert empty.returncode == 0, empty.stderr
        assert json.loads(empty.stdout) == payloads[-1]["envelope"]
        assert json.loads(empty.stdout)["data"] == {"runs": []}
        assert _metadata(empty)["next_cursor"] is None
        first = examples.run_report()
        second = first.model_copy(
            update={
                "run_id": "e" * 32,
                "started_at": first.started_at + timedelta(seconds=1),
                "completed_at": first.completed_at + timedelta(seconds=1),
            }
        )
        for report in (first, second):
            write_model(queries.layout.run_report(report.started_at, RunId(report.run_id)), report)
        page = await invoke("runs", "list", "--limit", "1")
        assert page.returncode == 0, page.stderr
        assert json.loads(page.stdout) == payloads[-1]["envelope"]
        assert json.loads(page.stdout)["data"] == {"runs": [second.run_id]}
        notice = _metadata(page)
        assert notice["archive_id"] == examples.ARCHIVE_ID
        assert notice["config_fingerprint"] == queries.config.fingerprint()
        assert notice["next_cursor"] is not None
        last = await invoke("runs", "list", "--limit", "1", "--cursor=" + notice["next_cursor"])
        assert last.returncode == 0, last.stderr
        assert json.loads(last.stdout)["data"] == {"runs": [first.run_id]}
        assert _metadata(last)["next_cursor"] is None
        detail = await invoke("--quiet", "runs", "show", "--", first.run_id)
        assert detail.returncode == 0, detail.stderr
        assert json.loads(detail.stdout) == payloads[-1]["envelope"]
        assert json.loads(detail.stdout)["data"]["report"] == first.model_dump(mode="json")
        assert _metadata(detail)["run_id"] == first.run_id
        assert _metadata(detail)["next_cursor"] is None
        missing = await invoke("runs", "show", "--", "f" * 32)
        assert missing.returncode == 10, missing.stderr
        assert json.loads(missing.stdout)["errors"][0]["code"] == "HFARG004"
        assert payloads[-1]["code"] == "HFARG004"
        assert PREFIX not in missing.stderr
        # Inventory drift invalidates the original cursor; never restart silently.
        third = second.model_copy(
            update={
                "run_id": "d" * 32,
                "started_at": second.started_at + timedelta(seconds=1),
                "completed_at": second.completed_at + timedelta(seconds=1),
            }
        )
        write_model(queries.layout.run_report(third.started_at, RunId(third.run_id)), third)
        stale = await invoke("runs", "list", "--limit", "1", "--cursor=" + notice["next_cursor"])
        assert stale.returncode == 10, stale.stderr
        assert json.loads(stale.stdout)["errors"][0]["code"] == "HFAPI007"
        assert PREFIX not in stale.stderr
        # Server problems retain their classification and request correlation.
        path = queries.layout.run_report(first.started_at, RunId(first.run_id))
        path.write_text('{"schema_version":1,"unexpected":"fixture"}')
        corrupt = await invoke("runs", "show", first.run_id)
        assert corrupt.returncode == 40, corrupt.stderr
        assert json.loads(corrupt.stdout)["errors"][0]["code"] == "HFVER007"
        assert (
            json.loads(corrupt.stdout)["errors"][0]["context"]["request_id"]
            == payloads[-1]["request_id"]
        )
        assert PREFIX not in corrupt.stderr
        assert application.state.operations.list() == ()

    server = build_server(application, policy)
    with listeners(policy.listener) as channels:
        asyncio.run(exercise(server, channels, request))
    assert all(method == "GET" for method, _ in observed)
    assert all(
        path in {"/api/v1/capabilities", "/api/v1/runs"} or path.startswith("/api/v1/runs/")
        for _, path in observed
    )
    assert not policy.listener.unix_socket.exists()
