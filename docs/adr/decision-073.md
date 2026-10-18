# Verification enumerates the retained set, and `current.json` is not in it

- Decision identity: 073.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Decision, context, and consequences

The verification contract says the quarterly job "validates
refs, manifests, and publication paths", and `docs/schemas.md` §4.2 states an
invariant in plain words: `current.json` always names a SHA that also has a
`refs/revisions/<sha>.json`, and both agree on `publication_id`. Nothing
checked it, and the reason is structural rather than an oversight in one
function.

`resolve_repository` walks `refs/revisions/`, and it is right to: a per-SHA
reference is what *makes* a SHA retained (`FS-11`), and enumerating the
revision directories instead would verify a repair's retired instance and
report an archive as degraded for holding evidence it was told to keep.
`current.json` sits outside that set by design — it is a pointer *into* it —
so a traversal defined as "every retained revision" reaches every byte a
consumer might copy and never reaches the file that tells them which bytes.

What that cost: point `current.json` at a publication id that does not exist
while leaving the per-SHA reference correct, and `verify --full` reports
`outcome: clean` at exit `0`. Every retained revision really is intact — the
traversal is not lying — but the archive is in `FS-10`'s forbidden state and
the integrity command says it is healthy. A consumer resolving that reference
finds nothing, and `docs/consumers.md` tells it to treat a vanished tree as
retryable, so it retries against a permanently dangling pointer.

The fix reuses `ref_invalid`/`HFVER008`, so there is no durable-format change,
and it is deliberately narrow. When the per-SHA reference is itself the
damaged artifact, `resolve_revision` already reports it and this reports
nothing: one broken file, one finding. The first draft did not observe that
and five existing tests failed, which is the suite doing its job.

The limit is worth stating because it is a real one. A `current.json` that
will not parse at all yields no finding here, because `Finding.commit_sha` is
required and an unparseable reference supplies none — `refs/revisions/<sha>`
carries its SHA in its *filename* and `current.json` does not. Attributing the
damage to an arbitrary retained revision would be a worse answer than
silence. It is not actually silent: `status` drops the repository to
`unverified`, and the consumer helper fails closed on it. Widening
`Finding.commit_sha` to optional would close it properly and is a schema
change, so it is left to a release that has a reason to make one.

## Later history and current interpretation

The retained-set/current-reference distinction remains. The stated limitation
for an unparseable `current.json` is superseded by [decision
78](decision-078.md), which makes the null-SHA finding representable and
durable.

## Provenance and governing evidence

The source entry first appears in
[a3e991a](https://github.com/wtcross/hfcache/commit/a3e991a8affdd07c4d39728a7b310d25e959a4bd)
(2026-07-27, `verification: full verification never read refs/current.json`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/architecture.md](../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/verification.py](../../src/hfcache/verification.py).

Relevant verification:
[tests/unit/test_verification.py](../../tests/unit/test_verification.py),
[tests/unit/test_verify_command.py](../../tests/unit/test_verify_command.py).
