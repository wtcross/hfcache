# Preserve the exact successful committed prune sequence predating container cleanup

- Decision identity: 166.
- Status: Accepted.
- Original decision date: 2026-11-05.
- Record introduced: `7e40849dafe340312244f181f66530ad8be672e6`.

## Context and decision

Actual installed metadata refresh refuses two valid committed prune journals
from2026-07-26 because decision068 added containers_removed on the next day.
The original producer at53afd6901631f1e7237ecdf2d190561d406ee127 uses exactly
plan_persisted, cache_revision_deleted, revision_ref_removed, tree_tombstoned,
manifest_tombstoned, catalog_published, prune_logically_committed,
audit_record_written, trash_removed, prune_completed. Those immutable original
bytes cannot acquire a checkpoint recording work their producer never performed.

Recognize only that exact complete schema-1 sequence for a committed successful
prune, with null error and completed_at at/after last_checkpoint_at. Every
existing schema, archive identity and structural check remains. The sequence
is resolved history, never an instruction to replay or clean up. Today's
checkpoint table remains unchanged and current writers cannot append
prune_completed while skipping containers_removed in an open transaction.

## Rationale, alternatives and consequences

This restores compatibility with an actual valid predecessor producer without
modifying archive evidence or inventing historical effects. Reject rewriting
or deleting old journals, rerunning retention, accepting arbitrary resolved
checkpoint sequences, and weakening unfinished-work/deletion guards. Failed,
needs-operator, open, missing-completion, error-bearing, reordered, othermissing
or unknown sequences do not gain the exception. No durable/wire format,
dependency, permission, CIL, namespace or journal-write behavior changes.

## Evidence and relationships

[Decision068](decision-068.md) retains the current cleanup rule and this narrow
historical amendment. Governing contracts: [architecture7.4](../architecture.md),
[schemas10](../schemas.md), [discovery](../discovery.md) and
[invariants](../invariants.md). Implementation: [checkpoint checker](../../src/hfcache/transactions.py).
Verification: [legacy journal regression](../../tests/unit/test_legacy_prune_journals.py)
and existing [supplemental guard tests](../../tests/unit/test_catalog_storage.py).
The actual old-journal hashes and installed failed operation remain in protected
operator evidence outside maintained documentation. Source validation and prepared artifacts do not
establish installed metadata-refresh/backfill acceptance.
