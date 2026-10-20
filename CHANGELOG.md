# Changelog

Annotated release tags identify reviewed deployed states; application source and
deployment commits may differ. This file summarizes user-visible changes and
rollback constraints. Installation targets 0.1.0 and 0.1.1 were not releases.

## 0.2.2 — 2026-10-20, local release with workload holds

This release combines the changes below since previously deployed source `4088994`.
The local installation now selects clean source `1c68501`, identified by local
annotated `v0.2.2`. Actual installed acceptance passed for the indexed artifacts,
TLS/authentication, private worker and fixed host client. Configuration, candidate,
predecessor, locks, receipts, handles and secret identities remain intact. Existing
NAS/workload holds remain; the tag has not been published to either remote.

- Cockpit preserves classified bridge, launcher, API and domain failures, plus
  original operation keys and IDs across tab changes and interrupted observation.
  Uncertain execution blocks another submission; recovery authenticates and
  observes the original operation without replay.
- Candidate preparation retains each validation/preview/confirmation result and
  reconciles captured exact bytes before further action. Bounded ASCII framing
  avoids NUL-triggered Cockpit text-channel disconnects. Installed confirmation
  gives PID1 a pipe and uses a bounded local collector, preserving SELinux
  confinement, original process statuses, the configuration lock and backup.
- Manual full jobs use the fixed REST client and fresh protected host permissions.
  Run reports use authenticated paged REST reads; optional journal diagnostics
  remain independent. Read views distinguish failed, partial, unavailable and
  known empty results, and diagnostics separate browser, selected-release and
  API identities.
- The Unix HTTP adapter treats empty writes as a no-op, preventing a late empty
  end-of-message write from closing a valid response's socket prematurely.
- Installed-wheel/private-socket and actual isolated Cockpit/PAM/rootless checks
  passed, including exact configuration installation/confirmation and read-only
  reconciliation after bridge interruption. These disposable checks remain
  separate from actual installed acceptance and do not prove the original
  installed browser symptom fixed. Its existing candidate is preserved.
- Optional normalized configuration tags, Cockpit authoring and current versus
  last-observed provenance are separate from operational policy and immutable
  publication/integrity identity.
- Local search, facets, exact catalog detail and variant pages share bounded
  REST, base-client/CLI and five additional read-only MCP tools. Technical
  predicates match one supported complete primary variant; unknown coverage
  remains explicit. MCP now exposes fourteen read-only tools. Static
  GGUF/AWQ/GPTQ and dataset declarations execute no code.
- Sync/repair capture and writer-only keyed offline refresh store independently
  atomic supplemental records. Reads never fetch, open model payloads or refresh.
- Old durable evidence stays byte-compatible. New tags, directory and refresh
  kinds have observed target-specific compatibility limits; retain backup/state/
  handles and actual executor drain. See [discovery rollback](docs/discovery.md#guarded-rollback-and-backup).
  In particular, the predecessor 0.2.1 binary refuses explicit configuration tags
  and its strict client refuses new refresh routes. Preserve a target-compatible
  configuration and compatible observation of retained new operation kinds;
  rollback never authorizes deleting supplemental metadata or receipts.

## 0.2.1 — 2026-10-18, local release with workload holds

- Service images use pinned UBI 10 micro with authenticated portable Python and
  verified executable/Red Hat CA donors. Application artifacts come from clean
  source `4088994`; local annotated `v0.2.1` identifies deployment `156506f`.
- The confined direct-PID1 worker creates its AF_UNIX listener and announces
  readiness before API startup. Installed API-container peer access passes under
  SELinux Enforcing, correcting the connection limitation recorded for 0.2.0.
  Native strict named-FD3 activation remains separate.
- Recorded local TLS/REST/MCP/client, isolation and non-killing drain/restart
  acceptance passed. NAS stays read-only, legacy writers masked and verification
  scheduling disabled. Live storage jobs, other-host and full workload acceptance
  are not claimed; see [deployment scope](docs/deployment-status.md).

## 0.2.0 — 2026-10-18, local partial-acceptance release

**Breaking change:** operational CLI commands require the authenticated REST API;
there is no local execution fallback. Reader installations need no archive mount,
archive policy, Hub credential or optional server framework.

- Authenticated REST provides bounded metadata, exact publication/report identity,
  typed keyed jobs, maintenance previews/applies and operation observation. Default
  JSON output and explicit results retain exact terminal server Envelopes.
  Complete inventory collection either finishes within finite budgets or fails
  visibly. Validated keys and accepted IDs remain visible in quiet mode.
- Independent strict client/server settings, fixed reader/writer capabilities,
  verified HTTPS/Unix transport and protected credential sources separate API
  authority from Hub access. Candidate syntax validation is separate from
  compatibility with installed authority; API previews cannot install policy.
- Durable local receipts and scheduled observer handles preserve keys across lost
  acknowledgement, restart and finite wait windows. Observation loss does not
  cancel work; startup and retries never automatically replay uncertain jobs.
- One bounded execution lane serializes mutations. Actual verification holds the
  archive lock through scope, hashing, report and catalog merge, and delegates to
  a peer-checked private no-IP/no-credential executor. Diagnostics and confirmed
  initialization use the same authority checks; initialization is disabled by
  default and never occurs during startup or recovery.
- Optional standalone FastMCP exposes exactly nine read-only metadata tools with
  bounded typed projections and exact source-bound pagination. It uses a distinct
  whole-archive MCP-reader credential. No jobs, Hub fetch, integrity verification,
  resources/prompts, OAuth provisioning or artifact transfer is exposed.
- Native activation and rootless Caddy/API/worker/client deployment profiles are
  separate. Cockpit uses the installed CLI, protected local API settings and
  approved host interfaces; browsers hold no bearer. Exact candidate/base guards
  preserve privileged atomic installation and backup.
- Structured execution correlation and nested secret redaction support concurrent
  metadata requests. Small server event-page limits drain within existing finite
  budgets without losing terminal results or reconnect handles. Consumer export
  and durable archive formats remain compatible.

Local annotated `v0.2.0` identifies deployment commit `11ddd55`; application
artifacts use clean source `481fcc4`. TLS/authentication, registry/client and
non-killing drain passed locally, but SELinux blocked API-container access to the
private worker. Host-origin probes did not prove that connection. **Rollback to
0.2.0 restores this limitation** unless separately corrected.

Rollback retains the independent guard, original lock inodes, both operation
stores, scheduled handles and reviewed manager bindings. A retained native
0.1.10 tree is not an automatic rootless rollback target. This release did not
clear NAS, calendar or other-host acceptance. Base and REST-only installations
remain supported independently of MCP. HTTPX/HTTPCore and optional transport
packages use the locked dependency closure.

## v0.1.10 — 2026-09-14

Completed journals unrelated to selected quarantine entries no longer block
cleanup solely because they use an older checkpoint sequence. Selected source
publications and their recovery proofs still require full validation, and
unfinished work and unsupported records still refuse cleanup. No archive
formats change.

## v0.1.9 — 2026-09-14

Quarantine cleanup also accepts valid early download journals that have no
publication ID, once committed recovery proves their rollback. The runbook
documents immediate recovery of proven empty staging after an explicitly
authorized sync interruption, preserving cached downloads for restart. This
supervised exception leaves the configured age threshold and automatic
recovery policy unchanged. Durable archive formats remain compatible.

## v0.1.8 — 2026-09-14

Recovered staging can now be cleaned with explicit transaction IDs through
`quarantine --dry-run` and `quarantine --apply`. Cleanup requires terminal
publication and committed recovery evidence, refuses unfinished transactions
and unknown content, and removes only empty directories or files freshly
verified against a retained current publication. Anchored filesystem operations
protect the deletion boundary; interrupted cleanup can be safely retried.
Original journals, published models, and durable JSON formats remain unchanged.
Cockpit recognizes the cleanup event in its activity feed.

Rollback to 0.1.7 preserves the three-revision policy and existing archive
formats; it simply lacks the new cleanup command.

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
  storage requirements, loopback quickstart, public-repository, and developer
  documentation now describe the deployed system.
- A failed run report may retain warnings observed before a later failure.
  This is a schema-version-1 field-combination widening: **rollback to 0.1.3
  only when the newest sync report uses an older-valid combination, or after a
  later compatible 0.1.4 sync supersedes it.** 0.1.3 rejects a mixed
  failed-plus-warning report as `HFVER007`; `status` silently falls back to an
  older readable report (`docs/deployment-centos-stream-10.md` §14).

## v0.1.3 — 2026-07-27

The health headline cannot go quiet: an unparseable `refs/current.json` — the
one file a consumer must read — is now a durable `HFVER008` finding at exit
`40`, where 0.1.2 reported the archive clean.

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
  list is asserted against the matrix itself rather than maintained by hand.
- Architecture §7.4 reconciled doc-to-code on `cleanup_deferred`: nothing
  ever recorded that checkpoint, and a prune journal carrying it is now
  refused as `HFTXN002`.

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
second client, reboot persistence, and the quarterly verification timer — separate operator
acceptance requirements described in the deployment guide.
