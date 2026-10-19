# Implementation Progress

**Current authority (`DOC-010`, 2026-10-17, decision 107).**
`docs/agents/plans/current.md` selects active work; dated plans own scope/order and
individual task files own execution status and evidence. This file retains
completed work-package evidence, Decisions, Operator handoff, and unmigrated
historical backlog. Its earlier tracker/startup instructions below remain
history, superseded for active work by `docs/agents/planning.md` and
`docs/agents/workflow.md`. An unchecked historical item is not authorization
to activate it.

Authoritative work-package tracker for `docs/agents/history/plan.md` §28, maintained under the
§36 Autonomous Implementation Protocol. Update this file **in the same commit**
as the work it records: mark the box, append `(YYYY-MM-DD, <short commit ref or
"this commit">)`.

Statuses: `[ ]` pending · `[x]` complete · `[b]` blocked (explain under
Operator handoff or Operator decisions needed).

Session startup: read `docs/agents/history/plan.md` in full, then this file, then
`git log --oneline -20`; re-run the §8.4 quality gates if source exists;
continue at the first unchecked item in phase order.

**Session protocol amendment (2026-10-17, `DOC-009`, decision 106).**
The startup paragraph above is the build-out record, superseded by
`docs/agents/workflow.md` at decision 82. `AGENTS.md` routes current sessions;
changes and plan implementations also review the affected invariants and ADRs
using `docs/invariants.md` and `docs/adr/README.md` progressively.

## Tags and discovery (2026-10-19)

- [x] CAT-001 Activate the feature plan and establish technical contracts
  (2026-10-19, this commit — [task](plans/tasks/cat-001-contracts-and-activation.md),
  [plan](plans/2026-10-19-plan-tags-and-discovery.md)). Reconciled `75d93a5`
  against reviewed `45f91c3`, preserving separate Timestral evidence. Proposed
  discovery/record/query contracts, optional metadata namespace, historical tag
  authority and narrow atomic adjunct exception are explicit in decision 133 and
  INV-018; relevant ADRs amended. Full baseline gate exited 0: 4315 passed/40
  deselected, build/three locked profiles and actual Cockpit lint/types/135 tests/
  build. Final changed-doc alignment (182 docs/19 helpers), 173 affected parser/
  contract tests and whitespace check passed. All feature code remains pending;
  no live/credential/production/push action occurred.

- [x] CAT-002 Add strict configuration tags and separate curation identity
  (2026-10-19, this commit — [task](plans/tasks/cat-002-configuration-tags-and-identities.md)).
  Shared bounded ASCII normalizer, frozen optional tags and schema-1 curation hash
  preserve the pinned old policy hash. Full caller audit retains operational
  comparisons, six-field authority and strict wrappers; real keyed admission
  distinguishes tag-only candidate content. Shared frontend fixture and config/
  discovery/example docs added. Focused 193 and final 43 tests passed. Full gate:
  4351 passed/40 deselected, build/three locked profiles and actual Cockpit lint/
  types/135 tests/build. INV-001/002/005/018 and decisions 119/122/133 reviewed;
  no new architectural choice/dependency, live action or push.

- [x] CAT-003 Add Cockpit tag authoring (2026-10-19, this commit —
  [task](plans/tasks/cat-003-cockpit-tag-authoring.md)). Legacy-safe optional tags,
  shared normalization, existing-config suggestions and repaired draft mode
  switching preserve labels. Exact installed-byte confirmation holds the root
  flock across API validation, buffers bounded stdout until postcheck and requires
  successful process completion. Tag-only races cannot hide behind equal policy
  hashes; backup/lock/privilege boundaries remain. CP-11/ADR122 amended under
  INV-018. Frontend gate actually ran; final focused guards/runner: 36 passed.
  Full gate: 4351 passed/40 deselected, build/three locked profiles and actual
  Cockpit lint/types/169 tests/build. Docs/whitespace and independent review pass.
  No production/live/credential/push action or new runtime dependency.

- [x] CAT-004 Implement bounded supplemental metadata records and storage
  (2026-10-19, this commit — [task](plans/tasks/cat-004-metadata-records-and-storage.md)).
  Strict independent record families/goldens, exact ref/manifest/source bindings,
  optional named namespace and original-live-lock/preflight capability guard
  descriptor-relative atomic records. Hard actual-read/JSON structure ceilings
  apply with shared budgets; unsupported/unsafe prior records and ambiguous temps
  remain preserved. No journal/index/GC/evidence rewrite. Review gaps fixed and
  final independent review clear. Focused 518 pass; full gate 4415 passed/40
  deselected, build/three locked profiles and actual Cockpit lint/types/169 tests/
  build. Affected INV/FS/TX and decision 133 reviewed; human contracts updated.
  No new dependency, production/live/credential/push operation.

- [x] CAT-005 Extract bounded static declarations (2026-10-19, this commit —
  [task](plans/tasks/cat-005-bounded-static-metadata-extraction.md)). Standard-library
  conservative YAML/strict JSON, exact no-follow manifest sources and shared actual
  byte/work limits retain only allowlisted attributed fields. Dataset declarations
  remain distinct from filename formats/availability; upstream tags remain separate.
  Hostile allocation/Unicode/alias fixtures and network/import/open spies cover
  V12-V14; independent review clear. Expanded focused 224 passed; final extractor
  37 passed. Full gate: 4452 passed/40 deselected in 485.46s, build/three locked
  profiles and actual Cockpit lint/types/169 tests/build. INV-018/AD-15/133 and
  related FS/authority requirements reviewed; human contracts/links updated.
  No runtime dependency, production/live/credential/host/push operation.

- [x] CAT-006 Detect bounded GGUF headers and exact shard sets (2026-10-19,
  this commit — [task](plans/tasks/cat-006-gguf-variants-and-shards.md)). Pinned
  v3LE mapping, explicit first-shard declaration authority and full unique
  publication/directory/prefix grouping retain honest formats/schemes/bits/roles.
  Safe tensor extents and contradiction checks never read tensor bodies;
  unbuffered source reads and realistic tokenizer arrays retain finite budgets.
  V15-V19 focused 194 passed; independent review clear. Full gate: 4551 passed/
  40 deselected in 486.30s, build/three locked profiles and actual Cockpit
  lint/types/169 tests/build. INV-018/AD-15/133 and related FS/authority requirements
  reviewed; human supported-subset/source/evidence docs updated. No new runtime
  dependency, production/live/credential/host/push operation.

- [x] CAT-007 Detect scoped AWQ/GPTQ declarations (2026-10-19, this commit —
  [task](plans/tasks/cat-007-quantized-weight-config-variants.md)). Explicit pinned
  producer fields bind one same-directory canonical/indexed member set; repeated
  index shard references count once. No root-policy inheritance, implicit defaults,
  runtime imports, unpickling or tensor reads. Pointer/truncated/ambiguous/unsafe/
  unsupported/contradictory candidates stay non-available; header arithmetic and
  aggregate work are bounded. V20-V22 expanded focused 248 pass; independent review
  and 4,394-case type probe clear. Full gate: 4605 passed/40 deselected in
  485.32s, build/three locked profiles and actual Cockpit lint/types/169 tests/
  build. INV-018/AD-15/133 and related FS/authority requirements reviewed; human
  producer/layout/schema/evidence docs updated. No new dependency or production/
  live/credential/host/push operation.

- [x] CAT-008 Capture sync and repair metadata (2026-10-19, this commit —
  [task](plans/tasks/cat-008-sync-metadata-lifecycle.md)). Joined producer/retention
  completion precedes original-lock capture; fresh installed curation projects
  tags/fingerprint/time without replacing admitted policy or credentials. Retained
  sync changes no download/publication/generation; repair binds only its exact
  replacement and preserves historical evidence/grace. Shared extraction/record
  budgets, capacity, bounded journal order/identity and canonical-before-read
  guards keep optional errors visible without changing successful domain exits.
  V23-V25 focused 221 pass; logging/MCP expectation checks 73 pass; independent
  review clear. Full gate: 4628 passed/40 deselected in 494.66s, build/three locked
  profiles and actual Cockpit lint/types/169 tests/build. INV-018/AD/TX/FS and
  decision 133 reviewed; human lifecycle/schema/CLI contracts updated. No new
  dependency or production/live/credential/host/push action.

- [x] CAT-009 Add typed offline refresh service (2026-10-19, this commit —
  [task](plans/tasks/cat-009-offline-refresh-service.md)). Strict canonical intent,
  fresh installed curation and one original lock/preflight guard resolve bounded
  configured/retained scope before independent record attempts. Exact current
  refs, honest skips/counts and typed partial/failed outcomes preserve history,
  unsupported records and immutable authority. Shared reader/extraction/write and
  complete-result budgets include actual generation widths. Unfinished work
  refuses without recovery/repair/prune/cleanup; no Hub/credential/config/hash
  authority is added. V26-V28 focused 184 pass, including 49 new cases and actual
  same-key/new-key runner replay; independent review clear. Full gate: 4677 pass/
  40 deselected in 507.48s, build/three locked profiles and actual Cockpit lint/
  types/169 tests/build. INV-018/AD/FS/TX and decision 133 reviewed; architecture,
  discovery/schema and invariant/ADR links current. No new runtime dependency,
  production/live/credential/host/push action or public endpoint activation.

## Documentation authority separation (2026-10-18)

- [x] DOC-011 Separate human documentation from implementation records
  (2026-10-18, this commit — [task](plans/tasks/doc-011-human-docs-authority-and-record-migration.md),
  [plan](plans/2026-10-18-plan-rest-mcp-docs-scripts-alignment.md)). Explicit
  decision-130 path amendment precedes 47 collision-checked moves; manifest
  records original git/SHA-256 provenance, exact documentation/reference inventory
  and normative coverage map. One selector, preserved CLAUDE symlink, process ADRs
  and INV-011 now under agents. Missing Hub/storage/copy/hash/logging/test/calendar
  requirements have living human homes; no archive behavior changed. Focused
  checks: 120 passed. Full `scripts/check.sh`: 4062 passed/40 opt-in deselected,
  formatting/lint/types/build and all three locked install profiles passed;
  actual Cockpit lint/135 tests/build passed with no skip. Markdown links/anchors,
  independent migration audit and diff whitespace checks passed. Reviewed
  FS-02/03/04/19, AD-17/18, INV-010/011 and process ADRs; technical guarantees and
  host restrictions unchanged. The later user instruction permits github/forgejo
  feature-branch pushes after final acceptance only. No host/live operation ran.

## REST and client reference (2026-10-18)

- [x] DOC-012 Publish current REST and client guides (2026-10-18, this commit —
  [task](plans/tasks/doc-012-human-rest-and-client-reference.md)). Four guides now
  describe current auth, modes/effects, strict wire/config boundaries, bounded
  complete collection, immutable identity and lost-ack recovery without tracking.
  Prior bodies/hashes and descriptive anchor map retained under agents; 69 exact
  transitional entries retired. Independent parity keeps all 29 CLI modes and
  selected real evidence; registry checks cover 34 routes/39 rows/15 strict POST
  models. Focused checks 88 passed; full `scripts/check.sh`: 4173 passed/40
  deselected, build/three locked profiles and actual Cockpit lint/135 tests/build
  passed. Reviewed INV-002/005/006/016 and ADR119/120/121/123; no runtime/format/
  dependency/architectural change. No live operation; existing restrictions stay.

## MCP user guide (2026-10-18)

- [x] DOC-013 Make the MCP guide user centered (2026-10-18, this commit —
  [task](plans/tasks/doc-013-human-mcp-guide-and-tool-contract.md)). Replaced
  chronology with connection/tool/identity/rotation/limit/profile guidance;
  preserved original bodies/hashes and repaired descriptive links. Actual mounted
  registry and disposable HTTP/TLS output now check the human tables/example.
  Focused 223 passed; full `scripts/check.sh`: 4173 passed/40 deselected,
  build/three locked profiles and actual Cockpit lint/135 tests/build passed.
  INV-002/003/007/010/016, ADR124/125 reviewed: no runtime/format/dependency change.
  Whole-archive trust and nine-read-only-tool boundary preserved. No host action.

## API operating and recovery runbooks (2026-10-18)

- [x] DOC-014 Update operating and recovery procedures for the API (2026-10-18,
  this commit — [task](plans/tasks/doc-014-current-operations-and-recovery-runbooks.md)).
  Replaced historical aliases/transcripts with explicit client arrays, effects,
  uncertainty/drain and evidence-preserving workflows; original bodies/hashes
  retained and anchors repaired. Shell syntax/actual CLI parsing, maintenance/
  private-worker/reader/no-replay fixtures pass. Fixed a test fault factory's
  fixture lifetime and added restoration regression. Focused 180 plus final 50
  checks passed. Full `scripts/check.sh`: 4209 passed/40 deselected, build/three
  locked profiles and actual Cockpit lint/135 tests/build passed. AD-13/16/17,
  FS-19, TX-06/07 reviewed; editorial/test alignment, no runtime/schema/ADR change.
  Existing guards and live acceptance restrictions remain; no host operation ran.

## Deployment and Cockpit profiles (2026-10-18)

- [x] DOC-015 Align deployment and Cockpit guides with runtime profiles
  (2026-10-18, this commit — [task](plans/tasks/doc-015-deployment-runtime-and-cockpit-guide-alignment.md)).
  Rewrote selected rootless/native/reader/consumer deployment, preserved rollback/
  drain/guard rules and eight historical guide bodies/hashes. Role matrix matches
  actual helper argv; Cockpit fixed launcher/rendered client, blocked system-bus
  controls and host-local report exception are explicit. Descriptive anchors and
  dated acceptance scope repaired; 55 transitional entries retired. Focused 417
  plus final 14 passed. Full `scripts/check.sh`: 4210 passed/40 deselected,
  build/three locked profiles and actual Cockpit lint/135 tests/build passed.
  CP-01–14 and ADR121/126–129/131/132 reviewed; no runtime/schema/dependency change.
  No host action; guard/NAS-ro/locks/stores/handles/calendar restrictions unchanged.

## Technical contract consolidation (2026-10-18)

- [x] DOC-016 Consolidate living technical contracts and architectural rationale
  (2026-10-18, this commit — [task](plans/tasks/doc-016-human-architecture-config-schemas-and-adrs.md)).
  Reworked five technical contracts and 151 ADR/index records with 156 preserved
  Git-hashed sources, descriptive anchors, current normative homes and separate
  agent maintenance policy. Original decision identities/rationale remain.
  Bulk-manifest migration backup/explicit-command safeguard restored. No runtime,
  durable-format, dependency or architectural choice changed; AD-05/FS-20 existing
  generation gap remains disclosed without weakening requirements or activating
  backlog. Focused 493 passed; human link/anchor scan zero broken. Full gate:
  4210 passed/40 deselected in 477.78s, build/three locked profiles and actual
  Cockpit lint/types/135 tests/build passed. No host/NAS/manager action.

## Reader onboarding and navigation (2026-10-18)

- [x] DOC-017 Make onboarding, examples and navigation reader-first
  (2026-10-18, this commit — [task](plans/tasks/doc-017-reader-first-onboarding-and-human-navigation.md)).
  Human README/index, base-reader quickstart, concise release notes and independent
  consumer guidance replace tracking/transcripts; five originals retain Git hashes.
  No transitional human tracking matches remain. Seven copy-helper fixture tests
  cover exact identity/hash/path sets, rejected corruption/mismatch, destination
  preservation and fresh-instance retry; quickstart grammar parses without effects.
  Focused 82 and final 15 passed. Full gate 4228 passed/40 deselected in 476.18s,
  build/three locked profiles and actual Cockpit lint/types/135 tests/build passed.
  FS-12/INV-008–010/AD-05/13/21 reviewed; editorial/help/test changes only.
  No host/NAS/manager action; retained restrictions and consumer ownership unchanged.

## Documentation and interface gate (2026-10-18)

- [x] DOC-018 Enforce documentation and interface alignment
  (2026-10-18, this commit — [task](plans/tasks/doc-018-automated-docs-and-interface-alignment-gate.md)).
  Offline parser-backed audience/link/anchor/catalog gate covers 180 human docs
  and 19 helpers with no leakage baseline. Bad fixtures exercise malformed links,
  alias/escape paths, missing/duplicate helpers, formatted IDs/stages and inert
  recipes. Import/help isolation, actual REST/MCP/role facts, numeric/default/
  semantic configuration constraints and 177 source/snapshot hash pairs are tested.
  Focused 246 plus final 95 passed. Full --with-build gate: 4315 passed/40 deselected
  in 483.90s, three locked profiles, actual Cockpit lint/types/135 tests/build and
  four wheel smoke tests passed. INV-010/dependency/authority contracts reviewed;
  no runtime dependency/format/application authority change or live-host action.

## Final alignment acceptance (2026-10-18)

- [x] DOC-019 Complete documentation and script alignment audit
  (2026-10-18, this commit — [task](plans/tasks/doc-019-alignment-acceptance-and-final-disposition.md)).
  [Final ledger](reviews/2026-10-18-alignment-acceptance.md) resolves F01–F14,
  all code/artifact candidates, 19 helpers, 47 relocations and 177 source/snapshot
  records. Legacy native credential reset example renamed/described explicitly;
  unit test, stale failure-hook comment, upgrade guidance and ADR links repaired.
  Human checker: 180 docs/19 helpers, zero errors/baseline. Focused 59 passed.
  Final --with-build gate: 4315 passed/40 deselected in 485.24s, build/three locked
  profiles, actual Cockpit lint/types/135 tests/build and four wheel smoke passed.
  All twelve packages complete; plan closed and selector cleared. No runtime,
  archive format, dependency, version, pin, credential or production change.
  Feature-only normal github/forgejo pushes follow per explicit user steering;
  no tag/merge/deploy/production archive operations. Live/installed acceptance remains unrun.

## Timestral live configuration checkpoint (2026-10-19)

- [x] OPS-022 Configure Timestral models and trigger a scoped live sync
  (2026-10-19, this commit). Operational evidence is recorded in the
[task](plans/tasks/ops-022-timestral-model-sync.md) and
[plan](plans/2026-10-19-plan-timestral-model-sync.md). Root preserves the original configuration flock, exact protected
predecessor and SELinux metadata, then atomically appends only four enabled
Timestral model entries with `revision = "main"` and empty dependencies.
Installed policy grows from 156 to 160 enabled repositories; every unrelated
parsed field and the original byte prefix remain unchanged. Compatible candidate
validation and four-model planning succeed; total expected Hub bytes are
1,459,902,655. Installed API validation exits 0 at `13:46:09 UTC` and confirms
fingerprint `4c33dc7bb7a5f5573d8ae1e9b4a3e20eaac3b3a0759e30747c406ade655c7b8c`.
Protected backup is `/etc/hfcache/config.toml.before-timestral-20261019` and full
local JSON evidence is `/opt/hfcache/deployment/20261019-timestral/`.

Exactly one four-model sync is durably admitted at `13:46:11 UTC`, operation
`0cb77c1c970e21033a9cab7fb8ea872d`, key
`timestral-sync-20261019-410f6659ff9b48379249e7a167a36400`. Show/lookup at
`13:46:39/41 UTC` report `waiting_lock`, no domain run/result. The custom root
orchestrator incorrectly expected a terminal Envelope after valid detached
admission; saved 202/handles resolve the uncertainty through observation only,
without a second POST. Initial wrong-identity/private-cwd client refusals are
also retained. The original guard PID `809950`/archive inode `27:2273`, NAS-ro,
writer/timer masks, lock identities, receipt stores and installed release `0.2.1`
remain; no restart, guard release, writable remount, hardening/secret/schedule
change or archive write occurs. Admission proves a trigger, not publication.
NAS-shadowed `scripts/check.sh` exits 0 in `hfcache-ops022-gate`; protected process
mount evidence confirms an empty read-only tmpfs over `/srv/hfcache`.
Formatting/lint/types/docs alignment pass; 4,315 Python tests pass/40 opt-in
deselected in 495.19 seconds, distribution build and all three locked installation
profiles pass, as do actual Cockpit lint/style/types/135 tests/production build.
Task retains the exact command, invocation and protected log SHA-256. Final
`13:56:31/34 UTC` validation/lookup confirms the same 160-entry fingerprint and
guard-held `waiting_lock`, no domain run/result. Invariant/ADR review finds no
behavior/architecture change. Plan is complete and selector inactive; trigger
completion does not claim download or publication.
Independent read-only review confirms exact policy/metadata preservation,
unchanged four lock identities and NAS-ro, actual guard flock ownership, and
exactly one new sync receipt without removal.

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
- [x] STO-001 NFS mount and filesystem-type detection (2026-07-25, this commit — the detection itself landed at `STO-000` (decision 28); this is the shared preflight built on it. `src/hfcache/storage.py`: the `.store/health/probe-<probe-id>` create/fsync/rename/delete probe (`HFMNT008`, plan §19 items 6 and 10) which removes every artifact it made including after a failure, and the staging/destination same-filesystem proof (`HFMNT009`, `FS-04`). `src/hfcache/preflight.py` (new, decision 33): the ordered check runner `doctor` and every mutating command share, plus `require_storage_safety`, the hard gate that raises with every problem at once. `doctor` now emits `docs/cli.md` §2 rows 2–5, 7, and 8 in table order with `credential` and `hub_endpoint` at 13 and 14, skips the probe under `--read-only`, and exits `20` when any check failed. `storage.py` and `preflight.py` both at 100% branch coverage; `tests/system/test_live_mount.py` proves rows 2–5 against the live `/srv/hfcache` mount read-only, `-m nfs`)
- [x] STO-002 Sentinel/archive-ID validation (2026-07-25, this commit — `src/hfcache/archive.py` split out of `storage.py` first, per the `STO-001` sizing note and decision 36; `storage.read_sentinel` is now shared by both. `doctor` check 6 `sentinel` reports `HFMNT005` when the archive is not initialized, `HFMNT006` when the sentinel is unreadable, malformed, or from a newer release, and `HFMNT007` when it names a different archive (`FS-03`). The check owns the "not initialized" condition for the gate, so checks 7 and 8 skip on it without reporting it again — one missing archive is one problem. `storage_checks` and `require_storage_safety` now take the configured `archive_id`. `archive.py`, `preflight.py`, and `storage.py` all at 100% branch coverage)
- [x] STO-003 Free-space and reserve calculations (2026-07-25, this commit — `storage.describe_capacity` measures the filesystem through `statvfs`, which reports the ZFS quota as the size when one is set and so answers `docs/configuration.md` §4's "quota, or capacity" without the writer knowing which case it is in; `effective_reserve` is whichever configured minimum binds harder; `capacity_problems` is `HFMNT011` against the need *plus* the reserve (plan §19 item 9) and `capacity_warnings` is `HFWRN005` at a tenth of the reserve (decision 38). `doctor` check 12 `free_space` runs against any proven mount rather than only an initialized archive (decision 39), and the warning reaches the envelope's `warnings` array with the exit code still `0`. `storage_checks` and `require_storage_safety` now take the whole `[storage]` table plus this run's `needed_bytes`. 100% branch coverage)
- [x] STO-004 Local exclusive locking (2026-07-25, this commit — `src/hfcache/locking.py` (new, decision 40): `flock(2)` on `/run/hfcache/hfcache.lock`, so the kernel releases it when the process dies and a crashed sync never leaves a lock an operator has to clear. `HFMNT010` on timeout, naming the holder from a diagnostic record the holder writes into the file. `preflight.guarded` composes the lock and the checks in plan §13.1's order — lock at step 2, preflight at step 3 — and is the single entry point every mutating command will use. 100% branch coverage; contention is exercised in-process, since `flock` conflicts between open file descriptions rather than between processes)
- [x] STO-005 Atomic JSON and ref writes (2026-07-25, this commit — `storage.write_model` and `storage.read_model`: model-aware durable JSON on top of `atomic_write_bytes` and `models.load`, each taking the caller's code so a failed manifest write is `HFSYN008` and a failed reference write `HFSYN007`. `src/hfcache/publication.py` (plan §7, no deviation) holds the reference writers: `publish_revision_reference` (`FS-11`) and `publish_current_reference` (`FS-08`), both enforcing `FS-10` at the point of the write — a reference whose tree or manifest is not durable is refused, with every missing target reported at once. `read_reference` reports `HFVER008`, because reading one happens while something is being checked. 100% branch coverage. **Still to come at `STO-007`:** the hardlink and copy publication primitives that create the tree a reference names)
- [x] STO-006 Staging creation and containment (2026-07-25, this commit — added to `publication.py`, which now has two halves: building a tree and naming it. `create_staging` makes `.store/staging/<transaction-id>/tree` exclusively — a colliding id fails rather than building into another transaction's area — with the `tree/` at the *published* mode, since publication is a rename and a rename does not change a mode. `discard_staging` is the module's one deletion and stays inside `FS-19` because the path is derived from a validated transaction id rather than read off the filesystem (`FS-18`). `source_problems` is `FS-15`: symlinks are resolved rather than refused, because the Hub cache reaches every file through one, and what is rejected is a link that escapes the approved cache root, dangles, or lands on something that is not a regular file (`HFSYN004`). `staged_path` joins a repository-relative path only after the grammar has proven it cannot escape (T-02). 100% branch coverage)
- [x] STO-007 Hardlink and copy publication primitives (2026-07-25, this commit — `src/hfcache/hashing.py` (plan §7): `sha256_file` streams a file and returns digest *and* size from one read, so the two can never describe different content. `publication.stage_file` proves the source contained (`FS-15`) then links or copies per `publication_mode`, never downgrading a mode automatically (`AD-11`); copy mode verifies the copy against a fresh hash of the source, because a copy that lost bytes would otherwise be published as the revision. `promote_staging` is plan §13.2 step 15, and refuses an existing destination *explicitly* rather than relying on `rename(2)` — which fails on a non-empty directory but replaces an empty one, so the syscall alone would break `FS-05` for an instance directory a crash left empty. `storage` gained the three §14.2 capability probes and `doctor` checks 9-11 (`HFMNT012`, `HFMNT013`), with `publication_mode = "copy"` reporting the hardlink check as not exercised rather than failed (decision 41). 100% branch coverage)
- [x] STO-008 Storage reconciliation and stale-staging reporting (2026-07-25, this commit — `src/hfcache/recovery.py` (plan §7): `reconcile_storage` scans the four transaction areas and reports what they hold without touching any of it. `HFWRN004` for staging past `sync.stale_staging_age_hours`, `HFWRN002` for a prune tombstone whose physical removal is outstanding, `HFWRN003` for an entry whose name is not a 32-hex transaction id — preserved, whatever it is (`FS-19`). Quarantine is reported and never warned about, because plan §16.5 retains it until an operator approves cleanup, so age says nothing about it. `measure_health` adds free space against the reserve, and `status` now emits the archive health block `docs/cli.md` §2 describes, with warnings on stderr and the exit code still `0`. 100% branch coverage. **Reclamation is deliberately absent:** plan §13.3 and `FS-18` allow it only for a directory that also *has a journal*, which arrives at `STO-010`, so `STO-011` is where removing one belongs)
- [x] STO-009 Complete mutating `doctor` tests (2026-07-25, this commit — the checks themselves landed at `STO-001`, `STO-002`, `STO-003`, and `STO-007`, each with its own unit coverage against a temporary archive and a fabricated mount table. What this package adds is `tests/system/test_live_mount.py`'s mutating half: sentinel, effective writability, and all three §14.2 publication capabilities asserted against the real NFS dataset, plus the probe area left empty. They are written now and **skip until the archive is initialized**, which is the §29 rollout checkpoint after `HOST-004` — so the checkpoint runs a test that already exists rather than one written to fit whatever it found. Run with `pytest -m nfs`)
- [x] STO-010 Durable transaction journals and validated checkpoint evidence (2026-07-25, this commit — `src/hfcache/transactions.py` (plan §7): `open_transaction` writes the journal durably before the first mutation (`TX-01`); `Transaction.checkpoint` appends after the act it names (`TX-02`) and refuses a name that is not next in the operation's documented sequence (`HFTXN002`). `CHECKPOINTS` holds the §7.3-§7.6 sequences and `tests/unit/test_transactions.py` parses them back out of `docs/architecture.md`, so neither table is written twice. `evidence_problems` confirms path evidence against the filesystem (`TX-03`, `HFTXN003`) under the key convention in decision 42. `read_journal` preserves keys this release does not know, which is the half of `docs/schemas.md` §1.1 that decision 20 assigned here. `open_journals` is what `TX-07` reconciles, and treats `needs_operator` as unresolved because it is exactly what must stop the next run. 100% branch coverage)
- [x] STO-011 Dry-run and apply recovery planning (2026-07-25, this commit — `recovery.plan_recovery` validates every open journal (schema, then checkpoint order, then evidence) and proposes one of four remedies; `apply_recovery` performs only a plan with nothing blocked, records one checkpoint per remediation in a §7.7 recovery journal, and writes the durable report now documented as `docs/schemas.md` §12 (decision 43). The `recover` command takes `--dry-run` or `--apply`, and `--apply` takes the lock and runs the §19 preflight because it is a mutating command. Idempotent by construction: each remedy closes the journal it resolved, so a second run finds nothing. 100% branch coverage. **The remedies for states this codebase cannot yet produce are reported as blocked rather than guessed at** — rolling a publication forward from checkpoint 5 needs `HUB-009`'s manifests, a prune needs `RET-006`, a repair needs `VER-006`; each package adds its own remedy as it lands, the way `doctor`'s checks did)

**Phase 3 complete.** Unsafe storage mutation is now structurally hard rather
than merely avoided: the mount is proven before anything is written, the sentinel
is the archive's identity, effective writability and all three publication
capabilities are demonstrated rather than assumed, one exclusive lock serializes
every mutating command, every durable write is a rename, every mutation is
bounded by a journal checkpoint carrying re-observable evidence, and nothing the
application did not create is ever removed. `scripts/check.sh` passes with 977
tests; every Phase 3 module is at 100% branch coverage.

New modules beyond the plan's §7 list, each with a recorded decision:
`preflight.py` (33), `archive.py` (36), `locking.py` (40).

## Phase 4 — Hub Resolution and Repository Ingestion

- [x] HUB-001 Typed Hub client adapter (2026-07-25, this commit — `src/hfcache/hub.py` (plan §7): the only place `huggingface_hub` is called and the only place its exceptions are caught. `HubApi` is a `Protocol`, so a test supplies an object with those methods and no library machinery — plan §12's "deterministic fakes without mocking library internals" implemented as a seam this application defines. Every call passes `token=` explicitly and never `None` (`docs/security.md` T-07); `RepositoryFacts`/`TreeEntry`/`HubIdentity` are types this application owns, so a response-shape change breaks here rather than near the archive; `hub_problem` maps the library's hierarchy onto `HFHUB001`/`004`/`005`/`006`/`007`/`010`; private and gated repositories are refused before anything is fetched. 100% branch coverage, with the library's real exception types constructed rather than approximated)
- [x] HUB-002 Optional identity verification (2026-07-25, this commit — `hub.resolve_host`, `hub.verify_tls`, and `hub.identity_problems`, wired into `preflight.hub_checks` as `doctor` rows 15-17. DNS and TLS are separate checks because they fail for unrelated reasons and are fixed in different places; each depends on the one before, so a host that does not resolve skips the rest rather than reporting three failures for one cause. `hub_identity` is *skipped* when `hub.expected_account` is unset — nothing was verified, and an anonymous archive of public content is a normal deployment — and `HFHUB003` when the Hub names a different account, which catches a credential swapped by mistake before a scheduled run uses it. All three read only, so `--read-only` runs them. `verify_tls` takes an injectable context so `tests/unit/conftest.py` can prove it against a real local TLS server with its own CA: the trust anchor is injected, never the answer, so the code under test is still verifying. `tests/system/test_live_hub.py` (marker `live`) exercises the adapter against the real Hub; the unit suite never touches the network. 100% branch coverage)
- [x] HUB-003 Resolve branch/tag to full SHA (2026-07-25, this commit — `HubClient.repository` performs the resolution and refuses anything but a full 40-character lowercase SHA (`HFHUB007`), since every path, manifest, and reference is keyed by it and an abbreviation never reaches disk. `plan` now resolves each enabled repository and reports `resolved_commit_sha` and `upstream_state`; one repository failing does not abandon the rest, and the run exits `30` if any did. `upstream_state` describes what is true of the *repository* — `missing`, `forbidden`, `refused`, `unresolvable`, `unreachable` — rather than which call reported it. **Still to come at `HUB-004`:** `plan`'s logical size, estimated new bytes, and projected copy-mode publication bytes)
- [x] HUB-004 Repository tree and dry-run size (2026-07-26, this commit — `HubClient.tree` lists the revision recursively against the *resolved SHA*, draining the generator inside the `try` because `list_repo_tree` makes its request during iteration; a file entry with no path is `HFHUB008`, since the listing is the exact path set every later step joins onto a filesystem path. `HubClient.estimate` is plan §13.2 step 3's dry run, against the same private cache a real download writes to and with no allow/ignore filters — and it creates nothing, not even the cache directory, which is proven live so `plan` is safe against an uninitialized archive. `publication.projected_publication_bytes` states the `AD-11` cost model once, so the estimate an operator reads and the reserve a sync will enforce cannot disagree. `plan` now reports `file_count`, `logical_bytes`, `estimated_new_bytes`, `projected_publication_bytes`, and `publication_mode`; a failure at any of the three Hub reads leaves the fields below it `null` rather than guessed. `hub.py` and `publication.py` at 100% branch coverage; `tests/system/test_live_hub.py` proves the tree and the dry run against the real Hub, including that the two agree about the revision's size. **Still to come at `HUB-009`:** `plan`'s retained/current state, which needs the references that package writes)
- [x] HUB-005 Complete `snapshot_download` (2026-07-26, this commit — `HubClient.download` performs plan §13.2 step 5 with every argument plan §12 item 4 requires be explicit: repository id and type, the resolved full SHA rather than the reference that produced it, the cache path, the configured worker count, and the token; no allow or ignore filters exist as arguments, because there is no supported way to archive part of a repository. Resumption is the library's — the canonical download store is the native Hub cache on NFS (`AD-09`), so an interrupted run costs the bytes it had not yet fetched. The `HubApi` protocol is now overloaded on `dry_run` exactly as the library is, so `estimate` and `download` are each typed for the answer they get. `_snapshot_path` refuses a returned path that is missing, unresolvable, outside the cache root, or not a directory — all `HFHUB009`, because to an operator they mean one thing: no usable snapshot. Containment is proven rather than assumed even though the value came from a library and not from a repository (`FS-15`). 100% branch coverage; `tests/system/test_live_hub.py` downloads both test repositories in full and asserts every tree path landed at its stated size, then proves a second dry run reports zero new bytes — plan §26.3's "download every file" and "no unnecessary download" at the adapter level)
- [x] HUB-006 Local-only completeness verification (2026-07-26, this commit — two independent checks, because either alone is insufficient. `HubClient.verify_local` is plan §12 item 5: the same call the download made with `local_files_only=True`, so the library assembles the revision from the cache with the network taken away and reports `HFSYN001` when it cannot. That check is not one this application could write for itself without doing what plan §12 item 7 forbids — parsing the cache's private layout. `src/hfcache/sync.py` (plan §7, no deviation) is the other half: `completeness_problems` compares what landed against the Hub tree independently, reporting missing *and* extra paths as `HFSYN002`, size disagreements as `HFSYN003`, and unsafe sources as `HFSYN004` through the same `source_problems` publication itself uses (`FS-15`). Upstream metadata is treated as a claim and local bytes as the evidence: a size mismatch stops the revision without deciding which side is wrong, since the manifest records what was read (`AD-18`). Path grammar and `T-02` collision folding run here too, so a name that could escape or that would merge with another on a consumer filesystem is refused before it is joined onto anything. **A defect the tests found:** `Path.exists()` and `Path.is_dir()` follow symlinks, so a dangling link in the snapshot looked absent to one check and present to the other and passed completeness with nothing behind it — both now use `follow_symlinks=False`, and the case is pinned by its own test. `hub.py` and `sync.py` at 100% branch coverage; the live suite proves both checks against real downloads of both test repositories, that the local check works with `HF_HUB_OFFLINE=1`, and that deleting one blob fails it)
- [x] HUB-007 Hash new unique content (2026-07-26, this commit — `sync.hash_snapshot` reads every newly introduced unique *physical object* once, streaming in bounded chunks through `hashing.sha256_file`. `ObjectIdentity` is `(st_dev, st_ino)` read during this run and nothing else, because plan §16.1 rules out every other candidate — cache path, prior-run inode, mtime, Git SHA-1, Xet identifier — for the same reason: each can be equal for objects that differ. Two kinds of reuse and the difference between them is the whole of §16.1: *within* a run two paths on one inode are hashed once and both still record `hashed = true`, since the bytes were read; *across* runs a digest is reused only when the inode **and** the size both match a retained publication, and that entry records `hashed = false` naming its source, so no manifest can hold a digest whose origin does not trace back to bytes this archive read. `sync.published_digests` builds that index — manifest for the digest, filesystem for the identity, neither sufficient alone. 100% branch coverage. Two corrections landed with it, decisions 46 and 47)
- [x] HUB-008 Durable manifest generation (2026-07-26, this commit — `sync.build_manifest` assembles the §10.1 field set and is deliberately thin: `RevisionManifest` already enforces `file_count` against `len(files)`, `total_bytes` against the sum, `reused_digests` against the unhashed entries, byte-wise path ordering, collision folding, and the timeline's order, so the builder arranges inputs and does not decide whether they are consistent. Every number comes from what was read; `TreeEntry` gained `git_oid`, `lfs_sha256`, and `xet_hash` off the real listing and they are recorded beside the digest, never as it (`AD-18`). `Timeline` is passed rather than stamped, because the moments it names happened in the caller and stamping them here would record when the manifest was assembled. `reporting.RuntimeVersions.measured()` is new and now the single reader of the three version fields a manifest and a run report both carry — `cli.py` was measuring them separately. Nothing is written: plan §13.2 steps 12 and 16 belong to the transaction that owns the filesystem, which is `HUB-009`. 100% branch coverage; the live suite runs the whole sequence against the real dataset repository — resolve, list, download, check, hash, describe — and round-trips the manifest through its durable form)
- [x] HUB-009 Publish revision instance; atomic per-SHA and current refs (2026-07-26, this commit — `sync.publish_revision` performs §7.3 checkpoints 4-9, each act followed by the checkpoint that names it; `Transaction.checkpoint` refuses a name that is not next, so a journal this function produced can only describe an execution that really happened. Every adjacency in the order is load-bearing and the docstring says which: the manifest is written into *staging* before the rename (`StagingPaths.manifest` is a sibling of `tree/`, so it does not travel with it) which is what makes a crash between checkpoints 5 and 6 recoverable; the tree is renamed before the manifest is published; both are durable before the per-SHA reference and that before `current.json`, a single rename so the previous current revision is usable on either side of it (`FS-10`, `FS-12`). The staging loop is driven by `manifest.files`, so the published tree cannot contain a path its own manifest does not list — by construction rather than by agreement between three collections. `publication.py` gained the derived view: `published_repositories` (read off disk, not configuration, because `AD-06` keeps an unconfigured repository's data), `retained_references`, `next_generation` (`max + 1`, never `count + 1` — a prune would make counting reissue a generation), `rebuild_catalog`, and `publish_catalog`. `identity.TYPE_DIRECTORIES` is public now, since discovery needs the same two names. Both modules at 100% branch coverage; `tests/unit/test_publish_revision.py` publishes through the real code path rather than fabricating output, and the live suite archives both test repositories end to end on a throwaway archive — every Hub path present at its stated size and sharing an inode with its cache blob, references resolving, manifest describing exactly the published tree. **`/srv/hfcache` is deliberately untouched:** the §36.4 one-time authorization is spent at the rollout checkpoint, not by a test)

**Phase 4 complete.** One public model and one public dataset can be archived:
resolved to an immutable SHA, enumerated, costed, downloaded, checked for
completeness two independent ways, hashed object-by-object, described by an
immutable manifest, and published as a hardlink tree behind two atomic
references — every step bounded by a §7.3 checkpoint carrying re-observable
evidence. `scripts/check.sh` passes with 1160 tests; `-m live` runs 24 against
the real Hub, including the full end-to-end publication of both test
repositories. Every Phase 4 module is at 100% branch coverage.

`sync.py` was added from plan §7's list, no deviation. Decisions 44-47 record
this phase's four settled interpretations.

## Phase 5 — Multi-repository Sync and Retention

- [x] SYNC-001 Deterministic multi-repository orchestration (2026-07-26, this commit — `sync.synchronize_repository` runs plan §13.2 end to end for one repository and `sync.synchronize` runs §13.1 steps 5-11 over a selection, in *configuration* order rather than selector or alphabetical order, because two runs naming the same repositories have to do the same things in the same sequence for a partial run's journals to be interpretable. The `sync` command holds `preflight.guarded` — lock then §19 checks — for the whole run rather than per repository: proving the archive sound and then letting another command mutate it throughout would prove nothing. `preflight.require_capacity` is new, because §13.1's whole-run preflight runs before any repository is resolved and so knows a need of zero; the per-repository gate is the same measurement taken immediately before the download it guards, so the repository that would have overflowed is the one that reports it. A disabled repository is reported rather than omitted, and a SHA the archive already retains is `skipped` or `ref_moved_to_retained_revision` — the two look alike from outside and mean different things. **Continuation landed here rather than at `SYNC-002`:** a loop that cannot record a failure cannot be tested at all, so `continue_on_repository_error` and per-repository failure recording are in this commit; `SYNC-002` takes the aggregate reporting that sits on top of them. 100% branch coverage on `sync.py`; `tests/unit/test_synchronize.py` drives whole runs through a `HubApi` fake whose cache is real — blobs reached through symlinks — so the inode sharing publication depends on is exercised rather than approximated)
- [x] SYNC-002 Continuation and aggregate failure reporting (2026-07-26, this commit — the aggregate a run produces, and the two commands that read it afterwards. `taxonomy.aggregate_exit_code` now decides the run's single exit from every code encountered, in `docs/cli.md` §3's operator-urgency order, while the durable report and the `--json` envelope both list all of them — aggregation decides which number a scheduler sees and hides nothing. The envelope's `errors` and `warnings` arrays are rebuilt from the durable report rather than collected alongside it, so the two cannot describe different runs, and each entry names the repository it belongs to. `status` now reports per-repository retained count, retained generations, current SHA and generation, and last-run status, read from the *references* and the newest run report rather than from the catalog — `status` is what an operator runs when something is already wrong, and the catalog is derived (`FS-16`). It tolerates damage in both: an unreadable reference costs that repository's current-revision fields and an unreadable run report costs one field, neither costs the command. **`hfcache list` is implemented here** (decision 48). 100% branch coverage on `sync.py`; `cli.py` at 99%, the one gap still the unreachable `hf_xet` fallback)
- [x] RET-001 Immutable publication-generation retention ordering (2026-07-26, this commit — `src/hfcache/retention.py` (plan §7): `ordered_revisions` reads the retained set from `refs/revisions/<sha>.json` and sorts by `publication_generation` ascending, and the module docstring records why every alternative key was rejected — wall-clock time reorders under repair, upstream commit time reorders under a force-push or a branch reset, directory mtime reorders under a backup, and a SHA has no order at all. The references rather than the revision directories, because a directory can hold a superseded repair instance inside its grace period and that instance is not retained. Gaps mean nothing and collisions are impossible (`FS-20`). 100% branch coverage, with the ordering asserted as a Hypothesis property over arbitrary generation sets rather than only over examples)
- [x] RET-002 Five-revision selection (2026-07-26, this commit — `prune_candidate` is plan §15.2 step 3, and returns `None` in three cases that are all correct behaviour rather than limitations: at or below the limit including exactly five, since a prune is triggered by a successful publication *beyond* the maximum (`AD-04`) and never by a count; when the oldest revision is the current one, which is reachable when upstream moves back to a repository's earliest retained SHA and where over-retention is the right answer; and when nothing is retained. `selection_problems`/`require_valid_selection` refuse a selection before a plan is built, so a caller gets a coded `HFRET001` naming the policy rather than a validation error naming a field — `PrunePlan` enforces the same rules on a recorded plan, and the duplication is deliberate because the cost of being wrong is deleting the wrong revision. Two Hypothesis properties pin the invariants no failure may break: a selection is never the current revision, and is always the lowest generation)
- [x] RET-003 Dry-run prune plans (2026-07-26, this commit — `retention.plan_prune` is plan §15.2 steps 1-4, built from the same reads the prune performs, so a plan an operator reviewed is the plan that runs. Non-mutating by construction: the plan is a value, and persisting it is checkpoint 1 of the transaction, because a plan that was written down is a commitment and reading one should not be. `unique_bytes_released_estimate` is named an estimate and is the tree's logical size, which is an upper bound — blobs shared with retained revisions release nothing and ZFS snapshots may hold the rest for weeks (§15.3); reporting the bound is honest where a computed figure would imply precision the storage layer does not offer. `prune --dry-run` / `--apply` implemented, with `--apply` planning *inside* the lock because a plan made before it could be stale by the time it ran)
- [x] RET-004 Published-view and manifest cleanup (2026-07-26, this commit — see `RET-006`; the tombstone rename of the tree and the manifest, the catalog republication, and the `audit/pruned/` records are checkpoints 3-6 and 8 of one transaction and are not separable from it. The original manifest is copied byte for byte rather than re-serialized from a parsed model: it is the evidence of what was there, and this release's rendering of it is not the bytes the archive published (`FS-06`))
- [x] RET-005 Supported Hub cache revision deletion (2026-07-26, this commit — `hub.delete_cache_revision` goes through `scan_cache_dir(...).delete_revisions(...).execute()` and never removes a blob by path (`FS-14`, plan §12 item 7). This application does not know which blobs a revision uniquely owns — that is the library's bookkeeping and a revision's blobs are routinely shared with revisions that are staying. It runs at checkpoint 2, while all six revisions are still published, so the hardlinks hold the bytes whatever the cache does; a failure is `HFRET002` and the revision is preserved)
- [x] RET-006 Prune journals, tombstone rename, reconciliation after partial failure (2026-07-26, this commit — `retention.apply_prune` performs all ten §7.4 checkpoints. **Checkpoint 7 is the commit point** and divides the transaction into two opposite failure regimes: before it a failure leaves six revisions published, because over-retention is always preferable to a revision that should not have gone; at or after it nothing is ever republished, because five revisions are what consumers see and re-adding the sixth would contradict a decision the archive recorded. The per-SHA reference is removed *before* the tree is tombstoned (decision 4), so no reference ever names a tree that has been renamed away. Retention runs from `sync` after the publication transaction has committed, never inside it, so a prune failure is its own failure with its own journal and can never take the revision just published down with it. **A bug the tests found:** the `prune --apply` path passed `_run_envelope(config)` to `apply_prune`, which reads `envelope["run_id"]` — a key that envelope does not carry, so the command would have raised `KeyError` the first time it had real work to do. The deferred-prune test is what exercised it)
- [x] RET-007 Protect unmanaged and upstream-missing repositories (2026-07-26, this commit — the guarantee is structural rather than a check: a prune is reachable only from a *successful publication* of that repository (`AD-04`), so a repository nothing is publishing to cannot reach one. A repository removed from configuration is not processed, keeps every revision and its current reference, and reads as `managed = false` with `enabled = null` in the catalog; a disabled one is reported and left alone; a 403, a 404, and an unreachable endpoint all end the repository without touching a byte of it (`AD-06`). Asserted rather than assumed — the tests remove a repository from configuration, disable one, and fail one upstream three ways, each time comparing the retained set and the current reference before and after. **A gap the tests found:** the catalog was rebuilt only inside `publish_revision`, so a run that published nothing left it stale, and a repository removed from configuration kept reading as managed until something else happened to publish. Plan §13.1 step 10 is a *whole-run* step distinct from §7.3 checkpoint 9, and `synchronize` now performs it)

**Phase 5 complete.** Unattended rolling synchronization works end to end: a
run takes one lock, proves the §19 requirements once, processes repositories in
configuration order, continues past a failure when configured to, rotates the
oldest revision out when a sixth is published, and records everything in a
durable run report an operator reads back through `status` and `list`. Five
revisions accumulate unchanged; a sixth prunes exactly one; a failed prune
prunes nothing and leaves six. `scripts/check.sh` passes with 1257 tests; every
Phase 5 module is at 100% branch coverage.

`retention.py` was added from plan §7's list, no deviation. Decision 48 records
where `hfcache list` landed.

## Phase 6 — Dependency Warnings and Archive Verification

**Carried into this phase — both now closed.**

1. **Recovery's roll-forward remedies were `blocked`.** `STO-011` deferred them
   explicitly and neither `HUB-009` nor `RET-006` added them. **Closed at
   `VER-006`**: all four `docs/architecture.md` §7.3 crash-matrix rows from
   "after 5, before 6" onward now resolve as `complete_publication` (or
   `quarantine_tree` for the row's own "if the staged manifest is gone"
   caveat), §7.4's two regimes as `rollback_prune` and `complete_prune`, and
   §7.5's crash between the two reference switches as `complete_repair`.
   Decision 53 records the evidence-convention defect that had to be fixed
   first — the journals were contradicting the filesystem by design in exactly
   those states.

2. **`verification_state` was hardcoded `"verified"` in three places.**
   **Closed at `VER-005`**, decision 51: it comes from
   `catalog/verification.json` through the single reader
   `publication.VerificationStates`, a revision nothing has re-read offline is
   `unverified`, and `failed` is reachable for the first time.

**Carried out of this phase — now closed.** One item was open that this phase
found and did not close, recorded here rather than left to be rediscovered:

1. **`TX-07` reconciliation is not implemented in `sync`.** `docs/architecture.md`
   §7.6 gives the sync run its own journal with seven checkpoints, the third of
   which is `journals_reconciled`, and `TX-07` requires *every* mutating command
   reconcile unfinished journals before contacting the Hub. `sync` opens no run
   journal and calls no reconciliation; `SYNC-001` and `SYNC-002` completed
   without it and `transactions.CHECKPOINTS["sync"]` has held the sequence since
   `STO-010` with nothing producing it. Nothing is unsafe today — `recover
   --dry-run` and `--apply` reconcile on demand, and a repair's deferred cleanup
   is surfaced by `HFWRN008` in `status` — but a scheduled run does not stop on
   a `needs_operator` journal the way §7.9 says it should. It belongs with the
   systemd work in Phase 7, where the scheduled invocation is what makes it
   matter. **Closed at `SYNC-003`** (Phase 7), which also extends the rule to
   `prune --apply` and `repair`, the other two mutating commands that never had
   it. Decision 55 records the one behaviour that had to change to get there: a
   crashed run journal now closes rather than stopping the machine.

- [x] DEP-001 Model-card dependency inspection (2026-07-26, this commit — `src/hfcache/dependencies.py` (plan §7) reads `README.md`'s YAML front matter through `huggingface_hub.repocard.metadata_load`, which parses with `yaml.safe_load`: no object construction, no tag that could reach a constructor (`AD-15`, T-04). A `base_model` holding a list produces one observation per entry, because a merged model legitimately names several parents. Detection reads the *snapshot*, so it sees the same bytes that were hashed and will be published — a detector reading anything else could report a dependency the archived revision does not declare)
- [x] DEP-002 Adapter-config dependency inspection (2026-07-26, this commit — `adapter_config.json` through `json.loads` and nothing else; PEFT would import it through its own loader, and reading it as the JSON document it is, is the whole difference between describing an adapter and running one. `base_model_name_or_path` is recorded at `high` confidence, above a card's `base_model`, because an adapter without its base cannot be loaded at all rather than merely being incomplete)
- [x] DEP-003 Compare observations with declared dependencies (2026-07-26, this commit — `declared` and `managed` are separate questions and the manifest records both: declared-but-unmanaged is an operator who knows and decided not to archive it, managed-but-undeclared is a stale declaration. Comparison is case-folded, because the Hub treats `Org/Model` and `org/model` as one repository while a `declared_dependencies` entry is typed by hand, and reporting a case difference as undeclared would train an operator to ignore the code. `managed` is matched on bare repository ids rather than selectors, since a `base_model` value carries no type prefix)
- [x] DEP-004 Persist and display non-fatal warnings (2026-07-26, this commit — an undeclared dependency emits `HFDEP001` once however many observations carry it (the code names the condition, not the instance), is written into the immutable manifest's `dependencies` array along with the declared ones, marks the repository `completed_with_warnings`, reaches the run report and the `--json` envelope, and leaves the exit code at `0`. It never triggers a download (`NG-05`): a detector that fetched what it found would turn one configured repository into an unbounded transitive closure. Unparseable metadata is recorded at `low` confidence rather than guessed at — 'this file did not parse' is a finding an operator can check. 100% branch coverage; the tests feed the detector a YAML tag naming a Python callable and assert the result is an observation rather than an effect)
- [x] VER-001 `verify --new` (2026-07-26, this commit — `src/hfcache/verification.py` (plan §7) and the `verify` command. The module has no write path at all, which is how plan §16.1's last line is enforced rather than remembered: a finding is a value, so a mismatch structurally cannot rewrite a manifest, prune a revision, or re-download over the evidence. Every artifact it reads can fail and none of those failures escape — an unparseable reference, a manifest that will not load, a manifest filed under the wrong SHA, and a tree that is not there are each a finding attributed to the revision they belong to, and the run continues to the next one, because `verify` is what an operator reaches for when the archive is *already* known to be wrong (§7.9). `ReadSet` is plan §16.2 item 4: keyed by `sync.ObjectIdentity` and confirmed with `samefile` rather than trusted, since an inode number is reused after deletion; sharing is decided per *file* from the manifest's own `publication_mode`, because a hardlink-mode and a copy-mode tree can both be retained and each has to be read the way its bytes are laid out. `--new` resolves through the archive's current references rather than the publication ids the run recorded, so a revision a later prune rotated out is not verified and one a later repair replaced is verified in its replacement. Exit `0` clean, `40` on any finding, with the envelope's `errors` grouped by `(kind, repository)` — the complete set is in `data`, and an array with one entry per finding is not something an operator reads. 100% branch coverage. **A correction landed with it:** `emit_envelope` minted a fresh run id for every command, so `sync`'s envelope and its durable report named different runs, which is precisely what `docs/cli.md` §4 says that field is for; both now pass the report's id. Decision 49 records the two contract amendments. **Still to come:** `--full` at `VER-002`, `--revision` at `VER-003`, `--estimate` at `VER-004`, and the durable report and catalog update at `VER-005` — this package builds the `VerificationReport` and emits it, and does not yet write it to `runs/`)
- [x] VER-002 Unique-object full verification (2026-07-26, this commit — `verify --full` over `verification.resolve_archive`, which reads the repository set off `published/repos/` rather than off configuration: removing a repository from configuration never deletes its archive (`AD-06`), so a quarterly job that skipped unmanaged repositories would leave exactly the content nothing else touches unchecked. The lock is `preflight.guarded` with `verification.lock_wait_seconds`, which is the *global* lock rather than a second one (§22.3) — that is what makes `--full` mutually exclusive with sync, prune, and repair, and it is taken before the §19 gate for the same reason every mutating command takes it first. `hub.networking_disabled` sets `HF_HUB_OFFLINE` for the duration and restores the previous value rather than clearing it, since a deployment may legitimately run offline; the real guarantee is structural, though, and is asserted as such — `verify` builds no `HubClient` and resolves no credential, and a test replaces `HubClient` with one that raises to prove it. Read-once is now demonstrated at archive scale: two revisions sharing hardlinked blobs report one read per object, and the same pair published in copy mode reports two. 100% branch coverage on `verification.py` and `hub.py`)
- [x] VER-003 Revision-scoped verification (2026-07-26, this commit — `verify --revision TYPE:ID@SHA`, the mode an operator uses after a `--full` reported a finding and again after a `repair` claims to have fixed it. The SHA is *required* rather than defaulted to the current revision: defaulting would answer a question nobody asked and would report clean while the suspect revision sat unexamined (`HFARG001` when the selector carries none). The repository need not be in configuration, because an unmanaged repository's data is still the archive's (`AD-06`) and a revision under investigation is often one whose repository was removed — so `--revision` deliberately does not go through `_select`. A SHA the archive does not retain is `HFARG004` at exit `10` rather than a finding at exit `40`, since telling a scheduler the archive is corrupt because somebody typed one wrong character is the worse failure; `verification.require_retained` owns that distinction and still returns a *damaged* revision as findings, because the operator asked about that SHA and it is there. `_mode_option` names the mode in the envelope's `command` even for an invocation that was itself the thing refused)
- [x] VER-004 Verification estimation (2026-07-26, this commit — `verify --estimate` costs a full verification with `stat` alone: nothing is hashed, nothing is opened, no lock is taken, and it always exits `0` because nothing was read and so nothing can have been found wrong. The unique set is built exactly the way `ReadSet` builds it — by `(device, inode)` for a hardlink-published instance and per file for a copy-published one — so the figure it reports is the figure `--full` would actually read rather than the archive's logical size. A path that cannot be `stat`ed is counted separately and charged nothing, so an operator reading a suspiciously small estimate can see why it is small. `publication.read_verification_catalog` is new and supplies the last measured throughput; it returns `None` for a catalog that is *absent or unreadable*, deliberately, because every caller uses that file to raise confidence and derived state (`FS-16`) must never do that — an unreadable catalog leaves every revision reading `unverified`, which is the signal an operator acts on. Before the first `--full` there is no measured rate and therefore no estimated duration: a number derived from a rate nobody measured is a guess wearing a decimal point, and this is the operator sizing a maintenance window. Decision 50 records why `storage_maintenance` reports `undetectable`)
- [x] VER-005 Verification reports and current health (2026-07-26, this commit — plan §16.2 items 8 and 9, and the second item this phase carried in. `verification.persist_verification` writes the durable `VerificationReport` under `runs/` and *then* the catalog that names it, in that order because `last_full_verification.report` is a path an operator follows and a catalog naming a report that did not exist yet would be a dangling reference in the one artifact reached for when the archive is already suspect. A failing run writes its report exactly as a clean one does: the evidence is the point. `verification.verification_catalog` **merges** rather than replaces, which is what `docs/schemas.md` §5.2 requires — an outstanding failure is cleared only by a verification that re-read the same object, never by a narrow run that did not look, and `first_seen_at` is preserved across re-reports so an operator can tell last night's fault from a quarter-old one. A third clearing path is added and documented: a revision that is no longer retained leaves the catalog, because a pruned revision does not exist and an archive reported permanently degraded over content it no longer holds carries a signal nobody can clear. `last_full_verification` is replaced only by `--full`, since a `--new` run measures a handful of objects and its throughput would give the estimator the wrong workload. `VerificationOutcome` now carries a `RevisionOutcome` per revision *covered*, because "this revision was re-read and was clean" is a fact no set of findings can express. `status` reports the archive-level verification block `docs/cli.md` §2 asks for and still exits `0` — it reports, and `verify` classifies. **Both carried-in items and two corrections:** decision 51 settles `verification_state` and gives all three call sites one source of truth (`failed` was previously unreachable); decision 52 fixes `storage.write_model`, which always raised `SafetyError` and so exited `20` for every `HFSYN`/`HFRET`/`HFVER` code it was given — decision 46's rule applied everywhere except there. All new modules at 100% branch coverage)
- [x] VER-006 Isolated-cache repair, atomic ref switching, retirement grace, checkpointed cleanup (2026-07-26, this commit — `src/hfcache/repair.py` (decision 54) performs all fifteen §7.5 checkpoints, and `recovery.py` gains the six remedies that close the first carried-in item. **Checkpoint 4 is the gate `AD-13` exists for**: the isolated download is hashed and compared against the *original* manifest, and a single difference is `HFRET006` with the published revision untouched — newly observed bytes are evidence of a failed repair, never a new expectation. **Checkpoint 8 is the second gate**: the replacement is re-read from its *published* location, through the same `verification.verify_target` `verify` uses, before any reference moves; a test loses a file between the rename and that read and asserts nothing switched. The download goes into `.store/repair/<txn>/hub` and nowhere else (`FS-14`'s single exception), because the canonical cache may hold the very blob under suspicion. The replacement keeps the SHA's `publication_generation` — a repair that reissued one would move the revision in the prune queue for having been fixed (`AD-05`) — and its manifest copies the original's path/size/digest set exactly *and* every digest in it was read from disk this run, which is how `docs/schemas.md` §3.5 and `AD-18` hold at once. The retired instance stays readable at its original locator for the seven-day grace, and after it a checkpointed cleanup **quarantines rather than deletes** (plan §16.5 item 12); `status` reports `HFWRN008` and what quarantine is holding. **The journal deliberately stays open past checkpoint 15**, because 16-18 are the same transaction and an open journal is the only durable record `recover` can find on its own. `repair.py` and `recovery.py` both at 100% branch coverage. Decision 53 records the evidence-convention fix the roll-forward remedies needed first, and the crash tests raise an exception nothing handles — the only way to leave a journal the way a killed process does, since every mutating command closes its own on a handled error)

**Phase 6 complete.** The archive can now be audited and mended. `verify` reads
published trees back against their immutable manifests in four scopes, reads
each physical object once, runs with Hub networking disabled, and exits `40` on
any finding without ever rewriting a manifest, pruning a revision, or
re-downloading over the evidence. `repair` replaces a damaged instance from an
isolated cache, refuses a download that does not match the original manifest,
switches references only after re-verifying where the replacement now lives, and
quarantines the superseded instance after its grace rather than deleting it.
`recover` resolves every §7.3, §7.4, and §7.5 state the documents give a
resolution for, and still refuses the ones they do not. `scripts/check.sh`
passes with 1463 tests; `-m live` runs 24 against the real Hub, now including
a `verify` over both freshly published test repositories with networking
disabled — clean, one read per physical object — and a flipped byte in one of
them reported without the manifest or the reference changing. Every Phase 6
module is at 100% branch coverage.

`verification.py` was added from plan §7's list, no deviation; `repair.py` was
added beyond it (decision 54). Decisions 49-54 record this phase's settled
interpretations, including both carried-in items.

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
- [x] SYNC-003 Sync run journal and `TX-07` reconciliation (2026-07-26, this commit — the Phase 6 carried-out item. `cli._run` opens the §7.6 journal inside `preflight.guarded` and records checkpoints 1-3: `run_started`, `preflight_passed`, and `journals_reconciled` — the third *after* `recovery.reconcile` has resolved every unfinished journal, under the lock the run already holds and before a single Hub request. `synchronize` takes the transaction and records 4-7, each after its own act is durable, and commits; a run whose exit is not `0` still commits, because the run transaction completed and which repositories failed is what the report carries. The reconciliation is real work, not a formality: a test leaves an abandoned staging directory from a previous run and the next `sync` quarantines it, names the recovery report in its own journal, and goes on to publish. A `needs_operator` journal stops the run at exit `20` with `hub.downloads == []` asserted — nothing fetched, nothing changed, and the run closes its own journal rather than leaving a second unfinished one behind. **`prune --apply` and `repair` reconcile too**, since `TX-07` says every mutating command does and leaving two of the three out would have recreated this same carried item; `verify` deliberately does not, because §7.9 requires it still answer when the machine has stopped. `plan_recovery` gained `exclude`, which is how a run reconciles everything except itself — `TX-01` opened its journal before it could act, so it is unfinished by construction throughout. Decision 55 records the crashed-run-journal resolution this needed. `recovery.py` and `sync.py` both at 100% branch coverage; `cli.py` back to its one pre-existing gap)
- [x] SYNC-004 Discard a committed transaction's staging area (2026-07-26, this commit — decision 56, found by running `status` on the live archive after the first sync: two successful publications reported `unfinished_transactions: 2`. `discard_staging` had existed since `STO-006` with nothing but its own tests calling it, because `promote_staging` renames `tree/` away and the pending manifest is its *sibling*. It is now the act of publication's checkpoint 10 and repair's checkpoint 15, both recording `staging_absent`, and `recovery._complete_publication` performs it too. `pending_manifest_path` loses its suffix by decision 53's rule — it mattered most for repair, whose journal stays open through the seven-day grace and would have reported `HFTXN003` to every `recover` in that window. The `HFTXN003` test now deletes the *published tree* instead, which is a real journal-contradicts-filesystem state; the deleted staged manifest correctly quarantines the tree. `docs/architecture.md` §7.3 and §7.5 amended. Every affected module still at 100% branch coverage)
- [x] HOST-004 Install the locked application environment (2026-07-26, this commit — `scripts/install-release.sh` performs plan §21.4 rather than describing it, and is the mechanism §30's upgrade steps 3 and 6 name; rollback is the same tool with `--switch`, because a rollback that uses a different procedure than the install is a procedure nobody has tested. Release 0.1.0 is live at `/opt/hfcache/releases/0.1.0` with `current` switched by rename onto a staged symlink — `ln -sfn` unlinks first and leaves a window in which `current` does not exist, which is the one thing a running service must never see. Root-owned, `0755`/`0644`, so the account that runs the archive cannot modify the code that runs it. **The interpreter is the deployment's own:** CentOS Stream 10 ships 3.12 and EPEL reaches 3.13, so CPython 3.14.6 is a uv-managed build installed into `/opt/hfcache/python` and pinned there — a venv whose `home` pointed under `/home` would start on a workstation and fail under `ProtectHome=true` (§22.5), which is a failure that would not have appeared until `SYS-002`. uv is pinned to 0.11.32 and the script refuses a different one. `--no-python-downloads` during `uv sync`, so that step can only use the interpreter the previous step installed. **A defect the build found:** `uv sync` in a staging directory writes that path into `pyvenv.cfg` and every console-script shebang, so the venv is built in its *final* path and it is `switch_to`'s refusal of a release with no `.venv/bin/hfcache` that keeps an incomplete build from becoming live. `packaging/tmpfiles.d/hfcache.conf` provisions `/run/hfcache` for operator-run commands, since `/run` is a tmpfs and the service account cannot create a directory in it. Decision 57 records the `--config` readability defect this exposed)
- [x] SYS-001 Install and validate systemd target, services, timers (2026-07-26, this commit — all seven §22 units written in `packaging/systemd/` and installed to `/etc/systemd/system`. `systemd-analyze verify` over all seven produces **no output at all**, which is the gate; it exits `0` even while reporting ordering cycles, and it did (decision 58). `systemd-analyze calendar` validates both expressions: `*-*-* 02:00:00` and `Wed *-01,04,07,10-01..07 04:00:00`, the latter resolving to the first Wednesday of January, April, July, and October at 04:00 local. **The fstab entry is retired**, commented in place with a pointer to the units and the original kept at `/etc/fstab.pre-hfcache-units`; `daemon-reload` handed the live mount over without interrupting it — same autofs fd, same NFS mount, `status` still `reachable` (decision 58). `hfcache.target` is enabled and started, `srv-hfcache.automount` enabled into both `remote-fs.target` and `hfcache.target`, `hfcache-sync.timer` enabled and active with its next elapse at 02:23 EDT (02:00 plus the randomized delay), and **`hfcache-verify.timer` installed, `disabled`, and inactive** — expressible only because the timers attach through their own `[Install] WantedBy=hfcache.target` rather than the target's `Wants=`, which would have started the disabled one. Starting the target ran no sync, per §22.1. Both services then run clean *through systemd*: `hfcache-sync.service` exits `0` with both repositories `skipped`, and its run report records `invocation_mode: systemd`, which is the distinction §22.2's `INVOCATION_ID` check exists to make; `hfcache-verify.service` exits `0`, `clean`, 17 objects and 12.1 MiB read. `/run/hfcache` is `0700 hfcache:hfcache` from `RuntimeDirectory` and survives the oneshot via `RuntimeDirectoryPreserve=yes`, and `HF_XET_CACHE`/`HF_HOME` have materialized at `/var/cache/hfcache/xet` and `/var/lib/hfcache/hf-home` — nothing resolved toward a home directory. No SELinux AVC denial from any of it. Hardening is `SYS-002`)
- [x] SYS-002 Apply and test systemd hardening (2026-07-26, this commit — every §22.5 setting applied to both service units and every one of them *tested*, by `scripts/check-hardening.sh` and `scripts/hardening-probe.py` (decision 59). The probe runs in a transient unit carrying the `[Service]` properties read out of the **installed** unit file at run time, so it cannot pass while the deployed unit drifts away from it, and it has two halves: the workload §22.5 names — DNS, TLS, a real `huggingface_hub` API call, a real `hf_xet` download, `pydantic_core`/`hf_xet`/`libyaml` imports, and create/fsync/rename/unlink on the NFS archive — and a confirmation that each setting is *in effect*, because a property systemd parsed and could not apply reads as protection in the unit file and is not there. **21 of 21 pass on both units**, with the four network checks inverted for the verification unit: reaching the Hub from it would be the failure. `ReadWritePaths=/srv/hfcache` is the entire non-systemd-managed mutation surface, and the probe confirms the archive inside the service's namespace is the live NFS mount rather than an empty autofs trigger the `ProtectSystem=strict` bind-mount could have captured — it reads the sentinel back. The real `hfcache-sync.service` and `hfcache-verify.service` then both run clean under the hardening, and `status` stays clean. `systemd-analyze verify` over all seven units: no output. `systemd-analyze security`: 2.9 and 2.8, both `OK`; the one ✗ is `UMask=0027`, which §22.2 requires. **Nothing was weakened** — the one probe failure was the probe's own bug (`ProtectHome=true` makes `/home` inaccessible, not empty). §22.3's `PrivateNetwork=true` is deliberately *not* enabled: decision 60)
- [x] SYNC-005 Discard staging when a publication fails before the rename (2026-07-26, this commit — decision 56's problem in the failure path, found at `SEL-001` when a real sync failed under the hardening and left `.store/staging/<txn>/` behind with nothing able to reclaim it. A journal closed `failed` is *resolved*, so `open_journals` skips it, `plan_recovery` never proposes a remedy, and `reconcile_storage` goes on reporting that directory as unfinished work — warning `HFWRN004` about it once it ages past the configured staleness. §7.3's "Before 5 → roll back" row is now performed by the command that knows it failed rather than left for a recovery that will never look. **Only before the rename:** at or after checkpoint 5 a tree is published and the staged manifest is the only thing that can validate it, so it is preserved — a resolved journal in that state is something an operator has to look at, and deleting its evidence first would be the wrong help. Both sides asserted: one test fails the local-completeness check and expects empty staging, the other fails the reference publication and expects the staged manifest to survive. `sync.py` at 100% branch coverage)
- [x] VER-007 Key the reported verification state on the publication instance (2026-07-26, this commit — decision 62, found at `SEL-001` by the retention rotation: a dataset revision that had been pruned and then re-synced under a new publication id read `verified` in `status`, on the strength of a verification of the instance the prune had removed. `catalog/verification.json` has recorded `publication_id` since `VER-005`; `VerificationStates.of` was keying on `(type, id, commit_sha)` and throwing it away, so `verified` became true of content nothing had ever re-read — the unfalsifiable field decision 51 existed to close, reappearing through a different door. The key is now the instance, all three call sites pass the id the reference or manifest already carries, and an entry whose `publication_id` is null raises nobody's confidence because it cannot be attributed to anything on disk. No durable format change: the field was already there. `docs/schemas.md` §5.2 amended. `publication.py` at 100% branch coverage)
- [x] SEL-001 Validate all operations with SELinux enforcing (2026-07-26, this commit — SELinux `Enforcing` throughout, `/srv/hfcache` carrying the normal `nfs_t` filesystem label (§23 item 2), and the services running in the **default** systemd service domain `unconfined_service_t` (item 3). Labels were fixed first, per item 6: every local path's *type* already matched the policy default, but the paths created at a shell carried `unconfined_u` where a system-installed file should carry `system_u`, so `restorecon -RF` was run over `/opt/hfcache`, `/etc/hfcache`, `/var/lib/hfcache`, and `/var/cache/hfcache` — 7 082 paths relabelled, and a second pass would relabel none. `install-release.sh` now uses `-RF` for the same reason. **Every item-4 path exercised on the real dataset:** sync with real downloads through the hardened unit, hashing, hardlink publication, atomic directory rename, the §7.4 **prune** — all ten checkpoints committed, both audit records written, the per-SHA reference removed, trash and quarantine empty — full verification, and `recover --dry-run`. Getting to a live prune took a real retention rotation, because `storage.maximum_revisions` is pinned to 5 by the schema (`HFCFG011`) and `AD-04` triggers a prune only from a *successful publication* beyond the maximum: four more real commits of `fixtures_ade20k` were published, the sixth publication pruned generation 1 automatically, and restoring `revision = "main"` re-downloaded and republished the pruned SHA as generation 7 — which pruned generation 2 in turn. That is §29 step 15's revision change and retention simulation, observed rather than simulated. Afterwards: `verify --full` read 23 unique objects across 6 revisions and reported `clean`; `status` exits `0`, not degraded, no outstanding failures, nothing unfinished. **Zero AVC denials** — no `type=AVC`, `USER_AVC`, or `SELINUX_ERR` record in `/var/log/audit/audit.log` and no `avc: denied` in the journal, for a boot that predates `HOST-004`, so the search covers every operation this session performed. No local policy module was created and none is needed (items 7-9), and nothing was weakened: no `setenforce 0`, no permissive domain, no allow rule, no boolean or fcontext customization. The exercise found three real defects — `SYNC-005`, `VER-007`, and decision 61's `RestrictSUIDSGID` incompatibility — which is what exercising is for)
- [x] SEC-001 Validate optional systemd credential support (2026-07-26, this commit — §22.6 item 4's drop-in is `packaging/systemd/hfcache-sync.service.d/credential.conf.example`, shipped with the release, **not installed**, and carrying the exact `systemd-creds encrypt` recipe plus its acceptance checks. It was installed, exercised, and removed here, because a drop-in nobody has run is a document rather than a control. Evidence, all of it against a deliberately fake token: the ciphertext does not contain the plaintext; `systemd-analyze verify` clean with the drop-in; the credential arrives at `$CREDENTIALS_DIRECTORY/hf-token` mode `0440` and the application resolves it with source `systemd-credential` and **decrypts to exactly the right bytes**, compared by digest rather than printed. `--token-file` resolves with source `token-file` (item 2) and a token file this identity cannot read is `HFARG005` at exit `10`, reported *by shape* — "is unreadable: Permission denied" — never by content. With `hub.expected_account` set, `whoami` is called and the Hub's 401 becomes a failed `hub_identity` check at exit `20` before any mutation (item 5), which is the credential-swapped-by-mistake case caught before a scheduled run uses it. **Ambient Hub environment variables are ignored entirely:** with `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` both set in the unit's environment and no credential supplied, `hub_argument` is exactly `False` — not `None` (T-07). And the secret persisted nowhere it could (item 3): zero occurrences in the archive, in `runs/`, in `config.toml`, in `/var/lib/hfcache`, in `/var/cache/hfcache`, in the release tree, and zero in the journal under either service unit, under any transient probe, or under uid 981. The only journal occurrences at all are `sudo`'s own audit records of the *searches* — uid 1000, session scope — which is the search looking at itself. Cleaned up afterwards with `shred`: the deployment is anonymous, `doctor` reads `credential: pass` (no token) and `hub_identity: skipped`)

**Phase 7 complete (writer side).** The application is deployed, the archive is
initialized and healthy, and every unit is installed, validated, and hardened
with each setting tested. Six work packages beyond the plan's Phase 7 list were
needed, all of them defects the deployment itself surfaced: `SYNC-003` (the
carried `TX-07` item), `SYNC-004`, `SYNC-005`, and `VER-007` in the application,
and decisions 57, 58, 61, and 62 in its contracts. That is the argument for
rolling out onto real storage before declaring anything done — none of the four
was reachable from the test suite as it stood.

**Carried out of this phase.** Two items are open that this phase found and did
not close, recorded here rather than left to be rediscovered:

1. **A pruned revision leaves an empty `revisions/<sha>/` directory behind.**
   ***Closed 2026-07-27 by `RET-008`*** — and it was two directories, not one:
   `manifests/<sha>/` is emptied by the same transaction. See the Phase 8 entry.
   §7.4's checkpoints tombstone the *instance* directory and its manifest;
   nothing removes the now-empty SHA container above it. Nothing derived is
   wrong — `list`, `status`, the catalog, `next_generation`, and `verify` all
   resolve through references, and all five were checked against the live
   archive after the retention rotation — but the tree accumulates one empty
   directory per pruned revision forever, in a consumer-visible location. Left
   open deliberately: removing it means adding an act to §7.4's documented
   checkpoint sequence, which is a durable-contract change and not a drive-by
   at `SEL-001`. It belongs with `OPS-003`/`REL-002`, where the consumer-facing
   tree is documented and reviewed.

2. **`RestrictSUIDSGID=true` is off, and could come back.** Decision 61 records
   why it cannot be set today: `create_staging` must create a setgid directory.
   If `PUBLISHED_DIRECTORY_MODE`'s setgid bit is ever revisited — for instance if
   the consumer export moves to POSIX ACLs, which would carry group inheritance
   without it — the setting becomes applicable again and
   `scripts/check-hardening.sh` is what would prove it.

*A note on two commits.* Decision 61's unit change and the probe extension that
covers it were staged into the `SYNC-005` commit rather than `SEL-001`, where
they belong. The decisions and this checklist attribute them correctly; the
history does not, and rewriting three commits to move two files would have risked
more than it fixed.

## Phase 8 — Operational Readiness and Release

- [x] OBS-001 Close §24's host half — persistent journald, `OnFailure=` hook (2026-07-27, this commit — decision 63. §24's last two bullets were the only part of the section with no implementation at all, and both are things `OPS-001`/`OPS-002` have to reference, so they land first. **Persistent journald:** CentOS Stream 10 ships no `/etc/systemd/journald.conf`, so the effective setting was the compiled `Storage=auto`, which is persistent *only if `/var/log/journal` already exists* — it did not, and every line since the 2026-07-25 boot was living in `/run/log/journal`. `packaging/journald.conf.d/hfcache.conf` sets `Storage=persistent`, `SystemMaxUse=1G`, and `MaxRetentionSec=1year`; the year covers four quarterly verifications, and 1 GiB is deliberate headroom against an observed 8 MiB for the whole of Phase 7. Applied with `systemctl restart systemd-journald && journalctl --flush` rather than a reboot (§36.4), and **the existing volatile history survived the migration** — verified after: same earliest record (the 2026-07-25 07:38 boot), all 75 `hfcache-sync` records, this morning's 02:19 timer run intact. `/run/log/journal` drained. **The `OnFailure=` hook:** `packaging/systemd/hfcache-failure@.service.example`, a template so one handler serves every unit and names which failed, shipped **uninstalled** with the matching `OnFailure=hfcache-failure@%n.service` line commented in both service units — §24 asks that a hook be *left*, and a handler that only reprints what systemd already logged is a seam rather than a control, so it ships like the credential drop-in beside it. It was nonetheless installed and **fired for real** before being withdrawn to an example, for the reason `SEC-001` gives about that drop-in — a control nobody has run is a document: against a genuinely failed `hfcache-sync.service`: five lines at `PRIORITY=3`, tagged `hfcache-failure`, carrying `Id`, `Result=exit-code`, `ExecMainStatus=10` — the application's own §11.2 classification travelling through systemd — and `InvocationID`, which `journalctl _SYSTEMD_INVOCATION_ID=<id>` then resolved to exactly that run's one output line, `HFCFG001`. Fired **once**, for the failure only; the clean run immediately after did not trigger it. The handler reads and does not act (`AD-16`). `systemd-analyze verify` over all eight units: no output, which is the gate (decision 58). Hardening re-checked on the sync unit after the edit: **23 of 23**, which corrected plan §22.5's stale "21")
- [x] OBS-002 Structured event log for §24 (2026-07-27, this commit — decision 64. `src/hfcache/logging.py` is plan §7's listed module, absent until now, and §24's "structured events with stable event names" was the largest thing in the plan with *no* implementation: zero of the thirteen families appeared anywhere in `src/`, and `--verbose` was parsed into `GlobalOptions.verbose` and read by nothing — a documented option that did nothing, which `docs/cli.md` §1 promised raised log detail. Standard library only (`FW-03`), logfmt on stderr so the §4 stdout envelope is untouched, `<N>` syslog prefixes only under systemd so `journalctl -p err` selects failures without leaving noise on an operator's terminal. **The vocabulary is closed** — `emit` refuses a name outside `EVENTS`/`DEBUG_EVENTS`, so a typo is a test failure rather than a line no filter matches. **The run id is injected, not passed:** no call site supplies it, `configure` binds one at startup, and commands that write a durable report rebind to that report's id — which also fixed a real incoherence, `emit_envelope` minting a *second* run id for commands that write no report, giving an operator two identifiers and no way to join them. Emission sites are the boundaries that were already there: `preflight.guarded` for `preflight.failed`, `synchronize_repository` for `repository.resolved`/`skipped`, `_ingest` for the download, dependency, and publication events, `_apply_retention` for `retention.pruned`, `synchronize` for `repository.failed`/`run.completed`, `_emit_verification` for `verification.completed`. `retention.deferred` went to `recovery._deferred_warnings` rather than the prune, because §7.4 names a `cleanup_deferred` checkpoint that **nothing records** — the observation of the tombstone is the only real signal, and that is where it is made. 61 new tests, `logging.py` at **100% branch coverage**, including plan §24's redaction requirement proven by pushing a real-shaped token through both a field named `token` and one named `detail` and searching the output. Four tests assert the wiring end to end: the full event sequence a sync leaves, that every line carries the report's run id, that a failing repository says so at `level=error`, and that `--quiet` leaves both streams empty on a clean run. 41 tests that parsed the JSON envelope out of `result.output` now read `result.stdout`, which is what `docs/cli.md` §4 always specified — a strengthening, not a concession: they now prove the envelope is alone on stdout)
- [x] HARD-001 Make the probe's setgid check exercise and assert the syscall the application depends on (2026-07-27, this commit — decision 66. Found at `OBS-001`, re-running `check-hardening.sh` after the unit edit: the check could not fail for the reason it exists. `hardening-probe.py`'s `_setgid_directory` called only `mkdir(mode=0o2750)`, but `publication.create_staging` calls `mkdir` **and then `chmod`** (`publication.py:139-140`), and on this NFS mount that difference decides the outcome: measured on `/srv/hfcache/.store/health` as the service identity, `mkdir` alone yields `0o750` with no setgid, `mkdir`+`chmod` yields `0o2750`. The check also never *asserts* the mode — it formats the result into its pass message, which is why it has been reporting `mkdir(mode=0o2750) -> 0o750` and passing. So the standing guard on the consumer-visible group-inheritance contract (§5.2) tests a syscall the application does not rely on, and could not fail if setgid stopped landing. Nothing is broken today: every directory in the live published tree is `2750`/`2755`, and decision 61's conclusion is unaffected because `RestrictSUIDSGID` filters the mode argument of `chmod` as well as `mkdir` and its attribution was proven separately in two transient units. The fix mirrors the application — `mkdir` then `chmod` — and asserts both `S_ISGID` and the exact mode on the result, because an unfalsifiable check is the family of defect decisions 51 and 62 exist to close and this was one. **The falsifiability was proven rather than assumed**, which is the only evidence that distinguishes this fix from the bug: run as the service identity against `/srv/hfcache/.store/health`, the new assertions *reject* the old sequence — `mkdir` alone raises `AssertionError: the setgid bit did not land: 0o750` — and accept the new one at `0o2750`. A passing check on its own could not have shown that, since the old check passed too. `check-hardening.sh` then ran green on **both** service units, 23 of 23 each, with the line that had read `mkdir(mode=0o2750) -> 0o750` now reading `mkdir+chmod(0o2750) -> 0o2750, S_ISGID set`; the verification unit still inverts its four network checks. Run from a root-owned staging path under `/opt` rather than the checkout, because `ProtectHome=true` makes the probe unreadable under `/home`, and rather than rebuilding release 0.1.1 in place, which `install-release.sh` warns wants `hfcache.target` stopped — and stopping the target unmounts the archive (decision 65). `REL-001` ships the fixed probe into `/opt/hfcache/current` properly. No AVC denial from any of it, and the probe area was left empty
- [x] OPS-001 Installation and upgrade runbooks (2026-07-27, this commit — `docs/deployment-centos-stream-10.md`, plan §7's listed document, taking a bare CentOS Stream 10 VM to a running `hfcache.target`: packages, the pinned uv and why the interpreter is uv-managed rather than the distribution's, service identity, local paths and why `/srv/hfcache` must not be writable by `hfcache`, the mount units and why network ordering belongs on the mount, configuration and its `0640 root:hfcache` contract, `install-release.sh`, the one-time `archive init`, tmpfiles/journald/failure-hook integration, unit install, `check-hardening.sh` from the *release* rather than a checkout, the prove-before-enabling sequence, and enablement with the verify timer deliberately off. **Every block marked observed is real output.** §30's upgrade and rollback were exercised rather than written from memory: `--no-switch` staging (quoting the same-version rebuild warning), `--switch`, a genuine rollback from 0.1.1 to 0.1.0 and forward again, and a no-change sync through the unit whose journal now shows the `OBS-002` event trail. `archive init` is the one step that could not be re-run — it is once-per-archive by design and its authorization was spent on 2026-07-26 — so it carries the recorded evidence and says plainly that it does. Two findings, decision 65: plan §30 step 1 as written would have unmounted the archive, and rollback needed a second release to be a rollback at all)
- [x] OPS-002 Sync, verification, pruning, and status runbooks (2026-07-27, this commit — `docs/operations.md`, plan §7's listed document and the one four units point `Documentation=` at. Covers `status`, `list`, `plan`, `sync`, `verify` in all four modes, `prune`, and `recover --dry-run` as an operator runs them, plus reading the journal and the durable run report, all eleven `HFWRN` codes with a response for each, every §11.2 exit code with what to do about it, and timer administration. **Every command block was run on this deployment.** The exit codes were provoked rather than described: four distinct `10`s — absent configuration, an unconfigured selector, `verify --revision` without a SHA, `prune` with neither mode — and a real `20`, by holding the exclusive lock with `flock` against a copy of the configuration carrying a one-second `lock_wait_seconds` so the refusal was quick rather than an hour. `40` and `50` stay unprovoked for the reason the rollout checkpoints already give: both need published content damaged, and §36.5 forbids writing to `/srv/hfcache` outside the application's own contracts — the suites cover them. Two accuracy corrections came out of writing it: `plan` emits `huggingface_hub`'s own dry-run progress on stderr, which `docs/cli.md` §1's "progress is disabled when stdout is not a terminal" does not quite describe — though the claim that matters holds, journald has never received a progress line from either unit, verified across the whole retained journal — and `list`'s *human* line does not distinguish an unmanaged repository, only `--json` and `status` do. The runbook says both rather than repeating the tidier claim)
- [x] RET-008 Remove the containers a prune empties (2026-07-27, this commit — decision 68, and the first of the two Phase 7 carried items. §7.4 gains checkpoint 10, `containers_removed`, so the documented sequence is eleven steps; `tests/unit/test_transactions.py` parses the §7.4 table out of `docs/architecture.md` and compares it to `CHECKPOINTS`, so the amendment was enforced by the suite rather than remembered. **Two containers, not one.** The carried item and plan §28 both named only `revisions/<sha>/`; tombstoning also moves the manifest out of `manifests/<sha>/`, and that is equally empty, equally permanent, and equally inside `published/`. The live archive had one of each, from the generation-2 prune of `527d5001…`. **It sits after the commit point**, with the other cleanup, because before checkpoint 7 a rollback puts the tree and manifest back into exactly these containers — removing them earlier would mean recreating them on the one path that must not acquire new failure modes. A crash between 7 and 10 leaves them, `recover` reports `complete_prune`, and finishing it removes them; there is a test that crashes precisely there. **The atomic act is `rmdir` and that is the whole safety argument:** it refuses a non-empty directory, so the two states in which a container must survive — a repair's retired instance sitting beside its replacement through the grace, and a superseded manifest — need no detection of their own and cannot be got wrong. `rmtree` would take both, and `FS-19` is why it is not used: this removes a directory it has *proven* empty, not one it has decided is unwanted. 10 new tests including the `ENOTEMPTY`-versus-real-error distinction, both containers surviving independently, `TX-04` idempotence, and a pruned SHA that returns rebuilding its own container — which is not hypothetical, it is what the live dataset did on 2026-07-26 (decision 62). `retention.py` and `recovery.py` both back to 100% branch coverage. **The live archive was brought into conformance**: the two pre-fix containers were removed with `rmdir` as the service identity — an operation that cannot destroy content, since a non-empty directory refuses it — and `verify --full` then read 23 unique objects across 6 revisions and reported `clean`, with `status` exit `0`, not degraded, nothing unfinished. Leaving them would have had `OPS-003` document a tree shape the live archive contradicted, which is the reason this package was sequenced first)
- [x] REP-001 An unreadable retirement record must stop recovery, not close the journal (2026-07-27, this commit — decision 70, and **found by `OPS-003`'s drill** rather than by the suite, which is the argument for exercising a runbook against a real deployment. Sequence on a throwaway archive: repair a damaged revision, then reach the post-grace state. `recover --apply` reported `applied 1` and did nothing — the retired instance stayed published, `.store/quarantine/` stayed empty, and the retirement record still read `cleanup: pending`. The applied remedy was `close_journal`, with the reason "the repair is complete and its retired instance has already been cleaned up". It had not been. `pending_cleanups` deliberately *skips* a retirement record it cannot parse, so that one damaged record cannot hide the others, and its docstring says `verify` and `recover` are what report damaged artifacts. But `_repair_remediation` turned that skip into a decision: `pending is None` meant "already cleaned up", so it closed the repair journal — and **that journal is the only thing that makes the post-grace cleanup reachable from `recover`**, since it is left open past checkpoint 15 for exactly this. Afterwards `recover` reported `actionable 0` forever while `status` went on emitting `HFWRN008` telling the operator that "`hfcache recover --apply` performs it". A warning pointing at a command that can no longer act, and a retired instance stranded at its published locator with nothing able to finish it. `unreadable_retirements` now names the damaged records, and the remediation is `BLOCKED` with `HFTXN003` — §7.9's "journal evidence that contradicts the filesystem", which stops the mutating command at exit `20` rather than guessing the smaller answer (`TX-06`). The test fails with `close_journal` when the fix is disabled and passes with it; the readable-and-complete case still closes, which is what `close_journal` is actually for. `repair.py` and `recovery.py` both at 100% branch coverage. *The defect was reached by a harness error of mine* — expiring the grace by moving `grace_expires_at` before `retired_at`, which the model rightly refuses — and that is precisely the shape of a real one: a record damaged by a partial write, a bad restore, or an editor)
- [x] OPS-003 Corruption and repair runbook → `docs/recovery.md`, repair half (2026-07-27, this commit — decision 72. Plan §7's last missing document but one. **The whole drill ran on a throwaway archive**, never on `/srv/hfcache`: §36.5 forbids damaging published content, and there is no override for the preflight either — the archive root must be a mount point of type `nfs`/`nfs4` read out of `/proc/self/mountinfo`, so a directory on local disk is not a stand-in. The throwaway is therefore a **second NFSv4 export served by the writer to itself**, which needs no NAS change and cannot reach the real dataset; §6 of the runbook is how to build one, because being able to rehearse is the point. `doctor` passes all 17 checks against it, hardlink and atomic-rename probes included, which is what makes a rehearsal there mean anything. Exercised on release 0.1.2 so the quoted output is the deployed CLI: a byte flipped in a published file, `verify --full` at exit `40` with `HFVER001` and a `digest_mismatch` finding carrying `expected` and `observed` side by side, `status` reading `failed` with `archive degraded` on **stderr** while still exiting `0`, then `repair`, then clean. Both instances present through the grace with `recover` answering `wait` and naming the expiry; past it, `HFWRN008` and `finish_repair_cleanup`; after it, the retired tree **moved into `.store/quarantine/<txn>/` rather than deleted**, its original manifest archived byte-for-byte beside the retirement record, `quarantined_bytes` 12 512 611, and `cleanup: completed`. The four `HFTXN` stopped-machine states were each provoked and quoted with the operator action for each — including that `HFTXN001` covers a *damaged* journal as well as a newer one, which the drill found by writing an invalid journal and getting the field-level validation error back. **`REP-001` came out of this drill**, which is the argument for the requirement that a runbook be exercised: the post-grace cleanup silently did nothing and reported `applied 1`)
- [x] VER-008 Full verification never read `refs/current.json` (2026-07-27, this commit — decision 73, and **found by `OPS-004`'s drill**, the second defect a runbook rehearsal has produced. `resolve_repository` enumerates `refs/revisions/`, because that is what makes a SHA retained (`FS-11`). `refs/current.json` is not in that directory, so nothing verification resolved ever reached it — and it is *the one file a consumer must read* (§6.3). Demonstrated on the throwaway: point `current.json` at a publication id that does not exist, leaving the per-SHA reference correct, and `verify --full` reported `outcome clean` at exit `0`. That is `FS-10`'s dangling reference, and it strands every consumer that resolves it — `docs/consumers.md` tells them to treat a vanished tree as retryable, so they would retry against it forever. Meanwhile plan §16.2 step 3 says the quarterly job "validates refs, manifests, and publication paths", and `docs/schemas.md` §4.2 states the invariant nothing enforced: `current.json` always names a SHA that also has a `refs/revisions/<sha>.json`, and both agree on `publication_id`. `resolve_current_reference` now checks exactly that, reported as `ref_invalid`/`HFVER008` — **no durable-format change**, because that finding kind already existed. Deliberately narrow: when the *per-SHA* reference is the damaged artifact, `resolve_revision` already reports it and this adds nothing, because one broken file must produce one finding — the first draft reported twice and five existing tests caught it. Its documented limit is a `current.json` that will not parse at all: a `Finding` requires a `commit_sha` and an unparseable reference supplies none, so rather than attribute damage to a revision that may be sound, nothing is reported — and it is not silent, since `status` drops the repository to `unverified` and `examples/copy-revision.py` fails closed at exit `2`. 6 new tests, `verification.py` at 100% branch coverage. Confirmed end to end on release 0.1.2: the state that read `clean` now reads `HFVER008` at exit `40`, and the live archive still verifies clean over 6 revisions)
- [x] OPS-004 Snapshot/replica restore, lost writer, and damaged references (2026-07-27, this commit — `docs/recovery.md` §§7–9, completing plan §7's document set bar `truenas.md`, which is handoff item 11. The ZFS drill itself is operator work and is **not** claimed as exercised: `NAS-006` is unconfigured, so there are no snapshots on this dataset to restore from, and the runbook says so rather than describing a rehearsal that did not happen. What it owns instead is everything around that drill, and all of it was run. **Before**: establish what is damaged from the findings, whether a transaction is in flight — a restore underneath an open transaction manufactures the `HFTXN003` state §5 documents — and which snapshot predates the damage; plus a preference order that puts individual files above whole datasets, and a warning not to restore `.store/` selectively, because journals and `published/` are consistent with each other and mixing them is how you make a contradiction. **After**: `verify --full` is what establishes a restore worked, per §16.3, and a still-failing verification means the wrong snapshot rather than a need to converge. **Catalog reconstruction demonstrated**: deleted `catalog/repositories.json`, showed `list` and `status` still answering because they read manifests and references, and a `sync` rebuilding it (`FS-16`). **Damaged `current.json` demonstrated**, which is what turned up `VER-008`; the runbook now documents both the loud case (`HFVER008`, exit `40`) and the quiet one, and reconstructs the reference from the per-SHA reference of the highest generation — never by modification time (§31, `AD-05`). **Lost writer**: same hostname and IP because the export is scoped to it, redeploy from `docs/deployment-centos-stream-10.md`, and *do not* re-run `archive init` — the sentinel is the guard that catches a wrong UUID or a misdirected mount. §9 is an acceptance sequence ending in a `sync`, because a clean sync is the only proof the archive will accept writes again. **Writing it found a defect in itself**: `list --revisions --json` is `No such option` at exit `2` — `--json` is a global option and precedes the subcommand — and the same error was in three more blocks I had already written. All four corrected and each re-run)
- [x] OPS-005 Close §26.6's failure-injection matrix (2026-07-27, this commit — decision 69. The audit found the matrix **substantially covered**, as plan §28 expected, and the two rows it named as thin were exactly the two that were: §7.3's `revision_ref_published` had no crash test at all — `test_an_older_revision_rolled_forward_does_not_become_current` exercises the *condition function* directly and its own docstring says "on its own" — and §7.4's commit point had crash tests on either side of it but none *at* it, because `crash_at(publish_catalog)` stops during checkpoint 6 and `crash_at(write_model)` stops during checkpoint 8. Four tests fill them: the two §7.3 boundaries after the per-SHA reference (`publish_current_reference` and `publish_catalog` in `sync`), the §7.4 state where `catalog_published` is the last checkpoint and the archive has therefore *not yet decided* — the last rollback-able moment, and `TX-06` says put the sixth revision back — and §26.6's eleventh row, an interruption **during** a quarterly verification, which had nothing. That last one needed a new kind of injection: §7.4's commit point has no function call between two checkpoints to hang a `crash_at` on, so `crash_at_checkpoint` counts the checkpoints themselves and kills the transaction after the nth. The verification test asserts the property §26.6 actually asks for rather than an exit code — every published byte fingerprinted before and after, no partial report, the catalog's `last_full_verification` untouched, and the next run still clean: an interrupted verification costs time, not evidence. **The map is executable.** `tests/unit/test_failure_matrix.py` names, for each of the eleven points, the tests that cover it, and resolves every name — it caught its own first error immediately, an entry attributing a test to `test_repair` when it lives in `test_recovery_planning`. A coverage claim in a comment rots silently; this one cannot. **`tests/integration/` is resolved by amending plan §7**, which listed it while it held nothing but `.gitkeep`: §26.2's integration tests all exist and all pass, but they live beside the unit tests of the same modules because they share those fixtures and because the tier boundary does not fall where a directory split would put it. Four new crash tests plus the map's own seventeen assertions; **1577 passing** by default, from 1546 at the start of the phase)
- [x] OPS-006 Measure §27's writer-side quantities (2026-07-27, this commit — recorded in `docs/operations.md` §10, with the method beside every number so they can be re-measured rather than trusted. All work ran in `/srv/hfcache/.store/health/`, the archive's own probe area, and was removed afterwards; `status` clean after. **Writer → NFS sequential write 114 MB/s; NFS sequential read 94 MB/s uncached (`iflag=direct`) and 117 MB/s cached; SHA-256 1 660 MB/s; Hub → writer 14.3 MB/s; hardlink publication 91 links/s; copy-mode fallback 41 files/s; `stat` 95 000/s; Xet peak 252 KiB.** Three of those change how the system should be planned rather than merely describing it. **Publication is metadata-bound**: 91 hardlinks per second means a 10 000-file dataset spends about two minutes in publication alone, after downloading and hashing — so for a large dataset repository it is the link rate, not throughput, that sets the sync window. **Hashing is free relative to the mount**: 1 660 MB/s against a mount that reads at 94 MB/s, and local disk measured 1 672 MB/s, so it is CPU-bound and ~18× faster than the storage feeding it — which is why a full verification's cost is the read, and why `verify --estimate` reports unique bytes. **`verify --full` plans at 94 MB/s** — 5.6 GiB/minute, 340 GiB/hour — which is the figure to schedule the quarterly job against and the concrete reason §16.2 says not to overlap a scrub. The two space quantities are **deferred with their methods recorded**, honestly rather than approximated: space-per-five-revisions needs the production list (operator decision 1) — measured on the current test repositories the logical-to-physical ratio is 1.01×, which measures nothing, because their revisions share almost no files and the sample is 12.5 MiB — and snapshot-held space needs `NAS-006`, since this dataset has no snapshot schedule yet)
- [x] OPS-007 Consumer copy-and-verify helper + `docs/consumers.md` (2026-07-27, this commit — decision 67. `examples/copy-revision.py` is plan §6.3's "small shell/Python example", and `docs/consumers.md` is plan §7's listed document; both are the downstream half of the archive, and sequencing them early is what unblocks handoff items 1, 2, and 5. **Standard library only** — a consumer should not have to install this project to read what it produced — so it was exercised with the host's system `python3` 3.12.13 rather than the release's 3.14, which is the proof that it carries no dependency on either. Both live repositories copied and verified from the writer against `/srv/hfcache/published` as the service identity: the model at 10 files / 12 512 611 bytes and the dataset at 7 files / 206 179 bytes, each matching the sizes recorded at `HUB-004` exactly. **The verifier was itself verified**, because an unfalsifiable check is what `HARD-001` had just finished closing: on a **throwaway** copy of the published tree in `/var/tmp` — never on `/srv/hfcache`, per §36.5 — a flipped byte is caught as a digest mismatch, a removed file as `missing`, an added file as `extra`, and a vanished tree as retryable, retried, and then given up on at exit `1`. The two states that mean the *archive* is inconsistent rather than racing are refused immediately at exit `2` without spending an attempt: a reference whose `tree` would escape the mount, and a reference and manifest naming different instances. §6.3's repair contract is demonstrated rather than asserted — with `current.json` switched to a second instance while the first was still present, which is exactly what a repair leaves during its grace, the helper resolved and verified the **new** one. The trap the document leads with: a reference's `tree`/`manifest` are relative to `published/` and the *manifest's own* `tree` field is archive-relative, so a consumer that used the latter would build a path it cannot see)
- [x] REL-001 Build and install release candidate 0.1.2 (2026-07-27, this commit — decision 71. The package's premise turned out to be **false on inspection**, which is why it is answered rather than performed: `install-release.sh` does not deploy a source tree. `uv sync --frozen --no-dev --no-editable` builds a wheel from the staged release tree and installs *that*, and the deployed venv proves it — `hfcache-0.1.2.dist-info/` with `WHEEL` reading `Generator: uv`, `Root-Is-Purelib: true`, `Tag: py3-none-any`, and a full `RECORD`. There is no `.pth`, no editable path reference, no `src/` on `sys.path`. So "no deployed release has been installed from the built artifact" was not the case; what was true is that it is not installed from **`dist/`**. Making it so was considered and rejected: `dist/` is a build directory that can hold a wheel built from a *different* checkout than the one being staged, which would deploy something that does not match the release tree beside it — a new failure mode in exchange for a property already held. The lock stays authoritative for dependencies, which `uv pip install`ing a wheel would give up. So the source-tree-plus-`uv sync` mechanism is **retained and documented**, `docs/deployment-centos-stream-10.md` §§13–14 keep their exercised output because the mechanism did not change, and the wheel is smoke-tested into a fresh venv by `-m build` as the package's fallback clause specifies. **0.1.2 is live**, installed by the §13 procedure exactly as written — timers quiesced rather than the target (decision 65), `--no-switch`, `config validate` on the staged tree, `--switch`, `daemon-reload`, a no-change sync through the unit (`Result=success`, `ExecMainStatus=0`), timer restarted. It carries `RET-008`, `HARD-001`, `REP-001`, `OPS-005`, and `OPS-007`. Afterwards: `verify --full` clean over 6 revisions, `status` exit `0` and not degraded, zero AVC denials, and **`check-hardening.sh` run from `/opt/hfcache/current` on both units, 23 of 23 each** — which is the run `HARD-001` deferred for want of a release carrying its fix. 0.1.0 and 0.1.1 retained as rollback targets. **The durable-format check decision 65 asked for was performed**, because this is the first release to change one: fed a prune journal recording `containers_removed`, 0.1.2 accepts it and 0.1.1 refuses it as `HFTXN002` — refused rather than read speculatively, which is the property that makes going back safe. §14 gains the operational consequence: roll back with no prune in flight)
- [x] REL-002 Final quality and security gates (2026-07-27, this commit — decision 74. **Quality:** `./scripts/check.sh --with-build` exit `0`; 1 585 tests by default, `-m live` 24, `-m nfs` 11 passed and 1 skipped, `-m build` 4. **Both Phase 7 carried items closed.** `RET-008` is **fixed** and its residue removed from the live archive. Decision 61's `RestrictSUIDSGID` watch item is **explicitly accepted, having been re-tested rather than assumed**: a transient unit carrying `RestrictSUIDSGID=true` still fails the setgid `mkdir`+`chmod` on the archive with `PermissionError: Operation not permitted`, and `publication.create_staging` still needs that mode, so the setting stays off on both units for the reasons decision 61 gives — and `HARD-001` means the guard on it can now actually fail, which is what the watch item was waiting for. **Security:** SELinux `Enforcing`, **zero** AVC/USER_AVC/SELINUX_ERR records across the whole retained journal, which since `OBS-001` is persistent and covers every operation of this phase. `systemd-analyze verify` over all eight units produces **no output**, which is the gate (decision 58); `systemd-analyze security` 3.1 and 2.9, both `OK`. `check-hardening.sh` 23 of 23 on both units, from `/opt/hfcache/current`. No token-shaped string persists anywhere it could — the only two matches are a `hf_xxxx…` placeholder in the shipped credential example and the `hf_xet` native library, both examined. `/etc/hfcache/config.toml` is `0640 root:hfcache`; the release tree is root-owned and unwritable by the service identity. **One real finding, fixed:** `uv python install` leaves `/opt/hfcache/python/.lock` at `0666` — a world-writable regular file inside a prefix plan §21.4 requires be root-owned and read-only to everything else. The 1 048 other `-perm -o+w` hits are symlinks, whose modes are meaningless. Narrowed to `0644` on the deployment and `install-release.sh` now sweeps the interpreter directory, which the per-release `chmod` never reached because it sits outside `${RELEASE}`. Afterwards: no world-writable regular file anywhere under the deployment, and the sync unit still runs `Result=success`. **Archive:** `verify --full` clean over 23 objects and 6 revisions, `status` exit `0` and not degraded, `recover --dry-run` actionable `0` blocked `0`, quarantine empty)
- [x] REL-003 Tag and document the first release (2026-07-27, this commit — decision 75. **The version is `v0.1.2`**, and the decision is to tag what is deployed rather than mint a number for the occasion. 0.1.0 and 0.1.1 were never releases: 0.1.0 was `HOST-004` proving the install mechanism, and 0.1.1 was cut at `OPS-001` for the sole reason that a rollback needs somewhere to go (decision 65). 0.1.2 is the artifact that carries every Phase 8 change, was installed by the §13 procedure, hardened 23-of-23 on both units, verified clean over 6 revisions, and rolled *back from* in a real cross-format check — tagging anything else would tag something that was never deployed. Not `1.0.0`, because §33's definition of done includes operator items that are genuinely outstanding: the consumer export, snapshots and replication, the disjointness proof, reboot persistence, and the quarterly timer. A `1.0.0` claiming those would be false. Annotated tag, so `git show v0.1.2` is the release note. **§36.6's eleven done criteria re-verified for the tag, not assumed**: gates pass with `--with-build`; 1 585 default plus 24 live, 12 nfs, 4 build; artifacts exist and the wheel installs into a fresh venv; 0.1.2 installed with `current` atomically switched; `config validate` clean over both test repositories; `doctor` 16 `pass` and exit `0` against the live mount; second sync an idempotent skip for both; units clean under `systemd-analyze verify` with the sync timer active and the verification timer installed and disabled; zero AVC denials; all four runbooks plus consumer documentation exist; and every work package is complete or in the handoff. `README.md` gains the release status and the full document table)
- [x] OPS-008 Name the crash-injection file for what it holds; make the matrix's module list self-checking (2026-07-27, this commit — decision 76. `tests/unit/test_repair.py` is now `tests/unit/test_crash_injection.py`, paying the churn decision 69 deferred: the file holds the publication, prune, repair, and recovery crash injections — 25 of them, 24 through `crash_at` and one through `crash_at_checkpoint` — and the name now says so. Test-tree only: no durable format touched, no deployed behaviour changed, no release forced. The 21 `MATRIX` entries and the `MODULES` entry naming the old module were updated in the same commit, and the matrix's own assertions are the proof the rename is complete — every name it holds still resolves, so a missed reference would have failed the suite rather than waited to be noticed. **One over-claim found in review, closed by assertion rather than corrected once:** `MODULES` listed `tests.unit.test_verification`, which no `MATRIX` row references — the claim "every module named in `MATRIX`" was a comment, and it had drifted. A new test derives the module set from `MATRIX` itself and requires `set(MODULES)` to equal it, so the list can neither miss a module the matrix names nor keep one it no longer does. `test_verification` is dropped: the audit found no row that should point there, and §26.6's verification-interruption coverage lives in `test_verify_command`, which stays. The straggler sweep (`rg "test_repair" --glob '!docs/agents/progress.md'`) finds nothing — decision 69's text in this file is history and stays as written, and `test_config.py`'s `test_repair_grace_at_the_floor_is_accepted` is a substring accident, not a reference. `./scripts/check.sh` exit `0`)
- [x] RET-009 Reconcile §7.4's `cleanup_deferred` claim with the implementation (2026-07-27, this commit — decision 77. `docs/architecture.md` §7.4's failure-regime table said a post-commit failure "records a `cleanup_deferred` checkpoint and warns `HFWRN002`", and nothing records one — `OBS-002` found that when placing `retention.deferred` and worked around it with a comment pointing at the doc claim; this closes it in the direction decision 77 argues for, **doc-to-code**. The row now states the mechanism as built: a failure in steps 8–10 leaves the journal open at the last recorded checkpoint, `recover` reports the prune as `complete_prune` and finishes only the cleanup, and `HFWRN002` comes from observing the outstanding tombstone during reconciliation. `docs/agents/history/plan.md` §15.2 step 11 carries the same amendment inline, dated and attributed, which is the established practice (`OPS-001`'s §30 amendment). **The checkpoint vocabulary is narrowed to match**: the `PERMITTED_EXTRA_CHECKPOINTS` permit for `cleanup_deferred` is removed — the mapping stays, empty, as the documented seam for a future release that wants an extra checkpoint recorded — and the test that exercised the permit is inverted into the falsifiable form of the same guard: a `cleanup_deferred` checkpoint on a prune journal is now **refused** as out-of-vocabulary (`HFTXN002`), with nothing written. **No durable write changes and no archive invalidated**: nothing in `src/` ever recorded the checkpoint — its only writer was the test — and the live archive was checked rather than reasoned about: 34 journals, zero matches. `recovery.py`'s `_deferred_warnings` comment now says what the docs say, that the tombstone observation is the signal; the `retention.deferred` emission itself is unchanged. The §7.4 checkpoint *table* is untouched, so `test_the_documented_sequence_is_the_implemented_sequence` parses the same eleven rows. `./scripts/check.sh` exit `0`; `recover --dry-run` on the live archive as the service identity: `actionable 0`, `blocked 0`)
- [x] VER-009 An unparseable `current.json` produces a durable finding (2026-07-27, this commit — decision 78, closing decision 73's documented limit and the reason 0.1.3 exists. `VER-008` left one case quiet: a `current.json` that will not parse yielded no finding, because `Finding.commit_sha` was required and an unparseable reference supplies none — `verify --full` reported `clean` over an archive whose one consumer-entry file was unreadable. **The widening:** `Finding.commit_sha` and `OutstandingFailure.commit_sha` are now nullable, guarded by model validators that hold `null` to exactly one shape — `ref_invalid` with `publication_id` null and `path` null — so a null SHA in any other finding is refused at construction; both `sort_key`s take `commit_sha or ""`, since a raw `None` in the sort tuple is a `TypeError`. `VerificationRevisionEntry.commit_sha` stays required: a per-revision outcome without a revision is meaningless, and null-SHA outcomes are kept out of `repositories[].revisions[]` and the covered set, so `VerificationStates` and every state consumer read exactly what they read before — proven by a test. `resolve_current_reference`'s silent branch is now the finding: `ref_invalid`/`HFVER008`, exit `40`, one finding, with the sound revision it pointed at coming out of the same run **clean** — one broken file, one finding, still. **The clearing rule is the one piece of real design:** the retained-key rule would silently drop a null-SHA entry on the next narrow run, violating §5.2's "cleared only by a re-read", so `_still_outstanding` gives it its own rule keyed to what actually re-reads the reference — only `--full` does — carried forward by `--new`/`--revision`, dropped by a `--full` (re-added with `first_seen_at` preserved while still broken), and leaving with its repository if the repository leaves `published/`. **No `schema_version` bump**, following the `containers_removed` precedent: field-level widening plus a documented rollback constraint, recorded in decision 78 and drilled at `REL-004`. Docs: `schemas.md` §7 covers both nullable fields, §5.2 the outstanding-failures rule; `cli.md` §5.4's `HFVER008` row gains the case; `recovery.md` §8's "quiet case" paragraph is now loud, with the pre-0.1.3 behaviour kept for operators on old releases; `consumers.md` verified unchanged — the helper's fail-closed behaviour never depended on the quiet case. 18 new test cases: invalid-JSON and valid-JSON-invalid-schema each at exit `40` with null SHA and publication id and `HFVER008` in `errors`; the validator accepts the one null shape and refuses the three distortions on both models; the catalog merge exercised in all four directions; `status` degraded over a null-SHA failure. 1 604 passing by default; `verification.py` and `reporting.py` at **100% branch coverage**; `./scripts/check.sh` exit `0`)
- [x] REL-004 Build, check, deploy, and tag 0.1.3 (2026-07-27, this commit — decision 79. **Gates:** `./scripts/check.sh --with-build` exit `0` — 1 604 tests by default, `-m build` 4; `-m live` 24 passed; `-m nfs` 11 passed, 1 skipped (the pre-checkpoint contract, as at `REL-002`). **The cross-format check decision 65 asks of every durable-format change was performed on a throwaway archive** (`docs/recovery.md` §6's loopback export, rebuilt for the drill and torn down after — its own UUID, never `/srv/hfcache`): with `current.json` broken, 0.1.3 `verify --full` reported **exit `40`, one finding, `HFVER008`, `commit_sha` and `publication_id` both null**, and `status` read `degraded: true, outstanding_failures: 1`. The 0.1.2 binary pointed at the **same catalog** read `degraded: false, outstanding_failures: 0, last_full_verification: null` — the catalog fails field validation, reads as `None`, and every revision reports `unverified`: confidence lowered, never raised (`FS-16`), but the **degraded signal itself is silently lost**. That observed loss is the release note's operational consequence, recorded in `docs/deployment-centos-stream-10.md` §14 beside the prune-in-flight rule: roll back to 0.1.2 only with no null-SHA finding outstanding, clearing it via a clean `--full` first — also observed, after which 0.1.2 read the same catalog fully, `verified` and not degraded. The drill's output is what `docs/recovery.md` §8 now quotes. **Deployed per §13 exactly**: timers quiesced (never `hfcache.target` — decision 65), `--no-switch`, `config validate` clean on the staged tree, `--switch 0.1.3`, `daemon-reload`, one sync through the unit (`Result=success`, `ExecMainStatus=0`, idempotent skip), timer restarted and active. **Post-deploy, on the live archive as the service identity**: `verify --full` clean — 23 objects, 12.3 MiB, 6 revisions, 2 repositories, exit `0`; `status` exit `0`, both repositories `verified`, not degraded; `recover --dry-run` `actionable 0 blocked 0`; `check-hardening.sh` from `/opt/hfcache/current` **23 of 23 on both units**; `systemd-analyze verify` over all eight units, no output (decision 58); SELinux `Enforcing`, zero AVC records. 0.1.0, 0.1.1, and 0.1.2 all retained as rollback targets. Annotated tag `v0.1.3` carries the release note; README release status updated)

## Public repository preparation (DOC, 2026-07-28)

The plan's phases end at Phase 8; these packages prepared the repository for
its public remote (`github`, primary) and lab mirror (`forgejo`) and added the
agent-context layer. Decision 80 records the family and this section sitting
outside §28's phase set.

- [x] DOC-001 Remove stale test-tree placeholders; consolidate `.gitignore` (2026-07-28, this commit — decision 80. The three `.gitkeep` files under `tests/unit/`, `tests/system/`, and `tests/fixtures/` predate the suites that populated those directories, and a placeholder in a populated directory asserts nothing — git tracks the members now. `.gitignore` carried `.claude/` three ways — two blanket entries plus a third naming one file inside it — accreted across sessions, and an uncommitted `.hypothesis` line at the end; now one entry per tool, grouped by what the state is, with `.hypothesis/` beside the other test artifacts it belongs to. No behaviour, no durable format, nothing a release ships. `./scripts/check.sh` exit `0`)
- [x] DOC-002 `AGENTS.md` context router, `CLAUDE.md` symlink, `docs/agents/` (2026-07-28, this commit — decisions 81, 82. The router is deliberately small and loads nothing: a read-first list, a task→document map, the non-negotiables with their IDs, and the commands, every reference a backticked path an agent reads on demand — decision 81 records why that shape and why `@`-imports were rejected. Four agent docs land under `docs/agents/`: `workflow.md`, the §36 successor — session startup, the work-package loop, the Decisions rules, and pushing to both remotes (decision 82); `conventions.md`, the code/test/doc conventions with their reasons, including the two doc-parsing tests and the closed dependency set; `environment.md`, the writer VM's facts and the hard limits carried unrelaxed from §36.4–§36.5; `release.md`, `REL-004`'s worked run distilled into the standing checklist — gates, the decision-65 drill, §13 deploy, the proof set, tag-then-push. Plan §7 and §36 carry dated amendments; README points agents at the router. `./scripts/check.sh` exit `0` — the §7.3–§7.5 table parser and the `cli.md` reader consume regions nothing here touches)
- [x] DOC-003 `CHANGELOG.md`; README `Status` becomes a pointer (2026-07-28, this commit — decision 83. Entries for `v0.1.2` and `v0.1.3` condensed from the annotated tags, which the preamble names as the complete notes — one authority, one convenience; 0.1.0 and 0.1.1 stated for what they were, install-mechanism proofs that were never releases. Each entry keeps the release's operational edge: 0.1.3's carries the null-SHA rollback rule beside the change that created it. README `Status` drops its per-release narrative — the paragraph had grown a release note each tag — and keeps the current version, the deployed state, and the pointers; plan §7 carries the one-line amendment. `./scripts/check.sh` exit `0`)
- [x] DOC-004 README for a public repository; `[project.urls]`; deployment §4 clone reality (2026-07-28, this commit — README gains a repository-layout table, and its `Development` section now says what the gate *is* — `scripts/check.sh`, with the three opt-in markers spelled out — instead of restating the §8.4 command list the script already runs in order; clone instructions name the public repository. `pyproject.toml` gains `[project.urls]` (homepage, repository, changelog, issues at `github.com/wtcross/hfcache`) — metadata only, no resolution input, so the lockfile stands and `uv lock --check` inside the gate proves it. `docs/deployment-centos-stream-10.md` §4's `git clone <origin>` placeholder and its "no remote is configured" note — true when written, wrong since decision 82 — now name the real repository and the mirror; a runbook is edited directly, not amended (`docs/agents/conventions.md`). No decision: nothing here deviates from a contract. `./scripts/check.sh` exit `0`)
- [x] DOC-005 Scrub environment specifics into placeholders (2026-07-28, this commit — decision 84. Every lab hostname, address, provisioned identifier, and login-account path in tracked files is replaced by a placeholder of the same shape: `*.lab.cross.solutions` → `*.lab.example.com` (RFC 2606), `192.168.10.x` → `192.0.2.x` (RFC 5737, last octets preserved so the export-allow-list narrative still reads), the provisioned archive UUID → the all-zeros UUID `examples/config.toml` already uses for "replace me" — its truncated `…-` form in the §24 log sample included — and `/home/tyler`, `` `tyler` ``, the sudoers filename, and the mirror URL's account → `<operator>`/`<user>`. The replacement reached everything the strings touched: contracts, runbooks, plan §34–§35's confirmed-values record, handoff items, decision 82's quoted URL, the golden fixtures **and** `tests/fixtures/examples.py` that generates them, unit-test fixture strings, `srv-hfcache.mount`'s `What=` and `Description=`, and the live-mount test's docstring. `CLAUDE.md` was excluded from the in-place pass because editing through it would have replaced the symlink with a regular file. Deployment §0 now states the placeholder convention. What stays, deliberately: the `wtcross` GitHub identity, author email, and license copyright (published on purpose), `tank/huggingface-archive` (TrueNAS's default pool name, generic), and hash or random log samples (config fingerprint, run ids) that identify nothing. `./scripts/check.sh` exit `0` — the goldens and their generator moved together. History before this commit still carries the originals; decision 84 records that boundary)
- [x] DOC-006 `docs/storage-requirements.md` and `docs/quickstart.md`; README requirements (2026-07-28, this commit — decision 85, closing the portability review's largest finding. The storage half of the system now has a server-agnostic statement: one filesystem with hardlink and atomic-rename semantics, the read/write writer export with every identity squashed to the writer pair, the server-enforced read-only `published/` export squashed to a read identity whose group is the entire read path, pre-creation and adoption (`FS-22`), and capacity — each citing its IDs, with plan §20 as the TrueNAS worked example and `doctor` as the proof. The quickstart promotes `docs/recovery.md` §6's loopback archive from rehearsal aid to first run, adapted to a checkout: `uv run`, the operator's own identity with no squash, the `/run/hfcache` hand-creation the deployment gets from tmpfiles, and the free-space reserve turned down from the example's production 100 GiB — with an explicit redirect to §6 on a host that already runs the deployment, where `/run/hfcache` belongs to the service identity. §6's form was exercised at `REL-004`; the checkout adaptation is derived from it, not freshly exercised, and states which knobs differ. README gains a Requirements section and the two table rows, and its `truenas.md` paragraph now sends the generic reader to `storage-requirements.md` while the lab's NAS runbook stays an operator deliverable (handoff item 11). Plan §7 carries the amendment. `./scripts/check.sh` exit `0`)
- [x] DOC-007 Portability notes: script overrides, path coupling, maintainer pushes (2026-07-28, this commit — the rest of the portability review's findings. `install-release.sh --help` now prints the environment overrides that already existed (`HFCACHE_PREFIX`, `HFCACHE_SOURCE`, `HFCACHE_UV`, `HFCACHE_UV_VERSION`) — the mechanism was there, undocumented, and the `--help` sed range moved with the header it prints (verified by running it). Deployment §3 says how to move with a moved uv pin; §2's "(uid 3001, gid 3002)" now reads as the server's choice of values with `storage-requirements.md` §2 as authority; §5 gains the one-path-five-files note — `srv-hfcache.mount`/`.automount` names derive from `Where=` via `systemd-escape --path`, both service units carry `RequiresMountsFor=` and `ReadWritePaths=`, and `storage.archive_root` must agree. `docs/agents/workflow.md` reframes pushing as the maintainer's step, since contributors hold neither remote. No decision: nothing deviates from a contract; everything here states what was already true. `./scripts/check.sh` exit `0`)
- [x] DOC-008 Document what happens when a sync outlasts its schedule (2026-07-28, this commit — the 2026-07-28 long-run investigation found the mechanics all present and the explanation absent: nothing said what happens when a run is still executing at the next 02:00. `docs/operations.md` §9 now carries "When a run outlasts the schedule": the oneshot merge — a trigger that elapses mid-run coalesces into it, the day is skipped, and `Persistent=true` covers a host that was down, not a unit that was busy; why the skip is `AD-02`/`AD-03` semantics rather than a fault; what survives an overrun (resumable cache partials per `AD-09`, per-repository transactions, next-run reuse); the lock as the second wall with its asymmetric waits and the `HFMNT010`/exit-`20` giving-up path that leaves no run report — precisely the case the inactive `hfcache-failure@` hook exists for; and the chronic-overrun guidance (fewer observations, `hfcache plan` before adding, stage large additions). The `Persistent=true` comment in `hfcache-sync.timer` gains the two sentences that prevent the misreading at the spot it would happen — comment-only, no behaviour change, no redeploy forced. No decision: everything stated was already true. `./scripts/check.sh` exit `0`)

## Guest memory bounding (SYS, 2026-07-29)

Opened after the 2026-07-29 incident: the hypervisor OOM-killed the writer VM
at 02:03:55 mid-way through a 1.5 TB download (decision 86 carries the
evidence and the reasoning).

- [x] SYS-003 Bound sync and verify page cache; absolute dirty-page limits (2026-07-29, this commit — decision 86. `MemoryHigh=4G` on `hfcache-sync.service` and `hfcache-verify.service`, no `MemoryMax=`, because above `high` the kernel throttles and reclaims where `max` kills — a slow sync beats a dead one, and exit `40` from verify must never mean "the cap was tight". New `packaging/sysctl.d/hfcache.conf` sets `vm.dirty_background_bytes=1G` / `vm.dirty_bytes=2G` so the dirty share of the budget stays reclaimable-adjacent rather than the ratio default's ~4.8 GiB, which alone could fill the cap with pages reclaim cannot take. Deployment §9 installs the fragment and states the design, including the half only the hypervisor can do. Applied live: units installed per §10, `systemd-analyze verify` silent, `scripts/check-hardening.sh` all 23 checks pass on both units, sysctl values confirmed active. Validated against the real workload: the pre-change boot-time catch-up sync peaked at 18.3 GiB of a 23 GiB guest in 26 minutes; restarted under the cap it streams a 209 GB repository at `MemoryCurrent` ≈ 4.0 GiB, `MemoryPeak` 4.3 GiB. `./scripts/check.sh` exit `0`)

## Sync throughput and queue-ahead pipeline (SYNC, 2026-08-10)

- [x] SYNC-006 Carry same-operation digest evidence through hardlink staging
  (2026-08-10, commit `92ebdba` — a 10.17 TB ingestion exposed that publication
  hashed the canonical cache once and then read every logical hardlink again,
  while discarding the second result. Hashing now records transient
  `(device, inode, size)` evidence from the same open descriptor as the digest;
  hardlink staging re-proves source and destination identity and carries that
  digest without another content read. Copy mode still hashes its distinct
  landed inode, now comparing it with the ingestion digest rather than a fresh
  source hash. A replaced source or unproven link is refused before rename and
  cleaned from staging. Repair uses the same evidence but retains its required
  final-locator re-verification. No durable schema or checkpoint changed;
  targeted hashing, sync, publication, verification, and crash-injection tests
  plus the full quality gate cover the change.)
- [x] SYNC-007 Download the admitted queue while earlier repositories hash
  (2026-08-10, this commit — the same live run showed the WAN idle for a serial
  10.17 TB hash while nineteen later repositories could not begin. With
  continuation enabled, sync now resolves and estimates every selected
  repository, admits the aggregate download-plus-copy requirement before any
  transfer, then uses one background repository producer whose sole transfer
  receives the existing four-file-worker budget. The main thread consumes,
  hashes, and publishes in configuration order while that producer downloads
  ahead; strict stop-on-error mode stays fully serial. Each completed transfer
  is an ordinary publication transaction at `download_completed`, so existing
  recovery and the native resumable cache remain the durable state. Dynamic
  capacity checks, copy-mode allocation exclusion, serialized cache scans, and
  retention deferred until every queued snapshot is consumed close the races
  introduced by overlap. Run reports retain completed transfer counters after a
  later failure. New queued/hash events make WAN-idle local work explicit in
  journald and Cockpit. Barrier, aggregate refusal, copy capacity, shared-SHA
  retention, failure, ordering, strict-mode, recovery, logging, and full-gate
  coverage exercise the pipeline.)
- [x] SYNC-008 Keep hardlink failure injection aligned with the real syscall
  (2026-08-11, this commit — the release-boundary gate caught one stale test
  double: hardlink publication now calls `os.link(..., follow_symlinks=True)`,
  but the `AD-11` failure injection still accepted only two positional
  arguments and therefore raised an uncoded `TypeError` before the intended
  `OSError` could prove `HFSYN005`. The fake now accepts and asserts the explicit
  keyword, so the test exercises the production call shape and again proves
  that an unavailable hardlink is never downgraded to a copy. The focused test
  and `scripts/check.sh` both exit `0`; source and deployed behaviour are
  unchanged.)

## Release 0.1.4 (REL, 2026-08-11)

- [x] REL-005 Cut and compatibility-check the 0.1.4 release candidate
  (2026-08-11, this commit — version and lock move together to 0.1.4;
  `CHANGELOG.md` accounts for the complete 25-commit delta from the deployed
  v0.1.3 tag — public/agent documentation, bounded service memory, the Cockpit
  administration package, and `SYNC-006`–`SYNC-008` — while README states
  honestly that v0.1.3 remains deployed until the upgrade proof completes. The
  decision-95 cross-format drill used `docs/recovery.md` §6's isolated loopback
  NFS archive, its own UUID, hfcache 0.1.4 with the production lock's exact
  Hub/Python versions, and never `/srv/hfcache`. The 0.1.4 durable writer wrote
  a schema-version-1 failed report carrying `HFWRN005` plus `HFRET002`; 0.1.4
  accepted it and `status` showed `last_run_status: failed`, while the installed
  0.1.3 reader refused the file as `HFVER007` and its lenient `status` fell back
  to the preceding `skipped` report. A later older-valid 0.1.4 report made both
  versions show `ref_moved_to_retained_revision`, proving supersession without
  deleting history. Deployment §14 records that observed rollback rule and now
  runs the current release's recovery/status checks before switching; §13 says
  explicitly that stopping a timer does not stop its active service. The drill
  export, mount, source, venv, and configuration were torn down after the proof.
  Integration evidence: the real-Hub suite passes 24 tests; the live-NFS suite
  passes 11 with its pre-initialization case skipped; `scripts/check.sh
  --with-build` exits `0`, including the default suite, type/lint/format/lock
  checks, 42 Cockpit tests and production build, wheel build, and clean-wheel
  install smoke.)

## Explicit repository purge (PUR, 2026-08-15)

- [x] PUR-001 Add explicit transactional removal for unmanaged repositories
  (2026-08-15, this commit — decision 96. New `purge` requires either explicit
  whole-repository selectors or `--all-unmanaged`, exactly one of `--dry-run`
  and `--apply`, and refuses every repository still present in configuration
  with `HFARG007`. Planning resolves every active reference, tree, and manifest
  and rejects unknown shallow content under `FS-19`; apply uses one prune-family
  transaction per repository, tombstones complete `refs/`, `revisions/`, and
  manifest directories, removes cache revisions only through the installed Hub
  API, and retains each original manifest byte-for-byte with a purge-reason
  audit record. Pre-commit recovery restores the whole repository with refs
  last; post-commit recovery never republishes it and completes audit/trash
  cleanup. `PurgePlan` is a new schema-version-1 durable format and the audit
  reason is a field-combination widening, both backed by golden/model tests;
  CLI scope/refusal/apply tests, transaction checkpoint tests, direct recovery
  tests, and the self-checking crash/failure matrix cover the new path. Operator,
  recovery, security, CLI, schema, plan, and architecture contracts were updated
  together. `scripts/check.sh` exits `0`: 1,650 default tests, wheel/sdist build,
  and all 42 Cockpit tests plus production build. No live archive content was
  touched; release compatibility, deployment, and the requested live purge are
  separate release/operator work.)

- [x] PUR-002 Purge live unmanaged repositories and resume catch-up sync
  (2026-08-15, this commit — the operator approved stopping the approximately
  12-hour full verification so the new lifecycle operation could proceed. The
  0.1.5 release candidate was staged and switched only after installed 0.1.4
  `recover --dry-run` reported zero actionable and blocked remedies and live
  `status` reported no degraded or unfinished state. Production
  `purge --dry-run --all-unmanaged` identified exactly nine repositories and
  13 revisions totaling 1,693,558,139,707 logical bytes; `--apply` completed
  one transaction per repository. A repeated dry run reported nothing to
  purge, recovery remained clean, all nine containers disappeared from `list`,
  and 13 retained manifests plus 13 purge records provide the audit trail.
  Available storage increased by 1,682,634,178,560 bytes, from
  20,868,706,074,624 to 22,551,340,253,184 bytes. The quarantine audit mapped
  every directory back to its transaction: the sole entry for a removed
  repository (`Qwen/Qwen3.6-35B-A3B`) contains only an empty `tree/`; all
  1,556,293,529,827 quarantined bytes belong to configured
  `unsloth/GLM-5.2-GGUF` and were preserved. Hardening checks, systemd unit
  verification, and the recent AVC check were clean. The sync timer was
  restored and run `3d006f9b888b49f0ae24a929ec66a2d4` started: all existing
  repositories skipped, the four newly configured repositories queued, and
  `/proc` write accounting proved `MiniMaxAI/MiniMax-Music3` was actively
  downloading rather than stalled. Final tagging remains gated on that run and
  a restarted full verification.)

## Release 0.1.5 (REL, 2026-08-15)

- [x] REL-006 Cut and compatibility-check the repository-purge release
  candidate (2026-08-15, this commit — version and lock move together to 0.1.5;
  `CHANGELOG.md` and README surface the explicit unmanaged-repository lifecycle
  operation. The decision-97 cross-format drill used a throwaway loopback NFS
  archive with its own UUID, never `/srv/hfcache`: 0.1.5 synced the 12.5 MB
  public test model, purged it with a committed complete-repository plan, and
  retained its manifest and purge record under `audit/pruned/`. Installed 0.1.4
  `status` and `recover --dry-run` both exited `0`, with no repositories,
  unfinished transactions, actionable remedies, or blocked remedies. A real
  0.1.4 re-add/sync then succeeded and retained generation 1 from the archived
  manifest; after a second 0.1.5 purge, the older status/recovery result stayed
  clean. Direct 0.1.4 `PrunedRevisionRecord` validation alone refused the new
  reason literal, which is now the precise rollback rule in deployment §14:
  no purge in flight, and use 0.1.5 for direct purge-record tooling. The drill
  export, mount, source, configuration, and local transfer cache were removed;
  `nfs-server` was restored to inactive. `scripts/check.sh --with-build` exits
  `0`; live switching and the requested purge remain the next operator step.)

## Cockpit administration plugin (CPT, 2026-07-30)

A browser administration UI for the deployed writer, as a Cockpit package in
`cockpit/`. `docs/cockpit.md` is the contract (`CP-01`–`CP-14`); decisions
87–89 record the shape and what lost. Read the contract before working any
package in this family.

- [x] CPT-001 Cockpit plugin contract and work-package plan (2026-07-30, this commit — decisions 87–89. `docs/cockpit.md`: rules `CP-01`–`CP-14`; the privilege model — superuser bridge, then `runuser` to the service identity, root never runs the CLI; the operation surface mapped to `docs/cli.md` and `docs/operations.md` mechanisms; envelope and exit-code rendering; the configuration validate-install pipeline with `plan` previews against candidate files; the timer drop-in protocol; the pnpm toolchain and the conditional plugin gate; testing scope and version-1 non-goals. `AGENTS.md`'s context map gains the row routing plugin work to the contract. The 2026-07-30 feasibility review established the facts the contract encodes: no publish command exists — publication is a stage of `sync` and `repair` is the only republish; cockpit 364 is installed and its socket active on the writer; node LTS and pnpm are provisioned operator-side under `PNPM_HOME`. Doc-only: no source, no packaging, no durable format touched. `./scripts/check.sh` exit `0`)
- [x] CPT-002 Scaffold `cockpit/` from the starter kit under pnpm (2026-07-30, this commit — decision 90. Derived from starter-kit @ `a099cb10` with cockpit `pkg/lib` pinned at `47108e2f` ("364 + 95 commits" — the deployed cockpit 364's own era), fetched by the Makefile into a throwaway git repository so cockpit objects never enter this one. Deviations from the kit as shipped: pnpm 11 via `PNPM_HOME` with a committed `pnpm-lock.yaml` and frozen installs (decision 88; `pnpm-workspace.yaml` carries pnpm 11's `allowBuilds` approvals for esbuild and @parcel/watcher, whose install scripts link the platform binary and build the native watcher); no gettext/po pipeline, no RPM/tarball/test-VM targets; `build.js` derives the bundled-package list from the pnpm `.pnpm` layout instead of package-lock.json; unit tests run under `node --test` — node 24 strips TypeScript natively, so the runner adds no dependency at all. `make` 4.4.1 installed host-side via dnf as the one new build tool (the Makefile is the workflow's spine and DoD's install path). The Makefile exports the resolved pnpm's directory onto recipe PATH, because lifecycle scripts need `node` beside pnpm and a non-login shell has neither. Gate wiring: `scripts/check.sh` runs `make -C cockpit check` (frozen install, ESLint, Stylelint, node:test, fresh production build) when `cockpit/`, pnpm, and make are all present, and prints a loud SKIP naming the missing tool otherwise. Proven here: `make` builds `dist/` in 2.4 s; `make lint test` clean with 1 test passing; `make devel-install` symlinks `dist` and `cockpit-bridge --packages` lists `hfcache: /home/<operator>/.local/share/cockpit/hfcache`; the manifest registers one entry labelled "hfcache" in the Tools section (the placement decision contract §8 left to scaffold time). `./scripts/check.sh` exit `0` with the plugin stage executed)
- [x] CPT-003 Invocation layer: envelope client, service-identity spawn, systemd D-Bus helpers (2026-07-30, this commit — four pure modules under `cockpit/src/lib/` (no cockpit import, so they run under node) and two browser-bound under `cockpit/src/api/`. `envelope.ts`: parse plus the `schema_version` gate refusing anything but `1` with upgrade guidance (`CP-02`); `classifyEnvelope` mapping exit codes to UI states with `HFMNT010` as first-class busy (`CP-10`); ops §7 operator guidance per exit code. `command.ts`: the one invocation shape — `runuser -u hfcache -- <cli> --config … --json` (`CP-03`), candidate-config override for the contract's §6 pipeline, and the §1.1 selector grammar (two-segment ids, abbreviated SHAs rejected as `HFARG001` would). `events.ts`: logfmt parser and the closed 13-name §24 vocabulary verbatim from `hfcache.logging.EVENTS`; unknown names are ignored, never errors. `warnings.ts`: ops §8 guidance carried inline. `api/hfcache.ts`: spawn through the superuser bridge with stdout accumulated so the envelope is recovered from non-zero exits — the envelope is emitted even on failure, so an empty stdout is the only spawn-level error. `api/systemd.ts`: D-Bus start/stop/enable/disable/daemon-reload plus unit-state, service-result, and timer-state reads, with `hfcache.target` (`CP-05`) and `hfcache-verify.timer` (`CP-06`) refused structurally inside the module rather than trusted to call sites. The plugin gate grows `tsc --noEmit` (with `skipLibCheck`, because PatternFly 6.1's own .d.ts does not self-check) — esbuild strips types and eslint does not run the checker, so before this nothing type-checked. 22 unit tests: envelope shapes including failure envelopes and the schema refusal, classification per contract §4, argv and selector grammar, real journal lines quoted from ops §4, quoted-logfmt unquoting, unknown-event tolerance — and `warnings.test.ts` parses `docs/operations.md` §8 itself, the repository's tests-parse-the-docs pattern applied to the plugin, so the UI's guidance cannot drift from the runbook. `./scripts/check.sh` exit `0` with the plugin stage running lint, typecheck, all 22 tests, and a production build)
- [x] CPT-004 Dashboard: status, doctor, version, warnings (2026-07-30, this commit — the Overview tab renders the live deployment: `status --json` drives an archive-health card (the ops §1 six fields plus capacity — available/reserve/headroom bytes — and identity/root), a findings table for the structured staging/quarantine observations status reports (the live archive currently shows 3 unfinished transactions and 2 stale staging entries left by the 2026-07-29 incident, so the card renders real signal on first paint), the envelope's coded warnings with ops §8 guidance inline via `WARNING_GUIDANCE`, and the repository table — id, type, enabled/unmanaged, current SHA short-form with full-SHA tooltip, retained count, last run, verification state — 19 rows on this deployment. `doctor` runs on demand, read-only or full, rendering the ordered `checks[]` with pass/fail/skipped labels; `version` renders its §4.1 payload. Shared pieces in `components.tsx`: one `EnvelopeAlert` for every surface, mapping `classifyEnvelope` to alert variants with `HFMNT010` presented as normal single-writer serialization (`CP-10`), and issue rows that always carry the stable code. The `useHfcache` hook holds envelopes; a non-zero exit is a value, not an error. `@patternfly/react-table` added at 6.6.0: react-core ships no table, cockpit's `ListingTable` wraps react-table, and 6.1.0's types predate the `hasAnimations`/`isContentExpanded` props pkg/lib uses — browser-bundled and build-time resolved, `CP-14` untouched. Status/version/list payload shapes were captured from the deployment itself, because `docs/cli.md` §4.1 abbreviates them. 25 unit tests; `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-005 Archive browser and run reports (2026-07-30, this commit — two tabs. **Repositories**: `list --revisions --json` as an expandable table — repository, type, enabled/unmanaged, current SHA, retained count, current-revision size; expanding shows every retained revision with generation (current marked), commit, file count, size, published timestamp, and verification state, which is the per-publication-instance reading decision 62 requires. **Runs**: the `CP-09` read — `runs/*.json` listed and read as the service identity via `runuser`, names validated against the `<UTC>-<run-id>.json` grammar before any path is built (`lib/reports.ts`, unit-tested against traversal and case tricks); newest 50 shown with parsed start time and run id; a selected report renders the §6-schema fields (command, outcome, exit code, invocation mode, per-repository outcomes with byte counts, totals with `_bytes` keys formatted) plus raw JSON behind an expander, degrading gracefully for verification reports. The run_id join is a button: `journalctl -g run_id=<id>` over the persistent journal renders the run's structured trail beside its durable report, exactly the ops §4 join. 28 unit tests; `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-006 Sync operations: units, schedule, selector sync, live activity (2026-07-30, this commit — the Sync tab. **Full runs through the unit** (`CP-04`): Sync now starts `hfcache-sync.service` behind a dialog stating it is the production unit and that a long run is never killed for being long; the button disables while a run is active, because a second start merges (ops §9). Stop is `systemctl stop` behind a consequence dialog quoting the crash-shape guarantees — published stays published, partials resume (`AD-09`) — and reconciliation surfaces automatically afterwards: `recover --dry-run` runs and renders its envelope (`docs/cockpit.md` §5), with apply deferred to the Maintenance tab. **Schedule** (`CP-05`): pause/resume operate on `hfcache-sync.timer` alone — the pause dialog says the mount and target are untouched and that a Persistent timer whose calendar elapsed while stopped fires once on resume; unit-file state, next elapse, and last trigger render from D-Bus timer properties via the new `useUnitPoll` (5 s polling). **Selector sync** (decision 89): enabled repositories from `status` as checkboxes; the confirm dialog states the page-process consequence before starting; the run streams with stderr merged (`err: "out"`) so the §24 checkpoint events are a live feed, and the envelope is recovered from the stream tail by `extractEnvelope` — a pure scanner over line starts (logfmt lines never begin `{`), unit-tested over mixed streams; a spawn-level failure also surfaces reconciliation. **Live activity** for unit runs: `journalctl -f` follower (closed on unmount) rendering latest-event-per-repository from the closed vocabulary plus the raw tail. 30 unit tests; `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-007 Verification surfaces (2026-07-30, this commit — the Verification tab, estimate-first by layout. **Estimate**: `verify --estimate` rendered as the maintenance-window answer — repositories, revisions, unique objects/bytes, estimated duration (new `formatDuration`), measured throughput or "unknown", detected storage-maintenance overlap. **Full verification**: only via `systemctl start hfcache-verify.service` (`CP-04`) behind a dialog stating the shared application lock's 24-hour wait and the HFWRN010 overlap check; while active the generalized `UnitActivity` journal follower (extracted from CPT-006's sync-only version) renders the closed-vocabulary feed; last Result/ExecMainStatus shown. **One revision**: a selector input validated live by the §1.1 grammar — the full-40-hex requirement enforced client-side exactly as `HFARG001` would — run as a streamed page process (read-only, so interruption reads nothing further), envelope + findings summary rendered; the Repositories tab's expanded revision rows now show the full commit SHA precisely so it can be copied into this form. **Quarterly timer**: display only (`CP-06`) — unit-file state, next elapse, and the handoff-item-8 reason written out; no operating control exists in the DOM, and `api/systemd` refuses the unit anyway. 31 unit tests; `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-008 Configuration editor and add-repository flow (2026-07-30, this commit — decision 91. The Configuration tab, two modes over one pipeline (`CP-11`). **Form mode** renders the whole schema: per-repository rows (id, type, revision with the §6 reference grammar validated live — including the abbreviated-SHA refusal — enabled, comma-separated `declared_dependencies`, add/remove with the `AD-06` never-deletes note inline) and all 19 global keys of §3–§5 as a data-driven grid, each with its documented constraint as the hint (`lib/config.ts` `GLOBAL_FIELDS`); serialization is canonical with a generated header naming the plugin, the write time, and the comment loss. **Text mode** edits the document verbatim. **The pipeline**: candidate written to `/etc/hfcache/.candidate.toml` at `0640 root:hfcache` via a root shell (mktemp + chown + rename — cockpit.file cannot set ownership); `config validate --json` against the candidate as the service identity, `HFCFG`/`HFARG` issues mapped back onto form fields best-effort (structured context first, then the `[path]` message convention — `extractFieldPath`, unit-tested) with verbatim messages always shown; when the candidate adds or retargets an enabled repository, `plan` runs **against the candidate file** — no lock, no mutation — and renders the runbook's mandatory sizing numbers (resolved SHA, logical/new/publication bytes); install copies one predecessor to `config.toml.bak` then fsyncs and renames; re-validate reports the fingerprint run reports will carry. `smol-toml` bundled for parse/stringify (decision 91). The §10 worked example in `docs/configuration.md` is the test fixture: parse, field coverage of all 19 keys, and serialize round-trip are asserted against the contract's own document. 38 unit tests; `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-009 Sync schedule editor (2026-07-30, this commit — a Schedule card on the Sync tab, drop-in only (`CP-12`). The managed file is `/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf`, generated with a header naming the plugin and the restore path; its `[Timer]` section clears the list-valued `OnCalendar=` with an empty assignment before setting the replacement — the systemd subtlety `lib/schedule.ts` encodes and the tests assert (clear precedes set), with `RandomizedDelaySec=` optional. Apply is gated on **Check calendar**: `systemd-analyze calendar --iterations=1` runs unprivileged, its normalized form and next elapse render, and editing the expression invalidates the check. Applying (or resetting, which removes the drop-in and its directory when empty) is confirmed by a dialog carrying the `Persistent=true` consequence — a calendar that elapsed while the timer was stopped fires once on restart — then daemon-reload and a timer restart only when the timer was active (`restartUnit` added to `api/systemd`, behind the same `CP-05`/`CP-06` structural guards). The shipped schedule (02:00 local, deliberately; 30 m randomized delay) and the merge-into-running semantics are stated beside the controls. `parseCalendarCheck` is tested against ops §9's own sample output. 41 unit tests; `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-010 Maintenance operations (2026-07-30, this commit — the Maintenance tab. **Prune** and **recover** share one dry-run-first component: the dry run renders its envelope, a scalar summary, and the full plan behind an expander; Apply stays disabled until a dry run in this session came back clean, and its confirmation dialog carries the operation's own guarantee — prune quotes `TX-06` (fails toward more data), recover quotes idempotence and `AD-16` (never guesses, never deletes unknown data). Blocked recovery states surface through the envelope's `HFTXN` codes in the shared alert, matching ops §6's reading. **Repair**: selector input under the same full-SHA grammar as verification, optional `--reason` recorded to the audit trail, and a confirmation stating the `AD-13` contract — verified against the *original* manifest, stops without switching if any digest differs, superseded instance readable through the grace floor — plus the page-process consequence; runs streamed with the command log behind an expander. The "launch from a finding" shape is copy-the-SHA: findings name the revision, and the form validates it exactly as `HFARG001` would. 41 unit tests; `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-011 Packaging, deployment docs, and live evidence (2026-07-30, this commit — **Packaging:** `sudo make -C cockpit install` placed the production build (compressed bundles + manifest) at `/usr/share/cockpit/hfcache`, root-owned; `cockpit-bridge --packages` lists `hfcache` (the development symlink, which shadows the system copy for this user — both paths proven). **Docs:** deployment runbook gains §16 (build/install/update/remove, the plugin's two pieces of host state, the privilege posture); `docs/security.md` gains T-13 and controls-summary row 18; `docs/operations.md` closes with the plugin pointer — the reconciliation `docs/cockpit.md` §10 deferred to this package. **Live evidence, on the deployment, using the plugin's exact invocation shapes:** `status`, `version`, `list --revisions` (12 repositories), and `doctor` (all 17 named checks in contract order, outcomes pass/skipped) all parsed at `schema_version` 1, exit `0`; `verify --estimate` exit `0` — 12 repositories, 16 revisions, ~31.6 h estimated full read at the measured 33 MB/s, which is itself the reason the full-verify surface matters. **Timer-only pause/resume:** stop/start of `hfcache-sync.timer` flipped only the timer between `active`→`inactive`→`active` while `hfcache.target`, `srv-hfcache.mount`, and the executing sync stayed untouched (`CP-05` observed). **Drop-in cycle:** `systemd-analyze calendar` validated `*-*-* 02:30:00`; the managed drop-in applied it (next elapse Fri 02:35:49, inside the randomized window; no spurious Persistent fire — the service stayed on its own run); removal restored the shipped schedule (next elapse Fri 02:21:26) and removed the directory. **Configuration round-trip through the §6 pipeline, forward and back:** candidate at `0640 root:hfcache`, `config validate` exit `0` with fingerprint `6b813bb8…`→`87eedf3c…`→`6b813bb8…` — the starting fingerprint is byte-for-byte the one the running sync's `run.started` event carries — ending `sha256`-identical to the start (`cf0dcc21…`) with `config.toml.bak` present at `0640 root:hfcache`. **The unit-start path:** the entire evidence window ran beside production reality — catch-up run `d694a1b6…` (started 2026-07-29 05:34, 19 repositories) published `moonshotai/Kimi-K3` at 1.56 TB mid-window and was downloading its unsloth mirror; the plugin's `StartUnit` call was issued against it and merged with **zero** new `run.started` events, exactly ops §9's semantics, and the run's closed-vocabulary events were captured live (`publication.completed` with `hashed_bytes=1560998984390` among them); the unit's last completed execution reads `Result=success`, `ExecMainStatus=0`. **Post-conditions:** SELinux `Enforcing`, AVC count today 0 before and after; `hfcache-verify.timer` `disabled`; `ProtectProc=invisible` confirmed applied on both units via `systemctl show` (check-hardening 22/23 — the one failure is the probe's idle-system assumption meeting the live run's same-uid pid, dissected in handoff item 13); nothing under `/srv/hfcache` was created or modified by anything except the application's own runs — the plugin's writes were `/etc/hfcache/{.candidate.toml,config.toml,config.toml.bak}` and the timer drop-in, all cycled back. Three lock-gated proofs are handoff item 13 with exact commands and expected outcomes: the single-revision verify, a fresh start-to-`Result=success`, and the 23/23 re-run — blocked by the terabyte catch-up holding the one archive lock (`AD-17`), and stopping a production 1.5 TB download to manufacture evidence was not a serious option. **Manual smoke checklist (browser-only behavior; operator):** (1) log into Cockpit as an administrator with the superuser bridge active, open Tools → hfcache; (2) Overview shows archive health with real findings, repositories table, doctor buttons produce the 17-check list, version card populated; (3) Sync tab shows the running/idle service state, live activity feed during a run, pause/resume flips only the timer, the selector-sync dialog states the page-process consequence; (4) Schedule card: check-calendar renders normalized form + next elapse, apply/reset both confirm with the Persistent warning; (5) Repositories tab expands to revision detail with full SHAs; (6) Verification tab: estimate renders sizes, revision form rejects an abbreviated SHA inline, quarterly timer card shows disabled with the handoff-8 reason and no enable control anywhere; (7) Configuration tab: form mode renders 19 global fields + repository rows, an invalid value comes back mapped onto its field at validate, text mode preserves comments, install shows the fingerprint; (8) Maintenance tab: prune/recover Apply stays disabled until a clean dry run, repair form requires the full SHA; (9) without administrative access, mutating controls are absent or fail closed. `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-012 Operator documentation: `docs/cockpit-plugin/` and README surfacing (2026-07-30, this commit — four operator-facing pages written against the contract for whoever deploys and uses the plugin: `docs/cockpit-plugin/README.md` (what it is, what it deliberately will not do, doc map), `installation.md` (requirements, production build and install, the build-elsewhere-copy-`dist/` path for hosts without node, development loop with the shadowing caveat, update, removal including the managed host state), `usage.md` (access model; the cross-cutting reading rules — exit-code alert table, `HFMNT010` as busy-not-failure, unit runs versus page processes — then every tab), and `troubleshooting.md` (eleven symptom→cause→fix entries, missing menu entry through leftover managed state). `cockpit/README.md` added as the subtree's pointer to contract and guide. Root `README.md` gains a Browser administration section, documentation-table rows for `docs/cockpit.md` and `docs/cockpit-plugin/`, the `cockpit/` repository-layout row, and the license split (MIT with the LGPL-2.1-or-later subtree, decision 90). `AGENTS.md`'s context map routes plugin work to the operator docs beside the contract; `docs/cockpit.md` names them non-normatively (contract wins on disagreement). One runbook correction folded in: deployment §16's build line becomes `make -C cockpit clean && make -C cockpit NODE_ENV=production` — `install` copies whatever `dist/` holds, so the bare `make` §16 showed would install an unminified development bundle, where CPT-011's actual install was the check target's production build; §16 now says what was done and why. Doc-only otherwise: no source, no packaging, no durable format touched. `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-013 Authenticated plugin invocations: transient units with `ImportCredential` (2026-07-30, this commit — decision 92, prompted by a live `HFHUB003` from the plugin's doctor surface the day `hub.expected_account` was set: every `runuser`-spawned command was anonymous by construction. **Code:** `hfcacheArgv` becomes the §2 `systemd-run` shape (transient unit, service identity, `ImportCredential=hf-token`, `UMask`/`MemoryHigh`/`HF_HOME`/`HF_XET_CACHE` parity with the sync unit); UI copy in sync/verify/maintenance restates the new lifetime (closing the tab detaches the view; the run continues into its run report). **Contract:** `docs/cockpit.md` §2 rewritten around the transient unit with `CP-03`/`CP-08` amended and §5's selector-sync lifetime updated; `docs/security.md` T-13 controls note the PID-1-only decryption; `packaging/…/credential.conf.example` migrates the store to `/etc/credstore.encrypted/hf-token`, corrects its unit-binding claim to name binding, and its drop-in body to `ImportCredential=hf-token`; operator docs (`usage.md`, `troubleshooting.md`) updated, the latter gaining the anonymous-doctor entry and the pipe-don't-redirect note. **Systemd facts verified on this host (systemd 257):** exit codes propagate through `--wait --pipe` (a forced 20 arrived as 20); import of an absent credential is skipped with the unit starting normally; a transient unit survives its killed waiter (`active` until stopped); stdout redirected to a user-labelled file reproduces the `init_t`→`user_tmp_t` AVC and the API-bus drop, recovered with `SIGUSR1` — four denials in the audit log, all mine, all this probe. **Deployed and proven live:** credential migrated by byte-identical copy into `/etc/credstore.encrypted/` (old file removed after `cmp`), installed drop-in now the one-line import, `daemon-reload` + `systemd-analyze verify` clean, `systemctl show` reports `ImportCredential=hf-token`; the plugin's exact argv ran `doctor --read-only` end to end — envelope `schema_version` 1, `credential` row "token from systemd-credential", `hub_identity` row "the Hub reports this run as wtcross", exit `0`; production build installed to `/usr/share/cockpit/hfcache` (bundle greps for `systemd-run`), the 1.56 TB catch-up sync running untouched through the whole window. 42 unit tests (the argv-shape test rewritten for the new shape, plus a new CP-08 no-token-surface assertion); `./scripts/check.sh` exit `0` with the plugin stage)
- [x] CPT-014 Link repository rows to Hugging Face (2026-08-30, this
  commit — decision 101. The Repositories tab renders each repository name as
  a type-aware external link: models at `/<owner>/<name>`, datasets at
  `/datasets/<owner>/<name>`. Identifier segments are percent-encoded; a new
  tab plus `noopener noreferrer` preserves the Cockpit session boundary and no
  archive credential enters the URL (`CP-08`). A pure URL builder covers both
  repository types and encoding. 44 Cockpit unit tests; `scripts/check.sh`
  exit `0` with the plugin stage)

## Authenticated restricted repositories (HUB, 2026-08-23)

- [x] HUB-010 Enable explicitly authenticated private and gated repository sync
  (2026-08-23, this commit — `hub.token_mode = "required"` is now the sole
  opt-in to restricted repository scope and requires an available credential;
  `disabled` and `optional` remain public-only even when optional resolves a
  token. Missing required credentials fail before Hub access as `HFARG008`;
  repositories whose gate has not been accepted fail as `HFHUB005`, while
  `HFHUB006` continues to diagnose restricted content outside required scope.
  `hub.expected_account` is enforced before repository access by `plan`,
  `sync`, and `repair`, and repair now classifies repository metadata before
  downloading. AD-21 and the configuration, CLI, security, operations,
  deployment, Cockpit, and consumer-boundary contracts define the policy,
  revocation, purge, and rollback behavior. Verification: focused sync/crash
  suite, 184 passed; Hub live suite, 24 passed; `scripts/check.sh`.)

## Release 0.1.6 (REL, 2026-08-23)

- [x] REL-007 Cut the authenticated-repository release candidate
  (2026-08-23, this commit — version and lock move together to 0.1.6;
  `CHANGELOG.md` and README describe the explicit required-token policy.
  HUB-010 changed no durable JSON shape, so decision 98's configuration
  rollback barrier applies and no cross-format drill is required. Verification:
  `scripts/check.sh --with-build`; Hub live suite, 24 passed.)

## Consumer model-store provisioning (OPS, 2026-08-24)

- [x] OPS-009 Add the consumer model-store setup script
  (2026-08-24, this commit — `scripts/setup-hfcache-consumer-model-store.sh`
  formalizes the downstream host setup for
  `unsloth/Qwen3.8-27B-NVFP4`: it validates 100 GiB of
  existing-model-plus-available capacity before mutation, installs
  `copy-revision.py` root-owned under `/usr/local/libexec/hfcache/`, creates or
  converges a locked `vllm:vllm` service identity, refuses symlinked store
  boundaries, and makes only the model's `revisions/` directory writable by
  vLLM while root retains the future serving-pointer boundary. The consumer
  runbook documents installation from a checkout, release, or separately
  transferred pair and the mandatory new-destination rule. No consumer-host
  state was mutated by this repository package; that root action remains for
  the operator. Three focused script tests; `scripts/check.sh`: 1,673 passed,
  40 deselected, sdist and wheel built; Cockpit stage skipped on this consumer
  because pnpm or make is absent.)

- [x] OPS-010 Add the verified-model vLLM container launcher
  (2026-08-24, this commit —
  `scripts/consumer-serve-hfcache-model.sh` accepts an operator-selected vLLM
  image, verified local model tree, and YAML configuration; resolves and
  validates the host paths; and execs a foreground `vllm serve` container with
  the model and config privately SELinux-labelled and read-only. It prefers
  Podman, supports explicit Podman or Docker selection with each runtime's
  NVIDIA GPU flag, publishes port 8000, uses host IPC, removes the stopped
  container, and propagates its exit status. The consumer runbook records the
  exact container paths and invocation. No GPU container was launched because
  no deployment image, model, or config was placed in scope. Seven focused
  script tests exercise validation and both generated runtime shapes;
  `scripts/check.sh`: 1,680 passed, 40 deselected, sdist and wheel built;
  Cockpit stage skipped on this consumer because pnpm or make is absent.)

## Three-revision retention (RET, 2026-09-14)

- [x] RET-010 Default to three retained revisions, preserving explicit five
  (2026-09-14, this commit — decision 102. Strict configuration accepts `3`
  or `5`, with omission selecting `3`; Cockpit offers the same numeric choices.
  Contracts, examples, and operator guidance describe adoption, rollback, and
  repeated prune rounds. Existing explicit-five scenarios remain covered;
  new regression coverage proves fourth-publication rotation and reducing an
  existing five-revision history to three. No durable JSON shape changes.
  Verification: 267 focused Python tests; `scripts/check.sh` exit `0`, with
  1,689 Python tests and all 45 Cockpit tests, types, lint, and production build.)

## Release 0.1.7 (REL, 2026-09-14)

- [x] REL-008 Cut the three-revision retention release candidate
  (2026-09-14, this commit — version and lock move together to 0.1.7;
  README and changelog describe the default and explicit-five compatibility.
  Deployment §14 records the configuration rollback barrier. The installed
  0.1.6 binary rejects the proposed live value of three with `HFCFG011`,
  exit `10`, as expected. No durable JSON format changes, so no cross-format
  archive drill is required. `scripts/check.sh --with-build` exits `0`:
  1,689 Python tests, 45 Cockpit tests, production build, and four installed
  wheel smoke tests.)

- [x] OPS-011 Deploy three-revision retention and prune the live model history
  (2026-09-14, this commit — staged and switched to 0.1.7 only through
  `scripts/install-release.sh`; the new binary accepted both the existing
  five-revision configuration and the proposed three-revision configuration.
  Atomically installed the single-key change, preserving `0640 root:hfcache`
  and the predecessor at `/etc/hfcache/config.toml.ret010.bak`. Installed the
  production Cockpit build and matched all five deployed files by digest.
  Explicit selectors covered seven enabled, archived models. Three reviewed
  prune rounds removed 7, 5, and 1 revisions, respectively: runs
  `2af25a222431434e8ef0a2f0e387b554`, `39e199c3e88440a9bfbbc95746e9dcc7`,
  and `943dce8e642349a2824c9d96ac3629e7`, all success without warnings.
  The archive now has 129 revisions across the same 99 models, every model
  at or below three. Exact surviving SHA/publication/generation tuples match
  the original inventory minus the 13 reviewed removals; every current
  reference is unchanged. Deleted SHA containers and cache revisions are
  absent, all 13 archived manifests match their original digests, and prune
  audit records remain. Status is not degraded, with zero unfinished
  transactions or deferred cleanup; recovery has zero actionable or blocked
  remedies and the final prune plan is empty. Logical removed tree bytes total
  7,666,936,383,779, but nearly all content was shared: unique retained file
  bytes fell by only 218,458 across 15 objects. Repeated NFS free-space reads
  stayed at 13,880,416,796,672 bytes, so there was no measurable NAS free-space
  increase at its 1 MiB reporting granularity. The enabled sync timer resumed;
  verification remains disabled. `scripts/check.sh` exit `0`, including the
  plugin stage. Formal release proof remains handoff item 15.)

## Explicit quarantine cleanup (QUA, 2026-09-14)

- [x] QUA-001 Add explicit cleanup of proven redundant recovered staging
  (2026-09-14, this commit — decision 103. The new `quarantine` command takes
  explicit transaction IDs and either `--dry-run` or `--apply`. Terminal
  publication and committed recovery journals must prove ownership of every
  target; unfinished transactions, unknown content, symlinks, and special files
  are refused. Only empty directories or files freshly proven identical to a
  retained current publication can be removed. Apply validates the entire
  batch under the writer lock, then uses anchored directory/file descriptors,
  identity checks, and fresh hashes through each unlink. Interrupted cleanup
  resumes from its proven remaining subset. Original journals and publication
  references remain unchanged; no new durable JSON shape is introduced.
  CLI/recovery contracts and Cockpit's event vocabulary cover the operation.
  Verification: 53 cleanup scenarios, including swapped ancestor directories,
  shared hardlinks, incomplete provenance, whole-batch refusal, and partial
  cleanup; 118 focused tests passed. `scripts/check.sh` exit `0`: 1,743 Python
  tests, 45 Cockpit tests, types, lint, and production builds. Live NFS suite:
  11 passed, one expected initialized-archive skip.)

## Releases 0.1.8–0.1.10 (REL/QUA, 2026-09-14)

- [x] REL-009 Cut the explicit quarantine cleanup release candidate
  (2026-09-14, this commit — version and lock move together to 0.1.8;
  README/changelog describe the explicit cleanup scope and deployment §14
  records unchanged-format rollback to 0.1.7. No cross-format archive drill
  is needed. `scripts/check.sh --with-build` exits `0`: 1,743 Python tests,
  45 Cockpit tests, production build, and four installed-wheel smoke tests.
  The live NFS suite already passed at QUA-001. The running 0.1.7 sync
  must finish before the staged candidate becomes current.)

- [x] QUA-002 Support cleanup after explicitly interrupted empty staging
  (2026-09-14, this commit — decision 104 permits the supervised recovery
  procedure, using the existing recovery APIs without changing their automatic
  age policy. Cleanup accepts valid early journals with no publication ID;
  terminal recovery proof and the prepublication checkpoint boundary still
  apply. Four new regression cases cover the real early journal shapes and
  refusal after publication rename. Version/lock/changelog/README move to
  0.1.9, superseding staged 0.1.8. `scripts/check.sh --with-build` exits `0`:
  1,747 Python tests, 45 Cockpit tests, production builds, and four installed
  wheel smoke tests. No durable JSON change or cross-format drill is needed.)

- [x] QUA-003 Scope checkpoint validation to quarantine deletion authority
  (2026-09-14, this commit — decision 105 corrects rejection of two completed
  July 26 prune journals whose historical sequence lacks `containers_removed`.
  Their records remain intact; actual source/recovery proof ordering remains
  mandatory. Three regression cases cover legacy history and malformed source
  and recovery ordering. All 43 live plans passed as the service identity using
  the updated module: six files, 86 directories, 1,688,517 logical bytes.
  Version 0.1.10 supersedes 0.1.9. `scripts/check.sh --with-build` exits `0`:
  1,750 Python tests, 45 Cockpit tests, production builds, and four installed
  wheel smoke tests. No durable formats change.)

- [x] OPS-012 Deploy 0.1.10 and clean the reviewed quarantine findings
  (2026-09-14, this commit — deployed only through `install-release.sh`, with
  the prior versions retained. Config validation preserved fingerprint
  `f9388bb0…` and the maximum of three; all five deployed Cockpit files match
  the production build. The operator explicitly authorized stopping sync
  `bf1f901508ae4fb4990157d69125ab78`, cleaning, and restarting with its cache.
  Confirmed service/PID termination and the free writer lock. Decision 104's
  exact two-journal, empty-staging recovery preview was reviewed and applied
  through the installed application: report
  `083ee779e9614f6faec1261a179a6a84`, with cache metadata and all references
  unchanged. No configuration age or timestamps were altered.
  The final explicit-ID dry run covered 43 entries: the original 42 plus that
  interrupted download's empty staging. Cleanup run
  `e64f33e61b0340099badc82d795f36f2` removed all 43 entries, 86 directories,
  and six files totaling 1,688,517 logical bytes. Quarantine and the pre-restart
  Findings list are empty; status is not degraded, unfinished/deferred counts
  are zero, and recovery has zero actionable or blocked remedies. All 363
  journals and 228 publication refs are byte-identical across cleanup; the
  original 360 journals also match their pre-interruption aggregate digest.
  Current and cache copies of the six files pass fresh digest checks; their
  link counts changed from three to two. Across all 17,028 cache entries,
  only those six inodes' expected ctime/link metadata changed. The paused
  model's 83,351,737,205 cached bytes remain, including incomplete downloads.
  NFS available space stayed at 13,802,195,124,224 bytes before and after:
  zero measurable NAS space increase, because the removed file links shared
  retained data. Sync restarted as `58dd7515d03b40398d20ac859ad2d86b`, resolving
  the same first commit and starting its download with 364,597,537,255 newly
  required bytes; the sync timer is active and enabled, verification disabled.
  The resumed run is still in progress; normal active staging may appear in
  Overview, while quarantine remains clear. Evidence is in `.git/qua001/`.
  `scripts/check.sh` exits `0`: 1,750 Python tests, 45 Cockpit tests, and
  production builds. Formal release proof remains handoff item 15.)

## Repository synchronization (OPS, 2026-10-17)

- [x] OPS-013 Reconcile local and remote main histories
  (2026-10-17, this commit — refreshed both remotes: GitHub main at
  `e35048a` is an ancestor of local main, while Forgejo main at `7368973`
  contains only the additional `.scratch/` ignore rule. Merged that commit
  without conflicts, retaining all nine local commits through `82bfb7a`
  and every existing work-package boundary. `scripts/check.sh` exits `0`:
  lock, formatting, lint, types, 1,750 Python tests, 45 Cockpit tests, and
  package and production plugin builds. The merge is ready for normal
  fast-forward pushes to both remotes; no history is rewritten.)

## Invariant and architectural decision registers (DOC, 2026-10-17)

- [x] DOC-009 Register current invariants and backfill individual ADRs
  (2026-10-17, this commit — decision 106;
  `docs/invariants.md` collects current constraints with contract and
  implementation/test evidence. `docs/adr/README.md` indexes individual
  architecture, framework, verification, scheduling, and numbered progress
  decisions: 130 ADRs, with original git provenance and explicit amendments.
  `AGENTS.md`, the workflow, conventions, and plan require affected invariants
  and ADRs to accompany every change or new plan implementation. Reconciled
  stale contract wording against existing decisions 20, 60, 61, 66, 96, 98,
  and 102; no application behaviour or durable format changes. Invariant and
  ADR review completed; the pre-existing lifetime-generation conformance gap
  is explicitly tracked as `RET-011`. Validation: all 105 historical decision
  bodies preserved, ADR coverage/index and local link/anchor checks pass,
  and cited local git commit objects resolve. `scripts/check.sh` exits `0`:
  lock, format, lint, types, 1,750 Python tests, 45 Cockpit tests, wheel/sdist,
  and the production plugin build.)

- [ ] RET-011 Resolve the publication-generation contract/implementation gap
  (identified 2026-10-17 during `DOC-009`; `AD-05` / `FS-20` require lifetime
  per-SHA generations and allocation from retained manifests plus pruned audit
  records. `publication.next_generation` currently reads retained references
  only, and `test_a_pruned_sha_that_returns_is_republished_into_a_fresh_container`
  explicitly assigns generation 7 to a returning pruned SHA. A whole-repository
  purge also empties the retained set while preserving generation audit.
  Reconcile the intended rule and allocator deliberately, with a new decision
  and regression evidence for re-observation, purge/re-add, and recovery.
  `docs/invariants.md` and `docs/adr/ad-05.md` distinguish the normative
  constraint from this existing enforcement gap. No runtime or policy change
  is made by the documentation backfill.)

## Dated plans and individual tasks (DOC, 2026-10-17)

- [x] DOC-010 Establish plan and task tracking
  (2026-10-17, this commit — decision 107;
  [plan](plans/2026-10-17-plan-planning-workflow.md),
  [task](plans/tasks/doc-010-planning-workflow.md). The new current selector,
  dated plans, and task files own active execution; progress retains completed
  audit evidence, Decisions, Operator handoff, and unmigrated backlog.
  The agent planning guide defines lifecycle, proportional templates,
  authorization, stable work-package IDs, dependencies, and retained history.
  Agent/human entry points and affected prior ADRs reflect the new authority;
  `INV-011` records the planning invariant. The setup plan/task are complete
  and retained; current selects no active plan, and existing backlog is not
  migrated or activated. Invariant/ADR review completed. Documentation
  link/anchor, plan/task identity/state, and ADR coverage checks pass.
  `scripts/check.sh` exits `0`: lock, format, lint, types, 1,750 Python tests,
  45 Cockpit tests, package builds, and production plugin build.)

## REST API and read-only MCP (API, 2026-10-17)

- [x] API-001 Activate the feature branch and define transport contracts
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-001-contract-and-activation.md); base/main/github
  `86f6e8b`, branch `feat/rest-api-and-mcp`. Imported drafts preserved and
  activated by implementation authorization; all later tasks remain pending.
  API/server contracts define 29 parity rows across 14 CLI families, roles,
  effects and execution. Decisions 108/109 explicitly amend FW transport and
  bounded non-resuming receipt boundaries. Reviewed FS/TX, credentials, output,
  consumer, Cockpit and planning invariants; INV-012–016 identify pending
  enforcement owners. Local links and parity table checks pass. Baseline and
  post-change `scripts/check.sh` exit 0: lock, format, lint, types, 1,750 Python
  tests, 45 Cockpit tests, package builds and production plugin build.
  No dependencies, runtime implementation, deployment or archive operations.)

- [x] API-002 Extract transport-neutral query services and command results
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-002-extract-queries-and-results.md).
  Extracted immutable execution/request/result records and local query services;
  CLI delegation preserves schema-1 envelopes/rendering. Fixed documented
  unmanaged status/list selectors and configured-plus-unmanaged status ordering.
  ID-based existing report/reference/manifest reads validate canonical identity,
  locators/generation and no-follow containment; exact vanished instances fail.
  Reviewed FS-08–12/16, AD-06/10/17, INV-005–008/012 and decisions 51/62/108:
  existing contracts preserved; no new ADR or durable format required. Updated
  architecture, CLI, API, consumer, invariant and Unreleased documentation.
  336 existing targeted tests and 47 new query/evidence tests pass. Initial gate
  stopped on two deliberate immutable-mutation test type errors; targeted test
  annotations corrected. Final `scripts/check.sh` exits 0: lock, format, lint,
  types, 1,797 Python tests, 45 Cockpit tests, wheel/sdist and plugin builds.
  Changed documentation links, parity-table structure and git whitespace pass.
  No host/live checks or production operations. HTTP traversal review/pagination
  and bounds remain API-006 scope; runtime HTTP routes remain planned.)

- [x] API-003 Extract guarded command services and close verification lock gaps
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-003-extract-guarded-commands.md).
  Extracted all operational command orchestration into immutable typed services;
  CLI remains parsing/rendering plus bootstrap config loading. Preserved domain
  engines, refusal ordering, partial errors and exact report/journal provenance.
  Decision 110 closes the baseline verification lock gap: every non-estimate
  mode holds common lock and storage preflight through scope/hash/report/catalog
  merge. Spawned-process interleaving preserves unrelated failures/instance state;
  phase tests prove lock ownership and all-mode unproven-storage refusals.
  Doctor probes and confirmed initialization serialize without invalid sentinel
  preflight or nested locks. Sync interruption joins its transfer before release;
  quarantine still refuses unfinished work without implicit reconciliation.
  Reviewed AD-13–20, FS-02/03/19, TX-01–07, INV-006/007/012/015 and related
  ADRs; amended AD-17, offline verification and decision 40, plus architecture,
  CLI, schemas persistence prose, invariant links and Unreleased notes.
  Targeted sweeps: 113, 177 and 320 passing tests; final guard/provenance/
  interleaving/interrupt selection: 20 passed, 113 deselected. Initial test
  fixtures and two characterized rendering/refusal regressions corrected.
  `rtk proxy bash scripts/check.sh` exits 0: lock, format, lint, types,
  1,816 Python tests, 45 Cockpit tests, wheel/sdist and production plugin builds.
  Changed-document links, task dependencies/current pointer, parity matrix and
  git whitespace pass. No durable schema/dependency change or production/host
  operation. Full-only offline env handling remains API-004; HTTP/isolated
  executor and MCP remain planned. Next selected task is API-004.)

- [x] API-004 Isolate execution correlation and offline initialization
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-004-isolate-execution-context.md).
  ContextVar snapshots replace process-global run correlation; emission-time
  capture and reserved fields preserve authoritative run/request/operation IDs.
  Concurrent scopes, exceptions and reused workers restore earlier context;
  sync's existing producer explicitly copies it. Daemon logging is configured
  once, while the isolated CLI retains per-invocation configuration.
  Exact registered opaque credentials are removed from nested diagnostics,
  logs, Problem output and exception string/repr paths, including late
  registration and mutable legacy contexts. All shared verification modes
  construct no Hub client/credential and never write the environment.
  Startup-only offline initialization is tested in child processes; it does
  not enforce no-IP sockets. API-008/014 still own the isolated executor.
  Reviewed AD-19, INV-002/005/006/007/012/015 and related ADRs; decision 111
  amends decision 64, offline verification, decision 110's deferred guard,
  AD-19 and scheduling provenance. API/server, architecture/invariants, CLI,
  security, schema provenance, original-plan amendments and Unreleased agree.
  Durable invocation_mode remains execution-host evidence, with submitter
  metadata deferred to receipts. Focused suites pass 310 and 163 tests; sync
  propagation/interruption selection passes 6 (113 deselected).
  `rtk proxy bash scripts/check.sh` exits 0 on its first full attempt: lock,
  formatting, lint, types, 1,835 Python tests (40 deselected), 45 Cockpit tests,
  wheel/sdist and production plugin build. Local links, task/current/dependency
  records, parity matrix, all 111 numbered decision/ADR records and whitespace
  pass. No durable schema/dependency, ASGI/MCP code or production operation;
  opt-in live/NFS/host checks did not run. Next selected task is API-005.)

- [x] API-005 Add strict server policy and verified bearer capabilities
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-005-server-config-and-bearer-auth.md).
  Added direct HTTPX and the optional FastAPI/Uvicorn server extra, preserving
  existing locked versions; Python 3.14 resolves four new runtime packages.
  Strict frozen ServerConfig and a separate example define default private Unix
  plus loopback TCP, explicit enable flags, TLS/proxy policy, bounds and restart
  semantics. Fresh archive snapshots pin startup root/UUID and retain existing
  secret-free policy fingerprints. Descriptor-pinned no-follow credential reads
  enforce owner/group/mode/single-inode/size/stability rules; fixed nonsecret
  principals and three-slot digest comparisons separate REST writer/reader and
  future MCP classes. Configured unusable/duplicate sources fail startup;
  optional unconfigured classes grant no access. Reusable FastAPI dependencies
  retain strict original-header checks and safe 401 challenge/403 behavior.
  HFAPI001–004 join the central exit-10 taxonomy. Exact opaque values register
  for redaction; no receipt or token-derived identity is introduced.
  Decision 112 records material transport/security/lifecycle correctness and
  official sources; decision 108/FW, INV-001–003/010/013, API/server,
  configuration/security, CLI taxonomy, README, historical plan and Unreleased
  agree. Strict socket-mode float coercion found in review was fixed before
  the gate. Focused configuration/property/auth/adversarial/transport sweep:
  360 passed. `rtk proxy bash scripts/check.sh` exits 0 on its first full
  attempt: locked server-extra sync, format/lint/types, 2,009 Python tests
  (40 deselected), wheel/sdist, real isolated offline locked base/server wheel
  install/import/help/version checks, 45 Cockpit tests and production build.
  Links, task/current/dependencies, parity matrix, 112 decision/ADR records and
  whitespace pass. No durable archive schema, runtime REST route/listener,
  MCP dependency/import, production operation or deployment; live/NFS/host and
  additional build-marker checks did not run. Next selected task is API-006.)

- [x] API-006 Serve bounded authenticated metadata with one lifespan
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-006-fastapi-lifecycle-and-reads.md).
  Implemented eight metadata parity rows, health/schema/optional docs and lazy
  foreground serve; 21 rows and public CLI-client migration remain planned.
  Every HTTP surface authenticates before routing/body/error handling, with
  strict transport/bounds, safe typed problems and authoritative correlation.
  Shared no-follow metadata readers harden status/list/latest-report/catalog/
  inspection/health/estimate paths without archive repair or false confidence.
  Exact publication locators retain their declared bases; bounded parsed-evidence
  streams and content-bound cursor continuation preserve identity and refusal.
  One private Unix/TCP application/lifespan/registry/pool is exercised with
  disposable TLS sockets and CA rejection. Typed startup errors retain their
  classification; serve's no-success-Envelope exception is explicit. Existing
  socket names are preserved, cleanup proves its created inode and lock inodes
  remain. Decision 113/112 amendment, invariant/architecture/API/server/CLI/
  security/consumer, README, plan and Unreleased contracts agree; no dependency
  or durable archive schema change. Focused selections: 227 app/config/auth,
  181 metadata, 76 adversarial HTTP, 9 bootstrap, 22 estimates and final 96
  HTTP/bootstrap tests pass. First gate stopped on formatting; second found a
  damaged-reference estimate count regression; third found a worker-callback
  capacity race. Estimator and deterministic delayed/cancelled-worker ownership
  regressions fix both. Fourth `rtk proxy bash scripts/check.sh` exits 0:
  locked sync, format/lint/types, 2,133 Python tests (40 deselected), wheel/sdist,
  isolated locked base/server install/import/help/version, 45 Cockpit tests and
  production build. Links/current/dependencies, 8 implemented/21 planned parity
  rows, 113 decision/ADR records and whitespace pass. Real socket/TLS tests use
  test-only OpenSSL certificates; live/NFS/installed-host and extra build-marker
  suites did not run. No production listener/archive operation, deployment,
  push, merge or tag. Next selected task is API-007.)

- [x] API-007 Persist non-resuming operation receipts and bounded observation
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-007-operation-receipts-and-idempotency.md).
  Independent schema-1 local receipts are the durable principal/hashed-key/request
  authority before admission returns; no raw key, credential or replayable body
  is stored. Atomic fsync/rename, strict duplicate/version checks, protected
  pinned files and shared store locks preserve evidence across faults and races.
  Exact terminal Envelopes retain domain identity and exit; bounded sequenced
  events report dropped prefixes. All REST readers may observe history/results,
  while key lookup stays in the fixed credential-class namespace across rotation.
  Five bounded authenticated GET surfaces work without fresh archive policy or
  domain execution. State/archive overlap refuses before default state creation.
  Count/space reservations refuse new admission rather than evicting unexpired
  30-day bindings; uncertain/nonterminal/interrupted history never ages out.
  Startup opens history without replay/classification; exact-worker reconciliation
  and heavy execution remain API-008, command POST routes API-009/010.
  Decision 114, amended 109/FW/AD-12/14/16, invariant enforcement links and all
  API/server/schema/security/recovery/configuration/CLI/rollback contracts agree.
  Actual isolated predecessor a856397/0.1.10 and tagged v0.1.3 wheel drills both
  lacked the operation reader/command (exit 2), preserved three state files
  byte-for-byte and created no archive; rollback must preserve history and cannot
  infer nonexecution. Final focused store/storage: 161 tests; broader selection:
  414; HTTP/config: 178; adversarial: 44. The first full gate passed 2,222 tests;
  two added ENOSPC fsync acceptance cases then passed without source changes.
  The definitive `rtk proxy bash scripts/check.sh` exits 0: lock/format/lint/types,
  2,224 Python tests (40 deselected, 118.15 seconds), 0.1.10 sdist/wheel, isolated
  locked base/server install/import/help/version, 45 Cockpit tests and production
  build. No gate attempt failed. Final links/current/dependencies, 9 implemented /
  20 planned matrix rows, 114 decision/ADR records and whitespace pass. Live/NFS,
  installed-host and extra build-marker suites did not run. No production archive/
  listener operation, deployment, push, merge or tag. Next selected task is API-008.)

- [x] API-008 Run one bounded lane and the private verification executor
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-008-bounded-runner-and-offline-executor.md).
  One bounded FIFO lane retains durable admission, frozen context/policy and one
  absolute host-monotonic queue/lock deadline. Service-owned flock hooks compare
  fresh policy before preflight/mutation, without parent/nested acquisition;
  zero wait is one idle attempt. Metadata stays independent and responsive.
  A strict peer/path-checked bounded verification-only protocol delegates real
  shared verification and complete report/catalog ownership. Exact operation /
  archive/fingerprint and result-reference hash/bytes precede trusted progress
  or completion. Fresh admissions probe availability; matching retries bypass it.
  Restart imports exact terminal evidence or reserves the lane for a live owned
  worker without replay. Unavailable/unsafe status preserves active receipts
  and blocks execution across restarts, while trusted missing/interrupted status
  permits interruption. Repeated cancellation/drain joins work and sync producers
  before store/instance/archive ownership ends. Decision 115 and affected ADR,
  invariant, architecture/API/server/schema/security/runbook records agree.
  No new dependency, durable family, public POST route or MCP is introduced.
  Focused selections: owned final 71 tests, broader 187, root HTTP/verifier 63,
  real producer drain 1 (119 deselected), corrected process startup 3 (42
  deselected). The first full gate passed 2,307 tests, but a subsequent real
  FD-3 activation probe found trusted imports opened /dev/urandom before the
  inherited-FD audit. Strict activation/environment/descriptor validation now
  precedes those imports; positive activation and extra credential-FD refusal
  regressions cover it. The corrected manual probe is available, exits 0,
  creates no archive/operation records and emits no stdout/stderr. Definitive
  `rtk proxy bash scripts/check.sh` exits 0: lock/format/lint/types, 2,309 Python
  tests (40 deselected, 124.99 seconds), 0.1.10 sdist/wheel, isolated locked
  base/server install/import/help/version, 45 Cockpit tests and production build.
  No gate attempt failed; the separate positive probe exposed the corrected bug.
  Final links/current/dependencies, 9 implemented / 20 planned rows, 115 decision /
  ADR records and whitespace pass. Live/NFS, installed-host and extra build-marker
  suites did not run. Actual systemd credential-free/no-IP acceptance remains
  API-014; a library offline flag alone is insufficient. No production archive /
  listener operation, deployment, push, merge or tag. Next selected task is API-009.)

- [x] API-009 Admit typed sync, verification, planning and diagnostics
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-009-sync-verification-and-diagnostics-api.md)).
  Eight more parity rows implement strict authenticated command DTOs, four keyed
  admission-only 202 jobs and immediate installed validation. Explicit role/body
  boundaries prevent implicit probes, arbitrary paths and credential overrides;
  shared grammar codes remain distinct from wire-shape failures. Selector sets
  normalize before hashing while installed revision/execution order is retained.
  Matching concurrent retries admit/probe/execute once and precede fresh policy/
  verifier checks. Exact terminal Envelopes preserve partial/domain exits.
  Real fake-Hub sync publishes, reobserves without download and refuses unknown
  journals before Hub contact; lost HTTP acknowledgement keeps producer/flock
  ownership and yields one exact result. Every actual verify mode delegates
  privately, with unavailable isolation refusing rather than falling back.
  Trusted startup Hub-file authority is separate from API bearers. Pure bounded
  candidate hooks compare six installed authority fields; current HTTP candidates
  remain refused until API-012. Decision 116, amendments 108/112/115, invariant
  enforcement and API/server/configuration/security/architecture/CLI/operator,
  README/plan/Unreleased records agree. Reviewed AD-01–03/17–19, TX-07 and
  INV-001/002/004/006/007/012–015 without changing domain safety or durable shapes.
  Focused model/runner: 55 passed in 2.04 seconds; adversarial HTTP: 109 in 9.40;
  real HTTP/domain/bootstrap: 19 in 3.42. Focused primitive validation and fixture/
  expectation corrections preceded the gate. First full
  `rtk proxy bash scripts/check.sh` exits 0: lock/sync, 321 formatted files,
  lint/types, 2,473 Python tests (40 deselected, 137.10 seconds), 0.1.10 sdist/wheel,
  locked isolated base/server install/import/help/version, 45 Cockpit tests and
  production build. No gate attempt failed or required a fix. Final links/current/
  dependencies, 17 implemented / 12 planned rows, 116 decision/ADR records and
  whitespace pass. No new durable format/dependency/MCP or production operation;
  live/NFS/installed-host and extra build-marker suites did not run. Maintenance,
  clients/candidates and installed hardening remain later tasks. Next is API-010.)

- [x] API-010 Expose explicit guarded maintenance and initialization
  (2026-10-17, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-010-guarded-maintenance-api.md)).
  Ten typed fixed resources separate prune/purge/recovery/quarantine preview and
  apply, plus repair and initialization, through shared keyed admission and exact
  terminal Envelopes. No posted plan, omitted mode or preview grants apply authority.
  Writer side effects revalidate fresh installed policy/scope/proof under the
  shared service lock; queued managed purge and changed two-ID quarantine evidence
  refuse while preserving every file. One-round prune/current refs, canonical-cache
  deletion, original manifest/audit, commit recovery and exact repair/generation/
  168-hour grace remain unchanged. Repair audit reasons redact registered API/Hub
  secrets after credential resolution. Initialization alone requires the disabled
  restart-only maintenance gate before body/POST retry, strict confirmation and
  configured root/UUID restated; old GET history stays observable. Synthetic tests
  prove no implicit health/startup/recovery initialization. Decision 117 and
  116/AD-16/17/20 amendments, FS-21's explicit-operation clarification, invariants
  and API/server/CLI/security/architecture/runbook/README/plan/Unreleased agree.
  Reviewed AD-06/13–17/20, FS-14/19/21–23, TX-06/07 and related invariants;
  RET-011 remains separate. Focused model/service/runner: 143 passed in 5.11
  seconds; adversarial: 127 in 15.19; seven real HTTP/shared-domain cases pass.
  First full `rtk proxy bash scripts/check.sh` exits 0: lock/sync, 327 formatted
  files, lint/types, 2,685 Python tests (40 deselected, 163.41 seconds), 0.1.10
  sdist/wheel, locked isolated base/server install/import/help/version, 45 Cockpit
  tests and production build. No functional fix/gate failure; one module-docstring
  correction had supplemental checks and was included in final builds/installs.
  Final links/current/dependencies, 27 implemented / 2 planned rows, 117 decision/
  ADR records and whitespace pass. No new durable shape/dependency/MCP or
  production operation; live/NFS/installed-host and extra build-marker suites did
  not run. Clients/candidates/installed hardening retain later gates. Next is API-011.)

- [x] API-011 Add independent typed client and reader configuration
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-011-typed-client-and-client-config.md)).
  Separate strict schema-1 client settings select one endpoint group and protected
  API-only source, optional CA/expected UUID and finite observation budgets without
  archive TOML/mount/Hub credentials or optional server/MCP frameworks. CLI selection
  options are stored; runtime migration remains API-012/013. Verified TLS/Unix,
  no redirects/ambient proxy/netrc, strict bounded streamed wire/Envelope versions,
  safe exact operation links and explicit capabilities preserve one authority.
  Page walks refuse cycles/duplicate identities while retaining failed domain
  Envelopes; digest tracking is bounded without aggregating rows. Receipt/result/
  events retain admitted fingerprint, distinct request/operation/domain identities
  and exact event gaps. Keys exist before POST; unusable acknowledgement preserves
  key/route and HFAPI020 without automatic replay. Validated remote problems retain
  server taxonomy and key/route too; a valid 500 cannot prove nonexecution.
  HFAPI017/018 exit 10 and HFAPI019/020 exit 20 distinguish config/protocol from
  connectivity/uncertainty. Decision 118 and 108/112/114 amendments, reviewed
  INV-001–003/006/008/012–014 / FS-12 / AD-21 and affected contracts agree.
  Client setup/TOML example, API/CLI/config/security/invariants/architecture/recovery,
  README/router/plan/Unreleased and actual base imports are documented.
  Core/adversarial: 127 passed in 0.78 seconds; adversarial alone: 113 in 0.73;
  config/real Unix/TCP/TLS: 40 in 2.55. Actual predecessor 66d85a3/Python 3.14.6
  wheel rejects the new option (exit 2), current local version accepts it (0),
  settings stay byte-identical and no API/Hub/archive operation occurs. The first
  scratch Python 3.12/cache mismatch was resolved in a separate locked Python 3.14
  environment without code/dependency/network changes. First full
  `rtk proxy bash scripts/check.sh` exits 0: lock/sync, 337 formatted files,
  lint/types, 2,852 Python tests (40 deselected, 163.45 seconds), 0.1.10 sdist/wheel,
  actual locked base/server install/import/help/version including client imports,
  45 Cockpit tests and production build. No gate failure/correction or post-freeze
  source change. Final links/current/dependencies, 27 implemented / 2 planned rows,
  118 decision/ADR records, example and whitespace pass. No new dependency/durable
  archive shape/MCP or production operation; live/NFS/installed-host and extra
  build-marker suites did not run. Next selected task is API-012 pending.)

- [x] API-012 Migrate reader CLI and candidate validation/planning
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-012-migrate-read-cli-and-candidates.md)).
  Actual reader modes use authenticated HTTP without local writer loaders,
  archive fallback or required client archive paths. Exact server Envelope IDs,
  times, warnings/errors/domain exits survive one terminal rendering. Complete
  bounded page reconstruction and inventory/revision joins preserve unmanaged/
  empty rows and refuse inconsistent current publication identity. Help/local
  version and explicit local validation stay bootstrap; non-inspect missing root
  retains usage exit 2 and legacy config/Hub overrides refuse before file access.
  Writer candidate content validation separates validity from false/unknown
  compatibility without credentials/Hub/probes; installed-authority planning
  rechecks all six fields after waiting, uses installed credentials/fingerprint,
  binds exact TOML text and preserves old absent-candidate key digests. Explicit
  null refuses. CP-11 host installation/backups remain outside REST. All 29 HTTP
  parity rows are implemented; mutating CLI and host/MCP acceptance remain gated.
  Required missing-UDS testing exposed a real dependency socket leak before the
  gate. Public Unix HTTPX/HTTPCore interfaces now close owned failed sockets and
  response resources while maintained HTTPCore retains HTTP framing/pooling and
  TCP/TLS stays on HTTPX. Direct HTTPCore retains locked 1.0.9 without a new
  package/version; no private mutation/global patch/IP fallback/warning suppression.
  Decision 119 and 087/108/112/116/118, AD-21/framework amendments record FW-04
  correctness rationale, reviewed invariants/CP-11 and affected contracts/examples.
  Focused candidate HTTP: 55 passed in 7.28 seconds; reader CLI: 84 in 16.65;
  local validation: 25 in 0.84; final CLI integration: 28 in 3.61; transport: 20
  in 0.55; real Unix/TCP/TLS: 3 in 2.14. Two legacy fixture-overlap assertions
  were corrected before the gate, with all 13 query cases then green. First full
  `rtk proxy bash -c 'bash scripts/check.sh > .scratch/api-012-gate.log 2>&1'`
  exits 0: lock/sync, 345 formatted files, lint/types, 2,953 Python tests
  (40 deselected, 195.16 seconds), 0.1.10 sdist/wheel, locked isolated base/server
  install/import/help/version, 45 Cockpit tests and production build. No gate
  failure/correction/retry or post-freeze source change. Final links/current/
  dependencies, 29 implemented / 0 planned rows, 119 indexed decision/ADR records
  and whitespace pass. No durable format/MCP or production operation; live/NFS/
  installed-host and additional build-marker suites did not run. Next selected
  task is API-013 pending, after this package's commit.)

- [x] API-013 Migrate operational CLI and preserve resumable observation
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-013-migrate-write-cli-and-operation-waiting.md)).
  Operational modes use typed HTTP without local mutation backends or archive
  fallback. Pure request/bootstrap extraction retains shared service exports and
  cold CLI imports load no archive/Hub/storage executors. Default command/wait
  output is the exact terminal server Envelope; show/lookup preserve metadata
  Envelopes. Explicit detach identifies admission separately without fabricated
  command outcome/exit. Validated key before POST and accepted-ID stderr handles
  survive quiet; bounded sequenced events/gaps render one escaped plain stderr
  line. One absolute status/event/result observation deadline retains original
  handles and HFAPI019/20 on timeout/SIGINT, HFAPI020 before usable acknowledgement,
  and original taxonomy on other errors. Retained-key 5xx warns work may continue;
  client departure never cancels/replays. Initialization obtains optional UUID
  from authenticated inspection while retaining explicit root/confirmation and
  server maintenance/DTO guards. No-confirm submits nothing; failed inspection
  stays exact, otherwise local refusal retains inspection/UUID/fingerprint.
  Pre-gate compatibility fixes preserve verification/quarantine HFARG001 grammar
  and remote private-worker crash HFAPI015/20 with every preservation assertion.
  Decision 120 and AD-16/17, 114/117/118/119 amendments plus affected invariants,
  original plan/CLI/client/API/server/security/configuration/architecture/runbooks,
  README/Unreleased agree. Focused helpers: 26 passed in 1.13 seconds; shared
  extraction: 87 in 8.38; writer CLI: 44 in 11.60; verification/crash/services:
  159 in 71.56; readonly/init/quarantine: 173 in 64.68; new adversarial: 8 in 5.70.
  Threaded real private-socket fixtures prove framed peer/guarded service behavior,
  not installed OS isolation. First full
  `rtk proxy bash -c 'bash scripts/check.sh > .scratch/api-013-gate.log 2>&1'`
  exits 0: lock/sync, 351 formatted files, lint/types, 3,031 Python tests
  (40 deselected, 303.11 seconds), 0.1.10 sdist/wheel, actual locked base/server
  installation/import/help/version, 45 Cockpit tests and production build.
  No gate failure/correction/retry or post-freeze source change. Final links/
  current/dependencies, 29 implemented parity rows, 120 unique indexed decision/
  ADR records and whitespace pass. No durable schema/dependency/MCP or production
  operation; live/NFS/installed-host and extra build-marker suites did not run.
  Next is API-014 pending after this commit; installed unit/no-IP/caller and REST
  acceptance remain gated.)

- [x] API-014 Package activated executors and durable scheduled observation
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-014-systemd-and-deployment-integration.md)).
  Named Unix/optional TCP activation feeds one application/lifespan; a separate
  unprivileged verifier validates inherited descriptors before shared imports,
  resolves trusted account/euid peers and carries offline/no-IP/source-masking
  policy. No manager `%U`, credential import or online fallback in the verifier;
  custom source paths require explicit masks/probes.
  Existing sync/verify service names/calendars, disabled verify timer, OnFailure,
  target/mount and shared runtime lock inodes remain. API-only AF_UNIX scheduled
  clients use independent strict schema-1 handles: key fsync before sole POST,
  endpoint/expected UUID/REST-writer binding, accepted ID and lookup-only recovery.
  Repeated finite windows preserve oneshot lifetime; exact terminal Envelope/exit
  alone permits owned pending removal. Same-class rotation can recover. Actual
  SIGINT/SIGTERM subprocesses preserve exact bytes/exclusive ownership with
  HFAPI019/20, no POST or terminal stdout; main restores handlers and library
  import/calls install none. Installer dry-run, locked server-extra smoke and
  two-tree switch/rollback fixtures retain evidence and hold a noncreating flock
  through switching; actual executor/cgroup accounting and target observer
  compatibility gate changes. Review corrected noncanonical archive aliases,
  ambiguous task accounting and the pending-state scan default; initial focused
  smoke also corrected a `str`/`Path` call before final 63 installer/probe cases.
  Final installed smoke: 2 passed in 6.73 seconds; activation/runtime: 99 in 37.03;
  scheduler/unit/model: 247 in 3.76; nine unit files verify without diagnostics
  under systemd 257. Actual installed predecessor `a01875c` lacks the observer
  module and preserves schema 1/future 2 bytes; current reads 1/refuses 2 at
  HFAPI014/20, using locked offline CPython 3.14.6 fixtures with no archive operation.
  Decision 121 and scheduling/offline, AD-17, 061/065/115/120/framework amendments,
  affected invariants, original plan/cancellation, server/client/API/schema/CLI/
  configuration/security, deployment/recovery/operations/agent guidance and
  README/Unreleased agree. First full gate was interrupted at exit 130 after a
  stale shipped-example assertion (`rest-writer`→`hfcache.api`), with no final
  suite count; assertion-only correction passed 1 test in 0.27 seconds. Definitive
  `rtk proxy bash scripts/check.sh > .scratch/api-014-gate.log 2>&1` exits 0:
  lock/sync, 360 formatted files, lint/types clean, 3,223 Python tests
  (40 deselected, 349.85 seconds), 0.1.10 sdist/wheel, actual locked isolated
  base/server install/import/help/version, 45 Cockpit tests and production build.
  No post-gate source change. Final links/current/dependencies, 29 implemented
  parity rows, 121 unique indexed decision/ADR records and whitespace pass.
  New private handle only; archive/receipt formats and dependencies unchanged.
  No MCP, production service/archive operation, deployment, push/merge/tag.
  Real installed socket/cgroup/no-IP/credential-source/SELinux/NFS/hardening and
  verify-calendar acceptance remain explicit operator holds; live/NFS and extra
  build-marker suites did not run. Next is API-015 pending after this commit.)

- [x] API-015 Preserve Cockpit workflows through guarded API clients
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-015-cockpit-api-client-compatibility.md)).
  Fixed service-identity transient CLI commands use local client TOML/socket and
  systemd API-only `hfcache.api`, never Hub/browser bearer authority. Strict
  complete/coherent schema-1 terminal parsing preserves failures and safe upgrade
  guidance. Independent UTF-8 framing bounds terminal JSON to 16 MiB, progress
  lines to 8 KiB, diagnostics/feeds to 64 KiB and feeds to 200 whole lines; validated
  handles survive display eviction. Abort/callback failure detaches the view,
  never cancels accepted work. Sync observer stop shows uncertainty/reconnect,
  without automatic recovery or no-change claims. Copied lookup keys are quoted
  and use `--`, including leading `-`/`~`; dashboard inspects server version.
  Unit/action allowlist preserves full sync/verify services, sync-timer-only
  controls and no target/init UI. Persistent root config flock and exact 1 MiB
  candidate/base guards protect no-follow editor reads, compatible assessment,
  required preview, atomic predecessor/install and exact installed fingerprint
  confirmation. Edits invalidate readiness; incompatible/unknown authority blocks
  plugin install. Install/confirmation failure requires reload and never invents
  success, prior-file preservation or rollback. Admitted snapshots/server fresh
  lock proof remain authoritative. Decision 122 and 087/089/091/092/119/120/121,
  CP-01–14/INV-002/003/006 and affected operator/client/config/security/contracts,
  README/Unreleased agree. Focused runner 35, envelope/unit 19 and candidate 59
  cases pass; actual disposable Bash/flock/cmp/fsync/rename guards fake only the
  systemd leaf. Standalone complete Cockpit gate passes 127 tests/2.035 seconds,
  lint/style/types and production build. Source and decompressed production
  searches find no bearer/Authorization/API token-file/Hub-token/environment
  handling, while expected API name/socket/client path remain. First full
  `rtk proxy bash scripts/check.sh > .scratch/api-015-gate.log 2>&1` exits 0:
  lock/sync, 361 formatted files, Ruff/types clean, 3,223 Python tests
  (40 deselected, 352.53 seconds), 0.1.10 sdist/wheel, actual locked isolated
  base/server install/import/help/version, 127 Cockpit tests/2.093 seconds and
  production build/1,171 ms. No gate correction/restart or post-gate source change.
  Final links/current/dependencies, 29 implemented parity rows, 122 unique indexed
  decision/ADR records and whitespace pass. No durable JSON/dependency/MCP or
  production operation/deployment/push/merge/tag. Actual browser/PAM/credential/
  cgroup/custom masks/hardening/SELinux/NFS/drain/verify-calendar checks remain
  operator holds; live/NFS and extra build-marker suites did not run. Next is
  API-016 pending after this commit; REST acceptance still gates all MCP work.)


- [x] API-016 Prove complete REST and CLI parity before MCP
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-016-rest-acceptance-gate.md)).
  All 29 semantic modes now cite concrete CLI/API functions and selected parameter
  cases in an independent manifest/AST gate. An independent inventory checks all
  34 method/path pairs (33 without interactive docs), bearers before body receive,
  and mixed read/write roles without admission. Native Unix/public TCP prefixes
  share one app/lifespan/registry: corroborated trusted peer and absolute Unix
  local scope jointly select native prefix/proxy-TLS exceptions, while missing/
  malformed/numeric local evidence refuses. Request-local links and copied native
  schema views retain deterministic public OpenAPI and original operation/key/
  admitted policy/result identities. Actual locked Uvicorn source and disposable
  Unix/TCP fixtures prove the predicate; no forwarded-header authority or new
  client setting. Complete size-one page walks retain empty/unmanaged inventory
  and exact publication/run/operation IDs. Five packaged examples use strict
  independent loaders; current docs/anchors and a cold disabled app prove no MCP
  import or state creation. Historical runbook aliases/logs remain explicitly
  historical; current reconnect keys are quoted after `--`.
  Focused final transport/read/command/client/bootstrap sweep: 130 passed in
  47.31 seconds; final new cases: 14 in 9.44; parity/positive CLI: 68 in 6.68;
  broader CLI: 154 in 61.20; security/examples: 19 in 3.23; final parsed matrix/
  anchors: 63 in 1.89. Fresh actual installed predecessor `9ba89cf` and working-tree
  base wheels (both application 0.1.10, distinct hashes) read schema 1/refuse
  future 2 across seven families, all 28 cases preserving bytes without network,
  listeners or archive operations. Decision 123 and 113/118/121/122 amendments,
  INV-003/006/010/011/012–014, API/server/client/config/security/CLI contracts,
  README/Unreleased and operator runbook boundaries agree.
  First full `rtk proxy bash scripts/check.sh --with-build > .scratch/api-016-gate.log 2>&1`
  exits 0: lock/sync, 368 formatted files, Ruff clean, Pyrefly 0 errors
  (11 suppressed, 57 warnings not shown), 3,324 Python tests
  (40 deselected, 358.69 seconds), 0.1.10 sdist/wheel and actual locked isolated
  base/server install/import/help/version. Complete Cockpit lint/style/types,
  127 tests in 2.134 seconds and production build in 1,224 ms pass; required extra
  wheel smoke passes 4 tests (3,360 deselected, 4.48 seconds). No gate correction,
  restart or post-gate source change. Final links/anchors/current/dependencies,
  29 implemented rows, 123 unique indexed decision/ADR records and whitespace pass.
  REST repository acceptance is complete; MCP-001 is next pending after this
  commit, with no MCP dependency/import/route/tool or research implementation yet.
  No dependency/config/durable shape or production operation/deployment/push/merge/
  tag. Live Hub/NFS and actual systemd/cgroup/no-IP/credential/custom-path/browser/
  PAM/SELinux/drain/rollback/verify-calendar proof remain deployment holds in
  Operator handoff 16/17; repository acceptance does not assert those passed.)


- [x] MCP-001 Mount optional authenticated FastMCP after REST acceptance
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/mcp-001-mount-authenticated-fastmcp.md)).
  Optional standalone FastMCP/fastmcp-slim 4.1.1, MCP/mcp-types 2.3.0 and
  HTTPX2/HTTPCore2 2.13.1 add 53 packages to the 94-package lock without changing
  existing versions. Actual base/server/server+MCP wheel profiles preserve cold
  CLI/import/help/version isolation, disabled factory without MCP import/path
  creation, missing enabled runtime HFCFG005 and enabled mounted factory.
  Production supported verifier accepts only shared protected MCP-reader
  authority; disabled mode resolves no MCP source. Canonical stateless `/mcp/`
  finite JSON retains no legacy sessions/resumption; every method authenticates,
  no session ID grants access and no tools/resources/prompts/commands are added.
  One trusted public/native projection prevents prefix collisions from confusing
  REST/MCP auth or static writer/body policy. Safe alias redirect, shared strict
  JSON/empty-body/no-query policy, pre-body reserved bounded capacity, buffered
  sanitized/capped responses and fixed JSON-RPC error projection contain SDK
  behavior. Stable closed-vocabulary `mcp.diagnostic` emits fixed text, original
  severity and bounded sanitized logger provenance, never raw SDK input/exception
  formatting; handlers restore. REST-before-MCP startup and reverse teardown
  preserve ownership/failure cleanup. Explicit installer --with-mcp is build/stage
  only and default remains server-only; named source needs deliberate API-service
  delivery, never worker credentials. Rollback deliberately disables MCP before
  server-only/pre-MCP startup, with no migration/fallback or target package change.
  Focused actual mounted 51 passed in 10.78 seconds, direct+mounted 63 in 10.25,
  REST 113 in 17.97, CLI 154 in 60.20, installer 40 in 30.36, examples/docs 7
  in 1.34 and final parsed matrix/anchors 63 in 1.02. First full gate exits 1:
  9 failed, 3,385 passed, 40 deselected in 380.11 seconds, all remaining test-only
  HTTPX/HTTPX2 private-transport borrowers. Shared public ApiCli exchange replaces
  those wrappers; zero private borrowers remain and 79 focused cases pass in
  6.80 seconds with interruption/retry/restart/no-second-POST proof preserved.
  No runtime/semantic correction; first log is retained and build/install/Cockpit
  were not reached. Definitive
  `rtk proxy bash scripts/check.sh > .scratch/mcp-001-gate-rerun.log 2>&1`
  exits 0: lock/both-extra sync, 373 formatted files, Ruff clean, Pyrefly 0 errors
  (11 suppressed, 59 warnings not shown), 3,394 Python tests (40 deselected,
  377.89 seconds), 0.1.10 sdist/wheel and actual locked isolated base/server/
  server+MCP install/import/help/version checks. Cockpit lint/style/types,
  127 tests in 2.152 seconds and production build in 1,203 ms pass. No source
  change after definitive acceptance. Decision 124, 064/108/112/113/123/framework/
  AD-21 amendments, FW-03/04 and INV-002/003/012–016, logging/original/active plan
  and current MCP/server/API/config/security/CLI/release/README/Unreleased agree.
  Final links/anchors/current/dependencies, all 29 REST modes, 124 unique indexed
  decision/ADR records and whitespace pass. No config/durable/domain authority
  change or production operation/deployment/push/merge/tag. MCP-002 is next pending
  after this commit; curated tools/side-effect proof and operator holds 16–18
  remain separate. Live Hub/NFS and extra build-marker suites were not run.)

- [x] MCP-002 Expose nine typed metadata tools through a narrow read capability
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/mcp-002-curated-read-only-tools.md)).
  Exactly nine explicit async tools receive only a narrow read protocol; app-owned
  bounded offload invokes shared safe metadata readers. No resources/prompts,
  SDK app/request capability, commands, Hub/credential/write helper or arbitrary
  path/URL input. Typed schema-1 MetadataRead retains fresh query/archive/policy
  identity and domain Envelope, while report headers keep original run identity,
  fingerprint and times. Explicit manifest/report projections preserve complete
  headers/totals and require collection reconstruction before durable validation.
  Exact publication reads never substitute current. Inventory cursors bind
  canonical selected rows/filter/policy, with fresh per-page headline/warnings;
  deterministic free-space drift preserves continuation and nested warnings.
  Immutable artifact cursors bind all sanitized headers/collections, including
  unreturned data. A two-registered-string swap proves visible-source binding
  stability; encoded numeric literals are scrubbed in source. SHA suffix/order/
  duplicate selector equivalence preserves domain ordering. Unknown catalogs
  remain unknown and estimates never hash/persist confidence. Fixed safe ToolError
  projection covers backend and SDK validation/unknown names; exact-name guard
  precedes SDK lookup/tracing and refuses aliases. Registry/schema equality and
  successful/failed mounted state snapshots plus command/Hub/credential/hash
  tripwires prove the boundary beyond hints. Mounted 65 passed in 18.71 seconds;
  final mounted/pool 66 in 18.68; final guard/pool 3 in 2.03; direct/legacy 32 in 2.03;
  transport/core 63 in 14.82; parsed REST matrix/anchors 63 in 1.14. Shared pool
  proves off-loop work, saturation, responsive REST and lease release. First full
  `rtk proxy bash scripts/check.sh > .scratch/mcp-002-gate.log 2>&1` exits 0:
  lock/both-extra sync, 380 formatted files, Ruff clean, whole Pyrefly 0 (11 suppressed,
  59 warnings not shown), 3,481 Python tests (40 deselected, 401.60 seconds), 0.1.10
  sdist/wheel and all three actual locked isolated base/server/server+MCP
  installation/import/help/version checks. Cockpit lint/style/types, 127 tests
  (0 failures, 2.093 seconds) and production build 1,246 ms pass. No gate failure/
  correction/restart or post-freeze source change. Decision 125 and AD-10/15/21,
  113/124 amendments, FS-08–12/16, INV-005/007/008/012–016 and affected MCP/server/
  API/config/security/consumer/schema/architecture/README/Unreleased agree.
  Final links/anchors/current/dependencies, 29 unchanged REST modes, 125 unique
  indexed decision/ADR records and whitespace pass. No new dependency/durable/
  config or domain algorithm, whole-archive role, production operation/deployment/
  push/merge/tag. MCP-003 is next pending after this commit; MCP-004/API-017 and
  operator holds 16–18 remain separate. Live Hub/NFS and extra build-marker suites
  were not run.)

- [x] MCP-003 Prove mounted MCP authentication and read-only behavior
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/mcp-003-mcp-security-and-side-effect-tests.md)).
  Twenty-seven concrete test functions map threats to existing authentication,
  exact registry/closed arguments, whole-state preservation, secret/evidence/
  confidence containment and bounded mixed-interface/cancellation/drain controls.
  New mounted proofs snapshot all post-startup archive/control/config/credential/
  runtime paths/content/modes for each valid/invalid call, with explicit admission/
  command/Hub/credential/probe/archive-byte-hash tripwires. Atime is excluded and
  sanitized operational logs remain the documented exception. Three original
  report types × seven corruption classes preserve malformed evidence; numeric
  cursor substitution cannot fingerprint a hidden registered value. String output
  redacts and unsafe numeric output safely refuses; unexpected reader errors and
  logs expose no private input/bearer. Root evidence: 25 passed in 6.50 seconds,
  after a test-only missing fixture import correction before its actual proof run.
  Closed authority: 12 in 9.84, covering all nine tools × 17 mutation field sets,
  writer/generic/OpenAPI/hashed aliases and empty resources/templates/prompts.
  Optional legacy params.task can yield the same finite approved read without
  task handle/retained task/job/admission; unsupported task RPCs refuse. No claim
  that all optional SDK fields reject. Intentional sanitized-metadata cursor hashes
  and authentication digests are distinct from prohibited archive-byte hashing.
  Four mixed-interface/cancellation/drain cases pass in 4.52 seconds: fake-Hub
  sync and actual framed verification keep the common lock while MCP reads remain
  responsive, preserve three-root state and distinct correlation, and add no
  authority/confidence. Observer detachment may retain both request and worker
  leases until completion; MCP-first drain preserves ownership. Parsed anchors/
  REST parity: 63 in 1.04; AST resolves all 27 mapped functions. First full
  `rtk proxy bash scripts/check.sh > .scratch/mcp-003-gate.log 2>&1` exits 0:
  lock/both-extra sync, 383 formatted files, Ruff clean, whole Pyrefly 0 errors
  (11 suppressed, 59 warnings not shown), 3,522 Python tests (40 deselected,
  417.54 seconds), 0.1.10 sdist/wheel and all three actual locked isolated
  base/server/server+MCP installation/import/help/version checks. Cockpit lint/
  style/types, 127 tests in 2.112 seconds and production build in 1,234 ms pass.
  No full-gate failure/correction/restart or runtime source change. AD-21,
  124/125 and INV-002/003/007/010/016 are reviewed; current MCP/security proof
  links and residual assumptions amend evidence, without a new decision. Stale
  executor/profile availability wording is corrected. Final links/current/
  dependencies, unchanged 29 REST modes, 125 unique indexed decisions, mapped
  functions and whitespace pass. No role/tool/domain/FS/TX/dependency/config/
  durable change or production operation/deployment/push/merge/tag. MCP-004 is
  next pending after this commit; final API-017 and operator holds 16–18 remain
  separate. Live Hub/NFS and extra build-marker suites were not run.)

- [x] MCP-004 Complete protected MCP client guidance and repository acceptance
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/mcp-004-mcp-client-docs-and-acceptance.md)).
  Runnable protected-file example uses explicit HTTP transport, verified trust/
  optional CA, no redirect/proxy/executable inference, one overall deadline and
  finite byte/tool-read budgets. Exact wire/archive/policy/current/publication/
  projection/count/cursor checks retain summary-only discovery; valid duplicate
  dependency keys remain. No domain Envelope/receipt, payload transfer, complete
  manifest or local archive/Hub/REST fallback is invented. Guidance completes
  whole-archive restricted metadata, independent versions, stateless auto/legacy
  sessions, restart-only rotation, disabled profiles, costs and safe troubleshooting.
  Positive actual HTTP/custom-CA TLS/CLI example: 6 passed in 9.06 seconds.
  Negative client plus REST/auth/OpenAPI/34-route/real command/rotation/packaging:
  88 in 4.46. Credential replacement stays inert until restart; old/new MCP
  capability changes without REST drift. Default units/credential-free no-IP
  verifier/API-only scheduled timers remain. Source/logger/redirect/trust/size/
  deadline/wire/identity/cursor/locator/count failures remain fixed/safe with no
  credential/private-input echo. Anchors/REST parity: 63 in 1.03. Root AGENTS.md
  context/locked-extra development commands and README match; production profiles
  remain deliberately separate. Current client/server/API/config/security/
  consumers/MCP/invariants/ADR/index/README/Unreleased guidance agrees, correcting
  stale living availability prose while preserving historical evidence. First
  `rtk proxy bash scripts/check.sh --with-build > .scratch/mcp-004-gate.log 2>&1`
  exits 0: lock/both-extra sync, 387 formatted files, Ruff clean, whole Pyrefly
  0 errors (11 suppressed, 59 warnings not shown), 3,616 Python tests
  (40 deselected, 425.94 seconds), 0.1.10 sdist/wheel, all three actual locked
  isolated base/server/server+MCP installation/import/help/version profiles,
  including exact-nine enabled registry and zero resources/templates/prompts.
  Cockpit lint/style/types, 127 tests in 2.141 seconds and production build in
  1,268 ms pass; extra build-marker wheel subset: 4 passed, 3,652 deselected in
  5.66 seconds. No gate failure/correction/restart or post-freeze source/semantic
  change. AD-21, 124/125 and INV-002/003/008/010/011/012/013/016 are reviewed;
  no new decision/tool/role/backend/dependency/config/durable shape. Final links/
  current/dependencies, unchanged 29 REST modes, 125 unique indexed decisions and
  whitespace pass. MCP repository acceptance is complete; next API-017 remains
  pending after this commit. Application version 0.1.10 is unchanged source
  metadata, not a release/tag. No live Hub/NFS, production archive/service action,
  installation/deployment/push/merge/tag or version bump. Actual TLS/firewall/
  socket/credential/worker hardening/custom masks/cgroup/SELinux/NFS/browser/PAM/
  drain/rollback/verify-calendar acceptance remains in operator holds 16–18.)

- [x] API-017 Complete integrated REST/MCP acceptance and operator handoff
  (2026-10-18, this commit — [plan](plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](plans/tasks/api-017-final-integration-and-handoff.md)).
  All 21 work packages are completed in dependency order with same-package
  implementation/tests/docs/task/progress/current evidence; the committed REST
  gate precedes all MCP work. Final branch/history/artifact/security/invariant
  review found no direct operational CLI backend, arbitrary file service,
  generic MCP dispatch, secret artifact or unrelated RET-011/domain change.
  Lock grows 37 to 94 packages with no prior version changed; source metadata
  stays 0.1.10, without a release/tag. Final inspected archives contain no
  private credential/certificate/environment/scratch/venv artifacts. The 68
  runtime Python modules byte-match the tested final compatibility wheel.
  Real CLI Unix/TCP subprocess integration exposed a pre-gate fixed event-limit
  observer bug after durable sync success. Correct it to omitted adaptive limits
  and contiguous event draining through empty under the same absolute deadline
  and per-drain max_pages; explicit limits, domain Envelope identity, retention
  gaps and original handles remain. No new capability/role/schema/dependency.
  Final focused observer/socket/client/helpers: 176 passed in 24.54 seconds;
  prior broad integration: 375 in 78.05. Four socket cases exercise Unix/TCP ×
  page/retained-event caps of 1 with actual private full verification, reader
  metadata/history/writer refusal and no extra operation/leak. Standalone
  Cockpit check exits 0. Current quickstart replaces retired direct-backend
  commands with authenticated API setup and distinguishes reader diagnostic
  jobs. Anchor/parity selection: 63 passed in 1.07 seconds. Client/CLI/invariant
  contracts and ADR 118/120 record the existing-contract correction; no new
  decision. All 125 indexed decisions and affected invariant/FS/TX/framework/
  retention boundaries are reviewed; core archive algorithms remain unchanged.
  Fresh final-source installed-reader drill exits 0 across 42 cases with input
  bytes preserved: feature predecessor 9ba89cf/current each seven schema-1
  reads and seven future-2 schema-aware refusals (28), pre-feature 86f6e8b
  archive-1 read/archive-2 refusal (2), plus 12 unavailable service-reader cases
  (not schema-aware success/refusal). Exact command, final wheel/probe hashes
  and preliminary-versus-final artifacts are retained in the task; equal
  displayed version is not artifact identity or a deployed previous release.
  First required
  `rtk proxy bash scripts/check.sh --with-build > .scratch/api-017-gate.log 2>&1`
  confirms actual exit 0: lock/both-extra sync, 388 formatted files, Ruff clean,
  whole Pyrefly 0 errors (11 suppressed, 59 warnings not shown); 3,624 Python
  tests passed, 40 deselected in 442.05 seconds; 0.1.10 sdist/wheel and all
  three actual locked isolated base/server/server+MCP import/help/version
  installation profiles, including exact-nine enabled tools and zero resources/
  templates/prompts. Cockpit lint/style/types, 127 tests in 2.110 seconds and
  production build in 1,291 ms pass; extra wheel subset: 4 passed, 3,660
  deselected in 5.33 seconds. No full-gate failure/correction/restart or
  post-freeze source/semantic change. Final records/links/dependencies, all
  completed tasks, cleared current selection, unchanged 29 REST modes, unique
  decisions and whitespace pass. Plan completed; only its selection is cleared.
  Operator handoff 16–19 and deployment §17 retain credential/whole-archive,
  artifact/version, transport/firewall/socket, worker no-IP/source masks/custom
  paths/cgroup, NFS/SELinux/hardening, client monitoring and guarded state-
  retaining drain/rollback checks. Verification timer stays disabled pending
  calendar approval. Live Hub/NFS and installed host/browser/PAM probes were
  not run; the required build-marked subset was. No production archive/service
  operation, installation, deployment, release/version bump, push, merge or tag.)

## Local rootless rollout (OPS/REL, 2026-10-18)

- [x] OPS-014 Establish authorized local rollout guardrails without NAS writes
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-local-rootless-rollout.md),
  [task](plans/tasks/ops-014-local-rollout-guardrails.md)).
  New user authority permits reviewed local release/rootless Caddy runtime work,
  while NAS content/metadata writes and other-host changes remain forbidden.
  Decision 126 and environment/release/deployment/original-plan/invariant/ADR
  amendments record actual-executor guards and honest partial acceptance.
  Root's transition exits 0 at 14:08:47Z; root-owned 0700 backup preserves original units,
  drop-ins, target wants/config, reproducible root-owned 0600 transition and before/after
  snapshots with exact hashes in the task. No UID 981 process preceded mutation.
  Sync/verify timers are stopped, disabled and masked; both services inactive,
  MainPID 0/cgroups empty and masked. Existing lifecycle target stays active and
  SELinux Enforcing. Persistent mount override and client remount make actual
  NFS read-only without disconnect/unmount or NAS file I/O. Original local
  device 27/inode 2273 flock stays held by guard PID 653008; independent conflict
  proof and post-gate recheck pass. No lock replacement/truncation/removal or
  secret values printed. Required gate runs as tyler behind an empty read-only
  tmpfs covering NAS, protecting even default collection's live-mount import.
  Initial direct-redirection launch was denied by SELinux before startup; no
  policy relaxed. First executing gate failed three interactive event assertions
  (3 failed/3,621 passed/40 deselected/454.50s) because inherited INVOCATION_ID
  selected legitimate systemd `<6>` priority prefixes. Failed log retained; no
  production/test source change. Corrected exact command in task clears only
  test identity variables and confirms actual exit 0 at 14:25:55Z: lock/both-extra
  sync, 395 formatted files, Ruff clean, whole Pyrefly 0 errors (11 suppressed,
  59 warnings not shown), 3,624 passed, 40 deselected in 455.10 seconds;
  0.1.10 sdist/wheel and three actual locked base/server/server+MCP installation/
  import/help/version profiles. Cockpit lint/style/types, 127 tests in 2.027
  seconds and production build in 1,257 ms pass. Task retains final gate log
  SHA and service duration 8 minutes 19.635 seconds. No extra build-marker subset was
  required for this guard-only package. INV-003/010/011/014/015, AD-16/17, FS-18/19,
  decisions 65/75/79/121 reviewed; links/dependencies/current/unique decision 126/matrix and
  whitespace pass. No dependency/schema/domain/version/container/release/tag
  change. OPS-015 next pending until this commit; no later task activated.
  Live sync/full-verify/NAS-write/probe/hardening/other-host acceptance remains
  forbidden and NOT RUN. No production switch, container startup, merge/tag/push,
  registry publication or ACME issuance. Operator handoff 20 retains live guards.)

- [x] OPS-015 Package and prove the rootless container runtime
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-local-rootless-rollout.md),
  [task](plans/tasks/ops-015-rootless-container-runtime.md)).
  Decision 127 packages explicit rootless user services/system bridge, Caddy TLS/
  Unix upstream, one API, credential-free FD3/PID1 verifier and API-only observers.
  Preserve the shared lock, separate stores/secrets, infinite non-killing drain
  and stopped-only cleanup. Actual NAS-free worker-6/selected-overlay stack-7
  proofs pass isolation, peer/lock, verified TLS, roles/registry and client checks;
  host UID 1000 maps container UID 981, not production-manager acceptance.
  Actual review corrected ineffective appended seccomp denies, unnecessary Caddy
  file capability and disconnected release selection without weakening hardening.
  Nine exact protected current bindings pin helper/profile/images/config together;
  indexed fsynced staging and real temporary switch/rollback refuse drift/unknown
  evidence. Task retains exact artifacts, failed attempts and uncertain-fsync rules.
  Focused installer 106/helper 28/build-probe 34 and Cockpit 135 pass. A manually
  stopped metadata-review gate and passing pre-selector gate remain separate;
  neither is substituted for final corrected acceptance. Final NAS-shadowed
  `rtk proxy bash scripts/check.sh --with-build` confirms pipeline exit 0:
  lock/both-extra sync, 404 formatted, Ruff/whole Pyrefly 0, 3,792 Python passed/
  40 deselected in 453.62 seconds, 0.1.10 sdist/wheel and three actual locked
  base/server/server+MCP installation profiles. Cockpit lint/style/types,
  135 tests in 2.213 seconds/build 1,178 ms; extra wheel subset 4 passed/
  3,828 deselected in 5.15 seconds. Exact log hash and unit duration are in task.
  INV-002/003/006/010–016, AD-16/17/21, CP-01–14 and 111/121/122/126 are reviewed;
  127/contracts/schemas 15/16/enforcement/README/Unreleased/router agree. Final
  records/links/current/dependencies/REST matrix/unique decision/whitespace pass.
  Pending REL-010 commits reviewed 0.2.0 source; new REL-012 builds clean-source
  artifacts before OPS-016. No later task activates before committed dependencies.
  Guard PID 653008, masked inactive writers, read-only NAS and Enforcing SELinux
  remain; no running fixture containers. No dependency/archive/service/domain/
  version change, production switch, NAS file I/O/live sync/full verification/
  NFS-hardening, other-host change, remote publication, ACME, merge or tag.
  Handoff 20/21 preserves installed-manager/full-storage acceptance holds.)

- [x] REL-010 Review and commit 0.2.0 source
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-local-rootless-rollout.md),
  [task](plans/tasks/rel-010-rootless-release-artifacts.md)).
  Root reviews/fast-forwards local main 86f6e8b→edef480 and returns to the clean
  feature branch without remote action. Only hfcache metadata changes 0.1.10→0.2.0;
  all 93 nonproject lock records are identical. README/CHANGELOG explicitly say
  preparing, not deployed/tagged, preserving historical feature/deployment proof.
  Required NAS-masked --with-build gate confirms exit 0: 405 formatted, Ruff/whole
  types 0, 3,792 Python passed/40 deselected in 461.15 seconds, 0.2.0 wheel/sdist
  and three locked isolated installation profiles. Cockpit lint/style/types,
  135 tests in 2.273 seconds/build 1,221 ms and four extra wheel smokes in
  7.15 seconds pass. Task retains exact log/preview hashes and successful unit
  duration. Preview artifacts are not deployable; REL-012 must build from this
  clean committed source and remains next pending until this commit. Reviewed
  INV-005/010/011/014/015 and 65/75/79/126/127; no runtime code, dependency,
  durable-format or architecture change/new decision. Records/links/current/
  dependencies and whitespace pass. No production switch/tag, NAS file I/O,
  other-host change or remote publication; held guard/read-only NAS/masked writers
  and installed/full-storage acceptance holds remain.)

- [x] REL-012 Build immutable artifacts from clean committed source
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-local-rootless-rollout.md),
  [task](plans/tasks/rel-012-clean-container-release-artifacts.md)).
  Clean detached 481fcc4 source produces 0.2.0 wheel/sdist and locked app/Caddy
  images with source_dirty=false; exact identities/protected OCI hashes are in
  task. Corrected source lives outside ignored parents; the first type-scope
  stopped gate is retained, not passed. Actual new-image worker isolation/drain,
  90 compatibility observations and host-tool/image boundary pass with evidence
  preserved. Root stages exact indexed artifacts, preserves an initial umask-077
  unreadable stage, then restages under 022 and proves actual UID-981 schema/
  readability controls. Native selector stays 0.1.10. Corrected NAS-masked
  --with-build confirms exit 0: 405 formatted/Ruff/whole types 0, 3,792 Python
  passed/40 deselected in 507.85 seconds, three locked installation profiles,
  135 Cockpit tests in 2.276 seconds/build 1,200 ms and four wheel smokes in
  5.31 seconds. Local exports are protected/hash-verified, not loaded into the
  service engine. Runtime/package inputs match 481fcc4 and its worktree stays
  Git-clean; this evidence commit is distinct from source. Reviewed
  INV-005/010/011/014/015 and 65/75/79/121/126/127; no source/dependency/format/
  architecture change or new decision. Final links/records/current/dependencies/
  whitespace pass; OPS-016 next pending until this commit. No production switch,
  account/secret/service activation, NAS file I/O/writes, other-host change,
  remote publication, ACME or tag; existing guards and acceptance holds remain.)

- [x] OPS-016 Deploy the local runtime with explicit partial acceptance
  (2026-10-18, this commit — [task](plans/tasks/ops-016-local-rootless-deployment.md)).
  Root selects indexed clean-481fcc4 0.2.0 artifacts, loads exact images as UID 981,
  reuses Hub/TLS material, separates six Podman secrets and preserves the original
  dev 27/inode 2273 under the permanent notify guard. Protected host socket alias
  retains bridge hardening; actual local TLS/auth/version/nine-tool registry,
  container CLI, UID/capability/resource/isolation and nonforce drain/restart pass.
  All probe failures/corrections and protected host ledgers are task evidence.
  API-container→worker SELinux connectto remains refused: host peer/FD3 proof is
  not end-to-end verification acceptance. No allow/label/execution bypass; new
  operator hold 22 requires a separately authorized design review. Final masked
  --with-build exits 0: 407 formatted/Ruff/whole types 0, 3,827 Python/40 deselected
  in 471.22s, 0.2.0 builds/three locked profiles, 135 Cockpit tests/build and four
  extra wheel smokes. Reviewed INV-002/003/005–007/010–016 and decisions 65/75/79/
  121/126/127; host policy is separate from unchanged app artifacts. Records/
  links/whitespace pass; REL-011 next pending until commit. NAS remains ro,
  all four legacy writer units masked/inactive and SELinux Enforcing. No NAS
  I/O/job/write, other-host change, remote publication, ACME or tag; full-storage
  and worker-connectivity holds remain explicit.)

- [x] REL-011 Record the local partial-acceptance release and handoff
  (2026-10-18, this commit — [task](plans/tasks/rel-011-local-release-and-handoff.md)).
  Final NAS-masked --with-build exits 0: 407 formatted/Ruff/whole types 0,
  3,827 Python passed/40 deselected in 455.86 seconds, 0.2.0 builds/three locked
  profiles, 135 Cockpit tests/build and four wheel smokes. Root creates verified
  local annotated v0.2.0 from clean reviewed 11ddd55; task records tag object,
  peel, full-note hash and exact deployed clean-481fcc4 artifact identities.
  Evidence-only closure changes no app/image/profile/host; tag target, build
  source and closure commit remain distinct. Reviewed INV-010/011/014/015 and
  65/75/79/121/126/127; records/links/whitespace pass. All six rollout tasks are
  complete and only this plan's selection clears. Local main fast-forward is
  planned after commit, not claimed executed. Worker SELinux hold 22, NAS-ro/
  original lock/writer masks/stores/handles and all forbidden storage/other-host/
  calendar checks remain. No remote publication or follow-up activation.)

## Confined rootless worker listener (OPS/REL, 2026-10-18)

- [x] OPS-017 Implement the confined worker-owned listener
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-container-worker-listener.md),
  [task](plans/tasks/ops-017-container-worker-listener.md)). Decision 128 preserves
  strict native named FD3 and adds explicit PID1-owned listener/locality/early
  signal audit, exact instance-parent-inode cleanup and real container READY.
  Rootless worker notify ordering/RW private-dir/API RO and dormant .socket retain
  existing bindings and confinement. Metadata 0.2.1 changes no dependency record,
  schema or domain algorithm. Focused app 162/runtime 197 and actual dirty preview 2
  container-peer/notify/isolation/direct-drain pass; failed early-stop regression,
  superseded untested preview 1 and simulated-PID1 source fixtures remain explicit.
  Full masked --with-build exits 0: 415 formatted/Ruff/whole types 0, 3,912 Python/
  40 deselected in 487.56s, 0.2.1 builds/three locked profiles, 135 Cockpit tests/
  build and four wheel smokes. Reviewed INV-002/003/005–007/010–016, AD-16/17/21,
  FS/TX and decisions 115/121/126/127/128/offline verification; contracts/index/
  register/enforcement links and final records/whitespace pass. REL-013 remains
  pending until commit. Dirty proof is not a clean release or installed acceptance:
  deployed/tagged 0.2.0/hold 22, NAS-ro/guard/masks and all forbidden NAS I/O/jobs/
  other-host/remote actions remain unchanged.)

- [x] OPS-019 Build service images on minimal viable UBI 10 bases
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-container-worker-listener.md),
  [task](plans/tasks/ops-019-ubi10-runtime-images.md)). Decision 129 implements
  pinned micro for every app/Caddy FROM stage; minimal contributes only Red Hat
  CA data and external uv/Caddy images only authenticated executables. Portable
  Python 3.14.6/locked dependencies/domain/schemas stay unchanged. Exact optional
  installer omission and supported caio fallback retain confinement; actual
  dirty preview foundation, notify/container-peer/isolation/cleanup and Caddy
  TLS/REST/MCP/client proofs pass. Failed foundations, stopped gate, provenance
  race correction and superseded Debian evidence remain explicit. Fresh masked
  --with-build exits 0: 423 formatted/Ruff/whole types 0; 4,057 Python/40 deselected
  in 469.08s; 0.2.1 wheel/sdist/three locked profiles; 135 Cockpit tests/build and
  four wheel smokes. Reviewed INV-002/003/005–007/010–016, FW-03/04, AD-16/17/21,
  FS/TX and decisions 126–129; contracts/register/ADR/source-test links, records
  and whitespace reconcile. REL-013 stays pending until commit and repeats all
  clean UBI acceptance. No preview deployment/tag or hold 22 closure: production
  0.2.0, guard/NAS-ro/writer masks/stores/handles and forbidden NAS I/O/jobs/
  other-host/remote actions remain unchanged.)

- [x] REL-013 Build clean UBI 0.2.1 artifacts and prove container peer access
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-container-worker-listener.md),
  [task](plans/tasks/rel-013-container-worker-artifacts.md)). Immutable clean source
  4088994 produces exact wheel/sdist/app/Caddy/provenance with unchanged closure;
  actual foundation, user notify/container-origin peer/isolation/cleanup, verified
  fixture TLS/REST/MCP/client and 126 compatibility observations pass. Separate
  simulated-NFS HTTP domain proves three complete modes and exact integrity 40/
  receipt/key/retry/result semantics; no real-NAS or deterministic active-observer
  drop/restart claim. Protected 0.2.1 stage/index 64 files passes actual UID 981
  access and 36 control-reader cases, preserving both stages/fixtures. Clean-source
  masked --with-build exits 0: 423 formatted/Ruff/whole types 0; 4,057 Python/
  40 deselected in 510.38s; three locked profiles; 135 Cockpit tests/build and four
  wheel smokes. Reviewed INV-002/003/005–007/010–016, AD-16/17/21, FS/TX and
  decisions 65/75/79/115/121/126–129; no source/dependency/schema/domain change.
  Records/links/current/whitespace reconcile; OPS-018 stays pending until commit.
  Superseded Debian/dirty/stopped/failed evidence remains. Images are not loaded
  into the production engine/selected; production 0.2.0/hold 22, permanent guard/
  NAS-ro/writer masks/stores/handles and forbidden NAS I/O/jobs/other-host/remote
  actions remain unchanged.)

- [x] OPS-018 Deploy and accept the corrected listener locally
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-container-worker-listener.md),
  [task](plans/tasks/ops-018-container-worker-rollout.md)). Protected0.2.1 source
  4088994/clean UBI images/index is selected under original guard/NAS-ro/masks;
  exact old socket is retained by same-filesystem rename. Actual installed
  API-container PROBE passes under Enforcing before/after non-killing drain/
  restart, closing hold 22 for this listener. Verified TLS/REST/auth/MCP9/fixed
  client, real READY/peer/isolation/effective units and unchanged stores/locks/
  six secrets pass. Refused intermediate snapshots/quiescence and ledger typo
  remain explicit. Full masked --with-build exits 0:423 formatted/Ruff/types 0;
  4,057 Python/40 deselected in 473.93s; three locked profiles; 135 Cockpit tests/
  build and four wheel smokes. Reviewed INV-002/003/005–007/010–016, AD-16/17/21,
  FS/TX and decisions 65/115/121/126–129; no source/dependency/schema/authority
  change. Living status/contracts/handoff/ADR links and final records/whitespace
  reconcile. REL-014 stays pending until commit; 0.2.1 tag not yet created.
  Old 0.2.0 failure/rollback and all NAS I/O/jobs/storage/calendar/other-host/
  remote holds remain; no NAS workload or hardening bypass occurred.)

- [x] REL-014 Record corrected local release and handoff
  (2026-10-18, this commit — [plan](plans/2026-10-18-plan-container-worker-listener.md),
  [task](plans/tasks/rel-014-container-worker-release.md)). Fresh masked
  --with-build exits 0:423 formatted/Ruff/whole types pass; 4,057 Python/40 deselected
  in 472.40s; three locked profiles; 135 Cockpit tests/build and four wheel smokes.
  Actual annotated local v0.2.1 object 9c8fc386… targets clean reviewed deployment/
  evidence 156506f; deployed immutable artifact source remains 4088994, not this
  records commit or gate artifacts. Exact note/cat-file hashes and existing
  unchanged v0.2.0 are recorded. Actual release-state ledger is byte-identical
  to OPS-018 final, and independent history/artifact/seven-record/current-status
  reviews release without blocker. Reviewed INV-010/011/014/015 and
  decisions 65/75/79/115/121/126–129; no runtime/application/image input/installed
  configuration/host-policy change. Protected evidence JSON/tag are new local
  records. All five tasks complete; plan closes/current=None with no new backlog
  activation. Hold 22 closes narrowly for 0.2.1 peer connectivity; NAS I/O/jobs/live
  verification/storage/NFS/calendar/other-host and remote actions remain unrun.
  Guard/original locks/NAS-ro/masks/stores/handles/secrets/Enforcing, old failures
  and 0.2.0 rollback limitation remain. Links/records/whitespace reconcile.)

## Live rollout checkpoints (§29, writer-side)

- [x] Archive initialized on `/srv/hfcache` with the UUID already provisioned in
      `/etc/hfcache/config.toml` (§36.4 one-time authorization, **spent
      2026-07-26**). `archive init --archive-root /srv/hfcache --archive-id
      00000000-0000-0000-0000-000000000000 --confirm`, run as the service
      identity from the installed release. `--inspect` first reported
      `initializable: true`, `adopted_published: true`, no unknown entries; the
      run created the fifteen remaining directories and `.hfcache-root`, and
      adopted the pre-created `published/` per §6.2. **Never re-initialize.**
- [x] `hfcache doctor` clean on the live mount (2026-07-26 — all 17 rows: 16
      `pass`, `hub_identity` `skipped` because `hub.expected_account` is unset,
      which §2 documents as a normal anonymous deployment. Effective writability
      and all three §14.2 publication capabilities *proven* on the real dataset,
      which under the Mapall export is the only way they can be (§35.3). Exit `0`,
      and the probe area left empty)
- [x] Test repositories chosen and recorded below; `hfcache plan` reviewed
      (2026-07-26 — the same two SHAs and sizes recorded at `HUB-004`:
      `71034c5d…` 10 files / 11.9 MiB and `850d349e…` 7 files / 201.3 KiB, all new)
- [x] First manual sync published both test repositories (2026-07-26 — exit `0`,
      both `published` at generation 1, 12 512 611 and 206 179 bytes downloaded;
      one §7.6 run journal and two publication journals, all `committed` with
      every documented checkpoint)
- [x] Second sync idempotent (skip) (2026-07-26 — exit `0`, both `skipped`,
      every total zero including `downloaded_bytes` and `hashed_bytes`)
- [x] `hfcache verify --full` clean; `hfcache status` clean (2026-07-26 —
      `verify --full` read 17 unique objects and 12 718 790 unique bytes, exactly
      the sum of the two revisions, so each physical object was read once;
      outcome `clean`, exit `0`. `status` exit `0`, both revisions `verified`,
      `degraded: false`, no outstanding failures, `unfinished_transactions: 0`
      and no findings — the last two only after `SYNC-004`, which this checkpoint
      is what found)
- [x] `hfcache.target` enabled; sync timer active; verification timer installed
      but disabled (2026-07-26 — `hfcache.target` and `srv-hfcache.automount`
      `enabled`, `hfcache-sync.timer` `enabled` and `active` with its next elapse
      02:18 EDT (02:00 plus the randomized delay), `hfcache-verify.timer`
      installed with `is-enabled` = `disabled` and `is-active` = `inactive`.
      Starting the target ran no sync, per §22.1. Both services then run clean
      through systemd, repeatedly: the sync is an idempotent skip and the
      verification reads 23 unique objects across 6 revisions and reports
      `clean`. Handoff item 8 remains for enabling the quarterly timer.)

**Observed exit codes (§11.2, §36.6 item 7).** Against this deployment,
2026-07-26: `0` from `status`, `plan`, both syncs, `verify --full`, and
`verify --revision` on a clean retained revision. `10` from an absent
configuration, an unreadable one (`HFCFG001`, decision 57), a selector naming an
unconfigured repository, `verify --revision` without a SHA, `verify --revision`
naming a SHA the archive does not retain, and `prune` with neither mode. `20`
with `HFMNT010` from **all four** mutating commands — `sync`, `verify --full`,
`prune --apply`, `recover --apply` — while another process held the lock, which
is §22.3's mutual exclusion demonstrated rather than assumed. `30` with
`HFHUB004` from a run whose only configured repository does not exist upstream;
its catalog rebuild marked the two real repositories unmanaged, and the next real
sync restored them, which is what `FS-16` promises about derived state.

`40` and `50` are deliberately **not** provoked here: both need published content
or a retained revision to be damaged, and §36.5 forbids rewriting content on
`/srv/hfcache` outside the application's own transactional contracts. They are
covered by the suites instead — `-m live` flips a byte in a freshly published
revision on a throwaway archive and asserts `40` with the manifest and reference
unchanged, and the retention and repair suites assert `50`.

## Test repositories (decided 2026-07-26 at `HUB-004`, §36.5)

- Model: **`hf-internal-testing/tiny-random-gpt2`** — 10 files, 12 512 611 bytes
  (11.9 MiB) at `71034c5d8bde858ff824298bdedc65515b97d2b9`.
- Dataset: **`hf-internal-testing/fixtures_ade20k`** — 7 files, 206 179 bytes
  (201.3 KiB) at `850d349e5038f291284e7999fcacbedc0922534b`.

Both public, neither private nor gated, sizes measured by `hfcache plan` against
the live Hub on 2026-07-26 without downloading anything. Recorded in
`examples/config.toml`, which validates, and used by `tests/system/test_live_hub.py`.

Why these two. `hf-internal-testing` is the organization Hugging Face maintains
for exactly this purpose, so the repositories are long-lived and unlikely to be
renamed or deleted out from under a test. Both are far under the §36.5 100 MB
ceiling, which matters because §36.6 item 7 requires a full sync, an idempotent
second sync, and a `verify --full` over them — a cycle that has to be cheap
enough to run repeatedly. And they differ in shape as well as size: the model is
a handful of large-ish weight files, the dataset a mix of images, a parquet file,
and a README, so publication and hashing are exercised over both profiles.

§36.5 authorizes the session to choose these; see **Operator decisions needed**
item 1 for the separate production-list question that does need an operator.

## Operator handoff

Keep instructions exact and copy-pasteable; add acceptance checks.

1. **NAS-004 — consumer export (TrueNAS UI on `nas.lab.example.com`):**
   NFSv4 export of `/mnt/tank/huggingface-archive/published`, read-only enabled
   server-side, Mapall `hfcache-read:hfcache-archive`, allowed clients =
   explicit consumer hosts or consumer VLAN, **excluding** `192.0.2.90`
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
   against the manifests. **The helper now exists** (`OPS-007`):
   `examples/copy-revision.py`, shipped in the release at
   `/opt/hfcache/current/examples/`, with `docs/consumers.md` as its runbook.
   Copy it to the consumer host — it needs only Python 3 and the read-only
   mount, not this project. Acceptance:

   ```bash
   python3 copy-revision.py --mount /mnt/hfcache --type model \
     --repository hf-internal-testing/tiny-random-gpt2 --destination ./gpt2
   python3 copy-revision.py --mount /mnt/hfcache --type dataset \
     --repository hf-internal-testing/fixtures_ade20k --destination ./ade20k
   ```

   Both exit `0` and report `verified`. It has been exercised from the *writer*
   against `published/`; what remains is running it from a genuine consumer
   client over the read-only export, which is what items 1 and 2 provide.
6. **Reboot persistence (§26.5):** reboot the writer; confirm mount, target,
   and timers return; confirm boot completes with the NAS down.
7. **Live-mount interruption window (§26.4):** operator-supervised NFS
   disconnect/reconnect during a test sync, or provision a disposable dataset.
8. **Verification timer enable (§29 step 14):** confirm the quarterly calendar
   does not overlap NAS scrub/SMART/replication, then enable.
9. **Optional cleanup:** revoke passwordless sudo
   (`sudo rm /etc/sudoers.d/<operator>-nopasswd`) after rollout.
10. **`PrivateNetwork=true` on `hfcache-verify.service` (§22.3, decision 60):**
    during the item 7 interruption window, add
    `PrivateNetwork=true` as a drop-in on `hfcache-verify.service`, start a full
    verification, and break and restore the NAS connection while it runs.
    Acceptance: the verification completes and reports `clean`, and no NFS
    operation returns an error. If it does, remove the drop-in and leave
    `IPAddressDeny=any` as the egress control. Steady-state reads are already
    proven under `PrivateNetwork=true`; only the reconnect path is open.
    **API-014 amendment (2026-10-18):** after the API arrangement is deployed,
    the actual executor is `hfcache-verification.service`; the named verify
    oneshot is an API-credentialed AF_UNIX observer. Probe executor cgroup/
    credential/NFS behavior, not just the wrapper. This task performs no such
    operator or live-mount test; item 16 tracks the new deployment holds.
11. **`docs/truenas.md` (plan §7):** the one document in §7's set with no work
    package that produces it. `OPS-001`–`OPS-004` account for
    `deployment-centos-stream-10.md`, `operations.md`, and `recovery.md`, and
    `consumers.md` falls out of `OPS-007`; nothing owns the TrueNAS side.
    Written by whoever performs handoff items 1–4, because the dataset tuning,
    the two exports, the disjointness proof, and the snapshot/replication/scrub
    schedule are the content, and this session cannot make or verify any of
    them (§36.4). Plan §20 is the specification to write it against; §35.2
    records what was already provisioned on 2026-07-24.
12. **Hypervisor memory for the writer VM (decision 86):** `SYS-003` bounds
    what the guest touches, but only the hypervisor can take reclaimed pages
    back or stop overcommitting them. On the virtualization host, either
    enable free page reporting on the balloon device —
    `<memballoon model='virtio' freePageReporting='on'/>` in the domain XML
    (libvirt ≥ 6.9, QEMU ≥ 5.1), then a full guest power cycle — or reserve
    the guest's full memory so ballooning is not load-bearing. The guest's
    balloon currently negotiates only `STATS_VQ`; neither free page hinting
    nor reporting is offered. Acceptance: after a terabyte-scale sync, the
    QEMU process RSS on the host returns to (reporting) or never leaves
    (reservation) the expected envelope, and no OOM kill of the VM appears in
    the host journal.

13. **Three CPT-011 evidence items deferred by the live catch-up sync**
    (2026-07-30, CPT-011). Run `d694a1b6…` — started 2026-07-29 05:34, 19
    repositories, terabyte-scale — was mid-download of
    `unsloth/Kimi-K3` (1.56 TB) throughout the CPT evidence window, and
    `sync`, `verify`, `prune`, and `repair` share the one application lock
    (`AD-17`), so three proofs could not run without either hanging on the
    lock for up to a day or stopping a production terabyte download, and
    neither was acceptable. After the catch-up completes, run:

    ```bash
    sudo runuser -u hfcache -- /opt/hfcache/current/.venv/bin/hfcache \
        --config /etc/hfcache/config.toml --json verify --revision \
        model:hf-internal-testing/tiny-random-gpt2@71034c5d8bde858ff824298bdedc65515b97d2b9
    # expect exit 0, outcome clean (12 MiB read)

    sudo systemctl start hfcache-sync.service && \
        systemctl show hfcache-sync.service -p Result -p ExecMainStatus
    # expect a short skip-run: Result=success, ExecMainStatus=0

    sudo /opt/hfcache/current/scripts/check-hardening.sh
    # expect 23 of 23 on both units on the then-idle system
    ```

    The 2026-07-30 check-hardening run scored 22/23: the `ProtectProc`
    probe asserts *no* other pid is visible, but `ProtectProc=invisible`
    hides other *users'* processes — the probe (uid `hfcache`) legitimately
    saw the live sync's own pid (9663, uid `hfcache`) and nothing else, and
    `systemctl show` confirms `ProtectProc=invisible` applied on both
    units. The probe assumes an idle system; filtering same-uid pids in
    `_protect_proc` is the one-line candidate fix, recorded here and not
    performed (it is deployment tooling outside the `CPT` family's
    surface).

14. **Finish the 0.1.5 release proof after the active catch-up sync**
    (2026-08-15, PUR-002). Wait for run
    `3d006f9b888b49f0ae24a929ec66a2d4` to finish with `Result=success` and
    `ExecMainStatus=0`; confirm all four queued repositories are published:
    `MiniMaxAI/MiniMax-Music3`, `unsloth/Muse-Glimmer-30B-GGUF`,
    `unsloth/gemma-4-31B-it-NVFP4`, and
    `RedHatAI/Muse-Glimmer-30B-NVFP4`. Then start
    `hfcache-verify.service`, require a clean full-verification report, and only
    then create and push the annotated `v0.1.5` tag. The quarterly verification
    timer remains disabled pending handoff item 8.

15. **Finish the current 0.1.10 candidate's formal release proof**
    (2026-09-14, OPS-012). Retention and quarantine cleanup are complete on
    installed 0.1.10, with previous releases retained for rollback. Formal
    tagging remains subject to `docs/agents/release.md`: a successful service
    sync, clean full verification, and the release hardening checks. Resumed
    run `58dd7515d03b40398d20ac859ad2d86b` is downloading the three newly
    configured models. Require its successful completion, then refresh
    `verify --estimate` before scheduling the full read. The earlier estimate
    covered 24.59 TB and approximately 8.55 days at old measured throughput;
    it is not a fresh estimate for the expanded archive. The sync timer is
    active on its existing schedule; verification stays disabled pending
    item 8. Complete these checks and tag the current candidate rather than
    a superseded deployed version from item 14.

16. **API-014 deployment acceptance holds (2026-10-18, decision 121):**
    repository activation/unit/installer/disposable drain/rollback tests do not
    prove the installed host. Before rollout acceptance, verify actual named
    socket activation feeds one API app across Unix/optional TCP; peer account
    identity and private socket restrictions hold; the actual verification cgroup
    denies IP and cannot access provisioned Hub/API/MCP credentials or daemon
    token cache; custom development source paths have explicit masks/probes;
    executor-aware installed hardening and SELinux/NFS behavior pass. Preserve
    verify timer disabled until item 8, shared runtime locks, and unresolved API/
    verifier/scheduled state. Rehearse actual server/worker drain before switch,
    and prove a stopped observer never authorizes duplicate execution. Use
    [deployment](../deployment-centos-stream-10.md#upgrade-and-drain),
    [server](../server.md#scheduled-observation-and-lifecycle-controls) and
    [scheduled schema](../schemas.md#14-scheduled-client-observation-handle).
    No production deployment, service/timer/mount manipulation or archive operation
    is authorized by implementation of this plan.

17. **API-015 Cockpit deployment acceptance (2026-10-18, decision 122):**
    repository process/config/browser-independent fixtures do not prove the
    installed Cockpit PAM/superuser bridge, named API credential delivery or
    SELinux/NFS behavior. Provision fixed local client TOML/socket and API-only
    `hfcache.api` without transient Hub authority; confirm closing/stopping an
    observer leaves accepted work independently observable. Check bounded
    terminal/progress handling and exact candidate/base/backup/fingerprint
    confirmation in an authorized disposable/deployment window. Preserve retained
    config locks and API/scheduled evidence. Actual executor hardening/drain and
    verify-calendar holds from item 16 remain. No production installation or
    operation is authorized by this work package.

18. **Optional MCP deployment acceptance (2026-10-18, decision 124):**
    select an actual server+MCP release profile and deliberately provision a
    distinct protected MCP-reader source to the API service, with the named
    credential drop-in or protected-file alternative in [MCP setup](../mcp.md).
    Default units do not import that optional credential. Verify actual public/
    native URLs, TLS/proxy/Host/Origin and internal-client bearer delivery in an
    authorized deployment window; no OAuth-only compatibility is promised.
    The worker must remain credential-free/no-IP, including custom source masks.
    Before rollback to server-only/pre-MCP, disable MCP configuration deliberately
    and preserve normal drain, lock and retained-state guards. Staging --with-mcp
    does not enable config, provision credentials or add packages to a switch
    target. MCP-002's nine tools and MCP-004 repository acceptance are complete;
    actual host enablement remains held. Existing holds 16/17 still apply; no
    production operation is authorized by this implementation package. The
    [consolidated API-017 rollout checklist](../deployment-centos-stream-10.md#acceptance-checklist)
    retains every host prerequisite and deliberate artifact/rollback identity.

19. **Final REST/MCP rollout handoff (API-017, 2026-10-18):** all items in the
    [operator checklist](../deployment-centos-stream-10.md#acceptance-checklist)
    remain pending outside repository implementation: distinct whole-archive
    credentials, actual TLS/proxy/firewall/Unix ownership, deliberate locked
    artifact/version, API/private-worker activation/no-IP/source masks, NFS/
    SELinux/executor hardening, state-retaining drain/rollback and client monitoring.
    Preserve both operation stores, scheduled pending handles, locks and prior
    artifacts; a stopped client/free lock/missing reader or receipt proves no
    execution outcome. Keep verify timer disabled pending item 8. Source metadata
    0.1.10 is unchanged, not a release/tag; choose commit and artifact hashes
    deliberately before an authorized rollout. Implementation completion never
    performs or approves these host/release actions.

20. **Data-preserving local rollout guard (OPS-014, 2026-10-18):** the new
    [local plan](plans/2026-10-18-plan-local-rootless-rollout.md) authorizes reviewed
    local rootless rollout work only. NAS is client-read-only, both legacy
    timers/services are masked, sync stopped and verify scheduling disabled;
    retained guard ownership and protected backups are recorded in the
    [task](plans/tasks/ops-014-local-rollout-guardrails.md). Do not restore writer
    activation or read-write NAS access as an automatic release step. Preserve
    existing lock inodes, service/scheduled evidence and old artifacts. Full
    NAS-write/domain acceptance, other-host/NAS changes and verify calendar work
    remain forbidden or separately held, not passed by local fixture/gate proof.
    OPS-015 architecture, later deployment and local release/tagging require their
    committed dependencies; no remote push/registry publication/ACME is authorized.

21. **Rootless packaging is not production acceptance (OPS-015, 2026-10-18):**
    actual NAS-free rootless login fixtures prove worker isolation/FD3/peer/lock,
    Caddy verified TLS/API/MCP/container-client behavior and selected physical
    overlays; they do not prove the production service account, effective manager
    fragments/drop-ins, installed target/bridge, real credential delivery, overlay
    placeholders, firewall/browser/PAM or NFS/SELinux workload behavior. Keep the
    [container contract](../containers.md) and both-manager reload/precedence checks
    in OPS-016. REL-010 prepares reviewed 0.2.0 source; REL-012 must build final
    immutable artifacts from its clean committed worktree and prove compatibility
    before deployment. Fixture images/0.1.10 metadata are not a release. Preserve
    item 20's masks/read-only NAS/held lock, both stores/handles and old artifacts.
    Never convert these local proofs into live NAS-write/full-domain acceptance
    or restore sync/verification scheduling automatically. No remote publication,
    other-host change or ACME is authorized.

22. **Private-worker SELinux hold — closed for 0.2.1 by OPS-018 (2026-10-18):**
    The original 0.2.0 Caddy/API runtime passed proxy/metadata checks but SELinux
    denied container_t connectto to the user-manager-created unconfined_t socket.
    Host UID 981/FD3 probes and host-origin fixtures never proved API-container
    access. That failed evidence remains intact and is a rollback limitation.
    Decisions 128/129, committed listener/UBI source and clean REL-013 artifacts
    now support actual installed [OPS-018](plans/tasks/ops-018-container-worker-rollout.md)
    acceptance: API-container framed PROBE passes with expected UID 981 under
    Enforcing before and after real non-killing drain/restart. Final proof
    2f879ff38f17df7eb9f1f0a4a5c602b4c6c13f56c6ccc35bd6fd826c8331034f
    closes this connection hold only. No allow rule, process-label override,
    unconfined/host executor or seccomp relaxation is used. Keep independent
    guard/original lock, read-only NAS, writer masks, stores/handles and history.
    Live NAS verification/jobs/full-domain/NFS workload, calendar and other-host
    acceptance remain unrun; this is not general writer-readiness certification.

23. **Timestral sync admitted but guard-held (OPS-022, 2026-10-19):** four requested
    Timestral model entries are installed and validated; one scoped sync is
    admitted as operation `0cb77c1c970e21033a9cab7fb8ea872d`, key
    `timestral-sync-20261019-410f6659ff9b48379249e7a167a36400`. Last observed
    `13:56:34 UTC`: `waiting_lock`, no domain run/result, guard PID `809950`
    still holding original `27:2273`, NAS-ro and all masks intact. From working
    directory `/`, observe under the service identity using the exact command:

    ```bash
    rtk proxy sudo -n -H -u hfcache -- /usr/local/libexec/hfcache-client --client-config /etc/hfcache/client.toml --json operations lookup -- timestral-sync-20261019-410f6659ff9b48379249e7a167a36400
    ```

    Preserve existing handles/stores and use observation only; a lock wait or
    terminal refusal is not publication. Do not release the guard, remount NAS,
    unmask writers, enable schedules or retry under a new key. Protected backup
    and full evidence paths are in the [task](plans/tasks/ops-022-timestral-model-sync.md).
    This scoped request does not resolve other live acceptance holds.

## Operator decisions needed

1. **Which repositories the archive is ultimately for** (raised 2026-07-24, during
   `CFG-002`; not blocking until `HUB-005`). Two separate questions have been
   conflated so far, so they are separated here:

   - *The two test repositories* (§36.5) did **not** need an operator: the plan
     authorizes the session to choose them, requiring only that each is public,
     well under 100 MB, and confirmed available at implementation time. **Settled
     2026-07-26 at `HUB-004`** — see "Test repositories" above; recorded in
     `examples/config.toml`. This half of the item is closed.
   - *The production repository list* does need an operator, because it is the
     only input to handoff item 4 (the TrueNAS dataset quota) and to §29 step 12.
     Nothing is blocked while it is open: Phases 3–6 are written against
     configuration, not against a particular repository.

   When the list is known, `hfcache plan` reports dry-run sizes for it without
   downloading anything, which is the number the quota decision wants.

## Decisions

_Settled implementation deviations from `docs/agents/history/plan.md`, with rationale (§36.3)._

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
    tested for identities this host cannot create — `<operator>` cannot `chown` to
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

33. **The check runner is its own module, `preflight.py`** (2026-07-25,
    STO-001). Plan §7's module list has no home for it, and neither of the two
    obvious ones works. `cli.py` is wrong because the runner is not the CLI's:
    a mutating command's hard gate uses the identical checks in the identical
    order, and a scheduled `sync` must not have to route through the command
    surface to reach them. `storage.py` is wrong because the table includes
    `configuration`, `credential`, and the four `hub_*` checks, which are not
    storage — and because `storage.py` is at 973 lines, near the point where one
    module carries everything. So the *primitives* stay in `storage.py`
    (`probe_writability`, `same_filesystem_problems`, `is_initialized`) and the
    *ordering, outcomes, and gate* are `preflight.py`, which is also where the
    normative `docs/cli.md` §2 table lives as `CHECK_ORDER`. Plan §7 updated in
    this commit.

    Sizing note for the next package: `storage.py` is now 973 lines and
    `STO-002` adds to it. The §36 protocol's instruction stands — split
    `archive init`/`--inspect` into `archive.py` at that point, with its own
    decision and plan §7 amendment. It is not done here because it would mix a
    large move into the commit that implements the preflight.

34. **`archive_root` reports `HFMNT015` as well as `HFMNT001`** (2026-07-25,
    STO-001). `docs/cli.md` §2 row 2 proved "the archive root exists" and named
    only `HFMNT001`. A symlink exists, and so does a regular file; neither is an
    archive root, and `mount_problems` already reports both as `HFMNT015`.
    Putting that under a later check was considered and rejected: `mount_point`
    would then fail for a path whose problem is not its mount, and the check
    that actually looked at the root would have reported `pass`. Row 2 is now
    "exists and is a directory" with both codes, which is what it always
    verified. `docs/cli.md` §2 updated in this commit.

35. **A skipped check has three meanings, and the gate reads them differently**
    (2026-07-25, STO-001). `docs/cli.md` §2 described `skipped` for two
    situations — `--read-only`, and an archive that is not initialized — and
    plan §19 requires the same checks to be a *hard* preflight for every
    mutating command. Those two cannot both be satisfied by one boolean: an
    uninitialized archive is a fine answer for `doctor`, which reports it and
    exits `0`, and an impossible one for a command that is about to write.

    A third case appeared while implementing rows 2–5. `mount_problems`
    short-circuits, so with an absent root nothing is known about its filesystem
    type; reporting `pass` there would be the one wrong answer, and reporting
    `fail` would invent a failure that was never observed.

    So a check carries the reason it did not run, and only the "not initialized"
    reason blocks a mutating command — as `HFMNT008`, which `docs/cli.md` §5.2
    already defines as a required directory being missing, which is exactly the
    condition. A precondition skip adds nothing, because the failure that caused
    it is already its own entry in the same report; restating it three times
    would make a single missing directory look like four problems.
    `require_storage_safety` deliberately takes no `--read-only` option: a
    command about to write has no business asking for one, and an option that
    silences a check is an option that lets one through. `docs/cli.md` §2
    updated in this commit.

36. **`archive.py` split out of `storage.py`** (2026-07-25, STO-002). The
    `STO-001` sizing note said to do this before adding to a 973-line module,
    and the cut turned out to be a real boundary rather than a line count.
    `storage.py` is now what a command must *prove about the mount* and the
    primitives that *act on it durably* — the mount table, atomic writes, the
    write probe, the same-filesystem proof, and reading the sentinel.
    `archive.py` is the one command that brings an archive into being: the
    known-empty-layout walk, `published/` adoption, `--inspect`, and
    `initialize_archive`. Each is now under 550 lines and neither imports the
    other's concerns.

    `_read_sentinel` became `storage.read_sentinel` in the move, because both
    sides need it: `archive.py` to tell an initialized archive from unknown
    content, and `preflight.py` for check 6. It reads the archive's identity off
    the mount, which is a storage question; deciding what a mismatch *means* is
    still the caller's. `tests/unit/test_storage.py` split the same way, into
    `test_archive.py` for the module and `test_archive_init.py` — which already
    existed — for the command. Plan §7 updated in this commit.

37. **The `sentinel` check owns "the archive is not initialized"** (2026-07-25,
    STO-002). `docs/cli.md` §2 puts checks 6-12 behind an initialized archive
    and has each report `skipped` with that as the reason, which is right for
    `doctor`. It is not enough for the gate: `STO-001` had checks 7 and 8 each
    carry `HFMNT008` for the condition, so a mutating command against an
    uninitialized archive would have reported two problems, and every later
    package would have added another.

    Check 6 is the one that actually observes it — the sentinel's absence *is*
    the condition, and the sentinel is written last, so nothing below it can be
    said either (`FS-23`). It therefore carries `HFMNT005` for the gate and the
    checks beneath it skip silently. One missing archive is one problem, with
    the code `docs/cli.md` §5.2 already assigns to exactly that condition.

38. **`HFWRN005` fires at a tenth of the reserve** (2026-07-25, STO-003).
    `docs/cli.md` §5.6 defines the warning as "free space approaching the
    configured reserve" and fixes no threshold, so the application has to choose
    one. It is expressed as a percentage *of the reserve* rather than as an
    absolute figure, because a deployment that reserved 100 GiB and one that
    reserved 1 TiB want to hear about it at different points, and the reserve is
    the only number that already scales with the deployment.

    A reserve of zero therefore never warns. That is the right reading of an
    operator who set both minimums to zero: they turned the reserve off, and a
    warning about a reserve that does not exist has nothing to say.

    The margin is also measured after `needed_bytes`, not before, so a run that
    is about to consume most of the headroom warns even when the archive looked
    comfortable before it started.

39. **`free_space` does not need an initialized archive** (2026-07-25, STO-003).
    `docs/cli.md` §2 put checks 6-12 behind an initialized archive in one
    sentence covering a range. It is right for 6-11, which all read or write
    archive-owned paths, and wrong for 12, which calls `statvfs` on the mount
    point. Reporting it as `skipped` would withhold a real answer from the
    operator most likely to want it — someone sizing the dataset *before*
    running `archive init` — and would do so for no reason, since nothing about
    the measurement depends on the layout existing. The sentence now reads 6-11,
    with check 12 called out separately. `docs/cli.md` §2 updated in this commit.

40. **`locking.py` added to the plan §7 module list** (2026-07-25, STO-004).
    The lock is neither archive storage nor a `doctor` check: it lives on local
    tmpfs under `/run/hfcache` (`AD-17`), it is never reported by `doctor` —
    which does not mutate and must not take it — and it is *held* for the
    duration of a command rather than checked once. `storage.py` is about
    proving and writing the NFS mount and `preflight.py` is about the check
    table, so it belongs in neither. Plan §7 updated in this commit.

    Two implementation points are worth recording. `flock(2)` rather than a pid
    file, because the lock lives on the open file description and the kernel
    drops it when the process dies — including under `SIGKILL` or an OOM kill —
    so a crashed sync cannot leave a lock that an operator has to clear by hand.
    And the holder record inside the file is diagnostic only: nothing reads it
    to decide anything, it exists so a command that gives up waiting can say
    *who* it waited for. It is cleared on release so a later refusal never names
    a process that has already finished.

41. **The capability probes stay inside `.store/health/`** (2026-07-25,
    STO-007). Plan §14.2 asks `doctor` to prove "a regular file can be
    hardlinked between private and published test directories", which reads as
    an instruction to create a test directory under `published/`. The probes do
    not do that, for two reasons.

    The first is that it does not match what publication actually does. A
    hardlink is made from a cache blob into `.store/staging` (§14.1 step 4), and
    what reaches `published/` is the *tree*, by rename (§13.2 step 15). Nothing
    is ever hardlinked into `published/`, so a probe that linked into it would be
    proving something the application never does.

    The second is that `doctor` takes no lock. A transient probe directory under
    `published/repos/` would be visible to a concurrent catalog rebuild or
    `verify`, and would be reported by `archive init --inspect` as content the
    application did not create. `docs/architecture.md` §5.1 designates exactly
    one probe area — `.store/health/probe-<probe-id>/` — and every probe stays
    inside it. Check 8 has already proven the whole layout is one filesystem, so
    a hardlink and a rename demonstrated there hold for the dataset.

    `_remove_probe` now removes the area with `rmtree` rather than entry by
    entry, since the capability probes build subdirectories in it. That stays
    inside `FS-19`: `probe-<16 random hex>` was created by this process moments
    earlier and cannot contain anything the application did not put there.

42. **Checkpoint evidence names paths by key suffix** (2026-07-25, STO-010).
    `TX-03` requires each checkpoint to carry re-observable evidence and
    requires recovery to confirm it by looking at the filesystem rather than by
    trusting the record. `docs/architecture.md` §7.3-§7.7 describe that evidence
    in prose — "published tree path, file count", "`.store/trash/<txn>/` absent"
    — which is enough for a human and not enough for code.

    The convention that makes it mechanical: an evidence key ending `_path`
    names an archive-relative path that must still exist, `_paths` a list of
    them, and `_absent` a path that must *not* exist. Everything else is left to
    the package that knows how to interpret it, because a file count or a digest
    means nothing without the artifact it describes.

    Suffixes rather than a fixed key list, because the same checkpoint carries
    different paths in different operations and a list would have to be extended
    every time one is added — which is exactly the kind of table that goes stale.
    The suffix travels with the key, so a caller that names a path correctly gets
    it checked for free. Evidence keys are durable, so this is a format decision
    and not only an implementation one.

43. **The recovery report is a run report** (2026-07-25, STO-011).
    `docs/architecture.md` §7.7 requires `recover --apply` to record a
    `recovery_report_written` checkpoint, but no document said what that report
    is. Three options were considered. Reusing the §6 run report unchanged does
    not fit — its body is per-repository sync results, and a recovery resolves
    transactions rather than repositories. Treating the journal itself as the
    report is a dodge: the journal is evidence of what happened, not a report an
    operator reads. Inventing a separate location would put a third kind of file
    somewhere `list` and `status` do not look.

    So it is `RecoveryReport`, the §6 envelope with a `remediations[]` body,
    written to the same `runs/` path — exactly the relationship the verification
    report already has to the run report, and for the same reason: one operator
    reads all three, so the shared part is one class rather than three that
    drift. Documented as `docs/schemas.md` §12 in this commit.

    `outcome: "pending"` is recorded for a remediation deliberately left alone —
    staging too young to be certainly abandoned. That is a real answer and worth
    persisting: an operator reading the report should see that recovery
    considered the directory and chose to wait, not that it missed it.

44. **`projected_publication_bytes` is measured under the configured mode, not
    hypothetically under copy** (2026-07-26, HUB-004). `docs/cli.md` §2 asked
    `plan` for "the projected publication bytes in copy mode", which reads two
    ways: the field means something only in copy mode, or the field always
    reports what copy mode *would* cost. The second was rejected. `plan` is the
    command the dataset quota is sized from, so the number it reports has to be
    the number the archive will actually consume — and under the default
    `hardlink` mode that is zero, because a hardlink points at a cache blob
    already on the dataset (`AD-11`).

    Nothing is lost by not reporting the hypothetical: copy mode's cost is
    exactly `logical_bytes`, which is in the same payload. A deployment weighing
    the switch reads it off the field beside it. `publication_mode` is reported
    with it so the zero is explicable rather than looking like a missing
    measurement. `docs/cli.md` §2 and §4.1 updated in this commit; §4.1 now names
    every field of the payload rather than summarizing it, since automation keys
    on them.

    The cost model itself is `publication.projected_publication_bytes` rather
    than a conditional at the call site, because plan §19 item 9 makes the same
    number part of a sync's free-space gate. An estimate an operator reads and a
    reserve a sync enforces that disagreed about what publication costs would be
    a capacity failure discovered mid-download.

45. **An empty tree listing is reported; an entry with no path is refused**
    (2026-07-26, HUB-004). `HFHUB008` is "repository tree metadata missing or
    incomplete", and two conditions could claim it. A revision containing no
    files is *not* one: it is a truthful answer to what the metadata call asked,
    `plan` reports it as `0 files`, and whether an empty revision is worth
    publishing — and consuming a retention slot — is a decision for the package
    that publishes one, not for the call that reads the metadata.

    A file entry with no path is the other, and it is refused. The listing is
    what plan §13.2 step 7 calls the exact repository path set, and every later
    step joins those names onto a filesystem path; an empty one would arrive at
    that join looking like a legitimate name for the tree's own root. The
    previous code coerced it to `""` and carried on. This is narrower than the
    path grammar in `hfcache.paths`, deliberately: the grammar answers "is this
    name safe to join", and this answers "did the response contain a name at
    all", which is a question about the library's shape and belongs at the seam.

46. **A hashing failure's error class must match its code's family** (2026-07-26,
    HUB-007). `sha256_file` took the caller's `code` and always raised
    `IntegrityError`, so `publication.stage_file`'s three calls — which correctly
    pass `HFSYN005` — would have exited `40` for a condition `docs/cli.md` §5.3
    classifies as `30`. Nothing had surfaced it yet, because publication is not
    reachable from a command until `HUB-009`; it would have arrived as an
    operator being told the archive is corrupt when a download failed.

    Two ways an exit is determined coexist in this codebase: `HfcacheError`
    subclasses carry one as a class attribute, and `taxonomy.classify` derives
    one from the code's family. They are not redundant — the first is what a
    raise site produces and the second is what the published tables promise — so
    they have to agree, and nothing was making them. `sha256_file` now takes
    `error` alongside `code`, which is exactly the shape decision 19 settled for
    reading a durable artifact, and `tests/unit/test_hashing.py` asserts
    `caught.value.exit_code == classify(code)` for every pairing used in `src/`.

    A single `error_for(code)` factory was considered and rejected: it would let
    a raise site name a code from a family it has no business raising and get a
    plausible-looking error back. Passing both makes the pairing visible at the
    call site, which is where a mistake is legible.

47. **`HFSYN009` added for content that cannot be read while hashing**
    (2026-07-26, HUB-007). Plan §13.2 step 9 hashes newly introduced objects and
    §16.1 requires a hash failure to prevent publication, but the taxonomy had no
    code for the failure itself. The nearby ones are all wrong: `HFSYN001` is the
    local-only completeness check specifically, `HFSYN003` is a size mismatch,
    `HFSYN004` is an unsafe path, `HFSYN005` is staging construction — which has
    not started yet at step 9.

    `HFVER006` ("object could not be read") describes the condition exactly and
    is still wrong, because it exits `40`. Nothing has been published when step 9
    runs, so no archive content is wrong; the run failed and the next one will
    retry. That is a `30`, which is what put the code in the `HFSYN` family.

    Added to `docs/cli.md` §5.3 in this commit. `tests/unit/test_taxonomy.py`
    reads that table, so the code is covered in both directions the moment it is
    published.

48. **`hfcache list` lands at `SYNC-002`** (2026-07-26). Plan §11 requires the
    command and plan §28 gives it no work package — the only v1 CLI command with
    no home. Three placements were considered. `CFG-006` implemented the
    read-only command surface and would have been the natural place, except that
    at Phase 2 there was nothing published to list, so the command could only
    have been written against a layout that did not exist yet. Phase 8 is
    documentation and release; adding a command there would mean shipping a
    runbook before the thing it documents. `SYNC-002` is where the archive first
    holds revisions an operator would want an inventory of, and where the sibling
    read commands — `status` reporting the same references — are being completed.

    `list` deliberately reads manifests and references and never the catalog,
    which `docs/cli.md` §2 already required and which is the reason it belongs
    beside `status` rather than beside the catalog rebuild: an operator taking
    inventory during an incident is exactly the person who cannot rely on derived
    state (`FS-16`). Selectors restrict the *configured* set, so naming one
    repository never hides an unmanaged one the operator did not ask about.

49. **A verification finding may name no publication instance, and `HFARG004`
    now covers a revision or a run this archive does not hold** (2026-07-26,
    `VER-001`). Two small contract amendments, both forced by the same thing:
    `verify` is the command an operator runs when the archive is *already* known
    to be wrong (`docs/architecture.md` §7.9), so it has to keep answering about
    artifacts it cannot read.

    `docs/schemas.md` §7 typed `finding.publication_id` as required. A reference
    that will not parse names no publication instance, so there is nothing to
    put there — and attributing the finding to whichever instance directory the
    filesystem happens to hold would assert exactly what the unreadable
    reference failed to say. The alternative was to raise instead of reporting,
    which would abandon every other repository in the run because one reference
    file is corrupt. The field is now nullable, `docs/schemas.md` §7 says the
    single case it is null for, and every other finding still carries it.

    `docs/cli.md` §5.1 defined `HFARG004` as a selector naming a repository
    absent from configuration. `verify --revision TYPE:ID@SHA` and
    `verify --new --run-id ID` can both name something that is not there, and
    neither is an integrity failure: a mistyped SHA reported as exit `40` would
    tell a scheduler the archive is corrupt because somebody typed one wrong
    character. The row now reads "an argument names something the archive does
    not hold", which is one condition with three instances rather than three
    codes for one mistake. `tests/unit/test_taxonomy.py` parses that table, so
    the widened row is checked in both directions.

50. **`verify --estimate` reports storage maintenance as `undetectable`**
    (2026-07-26, `VER-004`). Plan §16.4 asks the estimator for a "current
    TrueNAS scrub overlap warning when detectable", and `HFWRN010` exists for
    it. Nothing on the writer can detect it.

    The writer holds an NFS mount and nothing else. ZFS scrubs, SMART long
    tests, and replication all run on `nas.lab.example.com`, and the archive
    dataset exposes no channel that reports them: there is no configured NAS API
    endpoint, no credential for one, and §36.4 forbids changing the NAS to add
    one. Inferring maintenance from observed read latency was considered and
    rejected — a slow read distinguishes a scrub from a busy sync, a cold ARC,
    and a saturated uplink not at all, and a warning that fires on any of those
    is a warning an operator learns to ignore.

    So the field reports the literal string `undetectable` rather than a
    silently absent warning, and `HFWRN010` is never emitted by `--estimate`.
    The difference matters: an absent warning reads as "the window is clear",
    which this application has no basis to say. Plan §16.4's "when detectable"
    is what permits this, and `docs/cli.md` §4.1 now lists the estimate's field
    set, which is not a `VerificationReport` — `--estimate` verifies nothing, so
    there is no verification to report.

    `HFWRN010` stays in the taxonomy. Handoff item 8 already requires an
    operator to confirm the quarterly calendar does not overlap NAS maintenance
    before enabling the timer, which is the same decision made by the party that
    can actually see the schedule.

51. **`verification_state` comes from `catalog/verification.json`, and a
    revision nothing has re-read is `unverified`** (2026-07-26, `VER-005`).
    This settles the second item Phase 6 carried in. No document said whether a
    revision that was SHA-256 verified at ingestion but never verified offline
    is `verified` or `unverified`, and three call sites hardcoded `"verified"`,
    which made `failed` unreachable and `unverified` unreportable for any
    published revision.

    Ingestion hashing is not verification of the published revision. It reads
    the bytes in the *Hub cache*, before the publication tree exists, and its
    result is already recorded where it belongs — `manifest.verification.outcome`
    is `verified` and always will be, because a manifest is only published after
    ingestion succeeds (`docs/schemas.md` §3.4). `verify` reads the *tree*, which
    is a different set of bytes on a different filesystem at a different time,
    and `catalog/verification.json` is the record of that. Reporting `verified`
    for a revision nothing has ever re-read would make the field unfalsifiable —
    which is exactly the symptom the hardcoding produced.

    So: `clean` in the verification catalog is `verified`, `failed` is `failed`,
    and no entry is `unverified`. `publication.VerificationStates` is the single
    reader, and `publication._catalog_entry`, `cli._status_entry`, and
    `cli._listed_revision` all go through it. A newly published revision reads
    `unverified` until a `verify` covers it, which is what makes the §29 rollout
    checkpoint's `verify --full` a step that changes something observable.

    The two catalog models gained nullable `publication_id` for the same single
    case decision 49 gave `Finding`, and `docs/schemas.md` §5.2 now says so.

52. **`storage.write_model` takes the caller's error class, not just its code**
    (2026-07-26, `VER-005`). Decision 46 settled that an error's class and its
    code's family must agree, because the exit comes from the class and the
    `docs/cli.md` §5 classification comes from the family. `sha256_file` and
    `read_model` were fixed to take `error=`; `write_model` was not, and always
    raised `SafetyError`.

    Every existing call site was therefore mismatched. A failed reference write
    reported `HFSYN007` — documented as exit `30` — and exited `20`; a failed
    prune audit record reported `HFRET004` and exited `20` rather than `50`.
    Both send a scheduler to investigate the mount when the mount is fine and
    the run is what failed. `tests/unit/test_publication.py` had pinned the old
    behaviour with a comment explaining it, which is how it survived.

    `write_model` now takes `error=` with `SafetyError` as the default, and all
    nine call sites pair explicitly. `tests/unit/test_storage.py` parses the
    call sites out of `src/` with `ast` and checks each pairing against
    `taxonomy.classify`, so a new one is checked the moment it lands rather than
    at exit time during an incident.

53. **Evidence for a path a later checkpoint moves carries no `_path` suffix**
    (2026-07-26, `VER-006`). Decision 42 made evidence mechanically checkable
    with a key-naming convention: `_path` means "must still exist", `_absent`
    means "must not". `evidence_problems` enforces it, and `HFTXN003` — journal
    contradicts filesystem — stops the machine (§7.9).

    Three checkpoints recorded a `_path` for something the *next* checkpoint in
    their own sequence deliberately renames away: publication's `staging_built`
    named `staging_tree_path`, which checkpoint 5 renames into `published/`;
    prune's `tree_tombstoned` and `manifest_tombstoned` named paths under
    `.store/trash`, which checkpoint 9 removes. A journal that got past those
    steps therefore contradicted the filesystem *by design*, and recovery
    reported `HFTXN003` for the exact states §7.3 and §7.4 give roll-forward
    resolutions for. That is why the carried-in remedies could not simply be
    added: the evidence had to stop lying first.

    The rule is now: **evidence whose subject a later checkpoint in the same
    operation moves is recorded without a path suffix.** The value is still
    recorded and still re-observable by a person; it is just not asserted to
    still exist. Nothing loses the ability to *locate* anything, because
    `FS-18` guarantees every transaction area is derivable from the transaction
    id — which is how `_staging_remediation` and the prune remedies find their
    directories already.

    Repair follows the same rule for `corrupt_instance`, `original_manifest`,
    `isolated_cache`, `snapshot`, and `staging_tree`, all of which checkpoints
    14, 16, or 17 move — and it matters more there than anywhere, because a
    repair journal stays open for the whole seven-day grace and its evidence is
    re-checked by every `recover` in that window.

54. **`repair.py` added beyond plan §7's module list** (2026-07-26, `VER-006`).
    The fourth module added this way, after `preflight.py` (33), `archive.py`
    (36), and `locking.py` (40). §7 permits consolidating boundaries "where
    implementation remains small" and requires Hub access, storage mutation,
    retention, and verification stay independently testable; it does not say
    where repair goes.

    `retention.py` was the obvious candidate and is wrong: repair does not
    remove a revision, it replaces an instance of one, and the two transactions
    have opposite commit semantics — a prune's commit point makes deletion
    irreversible, while a repair never deletes at all. `sync.py` was the other
    candidate and is already the largest module in the project. Repair has its
    own §7.5 checkpoint sequence, its own two gates, its own crash matrix, and
    the only isolated cache in the design (`FS-14`'s single exception), so it
    is its own module. `docs/agents/history/plan.md` §7's listing is amended in this commit.

    The post-grace cleanup lives there too rather than in `recovery.py`, and
    recovery calls into it. Checkpoints 16-18 are steps of the *repair*
    transaction — recovery's job is to notice they are due and to run them, not
    to know how.

55. **A crashed sync run journal closes; it does not stop the machine**
    (2026-07-26, `SYNC-003`). Before this package nothing produced a `sync`
    journal, and `recovery._remediation` fell through to its final refusal for
    one: `HFTXN004`, blocked, operator decides. A test asserted exactly that.
    Once `sync` actually opens the §7.6 journal, that behaviour becomes
    unusable — every interrupted run would leave the archive refusing writes
    until a person cleared a journal about which nothing is ambiguous, and
    unattended operation is the point of the whole design (`AD-01`).

    §7.6 already said why it is not ambiguous: "the per-repository journals are
    the authority; the run journal exists to correlate them and to prove that
    reconciliation happened before Hub contact." Every mutation a run made is
    inside a publication or prune journal that has its own remedy. So the
    resolution is `close_journal`, whatever checkpoint the run reached, and
    `docs/architecture.md` §7.6 and §7.7 are amended in this commit to say so.

    Recovery deliberately does **not** roll a run forward through checkpoint 5,
    even though §7.7 permits rebuilding a catalog. Plan §13.1 step 10's rebuild
    reads *configuration* to decide which repositories are managed (`AD-06`),
    and recovery takes no configuration — rebuilding without it would mark every
    configured repository unmanaged, turning a merely stale derived file
    (`FS-16`) into an actively wrong one. The next sync rebuilds it correctly.
    The replaced test now provokes the genuine no-resolution case instead: a
    `recovery` transaction that itself crashed, which §7.7 gives no resolution
    for and which is still `HFTXN004`.

    Two smaller consequences, both load-bearing. The run journal excludes
    *itself* from reconciliation — `TX-01` opens it before the run may act, so
    it is unfinished for the whole run and a transaction cannot recover itself;
    `plan_recovery` gained `exclude` for that one caller. And a crash inside a
    run now leaves **two** open journals rather than one, which is what the
    filesystem has always implied and what six recovery tests had to start
    saying out loud: they now ask for the remedy of the operation they are about
    rather than taking `remediations[0]`.

56. **A committed publication or repair discards its staging area**
    (2026-07-26, `SYNC-004`). Found by running `status` on the live archive at
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

57. **The `--config` and `--token-file` options do not check readability at
    parse time** (2026-07-26, `HOST-004`). Found the moment
    `/etc/hfcache/config.toml` was installed at its documented `0640
    root:hfcache` (plan §21.2): every command run as an ordinary account began
    exiting `2` from typer's argument parser — including `hfcache version` and
    `hfcache --help`, which never open the file.

    Typer's `Path` parameter type defaults to `readable=True`, and with
    `exists=False` that means a path which does not exist passes while one that
    exists but is unreadable fails. `ExitCode` reserves `1` and `2` for a
    malformed command line "so a scheduler must be able to tell a malformed
    command line from an application outcome" — and a configuration file this
    identity cannot read is an application outcome. `load_config` already
    reported it correctly as `HFCFG001` at exit `10`, naming the path; the
    parser never let it get that far.

    Both options now pass `readable=False`, so the access decision belongs to
    the code that has an error taxonomy for it. `--token-file` gets the same
    treatment for the same reason: `HFARG005` at exit `10`, reported by shape and
    never by content. The mode on the configuration file is deliberately
    unchanged — it is the contract, and the fix is that the application reports
    it properly rather than that more identities can read it.

58. **The archive mount is defined by explicit units and the fstab line is
    retired** (2026-07-26, `SYS-001`). Plan §21.3 permits either mechanism, and
    the deployment had the fstab one from `HOST-003`. Keeping both is not a
    third option: a unit in `/etc/systemd/system` shadows the one
    `systemd-fstab-generator` produces from that line, so the file an operator
    would edit first would have had no effect at all. §22 lists the two units as
    shipped artifacts, so the units win and the fstab line is commented in place
    with a pointer to them; `/etc/fstab.pre-hfcache-units` holds the original.

    The handover was the risk — this session dies with the mount (§36.4) — so it
    was done with `daemon-reload` and nothing else. A reload re-reads unit files
    and does not stop active units, and a mount unit's active state comes from
    `/proc/self/mountinfo` rather than from its configuration. Confirmed after:
    the same autofs file descriptor, the same NFS mount with the same options,
    both units `active` and now sourced from `/etc/systemd/system`, and `status`
    still reporting the archive reachable. The unit's `Options=` apply from the
    next mount, not to the one already established, which is why `systemctl show`
    still lists the fstab-era `x-systemd.*` options.

    Two findings worth keeping. **`systemd-analyze verify` exits `0` while
    reporting ordering cycles**, so its *output* is the gate and its exit status
    is not — the same lesson as piping a gate into `grep`. And the first
    automount unit had one: `After=network-online.target` on the *automount*
    produced `local-fs.target → srv-hfcache.automount → network-online.target →
    NetworkManager.service → sysinit.target → local-fs.target`, because systemd
    gives every automount unit an implicit `Before=local-fs.target`. Network
    ordering belongs on the mount, which is the unit that contacts the NAS; an
    automount is a kernel trigger on a directory and needs nothing. The
    fstab generator had it right, and comparing against what it produced —
    `systemctl show` on the generated units, before the reload replaced them —
    is what found it.

    `hfcache.target` does **not** list the timers in `Wants=`. §22.4 says the
    target wants the automount and both timers, but a `Wants=` starts a unit
    whether or not it is enabled, and §34 requires the quarterly verification
    timer stay off until an operator confirms its calendar against the NAS
    schedules. The timers attach through their own `[Install]
    WantedBy=hfcache.target` instead, so what the target wants is exactly what
    has been enabled and "installed but disabled" is a state the design can
    actually express.

59. **The hardening is tested by a probe that reads the deployed unit**
    (2026-07-26, `SYS-002`). §22.5 says "test each setting against
    `huggingface_hub`, `hf_xet`, DNS, TLS, NFS, and Python native extensions",
    and a checklist an operator ticks is not a test. `scripts/check-hardening.sh`
    and `scripts/hardening-probe.py` are added beyond plan §7's layout, which is
    amended in this commit.

    One design decision carries the value: the probe does **not** restate the
    settings. `check-hardening.sh` reads the `[Service]` properties out of the
    installed unit file at run time and passes them to `systemd-run`, so the
    thing under test is the thing deployed. A probe holding its own copy would
    have gone green while the unit drifted, which is the failure mode of every
    security checklist.

    It asserts two different things. That the workload still runs — DNS, TLS, a
    real Hub API call, a real `hf_xet` download, the native extension imports,
    and a create/fsync/rename/unlink on the archive — because a setting that
    quietly breaks one of these does not announce itself; `snapshot_download`
    failing under `ProcSubset=pid` looks like a network problem at 02:00 on a
    Tuesday. And that each setting is *in effect*, because a property systemd
    parsed and could not apply reads as protection in the unit file and is not
    there.

    Two things it deliberately does not claim. `ProtectKernelTunables` and
    `ProtectKernelLogs` are confirmed only as *refusals*: `ProcSubset=pid`
    already hides `/proc/sys` and `PrivateDevices=true` already removes
    `/dev/kmsg`, so the refusal does not prove which line caused it. That is
    defence in depth, and reading the unit file rather than a copy is what keeps
    a removed line from going unnoticed. And the four network checks **invert**
    for the verification unit — reaching the Hub from it is the failure — because
    a probe that only ever asserted "the network works" would have to skip the
    offline unit entirely, and "the offline unit is actually offline" is the more
    valuable assertion of the two, being the one a dependency upgrade can quietly
    undo.

    The probe also confirms something the sandbox itself put at risk:
    `ProtectSystem=strict` bind-mounts the world read-only and `ReadWritePaths=`
    re-mounts the archive, and on an autofs path that could have captured the
    *trigger* instead of the NFS mount, leaving the service writing into an empty
    directory inside its own namespace. It reads the sentinel back to prove
    otherwise. All 21 checks pass on both units, and nothing was weakened to get
    there — the single failure was the probe's own bug, `ProtectHome=true` making
    `/home` inaccessible rather than empty.

60. **`IPAddressDeny=any` on the verification unit rather than
    `PrivateNetwork=true`** (2026-07-26, `SYS-002`). §22.3 asks that
    `PrivateNetwork=true` be tested on the deployed NFS mount and enabled "if the
    already-mounted filesystem remains reliable **under reconnect**".

    Both were tested. Under `PrivateNetwork=true` and under `IPAddressDeny=any`
    alike, a probe read all 21 published files — 12 721 220 bytes — off the
    already-mounted archive while outbound TCP and DNS both failed. Steady-state
    reads are fine either way, so that is not what decides it.

    The condition is the reconnect, and it cannot be met here: §36.4 defers NFS
    interruption against the live mount to an operator-supervised window, so this
    session has no way to provoke one. §22.3's own instruction for that case is to
    keep the command application-offline and document the narrower host egress
    control — so `HF_HUB_OFFLINE=1` stays, the structural guarantee stays
    (`verify` builds no `HubClient` and resolves no credential, asserted in the
    suite), and the third layer is `IPAddressDeny=any`.

    It is the better fit independently of the untested condition.
    `IPAddressDeny` filters the unit's own sockets through its cgroup and does not
    move the unit into a different network namespace at all; the NFS client's RPC
    sockets belong to the kernel and are untouched, so there is no reconnect path
    to be unsure about in the first place. `PrivateNetwork=true` would put the
    process in a namespace holding only loopback, and any NFS behaviour that
    depends on the caller's namespace — an upcall, a referral, a re-established
    connection — becomes a question this deployment cannot currently answer.

    Handoff item 10 carries the `PrivateNetwork=true` evaluation for the operator
    window that can answer it.

61. **`RestrictSUIDSGID=true` is the one §22.5 setting not applied**
    (2026-07-26, `SEL-001`). Found by a real sync failing under the hardening
    with `HFSYN005`: `staging ... could not be created: Operation not permitted`.

    The failing requirement. `publication.create_staging` creates the staging
    tree at `PUBLISHED_DIRECTORY_MODE = 0o2750` — setgid — because publication is
    a rename and a rename does not change a mode, so that is the only moment the
    published directory's mode can be set. The setgid bit is what carries the
    group the consumer export's read identity depends on (§5.2), and the
    `published/` anchor the NAS was provisioned with is `2750` for the same
    reason. `RestrictSUIDSGID=true` is implemented as a seccomp filter on the
    mode argument of `mkdir`/`chmod`/`mknod`, so it refuses that call outright.
    Attribution was proven rather than assumed: the same `mkdir(0o2750)` on the
    archive was run in two transient units differing only in that setting, and it
    is `Operation not permitted` under `true` and succeeds under `false`.

    The alternative that was rejected: stop asking for setgid and rely on the
    parent directory's inheritance. That trades a durable, consumer-visible
    on-disk contract for a hardening flag, and it would be silent when it was
    wrong — a published tree that quietly lost its group would only surface as a
    consumer permission failure, on a different host, later.

    The narrower control that replaces it. The escalation `RestrictSUIDSGID`
    exists to prevent is closed twice over: `/srv/hfcache` is mounted
    `nosuid,nodev,noexec`, so a setuid or setgid file on the only filesystem this
    service can write is inert; `NoNewPrivileges=true` means this service and
    every child can never gain privileges from such a bit wherever it sits; and
    the capability bounding and ambient sets are empty. The systemd-managed
    directories are `0750`/`0700` `hfcache:hfcache`, reachable only by this
    account and root, and root ignores setgid on exec anyway. It is dropped on
    **both** service units rather than only the one that needs it: two units with
    different hardening is a trap for whoever next adds a drop-in that runs
    `repair`, and the security delta is nil given the above.

    The probe missed it, and that is the more useful half of this entry. Its
    first version wrote *files* to the archive and never created a directory with
    the setgid bit, so the incompatibility surfaced as a failed sync rather than
    as a failed check — the exact thing `scripts/hardening-probe.py` exists to
    prevent. It now creates a setgid directory and a hardlink on the real archive,
    and both are among the 23 checks that pass.

62. **The reported verification state is keyed by publication instance, not by
    SHA** (2026-07-26, `VER-007`). Found at `SEL-001` by the retention rotation:
    a dataset revision that had been pruned and later re-synced read `verified`
    in `status`, on the strength of a verification of the instance the prune had
    removed.

    `catalog/verification.json` has recorded `publication_id` per revision since
    `VER-005`. `VerificationStates.of` keyed its lookup on
    `(repository_type, repository_id, commit_sha)` and discarded it. A
    verification re-reads the bytes of one published *instance*, and two
    instances of one SHA are different bytes in different places — a repair
    replaces one, and a prune followed by a later republication of the same SHA
    produces another. So `verified` became true of content nothing had ever
    re-read: decision 51's unfalsifiable field, reappearing through a different
    door, and reappearing in exactly the window an operator would look at, the
    one between publishing a revision and verifying it.

    The key is now the instance, and the three call sites — `status`, `list`, and
    the derived catalog — each pass the publication id the reference or the
    manifest they already hold carries. An entry whose `publication_id` is null
    raises nobody's confidence, because it cannot be attributed to anything on
    disk and the conservative answer to "was this instance re-read?" is no.

    No durable format change was needed; the field was already there.
    `docs/schemas.md` §5.2 now states the key. A repair was never affected —
    `VER-006`'s checkpoint 8 re-verifies the replacement before any reference
    moves, so it records its own entry — which is why this only ever surfaced
    through a prune.

63. **§24's host half is two shipped files, not two runbook steps** (2026-07-27,
    `OBS-001`). Both of §24's last bullets could have been discharged as
    instructions in `OPS-001` — "enable persistent journald", "consider an
    `OnFailure=` hook". They are shipped artifacts instead, for two different
    reasons.

    The journald setting, because §33 requires a fresh VM be reproducible **from
    documentation** and a setting that lives only in prose is one an operator
    silently skips. It is host-wide policy set by an application package, which
    would be presumptuous on a shared machine; this is a dedicated
    single-purpose writer (§21.1), so it is merely explicit. The values are
    bounded on both axes because they protect different things —
    `SystemMaxUse=1G` bounds the root filesystem the Xet cache shares, and
    `MaxRetentionSec=1year` bounds how far back an operator can look, at four
    quarterly verifications. `SystemKeepFree` is left at its 15% default, which
    is already the setting that stops the journal filling the disk under a
    download.

    The hook ships **uninstalled**, and the two halves of that are worth
    separating. §24 asks that a hook be *left* for future monitoring, and this
    deployment has nobody to notify: a handler that only reprints what systemd
    already logged is a seam, not a control, and installing one adds a unit that
    fires on every failure to no end. So it ships like
    `credential.conf.example` beside it — complete, with the matching
    `OnFailure=` commented in both units, so activating it is two documented
    steps.

    But an example nobody has run is the thing decision 59 warns about, so it
    was installed and fired against a real failed unit first, and withdrawn
    afterwards. Two properties are load-bearing and both were confirmed rather
    than assumed: `ExecMainStatus` carries the application's §11.2
    classification through systemd unchanged (`10` observed for an `HFCFG001`),
    and `InvocationID` resolves through `journalctl _SYSTEMD_INVOCATION_ID=` to
    that run's output and nothing else. The handler deliberately only reads. A
    failure handler that restarts or resets turns one bad run into a loop, and
    there is no hfcache failure mode where the right response is to try again
    immediately — `AD-16` says ambiguity stops the machine.

    **Why this preceded the runbooks rather than following them.** `OPS-002`
    would otherwise have had to write two instructions that were false: "check
    the journal for the failure", against a store that did not survive a reboot,
    and any statement that a failed run is noticed. The ordering is the point,
    not a preference.

    **What is deliberately still open.** The durable run report remains the
    record of what a run *did*; the journal is the record of what happened when
    a run could not get far enough to write one. `OBS-002` closes the gap
    between them by making the journal structured — today it carries systemd's
    start/stop lines and the CLI's human table rows, and nothing carrying a
    `run_id`.

64. **The event log is emitted, not returned; and its vocabulary is closed**
    (2026-07-27, `OBS-002`). Two choices carry this module, and both were
    between something testable and something merely tidy.

    **A module-level logger rather than a threaded-through object.** The
    alternative was an `EventLog` instance passed from the CLI down through
    `sync`, `publication`, `retention`, and `recovery`. That is the design that
    survives a second concurrent run in one process — and `AD-17` says there is
    exactly one writer and the lock is local, so a second run in one process is
    not a state this application has. What the threaded version would actually
    have bought is an extra parameter on eleven functions whose signatures plan
    §13.2 already fixes, and `# noqa: PLR0913` on several of them. The module
    keeps its state resettable and `reset()` is what the suite uses between
    tests, so the usual objection — leakage — is closed where it could bite.

    **`emit` raises on an unknown name.** A logger that quietly accepts any
    string is the normal shape, and it is wrong here. The names are the
    interface: `docs/cli.md` §6 tells an operator to filter on
    `event=publication.completed`, and a typo would produce a line that looks
    right in a terminal and matches nothing. Every call site is in this
    repository and covered, so the raise cannot reach production; what it does
    reach is the test run of whoever adds the fourteenth event.

    **Where `retention.deferred` had to go.** §7.4 lists a `cleanup_deferred`
    checkpoint and `transactions.py` accepts the name, but nothing in
    `retention.py` records one — the post-commit steps run inline and a failure
    there leaves a tombstone rather than a marker. So there is no moment in a
    prune at which "cleanup was deferred" is known. The tombstone found later by
    `recovery._deferred_warnings` is the only real signal, and the event is
    emitted there, beside the `HFWRN002` it already raises. The checkpoint name
    is left in place: it describes the state §7.4 intends, and closing that gap
    is a durable-contract change rather than a logging one.

    **One incoherence fixed in passing.** `emit_envelope` minted a fresh run id
    for any command that wrote no durable report, and its own docstring claimed
    this "still ties the envelope to that invocation's log lines" — which was
    true of nothing, because there were no log lines. Now that there are, the
    envelope reports the id `configure` bound, and the claim is true.

65. **Plan §30 step 1 would have unmounted the archive; and a rollback needs two
    releases** (2026-07-27, `OPS-001`). Two things found by performing §30
    instead of describing it, which is the entire argument for the requirement
    that a runbook be exercised.

    **The unmount.** §30's upgrade step 1 said "stop `hfcache.target`". §22.4
    puts `PartOf=hfcache.target` on `srv-hfcache.mount`, and `PartOf=` propagates
    stops — so the documented first step of every upgrade takes `/srv/hfcache`
    away. For an operator that is recoverable and nearly invisible, because the
    automount re-triggers on the next access. For this session it is fatal
    (§36.4), which is how it was noticed rather than performed.

    What step 1 is *for* is that no job is running when `current` moves, and
    stopping the two timers achieves exactly that. §30 is amended to say so and
    to keep the reason attached, because "stop the target" is the obvious thing
    to write again in six months. The `PartOf=` on the mount is deliberate and
    stays: it is what makes `systemctl stop hfcache.target` mean "stop using the
    archive", which is the right meaning for every purpose except this one.

    **The second release.** A rollback exercised against a single installed
    release is not a rollback; `--switch 0.1.0` when `current` is already 0.1.0
    proves only that the symlink can be rewritten. So the version was moved to
    **0.1.1** — which `OBS-001` and `OBS-002` had earned anyway, the event log
    being a new observable surface — 0.1.1 was installed and switched to, and the
    rollback went genuinely backwards to 0.1.0 and then forward again.

    The step worth keeping from that is the third one, not the switch:
    `recover --dry-run` on **0.1.0** against an archive **0.1.1** had written
    reported `actionable 0`, `blocked 0`. That is the property rollback actually
    depends on — durable formats are versioned and a newer one is refused rather
    than read speculatively — and it is worth re-checking whenever a release
    touches a durable format. This one did not; the event log writes nothing
    durable.

    0.1.1 is not a release in the `REL-003` sense and is not tagged. It exists so
    that two releases exist.

66. **A setgid directory on this mount is made by `chmod`, not by `mkdir`'s mode
    argument** (2026-07-27, `HARD-001`). Not a deviation from a plan sentence —
    the plan never says *how* `0o2750` is achieved — but a durable fact about the
    archive's mode contract that two documents imply the opposite of, and that
    the standing guard on that contract was silently wrong about.

    `docs/architecture.md` §5.2 describes directories under `published/` as
    "inherited setgid plus `UMask=0027`", which is true of the *children* of a
    published tree and false of its root. The root is created in
    `.store/staging/<txn>/`, which is `0o700` and carries no setgid to inherit,
    and it reaches `published/` by rename — and a rename does not change a mode.
    So the one moment the bit can be set is at creation, and
    `publication.create_staging` has always set it with `mkdir` **followed by
    `chmod`** (`publication.py:139-140`). The `chmod` reads as belt-and-braces
    beside the `mkdir(mode=...)`. It is not: it is the line that works.

    Measured as the service identity on `/srv/hfcache/.store/health`, `mkdir`
    alone yields `0o750` and `mkdir`+`chmod` yields `0o2750`. POSIX does not
    guarantee `mkdir` honours setgid in its mode argument, and this NFSv4 server
    does not; `umask` is not the cause, since the bit is absent under a umask that
    does not mask it. Nothing was broken by this — the live published tree is
    `2750`/`2755` throughout — because the application had the `chmod` from the
    start. What was broken was the *probe*, which had only the `mkdir` and
    therefore tested a call the application does not depend on.

    Two consequences worth attaching to the fact rather than rediscovering.
    Removing that `chmod` as redundant would silently drop the group the consumer
    export's read identity depends on, and it would surface as a consumer
    permission failure on a different host, later — the same shape of failure
    decision 61 rejected when it declined to trade the bit for a hardening flag.
    And decision 61's watch item is now genuinely checkable: `RestrictSUIDSGID`
    filters the mode argument of `chmod` as well as `mkdir`, so if that setting
    ever becomes applicable again, this check is what fails first.

67. **The consumer helper is `examples/copy-revision.py`, and it may not import
    `hfcache`** (2026-07-27, `OPS-007`). Plan §6.3 requires "a small shell/Python
    example that copies the tree and verifies it against the referenced manifest"
    and §33 requires that a downstream system can do exactly that, but plan §7's
    layout gave the example no home: `examples/` listed only `config.toml`. §7 is
    amended in this commit to list it.

    Where it went. `scripts/` was the other candidate and is wrong: everything in
    it — `check.sh`, `install-release.sh`, `check-hardening.sh` — is run by the
    *operator* on the writer, against a deployment. This is run by someone else,
    on a machine that has no deployment. `examples/` also ships in
    `RELEASE_CONTENT`, so the helper reaches `/opt/hfcache/current/examples/` and
    an operator has something to hand to a consumer.

    The constraint that shaped it: **standard library only**. The tempting
    alternative was to reuse `hfcache.verification`, which already hashes a tree
    against a manifest and is far better tested than anything written here. It was
    rejected because it inverts the dependency the archive exists to avoid. A
    consumer is a machine that mounts one read-only NFS export; requiring it to
    install this project — and therefore `huggingface_hub`, `pydantic`, `hf_xet`,
    and a Python 3.14 that CentOS Stream 10 does not ship — to *read a directory*
    would make the archive harder to consume than the Hub it is caching. The cost
    is a second implementation of the verification loop, and it is paid knowingly:
    the helper duplicates roughly forty lines of hashing and path checking.

    That duplication is also a mild benefit, and it is why the helper was proven
    against damage rather than only against success. It is an independent reading
    of the same manifest: it was run on a throwaway tree with a byte flipped, a
    file removed, and a file added, and it caught all three. If it and the
    application ever disagree about a published revision, that disagreement is
    information — one of them is wrong, and the manifest says which.

    Exit codes are the helper's own (`0`/`1`/`2`) and deliberately not §11.2's.
    It is not this application, it does not run on this host, and borrowing
    `40` for "digest mismatch" would imply a shared taxonomy that does not exist.

68. **A prune's container cleanup is checkpoint 10, after the commit point, and
    its atomic act is `rmdir`** (2026-07-27, `RET-008`). Plan §15.2 and
    `docs/architecture.md` §7.4 both described a prune that tombstones the
    publication instance and its manifest and then stops. Both are amended here,
    because that leaves two directories that nothing ever removes.

    What the documents missed. The instance is
    `revisions/<sha>/<publication-id>/` and its manifest is
    `manifests/<sha>/<publication-id>.json`, so tombstoning empties the `<sha>`
    directory *above* each of them. Nothing derived is wrong when they linger —
    `list`, `status`, the catalog, `next_generation`, and `verify` all resolve
    through references, and all five were checked against the live archive after
    the 2026-07-26 rotation. But they are permanent, they accumulate one pair per
    pruned SHA, and they are in `published/`, so a consumer listing `revisions/`
    sees SHAs the archive does not retain. The carried item named only the first
    of the two; the second was found by looking at the live archive rather than at
    the text.

    **Where it goes, and why not earlier.** The obvious placement is right after
    the two tombstoning steps, where the containers become empty. That is wrong,
    and the reason is the rollback path. Before checkpoint 7 the transaction can
    still be rolled back, and `recovery._rollback_prune` puts the tree and the
    manifest back *into these exact containers*. Removing them pre-commit would
    make the rollback recreate them, which adds a failure mode to the one path in
    §7.4 whose entire purpose is to restore six revisions safely. Post-commit,
    the revision is never coming back, and an empty directory is definitionally
    cleanup — which is precisely the regime checkpoints 8 and 9 already occupy and
    which §7.4 already says is the only thing retried later. The cost is a window:
    a crash between 7 and 10 leaves the containers until the next `recover
    --apply`. That is reportable, harmless, and tested.

    **Why `rmdir` and never `rmtree`.** Two states require a container to survive
    its own SHA being pruned, and both are real: a repair inside its grace period
    leaves the retired instance beside the replacement, so `revisions/<sha>/`
    holds two instances; and a superseded manifest can sit beside the tombstoned
    one. `rmdir` refuses a non-empty directory, so neither state needs to be
    detected, and the code cannot be wrong about them — the kernel is. `rmtree`
    would silently take both. `FS-19` is the rule this satisfies: the application
    removes a directory it has *proven* empty, not one it has decided is unwanted.
    `ENOTEMPTY` and `EEXIST` are the two answers POSIX permits for that refusal
    and both are treated as "keep"; `ENOENT` is idempotence (`TX-04`); anything
    else propagates, because reporting a permission failure as though the
    directory had merely been busy would hide it forever.

    The live archive was brought into conformance in the same commit rather than
    left as a documented exception, because `OPS-003` documents this tree's shape
    next and a runbook describing a shape the archive contradicts is worse than
    either. The removal used `rmdir`, which cannot destroy content;
    `verify --full` afterwards read 23 unique objects across 6 revisions and
    reported `clean`.

69. **There is no `tests/integration/`; the tier lives beside its fixtures, and
    §26.6's map is a test rather than a comment** (2026-07-27, `OPS-005`). Plan
    §7 listed `tests/integration/` from Phase 0 and it never held anything but
    `.gitkeep`. Two ways to resolve that, and the plan is amended rather than the
    tree populated.

    The reason is not effort. §26.2 names eighteen integration behaviours — first
    sync, sixth-revision rotation, interrupted publication at each transaction
    boundary, corrupt catalog reconstruction, and so on — and **every one of them
    exists and passes**. They sit in `tests/unit/` because they share the fixtures
    of the modules they exercise: `client`, `layout`, `config`, and the injectable
    fake Hub. Moving them would separate each from the fixture that builds its
    world, and would need those fixtures duplicated or promoted into a conftest
    serving two directories, for no gain in what is tested.

    The deeper reason is that the tier boundary does not fall where the directory
    split would put it. `tests/unit/test_synchronize.py` holds both a pure
    retention-ordering assertion over in-memory objects and a full six-revision
    publish-and-prune cycle against a fake Hub and a real temporary filesystem.
    Those are a unit test and an integration test by any definition, they are
    fifty lines apart, and they belong together because they are about the same
    thing. A directory that sorted them would be sorting by a property nobody
    reading the file cares about.

    What the empty directory *was* hiding is worth stating, because it is the
    real defect and it is not a layout problem: the whole §26.6 failure-injection
    matrix lives in `tests/unit/test_repair.py`, whose name suggests it holds
    repair tests. It holds the publication boundaries, the prune boundaries, the
    recovery remedies, and the repair switches — twenty-four crash injections
    through one `crash_at` helper. Nothing pointed at them, and the coverage
    claim in plan §28 had to be re-derived by reading them.

    So `tests/unit/test_failure_matrix.py` is the index, and it is executable:
    it names the covering tests for each of the eleven points and asserts every
    name still resolves. It found a wrong attribution in itself on its first run.
    Renaming `test_repair.py` to match its contents was the other candidate and
    was rejected as churn against a green suite with the phase unfinished; the
    map makes the location discoverable, which is what was actually missing.

70. **An artifact that will not parse is not an absent artifact** (2026-07-27,
    `REP-001`). Not a deviation from the plan — the plan is right and the code
    disagreed with it. `docs/architecture.md` §7.9 says a state recovery cannot
    resolve unambiguously stops the machine, and `TX-06` says a transaction that
    can fail either way leaves more rather than less. This path did neither.

    `pending_cleanups` skips a retirement record it cannot read. That is correct
    and deliberate: it answers a scheduling question, and one damaged record must
    not hide the others from `HFWRN008`. Its docstring even says which commands
    are responsible for reporting damage instead.

    `_repair_remediation` then asked it a different question — "does this repair
    still have a cleanup outstanding?" — and read the empty answer as *no*. So a
    record that could not be parsed became a repair that was finished, and the
    remedy became `close_journal`. The journal is left open past checkpoint 15
    for one reason, stated at the top of `repair.py`: it is the only durable
    record `recover` can find on its own, and it is what stops a deferred cleanup
    from being forgotten. Closing it forgot the cleanup. `status` kept warning
    `HFWRN008` and kept naming `recover --apply` as the remedy, which now
    reported `actionable 0`. The retired tree stayed published indefinitely.

    The rule this settles, and it generalises past this one call site: **a
    tolerant reader and a decision procedure must not share a return value.**
    Skipping a damaged artifact is a kindness to a *report*; to a *decision* it is
    a false negative, and here the false negative resolved toward discarding
    work. Where a function has to answer "is there any", callers that will act on
    "no" need to be able to distinguish "none exist" from "I could not tell", so
    `unreadable_retirements` exists to be asked the second question and the
    remediation is `BLOCKED` with `HFTXN003` when the answer is yes.

    Found by running `OPS-003`'s drill rather than by the suite, and it took a
    real deployment to surface: every test that damages a retirement record
    damages it while checking something else, so nothing had ever asked recovery
    what it made of one. That is the same argument `SEL-001` made for rolling out
    before declaring anything done, and this is the fifth defect it has produced.

71. **The release is deployed from a wheel already; it is not deployed from
    `dist/`, and it should not be** (2026-07-27, `REL-001`). Plan §28 and the
    Phase 8 checklist both assert that `install-release.sh` "stages a source tree
    and runs `uv sync`", so no deployed release has been installed from the built
    artifact. The first half is right and the conclusion does not follow.

    What is actually installed. `uv sync --frozen --no-dev --no-editable` builds
    a wheel *from the staged release tree* and installs that wheel. The evidence
    is in the deployed venv: `hfcache-0.1.2.dist-info/` carries a `WHEEL` file
    reading `Generator: uv`, `Root-Is-Purelib: true`, `Tag: py3-none-any`, plus a
    `RECORD`. There is no `.pth` file, no editable install, and `src/` is not on
    `sys.path`. `--no-editable` is the flag that makes this so, and it has been
    there since `HOST-004`. The application on the writer is a wheel.

    What is true is narrower: the deployed wheel is not the file in `dist/`. It is
    an equivalent wheel built at deploy time from the same sources. Changing that
    was considered and rejected on two grounds. `dist/` is a build directory whose
    contents can come from a different checkout than the tree being staged — it
    is `.gitignore`d and was last rewritten by a test run — so installing from it
    would let the deployed code diverge from the release tree sitting beside it,
    which is a new failure mode bought with no new guarantee. And `uv pip
    install`ing a wheel resolves its dependencies fresh; `uv sync --frozen` is
    what applies `uv.lock` exactly, and the lock is the entire reproducibility
    story. Trading a lockfile for a filename is a bad trade.

    So the mechanism is retained, `docs/deployment-centos-stream-10.md` §§13–14
    keep their exercised output because nothing about the procedure changed, and
    the built artifact keeps being smoke-tested into a clean virtual environment
    by `tests/system/test_wheel_smoke.py` under `-m build` — which is the fallback
    the work package itself names for this outcome.

    The plan text is left as it stands rather than corrected in place: it
    described a real gap in good faith, and this entry is the answer to it.

72. **A throwaway archive has to be a real NFS mount, so the writer exports one
    to itself** (2026-07-27, `OPS-003`). Plan §28 says the corruption and repair
    runbook is "exercised on a **throwaway archive**, never on `/srv/hfcache`",
    and does not say what a throwaway archive is. It cannot be a directory.

    §19's preflight requires the archive root to be a **mount point whose
    filesystem type is `nfs` or `nfs4`**, read from `/proc/self/mountinfo`, and
    there is no configuration escape hatch and no environment override — the test
    suite substitutes the mount table by monkeypatching a module constant, which
    is not available to a CLI invocation. So the options were to add an override
    to production safety code so a document could be written, to run the drill
    through Python and bypass the preflight the runbook is supposed to
    demonstrate, or to provide a real NFS mount.

    The third is the only one that leaves the application alone, and it is
    cheaper than it sounds: `nfs-utils` is already installed as the client,
    `nfs-server` was disabled and inactive with nothing on port 2049, and a
    one-line export to `127.0.0.1` gives a genuine NFSv4.2 mount that the
    preflight, the hardlink probe, and the atomic-rename probe all accept. It
    touches no TrueNAS state, needs no second host, and cannot reach
    `/srv/hfcache` — the export is a different directory with a different archive
    UUID. The live mount was checked after each step of standing it up.

    Two things about it are worth writing down because both cost a cycle.
    Mounting `127.0.0.1:/` gets the NFSv4 **pseudo-root**, which is read-only; the
    export path itself is what you mount. And the throwaway needs its **own
    `archive_id`** in its own config, because the sentinel is what stops a
    misdirected command, and reusing the real UUID would defeat exactly the check
    that protects the real archive.

    The runbook ships the recipe (`docs/recovery.md` §6) rather than leaving it
    implicit, because a repair rehearsal an operator cannot perform is a repair
    procedure nobody has tested — which is the same argument `SEC-001` and
    `OBS-001` made for exercising the credential drop-in and the failure hook.

73. **Verification enumerates the retained set, and `current.json` is not in it**
    (2026-07-27, `VER-008`). Plan §16.2 step 3 says the quarterly job "validates
    refs, manifests, and publication paths", and `docs/schemas.md` §4.2 states an
    invariant in plain words: `current.json` always names a SHA that also has a
    `refs/revisions/<sha>.json`, and both agree on `publication_id`. Nothing
    checked it, and the reason is structural rather than an oversight in one
    function.

    `resolve_repository` walks `refs/revisions/`, and it is right to: a per-SHA
    reference is what *makes* a SHA retained (`FS-11`), and enumerating the
    revision directories instead would verify a repair's retired instance and
    report an archive as degraded for holding evidence it was told to keep.
    `current.json` sits outside that set by design — it is a pointer *into* it —
    so a traversal defined as "every retained revision" reaches every byte a
    consumer might copy and never reaches the file that tells them which bytes.

    What that cost: point `current.json` at a publication id that does not exist
    while leaving the per-SHA reference correct, and `verify --full` reports
    `outcome: clean` at exit `0`. Every retained revision really is intact — the
    traversal is not lying — but the archive is in `FS-10`'s forbidden state and
    the integrity command says it is healthy. A consumer resolving that reference
    finds nothing, and `docs/consumers.md` tells it to treat a vanished tree as
    retryable, so it retries against a permanently dangling pointer.

    The fix reuses `ref_invalid`/`HFVER008`, so there is no durable-format change,
    and it is deliberately narrow. When the per-SHA reference is itself the
    damaged artifact, `resolve_revision` already reports it and this reports
    nothing: one broken file, one finding. The first draft did not observe that
    and five existing tests failed, which is the suite doing its job.

    The limit is worth stating because it is a real one. A `current.json` that
    will not parse at all yields no finding here, because `Finding.commit_sha` is
    required and an unparseable reference supplies none — `refs/revisions/<sha>`
    carries its SHA in its *filename* and `current.json` does not. Attributing the
    damage to an arbitrary retained revision would be a worse answer than
    silence. It is not actually silent: `status` drops the repository to
    `unverified`, and the consumer helper fails closed on it. Widening
    `Finding.commit_sha` to optional would close it properly and is a schema
    change, so it is left to a release that has a reason to make one.

74. **The interpreter directory is part of the deployment and was outside every
    sweep** (2026-07-27, `REL-002`). `install-release.sh` makes the release tree
    root-owned and read-only to the service identity, because plan §21.4 wants
    the account that runs the archive unable to modify the code that runs it. It
    does that with `chown -R` and `chmod -R` over `${RELEASE}`.

    `/opt/hfcache/python` is not under `${RELEASE}`. It holds the uv-managed
    CPython 3.14.6 that `HOST-004` installed there precisely so the venv would not
    depend on an interpreter under `/home` or on the distribution's 3.12, and it
    is deliberately *not* rebuilt per release — one interpreter serves every
    release, which is what makes a rollback a symlink switch. So the per-release
    sweep never touches it, and `uv python install` leaves `.lock` at `0666`.

    The exposure is small and worth stating precisely rather than dramatising: a
    zero-byte lock file that uv uses to serialise interpreter installs, with the
    interpreter binaries themselves root-owned `0755`. No code execution follows
    from writing it. But it is a world-writable regular file inside the prefix
    §21.4 says is root-owned, an unprivileged local user could interfere with a
    future `uv python install`, and "the deployment contains nothing
    world-writable" is a cheaper property to hold than to reason about each time.

    Two things this changes. The mode is narrowed to `0644`, which costs nothing
    because every caller of `uv python install` in this script is root and root
    ignores the write bit. And the sweep is extended to the interpreter directory,
    at `-maxdepth 1` so it corrects uv's own artifacts without walking 1 048
    symlinks and several thousand files of standard library on every install.

    The finding also says something about how the review found it. `find -perm
    -o+w` returned 1 049 paths and 1 048 of them were symlinks, whose modes are
    meaningless — a scan that reported "1 049 world-writable files" would have
    been dismissed as noise. Filtering to `-type f` is what turned an unreadable
    result into a one-line fix.

75. **The first release is `v0.1.2`, because that is what is deployed**
    (2026-07-27, `REL-003`). Plan §28 leaves the version open and notes that
    0.1.1 is live and untagged. Three candidates, and the accident of the
    numbering is the interesting part.

    0.1.0 and 0.1.1 were never releases in this sense. 0.1.0 existed because
    `HOST-004` had to prove `install-release.sh` worked at all. 0.1.1 existed
    because `OPS-001` discovered that a rollback exercised against a single
    installed release proves only that a symlink can be rewritten (decision 65),
    so a second release had to exist for the first to be rolled back from. Both
    are retained under `/opt/hfcache/releases`, and both remain useful for exactly
    that: §21.4 item 7 wants the previous release kept.

    Re-cutting a tidier number — 0.2.0, say, to mark the phase — was rejected
    because it would tag an artifact nobody had deployed. 0.1.2 is the tree that
    was installed by the documented §13 procedure, passed 23 of 23 hardening
    checks on both units, verified clean over six revisions, and served as the
    *new* side of a genuine cross-format rollback check. Tagging it means the tag,
    the running code, and the evidence in this file all name the same thing.

    Not `1.0.0`, and the reason is not modesty. §33's definition of done includes
    the consumer export, snapshots and replication, the disjointness proof from a
    second client, reboot persistence, and the quarterly verification timer. Every
    one of those is real, none can be performed from the writer, and all five are
    in the operator handoff. A `1.0.0` asserting them would be the same kind of
    unfalsifiable claim decisions 51, 62, and `HARD-001` exist to remove.

    The tag is annotated, so `git show v0.1.2` carries the release note and does
    not depend on a file the plan's §7 layout does not list.

76. **The rename decision 69 deferred is performed, and the index that made it
    safe now checks itself** (2026-07-27, `OPS-008`). Decision 69 rejected
    renaming `test_repair.py` as churn against a green suite with the phase
    unfinished, and built the executable matrix instead. Both halves of that
    reasoning have now expired in its favour: the phase is finished and v0.1.2
    is tagged, so the churn argument no longer applies — and the matrix it
    built is precisely what makes the rename a mechanical, verified operation
    rather than a risk. Every one of the 21 references the matrix holds to the
    module resolves by import, so a missed rename is a failed suite, not a
    silent gap. The deferral was correct then and paying it now is correct for
    the same reason: the safety was built first.

    The name matters because decision 69 said it did: the file holds the
    publication boundaries, the prune boundaries, the recovery remedies, and
    the repair switches — 25 provoked crash injections — and "nothing in
    `test_repair.py`'s name suggests" that was the stated defect. The matrix
    made the contents *discoverable*; the rename makes them *legible* from the
    directory listing. Sequenced first in this closeout so `VER-009`'s new
    tests land against the final module names and the matrix is edited once.

    The second half is the same defect decision 69 fixed, one layer up.
    `MODULES` claimed, in a comment, to be "every module named in `MATRIX`" —
    and it listed `tests.unit.test_verification`, which no row references. The
    comment was an honor-system claim sitting in the very file whose docstring
    says "a coverage claim in a comment rots silently. This one cannot." It
    had rotted. The fix is the file's own medicine: a test derives the module
    set from `MATRIX` and asserts `set(MODULES)` equals it, which closes both
    drift directions — a module the matrix gains must be added, and a module
    it loses must be removed. `test_verification` is dropped rather than a row
    added, because the audit stands: the §26.6 point that touches verification
    ("during quarterly verification") is covered from `test_verify_command`,
    where the interruption tests actually live.

77. **The docs move to the code, because the built mechanism already delivers
    §7.4's semantics and a failure-time checkpoint buys recovery nothing**
    (2026-07-27, `RET-009`). Two ways to reconcile "records a `cleanup_deferred`
    checkpoint" with an implementation that records no such thing: make the
    code write the checkpoint, or make the docs describe the mechanism. The
    second is chosen, and not because it is less work.

    What §7.4's failure regime actually promises is behavioural: never
    republish past the commit point, and retry only post-commit cleanup later.
    The implementation delivers exactly that, through the journal itself — a
    failure in steps 8–10 leaves the journal open at the last recorded
    checkpoint, and an open prune journal that has reached
    `prune_logically_committed` *is* the durable statement that cleanup is
    outstanding. `recover` derives everything it needs from two facts it
    already has: which checkpoints were reached, and whether the tombstone is
    present. A `cleanup_deferred` checkpoint recorded during the failure would
    restate the conjunction of those facts — and a marker written *while
    failing* is evidence of the weakest kind, since the failure that prompted
    it can just as easily take the marker down with it. The open journal
    requires no successful write at failure time; it is already on disk.

    Removing the permit instead of keeping a dead vocabulary entry follows
    from what the vocabulary check is for: `HFTXN002` exists to refuse "a
    journal no valid execution produces", and no valid execution has ever
    produced this checkpoint — its only writer in the entire tree was the test
    asserting it was permitted. The permit was, in miniature, the same
    honor-system defect as decision 76's module list: machinery attesting to a
    behaviour nothing exhibits. The inverted test is the falsifiable form —
    if a future release starts recording the checkpoint without widening the
    vocabulary deliberately, the suite fails.

    The removal is safe against every real archive for the same reason the
    permit was dead: no journal has ever contained the checkpoint (the live
    archive's 34 were scanned, zero matches), so no existing journal becomes
    refusable. Re-adding it later, should a release ever want the checkpoint
    recorded, is a one-line permit plus the standard cross-format note — the
    same widening path `containers_removed` took at `RET-008`.

78. **`commit_sha` widens to nullable with no schema bump, and the entry the
    retained-key rule cannot see gets its own clearing rule** (2026-07-27,
    `VER-009`). Decision 73 stated the limit honestly: a `current.json` that
    will not parse names no revision, `Finding.commit_sha` was required, and
    attributing the damage to an arbitrary retained revision would be a worse
    answer than silence. It also named the fix — widen the field — and left it
    "to a release that has a reason to make one". This is that release, and
    three choices in the widening are worth recording.

    **The null is guarded, not merely optional.** A nullable field with no
    constraint would let any finding drop its revision, and a report that
    attributes nothing is a report nobody can act on. The model validators
    hold `null` to the one shape this module produces — `ref_invalid`,
    `publication_id` null, `path` null — so the schema says what the docs say:
    one case, exactly. `VerificationRevisionEntry` deliberately does not
    widen; a per-revision outcome without a revision raises nobody's
    confidence, so null-SHA outcomes never reach `repositories[].revisions[]`
    and every `VerificationStates` consumer is provably untouched.

    **The clearing rule follows what re-reads the artifact.** §5.2's rule is
    that an entry is cleared only by a re-read, and its mechanism — match the
    entry's revision key against the retained and covered sets — implements
    that rule for entries that *have* a revision key. A null-SHA entry matches
    nothing, so the mechanism would drop it on the next narrow run: a
    `--revision` that never opened `current.json` would appear to have fixed
    it. The rule that preserves §5.2's meaning is keyed to the check itself:
    the current-reference check runs only through `resolve_repository`, which
    only `--full` reaches, so narrow runs carry the entry forward, a `--full`
    clears or re-establishes it (`first_seen_at` preserved), and it leaves
    with its repository. The code comment on `_still_outstanding` names the
    assumption that must be revisited if a narrower mode ever grows the check.

    **No `schema_version` bump, and the consequence is documented rather than
    engineered away.** The precedent is `containers_removed` (`RET-008`,
    `REL-001`): a field-level change an older release *refuses* cleanly needs
    a rollback constraint, not a version fence. An 0.1.2 binary meeting a
    null-SHA catalog fails field validation, which `read_verification_catalog`
    turns into `None` — every revision reads `unverified`, confidence lowered
    and never raised, exactly the direction `FS-16` requires derived state to
    err in. The verification *report* is write-only, so nothing older parses
    it back. What is genuinely lost on rollback is the degraded signal itself:
    0.1.2's `status` reports `unverified`, not `degraded`, over the same
    archive. Hence the release-note constraint `REL-004` records: roll back to
    0.1.2 only with no null-SHA finding outstanding, clearing it via a clean
    `--full` first.

79. **0.1.3 is tagged because it is deployed, and it is still not 1.0.0**
    (2026-07-27, `REL-004`). The version question decision 75 settled for the
    first release settles the same way for the second, and stating why briefly
    is cheaper than re-deriving it later. 0.1.3 is the tree that passed the
    gates with `--with-build`, was staged, validated, switched, and ran a clean
    sync through the unit; the tag, the running code, and this file's evidence
    all name one thing. A patch-level bump is right for the content: one
    field-level durable widening with no `schema_version` change, one permit
    removal that no real journal ever exercised, and a test-tree rename.

    The release exists for `VER-009` and is deliberately small around it. The
    ordering the closeout plan fixed — everything non-durable first — is what
    made the cross-format drill about one change alone: when 0.1.2 and 0.1.3
    read the same catalog differently, the only candidate explanation is the
    widening, not a pile of coincident changes. The drill showed the loss is
    exactly the one decision 78 predicted (the degraded signal, silently) and
    no other; the constraint is documented beside the prune-in-flight rule so
    every rollback rule lives on one page.

    Not `1.0.0`, for decision 75's unchanged reason: §33's definition of done
    still includes the consumer export, snapshots and replication, the
    disjointness proof from a second client, reboot persistence, and the
    quarterly verification timer — all operator items, all still open in the
    handoff. Gap 4 of the closeout (the production repository list) is likewise
    operator input; nothing writer-side blocks on it. The archive's health
    headline is the thing this release hardened, and it would be a poor joke to
    version-inflate the release that made a lost health signal loud.

80. **A `DOC` package family, tracked outside §28's phase set** (2026-07-28,
    DOC-001). Plan §28's phases end at Phase 8 and Phase 8 ended with
    `REL-004`; the repository then gained a public remote (`github`, primary)
    and a lab mirror (`forgejo`), which the plan never modelled — §36.2 says
    "no remote is configured; do not push", and §7's layout has no
    agent-context files. The preparation work is real work and this tracker is
    the record of work, so it is tracked the same way as everything else: a
    `DOC` family under its own section, one package per commit, a decision for
    each deviation as it lands. The alternative — doing it untracked because
    the phases are over — would make this file's claim to be authoritative
    quietly false at the exact moment the repository becomes visible.

81. **`AGENTS.md`, `CLAUDE.md`, and `docs/agents/` added beyond plan §7's
    layout** (2026-07-28, DOC-002). Four shapes were settled together. **A
    router, not a manual:** the three load-bearing documents (`docs/agents/history/plan.md`,
    `docs/agents/progress.md`, `docs/architecture.md`) total about 410 KB — an entry
    file that embedded or force-loaded them would spend an agent's context
    before the task started, so the router maps task to document and stops.
    **Backticked paths, not `@`-imports:** Claude Code inlines `@path`
    references from `CLAUDE.md` eagerly at session start, which is the exact
    opposite of the progressive loading the router exists for; a code-span
    path is inert there and reads identically in every other tool. **A
    symlink, not a copy:** `CLAUDE.md` and `AGENTS.md` are one file so the two
    entry conventions cannot drift; divergence becomes impossible rather than
    reviewed-for. **`docs/agents/`, not the contract set:** workflow,
    conventions, environment, and release are about how the repository is
    worked on; the `docs/` root set is normative for the application, and
    mixing the two would blur which documents bind the implementation.

82. **`docs/agents/workflow.md` supersedes plan §36 for sessions after the
    build-out; pushing joins the loop** (2026-07-28, DOC-002). §36 was written
    for one long autonomous run: startup meant reading the plan in full, no
    remote existed, and "do not push" was correct. All three are wrong for
    maintenance sessions on a public repository. `workflow.md` starts from the
    tracker tail and `AGENTS.md`'s map; `github`
    (`git@github.com:wtcross/hfcache.git`) is the primary public repository
    and `forgejo` (`ssh://git@git.lab.example.com:2222/<user>/hfcache.git`)
    the lab mirror, pushed with `--follow-tags` at package boundaries and
    never force-pushed — the history is the audit trail this tracker cites.
    What does **not** change: §36.4–§36.5's hard limits, which continue in
    `docs/agents/environment.md` and bind any session on the writer, and the
    tracker discipline itself. §36 keeps a dated amendment and remains the
    build-out's record.

83. **`CHANGELOG.md` beside the annotated tags, and README `Status` stops
    accreting release notes** (2026-07-28, DOC-003). The release record was
    annotated tags plus a README paragraph that grew a release's worth of
    detail each tag plus the `REL` entries here — all true, none browsable
    from a repository listing, which starts to matter the moment the
    repository has one. `CHANGELOG.md` states in its preamble that the tags
    carry the complete notes and it is the summary, so there is one authority
    and one convenience rather than two authorities that can drift. README
    `Status` keeps the current version and state and points at the changelog
    and the operator handoff. The 0.1.0/0.1.1 non-releases are explained in
    the preamble because a public reader who meets four version directories
    in the deployment doc deserves the explanation the `v0.1.2` tag already
    gives.

84. **Placeholders replace environment specifics, records included**
    (2026-07-28, DOC-005). The repository is public; the deployment's
    hostnames, addresses, and provisioned identifiers are the environment's
    business, not the repository's. Two rules shaped the scrub. **Same-shape
    placeholders**, so every document keeps its meaning: RFC 2606 names under
    the same labels (`hfcachewriter.lab.example.com`, `nas.lab.example.com`),
    RFC 5737's `192.0.2.0/24` with last octets preserved — the writer stays
    `.90` everywhere, so the export allow-list narrative still reads — and
    the all-zeros UUID `examples/config.toml` already established as
    "replace me". **Records are scrubbed too**: plan §35's environment
    inventory, the handoff items, and decision 82's quoted URL are historical
    records, but what they record — that a value was confirmed, provisioned
    once, excluded from an allow list — survives substitution intact, and a
    public record is exactly where the real values must not sit. What
    deliberately stays: the `wtcross` GitHub identity, author email, and
    license copyright (published on purpose), the `tank/huggingface-archive`
    dataset path (TrueNAS's default pool name, generic), and hash or random
    log samples (a config fingerprint, run ids) that identify nothing. The
    real values now live only where they operate: `/etc/hfcache/config.toml`,
    the sentinel, the NAS, and local git remote configuration. Git history
    before `DOC-005` still carries the originals; removing those is a history
    rewrite with new object ids throughout, which this decision does not
    perform and which, if wanted, is its own recorded step.

85. **The storage contract becomes server-agnostic, and evaluation gets a
    first run** (2026-07-28, DOC-006). The NAS half of the system existed
    only as plan §20's TrueNAS 25.10.5 steps plus the deliberately unwritten
    `docs/truenas.md` — right for the lab, nothing for anyone else, and the
    largest finding of the 2026-07-28 portability review. Two documents
    rather than one, because the audiences differ: `storage-requirements.md`
    is a contract a storage administrator reads standalone (any NFSv4.2
    server; TrueNAS "Mapall" stated beside its Linux `all_squash` equivalent;
    the numeric ids explicitly the server's choice), while `quickstart.md` is
    a procedure for someone with a laptop and an hour. The quickstart
    promotes recovery §6's loopback archive rather than inventing a new
    path, because §6 was exercised at `REL-004` and an exercised recipe
    beats an invented one; the checkout adaptation states its deltas (own
    identity, hand-made `/run/hfcache`, reduced free-space reserve) and
    redirects deployed hosts back to §6. The alternative rejected: relaxing
    `FS-02` to allow a local archive root for evaluation. The mount check is
    load-bearing — a missing mount must fail rather than silently land on
    the VM's root filesystem — and a loopback export meets the requirement
    honestly on one machine, so the requirement stands.

86. **Guest memory is bounded in the units, not trusted to the host**
    (2026-07-29, SYS-003). At 02:03:55 on 2026-07-29 the hypervisor
    OOM-killed the writer VM mid-way through the 1.5 TB
    `moonshotai/Kimi-K3` download. The guest-side evidence: the previous
    boot's journal ends abruptly in routine activity with no shutdown
    sequence and no wtmp shutdown record; every XFS filesystem replayed its
    log on the next boot; kdump was armed yet left no vmcore, ruling out a
    guest panic; no OOM or shutdown command inside the guest. The mechanism:
    `snapshot_download` streams every byte through the page cache, an
    unbounded cache makes the guest touch all of its RAM, and a guest page
    once touched is host memory committed for good — the balloon device
    negotiates only `STATS_VQ`, so nothing ever returns. The morning
    catch-up sync confirmed it directly: 18.3 GiB peak on a 23 GiB guest in
    26 minutes. **Decided:** `MemoryHigh=4G` on both service units plus
    absolute dirty-page sysctls (`packaging/sysctl.d/hfcache.conf`), so a
    run's footprint is a fixed working set regardless of repository size —
    validated live at ~4.0 GiB steady while streaming a 209 GB repository.
    **Rejected:** `MemoryMax=`, because it kills at the limit and would
    trade the host's OOM for one of our own — above `high` the kernel
    throttles and reclaims, and a slow sync beats a dead one; per-file cache
    hints (`posix_fadvise`) in the application, because the write path
    belongs to `huggingface_hub`/`hf_xet`, not to this code, and a cgroup
    bound covers both it and the xet chunk cache without a dependency on
    library internals; and fixing it host-side only, because the units
    should be safe guests on any hypervisor, not just a correctly configured
    one. The host retains its half — returning reclaimed pages or not
    overcommitting — as handoff item 12. This adds a resource control and
    weakens no §22.5 hardening; `check-hardening.sh` passed 23/23 on both
    units after the change.

87. **A Cockpit plugin in `cockpit/`, contracted by `docs/cockpit.md`,
    tracked as the `CPT` family** (2026-07-30, CPT-001). The operator wants
    browser administration of the deployed writer — sync control and live
    activity, verification, archive browsing, configuration and schedule
    editing — and Cockpit already serves this host. Decided: a Cockpit
    package in this repository under `cockpit/`, a client of the contracts
    that exist (the CLI's JSON envelope, the configuration schema, and the
    shipped units are its whole API), with a normative contract of its own
    and requirement IDs (`CP-01`–`CP-14`) the implementation and tests can
    cite; the family is tracked outside plan §28's phase set exactly as
    decision 80 did for `DOC`. **Rejected: a separate repository.** The UI
    encodes runbook semantics — the `hfcache.target` unmount footgun, the
    verify-timer reservation, the §8 warning responses — and an encoding
    that cannot change in the same commit as the contract it encodes will
    drift; that is the same argument that keeps docs and code in one tree.
    **Rejected: a plain no-build package** in the style of Cockpit's pinger
    example — no toolchain, but hand-rolled tables and dialogs instead of
    PatternFly's, visual drift from the rest of Cockpit, and none of the
    starter kit's lint and test scaffolding; the toolchain cost is paid
    once, at build time only.

88. **The starter kit runs under pnpm; node is a build-time toolchain, not a
    dependency** (2026-07-30, CPT-001). The operator provisioned node LTS
    (v24) and pnpm 11 under `PNPM_HOME` (`~/.local/share/pnpm`), and pnpm
    replaces the starter kit's npm throughout: one committed
    `pnpm-lock.yaml`, frozen installs, the node version pinned in-repo at
    scaffold time so builds reproduce. `FW-03`/`FW-04` are untouched — the
    plugin ships static files, the application's runtime set stays three
    packages, and nothing node produces runs outside the browser. The gate
    grows a conditional plugin stage (frozen install, lint, production
    build) that skips loudly when the toolchain is absent, because
    `scripts/check.sh` must keep meaning the same thing on hosts without
    node; the discipline that closes the skip's hole is that a `CPT`
    package lands only from a host where the plugin stage ran, recorded in
    its tracker evidence. **Rejected: distribution nodejs via dnf** —
    root-owned and centrally updated, but the pnpm-managed toolchain was
    already provisioned, and a second node on the host is a version-skew
    source with no compensating benefit.

89. **The operation surface bends to the CLI, not the reverse** (2026-07-30,
    CPT-001). Three shapes settled with the operator. **No publish action:**
    `docs/cli.md` §2 has no publish command — publication is an atomic
    stage inside `sync`, and `repair` is the only republish — so the UI
    says "Sync now" and renders published state from `list --revisions`,
    rather than the CLI growing a command to match a button. **Selector
    sync as a page-spawned process, in version 1:** a spawn dies with the
    browser tab, accepted for selector-restricted runs because interruption
    is a crash shape the application is designed for (`AD-09`,
    per-repository transactions, `docs/operations.md` §9) and the UI
    surfaces `recover --dry-run` afterward; the alternative — a templated
    `hfcache-sync@.service` carrying selectors under the full §22.5
    hardening — is recorded as the follow-up seam rather than built now,
    packaging surface ahead of demonstrated need. Full sync and full
    verification stay behind the shipped units unconditionally (`CP-04`):
    the units carry the sandbox, `MemoryHigh=`, and the journal identity,
    and Cockpit's own guidance is not to run long uninterruptible work from
    a page. **Excluded outright** (`CP-05`–`CP-08`): touching
    `hfcache.target`, enabling `hfcache-verify.timer` (handoff item 8 owns
    that calendar), `archive init` in any form, and any credential surface.

90. **`cockpit/` carries LGPL-2.1-or-later beside the repository's MIT**
    (2026-07-30, CPT-002). The plugin tree is a derivative of
    cockpit-project/starter-kit @ `a099cb10` and consumes cockpit's `pkg/lib`
    (fetched at build time, never committed), both LGPL-2.1-or-later. The
    derived and adapted files keep that license with per-file SPDX headers,
    and original plugin code added under `cockpit/` uses the same license so
    the subtree has one answer rather than a file-by-file puzzle. The
    top-level MIT `LICENSE` is unchanged and continues to cover everything
    outside `cockpit/`. The alternative — relicensing the derived scaffolding
    under MIT — is not this project's call to make.

91. **`smol-toml` is bundled for configuration round-tripping** (2026-07-30,
    CPT-008). Form mode must parse the installed document to populate its
    controls and serialize a candidate, and TOML is the configuration
    contract's format. `smol-toml` (MIT, TOML 1.0, parse and stringify, no
    dependencies of its own) is added as a browser-bundled dependency —
    build-time resolved, shipped inside `dist/`, nothing in the
    application's runtime set (`FW-03` untouched, `CP-14`). **Rejected:
    hand-rolling a parser** — a second TOML implementation in this
    repository would be a validation-drift source against the `tomllib` the
    application reads with, for no saving. **Rejected: a JSON side-channel**
    (teaching the CLI to emit or accept configuration as JSON for the
    plugin's convenience) — a new CLI surface grown to match a UI inverts
    decision 89's direction. Comment loss in form mode is stated in the
    generated header and in the UI; text mode exists precisely so an
    operator who keeps comments can.

92. **Plugin CLI invocations run in transient units that import the
    deployment's encrypted Hub credential** (2026-07-30, CPT-013). The
    `runuser` shape ran every plugin-spawned command anonymously, because
    the credential exists only inside units systemd loads it into — 
    invisible while `hub.expected_account` was empty, and an honest
    `HFHUB003` refusal ("the Hub reports this run as 'anonymous'") on every
    plugin doctor and mutating preflight the moment the operator set it.
    The one invocation shape becomes `systemd-run --quiet --wait --pipe
    --collect` with `User=`/`Group=` the service identity,
    `ImportCredential=hf-token`, and `UMask=`/`MemoryHigh=`/`Environment=`
    parity with `hfcache-sync.service` (the memory bound is decision 86's
    protection extended to page-spawned selector syncs). The credential
    moves to systemd's system credential store,
    `/etc/credstore.encrypted/hf-token` — where `ImportCredential=`
    searches — and the sync service's drop-in becomes the same one-line
    import: one credential, one location, every consumer. Import of an
    absent credential is silently skipped, which is `token_mode =
    "optional"` restated at the unit layer, so credential-less deployments
    keep a working, anonymous plugin. The ciphertext is bound to the host
    and the credential *name*, not to one unit — the old example text
    claiming unit binding was wrong and is corrected; name binding is
    exactly what lets the scheduled sync and the plugin's transient units
    share it. Lifetime semantics change deliberately: a transient unit
    outlives its page-side waiter (verified: unit stayed `active` after the
    waiter was killed), so closing a tab now detaches the view and loses
    the envelope rather than killing the run — contract §5, the UI copy,
    and `docs/cockpit-plugin/usage.md` restate it. `CP-08` holds:
    decryption is PID 1's, token bytes never pass through the bridge or
    the page. **Rejected: probing for a credential file and conditionally
    passing `LoadCredentialEncrypted=`** — turns the pure argv builder into
    an async, two-shape surface and hardcodes a path where systemd already
    owns a search order, and a missing explicit source fails the unit
    where an absent import is skipped. **Rejected: keeping `runuser` and
    unsetting `expected_account`** — gives up the swapped- and
    missing-token guard to keep the UI anonymous, inverting the operator's
    stated intent. One host finding recorded with the shape: `systemd-run
    --pipe` with stdout redirected to a user-labelled file hands PID 1 an
    fd SELinux denies (`init_t` write on `user_tmp_t`), which drops PID 1
    off the API bus with a cryptic `Remote peer disconnected` (self-heals,
    or `kill -USR1 1`); the denial is correct, nothing is weakened, the
    plugin always spawns onto pipes, and the operator docs say "pipe, don't
    redirect".

93. **A hardlink carries same-operation content evidence only with exact object
    identity** (2026-08-10, SYNC-006). The ingestion hash now obtains
    `(device, inode, size)` from the descriptor whose bytes it reads and keeps
    that identity only in memory. Publication may avoid rereading a hardlink
    because the link is the same inode, but only after both source and landed
    destination are re-proven against that evidence; any mismatch removes the
    unproven entry and stops before rename. This saves one complete logical-byte
    read — about 25 hours for the observed 10.65 TB repository — without
    weakening `AD-18`. Copy mode is deliberately different: its destination is
    a new inode, so it remains hashed and compared with the ingestion digest.
    **Rejected:** merely deleting the second hash with no identity proof, which
    would make a snapshot-path replacement publish bytes the manifest did not
    describe. **Rejected:** persisting device or inode values, because they are
    transient filesystem evidence and unsafe to reuse across runs.

94. **Queue-ahead uses one repository producer inside the existing run lock**
    (2026-08-10, SYNC-007). Continuation-enabled sync plans the selected queue,
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

95. **A failed report may retain warnings observed before another repository
    failed** (2026-08-10, SYNC-007). Queue-wide planning makes an old reachable
    defect immediate: one repository can complete with a dependency or capacity
    warning and a later repository can fail, but both durable `RunReport` and
    CLI `Envelope` validators previously required warnings if and only if the
    outcome was `success_with_warnings`. The command then failed while trying to
    describe the failure and lost its report. `success` still forbids warnings
    and `success_with_warnings` still requires them; `failed` now permits them
    alongside required errors. The field set and JSON shape do not change, so
    schema version 1 remains; this is a field-combination widening like decision
    78 and receives the same cross-version release drill. A pre-0.1.4 binary
    cannot parse a mixed failed-plus-warning report, so rollback requires the
    newest report to have a previously accepted combination or a later
    compatible sync report to supersede it.

96. **Whole-repository deletion is explicit, unmanaged-only, and reuses the
    prune commit point** (2026-08-15, PUR-001). Removing configuration or losing
    upstream still preserves every local revision (`AD-06`); permanent removal
    requires a separate `purge` invocation with an explicit selector set or
    `--all-unmanaged`, and `--apply` revalidates that scope under the writer lock.
    One transaction owns one complete repository so a broad purge has honest
    per-repository failure boundaries. Its `PurgePlan` names every active
    publication; whole `refs/`, `revisions/`, and manifest directories move to
    transaction trash, and an unknown entry refuses the repository instead of
    broadening deletion. Reusing `operation = "prune"` and
    `prune_logically_committed` keeps the established recovery rule: before the
    boundary restore everything, after it never surprise consumers by
    republishing and finish only audit/physical cleanup. A purge-only
    `repository_container_removed` checkpoint is accepted at exactly its one
    valid position; stripping it leaves the older prune sequence intact, so a
    completed journal is safely ignored by older binaries. `PurgePlan` and the
    `operator_requested_repository_purge` audit reason are durable-format
    widenings: a previous release must never be used while a purge journal is
    open, and release packaging must drill the previous reader against the new
    completed artifacts before deployment. **Rejected:** deleting immediately
    on a configuration edit, which turns mistakes into data loss; manual
    filesystem removal, which bypasses `FS-14`, `FS-19`, audit, and recovery;
    repeated one-revision prune, which exposes partially retained repositories;
    and a new journal operation literal, which adds a second recovery regime
    without changing the commit semantics.

97. **A completed 0.1.5 purge is operationally readable by 0.1.4; an open one
    is the rollback barrier** (2026-08-15, REL-006). The cross-format drill wrote
    the new `PurgePlan` and purge-reason record through the real 0.1.5 CLI on an
    isolated NFS archive. Installed 0.1.4 ignored the resolved journal exactly
    as intended: `status` and `recover --dry-run` were clean, and a real
    re-add/sync preserved generation 1 using the archived manifest. Its direct
    `PrunedRevisionRecord` parser rejected
    `operator_requested_repository_purge`, but no normal completed-purge read
    path needs that record. Therefore rollback requires no open purge journal;
    completed purge state is otherwise command-compatible, while direct audit
    tooling stays on 0.1.5. **Rejected:** declaring every completed purge a
    rollback blocker, because the old commands demonstrably consume the state;
    and weakening the record reason to an older value, because that would make
    the audit lie about why the complete repository disappeared.

98. **Restricted Hub scope requires explicit `required` token policy and one
    shared consumer authorization boundary** (2026-08-23, HUB-010). Setting
    `hub.token_mode = "required"` both requires a credential and authorizes
    private or gated repository metadata; `disabled` and `optional` remain
    public-only so ambient optional credentials cannot silently broaden archive
    scope. All configured consumers must be authorized for every archived
    repository because the exported tree has no per-repository ACL layer.
    Credential or gate revocation stops future fetches but does not delete
    already published revisions; removal from configuration followed by an
    explicit purge remains the deletion path. This widens configuration
    acceptance without changing a durable JSON format. Rolling back to a
    pre-HUB-010 binary requires stopping sync and temporarily returning the
    configuration to `optional`, without syncing restricted repositories on
    that release. AD-21 retires the original NG-06 public-only boundary.
    **Rejected:** letting an optional token automatically broaden repository
    scope, because ambient credential availability would change policy;
    per-repository credentials or ACLs, because the deployment has one trusted
    internal consumer boundary; automatic deletion on revocation, because it
    would violate the archive's explicit-deletion rule.

99. **Consumer revision creation and serving promotion have separate ownership boundaries** (2026-08-24, OPS-009). The locked `vllm` identity owns only `<model>/revisions/`, where every `copy-revision.py` invocation receives a new non-existent destination; root owns the model root and therefore the eventual `current` pointer changed only after manifest verification. This makes targeting a live serving path unavailable to the copy identity, which matters because the reference helper deliberately removes an existing destination before promotion. The 100 GiB figure is an existing-model-plus-available capacity check, not a claimed filesystem reservation: deployments needing isolation use a dedicated filesystem or quota. **Rejected:** making the whole model root writable by `vllm`, because a serving process could replace its own promotion pointer; preallocating a 100 GiB reserve file, because it consumes the capacity intended for model copies and requires a second unsafe shrink/replenish protocol.

100. **Serving consumes the verified ordinary-file tree through read-only container mounts** (2026-08-24, OPS-010). The image, model directory, and YAML configuration are explicit inputs because vLLM, CUDA, and model-specific settings belong to the consumer deployment rather than the archive contract. The launcher resolves both host paths, mounts the model and config privately SELinux-labelled and read-only, and supplies the mounted model path positionally to an explicit `vllm serve`; it does not repeat manifest verification already completed by the copy helper. Podman is preferred on this CentOS-family deployment, with Docker selectable for consumer portability, and the wrapper stays foreground so signals and the serving exit status retain their ordinary meanings. **Rejected:** installing or pinning vLLM on the host, which would add deployment-specific runtime dependencies to hfcache; disabling SELinux labelling for bind-mount access, which would weaken the host boundary; and silently taking a model identifier from YAML, which could serve something other than the verified directory the operator named.

101. **Repository names are canonical, type-aware external links** (2026-08-30,
    CPT-014). A model name links to `https://huggingface.co/<owner>/<name>` and
    a dataset name to `https://huggingface.co/datasets/<owner>/<name>`; encoding
    each identifier segment keeps the generated path structural. The page opens
    the destination in a new tab with `noopener noreferrer`, preserving the
    Cockpit view and carrying neither an opener relationship, a referrer, nor a
    Hub credential (`CP-08`). **Rejected:** linking the current commit instead,
    because the parent row represents the repository and its expansion already
    presents every retained revision; making one revision the navigation target
    would misstate that scope.

102. **Retention defaults to three while explicit five remains compatible**
    (2026-09-14, RET-010). The operator requested a smaller default and immediate
    cleanup of older revisions in configured models. Schema version 1 now
    accepts exactly `3` or `5` for `storage.maximum_revisions`, defaulting to
    `3`; the key is not renamed. Existing explicit-five configurations retain
    their policy, and adopting three is an explicit configuration migration on
    this writer. This deliberately widens configuration acceptance without
    changing durable JSON shapes or checkpoint semantics. The historical
    `sixth_unique_revision_published` audit reason remains the schema-1 name for
    exceeding the configured retention limit. Before rolling back to an older
    binary, restore an explicit value of `5`; deleted revisions are not restored
    by that policy rollback. Latest means immutable publication generation, and
    the current revision remains protected. Cleanup uses reviewed, explicitly
    selected model prune rounds because each invocation removes at most one
    revision per repository. **Rejected:** allowing arbitrary retention counts,
    which broadens policy beyond the request; rejecting existing explicit-five
    configurations, which needlessly breaks upgrades; and manually removing
    archive files, which bypasses the cache ownership, audit, and recovery
    contracts.

103. **Only resolved, proven redundant staging quarantine may be released**
    (2026-09-14, QUA-001). The operator requested immediate cleanup of the
    Overview's quarantine findings. The application now gains an explicit-ID,
    dry-run/apply cleanup path; manual archive deletion remains prohibited.
    A completed failed publication and its committed recovery checkpoint must
    jointly prove each target's provenance. Empty directories carry no content;
    remaining files must match the current retained manifest and freshly read
    current file bytes before they can be discarded. The complete batch is
    validated first, apply holds the writer lock, unresolved journals refuse
    cleanup, symlinks and unexplained entries are preserved, and each deletion
    rechecks its evidence. Original journals and published content remain intact.
    This is a narrow `TX-01` exception: no second cleanup journal is needed for
    monotonic removal of already resolved redundant data, since a crash leaves
    a subset that the same command can prove again. No durable JSON shape or
    checkpoint vocabulary changes. **Rejected:** blanket recursive deletion,
    which can erase unique or unresolved evidence; an automatic age-based purge,
    which treats age as deletion authority; and a new checkpoint format for
    these redundant artifacts, which would introduce recovery and rollback
    obligations without preserving additional content. Repair quarantine and
    unvalidatable publication trees remain outside this command's scope.

104. **Confirmed operator cancellation may replace the empty-staging age heuristic**
    (2026-09-14, QUA-002). The operator explicitly chose to pause the active
    sync, clean quarantine, and restart with its download cache preserved.
    Ordinary recovery would wait 24 hours even though that exact writer was
    deliberately stopped. For the identified run only, service/PID termination,
    the exclusive writer lock, exact journal/run/repository/commit evidence,
    and an empty `staging_created`-only publication permit the installed
    recovery planner's explicit zero-hour threshold. Reject other unfinished
    work, review the plan, recompute it under the standard preflight/lock, and
    apply through the existing journaled recovery code. No configuration or
    timestamps are changed; automatic recovery retains its age policy. The
    cache and published references remain intact. Recovery creates an ordinary
    empty quarantine entry that the explicit cleanup command can remove.
    Valid early download journals have a null publication ID, so cleanup must
    accept that existing shape when terminal recovery proves ownership.
    **Rejected:** killing the writer and deleting staging by hand; inventing
    timestamps or journal identities to satisfy a guard; globally shortening
    the age policy; and broadening the exception to populated or later-stage
    interrupted publications. No durable format changes are introduced.

105. **Only journals supplying deletion authority need current checkpoint order**
    (2026-09-14, QUA-003). The live cleanup preview correctly stopped before
    deletion but rejected two unrelated, completed historical prune journals.
    Parsing and resolution checks still apply to every inventory record;
    unsupported fields, unreadable records, and unfinished transactions still
    refuse cleanup. Full checkpoint-order checks apply to the selected source
    publications and their matching committed recovery proofs. Unrelated
    completed history is preserved and cannot grant deletion authority, so its
    older checkpoint sequence must not prevent an independently proven cleanup.
    This follows normal recovery's treatment of already resolved journals and
    changes no durable format or source evidence.

106. **Current invariants and individual ADRs accompany every implementation**
    (2026-10-17, DOC-009). `docs/invariants.md` is the current cross-contract
    register; `docs/adr/README.md` indexes standalone records for every existing
    `AD-nn`, the framework boundary, offline verification, systemd scheduling,
    and every numbered progress decision. Backfill preserves original dates,
    work packages, reasoning, alternatives, and git provenance rather than
    assigning new origins to old choices. Historical records carry explicit
    amendments and supersession links; current contracts and the invariant
    register state the effective policy. Every change or new plan being
    implemented must review affected invariants and ADRs, add new invariants
    and architectural choices, and maintain changed or superseded records in
    the same work package. `AGENTS.md` routes progressively through the
    register navigation and ADR index to only the relevant records, while
    the workflow makes this review part of contract-first implementation and
    commit completion. The append-only progress log remains the work tracker
    and chronological decision source. Backfill also reconciles existing
    journal unknown-key handling (decision 20), deployed hardening (60, 61,
    66), explicit deletion (96, 102), and restricted authorization (98) where
    standing prose lagged implementation; no new runtime policy or format is
    introduced. The audit labels the existing `AD-05` / `FS-20` lifetime-
    generation and audit-union conformance gap and tracks `RET-011` for an
    explicit future contract/code decision rather than silently weakening the
    requirement. **Rejected:** a single growing decision document as the only
    lookup surface, because it hides related reasoning across work packages;
    forcing every session to read the full ADR history, because that defeats
    progressive context loading; replacing existing IDs or rewriting the old
    decision log, because source and tests already cite that audit trail; and
    generating records without source or git evidence, because plausible
    retrospective reasoning is not provenance. See
    [the individual record](adr/decision-106.md).

107. **Active plans and task records own execution; progress retains the audit**
    (2026-10-17, DOC-010). The user requested dated plan records, a current
    active-plan tracker, and individual Markdown task files. They confirmed
    that the new files own active work, implementation authorization permits
    activation without a separate approval step, drafting alone does not
    activate, and setup finishes with no active plan or backlog migration.
    `docs/agents/plans/current.md` selects at most one active plan and points to the
    next task/blockers. Stable `YYYY-MM-DD-plan-<slug>.md` files own plan scope,
    lifecycle, and ordered task links; individual files under `tasks/` use
    existing work-package IDs and own task execution status, dependencies,
    acceptance, and evidence. Completed, cancelled, and superseded records
    remain at their original paths. Small implementation changes use a brief
    plan and single task; read-only and draft-only work needs no activation.
    `docs/agents/progress.md` retains completed work-package audit, Decisions,
    Operator handoff, and unmigrated historical backlog, rather than another
    active queue. This supersedes the progress-only selection and tracker
    authority in decisions 82 and 106 while retaining their commit, safety,
    invariant, and ADR upkeep rules. `docs/agents/planning.md` owns lifecycle
    and templates; `AGENTS.md` loads current, its selected dated plan, and
    the relevant task progressively. `docs/agents/history/plan.md` remains the original
    contract/history reference. `INV-011` records the new workflow constraint.
    **Rejected:** duplicate mutable task status in progress, plan tables, and
    task files, because they can disagree about completion; treating draft
    plans or old unchecked backlog as execution authority, because neither
    establishes the requested scope; mandatory separate activation approval,
    because the user chose implementation authorization as sufficient; and
    deleting or bulk-migrating historical records, because they preserve
    evidence and were not selected for current work. See
    [the individual record](adr/decision-107.md),
    [setup plan](plans/2026-10-17-plan-planning-workflow.md), and
    [DOC-010 task](plans/tasks/doc-010-planning-workflow.md).

108. **Typed services and maintained transports** (2026-10-17, API-001).
     [ADR](../adr/decision-108.md): ordinary query/guarded-command services retain
     domain authority; maintained httpx, FastAPI/Uvicorn, and later standalone
     FastMCP supply protocol correctness through scoped incremental extras.
     Reject CLI subprocess/callback adapters and duplicate domain engines.
     FW-03 is explicitly amended; dependencies land in later packages.
109. **Bounded non-resuming submissions** (2026-10-17, API-001).
     [ADR](../adr/decision-109.md): a bounded FIFO and atomic service-private
     receipts preserve observation across HTTP timeouts without a workflow
     engine. Reject broker/database/resume graphs and journal-driven normal
     execution. No replay or exactly-once claim; archive journals and flock
     remain authoritative. API-007/008 own implementation and crash proof.

110. **Guard complete command execution and verification persistence**
     (2026-10-17, API-003). [ADR](../adr/decision-110.md): all non-estimate
     verification owns the common flock and storage preflight from scope
     resolution through hashing, report write and complete catalog merge.
     Baseline full verification released before persistence; narrow modes had
     no common lock. Atomic replacement cannot serialize those merges; a
     spawned-process regression proves the protected interleaving, without
     asserting production corruption. Reject per-mode/process-only locks and
     persistence-only ownership. Typed command services own one acquisition;
     adapters and future runners do not nest locks. Doctor probes and confirmed
     initialization serialize with their own checks; read-only diagnostics,
     inspection, estimates and previews remain unlocked. AD-17, offline
     verification, INV-007/015 and historical doctor decision 40 are amended;
     existing FS/TX, quarantine and joined-transfer semantics stay authoritative.

111. **Scope execution correlation and offline process initialization**
     (2026-10-17, API-004). [ADR](../adr/decision-111.md): retain the closed event
     interface with immutable context-scoped run/request/operation correlation,
     captured at emission and deliberately copied into each worker, including
     the sync producer. Restore prior scope after success/failure; configure a
     daemon's handler/level once, with client verbosity confined to rendering
     and event selection. Reject process-global IDs, formatting-time provenance
     and per-request logger/environment reconfiguration. Shared verification
     constructs no Hub client/credential and never writes `os.environ`;
     dedicated-process offline initialization is startup-only and independently
     needs the future API-008/014 no-IP sandbox. Register exact opaque secrets
     before use and sanitize nested diagnostics and exception/problem output.
     Domain IDs and schema-1 invocation-mode vocabulary remain; execution-host
     `systemd` is not proof of timer/client origin, so later receipts carry the
     authenticated submitter. Amend decision 64, offline verification,
     decision 110's deferred guard, AD-19 and scheduling provenance; no durable
     schema/dependency, listener, ASGI or MCP implementation is introduced.

112. **Separate server authority and verified bearer capabilities**
     (2026-10-17, API-005). [ADR](../adr/decision-112.md): strict restart-only
     server configuration is independent of freshly frozen archive snapshots;
     startup root/UUID cannot hot-switch. Explicit protected API credentials
     grant fixed whole-archive REST reader/writer or future MCP capability
     principals. Descriptor-pinned bounded reads, distinct values, exact-secret
     registration and fixed-size constant-time comparisons prevent ambiguous
     authority; reject ambient/Hub reuse, anonymous socket exemptions and
     input-echoing diagnostics. Central HFAPI001–004 classify authentication,
     capability, credential and duplicate failures at exit 10. HTTPX is direct
     base; FastAPI/Uvicorn are optional server dependencies, with Python 3.14
     lock, official-source rationale and real isolated base/server wheel smoke
     checks. Reject handwritten protocol/lifecycle implementations and optional
     test skips. Existing versions, FS/TX, durable schemas and AD-21 remain.
     API-006 owns runtime route protection; receipts/execution and MCP remain
     later tasks. No listener or production installation is introduced.

113. **Serve bounded metadata through one authenticated lifespan**
     (2026-10-17, API-006). [ADR](../adr/decision-113.md): one injectable metadata
     app and explicit foreground bootstrap share Unix/TCP, a daemon lock and a
     bounded context-propagating pool. Authenticate all HTTP surfaces before
     routing/body/error processing, and bound typed wire resources/streams.
     Shared no-follow readers cover legacy local paths too; invalid derived
     evidence stays unknown without repair. Content-bound cursors refuse stale
     continuation; exact publication locators retain their declared bases.
     Configuration UUID metadata is not proof of a sentinel check on every
     read. Reject unbounded event-loop scans, per-socket apps, path-only evidence
     trust and raw error/input echoes. HFAPI005/008/009/011 override the family
     default to safety exit 20; auth/config/request cases retain 10. `serve` is
     the narrow no-success-Envelope bootstrap exception, preserving typed JSON
     startup failures. Disable raw framework logs/slash redirects; test the
     locked Uvicorn TLS/Unix lifecycle on disposable sockets. No job/write,
     verifier fallback, MCP, durable schema or production deployment is added.

114. **Persist non-resuming admission without discarding uncertainty**
     (2026-10-17, API-007). [ADR](../adr/decision-114.md): independently versioned
     local JSON receipts are the authoritative principal/key/request binding,
     persisted before runnability or acknowledgement. Fixed credential-class
     principals survive rotation; raw keys and request bodies are never stored.
     REST readers share whole-archive operation observation, while key lookup
     stays within the caller's namespace. Preserve unsupported, malformed,
     interrupted, ambiguous and nonterminal evidence; refuse count/space
     admission instead of evicting unexpired 30-day bindings. Startup never
     replays old work or reconstructs submissions from journals; interruption
     classification is explicit pending API-008 worker reconciliation. Reject separate
     authoritative key indexes, FIFO history eviction and broker/database/resume
     engines. This implements decision 109's narrow FW-01 exception and retains
     FW-02/AD-12/14/16; heavy execution and command submission remain later tasks.

115. **Execute one bounded lane and reconcile the exact verifier**
     (2026-10-17, API-008). [ADR](../adr/decision-115.md): one FIFO lane shares an
     absolute queue/lock deadline and passes policy/deadline hooks into the
     service-owned flock. Revalidate the admitted fingerprint under lock before
     mutation; keep sync producers joined inside ownership. Delegate verification
     only through a bounded peer-checked private protocol, retaining exact durable
     operation outcomes. Reconcile the exact surviving verifier before marking
     unresolved history interrupted; never replay receipts/journals or infer
     completion from PID, lock release or client loss. Reject reset timeouts,
     nested flocks, generic execution and in-process verification fallback.
     API-014 still owns actual credential-free/no-IP systemd hardening; a startup
     offline flag alone is not egress enforcement. No dependency or MCP is added.
     Unreachable/unsafe worker status preserves active receipts and disables
     execution across restarts; only trusted missing/interrupted evidence allows
     parent interruption. Reject immediate interruption on transport loss because
     a later restart would otherwise reopen the lane while a worker may survive.

116. **Admit typed command routes without widening server authority**
     (2026-10-17, API-009). [ADR](../adr/decision-116.md): explicit bounded strict
     JSON routes call shared services through durable keyed admission; 202 is
     admission only and exact terminal Envelopes retain domain exits. Authorize
     writer sync/verification/probes, reader installed planning and explicit
     read-only diagnostics; semantic reads still have Hub/resource/control-state
     effects. Normalize selector sets without changing configured sync order.
     Trust only startup/installed Hub credential sources; candidate hooks compare
     the complete installed authority without resolving secrets, network or
     paths. Reject generic commands, arbitrary server files/endpoints, request
     token overrides and implicit probe modes. Candidate HTTP/CLI pipeline stays
     API-012; maintenance, client and installed-worker hardening remain later.
     No archive/receipt format, dependency, MCP or production change is added.

117. **Revalidate explicit maintenance authority at execution**
     (2026-10-17, API-010). [ADR](../adr/decision-117.md): separate typed preview/
     apply URLs preserve explicit scope; every job requires durable idempotency,
     every side effect requires a writer, and previews confer no apply authority.
     Fresh locked policy/scope/guard/evidence validation preserves one-round prune,
     unmanaged-only purge, quarantine batch proof, exact-manifest repair and
     pre/post-commit recovery without widening deletion authority. Unknown evidence
     remains preserved. The disabled-by-default maintenance switch gates only
     explicitly confirmed initialization of the restated configured root/UUID;
     never initialize from startup, health, recovery or a missing sentinel.
     Reject generic execution, posted plans, mode defaults, unknown-data cleanup
     and silent replay. No durable schema/dependency/MCP or production change.

118. **Observe one API authority without replaying uncertain submissions**
     (2026-10-17, API-011). [ADR](../adr/decision-118.md): a separate strict schema-1
     client config selects one URL/socket authority and only an explicit API
     credential. CLI endpoint options override the configured endpoint as a group;
     no ambient proxy/Hub-token discovery, redirect credential forwarding, local
     archive fallback or automatic daemon startup. A synchronous base client
     validates versions, identities, Envelopes, pages and exact operation results
     under finite body/page/timeout/retry/poll budgets. Preserve an operation's
     admitted fingerprint and distinct request/operation/domain identities.
     Generate/retain one key before submission; lost acknowledgement or observation
     preserves uncertainty and never generates a new-key replay. HFAPI017/018
     classify config/protocol at exit 10; HFAPI019/020 classify connectivity/
     uncertain submission at exit 20. Unusable post-transmission acknowledgements,
     including malformed/wrong-identity 202 or untrusted error bodies, preserve the
     original key/route as uncertainty; validated problems retain their taxonomy
     and key/route too, because even a valid 500 can follow durable admission.
     CLI runtime migration remains API-012/013;
     no durable archive shape, runtime dependency, MCP or production change.

119. **Preserve server read identity and separate candidate validity from authority**
     (2026-10-18, API-012). [ADR](../adr/decision-119.md): CLI metadata/read-only jobs
     use the independent typed client without local archive fallback, retaining
     exact server Envelopes, times, domain IDs, errors and complete paged data.
     Inspection uses the configured server target; an optional root restatement
     checks the returned root and does not select it. Local help/version and
     explicit config validation --local remain bootstrap exceptions. Other API
     reads reject archive-config and Hub-token overrides. Candidate TOML is bounded
     local content, never a server file path; syntax-valid incompatible proposals
     remain valid with compatibility=false and mismatch names, without credentials.
     Candidate planning requires all six authority fields to match before installed
     credential use, while previewing candidate repository/policy intent. Retain
     installed admitted fingerprint and preserve old installed-plan key digests
     when candidate is absent. Installation/backups stay privileged host work.
     Promote already-locked HTTPCore 1.0.9 to a direct base dependency for a public
     Unix-only adapter that owns failed sockets and response cleanup, retaining
     maintained HTTP framing/pooling and TCP/TLS through HTTPX. No private pool
     mutation, global patch, IP fallback or warning suppression; the observed
     missing-socket leak provides material FW-04 correctness rationale. No new
     package/version, durable shape, MCP or production change.

120. **Separate command execution from resumable CLI observation**
     (2026-10-18, API-013). [ADR](../adr/decision-120.md): operational CLI modes use
     typed API requests without a local mutation backend. Default output is the
     exact terminal server Envelope; explicit detach is separately identified
     admission, never fabricated command success. Print validated key before POST
     and operation ID before waiting even in quiet mode. One finite observation
     deadline covers sanitized events/status/result reads and retries. Timeout,
     Ctrl-C or connection loss retains handles and states accepted work may
     continue, without cancel/replay. Authenticated show/wait/lookup observe only;
     missing history remains uncertainty. Initialization obtains omitted optional
     UUID from authenticated inspection while retaining user-restated root and
     explicit confirmation; no-confirm inspection/refusal never submits. Server
     maintenance/DTO/lock/recovery/private-verifier authority stays unchanged.
     No durable shape, dependency, MCP or production change.

121. **Activate one server and retain scheduled observation without replay**
     (2026-10-18, API-014). [ADR](../adr/decision-121.md): Unix/optional TCP activation
     shares one application/lifespan; dedicated unprivileged private verification
     encloses actual work with offline/no-IP/credential-free policy and peer UID
     account resolution, never manager `%U`. Hide credential/source stores, with
     explicit restrictions required for custom development paths. Preserve names,
     calendars, disabled verify timer, OnFailure/target/mount and shared lock
     lifetime. Scheduled AF_UNIX clients use distinct API credentials and strict
     private schema-1 observation handles: fixed sync/verify-full, endpoint, archive
     UUID, REST-writer namespace, key fsync before sole POST and accepted ID.
     Existing/unknown history never authorizes replay; repeated finite windows
     retain the active oneshot until exact terminal Envelope/exit, then safe handle
     removal. Same-class rotation can recover. No bearer/digest/body/queue, new
     dependency, MCP or production operation. Actual socket/cgroup/no-IP/credential/
     SELinux/NFS acceptance stays an explicit deployment hold.

122. **Preserve Cockpit authority through the API client and guarded candidates**
     (2026-10-18, API-015). [ADR](../adr/decision-122.md): transient service-identity
     clients import only named API `hfcache.api`, use fixed local client settings/
     socket and never pass ordinary archive config or Hub/browser bearer authority.
     Strict bounded terminal schema-1 Envelopes govern outcomes; separately
     validated bounded progress/handles may render and reconnect without invented
     checkpoint/percentage/outcome. Closing a page or stopping an observer never
     proves accepted work cancelled or recovery safe. Retain uncertain handles
     and use lookup/wait, without automatic recovery/replay. A persistent root
     config flock guards exact candidate and installed-base bytes through server
     validation/required preview/atomic install; edits invalidate readiness.
     Syntax validity, compatible authority and exact installed fingerprint
     confirmation are distinct gates. Incompatible/unknown authority blocks
     plugin installation with manual operator guidance. Preserve backup/mode,
     root/admin/service separation, installed full-sync/verify units, sync-timer
     only controls and no init UI. No durable JSON/dependency/MCP or production
     change; real host acceptance remains operator work.

123. **Keep public prefixes separate from native Unix REST paths**
     (2026-10-18, API-016). [ADR](../adr/decision-123.md): configured public prefix/
     TLS/proxy/Host/Origin policy remains for TCP; actual supported Uvicorn Unix
     scope alone may use native unprefixed REST. Authenticate and bound both;
     require both missing peer and an absolute Unix-path/None-port local address,
     since peer absence alone can mean a socket error. Apply that predicate to
     prefix/proxy-TLS exceptions; missing/malformed local evidence fails closed.
     headers never manufacture local authority. Derive links/docs prefix per
     request and spelling, without shared mutable prefix or cached-schema changes.
     Public OpenAPI stays deterministic; native `/` view is a response copy.
     Fixed local scheduled/Cockpit clients need no new prefix field or config
     version. Prove the distinction with locked source and actual disposable
     sockets, audit all 29 REST modes/examples/contracts and run fresh build
     acceptance before MCP. No dependency/durable schema or production change;
     real installed-host enforcement remains operator-held.

124. **Add an optional authenticated MCP transport after REST acceptance**
     (2026-10-18, MCP-001). [ADR](../adr/decision-124.md): API-016 committed
     acceptance precedes the standalone FastMCP optional dependency. Supported
     streaming/auth/lifespan implementation provides the material FW-04 benefit;
     base/REST-only installs stay independent. Compose REST-before-MCP startup
     and reverse teardown in one app, with failure cleanup. Production supported
     verifier accepts only shared protected MCP-reader authority; no development
     static verifier, cross-interface credential, ambient discovery or bearer in
     configuration/logs. Disabled MCP imports/resolves neither package nor its
     credential. Every transport request authenticates; session IDs grant no
     authority. Preserve Host/Origin/TLS/proxy/corroborated native-prefix checks
     and resource bounds. Pre-provisioned internal bearer is not OAuth discovery.
     Finite replies are sanitized/bounded before headers; one trusted path
     projection prevents interface confusion when public prefixes collide.
     Closed vocabulary adds stable `mcp.diagnostic` with fixed text, original
     severity and bounded sanitized logger provenance through existing emit/
     correlation, never formatting raw SDK rejected-value messages/exceptions;
     lower levels are suppressed and handlers restore. JSON-RPC errors project
     code/fixed message without raw SDK details. No OpenAPI conversion or
     tools/resources/prompts in this package; curated read-only tools remain MCP-002. No durable shape/workflow/domain authority
     or production deployment change; actual acceptance remains task evidence.

125. **Expose nine typed metadata tools through a narrow read capability**
     (2026-10-18, MCP-002). [ADR](../adr/decision-125.md): register exactly the plan's
     nine metadata names, no resources/prompts or generic dispatch. Adapters get
     only a narrow async read protocol, never SDK app/request context, commands,
     Hub/credentials, writes or arbitrary path/URL authority. App-owned bounded
     offload invokes shared validated readers; annotations describe rather than
     enforce read-only behavior. Strict schema-1 MetadataRead wraps fresh request/
     archive/policy identity plus domain Envelope and optional cursor. Explicit
     manifest/report projections preserve original headers/totals/run identity
     while paging selected collections; never claim a partial durable record is
     complete. Inventory/status cursors bind sanitized selected rows/filter/
     policy; status headline/warnings stay fresh per page so free-space changes
     do not break continuation. Immutable artifact cursors bind all sanitized
     headers/collections; known secret literals cannot enter hash fingerprints.
     Changed bound content/policy refuses rather than silently skipping. Exact SHA/publication reads never fall back to current;
     unknown catalogs stay unknown and estimates never hash/persist confidence.
     No dependency/durable/config change, job authority or later-task work;
     registry/schema, mounted parity and side-effect proof belong to this task.

126. **Guard a local rollout without NAS writes or false acceptance**
     (2026-10-18, OPS-014). [ADR](../adr/decision-126.md): new user authority permits
     reviewed changes, local release/tagging and rootless Caddy/API/worker/client
     rollout on this host only. NAS content/metadata writes and other-host changes
     remain forbidden; no remote push/registry publication or ACME issuance.
     Before rollout, root records local state without secrets/NAS file I/O,
     blocks legacy scheduling/writers, proves actual executor quiescence plus a
     retained noncreating local flock, and enforces a persistent client-side
     read-only mount without unmount/disconnect. Subsequent NAS binds remain
     read-only without chown/relabel/copyup. Keep sync stopped and verify timer
     disabled; preserve unknown receipts/handles/locks and hardening. Required
     live sync/full-verify/NAS probes cannot run under this constraint: local
     disposable and actual host isolation evidence remains explicitly partial,
     with forbidden checks NOT RUN. Local tag↔deployed artifact identity remains,
     with honest remaining holds; it never certifies skipped storage acceptance.
     OPS-015 owns the actual rootless architecture and proof, not this policy.

127. **Run reviewed rootless containers without forced executor cleanup**
     (2026-10-18, OPS-015). [ADR](../adr/decision-127.md): explicit rootless user
     systemd services and a reviewed system-to-user target bridge replace the
     initial Quadlet proposal. Fixed never-pull/no-replace/no-init/no-auto-remove
     persistent-role argv, infinite non-killing drain and stopped-only nonforce
     cleanup preserve unknown executor truth. Finite API-only observers alone may
     auto-remove their own stateless container; this cannot cancel server work or
     discard durable receipts/caller handles. One API, separate Network=none/seccomp IP-denied
     credential-free worker with real FD3/PID1/peer proof, Caddy existing verified
     TLS8443/Unix upstream and container clients keep shared local lock/state,
     read-only hot-reloaded policy directories and secret-class separation.
     No ACME/admin/raw-header logging, rootful/privileged/label-disable/Podman-
     socket shortcut, NAS relabel/chown/copyup or production switch. Exact hashed
     wheel/closure and platform image digests identify the runtime; separate
     protected immutable-manifest installer retains old artifacts/drain guards.
     Cockpit keeps outer privilege/candidate/observation contracts with only a
     fixed inner container-client launcher; no bare-host fallback. Necessary
     root-owned local account/rootless fixture infrastructure is authorized,
     but OPS-015 proofs bind only owned local fixtures, never NAS. Actual source,
     lifecycle/secret/SELinux/container and full gate evidence remain task-owned.
     Exact protected current bindings pin helper/profile/images/config together;
     missing/copied/drifted links refuse and effective managers still need review.
     REL-010 owns reviewed 0.2.0 source, REL-012 clean-source artifacts, and
     OPS-016 production profile enablement under the unchanged NAS-write ban.

128. **Create the rootless verifier listener inside its confinement**
     (2026-10-18, OPS-017). [ADR](../adr/decision-128.md): explicit PID1
     --container-listener audits inherited descriptors/activation/credential
     environment before opening resources, then creates the protected AF_UNIX
     listener under the worker's existing confinement. Native named-FD3 mode
     remains strict, with no fallback. Hold instance/pinned-parent/created-inode
     ownership through joined work and exact cleanup; stale/replaced evidence
     never grants deletion/replay authority. Worker Type=notify/NotifyAccess=all
     and --sdnotify=container report READY only after listener/store/worker init;
     API Requires+After that service. Rootless .socket stays dormant with its
     indexed binding. Reject SELinux allow/label/host-execution and seccomp/secret
     shortcuts. Planned 0.2.1 clean-image/installed proof is later work: existing
     0.2.0 partial evidence and worker hold remain until actual OPS-018 peer
     acceptance. Fixed host guard, NAS-ro/writer masks and no NAS I/O/jobs remain;
     no dependency/durable-format/domain change or remote action is introduced.

129. **Build all service image stages on pinned UBI 10 micro**
     (2026-10-18, OPS-019). [ADR](../adr/decision-129.md): new user steering supersedes
     Debian/Alpine candidates. Every app/Caddy FROM stage uses exact UBI 10 micro;
     actual included tools make a larger tooling stage/package transaction
     unnecessary. Minimal is only the pinned Red Hat CA-PEM donor; external uv/
     Caddy images supply only verified executables via COPY, no foreign OS/CA/
     environment defaults. Exact portable CPython3.14.6/20260718, wheel and locked
     application versions remain; fresh-inode Caddy install strips unnecessary
     file capabilities without weakening NNP. Provenance records all foundation/
     interpreter/binary/CA inputs. Repeat dirty then clean UBI proofs, preserve
     superseded candidate/stopped-gate evidence, and retain listener/SELinux/
     secret/seccomp/lock/drain/NAS constraints. REL-013 waits committed OPS-019;
     deployed0.2.0/hold 22 and all forbidden NAS/remote actions remain unchanged.

130. **Separate human contracts from agent implementation records**
     (2026-10-18, DOC-011). [Agent ADR](adr/decision-130.md) amends process
     decisions 82/106/107 with an explicit one-time stable-path exception.
     Collision-check each move into docs/agents, preserve 47 original records
     with git-baseline SHA-256 provenance, and select work only through the
     migrated current.md. Retain process ADR identities and INV-011 internally;
     rehome still-normative plan requirements in living human contracts before
     archiving history. Reject parallel selectors, deleted evidence and human
     redirect pages into tracking. The per-file transitional match inventory
     must shrink to zero by final acceptance. No technical invariant, runtime
     dependency, durable format or host-operation authorization changes.

131. **Make diagnostic authority explicit and isolation evidence qualified**
     (2026-10-18, OPS-020). [Technical ADR](../adr/decision-131.md) amends
     decisions 59/60: static entrypoints, explicit profile/disposable target/UUID/
     retained local lock, strict no-follow preflight and under-lock revalidation
     precede archive writes. Keep artifacts in an exclusive health child and
     preserve substituted/unknown evidence. Reject production/read-only targets
     and NFS workloads on hosts carrying the production mount, avoiding alias
     assumptions. Remove real kernel-setting and system-directory write probes.
     Permission errno evidence names only the denied action; imports/DNS/timeouts/
     unrelated I/O are not proven. Copy selected policy/read masks without
     production credentials/lifecycle/shared state and report overrides. Require
     complete role/network diagnostic results, reject duplicates/noninteger
     versions, suppress dependency output and project manager output safely.
     INV-017 records these tooling constraints; daemon/archive formats and
     hardening are unchanged. No host/live workload is authorized or performed.

132. **Positively classify native release layouts before effects.** A shared
     standard-library reader validates source/current/target without candidate
     execution; container/mixed/unknown/partial layouts refuse before staging,
     managers, switch or native diagnostics. Static help/list/dry-run and fresh
     native install remain supported. Retain rootless fixed roles, all scripts,
     dormant socket/native FD3, handles/stores and original lock authority.
     [Decision 132](../adr/decision-132.md) records rationale and evidence.


133. **Separate curation from publication authority** (2026-10-19, CAT-001).
     [Decision 133](../adr/decision-133.md) records current configuration tags,
     actual historical snapshots, separate curation identity and exact derived
     technical observations. Reject mutable manifest labels and a parallel tagging
     database. Approved optional metadata records/directories alone have independent
     atomic-file boundaries under lock/preflight/TX-07 guards; no existing archive
     transaction or registered read capability changes. Human discovery/schema/
     architecture contracts and INV-018 establish proposed behavior before code.

## Documentation and script alignment

- [x] API-018 Align CLI diagnostics and remove migration remnants (2026-10-18,
  this commit). Current command/option help separates local, REST, writer and
  private-worker effects. Quiet/JSON retain warnings/errors, degraded/gap notices
  and safety handles; exact Envelopes/exits remain. Per-invocation no-color covers
  eager help and output; ordinary progress requires both TTYs. Caller-audited
  unused helpers/rendering inputs/re-export and inert color field removed, with
  ledger and history retained. INV-006/decision 120 clarified, no new architecture.
  Focused 343 passed; final diagnostics 23 passed. Full `scripts/check.sh`:
  4,171 passed, 40 deselected; three locked wheel installation profiles; actual
  Cockpit lint/types, 135 tests and build. No production/live host operations.

- [x] OPS-021 Make deployment helpers profile aware (2026-10-18, this commit).
  Positive source/current/target proof, one parsed staging version and fresh-prefix
  ancestry checks refuse cross-profile/unknown native effects. Static help and
  fixed-role validation precede runtime access. All 18 scripts inventoried;
  rootless readiness/UBI guidance corrected; dormant/native/consumer artifacts
  retained. Decision 132 preserves lifecycle/state/lock authority. Expanded focused
  selection: 342 passed; final help: 9 passed; 3 masked-unit refusal fixtures passed.
  Full `scripts/check.sh`: 4,148 passed, 40 deselected; all three locked wheel
  installation profiles; actual Cockpit lint/types, 135 tests and build. No host,
  production archive or live network workload performed.

- [x] OPS-020 Make hardening probes explicit and fail closed (2026-10-18,
  this commit). Static entrypoints, strict disposable target/lock/sentinel proof,
  owned health artifacts and qualified evidence replace implicit production
  workloads and exception-as-denial. INV-017/decision 131 record the diagnostic
  boundary. Focused probe suite: 74 passed. Full `scripts/check.sh`: 4,107 passed,
  40 deselected; wheel and all three locked installation profiles; actual Cockpit
  lint/types, 135 tests and build. No live Hub/NFS/manager/production workload.
