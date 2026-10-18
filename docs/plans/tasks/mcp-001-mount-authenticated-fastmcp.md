# MCP-001: Mount optional authenticated FastMCP after REST acceptance

| Field | Value |
| --- | --- |
| Work package | `MCP-001` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-016](api-016-rest-acceptance-gate.md) |
| Phase | 4 — Read-only MCP |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `MCP-001: mount optional authenticated FastMCP transport` |

## Scope and acceptance

1. Confirm API-016 is completed with actual evidence before adding any MCP code or runtime dependency. Resolve standalone FastMCP for Python 3.14, record its material dependency decision, add the `mcp` extra, update lock/gate/wheel coverage, and preserve base/REST-only installs.
2. Add an optional server setting and mount FastMCP Streamable HTTP at `/mcp` in the same FastAPI process. Compose REST and MCP lifespans in the verified startup/shutdown order; no second Uvicorn process or nested event loop. Disabled MCP must require neither its credential nor importable package.
3. Implement a production token-verifier adapter over shared protected opaque-token validation, restricted to the distinct MCP reader credential. Missing credential when enabled fails closed; REST writer/read tokens do not grant MCP access and MCP credentials never grant REST write access.
4. Verify actual mounted-path auth/session behavior, supported Host/Origin controls, and path-prefix handling using the locked version. Document static bearer as a pre-provisioned internal-client model, not OAuth discovery. Do not use development-only StaticTokenVerifier in production.

## Contracts, invariants, and ADRs

`FW-03`/`FW-04`, `AD-21`, `INV-002`/`INV-003`, new MCP exposure invariants; plan §8.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Create `docs/mcp.md` for enablement, credential boundary, transport/path/lifespan, and client limitations. Update server/security/configuration docs, dependency ADR/index, README extras, and Unreleased notes as functionality lands.

## Validation

Planned checks, not execution evidence:

REST suite with MCP absent/disabled/enabled; combined lifespan order and teardown; mounted HTTP handshake with valid/missing/wrong-role bearer; session identity/path-prefix behavior; extra-specific wheel tests and import isolation. Use an actual streaming-capable HTTP test transport. Run `scripts/check.sh`.

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
