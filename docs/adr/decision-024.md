# Report established checks without inventing capability

- Decision identity: 024.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Context, decision and consequences

Operator diagnostics must describe supported checks and observed evidence, not
implementation status or fabricated passes. The current complete ordered check
table is governed by `docs/cli.md`; required checks cannot be silently omitted.
Read-only diagnostics explicitly report hardlink, atomic rename and reference
replacement as unproven because they omit write probes. That is a real capability
limit rather than a successful test. Status and planning likewise report only
facts they can establish and preserve explicit unknown confidence.

## Provenance and governing evidence

The source entry first appears in
[28b07c3](https://github.com/wtcross/hfcache/commit/28b07c3c0bfb8fa20d9c97b3a8a2598ccbcc2142)
(2026-07-25, `configuration validation: implement the read-only portions of doctor, plan, and
status`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/cli.py](../../src/hfcache/cli.py),
[src/hfcache/preflight.py](../../src/hfcache/preflight.py).

Relevant verification:
[tests/unit/test_readonly_commands.py](../../tests/unit/test_readonly_commands.py).
