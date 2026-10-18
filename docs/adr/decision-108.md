# Decision 108 — Typed services and maintained transport implementations

- MCP transport amendment: [decision 124](decision-124.md).
- Status: Accepted target contract; dependency/configuration/authentication enforcement advanced by [decision 112](decision-112.md), with reader/candidate integration and explicit HTTPCore use amended by [decision 119](decision-119.md).
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

## API-005 implementation (2026-10-17)

[Decision 112](decision-112.md) records the Python 3.14 locked dependency set,
strict separate server configuration, restart-only auth/transport authority,
fresh archive-policy snapshots and fixed verified bearer capabilities. HTTPX is
now a direct base dependency and FastAPI/Uvicorn are in the `server` extra;
the gate installs that extra and base imports remain independent. No REST route,
listener or MCP implementation is claimed by these primitives. The original
domain-service and framework exclusions remain authoritative.

## API-009 command transport (2026-10-17)

[Decision 116](decision-116.md) exposes typed sync/verification/planning/
diagnostic/installed-validation routes through the shared services and bounded
lane. Durable 202 admission is separate from exact terminal domain Envelopes.
Semantic read jobs retain explicit Hub/resource effects; writer probes and
private verification retain their existing ownership. Candidate hooks cannot
select server files or redirect credential authority. No CLI subprocess, duplicate
domain algorithm, dependency, archive format or MCP implementation is added.

## API-011 client implementation (2026-10-17)

[Decision 118](decision-118.md) implements the independent synchronous base client
and separate strict reader configuration using the already locked HTTPX transport.
Typed safe response/identity/version validation and finite observation retain
original keys on submission uncertainty. No archive policy, optional server/MCP
framework, ambient credential/proxy, local fallback or daemon-start authority is
introduced. Global endpoint/source options are stored; operational CLI migration
remains API-012/013. No additional dependency is required.

## API-012 reader and Unix transport implementation (2026-10-18)

[Decision 119](decision-119.md) migrates actual reader/candidate CLI modes and
promotes already-locked HTTPCore 1.0.9 to an explicit base dependency for a public
Unix-only HTTPX adapter. Socket ownership fixes observed failed-connect leakage,
while HTTPCore retains HTTP parsing/pooling and TCP/TLS stays on HTTPX. No package
or version upgrade, private pool mutation, global patch, IP fallback or warning
suppression is introduced. The exact server/domain authority and remaining
framework/MCP exclusions stand.

## 2026-10-18 optional MCP transport amendment (MCP-001)

[Decision 124](decision-124.md) activates the separately optional standalone
FastMCP transport after committed API-016 acceptance. Supported production token
verification delegates only to the active protected MCP-reader slot; disabled
mode imports/resolves neither its package nor credential. One composed lifespan
retains REST startup/ownership and closes MCP before REST drain/release. Existing
Host/Origin/TLS/proxy/corroborated native-prefix policy and class separation remain.
This package adds transport only, with no OpenAPI conversion or tools/resources/
prompts; curated reads and side-effect proof remain MCP-002. No archive/config/
durable format, domain workflow, production deployment or host-proof change.
See [MCP](../mcp.md) for exact supported protocol/path/session behavior and the
[MCP-001 task](../plans/tasks/mcp-001-mount-authenticated-fastmcp.md) for evidence.
