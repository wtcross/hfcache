# MCP-004: Complete MCP client guidance and the read-only acceptance gate

| Field | Value |
| --- | --- |
| Work package | `MCP-004` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [MCP-003](mcp-003-mcp-security-and-side-effect-tests.md) |
| Phase | 4 — Read-only MCP |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `MCP-004: document MCP clients and pass read-only acceptance` |

## Scope and acceptance

1. Provide a tested example client/setup using the locked FastMCP version and a protected credential file or explicitly supported secret mechanism. Do not put a real/static sample bearer in committed JSON, command arguments, URLs, or browser storage. Explain token acquisition is operator provisioning, not OAuth discovery.
2. Finish tool/reference documentation, expected resource costs and response limits, private/gated whole-archive trust boundary, exact publication locators, version/session compatibility, rotation/reconnect, disabled behavior, and troubleshooting.
3. Validate server packaging with REST alone and REST+MCP, ensuring optional MCP cannot alter REST auth/lifecycle or give the verification executor any credential. Keep worker egress and systemd timer policies intact.
4. Run the full MCP gate and REST regressions. Record actual mounted-HTTP evidence and remaining operator-only TLS/firewall/hardening checks, rather than suggesting unit tests proved host security. Fix in-scope issues in fresh coherent packages if necessary before marking complete.

## Contracts, invariants, and ADRs

All MCP/interface security invariants and `INV-010`/`INV-011`; plan §12 MCP gate.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Complete MCP, server, API-client/consumer cross-references, README, CHANGELOG, security/invariants, relevant ADR index/statuses, and agent context routing. Add no unrelated backlog to the plan.

## Validation

Planned checks, not execution evidence:

Complete registered-tool and mounted HTTP suites, example execution against a throwaway server, all-extra lock/install/import checks, REST disabled/enabled regressions, docs/schema/link validation, and `scripts/check.sh --with-build` including Cockpit.

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
