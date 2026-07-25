"""Exit classifications, problem records, and the application error hierarchy.

The codes here are the contract in `docs/cli.md` §3 and §5, and in
`docs/configuration.md` §8. They are stable: a code is never reused for a
different condition, and a retired condition retires its code.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Self

__all__ = [
    "CodedError",
    "ConfigurationError",
    "ExitCode",
    "HfcacheError",
    "IntegrityError",
    "Problem",
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

    def as_envelope_entry(self) -> dict[str, Any]:
        """Render this problem in the `docs/cli.md` §4 envelope shape."""
        return {
            "code": self.code,
            "context": dict(self.context) | ({"location": self.location} if self.location else {}),
            "message": self.message,
            "repository": self.repository,
        }

    def as_line(self) -> str:
        """Render this problem for human-readable output."""
        where = f" [{self.location}]" if self.location else ""
        who = f" ({self.repository})" if self.repository else ""
        return f"{self.code}{who}{where}: {self.message}"


class HfcacheError(Exception):
    """Base class for every failure that maps to an application exit code."""

    exit_code: ExitCode = ExitCode.CONFIGURATION

    def __init__(self, problems: list[Problem] | tuple[Problem, ...]) -> None:
        self.problems: tuple[Problem, ...] = tuple(problems)
        summary = "; ".join(problem.as_line() for problem in self.problems)
        super().__init__(summary or self.__class__.__name__)

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


class SafetyError(HfcacheError):
    """Mount, sentinel, permission, capacity, lock, or transaction safety failure.

    Exits `20`, always before a Hub download begins (`docs/plan.md` §19).
    """

    exit_code = ExitCode.SAFETY


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
