# WEB-011: Build authority-scoped query state and durable browser observation

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-010](web-010-repository-card-read-api.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-011: <completed outcome>` |

## Read before implementation

Typed client; Cockpit operation registry/recovery/event/failure tests; operation endpoints and errors; architecture operation constraints.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement the route-independent operation controller and bounded session recovery registry. Generate/store original key before POST; validate same authority/archive/subject scope; block submission on unresolved operations or pre-submit storage failure; preserve in-memory handle and block after post-submit storage failure. Restored terminal summaries require authenticated original observation before unblocking. Keep 32-record/64-KiB bounds and never evict unresolved entries.

Separate query loading/stale/unavailable/failed from operation queued/waiting/running/terminal/interrupted/observation-unknown states. Preserve request versus domain IDs and raw classified structured results through decoders; never parse human messages for authority. Poll result/events with finite read retry/backoff and cursor sequences, show gaps, stop when appropriate and keep observation after route changes. Abort read observation, not the backend operation. No POST retry/cancel/recover after timeout.

Clear private caches on changed authority/auth failure without discarding unresolved safe handles; prevent restored cross-origin/archive entries from auto-observation or auto-rebinding. Cross-tab coordination is bounded and advisory; backend idempotency/locks remain final. Provide manual original-key/ID lookup for migration from Cockpit.

## Unit and component validation

Test full registry/state transition matrix, corrupted storage, quota pre/post POST, restored metadata, scope drift, limits, event gaps, 202 semantics, no automatic retry and failed Envelope classifications.

## Integration validation

Use real operation API/runner/store with lost admissions/results, restart, expired/missing history and original-key lookups. Assert exactly one actual effect/operation even across remounts and observer timeouts.

## Functional validation

Through browser/Caddy start a fixture operation, navigate/unmount/reload, disconnect/reconnect, reopen original handles and preserve unknown state. Run two tabs and storage failure injections; inspect that no secret/TOML/body is persisted.

## Human documentation deliverables

Create user operations/reconnect guide and troubleshooting decision paths, including original handles, browser-session limits, stop-observing versus cancellation and missing-history stop conditions.

## Acceptance

Operation observation survives the supported UI lifecycle without replay and without false outcomes; all uncertainty/limits are visible; original safe handles remain recoverable and authority-scoped.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-011, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
