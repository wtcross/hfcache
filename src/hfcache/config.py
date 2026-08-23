"""Configuration loading and strict validation.

The schema, its constraints, and the `HFCFG###` error codes are the contract in
`docs/configuration.md`. Everything here runs before any network request or
filesystem mutation, so an invalid configuration can never partially apply.

Three properties are load-bearing and are enforced by `_Strict` rather than by
convention:

* `extra="forbid"` — a typo is an error, never a silently ignored setting.
* `strict=True` — `"4"` is not an integer and `1` is not a boolean. TOML already
  distinguishes these, so a type error always means the operator wrote the wrong
  thing.
* `frozen=True` — configuration is immutable for the life of the process.

Identifier grammars — repository ids, revisions, commit SHAs — live in
`hfcache.identity`, which is also where the paths built from them get their
guarantees. This module owns only the grammars that belong to a specific
configuration key. Every pattern here is applied with `fullmatch`: `$` also
matches immediately before a trailing newline, so an anchored `match` would
accept a value with a newline glued to the end of it.
"""

import hashlib
import json
import re
import tomllib
import uuid
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

from hfcache.errors import CodedError, ConfigurationError, Problem
from hfcache.identity import RepositoryIdentity, parse_repository_id, parse_revision

__all__ = [
    "SCHEMA_VERSION",
    "ApplicationConfig",
    "HubConfig",
    "RepairConfig",
    "RepositoryConfig",
    "StorageConfig",
    "SyncConfig",
    "VerificationConfig",
    "load_config",
    "parse_repository_id",
    "parse_revision",
    "validate_config_mapping",
]

SCHEMA_VERSION = 1

MAXIMUM_REVISIONS = 5
"""Fixed in schema version 1 (`docs/configuration.md` §4)."""

REPAIR_GRACE_FLOOR_HOURS = 168
"""Seven days. A superseded repair instance must stay readable at least this long."""

_ACCOUNT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}")
_CREDENTIAL_NAME = re.compile(r"[A-Za-z0-9._-]{1,64}")

_SECRET_LIKE_KEYS = frozenset(
    {"token", "hf_token", "api_token", "access_token", "secret", "password"}
)


def _parse_absolute_path(value: object) -> Path:
    if not isinstance(value, str):
        message = "path must be a string"
        raise CodedError(message, code="HFCFG006")
    pure = PurePosixPath(value)
    if not pure.is_absolute():
        message = f"path {value!r} must be absolute"
        raise CodedError(message, code="HFCFG006")
    if any(part in {".", ".."} for part in pure.parts):
        message = f"path {value!r} must be normalized: no '.' or '..' segments"
        raise CodedError(message, code="HFCFG006")
    if str(pure) != value:
        message = f"path {value!r} must be normalized: expected {str(pure)!r}"
        raise CodedError(message, code="HFCFG006")
    return Path(value)


def _parse_archive_id(value: object) -> str:
    if not isinstance(value, str):
        message = "archive_id must be a string"
        raise CodedError(message, code="HFCFG012")
    try:
        parsed = uuid.UUID(value)
    except ValueError as exc:
        message = f"archive_id {value!r} is not a canonical UUID"
        raise CodedError(message, code="HFCFG012") from exc
    if str(parsed) != value:
        message = f"archive_id must be the canonical lowercase form {str(parsed)!r}"
        raise CodedError(message, code="HFCFG012")
    return value


def _parse_endpoint(value: object) -> str:
    if not isinstance(value, str):
        message = "endpoint must be a string"
        raise CodedError(message, code="HFCFG014")
    if not value.startswith("https://"):
        message = (
            f"hub.endpoint {value!r} must use https://; TLS verification is not optional "
            f"and an archive fetched over an unauthenticated channel is not worth verifying"
        )
        raise CodedError(message, code="HFCFG014")
    remainder = value.removeprefix("https://")
    if not remainder or remainder.endswith("/") or "/" in remainder or "?" in remainder:
        message = (
            f"hub.endpoint {value!r} must be scheme and host only, "
            f"with no path, query, or trailing '/'"
        )
        raise CodedError(message, code="HFCFG014")
    return value


def _parse_token_mode(value: object) -> str:
    if value not in {"disabled", "optional", "required"}:
        message = f"hub.token_mode must be 'disabled', 'optional', or 'required', not {value!r}"
        raise CodedError(message, code="HFCFG005")
    return value


def _as_tuple(value: object) -> object:
    """Accept a TOML array for a tuple field.

    Strict mode will not turn a `list` into a `tuple`, and TOML arrays decode to
    lists. The fields stay tuples rather than becoming lists because a frozen
    model with a mutable list inside is not actually immutable.
    """
    if isinstance(value, list):
        return tuple(value)
    return value


RepositoryId = Annotated[str, BeforeValidator(parse_repository_id)]
Revision = Annotated[str, BeforeValidator(parse_revision)]
AbsolutePath = Annotated[Path, BeforeValidator(_parse_absolute_path)]
ArchiveId = Annotated[str, BeforeValidator(_parse_archive_id)]
Endpoint = Annotated[str, BeforeValidator(_parse_endpoint)]
TokenMode = Annotated[
    Literal["disabled", "optional", "required"], BeforeValidator(_parse_token_mode)
]


class _Strict(BaseModel):
    """Base for every configuration model: no extra keys, no coercion, immutable."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class HubConfig(_Strict):
    """`[hub]` — where content comes from and how identity is proven."""

    endpoint: Endpoint = "https://huggingface.co"
    expected_account: str = ""
    token_mode: TokenMode = "optional"  # noqa: S105 - a mode name, not a secret
    credential_name: str = "hf-token"

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.expected_account and not _ACCOUNT.fullmatch(self.expected_account):
            message = (
                f"hub.expected_account {self.expected_account!r} is not a valid Hub account name"
            )
            raise CodedError(message, code="HFCFG005")
        if self.credential_name in {".", ".."} or not _CREDENTIAL_NAME.fullmatch(
            self.credential_name
        ):
            # '.' and '..' match the grammar but name a directory rather than a
            # credential, so they are rejected here where the error is legible
            # instead of surfacing as an unreadable credential at run time.
            message = (
                f"hub.credential_name {self.credential_name!r} must match "
                f"[A-Za-z0-9._-]{{1,64}} and name a file, not '.' or '..'"
            )
            raise CodedError(message, code="HFCFG013")
        return self


class StorageConfig(_Strict):
    """`[storage]` — where the archive lives and how much of it is kept."""

    archive_root: AbsolutePath
    archive_id: ArchiveId
    publication_mode: Literal["hardlink", "copy"] = "hardlink"
    minimum_free_space_gib: int = Field(default=100, ge=0, le=1_048_576)
    minimum_free_space_percent: int = Field(default=10, ge=0, le=100)
    maximum_revisions: int = MAXIMUM_REVISIONS

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.maximum_revisions != MAXIMUM_REVISIONS:
            message = (
                f"storage.maximum_revisions must be {MAXIMUM_REVISIONS} in schema version "
                f"{SCHEMA_VERSION}; generalizing it is a schema change with a migration"
            )
            raise CodedError(message, code="HFCFG011")
        return self


class SyncConfig(_Strict):
    """`[sync]` — how a scheduled run behaves."""

    max_workers: int = Field(default=4, ge=1, le=32)
    lock_wait_seconds: int = Field(default=3600, ge=0, le=86_400)
    continue_on_repository_error: bool = True
    dependency_policy: Literal["warn"] = "warn"
    stale_staging_age_hours: int = Field(default=24, ge=1, le=8_760)


class VerificationConfig(_Strict):
    """`[verification]` — integrity policy."""

    algorithm: Literal["sha256"] = "sha256"
    hash_new_content: bool = True
    lock_wait_seconds: int = Field(default=86_400, ge=0, le=604_800)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if not self.hash_new_content:
            message = (
                "verification.hash_new_content must be true; publishing unhashed content "
                "is not a supported mode"
            )
            raise CodedError(message, code="HFCFG005")
        return self


class RepairConfig(_Strict):
    """`[repair]` — how long a superseded instance stays readable."""

    retired_instance_grace_hours: int = Field(default=REPAIR_GRACE_FLOOR_HOURS, le=8_760)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.retired_instance_grace_hours < REPAIR_GRACE_FLOOR_HOURS:
            message = (
                f"repair.retired_instance_grace_hours must be at least "
                f"{REPAIR_GRACE_FLOOR_HOURS} (seven days); lowering the floor requires "
                f"measured consumer-copy timings and a schema-version change"
            )
            raise CodedError(message, code="HFCFG016")
        return self


class RepositoryConfig(_Strict):
    """One `[[repositories]]` entry."""

    id: RepositoryId
    type: Literal["model", "dataset"]
    revision: Revision = "main"
    enabled: bool = True
    declared_dependencies: Annotated[tuple[RepositoryId, ...], BeforeValidator(_as_tuple)] = ()

    @model_validator(mode="after")
    def _check(self) -> Self:
        seen: set[str] = set()
        for dependency in self.declared_dependencies:
            if dependency in seen:
                message = f"duplicate declared dependency {dependency!r}"
                raise CodedError(message, code="HFCFG005")
            seen.add(dependency)
        return self

    @property
    def identity(self) -> RepositoryIdentity:
        """This entry as the identity every path is built from (`hfcache.paths`)."""
        return RepositoryIdentity.from_config(self)

    @property
    def key(self) -> tuple[str, str]:
        """The uniqueness key for a configured repository."""
        return (self.type, self.id)

    @property
    def selector(self) -> str:
        """The `TYPE:ID` form used by CLI selectors (`docs/cli.md` §1.1)."""
        return f"{self.type}:{self.id}"


class ApplicationConfig(_Strict):
    """The whole configuration file."""

    schema_version: int
    hub: HubConfig = HubConfig()
    storage: StorageConfig
    sync: SyncConfig = SyncConfig()
    verification: VerificationConfig = VerificationConfig()
    repair: RepairConfig = RepairConfig()
    repositories: Annotated[tuple[RepositoryConfig, ...], BeforeValidator(_as_tuple)] = ()

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.schema_version != SCHEMA_VERSION:
            message = (
                f"unsupported schema_version {self.schema_version}; "
                f"this release understands {SCHEMA_VERSION}"
            )
            raise CodedError(message, code="HFCFG004")
        seen: set[tuple[str, str]] = set()
        for repository in self.repositories:
            if repository.key in seen:
                message = f"duplicate repository entry {repository.selector!r}"
                raise CodedError(message, code="HFCFG007")
            seen.add(repository.key)
        return self

    @property
    def enabled_repositories(self) -> tuple[RepositoryConfig, ...]:
        """Configured repositories a run would process, in configuration order."""
        return tuple(repository for repository in self.repositories if repository.enabled)

    def fingerprint(self) -> str:
        """Return the configuration fingerprint (`docs/configuration.md` §9).

        Covers everything that determines what is archived, how much is
        retained, and where it is stored. Excludes `hub.credential_name` and any
        resolved credential, so the fingerprint can be written to durable
        artifacts that are not secret.
        """
        payload = {
            "hub": {
                "endpoint": self.hub.endpoint,
                "expected_account": self.hub.expected_account,
                "token_mode": self.hub.token_mode,
            },
            "repair": self.repair.model_dump(mode="json"),
            "repositories": [
                {
                    "declared_dependencies": list(repository.declared_dependencies),
                    "enabled": repository.enabled,
                    "id": repository.id,
                    "revision": repository.revision,
                    "type": repository.type,
                }
                for repository in self.repositories
            ],
            "schema_version": self.schema_version,
            "storage": self.storage.model_dump(mode="json"),
            "sync": self.sync.model_dump(mode="json"),
            "verification": self.verification.model_dump(mode="json"),
        }
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _location(loc: tuple[int | str, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        elif parts:
            parts.append(f".{item}")
        else:
            parts.append(str(item))
    return "".join(parts) or "<root>"


def _problems_from(exc: ValidationError) -> list[Problem]:
    problems: list[Problem] = []
    for error in exc.errors():
        location = _location(error["loc"])
        original = (error.get("ctx") or {}).get("error")
        if isinstance(original, CodedError):
            code, message = original.code, str(original)
        elif error["type"] == "extra_forbidden":
            code, message = "HFCFG003", f"unknown key {location!r}"
        elif error["type"] == "missing":
            code = "HFCFG004" if location == "schema_version" else "HFCFG005"
            message = f"missing required key {location!r}"
        else:
            code, message = "HFCFG005", error["msg"]
        problems.append(Problem(code=code, message=message, location=location))
    problems.sort(key=lambda problem: (problem.location or "", problem.code))
    return problems


def _reject_literal_secrets(mapping: dict[str, Any], prefix: str = "") -> list[Problem]:
    """Refuse a token written into configuration, reporting shape not value."""
    problems: list[Problem] = []
    for key, value in mapping.items():
        location = f"{prefix}{key}"
        if key.lower() in _SECRET_LIKE_KEYS:
            problems.append(
                Problem(
                    code="HFCFG010",
                    message=(
                        f"key {location!r} looks like a literal secret; tokens are supplied "
                        f"through a systemd credential or --token-file, never in this file"
                    ),
                    location=location,
                )
            )
        if isinstance(value, dict):
            problems.extend(_reject_literal_secrets(value, prefix=f"{location}."))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    problems.extend(_reject_literal_secrets(item, prefix=f"{location}[{index}]."))
    return problems


def validate_config_mapping(mapping: dict[str, Any]) -> ApplicationConfig:
    """Validate an already-decoded TOML mapping.

    Raises `ConfigurationError` carrying every problem found, so an operator
    fixes one file once rather than one key per run.
    """
    if secrets := _reject_literal_secrets(mapping):
        raise ConfigurationError(secrets)
    try:
        return ApplicationConfig.model_validate(mapping)
    except ValidationError as exc:
        raise ConfigurationError(_problems_from(exc)) from exc


def load_config(path: Path) -> ApplicationConfig:
    """Read, decode, and fully validate a configuration file."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        message = f"configuration file {path} does not exist"
        raise ConfigurationError.single(message, code="HFCFG001", location=str(path)) from exc
    except IsADirectoryError as exc:
        message = f"configuration path {path} is a directory, not a regular file"
        raise ConfigurationError.single(message, code="HFCFG001", location=str(path)) from exc
    except OSError as exc:
        message = f"configuration file {path} is unreadable: {exc.strerror}"
        raise ConfigurationError.single(message, code="HFCFG001", location=str(path)) from exc

    try:
        mapping = tomllib.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        message = f"configuration file {path} is not valid UTF-8"
        raise ConfigurationError.single(message, code="HFCFG002", location=str(path)) from exc
    except tomllib.TOMLDecodeError as exc:
        message = f"malformed TOML in {path}: {exc}"
        raise ConfigurationError.single(message, code="HFCFG002", location=str(path)) from exc

    return validate_config_mapping(mapping)
