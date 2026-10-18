# Delay stale-staging recovery under explicit ownership proof

- Decision identity: 005.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Context, decision and consequences

`sync.stale_staging_age_hours` defaults to 24 and permits 1–8760 hours. Age alone
never authorizes cleanup: transaction-shaped identity, journal ownership and
unambiguous state remain required. The delay prevents reclaiming another active
operator's staging merely because it looks unfinished. The separately documented
supervised zero-age exception needs exact stopped-run/empty-staging/lock proof
and has no public CLI/API override; it does not change automatic policy.

## Provenance and governing evidence

The source entry first appears in
[d1d2f00](https://github.com/wtcross/hfcache/commit/d1d2f007e32ccb3b037c89df988213e67a2e52df)
(2026-07-24, `contract definition: define transaction and crash-recovery boundaries`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents:
[docs/configuration.md](../configuration.md),
[docs/recovery.md](../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/config.py](../../src/hfcache/config.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_recovery_planning.py](../../tests/unit/test_recovery_planning.py).
