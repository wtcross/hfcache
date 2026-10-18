# Remove prune references before tombstoning content

- Decision identity: 004.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Context, decision and consequences

Removing content before its retained reference leaves a visible ref pointing at
trash and violates FS-10. Remove the reference first; the persisted PrunePlan
already identifies the tree for recovery. Cache deletion remains before logical
commit, rollback restores all retained trees/manifests then refs last, and original
manifests remain recoverable from owned trash. Post-commit recovery completes audit
and cleanup rather than republishing. This ordering keeps deletion and crash
recovery explicit without inventing a second commit point.

## Provenance and governing evidence

The source entry first appears in
[d1d2f00](https://github.com/wtcross/hfcache/commit/d1d2f007e32ccb3b037c89df988213e67a2e52df)
(2026-07-24, `contract definition: define transaction and crash-recovery boundaries`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/recovery.md](../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/retention.py](../../src/hfcache/retention.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).
