# The `--json` envelope is a model, not a dict

- Decision identity: 026.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

It is
not durable — nothing on the archive is ever this shape — but it is a contract
with automation, and it was being assembled by hand at each call site with the
`outcome`/`exit_code` agreement enforced by a conditional expression. It is
now `reporting.Envelope`, which refuses an undocumented exit code, an
`outcome` that contradicts it, `success_with_warnings` without warnings, and a
failure carrying no errors. It keeps its own `schema_version`, separate from
the durable schemas, because an invocation record and an archived manifest
change for different reasons.

## Provenance and governing evidence

The source entry first appears in
[49e61af](https://github.com/wtcross/hfcache/commit/49e61af233c9cca40a3e2ec09d69086eca31e011)
(2026-07-25, `configuration validation: implement the error taxonomy and the typed JSON
envelope`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/reporting.py](../../src/hfcache/reporting.py).

Relevant verification: [tests/unit/test_cli.py](../../tests/unit/test_cli.py).
