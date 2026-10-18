"""Strict client wire models, independent of application/server policy (decision 118)."""

from dataclasses import dataclass
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from hfcache.identity import parse_run_id, parse_transaction_id
from hfcache.models import as_tuple, parse_timestamp
from hfcache.reporting import Envelope  # noqa: TC001 - Pydantic nested validation at runtime

JOB_ROUTES = frozenset(
    "/api/v1/" + name
    for name in (
        "syncs",
        "plans",
        "verifications",
        "diagnostics",
        "prune-plans",
        "prunes",
        "purge-plans",
        "purges",
        "recovery-plans",
        "recoveries",
        "quarantine-plans",
        "quarantine-cleanups",
        "repairs",
        "archive/initializations",
    )
)


def exact_version(value: object) -> int:
    """Schema omission, bools, strings, coercion and future versions all fail closed."""
    if type(value) is not int or value != 1:
        message = "unsupported schema version"
        raise ValueError(message)
    return value


def _archive_id(value: object) -> str:
    if not isinstance(value, str):
        message = "archive identity must be canonical"
        raise ValueError(message)  # noqa: TRY004 - Pydantic validation
    if str(UUID(value)) != value:
        message = "archive identity must be canonical"
        raise ValueError(message)
    return value


Version = Annotated[int, BeforeValidator(exact_version)]
Identifier = Annotated[str, BeforeValidator(parse_run_id)]
ArchiveId = Annotated[str, BeforeValidator(_archive_id)]
Fingerprint = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$", min_length=64, max_length=64)]


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)


class ClientRead(WireModel):
    schema_version: Version
    request_id: Identifier
    archive_id: ArchiveId | None
    config_fingerprint: Fingerprint | None
    envelope: Envelope
    next_cursor: str | None = Field(default=None, min_length=1, max_length=256)

    @model_validator(mode="before")
    @classmethod
    def required_envelope_version(cls, value: object) -> object:
        if not isinstance(value, dict) or not isinstance(value.get("envelope"), dict):
            message = "missing envelope"
            raise ValueError(message)  # noqa: TRY004 - Pydantic validation
        exact_version(value["envelope"].get("schema_version"))
        return value

    @model_validator(mode="after")
    def coherent_envelope(self) -> Self:
        started = parse_timestamp(self.envelope.started_at)
        completed = parse_timestamp(self.envelope.completed_at)
        if completed < started or (self.envelope.exit_code == 0 and self.envelope.errors):
            message = "inconsistent envelope evidence"
            raise ValueError(message)
        return self


class ClientOperation(WireModel):
    schema_version: Version
    operation_id: Identifier
    principal: Literal["rest-writer", "rest-reader"]
    route: str
    archive_id: ArchiveId
    config_fingerprint: Fingerprint
    state: Literal["queued", "waiting_lock", "running", "succeeded", "failed", "interrupted"]
    created_at: str
    updated_at: str
    completed_at: str | None
    domain_run_id: Identifier | None
    transaction_ids: Annotated[
        tuple[Annotated[str, BeforeValidator(parse_transaction_id)], ...], BeforeValidator(as_tuple)
    ]
    next_event_sequence: int = Field(ge=1)
    result_recorded: bool

    @model_validator(mode="after")
    def evidence(self) -> Self:
        created, updated = parse_timestamp(self.created_at), parse_timestamp(self.updated_at)
        completed = parse_timestamp(self.completed_at) if self.completed_at is not None else None
        active = self.state in {"queued", "waiting_lock", "running"}
        terminal = self.state in {"succeeded", "failed"}
        if (
            self.route not in JOB_ROUTES
            or updated < created
            or (completed is not None and not created <= completed <= updated)
            or (active and (completed is not None or self.result_recorded))
            or (not active and completed is None)
            or (terminal and (not self.result_recorded or self.domain_run_id is None))
            or (self.state == "interrupted" and self.result_recorded)
        ):
            message = "inconsistent operation evidence"
            raise ValueError(message)
        return self


class ClientLinks(WireModel):
    status: str
    result: str
    events: str


class Acceptance(WireModel):
    schema_version: Version
    request_id: Identifier
    archive_id: ArchiveId
    config_fingerprint: Fingerprint
    operation: ClientOperation
    created: bool
    links: ClientLinks

    @model_validator(mode="after")
    def identity(self) -> Self:
        if (
            self.archive_id != self.operation.archive_id
            or self.config_fingerprint != self.operation.config_fingerprint
        ):
            message = "acceptance identity disagrees with receipt"
            raise ValueError(message)
        return self


@dataclass(frozen=True, slots=True)
class Submission:
    key: str
    acceptance: Acceptance


class Capabilities(WireModel):
    api_version: Version
    credential_class: Literal["rest-writer", "rest-reader"]
    capabilities: Annotated[tuple[Literal["read", "write"], ...], BeforeValidator(as_tuple)]
    instance_id: Identifier
    reads: bool
    operations: bool
    operation_history: bool
    mcp: bool
    maintenance_enabled: bool
    max_page_size: int = Field(ge=1, le=10000)

    @model_validator(mode="after")
    def permissions(self) -> Self:
        expected = {"read", "write"} if self.credential_class == "rest-writer" else {"read"}
        if set(self.capabilities) != expected or len(set(self.capabilities)) != len(
            self.capabilities
        ):
            message = "capability class and permissions disagree"
            raise ValueError(message)
        return self


class ClientProblem(WireModel):
    request_id: Identifier
    code: str
    message: str
    exit_code: int


class ClientEvent(WireModel):
    schema_version: Version
    sequence: int = Field(ge=1)
    at: str
    kind: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")
    message: str

    @model_validator(mode="after")
    def timestamp(self) -> Self:
        parse_timestamp(self.at)
        return self


class ClientEvents(WireModel):
    operation_id: Identifier
    events: Annotated[tuple[ClientEvent, ...], BeforeValidator(as_tuple)]
    next_cursor: int = Field(ge=0)
    oldest_sequence: int = Field(ge=1)
    truncated: bool
