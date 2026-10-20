# WEB-002: Create the strict React workspace and mandatory local gates

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P0 |
| Depends on | [WEB-001](web-001-baseline-and-contracts.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-002: <completed outcome>` |

## Read before implementation

cockpit/package.json and reusable license notices; scripts/check.sh; docs/development.md; architecture.md sections 3 and 5; testing-strategy.md.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Create web/ with React, Vite, strict TypeScript, pinned compatible Node/pnpm and frozen lockfile. Add type-aware linting, no unsafe any propagation, no unchecked casts at network boundaries, accessible UI primitives and a minimal route shell. Select React tooling deliberately; reuse licensed pure components/helpers only after removing Cockpit transport assumptions. Audit bundled/transitive licenses. Keep production dependencies in the browser bundle or optional server closure, never Node in runtime.

Implement documented lint/typecheck/test:unit/test:component/build scripts. Use a maintained component-testing stack, deterministic fixture network mocks only at component level, and coverage reporting for new code. Add --require-web to the provider-neutral scripts/check.sh, without removing existing Python, docs, build/install or Cockpit checks. Strict mode must fail if prerequisites are missing; default backend-only mode may have an explicit loud frontend omission, but it cannot satisfy this plan's gate. Add safe help and script inventory entries. Establish ignored artifact locations.

## Unit and component validation

Test helper functions and framework setup; prove deliberately invalid strict TypeScript/unsafe decoder fixtures fail the gate. Test script argument parsing and missing-tool refusal without touching runtime state.

## Integration validation

Run frozen install twice, deterministic production build, lint/typecheck/component suite, and scripts/check.sh --require-web. Assert no source mocks, credentials or external CDN references in the production output.

## Functional validation

Run the real-browser empty shell and keyboard-navigation smoke on an owned loopback fixture, explicitly labelled preliminary rather than Caddy/backend acceptance. Confirm a missing required browser exits nonzero.

## Human documentation deliverables

Update docs/development.md and docs/scripts.md with exact new commands, versions, dependency provisioning and no-skip rule; document that Node is build-time only. Start the human UI navigation explanation.

## Acceptance

Reproducible locked React workspace exists; strict checks are enforced, not merely configured; production bundle is buildable; no new CI-provider dependency or runtime Node requirement; baseline gates remain intact.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-002, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
