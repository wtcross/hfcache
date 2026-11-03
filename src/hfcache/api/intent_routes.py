"""Authenticated bounded observation and explicit original-key review (INV-023)."""

import hashlib
import json
import secrets
import time
from contextlib import ExitStack
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated, Literal

from fastapi import Request  # noqa: TC002 - FastAPI runtime annotations
from pydantic import BeforeValidator, Field
from starlette.responses import Response

from hfcache.api.auth import AuthenticationMethod, Capability, require_capability
from hfcache.api.commands import _key, _no_query, offload_command
from hfcache.api.intents import (
    IntentLease,
    IntentReview,
    LockIdentity,
    _schema_one,
    unavailable,
)
from hfcache.api.models import OperationView
from hfcache.errors import AuthorizationError, HfcacheError
from hfcache.host_models import HostStatus
from hfcache.host_protocol import HostProtocolError
from hfcache.locking import lock_path
from hfcache.metadata import MetadataReader, QueryBounds
from hfcache.models import ArchiveSentinel, DurableModel, TransactionJournal, load, serialize
from hfcache.paths import ArchiveLayout

if TYPE_CHECKING:
    from pathlib import Path

    from fastapi import FastAPI

    from hfcache.api.operations import IntentDisposition, OperationReceipt

PREFIX = "/api/v1"
MAX_INTENT_RESPONSE_BYTES = 65536


class RetirementRequest(DurableModel):
    schema_version: Annotated[Literal[1], BeforeValidator(_schema_one)]
    confirm: Literal["retire_unknown"]


class HelperInstance(DurableModel):
    pid: int = Field(strict=True, gt=1)
    start_ticks: int = Field(strict=True, gt=0)


class HelperReview(DurableModel):
    schema_version: Annotated[Literal[1], BeforeValidator(_schema_one)]
    archive_id: str
    deployment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    policy_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    effects_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    helper_instance: HelperInstance
    intent_lock: LockIdentity
    archive_lock: LockIdentity


def projection(
    archive_id: str, record: OperationReceipt | None, disposition: IntentDisposition | None
) -> dict[str, object]:
    operation = None
    if record is not None:
        raw = record.model_dump(mode="json")
        operation = OperationView.model_validate(
            {key: value for key, value in raw.items() if key in OperationView.model_fields}
            | {"result_recorded": record.result is not None}
        ).model_dump(mode="json")
    return {
        "schema_version": 1,
        "archive_id": archive_id,
        "state": "admitted"
        if record is not None
        else disposition.projected_state
        if disposition is not None
        else "unknown",
        "operation": operation,
        "disposition": disposition.projection(archive_id) if disposition is not None else None,
    }


def _response(value: dict[str, object]) -> Response:
    encoded = json.dumps(value, separators=(",", ":"), allow_nan=False).encode()
    if len(encoded) > MAX_INTENT_RESPONSE_BYTES:
        msg = "Intent response exceeds its bounded projection"
        raise unavailable(msg)
    return Response(encoded, media_type="application/json", headers={"Cache-Control": "no-store"})


def _remaining(deadline: float) -> None:
    if time.monotonic() >= deadline:
        msg = "Review deadline expired; preserve request and recheck actual executors"
        raise unavailable(msg)


def _archive_review(root: Path, archive_id: str) -> None:
    reader = MetadataReader(
        root,
        QueryBounds(
            maximum_entries=1024, maximum_artifact_bytes=1048576, maximum_total_bytes=8388608
        ),
    )
    layout = ArchiveLayout(root)
    sentinel = load(
        ArchiveSentinel, reader.read(layout.sentinel), error=HfcacheError, code="HFAPI015"
    )
    if sentinel.archive_id != archive_id:
        msg = "Archive identity changed; protected operator review required"
        raise unavailable(msg)
    for entry in reader.entries(layout.transactions, missing_ok=False):
        if not entry.path.name.endswith(".json"):
            msg = "Unclassified archive journal; operator review required"
            raise unavailable(msg)
        journal = load(
            TransactionJournal, reader.read(entry.path), error=HfcacheError, code="HFAPI015"
        )
        if not journal.is_resolved:
            msg = "Unfinished archive journal; operator recovery review required"
            raise unavailable(msg)


def _retire(request: Request, key: str) -> Response:  # noqa: PLR0915, PLR0912 - one bounded owned review
    state = request.app.state
    deadline = time.monotonic() + 30.0
    lanes = (state.runner, state.host_runner)
    with ExitStack() as owned:
        for lane in lanes:
            owned.enter_context(lane.review_barrier())
        if (
            state.runner.interlock is None
            or state.host_runner.interlock is None
            or state.runner.interlock.identity != state.host_runner.interlock.identity
        ):
            msg = "Companion authority is unproved; protected operator review required"
            raise unavailable(msg)
        intent = owned.enter_context(
            state.runner.interlock.acquire(exclusive=True, deadline=deadline)
        )
        store, archive_id = state.operations, state.policy.archive_id
        record, disposition = store.intent(request.state.principal, key, archive_id)
        if record is not None or (disposition is not None and disposition.review is not None):
            return _response(projection(archive_id, record, disposition))
        receipts = store.list()
        receipt_digest = store.receipt_set_digest(receipts)
        if any(item.state in {"queued", "waiting_lock", "running"} for item in receipts):
            msg = "Unfinished admitted operation; inspect its original receipt"
            raise unavailable(msg)
        try:
            worker = state.verifier.intent_review(deadline=deadline)
        except HfcacheError, OSError, ValueError, AttributeError:
            msg = "Private worker status is unproved; inspect the actual worker"
            raise unavailable(msg) from None
        _remaining(deadline)
        snapshot = state.policy.snapshot()
        if (
            worker.config_fingerprint != snapshot.fingerprint
            or worker.archive_id != archive_id
            or (worker.intent_device, worker.intent_inode)
            != (intent.identity.device, intent.identity.inode)
        ):
            msg = "Private worker instance/policy/companion differs; inspect selected runtime"
            raise unavailable(msg)
        helper = getattr(state, "host_helper", None)
        try:
            if helper is None:
                raise AttributeError  # noqa: TRY301 - narrow unavailable boundary
            helper_identity = helper.intent_review_identity()
            proof = HelperReview.model_validate(helper.intent_review(deadline=deadline))
            expected_helper = helper_identity.get("helper")
            if (
                not isinstance(expected_helper, dict)
                or proof.deployment_sha256 != helper_identity.get("deployment_sha256")
                or proof.policy_sha256 != helper_identity.get("policy_sha256")
                or proof.helper_instance.pid != expected_helper.get("pid")
                or proof.helper_instance.start_ticks != expected_helper.get("start_ticks")
            ):
                raise ValueError  # noqa: TRY301 - exact helper/runtime generation
            if helper.intent_review_identity() != helper_identity:
                raise ValueError  # noqa: TRY301 - reject changed helper within review
        except HostProtocolError, HfcacheError, OSError, ValueError, TypeError, AttributeError:
            msg = "Protected executor proof unavailable; inspect helper and pending outcomes"
            raise unavailable(msg) from None
        _remaining(deadline)
        if proof.archive_id != archive_id or proof.intent_lock != intent.identity:
            msg = "Protected runtime/archive binding changed; operator review required"
            raise unavailable(msg)
        # No helper/worker exchanges occur beneath this original noncreating lock.
        original = owned.enter_context(
            IntentLease(lock_path(), exclusive=True, deadline=deadline, expected=proof.archive_lock)
        )
        _archive_review(snapshot.config.storage.archive_root, archive_id)
        _remaining(deadline)
        if state.policy.snapshot().fingerprint != snapshot.fingerprint:
            msg = "Installed policy changed during review"
            raise unavailable(msg)
        if helper.intent_review_identity() != helper_identity:
            message = "Protected helper instance changed during review"
            raise unavailable(message)
        _remaining(deadline)
        review_data = {
            "schema_version": 1,
            "review_id": secrets.token_hex(16),
            "observed_at": datetime.now(UTC)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            "deployment_sha256": proof.deployment_sha256,
            "policy_sha256": proof.policy_sha256,
            "receipt_set_sha256": receipt_digest,
            "worker_state_sha256": hashlib.sha256(
                serialize(worker.model_dump(mode="json")).encode()
            ).hexdigest(),
            "helper_effects_sha256": proof.effects_sha256,
            "instances_sha256": hashlib.sha256(
                serialize(
                    {
                        "api": state.instance_id,
                        "worker": worker.instance_id,
                        "helper": proof.helper_instance.model_dump(),
                        "helper_binding": helper_identity,
                    }
                ).encode()
            ).hexdigest(),
            "intent_lock": intent.identity.model_dump(),
            "archive_lock": original.identity.model_dump(),
        }
        review = IntentReview.model_validate(
            review_data | {"sha256": hashlib.sha256(serialize(review_data).encode()).hexdigest()}
        )
        record, disposition = store.retire(
            request.state.principal, key, archive_id, review, receipt_set_sha256=receipt_digest
        )
        return _response(projection(archive_id, record, disposition))


def install_intent_routes(app: FastAPI) -> None:
    app.state.command_routes = frozenset(getattr(app.state, "command_routes", ())) | {
        PREFIX + "/operations/intent/retire"
    }

    @app.get(PREFIX + "/jobs/readiness")
    async def readiness(request: Request) -> Response:
        _no_query(request)
        require_capability(request.state.principal, Capability.READ)
        state = request.app.state
        value: dict[str, object] = {
            "schema_version": 1,
            "archive_id": state.policy.archive_id,
            "config_fingerprint": None,
            "archive": None,
            "hub": None,
            "control": None,
            "archive_writable": None,
            "verification_available": None,
        }
        try:
            snapshot = await offload_command(request, state.policy.snapshot)
            value["config_fingerprint"] = snapshot.fingerprint
        except HfcacheError:
            pass
        helper = getattr(state, "host_helper", None)
        if helper is not None:
            try:
                status = HostStatus.model_validate(await helper.async_status())
                if (
                    status.state in {"supported", "guarded"}
                    and status.binding is not None
                    and status.binding.archive_id == state.policy.archive_id
                    and status.facts is not None
                ):
                    value["archive_writable"] = status.facts.archive_mount in {"nfs-rw", "local-rw"}
                    if request.state.principal.authentication_method is AuthenticationMethod.BASIC:
                        for action in ("archive", "hub", "control"):
                            value[action] = getattr(status.permissions, action)
            except HostProtocolError, HfcacheError, OSError, ValueError, TypeError, AttributeError:
                value["archive_writable"] = None
        try:
            await offload_command(request, state.verifier.check_available)
            value["verification_available"] = True
        except HfcacheError, OSError, ValueError:
            pass
        return _response(value)

    @app.get(PREFIX + "/operations/intent")
    async def intent(request: Request) -> Response:
        _no_query(request)
        require_capability(request.state.principal, Capability.READ)
        key = _key(request)

        def read() -> Response:
            record, disposition = app.state.operations.intent(
                request.state.principal, key, app.state.policy.archive_id
            )
            return _response(projection(app.state.policy.archive_id, record, disposition))

        return await offload_command(request, read)

    @app.post(PREFIX + "/operations/intent/retire")
    async def retire(request: Request, body: RetirementRequest) -> Response:  # noqa: ARG001 - validation before side effects
        _no_query(request)
        if request.state.principal.authentication_method is not AuthenticationMethod.BASIC:
            raise AuthorizationError
        return await offload_command(request, lambda: _retire(request, _key(request)))
