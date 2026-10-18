> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 094: Queue-ahead uses one repository producer inside the existing run lock

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-08-10.
- Original work package: `SYNC-007`.
- Source: [decision 94 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Continuation-enabled sync plans the selected queue,
admits its aggregate requirement before transferring anything, and lets one
background repository transfer run while the main thread hashes and
publishes prior snapshots. That producer alone receives
`sync.max_workers=4`, so the setting remains a global Hub file-worker budget
rather than multiplying into unbounded Xet streams. Results and publication
remain in configuration order; stop-on-error runs remain serial because an
in-flight library transfer has no safe cancellation boundary. Multiple
queued-but-unstarted transfers are cancelled on an unexpected foreground
exception; the one active transfer is joined before the lock is released.
Multiple ordinary publication journals may wait at `download_completed`;
no queue format or checkpoint is added. Retention waits until every queued snapshot
is consumed because the installed Hub API deletes cache revisions by commit
hash across its scan, and the same Git SHA can exist in two repositories.
Cache writes and retention scans are serialized; copy-mode staging also
rechecks and holds allocation headroom, while hardlink staging can overlap.
**Rejected:** multiple repository downloads, which would multiply Xet's
internal concurrency under the 4 GiB service memory bound. **Rejected:** a
separate sync process, which would contend for the single-writer lock or
mutate cache outside its ownership. **Rejected:** enabling
`HF_XET_HIGH_PERFORMANCE`, whose installed-version buffer and stream limits
exceed the production memory model.

## Later history and current interpretation

This implements AD-19. Repository publication remains ordered, the Hub
file-worker budget remains global, and cache retention waits until queued
snapshots are consumed. It does not introduce multiple writer processes.

## Provenance and governing evidence

The source entry first appears in
[54e4671](https://github.com/wtcross/hfcache/commit/54e4671cec9cd2a2f82bfa73372e78478d29e7f4)
(2026-08-10, `SYNC-007: download ahead while repositories hash`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../../../../architecture.md),
[docs/configuration.md](../../../../../configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/sync.py](../../../../../../src/hfcache/sync.py).

Relevant verification:
[tests/unit/test_synchronize.py](../../../../../../tests/unit/test_synchronize.py).
