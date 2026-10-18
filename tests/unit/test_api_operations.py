"""Operation observations remain authenticated, bounded and independent of execution."""

import asyncio
import json
import threading

import httpx
import pytest

from hfcache.api.app import create_app
from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.operations import OperationLimits, OperationStore
from hfcache.errors import ConfigurationError, Problem, SafetyError
from hfcache.logging import reset
from hfcache.server_config import InstalledPolicy, validate_server_config_mapping
from hfcache.services.context import ExecutionContext, ServiceResult
from tests.fixtures import examples

WRITER = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
READER = "reader_9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVU"
WRITER_HEADERS = {"Authorization": f"Bearer {WRITER}"}
READER_HEADERS = {"Authorization": f"Bearer {READER}"}


@pytest.fixture(autouse=True)
def isolate_logging():
    reset()
    yield
    reset()


@pytest.fixture
def configured(tmp_path):
    archive_config = tmp_path / "archive.toml"
    archive_config.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n',
        encoding="utf-8",
    )
    credentials = {}
    for name, token in (("writer", WRITER), ("reader", READER)):
        path = tmp_path / name
        path.write_text(token, encoding="ascii")
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(archive_config),
            "state_directory": str(tmp_path / "state"),
            "credentials": credentials,
            "listener": {"allowed_hosts": ["testserver"]},
            "limits": {"operation_max_events": 2, "max_page_size": 2},
        }
    )
    store = OperationStore(server.state_directory, limits=OperationLimits(max_events=2))
    yield server, InstalledPolicy.open(server), store, tmp_path / "daemon.lock"
    store.close()


async def requests(app, action):
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client,
    ):
        await action(client)


def admitted(store, policy, *, key="known-submission", principal=CredentialClass.REST_WRITER):
    return store.admit(
        Principal(principal), key, "/api/v1/syncs", {"selectors": []}, policy.snapshot
    ).receipt


def test_reader_can_observe_writer_history_but_lookup_is_class_scoped(configured):
    server, policy, store, lock = configured
    writer = admitted(store, policy)
    reader = admitted(store, policy, principal=CredentialClass.REST_READER)
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        listed = await client.get("/api/v1/operations", headers=READER_HEADERS)
        assert listed.status_code == 200
        rows = listed.json()["envelope"]["data"]["operations"]
        assert {row["operation_id"] for row in rows} == {writer.operation_id, reader.operation_id}
        assert listed.json()["next_cursor"] is None
        shown = await client.get(
            f"/api/v1/operations/{writer.operation_id}", headers=READER_HEADERS
        )
        assert shown.status_code == 200
        data = shown.json()["envelope"]["data"]["operation"]
        assert data["principal"] == "rest-writer"
        assert data["result_recorded"] is False
        for headers, expected in ((WRITER_HEADERS, writer), (READER_HEADERS, reader)):
            looked = await client.get(
                "/api/v1/operations/lookup",
                headers=headers | {"Idempotency-Key": "known-submission"},
            )
            assert looked.status_code == 200
            assert (
                looked.json()["envelope"]["data"]["operation"]["operation_id"]
                == expected.operation_id
            )
        assert writer.key_digest not in shown.text
        assert writer.request_digest not in shown.text
        assert "known-submission" not in shown.text

    asyncio.run(requests(app, read))


def test_exact_stored_result_preserves_domain_envelope_and_failed_exit(configured):
    server, policy, store, lock = configured
    receipt = admitted(store, policy)
    store.transition(receipt.operation_id, "running")
    # Command failure is a successful HTTP retrieval with its exact original
    # domain exit, error details, timestamps and run identity.
    envelope = ServiceResult(
        "sync",
        {"details": "failed without archive action"},
        errors=(Problem("HFHUB004", "Hub unavailable"),),
        exit_code=30,
    ).envelope(ExecutionContext.create())
    store.transition(receipt.operation_id, "failed", envelope=envelope)
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        policy.path.write_text("invalid = [", encoding="utf-8")
        found = await client.get(
            f"/api/v1/operations/{receipt.operation_id}/result", headers=READER_HEADERS
        )
        assert found.status_code == 200
        assert found.json()["envelope"] == envelope.to_payload()
        assert found.json()["archive_id"] == receipt.archive_id
        assert found.json()["config_fingerprint"] == receipt.config_fingerprint
        assert found.json()["request_id"] != envelope.run_id
        shown = await client.get(
            f"/api/v1/operations/{receipt.operation_id}", headers=READER_HEADERS
        )
        assert shown.status_code == 200
        assert shown.json()["envelope"]["data"]["operation"]["result_recorded"] is True

    asyncio.run(requests(app, read))


def test_event_pages_have_explicit_dropped_prefix_and_sequence_cursor(configured):
    server, policy, store, lock = configured
    receipt = admitted(store, policy)
    for number in range(3):
        store.append_event(receipt.operation_id, "progress", f"step {number}")
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        first = await client.get(
            f"/api/v1/operations/{receipt.operation_id}/events?limit=1", headers=READER_HEADERS
        )
        assert first.status_code == 200
        page = first.json()["envelope"]["data"]
        assert page["truncated"] is True
        assert page["oldest_sequence"] == 2
        assert page["next_cursor"] == 2
        assert [event["sequence"] for event in page["events"]] == [2]
        second = await client.get(
            f"/api/v1/operations/{receipt.operation_id}/events?after=2&limit=1",
            headers=READER_HEADERS,
        )
        page = second.json()["envelope"]["data"]
        assert page["truncated"] is False
        assert page["next_cursor"] == 3
        assert [event["sequence"] for event in page["events"]] == [3]

    asyncio.run(requests(app, read))


@pytest.mark.parametrize("suffix", ["", "/result", "/events"])
def test_every_operation_surface_authenticates_and_never_executes(configured, suffix):
    server, policy, store, lock = configured
    receipt = admitted(store, policy)
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        # Startup classifies abandoned queued work; observations themselves do
        # not mutate history or invoke a command.
        before = {
            path.name: path.read_bytes()
            for path in server.state_directory.iterdir()
            if path.is_file()
        }
        path = f"/api/v1/operations/{receipt.operation_id}{suffix}"
        assert (await client.get(path)).status_code == 401
        response = await client.get(path, headers=READER_HEADERS)
        assert response.status_code == (409 if suffix == "/result" else 200)
        if suffix == "/result":
            assert response.json()["code"] == "HFAPI015"
            assert response.json()["exit_code"] == 20
        assert (await client.post("/api/v1/syncs", headers=WRITER_HEADERS)).status_code == 404
        assert {
            path.name: path.read_bytes()
            for path in server.state_directory.iterdir()
            if path.is_file()
        } == before

    asyncio.run(requests(app, read))
    assert not policy.root.exists()


def test_missing_lookup_is_uncertainty_not_proven_nonexecution(configured):
    server, _, store, lock = configured
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        response = await client.get(
            "/api/v1/operations/lookup",
            headers=READER_HEADERS | {"Idempotency-Key": "lost-acknowledgement"},
        )
        assert response.status_code == 404
        assert response.json()["code"] == "HFAPI013"
        assert response.json()["exit_code"] == 20
        assert "unknown" in response.json()["message"]
        assert "lost-acknowledgement" not in response.text
        assert (
            await client.get("/api/v1/operations/lookup", headers=READER_HEADERS)
        ).status_code == 422
        duplicate = await client.get(
            "/api/v1/operations/lookup",
            headers=[
                *READER_HEADERS.items(),
                ("Idempotency-Key", "one"),
                ("Idempotency-Key", "two"),
            ],
        )
        assert duplicate.status_code == 422
        assert (
            await client.get("/api/v1/operations/not-an-id", headers=READER_HEADERS)
        ).status_code == 422

    asyncio.run(requests(app, read))


def test_unknown_history_blocks_scans_but_keeps_healthy_exact_observation(configured):
    server, policy, store, lock = configured
    receipt = admitted(store, policy)
    unknown = server.state_directory / "future.json"
    unknown.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")
    unknown.chmod(0o600)
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        assert (await client.get("/api/v1/version", headers=READER_HEADERS)).status_code == 200
        assert (
            await client.get(f"/api/v1/operations/{receipt.operation_id}", headers=READER_HEADERS)
        ).status_code == 200
        response = await client.get("/api/v1/operations", headers=READER_HEADERS)
        assert response.status_code == 503
        assert response.json()["code"] == "HFAPI014"

    asyncio.run(requests(app, read))
    assert json.loads(unknown.read_text()) == {"schema_version": 999}


@pytest.mark.parametrize(
    "query",
    [
        "after=-1",
        "after=1.0",
        "after=1&after=2",
        "limit=0",
        "limit=3",
        "token=unregistered-opaque-secret",
    ],
)
def test_event_query_validation_is_bounded_and_secret_free(configured, query):
    server, policy, store, lock = configured
    receipt = admitted(store, policy)
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        response = await client.get(
            f"/api/v1/operations/{receipt.operation_id}/events?{query}", headers=READER_HEADERS
        )
        assert response.status_code == 422
        assert "unregistered-opaque-secret" not in response.text

    asyncio.run(requests(app, read))


@pytest.mark.parametrize("suffix", ["", "/published/api-state"])
def test_lifespan_refuses_archive_control_state_overlap_before_creation(configured, suffix):
    server, policy, _, lock = configured
    state = policy.root if not suffix else policy.root / suffix.lstrip("/")
    revised = validate_server_config_mapping(
        server.model_dump(mode="json") | {"state_directory": str(state)}
    )
    app = create_app(revised, instance_lock_path=lock)

    async def start():
        with pytest.raises(ConfigurationError, match="must not overlap"):
            async with app.router.lifespan_context(app):
                pytest.fail("overlapping operation state was created")

    asyncio.run(start())
    assert not policy.root.exists()


def test_operation_collection_pages_keep_identity_during_status_updates_and_refuse_new_members(
    configured,
):
    server, policy, store, lock = configured
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        receipts = [admitted(store, policy, key=f"submission-{number}") for number in range(3)]
        first = (await client.get("/api/v1/operations", headers=READER_HEADERS)).json()
        assert len(first["envelope"]["data"]["operations"]) == 2
        assert first["next_cursor"] is not None
        store.transition(receipts[0].operation_id, "running")
        second = await client.get(
            "/api/v1/operations", params={"cursor": first["next_cursor"]}, headers=READER_HEADERS
        )
        assert second.status_code == 200
        pages = (
            first["envelope"]["data"]["operations"]
            + second.json()["envelope"]["data"]["operations"]
        )
        assert {row["operation_id"] for row in pages} == {
            receipt.operation_id for receipt in receipts
        }
        admitted(store, policy, key="new-member")
        stale = await client.get(
            "/api/v1/operations", params={"cursor": first["next_cursor"]}, headers=READER_HEADERS
        )
        assert stale.status_code == 409

    asyncio.run(requests(app, read))


def test_unreachable_old_verifier_preserves_receipt_and_blocks_admission_but_serves_reads(
    configured,
):
    server, policy, store, lock = configured
    receipt = store.admit(
        Principal(CredentialClass.REST_WRITER),
        "old-verification",
        "/api/v1/verifications",
        {"mode": "full"},
        policy.snapshot,
    ).receipt
    app = create_app(server, operation_store=store, instance_lock_path=lock)

    async def read(client):
        assert store.get(receipt.operation_id).state == "queued"
        assert (await client.get("/api/v1/version", headers=READER_HEADERS)).status_code == 200
        with pytest.raises(SafetyError):
            app.state.runner.submit(
                Principal(CredentialClass.REST_WRITER),
                "new-work",
                "/api/v1/plans",
                {},
                command="plan",
                execute=lambda *_: pytest.fail("unsafe admission"),
                wait_seconds=1,
                requires_lock=False,
            )
        assert len(store.list()) == 1

    asyncio.run(requests(app, read))


@pytest.mark.parametrize("cancel_shutdown", [False, True])
def test_metadata_remains_responsive_and_lifespan_joins_active_domain_work(
    configured, cancel_shutdown
):
    server, _, store, lock = configured
    app = create_app(server, operation_store=store, instance_lock_path=lock)
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()

    def execute(snapshot, context):
        entered.set()
        assert release.wait(5)
        finished.set()
        return ServiceResult("plan", {"ready": True})

    async def exercise():
        lifespan = app.router.lifespan_context(app)
        await lifespan.__aenter__()
        closing = None
        try:
            receipt = app.state.runner.submit(
                Principal(CredentialClass.REST_WRITER),
                "active-work",
                "/api/v1/plans",
                {},
                command="plan",
                execute=execute,
                wait_seconds=10,
                requires_lock=False,
            ).receipt
            assert await asyncio.to_thread(entered.wait, 5)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                response = await client.get("/api/v1/version", headers=READER_HEADERS)
                assert response.status_code == 200
                assert not finished.is_set()
            closing = asyncio.create_task(lifespan.__aexit__(None, None, None))
            await asyncio.sleep(0)
            assert not closing.done()
            assert not finished.is_set()
            if cancel_shutdown:
                closing.cancel()
                await asyncio.sleep(0)
                closing.cancel()
                await asyncio.sleep(0)
                assert not closing.done()
            release.set()
            await asyncio.gather(closing, return_exceptions=True)
            assert finished.is_set()
            assert (
                json.loads(store.root.joinpath(receipt.operation_id + ".json").read_bytes())[
                    "state"
                ]
                == "succeeded"
            )
        finally:
            release.set()
            if closing is None:
                await lifespan.__aexit__(None, None, None)
            else:
                await asyncio.gather(closing, return_exceptions=True)

    asyncio.run(exercise())
