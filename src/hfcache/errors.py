"""Exit classifications for the command-line interface.

The values here are the contract in `docs/cli.md` §3. They are stable: a code is
never reused for a different condition, and `1` and `2` are deliberately unused
because Typer reserves them for usage errors — a scheduler must be able to tell a
malformed command line from an application outcome.
"""

from enum import IntEnum

__all__ = ["ExitCode"]


class ExitCode(IntEnum):
    """Aggregate outcome of a command.

    Aggregation rule (`docs/cli.md` §3): `CONFIGURATION` and `SAFETY` abort
    before per-repository work begins, so they never co-occur with the rest.
    Among the remaining three, the reported code is the first of `INTEGRITY`,
    `RETENTION`, `SYNC` that occurred — ordered by operator urgency.
    """

    SUCCESS = 0
    CONFIGURATION = 10
    SAFETY = 20
    SYNC = 30
    INTEGRITY = 40
    RETENTION = 50
