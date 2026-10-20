# Replace Cockpit with a publication-aware hfcache web UI

| Field | Value |
| --- | --- |
| Status | active |
| Created | 2026-10-20 |
| Authorization | Tyler's 2026-10-20 implementation instruction and bundled kickoff authorize activation, scoped source changes and owned local/isolated disposable tests on `feat/web-ui`, one work package per commit. No production deployment, remote publication, merge or tag. |
| Tracker | `docs/agents/plans/current.md` — sole active selector; intentionally not overwritten by extraction |
| Baseline | `6b8fae2e0997403ae5c716a2e92148af0a972af9` — main reviewed October 20, 2026 |
| Branch | `feat/web-ui` |
| Work-package family | WEB, deliberately introduced for this feature after collision check; one task = one work package = one implementation commit |
| References | [Bundle entrypoint](support/web-ui/README.md), [kickoff](support/web-ui/KICKOFF.md), [source review](support/web-ui/source-review.md) |

## Outcome and scope

Deliver a strict-TypeScript React SPA that completely replaces the Cockpit plugin as hfcache's management UI. Use the approved archive-first Library, rich model/dataset detail pages, configuration-backed tags, Operations, Maintenance and Administration. Render a securely captured, publication-pinned README when available, alongside every supported existing source-attributed catalog/inventory/integrity field. Preserve hfcache's unique safety, complete-snapshot, publication, retention, recovery and uncertainty contracts. Borrow the reference downloader's organization, not additional product features.

The UI is served by the existing hfcache API application through the **same existing Caddy instance, TLS endpoint and Unix upstream as REST and MCP**. No second Caddy/frontend server/public listener/Node runtime is introduced. One protected Basic-authenticated human administrator is the initial user; existing REST bearer clients and read-only MCP credentials remain compatible. An internal authentication-provider/principal/permission boundary enables a later identity provider without implementing multi-user/OIDC/repository ACL scope now.

The shipped UI assets belong in the existing API image, whose build and runtime
FROM stages retain the pinned, streamlined UBI 10 micro base. No separate frontend
image is introduced. Preserve the existing CA-data-only donor boundary and omit
frontend build tools from runtime. WEB-021 must verify actual image ancestry,
installed asset hashes and absence of Node/package managers; labels alone do not
prove this requirement. Isolated browser test images are unshipped tooling.

The source result includes necessary missing config/card/host REST capabilities, strict runtime wire validation, immutable release asset packaging for native/rootless profiles, real unit/integration/functional coverage, human-facing guides and migration/rollback procedures, and removal of Cockpit as the newly shipped UI only after parity is proven. Source retirement does not uninstall the live host's Cockpit or erase historical records.

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

Review at minimum INV-001/002/003/005/006/007 and current metadata/operation/supplemental/browser invariants; AD-01/06/12/14/15/16/17/18/21; FS-05–11/15/16/19 and initialization exclusion; relevant CP-01–14; FW-01–04. Confirm actual IDs/wording at execution. Review numbered ADRs 108–125 (services/REST/receipts/client/candidates/MCP), 126–129 (guarded rootless runtime), 133 (tags/discovery), 134–139 (Cockpit repair) and current amendments. Allocate new ADR numbers from the live index, not hard-coded future numbers in this draft. Preserve old reasons/IDs and explicitly amend/supersede changed current requirements.

Particular contract changes need explicit rationale: Basic principal and CSRF, new privileged administration capability/helper, exact config application outcome protocol, new README presentation adjunct and any bounded source hashing, application static serving, separate frontend release artifact/dependencies/test gates, and Cockpit retirement. Never loosen unrelated archive/security invariants to make a browser feature pass.

## Phases

| Phase | Outcome | Work packages |
| --- | --- | --- |
| P0 | Contracts, strict workspace and typed wire boundary | WEB-001–003 |
| P1 | Basic authentication, shared-Caddy serving and guarded configuration backend | WEB-004–008 |
| P2 | Writer-captured README records and exact card API | WEB-009–010 |
| P3 | Library/detail/README/tags/operations/maintenance SPA workflows | WEB-011–017 |
| P4 | Fixed host schedule/observer/journal parity and Administration | WEB-018–019 |
| P5 | Cross-browser hardening, immutable packaging, installed acceptance and rollback | WEB-020–023 |
| P6 | Human documentation acceptance, Cockpit retirement and final handoff | WEB-024–026 |

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
| 25 | [WEB-025 — Retire Cockpit packaging only after proven complete replacement](tasks/web-025-retire-cockpit-plugin.md) | WEB-024 |
| 26 | [WEB-026 — Close the implementation with complete evidence and an operator handoff](tasks/web-026-final-gate-and-handoff.md) | WEB-025 |

## Execution and resumption

1. Review git/current-plan/progress/handoff and reconcile the baseline. Do not force-reset, discard dirty work or overwrite an existing active plan silently. If unrelated work is active, record a legitimate pause/supersession or a blocker based on the new implementation instruction; preserve its history.
2. Activate this draft only on implementation instruction, create/resume `feat/web-ui`, set current selector and mark WEB-001 in progress. New untracked bundle files are committed with the activation work package after validation. Do not commit to main merely because it was checked out.
3. Select the next dependency-complete task. Read its relevant contracts/support specs; update contracts/invariants/ADRs in the same work package as behavior. Implement and run required unit/component, integration, functional and docs gates. Record actual results, not intended commands or a previous source snapshot's pass.
4. Complete task evidence, append progress/Decisions/Operator handoff, update current selector, and commit `<WEB-ID>: <outcome>`. One work package per commit. No automatic push, merge or tag. If work is larger than one package, split before completion rather than hide several commits under one completed ID.
5. On interruption, inspect code/status/evidence before resuming; never rerun a completed mutation or discard unresolved fixture/operation state. A required infrastructure or safety blocker remains explicit. Continue only genuinely ready independent work; do not mark skipped host/browser tests as complete.
6. Close the plan only after final acceptance. Keep all dated/task paths stable, clear current active selection, and give a human-ready handoff that distinguishes implementation/fixture readiness from unperformed production migration.

## Acceptance and validation

The [testing strategy](support/web-ui/testing-strategy.md), [95-scenario acceptance matrix](support/web-ui/acceptance-matrix.md), [interface/parity register](support/web-ui/interface-and-parity.md) and [migration specification](support/web-ui/migration-and-compatibility.md) are mandatory scoped acceptance, not optional suggestions. Machine-readable case and task indexes support execution audits but do not replace individual task evidence.

Completion requires:

- All four workspaces and rich model/dataset pages function without Cockpit, with config-backed tags and securely rendered archived cards. Existing operational and host-parity capabilities have executable tests or correct profile-specific denials; unsupported positive paths are not hidden as 'restricted'.
- The same actual Caddy fixture serves UI, existing REST bearer clients and fourteen read-only MCP tools with verified test TLS. Empty/nonempty prefixes, deep links, missing assets, errors and auth isolation work in Chromium, Firefox and WebKit. No fallback consumes API/MCP paths; no new public/privileged surface is introduced.
- Basic authentication, CSRF, strict types/runtime decoding, bounded reads/operations, exact publication identity, guarded config installs/locks, helper peer policy, untrusted README controls and no-replay uncertainty each have unit, integration and real functional failure coverage.
- Every new feature has human user/operator documentation created with its implementation, tested examples/links, accurate screenshots and useful troubleshooting. Agent docs/ADRs alone do not satisfy this requirement.
- Immutable UI/backend/helper artifacts are tested in actual isolated native/rootless profiles. Existing base/server/MCP installation and old client compatibility survive; durable-format/rollback drills preserve unknown state and unfinished evidence. Source retirement of Cockpit occurs only after these proofs.
- `scripts/check.sh --require-web --with-build --with-web-functional` (introduced by this plan) passes on final source with no required skip, alongside preserved applicable baseline gates. Exact test node IDs, commands/exits, coverage/budgets, artifact hashes, browser/profile and safe evidence locators cover every matrix row.
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
