# Writer REST API contract

Status: API-006 implements authenticated archive metadata and API-007 adds
bounded receipt/admission primitives and operation observation; API-009 adds
typed command routes under [the active plan](plans/2026-10-17-plan-rest-api-and-mcp.md).
Maintenance/initialization routes, candidate operations and API-backed public CLI
migration remain planned. No production installation or listener start is asserted
by implementation evidence.

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
| config validate (installed) | validate_config | POST /config/validate | R | none | no | Q | none | tests/unit/test_command_services.py; existing CLI suites | tests/unit/test_api_commands.py; tests/unit/test_api_command_adversarial.py | implemented |
| config validate --config (candidate) | validate_candidate | POST /config/validate | W | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | pending | planned |
| archive init --inspect | inspect_archive | GET /archive/inspection | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| archive init --confirm | initialize_archive | POST /archive/initializations | W | archive | no | J | receipt; initial layout/sentinel | pending | pending | planned |
| doctor --read-only | diagnose | POST /diagnostics | R | none | explicit | J | receipt only | tests/unit/test_command_services.py; existing CLI suites | tests/unit/test_api_commands.py; tests/unit/test_api_command_adversarial.py | implemented |
| doctor (probes) | diagnose | POST /diagnostics | W | archive | explicit | J | receipt; temporary health probes | tests/unit/test_command_services.py; existing CLI suites | tests/unit/test_api_commands.py; tests/unit/test_api_command_adversarial.py | implemented |
| plan (installed) | plan_sync | POST /plans | R | none | yes | J | receipt only | tests/unit/test_command_services.py; existing CLI suites | tests/unit/test_api_commands.py; tests/unit/test_api_command_adversarial.py | implemented |
| plan --config (candidate) | plan_candidate | POST /plans | W | none | yes | J | receipt only | pending | pending | planned |
| sync | synchronize | POST /syncs | W | archive | yes | J | receipt; journals/cache/publication/catalog/report | tests/unit/test_command_services.py; existing CLI suites | tests/unit/test_api_commands.py; tests/unit/test_api_command_adversarial.py | implemented |
| status [selectors] | archive_status | GET /status | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| list [selectors] [--type] | list_repositories | GET /repositories | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| list --revisions [selectors] [--type] | list_revisions | GET /repositories/revisions | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| verify --estimate | estimate_verification | GET /verification/estimate | R | none | no | Q | none | tests/unit/test_queries.py; tests/unit/test_query_evidence.py; existing CLI suites | tests/unit/test_api_reads.py; tests/unit/test_api_adversarial.py | implemented |
| verify --new [--run-id] | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | tests/unit/test_command_services.py; existing CLI suites | tests/unit/test_api_commands.py; tests/unit/test_api_command_adversarial.py | implemented |
| verify --full | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | tests/unit/test_command_services.py; existing CLI suites | tests/unit/test_api_commands.py; tests/unit/test_api_command_adversarial.py | implemented |
| verify --revision | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | tests/unit/test_command_services.py; existing CLI suites | tests/unit/test_api_commands.py; tests/unit/test_api_command_adversarial.py | implemented |
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
| operations show/wait/lookup | observe_operation | GET /operations; GET /operations/lookup; GET /operations/{id}[/result or /events] | R | none | no | Q | none | pending CLI migration | tests/unit/test_api_operations.py; tests/unit/test_operations.py; tests/unit/test_operation_store_adversarial.py | implemented |

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
inside its lock/preflight boundary (decision 110). API-009 exposes the command subset below through those services; maintenance,
candidate routes and remote CLI modes remain with their implementing tasks.

## Implemented metadata resources (API-006)

All paths below use `/api/v1` and require a REST reader or writer bearer.
Repository IDs have two separately validated path components, `{namespace}` and
`{name}`; `{repository_type}` is `model` or `dataset`. Full SHAs and publication/
run IDs retain domain grammars. No path parameter is an arbitrary filesystem path.

| GET resource | Result in `envelope.data` | Pagination |
| --- | --- | --- |
| `/version` | Existing local version payload; no archive-policy read per request | none |
| `/capabilities` | API/instance identity, credential class/capabilities, enabled read features and maximum page size; API-009 advertises `operations=true` for its implemented command subset and `operation_history=true`; MCP remains false | none |
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

## Implemented command resources (API-009)

Five explicit POST resources use shared services. They are management commands,
not arbitrary command/path dispatch. All reject query parameters and unknown
body fields. Every request authenticates before body reception; sync and
verification require writer capability before any body is read. Body-dependent
checks require writer capability before DTO validation when `candidate` is
present, or when diagnostics does not contain literal `read_only=true`.

| Route under `/api/v1` | Strict JSON object | Role/effect | Response |
| --- | --- | --- | --- |
| `POST /syncs` | `selectors` array, default `[]` | W; ordinary whole-run sync, archive mutation/automatic retention under the shared lock | Keyed job, 202 |
| `POST /verifications` | Required `mode`: `new`, `full` or `revision`; nullable `revision`/`run_id` as below | W; private offline verification, report/catalog persistence under worker-owned lock | Keyed job, 202 |
| `POST /plans` | `selectors` array, default `[]` | R; installed-policy Hub planning, no archive mutation/lock | Keyed job, 202 |
| `POST /diagnostics` | Required strict `read_only` boolean | R for `true`, W for `false`; Hub checks in both, write probes/lock only for `false` | Keyed job, 202 |
| `POST /config/validate` | Exactly `{}` | R; current installed-policy/credential-source validation, no Hub request, receipt or archive mutation | Immediate `ReadResponse`, 200 |

Sync/plan accept at most 100 selectors, each at most 256 characters, parsed by
existing repository validators and canonicalized as a sorted distinct repository
set before request hashing. Execution still follows installed configuration
order and enabled/continuation/capacity policy, never caller array order. Empty
selectors use all configured repositories. A missing configured repository is
reported by the existing service rather than silently substituted.
For sync/plan, a valid full-SHA suffix is validated then discarded when selecting
the repository, matching the existing service: it does not override that
repository's configured revision. The canonical digest uses distinct `TYPE:ID`
values, so duplicates, ordering and a valid unused suffix do not change scope.

Verification requires exactly one mode. A nonnull `revision` is required exactly
in revision mode and must identify `TYPE:ID@` a full lowercase 40-character SHA;
it is null or omitted otherwise. Nonnull `run_id` is optional only for new mode
and uses the existing 32-lowercase-hex
run grammar. These are selectors of existing domain evidence, not arbitrary
files. `estimate` is not an accepted job mode; use `GET /verification/estimate`.
New/full/revision all delegate to the private executor, which owns target
resolution, hashing, report persistence and catalog merge. The API bearer/Hub
credential is never forwarded there.

Diagnostics always requires an explicit boolean. A reader sending false,
missing mode or a non-boolean value receives 403 before DTO validation; a writer
with missing/invalid mode receives 422 and starts no probe. `read_only=true`
suppresses write probes but can resolve the installed Hub credential and contact
the Hub. Planning likewise resolves/tree-inspects through installed authority.
Both use the heavy lane and control-state receipts, so neither is an MCP metadata
read. Probing diagnostics retains the existing ability to diagnose uninitialized
storage without treating a missing sentinel as permission to initialize it.

### POST body boundary

Recognized command POSTs require exactly one `Content-Type: application/json`,
optionally `charset=utf-8` (quoted UTF-8 is accepted), and no `Content-Encoding`.
The body must contain a JSON object; `{}` is valid where the DTO permits it.
Empty bodies, arrays/scalars, invalid UTF-8 or escaped invalid Unicode, duplicate
keys, nonfinite constants, excessive nesting (maximum depth 32), unknown fields
and coercions fail safely. Shape/type failures use `HFAPI006`/422; shared selector
grammar refusals retain `HFARG001` with HTTP 422. Actual body bytes
over `max_request_bytes` are 413, including chunked bodies. Errors never echo
raw body, unknown keys, credentials or framework validation input. Unknown/read
routes retain their empty-body contract. Missing/invalid authentication takes
precedence over body reading, and a reader cannot send a malformed writer POST
to bypass the capability boundary.

### Admission model and exact results

The four job resources require exactly one valid `Idempotency-Key`. They use the
installed snapshot's `sync.lock_wait_seconds` for sync/planning/diagnostics and
`verification.lock_wait_seconds` for verification; one absolute budget spans
admission/queue and lock/delegation waiting. Matching retries consult the durable
binding before fresh policy, capacity or verifier probes. These routes never
turn a client-supplied timeout, configuration file or command name into execution
policy.

`AcceptanceResponse` is independent of `ReadResponse` and the durable schema.
It contains `schema_version=1`, current server-generated `request_id`, admitted
`archive_id`/`config_fingerprint`, public `operation: OperationView`, `created`
and `links: {status, result, events}`. HTTP 202 carries `Location` equal to the
status link; links include the configured URL prefix. A new operation has
`created=true`; a matching retry has `created=false` and the original operation,
including its admitted fingerprint after policy changes. Both return 202 even
if the operation has already finished. No terminal success Envelope is fabricated
inside an admission response, and no key/request digest or original body is exposed.

Poll the authenticated status link to inspect state and the events link with its
sequence cursor for bounded progress. Retrieve the result link for the exact
schema-1 Envelope/domain run ID/partial results and exit classification. A result
GET may return HTTP 200 with a failed domain Envelope; known unfinished/interrupted
results are `HFAPI015`/409 and missing/expired history is `HFAPI013`/404, both
exit 20. HTTP 202 is admission only. Losing the acknowledgement, response or
observer never proves nonexecution: use the original key's non-submitting lookup
before any deliberate retry. Do not generate another key to repeat uncertain work.

For an authenticated request, representative bodies are:

```http
POST /api/v1/plans
Content-Type: application/json
Idempotency-Key: example-plan-request

{"selectors":["model:organization/model-name"]}
```

```http
POST /api/v1/diagnostics
Content-Type: application/json
Idempotency-Key: example-read-only-diagnostics

{"read_only":true}
```

Writer-only sync uses the same selector body; verification uses, for example,
`{"mode":"full"}` or `{"mode":"new","run_id":"0123456789abcdef0123456789abcdef"}`.
Examples omit bearer values; authentication is required on submission and every
poll. Installed validation sends `{}` without a key and returns its ordinary
schema-1 validation result in `ReadResponse.envelope`; classified policy/credential
failures remain failed Envelopes at HTTP 200. It reports nonsecret token-source
classification and never returns a credential.

Candidate content is not accepted on these routes yet: raw `candidate` presence
is 403 for a reader, then an unknown-field 422 for a writer. The reserved bounded
`CandidatePayload` and pure authority-assessment hooks are API-012 preparation,
not candidate HTTP availability, arbitrary server-file loading or installation.

## Execution correlation (API-004)

[Decision 111](adr/decision-111.md) separates four identities without changing
schema-1 archive records. A trusted server boundary mints a fresh `request_id`
for each received request; caller headers cannot select the authoritative ID.
API-007 admission mints an independent `operation_id`, shared by its submission,
observation requests and execution. A domain `run_id` continues to identify the
CLI Envelope and any durable run report. A `transaction_id` continues to identify
one archive journal; a run may contain several transactions. These IDs use the
existing 32-lowercase-hex grammar. A request is not a run or a transaction, and
retrying or polling an operation does not mint a replacement domain identity.
API-007 receipts preserve domain relationships and the authenticated coarse
credential-class submitter; API-008 still owns actual execution propagation.

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
`offline.initialize_offline_process()` is the startup-only primitive for the
API-008 dedicated executor: call it before importing or using Hub libraries and retain
the flag for that process's lifetime. The helper does not deny IP sockets.
API-008 supplies the dedicated process/protocol and credential checks; API-014
must establish installed credential-free/no-IP hardening. No ASGI-process
verification fallback is permitted.

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

Decisions [109](adr/decision-109.md) and [114](adr/decision-114.md) permit a
bounded non-resuming submission registry, separate from archive journals.
API-007 implements durable admission primitives and HTTP observation. API-008
supplies one heavyweight FIFO lane (16 pending by default), policy/lock
revalidation and private verification protocol/process primitives;
API-009/010 add command submissions. The bounded metadata pool and daemon-instance
lock already exist. Never hold the archive flock for daemon lifetime. The process
is single-worker without auto-reload; heavy work stays outside the ASGI event loop.

Side-effecting submissions require `Idempotency-Key`. Persist a restrictive
atomic JSON receipt under service-private `/var/lib/hfcache/api/` before 202 or
execution. Bind fixed credential-class principal identity and the SHA-256 key
digest to a canonical route/request digest and admitted policy fingerprint.
Persist no raw key, candidate body, bearer or credential source/digest. The
receipt itself is the authoritative binding; indexes are derived. Matching
retries return the original operation before requesting a fresh policy snapshot,
even after policy changes; conflicting requests/routes return 409. Every
retry/lookup reauthenticates. Header-based lookup searches only the caller's
credential-class namespace, which survives credential rotation. It does not
submit work. All REST principals with read capability may observe any operation
metadata, events and results, just as they can read archive reports under AD-21.
An operation ID is never authentication.

The core key grammar is `1`–`128` ASCII characters from letters, digits,
`.`, `_`, `~`, `+` and `-`. Empty, whitespace, control or oversized keys fail
validation without echoing their value. Canonical request hashing uses the shared
deterministic JSON serializer over `{route, request}` with sorted keys and the
validated request mapping; the serialized comparison input is bounded to 8 MiB.
Object insertion order therefore does not change the digest; meaningful array
order and route identity do. It is never a hash of raw HTTP bytes and never
authorizes replaying the request. Public submission routes must validate strict
domain DTOs and require a key before calling admission.

For example, after losing an acknowledgement, an authenticated client sends
`GET /api/v1/operations/lookup` with the original `Idempotency-Key` header. It
does not resubmit or move the key into a URL. The core admission outcomes are:

| Retry condition | Outcome |
| --- | --- |
| Same credential class, key, route and validated request; object keys reordered | Original operation, no new policy lookup or admission |
| Same binding after installed policy changes or same-class credential rotation | Original admitted operation and fingerprint |
| Same class/key with a changed route or request | `HFAPI012`/409 conflict; no new operation |
| Same key under a different credential class | Separate namespace; lookup cannot find the first class's binding |
| Missing/expired history | `HFAPI013`/404 with unknown execution outcome; never automatic replay |

API-007 exposes non-submitting lookup; API-009 now provides the strict command
POST examples above, while maintenance/initialization routes remain API-010.

States: queued, waiting_lock, running, succeeded, failed, interrupted. Store the
exact terminal Envelope in a validated bounded result reference. Interrupted
means uncertain execution outcome and has no fabricated domain report. API-008
applies one absolute waiting deadline across queue, delegation and lock time,
reloads installed policy under the service-owned lock and refuses stale scope
before mutation without duplicate/nested lock acquisition. Verification delegates
to the private socket executor, which owns its lock through report/catalog
persistence. API-009 implements the command subset above; maintenance and
initialization POST resources remain API-010.

Disconnect and Ctrl-C stop observation. They do not cancel accepted work. Later
API-backed clients emit the nonsecret key before mutation submission and operation
ID before waiting, even in quiet mode; stdout carries exactly one terminal
Envelope. Sequenced sanitized events are bounded application evidence, never
arbitrary journald output.

Shutdown stops admission, drains/joins workers, and preserves receipts. Restart
never automatically reruns old queued/running work. API-007 opens the store
without classification; an explicit `interrupt_unfinished()` primitive is
available. API-008 reconciles exact surviving workers before marking unresolved
nonterminal receipts interrupted: recover an exact durable terminal Envelope or
reattach/await an exactly identified live worker without re-execution. Missing or
unavailable proof retains uncertainty, never a fabricated report. PID, released
lock, elapsed time or disconnected client do not prove
completion. Terminal key/result retention defaults to 30 days. Count/byte caps
refuse new admission rather than evicting unexpired bindings. Nonterminal and
interrupted records retain their receipt/result space reservation; they never
expire. Ambiguous, malformed, unsafe and unknown-version records are preserved
and fail admission closed. Healthy validated IDs remain observable. Delete only
validated owned succeeded/failed history after expiry. Expired/missing history
is uncertainty, not proof of nonexecution or permission to replay. See the
independent [schema/compatibility contract](schemas.md#13-service-private-operation-control-state-api-007)
and [recovery runbook](recovery.md#10-operation-history-and-uncertain-submissions).

Unavailable/unsafe verifier status specifically preserves the parent's active
receipt and disables fresh execution across restarts, while metadata remains
observable. Only trusted missing/interrupted evidence permits parent interrupted
classification. A transport failure cannot be converted to an interrupted marker
that a subsequent startup would skip while reopening the lane. Restored exact
status resolves this barrier without replay.

### Heavy-lane execution boundary (API-008)

Only new durable admission can create runnable work; retrying/observing an old
operation cannot. The single FIFO lane bounds pending work separately from
metadata workers. Full/draining admission returns `HFAPI009`/503. One absolute
host-monotonic deadline consumes queue residence and the remaining service-owned
archive-lock wait. A deadline bounds waiting to start, not the duration of a
running sync/verification. The under-lock guard reloads installed policy and
compares the admitted fingerprint before mutation; the daemon never pre-locks a
service or passes a held lock to the verifier.

The default lane permits one active item plus `max_queued_operations` pending.
Zero waiting budget is an idle-lane single lock attempt and cannot queue behind
another item. Expiry before execution records a failed `HFAPI015` Envelope;
archive-lock timeout keeps `HFMNT010`, and an under-lock changed fingerprint keeps
`HFAPI007`. These terminal domain/admission results are later retrieved with
HTTP 200 and their original exit classification, not translated into fabricated
success. Immediate full/draining refusal is `HFAPI009`/503 without new work.
Observation timeouts do not cancel accepted execution.

Every non-estimate verification requires the configured private executor.
Fresh admission probes availability before persisting a new receipt; matching
idempotent retries return the old binding without a new probe. A probe never
submits work.
`HFAPI016`/503, exit 20, reports unavailable/untrusted socket, peer, frame or
executor evidence. No generic command/config/path/credential crosses that
protocol, and no production fallback executes verification in ASGI. The private
worker preserves the API operation ID in its own schema-1 receipt and returns
the exact domain Envelope. Status lookup never submits; matching retry never
double-starts. Exact trusted running progress updates the parent receipt's phase
and domain run ID. A private `running` label with no owned live execution thread
is unavailable evidence and keeps the execution barrier closed. OS no-IP
enforcement and socket-activated unit acceptance remain
API-014, not a property of the process's library offline flag. See
[wire/trust/deadline details](server.md#verification-wire-and-local-trust).

### Implemented operation observation (API-007)

Every route below requires a REST principal with `read` capability. Observation
uses the same bounded metadata pool, request/response safeguards and stream
leases as archive reads. It does not load a fresh archive-policy snapshot, call
any domain command, acquire the archive flock, admit work or change a receipt.
Healthy exact-ID history therefore remains available after an invalid policy
update or unrelated corrupt receipt. Collection/key-lookup scans refuse unsafe,
unsupported or unexplained state instead of silently dropping it.
Capabilities advertises `operation_history=true` and, since API-009,
`operations=true` for its implemented command routes. Roles still apply; this
flag does not imply maintenance/candidate routes or full REST acceptance.

| Route under `/api/v1` | `envelope.data` / behavior |
| --- | --- |
| `GET /operations` | `operations`: newest-first public metadata; supports `limit`/`cursor` only |
| `GET /operations/lookup` | `operation`: original receipt found by exactly one `Idempotency-Key` header in the caller's namespace; no query parameters |
| `GET /operations/{operation_id}` | `operation`: public metadata by validated server ID; no query parameters |
| `GET /operations/{operation_id}/result` | Exact stored terminal domain Envelope in the response's `envelope`; no query parameters |
| `GET /operations/{operation_id}/events` | `operation_id`, `events`, integer `next_cursor`, `oldest_sequence`, `truncated`; accepts only `after`/`limit` |

`OperationView` exposes `schema_version`, `operation_id`, coarse `principal`,
`route`, admitted `archive_id`/`config_fingerprint`, `state`, `created_at`,
`updated_at`, nullable `completed_at`/`domain_run_id`, `transaction_ids`,
`next_event_sequence` and `result_recorded`. It excludes the key and request
digests, result-file reference and inline events. The principal is `rest-writer`
or `rest-reader`, not a person's identity. No raw key or original request is
available for retrieval.

All routes use `ReadResponse`. Exact show/lookup/events/result responses carry
the receipt's admitted archive UUID/fingerprint, even if installed policy later
changes. A collection uses the startup-pinned configured UUID and null wrapper
fingerprint; each item retains its own admitted identity. Ordinary observation
Envelopes identify the current request. The result endpoint preserves the stored
domain Envelope/run ID/exit classification: HTTP 200 can contain a failed domain
result. A known queued/waiting/running/interrupted receipt without a result returns
`HFAPI015`/409, exit 20; absent/expired history returns `HFAPI013`/404, exit 20.
It never invents an empty successful result. Invalid IDs/header/query input is
`HFAPI006`/422 without echoing input. Unsafe/unavailable/unexplained storage is
`HFAPI014`/503, exit 20.

Collection ordering is descending `(created_at, operation_id)`. Its default
limit is 100, bounded by `max_page_size`; its opaque cursor binds ordered IDs
and the daemon instance. Changed membership/order or a restart invalidates
continuation with `HFAPI007`/409. Receipt fields can change between pages without
changing membership, so this is not a frozen history snapshot. Start a fresh walk
after a stale cursor. Collection cursors are distinct from event sequences.

For events, `after` is a nonnegative decimal sequence (default `0`); `limit`
defaults to the minimum of `100`, `max_page_size` and `operation_max_events` and
cannot exceed either configured ceiling. Both are single ASCII decimal values
of at most ten digits. Events are returned in increasing sequence after `after`.
`next_cursor` is the last returned sequence, or the supplied `after` if empty;
pass it as the next `after`. `oldest_sequence` identifies the first retained
sequence, or the next sequence if no event exists. `truncated=true` explicitly
reports a gap when the caller's cursor predates the retained suffix. Event
retention is bounded independently of the receipt/key window; clients must
present a gap honestly rather than fabricate progress. No long-poll, SSE,
WebSocket, raw journal stream or cancellation endpoint is added.

Result reads validate the referenced file's bytes/hash/identity and schema-1
Envelope before streaming with the existing bounded JSON encoder/lease. Source
bytes are capped by `operation_max_result_bytes`; normal metadata uses
`max_response_bytes`, and encoded result responses use the existing large-evidence
ceiling of eight times `max_artifact_bytes`. No endpoint serves arbitrary control
files. The independent [durable schema](schemas.md#13-service-private-operation-control-state-api-007)
records file ownership, transitions, event/result bounds and compatibility.

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
