# Serve bounded metadata through one authenticated lifespan

- Decision identity: 113.

- MCP transport amendment: [decision 124](decision-124.md).
- Curated tool amendment: [decision 125](decision-125.md).
- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.
Native Unix/public-prefix routing is amended by [decision 123](decision-123.md).


## Context, decision and rationale

One application/lifespan owns authenticated Unix/TCP listeners, startup policy,
registry/logging, daemon-instance lock and a bounded shared metadata pool. Import
and factory construction perform no listen, Hub, initialization or archive mutation.
The daemon lock is distinct from operation-store and archive locks. Metadata reads
use fresh pinned policy and contained no-follow authoritative readers, never Typer,
Hub credential construction or catalog reconstruction. Health is not integrity
proof or permission to initialize.

Authenticate every route/error/health/schema/docs surface before body/routing.
Enforce Host/Origin/proxy/prefix, strict bounded bodies and sanitized wire errors.
Pages are deterministic and cursor-bound; byte/scan/artifact/aggregate exhaustion
is explicit failure. Public CLI uses bounded HTTP too. Worker leases cover actual
read and response/stream completion even after observer cancellation, preserving
capacity/drain ownership. Foreground and strict native activation share one server;
selected rootless listener creation/readiness is a separate deployment profile.

Handwritten protocol stacks, blocking event-loop scans, unbounded collections and
using a catalog as authority were rejected. Optional MCP shares lifespan/pool and
retains the same transport trust boundary with its separate read-only capability.

## Relationships and technical evidence

- [decision 124](decision-124.md)
- [decision 125](decision-125.md)
- [decision 123](decision-123.md)
- [CLI taxonomy](../cli.md#5-error-and-warning-taxonomy)
- [decision 108](decision-108.md)
- [decision 112](decision-112.md)
- [decision 111](decision-111.md)
- [API contract](../api.md)
- [server contract](../server.md)
- [read app/boundary](../../src/hfcache/api/app.py)
- [wire models](../../src/hfcache/api/models.py)
- [pool and instance lock](../../src/hfcache/api/lifecycle.py)
- [no-follow metadata/budgets](../../src/hfcache/metadata.py)
- [shared queries](../../src/hfcache/services/queries.py)
- [listener bootstrap](../../src/hfcache/server.py)
- [wire/read/lifespan tests](../../tests/unit/test_api_reads.py)
- [adversarial HTTP cases](../../tests/unit/test_api_adversarial.py)
- [shared query containment](../../tests/unit/test_query_boundary.py)
- [ephemeral Unix/TCP/TLS tests](../../tests/unit/test_server_bootstrap.py)
- [MCP](../mcp.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
