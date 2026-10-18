# REST client reference

Use the same synchronous client library for REST readers and writers. Reader
hosts need only the base wheel, endpoint and separate protected API credential;
they need no archive mount/TOML, service UID, Hub credential or server/MCP extra.
No API failure falls back to local archive execution or starts a daemon.

The optional [MCP example](mcp.md) uses its own SDK, MCP-reader bearer and `/mcp/`
endpoint. REST, MCP and Hub credentials are separate and never forwarded between
interfaces. [REST routes and effects](api.md#routes-and-effects) define current
capabilities; [CLI output](cli.md) defines terminal and admission rendering.

## Endpoint and credential selection

Client TOML is a separate strict schema-1 domain, with no archive storage, Hub
credential or server-listener fields. Explicit CLI `--api-url` and `--api-socket`
are mutually exclusive and override the configured endpoint as a group: choosing
one clears the other. Without a CLI endpoint use the configured URL/socket, then
the local Unix-socket default `/run/hfcache/api.sock`.
`resolve_client_config(path=None, ...)` uses optional installed
`/etc/hfcache/client.toml`: a missing default permits defaults, while an explicit
missing file or an installed unusable/malformed file fails HFAPI017. It reads no
archive TOML. Operational commands resolve these settings only when invoked;
local help/version and explicit local validation do not construct an API client.

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
by the [server credential contract](server.md#credentials-and-capabilities).
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

Unix connections use a narrow public HTTPX/HTTPCore adapter that closes owned
sockets on failed connects and response cleanup; no IP fallback is permitted.
TCP/TLS continues through HTTPX. HTTPCore is an explicit base dependency at the
already-locked 1.0.9 version; [decision 119](adr/decision-119.md#uds-descriptor-ownership-and-fw-04)
records the observed missing-socket leak and supported-interface rationale.
[`unix_http`](../src/hfcache/unix_http.py) owns descriptor creation/connect and
stream cleanup; [failure-path tests](../tests/unit/test_unix_http.py) retain
exception tracebacks while checking that failures release descriptors.

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
`submit(path, body, key=None, on_key=...)`, `lookup(key)`, `operation(id)`, `events(id, after=0, limit=None)`,
`result(id)` and `poll(id, ...)`, plus `version()`, `health()` and
`validate_installed()`, `validate_candidate(content)` and
`plan_candidate(content, selectors=(), key=None, on_key=None)`. Submission returns its retained key alongside
the typed acceptance; an unusable post-transmission acknowledgement raises
HFAPI020 with original key/route instead of replaying. `on_key` exposes the generated/explicit key before the HTTP send so callers
can preserve a lookup handle even if acknowledgement is lost. The CLI prints
that validated handle before sending, even in quiet mode. The
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
domain observation IDs may legitimately differ; the CLI adapter reconstructs
complete data and keeps the first Envelope's invocation metadata. A valid failed
domain Envelope is yielded intact and terminates the walk, even when its failure
data lacks the requested array; its exit must not become a generic protocol error.
Exact nonpage responses reject a nonnull wrapper `next_cursor`.

`operation_response(id)` / `lookup_response(key)` return validated
`ClientRead` with the exact server metadata Envelope; the existing operation/
lookup conveniences still return its typed receipt. `observe(id, timeout=...,
on_event=..., after=0)` observes exact result and optional sanitized bounded event
pages under one absolute deadline. Existing `poll` remains compatible without
mandatory event fetching. CLI helpers `submit_job`, `observe_operation` and
`admission_payload` separate typed terminal output from explicit detach and retain
already validated handles on classified errors.

Standalone `result(id)` and `events(id)` fetch exact operation metadata if it is
not already known. Result UUID/fingerprint/domain run ID and success/failure must
agree with that receipt; cached immutable identities cannot be replaced by current
policy. Event pages likewise retain admitted identity and require contiguous
sequences or the explicit `oldest_sequence`/`truncated` gap.
An omitted event limit is adaptive: no `limit` query parameter is sent, so the
existing route selects min(100, configured max_page_size, operation_max_events).
Explicit integer limits retain their existing validation/meaning. Progress
observation drains contiguous retained event pages through a final empty page
before treating that batch as exhausted; the empty response also counts against
that drain's max_pages. All observation reads, including empty drain/status/
result requests, share the existing absolute deadline and finite retry/body budgets. No extra
capability request is needed, and a terminal result never justifies silently
skipping retained progress. Existing poll without events remains compatible.
Polling checks its absolute deadline between retries and on each transport chunk; arriving bytes
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

The CLI uses these primitives for operational CLI modes and explicit resumable
observation. The independent [consumer helper](consumers.md) still owns bulk
copy and complete local verification against exact publication identity.

## CLI dispatch

The modes below report writer truth through the API. Reader setup needs
only this client configuration/credential, not `/etc/hfcache/config.toml`, archive
mount, service UID or Hub credential. Connection failure is a transport error;
there is no local archive fallback or automatic daemon start.

| CLI mode | Current boundary |
| --- | --- |
| help; `version` | Local, configuration/server independent |
| `version --server` | Authenticated server version, exact server Envelope |
| `status [selectors]` | API pages reconstructed completely |
| `list [selectors] [--type] [--revisions]` | API inventory plus exact revision rows when requested; consistent join or visible refusal |
| `archive init --inspect` | Configured writer inspection, no required client root; optional root only checks returned authority |
| `verify --estimate` | API metadata; no client hashing/probes |
| `config validate` | Installed writer policy/source validation through API |
| `--config PATH config validate` | Writer-only bounded local candidate content; syntax/policy validity separate from compatibility |
| `config validate --local` | Explicit local/bootstrap validation, never automatic fallback |
| `plan [selectors]`; `--config PATH plan [selectors]` | Keyed installed reader / candidate writer job, then exact terminal Envelope |
| `doctor --read-only` | Keyed reader diagnostic job; installed Hub checks, no write probes |
| `serve` | Writer-local foreground bootstrap |
| sync, actual verification, probing doctor, maintenance/confirmed init | Typed keyed API jobs with exact terminal results by default; explicit writer capability/guards for effects |
| `operations show`, `operations lookup` | Exact authenticated server metadata Envelopes; no submission |
| `operations wait` | Bounded sequenced progress then exact terminal command Envelope, or retained-handle observer refusal |
| Explicit `--detach` | Identified admission object after validated 202, separate from terminal Envelope |

Remote JSON rendering preserves the complete server Envelope command/run ID,
started/finished timestamps, status/warnings/errors, exit and payload; client
request/observer IDs never replace domain evidence. Joined/paged data retains the
first appropriate server Envelope's invocation metadata. Human output keeps the
same supported shapes and warning behavior. A 202 receipt is never rendered as
a completed result; plan/read-only diagnostics await their terminal Envelope.

The CLI's aggregate result is finite too: accumulated rows must fit the
configured response budget or fail visibly. It never silently truncates inventory.
`list --revisions` combines base inventory and revision pages, preserving base
empty/unmanaged rows and checking archive/fingerprint, row membership/counts,
current revision/publication identity and uniqueness. Changed/inconsistent evidence
is a refusal rather than mixed publication metadata. Pages are still not an
archive-wide snapshot.

An explicit global `--config` is candidate content only for validate/plan, even
when equal to the legacy default path. Other API modes reject it, and
all API modes reject Hub `--token-file`; use `--client-config` / API credentials.
Local validation explicitly selects `--local`. Candidate file content is bounded
independently of the server JSON cap; escaping/wrapper overhead can produce 413.
A valid incompatible candidate remains valid but cannot plan through changed
root/UUID/endpoint/credential authority. If installed policy is broken, syntax
validation can still succeed with unknown compatibility. Neither result installs
policy or grants mutation authority.

Representative reader invocations, after separately provisioning the API:

```text
hfcache --client-config /etc/hfcache/client.toml --json status
hfcache --client-config /etc/hfcache/client.toml list --revisions --type model
hfcache --client-config /etc/hfcache/client.toml version --server
hfcache --client-config /etc/hfcache/client.toml archive init --inspect
```

Candidate validate/plan requires the writer API source; `--config` names a file on
the CLI host, never a server file to open. Installation/backups remain privileged host work. Browser code never receives
the API bearer. See [candidate authority](configuration.md) and the client
integration/profile guidance below.

## Submit, detach and resume

All operational modes use the API without a direct local mutation backend.
Archive root/UUID, Hub credentials, preflight, common flock, scope/recovery proof
and private verification stay server-owned. Explicit local validation, help/local
version and foreground serve remain named bootstrap boundaries; unavailable API
never activates local execution. Pure request objects do not import executors.

Job commands wait by default and render the exact terminal server Envelope once,
including nonzero domain exits and partial results. This also applies to semantic
read jobs such as planning, read-only diagnostics and maintenance previews.
Global `--idempotency-key KEY` deliberately reuses an existing valid key for an
identical route/body. Otherwise generate one before POST. Print the validated
key to stderr before transmission and accepted operation ID before waiting,
including quiet mode; these nonsecret handles survive an acknowledgement loss.

Explicit global `--detach` renders admission separately. JSON output is exactly
`schema_version=1`, `kind="operation_admission"`, `idempotency_key` and
`acceptance` containing the validated server acceptance. There is no fabricated
terminal `outcome` or `exit_code`. Successful detach means accepted, not executed
or completed; human output says so too. Default commands never replace their
terminal Envelope with this object.

`operations show ID` and `operations lookup -- '<original-key>'` preserve exact server metadata
Envelopes (`operations show` / `operations lookup`) with `data.operation`.
`operations wait [--after N] -- '<operation-id>'` observes without submitting. The cursor resumes
sanitized bounded event pages; explicit oldest-sequence/truncated metadata reports
retention gaps. Ordinary progress requires both streams to be terminals with quiet off.
Gap notices, warnings/errors and mandatory safety handles remain on stderr even
with quiet and JSON.
No raw logs or event fields can become executable input or stdout JSON fragments.
The CLI escapes nonprintable Unicode/control characters in event text, keeping
each event one plain stderr line.

`--wait-timeout SECONDS` overrides client `wait_timeout` for job observation or
operation waiting, with finite `(0, 86400]` seconds. One absolute observation
deadline covers status/event/result reads and retries; trickling bytes/progress
cannot renew it. HTTP connect/read budgets and server queue/lock budgets remain
distinct. Job-only flags on non-submitting reads/bootstrap are refused;
operation wait accepts timeout/cursor, while show/lookup do not submit.

Timeout or Ctrl-C during observation yields HFAPI019 / exit 20 with original known key/operation ID/
route and a statement that accepted work may continue. Lost/unusable POST
acknowledgement, including interruption before it can be established, remains
HFAPI020. Other valid server/transport/protocol errors keep
their taxonomy plus known handles. A local observer error is not a terminal
execution Envelope. Never cancel accepted work or automatically replay with a
new key; missing/expired HFAPI013 or interrupted HFAPI015 history remains uncertain.
Validated retained-key 5xx refusals explicitly warn that work may continue while
preserving their server taxonomy; they are not proof of nonexecution.

Initialization requires the user-restated root. Its legacy optional UUID is
obtained from authenticated configured-target inspection when omitted, and must
match if supplied. No-confirm initialization performs no POST: preserve a failed
inspection Envelope, or return local HFARG003/HFMNT014 refusal with successful
unchanged inspection data plus `configured_archive_id` / `config_fingerprint`
and local invocation metadata. Disabled writer initialization explicitly refuses
HFAPI002 before POST; generic missing negotiated capabilities remain HFAPI018.
Confirmed submission still requires strict server DTO/maintenance guards. Existing production
archives must not be initialized again.

For a separately provisioned writer API source, these examples illustrate the
interface; run only against a separately authorized scope:

```text
hfcache --client-config /etc/hfcache/client.toml --json --detach sync
hfcache --client-config /etc/hfcache/client.toml --json operations lookup -- '<original-key>'
hfcache --client-config /etc/hfcache/client.toml --json operations show <operation-id>
hfcache --client-config /etc/hfcache/client.toml --json --wait-timeout 300 operations wait --after 12 -- '<operation-id>'
```

Use the same configured authority and credential class for key lookup. A stopped
client or sync/verify client service stops observation, not the server executor;
use [server drain](server.md#restart-and-drain) and
[recovery](recovery.md#preserve-four-kinds-of-authority) for execution
ownership. [Decision 120](adr/decision-120.md) records this boundary. Scheduled clients and Cockpit use the profile-specific boundaries below.

## Native Unix and public prefixes

Native Unix keeps fixed unprefixed local API paths usable
even when the same server has a public TCP `root_path`. Only trusted supported
Unix transport scope (`client=None` plus absolute Unix-path/None-port `server`)
selects that behavior; a missing peer alone is insufficient. Authentication/Host/Origin/bounds
remain. Returned links use the request's effective prefix, while TCP clients keep
their configured URL prefix and strict link checks. No new client setting or
schema is added; see [decision 123](adr/decision-123.md). Native Unix also accepts
the configured-prefixed spelling and emits matching operation/docs links; its
unprefixed OpenAPI view uses `/` without mutating the public cached schema.

## Cockpit client integration

The selected guarded rootless profile uses the fixed host client
`/usr/local/libexec/hfcache-client`, which launches the API-only image client
through fixed local Podman and a file-mounted `hfcache.api` secret. It does not use
host `ImportCredential`. API/worker sockets are `/run/hfcache/api/api.sock` and
`/run/hfcache/verification/verification.sock`; their services use the user manager.
Legacy system-bus writer controls remain blocked on this profile; never redirect
identically named units to another manager. The independent host guard and all
read-only restrictions remain.

A native Cockpit integration would require a service-identity transient host
CLI with fixed client configuration, `/run/hfcache/api.sock`, JSON and systemd
`ImportCredential=hfcache.api`. That credential is REST-writer only, separate from
daemon Hub `hf-token`. The shipped plugin has no native launcher selector; it
uses the fixed rootless wrapper above. No bearer reaches browser code, argv or
ambient environment.
Ordinary runtime calls omit archive `--config`; candidate validate/plan alone
uploads protected candidate content under exact candidate/base checks and the
privileged configuration flock.

The plugin requires a strict terminal schema-1 Envelope up to 16 MiB and separately
bounded diagnostics (8 KiB line, 64 KiB retained) and validated recovery handles.
Client stop, page closure or uncertainty never cancels accepted work or grants
recovery/replay authority. Candidate syntax, installed compatibility, required
preview and exact installed confirmation are distinct gates. Unknown/incompatible
authority blocks installation. The host-local report browser is a documented
exception, not another operational backend. See [Cockpit](cockpit.md) and
[configuration editing](cockpit.md#6-configuration-editing).

## Scheduled service observation

The guarded rootless deployment does not enable legacy calendars. In the
supported native scheduling profile, ordinary CLI waits remain finite and the
packaged sync/verify oneshots use
[`scheduled_client`](../src/hfcache/scheduled_client.py) for only fixed `sync` or
`verify-full`, keeping the unit active across repeated finite windows until the
exact terminal Envelope/exit is observed. Later timer ticks therefore merge into
the active service rather than creating duplicate submissions. No request queue,
domain engine, automatic POST replay or application scheduler is added.

[`scheduled-client.example.toml`](../packaging/scheduled-client.example.toml)
selects local Unix socket, API-only named `hfcache.api` credential and an explicit
expected archive UUID; replace its placeholder before enabling scheduling.
The same credential name is used by daemon/clients for encrypted-name binding,
separate from daemon-only Hub `hf-token`. Clients use AF_UNIX and need no archive
access; actual verifier imports no credential and has independent no-IP/source
masking. Host enforcement remains deployment acceptance.

The private [schema-1 handle](schemas.md)
binds fixed command, canonical endpoint, expected UUID and REST-writer class to
one key and optional accepted ID. Fsync key before the sole POST. Any existing
handle, including a crash before POST, permits only lookup/observation. Unknown/
malformed/future/mismatched history stays at HFAPI014/20; missing remote history
HFAPI013 or interrupted HFAPI015 grants no replay. Same-class credential rotation
can recover without a stored bearer/digest. Only exact terminal evidence permits
pending-file unlink/fsync; retained lock inode is never removed. Preserve state
on rollback and follow [actual executor drain](deployment-centos-stream-10.md),
not client-service termination. [Decision 121](adr/decision-121.md) records the
required refinement and repository-versus-host acceptance boundary.

The module entrypoint treats SIGINT/SIGTERM as observation interruption, reports
HFAPI019 / exit 20 and the sanitized preserved-state path, and restores both prior
handlers. Library import and `run_scheduled` have no signal side effects. Stopping
the client unit therefore preserves recovery handles; it does not cancel the
server's accepted operation.

## Troubleshooting and rollback

| Code/result | Meaning and next step |
| --- | --- |
| HFAPI017 / exit 10 | Invalid settings/selection or TLS client setup; check client TOML, endpoint group, absolute paths and explicit CA source |
| HFAPI003 / exit 10 | Selected protected API credential is missing/unsafe/malformed; fix that source rather than falling back anonymously |
| HFAPI001 / 401 or HFAPI002 / 403 | Server authentication/capability refusal; use the correct REST class and configured source, never a Hub/MCP token |
| HFAPI018 / exit 10 | Unsupported/malformed/version/identity-inconsistent read response or pre-send protocol refusal; inspect compatible API/schema/expected archive identity |
| HFAPI019 / exit 20 | Connectivity/read budget or finite observation deadline; preserve any known operation ID and continue observation deliberately |
| HFAPI020 / exit 20 | Unusable post-transmission acknowledgement; retain original key/route and perform authenticated lookup without a new-key replay |
| HFAPI013 or HFAPI015 / exit 20 | Missing/expired or unfinished/interrupted outcome; preserve uncertainty and follow the [recovery runbook](recovery.md#preserve-four-kinds-of-authority) |
| Terminal domain Envelope | Preserve its command/run/error/partial-result exit classification; transport HTTP 200 is not domain success |

Client TOML requires integer schema 1 independently of archive/receipt versions.
An older client without API-option support can reject `--client-config` with
usage exit 2; keep settings and retained observation state through rollback.
Unsupported client options never authorize deleting credentials/history or
inferring that accepted work did not execute.
