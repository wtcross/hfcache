# Decision 053: Evidence for a path a later checkpoint moves carries no `_path` suffix

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `VER-006`.
- Source: [decision 53 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Decision 42 made evidence mechanically checkable
with a key-naming convention: `_path` means "must still exist", `_absent`
means "must not". `evidence_problems` enforces it, and `HFTXN003` — journal
contradicts filesystem — stops the machine (§7.9).

Three checkpoints recorded a `_path` for something the *next* checkpoint in
their own sequence deliberately renames away: publication's `staging_built`
named `staging_tree_path`, which checkpoint 5 renames into `published/`;
prune's `tree_tombstoned` and `manifest_tombstoned` named paths under
`.store/trash`, which checkpoint 9 removes. A journal that got past those
steps therefore contradicted the filesystem *by design*, and recovery
reported `HFTXN003` for the exact states §7.3 and §7.4 give roll-forward
resolutions for. That is why the carried-in remedies could not simply be
added: the evidence had to stop lying first.

The rule is now: **evidence whose subject a later checkpoint in the same
operation moves is recorded without a path suffix.** The value is still
recorded and still re-observable by a person; it is just not asserted to
still exist. Nothing loses the ability to *locate* anything, because
`FS-18` guarantees every transaction area is derivable from the transaction
id — which is how `_staging_remediation` and the prune remedies find their
directories already.

Repair follows the same rule for `corrupt_instance`, `original_manifest`,
`isolated_cache`, `snapshot`, and `staging_tree`, all of which checkpoints
14, 16, or 17 move — and it matters more there than anywhere, because a
repair journal stays open for the whole seven-day grace and its evidence is
re-checked by every `recover` in that window.

## Later history and current interpretation

[Decision 56](decision-056.md) extends the same evidence rule to pending
manifests removed during committed staging cleanup.

## Provenance and governing evidence

The source entry first appears in
[f04aa31](https://github.com/wtcross/hfcache/commit/f04aa31e2b3d6f24753b1f24aac8947b5dab8740)
(2026-07-26, `VER-006: repair a damaged instance, and finish what a crash left
open`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/schemas.md](../schemas.md).

Implementation or shipped-artifact evidence:
[src/hfcache/transactions.py](../../src/hfcache/transactions.py),
[src/hfcache/repair.py](../../src/hfcache/repair.py).

Relevant verification:
[tests/unit/test_transactions.py](../../tests/unit/test_transactions.py),
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).
