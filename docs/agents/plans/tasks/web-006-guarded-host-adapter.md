# WEB-006: Implement a narrowly privileged host adapter and safe status projection

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-005](web-005-shared-caddy-spa-serving.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-006: <completed outcome>` |

## Read before implementation

Cockpit profile/config/systemd adapters; scripts/container-service.py inspection contract; protected release indexes and policy; docs/containers.md; new helper ADR/private protocol.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement a fixed-operation host-administration helper boundary with protected Unix transport, real peer verification, bounded strict requests and independently provisioned policy. Begin with config-base/status reads and host status; write grammar remains denied until its task. Keep all resource paths/service-manager/unit names fixed, no shell or generic filesystem/DBus/engine dispatch. API remains non-root and receives only the narrow helper socket; no helper access for Caddy or verifier.

Implement GET /host/status with explicit supported/guarded/unknown/unavailable state, safe release/policy binding, effective action permissions, fixed system services/timers and schedule view/revision. Preserve rootless denied schedule/observer semantics; lack of a guard is not permission. Reuse the existing proven profile inspection safely rather than ignoring its source/index checks. Generalize with explicit backward-compatible policy migration only if needed; do not auto-provision wider privileges.

Enforce fresh helper/policy proof at Basic human admission for archive/Hub/control actions as required by the former plugin's scope, while keeping domain guards final. Existing service bearer behavior and unknown authority remain explicit. Bound host inspection time/output and classify failures without claiming API/worker crashes.

## Unit and component validation

Test protocol unknown keys/version/commands/units/paths, malformed sizes and peer mismatch, protected policy no-follow/race checks, release drift, fixed-manager scoping and fail-closed permission computation.

## Integration validation

Exercise real Unix peer credentials from the intended unprivileged caller, helper unavailable/restart/timeouts and protected local config/status reads. Verify helper cannot access archive/Hub secrets; hostile local caller and header claims cannot manufacture authority.

## Functional validation

In an isolated systemd/rootless guest, prove actual container host UID mapping and socket separation, denied basic archive/Hub/control actions on the guarded policy, and visible UI denial reasons. Mocked unit outputs do not close the platform proof.

## Human documentation deliverables

Create administration guide and host-helper deployment/security sections. Document what permissions mean, supported profiles, independent policy provisioning and missing-helper troubleshooting. Update role/secret/socket matrices and script inventory.

## Acceptance

Authenticated host status is real, bounded and safe; helper isolation and peer identity are proven; no new general host authority exists; guarded rootless behavior is preserved and readable in the UI.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-006, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
