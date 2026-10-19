"""V39-40: keyed offline writes, lost observers, fresh lock scope and no replay."""

import asyncio
import json
import time
from threading import Event

import httpx
import pytest

from hfcache.api.app import create_app
from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.command_models import CatalogRefreshSubmission
from hfcache.api.operations import OperationStore
from hfcache.catalog_refresh import CatalogRefreshResult
from hfcache.catalog_storage import CatalogWriter, read_tag_snapshot
from hfcache.config import load_config
from hfcache.hub import HubClient
from hfcache.locking import exclusive_lock, lock_path
from hfcache.server_config import InstalledPolicy
from hfcache.services import commands
from hfcache.services.commands import CommandServices
from hfcache.services.context import ExecutionContext
from hfcache.services.requests import SelectionRequest
from tests.fixtures.gguf import gguf
from tests.unit import test_api_commands as api
from tests.unit.test_synchronize import ARCHIVE_ID, MODEL, SHA_A

configured = api.configured
ROUTE = "/api/v1/catalog/refreshes"
BODY = {"selectors": [MODEL.selector], "technical": False}


def tags(server, values):
    source = server.archive_config.read_text()
    needle = f'id = "{MODEL.id}"\n'
    lines = source.splitlines()
    source = "\n".join(line for line in lines if not line.startswith("tags = ")) + "\n"
    server.archive_config.write_text(
        source.replace(needle, needle + f"tags = {json.dumps(values)}\n")
    )


def archive_files(layout):
    return {
        str(path.relative_to(layout.root)): path.read_bytes()
        for path in layout.root.rglob("*")
        if path.is_file()
    }


def no_external_capability(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail(
            "offline refresh resolved credentials, contacted Hub/network or dispatched verifier"
        )

    monkeypatch.setattr(commands, "resolve_token", forbidden)
    monkeypatch.setattr(HubClient, "of", forbidden)
    monkeypatch.setattr("hfcache.hashing.sha256_file", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)
    monkeypatch.setattr("socket.getaddrinfo", forbidden)
    monkeypatch.setattr(
        "hfcache.verification_protocol.VerificationClient.check_available", forbidden
    )
    monkeypatch.setattr("hfcache.verification_protocol.VerificationClient.execute", forbidden)
    monkeypatch.setattr("hfcache.verification_protocol.VerificationClient.reconcile", forbidden)


def test_refresh_http_captures_once_replays_original_and_new_key_recaptures(
    configured, monkeypatch
):
    server, layout, _, _ = configured
    tags(server, ["original"])
    no_external_capability(monkeypatch)
    writes = []
    original_write = CatalogWriter.write

    def tracked(self, record, **kwargs):
        writes.append(record.kind)
        return original_write(self, record, **kwargs)

    monkeypatch.setattr(CatalogWriter, "write", tracked)
    original_authority = archive_files(layout)
    saved = []

    async def action(client, app):
        first = await api.submit(client, ROUTE, BODY, "capture-original")
        completed = await api.result(client, first)
        payload = CatalogRefreshResult.model_validate(completed["data"])
        assert completed["command"] == "catalog refresh"
        assert completed["exit_code"] == 0
        assert payload.counts.snapshots_written == 1
        assert payload.counts.observations_written == 0
        saved.append((first, completed))
        snapshot = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
        assert snapshot is not None
        assert snapshot.tags == ("original",)
        original = layout.repository(MODEL).tag_snapshot.read_bytes()
        before_fp = load_config(server.archive_config).fingerprint()
        tags(server, ["changed"])
        assert load_config(server.archive_config).fingerprint() == before_fp
        repeated = await api.submit(
            client, ROUTE, BODY | {"selectors": [MODEL.selector] * 2}, "capture-original"
        )
        assert repeated["created"] is False
        assert repeated["operation"]["operation_id"] == first["operation"]["operation_id"]
        assert await api.result(client, repeated) == completed
        assert layout.repository(MODEL).tag_snapshot.read_bytes() == original
        conflict = await client.post(
            ROUTE,
            json=BODY | {"technical": True},
            headers=api.WRITER_HEADERS | {"Idempotency-Key": "capture-original"},
        )
        assert conflict.status_code == 409
        assert conflict.json()["code"] == "HFAPI012"
        newer = await api.submit(client, ROUTE, BODY, "capture-new")
        result = await api.result(client, newer)
        assert (
            result["data"]["curation_fingerprint"]
            == load_config(server.archive_config).curation_fingerprint()
        )
        latest = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
        assert latest is not None
        assert latest.tags == ("changed",)
        assert writes == ["repository_tag_snapshot", "repository_tag_snapshot"]
        assert {
            key: value
            for key, value in archive_files(layout).items()
            if not key.startswith("published/metadata/")
        } == original_authority

    asyncio.run(api.exercise(configured, action))

    async def restarted(client, app):
        first, completed = saved[0]
        assert await api.result(client, first) == completed
        assert len(writes) == 2

    asyncio.run(api.exercise(configured, restarted))


@pytest.mark.parametrize(
    "body",
    [
        {"tags": 1},
        {"technical": "false"},
        {"tags": False, "technical": False},
        {"selectors": None},
        {"selectors": "model:org/repo"},
        {"selectors": [None]},
        {"selectors": [MODEL.selector + "@" + "a" * 40]},
        {"selectors": ["/tmp/path"]},
        {"selectors": ["https://example.invalid/repo"]},
        {"selectors": [MODEL.selector] * 257},
        {"revision_scope": "latest"},
        {"candidate": "private-refusal-marker"},
        {"token_file": "/private-refusal-marker"},
        {"archive_root": "/private-refusal-marker"},
    ],
)
def test_refresh_body_is_strict_and_rejections_have_no_writes(configured, body):
    _, layout, _, _ = configured
    before = archive_files(layout)

    async def action(client, app):
        response = await client.post(
            ROUTE, json=body, headers=api.WRITER_HEADERS | {"Idempotency-Key": "invalid"}
        )
        assert response.status_code == 422
        assert "private-refusal-marker" not in response.text
        assert app.state.operations.list() == ()

    asyncio.run(api.exercise(configured, action))
    assert archive_files(layout) == before


def test_refresh_requires_writer_key_and_empty_query_before_admission(configured):
    async def action(client, app):
        denied = await client.post(ROUTE, content=b"{", headers=api.READER_HEADERS)
        assert denied.status_code == 403
        assert (await client.post(ROUTE, json=BODY, headers=api.WRITER_HEADERS)).status_code == 422
        assert (
            await client.post(
                ROUTE + "?scope=all",
                json=BODY,
                headers=api.WRITER_HEADERS | {"Idempotency-Key": "query"},
            )
        ).status_code == 422
        assert app.state.operations.list() == ()

    asyncio.run(api.exercise(configured, action))


def test_unknown_selector_resolves_under_lock_as_failed_without_metadata(configured, monkeypatch):
    _, layout, _, _ = configured
    no_external_capability(monkeypatch)
    before = archive_files(layout)

    async def action(client, app):
        accepted = await api.submit(
            client, ROUTE, {"selectors": ["model:unknown/repository"]}, "unknown"
        )
        result = await api.result(client, accepted)
        assert result["exit_code"] == 10
        assert result["errors"]

    asyncio.run(api.exercise(configured, action))
    assert archive_files(layout) == before


@pytest.mark.parametrize("operational_change", [False, True])
def test_queued_refresh_checks_policy_and_fresh_curation_after_wait(
    configured, monkeypatch, operational_change
):
    server, layout, _, _ = configured
    source = server.archive_config.read_text().replace(
        "lock_wait_seconds = 0", "lock_wait_seconds = 10"
    )
    server.archive_config.write_text(source)
    tags(server, ["before-wait"])
    no_external_capability(monkeypatch)

    async def action(client, app):
        with exclusive_lock(lock_path(), command="fixture external owner", wait_seconds=0):
            accepted = await api.submit(client, ROUTE, BODY, "queued")
            identifier = accepted["operation"]["operation_id"]
            deadline = time.monotonic() + 5
            while app.state.operations.get(identifier).state != "waiting_lock":
                assert time.monotonic() < deadline
                await asyncio.sleep(0.01)
            tags(server, ["after-wait"])
            if operational_change:
                server.archive_config.write_text(
                    server.archive_config.read_text().replace(
                        "maximum_revisions = 5", "maximum_revisions = 3"
                    )
                )
        result = await api.result(client, accepted)
        if operational_change:
            assert result["exit_code"] == 10
            assert result["errors"][0]["code"] == "HFAPI007"
            assert not layout.repository(MODEL).tag_snapshot.exists()
        else:
            assert result["exit_code"] == 0
            snapshot = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
            assert snapshot is not None
            assert snapshot.tags == ("after-wait",)
            assert result["data"]["curation_fingerprint"] == snapshot.curation_fingerprint

    asyncio.run(api.exercise(configured, action))


def test_lost_http_acknowledgement_keeps_one_owned_refresh_and_key_lookup(configured, monkeypatch):
    server, layout, _, lock = configured
    no_external_capability(monkeypatch)
    app = create_app(server, instance_lock_path=lock)
    writes = []
    entered, release = Event(), Event()
    original = CatalogWriter.write

    def counted(self, record, **kwargs):
        writes.append(record.kind)
        entered.set()
        assert release.wait(5)
        return original(self, record, **kwargs)

    monkeypatch.setattr(CatalogWriter, "write", counted)

    async def lost_ack(scope, receive, send):
        async def dropped(message):
            if message["type"] == "http.response.start" and message["status"] == 202:
                raise asyncio.CancelledError
            await send(message)

        await app(scope, receive, dropped)

    async def exercise():
        async with app.router.lifespan_context(app):
            try:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=lost_ack), base_url="http://testserver"
                ) as client:
                    with pytest.raises(asyncio.CancelledError):
                        await client.post(
                            ROUTE,
                            json=BODY,
                            headers=api.WRITER_HEADERS | {"Idempotency-Key": "lost-ack"},
                        )
                assert await asyncio.to_thread(entered.wait, 5)
                assert not layout.repository(MODEL).tag_snapshot.exists()
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://testserver"
                ) as client:
                    lookup = await client.get(
                        "/api/v1/operations/lookup",
                        headers=api.WRITER_HEADERS | {"Idempotency-Key": "lost-ack"},
                    )
                    assert lookup.status_code == 200
                    assert lookup.json()["envelope"]["data"]["operation"]["state"] == "running"
                    repeated = await api.submit(client, ROUTE, BODY, "lost-ack")
                    assert repeated["created"] is False
                    assert (
                        repeated["operation"]["operation_id"]
                        == lookup.json()["envelope"]["data"]["operation"]["operation_id"]
                    )
                    assert app.state.pool.inflight == 0
                    release.set()
                    assert (await api.result(client, repeated))["exit_code"] == 0
                    assert writes == ["repository_tag_snapshot"]
                    assert layout.repository(MODEL).tag_snapshot.is_file()
            finally:
                release.set()

    asyncio.run(exercise())


def test_restart_preserves_abandoned_refresh_without_execution_or_replay(configured, monkeypatch):
    server, layout, _, _ = configured
    no_external_capability(monkeypatch)
    body = CatalogRefreshSubmission.model_validate(BODY).canonical_body()
    with OperationStore(server.state_directory) as store:
        receipt = store.admit(
            Principal(CredentialClass.REST_WRITER),
            "abandoned",
            ROUTE,
            body,
            InstalledPolicy.open(server).snapshot,
        ).receipt
    before = archive_files(layout)

    async def action(client, app):
        assert app.state.operations.get(receipt.operation_id).state == "interrupted"
        repeated = await api.submit(client, ROUTE, BODY, "abandoned")
        assert repeated["created"] is False
        assert repeated["operation"]["operation_id"] == receipt.operation_id
        response = await client.get(repeated["links"]["result"], headers=api.READER_HEADERS)
        assert response.status_code == 409
        assert response.json()["code"] == "HFAPI015"

    asyncio.run(api.exercise(configured, action))
    assert archive_files(layout) == before


def test_default_refresh_and_technical_only_keep_unpublished_skips_explicit(
    configured, monkeypatch
):
    no_external_capability(monkeypatch)

    async def action(client, app):
        first = await api.submit(client, ROUTE, {}, "default")
        result = await api.result(client, first)
        assert result["exit_code"] == 0
        assert result["data"]["counts"]["snapshots_written"] == 2
        assert result["data"]["counts"]["technical_skipped"] == 2
        before = archive_files(configured[1])
        second = await api.submit(client, ROUTE, {"tags": False}, "technical-only")
        result = await api.result(client, second)
        assert result["data"]["counts"]["snapshots_written"] == 0
        assert result["data"]["counts"]["technical_skipped"] == 2
        assert archive_files(configured[1]) == before

    asyncio.run(api.exercise(configured, action))


def test_technical_refresh_observes_exact_published_headers_without_other_archive_writes(
    configured, monkeypatch
):
    server, layout, hub, _ = configured
    hub.revisions[SHA_A] = {"model.gguf": gguf()[0]}
    outcome = CommandServices(
        load_config(server.archive_config), ExecutionContext.create()
    ).synchronize(SelectionRequest((MODEL.selector,)))
    assert outcome.exit_code == 0
    original_snapshot = layout.repository(MODEL).tag_snapshot.read_bytes()
    authority = {
        key: value
        for key, value in archive_files(layout).items()
        if not key.startswith("published/metadata/")
    }
    downloads = tuple(hub.downloads)
    no_external_capability(monkeypatch)

    async def action(client, app):
        accepted = await api.submit(
            client, ROUTE, {"selectors": [MODEL.selector], "tags": False}, "headers"
        )
        result = await api.result(client, accepted)
        assert result["exit_code"] == 0
        assert result["data"]["counts"]["observations_written"] == 1
        assert result["data"]["repositories"][0]["publications"][0]["commit_sha"] == SHA_A
        assert (
            result["data"]["repositories"][0]["publications"][0]["observation_status"] == "complete"
        )

    asyncio.run(api.exercise(configured, action))
    assert layout.repository(MODEL).tag_snapshot.read_bytes() == original_snapshot
    assert tuple(hub.downloads) == downloads
    assert {
        key: value
        for key, value in archive_files(layout).items()
        if not key.startswith("published/metadata/")
    } == authority
