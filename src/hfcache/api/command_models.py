"""Strict command admission DTOs, independent of durable schemas (decision 116)."""

from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from hfcache.api.models import (
    OperationView,  # noqa: TC001 - Pydantic resolves nested DTOs at runtime
)
from hfcache.errors import ConfigurationError
from hfcache.identity import parse_selector
from hfcache.models import RunIdField, as_tuple
from hfcache.services.commands import VerificationRequest
from hfcache.services.requests import CatalogRefreshRequest


def _selection(value: object) -> str:
    if not isinstance(value, str):
        message = "selector must be a string"
        raise ValueError(message)  # noqa: TRY004 - collected by Pydantic as request validation
    return parse_selector(value).identity.selector


Selector = Annotated[str, Field(max_length=256), BeforeValidator(_selection)]
_MAX_CANDIDATE_BYTES = 1048576


def _candidate_text(value: object) -> str:
    if not isinstance(value, str):
        message = "candidate must be TOML text"
        raise ValueError(message)  # noqa: TRY004 - Pydantic request validation
    if not 0 < len(value.encode("utf-8")) <= _MAX_CANDIDATE_BYTES:
        message = "candidate text exceeds its byte bounds"
        raise ValueError(message)
    return value


CandidateText = Annotated[str, BeforeValidator(_candidate_text)]


class CommandModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    def canonical_body(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class SyncSubmission(CommandModel):
    selectors: Annotated[
        tuple[Selector, ...], BeforeValidator(as_tuple), Field(max_length=100)
    ] = ()

    @model_validator(mode="after")
    def canonical(self) -> Self:
        object.__setattr__(self, "selectors", tuple(sorted(set(self.selectors))))
        return self


class CatalogRefreshSubmission(CommandModel):
    """Whole-repository offline intent, without path, credential or candidate fields."""

    selectors: Annotated[
        tuple[Annotated[str, Field(max_length=201)], ...],
        BeforeValidator(as_tuple),
        Field(max_length=256),
    ] = ()
    revision_scope: Literal["current", "retained"] = "retained"
    tags: bool = True
    technical: bool = True

    @model_validator(mode="after")
    def canonical(self) -> Self:
        try:
            request = self.service_request()
        except ConfigurationError:
            message = "Invalid catalog refresh intent"
            raise ValueError(message) from None
        object.__setattr__(self, "selectors", request.selectors)
        return self

    def service_request(self) -> CatalogRefreshRequest:
        return CatalogRefreshRequest(
            selectors=self.selectors,
            revision_scope=self.revision_scope,
            tags=self.tags,
            technical=self.technical,
        )


class PlanSubmission(SyncSubmission):
    candidate: CandidateText | None = None

    @model_validator(mode="after")
    def explicit_candidate(self) -> Self:
        if "candidate" in self.model_fields_set and self.candidate is None:
            message = "candidate must contain TOML text when supplied"
            raise ValueError(message)
        return self

    def canonical_body(self) -> dict[str, Any]:
        body = super().canonical_body()
        # Omission predates this optional field (decision 119). Other request
        # nulls, particularly verification scope, keep their established digest.
        if self.candidate is None:
            body.pop("candidate")
        return body


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
    """Bounded content hook; no request-selected server path exists."""

    candidate: CandidateText


class ValidationSubmission(CommandModel):
    candidate: CandidateText | None = None

    @model_validator(mode="after")
    def explicit_candidate(self) -> Self:
        if "candidate" in self.model_fields_set and self.candidate is None:
            message = "candidate must contain TOML text when supplied"
            raise ValueError(message)
        return self


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
