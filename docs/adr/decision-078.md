# Decision 078: `commit_sha` widens to nullable with no schema bump, and the entry the retained-key rule cannot see gets its own clearing rule

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `VER-009`.
- Source: [decision 78 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Decision 73 stated the limit honestly: a `current.json` that
will not parse names no revision, `Finding.commit_sha` was required, and
attributing the damage to an arbitrary retained revision would be a worse
answer than silence. It also named the fix — widen the field — and left it
"to a release that has a reason to make one". This is that release, and
three choices in the widening are worth recording.

**The null is guarded, not merely optional.** A nullable field with no
constraint would let any finding drop its revision, and a report that
attributes nothing is a report nobody can act on. The model validators
hold `null` to the one shape this module produces — `ref_invalid`,
`publication_id` null, `path` null — so the schema says what the docs say:
one case, exactly. `VerificationRevisionEntry` deliberately does not
widen; a per-revision outcome without a revision raises nobody's
confidence, so null-SHA outcomes never reach `repositories[].revisions[]`
and every `VerificationStates` consumer is provably untouched.

**The clearing rule follows what re-reads the artifact.** §5.2's rule is
that an entry is cleared only by a re-read, and its mechanism — match the
entry's revision key against the retained and covered sets — implements
that rule for entries that *have* a revision key. A null-SHA entry matches
nothing, so the mechanism would drop it on the next narrow run: a
`--revision` that never opened `current.json` would appear to have fixed
it. The rule that preserves §5.2's meaning is keyed to the check itself:
the current-reference check runs only through `resolve_repository`, which
only `--full` reaches, so narrow runs carry the entry forward, a `--full`
clears or re-establishes it (`first_seen_at` preserved), and it leaves
with its repository. The code comment on `_still_outstanding` names the
assumption that must be revisited if a narrower mode ever grows the check.

**No `schema_version` bump, and the consequence is documented rather than
engineered away.** The precedent is `containers_removed` (`RET-008`,
`REL-001`): a field-level change an older release *refuses* cleanly needs
a rollback constraint, not a version fence. An 0.1.2 binary meeting a
null-SHA catalog fails field validation, which `read_verification_catalog`
turns into `None` — every revision reads `unverified`, confidence lowered
and never raised, exactly the direction `FS-16` requires derived state to
err in. The verification *report* is write-only, so nothing older parses
it back. What is genuinely lost on rollback is the degraded signal itself:
0.1.2's `status` reports `unverified`, not `degraded`, over the same
archive. Hence the release-note constraint `REL-004` records: roll back to
0.1.2 only with no null-SHA finding outstanding, clearing it via a clean
`--full` first.

## Later history and current interpretation

This closes the null-SHA limitation explicitly left open by [decision
73](decision-073.md). The rollback restriction here applies to the 0.1.2/0.1.3
null-SHA widening. Later independent compatibility constraints are recorded in
[decision 95](decision-095.md), [decision 97](decision-097.md), [decision
98](decision-098.md), and [decision 102](decision-102.md).

## Provenance and governing evidence

The source entry first appears in
[605b50f](https://github.com/wtcross/hfcache/commit/605b50f7242fd0b956df05fe63cc9e04535e6d12)
(2026-07-27, `VER-009: an unparseable current.json produces a durable finding`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/agents/release.md](../agents/release.md).

Implementation or shipped-artifact evidence:
[src/hfcache/models.py](../../src/hfcache/models.py),
[src/hfcache/verification.py](../../src/hfcache/verification.py).

Relevant verification:
[tests/unit/test_verification.py](../../tests/unit/test_verification.py),
[tests/unit/test_verify_command.py](../../tests/unit/test_verify_command.py).
