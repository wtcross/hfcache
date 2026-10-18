# Decision 113 — Serve bounded metadata through one authenticated lifespan

- Status: Accepted; implemented by API-006.
- Date: 2026-10-17.
- Work package: API-006, this commit.
- Source: [progress decision 113](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-006-fastapi-lifecycle-and-reads.md).

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
domain error aggregation. The [CLI taxonomy](../cli.md#5-error-taxonomy) records
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
Validation and source links accompany the [API-006 task](../plans/tasks/api-006-fastapi-lifecycle-and-reads.md).

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
