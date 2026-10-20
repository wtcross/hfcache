# hfcache invariants

This is the living register of current system constraints. It collects the current contracts; the linked documents
retain their detailed validation rules, checkpoint tables, and operational
procedures. The [ADR index](adr/README.md) records why these boundaries exist.
Historical decisions do not override a later, explicitly superseding decision.

An invariant describes a guarantee or constraint, not a snapshot of a deployment
or an implementation preference. Filesystem guarantees apply at the observable
boundaries defined in [architecture §6–§7](architecture.md#6-filesystem-invariants),
including recoverable crash states; they do not claim that several independent
filesystem operations form one atomic operation.

## Using this register

Requirements retain stable identities. Detailed contracts define scope and
validation; ADR status/amendment links explain why a requirement changed.
An explicitly labelled conformance gap is not an enforced guarantee. Source and
meaningful verification links identify enforcement; a documentation entry alone
does not establish it.

Read only the affected areas:

| Area | Start here |
| --- | --- |
| Archive identity, NFS, initialization | [Identity and location](#identity-and-location) |
| Hub ingestion, publication, hashing, paths | [Snapshots and publication](#snapshots-and-publication) |
| Retention, deletion, repair | [Retention and repair](#retention-and-repair) |
| Journals, crash recovery, quarantine | [Transactions and recovery](#transactions-and-recovery) |
| Download overlap and resource admission | [Bounded synchronization](#bounded-synchronization) |
| Configuration, credentials, authorization | [Configuration and security](#configuration-and-security) |
| JSON, CLI, verification confidence | [Durable formats and reporting](#durable-formats-and-reporting) |
| Downstream copies and serving | [Consumer boundary](#consumer-boundary) |
| Browser management | [Cockpit boundary](#cockpit-boundary) |
| Dependencies, tests, implementation model | [Framework and engineering](#framework-and-engineering) |

## Identity and location

- **`FS-01`, `FS-03`** — The versioned `.hfcache-root` sentinel identifies the
  archive. Its UUID must equal `storage.archive_id`; a mismatch is fatal and
  must never be ignored, regenerated, or repaired automatically.
- **`FS-02`** — Before mutation, prove that the archive root is an actual
  read/write NFS/NFSv4 mount distinct from its parent. A directory at the
  expected pathname is insufficient.
- **`FS-04`** — Staging and its publication destinations must share the archive
  filesystem; promotion must use an atomic rename rather than a cross-device
  copy. Explicit copy publication changes how files reach staging, not the
  atomic promotion requirement.
- **`FS-21`–`FS-23`** — Only the explicit initialization operation, through
  CLI `archive init` or the guarded REST configured-target resource, creates the
  sentinel and initial layout; never sync, recovery, startup, health or a timer.
  It refuses existing archive identity, unknown content and symlinks; only the
  documented empty, correctly owned and moded `published/` and application-owned interrupted-init
  states may be adopted or retried. The sentinel is written last and never
  rewritten. This deployment already exists: agents must never run init.
- **`AD-17`** — Exactly one host has archive write authority, enforced by the
  server's exact-host export. Mutation and verification share a local exclusive
  lock under `/run/hfcache`; there is no NFS lock or second writer host.

Contract: [architecture §5–§7](architecture.md#5-filesystem-layout),
[CLI initialization and doctor](cli.md#archive-init), and
[recorded deployment scope](deployment-status.md).
Enforcement: [storage](../src/hfcache/storage.py),
[preflight](../src/hfcache/preflight.py),
[initialization](../src/hfcache/archive.py), and
[locking](../src/hfcache/locking.py).
Evidence: [preflight tests](../tests/unit/test_preflight.py),
[initialization tests](../tests/unit/test_archive_init.py),
[locking tests](../tests/unit/test_locking.py), and opt-in
[real-mount tests](../tests/system/test_live_mount.py).

maintenance routes transport enforcement: explicit confirmation/restatement of configured
root/UUID, writer capability and the disabled-by-default initialization-only
maintenance gate; see [decision 117](adr/decision-117.md),
[typed routes](../src/hfcache/api/maintenance.py) and
[HTTP initialization tests](../tests/unit/test_api_maintenance.py).
A request cannot choose a different archive, and disabling the gate after restart
refuses POST retries without hiding original operation observation.

## Snapshots and publication

- **`AD-01`–`AD-03`** — The archive unit is one complete model or dataset
  repository at one resolved, full immutable commit SHA. Resolution precedes
  download, and subsequent Hub calls use that SHA. First sync captures the
  first observed revision; later runs capture what they observe. Git history,
  skipped intermediate commits, external dataset payloads, and implicit
  transitive downloads are outside completeness (`NG-01`–`NG-05`, `NG-07`).
- **`AD-08`, `FS-13`** — Hub access and canonical-cache inspection use supported
  `huggingface_hub` APIs through the injectable adapter. No Hub/Git CLI
  subprocesses or cache-directory-name parsing may infer blob locations.
- **`AD-09`, `AD-10`** — The canonical Hub download cache is private operational
  state. The consumer product is a complete immutable tree of ordinary files
  and directories with the repository's relative paths, never cache symlinks.
- **`AD-11`** — Hardlink publication is the default. Copy publication requires
  explicit configuration and capacity admission; unavailable hardlinks must
  fail before download, never trigger a silent fallback. Published files must
  never be chmodded: they may share the cache inode. The staged tree root must
  receive its explicit published directory mode before promotion (§5.2).
- **`AD-18`, `FS-15`** — Every newly introduced unique physical object must be
  locally read and SHA-256 hashed before publication. Cross-run digest reuse
  requires current proof of the same physical inode and size as an already
  verified retained publication, with the reuse source recorded. Cache paths,
  mtimes, historical inode numbers, Git SHA-1s, ETags, and Xet identifiers are
  never substitutes for that proof.
- **`AD-18`, `FS-15`** — Within one ingestion operation, hardlink staging may
  carry a digest forward only after source and destination prove the exact
  `(device, inode, size)` observed by that operation's hash. Failed identity
  proof removes the unproven staging entry and prevents publication. This
  transient identity never becomes durable manifest/journal provenance;
  `hashed = true` still records the operation's own read. Copy mode hashes its
  distinct landed object and compares it with the ingestion digest.
- **`AD-15`, `FS-09`, `FS-15`** — Treat repository content as hostile data:
  never execute, import, unpickle, instantiate it, or enable `trust_remote_code`.
  Validate repository path grammar and containment before use, reject special
  files and escapes, and reject NFC/case-fold collisions. A cache symlink is
  acceptable only when it resolves to a regular file inside the operation's
  approved cache root; published files are ordinary files.
- **`FS-05`–`FS-07`** — Published instances and expected manifests are immutable.
  An instance may only be renamed away wholesale. Repair creates a new instance
  and manifest preserving the original expected path/size/digest set and the
  original manifest byte-for-byte; later observations never redefine evidence.
- **`FS-08`–`FS-11`** — References are versioned objects replaced by atomic
  rename after both their complete tree and manifest are durable. Per-SHA refs
  define the retained set; current names a retained SHA. Reference `tree` and
  `manifest` paths resolve relative to `published/`; other durable artifact
  paths resolve relative to the archive root.
- **`FS-16`, `AD-12`** — Manifests and references are authority; catalogs are
  derived, rebuildable indexes, never a database or an independent authority.
  Historical tag snapshots have the narrow last-observed-label authority (`INV-018`); they cannot establish archive membership or integrity.

Contract: [architecture §3, §5.2–§7.3](architecture.md#3-architecture-decisions),
[schema path conventions](schemas.md#1-conventions), and
[security T-01–T-04](security.md#3-threats-and-controls).
Enforcement: [Hub adapter](../src/hfcache/hub.py),
[ingestion](../src/hfcache/sync.py), [hashing](../src/hfcache/hashing.py),
[paths](../src/hfcache/paths.py), and
[publication](../src/hfcache/publication.py).
Evidence: [Hub tests](../tests/unit/test_hub.py),
[path tests](../tests/unit/test_paths.py),
[publication identity/race tests](../tests/unit/test_publication.py), and
[complete-sync tests](../tests/unit/test_synchronize.py).
Metadata enforcement: [shared no-follow reader/budgets](../src/hfcache/metadata.py),
[query identity/confidence checks](../src/hfcache/services/queries.py), and
[read-boundary regressions](../tests/unit/test_query_boundary.py), metadata lifecycle.
History: `Hub access` (`45f1ccf`) established physical-object hashing;
`synchronization` (`92ebdba`) added same-operation hardlink identity proof.

## Retention and repair

- **`AD-04`, `AD-05`, `FS-20`** — Retention defaults to three unique SHAs;
  explicit five remains supported. Order is immutable publication generation,
  never a timestamp or a publication ID; current is protected from ordinary
  retention. Allocation considers retained manifests and pruned audit records,
  never reuses a generation for a different SHA, and permits crash-induced
  gaps. Reobserving or repairing a SHA preserves its original generation.
- **`AD-06`** — Upstream errors, disappearance, credential/gate revocation,
  disabled configuration, and configuration removal never delete retained
  content. Automatic retention follows successful new publication. Explicit
  `prune` may finish deferred retention or apply a lower configured limit;
  changing configuration alone does not prune. One prune invocation removes at
  most one eligible revision per repository, so lowering the limit may require
  repeated reviewed prune rounds.
- **`AD-07`** — Dependencies are detected only from known static metadata and
  recorded as warnings and manifest evidence. They are never implicitly
  downloaded. Warnings alone do not change exit `0`; dependency archiving
  requires explicit repository configuration.
- **`FS-14`** — Delete canonical Hub cache content only through supported cache
  APIs. The sole filesystem-deletion exception is an application-owned isolated
  repair cache, removed wholesale after its content is durable in publication.
  Published hardlinks preserve bytes even after canonical-cache deletion.
- **`TX-06`** — Prune's `prune_logically_committed` checkpoint is the deletion
  boundary: before it, restore tree, manifest, references, and catalog; at or
  after it, never republish and finish only audit/physical cleanup. Preserve
  byte-for-byte manifests plus reason records. Remove emptied SHA/namespace
  containers only with `rmdir`, preserving any remaining instance or entry.
- **`AD-20`** — Whole-repository purge requires explicit unmanaged selectors or
  `--all-unmanaged`, exactly one of dry-run/apply, and renewed scope validation
  under the writer lock. A configured repository is ineligible. Validate the
  entire shallow layout before mutation; unknown entries or grace-period
  repair instances refuse the repository. Each repository has its own prune
  transaction and the same commit boundary, and audit is never purged.
- **`AD-13`, `FS-07`** — Repair downloads the same immutable SHA into a fresh,
  isolated transaction cache; it must reproduce the original manifest and
  verify the landed replacement before switching any reference. It preserves
  generation, uses a new publication ID, and keeps the retired instance at its
  original locator for at least 168 hours. Post-grace evidence enters
  quarantine and is never automatically deleted.

**Known conformance gap.** The lifetime-generation and audit-union
requirements above remain the declared `AD-05`/`FS-20` contract, but current
implementation evidence does not establish them.
[`next_generation`](../src/hfcache/publication.py) scans retained references
only. The regression test
`test_a_pruned_sha_that_returns_is_republished_into_a_fresh_container` in
[the sync suite](../tests/unit/test_synchronize.py) explicitly expects a pruned
SHA to return with a fresh generation of 7. Retained-SHA reobservation and repair
preserve their generation. Whole purge can empty retained references while audit
survives. The stronger lifetime/audit-aware allocation requirement remains an
explicit conformance gap, not a deployed guarantee. Current cannot be reconstructed
solely from maximum generation: valid sync can return to an older retained SHA.


Contract: [architecture retention, purge, and repair](architecture.md#74-prune-transaction),
[storage policy](configuration.md#4-storage), and
[prune/purge/audit schemas](schemas.md#8-prune-plan).
Enforcement: [retention](../src/hfcache/retention.py),
[purge](../src/hfcache/purge.py), [repair](../src/hfcache/repair.py), and
[generation allocation](../src/hfcache/publication.py).
Evidence: [retention tests](../tests/unit/test_retention.py),
[purge rollback/commit tests](../tests/unit/test_purge.py),
[crash tests](../tests/unit/test_crash_injection.py), and
[complete-sync tests](../tests/unit/test_synchronize.py).
History:  (`7370af2`) adds explicit purge;
`retention` (`ec3e630`) replaces the original fixed-five default. The schema-1
audit reason `sixth_unique_revision_published` remains its historical name for
exceeding the configured limit; it does not require retaining five.

maintenance routes transport enforcement retains one-round prune, unmanaged-only purge,
original-manifest repair and canonical-cache deletion through the
[typed maintenance routes](../src/hfcache/api/maintenance.py).
[Real HTTP/domain tests](../tests/unit/test_api_maintenance.py) and
[adversarial maintenance tests](../tests/unit/test_api_maintenance_adversarial.py)
cover fresh locked scope/proof and exact classified outcomes. Previews are keyed
control-state jobs and confer no deletion authority; retention remains unchanged.

## Transactions and recovery

- **`AD-14`, `FS-17`, `TX-01`, `TX-02`** — Normal archive mutation opens a
  durable transaction journal before its first mutation. Append a checkpoint
  only after the named operation is durable. Journals describe filesystem
  facts, never instructions to replay. The resolved-quarantine exception below
  reuses existing terminal journals and creates no new one. `INV-018` separately
  permits independently atomic supplemental records and their approved namespace
  creation after initialized preflight; no existing transaction is exempted.
- **`TX-03`–`TX-05`** — Checkpoints are append-only, consecutively sequenced,
  and supported by re-observable evidence. Each state-changing step has its
  own atomic boundary; no ordering between separate renames is assumed.
  Recovery validates the evidence and is idempotent.
- **`TX-06`, `AD-16`, `FS-19`** — Prefer reportable over-retention to losing
  content. Unknown files, unsupported state, impossible checkpoint sequences,
  inconsistent evidence, and ambiguous targets must be reported and preserved,
  never guessed at, rewritten, or deleted. A recovery refusal leaves an
  operator-visible reason and stops the mutating command before Hub contact.
- **`TX-07`** — A mutating command reconciles unfinished journals under its own
  exclusive lock before Hub contact or its new archive work. A sync excludes
  its own active run journal. Resolved journals need no replay; a
  `needs_operator` journal remains unresolved. Quarantine cleanup and supplemental
  refresh instead refuse unfinished work without recovering unrelated transactions.
- **`FS-18`** — Acting on stale transaction artifacts requires a recognized
  transaction-ID name, its journal, and the configured minimum age. Age alone
  never grants deletion authority. The sole early-recovery exception is the
  supervised cancellation in architecture §7.8.2: confirmed writer termination,
  the exclusive lock, exact reviewed run/journal evidence, and empty
  `staging_created`-only staging permit an explicitly scoped zero-hour recovery
  plan. The configured automatic age policy remains intact.
  For API-backed execution, prove termination of the actual operation/executor;
  a stopped observer/client service, vanished PID or free lock alone is not that
  proof (decision 115). The supervised exception is not a cancellation endpoint.
- **`TX-01` exception, `FS-19`** — Explicit quarantine cleanup is limited to
  selected transaction IDs whose completed failed publication and matching
  committed recovery journal prove abandoned pre-publication staging. Validate
  the complete requested batch before removing anything; apply holds the lock
  and preflight guards, and revalidates each deletion. Empty directories need
  no replacement bytes; every file removed must match both the current
  retained manifest and freshly hashed retained content. Unlink only proven
  files, then `rmdir` empty directories. A crash leaves a reprovable subset.
- **`AD-16`, `FS-19`** — Quarantine cleanup must preserve repair evidence,
  unvalidated publication trees, symlinks, special files, and unexplained
  entries. Selected authority journals require full checkpoint validation;
  unrelated completed legacy journals need not match today's checkpoint
  sequence and cannot supply deletion authority. Unreadable or unsupported
  journal records and unfinished work still refuse cleanup. Original journals
  and retained publications remain unchanged; there is no implicit all-entry
  selector or scheduled quarantine deletion.

Contract: [architecture §7](architecture.md#7-transaction-and-crash-recovery-boundaries),
[recovery runbook](recovery.md), and
[CLI quarantine](cli.md#quarantine).
Enforcement: [transactions](../src/hfcache/transactions.py),
[recovery](../src/hfcache/recovery.py), and
[quarantine](../src/hfcache/quarantine.py).
Evidence: [checkpoint-contract tests](../tests/unit/test_transactions.py),
[recovery planning tests](../tests/unit/test_recovery_planning.py),
[crash injection](../tests/unit/test_crash_injection.py), and
[quarantine proof/race tests](../tests/unit/test_quarantine.py).
History: `quarantine cleanup` (`1ad4181`), `quarantine cleanup` (`7b5e4e2`), and
`quarantine cleanup` (`c2b52ff`) define the narrow cleanup and cancellation exceptions.

maintenance routes's [maintenance transport](../src/hfcache/api/maintenance.py) calls these
same services; it accepts no executable preview/plan. Queued work revalidates the
admitted fingerprint under lock, and each apply reconstructs current scope and
proof. [HTTP/domain](../tests/unit/test_api_maintenance.py) and
[adversarial tests](../tests/unit/test_api_maintenance_adversarial.py) cover stale
scope, ambiguous/altered evidence, original audits and lost observations;
[decision 117](adr/decision-117.md). No new checkpoint or deletion authority.

## Bounded synchronization

- **`AD-19`** — Continuation-enabled sync resolves and estimates its selected
  queue and admits aggregate download plus copy-publication capacity before the
  first transfer. One background producer may overlap later downloads with
  foreground hashing/publication; only one repository transfer is active.
  `sync.max_workers` is that transfer's file-worker budget, never a multiplier
  for concurrent repository transfers.
- **`AD-19`** — Publication, generation assignment, results, and error selection
  remain deterministic in configuration order. Strict stop-on-error sync stays
  serial. No worker may outlive the whole-run archive lock: unexpected
  foreground failure cancels unstarted work and joins the active transfer.
- **`AD-19`** — Serialize Hub cache mutation with retention's whole-cache scan;
  defer queue-ahead retention until all downloaded snapshots are consumed.
  Every transfer rechecks capacity before starting. Copy staging rechecks and
  holds the allocation guard while it writes; hardlink staging needs no copy
  allocation pause. Queued publications use ordinary independent journals,
  never a new queue-wide durable commit point.

Contract: [AD-19](architecture.md#ad-19--download-ahead-with-one-bounded-producer),
[worker settings](configuration.md#5-sync-verification-repair), and
[resource controls T-11](security.md#t-11--resource-exhaustion-turns-into-data-loss).
Enforcement: [sync producer/admission](../src/hfcache/sync.py) and
[Hub cache guard](../src/hfcache/hub.py).
Evidence: [queue, interruption, strict-mode, and capacity tests](../tests/unit/test_synchronize.py).
History: `synchronization` (`54e4671`), decision 94.

## Configuration and security

- **`INV-001` — Configuration is explicit, strict, and immutable.** Require
  schema version 1, reject unknown keys and coercions, normalize absolute
  filesystem paths, and reject invalid or duplicate repository identities
  before locks, network, or mutation. `config validate` uses the same
  validation and changes nothing. Keep archive policy, restart-only server
  transport/auth and independent client settings in separate schemas. A server freezes
  freshly validated archive snapshots per request/admission and pins root/UUID
  to startup authority; it never hot-switches archives (decision 112).
  Client configuration has independent required integer schema 1 and explicit
  endpoint-group/source precedence; it loads no archive policy (decision 118). Pure
  candidate syntax assessment is separate from authority compatibility; no request
  can redirect installed credentials through candidate endpoint/source changes
  (decisions 116/119). Valid incompatible syntax remains valid; unavailable installed
  policy gives unknown compatibility, never permission to plan. See
  [configuration §1–§2, §6](configuration.md#1-validation-rules-that-apply-to-every-field).
- **`INV-002` — Credentials have only explicit sources and never become
  evidence.** Accept only an explicit token file or systemd credential, with
  the documented precedence and file validation. Disable ambient discovery;
  every Hub call passes an explicit token or `False`, never `None`. Missing
  optional credentials permit anonymous access; installed unusable credentials
  fail. That anonymous fallback applies to Hub policy; API writer authentication
  is required and an unprovisioned optional API reader grants no capability.
  API and Hub credentials are distinct explicit sources, never ambient reuse.
  The shipped Cockpit rootless launcher mounts API-only Podman `hfcache.api`
  inside its finite client; no host ImportCredential applies. Native named
  systemd credentials remain a separate supported source. Hub authority stays
  daemon-side and the page never handles a bearer.
  A reader resolves only its selected protected API file/named systemd source;
  no Hub/netrc/ambient token or anonymous fallback after source failure.
  The server's explicit Hub file is a trusted startup option, never request input;
  candidate validation resolves no credential. Candidate planning rechecks all six
  installed authority fields after queue waiting before using installed credentials,
  including credential name excluded from the policy fingerprint (decision 119). Repair audit reasons
  redact registered credential values after credential resolution and before
  durable domain writing (decision 117).
  Never emit secrets in configuration errors, logs, manifests, journals,
  reports, operation state or fingerprints. Register exact resolved opaque credentials before
  use; sanitize nested diagnostic contexts and exception/public output as well
  as recognized token shapes (decision 111). See [configuration §7, §9](configuration.md#7-credentials)
  and [security T-07](security.md#t-07--a-token-leaks).
- **`AD-21`** — Only `hub.token_mode = "required"` enables private/gated
  repository scope, and a credential must resolve before any Hub request.
  Disabled and optional modes remain public-only even with a token. Every
  consumer of the single publication export must be authorized for every
  archived repository; there is no per-repository ACL promise. Revocation
  stops future fetches and does not delete retained content. `NG-06` is retired.
- **`INV-003` — Transport, host, and export boundaries remain enforced.** Hub
  endpoints require HTTPS and TLS verification. Archive services run as the
  unprivileged service identity with locked release dependencies; consumer
  writes are denied by a server-side read-only export. SELinux stays enforcing
  and systemd hardening must not be weakened to make a test or operation pass.
  Management off-host access requires verified TLS or an explicitly trusted
  local TLS proxy, and Unix-socket access still authenticates.
  Only supported actual Uvicorn Unix transport scope may use native unprefixed
  REST paths when TCP has a public prefix. Per-request links/schema views cannot
  mutate global prefix/cache state or trust forwarded-prefix authority; TCP keeps
  configured prefix/TLS/proxy/Host/Origin checks (decision 123).
  Native scope requires both `client=None` and corroborating absolute Unix-path/
  None-port `server` evidence; peer absence on socket error cannot bypass prefix
  or proxy-TLS checks. Missing/malformed local evidence fails closed.
  See [security §2–§5](security.md#2-trust-boundaries),
  [deployment](deployment-centos-stream-10.md), and
  [recorded deployment scope](deployment-status.md).
  scheduled observation packages no-IP/offline and credential-source masking around the actual
  private verifier; the AF_UNIX scheduled client uses API credentials separately.
  Custom source locations require explicit masks/probes, and repository unit/
  activation tests do not establish installed cgroup/SELinux/NFS enforcement.
  Packaged enforcement: [actual API service](../packaging/systemd/hfcache-api.service),
  [private worker service](../packaging/systemd/hfcache-verification.service),
  [executor-aware probe](../scripts/check-hardening.sh) and
  [probe implementation](../scripts/hardening-probe.py).
  Evidence: [unit contracts](../tests/unit/test_systemd_units.py) and
  [probe fixtures](../tests/unit/test_hardening_probe.py), decision
  [121](adr/decision-121.md); installed acceptance remains separate.
  **guarded deployment scoped rollout (2026-10-18, [decision 126](adr/decision-126.md)).**
  Current local-host deployment authority requires a persistent client read-only
  NAS guard, blocked legacy writers and retained actual-executor/local-flock
  quiescence proof. NAS content/metadata writes, relabel/chown/copyup and other-
  host changes are forbidden; sync remains stopped and verify scheduling disabled.
  Local disposable/container proofs do not pass forbidden real storage checks.
  **rootless runtime profile (2026-10-18, [decision 127](adr/decision-127.md)).**
  Explicit rootless user services and a system target bridge use Caddy/one API/
  isolated FD3 worker and container clients. Immutable never-pull/no-replace/
  no-init/no-auto-remove persistent-role commands, infinite non-killing drain and actual libpod
  cgroup/peer/secret proof preserve unknown execution. No rootful/privileged/
  label-disable/control-socket fallback; shared original local lock and read-only
  NAS/policy-directory boundaries remain. Actual disposable container proof binds
  no NAS; packaging cannot clear installed or full storage acceptance holds.
  Finite stateless observer containers alone may auto-remove without canceling
  server execution or discarding receipts/handles. Exact protected execution
  bindings through current select one physical helper/profile/image/config tree;
  missing/copied/drifted bindings refuse, never a disconnected runtime copy.
  Effective manager fragments/drop-ins must be inspected after both-manager reload
  before activation. Enforcement: [fixed helper](../scripts/container-service.py),
  [protected installer](../scripts/install-container-release.py),
  [runtime tests](../tests/unit/test_container_service.py) and
  [selection/rollback tests](../tests/unit/test_container_release_installer.py).
  host read-only guard pins the readonly boot guard/helper outside current, with host
  /proc/1/mountinfo proof before READY and lifetime original-flock ownership.
  A private sandbox's read-only view cannot prove the host mount; the guard is
  not continuous monitoring. Bridge readiness dependency/no user-default app
  autostart and nontruncating boot files preserve the controlled holder transfer.
  Enforcement: [fixed host guard](../scripts/hold-readonly-guard.py) and
  [guard/unit/tmpfiles tests](../tests/unit/test_readonly_guard.py); actual host
  readiness/lock transfer is separately recorded in host read-only guard.
  **Worker listener ownership ([decision 128](adr/decision-128.md)).**
  rootless PID1 startup explicitly creates its own private socket after rejecting
  inherited activation/FDs before resources. Instance/pinned-parent/created-inode
  ownership lasts through joined shutdown and exact cleanup; existing/replaced
  paths remain. Owned socket/archive lexical disjointness and mountinfo-only
  local-filesystem proof precede parent traversal/bind, with no realpath/NAS stat.
  Worker writable private directory/API read-only view and real
  container-proxied READY change no SELinux/seccomp/credential authority. Native
  FD3 activation stays strict. Recorded 0.2.1 installed peer connectivity is distinct from outstanding NAS
  workload acceptance; rollback to 0.2.0 retains its connection limitation.
  See [deployment status](deployment-status.md).
  Enforcement/evidence: [owned listener](../src/hfcache/verification_listener.py),
  [bootstrap](../src/hfcache/verification_worker.py) and
  [kernel/cleanup tests](../tests/unit/test_verification_listener.py).
- **`INV-004` — Capacity admission includes publication cost and reserve.**
  Require free capacity beyond estimated download bytes, explicit copy-mode
  publication bytes, and the greater of the GiB and percentage reserves.
  Fail closed before starting an unaffordable transfer. Advisory local Xet
  cache limits warn; they are not a filesystem reservation or deletion license.
  See [configuration §4](configuration.md#4-storage) and
  [CLI plan](cli.md#plan).

Enforcement: [configuration](../src/hfcache/config.py),
[credentials](../src/hfcache/credentials.py), [Hub policy](../src/hfcache/hub.py),
[shared redaction](../src/hfcache/redaction.py), [logging](../src/hfcache/logging.py), and
[capacity/preflight](../src/hfcache/preflight.py).
Evidence: [configuration tests](../tests/unit/test_config.py),
[credential tests](../tests/unit/test_credentials.py),
[Hub tests](../tests/unit/test_hub.py),
[redaction tests](../tests/unit/test_logging.py),
[opaque-token and exception tests](../tests/unit/test_execution_isolation.py), and
[preflight tests](../tests/unit/test_preflight.py).
Off-host export enforcement and installed host hardening require the documented
operator acceptance checks; unit tests cannot prove those deployment facts.
History: `Hub access` (`c082f87`), decision 98, supersedes public-only scope.
server authentication enforcement: [server configuration and policy snapshots](../src/hfcache/server_config.py),
[protected API credentials and fixed capabilities](../src/hfcache/api/auth.py),
[optional FastAPI adapter](../src/hfcache/api/security.py),
[configuration/reload tests](../tests/unit/test_server_config.py), and
[adversarial credential/capability tests](../tests/unit/test_server_auth_adversarial.py).
command routes command/authority enforcement: [typed DTOs](../src/hfcache/api/command_models.py),
[shared-service route adapters](../src/hfcache/api/commands.py),
[pure candidate assessment](../src/hfcache/services/candidates.py),
[model/authority tests](../tests/unit/test_command_models.py),
[HTTP/domain tests](../tests/unit/test_api_commands.py), and
[adversarial command tests](../tests/unit/test_api_command_adversarial.py).
Decisions [112](adr/decision-112.md)/[116](adr/decision-116.md) distinguish runtime
route enforcement from installed host acceptance.

## Durable formats and reporting

- **`INV-005` — Durable formats are versioned, deterministic, and atomic.**
  Use the shared JSON serializer: UTF-8, sorted keys, documented array order,
  two-space durable indentation, one trailing newline, UTC microsecond `Z`
  timestamps, lowercase digests, full lowercase SHAs, explicit nulls, and
  logical byte counts. Write a temporary sibling, fsync it, rename, then fsync
  the parent. Reject unsupported versions instead of guessing. Strict models
  reject unknown fields; the journal reader separately preserves unknown
  top-level fields across rewrites (decision 20). Preservation alone grants no
  recovery/deletion authority. See [schemas §1, §10–§11](schemas.md#1-conventions).
  operation control state's independent local receipt/event/reference version rejects missing,
  noninteger, duplicate-key and unsupported state; it does not widen archive
  formats. Receipt/result updates use the same durable serializer and fsync
  boundary. See [schemas §13](schemas.md#13-service-private-operation-control-state).
- **`INV-006` — CLI output and failure classification are stable contracts.**
  `--json` emits exactly one schema-1 envelope on stdout, including failures;
  stderr is display/event output. Quiet preserves warnings/errors and mandatory
  safety handles, including with JSON. Ordinary live events require both output
  streams to be terminals; gap diagnostics remain visible. No-color applies to
  help and human rendering through per-invocation controls.
  Error classes, stable taxonomy codes, and
  exit priority must agree. Warnings alone keep exit `0`; any failed repository
  makes the aggregate run fail. `success` carries no warnings,
  `success_with_warnings` requires them, and `failed` may retain earlier
  warnings alongside its errors. See [CLI §3–§6](cli.md#3-exit-codes) and
  [run reports](schemas.md#6-run-report).
  Execution correlation is context-scoped, captured when emitted and explicitly
  copied into workers; server request/operation IDs cannot replace domain
  run/journal identities. Daemon logger configuration is startup-only.
  Durable `invocation_mode` describes the execution host, not timer or submitter
  origin; API receipts record the authenticated credential-class submitter
  separately (decisions 111/114), without claiming individual user attribution.
  The foreground `serve` bootstrap is a narrow exception: normal daemon
  execution has no terminal success Envelope/stdout, while classified startup
  failures preserve the schema-1 error Envelope under `--json` (decision 113).
  The command service's 202 is admission only; exact result retrieval preserves the shared
  terminal Envelope, including partial failure and domain exit priority.
  The CLI preserves exact server Envelope identity/timestamps in JSON for remote
  reads and completed jobs; human rendering summarizes classified results. Page joins keep the first server invocation metadata,
  include all rows under finite bounds and refuse inconsistent publication evidence.
  CLI observation defaults jobs to classified terminal output, preserving the
  exact stored Envelope in JSON/results. Explicit detach is a
  separately identified schema-1 `operation_admission`, without a fabricated
  command outcome/exit. Show/lookup keep exact server metadata Envelopes.
  Mandatory validated key/accepted-ID safety messages stay on stderr even quiet;
  bounded sanitized event progress never fragments stdout. Observation under small server page/retention caps uses omitted adaptive event
  limits and complete retained-page draining share the same absolute deadline;
  each drain's final empty page counts toward max_pages. Explicit integer limits
  retain their meaning. [Real CLI socket/private-worker integration](../tests/unit/test_interface_integration.py)
  proves exact terminal results and roles without changing admitted identity.
  Client-only no-confirm
  init refusal uses local metadata plus successful inspection evidence; failed
  inspection remains exact server evidence. See [decision 120](adr/decision-120.md).
  Authenticated client-authority presentation preserves exact failed server
  Envelopes rather than renaming their command/result. Successful metadata uses
  a strict nonsecret allowlist; derived hashes/identifiers that collide with a
  registered credential refuse safely before output. A local authority comparison
  cannot replace domain result identity or turn unknown archive UUID into proof.
- **`INV-007` — Verification reports evidence without rewriting it.** Verify
  the complete path set, sizes, and local SHA-256 bytes; an integrity finding
  exits `40`, preserves content/expectations, and never performs repair or
  prune. All non-estimate modes acquire the common lock, prove storage safety,
  then resolve targets, hash, persist the report and read/merge/write the catalog
  before releasing it (decision 110). Atomic replacement does not serialize
  merges. Shared verification constructs no Hub client/credential and changes no
  process-wide offline environment. Verification uses no Hub download.
  Estimates do no hashing and confer
  no verification confidence. Confidence belongs to the exact
  `(type, repository, SHA, publication ID)` instance; absent/unreadable derived
  state or a null publication ID must never raise confidence. Outstanding
  failures survive runs that do not recheck them and clear only through their
  documented successful verification, completed repair, or retention/removal
  rules. See [CLI verify](cli.md#verify) and
  [verification catalog](schemas.md#52-catalogverificationjson).

Enforcement: [models/serialization](../src/hfcache/models.py),
[atomic storage](../src/hfcache/storage.py),
[journal preservation](../src/hfcache/transactions.py),
[reporting](../src/hfcache/reporting.py),
[verification](../src/hfcache/verification.py), and
[command ownership](../src/hfcache/services/commands.py).
Evidence: [golden formats](../tests/fixtures/schemas),
[model tests](../tests/unit/test_models.py),
[journal tests](../tests/unit/test_transactions.py),
[CLI tests](../tests/unit/test_cli.py),
[verification tests](../tests/unit/test_verification.py), and
[verification lock/interleaving tests](../tests/unit/test_command_locking.py).
Correlation/diagnostic enforcement: [execution context](../src/hfcache/services/context.py),
[event capture and copied workers](../src/hfcache/logging.py),
[sync producer](../src/hfcache/sync.py), and
[isolation tests](../tests/unit/test_execution_isolation.py).
Durable shape, enum, and field-combination changes require the
[recorded deployment scope](deployment-status.md); schema version 1 is not a
blanket claim that old binaries accept every later widening.
operation control state control-state enforcement: [receipt models/store](../src/hfcache/api/operations.py),
[golden operation fixtures](../tests/fixtures/schemas/operation-receipt.json),
[lifecycle/idempotency/result tests](../tests/unit/test_operations.py), and
[fault/concurrent admission/retention tests](../tests/unit/test_operation_store_adversarial.py).
Previous-binary compatibility is a separate assessment from schema equality.

## Consumer boundary

- **`FS-12`** — Read one current reference once per copy attempt and copy the
  exact instance it names. Never reread the reference mid-copy and splice
  instances. A vanished or invalid instance is a visible retryable failure;
  restart from a newly read reference rather than accept partial content.
- **`INV-008` — Promotion follows complete local verification.** Resolve ref
  locators relative to the mounted `published/`, validate containment and
  identity, and check both missing/extra paths, sizes, and SHA-256. Assemble in
  temporary local storage and rename only after verification. Consumers mount
  only the read-only publication export and never use it as `HF_HOME` or
  `HF_HUB_CACHE`. See [consumer contract](consumers.md#2-the-contract-in-one-paragraph)
  and [independent implementations](consumers.md#7-doing-it-without-the-helper).
  curated metadata tools discovery retains exact publication IDs and locator bases; partial
  manifest/report pages are explicit projections, never complete durable records.
  Reconstruct all selected collections and validate before consumer verification;
  a vanished requested instance refuses instead of substituting a new current.
  See [MCP metadata tools](mcp.md#available-tools), decision 125.
- **`INV-009` — Copying and serving promotion have separate ownership.** The
  consumer copy identity writes only a new, non-existent destination under
  `<model>/revisions/`; root owns the model root and the serving pointer.
  The helper must never target a live serving path. The launcher serves the
  explicitly named verified directory through read-only, SELinux-labelled
  model/config container mounts. Capacity checks do not promise reserved
  blocks. See [consumer setup and serving](consumers.md#3-copying-a-revision),
  decisions 99–100.

Enforcement and evidence: [copy helper](../examples/copy-revision.py),
[model-store setup](../scripts/setup-hfcache-consumer-model-store.sh),
[serving launcher](../scripts/consumer-serve-hfcache-model.sh),
[model-store tests](../tests/unit/test_consumer_model_store_script.py), and
[launcher tests](../tests/unit/test_consumer_serve_script.py).
The [consumer runbook](consumers.md) records the helper's copy/corruption/retry
acceptance evidence; it is an example consumer, not an application dependency.

## Cockpit boundary

[Decision 134](adr/decision-134.md) requires stage-aware error preservation,
close-aware read recovery and authority-scoped operation handles outside tab
lifetimes. These boundaries are implemented in source.
[Decision 136](adr/decision-136.md) retires the CP-01/09 direct-report exception.
[Decision 135](adr/decision-135.md) replaces manual service starts with keyed
REST jobs and requires fresh protected host-profile permission before effects.
No new workload or deployment authority follows.

[Decision 137](adr/decision-137.md) requires validated read presentation with
explicit failure, partial, unavailable and empty states. Stale/malformed/partial
evidence never grants action readiness. Passive invalidation cannot erase newer
acknowledged evidence in the current connection generation. Browser build provenance, selected
physical release and authenticated API identity remain separate advisory facts;
neither a matching version nor daemon readiness proves writability or active
payload parity. No server capability or execution authority is added.

- **`CP-01`, `CP-02`, `CP-09`** — The plugin uses installed CLI JSON envelopes
  and systemd, never reimplements archive logic or writes archive files. The
  plugin has no direct archive-read exception. Reports use authenticated fixed
  CLI reads with one bounded inventory page and exact run/archive identity.
  A separate bounded read-metadata notice carries cursor/response identity while
  terminal Envelopes remain unchanged. Optional journal events are bounded
  host-local diagnostics and cannot define outcome. Refuse unknown Envelope
  versions and unbounded/malformed terminal
  output. Separately validated bounded progress/safety notices may render and
  reconnect, never grant domain authority or invent outcome/checkpoints/percentages
  (decision [122](adr/decision-122.md)).
  Boundary errors retain validated stage/problem/process facts, withholding raw
  exception/stderr contents. Close/privilege transitions invalidate connections
  and stale UI evidence; bounded read retries never replay mutations. See
  [presentation and connection rules](cockpit.md#4-envelope-and-error-handling).
  Validated original key/ID collection is independent of display truncation or
  abort. Terminal result identities and classified failures remain distinct from
  bridge/process failure and missing or expired observation history.
- **`CP-03`, `CP-04`, `CP-10`** — Mutation needs administrative Cockpit access,
  while CLI work runs as the service identity in a transient unit, never root.
  Manual full sync/verification use the same keyed REST-backed transient client
  as selected jobs. Scheduled observers remain separate; their unit/journal state
  cannot establish a manual result. Respect the single writer lock; report busy
  without bypassing it. Fresh root-only read-only inspection must prove the
  selected indexed deployment and protected explicit permission before archive,
  Hub/control job, configuration, schedule or observer effects. Unknown or drifted
  evidence denies effects; absence of a guard/mask cannot grant permission.
  A held or unconfirmed guard denies archive execution. No native fallback or
  alternate manager is permitted. Metadata and synchronous validation remain
  separate from keyed sizing/diagnostics and archive jobs.
  Page-keyed jobs persist an original key before their submit process starts and
  preserve it across tab/reload. An unresolved record blocks additional keyed
  submissions on that host. Uncertain maintenance Apply cannot reuse an old
  successful dry run; Apply consumes its preview before asynchronous work.
  Capture invocation intent before asynchronous checks/callbacks and use a closed
  plugin command grammar; null job classification cannot forward arbitrary CLI
  text. An acknowledged host mutation followed by a failure remains uncertain
  across tab lifetimes until explicit read-only reconciliation/acknowledgement.
- **`CP-05`–`CP-08`** — Schedule controls affect only the sync timer; never
  manipulate `hfcache.target`, enable the verify timer, or expose archive init.
  The page never reads credentials or accepts tokens; the fixed launcher mounts its
  API-only `hfcache.api` credential inside the fixed rootless client, never Hub
  authority or browser/environment/argument bearers (decision 122).
  Recovery storage contains only validated nonsecret scoped metadata, bounded to
  32 records/64 KiB; corrupt, unavailable or full storage blocks submissions.
  Unresolved records are never evicted. Authenticated metadata binds the trusted
  host, selected profile/endpoint, credential class and confirmed archive UUID;
  unknown/changed authority blocks saved observation. The same CLI process
  compares its expected authority before submission or original-key lookup/wait.
  Restored terminal summaries remain unverified until authenticated observation;
  valid-looking stored metadata cannot unblock another submission on its own.
  Browser storage cannot select an endpoint, replay a POST, cancel work or replace
  an original key merely because history is missing.
- **`CP-11`, `CP-12`** — Config installs follow candidate → successful CLI
  validation → required successful preview → atomic install → exact installed
  content and operational fingerprint confirmation. Required preview success
  covers exact captured selectors/revisions and complete sizing; malformed success
  never grants readiness. Confirmation compares installed
  bytes before/after API validation under the root config flock, including tags
  excluded from policy identity. A retained root config flock and exact candidate/base
  bytes guard the pipeline; incompatible/unknown authority blocks plugin install.
  Guarded stdin uses two bounded canonical ASCII base64 lines on the Cockpit
  text channel. Decode and validate exact UTF-8 documents before filesystem/lock
  effects; malformed frames never create a lock or comparison artifact
  ([decision 138](adr/decision-138.md)).
  Preserve original failed Envelopes and stage causes. Capture draft/base before
  transmission in application memory; uncertain write/install blocks another
  write/install/discard. Read-only inspection creates no files and requires the
  original lock; explicit matching revalidation skips writes. Uncertain install
  needs exact installed/backup proof, explicit confirmation and acknowledgement;
  confirmation gives PID1 a pipe and uses a bounded local collector, withholding
  all output on collection/postcheck failure and preserving original launcher
  status ([decision 139](adr/decision-139.md));
  remount/reload cannot silently reset it. Preview, install, confirmation and
  acknowledgement require the captured authority and administrative session to
  remain current. Retain the predecessor and `0640 root:hfcache` ownership/mode.
  Timer changes use validated calendar drop-ins,
  never edit shipped units.
- **`CP-13`, `CP-14`** — Never weaken host hardening. The plugin ships static
  files; Node tooling is build-time only, adds no Python runtime dependency,
  and generated bundles/node_modules are never committed.
  Frontend-required gates refuse unavailable sources/tools; a skipped frontend
  stage never supplies plugin acceptance. Executed browser and real disposable
  Cockpit/PAM evidence remain separate test layers.

Contract: [Cockpit rules and pipelines](cockpit.md#1-rules).
Enforcement: [CLI/unit API](../cockpit/src/api/hfcache.ts),
[config API](../cockpit/src/api/config.ts),
[schedule API](../cockpit/src/api/schedule.ts), and
[command boundary](../cockpit/src/lib/command.ts).
Cockpit API integration enforcement: [bounded observation runner](../cockpit/src/lib/runner.ts),
[UTF-8 framing](../cockpit/src/lib/stream.ts),
[validated notices](../cockpit/src/lib/events.ts),
[terminal classification](../cockpit/src/lib/envelope.ts),
[scoped registry](../cockpit/src/lib/operation-registry.ts),
[authenticated recovery](../cockpit/src/api/operations.ts),
[client authority metadata](../src/hfcache/client_metadata.py) and
[unit/action allowlist](../cockpit/src/lib/systemd.ts), decision
[122](adr/decision-122.md). The browser can stop only sync observation, start
installed sync/verify clients and control the sync timer; actual API/worker/socket/
mount/arbitrary unit actions are refused.
Candidate enforcement/evidence: [exact-content guard](../cockpit/src/lib/candidate-guard.ts),
[readiness/confirmation pipeline](../cockpit/src/lib/config-pipeline.ts),
[guarded filesystem fixtures](../cockpit/test/candidate-guard.test.ts) and
[pipeline cases](../cockpit/test/config-pipeline.test.ts). These preserve the
privileged host-install boundary and do not prove deployed browser/SELinux behavior.
Evidence: [plugin tests](../cockpit/test) and the
[operator install/acceptance runbooks](cockpit-plugin/README.md).

## Framework and engineering

- **`INV-017` — Diagnostics require explicit authority and honest evidence.**
  Import/help/default/dry-run never contact managers, credentials, archive or
  network. A disposable workload proves target, UUID, filesystem, ownership and
  existing local lock before writes, revalidates under lock, and confines archive writes
  to its owned health child. Preserve unexplained or substituted entries.
  Production and guarded/read-only targets refuse archive-write probes.
  Never mutate real host settings as a denial test. Expected action refusals,
  missing prerequisites and installed control attribution are distinct results.
  Enforcement: [probe](../scripts/hardening-probe.py) and
  [fixture tests](../tests/unit/test_hardening_probe.py);
  rationale: [decision 131](adr/decision-131.md).
- **`FW-01`, `FW-02`** — Use ordinary deterministic Python functions and typed
  append-only records. Journals are recovery evidence, never an orchestration
  engine. No workflow/DAG/actor/task/agent framework or mutable archive database.
- **`FW-03`, `FW-04`** — Runtime dependencies are `huggingface-hub`, `pydantic`,
  `typer`, the resolved Hub client's required transfer backend, and the direct
  base HTTPX/HTTPCore client; FastAPI/Uvicorn are optional `server` dependencies
  (decision 112, implementing the decision 108 exception). Use the
  standard library for TOML, JSON, hashing, filesystem work, locking, and
  logging. An addition needs a recorded material correctness argument, not
  convenience or fewer lines.
- **`INV-010` — Safety checks and evidence survive routine execution.** Source
  safety checks raise exceptions and never depend on removable assertions.
  Default tests stay offline/hermetic and strip ambient credentials; Hub tests
  use injectable deterministic fakes. Live Hub/off-host network and real NFS tests
  are opt-in; actual disposable Unix/loopback TCP/TLS tests run in the default gate.
  The default gate builds and smoke-installs locked base/server/server+MCP wheels;
  additional build-marker tests remain opt-in. The quality gate is
  `scripts/check.sh`; durable-format fixtures and checkpoint-contract tests
  remain synchronized with their contracts.

Contract: [framework boundary](architecture.md#8-framework-boundary),
[development and validation](development.md).
Enforcement and evidence: [dependency/tool configuration](../pyproject.toml),
[locked dependencies](../uv.lock), [gate](../scripts/check.sh),
[test isolation](../tests/conftest.py),
[failure matrix](../tests/unit/test_failure_matrix.py), and
[checkpoint tests](../tests/unit/test_transactions.py).

## Remote management

Authenticated REST uses typed query/command services, bounded receipt-backed
execution and a separate private verifier. Public CLI and Cockpit clients retain
server authority and finite observation. Optional MCP exposes exactly fourteen read
tools with no execution capability. [API](api.md), [server](server.md), [MCP](mcp.md)
and [deployment status](deployment-status.md) define current behavior and the
limits of recorded installed acceptance.

- **`INV-012` — Adapters share one domain implementation.** HTTP/MCP
  adapters call typed services, never Typer/public CLI callbacks or each other's
  adapter callbacks. Operational CLI uses the independent typed HTTP client.
  Remote access
  changes no FS/TX, whole-archive authorization, or publication locator rule.
  Query enforcement: [shared services](../src/hfcache/services/queries.py),
  introduced by shared queries; command enforcement:
  [guarded services](../src/hfcache/services/commands.py), introduced by guarded command services.
  Metadata transport enforcement: [read application](../src/hfcache/api/app.py),
  metadata lifecycle. command routes [command adapters](../src/hfcache/api/commands.py) retain shared
  sync ordering, reconciliation, capacity, continuation, producer joins and exact
  verification delegation, covered by [HTTP/domain tests](../tests/unit/test_api_commands.py).
  independent REST client supplies the independent typed client/configuration and API-backed reader CLI migrates
  read CLI/candidates. CLI operation observation's operational CLI uses pure request types and typed
  HTTP only, with no direct mutation backend imports or local fallback. curated metadata tools
  uses the same validated metadata readers through explicit narrow adapters;
  no REST writer route is converted into an MCP tool.
- **`INV-013` — Authenticate and bound every management boundary.** Distinct
  REST writer/reader and MCP reader credentials; no cross-interface credential
  acceptance, ambient discovery, token disclosure, or unbounded requests.
  Off-host access verifies TLS. Enforcement uses the server registry, typed client and optional MCP boundary.
  server authentication supplies strict server configuration, explicit credential validation,
  fixed REST principals/capabilities and the optional FastAPI bearer adapter.
  metadata lifecycle now authenticates metadata routes, unknown paths/methods, docs and
  schema before routing/body validation, with strict Host/Origin/proxy/prefix,
  request/response/work limits and sanitized typed errors. Cursor pages bind
  filters/policy and row contents; changed rows fail continuation rather than
  silently skipping them. Shared read budgets and a pool lease cover active
  streams until completion/disconnect. Exact published-relative reference
  locators do not become HTTP artifact paths. command routes command POSTs authenticate
  before receiving a body, authorize static writer routes before reading it and
  mixed capability before DTO validation. Explicit JSON/media/encoding/depth and
  byte limits cover chunked inputs; unknown paths/credential overrides cannot
  become execution authority. maintenance routes extends the same boundary to explicit
  maintenance routes and gates initialization before body reception. API-backed reader CLI
  candidate presence requires writer capability before DTO validation; only bounded
  TOML content, not server paths/credentials, can be submitted. optional MCP transport adds its
separate protected verifier only after REST acceptance. independent REST client's independent client uses explicit API
  sources, verified TLS/Unix transport, no redirect/ambient proxy forwarding and
  finite response/page/read-retry/poll budgets with strict identity/version checks.
  It never falls back to archive filesystem access or starts a daemon.
  Enforcement/evidence: [boundary/resources](../src/hfcache/api/app.py),
  [pool/instance lock](../src/hfcache/api/lifecycle.py),
  [single Unix/TCP bootstrap](../src/hfcache/server.py),
  [wire/read tests](../tests/unit/test_api_reads.py),
  [adversarial HTTP tests](../tests/unit/test_api_adversarial.py), and
  [ephemeral TLS/socket tests](../tests/unit/test_server_bootstrap.py);
  [typed command/adversarial tests](../tests/unit/test_api_command_adversarial.py);
  decisions [113](adr/decision-113.md)/[116](adr/decision-116.md).
  This is no production deployment proof.
  REST acceptance corroborates trusted native Unix scope using both peer/local address
  evidence; prefix and proxy-TLS exceptions share that predicate, without header
  authority or global prefix/cache mutation. Enforcement/evidence:
  [HTTP boundary](../src/hfcache/api/app.py),
  [real transports/OpenAPI/negative scopes](../tests/unit/test_rest_transport_gate.py),
  [route-complete auth/roles](../tests/unit/test_rest_security_gate.py),
  [paged completeness](../tests/unit/test_rest_pagination_gate.py) and
  [examples/docs/disabled imports](../tests/unit/test_rest_examples_gate.py),
  decision [123](adr/decision-123.md).
- **`INV-014` — Admission receipts do not resume domain execution.** Persist
  before runnable/202, bind principal/key/request, fail stale policies closed,
  retain ambiguous history, and never infer success or replay from missing
  history. One bounded lane retains the cross-process archive flock.
  The receipt itself is the durable key binding; only derived indexes rebuild.
  Key digests never expose raw keys, and fixed credential-class namespaces
  survive rotation. All REST readers may observe operation metadata/results;
  key lookup searches only the caller's namespace. Unexpired terminal bindings
  retain the configured 30-day default window; count/byte limits refuse admission
  rather than evicting them. Interrupted/ambiguous/nonterminal/unsupported state
  never ages out. operation control state implements core/HTTP observation.
  bounded runner and private verifier adds the bounded FIFO lane, one absolute queue/lock deadline and a
  fresh fingerprint guard inside the service-owned archive lock. A runner never
  pre-locks or nests that service. Exact surviving verifier evidence is reconciled
  before interruption; unavailable/unsafe status preserves active receipts and
  closes execution across restarts. Metadata stays diagnosable. command routes submits
  its four keyed job routes with normalized typed bodies and 202 observation links;
  matching retries preserve the original binding. maintenance routes extends keyed admission
  to separate maintenance preview/apply, repair and guarded initialization URLs;
  previews grant no future apply authority. API-backed reader CLI's absent candidate field preserves
  historical installed-plan canonical key mappings; exact candidate text binds a
  new request and the receipt retains installed admitted fingerprint. independent REST client generates/exposes a retained
  key before POST and reports uncertainty without automatic replay; lookup and
  finite observation never cancel accepted work. CLI operation observation prints validated key
  before POST and operation ID after acceptance even quiet. One deadline covers
  event/status/result reads and retries; timeout/Ctrl-C retains handles and says
  accepted work may continue. Show/wait/lookup observe without submitting,
  cancellation or new-key replay. Detached admission never claims domain completion.
  Decisions [109](adr/decision-109.md),
  [114](adr/decision-114.md) and [115](adr/decision-115.md); [schema and compatibility](schemas.md#13-service-private-operation-control-state).
  Enforcement/evidence: [core store](../src/hfcache/api/operations.py),
  [HTTP observation](../src/hfcache/api/app.py),
  [core tests](../tests/unit/test_operations.py),
  [adversarial store tests](../tests/unit/test_operation_store_adversarial.py), and
  [HTTP history tests](../tests/unit/test_api_operations.py).
  Execution enforcement: [runner](../src/hfcache/api/runner.py),
  [context-scoped lock control](../src/hfcache/locking.py), and
  [runner/deadline/reconciliation tests](../tests/unit/test_runner.py).
  Trusted private running/domain-run progress updates the parent receipt; a stale
  private label without a live owned thread cannot establish executor liveness.
  independent REST client client enforcement: [strict settings/sources](../src/hfcache/client_config.py),
  [typed wire models](../src/hfcache/client_models.py) and
  [synchronous transport/observation](../src/hfcache/client.py);
  owned Unix streams make empty writes a no-op, preserving already-sent responses
  while retaining descriptor cleanup for actual nonempty I/O failures (decision119).
  [decision 118](adr/decision-118.md), [client contract](api-client.md).
  Evidence: [core client tests](../tests/unit/test_api_client.py),
  [config/source tests](../tests/unit/test_client_config.py),
  [real socket/TLS tests](../tests/unit/test_api_client_sockets.py),
  [adversarial wire/retry tests](../tests/unit/test_api_client_adversarial.py) and
  [actual locked base/server import smoke](../scripts/check-installations.py).
  Reader metadata does not change FS-12/INV-008's exact publication copy/verification
  authority; bulk transfer remains the independent consumer workflow.
  API-backed reader CLI enforcement/evidence: [reader CLI](../src/hfcache/cli.py),
  [finite aggregation/transport rendering](../src/hfcache/cli_client.py),
  [pure validation/authority](../src/hfcache/services/candidates.py),
  [candidate HTTP](../src/hfcache/api/commands.py),
  [authenticated CLI fixture](../tests/api_cli.py),
  [read CLI tests](../tests/unit/test_readonly_commands.py),
  [candidate tests](../tests/unit/test_api_candidates.py) and
  [reader/candidate adversarial tests](../tests/unit/test_api_candidates_adversarial.py);
  [decision 119](adr/decision-119.md). Server installation/host acceptance remains
  separate from these hermetic tests.
  CLI operation observation enforcement/evidence: [pure request types](../src/hfcache/services/requests.py),
  [bootstrap descriptions](../src/hfcache/services/bootstrap.py),
  [operational CLI](../src/hfcache/cli.py),
  [submission/observation helpers](../src/hfcache/cli_client.py),
  [typed deadline/event client](../src/hfcache/client.py),
  [write CLI integration](../tests/unit/test_cli_api_writes.py),
  [helper tests](../tests/unit/test_cli_operation_helpers.py) and
  [writer observation/adversarial tests](../tests/unit/test_cli_operations_adversarial.py);
  [decision 120](adr/decision-120.md). No client/service-stop proof replaces exact
  executor ownership or installed OS isolation acceptance.
  scheduled observation uses one application for named Unix/optional TCP activation and retains
  shared runtime lock inodes. Scheduled strict private schema-1 handles bind fixed
  sync/verify-full, endpoint/expected UUID/class and key/op, never bearer/digest/
  body/queue. Fsync key before sole POST; existing history permits lookup/observe
  only, repeated finite windows preserve oneshot lifetime, and exact terminal
  evidence alone permits removal. Unknown/malformed/future/mismatched state is
  preserved at exit 20. [Decision 121](adr/decision-121.md) and
  [schema§14](schemas.md#14-scheduled-client-observation-handle).
  Enforcement/evidence: [activation](../src/hfcache/server.py),
  [scheduled observer](../src/hfcache/scheduled_client.py),
  [release guard](../scripts/release-functions.sh),
  [activation fixtures](../tests/unit/test_server_activation.py),
  [observer recovery tests](../tests/unit/test_scheduled_client.py) and
  [release switch/drain fixtures](../tests/unit/test_release_installer.py).
- **`INV-015` — Verification isolation encloses persistence.** Non-estimate
  verification locks target resolution, hashing, report write and catalog merge
  in a credential-free no-IP executor. Estimates remain metadata reads.
  Lock/persistence enforcement: [command services](../src/hfcache/services/commands.py)
  and [multiprocess tests](../tests/unit/test_command_locking.py), guarded command services.
  The API runner/private verifier implement the strict peer-checked private protocol, dedicated startup
  and exact durable outcome/reconciliation primitives; Native units supply credential-free/no-IP policy while installed enforcement remains host acceptance. No unsafe
  ASGI-process fallback. Shared services never toggle the offline environment. Dedicated startup uses [startup-only offline initialization](../src/hfcache/offline.py)
  for the dedicated process, verified in [child-process tests](../tests/unit/test_offline_process.py).
  That helper alone does not deny IP sockets; decision [111](adr/decision-111.md).
  Protocol/process enforcement: [private client/framing/peer validation](../src/hfcache/verification_protocol.py),
  [worker runtime](../src/hfcache/verification_executor.py),
  [inherited-socket startup](../src/hfcache/verification_worker.py), and
  [executor/protocol tests](../tests/unit/test_verification_executor.py);
  decision [115](adr/decision-115.md). The command service's writer-only verification route
  has no HTTP-process execution path; [route tests](../tests/unit/test_api_commands.py)
  prove all three modes delegate and refuse unavailable private execution.
  These tests do not prove installed OS egress.
  Native packaging/evidence: [worker service](../packaging/systemd/hfcache-verification.service),
  [private socket](../packaging/systemd/hfcache-verification.socket),
  [activation/bootstrap tests](../tests/unit/test_verification_worker_bootstrap.py)
  and [unit contracts](../tests/unit/test_systemd_units.py); decision
  [121](adr/decision-121.md). See [deployment status](deployment-status.md) for
  recorded installed peer/confinement scope and outstanding NAS/other-host work.
  [Decision 128](adr/decision-128.md) adds a distinct PID1-only container-listener
  mode without a native bind fallback. Early inherited-FD/activation/credential
  audit precedes owned resources and shared imports; parent/instance ownership
  encloses listener creation, joined work and exact-inode cleanup. READY follows
  listener/store/worker initialization, never a sleep or conmon start. Only the
  worker's private directory becomes writable; API stays read-only. Offline/no-IP,
  no credentials, exact private protocol/results and no replay remain. Rootless
  API Requires+After worker.service; dormant .socket/native activation remain
  separate. Source fixtures and host probes do not prove actual container peer access.
  [Recorded 0.2.1 scope](deployment-status.md) includes the installed peer path
  under Enforcing before/after drain/restart. Live NAS verification/workload acceptance remains unrun; rollback to
  0.2.0 restores its recorded connection limitation.
- **`INV-016` — MCP has no mutation or job path.** Only explicitly registered
  metadata reads through a narrow read-service interface; no Hub, probes,
  persistence, recovery, or operation admission. The optional transport registers exactly fourteen approved metadata tools, no resources/prompts or REST OpenAPI conversion; only the distinct
  MCP-reader credential is accepted through a
  production supported verifier. Disabled mode imports/resolves neither package
  nor credential; one composed lifespan retains REST ownership and transport
  security. Stateless HTTP retains no legacy session/resumption store; session IDs
  grant no authority and every transport request authenticates. The narrow `/mcp`
  to `/mcp/` redirect is authenticated, relative and cannot reflect caller input;
  REST slash redirects remain disabled. One trusted public/native interface
  projection governs authentication, static writer/body policy and links, including
  configured-prefix collisions. Finite MCP replies are buffered/sanitized and
  bounded before headers; separate in-flight capacity adds no retained queue.
  curated metadata tools tool functions receive only a narrow async read protocol, no SDK app/
  request context, commands, Hub/credential resolver or writable helpers. Typed
  metadata results use explicit manifest/report projections. Inventory cursors
  bind complete selected rows/filter/policy while status headline/warnings remain
  fresh per page; immutable artifact cursors bind all sanitized headers/collections.
  Registered secrets never enter cursor hashing; changed bound content refuses. Exact SHA/
  publication reads never substitute current, and estimates/catalog reads never
  increase confidence or trigger persistence/rebuild. Registry/schema equality
  and success/failure archive/control-state snapshots prove the boundary;
  annotations alone do not. Mounted fixtures test registry/side effects and client behavior; installed
  acceptance remains separately scoped by the deployment status.
  Enforcement: [optional verifier/finite transport](../src/hfcache/mcp.py),
  [application boundary/lifecycle](../src/hfcache/api/app.py),
  [direct verifier/lifecycle tests](../tests/unit/test_mcp_mount.py) and
  [mounted streaming/security tests](../tests/unit/test_mcp_transport.py).
  Curated enforcement: [read-only projection backend](../src/hfcache/services/mcp_queries.py),
  [original tool functions/read port](../src/hfcache/mcp_tools.py),
  [five catalog tools/read port](../src/hfcache/mcp_catalog_tools.py) and
  [app-owned bounded facade](../src/hfcache/api/mcp_reads.py) and
  [catalog facade](../src/hfcache/api/catalog_mcp_reads.py).
  Evidence: [backend](../tests/unit/test_mcp_queries.py) and
  [mounted registry/tools](../tests/unit/test_mcp_tools.py).
  See [MCP](mcp.md), [decision 124](adr/decision-124.md) and
  [decision 125](adr/decision-125.md). The
  [mounted security checks threat/control/test map](mcp.md#read-only-boundary)
  distinguishes application snapshots and mixed-interface ownership from
  installed-host assumptions, with [malformed evidence/secret proof](../tests/unit/test_mcp_security_evidence.py),
  [closed authority/state snapshots](../tests/unit/test_mcp_security.py) and
  [mixed-interface/cancellation/drain tests](../tests/unit/test_mcp_concurrency.py).
  protected MCP client client/packaging guidance: [protected-file example](../examples/mcp-client.py),
  [setup/version/rotation/cost contract](mcp.md#connect)
  and [REST/auth/rotation/unit acceptance](../tests/unit/test_mcp_acceptance.py).
  The independent REST base client retains no MCP runtime requirement; example
  discovery grants no complete-artifact/copy or command authority.

FW-01/FW-03 above retain their historical baseline with the explicit
[108](adr/decision-108.md)/[109](adr/decision-109.md) amendment: scoped transport
dependencies and the bounded non-resuming lane are narrow explicit exceptions.
[Decision 112](adr/decision-112.md) records the actual HTTPX and `server` extra
addition and its material correctness rationale.
[Decision 124](adr/decision-124.md) adds standalone FastMCP only in the optional
`mcp` extra after committed REST acceptance, for maintained streaming protocol,
production token verification and composed ASGI lifecycle; base/REST installs
remain independent. No domain workflow framework is introduced.
[Decision 119](adr/decision-119.md) adds an explicit HTTPCore declaration at the
already-locked 1.0.9 version for resource-safe public Unix transport interfaces.
Enforcement: [Unix transport](../src/hfcache/unix_http.py) and
[descriptor/stream regressions](../tests/unit/test_unix_http.py).
No other workflow framework or runtime dependency is authorized.

## UBI 10 image-foundation qualification

[Decision 129](adr/decision-129.md) applies INV-003/005/010/015 to new service
foundations: all app/Caddy FROM stages use pinned minimal-viable UBI 10 micro.
Minimal contributes only Red Hat CA data; external uv/Caddy donors only verified
executables, not foreign OS/CA/defaults. Portable interpreter and locked app
versions stay fixed. Actual linkage, inherited/owned listener, notify/peer,
secret/seccomp/SELinux/UID/drain/lock proofs remain mandatory; a base label alone
establishes none. Superseded Debian success cannot stand in for UBI acceptance.
Enforcement: [app recipe](../packaging/containers/Containerfile),
[Caddy recipe](../packaging/containers/Containerfile.caddy),
[immutable pins](../packaging/containers/images.json),
[app builder](../scripts/build-container.py),
[Caddy builder](../scripts/build-caddy-container.py),
[public fetcher](../scripts/fetch-container-python.py) and
[foundation proof](../scripts/check-container-foundation.py).
Evidence: [app build tests](../tests/unit/test_container_runtime.py),
[Caddy build tests](../tests/unit/test_caddy_container_build.py),
[fetch tests](../tests/unit/test_fetch_container_python.py) and
[foundation tests](../tests/unit/test_container_foundation.py), with actual
image/worker/TLS fixture records and clean immutable artifact identities.

## Tags and supplemental discovery metadata

- **`INV-018` — Separate curation, observations and archive authority.** Current
  validated config supplies operator tags, including disabled/empty entries;
  only an actual writer-observed snapshot supplies historical labels. Policy
  fingerprints exclude tags; curation has a separate versioned identity.
  Supplemental schema-1 records live only in optional `published/metadata/`.
  Each replacement and approved directory creation is independently atomic under
  the sole writer lock, initialized identity, storage preflight and TX-07 guards;
  this is a narrow FS-17/TX-01 exception without multi-file atomicity or replay.
  Unsupported/malformed/unsafe existing records remain preserved and refuse.
  Derived publication observations bind exact retained manifests and cannot
  establish membership or verification confidence. Reads never write, refresh,
  contact Hub or open payloads. Technical predicates bind one complete eligible
  variant in one publication; missing coverage stays unknown. Historical tags
  require backup. Inert metadata cannot resurrect pruned or purged content.

Contract: [discovery](discovery.md), [record schemas](schemas.md#17-supplemental-discovery-records),
[decision 133](adr/decision-133.md). Record enforcement: [strict models](../src/hfcache/catalog_models.py),
[bounded no-follow storage](../src/hfcache/catalog_storage.py),
[active caller lock](../src/hfcache/locking.py) and
[crash/identity/preservation fixtures](../tests/unit/test_catalog_storage.py).
Extraction enforcement: [bounded static access](../src/hfcache/catalog_extractors.py),
[inert parsers](../src/hfcache/catalog_parsing.py) and
[hostile declaration fixtures](../tests/unit/test_catalog_extractors.py).
Variant enforcement: [GGUF bounded headers/grouping](../src/hfcache/catalog_gguf.py)
and [synthetic mapping/shard/budget fixtures](../tests/unit/test_catalog_gguf.py).
Scoped declarations: [weight indexes/headers](../src/hfcache/catalog_weights.py)
and [scope/pointer/ambiguity fixtures](../tests/unit/test_catalog_weights.py).
Lifecycle enforcement: [joined writer capture](../src/hfcache/catalog_capture.py),
[sync/repair service](../src/hfcache/services/commands.py) and
[retained/repair/failure fixtures](../tests/unit/test_catalog_lifecycle.py).
Refresh enforcement: [typed offline service](../src/hfcache/catalog_refresh.py),
[bounded ref inventory](../src/hfcache/catalog_inventory.py),
[scope/failure fixtures](../tests/unit/test_catalog_refresh.py) and
[keyed replay fixture](../tests/unit/test_catalog_refresh_replay.py).
Remaining proposed query/transport interfaces require their own
validation before support is declared. Offline evidence is not production acceptance.

Query enforcement: [shared catalog reader](../src/hfcache/services/catalog_queries.py),
[strict query/payload models](../src/hfcache/catalog_query_models.py) and
[scope/variant/privacy fixtures](../tests/unit/test_catalog_queries.py).
Sanitize before predicates, counts and cursor identity; opaque source curation
fingerprints are withheld from read projections. Whole selected coverage and
finite aggregate bounds apply before paging.
REST enforcement: [catalog adapters](../src/hfcache/api/catalog.py), the existing
[metadata pool/render boundary](../src/hfcache/api/app.py) and
[HTTP grammar/auth/cursor fixtures](../tests/unit/test_api_catalog.py) preserve
strict existing wrappers and whole-archive read capability.
Refresh admission: [strict intent DTO](../src/hfcache/api/command_models.py),
[keyed writer adapter](../src/hfcache/api/catalog_refresh.py) and
[HTTP replay/wait/disconnect/restart fixtures](../tests/unit/test_api_catalog_refresh.py)
reuse the same lane/guard/result ownership without widening verifier authority.
Client enforcement: [typed HTTP methods](../src/hfcache/client.py),
[pure catalog validation/collection](../src/hfcache/client_catalog.py),
[pure refresh DTOs](../src/hfcache/catalog_refresh_models.py) and
[inert human rendering](../src/hfcache/catalog_display.py), with
[client consistency/import fixtures](../tests/unit/test_catalog_client.py) and
[actual HTTP CLI evidence](../tests/unit/test_cli_catalog.py), preserve the base
reader boundary and exact server Envelope identity through complete collection.

Catalog normalization under INV-018 must not bypass INV-002: suppress casefolded
registered-secret representations before matching, facets and cursor identity.
Enforcement: [catalog checks](../src/hfcache/services/catalog_queries.py),
[explicit folded literal check](../src/hfcache/redaction.py) and
[adversarial evidence](../tests/unit/test_catalog_adversarial.py).

INV-018 lifecycle/compatibility enforcement also includes
[real repair/prune/purge discovery](../tests/unit/test_catalog_final_lifecycle.py)
and [actual isolated installed targets](../tests/system/test_catalog_compatibility.py).
Old goldens remain identical; unknown adjuncts never restore membership or
confidence. Target-specific config/layout/client refusals require preservation
and guarded validation, not deletion or a universal compatibility assumption.
