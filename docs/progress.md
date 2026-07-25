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

- [x] BOOT-001 Initialize uv project and `src/` layout (includes `git init` + initial docs commit per §36.2) (2026-07-24, this commit — `pyproject.toml`, `src/hfcache/`, `tests/{unit,integration,system,fixtures}`, `examples/`, `packaging/systemd/`, `README.md`, `LICENSE`, `.editorconfig`; git baseline commit `87323c2`)
- [x] BOOT-002 Pin Python and create `uv.lock` (2026-07-24, this commit — CPython 3.14.6 validated against the full locked set; `huggingface-hub` 1.24.0, `hf-xet` 1.5.2, `pydantic` 2.13.4, `typer` 0.27.0)
- [x] BOOT-003 Configure Ruff formatting and linting (2026-07-24, this commit — 37 rule families incl. `DTZ`, `S`, `PTH`, `TRY`, `FBT`, `SLF`; relative imports banned; `assert` flagged in `src/`)
- [x] BOOT-004 Configure Pyrefly (2026-07-24, this commit — `src` + `tests` checked, Python 3.14, non-permissive ignores; Ruff `ANN` added since pyrefly infers rather than requires annotations)
- [x] BOOT-005 Configure pytest and coverage (2026-07-24, this commit — strict markers/config, `live`/`nfs` opt-in markers deselected by default, warnings-as-errors, branch coverage; autouse fixture strips ambient Hub state from every test)
- [x] BOOT-006 Add Typer entry point and version command (2026-07-24, this commit — `src/hfcache/cli.py`, `errors.py` `ExitCode`, `__main__.py`, console script; `--json` envelope emitted and asserted against the `docs/cli.md` §4 contract)
- [x] BOOT-007 Add provider-neutral quality scripts and build smoke test (2026-07-24, this commit — `scripts/check.sh` runs the §8.4 gate; `tests/system/test_wheel_smoke.py` installs the wheel into a clean venv, marker `build`)

**Phase 1 complete.** `scripts/check.sh --with-build` passes from a clean
checkout: lock check, format, lint, pyrefly, pytest, `uv build`, and the wheel
install smoke test.

## Phase 2 — Configuration, Models, and Read-only CLI

- [x] CFG-001 Strict Pydantic configuration models (2026-07-24, this commit — `src/hfcache/config.py`, `errors.py` `Problem`/`HfcacheError`; all 16 `HFCFG###` codes implemented and each provoked by a test)
- [x] CFG-002 Token-source abstraction without literal secrets (2026-07-24, this commit — `src/hfcache/credentials.py`: §7 resolution order, `HFARG002`/`HFARG005`/`HFARG006`, `hub_argument` returns `False` and never `None`, redaction proven over generated tokens; no function in the module accepts a token value. The `--token-file` option is parsed by the CLI as of `BOOT-006`; it is *resolved* by the first command that loads configuration, which is `CFG-005`)
- [x] CFG-003 Repository identity and safe path mapping (2026-07-25, this commit — `src/hfcache/identity.py`: every Hub-facing grammar, `RepositoryIdentity` self-validating, `TYPE:ID[@SHA]` selectors, opaque-id minting; `src/hfcache/paths.py`: the whole §5.1 tree, relative-path grammar, containment, collision folding. Both at 100% branch coverage. `config.py` now imports its identifier grammars rather than defining them)
- [x] CFG-004 Manifest and report models (2026-07-25, this commit — `src/hfcache/models.py` (foundation, sentinel, reference, prune plan, audit records, journal), `manifests.py` (`RevisionManifest`), `reporting.py` (run report, verification report, catalog). One serializer for every writer including the CLI envelope; §1.1 version refusal; a golden fixture per format in `tests/fixtures/schemas/`. All three modules at 100% branch coverage)
- [x] CFG-005 `config validate` (2026-07-25, this commit — `config` sub-app in `src/hfcache/cli.py`; loads configuration and resolves the credential, takes no lock and makes no network call; failure envelope emitted with every problem, exit `10`; `--token-file` is now resolved as `CFG-002` said it would be here)
- [x] CFG-006 Read-only portions of `doctor`, `status`, and `plan` (2026-07-25, this commit — selector resolution with `HFARG001`/`HFARG004`; `doctor` check-runner with `configuration`, `credential`, `hub_endpoint`, and `--read-only`'s three explicit unproven capabilities; `plan` over enabled repositories in configuration order; `status` reporting local truth with `upstream_state: unknown`. **Still to come:** `doctor`'s storage probes at `STO-009` and its Hub reachability/identity checks at `HUB-001`/`HUB-002`; `plan`'s resolved SHA and size estimates at `HUB-003`/`HUB-004`; `status`'s retained-revision and health blocks at `STO-008`/`VER-005`)
- [x] CFG-007 Deterministic JSON output and error taxonomy (2026-07-25, this commit — `src/hfcache/taxonomy.py`: every family's exit classification and the §3 aggregation rule; `Envelope`/`EnvelopeProblem` in `reporting.py` so the `--json` contract is a model rather than a dict built per call site. `tests/unit/test_taxonomy.py` parses the code tables out of `docs/cli.md` §5 and `docs/configuration.md` §8 and checks both directions, so the taxonomy cannot drift from the documents that define it)

**Phase 2 complete.** Every operator input is validated before any network or
filesystem access: configuration, credentials, repository identity, path safety,
durable schemas, and the read-only command surface. `scripts/check.sh` passes
with 566 tests; every Phase 2 module is at 100% branch coverage except `cli.py`
at 99% and `config.py` at 89%, whose gaps are the non-string type guards that
predate `CFG-003`.

## Phase 3 — Storage Safety and Publication Primitives

- [x] STO-000 Guarded one-time archive initialization and inspection (2026-07-25, this commit — `src/hfcache/storage.py`: mount-table proof, durable byte writes, the known-empty-layout walk, and `initialize_archive`; `archive` sub-app in `src/hfcache/cli.py` with `init`, `--inspect`, `--confirm`, and `--archive-id`. The §6.2 empty-`published/` adoption is implemented with ownership compared against the archive root, per decision 31. 100% branch coverage. **Not yet run against `/srv/hfcache`:** the §36.4 one-time authorization is spent at the rollout checkpoint after `HOST-004`, not here)
- [ ] STO-001 NFS mount and filesystem-type detection — *the detection itself landed at `STO-000` (decision 28), so what remains is the shared preflight built on it:* the `.store/health/probe-<probe-id>` create/fsync/rename/delete writability probe (`HFMNT008`, plan §19 items 6 and 10), the staging/destination same-filesystem check (`HFMNT009`, `FS-04`), one ordered check runner both `doctor` and every mutating command use, `doctor` checks 2–5, 7, and 8 of the `docs/cli.md` §2 table wired in, `--read-only` skipping the probe, and `doctor` exiting `20` when any check fails instead of always `0`
- [ ] STO-002 Sentinel/archive-ID validation — `doctor` check 6; `_read_sentinel` exists in `storage.py` from `STO-000`, so this is `HFMNT005` for an absent sentinel plus the gate every mutating command runs
- [ ] STO-003 Free-space and reserve calculations — `doctor` check 12 (`HFMNT011`) and the `HFWRN005` approaching-reserve warning
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

- [ ] Archive initialized on `/srv/hfcache` with the UUID already provisioned in
      `/etc/hfcache/config.toml` (§36.4 one-time authorization). `STO-000` built
      the command; the authorization is spent here, after `HOST-004` installs a
      release, so the layout is the one the finished application uses.
      `archive init --inspect` is non-mutating and may be run against the live
      mount at any time before that.
- [ ] `hfcache doctor` clean on the live mount
- [ ] Test repositories chosen and recorded below; `hfcache plan` reviewed
- [ ] First manual sync published both test repositories
- [ ] Second sync idempotent (skip)
- [ ] `hfcache verify --full` clean; `hfcache status` clean
- [ ] `hfcache.target` enabled; sync timer active; verification timer installed but disabled

## Test repositories (decide at implementation time, §36.5)

- Model: _TBD — small public model, well under 100 MB, availability confirmed on the Hub_
- Dataset: _TBD — small public dataset, well under 100 MB, availability confirmed on the Hub_

Chosen at `HUB-004`, when the Hub adapter can confirm availability and size
without downloading. §36.5 authorizes the session to choose; see **Operator
decisions needed** item 1 for the separate question that does need an operator.

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

1. **Which repositories the archive is ultimately for** (raised 2026-07-24, during
   `CFG-002`; not blocking until `HUB-005`). Two separate questions have been
   conflated so far, so they are separated here:

   - *The two test repositories* (§36.5) do **not** need an operator: the plan
     authorizes the session to choose them, requiring only that each is public,
     well under 100 MB, and confirmed available at implementation time. They stay
     `_TBD_` above until `HUB-004` can resolve and size candidates against the
     live Hub, and the choice is recorded here and in `examples/config.toml` when
     made.
   - *The production repository list* does need an operator, because it is the
     only input to handoff item 4 (the TrueNAS dataset quota) and to §29 step 12.
     Nothing is blocked while it is open: Phases 3–6 are written against
     configuration, not against a particular repository.

   When the list is known, `hfcache plan` reports dry-run sizes for it without
   downloading anything, which is the number the quota decision wants.

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

6. **MIT license, `uv_build` backend** (2026-07-24, BOOT-001). Plan §7 requires a
   `LICENSE` file but names no license, and §8.1 requires `uv build` artifacts
   without naming a backend. MIT is the conventional permissive default for an
   internal tool and constrains nothing; changing it is a one-file edit with no
   code impact. `uv_build` is uv's own PEP 517 backend, needs no extra build
   dependency, and supports the `src/` layout natively — consistent with §8.1's
   requirement to build both sdist and wheel with `uv build`.

7. **Python 3.14 pin confirmed; `hf-xet` is a required dependency, not an extra**
   (2026-07-24, BOOT-002). Plan §8.1 made the 3.14 pin "subject to final
   compatibility validation" and §8.2 left open whether the Xet backend arrives
   by default or via the `huggingface_hub[hf_xet]` extra. Both are now settled:
   `huggingface-hub` 1.24.0 requires `hf-xet` directly, and `hf-xet` 1.5.2 ships
   `cp38-abi3` manylinux wheels that install on CPython 3.14.6 with no source
   build. The fallback to 3.13 is not needed. Plan §8.1 and §8.2 updated in this
   commit.

   Also verified against the locked version, since the plan's design depends on
   them: `HfApi.{repo_info,model_info,dataset_info,list_repo_tree,whoami}`,
   `snapshot_download`, `scan_cache_dir`, `HFCacheInfo.delete_revisions`, and the
   `Cached{Repo,Revision,File}Info` types all exist. `snapshot_download` accepts
   `dry_run`, which is what plan §13.2 step 3 needs for pre-download size
   estimation — no separate estimation path is required.

8. **`scripts/` added to the project layout; no CI-provider configuration**
   (2026-07-24, BOOT-007). Plan §7's tree has nowhere to put the
   "provider-neutral quality scripts" `BOOT-007` requires, so `scripts/check.sh`
   is added and plan §7 updated in this commit. Deliberately *not* added: any
   CI-provider file. The gate is one script that a shell, a git hook, or a
   pipeline all invoke identically, so a green pipeline and a green workstation
   mean the same thing. A Makefile was considered and rejected — `make` is not
   installed on the CentOS Stream 10 writer, and bash is.

9. **`--token-file` with `token_mode = "disabled"` is `HFARG002`, not a silent
   choice** (2026-07-24, CFG-002). `docs/configuration.md` §3 says `"disabled"`
   means Hub calls *always* pass `token=False`; §7 says `--token-file` is the
   first-match-wins source. When both are present the two sentences disagree, and
   the contract did not say which wins. Honouring the flag violates the configured
   mode. Ignoring the flag is worse: the operator believes the run was
   authenticated and nothing says otherwise. So the combination is refused before
   any Hub request, consistent with `AD-11`'s rule that a mode is never silently
   downgraded. `docs/configuration.md` §7.2 and the `HFARG002` row in
   `docs/cli.md` §5.1 are updated in this commit.

10. **`HFARG006` added for a systemd credential that is present but unusable**
    (2026-07-24, CFG-002). The taxonomy had `HFARG005` for `--token-file` and
    nothing for the other source, so an empty, unreadable, or malformed systemd
    credential had no code. It needs one distinct from `HFARG005`, because the two
    conditions have different fixes — one is a mistyped command line, the other a
    broken unit or credential store. Absence still resolves to anonymous access,
    since `token_mode = "optional"` says a missing credential is normal; presence
    plus unusability does not, because continuing anonymously would report success
    for a run the operator believes was authenticated. `$CREDENTIALS_DIRECTORY`
    set to a relative path shares the code: systemd always sets it absolute, so a
    relative value means the environment is wrong and a credential would otherwise
    be read relative to the working directory. Added to `docs/cli.md` §5.1 in this
    commit; the plan does not enumerate `HFARG` codes, so no plan amendment is
    needed.

11. **A credential file is validated, never sanitized** (2026-07-24, CFG-002).
    §7 said to strip a single trailing newline and said nothing about what may
    remain. A token becomes an `Authorization` header, so a value containing a
    stray carriage return, tab, or second newline must not be forwarded — and must
    not be quietly cleaned up either, because a file that malformed is not
    reliably the token the operator intended. After the one newline is removed the
    remainder must be non-empty printable ASCII with no whitespace, in a regular
    file of at most 4096 bytes. The size cap keeps a mistyped path from reading a
    large file into memory before its contents are found unusable. Recorded as
    `docs/configuration.md` §7.1.

12. **`hub.credential_name` may not be `.` or `..`** (2026-07-24, CFG-002). Both
    match the published `[A-Za-z0-9._-]{1,64}` grammar, and both name a directory
    rather than a credential. Neither is exploitable — no `/` is permitted, so the
    worst case resolves to `$CREDENTIALS_DIRECTORY` itself and fails as "not a
    regular file" — but it fails at run time with a confusing message instead of
    at `config validate` with a clear one. Rejected as `HFCFG013`, and the §3
    constraint column is updated in this commit.

13. **A reference's paths are relative to `published/`, every other artifact's are
    archive-relative** (2026-07-25, CFG-003). `docs/schemas.md` §1 said every path
    field is archive-relative; §4.1 said a reference's `tree` and `manifest` are
    relative to `published/`, and its worked example was written that way. Only one
    can hold. `published/` wins, because it is not a stylistic choice: a consumer
    mounts `published/` and nothing else, so an archive-relative `published/repos/…`
    would resolve to `<mount>/published/repos/…`, which does not exist. The rule is
    now stated once with its exception, in `docs/schemas.md` §1 and in `FS-09`, both
    amended in this commit. `RepositoryLayout` exposes the two forms as separate
    methods — `tree_reference` and `manifest_tree_field` — so the distinction is
    made by the type of artifact being written rather than by a caller remembering
    which base applies.

    Extended at `CFG-004`: the prose was right and three *examples* were wrong.
    The manifest (§3), prune plan (§8), and journal (§10) examples had all copied
    the reference's published-relative form into fields their own prose calls
    archive-relative, so every one of them was missing the `published/` prefix.
    Corrected in the `CFG-004` commit. The rule that decides the base is narrow:
    a field is published-relative only when a consumer has to resolve it, which
    is true of exactly the reference's `tree` and `manifest`. Everything else is
    archive-relative, including `catalog/verification.json`'s `report`, which
    names a path under `runs/` that a consumer deliberately cannot follow.

14. **The repository-relative path grammar is published** (2026-07-25, CFG-003).
    `docs/security.md` T-02 required every repository path to be "normalized and
    validated to remain under the publication root" but never said against what
    grammar, so the requirement could not be implemented twice the same way. Now
    written out as a table in `docs/architecture.md` §5.3. The rule that generated
    it: reject what can **escape**, allow what is merely awkward. A backslash is
    rejected because it is a path separator on a consumer platform, where
    `a\..\..\b` traverses; a trailing space or a name like `CON` is left alone,
    because this application does not get to decide what a repository may call its
    files. Sizes are measured in bytes rather than characters, since `NAME_MAX` is.

15. **Collision folding is deliberately stricter than any one filesystem**
    (2026-07-25, CFG-003). T-02 requires rejecting two manifest entries that
    "resolve to the same on-disk path — including via case or Unicode-normalization
    collision" without fixing a fold. The fold is NFC plus `str.casefold`. Full case
    folding also maps some ligatures, so `ﬁle` and `file` are reported as colliding
    even though nothing would really merge them. That over-rejection is the intended
    direction: refusing a pair of names is visible, explainable, and recoverable by
    an operator, while publishing a tree in which two manifest entries resolve to
    one file is silent and corrupts the thing being archived (`AD-16`). NFKC is not
    applied — it folds superscripts and width variants that no consumer could
    confuse, and would refuse legitimate names for nothing.

16. **Five identifier grammars accepted a trailing newline; fixed** (2026-07-25,
    CFG-003). `config.py` compiled `^…$` and applied it with `re.match`, and in
    Python `$` also matches immediately before a trailing newline. So
    `parse_revision` accepted `"main\n"` and, worse, accepted a 40-character SHA
    with a newline glued to it and returned the value including the newline — which
    would then have been sent to the Hub and written into a path and a manifest.
    TOML can produce such a value through an escape or a multi-line string. All five
    patterns (`_SEGMENT`, `_REFERENCE_NAME`, `_COMMIT_SHA`, `_ACCOUNT`,
    `_CREDENTIAL_NAME`) now use `fullmatch` with no anchors, `tests/unit/
    test_identity.py` provokes the newline case for every grammar, and a structural
    test fails if any future pattern in the module is written anchored. This is the
    same defect found in `credentials.py` during `CFG-002`; finding it a second time
    is why the guard is now structural rather than another example.

17. **`credentials.py` and `identity.py` added to the plan §7 module list**
    (2026-07-25, CFG-003). Neither existed in the plan's source tree.
    `credentials.py` should have been added by `CFG-002` and was missed;
    `identity.py` is new here, splitting the *names* the archive uses from the
    *paths* built out of them. The split has a purpose beyond tidiness: `paths.py`
    joins identifiers straight into filesystem paths, so it needs a module whose
    whole contract is that a value which came out of it is safe to join. Plan §7 is
    updated in this commit.

18. **Durable files are indented; the `--json` envelope is not** (2026-07-25,
    CFG-004). `docs/schemas.md` §1 named the separators `(",", ": ")` but no
    indentation. That pair is exactly what `json.dumps` uses *when indentation is
    on* — the compact spelling would be `(",", ":")` — and every worked example in
    the document is 2-space indented, so indentation was intended and unstated.
    Now stated. The envelope stays unindented, which is not an inconsistency but
    the distinction that matters: a durable file is read and diffed by an operator
    during an incident, while the envelope is one machine-read line on a pipe.
    `docs/cli.md` §4 already listed only the three rules that carry over — sorted
    keys, UTF-8, trailing newline — so no change was needed there. Both paths call
    `models.serialize`, so §11's "one shared function" is literal rather than
    aspirational.

19. **Reading a durable artifact takes the caller's error class *and* code**
    (2026-07-25, CFG-004). The same malformed file means different things
    depending on which artifact it is: a bad manifest is `HFVER007` at exit `40`,
    a bad journal is `HFTXN001` at exit `20`, a bad sentinel is `HFMNT006` at exit
    `20`. `load` therefore takes both, and applies the code to every problem it
    reports, with the field path as the location. That is what lets the field
    validators in `hfcache.identity` and `hfcache.paths` stay ignorant of which
    artifact they are validating — the artifact names the code, the field names
    the place. `parse_archive_relative` and `parse_repository_relative` gained an
    optional `code`; omitted, they raise an uncoded `ValueError` for a validator
    to collect.

20. **§1.1's "unknown keys are preserved when rewritten" applies only to the
    journal** (2026-07-25, CFG-004). It contradicts §11's `extra="forbid"` as
    written. The contradiction is narrower than it looks: manifests are immutable,
    references are replaced wholesale, and the catalog is rebuilt from scratch, so
    the transaction journal is the only artifact that is ever read, modified, and
    written back — the only place an unknown key could be destroyed. Every model
    forbids unknown keys and reports them by location, which satisfies "reported
    and never silently dropped". The preservation half is a journal-rewrite
    concern and belongs to `STO-010`, which is where that rewrite is implemented.

21. **A Pydantic validator must raise `ValueError`, never `TypeError`**
    (2026-07-25, CFG-004). Found by a test: Pydantic converts `ValueError` and
    `AssertionError` into validation errors and lets everything else propagate, so
    a `TypeError` raised for a non-string digest escaped `load` as a bare
    exception instead of being reported as a coded problem naming the field — the
    one thing `load` exists to guarantee. Both sites now raise `ValueError` with a
    `# noqa: TRY004`, since Ruff reasonably prefers `TypeError` for a type check
    and is wrong about it here.

22. **`config validate` reports `token_source`** (2026-07-25, CFG-005).
    `docs/cli.md` §4.1 listed only the fingerprint and two counts. The command an
    operator runs before enabling the timer should also answer "did the credential
    resolve, and from where" — otherwise the first evidence that a systemd
    credential is missing or that `--token-file` is unreadable arrives during a
    scheduled run hours later. The field carries the *source* name only
    (`token-file`, `systemd-credential`, `none`), never the value, which is what
    `docs/security.md` T-07 permits. `docs/cli.md` §2 and §4.1 updated in this
    commit.

23. **A whole-table constraint is not reported alongside a bad field in the same
    table** (2026-07-25, CFG-005). Pydantic does not run a `mode="after"` model
    validator when a field in that model already failed, so a configuration with
    both a bad `storage.archive_root` and `maximum_revisions = 9` reports
    `HFCFG006` now and `HFCFG011` only after the path is fixed. This narrows
    `docs/configuration.md` §8's promise that an operator fixes one file once, and
    it is recorded rather than worked around: making it complete would mean
    turning every table-level rule into a field-level one, which would lose the
    cross-field checks that are the reason those validators exist. The behaviour
    is asserted in `tests/unit/test_config_validate.py` so it cannot change
    silently.

24. **A partially implemented command reports what it probed, not a placeholder**
    (2026-07-25, CFG-006). `doctor` is specified with fourteen checks; Phase 2 can
    perform three of them, because the rest need the storage layer or the Hub
    adapter. Two ways to handle that were rejected: emitting the missing checks
    with a `skipped` outcome and a "not implemented yet" detail, which puts
    development state into operator-facing output, and emitting them as `pass`,
    which is a lie. They are simply absent until the package that performs them
    lands, and the `checks[]` array is ordered and open-ended so appending is the
    natural way to add one. `--read-only` is the exception and is *not*
    development state: `docs/cli.md` §2 requires it to say that hardlink, rename,
    and ref-replacement capability are unproven, so those three entries are real
    output that will still be there at v1. The same rule governs `plan` and
    `status`: each reports the fields it can determine and omits the rest, and the
    checkbox above names the work package that completes each one.

25. **The taxonomy is checked against the documents that define it, in both
    directions** (2026-07-25, CFG-007). A table of codes in a document and a table
    of codes in a module drift the moment someone edits one. `test_taxonomy.py`
    therefore parses `docs/cli.md` §5 and `docs/configuration.md` §8 and asserts
    that every documented code classifies as its own section header says, that
    every family the code knows about appears in the documents, and that the
    `HFCFG` range has no gaps. It reads only the leading cell of a table row:
    §5.3's prose cross-references `HFVER002` while explaining how it differs from
    `HFSYN003`, and a mention is not a claim about which section a code belongs
    to. Classification is by family prefix rather than by a per-code table,
    because a code's family already determines its exit and a second table would
    be a second thing to keep in sync.

26. **The `--json` envelope is a model, not a dict** (2026-07-25, CFG-007). It is
    not durable — nothing on the archive is ever this shape — but it is a contract
    with automation, and it was being assembled by hand at each call site with the
    `outcome`/`exit_code` agreement enforced by a conditional expression. It is
    now `reporting.Envelope`, which refuses an undocumented exit code, an
    `outcome` that contradicts it, `success_with_warnings` without warnings, and a
    failure carrying no errors. It keeps its own `schema_version`, separate from
    the durable schemas, because an invocation record and an archived manifest
    change for different reasons.

27. **`archive init` writes the configured archive id; it does not mint one**
    (2026-07-25, STO-000). Plan §6.2 steps 4 and 7 had initialization generate a
    UUID and print it for the operator to paste into configuration. That cannot
    be reconciled with the rest of the contract. `--archive-root` must equal
    `storage.archive_root` (`docs/cli.md` §2), so configuration is loaded and
    fully validated before anything happens — and `storage.archive_id` is a
    *required* canonical UUID (`HFCFG012`), so the operator has necessarily
    already chosen one before `archive init` can run at all. Minting a second
    would write a sentinel that disagrees with configuration, which is precisely
    the state `FS-03` calls fatal and never repairable, and would leave the new
    archive unusable until an unrelated file was edited. The UUID is therefore
    provisioned into configuration — which is what the `"replace-with-provisioned-uuid"`
    placeholder in `docs/configuration.md` §4 has always asked for — and
    `--archive-id` is kept as the same deliberate restatement `--archive-root`
    is: the one irreversible command does not take its inputs from a file alone.
    Disagreement is `HFARG002`. Plan §6.2 and `docs/cli.md` §2 updated in this
    commit.

28. **`STO-000` lands the primitives it cannot be correct without** (2026-07-25,
    STO-000). It is the first package of Phase 3 but depends on three later
    ones: mount and filesystem-type detection (`STO-001`), reading the sentinel
    and comparing its id (`STO-002`), and atomic writes (`STO-005`). An
    initialization that cannot prove its target is NFS, cannot tell an
    initialized archive from unknown content, and cannot write its sentinel
    without a torn-write window is not a *guarded* initialization, so those
    pieces are here in their minimal form. The packages keep the rest of their
    scope: `STO-001` the shared preflight every mutating command runs plus
    `doctor`'s mount checks, `STO-002` that preflight's sentinel gate, `STO-005`
    the model-aware JSON and reference writers built on `atomic_write_bytes`.

29. **`archive init --inspect` exits `0` for an already-initialized archive**
    (2026-07-25, STO-000). `docs/cli.md` fixed no exit code for `--inspect`.
    Its two real uses both want a non-zero on a bad answer: confirming a target
    is clean before initializing, and confirming a failed initialization left
    only known partial paths so a retry is safe. But a healthy initialized
    archive is also "not initializable", and exiting `20` there would make the
    command useless as a routine check. So `--inspect` exits `0` when the target
    is initializable **or** correctly initialized, and `20` when it is neither —
    unknown content, symlinks, the wrong filesystem, or a malformed or
    mismatched sentinel. Recorded in `docs/cli.md` §2.

30. **A leftover `.tmp-` sibling is part of the known-empty layout contract**
    (2026-07-25, STO-000). §6.2 permits retrying a failed initialization once
    `--inspect` confirms the partial paths match the contract, but a crash
    between the sentinel's temporary write and its rename leaves a file the
    contract did not name — so the retry would refuse as "unknown content" and
    the archive could never be initialized without manual cleanup. Writing the
    sentinel in place instead was rejected: `O_EXCL` makes its *appearance*
    atomic but not its *contents*, and a truncated sentinel is worse than a
    stray temporary, because it looks like an initialized archive. The temporary
    is therefore recognised by its `<name>.tmp-<16 hex>` grammar, reported by
    `--inspect`, and removed by the retry. It is the only deletion this command
    performs and it is on a file the command owns, so `FS-19` is intact.

31. **`published/` adoption compares ownership against the archive root**
    (2026-07-25, STO-000). §6.2 and `FS-22` adopt a pre-existing `published/`
    only when "its ownership and mode already match §20.1", but §35.3 rules out
    the obvious implementation: the Mapall writer export presents NAS-side ids
    (`3001:3002`) that have no local account, so there is nothing local to
    compare `st_uid` with. "The same identity owns `published/` as owns the
    archive root" is the same rule in a form the writer can evaluate, and it
    fails exactly when the intended one would. The policy takes two
    `os.stat_result` values rather than two paths, which is what lets it be
    tested for identities this host cannot create — `tyler` cannot `chown` to
    3001. `docs/architecture.md` `FS-22` updated in this commit.

32. **A write that fails after every check passed is `HFMNT008`** (2026-07-25,
    STO-000). Everything `archive init` proves beforehand is a read, so a
    server-side read-only export presenting `rw` client options, a reached
    dataset quota, or the NAS going away mid-command are all discovered only by
    writing. Without a mapping those surface as an `OSError` traceback from the
    middle of a half-created layout. `docs/cli.md` §5.2 defines `HFMNT008` as a
    required directory being missing or failing the effective-write probe, which
    is the same condition observed a different way, so the whole mutation is
    wrapped and reported under it at exit `20`. The message names the failing
    path and points at `--inspect`, because decision 30 is what makes the retry
    safe.
