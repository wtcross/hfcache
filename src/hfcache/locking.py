"""The local exclusive lock that serializes every mutating command.

`AD-17`: exactly one host has read/write access to the archive, enforced by the
export's exact-host restriction, so mutual exclusion between `sync`, `verify`,
`prune`, `repair`, and `recover` is a *local* lock under `/run/hfcache`. There
are deliberately no lock files on NFS: distributed locking over NFS is a
well-known source of subtle failure and buys nothing when there is one writer.

`flock(2)` is what makes this correct rather than advisory-in-name-only. The
lock lives on the open file description, so the kernel releases it when the
process dies — including on `SIGKILL`, an OOM kill, or a panic — and a crashed
sync therefore cannot leave a lock that an operator has to clear by hand. That is
the property a pid file would not have.

The holder record written into the file is diagnostic only. Nothing depends on
it: it exists so that a command which gives up waiting can say *who* it was
waiting for instead of just that it waited.
"""

import fcntl
import json
import os
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from hfcache.errors import Problem, SafetyError

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "LOCK_DIRECTORY",
    "LOCK_DIRECTORY_MODE",
    "LOCK_MODE",
    "LOCK_NAME",
    "exclusive_lock",
    "lock_path",
    "read_holder",
]

LOCK_DIRECTORY = Path("/run/hfcache")
"""Transient run state, created by `RuntimeDirectory=hfcache` (plan §22.5).

`/run` is a tmpfs, so the lock file cannot survive a reboot — which is the
correct lifetime for something whose whole meaning is "a process is running".
"""

LOCK_NAME: Final = "hfcache.lock"
"""One lock for every mutating command, not one per command (`AD-17`)."""

LOCK_DIRECTORY_MODE: Final = 0o700
LOCK_MODE: Final = 0o600

_POLL_SECONDS: Final = 1.0
"""How often a waiting command retries.

`flock` has no timed variant, so waiting is a poll. One second is short against
the hour a scheduled sync waits and the day a verification waits
(`docs/configuration.md` §5), and long enough that an hour of waiting is 3600
cheap syscalls rather than a spin.
"""


def lock_path(directory: Path | None = None) -> Path:
    """Where the lock lives. Overridable so tests never touch `/run`."""
    return (LOCK_DIRECTORY if directory is None else directory) / LOCK_NAME


def read_holder(path: Path) -> dict[str, Any]:
    """Best-effort: what the holding process recorded about itself.

    Deliberately forgiving. This runs only when a command has already failed to
    acquire the lock, so an unreadable or half-written record must not replace
    "someone else holds the lock" with a parse error — the answer to report is
    the one already known.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        holder = json.loads(raw)
    except ValueError:
        return {}
    return holder if isinstance(holder, dict) else {}


@contextmanager
def exclusive_lock(
    path: Path,
    *,
    command: str,
    wait_seconds: int,
    poll_seconds: float = _POLL_SECONDS,
) -> Iterator[Path]:
    """Hold the exclusive lock for the body, or raise `HFMNT010` (plan §19 item 8).

    Acquired *before* the storage preflight, per plan §13.1 steps 2 and 3: two
    commands running concurrently is the condition this exists to prevent, and
    finding out early costs one syscall.

    `wait_seconds` comes from configuration and is asymmetric by design — a
    scheduled sync waits an hour because the next timer firing is cheap, while a
    quarterly verification waits a day because a legitimately long sync should
    delay it rather than race it (`docs/configuration.md` §5). Zero means try
    once and give up.
    """
    path.parent.mkdir(mode=LOCK_DIRECTORY_MODE, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, LOCK_MODE)
    try:
        _acquire(descriptor, path, command=command, wait_seconds=wait_seconds, poll=poll_seconds)
        try:
            yield path
        finally:
            # Clear the record before releasing, so the next command to fail an
            # acquisition never reports a process that has already finished.
            _write_holder(descriptor, {})
    finally:
        # Closing releases the lock. It is also what releases it when this
        # process is killed, which is the reason the lock is an `flock` and not
        # a file whose existence means something.
        os.close(descriptor)


def _acquire(descriptor: int, path: Path, *, command: str, wait_seconds: int, poll: float) -> None:
    """Poll for the lock until the configured wait is spent."""
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            if time.monotonic() >= deadline:
                raise _refusal(path, command=command, wait_seconds=wait_seconds) from None
            time.sleep(poll)
        else:
            _write_holder(
                descriptor,
                {
                    "command": command,
                    "pid": os.getpid(),
                    "started_at": datetime.now(UTC)
                    .isoformat(timespec="seconds")
                    .replace("+00:00", "Z"),
                },
            )
            return


def _refusal(path: Path, *, command: str, wait_seconds: int) -> SafetyError:
    """Report `HFMNT010`, naming the holder when it left a record."""
    holder = read_holder(path)
    who = (
        f"held by {holder.get('command')} (pid {holder.get('pid')}) "
        f"since {holder.get('started_at')}"
        if holder
        else "the holder left no record"
    )
    message = (
        f"{command} could not acquire the exclusive lock {path} within {wait_seconds}s; {who}. "
        f"Exactly one mutating command runs at a time (`AD-17`)"
    )
    return SafetyError([Problem(code="HFMNT010", message=message, location=str(path))])


def _write_holder(descriptor: int, holder: dict[str, Any]) -> None:
    """Replace the diagnostic record, tolerating a read-only or full `/run`.

    Failing to write it is not a reason to refuse: the lock is held either way,
    and the record only ever improves a message.
    """
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.ftruncate(descriptor, 0)
        if holder:
            os.write(descriptor, json.dumps(holder, sort_keys=True).encode("utf-8"))
    except OSError:  # pragma: no cover - /run is a tmpfs the service owns
        return
