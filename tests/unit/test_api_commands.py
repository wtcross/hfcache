"""Public HTTP commands exercise the real services with a hermetic Hub/archive."""

import asyncio
import time

import httpx
import pytest

from hfcache import locking, storage
from hfcache.api.app import create_app
from hfcache.archive import initialize_archive
from hfcache.credentials import ResolvedToken, TokenSource
from hfcache.errors import IntegrityError, Problem
from hfcache.hub import HubClient
from hfcache.identity import new_transaction_id
from hfcache.logging import reset
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.preflight import Check
from hfcache.publication import read_reference
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.storage import parse_mount_table
from tests.unit.test_api_operations import READER, READER_HEADERS, WRITER, WRITER_HEADERS
from tests.unit.test_synchronize import ARCHIVE_ID, CONFIG, CONTENT, DATASET, MODEL, SHA_A, FakeHub
from tests.unit.test_verification import nfs_line


@pytest.fixture
def configured(tmp_path, monkeypatch):
    reset()
    root = tmp_path / "archive"
    root.mkdir()
    table = tmp_path / "mountinfo"
    table.write_text(nfs_line(str(root)))
    monkeypatch.setattr(storage, "MOUNT_TABLE", table)
    monkeypatch.setattr(locking, "LOCK_DIRECTORY", tmp_path / "run")
    layout = ArchiveLayout(root)
    initialize_archive(layout, archive_id=ARCHIVE_ID, table=parse_mount_table(nfs_line(str(root))))
    archive_config = tmp_path / "config.toml"
    archive_config.write_text(CONFIG.format(root=root, archive_id=ARCHIVE_ID, reserve_gib=0))
    credentials = {}
    for name, token in (("writer", WRITER), ("reader", READER)):
        path = tmp_path / name
        path.write_text(token)
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(archive_config),
            "state_directory": str(tmp_path / "state"),
            "credentials": credentials,
            "listener": {"allowed_hosts": ["testserver"]},
        }
    )
    hub = FakeHub(
        revisions={SHA_A: dict(CONTENT)}, heads={MODEL.selector: SHA_A, DATASET.selector: SHA_A}
    )
    client = HubClient(api=hub, token=ResolvedToken(source=TokenSource.NONE))
    monkeypatch.setattr("hfcache.services.commands.HubClient.of", lambda *_args, **_kwargs: client)
    monkeypatch.setattr(
        "hfcache.services.commands.hub_checks", lambda *_: [Check.passed("hub_dns", "fake Hub")]
    )
    yield server, layout, hub, tmp_path / "daemon.lock"
    reset()


async def exercise(configured, action, **options):
    server, _, _, lock = configured
    app = create_app(server, instance_lock_path=lock, **options)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client,
    ):
        await action(client, app)


async def submit(client, path, body, key, *, headers=WRITER_HEADERS):
    response = await client.post(path, json=body, headers=headers | {"Idempotency-Key": key})
    assert response.status_code == 202, response.text
    accepted = response.json()
    assert response.headers["location"] == accepted["links"]["status"]
    assert accepted["operation"]["operation_id"]
    assert "envelope" not in accepted
    return accepted


async def result(client, accepted):
    deadline = time.monotonic() + 10
    while True:
        response = await client.get(accepted["links"]["status"], headers=READER_HEADERS)
        assert response.status_code == 200
        state = response.json()["envelope"]["data"]["operation"]["state"]
        if state in {"succeeded", "failed"}:
            break
        assert state != "interrupted", response.text
        assert time.monotonic() < deadline, response.text
        await asyncio.sleep(0.01)
    response = await client.get(accepted["links"]["result"], headers=READER_HEADERS)
    assert response.status_code == 200, response.text
    return response.json()["envelope"]


def test_sync_rest_runs_real_publication_and_reobserves_without_download(configured):
    _, layout, hub, _ = configured

    async def action(client, app):
        first = await submit(client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, "first")
        completed = await result(client, first)
        assert completed["exit_code"] == 0
        assert completed["command"] == "sync"
        assert completed["run_id"] != first["operation"]["operation_id"]
        assert completed["data"]["repositories"][0]["status"] == "completed_with_warnings"
        assert completed["data"]["repositories"][0]["warnings"] == ["HFWRN011"]
        assert (layout.root / completed["data"]["report"]).is_file()
        reference = read_reference(layout, RepositoryLayout(layout, MODEL).current_ref)
        assert reference.commit_sha == SHA_A
        assert (layout.published / reference.tree / "weights.bin").read_bytes() == CONTENT[
            "weights.bin"
        ]
        assert len(hub.downloads) == 1
        second = await submit(client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, "second")
        again = await result(client, second)
        assert again["exit_code"] == 0
        assert again["data"]["repositories"][0]["status"] == "skipped"
        assert len(hub.downloads) == 1

    asyncio.run(exercise(configured, action))


def test_reader_plan_and_explicit_diagnostics_keep_effects_and_lock_boundaries(configured):
    _, layout, hub, _ = configured

    async def action(client, app):
        plan = await submit(client, "/api/v1/plans", {}, "plan", headers=READER_HEADERS)
        planned = await result(client, plan)
        assert planned["exit_code"] == 0
        assert len(planned["data"]["repositories"]) == 2
        assert hub.downloads == []
        assert list(layout.runs.iterdir()) == []
        with locking.exclusive_lock(locking.lock_path(), command="external writer", wait_seconds=0):
            readonly = await submit(
                client,
                "/api/v1/diagnostics",
                {"read_only": True},
                "readonly",
                headers=READER_HEADERS,
            )
            checked = await result(client, readonly)
            assert checked["exit_code"] == 0
            assert any(row["name"] == "hub_dns" for row in checked["data"]["checks"])
            probing = await submit(client, "/api/v1/diagnostics", {"read_only": False}, "probing")
            refused = await result(client, probing)
            assert refused["exit_code"] == 20
            assert refused["errors"][0]["code"] == "HFMNT010"
        assert list(layout.health.iterdir()) == []

    asyncio.run(exercise(configured, action))


def test_sync_refuses_unknown_journal_before_first_hub_contact(configured, monkeypatch):
    _, layout, hub, _ = configured
    (layout.transactions / f"{new_transaction_id()}.json").write_text('{"schema_version":999}')
    monkeypatch.setattr(
        hub, "repo_info", lambda *_args, **_kwargs: pytest.fail("Hub before reconciliation")
    )

    async def action(client, app):
        accepted = await submit(client, "/api/v1/syncs", {}, "unknown-journal")
        completed = await result(client, accepted)
        assert completed["exit_code"] == 20
        assert any(item["code"].startswith("HFTXN") for item in completed["errors"])
        assert hub.downloads == []

    asyncio.run(exercise(configured, action))


def test_sync_http_preserves_partial_failure_priority(configured, monkeypatch):
    _, _, hub, _ = configured
    del hub.heads[MODEL.selector]

    def integrity_failure(*_args, **_kwargs):
        message = "synthetic unusable manifest"
        raise IntegrityError.single(message, code="HFVER007")

    monkeypatch.setattr(HubClient, "verify_local", integrity_failure)

    async def action(client, app):
        completed = await result(client, await submit(client, "/api/v1/syncs", {}, "failures"))
        assert completed["exit_code"] == 40
        assert {row["status"] for row in completed["data"]["repositories"]} == {"failed"}
        codes = {error["code"] for error in completed["errors"]}
        assert any(code.startswith("HFHUB") for code in codes)
        assert any(code.startswith("HFVER") for code in codes)

    asyncio.run(exercise(configured, action))


@pytest.mark.parametrize(
    "body",
    [
        {"mode": "new"},
        {"mode": "full"},
        {"mode": "revision", "revision": f"{MODEL.selector}@{SHA_A}"},
    ],
)
def test_every_public_verification_mode_delegates_and_preserves_exact_integrity_result(
    configured, body
):
    class Executor:
        def __init__(self):
            self.calls = []

        def check_available(self):
            pass

        def reconcile(self, receipt):
            pytest.fail("unexpected reattachment")

        def execute(self, operation_id, request, expected_fingerprint, remaining_wait_seconds):
            self.calls.append((operation_id, request, expected_fingerprint, remaining_wait_seconds))
            return ServiceResult(
                "verify --" + request.mode,
                {"delegated": True},
                errors=(Problem("HFVER006", "synthetic integrity finding"),),
                exit_code=40,
            ).envelope(ExecutionContext.create(operation_id=operation_id))

    executor = Executor()

    async def action(client, app):
        accepted = await submit(client, "/api/v1/verifications", body, "verification")
        completed = await result(client, accepted)
        assert completed["exit_code"] == 40
        assert completed["data"] == {"delegated": True}
        assert len(executor.calls) == 1
        assert executor.calls[0][0] == accepted["operation"]["operation_id"]
        assert executor.calls[0][2] == accepted["config_fingerprint"]

    asyncio.run(exercise(configured, action, verification_executor=executor))


def test_installed_validation_reports_domain_failure_without_hub_or_probes(configured, monkeypatch):
    server, _, hub, _ = configured
    monkeypatch.setattr(
        hub, "repo_info", lambda *_args, **_kwargs: pytest.fail("validation contacted Hub")
    )

    async def action(client, app):
        valid = await client.post("/api/v1/config/validate", json={}, headers=READER_HEADERS)
        assert valid.status_code == 200
        assert valid.json()["envelope"]["exit_code"] == 0
        assert valid.json()["envelope"]["data"]["repositories"] == 2
        assert app.state.operations.list() == ()
        server.archive_config.write_text("private_candidate_marker = [")
        invalid = await client.post("/api/v1/config/validate", json={}, headers=READER_HEADERS)
        assert invalid.status_code == 200
        assert invalid.json()["envelope"]["exit_code"] == 10
        assert invalid.json()["config_fingerprint"] is None
        assert "private_candidate_marker" not in invalid.text

    asyncio.run(exercise(configured, action))


def test_validation_and_plan_use_only_trusted_server_hub_file(configured, tmp_path, monkeypatch):
    _, _, hub, _ = configured
    token = "hf_syntheticHubCredential0123456789abcdef0123456789"
    path = tmp_path / "trusted-hub-token"
    path.write_text(token)
    path.chmod(0o600)
    observed = []

    def client_for(resolved, *, endpoint):
        observed.append((resolved.source, resolved.hub_argument, endpoint))
        return HubClient(api=hub, token=resolved)

    monkeypatch.setattr(HubClient, "of", client_for)

    async def action(client, app):
        validated = await client.post("/api/v1/config/validate", json={}, headers=READER_HEADERS)
        assert validated.status_code == 200
        assert validated.json()["envelope"]["data"]["token_source"] == "token-file"
        planned = await result(
            client,
            await submit(client, "/api/v1/plans", {}, "trusted-file-plan", headers=READER_HEADERS),
        )
        assert planned["exit_code"] == 0
        assert observed == [(TokenSource.TOKEN_FILE, token, "https://huggingface.co")]
        assert token not in validated.text
        assert token not in str(planned)
        assert all(
            token.encode() not in file.read_bytes() for file in app.state.operations.root.iterdir()
        )

    asyncio.run(exercise(configured, action, hub_token_file=path))
