# Typed services and maintained transport implementations

- Decision identity: 108.

- MCP transport amendment: [decision 124](decision-124.md).
- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.


## Context, decision and rationale

Authenticated REST and optional read-only MCP need maintained HTTP/TLS/ASGI and
protocol implementations while archive algorithms remain ordinary typed services.
Use HTTPX/HTTPCore in the base client, FastAPI/Uvicorn in the server extra, and
standalone FastMCP in the separate MCP extra. Readers do not import optional server
frameworks. Their material protocol/lifecycle/resource-safety benefits justify the
narrow FW-03/FW-04 exceptions; handwritten framing or CLI subprocess adapters would
add security and correctness risk without new domain authority.

Queries and guarded commands remain transport-neutral. Adapters never invoke
Typer callbacks, parse CLI stdout or duplicate domain engines. The bounded lane
and private verifier preserve the local flock; optional MCP delegates exactly
nine typed reads and adds no execution capability. No workflow engine, broker,
database, scheduler or journal-driven normal execution is introduced.

## Relationships and technical evidence

- [decision 124](decision-124.md)
- [decision 112](decision-112.md)
- [decision 119](decision-119.md)
- [FW-01–FW-04](fw-01.md)
- [API contract](../api.md)
- [server contract](../server.md)
- [Decision 116](decision-116.md)
- [Decision 118](decision-118.md)
- [MCP](../mcp.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
