# API-005: Add server dependencies, strict configuration, and bearer capabilities

| Field | Value |
| --- | --- |
| Work package | `API-005` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-004](api-004-isolate-execution-context.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-005: add strict server configuration and bearer capabilities` |

## Scope and acceptance

1. Add the recorded HTTP-client dependency and FastAPI/Uvicorn `server` extra with compatible Python 3.14 versions; update the lock and gate provisioning. Do not add FastMCP yet. Reader imports must not require server packages.
2. Introduce versioned immutable ServerConfig independent of archive TOML. Define private socket/loopback/TLS policy, credential sources, limits, maintenance flag, server startup settings, and reload boundaries. Unknown keys/coercion/invalid paths are rejected without exposing input secrets.
3. Implement distinct REST writer/reader credential validation, using explicit files/systemd credentials, bounded input and constant-time comparisons. Missing writer credentials fail startup; optional unprovisioned reader capability is disabled. Reject ambiguous duplicate secrets. No Hub token reuse or ambient credential lookup.
4. Implement reusable authenticated-principal/capability checks with stable 401 challenge and 403 responses. Register redaction for opaque tokens and test config fingerprints/receipts never contain their values. MCP credential support is a future interface, not an active endpoint.

## Contracts, invariants, and ADRs

`FW-03`/`FW-04`, `AD-21`, `INV-001`–`INV-003`, `INV-010`; plan §3.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Create concrete `docs/server.md` config/auth sections and server config examples. Update configuration/security contracts, FW dependency decision and index, API authentication matrix, README writer installation, and Unreleased changelog.

## Validation

Planned checks, not execution evidence:

Config and credential validation/property tests, token-class matrix, empty/wrong/malformed bearer, invalid file modes/types/symlinks, missing credentials, opaque-token redaction, and Python 3.14 lock/install tests. Ensure base CLI help/version imports without the server extra. Run the gate with the server extra installed.

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
