# Decision 011: A credential file is validated, never sanitized

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `CFG-002`.
- Source: [decision 11 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

§7 said to strip a single trailing newline and said nothing about what may
remain. A token becomes an `Authorization` header, so a value containing a
stray carriage return, tab, or second newline must not be forwarded — and must
not be quietly cleaned up either, because a file that malformed is not
reliably the token the operator intended. After the one newline is removed the
remainder must be non-empty printable ASCII with no whitespace, in a regular
file of at most 4096 bytes. The size cap keeps a mistyped path from reading a
large file into memory before its contents are found unusable. Recorded as
`docs/configuration.md` §7.1.

## Provenance and governing evidence

The source entry first appears in
[8e407b6](https://github.com/wtcross/hfcache/commit/8e407b60271e7365d1ca18a554d4afcf91086b83)
(2026-07-24, `CFG-002: implement the token-source abstraction`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents:
[docs/configuration.md](../../docs/configuration.md),
[docs/cli.md](../../docs/cli.md), [docs/security.md](../../docs/security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/credentials.py](../../src/hfcache/credentials.py).

Relevant verification:
[tests/unit/test_credentials.py](../../tests/unit/test_credentials.py).
