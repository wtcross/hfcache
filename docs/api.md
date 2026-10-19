# REST API reference

The writer exposes authenticated metadata reads, synchronous validation and keyed
jobs under `/api/v1`. The operational [CLI](cli.md) and [Python client](api-client.md)
use this interface. The writer owns archive policy, Hub authority, preflight,
local locking, publication and recovery. The private offline worker owns actual
verification. HTTP never invokes CLI callbacks or starts a worker automatically.
The optional [MCP interface](mcp.md) has a distinct read-only credential and protocol.

## Connect and authenticate

Use verified HTTPS off-host, with the configured public prefix before `/api/v1`,
for example `https://archive.example.com/management/api/v1/version`. Native Unix
clients can use unprefixed `/api/v1` on the same application; only corroborated
Unix transport scope selects that authority. Headers cannot manufacture locality.
Native Unix also accepts the configured prefix; links follow the effective spelling.

Every surface authenticates before routing and body validation: health, errors,
unknown paths, unsupported methods, schema and optional interactive docs. REST
writer credentials grant read/write; REST readers grant read. An MCP-reader bearer
has no REST authority, and a Hub token is never an API credential. All readers must
be entitled to the whole archive, including restricted metadata; there are no
per-repository ACLs. An operation ID is not authentication.

Use a separately provisioned protected token **pathname**, never a literal bearer
in command arguments or URLs. The client reads that selected source and sends
`Authorization: Bearer <selected value>` internally. There is no token issuance,
OAuth login, ambient discovery, redirect or proxy fallback. See
[client setup](api-client.md#client-configuration-and-setup) and
[server credentials](server.md) for file/name delivery and restart-based rotation.

## Routes and effects

Paths in this canonical matrix are relative to `/api/v1`. R permits a REST reader
or writer; W requires a writer. Synchronous calls return metadata/validation;
keyed jobs require `Idempotency-Key` and return durable admission before execution.
A receipt is a control-state write even when archived content is unchanged.
Ordinary logs/process activity are outside the archive-effects column.

`archive` is the shared local exclusive flock through domain persistence;
`worker archive` is that lock held by the offline verifier. Preview does not grant
apply authority. All POSTs reject query parameters. Optional docs require
`interactive_docs=true`; the authenticated schema remains available when docs are off.

| Method/path | Mode | CLI mapping | Capability | Execution | Archive lock | Hub contact | Archive effects | Control-state effects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /version` | default | version --server | R | synchronous | none | no | none | none |
| `GET /capabilities` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `POST /config/validate` | installed | config validate (installed) | R | synchronous | none | no | none | none |
| `POST /config/validate` | candidate | --config PATH config validate | W | synchronous | none | no | none | none |
| `GET /archive/inspection` | default | archive init --inspect | R | synchronous | none | no | none | none |
| `POST /archive/initializations` | default | archive init --confirm | W + initialization gate | keyed job | archive | no | initial layout/sentinel | receipt, events and result |
| `POST /diagnostics` | read_only=true | doctor --read-only | R | keyed job | none | yes | none | receipt, events and result |
| `POST /diagnostics` | read_only=false | doctor (probes) | W | keyed job | archive | yes | temporary health probes | receipt, events and result |
| `POST /plans` | installed | plan (installed) | R | keyed job | none | yes | none | receipt, events and result |
| `POST /plans` | candidate | --config PATH plan | W | keyed job | none | yes | none | receipt, events and result |
| `POST /syncs` | default | sync | W | keyed job | archive | yes | journals/cache/publication/catalog/report | receipt, events and result |
| `GET /catalog/search` | default | search | R | synchronous | none | no | none | none |
| `GET /catalog/facets` | default | tags | R | synchronous | none | no | none | none |
| `GET /catalog/repositories/{repository_type}/{namespace}/{name}` | default | catalog show TYPE:ID | R | synchronous | none | no | none | none |
| `GET /catalog/repositories/{repository_type}/{namespace}/{name}/variants` | default | catalog variants TYPE:ID | R | synchronous | none | no | none | none |
| `POST /catalog/refreshes` | default | catalog refresh [selectors] | W | keyed job | archive | no | supplemental metadata | receipt, events and result |
| `GET /status` | default | status [selectors] | R | synchronous | none | no | none | none |
| `GET /repositories` | default | list [selectors] [--type] | R | synchronous | none | no | none | none |
| `GET /repositories/revisions` | default | list --revisions [selectors] [--type] | R | synchronous | none | no | none | none |
| `GET /verification/estimate` | default | verify --estimate | R | synchronous | none | no | none | none |
| `POST /verifications` | mode=new | verify --new [--run-id] | W | keyed job | worker archive | no | report/catalog | receipt, events and result |
| `POST /verifications` | mode=full | verify --full | W | keyed job | worker archive | no | report/catalog | receipt, events and result |
| `POST /verifications` | mode=revision | verify --revision | W | keyed job | worker archive | no | report/catalog | receipt, events and result |
| `POST /prune-plans` | default | prune --dry-run | R | keyed job | none | no | none | receipt, events and result |
| `POST /prunes` | default | prune --apply | W | keyed job | archive | no | guarded domain mutation/audit | receipt, events and result |
| `POST /purge-plans` | default | purge --dry-run [selectors XOR --all-unmanaged] | R | keyed job | none | no | none | receipt, events and result |
| `POST /purges` | default | purge --apply [selectors XOR --all-unmanaged] | W | keyed job | archive | no | guarded domain mutation/audit | receipt, events and result |
| `POST /recovery-plans` | default | recover --dry-run | R | keyed job | none | no | none | receipt, events and result |
| `POST /recoveries` | default | recover --apply | W | keyed job | archive | no | guarded domain mutation/audit | receipt, events and result |
| `POST /quarantine-plans` | default | quarantine --dry-run IDs | R | keyed job | none | no | none | receipt, events and result |
| `POST /quarantine-cleanups` | default | quarantine --apply IDs | W | keyed job | archive | no | guarded domain mutation/audit | receipt, events and result |
| `POST /repairs` | default | repair TYPE:ID@SHA [--reason] | W | keyed job | archive | yes | guarded domain mutation/audit | receipt, events and result |
| `GET /runs` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /runs/{run_id}` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /repositories/{repository_type}/{namespace}/{name}/references/{revision}` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /repositories/{repository_type}/{namespace}/{name}/manifests/{commit_sha}/{publication_id}` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /operations` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /operations/lookup` | default | operations lookup | R | synchronous | none | no | none | none |
| `GET /operations/{operation_id}` | default | operations show | R | synchronous | none | no | none | none |
| `GET /operations/{operation_id}/result` | default | operations wait | R | synchronous | none | no | none | none |
| `GET /operations/{operation_id}/events` | default | operations wait | R | synchronous | none | no | none | none |
| `GET /health` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /openapi.json` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /docs` | optional | SDK / HTTP | R | synchronous | none | no | none | none |

## Metadata reads

Repository path components are separately validated: type is `model` or `dataset`,
then namespace/name. References select `current` or a full lowercase 40-character
SHA; manifests require both SHA and exact 32-lowercase-hex publication ID. Run and
transaction identifiers retain their domain grammars. No parameter is an arbitrary
filesystem path, and no endpoint serves repository payload files.

Status covers configured repositories plus unmanaged published data. Unknown
selectors fail HFARG004. Inventory reads authoritative references/manifests, even
when a derived catalog is missing or corrupt; missing confidence remains unknown
and never authorizes rebuilding a catalog. Metadata checks validate safe paths,
configured archive identity, repository/SHA/publication/generation and canonical
locators. They do not claim sentinel revalidation on every read. Exact report
reads check archive UUID, filename/time and run identity; informational latest-run
summaries can ignore unreadable or mismatched reports. Verification catalogs are
derived and have no archive-ID field; exact publication keys govern confidence.

`health.ready` describes daemon readiness, not archive integrity, mount proof,
initialization or an open execution lane. `policy_valid` is true/false after a
fresh diagnosis, or null if capacity prevents it; archive diagnostics can be null.
Health neither probes writability nor repairs/rebuilds state. Version/capabilities
remain available if the installed archive policy later becomes invalid; startup
still requires valid server configuration, credentials and initial policy.

### Catalog reads

Catalog routes use the same authenticated, bounded metadata pool and strict
`ReadResponse`. Their Envelope data is an independently strict schema-1
[catalog payload](schemas.md#172-catalog-payloads). Search accepts `type`, `q`,
repeated `tag_all`/`tag_any`, `tag_source`, `scope`, `revision_scope`, `format`,
`quantization`, `quantization_method`, `bits`, `max_variant_bytes`, `limit`,
`cursor`. Facets accepts the same query plus required `facet` (`tag`, `format`,
`quantization_method`, `quantization`). Scalars cannot repeat. Numbers use
canonical unsigned decimal spelling; booleans, signs and fractions refuse.
Unknown keys and GET bodies refuse. Tags normalize as in configuration.

Detail and variant collections accept `revision_scope` and paired `commit_sha`/
`publication_id`; the model-only variants collection additionally accepts `limit`/`cursor`. An exact pair
selects that retained publication, including a noncurrent one; a vanished pair
returns 404 without falling back. Detail has at most 64 observation summaries;
full variants are separately paged. Reads never scan payloads, acquire the archive
lock, refresh metadata, resolve Hub credentials or write. Availability describes
retained declarations, not a fresh integrity check. Entire scoped coverage and
`HFWRN011` qualify known matches, including zero. See [predicate and provenance
semantics](discovery.md#queries-coverage-and-pages).

The API version and exact capabilities object remain unchanged: existing `reads`
covers these additive reads. New catalog schemas are independently versioned and
advertised in OpenAPI; adding a capability field would break strict existing
clients. Catalog cursors bind route, normalized predicates, visible policy and
curation, exact refs, observations, ordering and coverage. Tag-only edits can
invalidate them even when the old operational fingerprint remains unchanged.

### Read response

A strict schema-1 `ReadResponse` contains exactly:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer 1 |
| `request_id` | Server-generated HTTP request identity |
| `archive_id` | Snapshot or startup-pinned configured UUID; not sentinel proof |
| `config_fingerprint` | Fresh policy fingerprint, or null for policy-independent diagnostics |
| `envelope` | Complete schema-1 domain Envelope, or one explicitly paged data projection |
| `next_cursor` | Opaque continuation, or null |

Request IDs never replace a report's domain run ID. Failed inspection/validation
can return HTTP 200 with a failed Envelope. Preserve its warnings, errors, partial
data and exit classification. [CLI output](cli.md#4-json-output) defines the Envelope.

References return `locator_base="published/"`. Manifests return
`tree_base="archive-root/"`. Pin SHA, publication ID, generation and locator;
never substitute a newer current publication when an exact instance disappears.
Use the [consumer data path](consumers.md) for bulk copying and local verification.

### Pagination and budgets

Status/inventory/revision pages accept repeated `selector`, optional `type`,
`limit` and `cursor`. Report/operation inventories accept their documented bounded
pagination; operation events use integer `after` and `limit`. Other metadata reads
reject query parameters. Unknown keys, repeated scalars, coercive numeric forms,
nonempty GET bodies and malformed domain values refuse, including chunked input.
Limits are positive ASCII decimal integers, default min(100, configured maximum).
REST selectors are at most 100 values of 256 characters; cursors at most 256.
Raw query bytes are capped at 8192; total header name/value bytes at 32768.

Status preserves configuration order followed by unmanaged publication order.
Inventory uses canonical repository order; revisions then use retained publication
generation. Report IDs use reverse timestamped filename order. Cursors bind route,
normalized filters, policy fingerprint and a digest of the complete selected array.
Changed scope/policy/array or an out-of-range offset returns 409; malformed encoding
returns 422. Restart the walk after a stale cursor. Pages are not an archive-wide
snapshot; ancillary fields may change independently. Walk until `next_cursor=null`.

Normal responses default to 8 MiB. Metadata scans default to 10,000 entries and
64 MiB per artifact **and aggregate** source bytes. Small pages do not bypass those
underlying scans. Exhaustion is HFAPI005/503, never an empty/truncated success or
an upgrade of unknown verification confidence. Reports/manifests/results have a
distinct encoded stream bound of `max_artifact_bytes * 8`, pre-counted before
headers, with chunks at most 8192 bytes. Parsed representation remains bounded;
this is neither an unbounded file relay nor payload transfer. The metadata lease
lasts through worker and response/stream completion, including disconnect.

Public operational CLI collection is bounded too: per-response bytes, cumulative
identity-digest bytes, page count and aggregate serialized rows. `list --revisions`
checks membership, counts, archive/fingerprint, current/exact publication identity,
uniqueness and generation order while retaining empty/unmanaged base rows. Any
inconsistency or exhausted limit fails explicitly; no silent partial inventory is
success. Direct internal query APIs are not an alternate unbounded operational CLI.

## Command requests

Bodies require exactly one `Content-Type: application/json`, optionally with a
quoted or unquoted UTF-8 charset, and no `Content-Encoding`. The server rejects
duplicate keys, nonfinite numbers, invalid Unicode and nesting deeper than 32.
The request limit applies to actual received bytes, including chunked bodies.
Objects forbid unknown fields and coercion. Route URLs
choose preview/apply; a posted plan, preview operation ID, mode override or client
filesystem proof never authorizes apply. Common selectors default to `[]`, are
validated, deduplicated and sorted for canonical admission. There are at most 100
selectors, each at most 256 characters.

- Sync/installed plan take `selectors`. Candidate plan additionally takes nonempty
  `candidate` TOML text. Planning uses Hub metadata without payload downloads or
  archive mutation; failures retain useful results for other repositories.
- Diagnostics require explicit literal `read_only=true` for reader authority;
  ordinary probing requires writer authority. Both contact the Hub. Read-only
  skips archive-write probes and lock; probing uses temporary health artifacts.
- Validation takes `{}` for installed policy or `{"candidate": "..."}` for a
  writer-authorized candidate. It is synchronous and creates no receipt.
- Verification takes `mode` exactly `new`, `full` or `revision`. `revision` is
  non-null exactly for revision mode; `run_id` may be non-null only for new mode.
  Explicit null is accepted for unused scope fields. Actual verification
  is offline, locked and persists reports/catalog; estimates neither hash nor submit.
- Prune uses configured selection; a SHA suffix does not override retention policy.
  Purge requires whole-repository selectors XOR `all_unmanaged=true`; empty scope,
  revision selectors and currently configured repositories refuse.
- Recovery takes exactly `{}`. Quarantine requires 1–100 explicit transaction IDs,
  sorted/deduplicated, with complete batch proof before any removal.
- Repair requires exact `TYPE:ID@SHA`; `reason` defaults to `operator_requested`,
  maximum 2048 characters. It accepts no Hub endpoint, credential or source override.
  Installed secrets are redacted from the audit reason before persistence.
- Initialization requires `archive_root`, canonical UUID `archive_id` and literal
  `confirm=true`. Root paths are absolute, at most 4096 UTF-8 bytes, with no dot,
  traversal, backslash or nonprintable components. The root/UUID must match
  installed authority; they never choose a different archive.

### Offline catalog refresh

`POST /catalog/refreshes` accepts only `selectors=[]`, `revision_scope=retained`,
`tags=true`, `technical=true`. Selectors are at most 256 raw canonical whole
repository identities; they sort/deduplicate, and revision suffixes, paths and
URLs refuse. Flags are strict booleans with at least one enabled. This writer-only
keyed operation uses the existing FIFO lane, original shared archive guard and
exact receipt/event/result observation. Admission grants no configuration-install,
credential override, verifier dispatch or model download authority.

Fresh installed curation and scope are resolved after lock wait, retaining admitted
operational authority. Tag-only changes can affect a new capture without changing
the policy hash. The original key always observes its original operation; a new
capture needs a new key. Failed/partial per-record outcomes remain visible in the
strict [refresh payload](schemas.md#173-offline-refresh-result). Refresh performs
no recovery/repair/prune/cleanup or integrity hashing. Observer departure cannot
cancel it; startup never replays it. Preserve uncertain handles and original state.

The canonical route identifies this operation kind; its Envelope command is
`catalog refresh`. Existing receipt/result-reference/Envelope versions and fields
remain unchanged. Strict older operation-route clients may refuse the new kind.
Drain and preserve control evidence before any separately approved rollback.

### Candidate content and installed authority

Candidates are at most 1 MiB of UTF-8 TOML; JSON escaping/wrapper overhead still
counts against the server request cap. Explicit `candidate:null` is invalid and
field presence already requires writer authority. Content is never a server
pathname, installed policy, credential value or durable replay body.

Validation separates syntax/policy validity from compatibility with installed
root, UUID, Hub endpoint, token mode, credential name and expected account. A valid
incompatible candidate remains valid but cannot plan. Broken installed policy can
leave compatibility unknown while candidate syntax validation succeeds. Candidate
planning always uses installed Hub authority, captures immutable repository policy
and rechecks compatibility before execution. Neither validation nor planning
installs configuration or grants mutation authority.

### Maintenance requests

Apply acquires the shared lock once, reloads installed policy, compares the admitted
fingerprint and reconstructs its own scope/evidence. Stale policy or newly managed
purge targets refuse before mutation. Quarantine proves the entire named batch;
changed bytes, unknown files, repair evidence or unfinished transactions remain.
Recovery rolls forward only explainable states and preserves ambiguity at exit 20.
Prune/purge preserve the logical commit boundary: restore before it, finish audit/
physical cleanup after it. Canonical cache deletion uses supported APIs; audits
and original manifests remain; empty containers use `rmdir`.

Repair verifies immutable-SHA downloads against original expectations, reverifies
its new exact publication before switching references and retains the previous
locator through the grace period. A SHA/generation alone does not identify a
replacement instance; consumers must retain the exact publication ID and locator.
The current allocator reads retained references rather than the full retained/audit
union required by lifetime-generation invariants. Re-observing a pruned SHA can
assign a fresh generation; whole-repository purge/re-add has the same retained-set
limitation. These routes do not resolve that existing conformance gap.

`maintenance_enabled=false` is restart-only and gates **initialization only**.
Disabled initialization rejects with HFAPI002/403 before body reception or old-key
handling, including retries of previously admitted keys. Original observation stays
available. A valid mismatched root/UUID can be admitted but ends HFARG002/10 without
initialization. Existing/unknown content, unsafe mount or sentinel refuses; sentinel
is written last. Startup, health, recovery and a missing sentinel never initialize.

For a separately authorized disposable scope, a preview request body can be
`{"selectors":["model:retired/model-name"]}` at `/purge-plans`. Apply uses `/purges`
with that explicit scope and a distinct deliberate key after reviewing current
proof. Never send the returned plan as authority. These interface examples do not
authorize operations on an existing production archive.

## Admission, idempotency, and lifecycle

Every keyed job requires a nonsecret `Idempotency-Key`: 1–128 ASCII letters,
digits, `.`, `_`, `~`, `+` or `-`. Invalid values refuse without echo. Generate and
preserve the key before POST. A schema-1 acceptance contains request/archive/
fingerprint identity, the operation receipt, `created` and same-operation status,
result and event links; HTTP 202/Location prove durable acceptance only.

Before execution or 202, persist an atomic restrictive local receipt binding the
credential class, key digest, canonical route/request digest and admitted policy.
Canonical hashing uses deterministic sorted-key JSON over `{route, request}`,
bounded to 8 MiB; object insertion order is irrelevant. Store no raw key, request
body, candidate content, bearer or credential source/digest. Indexes are derived;
receipts are authority. Scheduled observation handles are separate local state.

| Condition | Result |
| --- | --- |
| Same class/key/route/canonical request, including reordered object keys | Original operation, `created=false`; no fresh policy lookup or enqueue |
| Same binding after policy change or same-class credential rotation | Original admitted identity/fingerprint |
| Same class/key with changed request or route | HFAPI012/409 conflict |
| Same key in another class | Separate namespace |
| Missing/expired history | HFAPI013/404; execution remains unknown |

Lookup uses `GET /api/v1/operations/lookup` with the original key in the header,
never a URL. Every lookup/retry reauthenticates. Lookup is class-scoped; known-ID
observation and listing are available to all REST readers/writers under whole-
archive trust. A missing receipt never grants replay authority.

States are `queued`, `waiting_lock`, `running`, `succeeded`, `failed`, `interrupted`.
The exact terminal Envelope carries domain run ID/outcome and exit priority
(40 integrity, then 50 maintenance, then 30 sync). Result HTTP 200 does not imply
successful execution. Interrupted work has no fabricated terminal report.
Events are bounded sequenced application evidence, with `oldest_sequence`,
`truncated` and `next_cursor` exposing retained-history gaps; they are not raw logs.

One FIFO heavy lane defaults to 16 pending entries; metadata has its own bounded
pool. One monotonic waiting deadline spans queue, delegation and lock acquisition;
running domain work may outlast it. Verification admission first proves worker
availability before a new receipt, while matching retries return existing history
without that fresh-only probe. The HTTP process never hashes or starts the worker.
Worker receipt/result identity and digest must match exactly.

Shutdown stops admission and joins owned work before releasing metadata/store/
instance ownership. Restart never replays queued/running requests. Reconcile exact
surviving verifier evidence: recover its durable result or reattach to that live
operation. Unavailable/unsafe/mismatched worker evidence preserves parent history
and closes fresh execution across restarts; metadata observation remains available.
Only trusted missing/interrupted evidence permits interrupted classification.
PID, free lock, elapsed time and observer exit are not executor-termination proof.

Terminal key/result retention defaults to 30 days. Count/byte pressure refuses new
admission rather than evicting unexpired keys or unresolved evidence. Nonterminal
and interrupted receipts reserve maximum receipt/result space and never expire;
terminal records use actual bytes. Preserve unsafe, malformed and unknown-version
records; admission fails closed while healthy IDs remain observable. Delete only
validated owned succeeded/failed history after expiry. See [control-state schemas](schemas.md)
and the [recovery runbook](recovery.md#preserve-four-kinds-of-authority).

## Wire validation and errors

Wire models are independently strict and versioned. Shared sanitization removes
sensitive keys, known token/signed-URL shapes and registered exact secrets before
rendering; arbitrary unknown strings cannot be identified as secrets. Diagnostics
never echo framework input, raw bodies, exception text or tracebacks.

`ApiProblem` contains exactly `request_id`, stable `code`, safe `message` and
`exit_code`. Every response supplies authoritative `X-Request-ID`, `Cache-Control:
no-store`, `X-Content-Type-Options: nosniff` and a frame-ancestor CSP. Caller request
IDs do not choose correlation. Noncanonical REST trailing slashes refuse without
redirecting or reflecting query text into Location.

| HTTP status | Meaning |
| --- | --- |
| 401 | Missing/invalid/wrong-interface bearer; challenge included |
| 403 | Insufficient capability or disabled initialization |
| 404 | Missing resource/history; absence does not prove nonexecution |
| 405 | Authenticated unsupported method, HFAPI007 |
| 409 | Stale cursor/policy, conflicting key, unfinished result or classified read-integrity refusal |
| 413 / 422 | Oversized / invalid strict request |
| 503 | Capacity, draining or unavailable executor |
| 500 | Sanitized unexpected failure |

Read-integrity refusals retain their HFVER taxonomy/exit. Client configuration,
authentication and protocol failures exit 10; unavailable/uncertain observation
exits 20. Exact terminal domain results retain their own exits. See the complete
[CLI error taxonomy](cli.md#5-error-and-warning-taxonomy).

## Reconnect after lost acknowledgement

1. Retain the original key, route, configured authority and credential class.
   Do not generate another key or automatically POST again.
2. Run `hfcache --client-config /etc/hfcache/client.toml --json operations lookup -- '<original-key>'`.
   Lookup submits nothing. Once known, preserve the operation ID.
3. Use `operations show ID` or `operations wait --after N -- '<operation-id>'`
   with a finite wait budget. Inspect the exact terminal Envelope and domain exit.
4. HFAPI013 missing/expired or HFAPI015 interrupted history remains uncertainty;
   preserve handles/evidence and follow recovery. Client timeout, disconnect or
   Ctrl-C never cancels accepted work.

HFAPI020 means an unusable POST acknowledgement after transmission may hide
accepted execution. Even a validated retained-key 5xx can follow durable admission.
Keep its taxonomy and warn that work may continue. Client read retries never replay
POST. [Server lifecycle](server.md#restart-and-drain) governs actual executor drain.
