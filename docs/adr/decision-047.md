# Decision 047: `HFSYN009` added for content that cannot be read while hashing

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `HUB-007`.
- Source: [decision 47 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §13.2 step 9 hashes newly introduced objects and
§16.1 requires a hash failure to prevent publication, but the taxonomy had no
code for the failure itself. The nearby ones are all wrong: `HFSYN001` is the
local-only completeness check specifically, `HFSYN003` is a size mismatch,
`HFSYN004` is an unsafe path, `HFSYN005` is staging construction — which has
not started yet at step 9.

`HFVER006` ("object could not be read") describes the condition exactly and
is still wrong, because it exits `40`. Nothing has been published when step 9
runs, so no archive content is wrong; the run failed and the next one will
retry. That is a `30`, which is what put the code in the `HFSYN` family.

Added to `docs/cli.md` §5.3 in this commit. `tests/unit/test_taxonomy.py`
reads that table, so the code is covered in both directions the moment it is
published.

## Provenance and governing evidence

The source entry first appears in
[45f1ccf](https://github.com/wtcross/hfcache/commit/45f1ccf55656760db38e5242f3ef827bd07ef6de)
(2026-07-26, `HUB-007: hash every newly introduced unique physical object`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../docs/cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/hashing.py](../../src/hfcache/hashing.py),
[src/hfcache/taxonomy.py](../../src/hfcache/taxonomy.py).

Relevant verification:
[tests/unit/test_hashing.py](../../tests/unit/test_hashing.py),
[tests/unit/test_taxonomy.py](../../tests/unit/test_taxonomy.py).
