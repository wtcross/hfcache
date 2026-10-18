"""Maintenance URLs cannot bypass fresh authority or evidence (INV-013/014, FS-19)."""

import asyncio
import json
import time

import httpx
import pytest

from hfcache import locking
from hfcache.api.app import create_app
from hfcache.logging import reset
from hfcache.paths import RepositoryLayout
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.commands import CommandServices
from hfcache.services.context import ServiceResult
from tests.fixtures import examples
from tests.unit.test_api_command_adversarial import MCP, READER, WRITER, _raw
from tests.unit.test_api_commands import (
    configured as command_archive,  # noqa: F401 - real archive fixture
)
from tests.unit.test_quarantine import abandoned, publish_current
from tests.unit.test_synchronize import MODEL

PREVIEW_ROUTES = (
    "/api/v1/prune-plans",
    "/api/v1/purge-plans",
    "/api/v1/recovery-plans",
    "/api/v1/quarantine-plans",
)
APPLY_ROUTES = (
    "/api/v1/prunes",
    "/api/v1/purges",
    "/api/v1/recoveries",
    "/api/v1/quarantine-cleanups",
    "/api/v1/repairs",
    "/api/v1/archive/initializations",
)
INIT = "/api/v1/archive/initializations"


@pytest.fixture(autouse=True)
def isolate_logging():
    reset()
    yield
    reset()


@pytest.fixture
def settings(tmp_path):
    archive = tmp_path / "archive"
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{archive}"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n[hub]\ntoken_mode="disabled"\n'
    )
    credentials = {}
    for name, value in (("writer", WRITER), ("reader", READER), ("mcp_reader", MCP)):
        path = tmp_path / name
        path.write_text(value, encoding="ascii")
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(policy),
            "state_directory": str(tmp_path / "state"),
            "credentials": credentials,
            "listener": {"allowed_hosts": ["testserver"]},
            "limits": {"max_request_bytes": 1024},
        }
    )
    return server, policy, archive, tmp_path / "daemon.lock"


@pytest.fixture
def configured(settings):
    server, policy, archive, lock = settings
    return create_app(server, instance_lock_path=lock), policy, archive


@pytest.mark.parametrize("route", [*PREVIEW_ROUTES, *APPLY_ROUTES])
@pytest.mark.parametrize("token", [None, MCP])
def test_every_maintenance_surface_authenticates_before_receiving_body(configured, route, token):
    app, _, archive = configured

    status, payload, received = asyncio.run(_raw(app, route, token=token, body=b"x" * 2048))

    assert status == 401
    assert payload["code"] == "HFAPI001"
    assert received == 0
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize("route", APPLY_ROUTES)
def test_every_apply_route_requires_writer_before_receiving_body(configured, route):
    app, _, archive = configured

    status, payload, received = asyncio.run(_raw(app, route, token=READER, body=b"x" * 2048))

    assert status == 403
    assert payload["code"] == "HFAPI002"
    assert received == 0
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


def test_initialization_is_disabled_before_body_or_receipt(configured):
    app, _, archive = configured

    status, payload, received = asyncio.run(_raw(app, INIT, body=b"x" * 2048))

    assert status == 403
    assert payload["code"] == "HFAPI002"
    assert received == 0
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize("route", [*PREVIEW_ROUTES, *APPLY_ROUTES[:-1]])
@pytest.mark.parametrize("field", ["apply", "dry_run", "preview", "plan"])
def test_body_mode_or_altered_preview_cannot_grant_execution(configured, route, field):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(
            app,
            route,
            body=json.dumps({field: True}).encode(),
            headers=[(b"idempotency-key", b"altered-preview")],
        )
    )

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize("confirm", [None, False, 0, 1, "true", [], {}])
def test_initialization_requires_literal_true_confirmation(settings, confirm):
    server, _, archive, lock = settings
    app = create_app(
        server.model_copy(update={"maintenance_enabled": True}), instance_lock_path=lock
    )
    body = {"archive_root": str(archive), "archive_id": examples.ARCHIVE_ID}
    if confirm is not None:
        body["confirm"] = confirm

    status, payload, _ = asyncio.run(
        _raw(
            app,
            INIT,
            body=json.dumps(body).encode(),
            headers=[(b"idempotency-key", b"invalid-confirmation")],
        )
    )

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("archive_root", "relative"),
        ("archive_root", "/tmp/a/../different"),
        ("archive_root", "/tmp/escaped\x00path"),
        ("archive_root", 1),
        ("archive_id", None),
        ("archive_id", "../not-an-id"),
        ("archive_id", 1),
        ("inspect", True),
        ("token_file", "/tmp/secret"),
        ("config", "/tmp/other.toml"),
    ],
)
def test_initialization_rejects_unsafe_or_untyped_authority_fields(settings, field, value):
    server, _, archive, lock = settings
    app = create_app(
        server.model_copy(update={"maintenance_enabled": True}), instance_lock_path=lock
    )
    body = {"archive_root": str(archive), "archive_id": examples.ARCHIVE_ID, "confirm": True}
    body[field] = value

    status, payload, _ = asyncio.run(
        _raw(
            app,
            INIT,
            body=json.dumps(body).encode(),
            headers=[(b"idempotency-key", b"invalid-authority")],
        )
    )

    assert status == 422
    assert payload["code"] in {"HFAPI006", "HFARG001"}
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize("route", ["/api/v1/purge-plans", "/api/v1/purges"])
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"selectors": []},
        {"selectors": [MODEL.selector], "all_unmanaged": True},
        {"all_unmanaged": 1},
        {"all_unmanaged": "true"},
        {"selectors": [MODEL.selector + "@" + examples.SHA]},
    ],
)
def test_purge_requires_one_explicit_unmanaged_repository_scope(configured, route, body):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(
            app,
            route,
            body=json.dumps(body).encode(),
            headers=[(b"idempotency-key", b"invalid-purge-scope")],
        )
    )

    assert status == 422
    assert payload["code"] in {"HFAPI006", "HFARG001"}
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize("route", ["/api/v1/quarantine-plans", "/api/v1/quarantine-cleanups"])
@pytest.mark.parametrize(
    "ids", [None, [], "a" * 32, ["../escape"], ["A" * 32], [1], ["a" * 32] * 101]
)
def test_quarantine_requires_a_bounded_explicit_transaction_id_array(configured, route, ids):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(
            app,
            route,
            body=json.dumps({"transaction_ids": ids}).encode(),
            headers=[(b"idempotency-key", b"invalid-quarantine-scope")],
        )
    )

    assert status in {413, 422}
    assert payload["code"] in {"HFAPI006", "HFARG001"}
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize(
    ("route", "body"),
    [
        ("/api/v1/prune-plans", {}),
        ("/api/v1/prunes", {}),
        ("/api/v1/purge-plans", {"all_unmanaged": True}),
        ("/api/v1/purges", {"all_unmanaged": True}),
        ("/api/v1/recovery-plans", {}),
        ("/api/v1/recoveries", {}),
        ("/api/v1/quarantine-plans", {"transaction_ids": ["a" * 32]}),
        ("/api/v1/quarantine-cleanups", {"transaction_ids": ["a" * 32]}),
        ("/api/v1/repairs", {"revision": MODEL.selector + "@" + examples.SHA}),
    ],
)
def test_even_semantic_preview_requires_submission_key_before_service_work(configured, route, body):
    app, _, archive = configured

    status, payload, _ = asyncio.run(_raw(app, route, body=json.dumps(body).encode()))

    assert status == 422
    assert payload["code"] == "HFAPI006"
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"revision": MODEL.selector},
        {"revision": MODEL.selector + "@main"},
        {"revision": MODEL.selector + "@" + "A" * 40},
        {"revision": "../escape"},
        {"revision": 1},
        {"revision": MODEL.selector + "@" + examples.SHA, "reason": 1},
        {"revision": MODEL.selector + "@" + examples.SHA, "reason": None},
        {"revision": MODEL.selector + "@" + examples.SHA, "token_file": "/tmp/secret"},
    ],
)
def test_repair_requires_exact_revision_and_never_accepts_credential_override(configured, body):
    app, _, archive = configured

    status, payload, _ = asyncio.run(
        _raw(
            app,
            "/api/v1/repairs",
            body=json.dumps(body).encode(),
            headers=[(b"idempotency-key", b"invalid-repair")],
        )
    )

    assert status == 422
    assert payload["code"] in {"HFAPI006", "HFARG001"}
    assert not archive.exists()
    assert not list(app.state.operations.root.glob("*.json"))


def test_preview_key_does_not_authorize_apply_and_maintenance_gate_only_controls_init(
    configured, tmp_path, monkeypatch
):
    app, _, archive = configured
    requests = []

    def recover(self, request):
        requests.append((request.dry_run, request.apply))
        command = "recover --apply" if request.apply else "recover --dry-run"
        if request.apply:
            with locking.exclusive_lock(tmp_path / "archive.lock", command=command, wait_seconds=0):
                return ServiceResult(command, {})
        return ServiceResult(command, {})

    monkeypatch.setattr(CommandServices, "recover", recover)

    async def scenario():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            headers = {"Authorization": f"Bearer {WRITER}", "Idempotency-Key": "preview-only"}
            preview = await client.post("/api/v1/recovery-plans", json={}, headers=headers)
            assert preview.status_code == 202
            identifier = preview.json()["operation"]["operation_id"]
            planned = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=5)
            assert planned.command == "recover --dry-run"
            conflict = await client.post("/api/v1/recoveries", json={}, headers=headers)
            assert conflict.status_code == 409
            assert conflict.json()["code"] == "HFAPI012"
            assert len(app.state.operations.list()) == 1
            assert requests == [(True, False)]
            applied = await client.post(
                "/api/v1/recoveries",
                json={},
                headers=headers | {"Idempotency-Key": "explicit-apply"},
            )
            assert applied.status_code == 202
            completed = await asyncio.to_thread(
                app.state.runner.wait, applied.json()["operation"]["operation_id"], timeout=5
            )
            assert completed.command == "recover --apply"
            assert completed.exit_code == 0
            assert requests == [(True, False), (False, True)]
            assert len(app.state.operations.list()) == 2

    asyncio.run(scenario())
    assert not archive.exists()


def test_queued_purge_becoming_managed_refuses_under_lock_before_hub_or_deletion(
    request, monkeypatch
):
    server, layout, _, lock = request.getfixturevalue("command_archive")
    publish_current(layout, {"config.json": b"preserve these archived bytes"})
    repository = RepositoryLayout(layout, MODEL)
    original_reference = repository.current_ref.read_bytes()
    base = (
        f'schema_version=1\n[storage]\narchive_root="{layout.root}"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\nminimum_free_space_gib=0\n'
        "minimum_free_space_percent=0\n[sync]\nlock_wait_seconds=10\n"
        '[hub]\ntoken_mode="disabled"\n'
    )
    server.archive_config.write_text(base)

    def forbidden(*args, **kwargs):
        pytest.fail("stale or managed purge contacted Hub or attempted deletion")

    monkeypatch.setattr("hfcache.services.commands.HubClient.of", forbidden)
    monkeypatch.setattr("hfcache.services.commands.apply_purge", forbidden)
    app = create_app(server, instance_lock_path=lock)

    async def scenario():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            headers = {"Authorization": f"Bearer {WRITER}", "Idempotency-Key": "queued-purge"}
            with locking.exclusive_lock(
                locking.lock_path(), command="external writer", wait_seconds=0
            ):
                accepted = await client.post(
                    "/api/v1/purges", json={"selectors": [MODEL.selector]}, headers=headers
                )
                assert accepted.status_code == 202
                identifier = accepted.json()["operation"]["operation_id"]
                deadline = time.monotonic() + 5
                while app.state.operations.get(identifier).state != "waiting_lock":
                    assert time.monotonic() < deadline
                    await asyncio.sleep(0.005)
                server.archive_config.write_text(
                    base + f'[[repositories]]\ntype="model"\nid="{MODEL.id}"\n'
                )
            outcome = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=5)
            assert outcome.exit_code == 10
            assert [problem.code for problem in outcome.errors] == ["HFAPI007"]
            again = await client.post(
                "/api/v1/purges",
                json={"selectors": [MODEL.selector]},
                headers=headers | {"Idempotency-Key": "new-managed-purge"},
            )
            assert again.status_code == 202
            managed = await asyncio.to_thread(
                app.state.runner.wait, again.json()["operation"]["operation_id"], timeout=5
            )
            assert managed.exit_code == 10
            assert [problem.code for problem in managed.errors] == ["HFARG007"]
            assert repository.current_ref.read_bytes() == original_reference
            assert list(repository.revisions.iterdir())
            assert list(layout.transactions.iterdir()) == []

    asyncio.run(scenario())


def test_quarantine_apply_reproves_entire_batch_after_preview_and_preserves_unknown_evidence(
    request,
):
    server, layout, _, lock = request.getfixturevalue("command_archive")
    first, second = sorted([abandoned(layout), abandoned(layout)])
    paths = [layout.quarantine_for(identifier) for identifier in (first, second)]
    journals = {path.name: path.read_bytes() for path in layout.transactions.iterdir()}
    app = create_app(server, instance_lock_path=lock)

    async def scenario():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client,
        ):
            body = {"transaction_ids": [first, second]}
            preview = await client.post(
                "/api/v1/quarantine-plans",
                json=body,
                headers={"Authorization": f"Bearer {READER}", "Idempotency-Key": "batch-preview"},
            )
            assert preview.status_code == 202
            preview_id = preview.json()["operation"]["operation_id"]
            proven = await asyncio.to_thread(app.state.runner.wait, preview_id, timeout=5)
            assert proven.exit_code == 0
            assert len(proven.data["plans"]) == 2
            unknown = paths[1] / "unknown-proof.bin"
            unknown.write_bytes(b"preserve unrecognized quarantine evidence")
            applied = await client.post(
                "/api/v1/quarantine-cleanups",
                json=body,
                headers={"Authorization": f"Bearer {WRITER}", "Idempotency-Key": "batch-apply"},
            )
            assert applied.status_code == 202
            identifier = applied.json()["operation"]["operation_id"]
            outcome = await asyncio.to_thread(app.state.runner.wait, identifier, timeout=5)
            assert outcome.exit_code == 50
            assert [problem.code for problem in outcome.errors] == ["HFRET010"]
            assert all(path.is_dir() for path in paths)
            assert unknown.read_bytes() == b"preserve unrecognized quarantine evidence"
            assert {
                path.name: path.read_bytes() for path in layout.transactions.iterdir()
            } == journals
            fetched = await client.get(
                f"/api/v1/operations/{identifier}/result",
                headers={"Authorization": f"Bearer {READER}"},
            )
            assert fetched.status_code == 200
            assert fetched.json()["envelope"] == outcome.to_payload()
            assert app.state.operations.result(preview_id) == proven

    asyncio.run(scenario())
