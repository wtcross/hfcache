# WEB-013: Build rich exact-publication model and dataset detail pages

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-012](web-012-library-and-discovery.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-013: <completed outcome>` |

## Read before implementation

Catalog detail/variants, references/manifests/revisions, verification evidence; model/dataset screenshots; exact identity and dataset declaration contracts.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement stable repository routes plus exact selected SHA/publication state in URLs. Resolve current separately, then pin all derived panel queries to the resulting pair. Provide Overview, Variants/Dataset details, Files & manifest, Revisions, Integrity and Activity tabs. Switching selection invalidates old requests and does not mix cards/variants/verification from different publications.

Show all existing structured evidence with source/capture/coverage: task/language/license/base model/upstream tags; model format/encoding/role/method/scheme/bits/group size/member paths and bytes/completeness/diagnostics; dataset static configs/splits/features/formats. Keep tags explicitly current or last-observed. Unknown values stay unknown; do not infer parameter count/context/GPU fit/rows from filenames.

Show exact publication ID, full/copyable SHA, generation, timestamp, manifest path/digest and logical file/byte totals from available payloads. Provide a bounded accessible file/manifest table and copyable labelled consumer locators, no raw payload endpoint. Integrity uses existing exact-publication evidence; metadata completeness and API health never substitute. Activity is linked loaded history with explicit extent, not an invented complete audit.

## Unit and component validation

Test identity pinning, race/stale queries, conditional model/dataset fields, unknown versus zero, provenance labels, manifest integer/budget handling and URLs/link protocol safety.

## Integration validation

Exercise current changes, old retained publications, repair same-SHA/new-publication, corrupt/missing catalogs with authoritative manifest inventory, and oversized detail/manifest responses against real APIs.

## Functional validation

Navigate all tabs for model and dataset through Caddy, bookmark an old exact publication, change current, revisit, then remove that publication and verify explicit unavailable rather than latest fallback. Test file table keyboard use and consumer-locator labels.

## Human documentation deliverables

Create repository-details.md explaining all identity/evidence classes and dataset limitations; update consumer links and troubleshooting. Screenshots must come from the actual synthetic functional deployment.

## Acceptance

Each detail page surfaces the available evidence without fabricating metadata or mixing publications, supports models/datasets correctly, and remains useful when supplemental metadata is unavailable.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-013, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
