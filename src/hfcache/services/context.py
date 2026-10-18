"""Immutable execution identity and transport-independent schema-1 results."""

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

from hfcache.errors import ExitCode, Problem
from hfcache.identity import RunId, new_run_id, parse_run_id
from hfcache.logging import scoped_context
from hfcache.models import format_timestamp, parse_timestamp
from hfcache.reporting import Envelope, EnvelopeProblem

if TYPE_CHECKING:
    from collections.abc import Iterator


def new_request_id() -> str:
    """Mint a transport request ID on the trusted boundary, never from a header."""
    return new_run_id()


def new_operation_id() -> str:
    """Mint an admission ID independent of its requests, run and transactions."""
    return new_run_id()


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _freeze_problem(problem: Problem) -> Problem:
    snapshot = Problem(
        code=problem.code,
        message=problem.message,
        location=problem.location,
        repository=problem.repository,
        context=problem.context,
    )
    object.__setattr__(snapshot, "context", _freeze(snapshot.context))
    return snapshot


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """One invocation's nonsecret identity, shared by adapters and services."""

    run_id: RunId
    started_at: datetime
    request_id: str | None = None
    operation_id: str | None = None

    def __post_init__(self) -> None:
        parse_run_id(self.run_id)
        for identifier in (self.request_id, self.operation_id):
            if identifier is not None:
                parse_run_id(identifier)
        object.__setattr__(self, "started_at", parse_timestamp(self.started_at))

    @classmethod
    def create(
        cls, *, request_id: str | None = None, operation_id: str | None = None
    ) -> ExecutionContext:
        """Create a context for an invocation without a durable run report."""
        return cls(
            run_id=new_run_id(),
            started_at=datetime.now(UTC),
            request_id=request_id,
            operation_id=operation_id,
        )

    @classmethod
    def new_request(cls) -> ExecutionContext:
        """Mint authoritative request and invocation identities at the server boundary."""
        return cls.create(request_id=new_request_id())

    @contextmanager
    def activate(self) -> Iterator[ExecutionContext]:
        """Activate this execution without changing global log level or handlers."""
        with scoped_context(
            run_id=self.run_id, request_id=self.request_id, operation_id=self.operation_id
        ):
            yield self


@dataclass(frozen=True, slots=True)
class ServiceResult:
    """An immutable payload and classified problems, without output side effects.

    ``data`` returns a fresh JSON-compatible tree so adapters cannot mutate the
    result another observer receives. Envelope serialization stays schema 1
    (INV-005/INV-006), including its established error-priority classification.
    """

    command: str
    payload: Mapping[str, Any]
    warnings: tuple[Problem, ...] = ()
    errors: tuple[Problem, ...] = ()
    exit_code: int = ExitCode.SUCCESS
    run_id: RunId | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze(self.payload))
        object.__setattr__(self, "warnings", tuple(_freeze_problem(item) for item in self.warnings))
        object.__setattr__(self, "errors", tuple(_freeze_problem(item) for item in self.errors))
        if self.run_id is not None:
            parse_run_id(self.run_id)

    @property
    def data(self) -> dict[str, Any]:
        """Return an independent rendering payload."""
        return cast("dict[str, Any]", _thaw(self.payload))

    def envelope(
        self, context: ExecutionContext, *, completed_at: datetime | None = None
    ) -> Envelope:
        """Build the deterministic public envelope; callers choose how to emit it."""
        outcome = (
            "failed"
            if self.exit_code
            else ("success_with_warnings" if self.warnings else "success")
        )
        return Envelope(
            command=self.command,
            completed_at=format_timestamp(completed_at or datetime.now(UTC)),
            data=self.data,
            errors=tuple(
                EnvelopeProblem.model_validate(_thaw(problem.as_envelope_entry()))
                for problem in self.errors
            ),
            exit_code=self.exit_code,
            outcome=outcome,
            run_id=self.run_id or context.run_id,
            started_at=format_timestamp(context.started_at),
            warnings=tuple(
                EnvelopeProblem.model_validate(_thaw(problem.as_envelope_entry()))
                for problem in self.warnings
            ),
        )
