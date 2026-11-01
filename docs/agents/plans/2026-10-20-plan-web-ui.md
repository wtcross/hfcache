# Replace Cockpit with a publication-aware hfcache web UI

| Field | Value |
| --- | --- |
| Status | active |
| Created | 2026-10-20 |
| Authorization | Tyler's 2026-10-20 implementation instruction and bundled kickoff authorize activation, scoped source changes and owned local/isolated disposable tests on `feat/web-ui`, one work package per commit. No production deployment, remote publication, merge or tag. |
| Tracker | `docs/agents/plans/current.md` — sole active selector; intentionally not overwritten by extraction |
| Baseline | `6b8fae2e0997403ae5c716a2e92148af0a972af9` — main reviewed October 20, 2026 |
| Branch | `feat/web-ui` |
| Latest completed package | WEB-023, this commit; WEB-024 is next |
| Work-package family | WEB, deliberately introduced for this feature after collision check; one task = one work package = one implementation commit |
| References | [Bundle entrypoint](support/web-ui/README.md), [kickoff](support/web-ui/KICKOFF.md), [source review](support/web-ui/source-review.md) |

## Compatibility and rollback completed (2026-11-01)

WEB-023 completes with actual old0.2.2 transport/copied-state classifications and
owned native/rootless78→77→78 roundtrips. Both fixtures return to78; no operation
is replayed or unknown evidence deleted. Rootless candidate refusals and known77
configuration-read limits remain explicit. Required Gate1 passes9650 backend,
4051 combined web and16 wheel checks,1547 inputs unchanged; Cockpit is excluded
per the latest user instruction. All88 completed cases retain their required
layers, seven later-owner cases remain pending. WEB-024 guide acceptance is next.
See [WEB-023](tasks/web-023-compatibility-and-rollback-drill.md#completion-evidence)
for exact source/artifact and retained failure scope; no production acceptance.

## Installed acceptance through WEB-022 (2026-11-01)

WEB-022 completes under the adopted product-focused criteria: all85 owned-through
scenarios have required-layer and actual installed evidence; ten later-owner cases
remain pending. Required Gate21 passes9646 backend/4051 combined frontend/581
Cockpit/16 wheel checks with1545 inputs unchanged. Original failed aggregates,
unknown operations and qualified observations remain preserved. See the task's
completion evidence and human test-release summary for exact scope. This is not
production rollout or NAS acceptance. Next, refresh/apply the WEB-023–026 bounded-
testing/effort amendments before compatibility/rollback implementation.

## Resumption (2026-11-01)

The user's fresh-session execution goal resumes this plan and authorizes
WEB-022–026 in dependency order, local commits, final validation and closure.
WEB-022 remains in_progress. Reconcile retained evidence under the accepted
product-focused criteria before adding checks for any concrete missing clause.
The pause below is historical; its preservation limits remain in force.

## Pause handoff (2026-11-01)

The user explicitly requests a stopping point and pause after accepting the
product-focused proposal. Implementation is paused; WEB-022 stays in_progress,
WEB-023–026 pending, with no completion or partial package commit claimed.
The [fresh-session prompt](support/web-ui/fresh-session-implementation.md) and
[copyable goal](support/web-ui/fresh-session-goal.md) record current state,
accepted criteria, evidence and preservation limits. A new execution request
using that prompt authorizes resumption as active. No acceptance decision is
pending. The untouched ledger has73 completed/12 unfinished through WEB-022;
Gate21 is prepared/unrun and Gate20 remains the last full passing gate.

## Outcome and scope

2026-10-29 continuation authority: the user's explicit WEB-021 through WEB-026
goal authorizes the remaining sequential source work, owned disposable installed
acceptance, local work-package commits and plan closure. It supersedes the prior
WEB-020-only stopping point and grants no production/NAS, merge/push/tag or live
Cockpit-uninstall authority.

Deliver a strict-TypeScript React SPA that completely replaces the Cockpit plugin as hfcache's management UI. Use the approved archive-first Library, rich model/dataset detail pages, configuration-backed tags, Operations, Maintenance and Administration. Render a securely captured, publication-pinned README when available, alongside every supported existing source-attributed catalog/inventory/integrity field. Preserve hfcache's unique safety, complete-snapshot, publication, retention, recovery and uncertainty contracts. Borrow the reference downloader's organization, not additional product features.

The UI is served by the existing hfcache API application through the **same existing Caddy instance, TLS endpoint and Unix upstream as REST and MCP**. No second Caddy/frontend server/public listener/Node runtime is introduced. One protected Basic-authenticated human administrator is the initial user; existing REST bearer clients and read-only MCP credentials remain compatible. An internal authentication-provider/principal/permission boundary enables a later identity provider without implementing multi-user/OIDC/repository ACL scope now.

The shipped UI assets belong in the existing API image, whose build and runtime
FROM stages retain the pinned, streamlined UBI 10 micro base. No separate frontend
image is introduced. Preserve the existing CA-data-only donor boundary and omit
frontend build tools from runtime. WEB-021 must verify actual image ancestry,
installed asset hashes and absence of Node/package managers; labels alone do not
prove this requirement. Isolated browser test images are unshipped tooling.

The source result includes necessary missing config/card/host REST capabilities, strict runtime wire validation, immutable release asset packaging for native/rootless profiles, real unit/integration/functional coverage, human-facing guides and migration/rollback procedures. Per the latest user amendment below, deprecate Cockpit once the new web UI is complete and preserve its legacy source, history, licenses and live installation. No further plugin validation, exhaustive retirement work or uninstall is required.

## Explicit non-goals and authority limits

No inference/model execution, GPU-fit estimation, quantization conversion, selective/partial downloads, mirror/export/upload, arbitrary Hub browsing, full-text README search, new scheduler, generic terminal/file/systemd API, browser token editor, repository ACLs, signup or password reset. No generic payload endpoint or arbitrary remote image proxy. No initialization/reinitialization surface. Existing verified publication and complete-repository semantics remain.

Do not merge, push, tag, deploy, reload production Caddy, rotate real credentials, modify live services/timers/guards, access NAS contents or clear workload holds. Historical rollout authorization does not carry forward. Read `docs/agents/environment.md` before leaving the repository; use owned local fixtures and isolated guests only. Existing protected candidate/backup/lock/operation stores and original handles are evidence to preserve. Missing required test infrastructure blocks acceptance; it never authorizes production tests or security weakening.

## Selected architecture and necessary API delta

[Architecture](support/web-ui/architecture.md) is the implementation design; [API contracts](support/web-ui/api-contracts.md) define precise proposed boundaries and compatibility. WEB-001 reconciles concrete names/DTOs with current source and amends standing contracts/ADRs before implementation; the plan cannot silently supersede them.

Reuse catalog search/facets/details/variants, status/inventory/revisions, exact references/manifests, validation/plans, sync/verification/diagnostics/refresh, all existing maintenance, operations/results/events and runs. Do not add duplicate `/models`, `/datasets`, `/dashboard`, tag CRUD, cancel, SSE or WebSocket endpoints.

The missing capabilities are a safe installed config read and guarded keyed apply (reuse validation/planning with a managed-edit alternative), exact archived card read, fixed host status/calendar validation/schedule change/observer stop/journal diagnostics, and authenticated UI assets/bootstrap. Host effects require a narrow protected helper, not root API privileges or broad writable host mounts. Card GET reads only a bounded adjunct captured by writer work, not model payloads or the Hub. Keep strict existing capability/Envelope/operation/refresh schemas compatible.

Preserve current rootless schedule/observer denials when bindings are unproved; show clear reasons. Positive supported native host controls are implemented and tested. Do not turn restricted-profile UI into permission to add a scheduler, unmask legacy units or redirect system control to same-named user-manager units.

## Contracts, invariants and ADR review

Every task follows `AGENTS.md`, `docs/agents/planning.md`, `docs/agents/invariants.md`, `docs/agents/workflow.md` and `docs/agents/technical-record-policy.md`. Start from the invariant/ADR indexes and load relevant sections rather than all history.

Affected living contracts: `docs/api.md`, `server.md`, `api-client.md`, `mcp.md`, `configuration.md`, `discovery.md`, `schemas.md`, `security.md`, `cockpit.md`, `containers.md`, `operations.md`, `recovery.md`, `consumers.md`, `development.md`, `scripts.md`, deployment/release and human docs indexes. Human additions are mapped in [documentation requirements](support/web-ui/documentation-map.md).

Review at minimum INV-001/002/003/005/006/007 and current metadata/operation/supplemental/browser invariants; AD-01/06/12/14/15/16/17/18/21; FS-05–11/15/16/19 and initialization exclusion; relevant CP-01–14; FW-01–04. Confirm actual IDs/wording at execution. Review numbered ADRs 108–125 (services/REST/receipts/client/candidates/MCP), 126–129 (guarded rootless runtime), 133 (tags/discovery) and current amendments. Preserve134–139 Cockpit repair history without further plugin review under the latest user amendment. Allocate new ADR numbers from the live index, not hard-coded future numbers in this draft. Preserve old reasons/IDs and explicitly amend/supersede changed current requirements.

Particular contract changes need explicit rationale: Basic principal and CSRF, new privileged administration capability/helper, exact config application outcome protocol, new README presentation adjunct and any bounded source hashing, application static serving, separate frontend release artifact/dependencies/test gates, and legacy deprecation handoff. Never loosen unrelated archive/security invariants to make a browser feature pass.

## Phases

| Phase | Outcome | Work packages |
| --- | --- | --- |
| P0 | Contracts, strict workspace and typed wire boundary | WEB-001–003 |
| P1 | Basic authentication, shared-Caddy serving and guarded configuration backend | WEB-004–008 |
| P2 | Writer-captured README records and exact card API | WEB-009–010 |
| P3 | Library/detail/README/tags/operations/maintenance SPA workflows | WEB-011–017 |
| P4 | Fixed host schedule/observer/journal parity and Administration | WEB-018–019 |
| P5 | Cross-browser hardening, immutable packaging, installed acceptance and rollback | WEB-020–023 |
| P6 | Human documentation acceptance, legacy deprecation and final handoff | WEB-024–026 |

Each feature task includes tests and human documentation. Later testing/documentation phases broaden and verify prior work; they are not permission to defer initial coverage or guides. Tasks are serial by default. Necessary task splits get fresh WEB work-package IDs with explicit dependencies and acceptance, preserving completed evidence.

## Ordered task records

Task files own status and dependencies. This table lists order only; do not duplicate mutable task status here.

| Order | Work package and task | Depends on |
| --- | --- | --- |
| 1 | [WEB-001 — Activate the reviewed scope and resolve contracts](tasks/web-001-baseline-and-contracts.md) | None |
| 2 | [WEB-002 — Create the strict React workspace and mandatory local gates](tasks/web-002-strict-frontend-and-gates.md) | WEB-001 |
| 3 | [WEB-003 — Make the browser wire boundary precisely typed and validated](tasks/web-003-typed-wire-contracts.md) | WEB-002 |
| 4 | [WEB-004 — Add one Basic administrator through a replaceable principal boundary](tasks/web-004-basic-auth-and-permissions.md) | WEB-003 |
| 5 | [WEB-005 — Serve authenticated assets through the existing Caddy and build the real functional harness](tasks/web-005-shared-caddy-spa-serving.md) | WEB-004 |
| 6 | [WEB-006 — Implement a narrowly privileged host adapter and safe status projection](tasks/web-006-guarded-host-adapter.md) | WEB-005 |
| 7 | [WEB-007 — Expose safe installed configuration and exact managed-edit validation/preview](tasks/web-007-configuration-read-and-preview.md) | WEB-006 |
| 8 | [WEB-008 — Implement guarded atomic configuration application and recovery](tasks/web-008-atomic-configuration-application.md) | WEB-007 |
| 9 | [WEB-009 — Capture publication-pinned README presentation records safely](tasks/web-009-repository-card-capture.md) | WEB-008 |
| 10 | [WEB-010 — Expose a bounded exact-publication card read](tasks/web-010-repository-card-read-api.md) | WEB-009 |
| 11 | [WEB-011 — Build authority-scoped query state and durable browser observation](tasks/web-011-query-and-operation-state.md) | WEB-010 |
| 12 | [WEB-012 — Implement the unified model and dataset Library](tasks/web-012-library-and-discovery.md) | WEB-011 |
| 13 | [WEB-013 — Build rich exact-publication model and dataset detail pages](tasks/web-013-publication-detail-pages.md) | WEB-012 |
| 14 | [WEB-014 — Render archived README cards as inert, bounded React content](tasks/web-014-safe-markdown-rendering.md) | WEB-013 |
| 15 | [WEB-015 — Implement repository configuration and tag management workflows](tasks/web-015-configuration-and-tag-ui.md) | WEB-014 |
| 16 | [WEB-016 — Expose existing jobs, verification, diagnostics and reports](tasks/web-016-operations-and-reports-ui.md) | WEB-015 |
| 17 | [WEB-017 — Implement guarded maintenance and integrity remediation](tasks/web-017-maintenance-ui.md) | WEB-016 |
| 18 | [WEB-018 — Preserve fixed schedule, observer and diagnostic host functions](tasks/web-018-schedule-observer-and-journal.md) | WEB-017 |
| 19 | [WEB-019 — Complete the operator administration workspace](tasks/web-019-administration-and-diagnostics-ui.md) | WEB-018 |
| 20 | [WEB-020 — Harden end-user workflows, accessibility and bounded performance](tasks/web-020-cross-browser-accessibility-and-load.md) | WEB-019 |
| 21 | [WEB-021 — Integrate web assets and the host adapter into native/rootless releases](tasks/web-021-immutable-ui-release-packaging.md) | WEB-020 |
| 22 | [WEB-022 — Prove full installed functionality on isolated native and rootless targets](tasks/web-022-installed-functional-acceptance.md) | WEB-021 |
| 23 | [WEB-023 — Verify old clients, durable formats and evidence-preserving rollback](tasks/web-023-compatibility-and-rollback-drill.md) | WEB-022 |
| 24 | [WEB-024 — Complete the human operator and user documentation walkthrough](tasks/web-024-human-documentation-acceptance.md) | WEB-023 |
| 25 | [WEB-025 — Deprecate legacy Cockpit and hand off the independent web UI](tasks/web-025-retire-cockpit-plugin.md) | WEB-024 |
| 26 | [WEB-026 — Close the implementation with complete evidence and an operator handoff](tasks/web-026-final-gate-and-handoff.md) | WEB-025 |

## Execution and resumption

1. Review git/current-plan/progress/handoff and reconcile the baseline. Do not force-reset, discard dirty work or overwrite an existing active plan silently. If unrelated work is active, record a legitimate pause/supersession or a blocker based on the new implementation instruction; preserve its history.
2. Activate this draft only on implementation instruction, create/resume `feat/web-ui`, set current selector and mark WEB-001 in progress. New untracked bundle files are committed with the activation work package after validation. Do not commit to main merely because it was checked out.
3. Select the next dependency-complete task. Read its relevant contracts/support specs; update contracts/invariants/ADRs in the same work package as behavior. Implement and run required unit/component, integration, functional and docs gates. Record actual results, not intended commands or a previous source snapshot's pass.
4. Complete task evidence, append progress/Decisions/Operator handoff, update current selector, and commit `<WEB-ID>: <outcome>`. One work package per commit. No automatic push, merge or tag. If work is larger than one package, split before completion rather than hide several commits under one completed ID.
5. On interruption, inspect code/status/evidence before resuming; never rerun a completed mutation or discard unresolved fixture/operation state. A required infrastructure or safety blocker remains explicit. Continue only genuinely ready independent work; do not mark skipped host/browser tests as complete.
6. Close the plan only after final acceptance. Keep all dated/task paths stable, clear current active selection, and give a human-ready handoff that distinguishes implementation/fixture readiness from unperformed production migration.

## WEB-023–026 execution amendment (2026-11-01)

After completing WEB-022/9d11738, apply the [bounded-testing and effort policy](support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort).
The four task records select GPT-6.1-sol high/medium/high/medium with rationale
and concrete escalation criteria. All95 behaviors, required layers, real installed
browser/profile coverage, compatibility/rollback and safety outcomes remain.
The accepted product-focused method replaces mandatory runner cross-products;
optional diagnostics remain strict. Preserve original failed results and do not
repeat accepted effects. Historical bundle hashes/reviews remain intact.

Latest user amendment,2026-11-01: the user explicitly said to “ignore the cockpit
plugin moving forward” and deprecate it once the new web UI is complete. This
supersedes pending plugin validation, exhaustive retirement inventories, harness
ports, dependency cleanup and source/live removal. WEB-025 now records a
proportional deprecation/handoff while preserving legacy source/history/licenses,
generic clients/runtime helpers and the live installation. RELEASE-08 still
proves new-web independence using actual matching web/release evidence at its
existing minimum layers. All95 underlying new-web behaviors and remaining
WEB-023/024/026 work remain; this amendment claims no pass.

## Acceptance and validation

The [testing strategy](support/web-ui/testing-strategy.md), [95-scenario acceptance matrix](support/web-ui/acceptance-matrix.md), [interface/parity register](support/web-ui/interface-and-parity.md) and [migration specification](support/web-ui/migration-and-compatibility.md) are mandatory scoped acceptance, not optional suggestions. Machine-readable case and task indexes support execution audits but do not replace individual task evidence.

Completion requires:

- All four workspaces and rich model/dataset pages function without Cockpit, with config-backed tags and securely rendered archived cards. Existing operational and host-parity capabilities have executable tests or correct profile-specific denials; unsupported positive paths are not hidden as 'restricted'.
- The same actual Caddy fixture serves UI, existing REST bearer clients and fourteen read-only MCP tools with verified test TLS. Empty/nonempty prefixes, deep links, missing assets, errors and auth isolation work in Chromium, Firefox and WebKit. No fallback consumes API/MCP paths; no new public/privileged surface is introduced.
- Basic authentication, CSRF, strict types/runtime decoding, bounded reads/operations, exact publication identity, guarded config installs/locks, helper peer policy, untrusted README controls and no-replay uncertainty each have unit, integration and real functional failure coverage.
- Every new feature has human user/operator documentation created with its implementation, tested examples/links, accurate screenshots and useful troubleshooting. Agent docs/ADRs alone do not satisfy this requirement.
- Immutable UI/backend/helper artifacts are tested in actual isolated native/rootless profiles. Existing base/server/MCP installation and old client compatibility survive; durable-format/rollback drills preserve unknown state and unfinished evidence. The independent new web UI and legacy deprecation handoff preserve Cockpit source/history/licenses and the live installation.
- `scripts/check.sh --require-web --with-build` passes on final source with no required new-web/backend skip; no further legacy plugin validation is required. Separate direct installed final acceptance follows the adopted product-focused criteria and accounts for all95 scenarios with exact nodes, commands/exits, coverage/budgets, artifact hashes, browser/profile scopes and locators. `--with-web-functional` remains an optional strict diagnostic, never a claimed pass when unexecuted.
- No production deployment, NAS acceptance, Caddy reload, credential/service/timer change, remote push/tag or live plugin uninstall is claimed. Remaining production authorization/acceptance is a separate operator handoff, not hidden source incompleteness.

## Lifecycle and amendments

- 2026-10-20: Draft created from Tyler's approved UI direction and request for an executable plan bundle, continuous human documentation, core test coverage and the same Caddy instance. No implementation or deployment performed by bundle creation.
- 2026-10-20: Explicit implementation/kickoff instruction activates the plan on
  `feat/web-ui`; baseline matches exactly, selector was inactive and only intended
  bundle additions existed. No WEB ID collision. [WEB-001](tasks/web-001-baseline-and-contracts.md)
  resolves [exact execution boundaries](support/web-ui/execution-contract.md),
  allocates decisions 140–144 (retirement conditional), preserves original bundle
  hashes and records [prerequisites](support/web-ui/prerequisites.md). All 95
  feature cases remain pending until actual required test layers establish them.
  Production/remote/live archive restrictions and historical unknown evidence
  remain unchanged. No acceptance requirement is relaxed.
- 2026-10-20: WEB-001's mandatory baseline gate exposed a reproducible intermittent
  Bash line-reader wait refusal. Include its minimal in-memory framing correction,
  deterministic regression, bounded timing and human troubleshooting in this
  baseline package before proceeding. No web feature or production rollout is
  folded into that correction; the exact original baseline/evidence remains.
- 2026-10-20: [WEB-002](tasks/web-002-strict-frontend-and-gates.md) introduces the
  strict locked React workspace and mandatory web gate, complete dependency
  license inventory, no-skip/timeout refusal and retained local browser evidence.
  Required backend/Cockpit/web gates pass; the built-shell check is preliminary
  and disconnected. Initial contrast-artifact loss is recorded, and subsequent
  real failure-retention and timeout proofs pass. No Caddy/API/installed feature
  acceptance is inferred; all 95 feature cases remain pending. Next is WEB-003's
  precise wire boundary. Scope, task order and production restrictions are unchanged.
- 2026-10-20: [WEB-003](tasks/web-003-typed-wire-contracts.md) completes precise
  source-audited route/mode contracts, reconstructing TypeScript decoders, bounded
  pre-conversion numeric and pinned Unicode16 validation, explicit same-origin
  transport and classified failure/no-replay behavior. Independent original-model
  and malformed-wire corpora, component coverage and 14 actual React/API browser
  checks pass in the complete strict gate, preserving backend/Cockpit/install
  regressions. Decision145/INV021 and human references align. The permitted
  temporary source fixture does not prove Caddy/Basic/installed or platform
  behavior; all95 feature cases remain pending. Exact future config/card/host
  DTOs enter the registry with their implementing endpoints, as recorded in the
  task. Baseline prefix header/redirect defects discovered read-only are retained
  for WEB-005, not silently redefined. Next is WEB-004; production limits hold.
- 2026-10-20: [WEB-004](tasks/web-004-basic-auth-and-permissions.md) completes the
  optional protected Basic administrator, bounded independent Argon2id provider,
  internal grants, subject-bound original keys and browser CSRF, preserving REST
  bearer and read-only MCP compatibility. Decision146 and human provisioning/
  delivery/rotation/security guides align. Actual installed direct-TLS API testing
  in a fresh isolated guest passes48native browser checks across three engines and
  both prefixes, with real preflight/TLS negatives, kernel sandbox and exact drain.
  A final strict source gate passes5940Python and all preserved Cockpit/web/install
  stages on the same frozen1278-file snapshot. Superseded gates and eight failed
  native attempts remain explicit. Built UI/shared-Caddy/platform roles and all95
  full feature cases remain pending. Next is WEB-005; no production/remote/NAS/
  retirement action is authorized or claimed. Shipped UI assets remain allocated
  to the existing pinned UBI10micro API image, without runtime Node.

- 2026-10-21: Tyler explicitly requests a stopping point and pause. The selector
  has no active plan/task; this plan resumes only on explicit user instruction,
  beginning with incomplete, uncommitted [WEB-005](tasks/web-005-shared-caddy-spa-serving.md).
  Preserve frozen host source14, guest source13/artifact4 provenance, all failed/
  UNKNOWN records and conditional completion HOLDs. Only already-running gate14
  and already-started read-only closure work may finish before stopping; their
  final results are pending at this checkpoint. Common21 manifest/native20
  provisioning pass without services started; rootless21 is uninstalled and all
  common21 functional execution is unstarted. No further binding, provisioning,
  preparation, tests or role starts follow this pause checkpoint.
- 2026-10-21: The already-running final source gate14 finishes before the pause:
  `scripts/check.sh --require-web --require-cockpit` exits0/reaped,6643Python and
  all required wheel/Cockpit/web stages pass. Independent completion audit
  `d80896c63f824cffb9ade963ed611481422bd5a346ef3c57538f311323b174d4`
  confirms all1310 frozen hashes/modes unchanged and seven processes closed.
  All already-running checks are finished. The plan remains paused; WEB-005 is
  incomplete/uncommitted because installed all-six acceptance remains required.

- 2026-10-21: Tyler explicitly resumes with “continue”. Reactivate this plan and
  [WEB-005](tasks/web-005-shared-caddy-spa-serving.md), preserving the prior pause
  and every failed/UNKNOWN record. Gate14 and its independent audit have completed
  successfully on frozen host source14; installed acceptance remains incomplete.
  Continue private common21 binding/review and fresh required all-six acceptance
  with guest source13/artifact4 provenance unchanged. No successor task, feature
  closure, production action or remote publication follows this resumption.

- 2026-10-21: WEB-005 completes scoped shared-Caddy serving and the provider-neutral
  installed harness after source14/gate14, original guest13/common21 all-six
  monitor0/normal closure/audit and a separate exact compatibility receipt pass.
  Preserve the prior pause and every failed/UNKNOWN/HOLD. Later ROUTE02/03/06
  clauses, RELEASE03/WEB021 and full95 remain pending; next is WEB-006. No
  production/NAS/remote/retirement authority changes.

- 2026-10-21: WEB-005 is committed as `07d10e0`; clean checkout selects WEB-006
  in progress. Adopt its narrow protected read/helper and fresh Basic admission
  boundary before source changes; preserve bearer/MCP, original operation
  handles, denied write grammar and production restrictions. Installed native/
  rootless acceptance remains required for this new work package.

- 2026-10-22: WEB-006 source13 strict gate passes and fresh native/rootless
  staging plus policy26 preparation pass in the owned disposable guest.
  Preserve failed native12 and partial authority9; fresh authority10 now passes
  with unchanged controller rules and protected exact-byte historical copies.
  All45 preparation commands are reaped; no application starts or installed
  feature acceptance is inferred. Native/rootless functional, faults, exact-ID
  secret lifecycle and strict drain proofs remain required before completion.

- 2026-10-22: A later native13 credential failure is attributed through exact
  invocation/PPID/openat/inode/SID and separate AVC path/device proof. Preserve
  prior failed/false/UNKNOWN records. Source14 adds only trusted-manager secret
  file open, with helper denials unchanged, and updates human contracts/tests.
  APP-only source9-to-source14 input comparison also passes with independent
  actual review; original source9 build provenance and pinned UBI10micro recipes
  remain intact. Host compatibility is false and new installed proof is required.
  Focused297 and documentation206human/27helpers pass; fullstrictgate14 passes0
  with all1359 hashes/modes unchanged. Protected source14 transfer also passes.
  Read-only audit and same-inode preservation also pass: private source14 is
  extracted, public source remains13, and loaded policy remains26. Original
  selector/configuration and both13 release trees are retained at recorded
  paths; their five old names are absent. Public source14 update and native/rootless14 staging also pass. Policy27 also passes with original26 inodes retained and no service starts. Fresh
  authority11 preparation fails before publication with errno24 while retaining
  historical evidence. A new read-only getter confirms all28 fixed publication
  and selection paths absent, with original failure/channels/donors preserved.
  A measured finite2048 disposable collector budget is restored exactly to1024,
  with its hard limit unchanged. Fresh authority12 then passes all45 preparation
  commands, original installed validation and held-input closure; failed11 and
  every prior record remain preserved. The one original native14/auth12 run
  then fails before its summary; preserve that failure and diagnose its new
  generation/service state read-only before any correction or fresh attempt;
  installed native/rootless/fault/secret/drain acceptance remains pending. No completion
  or production/remote action follows these preparation results.

- 2026-10-22: Source15 strict gate/build/transfers pass and image07bd818e loads
  once. Preserve the failed outer load classifier and separate successful
  exact saved-output interpretation. Original image audit then passes runtime
  bytes and stopped/exit0 inspect but refuses raw Podman gate mount Mode
  `Z`-to-empty equality; preserve this failure and original CID/PID handles.
  Checkpoint67 records the exact actual result and1361 unchanged source leaves.
  Separate read-only completion/process/cgroup proof, finite preservation,
  native4/rootless5 staging/authority15 and installed acceptance remain pending.

- 2026-10-22: Checkpoint68 records separate read-only image completion passing,
  original PID/cgroup closure, four no-replace same-inode moves and successful
  original native4/rootless5 staging. Both failed original image callers remain
  failed; no lifecycle replay or application start occurs. Source15's1361 leaves
  remain unchanged. Exact authority core/input bindings are ready; their donor
  transfer, fresh authority15 and installed native/rootless/negative/fault/
  secret/drain acceptance remain pending before WEB-006 can be committed.

- 2026-10-22: Checkpoint69 records source/input donor success and original
  authority15 preparation failure before application startup. Preserve failed15,
  its private channels and every earlier result; its functional successors stay
  inert. Read the exact saved stack and publication state before selecting any
  fresh namespace. Existing source15 gate/image/preservation/staging evidence
  remains valid; installed acceptance and WEB-006 completion remain pending.

- 2026-10-22: Checkpoint70's bounded read-only diagnosis reaches the generic
  4MiB limit while recording the copied Node test executable. Exact Node/
  partial-state inventory is next. Preserve failed15/partial publication and
  all inert15 successors; select fresh authority16/control17 intent with the
  unchanged source15/native4/rootless5 stages, disjoint browser input paths and
  positive retained-state joins. No new authority or application has started.

- 2026-10-22: Checkpoint71 confirms both exact test-only Node copies at
  123656816B and inventories all263 retained partial15 nodes plus parents and
  shared support files through a closed read-only call. No authority replay or
  application start occurs. Fresh16 normalization/donors precede native/rootless
  installed acceptance; source15 and existing stages remain unchanged.

- 2026-10-22: Checkpoint72 records successful fresh3 donor16 transfer and
  original authority16 preparation, with16 commands0/reaped, installed validator
  and complete retained-input closure. Source15's1361 leaves stay unchanged.
  No application starts. Account for the measured larger authority through
  explicit bounded harness call sites before native16's first functional run;
  installed native/rootless/negative/fault/secret/drain acceptance remains pending.

- 2026-10-22: Checkpoint73 preserves the first original native16 functional
  failure before READY/SUMMARY. A separate read-only post-run check closes all
  recorded handles, roles, cgroups and endpoints. Preserve its present native4
  selection/configuration and exact generation; all16 success-dependent scopes
  remain inert. Diagnose actual startup evidence before any correction or fresh
  attempt. Source15 stays unchanged and installed acceptance remains pending.

- 2026-10-22: Checkpoint74 preserves a failed journal collector and records a
  separate corrected read-only collection passing with all9 queries0/reaped,
  closed captures and unchanged manager state. Real symlink regression fixes
  the collector's stale fixture-version comparison; no functional outcome is
  promoted. Original-window journals contain no API exception/code/frame.
  Trace bootstrap readiness and retained logs/responses next, preserving native16
  failure/current selection and all inert successors. Source15 remains exact.

- 2026-10-22: Checkpoint75 records saved startup/static/workspace evidence
  passing, with4 readonly queries0/reaped and all captures closed. Both public
  CA/server certificates are outside the exact original native16 window;
  original exception/sole cause is not recovered. Select fresh unpublished
  derivative17/control18/generations18 with valid owned test PKI and explicit
  consumer bindings, retaining old PKI/current3/failure records and reusing
  unchanged source15/stages/browser tools. Source-only bounded bootstrap
  diagnostics pass24 root tests; no17 publication/start or acceptance occurs.

- 2026-10-22: Checkpoint76 records actual isolated PKI17 renewal passing:
  new7-day CA/leaf pass chain/IP/server-purpose checks, private nodes are labeled
  before bytes, old unit/PKI and current3/key/kernel remain retained. Only two
  isolated Caddy credential-source paths change; no daemon reload/start occurs.
  Root19 renewal and26 controller-guard/actual-consumer tests pass0skip.
  Fresh derivative17 core/inputs are locally data-bound with all other AST
  unchanged; donor transfer/preparation/functional proof remain pending.
  All1361 source hashes/modes stay exact; no installed acceptance is claimed.

- 2026-10-22: Checkpoint77 records original donor17 transfer success, then
  original authority17 preparation failure before authority RESULT/application
  startup. The first query returns0/reaps, but retaining its private output
  raises FileNotFoundError; original outer false closure/failure is preserved.
  Read the protected traceback and prove fresh closure before correction.
  All17 success-dependent scopes stay inert; source15 remains exact and no
  installed acceptance or production change is claimed.

- 2026-10-22: Checkpoint78 records separate saved failed17 traceback/closure
  passing,6 readonly queries0/reaped, unchanged current3/key/13 roles and closed
  original handles. Original trace/source plus a real-child regression establish
  the query-output-before-WORK preparation defect. No application started.
  Select fresh unpublished18/control19, preserving all17 failures/inert scopes,
  reusing PKI17/stages/source15 and moving owned WORK initialization before the
  first query. Real selector4/5 regression prevents stale fixture literals.
  Root14 getter/3 collector/92 inert18 checks pass0skip; installed acceptance
  remains pending and all1361 source hashes/modes stay unchanged.

- 2026-10-22: Checkpoint79 records donor18 success, then original preparation18
  failure after two completed same-inode preservation moves. Selector/deployment
  remain at protected WORK18 destinations; policy remains at its original path.
  Six queries0/reaped and final strict closure pass; no roles start. Preserve
  the partial result, never replay completed moves, and read exact saved trace/
  partial inventory before correction. All18 success-dependent scopes stay inert.
  Root51 core/17 donor/28 safe checks pass0skip but do not establish installed
  acceptance. Source15 remains exact; production is untouched.

- 2026-10-22: Checkpoint80 records separate saved18 partial trace/inventory
  passing,6 queries0/reaped and complete capture/handle closure. Exact trace,
  source and real-file regression establish enriched move provenance passed
  to fixed capture-record equality. All16 partial nodes and both moved inodes
  are retained; remaining policy/key unchanged, staged units inactive. Prepare
  a new scope consuming both completed moves and moving only the policy after
  fresh strict drain; nothing is published/replayed yet. Root15 checks pass
  0skip and source15 stays exact; installed acceptance remains pending.

- 2026-10-22: Checkpoint81 retains first19 transfer validation failure before
  publication, fixes a new consumer's tuple ABI under distinct v2 paths, and
  records genuine v2 transfer/preparation success. Original WORK18 selector/
  deployment moves are consumed, only policy moves once; all current aliases
  are absent. Eight commands0/reaped, installed validator/controller load pass,
  no roles start. Fresh19/control20 readiness may now bind native19 acceptance.
  Root45 checks0skip/actual17+5 FD preflights pass; source15 remains exact.
  All old failures and18 successors stay retained/inert; acceptance is pending.

- 2026-10-22: Checkpoint82 records original native19 functional failure1/no
  SUMMARY, retaining original outer refusal. Separate post/saved/UID1000 readers
  pass; actual PKI/first TLS bootstrap/native principals pass, all original
  handles/13 roles/four cgroups/five endpoints close. Saved ready/runtime and
  file-input checks pass but no browser intent/report exists. Read-only launch/
  image-visibility diagnosis precedes correction/fresh scope; all19 functional
  successors remain inert. Root130 tests0skip and1361 frozen source checks pass.
  Installed acceptance remains incomplete; no production change or replay.

Checkpoint82 phase-name correction2026-10-22: the collector checked `normal`,
while the actual checker starts with `baseline`. Its missing normal-named files
do not establish that no browser started or no baseline evidence exists. The
independent launch readback e86fb00d/58090 passes collection but its synthetic
normal request is rejected by input_bundle before an engine call. That is not
an original browser exception. Original native19 remains failed; corrected
baseline evidence/closure readback is next. Original receipts remain unchanged;
`.scratch/web-006-source15-checkpoint82-phase-clarification-v1.json` records
this interpretation correction. No functional acceptance or replay is claimed.

- 2026-10-22: Checkpoint83 records corrected actual baseline/create evidence.
  Saved credential-free Podman error proves create --stop-timeout=-1 rejection
  rc125; independent exact-name absence/CID absence/three CLI closure pass.
  Original failure/drain_unknown and two failed diagnostic consumers remain
  retained. Select unpublished20/control21 to remove only unsupported create
  flag while retaining explicit indefinite graceful stop; preserve three new
  native19 aliases once and retain older moves. Root37 focused checks0skip,
  207/27 docs and1361 source hashes/modes pass; all installed acceptance pending.

- 2026-10-22: Checkpoint84 retains first20 donor validation failure and failed
  diagnosticv3; readonlyv4 passes collection with exact reproduced tar-size
  refusal in the new consumer. All8futurepathsabsent/21local+guestinputsclose,
  noqueries/publication/app/moves. Newv2 preserves exact98-prefix sizes/order
  within inherited128MiB ceiling, keepsnewsmallinputs4MiB, and fixespublic
  manifest/control-input filtering. Real15diagnostic/10prefix regressionspass
  0skip; source1361unchanged. Fresh20 preparation/native20 stillunperformed.

- 2026-10-22: Checkpoint85 records genuine fresh20-v2 donor/preparation passes,
  all captures/commands closed, validator/controller load passing and3newmoves
  preserved once. Original failures retained, source1361exact. No app roles
  started; native20/rootless/negative/fault/secret/drain acceptance remains next.

- 2026-10-22: Checkpoint86 records original native20 failure1/noSUMMARY and
  separate strict post20 passing with28+5original handles gone,13roles/four
  cgroups/five endpoints closed. PKI/bootstrap/native principals pass; cause
  remains unobserved, all20 successors inert. Source1361exact, no replay.

- 2026-10-22: Checkpoint87 saved reader passes: original create0/exactCID
  retained, report absent, saved start-attach drain_unknown unchanged. Six
  engine handles and attach gone; actual container state/startup cause remain
  unobserved. ExactCID read-only inspection next; no replay/fresh preparation.

- 2026-10-22: Checkpoint88 exactCID inspection passes; current browser state
  created/PID0/nonrunning, labels/image match, private OCIerror classifies
  SELinux permission denial. Original unknown stays unknown. Actualsource1123
  is terminaldrain refusal; precise startupaction requires savedprivateparse.

- 2026-10-22: Checkpoint89 private saved-error projection passes with fixed
  label/change/SELinux words and container_file_t:s0 object context. No raw
  error/environment/path export or engine query. Join fixed original volume
  sources next; precise target/correction unselected, original failure retained.

- 2026-10-22: Checkpoint90 identifies only renewed publicCA at original
  volumeindexes5/6 in savedlsetxattr/relabel error. Metadata root0644/1574B
  user_home_t unchanged. Select separate identicalrootownedCAcopy prelabelled
  container_file_t:s0 +new gatedreadonlyprototype; no publication/probe yet.

- 2026-10-23: Checkpoint91 records actual separate public CA publication passing
  with root0644/container_file_t:s0 verified before1574 public bytes. Original
  CA/PKI and native20 failed/UNKNOWN evidence remain unchanged; no app/container
  starts. New gated read-only primitive and installed acceptance remain pending.

- 2026-10-23: Checkpoint92 records the actual gated public-CA read passing in a
  new UID1000 capless/NNP/seccomp container with observed SELinux MCS pair, exact
  1574B/SHA and original CLI/init/cgroup drain. Original-role closure was before
  the probe; separate fresh closure/finite mount inventory are next. Original
  failed/UNKNOWN and installed application acceptance remain unchanged/pending.

- 2026-10-23: Checkpoint93 records actual fresh post-probe strict app/probe
  closure and finite public inventory passing. All230 old root-owned tool nodes
  remain unchanged/user_home_t; select new byte-identical prelabelled copies
  plus a prelabelled new manifest. Current parent/alias/ROOT observations now
  support preparing fresh21; no new authority/app acceptance is claimed.

- 2026-10-23: Fresh21 fixture correction also selects7 identical prelabelled
  code copies, preserving all1361 original guest source full9/hash/contexts.
  Only bind sources/copy validation change; original container code targets,
  Node argv, executable driver bytes and lifecycle stay fixed. Local review
  precedes new publication and no application acceptance is inferred.

- 2026-10-23: Checkpoint94 records original bounded read-only capture of exact
  control20/manifest20/generation20 JSON bodies passing, with ROOT467 unchanged,
  no guest publication/query/action and original executor/SSH/captures closed.
  All25 static input bodies now verified locally for composed fresh21 admission;
  fresh21 remains unpublished and installed application acceptance pending.

- 2026-10-23: Checkpoint95 records original fresh21 eleven-object donor
  transfer passing with all local/guest captures and original executor/SSH
  closed, six queries0/reaped, exact ROOT467→469. Preparation21 and application
  runs have not occurred; actual donor-bound safe caller precedes them.

- 2026-10-23: Checkpoint96 records original preparation21 passing with exact
  tool/code prelabelled copies, originals retained,3current aliases preserved,
  ROOT473 and validator/controller/source/key/kernel/FD/process closure.
  Noapproles start. Native21 bound fromgenuineoutcomes precedes rootless normal;
  required functional acceptance remains pending.

- 2026-10-23: Checkpoint97 retains originalnative21 functionalFAIL1/noSUMMARY
  and independent strictpostPASS13roles/28+5handles/4cgroups/5endpoints.
  PKI/authenticatedbootstrap200 pass, but savedbrowser diagnosis/closure remain
  unobserved. Preserve currentnative21 aliases and allfailed/inertsuccessors;
  nofresh22 selected. Installed acceptance incomplete.

- 2026-10-23: Checkpoint98 retains firstsaved21 getterFAIL at text-vs-object
  JS diagnostic projection. Partial originalproof shows create0/containerclosed,
  but reportfailed/originalUNKNOWN and underlying UIcasecause unobserved.
  Separate bounded correctshapev2readonly capture next, no replay/fresh22.

- 2026-10-23: Checkpoint99 records readonlysavedv3/factsPASS: Firefox2host/UI
  passes and5actual10→expected2 refusalassertions identify harnesswrongexit.
  Chromiumsetupunclassified, WebKitcertificatefailure/sourceaudittrustmismatch
  stillneedmeasurement; all21functional failures anddependentINERT remain.
  Correctharnesscontract, measuretrust/closure beforefreshscope.

- 2026-10-23: Checkpoint100 records originalCID/currentprocess/scopeclosurePASS
  andexactChromiumlatebodyprotocolmarkers. Five-file source16harness/docs fixes
  arefrozen1361/snapshot2da61616; actualstrictgatebegan10:53Z,noPASSyet.
  APIUIUBImicroartifactsource15unchanged; WebKittrustmeasurement/exportnext,
  nofresh22selected oroldfailurepromotion.

- 2026-10-23: Checkpoint101 records actual strict source16 gate PASS, all1361
  hashes/modes unchanged, and separate public-CA export21v3 PASS. Installed
  browser acceptance remains pending; test-image measurement and source16 test
  projection preparation continue. Original source15 UBI10micro runtime
  provenance and all failed/UNKNOWN scopes remain unchanged.

- 2026-10-23: Checkpoint102 records actual no-network browser-image measurement
  PASS, Config.User1000:1000 and old expired CA/current CA absent from OS bundle.
  New probe processes/cgroup close. No image build or TLS/functional acceptance
  is inferred; distinct trusted-only descendant and same-current-Caddy untrusted
  rejection preflight precede a fresh source16 functional fixture. Source16 and
  original source15 UBI10micro API/UI artifact provenance remain unchanged.

- 2026-10-23: Checkpoint103 preserves the original trusted-test image build
  stage failing its path-diff audit after command0/new untagged IID053ce201.
  Original images/tags/container IDs and recorded CLI/IID/input closure pass;
  overall failed/capture flags stay false. Read-only exact diff and fresh
  closure must precede any policy amendment or post-build audit. No replay,
  image eligibility, fresh fixture or functional acceptance is claimed.

- 2026-10-23: Checkpoint104 records separate retained-image readonly diff PASS
  and fresh closure. Only /tmp is outside the original path policy; actual baked
  directory/mount and post-build OS trust/package/updater audits remain required.
  Original build failure/false flags stay unchanged and its image is ineligible.
  Host-only source16 metadata projection can proceed independently without
  selecting a new guest scope or relabelling original source15 runtime evidence.

- 2026-10-23: Checkpoint105 records actual host-only source16 two-TOML fixture
  projection PASS, snapshot706a11e4/1361 leaves with108API/27UI source equality.
  Canonical0.2.2 and original source15 runtime artifacts remain unchanged. No
  image/build/guest/install/authority selection or functional acceptance occurs.
  Local transfer preparation continues while independent image audits remain open.

- 2026-10-23: Checkpoint106 retains paired OS audit overallFAIL9d830598 after
  both probes pass and final image query passes. New bundle contains currentCA;
  both images have one /tmp directory entry and shared file label s0, contrary
  to draft empty/per-init-MCS assumptions. New image stays ineligible pending
  separate bounded retained-filesystem proof; original failures stay unchanged.

- 2026-10-23: Checkpoint107 retains three separate readonly rootfs inspection
  failures. Actual /tmp inode/non-mapping full9 match; both CIDs stay exited0,
  inspector CLIs close and fresh37 audit handles are gone. Existing subtree is
  nonempty/wider than64; complete bounded streaming equality remains required.
  No image eligibility or source16 guest scope/functional acceptance is granted.

- 2026-10-23: Checkpoint108 records streaming retained-rootfs audit PASS and
  separate fixed browser-fixture admission, preserving all original failures.
  Both565entry/1419404byte subtrees match; only /tmp directory metadata is excepted
  for dffe5ada->053ce201/currentCA1dbeeac8. Same-Caddy browser acceptance remains
  required. Host-only source16 packet36.46MB/13members also passes; no fresh guest
  scope/transfer/install/staging or functional acceptance occurs.

- 2026-10-23: Checkpoint109 retains source16 transfer FAILa114877d after
  protected data copy, before PUBLIC mkdir: inherited O_PATH FD cannot listdir.
  Source15 all1361full9/hash/SID records and strict13role closure pass. A separate
  completion must revalidate retained data and use a readable parent FD, with
  no protected-write replay, installation or fresh functional authority yet.

- 2026-10-23: Checkpoint110 records separate retained-data public-copy completion
  PASS21fcee64:1361source16 files/full9/hash/mode/SID verified, oldsource15 before/
  after/finally unchanged and strict13role closure. Original failed transfer and
  protected data remain unchanged. No package projection, fresh functional
  authority, install/staging/Caddy change or browser acceptance yet.

- 2026-10-23: Checkpoint111 retains package-projection FAIL513d3fae: first
  bind command32/reaped; readonly/import unproved.108package inventory/source16
  file preservation and strictrole closure pass. New target/intent preserved;
  separate readonly stderr/mountinfo/inode observation precedes further action.
  No automatic retry/cleanup, functional authority or installed acceptance.

WEB-006 checkpoint112 update2026-10-23: separate readonly mount diagnostic passes.

Actual executor3445091/start425286736 returns0/reaps/absent in1.699454s.
Local15f3bb9d/98145bytes and protected77940f35/58847bytes preserve the
observations. All50held local descriptors rejoin/close;17local models pass
with zero skips. Saved credential-free mount stderr is classified missing-path,
with procFD239 referenced; raw error text is not exported. Actual target
inode18978723/full9/SID exactly matches the original underlying empty directory,
with zero entries, no exact mountinfo row and readonly=false. Mountinfo rejoins.
All5original projection process identities are freshly gone, and final13role/
4cgroup/5endpoint strict closure passes. No retry, cleanup or unmount occurred.
Original FAIL513d3fae/32346d60 and its false readonly/completion flags remain
unchanged. This observation clears only mount-state uncertainty.

Next is a separate direct mount(2) completion using held source/target directory
FDs, after fresh empty-target/mountinfo/inode guards. No installation/restaging,
fresh functional authority or browser acceptance is granted. Source16 gate and
fixed browser admission remain valid; production/NAS/live Cockpit untouched.
Checkpoint112 `.scratch/web-006-source16-current-state-v112.json` SHA256795cf39dfcf27252d96ae49aeb1bb0d9ffb45d75724da8a14855fd2fe0b4bfca.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted.

WEB-006 checkpoint113 update2026-10-23: separate readonly package completion passes.

Actual executor3446537/start425345409 returns0/reaps/absent in4.951319s.
Locald9d4e45b/181815bytes and protected39a660ce/135386bytes preserve the result.
Rootf181a65e/131171bytes and caller1d42abd2/58237bytes pass composed lint,
16local models/zero skips and53input/56FD/QEMU capture checks; SSH114297bytes
remains below120000. Fresh receipt/empty-target/full9/mountinfo guards precede
both effects. Direct owning-process mount(2) calls bind4096 and remount4129
return0/errno0; exact target mount row is readonly. All108package leaves share
installed full9/hash/SID and match wheel/source16. UID1000 import104145/
start26228706 resolves the new projection/version0.2.4; wrapper104144/
start26228705 returns0/reaps and both identities close. The original wheel
79f1d75a/500283bytes is copied once to the new installed-v1 scope, labelledusr_t
before bytes. Public source-root full9 remains unchanged in this completion.
All1361source16 files pass before/after/finally; held releases[], all5actual
CLIcommands close and final13roles/4cgroups/5endpoints are strictquiescent.

Original FAIL513d3fae/32346d60 and UNKNOWN-era receipt remain unchanged.
No reinstall/staging, selector/service/timer/policy/credential change or browser
acceptance occurred. Next: empty prelabelled shared public tool/code inputs,
new launcher with real same-current-Caddy untrusted/trusted epoch, then a fresh
native/rootless authority. Old21success-dependent scopes remain inert.
Checkpoint113 `.scratch/web-006-source16-current-state-v113.json` SHA256ad5c2fea0cd8daf8ecb7981c738033d32d169bd1ef85b0c15c7401d0bb08a4fc.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint114 update2026-10-23: new prelabelled public browser inputs pass.

Actual executor3447872/start425396209 returns0/reaps/absent in9.572909s.
Localcf54e1d6/325758bytes and protected5dba6bfe/274025bytes retain the result.
Root1228ef4b/117133bytes and callerf7cf5795/57499bytes pass composed lint,
13local models/zero skips and53input/56FD/QEMU preflight; SSH101664bytes
stays below120000. Model tests use owned repository scratch; the initial /tmp
model fixture refusal is preserved and corrected without relaxing parent guards.

New `/home/webfixture/hfcache-web006-source16-fixture-v1/.scratch/provisioning/web006-browser-inputs-source16-v1`
has194ordinary files/50directories, allroot0:0 with container_file_t:s0 set
while EMPTY before bytes/entries. The185tool files total144525705bytes;
seven source16 browser-test files, public currentCA1dbeeac8 and fixtureinventory
c70000ea are copied with exact hashes. Protected inventory0600 is copied to
new public0644; its original is unchanged. All old185file/45directory full9/
hash/SID records remain held and rejoin; corrected source16 seven-file records
also rejoin. New tree entries are exact, with no extra paths. Actual heldFD740
plus reserved32 remains below existing soft1024/hard524288; limits unchanged.
The108same-inode readonly package files pass before/after. All1361source16files
pass before/after/finally; held release failures[], final13roles/4cgroups/
5endpoints strictquiescent. No browser, selector, services, timers, credentials,
policy, reinstall/staging or production action occurs.

Next: a fresh launcher using modern EOF/reap ownership for BOTH untrusted and
trusted browser containers, shared protected code mounts without borrowed :z,
and actual same-current-Caddy CA/leaf epoch checks. Legacy005 forced-stop drain
must not be imported into the new phase. Old failed/UNKNOWN receipts remain
unchanged; no fresh functional authority or installed acceptance yet.
Checkpoint114 `.scratch/web-006-source16-current-state-v114.json` SHA25635674181cfc8d860666029ac3b775cc195d6627c41de80c44b30a3b8d00c2d95.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint115 update2026-10-23: readonly authority inputs pass; launcher draft stays inert.

Actual reader3449764/start425468239 returns0/reaps/absent in3.982534s.
Local0465e0b6/351279bytes and protected0ec8e997/294863bytes retain the result;
rootfb88d252/116843bytes and callerd45c0ef3/61344bytes pass composed lint and
59input/62FD/QEMU preflight. Quoted SSH107817 stays below120000. All194public
file/50directory full9/hash/SID inputs rejoin unchanged; source16 all1361files
pass before/after, releases[], final13role/4cgroup/5endpoint strict closure.
No services/selectors/credentials/policy/sudoers changed, no authority selected.
Static control22 and manifest21 reconstruct EXACT original bytes/hashes977a3ca9
(31471bytes) and89adb78f(5004bytes). Actual controller source is confirmed
2a2219d8/111918bytes. Tool inventory is an explicitly SEMANTIC projection:
183files/schema1; localf34dfeb1/24577bytes differs from original bytehashfb271905.
Do not claim a raw-byte join or original hash for that projection.

INERT launcher70b05f87/99007bytes and helper7caf2027 derive both phases from the
modern browser owner; legacy005 forced-stop drain is not imported. Negative
stdin is DEVNULL and receives no auth, fixtureCA/NSS/Firefox trust injection;
all194public files/50dirs plus original manifest/runtime are held/full9/hash/SID
rejoined across before/middle/after TLS-peer observations and negative/trusted
browsers. Borrowed mounts use :ro, new owned gate/phase/output only may relabel.
Per-mode negative workspaces preserve distinct original handles. Loopback/pure
models51PASS/zero skips and composed launcher lint pass. This is NOT guest
publication, a selected authority or real Caddy/browser/installed acceptance.
Model evidence6cea91b8/1498bytes retains the exact draft/adapter/builder/test hashes.

Next fresh22/controller23 preparation must also put assets and public deployment/
policy copies under the NEW source16 root because the installed fixture checker
refuses old-root inputs. The183file tool inventory may be reserialized only as
new data with its own hash/provenance. Preserve all161original control input
records as an ordered prefix, installed0.2.4/0.2.5/artifact provenance, old native21
aliases and original key metadata until fresh strict drain and explicit scoped
preservation. Validate the installed manifest before one fresh native run.
Checkpoint115 `.scratch/web-006-source16-current-state-v115.json` SHA256ec94700ec96c4df30944ee6ccf0548f1f94ae543890692d68776d136ad03f662.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint116 update2026-10-23: fresh22 public preparation/static validator passes.

Actual executor3452960/start425596323 returns0/reaps/absent in5.838016s.
Localed7f29c8/105752bytes and protectedd1917f35/88625bytes retain the result.
Rootef377c80/123160bytes, calleraecb8213/14035bytes,26local publication/document
models/zero skips and expanded lint pass. Preflight holds20inputs plus1361actual
canonical source files,1383FDs rejoined/closed, unchanged SSHcap107441/120000.
Gate16source2da61616/7749Python/fullrequiredstages still matches; complete
local source full9 ledger27ecae43/612049bytes is retained. Two owned localgit
commands and SSH finish normally; no automatic signals or source substitution.

Fresh authority22 UUID0a1ab232-4c2c-411b-b186-90df3c5b78b7 now has21newfiles:
4private artifacts and17public fixture files, all EMPTY-label-before-bytes.
Public tree includes unchanged six built0.2.4UI assets/f09f904e, four deployment/
policy copies with unchanged hashes, semantic toolinventoryf34dfeb1, marker,
modern browser launcher70b05f87, fixed native/rootless wrappers, private-wheel
runner and manifestf8faa1e9/5020bytes. All public paths are under source16 root;
new public labelscontainer_file_t:s0, private codeusr_t. The installed original
0.2.4validator runs asUID1000: actualpython104316/start26479609 and wrapper
104315/start26479608 both close, wrapper0/reaped, manifest/package identity pass.
No browser/service execution occurs. Controller23source8c160dee changes only
CONTROL/generation/repository path assignments from actual2a2219d8; retained
primitives88b4bf39/26980bytes are an exact AST dependency closure, no guard changes.

All194borrowed public files/50dirs full9/hash/SID rejoin; all33original native21
handles freshly gone; local/guest1361source files unchanged;108readonly package
files pass before/after, releases[], five CLIcommandsclose, final13roles/
4cgroups/5endpoints strictquiescent. Old current/deployment/policy/key metadata
remain unchanged. No control23/generations23/sudoers selection, install/staging,
credentials/timers/policy changes or functional acceptance. Existing API/UI
artifact07bd818e retains pinned UBI10micro provenance/no runtimefrontend server.

Next is SEPARATE selection preparation using original controller.lock inode,
fresh strict drain and original native21 alias preservation; do not repeat this
publication. Old native/build/paired-audit/UNKNOWN receipts stay unchanged. Then
one fresh native run plus strict postrun, followed by required rootless/fault/
retirement cohorts. Checkpoint116 `.scratch/web-006-source16-current-state-v116.json` SHA2564f737e3d2917f194835fd7e988af57947477a4deeafb244b5e58f54cd090cbe0.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint117 update2026-10-23: fresh22/controller23 preparation passes.

Actual executor3455114/start425681592 returns0/reaps/absent in4.671338s.
Local48f91582/82607bytes and protected183dd930/63270bytes retain the result.
Root02e82859/30556bytes and caller6dc1411a/17390bytes pass composed lint and
15local models/zero skips, including actual owned renameat2 regular/symlink/
EEXIST and real flock tests. Local login-user lock fixtures use the existing
public-parent resolver only for unit FD semantics; the actual guest retains the
root-only private-parent rule. The initial local private-parent refusal is
preserved; no guest guard was weakened. Preflight rejoined26inputs/1361canonical
sources/1389FDs, quotedSSH20439 below120000. Actual813FD+reserved32 remains
below unchanged soft1024. Source gate16 remains unchanged/green.

Under original NONCREATING controller.lock inode43335379, visudo passes;
control23=1c98b0c2/32738bytes and generationrootv23 are created, controller8c160dee
loads exactly matching manifestf8faa1e9. All161old control inputs remain an
ordered prefix, with7new protected receipts appended. Fresh before/preservation/
final13role/4cgroup/5endpoint closure passes. Three original native21 aliases
are atomically preserved via renameat2/RENAME_NOREPLACE/rc0, no replay: selector
inode60320036, deployment78478733 and policy78478734 now under
`/opt/hfcache-web006/fixture-authority-v22-selection-v1/`. Inode/mode/owner/size/
mtime/SID and selector stringreleases/0.2.4 are retained; only recorded rename
ctime advances. All3old alias names are absent; release trees are untouched.
New scoped sudoersv22=30ada05e/221bytes is0440 and inherits oldetc_t label while
EMPTY before bytes. This is entirely inside the positively owned disposable VM.

Master-key metadata inode78157344 remains held/rejoined, no keybody/hash read.
Original lock inode rejoined/closed, releases[], all7CLIcommands0/reaped;
all1361local/guest source files,194public files/50dirs,21publication files and
108readonly package files remain unchanged. No services/timers/credentials/kernel
policy, installed version or browser execution changes. Old failed/UNKNOWN
native/build/audits remain unchanged, all21success-dependent scopes inert.

Fresh22 UUID0a1ab232-4c2c-411b-b186-90df3c5b78b7 is now prepared; next is ONE new
native functional invocation using runnera36d43a9 and manifestf8faa1e9, with
strict postrun/original-handle collection prepared first. Do not repeat this
selection or publication and do not invoke oldnative21. Rootless/negative/fault/
retirement acceptance remains pending. Checkpoint117 `.scratch/web-006-source16-current-state-v117.json` SHA2564e86e6688f6a646bdb90889e5f6298e8f4f37511e052ebd1782a8693f11b7d2a.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint118 update2026-10-23: original native22 fails; real TLS/14baseline cases pass.

Original executor3457515/start425783437 returns1/reaps/absent in98.195719s.
Localf26079e1/52429bytes and protected33d92a5a/31550bytes retain the original
failure. Actual runner104429/start26666591 returns1/reaps in96.477470s; noSUMMARY.
Caller497c2111/22971bytes and root9ba8c437/38045bytes were captured exactly.
33inputs/1361canonical sources/1396FD preflight closes, quotedSSH20675; prepared
strict postrun template253348c2 and5local entry checks/zero skips/lint pass.
Native root/local inputs all rejoin/close; original native_functional_passed=false
is explicit. Root strict before/after13roles/4cgroups/5endpoints pass, kernel45bb
unchanged. No retry/forced signal or original native21/22 replay occurred.

Separate prepared postread25b4857d/53281bytes passes0 (protected d26e7b49/29324):
original runner/5CLIidentities gone, no summary, failed outcome unmodified.
Readonly partial059b11ac/74531bytes passes0 (protected5c40a943/49413), then exact
sanitized diagnostic8d4dc87c/96674bytes passes0 (protectede5b1a165/71200).
Generationc99d52bf50dd41aabede754686d794a6/profile cleanup_unknown=false.
Before/after-negative TLSpeer CA1dbee/leafDER2b5c7f9b are equal. All THREE real
untrusted engines pass one certificate-refusal attempt each; negativeCIDfeab1207
actuallyexited0/PID0. Trusted Firefox and WebKit each pass ALL7baseline host/UI/
denial cases. Trusted Chromium completes0cases with infrastructure_failed=true.
Its actual sanitized error remains response.json/Network.getResponseBody:
"No data found for resource with given identifier" despite eager capture.
TrustedCIDc03e56bc actuallyexited1/PID0; both init/client handles/descendants
closed, no OOM/forced browser close. Original drain_or_evidence_unknown=true
at report_passed is PRESERVED; separate current closure does not rewrite it.
Helper-down/restarted/timeout and all rootless/fault cohorts were not reached.

Next is a contract-first source17 harness correction: read the real JSON reply
in browser page execution after UI navigation, keep that GET's own status/
headers/body, retain actual UI state checks and all permission/timing assertions.
No route interception, mocks, TLS ignore, capability relaxation or failed-read
retry. The extra deliberate read is safe status observation, never operation
replay. Rerun a fresh strict source gate and use a NEW fixture/authority; do not
alter source16/native22 or republish existing installed artifacts. Invariant006/
ADR113/150 review: API/UI production behavior and dependency decisions unchanged;
only the functional observation mechanism changes. API/UI artifact07bd818e keeps
original source15/pinned UBI10micro provenance. Checkpoint118 `.scratch/web-006-source16-current-state-v118.json` SHA25609911c6183d123e30bdbb992d52c2ff878af42b3a969274c5fdbb250c60dc62c.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint119 update2026-10-23: source17 browser-page capture fix; strict gate RUNNING.

Contract-first host acceptance now performs one explicit same-origin real GET
inside the browser page after UI navigation, capturing its own status/headers/
JSON together. The UI's host-state/reason checks, native Basic cache, normal TLS,
passive network observer, deadline/permission assertions and no-retry behavior
remain. No Playwright response body lookup, route interception, synthetic reply,
Node-side request fallback or operation replay is introduced. Human development/
troubleshooting guidance explains the tooling failure and safe new-fixture path.
14Node checks pass/zero skips, including owned actualHTTP200/403 identity/body,
invalidJSON single-read failure and no Node fallback. ESLint/Prettier pass.
INV006/ADR113/150 review: no server behavior, UI source, invariant or dependency
change; known authorization exit10 stays intact. All108API/27UI bytes remain
unchanged from source16/15, so existing0.2.4/0.2.5 artifacts keep original
source15 provenance/pinned UBI10micro base; no rebuild/reinstall/restaging.

Frozen canonical source17 contains1361files/snapshot3b146543. Exactly four deltas
from source16: driver.mjs/driver.test.mjs and human development/troubleshooting
docs; modes/membership unchanged. Inventory0c87de18/244519bytes, tar54b3f82d/
17725440bytes, capture8a7f72f8/684bytes. Capture executor3461542/start425910035
returns0/reaps/absent; an earlier wrong-hash wrapper request refused before any
process/locator/artifact, then the observed exact source hash54b83d24 was used.
Original source16/native22 data are untouched. The new public GET is planned
observation; failure ends the invocation, with no subsequent failed-read retry.

Actual strict gate17 `scripts/check.sh --require-web --require-cockpit` is RUNNING:
outer3461656/start425913683, gate3461657/start425913701, session56166;
runnerdcb85031/6619bytes, start21:23:15.171660Z, log `.scratch/web-006-gate17.log`.
No PASS is claimed. Source17 fixture projection template9d6412b8 remains INERT
with gate/log pinsNone. Pure twoTOML model changes only copied pyproject/uv-lock
version0.2.2->0.2.4, predicts snapshotcb64ae60, revalidates all1361canonical bytes;
it is not a guest copy, installation or acceptance. Next: wait on THIS gate;
after actual PASS/unchanged source, bind projection, transfer NEW source17 and
prepare NEW authority23/control24. Native22 must never be rerun/promoted.
Current aliases were absent at fresh22 preparation; native22 activation has
since run. Fresh actual metadata is required before any new preservation.
Checkpoint119 `.scratch/web-006-source17-current-state-v119.json` SHA2564dbd6fa228925f650095670d522a4524fa05dbd35c04553e4c722d53c7fd4db3.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint120 update2026-10-23: actual source17 strict gate and local preparation PASS.

Original gate17 exits0 after1246.827779s at21:44:01.999420Z:7749Python,
52opt-in deselections, three locked wheel profiles, preserved Cockpit checks,
2786frontend unit and2846component tests, production build, two sandboxed
Chromium startup checks and real React/API read fixture all pass. Required
frontend checks report no skips. Gate3461657/start425913701 and outer3461656/
start425913683 are reaped/absent. Gate resulte3100b94/816bytes, log4204e849/
100870bytes, wrapper5d1a3c37/738bytes. All1361frozen source hashes/modes remain
unchanged, snapshot3b146543; no installed host acceptance follows from this gate.

Bound source17 fixture metadata projectionfa1990dc/21291bytes executes ONCE,
3480555/start426043376, returns0/reaps/absent after5.419822s. Projection0a8f4d85/
260485bytes changes only copied pyproject.project.version and uv-lock self
version0.2.2->0.2.4; fixture snapshotcb64ae60/all1361files verified. Canonical
product0.2.2,108API/27UI sources and original artifact provenance stay unchanged.
Packet builder0cf7a0fd/8067bytes executes ONCE,3480679/start426046909,
returns0/reaps/absent after1.340060s; its13member packet and exact gate channels
validate locally. No source17 guest copy, build, install, authority selection
or real functional acceptance has run. Old source16/native22 failed/UNKNOWN
records and handles remain unchanged. Next: NEW source17 transfer and protected
preparation, then NEW authority23/control24 after fresh current-alias metadata.
Checkpoint120 `.scratch/web-006-source17-current-state-v120.json` SHA256917354a2b1d65cbc874e6d4a9772c504f66017f8cfef386a2a4fea906fb49825.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint121 update2026-10-23: source17 new guest tree copied and verified.

Original transfer769d860c/10299bytes FAIL1 remains preserved. Both status-query
processes106170/start26957817 and106171/start26957832 exit0/reap; saving private
channels failed before WORK creation. No public or protected packet member was
copied. Failure root JSON8d6cc21a/1634bytes is retained separately; its invocation
3481425/start426074594 returns1/reaps/absent. No original operation is replayed.
The corrected separate completion creates its NEW protected diagnostic scope
before any status query, saves the original failure unchanged, verifies both
original identities gone and uses the same held packet only for its first copy.
17local models/preflight PASS, E9/F821 PASS, all1361current source plus13inputs/
1376FDs rejoin; SSH18554bytes below120000. A malformed local hash argument refused
before process/locator creation; the exact observed64hex hash then executes.

Separate completionee425ff3/952452bytes PASS0, protected1213097d/897849bytes at
`/opt/hfcache-web006/source17-fixture-transfer-completion-v1/RESULT.json`.
Caller49c449e1/13942bytes, rootef6f84ba/53234bytes; actual3481712/start426082882
returns0/reaps/absent after19.027359s. All1361new source17 files verify full9/
hash/mode/SID, fixture snapshotcb64ae60, source snapshot3b146543. Files are labelled
usr_t while empty before bytes. All1361oldsource16 files retain full9/hash/SID
before/after/finally; current native22 aliases and metadata-only key are unchanged.
Strict13role/4cgroup/5endpoint closure and four queries0/reaped pass. The original
failed native22 remains failed. No build/install/restage/new authority/browser or
functional acceptance is claimed. Next: new readonly package projection and
prelabelled public browser inputs, then authority23/control24.
Checkpoint121 `.scratch/web-006-source17-current-state-v121.json` SHA25620209875415c4e2b8f443da7ffb4eee01034dab95ac66530e00ffab12575b728.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint122 update2026-10-23: new source17 environment and separate installed static validation PASS.

Environment8d9386ea/334987bytes PASS0, protected840fab68/310938bytes. Actual
3482454/start426110370 returns0/reaps/absent after9.119465s. Direct mount(2)
creates a NEW readonly projection preserving all108package inode/hash/SIDs,
UID1000 import passes.194new browser files/50dirs are labelled empty before
bytes;194old files/50dirs remain full9/hash/SID unchanged. Seven source17 code
files and inventorybc8787d4 selected, current CA1dbee retained. FD774+32<1024,
limits unchanged; all1361source17 files before/after/finally and strict closure
pass. Local environment models/preflight and E9/F821 pass.

Fresh23/controller24 public preparationc3eb8c13/101946bytes FAIL1 preserved,
protectedeb38c9f6/85639bytes. Actual3483129/start426132810 returns1/reaps/absent
after4.593230s;21new files published/manifest0ae5c2d2/5020bytes, static validator
returns1. All roles close; source17 unchanged, old selection unchanged. Saved
validator readf68d368e/40900bytes PASS0 (protectedbe00b339/30091): actual failure
is the fixture's .scratch mode0755 rather than required current-user-private0700.
No runtime/security contract is relaxed. Launcher8e97ea6d binds actual194/50
records/new driver; every launch/TLS/drain function AST is identical to source16.
Documents71a760b5 fixes the inert inventory lookup v16->v17 before publication;
all168control inputs remain preserved in pure models. Required guest proof is
still separate from these model passes.

Separate completion60b73cbe/51654bytes PASS0, protected925c9db1/40194bytes at
`/opt/hfcache-web006/fixture-authority-v23-completion-v1/RESULT.json`.
Actual3483966/start426161426 returns0/reaps/absent after5.447450s; caller0ba59805/
12328bytes, root2996fe09/35377bytes. Only owned .scratch mode0755->0700 and ctime
change; original inode/owner/SID/entries preserved. All21published files and
194browser files/50dirs stay unchanged. The installed UID1000 validator106392/
start27044658 passes, wrapper106391/start27044657 returns0/reaps, both identities
gone. All108readonly package files and1361source17 files remain unchanged;
FD815+32<1024, five queries/validator processes0/reaped and strict13/4/5closure
pass. Original publication remains FAILED; this is a new correction/validation
receipt, not its promotion or a publication replay. No control24/sudoers/selector
change or browser/app-service execution yet. Next: locked control24 preparation,
preserve fresh native22 aliases and prepare native23/strict postrun before run.
Checkpoint122 `.scratch/web-006-source17-current-state-v122.json` SHA256dfd20b6b49eece268ac03e32ddbe92e9e70c559b2f417cbb7659fe9d8ab730fa.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint123 update2026-10-23: control24 preparation PASS; ORIGINAL native23 RUNNING.

Selection30ffcff6/75417bytes PASS0 (protected2dabc4bd/60041bytes), actual3484814/
start426191646 returns0/reaps/absent after4.887578s. Control24 SHA256e27358e6/
34151bytes inode43477818 preserves all168prior inputs plus8new protected records
(total176). Controller24 actual load_control equality and visudo pass; scoped
sudoers v23 and generations24 prepared. Original noncreating lock43335379 and
metadata-only key78157344 stay unchanged. Three native22 aliases are preserved
with renameat2 NOREPLACE under fixture-authority-v23-selection-v1/native22-*:
selector60372219, deployment78518898, policy78518899, all original SID/inodes/
mtime preserved; only ctime advances. Seven CLI processes0/reaped, strict13/4/5
closure,108readonly package and1361source17/borrowed public files unchanged.
FD815+32<1024. Fifteen actual local rename/lock/refusal tests PASS, E9/F821 PASS.
First local preflight fails its FD count because ctypes initializes after the
baseline; no guest call/selector action. New preflight initializes library first,
then all held sources/FDs rejoin/close and passes; original failure retained.

New native23 rootf88566e4/38747bytes binds authority23/control24/manifest0ae5c2d2,
unchanged checker7af9b0ba and runner9a5e43f7. New callerbbdeb6b8/14732bytes and
strict post template3849e61f/21144bytes are bound BEFORE execution. Post remains
NATIVE_PIN=None until actual receipt, correctly targets generations24; earlier
unused v1draft stays INERT. Six local runner/post tests PASS and held preflight
passes1361current source files+20inputs, actual prior wrapper/channels/protected
selection hash, unchanged source gate17 and exact QEMU/SSH identity. No failed
native21/22 invocation is retried or promoted.

ORIGINAL native23 starts ONCE:3485500/start426215529, session56962, stem
`.scratch/web-006-original-native-functional-source17-authority23-v1-execution`.
It is RUNNING; no PASS/result/functional acceptance claimed. Root runner budget
1800s, owned SSH budget2100s, original EOF/reap/no automatic kill preserved.
Only this original invocation owns the guest lane until exit. Current aliases
were absent after selection preparation; native23 may activate NEW aliases, so
fresh actual metadata is required later. Next: wait on THIS session, preserve
actual outcome, bind prepared strict postrun to its exact receipt. Native/rootless
isolation, remaining faults/retirement acceptance stay incomplete.
Checkpoint123 `.scratch/web-006-source17-current-state-v123.json` SHA25681c36c38f4ff31d6d35746033a0bc111535acd52383f1a785a46b0a6b629e258.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint124 update2026-10-23: ORIGINAL native23 and strict postrun PASS.

Native23e14ab38f/45644bytes PASS0, protectedb4ffc5c7/31543bytes. Actual3485500/
start426215529 returns0/reaps/absent after331.488119s; runner106479/start27098665
returns0/reaps after329.706514s. Original checker7af9b0ba and fixture0.2.4 installed
API execute built UI -> SAME real Caddy with current trusted TLS. All four modes
baseline/helper-down/restarted/timeout complete; SUMMARY exists, no required
skips/retries. Native21/22 failures and UNKNOWNs remain unchanged; no replay.

Prepared strict postrun binds ONLY this actual receipt: rootbce1020f/21328bytes,
caller11621499/11967bytes. Held1361source/14input preflight and E9/F821 PASS.
Actual3486717/start426258619 returns0/reaps/absent after2.633729s; collection
 a365464c/86696bytes PASS0, protected7dc92b2a/72974bytes. Generation
`ece999e6efd342a3882aba73b3e45574`, stateb6fcec6c/58016bytes under generations24;
SUMMARY110d414f/383168bytes. All THREE engines pass7baseline+2helper-down+
1restart+1timeout cases (33host/UI assertions total), one attempt each. Every
mode's three untrusted engines also refuse the SAME Caddy/current CA once
(12certificate refusals total), and before/middle/after TLS epochs agree.
No TLS ignore, mock, failed-read retry or forced browser close is used.

All8exact trusted/untrusted CIDs actually inspect as exited0/PID0/notOOM;
original init/client identities closed. All43generation application processes,
original runner and5top-level CLI identities are gone; strict13role/4cgroup/
5endpoint closure passes. Original summary/profile cleanup_unknown=false;
no required skip or retry. This establishes the native23 browser cohort only.
Rootless, dedicated peer/role/secret isolation, supplemental faults, exact secret
ownership/retirement and full WEB006 acceptance remain pending. Current aliases
can now reflect native23 activation; use fresh actual state before later changes.

Inert normal23 prerequisiteaf8f71fa/16917bytes was derived locally from reviewed
normal21 code with actual selection schema/source17 paths; future generation/
record pins remain UNBOUND until this PASS is adopted. Old21 successor templates
remain permanently inert and unmodified. Next: bind actual native23 normal
proof, then rootless baseline/live ownership watcher/one original rootless run,
followed by required isolation/fault/lifecycle cohorts. The shared API/UI image
keeps original source15/pinned UBI10micro provenance; no rebuild/reinstall/restage.
Checkpoint124 `.scratch/web-006-source17-current-state-v124.json` SHA256752bfa44bae411bb625927f0fb272aa38b588442d2ffd0933de22b52bd03908e.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint125 update2026-10-23: native23 normal prerequisite and EMPTY stock983 baseline PASS.

Normal publicatione0afb9a0/55700bytes PASS0, protected598fe2b0/43329bytes.
Actual3487932/start426307931 returns0/reaps/absent after3.987100s; root6251a9ec/
52077bytes, caller64747ee5/12832bytes. Bound common code9c67021d/18099bytes
is private root0600/usr_t at private-normal-code-source17-authority23-v1/
normal-readiness.py (inode78600735), labelled empty before bytes. It revalidates
actual seven native result/SUMMARY/generation/control/authority/manifest/checker
records,33browser cases and protected delivery/hygiene metadata. Public SAFE
projection2e587711/5167bytes is container_file_t:s0, labelled before bytes.
All48native app/CLI identities are freshly gone,1361source17 files unchanged
before/after/finally, four status queries0/reaped and strict13/4/5closure pass.
Eight local binding models/held1361source15input preflight and lint PASS. Old21
successors remain inert; existing source15 runtime artifacts keep provenance.

NEW rootless23 metadata baseline5c92dbcd/31883bytes PASS0, protecteddabc9574/
15832bytes at rootless-secret-baseline-source17-authority23-normal-v1/RESULT.json.
Its protected serialization is COMPACT sort_keys JSON+newline, not indent2.
Actual3488631/start426334160 returns0/reaps/absent after1.414381s; caller0d118511/
13030bytes, rooteef9f963/40744bytes. The native parser now accepts EXACTLY its
actual two additional strict pre/post guard fields and independently verifies
13inactive units,4empty cgroups,5refused endpoints for each; no field is dropped
or inferred. Eight local actual-receipt/hostile guard/pause tests and held1361
source15input preflight/lint PASS before execution.

Stock UID983 secret listing is EMPTY: count0/unknown0/no rows, complete safe
store metadata before==after, no new/missing/changed paths or engine-created
store. Pause70549/start6647855/UIDGID983 remains user:[4026532304]/mnt:[4026532305].
All13roles are quiescent before/after; five metadata/status CLI children return0/
reap, kernel45bb unchanged. No payload body/digest, key or credential is read;
no explicit secret creation/removal/replacement/store write, ownership grant,
retirement or application start occurs. The next required step is a NEW live
ownership watcher armed before ONE original rootless generation. Actual six-ID/
three-CID ownership, rootless browsers, strict postrun, dedicated isolation/fault
and exact-ID retirement remain unaccepted. Native23 acceptance stays preserved.
Checkpoint125 `.scratch/web-006-source17-current-state-v125.json` SHA256142c2594df1550c2f4b1acd036a5da43c173aff13eb691f539bf5063cddb0eb3.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint126 update2026-10-23: NEW original paired rootless23 coordinator RUNNING.

New observerb5da1ead/52075bytes adapts actual selection23/control24/empty compact
baseline dabc9574 and pause70549. Protected ARMEd metadata is fully written and
fsynced before atomic renameat2 NOREPLACE publishes ARMED.json; four real local
filesystem tests PASS for complete inode-preserving handoff, existing/missing
source/destination and non-directory refusal. No existing file is overwritten.
Earlier unused observer0381a389 remains inert. Original runner templateeae39529/
37482bytes preserves its methods except explicit current authority schema/path/
source bindings; ARMED_SHA256/WATCHER_SHA stay UNBOUND until actual live handoff.

Coordinatoraa1a4f26/129948bytes owns BOTH original children under one guest call.
It requires actual native23 PASS and empty baseline, starts the metadata-only
observer, holds/verifies live PID/start/source hash and atomic ARMED record, then
binds exactly two runner assignments and starts ONE original rootless runner.
Both children use captured verified code; no file-loader reopen, credential
payload collection, replay, automatic signal or secret retirement. Primary errors
survive cleanup; real EOF/reap of both children precedes publication on every
entry path. Eight local coordinator tests PASS: actual child early-EOF/late-exit,
overflow drained/reaped without signals, first entry error retained while the
same child drains, and exact two-field/runtime-pin validation. Lint PASS.

Prepared readonly postrund8c25d0f/91397bytes remains COORDINATOR_PIN=None until
actual result. It checks all4modes/3engines,8exact browser CIDs,3live-owned app
CIDs,6original secret IDs, original process/pause closure and strict13/4/5guards;
no app start/secret body/digest/retirement. Current native23 acceptance stays
preserved; dedicated isolation/fault/exact-ID lifecycle acceptance stays pending.

Caller e4340ac0/14475bytes captures current1361source files plus18pinned inputs,
actual compact baseline/executor/channels, observer/runner templates and prepared
postrun. Local preflight0df73814 PASS0/reaped/closed, four binding checks, guest0;
all prior source/gate/QEMU/SSH proofs rejoin. Owned SSH budget2100s; runner1850s/
watcher2050s owners retain original EOF/reap, without automatic kill.
ORIGINAL paired invocation starts ONCE:3492279/start426492665, session92181,
stem `.scratch/web-006-rootless23-coordinator-v1-execution`. It is RUNNING;
no rootless functional PASS/result/acceptance claimed. Only this coordinator
owns the guest lane until all original children close. Next: wait on THIS session,
preserve outcome and bind its prepared strict postrun; never rerun the cohort.
Checkpoint126 `.scratch/web-006-source17-current-state-v126.json` SHA2566c0084b36350eb34b1169db85a9bff98dccdfa24ae43a5656c5404a58a3ef021.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint127 update2026-10-23: first coordinator setup FAIL preserved; corrected setup RUNNING.

Original coordinator-v1e99a3df9/43706bytes FAIL1, protected7feac8d4/30579bytes.
Actual3492279/start426492665 returns1/reaps/absent after1.433398s. Observer111937/
start27375775 exits1/reaps; no original_runner entry, ARMED or application launch.
Five original children are gone, strict13/4/5closure passes. Saved observer
stderr93587b23/722bytes is retained. Separate readonly diagnostic355c5f6d/
41209bytes PASS0, protectedd44a924b/30304bytes;3492874/start426515637 returns0/
reaps/absent after1.199847s. It confirms missing path fixture-authority-v23/
RESULT.json: the actual authority is fixture-authority-v23-selection-v1/RESULT.json.
Observer work/ARMED and original rootless runner work are actually ABSENT.
No rootless application operation was invoked, no failed invocation is replayed.

New observer65b3d375/52084bytes and runner28f35c3d/37491bytes bind the authority
path by AST assignment to the actual receipt, replacing fragile literal matching.
New coordinator781a7db3/131044bytes pins original failure+diagnostic and requires
that failed setup had no runner and diagnostic observed absent scopes before
proceeding. Old v1 and its handles/false flags stay unchanged. Nine corrected
local lifecycle/path tests PASS, including both paths/hashes against actual
selected receipt; previous four real atomic handoff tests remain PASS. Lint PASS.
Prepared post636a5fd0/91408bytes stays unbound for coordinator-v2 only.

Caller60a1fd83/17927bytes pins28inputs/current1361files, actual empty compact
baseline, failed setup and saved diagnostic execution/channels/protected hashes,
new observer/runner and prepared post. Preflightb7eca9ed PASS0/reaped/closed,
no guest call; all held source/gate/QEMU/SSH and fields rejoin. Corrected setup
starts ONCE as3493718/start426548196, session50231, stem
`.scratch/web-006-rootless23-coordinator-v2-execution`; currently RUNNING.
No corrected result/rootless PASS/acceptance or secret retirement is claimed.
Only this call owns the guest lane until both original children close. It can
launch the FIRST actual rootless23 application invocation only after a valid
live atomic ARMED handoff. Next: wait on THIS invocation, preserve outcome,
bind the already prepared strict postrun to its actual result. Required dedicated
isolation/fault/exact-ID lifecycle evidence remains pending; native23 stays accepted.
Checkpoint127 `.scratch/web-006-source17-current-state-v127.json` SHA2561f64a73d90d33962a5859905eb3d092248a95ca431e6a782c445c2406deea3d1.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint128 update2026-10-23: corrected coordinator and FIRST rootless run FAIL; closed diagnostics isolate a fixture empty-list parser defect.

Original corrected coordinator-v2 local68298c55/67485bytes, protectedf5b9b8de/
48201bytes FAIL1;3493718/start426548196 returns1/reaps/absent after5.790317s.
Atomic ARMED99fd55eb succeeded with live watcher112027/start27431305, then
FIRST rootless driver112028/start27431325 and functional child112032/
start27431352 returned1/reaped. No invocation is replayed. Generation41b7055e
is stopped=true/started=false/containers=[], six tracked processes gone.
Observer exited0 but explicitly records successful_ownership_proof=false,
all_sources_closed=false/error_class=ValueError; payload-read/digest field UNKNOWN
is retained. No ownership or secret retirement is inferred from its exit code.
The missing SUMMARY caused a secondary FileNotFoundError; primary startup refusal
is preserved independently. All coordinator/driver children are gone and strict
13role/4cgroup/5endpoint closure passes.

Separate readonly original-run diagnostic269ea27c/protectedd1287fe0 PASS0.
Boundary read e15ecaa6/43385bytes/protectedc0c5ba68/32340bytes PASS0;
3495076/start426604772 returns0/reaps/absent after1.268161s. Certificate
prestart phase=passed, public inputs closed, more than515708seconds remaining;
no expired-TLS failure. No service-start or secret-label gate was reached.
Six original generation PIDs freshly gone; workspace filename metadata retained.

A NEW readonly exact engine-list probe54f978a5/43504bytes/protected0349e321/
31452bytes FAILs with JSONDecodeError after actual metadata child112266/
start27523599 returns0/reaps with stdout ZERO bytes and empty stderr. Its
execve UID/GID983, empty supplementary groups, cwd / and environment match the
executed controller. This reproduces the fixture's unconditional json.loads on
empty stock Podman secret-list output. Outer3496008/start426640503 returns1/
reaps/absent after1.371944s; strict closure still passes. Empty output alone is
not a complete current ownership/store proof. No payload body/digest or secret
retirement occurred. Original failure remains failed. A local builder syntax
error and malformed wrapper arguments were refused before any guest action;
corrected finite reader artifacts are separately preserved.

Next: guarded correction in a NEW controller/authority scope, actual empty-store
metadata proof, fresh live ownership watcher, ONE new rootless generation and
its strict postrun; required dedicated isolation/fault/exact-ID lifecycle proof
remains pending. Source17 canonical1361files/gate17 and native23 PASS remain
unchanged. All earlier failures/UNKNOWNs/handles are retained. Shared shipped
API/UI image remains pinned UBI10micro. No production/NAS/live Cockpit changes.
Checkpoint128 `.scratch/web-006-source17-current-state-v128.json` SHA256f2b71a1e9f3476d7ac84e25015d64cdc74e8e19828965ba080d261cefa91b5b5.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted.

WEB-006 checkpoint129 update2026-10-23: fixture controller25 corrected; NEW authority24/current baseline PASS; rootless24 RUNNING ONCE.

Controller99bfb5ee/112373bytes adds bounded require_empty_secret_listing:
only actual zero-byte successful stdout or explicit JSON [] is empty; malformed,
null/object/nonempty output remains refused before creation. Only credential
parse and control25/generations25 assignments differ; original start/stop,
bootstrap, permissions and bounded process ownership are unchanged. Eighteen
regression tests PASS. New launcher0410b08c/98829bytes changes only manifest path.
No canonical product source/runtime byte changes, rebuild/reinstall/restage or
policy/security relaxation. All1361source17files remain frozen/gate17 PASS.

New authority24 first preparationa502d304/82592bytes FAIL1 (3497095/
start426678468/reaped/gone4.795255s), protected145ae862/65322bytes.
Actual installed static validator and controller load pass; a missing DOCUMENTS
reference stops before the first preservation intent/rename or sudoers activation.
Original failure stays failed. Separate completion actually completes preservation
of all3rootless23 aliases by NOREPLACE, same inodes/SIDs/mtime (ctime only),
new fixed sudoers and full8published-record/194public-file/50directory/108ROpackage
proof, used778+32FDs<1024, strict closure. Protected completion57106dba/60192bytes
PASS; outer3497427/start426688956 exits1/reaped/gone5.544738s because the local
classifier wrongly requires an absent error_class key. Its local KeyError/false
flags remain unchanged. No completed action is replayed.

Separate readonly admission2b26c631/50111bytes/protectedd708f95e/32780bytes PASS0:
3497820/start426701252/reaped/gone1.400888s. It rejoins all8published inodes,
new control25c2b3d244/35384bytes, controller/manifestaa1c02f5/5019bytes, original
noncreating lock and key METADATA ONLY; controller load equals captured documents,
original176control inputs preserved in order, generations25 empty, aliases absent
and preserved identities exact, all completion processes gone and strict13/4/5
closure. This independent admission establishes new readiness, never promotes
original failed preparation or local classifier. Fixture UUID749bc2aa-bd29-41c4-
9e33-18c5940cda71. No application service/container or secret payload operation.

NEW stock983 baselineaf147ae0/33173bytes/protectedaa4bc19b/16058bytes PASS0:
3498010/start426706785/reaped/gone1.452087s. EMPTY0secrets/unknown0, complete safe
store metadata unchanged/no created paths, same pause70549/start6647855/userns
4026532304/mntns4026532305, all13roles quiescent. Original native23 prerequisites
remain independently bound; fresh authority24 admission also held/closed. No
payload body/digest, key, credentials, ownership/retirement or application start.
Protected baseline serialization is compact sort_keys JSON+newline.

New observer906d3d6d/45883bytes and runnerd593dbd9/34624bytes bind new authority,
workspace, baseline/control/controller and UUID; exact atomic ARMED and original
EOF/reap lifetimes remain. Runner borrows unchanged old public run-host-fixture-v1
wrapper while passing explicit NEW manifest; no nonexistent new wrapper assumed.
Coordinatorv1 local tests found stale absolute receipt paths; preflight found an
old execution basename. Both were refused before guest action and remain inert.
New coordinatorv2defe919e/52126bytes binds all exact current paths. Twenty-eight
local parser/child lifetime/runtime-pin/current-receipt tests PASS3.85s; lint and
held1361source/30input preflight PASS (quoted SSH42699bytes<120000). Prepared
post203e30d0 remains unbound/inert and still needs full current-field review.

Original NEW rootless24 coordinator starts ONCE as3498897/start426734374,
session83865, callerc3b5a8e6/18534bytes; currently RUNNING. Only this call owns
the guest lane. Fresh live atomic ARMED precedes ONE new generation; two runtime
pins only, no replay of original23 operations, no automatic signals/retirement.
Next: wait on THIS invocation, preserve outcome and bind/review strict postrun;
dedicated isolation/fault/exact-ID lifecycle acceptance remains pending.
Checkpoint129 `.scratch/web-006-source17-current-state-v129.json` SHA256437d8573246b0f6c581e698f95a0ba4dbbe7d9df5399643ff5fa223cea5c5132.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint130 update2026-10-23: rootless24 FAIL; real installed mount prerequisite identified. Checkpoint129 RUNNING wording was already stale when saved; this corrects that bookkeeping error.

Original coordinator3f7c902c/57261bytes/protected36590fa0/37552bytes FAIL1;
3498897/start426734374 returns1/reaps/absent8.509060s. Atomic ARMED735e87e3
was live and matched fresh empty baseline, watcher112488/start27617477/runner
112489/start27617499 and original functional child112493/start27617530 all
closed. New generatione5ce5fef49254d1791ede5ca5eedb207/control25 started=true,
stopped=true, containers=[], all17recorded processes freshly gone. Its original
prestart secret gate PASSED8actual inode/kernel read-open denials, kernel45bb
unchanged, sequence47. No delivered gate/browser/feature acceptance follows.
Observer ownership=false/all_sources_closed=false/ValueError; payload-read/hash
UNKNOWN remains UNKNOWN. Six created fixture secrets remain preserved; no
retirement is authorized by a matching name or this failed observer.

Separate readonly failure diagnosticd80a0ea1/67918bytes/protected306e3bed/
48609bytes PASS0;3499681/start426759829/reaped/gone1.204860s. All original
coordinator identities and17generation PIDs gone. Worker/caddy user units remain
FAILED (MainPID=ControlPID0, no active cgroups), so strict13role/4cgroup/5endpoint
closure does NOT PASS. No reset-failed/stop replay or hidden acceptance. Worker
InvocationID6f4f288c41ed48098dc8c3a6f66c9a93/ExecMainPID112647/status20;
Caddy4181e0ce36dc493191411cdaeb7eb8f3/112649/status125. Generationdceba6fa/
14636bytes and original stop evidence preserve all17gone, empty recordedgroups/
containers and four refused rootless helper/API/worker/TLS endpoints.

Readonly saved journal+fixed-container queryf0af7ae6/61857bytes/protectedaf6f99d0/
41974bytes PASS0;3500166/start426776007/reaped/gone1.411618s. No fixed app
containers exist. Bounded UID983 original startup window: worker reports fixed
container-boundary refusal; API dependency fails; Caddy then reports missing
/run/hfcache/api and exits125. Raw channels were privately labelled before bytes;
public projection suppresses private-key/password markers and long/authorization
values. Failed first readerTypeError (unsupported collect keyword) and earlier
inert/missing-entry/shadowed-scope/refused-argument diagnostic attempts remain
preserved; no application invocation was replayed by any read.

Actual captured INSTALLED0.2.5 container-service.py8a692faa/47743bytes was run
through read-only preflight at UIDGID983: profile load and exact worker command
construction PASS; archive_readonly() raises RuntimeError with the exact known
read-only NAS mount barrier unavailable message. No prepare_start, container
exec/start/drain, service action, archive content or secret access occurs.
Receiptb5e63156/50738bytes/protected386f2ccd/30478bytes PASS0;3500768/
start426796800/reaped/gone1.289944s. rpc.nfsd and exportfs already exist; no NFS
client/server filesystem registered, and no package/module/mount action occurred.
This confirms XFS synthetic storage cannot satisfy the unchanged production
worker's real read-only NFS prerequisite. Bypassing that guard would be invalid.

Next authorized environment work: prepare a separately recorded owned LOOPBACK
NFS export of synthetic guest data, without accessing any external NAS or
weakening the product mount guard/SELinux/systemd constraints. Before effects,
prove exact existing mount/server/listener/process/secret ownership and preserve
all old fixture inputs/evidence. New private fixture guards may admit ONLY that
proved localhost export/mount and continue refusing every external/unknown
network/shared mount. Do not reinterpret earlier XFS/native evidence as NFS or
production acceptance. Preserve the original pause and namespaces; verify both
host and pause mount views before any future application generation. The six
failed-cohort secret IDs need separate conservative ownership review before any
retirement. No old run/stop/start is replayed, no service reset silently clears
failed evidence, and no current rootless normal/negative/lifecycle PASS exists.
Checkpoint130 `.scratch/web-006-source17-current-state-v130.json` SHA256cf92501042317220218c73335591b43318e0a0819f1b1c53cb565f040d97db50.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; source17/native23 PASS retained; production/NAS/live Cockpit untouched.

WEB-006 checkpoint131 update2026-10-23: owned loopback NFS prerequisites measured; no server/export/mount/module effect yet.

Readonly inventory4e1080b2/53157bytes/protected75a314bf/31818bytes PASS0,
3501850/start426834691/reaped/gone1.215379s. Matching kernel6.12.0-275 modules
nfs.ko.xz and nfsd.ko.xz exist. NFS-server/mountd/rpcbind service/socket are
inactive with zero processes/cgroups; ports111/2049/20048/32048/32049 unused.
/etc/exports is the original empty inode16908571; etab/rmtab/state are absent.
Installed utility help is captured; exportfs does not support --help and its
usage refusal is retained, not silently treated as a successful help option.
First two inventory readers refused an assumed read-only pause mount; their
failed receipts remain. Corrected observational reader preserves raw mount rows.

Host /srv/hfcache is XFS535/shared:1 on the owned archive-seed, flags
ro,nosuid,nodev,noexec. Original pause70549/start6647855/mnt:[4026532305] sees
XFS536/master:1 with RW,relatime. This second real fixture defect is not accepted
as rootless read-only archive proof. Do not repeat a bind-then-remount sequence
that can propagate a writable initial mount; require read-only NFS at creation
and actual proof in BOTH host and original pause namespaces before any app run.
The original XFS inodes/views remain preserved and no archive contents were read.

Readonly label/tool preflightacf6a4c6/26021bytes/protectedd52ab871/5193bytes
PASS0,3502284/start426850413/reaped/gone0.783961s. Existing SELinux booleans
nfs_export_all_ro=on/nfs_export_all_rw=on are measured, NOT changed. No SELinux
boolean/type/policy relaxation is authorized. Original synthetic seed root
inode118335700/root0:0/0755/hfcache_archive_t is unchanged. Four actual installed
NFS utility binaries have full9/hash/SID pins; no package install is needed.

Next private fixture preparation may load those existing vendor NFS modules,
create ONE explicitly localhost-only read-only export of the owned synthetic
seed, run separately named owned NFS test-tool units and mount its NFSv4 view
with read-only/nosuid/nodev/noexec flags at creation. Require original export/
listener absence, utility/source/namespace identity, exact localhost endpoint,
unchanged kernel policy/booleans and original borrowed inputs. Preserve the old
XFS mount and all failed application/unit/secret evidence. Probe a NEW owned
client mount before selecting /srv/hfcache; require actual host+pause NFS-ro
views and bounded UID983 denial. Do not start any application or change/reset
its failed units or retire secrets in that preparation. All external/unknown
NAS/shared mounts remain refused; no synthetic result establishes production
NAS acceptance. Record every effect/handle and partial failure without replay.
Checkpoint131 `.scratch/web-006-source17-current-state-v131.json` SHA256fa697e734e096284e9a0d5c58b837e0925bcbedf113c8faa0cebac8c5b6f761c.
WEB-006/AUTH-08/HOST-01–03 incomplete; source17/native23 PASS retained; no production/NAS/live Cockpit changes.

WEB-006 checkpoint132 update2026-10-23: localhost NFS preparation failed with partial owned effects; exact original export independently reconciled, no replay.

Vendor unit read3a9b1aba/29527bytes/protectedbc9175cc/8589bytes PASS0;
3502874/start426873086/reaped/gone0.784624s. Default root NFS service security
properties are retained; new independently named test tools will compare all
security fields against the actual vendor units, with no removal of confinement.
Nineteen export-client/RO/squash/unknown-state/actual failed-unit preservation
tests PASS1.62s; lint and held1361source39input preflight PASS. An initial local
preflight expected37inputs and refused before guest action; corrected count39.

Actual original server preparation066f3845/70554bytes/protectedd8f523ac/
45778bytes FAIL1:3503743/start426906169/reaped/gone3.044682s. Exact vendor
modules nfsd/nfs loaded successfully and NFSD control mount created (three0
children); original exportfs returns1. The recipe stops before any mountd/NFSD
unit, client mount, archive projection, app/unit reset or secret action. All
phase/intent/channel records retained under /opt/hfcache-web006/loopback-nfs-v1.
Original failure remains failed; never rerun these effects on an empty-baseline
assumption. No app/source/image/SELinux/boolean or hardening change occurs.

Separate readonly diagnosticaa99e4ea/44030bytes/protected85fcc83c/19693bytes
PASS0,3504029/start426915997/reaped/gone1.045603s, all original CLI identities
gone. Saved export stderr says it could not open previously absent etab for
reading. Despite return1, the original effect DID publish exactly one export:
owned archive-seed ->127.0.0.1, ro/sync/secure/root_squash/no_subtree_check/fsid0.
Do NOT replay it. New etab inode10403883/root0644/var_lib_nfs_t/229bytes is
captured as metadata; original empty /etc/exports inode16908571 unchanged,
rmtab/state still absent. NFSD threads0; control mount760/0:55/shared621 at
/proc/fs/nfsd. Kernel policy45bb unchanged. Application failed states/secrets
remain retained and no NFS client mount exists.

Next: separately versioned completion must hold original failure+readonly
reconciliation, verify the exact current export/etab/control/module/source/
namespace/security inputs, and adopt ONLY that already observed original effect.
It may start the first separately named mountd/NFSD tools with bounded exact
localhost listener proof; no export replay, app action, client mount or secret
retirement. Subsequent client/host/pause RO validation and fresh authority,
rootless browser/isolation/fault/lifecycle acceptance remain necessary.
Checkpoint132 `.scratch/web-006-source17-current-state-v132.json` SHA2569e83833cc57cdc9921ef3ebcd139ab5d79558715d4e6518b97df48e7ed6203e1.
WEB-006/AUTH-08/HOST-01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint133 update2026-10-23: first owned mountd is live; separate completion metadata parser FAIL preserved, NFSD/client mount not started.

Twenty-nine local export/adoption/original-failure preservation tests PASS3.06s;
lint and held1361source43input preflight PASS. Separate completion6e1e309d/
75130bytes/protected55061cac/48071bytes FAIL1,3504636/start426937929 returns1/
reaps/gone2.566078s. It adopts the independently observed original localhost
RO export without reloading modules, remounting control or replaying exportfs.
First ONLY tool effect start-owned-mountd returns0. Actual independently named
unit web006-loopback-mountd-v1.service is active/running, MainPID113311/
start27821165, InvocationID27440f83be924c72981e70e1158edda3, fixed cgroup,
exact original foreground argv. No restart/replay/automatic signal occurs.

Original raw recorded SELinux context is system_u:system_r:nfsd_t:s0 followed by
NUL. The parser used text.strip(), which does not remove that terminator, and
refuses before vendor-security comparison or NFSD startup. This is an observed
private metadata encoding issue, not a domain transition failure. Original raw
context/false flags/outcome stay unchanged. No policy/type/boolean/hardening
change. NFSD threads remain0 (not yet freshly recollected after this refusal),
NFSD unit/client mounts/app/failure-reset/secret retirement were not invoked.

Next completion must use a bounded exact raw-context decoder preserving all raw
bytes, adopt ONLY the SAME live mountd PID/start/unit invocation/executable/argv/
cgroup and verify vendor security properties. Never start mountd again or
promote the old completion. Then the FIRST NFSD tool start may proceed, with
exact localhost listener/version/thread proof. Client/host/pause read-only
NFS validation and rootless real browsers/isolation/lifecycle remain pending.
Checkpoint133 `.scratch/web-006-source17-current-state-v133.json` SHA256a25aca7f076f2b9a7161652d2246c8ad4e1c3dd9b08290a73c366e278c34353a.
WEB-006/AUTH-08/HOST-01–03 incomplete; original app failures and6secrets retained; production/NAS/live Cockpit untouched.

WEB-006 checkpoint134 update2026-10-23: SAME live mountd/context/security validated; FIRST NFSD tool invocation FAIL on unsupported NFSv2 option.

Closed proc-context decoder preserves actual raw hex/length/hash and permits
only the observed terminal-NUL nfsd_t representation; embedded/extra terminators,
other domains/MCS/whitespace/types refuse. Thirty-nine local guard/adoption/raw
context/no-replayed-effect tests PASS4.74s; lint and held1361source46input
preflight PASS. Original mountd-start completion remains failed/unmodified.
New completiona9c4da96/78372bytes/protectedc452b5b2/49641bytes FAIL1;
3505444/start426968241/reaped/gone2.618132s. It verifies SAME mountd113311/
start27821165/invocation27440f83be924c72981e70e1158edda3, exact argv/cgroup,
host user/mount namespaces, live pidfd and canonical observed nfsd_t context.
All vendor security properties match. No mountd/module/export/control replay.

FIRST NFSD unit invocation web006-loopback-nfsd-v1 is attempted once and fails.
Separate readonly diagnosticc154f429/60747bytes/protected657f64fe/32100bytes
PASS0;3505789/start426980953/reaped/gone1.228446s. Exact saved unit is failed,
MainPID=ControlPID0/empty cgroup, ExecMainPID113363/status1,
InvocationIDec12afcf7e114d598c90af2ef7884f5a. Journal's exact reason:
2: Unsupported version. Current supported tokens are +3 +4 +4.1 +4.2;
NFSv2 is absent and this installed utility rejects even the disable-v2 option.
No NFS listener, threads0, no client mount; original localhost-only RO export
still matches. Kernel45bb and original export booleans unchanged. Mountd remains
SAME live process with vendor security equality. App failures/6secrets unchanged.

Next new completion must pin both old NFSD failure and its closed readback,
preserve that failed unit without resetting/restarting it, rejoin SAME mountd,
and admit only the known zero-thread/no-listener state. A separately named
web006-loopback-nfsd-v2 tool may omit unsupported v2, disable supported v3,
enable v4 and use the standard localhost2049 port, already observed unused.
Retain raw version tokens; do not invent a -2 token or infer a port/SELinux
failure that was never observed. No port label/boolean/policy/hardening change.
Original modules/control/export/mountd are adopted, not replayed. Only after
actual localhost listener/vendor security proof may client and host/pause
read-only NFS validation proceed. Required real rootless acceptance stays pending.
Checkpoint134 `.scratch/web-006-source17-current-state-v134.json` SHA2566964d1de93adaba17e7ed8a37a7b1524a578b9b43129ccb78fd04721dd322d75.
WEB-006/AUTH-08/HOST-01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint135 update2026-10-23: owned localhost NFS server readiness PASS; no client/archive/app mount change yet.

A new completion-v3 phase label included uppercase NFSD and was correctly
refused by its bounded owner grammar BEFORE any effect; original1902972c/
80311bytes/protected8a22c7c5/48959bytes FAIL,3506559/start427009437/reaped/
gone2.384564s. No NFSD-v2 start occurred. Corrected separate scope v4 pins this
failure, normalizes only its NEW phase label and retains the old record. Added
static phase/effect grammar regression;49local guards/adoption/context/version/
no-replay tests PASS7.34s. Lint and held1361source54input preflight PASS,
quoted15898bytes<120000. Original failed NFSD-v1 remains unmodified.

Actual completion-v4 local813ef83e/112069bytes/protected6a2037c2/77461bytes
PASS0:3506975/start427024162 returns0/reaps/gone5.031139s. It adopts only
reconciled original module/control/export and SAME mountd113311/start27821165/
invocation27440f83be924c72981e70e1158edda3, live pidfd/argv/cgroup/host
namespaces/raw nfsd_t context. All vendor security properties match. Its ONE
new effect is the FIRST NFSD-v2 start, return0; no old start/export/module/mount
operation is replayed and no failed unit is reset.

web006-loopback-nfsd-v2.service is active/exited success, MainPID=ControlPID0/
empty cgroup, ExecMainPID113507/status0,
InvocationID5006567266d949d2bcb45fd79652ee53. Two kernel NFSD threads are
observed. The ONLY monitored NFS listener is actual tcp127.0.0.1:2049,
kernel inode709143/state0A. Raw versions are -3 +4 +4.1 +4.2; no invented
v2 token. Export remains exact owned synthetic seed to127.0.0.1, ro/secure/
root_squash/fsid0. Original unsupported-v2 unit/status1 is preserved separately.
Mountd/NFSD service security equals installed vendor defaults; kernel45bb,
existing booleans, original utility/unit/seed metadata and all1361source full9/
hashes/SIDs before/after unchanged. Original app failed states/6secrets retained.

This establishes TEST SERVER readiness only. No NFS client mount exists and no
archive contents, app role, failed-unit reset or secret retirement occurred.
Next a NEW owned client mount must use exact localhost NFS4.2/TCP2049 and
ro/nosuid/nodev/noexec at creation, prove live server/export binding, actual
UID983 EROFS and unchanged source/security. A new private fixture guard may
admit only that exact owned NFS mount and reject every external/unknown mount.
Then host+original pause archive views require actual NFS-ro proof, followed by
new authority, conservative exact-ID secret lifecycle and one fresh rootless
normal cohort/required isolation/fault checks. No rootless feature acceptance.
Checkpoint135 `.scratch/web-006-source17-current-state-v135.json` SHA2560195f20790fd050b089b88384f3ca7f623f1082358ff6c0f3bcbb70b46c9ced4.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/live Cockpit untouched.

WEB-006 checkpoint136 update2026-10-23: actual owned NFS4.2-ro client and UID983 EROFS PASS; archive namespace projection still pending.

Thirty-two private mount/network guards PASS1.70s: wrong target/IP/filesystem/
version/port, writable/missing-hardening/soft mounts, duplicate/unknown shared
mounts, changed/wildcard listener and external client refuse. Raw permitted
loopback TCP transition rows are retained beside a required established client;
they are never substituted for the listening socket or actual NFS mount proof.
Lint and held1361source57input preflight PASS; both actual mount executable and
hash-pinned installed mount.nfs are held through the original invocation.

Original client receipt7346a4d7/91820bytes/protectedf4cace9c/56890bytes PASS0;
3508511/start427085701 returns0/reaps/gone3.836264s. ONE original mount child
113577/start27968900 returns0/reaps0.332182s with empty streams. New client
mount766/dev0:58/shared624, nfs4 127.0.0.1:/, ro/nosuid/nodev/noexec/relatime,
vers4.2/hard/TCP/sec=sys/clientaddr127.0.0.1/addr127.0.0.1. Kernel omits its
default port field; explicit original argv requests2049 and independent actual
loopback TCP tuples bind it to the SAME listening inode709143 at127.0.0.1:2049.
No alias/default-port inference alone establishes that conjunction.

Actual dropped UIDGID983 probe uses only the NEW client root FD: statvfs RO,
exclusive write-open returns errno30/EROFS, no file created. EACCES/EEXIST or
other errors do not count as RO. No source payload, archive contents or secret
value read/hash. All1361source full9/hashes/SIDs, owned server/export/PID/
namespace/security/booleans, old failed application states and6secrets unchanged.
Only the new client mount was targeted. Its no-pause-change flag describes no
explicit pause-target command; it does not establish shared-mount propagation
or a read-only archive view in that namespace. Those remain to be inspected.

Next project the same proved NFS-ro view into host and ORIGINAL pause archive
views, after fresh exact mount/source/namespace ownership proof. Preserve all
old XFS inodes/mount evidence; isolate only the owned shared bind's propagation
where necessary to avoid overmounting the protected export source through a
shared peer. This isolation tightens mount propagation, never relaxes SELinux/
systemd or readonly flags. Pin the original pause namespace FD/PID/start and
use only fixed mount targets/source handles; retain each original effect and
partial failure without replay. Require actual NFS-ro and UID983 EROFS in BOTH
views, unchanged export source, before any fresh app generation. No app/reset/
secret retirement is authorized by this client-readiness result. Every future
guest tool must admit ONLY the exact proved owned localhost mount(s), refusing
all external/unknown NAS/shared filesystems; old no-NFS templates remain inert.
Checkpoint136 `.scratch/web-006-source17-current-state-v136.json` SHA256f960870068e15b13562b4755b672cae457ac9657a48d9bb7a6cf65850620da27.
WEB-006/AUTH-08/HOST-01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint137 update2026-10-23: independent exact archive/namespace read PASS; projection intent bounded before effects.

Readonly views receipt c6a082da/66503bytes, protected1a4dc82a/31959bytes PASS0;
3510139/start427156252 reaped/gone1.249155s. ORIGINAL pause70549/start6647855
and pinned namespace inode4026532305 remain alive. Client766/767 is already
NFS4.2-ro in host AND pause through observed shared propagation; archive535
is original XFS-ro/shared1, pause536 original XFS-rw/master1. Protected export
source inode118335700/full9/SID unchanged and not overmounted. All actual
filesystem kinds and namespace links recorded. No mount/app/secret effect.

Next isolate ONLY owned host archive535 propagation with make-private before
NFS bind, preventing shared-peer overmount of export source. Bind SAME proven
RO client into fixed host and ORIGINAL pinned pause archive targets. Preserve
lower XFS identities/raw evidence. Require source/export/security/source1361
unchanged plus actual UID983 EROFS and installed readonly preflight in BOTH.
No application start, failed-unit reset, secret retirement or effect replay.
Checkpoint137 `.scratch/web-006-source17-current-state-v137.json` SHA256f534449768e64ba8c1518f8937ede9598d2b22109f4854f988db842f35c2fec6.
WEB006/AUTH08/HOST01–03 pending; native23/gate17 unchanged.

WEB-006 checkpoint138 update2026-10-23: actual host+ORIGINAL pause NFS-ro projection and installed UID983 preflight PASS.

First projection14cc8317/protectedcd16b528 FAIL before effects: namespace full9
timestamps changed. Independent readonly read0b4e4b33/protected251d68b1 PASS,
3512232/start427236320 reaped/gone1.200263s; exact views unchanged. Original
namespace dev4/inode4026532305/first7 fields/PID70549/start6647855 match; only
mtime=ctime differs between opens. Original failure stays failed, effects empty.
New tool compares semantic namespace identity to history and verifies its
CURRENT full9 for the retained FD lifetime, with original PID/start and pidfd.
29local regressions PASS1.72s; lint and held1361source67input preflight PASS.

New projection9a900a77/132704bytes, protected1be000bd/90356bytes PASS0;
3512455/start427243391 reaped/gone3.905217s. Exactly three original effects
return0/reap: make ONLY host archive535 private; bind SAME proved NFS-ro client
to host archive765; bind to ORIGINAL pinned pause namespace archive780.
Lower original XFS535/536 retained. Protected physical export inode118335700/
full9/SID unchanged, no source overmount. Exact listener709143/export/server
security/kernel45bb/booleans and1361source full9/hash/SIDs before+after unchanged.

BOTH actual UIDGID983 probes return EROFS30/statvfsRO/no created file; BOTH
unchanged installed0.2.5 load_profile/fixed-worker-command/archive_readonly()
preflights PASS. NFS mount is4.2/TCP/localhost/ro/nosuid/nodev/noexec/hard/sec=sys.
No app start, failed-unit reset, secret read/retirement or old effect replay.
Original failed worker/Caddy states and observer UNKNOWN remain; strict role
closure and rootless/browser/isolation/fault/lifecycle acceptance still pending.
Old no-NFS tools remain inert. Next conservative failed-cohort6secret exact-ID
ownership review, fresh NFS-aware authority, explicit exact failed-state prep,
then ONE fresh rootless normal cohort and dedicated required checks.
Checkpoint138 `.scratch/web-006-source17-current-state-v138.json` SHA25630d2f78bb8f3b2e99d1a86831a232b1dcb775358dc63cf8b3b5f9b09fcda8b8f.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint139 update2026-10-23: conservative failed-cohort secret metadata read PASS; no deletion yet.

Readonly receipt d723dc2b/115681bytes, protectedf8cce47f/73130bytes PASS0;
3513052/start427263281 reaped/gone1.779062s. Exactly6fixed file-driver secret
IDs, no unknowns, stock inspect metadata only/NO SecretData requested. All six
CreatedAt=UpdatedAt in original23:39:57 create order/window after original empty
baseline and before stopped generation. Original payload inode127749655/full9/
SID matches recorded passed prestart gate; complete safe store before/after
unchanged. Original17PIDs gone. Projection/server/app failures unchanged.
Podman secret events EMPTY and journal metadata has NO Podman creation events;
these establish NO event-based ownership proof. Observer UNKNOWN preserved.

Separately scoped FAILED-BEFORE-CONTAINER cleanup may explain only these exact
6IDs using pinned original empty baseline + sealed controller's completed6create
stage before passed prestart gate + stopped original generation + matching live
inspect/creation order/window/store inode metadata. No name-only/unknown delete.
Require noncreating original controller lock, zero account containers, fresh exact
IDs/inspect/store equality, per-ID original intent/result and empty final list.
No collector payload body/hash; stock engine removal may internally read/rewrite
its own store. This branch NEVER supplies normal6ID/3liveCID secret lifecycle
acceptance, promotes observer failure, resets a failed unit or replays any app.
Fresh successful normal+dedicated lifecycle cohorts remain mandatory.
Checkpoint139 `.scratch/web-006-source17-current-state-v139.json` SHA256d18112f9e7234ac3ecd4ad76a6c86e91371ae77730eb7f190c71b0940c6d3891.
WEB006/AUTH08/HOST01–03 pending. Production/NAS/live Cockpit untouched.

WEB-006 checkpoint140 update2026-10-23: failed-before-container exact6ID cleanup PASS; normal lifecycle acceptance still pending.

Cleanup-v1 FAIL6f688bf1/protected0be55c75 before any removal: raw secret-list
order differs. Separate completion retains raw278bytes/hash6d999e3c, verifies
complete metadata equality keyed by exact ID; no field/unknown-ID relaxation.
Cleanup-v2 FAIL1e194ef7/protectedf7d55e09 before removal: account contains THREE
retained image-audit fixtures, not zero. Original claims/receipts stay failed.
Reference reader-v1 template field Id refused125 before modification; readonly
v2 PASS165b4fc6/protected00d44ba2,3514293/start427304683 reaped1.572013s. Exact
3audit CIDs are exited0/PID0/notOOM/noSecrets, finishedOct21/22 before cohort.
No unknown/live/secret-using container is admitted and no audit is removed.

36adversarial ownership/retained-container tests PASS1.70s, lint and held1361
source80input preflight PASS. New cleanup-v3 local77999054/126678bytes and
protectedf8368711/78493bytes PASS0;3514499/start427310202 reaped/gone4.535258s.
Original empty baseline/completed6create stage/passed prestart gate/17gone and
creation order/window + current original payload inode/full9/SID/complete store/
exact6IDs/inspect equality are joined under original noncreating controller lock.
Only6original per-ID Podman removals return0, each with intent/result and exact
remaining set; final list empty0/unknown0. Original2unit failures unchanged.
Three old exact exited/secret-free audit containers rechecked and preserved.
No collector payload body/hash; engine performs its own normal store rewrite.
This is FAILED-FIXTURE cleanup only: observer UNKNOWN and failed cohorts remain
unmodified, normal6ID/3liveCID lifecycle and rootless acceptance NOT supplied.

Next explicit separate prep may reset-failed ONLY exact known worker invocation
6f4f288c/status20 and Caddy4181e0ce/status125 after preserving before/journal/
original gone/cgroups/no app proof. No unit start/restart, no unknown reset or
old application replay. Require all13fixed roles inactive,4cgroups empty,5
endpoints refused before fresh NFS-aware authority/cohort. No production change.
Checkpoint140 `.scratch/web-006-source17-current-state-v140.json` SHA256b54e6a8de8a5381ca041b03fc67ac780475416911aabb87c98a2b9d33dc9f30b.
WEB006/AUTH08/HOST01–03 pending; gate17/native23/source1361 unchanged.

WEB-006 checkpoint141 update2026-10-23: explicit known failed-unit preparation PASS; actual strict fixture closure restored, no app replay.

Local unexecuted preparation-v1 syntax typo was caught before guest admission;
invalid draft/caller retained. Separate reviewed-v2 lint/held1361source82input
preflight PASS. Actual3d6c2ab0/81752bytes, protected2231c982/35105bytes PASS0;
3514922/start427322979 reaped/gone3.280696s. Holds original journalaf6f99d0,
failed generationdceba6fa/17gone, exact6ID cleanupf8368711/finalempty, original
noncreating controller lock, original pause70549/start6647855/pidfd and current
namespace FD/full9. Before requires ONLY exact worker6f4f288c/status20 and Caddy
4181e0ce/status125 failed, no app PIDs/cgroups. ONE reset-failed child returns0
for ONLY those2user units, no start/restart or replay. Original receipts unchanged.
After all13fixed roles inactive/PID0,4fixed cgroups empty,5endpoints refused:
strict closure PASS. NFS host/pause projection and source1361 full9/hash/SIDs
before+after unchanged, original pause alive. New acceptance not yet attempted.
Next fresh NFS-aware private authority/controller, fresh empty baseline/live
watcher, ONE new rootless normal cohort plus required isolation/fault/lifecycle.
Checkpoint141 `.scratch/web-006-source17-current-state-v141.json` SHA25697b0f92cd3ed5defe70fb68f8e4e6cde447dac05c315de91e960bdcb94a5ea16.
WEB006/AUTH08/HOST01–03 pending; production/NAS/live Cockpit untouched.

WEB-006 checkpoint142 update2026-10-23: NFS container policy prerequisites PASS; new authority25 static marker mismatch FAIL preserved before activation.

Readonly NFS policy read e7bfa085/protectedbe943a76 PASS0;3515486/start427343201
reaped/gone1.358621s. Actual target nfs_t:s0; existing virt_use_nfs ON; active
kernel seq47 permits requested container_t dir getattr/search/read/open and file
getattr/open/read. Kernel45bb unchanged before/after, Enforcing; no boolean/label/
policy/hardening change, archive content read or application start. Strict closure
PASS. This is prerequisite evidence only, never actual container I/O acceptance.

New private controller26 changes ONLY control/generation paths and closed owned
NFS fixture guard; original Controller class/all application methods AST unchanged.
Exact host765/766 and original pause767/780 NFS rows/socket709143/PID bindings;
unknown/external filesystems refuse; only owned default rootless engine overlay
paths may be admitted.19local adversarial/AST tests PASS1.79s; composed-root
name/entrypoint/work audit, lint, held1361source92input preflight PASS;55688<120000.

Actual authority25 prep facf2a0a/98631bytes, protected725f2c5f/46170bytes FAIL1;
3516640/start427387562 reaped/gone4.204449s. SIX new files published exactly once
(controller26,launcher,2profile launchers,marker,manifest); original metadata/SIDs
retained in failed receipt. Static validator refuses marker scope text introduced
by this tooling; exact required scope is owned isolated WEB006 only. No control26,
generation26 directory, sudoers25, alias preservation, activation or app start.
Original current rootless24 selector/deployment/policy remain, strict closure PASS.

Next new completion must pin original failure and all6published full9/hash/SIDs,
never rewrite/relabel/replay them. Create only new marker/launcher/manifest v2
filenames with exact reviewed marker scope, validate actual installed package,
then publish control26/preserve original aliases NOREPLACE/install only scoped
fixture sudoers. Keep fresh fixture UUID949ea0af-c6fd-40f0-8d3e-b99f0cb6e989,
source17/runtime/package/image unchanged. No rootless acceptance inferred.
Checkpoint142 `.scratch/web-006-source17-current-state-v142.json` SHA256062ef390589db318a59f29f6f518ebafc12dbbe0ed633f1ce9fc1b3851339f85.
WEB006/AUTH08/HOST01–03 pending; production/NAS/live Cockpit untouched.

WEB-006 checkpoint143 update2026-10-23: separate authority25/controller26 completion PASS, no old publication rewrite or application start.

Composed name/marker/entrypoint/adoption audit and held1361source96input preflight
PASS;55969<120000. Original authority25 marker refusal stays failed. All6original
published full9/hash/SIDs held/rejoined unchanged. Only NEW marker-v2, browser
launcher-v2 and manifest-final-v2 files are created, with exact reviewed scope.
Actual installed validator asUID1000 PASS against same readonly108file0.2.4
package projection. Original6files/oldsource/publications not rewritten/relabelled.

Actual completion c818d908/131388bytes, protectedbc7397c5/75143bytes PASS0;
3517256/start427410577 reaped/gone5.474649s. New fixture949ea0af-c6fd-40f0-8d3e-
b99f0cb6e989; controller26 hash8d968403/116310bytes, control26 hash7144c1e0/
37141bytes; all183old control inputs preserved in order plus10explicit inputs.
New manifest4900f165/5025bytes at authority-v25/...v25-final-v2.json; browser
launcher254f25b3/98832bytes. Controller load equality and exact owned NFS guard
PASS. Original rootless24 selector/deployment/policy preserved by3NOREPLACE
renames to completion scope, with intent/result/current inode/SID evidence;
current aliases absent until NEW controller selection. Only new scoped sudoers25
installed after visudo PASS. No services/timers/credentials/kernel changes or
old run replay. Source1361/full9/hash/SIDs before/after/finally and readonly
package108files unchanged. Strict13role/4cgroup/5endpoint closure PASS. Actual
FDused780/soft1024/reserve32, unchanged limits. No normal rootless acceptance.

Next fresh authority25 empty secret baseline and newly bound NFS-aware live
observer/runner/coordinator, then ONE new rootless normal functional cohort.
Old no-NFS templates remain inert. Original native23/gate17 retained; required
rootless and dedicated isolation/fault/lifecycle acceptance remains pending.
Checkpoint143 `.scratch/web-006-source17-current-state-v143.json` SHA256f89dfc4266d47bb178e08c8f379a4e6d83731373e3a9fb26b11758f715e3c181.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint144 update2026-10-23: authority25 fresh empty baseline PASS; ONE new normal rootless coordinator prepared, not yet invoked.

Baseline42673de3/80292bytes, COMPACT protected9e8ccb8f/19258bytes PASS0;
3517707/start427426660 reaped/gone1.405445s. Actual stock983 empty0/unknown0,
complete safe store before/after unchanged; original pause identity retained,
strict role closure PASS. Original native23 prerequisite/authority25 completion
held/closed. Only exact owned NFS guard differs from old no-NFS baseline; no
secret payload, app role or old run replay. This baseline is historical once
NEW credentials are created; never assume current emptiness later.

New authority25 observer89fde507/49863bytes and runnerb7e8f892/38599bytes bind
actual control26/manifest-v2/controller26/completion/baseline hashes and original
70549namespace. Normal6ID/3liveCID ownership and delivered gates remain mandatory.
Coordinator4c9d43c7/57288bytes preserves original paired-child EOF/reap, atomic
ARMED/source-command hash and ONLY2runtime assignments. Latest failed24 children
are freshly proved gone, never replayed/promoted. Stronger all183input prefix
proof replaces older168field check; new completion explicitly preserves183.
Borrowed original authority23 runner wrapper unchanged; new manifest passed
explicitly.29real-child/binding/mount guards PASS3.63s, leaf lint and composed
dependency audit PASS. Local caller-v1 preflight missing ast import refused
BEFORE guest call; invalid draft/failure record retained. New caller-v2 preflight
PASS held1361source104inputs;47766<120000, original SSH EOF budget2100s, no auto
signals/retry. Ready to invoke ONCE; no rootless acceptance inferred yet.
Checkpoint144 `.scratch/web-006-source17-current-state-v144.json` SHA256fbad984929b650f71852b966d6387be60b6019700581e3424b641d28388feba1.
WEB006/AUTH08/HOST01–03 pending; production/NAS/live Cockpit untouched.

WEB-006 checkpoint145 update2026-10-23: first authority25 coordinator refuses stale embedded-body scalar pins BEFORE children/app; strict closure PASS.

Original c5a9c466/87648bytes, protected33a4d656/29927bytes FAIL1;
3518774/start427465234 reaped/gone1.277407s. New embedded observer/runner bytes
were correct; their separate scalar SHA assignments retained old values because
a textual replacement assumed spacing. Refusal occurs at body checksum check,
BEFORE watcher, ARMED, runner, secrets or application generation. Original
latest failed24 children freshly gone, source/authority/baseline held, final
strict13role/4cgroup/5endpoint closure PASS. No app operation admitted/replayed.

New coordinator scope rootless25-coordinator-v2 pins that original failed
setup record and requires its no-child/strict-closure facts. AST assignment
updates actual observer89fde507 and runnerb7e8f892 scalar pins. Added direct
exact-body SHA regression;30local real-child/binding/mount tests PASS3.77s.
New rootbd8ea3c5; caller-v3 preflight held1361source107inputs PASS,47849<120000
and2100s original SSH EOF budget. Ready for FIRST normal app cohort under new
scope; old setup failure remains failed, never replayed/promoted. Documentation
alignment PASS207human/27helpers. No rootless acceptance yet.
Checkpoint145 `.scratch/web-006-source17-current-state-v145.json` SHA2569a5c7ea9af0764079417c511e674bfbc8a7a76f3fd12b4a471beba2e93506043.
WEB006/AUTH08/HOST01–03 pending; production/NAS/live Cockpit untouched.

WEB-006 checkpoint146 update2026-10-23: actual authority25 normal run FAIL at protected helper startup; original generation/journals retained, no browser acceptance.

Actual coordinator beb19c36/96109bytes, protectedea4b0b4b/36571bytes FAIL1;
3519284/start427482943 reaped/gone7.221447s. Live watcher114592/start28366019
ARMED6dd4df59 matched fresh authority/baseline before runner114593/start28366041.
Original functional child114597/start28366069 returns1/reaps5.263804s. No SUMMARY
or browser cases. Original failed scopes remain failed; no replay or acceptance.

Readonly startup diagnostic986b28c7/protected549e3f59 PASS0;3519834/start427502414
reaped/gone1.361900s. Generation0a14f7465cfc4f0185d5e463ff682dc8/efd6d888 is
started+stopped, no containers/ready;16original PIDs and watcher/runner freshgone.
Original8input prestart gate PASS; six fixture secrets created, NOT retired.
Observer394d13cc ownershipFalse/payload-read UNKNOWN/all_sources_closedFalse
retained. ONLY system helper failed/invocation98906cde7f484316b3045068b5df2615/
status20, PID0/empty cgroup; user API/worker/Caddy remain inactive/unstarted.
Journal shows protected helper fixed generic startup refusal. Strict closure is
NOT accepted while helper failed; no reset/restart performed.

Known fixture defect: host /srv has BOTH original lower535XFS-ro and upper765
NFS-ro rows. Unchanged _inspection_archive_mount requires one non-autofs row
and refuses this ambiguity. Worker mount barrier itself passed earlier; do not
weaken the host inspector to accept a synthetic stack. Next correct ONLY owned
guest mount topology under exact zero-executor/lock/PID namespace proof: tighten
guest root71 shared propagation to private (mount moves under shared ancestor
are unsupported), move SAME765 NFS-ro to owned private parking, move original
535 XFS-ro to owned preserved parking, then move SAME765 back as sole host
archive row. Original source inode/RO client/server and original pause536/780
remain; no unmount, payload read/write, app/reset/secret action or old-effect
replay. Intermediate host availability is explicitly unaccepted; actual apps
stay stopped and physical RO NFS client/export never become writable. Require
all source/security/server/mount IDs and actual983EROFS host+pause before new
authority/failed-secret cleanup/fresh cohort. Production is outside this scope.
Checkpoint146 `.scratch/web-006-source17-current-state-v146.json` SHA256f39cffcbcebf01642226109cdb28e87425ab7fffd62a55f6e631eb712eac34b4.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint147 update2026-10-23: actual sole host NFS-ro archive view and unchanged installed inspector PASS; original mounts preserved.

18local stage/identity/flag/namespace/effect allowlist tests PASS1.68s; lint and
held1361source112input preflight PASS18511<120000. Actual27192336/175927bytes,
protected953da425/109874bytes PASS0;3521619/start427577374 reaped/gone4.066254s.
Original source/server/PID/namespace/zero-executor/lock proofs held. Exactly4
first effects return0/reap: make guest root71 propagation PRIVATE (nonrecursive);
move SAME765NFS-ro to owned parking; move SAME535XFS-ro to preserved-original-XFS
parking; move SAME765 back to /srv as ONLY host archive row, now parent71. No
unmount or mount-ID replacement. Temporary uncovered host path proved empty,
root-owned/local/no group/other write; intermediate availability NOT accepted.
No app executor can run: original controller lock held, all13fixed roles PID0/
empty cgroups (only known helper98906cde failed),4cgroups empty,5endpoints refused.

Original physical export inode118335700/full9/SID unchanged, original NFS client/
server/export/socket709143 and original pause mount rows unchanged. SAME original
70549namespace FD/pidfd and mountd remain live. Existing RO flags never changed.
Actual UIDGID983 in HOST+PAUSE receives EROFS30/statvfsRO/no probe file and both
unchanged installed worker readonly preflights PASS. Most importantly unchanged
installed _inspection_archive_mount now returns nfs-ro against actual HOST rows.
No host-inspector guard relaxation, app/reset/secret operation or replay.
Source1361/full9/hash/SIDs and server/security/kernel45bb/booleans unchanged.
Old XFS535 retained RO at /opt/hfcache-web006/host-archive-single-view-v1/
preserved-original-XFS; original pause536/780 retained. Old guards pinned to
765parent535 are INERT now. New exact guard must bind actual765parent71 and
unchanged client766/pause767/780, refusing every other NFS/external filesystem.

Next failed25 exact6ID metadata/lifecycle review (current secrets not read or
removed here), known helper failed-state preparation, fresh authority26/controller27
and ONE fresh normal cohort. Original failed25/observer UNKNOWN remain. Native23
and gate17 unchanged; full rootless/isolation/fault/lifecycle acceptance pending.
Checkpoint147 `.scratch/web-006-source17-current-state-v147.json` SHA2569ecead5bb4351ea0cdbbdefcbae1df956f9d1da66c7071eb277e44a0e0a34de3.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint148 update2026-10-23: installed rootless readonly stage/bindings PASS and failed25 six-ID metadata PASS; new NFS receipt/index preparation required.

Actual installed-profile3e1bc66d/protecteda49c2fde PASS0;3522592/start427613484
reaped/gone1.489325s. Exact installed host_policy602767a6 performs original
rootless stage/index/rendered policy/binding verifier and single-host archive
classifier:74files/799588bytes, nfs-ro. CONFIGURATION and REVISION_KEY are NOT
read; key/config buffers remain empty. No daemon/domain acceptance or payload
read implied. Current helper still failed98906cde/status20. Guard-v2 local
mutation test found duplicate NON-NFS mount IDs were not refused; no mutation
used it. Readonly profile probe used actual unique kernel rows. New guard-v3
adds closed unique mount IDs, exact archive counts (host765only; pause536/780),
keeps exact4NFS rows and old-private external-fs refusal;20tests PASS1.75s.

Failed25 metadata41ab6138/133849bytes, protected3b37aee0/65196bytes PASS0;
3523516/start427649569 reaped/gone3.166091s. Exactly6known file-driver IDs, no
unknowns; default inspect has NO SecretData. Complete store before/after same;
original payload inode/full9/SID matches original passed prestart gate. Original
generation0a14f746/16PIDs freshlygone. No payload body/digest, retirement, unit
reset or source/policy change. Original observer ownershipFalse/UNKNOWN retained.
Readonly semodule --list-modules=full --checksum succeeds: loaded helper CIL
priority400 SHA2565e343f13ff66a591350c6db582eb1debd7746b784f263d552704f602184fac3e.

Actual NFS archive type is nfs_t; existing provisioning receipt still attests
old local hfcache_archive_t. Host-administration/security contracts explicitly
require fresh receipt/index on administrative label change. Do not ignore this
or weaken policy. Root-owned next fixture preparation must preserve original
fixed receipt inode/bytes, create new receipt differing ONLY archive label and
current verified provisioning facts, rebind NEW protected native/rootless
deployment/policy descriptors (same versions/artifacts and configuration-only
grants), no CIL/module/boolean/permission changes. Fixed receipt is NOT among
old193control inputs, so historical prefix can remain unchanged. Original
control/receipts/profiles and failed cohorts stay preserved and inert.

Next separately reviewed failed25 exact6ID cleanup under original empty baseline/
completed create stage/passed gate/creation window and original lock, preserving
only3known exited0/no-secret image audits; then ONLY exact helper failed reset,
new receipt/index prep and strict closure before fresh authority26/controller27.
No normal6ID/3liveCID lifecycle acceptance or app replay inferred.
Checkpoint148 `.scratch/web-006-source17-current-state-v148.json` SHA256750c263ed2d5ec431d81973f38b5d9643d11f9253bf26a31112334cf53a04678.
WEB006/AUTH08/HOST01–03 pending; production/NAS/live Cockpit untouched.

WEB-006 checkpoint149 update2026-10-23: failed25 exact6ID fixture cleanup PASS; original observer failure/UNKNOWN not promoted.

29local cohort/timestamp/ownership/exact-removal tests PASS1.74s, lint and held
1361source124input preflight PASS17576<120000. Actual0bff17cf/147453bytes and
protected53df5c49/76656bytes PASS0;3525184/start427720443 reaped/gone4.495850s.
Original empty9e8ccb8f baseline, failed generationefd6d888/16freshgone, original
watcher+runner freshgone, sealed controller8d968403 and passed prestart6create
stage are joined with exact6live IDs/inspect metadata, creation order/window
and original store payload inode/full9/SID under original noncreating lock.
Only3historical exact exited0/PID0/noSecrets audits are admitted and preserved.
All6first per-ID removals return0, exact remaining set checked after each; final
empty0/unknown0, complete safe store. No force/all/ignore/name-only or unknown
secret deletion. Collector does not open/read/hash payload; stock engine performs
its own store removal. Original known helper failure98906cde/status20 remains
unchanged, no reset/start/replay. Normal6ID/3liveCID lifecycle acceptance remains
FALSE, original observer394d13cc ownershipFalse/payloadUNKNOWN preserved.

Next prepare new nfs_t installation receipt and NEW native/rootless protected
descriptor/policy copies with unchanged versions/assets/config-only grants.
Preserve original fixed receipt inode/bytes by explicit NOREPLACE moves; verify
actual current nfs_t/loaded module checksum/kernel and no source/policy change.
Then ONLY exact known helper reset and strict closure, fresh authority26/controller27
and new cohort. No prior app acceptance or operation replay is inferred.
Checkpoint149 `.scratch/web-006-source17-current-state-v149.json` SHA256ded608f30db07fc3f2f0eca83151f3a6df9e0d1db0ce44032414c85497d755ef.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint150 update2026-10-23: fresh actual-NFS label receipt and NEW descriptor/policy copies PASS, no policy/grant/service change.

15local receipt/type/module/index/exact-byte policy-link/non-broadening/atomic
preservation tests PASS1.67s, lint and held1361source127input preflight PASS
15666<120000. Actual6d8eeacf/110475bytes, protected62d52b6a/40430bytes PASS0;
3526379/start427771288 reaped/gone2.626308s. Actual current nfs_t, loaded CIL
checksum5e343f13, installed source CIL and kernel45bb join original old receipt.
Product closed schema validates complete new candidates BEFORE fixed-path change.

Original receipt inode78232543/bodyd0e28181 preserved NOREPLACE at
/opt/hfcache-web006/nfs-label-receipt-v1/preserved-original-host-helper-selinux.json.
NEW prelabelled receipt moves NOREPLACE to fixed /etc/hfcache/host-helper-selinux.json,
inode78601867/SHA79f3db35/1091bytes/root0644/ConfSID. Parsed receipt changes ONLY
archive role hfcache_archive_t→nfs_t; every other label/module/kernel field stays.
Existing kernel/source/module/booleans/permissions unchanged, no policy reload.
Master-key inode78157344/full9/SID held metadata ONLY; body/digest never read.

NEW protected files under same owned receipt scope: native deployment831af976/
policycbad31d5; rootless deploymentae50d0f7/policyc1ce5ca4. Only descriptor's
selinux_installation_sha256 and its policy deployment_sha256 change; original
versions0.2.4/0.2.5, exact artifacts/assets and configuration-only grants remain.
All original profile files preserved. Candidate labels established while empty,
original controller lock held through data-only provisioning. Original helper
failed98906cde/status20 and all13role PID0/cgroup state unchanged; no reset/start,
secret operation, old-effect replay or source/artifact rewrite. Current OLD
deployment intentionally refers to old receipt until NEW controller selection;
old controllers are inert and no availability is accepted from this preparation.

Next ONLY exact helper failed reset with original journal/gen/cleanup/receipt
proof and strict13role/4cgroup/5endpoint closure; fresh authority26/controller27
uses NEW profiles/receipt and exact NFS guard3. Fresh baseline/live normal cohort
and required isolation/fault/lifecycle remain pending.
Checkpoint150 `.scratch/web-006-source17-current-state-v150.json` SHA256da3ec46d5ae98ebe5628466cb2e2f7a25462ff847cd5519be7bb5f3f0794fb38.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint151 update2026-10-23: ONLY known helper failed-state preparation PASS; strict fixture closure restored without startup.

Lint/held1361source129input preflight PASS12969<120000. Actuald7344a83/103581bytes,
protectedf9044f0b/32851bytes PASS0;3527039/start427797697 reaped/gone1.294537s.
Original failed25 diagnostic/gen/observer/runner freshgone, exact6ID cleanup and
new NFS receipt prep are held/rejoined. Current fixed receipt79f3db35/nfs_t held.
Before requires ONLY exact failed helper98906cde7f484316b3045068b5df2615/status20/
PID0; all other fixed roles inactive/PID0. Under original noncreating controller
lock ONE system reset-failed hfcache-host-helper.service returns0/reaps. No app
start/restart, secret/policy/receipt operation or old app replay. After all13fixed
roles inactive,4cgroups empty,5endpoints refused: actual strict closure PASS.
Original70549pause and exact NFS guard3 still match. Original failures unchanged.
Next fresh authority26/controller27 with nfs_t receipt/new protected profile
indexes; old controls are inert. New baseline/live paired normal cohort and
required dedicated isolation/fault/lifecycle acceptance remain pending.
Checkpoint151 `.scratch/web-006-source17-current-state-v151.json` SHA25630f88b960bfc6f23aa1bfc59577ccef5c3ad99bd778ee19b638efcb06d8c91c3.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint152 update2026-10-23: new authority26 preparation stopped before control installation or application startup.

Pre-invocation review corrected stale browser profile pins;26local tests and
held1361source137input preflight PASS. Actual cc45d93a/119615bytes, protected
8ff3f59d/44092bytes FAIL ValueError at saved/captured record-shape comparison;
3529692/start427909643 returns1/reaped/gone3.927596s. Five exact controller/
launcher/marker files are preserved. No new profile copies, manifest, control,
sudoers, selection preservation or app generation was installed. Final actual
13role/4cgroup/5endpoint strict closure PASS, source17 unchanged.

Separate completion holds the original failed receipt and all5file full9/hash/
SIDs, reuses their original inodes without republishing, and joins captured
metadata plus actual length/hash explicitly. New public profile copies bind
exact protected new-receipt descriptors/policies BEFORE installed validation;
original193control inputs preserved.28local regressions PASS3.38s; completion
held1361source140input preflight PASS57060bytes. Completion is prepared only,
not yet invoked. No old failure or UNKNOWN result is promoted.
Checkpoint152 `.scratch/web-006-source17-current-state-v152.json` SHA256b6c494f3ea888f18005f38dd5e2103f845cf0a57910394aaa61b484a965da198.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint153 update2026-10-23: new NFS-aware authority26/controller27 preparation PASS; applications remain unstarted.

Separate completion-v1 ba091012/protected64271929 FAIL index uniqueness check
after actual installed manifest validator PASS, before control/selection/apps.
Original193inputs contain4identical historical repeated pins; preserve their
exact order and require equality for every repeated path. Completion-v2 afce381c/
protected1b02b4c3 FAIL at candidate record's known empty-label attestation field;
only new result scope created, all original files intact. These failures remain.
New comparison explicitly admits only exact capture fields, byte count and the
known true label attestation; unknown fields/conflicting hashes refuse.

31local regressions PASS3.52s; held1361source146input preflight PASS57591bytes.
Actual completion-v3 30c1628d/163619bytes, protected95cbabf5/81296bytes PASS0;
3530744/start427941918 returns0/reaped/gone5.547205s. All11original partial files
and empty generations directory are adopted at exact original full9/hash/SIDs.
Installed static validator, controller load equality and scoped visudo PASS.
Control27 SHA790913da/39950bytes, manifestc67348b5/5019bytes, controllerd6ac6e16.
UUID84387eb1-9863-45be-83b0-92b6d1013ab6. New protected/public profile hashes
match new nfs_t receipt79f3db35. Original193input prefix including4identical
repeats is preserved; existing NFS policy pin rejoined without duplication.

Original rootless25 selector/deployment/policy preserved NOREPLACE in new
completion-v3 scope; current aliases absent until a NEW controller selection.
Only scoped sudoers26 installed, no services started or image/source restaged.
Actual final13role/4cgroup/5endpoint strict closure PASS.809FD+32reserve<1024,
limits unchanged. Source1361/readonly108package/originalpause/kernel unchanged.
Next fresh authority26 baseline/live paired rootless normal cohort; dedicated
isolation/fault/lifecycle still pending. Native23/gate17 unchanged.
Checkpoint153 `.scratch/web-006-source17-current-state-v153.json` SHA256cd67e4500d59a4f0c17f6e918d5cd35b5f193a6b48d80afa32badc8b7c955952.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint154 update2026-10-23: fresh authority26 stock983 empty baseline PASS; new live paired cohort prepared.

21baseline/guard tests PASS3.07s and lint PASS. Caller-v2 held1361source149inputs
preflight PASS15646bytes. Initial outer wrapper refused a mistyped SHA BEFORE
spawning any child or guest call; corrected exact pin used a separate execution
stem. Actual baseline2b33c7b6/106508bytes, protected COMPACTf304e156/19258bytes
PASS0;3531137/start427952526 returns0/reaped/gone1.467806s. Empty0/unknown0,
complete store full9/SIDs unchanged;13fixed roles quiescent, original70549pause
and unchanged native23 prerequisite/current authority26 held and rejoined.
No secret payload/hash, secret mutation, application start or retirement.

New observerb11bea1f/runner-templateec73aed2/coordinator96f1b9eb bind actual
control27/manifest26/receipt and baseline; exact guard3/single host NFS retained.
Original PUB23 functional wrapper remains unchanged with explicit NEW manifest.
Historical failed25 runner/watcher must be freshgone. Atomic live ARMED then
only2runtime pins; original child EOF/reap ownership and1850/2050/2100budgets
retained. Offline stale embedded-body assertions corrected before invocation;
34local binding/EOF/overflow/unknown-global regressions PASS5.29s, leaf lint PASS.
Caller1051f5f4 held1361source154inputs preflight PASS48299<120000; cohort is
PREPARED ONLY. Next invoke once; required normal ownership/live3CID/6ID, built
UI all3engines/shared Caddy and strict postrun remain unperformed, as do dedicated
isolation/fault/lifecycle checks. No previous failure/UNKNOWN promoted.
Checkpoint154 `.scratch/web-006-source17-current-state-v154.json` SHA2564e98cb2b19cc429ee94d472f41dcc77091635e72ebc69354007b233631f8060d.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint155 update2026-10-23: actual rootless26 normal cohort FAIL at missing local container bind sources, before browser cases.

Actual d51aacc7/122241bytes, protected29186321/38425bytes FAIL1;3531700/
start427970737 returns1/reaped/gone9.742520s. Live ARMED3300e70d matched new
authority/baseline; watcher115595/start28853795 and runner115596/start28853823
are reaped/gone. Original functional child115600/start28853850 returns1/reaped
7.374257s. Generation54d52dc79ca34ab98696eb554aa0fe3e is started/stopped,
containers/ready empty; all17original process pairs now gone. Original8inode
label gate passed; delivered gate/browser SUMMARY absent. Observer ownership
False/payload-read UNKNOWN preserved. Six NEW fixture secrets are retained;
historical empty baseline is NOT evidence of current emptiness.

Readonly diagnostic-v1 65f391fe/protected9824d1ba collected current generation/
manager/helper journals, but its original-failure path still selected failed25
and --user-unit as root omitted983journal entries. It is NOT failed26-child
closure evidence. Corrected literal-bound read-v2 90a0085a/152402bytes, protected
48857012/65546bytes PASS0;3532157/start427983776 reaped/gone1.319766s; binds
actual failed26 receipt and both correct original children freshgone. Exact
UID983/user-unit matches reveal worker115755/fadc568e/status125: missing
/run/hfcache/verification; Caddy115778/9ef8f21c/status125: missing
/var/lib/hfcache/caddy-config. Both MainPID/ControlPID0/cgroup empty. System
helper actually STARTED and STOPPED normally; no helper startup refusal here.
Strict13role closure remains unaccepted because two user units are failed.

Readonly bind metadata c77c96a2/172113bytes, protectedfa1cfd79/82117bytes PASS0;
3532631/start427998116 reaped/gone1.249645s. Both HOST and ORIGINAL pause70549
see identical paths/inodes: /run/hfcache/api, /run/hfcache/verification,
/run/hfcache/hfcache.lock and /var/lib/hfcache/caddy-data/caddy-config absent.
Existing api.lock inode17356 and verification.instance.lock52246781 are retained.
No file payload/hash, mount/secret/reset/start action. Next inspect/reconcile
failed26 secret metadata, scoped fixed missing-directory provisioning and original
lock history before creating any absent lock; ONLY known user failures reset,
fresh authority/baseline/cohort afterward. Do not replay failed26 or mutate
security policy to bypass it. Required dedicated checks remain pending.

Documentation alignment PASS207human/27helpers; git diff --check PASS. Current
selector condensed to navigation/current state; detailed checkpoint history remains
in this task, dated plan and progress, with prior selector bytes retained privately.
Checkpoint155 `.scratch/web-006-source17-current-state-v155.json` SHA256655beccfcc6506e639eeadfdcd16366f76d820a8485898a6f7995518292283f2.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint156 update2026-10-23: failed26 exact secret cleanup and missing fixed bind sources provisioned; strict fixture closure restored.

Readonly metadata40f74602/156066bytes, protected3e6a30e6/65727bytes PASS0;
3533070/start428012740 reaped/gone3.036645s. Six exact metadata IDs joined
original empty baseline/completed create sequence/17gone generation/passed
8inode gate/full unchanged store; no collector payload read/hash.
36local failed-cohort/identity/known-state regressions PASS1.83s, lint and held
1361source166input preflight PASS17625bytes. Actual cleanup432f1723/169513bytes,
protectedc10487e5/77052bytes PASS0;3533351/start428021253 reaped/gone4.489122s.
All6exact-ID removes return0; final empty0/unknown0;3historical audit containers
remain exited0/PID0/secret-free and unchanged. This supplies NO normal lifecycle
acceptance; observer False/payload UNKNOWN stays recorded.

13local exact-missing-set/unknown-input/real-exclusive-no-overwrite tests PASS
1.76s. Held1361source169input preflight PASS16725bytes. Bind preparation
3a39a660/244879bytes, protectedd9e03f39/145897bytes PASS0;3533855/start428039645
reaped/gone1.376418s. Original noncreating controller lock retained; scan finds
NO live/open/deleted /run/hfcache/hfcache.lock handle before new creation. ONLY
5proved-absent fixed paths created exclusively, empty, uidgid983: api20435,
verification20437 and hfcache.lock20436 under /run/hfcache; caddy-config4487064
and caddy-data4487065 under /var/lib/hfcache. Dirs0700/file0600; ordinary
var_run_t/var_lib_t label set while empty, no security/policy relaxation.
Host+originalpause see identical new inodes/SIDs. Existing api.lock17356 and
verification.instance.lock52246781 full9/SIDs preserved. No app/reset/secret
action, no existing leaf overwritten.

5exact receipt/cohort/reset-argv checks PASS1.65s; held1361source172inputs
preflight PASS15713bytes. Known-state prep5ba64c45/128918bytes, protecteda07ab2b7/
35818bytes PASS0;3534216/start428051464 reaped/gone3.487550s. ONLY exact user
fadc568e/9ef8f21c failed states reset-failed in one fixed command after all
17generation/two original child pairs freshgone, empty listing and repair proof.
Actual13role/4cgroup/5endpoint strict closure PASS. Source1361/guard3/kernel/
original70549pause/installed artifacts unchanged. No start/restart/replay.

Next fresh baseline/observer/runner/workspace-v2 and a new generation on SAME
validated authority26/control27. Reuse is deliberate: no installed source, UI,
protected descriptor/policy, kernel or control input changed; new repair/cleanup/
closure receipts are additional held admission prerequisites. Avoid redundant
controller/asset publication. A new generation/ARMED/workspace never replays the
failed original handles. Required rootless normal browser/lifecycle and dedicated
isolation/fault acceptance remain pending; WEB006 cannot be committed yet.
Checkpoint156 `.scratch/web-006-source17-current-state-v156.json` SHA2560c37476592aef44c77a4798c526923b7b0b07937c99147db6fca30df9e842939.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint157 update2026-10-23: repaired baseline PASS; fresh rootless27 normal cohort FAIL before browser on missing nested mount placeholders.

Fresh baseline-v2 2c1c08ec/120335bytes, COMPACTde34edf1/19917bytes PASS0;
3534673/start428067868 reaped/gone1.523837s. Current repair/cleanup/strict closure
receipts held;5new sources matched exact current full9/SIDs before engine start.
Empty0/unknown0/complete store unchanged. Same authority26/control27 reused
explicitly; fresh normal-v2 observer/runner/workspace and new generation.35local
coordinator/current-proof/EOF/guard tests PASS3.93s; lint and held1361source179
input preflight PASS48808bytes. Actual b47d9c9d/137374bytes, protected3a7611ba/
40426bytes FAIL1;3535032/start428079814 reaped/gone13.386461s. ARMED951d02cf
matched; watcher116415/start28962874 and runner116416/start28962900 reaped/gone.
Functional child116420/start28962932 returns1/reaped11.224781s. No SUMMARY or
browser cases. Generation40c64cd7a7e542e88cc998b3689c8581 stopped/containers/
ready empty; all17original process pairs gone.8original inode gate PASS; no
delivered gate. Observer False/payload UNKNOWN preserved;6new secrets retained.

Readonly diagnostics37b2ca79/protected04091ffc and exact-invocation journal
93f19958/171003bytes, protected54e9e90e/70809bytes PASS0. Latest3535654/
start428099897 reaped/gone1.307061s. Old generation54d52dc7/shaac4c27a5
preserved unchanged beside new176a8f06/14636bytes. System helper starts/stops
normally. Worker116574/invocation964a4b5a84d24c4ca7ff6d3aed1ee151/status126
refuses OCI mkdir /etc/hfcache/containers: permission denied under read-only
parent bind. Caddy116611/invocation63a6976a1a7249f6a8a2343d5cdb130b/status1
occurs during immediate stop after worker failure; no separate Caddy cause
established. Both PID0/cgroups empty; strict13role closure NOT accepted.

Metadata proves /etc/hfcache/containers AND /etc/hfcache/client.toml absent.
Standing containers contract requires root-owned real placeholders; fixture
provisioning omitted them. Existing credentials directory inode118329700/0750/
root:983/secret_t is preserved; no permission widening is selected. Next only
exclusive empty root-owned placeholders, after exact failed27 secret cleanup.
No image/source/profile/security change or new publication is needed. Existing
5new runtime/state inodes and original locks remain; future current metadata
must account for legitimate engine :z labels/ctime rather than reuse prestart
full9 after an actual attempt.

Readonly secret metadata6415d2a3/168219bytes, protected03097f39/65899bytes PASS0;
3535885/start428106984 reaped/gone3.239455s.6exact IDs/unknown0/complete store
unchanged/original payload inode gate match.36local failed27 cleanup witness/
identity/known-state checks PASS1.81s, lint and held1361source189input preflight
PASS17638bytes. Cleanup9fc15d05/caller448e2391 is PREPARED, NOT invoked.
Next invoke once; reset only exact two known closed failed unit states afterward.
Docs alignment207human/27helpers and git diff --check PASS; source1361/gate17/
native23 unchanged. Required normal/dedicated acceptance remains incomplete.
Checkpoint157 `.scratch/web-006-source17-current-state-v157.json` SHA2561fbc189006f548046555cbcfd44f6c8ad7b2ca58cbceb43da205d9735c066ad7.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint158 update2026-10-23: exact retained created-container and six-secret failed27 cleanup PASS; no app restart or acceptance.

Initial secret cleanup-v1 bf497e29/130178bytes, protected81f165c2/28608bytes
FAIL before removals: account inventory correctly finds2new retained containers
in addition to3historical audits.3536268/start428120734 reaped/gone1.618312s;
removals[]/no secret change. Original failure stays retained. Readonly container
metadata-v1 a941bc6b/protectedb5cbd0d7 FAIL bounded Go-template inspection before
any result/container action;3536718/start428134439 reaped/gone1.347474s.
Separate default-inspection metadata projection-v2 1b337446/160848bytes,
protected2b787a54/55803bytes PASS0;3536910/start428140982 reaped/gone2.277219s.
Only whitelisted metadata is published; raw diagnostic stays root/private.

Worker6d34f753fe226ec95905f312350ae8e60640fcc3078ac00b676d21cfd6a18192 and
Caddy6420cd4cde7c85273f5b52dd3a6552c05e9d84ef540c767a0a351fa09dd3dc23
are CREATED/never started, PID0/RunningFalse/zero StartedAt/FinishedAt, no matching
cgroups in408scanned entries. Original17generation/runner/watcher remain gone.
Actual creation times, protected deployment image identities, rootless role labels,
fixed command/worker invocation and Caddy's2exact current secret IDs match this
failed cohort; worker has no secrets. No live3CID proof is inferred.

16local forged-identity/live-state/creation-window/secret/cgroup/no-force tests
PASS1.68s; held1361source196inputs preflight PASS18058bytes. Actual exact-ID
container retirementa9131457/166630bytes, protectedd4c76220/59695bytes PASS0;
3537507/start428163615 reaped/gone3.371165s. Both original nonforced per-CID
removes return0/reap, exact exists returns1. Original metadata retained;3old
audit CID/name/complete stopped-state/no-secret checks passed before effects
and remaining3IDs/names preserved. No secret/service/policy action.

36local failed-secret tests PASS1.72s, lint and held1361source199inputs preflight
PASS17925bytes. Separate cleanup-v2 2a6b8d04/187904bytes, protectedf827b20c/
78149bytes PASS0;3537726/start428169624 reaped/gone4.501268s. Holds original
pre-removal refusal and exact created-container retirement; original secret
store/IDs still match metadata witness. All6per-ID removals return0, final
empty0/unknown0. No force/all/ignore/name-only deletion or normal lifecycle
acceptance; original observer False/payload UNKNOWN remains.

Next provision ONLY absent /etc/hfcache/containers root0755 and empty client.toml
root0644 real mount placeholders; preserve existing credential directory/modes
and original lock identities. Then ONLY exact worker964a4b5a/status126 and
Caddy63a6976a/status1 failed states reset, fresh metadata/baseline/cohort.
Installed bytes/control27/source1361/gate17/native23 unchanged. Strict13role
closure remains NOT accepted until separate known-state prep; no app replay.
Checkpoint158 `.scratch/web-006-source17-current-state-v158.json` SHA256905e55d9970c5486facf153c3a5b8993193ee8c33aa5de8ee80af4335ce8f43e.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint159 update2026-10-23: ONLY two missing empty root-owned placeholders provisioned; exact failed user-state prep restores strict fixture closure.

13local plan/closed grammar/real-exclusive-no-overwrite checks PASS5.88s after
unit input normalization from metadata-only absence to traversal-record format.
Inert compile/warnings/one-entrypoint/unknown-global audit PASS. Held1361source
202inputs preflight PASS16761bytes. Actual placeholder prepa8783fda/286894bytes,
protected05669f45/169120bytes PASS0;3538455/start428198362 reaped/gone1.361200s.
Exactly two exclusive effects: empty client.toml inode78602581/root:root0644 and
empty containers directory101851392/root:root0755, ordinary inherited etc_t SID.
Host and ORIGINAL pause see identical new inodes. All18fixed source metadata
remeasured; existing3locks and credential directory full9/SIDs unchanged. No
existing leaf overwritten, credential permission broadened, service/reset/secret
or kernel action. Runtime :z metadata from actual prior attempt is measured as
current; earlier full9 remains historical.

5actual pin/cohort/exact-argv checks PASS1.69s; held1361source205input preflight
PASS16003bytes. Actual known-state prepfa4284a5/146288bytes, protected181e7dc9/
35937bytes PASS0;3538875/start428213082 reaped/gone3.328279s. Holds original
failed27 generation/journal/17gone children, exact6ID cleanup and current2target
provisioning. ONLY exact user964a4b5a/worker126 and63a6976a/Caddy1 failed states
reset-failed in one fixed command. No start/restart/replay. Actual13fixed roles
inactive/PID0,4cgroups empty,5endpoints refused PASS. Additional rootless Caddy
127.0.0.1:8443 also actually refuses ECONNREFUSED111. Source1361 unchanged.

Next fresh baseline normal-v3 binds current18path metadata plus exact new
cleanup/placeholder/closure receipts; same authority26/control27/source17 and
installed image/package retained. New observer/runner/workspace-v3 and new
generation, no old handles replay. Required rootless normal browser/lifecycle
and dedicated isolation/fault checks remain pending. Native23/gate17 unchanged.
Checkpoint159 `.scratch/web-006-source17-current-state-v159.json` SHA256b8b387f111f794317aeb38e17064db6f0ef100cfe7d3d9f499577b8a6dc74e20.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint160 update2026-10-23: fresh current18path baseline normal-v3 PASS; new rootless28 paired cohort prepared.

Baseline rootd02a4196 retains native23 and authority26/control27 prerequisites,
adds exact current cleanup/placeholder/closure pins and remeasures all18path
full9/SIDs after prior legitimate engine :z effects. Lint and held1361source
207input preflight PASS16459bytes. Actuald46d35b0/137568bytes, protectedCOMPACT
b0f1d98c/19915bytes PASS0;3539200/start428223521 reaped/gone1.579389s. Actual
empty0/unknown0/complete store unchanged, roles quiet, all held current repair
records/native prerequisites rejoined/closed. No app/secret action or acceptance.

New observerd3319844/runner-template6a00eefd/coordinator92a216e7 binds new
baseline, current3repair records and original failed27 handles freshgone. Same
authority26/control27/manifestc67348b5 and unchanged installed artifacts reused;
normal-v3 WORK/ARMED/workspace and future generation are new. Original PUB23
functional wrapper remains with explicit current manifest; original observer
atomic ARMED and2runtime bindings/EOF/reap ownership remain.35local exact
receipt/body pin/unknown-global/EOF/overflow/guard regressions PASS3.98s, leaf
lint PASS. Callerc3aaa8be held1361source212inputs preflight PASS48835bytes,
2100s original SSH EOF budget retained. PREPARED ONLY, not yet invoked.
Next invoke exactly once; built UI through shared Caddy/all3engines,6ID/3liveCID
normal ownership, strict postrun and dedicated isolation/fault/lifecycle remain
pending. No old failed generation/observer/operation replay.
Checkpoint160 `.scratch/web-006-source17-current-state-v160.json` SHA25648eeaabb29f8098fc09c510c8920dcfef2658bb7e8ddf23ff4e5ea60c72dc813.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint161 update2026-10-24: worker actually starts/notifies ready; fresh rootless28 cohort FAIL at API protected credential source. Exact namespace metadata verifies fixture ownership error without payload read.

Actual rootless28 2662f2c6/154606bytes, protected3a59aa67/40424bytes FAIL1;
3539614/start428237250 reaped/gone24.594826s. Original watcher117566/
start29120302 and runner117567/start29120327 reaped/gone. No SUMMARY/browser
cases. New generation627c7a836d2f4d399c830ae9e530ebf0 stopped/containers/ready
empty; all20original process pairs now gone.8original inode gate PASS; no
delivered gate. Observer False/payload UNKNOWN preserved;6NEW secrets retained.

Readonly diagnostic25c047d3/195268bytes, protectedaae4638c/78421bytes PASS0;
3539932/start428247858 reaped/gone1.335145s. Both earlier generation records
remain exact. Actual worker98448c116cd749978305f063ec5c470f starts/notifies READY
and stops normally. API117783/invocation89549069449940bb8eb195d8aa8f53fd/status10
prints HFAPI003. Caddy117784/invocation7345d69ffe324acea168fb0d5a4d8a9b/status2
occurs during early cleanup. Pasta emits no-nameserver warning; independent
Caddy cause remains unproved. Both current failed units PID0/cgroups empty;
strict13role closure NOT accepted. Fixed real placeholders now exist.

Current docs explicitly require rootless Basic record0400/0600 owned by the
actual service identity mapped to API981 (web-ui/deployment.md97). Fixture
controller instead writes host-root0640. New actual unchanged-image/keep-id
metadata probe uses no network/secrets, capless/NNP/read-only /etc/hfcache bind,
O_PATH plus readable-open metadata and the ORIGINAL installed credential reader.
Its os.read guard forbids payload reads; original reader raises HFAPI003 before
any payload call. Actual3b8038dd/155593bytes, protectedb3583462/38823bytes PASS0;
3541264/start428301751 reaped/gone3.198363s. Inside EUID/GID981/groups[981],
SAME inode118606297/221bytes/0640 has UID65534/GID981.0payload reads. Passed
probe CID35127297145ffa96149e5f1f05ac005d11ef735d7a9a0d5b28fa857ffed17bac
exits0/PID0/no secrets; original metadata retained and exact nonforced retirement
passes. No actual application role restarted, credential file read/changed,
policy/SELinux change or product guard bypass. All failed28 resources remain.

Next private fixture controller writes ONLY rootless Basic record as actual
mapped hostUID983/0400 per existing contract; native remains root0640. Its
original label/active-kernel helper-denial gate stays. Source review also finds
Type=exec API/Caddy are inspected immediately; bounded read-only cohort polling
will precede delivered-secret gate without any service-start replay. These are
fixture corrections, not a relaxed product credential guard/new runtime source.
Before new authority, reconcile failed28 current container/secret metadata and
perform only positively owned exact-ID cleanup/known-state prep. Required normal
and dedicated acceptance remains pending; source1361/gate17/native23 unchanged.
Docs alignment207human/27helpers and git diff --check PASS.
Checkpoint161 `.scratch/web-006-source17-current-state-v161.json` SHA256dc083a10fc791f3a84b09f4bd1d8c4f4db93c3270215772c5909ffba581b165f.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

WEB-006 checkpoint162 update2026-10-24: failed28 exact6ID cleanup and known-state prep PASS; corrected private controller28 remains inert/unpublished.

Readonly metadataa58d570d/187042bytes, protectedd485c90e/66887bytes PASS0;
3541968/start428329571 reaped/gone2.863852s. Actual6IDs/unknown0/complete store
unchanged/original payload inode gate match. Account inventory has ONLY3known
historical audits; application containers from failed28 are already absent.
36local failed28 identity/time-window/known API10+Caddy2 tests PASS1.74s, lint
and held1361source225inputs preflight PASS17653bytes. Actual cleanupab4084c4/
200921bytes, protecteda455e570/77668bytes PASS0;3542895/start428365669 reaped/
gone4.508848s. All6exact per-ID removals0, final empty0/unknown0; original3
stopped/secret-free audits preserved. No normal6ID/3liveCID acceptance supplied.
Observer False/payload UNKNOWN remains, all20original generation pairs gone.

5pin/cohort/exact-argv tests PASS1.69s; held1361source228input preflight
PASS16118bytes. Actual known-state prepc68521bf/159388bytes, protecteda58f046e/
36999bytes PASS0;3543549/start428392308 reaped/gone3.289065s. Holds failed28
generation/diagnostic/cleanup, actual passed owner-map probe and standing
placeholder receipt. ONLY exact API89549069/status10 and Caddy7345d69f/status2
user failed states reset-failed. No start/restart/policy/credential action.
Actual13role/4cgroup/5endpoint strict closure PASS; rootless8443 also refused111.
Original70549pause/NFS guard3/source1361 unchanged.

Private controller28 prototype6c276cb7 prepares mapped rootless Basic file
UID983/0400 per existing guide; native remains UID0/0640. Original secret label/
active-kernel helper-denial gate uses corresponding Basic owner; other7original
source checks remain. Added bounded90second read-only initial rootless cohort
polling for existing Type=exec starts; failed units refuse, first timeout error
is retained, no service start/restart replay.5local metadata/native-preservation/
read-poll/failed-unit/budget/method-delta tests PASS1.84s, lint PASS. AST confirms
ONLY credentials, secret_label_gate and start methods change, plus one new read
wait and pure metadata helper; source/API/product guard/image/policy unchanged.
Prototype is INERT, not published/installed/accepted. First formatting-dependent
local edit refused before writing; AST-selected prototype and tests pass.

Next authority27/control28/generations28, preserving209old immutable inputs and
current rootless aliases; only new private controller/marker/launchers/manifest/
scoped sudoers, reuse existing public profile records and installed bytes.
Hold actual owner-probe/cleanup/closure/placeholder proof, then fresh baseline/
live paired normal cohort. No old failed app/proof replay or required test skip.
Normal rootless and dedicated isolation/fault/lifecycle acceptance still pending.
Checkpoint162 `.scratch/web-006-source17-current-state-v162.json` SHA2565dede164aa6c028a9da1b622b7e405aeb77aac535388ba449687a84efa1bbf99.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/live Cockpit untouched.

- 2026-10-24: Checkpoint163 records actual corrected authority27/controller28 publication and fresh baseline PASS; original new rootless29 cohort running with exact current bindings. Previous failed evidence preserved; required normal and dedicated acceptance remains open. Source17/gate/native23/UBI10 image unchanged; no production action.

- 2026-10-24: Checkpoint164 preserves actual rootless29 prestart failure and successful read-only diagnostics/strict closure; remaining private Basic publication guards corrected inertly and exact old-inode preservation prepared. Normal/dedicated acceptance remains open.

- 2026-10-24: Checkpoint165 records actual authority28/controller29 publication PASS, oldBasic inode preserved metadata-only/NOREPLACE, fresh empty baseline PASS and original rootless30 cohort running.218old inputs/source17/native23/UBI10 image unchanged; normal/dedicated acceptance remains pending.

- 2026-10-24: Checkpoint166 records real8original/5delivered gates and6ID3liveCID ownership PASS without payload reads; rootless30 still FAIL atAPIHFAPI003/502, original stop refuses knownnsfs before effects. Actual readonly namespace/CID attribution passes; exact original cohort drain now running. Full acceptance remains pending.

- 2026-10-24: Checkpoint167 retains partial original drain (39pairs gone, exact API CID removed, sole original failed unit state remains). Actual same-image Basic leaf metadata/read-open succeeds but parent O_RDONLY open EACCES13; original guardHFAPI003 before0payload reads. Select narrow O_PATH directory traversal correction after source17 owned cleanup, then new gate/installed proofs; no MAC grant.

- 2026-10-24: Checkpoint168 closes failed30 owned cleanup: durable secret-labelled-before-bytes opaque backup, six exact removals/finalempty, sole originalAPI failed-state reset and actual13role/4cgroup/5endpoint strict closure PASS. All39+2original handles gone; old failed evidence retained. Proceed narrow O_PATH correction and new source gate/installed proofs, no security grant.

- 2026-10-24: Checkpoint169 implements narrow O_PATH directory traversal with every existing leaf/ACL guard retained and no security grant.114ACL/adversarial +150Basic/MCP tests PASS; human/contracts/decision152 align.1361source18 freeze/8exact changes; original strict gate18 running. Source17 proofs remain historical; fresh installed acceptance still required.

- 2026-10-24: Checkpoint170 retains gate18 type failure (test Path.chown), corrects only test to os.chown, pyrefly/18tests PASS; source19 frozen and original strict gate running. Host-only two-field0.2.6 fixture projection PASS/all108package bytes frozen19; private bounded stock netns guard4 INERT/30tests PASS. No guest effect/new installed acceptance.

- 2026-10-24: Checkpoint171 records actual strict gate19 PASS7750Python/2786frontendunit/2846component, wheels/Cockpit/build/Chromium/read fixture, unchanged1361snapshot. Actual new source19 guest transfer PASS/oldsource17 full9 preserved/strict closure. Controller30/source19 versions006/007 prototype INERT. New installed native/rootless and dedicated acceptance remain pending; no production action.


Checkpoint172 (2026-10-24): SOURCE19 remains frozen at1361files/snapshot586acd13;
no canonical edit after green gate19. Canonical artifact06496e45 and explicit
fixture0.2.6 artifact4867a0a7 actually build PASS16.57s/17.19s, each with two
byte-identical UI builds. Fixture wheel0dd17b83/500326B, manifest0144a394;
measured fixture Python reports0.2.6/all108package leaves match frozen19.
Canonical product version remains0.2.2. Shared API/UI image build actually PASS
27.70s, image dedf864e4c3e0892f1af1f7509d1041f39c4a042a925b96c9f8ec9f545792744,
receipt a254127e. Both FROM stages remain pinned UBI10micro87a27d71. No separate
frontend image/server or runtime Node introduced; runtime absence/installed
image audit remains pending. Actual OCI export ebbdbea7 PASS5.32s, original
base/Caddy archives reused exactly; original bounded OCI transfer is running,
not yet accepted. No guest image load/application start inferred from export.

Actual quiescent staging readiness9efcc49e/protected64f221ea PASS6.02s preserves
all3original selectors and mapped Basic inode118570589 with metadata-only
RENAME_NOREPLACE; no secret/master-key body/hash read. Actual control29 has224
immutable input rows. Strict13role/4cgroup/5endpoint closure and empty secret
store hold.9local actual rename/collision/metadata checks PASS1.82s.
Native preparation1 ce6074a0/79d2a881 FAIL before installer on the pinned old
17,725,440B source archive exceeding8MiB; preparation2 1efc17be/8d019f87 FAIL
before installer on restorecon-nRFv7058B. Both partial scopes/receipts retained.
Readonly label diagnosis383eda0c/642bfad0 PASS1.37s proves52differences limited
to old stopped0.2.5 release SELinux user unconfined_u->system_u, identical
object_r/usr_t/s0; target0.2.6 absent, captured source19 retained.

Native attempt3 original unchanged install-release.sh --no-switch --with-mcp
ACTUALLY returns0 in16.63s, PID121406/start30006482. Collector223b8b74/a596faac
then FAILS its process-record shape check before post-install verification;
that receipt remains failed. Installer is NOT replayed. Separate read-only
completion0a0693e1/protected05700295 PASS5.38s verifies original child gone,
installed0.2.6/all108package leaves match frozen19, all224old inputs and old
readonly108package full9/hash/SIDs preserved, captured1361/private and public
source unchanged. Exact52standard SELinux user normalizations preserve43regular
file hashes and all bytes/UID/GID/mode/inode/mtime/nlink; only allowed SID-user/
ctime change. No further label correction remains; kernel45bb34e8/Enforcing
and owned NFS identities unchanged. Native UI/server candidate, image runtime,
new native/rootless browser and dedicated isolation/fault/lifecycle acceptance
remain pending. All application roles stopped; original selectors/Basic absent
and preserved, stock rootless secret store empty.10new preparation guard tests
PASS1.88s;7OCI destination/network-mount fault tests PASS1.73s. These tooling
checks do not replace installed functional acceptance. WEB006 in progress/
uncommitted; AUTH-08/HOST-01–03 pending, WEB007–026 not started. Production
unchanged. Checkpoint172 ignored state records exact current artifact identities.


Checkpoint173 (2026-10-24): actual OCI transfer4f374b0c PASS3.35s/all4home
files full9/hash/SID rejoined; all original copy children reaped/gone. Fresh
SOURCE19 UI packet837769b1/1,269,760B has8fixed members, bound codecbafa3ddc;
9actual duplicate/foreign-header/corruption/version guard tests PASS1.75s.
Native UI staging8f363c78/protectedf943f8b7 publishes6exact UI files plus
native server candidatebd9f1415 (ONLY web.asset_root/manifest_sha256 changed)
then FAILS the readonly asset inspector: original installed source_path raises
HFAPI003 because the inspector omitted CREDENTIALS_DIRECTORY. Original receipt
remains failed; no UI/config/installer restaging, application or Caddy start.
Separate readonly completiona32df7a2/protected8052120b PASS3.34s with exact native
credential-directory SPELLING only, no credential contents loaded. Actual
installed0.2.6 capture validates manifest0144a394,5members/1configured prefix
shell and wire891b5b45. All6UI and108package full9/hash/SIDs stay exact; candidate
is not installed/selected. Strict closure, empty secrets, preserved aliases and
master-key metadata hold.

Original stock UID983 image load PID121892/start30123477 actually returns0 in
3.83s. The surrounding collector7c874a2f/protected640bbf9b FAILS on667B nonempty
stderr before image inspection; failed receipt remains. Separate readonly
completion6e161f2f/protected040c7b70 PASS2.84s proves all9stderr lines are known
image-copy progress prefixes, original load PID gone, exact appdedf864e/Caddy
fa2a5634/base34f13727 and genuine pinned micro layer prefix, archive4full9/
hashes/SIDs,3old stopped audit containers, empty secret store, exact original
NFS/kernel/Enforcing and13role4cgroup5endpoint closure. The image load is NOT
replayed; Caddy/base not reloaded, no container/service started. Keep both
observed image sizes: build-host204760968B, guest204761022B. Runtime tool/module
absence and actual package/UI/UID mapping audit remain pending, as do new
native/rootless shared-Caddy browser and dedicated isolation/fault/lifecycle
acceptance. No partial proof closes AUTH-08/HOST-01–03; WEB006 remains in
progress/uncommitted, WEB007–026 pending. All guest lanes idle/closed here;
production unchanged. Checkpoint173 ignored state owns exact current identities.


Checkpoint174 (2026-10-24): NEW source19 image runtime audit original attached
process122213/start30175964 exits0, actual container outer122237/start30175989
runsPID1/inner981 mappinghost983, all108package+6UI hashes match,35named tools
and8modules absent (including Node/npm/pnpm, compilers, rpm/dnf and pip/uv).
Actual E/P/I/A/Bnd capabilities0, NNP1/seccomp2, immutable root/network-none,
only owned readonly gate/private tmpfs and no credential mounts. Original probe
f3f99a7d/12188B retained. Original collectorc7555247/protected12502aa6 FAILS when
Podman normalizes ONLY Mounts[0].Mode Z->empty at start; all substantive mount
fields/RO/source/options/propagation identical. Do not promote that receipt.
Separate completiondc3f88f1/protectedf18770c9 actually PASS3.37s, verifies raw
original probe/attach0, all108/6/35/8 and real UID/capability evidence, exact
Mode-only normalization, original attach/outer gone and cgroup closed. It then
retires ONLY original positively stopped/exit0/noSecrets audit CIDec8cc5bf with
nonforced exact-ID rm, proves absence1, original3stopped audit CIDs unchanged,
secretstoreempty, selectors/Basic absent/preserved, kernel45bb34e8/Enforcing,
owned NFS and strict13role4cgroup5endpoint closure. No audit, image load or
native installer is replayed. Actual shared API/UI image dedf864e now has
fresh runtime ancestry/absence proof on pinned UBI10micro; browser Debian/Node
tooling remains unshipped and separate. This is not installed helper/API/worker
role, new native/rootless shared-Caddy browser or dedicated isolation/fault/
secret-lifecycle acceptance; those remain mandatory and pending. WEB006 stays
in_progress/uncommitted; AUTH-08/HOST-01–03 pending and WEB007–026 not started.
All guest calls closed, app lane quiescent; production untouched. Next source19
browser/readonly package environment, rootless007 and authority29/controller30.


Checkpoint175 (2026-10-24): actual SOURCE19 environment6ab3f878/protected4767d314
PASS9.55s. Fresh descriptor-anchored bind/remount exposes the installed native006
package at new source19 provisioning path, statvfs/mountinfo readonly and same
108inodes/full9/hashes/SIDs; original source is root-owned and unchanged. Actual
UID1000 import resolves exactly that target and reports0.2.6 (PID122429/start
30241508 exited). Explicit0.2.6 wheel0dd17b83 copied/hash-verified.194public browser
files/50directories freshly staged/prelabelled/rejoined from unchanged original
browser tooling plus7captured source19 drivers and new fixture inventory. All
1361frozen source19 tracked leaves unchanged; only intended .scratch direct-entry
root transition. All old sources preserved, helper-key metadata only, exactNFS/
kernel/Enforcing, empty secret store, selector/Basic absence and strict13/4/5
closure. All original executor handles reaped/gone. No browser, API/helper/worker
or Caddy service started; this is environment staging only, not new normal or
dedicated functional acceptance. Next rootless007 original stage/render with
auditeddedf864e, then authority29/controller30, retaining224old rows. WEB006
in_progress/uncommitted and AUTH-08/HOST-01–03 pending; WEB007–026 pending.
Production remains unchanged. Checkpoint175 ignored state owns current identities.


Checkpoint176 (2026-10-24): actual rootless007 original stage/render03366bda/
protectedb507acaf PASS5.61s. New /opt/hfcache/releases/0.2.7 has28captured input
files, complete6helper copies/explicit host-helper opt-in, exact supported Basic/
web tables and test TLS default-SNI overlay. Original stage() and _verify_stage()
execute unchanged; index3879aa56/runtimeb3563b3a/server759807c5 bind host983,
audited shared API/UIdedf864e, unchanged Caddyfa2a5634 and UI0144a394/software006.
Actual full image-build receipt remains locally bound by FD/hasha254127e; a
precisely checked1215B selected-field document is published in guest with that
explicit provenance, not labelled as the full receipt. Native108readonly package
FDs,1361public source bytes/full9, selector/Basic absence, empty secrets, kernel/
Enforcing/NFS and strict13/4/5 closure preserved. No image load/audit/native
installer replay, application/Caddy start or policy/credential grant. Independent
new profile bindings and authority29/controller30 remain required before actual
application/browser tests. All calls closed. WEB006 in_progress/uncommitted;
AUTH-08/HOST-01–03 pending, WEB007–026 pending; production untouched.


Checkpoint177 (2026-10-24): original protected index preparer actually PASS
44c9920c/protected072904f1 in3.16s against new native006/rootless007 files.
Native indexf1774770 (222actual authority files)/policy8fd0496b; rootless index
bf09c14d (43files)/policyed6fa6f4. Index source snapshot9daf2d5a truthfully names
the actual two-field006fixture build, with genuine parent07d10e0/dirtytrue;
canonical gate19 snapshot586acd13 remains separately recorded. SELinux receipt
79f3db35/kernel45bb34e8 unchanged, no module/type/permission grant. Both policy
documents preserve EXACT old6bits: configurationtrue, all otherfalse. Each
exclusive own temporary selector is fully verified over original preparation
and preserved via exact inode/target/SID RENAME_NOREPLACE; both selectors kept
as evidence, current absent again. No global deployment/policy/credential
installation, application start or key/secret payload/hash read. Native readonly
108package retained, strict13/4/5 closure and empty secret store PASS. All actual
child handles closed; production unchanged. Next authority29/controller30
publication/manifest using actualsource19environment/profiles while preserving
224old control rows, then new installed native/rootless/shared-Caddy and
dedicated isolation/fault/lifecycle acceptance. WEB006 in_progress/uncommitted;
AUTH-08/HOST-01–03 and WEB007–026 still pending. Checkpoint177 records exact pins.


Checkpoint178 (2026-10-24): actual separate readonly source19 authority29
completion PASS cb644dc5/protectede37b3297 in3.70s.
Original preparation OSError and subsequent 8MiB tool-size refusal remain failed;
separate streaming two-FD anchors retain full9/hash/SID checks without changing
RLIMIT. Publication then actually succeeds, but its final ancestor guard refuses
the intentional own .scratch0755->0700 narrowing; that original receipt stays
failed. No publication replay: readonly completion rechecks the exact recorded
mode/ctime-only transition,108native package/194browser files/50directories,
all21published files, master-key metadata only, actual installed validator and
visudo. Control30 4a6068e0 has240rows with all224old rows preserved in order;
manifest2e5f9473, wrappera9a552e2, controllerdde9de38 and launcher672262b4 remain
exact. Actual834FDs/1024soft/32reserve, no limit change. Current/global bindings/
Basic absent, secrets empty, strict13role4cgroup5endpoint closure/kernel/NFS/
Enforcing preserved. All original executors closed; no application/Caddy/browser
start or new normal/dedicated acceptance. Next fresh native24/rootless31 through
real shared Caddy, then required dedicated isolation/fault/secret-lifecycle tests.
WEB006 in_progress/uncommitted; AUTH-08/HOST-01–03 and WEB007–026 pending.
Production untouched; no Cockpit retirement. Ignored checkpoint178 owns full pins.


Checkpoint179 (2026-10-24): actual native24 original checker122866/start30584912
returns1 after168.49s; wrapper3596590 closed170.69s. Original failed protected
receipt3d24dac1 and generation3e3ebc4e10464f3ab7eb87e3693fa60d retained unchanged,
no SUMMARY/no acceptance. Baseline and helper-down actual3engines PASS24host
assertions, same-Caddy trusted/untrusted pairs retain their own proofs; original
helper restart preserves API/worker/Caddy before the next browser phase. In
restarted untrusted phase Chromium/Firefox prove certificate refusal, but WebKit
returns ambiguous navigation cancellation rather than a certificate signature.
The strict validator correctly refuses it; no cancellation is accepted as TLS
proof. All3browser engines/that CID drain, original generation stopped/pausedfalse,
all recorded application PID/start pairs gone,13role4cgroup5endpoint closure and
empty secretstore PASS. Readonly diagnoses preserve raw report and metadata;
Basic remains root:983/0640 inode118619972/secret_t, payload/hash unread. No replay,
production changes or case completion. Next strengthen explicit blank-page
readiness and single-navigation transport evidence, preserving certificate-
specific requirement/no response/no auth/no retry, then fresh source gate/fixture.
Native24 failure remains historical; new native/rootless and dedicated/lifecycle
acceptance are still mandatory. WEB006 in_progress/uncommitted; WEB007–026 pending.


Checkpoint180 (2026-10-24): narrowed native24 failure to real WebKit untrusted
navigation cancellation after baseline/helper-down pass; no ambiguity accepted.
Source20 changes ONLY functional driver, its guard tests and human troubleshooting.
It settles the initial blank frame before one HTTPS navigation, records the exact
failed main navigation transport, and requires an actual certificate signature
with no HTTP response. Navigation and transport diagnostics stay distinct and
sanitized; no retry, TLS bypass or generic cancellation category.10focused driver
metadata tests, full web lint/format, docs207/27 and diffcheck PASS. No new runtime
dependency, permission or architectural grant; original certificate-specific
contract retained. Frozen1361source20 snapshot3c50c138/capture55a41976, only these
3changes from19; all108runtime package source and UI build inputs unchanged.
Explicit two-field006fixture projection11a82a1a/snapshot5c3c8e44 PASS, canonical
version002 unchanged. Actual strict gate20 started outer3598949/start429776482,
runnerc847585e, original retained command scripts/check.sh --require-web
--require-cockpit; still RUNNING/no outcome inferred. No source changes after20
freeze. Gate19 remains historical PASS. No source20 guest transfer or application
acceptance yet; source19 native24 FAIL remains unchanged. Next actual gate20
closure, new source20 disposable source/browser bindings, native25/rootless31
shared-Caddy and dedicated isolation/fault/secret-lifecycle acceptance. Basic
native root:983/0640 must be preserved metadata-only before rootless owner change.
WEB006 in_progress/uncommitted, AUTH-08/HOST-01–03/WEB007–026 pending; production
untouched. Full ignored checkpoint180 owns current receipts and execution handles.


Checkpoint181 (2026-10-24): source20 strict gate still RUNNING; actual backend
7750PASS/52opt-in deselections,3locked wheel profiles and Cockpit572PASS/0skips.
Do not infer the complete frontend/build/realAPI gate outcome yet. Source20
canonical1361snapshot3c50c138 remains unchanged. Actual local artifact comparison
3d5097bd/17110B verifies all108runtime package leaves,46actual consumed UI build
inputs (inventory33271a75), self-version metadata and existing006UI0144a394 are
unchanged from source19-built artifacts. Reuse original installed006/rootless007/
shared UBI10microdedf864e artifacts with their GENUINE source19 build provenance
9daf2d5a, preserving original profilesf1774770/bf09c14d and policy bytes. Source20
5c3c8e44 identifies the changed test fixture, not a fabricated new artifact build.
New source20 source transfer/private scratch/readiness/environment and authority30
are INERT/UNBOUND preparations only. Existing native24 failed Basic root:983/0640
inode118619972 and native aliases must be NOREPLACE preserved after transfer,
without reading/hash of payload or changing old-owner guards.22actual local
NOREPLACE/collision/metadata/controller31/guard4 tests PASS7.36s/0skips; controller31
f8e9fbfc changes only repository/control/generation bindings, all function/class
ASTs match30. No source20 guest call/application start, no new browser/dedicated
acceptance. Next close gate20, bind/execute new transfer once, preserve originals,
stage source20 environment, publish authority30 keeping all240old control inputs,
then fresh native25/rootless31 and dedicated isolation/fault/secret lifecycle tests.
WEB006 in_progress/uncommitted; AUTH-08/HOST-01–03 and WEB007–026 pending;
production unchanged. Checkpoint181 records actual pins and next execution handles.


Checkpoint182 (2026-10-24): actual strict source20 gate PASS
c8fd9d01/log0aecaa96 in1257.58s, original child3598952/start429776501
and outer3598949/start429776482 reaped/gone.7750Python/52opt-in deselections,
3locked wheel profiles, Cockpit572/0skips,2786frontend units/2846components,
10functional-driver metadata tests, lint/types/wire135definitions/build,
sandboxed Chromium startup and realHTTP/API React read fixture PASS.1361source20
snapshot3c50c138 unchanged; no required default skip or installed acceptance
inferred. Bound packet492aed15/36,321,280B, codec5a0fb397 and19actual archive/
corruption/foreign-scope/pin guard tests PASS4.32s.

Actual new guest transfer 26f57ab1/protected122f7832 PASS19.77s:
all1361new source20 files/hash/full9/SIDs verified, oldsource17 and oldsource19
all1361each preserved. Original failed native24 receipt/generation and all its
closed PID/start handles rejoined; current native006/Basic metadata only untouched.
Actual readiness 8eeabc18/089ef727 PASS4.33s: original
Basic inode118619972 root:983/0640 and3native aliases preserved NOREPLACE, stable
identity/bytes-size/SID except rename ctime. Payload/hash unread, no owner guard
bypass, absent current/deployment/policy/Basic and empty secrets/strict closure.
Actual environment 9bae0908/protected65c81843 PASS8.31s:
fresh readonly same-inode native006 package108leaves and UID1000 import;194browser
files/50directories including current source20 drivers, private0700scratch from
creation. Runtime comparison3d5097bd is actually checked against new1361source,
108package/46UI consumed inputs and installed UI0144a394, while preserving genuine
source19 build9daf2d5a/profile/artifact provenance. No reinstall/image rebuild or
service/Caddy start.776FDs/1024soft/32reserve, no limit change; source1361/keymeta/
kernel/NFS/Enforcing/originalpreservedBasic/strict13role4cgroup5endpoint closure
and empty secrets PASS. All original calls closed; production untouched.

Next bind new launcher from actual environment metadata and publish authority30/
controller31 preserving all240old control rows and exact old source19-built profile
bytes. Then fresh native25/rootless31 through real shared Caddy and dedicated
isolation/fault/secret-lifecycle acceptance. Native24 remains FAIL/no SUMMARY;
AUTH-08/HOST-01–03 pending, WEB006 in_progress/uncommitted and WEB007–026 pending.
Checkpoint182 owns full pins; no Cockpit retirement or production rollout accepted.


Checkpoint183 (2026-10-24): actual source20 authority30 publication PASS
69ff8293 in4.03s, original3619589/start429963632 reaped/gone. Controller31f8e9fbfc,
launcher1a671909, manifestcdc9a068 and wrapperc84c1c8f pass actual installed static
validation/visudo/controller load.247control inputs preserve all240prior rows in
order; unchanged genuine source19 build9daf2d5a/profiles retained separately from
source20 test fixture5c3c8e44.810FDs/1024soft/32reserve, no limit change. New scratch
0700 already set before holding child inputs; no ancestor mode mutation or late
rejoin exception. Key metadata only, preserved originals/emptysecrets/strict
13role4cgroup5endpoint closure/kernel/NFS/Enforcing preserved. No application
acceptance inferred from publication.

Fresh native25 original functional checker now RUNNING through source20 wrapper,
caller3e182f2f/root401f1318, original outer3620035/start429981414, session97406.
No result inferred; no parallel guest call while it owns the lane. It uses new
source20 TLS driver and source20 readonly package/browser inputs, original same
Caddy/native006 artifacts with correct build provenance. Original native24 FAIL
and all its handles/receipts remain untouched. Next close this original executor,
then actual postrun/normal-readiness and metadata-only preservation of its new
Basic inode before rootless31. Rootless and dedicated isolation/fault/secret-
lifecycle acceptance remains mandatory and pending. WEB006 in_progress/uncommitted;
AUTH-08/HOST-01–03 and WEB007–026 pending. Production unchanged.


Checkpoint184 (2026-10-24): source20 native25 actually PASS local0a22f1e8/
protected78d91d68; checker126591/start30864451 returns0 in325.75s, original outer
3620035 reaped/gone328.56s. Fresh SUMMARYa0b39391/generation9b05fac47df94fc896ead1e8ace427b1
contains4modes/3engines/33host assertions,0required retries/skips, actual normal
stop/cleanup_unknownfalse. Separate readonly postrun68187fbc PASS1.91s rechecks
all4same-Caddy trusted/untrusted pairs/12certificate-specific refusals, exact
single navigation/noHTTPresponse, all browser CIDs/init handles gone, original
application generation handles gone,8original/2delivered secret-label gates,
normal hygiene and same-instance API/worker/Caddy across helper loss/restart/
timeout. Normal-readiness codef9be35ef/18567B is bound from actual7records and
passes all held full9/hash/SID checks. No rootless or dedicated acceptance inferred.

Native25 original Basic inode118634654 root:983/0640/secret_t and3current bindings
actually NOREPLACE preserved09f60fc9; payload/digest unread, no owner override.
Fresh actual rootless baseline279799d2 PASS1.54s: metadata-only complete safe store,
zero IDs/unknown names, original pause70549 and normal native/authority30 proofs
rejoined. Rootless31 fresh paired watcher/original runner now RUNNING via original
coordinator3653559/start431059534/session25994; no outcome inferred/no parallel
guest call. Watcher9c9e2c5b,runnerb05afdf5,coordinator387722ce; actual source20/
authority30/control31 and genuine unchanged006/007runtime profiles retained.
All preparation compile/schema/binding/global audits pass before effects. Next
close original coordinator/children, reconcile real normal/TLS/live six-ID/three-
CID ownership/delivery/drain, opaque prelabelled backup and exact-ID retirement.
Dedicated native/rootless isolation/fault/secret-lifecycle proof still required.
WEB006 in_progress/uncommitted; AUTH-08/HOST-01–03 and WEB007–026 pending.
Production untouched; native24 failed run remains unchanged, no replay/promotion.


Checkpoint185 (2026-10-24): rootless31 actually FAIL de897ddd after75.04s;
original checker132293/start31942550 returns1/72.89s. API/worker/Caddy readiness,
8original/5delivered secret-label gates, real6ID/3liveCID ownership and3browser
untrusted-TLS refusal PASS as partial proofs. Baseline host status is unavailable
in all3trusted engines, no cases/SUMMARY accepted. Original generation2ad128d4
remains startedtrue/stoppedfalse; never promote/replay it. Readonly00bf4ff5 and
metadataebf25e38 prove all62original app PID/start pairs and coordinator/watcher/
runner gone,13role4cgroup5endpoint closure, only3old stopped audit CIDs with no
secret references. Separate exact-ID retirement24120791 PASS4.57s uses genuine
live ownership, complete opaque whole-store backup labelled secret_t BEFORE
bytes,6exact removals and final empty store. No blanket/name-only deletion,
production action or original generation rewrite. AVC query finds no owned AVC;
absence of an AVC is not permission proof.

Actual same UBI10micro image metadata probe under real container_t PASS4.13s:
original helper parent inode10829/runtime_t projects65534:981/0750. Readable
O_RDONLY directory open and original EndpointBinding._open_parent both fail
EACCES13, while O_PATH succeeds on EXACT same inode. No payload/binding read or
helper request; all metadata unchanged. Original passed diagnostic CIDe9ff4a8a
is positively stopped exit0/noSecrets, retired nonforced by exact ID and absent.
This narrows the rootless host-status cause without a permission grant.

Contract-first decision150/host administration/security/invariants/deployment/
troubleshooting align. Source21 changes client directory handles ONLY to
O_PATH|DIRECTORY|NOFOLLOW|CLOEXEC, preserving all ancestor/owner/group/mode,
attestation/binding-leaf/peer/lifetime checks.2new search-only regression cases
actually fail original client; corrected helper-client/protocol/status108tests
PASS8.12s. Lint/format/docs207/27/diffcheck PASS. No SELinux/MAC/DAC/capability/
systemd grant or runtime dependency. Frozen1361source21 snapshot827c1047/capture
e223625e has exactly8changes from20; no edits after freeze. Original strict
gate21 RUNNING, outer3655978/start431132735/session88837, codeea81b220; no outcome
inferred. Explicit two-field008fixture projectionba3012ea/snapshotdc1d3ff5 PASS;
canonical002 unchanged, new native008/rootless009 artifacts must carry corrected
client. Source20 native25 PASS remains historical, not new21 acceptance.

Next close gate21, new source21 artifact/image/guest staging, then fresh actual
native/rootless shared-Caddy browser and dedicated isolation/fault/secret-lifecycle
acceptance. WEB006 remains in_progress/uncommitted; AUTH-08/HOST-01–03 and
WEB007–026 pending. Guest app lane quiescent/secretstoreempty; production
unchanged. Full original handles/pins and blockers are in ignored checkpoint185.


Checkpoint186 (2026-10-24): source21 strict gate actually PASS1248.50s,
outer3655978 reaped/gone1248.71s; source827c1047/1361files unchanged. Actual
7752Python/52opt-in deselections,572Cockpit/0skips,2786unit/2846component,
21sandbox/10driver metadata,135wire/types/lint/build,207human-doc/27helper and
realAPI/browser smoke pass. Gate log889a4381; no installed acceptance inferred.

New canonical artifact710d9e07 and explicit008 fixtureda8738eb built; shared
API/UI image92c09797 retains both pinned UBI10micro FROM stages. Source21
transfer950426db and original rootless31 Basic/3alias preservation54c4c33f PASS.
Original native008 actor FAIL66c9add9 at readonly restorecon preflight BEFORE
installer, retains private1361source. Wrong-command readonly diagnostic stays
FAIL; corrected8cb5af24 identifies52old0.2.7 paths with only SELinux User
unconfined_u->system_u, same role/type/range/mode/owner. Exact52metadata-only
normalizationdf0cce03 PASS, no policy/permission grant. Separate first installer
actually PASS87fdfb20/24.70s, original3680671 reaped/gone, measured008/108package
files. No recopy/replay or failed-receipt promotion. UI local-v1 preflight refuses
stale snapshot before guest; corrected actual-v2 PASSb052b7d0/5.41s, six assets,
installed capture and native candidate only; original3680980 reaped/gone.

Actual OCI exportfad25c7f and prelabelled exclusive guest transfer PASS. Full
build95a9f77a/585688B separately uploaded/held for genuine rootless provenance.
Original image loadPASS7.59s, runtime auditPASSac7f6066/34.43s:108package/6UI,
35tools/8modules absent, real981->983 mapping,capless/NNP/seccomp/readonly/noNet/
noSecrets; actual micro ancestry. ProbeCIDf8598dc6 retired exact-ID/nonforced,
originalouter135702 gone/cgroupclosed,3oldstoppedaudits/emptysecrets preserved.
No source21 native/rootless application/browser or dedicated acceptance yet.

New environment projection original3681622/start431366568/session3616 RUNNING;
no outcome inferred/no concurrent guest call. Next close it, rootless009 staging,
new genuine profiles/authority31/controller32, fresh native26/rootless32 normal
and dedicated isolation/fault/secret-lifecycle tests. WEB006 in_progress and
uncommitted; AUTH-08/HOST-01–03 and WEB007–026 pending. Source20native25 PASS
remains historical; rootless31FAIL/stoppedfalse and all original failures remain.
Production/NAS/liveCockpit untouched. Full actual pins and original handles:
`.scratch/web-006-source21-current-state-v186.json` SHA256 833acc11e33a3f42176916ee1a371fae33059cfabbb660330f07d9a3de1f9271.


Checkpoint187 (2026-10-24): new source21 environment actual PASSa7e06dc0/
17.13s, original3681622 reaped/gone. Same-inode readonly108package projection,
realUID1000 installed008 import,194browser files/50dirs and all old source
1361full9/hash/SID records rejoin. Rootless009 actual stage/render PASSa18ce1d4/
6.39s, original3682269 reaped/gone; actual uploaded full585688B build receipt
95a9f77a is held with inode/hash/selectedfields. No app starts or selector switch.
Actual protected proposals PASS5.62s, original3682582 reaped/gone: genuinely
new native008/rootless009 build snapshotdc1d3ff5, original configuration-only
permissions retained, temporary own selectors preserved and current absent.

Before authority publication, static review identifies rootless31 stop-harness
failure: it inspects containers after real services auto-remove them. No absence
can prove exit0. New controller32v2 is being prepared/reviewed to arm exact
original-CID wait observers while live, then perform one normal stop and retain
actual exit statuses/reaped handles, originalPID/cgroup drain and exactabsence.
No product runtime/unit/permission or canonical source change. V1f0 retained;
v2/authority31 not yet published or executed, no outcome inferred. Existing
rootless31FAIL/stoppedfalse is never rewritten. Guest app lane is quiescent,
secrets empty; native26/rootless32 and dedicated isolation/fault/lifecycle proof
still required before WEB006 commit. Source21 gate remains green/frozen, all
required cases pending; production untouched. Full actual pins/handles:
`.scratch/web-006-source21-current-state-v187.json` SHA256 2e1e1d21cf48779b012652d1ca394849027c3be9ae4f264f5c5f6cb2cb9f4de0.


Checkpoint188 (2026-10-24): reviewed controller32v2 8adfaaa7/117990B is
actually published and loaded. Six real local child/pipe tests PASS0.607s,
separate review confirms fixed grammar/no force/replay/payload reads. Exact
original3CID waiters arm whilelive, original normalstop happens once, real
waitstdout0/CLI0, exactCIDabsence1 and originalPID/cgroup drain are required;
collector preserves firstfailure and retains pipes until actualEOF/reap.
Actual stock Podman/rootless normal acceptance remains pending.

First authority actor FAILb478a93b before any PUBLIC/controller/control/
generation/sudoers publication: newWORK only, error-directory parentSID check
did not exempt exact protected existing ROOT unconfined_u:usr_t. Original
failed scope/5evidencefiles retained. New independent preparation-v2 validates
that failure and alltargetabsence; exact ROOT fd/full9/owner/mode/SID guard,
labels only the NEW EMPTY error directory. No parent relabel or product change.
Actual authorityv2 PASS3.75s, original3686158/start431529295 reaped/gone:
264control inputs preserve all247old rows in order; installed validator,
controllerload/visudo, fullpackage/browser/source/label/kernel/NFS/strict
closure pass. Newprotectedreceipt
`/opt/hfcache-web006/fixture-authority-v31-preparation-v2/RESULT.json`.

Fresh source21 native26 original functional run NOW RUNNING through real
installed008/sharedCaddy/3browser tooling. Original outer3686310/
start431533207/session49414, actor de238f20/caller03528b81; no result inferred
and no concurrent guest call. On completion collect actualpostrun/normal proof,
preserve its actual Basic/aliases, then rootless32 with actual armed ownership
watcher. Dedicated isolation/fault/secret-lifecycle proof is still mandatory.
WEB006 in_progress/uncommitted, AUTH-08/HOST-01–03 and WEB007–026 pending;
source21 strictgate remains green/frozen. All old failures and rootless31
startedtrue/stoppedfalse stay. Production/NAS/liveCockpit untouched.
Exact current pins/handles: `.scratch/web-006-source21-current-state-v188.json`
SHA256 d0b683736c81dff62a0e5f9863ab1eef99b650044b93e8b4455d83b51a804042.


Checkpoint189 (2026-10-24): fresh source21 native26 ACTUAL PASS95167582/
338.50s; original3686310/start431533207 reaped/gone. Checker136100/
start32416193 returns0/335.69s. Generation401b22ff37074827b2efab9911bcd2c2,
SUMMARY47d9e60a/385049B has4modes/3engines/33host assertions and12same-Caddy
certificate-specific TLS refusals,0requiredretries/skips/normalstop. Actual
readonly postrunc8b01ae7 PASS1.81s;8record normal adapter880156ee/19238B,
all original handles gone, real TLS/noHTTP-response/secret gates rejoined.
Native actual Basic inode118708497/root:983/0640 and3aliases NOREPLACE-preserved
4cbe3bae PASS1.84s, no payload/digest read. Fresh rootless emptybaselinef9909fa6
PASS1.51s, original3687804 reaped/gone.

Rootless32 actual original coordinator FAILdecaafbe/82.26s, outer3688017/
start431587685 reaped/gone. Watcher141571/start32470630 andrunner141572/
start32470656 gone. Original checker141576/start32470682 returns1/80.14s:
all3trusted engines baseline hoststatus unavailable versus supported;0accepted
cases/noSUMMARY. Original runner additionally tries missingSUMMARY and records
secondary FileNotFoundError; that does not replace original checker failure.
New inert future error collectors preserve both and always collect the watcher;
executed32 bytes/failure remain unchanged. No replay or acceptance promotion.

Readonly diagnosisdac1c78c PASS1.846s, original3689465 reaped/gone: generation
ea614316bb6a462c8458971e239cd8fe startedTRUE/stoppedTRUE. Controller32v2 drain
fix ACTUALLY passes stockengine:3original exactCID waits return0/stdout0newline,
3exactCIDexists return1,6observers EOF/reaped/no lostFD/unknown,69original
generation PID/start pairs gone, no controller errors. Actual3liveCID/6ID
ownership passes as a separate partial proof; untrusted3browser TLS refusals
pass, but hoststatus/normal acceptance does not. Basic inode118729990/983:983/
0400/secret_t read metadataonly. Original rootless31FAIL/stoppedFALSE unchanged.

Failed32 separate exact-ID cleanup ACTUAL PASS5.117s, original3691144/
start431702236 reaped/gone: genuine liveownership/emptybaseline/failed receipts
and actual independent drain held; whole-store opaque backup labelledsecret_t
BEFOREbytes;6original creation-bound IDs each get durable intent/nonforced
removal, finalempty/3oldstoppedaudits/noRefs/strict13role4cgroup5endpoint closure.
No successful-normal proof fabricated, no current Basic/alias switch or service
replay. Next a new helper-only sameimage metadata/client-stage probe to identify
remaining refusal; not started, no authpayload or host-status acceptance implied.
Source21 strictgate remains green/frozen. WEB006 and AUTH-08/HOST-01–03 remain
pending/uncommitted, WEB007–026 pending. Production/NAS/liveCockpit untouched.
Full current pins/handles: `.scratch/web-006-source21-current-state-v189.json`
SHA256 ffb40d7d5d09838ca183784c151c4a44c87ca6bd6e8755d3fb3bf5fa9f6cb5e6.


Checkpoint190 (2026-10-24): first helper-only diagnostic FAIL5275cc64/
3.196s, outer3692658 reaped/gone: missing outer select import atline641,
before any probeCID or image stage. Helper143896/start32642462 started/stopped
normally and gone; strictclosure/secrets-empty verified. Originalfailure stays.
New v2scope holds that actual closed failure; importsselect, composednamespace
audit resolves allglobals before effects. Actor41911cba/caller7ee9ddf0.

Actual helper-only v2 probe PASS6.887s, original3693242/start431780291 reaped/
gone. Real canonical container-service projection runs asUID983 from current.9;
actualsame UBI10micro image92c09797 undercontainer_t,981:981/noSecrets/noNet/
caps0/NNP/ROhelpermount. ALL measured stages pass:O_PATH parent, nonsecretbinding
read,actualEndpointBinding.from_startup/_runtime_binding, realSO_PEERCRED
(pid0,uid65534,gid65534),SO_PEERPIDFD(fdinfoPid0/NSpid0/livepoll), actual
binding.connect. No auth/protocolpayload/status request. Original helper143992/
start32663253 stayslive across samples, stopsnormally/drains; exactdiagnostic
CID exited0/noSecrets and retirednonforced, strict13role4cgroup5endpoint and
emptysecrets restored. No functional/rootless hoststatus acceptance inferred.

Remaining refusal is AFTER the proven transport. Next narrow actual fixed
peer-observer/request path, using retained facts first and a NEW diagnostic
API cohort only with original confinement, watcher-before-secrets, preserved
Basic/aliases and fixed safe tracing. Newcohort/trace being prepared, notrun.
No productcode change or policygrant byguess; source21 remainsfrozen/strictgate
green. Native26PASS retained; rootless32FAIL/0acceptedcases remains unchanged,
its genuine3wait0/3exists1/drain and6IDretirement are partialproofs only.
WEB006 and requiredAUTH/HOST cases remain pending/uncommitted. Production,
NAS/liveCockpit untouched. Full exactpins/handles:
`.scratch/web-006-source21-current-state-v190.json` SHA256 e7c61dc1dc4dc7df8fc0cb11f84dc339e15c22f7abcb62fcdb90eb4e3fb9acff.


Checkpoint191 (2026-10-24): rootless32 retained original API PID141854/exact
CID402337246bc1602c61488f1d8c93756a2b22606c34f842ca33ae10c95fed3865
has actualcgroup .../libpod-<FULLCID>.scope/container. Source21's scope-only
host_peer._container predicate1825 evaluates FALSE on these measured joined
facts. Independent review confirms this is a demonstrated compatibility refusal;
innerPID1/UID/GIDmaps/manager distinction and adjacent exportedfacts pass. No
second mismatch is claimed; complete vendor JSON stillneeds retained-data review.

Contract-first hostadmin/ADR150/INV020/humantroubleshooting refinement: allowonly
exact full inspectedCID scope or its SINGLE fixed container child. Original raw
cgroup staysinproof. Every PID/pidfd/manager/image/argv/env/map/mount/namespace/
security check remains. No privilege/SELinux/capability/dependency change.
New regression actually FAILS originalcode (1fail/1pass); correction plus
206peer/protocol/client/status tests PASS13.73s, lint/format/docs207/27/diffcheck
pass.21 independent security mutations cover BOTHlayouts; foreign64CID/shortCID/
nonlibpod/scopex/containerx/nested/arbitrary/trailingSlash paths refuse. Independent
source review passes, not installed acceptance. No new peer33diagnostic activated.

Frozen source22 1361files snapshot6496929e, capture04e0e36b/684B, exactly6changed
files from21. No canonical edits aftercapture. Canonical002unchanged; explicit
two-TOML-field fixture010 projectionb6d3491c/245249B/snapshot04c9aa85 preserves
all108source22 package bytes. Rootlessdeployment011. Newartifacts/image/staging
remain unbuilt/unexecuted; preparation only while original strict gate22 RUNNING
outer3696772/start431918922/session11188, runnerbbaf74be. No outcome inferred.
No new service/container/install activation before actual green gate22.

Source21 native26 PASS remains genuine historical evidence, not source22
acceptance. Rootless32 FAIL/0cases and original69handle/3wait0/3exists1 drain,
6IDcleanup/emptysecrets/transportprobePASS remain preserved separately. All app
rolesinactive; no guest executoractive. WEB006 in_progress/uncommitted,
AUTH-08/HOST-01–03 and WEB007–026 pending. Production/NAS/liveCockpit unchanged.
Exact current pins/handles: `.scratch/web-006-source22-current-state-v191.json`
SHA256 535692f8b8b44b8c354a064607428dbabe0da3dd2d07daa5bc46d2474f18248d.


Checkpoint192 (2026-10-24): source22 strict gate ACTUALLY PASSED, original
outer3696772/start431918922 reaped and gone, rc0,1254.87s. Command:
`scripts/check.sh --require-web --require-cockpit`. All1361 frozen inputs
unchanged;7782 Python tests passed (52 explicit opt-in deselections),572 Cockpit,
2786 web unit,2846 component,21 sandbox/10 driver checks, locked base/server/MCP
wheel profiles, strict wire/lint/types/build and real HTTP/API React fixture
passed. Required selected tests had no skips; installed Caddy/host acceptance is
separate. Log SHA2569c9f095e91d17bebe4e7a04882f067a4925637a8bd9d7ce3c948f4fff9917c9b/100877B.

One dedicated READ-ONLY collection rejoined the original protected source21
67372B container-inspect capture and closed its exact QEMU/boot/SSH/input
handles. All19 pre-process metadata predicates and the original mount verifier
pass. The only demonstrated mismatch remains the old scope-only cgroup check
versus the original exactCID .scope/container path. No live PID, new source22
runtime or functional acceptance is inferred; no service/container/credential
or protocol request occurred. Reader outer3714943/start432040077 rc0,0.78s,
reaped/gone; independent result review agrees.

Fresh source22 build/staging is underway. An initial host-only packet preparer
refused in overlay_versions before publishing a packet or contacting the guest;
its failure is retained and the ignored fixture codec is being corrected.
Source22 remains frozen; no product-code change or repeated full gate is needed
for that fixture-only correction. WEB006 remains in_progress/uncommitted;
AUTH-08/HOST-01–03 remain pending. New010/011 installed native/rootless browser,
dedicated isolation/fault and secret lifecycle acceptance are still required.
Previous source21 native26 PASS/rootless32 FAIL and all original evidence remain
distinct. Production/NAS/live Cockpit remain untouched.
Current pins: `.scratch/web-006-source22-current-state-v192.json`
SHA256ad616f7c24a8242f4c3c2ce7864d7bbcffd77ac5e73b4ce67f69f16ce452128d.


Checkpoint193 (2026-10-24): canonical and explicit010 fixture artifacts,
shared API/UI image, transfer, readiness, native010 first installation/UI,
OCI export/transfer/full receipt upload, guest load and runtime audit ACTUALLY
PASS with original executors reaped/gone. Compact independent evidence index:
`.scratch/web-006-source22-build-staging-EVIDENCE-v1.json`,
SHA256a2eaadd7d41da41106bd3531eaee5265bfd13c845acb4f890febb666bc9c0dec. Gate22 remains green on unchanged source22.
Image ccb43a3e has actual pinned UBI10 micro ancestry,108 backend/6 UI leaves,
35 absent tools/8 absent modules, capless/NNP/read-only/no-secret confinement;
its one audit CID exited0, drained and was retired without force.

Readiness preserved previous Basic inode118729990 and three aliases without
replacement or payload inspection. Exactly52 old009 SELinux User corrections
preserved type/role/range/mode/owner/bytes, and all264 prior control inputs were
rejoined. Original native installer144380/start32963213 ran once, rc0/reaped,
17.06s; outer3719599 closed in38.19s. UI outer3720229 passed in5.55s.

Environment-v1 FAIL47dfa431 was a fixture clone allowlist omission, before any
public copy. New environment-v2 also corrected the borrowed inventory name,
held the original failure/work and ACTUALLY PASSED19.16s, outer3722316 reaped/
gone. It proves the new108-leaf read-only package projection and194 browser
files/50 directories, preserving all old17/19/20/21 source trees. Rootless011
stage/render ACTUALLY PASSED5.46s, original3722484 reaped/gone; no activation.

Profile-proposals-v1 ACTUALLY FAILED3.74s, original3722690/start432161324 reaped/
gone. Canonical prepare() correctly refused a protected bootstrap binding hash
at host_policy.bindings1048. No profile/policy proposals were published; its
temporary native selector inode60996809 was preserved with NOREPLACE, and
strict role/cgroup/endpoint closure passes. The new peer module still needs its
separate protected bootstrap installation in the owned guest. A narrow guarded
refresh and NEW profile-v2 scope are being prepared, preserving original files,
failure/work/selector and security policy. No product code or gate replay.

Native27 must be followed by native isolation/fault acceptance while its Basic
file still has native ownership, before preservation and rootless33 acceptance.
All this remains pending. Source21 native26 PASS and rootless32 FAIL remain
historical, distinct evidence. WEB006 in_progress/uncommitted; AUTH-08/HOST-01–03
pending; WEB007–026 pending. Production/NAS/live Cockpit remain untouched.
Exact current pins: `.scratch/web-006-source22-current-state-v193.json`
SHA2569348617f94f10fad55af9771422da3602751733cfbd34d899d1f8799daafbff9.


Checkpoint194 (2026-10-24): source22 staging is complete through ACTUAL successful
authority32 publication. Independent compact evidence indexv5,
SHA2563c4c788bcfdb37cf2bcc901480c356a2b830da9005387a82bf2a33545b2a1d4f/33424B, verifies18 successful original
stages/observations and retains seven original failures without promotion.
Gate22 remains green/frozen; no product-source edit or repeated build/install.

Bootstrap-refresh-v1 failed on a missing contextmanager decorator before target
access. Refresh-v2 refused a guessed SELinux User before candidate/intent/mutation.
The first metadata collector also retained its WORK-lifetime failure; corrected
metadata-v2 ACTUALLY PASSED1.58s and measured old peer inode78157341/dev64515,
SHA2803c60e, unconfined_u:object_r:hfcache_host_helper_code_t:s0. New refresh-v3
ACTUALLY PASSED2.09s, original3726222/start432278040 reaped/gone: old exact inode,
hash and SID preserved with NOREPLACE; empty candidate labelled with that SAME
SID before bytes; source22 becb6ddb peer published without overwrite. Kernel,
policy, units, roles, credentials and selectors unchanged. No bootstrap replay.

New profile-v2 ACTUALLY PASSED4.75s, original3726418/start432283464 reaped/gone,
holding the original failed proposal/work/selector. Native222/rootless43 authority
files and original permission bits agree. Authority32 ACTUALLY PASSED3.99s,
original3726704/start432292903 reaped/gone: control33 has280 actual inputs with
all264 previous rows preserved in order; new fixturebf27/controller13d9 and
installed validator/visudo joins pass. No application acceptance from staging.

Original native27 real same-Caddy/browser run outer3726922/start432298258/
session22968 is RUNNING; no outcome inferred. Preserve this exact run; do not replay it. After
positive postrun, native isolation/fault checks must run BEFORE preserving its
Basic file and crossing to rootless33. Rootless normal, dedicated isolation/fault
and exact-ID secret lifecycle acceptance still remain required. WEB006 remains
in_progress/uncommitted; AUTH-08/HOST-01–03 and WEB007–026 remain pending.
Production/NAS/live Cockpit are untouched. Current original handles/pins:
`.scratch/web-006-source22-current-state-v194.json` SHA2569d1bb43de1b4e555e1b8c13db6643659109beac3accfb68fb0da39bcb1edef6a.


Checkpoint195 (2026-10-24): source22 native27 ACTUALLY PASSED333.16s, original
outer3726922/start432298258 reaped/gone, checker145762/start33181217 rc0/reaped
in330.27s. Real production-built UI -> same actual Caddy/trusted TLS -> installed
native010 API, four modes/three engines/33 host assertions and12 negative TLS
checks; no required retry/skip. Independent postrun ACTUALLY PASSED1.70s,
outer3728181/start432341444 reaped/gone: all8 original records close, generation
b0accf80979942e5bbaf1fe55c9a56e7 stoppedTRUE, all original handles gone, same
Caddy/TLS joins retained. Protected normal code e85e132e/18777B is held directly.

Native Basic inode118755357/root0:GID983/0640/secret_t remains current, metadata
only. Native fault source publication ACTUALLY PASSED1.77s, original3728713/
start432359350 reaped/gone; no fault entry or normal source was executed or
republished by publication. This is preparation, not dedicated acceptance.
Next acquire actual helper filter/unit/sentinel metadata, then native dedicated
isolation/fault cohorts BEFORE Basic preservation/rootless33. New collectors and
rootless generation-specific exact-ID cleanup adapters are being prepared inertly.

Human operator audit found two upgrade/rollback gaps: explicit protected fixed
bootstrap refresh before index prepare, and retention/restoration of matching
bootstrap bytes/inodes/labels alongside selector rollback. Initial copy/label
instructions and independent policy boundaries are correct. A docs-only patch
is being drafted without changing frozen source22; it must land with validated
final documentation before this work-package commit. Runtime fixtures will
retain their actual source22 identity. WEB006 is still in_progress/uncommitted;
AUTH-08/HOST-01–03/rootless33/dedicated/lifecycle acceptance remain pending.
Production/NAS/live Cockpit remain untouched. Exact pins/original handles:
`.scratch/web-006-source22-current-state-v195.json` SHA25697f0a1868759021d727249677640524bc878b1adab2897d2c37a3080dd6876e6.


Checkpoint196 (2026-10-24): native isolation-input metadata ACTUALLY PASSED3.96s,
outer3729611/start432392172 reaped/gone. One helper151199/start33275101 started,
measured root/helper-domain/NNP/seccomp with24 filters, then normally stopped and
drained. Actual unit79d491f8/policy27 receipt9f451aa2 and owned NFS sentinel
dev58/inode118335703/nfs_t/full9 were captured metadata-only; no protocol or
container. This is metadata preparation, not dedicated acceptance.

First native fault collector ACTUALLY FAILED2.72s, outer3730013/start432404701
reaped/gone; bootstrap151300/start33287686 rc1/reaped after0.42s. Original
stderr683a429a/1619B is retained. Safe original read-only traceback/errno
collection ACTUALLY PASSED (latest3732060/start432479069,0.80s): OSError errno24,
EMFILE at parent_descriptor90 while the preloader held108 package leaves with
duplicated ancestor FDs. Fault main, generation and RESULT were not reached;
the collector's missing-RESULT failure remains a secondary failure. All roles
are inactive; original current Basic was unchanged. New bounded-FD preloader
and fresh collector scope are being prepared without raising limits or replay.

Initial native27 preservation ACTUALLY PASSED1.70s, original3731972/
start432476839 reaped/gone. Basic inode118755357 and three original native
aliases were preserved with NOREPLACE before a new cohort can regenerate owned
fixture credentials. They are now absent. Native fault/isolation collectors
must join this actual preservation for their first absent-start preflight.
An inter-native preservation and final-native adapter will retain later actual
cohort credentials; rootless transition still requires BOTH native dedicated
passes. Frozen source22/gate22/native27 normal/postrun remain valid. Required
AUTH-08/HOST-01–03, rootless33, dedicated/lifecycle and human doc corrections
remain pending; WEB006 is uncommitted. Production/NAS/live Cockpit untouched.
Current pins: `.scratch/web-006-source22-current-state-v196.json`
SHA2564a565bc9106ccae450b599cbd1f419538e746c3e2fb55bdbc71716045aaa4941.


Checkpoint197 (2026-10-24): corrected bounded-FD preload actually verified108
leaves/11 shared directory handles with137 open FDs, unchanged soft1024/hard524288,
and closed at8 FDs. It reached fault main. Native fault-v2 still FAILED before
generation: canonical manifest validation was invoked as root while unchanged
validator requires the fixture owner UID1000. Original safe diagnosis PASS0.76s,
outer3750661/start433317546 reaped/gone, confirms exact path_input284 frames.
No validators or ownership rules were relaxed.

New private fault source dd8ad806/63395B changes only the two validator invocations
to finite owned UID1000 children and gives new result/workspace names. New source/
preloader publication ACTUALLY PASSED1.85s, original3753351/start433423685 reaped/
gone; original sources/results and both old budget records are held unchanged.
Actual local stem is publication-v3-final; earlier reserved v3 caller was never
executed. Corrected native fault-v3 ACTUALLY FAILED22.57s, outer3753692/
start433435502 reaped/gone; child151883/start34318448 rc20/reaped in20.55s,
stderr0/stdout633B. All13 roles/4 cgroups/5 endpoints close. Its original saved
state must be diagnosed before another cohort; no failure or missing result is
promoted. Current selector/Basic metadata is pending that read-only diagnosis.

Native27 normal/browser33 assertions/12 TLS checks and independent normal8
postrun remain passed. Native isolation sources are published, not executed.
Initial Basic/aliases remain retained in their preservation scope. Required
native dedicated, rootless33 and lifecycle acceptance remain pending; WEB006
is in_progress/uncommitted. Revised scratch-only human operator patch5a3e51ff/
8005B passes apply-check and clarifies preserve-before-replace, upgrade permission/
key retention and helper-aware rollback. It remains unapplied while source22 is
frozen; final human docs/gates remain required. Production/NAS/live Cockpit
untouched. Exact current pins:
`.scratch/web-006-source22-current-state-v197.json` SHA256d38db3f9218f872c5f59cff69cab6b2cefbbc153aa0cb32b045878e47bcc28fb.

Checkpoint198 (2026-10-24): retained native fault-v3 diagnosis confirms the real
refusal was HTTP 403 / HFAPI002 / CLI exit 10; the private fixture still expected
exit 2. The product matched its existing contract. Its original failed result
remains failed. Generation `852e90dfed034076a82e623fcbe0906e` started and stopped;
all 29 original process handles are gone and no mutation phase was reached.

Failed3 preservation ACTUALLY PASSED in 1.7527s, original 3757110 /
start 433561558, rc0/reaped/gone. Basic inode 118779523 and the three native
aliases were retained metadata-only with NOREPLACE. Publication4 ACTUALLY PASSED
in 1.8783s, original 3757297 / start 433565820, rc0/reaped/gone. Its new private
fault source `e250db80` / 63396B corrects the stale assertion to exit 10; canonical
source22 and all 1361 frozen inputs stay unchanged.

Fault-v4 ACTUALLY FAILED before fault main or a generation: original 3757436 /
start 433568462, rc1/reaped/gone in 2.1576s; child 152349 / start 34451406,
rc1/reaped in 0.1087s. Safe original stderr collection ACTUALLY PASSED in 0.7418s,
original 3757838 / start 433578627, rc0/reaped/gone. It reports ValueError at
`load_fault:138`: a stale dynamic private-v2 path guard rejects the actual
private-v3 source. Main-v3 RESULT is absent. Original stderr and failures remain
retained, with no replay or new acceptance claim. All 13 roles, 4 cgroups and
5 endpoints were closed after the failed collector. Fresh preloader5/collector5
execution has no accepted functional result at this checkpoint.

Native27 normal/postrun remain passed. Native fault/isolation, rootless33,
lifecycle and AUTH-08/HOST-01–03 acceptance remain pending; WEB006 is
in_progress/uncommitted and WEB007–026 remain pending. Human operator patch v2
is scratch-only and unapplied. Source22 remains frozen/green; production, NAS
and live Cockpit are untouched. Task006 records the actual receipt pins.

Checkpoint199 (2026-10-24): native fault5 ACTUALLY PASSED in 99.9186s,
original 3758671 / start 433603274, rc0/reaped/gone. Its original fault runner
152476 / start 34486208 returned rc0/reaped in 97.2586s. All five supplemental
fault phases passed, including the unproved-binding browser phase in Chromium,
Firefox and WebKit. Inputs were restored, original operation handles stayed
unchanged, and generation `16f5664de755463380b65d14b4169aab` stopped with all
46 original process handles gone. All 13 roles, 4 cgroups and 5 endpoints closed.
Parser reach and full feature acceptance remain explicitly unclaimed.

Inter-native preservation ACTUALLY PASSED in 1.8969s, original 3759171 /
start 433616954, rc0/reaped/gone. It retained the actual fault5 Basic inode
118708498 and three native aliases metadata-only with NOREPLACE; the four active
paths were absent at completion. Historical normal8 and source22/gate22 remain
unchanged. Original failures through fault4 and their receipts stay retained.

AUTH-08/HOST-01–03 remain pending. Native isolation, rootless33, dedicated
isolation/lifecycle and final human docs/gates remain required; the new native
isolation coordinator-v2 has not been published or executed at this checkpoint.
Human operator patch v2 remains scratch-only and unapplied. WEB006 remains
in_progress/uncommitted; WEB007–026 stay pending. The shared API/UI runtime keeps
pinned UBI10 micro. Production/NAS/live Cockpit remain untouched. Actual pins
and original handles are recorded in task006.

Checkpoint200 (2026-10-24): native isolation ACTUALLY FAILED in 9.2523s,
original 3760638 / start 433669933, rc1/reaped/gone. Its original coordinator
154201 / start 34552870 returned rc1/reaped in 7.1453s. Saved metadata collection
ACTUALLY PASSED in 0.7586s and confirms failure_stage=start, before private proof.
Generation `1f600631b89c4a229e0c63512037461a` started/stopped, with all 20 original
PID/start identities gone; public stop records inputs unchanged. The original
coordinator still records cleanup_unknown/cohort_cleanup_unknown=true because
its retained-ready list was empty; private_proof_cleanup_unknown=false. These
original flags remain unchanged. All 13 roles, 4 cgroups and 5 endpoints closed.

The original first diagnostic failed with empty guest channels; the second
refused its traceback format. Both failures remain retained. Safe diagnostic3
ACTUALLY PASSED in 0.7464s and identifies only the unchanged checker's
`exchange:575` refusal of a nonzero child return code, not the startup cause.
The generation's fixed_start_failure needs separate original-evidence diagnosis;
no new cohort or permission change is inferred. Basic inode118788081 and all
three native aliases were present in metadata-only collection and await a
separate guarded preservation after the cause is established.

Native fault5 and native27 normal/postrun passes remain unchanged. Native
isolation, rootless33, dedicated/lifecycle, human docs and final gates remain
required; AUTH-08/HOST-01–03 stay pending. WEB006 remains in_progress/uncommitted,
WEB007–026 pending, source22 frozen/green and human patch v2 unapplied. Shared
API/UI runtime remains pinned UBI10 micro. Production/NAS/live Cockpit untouched.
Task006 holds all actual original receipts and the diagnostic limitations.

Checkpoint201 (2026-10-24): original start-failure collection ACTUALLY PASSED
in 0.7680s, original 3762965 / start 433746206, rc0/reaped/gone. The retained
failure is OSError at controller `secret_kernel_marker:359` opening the SELinux
policy, via `start:1138` → `secret_label_gate:864`. The original errno was not
retained because the unchanged checker discarded the launcher stderr.

A separate current simultaneous-open probe ACTUALLY PASSED in 0.9453s,
original 3763814 / start 433776310, rc0/reaped/gone. Its second policy open
returned errno16/EBUSY while its first descriptor was held; all descriptors
closed and kernel hash45bb34e8 stayed unchanged. This current observation is
explicitly neither the original errno nor proof of the original root cause.

Failed-isolation1 preservation ACTUALLY PASSED in 1.8434s, original 3764843 /
start 433813466, rc0/reaped/gone. Basic inode118788081 and all three aliases were
retained metadata-only with NOREPLACE; active paths were absent at completion.
Original failed cleanup flags stay unchanged; all20 original generation handles
are separately proved gone. New coordinator-v3 only adds bounded stderr
observability for four fixed launcher phases in a fresh attempt2 workspace;
future collector-v6 preparation does not establish a new cohort or acceptance.

Source22 remains frozen/green; native27 normal/postrun and fault5 passes stand.
Native isolation, rootless33, dedicated/lifecycle, human docs and final gates
remain required; AUTH-08/HOST-01–03 remain pending. Human patch v2 is unapplied;
WEB006 remains in_progress/uncommitted. Pinned UBI10 micro and production/NAS/live
Cockpit boundaries remain unchanged. Task006 holds actual evidence pins.

Checkpoint202 (2026-10-24): native isolation2 ACTUALLY FAILED in 17.7940s,
original 3766361 / start 433867300, rc1/reaped/gone; original coordinator
154750 / start 34750237 returned rc1/reaped in 15.7018s. Combined read-only
diagnosis ACTUALLY PASSED in 0.7899s, original 3767370 / start 433901752,
rc0/reaped/gone. Original launcher START rc0, private-proof rc1 and STOP rc0
all have both EOFs and original identities reaped/gone. Generation
`dcdd4d59179f483f84b77b44598f88ef` stopped with all37 recorded application
handles gone; public stop inputs are unchanged. Original private-proof cleanup
uncertainty remains true. Separate custom-unit lifecycle evidence is pending;
this does not prove all private children closed.

Safe private-proof frames reach `owned_setup:445`, checking child record state
complete after returncode0/reaped/timely/no-overflow checks. The inner child's
error has not been joined. Static review separately found `mount_rows:85`
rejects NFS while the required owned archive inode remains on NFS after bind.
That fixture contradiction is not yet proved to be this child's first failure.
A fixture correction is UNBOUND; no security or canonical product change is
claimed. Current Basic inode118779524 and three aliases were observed present
metadata-only; original failures and cleanup flags remain retained.

Source22/gate22, native27 normal/postrun and fault5 passes remain unchanged.
AUTH-08/HOST-01–03 stay pending, as do native isolation, rootless33,
dedicated/lifecycle, human docs and final strict gates. Human patch v2 is
unapplied; WEB006 is in_progress/uncommitted. Shared API/UI remains pinned
UBI10 micro. No production/NAS/live Cockpit effects. Task006 holds actual pins.

Checkpoint203 (2026-10-24): private lifecycle collection ACTUALLY PASSED in
0.8090s, original 3769347 / start 433976374, rc0/reaped/gone. The owned custom
unit is inactive/dead with its cgroup absent; root155004 and setup155007 are
freshly gone, as are all37 recorded application handles. Original
owned_children_reaped=false and cleanup_unknown=true remain unchanged. The
retained setup output is44B/hash36af17c2, matching one canonical Refused candidate;
no original frames or errno were recovered. Static NFS fixture incompatibility
requires correction but is not established as the actual first guard failure.

First isolation2 preservation ACTUALLY FAILED in1.3648s, original3770436 /
start434019258, rc1/reaped/gone: raw private-unit bytes were decoded as JSON at
readiness303. Only its owned WORK was created; no four rename intents or inode
mutations occurred, and strict closure passed. The fresh v2 preservation
ACTUALLY PASSED in1.9577s, original3771223 / start434050188, rc0/reaped/gone.
It distinguishes two raw records from12 JSON records, retains Basic118779524
and three aliases metadata-only/NOREPLACE, and confirms active paths absent.
Both original failures and cleanup flags remain unchanged.

Projection candidate256ee20b is reviewed with local checks only, not privileged
acceptance; private publication2/coordinator4 remain preparation at this
checkpoint. Source22/gate22 and native27/fault5 passes stand. Required cases,
isolation/rootless/lifecycle and human docs/final gates stay pending; human
patch v2 unapplied, WEB006 in_progress/uncommitted. Pinned UBI10 micro and
production/NAS/live Cockpit limits remain unchanged. Task006 holds actual pins.

Checkpoint204 (2026-10-24): private publication2 ACTUALLY PASSED in2.1123s,
original3772060/start434079367 rc0/reaped/gone. Isolation3 ACTUALLY FAILED
in17.7129s, original3772984/start434117147 rc1/reaped/gone; coordinator155341/
start35000078 rc1/reaped in15.5428s. Combined3 and lifecycle3 read-only collection
ACTUALLY PASSED, respectively3773463/start434135626 in0.8033s and3774106/
start434160624 in0.8110s, rc0/reaped/gone. Direct retained child evidence now
identifies Refused at the BEFORE mount_rows120 shared-mount guard. The NFS-row
admission branch and alias binds were not reached. This does not establish the
original isolation1 OSError or isolation2 first guard.

Original private owned_children_reaped=false and cleanup_unknown=true remain
unchanged. Separate current evidence shows the custom unit inactive/cgroup
absent, root155594/setup155597 freshly gone and all37 application handles gone.
Preservation3 ACTUALLY PASSED in1.9993s, original3775576/start434221076
rc0/reaped/gone: Basic118788486 and three aliases retained metadata-only with
NOREPLACE; active paths absent at completion, no Basic payload/hash read.

A new private3 candidate is preparation only: strengthen propagation inside the
proved disposable MNT before aliases and on each new file bind, retain strict
shared/NFS/readonly/identity guards, and prove host/real-helper MNT unchanged.
No application, policy, permission or hardening change is proposed. Source22/
gate22 and native27/fault5 passes stand; required cases, native isolation,
rootless/lifecycle, human docs/final gates remain pending. Human patch v2 remains
unapplied, WEB006 in_progress/uncommitted. Pinned UBI10 micro and production/NAS/
live Cockpit boundaries remain unchanged. Task006 holds actual evidence pins.

Checkpoint205 (2026-10-24): private publication3 ACTUALLY PASSED in2.2663s,
original3779837/start434398029 rc0/reaped/gone, with no application/isolation
main execution. Isolation4 ACTUALLY FAILED in9.6112s, original3780250/
start434413339 rc1/reaped/gone; coordinator155888/start35296274 returned
rc1/reaped in7.2492s. Combined4 read-only collection ACTUALLY PASSED in0.8188s,
original3780715/start434430590 rc0/reaped/gone.

Actual START failed with OSError at `secret_kernel_marker:359` via the BEFORE
label gate810; the original errno was not retained. No namespace/private-proof
code was reached. Generation457300722bc848df85fe9afe9f4ee375 stopped with all18
recorded application handles gone and unchanged public-stop inputs. Original
private_proof_cleanup_unknown=false, cohort_cleanup_unknown/cleanup_unknown=true
remain unchanged. Private3 namespace preparation remains unaccepted; this is
neither evidence of its regression nor proof of an EBUSY startup cause.

Failed4 preservation is pending. An explicit pinned native-only observer adapter
is being designed to call unchanged controller.main once and retain numeric
errno separately, with no retries, monkeypatching, permission or runtime-source
changes. No adapter execution or cause inference is claimed. Source22/gate22,
native27 and fault5 passes remain stable; required cases, isolation/rootless/
lifecycle and human docs/final gates pending. Human patch v2 is unapplied,
WEB006 in_progress/uncommitted, UBI10 micro and production/NAS/live Cockpit
boundaries unchanged. Task006 holds exact original receipts.

Checkpoint206 (2026-10-24): failed4 preservation, fixed observer publication
and coordinator6 publication ACTUALLY PASSED in1.9296s/1.9033s/2.0699s. Native
isolation5 ACTUALLY FAILED in18.2118s, original3786240/start434638312
rc1/reaped/gone; coordinator156346/start35521244 rc1/reaped in15.8474s.
Combined5/lifecycle5 read-only collection PASSED in0.7952s/0.8407s and directly
identify a parent fixture bug: `_projection_parent_snapshot` calls unchanged
controller.pair(1), whose proc_start guard requires pid>1. START0/STOP0 passed,
private-proof1 refused before setup; no setup child or namespace operation ran.
All37 application handles and the private worker are currently gone; original
private reap=false/cleanup_unknown=true remain unchanged.

Preservation5 ACTUALLY PASSED in2.1138s, original3787405/start434673792
rc0/reaped/gone, retaining Basic118779525/three aliases metadata-only with
NOREPLACE, active paths absent. Private4 publication ACTUALLY PASSED in2.1837s,
original3787879/start434687004 rc0/reaped/gone. It publishes only a fixed PID1
stat reader permitting start_ticks>=0 and replaces two PID1 calls, with fresh
version wiring; generic PID/auth/runtime/namespace checks remain unchanged.
Old sources/failures remain retained. The private4 namespace candidate is still
unaccepted; native6 has no observed outcome at this checkpoint.

Source22/gate22, native27 and fault5 passes stand; required cases, native
isolation/rootless/lifecycle, human docs and final gates remain pending. Human
patch v2 unapplied, WEB006 in_progress/uncommitted; pinned UBI10 micro and
production/NAS/live Cockpit boundaries unchanged. Task006 holds actual pins.

Checkpoint207 (2026-10-24): native isolation6 ACTUALLY FAILED in18.4707s,
original3788112/start434691704 rc1/reaped/gone; coordinator156844/
start35574621 rc1/reaped in16.2773s. Combined6 and lifecycle6 read-only collection
PASSED in0.8228s/0.8211s: START0/private-proof1/STOP0 all reached EOF/reap/gone,
generationb211d8dc47c64d198eb82203933fcf79 stopped with all37 application handles
gone. Direct child evidence identifies OSError errno22 at the first MS_BIND,
project_in_child376. The12 required denial cases were not executed; private4
remains unaccepted.

The read-only propagation adjunct PASSED in0.7817s and confirms recursive
PRIVATE completed with all nonpropagation fields unchanged, then refusal at
alias_bind/source-basic, zero alias splits and final_strict_no_shared=false.
All six outside host/parent/API/worker/Caddy/helper mount-table hashes and full
before/after boundary records are equal. Original private worker157096 and
setup157099 are gone; setup wait0/EOF/closed/reaped, custom unit inactive and
cgroup absent. Original owned_children_reaped=false and private cleanup_unknown
remain unchanged beside separate current drain evidence.

Preservation6 ACTUALLY PASSED in1.9558s, original3789410/start434732189
rc0/reaped/gone, retaining Basic118788497 and three aliases metadata-only with
NOREPLACE; all four current paths are absent. Protected receipt65e3344f/76819B
holds the original failures unchanged. A detached-clone fixture5 is only design/
preparation; no new publication, cohort, denial or acceptance is inferred.

Source22/gate22 and native27/fault5 passes stand. Required cases, native
isolation/rootless/lifecycle, human docs and final strict gates remain pending.
Human patch v2 is unapplied; WEB006 in_progress/uncommitted. Pinned UBI10 micro
behind existing Caddy and production/NAS/live Cockpit boundaries are unchanged.
Task006 holds actual receipts; diagnosis/preservation are not functional runs.

Checkpoint208 (2026-10-24): detached-kernel prototype2 ACTUALLY PASSED
in0.8589s and private5 source publication PASSED in2.3186s. The earlier
prototype1 caller was never executed: an omitted sha helper was caught before
guest execution; temporarily edited source1 bytes were restored, local metadata
changed, and its captured caller remains retained/unexecuted. Fresh prototype2
proves only two synthetic private-MNT kernel mechanics, not feature acceptance.

Native isolation7 ACTUALLY FAILED in18.5878s, original3794385/start434912479
rc1/reaped/gone; coordinator157449/start35795398 rc1/reaped in16.3070s.
Actual prelaunch FD usage934/soft1024/hard524288 confirms unchanged limits and
the original fail-closed reserve guard. Combined7/lifecycle7 read-only collection
PASSED in0.8062s/0.8287s. Generation0d6156c4c0db487dbf4cb6a990a2c372 stopped with
all36 application handles gone; private worker157702/setup157705 are gone,
setup wait0/EOF/closed/reaped and custom unit inactive/cgroup absent.

All11 detached clones were prepared with readonly/private attrs and closed;
nine attached before Refused at archive-sentinel _preparation_rows276. Actual
BEFORE names/count11 agree with source groups. Original metadata-rejoined=false,
private reap=false/cleanup_unknown=true remain unchanged. The12 denial cases
were not executed; private5 remains unaccepted.

Owned-loopback NFS metadata prototype3 PASSED in0.8697s. Its actual alias has
device0:58/root '/'/nfs4/source127.0.0.1:/WEB006_OWNED_SENTINEL, RO/nosuid/nodev/
noexec and no propagation fields; host/parent tables stayed unchanged. This
confirms a narrow fixture formatter mismatch, without archive payload access.
Preservation7 PASSED in2.0433s, original3796203/start434971676 rc0/reaped/gone:
Basic118788083/three aliases retained metadata-only/NOREPLACE, current four
paths absent, protecteddefde8bf2/81039B. Source6's narrow row-map publication6
ACTUALLY PASSED in2.3090s, original3796805/start434989959 rc0/reaped/gone,
protected4baae33c/92770B. No application/isolation main ran in publication.
Native8 is running3797028/start434994051; no outcome or acceptance is inferred.

Source22/gate22 and native27/fault5 passes stand. Required cases, native
isolation/rootless/lifecycle, human documentation and final strict gates remain
pending; human patch v2 is unapplied and WEB006 in_progress/uncommitted. Actual
pinned UBI10 micro/shared-Caddy audit and production/NAS/live Cockpit boundaries
are unchanged. Task006 holds exact receipts; prototype/publication/diagnosis/
preservation results are not functional ledger runs.

Checkpoint209 (2026-10-24): native8's actual original cohort completed rc0
in20.2617s, runner157986/start35876980 reaped/gone; all four START/private-proof/
INSPECT/STOP children returned0 with both EOFs and original identities gone.
The outer collector ACTUALLY FAILED in22.9467s, original3797028/start434994051
rc1/reaped/gone, solely at its stale three-phase/count12 expectation. Its
passed/all-inputs=false receipt51344ceb remains unchanged; no operation replay.

A read-only DTO projection PASSED in0.7955s. Actual source-derived multiplicities
are19 attempted/19 denied: root11 (nine credential/archive/attachment), account8
(five credential/hub/archive/attachment). The actual delivered TLS metadata
0:0/0440 does not admit a Caddy-owner982 phase; none was invented. Full read-only
revalidation ACTUALLY PASSED in2.8479s, original3799225/start435070987
rc0/reaped/gone, protectedd48988b8/257263B. It independently recomputes the exact
Counter from pinned admitted_phases and original INPUT, and rechecks all source,
control, package, normal, four-phase, namespace/11-clone/readonly and stop proof.
All47 generation handles are gone; all six outside tables unchanged. Native
isolation evidence is accepted through this original-run/read-only proof pair,
while the original outer failure is retained.

Final BOTH native preservation3 ACTUALLY PASSED in1.8077s, original3799556/
start435081556 rc0/reaped/gone, protecteda32b6c24/65424B. Exact six-input and
19-counter guards join native27 normal8, fault5 and revalidated original native8;
Basic118788084/three aliases retained metadata-only/NOREPLACE, current four paths
absent. This preservation starts no app and is not a new functional run.
Rootless33 baseline is next; no rootless outcome is inferred.

AUTH-08/HOST-01–03 remain globally pending for required rootless/lifecycle,
human documentation and final strict gates. WEB006 is in_progress/uncommitted;
source22/gate22/native27/fault5 and actual pinned UBI10 micro/shared-Caddy audit
stand. Human patch v2 remains unapplied. Production/NAS/live Cockpit are untouched;
rollout, merge, push and tag remain unauthorized. Task006 holds exact receipts.

### Execution checkpoint210 (2026-10-24)

Checkpoint210: rootless33 normal FAILED after successful startup/TLS/Basic UI.
All three trusted browsers report host state unavailable; zero host cases ran.
All69 original process handles and three CIDs are drained, but six owned secrets,
Basic983:9830400 and three selection aliases remain retained pending exact-ID
retirement and NOREPLACE preservation. Read-only AVCs identify fixed manager
private-socket access denial; narrow session-bus correction is under review.
Source22/native evidence remains historical; no broad policy allow or replay.

Actual detailed receipts and original failures remain in task006. No package
completion, production rollout or later task activation is inferred.

### Execution checkpoint211 (2026-10-24)

Checkpoint211: failed rootless33 is drained, exact six-ID retirement passed,
and Basic/three selectors are preserved NOREPLACE. Current four paths are absent.
The narrow rootless session-bus fix and human bootstrap/rollback documentation
are applied in frozen source23; 137 targeted tests and docs207/27 pass. Gate23
is running; fresh installed native/rootless acceptance remains required.

Source22 evidence remains historical, including original failures. WEB006 is
uncommitted; subsequent work packages and production rollout remain pending.

### Execution checkpoint212 (2026-10-24)

Checkpoint212: source23 strict gate PASSED (7784 Python,572 Cockpit,
2786 web unit,2846 component); all1361 source hashes/modes unchanged.
Fresh canonical/fixture wheels and shared UBI10 micro API/UI image built; both
artifact builds reproduced UI assets twice. Source23 guest installation and
real native/rootless acceptance remain pending. A packet-schema tooling fix is
in progress; original failures and frozen projection remain preserved.

Human documentation is applied/reviewed; no package or installed acceptance
is inferred from the source gate/builds. See task006 for exact receipts.

### Execution checkpoint213 (2026-10-24)

Checkpoint213: source23 transfer/readiness and OCI/build-evidence transfers
passed; UI packet2 validates the actual wheel/assets. Native stage1 stopped
BEFORE calling the installer because its broad restorecon would alter retained
rootless.11 SELinux-user metadata. Original failure/labels remain preserved.
A child-only private-MNT pilot is under review; no core-source/security change,
service start or installed acceptance is inferred. Gate23/build passes stand.

Task006 owns detailed outcomes; required native/rootless/lifecycle work remains.

### Execution checkpoint214 (2026-10-24)

Checkpoint214: native namespace pilot and FIRST ACTUAL native installer passed.
Real host-backed release0.2.12 reports version0.2.12/all108 source leaves match.
Old rootless.11 full9/SID/hash, failed source1 and host/parent/pause mount tables
are unchanged. Current selection absent, all roles quiet. UI transfer binding,
image audit and real native/rootless Caddy/browser/lifecycle acceptance remain.
Source23 strict gate/builds remain valid; WEB006 is still uncommitted.

This proves fresh native installation, not mixed-history upgrade compatibility.
Exact original handles, failures and namespace receipts remain in task006.

### Execution checkpoint215 (2026-10-24)

Checkpoint215: native UI, image load/runtime audit, environment and rootless.13
staging pass. Actual image410c627e proves pinned UBI10 micro ancestry,108package/
6UI hashes,35tools+8modules absent and confinement. Helper refresh1 refused an
old candidate-name guard BEFORE file creation/rename; original code is unchanged.
Fresh exact-path correction is under review. Profiles and real native/rootless/
lifecycle acceptance remain pending; WEB006 is uncommitted.

No image/staging result substitutes for required installed host/UI acceptance.
Detailed original receipts, refusal and preserved handles remain in task006.

### Execution checkpoint216 (2026-10-24)

Checkpoint216: helper refresh2, native/rootless profile proposals2 and authority33/controller34 preparation pass. The first source23 native28 real functional runner FAILED14.662615s without SUMMARY; all fixed roles/cgroups/endpoints subsequently closed and secrets remained empty. Original records and newly created Basic inode118816437 remain preserved pending bounded startup diagnosis and exact no-replace preservation. No source23 functional acceptance is inferred; source23/gate23 and pinned UBI10 micro image stand. WEB006 remains uncommitted; WEB007–026 pending.

Task006 retains exact original executions and protected receipts; failed native28 is not replayed.

### Execution checkpoint217 (2026-10-24)

Checkpoint217: original native28 startup was successful (authenticated Caddy HTTP200, matching assets, both credential gates); failure is a concrete fixture launcher format defect. The actual root0755 browser launcher lacks its required interpreter line after AST regeneration. Read-only original-record checks and a harmless executable-format reproduction confirm this without replay. All28 original handles are gone and normal stop passed. Preserve failed28 credential/aliases, publish corrected fresh authority, then execute a fresh native/rootless cohort. WEB006 remains uncommitted; all four cases pending; source23/gate23 and UBI10 micro image unchanged.

### Execution checkpoint218 (2026-10-24)

Checkpoint218: failed native28 Basic and three aliases were actually preserved with NOREPLACE after fresh drain checks. Corrected authority34/controller35 actually passes with all four executable headers verified,303 inputs preserving the original298 prefix, and all21 prior published files retained. Fresh native29 real Caddy/browser functional execution is running; outcome remains pending. Source23/gate23 and pinned UBI10 micro image are unchanged. WEB006 remains uncommitted; all four cases pending; WEB007–026 pending.

### Execution checkpoint219 (2026-10-24)

Checkpoint219: fresh source23 native29 normal functional acceptance PASSED (four modes, all three engines,33 host assertions,12 untrusted TLS refusals, zero required skips/retries), with successful original runner/closure. Actual postrun validation and ordinary Basic/three-alias preservation also pass. Fresh rootless34 secret baseline passes, and its original real functional coordinator is now running. Rootless and dedicated fault/isolation/lifecycle remain pending. WEB006 stays uncommitted; source23/gate23 and pinned UBI10 micro image unchanged; WEB007–026 pending.

### Execution checkpoint220 (2026-10-24)

Checkpoint220: source23 rootless34 normal functional run FAILED83.579333s with original runner/checker nonzero and no SUMMARY. Watcher succeeded in exact process/six-secret ownership; original watcher/runner are gone and final fixed-role closure passes. Six secrets and current Basic/aliases are retained pending bounded original browser/generation diagnosis and exact failure-only retirement/preservation. Cause remains unproved; no replay. Native29 normal remains accepted; all four WEB006 cases pending, WEB006 uncommitted, source23/gate23 and UBI10 micro unchanged.

### Execution checkpoint221 (2026-10-24)

Checkpoint221: failed rootless34 is fully drained (all69 handles, exact3CIDs wait0/exists1), its exact6secrets durably backed up/retired without force and Basic/three aliases preserved. Original browser report shows unavailable vs supported in all3engines, zero cases. Bounded AVC read records7 helper-domain connectto denials to unconfined_dbusd_t session-broker type; exact syscall/broker attribution and narrow compatibility review are pending. No security/source change applied, no replay. Native29 normal and source23/gate23/UBI10 micro stand; WEB006 uncommitted, all4cases pending.

### Execution checkpoint222 (2026-10-24)

Checkpoint222: exact paired original audit proves all7 fixed-systemctl connect syscalls failed EACCES against unconfined_dbusd_t; current UID983 broker and bus inode18/label match. Reviewed singleton peer connectto policy/contract/regression patch is APPLIED. Focused138 tests, Ruff, docs207/27 and diff check pass. Exactly7 canonical files changed from source23; Python108/web96 unchanged. Source24 capture/full gate and all fresh installed acceptance are PENDING. Source23 gate/native pass remain historical evidence only; WEB006 uncommitted, all4cases pending.

### Execution checkpoint223 (2026-10-24)

Checkpoint223: source24 snapshot71cdbc2b captured/verified with1361 files and exact7-file delta. Guarded strict gate24 is ACTUALLY RUNNING (originalgate3855792/start436260088; outer3855791/start436260069), outcome pending. Disposable .14 projection826613a0 passes full tar/hash/mode/current checks, only2TOML version fields changed. No source24 artifact/build/install/policy or functional result is inferred. Frozen source24 permits only5 bookkeeping edits. WEB006 uncommitted/all4cases pending; native29 is historical source23 only.

### Execution checkpoint224 (2026-10-24)

Checkpoint224: readonly installation assessment and measured two-shadow pilot ACTUALLY PASS. Both retained rootless trees would receive52 SELinux-user-only relabels each; prior native.12 has0. Pilot preserves old trees/native108/outside mount tables and leaves .14 absent, with no installer or policy load. Gate24 remains running (Python phase85% at02:20:57Z); no full-gate or installed acceptance inferred. Source24 frozen; WEB006 uncommitted/all4cases pending.

### Execution checkpoint225 (2026-10-24)

Checkpoint225: source24 strict gate ACTUALLY PASSED1270.412292s with1361hashes/modes unchanged: Python7785/52 documented opt-in deselections,Cockpit572/0skip,web2786unit/2846component,sandbox21/startup2 and builds. Canonical+fixture wheel/UI and shared pinned UBI10 micro image40a751be builds/export pass; source/UI packets validate before publication. Runtime ancestry/absence audit and installed policy/native/rootless/dedicated acceptance remain pending. WEB006 uncommitted,all4cases pending; WEB007–026 pending.

### Execution checkpoint226 (2026-10-24)

Source24 actual source transfer passes; readiness-v1 failed only on stale fixture receipt keys before installer/service/policy/credential effects. Fresh readiness-v2 is being validated against all six actual DTOs. Control35 readonly303-row export passes; native014/policy installer reviews pass, neither installer has run. Source gate/artifacts/shared pinned UBI10 micro image remain valid. Runtime audit and installed source24 native/rootless/dedicated acceptance remain pending; WEB006 uncommitted/all4cases pending, WEB007–026 pending. Task006 retains original identities and failed evidence.

### Execution checkpoint227 (2026-10-24)

Checkpoint227: readiness-v2 ACTUALLY PASSES4.004387s, retaining303 prior inputs/secret0/strict closure. First native014 install ACTUALLY PASSES38.981780s with108 matching package files and preserved old releases/mount tables. UI guest publication passes for6 assets, but original local collector fails KeyError held_release_failure_classes after publication; its rc1/false flags remain retained. Fresh readonly completion/rejoin is required, with no installer/UI replay. OCI transfer binder also refuses during local prepublication DTO validation, with no guest action. Source24 gate/build/image remain valid; runtime audit, new policy and all source24 installed browser/dedicated acceptance remain pending. WEB006 uncommitted/all4cases pending; WEB007–026 pending.

### Execution checkpoint228 (2026-10-24)

Checkpoint228: readonly UI completion ACTUALLY PASSES; original publication/local collector failure remain separately preserved with no replay. OCI/build-receipt handoffs, image load and actual runtime audit PASS for image40a751be: pinned UBI10 micro ancestry,108 package/6UI hashes,35 tools/8 modules absent, rootless/capless/NNP/seccomp/readonly/network-none/secret0. Policy-v1 refuses before effects on a malformed63-character fixture hash; no module/CIL/receipt changed. Fresh policy-v2 will derive exact64-character actual hash and attest measured nfs_t. Source24 gate/builds remain valid; new policy/rootless bus/native-rootless browser/dedicated acceptance remain pending. WEB006 uncommitted/all4cases pending; WEB007–026 pending.

### Execution checkpoint229 (2026-10-24)

Checkpoint229: policy-v2 ACTUALLY PASSES14.843177s; new kernel24165559 and receipt725f5a0c bind exact singleton CIL1d9d7f31/current nfs_t, preserving old globals and other modules/booleans. Environment ACTUALLY PASSES27.620952s with108 installed leaves readonly/new-policy proof. Optional bus probe-v2 fails before unit/worker start on a nonexistent collect-row proc_absent field; fresh v3 correction is pending with original failure preserved. Rootless015 staging/profile/authority and native30/rootless35/dedicated acceptance remain pending; no source24 application has started. Source24 gate/UBI10 micro runtime audit remain valid. WEB006 uncommitted/all4cases pending; WEB007–026 pending.

### Execution checkpoint230 (2026-10-24)

Checkpoint230: rootless015 staging and both new-policy profile proposals ACTUALLY PASS. Optional bus probe-v3 fails203/EXEC before its worker; unit is stopped/reset, PID absent/cgroup empty, original false retained and optional diagnostic repair ends. Actual authority35 publication fails on inherited old control.selinux hashes before application/sudoers admission; partial files and false receipt retained. Fresh authority36/controller37/control37 is being prepared with exact current CIL/receipt and measured nfs_t map. Source24 gate/native installation/UI/image audit/policy/environment remain valid. No source24 browser application run yet; all required normal/fault/isolation/lifecycle acceptance pending. WEB006 uncommitted/all4cases pending; WEB007–026 pending.

### Execution checkpoint231 (2026-10-24)

Checkpoint231: fresh authority36/controller37 ACTUALLY PASSES4.543562s with exact current SELinux pins,11-field constructed-control audit,326 input rows preserving original303 prefix, all19 partial35 files retained, and controller load/visudo/strict closure pass. Source24 native30 real Caddy/installed-API/helper/browser functional run is NOW RUNNING under original3890447/start436775404; no outcome inferred. Shared pinned UBI10 micro runtime audit, native/rootless staging, policy/environment/profiles remain valid. Rootless35 and dedicated fault/isolation/lifecycle acceptance remain pending; all4cases pending,WEB006 uncommitted,WEB007–026 pending.

### Execution checkpoint232 (2026-10-24)

Checkpoint232: source24 native30 normal ACTUALLY PASSES342.416869s (4 modes/3 engines/33 host assertions/12 untrusted TLS refusals,0 required skips/retries), with postrun validation and ordinary Basic/three-selector preservation also passed. Rootless35 secret baseline passes; original real rootless coordinator3892604/start436841476 is NOW RUNNING with the original ownership-watcher sequence; no current ARMED/runner/rootless outcome is inferred. Dedicated fault/isolation/lifecycle remain pending; all4cases pending,WEB006 uncommitted,WEB007–026 pending. Source24 frozen gate/UBI10 micro/native+rootless artifacts/current policy+profiles remain valid.

Checkpoint232 continuing audit: native30 ordinary-functional ledger now records actual source24 pass in all4 still-pending cases. Rootless35 is still running; source audit identifies7 stale fixture inventory predicates/producer copies. Corrected unbound candidates pass actual92a6 checks, with no original-source edit or replay. Original outcome/drain and fresh scope remain pending. Dedicated MAC attribution and canonical-helper seccomp metadata remain required evidence, with no old-state inference.

### Execution checkpoint233 (2026-10-24)

Checkpoint233: original source24 rootless35 FAILED601.597356s and closed, protected581a07b4/39565B. Original runner178324/start37724278 rc1/reaped0.096582s/no JSON; watcher178323/start37724250 rc0/reaped600.197731s but ownership/all-source-closure false. Both original identities gone, final fixed-role closure true. Stale inventory5d vs actual92a is proven in pre-create source guards; bounded original traceback/state readiness is pending before any no-effect claim or fresh rootless36 scope. Native30 ordinary acceptance remains passed; all4cases pending,WEB006 uncommitted,WEB007–026 pending.

### Execution checkpoint234 (2026-10-25)

Checkpoint234: failed35 readonly readiness ACTUALLY PASSES2.437954s, proving original ValueError at execute382 before WORK/start, both runner/browser WORKs absent, only retained native30 generation, secret0/unknown0, four current paths absent,326 immutable records/current2416/key intact. Original failed35/watcher false flags remain unchanged. Fresh rootless36 with same authority36/control37/UUID94af and new normal-v2 baseline/ownership is selected; corrected92a guards/producers are being bound. Native30 pass remains valid. Current rootless and all dedicated/MAC/lifecycle acceptance pending; all4cases pending,WEB006 uncommitted,WEB007–026 pending.

### Execution checkpoint235 (2026-10-25)

Checkpoint235: fresh rootless36 baseline ACTUALLY PASSES1.581804s with required failed35 recovery f778. Full actual-manifest predicates/producers and independent eight-model review pass all seven corrected92a sites, exact8266 snapshot, authority36/control37 and unused normal-v2 scopes. Original real rootless36 coordinator3896941/start436990914 is NOW RUNNING; no current ARMED/runner/browser outcome inferred. Native30 ordinary pass remains valid. Required both-profile isolation/fault/MAC attribution/helper metadata/lifecycle remain pending; all4cases pending,WEB006 uncommitted,WEB007–026 pending.

### Execution checkpoint236 (2026-10-25)

Checkpoint236: fresh rootless36 real normal FAILED83.559951s after actual application start; protected681e0035/68006B. Original runner178503/start37873708 rc1/reaped81.854208s and watcher178502/start37873681 rc0/reaped82.142592s are gone; ownership/all-source closure true, final fixed-role closure true, but functional/all-input flags remain false. Original browser/gen/CID/Basic and bounded AVC+SYSCALL diagnostics are being prepared; exact six-owned-ID cleanup awaits measured drain. No cause or rootless acceptance inferred. Native30 pass stands; all4cases pending,WEB006 uncommitted,WEB007–026 pending.

### Execution checkpoint237 (2026-10-25)

Checkpoint237: original failed36 browser/gen/stop diagnosis PASSES; all3 engines unavailable vs supported/0cases, startup/TLS ready, all69 process pairs/3 exact CIDs/six observers drained. Exact6ID failed-only retirement PASSES5.411976s after opaque backup, four-path NOREPLACE preservation PASSES1.992778s, known/unknown secrets0/current4absent/key+kernel2416 unchanged. Kernel audit38 paired ioctl/cert-search events has0systemctl/connectto; separate USER_AVC collection0, which does not prove send_msg allowed because broker may log to stderr. Original broker capability/journal diagnosis pending; no permission/source change or cause inferred. Native30 stands; all4cases pending,WEB006 uncommitted,WEB007–026 pending.

### Execution checkpoint238 (2026-10-25)

Checkpoint238: exact original broker journal ACTUALLY PASSES0.910336s and records7 enforcing helper_t→unconfined_dbusd_t dbus(send_msg) refusals; current broker caps0/audit-write false, no client PID/method inferred. Reviewed seven-file singleton permission/contracts/tests patch APPLIED; focused144 tests/Ruff/docs20727/diff pass. Source25 ACTUALLY CAPTURED59f78c03/1361 and projected753a5334 (.16 only2TOML fields), then frozen with5 bookkeeping exclusions. Original strict gate25 outer3903965/start437194105 is RUNNING. Owned native016 readonly assessmentv1/v2 both refuse before installer/restorecon: channel-before-WORK and intended duplicate-control guard; freshv3 guard/call-order correction pending. Guest policy remains old2416/1d9/725f, failed36 fully preserved. All4cases pending,WEB006 uncommitted,WEB007–026 pending.

### Execution checkpoint239 (2026-10-25)

Checkpoint239: source25 strict gate ACTUALLY PASSES1279.972094s (outer3903965/start437194105 rc0/reaped/gone, all1361 hashes/modes unchanged). Assessment3 PASSES8.631138s with156 user-only relabel rows across retained .11/.13/.15, none native/outside. Private-MNT pilot PASSES10.615112s with installer disabled/.16 absent and old five trees/control326/mounts/key/kernel unchanged. Canonical artifacts pass; fixture build active and sealed source packet published locally. Fresh installed .16/.17/policy/native/rootless/dedicated acceptance remains pending. Source25 frozen, WEB006 uncommitted/all4cases pending; WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint240 (2026-10-25)

Checkpoint240: source25 canonical/fixture wheel/UI and shared pinned UBI10 micro image builds ACTUALLY PASS; image04725627d282cc67c500243f3d778640f8212399bd2b608ad5980422a14f7b81. OCI export and sealed source guest transfer PASS. Readiness-v1 FAILS1.428380s on obsolete retained ENV24 protected pathname before application/installer/policy effects; final fixed-role closure true and original outer3927939/start437371024 rc1/reaped/gone. Fresh readiness-v2 correction/full actual-path preflight pending; failedv1 retained. Source25 gate/preservation pilot valid; installed .16/.17/newpolicy/normal/dedicated acceptance remains pending. WEB006 uncommitted/all4cases pending; WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint241 (2026-10-25)

Checkpoint241: fresh source25 readiness-v2 PASSES3.976259s with326 retained inputs and failedv1 preserved. First native016 installation PASSES41.645655s, UI staging PASSES5.608731s; all108 package/6UI inputs and retained native216/rootless trees/mounts preserved. OCI/full-build transfers and image load pass. Actual shared UBI10 micro image runtime/ancestry/absence/confinement audit PASSES57.477612s; exact audit CID retired, original handles/cgroup gone, secret0/current paths absent and oldkernel2416 unchanged. Reviewed policy25 installation is now running; no newpolicy or installed browser acceptance inferred. Source25 frozen/gate valid, WEB006 uncommitted/all4cases pending, WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint242 (2026-10-25)

Checkpoint242: owned policy25 installation PASSES15.336598s with actual newkernel fdd75280 and currentreceipt0d2bdb1d/CILa051; othermodules/booleans/labels/credentials/oldfive/global evidence unchanged. ENV PASSES29.831424s, rootless017 original stage/render PASSES5.513632s and both-profile proposals PASSES5.392127s. Native.16/rootless.17 and newpolicy actual receipts align; services remain quiescent/current aliases absent, no installed functional acceptance yet. Authority37/controller38 preparation is next, then native31/rootless37 real browser and dedicated isolation/fault/MAC/lifecycle. Source25 frozen/gate valid, WEB006 uncommitted/all4cases pending; WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint243 (2026-10-25)

Checkpoint243: source25 authority37 original execution FAILS2.431101s (3931416/start437479197 rc1/reaped/gone). OSError at publication of rootless/policy.json; exact errno unrecorded. Four original queries rc0/reaped and final strict closure true; no application/global policy/credential action. Fourteen published files/seven directories and failed37 receipt retained. Native31/rootless37 have not started. New authority38/controller39 preparation must diagnose/bound the fixture resource/path failure and preserve partial37, without replay or raising limits. Source25 gate/build/runtime/install/policy/ENV/profiles remain valid; all4cases pending/WEB006 uncommitted, WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint244 (2026-10-25)

Checkpoint244: fresh authority38/controller39 ACTUALLY PASSES4.162723s (original3933783/start437573181 rc0/reaped/gone). Actual control39f7a10616 has349 inputs preserving original326 prefix; current fdd/a051/0d2 and both .16/.17 bindings pass. Historical snapshots now sequentially rejoin under originalflock after current inputs close; original37/14partial files retained, no RLIMIT/hardening change. Actual FD862+reserve64<soft1024; real local2048-file/flock15checks pass, not guest acceptance. Native31 real Caddy/installed API/browser execution is RUNNING (original3934078/start437580447), outcome pending. Rootless37 and both-profile dedicated fault/isolation/MAC/helper-filter/lifecycle remain required. Source25 frozen/gate valid, WEB006 uncommitted/all4cases pending, WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint245 (2026-10-25)

Checkpoint245: source25 native31 real shared-Caddy/built-UI/installed API/helper normal acceptance ACTUALLY PASSES350.399653s, original3934078/start437580447 rc0/reaped/gone; runner182455/start38463236 rc0/reaped347.303334s. Four modes/3engines/33assertions/0requiredskip-or-retry pass; original SUMMARYe2716cf7/379447. Actual postrun PASSES1.764232s and ordinary Basic/three-alias preservation PASSES1.822340s. Fresh rootless37 empty-secret baseline PASSES1.543812s; rootless37 original real coordinator3935832/start437626116 is RUNNING. Outcome pending; no rootless/dedicated acceptance inferred. All4cases remain pending, WEB006 uncommitted/WEB007–026 pending; source25 frozen/gate valid/pinned shared UBI10 micro retained. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint246 (2026-10-25)

Checkpoint246: source25 rootless37 ORIGINAL FAILS86.239234s (3935832/start437626116 rc1/reaped/gone). Runner187915/start38508897 rc1/reaped84.499810s and watcher187914/start38508867 rc0/reaped84.806543s are numerically absent; ownership/all-source closure true, final fixed-role closure true/heldfail[]. Functional/all-input flags remain false; exact cause unproved. Six credentials/current Basic+aliases retained pending bounded original browser/gen/CID/Basic diagnosis and failure-only backup/retirement/preservation. No replay or policy change selected. Native31 normal/postrun/preservation valid; all4cases pending,WEB006 uncommitted/WEB007–026 pending, source25 frozen/gate valid. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint247 (2026-10-25)

Checkpoint247: failed37 original metadata diagnosis PASSES0.957949s: all69 pairs/3CIDs/6stop observers drained, all3baseline browsers unavailable vs supported/0cases but browsers exit0/closed, startup eventually200 and peer-otherTGID refusal true. Exact6ID failure-only opaque backup/retirement PASSES5.604971s; Basic/3aliases NOREPLACE preservation PASSES1.864468s, secrets known/unknown0/four current paths absent. Broker-v1 diagnostic read obsolete literal window and failedprojection before causal output; freshv2 actualoriginalwindow PASSES0.859487s with0entries, not permission proof. AVC+USER originalwindow reader PASSES0.910696s:38 paired ioctl/cert events,0USER_AVC,0fixed systemctl/Podman executable attribution. Cause remains unproved; no grant/source change selected. Fresh bus-only read-only diagnostic is being prepared under original hardening; no normal replay/acceptance. Native31 valid/all4cases pending/WEB006 uncommitted, WEB007–026 pending, source25 frozen/gate valid. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint248 (2026-10-25)

Checkpoint248: NEW owned fixed bus-only diagnostic executes the real five-property systemctl query under helper_t/UID983 with original hardening, then returns AccessDenied (rc1/stdout0/stderr40B). Outer3941691/start437822806 rc1/reaped/gone2.093795s; query190343/start38705582 rc1/reaped/gone0.012896s, no timeout/overflow. Root/child/worker/unit normal-stop/reset/cgroup closure pass, global fdd/a051/0d2/key/credentials unchanged. Diagnostic false flags retained; no permission or original-method cause inferred. Preparing two-window original USER-MANAGER70491 journal metadata reader; brokerzero doesnotexplainthisrefusal. Native31 valid/rootless37failed and fullycleaned; all4cases pending, WEB006 uncommitted/WEB007–026 pending, source25 frozen/gate valid. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint249 (2026-10-25)

Checkpoint249: original user-manager journal reader ACTUALLY PASSES0.944871s. Failed37 window contains7 enforcing helper_t→usr_t SERVICE(status) refusals; separate stopped-API bus diagnostic has1 helper_t→unconfined_t SYSTEM(status) refusal. No reporter→client attribution. Fixed fragment reader PASSES0.884499s: original indexed .17 rendered/packaged API bytes3196/565 are usr_t, fixed/current binding is etc_t, all predating original failure. Existing deployment contract requires systemd_unit_file_t for target+binding; no usr_t/etc_t/newSYSTEM grant selected. Preserve17/allold7 and original binding inodes/SIDs; prepare fresh rootless18 with narrow persistent label provisioning before profiles/activation. Original installer permits genuineimage047/software16 reuse; dd590 build metadata17 stays byte-exact, no built18 claim. Source25 frozen/gate valid/native31 valid; newauthority39/control40 andnative32/rootless38 are preparation only. All4cases pending,WEB006 uncommitted/WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint250 (2026-10-25)

Checkpoint250: fresh owned rootless18 staging ACTUALLY PASSES8.071190s using the existing genuine software16/image047 build; no built18 image claim. Passive unit-label readiness PASSES3.647956s. Original provision-v1 remains FALSE/ValueError after preserving7 original binding inodes/SIDs and adding13 exact new-candidate regular-file rules; its first system-link rule is rejected by the existing vendor equivalence. No restorecon or new global binding publication ran in that failed attempt. Recovery readiness PASSES3.428643s and verifies the exact partial state. Fresh completion PASSES10.837278s without replaying13 additions or7 preservations:5 exact user-link rules,13 new18 file labels,7 first NOREPLACE publications and7 link labels;18 owned local rules plus2 unchanged vendor defaults satisfy20 objects. Allold7 releases/control349/original backups/key/CIL/receipt and compiled kernel fdd remain unchanged; no new SELinux grant. Authenticated native16/rootless18 profiles PASSES6.007334s, temporary selectors preserved/absent and permission bits unchanged. Authority39/controller40 publication PASSES5.152946s,21 files/control40c7cf53f0/363 inputs with original349 ordered prefix, current label/SELinux/deployment/visudo checks and fixed-role closure. Actual FD876+reserve64<soft1024, limits unchanged. Native32 original3957799/start438399552 is RUNNING; no outcome inferred. Source25/gate25 remain frozen/valid; native31 evidence stands, required fresh native32/rootless38 and both-profile dedicated fault/isolation/MAC/helper-filter/lifecycle acceptance remain pending. AUTH-08/HOST-01–03 pending; WEB006 in_progress/uncommitted and WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint251 (2026-10-25)

Checkpoint251: source25 native32 real shared-Caddy/built-UI/installed native16 API/helper ordinary normal ACTUALLY PASSES340.545725s (original3957799/start438399552 rc0/reaped/gone), all4modes/3engines/33host assertions and12 same-Caddy untrusted-TLS negatives,0required retry/skip. SUMMARY0413b309/383165 and generation0023b5159a374ff1900ae793b4806a72 close; original checker191070/start39282313 rc0/reaped337.692983s. Native postrun PASSES1.833743s and metadata-only Basic inode118921755/3alias NOREPLACE preservation PASSES1.921970s. Fresh rootless38 empty-secret baseline PASSES1.661575s. Original rootless38 real run then FAILS90.248917s (3959326/start438448331 rc1/reaped/gone); runner196469/start39331073 rc1/reaped88.624725s, watcher196468/start39331045 rc0/reaped88.921147s. Ownership/all-source closure and final strict role closure are true, heldfail[]; functional/all-input flags remain false. Exact cause is unproved; bounded original metadata/journal diagnosis and failure-only six-ID retirement/Basic+aliases preservation remain pending, with no replay or new permission selected. Native32 ordinary evidence stands; rootless38 and both-profile dedicated fault/isolation/MAC/helper-filter/lifecycle clauses remain required. Source25/gate25 frozen/valid/current fdd/a051/0d2 unchanged. AUTH-08/HOST-01–03 remain pending,WEB006 in_progress/uncommitted/WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Execution checkpoint252 (2026-10-25)

Checkpoint252: failed rootless38 original metadata ACTUALLY PASSES0.895367s (3960590/start438486148): startup ready, all3baseline engines unavailable versus supported/0cases, original reason absent,69original pairs/3CIDs/6stop observers drained. Exact-six-ID failure-only backup/retirement PASSES5.415156s (3960950/start438496162); metadata-only Basic inode118921888/three-alias NOREPLACE preservation PASSES1.964831s (3961157/start438502325), known/unknown secrets0 and current4paths absent. Original rootless38 remains false; no lifecycle acceptance is promoted. Manager70491 original-window read PASSES0.884887s (3961443/start438510324):88journal entries,26enforcing helper_t→unconfined_t SYSTEM denials,13start+13status; no service/usr_t refusal remains. Kernel/USER read PASSES0.962106s (3961676/start438517515):153exact paired AVC/SYSCALL records plus13USER_AVC. Fixed Podman executable is attributed to13 syslogd_var_run_t directory-search/openat,13 user_tmp_t directory-write/faccessat269 and13 container_ro_file_t directory-ioctl16 refusals;13userspace records show helper_t→systemd_logind_t dbus send_msg denial. Manager/broker reporters are not client PID/method attribution. These are observed boundary refusals; exact original fatal path/cause remains unproved and no start/status/logind/ioctl/search/write grant or source change is selected. Native32 ordinary evidence stands; rootless and both-profile dedicated fault/isolation/MAC/helper-filter/lifecycle acceptance remain required. Source25/gate25 frozen/valid, compiled fdd/CILa051/receipt0d2/key unchanged. AUTH-08/HOST-01–03 remain pending,WEB006 uncommitted/WEB007–026 pending. No production/NAS/live Cockpit/rollout/merge/push/tag.

### Application development continuation (2026-10-25)

2026-10-25 development continuation: source25 capture, gate, artifacts and original outcomes remain retained. Native32 acceptance passed; rootless38 failed and is drained, retired and preserved. The corrected INFO diagnostic succeeds under existing confinement; it does not establish full container-inspection acceptance. Following the user instruction to cut orchestration overhead and refocus application development, source25 is unfrozen for targeted application diagnostics and the rootless fix. Use existing fixtures and concise test evidence; required source/native/rootless/isolation/fault gates remain mandatory before WEB006 completion. All four cases remain pending. No production, NAS, merge, push, tag or rollout actions.

2026-10-25: WEB-006 completed in this commit after the current strict gate
(7,806 Python tests plus strict frontend/Cockpit), native/rootless real-Caddy
browser acceptance and both dedicated isolation/fault cohorts pass. All105
rootless/57 native file-and-attachment operations have unique enforcing kernel
joins; original inputs, operation handles, mounts and lifecycle closure pass.
Task006 records exact current artifacts and retained failed attempts.
AUTH-08/HOST-01–03 are complete. The selector advances to WEB-007. No runtime
dependency or production/NAS/live Cockpit/rollout/publication action follows.

2026-10-25: WEB-008 completes guarded atomic configuration application and original-operation read-only recovery. Strict gate5, native/rootless normal workflows and representative process-crash, legacy, stale-tag, queued-policy and genuine-quota acceptance pass; original failed cohorts remain retained. CONFIG06–11 complete. Continue WEB-009; production rollout and final plan-wide acceptance remain separate.

2026-10-25: WEB-009 completes bounded publication-pinned README capture through
joined sync/repair and existing technical refresh. Strict gate8500 backend plus
full web/Cockpit passes; installed application functional capture and actual
previous-release binary drill pass, with storage simulation and catalog rollback
refusal explicitly disclosed. CARD01–06 complete. Exact card read is next;
rendering remains WEB-014. Shared image retains pinned UBI10 micro/no runtime Node.
No production/NAS/live Cockpit/rollout/publication authority changes.

2026-10-26: WEB-010 completes authenticated exact-publication card reads. Strict
gate3 and installed real-Caddy/typed-client acceptance pass; CARD07–09 complete.
Retained inventory/count failures are corrected without runtime changes and
original failures remain recorded. Shared image stays pinned UBI10 micro with
no runtime Node. Continue WEB-011 query and operation state; README rendering
remains WEB-014 and production rollout/publication remain separate.

2026-10-26: WEB-011 completes authority-scoped query state and original-operation
recovery. Strict gate2 passes1501.198s and nine genuine native Basic/Caddy/API/helper
browser cases pass89.587s, including real API restart, lost202, quotas and tabs.
The first installed run exposed an unbound native fetch receiver; its failed
browser and succeeded original operation remain retained. The central binding
fix and production-mount regressions pass. OPS01–05 complete; continue WEB-012.
Shared API/UI image remains pinned UBI10 micro without runtime Node. Full Library,
job forms, later host/cross-browser/platform acceptance and production rollout
remain separate tasks; no production/NAS/live Cockpit/publication action occurs.

2026-10-26: WEB-013 completes exact-publication model/dataset detail pages.
Strict gate1 passes1608.747s (8591 backend tests and required web/Cockpit checks),
with all1431 frozen hashes/modes unchanged. Thirty-nine one-attempt installed
Caddy/API cases pass309.282s across all three engines, including actual Library
navigation, six tabs, current/repair/prune pinning, useful manifests during
supplemental failure and bounded keyboard/mobile locator use. CATALOG06–08
complete; human guide/actual synthetic screenshots and living contracts align.
The first private fixture setup failure is retained, with corrected source in a
fresh successful cohort and no product rebuild. Shared image4e04c3d1 retains
actual pinned UBI10micro ancestry and verified no-runtime-Node/tooling. Continue
WEB-014; production rollout, NAS and final platform/parity acceptance remain
separate. No production/NAS/live Cockpit or publication action occurred.


2026-10-26: WEB-014 completes bounded inert archived README rendering. Strict
gate4 passes1465.321s on unchanged4b336cd3…/1441 inputs; all36 installed
three-engine cases pass235.043s with90 zero-CSP checkpoints and0POST. Matching
UBI10micro image/no runtime Node, exact source/provenance, capture refusals and
Recovery radio compatibility are proven. CARD10–12 and human guides/screenshots
are complete; original withdrawn/interrupted/failed/diagnostic evidence remains.
[Task014](tasks/web-014-safe-markdown-rendering.md) owns exact evidence. Next is
WEB-015; production rollout, NAS, full platform/parity and final acceptance remain
separate. No merge, push, tag, rollout or live Cockpit removal.


2026-10-26: WEB-015 completes structured configuration/tag workflows and original
host-outcome recovery. Strict gate3 passes1645.369s on unchangedbc1d0602…/1457;
33 installed three-engine normal cases pass976.213s with24 original operations/
12 confirmed applications, then three original single-Apply fault/recovery cases
pass84.722s. The original interrupted receipt/installed-unconfirmed pending host
state is preserved, never replayed or promoted. CONFIG-12 and actual guide/screens
are complete; all original roles/Hub drain normally. Task015 retains exact pins,
all failed attempts, source3 Firefox-origin fix and scoped native owned-RO-NFS
limits. Continue WEB-016; later platform/parity/rollback/final acceptance and
production rollout remain separate. No production/NAS/live Cockpit/publication.


2026-10-26: WEB-016 completes existing jobs and exact operation and run reports.
Strict gate 4 passes in 1781.806 seconds on unchanged source 7fa3bb9f… / 1473
inputs, with 8608 backend tests, 3557 web unit tests, 3799 combined frontend tests,
required Cockpit, build, wheel, browser and documentation checks, and zero required
skips. Fresh installed native .36 acceptance passes all 47 current cases: 36 normal
browser cases, nine busy, partial and integrity cases across three engines, and
two actual SDK signal stops. Exact results and reports, bounded history paging,
true lost-response original-key recovery and backend continuation are proved.
Final integrity damage remains unhealed. The source, wheel, UI and shared UBI 10
micro image match, with no runtime Node. All original roles drain, and 667 old
fixture objects and five baseline pairs remain unchanged. Task016 retains exact
current hashes, earlier failed gates and cohorts, and SDK1's unchanged false
collector result with separate retrospective closure. OPS06–09 and human guidance
are complete. WEB-017 remains pending for activation after this commit.
Production, NAS, new rootless UI, WEB022 platform, parity, final acceptance and
rollout remain separate. No merge, push or tag action occurred.


2026-10-26: WEB-017 activated after dependency WEB-016 committed as `b48bc53`.
The existing typed maintenance routes, shared operation state and disposable
application environment are reused. Scope, required gates and production
restrictions are unchanged; task017 owns execution status and evidence.


2026-10-27: WEB-017 completes guarded maintenance and finding-based exact repair.
Strict gate2 passes in 1768.399s on unchanged S2 8e320cf1… / 1481 inputs;
8610 backend / 3858 combined frontend and all required Cockpit/build/docs checks
pass without required skips. All 39 current installed browser cases pass across
three engines, with 33 original browser POSTs, 331 trusted requests and 78 zero-CSP
checkpoints. Original repair collector failure is retained and separately
qualified by exact read-only closure of legitimate provider-cache link changes;
no job is replayed to obtain acceptance. Final ambiguous journal, damaged retired
predecessors, grace records, 4128 older objects and baseline five remain preserved.
Matching shared .42 fixture artifacts retain pinned UBI 10 micro without runtime
Node. MAINT01–06 and human guides are complete. Task017 owns exact evidence and
limits. WEB-018 is pending next; production/NAS/new rootless/platform/parity/final
acceptance and rollout remain separate. No merge, push, Git tag or live Cockpit removal.


2026-10-27: WEB-018 activated after WEB-017 committed at `bcde0dd` with a clean
checkout. Decision156/INV022 specify fixed independently observable host effects,
exact original-process stop and disjoint host/domain runner ownership. Source,
strict typed browser ports, narrow optional native labels and human guidance are
in progress. Existing guest/Caddy/engine will be reused; no production or new
engine framework is authorized. Task018 owns actual gates and acceptance.


2026-10-27: WEB-018 completes fixed schedule, exact observer and bounded journal
APIs. Strict gate6 passes1813.441s on unchanged source5 `415d9b73…`/1500 inputs;
all48 scoped installed cases pass across three engines:33 native (separately
qualified original collector failure, never replayed) and15 normal rootless
cases. Two unshipped assertion corrections leave runtime/artifact source2 exact.
The shared images retain verified pinned UBI10micro with no runtime Node.
HOST04–09, human guides and living contracts are complete. Existing engine/Caddy
and all original pending/failed/damaged evidence remain preserved. Task018 owns
exact proofs and limits. Continue WEB-019 forms; later platform, compatibility,
retirement, final acceptance and production rollout remain separate. No merge,
push, Git tag, NAS or live Cockpit action occurred.

2026-10-27: WEB-019 activated after committed WEB-018 and its clean strict/48-case acceptance. Complete rendered Administration using existing typed authorities, query/operation owners and test environments. No new engine or privilege surface is authorized.

2026-10-27: WEB-019 completes the rendered Administration workspace, independent
health/readiness/permission/software facts, warning guidance, one-use fixed
schedule/original-observer controls, bounded journals, explicit diagnostics and
global original-outcome recovery. Strict gate2 passes1994.337s on unchanged
S3 `107e45b4…`/1519 inputs with8927 backend/3690 web unit/4007 combined tests,
94.94% line/90% branch coverage and no required skips. All42 accepted scoped
browser cases pass:27 native pairs join original Chromium9/Firefox9 with targeted
WebKit9 plus separate read-only qualifications, preserving both failed original
collectors;15 rootless pass normally254.036s. The fixture's60s sync wait is
retained and restored to shipped3600; the corrected journal join admits exactly
one legitimate failed SDK sync journal, never a publication. Existing Caddy/
engines and pinned UBI10micro shared images without runtime Node are retained.
OPS-10, human guides/screenshots and living ADR/invariant/contracts are aligned.
Task019 owns exact sources, original evidence and limits; aggregate3ebb9e27…
records506 trusted requests/84 clear CSP checkpoints and normal rootless drain.
WEB-020 is pending next. NAS/production/full-platform, compatibility, retirement,
final gate and rollout remain separate; no merge, push, tag or live Cockpit action.

2026-10-27: WEB-020 activated after WEB-019 committed at `abaef80` with a clean
tree. Harden actual end-user accessibility, hidden/disconnected polling and
bounded large-data workflows, measuring the existing budgets through real
Caddy/API in all three engines. Establish actual owned reader/keyboard/zoom
evidence; preserve earlier acceptance and all uncertain originals. Reuse owned
test infrastructure and keep production/NAS/retirement/rollout outside this task.

2026-10-27 WEB-020 checkpoint: matching source4 strict gate passes with8978
backend and4029 combined web tests, no required skips,95% line/90.01% branch
coverage and completed real-API100-cycle integration. Native53/rootless54 stock
artifacts are built; native53 prefix installation and confined module imports
pass. Actual initial native JavaScript requests total204,904 gzip bytes.
Installed cohort7 stops after10 usable Library samples at a read-settlement
deadline, with normal role closure and unchanged fixture data. Twenty-sample
p95, final installed browser/zoom/reader/positive-helper/transition acceptance
remain open. Task020 owns exact evidence; no WEB020 commit or WEB021 advance.

The subsequent source4 cohort8 completes20 Chromium loads, measuring2.754s p95,
then fails the connected repository-detail contrast scan. Normal role closure,
unchanged fixture data and both false originals are retained. A shared-foreground
contrast fix is now implemented; the next matching source/gate and artifact
acceptance are pending. The harness's actual authenticated browser cache behavior
is being checked independently before attributing its repeated full asset
transfers to application performance. Task020 remains active and uncommitted.

Source5 cohort9 verifies default-cache restoration on the actual Chromium SDK
protocol owner and completes20 samples at2.234s p95, still above2s. All29 covered
accessibility scans have no serious/critical finding. Its large-manifest failure
is reproduced as an oversized ASCII-escaped response; a new mixed-Unicode fixture
preserves file/path/work stress while fitting the existing browser byte limit.
Source6 now adopts decision157's bounded frozen-model parsing reuse only after
fresh authoritative reads and charges. An isolated installed55 full-query
comparison improves0.981s to0.630s with identical output; final browser evidence
is still required. Actual SPA100-cycle retention, all-engine native/rootless,
reader/zoom/positive-helper/transitions and a matching strict gate remain open.

2026-10-27 later WEB-020 checkpoint: source6 matching gate4 passes9030 backend/
4029 combined web tests with unchanged inputs. Installed native57 cohort10
closes normally but remains false:20 Chromium samples yield2.844s p95 against
the unchanged2s target. The large manifest now renders and supports its keyboard
jump;12 metadata-button accessible names fail the next scan. The corrected
names pass8 component tests and require updated artifacts/browser validation.
Initial JavaScript is204,899 gzip bytes, below358,400. All-engine positive
workflows, SPA retention, transitions, genuine zoom, application reader and
installed slow/cancelled/stale reads remain acceptance work; WEB-020 is not
complete and WEB-021 has not started.
Task020 owns detailed evidence; no commit or WEB021 advance has occurred.

2026-10-27 source7 checkpoint: matching strict gate5 passes0 in1522.413s with
unchanged1528 inputs. Native59/rootless60 stock builds and fresh59 prefix/import
checks pass. Live installed59 cohort11 completes Chromium's13 cases/100SPA
cycles at1.793s load p95; Firefox's load passes at1.874s, with connected/large
accessibility and its first50SPA cycles passing. WebKit/final original closure,
positive workflows, actual zoom/reader, races and installed transport cases remain
open. Source-only coordinators and separate candidate-staging qualification do
not close those acceptance rows. WEB-020 remains active and uncommitted.

Later original-cohort audit5 confirms Chromium and Firefox each complete13
cases/100SPA cycles, with20-sample load p95 at1.793s/1.874s. WebKit's initial load
passes at1.953s, alongside connected/large-manifest accessibility and30SPA cycles.
Its remaining cycles and original normal closure are pending; all other open
WEB-020 acceptance remains required before the single work-package commit.

Cohort11's original result is now false with normal verified closure. Separate
read-only retrieval preserves its9.4MB report beyond the old8MiB artifact cap:
Chromium/Firefox complete13 cases/100SPA cycles each, all3 load p95 pass and90
accessibility scans pass. WebKit stops at95 cycles on1ms time-origin drift despite
unchanged actual Document/navigation fences; a corrected whole100-cycle WebKit
run remains required. Matching gate5 read-fixture and all3 initial JavaScript
request-closure joins pass. Other installed WEB-020 acceptance remains open.

Independent accessibility review identifies three intentional labels on generic
containers that require explicit nameable group roles. WEB-020 includes this
semantic correction, focused regressions and ADR145/human guidance amendments
in a new source8 snapshot. Existing source7 artifacts/results stay preserved;
its targeted WebKit100-cycle run continues against those immutable inputs.
Fresh source8 artifacts, matching gate and installed acceptance remain required.

Source8 now freezes1528 inputs at32e7f0b7, with59 focused component cases and
matching native61/rootless62 builds passing. Both actual images have no runtime
Node/package managers; gate6 is running. The original source7 targeted WebKit
run closes normally but fails at83 cycles on a15s Library-settlement predicate;
its unchanged archive/configuration, zero POSTs and exact closure are retained.
Source8 final browser/reader/installed workflow acceptance remains open.

Matching source8 gate6 passes1508.707s with unchanged1528 inputs,9030 backend/
4029 combined frontend tests and all required checks; the source8 HTTP fixture
join also passes. Native61's first prefix stage remains false on its empty UV
lock permission check after package/asset installation. A separate guarded
completion is being prepared; source8 installed/browser acceptance stays open.

The separate completion-v1 also refuses before mutation on a root-inclusive
versus descendant count mismatch. Fresh read-only proof confirms5319 total/
5318 descendant entries, the unchanged0666 empty UV lock, absent runtime/
installation receipts and the quiet baseline. All failed records remain intact;
a new scoped completion version must join those actual facts.

2026-10-28: scoped completion-v2 (`fd9f4bef…`) and protected public-helper
stage-v4 (`45e53ff4…`, manifest `e920ff4f…`) now pass with original transports
reaped and no unknown cleanup. The sole empty noncode UV lock retains its inode
with mode0600; code, current49 and the quiet baseline are preserved. Original
false stage/completion-v1 records remain unchanged. New bound three-engine core
acceptance is next; remaining WEB-020 acceptance and its commit stay open.

The first source8 core cohort now runs against frozen graph `8a36274c…` and
manifest `ac4400d1…`. Actual stage/import completion is separately joined by
read-only qualification `a59970c1…`; its original final read-back NameError
result remains false/unknown. The entire three-engine load/accessibility/100-SPA
cohort owns the quiet measurement lane. No browser result is inferred early.

That source8 cohort now closes false/known in1373.163s after Chromium completes
13 cases/100 cycles at1.876s p95. Three supported100-selector requests exceed
the collector's32-pair metadata bound; their detailed queries remain unknown,
while complete native origin counts and200 response records are retained.
Separate qualification `b67e9697…` preserves completed Chromium facts and the
raw false result. Corrected Firefox/WebKit whole-case coverage is next; fresh
root closure releases the quiet lane with current49/base5/5314 archive and
configuration files unchanged. Remaining WEB-020 acceptance stays open.

The corrected Firefox/WebKit whole-case target now runs from frozen closure
`acff756b…` after successful protected stage/import `7af15e42…`. It explicitly
requires the separately qualified Chromium scopes, keeps every per-engine case
and budget, and owns a new quiet lane through both engines' measurements.

2026-10-28 Source9 checkpoint: the primary-action hover contrast correction
freezes1528 inputs at776470cc; matching gate7, native63/rootless64 stock builds,
scoped no-runtime-Node proofs and root/prefix real API integration pass. Separate
runtime completion and protected public-helper staging pass while the original
false installation is retained. Fresh all-three-engine core-v2 acceptance is
running under a whole-target quiet reservation after protected stage/import.
Its complete JSON evidence retains every field within the unchanged16MiB cap
by removing formatting whitespace. Native visibility still fails Firefox in the
separate inert prerequisite; positive workflows, rootless acceptance, real races,
genuine zoom/reader and final case mappings remain open. WEB-020 is active and
uncommitted; WEB-021 has not started. Task020 owns detailed evidence.

2026-10-28 WEB-020 fixture sequencing amendment: retain the three completed
current49 GET scopes (core, read-budget negatives and read transport), their
normal closures and every failed race record. Canonical staging and genuine
protected native fixture preparation may precede the still-required prefixed
race scope. Requiring all four scopes before that preparation was an agent
fixture dependency assumption, not an acceptance requirement; it creates a
cycle because Basic read-only Doctor correctly requires fresh protected Hub
authority. This amendment changes test order only. It grants no application
authority, reduces no scenario or budget and supplies no fourth-scope pass.

The next race fixture must use actual supported old51 and new63 profiles,
version-matched API/helper proof, the fixed hfcache principal, private /etc and
/srv bindings and a separately provisioned Hub-only protected policy. A runtime
prefix survey alone does not qualify an official native51 installation. Fresh
qualification, or guarded official staging if absent, precedes browser effects.
Each engine still opens the real old51 page before replacement by63, retaining
the owned browser while API/worker/helper phases drain normally. The full
controller teardown still requires known browser closure; unknown dependencies
are preserved. New executable copies and effects require concrete source review.
Native/rootless positive workflows, genuine zoom/reader, affected Firefox
performance and every final gate remain required. Historical artifacts,
contracts, receipts and failed outcomes are preserved unchanged.


2026-10-28 later Core4 checkpoint: the unchanged Source9 build remains under
acceptance. Core3's bootstrap-body observer fails after complete Chromium cases;
its original failed/known result and normal closure are preserved. The reviewed
first-response lifetime fix is staged/imported and Firefox-only attempt2 now
owns QUIETv4. Historical accepted Chromium/WebKit checks remain separate; no
stock-Firefox donation or fresh acceptance is inferred. Native/races/rootless,
genuine zoom/reader and final mapping/documentation work remain open; task020
owns exact evidence and WEB-021 has not started.

Subsequent actual Core4 completion: affected modified Firefox passes13cases,
20 loads at1.802s p95,100SPA and30AX in1375.871s with normal original closure.
Fresh current49/base5/confinement/quiet audit passes and QUIETv4 is released.
The remaining actual read-negative/transport, native/races/rootless and genuine
zoom/reader acceptance stays open; task020 owns exact records.

Later Negative5 original closes failed/known on WebKit CJK diagnostic errors,
with normal closure and fresh quiet audit. Lost before-facts are not reconstructed;
a new affected-Firefox collector will persist them. Transport6 stage/import pass
and actual attempt1 runs under quiet; task020 retains exact records and all
remaining native/race/rootless/zoom/reader acceptance. No WEB-020 commit yet.

Subsequent Transport6 actual completion passes all12cases across3engines in
585.171s, with normal closure and fresh current49/base5/confinement/quiet audit.
Negative collection/diagnosis and actual native/races/rootless/zoom/reader remain
open. Task020 records exact evidence; WEB-020 stays active and uncommitted.

Subsequent actual scoped Firefox negative qualification535fcda6 accepts both
original cases/byte and ownership predicates, retaining two runtime ctime
differences and the failed aggregate. Official native51/63 target-only stages
now pass119wheel/7UI/layout/current49-preservation with actual equal3closure
maps. Initial63 preparation is locally bound/preflighted but unexecuted; the
WebKit diagnostic precedes selection. Task020 owns exact records and open work.

Subsequent actual single-WebKit diagnostic7 now closes failed/known with strict
errors preserved (`292edbe8…`, wrapper `95a4f59c…`). Full same-origin Library
facet access-control messages are captured; cancellation timing is evidence,
not a causal waiver. Both post-inspections and normal closure complete; fresh
current49 audit `d8492d2e…` passes and quiet is released. Root initial native63
preparation now runs from actual targets/bindings, with roles stopped and no
acceptance inferred early. Diagnosis continues alongside the remaining actual
races/positive/rootless/zoom/reader work; task020 owns exact evidence.

Subsequent actual WebKit8 original CJK scope separately qualifies (`14442103…`):
case/strict zero SDK errors/byte limits/stock refusal/preservation/normal closure
pass. Raw and added auxiliary Window diagnostic flags stay false; its fourth
Document exceeds the unchanged3 cap, with no auxiliary event-absence claim or
original predicate waiver. Fresh `5ee44b98…` passes and quiet is released.
Corrected initial native preparation7 now runs, reusing exact14 sealed inputs
read-only and using verified63 Python for setup. Task020 retains all exact facts;
genuine native races/positive/rootless/zoom/reader/final work remain required.

Actual initial preparation7 now passes (`fc09e327…`), selects supported63 with
roles stopped and retains old objects. Actual initial/target bindings `ddd65682…`,
Root review and local race11 activation `77ff51e1…` pass; protected stage/import
`df0ac983…`/`458d6657…` close normally. Genuine native51A→63A→63B attempt1 is
running; no race/restoration/completion or positive workflow claim is inferred.
Task020 owns exact records and the remaining acceptance/commit work.

2026-10-28 subsequent user steering: stop further validation of test machinery
and exercise the real application directly. Preserve the existing fixture drafts,
failed outcomes and original acceptance requirements. WEB-020 stays active and
uncommitted; task020 remains the evidence authority and WEB-021 has not started.

Direct guest inspection resolves the first old51 helper startup failure as a
documented missing runtime directory. Applying its specified ownership/modes and
existing SELinux labels starts the helper without policy or hardening changes.
Normal drain and the official installer return to the already prepared 0.2.63 target;
the retained helper unit and prior51 variant are preserved. This is not race or
Restored63 acceptance. Real helper/verifier/API/shared Caddy now run, with 200
health/catalog/native HostStatus/UI/bootstrap and six native grants. All three
stock browsers pass trusted-HTTPS desktop/mobile navigation and later loaded
Library240/search/3997-file keyboard checks with 10 mounted rows. Original script
envelope/auth-challenge errors remain false and are not product regressions.

The direct checks reveal a genuine archive-health classification bug for the
four documented optional publication directories. The narrow product fix passes
153 regressions and Ruff; the full product gate is running, not yet passed.
Distinct 0.2.65 source/wheel/UI artifacts are built in
`/home/tyler/web020-app-native-0.2.65-build-6125d5269844`; installation and actual
fixed-health retest are pending. All six owned acceptance rows remain open.
Native writes/race-equivalent application workflows, rootless, real zoom/reader,
applicable performance and final mappings/docs/checks remain required before the
single WEB-020 commit and WEB-021 handoff. No production/NAS or remote effect
authority is added.


2026-10-29 current direct application checkpoint: the archive fix and reviewed
wire-audit update pass the full `scripts/check.sh` gate2 (exit 0, 9039 passed,
52 deselected in 1196.62s; frontend/Cockpit/installation/build and all other checks
passed). Logs remain at
`/var/tmp/web-020-validation-nvj5zeg7/direct-application-fix-gate2.*`.
Native 0.2.66 source `5d1fbe6e…`/wire `320c5fb1…` is actually staged and normally switched/started
(helper 25579/verifier 25605/API 25613/Caddy 25619). Original switch `f74ca077…`
and HTTP `d83eb9c0…` show archive initialized, zero unknown entries, ready/valid
policy, supported native six grants and matching 0.2.66 UI/bootstrap. Native 0.2.65 stays
unqualified/inactive; rootless 0.2.67 is built only without guest acceptance.

The original succeeded preview `e4fb1f4f…` and interrupted Apply `1b808e75…` remain.
Transmission exists, the original application key is lost and no replay occurs.
Upgrade attempt `e41f6f0…` remains false because switching preceded all three old
pages being ready (Firefox connection refused, WebKit not reached); exact upgrade
acceptance remains required. All six owned rows stay open; WEB-020 remains
in_progress/uncommitted with native writes/race-equivalent flows, rootless,
genuine zoom/reader and final mapping/documentation/commit work outstanding.
Task020 retains the exact actual paths and scopes; earlier failed records remain.


2026-10-29 direct application continuation: original interrupted-operation
recovery passes all three browsers in `27fad989…` (raw exit0), retaining the same
imported ID after reload and blocking new diagnostic jobs, with zero POSTs/errors.
Native 200% zoom passes seven surfaces for Chromium/WebKit in `aaf812d0…`; its raw
aggregate remains exit1 for Firefox pointer-coordinate activation failure.
Firefox-only keyboard continuation `f3c0a3cc…` exits0 on all seven surfaces with
fixed 1440×1000 native PNGs, CSS viewport1440x1000→720x500, six true DOM CSS hits,
focus/overflow/dialog checks and zero POSTs/errors. No Firefox pointer or reader pass
is claimed. Earlier failed zoom `79707d48…` remains preserved.

Task020 and the evidence ledger record exact raw artifacts and functional scope
against canonical native 0.2.66 source `5d1fbe6e…`/wire `320c5fb1…`/UI `1faa4d4e…`. UX-01–03 advance
only to in_progress; all six owned rows remain open because required layer/clause
coverage is incomplete. No existing unit node is invented or failed flag changed.
WEB-020 remains uncommitted; Root alone continues actual application checks.


2026-10-29 subsequent direct upgrade: all three ready old63 browser Documents
survive the official66 switch, explicitly reconnect to **Interface update
required**, clear private API/HostStatus observations and retain their old marker.
Explicit reload connects to66, with zero POSTs/page errors in every row. Original
`16210ea8…` exits0; both preview/interrupted Apply receipts remain and no Apply is
replayed. Official roundtrips `32d2cef5…`→63 and `2428a034…`→66 retain their records;
final services are helper30749/verifier30767/API30775/Caddy30781. Earlier premature
upgrade failures stay false. Task020/ledger retain stdout464eae74…/6710B and scoped
AUTH-10/UX-01 functional evidence. All six owned rows remain open/in_progress or
pending; no missing layer or remaining profile/workflow clause is invented.


2026-10-29 direct catalog/row completion checkpoint:

Actual native66 offline catalog writes now exist once per engine: Chromium
`0ffe8fcf0df51146d674f13406706a3f`, Firefox
`34d046383a320b6ec34c9c15777bbdb5` and WebKit
`6a4198c1fb65fb36cc2a3000ed09d86c`. Each original receives202 after one POST and
succeeds with domain exit0/**success_with_warnings**, HFWRN011, one captured tag
snapshot, one written observation and zero failed records. Technical evidence
remains partial/unsupported for this fixture; no integrity claim follows.

Raw mutator scripts remain exit1: Chromium's DevTools body resource is unavailable,
Firefox's separate Node observer lacks CA trust, and WebKit's result-region lookup
is wrong. Their jobs are not replayed. Separate original-key/result GETs confirm
Chrome/Firefox saved keys and exact succeeded operations. The read-only all3 UI
continuation `d093bb9f…` exits0, opens **Validated original result**, renders the
actual warning/counts, reloads and explicitly observes the same IDs, with zero
POSTs/page errors. All three mutators are known terminal/closed. Exact originals
and raw hashes are in task020 and the evidence ledger.

CATALOG-09 completes its own matrix/layer requirements using mapped unit/integration,
original Source9 real functional read scopes and current native66 update-clearing,
error/result and recovery observations. Historical Source9 hashes remain unchanged;
no current-source/performance or rootless result is donated. At that checkpoint AUTH-10 stayed
in_progress for one specific installed predicate: the upgrade's old contexts held
no unresolved browser records, so separate recovery/reload and authority-transition
checks do not directly observe a retained unresolved handle across that transition.
Its unit coverage remains valid; this gap is not an Orca/rootless requirement.
The subsequent AUTH-10/UX-01 completions and retained UX-04 scope are recorded below. WEB-020 stays in_progress/uncommitted.


2026-10-29 rootless Gen2 negative-state checkpoint:

UX-04 is completed using retained original Source9 load/JS/100-SPA/DOM and
encoded-retention evidence, existing real HTTP integration and 95%/90.01% coverage;
no Source9 hash is relabelled as 5d1. The 189-runtime-path comparison changes only
archive health, its wire-audit pin and two generated wire artifacts. RSS/unsupported
heap limitations remain. UX-03 has existing component/API mappings but stays open
for the actual 1440/390/reduced-motion/font check; no new test was added.

Current rootless67 Gen2 negative UI case `56ca7d31…` passes all three browsers,
raw exit0 with normal closure and zero POSTs/page errors. The real Library reports
HFVER007 without an invented table; Administration is unavailable and configuration
GET503/HFAPI022 supplies no private edit controls. Six axe4.14.0 whole-document
scans have zero serious/critical **violations**, while moderate region violations
and serious color-contrast **incompletes** remain. This is not full accessibility,
contrast or positive rootless acceptance: Gen2's global archive is invalid/empty.
Gen3 preparation is separate and has no result inferred here.


2026-10-29 rootless67 generation3 positive application continuation:

All three Chromium/Firefox/WebKit rows in `484da9b4…` pass with normal closure:
220-match populated catalog/Library, actual model-001 archived README source,
supported rootless HostStatus (configuration true/other five false),25 private
edit controls, tags-only draft validation/discard and disabled Maintenance.
Exactly one `/api/v1/config/validate` POST per engine and zero page errors occur;
no Apply or job is run. Raw65904B/SHA `b3c17bf76db44892b31b7e387f3ebd6f666299af332b79ddeb39fdb47d4a03d1`
is preserved in task020/the ledger. Original `24ed55fb…` stays collector-false
for its wrong table label, with0POSTs; it is not an app failure.

Twelve axe4.14.0 whole-document scans have zero serious/critical violations,
but retain moderate preview-banner region violations and serious contrast
incompletes: all checks report nonBmp decorative glyphs (55nodes/engine).
No full accessibility/contrast or reader claim follows. Readonly writer-health
still reports archive unusable; successful catalog reads do not make it initialized.

The independent de787 fixture uses readonly native archive binds and derivative
imagedc8800d7 with stock67 modules/UI/API+worker argv, changing only the console
local-mount metadata hook. This is LOCAL_NFS_METADATA_SIMULATION, not NAS proof,
old-global reconciliation or a policy weakening. Original global pending/config/
stores remain under the binds; setup failures and their corrected new0600
instance locks/existing SHM label provisioning remain recorded. Precleanup
`7bc8046a…` normally closes roles/cgroups, removes aliases and restores the native
domain-lock label (ctime transition retained); normal return `e1e353d7…` selects66
and restores original guards. No acceptance-row status changes from this addition.

AUTH-10 now completes on actual case `94221fa0d73d4adfb5f5ed61bebda6cf`,
raw exit0/normal closure in all three browsers. Each genuine original Basic key
starts unobserved with IDnull and25 private configuration controls. The actual
same66 API/Caddy restart changes instance/authority epoch; explicit Reconnect
clears private controls, preserves the exact original authority/key/IDnull and
makes no automatic lookup or POST. Explicit Observe makes one original lookup
and recovers its correct verified terminal catalog warning result. Zero POSTs/page
errors occur and no key is printed or replayed. Source is
`.scratch/web-020-direct-app-unresolved-reconnect-v2.mjs`; original stdout is
1884B/SHA256 `74be2ec9ea814607b78e6dc12b0dae473c4ad09b512458dfbc4c1bf1311efc72`.
The separate restart43df0/socket MainPID error and f518/immediate readiness
refusal remain failed; readiness/marker080a5ccd succeeds without another restart.
Original configuration Apply uncertainty is unchanged.

UX-01 also completes from the mapped real native66 Basic/read/catalog-write/
upgrade/recovery cases and rootless67 generation3 reads/validation/denials,
plus historical all3 native `/management` bootstrap/deep-refresh/history/prefix
checks. Original prefix generation412ce26a has RESULT SHA `f3b97ea9…`/244192B,
browser report `1d46fd17…`/224940B and local common21 metrics/postverify
`73321b0c…`/`283e5818…`; Source13 identities are retained, not called5d1.
Existing Basic unit/socket integration nodes are mapped, not invented. The
rootless local-mount simulation and readonly health limitations remain explicit.
At that checkpoint AUTH-10, CATALOG-09, UX-01 and UX-04 were complete; subsequent UX-03 completion is recorded below.
No reader/responsive outcome, configuration Apply success or old failed race is
inferred. WEB-020 remains in_progress/uncommitted.

UX-03 now completes with actual responsive case `df3610c0f3de4552874fd422f7da2791`,
raw exit0/normal closure in all three browsers, source
`.scratch/web-020-direct-app-responsive-motion-fonts-v2.mjs`. At both1440 and390,
loaded Library/model001, README source, four workspaces/mobile menu and25 private
Administration controls remain reachable. Real Tab/ShiftTab focus is visible
(3px outline), in bounds, without document overflow. Reduced-motion matches true,
measured transitions/animations are0 and actual font resources/requests/document
font faces/external fonts are0; every row records0POSTs/page errors. Stdout is
20118B/SHA256 `438d830aa1c41cb307322572b2ef379aa3bb490977f56868c4cd7e9d51432701`.
Existing seven-surface native200% Chromium/WebKit and separate Firefox keyboard
observations plus mapped component/API evidence complete the row. No Firefox
pointer or universal accessibility conformance is inferred.

Original responsive `4f9973af…` remains collector-false: Chromium1440 passes, then
390 calls isVisible before asynchronous mounting; v2 awaits the same control within
the unchanged30s action limit. Its2887B/SHA `5320817031b897ea383e9f884cc421a733cd43c505b630ad9220a6fb87499de5`
is preserved; no application defect or erased failure is claimed. AUTH-10,
CATALOG-09 and UX-01/03/04 are complete; UX-02 genuine reader smoke is the only
remaining owned acceptance row. WEB-020 remains in_progress/uncommitted.

The actual seven-surface Orca run `meyymo95` records genuine DOM/speech/PCM
for its named controls (`f03688a1…`,28544B), without claiming every warning
paragraph must speak automatically. A separate natural status check `s248grsi`
finds a real app bug: invalid handle import displays the error but does not
announce it while Save retains focus (`8a55fd66…`,4773B;0POSTs/page errors).
Outer owned closure is normal; original worker wait flags remain separate.
The minimal error-alert/success-polite fix and human clarification are ready with
nine focused components/type/format passing. Prior5d1 gate2 remains historical;
the changed source needs its full gate/new68 installed-reader recheck. UX-02
stays open; the other five owned rows remain complete.

UX-02 now completes from prior actual seven-surface `meyymo95` plus the
Native68 specific error-announcement pass `dum9rf2m`: the browser verifies68/
manifestac39/wire320c, and genuine Orca speaks the full rejected-handle failure
including **No operation was submitted**, with Save focus retained,0POSTs/page
errors and790854 PCM bytes (284623nonzero samples/peak30308). Original report
is6060B/SHA `adf35cb38477961326af168e0925f1983852d2431dd65de9cf4321ca68a6be68`.
Outer Root93690 closes normally in37.526s (parent0/timeoutfalse/allownedclosed,
SHA `d80b9a8c…`); original worker reviewedfalse/readerreapedfalse stay unchanged.
The ledger maps existing component/API checks and actual reader/keyboard/axe
scopes without claiming human listening or full contrast/conformance.

All six owned rows are complete, but WEB-020 remains in_progress/uncommitted:
required changed-source full gate2 (Root86932) is still running. Prior5d1 green
results are historical. Native68 build/stage/switch/HTTP pass at canonical
`610de3ca…`, UI-build274933cb/manifestac39b9d1/wire320c; the post-build ADR
label/link correction changes no app/runtime bytes. Its complete JS inventory is
253846 gzip bytes (entry204530/lazy49316) below358400, with no new p95 claim.
Review of INV-021/ADR145 finds a local message-severity correction only: focus,
original handles/authority, no-replay HTTP, wire/storage formats and dependencies
are unchanged. No new architecture/invariant is introduced. Human docs stay
frozen. Do not complete the task, commit or select WEB-021 before gate2 passes.

Changed-source gate2 exits1 only for the strict ledger metadata check:9038 tests
pass/52 are deselected in1114.68s. Two unknown-exit reader observations are now
retained verbatim in task020 history instead of known-exit executions; no exit is
invented. The existing entire `tests/unit/test_web_plan.py` then passes9tests in
0.41s. App/source/human docs and all six completed row statuses are unchanged.
The mandatory full gate3 rerun remains pending; WEB-020 is not complete/committed.

## WEB-020 completion and pending WEB-021 handoff (2026-10-29)

WEB-020 completed 2026-10-29, **this commit**:
`WEB-020: harden browser recovery, accessibility and bounded reads`.
All six owned acceptance rows are complete. Final required gate3 exits0 on
canonical3f97731e/1528:9039 backend/52 opt-in deselections/1067.78s backend,
3702 web unit/4029 combined frontend,95% line/90.02% branch coverage, Cockpit,
wheel/build/browser smoke and real HTTP/API React integration all pass.
Original stdout359596b0…/124539B and stderr4dcb9afe…/9402B are retained under
`/var/tmp/web-020-validation-nvj5zeg7/direct-application-status-fix-gate3.*`.
Native68 actual reader/error/PCM and prior all3 native/rootless/keyboard/zoom/
responsive/write/recovery scopes are mapped without relabelling Source9 p95,
unknown worker exits, failed originals or local storage simulation. Native68
build610 and final3f977 differ only in ADR145's removed forbidden label/link;
app/runtime/UI bytes are identical. INV-018/021 and ADR145/157 with AD12/ADR113
are aligned; the error-alert fix adds no authority, wire, dependency or execution
boundary. Original interrupted Apply/lost-key uncertainty remains unreplayed.
Next is **WEB-021 pending/handoff only**, not started. Production/NAS deployment,
merge/push/tag and Cockpit retirement remain outside this completed package.

## WEB-021 completion and continued installed acceptance (2026-10-29)

WEB-021 completes in this commit with reproducible clean source245f2eaa artifacts,
explicit native/rootless UI enablement, copied installer-free native runtime and
fixed metadata-only rootless archive-lock policy. The task and four completed
ledger rows retain exact artifact hashes, three-browser native/rootless packaging
smoke, actual role/secret isolation, atomic configuration visibility, historical
dirty-document upgrade and all failed/unknown observations. Final gate6 exits0:
9318 backend,3702 web unit/4029 combined frontend,95% lines/90.02% branches,
required Cockpit/browser/HTTP checks and16 wheel smoke tests. All1005 frozen
product files stay unchanged. This is isolated packaging acceptance; no full
positive fourteen-tool MCP, complete workflow, rollback, NAS or production claim.
WEB-022 is next under the existing continuation authorization. The plan stays
active; no merge/push/tag or live Cockpit removal is authorized.

## Installed-gate dependency sequencing correction (2026-10-29, WEB-022)

The original task022 command invoked the final95-case gate, including the
WEB-025 Cockpit-absence and WEB-026 handoff cases before their prerequisites.
Implement the existing early-versus-final rule precisely: the same installed
runner requires all85 cases owned throughWEB022 in all18 profile/prefix/browser
cells, later packages add their owned cases, and the final WEB026 command remains
all95×18. A through-task invocation reports later cases pending and cannot use
the final flag. No case is waived, no required omission passes and no Cockpit
retirement moves ahead of its dependency. The task/testing contracts carry the
commands; this clarification implements ADR143 without a new runtime authority
or fixture framework.

2026-10-31 continuation: the focused native Chromium/root configuration read
passes0 (87aad721…), HTTP200/exact draft base/disabled actions and normal closure;
old native-six aggregate remains failed. Check5 docs/plan/shadow pass0 on their
prior record snapshot. Public differential inputs generate/check0 (cf86b621…/
7a65c192…): three tiny revisions total29821B, no archive records preseeded. The
owned Hub successor setup passes0 (bc8c26fd…), normal old listener exit0 and
unchanged app/archive/config/credentials/CA; extra backing masks retain confinement.
The first differential UI launcher then refuses at host capacity preflight,
before intent/SSH/browser/POST: Home84574208B is below268435456B. No Apply/Sync
occurs; refusal10f234d0… is retained on rootFS. Safe completed-build preservation
continues; no reserve reduction, guest/image action or acceptance claim follows.

2026-10-30 WEB-022 progress: native75 C2/D1/E1 counters, READ3 and same-original
NEW/E2 verification pass; old full reports/last_full remain. Rootless75 six-cell
read UI and a separate Chromium/root18-refresh/4CLI/28MCP overlap pass, with seed
reports not new worker jobs. Same-VM903118a5 corpus activation A2/B passes after
A1's four drains/timer-property failure, without repeat stops or authority/server/
credential writes. Pilot1 passes three steps, then fails step4's45s aggregate
budget after27 queries; seven steps remain unrun, all preservation holds and no
new mapped-row pass is credited. Pilot2 also fails step4's10s wait after23 states;
focused AND-zero/Clear29 diagnostic0 establishes no cause or full-step acceptance.
Pilot3 fails after nine passes on a premature tenth loading check; two driver
readiness waits precede actual pilot4's all-eleven transport/browser0 in one
Chromium/root cell. QA1 passes three combined technical-filter checks and keyboard/
filter pagination, then its retained-tab focus observation fails before async
restoration; remaining checks unrun. QA2 also remains1: six checks pass including
retained keyboard/README/390px, step7 real200% zoom unobserved, later checks unrun;
closed/zero effects/other preservation hold. Root visually reviews390px images,
explicit metadata loading state retained. Rootless corpus A1 remains1 after stock
bridge0/CID-observation race; exact-checkpoint A2/B2 now pass0 without stop replay,
with byte-identical reviewed authority/config-only grants/original1790/RO/old
state retained and zero authority/server/credential writes. Rich rootless pilot1
remains1 after ten passes/last exact-base wait with two GETs pending; closed/zero
effects/errors/four other proofs hold. Fresh rootless6v2/3855 now passes0/all six
cells/66 fresh steps, all closures/five proofs/zero effects/errors;120s pilot/
10s DOM/15s navigation scope gives no mapped/full85×18 stamp. Separate Settings200%
zoom0 proves Files layout/restores
100%/closes/preserves state; README is still Loading in the reviewed cropped image,
so zoom1 alone leaves loaded README unproven. Separate zoom2/3855 actual0 now
proves exact loaded README/table/code and Files at100/200%, correct1440×913
viewport images/restored100%/closed/all five proofs/no effects. Native07fe completes1:
all6 first ten Library/Files/README pass, configuration5/6 with Chromium/root's
original10s base-wait false; all close/zero effects/errors/four other root proofs
true, aggregate flag false. Focused native Chromium/root configuration follow-up
passes0 for that cell only; no old aggregate or full-case pass is relabelled.
QA2 stays false, no copied full-case credit.
Three completed release trees preserve to root/old-path links; Home258334720→
378793984B without guest changes. Exact green gate11 TMPDIR retirement0 restores
root1349586944→2272735232B, preserving logs/results/freeze/inventory. Prior check4 docs/plan/shadow0
predates this update. Gate10 types1 stays;
gate11 inner/outer0 covers its prior1006-file source,9580 backend/4049 frontend/
581 Cockpit/16 wheel/two browser checks. Current driver3855cebb/freeze4 adds a
test35s HTTP-response wait before existing10s DOM base; fetch30s/queue caveat and
strict45s unchanged. The current full gate is required, source13's other1002
unchanged. Task022 retains scope/
failures;16 mappings/34 steps and full85×18 remain open, CARD-10/12 partial,
23–26 pending and old unknown outcomes untouched.

2026-10-31 WEB-022 progress: eight static outputs preserve0 on same-host root/old-
path links, Home76840960→516915200B, without guest changes. Capacity and retained-
cache-symlink observation failures remain. Installed pure plan0 observes903a88
58.93h/24h/actionable1/blocked0/problems0 without jobs/writes. Present2 remains1:
two UI steps pass, original Sizing succeeds and original Apply confirms/pendingfalse,
adding only one enabled7-SHA model to28 unchanged disabled entries. Late Edit
lookup fails on25-row pagination; no Sync/Sync admission occurs. Old seven sets/
unknowns/private originals/roles1722 preserve, all browser closures/zero errors.
Present3 remains1 on dynamic request_id comparison; present4 remains1 after
both SAME-original UI observations/host confirmation pass, on nested entry-tags
locator scope. Both zero-POST/operations/closed/preserved, no Sync. Present5 now
remains parent/browser1 after five passed steps and one FIRST genuine selected
Sync:7-SHA/e6ad4b8a/gen1/8files16926B, reused0, HFWRN011. Known a88 normal TX-07
quarantine/failedHFTXN003 plus one RecoveryReport and three committed journals are
actual. Present5 browser/parent failures stay; qualification2 effects/preservation0
(2539ceed…) allows only the exact191B HF marker beyond reviewed changes. Present6
remains1 after four read steps/four AND queries on CDP response-body timing.
Fresh present7 passes0/five fresh steps/nine AND queries/zero POSTs or operations/
all closures/six proofs in one Chromium/root cell, no replay/mapped/full85×18 stamp.
Native29/30/8 versus independent rootless28/29/7 stays explicit. Static artifacts
remain same-host root `/var/tmp` with home aliases, after7 free root1815605248B/
home470507520B, historical preservation figures untouched. Revision8 attempts1/2
remain1 before POST/operations:10s draft-base wait, then35s completed-response
observer. Attempt2's actual DOM/root-viewed image shows loaded base38cc00c9…/
29 clean rows/no alerts; HTTP200→ERR_ABORTED is consistent with the UI client's
unconditional finally abort after strict decode, not proof of failed UI reading
or completed transfer. Both close/preserve; no app defect is established.
Actual3 browser passes all six steps/closed/zero errors: original Sizing/Apply/
selected Sync publishes8/5ef704ee…/gen2,6609B published/382B downloaded/6227B
reused/HFWRN011; retained7 README/source and current8 withheld/no-fallback UI pass.
Its original parent1/cache-lock expectation and qualification1/2 failures stay.
Independent read-only qualification3 passes0/9ca547c1…/all seven boolean proofs:
only14 shared-payload link/ctime rows plus seven exact empty lock timestamps and
the exact8-origin tree inventory are allowed; all other state stays exact.
Native reaches29/30/9/current8, with root-viewed README images retaining other-
panel Loading limits. Actual9 now passes transport/browser0/all six UI STEPS in
ONE Chromium/root cell/8a34e9c1…: original Sizing/Apply/selected Sync publishes
ed17f321…/gen3,6286B published/59B downloaded/6227B reused/HFWRN011, no Recovery.
Unsafe9 withheld, unsupported8/present7 retained, explicit current9 no-fallback,
all closures/six boolean proofs pass; only21 payload link/ctime rows/seven exact
cache-lock timestamps change. Native now29/30/10, rootless28/29/7 unchanged.
Actual six-cell aggregate1/a44f42d9… retains four Chromium/Firefox cells×six
passed steps; WebKit both aliases pass authority/README assertions but screenshot-
induced CSP console errors fail strict health. All close/preserve/no effects;
aggregate false/final probe unrun. Separate real q→Models75.2ms probe1/21598052…
finds the actual search-reset bug/15 results instead of1. Three-file contract-first
DOM-q/type composition fix passes23/23 component tests plus lint/format after
two fail-before regressions; INV018/021/ADR145 reviewed. Screenshot diagnostic0/
6f6094d6… proves Playwright's transient HEAD `body {}` caused CSP only at capture;
no product CSP change. Fresh strict WebKit follow-up0/818d8c17… passes both aliases/
six steps/nine AND queries each, console0/closures/six root proofs. With the four
earlier Chromium/Firefox cells, native source75 read coverage reaches six cells;
original aggregate remains false. Nine-query aggregates46.14/77.52s use pilot120s,
not strict45s/performance acceptance. Historical pre-fix gate12 stays green;
exact generated temps retire0/3a91b6d7…/179508 inventory/two no-reference proofs/
logs retained. Post-fix gate13 now passes inner/outer0/dca41acd…/0a0c45c8…,
frozen1006 unchanged:9580 backend/4051 frontend/Cockpit/wheel/built-browser/HTTP.
Clean source14/.76 cut0/d4d99f8d… leaves main refs/index/product exact. Native14
build0/b4eaf3ae…/18 reproducible artifacts and postproof620873aa… pass; API76
canonical build0/98aae0b4… and canonical runtime foundation0/e529c2eb…/proof93c873f6…
pass; stores/main/reserves stay exact. Native76 A/B/C0/8228400d… now runs new
helper86976/worker86996/API87017/Caddy87027 on RW903, preserving original1722/
keys/old reports/stores/Hub and all19 bindings/six grants/SELinux receipt.
Original native q6 remains1/71235451…: five cells/ten cases pass, WK-management406ms
typed is timing-unobserved/clear unrun, all health/closures/preservation hold.
Fresh WK-management2 pass0/6f35217a… qualifies both85/84ms cases/strict health/
closures/seven proofs. Installed q fix thus has six-cell coverage from5+1 receipts;
old aggregate/source75 failure stay false, no merged matrix stamp. Rootless76
normal app start0/bda51883… and fresh q/type six-cell0/19d7e7c3… now prove12 cases
in97.165s, strict health/closures/six preservation proofs/zero effects; its28/29/7
corpus remains separate from native29/30/10. Native first schedule530db125… stays
failed after one accepted replacement: ec674 interrupted/no result, foreign3f
history rejected before protected work. GET observer830efb44… remains aggregate1
for expected409 console; scope184ac01a… qualifies its actual original-key UI reads/
unknown-pendingfalse guidance/closures/preservation, not reconciliation. Fresh
same-VM control prepare0/eee774bc… plus review3627a890… retain old API/history/
backups/server/903/reports/keys/locks and identical65e929fe… authority. First restart
7ec644f8… remains failed after four starts; read-only qualification2 passes0/
a72d807a… in5.279s using the SAME roles/new store and all preservation joins,
zero new starts. Scoped schedule summary0/cd798799… now joins five full sessions
and Firefox-management's original2+new PauseReset2,24 distinct confirmed originals,
all six final default/inactive. Raw9dae3804… stays false; GET diagnostic0/35bcc3ad…
shows current enabled controls/both confirmed originals without proving the old
page's cause; new-only PauseReset0/4dbc97db… reloads all four. Both unrun WebKit
cells pass0/abd3239d…/89679218…. This gives no full HOST/matrix stamp. Rootless76
admin1/8f027823… remains1/919.435s (locator404 console/read deadlines), admin2/
5bdb14be… remains1/301.809s (abort/deadlines/expected400 versus actual422). All
close/preserve, zero operations/effects; one pure validation422 in admin2. Ordinary
workload3 passes0/740d46ba… in580.334s: six cells/six callbacks each,12 pure UI
validations, zero operations, all seven preservation flags/closures, maximum32.101s.
35/36 UI bodies are captured; one Chromium-management body is unavailable, so no
complete wire-transfer claim.
Focused rootless tag19 passes0/231f8cc6… in479.852s: six cells/19 fresh callbacks
each,114 passes, maximum10.165s; each joins16 queries and three client refusals.
Zero POSTs/operations, all seven preservation flags/closures and strict console/
CSP checks pass. Split tag-provenance/bounds scope adds no full-case/matrix stamp
or completed-transfer claim. Earlier aggregate failures stay false.
The tracked test driver now replaces the overlong tag aggregate with19 named
45s callbacks; CATALOG-02 requires all19, with52 baseline assertion IDs and16
case mappings. Exact query/hash/settled-DOM and client-side no-request refusals
remain; no receipt import or timeout relaxation is added. Driver8cba6cd6…/
runner70b3a8fb… and the existing unit fixture's ID list are the only new test
changes. Existing Node metadata18 and Python functional-runner545 checks pass0;
the initial27 stale-fixture-ID failures stay retained. Ruff/ESLint/format/syntax
pass; no new full gate covers this test-only integration. Installed tools3855
and source76 runtime/UI are unchanged, ordinary/negative integration is pending.
Rootless configuration-negatives1 remains transport/browser1/1320d5a6… in699.559s:
five cells each pass25 callbacks/24 local refusals; WebKit-root times out on its
first10s Administration navigation click before config GET. Zero POSTs/operations,
strict health/all closures and all other preservation flags pass. Focused fresh
WebKit-root2 is running, not yet qualified; any later coverage must join original
five plus its actual result, retaining the failed aggregate. No server422 claim
comes from these local form refusals.
Native maintenance4 remains transport/browser1/fa102fc6… in1084.098s: seven UI
steps pass, publishing only the new903 copy's B/C/D pairs, each2files/4751B,
with four successful Sizings and three confirmed Applys. Apply-E original
7d6d6295954ab6087f8f1ec8bc344a2b fails20/HFAPI022 on protected policy inspection
timeout before helper handoff; it is not resubmitted. Read-only0d8be27c…/
cb8b2777… prove empty events, configuration-D/retention5 and no pending host or
configuration intent/application audit for that failed original. The UI correctly
fails closed under ADR154; no product defect is established. All browsers close,
with zero unexpected page/console/5xx errors, and the old ten publications,
worker reports, private originals, roles/keys/1722/Hub remain protected. E Sync,
retention reduction, prune and purge are unrun. Fresh-context M5 preparation is
for a distinct reviewed remaining workflow, not replay or a false M4 pass.
TARs4 preservation passes0/12807934… at same-host ROOT
`/var/tmp/web022-retained-public-source-tars4`: four completed public source6–9
TARs retain bytes/semantic metadata/old HOME aliases and88 producer/artifact
hashes. HOME276353024→346816512B/net70463488B; ROOT1975537664→1904615424B.
FIEMAP70660096 exclusive bytes remains separate from actual net free movement.
Source10–13 capture-only originals stay untouched; no VM/image/checkout/venv/
private-store cleanup, off-machine backup or lowered reserve occurs. WEB-022
and full85×18 remain open; check18 is historical to these new records.

Native maintenance1 stays1/6e15398a…/41.963s before POST on the outdated clean-
paragraph locator. Numbered2's pre-intent capacity refusal30089af6… remains;
after preservation its actual run fails1/3bedfaff…/41.378s at baseline4!==30.
Numbered3 also fails1/2c45b00c…/95.402s at baseline404!==200 with one console404.
Both send zero POSTs/operations/publications and close all contexts; old payloads/
stores/config/roles preserve. Observer/backend Stop remains unsealed pending
genuine maintenance success. No replay or app-cause claim follows. Driver16 mappings/52 baseline IDs,
full85×18 and CARD gaps remain open; check17 historical.
Gate13 TMP retirement0/1b7149ee… preserves logs/source/inventory. Root dependency
retirements retain all sources/artifacts/venvs; later two-cache0/56fd4000… gains
648273920B/2069 hashes safe. One HOME completed source21 cache retires0/c93f7fda…,
Home277278720→572784640B net/6602 protected records. Exclusive FIEMAP284188672B/
shared0 is qualified separately; both preparations remain. No VM/image/service
cleanup or lowered reserve. Old .venv donor refuses on3.4MB exclusive/86.2MB
shared, no effects. Three public source TARs preserve3/0/4d53b464… onto same-host
ROOT `/var/tmp/web022-retained-public-source-tars1`; three original HOME-path
links/all63 artifact hashes stay. HOME278671360→331792384B/net53.12MB, distinct
from53.20MB exclusive FIEMAP; no off-machine backup/checkout/venv/guest moves.
Four more completed public TARs22–25 preserve4/0/c99ad8a6… on this same host's
root `/var/tmp/web022-retained-public-source-tars2`:84 producer/artifact hashes,
original HOME aliases and bytes/semantic metadata retained. HOME270708736→
341733376B/net71024640B; ROOT2236841984→2165592064B. No VM/image/checkout/venv/
store/unknown-evidence moves or off-machine backup. Existing reserves stay fixed.
Four public fixture-projection TARs19/21/22/23 then preserve4/0/5fc485f6… at
same-host ROOT `/var/tmp/web022-retained-public-source-tars3`, with all100 producer/
artifact hashes, original HOME aliases, bytes and semantic metadata intact.
HOME257499136→328552448B/net71053312B; ROOT2153357312→2082168832B. FIEMAP70975488
exclusive bytes is separate from shared-filesystem free-space movement. No guest,
VM/image, checkout/.venv, private-state moves or off-machine backup.
Remaining HOST branches/full85×18 remain pending.
Source75 worker UI0/a65fcdaf… passes five steps/one Chromium-root: genuine clean
full4/10/23/41279B and revision9 scope1/1/8/6286B, both original/reload/report joins,
18 Library refreshes/all nine preservation proofs/closures/errors0. Separate
clients0/ed69d827… pass four CLI+28 MCP reads/both prefixes during SAMEbrowser
refresh2→5; both report tools join the new full/revision jobs, no seeded-job credit.
Old reports/payloads/new lastFull remain, original1722/roles/Hub counter exact.
That source75 concurrency checkpoint gives no installed-qfix/full85×18/client-matrix/
CARD acceptance. Old failures/unknowns remain protected, cheap checks historical.

2026-10-31 [checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-10-31-gate15-and-installed-doctor77): historical Gate15 passes all1541 frozen files;
Source15/native77 Doctor, API77 inputs and rootless77 upgrade/SDK pass. UI2's five
passing cells plus focused UI4's seven Chromium/root callbacks give six scoped
observations on reused browser storage, not fresh lifecycle/matrix acceptance.
UI1/2/3 stay false; helper-refusal cause remains unestablished without relaxation.
Existing573 Python/18 Node checks pass. CONFIG03 pilot1 passes28 read/local
refusals, then fails blank-session navigation before any Apply/operation; its
implicit favicon404 is separately under review. Gate16, complete CONFIG03,
fresh canonical profiles and85×18 acceptance remain pending. Pilot2 also stops
before Apply after28 passing callbacks; focused pilot3 finds config GET503 from
peer-observer deadline expiry, with no POST/operation or configuration change.
Single bound-read implementation passes568 focused regressions and canonical
wire regeneration; deadlines/public DTOs remain intact. Gate16 stops at ADR143
documentation alignment before tests/build with all1542 files unchanged; the
record-placement wording is corrected. Gate17 passes9645 backend/three wheel
profiles/581 Cockpit, then fails test-driver cleanup lint. The minimal correction
passes full web lint without product-runtime changes. Full Gate18 and new
Source16/version78 installed SPA proof are pending; no extra test layer is added.

Historical checkpoint before C qualification and repair: [task details](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-10-31-maintenance-authentication-and-source-validation)
separate M10 browser success from parent failure/qualification0, partial Origin
refusals and pending observer C qualification. Role joins remain unmapped;
source-only23 drift checks add no installed credit. WEB-02285×18 remains open;
WEB-023–026 stay pending.

2026-10-31 [latest checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-10-31-gate18-and-source16version78): Gate18 full pass (0), Source16/version78 native 19 artifacts,
API78 build/foundation/export, input16 pack/render and native A/B/C pass (0).
Rootless78 and the existing 41-callback SPA flow remain pending; WEB-022's 85×18 matrix
and WEB-023–026 are incomplete. After WEB-022 and before WEB-023, revise all
remaining task/plan/testing guidance for bounded product-focused testing and
explicit `gpt-6.1-sol` efforts high/medium/high/medium, task-specific rationale
and escalation criteria. This records the user directive; later-plan edits wait.

2026-10-31 [UI continuation](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-10-31-rootless78-configuration-observations): rootless78 upgrade passes0 and configuration GETs return200/no503.
Pilots1/2 pass30 callbacks each; pilot3 passes six including one confirmed tag-only
Apply, independently qualified60a2fdce. All three aggregates remain false; no Apply
replay, stale409/13-callback acceptance or normal85×18 credit. The existing normal
manifest is Source13, not78; WEB-022 stays open and WEB-023–026 pending. Two test-only
driver corrections postdate Gate18. User model data/HOME alias remain preserved.

2026-10-31 [tag/SDK checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-10-31-rootless78-tag-propagation-and-sdk): Tag2 `9af356bc` passes six cells/36 read callbacks0,
zero POSTs/operations, strict health/closures/seven proofs; SDK78 `0ee0aacf` passes0
without selected-role changes. Tag1 remains false. Normal85×18 is unproved: the
stock lifecycle branch is missing and only18 case IDs are mapped. Scope-decision
proposal is unapproved; no harness implementation has started. WEB-022 remains
in_progress/WEB-023–026 pending; the future-plan patch remains unapplied.

2026-11-01 [CLI/MCP and original-handle checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-climcp-reads-and-original-handle-observation): rootless `c6bf5fb4` and native `423e1a85` pass4CLI/28MCP
reads each; synthetic rootless versus genuine Source75 native reports stay distinct,
with no new-job/concurrency claim. Import/reload `6812c64e` passes eight UI phases0,
zero POSTs and original Apply confirmed twice. Full13/old-B stale409/AUTH-05/85×18
remain open; WEB-022 in_progress, scope proposal unapproved, future patch unapplied.

2026-11-01 direct stale-B API probe `a03d6af5` passes0/409 HFAPI007 without
admission/configuration change; this adds no old-B UI stale-submit/full13 credit.

2026-11-01 [management/gate checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-management-conflict-and-interrupted-gate): Management1 raw1/40of41 includes actual UI409 and
qualified A-Apply74c9794a (43c10d4c); never replay it or root Apply1dc6b7fd. Final
unsaved-draft navigation is corrected in the driver; read-only recovery is pending.
Gate19 ends2 after ordinary pytest interruption/1953 passed/1542 unchanged; Gate20
is prepared, not started. Firefox multipart remains unqualified AUTH-05; no form
reruns. Human summary is INCOMPLETE;85×18/full13/scope decision remain open and the
future23–26 patch unapplied.

2026-11-01 [separate read-only follow-up](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-separate-read-only-navigation-and-b-recovery) `d008066c` passes0/23.266s: explicit discard navigation,
exact saved-B preview/stale records/results across reload, zero POSTs/state changes.
Original40/41 remains false; no same-run all41/full13/matrix pass. AUTH-05 stays
unqualified after empty same-attempt logs/journal; Gate20 prepared/not started.

2026-11-01 [Gate20/product-gap checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-gate20-passes-product-acceptance-remains-open): innerfa2b6d86/outer2596cc63 pass0/1723s,
9645 backend/4051 frontend/581 Cockpit/16 wheel/three locked profiles/two built-browser+
real HTTP/all1543 unchanged. Successful TMP retirement48f3300c retains inventory/13
outputs and gains953991168 B; Gate19/VMs/originals/user cache untouched. CONFIG-12's
model+dataset add/remove20-callback workflow is prepared, unexecuted; existing28+13
callbacks omit it. Full13/AUTH-05/85×18 remain open; stock-branch attempt scratch-only,
no weakening. WEB-022 in_progress, optional scope decision pending/requirements
unchanged;23–26 pending/future effort patch unapplied.

2026-11-01 [CONFIG-12 add checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-config-12-add-succeeds-workflow-remains-incomplete): browser4 b19649b3 raw1/first8 pass before wrong-fingerprint
comparison, but real model+dataset Add Applyc00f41e4 succeeds/host confirmed/exact30
disabled; seven publications and three preservation claims pass. Never replay it
or prior1dc/74c. Original recovery/removal are prepared, NOT executed; CONFIG-12/
full20/matrix remain incomplete. Gate20/retirement unchanged; optional scope
unanswered, requirements unchanged/WEB-022 in_progress/23–26 pending. Future13-doc
patch2 b189fe19 is prepared/unapplied with high/medium/high/medium efforts.

2026-11-01 [scoped add/remove continuation](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-scoped-config-12-addremove-continuation-passes):335c8e20 passes0/12callbacks/152.825s, original Add
recovery and one new removal21f81fd4 host confirmed. Final29 all disabled; seven
publications/old evidence/roles/guard unchanged, removed dataset unmanaged/Tags not
observed. Never repeat Addc00/removal21f/prior1dc/74c. Older aggregates remain failed;
scoped add/remove passes do not stamp full20/whole CONFIG-12/matrix. WEB-022
in_progress/requirements unchanged/futurepatch2 unapplied/023–026 pending.

2026-11-01 [native overlap checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-native-uiclient-overlap-qualifies):73611ddb/qualified052f7b3a pass0,9 actual Library intents plus
4CLI/28MCP, all32 client intervals inside native Chromium/root UI window with40 UI
API requests during clients. Strict health/closures/preservation pass; old0.2.75
reports read exactly, no new worker/rootless concurrency/matrix claim. Overlap1
remains failed before clients. CONFIG-12/Gate20/status/futurepatch2 unchanged.

2026-11-01 [native78 worker/report checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-genuine-native78-revision-worker-and-mcp-report): UI once-only5a4d8703 succeeds clean/1repo/1rev/
8objects6286B, browser5of5; raw1779478a outer1 retains lock-timestamp collector failure,
qualification04dd2f88 passes0/preservation joined.19 aborted requests retained, not
zero. Two MCP reads39b8a777 join exact new0.2.78 report separately; prior overlap
still uses old0.2.75 reports/no new-worker concurrency. Never repeat the job.
Gate20/CONFIG-12/status/futurepatch2 unchanged; overall INCOMPLETE.

2026-11-01 [current README/Files checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-current-readmefiles-pass-in-native-and-rootless): nativee60ce316/rootless8db31b1f each pass six
cells/12 checks for exact current TWO-file publications; strict health/closures/
preservation/no effects, abort diagnostics retained. Native1 failed Library lookup
stays failed/cause unqualified; direct-link success supplies no full CARD-12/
CATALOG-08/matrix credit. One bounded query probe prepared; Gate20/worker/MCP/
CONFIG-12/status/futurepatch2 unchanged.

2026-11-01 [bounded query/card-metadata checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-query-loss-not-reproduced-in-one-bounded-attempt):3792865a passes0/17.513s/two callbacks, exactly
one attempt/q+URL+one row retained. Loss not reproduced once; older failure stays
unqualified/no fix or resolution/no diagnostic loop. Both retained-card metadata
reads0/pairs match; fail-closed/deep/link actual UI checks are prepared, unexecuted,
using existing fixtures. Gate20/positive scopes/status/futurepatch2 unchanged.

2026-11-01 [retained-card UI checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-retained-readme-card-state-ui-passes): nativef540f7b6/rootlessfdfcd805 each pass0/six cells/24callbacks,
unsafe/unsupported failclosed, deep refusal/source and table/code/placeholder/link
protections. Strict health/closures/preservation/no effects; cancellation diagnostics
retained, no zero-failure claim. Existing browser image reused/stopped7cfc165d;
selected-state scope only, no fullCARD12/CATALOG08/family/matrix. Query failure
unqualified/one successful probe/no loop; Gate20/worker/MCP/config/status/patch2 unchanged.

2026-11-01 [dataset checkpoint](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-dataset-detail-scope-passes-with-retained-continuation): nativefcf279a3 passes six cells/18callbacks; rootless033f2297 passes
remaining four cells/12callbacks plus retained Chromium2cells from failed10e0d8b0,
without replaying Chromium. Exact dataset pair/twofiles319B/attributed fields,
Files404/nonHTML/reload-history pass; supplemental Firefox401event retained while
actual fetch404 required. Strict health/preservation/closures/no effects, cancellations
retained. No fullCATALOG07/08/family/matrix claim; all prior positives/status/patch2 unchanged.

2026-11-01 [rootless host visibility](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-rootless-administration-denial-visibility-passes):3a2bd481 passes0/121.763s/six cells/12callbacks,
actual guarded reasons and disabled/absent controls/read-only timer. GET-only/
health/closures/five preservation proofs pass, cancellations retained. Denial
visibility only, no backend mutating refusal/fullHOST08/family/matrix claim.
All test executors terminal; prior outcomes/status/futurepatch2 unchanged.

2026-11-01 [required acceptance-basis blocker](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-blocked-on-required-acceptance-basis-decision): WEB-022 **blocked** after the third consecutive
impasse; final prepared outcome **blocking decision required; goal blocked**.
Plan remains active/not paused,023–026 pending. Unblock by adopting the prepared
product/safety-preserving acceptance proposal OR explicitly authorizing necessary
runner implementation retaining original85×18/95×18. No default waiver/subset
substitute/repeated checks/observer loops. All product evidence and futurepatch2
unapplied status remain unchanged; Root verifies goal status after record validation.

2026-11-01 [acceptance adoption](tasks/web-022-installed-functional-acceptance.md#checkpoint-2026-11-01-acceptance-proposal-adopted-task-continues): user “i accept the new proposal”. WEB-022 returns to
in_progress/plan active; prior decision blocker resolved. Product-focused criteria
supersede only governing mandatory normal-runner85×18/95×18, retaining historical
evidence/all95 behaviors+clauses/missing list/failures/IDs. Appropriate unit/integration/
direct installed UI evidence; three engines/native-rootless/root-management remain,
deeper cases once where relevant/full source gate unchanged. Tool status remains
blocked/no resume-method claim; user authorizes continuation. No completion/023
activation/futurepatch2 application follows; effort update still AFTER22/BEFORE23.
