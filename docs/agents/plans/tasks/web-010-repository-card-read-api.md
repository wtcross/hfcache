# WEB-010: Expose a bounded exact-publication card read

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P2 |
| Depends on | [WEB-009](web-009-repository-card-capture.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-010: <completed outcome>` |

## Read before implementation

API metadata leases and identity checks; card model/layout; generated wire schemas; exact publication routes and API contract.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement only the narrow exact SHA/publication card GET. Validate all identity segments and authoritative retained publication membership before returning a card adjunct. No current fallback on missing/pruned/repaired identity, no arbitrary file/URL, no payload open, lock, network, credential resolution, write or refresh from GET.

Return independently versioned card states, bounded sanitized Markdown/source provenance, capture time/presentation version and diagnostics. Missing capture/README are explicit normal states; malformed schema/identity or exhausted budgets are classified failures, not empty success. Preserve metadata pool/lease lifetime through encoding/stream completion and disconnect. Enforce JSON encoding/response maximum before headers and no-store/nosniff/authentication. Add precise schema registry and runtime decoder coverage; source view exposes only the sanitized derivative.

## Unit and component validation

Test identity/type/path grammar, missing/invalid/corrupt adjuncts, retained versus vanished membership, state serialization, byte bounds, redaction and decoder unknown versions.

## Integration validation

Exercise real authenticated GET with REST reader/writer/Basic and denied MCP credentials. Instrument filesystem/network/locks to prove the read touches only allowed metadata and remains bounded under slow clients and disconnect.

## Functional validation

Through Caddy load exact card data for model/dataset and all unavailable states, switch current/repair/prune fixtures mid-observation and prove no silent fallback or mixed publication content.

## Human documentation deliverables

Update API matrix and schema with mode/authority/effects/status/bounds, plus human guide explanations of not captured, missing README, unsafe/oversized card and vanished publication.

## Acceptance

An authenticated browser can obtain only the bounded sanitized card for the requested retained publication, without changing archive state or reaching the Hub; all unavailable/error cases are distinguishable.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-010, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
