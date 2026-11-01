"""WEB016: public API/runner to real Unix worker and guarded business services.

Only the external Hub and local mount/lock fixture seams are deterministic.
Admission, publication, private IPC, hashing, durable reports and reads are real.
"""

import asyncio
import socket
import threading

import httpx
import pytest

from hfcache import verification_executor
from hfcache.api.app import create_app
from hfcache.api.operations import OperationStore
from hfcache.paths import RepositoryLayout
from hfcache.preflight import hub_checks
from hfcache.publication import read_reference
from hfcache.server_config import InstalledPolicy
from hfcache.verification_executor import VerificationWorker
from tests.unit.test_api_commands import configured as configured  # noqa: PLC0414 - shared fixture
from tests.unit.test_api_commands import result, submit
from tests.unit.test_api_operations import READER_HEADERS, WRITER_HEADERS
from tests.unit.test_synchronize import CONTENT, MODEL, SHA_A
from tests.unit.test_verification_executor import listening


@pytest.fixture
def real_services(configured, monkeypatch):
    # The inherited fixture supplies only owned local storage/Hub data. Restore
    # real business preflight and substitute its external DNS/TLS boundaries.
    def verifies(_host, *, port):
        assert port == 443
        return "TLSv1.3"

    monkeypatch.setattr("hfcache.services.commands.hub_checks", hub_checks)
    monkeypatch.setattr("hfcache.preflight.resolve_host", lambda _host: ("192.0.2.1",))
    monkeypatch.setattr("hfcache.preflight.verify_tls", verifies)
    return configured


async def read_report(client, envelope):
    run_id = envelope["run_id"]
    response = await client.get("/api/v1/runs/" + run_id, headers=READER_HEADERS)
    assert response.status_code == 200, response.text
    wrapper = response.json()
    assert wrapper["envelope"]["command"] == "runs read"
    assert wrapper["envelope"]["run_id"] == run_id
    report = wrapper["envelope"]["data"]["report"]
    assert report["run_id"] == run_id
    assert report["archive_id"] == wrapper["archive_id"]
    assert report["config_fingerprint"] == wrapper["config_fingerprint"]
    assert report["exit_code"] == envelope["exit_code"]
    return report


def test_real_api_sync_then_all_unix_verification_modes_and_integrity_report(
    real_services, tmp_path
):
    server, layout, hub, instance_lock = real_services
    policy = InstalledPolicy.open(server)

    async def workflow(verifier, worker_store):
        app = create_app(server, instance_lock_path=instance_lock, verification_executor=verifier)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            admitted = await submit(
                client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, "web016-original-sync"
            )
            synced = await result(client, admitted)
            assert synced["exit_code"] == 0
            assert synced["run_id"] != admitted["operation"]["operation_id"]
            assert synced["data"]["repositories"][0]["status"] == "completed_with_warnings"
            assert synced["data"]["repositories"][0]["warnings"] == ["HFWRN011"]
            reference = read_reference(layout, RepositoryLayout(layout, MODEL).current_ref)
            tree = layout.published / reference.tree
            assert (tree / "weights.bin").read_bytes() == CONTENT["weights.bin"]
            assert len(hub.downloads) == 1
            assert (await read_report(client, synced))["repositories"][0]["publication_id"] == (
                reference.publication_id
            )

            verification_ids = []
            for mode, extra in (
                ("new", {"run_id": synced["run_id"]}),
                ("full", {}),
                ("revision", {"revision": f"{MODEL.selector}@{SHA_A}"}),
            ):
                accepted = await submit(
                    client,
                    "/api/v1/verifications",
                    {"mode": mode, **extra},
                    "web016-original-verify-" + mode,
                )
                identifier = accepted["operation"]["operation_id"]
                verification_ids.append(identifier)
                verified = await result(client, accepted)
                assert verified["exit_code"] == 0
                assert verified["data"]["mode"] == mode
                assert verified["data"]["verification_outcome"] == "clean"
                assert verified["data"]["scope"]["unique_objects_read"] > 0
                assert verified == worker_store.result(identifier).model_dump(mode="json")
                assert worker_store.get(identifier).domain_run_id == verified["run_id"]
                assert (await read_report(client, verified))["findings"] == []
                lookup = await client.get(
                    "/api/v1/operations/lookup",
                    headers=WRITER_HEADERS | {"Idempotency-Key": "web016-original-verify-" + mode},
                )
                assert lookup.status_code == 200
                assert lookup.json()["envelope"]["data"]["operation"]["operation_id"] == identifier

            downloads = tuple(hub.downloads)
            (tree / "weights.bin").write_bytes(b"damaged owned fixture publication")
            failed = await submit(
                client, "/api/v1/verifications", {"mode": "full"}, "web016-original-integrity"
            )
            integrity = await result(client, failed)
            assert integrity["exit_code"] == 40
            assert integrity["outcome"] == "failed"
            assert integrity["data"]["verification_outcome"] == "failed"
            assert integrity["data"]["findings"]
            assert integrity == worker_store.result(failed["operation"]["operation_id"]).model_dump(
                mode="json"
            )
            report = await read_report(client, integrity)
            assert report["findings"] == integrity["data"]["findings"]
            assert (tree / "weights.bin").read_bytes() == b"damaged owned fixture publication"
            assert tuple(hub.downloads) == downloads
            assert len(worker_store.list()) == len(verification_ids) + 1
            inventory = await client.get("/api/v1/runs?limit=25", headers=READER_HEADERS)
            assert inventory.status_code == 200
            assert set(inventory.json()["envelope"]["data"]["runs"]) == {
                synced["run_id"],
                *(row.domain_run_id for row in worker_store.list()),
            }

    with (
        OperationStore(tmp_path / "private-worker-state") as worker_store,
        listening(tmp_path, VerificationWorker(policy, worker_store)) as (verifier, _),
    ):
        asyncio.run(workflow(verifier, worker_store))


def test_lost_real_unix_submit_ack_reconciles_original_worker_without_second_effect(
    real_services, tmp_path, monkeypatch
):
    """Drop only the transport reply, after the real worker admitted its original scope."""
    server, layout, _, instance_lock = real_services
    policy = InstalledPolicy.open(server)
    real_send = verification_executor.send_frame
    dropped = threading.Event()
    lost_ids = []

    def lose_one_ack(connection, reply, maximum):
        if reply.receipt is not None and not dropped.is_set():
            lost_ids.append(reply.receipt.operation_id)
            dropped.set()
            connection.shutdown(socket.SHUT_RDWR)
            return
        real_send(connection, reply, maximum)

    monkeypatch.setattr(verification_executor, "send_frame", lose_one_ack)

    async def workflow(verifier, worker_store):
        app = create_app(server, instance_lock_path=instance_lock, verification_executor=verifier)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            synced = await result(
                client,
                await submit(
                    client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, "web016-fixture-sync"
                ),
            )
            assert synced["exit_code"] == 0
            before_reports = set(layout.runs.iterdir())
            accepted = await submit(
                client, "/api/v1/verifications", {"mode": "full"}, "web016-lost-private-ack"
            )
            original = accepted["operation"]["operation_id"]
            completed = await result(client, accepted)
            assert dropped.is_set()
            assert lost_ids == [original]
            assert completed["exit_code"] == 0
            assert completed["data"]["verification_outcome"] == "clean"
            assert [row.operation_id for row in worker_store.list()] == [original]
            assert worker_store.result(original).model_dump(mode="json") == completed
            assert len(set(layout.runs.iterdir()) - before_reports) == 1
            lookup = await client.get(
                "/api/v1/operations/lookup",
                headers=WRITER_HEADERS | {"Idempotency-Key": "web016-lost-private-ack"},
            )
            assert lookup.status_code == 200
            assert lookup.json()["envelope"]["data"]["operation"]["operation_id"] == original
            assert (await read_report(client, completed))["verification_outcome"] == "clean"

    with (
        OperationStore(tmp_path / "private-worker-state") as worker_store,
        listening(tmp_path, VerificationWorker(policy, worker_store)) as (verifier, _),
    ):
        asyncio.run(workflow(verifier, worker_store))
