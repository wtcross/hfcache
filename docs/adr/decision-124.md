# Decision 124 — Add an optional authenticated MCP transport after REST acceptance

- Curated tool amendment: [decision 125](decision-125.md).
- Status: Accepted; implemented by MCP-001.
- Date: 2026-10-18.
- Work package: MCP-001, this commit.
- Source: [progress decision 124](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/mcp-001-mount-authenticated-fastmcp.md).

## Context and decision

API-016's committed REST acceptance (`07ff468`) precedes every MCP dependency,
import and endpoint. Add standalone FastMCP only in the optional `mcp` extra,
with the separately selected `server` extra hosting one FastAPI/Uvicorn process.
Resolve and verify the supported public Streamable HTTP, token-verifier and
lifespan interfaces on CPython 3.14; keep base and REST-only installs independent.
The lock selects FastMCP/fastmcp-slim 4.1.1 (`>=4.1.1,<5`), MCP/mcp-types 2.3.0
and HTTPX2/HTTPCore2 2.13.1, with 53 optional additions and 94 total packages. Existing locked versions remain, including HTTPX
0.28.1, FastAPI 0.143.3, Starlette 1.8.0, Uvicorn 0.54.0 and Pydantic 2.13.4.
These optional protocol dependencies do not replace the base client transport.
The installer's explicit `--with-mcp` flag selects both locked extras and smoke
for build/stage only; default remains server-only. It does not enable config,
provision credentials, change services or bypass quiescence/rollback guards.

Mount the FastMCP HTTP application at the fixed `/mcp` boundary in the existing
application. Explicitly compose lifespans: existing REST authority/resources
initialize before MCP, and MCP closes before those resources are drained and
released. Startup failure unwinds acquired ownership. Never replace REST startup,
run a second Uvicorn application, nest an event loop or expose the REST OpenAPI
as an automatically generated tool registry. MCP-001 supplies transport only;
curated tools belong to MCP-002.

Use FastMCP's supported `TokenVerifier` extension backed by the shared protected
opaque-token registry. Only the distinct `mcp-reader` credential authenticates
MCP; REST writer/reader and Hub credentials cannot. MCP credentials never authorize
REST access. Authenticate every supported HTTP request, including transport
continuations; a session identifier never grants authority. Do not use the
upstream development `StaticTokenVerifier`, ambient auth discovery or plaintext
secret configuration. Accepted tokens remain registered for redaction.

Disabled MCP imports no optional package, mounts no endpoint and does not resolve
or require its credential even if an inert source is configured. Enabling requires
both the package and a usable distinct configured source at startup. Auth policy
and rotation remain restart-only. The fixed MCP reader is a whole-archive
capability under AD-21, not an individual identity or repository ACL.

Retain existing Host/Origin/TLS/proxy/prefix and request/response/concurrency
boundaries, including decision 123's corroborated native Unix scope. Mount-path
selection cannot bypass REST authentication or expose command routes to MCP.
Use supported `stateless_http=True`: no retained legacy sessions or resumption
store. The canonical endpoint is `/mcp/`; a narrow authenticated safe relative
307 from `/mcp` follows all transport/body/query checks without reflecting input.
REST slash redirects stay disabled. One trusted path projection prefers configured
prefixes when their remainder identifies REST/MCP, otherwise corroborated native
interface spelling; authentication, writer/body routing, effective prefix and
links use the same result. This preserves both interfaces when a public prefix
collides with `/mcp` or `/api`.

Use finite `json_response=True`, the shared strict bounded JSON POST/empty-body
other-method policy and no MCP query parameters. A separate MCP in-flight ceiling
uses metadata workers plus pending capacity and reserves after auth before body
collection, releasing through response/disconnect/failure; it adds no retained
session queue and slow bodies cannot bypass the limit.
Buffer/sanitize each bounded finite response before headers and recheck encoded
size, so overflow cannot appear as successful truncated output. SDK diagnostics
must use sanitized scoped logging, never raw tracebacks. Add only the stable
closed-vocabulary warning `mcp.diagnostic`: suppress SDK levels below WARNING,
emit fixed text with original severity and bounded sanitized logger provenance
through the existing correlation API, restoring handlers on lifecycle exit.
Never format SDK messages/arguments/exceptions. JSON-RPC errors retain code but
use fixed messages and drop raw SDK/Pydantic data/details; successful values keep
registered-secret sanitization. Exact public APIs,
method/client behavior and bounds have source/test evidence in the task.

## Rationale and alternatives

Maintained protocol negotiation, streaming framing, cancellation/session handling,
auth extensions and lifecycle are a material correctness benefit beyond the
standard library. This scoped FW-04 addition implements decision 108 after its
REST gate; it adds no domain workflow framework, scheduler, database, durable
queue or new storage authority. Handwritten MCP framing would duplicate a complex
protocol. Auto-converting REST would expose writer jobs and semantic read-side
effects that the curated MCP boundary forbids.

Static pre-provisioned bearer verification supports controlled internal clients.
It does not implement OAuth discovery, registration, consent or token issuance;
clients must support supplying the provisioned bearer. Separate lifecycle and
class checks keep protocol features from widening archive authority.

## Evidence and relationships

Amends [64](decision-064.md), [108](decision-108.md), [112](decision-112.md),
[113](decision-113.md), [123](decision-123.md), [FW-01–04](fw-01.md) and
[AD-21](ad-21.md). Preserves INV-002/003/012–016, existing domain algorithms,
archive/receipt/config versions and operator deployment holds.
[MCP](../mcp.md), [server](../server.md), [API](../api.md),
[security](../security.md) and [invariants](../invariants.md) own the contract.
Task evidence records actual version/import/install, streaming/auth/prefix,
lifecycle and full-gate outcomes; repository acceptance is recorded below.

Official references consulted for this decision:

- [FastMCP 4.1.1 release metadata](https://pypi.org/pypi/fastmcp/4.1.1/json).
- [Mounted FastAPI applications and composed lifespans](https://gofastmcp.com/integrations/fastapi).
- [Token-verifier extension](https://gofastmcp.com/servers/auth/token-verification)
  and [supported auth classes](https://gofastmcp.com/python-sdk/fastmcp-server-auth-auth).
- [HTTP transport, sessions and Host/Origin protection](https://gofastmcp.com/deployment/http).

No production rollout, installed-host hardening proof, command/job MCP path or
curated tool implementation is introduced by this package.

Implementation references: [optional MCP module](../../src/hfcache/mcp.py),
[application projection/lifecycle](../../src/hfcache/api/app.py),
[active credential loader](../../src/hfcache/api/auth.py),
[closed event vocabulary](../../src/hfcache/logging.py),
[transport/verifier cases](../../tests/unit/test_mcp_transport.py) and
[mounted streaming/security cases](../../tests/unit/test_mcp_mount.py).

Repository acceptance completed 2026-10-18. The definitive full gate exits 0 with
3,394 Python tests, three locked wheel profiles and the complete 127-test Cockpit
build gate. The task preserves actual streaming/auth/lifecycle/limit and optional
installation evidence, plus the earlier nine test-fixture failures and public
exchange correction. No post-definitive-gate source change. MCP-002 remains
pending for curated tools; deployment/credential/hardening holds remain explicit.

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
[MCP-002 task](../plans/tasks/mcp-002-curated-read-only-tools.md).

## 2026-10-18 mounted security traceability (MCP-003)

[MCP-003](../plans/tasks/mcp-003-mcp-security-and-side-effect-tests.md) maps this
existing decision to required [threat/control/test evidence](../mcp.md#threat-control-and-test-traceability-mcp-003).
Parent-lifespan mounted authorization, closed registry/arguments, whole-state
snapshots, malformed evidence and secret containment, finite mixed-interface
work and cancellation/drain ownership are proofs of the existing boundary.
They add no role/tool/durable format or architectural choice. Post-startup
baselines exclude atime and permit sanitized operational logging; concurrent REST
fixture effects remain attributable to REST. Actual host credential/egress/
transport/SELinux/NFS/drain/rollback acceptance remains separate operator work.
Repository proof completed 2026-10-18: the first full gate exits 0 with 3,522
Python tests (40 deselected, 417.54 seconds), all three locked wheel profiles and
127 Cockpit tests/production build. No runtime source or architectural choice
changed. The task owns exact evidence; MCP-004/API-017 and real host acceptance
remain separate. No new numbered decision is introduced for these proofs.
