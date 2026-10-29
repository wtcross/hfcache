# Writer server reference

Run one authenticated writer application with one registry, metadata pool, heavy
lane and daemon-instance lock across its enabled listeners. The daemon does not
hold the archive-operation lock for its lifetime. Run a single process without
auto-reload; heavy work stays outside the ASGI event loop. Operational clients
use [REST](api.md), while the separate offline worker performs verification.
No request starts a daemon/worker or falls back to local verification.

## Deployment profiles

| Profile | Executables and managers | Listener and credentials |
| --- | --- | --- |
| Guarded rootless | Fixed `/usr/local/libexec/hfcache-client` and container-service launcher; image Python/application under `/opt/hfcache/.venv/bin`; user API/worker/Caddy services behind system bridge/independent host guard | Unix-only API `/run/hfcache/api/api.sock` behind Caddy TLS; notify-ready worker-created `/run/hfcache/verification/verification.sock`; explicit Podman secret files, none in worker |
| Native | Host release `.venv/bin`, system API/worker services and named socket activation | API `/run/hfcache/api.sock`, private `/run/hfcache/verification.sock`; systemd named credentials, worker receives none |

The selected recorded rootless profile keeps NAS read-only, writer masks,
disabled calendars, both operation stores, pending handles and original locks.
Its API requires the ready worker **service**. The indexed rootless `.socket`
artifact stays dormant with `RefuseManualStart=yes`; native named-FD3 activation
remains supported. Native tools positively classify release layouts and refuse
container/mixed/unknown targets. No identical unit name implicitly selects another
manager. See [scripts](scripts.md), [containers](containers.md) and
[recorded deployment restrictions](deployment-status.md).

## Public prefix and native Unix requests

TCP uses the configured public `root_path`. Native unprefixed REST requires both
`client=None` and a corroborating local `(absolute Unix path, None port)` server
address; missing peer alone is insufficient. Headers cannot assert locality.
Native Unix also accepts public-prefixed spelling, and operation/docs links use
the trusted effective prefix. Prefix overlap recognizes a valid prefixed REST/MCP
remainder first. Native unprefixed OpenAPI gets a response copy with server `/`;
the public cached schema is not mutated. Authentication, Host/Origin policy and
all resource limits apply to either spelling.

## Server configuration

[`ServerConfig`](../src/hfcache/server_config.py) independently of the archive
TOML. `load_server_config` reads UTF-8 TOML and
`validate_server_config_mapping` applies strict frozen models with unknown keys
forbidden. There is no type coercion or literal-token field. Path values must be
absolute normalized strings below `/`, with no `..`, trailing slash, backslash or
nonprintable character.
Validation exposes stable code/shape diagnostics without echoing input values,
unknown caller-selected keys or raw TOML exception text. Existing HFCFG codes
classify missing/unreadable files, malformed TOML, unknown fields, schema version
and invalid constraints. The configuration model itself adds no durable JSON
format; The independent local receipt schema is described separately below.

The server configuration default is `/etc/hfcache/server.toml`.
[`packaging/server.toml`](../packaging/server.toml) is an example for this separate
domain, not an addition to `examples/config.toml` and not an installed listener.
Server-configuration ownership remains operator-controlled `root:hfcache`; no API
installs listener/authentication settings. The separate guarded configuration API
can install only managed archive-policy edits through the protected host helper.
See [administration availability](#web-ui-design-and-current-availability).
Listener/auth settings are immutable until
restart. Configured TLS paths are declarations; the listener loads and validates
the certificate/key before accepting connections.

| Top-level key | Type/default | Constraint or meaning |
| --- | --- | --- |
| `schema_version` | required integer | Exactly `1` |
| `archive_config` | path, `/etc/hfcache/config.toml` | Installed archive policy, not caller-selected candidate authority |
| `state_directory` | path, `/var/lib/hfcache/api` | Local service-private control state; outside publication trees |
| `credentials` | required table | Required writer source and optional reader/MCP sources below |
| `basic` | absent | Optional restart-only Basic administrator; exact HTTPS origin and protected administrator source below |
| `listener` | table, defaults below | Unix/TCP/TLS and browser/proxy policy |
| `limits` | table, defaults below | Bounded resource policy for metadata, command routes and runner |
| `verification` | table, defaults below | Private executor client policy; no worker process is launched |
| `maintenance_enabled` | bool, `false` | Initialization only: requires this gate plus writer capability and explicit configured-target confirmation |
| `interactive_docs` | bool, `false` | Enables authenticated `/api/v1/docs`; `/api/v1/openapi.json` is always authenticated |
| `mcp_enabled` | bool, `false` | Optional MCP transport; requires installed `mcp` extra plus usable distinct `mcp_reader` source, restart-only |
| `log_level` | str, `"info"` | `debug`, `info`, `warning` or `error`; startup-only |

### Listener settings

| `[listener]` key | Default | Constraint |
| --- | --- | --- |
| `unix_enabled` | `true` | Enable the configured Unix socket; Unix and TCP cannot both be disabled |
| `unix_socket` | `/run/hfcache/api.sock` | Absolute normalized path; socket mode below |
| `socket_mode` | `0o660` | Only `0o600` or `0o660` |
| `tcp_enabled` | `true` | Enable the configured TCP listener |
| `tcp_host` | `127.0.0.1` | Explicit IP address |
| `tcp_port` | `8787` | Integer `1`–`65535` |
| `tls` | absent | When present, `[listener.tls]` requires `certificate` and `private_key` absolute paths |
| `proxy_tls` | `false` | Only loopback TCP with explicit trusted proxies and no direct TLS |
| `allowed_hosts` | `["localhost", "127.0.0.1", "[::1]"]` | Nonempty distinct explicit host names/IP forms, with no wildcard, port or URL |
| `allowed_origins` | `[]` | Exact HTTP(S) origins; no wildcard, userinfo, path, query, fragment or whitespace |
| `trusted_proxies` | `[]` | Explicit IP addresses or canonical networks; no wildcard or prefix-zero network |
| `root_path` | `""` | Empty or normalized absolute URL prefix, no trailing slash, traversal, query, fragment, backslash, percent escape or whitespace |

Listener strings reject nonprintable characters before URL parsing. Both local
listeners default enabled; use explicit `unix_enabled`/`tcp_enabled` booleans to
select one in TOML, which has no null literal. At least one must remain enabled.
`ListenerConfig.unix_address` and `.tcp_address` expose only enabled addresses
to server wiring; unused configured addresses retain strict validation.

Unix sockets authenticate exactly as TCP does. Non-loopback TCP requires direct
TLS. An off-host TLS proxy connects only to loopback TCP and requires
`proxy_tls=true` plus explicit trusted proxy addresses; forwarded headers are
never trusted from everyone. The config model validates those combinations;
The HTTP boundary applies Host/Origin/proxy-prefix policy at the HTTP boundary.
No wildcard CORS, token query parameters or URL userinfo is permitted by the
management contract. The client always verifies off-host TLS.

### Resource settings

| `[limits]` key | Default | Range |
| --- | --- | --- |
| `max_request_bytes` | `1048576` | `1024`–`16777216` |
| `max_page_size` | `1000` | `1`–`10000` |
| `metadata_workers` | `4` | `1`–`32` |
| `metadata_queue` | `32` | `1`–`1024` |
| `max_queued_operations` | `16` | `0`–`64` |
| `retained_terminal_operations` | `1000` | `1`–`100000` |
| `shutdown_timeout_seconds` | `300` | `1`–`86400` |
| `max_response_bytes` | `8388608` | `1024`–`67108864` |
| `max_artifact_bytes` | `67108864` | `1024`–`1073741824` |
| `max_scan_entries` | `10000` | `10`–`1000000` |
| `operation_max_receipt_bytes` | `1048576` | `4096`–`16777216` |
| `operation_max_result_bytes` | `8388608` | `1024`–`67108864` |
| `operation_max_events` | `256` | `1`–`10000` |
| `operation_max_event_bytes` | `2048` | `256`–`65536` |
| `operation_max_store_bytes` | `268435456` | `1048576`–`17179869184` |
| `operation_retention_days` | `30` | `1`–`36500` |

Read/body/response/work limits are enforced, and shutdown joins workers.
`retained_terminal_operations` conservatively caps **all** retained receipts; it
does not permit eviction of unexpired or unresolved history. Nonterminal and
interrupted operations reserve maximum receipt/result space, while terminal
succeeded/failed records consume actual bytes. Count/space pressure refuses
admission. Retention never expires ambiguous/nonterminal/interrupted evidence.

Metadata entry/artifact/aggregate-byte budgets apply to the complete underlying
scan, regardless of page size. Exhaustion returns HFAPI005/503, never a partial
success or higher verification confidence. Public operational CLI collection also
uses bounded HTTP and aggregate limits; it is complete or fails explicitly.
Metadata scans do not hash payload content, initialize or repair an archive.
See [response budgets](api.md#pagination-and-budgets).

### Private verifier client settings

| `[verification]` key | Default | Constraint |
| --- | --- | --- |
| `unix_socket` | `/run/hfcache/verification.sock` | Absolute normalized protected Unix-socket path |
| `expected_peer_uid` | omitted | Nonnegative integer when set; omission uses the API process's effective UID |
| `expected_socket_owner_uid` | omitted | Nonnegative integer when set; omission uses the resolved expected peer UID |
| `timeout_seconds` | `5.0` | Finite number, greater than 0 and at most 60; each bounded control exchange |
| `poll_seconds` | `0.2` | Finite number, greater than 0 and at most 60; exact operation observation interval |
| `max_frame_bytes` | `16777216` | Integer `1024`–`16777216` |

These are restart-only server-side client settings, not caller-selected request
values or worker-launch permissions. Omit `expected_peer_uid` to use the service
UID; TOML has no null literal. The worker's separate store uses fixed default
`OperationLimits`, independently of API receipt-limit overrides.
Its state directory must be provisioned separately, never nested with API state.

Socket ownership and kernel peer credentials are independently checked. For
native system-manager activation, retain the original service-owned socket and
configure `expected_peer_uid = 0` plus `expected_socket_owner_uid` equal to the
actual service account's numeric UID. The root manager created the listener;
its kernel credential is not the accepting worker's UID. Rootless worker-created
listeners retain their existing equal owner/peer UID and can omit the new owner
setting. Omission preserves the previous ownership rule for every configuration.
Neither setting changes worker ownership validation, inode/mode/parent checks,
API-client authentication, activation mode or execution permissions. See
[decision 148](adr/decision-148.md).

### Archive-policy reload

`InstalledPolicy.open(server_config)` pins the installed archive root and UUID
at startup. Every `snapshot()` reloads and validates the archive TOML, returning
a frozen `PolicySnapshot(config, fingerprint)` using the existing archive
fingerprint. Earlier snapshots remain unchanged. Invalid updates fail new
archive work; changed root/UUID fails closed with `HFCFG005` until restart.
API credentials never enter the archive snapshot or fingerprint; no new server
fingerprint format exists. Each archive query takes a snapshot;
queued mutation additionally reloads/compares policy under the archive lock before a
queued mutation. These primitives do not install policy or switch archive
authority. Version/capabilities do not need a fresh archive snapshot; health can
diagnose failed updated policy without silently switching archive authority.

## Credentials and capabilities

`[credentials.writer]` is mandatory. `[credentials.reader]` and
`[credentials.mcp_reader]` are optional. Each configured source contains exactly
one `file` absolute path or `systemd_name`; the latter resolves only through the
absolute `CREDENTIALS_DIRECTORY` supplied by systemd. Names use
`[A-Za-z0-9._-]{1,64}`, excluding `.` and `..`. An absent optional source disables
that class. Every active configured source must load successfully; Disabled MCP skips
the MCP source entirely while disabled, even if configured. Missing, unsafe,
racing or malformed active sources fail startup with `HFAPI003`, and duplicate
active class values fail with `HFAPI004`. No ambient Hub/API
token is discovered, no Hub credential is forwarded, and API tokens never appear
in process arguments or configuration.

[`read_protected_token`](../src/hfcache/api/auth.py) opens every path component
relative to pinned directory descriptors and refuses symlinks. The credential
directories are held with Linux `O_PATH` descriptors: the service needs search
access to each parent, not permission to read or list the directory. Only the
credential leaf is opened for reading. This preserves an independently confined
credential directory without adding a directory-read permission.
The credential
must be a regular inode owned by root or the effective server user, with exactly
one hardlink and mode `0400`, `0440`, `0600` or `0640`. Reads stay on the checked
inode across pathname replacement; bounded reads and before/after descriptor
metadata refuse content/ownership/mode changes to that inode. Group access
must be provisioned deliberately for the service identity; world access and
executable/writable-by-group modes refuse loading.
For ordinary group-readable files, the credential group must be the server's
effective or supplementary group. One alternative covers a root:root `0440`
inode: its descriptor-read POSIX access ACL must be exactly owner-read, one
named effective-UID read entry, owning-group-none, mask-read and other-none,
without additional entries. Stat group bits here describe the ACL mask, not
root-group read access. Require the canonical five-entry, 44-byte Linux version-2
value. Missing, inaccessible, unsupported, malformed or different ACLs refuse
this alternative. Compare the ACL before and after bounded content reading,
then recheck all descriptor metadata. Authentication changes no permissions and
copies no delivered credential. See [decision152](adr/decision-152.md).
The unreleased source reader implements this policy; installed application
acceptance remains a separate deployment check.

Provision a high-entropy opaque token, alone in the file with at most one final
LF. The token must have `32`–`4096` ASCII characters matching the RFC 6750 bearer
alphabet (`A`–`Z`, `a`–`z`, digits, `.`, `_`, `~`, `+`, `/`, `-`, followed by at
most two `=` padding characters); the file is at most `4097` bytes. Hub-style
`hf_` values are rejected as API credentials. Length/shape
validation is not a proof of entropy. Literal values are registered for shared
redaction before use; the auth registry retains only fixed-size SHA-256 digests.
Its authentication loop compares all three fixed capability slots, using dummy
digests for disabled slots, through `hmac.compare_digest`.

| Credential class | Accepted interface | Principal capabilities |
| --- | --- | --- |
| REST writer | REST only | `read`, `write`; maintenance/domain gates still apply |
| REST reader | REST only | `read` |
| MCP reader | MCP only when enabled | `mcp-read`; rejected by the REST verifier |

The framework-independent bearer verifier returns a frozen nonsecret `Principal`
with the configured class, method `bearer`, fixed subject
`credential-class:<class>` and no administrative grants. It identifies a class,
not an individual user or token-derived identity. Every reader must be authorized
for the whole archive,
including restricted repositories (AD-21). Cross-interface credentials and
missing/malformed/invalid bearers all receive `HFAPI001`, HTTP 401 with
`WWW-Authenticate: Bearer realm="hfcache"` and `Not authenticated`; a valid
principal missing a required capability receives `HFAPI002`, HTTP 403 `Forbidden`.

The optional [`api.security`](../src/hfcache/api/security.py) adapter supplies
`BearerAuthentication(registry)` and `RequireCapability(authentication, capability)`.
It validates the original single bounded Authorization field before FastAPI can
normalize input, delegates verification to the core and preserves those
responses. The adapter itself creates no application. The outer HTTP boundary
dispatches the selected provider before framework routing/validation on every HTTP
surface, including health, capabilities, docs, OpenAPI, unknown paths and method
errors, and sanitizes validation/exception output. Receipts store only the
nonsecret principal and operation/domain correlation, never a token, credential
digest or source path. Their private idempotency-key digest is a separate
comparison value and is never exposed by HTTP.

Rotation means replace the protected credential, then restart the server to load
it. Existing clients must use the new value on subsequent requests; stale tokens
fail authentication after restart. No request mutates the registry or discovers
replacement credentials automatically. Enabling MCP activates the existing MCP source
only when `mcp_enabled` is true; disabled MCP never reads that source. Enabling
requires a usable distinct credential and the optional package. It exposes
exactly fourteen metadata tools through a narrow
read protocol; no resources/prompts or command paths. See [MCP](mcp.md).

### Basic administrator

Optional restart-only `[basic]` has exactly `origin` and `administrator`.
The origin is one browser-canonical HTTPS origin without userinfo, path, query,
fragment, whitespace or explicit default port; its host must be allowed by
`listener.allowed_hosts` and the exact origin by `listener.allowed_origins`.
`[basic.administrator]` contains exactly one existing `CredentialSource` form:
protected `file` or named `systemd_name`. Absence disables Basic without reading
a record. A configured unusable source fails startup with HFAPI003; it never
falls back to bearer, another file or an ambient source. The writer bearer source
remains mandatory. See [decision146](adr/decision-146.md).

The protected UTF-8 JSON record is at most 8192 bytes, has no duplicate/unknown
fields and contains exactly integer `schema_version:1`, `subject`, `username`
and `password_hash`. Subject matches `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`;
username is nonempty printable UTF-8, at most 128 bytes, without colon. The record
uses the same no-follow, owner/group/mode, single-link, descriptor-race policy
as bearer files. Only the API receives this record. Never put a plaintext password
in TOML, arguments, environment, files, logs or browser JavaScript.
The provisioning helper emits canonical sorted, two-space-indented UTF-8 JSON
with one final newline; this private schema 1 has its own golden fixture and is
independent of archive-format versioning.

The rootless template uses the optional protected file
`/etc/hfcache/credentials/ui-administrator.json`. The API's existing read-only
`/etc/hfcache` bind supplies it; worker/client already mask the fixed credentials
directory, and Caddy has no `/etc/hfcache` bind. Enabling Basic adds no unconditional
Podman secret or `runtime.json` migration. The native template instead names
`hfcache.ui-administrator`; its optional `LoadCredentialEncrypted` drop-in must be
provisioned and activated separately. These packaging paths do not establish
installed role isolation or authorize changing a running deployment. See the
[operator deployment instructions](web-ui/deployment.md).

The PHC string must be canonical ASCII Argon2id/version 19 with exact ordered
`m=65536,t=3,p=1`, unpadded standard-Base64 salt 16 bytes and hash 32 bytes. Startup
checks the complete profile before constructing a verifier; a hash cannot select
larger memory/time/parallelism. The optional server profile uses its locked
cryptography implementation. Encoded Authorization is at most 8192 bytes, decoded
UTF-8 username at most 128 bytes and password at most 1024 bytes. Wrong username and
password use the same configured hash work, then combine constant-time username
comparison with the verification result. Failed supplied passwords are never
registered as global redaction literals; Basic Authorization is scrubbed by shape.

A dedicated two-thread executor owns at most two active attempts and eight
waiting requests, independently of metadata/operation observation. A bounded
global sliding 60-second deque counts failures, and active attempts reserve their
possible failure under the same lock. When failures plus reservations reach 30,
refuse further expensive work; queued attempts recheck at actual start. Capacity
and throttle refusals are HFAPI021/HTTP429/exit20. Cancellation retains the slot
until actual work completes. Stop new admission, drain every accepted job and
join exact workers under lifespan cancellation deferral, including partial-startup
cleanup. A draining/failed provider is unavailable, never a successful login.

Basic projects as public `rest-writer` with the unchanged `read`/`write` array.
Its separate immutable internal grants are `config-read`, `config-write`,
`host-read`, `schedule-write`, `observer-stop`; ordinary bearer writer has none.
These grants alone authorize no host effects or protected configuration install;
the separate helper/policy boundary remains required. Protected status and fresh
Basic job checks use the [host helper](host-administration.md); configuration
application additionally requires its fixed guarded writer and matching preview.
The UI advertises implemented configuration-read and configuration-write
affordances from those respective grants; neither is gated by host-read. Each
configuration request still enforces its own current capability and protected
policy. The browser composes existing endpoints only: one editable draft, exact
managed validation/preview/application and explicit original-outcome reads add
no server endpoint, TOML upload or automatic retry.
Basic never authenticates MCP. No new class, permission, subject or attribution
field joins the stable capabilities response or old strict receipts.

Missing REST credentials advertise Basic and Bearer when configured; explicit
REST Basic failures with the provider configured advertise only
`Basic realm="hfcache", charset="UTF-8"`.
Explicit bearer and MCP failures retain the existing Bearer challenge. Invalid
credentials remain HFAPI001/401; missing capability remains HFAPI002/403.
Disabled Basic retains the legacy Bearer challenge. There is no scheme fallback.
Browser-managed Basic lifetime has no reliable
application logout. Rotation replaces the protected hash record and restarts
the API; preserving subject preserves original-key ownership across username/
password changes. Changing subject deliberately selects a new key namespace.

Authenticated REST OpenAPI describes Basic and Bearer as alternatives only when
Basic is configured; disabled configurations retain the bearer-only description.
The Basic schema marker does not decode a password or authenticate a request;
the outer provider remains authoritative, including UTF-8 credentials. MCP stays
outside the REST schema and retains its separate bearer-only boundary. The schema
also documents HFAPI021/429 with the existing typed problem response.

For configured Basic, cheap header/query/content-length work bounds and TLS proof
precede Argon. Missing credentials and bearer authentication retain their existing
precedence over work limits.
Ordinary Host/Origin/routing checks and Basic CSRF follow authentication, before
body reception. Every method except GET/HEAD requires exact single configured
Origin, application/json (optional UTF-8 charset) and exactly
`X-Hfcache-Request:1`, without content encoding. This includes OPTIONS/preflight,
TRACE, CONNECT and unknown/denied paths. Missing/null/foreign/duplicate Origin,
simple forms and missing/duplicate/wrong intent refuse HFAPI010/403. Legacy
nonbrowser bearer requests still need no Origin.

Authenticated native Unix scope uses both peer and local-address corroboration.
Actual numeric-loopback HTTP is permitted for local access; remote Basic requires
actual HTTPS or configured `proxy_tls`, trusted actual peer and exactly one
`X-Forwarded-Proto:https`. A caller header cannot assert TLS or Unix locality.
Real native browser challenges/TLS and installed profile delivery require their
own acceptance; source tests do not enable or deploy any service. Authenticated
SPA/static serving is separately enabled and governed by the immutable asset
boundary below.

## Metadata lifespan and request boundary

Authenticate before routing, body reception/validation and ordinary errors on
every HTTP surface, including health, schema/docs, unknown routes and methods.
Configured Basic's cheap header/query/content-length bounds and TLS transport
proof are the explicit pre-verification exceptions; they never receive a body or
route work. Missing/bearer credentials preserve authentication before work limits.
Enforce Host/Origin, content type, header/query/body/response bounds and sanitized
errors. No wildcard CORS, query bearer or reflected redirect is permitted.
Trusted proxies are explicit; headers cannot upgrade caller capabilities.

The daemon holds `/run/hfcache/api.lock` throughout its lifespan, separately
from the operation-store lock and archive flock. Its pre-existing parent is
opened without following symlinks; the lock must be an effective-user-owned,
regular, single-link mode-0600 inode. Invalid or already-held locks fail with
`HFAPI011`. The application never unlinks this lock.

One bounded metadata pool is shared across listeners. Capacity covers both the
worker and response/stream lifetime, including disconnected observers, so a client
cannot release a slot while its scan still runs. Request cancellation never
abandons ownership prematurely. Metadata uses safe no-follow reads and frozen
policy snapshots; it neither hashes repository content nor reconstructs a catalog.
Health readiness does not certify archive integrity or open execution admission.

Reference and manifest parsing can reuse a frozen model only after the current
anchored read returns identical bytes and charges the current query budget.
The process retains at most512 reference inputs of at most4KiB each and one
manifest input between64KiB and8MiB; other inputs parse normally. This bounds raw
keys at10MiB, separately from decoded model and active-worker memory. Parser
entries contain no filesystem capability or authenticated response. Fresh policy,
archive identity and publication/retention joins remain required; missing,
replaced, unsafe or exhausted reads still refuse. See
[the parsing decision](adr/decision-157.md).

Request IDs are server-generated, separate from operation IDs and domain report/
journal run IDs. Execution correlation is context-scoped and copied into workers;
invocation mode describes the execution host, not a timer/submitter origin.
A credential class is not individual user attribution. Logging is configured at
startup; client verbosity does not reconfigure the daemon. Diagnostics register
exact secrets before use and sanitize again on presentation, without echoing input.

## Command admission and policy authority

[The route matrix](api.md#routes-and-effects) is the canonical mode/capability/
effects inventory. Synchronous validation creates no receipt. Keyed plans,
diagnostics and maintenance previews create local control history even when they
preserve archived content. Plans and both diagnostic modes contact the Hub.
Apply reloads policy and reconstructs scope/evidence under the shared lock; posted
previews never grant apply authority. Initialization alone additionally requires
`maintenance_enabled`, writer authority, configured root/UUID and literal confirmation.

Candidate TOML is bounded content, never a server pathname, installation, Hub
source or durable replay body. Validity and installed compatibility are separate.
Planning compares root/UUID/Hub endpoint/token mode/credential name/expected
account and rechecks before execution, always using installed credentials.
The receipt retains admitted identity; matching retries do not reload changed
policy or enqueue again. No request can supply a generic executor, command,
configuration path, network credential or lifecycle-control escape.

## Operation control state

The application lifespan owns one `OperationStore` under `state_directory`,
separate from the archive lock and publication/export tree. The configured state
root and startup-pinned archive root must not overlap in either direction;
refuse this before creating any state directory or `.lock` inode. The state
parent must already exist; only the final private directory may be created,
mode `0700`, with parent fsync. Checked regular files use service ownership,
mode `0600` and one hardlink. Every component is opened no-follow, and bounded
reads stay on stable pinned descriptors. The retained control-state `.lock`
serializes store operations across handles/processes and is never unlinked.
It is separate from both the daemon-instance lock and archive-operation flock.

`OperationLimits` maps the server limits above, including the conservative
`retained_terminal_operations` ceiling across all receipts. Each unresolved
nonterminal/interrupted record reserves its maximum receipt plus result bytes;
terminal succeeded/failed records consume actual retained bytes. Full count or
reservation budgets refuse admission. A failed storage/fsync/write never makes
work runnable. Receipts themselves bind keys; indexes/scans are derived and no
command body is retained for replay.

Startup opens the store; shutdown closes its pinned descriptors only after
joined execution drain. Reconcile exact surviving executors before classifying
unresolved receipts. Unsupported/malformed/unexplained state is preserved and
blocks scan/admission, while healthy exact-ID reads and policy-independent
diagnostics remain available. A retained running label never proves liveness.
Core interrupt/expiry primitives are not HTTP mutation endpoints.

Operation observation uses authenticated bounded HTTP metadata work, never the
archive flock or a domain command. All REST read-capable principals share this
whole-archive metadata/result boundary; idempotency lookup alone uses the caller's
bearer credential-class or Basic stable-subject namespace. Bearer digest bytes
remain unchanged; Basic's versioned length-framed digest uses only subject and
the original key, with no printable surrogate or new receipt field. The
[API contract](api.md#admission-idempotency-and-lifecycle)
defines wire/status/event semantics; [control-state schemas](schemas.md)
defines the independent local family and retention compatibility. The execution
lane and strict route matrix preserve these boundaries.

## Bounded execution and private verification

One heavyweight FIFO lane is separate from the bounded metadata pool. Admission
must be durable before an item becomes runnable. Matching idempotent retries
return the original operation and never add another queue item. The pending
count is bounded by `max_queued_operations`; saturation and drain refuse new
admission rather than creating an unbounded executor queue.

A separate fixed host-action lane reuses the same operation store/runner lifecycle
for schedule changes and original scheduled-observer stops: one executing and at
most one queued action. Its route ownership is disjoint from the domain lane at
admission and startup reconciliation. It never acquires the archive flock or runs
archive/verification work. A long accepted backend job therefore cannot prevent
stopping its original client observer. Journal reads use neither effect lane.

Admission captures one absolute host-monotonic waiting deadline. Queue residence,
private delegation and archive-lock acquisition consume that budget without
resetting it. Domain execution may outlast its waiting deadline after safely
starting; the deadline is not an unsupervised cancellation timer. The trusted
`CommandLockControl` scope carries deadline, waiting/acquired and policy hooks
into the service-owned archive lock. The runner never pre-locks a command or
transfers its flock to another process. Under-lock policy reload must match the
admitted fingerprint before preflight/mutation; stale work fails visibly. Plain
local services retain their existing lock behavior when no control is scoped.
Zero wait permits one immediate lock attempt only when the lane is idle; it
never waits behind existing work. `max_queued_operations=0` still permits one
active item and no pending item. Matching retries remain observable even when
new admission is closed or capacity is full.

`OperationRunner(store, policy, max_pending=16, check_verification_available=...)`
owns this lane. Trusted adapters
call `submit(..., command, execute(snapshot, context), wait_seconds, ...)`;
the callable and frozen policy remain in memory, while only the receipt/digests
are durable. `start(reconcile=...)`, `stop_admission()`, `drain()`/`close()` and
`wait()` define lifecycle/observation. A wait timeout never cancels or requeues.
Trusted `delegated=True` forbids parent archive-lock acquisition; the verifier
acquires in its own process. In this domain lane, `requires_lock=False` is only for a genuine
non-mutating heavy read, which validates its snapshot before execution. These
flags are not caller-selectable request fields. A successful locking task must
prove that its service-owned guard ran; an arbitrary unlocked callback cannot
claim success. Unexpected local execution/result-persistence failure halts the
lane and preserves interruption rather than inventing a replacement result.
Fresh verification admission probes the configured executor before writing a
new receipt; a missing/untrusted adapter refuses with `HFAPI016`. Matching
idempotent retries bypass this fresh-only probe and retain their original binding.
The probe never submits or starts verification.
Fresh admission permits a trusted `wait_seconds(snapshot)` selector as well as a numeric
budget, so fresh admission uses the installed sync/verification waiting policy
without loading changed policy on an idempotent retry. No request field supplies
that callable or changes the server's waiting policy.

The separate verifier uses the same complete target/hash/report/catalog lock
boundary. The HTTP process imports its protocol/client without executing archive
verification. A missing/untrusted executor is `HFAPI016`, HTTP 503 / exit 20;
there is no production in-process fallback, process spawning from a request or
generic systemctl/sudo command. The supported native
units and rootless roles enclose the actual executor in credential-free/offline
confinement. Installed peer/cgroup/SELinux/network proof is distinct from source
fixtures; no process-spawning or in-process verification fallback exists.

### Verification wire and local trust

[`verification_protocol`](../src/hfcache/verification_protocol.py) defines a
schema-version-1 private stream protocol. Each UTF-8 JSON frame has a four-byte
network-order unsigned length, bounded before reading the body; the absolute
maximum is 16 MiB. An explicit integer `schema_version=1` is required; missing,
boolean and unsupported versions refuse. Strict models reject unknown fields, duplicate JSON keys,
contradictory actions, malformed IDs/digests, unsupported versions and nonfinite
deadlines. This is not an HTTP endpoint or a general RPC command surface.

| `WorkerRequest.action` | Allowed fields beyond `schema_version`/`action` |
| --- | --- |
| `probe` | None; availability only, no operation or archive work |
| `status` | Exact `operation_id` and expected `config_fingerprint`; never submits |
| `submit` | Same identity plus strict `scope`, finite nonnegative `lock_deadline` and optional `try_lock` boolean |

`VerificationScope` permits only `mode = new | full | revision`. `revision` is
required exactly for revision mode and must contain an immutable full SHA;
`run_id` is optional only for new mode. Estimates stay ordinary metadata reads
and cannot use this executor. No request contains a configuration path, archive
root, arbitrary command, candidate policy or credential.

`lock_deadline` is the original absolute host-monotonic deadline, computed from
the runner's remaining budget before connection. Both processes use the same
host clock; the worker additionally bounds it by its installed verification
lock-wait policy. IPC never starts a fresh waiting timer. `try_lock=true` is the
original zero-wait single-attempt mode, permitted only on submit; it cannot turn
a positive budget into a new timeout. Replies contain
`outcome = available | found | missing | unavailable | conflict`, nullable exact
`receipt` and nullable exact terminal `envelope`. A `found` reply needs its
receipt; succeeded/failed additionally require a matching domain run ID/exit
Envelope. The production client verifies requested operation ID/fingerprint,
fixed verification route and startup-pinned archive UUID before any progress or
result is trusted. A wrong archive is unsafe `HFAPI016`, never trusted missing
history. The reply's exact Envelope, serialized with the shared durable encoder,
must match its receipt result-reference SHA-256 and byte count as well as domain
run ID/exit coherence; wire frame length is a separate bound.
Trusted running progress also propagates the private receipt's domain run ID
into the parent API receipt; callers do not select that execution evidence.
A nonterminal private label alone is insufficient: status must prove the worker
still owns a live thread for that exact operation, otherwise it is unavailable.

Client connection opens every socket-path component no-follow through pinned
descriptors, checks the parent is root/service-owned and not group/world
writable, and requires an expected-owner socket of mode `0600` or `0660`.
It connects through that pinned parent, verifies Linux `SO_PEERCRED` UID and
checks that the named socket inode did not change. The worker verifies the
connecting API peer UID too. A path check alone, local socket transport alone or
caller PID does not authenticate this boundary. Protected parent/socket setup
and exact service identities are operator provisioning requirements.

### Restart and drain

Reconcile old nonterminal API receipts before admitting new execution. An exact
surviving verifier is awaited/reattached, and its exact durable terminal Envelope
can finish the API receipt after an acknowledgement/daemon crash without rerun.
Trusted missing/interrupted worker history permits parent interrupted
classification, preserving uncertainty. Unavailable, unsafe or mismatched peer/
protocol evidence does not prove the old worker ended: preserve the parent's
active receipt and close execution admission. Keep that barrier across later
daemon restarts until exact status is restored; do not mark it interrupted merely
to make a subsequent restart skip it and reopen the lane. Metadata and healthy
exact-ID history stay available. `health.ready` still describes the daemon,
not proof that execution admission is open. A delegation losing trusted status after submit
likewise halts the lane while preserving active evidence. Never requeue an old
queued/running receipt or reconstruct a command from archive journals.

Drain stops admission first and joins accepted work. A sync still joins its one
active producer before the archive lock is released. Client disconnect/Ctrl-C
stops observation; it does not cancel the real writer. Forced process death
leaves receipts/journals for diagnosis. Recovery must identify the actual
executor and operation, preserving the narrow supervised-cancellation checks.
The app stops admission to both domain and fixed host-action lanes before draining
either, and keeps the helper client available until both have drained. Only then
does it close helper/metadata workers, control store descriptors and the
daemon-instance lock. A blocked/heavy item does not
occupy the metadata pool; lightweight HTTP reads remain responsive while it runs.
Lifespan cleanup shields the entire runner/metadata drain against repeated task
cancellation before releasing store/instance ownership. This is joined graceful
shutdown, not a claim that SIGKILL can finish work.

Catalog search/detail/variant/facet reads share this metadata pool and its leases,
scan/artifact/response ceilings and shutdown ownership. They instantiate only the
bounded catalog reader from a fresh policy snapshot. No read can enter the heavy
lane or create a writer, Hub client, credential resolver or background refresh.
Whole selected evidence is validated before paging; a small page does not expand
the scan budget. [Catalog semantics](discovery.md#queries-coverage-and-pages)
define coverage and visible cursor identity independently of old policy hashes.

Writer-only catalog refresh uses the same heavy lane and original archive lock.
It refreshes only adjunct records with fresh installed curation after waiting;
there is no verifier dispatch, credential resolution, recovery or implicit startup
refresh. Its canonical operation route is `/api/v1/catalog/refreshes`; existing
receipts and exact results remain independently versioned. Lost acknowledgements
and reconnects use the original key, and restart preserves interrupted work without
replaying it. A new capture after label changes needs a new key.

### Dedicated worker bootstrap and limitations

`python -m hfcache.verification_worker` is a private local service entrypoint,
not a public command-dispatch interface. It takes trusted local `--config`,
`--state-directory` and `--socket`; optional `--api-user` and `--api-uid` are
mutually exclusive, defaulting to effective UID. System-manager `%U` is not the
service peer identity. API/worker stores must not nest or overlap the archive.

Native bootstrap requires exactly named FD3 and matching `LISTEN_PID`,
`LISTEN_FDS`, `LISTEN_FDNAMES` and optional PIDFD identity, with no extra inherited
descriptors. It validates the existing protected listening Unix stream socket;
it never binds/rebinds, unlinks or shuts down an activated socket.

Rootless owned-listener bootstrap is direct Python PID1. It refuses all
`LISTEN_*` activation state and descriptors above stderr, reserving FD3 before
NSS/shared imports. Prove local paths/mount information (bounded to 1 MiB) before
traversal; require the exact UID/GID parent at 0700, create a 0600 socket with
backlog 8, retain parent/instance/socket identities and clean only the unchanged
owned inode after joined shutdown. Unknown stale sockets remain preserved.
Notify has a 1-second timeout; READY follows listener/instance/store/worker
initialization and never follows stop. API ordering follows that real readiness.

Both bootstraps reject known Hub/API/MCP credential environment sources before
shared imports, set `HF_HUB_OFFLINE=1` once, and resolve no verification credential.
These checks cannot discover arbitrary secret strings or alone deny IP sockets.
Actual units/containers must enforce no-IP, source masking, seccomp/capabilities
and SELinux; standalone or host-origin tests cannot certify an installed container.

The worker holds retained sibling `<state-name>.instance.lock` before its store.
Old unresolved private receipts are interrupted only after proving this is a new
instance, never requeued. Matching trusted operation/scope/fingerprint submit
returns the existing binding; changed identity conflicts. One verification thread
owns its full lock/hash/report/catalog boundary. The strict private protocol has
no estimate, arbitrary command, configuration, candidate or credential fields.
Control timeout is 5 seconds; accept polling 0.2 seconds. SIGTERM/SIGINT stop
control admission and join active verification. Setup refusal exits 20, argument
usage 2; domain outcomes remain in exact Envelopes, independently of process exit.

## Foreground listener bootstrap

`hfcache serve --server-config /etc/hfcache/server.toml` requires the server extra.
Listener, TLS, auth registry and configuration checks precede admission. Foreground
Unix startup refuses existing names, binds through a pinned no-follow parent and
cleans only its unchanged owned inode. Activated listeners are validated, never
rebound/unlinked/shut down by the application. Named Unix/optional TCP activation
shares one application/lifespan. Activation requires matching `LISTEN_PID`,
`LISTEN_FDS` and `LISTEN_FDNAMES`, with every name exactly `hfcache-api` and
exactly the enabled listener set. Classification uses socket family/address,
not descriptor order; IPv6 listeners must be IPv6-only. An optional
`LISTEN_PIDFDID` must match. Activation variables are cleared after capture, and
malformed activation never falls back to fresh binding. No initialization or Hub
request occurs on startup.

For an owned foreground Unix socket, default SIGTERM on the main thread of a
non-PID1 process is deferred through the complete listener cleanup scope. This
scope arms only after exact socket device/inode and mode bookkeeping. Uvicorn
still performs its normal graceful shutdown; when it restores and replays the
signal, a private unwind keeps the original socket close, exact-inode unlink and
pinned-parent close ahead of restoring the original handler and delivering the
original SIGTERM. Further TERM during this cleanup does not interrupt it. The
process retains signal termination rather than reporting success or a startup
error. Custom/ignored handlers, non-main threads, PID1, TCP-only listeners and
manager-owned activation keep their existing behavior. Pre-existing or replaced
nodes remain untouched. This is no cleanup guarantee for SIGKILL or other forced
process death; an unexplained remaining node still refuses a later startup.
[Decision 149](adr/decision-149.md) records this narrow ownership rule.

Raw Uvicorn access/error logging and ASGI tracing are disabled;
`proxy_headers=False` prevents implicit forwarded-header trust. TLS setup never
accepts plaintext first. `shutdown_timeout_seconds` bounds HTTP shutdown before
joined worker cleanup.

`--hub-token-file` is an explicit server-local development/startup source, separate
from rejected global client `--token-file`. Requests never choose it. Native named
Hub delivery and selected rootless file-mounted Podman delivery remain distinct;
verification receives neither. Normal daemon execution emits no terminal success
Envelope; classified startup failure can emit schema-1 failure under `--json`.

## Scheduled observation and lifecycle controls

Native sync/verify oneshots use the API-only scheduled observer for fixed sync or
full verification. It fsyncs a key before the sole POST and retains a strict private
handle across repeated finite windows. Existing handles, including uncertain
pre-POST crashes, permit lookup/observation only. Matching exact terminal evidence
alone permits owned handle unlink/fsync. Rotation within the same class preserves
lookup; malformed/future/mismatched history stays preserved at exit 20.
The selected guarded rootless profile does not enable legacy schedules.

Stopping a client never proves writer/verifier termination. Drain actual API work
while private worker status/result handoff remains available, then drain private
activation/service. Keep shared runtime lock inodes, both stores, scheduled handles
and previous artifacts through upgrade/rollback. Unknown activity refuses selection;
no killing, lock replacement, state clearing or target stop establishes quiescence.
See [client observation](api-client.md#scheduled-service-observation) and
[deployment](deployment-centos-stream-10.md) for profile-specific operator steps.

## Optional MCP transport

Base and REST-only profiles keep `mcp_enabled=false`: no optional import, credential
read or endpoint mount. Enabling requires the locked MCP extra, a separate usable
MCP-reader source and restart. Compose its lifespan with the same application;
it has fourteen narrow read tools, finite authenticated requests and no writes,
commands, resources/prompts or OAuth issuance. The selected rootless template
already enables MCP with its own file secret; native provisioning remains explicit.
[MCP](mcp.md) owns connect/tool/rotation/budget details. Source/fixture acceptance
does not certify installed NAS, egress, SELinux or other-host operation.

## Web UI design and current availability

Unreleased source implements the optional Basic provider and authenticated
application asset/bootstrap serving below. It remains disabled unless explicitly
configured with a matching protected artifact. Administration composes existing
status/readiness/version reads, protected host observations, configuration,
explicit diagnostics and fixed schedule/observer/journal controls. Opening or
refreshing a read panel submits no operation. Basic grants, protected host
permissions and each action's fresh execution proof remain independent; a Basic
grant alone authorizes no host effect. These source capabilities do not change
an installed release or permit adding unsupported
settings to its server. The shipped Cockpit plugin remains supported.
[UI status](web-ui/README.md) and
decisions [140](adr/decision-140.md), [141](adr/decision-141.md),
[142](adr/decision-142.md), [143](adr/decision-143.md) describe the replacement
boundary; [144](adr/decision-144.md) keeps retirement conditional on actual proof.

### Authenticated application assets

Keep the existing Caddy TLS instance and API Unix upstream. The application owns
authenticated `/ui/` navigation, indexed assets and independently versioned
`/ui/bootstrap.json`; Caddy does not gain a file server, archive mount, hash record
or global Basic gate. Do not add a second proxy/frontend server/public listener
or deployed Node runtime. Preserve existing TLS secret delivery, discarded default
logging, `admin off`, `auto_https off`, `persist_config off` and streaming.

The restart-only `web` object is `{enabled, asset_root, manifest_sha256}`. It
defaults disabled; disabled deployments open neither assets nor mount metadata.
Enabled UI requires a Basic provider, explicit protected immutable asset root
and exact canonical manifest SHA256. Missing, unsafe or incompatible assets
refuse startup instead of disabling the UI. UI-enabled origin and public prefix
are bounded to4096ASCII and1024UTF-8 bytes respectively; these ceilings do not
restrict backend-only deployments. See the exact
[capture/bootstrap contract](adr/decision-147.md).

The root is physically and lexically disjoint from actual archive, policy,
credentials/delivery directories, TLS material, writable state, instance lock
and sockets. Protected owner/mode and no-follow descriptor checks apply to every
ancestor and member. A finite rich mount snapshot detects bind aliases without
opening/statting archive contents; unsupported proof refuses enabled UI. Asset
mounts initially allow ext4, xfs, btrfs, tmpfs and overlay, never network or unknown
filesystems. Credential delivery pseudo filesystems retain their existing rules.

At startup capture at most4096 indexed regular single-link files,64MiB aggregate,
8MiB per member and2MiB canonical manifest. Reject unindexed files, symlinks,
special files, source maps and SVG. Permit HTML, CSS, JavaScript, JSON, PNG, WebP
and WOFF2, plus `text/plain` only for fixed `THIRD_PARTY_NOTICES.txt`. Keep one
root descriptor and immutable captured bytes, not4096 leaf descriptors or
request-time filesystem reads. Two separately bounded rendered shell variants
add at most16MiB; byte budgets do not promise process RSS. Capture precedes
operation-store construction/reconciliation and runner admission; partial failure
and cancellation close owned descriptors and drain exact active work.

The public prefix comes only from validated deployment configuration. Recognized
GET/HEAD UI routes alone receive shell fallback. Missing assets, wrong methods,
API typos and MCP errors never become index HTML. Authenticate before revealing
route state, including disabled UI. Build relative assets and a safely escaped
deployment-derived base; never interpolate request headers into executable code.
Bootstrap schema 1 contains only nonsecret paths, release/UI/server contract
identity and effective subject/permission context, separately from the stable
strict API capabilities object. Its archive UUID comes from installed policy,
not a sentinel read, health assessment, Hub or host probe. Derive expected wire
identity from the actual installed Python authorities, not the manifest's claim.
The browser validates inert DOM slots, bounded bootstrap, platform-crypto build
coherence and compiled source/contract before mounting. Failed entry/bootstrap
leaves a script-free reload explanation; no fake successful connection appears.

Every UI path is Basic-only, including assets, errors and direct Unix access.
Allowed navigation is `/ui/`, `/ui/library`, `/ui/operations`, `/ui/maintenance`
and `/ui/administration`, plus the explicitly recognized repository path
`/ui/repositories/{model|dataset}/{namespace}/{name}`. Repository components use
the existing identity grammar, without extra segments, traversal or encoded
separators. A bounded browser fragment selects an optional paired full lowercase
`commit_sha`/`publication_id` and a fixed tab; it never chooses an endpoint or
authority. Repository shell query strings remain refused. Unknown paths receive
the existing authenticated typed404, without arbitrary SPA fallback.
The authenticated `/ui` alias redirects307 to the trusted encoded `/ui/`.
Query/body misuse, missing JS/CSS, API typos, MCP errors and other methods never
receive shell fallback. HEAD retains GET status/headers/length and sends no body,
including authentication/error/saturation responses.

All UI responses have exactly one nosniff, no-referrer, restrictive same-origin
CSP and `Permissions-Policy: camera=(), microphone=(), geolocation=()`. No inline/
eval/data/blob/CDN allowance or service worker is added. HTML/bootstrap/errors/
aliases/notices/licenses are `no-store`. Only validated hashed members under
`assets/` use `private, max-age=3600, immutable`; API responses keep existing
no-store behavior. Bound successful body streams to16 active, no waiting queue,
64KiB chunks and30s including response.start; small refusal sends are bounded too.
HEAD needs no body-stream lease. Disconnect/error/cancellation releases each exact
lease once. Release switching offers explicit reload while preserving drafts,
uncertainty and original operation handles; it never reloads or replays silently.

### Basic provider and request admission

The [implemented optional provider](#basic-administrator) and decision146 retain
bearer/MCP compatibility, finite verification work, exact subject/key ownership
and post-authentication CSRF checks. This source boundary does not establish
installed availability, authorize credential/service changes or make the future
UI/static/helper settings available. Native browser challenge/deep-link/reuse and
all three browser engines require actual acceptance; no per-request Authorization
injection or TLS bypass substitutes for it.

### Narrow administration helper

`[host_helper]` is disabled by default and performs no endpoint/filesystem work
when disabled. To opt in, set `enabled=true`, `profile="native"` or `"rootless"`
and the measured positive `api_host_gid`. Optional `deployment_sha256` is an
additional exact lowercase SHA256 pin. Enabled support requires the fixed
`archive_config="/etc/hfcache/config.toml"`; inactive helper parameters and unknown
fields refuse configuration. Native startup derives an omitted deployment pin
only from the root-protected current-boot binding. Rootless startup derives it
only from the fixed host launcher's independently verified parent attestation,
never the socket's own claims. Indexed templates cannot contain their own hash.

The application owns a separate bounded helper client, outside metadata and
authentication executors. It admits eight active exchanges and no queued jobs,
uses one absolute22-second deadline, closes its exact socket on cancellation,
and retains capacity until the actual worker exits. Lifespan shutdown drains
the owned client; uncertain drain is a classified failure, never successful
closure. Login, bootstrap, static assets, ordinary metadata and original operation
observation do not inspect the host helper.

The unprivileged API connects only to an independently protected, peer-verified
Unix protocol with fixed host/configuration operations. Caddy/verifier cannot
connect, and the API receives no broad writable `/etc`, manager or container-engine
socket. Bind actual native/rootless peer process/namespace identity rather than
trusting a username/UID field. The helper has no Hub credentials or payload access.
Each action rechecks selected physical release/profile/config, explicit protected
permissions, guard/mask and expected object revision/invocation at execution.
Unavailable/unsafe proof yields a classified denial, never fallback.

Keep the original persistent configuration lock, candidate and predecessor backup.
Read-only managed reconstruction creates no missing files and uses a pinned
capture with bracketed exact byte/metadata revalidation; no lock is held during
validation/Hub preview. Persistent staging and backup/install/confirmation retain
the original configuration lock and require fresh exact base comparison.
Never nest operation-store/admission locks around helper calls; the helper cannot
acquire those locks or the archive flock. Private outcome evidence and original
key/ID support read-only reconciliation after interruption, never mutation replay.
Rootless schedule/observer permissions remain denied until their actual bindings
are proved; same-named user units are not substitutes. Native positive controls
must be accepted on an isolated supported profile. See the [API design](api.md#web-ui-and-administration-design)
and [private record design](schemas.md#18-web-ui-and-administration-design-records).

### Managed configuration read and preview

The API uses the same protected helper client for fixed `config-read` and
non-installing `config-prepare`. GET `/api/v1/config` requires the internal
configuration-read grant; managed validation/plans require configuration-write.
Both also require fresh independent configuration permission. Service writer
bearers receive no such grant. The private helper response may carry one bounded
candidate to the API for independent validation; it is never returned to the
browser or stored in generic operations. Private encoded frames remain bounded
at2MiB even when raw TOML fits1MiB.

Nonempty server-derived preview scope additionally requires explicit Hub
permission and complete existing-service sizing. Empty-scope assessments contact
no Hub and retain the explicit successful operation needed by later application.
The API does not hold admission/store locks across helper calls or Hub work.
Queue execution rechecks full-byte base, opaque candidate identity and all six
protected authority fields. Comments and tags invalidate base identity even when
operational fingerprints remain unchanged. See [API contracts](api.md#managed-configuration-read-and-assessment-responses).


### Guarded configuration application

The API durably admits a keyed configuration application before sending the
fixed helper request. It stores a canonical request digest, safe original receipt
and transmission-intent event, never private TOML, keys or helper diagnostics.
Duplicate keys resolve the original receipt before preparing another candidate.
Queued execution rechecks current capability, independent policy, exact base and
candidate, protected authority and successful complete original preview. No Hub
preview is repeated by apply. Helper calls occur outside admission/store locks.

The helper owns only labelled fixed configuration paths under `/etc/hfcache`.
It uses the original flock inode and same-filesystem private operation directory,
stages0640 root:hfcache, preserves original predecessor/backup inodes and confirms
installed bytes/fingerprint before acknowledging. A durable pending marker
precedes effects; legacy writers check it under the same flock. Cockpit previews
release that flock over network work, capture bounded output and reacquire/recheck
original base/candidate before returning the result.

On startup unfinished application receipts become interrupted without helper
transmission. Once ready, the original configuration outcome route permits a
configuration-read administrator with the original subject-scoped key to inspect
authenticated host evidence independently of that monotonic generic receipt.
Lost replies never cause replay, rollback or automatic cleanup. Missing/ambiguous
history or pending state blocks another apply. Private retention has fixed
64-operation/16MiB refusal limits; original receipts are conservatively retained.
See [application wire contract](api.md#guarded-configuration-application-and-original-outcomes)
and [interruption handling](web-ui/configuration-and-tags.md#observe-an-interrupted-application).

### Fixed host-action lifecycle

The independent host lane admits only the two keyed host-effect routes defined
in the [host API](api.md#fixed-host-actions-and-original-outcomes). Restart marks
unfinished host receipts interrupted without replay, while domain reconciliation
continues to own only its own routes. No store/admission lock is held during a
helper exchange. Original subject/key lookup and authenticated outcome reads are
available independently of a new effect grant.

Known pre-effect refusals, including stale expected schedule revision, return a
normal failed receipt and bounded typed evidence; exit10 alone never proves host
certainty. An unclassified post-handoff failure preserves interruption and holds
the host lane, rather than manufacturing a failed Envelope or replaying the
request. That hold does not cancel or take ownership of accepted domain work.
Stored-file, manager-acknowledgement and original-process evidence remain separate
in the host outcome. Private pending/history and original API handles are retained
for read-only reconciliation. See [decision156](adr/decision-156.md) and the
[fixed host contract](host-administration.md#fixed-schedule-observer-and-journal-operations).

New native grants/effects also require a safely absent fixed legacy Cockpit policy
or its strict protected schedule/observer bits both false. Capture and revalidate
that file or absence; its old source/index identity is not replaced by the new
release. This read-only exclusion does not establish that an earlier privileged
call has drained. Quiescent activation is a separate operator prerequisite, with
all original records preserved. Existing version1 read/configuration profiles do
not acquire this new effect gate or any new permission.
