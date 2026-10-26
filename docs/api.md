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

An optional application-owned [Basic administrator](server.md#basic-administrator)
provides the same public `rest-writer` class and `read`/`write` capability array.
It does not issue a bearer, authenticate MCP or extend existing strict wire
schemas. Its stable subject and separate administrative grants are internal;
host/configuration administration and authenticated SPA serving require their
separate implemented boundaries. Browser JavaScript never handles a password.

Missing REST credentials advertise Basic and Bearer when Basic is configured.
Explicit REST Basic failures when the provider is configured advertise only
`Basic realm="hfcache", charset="UTF-8"`; explicit bearer and all MCP failures
retain `Bearer realm="hfcache"`; disabled Basic preserves that legacy challenge.
There is no provider fallback. One original
Authorization field is allowed, at most 8192 encoded bytes; Basic's decoded UTF-8
username/password ceilings are 128/1024 bytes. Configured Basic's header/query/
content-length work bounds and transport proof may refuse before expensive
verification; ordinary route, Host/Origin and body errors follow authentication.
Missing credentials and bearer authentication retain their existing precedence
over request-size/work errors.

Every Basic method except GET/HEAD, including OPTIONS, TRACE, CONNECT and unknown
paths, requires exactly one Origin equal to configured `basic.origin`, JSON media
type and exactly `X-Hfcache-Request: 1`. Missing/null/foreign/duplicate Origin,
form/text/multipart bodies, content encoding and missing/duplicate/wrong intent
headers refuse with HFAPI010/403 before receiving a body. Credentialed browser
preflights cannot supply this actual request contract. Bearer clients retain
their no-Origin behavior. Basic's separate two-active/eight-waiting verifier and
global 30-failure/reservation sliding 60-second budget return HFAPI021/429/exit20 on capacity
or throttling; no domain admission follows that refusal. Basic is authenticated
on native corroborated Unix or numeric-loopback HTTP; remote access requires TLS
or the configured trusted-proxy proof. These source behaviors establish no
production deployment or shared-Caddy UI availability.

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
| `GET /host/status` | default | browser / HTTP | internal host-read | synchronous protected helper read | none | no | none | none |
| `GET /config` | default | browser / HTTP | internal config-read | synchronous protected helper read | none | no | none | none |
| `POST /config/validate` | installed | config validate (installed) | R | synchronous | none | no | none | none |
| `POST /config/validate` | candidate | --config PATH config validate | W | synchronous | none | no | none | none |
| `POST /config/validate` | managed | browser / HTTP | internal config-write | synchronous | none | no | none | none |
| `POST /config/applications` | managed | browser / HTTP | internal config-write | keyed guarded helper application | none | no | none | receipt/events/result + private configuration outcome state |
| `GET /config/applications/{operation_id}` | default | browser / HTTP | internal config-read + original key | synchronous protected outcome read | none | no | none | none |
| `GET /archive/inspection` | default | archive init --inspect | R | synchronous | none | no | none | none |
| `POST /archive/initializations` | default | archive init --confirm | W + initialization gate | keyed job | archive | no | initial layout/sentinel | receipt, events and result |
| `POST /diagnostics` | read_only=true | doctor --read-only | R | keyed job | none | yes | none | receipt, events and result |
| `POST /diagnostics` | read_only=false | doctor (probes) | W | keyed job | archive | yes | temporary health probes | receipt, events and result |
| `POST /plans` | installed | plan (installed) | R | keyed job | none | yes | none | receipt, events and result |
| `POST /plans` | candidate | --config PATH plan | W | keyed job | none | yes | none | receipt, events and result |
| `POST /plans` | managed | browser / HTTP | internal config-write + derived Hub permission | keyed job | none | derived scope | none | receipt, events and result |
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
| `GET /runs` | default | runs list | R | synchronous | none | no | none | none |
| `GET /runs/{run_id}` | default | runs show RUN_ID | R | synchronous | none | no | none | none |
| `GET /repositories/{repository_type}/{namespace}/{name}/references/{revision}` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /repositories/{repository_type}/{namespace}/{name}/manifests/{commit_sha}/{publication_id}` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /repositories/{repository_type}/{namespace}/{name}/publications/{commit_sha}/{publication_id}/card` | default | browser / HTTP | R | synchronous | none | no | none | none |
| `GET /operations` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /operations/lookup` | default | operations lookup | R | synchronous | none | no | none | none |
| `GET /operations/{operation_id}` | default | operations show | R | synchronous | none | no | none | none |
| `GET /operations/{operation_id}/result` | default | operations wait | R | synchronous | none | no | none | none |
| `GET /operations/{operation_id}/events` | default | operations wait | R | synchronous | none | no | none | none |
| `GET /health` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /openapi.json` | default | SDK / HTTP | R | synchronous | none | no | none | none |
| `GET /docs` | optional | SDK / HTTP | R | synchronous | none | no | none | none |

Basic keyed jobs additionally require fresh protected host permissions at
admission and immediately before dispatch. Archive jobs require `archive`, Hub
sizing/diagnostics require `hub`, and maintenance previews require `control`;
non-read-only diagnostics require both `hub` and `archive`. Archive initialization
is denied for Basic. Unknown actions deny. Duplicate POSTs repeat these checks;
original operation lookup/result reads remain available without them. Service
bearers retain their existing behavior. See the exact
[action matrix](host-administration.md#fresh-basic-admission-and-uncertainty).

## Protected host status

`GET /api/v1/host/status` accepts no query parameters and requires the internal
`host-read` capability. Ordinary reader/writer and MCP bearers have no such grant.
Successful authentication returns the ordinary read wrapper with command
`host status`, `config_fingerprint: null`, and the strict `HostStatus` data object.
Its configured archive UUID must match the outer response. The read neither
scans archive contents nor acquires metadata/operation/configuration/archive
locks. It creates no receipt and contacts no Hub service.

The projection distinguishes `supported`, `guarded`, `unknown`, `unavailable`,
six explicit effective permissions/reasons, selected release/policy/source
binding and fixed system unit/timer/sync-schedule facts. Missing, unsafe, busy or
timed-out helper proof returns typed unavailable data with every permission
false. It never fabricates inactive services or archive health. For keyed Basic
admission the same unavailable proof is `HFAPI022`/HTTP503/exit20; a known denial
is `HFAPI002`/HTTP403/exit10. Accepted operations retain original handles and are
not replayed after a failed observation. See
[status schema](schemas.md#185-host-status-schema-1) and the
[protected helper contract](host-administration.md).

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

The [browser detail page](web-ui/repository-details.md) resolves current separately
and then supplies the selected exact pair to publication panels. The recognized
shell path is `/ui/repositories/{model|dataset}/{namespace}/{name}`, with the
configured public prefix. Its browser fragment admits only paired lowercase
`commit_sha` (40hex)/`publication_id` (32hex) and
`tab=overview|details|files|revisions|integrity|activity`; both identity fields or
neither are required. The fragment is bounded to8192UTF-8 bytes and rejects
duplicates/unknown fields. Shell queries, malformed identity paths and arbitrary
SPA fallback remain refused. No REST endpoint or permission is added.

The browser also validates that the full-SHA retained reference still names the
selected publication/generation. The existing manifest endpoint can read a
preserved repair predecessor; manifest existence alone cannot establish current
retained membership. This browser join does not narrow that established REST
behavior or make optional catalog/card availability the membership authority.

REST manifests remain complete bounded artifacts; they do not acquire file-table
`limit`/`cursor` parameters. The browser pages accepted file metadata locally and
refuses an oversized artifact explicitly. A manifest-file digest is available
from the existing exact card read, including `not_captured`; it must not be
invented by hashing reserialized HTTP JSON. Missing supplemental detail does not
erase independently validated authoritative inventory or manifest evidence.

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

In unreleased source, `technical=true` also captures the exact publication's
manifest-listed root `README.md` into an independent
[RepositoryCard](schemas.md#181-repositorycard-schema-1). A bounded fresh source
SHA-256 comparison establishes only README provenance; it does not verify the
publication or update integrity confidence. No Hub request or payload download
is added. Card failure uses existing `HFWRN011` warnings and the existing partial
result rules. Publication observation fields and counts retain their original
meaning; there is no card count, refresh flag or additional refresh route.
The exact card read API is implemented in unreleased source; browser rendering
remains subsequent work. See the
[capture guide](web-ui/readme-cards.md).

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

Bearer key digests remain byte-for-byte SHA256(original ASCII key), with the
existing credential-class namespace. Basic uses SHA256 of
`hfcache\0idempotency\0basic-subject\0v1\0`, followed by a four-byte big-endian
UTF-8 subject length, subject bytes, a four-byte big-endian ASCII key length and
the original key bytes. Validate the unchanged key grammar before hashing or
store locking. This is a private digest preimage, not a printable surrogate key.
No subject/authentication fields or attribution sidecars join strict receipts.

| Condition | Result |
| --- | --- |
| Same namespace/key/route/canonical request, including reordered object keys | Original operation, `created=false`; no fresh policy lookup or enqueue |
| Same binding after policy change or subject-preserving credential rotation | Original admitted identity/fingerprint |
| Same namespace/key with changed request or route | HFAPI012/409 conflict |
| Same key in another bearer class, another Basic subject, or Basic versus bearer | Separate namespace |
| Same Basic subject/key after username/password rotation | Original operation; changing subject selects a distinct namespace |
| Missing/expired history | HFAPI013/404; execution remains unknown |

Lookup uses `GET /api/v1/operations/lookup` with the original key in the header,
never a URL. Every lookup/retry reauthenticates. Lookup uses the caller's bearer
class or Basic stable-subject namespace; known-ID
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
| 401 | Missing/invalid/wrong-interface credential; scheme-specific challenge included |
| 403 | Insufficient capability, unsafe Basic request, transport/origin refusal or disabled initialization |
| 404 | Missing resource/history; absence does not prove nonexecution |
| 405 | Authenticated unsupported method, HFAPI007 |
| 409 | Stale cursor/policy, conflicting key, unfinished result or classified read-integrity refusal |
| 413 / 422 | Oversized / invalid strict request |
| 429 | HFAPI021: independent Basic verification capacity or failure throttle; exit20 |
| 503 | Capacity, draining or unavailable executor; HFAPI022 for unavailable protected host authority at Basic admission |
| 500 | Sanitized unexpected failure |

Read-integrity refusals retain their HFVER taxonomy/exit. Client configuration,
authentication and protocol failures exit 10; unavailable/uncertain observation
exits 20. Exact terminal domain results retain their own exits. See the complete
[CLI error taxonomy](cli.md#5-error-and-warning-taxonomy).

### Browser wire boundary

The browser contract registry selects precise payloads by HTTP method, route and
request mode. It preserves the existing ReadResponse, capabilities, acceptance,
operation and domain Envelope shapes. Identical command names do not imply
identical data: repository inventory differs from revision inventory, and
installed configuration validation differs from literal-candidate validation.
Stored operation results are interpreted using their original receipt route and
domain command. The private receipt store is not a public payload.

Generated runtime decoders reconstruct validated values from unknown input.
Serialized response fields must be present; browser decoding does not fill server
defaults. Explicit null, false, zero and omission retain their separate meanings.
Unsupported versions, forbidden fields, inconsistent identities or unaudited
schema/semantic changes refuse. See [schema compatibility](schemas.md#11-validation-summary)
and [contract development](development.md#generated-browser-contracts).

A browser read distinguishes a validated success, failed domain Envelope, HTTP
ApiProblem, protocol failure, transport failure and aborted observation. An HTTP
200 failed Envelope retains its original command, identity, errors and exit
classification. Validated partial failure data is informational; malformed or
unavailable data never becomes an empty inventory, zero capacity or readiness.
Unrecognized diagnostic codes remain text when their enclosing data validates;
raw rejected bodies and exception text are withheld.

The browser collects decoded response bytes under its own hard ceilings:
16 MiB for ordinary responses, 64 MiB for artifact reads, JSON depth 32,
1,000,000 value tokens and 100,000 aggregate object keys. These client ceilings
are independent of server configuration. Duplicate decoded keys, invalid UTF-8,
lone surrogates and unsupported numeric source context refuse. Integer tokens
must have integer syntax and fit both their field bounds and JavaScript's safe
integer range before conversion; an oversized count is unavailable rather than
rounded. Timestamp microseconds and exact publication identity are preserved.
Manifest path collisions use the pinned Python Unicode 16 NFC-then-full-casefold
rule, including canonical-equivalent spellings and full case expansions. The
browser does not substitute its engine's Unicode version or compatibility
normalization. Manifest Unicode processing has a shared 8,000,000-step ceiling;
exhaustion refuses the read rather than dropping files or collision checks.

Named client methods construct only same-origin registered routes under the
validated public prefix. Reads accept AbortSignal and bounded bodies. POST paths
are separate, use the required request metadata and never retry automatically.
Validated operation links cannot redirect to another origin, prefix or operation.
Query identities contain authenticated authority, archive and exact publication
scope; passwords and bearer values never belong in query keys or browser state.

The route-independent browser observation controller retains original keys/IDs
across navigation without introducing a submission endpoint or receipt format.
Its recovery metadata is bounded to32 records/64KiB; restored records are
unverified until authenticated original observation. Basic keys retain their
stable-subject namespace, while manually retained Cockpit bearer keys remain
unbound legacy references. ID observation does not prove creator/key ownership.
An explicit compatible reconnect can refresh the API instance/authority epoch
without rebinding the original operation's admitted authority. Authentication or
scope changes clear private cached evidence, including a local authentication
generation change whose returned values are identical.

One shared32MiB encoded logical-evidence budget bounds retained browser reads;
it is not an exact heap limit. Observation reads use an8MiB per-response ceiling
clamped to the existing route ceiling (including2MiB cards), two concurrent
reads globally/one per handle, at most three eligible GET retries after the
initial attempt at1/2/4seconds, and at most120 cycles or five minutes. Event
retention is32 events/64KiB per handle with explicit sequence gaps. These bounds
only lower existing client ceilings and add no server setting. Stop observing
aborts local reads, never execution. Unknown, missing, interrupted, partial and
failed results remain distinct; see the [browser recovery guide](web-ui/operations.md).

## Reconnect after lost acknowledgement

1. Retain the original key, route, configured authority and credential class
   (plus the same stable subject when using Basic).
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

## Web UI and administration design

Optional Basic authentication and the indexed `/ui/` navigation/assets/bootstrap
surface are implemented in unreleased source, preserving existing REST/MCP
credential classes and strict public schemas. Protected host status and managed
configuration read/validation/preview, guarded application and exact-publication
card reads are implemented in unreleased source. Other host controls below retain their
separate design and acceptance obligations. These source additions do not change an installed release or grant
host authority.
See [UI availability](web-ui/README.md), [authentication decision](adr/decision-140.md),
[host/configuration decision](adr/decision-141.md) and
[card decision](adr/decision-142.md). Each addition requires executable
unit/integration and real installed functional evidence before support is claimed.

Preserve all current endpoints and wrappers. Add only these surfaces, with the
configured public prefix before `/api/v1` or `/ui/`:

| Method/path | Required authority and outcome |
| --- | --- |
| `GET /api/v1/config` | Explicit configuration-read administration capability and protected helper proof; strict nonsecret installed projection and opaque exact-byte base revision |
| `POST /api/v1/config/applications` | Explicit configuration-write administration capability plus protected host policy; keyed admission and guarded helper application, never arbitrary policy paths |
| `GET /api/v1/config/applications/{operation_id}` | Configuration-read capability plus original subject-scoped application key; protected outcome observation without replay |
| `GET /api/v1/repositories/{repository_type}/{namespace}/{name}/publications/{commit_sha}/{publication_id}/card` | REST metadata read; exact retained publication and bounded adjunct only |
| `GET /api/v1/host/status` | Explicit administration-read capability; bounded selected-profile, permissions/reasons, fixed unit/timer and sync-schedule revision facts |
| `POST /api/v1/host/sync-schedule/validations` | Explicit schedule administration capability and host policy; bounded read-only fixed systemd calendar/timespan validation |
| `POST /api/v1/host/sync-schedule/changes` | Explicit schedule administration capability plus protected supported-profile proof; keyed closed action `pause`, `resume`, `replace` or `reset`, with exact expected revision |
| `POST /api/v1/host/sync-observer/stops` | Explicit observer administration capability plus policy; keyed fixed stop with exact expected invocation identity, never job cancellation |
| `GET /api/v1/host/journal` | Explicit administration-read capability plus policy; fixed source, bounded page/cursor, redacted diagnostics rather than job outcomes |
| `GET`/`HEAD /ui/` recognized navigation/assets and `/ui/bootstrap.json` | Basic administrator only, fixed indexed non-archive assets and independent nonsecret UI bootstrap |

Do not add duplicate models/datasets/dashboard/tag CRUD, generic payload/URL,
schedule GET, arbitrary unit/terminal, cancellation, SSE or WebSocket routes.
`host/status` includes the sync schedule and display-only verification timer facts.
Rootless schedule/observer changes remain denied while fixed system-manager
bindings are unproved; supported native positive paths still require acceptance.

[Decision147](adr/decision-147.md) fixes the exact strict asset/bootstrap schema1,
configured-policy archive identity, compiled build/source binding, route/HEAD/
cache/header behavior and finite protected capture/send budgets. UI bootstrap is
plain typed JSON, separate from the existing Envelope and `/capabilities` schemas;
it grants no archive health or protected host authority. Every UI asset/alias/error
is Basic-only while REST bearer and read-only MCP remain independent. Enabled UI
requires the exact immutable manifest hash and actual installed version/wire
identity before admission; disabled UI reads no asset or mount data.

Public prefix migration rejects leading `//` explicitly. Operation JSON links
retain raw canonical application spelling; only the single Location header is
UTF-8 URI-encoded with the shared path encoder. Both client boundaries compare
that exact encoded header separately from raw links, preserving original keys
and uncertainty/no replay on malformed acknowledgments. Ordinary supported
ASCII/native CLI behavior is byte-identical. Previously accepted Unicode or
unsafe-ASCII server prefixes had invalid/inconsistent header behavior; no old
CLI Unicode support is claimed. The new UI-specific prefix/origin size ceilings
apply only to enabled UI, as documented in [server configuration](server.md).

### Managed configuration form

The new strict `ManagedEditRequest` is `{base_revision, edits}`. Extend existing
validation/planning DTOs with `{managed: ManagedEditRequest}`, mutually exclusive with literal
`candidate`. Installed `{}` and existing candidate forms retain their exact
request canonicalization and response shapes. Legacy plans retain existing
`selectors`; the managed form requires them omitted or empty. The server derives
the exact newly added, enabled or retargeted enabled repository set required by
the existing configuration-preview rule, never a caller subset. Nonempty scope
requires complete Hub sizing and explicit Hub host permission. Empty scope still
requires a successful bound managed assessment after validation, without Hub
contact; this includes tag/settings/removal-only and all-disabled changes. Apply
verifies exact required scope, resolved revisions where sized, and complete
assessment. Existing preview exemptions remain; no new tag-only exemption is added.
Managed forms require explicit configuration administration capability and a new
independently versioned assessment projection; ordinary bearer writer authority
does not grant helper access. Reject unknown fields, explicit nulls where a value
is required, mixed forms and coercions.

`edits` contains at most 256 entries in a closed discriminated union:

| `kind` | Fields and constraints |
| --- | --- |
| `repository-upsert` | `repository`: complete existing strict repository configuration fields; server applies by `(type,id)` |
| `repository-remove` | `repository_type`, `repository_id`: existing grammars; remove configuration only, never retained content |
| `settings-replace` | `settings`: nonempty closed optional field replacements under `storage`, `sync`, `verification`, `repair`; values retain existing strict field constraints |

Each repository identity may be touched only once; there is at most one
`settings-replace`, and every supplied nested settings table must be nonempty.
Editable storage fields are `publication_mode`,
`minimum_free_space_gib`, `minimum_free_space_percent`, `maximum_revisions`.
Editable sync fields are the current documented fields in that table;
verification permits `lock_wait_seconds` and repair permits
`retired_instance_grace_hours`. Algorithm and required hashing remain protected,
as do root/UUID/Hub/credential/server-policy keys.
Resolve edits against fresh installed policy server-side and preserve hidden and
protected fields; do not accept JSON pointers, paths or redaction placeholders.

Read binds the complete installed document, including tag-only changes, to a
strong opaque `base_revision` using a protected stable HMAC key. Do not return
secret-dependent full-document hashes. Application is
`{managed: ManagedEditRequest, preview: {operation_id, key}}`, naming the exact
required successful managed assessment and its original idempotency key. Revalidate original identity, exact
candidate/base, complete required sizing or explicit empty-scope assessment,
server-derived scope and current capability/policy before installation.
A preview reference is evidence, never
a transferable authorization token. Configuration documents remain at most 1 MiB.

Apply follows existing exact candidate/base comparisons under the original config
lock, durable predecessor backup, atomic `0640 root:hfcache` install and exact
post-install bytes/fingerprint confirmation. The lock is released during Hub
sizing. Receipt/helper interruption yields explicit staged, unchanged,
installed_unconfirmed, confirmed, conflict or unknown observations through original handles;
it never causes automatic replay, rollback or evidence cleanup. Generic receipts,
events and results contain no raw configuration or credentials.
Unknown existing candidate/backup evidence refuses application and is preserved.
A known predecessor backup tied to a confirmed helper outcome may be superseded
only after a durable per-operation private copy preserves it; replacing the fixed
backup never deletes uncertain or unexplained history.

### Guarded configuration application and original outcomes

POST `/config/applications` accepts exactly `ConfigApplicationSubmission`:
`{managed: {base_revision, edits}, preview: {operation_id, key}}`. Supply a new
application `Idempotency-Key`, distinct from the preview key. Every change,
including an empty sizing scope, requires the original successful complete
managed assessment for the same exact base, candidate and derived scope.
The preview/key confer no permission. Admission and queued execution recheck the
current configuration-write grant, independent host policy, protected authority
and exact candidate identity; nonempty scope also requires Hub permission.
Apply performs no Hub request and never repeats the preview.

HTTP202 returns the ordinary original operation receipt. Durable admission and
a fixed transmission-intent event precede helper effects. Canonical request data
is represented by its digest; raw configuration, credentials, preview keys and
private helper diagnostics never enter generic receipts/events/results. A
matching duplicate key returns the original receipt before new helper preparation;
conflicting data refuses. The fixed helper performs one guarded application under
the original configuration flock. An existing operation ID is observe-only,
including another identical apply request. No restart or observation replays it.

GET `/config/applications/{operation_id}` requires configuration-read capability
and the **application's** original `Idempotency-Key` under the same authenticated
subject. It returns an Envelope with command `config outcome` and strict
`ConfigApplicationOutcome` data: `schema_version`, `archive_id`, `operation_id`,
`request_digest`, nullable `base_revision`, nullable `candidate_revision`, nullable
`config_fingerprint`, `state` and `pending`. The three nullable identities are
all present or all null; states other than `unknown` require them. States are
`staged`, `unchanged`, `installed_unconfirmed`, `confirmed`, `conflict`, `unknown`.
These are independent host observations, not new generic receipt states.
Only `confirmed` with `pending=false` establishes a completed application.
An interrupted generic receipt remains interrupted even when its original
protected outcome proves confirmation. A later legitimate configuration change
does not invalidate authenticated historical confirmation.

Missing/corrupt/unknown private history, unresolved outcomes or a surviving
pending marker block new applications. Reads create no state or lock and perform
no repair. Do not resubmit with another key, roll back automatically, remove the
marker, discard a backup or clean private history to unblock work. Preserve the
original receipt/key and follow the [configuration recovery procedure](web-ui/configuration-and-tags.md#observe-an-interrupted-application).

### Managed configuration read and assessment responses

GET `/config` has no query/body parameters and requires configuration-read
administration plus independently provisioned configuration permission. It returns
an ordinary authenticated read wrapper whose command is `config read`; `data` is
independent schema1 with `archive_id`, `base_revision`, `editable`,
`editable_fields` and `protected_fields`. `editable` has complete repositories
and only the eleven supported settings, with defaults materialized. Metadata lists
fixed editable paths and protected `{field,description}` entries without values.
No raw TOML, Hub/credential values or full-document hash is returned.

Managed validation requires configuration-write administration and configuration
permission. Its `config validate` data is independent schema1 with `archive_id`,
`base_revision`, `candidate_revision`, `required_selectors` and `valid=true`.
Malformed edits refuse as requests; legacy literal syntax/authority results keep
their existing shapes. `candidate_revision` is a domain-separated opaque HMAC,
not a content hash. Upsert is a complete repository replacement with the existing
defaults; remove requires a configured identity. No edit can replace protected
fields. Canonical TOML reconstruction discards comments/formatting, uses fixed
ordering/escaped strings and obeys the1MiB whole-document limit. Full original
bytes, including comments/tags, determine base identity.

A managed plan still returns202 with the existing original operation handle.
Its terminal `plan` data is independent schema1 with those same bound identities,
`required_selectors`, `complete` and nullable `sizing` (the existing strict plan
projection). Empty scope succeeds with `complete=true,sizing=null` and no Hub
permission/contact. Nonempty scope requires fresh explicit Hub permission and
all required repositories completely sized; missing/failed sizing never yields
complete acceptance. The runner rechecks the full-byte base and all protected
authority after queue waiting, before any Hub access. Generic records contain no
raw base/candidate. A stale base yields `HFAPI007` conflict, including a classified
failed original operation if the change occurred after admission.

Read-only preparation uses one descriptor-pinned capture and bracketed exact
revalidation, creating no lock/candidate/backup/outcome. Persistent staging and
installation still require the original configuration lock. A duplicate POST may
refuse after base/policy changes; retain its original key/ID and read observation
routes instead of submitting another preview. Validation and planning install
nothing. See [managed reconstruction](adr/decision-153.md) and the
[configuration guide](web-ui/configuration-and-tags.md).

### New presentation and host bounds

`GET /api/v1/repositories/{repository_type}/{namespace}/{name}/publications/{commit_sha}/{publication_id}/card`
accepts no query parameters or body selectors. It requires normal REST read
authority: reader, writer or Basic administrator; MCP credentials do not grant
REST access. No archive-write or protected host-helper permission is needed for
this read. Use the configured public prefix as for other REST routes.

The ordinary read wrapper has command `card read`, `next_cursor: null` and a flat
strict [RepositoryCardRead schema 1](schemas.md#card-read-projection-schema-1)
in `envelope.data`, not a nested card object. Archive/repository/SHA/publication/
generation, manifest identity and source identity bind the exact selected retained
publication. A current-pointer change cannot select another card. Missing retained
ref, a valid ref naming another publication, or a missing requested manifest/tree
returns404 without falling forward to current or a repair replacement. Orphan
card/manifest files do not authorize a read.

A missing adjunct returns200 with `state=not_captured`; it creates no record.
`captured_at`, `presentation_version`, `markdown` and `presentation_sha256` are
null and diagnostics empty. Its source path/expected digest come only from the
manifest, or are both null when no root README is listed. A stored `absent` card
instead records an actual capture finding no manifest-listed README. The other
stored states remain explicit; only `present` carries sanitized Markdown and its
matching UTF-8 digest. A present empty string is valid.

Malformed authoritative metadata is classified `HFVER007`/`HFVER008`; corrupt,
unsafe, unknown-version or mismatched adjuncts are `HFVER007`, not successful
empty content. Metadata/parser work exhaustion is `HFAPI005`. The API rechecks
retained ref/manifest identity after reading the adjunct and refuses unsafe
presentation or any output sanitization that would change its body/identity while
retaining an old digest. The typed browser client binds the exact request identity
and verifies present-body SHA-256 with native WebCrypto before exposing data.

Presentation UTF-8 and JSON-string bytes each fit1MiB. The complete encoded read
response fits the smaller of configured `max_response_bytes` and2MiB, checked
before headers; response overflow returns413. Reads share the normal bounded
metadata pool and lease through encoding, response completion and disconnect;
cancelling an observer cannot release a still-running worker's slot. Responses
retain `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`.

Card GET reads adjunct and authoritative metadata only. It never opens README or
other file payloads, acquires the archive writer lock, resolves Hub credentials,
contacts Hub, writes, refreshes or verifies publication content. There is no raw
README, HTML or general file endpoint. Browser rendering remains later work;
this API does not enable a card view. See the [read procedure](web-ui/readme-cards.md#read-one-exact-publication).

Calendar expressions are one nonempty printable ASCII line, at most 4096 bytes,
without backslash; delay is a printable ASCII line at most 256 bytes without
backslash. Only `replace` carries them. Journal source is `sync`, `verification`,
`api` or `worker`, with at most 200 events and 64 KiB serialized page, bounded
opaque cursor and no arbitrary filters/unit/path. Helper protocol is independently
versioned, closed and peer-verified; its absence is unavailable, never fallback.

Basic browser authentication and effective permission/bootstrap context use
separate schemas. Existing bearer credentials, fourteen read-only MCP tools,
public operation credential-class grammar and strict capabilities remain unchanged.
Unsafe Basic requests require exact configured Origin, JSON and a non-simple
application header; nonbrowser bearer no-Origin behavior remains compatible.
No UI fallback may consume REST/MCP paths or errors. See [server configuration
design](server.md#web-ui-design-and-current-availability) and
[browser security](security.md#browser-administration-design).
