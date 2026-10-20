"""Manual full jobs cross the real CLI/UDS and private verifier boundaries."""

import asyncio
import json

import pytest

from hfcache.api.app import create_app
from hfcache.paths import RepositoryLayout
from hfcache.publication import read_reference
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping
from tests.api_cli import private_verifier
from tests.unit.test_api_commands import configured as hermetic_archive  # noqa: F401 - fixture
from tests.unit.test_cli_client_describe import _process
from tests.unit.test_server_bootstrap import exercise
from tests.unit.test_synchronize import MODEL


@pytest.fixture
def configured(request):
    return request.getfixturevalue("hermetic_archive")


@pytest.mark.parametrize(
    "case",
    [
        (["sync"], "/api/v1/syncs", {"selectors": []}, False),
        (
            ["verify", "--full"],
            "/api/v1/verifications",
            {"mode": "full", "revision": None, "run_id": None},
            False,
        ),
        (
            ["verify", "--full"],
            "/api/v1/verifications",
            {"mode": "full", "revision": None, "run_id": None},
            True,
        ),
    ],
)
def test_full_job_actual_cli_socket_has_one_original_submission_and_exact_wait(
    configured, tmp_path, monkeypatch, case
):
    arguments, route, body, damaged = case
    policy, layout, _, lock = configured
    policy = validate_server_config_mapping(
        policy.model_dump(mode="json")
        | {
            "listener": {
                "unix_socket": str(tmp_path / "manual.sock"),
                "tcp_enabled": False,
                "allowed_hosts": ["localhost"],
            }
        }
    )
    selected = tmp_path / "manual-client.toml"
    selected.write_text(
        f'schema_version=1\napi_socket="{policy.listener.unix_socket}"\n'
        f'api_token_file="{policy.credentials.writer.file}"\nread_retries=0\n'
    )
    observed = []
    with private_verifier(policy) as verifier:
        application = create_app(policy, instance_lock_path=lock, verification_executor=verifier)

        @application.middleware("http")
        async def capture(request, call_next):
            if request.method == "POST":
                observed.append(
                    (request.url.path, request.headers.get("idempotency-key"), await request.json())
                )
            return await call_next(request)

        async def request():
            if arguments[0] == "verify":
                seed = await asyncio.to_thread(
                    _process, selected, "--idempotency-key", "seed", "sync"
                )
                assert seed.returncode == 0, seed.stderr
                if damaged:
                    reference = read_reference(layout, RepositoryLayout(layout, MODEL).current_ref)
                    (layout.published / reference.tree / "weights.bin").write_bytes(
                        b"damaged fixture"
                    )

                def forbidden(*_args, **_kwargs):
                    pytest.fail("Offline full verification attempted Hub access")

                monkeypatch.setattr("hfcache.services.commands.HubClient.of", forbidden)
                observed.clear()
            prior = {receipt.operation_id for receipt in application.state.operations.list()}
            metadata = await asyncio.to_thread(_process, selected, "client", "describe")
            assert metadata.returncode == 0, metadata.stderr
            scope = json.loads(metadata.stdout)["data"]["authority_fingerprint"]
            key = "manual-original-full-job"
            completed = await asyncio.to_thread(
                _process,
                selected,
                "--expected-client-scope",
                scope,
                "--idempotency-key",
                key,
                *arguments,
            )
            assert completed.returncode == (40 if damaged else 0), completed.stderr
            (receipt,) = [
                row for row in application.state.operations.list() if row.operation_id not in prior
            ]
            assert receipt.route == route
            assert observed == [(route, key, body)]
            terminal = application.state.operations.result(receipt.operation_id)
            assert json.loads(completed.stdout) == terminal.to_payload()
            assert f"Operation: {receipt.operation_id}" in completed.stderr
            for mode, handle in (("lookup", key), ("wait", receipt.operation_id)):
                recovered = await asyncio.to_thread(
                    _process,
                    selected,
                    "--expected-client-scope",
                    scope,
                    "operations",
                    mode,
                    "--",
                    handle,
                )
                assert recovered.returncode == (40 if damaged and mode == "wait" else 0), (
                    recovered.stderr
                )
                if mode == "wait":
                    assert json.loads(recovered.stdout) == terminal.to_payload()
            assert observed == [(route, key, body)]
            assert {row.operation_id for row in application.state.operations.list()} == prior | {
                receipt.operation_id
            }

        server = build_server(application, policy)
        with listeners(policy.listener) as channels:
            asyncio.run(exercise(server, channels, request))
    assert not policy.listener.unix_socket.exists()
