# Changelog

Releases are deployed first and tagged for what is deployed
(`docs/progress.md` decisions 75 and 79). The annotated tags carry the
complete release notes; this file is the browsable summary. Versions 0.1.0
and 0.1.1 exist only as install targets under `/opt/hfcache/releases` — one
proved the install mechanism, the other gave rollback somewhere to go — and
were never releases.

## v0.1.7 — 2026-09-14

`storage.maximum_revisions` now defaults to three. Explicit five-revision
policies remain valid; the Cockpit form offers both supported values. Adopting
three on an existing archive requires validated configuration and repeated
reviewed prune rounds, preserving the current revision and manifest audit
evidence. Retention ordering and durable JSON formats are unchanged.

Before rolling back to an older binary, restore an explicit
`maximum_revisions = 5`. That restores the older policy, not deleted revisions.

## v0.1.6 — 2026-08-23

Private and gated Hub repositories can now be archived through the explicit
`hub.token_mode = "required"` policy. Required mode fails before Hub access
when its credential is unavailable, verifies the configured account identity,
and distinguishes an unaccepted gate from the public-only scope refusal that
remains in `disabled` and `optional` modes. The Cockpit configuration form and
operator runbooks cover the same restricted-repository workflow.

## v0.1.5 — 2026-08-15

Repositories intentionally removed from configuration can now be deleted with
an explicit, dry-run-first, transactionally recoverable `purge` command.

- `purge` accepts explicit whole-repository selectors or `--all-unmanaged`,
  refuses configured repositories, and deletes one complete repository per
  durable transaction. Unknown content is preserved rather than broadened into
  the deletion scope.
- Cache revisions are removed only through `huggingface_hub`; complete
  publication references, trees, and manifests are tombstoned atomically.
  Original manifests and one purge-reason record per revision remain under
  `audit/pruned/`.
- Pre-commit recovery restores every revision with references last;
  post-commit recovery keeps the consumer-visible removal and finishes audit
  and trash cleanup.
- `PurgePlan` is a new schema-version-1 durable shape and
  `operator_requested_repository_purge` widens the prune-record reason. The
  0.1.4 reader accepts completed purge journals in `status` and
  `recover --dry-run`, and can re-add/sync the purged SHA using the archived
  manifest. Its generic prune-record parser rejects the new reason literal.
  Therefore **roll back to 0.1.4 only with no purge transaction in flight**;
  use 0.1.5 for direct purge-record inspection.

## v0.1.4 — 2026-08-11

Large archives no longer leave the Hub idle for days while one repository is
hashed. One repository download now runs ahead of the serial hash/publication
path, using the existing four-worker global budget, while hardlink publication
carries proven same-inode digest evidence instead of rereading every byte.

- Queue-wide admission, per-transfer capacity rechecks, serialized cache
  mutation, deferred retention, and ordinary publication journals preserve the
  single-writer and recovery contracts while downloads overlap hashing.
- New `repository.queued`, `hash.started`, and `hash.completed` events make the
  WAN-idle hashing phase and its progress explicit in journald and Cockpit.
- The new Cockpit package supplies archive and run-report views, sync and
  verification controls, dry-run-first maintenance, configuration and schedule
  editors, and authenticated transient-unit invocations that import the same
  encrypted Hub credential as the scheduled service.
- Sync and verification units bound page-cache pressure with `MemoryHigh=4G`;
  absolute dirty-page limits keep the writeback share reclaimable. Operations,
  storage requirements, loopback quickstart, public-repository, and agent
  workflow documentation now describe the deployed system.
- A failed run report may retain warnings observed before a later failure.
  This is a schema-version-1 field-combination widening: **rollback to 0.1.3
  only when the newest sync report uses an older-valid combination, or after a
  later compatible 0.1.4 sync supersedes it.** 0.1.3 rejects a mixed
  failed-plus-warning report as `HFVER007`; `status` silently falls back to an
  older readable report (`docs/deployment-centos-stream-10.md` §14).

## v0.1.3 — 2026-07-27

The health headline cannot go quiet: an unparseable `refs/current.json` — the
one file a consumer must read — is now a durable `HFVER008` finding at exit
`40`, where 0.1.2 reported the archive clean (`VER-009`).

- `Finding.commit_sha` and `OutstandingFailure.commit_sha` widen to nullable,
  guarded to exactly one shape, with no `schema_version` bump. The finding
  persists in `catalog/verification.json`, degrades `status`, and clears only
  when a `verify --full` re-reads the reference.
- **Rollback rule:** return to 0.1.2 only with no null-SHA finding
  outstanding — 0.1.2 reads such a catalog as everything-`unverified` and
  **not** degraded, silently losing the degraded signal. A clean
  `verify --full` clears it first (`docs/deployment-centos-stream-10.md` §14).
- The crash-injection suite is named for what it holds
  (`tests/unit/test_crash_injection.py`), and the failure matrix's module
  list is asserted against the matrix itself rather than maintained by hand
  (`OPS-008`).
- Architecture §7.4 reconciled doc-to-code on `cleanup_deferred`: nothing
  ever recorded that checkpoint, and a prune journal carrying it is now
  refused as `HFTXN002` (`RET-009`).

## v0.1.2 — 2026-07-27

First release. The writer is complete and deployed: it syncs public model and
dataset repositories pinned to resolved full commit SHAs, SHA-256 hashes
every new object before publication, publishes hardlink trees by atomic
rename behind an atomically replaced `current.json`, retains five revisions
per repository and prunes the sixth, verifies offline against immutable
manifests, repairs without letting corrupt bytes become the expectation, and
recovers every documented interrupted-transaction state — or stops and says
why.

At release: deployed on the writer VM against a TrueNAS NFSv4.2 export,
SELinux enforcing with zero AVC denials, systemd hardening probed at 23 of 23
on both service units, 1 585 tests by default plus the opt-in live, NFS, and
build suites.

Deliberately not done, and why this is 0.1.x and not 1.0.0: the read-only
consumer export, snapshots and replication, the disjointness proof from a
second client, reboot persistence, and the quarterly verification timer — all
operator items, tracked under **Operator handoff** in `docs/progress.md`.
