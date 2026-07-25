"""The error taxonomy, and the rule that turns several failures into one exit.

`docs/cli.md` §3 and §5 and `docs/configuration.md` §8 are the contract. Codes
are stable across releases: a code is never reused for a different condition, and
a retired condition retires its code.

Two things live here rather than being spread across the modules that raise:

* **Every code's exit classification, in one table.** A code's prefix determines
  its classification, so a raise site cannot pair `HFVER003` with exit `30` by
  accident. `tests/unit/test_taxonomy.py` reads the published tables out of the
  documentation and fails if either side gains an entry the other lacks, so the
  taxonomy cannot drift away from the document that defines it.
* **Aggregation.** A run that touched several repositories can end holding a
  sync failure, an integrity failure, and a retention failure at once. Exactly
  one number reaches the scheduler, and which one is a decision about what an
  operator should look at first — not an accident of which failure happened last.
"""

from typing import TYPE_CHECKING, Final

from hfcache.errors import ExitCode

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = [
    "AGGREGATION_ORDER",
    "PREFIX_EXIT_CODES",
    "WARNING_PREFIXES",
    "aggregate_exit_code",
    "classify",
    "is_warning",
]

PREFIX_EXIT_CODES: Final = {
    "HFCFG": ExitCode.CONFIGURATION,
    "HFARG": ExitCode.CONFIGURATION,
    "HFMNT": ExitCode.SAFETY,
    "HFTXN": ExitCode.SAFETY,
    "HFHUB": ExitCode.SYNC,
    "HFSYN": ExitCode.SYNC,
    "HFVER": ExitCode.INTEGRITY,
    "HFRET": ExitCode.RETENTION,
}
"""Which exit classification each code family carries (`docs/cli.md` §5)."""

WARNING_PREFIXES: Final = frozenset({"HFWRN", "HFDEP"})
"""Families that never change a `0` exit on their own (`docs/cli.md` §5.6)."""

AGGREGATION_ORDER: Final = (ExitCode.INTEGRITY, ExitCode.RETENTION, ExitCode.SYNC)
"""Operator urgency: possible corruption, then degraded retention, then stale content.

`docs/cli.md` §3. `CONFIGURATION` and `SAFETY` abort before per-repository work
begins, so they never co-occur with these three and are not part of the ordering.
"""

_CODE_LENGTH = 8
"""Five letters of prefix and three digits, e.g. `HFVER001`."""


def _prefix(code: str) -> str:
    if len(code) != _CODE_LENGTH or not code[5:].isdigit():
        message = f"{code!r} is not a taxonomy code; expected five letters and three digits"
        raise ValueError(message)
    return code[:5]


def is_warning(code: str) -> bool:
    """Whether this code is a warning rather than a failure."""
    return _prefix(code) in WARNING_PREFIXES


def classify(code: str) -> ExitCode:
    """Return the exit classification a code carries.

    A warning classifies as `SUCCESS`, which is the whole point of the warning
    families: `HFDEP001` is written to the manifest, surfaced by `status`, and
    leaves the exit code at `0` when nothing else failed (`AD-07`).
    """
    prefix = _prefix(code)
    if prefix in WARNING_PREFIXES:
        return ExitCode.SUCCESS
    classification = PREFIX_EXIT_CODES.get(prefix)
    if classification is None:
        message = f"{code!r} has no known family; every code belongs to one (`docs/cli.md` §5)"
        raise ValueError(message)
    return classification


def aggregate_exit_code(codes: Iterable[str]) -> ExitCode:
    """Reduce every classification a run encountered to the one it exits with.

    `CONFIGURATION` and `SAFETY` win outright when present, because they abort
    before per-repository work and so describe a run that did not happen rather
    than one that partly did. Otherwise the first of `AGGREGATION_ORDER` that
    occurred wins.

    Aggregation hides nothing: every code encountered is still listed in the
    envelope's `errors` array, and this function only decides which single
    number the scheduler sees (`docs/cli.md` §3).
    """
    encountered = {classify(code) for code in codes}
    for aborting in (ExitCode.CONFIGURATION, ExitCode.SAFETY):
        if aborting in encountered:
            return aborting
    for classification in AGGREGATION_ORDER:
        if classification in encountered:
            return classification
    return ExitCode.SUCCESS
