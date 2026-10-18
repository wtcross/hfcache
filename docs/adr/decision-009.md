# `--token-file` with `token_mode = "disabled"` is `HFARG002`, not a silent choice

- Decision identity: 009.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Decision, context, and consequences

`docs/configuration.md` §3 says `"disabled"`
means Hub calls *always* pass `token=False`; §7 says `--token-file` is the
first-match-wins source. When both are present the two sentences disagree, and
the contract did not say which wins. Honouring the flag violates the configured
mode. Ignoring the flag is worse: the operator believes the run was
authenticated and nothing says otherwise. So the combination is refused before
any Hub request, consistent with `AD-11`'s rule that a mode is never silently
downgraded. `docs/configuration.md` §7.2 and the `HFARG002` row in
`docs/cli.md` §5.1 are updated.

## Provenance and governing evidence

The source entry first appears in
[8e407b6](https://github.com/wtcross/hfcache/commit/8e407b60271e7365d1ca18a554d4afcf91086b83)
(2026-07-24, `configuration validation: implement the token-source abstraction`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents:
[docs/configuration.md](../configuration.md),
[docs/cli.md](../cli.md), [docs/security.md](../security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/credentials.py](../../src/hfcache/credentials.py).

Relevant verification:
[tests/unit/test_credentials.py](../../tests/unit/test_credentials.py).
