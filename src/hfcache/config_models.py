"""Strict managed configuration projections and edits (CONFIG-01 through05, decision153)."""

import re
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from hfcache.config import (  # noqa: TC001 - Pydantic resolves fields at runtime
    RepositoryConfig,
    RepositoryId,
)
from hfcache.errors import ConfigurationError
from hfcache.identity import parse_selector
from hfcache.models import ArchiveIdField, RunIdField, as_tuple
from hfcache.wire_models import PlanPayload  # noqa: TC001 - Pydantic resolves nested DTOs

MAXIMUM_EDITS = 256
MAXIMUM_CANDIDATE_BYTES = 1048576

EDITABLE_FIELDS = (
    "storage.publication_mode",
    "storage.minimum_free_space_gib",
    "storage.minimum_free_space_percent",
    "storage.maximum_revisions",
    "sync.max_workers",
    "sync.lock_wait_seconds",
    "sync.continue_on_repository_error",
    "sync.dependency_policy",
    "sync.stale_staging_age_hours",
    "verification.lock_wait_seconds",
    "repair.retired_instance_grace_hours",
    "repositories",
)
PROTECTED_FIELDS = (
    ("storage.archive_root", "Archive root is fixed by installed deployment authority."),
    ("storage.archive_id", "Archive identity is fixed by installed deployment authority."),
    ("hub", "Hub endpoint and credential authority are preserved privately."),
    ("verification.algorithm", "The verification algorithm is fixed."),
    ("verification.hash_new_content", "Hashing new content is required."),
    ("server", "Server policy and credentials are managed outside archive configuration."),
)


def _one(value: object) -> int:
    if type(value) is not int or value != 1:
        message = "configuration schema version must be integer1"
        raise ValueError(message)
    return value


def _revision(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch("[0-9a-f]{64}", value) is None:
        message = "configuration revision must be an opaque lowercase64-hex token"
        raise ValueError(message)
    return value


def _whole_selector(value: object) -> str:
    if not isinstance(value, str):
        message = "required selector must be a string"
        raise ValueError(message)  # noqa: TRY004 - Pydantic validation
    try:
        parsed = parse_selector(value)
    except ConfigurationError:
        message = "required selector has invalid repository grammar"
        raise ValueError(message) from None
    if parsed.commit_sha is not None:
        message = "required selector must identify a whole repository"
        raise ValueError(message)
    return parsed.identity.selector


def _candidate(value: object) -> str:
    if not isinstance(value, str):
        message = "private candidate must contain TOML text"
        raise ValueError(message)  # noqa: TRY004 - Pydantic validation
    if not 0 < len(value.encode("utf-8")) <= MAXIMUM_CANDIDATE_BYTES:
        message = "private candidate exceeds its byte bounds"
        raise ValueError(message)
    return value


SchemaOne = Annotated[Literal[1], BeforeValidator(_one)]
OpaqueRevision = Annotated[str, BeforeValidator(_revision)]
WholeSelector = Annotated[str, BeforeValidator(_whole_selector)]
RequiredSelectors = Annotated[
    tuple[WholeSelector, ...], BeforeValidator(as_tuple), Field(max_length=MAXIMUM_EDITS)
]
PublicationMode = Literal["hardlink", "copy"]
FreeGiB = Annotated[int, Field(ge=0, le=1048576)]
FreePercent = Annotated[int, Field(ge=0, le=100)]
Workers = Annotated[int, Field(ge=1, le=32)]
SyncWait = Annotated[int, Field(ge=0, le=86400)]
StagingAge = Annotated[int, Field(ge=1, le=8760)]
VerificationWait = Annotated[int, Field(ge=0, le=604800)]
RepairGrace = Annotated[int, Field(ge=168, le=8760)]


def _retention(value: object) -> int:
    if type(value) is not int or value not in {3, 5}:
        message = "maximum revisions must be integer3 or5"
        raise ValueError(message)
    return value


Retention = Annotated[int, BeforeValidator(_retention)]


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)


class EditableStorage(ConfigModel):
    publication_mode: PublicationMode
    minimum_free_space_gib: FreeGiB
    minimum_free_space_percent: FreePercent
    maximum_revisions: Retention


class EditableSync(ConfigModel):
    max_workers: Workers
    lock_wait_seconds: SyncWait
    continue_on_repository_error: bool
    dependency_policy: Literal["warn"]
    stale_staging_age_hours: StagingAge


class EditableVerification(ConfigModel):
    lock_wait_seconds: VerificationWait


class EditableRepair(ConfigModel):
    retired_instance_grace_hours: RepairGrace


class EditableConfig(ConfigModel):
    storage: EditableStorage
    sync: EditableSync
    verification: EditableVerification
    repair: EditableRepair
    repositories: Annotated[tuple[RepositoryConfig, ...], BeforeValidator(as_tuple)]

    @model_validator(mode="after")
    def unique_repositories(self) -> Self:
        keys = [row.key for row in self.repositories]
        if len(keys) != len(set(keys)):
            message = "editable configuration contains duplicate repository identities"
            raise ValueError(message)
        return self


class SettingsTable(ConfigModel):
    """An omitted replacement differs from null, zero and false (decision153)."""

    @model_validator(mode="after")
    def nonempty(self) -> Self:
        if not self.model_fields_set or any(
            getattr(self, key) is None for key in self.model_fields_set
        ):
            message = "settings replacement tables must be nonempty and cannot contain null"
            raise ValueError(message)
        return self


class StorageReplacement(SettingsTable):
    publication_mode: PublicationMode | None = None
    minimum_free_space_gib: FreeGiB | None = None
    minimum_free_space_percent: FreePercent | None = None
    maximum_revisions: Retention | None = None


class SyncReplacement(SettingsTable):
    max_workers: Workers | None = None
    lock_wait_seconds: SyncWait | None = None
    continue_on_repository_error: bool | None = None
    dependency_policy: Literal["warn"] | None = None
    stale_staging_age_hours: StagingAge | None = None


class VerificationReplacement(SettingsTable):
    lock_wait_seconds: VerificationWait | None = None


class RepairReplacement(SettingsTable):
    retired_instance_grace_hours: RepairGrace | None = None


class SettingsReplacement(SettingsTable):
    storage: StorageReplacement | None = None
    sync: SyncReplacement | None = None
    verification: VerificationReplacement | None = None
    repair: RepairReplacement | None = None


class RepositoryUpsert(ConfigModel):
    kind: Literal["repository-upsert"]
    repository: RepositoryConfig


class RepositoryRemove(ConfigModel):
    kind: Literal["repository-remove"]
    repository_type: Literal["model", "dataset"]
    repository_id: RepositoryId


class SettingsReplace(ConfigModel):
    kind: Literal["settings-replace"]
    settings: SettingsReplacement


ManagedEdit = Annotated[
    RepositoryUpsert | RepositoryRemove | SettingsReplace, Field(discriminator="kind")
]


class ManagedEditRequest(ConfigModel):
    base_revision: OpaqueRevision
    edits: Annotated[
        tuple[ManagedEdit, ...], BeforeValidator(as_tuple), Field(max_length=MAXIMUM_EDITS)
    ]

    @model_validator(mode="after")
    def unique_edits(self) -> Self:
        seen: set[tuple[str, str]] = set()
        settings = False
        for edit in self.edits:
            if isinstance(edit, SettingsReplace):
                if settings:
                    message = "at most one settings replacement is permitted"
                    raise ValueError(message)
                settings = True
                continue
            key = (
                edit.repository.key
                if isinstance(edit, RepositoryUpsert)
                else (edit.repository_type, edit.repository_id)
            )
            if key in seen:
                message = "a repository identity may be edited only once"
                raise ValueError(message)
            seen.add(key)
        return self


class ProtectedField(ConfigModel):
    field: str
    description: str

    @model_validator(mode="after")
    def fixed_description(self) -> Self:
        if (self.field, self.description) not in PROTECTED_FIELDS:
            message = "protected field descriptions must use the fixed nonsecret metadata"
            raise ValueError(message)
        return self


class ConfigRead(ConfigModel):
    schema_version: SchemaOne
    archive_id: ArchiveIdField
    base_revision: OpaqueRevision
    editable: EditableConfig
    editable_fields: Annotated[tuple[str, ...], BeforeValidator(as_tuple)]
    protected_fields: Annotated[tuple[ProtectedField, ...], BeforeValidator(as_tuple)]

    @model_validator(mode="after")
    def fixed_fields(self) -> Self:
        if (
            self.editable_fields != EDITABLE_FIELDS
            or tuple((row.field, row.description) for row in self.protected_fields)
            != PROTECTED_FIELDS
        ):
            message = "configuration metadata must contain the complete fixed field descriptions"
            raise ValueError(message)
        return self


class ConfigPrepared(ConfigModel):
    """Private helper reply; candidate text must never enter public operation results."""

    schema_version: SchemaOne
    archive_id: ArchiveIdField
    base_revision: OpaqueRevision
    candidate_revision: OpaqueRevision
    candidate: Annotated[str, BeforeValidator(_candidate)]
    editable: EditableConfig
    required_selectors: RequiredSelectors

    @model_validator(mode="after")
    def unique_scope(self) -> Self:
        _require_unique_scope(self.required_selectors)
        return self


def _require_unique_scope(selectors: tuple[str, ...]) -> None:
    if len(selectors) != len(set(selectors)):
        message = "required repository scope must not contain duplicates"
        raise ValueError(message)


class ManagedValidation(ConfigModel):
    schema_version: SchemaOne
    archive_id: ArchiveIdField
    base_revision: OpaqueRevision
    candidate_revision: OpaqueRevision
    required_selectors: RequiredSelectors
    valid: Literal[True]

    @model_validator(mode="before")
    @classmethod
    def strict_valid(cls, value: object) -> object:
        if isinstance(value, dict) and type(value.get("valid")) is not bool:
            message = "managed validation validity must be a boolean"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def unique_scope(self) -> Self:
        _require_unique_scope(self.required_selectors)
        return self


class ManagedAssessment(ConfigModel):
    schema_version: SchemaOne
    archive_id: ArchiveIdField
    base_revision: OpaqueRevision
    candidate_revision: OpaqueRevision
    required_selectors: RequiredSelectors
    complete: bool
    sizing: PlanPayload | None

    @model_validator(mode="after")
    def complete_scope(self) -> Self:
        _require_unique_scope(self.required_selectors)
        if not self.required_selectors:
            if self.sizing is not None:
                message = "empty managed scope must not include Hub sizing"
                raise ValueError(message)
            return self
        if self.sizing is None:
            if self.complete:
                message = "complete managed assessment requires sizing for its scope"
                raise ValueError(message)
            return self
        selectors = [
            f"{row.repository_type}:{row.repository_id}" for row in self.sizing.repositories
        ]
        if len(selectors) != len(set(selectors)) or set(selectors) != set(self.required_selectors):
            message = "managed sizing must match the exact required repository scope"
            raise ValueError(message)
        if self.complete and any(
            not row.enabled
            or row.upstream_state != "available"
            or any(
                value is None
                for value in (
                    row.resolved_commit_sha,
                    row.estimated_new_bytes,
                    row.file_count,
                    row.logical_bytes,
                    row.projected_publication_bytes,
                )
            )
            for row in self.sizing.repositories
        ):
            message = "complete managed sizing requires enabled and fully sized repositories"
            raise ValueError(message)
        return self


def _preview_key(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9._~+-]{1,128}", value) is None:
        message = "preview key must use the bounded idempotency-key grammar"
        raise ValueError(message)
    return value


class ConfigPreviewReference(ConfigModel):
    operation_id: RunIdField
    key: Annotated[str, BeforeValidator(_preview_key)]


class ConfigApplicationSubmission(ConfigModel):
    managed: ManagedEditRequest
    preview: ConfigPreviewReference

    def canonical_body(self) -> dict[str, Any]:
        return {
            "managed": self.managed.model_dump(mode="json", exclude_none=True),
            "preview": self.preview.model_dump(mode="json"),
        }


class ConfigApplicationOutcome(ConfigModel):
    """Authenticated host observation, independent of an API receipt's state."""

    schema_version: SchemaOne
    archive_id: ArchiveIdField
    operation_id: RunIdField
    request_digest: OpaqueRevision
    base_revision: OpaqueRevision | None
    candidate_revision: OpaqueRevision | None
    config_fingerprint: OpaqueRevision | None
    state: Literal[
        "staged", "unchanged", "installed_unconfirmed", "confirmed", "conflict", "unknown"
    ]
    pending: bool

    @model_validator(mode="after")
    def coherent_identity(self) -> Self:
        known = tuple(
            value is not None
            for value in (
                self.base_revision,
                self.candidate_revision,
                self.config_fingerprint,
            )
        )
        if (any(known) and not all(known)) or (self.state != "unknown" and not all(known)):
            message = "host outcome requires a complete original configuration identity"
            raise ValueError(message)
        return self
