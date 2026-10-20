# WEB-025: Retire Cockpit packaging only after proven complete replacement

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P6 |
| Depends on | [WEB-024](web-024-human-documentation-acceptance.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-025: <completed outcome>` |

## Read before implementation

Completed parity register and functional/compatibility evidence; cockpit source/tests/license; all installer/build/index/client references; migration guide.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Inventory every Cockpit-only source file, test, asset, build/install hook and documentation entry and classify retention/move/replacement/removal. Port reusable pure logic and all safety regressions before removing the old harness; preserve LGPL notices for copied code. Keep generic fixed CLI clients, container runtime helpers, shared policy/lock behavior and other users of them.

Remove Cockpit as the newly shipped management UI and retire its runtime dependency paths. Update gate flags/install manifests/index checks to require web rather than Cockpit for new full releases; legacy flag handling must produce a clear documented message, not silent skip. Preserve backend-only gates and all equivalent test coverage. Remove no production Cockpit package, global service or browser storage in this source task.

Preserve historical plans, ADR reasoning, deployment evidence and old immutable release artifacts. Mark old human docs legacy with migration links as appropriate rather than breaking history. Every parity row must point to a covered new screen/action or a legitimate profile-specific denial; link-to-Cockpit and 'future work' fail replacement acceptance. Remaining original handles/candidates are supported through safe manual lookup/reconciliation, not automatic adoption/replay.

## Unit and component validation

Test new gate/install manifests and absence of frontend Cockpit imports/bridge calls in production web/app code. Prove all ported critical failure/operation/config tests still run.

## Integration validation

Run full backend/frontend/doc/build and installed artifact checks without cockpit build artifacts or installed plugin. Verify generic client/runtime helper callers remain functional.

## Functional validation

Run full three-browser/native/rootless Caddy functional workflows with no Cockpit package/runtime available in the test target; observe denied profile paths and permitted supported controls. Repeat original-key migration lookup.

## Human documentation deliverables

Finalize migration-from-cockpit.md, supported UI/navigation/install pages and legacy annotations; update script/build/gate help. Preserve historical evidence and document limited uninstall scope for future operator authorization.

## Acceptance

New releases no longer depend on or ship Cockpit as their UI; all retained capabilities and safety tests have proven replacements; source retirement does not modify the live host or erase history.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-025, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
