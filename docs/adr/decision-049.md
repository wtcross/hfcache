# A verification finding may name no publication instance, and `HFARG004` now covers a revision or a run this archive does not hold

- Decision identity: 049.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.

## Decision, context, and consequences

Two small contract amendments, both forced by the same thing:
`verify` is the command an operator runs when the archive is *already* known
to be wrong (`docs/architecture.md` §7.9), so it has to keep answering about
artifacts it cannot read.

`docs/schemas.md` §7 typed `finding.publication_id` as required. A reference
that will not parse names no publication instance, so there is nothing to
put there — and attributing the finding to whichever instance directory the
filesystem happens to hold would assert exactly what the unreadable
reference failed to say. The alternative was to raise instead of reporting,
which would abandon every other repository in the run because one reference
file is corrupt. The field is now nullable, `docs/schemas.md` §7 says the
single case it is null for, and every other finding still carries it.

`docs/cli.md` §5.1 defined `HFARG004` as a selector naming a repository
absent from configuration. `verify --revision TYPE:ID@SHA` and
`verify --new --run-id ID` can both name something that is not there, and
neither is an integrity failure: a mistyped SHA reported as exit `40` would
tell a scheduler the archive is corrupt because somebody typed one wrong
character. The row now reads "an argument names something the archive does
not hold", which is one condition with three instances rather than three
codes for one mistake. `tests/unit/test_taxonomy.py` parses that table, so
the widened row is checked in both directions.

## Later history and current interpretation

[Decision 78](decision-078.md) additionally permits a narrowly guarded null
`Finding.commit_sha` for an unreadable current reference. Nullable publication
identity alone was the original widening.

## Provenance and governing evidence

The source entry first appears in
[677dc17](https://github.com/wtcross/hfcache/commit/677dc1795b2ac10ad22e8f0c1fb809e4f0c6e981)
(2026-07-26, `verification: verify the content one run introduced`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py),
[src/hfcache/verification.py](../../src/hfcache/verification.py).

Relevant verification:
[tests/unit/test_verification.py](../../tests/unit/test_verification.py).
