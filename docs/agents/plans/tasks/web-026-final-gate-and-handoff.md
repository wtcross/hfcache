# WEB-026: Close the implementation with complete evidence and an operator handoff

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P6 |
| Depends on | [WEB-025](web-025-retire-cockpit-plugin.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-026: <completed outcome>` |

## Read before implementation

All task evidence; current selector; acceptance/test mappings; clean branch/source artifact identity; docs and compatibility/retirement records.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Audit every acceptance case and task dependency against actual passing test node IDs and artifacts. No unresolved blocker, silent skip, mocked-only host parity, placeholder endpoint, unsupported browser or deferred human documentation may be relabelled complete. Reconcile current plan/task/progress/ADR/invariant state with git. If needed split additional bounded tasks, allocate fresh work-package IDs and keep this task blocked until their evidence exists.

Run the strict full gate and final clean installed functional/compatibility smoke using the final source/artifacts after Cockpit removal. Record source, build/runtime hashes, dependency/license inventory, browser/profile matrix, unit/integration/functional counts, docs gate and honest residual production/NAS limitations. Keep raw secret-free evidence locators outside normal source as appropriate.

Provide a human operator handoff with how to build/install/validate through the existing Caddy, configure the one Basic user, preserve original handles/candidates, understand restricted profile controls, and perform a compatible rollback only when separately authorized. Set plan completed and clear current selector only when all scoped acceptance is met. Commit this work package on feat/web-ui; leave merge/push/tag/deploy for explicit later instruction.

## Unit and component validation

Run all unit/component/coverage/type/lint/doc checks and validate no critical acceptance case lacks executable coverage. Record actual results, not intended commands.

## Integration validation

Run all integration/private-worker/CLI/MCP/strict install/format compatibility suites on final source and artifact indexes. Verify final baseline gates were not weakened during retirement.

## Functional validation

Run scripts/check.sh --require-web --with-build --with-web-functional after final changes; include actual same-Caddy browser+REST+MCP, supported native and guarded rootless, negative security and interrupted-operation/config cases with no required skips.

## Human documentation deliverables

Update release notes as unreleased/source-ready, human handoff and actual fixture acceptance summary; preserve current production deployment-status facts. Complete task/progress/ADR/invariant review and plan/current records in this commit.

## Acceptance

All requested source features, unit/integration/functional testing, documentation and Cockpit source retirement are complete and evidenced on a clean feature branch; production rollout/remote publication remain explicitly unperformed.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-026, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
