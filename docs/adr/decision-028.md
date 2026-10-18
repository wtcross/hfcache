# Guarded initialization requires storage and atomic-write proof

- Decision identity: 028.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Context, decision and consequences

Initialization must prove NFS target identity/type, distinguish an existing
sentinel from unknown content and write the sentinel without a torn-write window.
Those storage and atomic-write primitives are prerequisites, not optional checks.
The shared preflight/doctor readers and model-aware JSON/reference writers reuse
these primitives. Initialization remains explicit, confirmed and known-layout-only;
it never becomes recovery for an existing archive.

## Provenance and governing evidence

The source entry first appears in
[5a6fa18](https://github.com/wtcross/hfcache/commit/5a6fa1816bedacf014f135468241f99ca42cca60)
(2026-07-25, `storage primitives: implement guarded one-time archive initialization and
inspection`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/archive.py](../../src/hfcache/archive.py).

Relevant verification:
[tests/unit/test_archive.py](../../tests/unit/test_archive.py),
[tests/unit/test_archive_init.py](../../tests/unit/test_archive_init.py).
