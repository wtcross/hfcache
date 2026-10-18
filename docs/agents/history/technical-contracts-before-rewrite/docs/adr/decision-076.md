> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 076: The rename decision 69 deferred is performed, and the index that made it safe now checks itself

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `OPS-008`.
- Source: [decision 76 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Decision 69 rejected
renaming `test_repair.py` as churn against a green suite with the phase
unfinished, and built the executable matrix instead. Both halves of that
reasoning have now expired in its favour: the phase is finished and v0.1.2
is tagged, so the churn argument no longer applies — and the matrix it
built is precisely what makes the rename a mechanical, verified operation
rather than a risk. Every one of the 21 references the matrix holds to the
module resolves by import, so a missed rename is a failed suite, not a
silent gap. The deferral was correct then and paying it now is correct for
the same reason: the safety was built first.

The name matters because decision 69 said it did: the file holds the
publication boundaries, the prune boundaries, the recovery remedies, and
the repair switches — 25 provoked crash injections — and "nothing in
`test_repair.py`'s name suggests" that was the stated defect. The matrix
made the contents *discoverable*; the rename makes them *legible* from the
directory listing. Sequenced first in this closeout so `VER-009`'s new
tests land against the final module names and the matrix is edited once.

The second half is the same defect decision 69 fixed, one layer up.
`MODULES` claimed, in a comment, to be "every module named in `MATRIX`" —
and it listed `tests.unit.test_verification`, which no row references. The
comment was an honor-system claim sitting in the very file whose docstring
says "a coverage claim in a comment rots silently. This one cannot." It
had rotted. The fix is the file's own medicine: a test derives the module
set from `MATRIX` and asserts `set(MODULES)` equals it, which closes both
drift directions — a module the matrix gains must be added, and a module
it loses must be removed. `test_verification` is dropped rather than a row
added, because the audit stands: the §26.6 point that touches verification
("during quarterly verification") is covered from `test_verify_command`,
where the interruption tests actually live.

## Later history and current interpretation

This performs the rename deferred by [decision 69](../../../../../adr/decision-069.md). Current
evidence links use `test_crash_injection.py`; the old filename is retained in
the reasoning as historical context.

## Provenance and governing evidence

The source entry first appears in
[eebd7af](https://github.com/wtcross/hfcache/commit/eebd7af61b060f88d1a6e806a6d7c06d46a6f947)
(2026-07-27, `OPS-008: name the crash-injection file for what it holds`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents:
[docs/agents/conventions.md](../../../../conventions.md),
[docs/agents/history/plan.md](../../../plan.md).

Implementation or shipped-artifact evidence:
[tests/unit/test_crash_injection.py](../../../../../../tests/unit/test_crash_injection.py).

Relevant verification:
[tests/unit/test_failure_matrix.py](../../../../../../tests/unit/test_failure_matrix.py).
