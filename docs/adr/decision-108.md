# Decision 108 — Typed services and maintained transport implementations

- Status: Accepted target contract; enforcement lands incrementally.
- Date: 2026-10-17.
- Work package: API-001, this commit.
- Source: [progress decision 108](../progress.md),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-001-contract-and-activation.md).

## Context and decision

Remote management requires authenticated HTTP, preserved CLI results, and later
read-only MCP. Extract transport-neutral typed queries and guarded commands;
keep archive algorithms and their local flock authoritative. Adapters may not
invoke CLI callbacks, spawn the CLI, or parse stdout. CLI becomes a typed client.

Authorize incremental dependencies: directly used `httpx` in base for verified
TLS, Unix HTTP, bounded transport timeouts, streaming and redirect control;
FastAPI and Uvicorn in `server` for ASGI lifecycle, HTTP parsing, validation and
bearer integration; standalone `fastmcp` in `mcp` only after REST acceptance for
the actual streaming/session protocol and token-verifier extension. Resolve
Python 3.14 compatibility and consult official docs when adding each dependency.
No dependency is added by API-001 itself.

## Rationale and alternatives

Handwritten HTTP/TLS/streaming and MCP protocol implementations would introduce
security and correctness risks the standard library alone does not address.
Transport frameworks supply protocol correctness; they do not own domain
orchestration. Reject direct endpoint calls to Typer, duplicate domain engines,
CLI subprocess wrappers, and early MCP inclusion. Readers need the base client
without importing optional server modules.

## Consequences and relationships

Amends [FW-01–FW-04](fw-01.md)'s closed list only for these scoped additions.
No workflow framework, new archive database, scheduler, or storage authority.
[API contract](../api.md) records complete parity and capability requirements;
[server contract](../server.md) records the planned isolated verifier. AD-17,
AD-21, FS/TX, output and consumer contracts remain authoritative. API-002 fixes
the existing unmanaged status/list selector mismatch with the CLI contract.
Tests and locked versions are evidence of the implementing packages, not a
claim of an installed server here.
