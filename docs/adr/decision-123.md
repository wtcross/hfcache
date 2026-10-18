# Decision 123 — Keep public prefixes separate from native Unix REST paths

- MCP transport amendment: [decision 124](decision-124.md).
- Status: Accepted; implemented by API-016.
- Date: 2026-10-18.
- Work package: API-016, this commit.
- Source: [progress decision 123](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-016-rest-acceptance-gate.md).

## Context and decision

The same application serves public TCP and private Unix sockets. A public
`root_path` such as `/management` currently also forces that prefix onto native
Unix requests, while installed scheduled/Cockpit clients deliberately use the
fixed unprefixed local API. Prefix-bearing acceptance links compound the mismatch.
REST acceptance must resolve the complete supported arrangement before MCP starts.

Keep configured public prefix, TLS/proxy and Host/Origin enforcement for TCP.
Permit native unprefixed REST paths only for the supported Uvicorn AF_UNIX
transport's trusted ASGI scope: `client=None` together with
`server=(absolute Unix socket pathname, None)`, verified against the locked
implementation and real socket fixtures. Missing peer alone is insufficient:
Uvicorn can also return `client=None` on socket errors, while TCP's local address
has an IP and numeric port. Require the corroborated native predicate for both
prefix and existing proxy-TLS exceptions; missing/malformed local evidence fails
closed. Unix still requires the same REST
bearer, Host/Origin validation and request/response/resource limits. A forwarded
header, URL, request body or client option cannot select this transport authority.
Do not trust arbitrary ASGI integrations to manufacture native Unix identity.

Choose a trusted effective prefix per request and use it for acceptance operation
links and docs/schema URLs. Never mutate a process-global prefix or substitute
forwarded-header authority. TCP continues to require its configured public path;
native Unix responses use paths its existing local client can validate. Public
OpenAPI stays deterministic with the configured public server prefix, without
machine-specific addresses, secrets or timestamps.
Native Unix accepts both unprefixed and configured-prefixed spellings and returns
links for the spelling used. Its unprefixed OpenAPI response may copy the schema
with `servers=[{"url":"/"}]`; prefixed/TCP responses keep the configured public
prefix. Never mutate the cached public schema to produce that native view.

No client/config/durable format change is needed. The existing endpoint-group
selection, verified TLS, disabled ambient proxy/credential discovery and strict
same-operation link validation remain. Scheduled/Cockpit clients keep their
fixed local socket/client TOML and API-only credential boundaries. Request,
operation, admitted fingerprint and domain result identities are unchanged.

## Rationale and alternatives

Adding a Unix-prefix setting would make local packaged clients depend on public
proxy routing and widen a durable config surface unnecessarily. Removing prefix
checks for TCP would weaken its existing public boundary. One request-scoped
transport distinction retains both supported interfaces without a second app,
redirects, forwarded-prefix trust or silently rewritten client links.

Treating a source inspection or unit file as installed-host proof would obscure
the remaining boundary. Require locked-source and actual disposable socket tests;
keep deployed systemd/cgroup/credential/hardening/SELinux/NFS/browser acceptance
as explicit operator holds. The complete REST matrix and fresh full build gate,
not one prefix regression, decide API-016 acceptance. MCP remains absent until
this package passes and commits.

## Consequences and relationships

Amends [113](decision-113.md), [118](decision-118.md),
[121](decision-121.md) and [122](decision-122.md). Preserves
INV-003/006/010/011/012–014, existing credential/FS/TX authority, one application
and lifecycle, all 29 REST parity modes and the client uncertainty boundary.
No dependency, durable JSON/config schema, production operation or deployment
authorization is introduced.

[Server](../server.md), [API](../api.md), [client](../api-client.md),
[security](../security.md) and [invariants](../invariants.md) own the detailed
rules. The task records actual source/socket, parity, example, compatibility and
full-gate evidence; unsupported or unrun host checks are never asserted passed.

Enforcement: [trusted boundary/effective prefix](../../src/hfcache/api/app.py) and
[supported Uvicorn bootstrap](../../src/hfcache/server.py).
Evidence: [actual socket/schema/scope cases](../../tests/unit/test_rest_transport_gate.py),
[complete paged reads](../../tests/unit/test_rest_pagination_gate.py),
[independent route security inventory](../../tests/unit/test_rest_security_gate.py),
[semantic parity manifest](../../tests/rest_parity.py),
[static citation/parameter validation](../../tests/unit/test_rest_parity_gate.py) and
[strict examples/docs/cold-disabled process](../../tests/unit/test_rest_examples_gate.py).

Repository acceptance completed 2026-10-18: the first full
`scripts/check.sh --with-build` exits 0 with 3,324 default Python tests, four
additional wheel smoke tests, locked base/server installations and the complete
127-test Cockpit gate/build. The task preserves focused source/socket/page,
route/parity/example/docs and actual predecessor/current compatibility evidence.
This completes the REST repository boundary; installed-host holds remain and MCP
is still absent until this package commits.

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

The MCP-001 refinement uses one trusted path projection when a configured public
prefix overlaps fixed REST/MCP spellings: configured prefix wins when its remainder
identifies an interface; otherwise corroborated Unix native interface spelling
may apply. Interface credential selection, early static writer/body policy,
effective root and response links all consume that same projection. Prefixes
such as `/m`, `/mcp` and `/api` cannot confuse REST with MCP authority. TCP still
requires its configured prefix and no header supplies transport authority.
