# Name crash-injection tests clearly and verify the coverage index

- Decision identity: 076.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Decision, context, and consequences

The crash-injection suite covers publication and prune boundaries, recovery
remedies and repair switches. Name it `test_crash_injection.py` so its purpose is
visible in the directory listing. The earlier `test_repair.py` name hid that scope.
The executable failure matrix introduced by [decision 69](decision-069.md)
resolves its references by import, making a missed rename fail verification.
That coverage made the rename mechanical without weakening crash tests.

The matrix's `MODULES` index must equal the module set derived from `MATRIX`.
An independently maintained comment claiming completeness had drifted: it listed
`test_verification` although no row referenced that module. Assert equality in
both directions instead of adding an unsupported coverage row. Quarterly
verification interruption evidence belongs to `test_verify_command`, where those
tests actually live.

## Later history and current interpretation

This performs the rename deferred by [decision 69](decision-069.md). Current
evidence links use `test_crash_injection.py`; the old filename is retained in
the reasoning as historical context.

## Provenance and governing evidence

The source entry first appears in
[eebd7af](https://github.com/wtcross/hfcache/commit/eebd7af61b060f88d1a6e806a6d7c06d46a6f947)
(2026-07-27, `operational tooling: name the crash-injection file for what it holds`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents:
[current technical contract](../architecture.md).

Implementation or shipped-artifact evidence:
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).

Relevant verification:
[tests/unit/test_failure_matrix.py](../../tests/unit/test_failure_matrix.py).
