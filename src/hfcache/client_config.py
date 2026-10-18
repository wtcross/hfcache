"""Independent strict reader settings and explicit API credentials (decision 118)."""

import contextlib
import ipaddress
import math
import os
import re
import stat
import tomllib
from pathlib import Path
from typing import Annotated, Self
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

from hfcache.api.auth import read_protected_token
from hfcache.errors import ConfigurationError

DEFAULT_CLIENT_CONFIG = Path("/etc/hfcache/client.toml")
DEFAULT_API_SOCKET = Path("/run/hfcache/api.sock")
MAX_CLIENT_CONFIG_BYTES = 1024 * 1024
_MAX_LOCATION_BYTES = 4096
_NAME = re.compile(r"[A-Za-z0-9_.-]{1,128}")
_PREFIX = re.compile(r"(?:/[A-Za-z0-9_-]+)*")


def _invalid() -> ConfigurationError:
    return ConfigurationError.single(
        "Invalid API client configuration or selection", code="HFAPI017"
    )


def _version(value: object) -> int:
    if type(value) is not int or value != 1:
        msg = "schema_version must be integer 1"
        raise ValueError(msg)
    return value


def _path(value: object) -> Path:
    if not isinstance(value, str | Path):
        msg = "path must be absolute"
        raise ValueError(msg)  # noqa: TRY004 - Pydantic validator
    text = str(value)
    if (
        not text.startswith("/")
        or any(part in {".", ".."} for part in text.split("/"))
        or "\\" in text
        or len(text.encode("utf-8")) > _MAX_LOCATION_BYTES
        or any(not character.isprintable() for character in text)
    ):
        msg = "path must be absolute without escaping components"
        raise ValueError(msg)
    return Path(text)


def _url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        msg = "invalid API URL"
        raise ValueError(msg) from None
    if (
        value != value.strip()
        or len(value) > _MAX_LOCATION_BYTES
        or any(not character.isprintable() or character.isspace() for character in value)
        or "\\" in value
        or parsed.scheme not in {"https", "http"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.netloc.endswith(":")
        or "?" in value
        or "#" in value
        or (port is not None and port == 0)
        or not _PREFIX.fullmatch(parsed.path.rstrip("/"))
    ):
        msg = "API URL must be a safe origin with an optional path prefix"
        raise ValueError(msg)
    if parsed.scheme == "http":
        loopback = parsed.hostname.lower() == "localhost"
        with contextlib.suppress(ValueError):
            loopback = loopback or ipaddress.ip_address(parsed.hostname).is_loopback
        if not loopback:
            msg = "remote API URL requires verified HTTPS"
            raise ValueError(msg)
    return value.rstrip("/")


AbsolutePath = Annotated[Path, BeforeValidator(_path)]


class ClientConfig(BaseModel):
    """No archive configuration, Hub credential, or filesystem discovery."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)

    schema_version: Annotated[int, BeforeValidator(_version)]
    api_url: str | None = None
    api_socket: AbsolutePath | None = None
    api_token_file: AbsolutePath | None = None
    credential_name: str = "hfcache.api"
    expected_archive_id: str | None = None
    ca_file: AbsolutePath | None = None
    connect_timeout: float = Field(default=5.0, gt=0, le=300)
    read_timeout: float = Field(default=30.0, gt=0, le=3600)
    read_retries: int = Field(default=2, ge=0, le=5)
    poll_interval: float = Field(default=0.2, gt=0, le=60)
    wait_timeout: float = Field(default=300.0, gt=0, le=86400)
    max_response_bytes: int = Field(default=16 * 1024 * 1024, ge=1024, le=64 * 1024 * 1024)
    max_pages: int = Field(default=10000, ge=1, le=10000)

    @model_validator(mode="after")
    def boundary(self) -> Self:
        if self.api_url is not None and self.api_socket is not None:
            msg = "API URL and socket are mutually exclusive"
            raise ValueError(msg)
        if self.api_url is not None:
            object.__setattr__(self, "api_url", _url(self.api_url))
        if not _NAME.fullmatch(self.credential_name) or self.credential_name in {".", ".."}:
            msg = "invalid named API credential"
            raise ValueError(msg)
        if self.expected_archive_id is not None:
            try:
                canonical = str(UUID(self.expected_archive_id))
            except ValueError:
                msg = "expected archive identity must be a canonical UUID"
                raise ValueError(msg) from None
            if canonical != self.expected_archive_id:
                msg = "expected archive identity must be a canonical UUID"
                raise ValueError(msg)
        if any(
            not math.isfinite(number)
            for number in (
                self.connect_timeout,
                self.read_timeout,
                self.poll_interval,
                self.wait_timeout,
            )
        ):
            msg = "client timing bounds must be finite"
            raise ValueError(msg)
        return self

    @property
    def url(self) -> str:
        return self.api_url or "http://localhost"

    @property
    def socket(self) -> Path | None:
        return (
            self.api_socket if self.api_url is not None else (self.api_socket or DEFAULT_API_SOCKET)
        )


def _read_config(path: Path) -> dict[str, object]:
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_CLIENT_CONFIG_BYTES:
            raise _invalid()
        raw = bytearray()
        while len(raw) <= MAX_CLIENT_CONFIG_BYTES:
            part = os.read(descriptor, min(65536, MAX_CLIENT_CONFIG_BYTES + 1 - len(raw)))
            if not part:
                break
            raw.extend(part)
        after = os.fstat(descriptor)
        stable_fields = (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_uid",
            "st_gid",
            "st_nlink",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
        if (
            any(getattr(before, name) != getattr(after, name) for name in stable_fields)
            or len(raw) != before.st_size
            or len(raw) > MAX_CLIENT_CONFIG_BYTES
        ):
            raise _invalid()
        return tomllib.loads(raw.decode("utf-8"))
    except OSError, UnicodeError, tomllib.TOMLDecodeError:
        raise _invalid() from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def resolve_client_config(
    path: Path | None = None,
    *,
    api_url: str | None = None,
    api_socket: Path | None = None,
    api_token_file: Path | None = None,
) -> ClientConfig:
    """Explicit endpoint choices replace the entire configured endpoint group."""
    if api_url is not None and api_socket is not None:
        raise _invalid()
    values: dict[str, object]
    try:
        selected = _path(path if path is not None else DEFAULT_CLIENT_CONFIG)
        # Missing default settings permit the documented local socket default;
        # any explicit or installed unusable source is a configuration error.
        if path is not None:
            values = _read_config(selected)
        else:
            try:
                selected.lstat()
            except FileNotFoundError:
                values = {"schema_version": 1}
            else:
                values = _read_config(selected)
        if api_url is not None or api_socket is not None:
            values |= {"api_url": api_url, "api_socket": api_socket}
        if api_token_file is not None:
            values["api_token_file"] = api_token_file
        config = ClientConfig.model_validate(values)
        if config.api_url is None and config.api_socket is None:
            config = config.model_copy(update={"api_socket": DEFAULT_API_SOCKET})
    except OSError, ValueError, ValidationError:
        raise _invalid() from None
    return config


def resolve_api_token(config: ClientConfig) -> str:
    """Load only the selected API source; never inspect Hub or ambient tokens."""
    if config.api_token_file is not None:
        return read_protected_token(config.api_token_file)
    directory = os.environ.get("CREDENTIALS_DIRECTORY")
    if not directory:
        message = "Named API credential is unavailable or unsafe"
        raise ConfigurationError.single(message, code="HFAPI003")
    try:
        source = _path(directory) / config.credential_name
    except ValueError:
        msg = "Named API credential is unavailable or unsafe"
        raise ConfigurationError.single(msg, code="HFAPI003") from None
    return read_protected_token(source)
