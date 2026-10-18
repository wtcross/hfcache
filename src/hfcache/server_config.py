"""Strict restart-only server policy and freshly loaded archive snapshots.

`docs/server.md`, plan §3 and decision 112 separate transport/auth authority
from archive policy. This module neither starts a listener nor resolves secrets.
"""

import ipaddress
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, NoReturn, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

from hfcache.config import ApplicationConfig, load_config
from hfcache.errors import ConfigurationError, Problem

_CREDENTIAL_NAME = re.compile(r"[A-Za-z0-9._-]{1,64}")
_HOST = re.compile(r"(?:[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?|\[[0-9a-fA-F:]+\])")


def _invalid(message: str) -> NoReturn:
    raise ValueError(message) from None


def _path(value: object) -> Path:
    if not isinstance(value, str):
        _invalid("path must be an absolute normalized string")
    pure = PurePosixPath(value)
    if (
        not pure.is_absolute()
        or str(pure) != value
        or ".." in pure.parts
        or value == "/"
        or "\\" in value
        or any(not character.isprintable() for character in value)
    ):
        _invalid("path must be absolute, normalized and below the filesystem root")
    return Path(value)


def _array(value: object) -> object:
    return tuple(value) if isinstance(value, list) else value


def _schema(value: object) -> int:
    if type(value) is not int or value != 1:
        _invalid("schema_version must be integer 1")
    return value


def _socket_mode(value: object) -> int:
    if type(value) is not int:
        _invalid("socket_mode must be an integer POSIX mode")
    return value


AbsolutePath = Annotated[Path, BeforeValidator(_path)]
StringArray = Annotated[tuple[str, ...], BeforeValidator(_array)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)


class CredentialSource(_Strict):
    """One explicit source, never a literal secret or ambient Hub discovery."""

    file: AbsolutePath | None = None
    systemd_name: str | None = None

    @model_validator(mode="after")
    def one_source(self) -> Self:
        if (self.file is None) == (self.systemd_name is None):
            _invalid("credential source requires exactly one file or systemd_name")
        if self.systemd_name is not None and (
            not _CREDENTIAL_NAME.fullmatch(self.systemd_name) or self.systemd_name in {".", ".."}
        ):
            _invalid("systemd credential name has invalid grammar")
        return self


class ServerCredentials(_Strict):
    writer: CredentialSource
    reader: CredentialSource | None = None
    mcp_reader: CredentialSource | None = None


class TLSConfig(_Strict):
    certificate: AbsolutePath
    private_key: AbsolutePath


class ListenerConfig(_Strict):
    unix_enabled: bool = True
    unix_socket: AbsolutePath = Path("/run/hfcache/api.sock")
    socket_mode: Annotated[Literal[0o600, 0o660], BeforeValidator(_socket_mode)] = 0o660
    tcp_enabled: bool = True
    tcp_host: str = "127.0.0.1"
    tcp_port: int = Field(default=8787, ge=1, le=65535)
    tls: TLSConfig | None = None
    proxy_tls: bool = False
    allowed_hosts: StringArray = ("localhost", "127.0.0.1", "[::1]")
    allowed_origins: StringArray = ()
    trusted_proxies: StringArray = ()
    root_path: str = ""

    @model_validator(mode="after")
    def exposure_policy(self) -> Self:  # noqa: PLR0912 - coupled listener safety policy
        strings = (
            *self.allowed_hosts,
            *self.allowed_origins,
            *self.trusted_proxies,
            self.root_path,
            self.tcp_host,
        )
        if any(not character.isprintable() for value in strings for character in value):
            _invalid("listener strings cannot contain control characters")
        if not self.unix_enabled and not self.tcp_enabled:
            _invalid("at least one Unix or TCP listener must be configured")
        if not self.allowed_hosts or len(set(self.allowed_hosts)) != len(self.allowed_hosts):
            _invalid("allowed_hosts must contain distinct explicit host names")
        if any(not _HOST.fullmatch(host) for host in self.allowed_hosts):
            _invalid("allowed_hosts must contain host names without wildcard, port or URL")
        for origin in self.allowed_origins:
            parsed = urlsplit(origin)
            try:
                port = parsed.port
            except ValueError:
                _invalid("allowed_origins contains an invalid port")
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
                or (port is not None and port < 1)
                or "*" in origin
                or any(character.isspace() for character in origin)
            ):
                _invalid("allowed_origins must be exact HTTP(S) origins without userinfo")
        for proxy in self.trusted_proxies:
            try:
                network = ipaddress.ip_network(proxy, strict=True)
            except ValueError:
                _invalid("trusted_proxies must contain explicit IP addresses or networks")
            if network.prefixlen == 0:
                _invalid("trusted_proxies cannot trust every address")
        if self.root_path and (
            not self.root_path.startswith("/")
            or self.root_path.endswith("/")
            or str(PurePosixPath(self.root_path)) != self.root_path
            or ".." in PurePosixPath(self.root_path).parts
            or any(character in self.root_path for character in "?#\\%")
            or any(character.isspace() for character in self.root_path)
        ):
            _invalid("root_path must be empty or a normalized absolute URL path prefix")
        loopback = True
        try:
            loopback = ipaddress.ip_address(self.tcp_host).is_loopback
        except ValueError:
            _invalid("tcp_host must be an explicit IP address")
        if self.proxy_tls and (
            not self.tcp_enabled or not loopback or not self.trusted_proxies or self.tls is not None
        ):
            _invalid("proxy_tls requires loopback TCP, explicit trusted proxies and no direct TLS")
        if not loopback and self.tls is None:
            _invalid("off-host TCP requires direct TLS; a TLS proxy must connect over loopback")
        return self

    @property
    def unix_address(self) -> Path | None:
        """Effective Unix listener, disabled explicitly rather than with a path sentinel."""
        return self.unix_socket if self.unix_enabled else None

    @property
    def tcp_address(self) -> tuple[str, int] | None:
        """Effective TCP address; binding remains the server's API-006 responsibility."""
        return (self.tcp_host, self.tcp_port) if self.tcp_enabled else None


class ServerLimits(_Strict):
    max_request_bytes: int = Field(default=1048576, ge=1024, le=16777216)
    max_page_size: int = Field(default=1000, ge=1, le=10000)
    metadata_workers: int = Field(default=4, ge=1, le=32)
    metadata_queue: int = Field(default=32, ge=1, le=1024)
    max_queued_operations: int = Field(default=16, ge=0, le=64)
    retained_terminal_operations: int = Field(default=1000, ge=1, le=100000)
    shutdown_timeout_seconds: int = Field(default=300, ge=1, le=86400)
    max_response_bytes: int = Field(default=8388608, ge=1024, le=67108864)
    max_artifact_bytes: int = Field(default=67108864, ge=1024, le=1073741824)
    max_scan_entries: int = Field(default=10000, ge=10, le=1000000)
    operation_max_receipt_bytes: int = Field(default=1048576, ge=4096, le=16777216)
    operation_max_result_bytes: int = Field(default=8388608, ge=1024, le=67108864)
    operation_max_events: int = Field(default=256, ge=1, le=10000)
    operation_max_event_bytes: int = Field(default=2048, ge=256, le=65536)
    operation_max_store_bytes: int = Field(default=268435456, ge=1048576, le=17179869184)
    operation_retention_days: int = Field(default=30, ge=1, le=36500)


class ServerConfig(_Strict):
    schema_version: Annotated[Literal[1], BeforeValidator(_schema)]
    archive_config: AbsolutePath = Path("/etc/hfcache/config.toml")
    state_directory: AbsolutePath = Path("/var/lib/hfcache/api")
    credentials: ServerCredentials
    listener: ListenerConfig = Field(default_factory=ListenerConfig)
    limits: ServerLimits = Field(default_factory=ServerLimits)
    maintenance_enabled: bool = False
    interactive_docs: bool = False
    mcp_enabled: bool = False
    log_level: Literal["debug", "info", "warning", "error"] = "info"

    @model_validator(mode="after")
    def mcp_requires_credential(self) -> Self:
        if self.mcp_enabled and self.credentials.mcp_reader is None:
            _invalid("mcp_enabled requires a distinct mcp_reader credential source")
        return self


def validate_server_config_mapping(mapping: dict[str, Any]) -> ServerConfig:
    """Validate without copying secret-like input values into diagnostic output."""
    try:
        return ServerConfig.model_validate(mapping)
    except ValidationError as exc:
        problems = []
        for error in exc.errors(include_input=False, include_context=False):
            # Even unknown key names are untrusted. Diagnostics identify a known
            # schema location only, never echo caller-selected values/keys.
            location = ".".join(str(item) for item in error["loc"] if isinstance(item, int))
            code = "HFCFG003" if error["type"] == "extra_forbidden" else "HFCFG005"
            if error["loc"] == ("schema_version",):
                code = "HFCFG004"
            problems.append(
                Problem(code, "invalid server configuration field", location=location or None)
            )
        raise ConfigurationError(problems) from None


def load_server_config(path: Path) -> ServerConfig:
    """Load an operator-owned TOML file; syntax errors never echo source text."""
    try:
        raw = path.read_bytes()
    except OSError:
        message = "server configuration is missing or unreadable"
        raise ConfigurationError.single(message, code="HFCFG001") from None
    try:
        mapping = tomllib.loads(raw.decode("utf-8"))
    except UnicodeDecodeError, tomllib.TOMLDecodeError:
        message = "server configuration is not valid UTF-8 TOML"
        raise ConfigurationError.single(message, code="HFCFG002") from None
    return validate_server_config_mapping(mapping)


@dataclass(frozen=True, slots=True)
class PolicySnapshot:
    """One immutable installed archive policy; safe for admission evidence."""

    config: ApplicationConfig
    fingerprint: str


@dataclass(frozen=True, slots=True)
class InstalledPolicy:
    """Reload per admission, while retaining the startup storage authority."""

    path: Path
    root: Path
    archive_id: str

    @classmethod
    def open(cls, server: ServerConfig) -> Self:
        policy = load_config(server.archive_config)
        return cls(server.archive_config, policy.storage.archive_root, policy.storage.archive_id)

    def snapshot(self) -> PolicySnapshot:
        config = load_config(self.path)
        if config.storage.archive_root != self.root or config.storage.archive_id != self.archive_id:
            message = "archive root or UUID changed; restart the server before new archive work"
            raise ConfigurationError.single(message, code="HFCFG005")
        return PolicySnapshot(config, config.fingerprint())
