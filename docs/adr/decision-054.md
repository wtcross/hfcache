# Keep instance repair separate from retention deletion

- Decision identity: 054.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.

## Context, decision and consequences

Repair replaces an instance while preserving revision identity and original
manifest expectations; prune irreversibly removes retained content after its
logical commit. Combining these opposite transaction policies in retention would
blur deletion authority. Repair also has its own isolated cache exception, gates,
reference-switch sequence and crash matrix, so it owns a separate module rather
than growing sync's orchestration.

Post-grace cleanup remains part of the repair transaction. Recovery identifies
due work and invokes its proven repair cleanup; it does not duplicate that policy.
Retired trees become quarantine evidence, never automatic deletion.

## Provenance and governing evidence

The source entry first appears in
[f04aa31](https://github.com/wtcross/hfcache/commit/f04aa31e2b3d6f24753b1f24aac8947b5dab8740)
(2026-07-26, `verification: repair a damaged instance, and finish what a crash left
open`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/recovery.md](../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/repair.py](../../src/hfcache/repair.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).
