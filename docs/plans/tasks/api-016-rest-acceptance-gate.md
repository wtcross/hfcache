# API-016: Prove complete REST and CLI parity before beginning MCP

| Field | Value |
| --- | --- |
| Work package | `API-016` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-015](api-015-cockpit-api-client-compatibility.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-016: pass REST parity security and client acceptance gate` |

## Scope and acceptance

1. Audit every baseline command/mode against the API/service/role/effect/test matrix. Close missing routes, invalid-mode checks, selector coverage, legacy output mismatches, and candidate/systemd/Cockpit integration gaps with fresh task splits if needed; do not declare parity based only on sync/status tests.
2. Add/review a full adversarial suite covering credentials on every endpoint, read/write capability separation, traversal and unauthorized authority selection, stale destructive scopes, verification persistence races, queue saturation, API responsiveness, idempotency/crash boundaries, restart/no-replay, and client disconnect behavior.
3. Prove ordinary reader execution without archive config/mount/Hub token, writer-local Unix transport, base/server wheel isolation, large result streaming/page completeness, and stable API/envelope negotiation. Check legacy failure aggregation and report identity. No FastMCP dependency/import/route may yet be required.
4. Validate all current REST/server/client examples, OpenAPI determinism, documentation links, contracts, invariants, and ADR amendments. Separate implemented/tested repository behavior from pending operator installation/hardening/NFS acceptance. Record a deployment hold for any unperformed required host check.

## Contracts, invariants, and ADRs

All affected register sections; `INV-010`/`INV-011`; plan §12 REST gate.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Complete REST/CLI/server/consumer migration documentation and the traceability matrix. Record gate evidence in this task and progress. Update current selector to MCP-001 only after this package passes.

## Validation

Planned checks, not execution evidence:

`scripts/check.sh --with-build` with implemented server extras, complete Cockpit gate, full default Python suite, real throwaway Unix/TCP transport integration, documented compatibility drill, and docs/OpenAPI/example checks. Record actual versions/counts/outputs and any operator-only pending checks; no inherited prior test counts.

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
