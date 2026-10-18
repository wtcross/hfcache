# Changelog

Releases are deployed first and tagged for what is deployed
(`docs/progress.md` decisions 75 and 79). The annotated tags carry the
complete release notes; this file is the browsable summary. Versions 0.1.0
and 0.1.1 exist only as install targets under `/opt/hfcache/releases` — one
proved the install mechanism, the other gave rollback somewhere to go — and
were never releases.

## Unreleased

Local metadata orchestration now uses transport-neutral query services.
`status` includes unmanaged published repositories, and `status`/`list` accept
their explicit selectors as documented. Read-only evidence services validate
exact report/reference/manifest identity and contained locators. Durable archive
formats and the consumer export remain unchanged. REST/CLI migration and MCP
remain in progress under the [active plan](docs/plans/2026-10-17-plan-rest-api-and-mcp.md).

All operational commands now delegate to typed services. Non-estimate
verification holds the common archive lock and storage preflight through scope
resolution, hashing, report write and catalog merge, preventing competing
verification updates from losing unrelated state. Probing diagnostics and
confirmed initialization also serialize on that lock. Dry runs and metadata
reads remain lock-free; durable formats are unchanged.

Execution correlation now stays within each task and worker thread, with stable
run identities and optional request/operation IDs. Shared verification no longer
toggles process-wide Hub networking flags. Registered opaque credentials are
redacted from nested diagnostics and exception output. Daemon startup primitives
support the HTTP server and isolated executor described below.

Server configuration now has its own strict schema and explicit protected bearer
sources. Fixed reader/writer capabilities, safe credential loading and fresh
archive-policy snapshots provide the authentication boundary for later routes.
HTTPX is a direct base dependency; FastAPI/Uvicorn are an optional `server`
extra. Installing dependencies alone starts no listener or production installation.

Authenticated REST metadata is now available through an injectable application
and explicit `serve` bootstrap, with one lifespan for Unix/TCP, bounded queries,
safe errors/pages/streams and fresh policy snapshots. Shared readers reject
unsafe paths and inconsistent evidence without repairing an archive. References
retain published-relative locators; the API-backed CLI and MCP remain planned. Tests use disposable sockets; no production server was started.

Operation admission now has an independent local JSON receipt/key authority,
bounded sanitized events/results and authenticated observation. Matching retries
retain their original binding across policy changes and credential rotation.
Startup never replays unfinished history; explicit interruption records uncertainty.
Retention never evicts unexpired keys or uncertain work for capacity. No
production state was created or changed.

The daemon now has one bounded execution lane with one queue/lock waiting
deadline and an under-lock admitted-policy check. Private verification delegates
through a peer-checked bounded Unix protocol with exact durable outcomes and
restart reconciliation; accepted work is never automatically replayed. Installed
systemd/no-IP enforcement remains later work. No in-process production verification fallback or MCP dependency is added.

Typed REST commands now admit sync, all actual verification modes, installed
planning and explicit read-only/probing diagnostics with durable keyed 202
receipts. Status/events and exact terminal Envelopes preserve domain outcomes;
losing an observer does not cancel execution. Installed configuration validation
is an immediate query. Strict authenticated JSON/role boundaries forbid request
paths, credential overrides and implicit probes. A trusted startup Hub token-file
option supports development; candidate authority assessment supports the bounded
validation/planning pipeline below. No new durable format/dependency,
MCP capability or production operation is introduced.

Typed REST maintenance now separates reader previews from writer applies for
prune, purge, recovery and quarantine, plus exact-manifest repair and guarded
initialization. Every route uses keyed admission and exact domain results;
previews grant no future apply authority. Locked fresh policy/scope/evidence
checks preserve unknown data, audits, commit recovery and grace periods. Repair
audit reasons redact registered API/Hub secrets after credential resolution.
Initialization alone needs the disabled-by-default server maintenance gate,
confirmation and the configured root/UUID restated; startup/health/recovery never
initialize. All 29 HTTP mode rows now have resources; mutating CLI/host/MCP
acceptance remains later work. No production operation,
new durable format or runtime dependency is introduced.

An independent synchronous typed API client and strict schema-1 reader settings
now support explicit endpoint/API credential selection, verified TLS/Unix sockets,
finite response/page/read-retry/poll budgets and strict response/identity checks.
Old operation fingerprints and exact domain results are preserved. Lost POST
acknowledgement retains its original key and uncertainty without automatic replay.
Reader hosts need no archive policy/mount/Hub credential or server extra. New CLI
selection options drive reader modes; mutating CLI migration remains API-013. Client
config/protocol failures exit 10 and connectivity/uncertainty exit 20. No new durable
archive shape, dependency, MCP or production operation is introduced.

Read CLI modes now use the authenticated API with complete finite pagination,
consistent inventory/revision joins and exact server Envelope identities/times/
exits. Help/local version and explicit `config validate --local` remain bootstrap;
API errors never fall back to a local archive. Bounded candidate TOML content is
validated separately from authority compatibility, including unknown compatibility
when installed policy is broken. Candidate planning rechecks installed authority
before installed credential use, retains installed admitted fingerprints and old
installed-plan key digests, and never installs configuration. All 29 HTTP parity
rows are implemented; side-effecting CLI and installed-host/MCP gates remain.
Unix client connections now close failed sockets through public HTTPX/HTTPCore
interfaces; HTTPCore is direct at its already-locked 1.0.9 version. No new package,
version, durable shape or production operation is introduced.

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
