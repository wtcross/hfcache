# Decision 093: A hardlink carries same-operation content evidence only with exact object identity

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-10.
- Original work package: `SYNC-006`.
- Source: [decision 93 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The ingestion hash now obtains
`(device, inode, size)` from the descriptor whose bytes it reads and keeps
that identity only in memory. Publication may avoid rereading a hardlink
because the link is the same inode, but only after both source and landed
destination are re-proven against that evidence; any mismatch removes the
unproven entry and stops before rename. This saves one complete logical-byte
read — about 25 hours for the observed 10.65 TB repository — without
weakening `AD-18`. Copy mode is deliberately different: its destination is
a new inode, so it remains hashed and compared with the ingestion digest.
**Rejected:** merely deleting the second hash with no identity proof, which
would make a snapshot-path replacement publish bytes the manifest did not
describe. **Rejected:** persisting device or inode values, because they are
transient filesystem evidence and unsafe to reuse across runs.

## Later history and current interpretation

This refines AD-18 for hardlinks only: the optimization carries exact in-memory
same-operation object identity. It does not authorize digest reuse from a
different inode, a previous run, or a copied destination.

## Provenance and governing evidence

The source entry first appears in
[92ebdba](https://github.com/wtcross/hfcache/commit/92ebdba2d1462c0febf0333a4da161e75f459dec)
(2026-08-10, `SYNC-006: avoid redundant hardlink content reads`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../docs/architecture.md),
[docs/security.md](../../docs/security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/hashing.py](../../src/hfcache/hashing.py),
[src/hfcache/publication.py](../../src/hfcache/publication.py).

Relevant verification:
[tests/unit/test_publication.py](../../tests/unit/test_publication.py),
[tests/unit/test_hashing.py](../../tests/unit/test_hashing.py).
