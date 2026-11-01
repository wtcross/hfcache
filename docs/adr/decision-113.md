# Serve bounded metadata through one authenticated lifespan

- Decision identity: 113.
- Asset/bootstrap refinement: [decision147](decision-147.md).

- MCP transport amendment: [decision 124](decision-124.md).
- Curated tool amendment: [decision 125](decision-125.md).
- Independent bounded Basic verification: [decision146](decision-146.md).
- Foreground default-SIGTERM cleanup ordering: [decision149](decision-149.md).
- Fresh-byte parser memoization: [decision157](decision-157.md).
- Status: Amended; current scope includes the amendments referenced below.
- Replacement design: see the 2026-10-20 amendment below; executable conformance remains pending.
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

## Replacement UI design amendment (2026-10-20)

[Decision 140](decision-140.md) amends this record for the accepted
replacement design. Accepted application-owned authenticated UI/static design retains this one lifespan and bounds; UI routing and assets are not implemented yet.

## Authenticated asset and bootstrap amendment (2026-10-20)

[Decision147](decision-147.md) amends this record. This refinement adds one bounded immutable static capture and a separate finite body-send admission budget to the existing lifespan. Capture precedes operation-store construction/reconciliation, and every partial failure or cancellation drains exact owned work before releasing root descriptors and the instance lock. REST/MCP pools and response identity remain separate.

## Source implementation clarification (2026-10-21)

The earlier replacement-design amendment records its introduction-stage scope.
Unreleased source now implements authenticated indexed assets, bootstrap and
recognized UI routing under [decision147](decision-147.md), composed with this
same application lifespan and its original REST/MCP pools. The protected capture
and finite stream budget do not add another application or worker. Actual
installed/browser conformance and exact resource drain remain independently
required; no release or production availability is claimed. See the
[asset-serving contract](../server.md#authenticated-application-assets).

## Fresh-byte parsing refinement (2026-10-27)

[Decision157](decision-157.md) adds bounded process-local parsing reuse for two
frozen metadata model families. It follows every fresh no-follow read and query
charge, and leaves publication/policy joins and response leases unchanged. Raw
key retention is bounded separately from decoded objects and active read memory;
this memo never caches an authenticated response or filesystem authority.
The refinement is implemented in unreleased source. Its product gate and
artifact builds remain distinct from final installed performance/profile results.
