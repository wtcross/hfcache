# Keep the CLI reference separate from operational workflows

- Decision identity: 002.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Context, decision and consequences

`docs/cli.md` owns commands, options, JSON Envelopes, exit aggregation and the
complete error taxonomy. A runbook answers operational questions and is the wrong
home for the normative command reference. Keeping these rules together gives
implementation, clients and operators one authoritative interface specification.

## Provenance and governing evidence

The source entry first appears in
[00c5957](https://github.com/wtcross/hfcache/commit/00c59571e747ca03e5f788aabc9e18ba9627a563)
(2026-07-24, `contract definition: define CLI commands, JSON output, and exit codes`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/reporting.py](../../src/hfcache/reporting.py),
[src/hfcache/taxonomy.py](../../src/hfcache/taxonomy.py).

Relevant verification:
[tests/unit/test_taxonomy.py](../../tests/unit/test_taxonomy.py).
