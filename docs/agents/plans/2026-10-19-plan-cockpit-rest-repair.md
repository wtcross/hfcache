# Restore Cockpit administration through the REST-backed client

| Field | Value |
| --- | --- |
| Status | active |
| Created | 2026-10-19 (America/New_York) |
| Authorization | 2026-10-19 user instruction explicitly authorizes activation and scoped source implementation; local-host development authorization amended below; no NAS/live workload, registry operations, push, merge, or tag. |
| Reviewed repository | `wtcross/hfcache`, `main` |
| Reviewed commit | `dcc2c562b52304541d0cb85d20fc046072038e79` — `CAT-016: complete lifecycle compatibility and final acceptance` |
| Tracker | `docs/agents/plans/current.md` |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Work-package family | `CPR` = Cockpit REST repair; these are work-package IDs, not a separate task-status sequence or replacements for `CP-xx` invariants. |

## Outcome

Restore reliable candidate validation and a truthful, recoverable Cockpit interface
for the REST API already implemented. A Cockpit channel interruption must not be
presented as an unexplained `reconnected` backend failure, discard the underlying
classified error, silently reissue a job, or enable installation without fresh
exact-content evidence.

The review found an existing REST-backed CLI adapter, not an unmigrated local
execution backend. The recommended path remains:

```text
Cockpit page
  -> Cockpit privileged bridge
  -> fixed transient systemd client under the hfcache identity
  -> /usr/local/libexec/hfcache-client
  -> pinned, API-only rootless client with its protected API credential
  -> authenticated REST API over the selected Unix socket
  -> server-owned operation / private verification worker
```

Do not put API credentials in JavaScript, replace this with arbitrary browser HTTP,
route administration through read-only MCP, or introduce a second daemon. Candidate
validation and planning upload content through REST; atomic configuration
installation and schedule administration remain explicit, privileged host work.

## Review result and uncertainty

The source path can surface a Cockpit spawn error's message verbatim, including
`reconnected`, while discarding its structured problem and process information.
The configuration pipeline also mistakes ordinary failure Envelopes for malformed
candidate assessments. These are distinct, concrete error-handling defects.
The deployed channel transition that produced the user's exact message was not
observed: no installed browser session, launcher artifacts, server logs, or live
writer were available to this review. Do not promote a hypothesis about PAM,
Podman, socket permissions, or the daemon into an established root cause.

Additional reviewed gaps include lost operation handles on tab unmount, a
maintenance Apply path that can remain enabled after an uncertain process failure,
non-recovering cached D-Bus clients, misleading masked-service controls, direct
host run-report reads despite existing REST routes, and read-result cards which
hide nonzero Envelopes. See the [audit](support/cockpit-rest-repair/audit.md) for
source evidence, confidence, and the distinction between bugs and deliberate
legacy exceptions.

## Scope and boundaries

In scope: `cockpit/`, narrowly scoped CLI read adapters over existing REST routes,
launcher/profile diagnostics and release packaging where required to repair the
integration, regressions at the real interface boundaries, and corresponding
human contracts, ADRs, invariants, planning evidence, and troubleshooting docs.
Repair the underlying launcher/session cause when reproduced; do not stop at
renaming the message.

Out of scope: new REST cancellation, configuration-installation or scheduling
endpoints; browser token entry; MCP writes; archive schema/publication/retention
redesign; new discovery features; a general-purpose HTTP/shell proxy; changes to
NAS export, mounts, security policy, timers or production services during source
implementation; live synchronization, verification, recovery, pruning, repair,
initialization, deployment, image publication, tagging, pushing or merging.

All existing read-only guards, workload holds and system-unit masks remain in
force. In particular, moving a manual full-job button to an API submission must
not provide a way around the guarded deployment's restrictions. Unknown profile
or permission state disables affected actions. Never redirect masked system units
to same-named user units, stop the API/worker/target to implement Cancel, release
the guard lock, or infer authorization from the absence of a mask.

## Contracts and decisions

Read [planning](../planning.md), [workflow](../workflow.md), and
[workflow invariants](../invariants.md) before activation. Technical review starts
at [the invariant register](../../invariants.md), [Cockpit](../../cockpit.md),
[REST API](../../api.md), [client](../../api-client.md),
[configuration](../../configuration.md), [CLI](../../cli.md),
[security](../../security.md), [containers](../../containers.md), and
[deployment status](../../deployment-status.md).

Preserve `CP-02/03/05/06/07/08/10/11/13/14`, `AD-17`, `FS-02`, `FS-21`–`FS-23`,
`INV-006`, and workflow `INV-011`. Review other affected entries by section, not
by assuming that this list replaces the living register.

Two changes deliberately amend existing contracts rather than silently declaring
those contracts wrong:

1. Amend `CP-04` and related operation tables to distinguish manual full REST jobs
   from separately managed scheduled observers. Use existing `sync` and
   `verify --full` modes, subject to the original deployment gates.
2. Amend `CP-01/09` to retire direct archive report browsing after the existing
   REST `/runs` routes have a tested CLI/UI adapter. Journals remain separately
   labeled, bounded host diagnostics; configuration and scheduling retain their
   legitimate host boundaries.

Review and amend [decision 122](../../adr/decision-122.md) and relevant older
Cockpit decisions through [the ADR index](../../adr/README.md); preserve
[decision 127](../../adr/decision-127.md)'s fixed rootless runtime/credential
boundary. Allocate any new decision number from the repository at implementation
time. This draft reserves no ADR number. Update affected contracts and records
in the same work package as behavior changes. Do not weaken exact-byte confirmation
introduced for tag-only edits, whose operational fingerprint may remain unchanged.

## Bundle navigation

- [START-HERE](support/cockpit-rest-repair/START-HERE.md): extraction and activation.
- [Audit](support/cockpit-rest-repair/audit.md): findings and evidence.
- [Design](support/cockpit-rest-repair/design.md): chosen implementation behavior.
- [Surface map](support/cockpit-rest-repair/surface-map.md): current and target boundaries.
- [Validation matrix](support/cockpit-rest-repair/validation-matrix.md): observable test cases.
- [Diagnosis runbook](support/cockpit-rest-repair/diagnosis-runbook.md): isolate the reported symptom without speculative repairs.
- [Source review](support/cockpit-rest-repair/source-review.md): pinned sources and review limitations.
- [Implementation prompt](support/cockpit-rest-repair/implementation-prompt.md): start/resume instruction, used only with explicit implementation authorization.
- [Acceptance record](support/cockpit-rest-repair/acceptance-record.md): unfilled evidence template.
- [Bundle manifest](support/cockpit-rest-repair/bundle-manifest.json): exact new files and SHA-256 hashes.

## Ordered work packages

Task files own status, dependencies and completion evidence. Execute serially;
this plan does not authorize parallel work or unrelated historical backlog.

| Order | Work package | Depends on |
| --- | --- | --- |
| 1 | [CPR-001 — Freeze the baseline, reproduce failures, and amend contracts](tasks/cpr-001-baseline-and-contracts.md) | None |
| 2 | [CPR-002 — Classify bridge failures and repair connection lifecycle](tasks/cpr-002-bridge-errors-and-reconnect.md) | CPR-001 |
| 3 | [CPR-003 — Preserve validation evidence and reconcile configuration stages](tasks/cpr-003-candidate-validation-pipeline.md) | CPR-002 |
| 4 | [CPR-004 — Retain operation handles and prevent uncertain resubmission](tasks/cpr-004-operation-recovery-and-replay-guards.md) | CPR-003 |
| 5 | [CPR-005 — Align manual operations and guarded host controls](tasks/cpr-005-rest-operations-and-host-controls.md) | CPR-004 |
| 6 | [CPR-006 — Move run-report browsing onto the existing REST routes](tasks/cpr-006-rest-run-reports.md) | CPR-005 |
| 7 | [CPR-007 — Render every failed read and expose accurate readiness](tasks/cpr-007-read-results-and-diagnostics.md) | CPR-006 |
| 8 | [CPR-008 — Prove the browser, launcher, CLI, and API boundaries](tasks/cpr-008-cross-boundary-regressions.md) | CPR-007 |
| 9 | [CPR-009 — Complete release evidence, documentation, and operator handoff](tasks/cpr-009-release-evidence-and-handoff.md) | CPR-008 |

## Acceptance and validation

The source-remediation milestone requires all of the following:

1. Candidate validate/required preview/install/confirm works through the selected
   client with exact candidate/base comparisons, preserved ownership and backup,
   and explicit incompatibility handling. Every refusal leaves Install disabled.
2. Known bridge problems, process failures, API errors and failed domain results
   remain distinguishable. The `reconnected` scenario has a regression test with
   stage-aware recovery; an actual underlying defect is fixed when reproduced.
3. Every keyed operation preserves a nonsecret original key before transmission,
   retains its operation ID when observed, survives tab unmount, and offers
   authenticated lookup/wait. No disconnect, timeout, refresh, remount or uncertain
   Apply creates another submission automatically.
4. Synchronous validation has no invented operation receipt. Lost host-write or
   install acknowledgement is reconciled under the configuration guard and never
   treated as proof that no write occurred.
5. Manual full sync/verification use the existing REST-backed client only within
   an explicitly supported, permitted profile. Guarded/unknown profiles and masked
   schedule controls refuse with an explanation, without changing host safeguards.
6. Run reports use authenticated, bounded existing REST reads with exact report
   identity. No direct `/srv/hfcache/runs` read remains in the plugin. Journals
   remain bounded diagnostics, never operation result authority.
7. Estimate, server version, status, inventory, report and operation views all
   show valid nonzero Envelopes, not successful-looking empty values. Old data
   after failed refresh is absent or explicitly stale and cannot authorize actions.
8. No credential, candidate document or raw diagnostic log is persisted in browser
   storage. Recovery handles are scoped to their original trusted host/profile/API
   authority; corruption or scope changes fail closed.
9. Required automated tests in the matrix pass, including component lifecycle,
   failed real CLI/Unix-socket boundaries, and staged configuration filesystem
   tests. Existing strict envelopes, bounded streams, no-cancel semantics and
   credential separation do not regress.
10. Every work package passes `scripts/check.sh` with the Cockpit stage actually
    executed. Final acceptance also runs `scripts/check.sh --with-build` and
    `make -C cockpit check`. Use the pinned Node/pnpm toolchain, not a silent skip.
11. Tasks, ADRs, contracts, release notes, progress audit and tracker are consistent;
    the source/deployment distinction and remaining installed acceptance are explicit.

Actual Cockpit/PAM/rootless-container proof is a separate evidence layer, not
implied by a mock. Run it only in a provisioned disposable environment with no
live archive. If that environment is unavailable, record the precise blocker and
leave that required acceptance item unpassed. Production symptom resolution is
not claimed until an authorized operator verifies the installed release and the
original candidate flow. Source implementation never clears existing NAS/workload
acceptance holds.

## Activation, commits and resumption

At explicit implementation authorization, inspect git history/status and the
current selector, compare the actual tree with the pinned review, and reconcile
any active plan. Recheck CPR IDs against pre-existing records outside this bundle;
the connector search returned no CPR matches but is not a substitute for a current
working-tree collision check. Preserve every historical ID and record.

Create or safely resume `fix/cockpit-rest-api-alignment`; do not discard unrelated
working changes. Activate this plan in `current.md` only then. Complete one task
per commit named `<CPR-ID>: <summary>`, including its tests, documentation,
invariant/ADR review, task status/evidence, progress entry and next-task pointer.
Use `this commit` while recording an uncommitted result; never invent a hash.

A blocker remains a blocker. Do not bypass missing host/runtime proof with a
local execution fallback, undocumented install, disabled security control, or
fabricated test result. On resumption reconcile git evidence, selected task and
lifecycle before repeating any operation. On completion preserve all plan/task
files and clear the selector; do not select old backlog.

## Lifecycle and amendments

- 2026-10-19: Draft created from the user's review/plan-bundle request at pinned
  commit `dcc2c562b52304541d0cb85d20fc046072038e79`. No implementation, tracker
  replacement, live inspection, credentials, host modifications or deployment
  occurred. Product tests were not run in this review environment.

- 2026-10-19: Activated by explicit implementation instruction on
  `fix/cockpit-rest-api-alignment`. HEAD equals the reviewed commit; no selected
  active plan required reconciliation. Imported untracked bundle retained.

- 2026-10-19: User steering authorizes development on this local host, a service
  outage if needed, and removal/restoration of the installed application only
  with necessary configuration backed up and restored. NAS data must remain
  unaffected. Prefer independent owned fixtures; preserve original guards, lock
  inodes, masks, hardening, credentials, receipts and pending operation identities.
  This narrowly supersedes the original no-host-inspection/change limit for local
  development; it grants no NAS/live workload, registry/push/merge/tag or other-host
  authority. Provision disposable local runtime fixtures before acceptance; do not
  treat the production deployment as a disposable archive.

- 2026-10-19: Baseline activation exposed a CAT acceptance test that incorrectly
  froze the live selector inactive after CAT-016. The baseline package may correct
  that regression to inspect CAT-016's committed selector, preserving historical
  completion while permitting this authorized plan. No product scope expansion.
