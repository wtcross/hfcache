# Exit-code aggregation order fixed as `40`, `50`, `30`

- Decision identity: 003.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Decision, context, and consequences

The CLI contract fixes the codes and requires a non-zero result when a
run continues past a repository failure, but does not say which code wins
when several arise in one run. Codes `10` and `20` abort before
per-repository work, so only `30`/`40`/`50` can co-occur. They are ordered by
operator urgency — possible corruption, then degraded retention, then stale
content — and every classification encountered is still listed in the JSON
envelope's `errors` array, so aggregation hides nothing.

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
