# WEB-005: Serve authenticated assets through the existing Caddy and build the real functional harness

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-004](web-004-basic-auth-and-permissions.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-005: <completed outcome>` |

## Read before implementation

packaging/containers/Caddyfile.in and server.toml.in; app lifespan/outer middleware; architecture deployment/static root; existing test socket/lifespan fixtures.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement optional app-owned UI static serving from an explicitly configured immutable asset root and independently versioned bootstrap context. Expose P/ui/ navigation/assets and preserve P/api/v1 and P/mcp under the same Caddy instance and existing Unix upstream. Retain Caddy TLS/auth-header/streaming/no-admin/no-ACME/no-archive boundaries. Do not add global Caddy Basic or another frontend server.

Validate asset manifest/paths/bounds/identity and isolate UI history fallback from missing assets, API/MCP routes and non-GET methods. Preserve native Unix prefix behavior. Implement safe base path/runtime bootstrap and strict headers/cache policies without inline script or externally loaded assets. UI-disabled deployments remain compatible; enabled missing assets produce explicit startup refusal. Query a safe UI contract/build identity without changing /capabilities.

Introduce the provider-neutral real functional runner and --with-web-functional gate scaffold with application/platform profiles. It owns test Caddy, CA, browsers, API, fixture state and finite cleanup. No test shortcut disables TLS or production guards. Early suite runs the completed routing/auth cases and clearly reports later feature cases as pending; final strict acceptance will require all cases.

## Unit and component validation

Test route classification/fallback, MIME allowlist, asset traversal/symlink/unknown manifest, startup enablement, bootstrap escaping, paths/prefixes, security headers and script runner unsafe workspace/prerequisite refusals.

## Integration validation

Run real Caddy TLS -> API Unix routing plus concurrent lifespan/prefix requests. Confirm one app registry/pool/worker relationship, unchanged bearer REST/MCP endpoints, and bounded static serving on disconnect.

## Functional validation

Run Chromium/Firefox/WebKit login, deep-link refresh, root/nonroot prefix, missing JS 404, API typo and MCP errors never HTML, rejected plaintext/untrusted certificates, and REST/MCP bearer calls on the same Caddy origin while a Basic browser is active. Inspect browser network to prove no CDN/other origin dependency.

## Human documentation deliverables

Write user entrypoint/navigation and operator shared-Caddy deployment/prefix sections. Update containers/server/API security boundaries and development/script references. Document exact unavailable/missing-assets messages.

## Acceptance

A built authenticated SPA works through the existing Caddy topology with real trusted test TLS and no bearer regressions; route/security tests pass in three engines; the reusable functional harness is fail-closed.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-005, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
