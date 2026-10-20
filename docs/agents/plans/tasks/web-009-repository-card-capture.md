# WEB-009: Capture publication-pinned README presentation records safely

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P2 |
| Depends on | [WEB-008](web-008-atomic-configuration-application.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-009: <completed outcome>` |

## Read before implementation

catalog_capture/extractors/models/read/write budgets; sync/repair lifecycle; publication manifests; discovery and adjunct schema contract; card specification.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Add the independently versioned card adjunct and central layout builders under the approved supplemental namespace. Capture root manifest-listed README.md in existing writer-owned post-publication sync/repair and technical=true offline refresh work. Read no code, loaders, remote URL, arbitrary path or tensor payload. Enforce no-follow regular-file/descriptor stability, source identity, source/presentation byte bounds and shared aggregate work limits before allocations.

Retain sanitized inert Markdown separately from structured declarations. Record source expected digest and presentation identity without conflating them; implement and document bounded README source-digest comparison as a narrow metadata check where selected. Capture failure/mismatch/unsupported/oversize states warn without undoing valid publication integrity. Missing README is normal. Redact registered/recognized credentials before durable presentation; do not alter immutable source/manifests or structured observations to hold the body.

Keep old sync/refresh request and result shapes: technical=true now additionally captures presentation under a documented adjunct contract. No redundant refresh endpoint or cards flag unless actual compatibility forces a separately recorded adjustment. Whole-record atomic writes follow existing initialized archive/preflight/writer-lock/journal-safe rules, preserve unknown records, and never use GET as refresh. Bound serialized record and aggregate count/storage; no new global index or automatic garbage collector.

## Unit and component validation

Test safe/hostile paths, symlinks/special files, descriptor changes, manifest mismatch, invalid UTF-8, exact limits/Unicode/JSON expansion, secrets, unsupported versions, atomic write failures and stale adjunct membership. Assert immutable evidence byte stability.

## Integration validation

Run real sync/repair/refresh service fixtures for model/dataset/absent README and retained-SHA recapture. Inject card failures after successful publication and verify existing outcome/warning classification and old response validation.

## Functional validation

In the Caddy/API fixture run the existing metadata-refresh workflow over owned retained publications, then inspect the resulting adjunct through test evidence. Confirm no Hub contact and no altered verification confidence; UI display arrives in WEB-010/014.

## Human documentation deliverables

Write readme-cards provenance/refresh/limitations guide sections; update discovery, schemas, security, invariant adjunct exception and compatibility notes with precise bounds and capture effects.

## Acceptance

Cards are bounded derived records tied to exact publications; capture executes no repo code/network; old evidence/results remain compatible; partial capture is explicit and never turns into archive corruption or silent success.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-009, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
