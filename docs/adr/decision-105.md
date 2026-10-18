# Decision 105: Only journals supplying deletion authority need current checkpoint order

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-09-14.
- Original work package: `QUA-003`.
- Source: [decision 105 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The live cleanup preview correctly stopped before
deletion but rejected two unrelated, completed historical prune journals.
Parsing and resolution checks still apply to every inventory record;
unsupported fields, unreadable records, and unfinished transactions still
refuse cleanup. Full checkpoint-order checks apply to the selected source
publications and their matching committed recovery proofs. Unrelated
completed history is preserved and cannot grant deletion authority, so its
older checkpoint sequence must not prevent an independently proven cleanup.
This follows normal recovery's treatment of already resolved journals and
changes no durable format or source evidence.

## Later history and current interpretation

This qualifies [decision 103](decision-103.md): parsing and resolution checks
remain global, while full current checkpoint-order validation is confined to
selected source publications and their committed recovery proofs. Unrelated
completed journals cannot authorize deletion.

## Provenance and governing evidence

The source entry first appears in
[c2b52ff](https://github.com/wtcross/hfcache/commit/c2b52ffbfbdd72e7de561c12f63b552511c22e67)
(2026-09-14, `QUA-003: accept unrelated completed legacy journals`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/recovery.md](../recovery.md),
[docs/architecture.md](../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/quarantine.py](../../src/hfcache/quarantine.py).

Relevant verification:
[tests/unit/test_quarantine.py](../../tests/unit/test_quarantine.py).
