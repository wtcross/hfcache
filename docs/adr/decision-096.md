# Whole-repository deletion is explicit, unmanaged-only, and reuses the prune commit point

- Decision identity: 096.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-15.

## Decision, context, and consequences

Removing configuration or losing
upstream still preserves every local revision (`AD-06`); permanent removal
requires a separate `purge` invocation with an explicit selector set or
`--all-unmanaged`, and `--apply` revalidates that scope under the writer lock.
One transaction owns one complete repository so a broad purge has honest
per-repository failure boundaries. Its `PurgePlan` names every active
publication; whole `refs/`, `revisions/`, and manifest directories move to
transaction trash, and an unknown entry refuses the repository instead of
broadening deletion. Reusing `operation = "prune"` and
`prune_logically_committed` keeps the established recovery rule: before the
boundary restore everything, after it never surprise consumers by
republishing and finish only audit/physical cleanup. A purge-only
`repository_container_removed` checkpoint is accepted at exactly its one
valid position; stripping it leaves the older prune sequence intact, so a
completed journal is safely ignored by older binaries. `PurgePlan` and the
`operator_requested_repository_purge` audit reason are durable-format
widenings: a previous release must never be used while a purge journal is
open, and release packaging must drill the previous reader against the new
completed artifacts before deployment. **Rejected:** deleting immediately
on a configuration edit, which turns mistakes into data loss; manual
filesystem removal, which bypasses `FS-14`, `FS-19`, audit, and recovery;
repeated one-revision prune, which exposes partially retained repositories;
and a new journal operation literal, which adds a second recovery regime
without changing the commit semantics.

## Later history and current interpretation

This implements AD-20 without weakening AD-06. [Decision 97](decision-097.md)
records the observed older-reader behavior: completed purge state is
command-compatible, while open purge journals block rollback and direct audit
tooling must understand the new reason.

## Provenance and governing evidence

The source entry first appears in
[7370af2](https://github.com/wtcross/hfcache/commit/7370af22b53d9a8ec6af855b74005f394b35ad89)
(2026-08-15, `: add transactional unmanaged repository purge`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/cli.md](../cli.md), [docs/schemas.md](../schemas.md).

Implementation or shipped-artifact evidence:
[src/hfcache/purge.py](../../src/hfcache/purge.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py),
[src/hfcache/transactions.py](../../src/hfcache/transactions.py).

Relevant verification:
[tests/unit/test_purge.py](../../tests/unit/test_purge.py).
