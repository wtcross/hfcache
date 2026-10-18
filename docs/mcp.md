# Optional MCP transport

MCP-001 adds an optional authenticated Streamable HTTP transport after committed
REST acceptance. MCP-002 adds the explicit nine-tool metadata read interface,
with repository acceptance recorded in its task. No command/job interface is exposed.
[Decision 124](adr/decision-124.md) records dependency/auth/lifecycle rationale;
the [transport task](plans/tasks/mcp-001-mount-authenticated-fastmcp.md) owns its
acceptance evidence. [Decision 125](adr/decision-125.md) and the
[tool task](plans/tasks/mcp-002-curated-read-only-tools.md) own curated exposure
and its registry/schema/side-effect proof.

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

## Curated metadata tools (MCP-002)

[Decision 125](adr/decision-125.md) permits exactly the following nine names.
No resources or prompts are registered. Every adapter receives only the narrow
async read protocol, with app-owned bounded metadata offload to a transport-neutral
backend. No SDK Context/Request/app object, command service, Hub client, credential
resolver, writable helper or arbitrary path/URL dispatcher is available. Tool
annotations are read-only, non-destructive, idempotent and closed-world, with no
background task execution; those hints do not enforce the boundary.

`repository_type` is `model` or `dataset`. Repository IDs and full SHA/publication/
run IDs use the shared validated grammars. Common page arguments are `limit=None`
and `cursor=None`; omission resolves to min(100, configured server maximum).
Requested limits are strict integers 1–10,000 and cannot exceed that maximum.
Cursors are at most 256 characters. Inventory selector lists are at most 64
strings of at most 256 characters each; no selector is a filesystem locator.
Selectors retain shared inventory semantics: a valid full-SHA suffix is accepted
but ignored for repository scope. Cursor scope uses sorted unique canonical
TYPE:ID identities, so suffix/order/duplicates do not change logical selection;
returned source ordering is unchanged.

| Tool | Inputs | Read source, result and cost |
| --- | --- | --- |
| `get_archive_status` | `selectors=None`, `repository_type=None`, limit/cursor | Shared status/health metadata, including configured empty repositories and archived unmanaged data; scans bounded metadata, never probes or repairs |
| `list_repositories` | Same inventory arguments | Authoritative archived repository inventory including unmanaged entries; domain order, bounded page |
| `list_revisions` | Same inventory arguments | Archived revisions with exact publication identity and honest verification state; bounded flattened revision page |
| `get_current_reference` | Required repository_type/repository_id | One validated current reference with `locator_base="published/"`; validates retained agreement and exact manifest/generation, never returns arbitrary file bytes |
| `get_revision_manifest` | Required repository_type/repository_id/commit_sha/publication_id; `collection="files"` or `"dependencies"`; limit/cursor | Exact immutable manifest instance, explicit selected-collection projection; full artifact validation may cost more than one page |
| `list_run_reports` | limit/cursor | Validated existing run IDs in reverse chronological filename order; never executes a run |
| `get_run_report` | Required run_id; limit/cursor | Existing run/recovery/verification report, explicit primary-collection projection and original evidence identity |
| `get_verification_report` | Required run_id; limit/cursor | Existing VerificationReport only; wrong report type refuses HFARG004; no hashing or persistence |
| `estimate_verification` | None | Existing stat/metadata estimator, no hashes/writes/Hub/lock or increase in verification confidence; large scans remain bounded work |

### Metadata output and pages

Every successful tool returns strict frozen `MetadataRead`: independent integer
`schema_version=1`, server `request_id`, `archive_id`, fresh installed
`config_fingerprint`, the existing typed `envelope`, and nullable `next_cursor`.
The envelope preserves the shared service's classified outcome/warnings/errors.
Its query metadata does not replace original report header run ID, configuration
fingerprint or timestamps. Request, operation and domain run identities remain
distinct; metadata tools create no operation or admission receipt. The wrapper
archive UUID comes from startup-pinned installed policy, not proof that each call
revalidates the sentinel. Reports check their archive UUID; references/manifests
check repository/SHA/publication/generation and canonical locators. Query outcome
success is not a clean-integrity claim: status can successfully report degradation,
and missing verification confidence remains unknown.

Status preserves configured TOML order followed by unmanaged identities in
byte-wise (type, ID) order; repository inventory uses that byte-wise identity
order. Flattened revision pages follow repository order and ascending immutable
publication generation within each repository. Manifest files retain byte-wise
path order and dependencies retain (source_file, source_field, detected_id)
order; report entries retain validated original array order. Empty/unmanaged
semantics match shared readers. Report ID listing checks filename identity and
ordinary-file containment, not every report body; exact report reads validate
body/filename/time/run/archive agreement. Inventory/status/revision cursors bind tool, normalized filters, installed
fingerprint and the complete selected row collection. Status archive headline
and warnings are fresh observations per page; changing free space/headroom alone
does not invalidate repository-row continuation. Immutable manifest/report
cursors additionally bind all sanitized source headers and collections, including
unreturned ones. Registered secret values (including known numeric literals) are
sanitized before hashing, so hidden secret substitutions cannot create distinct
credential-derived cursors. Changed visible bound content or policy refuses
HFAPI007; continuation is never a silent skip or global archive snapshot. Follow every
next_cursor until null to complete a selected collection. Scan/artifact/response
budget exhaustion refuses visibly rather than masquerading as an empty page.
Page limits count entries, not encoded bytes: even one large header/entry can
exceed the response cap and refuse rather than silently dropping fields.

Manifest data is `{projection:true, manifest:<header>, collection, entries,
total_entries, tree_base:"archive-root/"}`. The header excludes both `files` and
`dependencies`; collection selects one. Header `file_count`/`total_bytes` describe
the original complete validated artifact, not the returned page. Gather both
collections before reconstructing the durable manifest; never feed a partial
projection to copy/verification as though it were a complete manifest.

Report data is `{projection:true, report_type, report:<header>, collection,
entries, total_entries}`. Report types `run`/`recovery`/`verification` use primary
collections `repositories`/`remediations`/`findings`. The header excludes only that
primary collection and retains original evidence identity/times; reattach the
complete collection to reconstruct the original. The specialized verification
read never substitutes another report type or executes verification.

### Identity, confidence and refusal

Read current once, then request its explicit full SHA/publication ID. Both current
and exact metadata retain validated canonical locators and generation. A vanished
or mismatched exact publication refuses; the tool never substitutes a newer
current instance. Reference locators are relative to published/, manifest tree
locators to archive root, never an HTTP/MCP URL. Bulk copying remains the read-only
export and independent consumer workflow.

Absent/corrupt/unsafe derived catalogs retain unknown confidence and never trigger
repair/rebuild. Existing report failures remain evidence, not an instruction to
repair. Estimation is cost information, not verified integrity. Archive-derived
strings are untrusted data and must never be executed or treated as instructions.
Grammar/scope/identity/cursor/limit failures and missing/wrong-type evidence refuse
explicitly. Classified backend failures are MCP ToolError with stable code(s) and
fixed `metadata query failed`, never fabricated success metadata or an unknown
fingerprint. A supported SDK call-error middleware maps argument validation to
fixed HFAPI006 and unknown tool to HFAPI007; an exact-name guard refuses aliases
and unapproved names before SDK lookup/tracing. It never echoes rejected inputs.
Unexpected errors remain fixed/masked. HTTP/protocol success alone does not mean
a successful metadata call; inspect MCP isError and the returned domain Envelope.
This protocol guard supplies no SDK context/app capability to the nine functions.
No partial page, malformed artifact or missing state grants execution authority.

The transport cannot submit jobs, run actual verification, perform diagnostics/
probes, use Hub credentials, rebuild catalogs, recover/cleanup or install config.
Registry/schema equality and before/after archive/control-state snapshots must
prove this for successful and failed mounted calls; annotations alone do not.

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

MCP-002 enforcement is split deliberately: the transport-neutral
[MetadataReadQueries/MetadataRead/QueryPage backend](../src/hfcache/services/mcp_queries.py)
projects existing [shared authoritative reads](../src/hfcache/services/queries.py).
[MetadataReadPort and nine explicit functions](../src/hfcache/mcp_tools.py) expose
only named reads; the [app-owned adapter](../src/hfcache/api/mcp_reads.py) and
[application wiring](../src/hfcache/api/app.py) alone own bounded offload and
request context. The SDK request is not a tool argument or backend capability.
[Backend tests](../tests/unit/test_mcp_queries.py) and
[mounted registry/tool tests](../tests/unit/test_mcp_tools.py) provide task evidence.
[Shared metadata-pool tests](../tests/unit/test_mcp_pool.py) prove off-loop work
and refusal at the shared capacity limit.
