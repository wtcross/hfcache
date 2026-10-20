# WEB-004: Add one Basic administrator through a replaceable principal boundary

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-003](web-003-typed-wire-contracts.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-004: <completed outcome>` |

## Read before implementation

api/auth.py, api/app.py outer middleware, server_config.py, server credential delivery; architecture security section and api-contracts.md; auth and CSRF acceptance rows.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement the configured single human identity and protected Argon2id hash/provider in the optional server closure. Keep stable subject/authentication-method metadata separate from legacy wire credential classes. Preserve REST bearer writer/reader and MCP bearer-only separation. Keep new administrative permission policy internal or in the independent UI/host projection; do not append unknown capability strings to the existing strict response.

Extend outer pre-routing authentication, body/capability checks and error/challenge handling, not only a route-level FastAPI dependency. Implement bounded credential parsing, verification concurrency, failed-attempt throttling, startup hash source validation and protected file/named credential delivery. No raw password in arguments, storage, logs, traces, fixtures or browser code. Do not accumulate attacker-supplied failed passwords in a global secret-redaction registry; scrub Authorization independently.

Require exact same-origin, JSON and a non-simple header for unsafe Basic browser calls; reject missing/null/foreign origins. Retain no-Origin nonbrowser bearer clients. Explicitly gate new admin capabilities separately from old writer capability; host proof integrates in WEB-006. Authentication failure must not invoke body parsing, domain work or credential-source fallback. Define native browser challenge and truthful logout limitations.

## Unit and component validation

Test wrong user/password equivalence, malformed/duplicate/oversized headers, corrupted/symlinked/hash sources, password-hash resource ceilings, credential class matrix, admin denial, CSRF media/header/origin cases, and unconditional credential redaction.

## Integration validation

Exercise real middleware on HTTP and Unix sockets with each credential class, both methods/prefix modes, errors/unknown routes/schema and MCP. Test concurrent bad-password requests while original operation reads remain bounded/available.

## Functional validation

Add real browser Basic challenge and authorized same-origin fetch tests, with no injected per-request Authorization shortcut for the positive browser flow. Exercise foreign-origin form/fetch refusal through an owned real origin; complete Caddy-specific proof in WEB-005.

## Human documentation deliverables

Create human deployment/login/security/troubleshooting sections with protected password provisioning, rotation effects, TLS requirement, single whole-archive account and no reliable app logout. Update server examples/strict schemas and security ADRs.

## Acceptance

One configured Basic administrator works without exposing a bearer; existing CLI/MCP authentication remains compatible; server-side admin/CSRF policies are enforced; missing or unsafe credential sources fail closed.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-004, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
