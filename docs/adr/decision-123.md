# Keep public prefixes separate from native Unix REST paths

- Decision identity: 123.

- MCP transport amendment: [decision 124](decision-124.md).
- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-18.


## Context, decision and rationale

Public TCP requests retain configured prefix, verified TLS/proxy and Host/Origin
policy. Native unprefixed Unix requests require corroborated trusted ASGI transport
scope: missing peer alone is insufficient, and forwarded headers cannot manufacture
locality. Unix still requires the correct bearer and all resource limits.

One trusted projection chooses interface, effective root, auth/static body policy,
links and redirects, including prefixes colliding with /api/v1 or /mcp. Prefer a
configured-prefix interface spelling; permit native spelling only with corroborated
Unix scope. OpenAPI's cached public schema is never mutated per request; native
views/links preserve their own root. Reject arbitrary prefix stripping or trusting
caller headers, which could turn REST paths into MCP authority.

The optional MCP mount preserves this projection and its separate class. Its sole
slash alias is authenticated, relative and non-reflecting; REST slash redirects
stay disabled. Current curated tools are independently read-only. Installed TLS/
proxy/Unix acceptance remains profile-specific rather than implied by source tests.

## Relationships and technical evidence

- [decision 124](decision-124.md)
- [113](decision-113.md)
- [118](decision-118.md)
- [121](decision-121.md)
- [122](decision-122.md)
- [Server](../server.md)
- [API](../api.md)
- [client](../api-client.md)
- [security](../security.md)
- [invariants](../invariants.md)
- [trusted boundary/effective prefix](../../src/hfcache/api/app.py)
- [supported Uvicorn bootstrap](../../src/hfcache/server.py)
- [actual socket/schema/scope cases](../../tests/unit/test_rest_transport_gate.py)
- [complete paged reads](../../tests/unit/test_rest_pagination_gate.py)
- [independent route security inventory](../../tests/unit/test_rest_security_gate.py)
- [semantic parity manifest](../../tests/rest_parity.py)
- [static citation/parameter validation](../../tests/unit/test_rest_parity_gate.py)
- [strict examples/docs/cold-disabled process](../../tests/unit/test_rest_examples_gate.py)
- [MCP](../mcp.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
