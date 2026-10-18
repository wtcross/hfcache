# Separate ingestion hashing from published-instance confidence

- Decision identity: 051.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.

## Context, decision and consequences

Ingestion hashing verifies cache bytes before the publication tree exists;
its successful result belongs to manifest ingestion evidence. Offline verification
reads the landed publication at a different time and records that evidence in the
verification catalog. Treating every ingested revision as offline-verified would
make the displayed confidence unfalsifiable.

A clean catalog entry means verified, a failed entry means failed, and absent or
unsafe evidence means unverified/unknown. Lookup binds repository, full SHA and
exact publication instance; earlier evidence cannot confer confidence on a repair
or reintroduced revision. Nullable corrupt-current findings remain a separate
clearing rule, as explained by decisions 62 and 78.

## Provenance and governing evidence

The source entry first appears in
[6c5389b](https://github.com/wtcross/hfcache/commit/6c5389bb95aa95380c13757cd7af9e26d21f2885)
(2026-07-26, `verification: persist verification reports and report current health`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/publication.py](../../src/hfcache/publication.py),
[src/hfcache/verification.py](../../src/hfcache/verification.py).

Relevant verification:
[tests/unit/test_verify_command.py](../../tests/unit/test_verify_command.py).
