# Decision 004: Prune removes the per-SHA reference before tombstoning the tree

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `ARC-006`.
- Source: [decision 4 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §15.2 ordered these the other way — tombstone the
tree and manifest at step 8, remove `refs/revisions/<sha>.json` at step 9.
That leaves a window in which a reference names a tree that has already been
renamed into trash, which breaks the invariant that every existing reference
resolves (`FS-10`) and would be visible to `verify` and `repair`, both of
which resolve per-SHA refs. Recovery never needed the reference to find the
tree: the persisted `PrunePlan` already names it. Every property plan §15.2
asserts is preserved — cache deletion still happens while all six revisions
are published, rollback before the commit point still restores six revisions,
and the complete manifest is still recoverable from trash. Plan §15.2 steps
8–9 are updated in this commit.

## Provenance and governing evidence

The source entry first appears in
[d1d2f00](https://github.com/wtcross/hfcache/commit/d1d2f007e32ccb3b037c89df988213e67a2e52df)
(2026-07-24, `ARC-006: define transaction and crash-recovery boundaries`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/recovery.md](../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/retention.py](../../src/hfcache/retention.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).
