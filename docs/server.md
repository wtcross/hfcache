# Writer server contract

Status: API-005 implements configuration and bearer-capability primitives.
Runtime HTTP endpoints, lifecycle, executor and service packaging remain
API-006/008/014. API-001 establishes the target boundary.
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
restart. Configured TLS paths are declarations; the later listener must load and
validate the certificate/key before binding.

| Top-level key | Type/default | Constraint or meaning |
| --- | --- | --- |
| `schema_version` | required integer | Exactly `1` |
| `archive_config` | path, `/etc/hfcache/config.toml` | Installed archive policy, not caller-selected candidate authority |
| `credentials` | required table | Required writer source and optional reader/MCP sources below |
| `listener` | table, defaults below | Unix/TCP/TLS and browser/proxy policy |
| `limits` | table, defaults below | Bounded resource policy for later routes/runner |
| `maintenance_enabled` | bool, `false` | Later archive initialization requires this gate plus writer capability and domain confirmation |
| `interactive_docs` | bool, `false` | Later docs/OpenAPI routes remain authenticated when enabled |
| `mcp_enabled` | bool, `false` | Requires an `mcp_reader` source; no mount/import is implemented before REST acceptance |
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
to the later server wiring; unused configured addresses retain strict validation.

Unix sockets authenticate exactly as TCP does. Non-loopback TCP requires direct
TLS. An off-host TLS proxy connects only to loopback TCP and requires
`proxy_tls=true` plus explicit trusted proxy addresses; forwarded headers are
never trusted from everyone. The config model validates those combinations;
actual Host/Origin, proxy-prefix and listener enforcement lands in API-006/008.
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

These are configuration constraints, not evidence that admission, pagination,
body limits, shutdown or receipt retention already run. API-006/007/008 must
enforce the corresponding limits and cannot age out ambiguous/nonterminal work
to satisfy a terminal-history count. Receipt retention policy remains subject to
the admitted-operation contract in [API lifecycle](api.md#admission-idempotency-and-lifecycle).

### Archive-policy reload

`InstalledPolicy.open(server_config)` pins the installed archive root and UUID
at startup. Every `snapshot()` reloads and validates the archive TOML, returning
a frozen `PolicySnapshot(config, fingerprint)` using the existing archive
fingerprint. Earlier snapshots remain unchanged. Invalid updates fail new
archive work; changed root/UUID fails closed with `HFCFG005` until restart.
API credentials never enter the archive snapshot or fingerprint; no new server
fingerprint format exists. API-006 will take a snapshot for each query/admission;
API-008 must additionally reload/compare policy under the archive lock before a
queued mutation. These primitives do not install policy or switch archive
authority, and route wiring is not implemented in API-005.

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
responses. It creates no application or runtime route. API-006 must attach the
boundary to every endpoint, including health, capabilities, docs and OpenAPI,
and sanitize HTTP validation/exception output. Operation receipts do not exist
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

## Runtime target (not yet implemented)

Run one unprivileged process, one admission registry, one heavyweight worker,
a bounded metadata pool, and both local Unix and optional TCP listeners sharing
that application. A daemon-instance lock prevents competing registries. Actual
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
