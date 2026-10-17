# Decision 079: 0.1.3 is tagged because it is deployed, and it is still not 1.0.0

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `REL-004`.
- Source: [decision 79 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The version question decision 75 settled for the
first release settles the same way for the second, and stating why briefly
is cheaper than re-deriving it later. 0.1.3 is the tree that passed the
gates with `--with-build`, was staged, validated, switched, and ran a clean
sync through the unit; the tag, the running code, and this file's evidence
all name one thing. A patch-level bump is right for the content: one
field-level durable widening with no `schema_version` change, one permit
removal that no real journal ever exercised, and a test-tree rename.

The release exists for `VER-009` and is deliberately small around it. The
ordering the closeout plan fixed — everything non-durable first — is what
made the cross-format drill about one change alone: when 0.1.2 and 0.1.3
read the same catalog differently, the only candidate explanation is the
widening, not a pile of coincident changes. The drill showed the loss is
exactly the one decision 78 predicted (the degraded signal, silently) and
no other; the constraint is documented beside the prune-in-flight rule so
every rollback rule lives on one page.

Not `1.0.0`, for decision 75's unchanged reason: §33's definition of done
still includes the consumer export, snapshots and replication, the
disjointness proof from a second client, reboot persistence, and the
quarterly verification timer — all operator items, all still open in the
handoff. Gap 4 of the closeout (the production repository list) is likewise
operator input; nothing writer-side blocks on it. The archive's health
headline is the thing this release hardened, and it would be a poor joke to
version-inflate the release that made a lost health signal loud.

## Later history and current interpretation

This is the historical 0.1.3 release record, including the then-open operator
work. Current release status and handoff must be read from the current tracker
and changelog.

## Provenance and governing evidence

The source entry first appears in
[4dd886e](https://github.com/wtcross/hfcache/commit/4dd886ed8982688bbad05cf71c85079e460b695d)
(2026-07-27, `REL-004: build, check, deploy, and tag 0.1.3`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents:
[docs/agents/release.md](../../docs/agents/release.md),
[CHANGELOG.md](../../CHANGELOG.md).

Implementation or shipped-artifact evidence:
[pyproject.toml](../../pyproject.toml),
[scripts/install-release.sh](../../scripts/install-release.sh).

Verification or recorded operational evidence:
[docs/progress.md](../../docs/progress.md).
