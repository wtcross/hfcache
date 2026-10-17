# Decision 028: `STO-000` lands the primitives it cannot be correct without

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-000`.
- Source: [decision 28 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

It is the first package of Phase 3 but depends on three later
ones: mount and filesystem-type detection (`STO-001`), reading the sentinel
and comparing its id (`STO-002`), and atomic writes (`STO-005`). An
initialization that cannot prove its target is NFS, cannot tell an
initialized archive from unknown content, and cannot write its sentinel
without a torn-write window is not a *guarded* initialization, so those
pieces are here in their minimal form. The packages keep the rest of their
scope: `STO-001` the shared preflight every mutating command runs plus
`doctor`'s mount checks, `STO-002` that preflight's sentinel gate, `STO-005`
the model-aware JSON and reference writers built on `atomic_write_bytes`.

## Provenance and governing evidence

The source entry first appears in
[5a6fa18](https://github.com/wtcross/hfcache/commit/5a6fa1816bedacf014f135468241f99ca42cca60)
(2026-07-25, `STO-000: implement guarded one-time archive initialization and
inspection`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../docs/architecture.md),
[docs/cli.md](../../docs/cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/archive.py](../../src/hfcache/archive.py).

Relevant verification:
[tests/unit/test_archive.py](../../tests/unit/test_archive.py),
[tests/unit/test_archive_init.py](../../tests/unit/test_archive_init.py).
