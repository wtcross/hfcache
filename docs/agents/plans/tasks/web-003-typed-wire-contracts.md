# WEB-003: Make the browser wire boundary precisely typed and validated

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P0 |
| Depends on | [WEB-002](web-002-strict-frontend-and-gates.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-003: <completed outcome>` |

## Read before implementation

src/hfcache/api/models.py, app.py, catalog.py; domain/catalog payload models; current OpenAPI and ReadResponse contracts; web workspace.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Define the typed response/payload registry needed by each UI route. Resolve generic Envelope data and x-catalog-payload schemas without changing stable ReadResponse/capabilities/operation wire shapes unnecessarily. Generate types/runtime schemas mechanically from authoritative models, with independent expected fixtures and checked regeneration drift. Add runtime decoders from unknown, discriminated state models, safe large-integer handling, limits and domain-error preservation. Typed ApiProblem handling must distinguish transport errors from failed domain Envelopes.

Build a same-origin REST client with explicit read versus mutation paths, no automatic mutation retry, bounded read body collection, AbortSignal, validated relative links, and consistent request metadata. Query keys include auth/authority/archive and exact publication identity. Do not cache passwords or expose generic arbitrary-target fetch. Define typed contracts for forthcoming config/card/host payloads only after WEB-001's contract decision; never pretend unimplemented endpoints return data.

## Unit and component validation

Golden tests cover valid and malformed wrappers, unknown schema, missing fields, false/zero/null distinctions, extra forbidden keys, failed HTTP-200 Envelopes, UTF-8 and large integers. Exhaustively test client URL/path construction and no mutation retry.

## Integration validation

Round-trip actual Python-serialized schemas through TS validators. Call real baseline REST routes with the client on an owned ASGI/HTTP fixture. Prove schema regeneration drift and independent incorrect wire fixtures fail.

## Functional validation

Mount a real React status/read view against the owned real API and verify failed/unknown payload presentation. This may use temporary shell routing until WEB-005; report that limitation.

## Human documentation deliverables

Update API/schema and development references for generated contracts, error taxonomy and bounds; update troubleshooting language for unavailable versus failed reads. Do not expose internal type-generation steps as user workflow.

## Acceptance

No UI route relies on a free-form any Envelope or blind cast; actual backend payloads validate; error and integer handling are tested; old wire schemas and base client behavior remain compatible.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-003, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
