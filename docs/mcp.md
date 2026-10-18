# Optional MCP metadata interface

MCP-001 adds an optional authenticated Streamable HTTP transport after committed
REST acceptance. MCP-002 adds the explicit nine-tool metadata read interface,
with repository acceptance recorded in its task. No command/job interface is exposed.
[Decision 124](adr/decision-124.md) records dependency/auth/lifecycle rationale;
the [transport task](agents/plans/tasks/mcp-001-mount-authenticated-fastmcp.md) owns its
acceptance evidence. [Decision 125](adr/decision-125.md) and the
[tool task](agents/plans/tasks/mcp-002-curated-read-only-tools.md) own curated exposure
and its registry/schema/side-effect proof.
MCP-003 supplies mounted security/side-effect evidence; MCP-004 completes the
protected-file client and required build acceptance. The
[acceptance task](agents/plans/tasks/mcp-004-mcp-client-docs-and-acceptance.md) records
actual runs. MCP repository acceptance is complete; final API-017 closure and
installed-host operator holds remain separate.

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

## Protected-file example client (MCP-004)

[`examples/mcp-client.py`](../examples/mcp-client.py) is a deterministic metadata
client for the locked FastMCP 4.1.1 interface. It does not run an agent, accept a
command/tool name, discover credentials or install anything. An operator must
first provision a distinct MCP-reader secret through the protected file rules in
[server authentication](server.md#implemented-credential-and-capability-boundary-api-005).
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

This is an operator-adapted setup example, not a command run on the production
archive. Choose the real authority, public prefix, protected source and archive
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
remains the [consumer workflow](consumers.md#mcp-metadata-discovery-mcp-002).
No archive mount/config, Hub credential, REST writer token or local mutation
fallback is required or used.

Each received response is capped at 16 MiB by the example, under one deadline;
the server's smaller configured cap still applies. It disables redirects,
ambient proxies and implicit credential discovery, retains certificate
verification and caches no credential or result to disk. Errors use fixed safe
diagnostics rather than rejected input or SDK tracebacks. These client bounds do
not expand server budgets or authorize execution. Actual positive/negative
example execution belongs to the MCP-004 task evidence.

### Wire, sessions and reconnect

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

### Rotation and disabled operation

Authentication sources are loaded at startup, not watched. Replacing the source
file alone does not revoke an in-memory old credential. An operator provisions a
new distinct MCP secret, follows the existing API drain/restart procedure with
that source, then recreates clients so they reread it. No session ID bridges the
rotation. Verify old credentials refuse, the new credential sees the exact nine
tools and separate REST credentials retain their own authority. Do not give the
private verification worker the MCP source or use the REST token as a workaround.
These are operator acceptance instructions, not service changes performed here.

When disabled, no MCP package/source/endpoint is required and REST auth/lifecycle
stays independent. Enabling needs both installed extras and a usable distinct
source before startup. The default packaged unit does not import an optional MCP
credential; named-source delivery is the explicit drop-in above. Reverting to a
server-only/pre-MCP target requires deliberately disabling MCP before restart;
there is no automatic fallback, source copying or archive/config schema migration.

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
Registry/schema equality and before/after archive/control-state snapshots must
prove this for successful and failed mounted calls; annotations alone do not.

Archive/receipt/config schemas, domain algorithms and whole-archive authorization
are unchanged. Local socket/streaming tests and locked wheel installs do not prove
deployed systemd/cgroup credentials, no-IP masks, browser/PAM, SELinux/NFS or
rollback/drain acceptance. Existing [operator holds](agents/progress.md#operator-handoff)
remain deployment prerequisites; no production operation is authorized.

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

## Threat, control and test traceability (MCP-003)

These are required acceptance claims under decisions 124/125 and INV-002/003/
007/010/016. The [MCP-003 task](agents/plans/tasks/mcp-003-mcp-security-and-side-effect-tests.md)
owns executed results; a listed control or test reference alone is not evidence
that its latest run passed. Mounted tests must enter the parent FastAPI lifespan
and use supported streaming HTTP or disposable sockets, not only direct SDK calls.

| Threat or failure | Required control and observable refusal | Concrete test entry point |
| --- | --- | --- |
| Missing/cross-class bearer, reused session identity or protocol-method bypass | Authenticate each request before body/protocol handling; an MCP bearer cannot reach REST and a session ID grants no authority | [test_every_mounted_method_authenticates_before_protocol_or_session_use](../tests/unit/test_mcp_transport.py), [test_stateless_handshake_issues_no_session_authority_and_every_followup_reauthenticates](../tests/unit/test_mcp_transport.py) |
| Host/Origin/prefix/proxy confusion | One trusted interface projection and corroborated Unix scope retain transport policy; alias redirects cannot reflect caller data | [test_real_unix_native_and_tcp_public_mcp_share_one_authenticated_lifespan](../tests/unit/test_mcp_transport.py), [test_slash_alias_is_authenticated_and_cannot_reflect_query_or_proxy_prefix](../tests/unit/test_mcp_transport.py) |
| Writer name, hidden tool/resource/prompt, generic invocation or mutation-shaped arguments | Exact nine-name registry and typed closed schemas; unsupported tool spellings/tool-argument fields refuse without command or state effects | [test_actual_mounted_registry_has_exact_typed_allowlist_and_read_only_hints](../tests/unit/test_mcp_tools.py), [test_every_tool_rejects_mutation_fields_without_archive_or_control_writes](../tests/unit/test_mcp_security.py), [test_all_writer_command_names_and_generic_dispatch_aliases_are_unknown](../tests/unit/test_mcp_security.py), [test_resources_prompts_and_background_tasks_cannot_expand_the_registry](../tests/unit/test_mcp_security.py) |
| A read creates reports, receipts, directories, locks, caches or recovery output | Narrow read capability plus per-call archive/control-state snapshots and command/Hub/credential/archive-byte-hash tripwires; hints alone are insufficient | [test_every_success_and_failed_tool_preserves_archive_and_operation_state](../tests/unit/test_mcp_tools.py), [test_exact_registry_and_valid_reads_preserve_archive_control_and_runtime_directories](../tests/unit/test_mcp_security.py) |
| Malformed or stale evidence becomes authority or a newer publication is substituted | Validate original evidence and exact identity before projection; refuse malformed/wrong-kind/stale data, never reconstruct it or infer confidence | [test_exact_manifest_never_substitutes_current_after_stale_or_unsafe_identity](../tests/unit/test_mcp_tools.py), [test_verification_report_requires_actual_verification_evidence](../tests/unit/test_mcp_tools.py), [test_corrupt_original_reports_refuse_without_repair_or_diagnostic_echo](../tests/unit/test_mcp_security_evidence.py) |
| Secret or rejected input escapes in output, errors, cursor hashes or SDK logs | Registered-value sanitization before encoded output/hash, fixed safe errors/diagnostics and no raw rejected-value formatting; unsafe identities refuse | [test_archive_strings_remain_inert_data_and_registered_tokens_never_reach_tool_outputs](../tests/unit/test_mcp_tools.py), [test_malformed_protocol_does_not_echo_rejected_values_in_output_or_diagnostics](../tests/unit/test_mcp_transport.py), [test_numeric_registered_secret_changes_do_not_fingerprint_report_cursors](../tests/unit/test_mcp_security_evidence.py), [test_registered_secret_in_actual_report_response_is_redacted_or_refused](../tests/unit/test_mcp_security_evidence.py) |
| Large metadata/slow body/read consumes unbounded work or returns truncated success | Explicit body/scan/artifact/page/response ceilings and bounded transport/shared metadata capacity; exhaustion is visible failure and ownership releases safely | [test_actual_mounted_protocol_enforces_byte_budgets_and_recovers_capacity](../tests/unit/test_mcp_transport.py), [test_exhausted_metadata_budget_is_visible_failure_never_an_empty_success](../tests/unit/test_mcp_tools.py) |
| Missing catalog or partial archive becomes a false verified result | Preserve unknown instance-bound confidence; reads never hash archive content, persist findings or rebuild catalog state | [test_bad_derived_catalogs_stay_unknown_and_are_never_rebuilt](../tests/unit/test_mcp_tools.py), [test_partial_archive_estimate_reports_missing_bytes_without_hashing_or_false_confidence](../tests/unit/test_mcp_tools.py) |
| Observer cancellation, mixed REST/MCP work or shutdown loses active read ownership | Offload through the shared bounded pool, keep independent correlation and retain a worker lease until actual completion; drain before releasing lifecycle ownership | [test_blocked_estimator_uses_shared_pool_without_blocking_metadata_or_leaking_slots](../tests/unit/test_mcp_pool.py), [test_parallel_mcp_reads_during_rest_sync_and_verification_keep_ids_and_authority](../tests/unit/test_mcp_concurrency.py), [test_cancelled_mcp_observer_keeps_metadata_lease_until_worker_finishes](../tests/unit/test_mcp_concurrency.py), [test_shutdown_after_cancelled_mcp_read_waits_for_worker_and_instance_ownership](../tests/unit/test_mcp_concurrency.py) |
| Disabled MCP gains a dependency, credential read or endpoint | Disabled mode imports/resolves neither optional runtime nor MCP source; isolated base/server installations remain usable | [test_disabled_mcp_neither_reads_inert_credential_nor_mounts_endpoint](../tests/unit/test_mcp_transport.py), [isolated wheel profiles](../scripts/check-installations.py) |

The locked SDK may ignore legacy top-level `params.task` metadata on an otherwise
valid allowlisted `tools/call` and perform the ordinary finite synchronous read.
The accepted behavior is no task handle, retained task, operation/job or state
effect, not blanket refusal of every optional protocol field. Unsupported task
RPC methods refuse; mutation-shaped fields inside the tool's arguments remain
closed and refuse. `task=False` and hints describe no background authority, not a
promise about every SDK extension field.

Malformed original report proof covers run/recovery/verification evidence and
JSON, version, run/archive/time identity, symlink and duplicate-file damage.
[test_unexpected_reader_exception_is_masked_over_actual_http_and_in_diagnostics](../tests/unit/test_mcp_security_evidence.py)
requires fixed safe failure over the actual mounted boundary and captured logs.
Registered string report values redact; unsafe registered numeric values may
refuse at the parent boundary with HFAPI008/HTTP 500 rather than return changed
or exposed evidence. The numeric cursor substitution test independently proves
that hidden numeric values do not enter client-visible continuation fingerprints.

Repository proof completed 2026-10-18 with the first full gate exiting 0; the task
records 3,522 Python tests, all three locked wheel profiles and 127 Cockpit tests.
Dedicated MCP client/final acceptance remains MCP-004. No runtime behavior or
architectural decision changed in this proof package.

### Snapshot and concurrency method

No-hash assertions concern verification/ingestion hashing of archived payload
bytes. Cursor hashing of sanitized metadata and credential-digest authentication
remain intentional and are not archive verification.

Take application-state baselines after ordinary lifespan initialization and
credential loading. For every valid/invalid tool, compare all relevant archive
and operation-state paths, ordinary file contents and modes, including refs,
manifests, object/publication content, catalogs, reports, journals and pending
operation evidence. Adding a path is a change even when no existing file changed.
Do not treat filesystem atime updates as application writes. Normal sanitized
operational logging is the documented exception; it cannot create archive or
operation evidence. Test fixtures may deliberately corrupt evidence before the
baseline to verify fail-closed behavior, but the read must preserve that evidence.

During a concurrent REST command, its authorized fixture mutations remain
attributable to that command. MCP must add no admission/domain/Hub/credential/
archive-byte-hash invocation or derived artifact. Responsiveness alone does not prove this
boundary. Distinct request/run correlation must survive overlapping reads, and
cancellation closes observation without treating a still-running read as finished.
The supported streaming observer may detach while the server conservatively
retains both its transport request slot and metadata-worker lease until actual
completion. Shutdown may join at the MCP layer before the REST pool closes;
neither observer cancellation nor a pending drain proves capacity is already free. Pages remain bounded
observations rather than a global archive snapshot; status headline/warnings may
change between pages while row-bound cursors remain valid.

### Residual deployment assumptions

The narrow tool capability is an application boundary inside the shared API
process, not a separate process sandbox. The MCP credential intentionally reads
the whole archive, including restricted metadata. No per-repository ACL or individual attribution is claimed. A trusted
client must protect its provisioned bearer and use verified TLS or the protected
authenticated Unix path; session identifiers are not credentials. Exposed names,
report messages and dependency observations remain untrusted data even after
successful validation, never instructions to execute.

Hermetic mounted/streaming/socket tests and archive snapshots prove application
behavior under the tested process and filesystem conditions. They do not certify
installed socket ownership, TLS/proxy deployment, credential delivery/rotation,
worker no-IP/source masks, cgroups, custom source paths, SELinux/NFS, browser/PAM
or real drain/rollback behavior. Dependency/parser/SDK compromise and privileged
host/operator compromise remain outside the narrow tool capability proof. Keep
[operator holds 16–18](agents/progress.md#operator-handoff) open until separately
performed; no production operation or hardening change is part of these tests.

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


MCP-004 client/packaging acceptance uses [the runnable example](../examples/mcp-client.py),
[actual example socket tests](../tests/unit/test_mcp_client.py),
[negative client/trust/budget tests](../tests/unit/test_mcp_client_security.py) and
[REST/rotation/packaging acceptance](../tests/unit/test_mcp_acceptance.py). The
[MCP-004 task](agents/plans/tasks/mcp-004-mcp-client-docs-and-acceptance.md) owns precise
commands/counts and the required --with-build gate, including all implemented
extras, three real locked wheel profiles and Cockpit. Cold base/REST-only imports,
unchanged verifier no-IP/credential/timer policy and disabled/enabled REST parity
are repository claims; operator-only deployment holds are not inferred passes.
