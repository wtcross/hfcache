"""Token resolution — the only path by which a credential reaches this process.

The resolution order, the sources that are deliberately ignored, and the
guarantee that a Hub call never sees `token=None` are the contract in
`docs/configuration.md` §7 and `docs/security.md` T-07.

Three properties here are security controls rather than conveniences:

* **No function accepts a token value.** A caller may name a file to read; it
  cannot pass a literal secret. There is no signature into which a token could
  be threaded from configuration, an environment variable, or a command line.
* **`ResolvedToken` cannot print its secret.** `repr`, `str`, and every f-string
  redact, so a token cannot reach a log line, an exception message, or a durable
  artifact through an interpolation nobody thought to audit.
* **Absence is explicit.** `hub_argument` returns `False`, never `None`.
  `token=None` re-enables implicit discovery inside `huggingface_hub`, which
  would let a developer's cached credential silently change what a production
  run does.

Every failure in this module is reported by *shape* — which file, what is wrong
with it — and never by content, so a malformed credential can be diagnosed from
a log without the log becoming a place a secret lives.
"""

import os
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from stat import S_ISREG
from typing import TYPE_CHECKING, Literal, NoReturn, final

from hfcache.errors import ConfigurationError
from hfcache.redaction import register_secret

if TYPE_CHECKING:
    from collections.abc import Mapping

    from hfcache.config import HubConfig

__all__ = [
    "AMBIENT_TOKEN_VARIABLES",
    "CREDENTIALS_DIRECTORY_VARIABLE",
    "MAXIMUM_TOKEN_FILE_BYTES",
    "NO_TOKEN",
    "RepositoryScope",
    "ResolvedToken",
    "TokenSource",
    "ambient_token_variables",
    "resolve_token",
]

CREDENTIALS_DIRECTORY_VARIABLE = "CREDENTIALS_DIRECTORY"
"""Set by systemd for a unit declaring `LoadCredential=` or `SetCredential=`."""

AMBIENT_TOKEN_VARIABLES = frozenset({"HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN"})
"""Implicit sources this application refuses to read (`docs/security.md` T-07).

Listed so `doctor` can tell an operator that a variable they set is deliberately
having no effect. Nothing in this module consults them.
"""

MAXIMUM_TOKEN_FILE_BYTES = 4096
"""A Hub token is tens of bytes. The cap stops a mistyped path from reading a
large file into memory before its contents are found to be unusable."""

_SECRET_BODY = re.compile(r"[!-~]+")
"""Printable ASCII, no whitespace. Applied with `fullmatch`.

`fullmatch` rather than an anchored `match`: `$` also matches immediately before
a trailing newline, so an anchored pattern would accept a second trailing newline
that this module has deliberately not stripped.

A token becomes an `Authorization` header. A stray carriage return, tab, or
non-ASCII byte in the file means the file is malformed, and quietly forwarding
it would put whitespace into a header.
"""


class TokenSource(StrEnum):
    """Where a resolved token came from, in `docs/configuration.md` §7 order."""

    TOKEN_FILE = "token-file"  # noqa: S105 - a source name, not a secret
    SYSTEMD_CREDENTIAL = "systemd-credential"
    NONE = "none"


class RepositoryScope(StrEnum):
    """Which Hub repository access class this resolved credential authorizes."""

    PUBLIC = "public"
    RESTRICTED = "restricted"


@final
@dataclass(frozen=True, slots=True)
class ResolvedToken:
    """A resolved credential, or the explicit absence of one.

    `secret` carries `repr=False`, so the generated `__repr__` — and therefore
    `str()`, `format()`, and every f-string — names the source and the origin
    path but never the value. `dataclasses.asdict` would defeat that; nothing
    serializes this type, and the fingerprint in `docs/configuration.md` §9
    excludes credentials by construction.
    """

    source: TokenSource
    origin: Path | None = None
    secret: str | None = field(default=None, repr=False)
    repository_scope: RepositoryScope = RepositoryScope.PUBLIC

    def __post_init__(self) -> None:
        """Enforce the invariant every caller depends on: `NONE` means no secret."""
        if (self.source is TokenSource.NONE) != (self.secret is None):
            message = f"token source {self.source.value!r} is inconsistent with its secret"
            raise ValueError(message)
        if self.repository_scope is RepositoryScope.RESTRICTED and self.secret is None:
            message = "restricted repository scope requires a resolved credential"
            raise ValueError(message)

    @property
    def has_token(self) -> bool:
        """Whether a credential was found."""
        return self.secret is not None

    @property
    def allows_restricted_repositories(self) -> bool:
        """Whether configuration explicitly opted into private/gated scope (`AD-21`)."""
        return self.repository_scope is RepositoryScope.RESTRICTED

    @property
    def hub_argument(self) -> str | Literal[False]:
        """The exact value to pass as `token=` to every `huggingface_hub` call.

        Never `None`. docs/security.md Hub adapter boundary and `docs/security.md` T-07 both require
        an explicit `False` in anonymous mode, because `None` is the value that
        activates implicit discovery.
        """
        if self.secret is None:
            return False
        return self.secret

    def describe(self) -> str:
        """Describe provenance for a log line or `doctor` output, never the value."""
        if self.source is TokenSource.NONE:
            return "no token; Hub calls pass token=False"
        return f"token from {self.source.value} at {self.origin}"


NO_TOKEN = ResolvedToken(source=TokenSource.NONE)
"""Anonymous public access — the version 1 default (`docs/configuration.md` §3)."""


def _read_secret(path: Path, *, code: str, what: str) -> str:
    """Read one credential file strictly, reporting failures by shape only.

    `code` is the caller's error code — `HFARG005` for `--token-file`,
    `HFARG006` for a systemd credential — so an operator learns which of the two
    sources is broken from the code alone.
    """
    try:
        status = path.stat()
    except FileNotFoundError as exc:
        message = f"{what} ({path}) does not exist"
        raise ConfigurationError.single(message, code=code, location=str(path)) from exc
    except OSError as exc:
        message = f"{what} ({path}) is unreadable: {exc.strerror}"
        raise ConfigurationError.single(message, code=code, location=str(path)) from exc

    if not S_ISREG(status.st_mode):
        message = f"{what} ({path}) is not a regular file"
        raise ConfigurationError.single(message, code=code, location=str(path))
    if status.st_size == 0:
        message = f"{what} ({path}) is empty"
        raise ConfigurationError.single(message, code=code, location=str(path))
    if status.st_size > MAXIMUM_TOKEN_FILE_BYTES:
        message = (
            f"{what} ({path}) is {status.st_size} bytes; a token file may not exceed "
            f"{MAXIMUM_TOKEN_FILE_BYTES}, so this is not a credential"
        )
        raise ConfigurationError.single(message, code=code, location=str(path))

    try:
        raw = path.read_bytes()
    except OSError as exc:
        message = f"{what} ({path}) is unreadable: {exc.strerror}"
        raise ConfigurationError.single(message, code=code, location=str(path)) from exc

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        message = f"{what} ({path}) is not valid UTF-8"
        raise ConfigurationError.single(message, code=code, location=str(path)) from exc

    # Exactly one trailing newline, per `docs/configuration.md` §7 — not a full
    # strip. Anything else left over is caught below rather than silently
    # forwarded into an Authorization header.
    secret = text.removesuffix("\n")
    if not secret:
        message = f"{what} ({path}) contains only a newline"
        raise ConfigurationError.single(message, code=code, location=str(path))
    if not _SECRET_BODY.fullmatch(secret):
        message = (
            f"{what} ({path}) contains whitespace or characters outside printable ASCII; "
            f"the file must hold the token alone, with at most one trailing newline"
        )
        raise ConfigurationError.single(message, code=code, location=str(path))
    register_secret(secret)
    return secret


def _reject_relative_credentials_directory(directory: str) -> NoReturn:
    message = (
        f"${CREDENTIALS_DIRECTORY_VARIABLE} is {directory!r}, which is not an absolute path; "
        f"systemd always sets it absolute, so this environment is misconfigured and a "
        f"credential would be read relative to the current working directory"
    )
    raise ConfigurationError.single(
        message, code="HFARG006", location=CREDENTIALS_DIRECTORY_VARIABLE
    )


def _systemd_credential_path(credential_name: str, environ: Mapping[str, str]) -> Path | None:
    """Locate the systemd credential, or return `None` when none was supplied.

    A missing credential is not an error in `token_mode = "optional"`. A
    credential whose *name* exists but cannot be read is an error, raised by
    `_read_secret`: running anonymously because an installed credential was
    silently unusable is the failure this design refuses to have.
    """
    directory = environ.get(CREDENTIALS_DIRECTORY_VARIABLE, "")
    if not directory:
        return None
    root = Path(directory)
    if not root.is_absolute():
        _reject_relative_credentials_directory(directory)
    path = root / credential_name
    if path.exists() or path.is_symlink():
        return path
    return None


def resolve_token(
    hub: HubConfig,
    *,
    token_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> ResolvedToken:
    """Resolve a credential in `docs/configuration.md` §7 order, first match wins.

    1. `--token-file PATH`, when an operator passed one.
    2. `${CREDENTIALS_DIRECTORY}/<credential_name>`, when systemd supplied one.
    3. No token, so Hub calls pass `token=False` unless `token_mode =
       "required"`, which is `HFARG008`.

    `token_mode = "disabled"` means no credential is read at all. Passing
    `--token-file` anyway is a contradiction rather than a preference, so it is
    `HFARG002`: honouring the flag would violate the configured mode, and
    ignoring it would let an operator believe a run was authenticated when it was
    not.

    Raises `ConfigurationError` (exit `10`) for every failure, always before a
    Hub request is made.
    """
    environment = os.environ if environ is None else environ
    repository_scope = (
        RepositoryScope.RESTRICTED
        if hub.token_mode == "required"  # noqa: S105 - a mode name, not a secret
        else RepositoryScope.PUBLIC
    )

    if hub.token_mode == "disabled":  # noqa: S105 - a mode name, not a secret
        if token_file is not None:
            message = (
                "--token-file was given but hub.token_mode is 'disabled', which requires that "
                "no credential be read; set token_mode = 'optional' or drop the option"
            )
            raise ConfigurationError.single(message, code="HFARG002", location="--token-file")
        return NO_TOKEN

    if token_file is not None:
        secret = _read_secret(token_file, code="HFARG005", what="--token-file")
        return ResolvedToken(
            source=TokenSource.TOKEN_FILE,
            origin=token_file,
            secret=secret,
            repository_scope=repository_scope,
        )

    credential = _systemd_credential_path(hub.credential_name, environment)
    if credential is not None:
        secret = _read_secret(
            credential,
            code="HFARG006",
            what=f"systemd credential {hub.credential_name!r}",
        )
        return ResolvedToken(
            source=TokenSource.SYSTEMD_CREDENTIAL,
            origin=credential,
            secret=secret,
            repository_scope=repository_scope,
        )

    if hub.token_mode == "required":  # noqa: S105 - a mode name, not a secret
        message = (
            "hub.token_mode is 'required', but neither --token-file nor systemd "
            f"credential {hub.credential_name!r} resolved; restricted repository "
            "scope requires an explicit credential"
        )
        raise ConfigurationError.single(message, code="HFARG008", location="hub.token_mode")

    return NO_TOKEN


def ambient_token_variables(environ: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """Return the ambient credential variables that are set, sorted.

    Reported by `doctor` so an operator can see that a variable they exported is
    deliberately having no effect. Resolution never consults these.
    """
    environment = os.environ if environ is None else environ
    return tuple(sorted(name for name in AMBIENT_TOKEN_VARIABLES if environment.get(name)))
