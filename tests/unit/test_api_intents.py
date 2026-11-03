"""Original-key HTTP semantics under the actual Basic/ASGI boundary (INV-023)."""

import asyncio

import httpx
import pytest

from hfcache.api.auth import AuthenticationMethod, CredentialClass, Principal
from hfcache.api.command_models import SyncSubmission
from hfcache.errors import OperationError
from hfcache.logging import reset
from tests.fixtures import examples
from tests.intent_fixtures import create_app
from tests.unit.test_host_authorization import StatusClient as StatusSource
from tests.unit.test_host_authorization import status
from tests.unit.test_web_basic_boundary import authorization
from tests.unit.test_web_basic_boundary import configured as configured  # noqa: PLC0414 - fixtures
from tests.unit.test_web_basic_boundary import (
    in_memory_administrator as in_memory_administrator,  # noqa: PLC0414 - fixtures
)


class StatusClient(StatusSource):
    def close(self):
        return True


@pytest.fixture(autouse=True)
def isolated_logging():
    reset()
    yield
    reset()


def headers(password, key="original"):
    return {
        "Authorization": authorization(password),
        "Origin": "https://testserver",
        "X-Hfcache-Request": "1",
        "Idempotency-Key": key,
    }


def test_fresh_refusal_is_durable_and_own_namespace_get_survives_reload(configured):
    server, password, lock = configured
    helper = StatusClient(
        status(denied=("archive", "hub", "control", "configuration", "schedule", "observer"))
    )

    async def action():
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            refusal = await client.post("/api/v1/syncs", headers=headers(password), json={})
            assert refusal.status_code == 403
            assert refusal.headers["Hfcache-Intent"] == "closed"
            response = await client.get("/api/v1/operations/intent", headers=headers(password))
            saved = response.json()
            assert saved["state"] == "not_admitted"
            assert saved["operation"] is None
            assert saved["disposition"]["reason"] == "permission_denied"
            assert "key_digest" not in response.text
            assert "request_digest" not in response.text
            assert app.state.operations.list() == ()
            malformed = await client.post(
                "/api/v1/syncs", headers=headers(password, "malformed"), json={"schema_version": 2}
            )
            assert malformed.status_code == 422
            assert "Hfcache-Intent" not in malformed.headers
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            assert (
                await client.get("/api/v1/operations/intent", headers=headers(password))
            ).json() == saved
            bearer = await client.get(
                "/api/v1/operations/intent",
                headers={
                    "Authorization": "Bearer writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
                    "Idempotency-Key": "original",
                },
            )
            assert bearer.json()["state"] == "unknown"
            retired = await client.post(
                "/api/v1/operations/intent/retire",
                headers={
                    "Authorization": "Bearer writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
                    "Idempotency-Key": "original",
                },
                json={"schema_version": 1, "confirm": "retire_unknown"},
            )
            assert retired.status_code == 403

    asyncio.run(action())


def test_existing_admission_precedes_later_helper_denial_without_enqueue(configured):
    server, password, lock = configured
    helper = StatusClient(status(denied=("archive",)))

    async def action():
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            principal = Principal(
                CredentialClass.REST_WRITER,
                authentication_method=AuthenticationMethod.BASIC,
                subject="boundary-administrator-v1",
            )
            admission = app.state.operations.admit(
                principal,
                "original",
                "/api/v1/syncs",
                SyncSubmission().canonical_body(),
                app.state.policy.snapshot,
            )
            response = await client.post("/api/v1/syncs", headers=headers(password), json={})
            assert response.status_code == 202
            assert response.json()["created"] is False
            assert response.json()["operation"]["operation_id"] == admission.receipt.operation_id
            assert helper.async_calls == 0
            assert app.state.runner.active_operation_id is None
            conflict = await client.post(
                "/api/v1/diagnostics",
                headers=headers(password),
                json={"read_only": True},
            )
            assert conflict.status_code == 409

    asyncio.run(action())


def test_failed_fence_publication_has_no_closed_hint_or_execution(configured, monkeypatch):
    server, password, lock = configured
    helper = StatusClient(status(denied=("archive",)))

    async def action():
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):

            def fail(*_):
                raise OperationError

            monkeypatch.setattr(app.state.operations, "_write", fail)
            response = await client.post("/api/v1/syncs", headers=headers(password), json={})
            assert response.status_code == 503
            assert "Hfcache-Intent" not in response.headers
            assert (
                await client.get("/api/v1/operations/intent", headers=headers(password))
            ).json()["state"] == "unknown"
            assert app.state.operations.list() == ()

    asyncio.run(action())


def test_readiness_needs_read_capability_and_reports_nullable_fresh_facts(configured):
    server, password, lock = configured
    helper = StatusClient(status(denied=("archive", "hub", "control")))

    async def action():
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            unauthenticated = await client.get("/api/v1/jobs/readiness")
            assert unauthenticated.status_code == 401
            response = await client.get("/api/v1/jobs/readiness", headers=headers(password))
            assert response.status_code == 200
            data = response.json()
            assert data["archive_id"] == examples.ARCHIVE_ID
            assert data["archive"] is False
            assert data["hub"] is False
            assert data["control"] is False
            assert data["verification_available"] is None
            assert "units" not in data

    asyncio.run(action())


def test_bounded_metadata_pool_refusal_cannot_publish_a_fence(configured):
    import threading  # noqa: PLC0415 - hold the existing bounded worker

    server, password, lock = configured
    server = server.model_copy(
        update={
            "limits": server.limits.model_copy(update={"metadata_workers": 1, "metadata_queue": 0})
        }
    )
    helper = StatusClient(status(denied=("archive",)))

    async def action():
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            reached, finish = threading.Event(), threading.Event()

            def hold():
                reached.set()
                assert finish.wait(5)

            lease = app.state.pool.submit(hold)
            assert reached.wait(5)
            try:
                response = await client.post("/api/v1/syncs", headers=headers(password), json={})
                assert response.status_code == 503
                assert "Hfcache-Intent" not in response.headers
                assert helper.async_calls == 0
            finally:
                finish.set()
                await lease.future
                lease.finish_request()
            principal = Principal(
                CredentialClass.REST_WRITER,
                authentication_method=AuthenticationMethod.BASIC,
                subject="boundary-administrator-v1",
            )
            assert app.state.operations.intent(principal, "original", examples.ARCHIVE_ID) == (
                None,
                None,
            )

    asyncio.run(action())


def test_actual_directory_fsync_failure_after_receipt_rename_never_acknowledges_queued(
    configured, monkeypatch
):
    import errno  # noqa: PLC0415 - actual fsync fault boundary
    import os  # noqa: PLC0415

    server, _, lock = configured

    async def action():
        app = create_app(server, instance_lock_path=lock)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            store = app.state.operations
            renamed = False
            sync = os.fsync

            def checkpoint(name):
                nonlocal renamed
                if name == "after_rename":
                    renamed = True

            def broken(descriptor):
                if renamed and descriptor == store._fd:
                    raise OSError(errno.EIO, "injected directory fsync failure")
                return sync(descriptor)

            auth = {
                "Authorization": "Bearer writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
                "Idempotency-Key": "publication",
            }
            store.checkpoint = checkpoint
            with monkeypatch.context() as patch:
                patch.setattr(os, "fsync", broken)
                response = await client.post("/api/v1/plans", headers=auth, json={})
                assert response.status_code == 503
                assert "Hfcache-Intent" not in response.headers
                assert renamed
                assert app.state.runner.active_operation_id is None
                assert not app.state.runner._queue
                assert (
                    await client.get("/api/v1/operations/intent", headers=auth)
                ).status_code == 503
            store.checkpoint = None
            observed = (await client.get("/api/v1/operations/intent", headers=auth)).json()
            assert observed["state"] == "admitted"
            assert observed["operation"]["state"] == "interrupted"

    asyncio.run(action())


def test_unsupported_query_cannot_close_a_validated_job_body(configured):
    server, password, lock = configured
    helper = StatusClient(status(denied=("archive",)))

    async def action():
        app = create_app(server, instance_lock_path=lock, host_helper=helper)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://testserver"
            ) as client,
        ):
            response = await client.post(
                "/api/v1/syncs?unsupported=1", headers=headers(password), json={}
            )
            assert response.status_code == 422
            assert "Hfcache-Intent" not in response.headers
            assert helper.async_calls == 0
            assert (
                await client.get("/api/v1/operations/intent", headers=headers(password))
            ).json()["state"] == "unknown"

    asyncio.run(action())
