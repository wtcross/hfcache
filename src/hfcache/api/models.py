"""Versioned wire metadata, separate from durable archive schemas (decision 113)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiProblem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    request_id: str
    code: str
    message: str
    exit_code: int


class ReadResponse(BaseModel):
    """A complete schema-1 Envelope, or one explicitly paged piece of its data.

    Cursor walkers concatenate the named array and retain the first envelope's
    invocation metadata. They never silently replace a domain report identity.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    schema_version: Literal[1] = 1
    request_id: str
    archive_id: str | None
    config_fingerprint: str | None
    envelope: dict[str, Any]
    next_cursor: str | None = None


class PageQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    limit: int = Field(default=100, ge=1, le=10000)
    cursor: str | None = Field(default=None, max_length=256)
    selectors: tuple[str, ...] = ()
    repository_type: Literal["model", "dataset"] | None = None
