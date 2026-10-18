> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 002: `docs/cli.md` added beyond the plan §7 documentation set

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `ARC-005`.
- Source: [decision 2 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Same reasoning as decision 1. `operations.md` is the Phase 8
runbook document — task-oriented, "how do I rotate a revision" — and is the
wrong home for a reference contract that Phase 2 code is written against.
Keeping the command surface, JSON envelope, exit-code aggregation, and the
complete error taxonomy in one place also means `CFG-007` has a single
normative source. Plan §7's `docs/` listing is updated in this commit to
include both `cli.md` and `schemas.md`; the deviation is now final.

## Provenance and governing evidence

The source entry first appears in
[00c5957](https://github.com/wtcross/hfcache/commit/00c59571e747ca03e5f788aabc9e18ba9627a563)
(2026-07-24, `ARC-005: define CLI commands, JSON output, and exit codes`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../../../../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/reporting.py](../../../../../../src/hfcache/reporting.py),
[src/hfcache/taxonomy.py](../../../../../../src/hfcache/taxonomy.py).

Relevant verification:
[tests/unit/test_taxonomy.py](../../../../../../tests/unit/test_taxonomy.py).
