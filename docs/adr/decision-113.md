# Decision 113 — Serve bounded metadata through one authenticated lifespan

- MCP transport amendment: [decision 124](decision-124.md).
- Curated tool amendment: [decision 125](decision-125.md).
- Status: Accepted; implemented by API-006.
- Date: 2026-10-17.
- Work package: API-006, this commit.
- Source: [progress decision 113](../agents/progress.md#decisions),
  [active plan](../agents/plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../agents/plans/tasks/api-006-fastapi-lifecycle-and-reads.md).
Native Unix/public-prefix routing is amended by [decision 123](decision-123.md).

## Context and decision

The shared query services now need a real management transport without changing
archive authority or delaying the event loop behind filesystem scans. Read-only
access still needs filesystem containment: legacy status/list/latest-report and
catalog paths must not follow a swapped directory or accept a body belonging to
another archive merely because the requested file name looks valid.

Provide an injectable FastAPI application factory and a local `hfcache serve`
bootstrap. Import/factory construction does not start a listener, contact the
Hub, initialize storage or mutate the archive. One lifespan owns startup-only
configuration/authentication/logging, a daemon-instance lock and bounded query
workers; Unix and TCP sockets serve the same application. This instance lock is
separate from the archive flock and grants no mutation authority. The latter
remains operation-scoped when job execution lands.

Authenticate every HTTP surface before route/body/error processing, including
health, unknown routes, disabled docs and OpenAPI. Enforce configured Host,
Origin, proxy/prefix and request/response bounds, generate authoritative request
correlation and return sanitized typed problems. Route adapters use shared query
services and a fresh pinned archive-policy snapshot; they never call Typer or
construct Hub credentials. Health reports diagnostics without probes or repair.
Absent/unavailable/uninitialized archive state is not permission to initialize
or rebuild derived catalogs. Version/health remain useful when later installed
policy becomes invalid, without switching archive root/UUID authority.

Expose only the metadata resources listed as implemented in the API matrix:
version/capabilities/health, status, inventory/revisions, exact references and
manifest evidence, existing reports, verification estimates and archive
inspection. Use bounded deterministic pages and explicit wire models separate
from durable records. Pages are not an archive-wide snapshot; clients must walk
them without silently truncating a legacy result. Exact-instance reads retain
publication identity and `published/`-relative locators, and a vanished instance
fails visibly rather than substituting a newer current tree. Existing reports
stream from validated contained evidence without unbounded duplicate buffers.

Strengthen the underlying local readers as part of exposing them remotely:
no-follow descriptor-relative traversal, archive/body/path identity checks and
safe classified refusals. Preserve tolerant absent/corrupt derived-catalog
behavior and unknown verification confidence; these safety checks do not grant
repair or deletion authority.

Archive-policy root/UUID pinning is configuration authority, not proof that every
metadata request has revalidated the sentinel. Exact reports check the configured
archive UUID and filename/time/run identity. The verification catalog has no
archive-ID field; absent/corrupt/unsafe state yields unknown confidence, and
budget exhaustion still propagates. References/manifests check their
repository/SHA/publication/generation and canonical locators. Separate archive
inspection diagnoses sentinel state without repair. Transport-injected
`QueryBounds` preserve the local CLI's complete default results while making
remote budget exhaustion visible instead of silently returning an empty page.

Extend the central HFAPI taxonomy deliberately: authentication/configuration and
invalid/absent/security-policy requests remain exit 10. Exact codes HFAPI005
(metadata budget), HFAPI008 (unexpected failure), HFAPI009 (full/draining) and
HFAPI011 (instance lock) override the family default to exit 20. An unavailable
or unsafe service is not an invalid credential, and HTTP status does not replace
domain error aggregation. The [CLI taxonomy](../cli.md#5-error-and-warning-taxonomy) records
every code; no existing code is reused.

## Rationale and alternatives

An async route that directly scans the archive would block unrelated requests;
an unbounded worker queue would merely move the resource-exhaustion boundary.
Bound both workers and pending work, propagate independent execution contexts,
and retain ownership until work or an evidence stream really finishes.
Creating one writer application per socket would duplicate admission/lifecycle
state; both transports instead share one application and instance lock.

Protecting only known success routes leaves unauthenticated error or schema
surfaces. Validating only a final path component leaves symlinked ancestors and
cross-archive record bodies unchecked. Atomic catalog replacement is unrelated
to safe read containment. Reusing and hardening shared queries preserves the
local contract while providing the same checks to HTTP and future transports.

## Consequences and relationships

Advances the transport boundary in [decision 108](decision-108.md) and the
route/lifespan enforcement deferred by [decision 112](decision-112.md).
Preserves [decision 111](decision-111.md)'s scoped correlation, AD-21's whole-
archive credential boundary, FS/TX, durable formats and consumer verification.
No bulk artifact route, configuration installation, job admission, write route,
in-process verifier fallback, MCP import/dependency or production rollout is
introduced. The installed CLI continues its existing local operations until
API-011–013 migrate it; `serve` is the authorized bootstrap addition.

The foreground daemon writes no terminal success Envelope/stdout. Classified
startup failures preserve their original HfcacheError code/exit and the normal
schema-1 error Envelope under `--json`. This is an explicit narrow exception to
INV-006 for `serve`, not a change to operational command results. One locked
Uvicorn lifecycle override applies TLS to TCP while retaining local Unix HTTP;
real socket/TLS tests protect that version-coupled boundary.
Address reservation precedes TLS validation, but connections are accepted only
after successful TLS/lifespan startup; failed setup closes reserved sockets and
cleans only the owned unchanged Unix inode. Raw framework
request logging and slash redirects are disabled to prevent URL/header/query
secret echoes; schema/docs obey response ceilings too. The API wrapper's UUID
can fall back to startup-pinned configuration, never a sentinel-proof claim.

Exact resources, DTO fields, statuses, page order/bounds and streaming limits
are specified in the [API contract](../api.md). Startup/listener/shutdown
requirements and implemented/pending boundaries are in the [server contract](../server.md).
Validation and source links accompany the [API-006 task](../agents/plans/tasks/api-006-fastapi-lifecycle-and-reads.md).

Implementation: [read app/boundary](../../src/hfcache/api/app.py),
[wire models](../../src/hfcache/api/models.py),
[pool and instance lock](../../src/hfcache/api/lifecycle.py),
[no-follow metadata/budgets](../../src/hfcache/metadata.py),
[shared queries](../../src/hfcache/services/queries.py), and
[listener bootstrap](../../src/hfcache/server.py).
Evidence: [wire/read/lifespan tests](../../tests/unit/test_api_reads.py),
[adversarial HTTP cases](../../tests/unit/test_api_adversarial.py),
[shared query containment](../../tests/unit/test_query_boundary.py), and
[ephemeral Unix/TCP/TLS tests](../../tests/unit/test_server_bootstrap.py).


## 2026-10-18 native Unix prefix and REST acceptance amendment (API-016)

The authenticated single application now distinguishes trusted supported Unix
transport scope from public TCP prefix routing. Native Unix may use unprefixed or
configured-prefixed REST paths with matching links/docs; TCP retains configured
prefix/TLS/proxy/Host/Origin checks. Native OpenAPI is a response copy and cannot
mutate deterministic public cache state. No forwarded header grants native
transport identity. Locked-source/actual socket evidence and complete fresh REST
acceptance are required before MCP; see [decision 123](decision-123.md).

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
[MCP-001 task](../agents/plans/tasks/mcp-001-mount-authenticated-fastmcp.md) for evidence.

## 2026-10-18 curated metadata tool amendment (MCP-002)

[Decision 125](decision-125.md) registers exactly nine typed metadata tools via
an explicit narrow read capability, with no resources/prompts, OpenAPI conversion,
SDK app/request context, command/Hub/credential resolver or writable helper.
Read-only annotations describe the capability; registry/schema equality and
success/failure archive/control-state snapshots must prove it.

Shared validated readers preserve exact SHA/publication identity, canonical
locator bases and unknown derived confidence without writes or reconstruction.
Manifest/report pages are explicit projections, not complete durable artifacts;
headers preserve original totals/report provenance and complete source content
binds cursors. Missing/stale instances refuse rather than substituting current.
Archive-derived strings and dependency observations remain untrusted data, never
instructions or executable content. Consumer copy/verification/promotion and
whole-archive authorization remain unchanged. No dependency, config/durable
schema, job path or production operation is added. See [MCP](../mcp.md) and the
[MCP-002 task](../agents/plans/tasks/mcp-002-curated-read-only-tools.md).
