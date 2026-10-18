# Preserve unknown journal fields while rejecting unknown model keys

- Decision identity: 020.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

A blanket unknown-key preservation rule would contradict the schema contract’s
`extra="forbid"`. The contradiction is narrower than it looks: manifests are immutable,
references are replaced wholesale, and the catalog is rebuilt from scratch, so
the transaction journal is the only artifact that is ever read, modified, and
written back — the only place an unknown key could be destroyed. Every model
forbids unknown keys and reports them by location, which satisfies "reported
and never silently dropped". The preservation half is a journal-rewrite
concern and belongs to `storage primitives`, which is where that rewrite is implemented.

## Later history and current interpretation

The journal preservation exception is implemented by `transactions.JournalFile`;
model-level `extra="forbid"` remains the general rule. Preserved unknown journal
fields are reported, not permission to perform an unsupported mutation.

## Provenance and governing evidence

The source entry first appears in
[2133496](https://github.com/wtcross/hfcache/commit/21334967781eef8ee37600ed63fad4e42e404180)
(2026-07-25, `configuration validation: implement the durable manifest and report models`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md).

Implementation or shipped-artifact evidence:
[src/hfcache/transactions.py](../../src/hfcache/transactions.py),
[src/hfcache/models.py](../../src/hfcache/models.py).

Relevant verification:
[tests/unit/test_transactions.py](../../tests/unit/test_transactions.py).
