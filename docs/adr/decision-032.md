# Decision 032: A write that fails after every check passed is `HFMNT008`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-000`.
- Source: [decision 32 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Everything `archive init` proves beforehand is a read, so a
server-side read-only export presenting `rw` client options, a reached
dataset quota, or the NAS going away mid-command are all discovered only by
writing. Without a mapping those surface as an `OSError` traceback from the
middle of a half-created layout. `docs/cli.md` §5.2 defines `HFMNT008` as a
required directory being missing or failing the effective-write probe, which
is the same condition observed a different way, so the whole mutation is
wrapped and reported under it at exit `20`. The message names the failing
path and points at `--inspect`, because decision 30 is what makes the retry
safe.

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
