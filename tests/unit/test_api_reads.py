"""Read projections, cursor stability, streaming and metadata isolation (API-006)."""

import asyncio
import json
import threading
from datetime import timedelta

import httpx
import pytest

from hfcache.api.app import create_app
from hfcache.api.lifecycle import MetadataPool
from hfcache.config import load_config
from hfcache.errors import SafetyError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, RunId
from hfcache.logging import current_correlation, reset
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.context import ServiceResult
from hfcache.services.queries import ALL_REPOSITORIES, LocalQueries, PublicationQuery
from tests.fixtures import examples

WRITER = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
READER = "reader_9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVU"
HEADERS = {"authorization": f"Bearer {READER}"}


@pytest.fixture(autouse=True)
def isolate_logging():
    reset()
    yield
    reset()


@pytest.fixture
def configured(tmp_path):
    archive = tmp_path / "archive"
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{archive}"\narchive_id="{examples.ARCHIVE_ID}"\n'
    )
    credentials = {}
    for name, token in (("writer", WRITER), ("reader", READER)):
        path = tmp_path / name
        path.write_text(token)
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    data = {
        "schema_version": 1,
        "archive_config": str(policy),
        "state_directory": str(tmp_path / "api-state"),
        "credentials": credentials,
        "listener": {"allowed_hosts": ["testserver"]},
    }
    return data, policy, archive, tmp_path / "daemon.lock"


async def client_context(app, action):
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver", headers=HEADERS
        ) as client,
    ):
        return await action(client)


def write_model(path, model):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.to_json())


def publish(policy):
    queries = LocalQueries(load_config(policy))
    request = PublicationQuery(
        RepositoryIdentity.of("model", examples.REPOSITORY_ID),
        CommitSha(examples.SHA),
        PublicationId(examples.PUBLICATION),
    )
    repository = queries.layout.repository(request.identity)
    repository.instance(request.commit_sha, request.publication_id).mkdir(parents=True)
    write_model(
        repository.manifest(request.commit_sha, request.publication_id), examples.manifest()
    )
    write_model(repository.current_ref, examples.reference())
    write_model(repository.revision_ref(request.commit_sha), examples.reference())
    return queries


def test_factory_has_no_io_and_lifespan_never_initializes_archive(configured):
    data, _, archive, lock = configured
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)
    assert not archive.exists()
    assert not lock.exists()

    async def read(client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["envelope"]["data"]["archive"]["state"] == "unusable"
        assert not archive.exists()

    asyncio.run(client_context(app, read))
    assert lock.is_file()
    assert not archive.exists()


def test_exact_namespace_name_refs_manifests_and_report_run_identity(configured):
    data, policy, _, lock = configured
    queries = publish(policy)
    report = examples.run_report()
    write_model(queries.layout.run_report(report.started_at, RunId(report.run_id)), report)
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)
    stem = "/api/v1/repositories/model/" + examples.REPOSITORY_ID

    async def read(client):
        reference = await client.get(stem + "/references/current")
        assert reference.status_code == 200
        payload = reference.json()
        assert payload["archive_id"] == examples.ARCHIVE_ID
        assert payload["config_fingerprint"] == load_config(policy).fingerprint()
        assert payload["envelope"]["data"]["locator_base"] == "published/"
        assert payload["envelope"]["data"]["reference"] == examples.reference().model_dump(
            mode="json"
        )
        manifest = await client.get(stem + f"/manifests/{examples.SHA}/{examples.PUBLICATION}")
        assert manifest.status_code == 200
        assert manifest.json()["envelope"]["data"] == {
            "tree_base": "archive-root/",
            "manifest": examples.manifest().model_dump(mode="json"),
        }
        found = await client.get("/api/v1/runs/" + report.run_id)
        assert found.status_code == 200
        assert found.json()["envelope"]["run_id"] == report.run_id
        assert found.json()["envelope"]["data"]["report"] == report.model_dump(mode="json")
        runs = await client.get("/api/v1/runs")
        assert runs.json()["envelope"]["data"]["runs"] == [report.run_id]
        revisions = await client.get("/api/v1/repositories/revisions")
        assert (
            revisions.json()["envelope"]["data"]["revisions"][0]["publication_id"]
            == examples.PUBLICATION
        )
        inventory = await client.get("/api/v1/repositories")
        assert inventory.status_code == 200
        assert inventory.json()["envelope"]["data"]["repositories"][0]["managed"] is False
        estimate = await client.get("/api/v1/verification/estimate")
        assert estimate.status_code == 200
        inspected = await client.get("/api/v1/archive/inspection")
        assert inspected.status_code == 200
        assert inspected.json()["envelope"]["exit_code"] == 20

    asyncio.run(client_context(app, read))


def test_status_pages_reconstruct_configuration_order_and_refuse_stale_cursor(configured):
    data, policy, _, lock = configured
    with policy.open("a") as stream:
        for name in ("zeta/first", "alpha/second", "middle/third"):
            stream.write(f'\n[[repositories]]\ntype="model"\nid="{name}"\n')
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        first = (await client.get("/api/v1/status?limit=1")).json()
        second = (
            await client.get(
                "/api/v1/status", params={"limit": "1", "cursor": first["next_cursor"]}
            )
        ).json()
        third = (
            await client.get(
                "/api/v1/status", params={"limit": "1", "cursor": second["next_cursor"]}
            )
        ).json()
        rows = [
            page["envelope"]["data"]["repositories"][0]["repository_id"]
            for page in (first, second, third)
        ]
        assert rows == ["zeta/first", "alpha/second", "middle/third"]
        assert third["next_cursor"] is None
        unrelated = await client.get(
            "/api/v1/repositories", params={"cursor": first["next_cursor"]}
        )
        assert unrelated.status_code == 409
        policy.write_text(policy.read_text().replace("zeta/first", "zeta/changed"))
        stale = await client.get("/api/v1/status", params={"cursor": first["next_cursor"]})
        assert stale.status_code == 409

    asyncio.run(client_context(app, read))


def test_report_cursor_detects_new_publication_without_policy_change(configured):
    data, policy, _, lock = configured
    queries = LocalQueries(load_config(policy))
    one = examples.run_report()
    two = one.model_copy(
        update={"run_id": "b" * 32, "started_at": one.started_at + timedelta(seconds=1)}
    )
    write_model(queries.layout.run_report(one.started_at, RunId(one.run_id)), one)
    write_model(queries.layout.run_report(two.started_at, RunId(two.run_id)), two)
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        first = (await client.get("/api/v1/runs?limit=1")).json()
        assert first["envelope"]["data"]["runs"] == [two.run_id]
        three = one.model_copy(
            update={"run_id": "c" * 32, "started_at": one.started_at + timedelta(seconds=2)}
        )
        write_model(queries.layout.run_report(three.started_at, RunId(three.run_id)), three)
        assert (
            await client.get("/api/v1/runs", params={"cursor": first["next_cursor"]})
        ).status_code == 409

    asyncio.run(client_context(app, read))


def test_version_health_diagnose_later_invalid_policy_and_capabilities_show_role(configured):
    data, policy, _, lock = configured
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)

    async def read(client):
        policy.write_text("bad = [")
        assert (await client.get("/api/v1/version")).status_code == 200
        health = await client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["envelope"]["data"]["policy_valid"] is False
        assert (await client.get("/api/v1/status")).status_code == 503
        reader = (await client.get("/api/v1/capabilities")).json()["envelope"]["data"]
        assert reader["capabilities"] == ["read"]
        writer = (
            await client.get("/api/v1/capabilities", headers={"authorization": f"Bearer {WRITER}"})
        ).json()["envelope"]["data"]
        assert writer["capabilities"] == ["read", "write"]
        assert writer["operations"] is False

    asyncio.run(client_context(app, read))


def test_large_reports_stream_in_bounded_chunks_and_sanitize_registered_secrets(configured):
    data, policy, _, lock = configured
    queries = LocalQueries(load_config(policy))
    report = examples.run_report()
    payload = report.model_dump(mode="json") | {
        "outcome": "failed",
        "exit_code": 30,
        "errors": ["x" * 1048576 + WRITER],
    }
    path = queries.layout.run_report(report.started_at, RunId(report.run_id))
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload))
    app = create_app(validate_server_config_mapping(data), instance_lock_path=lock)
    sizes = []

    async def counted(scope, receive, send):
        async def monitor(message):
            if message["type"] == "http.response.body":
                sizes.append(len(message.get("body", b"")))
            await send(message)

        await app(scope, receive, monitor)

    async def read(_):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=counted),
            base_url="http://testserver",
            headers=HEADERS,
        ) as client:
            response = await client.get("/api/v1/runs/" + report.run_id)
        assert response.status_code == 200
        assert WRITER not in response.text
        assert response.json()["envelope"]["data"]["report"]["exit_code"] == 30
        assert max(sizes) <= 8192
        assert len(sizes) > 100

    asyncio.run(client_context(app, read))


def test_metadata_saturation_keeps_version_responsive_and_retains_worker_context(configured):
    data, _, _, lock = configured
    data["limits"] = {"metadata_workers": 1, "metadata_queue": 1}
    entered = threading.Event()
    release = threading.Event()
    correlations = []

    class BlockingQueries(LocalQueries):
        def archive_status(self, request=ALL_REPOSITORIES):
            correlations.append(current_correlation())
            entered.set()
            if not release.wait(5):
                msg = "test worker release timed out"
                raise RuntimeError(msg)
            return ServiceResult("status", {"repositories": []})

    app = create_app(
        validate_server_config_mapping(data), query_factory=BlockingQueries, instance_lock_path=lock
    )

    async def read(client):
        first = asyncio.create_task(client.get("/api/v1/status"))
        while not entered.is_set():
            await asyncio.sleep(0.001)
        second = asyncio.create_task(client.get("/api/v1/status"))
        while app.state.pool.inflight != 2:
            await asyncio.sleep(0.001)
        try:
            assert (await asyncio.wait_for(client.get("/api/v1/version"), 1)).status_code == 200
            assert (await client.get("/api/v1/status")).status_code == 503
            assert app.state.pool.inflight == 2
        finally:
            release.set()
        responses = await asyncio.gather(first, second)
        assert all(response.status_code == 200 for response in responses)
        assert {value.request_id for value in correlations} == {
            response.json()["request_id"] for response in responses
        }
        assert app.state.pool.inflight == 0

    asyncio.run(client_context(app, read))
    assert app.state.pool.closed is True


def test_unexpected_worker_exception_is_sanitized_and_capacity_restores(configured):
    data, _, _, lock = configured

    class BrokenQueries(LocalQueries):
        def archive_status(self, request=ALL_REPOSITORIES):
            msg = "unregistered-secret-never-echo-this"
            raise RuntimeError(msg)

    app = create_app(
        validate_server_config_mapping(data), query_factory=BrokenQueries, instance_lock_path=lock
    )

    async def read(client):
        response = await client.get("/api/v1/status")
        assert response.status_code == 500
        assert response.json()["code"] == "HFAPI008"
        assert "unregistered-secret" not in response.text
        assert app.state.pool.inflight == 0

    asyncio.run(client_context(app, read))


def test_completed_worker_releases_capacity_before_delayed_loop_callback():
    async def exercise():
        pool = MetadataPool(workers=1, pending=1)
        lease = pool.submit(lambda: None)
        # Do not yield this loop: the concurrent worker completes but its
        # call_soon_threadsafe completion callback cannot have run yet.
        lease.worker.result(timeout=5)
        assert lease.worker_done is False
        lease.finish_request()
        assert pool.inflight == 0
        await asyncio.sleep(0)
        assert pool.inflight == 0
        await pool.close()

    asyncio.run(exercise())


def test_cancelled_observer_retains_capacity_until_original_worker_finishes():
    async def exercise():
        pool = MetadataPool(workers=1, pending=0)
        entered = threading.Event()
        release = threading.Event()

        def work():
            entered.set()
            assert release.wait(5)

        lease = pool.submit(work)
        try:
            assert await asyncio.to_thread(entered.wait, 5)
            lease.future.cancel()
            with pytest.raises(asyncio.CancelledError):
                await lease.future
            lease.finish_request()
            assert not lease.worker.done()
            assert pool.inflight == 1
            with pytest.raises(SafetyError):
                pool.submit(lambda: None)
            release.set()
            async with asyncio.timeout(5):
                while pool.inflight:
                    await asyncio.sleep(0)
            assert lease.worker.done()
            lease.finish_request()
            assert pool.inflight == 0
        finally:
            release.set()
            await pool.close()

    asyncio.run(exercise())


def test_second_app_refuses_same_instance_inode_but_can_restart_after_release(configured):
    data, _, _, lock = configured
    config = validate_server_config_mapping(data)
    first = create_app(config, instance_lock_path=lock)
    second = create_app(config, instance_lock_path=lock)

    async def read(client):
        inode = lock.stat().st_ino
        with pytest.raises(SafetyError):
            async with second.router.lifespan_context(second):
                pytest.fail("second daemon acquired same lock")
        assert lock.stat().st_ino == inode
        assert (await client.get("/api/v1/version")).status_code == 200

    asyncio.run(client_context(first, read))
    inode = lock.stat().st_ino

    async def healthy(client):
        assert (await client.get("/api/v1/version")).status_code == 200

    asyncio.run(client_context(second, healthy))
    assert lock.stat().st_ino == inode
