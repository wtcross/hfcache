# Organize integration coverage with its shared fixtures

- Decision identity: 069.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Context, decision and consequences

Hermetic unit and integration behaviors can share one module when they depend
on the same fake Hub, layout and policy fixtures. Splitting directories solely by
unit/integration classification would duplicate fixtures or impose a larger shared
conftest without improving coverage. Pure retention-order assertions and complete
publish/prune cycles can remain beside each other.

An executable failure-matrix index makes publication/prune/repair/recovery crash
coverage discoverable and verifies that every named covering test still exists.
Directory names alone do not prove behavior. The historical alternative of moving
all integration tests was rejected because it separated tests from their subject;
the crash suite now has the descriptive `test_crash_injection.py` name, while the
shared-fixture organization and executable matrix remain.

## Provenance and governing evidence

The source entry first appears in
[69323a9](https://github.com/wtcross/hfcache/commit/69323a95a4fc932aaf7e53f91a285de9d6a0e0e9)
(2026-07-27, `operational tooling: close §26.6's failure-injection matrix`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents:
[current technical contract](../architecture.md).

Implementation or shipped-artifact evidence:
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).

Relevant verification:
[tests/unit/test_failure_matrix.py](../../tests/unit/test_failure_matrix.py).
