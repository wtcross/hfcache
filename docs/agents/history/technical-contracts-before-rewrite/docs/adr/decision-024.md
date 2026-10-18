> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 024: A partially implemented command reports what it probed, not a placeholder

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-006`.
- Source: [decision 24 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`doctor` is specified with fourteen checks; Phase 2 can
perform three of them, because the rest need the storage layer or the Hub
adapter. Two ways to handle that were rejected: emitting the missing checks
with a `skipped` outcome and a "not implemented yet" detail, which puts
development state into operator-facing output, and emitting them as `pass`,
which is a lie. They are simply absent until the package that performs them
lands, and the `checks[]` array is ordered and open-ended so appending is the
natural way to add one. `--read-only` is the exception and is *not*
development state: `docs/cli.md` §2 requires it to say that hardlink, rename,
and ref-replacement capability are unproven, so those three entries are real
output that will still be there at v1. The same rule governs `plan` and
`status`: each reports the fields it can determine and omits the rest, and the
checkbox above names the work package that completes each one.

## Later history and current interpretation

The phase-by-phase omissions describe implementation rollout, not a present-day
permission to omit required checks. Current command payloads and the complete
check table are governed by `docs/cli.md`.

## Provenance and governing evidence

The source entry first appears in
[28b07c3](https://github.com/wtcross/hfcache/commit/28b07c3c0bfb8fa20d9c97b3a8a2598ccbcc2142)
(2026-07-25, `CFG-006: implement the read-only portions of doctor, plan, and
status`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../../../../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/cli.py](../../../../../../src/hfcache/cli.py),
[src/hfcache/preflight.py](../../../../../../src/hfcache/preflight.py).

Relevant verification:
[tests/unit/test_readonly_commands.py](../../../../../../tests/unit/test_readonly_commands.py).
