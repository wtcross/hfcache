# WEB-018: Preserve fixed schedule, observer and diagnostic host functions

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P4 |
| Depends on | [WEB-017](web-017-maintenance-ui.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-018: <completed outcome>` |

## Read before implementation

Existing Cockpit systemd/schedule/journal code; CP-05/06/12 and host-policy bindings; helper transport; host API definitions.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement fixed sync schedule validation/change endpoints, observer stop, and bounded journal diagnostics through the narrow helper. Use actual systemd-analyze calendar/timespan with fixed argv, strict values, finite output/time and no shell interpretation. Managed drop-in apply/reset keeps ownership/mode, expected revision, backup/outcome evidence and explicit manager reload semantics. Pause/resume touches only the fixed sync timer and documented activation semantics.

Schedule and observer changes use keyed receipts and private durable helper outcomes with post-timeout read-only reconciliation. Stop observer requires the expected service/invocation binding and explicit supported-profile permission; it never claims cancellation of accepted API work. Never stop/start hfcache.target or API/worker, never enable verification timer, never redirect system names to user units. On the current rootless profile denied schedule/observer remains denied; test supported positive native behavior rather than create extra scope.

Journal GET exposes only a fixed source enum, finite lines/bytes/time and opaque bounded cursor, with redaction and explicit gaps. It is diagnostic, not an authority for operation completion. Wrong/missing helper policy, release drift, unsafe drop-ins, user-manager confusion or actual observer ambiguity refuses effects.

## Unit and component validation

Test action enums, calendars/timespans including shell/control characters, expected revision/invocation mismatches, managed drop-in paths, budgets/redaction, no target/verify timer actions and restart/unknown outcome classification.

## Integration validation

Exercise real helper sockets/files/processes in a guest and API operation reconciliation across timer/drop-in/observer actions; concurrently modify schedules and revoke policy to prove fresh refusal. Bounded journal stream cannot exhaust operation readers.

## Functional validation

Actual disposable systemd native profile: validate/apply/reset/pause/resume sync schedule and stop a proven fixture observer while backend work continues. Guarded rootless profile: same actions denied with real reasons, no service-manager fallback; verify timer stays disabled.

## Human documentation deliverables

Update administration/deployment/troubleshooting guides, host API effects, fixed manager and observer semantics, script inventory and schedule reference. Clearly label positive supported profile versus current guarded restriction.

## Acceptance

All retained Cockpit host functions have narrow typed replacements, positive supported-profile proof and denied-profile proof; no general command authority, unsafe cleanup or false cancellation is introduced.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-018, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
