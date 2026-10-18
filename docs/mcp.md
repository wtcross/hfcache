# Optional MCP transport

MCP-001 adds an optional authenticated Streamable HTTP transport after committed
REST acceptance. Repository transport acceptance is complete; no curated tools
are implemented by this package. MCP-002 owns the explicit read-only toolset.
[Decision 124](adr/decision-124.md) records dependency/auth/lifecycle rationale;
the [task](plans/tasks/mcp-001-mount-authenticated-fastmcp.md) owns actual evidence.

## Enablement and authority

Install the server and MCP extras together, then deliberately set the existing
server `mcp_enabled = true` and provision a separate protected
`[credentials.mcp_reader]` source. No token value belongs in TOML, a URL, command
argument, browser code or logs. The [server configuration](server.md) and
[security contract](security.md) define protected file/named credential rules.
Disabled MCP imports no FastMCP package, resolves no MCP credential and mounts no
MCP endpoint; ordinary base and REST-only installations remain independent.

The MCP reader is a distinct fixed whole-archive capability. REST writer/reader
bearers cannot access MCP, and the MCP bearer cannot access REST. Production
verification uses the supported FastMCP `TokenVerifier` extension over the shared
protected opaque-token registry, never its development static verifier. A valid
session identifier alone grants no access; every transport request authenticates.
Authentication/credential rotation is startup-only and requires restart.

This is pre-provisioned bearer authentication for controlled internal clients.
No OAuth discovery/registration, consent, login or token issuance is provided.
Choose a client that can supply its provisioned bearer over verified HTTPS;
public OAuth-only clients are not automatically compatible. Examples must never
contain real tokens or imply an unperformed host installation.

For locked checkout development, select both extras:

```bash
uv sync --locked --extra server --extra mcp
```

The release installer supports explicit `--with-mcp` for build/stage operations;
it is refused with list/switch modes and does not modify config or start services.
Default staging remains server-only. Enabling against a release without the
optional package fails closed; staging alone does not provision authentication.

The shipped server example's optional named source is `hfcache.mcp-reader`.
Default API units import only their existing credentials, so a named MCP source
requires deliberate delivery to the API service. An operator-selected drop-in
may add this declaration after provisioning its encrypted credential:

```ini
[Service]
LoadCredentialEncrypted=hfcache.mcp-reader:/etc/credstore.encrypted/hfcache.mcp-reader
```

Then `[credentials.mcp_reader] systemd_name = "hfcache.mcp-reader"` selects that
name in server TOML. A protected explicit file is the alternative; neither path
permits a literal value in configuration or request input. This is an installation
example, not an executed host change. The private verification worker must receive
neither MCP nor REST/Hub credentials; standard stores are masked, while custom
source paths require explicit masks/probes under existing operator holds.

## Transport and lifecycle

The fixed canonical `/mcp/` HTTP application shares one FastAPI/Uvicorn process
with REST.
Existing REST startup enters before the explicitly composed MCP lifespan; MCP
closes before REST ownership drains/releases. Failure unwinds resources without
replacing the archive/instance locks or starting a nested server/event loop.

MCP retains Host/Origin/TLS/proxy and public-prefix enforcement. Only corroborated
trusted native Unix transport may use unprefixed paths, following
[decision 123](adr/decision-123.md); request headers cannot manufacture locality.
The supported mount uses `http_app(path="/", stateless_http=True)` under
`Mount("/mcp", ...)`. Requests to `/mcp` receive a safe relative 307 to `/mcp/`
only after authentication and transport/body/query checks; no query or caller
header is copied into Location. This narrow MCP spelling redirect does not
re-enable REST slash redirects. Configured public TCP prefixes apply to the mount;
corroborated native Unix may use its native spelling under decision 123.

Stateless mode retains no server-side legacy session or resumption history.
Clients can negotiate and make protocol requests, but a session header never
creates an authorization bypass or an execution receipt. MCP-001 selects
`json_response=True`: each response is finite JSON, not a retained SSE feed. The locked SDK handles
POST/DELETE; stateless GET is authenticated before its method refusal. Both the
outer registry and supported production FastMCP verifier enforce MCP-only class
authority on every request. No OAuth discovery routes are mounted. The actual SDK/streaming-client modern
and legacy behavior is acceptance evidence, not an OAuth-client compatibility
promise.

One trusted path projection handles public-prefix collisions with `/api/v1` and
`/mcp`: prefer the configured-prefix spelling when the remainder identifies an
interface; otherwise permit the native interface spelling only for corroborated
Unix scope. The same projection selects interface authentication, static writer/
body policy, effective root, redirects and links. A public root `/mcp` cannot
turn its REST paths into MCP-authenticated requests; native MCP remains reachable.

Every MCP request rejects query parameters. POST requires the shared bounded
strict JSON-object/media/encoding/UTF-8/depth/duplicate-key policy; other methods
require empty bodies before SDK method handling. Existing `max_request_bytes`
applies. MCP transport has a separate in-flight ceiling equal to
`metadata_workers + metadata_queue`. A request reserves its slot immediately
after successful authentication, before body collection, and releases on response/
disconnect/failure. Slow chunked bodies therefore count; excess requests refuse
instead of retaining an unbounded session queue. It buffers each finite response
before sending headers,
refuses over `max_response_bytes`, sanitizes registered secrets in JSON/text and
checks the encoded bound again. Thus an oversized response cannot become a
truncated successful stream. The original and sanitized bodies are bounded;
this transport does not promise an unbounded incremental SSE feed. SDK errors and
scoped diagnostics are sanitized, without returning raw tracebacks or registering
new execution authority. The lifespan bridge records SDK warning/error provenance
through stable closed-vocabulary `mcp.diagnostic` and captured correlation;
`sdk_level` retains original lowercase severity and `sdk_logger` is bounded to
256 characters and sanitized. Diagnostic text is fixed: the bridge never evaluates
SDK messages, formatting arguments or exceptions, which may contain rejected
inputs. Messages below WARNING are suppressed and original SDK handlers restore
on exit.

This is operational evidence, not a command outcome or checkpoint. JSON-RPC
errors preserve their integer code but use fixed safe messages and drop SDK error
message/data/details; raw Pydantic rejected values never become protocol output.
Registered-secret sanitization still covers successful values/IDs, with unsafe
numeric identities refused rather than echoed.

## Current exposure and limitations

No tools, resources or prompts are registered in MCP-001. The transport is not a
REST OpenAPI conversion, command dispatcher, URL fetcher or arbitrary file reader.
It cannot submit jobs, run verification, perform diagnostics/probes, use Hub
credentials, rebuild catalogs or install configuration. Future tool enforcement
must use narrow read-service interfaces, explicit allowlists and no-side-effect
proof; `readOnlyHint` annotations alone grant no security.

Archive/receipt/config schemas, domain algorithms and whole-archive authorization
are unchanged. Local socket/streaming tests and locked wheel installs do not prove
deployed systemd/cgroup credentials, no-IP masks, browser/PAM, SELinux/NFS or
rollback/drain acceptance. Existing [operator holds](progress.md#operator-handoff)
remain deployment prerequisites; no production operation is authorized.

## Rollback and deployment limits

The existing config slot is already readable by predecessor feature releases,
but pre-MCP runtimes refuse enabled MCP. Before rollback to a server-only or
pre-MCP target, deliberately disable MCP in server configuration under the
normal restart/drain procedure. There is no schema migration or automatic
fallback. `--with-mcp` stages a chosen dependency profile; it cannot add packages
to an existing `--switch` target. Preserve previous trees, operation/scheduled
history and all existing quiescence/lock guards. Neither staging nor these
examples performs a production service change.

## Enforcement and evidence

[`hfcache.mcp`](../src/hfcache/mcp.py) provides `OpaqueTokenVerifier`,
`create_mcp_app`, `BoundedMCPTransport` and scoped `mcp_diagnostics`. The
[outer boundary/application](../src/hfcache/api/app.py) owns interface projection,
shared transport/body checks and composed lifecycle. The
[credential core](../src/hfcache/api/auth.py) owns active protected source loading
and constant-time class separation. [Mounted streaming/security tests](../tests/unit/test_mcp_transport.py)
and [direct verifier/lifecycle/limit tests](../tests/unit/test_mcp_mount.py)
exercise supported SDK paths rather than an in-memory direct server shortcut.

[Locked isolated installation checks](../scripts/check-installations.py) preserve
base, server-only and server+MCP profiles, including cold CLI imports independent
of optional frameworks. [Installer tests](../tests/unit/test_release_installer.py)
cover explicit dependency selection without host operations. Task evidence owns
actual executed counts and the full gate; pending host checks stay separate.
