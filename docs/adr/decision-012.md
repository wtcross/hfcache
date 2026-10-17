# Decision 012: `hub.credential_name` may not be `.` or `..`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `CFG-002`.
- Source: [decision 12 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Both
match the published `[A-Za-z0-9._-]{1,64}` grammar, and both name a directory
rather than a credential. Neither is exploitable — no `/` is permitted, so the
worst case resolves to `$CREDENTIALS_DIRECTORY` itself and fails as "not a
regular file" — but it fails at run time with a confusing message instead of
at `config validate` with a clear one. Rejected as `HFCFG013`, and the §3
constraint column is updated in this commit.

## Provenance and governing evidence

The source entry first appears in
[8e407b6](https://github.com/wtcross/hfcache/commit/8e407b60271e7365d1ca18a554d4afcf91086b83)
(2026-07-24, `CFG-002: implement the token-source abstraction`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents:
[docs/configuration.md](../../docs/configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/config.py](../../src/hfcache/config.py).

Relevant verification:
[tests/unit/test_config.py](../../tests/unit/test_config.py).
