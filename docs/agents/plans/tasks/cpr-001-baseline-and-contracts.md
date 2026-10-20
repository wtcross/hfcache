# CPR-001: Freeze the baseline, reproduce failures, and amend contracts

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | None |
| Work package / commit | `CPR-001` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Establish the current baseline before modifying behavior. Read the pinned audit,
then inspect actual git history/status, the current selector, relevant progress
handoff and deployment status. Compare current Cockpit, CLI, API, launcher,
container profile and documentation against the reviewed SHA. Record source drift
rather than assuming the bundle describes a later checkout exactly.

Recheck CPR work-package IDs against existing records outside imported files.
Activate only upon explicit implementation authorization, on the dedicated branch.
Preserve another selected plan unless its pause/supersession is explicitly
reconciled. Draft extraction alone does not select this work.

Produce a safe baseline diagnostic inventory: source commit, browser build,
physical launcher/profile binding, image identity, API/client versions when available,
profile restrictions, and which evidence is source-only. Never inspect secret
contents. Identify each stage behind the Validate candidate button, including its
host write and possible keyed Hub-contacting plan. Instrumentation/reproduction
must locate the failure relative to those stages, not infer daemon failure from
one message.

Record minimal fail-before-fix cases for F01/F02/F05 and tab unmount. Do not commit
a permanently failing default test suite or declare mocks to be installed proof.
Introduce regression assertions with their owning fix; use bounded investigation
fixtures for baseline evidence. Capture the original symptom in a disposable
Cockpit environment when available; otherwise keep that cause explicitly unresolved.

Adopt the design decisions, marking known conformance gaps until the respective
work package lands. Allocate a real new ADR number if needed. Amend the relevant
contract rationale for manual REST jobs and REST report browsing in coordination
with CPR-005/006, retaining historical text/status links. No blanket override of
CP-04/09, decision 122, or the guarded rootless restrictions is allowed.

## Acceptance criteria

A current-tree source map and exact discrepancy list exist. F01/F02/F05 have
reproduction inputs and observed current behavior, without unsupported live-cause
claims. Scope, branch, IDs, lifecycle and prerequisite evidence are consistent.
Contracts explicitly distinguish implemented repairs from planned amendments.
Every production/disposable test restriction and missing prerequisite is recorded.

## Contracts, invariants and ADRs

Review `AGENTS.md`, planning/workflow/environment, CP-01–14, INV-006,
workflow INV-011, decision 122 and the relevant ADR index relationships. Record
rootless fixed-launcher/credential and existing workload-hold review. This package
may edit documents and test investigation fixtures only; new product behavior is
owned by following tasks.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

Executed bounded investigation:
`rtk node --experimental-strip-types docs/agents/plans/support/cockpit-rest-repair/baseline-reproduce.ts`
(exit 0). V01/V11/V24/V27 baseline gaps reproduced as qualified above; V55
installed identity remains unavailable. Node v24.18.1/pnpm11.18.0 verified.
Documentation alignment: 183 human documents/19 helpers, exit 0. Full gate retry passed; see completion evidence.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

2026-10-19: Activated on the dedicated branch by explicit user instruction. No
other selected active plan; HEAD equals the reviewed baseline. Full tracked and
untracked scan outside the import found no CPR collisions. Preserved the imported
bundle and all prior completed/handoff records. Decision 134 allocated from actual
repository state. Product behavior remains unchanged in this package.

[Baseline evidence](../support/cockpit-rest-repair/baseline-evidence.md) records
current surfaces, F01/F02/F05 reproduction, source-only F04 lifetime evidence and
pipeline stage inventory. [Raw bounded results](../support/cockpit-rest-repair/baseline-results.jsonl)
retain the observed output. Original installed trigger is unresolved.
No production inspection or host operation was performed. V54 needs an explicitly
provisioned isolated Cockpit/PAM/systemd/rootless target with synthetic credentials,
immutable fixtures and no live/NAS archive; its absence blocks runtime acceptance,
not this baseline-recording task. Required repair regressions remain unpassed.

## Completion evidence

2026-10-19, CPR-001, this commit: baseline/source map, ID/branch/selector
reconciliation, pure F01/F02/F05 and mounted F01/F05/root-remount evidence complete.
Gate retry: `rtk proxy scripts/check.sh` exit 0, 5008 passed/42 deselected in
593.55s; wheel/base/server/server+MCP checks, actual Cockpit lint/style/types,
170 tests (0 failed/skipped) and production build. Initial gate failure and narrow
historical-test correction retained below. Documentation alignment passed.
CP-01–14, INV-006, workflow INV-011 and decisions 087/089/092/118–122/127/133
reviewed; decision134 adopts repair requirements with current gaps explicit.
CP-04/09 behavior remains unchanged pending its owning amendments; exact config,
credential, no-cancel and workload holds preserved. No runtime dependency or
product behavior changed. Full isolated real runtime remains to be provisioned
under the user's local-development amendment; original installed trigger unresolved.
See [acceptance record](../support/cockpit-rest-repair/acceptance-record.md) and
completed [progress entry](../../progress.md). Next: CPR-002.


### Gate prerequisite correction

The first `rtk proxy scripts/check.sh` failed with 1 failed/5007 passed/42
deselected (600.24s): CAT-016's evidence test required today's selector to remain
inactive after historical completion. Activation necessarily changes that selector.
The test now verifies the inactive/empty selector in the actual CAT-016 commit,
while still requiring retained completed plan/task records. Focused evidence tests:
2 passed (1.07s). This narrow workflow regression correction is included in the
baseline package; it changes no product behavior or completed historical record.
The full gate is being rerun, with frontend execution still required.


Mounted baseline: `rtk node docs/agents/plans/support/cockpit-rest-repair/baseline-browser.mjs`
exit 0, actual Firefox/React Maintenance and QueryError through the actual
adapter/runner at a controlled Cockpit process boundary. F05 enabled Apply after
one uncertain synthetic submission; F01 lost stage/problem; root remount lost
handles with zero calls. See bounded browser artifact linked in acceptance record.
This strengthens source baseline evidence without claiming real tab/PAM acceptance.
