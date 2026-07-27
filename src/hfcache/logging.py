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

*The run id in every event.* `emit` injects it; no call site passes it. There is
always one, because `configure` binds a fresh id and `cli.emit_envelope` reports
that same id when a command writes no durable report — so the envelope on stdout
and the lines on stderr always name the same invocation.

*Durable checkpoints, not per-chunk noise.* The default level emits one line per
thing that became durable. Nothing here is called from inside a transfer or a
hashing loop, and the count of lines a run produces is a function of how many
repositories it touched, never of how many bytes it moved.

*Never a token, header, or signed URL.* Two layers. Structurally, only named
fields reach `emit`, and no call site passes a credential. Mechanically,
`_scrub` redacts by key and by value shape anyway, because the structural
argument holds only until someone adds a call site.

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
import re
import sys
from typing import Final, TextIO

from hfcache.identity import new_run_id

__all__ = [
    "DEBUG_EVENTS",
    "EVENTS",
    "LOGGER_NAME",
    "REDACTED",
    "bind_run",
    "configure",
    "current_run_id",
    "emit",
    "level_for",
    "reset",
    "under_systemd",
]

LOGGER_NAME: Final = "hfcache"

EVENTS: Final = (
    "run.started",
    "preflight.failed",
    "repository.resolved",
    "repository.skipped",
    "download.started",
    "download.completed",
    "verification.completed",
    "dependency.undeclared",
    "publication.completed",
    "retention.pruned",
    "retention.deferred",
    "repository.failed",
    "run.completed",
)
"""Plan §24's recommended families, adopted verbatim as the stable vocabulary."""

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
_WARNING: Final = frozenset({"dependency.undeclared", "retention.deferred"})

REDACTED: Final = "[redacted]"

_SECRET_KEYS: Final = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "cookie",
        "credential",
        "header",
        "password",
        "secret",
        "token",
    }
)
"""Field names that never carry a loggable value (`docs/security.md` T-07)."""

_SECRET_VALUE: Final = re.compile(r"(?:hf_[A-Za-z0-9]{8,}|bearer\s+\S+)", re.IGNORECASE)
"""A Hub token or an `Authorization` value that reached a field by another name."""

_SIGNED_URL: Final = re.compile(
    r"https?://\S*[?&](?:x-amz-|x-goog-|sig=|signature=|token=)", re.IGNORECASE
)
"""A presigned download URL. Plan §24 forbids logging these specifically."""

_PRIORITY: Final = {
    logging.ERROR: "<3>",
    logging.WARNING: "<4>",
    logging.INFO: "<6>",
    logging.DEBUG: "<7>",
}

_run_id: str | None = None


def under_systemd() -> bool:
    """Whether this process was started by a systemd unit.

    `INVOCATION_ID` is set for every unit systemd starts and for nothing else,
    which is the one signal that does not depend on the environment an operator
    happens to have. Also what `cli._run_envelope` reports as `invocation_mode`,
    so the run report and the log agree about where a run came from.
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
    if key.lower() in _SECRET_KEYS:
        return REDACTED
    text = str(value)
    if _SECRET_VALUE.search(text) or _SIGNED_URL.search(text):
        return REDACTED
    return _quote(text)


class _LogfmtFormatter(logging.Formatter):
    """`event=… level=… run_id=… key=value` on one line, keys sorted after the first three."""

    def __init__(self, *, prefix: bool) -> None:
        super().__init__()
        self._prefix = prefix

    def format(self, record: logging.LogRecord) -> str:
        fields: dict[str, object] = getattr(record, "fields", {})
        event = getattr(record, "event", record.getMessage())
        parts = [
            f"event={_scrub('event', event)}",
            f"level={record.levelname.lower()}",
            f"run_id={_scrub('run_id', _run_id or '-')}",
        ]
        parts.extend(f"{key}={_scrub(key, fields[key])}" for key in sorted(fields))
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
    """Install the stderr handler and bind a run id. Idempotent.

    Called once from the CLI callback, before any command runs, so a failure in
    argument handling is still logged. Replacing the handler rather than adding
    one is what makes it safe to call repeatedly, which the test suite does.
    """
    logger = logging.getLogger(LOGGER_NAME)
    for existing in list(logger.handlers):
        logger.removeHandler(existing)
    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.setFormatter(_LogfmtFormatter(prefix=under_systemd()))
    logger.addHandler(handler)
    logger.setLevel(level_for(verbose=verbose, quiet=quiet))
    # Never up to the root logger: a dependency that configured logging must not
    # be able to duplicate these lines or redirect them onto stdout.
    logger.propagate = False
    bind_run(run_id if run_id is not None else new_run_id())


def bind_run(run_id: str | None) -> None:
    """Name the run every subsequent event belongs to.

    Commands that write a durable report call this with that report's id, so the
    log, the envelope, and `runs/<…>.json` all carry one identifier (§24).
    """
    global _run_id  # noqa: PLW0603 - one process, one run; see the module docstring
    _run_id = run_id


def current_run_id() -> str | None:
    """The bound run id, for `cli.emit_envelope` to report as its own."""
    return _run_id


def reset() -> None:
    """Drop the handler and the bound run id, so one test cannot leak into another."""
    logger = logging.getLogger(LOGGER_NAME)
    for existing in list(logger.handlers):
        logger.removeHandler(existing)
    logger.setLevel(logging.NOTSET)
    bind_run(None)


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
    logging.getLogger(LOGGER_NAME).log(level, name, extra={"event": name, "fields": fields})
