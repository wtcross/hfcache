# Decision 005: `sync.stale_staging_age_hours` added to the configuration schema

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `ARC-006`.
- Source: [decision 5 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §13.3 requires that stale staging directories be
reclaimed only when they "exceed a configurable age", but the §9 schema had no
key for it, so the requirement was unimplementable as written. Added with a
24-hour default and a `1..8760` range. The delay is not the safety mechanism
on its own — reclamation also requires a transaction-ID-shaped name and an
existing journal — it exists so a concurrent operator command cannot have its
working directory reclaimed underneath it. Plan §9 and §9.1 are updated in
this commit.

## Later history and current interpretation

The ordinary configured age policy still applies. [Decision
104](decision-104.md) records one identified, confirmed operator cancellation
using the existing recovery planner with a zero-hour threshold; it does not
change the automatic policy.

## Provenance and governing evidence

The source entry first appears in
[d1d2f00](https://github.com/wtcross/hfcache/commit/d1d2f007e32ccb3b037c89df988213e67a2e52df)
(2026-07-24, `ARC-006: define transaction and crash-recovery boundaries`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents:
[docs/configuration.md](../configuration.md),
[docs/recovery.md](../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/config.py](../../src/hfcache/config.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_recovery_planning.py](../../tests/unit/test_recovery_planning.py).
