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
Install/update ownership remains operator-controlled `root:hfcache`; the server
has no configuration-install API. Listener/auth settings are immutable until
restart. Configured TLS paths are declarations; the listener loads and validates
the certificate/key before accepting connections.

| Top-level key | Type/default | Constraint or meaning |
| --- | --- | --- |
| `schema_version` | required integer | Exactly `1` |
| `archive_config` | path, `/etc/hfcache/config.toml` | Installed archive policy, not caller-selected candidate authority |
| `state_directory` | path, `/var/lib/hfcache/api` | Local service-private control state; outside publication trees |
| `credentials` | required table | Required writer source and optional reader/MCP sources below |
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
| `timeout_seconds` | `5.0` | Finite number, greater than 0 and at most 60; each bounded control exchange |
| `poll_seconds` | `0.2` | Finite number, greater than 0 and at most 60; exact operation observation interval |
| `max_frame_bytes` | `16777216` | Integer `1024`–`16777216` |

These are restart-only server-side client settings, not caller-selected request
values or worker-launch permissions. Omit `expected_peer_uid` to use the service
UID; TOML has no null literal. The worker's separate store uses fixed default
`OperationLimits`, independently of API receipt-limit overrides.
Its state directory must be provisioned separately, never nested with API state.

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
| MCP reader | MCP only when enabled | `mcp-read`; rejected by the REST verifier |

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
responses. The adapter itself creates no application. The outer HTTP boundary
uses the same core verifier before framework routing/validation on every HTTP
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
exactly nine metadata tools through a narrow
read protocol; no resources/prompts or command paths. See [MCP](mcp.md).

## Metadata lifespan and request boundary

Authenticate before routing, body reception/validation and ordinary errors on
every HTTP surface, including health, schema/docs, unknown routes and methods.
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
credential-class namespace. The [API contract](api.md#admission-idempotency-and-lifecycle)
defines wire/status/event semantics; [control-state schemas](schemas.md)
defines the independent local family and retention compatibility. The execution
lane and strict route matrix preserve these boundaries.

## Bounded execution and private verification

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
The app drains the heavyweight runner before closing metadata workers, control
store descriptors and the daemon-instance lock. A blocked/heavy item does not
occupy the metadata pool; lightweight HTTP reads remain responsive while it runs.
Lifespan cleanup shields the entire runner/metadata drain against repeated task
cancellation before releasing store/instance ownership. This is joined graceful
shutdown, not a claim that SIGKILL can finish work.

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
it has nine narrow read tools, finite authenticated requests and no writes,
commands, resources/prompts or OAuth issuance. The selected rootless template
already enables MCP with its own file secret; native provisioning remains explicit.
[MCP](mcp.md) owns connect/tool/rotation/budget details. Source/fixture acceptance
does not certify installed NAS, egress, SELinux or other-host operation.
