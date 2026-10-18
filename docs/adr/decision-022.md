# `config validate` reports `token_source`

- Decision identity: 022.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

`docs/cli.md` §4.1 listed only the fingerprint and two counts. The command an
operator runs before enabling the timer should also answer "did the credential
resolve, and from where" — otherwise the first evidence that a systemd
credential is missing or that `--token-file` is unreadable arrives during a
scheduled run hours later. The field carries the *source* name only
(`token-file`, `systemd-credential`, `none`), never the value, which is what
`docs/security.md` T-07 permits. The CLI configuration result documents this field.

## Provenance and governing evidence

The source entry first appears in
[9477861](https://github.com/wtcross/hfcache/commit/947786190912145451439f970bea478037896b07)
(2026-07-25, `configuration validation: implement config validate`). The decision text above
preserves the complete reasoning in the current historical log, including its
recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md),
[docs/configuration.md](../configuration.md),
[docs/security.md](../security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/cli.py](../../src/hfcache/cli.py),
[src/hfcache/credentials.py](../../src/hfcache/credentials.py).

Relevant verification:
[tests/unit/test_config_validate.py](../../tests/unit/test_config_validate.py).
