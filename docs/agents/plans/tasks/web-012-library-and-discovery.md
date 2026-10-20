# WEB-012: Implement the unified model and dataset Library

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-011](web-011-query-and-operation-state.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-012: <completed outcome>` |

## Read before implementation

Catalog query/coverage models and routes; repository/status read shapes; approved Library screenshot; interface filter semantics.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build the dense accessible Library table with All/Models/Datasets, configured/archived/all and current/retained scopes, literal ID/tag search, all/any tag filters/provenance, format and model-only variant filters. Encode only supported API query keys; reflect filters in deep links and clear incompatible dataset/model predicates deliberately. Preserve normalized values while presenting readable labels and debounced finite reads.

Join catalog rows to bounded status/revision metadata by validated type/ID and authority, not array position. Keep known matches, coverage, configured/enabled/archived/unmanaged and last-observed tags distinct. Summaries must state scope and source; don't invent archive-wide disk usage or counts from a single page or double-count hardlinked logical bytes. Page/reset correctly on stale cursors and explicit budget failures, without hidden unbounded collection.

Actions use explicit reviewed canonical selected repositories and current permissions. No partial-weight selection or unbounded bulk-all-results mutation. Friendly empty and unavailable states preserve unknown coverage. Large results are virtualized/paged, keyboard usable and responsive.

## Unit and component validation

Test filter combinations, exact query grammar, all/any/provenance, model-only dataset refusal, Unicode query bounds, same-variant semantics and table empty/error/coverage states.

## Integration validation

Call real catalog/status with all fixture repository states, page/limit changes, curation-only invalidation, stale cursor, malformed responses and selection changes; verify stable keyed joins and bounded requests.

## Functional validation

Three browsers through Caddy perform ID/tag search, filter a model variant, switch to datasets/configured/unmanaged, page and return via deep link. Assert no unsupported upstream request and no false 'no matches' under incomplete coverage.

## Human documentation deliverables

Create library.md and update root navigation; explain scopes, search boundaries, unknown technical evidence, logical sizes and filter combinations with synthetic examples/screenshots.

## Acceptance

The Library exposes existing hfcache discovery and inventory accurately with bounded requests and useful filters; model/dataset/provenance distinctions and unknown coverage survive all read states.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-012, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
