# API-011: Build the typed API client and reader-only configuration

| Field | Value |
| --- | --- |
| Work package | `API-011` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-010](api-010-guarded-maintenance-api.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-011: add typed API client and reader configuration` |

## Scope and acceptance

1. Implement a typed synchronous client appropriate for Typer, with explicit HTTP/Unix-socket transport, connect/read timeouts, streaming, response/envelope validation, page iteration, server capability negotiation, and optional expected archive UUID. Keep it independent of ApplicationConfig, archive filesystem paths, and server/MCP imports.
2. Add strict client TOML and `--client-config`, `--api-url`, `--api-socket`, `--api-token-file` selection using plan §7 precedence. Resolve only the named API credential. Preserve local help/version and handle missing writer config on reader hosts without trying to load it.
3. Verify TLS; reject token-bearing URLs/userinfo and cross-origin redirect credential forwarding. Disable ambient proxy/credential behavior by default. Distinguish protocol/auth/config failures from absent API or uncertain execution using the new documented HFAPI codes.
4. Generate mutation idempotency keys before transmission and retain them across permitted retries. Support an explicit key for a deliberate retry and expose authenticated lookup without resubmission. Poll/read retries are bounded; a lost response never triggers a new-key mutation replay. Validate API/envelope versions and unknown server capabilities rather than guessing.

## Contracts, invariants, and ADRs

`INV-001`–`INV-003`, `INV-006`, `INV-008`; plan §§3–5, 7.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Create `docs/api-client.md` with reader and writer setup, endpoint/credential precedence, TLS/CA behavior, compatibility/version errors, retry rules, and troubleshooting. Update configuration, README, and CLI global-option contracts.

## Validation

Planned checks, not execution evidence:

Mock transport plus real temp Unix/TCP server tests; reader without /etc archive config/mount/Hub credential; auth failures, TLS/redirect policy, truncated or malformed JSON, unsupported versions, pagination completeness, uncertain POST retry identity, and base-wheel import smoke. Run `scripts/check.sh`.

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
