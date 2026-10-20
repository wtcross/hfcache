"""Installed CLI wheels cross authenticated private UDS boundaries (CP-02/08/11).

The API uses existing deterministic synthetic Hub/verifier fixtures. This proves
wheel/CLI/HTTP/authentication/result compatibility, not Cockpit/PAM or host guards.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from hfcache.api.app import create_app
from hfcache.errors import Problem
from hfcache.identity import RunId
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.context import ExecutionContext, ServiceResult
from tests.fixtures import examples
from tests.installed_cli import installed_cli as installed_cli  # noqa: PLC0414 - shared fixture
from tests.unit.test_api_commands import configured as synthetic_archive  # noqa: F401 - fixture
from tests.unit.test_api_reads import write_model
from tests.unit.test_cli_runs import PREFIX
from tests.unit.test_server_bootstrap import exercise
from tests.unit.test_synchronize import MODEL

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

pytestmark = pytest.mark.build


@dataclass
class WireRecord:
    method: str
    path: str
    key: str | None
    content_length: int
    request: bytearray = field(default_factory=bytearray)
    response: bytearray = field(default_factory=bytearray)
    status: int = 0

    def payload(self):
        return json.loads(self.response)


class WireBoundary:
    """Observe the real wire without consuming/replaying a request or credentials."""

    def __init__(self, app: ASGIApp, *, records: list[WireRecord]):
        self.app, self.records = app, records

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        record = WireRecord(
            scope["method"],
            scope["path"],
            headers.get(b"idempotency-key", b"").decode() or None,
            int(headers.get(b"content-length", b"0")),
        )
        self.records.append(record)

        async def observe_receive():
            message = await receive()
            record.request.extend(message.get("body", b""))
            assert len(record.request) <= 2 * 1024 * 1024
            return message

        async def observe_send(message):
            if message["type"] == "http.response.start":
                record.status = message["status"]
            if message["type"] == "http.response.body":
                record.response.extend(message.get("body", b""))
                assert len(record.response) <= 2 * 1024 * 1024
            await send(message)

        return await self.app(scope, observe_receive, observe_send)


@pytest.fixture
def boundary(request, tmp_path):
    original, layout, hub, lock = request.getfixturevalue("synthetic_archive")
    policy = validate_server_config_mapping(
        original.model_dump(mode="json")
        | {
            "listener": {
                "unix_socket": str(tmp_path / "installed.sock"),
                "tcp_enabled": False,
                "allowed_hosts": ["localhost"],
            },
            "limits": original.limits.model_dump(mode="json") | {"max_page_size": 1},
        }
    )
    settings = {}
    for role in ("writer", "reader", "wrong", "unsafe"):
        credential = getattr(policy.credentials, role, None)
        token = credential.file if credential else tmp_path / (role + ".token")
        if credential is None:
            token.write_text("synthetic-installed-cli-" + role + "Q" * 40)
            token.chmod(0o644 if role == "unsafe" else 0o600)
        selected = tmp_path / (role + "-client.toml")
        selected.write_text(
            f'schema_version=1\napi_socket="{policy.listener.unix_socket}"\n'
            f'api_token_file="{token}"\nexpected_archive_id="{examples.ARCHIVE_ID}"\n'
            "read_retries=0\npoll_interval=0.01\n"
        )
        settings[role] = selected
    return policy, layout, hub, lock, settings


def serve(boundary, action, **options):
    policy, _, _, lock, _ = boundary
    records = []
    application = create_app(policy, instance_lock_path=lock, **options)
    application.add_middleware(WireBoundary, records=records)
    server = build_server(application, policy)
    with listeners(policy.listener) as channels:
        asyncio.run(exercise(server, channels, lambda: action(application, records)))
    assert not policy.listener.unix_socket.exists()


def client(installed_cli, boundary, role="writer"):
    policy, layout, _, _, settings = boundary

    async def invoke(*arguments):
        result = await asyncio.to_thread(
            installed_cli.invoke,
            settings[role],
            layout.root,
            policy.listener.unix_socket,
            *arguments,
        )
        for credential in (policy.credentials.writer, policy.credentials.reader):
            assert credential.file.read_text() not in result.stdout + result.stderr
        return result

    return invoke


def notice(result):
    (line,) = [line for line in result.stderr.splitlines() if line.startswith(PREFIX)]
    assert len(line.encode()) <= 2048
    return json.loads(line[len(PREFIX) :])


def test_installed_wheel_matches_source_bytes_and_isolates_real_console_entrypoint(installed_cli):
    assert installed_cli.identity["matched_python_files"] > 0
    assert installed_cli.identity["isolated_entrypoint"] is True
    assert installed_cli.identity["cwd_outside_checkout"] is True
    result = installed_cli.invoke(
        installed_cli.workspace / "absent-client.toml",
        installed_cli.workspace / "absent-archive",
        installed_cli.workspace / "absent.sock",
        "--help",
    )
    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout


def test_installed_candidate_exact_utf8_validation_and_escaped_wire_size_refusal(
    installed_cli, boundary, tmp_path
):
    policy, layout, hub, _, _ = boundary
    candidate = tmp_path / "candidate.toml"
    content = (
        policy.archive_config.read_text()
        + '\ntags=["coding"]\n# synthetic quote \\" and slash \\\\ ☃\n'
    )
    candidate.write_text(content, encoding="utf-8")
    invoke = client(installed_cli, boundary)

    async def action(application, records):
        valid = await invoke("--config", str(candidate), "config", "validate")
        assert valid.returncode == 0, valid.stderr
        assert json.loads(valid.stdout) == records[-1].payload()["envelope"]
        assert json.loads(valid.stdout)["data"]["authority_compatible"] is True
        assert records[-1].key is None
        assert json.loads(records[-1].request) == {"candidate": content}
        assert hub.downloads == []
        assert application.state.operations.list() == ()
        candidate.write_text(content.replace('tags=["coding"]', 'tags=["vision"]'))
        retagged = await invoke("--config", str(candidate), "config", "validate")
        assert retagged.returncode == 0, retagged.stderr
        assert json.loads(retagged.stdout) == records[-1].payload()["envelope"]
        assert (
            json.loads(retagged.stdout)["data"]["config_fingerprint"]
            == json.loads(valid.stdout)["data"]["config_fingerprint"]
        )
        assert json.loads(records[-1].request)["candidate"] == candidate.read_text()
        candidate.write_text("invalid synthetic TOML [")
        invalid = await invoke("--config", str(candidate), "config", "validate")
        assert invalid.returncode == 10, invalid.stderr
        assert json.loads(invalid.stdout) == records[-1].payload()["envelope"]
        assert json.loads(invalid.stdout)["data"]["syntax_valid"] is False
        assert "invalid synthetic TOML" not in invalid.stdout
        # Raw candidate fits 1 MiB, but JSON escaping exceeds the server's bound.
        candidate.write_text(content + "#" + '"' * 550_000 + "\n")
        assert candidate.stat().st_size < 1024 * 1024
        oversized_wire = await invoke("--config", str(candidate), "config", "validate")
        assert oversized_wire.returncode == 10, oversized_wire.stderr
        assert records[-1].status == 413
        assert records[-1].content_length > policy.limits.max_request_bytes
        problem = records[-1].payload()
        error = json.loads(oversized_wire.stdout)["errors"][0]
        assert error["code"] == problem["code"] == "HFAPI006"
        assert error["context"]["request_id"] == problem["request_id"]
        before = len(records)
        candidate.write_bytes(b"#" * (1024 * 1024 + 1))
        oversized_file = await invoke("--config", str(candidate), "config", "validate")
        assert oversized_file.returncode == 10
        assert json.loads(oversized_file.stdout)["errors"][0]["code"] == "HFARG002"
        assert len(records) == before
        for raw, code in ((b"", "HFARG002"), (b"\xff", "HFCFG001")):
            candidate.write_bytes(raw)
            refused = await invoke("--config", str(candidate), "config", "validate")
            assert refused.returncode == 10
            assert json.loads(refused.stdout)["errors"][0]["code"] == code
            assert len(records) == before
        assert application.state.operations.list() == ()
        assert list(layout.runs.iterdir()) == []

    serve(boundary, action)


@pytest.mark.parametrize(
    ("role", "code"),
    [("wrong", "HFAPI001"), ("reader", "HFAPI018"), ("unsafe", "HFAPI003"), ("pin", "HFAPI017")],
)
def test_installed_candidate_authentication_and_capability_fail_closed(
    installed_cli, boundary, tmp_path, role, code
):
    policy, _, hub, _, _ = boundary
    candidate = tmp_path / "candidate.toml"
    candidate.write_text(policy.archive_config.read_text())
    invoke = client(installed_cli, boundary, "writer" if role == "pin" else role)

    async def action(application, records):
        result = await invoke(
            *(["--expected-client-scope", "f" * 64] if role == "pin" else []),
            "--config",
            str(candidate),
            "config",
            "validate",
        )
        assert result.returncode == 10, result.stderr
        assert json.loads(result.stdout)["errors"][0]["code"] == code
        assert all(record.method == "GET" for record in records)
        if role == "unsafe":
            assert records == []
        if role == "wrong":
            assert records[-1].status == 401
            assert (
                json.loads(result.stdout)["errors"][0]["context"]["request_id"]
                == records[-1].payload()["request_id"]
            )
        assert hub.downloads == []
        assert application.state.operations.list() == ()

    serve(boundary, action)


def test_installed_conditional_candidate_plan_keeps_original_key_receipt_and_exact_result(
    installed_cli, boundary, tmp_path
):
    policy, layout, hub, _, _ = boundary
    candidate = tmp_path / "candidate.toml"
    content = policy.archive_config.read_text() + "\n# exact original candidate\n"
    candidate.write_text(content)
    invoke = client(installed_cli, boundary)

    async def action(application, records):
        metadata = await invoke("client", "describe")
        assert metadata.returncode == 0, metadata.stderr
        scope = json.loads(metadata.stdout)["data"]["authority_fingerprint"]
        key = "-installed-candidate-original"
        completed = await invoke(
            "--expected-client-scope",
            scope,
            "--idempotency-key=" + key,
            "--config",
            str(candidate),
            "plan",
            MODEL.selector,
        )
        assert completed.returncode == 0, completed.stderr
        (receipt,) = application.state.operations.list()
        terminal = application.state.operations.result(receipt.operation_id)
        assert json.loads(completed.stdout) == terminal.to_payload()
        assert "Idempotency key: " + key in completed.stderr
        assert "Operation: " + receipt.operation_id in completed.stderr
        submissions = [record for record in records if record.method == "POST"]
        assert len(submissions) == 1
        assert (submissions[0].path, submissions[0].key) == ("/api/v1/plans", key)
        assert submissions[0].payload()["created"] is True
        assert submissions[0].payload()["operation"]["operation_id"] == receipt.operation_id
        assert submissions[0].payload()["archive_id"] == receipt.archive_id
        assert submissions[0].payload()["config_fingerprint"] == receipt.config_fingerprint
        assert json.loads(submissions[0].request) == {
            "candidate": content,
            "selectors": [MODEL.selector],
        }
        durable_before = {
            str(path.relative_to(application.state.operations.root)): path.read_bytes()
            for path in application.state.operations.root.rglob("*.json")
        }
        for mode, handle in (("lookup", key), ("wait", receipt.operation_id)):
            recovered = await invoke(
                "--expected-client-scope", scope, "operations", mode, "--", handle
            )
            assert recovered.returncode == 0, recovered.stderr
            if mode == "wait":
                assert json.loads(recovered.stdout) == terminal.to_payload()
            else:
                assert (
                    json.loads(recovered.stdout)["data"]["operation"]["operation_id"]
                    == receipt.operation_id
                )
        assert sum(record.method == "POST" for record in records) == 1
        assert {
            str(path.relative_to(application.state.operations.root)): path.read_bytes()
            for path in application.state.operations.root.rglob("*.json")
        } == durable_before
        assert all(
            content.encode() not in body and key.encode() not in body
            for body in durable_before.values()
        )
        assert hub.downloads == []
        assert list(layout.runs.iterdir()) == []

    serve(boundary, action)


@pytest.mark.parametrize("mode", ["sync", "verify"])
def test_installed_manual_full_jobs_preserve_exact_failed_terminal_and_original_observation(
    installed_cli, boundary, mode
):
    _, _, hub, _, _ = boundary
    hub.heads.clear()

    class Verifier:
        def check_available(self):
            pass

        def reconcile(self, receipt):
            pytest.fail("Fresh synthetic fixture unexpectedly reattached history")

        def execute(self, operation_id, request, expected_fingerprint, remaining_wait_seconds):
            return ServiceResult(
                "verify --full",
                {},
                errors=(Problem("HFVER006", "Synthetic immutable failure"),),
                exit_code=40,
            ).envelope(ExecutionContext.create(operation_id=operation_id))

    invoke = client(installed_cli, boundary)

    async def action(application, records):
        metadata = await invoke("client", "describe")
        assert metadata.returncode == 0, metadata.stderr
        pin = json.loads(metadata.stdout)["data"]["authority_fingerprint"]
        key = "installed-original-full-" + mode
        completed = await invoke(
            "--expected-client-scope",
            pin,
            "--idempotency-key",
            key,
            *(["sync"] if mode == "sync" else ["verify", "--full"]),
        )
        expected = 30 if mode == "sync" else 40
        assert completed.returncode == expected, completed.stderr
        (receipt,) = application.state.operations.list()
        terminal = application.state.operations.result(receipt.operation_id)
        assert json.loads(completed.stdout) == terminal.to_payload()
        assert terminal.exit_code == expected
        assert terminal.run_id != receipt.operation_id
        assert f"Operation: {receipt.operation_id}" in completed.stderr
        for observation, handle in (("lookup", key), ("wait", receipt.operation_id)):
            recovered = await invoke(
                "--expected-client-scope", pin, "operations", observation, "--", handle
            )
            assert recovered.returncode == (expected if observation == "wait" else 0), (
                recovered.stderr
            )
            if observation == "wait":
                assert json.loads(recovered.stdout) == terminal.to_payload()
            else:
                assert (
                    json.loads(recovered.stdout)["data"]["operation"]["operation_id"]
                    == receipt.operation_id
                )
        submissions = [record for record in records if record.method == "POST"]
        assert len(submissions) == 1
        assert submissions[0].key == key
        assert submissions[0].path == (
            "/api/v1/syncs" if mode == "sync" else "/api/v1/verifications"
        )
        assert json.loads(submissions[0].request) == (
            {"selectors": []}
            if mode == "sync"
            else {"mode": "full", "revision": None, "run_id": None}
        )
        assert len(application.state.operations.list()) == 1
        assert hub.downloads == []

    serve(boundary, action, verification_executor=Verifier())


def test_installed_report_pages_detail_and_negative_identity_are_exact_and_read_only(
    installed_cli, boundary
):
    _, layout, _, _, _ = boundary
    first = examples.run_report()
    second = first.model_copy(
        update={
            "run_id": "e" * 32,
            "started_at": first.started_at + timedelta(seconds=1),
            "completed_at": first.completed_at + timedelta(seconds=1),
        }
    )
    for report in (first, second):
        write_model(layout.run_report(report.started_at, RunId(report.run_id)), report)
    invoke = client(installed_cli, boundary, "reader")

    async def action(application, records):
        page = await invoke("runs", "list", "--limit", "1")
        assert page.returncode == 0, page.stderr
        assert json.loads(page.stdout) == records[-1].payload()["envelope"]
        assert json.loads(page.stdout)["data"] == {"runs": [second.run_id]}
        metadata = notice(page)
        assert metadata["archive_id"] == examples.ARCHIVE_ID
        cursor = metadata["next_cursor"]
        assert cursor is not None
        last = await invoke("runs", "list", "--limit", "1", "--cursor=" + cursor)
        assert last.returncode == 0, last.stderr
        assert json.loads(last.stdout)["data"] == {"runs": [first.run_id]}
        assert notice(last)["next_cursor"] is None
        detail = await invoke("--quiet", "runs", "show", "--", first.run_id)
        assert detail.returncode == 0, detail.stderr
        assert json.loads(detail.stdout) == records[-1].payload()["envelope"]
        assert json.loads(detail.stdout)["data"]["report"] == first.model_dump(mode="json")
        assert notice(detail)["run_id"] == first.run_id
        assert notice(detail)["config_fingerprint"] != first.config_fingerprint
        missing = await invoke("runs", "show", "--", "f" * 32)
        assert missing.returncode == 10, missing.stderr
        assert json.loads(missing.stdout)["errors"][0]["code"] == "HFARG004"
        assert (
            json.loads(missing.stdout)["errors"][0]["context"]["request_id"]
            == records[-1].payload()["request_id"]
        )
        assert PREFIX not in missing.stderr
        layout.run_report(first.started_at, RunId(first.run_id)).write_text(
            '{"schema_version":1,"unknown":"synthetic"}'
        )
        corrupt = await invoke("runs", "show", "--", first.run_id)
        assert corrupt.returncode == 40, corrupt.stderr
        assert json.loads(corrupt.stdout)["errors"][0]["code"] == "HFVER007"
        assert (
            json.loads(corrupt.stdout)["errors"][0]["context"]["request_id"]
            == records[-1].payload()["request_id"]
        )
        assert PREFIX not in corrupt.stderr
        assert application.state.operations.list() == ()
        assert all(record.method == "GET" and record.key is None for record in records)

    serve(boundary, action)
