# MCP-003: Prove MCP cannot mutate through tools, auth, or transport bypasses

| Field | Value |
| --- | --- |
| Work package | `MCP-003` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [MCP-002](mcp-002-curated-read-only-tools.md) |
| Phase | 4 — Read-only MCP |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `MCP-003: prove mounted MCP authentication and read-only behavior` |

## Scope and acceptance

1. Test the mounted `/mcp` HTTP application through the parent FastAPI middleware/lifespan, not just direct tool calls. Cover supported streaming/session requests, missing/invalid credentials, cross-class credentials, replayed session identity, proxy-prefix/Host/Origin handling, malformed input, and shutdown during active reads.
2. Attempt writer command names and mutation-shaped arguments against every registered tool and any resource/prompt handlers. Assert the exact exposed registry, no hidden OpenAPI-generated write operations, no generic invocation capability, and no REST write access with an MCP bearer.
3. For each valid and invalid tool call, compare archive refs/manifests/content/catalogs/runs/transactions and API operation-state files before/after. Reads must create no reports, jobs, directories, locks, caches, or recovered artifacts; access logs are the documented exception. Inspect paths/content/modes rather than treating filesystem atime changes as application writes.
4. Exercise concurrent MCP reads during fake long REST sync/verification, large-page bounds, cancellation, and malformed upstream evidence. Verify no event-loop starvation, cross-request IDs, token leakage, or false verification confidence.

## Contracts, invariants, and ADRs

`INV-002`/`INV-003`/`INV-007`/`INV-010`, MCP allowlist/no-side-effect invariants; plan §§8, 12.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Add a threat/control/test traceability section to MCP/security docs and record residual deployment assumptions. Update any incorrect transport/client examples found by mounted-boundary tests.

## Validation

Planned checks, not execution evidence:

Mounted streaming transport integration, route/registry authorization matrix, filesystem and service-state snapshots, adversarial tool arguments, secret scans over logs/errors/responses, concurrent mixed-interface tests, disabled-mode regression, and `scripts/check.sh`.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Not started. The draft does not authorize implementation. Record actual changes,
resolved design issues, scope amendments, and any blocker/unblock condition here.
Operator-only deployment checks remain explicit handoff items, not asserted passes.

## Completion evidence

Not executed. On completion record the date; acceptance results; exact commands
and outcomes; invariant/ADR review and amendments; documentation changes; a link
to this package's completed [progress audit](../../progress.md); and any operator
handoff. Then set Status to `completed` in the same commit as the work.
