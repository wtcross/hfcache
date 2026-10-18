# API client contract

Status: API-011 implements independent client/configuration primitives under the
[active plan](plans/2026-10-17-plan-rest-api-and-mcp.md). Its task records validation;
public operational CLI migration remains API-012/013. Global endpoint/source options
are stored now without switching existing command execution to HTTP. No production
client/server rollout is asserted.

[Decision 118](adr/decision-118.md) defines one explicit API authority, finite safe
observation and retained-key uncertainty. Reader and writer clients use the same
synchronous library; readers need no archive TOML/mount, service UID, Hub credential
or optional server/MCP package. The client never silently falls back to local
archive access or starts a daemon.

## Endpoint and credential selection

Client TOML is a separate strict schema-1 domain, with no archive storage, Hub
credential or server-listener fields. Explicit CLI `--api-url` and `--api-socket`
are mutually exclusive and override the configured endpoint as a group: choosing
one clears the other. Without a CLI endpoint use the configured URL/socket, then
the local Unix-socket default `/run/hfcache/api.sock`.
`resolve_client_config(path=None, ...)` uses optional installed
`/etc/hfcache/client.toml`: a missing default permits defaults, while an explicit
missing file or an installed unusable/malformed file fails HFAPI017. It reads no
archive TOML. The current CLI only stores option values; resolving settings occurs
when a client is deliberately constructed, or in later migrated commands.

API credential precedence is explicit `--api-token-file`, then configured token
file, then explicitly named systemd API credential. Resolve only the selected
source; a selected missing/unsafe/malformed source is an error, never anonymous
fallback. No plaintext-token option, Hub token reuse, ambient discovery or browser
credential handling is provided. Exact values register for shared redaction before
use and never appear in diagnostics or fingerprints.

## Client configuration and setup

[`ClientConfig`](../src/hfcache/client_config.py) requires explicit integer
`schema_version=1`; unknown fields and coercion are refused. It is independent of `ApplicationConfig`. Optional
`api_url` and `api_socket` are mutually exclusive; optional `api_token_file`,
`ca_file` and canonical UUID `expected_archive_id` are separate reader settings.
`credential_name` defaults to `hfcache.api`, resolved only through the explicitly
named systemd credential directory when no token file wins. Names use
`[A-Za-z0-9._-]{1,128}`, excluding `.` and `..`. The settings file is a nonempty
regular UTF-8 TOML file of at most 1 MiB; final symlinks, unstable descriptor
metadata, unreadable files and malformed TOML fail safely without input echo.
Protected token loading separately checks every path component/inode as documented
by the [server credential contract](server.md#implemented-credential-and-capability-boundary-api-005).
A missing/unsafe selected credential retains HFAPI003 / exit 10.

| Setting | Default | Range / purpose |
| --- | --- | --- |
| `connect_timeout` | `5.0` seconds | Finite `(0, 300]`; connect/pool budget |
| `read_timeout` | `30.0` seconds | Finite `(0, 3600]`; read/write budget |
| `read_retries` | `2` | Integer `0`–`5`; read retries only, no automatic POST replay |
| `poll_interval` | `0.2` seconds | Finite `(0, 60]`; operation observation interval |
| `wait_timeout` | `300.0` seconds | Finite `(0, 86400]`; observation deadline, never cancellation |
| `max_response_bytes` | `16777216` | Integer `1024`–`67108864`; actual per-response bytes |
| `max_pages` | `10000` | Integer `1`–`10000`; page-walk continuation ceiling |

All client paths must be absolute and refuse dot/traversal, backslash and control
components. URLs allow only a safe optional root prefix with ASCII alphanumeric,
underscore or hyphen components. HTTPS is required except `localhost`/numeric
loopback HTTP; userinfo, query, fragment and backslash are refused. After its
selected token is resolved/registered, the client also refuses a configured URL
containing that bearer, including a superficially safe path prefix.

[`packaging/client.example.toml`](../packaging/client.example.toml) is a complete
reader example with endpoint/source-path placeholders, independently versioned
from archive/server TOML. Copy only after choosing the intended API authority and
separately provisioning its protected credential. Default named `hfcache.api` is
API-only and never a Hub credential.

A reader setup uses only client configuration and a separately provisioned
protected API reader credential. For example:

```toml
schema_version = 1
api_url = "https://archive.example.com/management"
api_token_file = "/etc/hfcache/api-reader.token"
# ca_file = "/etc/hfcache/archive-ca.pem"
# expected_archive_id = "01234567-89ab-4cde-8fab-0123456789ab"
```

A local reader can use `api_socket = "/run/hfcache/api.sock"` instead of `api_url`,
while still authenticating. A writer uses the same client with its distinct
protected writer API source; it gains no authority to bypass server/domain gates.
The base wheel supplies HTTPX/client support without the `server` extra. Never
put a literal bearer in TOML or URL. These setup examples do not start a listener,
change installed writer configuration or perform archive operations.

## Transport and compatibility

API URLs require HTTPS except explicit loopback HTTP; optional normalized root
prefixes identify the configured proxy mount. Off-host access requires verified
TLS using default trust or an explicit CA file.
Unix sockets still authenticate. Refuse URL userinfo, token/query fragments and
endpoint escape; disable redirects and ambient proxies/netrc/credentials. Response
links cannot redirect Authorization to another authority. Bounded streamed reads
validate actual bytes, strict JSON/version/Envelope shape and identity before use;
malformed/truncated/oversized responses never become partial success. Response
headers are bounded to 32 KiB; accept one JSON media type with optional UTF-8,
identity/no encoding, consistent bounded Content-Length and maximum JSON depth 32.
Encoded request bodies also obey `max_response_bytes` and depth/finite-value
validation before transmission; these client ceilings never override the server's
possibly smaller request limit.

Negotiate API/envelope compatibility and needed capabilities explicitly. Preserve
request IDs as request correlation, operation IDs as admission identity and domain
run IDs as report/result evidence. An old operation retains its admitted archive
UUID/fingerprint after policy changes. Paginated reconstruction retains the first
Envelope's invocation metadata and named-array ordering; stale cursors/changed
scope are visible refusals. Finite per-response bytes, page count, timeouts and
read/poll retry budgets prevent endless observation without silent truncation.

## Submission and observation

Generate or accept one nonsecret key before the first POST. A keyed 202 is durable
admission only; poll authenticated status/events and retrieve the exact terminal
Envelope. Keep its domain exit/error/partial-result classification even at HTTP 200.
No client request cancels accepted work. Once POST transmission begins, a lost,
truncated, malformed or identity-inconsistent acknowledgement (including an unsafe
202 or untrusted error body) is HFAPI020 with the original key/route: admission
may already exist. A validated remote problem retains its server code/exit and
original key/route on `RemoteApiError`, including a generated key. Even a valid
HFAPI008/500 may follow durable admission and is not proof of nonexecution.
Pre-send validation remains a config/protocol refusal. Missing/expired history or an
observation timeout preserves uncertainty and the original key/ID;
never generate a new key to replay uncertain mutation. Authenticated key lookup
observes without submitting and remains within the credential-class namespace.

The central client errors are HFAPI017 configuration and HFAPI018 protocol/
compatibility at exit 10; HFAPI019 connectivity and HFAPI020 uncertain submission
at exit 20. Auth/capability problems retain their existing API codes; exact terminal
domain Envelopes retain their own application exits. Diagnostics never echo raw
response bodies, bearer values or transport exception text.

## Typed synchronous interface

`ApiClient(config, *, transport=None, sleep=..., monotonic=...)` owns and closes
its HTTP client, including through a context manager. Construction makes no hidden
request; explicit `capabilities()` / `require_capabilities()` negotiate compatibility.
Trusted transport/clock injection supports hermetic tests, not a remote option.

The interface provides `read(path, params=...)`, `iter_pages(path, field, ...)`,
`submit(path, body, key=None, on_key=...)`, `lookup(key)`, `operation(id)`, `events(id, after, limit)`,
`result(id)` and `poll(id, ...)`, plus `version()`, `health()` and
`validate_installed()`. Submission returns its retained key alongside
the typed acceptance; an unusable post-transmission acknowledgement raises
HFAPI020 with original key/route instead of replaying. `on_key` exposes the generated/explicit key before the HTTP send so later CLI
adapters can preserve a lookup handle even if acknowledgement is lost. The
selected credential is loaded once per client object; construct a new client
after deliberately changing its source/value rather than discovering replacements
or borrowing another credential during a request.

Public paths are complete `/api/v1/...` paths. The client prepends its configured
URL root prefix and checks returned status/result/events links against the exact
derived same-operation paths; it never follows arbitrary server links or redirects.
`iter_pages(path, field, params=None)` yields typed `ClientRead` pages, pins archive
UUID/fingerprint/command and refuses cursor cycles, duplicate primary row identities
and max-page exhaustion. SHA-256 identity digests use a cumulative digest-byte
ceiling of `max_response_bytes`, without aggregating result rows. Per-page request/
domain observation IDs may legitimately differ; the future CLI adapter owns
reconstruction and keeps the first Envelope's invocation metadata. A valid failed
domain Envelope is yielded intact and terminates the walk, even when its failure
data lacks the requested array; its exit must not become a generic protocol error.
Exact nonpage responses reject a nonnull wrapper `next_cursor`.

Standalone `result(id)` and `events(id)` fetch exact operation metadata if it is
not already known. Result UUID/fingerprint/domain run ID and success/failure must
agree with that receipt; cached immutable identities cannot be replaced by current
policy. Event pages likewise retain admitted identity and require contiguous
sequences or the explicit `oldest_sequence`/`truncated` gap. Polling checks its
absolute deadline between retries and on each transport chunk; arriving bytes
never reset that deadline. Read retries cover transport failures
only; malformed responses or validated remote problems do not trigger replay.

For library use after separately provisioning the configured API source:

```python
from hfcache.client import ApiClient
from hfcache.client_config import resolve_client_config

with ApiClient(resolve_client_config()) as client:
    client.require_capabilities("reads")
    response = client.version()
    envelope = response.envelope
```

Construction loads settings/credentials but sends no request; the explicit
negotiation and version calls above contact only the configured management API.
The client has no artifact-byte transfer or local archive reader.

CLI read/candidate migration remains API-012 and commands/operation UX remains
API-013. The independent [consumer helper](consumers.md) still owns bulk
copy and complete local verification against exact publication identity.

## Troubleshooting and rollback

| Code/result | Meaning and next step |
| --- | --- |
| HFAPI017 / exit 10 | Invalid settings/selection or TLS client setup; check client TOML, endpoint group, absolute paths and explicit CA source |
| HFAPI003 / exit 10 | Selected protected API credential is missing/unsafe/malformed; fix that source rather than falling back anonymously |
| HFAPI001 / 401 or HFAPI002 / 403 | Server authentication/capability refusal; use the correct REST class and configured source, never a Hub/MCP token |
| HFAPI018 / exit 10 | Unsupported/malformed/version/identity-inconsistent read response or pre-send protocol refusal; inspect compatible API/schema/expected archive identity |
| HFAPI019 / exit 20 | Connectivity/read budget or finite observation deadline; preserve any known operation ID and continue observation deliberately |
| HFAPI020 / exit 20 | Unusable post-transmission acknowledgement; retain original key/route and perform authenticated lookup without a new-key replay |
| HFAPI013 or HFAPI015 / exit 20 | Missing/expired or unfinished/interrupted outcome; preserve uncertainty and follow the [recovery runbook](recovery.md#10-operation-history-and-uncertain-submissions) |
| Terminal domain Envelope | Preserve its command/run/error/partial-result exit classification; transport HTTP 200 is not domain success |

The independent client TOML requires schema 1; archive JSON/receipt versions do
not change. An actual isolated predecessor `66d85a3` wheel on Python 3.14.6 rejects
`--client-config` with usage exit 2, while the new local version command accepts
the stored option and exits 0 without resolving it. Both preserve the complete
client file byte-for-byte and perform no API/Hub/archive operation. Keep client
settings on rollback; lack of old option/client support is not permission to
remove credentials/history or infer that an operation never executed. The task
records the compatibility drill and definitive gate evidence.
