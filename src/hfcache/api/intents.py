"""Permanent original-key closure and independent execution leases (INV-023).

The public store owns all publication under its original flock. No saved proof
can substitute for live exclusive ownership during an original-request review.
"""

import fcntl
import hashlib
import os
import stat
import time
from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import BeforeValidator, Field, model_validator

from hfcache.api.auth import CredentialClass
from hfcache.api.lifecycle import open_directory
from hfcache.config import ArchiveId  # noqa: TC001 - runtime Pydantic field
from hfcache.errors import OperationError
from hfcache.models import DurableModel, RunIdField, Sha256, Timestamp, as_tuple, dump, serialize

if TYPE_CHECKING:
    from pathlib import Path


INTENT_NAME = "intent-dispositions.json"
MAX_INTENT_BYTES = 1048576
MAX_INTENTS = 1024
MAX_REVIEW_BYTES = 4096
INTENT_MODE = 0o600
RefusalReason = Literal[
    "permission_denied",
    "storage_read_only",
    "executor_unavailable",
    "admission_unavailable",
    "invalid_policy",
]


class LockIdentity(DurableModel):
    device: int = Field(strict=True, ge=0)
    inode: int = Field(strict=True, ge=0)


def _schema_one(value: object) -> object:
    if type(value) is not int or value != 1:
        msg = "unsupported original-intent schema"
        raise ValueError(msg)
    return value


class IntentReview(DurableModel):
    schema_version: Annotated[Literal[1], BeforeValidator(_schema_one)]
    review_id: RunIdField
    observed_at: Timestamp
    deployment_sha256: Sha256
    policy_sha256: Sha256
    receipt_set_sha256: Sha256
    worker_state_sha256: Sha256
    helper_effects_sha256: Sha256
    instances_sha256: Sha256
    intent_lock: LockIdentity
    archive_lock: LockIdentity
    sha256: Sha256

    @model_validator(mode="after")
    def coherent(self) -> Self:
        body = serialize(self.model_dump(mode="json", exclude={"sha256"})).encode()
        if len(dump(self)) > MAX_REVIEW_BYTES or hashlib.sha256(body).hexdigest() != self.sha256:
            msg = "invalid original-intent review digest"
            raise ValueError(msg)
        return self


def _principal(value: object) -> CredentialClass:
    if not isinstance(value, str):
        message = "intent requires a credential class"
        raise ValueError(message)  # noqa: TRY004 - Pydantic collects ValueError
    return CredentialClass(value)


class IntentDisposition(DurableModel):
    disposition_id: RunIdField
    principal: Annotated[CredentialClass, BeforeValidator(_principal)]
    key_digest: Sha256
    state: Literal["not_admitted", "retired_unknown"]
    route: str | None
    request_digest: Sha256 | None
    created_at: Timestamp
    reason: RefusalReason | None
    review: IntentReview | None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.principal is CredentialClass.MCP_READER:
            msg = "intent requires a REST namespace"
            raise ValueError(msg)
        refused = self.state == "not_admitted"
        if refused != (self.reason is not None) or (not refused and self.review is None):
            msg = "intent state contradicts evidence"
            raise ValueError(msg)
        if refused != (self.route is not None) or refused != (self.request_digest is not None):
            msg = "intent state contradicts request binding"
            raise ValueError(msg)
        if self.route is not None:
            import re  # noqa: PLC0415 - grammar matches unchanged receipt routes

            if not re.fullmatch(r"/api/v1/[a-z0-9_/-]{1,200}", self.route) or "//" in self.route:
                msg = "invalid canonical intent route"
                raise ValueError(msg)
        return self

    @property
    def projected_state(self) -> Literal["not_admitted", "retired_unknown"]:
        return "retired_unknown" if self.review is not None else "not_admitted"

    def projection(self, archive_id: str) -> dict[str, object]:
        reviewed = self.review is not None
        return {
            "disposition_id": self.review.review_id
            if self.review is not None and self.state == "not_admitted"
            else self.disposition_id,
            "state": self.projected_state,
            "archive_id": archive_id,
            "route": None if reviewed else self.route,
            "created_at": self.review.model_dump(mode="json")["observed_at"]
            if self.review is not None
            else self.model_dump(mode="json")["created_at"],
            "reason": None if reviewed else self.reason,
            "review_sha256": self.review.sha256 if self.review is not None else None,
        }


class IntentState(DurableModel):
    schema_version: Annotated[Literal[1], BeforeValidator(_schema_one)]
    archive_id: ArchiveId
    entries: Annotated[tuple[IntentDisposition, ...], BeforeValidator(as_tuple)] = ()

    @model_validator(mode="after")
    def coherent(self) -> Self:
        bindings = [(entry.principal.value, entry.key_digest) for entry in self.entries]
        if (
            bindings != sorted(set(bindings))
            or len({entry.disposition_id for entry in self.entries}) != len(self.entries)
            or len(self.entries) > MAX_INTENTS
            or len(dump(self)) > MAX_INTENT_BYTES
        ):
            msg = "invalid bounded intent state"
            raise ValueError(msg)
        return self


def unavailable(
    message: str = "Original-intent authority unavailable; preserve state for review",
) -> OperationError:
    return OperationError(code="HFAPI015", status_code=503, message=message)


class IntentRefusalError(OperationError):
    """An explicit supported pre-admission refusal, still uncertain until fenced."""

    def __init__(self, reason: RefusalReason, message: str) -> None:
        self.reason = reason
        super().__init__(
            code="HFMNT004" if reason == "storage_read_only" else "HFAPI015",
            status_code=503,
            message=message,
        )


class AdmissionUncertainError(OperationError):
    """This publisher has not handed its new receipt to any executor."""

    def __init__(self, operation_id: str) -> None:
        self.operation_id = operation_id
        super().__init__(
            code="HFAPI015",
            status_code=503,
            message="Admission publication is uncertain; preserve and review the original request",
        )


class IntentLease:
    """One no-follow open description per lease; close only the owned description."""

    def __init__(
        self,
        path: Path,
        *,
        exclusive: bool = False,
        deadline: float | None = None,
        expected: LockIdentity | None = None,
    ) -> None:
        self.fd = -1
        self.transferred = False
        parent = -1
        try:
            parent = open_directory(path.parent)
            self.fd = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent
            )
            before = os.fstat(self.fd)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_uid != os.geteuid()
                or stat.S_IMODE(before.st_mode) != INTENT_MODE
                or before.st_nlink != 1
            ):
                raise unavailable()  # noqa: TRY301 - owned descriptor cleanup
            kind = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            while True:
                try:
                    fcntl.flock(self.fd, kind | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if deadline is None or time.monotonic() >= deadline:
                        msg = "Original request needs review: execution lease is busy"
                        raise unavailable(msg) from None
                    time.sleep(min(0.025, max(0, deadline - time.monotonic())))
            linked = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            if (linked.st_dev, linked.st_ino) != (before.st_dev, before.st_ino):
                raise unavailable()  # noqa: TRY301 - owned descriptor cleanup
            self.identity = LockIdentity(device=before.st_dev, inode=before.st_ino)
            if expected is not None and self.identity != expected:
                msg = "Companion identity changed; protected operator review required"
                raise unavailable(msg)  # noqa: TRY301 - owned descriptor cleanup
        except OSError:
            self.close()
            raise unavailable() from None
        except BaseException:
            self.close()
            raise
        finally:
            if parent >= 0:
                os.close(parent)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


class IntentInterlock:
    """Pin first validated companion identity; every lease must match it."""

    def __init__(self, path: Path) -> None:
        self.path = path
        with IntentLease(path) as initial:
            self.identity = initial.identity

    def acquire(self, *, exclusive: bool = False, deadline: float | None = None) -> IntentLease:
        return IntentLease(
            self.path, exclusive=exclusive, deadline=deadline, expected=self.identity
        )
