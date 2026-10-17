# Decision 056: A committed publication or repair discards its staging area

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `SYNC-004`.
- Source: [decision 56 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Found by running `status` on the live archive at
the §29 rollout checkpoint: after two successful publications it reported
`unfinished_transactions: 2`, with two `.store/staging/<txn>/` directories
holding nothing but a copy of a manifest that was already published.

`publication.discard_staging` had existed since `STO-006` and was called by
nothing but its own tests. `promote_staging` renames `tree/` out of the
staging directory and the pending manifest is its *sibling*, so it stays —
which is the whole point between checkpoints 5 and 6, and pure residue after
6. Nothing was at risk, but the consequences compound: `reconcile_storage`
reads `.store/staging` to find unfinished work, so every published revision
would have left a permanent false positive, and each would have begun
warning `HFWRN004` — "staging past the stale age" — a day later. An operator
who learns to ignore that code stops reading the one signal that means a run
really did stop half way.

So the discard is now the *act* of the last checkpoint: publication's 10 and
repair's 15, each recording `staging_absent` — `_absent` being mechanically
checkable in the opposite direction (decision 42). `recovery`'s
`_complete_publication` does it too, since a recovery-completed publication
is the only other place those steps will ever run for that transaction.

Two knock-on corrections. Checkpoint 4's `pending_manifest_path` becomes
`pending_manifest`, by decision 53's rule — a later step in the same
operation removes it, so asserting it still exists would make every
committed journal contradict the archive, and would block every `recover`
during a repair's seven-day grace. And the test that provoked `HFTXN003` by
deleting the staged manifest no longer can: that deletion now correctly
means "the tree cannot be validated" and quarantines it (§7.3's caveat). The
`HFTXN003` case is provoked instead by deleting the *published tree*
checkpoint 5 named, which is a genuine journal-contradicts-filesystem state.
`docs/architecture.md` §7.3 and §7.5 are amended in this commit.

## Later history and current interpretation

[Decision 103](decision-103.md) separately authorizes explicit cleanup of proven
redundant quarantine after resolved failed publication/recovery. Successful
staging discard does not grant authority to discard arbitrary failed staging.

## Provenance and governing evidence

The source entry first appears in
[41690bd](https://github.com/wtcross/hfcache/commit/41690bd7cd5da5231e74e504489f1eba60dc945b)
(2026-07-26, `SYNC-004: discard a committed transaction's staging area`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../docs/architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/publication.py](../../src/hfcache/publication.py),
[src/hfcache/repair.py](../../src/hfcache/repair.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_publish_revision.py](../../tests/unit/test_publish_revision.py),
[tests/unit/test_crash_injection.py](../../tests/unit/test_crash_injection.py).
