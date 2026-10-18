> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 104: Confirmed operator cancellation may replace the empty-staging age heuristic

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-09-14.
- Original work package: `QUA-002`.
- Source: [decision 104 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The operator explicitly chose to pause the active
sync, clean quarantine, and restart with its download cache preserved.
Ordinary recovery would wait 24 hours even though that exact writer was
deliberately stopped. For the identified run only, service/PID termination,
the exclusive writer lock, exact journal/run/repository/commit evidence,
and an empty `staging_created`-only publication permit the installed
recovery planner's explicit zero-hour threshold. Reject other unfinished
work, review the plan, recompute it under the standard preflight/lock, and
apply through the existing journaled recovery code. No configuration or
timestamps are changed; automatic recovery retains its age policy. The
cache and published references remain intact. Recovery creates an ordinary
empty quarantine entry that the explicit cleanup command can remove.
Valid early download journals have a null publication ID, so cleanup must
accept that existing shape when terminal recovery proves ownership.
**Rejected:** killing the writer and deleting staging by hand; inventing
timestamps or journal identities to satisfy a guard; globally shortening
the age policy; and broadening the exception to populated or later-stage
interrupted publications. No durable format changes are introduced.

## Later history and current interpretation

This is a narrowly evidenced operator cancellation, not a new automatic
recovery-age policy or a general command to stop the writer. [Decision
105](../../../../../adr/decision-105.md) separately refines unrelated completed-history handling
during cleanup.

## Provenance and governing evidence

The source entry first appears in
[7b5e4e2](https://github.com/wtcross/hfcache/commit/7b5e4e2a0866937c4f3eed5f1d60642d643135bf)
(2026-09-14, `QUA-002: clean recovered interrupted download staging`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/recovery.md](../../../../../recovery.md),
[docs/architecture.md](../../../../../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/recovery.py](../../../../../../src/hfcache/recovery.py),
[src/hfcache/quarantine.py](../../../../../../src/hfcache/quarantine.py).

Relevant verification:
[tests/unit/test_quarantine.py](../../../../../../tests/unit/test_quarantine.py).
