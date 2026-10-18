"""Exit classifications, problem records, and the application error hierarchy.

The codes here are the contract in `docs/cli.md` §3 and §5, and in
`docs/configuration.md` §8. They are stable: a code is never reused for a
different condition, and a retired condition retires its code.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from types import MappingProxyType
from typing import Any, Self, cast

from hfcache.redaction import redact_text, sanitize

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "CodedError",
    "ConfigurationError",
    "ExitCode",
    "HfcacheError",
    "IntegrityError",
    "OperationError",
    "Problem",
    "RequestError",
    "RetentionError",
    "SafetyError",
    "SynchronizationError",
]


class CodedError(ValueError):
    """A grammar or constraint failure that already knows its error code.

    Raised by the low-level validators in `hfcache.identity` and
    `hfcache.config`. It is a `ValueError` so that Pydantic collects it as an
    ordinary validation failure, and it carries the code so the collector does
    not have to re-derive which rule was broken from the message text.

    The message comes first so a raise site reads as an ordinary exception and
    the message stays in a variable, which is what keeps tracebacks readable.
    """

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class ExitCode(IntEnum):
    """Aggregate outcome of a command.

    Aggregation rule (`docs/cli.md` §3): `CONFIGURATION` and `SAFETY` abort
    before per-repository work begins, so they never co-occur with the rest.
    Among the remaining three, the reported code is the first of `INTEGRITY`,
    `RETENTION`, `SYNC` that occurred — ordered by operator urgency.

    `1` and `2` are deliberately unused because Typer reserves them for usage
    errors; a scheduler must be able to tell a malformed command line from an
    application outcome.
    """

    SUCCESS = 0
    CONFIGURATION = 10
    SAFETY = 20
    SYNC = 30
    INTEGRITY = 40
    RETENTION = 50


@dataclass(frozen=True, slots=True)
class Problem:
    """One coded warning or error, as it appears in the JSON envelope.

    `location` names *where* the problem is — a TOML key path, an
    archive-relative file path — never the offending value. A secret is
    reported by shape, never by content (`docs/cli.md` §6).
    """

    code: str
    message: str
    location: str | None = None
    repository: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Snapshot safe diagnostics before exceptions or durable code can inspect them."""
        object.__setattr__(self, "message", redact_text(self.message))
        if self.location is not None:
            object.__setattr__(self, "location", redact_text(self.location))
        if self.repository is not None:
            object.__setattr__(self, "repository", redact_text(self.repository))
        object.__setattr__(self, "context", cast("dict[str, Any]", sanitize(self.context)))

    def as_envelope_entry(self) -> dict[str, Any]:
        """Render this problem in the `docs/cli.md` §4 envelope shape."""
        return cast(
            "dict[str, Any]",
            sanitize(
                {
                    "code": self.code,
                    "context": dict(self.context)
                    | ({"location": self.location} if self.location else {}),
                    "message": self.message,
                    "repository": self.repository,
                }
            ),
        )

    def as_line(self) -> str:
        """Render this problem for human-readable output."""
        where = f" [{self.location}]" if self.location else ""
        who = f" ({self.repository})" if self.repository else ""
        return redact_text(f"{self.code}{who}{where}: {self.message}")

    def __repr__(self) -> str:
        """Avoid auto-dataclass repr bypassing credentials registered after construction."""
        return f"Problem({self.as_envelope_entry()!r})"


class HfcacheError(Exception):
    """Base class for every failure that maps to an application exit code."""

    exit_code: ExitCode = ExitCode.CONFIGURATION

    def __init__(self, problems: list[Problem] | tuple[Problem, ...]) -> None:
        self.problems: tuple[Problem, ...] = tuple(problems)
        summary = "; ".join(problem.as_line() for problem in self.problems)
        super().__init__(summary or self.__class__.__name__)

    def __str__(self) -> str:
        """Also cover credentials registered after this exception was constructed."""
        return redact_text(super().__str__())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r})"

    @classmethod
    def single(
        cls,
        message: str,
        *,
        code: str,
        location: str | None = None,
        repository: str | None = None,
        **context: object,
    ) -> Self:
        """Build an error carrying exactly one problem.

        The message comes first so a raise site reads as an ordinary exception.
        Returning `Self` keeps `ConfigurationError.single(...)` typed as a
        `ConfigurationError`, so callers do not have to re-narrow it.
        """
        return cls(
            [
                Problem(
                    code=code,
                    message=message,
                    location=location,
                    repository=repository,
                    context=context,
                )
            ]
        )


class ConfigurationError(HfcacheError):
    """Invalid configuration or invocation precondition. Exits `10`.

    Raised before any lock is taken, any Hub request is made, or any path is
    mutated (`docs/configuration.md` §8).
    """

    exit_code = ExitCode.CONFIGURATION


class AuthenticationError(ConfigurationError):
    """Missing, malformed or wrong-interface bearer; stable HTTP 401 (HFAPI001)."""

    status_code = 401
    detail = "Not authenticated"
    headers = MappingProxyType({"WWW-Authenticate": 'Bearer realm="hfcache"'})

    def __init__(self) -> None:
        super().__init__([Problem("HFAPI001", self.detail)])


class AuthorizationError(ConfigurationError):
    """A valid principal lacks the required capability; stable HTTP 403 (HFAPI002)."""

    status_code = 403
    detail = "Forbidden"
    headers = MappingProxyType({})

    def __init__(self) -> None:
        super().__init__([Problem("HFAPI002", self.detail)])


class RequestError(ConfigurationError):
    """Sanitized transport validation/security refusal, with a stable HTTP status."""

    def __init__(
        self,
        *,
        code: str = "HFAPI006",
        status_code: int = 422,
        message: str = "Invalid request",
    ) -> None:
        self.status_code = status_code
        super().__init__([Problem(code, message)])


class SafetyError(HfcacheError):
    """Mount, sentinel, permission, capacity, lock, or transaction safety failure.

    Exits `20`, always before a Hub download begins (docs/cli.md doctor contract).
    """

    exit_code = ExitCode.SAFETY


class OperationError(SafetyError):
    """Preserved control-plane uncertainty, never evidence of nonexecution."""

    def __init__(
        self,
        *,
        code: str = "HFAPI014",
        status_code: int = 503,
        message: str = "Operation history is unsafe, full or unavailable",
    ) -> None:
        self.status_code = status_code
        super().__init__([Problem(code, message)])


class SynchronizationError(HfcacheError):
    """Hub resolution, download, or publication failure. Exits `30`.

    Per-repository: with `sync.continue_on_repository_error`, one of these ends
    the repository rather than the run, and every local revision is preserved
    (`AD-06`).
    """

    exit_code = ExitCode.SYNC


class IntegrityError(HfcacheError):
    """Content does not match its manifest, or a manifest is unusable. Exits `40`.

    Never triggers a rewrite, a prune, or a re-download over the evidence
    (`AD-13`, `AD-18`). The finding is the point.
    """

    exit_code = ExitCode.INTEGRITY


class RetentionError(HfcacheError):
    """Prune, repair, or recovery failure. Exits `50`.

    Ranked below integrity in aggregation because degraded retention keeps more
    data than intended, while an integrity failure means data is already wrong.
    """

    exit_code = ExitCode.RETENTION
