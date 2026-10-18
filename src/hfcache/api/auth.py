"""Explicit API bearer capabilities, without framework or Hub authentication.

Descriptor-pinned credential loading and bounded fixed-size comparisons enforce
INV-002/013, plan §3.4 and decision 112. No application or endpoint is created.
"""

import hashlib
import hmac
import os
import re
import stat
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from hfcache.errors import AuthenticationError, AuthorizationError, ConfigurationError
from hfcache.redaction import register_secret

if TYPE_CHECKING:
    from collections.abc import Mapping

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


@dataclass(frozen=True, slots=True)
class Principal:
    """A credential class, never a token or token-derived receipt identifier."""

    credential_class: CredentialClass

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


def _metadata(status: os.stat_result) -> tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def read_protected_token(path: Path) -> str:  # noqa: PLR0912 - one descriptor validation boundary
    """Read one bounded protected inode, rejecting symlink components and races.

    Parent directories are opened relative to pinned descriptors. Reading never
    reopens a checked pathname, and concurrent content/ownership/mode changes
    are refused by the second descriptor metadata snapshot (INV-002).
    """
    if (
        not path.is_absolute()
        or ".." in path.parts
        or "\\" in str(path)
        or any(not character.isprintable() for character in str(path))
    ):
        raise _invalid_credential()
    directory = -1
    descriptor = -1
    try:
        directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        for component in path.parts[1:-1]:
            child = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        descriptor = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=directory,
        )
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid not in {0, os.geteuid()}
            or stat.S_IMODE(before.st_mode) not in {0o400, 0o440, 0o600, 0o640}
            or (
                before.st_mode & stat.S_IRGRP
                and before.st_gid not in {os.getegid(), *os.getgroups()}
            )
            or before.st_nlink != 1
            or not 0 < before.st_size <= MAXIMUM_TOKEN_FILE_BYTES
        ):
            raise _invalid_credential()
        raw = bytearray()
        while len(raw) <= MAXIMUM_TOKEN_FILE_BYTES:
            part = os.read(descriptor, MAXIMUM_TOKEN_FILE_BYTES + 1 - len(raw))
            if not part:
                break
            raw.extend(part)
        after = os.fstat(descriptor)
        if _metadata(before) != _metadata(after) or len(raw) != before.st_size:
            raise _invalid_credential()
    except OSError:
        raise _invalid_credential() from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if directory >= 0:
            os.close(directory)
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
    if source.file is not None:
        return source.file
    directory = environ.get("CREDENTIALS_DIRECTORY", "")
    if not directory or not Path(directory).is_absolute() or source.systemd_name is None:
        raise _invalid_credential()
    return Path(directory) / source.systemd_name


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
