"""Maintenance uses real archive services; verification remains private Unix IPC.

Only owned storage and the external Hub/DNS/TLS fixture boundaries are supplied.
No maintenance executor, safety predicate or operation response is replaced.
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from hfcache.identity import TransactionId
from hfcache.paths import RepositoryLayout
from hfcache.publication import read_reference, retained_references
from hfcache.server_config import InstalledPolicy
from hfcache.verification_executor import VerificationWorker
from tests.intent_fixtures import OperationStore, create_app
from tests.unit.test_api_commands import configured as configured  # noqa: PLC0414 - shared fixture
from tests.unit.test_api_commands import submit
from tests.unit.test_api_operations import READER_HEADERS, WRITER_HEADERS
from tests.unit.test_synchronize import CONTENT, DATASET, MODEL, SHA_A
from tests.unit.test_verification_executor import listening
from tests.unit.test_web_operations_worker import (
    real_services as real_services,  # noqa: PLC0414 - real external-boundary fixture
)
from tests.unit.test_web_operations_worker import result


def retained_file(path):
    """Compare persistent identity and bytes, excluding read-induced atime."""
    info = path.stat()
    return (
        tuple(
            getattr(info, name)
            for name in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_uid",
                "st_gid",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        ),
        path.read_bytes(),
    )


def repaired_evidence(layout, identity, original, repaired):
    reference, manifest, manifest_before, member, damaged_before = original
    assert repaired["exit_code"] == 0
    replacement = read_reference(layout, RepositoryLayout(layout, identity).current_ref)
    assert replacement.commit_sha == reference.commit_sha
    assert replacement.publication_generation == reference.publication_generation
    assert replacement.publication_id != reference.publication_id
    replacement_member = layout.published / replacement.tree / "weights.bin"
    assert replacement_member.read_bytes() == CONTENT["weights.bin"]
    assert retained_file(manifest) == manifest_before
    assert retained_file(member) == damaged_before
    transaction_id = repaired["data"]["transaction_id"]
    journal = layout.journal(TransactionId(transaction_id))
    retirement = layout.root / repaired["data"]["retirement_record"]
    evidence = json.loads(journal.read_bytes())
    assert evidence["state"] == "open"
    assert evidence["checkpoints"][-1]["name"] == "repair_committed"
    grace = json.loads(retirement.read_bytes())
    assert datetime.fromisoformat(grace["grace_expires_at"]) - datetime.fromisoformat(
        grace["retired_at"]
    ) >= timedelta(hours=168)
    assert datetime.fromisoformat(grace["grace_expires_at"]) > datetime.now(UTC)
    return transaction_id, {
        path: retained_file(path) for path in (journal, retirement, manifest, member)
    }


def test_sequential_api_repairs_preserve_open_grace_and_real_worker_verifies_replacements(
    real_services, tmp_path
):
    server, layout, _, instance_lock = real_services
    policy = InstalledPolicy.open(server)

    async def workflow(verifier, worker_store):
        app = create_app(server, instance_lock_path=instance_lock, verification_executor=verifier)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            synced = await result(client, await submit(client, "/api/v1/syncs", {}, "seed-both"))
            assert synced["exit_code"] == 0
            original = {}
            for identity in (MODEL, DATASET):
                reference = read_reference(layout, RepositoryLayout(layout, identity).current_ref)
                manifest = layout.published / reference.manifest
                member = layout.published / reference.tree / "weights.bin"
                # Preserve canonical Hub cache bytes; this damage belongs only
                # to the owned published inode under test.
                member.unlink()
                member.write_bytes(("damaged " + identity.selector).encode())
                original[identity] = (
                    reference,
                    manifest,
                    retained_file(manifest),
                    member,
                    retained_file(member),
                )

            damaged = await submit(
                client, "/api/v1/verifications", {"mode": "full"}, "before-repair"
            )
            findings = await result(client, damaged)
            assert findings["exit_code"] == 40
            assert {row["repository_type"] for row in findings["data"]["findings"]} == {
                "model",
                "dataset",
            }
            assert (
                worker_store.result(damaged["operation"]["operation_id"]).model_dump(mode="json")
                == findings
            )

            first_preserved = {}
            repair_transactions = set()
            for identity in (MODEL, DATASET):
                accepted = await submit(
                    client,
                    "/api/v1/repairs",
                    {
                        "revision": f"{identity.selector}@{SHA_A}",
                        "reason": "owned integrity finding",
                    },
                    "repair-" + identity.type,
                )
                repaired = await result(client, accepted)
                transaction_id, preserved = repaired_evidence(
                    layout, identity, original[identity], repaired
                )
                repair_transactions.add(transaction_id)
                assert all(
                    retained_file(path) == before for path, before in first_preserved.items()
                )
                first_preserved.update(preserved)

            preview = await result(
                client,
                await submit(
                    client, "/api/v1/recovery-plans", {}, "grace-preview", headers=READER_HEADERS
                ),
            )
            assert preview["exit_code"] == 0
            assert preview["data"]["blocked"] == preview["data"]["actionable"] == 0
            assert {row["transaction_id"] for row in preview["data"]["plan"]} == repair_transactions
            assert {row["remedy"] for row in preview["data"]["plan"]} == {"wait"}
            assert all(retained_file(path) == before for path, before in first_preserved.items())

            accepted = await submit(
                client, "/api/v1/verifications", {"mode": "full"}, "after-both-repairs"
            )
            clean = await result(client, accepted)
            assert clean["exit_code"] == 0
            assert clean["data"]["findings"] == []
            assert (
                worker_store.result(accepted["operation"]["operation_id"]).model_dump(mode="json")
                == clean
            )
            assert len(worker_store.list()) == 2
            assert all(retained_file(path) == before for path, before in first_preserved.items())

    with (
        OperationStore(tmp_path / "maintenance-worker") as worker_store,
        listening(tmp_path, VerificationWorker(policy, worker_store)) as (verifier, _),
    ):
        asyncio.run(workflow(verifier, worker_store))


def test_lost_prune_acceptance_recovers_original_key_without_replaying_domain_effect(
    real_services,
):
    server, layout, hub, instance_lock = real_services

    class LostAcceptance(httpx.AsyncBaseTransport):
        """Drop only one genuine ASGI 202 after the real app admitted its job."""

        def __init__(self, app):
            self.actual = httpx.ASGITransport(app=app)
            self.attempts = 0

        async def handle_async_request(self, request):
            response = await self.actual.handle_async_request(request)
            if request.method == "POST" and request.url.path == "/api/v1/prunes":
                self.attempts += 1
                assert self.attempts == 1
                assert response.status_code == 202
                await response.aclose()
                message = "owned loss after actual prune admission"
                raise httpx.ReadError(message, request=request)
            return response

        async def aclose(self):
            await self.actual.aclose()

    async def workflow():
        app = create_app(server, instance_lock_path=instance_lock)
        transport = LostAcceptance(app)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=transport, base_url="http://testserver") as client,
        ):
            for number in range(1, 6):
                sha = str(number) * 40
                hub.revisions[sha] = dict(CONTENT) | {"revision.txt": str(number).encode()}
                hub.heads[MODEL.selector] = sha
                seeded = await result(
                    client,
                    await submit(
                        client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, f"seed-{number}"
                    ),
                )
                assert seeded["exit_code"] == 0
            server.archive_config.write_text(
                server.archive_config.read_text().replace(
                    "maximum_revisions = 5", "maximum_revisions = 3"
                )
            )
            current = RepositoryLayout(layout, MODEL).current_ref
            protected = retained_file(current)
            planned = await result(
                client,
                await submit(
                    client,
                    "/api/v1/prune-plans",
                    {"selectors": [MODEL.selector]},
                    "review-round",
                    headers=READER_HEADERS,
                ),
            )
            assert planned["exit_code"] == 0
            assert len(retained_references(layout, MODEL)) == 5
            original_key = "original-lost-prune"
            with pytest.raises(httpx.ReadError, match="owned loss after actual prune admission"):
                await client.post(
                    "/api/v1/prunes",
                    json={"selectors": [MODEL.selector]},
                    headers=WRITER_HEADERS | {"Idempotency-Key": original_key},
                )

            lookup = await client.get(
                "/api/v1/operations/lookup",
                headers=WRITER_HEADERS | {"Idempotency-Key": original_key},
            )
            assert lookup.status_code == 200
            original = lookup.json()["envelope"]["data"]["operation"]
            assert original["route"] == "/api/v1/prunes"
            recovered = await result(
                client,
                {
                    "links": {
                        "status": f"/api/v1/operations/{original['operation_id']}",
                        "result": f"/api/v1/operations/{original['operation_id']}/result",
                    }
                },
            )
            assert recovered["exit_code"] == 0
            assert transport.attempts == 1
            assert len(retained_references(layout, MODEL)) == 4
            assert retained_file(current) == protected
            assert len(list(layout.pruned_audit.rglob("*.manifest.json"))) == 1
            assert sum(row.route == "/api/v1/prunes" for row in app.state.operations.list()) == 1

    asyncio.run(workflow())
