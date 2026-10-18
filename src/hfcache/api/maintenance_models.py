"""Explicit maintenance scope; URLs alone select preview or apply (decision 117)."""

from pathlib import Path
from typing import Annotated, Self

from pydantic import BeforeValidator, Field, model_validator

from hfcache.api.command_models import CommandModel, SyncSubmission
from hfcache.config import ArchiveId  # noqa: TC001 - Pydantic field validation runs at runtime
from hfcache.identity import parse_selector
from hfcache.models import TransactionIdField, as_tuple
from hfcache.services.commands import RepairRequest

_MAX_ROOT_BYTES = 4096


def _whole_repository(value: object) -> str:
    if not isinstance(value, str):
        message = "selector must be a string"
        raise ValueError(message)  # noqa: TRY004 - Pydantic request validation
    parsed = parse_selector(value)
    if parsed.commit_sha is not None:
        message = "purge requires whole repository selectors without a revision"
        raise ValueError(message)
    return parsed.identity.selector


def _archive_root(value: object) -> Path:
    if not isinstance(value, str):
        message = "archive root must be an absolute path string"
        raise ValueError(message)  # noqa: TRY004 - Pydantic request validation
    if (
        not value.startswith("/")
        or len(value.encode("utf-8")) > _MAX_ROOT_BYTES
        or any(part in {".", ".."} for part in value.split("/"))
        or "\\" in value
        or any(not character.isprintable() for character in value)
    ):
        message = "archive root must be an absolute path without escaping components"
        raise ValueError(message)
    return Path(value)


WholeRepository = Annotated[str, Field(max_length=256), BeforeValidator(_whole_repository)]


class PruneSubmission(SyncSubmission):
    """Configured selection; the service preserves configuration order."""


class PurgeSubmission(CommandModel):
    selectors: Annotated[
        tuple[WholeRepository, ...], BeforeValidator(as_tuple), Field(max_length=100)
    ] = ()
    all_unmanaged: bool = False

    @model_validator(mode="after")
    def scope(self) -> Self:
        if bool(self.selectors) == self.all_unmanaged:
            message = "purge requires explicit selectors or all_unmanaged, exclusively"
            raise ValueError(message)
        object.__setattr__(self, "selectors", tuple(sorted(set(self.selectors))))
        return self


class RecoverySubmission(CommandModel):
    """Recovery always derives its complete scope from current journal evidence."""


class QuarantineSubmission(CommandModel):
    transaction_ids: Annotated[
        tuple[TransactionIdField, ...],
        BeforeValidator(as_tuple),
        Field(min_length=1, max_length=100),
    ]

    @model_validator(mode="after")
    def canonical(self) -> Self:
        object.__setattr__(self, "transaction_ids", tuple(sorted(set(self.transaction_ids))))
        return self


class RepairSubmission(CommandModel):
    revision: str = Field(max_length=256)
    reason: str = Field(default="operator_requested", max_length=2048)

    @model_validator(mode="after")
    def scope(self) -> Self:
        # The shared request validates exact immutable SHA scope without IO.
        self.service_request()
        return self

    def service_request(self) -> RepairRequest:
        return RepairRequest(self.revision, reason=self.reason)


class InitializationSubmission(CommandModel):
    archive_root: Annotated[Path, BeforeValidator(_archive_root)]
    archive_id: ArchiveId
    confirm: bool

    @model_validator(mode="after")
    def confirmation(self) -> Self:
        if self.confirm is not True:
            message = "initialization requires explicit true confirmation"
            raise ValueError(message)
        return self
