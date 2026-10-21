"""Independent strict UI artifact/bootstrap schema1 (decision147).

These pure authorities carry configured identity, never observed archive health.
HTML placement and protected filesystem capture remain separate context checks.
"""

import re
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import AnyHttpUrl, BeforeValidator, ConfigDict, Field, model_validator

from hfcache.models import ArchiveIdField, CommitShaField, DurableModel, Sha256, as_tuple
from hfcache.url_paths import uri_path

MAX_PREFIX_BYTES = 1024
MAX_ORIGIN_BYTES = 4096
MAX_PATH_DEPTH = 8
MAX_COMPONENT_BYTES = 255
MAX_TOTAL_BYTES = 67108864
ASCII_SPACE = 32
ASCII_TILDE = 126


def _ascii(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(not ASCII_SPACE <= ord(c) <= ASCII_TILDE for c in value)
    ):
        message = "value must be nonempty printable ASCII"
        raise ValueError(message)
    return value


def _one(value: object) -> int:
    if type(value) is not int or value != 1:
        message = "UI contract version must be integer1"
        raise ValueError(message)
    return value


def _prefix(value: object) -> str:
    if not isinstance(value, str):
        message = "UI prefix must be text"
        raise ValueError(message)  # noqa: TRY004 - Pydantic collects ValueError
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        message = "UI prefix must be valid Unicode"
        raise ValueError(message) from None
    if size > MAX_PREFIX_BYTES or (
        value
        and (
            not value.startswith("/")
            or value.startswith("//")
            or value.endswith("/")
            or str(PurePosixPath(value)) != value
            or ".." in PurePosixPath(value).parts
            or any(c in value for c in "?#\\%")
            or any(c.isspace() for c in value)
            or not value.isprintable()
        )
    ):
        message = "UI prefix must be a bounded canonical application prefix"
        raise ValueError(message)
    return value


def _origin(value: object) -> str:
    text = _ascii(value)
    try:
        parsed = urlsplit(text)
        canonical = str(AnyHttpUrl(text)).removesuffix("/")
    except ValueError:
        message = "UI origin must be canonical HTTPS"
        raise ValueError(message) from None
    if (
        len(text) > MAX_ORIGIN_BYTES
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or canonical != text
    ):
        message = "UI origin must be canonical HTTPS"
        raise ValueError(message)
    return text


def _subject(value: object) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value) is None
    ):
        message = "UI subject must be the stable bounded administrator identity"
        raise ValueError(message)
    return value


def _instance(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{32}", value) is None:
        message = "UI instance identity must be32 lowercase hex characters"
        raise ValueError(message)
    return value


def _asset_path(value: object) -> str:
    text = _ascii(value)
    parts = text.split("/")
    if (
        len(text) > MAX_PREFIX_BYTES
        or len(parts) > MAX_PATH_DEPTH
        or any(
            len(part) > MAX_COMPONENT_BYTES
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", part) is None
            or part in {".", ".."}
            for part in parts
        )
    ):
        message = "UI member path must be a bounded canonical relative ASCII path"
        raise ValueError(message)
    return text


SchemaOne = Annotated[Literal[1], BeforeValidator(_one)]
Ascii128 = Annotated[str, BeforeValidator(_ascii), Field(max_length=128)]
Ascii64 = Annotated[str, BeforeValidator(_ascii), Field(max_length=64)]
Prefix = Annotated[str, BeforeValidator(_prefix)]
EncodedPath = Annotated[str, BeforeValidator(_ascii)]
Capability = Literal["config-read", "config-write", "host-read", "observer-stop", "schedule-write"]
CAPABILITIES = ("config-read", "config-write", "host-read", "observer-stop", "schedule-write")


class UiModel(DurableModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)


class UiToolchain(UiModel):
    node: Ascii64
    pnpm: Ascii64
    typescript: Ascii64
    vite: Ascii64


class UiBuildMetadata(UiModel):
    application_version: Ascii128
    source_commit: CommitShaField
    source_snapshot_sha256: Sha256
    source_dirty: bool
    ui_contract_version: SchemaOne
    rest_api_schema_version: SchemaOne
    wire_source_digest: Sha256
    pnpm_lock_sha256: Sha256
    toolchain: UiToolchain
    toolchain_sha256: Sha256
    licenses_sha256: Sha256
    notices_sha256: Sha256


class UiHtmlMetaIdentity(UiModel):
    ui_base: Literal["__HFCACHE_UI_BASE_V1__"]
    bootstrap_path: Literal["__HFCACHE_UI_BOOTSTRAP_V1__"]
    asset_fingerprint: Literal["__HFCACHE_UI_FINGERPRINT_V1__"]
    ui_contract: Literal["__HFCACHE_UI_CONTRACT_V1__"]


class UiAssetMember(UiModel):
    path: Annotated[str, BeforeValidator(_asset_path)]
    bytes: Annotated[int, Field(ge=0, le=8388608)]
    sha256: Sha256
    mime: Literal[
        "text/html",
        "text/css",
        "text/javascript",
        "application/json",
        "image/png",
        "image/webp",
        "font/woff2",
        "text/plain",
    ]

    @model_validator(mode="after")
    def _member(self) -> Self:
        types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "text/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".webp": "image/webp",
            ".woff2": "font/woff2",
        }
        if self.path == "THIRD_PARTY_NOTICES.txt":
            valid = self.mime == "text/plain"
        else:
            valid = types.get(PurePosixPath(self.path).suffix) == self.mime
        if (
            not valid
            or (self.mime == "text/html" and self.path != "index.html")
            or (
                self.path not in {"index.html", "licenses.json", "THIRD_PARTY_NOTICES.txt"}
                and not self.path.startswith("assets/")
            )
            or (self.path == "index.html" and self.bytes == 0)
        ):
            message = "UI member location, size and MIME must agree"
            raise ValueError(message)
        return self


class UiAssetManifest(UiModel):
    schema_version: SchemaOne
    kind: Literal["hfcache_web_assets"]
    build: UiBuildMetadata
    entrypoint: Literal["index.html"]
    meta_identity: UiHtmlMetaIdentity
    members: Annotated[
        tuple[UiAssetMember, ...], BeforeValidator(as_tuple), Field(min_length=1, max_length=4096)
    ]

    @model_validator(mode="after")
    def _members(self) -> Self:
        paths = tuple(member.path for member in self.members)
        records = {member.path: member for member in self.members}
        if (
            paths != tuple(sorted(set(paths)))
            or not {"index.html", "licenses.json", "THIRD_PARTY_NOTICES.txt"} <= records.keys()
            or sum(member.bytes for member in self.members) > MAX_TOTAL_BYTES
            or records["licenses.json"].sha256 != self.build.licenses_sha256
            or records["THIRD_PARTY_NOTICES.txt"].sha256 != self.build.notices_sha256
        ):
            message = "UI manifest members must be complete, sorted, unique and build-bound"
            raise ValueError(message)
        return self


class UiPaths(UiModel):
    public_prefix: Prefix
    effective_prefix: Prefix
    ui_base: Annotated[EncodedPath, Field(max_length=3076)]
    bootstrap: Annotated[EncodedPath, Field(max_length=3090)]
    api_base: Annotated[EncodedPath, Field(max_length=3079)]
    mcp_base: Annotated[EncodedPath, Field(max_length=3077)] | None

    @model_validator(mode="after")
    def _paths(self) -> Self:
        prefix = self.effective_prefix
        if (
            self.effective_prefix not in {self.public_prefix, ""}
            or self.ui_base != uri_path(prefix + "/ui/")
            or self.bootstrap != uri_path(prefix + "/ui/bootstrap.json")
            or self.api_base != uri_path(prefix + "/api/v1")
            or self.mcp_base not in {None, uri_path(prefix + "/mcp/")}
        ):
            message = "UI paths must bind the trusted prefix to fixed endpoints"
            raise ValueError(message)
        return self


class UiAdminPermission(UiModel):
    capability: Capability
    granted: bool
    effective: bool
    reason: Literal["allowed", "not_granted", "feature_unavailable"]

    @model_validator(mode="after")
    def _permission(self) -> Self:
        expected = (
            "allowed"
            if self.effective
            else "feature_unavailable"
            if self.granted
            else "not_granted"
        )
        if (self.effective and not self.granted) or self.reason != expected:
            message = "UI permission reason must agree with grant and availability"
            raise ValueError(message)
        return self


class UiUser(UiModel):
    subject: Annotated[str, BeforeValidator(_subject)]
    display_name: Annotated[str, BeforeValidator(_subject)]
    authentication_method: Literal["basic"]
    credential_class: Literal["rest-writer"]
    rest_capabilities: Annotated[
        tuple[Literal["read", "write"], ...],
        BeforeValidator(as_tuple),
        Field(min_length=2, max_length=2),
    ]
    admin_permissions: Annotated[
        tuple[UiAdminPermission, ...], BeforeValidator(as_tuple), Field(min_length=5, max_length=5)
    ]

    @model_validator(mode="after")
    def _user(self) -> Self:
        if (
            self.display_name != self.subject
            or self.rest_capabilities != ("read", "write")
            or tuple(item.capability for item in self.admin_permissions) != CAPABILITIES
        ):
            message = "UI user projection must preserve exact principal and capability identity"
            raise ValueError(message)
        return self


class UiBuildIdentity(UiModel):
    asset_manifest_sha256: Sha256
    metadata: UiBuildMetadata


class UiBootstrap(UiModel):
    schema_version: SchemaOne
    kind: Literal["hfcache_ui_bootstrap"]
    ui_contract_version: SchemaOne
    rest_api_schema_version: SchemaOne
    wire_source_digest: Sha256
    instance_id: Annotated[str, BeforeValidator(_instance)]
    authority_epoch: Annotated[str, BeforeValidator(_instance)]
    configured_archive_id: ArchiveIdField
    archive_identity_source: Literal["installed_policy"]
    config_fingerprint: None
    configured_origin: Annotated[str, BeforeValidator(_origin)]
    paths: UiPaths
    user: UiUser
    build: UiBuildIdentity

    @model_validator(mode="after")
    def _bootstrap(self) -> Self:
        if (
            self.authority_epoch != self.instance_id
            or self.wire_source_digest != self.build.metadata.wire_source_digest
            or self.ui_contract_version != self.build.metadata.ui_contract_version
            or self.rest_api_schema_version != self.build.metadata.rest_api_schema_version
        ):
            message = "UI bootstrap authority and contract identities must agree"
            raise ValueError(message)
        return self
