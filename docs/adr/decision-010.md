# Reject a present but unusable systemd credential

- Decision identity: 010.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Decision, context, and consequences

The taxonomy had `HFARG005` for `--token-file` and
nothing for the other source, so an empty, unreadable, or malformed systemd
credential had no code. It needs one distinct from `HFARG005`, because the two
conditions have different fixes — one is a mistyped command line, the other a
broken unit or credential store. Absence still resolves to anonymous access,
since `token_mode = "optional"` says a missing credential is normal; presence
plus unusability does not, because continuing anonymously would report success
for a run the operator believes was authenticated. `$CREDENTIALS_DIRECTORY`
set to a relative path shares the code: systemd always sets it absolute, so a
relative value means the environment is wrong and a credential would otherwise
be read relative to the working directory. The credential-source failures have distinct entries in the CLI error taxonomy.

## Later history and current interpretation

The absent-credential fallback describes `optional` mode. [Decision
98](decision-098.md) adds explicit `required` mode, which refuses missing
credentials and authorizes restricted repository scope.

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
