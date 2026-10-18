"""Strict command admission DTOs, independent of durable schemas (decision 116)."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from hfcache.api.models import (
    OperationView,  # noqa: TC001 - Pydantic resolves nested DTOs at runtime
)
from hfcache.identity import parse_selector
from hfcache.models import RunIdField, as_tuple
from hfcache.services.commands import VerificationRequest


def _selection(value: object) -> str:
    if not isinstance(value, str):
        message = "selector must be a string"
        raise ValueError(message)  # noqa: TRY004 - collected by Pydantic as request validation
    return parse_selector(value).identity.selector


Selector = Annotated[str, Field(max_length=256), BeforeValidator(_selection)]


class CommandModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class SyncSubmission(CommandModel):
    selectors: Annotated[
        tuple[Selector, ...], BeforeValidator(as_tuple), Field(max_length=100)
    ] = ()

    @model_validator(mode="after")
    def canonical(self) -> Self:
        object.__setattr__(self, "selectors", tuple(sorted(set(self.selectors))))
        return self


class PlanSubmission(SyncSubmission):
    pass


class VerificationSubmission(CommandModel):
    mode: Literal["new", "full", "revision"]
    revision: str | None = Field(default=None, max_length=256)
    run_id: RunIdField | None = None

    @model_validator(mode="after")
    def scope(self) -> Self:
        if (self.mode == "revision") != (self.revision is not None) or (
            self.run_id is not None and self.mode != "new"
        ):
            message = "verification mode and scope are inconsistent"
            raise ValueError(message)
        if self.revision is not None:
            parsed = parse_selector(self.revision)
            if parsed.commit_sha is None:
                message = "revision verification requires a full commit SHA"
                raise ValueError(message)
        return self

    def service_request(self) -> VerificationRequest:
        return VerificationRequest(
            new=self.mode == "new",
            full=self.mode == "full",
            revision=self.revision,
            run_id=self.run_id,
        )


class DiagnosticsSubmission(CommandModel):
    read_only: bool


class InstalledValidationSubmission(CommandModel):
    pass


class CandidatePayload(CommandModel):
    """Reserved API-012 content hook; no request-selected server path exists."""

    candidate: str = Field(min_length=1, max_length=1048576)


class OperationLinks(CommandModel):
    status: str
    result: str
    events: str


class AcceptanceResponse(CommandModel):
    schema_version: Literal[1] = 1
    request_id: str
    archive_id: str
    config_fingerprint: str
    operation: OperationView
    created: bool
    links: OperationLinks
