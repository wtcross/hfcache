"""Explicit API bearer capabilities, without framework or Hub authentication.

Descriptor-pinned credential loading and bounded fixed-size comparisons enforce
INV-002/013, docs/server.md bearer configuration and decision 112. No application or endpoint is
created.
"""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

from hfcache.api.credential_sources import read_protected_bytes, source_path
from hfcache.errors import AuthenticationError, AuthorizationError, ConfigurationError
from hfcache.redaction import register_secret

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from hfcache.server_config import CredentialSource, ServerConfig

MINIMUM_TOKEN_BYTES = 32
MAXIMUM_TOKEN_BYTES = 4096
MAXIMUM_TOKEN_FILE_BYTES = MAXIMUM_TOKEN_BYTES + 1
_TOKEN = re.compile(r"[A-Za-z0-9._~+/-]+={0,2}")
_DUMMY_DIGEST = bytes(hashlib.sha256().digest_size)


class CredentialClass(StrEnum):
    REST_WRITER = "rest-writer"
    REST_READER = "rest-reader"
    MCP_READER = "mcp-reader"


class Capability(StrEnum):
    READ = "read"
    WRITE = "write"
    MCP_READ = "mcp-read"


class AuthenticationMethod(StrEnum):
    BEARER = "bearer"
    BASIC = "basic"


class AdminCapability(StrEnum):
    CONFIG_READ = "config-read"
    CONFIG_WRITE = "config-write"
    HOST_READ = "host-read"
    SCHEDULE_WRITE = "schedule-write"
    OBSERVER_STOP = "observer-stop"


@dataclass(frozen=True, slots=True)
class Principal:
    """A credential class, never a token or token-derived receipt identifier."""

    credential_class: CredentialClass
    authentication_method: AuthenticationMethod = field(
        default=AuthenticationMethod.BEARER, kw_only=True
    )
    subject: str | None = field(default=None, kw_only=True)
    admin_capabilities: frozenset[AdminCapability] = field(default_factory=frozenset, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.credential_class, CredentialClass) or not isinstance(
            self.authentication_method, AuthenticationMethod
        ):
            message = "principal identity must use the internal credential and authentication enums"
            raise TypeError(message)
        if not isinstance(self.admin_capabilities, frozenset) or any(
            not isinstance(value, AdminCapability) for value in self.admin_capabilities
        ):
            message = "administrative grants must be a frozen internal capability set"
            raise ValueError(message)
        if self.authentication_method is AuthenticationMethod.BEARER:
            label = "credential-class:" + self.credential_class.value
            if self.admin_capabilities or self.subject not in {None, label}:
                message = "bearer principals carry the legacy class identity without admin grants"
                raise ValueError(message)
            object.__setattr__(self, "subject", label)
        elif (
            self.credential_class is not CredentialClass.REST_WRITER
            or not isinstance(self.subject, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", self.subject)
        ):
            message = "Basic principals require one stable administrator subject"
            raise ValueError(message)

    @property
    def capabilities(self) -> frozenset[Capability]:
        return {
            CredentialClass.REST_WRITER: frozenset({Capability.READ, Capability.WRITE}),
            CredentialClass.REST_READER: frozenset({Capability.READ}),
            CredentialClass.MCP_READER: frozenset({Capability.MCP_READ}),
        }[self.credential_class]


def _invalid_credential() -> ConfigurationError:
    return ConfigurationError.single(
        "API credential source is missing, unsafe, changed while reading or malformed",
        code="HFAPI003",
    )


def read_protected_token(path: Path) -> str:
    """Read one bounded protected inode, rejecting symlink components and races.

    Parent directories are opened relative to pinned descriptors. Reading never
    reopens a checked pathname, and concurrent content/ownership/mode changes
    are refused by the second descriptor metadata snapshot (INV-002).
    """
    raw = read_protected_bytes(path, MAXIMUM_TOKEN_FILE_BYTES)
    try:
        secret = raw.decode("ascii").removesuffix("\n")
    except UnicodeDecodeError:
        raise _invalid_credential() from None
    if secret:
        register_secret(secret)
    if (
        not MINIMUM_TOKEN_BYTES <= len(secret) <= MAXIMUM_TOKEN_BYTES
        or not _TOKEN.fullmatch(secret)
        or secret.startswith("hf_")
    ):
        raise _invalid_credential()
    return secret


def _source_path(source: CredentialSource, environ: Mapping[str, str]) -> Path:
    return source_path(source, environ)


@dataclass(frozen=True, slots=True)
class CredentialRegistry:
    """Startup-only fixed capability slots; secret values are not retained here."""

    _digests: tuple[tuple[CredentialClass, bytes], ...] = field(repr=False)

    def authenticate(
        self, authorization: str | None, *, interface: Literal["rest", "mcp"] = "rest"
    ) -> Principal:
        return authenticate_bearer(self, authorization, interface=interface)


def load_credentials(
    server: ServerConfig, *, environ: Mapping[str, str] | None = None
) -> CredentialRegistry:
    """Load configured classes once; optional unconfigured classes authorize nobody."""
    environment = os.environ if environ is None else environ
    digests = []
    for credential_class, source in (
        (CredentialClass.REST_WRITER, server.credentials.writer),
        (CredentialClass.REST_READER, server.credentials.reader),
        (
            CredentialClass.MCP_READER,
            server.credentials.mcp_reader if server.mcp_enabled else None,
        ),
    ):
        if source is None:
            continue
        secret = read_protected_token(_source_path(source, environment))
        digest = hashlib.sha256(secret.encode("ascii")).digest()
        if any(hmac.compare_digest(digest, previous) for _, previous in digests):
            message = "API credential classes must have distinct secrets"
            raise ConfigurationError.single(message, code="HFAPI004")
        digests.append((credential_class, digest))
    return CredentialRegistry(tuple(digests))


def authenticate_bearer(
    registry: CredentialRegistry,
    authorization: str | None,
    *,
    interface: Literal["rest", "mcp"] = "rest",
) -> Principal:
    """Return a principal or the same 401 for absent, malformed or wrong-class input."""
    if (
        interface not in {"rest", "mcp"}
        or authorization is None
        or len(authorization) > MAXIMUM_TOKEN_BYTES + len("Bearer ")
    ):
        raise AuthenticationError
    scheme, separator, token = authorization.partition(" ")
    if (
        scheme.lower() != "bearer"
        or separator != " "
        or not MINIMUM_TOKEN_BYTES <= len(token) <= MAXIMUM_TOKEN_BYTES
        or not _TOKEN.fullmatch(token)
    ):
        raise AuthenticationError
    digest = hashlib.sha256(token.encode("ascii")).digest()
    match = None
    for credential_class in CredentialClass:
        expected = next(
            (value for kind, value in registry._digests if kind == credential_class),  # noqa: SLF001 - same-module verifier
            _DUMMY_DIGEST,
        )
        accepted = hmac.compare_digest(digest, expected)
        if accepted:
            match = credential_class
    if match is None or (interface == "rest") == (match is CredentialClass.MCP_READER):
        raise AuthenticationError
    return Principal(match)


def require_capability(principal: Principal, capability: Capability) -> Principal:
    if capability not in principal.capabilities:
        raise AuthorizationError
    return principal


def require_admin_capability(principal: Principal, capability: AdminCapability) -> Principal:
    """Internal application grant; never widen the strict legacy wire vocabulary."""
    if capability not in principal.admin_capabilities:
        raise AuthorizationError
    return principal
