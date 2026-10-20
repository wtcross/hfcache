# WEB-017: Implement guarded maintenance and integrity remediation

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-016](web-016-operations-and-reports-ui.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-017: <completed outcome>` |

## Read before implementation

Existing maintenance routes/services; retention/recovery/repair docs; exact publication findings; operation controller and fixture failure matrix.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build dedicated flows for prune, unmanaged purge, recovery, quarantine cleanup and repair from exact findings. Reuse existing preview/apply endpoints and typed scopes; review selected identities/reasons/retention effects and demand explicit confirmation. Server re-evaluates scope/authority under its existing locks. Keep current protected, configured repositories ineligible for purge, quarantine IDs explicit, and repair same-SHA replacement evidence intact.

Render preview refusals/partial outcomes and transaction diagnostics, never turn a preview handle or plan body into deletion authority. Removing config and applying prune/purge remain separate decisions. Explain one-round pruning and over-retention safety. On integrity or unknown recovery states stop and present evidence/runbook paths. No automatic repair/recover/prune/cleanup, arbitrary file selections or archive initialization control.

Connect resulting receipts/events/reports to shared original-operation controller, preserve uncertainty on disconnect and safe handoff of exact keys/IDs. UI confirmations are useful intent but never replace backend proof.

## Unit and component validation

Test maintenance request builders, eligibility checks, exact revision grammar, confirmation content, refusal states, warnings/partial/integrity priorities and no implicit mutation from read/preview.

## Integration validation

Execute real domain fixtures for each preview/apply, changed scope between steps, common-lock contention, protected current, managed purge denial, ambiguous journal preservation and repaired publication identity. Retain existing crash injection regressions.

## Functional validation

Through Caddy browser flows perform safe prune/purge/quarantine/repair/recovery on tiny owned fixtures, verify exact on-disk outcomes/audits and preserved unknown evidence, and lose an apply response without replay. No production/NAS data is involved.

## Human documentation deliverables

Create maintenance.md with prerequisites, effects, confirmations, safe stop conditions and links to existing recovery/operations contracts. Use only clearly labelled fixture examples; update relevant error help.

## Acceptance

Every existing maintenance capability is available with truthful previews and strict backend authority; destructive or ambiguous cases cannot bypass safeguards through the UI.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-017, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
