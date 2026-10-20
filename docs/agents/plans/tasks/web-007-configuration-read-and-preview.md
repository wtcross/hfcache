# WEB-007: Expose safe installed configuration and exact managed-edit validation/preview

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-006](web-006-guarded-host-adapter.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-007: <completed outcome>` |

## Read before implementation

config models/candidate assessment; existing POST config validate/plans DTOs and renderer; Cockpit candidate guard/read pipeline; config API specification.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement GET /config with nonsecret editable projection, protected-field descriptions and opaque full-byte base revision. Never publish a secret-bearing raw hash or sanitized placeholder document that can overwrite real configuration. Keep reads read-only even when candidate/lock files are absent. Define a strict typed managed-edit representation that can add/update/remove model/dataset entries and supported nonsecret global fields; preserve hidden/protected fields server-side and tag-only identity.

Extend existing validation and planning requests with the exclusive managed-edit form, retaining installed/literal candidate request and response compatibility. Reconstruct exact candidate bytes through one backend service and include versioned assessment/preview identity needed for application. Bound edits, strings and serialization before allocation. Reject authority-changing edits that cannot be safely installed under startup-pinned root/UUID/Hub/credential authority. No browser path/token/source override.

Plan/validate are never installation. Snapshot under the existing config guard where needed, release locks before Hub preview, and later compare exact base identity. Preserve domain warning/error results and compatible-authority distinctions. Define serialization behavior and comments/formatting expectations; use a justified maintained TOML writer/round-trip library if needed rather than regex rewrites.

## Unit and component validation

Test field constraints, normalization, tag-only base changes, opaque-token scope, hidden-field preservation, malformed/coercive/mixed bodies, deterministic exact reconstruction, unsupported authority changes and secret-safe output.

## Integration validation

Call real config read/validate/plan through API/helper with installed and candidate fixtures. Race two readers/editors and change base bytes without changing policy fingerprint; verify stale refusal. Test CLI literal candidate behavior remains unchanged.

## Functional validation

Through Caddy, read config, submit valid/invalid/tag-only candidates and sizing previews, observe exact classified results and protected fields. Lost preview observation retains original operation identity and does not install anything.

## Human documentation deliverables

Start configuration-and-tags guide with projection/advanced-view limits, normalization, validation versus preview, conflict handling and authority-changing manual procedure. Update API/config/server schema and examples.

## Acceptance

The UI has a safe complete editable source with full-byte concurrency protection; existing candidate clients work; preview is exact and non-installing; protected authority and secrets cannot be changed via redacted fields.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-007, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
