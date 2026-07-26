"""Repository identity and the identifiers the archive names things with.

Every grammar here is fixed by `docs/architecture.md` §5.3, `docs/cli.md` §1.1,
and `docs/configuration.md` §6. Collecting them in one module is a safety
property rather than tidiness: `hfcache.paths` joins these values directly into
filesystem paths, so a value that has been through this module is already known
to be one harmless path segment.

Two conventions here are load-bearing:

* **Patterns are matched with `fullmatch`, never with an anchored `match`.** In
  Python `$` also matches immediately before a trailing newline, so an anchored
  pattern accepts an identifier with a newline glued to its end — which would
  then be written into a path, into a URL, and into a durable artifact.
* **`RepositoryIdentity` validates in `__post_init__`, not only in its
  constructors.** The type is meant to be proof that a repository name is safe
  to build a path from, and a proof that any caller can bypass by using the
  generated `__init__` is not one.
"""

import re
import secrets
import uuid
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal, NewType, Self, final

from hfcache.errors import CodedError, ConfigurationError

if TYPE_CHECKING:
    from hfcache.config import RepositoryConfig

__all__ = [
    "COMMIT_SHA_LENGTH",
    "OPAQUE_ID_LENGTH",
    "PROBE_ID_LENGTH",
    "REPOSITORY_TYPES",
    "SEGMENT_MAXIMUM_LENGTH",
    "TYPE_DIRECTORIES",
    "CommitSha",
    "ProbeId",
    "PublicationId",
    "RepositoryIdentity",
    "RepositorySelector",
    "RepositoryType",
    "RunId",
    "TransactionId",
    "new_probe_id",
    "new_publication_id",
    "new_run_id",
    "new_transaction_id",
    "parse_commit_sha",
    "parse_probe_id",
    "parse_publication_id",
    "parse_repository_id",
    "parse_repository_type",
    "parse_revision",
    "parse_run_id",
    "parse_selector",
    "parse_transaction_id",
]

RepositoryType = Literal["model", "dataset"]

REPOSITORY_TYPES: Final = ("dataset", "model")
"""Every supported type, sorted, so any listing derived from it is deterministic."""

TYPE_DIRECTORIES: Final = MappingProxyType({"dataset": "datasets", "model": "models"})
"""Singular in configuration and on the command line, plural on disk (§5.3).

Public because it is also the enumeration of what the archive can hold: walking
`published/repos/` to discover repositories needs the same two names, and a
second copy of them somewhere else is a third place a future repository type
would have to be added.
"""

SEGMENT_MAXIMUM_LENGTH = 96
COMMIT_SHA_LENGTH = 40
OPAQUE_ID_LENGTH = 32
PROBE_ID_LENGTH = 16

_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_REFERENCE_NAME = re.compile(r"[A-Za-z0-9._/-]{1,255}")
_COMMIT_SHA = re.compile(r"[0-9a-f]{40}")
_OPAQUE_ID = re.compile(r"[0-9a-f]{32}")
_PROBE_ID = re.compile(r"[0-9a-f]{16}")
_ANY_CASE_SHA = re.compile(r"[0-9a-fA-F]{40}")
_ABBREVIATED_SHA = re.compile(r"[0-9a-fA-F]{4,39}")

CommitSha = NewType("CommitSha", str)
"""A full 40-character lowercase commit SHA. Abbreviations never reach disk."""

PublicationId = NewType("PublicationId", str)
"""32 hex identifying one materialization of a revision. Carries no ordering."""

TransactionId = NewType("TransactionId", str)
"""32 hex naming a journal and every directory that journal is responsible for."""

RunId = NewType("RunId", str)
"""32 hex naming one invocation and its run report."""

ProbeId = NewType("ProbeId", str)
"""16 hex naming one preflight write probe under `.store/health`."""


def _parse_hex(
    value: object, *, pattern: re.Pattern[str], length: int, what: str, code: str
) -> str:
    if not isinstance(value, str):
        message = f"{what} must be a string"
        raise CodedError(message, code=code)
    if not pattern.fullmatch(value):
        message = f"invalid {what} {value!r}: expected exactly {length} lowercase hex characters"
        raise CodedError(message, code=code)
    return value


def parse_commit_sha(value: object, *, code: str = "HFCFG009") -> CommitSha:
    """Validate a full 40-character lowercase commit SHA."""
    return CommitSha(
        _parse_hex(
            value, pattern=_COMMIT_SHA, length=COMMIT_SHA_LENGTH, what="commit SHA", code=code
        )
    )


def parse_publication_id(value: object, *, code: str = "HFCFG005") -> PublicationId:
    """Validate a publication identifier."""
    return PublicationId(
        _parse_hex(
            value, pattern=_OPAQUE_ID, length=OPAQUE_ID_LENGTH, what="publication id", code=code
        )
    )


def parse_transaction_id(value: object, *, code: str = "HFCFG005") -> TransactionId:
    """Validate a transaction identifier."""
    return TransactionId(
        _parse_hex(
            value, pattern=_OPAQUE_ID, length=OPAQUE_ID_LENGTH, what="transaction id", code=code
        )
    )


def parse_run_id(value: object, *, code: str = "HFCFG005") -> RunId:
    """Validate a run identifier."""
    return RunId(
        _parse_hex(value, pattern=_OPAQUE_ID, length=OPAQUE_ID_LENGTH, what="run id", code=code)
    )


def parse_probe_id(value: object, *, code: str = "HFCFG005") -> ProbeId:
    """Validate a preflight probe identifier."""
    return ProbeId(
        _parse_hex(value, pattern=_PROBE_ID, length=PROBE_ID_LENGTH, what="probe id", code=code)
    )


def new_publication_id() -> PublicationId:
    """Mint a publication identifier (`docs/architecture.md` §5.3)."""
    return PublicationId(uuid.uuid4().hex)


def new_transaction_id() -> TransactionId:
    """Mint a transaction identifier."""
    return TransactionId(uuid.uuid4().hex)


def new_run_id() -> RunId:
    """Mint a run identifier."""
    return RunId(uuid.uuid4().hex)


def new_probe_id() -> ProbeId:
    """Mint a preflight probe identifier.

    Shorter than the other identifiers because it names a directory that lives
    for the duration of one probe, and `secrets` rather than `random` so a local
    user cannot predict the next probe path (`docs/security.md` T-10).
    """
    return ProbeId(secrets.token_hex(PROBE_ID_LENGTH // 2))


def parse_repository_type(value: object, *, code: str = "HFCFG005") -> RepositoryType:
    """Validate the singular repository type used in configuration and selectors."""
    if value == "model":
        return "model"
    if value == "dataset":
        return "dataset"
    message = f"repository type {value!r} must be 'model' or 'dataset'"
    raise CodedError(message, code=code)


def _require_repository_segment(value: str, *, whole: str) -> None:
    if value in {".", ".."} or not _SEGMENT.fullmatch(value) or len(value) > SEGMENT_MAXIMUM_LENGTH:
        message = f"invalid repository identifier {whole!r}: bad segment {value!r}"
        raise CodedError(message, code="HFCFG008")


def parse_repository_id(value: object) -> str:
    """Validate a two-segment Hub repository identifier.

    Single-segment canonical identifiers are rejected. Every canonical Hub
    repository now has a namespaced form (`gpt2` -> `openai-community/gpt2`), and
    requiring it keeps the on-disk layout unambiguous
    (`docs/architecture.md` §5.3).
    """
    if not isinstance(value, str):
        message = "repository id must be a string"
        raise CodedError(message, code="HFCFG008")
    segments = value.split("/")
    if len(segments) != 2:  # noqa: PLR2004 - exactly namespace and name
        message = (
            f"invalid repository identifier {value!r}: expected exactly two segments "
            f"'<namespace>/<name>'"
        )
        raise CodedError(message, code="HFCFG008")
    for segment in segments:
        _require_repository_segment(segment, whole=value)
    return value


def parse_revision(value: object) -> str:
    """Validate a branch name, tag name, or full 40-character commit SHA.

    Abbreviated SHAs are rejected: they are ambiguous, and an abbreviation is
    never written to disk (`docs/configuration.md` §6).
    """
    if not isinstance(value, str):
        message = "revision must be a string"
        raise CodedError(message, code="HFCFG009")
    if _COMMIT_SHA.fullmatch(value):
        return value
    if _ANY_CASE_SHA.fullmatch(value):
        # Reachable only for a mis-cased SHA, since the lowercase form returned
        # above. Treating it as a branch name would send an uppercase SHA to the
        # Hub and write a non-canonical value toward disk.
        message = (
            f"invalid revision {value!r}: a commit SHA must be lowercase hex; use {value.lower()!r}"
        )
        raise CodedError(message, code="HFCFG009")
    if _ABBREVIATED_SHA.fullmatch(value):
        message = (
            f"invalid revision {value!r}: abbreviated commit SHAs are ambiguous; "
            f"use the full 40-character SHA or a branch or tag name"
        )
        raise CodedError(message, code="HFCFG009")
    if (
        not _REFERENCE_NAME.fullmatch(value)
        or value.startswith(("-", "/"))
        or value.endswith(("/", ".lock"))
        or "//" in value
        or ".." in value
    ):
        message = f"invalid revision {value!r}: not a usable branch or tag name"
        raise CodedError(message, code="HFCFG009")
    return value


@final
@dataclass(frozen=True, slots=True)
class RepositoryIdentity:
    """One repository the archive can name: its type and its two id segments.

    Constructing this type proves the name is safe to build a path from, so
    `hfcache.paths` joins `namespace` and `name` without re-checking them.
    `__post_init__` is what makes that true for every construction, including
    the generated `__init__` and `dataclasses.replace`.
    """

    type: RepositoryType
    namespace: str
    name: str

    def __post_init__(self) -> None:
        """Re-validate both segments, whichever constructor was used."""
        whole = f"{self.namespace}/{self.name}"
        parse_repository_type(self.type)
        _require_repository_segment(self.namespace, whole=whole)
        _require_repository_segment(self.name, whole=whole)

    @classmethod
    def of(cls, repository_type: object, repository_id: object) -> Self:
        """Build an identity from an unvalidated type and `<namespace>/<name>`."""
        namespace, name = parse_repository_id(repository_id).split("/")
        return cls(type=parse_repository_type(repository_type), namespace=namespace, name=name)

    @classmethod
    def from_config(cls, repository: RepositoryConfig) -> Self:
        """Build an identity from a validated `[[repositories]]` entry."""
        return cls.of(repository.type, repository.id)

    @property
    def id(self) -> str:
        """The two-segment Hub identifier, `<namespace>/<name>`."""
        return f"{self.namespace}/{self.name}"

    @property
    def selector(self) -> str:
        """The `TYPE:ID` form used by CLI selectors (`docs/cli.md` §1.1)."""
        return f"{self.type}:{self.id}"

    @property
    def directory(self) -> str:
        """The plural on-disk directory name for this type (`models`, `datasets`)."""
        return TYPE_DIRECTORIES[self.type]

    @property
    def sort_key(self) -> tuple[str, str]:
        """Ordering key for any generated listing: byte-wise on `(type, id)`.

        Deliberately not `dataclass(order=True)`, which would compare
        `(type, namespace, name)` and put `a/b-x` before `a-b/x` — the opposite
        of the byte-wise ordering on `id` that `docs/architecture.md` §5.3
        requires, because `-` sorts before `/`.
        """
        return (self.type, self.id)

    def __str__(self) -> str:
        """Render as the selector an operator would type."""
        return self.selector


@final
@dataclass(frozen=True, slots=True)
class RepositorySelector:
    """A parsed `TYPE:ID` or `TYPE:ID@SHA` command-line selector."""

    identity: RepositoryIdentity
    commit_sha: CommitSha | None = None

    @property
    def sort_key(self) -> tuple[str, str, str]:
        """Ordering key that keeps selector listings deterministic."""
        return (*self.identity.sort_key, self.commit_sha or "")

    def __str__(self) -> str:
        """Render as the selector an operator would type."""
        if self.commit_sha is None:
            return self.identity.selector
        return f"{self.identity.selector}@{self.commit_sha}"


def _reject_selector(value: str, detail: str) -> ConfigurationError:
    message = (
        f"invalid selector {value!r}: {detail}; expected TYPE:NAMESPACE/NAME "
        f"or TYPE:NAMESPACE/NAME@SHA"
    )
    return ConfigurationError.single(message, code="HFARG001", location=value)


def parse_selector(value: str) -> RepositorySelector:
    """Parse one `TYPE:ID[@SHA]` selector (`docs/cli.md` §1.1).

    Every rejection is `HFARG001`, including an abbreviated SHA, which the
    contract calls out specifically: an abbreviation could match more than one
    revision, and choosing one of them would be a guess (`AD-16`).
    """
    type_text, separator, remainder = value.partition(":")
    if not separator:
        raise _reject_selector(value, "no ':' between type and repository id")
    identifier, at_sign, sha_text = remainder.partition("@")
    try:
        identity = RepositoryIdentity.of(type_text, identifier)
    except CodedError as exc:
        raise _reject_selector(value, str(exc)) from exc
    if not at_sign:
        return RepositorySelector(identity=identity)
    if _ABBREVIATED_SHA.fullmatch(sha_text):
        detail = f"{sha_text!r} is an abbreviated commit SHA; give all {COMMIT_SHA_LENGTH}"
        raise _reject_selector(value, detail)
    try:
        commit_sha = parse_commit_sha(sha_text, code="HFARG001")
    except CodedError as exc:
        raise _reject_selector(value, str(exc)) from exc
    return RepositorySelector(identity=identity, commit_sha=commit_sha)
