# Writer server contract

Status: API-006 implements authenticated metadata HTTP resources and their
controlled application lifespan over API-005 configuration/auth primitives.
API-007 adds bounded receipt/admission primitives and operation observation;
API-008 adds the heavyweight lane and private verifier process/protocol; API-009
adds typed sync, verification, planning, diagnostics and installed validation.
Maintenance, candidate operations, CLI migration and installed service hardening
remain later tasks.
See [the API contract](api.md) and [active plan](plans/2026-10-17-plan-rest-api-and-mcp.md).
No service is installed or listening as a result of this document.

## Implemented configuration boundary (API-005)

[Decision 112](adr/decision-112.md) introduces
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
format; API-007's independent local receipt schema is described separately below.

The server configuration default is `/etc/hfcache/server.toml`.
[`packaging/server.toml`](../packaging/server.toml) is an example for this separate
domain, not an addition to `examples/config.toml` and not an installed listener.
Install/update ownership remains operator-controlled `root:hfcache`; the server
has no configuration-install API. Listener/auth settings are immutable until
restart. Configured TLS paths are declarations; the listener loads and validates
the certificate/key before accepting connections.

| Top-level key | Type/default | Constraint or meaning |
| --- | --- | --- |
| `schema_version` | required integer | Exactly `1` |
| `archive_config` | path, `/etc/hfcache/config.toml` | Installed archive policy, not caller-selected candidate authority |
| `state_directory` | path, `/var/lib/hfcache/api` | Local service-private API-007 control state; outside publication trees |
| `credentials` | required table | Required writer source and optional reader/MCP sources below |
| `listener` | table, defaults below | Unix/TCP/TLS and browser/proxy policy |
| `limits` | table, defaults below | Bounded resource policy for metadata, command routes and runner |
| `verification` | table, defaults below | Private executor client policy; no worker process is launched |
| `maintenance_enabled` | bool, `false` | Later archive initialization requires this gate plus writer capability and domain confirmation |
| `interactive_docs` | bool, `false` | Enables authenticated `/api/v1/docs`; `/api/v1/openapi.json` is always authenticated |
| `mcp_enabled` | bool, `false` | Requires an `mcp_reader` source in the model; runtime startup refuses enablement before the REST/MCP gate |
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
API-006 applies Host/Origin/proxy-prefix policy at the HTTP boundary.
No wildcard CORS, token query parameters or URL userinfo is permitted by the
management contract. The later client always verifies off-host TLS.

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

API-006 enforces read-page/body/response/work and metadata-pool limits; shutdown
joins its workers.
API-007 uses `retained_terminal_operations` as a conservative ceiling across
all retained receipts, not permission to evict history. The operation-specific
limits bound its independently versioned local store, events and terminal
Envelopes. Retention never ages out interrupted/ambiguous/nonterminal work;
unexpired terminal keys cannot be evicted for the count cap. Admission reserves
the maximum receipt plus result allowance for each nonterminal/interrupted
operation, while succeeded/failed history consumes actual bytes. Refuse new
admission if that count/space reservation does not fit. API-008 implements the
execution/queue policy below; [API lifecycle](api.md#admission-idempotency-and-lifecycle)
defines the safety boundary.

API-006 applies finite metadata entry/artifact/total-byte budgets through shared
`QueryBounds`. A page size limits its returned items, not the cost of the bounded
underlying scan; budget exhaustion returns visible `HFAPI005`/503. It never
becomes an empty page or raises verification confidence. The local CLI's default
queries retain complete results without HTTP ceilings. No metadata scan hashes
artifact content or creates/repairs an archive.

### Private verifier client settings (API-008)

| `[verification]` key | Default | Constraint |
| --- | --- | --- |
| `unix_socket` | `/run/hfcache/verification.sock` | Absolute normalized protected Unix-socket path |
| `expected_peer_uid` | omitted | Nonnegative integer when set; omission uses the API process's effective UID |
| `timeout_seconds` | `5.0` | Finite number, greater than 0 and at most 60; each bounded control exchange |
| `poll_seconds` | `0.2` | Finite number, greater than 0 and at most 60; exact operation observation interval |
| `max_frame_bytes` | `16777216` | Integer `1024`–`16777216` |

These are restart-only server-side client settings, not caller-selected request
values or worker-launch permissions. Omit `expected_peer_uid` to use the service
UID; TOML has no null literal. The worker's separate store uses fixed default
`OperationLimits` from API-007, independently of API receipt-limit overrides.
Its state directory must be provisioned separately, never nested with API state.

### Archive-policy reload

`InstalledPolicy.open(server_config)` pins the installed archive root and UUID
at startup. Every `snapshot()` reloads and validates the archive TOML, returning
a frozen `PolicySnapshot(config, fingerprint)` using the existing archive
fingerprint. Earlier snapshots remain unchanged. Invalid updates fail new
archive work; changed root/UUID fails closed with `HFCFG005` until restart.
API credentials never enter the archive snapshot or fingerprint; no new server
fingerprint format exists. API-006 takes a snapshot for each archive query;
API-008 additionally reloads/compares policy under the archive lock before a
queued mutation. These primitives do not install policy or switch archive
authority. Version/capabilities do not need a fresh archive snapshot; health can
diagnose failed updated policy without silently switching archive authority.

## Implemented credential and capability boundary (API-005)

`[credentials.writer]` is mandatory. `[credentials.reader]` and
`[credentials.mcp_reader]` are optional. Each configured source contains exactly
one `file` absolute path or `systemd_name`; the latter resolves only through the
absolute `CREDENTIALS_DIRECTORY` supplied by systemd. Names use
`[A-Za-z0-9._-]{1,64}`, excluding `.` and `..`. An absent optional source disables
that class. Every configured source must load successfully, including optional
classes; missing, unsafe, racing or malformed sources fail startup with
`HFAPI003`, and duplicate class values fail with `HFAPI004`. No ambient Hub/API
token is discovered, no Hub credential is forwarded, and API tokens never appear
in process arguments or configuration.

[`read_protected_token`](../src/hfcache/api/auth.py) opens every path component
relative to pinned directory descriptors and refuses symlinks. The credential
must be a regular inode owned by root or the effective server user, with exactly
one hardlink and mode `0400`, `0440`, `0600` or `0640`. Reads stay on the checked
inode across pathname replacement; bounded reads and before/after descriptor
metadata refuse content/ownership/mode changes to that inode. Group access
must be provisioned deliberately for the service identity; world access and
executable/writable-by-group modes refuse loading.
For group-readable modes, the credential group must be the server's effective
or supplementary group.

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
| MCP reader | Future MCP only | `mcp-read`; rejected by the REST verifier |

The framework-independent verifier returns a frozen nonsecret `Principal` with
the configured class. It identifies a credential class, not an individual user
or token-derived identity. Every reader must be authorized for the whole archive,
including restricted repositories (AD-21). Cross-interface credentials and
missing/malformed/invalid bearers all receive `HFAPI001`, HTTP 401 with
`WWW-Authenticate: Bearer realm="hfcache"` and `Not authenticated`; a valid
principal missing a required capability receives `HFAPI002`, HTTP 403 `Forbidden`.

The optional [`api.security`](../src/hfcache/api/security.py) adapter supplies
`BearerAuthentication(registry)` and `RequireCapability(authentication, capability)`.
It validates the original single bounded Authorization field before FastAPI can
normalize input, delegates verification to the core and preserves those
responses. The adapter itself creates no application. API-006's outer boundary
uses the same core verifier before framework routing/validation on every HTTP
surface, including health, capabilities, docs, OpenAPI, unknown paths and method
errors, and sanitizes validation/exception output. API-007 receipts store only the
nonsecret principal and operation/domain correlation, never a token, credential
digest or source path. Their private idempotency-key digest is a separate
comparison value and is never exposed by HTTP.

Rotation means replace the protected credential, then restart the server to load
it. Existing clients must use the new value on subsequent requests; stale tokens
fail authentication after restart. No request mutates the registry or discovers
replacement credentials automatically. MCP source/model slots reserve its later
boundary; they do not enable MCP imports, tools or endpoints now.

## Package and client-transport primitives (API-005)

HTTPX is a direct base dependency; FastAPI/Uvicorn are available only through the
`server` extra. The Python 3.14 locked versions and official sources are recorded
in [decision 112](adr/decision-112.md). The default gate synchronizes that extra,
runs its tests without optional-import skips, builds the wheel and installs the
locked base and server variants into real isolated environments. Those smoke
checks import the CLI/auth core, exercise help/schema-1 local version, confirm
base has no FastAPI/Uvicorn, import the server adapter with the extra, and confirm
FastMCP is absent in both.

[`create_http_client`](../src/hfcache/http_transport.py) supplies a directly used
HTTPX construction boundary for API-011: verified default/custom-CA TLS, optional
Unix-socket transport, no ambient proxy/credential discovery, redirects disabled
and no transport retries. It bounds connections to 8 (4 keepalive) and timeouts
to 5 seconds for connect/pool and 30 seconds for read/write. Callers own closing
the client. The primitive sends no request and defines no API endpoint, bearer
forwarding or response policy; API-011 still owns the actual client.

## Implemented metadata lifespan (API-006)

[`create_app`](../src/hfcache/api/app.py) accepts a frozen server config and
optional credential registry, installed policy, query factory and instance-lock
path for hermetic tests, plus the trusted startup-only `hub_token_file` source.
Import/factory construction starts no listener and performs no archive
initialization, repair or Hub call. The lifespan owns real
startup effects: refuse early MCP enablement, acquire the local daemon lock,
configure logging once, load explicit API credentials, pin installed archive
policy, construct the bounded metadata pool and cache policy-independent version
information. Failure does not create the archive or reconstruct a catalog.

The default daemon lock is `/run/hfcache/api.lock`, separate from the archive
flock. Its parent must already exist and every component is opened no-follow.
The retained lock inode must be a regular single-link file, owned by the effective
server user and mode `0600`; a held/unsafe/unavailable lock refuses with
`HFAPI011`. It is never unlinked. The lock covers the application lifespan,
not archive mutation; operation-scoped archive flock ownership remains unchanged.

Blocking queries run in `metadata_workers` threads, with total capacity bounded
by workers plus `metadata_queue`. Each submission gets an independent copied
execution context. Capacity remains reserved for worker completion and request/
stream completion, including a disconnected observer whose worker is still
running. Full/draining admission returns `HFAPI009`/503. Version/capabilities
remain independent of archive scans. Shutdown closes pool admission and joins
its workers before releasing the instance lock; it never cancels an archive
operation or infers a durable result from a lost observer.

The API contract records exact [resources/wire models](api.md#implemented-metadata-resources-api-006),
page ordering and source/response bounds. Read-only inspection uses the bounded
no-follow metadata hook; unsafe/corrupt/missing sentinel state produces unusable
diagnostics without changing it. `health.ready` reports the daemon rather than
archive integrity, mount safety or initialization. No health path probes writes,
rebuilds a catalog or constructs a Hub credential. Ref/manifest checks do not
claim per-request sentinel proof; report identity and catalog confidence retain
their own documented validation rules.

## Command admission and Hub authority (API-009)

[`install_command_routes`](../src/hfcache/api/commands.py) binds explicit strict
[command DTOs](../src/hfcache/api/command_models.py) to the shared services and
bounded runner. The [API contract](api.md#implemented-command-resources-api-009)
records exact body/capability rules, 202 models, key lookup and terminal results.
Sync and every actual verification require writer capability; installed planning
and explicitly read-only diagnostics permit REST readers while retaining Hub,
resource and control-state effects. Probing diagnostics require a writer and the
service-owned lock. Installed validation is an immediate query, not a job.

The outer boundary authenticates before receiving a body, authorizes known writer
routes before reading it, and enforces mixed-route capabilities before typed
validation. It accepts one bounded strict JSON object with explicit media/encoding
rules and sanitized errors. Metadata/observation remain responsive while accepted
heavy work runs. A 202 proves durable admission only; the exact result Envelope
retains domain failure/partial-result classifications. A lost/oversized admission
response cannot prove nonexecution; the original key identifies its binding.

`serve --hub-token-file PATH` is a trusted development/startup option forwarded
to `create_app(..., hub_token_file=...)`, separate from API bearer credentials.
Only that explicit server-local file or the installed systemd Hub credential
source can supply Hub authority, under the existing token-mode/account rules.
Adapters resolve it when the shared command or installed validation requires it;
startup performs no Hub call. No HTTP body can select a token, source file,
endpoint, archive root or arbitrary command. Verification receives none of those
credentials and always delegates through the configured private executor.

The pure [candidate hooks](configuration.md#12-candidate-authority-preparation-api-009)
compare installed authority without resolving proposed credentials or contacting
the Hub. Current routes reject candidate fields; the complete candidate/client
pipeline belongs to API-012. No configuration-install endpoint is provided.

## Foreground listener bootstrap (API-006)

`hfcache serve --server-config /etc/hfcache/server.toml` explicitly starts the
configured server; it requires the `server` extra. This implementation was tested
on disposable local sockets, not started against the production archive.
One Uvicorn instance/worker, one ASGI lifespan, credential registry and metadata
pool serve both configured listeners. Direct TLS applies to TCP only; the Unix
socket stays ordinary local HTTP for deny-all-IP clients. TLS certificates and
keys must load successfully before accepting work. Auto-reload is not enabled,
and proxy headers are disabled in Uvicorn so the application owns explicit trust.
Bootstrap reserves addresses before Uvicorn validates TLS and starts the
lifespan/listeners. Reserved sockets accept no plaintext connections during that
interval. Invalid TLS closes them and removes only the owned unchanged Unix inode.

Runtime directories must already exist. The Unix socket binds through a pinned
no-follow parent descriptor, initially mode `0600`, then the configured
`0600`/`0660`. Startup never adopts or unlinks an existing path. Cleanup removes
only the exact socket inode this process created; a replaced name is preserved.
A socket left after a crash requires an operator to prove it unused before
cleanup. The daemon lock inode is always retained. No directory or archive
initialization is hidden in listener setup.

Uvicorn raw access/error/ASGI tracing is disabled to avoid logging request URLs
or headers; the application retains sanitized problems and structured event
correlation. The foreground wrapper preserves typed lifespan startup failures
instead of reducing unsafe credentials or invalid archive policy to a generic
unavailable error. `serve --json` writes a classified startup failure Envelope;
normal daemon execution writes no success Envelope/stdout. Uvicorn's graceful
HTTP shutdown timeout uses `shutdown_timeout_seconds`, followed by joined
metadata-worker shutdown. Tests use ephemeral TCP/Unix sockets and disposable
OpenSSL-generated certificates to prove TLS verification and CA rejection;
OpenSSL is a test tool, not a runtime dependency or production certificate change.
The small `ListenerServer.startup` override is tied to the locked Uvicorn
0.54 lifecycle and is covered by those real-socket tests; revisit it during a
Uvicorn upgrade. Proven local Unix requests remain available when TCP uses a
trusted TLS proxy; TCP peers must satisfy explicit numeric proxy/HTTPS checks.

## Implemented operation control state (API-007)

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

Startup opens the store and shutdown closes its pinned descriptors. API-007
alone did not run a worker, expire history or classify old receipts; API-008 now
adds the runner/reconciliation lifecycle described below.
`interrupt_unfinished()` and `expire()` are explicit core primitives, not HTTP
mutation endpoints. API-008 must reconcile exact surviving executors before
classifying unresolved work. Unsupported/malformed/unexplained state is preserved
and blocks scan/admission, while healthy exact-ID reads and policy-independent
diagnostics remain available. A retained `running` label never proves liveness.

Operation observation uses authenticated bounded HTTP metadata work, never the
archive flock or a domain command. All REST read-capable principals share this
whole-archive metadata/result boundary; idempotency lookup alone uses the caller's
credential-class namespace. The [API contract](api.md#admission-idempotency-and-lifecycle)
defines wire/status/event semantics; [schemas §13](schemas.md#13-service-private-operation-control-state-api-007)
defines the independent local family and retention compatibility. Heavy execution,
submission routes and isolated verification remain later tasks.

## Bounded execution and private verification (API-008)

One heavyweight FIFO lane is separate from the bounded metadata pool. Admission
must be durable before an item becomes runnable. Matching idempotent retries
return the original operation and never add another queue item. The pending
count is bounded by `max_queued_operations`; saturation and drain refuse new
admission rather than creating an unbounded executor queue.

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
acquires in its own process. `requires_lock=False` is only for a genuine
non-mutating heavy read, which validates its snapshot before execution. These
flags are not caller-selectable request fields. A successful locking task must
prove that its service-owned guard ran; an arbitrary unlocked callback cannot
claim success. Unexpected local execution/result-persistence failure halts the
lane and preserves interruption rather than inventing a replacement result.
Fresh verification admission probes the configured executor before writing a
new receipt; a missing/untrusted adapter refuses with `HFAPI016`. Matching
idempotent retries bypass this fresh-only probe and retain their original binding.
The probe never submits or starts verification.
API-009 permits a trusted `wait_seconds(snapshot)` selector as well as a numeric
budget, so fresh admission uses the installed sync/verification waiting policy
without loading changed policy on an idempotent retry. No request field supplies
that callable or changes the server's waiting policy.

The separate verifier uses the same complete target/hash/report/catalog lock
boundary. The HTTP process imports its protocol/client without executing archive
verification. A missing/untrusted executor is `HFAPI016`, HTTP 503 / exit 20;
there is no production in-process fallback, process spawning from a request or
generic systemctl/sudo command. Socket-activated systemd units and installed
no-IP/credential-free hardening remain API-014, not proof supplied by API-008.

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
The app drains the heavyweight runner before closing metadata workers, control
store descriptors and the daemon-instance lock. A blocked/heavy item does not
occupy the metadata pool; lightweight HTTP reads remain responsive while it runs.
Lifespan cleanup shields the entire runner/metadata drain against repeated task
cancellation before releasing store/instance ownership. This is joined graceful
shutdown, not a claim that SIGKILL can finish work.

### Dedicated worker bootstrap and limitations

`python -m hfcache.verification_worker` is a private service-manager entry point,
not a public remote CLI command. It requires trusted local `--config`,
`--state-directory`, `--socket` and `--api-uid` settings and exactly one inherited
systemd listening descriptor at FD 3 (`LISTEN_PID`/`LISTEN_FDS` must match).
It neither binds a new socket nor accepts a caller-selected configuration over
IPC. The inherited listener must already be a listening Unix stream socket at
the protected configured name. The state root cannot overlap the installed
archive root. Keep API and verifier state roots separate, never nested, because
each flat store preserves/refuses unexplained entries.

The bootstrap validates activation, known credential environment sources and
unexpected inherited descriptors before shared runtime imports can open their
own files. It sets `HF_HUB_OFFLINE=1` once before importing shared command/Hub
modules. It refuses known Hub/API/MCP credential sources, including
`CREDENTIALS_DIRECTORY`, and live inherited descriptors above FD 3 rather than
carrying API secrets into the worker. No credential is resolved by the
verification path. These checks do not discover every arbitrary secret string
or deny IP sockets: API-014 must provision the independent credential-free
environment, socket activation, permissions and `IPAddressDeny=any` sandbox.
Standalone development execution alone cannot make that installed-host claim.

The worker holds a retained sibling `<state-name>.instance.lock` before opening
its store. A newly started worker therefore cannot be its previous still-live
instance; old unresolved private receipts are explicitly interrupted, never
requeued. It admits a trusted exact API operation ID into the existing
OperationStore schema-1 family and records its exact terminal Envelope before
reporting completion. Status lookup never submits. Repeating a matching submit
returns the old binding; changing scope/fingerprint conflicts rather than
starting a second verification. Only one active verification thread runs.

SIGTERM/SIGINT stop accepting control connections and join active verification;
they do not abandon its lock/report/catalog boundary. Classified setup refusals
exit 20 without raw exception/credential output; local argument-usage errors
retain argparse exit 2. Domain exits remain in the exact operation Envelope,
independent of the long-lived worker's process lifecycle. The API client never launches this
process, inherits its environment or falls back to local verification. Disposable
socket/process tests establish these primitives; installed units, timeout/drain
policy and real egress enforcement remain the later packaging acceptance gate.

## Remaining deployment and client target

API-008's lane and API-007's registry already share the unprivileged application
and separate bounded metadata pool across both listeners. The daemon-instance
lock prevents competing registries; actual archive work retains the operation-
scoped flock. Later tasks add command routes and client/unit integration, not a
second execution authority. Metadata reads create no archive layout or catalog.
Systemd remains scheduling authority.

API-004 establishes shared correlation primitives ahead of this server:
configure logging once at startup, generate authoritative request and admission
IDs, activate an immutable execution context per request/operation, and copy it
deliberately into worker submissions. Never change logger levels/handlers or
offline environment flags per request. Domain run and journal identities retain
their existing meanings. A report's `invocation_mode=systemd` describes the daemon
host, not the timer/client that submitted work; API-007 receipts carry the
authenticated credential-class submitter separately. See [decision 111](adr/decision-111.md) and
[API correlation](api.md#execution-correlation-api-004).

Archive policy reloads per admission; server listener and credentials require
restart. Root/UUID changes require restart and cannot hot-switch authority.
Configuration is operator-owned; REST cannot write `/etc/hfcache`. New config
cannot redirect an existing credential to a candidate-selected Hub endpoint.

Verification is delegated only to a narrow socket-activated executor with
`HF_HUB_OFFLINE=1`, `IPAddressDeny=any`, no credentials, peer identity checks,
bounded framed requests, and operation-correlated durable outcomes. It owns
the archive lock through hashing, report write, and catalog merge. No production
fallback runs it in the network-enabled HTTP process. Hermetic tests inject
an executor; host hardening remains an operator acceptance prerequisite.
`offline.initialize_offline_process()` sets only the library flag at dedicated
process startup, before Hub imports/use; it does not enforce no-IP isolation.

Drain stops admission and joins work; disconnecting a scheduled CLI or Cockpit
client leaves accepted work running. Recovery evidence must identify the real
executor and operation, not a vanished CLI process. Preserve FS-18's narrow
supervised-cancellation rule. Never unlink a potentially held lock file.

Packaging will preserve sync/verify service names as authenticated Unix HTTP
clients. The actual verifier and its client both retain deny-all IP policy.
Deployment requires locked server extras, protected API credentials, socket
ownership, startup ordering, TLS/Host/Origin/proxy configuration, graceful drain,
rollback barriers, NFS and hardening acceptance, and the disabled verify timer.
No host policy changes or production listener starts are authorized here.
