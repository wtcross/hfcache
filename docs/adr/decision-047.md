# Classify content that cannot be read while hashing

- Decision identity: 047.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.

## Decision, context, and consequences

The sync transaction contract hashes newly introduced objects and
verification requires a hash failure to prevent publication, but the taxonomy had no
code for the failure itself. The nearby ones are all wrong: `HFSYN001` is the
local-only completeness check specifically, `HFSYN003` is a size mismatch,
`HFSYN004` is an unsafe path, `HFSYN005` is staging construction — which has
not started yet before staging.

`HFVER006` ("object could not be read") describes the condition exactly and
is still wrong, because it exits `40`. Nothing has been published when ingestion hashing
runs, so no archive content is wrong; the run failed and the next one will
retry. That is a `30`, which is what put the code in the `HFSYN` family.

Added to `docs/cli.md` §5.3. `tests/unit/test_taxonomy.py`
reads that table, so the code is covered in both directions the moment it is
published.

## Provenance and governing evidence

The source entry first appears in
[45f1ccf](https://github.com/wtcross/hfcache/commit/45f1ccf55656760db38e5242f3ef827bd07ef6de)
(2026-07-26, `Hub access: hash every newly introduced unique physical object`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/hashing.py](../../src/hfcache/hashing.py),
[src/hfcache/taxonomy.py](../../src/hfcache/taxonomy.py).

Relevant verification:
[tests/unit/test_hashing.py](../../tests/unit/test_hashing.py),
[tests/unit/test_taxonomy.py](../../tests/unit/test_taxonomy.py).
