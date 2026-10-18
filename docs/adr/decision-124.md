# Add an optional authenticated MCP transport after REST acceptance

- Decision identity: 124.

- Curated tool amendment: [decision 125](decision-125.md).
- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-18.


## Context, decision and rationale

Use optional standalone FastMCP in the server+MCP profile for maintained
Streamable HTTP, finite JSON responses, supported token-verifier extension and
explicit composed ASGI lifespan. Base/REST-only installations remain independent;
disabled mode imports neither package nor source and mounts no endpoint. Enabling
requires the optional package and distinct protected MCP-reader source at startup;
rotation requires drain/restart and client reread.

The outer boundary and production opaque-token verifier authenticate every method
before body/protocol handling. No session identifier grants authority. Canonical
/mcp/ and its authenticated relative slash alias preserve public/native projection,
Host/Origin/TLS/proxy and strict JSON/query/body policy. Stateless operation retains
no SSE/resumption/session execution history, OAuth discovery/login/issuance,
resources/prompts or background jobs. Buffer/sanitize/bound finite replies before
headers; separate inflight capacity and shared metadata leases remain bounded.
SDK diagnostics preserve safe correlation/provenance without evaluating rejected
messages/exceptions or echoing raw inputs.

The transport delegates nine explicit typed reads through the separate curated
registry; it does not convert REST OpenAPI into tools or expose writable dispatch.
Upstream SDK features confer no hfcache authority. Handwritten protocol/session
machinery and development static token verifiers were rejected. Dependency/parser/
privileged-host compromise remains outside this narrow application capability;
fixture results do not certify installed isolation or NAS workloads.

## Relationships and technical evidence

- [decision 125](decision-125.md)
- [64](decision-064.md)
- [108](decision-108.md)
- [112](decision-112.md)
- [113](decision-113.md)
- [123](decision-123.md)
- [FW-01–04](fw-01.md)
- [AD-21](ad-21.md)
- [MCP](../mcp.md)
- [server](../server.md)
- [API](../api.md)
- [security](../security.md)
- [invariants](../invariants.md)
- [optional MCP module](../../src/hfcache/mcp.py)
- [application projection/lifecycle](../../src/hfcache/api/app.py)
- [active credential loader](../../src/hfcache/api/auth.py)
- [closed event vocabulary](../../src/hfcache/logging.py)
- [transport/verifier cases](../../tests/unit/test_mcp_transport.py)
- [mounted streaming/security cases](../../tests/unit/test_mcp_mount.py)
- [threat/control/test evidence](../mcp.md#read-only-boundary)
- [protected-file example](../../examples/mcp-client.py)
- [MCP setup/session/rotation guide](../mcp.md#connect)
- [cost/refusal guidance](../mcp.md#resource-costs-and-troubleshooting)
- [acceptance tests](../../tests/unit/test_mcp_acceptance.py)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).

- [FastMCP 4.1.1 release metadata](https://pypi.org/pypi/fastmcp/4.1.1/json)

- [Mounted FastAPI applications and composed lifespans](https://gofastmcp.com/integrations/fastapi)

- [Token-verifier extension](https://gofastmcp.com/servers/auth/token-verification)

- [supported auth classes](https://gofastmcp.com/python-sdk/fastmcp-server-auth-auth)

- [HTTP transport, sessions and Host/Origin protection](https://gofastmcp.com/deployment/http)
