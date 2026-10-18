# Decision 051: `verification_state` comes from `catalog/verification.json`, and a revision nothing has re-read is `unverified`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `VER-005`.
- Source: [decision 51 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

This settles the second item Phase 6 carried in. No document said whether a
revision that was SHA-256 verified at ingestion but never verified offline
is `verified` or `unverified`, and three call sites hardcoded `"verified"`,
which made `failed` unreachable and `unverified` unreportable for any
published revision.

Ingestion hashing is not verification of the published revision. It reads
the bytes in the *Hub cache*, before the publication tree exists, and its
result is already recorded where it belongs — `manifest.verification.outcome`
is `verified` and always will be, because a manifest is only published after
ingestion succeeds (`docs/schemas.md` §3.4). `verify` reads the *tree*, which
is a different set of bytes on a different filesystem at a different time,
and `catalog/verification.json` is the record of that. Reporting `verified`
for a revision nothing has ever re-read would make the field unfalsifiable —
which is exactly the symptom the hardcoding produced.

So: `clean` in the verification catalog is `verified`, `failed` is `failed`,
and no entry is `unverified`. `publication.VerificationStates` is the single
reader, and `publication._catalog_entry`, `cli._status_entry`, and
`cli._listed_revision` all go through it. A newly published revision reads
`unverified` until a `verify` covers it, which is what makes the §29 rollout
checkpoint's `verify --full` a step that changes something observable.

The two catalog models gained nullable `publication_id` for the same single
case decision 49 gave `Finding`, and `docs/schemas.md` §5.2 now says so.

## Later history and current interpretation

[Decision 62](decision-062.md) makes the lookup key include publication identity
so an earlier instance cannot confer verification on its replacement. [Decision
78](decision-078.md) adds the separate clearing rule for null-SHA
current-reference findings.

## Provenance and governing evidence

The source entry first appears in
[6c5389b](https://github.com/wtcross/hfcache/commit/6c5389bb95aa95380c13757cd7af9e26d21f2885)
(2026-07-26, `VER-005: persist verification reports and report current health`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/publication.py](../../src/hfcache/publication.py),
[src/hfcache/verification.py](../../src/hfcache/verification.py).

Relevant verification:
[tests/unit/test_verify_command.py](../../tests/unit/test_verify_command.py).
