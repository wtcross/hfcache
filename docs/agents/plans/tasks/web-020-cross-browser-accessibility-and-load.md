# WEB-020: Harden end-user workflows, accessibility and bounded performance

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P5 |
| Depends on | [WEB-019](web-019-administration-and-diagnostics-ui.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-020: <completed outcome>` |

## Read before implementation

All new screens/controllers; acceptance cases; real functional harness; testing browser/a11y/performance budgets.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Complete the cross-browser matrix of Library/detail/README/tags/config/jobs/maintenance/admin workflows over real Caddy/API. Stress changing current pointers, slow responses, auth/authority changes, large manifests and route churn without mixing data or retrying writes. Test new server/UI contract mismatch with an old open page.

Apply automated accessibility checks and manual keyboard/screen-reader smoke to tables, filters, dialogs, validation, global recovery and content views. Fix focus order/restoration, announcements, semantic names, contrast and responsive/zoom issues. Use reduced motion and no network fonts. Ensure virtualized content remains operable.

Measure bundle size, initial usable Library, long tasks, DOM/memory bounds and polling on a fixed realistic synthetic fixture. Optimize avoidable per-row requests and lazy-load costly renderers without new aggregate endpoints. Enforce declared coverage/bundle/performance targets; record observed hardware/browser/data, not universal performance claims. No unchecked flaky-test retries or silent acceptance target inflation.

## Unit and component validation

Run full new frontend unit/component coverage and critical branch mapping; regress every discovered bug with a focused test. Verify coverage exclusions cannot hide security/controller code.

## Integration validation

Run slow/cancelled/stale/large-response loops against real API pools and assert bounded request concurrency, response work and retained memory. Decode large integer and limit failures safely.

## Functional validation

Run Chromium/Firefox/WebKit, 1440px/390px and 200% zoom, keyboard dialogs, screen-reader smoke, hostile README network inspection and 100 route/refresh cycles. Record target budgets and resolve serious/critical accessibility failures.

## Human documentation deliverables

Document browser support, keyboard/use patterns and practical large-library limitations. Correct any guide label/screenshots discovered inconsistent during real workflows.

## Acceptance

Cross-browser functional, accessibility and bounded-performance acceptance has actual evidence; the UI remains safe/usable under races, large data and interruption rather than only happy-path screenshots.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-020, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
