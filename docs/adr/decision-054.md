# Decision 054: `repair.py` added beyond plan §7's module list

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `VER-006`.
- Source: [decision 54 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The fourth module added this way, after `preflight.py` (33), `archive.py`
(36), and `locking.py` (40). §7 permits consolidating boundaries "where
implementation remains small" and requires Hub access, storage mutation,
retention, and verification stay independently testable; it does not say
where repair goes.

`retention.py` was the obvious candidate and is wrong: repair does not
remove a revision, it replaces an instance of one, and the two transactions
have opposite commit semantics — a prune's commit point makes deletion
irreversible, while a repair never deletes at all. `sync.py` was the other
candidate and is already the largest module in the project. Repair has its
own §7.5 checkpoint sequence, its own two gates, its own crash matrix, and
the only isolated cache in the design (`FS-14`'s single exception), so it
is its own module. `docs/plan.md` §7's listing is amended in this commit.

The post-grace cleanup lives there too rather than in `recovery.py`, and
recovery calls into it. Checkpoints 16-18 are steps of the *repair*
transaction — recovery's job is to notice they are due and to run them, not
to know how.

## Provenance and governing evidence

The source entry first appears in
[f04aa31](https://github.com/wtcross/hfcache/commit/f04aa31e2b3d6f24753b1f24aac8947b5dab8740)
(2026-07-26, `VER-006: repair a damaged instance, and finish what a crash left
open`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../docs/architecture.md),
[docs/recovery.md](../../docs/recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/repair.py](../../src/hfcache/repair.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).
