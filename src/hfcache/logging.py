"""Structured event log for journald (`docs/plan.md` §24).

The durable run report under `runs/` is the record of what a run *did*. This is
the record of what *happened* — and the two are not the same thing, because a
run report only exists once a run gets far enough to write one. A run that dies
in preflight, on a lock timeout, or part way through a download leaves no report
at all, so without this the only trace is systemd's exit code. Those are exactly
the runs an operator needs to reconstruct.

Four properties §24 asks for, and how each is obtained here:

*Stable event names.* `EVENTS` is a closed vocabulary and `emit` refuses a name
outside it. A typo is a test failure rather than a line nobody greps for, and an
operator's `journalctl … event=publication.completed` keeps working across
releases.

*Execution correlation in every event.* `emit` captures the current context at
record creation, including its domain run ID and optional request/operation IDs.
Scoped bindings restore after success or failure; thread submissions explicitly
copy context. CLI startup binds one invocation; daemon startup binds no request.
Call-site fields cannot replace authoritative IDs (decision 111).

*Durable checkpoints, not per-chunk noise.* The default level emits one line per
thing that became durable. Nothing here is called from inside a transfer or a
hashing loop, and the count of lines a run produces is a function of how many
repositories it touched, never of how many bytes it moved.

*Never a token, header, or signed URL.* Two layers. Structurally, only named
fields reach `emit`, and no call site passes a credential. Mechanically,
the shared sanitizer redacts sensitive keys, registered opaque values and known
credential/URL shapes. Unknown arbitrary secrets cannot be recognized by regex;
credential loaders register exact values before use.

Output is logfmt on **stderr** — `docs/cli.md` §4 reserves stdout for the JSON
envelope, so piping stdout stays safe at any verbosity. Under systemd each line
carries a `<N>` syslog prefix, which journald strips and turns into `PRIORITY`,
so `journalctl -p err -u hfcache-sync.service` selects failures. Interactively
there is no prefix, because it would just be noise on a terminal.

`import logging` below is the standard library's, not this module: Python 3
resolves it absolutely. Plan §7 fixes this module's name and `FW-03` requires
logging come from the standard library, so the collision is by design and costs
nothing.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from dataclasses import dataclass, replace
from threading import RLock
from typing import TYPE_CHECKING, Final, TextIO

from hfcache.identity import new_run_id
from hfcache.redaction import REDACTED, redact_text, sanitize

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from concurrent.futures import Executor, Future

__all__ = [
    "DEBUG_EVENTS",
    "EVENTS",
    "LOGGER_NAME",
    "REDACTED",
    "Correlation",
    "bind_run",
    "configure",
    "configure_daemon",
    "current_correlation",
    "current_run_id",
    "emit",
    "level_for",
    "reset",
    "scoped_context",
    "submit_with_context",
    "under_systemd",
]

LOGGER_NAME: Final = "hfcache"

EVENTS: Final = (
    "run.started",
    "preflight.failed",
    "repository.resolved",
    "repository.queued",
    "repository.skipped",
    "download.started",
    "download.completed",
    "hash.started",
    "hash.completed",
    "verification.completed",
    "dependency.undeclared",
    "publication.completed",
    "retention.pruned",
    "retention.deferred",
    "quarantine.cleaned",
    "repository.failed",
    "run.completed",
    "mcp.diagnostic",
)
"""Plan §24's stable vocabulary, including the decision 103 cleanup amendment."""

DEBUG_EVENTS: Final = (
    "preflight.check",
    "capacity.evaluated",
)
"""Detail `--verbose` adds, deliberately outside §24's stable set.

Both are bounded: one line per §19 check, and one per capacity evaluation. They
exist so `-v` selects something real — a flag that lowers a threshold nothing
emits below is the same kind of documented lie as one that is never read at all.
They are not part of the §24 contract and may change; the `EVENTS` names may not.
"""

_ERROR: Final = frozenset({"preflight.failed", "repository.failed"})
_WARNING: Final = frozenset({"dependency.undeclared", "retention.deferred", "mcp.diagnostic"})

_PRIORITY: Final = {
    logging.ERROR: "<3>",
    logging.WARNING: "<4>",
    logging.INFO: "<6>",
    logging.DEBUG: "<7>",
}


@dataclass(frozen=True, slots=True)
class Correlation:
    """Nonsecret request/operation relationships; durable run IDs remain independent."""

    run_id: str | None = None
    request_id: str | None = None
    operation_id: str | None = None


_EMPTY_CORRELATION = Correlation()
_correlation = ContextVar("hfcache_correlation", default=_EMPTY_CORRELATION)
_configuration_lock = RLock()
_daemon_configured = False


def under_systemd() -> bool:
    """Whether this process was started by a systemd unit.

    `INVOCATION_ID` is set for every unit systemd starts and for nothing else,
    which is the one signal that does not depend on the environment an operator
    happens to have. The durable `invocation_mode` describes this execution host,
    not an authenticated submitter or proof of timer origin (decision 111).
    """
    return bool(os.environ.get("INVOCATION_ID"))


def level_for(*, verbose: int, quiet: bool) -> int:
    """Map `docs/cli.md` §1's verbosity options onto a level.

    `--quiet` suppresses informational output and leaves warnings and errors,
    which is exactly `WARNING`. Default is `INFO`, because the §24 families are
    the record an unattended run leaves behind and requiring a flag to get them
    would mean the systemd units had to pass one. `-v` adds `DEBUG_EVENTS`.

    Repeats beyond the first are accepted and currently equivalent to one, since
    the vocabulary bottoms out at `DEBUG`; `docs/cli.md` says so rather than
    implying a finer level that does not exist.
    """
    if quiet:
        return logging.WARNING
    if verbose:
        return logging.DEBUG
    return logging.INFO


def _quote(value: str) -> str:
    """Wrap a logfmt value only when it would otherwise be ambiguous."""
    if value == "":
        return '""'
    if any(character in value for character in ' ="\\') or "\n" in value:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    return value


def _scrub(key: str, value: object) -> str:
    """Render one field, redacting anything that could be a secret.

    By key first, because a field named `token` has no rendering that is safe.
    Then by value shape, which is the layer that catches a token or a presigned
    URL arriving under an innocent name — `location`, `detail`, `source`. Both
    are cheap and neither is the real guarantee: the real one is that no call
    site passes a credential. This is what keeps that true when one does.
    """
    return _quote(redact_text(str(sanitize(value, key=key))))


class _LogfmtFormatter(logging.Formatter):
    """`event=… level=… run_id=… key=value` on one line, keys sorted after the first three."""

    def __init__(self, *, prefix: bool) -> None:
        super().__init__()
        self._prefix = prefix

    def format(self, record: logging.LogRecord) -> str:
        fields: dict[str, object] = getattr(record, "fields", {})
        event = getattr(record, "event", record.getMessage())
        correlation = getattr(record, "correlation", current_correlation())
        parts = [
            f"event={_scrub('event', event)}",
            f"level={record.levelname.lower()}",
            f"run_id={_scrub('run_id', correlation.run_id or '-')}",
        ]
        relationships = {
            key: value
            for key, value in (
                ("request_id", correlation.request_id),
                ("operation_id", correlation.operation_id),
            )
            if value is not None
        }
        # Caller fields cannot replace authoritative correlation captured at emit.
        reserved = {"event", "level", "run_id", "request_id", "operation_id"}
        combined = {
            key: value for key, value in fields.items() if key not in reserved
        } | relationships
        parts.extend(f"{key}={_scrub(key, combined[key])}" for key in sorted(combined))
        line = " ".join(parts)
        if self._prefix:
            return f"{_PRIORITY[record.levelno]}{line}"
        return line


def configure(
    *,
    verbose: int = 0,
    quiet: bool = False,
    stream: TextIO | None = None,
    run_id: str | None = None,
) -> None:
    """Configure isolated CLI startup; daemon request code must never call this.

    Called once from the CLI callback before command execution. Replacing rather
    than adding a handler supports repeated isolated CLI invocations in tests.
    A configured daemon refuses this entry point instead of changing its policy.
    """
    with _configuration_lock:
        if _daemon_configured:
            message = "daemon logging is configured at startup; requests cannot reconfigure it"
            raise RuntimeError(message)
        _install(stream=stream, level=level_for(verbose=verbose, quiet=quiet))
    bind_run(run_id if run_id is not None else new_run_id())


def _install(*, stream: TextIO | None, level: int) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    for existing in list(logger.handlers):
        logger.removeHandler(existing)
        existing.close()
    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.setFormatter(_LogfmtFormatter(prefix=under_systemd()))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def configure_daemon(*, stream: TextIO | None = None, level: int = logging.INFO) -> None:
    """Install one request-neutral handler at daemon startup; repeat calls are no-ops.

    Request quiet/verbose flags belong to client rendering and event selection,
    never to this process-wide logger's configuration (decision 111).
    """
    global _daemon_configured  # noqa: PLW0603 - process startup configuration, not request state
    with _configuration_lock:
        if not _daemon_configured:
            _install(stream=stream, level=level)
            _daemon_configured = True
            _correlation.set(Correlation())


def current_correlation() -> Correlation:
    """Return this task/thread's frozen nonsecret correlation snapshot."""
    return _correlation.get()


@contextmanager
def scoped_context(
    *, run_id: str | None, request_id: str | None = None, operation_id: str | None = None
) -> Iterator[Correlation]:
    """Bind execution IDs and restore the previous scope on every exit path."""
    correlation = Correlation(run_id, request_id, operation_id)
    token = _correlation.set(correlation)
    try:
        yield correlation
    finally:
        _correlation.reset(token)


def submit_with_context[**P, ResultT](
    executor: Executor, function: Callable[P, ResultT], /, *args: P.args, **kwargs: P.kwargs
) -> Future[ResultT]:
    """Submit one independent context copy; reused worker threads retain no scope."""
    context = copy_context()
    return executor.submit(context.run, function, *args, **kwargs)


def bind_run(run_id: str | None) -> None:
    """Set the current scope's run identity for isolated CLI compatibility.

    Request and worker execution use scoped_context/ExecutionContext.activate so
    completion and exceptions restore the caller's previous identity (§24).
    """
    _correlation.set(replace(current_correlation(), run_id=run_id))


def current_run_id() -> str | None:
    """The bound run id, for `cli.emit_envelope` to report as its own."""
    return current_correlation().run_id


def reset() -> None:
    """Drop the handler and the bound run id, so one test cannot leak into another."""
    global _daemon_configured  # noqa: PLW0603 - explicit process teardown/test reset
    with _configuration_lock:
        logger = logging.getLogger(LOGGER_NAME)
        for existing in list(logger.handlers):
            logger.removeHandler(existing)
            existing.close()
        logger.setLevel(logging.NOTSET)
        _daemon_configured = False
    _correlation.set(Correlation())


def emit(name: str, /, **fields: object) -> None:
    """Record one durable fact.

    `name` is positional-only so a field may legitimately be called `name`, and
    it must be in `EVENTS` or `DEBUG_EVENTS`: the vocabulary is the contract
    operators write filters against, and a name outside it is a programming
    error that should fail in the suite rather than reach a journal.
    """
    if name in _ERROR:
        level = logging.ERROR
    elif name in _WARNING:
        level = logging.WARNING
    elif name in EVENTS:
        level = logging.INFO
    elif name in DEBUG_EVENTS:
        level = logging.DEBUG
    else:
        message = f"{name!r} is not a known event; see hfcache.logging.EVENTS"
        raise ValueError(message)
    logging.getLogger(LOGGER_NAME).log(
        level,
        name,
        extra={"event": name, "fields": sanitize(fields), "correlation": current_correlation()},
    )
