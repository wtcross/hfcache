# Keep public prefixes separate from native Unix REST paths

- Decision identity: 123.
- Asset/bootstrap refinement: [decision147](decision-147.md).

- MCP transport amendment: [decision 124](decision-124.md).
- Status: Amended; current scope includes the amendments referenced below.
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

Deployment prerequisites are defined in the
[deployment guide](../deployment-centos-stream-10.md).

## Replacement UI design amendment (2026-10-20)

[Decision 140](decision-140.md) amends this record for the accepted
replacement design. Accepted UI prefix design extends future recognized paths without trusting forwarded headers or weakening corroborated native Unix exceptions; current REST/MCP behavior remains implemented authority.

## Authenticated asset and bootstrap amendment (2026-10-20)

[Decision147](decision-147.md) amends this record. This refinement extends the single trusted projection to /ui while preserving the corroborated native Unix exception. It explicitly rejects a configured leading double slash and URI-encodes Location using UTF-8 while retaining raw JSON operation links and original handles. Ordinary supported ASCII/native CLI behavior is byte-identical; new UI origin/prefix byte limits apply only when UI is enabled.
