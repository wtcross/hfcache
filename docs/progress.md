# Implementation Progress

Authoritative work-package tracker for `docs/plan.md` §28, maintained under the
§36 Autonomous Implementation Protocol. Update this file **in the same commit**
as the work it records: mark the box, append `(YYYY-MM-DD, <short commit ref or
"this commit">)`.

Statuses: `[ ]` pending · `[x]` complete · `[b]` blocked (explain under
Operator handoff or Operator decisions needed).

Session startup: read `docs/plan.md` in full, then this file, then
`git log --oneline -20`; re-run the §8.4 quality gates if source exists;
continue at the first unchecked item in phase order.

## Phase 0 — Contract and Architecture

- [x] ARC-001 Record architecture decisions and non-goals (2026-07-24, this commit — `docs/architecture.md` §1–4: `AD-01`–`AD-18`, `NG-01`–`NG-12`)
- [x] ARC-002 Define filesystem layout and invariants (2026-07-24, this commit — `docs/architecture.md` §5–6: layout, ownership/modes, path grammar, `FS-01`–`FS-23`)
- [x] ARC-003 Define configuration schema version 1 (2026-07-24, this commit — `docs/configuration.md`: every key typed and constrained, credential resolution, `HFCFG001`–`HFCFG016`, config fingerprint)
- [x] ARC-004 Define manifest, catalog, run-report, and verification schemas (2026-07-24, this commit — `docs/schemas.md`: sentinel, manifest, refs, catalog, run report, verification report, prune plan, audit records, transaction journal)
- [x] ARC-005 Define CLI commands, JSON output, and exit codes (2026-07-24, this commit — `docs/cli.md`: every command and option, selector grammar, JSON envelope, exit-code aggregation, `HFARG`/`HFMNT`/`HFTXN`/`HFHUB`/`HFSYN`/`HFVER`/`HFRET`/`HFWRN` taxonomy)
- [x] ARC-006 Define transaction and crash-recovery boundaries (2026-07-24, this commit — `docs/architecture.md` §7: `TX-01`–`TX-07`, named checkpoints and crash matrices for publication/prune/repair/sync/recovery, prune commit point, `needs_operator` conditions)
- [x] ARC-007 Define security and threat assumptions (2026-07-24, this commit — `docs/security.md`: assets, trust boundaries, threats `T-01`–`T-12` with controls, hardening posture, explicit out-of-scope list, verification tests)
- [x] ARC-008 Enforce the framework boundary (no workflow engine in v1) (2026-07-24, this commit — `docs/architecture.md` §8 `FW-01`–`FW-04`, plus §9 Phase 0 acceptance)

**Phase 0 complete.** Contracts: `docs/architecture.md`, `docs/configuration.md`,
`docs/schemas.md`, `docs/cli.md`, `docs/security.md`. Acceptance evidence in
`docs/architecture.md` §9.

## Phase 1 — Project Bootstrap and Quality Gates

- [ ] BOOT-001 Initialize uv project and `src/` layout (includes `git init` + initial docs commit per §36.2)
- [ ] BOOT-002 Pin Python and create `uv.lock`
- [ ] BOOT-003 Configure Ruff formatting and linting
- [ ] BOOT-004 Configure Pyrefly
- [ ] BOOT-005 Configure pytest and coverage
- [ ] BOOT-006 Add Typer entry point and version command
- [ ] BOOT-007 Add provider-neutral quality scripts and build smoke test

## Phase 2 — Configuration, Models, and Read-only CLI

- [ ] CFG-001 Strict Pydantic configuration models
- [ ] CFG-002 Token-source abstraction without literal secrets
- [ ] CFG-003 Repository identity and safe path mapping
- [ ] CFG-004 Manifest and report models
- [ ] CFG-005 `config validate`
- [ ] CFG-006 Read-only portions of `doctor`, `status`, and `plan`
- [ ] CFG-007 Deterministic JSON output and error taxonomy

## Phase 3 — Storage Safety and Publication Primitives

- [ ] STO-000 Guarded one-time archive initialization and inspection (note the §6.2 empty-`published/` adoption exception)
- [ ] STO-001 NFS mount and filesystem-type detection
- [ ] STO-002 Sentinel/archive-ID validation
- [ ] STO-003 Free-space and reserve calculations
- [ ] STO-004 Local exclusive locking
- [ ] STO-005 Atomic JSON and ref writes
- [ ] STO-006 Staging creation and containment
- [ ] STO-007 Hardlink and copy publication primitives
- [ ] STO-008 Storage reconciliation and stale-staging reporting
- [ ] STO-009 Complete mutating `doctor` tests
- [ ] STO-010 Durable transaction journals and validated checkpoint evidence
- [ ] STO-011 Dry-run and apply recovery planning

## Phase 4 — Hub Resolution and Repository Ingestion

- [ ] HUB-001 Typed Hub client adapter
- [ ] HUB-002 Optional identity verification
- [ ] HUB-003 Resolve branch/tag to full SHA
- [ ] HUB-004 Repository tree and dry-run size
- [ ] HUB-005 Complete `snapshot_download`
- [ ] HUB-006 Local-only completeness verification
- [ ] HUB-007 Hash new unique content
- [ ] HUB-008 Durable manifest generation
- [ ] HUB-009 Publish revision instance; atomic per-SHA and current refs

## Phase 5 — Multi-repository Sync and Retention

- [ ] SYNC-001 Deterministic multi-repository orchestration
- [ ] SYNC-002 Continuation and aggregate failure reporting
- [ ] RET-001 Immutable publication-generation retention ordering
- [ ] RET-002 Five-revision selection
- [ ] RET-003 Dry-run prune plans
- [ ] RET-004 Published-view and manifest cleanup
- [ ] RET-005 Supported Hub cache revision deletion
- [ ] RET-006 Prune journals, tombstone rename, reconciliation after partial failure
- [ ] RET-007 Protect unmanaged and upstream-missing repositories

## Phase 6 — Dependency Warnings and Archive Verification

- [ ] DEP-001 Model-card dependency inspection
- [ ] DEP-002 Adapter-config dependency inspection
- [ ] DEP-003 Compare observations with declared dependencies
- [ ] DEP-004 Persist and display non-fatal warnings
- [ ] VER-001 `verify --new`
- [ ] VER-002 Unique-object full verification
- [ ] VER-003 Revision-scoped verification
- [ ] VER-004 Verification estimation
- [ ] VER-005 Verification reports and current health
- [ ] VER-006 Isolated-cache repair, atomic ref switching, retirement grace, checkpointed cleanup

## Phase 7 — TrueNAS and CentOS Stream Deployment

- [x] NAS-001 Create and tune the TrueNAS dataset (2026-07-24, host prep — quota deferred to handoff item 4)
- [x] NAS-002 Create sync and read identities and permissions (2026-07-24, host prep)
- [x] NAS-003 Configure exact-host read/write export (2026-07-24, host prep; write-verified)
- [b] NAS-004 Server-side read-only consumer export — operator (handoff item 1)
- [b] NAS-005 Disjoint writer/consumer export proof — operator-assisted (handoff item 2); hardlink + atomic rename already proven on the live dataset 2026-07-24
- [b] NAS-006 Snapshots, replication, scrubs, capacity alerts — operator (handoff item 3)
- [x] HOST-001 Provision CentOS Stream 10 VM, DNS, time, updates (2026-07-24, host prep)
- [x] HOST-002 Service identity and local paths (2026-07-24, host prep)
- [x] HOST-003 Hard NFSv4 mount (2026-07-24, host prep; automount active)
- [ ] HOST-004 Install the locked application environment
- [ ] SYS-001 Install and validate systemd target, services, timers
- [ ] SYS-002 Apply and test systemd hardening
- [ ] SEL-001 Validate all operations with SELinux enforcing
- [ ] SEC-001 Validate optional systemd credential support

## Phase 8 — Operational Readiness and Release

- [ ] OPS-001 Installation and upgrade runbooks
- [ ] OPS-002 Sync, verification, pruning, and status runbooks
- [ ] OPS-003 Corruption and repair runbooks
- [ ] OPS-004 Snapshot/replica restore runbook
- [ ] OPS-005 Failure-injection suite (test-level §26.6; live-mount interruption tests are handoff item 7)
- [ ] OPS-006 Capacity and throughput benchmarks (writer-side measurements)
- [ ] OPS-007 Downstream copy and manifest verification (exercise the consumer helper from the writer against `published/`; the true consumer-client test is handoff item 5)
- [ ] REL-001 Build and install release candidate from wheel
- [ ] REL-002 Final quality and security gates
- [ ] REL-003 Tag and document the first release

## Live rollout checkpoints (§29, writer-side)

- [ ] Archive initialized on `/srv/hfcache`; UUID recorded in `/etc/hfcache/config.toml` (§36.4 one-time authorization)
- [ ] `hfcache doctor` clean on the live mount
- [ ] Test repositories chosen and recorded below; `hfcache plan` reviewed
- [ ] First manual sync published both test repositories
- [ ] Second sync idempotent (skip)
- [ ] `hfcache verify --full` clean; `hfcache status` clean
- [ ] `hfcache.target` enabled; sync timer active; verification timer installed but disabled

## Test repositories (decide at implementation time, §36.5)

- Model: _TBD — small public model, well under 100 MB, availability confirmed on the Hub_
- Dataset: _TBD — small public dataset, well under 100 MB, availability confirmed on the Hub_

## Operator handoff

Keep instructions exact and copy-pasteable; add acceptance checks.

1. **NAS-004 — consumer export (TrueNAS UI on `nas.lab.cross.solutions`):**
   NFSv4 export of `/mnt/tank/huggingface-archive/published`, read-only enabled
   server-side, Mapall `hfcache-read:hfcache-archive`, allowed clients =
   explicit consumer hosts or consumer VLAN, **excluding** `192.168.10.90`
   (plan §20.2). Acceptance: consumer can read; consumer create/modify/
   rename/delete all fail at the server.
2. **NAS-005 — disjointness proof:** from a consumer client, mount the
   `published/` export and prove read works and writes fail while the writer
   export stays read/write; confirm TrueNAS 25.10.5 accepts the
   parent/subdirectory topology, else invoke the §20.2 two-dataset fallback.
3. **NAS-006 — data protection:** snapshots (daily ×14 d, weekly ×8 w, monthly
   ×12 m, daily before 02:00 sync), replication, scrub cadence, capacity
   alerts per plan §20.3.
4. **Dataset quota:** set after the session reports dry-run sizes for the
   chosen production repositories (plan §20.1).
5. **Consumer copy test (§29 steps 10–11):** from a consumer client, copy the
   current model and dataset revisions with the documented helper and verify
   against the manifests.
6. **Reboot persistence (§26.5):** reboot the writer; confirm mount, target,
   and timers return; confirm boot completes with the NAS down.
7. **Live-mount interruption window (§26.4):** operator-supervised NFS
   disconnect/reconnect during a test sync, or provision a disposable dataset.
8. **Verification timer enable (§29 step 14):** confirm the quarterly calendar
   does not overlap NAS scrub/SMART/replication, then enable.
9. **Optional cleanup:** revoke passwordless sudo
   (`sudo rm /etc/sudoers.d/tyler-nopasswd`) after rollout.

## Operator decisions needed

_None yet._

## Decisions

_Settled implementation deviations from `docs/plan.md`, with rationale (§36.3)._

1. **`docs/schemas.md` added beyond the plan §7 documentation set** (2026-07-24,
   ARC-004). The plan's `docs/` listing has no home for `ARC-004`'s durable JSON
   schemas. Folding them into `architecture.md` would have made one document
   carry both the reasoning and roughly a thousand lines of format reference;
   folding them into `configuration.md` would have conflated operator input with
   application output. A dedicated schema reference is also the document a
   consumer or auditor reads without needing anything else. Plan §7 is updated
   in the `ARC-005` commit, once the full documentation-set deviation is known.

2. **`docs/cli.md` added beyond the plan §7 documentation set** (2026-07-24,
   ARC-005). Same reasoning as decision 1. `operations.md` is the Phase 8
   runbook document — task-oriented, "how do I rotate a revision" — and is the
   wrong home for a reference contract that Phase 2 code is written against.
   Keeping the command surface, JSON envelope, exit-code aggregation, and the
   complete error taxonomy in one place also means `CFG-007` has a single
   normative source. Plan §7's `docs/` listing is updated in this commit to
   include both `cli.md` and `schemas.md`; the deviation is now final.

3. **Exit-code aggregation order fixed as `40`, `50`, `30`** (2026-07-24,
   ARC-005). Plan §11.2 fixes the codes and requires a non-zero result when a
   run continues past a repository failure, but does not say which code wins
   when several arise in one run. Codes `10` and `20` abort before
   per-repository work, so only `30`/`40`/`50` can co-occur. They are ordered by
   operator urgency — possible corruption, then degraded retention, then stale
   content — and every classification encountered is still listed in the JSON
   envelope's `errors` array, so aggregation hides nothing.

4. **Prune removes the per-SHA reference before tombstoning the tree**
   (2026-07-24, ARC-006). Plan §15.2 ordered these the other way — tombstone the
   tree and manifest at step 8, remove `refs/revisions/<sha>.json` at step 9.
   That leaves a window in which a reference names a tree that has already been
   renamed into trash, which breaks the invariant that every existing reference
   resolves (`FS-10`) and would be visible to `verify` and `repair`, both of
   which resolve per-SHA refs. Recovery never needed the reference to find the
   tree: the persisted `PrunePlan` already names it. Every property plan §15.2
   asserts is preserved — cache deletion still happens while all six revisions
   are published, rollback before the commit point still restores six revisions,
   and the complete manifest is still recoverable from trash. Plan §15.2 steps
   8–9 are updated in this commit.

5. **`sync.stale_staging_age_hours` added to the configuration schema**
   (2026-07-24, ARC-006). Plan §13.3 requires that stale staging directories be
   reclaimed only when they "exceed a configurable age", but the §9 schema had no
   key for it, so the requirement was unimplementable as written. Added with a
   24-hour default and a `1..8760` range. The delay is not the safety mechanism
   on its own — reclamation also requires a transaction-ID-shaped name and an
   existing journal — it exists so a concurrent operator command cannot have its
   working directory reclaimed underneath it. Plan §9 and §9.1 are updated in
   this commit.
