"""Exit classifications, problem records, and the application error hierarchy.

The codes here are the contract in `docs/cli.md` §3 and §5, and in
`docs/configuration.md` §8. They are stable: a code is never reused for a
different condition, and a retired condition retires its code.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Self

__all__ = [
    "ConfigurationError",
    "ExitCode",
    "HfcacheError",
    "Problem",
    "SafetyError",
]


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
