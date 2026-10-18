# Decision 062: The reported verification state is keyed by publication instance, not by SHA

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `VER-007`.
- Source: [decision 62 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Found at `SEL-001` by the retention rotation:
a dataset revision that had been pruned and later re-synced read `verified`
in `status`, on the strength of a verification of the instance the prune had
removed.

`catalog/verification.json` has recorded `publication_id` per revision since
`VER-005`. `VerificationStates.of` keyed its lookup on
`(repository_type, repository_id, commit_sha)` and discarded it. A
verification re-reads the bytes of one published *instance*, and two
instances of one SHA are different bytes in different places — a repair
replaces one, and a prune followed by a later republication of the same SHA
produces another. So `verified` became true of content nothing had ever
re-read: decision 51's unfalsifiable field, reappearing through a different
door, and reappearing in exactly the window an operator would look at, the
one between publishing a revision and verifying it.

The key is now the instance, and the three call sites — `status`, `list`, and
the derived catalog — each pass the publication id the reference or the
manifest they already hold carries. An entry whose `publication_id` is null
raises nobody's confidence, because it cannot be attributed to anything on
disk and the conservative answer to "was this instance re-read?" is no.

No durable format change was needed; the field was already there.
`docs/schemas.md` §5.2 now states the key. A repair was never affected —
`VER-006`'s checkpoint 8 re-verifies the replacement before any reference
moves, so it records its own entry — which is why this only ever surfaced
through a prune.

## Provenance and governing evidence

The source entry first appears in
[657d5a7](https://github.com/wtcross/hfcache/commit/657d5a711bd442a09511915f94c0eebc4359d52f)
(2026-07-26, `SEL-001: validate every archive operation with SELinux
enforcing`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

The named work package's implementation commit is
[fd59580](https://github.com/wtcross/hfcache/commit/fd595801d99685886c4af28206e7714907a41095).
The source-entry introduction and implementation are recorded separately rather
than inferred to be the same commit.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/architecture.md](../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/publication.py](../../src/hfcache/publication.py),
[src/hfcache/verification.py](../../src/hfcache/verification.py).

Relevant verification:
[tests/unit/test_verify_command.py](../../tests/unit/test_verify_command.py).
