# Decision 075: The first release is `v0.1.2`, because that is what is deployed

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `REL-003`.
- Source: [decision 75 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §28 leaves the version open and notes that
0.1.1 is live and untagged. Three candidates, and the accident of the
numbering is the interesting part.

0.1.0 and 0.1.1 were never releases in this sense. 0.1.0 existed because
`HOST-004` had to prove `install-release.sh` worked at all. 0.1.1 existed
because `OPS-001` discovered that a rollback exercised against a single
installed release proves only that a symlink can be rewritten (decision 65),
so a second release had to exist for the first to be rolled back from. Both
are retained under `/opt/hfcache/releases`, and both remain useful for exactly
that: §21.4 item 7 wants the previous release kept.

Re-cutting a tidier number — 0.2.0, say, to mark the phase — was rejected
because it would tag an artifact nobody had deployed. 0.1.2 is the tree that
was installed by the documented §13 procedure, passed 23 of 23 hardening
checks on both units, verified clean over six revisions, and served as the
*new* side of a genuine cross-format rollback check. Tagging it means the tag,
the running code, and the evidence in this file all name the same thing.

Not `1.0.0`, and the reason is not modesty. §33's definition of done includes
the consumer export, snapshots and replication, the disjointness proof from a
second client, reboot persistence, and the quarterly verification timer. Every
one of those is real, none can be performed from the writer, and all five are
in the operator handoff. A `1.0.0` asserting them would be the same kind of
unfalsifiable claim decisions 51, 62, and `HARD-001` exist to remove.

The tag is annotated, so `git show v0.1.2` carries the release note and does
not depend on a file the plan's §7 layout does not list.

## Later history and current interpretation

This is a historical release-selection record. Current version and release
status belong to the changelog, annotated release tags, and tracker handoff.

## Provenance and governing evidence

The source entry first appears in
[e62ddbc](https://github.com/wtcross/hfcache/commit/e62ddbcf09376c3ad531c607faf3ee7f51b4fd25)
(2026-07-27, `REL-003: tag and document the first release`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents:
[docs/agents/release.md](../../docs/agents/release.md),
[CHANGELOG.md](../../CHANGELOG.md).

Implementation or shipped-artifact evidence:
[pyproject.toml](../../pyproject.toml).

Verification or recorded operational evidence:
[docs/progress.md](../../docs/progress.md).
