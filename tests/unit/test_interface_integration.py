"""API-017: OS CLI processes cross real local listeners and private verification."""

import asyncio
import json
import socket
import sys

import pytest

from hfcache.api.app import create_app
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping
from tests.api_cli import private_verifier
from tests.fixtures.examples import ARCHIVE_ID
from tests.unit.test_api_commands import configured as configured_base  # noqa: F401 - fixture
from tests.unit.test_api_operations import READER, WRITER
from tests.unit.test_mcp_tools import snapshot
from tests.unit.test_server_bootstrap import exercise
from tests.unit.test_synchronize import MODEL


@pytest.fixture
def configured(request):
    return request.getfixturevalue("configured_base")


@pytest.mark.parametrize("endpoint", ["unix", "tcp"])
@pytest.mark.parametrize("small_limit", ["metadata-page", "retained-events"])
def test_actual_cli_processes_preserve_roles_results_and_private_worker_over_real_listeners(  # noqa: PLR0915 - one complete boundary composition
    configured, tmp_path, endpoint, small_limit
):
    base, layout, hub, instance_lock = configured
    settings = validate_server_config_mapping(
        base.model_dump(mode="json")
        | {
            "listener": {
                "unix_socket": str(tmp_path / "api.sock"),
                "tcp_enabled": False,
                "allowed_hosts": ["localhost", "127.0.0.1"],
            },
            "limits": base.limits.model_dump(mode="json")
            | (
                {"max_page_size": 1}
                if small_limit == "metadata-page"
                else {"operation_max_events": 1}
            ),
        }
    )
    client_settings = tmp_path / "client.toml"
    client_settings.write_text(
        f'schema_version=1\nexpected_archive_id="{ARCHIVE_ID}"\n'
        "read_retries=0\npoll_interval=0.01\nwait_timeout=10.0\n"
    )
    with (
        private_verifier(settings) as verifier,
        listeners(settings.listener) as channels,
        socket.socket() as tcp,
    ):
        tcp.bind(("127.0.0.1", 0))
        port = tcp.getsockname()[1]
        app = create_app(settings, instance_lock_path=instance_lock, verification_executor=verifier)
        server = build_server(app, settings)
        target = (
            ["--api-socket", str(settings.listener.unix_socket)]
            if endpoint == "unix"
            else ["--api-url", f"http://127.0.0.1:{port}"]
        )

        async def invoke(role, *arguments, exit_code=0):
            credential = getattr(settings.credentials, role)
            assert credential is not None
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "hfcache",
                "--json",
                "--quiet",
                "--client-config",
                str(client_settings),
                *target,
                "--api-token-file",
                str(credential.file),
                *arguments,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20)
            assert process.returncode == exit_code, stdout.decode() + stderr.decode()
            assert len(stdout.splitlines()) == 1
            for token in (WRITER, READER):
                assert token.encode() not in stdout + stderr
            return json.loads(stdout), stderr.decode()

        async def request():
            sync, sync_notices = await invoke(
                "writer", "--idempotency-key", "final-sync", "sync", MODEL.selector
            )
            assert sync["command"] == "sync"
            assert sync["exit_code"] == 0
            (sync_receipt,) = app.state.operations.list()
            assert sync_receipt.domain_run_id == sync["run_id"]
            assert sync_receipt.operation_id in sync_notices
            assert "final-sync" in sync_notices
            assert app.state.operations.result(sync_receipt.operation_id).to_payload() == sync

            verified, verify_notices = await invoke(
                "writer", "--idempotency-key", "final-verify", "verify", "--full"
            )
            assert verified["command"] == "verify --full"
            assert verified["exit_code"] == 0
            receipts = app.state.operations.list()
            verification = next(row for row in receipts if row.route == "/api/v1/verifications")
            assert verification.operation_id in verify_notices
            assert verification.domain_run_id == verified["run_id"]
            assert app.state.operations.result(verification.operation_id).to_payload() == verified
            assert len(hub.downloads) == 1
            before = snapshot(layout.root, settings.state_directory)

            status, _ = await invoke("reader", "status")
            assert status["command"] == "status"
            assert len(status["data"]["repositories"]) == 2
            shown, _ = await invoke("reader", "operations", "show", verification.operation_id)
            assert shown["data"]["operation"]["operation_id"] == verification.operation_id
            observed, _ = await invoke("reader", "operations", "wait", verification.operation_id)
            assert observed == verified
            denied, _ = await invoke(
                "reader", "--idempotency-key", "forbidden", "sync", MODEL.selector, exit_code=10
            )
            # The public CLI refuses a missing write capability before POST;
            # mounted REST role tests separately prove server-side 403.
            assert denied["errors"][0]["code"] == "HFAPI018"
            assert snapshot(layout.root, settings.state_directory) == before
            assert len(app.state.operations.list()) == 2
            assert len(hub.downloads) == 1

        asyncio.run(exercise(server, [*channels, tcp], request))
        assert app.state.credentials is None
