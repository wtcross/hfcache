"""HTTP maintenance reuses real deletion, repair, recovery and initialization proofs."""

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta

import pytest

from hfcache.identity import TransactionId
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import create_staging, read_reference, retained_references
from tests.unit.test_api_commands import (
    configured as command_archive,  # noqa: F401 - reused pytest fixture
)
from tests.unit.test_api_commands import exercise, result, submit
from tests.unit.test_api_operations import READER_HEADERS, WRITER_HEADERS
from tests.unit.test_quarantine import abandoned, begin
from tests.unit.test_synchronize import ARCHIVE_ID, CONTENT, DATASET, MODEL, SHA_A
from tests.unit.test_verification import nfs_line


@pytest.fixture
def configured(request):
    return request.getfixturevalue("command_archive")


def test_prune_previews_and_applies_one_round_without_replaying_key(configured):
    server, layout, hub, _ = configured

    async def action(client, app):
        for number in range(1, 6):
            sha = str(number) * 40
            hub.revisions[sha] = dict(CONTENT) | {"revision.txt": str(number).encode()}
            hub.heads[MODEL.selector] = sha
            synced = await result(
                client,
                await submit(
                    client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, f"seed-{number}"
                ),
            )
            assert synced["exit_code"] == 0
        server.archive_config.write_text(
            server.archive_config.read_text().replace(
                "maximum_revisions = 5", "maximum_revisions = 3"
            )
        )
        body = {"selectors": [MODEL.selector]}
        preview = await result(
            client,
            await submit(client, "/api/v1/prune-plans", body, "preview", headers=READER_HEADERS),
        )
        assert preview["exit_code"] == 0
        assert len(preview["data"]["plans"]) == 1
        assert len(retained_references(layout, MODEL)) == 5
        first = await submit(client, "/api/v1/prunes", body, "apply-round")
        assert (await result(client, first))["exit_code"] == 0
        assert len(retained_references(layout, MODEL)) == 4
        retry = await submit(client, "/api/v1/prunes", body, "apply-round")
        assert retry["created"] is False
        assert retry["operation"]["operation_id"] == first["operation"]["operation_id"]
        assert len(retained_references(layout, MODEL)) == 4
        second = await result(client, await submit(client, "/api/v1/prunes", body, "next-round"))
        assert second["exit_code"] == 0
        assert len(retained_references(layout, MODEL)) == 3
        current = read_reference(layout, RepositoryLayout(layout, MODEL).current_ref)
        assert current.commit_sha == "5" * 40

    asyncio.run(exercise(configured, action))


def test_unmanaged_purge_preserves_unknown_entries_then_audits_explicit_apply(configured):
    server, layout, _, _ = configured

    async def action(client, app):
        assert (await result(client, await submit(client, "/api/v1/syncs", {}, "seed")))[
            "exit_code"
        ] == 0
        server.archive_config.write_text(
            server.archive_config.read_text().replace(
                '[[repositories]]\nid = "organization/model-name"\ntype = "model"\n', ""
            )
        )
        body = {"selectors": [MODEL.selector]}
        preview = await result(
            client,
            await submit(
                client, "/api/v1/purge-plans", body, "purge-preview", headers=READER_HEADERS
            ),
        )
        assert preview["exit_code"] == 0
        repository = RepositoryLayout(layout, MODEL)
        reference = read_reference(layout, repository.current_ref)
        original_manifest = (layout.published / reference.manifest).read_bytes()
        unexpected = repository.directory / "unknown-proof.bin"
        unexpected.write_bytes(b"unexplained fixture evidence")
        refused = await result(client, await submit(client, "/api/v1/purges", body, "unknown"))
        assert refused["exit_code"] == 50
        assert unexpected.read_bytes() == b"unexplained fixture evidence"
        assert repository.current_ref.exists()
        # This fixture removes exactly the marker it introduced, then exercises
        # the unchanged application deletion/audit path with a new reviewed key.
        unexpected.unlink()
        completed = await result(client, await submit(client, "/api/v1/purges", body, "purge"))
        assert completed["exit_code"] == 0
        assert not repository.directory.exists()
        assert RepositoryLayout(layout, DATASET).current_ref.is_file()
        manifests = list(layout.pruned_audit.rglob("*.manifest.json"))
        assert any(path.read_bytes() == original_manifest for path in manifests)

    asyncio.run(exercise(configured, action))


def test_repair_keeps_original_manifest_generation_locator_and_grace(configured):
    _, layout, _, _ = configured

    async def action(client, app):
        assert (
            await result(
                client,
                await submit(client, "/api/v1/syncs", {"selectors": [MODEL.selector]}, "seed"),
            )
        )["exit_code"] == 0
        repository = RepositoryLayout(layout, MODEL)
        original = read_reference(layout, repository.current_ref)
        original_manifest = (layout.published / original.manifest).read_bytes()
        (layout.published / original.tree / "weights.bin").write_bytes(b"damaged fixture")
        completed = await result(
            client,
            await submit(
                client,
                "/api/v1/repairs",
                {"revision": f"{MODEL.selector}@{SHA_A}", "reason": "HTTP fixture"},
                "repair",
            ),
        )
        assert completed["exit_code"] == 0
        replacement = read_reference(layout, repository.current_ref)
        assert replacement.commit_sha == original.commit_sha
        assert replacement.publication_generation == original.publication_generation
        assert replacement.publication_id != original.publication_id
        assert (layout.published / replacement.tree / "weights.bin").read_bytes() == CONTENT[
            "weights.bin"
        ]
        assert (layout.published / original.tree / "weights.bin").read_bytes() == b"damaged fixture"
        assert (layout.published / original.manifest).read_bytes() == original_manifest
        retirement = json.loads((layout.root / completed["data"]["retirement_record"]).read_bytes())
        assert retirement["reason"] == "HTTP fixture"
        assert retirement["retired_publication_id"] == original.publication_id
        created = datetime.fromisoformat(retirement["retired_at"])
        expires = datetime.fromisoformat(retirement["grace_expires_at"])
        assert expires - created >= timedelta(hours=168)

    asyncio.run(exercise(configured, action))


def test_recovery_preview_and_apply_preserve_exact_durable_report_identity(configured):
    _, layout, _, _ = configured
    transaction = begin(layout)
    identifier = TransactionId(transaction.journal.transaction_id)
    staging = create_staging(layout, identifier)
    transaction.checkpoint(
        "staging_created", staging_path=str(layout.archive_relative(staging.directory))
    )
    old = (datetime.now(UTC) - timedelta(hours=48)).timestamp()
    os.utime(staging.directory, (old, old))

    async def action(client, app):
        preview = await result(
            client,
            await submit(
                client, "/api/v1/recovery-plans", {}, "recovery-preview", headers=READER_HEADERS
            ),
        )
        assert preview["exit_code"] == 0
        assert preview["data"]["actionable"] == 1
        assert staging.directory.exists()
        applied = await result(client, await submit(client, "/api/v1/recoveries", {}, "recovery"))
        assert applied["exit_code"] == 0
        assert applied["data"]["applied"] == 1
        assert not staging.directory.exists()
        assert layout.quarantine_for(identifier).exists()
        report = json.loads((layout.root / applied["data"]["report"]).read_bytes())
        assert report["run_id"] == applied["run_id"]

    asyncio.run(exercise(configured, action))


def test_quarantine_cleanup_uses_full_batch_proof_and_preserves_other_evidence(configured):
    _, layout, _, _ = configured
    selected, other = abandoned(layout), abandoned(layout)
    selected_path, other_path = layout.quarantine_for(selected), layout.quarantine_for(other)
    before = {path.name: path.read_bytes() for path in layout.transactions.iterdir()}

    async def action(client, app):
        body = {"transaction_ids": [selected]}
        preview = await result(
            client,
            await submit(
                client,
                "/api/v1/quarantine-plans",
                body,
                "quarantine-preview",
                headers=READER_HEADERS,
            ),
        )
        assert preview["exit_code"] == 0
        assert selected_path.exists()
        completed = await result(
            client, await submit(client, "/api/v1/quarantine-cleanups", body, "clean")
        )
        assert completed["exit_code"] == 0
        assert not selected_path.exists()
        assert other_path.exists()
        assert {path.name: path.read_bytes() for path in layout.transactions.iterdir()} == before

    asyncio.run(exercise(configured, action))


@pytest.mark.parametrize("enabled", [False, True])
def test_initialization_is_only_explicit_confirmed_and_configured(configured, tmp_path, enabled):
    server, old_layout, hub, lock = configured
    root = tmp_path / "fresh"
    root.mkdir()
    server.archive_config.write_text(
        server.archive_config.read_text().replace(str(old_layout.root), str(root))
    )
    (tmp_path / "mountinfo").write_text(nfs_line(str(root)))
    revised = (
        server.model_copy(update={"maintenance_enabled": enabled}),
        ArchiveLayout(root),
        hub,
        lock,
    )

    async def action(client, app):
        assert (await client.get("/api/v1/health", headers=READER_HEADERS)).status_code == 200
        assert (
            await client.get("/api/v1/archive/inspection", headers=READER_HEADERS)
        ).status_code == 200
        assert not ArchiveLayout(root).sentinel.exists()
        body = {"archive_root": str(root), "archive_id": ARCHIVE_ID, "confirm": True}
        if not enabled:
            response = await client.post(
                "/api/v1/archive/initializations",
                json=body,
                headers=WRITER_HEADERS | {"Idempotency-Key": "initialization"},
            )
            assert response.status_code == 403
            assert response.json()["code"] == "HFAPI002"
            assert app.state.operations.list() == ()
            assert not ArchiveLayout(root).sentinel.exists()
        else:
            completed = await result(
                client,
                await submit(client, "/api/v1/archive/initializations", body, "initialization"),
            )
            assert completed["exit_code"] == 0
            sentinel = json.loads(ArchiveLayout(root).sentinel.read_bytes())
            assert sentinel["archive_id"] == ARCHIVE_ID

    asyncio.run(exercise(revised, action))
