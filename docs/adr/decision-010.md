# Decision 010: `HFARG006` added for a systemd credential that is present but unusable

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `CFG-002`.
- Source: [decision 10 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

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
be read relative to the working directory. Added to `docs/cli.md` §5.1 in this
commit; the plan does not enumerate `HFARG` codes, so no plan amendment is
needed.

## Later history and current interpretation

The absent-credential fallback describes `optional` mode. [Decision
98](decision-098.md) adds explicit `required` mode, which refuses missing
credentials and authorizes restricted repository scope.

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
