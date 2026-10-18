> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 022: `config validate` reports `token_source`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-005`.
- Source: [decision 22 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`docs/cli.md` §4.1 listed only the fingerprint and two counts. The command an
operator runs before enabling the timer should also answer "did the credential
resolve, and from where" — otherwise the first evidence that a systemd
credential is missing or that `--token-file` is unreadable arrives during a
scheduled run hours later. The field carries the *source* name only
(`token-file`, `systemd-credential`, `none`), never the value, which is what
`docs/security.md` T-07 permits. `docs/cli.md` §2 and §4.1 updated in this
commit.

## Provenance and governing evidence

The source entry first appears in
[9477861](https://github.com/wtcross/hfcache/commit/947786190912145451439f970bea478037896b07)
(2026-07-25, `CFG-005: implement config validate`). The decision text above
preserves the complete reasoning in the current historical log, including its
recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../../../../cli.md),
[docs/configuration.md](../../../../../configuration.md),
[docs/security.md](../../../../../security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/cli.py](../../../../../../src/hfcache/cli.py),
[src/hfcache/credentials.py](../../../../../../src/hfcache/credentials.py).

Relevant verification:
[tests/unit/test_config_validate.py](../../../../../../tests/unit/test_config_validate.py).
