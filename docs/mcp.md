# Read-only MCP metadata interface

hfcache provides an optional MCP interface for exploring archive metadata. Its
nine tools inspect status, repositories, retained revisions, references, manifests
and existing run or verification reports, and estimate verification work. They
cannot start jobs, download repositories, repair/delete data or perform integrity
verification.

Connect to the writer's `/mcp/` endpoint with a separately provisioned MCP-reader
bearer. It grants metadata access across the entire archive, including restricted
repositories; every client must be entitled to that scope. REST and Hugging Face
credentials are separate and cannot substitute for it. Requests use authenticated
Streamable HTTP with finite JSON responses and no OAuth login/token issuance.
Off-host connections require verified HTTPS.

## Connect

[`examples/mcp-client.py`](../examples/mcp-client.py) is a deterministic metadata
client for the locked FastMCP 4.1.1 interface. It does not run an agent, accept a
command/tool name, discover credentials or install anything. An operator must
first provision a distinct MCP-reader secret through the protected file rules in
[server authentication](server.md#credentials-and-capabilities).
Token acquisition is operator provisioning, not OAuth discovery. Supply only the
absolute protected file pathname; never put its contents in argv, URLs, JSON,
shell history or browser storage.

From a locked checkout with both test/server extras selected:

```bash
uv sync --locked --extra server --extra mcp
uv run --locked --extra server --extra mcp python examples/mcp-client.py \
    --url https://archive.example.com/management/mcp/ \
    --token-file /etc/hfcache/mcp-reader.token \
    --expected-archive-id 01234567-89ab-4cde-8fab-0123456789ab
```

Choose your provisioned authority, public prefix, protected source and archive
UUID. Use `--ca-file /etc/hfcache/archive-ca.pem` for a private CA rather than
disabling verification. The source is validated/registered before network I/O;
it is the MCP credential, never `hfcache.api` or the Hub secret. The example
selects an explicit HTTP transport rather than SDK inference from an arbitrary
string that could identify a local executable.

| Argument | Default / meaning |
| --- | --- |
| `--url` | Required canonical HTTPS URL ending `/mcp/`, including any public prefix; explicit loopback HTTP is the development exception |
| `--token-file` | Required absolute protected opaque MCP-reader credential file; no token-value/environment option |
| `--ca-file` | Optional explicit CA file; ordinary verified system trust otherwise |
| `--expected-archive-id` | Optional canonical UUID pin; recommended to detect a wrong archive before using metadata |
| `--page-size` | `100`; integer 1–10,000 within the server's configured maximum, never a promise that a row fits its byte limit |
| `--max-pages` | `1000`; integer 1–10,000 across all metadata tool reads, including current and both manifest collections, not silent truncation |
| `--timeout` | `30` seconds; finite `(0, 300]` overall deadline including negotiation and page reads |
| `--mode` | `auto` or `legacy`; normal supported negotiation or explicit initialize-handshake compatibility |
| `--type`, `--repository` | Both together select one repository for exact current/manifest discovery; omitted means inventory only |

The example walks repository inventory and prints one JSON object with
`kind="discovery_summary"`, `repository_count` and `metadata_pages`. Success exits
0; failure/interrupt exits 1 with a fixed safe diagnostic and no partial summary.
This is example output, not a domain Envelope or receipt.
Optional repository discovery reads current once, then walks both manifest
collections at its exact full SHA/publication ID, adding `manifest_files` and
`manifest_dependencies` counts. It pins archive UUID and fresh
policy identity across the walk, checks typed schema-1 responses, exact artifact
headers and cursor continuity, and rejects repeated cursors/inconsistent or
unfinished walks. `metadata_pages` counts all metadata calls, including the unpaged
current reference. It returns counts, not file content or an authoritative durable
manifest. Reconstructing and independently verifying a complete consumer copy
remains the [consumer workflow](consumers.md#mcp-metadata-discovery).
No archive mount/config, Hub credential, REST writer token or local mutation
fallback is required or used.

Each received response is capped at 16 MiB by the example, under one deadline;
the server's smaller configured cap still applies. It disables redirects,
ambient proxies and implicit credential discovery, retains certificate
verification and caches no credential or result to disk. Errors use fixed safe
diagnostics rather than rejected input or SDK tracebacks. These client bounds do
not expand server budgets or authorize execution.

### Negotiation and reconnect

MCP protocol negotiation, the independent `MetadataRead.schema_version=1` and
its nested domain Envelope schema are different compatibility boundaries. Check
the typed metadata version and identity rather than inferring them from a server
package/version string. Unknown/malformed metadata or durable evidence refuses;
do not coerce it, rewrite its version or continue a partial collection.

The locked SDK's `mode="auto"` negotiates modern `server/discover`; `legacy`
uses `initialize`. Both are tested against this stateless mount. Use a fresh
client context for each connection and let the supported SDK negotiate; a legacy
session identifier is never authentication or retained hfcache work. There is no
hfcache SSE event feed, task/job receipt, background execution, resource/prompt
interface or server-side resumption history. Closing a connection stops
observation; an already running bounded read may finish before its lease releases.

[Official client lifecycle/negotiation](https://gofastmcp.com/clients/client),
[explicit HTTP transport/trust](https://gofastmcp.com/clients/transports) and
[bearer authentication](https://gofastmcp.com/clients/auth/bearer) references were
checked against locked 4.1.1. Upstream OAuth/STDIO/in-memory/task examples do not
add those interfaces or authority to this server. A desktop/browser client that
requires OAuth discovery cannot use this pre-provisioned endpoint automatically.

## Available tools

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
| `get_verification_report` | Required run_id; limit/cursor | Existing VerificationReport only; wrong report type refuses HFARG004; no archive-byte hashing or persistence |
| `estimate_verification` | None | Existing stat/metadata estimator, no archive-byte hashing/writes/Hub/lock or increase in verification confidence; large scans remain bounded work |

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
Read-only annotations describe this boundary; the narrow read capability and
request validation enforce it.

## Authentication and rotation

Authentication sources are loaded at startup, not watched. Replacing the source
file alone does not revoke an in-memory old credential. An operator provisions a
new distinct MCP secret, follows the existing API drain/restart procedure with
that source, then recreates clients so they reread it. No session ID bridges the
rotation. Verify old credentials refuse, the new credential sees the exact nine
tools and separate REST credentials retain their own authority. Do not give the
private verification worker the MCP source or use the REST token as a workaround.


## Resource costs and troubleshooting

A small page limits output entries, not the work required to validate underlying
metadata. Each page uses fresh policy and bounded authoritative readers; a large
inventory scan or a fully parsed immutable manifest/report can cost substantial
filesystem I/O even for `limit=1`. None of this verifies archived payload hashes
or increases confidence. Prefer sequential bounded walks; do not increase
concurrency merely because tools have read-only hints.

| Server limit | Default and consequence |
| --- | --- |
| Request bytes | 1 MiB strict JSON; unknown argument fields still refuse |
| Page entries | Omitted limit resolves to 100; configured maximum is 1000, within the allowed 1–10,000 range |
| Metadata scan | 10,000 aggregate entries and 64 MiB per-artifact/aggregate bytes; smaller pages cannot bypass a full-source validation budget |
| Encoded response | 8 MiB before headers, checked again after sanitization; even one large header/entry may refuse |
| Shared metadata work | Four workers plus 32 pending slots, shared with REST metadata |
| MCP in-flight transport | Separate 36-request default ceiling, reserved after auth before body collection; active canceled observers may retain ownership until real completion |

Values are restart-only [server resource settings](server.md#resource-settings),
not tool parameters or permission to exceed limits. Counts are not an integrity
percentage, reservation or archive-wide snapshot. Classified failure may be a
parent HTTP Problem or MCP `isError` tool result; HTTP 200 alone is insufficient.
Never replace a failed page with an empty successful page. The example prints
only fixed safe failure text; codes below describe classified server responses,
not a promise that arbitrary SDK errors are shown. Use bounded safe server
diagnostics rather than enabling raw rejected-value/debug output.

| Symptom | Safe interpretation / next check |
| --- | --- |
| No MCP endpoint or disabled-client refusal | Check deliberate enablement, canonical `/mcp/` and the public prefix; disabled MCP sources are inert, and authentication can refuse before any 404 |
| Enabled startup HFCFG005 or credential failure | Install the selected optional release profile and provision the distinct source before normal restart; do not expect fallback or copy a REST/Hub token |
| 401 / HFAPI001 | Missing, stale or wrong-class bearer; load the protected MCP source and recreate the client after rotation; a session ID is insufficient |
| Host/Origin/TLS/proxy refusal / HFAPI010 | Check the actual authority, configured allowlists, public prefix and verified proxy path; forwarded headers cannot manufacture native Unix access |
| TLS trust failure | Use the correct hostname and trusted CA file; never disable verification |
| 307, noncanonical slash or query rejection | Supply the exact `/mcp/` URL with no query/userinfo/fragment; the example does not follow redirects |
| HFAPI006 or fixed invalid-arguments ToolError | Use the exact tool schema and bounded typed fields; no arbitrary path/URL/credential/job field is permitted |
| HFAPI007 or continuation refusal | A tool/scope/policy/visible source changed, or the name is unsupported; discard partial aggregation and restart a fresh metadata walk |
| HFARG004 or missing/stale immutable evidence | Check the exact run/report kind or pinned SHA/publication; never substitute a newer current instance inside the old attempt |
| HFAPI005, response-size refusal or page limit | A bounded scan/artifact/wire/client budget was exhausted; fewer entries may help output size, but only an operator can review server budgets and a huge header/full-source scan may still refuse |
| HFAPI009 / temporary saturation | Wait and retry a read under finite bounds; do not create jobs, parallel unbounded retries or change credentials |
| Unknown schema, timeout or disconnect | Refuse incomplete output, close/recreate the client and repeat discovery if needed; no MCP execution receipt, replay/cancel or automatic recovery is involved |
| Unverified/unknown catalog state | Honest missing/stale evidence, not a failed request or authorization to rebuild; only separately authorized actual verification can establish confidence |

## Deployment profiles

| Installation | Enablement and source |
| --- | --- |
| Base reader or REST-only | MCP is disabled by default; no optional import, source resolution or mount occurs |
| Native service | Stage with explicit `--with-mcp`, install server and MCP extras, set `mcp_enabled=true`, and deliberately deliver a distinct protected source |
| Selected rootless template | Already sets `mcp_enabled=true`; the fixed helper mounts the named Podman MCP-reader secret at `/run/secrets/hfcache.mcp-reader` |

For native builds, `scripts/install-release.sh --with-mcp` selects the optional
closure only during build/stage; it refuses list/switch combinations. It neither
changes configuration nor starts services, and cannot add packages to a switch
target. Default native staging remains server-only. Enabled startup without the
optional package or usable distinct source fails closed.

The native example selects `[credentials.mcp_reader]` with
`systemd_name = "hfcache.mcp-reader"`. Default native units do not import this
optional source. After provisioning the encrypted credential, a deliberate native
API-service drop-in can deliver it:

```ini
[Service]
LoadCredentialEncrypted=hfcache.mcp-reader:/etc/credstore.encrypted/hfcache.mcp-reader
```

A protected explicit `file` source is the alternative. This is separate from the
rootless helper's file-mounted Podman secret delivery; host `ImportCredential`
is not the container source. See [server credentials](server.md#credentials-and-capabilities)
and [container roles](containers.md). The private verifier receives no REST, MCP
or Hub credential; custom source locations require explicit isolation acceptance.

Rollback to a server-only or pre-MCP runtime requires deliberately disabling MCP
before normal drain/restart. There is no automatic fallback or schema migration.
Preserve previous trees, receipt stores, scheduled handles and shared lock inodes.
The selected deployment remains guarded/read-only; see the dated
[deployment status](deployment-status.md) for recorded scope and outstanding
NAS, isolation, consumer and browser acceptance. Repository fixtures do not prove
installed SELinux/NFS, credential delivery, cgroups or real drain/rollback.

## Disposable example workflow

The mounted example fixture creates its own archive, protected synthetic bearer,
API/control state and loopback listener. Run the bounded discovery workflow from
a locked checkout without a deployed service or archive mount:

```bash
uv run --locked --extra server --extra mcp pytest \
    tests/unit/test_mcp_client.py \
    -k test_example_walks_actual_mounted_pages_and_one_exact_publication --no-cov
```

For its four repositories and selected `model:alpha/model`, page size 1 reads
current once and then three file pages and two dependency pages at that exact
publication. Both supported negotiation modes run over disposable HTTP and TLS.
The example's successful output is:

```json
{"kind":"discovery_summary","manifest_dependencies":2,"manifest_files":3,"metadata_pages":10,"repository_count":4}
```

A timeout, exhausted page/byte budget, changed identity or failed page emits the
fixed safe diagnostic, exits 1 and produces no partial summary. Restart discovery
as a new attempt; do not splice pages from different attempts.

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
creates an authorization bypass or an execution receipt. The transport uses
`json_response=True`: each response is finite JSON, not a retained SSE feed. The locked SDK handles
POST/DELETE; stateless GET is authenticated before its method refusal. Both the
outer registry and supported production FastMCP verifier enforce MCP-only class
authority on every request. No OAuth discovery routes are mounted. Modern and legacy SDK support does not provide OAuth-client compatibility.

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

## Read-only boundary

Tool schemas are closed. Unsupported names, arbitrary paths/URLs, credentials,
mutation fields and execution RPCs refuse. The locked SDK may ignore legacy
`params.task` metadata on an otherwise valid read: that still performs an ordinary
finite synchronous read, with no task handle, retained task, job or state effect.
No resources/prompts or generic invocation interface is exposed.

The tool boundary is inside the shared API process, not a separate process sandbox.
Archive strings and dependency observations remain untrusted data, never executable
instructions. Unknown catalogs stay unknown; reads do not repair evidence or
rebuild derived state. Metadata/credential digest hashing is distinct from hashing
archived payloads. Ordinary sanitized logs and filesystem atime effects do not
constitute archive or operation-state mutation.

Cancellation closes observation but an active bounded read can retain its transport
slot and worker lease until actual completion. Shutdown joins that work before
releasing instance ownership. Concurrent authorized REST mutations belong to those
commands; MCP adds no admission, Hub request, credential resolution or artifact.

## Tool argument reference

These are exact schema field names. Required arguments must be supplied; optional
arguments use the defaults and bounds above. Names absent here are rejected.

| Tool | Required fields | Optional fields |
| --- | --- | --- |
| `get_archive_status` | `[]` | `["selectors", "repository_type", "limit", "cursor"]` |
| `list_repositories` | `[]` | `["selectors", "repository_type", "limit", "cursor"]` |
| `list_revisions` | `[]` | `["selectors", "repository_type", "limit", "cursor"]` |
| `get_current_reference` | `["repository_type", "repository_id"]` | `[]` |
| `get_revision_manifest` | `["repository_type", "repository_id", "commit_sha", "publication_id"]` | `["collection", "limit", "cursor"]` |
| `list_run_reports` | `[]` | `["limit", "cursor"]` |
| `get_run_report` | `["run_id"]` | `["limit", "cursor"]` |
| `get_verification_report` | `["run_id"]` | `["limit", "cursor"]` |
| `estimate_verification` | `[]` | `[]` |
