# WEB-019: Complete the operator administration workspace

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P4 |
| Depends on | [WEB-018](web-018-schedule-observer-and-journal.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-019: <completed outcome>` |

## Read before implementation

Host status/schedule/journal endpoints; diagnostics/runs; config forms; current Cockpit dashboard and warning runbooks.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Integrate Administration panels for profile/permissions, archive health/free reserve, installed config, diagnostics, fixed sync schedule/observer, read-only verification timer and bounded journals. Surface archive/Hub/control/config/schedule/observer permission reasons independently from Basic authentication and daemon ready. Unknown/missing facts never look healthy or writable.

Map existing archive-health fields and warning codes to human guidance and relevant actions; distinguish snapshot status, actual verification, metadata coverage, API readiness and host restrictions. Show safe server/UI/release identities without secrets or false deployment claims. Schedule forms preview normalized expression/next event and explicit timezone, show expected-revision conflict, and explain reset/pause semantics. Display original operation recovery globally even on host panels.

Ensure all parity rows are linked to a real workspace/control or a profile-justified denial, not a placeholder toast. Keep technical evidence available without burying ordinary workflows. No direct Cockpit/D-Bus/file/shell dependency remains in newly implemented screens.

## Unit and component validation

Component tests cover permission/status combinations, unknown states, all legacy warning/health mappings, schedule timezone/reset/conflict, verification timer read-only and journals' diagnostic labels.

## Integration validation

Call real host/diagnostic/config routes with multiple policy/profile bindings and unavailable helper. Assert no effects when viewing or refreshing read panels and no broad service control in requests.

## Functional validation

Follow operator administration guide in three browsers/Caddy on permitted native and guarded rootless guests: inspect, diagnose, edit permitted schedule, observe a denied action and read bounded diagnostic logs; verify no forbidden unit/timer changes.

## Human documentation deliverables

Complete administration.md and troubleshooting, update navigation, operator screenshots and parity documentation. Explain human consequences of version/profile mismatch and unsupported actions.

## Acceptance

Administration replaces the existing operator information/control surface accurately, with clear permission/unknown states and no dependence on Cockpit or a browser host bridge.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-019, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
