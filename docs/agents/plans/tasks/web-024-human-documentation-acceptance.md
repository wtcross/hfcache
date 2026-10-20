# WEB-024: Complete the human operator and user documentation walkthrough

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P6 |
| Depends on | [WEB-023](web-023-compatibility-and-rollback-drill.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-024: <completed outcome>` |

## Read before implementation

All human guides created in earlier packages; documentation-map.md; actual installed fixture screens and evidence; docs validator and script inventory.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Audit every user-visible workflow against real implemented behavior and guide wording: login, scopes/filters, publication/README, tag/config apply/conflict, operations and reconnect, verification/maintenance, host scheduling/denials and deployment/rollback. Fix inaccurate labels, undocumented side effects, missing stop conditions and assumptions about production permissions.

Finish human navigation from root README/docs index, cross-links to reference/runbooks, useful screenshot alt text and synthetic actual-UI screenshots. Keep technical references accurate without making users read agent plans. Document Basic credential lifetime, no app logout, whole-archive trust, blocked media, no automatic payload/Hub fetch, no job cancel, unknown history and current restricted-profile behavior.

Validate every new script is classified and every example is safe/contextual. Do not execute effectful snippets blindly. Documentation status distinguishes source availability, fixture acceptance and real deployment; no unchecked TODO or placeholder guide is published as completed. Prepare operator handoff checklist without checking production boxes.

## Unit and component validation

Run docs links/anchors/image/route/default/schema/helper inventory bad-fixture tests and safely parse operational examples without callbacks. Test documentation grep/audience rules do not exempt new human guides.

## Integration validation

Validate documented config/REST examples against actual strict parsers/routes and script help behavior. Independently compare docs matrices to actual routes and permissions, not just generated matching tables.

## Functional validation

Follow each representative human guide on the installed fixture, including an error/refusal and reconnect/conflict path. Record manual keyboard/screen-reader smoke and actual UI screenshots with fixture/version labels.

## Human documentation deliverables

This package completes and verifies documentation already delivered throughout WEB-001..023. Update README/docs navigation, all docs/web-ui guides, API/server/security/discovery/config/deployment/containers/development/script references and migration notices as affected.

## Acceptance

A human can operate and troubleshoot the UI from the guides without agent context; examples, routes, screenshots and safety statements match actual tested behavior and no production readiness is fabricated.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-024, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
