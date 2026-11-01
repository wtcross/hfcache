# WEB-026: Close the implementation with complete evidence and an operator handoff

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P6 |
| Depends on | [WEB-025](web-025-retire-cockpit-plugin.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-026: <completed outcome>` |
| Model / effort | `gpt-6.1-sol` / medium |

## Execution approach

Apply the [shared bounded-testing policy](../support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort).
Effort rationale: The work reconciles concrete evidence, runs required final checks and prepares an accurate handoff.
Reconcile matching evidence before final-source gates and fresh installed acceptance. Rerun other checks only for a concrete gap, change or failure. Escalate to high for conflicting evidence, a safety contradiction or an actual final-gate diagnosis.

## Read before implementation

All task evidence; current selector; acceptance/test mappings; clean branch/source artifact identity; docs, compatibility and legacy-deprecation records.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Audit every acceptance case and task dependency against actual passing test node IDs and artifacts. No unresolved blocker, silent skip, mocked-only host parity, placeholder endpoint, unsupported browser or deferred human documentation may be relabelled complete. Reconcile current plan/task/progress/ADR/invariant state with git. If needed split additional bounded tasks, allocate fresh work-package IDs and keep this task blocked until their evidence exists.

Run the strict web/backend gate and final clean installed functional/compatibility smoke using the final source/artifacts. Per the user's2026-11-01 instruction to ignore and deprecate Cockpit, preserve its legacy source/history/licenses/live installation; no plugin removal or further plugin validation is a prerequisite. Record source, build/runtime hashes, dependency/license inventory, browser/profile matrix, unit/integration/functional counts, docs gate and honest residual production/NAS limitations. Keep raw secret-free evidence locators outside normal source as appropriate.

Provide a human operator handoff with how to build/install/validate through the existing Caddy, configure the one Basic user, preserve original handles/candidates, understand restricted profile controls, and perform a compatible rollback only when separately authorized. Set plan completed and clear current selector only when all scoped acceptance is met. Commit this work package on feat/web-ui; leave merge/push/tag/deploy for explicit later instruction.

## Unit and component validation

Run all unit/component/coverage/type/lint/doc checks and validate no critical acceptance case lacks executable coverage. Record actual results, not intended commands.

## Integration validation

Run all integration/private-worker/CLI/MCP/strict install/format compatibility suites on final source and artifact indexes. Verify required new-web/backend gates remain strict through the legacy-deprecation amendment.

## Functional validation

Run `scripts/check.sh --require-web --with-build` after final changes and separate direct installed final acceptance under the adopted product-focused criteria: actual same-Caddy Chromium/Firefox/WebKit at both prefixes on native/rootless, REST/MCP, supported native/guarded-rootless controls, negative security and interrupted-operation/config behavior at the relevant boundary. Account for all95 scenarios without required skips. Reuse unchanged deep proofs with explicit justification. The existing `--with-web-functional` runner is optional and remains strict if invoked; never claim it passed from direct checks.

## Human documentation deliverables

Update release notes as unreleased/source-ready, human handoff and actual fixture acceptance summary; preserve current production deployment-status facts. Complete task/progress/ADR/invariant review and plan/current records in this commit.

## Acceptance

All requested new-web source features, unit/integration/functional testing,
documentation and legacy deprecation handoff are complete and evidenced on a
clean feature branch. All95 new-web behaviors and minimum layers remain;
production rollout/remote publication and live plugin uninstall are unperformed.

The task also requires the existing strict web/backend `scripts/check.sh` gate
and functional checks described above. The latest user amendment requires no
further legacy Cockpit checks. New capabilities are not completed solely by
adding test descriptions. Update actual test-to-case mappings and run them.
Documentation and relevant contract/invariant/ADR updates land with the behavior.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-026, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
