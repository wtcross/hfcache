# Expose nine typed metadata tools through a narrow read capability

- Decision identity: 125.

- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-18.


## Context, decision and rationale

Expose exactly nine explicit typed metadata tools through a narrow async read
port. Tool functions receive no SDK app/request context, command service, Hub client,
credential resolver, writable helper or arbitrary path/URL dispatcher. Read-only,
idempotent/non-destructive hints describe the boundary; closed schemas, exact-name
guards, contained readers and success/failure state-preservation tests enforce it.
No resources/prompts or background execution authority is registered.

Strict schema-1 MetadataRead wrappers preserve archive/request/fresh policy identity
and classified domain outcomes. References/manifests bind exact SHA/publication/
generation and canonical locator bases; a vanished instance never substitutes a
new current. Manifest/report projections require complete collection assembly before
use as durable evidence. Cursors bind complete selected rows or all sanitized source
headers/collections, including unreturned ones; visible changes refuse. Known secrets
are sanitized before cursor hashes, including numeric substitutions. Status headline
can change independently, so pages are observations rather than a global snapshot.

Missing/unsafe derived catalogs remain unknown; reads and estimates never hash
payloads, repair, rebuild, persist receipts or contact the Hub. Full-source/scan/
artifact/page/wire/capacity bounds can refuse even a one-entry page. Classified
errors remain fixed/safe, not fabricated success. Archive strings are inert untrusted
data. Legacy optional params.task metadata may be ignored for an ordinary finite
read, but creates no task handle/job/state. Actual no-IP/SELinux/NFS/consumer/browser
acceptance remains distinct from hermetic registry, concurrency and client checks.

## Relationships and technical evidence

- [124](decision-124.md)
- [113](decision-113.md)
- [AD-10](ad-10.md)
- [AD-15](ad-15.md)
- [AD-21](ad-21.md)
- [MCP](../mcp.md)
- [API](../api.md)
- [consumers](../consumers.md)
- [transport-neutral backend/models](../../src/hfcache/services/mcp_queries.py)
- [nine tools/narrow protocol](../../src/hfcache/mcp_tools.py)
- [app-owned facade](../../src/hfcache/api/mcp_reads.py)
- [bounded wiring](../../src/hfcache/api/app.py)
- [backend cases](../../tests/unit/test_mcp_queries.py)
- [actual registry/tool proof](../../tests/unit/test_mcp_tools.py)
- [threat/control/test evidence](../mcp.md#read-only-boundary)
- [protected-file example](../../examples/mcp-client.py)
- [MCP setup/session/rotation guide](../mcp.md#connect)
- [cost/refusal guidance](../mcp.md#resource-costs-and-troubleshooting)
- [acceptance tests](../../tests/unit/test_mcp_acceptance.py)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).

- [FastMCP tool/typed output/annotation reference](https://gofastmcp.com/servers/tools)
