# Writer REST API contract

Status: API-006 implements the authenticated metadata resources below under
[the active plan](plans/2026-10-17-plan-rest-api-and-mcp.md). Job/write routes,
candidate operations and API-backed public CLI migration remain planned. No
production installation or listener start is asserted by implementation evidence.

## Service and transport boundary

Decision [108](adr/decision-108.md) introduces ordinary typed query/command
services. Typer, FastAPI, and later FastMCP are adapters; they never call each
other, run the public CLI, or parse its stdout. Archive algorithms, FS/TX
requirements, sentinel identity, local flock, and publication authority remain
unchanged. HTTP metadata is not artifact transfer: locators are relative to
`published/` and identify exact immutable publication instances (FS-12).

All routes below have prefix `/api/v1`. R permits a REST reader or writer;
W requires a REST writer. MCP credentials authorize no REST requests.
Short queries return typed data; heavyweight calls return durable receipts
and eventually the exact schema-1 CLI Envelope. Auth precedes all reads,
including health, docs, and OpenAPI. Interactive docs default disabled.

## Operation parity matrix

This table is the machine-readable parity source. Test columns are explicit
pending evidence rather than claims that a proposed route works. Preserve
one row for each mode when filling them. `archive` means the cross-process
local flock through all domain persistence; `worker archive` means that same
lock is owned by the offline executor. A preview cannot grant apply authority.
An implemented read row means its HTTP resource exists; the public CLI still
uses its local service until API-011–013 migrate it.

| CLI mode | Service | Route | Role | Lock | Hub | Execution | Effects | CLI test | API test | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| version --server | version | GET /version | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| capabilities | capabilities | GET /capabilities | R | none | no | Q | none | pending CLI migration | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| config validate (installed) | validate_config | POST /config/validate | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | pending | planned |
| config validate --config (candidate) | validate_candidate | POST /config/validate | W | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | pending | planned |
| archive init --inspect | inspect_archive | GET /archive/inspection | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| archive init --confirm | initialize_archive | POST /archive/initializations | W | archive | no | J | receipt; initial layout/sentinel | pending | pending | planned |
| doctor --read-only | diagnose | POST /diagnostics | R | none | explicit | J | receipt only | pending | pending | planned |
| doctor (probes) | diagnose | POST /diagnostics | W | archive | explicit | J | receipt; temporary health probes | pending | pending | planned |
| plan (installed) | plan_sync | POST /plans | R | none | yes | J | receipt only | pending | pending | planned |
| plan --config (candidate) | plan_candidate | POST /plans | W | none | yes | J | receipt only | pending | pending | planned |
| sync | synchronize | POST /syncs | W | archive | yes | J | receipt; journals/cache/publication/catalog/report | pending | pending | planned |
| status [selectors] | archive_status | GET /status | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| list [selectors] [--type] | list_repositories | GET /repositories | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| list --revisions [selectors] [--type] | list_revisions | GET /repositories/revisions | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| verify --estimate | estimate_verification | GET /verification/estimate | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| verify --new [--run-id] | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | pending | pending | planned |
| verify --full | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | pending | pending | planned |
| verify --revision | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | pending | pending | planned |
| prune --dry-run | preview_prune | POST /prune-plans | R | none | no | J | receipt only | pending | pending | planned |
| prune --apply | apply_prune | POST /prunes | W | archive | no | J | receipt; guarded domain mutation/audit | pending | pending | planned |
| purge --dry-run [selectors XOR --all-unmanaged] | preview_purge | POST /purge-plans | R | none | no | J | receipt only | pending | pending | planned |
| purge --apply [selectors XOR --all-unmanaged] | apply_purge | POST /purges | W | archive | no | J | receipt; guarded domain mutation/audit | pending | pending | planned |
| recover --dry-run | preview_recovery | POST /recovery-plans | R | none | no | J | receipt only | pending | pending | planned |
| recover --apply | apply_recovery | POST /recoveries | W | archive | no | J | receipt; guarded domain mutation/audit | pending | pending | planned |
| quarantine --dry-run IDs | preview_quarantine | POST /quarantine-plans | R | none | no | J | receipt only | pending | pending | planned |
| quarantine --apply IDs | apply_quarantine | POST /quarantine-cleanups | W | archive | no | J | receipt; guarded domain mutation/audit | pending | pending | planned |
| repair TYPE:ID@SHA [--reason] | repair_revision | POST /repairs | W | archive | yes | J | receipt; guarded domain mutation/audit | pending | pending | planned |
| reports/references/manifests | read_evidence | GET /runs; GET /runs/{run_id}; repository subresources | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py; tests/unit/test_query_boundary.py | implemented |
| operations show/wait/lookup | observe_operation | GET /operations; GET /operations/lookup; GET /operations/{id}[/result or /events] | R | none | no | Q | none | pending | pending | planned |

Local `version`, help, `serve`, and `config validate --local` are explicit
bootstrap commands, outside remote operation parity. API-backed commands reject
Hub token overrides. Selectors retain existing grammars and unmanaged-repository
exceptions. Sync is explicitly included here (the draft's §4 table omitted it).

## Shared query results (API-002)

Transport-neutral local queries share orchestration with the CLI and implemented
HTTP metadata routes. `LocalQueries` receives one frozen policy snapshot and
`ExecutionContext` captures execution identity; `ServiceResult` carries payload, problems, classification
and run correlation without rendering. `MetadataQueries` is the narrow read
interface implemented by `LocalQueries`; it offers no command or credential
resolver. Config-validation payload construction takes an already resolved
credential source, never a token value.

Status/list retain schema-1 payload keys, deterministic ordering and unknown
verification confidence. Status covers configured plus unmanaged published
repositories; selectors unknown to both fail HFARG004. Missing/corrupt derived
repository catalogs never authorize a rebuild. ID-based report, reference and
manifest reads reject identity mismatch and unsafe paths and retain exact
publication identity and `published/`-relative locators. API-006 wire
pagination/projections remain separate from these domain results.

API-006 strengthens the shared local read boundary with descriptor-relative
no-follow traversal and optional `QueryBounds`. HTTP supplies finite entry,
artifact and total-byte budgets; a refusal is `HFAPI005`, never an empty or
silently truncated success. Default local CLI queries retain complete results
without artificial transport ceilings. Status/list/latest-run/catalog reads and
the health/estimate paths use the same safe reader. Missing/corrupt derived
catalogs retain unknown verification confidence and grant no rebuild authority.
Latest-run summaries ignore unreadable or identity-mismatched informational
reports; exact report reads refuse them. Reports check the configured archive
UUID, filename/time and run ID. The verification catalog has no archive-ID field;
safe parse/containment and exact publication-instance keys govern its derived
confidence. References/manifests check repository, SHA, publication identity,
generation and canonical locators. These metadata checks do not assert that
every read revalidates the archive sentinel. Policy pins configured root/UUID;
archive inspection remains a separate diagnostic and performs no repair.

API-003 adds `CommandServices` and immutable requests for the command rows above.
These services preserve domain ordering and classified partial results; public
commands own the common archive lock once. Adapters and later operation runners
must call them without an outer archive lock. Verification persistence now stays
inside its lock/preflight boundary (decision 110). This establishes local service
behavior only: HTTP routes and remote CLI modes remain planned until their
implementing acceptance tasks complete.

## Implemented metadata resources (API-006)

All paths below use `/api/v1` and require a REST reader or writer bearer.
Repository IDs have two separately validated path components, `{namespace}` and
`{name}`; `{repository_type}` is `model` or `dataset`. Full SHAs and publication/
run IDs retain domain grammars. No path parameter is an arbitrary filesystem path.

| GET resource | Result in `envelope.data` | Pagination |
| --- | --- | --- |
| `/version` | Existing local version payload; no archive-policy read per request | none |
| `/capabilities` | API/instance identity, credential class/capabilities, enabled read features and maximum page size; operations/MCP remain false | none |
| `/health` | Daemon readiness, policy-validation state and read-only archive inspection when available | none |
| `/status` | Archive headline plus repository status rows | `repositories` |
| `/repositories` | Published inventory, including unmanaged repositories | `repositories` |
| `/repositories/revisions` | Flat rows containing `repository_type`, `repository_id` and each retained revision's existing fields | `revisions` |
| `/verification/estimate` | Existing estimate payload; no hashing, lock, persistence or Hub | none |
| `/archive/inspection` | Read-only initialization inspection and classified domain problems | none |
| `/runs` | Report IDs in reverse chronological filename order | `runs` |
| `/runs/{run_id}` | Validated existing `report`; preserves that report's domain run ID | bounded JSON stream |
| `/repositories/{repository_type}/{namespace}/{name}/references/{revision}` | `reference` plus `locator_base="published/"`; revision is `current` or a full SHA | none |
| `/repositories/{repository_type}/{namespace}/{name}/manifests/{commit_sha}/{publication_id}` | Exact `manifest` plus `tree_base="archive-root/"` | bounded JSON stream |

`health.ready` describes the daemon, not archive integrity, mount proof or
initialization. `policy_valid` is true after a valid fresh snapshot, false on a
classified failed policy/inspection, or null when query capacity prevents that
diagnosis; `archive` may be null. Health returns diagnostics without repairing,
probing writability or reconstructing a catalog. Version/capabilities remain
available if installed archive policy later becomes invalid. Startup still
requires valid server configuration/credentials and an initial installed policy.

### Read and problem wire models

[`ReadResponse`](../src/hfcache/api/models.py) is separate from durable schemas:

| Field | Meaning |
| --- | --- |
| `schema_version` | Wire wrapper version `1` |
| `request_id` | Authoritative server-generated ID for this HTTP request |
| `archive_id` | Fresh snapshot UUID, or startup-pinned configured UUID for policy-independent/fallback diagnostics; never a sentinel-proof claim |
| `config_fingerprint` | Existing archive-policy fingerprint, or null when no fresh snapshot was used |
| `envelope` | Complete schema-1 Envelope, or an explicitly paged piece of its data |
| `next_cursor` | Opaque next-page token, or null |

The Envelope retains domain warnings/errors, exit classification, command and
run identity. Archive inspection can return HTTP 200 with a failed domain
Envelope; a transport success does not make the archive healthy. Report reads
use the existing report's run ID while request correlation remains independent.
Future CLI clients reconstruct paged arrays and retain the first Envelope's
invocation metadata. For `list --revisions`, combine inventory rows with revision
pages grouped by repository; the transport does not silently discard inventory
metadata or claim the current CLI is already remote.

`ApiProblem` has exactly `request_id`, `code`, safe `message` and `exit_code`.
It contains no framework input echo, raw artifact context, exception or traceback.
Every HTTP response carries `X-Request-ID`, `Cache-Control: no-store`,
`X-Content-Type-Options: nosniff` and a frame-ancestor CSP. Incoming request IDs do
not choose authoritative correlation. Authentication precedes known/unknown
routes, method errors, docs/schema and request-body validation.
Noncanonical trailing-slash paths return an error without automatic redirects,
so a rejected query is never reflected into a Location header. OpenAPI and the
optional docs HTML obey the same normal response byte ceiling.

### Query parameters and page ordering

Status, repository inventory and revision pages accept repeated `selector`
values using domain `TYPE:ID`, optional `type=model|dataset`, `limit` and `cursor`.
Report inventory accepts only `limit` and `cursor`. Other read routes reject all
query parameters. Unknown keys, repeated scalar parameters, coercive numeric
forms and malformed domain values fail safely. `limit` is a positive ASCII
decimal integer, default `100`, capped by `limits.max_page_size`; at most `100`
selectors of at most `256` characters are accepted. Cursors are at most `256`
characters. The raw query is capped at `8192` bytes and total header name/value
bytes at `32768`. Read routes accept no nonempty body; the byte limit is enforced
even without Content-Length.

Status preserves configured order followed by unmanaged publication order;
inventory uses canonical repository order, revisions use that order followed by
retained publication generation, and report IDs use reverse timestamped filename
order. Offset cursors bind route/filter scope, policy fingerprint and a digest
of the sanitized paged array. Changed scope/policy/array or an offset beyond the
current result returns 409; malformed encoding returns 422. Restart the walk
after a stale-cursor refusal. Cursor contents are not an authorization grant.
Walk until `next_cursor=null`; page sequences are not an archive-wide snapshot
and ancillary fields can change independently of the paged array. No page silently substitutes a newer exact
publication or truncates a legacy result.

### Response and evidence budgets

Normal JSON responses are capped at `limits.max_response_bytes` (default 8 MiB).
Shared metadata work is bounded by `max_scan_entries` and per-artifact plus
aggregate bytes, each byte ceiling defaulting to `max_artifact_bytes` (64 MiB).
Exhaustion is `HFAPI005`/503, never an empty page or an unverified-to-verified
upgrade. A small returned page does not bypass the bounded underlying scan.

Reports/manifests are parsed and identity-validated within that source budget,
then stream a `ReadResponse` using incremental JSON encoding with chunks at most
8192 bytes. The encoded stream is pre-counted and capped at eight times the
configured artifact ceiling to allow JSON escaping/wrapper overhead. It retains
a bounded parsed representation in memory; it is not bulk file transfer or an
unbounded raw-file relay. Response-size refusal happens before headers, and the
metadata lease remains held through stream completion/disconnect.

## Execution correlation (API-004)

[Decision 111](adr/decision-111.md) separates four identities without changing
schema-1 archive records. A trusted server boundary mints a fresh `request_id`
for each received request; caller headers cannot select the authoritative ID.
Admission later mints an independent `operation_id`, shared by its submission,
observation requests and execution. A domain `run_id` continues to identify the
CLI Envelope and any durable run report. A `transaction_id` continues to identify
one archive journal; a run may contain several transactions. These IDs use the
existing 32-lowercase-hex grammar. A request is not a run or a transaction, and
retrying or polling an operation does not mint a replacement domain identity.
Receipt relationships and authenticated submitter metadata land in API-007/008.

`ExecutionContext` holds the run ID and optional request/operation IDs.
Its `activate()` scope binds an immutable `ContextVar` correlation snapshot and
restores the prior scope after success or failure. Command services activate
their context; adapters must scope local query work too. `emit` captures that
snapshot in the log record when the event is emitted, so delayed formatting
cannot borrow another request's identity. Reserved event, level and correlation
fields supplied by a call site cannot override the captured values. Each service
thread submission copies its own context through `submit_with_context`; the
existing sync producer now uses the same boundary. Reused workers retain no
completed request scope.

`configure_daemon` installs one request-neutral handler and level at startup;
repeated startup calls are idempotent. Requests never call CLI `configure` or
reset handlers. Quiet/verbose preferences belong to client rendering and bounded
event selection, not a process-wide logger level. The isolated CLI retains its
per-invocation startup configuration and stderr-only event output.

Shared verification constructs no Hub client or credential and never changes
`os.environ`. The removed scoped offline toggle cannot affect concurrent work.
`offline.initialize_offline_process()` is a startup-only primitive for the later
dedicated executor: call it before importing or using Hub libraries and retain
the flag for that process's lifetime. The helper does not deny IP sockets.
API-008/014 must separately establish the credential-free no-IP sandbox; no
ASGI-process verification fallback is permitted.

## Wire validation and errors

Wire models are separate from durable archive models. Forbid unknown keys,
coercion, conflicting modes, arbitrary paths, and oversized bodies, including
chunked bodies. Validate repository type/ID, full SHA, publication ID, run ID,
and transaction IDs with domain validators. Query strings have explicit
conversion to strict typed values. Bound strings, lists, query concurrency,
page sizes, report projections, and event buffers.

`ApiProblem` contains a request ID, stable code/message, and applicable exit
classification, never raw framework exception input or tracebacks. HTTP errors:
401 missing/invalid bearer with challenge; 403 wrong capability; 404 absent;
409 stale policy, conflicting key, or unfinished result; 422 invalid request;
503 full/draining/unavailable executor; 500 sanitized unexpected error. Unsupported
methods receive authenticated 405 with `HFAPI007`. Current read integrity
refusals use 409 and retain their domain HFVER code/exit classification.
A terminal failed domain Envelope is retrieved with HTTP 200 and retains its
application exit code (priority 40, 50, 30); HTTP success never means domain
success. New HFAPI client config/auth failures exit 10; unavailable or uncertain
execution exits 20.

The shared sanitizer removes sensitive keys, known Hub/bearer/signed-URL shapes
and exact registered credential values from diagnostic trees. Opaque tokens must
be registered when loaded, before use; arbitrary unknown strings cannot be
recognized as secrets. `Problem` snapshots sanitized diagnostics, and public
rendering plus exception string/repr paths sanitize again to cover late
registration or mutable legacy contexts. API-005 registers inbound API
credentials and API-006 applies the same boundary to response diagnostics and
validation/exception output.

Inventory, revisions, reports, operations, and events use bounded cursor pages
with deterministic ordering documented as each route lands. Clients walk all
pages to preserve complete legacy envelopes. Pages are not an archive-wide
snapshot. Ref/manifest reads pin exact publication identity; vanished instances
return a visible stale/absent result, never substitute a new current tree.
Existing large reports stream without unbounded duplicate buffers.

## Admission, idempotency, and lifecycle

Decision [109](adr/decision-109.md) permits a bounded non-resuming submission
registry, separate from archive journals. One heavyweight FIFO lane (16 pending
by default), bounded metadata pool, and separate daemon-instance lock; never
hold the archive flock for daemon lifetime. The process is single-worker,
without auto-reload. Heavy work runs outside the ASGI event loop.

Side-effecting submissions require `Idempotency-Key`. Persist a restrictive
atomic JSON receipt under service-private `/var/lib/hfcache/api/` before 202 or
execution. Bind principal identity and key to canonical route/body digest and
admitted policy fingerprint. Matching retries return the original operation
even after policy changes; conflicting requests return 409. Every retry/lookup
reauthenticates. Header-based lookup searches only the caller's namespace.

States: queued, waiting_lock, running, succeeded, failed, interrupted. Store the
exact terminal Envelope or reference durable evidence. One waiting budget covers
queue and lock time. Reload installed policy under lock and refuse stale scope
before mutation. No duplicate/nested lock acquisition. Verification delegates to
a private socket executor that owns its lock through report/catalog persistence.

Disconnect and Ctrl-C stop observation. They do not cancel accepted work. Clients
emit the nonsecret key before mutation submission and operation ID before wait,
even in quiet mode; stdout carries exactly one terminal Envelope. Sequenced
sanitized events are bounded, never arbitrary journald output.

Shutdown stops admission, drains/joins workers, and preserves receipts. Restart
never automatically reruns old queued/running work: reattach an exactly identified
surviving verifier or classify interrupted without fabricating a report. PID,
released lock, elapsed time, or disconnected client do not prove completion.
Terminal key/result retention defaults to 30 days. Never age out nonterminal or
ambiguous records; delete only validated owned terminal records. Expired/missing
history is uncertainty, not proof of nonexecution or permission to replay.

## Credentials and configuration

API-005 supplies strict configuration, credential loading, fixed capability
principals and a reusable FastAPI bearer adapter. API-006 authenticates all
metadata HTTP routes/errors/schema/docs and applies transport bounds. Jobs,
candidate operations and write endpoints remain planned.

| Credential class | Accepted interface | Core capability | REST read | REST write |
| --- | --- | --- | --- | --- |
| REST writer | REST | `read`, `write` | authorized | authorized, subject to maintenance/domain gates |
| REST reader | REST | `read` | authorized | 403 `HFAPI002` |
| MCP reader | Future MCP only | `mcp-read` | 401 `HFAPI001` | 401 `HFAPI001` |
| Absent, invalid or malformed bearer | none | none | 401 `HFAPI001` | 401 `HFAPI001` |

These capability results do not imply that a planned job/write route exists.
Cross-interface credentials are rejected as unauthenticated. Missing,
malformed and invalid authentication uses the same safe detail `Not authenticated`
and `WWW-Authenticate: Bearer realm="hfcache"`; capability refusal is `Forbidden`.
Configured missing/unsafe/racing/malformed API credentials are startup
`HFAPI003`; duplicate values across classes are `HFAPI004`. All four codes retain
the exit-10 authentication/configuration classification. No raw bearer or
credential-derived principal identifier is returned.

Separate strict versioned archive, server, and client config domains. Server
transport/auth changes require restart. Each request/admission freezes a freshly
loaded archive policy and nonsecret fingerprint; root/UUID changes fail closed
until restart. Invalid new policy fails archive operations while health/version
remain diagnostic. Candidate content is bounded TOML, never a server path.
Planning requires installed root/UUID/Hub/credential authority; only the installed
credential is resolved. Validation does not install a candidate.

Distinct protected bearer files/systemd credentials for REST writer, optional
REST reader, and later MCP reader. Reject duplicates, bound lengths, validate
ownership/type/mode, compare in constant time, redact opaque tokens everywhere.
API-005 opens credential files through pinned no-follow descriptors, validates
root/effective-user ownership, one hardlink and explicit protected modes, then
compares fixed-size digests over all three slots. Unconfigured optional classes
authorize nobody; every configured source must load. The
[server contract](server.md#implemented-credential-and-capability-boundary-api-005)
states token grammar/limits, file policy, rotation and exact configuration keys.
No ambient discovery or credential forwarding. Unix sockets still authenticate.
Local default socket is `/run/hfcache/api.sock`; TCP defaults loopback. Off-host
access requires verified TLS or an explicitly trusted local TLS proxy. Validate
Host/Origin, disallow wildcard CORS, URL userinfo and token queries, and explicitly
configure trusted proxies. Every reader is authorized for the entire archive
(AD-21); no per-repository ACL claim.

## Acceptance boundaries

[Server contract](server.md) owns deployment/lifecycle detail. API-016 must prove
complete REST, CLI, Cockpit, packaging, and offline tests before MCP code,
dependencies, imports or endpoints are added. Operator-only production checks
remain deployment prerequisites. This plan authorizes no production operations.
