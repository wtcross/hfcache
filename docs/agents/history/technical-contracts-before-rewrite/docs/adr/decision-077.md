> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 077: The docs move to the code, because the built mechanism already delivers §7.4's semantics and a failure-time checkpoint buys recovery nothing

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `RET-009`.
- Source: [decision 77 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Two ways to reconcile "records a `cleanup_deferred`
checkpoint" with an implementation that records no such thing: make the
code write the checkpoint, or make the docs describe the mechanism. The
second is chosen, and not because it is less work.

What §7.4's failure regime actually promises is behavioural: never
republish past the commit point, and retry only post-commit cleanup later.
The implementation delivers exactly that, through the journal itself — a
failure in steps 8–10 leaves the journal open at the last recorded
checkpoint, and an open prune journal that has reached
`prune_logically_committed` *is* the durable statement that cleanup is
outstanding. `recover` derives everything it needs from two facts it
already has: which checkpoints were reached, and whether the tombstone is
present. A `cleanup_deferred` checkpoint recorded during the failure would
restate the conjunction of those facts — and a marker written *while
failing* is evidence of the weakest kind, since the failure that prompted
it can just as easily take the marker down with it. The open journal
requires no successful write at failure time; it is already on disk.

Removing the permit instead of keeping a dead vocabulary entry follows
from what the vocabulary check is for: `HFTXN002` exists to refuse "a
journal no valid execution produces", and no valid execution has ever
produced this checkpoint — its only writer in the entire tree was the test
asserting it was permitted. The permit was, in miniature, the same
honor-system defect as decision 76's module list: machinery attesting to a
behaviour nothing exhibits. The inverted test is the falsifiable form —
if a future release starts recording the checkpoint without widening the
vocabulary deliberately, the suite fails.

The removal is safe against every real archive for the same reason the
permit was dead: no journal has ever contained the checkpoint (the live
archive's 34 were scanned, zero matches), so no existing journal becomes
refusable. Re-adding it later, should a release ever want the checkpoint
recorded, is a one-line permit plus the standard cross-format note — the
same widening path `containers_removed` took at `RET-008`.

## Later history and current interpretation

This supersedes the temporary `cleanup_deferred` permit described in [decision
64](../../../../../adr/decision-064.md). Later checkpoint widenings, including [decision
96](../../../../../adr/decision-096.md), require their own order and rollback analysis.

## Provenance and governing evidence

The source entry first appears in
[8f0af80](https://github.com/wtcross/hfcache/commit/8f0af80b55b19400b5ab97fd5d75d92c772e9787)
(2026-07-27, `RET-009: reconcile §7.4's cleanup_deferred claim with the
implementation`). The decision text above preserves the complete reasoning in
the current historical log, including its recorded alternatives and
consequences.

Current governing documents: [docs/architecture.md](../../../../../architecture.md),
[docs/recovery.md](../../../../../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/transactions.py](../../../../../../src/hfcache/transactions.py),
[src/hfcache/recovery.py](../../../../../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_transactions.py](../../../../../../tests/unit/test_transactions.py),
[tests/unit/test_retention.py](../../../../../../tests/unit/test_retention.py).
