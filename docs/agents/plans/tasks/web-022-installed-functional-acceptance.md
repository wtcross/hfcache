# WEB-022: Prove full installed functionality on isolated native and rootless targets

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P5 |
| Depends on | [WEB-021](web-021-immutable-ui-release-packaging.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-022: <completed outcome>` |

## Read before implementation

Strict final functional gate and fixture runner; artifact indexes from WEB-021; complete parity/acceptance matrices; actual guest hardening checks.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Run the full application and platform functional profiles using exact installed release artifacts, trusted private TLS and real browsers. Rootless uses actual Podman/systemd identity/manager boundaries and native uses actual bound system units; keep guests and state disjoint from production. Capture peer, service, cgroup, socket, asset and secret visibility evidence from running processes, not only template inspection.

Exercise every required UI workflow including real config application, card read/capture, original operation recovery, worker verification, all maintenance fixture effects, positive supported schedule/observer behavior and guarded rootless denials. Existing CLI bearer reader/writer and fourteen read-only MCP tools operate through the same Caddy concurrently. Test missing/unsafe config/helper, late permission drift, lost response/process interruption and drains with evidence preserved.

Fix discovered defects with scoped tests and recorded work-package boundaries; split follow-up packages if needed without editing completed evidence. A missing browser/image/guest/network isolation resource blocks this task; do not redefine component fixtures as platform acceptance. Do not run live Hub or NAS tests to compensate.

## Unit and component validation

Full backend/frontend/unit/component gates remain green; trace any installed failures to new regression tests. Validate acceptance evidence structure and required test-to-case links.

## Integration validation

Run all new integration suites plus existing CLI/HTTP/Unix/worker/MCP regressions and safe release install checks on the selected artifact source. No skipped required suite.

## Functional validation

Execute scripts/check.sh --require-web --with-build --with-web-functional in the documented owned environment; all browser and supported profile cases pass. Record exact artifacts, browsers, guest setup, exit codes and meaningful assertions, with raw evidence safe to retain.

## Human documentation deliverables

Correct deployment/troubleshooting guides from the installed walkthrough. Add a human-readable test-release acceptance summary that explicitly excludes production rollout/NAS proof.

## Acceptance

Real installed native/rootless functional acceptance is complete with no mock-only parity claims or skipped prerequisites; evidence identifies exact artifacts and the limits of the proof.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-022, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
