# Decision 019: Reading a durable artifact takes the caller's error class *and* code

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-004`.
- Source: [decision 19 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The same malformed file means different things
depending on which artifact it is: a bad manifest is `HFVER007` at exit `40`,
a bad journal is `HFTXN001` at exit `20`, a bad sentinel is `HFMNT006` at exit
`20`. `load` therefore takes both, and applies the code to every problem it
reports, with the field path as the location. That is what lets the field
validators in `hfcache.identity` and `hfcache.paths` stay ignorant of which
artifact they are validating — the artifact names the code, the field names
the place. `parse_archive_relative` and `parse_repository_relative` gained an
optional `code`; omitted, they raise an uncoded `ValueError` for a validator
to collect.

## Provenance and governing evidence

The source entry first appears in
[2133496](https://github.com/wtcross/hfcache/commit/21334967781eef8ee37600ed63fad4e42e404180)
(2026-07-25, `CFG-004: implement the durable manifest and report models`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../../docs/schemas.md),
[docs/cli.md](../../docs/cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py).

Relevant verification:
[tests/unit/test_models.py](../../tests/unit/test_models.py).
