# A failed report may retain warnings observed before another repository failed

- Decision identity: 095.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-10.

## Decision, context, and consequences

Queue-wide planning makes an old reachable
defect immediate: one repository can complete with a dependency or capacity
warning and a later repository can fail, but both durable `RunReport` and
CLI `Envelope` validators previously required warnings if and only if the
outcome was `success_with_warnings`. The command then failed while trying to
describe the failure and lost its report. `success` still forbids warnings
and `success_with_warnings` still requires them; `failed` now permits them
alongside required errors. The field set and JSON shape do not change, so
schema version 1 remains; this is a field-combination widening like decision
78 and receives the same cross-version release drill. A pre-0.1.4 binary
cannot parse a mixed failed-plus-warning report, so rollback requires the
newest report to have a previously accepted combination or a later
compatible sync report to supersede it.

## Later history and current interpretation

This is a schema-1 acceptance widening, not universal backwards compatibility.
Its mixed failed-plus-warning rollback constraint is independent of the other
release barriers in the release runbook.

## Provenance and governing evidence

The source entry first appears in
[54e4671](https://github.com/wtcross/hfcache/commit/54e4671cec9cd2a2f82bfa73372e78478d29e7f4)
(2026-08-10, `synchronization: download ahead while repositories hash`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/cli.md](../cli.md),
[recorded deployment scope](../deployment-status.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py),
[src/hfcache/reporting.py](../../src/hfcache/reporting.py).

Relevant verification:
[tests/unit/test_models.py](../../tests/unit/test_models.py),
[tests/unit/test_cli.py](../../tests/unit/test_cli.py).
