# Writer server contract

Status: API-006 implements authenticated metadata HTTP resources and their
controlled application lifespan over API-005 configuration/auth primitives.
Jobs, isolated execution, CLI migration and service packaging remain later tasks.
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
and invalid constraints; no new durable JSON schema is added.

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
| `credentials` | required table | Required writer source and optional reader/MCP sources below |
| `listener` | table, defaults below | Unix/TCP/TLS and browser/proxy policy |
| `limits` | table, defaults below | Bounded resource policy for later routes/runner |
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

API-006 enforces read-page/body/response/work and metadata-pool limits; shutdown
joins its workers.
Job admission and receipt retention remain API-007/008 work and cannot age out
ambiguous/nonterminal work to satisfy a terminal-history count. Receipt policy remains subject to
the admitted-operation contract in [API lifecycle](api.md#admission-idempotency-and-lifecycle).

API-006 applies finite metadata entry/artifact/total-byte budgets through shared
`QueryBounds`. A page size limits its returned items, not the cost of the bounded
underlying scan; budget exhaustion returns visible `HFAPI005`/503. It never
becomes an empty page or raises verification confidence. The local CLI's default
queries retain complete results without HTTP ceilings. No metadata scan hashes
artifact content or creates/repairs an archive.

### Archive-policy reload

`InstalledPolicy.open(server_config)` pins the installed archive root and UUID
at startup. Every `snapshot()` reloads and validates the archive TOML, returning
a frozen `PolicySnapshot(config, fingerprint)` using the existing archive
fingerprint. Earlier snapshots remain unchanged. Invalid updates fail new
archive work; changed root/UUID fails closed with `HFCFG005` until restart.
API credentials never enter the archive snapshot or fingerprint; no new server
fingerprint format exists. API-006 takes a snapshot for each archive query;
API-008 must additionally reload/compare policy under the archive lock before a
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
errors, and sanitizes validation/exception output. Operation receipts do not exist
yet; API-007 must store only the nonsecret principal and correlation metadata,
never a token, digest or credential source path.

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
path for hermetic tests. Import/factory construction starts no listener and
performs no archive initialization, repair or Hub call. The lifespan owns real
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

## Execution and deployment target (not yet implemented)

The later execution target adds one admission registry and one heavyweight worker
to the same unprivileged application and bounded metadata pool. Both listeners
share that application; the daemon-instance lock prevents competing registries. Actual
archive work retains the existing local flock; metadata reads do not create
archive layout or rebuild catalogs. Systemd remains scheduling authority.

API-004 establishes shared correlation primitives ahead of this server:
configure logging once at startup, generate authoritative request and admission
IDs, activate an immutable execution context per request/operation, and copy it
deliberately into worker submissions. Never change logger levels/handlers or
offline environment flags per request. Domain run and journal identities retain
their existing meanings. A report's `invocation_mode=systemd` describes the daemon
host, not the timer/client that submitted work; API-007 receipts must carry the
authenticated submitter separately. See [decision 111](adr/decision-111.md) and
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
