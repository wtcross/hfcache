# WEB-016: Expose existing jobs, verification, diagnostics and reports

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-015](web-015-configuration-and-tag-ui.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-016: <completed outcome>` |

## Read before implementation

Operation controller; existing sync/plans/verification/diagnostics/refresh/runs contracts; Cockpit activity/report behaviors.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement Operations list/detail, original lookup, event/result presentation and run-report browsing. Connect full/selected sync, installed/candidate sizing, new/full/exact revision verification, estimate, diagnostics read-only/probing and metadata refresh to existing routes. Explain each scope's archive/Hub/control effects and effective permission. No byte percentage unless actual validated progress supplies it; no Cancel button.

Render queued/waiting-lock/running/terminal/interrupted/unknown observation separately, with persistent error/warning codes and full per-repository partial results. HFMNT010 is benign busy; integrity findings persist and direct to review/repair rather than suggesting blind sync/prune. Keep run IDs distinct from request/operation IDs. Show report and operation pagination and known loaded extent. Bounded journals are not substituted for results.

Navigation, background tabs, retries and page refresh retain original handles and do not resubmit. Expose read-only observation/export of safe original handles for operator handoff, not bearer-bearing URLs. Continue enforcing one unresolved mutation submission lane in the UI and backend guards.

## Unit and component validation

Component/state tests cover each action DTO, scope, permission, 202 versus completed output, every domain classification, partial reports, busy and missing-history results; ensure no mutation is registered as a read retry.

## Integration validation

Use real service/runner/private-worker fixtures for sync/verify/diagnose/refresh and reports with no live Hub. Inject queue wait, original-key conflict, worker disconnect, result size/event gaps and history expiration.

## Functional validation

Three engines submit/observe representative sync, verification, diagnostics and refresh via Caddy, then reconnect after dropped response with no duplicate effect. Follow a run report from repository detail and preserve findings/loaded-history labels.

## Human documentation deliverables

Complete operations.md and relevant troubleshooting/runbook links; update actual job examples and clear no-cancel/observer limitations. Human guides distinguish offline refresh, Hub sizing/diagnostics and verification.

## Acceptance

Existing operational capabilities are reachable and observable from the SPA with exact results, safe original-handle recovery, bounded reports and no fabricated progress/outcome.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-016, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
