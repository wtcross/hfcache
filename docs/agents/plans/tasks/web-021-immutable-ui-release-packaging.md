# WEB-021: Integrate web assets and the host adapter into native/rootless releases

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P5 |
| Depends on | [WEB-020](web-020-cross-browser-accessibility-and-load.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-021: <completed outcome>` |

## Read before implementation

Existing build-container, native/container release installers/indexers and packaging templates; asset manifest contract; docs/containers.md and release workflow.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build a reproducible separately indexed UI artifact tied to source/UI schema/lock/toolchain/license identity. Extend clean release construction to require/verify this artifact, retain base uv build without Node, and stage immutable native assets or copy them into the rootless API image. Do not put frontend files in Caddy or add a Node service. Pin/bound startup asset verification and server web configuration; UI-disabled old deployment remains valid.

Update actual release artifact indexes, strict installer requirements, role/secret/socket definitions, service confinement and safe enablement examples for Basic hash and the narrow helper. Prove read-only policy-directory replacement visibility and that Caddy/worker cannot see helper/Basic secret. Keep existing Caddy instance/template routing/port/TLS and private-worker lifecycle. Packaging must not grant default host policies, unmask timers, enable UI implicitly in existing production, or pull images at runtime.

Build native and rootless artifacts from exact clean committed source using the established staged-build workflow. Keep dirty-fixture results distinguished. Validate fresh installation, enabled missing/mismatched UI refusal and backend-only installs, stable same-origin base/prefix and actual asset hashes. Any unavoidable runtime dependency/schema changes have reviewed ADR/index/lock updates.

## Unit and component validation

Test release manifest parsing, hashes/missing/extra assets, traversal/symlink input, enabled/disabled UI config, strict role metadata, safe help, no runtime Node and no secret/host socket added to wrong roles.

## Integration validation

Run base/server/server+MCP wheel installs without Node; stage verified UI artifact in native fixture and build rootless app image from pinned local inputs. Inspect installed bytes, permissions and role mount/secret separation; no dirty build masquerades as clean.

## Functional validation

Launch the actual staged native/rootless release behind the same Caddy fixture and repeat login/deep-link/asset/API/MCP/host-helper paths. Verify bad asset/index and missing hash provisioning fail visibly; no Vite dev server is present.

## Human documentation deliverables

Complete deployment.md for operator prerequisites, exact artifact selection, shared Caddy, Basic hash provisioning, native/rootless differences and no production effects. Update scripts, containers, server and release/install examples and license attribution.

## Acceptance

A complete immutable release carries matching SPA/backend/helper artifacts and runs with existing Caddy/no Node runtime; Python-only profiles remain supported; packaging preserves all role/policy safety boundaries.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-021, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
