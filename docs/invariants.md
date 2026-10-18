# hfcache invariants

This is the living register of conditions that every implementation and new
plan must preserve. It collects the current contracts; the linked documents
retain their detailed validation rules, checkpoint tables, and operational
procedures. The [ADR index](adr/README.md) records why these boundaries exist.
Historical decisions do not override a later, explicitly superseding decision.

An invariant describes a guarantee or constraint, not a snapshot of a deployment
or an implementation preference. Filesystem guarantees apply at the observable
boundaries defined in [architecture §6–§7](architecture.md#6-filesystem-invariants),
including recoverable crash states; they do not claim that several independent
filesystem operations form one atomic operation.

## Using and maintaining this register

Before implementing a change or a new plan, review the affected sections below
and follow their links to the governing contracts. In the same work package:

1. Add every newly introduced invariant here, and update any invariant whose
   guarantee, scope, or exception changes. Update its governing contract and
   the relevant [ADRs](adr/README.md) alongside the implementation or plan.
2. Cite the existing requirement ID when one exists (`AD`, `FS`, `TX`, `FW`,
   `CP`, or another contract's established namespace). Use a new sequential
   `INV-nnn` ID only for a constraint without an existing requirement ID.
3. Preserve IDs. When a guarantee is retired or superseded, retain its ID and
   state its replacement and the decision authorizing the change; never reuse
   the ID for a different guarantee. Keep historical alternatives in the ADRs,
   rather than presenting them as current invariants.
4. Keep source and verification links useful. New enforcement belongs in the
   appropriate code and meaningful tests; a documentation entry alone does not
   establish the guarantee. Run the work package's required gate and record the
   evidence in [progress](progress.md), following the
   [workflow](agents/workflow.md).

Every implemented change and new plan requires this review. A change that
introduces or changes no invariant need not edit this file or invent an ADR.
A change that creates a disagreement between this register, a governing
contract, and the code must resolve it explicitly in the same work package,
with the reasoning recorded. A pre-existing conformance gap discovered outside
that change's scope must be labelled here and tracked in progress; do not
present its requirement as an enforced guarantee or silently weaken it.

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
- **`FS-21`–`FS-23`** — Only explicit `archive init` creates the sentinel and
  initial layout, never sync, recovery, or a timer. It refuses existing archive
  identity, unknown content, and symlinks; only the documented empty,
  correctly owned and moded `published/` and application-owned interrupted-init
  states may be adopted or retried. The sentinel is written last and never
  rewritten. This deployment already exists: agents must never run init.
- **`AD-17`** — Exactly one host has archive write authority, enforced by the
  server's exact-host export. Mutation and verification share a local exclusive
  lock under `/run/hfcache`; there is no NFS lock or second writer host.

Contract: [architecture §5–§7](architecture.md#5-filesystem-layout),
[CLI initialization and doctor](cli.md#archive-init), and
[agent environment](agents/environment.md).
Enforcement: [storage](../src/hfcache/storage.py),
[preflight](../src/hfcache/preflight.py),
[initialization](../src/hfcache/archive.py), and
[locking](../src/hfcache/locking.py).
Evidence: [preflight tests](../tests/unit/test_preflight.py),
[initialization tests](../tests/unit/test_archive_init.py),
[locking tests](../tests/unit/test_locking.py), and opt-in
[real-mount tests](../tests/system/test_live_mount.py).

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
[read-boundary regressions](../tests/unit/test_query_boundary.py), API-006.
History: `HUB-007` (`45f1ccf`) established physical-object hashing;
`SYNC-006` (`92ebdba`) added same-operation hardlink identity proof.

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

**Known conformance gap (`RET-011`).** The lifetime-generation and audit-union
requirements above remain the declared `AD-05`/`FS-20` contract, but current
implementation evidence does not establish them.
[`next_generation`](../src/hfcache/publication.py) scans retained references
only. The regression test
`test_a_pruned_sha_that_returns_is_republished_into_a_fresh_container` in
[the sync suite](../tests/unit/test_synchronize.py) explicitly expects a pruned
SHA to return with a fresh generation of 7. Retained-SHA reobservation and repair
preserve their generation; the pruned/reintroduced case needs an explicit future
contract or code decision. The [progress tracker](progress.md) records this gap;
this register must not silently treat the stronger contract as already enforced.

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
History: `PUR-001` (`7370af2`) adds explicit purge;
`RET-010` (`ec3e630`) replaces the original fixed-five default. The schema-1
audit reason `sixth_unique_revision_published` remains its historical name for
exceeding the configured limit; it does not require retaining five.

## Transactions and recovery

- **`AD-14`, `FS-17`, `TX-01`, `TX-02`** — Normal archive mutation opens a
  durable transaction journal before its first mutation. Append a checkpoint
  only after the named operation is durable. Journals describe filesystem
  facts, never instructions to replay. The resolved-quarantine exception below
  reuses existing terminal journals and creates no new one.
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
  `needs_operator` journal remains unresolved. Quarantine cleanup instead
  refuses unfinished work and does not recover unrelated transactions.
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
History: `QUA-001` (`1ad4181`), `QUA-002` (`7b5e4e2`), and
`QUA-003` (`c2b52ff`) define the narrow cleanup and cancellation exceptions.

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
History: `SYNC-007` (`54e4671`), decision 94.

## Configuration and security

- **`INV-001` — Configuration is explicit, strict, and immutable.** Require
  schema version 1, reject unknown keys and coercions, normalize absolute
  filesystem paths, and reject invalid or duplicate repository identities
  before locks, network, or mutation. `config validate` uses the same
  validation and changes nothing. Keep archive policy, restart-only server
  transport/auth and later client settings in separate schemas. A server freezes
  freshly validated archive snapshots per request/admission and pins root/UUID
  to startup authority; it never hot-switches archives (decision 112). Pure
  candidate syntax assessment is separate from authority compatibility; no request
  can redirect installed credentials through candidate endpoint/source changes
  (decision 116). See
  [configuration §1–§2, §6](configuration.md#1-validation-rules-that-apply-to-every-field).
- **`INV-002` — Credentials have only explicit sources and never become
  evidence.** Accept only an explicit token file or systemd credential, with
  the documented precedence and file validation. Disable ambient discovery;
  every Hub call passes an explicit token or `False`, never `None`. Missing
  optional credentials permit anonymous access; installed unusable credentials
  fail. That anonymous fallback applies to Hub policy; API writer authentication
  is required and an unprovisioned optional API reader grants no capability.
  API and Hub credentials are distinct explicit sources, never ambient reuse.
  The server's explicit Hub file is a trusted startup option, never request input;
  candidate assessment resolves no proposed credential.
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
  See [security §2–§5](security.md#2-trust-boundaries),
  [deployment](deployment-centos-stream-10.md), and
  [agent environment](agents/environment.md).
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
History: `HUB-010` (`c082f87`), decision 98, supersedes public-only scope.
API-005 enforcement: [server configuration and policy snapshots](../src/hfcache/server_config.py),
[protected API credentials and fixed capabilities](../src/hfcache/api/auth.py),
[optional FastAPI adapter](../src/hfcache/api/security.py),
[configuration/reload tests](../tests/unit/test_server_config.py), and
[adversarial credential/capability tests](../tests/unit/test_server_auth_adversarial.py).
API-009 command/authority enforcement: [typed DTOs](../src/hfcache/api/command_models.py),
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
  API-007's independent local receipt/event/reference version rejects missing,
  noninteger, duplicate-key and unsupported state; it does not widen archive
  formats. Receipt/result updates use the same durable serializer and fsync
  boundary. See [schemas §13](schemas.md#13-service-private-operation-control-state-api-007).
- **`INV-006` — CLI output and failure classification are stable contracts.**
  `--json` emits exactly one schema-1 envelope on stdout, including failures;
  stderr is display/event output. Error classes, stable taxonomy codes, and
  exit priority must agree. Warnings alone keep exit `0`; any failed repository
  makes the aggregate run fail. `success` carries no warnings,
  `success_with_warnings` requires them, and `failed` may retain earlier
  warnings alongside its errors. See [CLI §3–§6](cli.md#3-exit-codes) and
  [run reports](schemas.md#6-run-report).
  Execution correlation is context-scoped, captured when emitted and explicitly
  copied into workers; server request/operation IDs cannot replace domain
  run/journal identities. Daemon logger configuration is startup-only.
  Durable `invocation_mode` describes the execution host, not timer or submitter
  origin; API-007 receipts record the authenticated credential-class submitter
  separately (decisions 111/114), without claiming individual user attribution.
  The API-006 foreground `serve` bootstrap is a narrow exception: normal daemon
  execution has no terminal success Envelope/stdout, while classified startup
  failures preserve the schema-1 error Envelope under `--json` (decision 113).
  API-009's 202 is admission only; exact result retrieval preserves the shared
  terminal Envelope, including partial failure and domain exit priority.
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
Evidence: [golden formats](../tests/fixtures/schemas/),
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
[release compatibility drill](agents/release.md); schema version 1 is not a
blanket claim that old binaries accept every later widening.
API-007 control-state enforcement: [receipt models/store](../src/hfcache/api/operations.py),
[golden operation fixtures](../tests/fixtures/schemas/operation-receipt.json),
[lifecycle/idempotency/result tests](../tests/unit/test_operations.py), and
[fault/concurrent admission/retention tests](../tests/unit/test_operation_store_adversarial.py).
Its task records the separate previous-binary compatibility drill.

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

- **`CP-01`, `CP-02`, `CP-09`** — The plugin uses installed CLI JSON envelopes
  and systemd, never reimplements archive logic or writes archive files. The
  sole direct archive-read exception is run-report browsing as the service
  identity. Refuse unknown envelope versions; stderr is display-only.
- **`CP-03`, `CP-04`, `CP-10`** — Mutation needs administrative Cockpit access,
  while CLI work runs as the service identity in a transient unit, never root.
  Full sync/verification use their installed services. Respect the single
  writer lock; report busy without bypassing it.
- **`CP-05`–`CP-08`** — Schedule controls affect only the sync timer; never
  manipulate `hfcache.target`, enable the verify timer, or expose archive init.
  The page never reads credentials or accepts tokens; systemd imports its
  credential directly into spawned CLI work.
- **`CP-11`, `CP-12`** — Config installs follow candidate → successful CLI
  validation → atomic install, retaining the predecessor and `0640`
  `root:hfcache` ownership/mode. Timer changes use validated calendar drop-ins,
  never edit shipped units.
- **`CP-13`, `CP-14`** — Never weaken host hardening. The plugin ships static
  files; Node tooling is build-time only, adds no Python runtime dependency,
  and generated bundles/node_modules are never committed.

Contract: [Cockpit rules and pipelines](cockpit.md#1-rules).
Enforcement: [CLI/unit API](../cockpit/src/api/hfcache.ts),
[config API](../cockpit/src/api/config.ts),
[schedule API](../cockpit/src/api/schedule.ts), and
[command boundary](../cockpit/src/lib/command.ts).
Evidence: [plugin tests](../cockpit/test/) and the
[operator install/acceptance runbooks](cockpit-plugin/README.md).

## Framework and engineering

- **`FW-01`, `FW-02`** — Use ordinary deterministic Python functions and typed
  append-only records. Journals are recovery evidence, never an orchestration
  engine. No workflow/DAG/actor/task/agent framework or mutable archive database.
- **`FW-03`, `FW-04`** — Runtime dependencies are `huggingface-hub`, `pydantic`,
  `typer`, the resolved Hub client's required transfer backend, and the direct
  base HTTPX client; FastAPI/Uvicorn are optional `server` dependencies
  (decision 112, implementing the decision 108 exception). Use the
  standard library for TOML, JSON, hashing, filesystem work, locking, and
  logging. An addition needs a recorded material correctness argument, not
  convenience or fewer lines.
- **`INV-010` — Safety checks and evidence survive routine execution.** Source
  safety checks raise exceptions and never depend on removable assertions.
  Default tests stay offline/hermetic and strip ambient credentials; Hub tests
  use injectable deterministic fakes. Network and real NFS tests are opt-in.
  The default gate builds and smoke-installs locked base/server wheels;
  additional build-marker tests remain opt-in. Every work-package commit updates progress and passes
  `scripts/check.sh`; durable-format fixtures and checkpoint-contract tests
  remain synchronized with their contracts.
- **`INV-011` — Active work has one plan and explicit task authority.**
  `docs/plans/current.md` selects at most one active dated plan. Each
  implementation work package has an individual task file before execution;
  the task owns status, dependencies, acceptance criteria, and evidence. The
  dated plan owns scope and task order; current is a short selector and next-
  task pointer. User authorization to implement permits activation, while a
  draft or an old backlog item alone does not. Preserve plan/task identities
  and completed or superseded records. Keep active records and completed
  progress evidence consistent in the implementation commit. The historical
  progress log retains completed work packages, Decisions, Operator handoff,
  and unmigrated backlog, without duplicating the active queue.

Contract: [framework boundary](architecture.md#8-framework-boundary),
[conventions](agents/conventions.md), [workflow](agents/workflow.md), and
[planning lifecycle](agents/planning.md).
Enforcement and evidence: [dependency/tool configuration](../pyproject.toml),
[locked dependencies](../uv.lock), [gate](../scripts/check.sh),
[test isolation](../tests/conftest.py),
[failure matrix](../tests/unit/test_failure_matrix.py), and
[checkpoint tests](../tests/unit/test_transactions.py).
Planning evidence: [current selector](plans/current.md),
[retained setup plan](plans/2026-10-17-plan-planning-workflow.md), and
[DOC-010 task](plans/tasks/doc-010-planning-workflow.md).
`INV-011` is a repository workflow requirement reviewed through these records
and git; the application test suite does not enforce planning lifecycle.

## Remote management (incremental enforcement)

API-001 introduces these constraints for the activated plan. API-006 implements
authenticated metadata HTTP and its foreground bootstrap; API-007 adds durable
admission primitives and operation observation. API-008 adds execution/private
verification and API-009 adds the typed command subset. Maintenance, candidate
operations, client migration, installed isolation hardening and MCP remain pending.
[API](api.md) and [server](server.md) track exact availability; implementing tasks
own proof.

- **`INV-012` — Adapters share one domain implementation.** Transports call
  typed services, never one another or public CLI callbacks. Remote access
  changes no FS/TX, whole-archive authorization, or publication locator rule.
  Query enforcement: [shared services](../src/hfcache/services/queries.py),
  introduced by API-002; command enforcement:
  [guarded services](../src/hfcache/services/commands.py), introduced by API-003.
  Metadata transport enforcement: [read application](../src/hfcache/api/app.py),
  API-006. API-009 [command adapters](../src/hfcache/api/commands.py) retain shared
  sync ordering, reconciliation, capacity, continuation, producer joins and exact
  verification delegation, covered by [HTTP/domain tests](../tests/unit/test_api_commands.py).
  Public CLI client migration remains API-011–013 and MCP-002 later.
- **`INV-013` — Authenticate and bound every management boundary.** Distinct
  REST writer/reader and MCP reader credentials; no cross-interface credential
  acceptance, ambient discovery, token disclosure, or unbounded requests.
  Off-host access verifies TLS. Enforcement: API-005/006/011 and MCP-001/003.
  API-005 supplies strict server configuration, explicit credential validation,
  fixed REST principals/capabilities and the optional FastAPI bearer adapter.
  API-006 now authenticates metadata routes, unknown paths/methods, docs and
  schema before routing/body validation, with strict Host/Origin/proxy/prefix,
  request/response/work limits and sanitized typed errors. Cursor pages bind
  filters/policy and row contents; changed rows fail continuation rather than
  silently skipping them. Shared read budgets and a pool lease cover active
  streams until completion/disconnect. Exact published-relative reference
  locators do not become HTTP artifact paths. API-009 command POSTs authenticate
  before receiving a body, authorize static writer routes before reading it and
  mixed capability before DTO validation. Explicit JSON/media/encoding/depth and
  byte limits cover chunked inputs; unknown paths/credential overrides cannot
  become execution authority. Maintenance/candidate/MCP paths remain pending.
  Enforcement/evidence: [boundary/resources](../src/hfcache/api/app.py),
  [pool/instance lock](../src/hfcache/api/lifecycle.py),
  [single Unix/TCP bootstrap](../src/hfcache/server.py),
  [wire/read tests](../tests/unit/test_api_reads.py),
  [adversarial HTTP tests](../tests/unit/test_api_adversarial.py), and
  [ephemeral TLS/socket tests](../tests/unit/test_server_bootstrap.py);
  [typed command/adversarial tests](../tests/unit/test_api_command_adversarial.py);
  decisions [113](adr/decision-113.md)/[116](adr/decision-116.md).
  This is no production deployment proof.
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
  never ages out. API-007 implements core/HTTP observation.
  API-008 adds the bounded FIFO lane, one absolute queue/lock deadline and a
  fresh fingerprint guard inside the service-owned archive lock. A runner never
  pre-locks or nests that service. Exact surviving verifier evidence is reconciled
  before interruption; unavailable/unsafe status preserves active receipts and
  closes execution across restarts. Metadata stays diagnosable. API-009 submits
  four keyed job routes with normalized typed bodies and 202 observation links;
  matching retries preserve the original binding. Maintenance submissions and
  public client safety remain API-010/013. Decisions [109](adr/decision-109.md),
  [114](adr/decision-114.md) and [115](adr/decision-115.md); [schema and compatibility](schemas.md#13-service-private-operation-control-state-api-007).
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
- **`INV-015` — Verification isolation encloses persistence.** Non-estimate
  verification locks target resolution, hashing, report write and catalog merge
  in a credential-free no-IP executor. Estimates remain metadata reads.
  Lock/persistence enforcement: [command services](../src/hfcache/services/commands.py)
  and [multiprocess tests](../tests/unit/test_command_locking.py), API-003.
  API-008 implements the strict peer-checked private protocol, dedicated startup
  and exact durable outcome/reconciliation primitives; API-014 retains installed
  credential-free/no-IP unit enforcement and host acceptance. No unsafe
  ASGI-process fallback. API-004 removes the shared-service offline environment
  toggle and provides [startup-only offline initialization](../src/hfcache/offline.py)
  for the dedicated process, verified in [child-process tests](../tests/unit/test_offline_process.py).
  That helper alone does not deny IP sockets; decision [111](adr/decision-111.md).
  Protocol/process enforcement: [private client/framing/peer validation](../src/hfcache/verification_protocol.py),
  [worker runtime](../src/hfcache/verification_executor.py),
  [inherited-socket startup](../src/hfcache/verification_worker.py), and
  [executor/protocol tests](../tests/unit/test_verification_executor.py);
  decision [115](adr/decision-115.md). API-009's writer-only verification route
  has no HTTP-process execution path; [route tests](../tests/unit/test_api_commands.py)
  prove all three modes delegate and refuse unavailable private execution.
  These tests do not prove installed OS egress.
- **`INV-016` — MCP has no mutation or job path.** Only explicitly registered
  metadata reads through a narrow read-service interface; no Hub, probes,
  persistence, recovery, or operation admission. Enforcement: MCP-001–004,
  which cannot begin until API-016 completes.

FW-01/FW-03 above retain their historical baseline with the explicit
[108](adr/decision-108.md)/[109](adr/decision-109.md) amendment: scoped transport
dependencies and the bounded non-resuming lane are permitted incrementally.
[Decision 112](adr/decision-112.md) records the actual HTTPX and `server` extra
addition and its material correctness rationale; FastMCP remains pending.
No other workflow framework or runtime dependency is authorized.
