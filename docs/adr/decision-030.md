# Decision 030: A leftover `.tmp-` sibling is part of the known-empty layout contract

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-000`.
- Source: [decision 30 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

§6.2 permits retrying a failed initialization once
`--inspect` confirms the partial paths match the contract, but a crash
between the sentinel's temporary write and its rename leaves a file the
contract did not name — so the retry would refuse as "unknown content" and
the archive could never be initialized without manual cleanup. Writing the
sentinel in place instead was rejected: `O_EXCL` makes its *appearance*
atomic but not its *contents*, and a truncated sentinel is worse than a
stray temporary, because it looks like an initialized archive. The temporary
is therefore recognised by its `<name>.tmp-<16 hex>` grammar, reported by
`--inspect`, and removed by the retry. It is the only deletion this command
performs and it is on a file the command owns, so `FS-19` is intact.

## Provenance and governing evidence

The source entry first appears in
[5a6fa18](https://github.com/wtcross/hfcache/commit/5a6fa1816bedacf014f135468241f99ca42cca60)
(2026-07-25, `STO-000: implement guarded one-time archive initialization and
inspection`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/archive.py](../../src/hfcache/archive.py).

Relevant verification:
[tests/unit/test_archive.py](../../tests/unit/test_archive.py),
[tests/unit/test_archive_init.py](../../tests/unit/test_archive_init.py).
