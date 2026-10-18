# Add the writer REST API, migrate the CLI, and expose read-only MCP

| Field | Value |
| --- | --- |
| Plan ID | `2026-10-17-plan-rest-api-and-mcp` |
| Status | active |
| Created | 2026-10-17 |
| Authorization | Tyler instructed implementation on 2026-10-17, on the feature branch with incremental commits and no push, merge, tag, deploy, or production operations. |
| Reviewed baseline | `wtcross/hfcache`, `main`, `86f6e8bbf78503497cb4c913c10b6612ee6b5aeb`; project version `0.1.10`; Python `>=3.14` |
| Feature branch | `feat/rest-api-and-mcp` |
| Tracker | [current.md](current.md) |
| Execution | Sequential work packages; one task record and one commit per package |

## 1. Outcome and scope

Run a lightweight, authenticated FastAPI application on the existing writer.
Expose the application's existing operational reads and writes through a
versioned REST API. Make the installed Typer CLI an API client for both the
writer and remote reader hosts. After REST, CLI, and their deployment boundary
pass the REST acceptance gate, mount a deliberately read-only FastMCP server
in that same application.

The writer remains the only machine with archive write authority. REST and MCP
are management and metadata interfaces, not new storage authorities. Published
ordinary-file trees, immutable manifests, references, retention semantics,
transaction journals, and consumer verification retain their current meaning.

This plan includes compatibility work in systemd and Cockpit, documentation
throughout implementation, security tests, and an operator deployment handoff.
It does not authorize production installation, starting new listeners on the
live writer, changing host policies, modifying NAS exports, enabling the
verification timer, or exercising destructive operations against the live archive.

### Explicit boundaries

- REST must cover every existing CLI command/mode in §4, including dry runs,
  diagnostics, verification, repair, quarantine cleanup, and guarded archive
  initialization. Do not quietly implement only status/list/sync.
- MCP exposes a useful subset of genuinely read-only metadata operations. It
  must not start verification, create jobs, probe writability, contact the Hub,
  download files, or reach any mutation service.
- Bulk artifact transfer remains the read-only `published/` export and the
  existing consumer copy workflow. No arbitrary-path file server, Hugging Face
  protocol proxy, repository-code execution, or model-serving API is introduced.
- No multiwriter support, per-repository ACLs, OAuth identity provider,
  configuration-install API, new scheduler, distributed broker, mutable archive
  database, or workflow framework. The bounded operation receipt mechanism in
  §5 is not permission to build a general orchestration engine.
- The documented `RET-011` generation-allocation gap and unrelated operator
  backlog remain outside this plan. Record newly discovered unrelated defects;
  do not silently activate their implementation.

## 2. Baseline review and required consequences

These observations refer to the pinned baseline, not a claim that future `main`
will remain unchanged. Reconcile the diff before activation. This review did not
run the repository test suite or inspect the deployed host.

| Area reviewed | Baseline observation | Required consequence |
| --- | --- | --- |
| [Planning guide](../agents/planning.md), [workflow](../agents/workflow.md), [current selector](current.md) | Latest commit introduces dated plans and individual task authority; no plan is currently active. | Preserve draft status now. Activate explicitly when implementation is authorized. Keep status in task files, not duplicate plan-table checkboxes. |
| [CLI](../../src/hfcache/cli.py), [CLI contract](../cli.md) | `cli.py` mixes Typer parsing/rendering with config loading, credentials, selection, locking, reconciliation, and domain orchestration. | Extract ordinary typed services; transport adapters must not invoke CLI callbacks, spawn the public CLI, or parse its stdout. |
| [Lock](../../src/hfcache/locking.py), [invariants](../invariants.md) | Archive exclusion is a local `flock` under `/run/hfcache`, with kernel release on process death. | Retain it across every actual mutating/verification operation, not for the daemon's lifetime. An in-process queue is not a replacement lock. |
| [CLI verification](../../src/hfcache/cli.py), [verification persistence](../../src/hfcache/verification.py) | Full verification leaves its guarded block before report/catalog persistence. New/revision verification do not use that guard. Persistence performs a catalog read/merge/write; atomic replacement alone does not serialize competing merges. | Characterize and fix this concurrency boundary in API-003: all non-estimate verification resolves, hashes, writes its report, and merges the catalog under the same archive lock. Record the intentional contract/ADR amendment and regression evidence. |
| [Logging](../../src/hfcache/logging.py) | `_run_id` is process-global; configuring logging replaces handlers. | Configure once per server process; scope correlation to execution contexts and propagate it into background work. |
| [Hub adapter](../../src/hfcache/hub.py) | `networking_disabled()` changes `os.environ["HF_HUB_OFFLINE"]`. | Never toggle process-wide networking flags in concurrent ASGI requests. Preserve offline verification using the isolated executor in §6. |
| [Verify service](../../packaging/systemd/hfcache-verify.service), [offline ADR](../adr/offline-verification.md) | Verification has `HF_HUB_OFFLINE=1`, no Hub credential, and `IPAddressDeny=any`; systemd owns its scheduling. | A TCP-only client would fail in the shipped sandbox. Use authenticated Unix-socket HTTP locally, and preserve deny-all IP protection around the actual verification executor, not merely around the client. |
| [Configuration](../../src/hfcache/config.py), [credential contract](../configuration.md) | Config is strict, frozen, schema-versioned; `--token-file` means a Hub token. | Separate archive/server/client configuration and API/Hub credentials. Define long-lived config refresh explicitly. Never reinterpret a Hub flag as API authentication. |
| [Cockpit CLI adapter](../../cockpit/src/api/hfcache.ts), [candidate pipeline](../../cockpit/src/api/config.ts) | Cockpit consumes schema-1 CLI envelopes, streams progress, and validates/plans a candidate config before root-owned atomic installation. | Preserve those workflows via the API-backed CLI. Candidate content is validated without granting a caller arbitrary writer paths or endpoints. Browser code never receives tokens. |
| [Framework ADR](../adr/fw-01.md), [pyproject](../../pyproject.toml) | Runtime dependencies are deliberately closed; Python is 3.14. | Record the correctness rationale for HTTP client, FastAPI, Uvicorn, and later FastMCP; lock and test compatible versions. Avoid unrelated dependency upgrades. |
| [Consumer boundary](../consumers.md), [AD-21](../adr/ad-21.md) | Reference locators are relative to `published/`; restricted repositories can be archived; all consumers share one authorization boundary. | API locators retain their base and exact publication identity. Reader and MCP credentials authorize the whole exposed archive, not merely public repositories. |

### Governing contracts and decisions

Load the relevant sections, not all historical documentation in every session:

- Identity/publication/deletion: `FS-01`–`FS-23`, `AD-09`–`AD-18`, `AD-20`,
  `TX-01`–`TX-07`, [architecture](../architecture.md),
  [schemas](../schemas.md), [recovery](../recovery.md).
- Concurrency and authority: `AD-17`, `AD-19`, `INV-005`–`INV-007`,
  [single-writer ADR](../adr/ad-17.md),
  [offline-verification ADR](../adr/offline-verification.md),
  [scheduling ADR](../adr/systemd-scheduling.md).
- Security/configuration: `AD-15`, `AD-21`, `INV-001`–`INV-004`,
  [security](../security.md), [configuration](../configuration.md).
- Interfaces/process: `INV-006`, `INV-008`–`INV-011`, `CP-01`–`CP-14`,
  `FW-01`–`FW-04`, [CLI](../cli.md), [Cockpit](../cockpit.md),
  [agent conventions](../agents/conventions.md), [release](../agents/release.md).

Create numbered progress decisions and corresponding `decision-NNN.md` records
for the service boundary/dependencies, command admission, credentials, verification
isolation, CLI migration, and MCP exposure as each is implemented. Allocate actual
numbers from the current log; do not reserve or invent already-accepted decisions
in this draft. Amend predecessor ADR statuses and links. Add new invariant IDs
only after checking the current register. A plan is not itself authority to
silently overwrite these contracts.

## 3. Target architecture and configuration

### 3.1 Small transport adapters, one domain implementation

Introduce these modules or narrowly scoped equivalents; record any naming changes
in the implementing task:

| Layer | Proposed location | Responsibility |
| --- | --- | --- |
| Shared services | `src/hfcache/services/{context,queries,commands}.py` | Typed immutable execution context, application results, reusable queries and guarded commands; no Typer/FastAPI/FastMCP types. |
| REST | `src/hfcache/api/{app,auth,models,routes}.py` | Application factory, schemas, authentication/authorization, HTTP error translation, dependency wiring. |
| Operation receipts/runner | `src/hfcache/api/operations.py` or a small package | Bounded admission, JSON receipts, idempotency, event/result retrieval, one heavyweight execution lane. |
| Server entry | `src/hfcache/server.py` | `hfcache serve`, application lifespan, sockets, process configuration, shutdown. |
| Verification executor | `src/hfcache/verification_worker.py` | Private Unix-socket protocol restricted to verification; calls the shared service inside its own sandbox. |
| API client | `src/hfcache/client.py` and client configuration module | HTTP/Unix-socket transport, typed validation, polling, retry rules; no archive access. |
| CLI | `src/hfcache/cli.py` plus rendering helpers as needed | Parsing and display only for normal runtime operations; isolated local bootstrap commands below. |
| MCP | `src/hfcache/mcp.py` or a small package | Explicitly registered tools over a narrow read-service interface, mounted only when enabled. |

Keep existing storage, publication, sync, retention, purge, recovery, quarantine,
repair, and verification algorithms behind the service layer. Do not duplicate
those algorithms in HTTP routes or introduce a second catalog authority.

### 3.2 Packaging and lightweight reader installation

Add the chosen, directly used HTTP client as an explicit runtime dependency;
use `httpx` unless compatibility testing provides a recorded reason for a different
maintained client. Add FastAPI and Uvicorn in a `server` extra, then standalone
`fastmcp` in an `mcp` extra only after the REST gate. Writer installs the appropriate
extras; a reader installs the base CLI without importing server/MCP modules.
Do not confuse the standalone `fastmcp` package with a different bundled
`FastMCP` class in the MCP SDK.

Resolve compatible versions on Python 3.14 at execution time, record the versions
and official documentation consulted, and update `uv.lock`. Pin release installs
to that lock. Update the gate to provision/test every implemented extra; optional
imports must not silently skip server tests. Add wheel smoke tests for base,
REST-server, and REST-plus-MCP installations. A base installation need not remove
pre-existing Hub dependencies to satisfy this plan.

### 3.3 Three explicit configuration domains

Preserve `ApplicationConfig` as the archive-policy model. Add strict, versioned
`/etc/hfcache/server.toml` and a lightweight client config, defaulting to
`~/.config/hfcache/client.toml` for an interactive client. Server config points
to the operator-owned archive config, sockets/TLS policy, credential sources,
limits, and maintenance/MCP enablement. Client config contains only endpoint,
API credential source, optional CA path, and optional expected archive UUID.
Do not add server-only fields to every existing archive TOML example.

Server transport/auth settings are immutable until restart. Load and validate the
installed archive policy afresh for each query or operation admission; freeze
one snapshot and fingerprint for that request/operation. A changed archive root
or UUID requires an operator restart, never a hot switch. Invalid updated config
fails new archive operations closed while version/health can diagnose the issue.
Already-running work keeps its original snapshot.

Before any queued side-effecting job starts, under its archive lock, reload the
installed policy and compare its fingerprint with the admitted fingerprint. Refuse
a stale job before mutation; do not quietly execute it against a different policy.
This is especially important when a purge target becomes configured after admission.
Configuration ownership remains `root:hfcache`; the server cannot install files in
`/etc/hfcache`.

### 3.4 Authentication, authorization, and exposure

Use bearer authentication on every REST endpoint, including health, capabilities,
OpenAPI, and interactive documentation. Disable interactive docs by default;
when enabled, protect both the UI and schema and avoid caching secrets. Use
FastAPI's bearer integration plus an application-owned verifier and stable
401/403 behavior; token extraction alone is not validation.

Support a small fixed capability model, not a user-management system:

| Credential class | Accepted interface | Capability |
| --- | --- | --- |
| REST writer | REST only | All implemented REST reads and writes; initialization still requires the maintenance gate. |
| REST reader | REST only | Non-mutating operations marked `R` in §4. |
| MCP reader | MCP only | The explicit tool/resource allowlist in §8; never valid for REST mutation. |

Provision distinct high-entropy opaque tokens through explicit protected files or
systemd credentials. REST writer authentication is required when REST is enabled;
unprovisioned optional reader classes grant nobody access. MCP cannot be enabled
without its own reader credential. Reject duplicate token values assigned to
different classes. Use constant-time comparison, bounded token length, deliberate
file ownership/type/mode validation, and no ambient Hub-token discovery. Rotation
is an operator-controlled credential replacement and restart, documented with
client reconnect consequences.

Tokens must never enter logs, validation-error input echoes, tracebacks returned
to callers, OpenAPI examples, operation receipts, manifests, journals, reports,
config fingerprints, browser state, URLs, or process arguments. Keep the Hub token
server-side and separate; it is never the inbound API bearer. Redaction tests must
include opaque tokens without the `hf_` prefix, not just existing Hub-token patterns.

Default to a service-private Unix socket and loopback TCP. Require verified TLS
for off-host access, directly or through an explicitly trusted local TLS proxy;
never suggest disabling certificate verification. Permit no wildcard CORS, URL
userinfo, or token query parameters. Check Host and browser Origin; configure
trusted proxy addresses explicitly and test forwarding/path-prefix behavior.
A Unix socket reduces exposure but does not exempt REST bearer authentication.
All authorized reader classes must be entitled to every archived repository under
AD-21; this plan makes no per-repository ACL claim.

## 4. REST contract and complete operation coverage

Use `/api/v1`. Resource routes use structured identifiers, not a free-form server
path: repository type plus namespace/name, full SHA, publication ID, run ID, and
transaction ID use existing validators. Resolve locators relative to `published/`
and validate identity/containment. Request models forbid unknown keys, coercion,
and mutually inconsistent mode/scope fields. HTTP query-string conversion must be
explicitly defined without weakening strict domain validation.

The following surface is the default design. `R` means REST reader or writer;
`W` means writer only. `J` returns an operation receipt (`202`) and is polled;
`Q` returns a bounded query/result directly. Semantic reads may use POST and may
create control-plane receipts, but never mutate the archive. The distinction is
capability/behavior, not the HTTP verb.

| Existing command/mode | Proposed `/api/v1` route | Access / execution | Required behavior |
| --- | --- | --- | --- |
| `version` (server inspection) | `GET /version`, `GET /capabilities` | R / Q | Server version, API/envelope support, archive identity when known, enabled features and role capabilities. Local `version` remains available offline. |
| `config validate` | `POST /config/validate` | R / Q installed; W / Q candidate | Same archive validation and credential-source reporting, never token values. Candidate policy follows §7. |
| `archive init --inspect` | `GET /archive/inspection` | R / Q | Existing inspection result, no automatic layout creation. |
| `archive init --confirm` | `POST /archive/initializations` | W / J | Disabled by default in server config; explicit confirm and restated configured root/UUID; all existing initialization refusals retained. |
| `doctor --read-only` | `POST /diagnostics` with `read_only=true` | R / J | Only non-probing checks; Hub checks remain explicit and bounded. |
| `doctor` | `POST /diagnostics` with `read_only=false` | W / J | Write probes serialized/guarded; no probe residue. No unsafe default. |
| `plan [selectors]` | `POST /plans` | R / J installed; W / J candidate | Existing Hub resolve/tree/estimate semantics, no archive writes; approved endpoint/credentials only. |
| `status [selectors]` | `GET /status` | R / Q | Local truth; no Hub dependency; unreachable/partial state honestly represented. |
| `list [--type] [--revisions] [selectors]` | `GET /repositories` and revision subresources | R / Q | Inventory from refs/manifests, including unmanaged repositories, correct filtering and deterministic ordering. |
| `verify --estimate` | `GET /verification/estimate` | R / Q | No hashing or report/catalog persistence; unknown rate stays unknown. |
| `verify --new [--run-id]`, `--full`, `--revision` | `POST /verifications` | W / J | Exactly one mode; isolated offline executor; complete locked read-and-persist boundary. |
| `prune --dry-run`, `--apply` | `POST /prune-plans`, `POST /prunes` | R / J; W / J | Preview only versus fresh locked plan/apply; retain one-eligible-revision-per-repository behavior. |
| `purge --dry-run`, `--apply` | `POST /purge-plans`, `POST /purges` | R / J; W / J | Explicit selectors XOR all-unmanaged; no configured target; complete shallow-layout validation and audit preservation. |
| `recover --dry-run`, `--apply` | `POST /recovery-plans`, `POST /recoveries` | R / J; W / J | Ambiguity remains a safety refusal; no guessing or automatic startup recovery. |
| `quarantine --dry-run`, `--apply` | `POST /quarantine-plans`, `POST /quarantine-cleanups` | R / J; W / J | Explicit transaction IDs only; prove redundancy; preserve unknown/repair evidence; do not reconcile unrelated work. |
| `repair TYPE:ID@SHA [--reason]` | `POST /repairs` | W / J | Original manifest expectations, isolated download, new instance, original generation, grace period. |
| Existing reports/references/manifests | `GET /runs`, `GET /runs/{run_id}`, repository ref/manifest subresources | R / Q | Read existing evidence by validated IDs; no caller-selected filesystem paths. |
| New operation observation | `GET /operations`, `GET /operations/lookup`, `GET /operations/{id}`, `/result`, `/events` | R / Q | Bounded metadata, terminal result, sanitized sequenced events, explicit pagination and retention. |

Create a machine-checkable parity matrix in `docs/api.md`: every existing CLI
mode maps to a service, route, role, lock/Hub effects, CLI test, and API test.
Characterization may discover an existing code/document mismatch (for example
selector handling); resolve it explicitly, preserving the required contract or
recording an intentional amendment, rather than blindly freezing a bug.

Use bounded pagination with stable documented ordering for inventory, revisions,
reports, and events. Never silently truncate a legacy CLI result: the client must
walk pages or stream a complete terminal envelope. A page sequence is not an
archive-wide transaction snapshot. Pin exact ref/publication identities where
needed; vanished instances yield a visible retryable/stale result rather than
substitution with a new current instance. Reject oversized request bodies even
without Content-Length, bound list/string fields, and stream large existing report
results rather than assembling unbounded duplicate response buffers.

Keep API wire schemas separate from durable archive models. Specify typed
query/page models, an operation-receipt model, and a sanitized `ApiProblem`
containing request ID plus stable codes/messages and applicable application exit
classification. A terminal command result remains the existing schema-1 Envelope;
the client must preserve its domain payload, outcome, and run identity. Document
how query results become that envelope without exposing framework exceptions or
silently changing the legacy data contract.

Keep HTTP admission errors separate from domain outcomes. Define and test 401
(missing/invalid bearer plus challenge), 403 (capability denied), 404 (absent
resource), 409 (stale fingerprint/conflicting key/not-yet-terminal result), 422
(invalid request), 503 (queue full, draining, executor unavailable), and sanitized
500 (unexpected internal error). Successful retrieval of a terminal operation can
be HTTP 200 with a failed application envelope. Never convert an application
integrity failure to success merely because polling succeeded.

## 5. Long-running execution without a workflow engine

Downloads and full verification can exceed HTTP request timeouts. Do not run them
on the ASGI event loop or in unsupervised request `BackgroundTasks`.

### Admission and results

Use one heavyweight execution lane and a bounded FIFO pending queue (default 16,
strictly configurable), plus a small bounded pool for metadata reads. A serial
lane limits load; the existing `flock` remains the cross-process safety authority.
Simple reads stay available during long work. Add a separate daemon-instance lock
so accidental second Uvicorn workers cannot create competing admission registries;
production uses one ASGI worker and no auto-reload.

An accepted job gets a server-generated operation ID and a durable JSON receipt
before it can become runnable or return 202. Store service-private receipts under
`/var/lib/hfcache/api/`, not in `published/`. Use existing atomic serialization
primitives, a documented independent schema version, restrictive permissions, and
an explicitly configured test directory. A receipt references existing run IDs,
reports, and journal evidence; it never supersedes those artifacts or instructs
the domain engine to replay checkpoints.

States are `queued`, `waiting_lock`, `running`, `succeeded`, `failed`, or
`interrupted`. A terminal success/failure stores or references the exact schema-1
command envelope. An interruption is not success and must not fabricate a domain
report. Define a new stable `HFAPI` taxonomy, map client configuration/auth errors
to exit 10 and unavailable/uncertain execution to exit 20, and preserve existing
domain exit codes and their 40 > 50 > 30 priority.

Require `Idempotency-Key` for side-effecting submissions; the client generates it
before first transmission. Make `(nonsecret principal identity, key)` the unique
binding and compare the canonical route/request digest on retries, with the
admitted config fingerprint retained in the receipt. A matching key/request
returns the original operation even if
installed config later changes; a different request under the key is 409.
Authenticate every lookup/retry anew. The durable receipt is authoritative for key
lookup; any in-memory index is rebuildable. Test concurrent submissions and crashes
at every admission boundary. Do not claim exactly-once execution across all crashes.

Apply the configured waiting budget across queue residence and lock acquisition,
not twice. Refuse expired queued work without invoking domain code. Revalidate
scope/fingerprint/preflight under the archive lock immediately before execution;
never apply an earlier preview verbatim. Do not nest acquisition of the same lock
through two service layers. The verification worker acquires its own lock rather
than receiving one held by its caller.

### Crash, disconnect, shutdown, and retention

A dropped HTTP connection or CLI Ctrl-C stops waiting, not accepted server work.
Offer `operations show`, `operations wait`, `operations lookup`, and optional
explicit detached submission. Accept an explicit `--idempotency-key` for deliberate
retry of a known submission. Emit the nonsecret submission key to stderr before
the first mutation POST, then the operation ID once acknowledged. This preserves
a lookup handle even if the acknowledgement is lost. The authenticated lookup
route takes the key in an `Idempotency-Key` header and searches only the caller's
principal namespace; it never submits work. Distinguish not-found/expired history
from proven nonexecution. Document these safety-correlation messages even in
quiet mode. Print the operation ID before beginning the wait. Normal legacy
commands wait and emit exactly one final envelope, never the interim receipt on
stdout. Progress comes from bounded cursor-based event polling; callers do not
receive arbitrary journald contents.

On shutdown, stop admission, drain/join work, and preserve all active receipts.
The sync producer must still finish or join before its archive lock is released.
Forced termination leaves journals/receipts for diagnosis. On restart, do not
automatically rerun any pre-existing queued/running mutation. Reconcile receipt
state with a verifiably still-running isolated worker and existing durable results;
otherwise classify it as interrupted with a clear operator path. Do not infer
completion from a released lock, PID alone, elapsed time, or a disconnected socket.
A surviving verification worker is reattached by exact operation ID or awaited;
no duplicate execution is launched. Recovery of archive transactions still follows
the existing guarded application path and stale-age policy.

Retain terminal results/keys for a documented configurable period, default 30 days;
never age out nonterminal or ambiguous records. Delete only validated,
application-owned terminal records. Within retention, retries are deduplicated;
after expiry, clients must not automatically replay an uncertain mutation with an
expired key. Missing/expired history returns a documented unavailable/expired
result, not invented success. Local receipt loss is control-plane history loss,
not permission to reconstruct and rerun commands from journals.

The numbered decision must explicitly distinguish this bounded, non-resuming
submission registry from the forbidden home-built workflow engine. No DAGs,
resumable command graphs, broker, database, or journal-driven normal execution.

## 6. Verification isolation and writer lifecycle

Keep all non-estimate verification out of MCP. It records evidence, so it belongs
to the serialized writer operation surface even though it must never repair data.

Provide a narrowly scoped, systemd socket-activated verification executor on a
private Unix socket. It accepts only validated verification mode/scope, operation
identity, and an expected installed-config fingerprint. It cannot run arbitrary
commands, load a caller-selected config path, install files, or accept credentials.
Run it as `hfcache`, with `HF_HUB_OFFLINE=1`, `IPAddressDeny=any`, no Hub/API/MCP
credentials, and the existing filesystem/systemd hardening. It calls the shared
verification service and owns the archive lock through report/catalog persistence.
Protect the socket and check peer identity; use bounded framed messages and
operation-correlated result/status replies. Persist a terminal executor receipt
before declaring completion so daemon reconnect can identify the exact outcome.

The server delegates through this socket; it does not call `systemctl` with client
arguments or gain broad sudo/polkit privileges. The worker must not inherit the
API process's secret-bearing environment or file descriptors. Fail verification
admission closed if the required executor is unavailable. Hermetic tests inject a
fake executor; no production fallback quietly runs verification in the
network-enabled ASGI process. Document standalone development limitations.

Serve writer-local REST over `/run/hfcache/api.sock`; scheduled CLI clients use
that socket with their own API credential. This allows the existing verify-client
unit to retain deny-all IP policy. Move the effective no-IP/no-Hub protections to
the actual executor as well. Preserve sync/verify unit names as API-client wrappers
so schedules, Cockpit integration, exit outcomes, and monitoring remain legible.
Use a single app/admission registry for local and TCP listeners; test the chosen
Uvicorn socket arrangement rather than launching an independent server per socket.

Update `scripts/install-release.sh`, unit/config packaging, hardening probes, and
release runbooks for server dependencies, socket lifecycle, credential ownership,
startup ordering, graceful drain, rollback, and stale lock-directory protection.
Never unlink or recreate a lock file another process may still hold. Do not enable
`hfcache-verify.timer`, stop `hfcache.target`, relax SELinux, add blanket egress
exceptions, or test NFS disconnection against the production mount.

Stopping an API-backed `hfcache-sync.service` or closing Cockpit now stops a client,
not necessarily the writer. Explicitly amend supervised-cancellation/recovery
instructions (including architecture §7.8.2): proof of writer termination must
identify the actual executor and operation. Preserve the narrow QUA-003 age-policy
exception; a vanished CLI process is not sufficient proof to invoke it.

## 7. CLI and Cockpit migration contract

### Normal runtime commands

Keep existing commands, selectors, human rendering, JSON schema-1 envelopes,
warning behavior, and domain exit classifications. Writer and reader use the same
API client. A reader needs no archive mount, archive TOML, service UID, `/run`
write access, or Hub credential. There is no silent direct-filesystem fallback
when the API is down and no automatic daemon startup from a client command.
API-backed status, doctor, and installed-config validation describe the writer,
not the reader host's mount or local Hub account. Client connectivity errors are
reported as transport failures; the independent consumer copy helper still owns
local-copy verification.

Add `--api-url`, `--api-socket`, `--client-config`, and `--api-token-file`; URL and
socket are mutually exclusive. Precedence is explicit CLI options, then client
config, then the local Unix-socket default. API credential precedence is explicit
API token file, then client-config token file, then the explicitly named systemd
API credential; an installed unusable source is an error, not anonymous fallback.
Do not add a plaintext-token argument. Disable ambient HTTP proxy/credential
behavior unless explicitly configured and documented; never forward Authorization
through redirects to a different origin.

Keep `--help` and local `version` independent of any config/server, and add
`version --server`. `hfcache serve` is writer-local bootstrap and uses server
configuration. Retain an explicit `config validate --local` mode for offline
operator validation/bootstrap; it validates on that host, is never an API fallback,
and is documented separately from server-side validation.

For API-backed runtime operations, `--token-file` is rejected with a clear
migration error; it remains a Hub credential option only in explicitly local
bootstrap/validation contexts. Add a dedicated `serve --hub-token-file` where
needed for non-systemd development. Never transmit an operator's Hub token to the
REST server as an implicit override.

### Candidate configuration and legacy `--config`

For API `config validate` and `plan`, an explicit `--config PATH` means a candidate
file on the CLI host: read bounded TOML content and submit that content, never a
server pathname. The server validates it without installation. Installed-config
operations with no explicit candidate use the server's installed archive policy.
An explicit `--config` on other API runtime commands is a migration error rather
than a silently ignored option. Update shipped systemd/Cockpit callers so they
no longer pass the archive path to ordinary runtime commands.

Candidate validation returns syntax/policy validity separately from compatibility
with the running writer. For candidate Hub planning, require the candidate archive
root/UUID, Hub endpoint, credential source, token mode, and expected account to
match the installed authority boundary; otherwise refuse planning with a specific
reason. It may preview repository/retention/worker-policy changes. Resolve only
the installed authorized Hub credential, never a candidate-selected credential.
Prospective authority changes can be syntax-validated but require an operator
configuration/restart procedure before network planning. This deliberate limit
prevents sending the writer's credential to an attacker-controlled endpoint.

Keep Cockpit's existing administrative candidate → validate → preview → atomic
install pipeline. Installation and backups remain privileged host work outside
REST. After install, a fresh API query/operation observes the new config fingerprint
without restarting the server unless authority changed. Update Cockpit UI messaging
for candidate restrictions and running-operation snapshots. Its transient CLI
units import the API credential directly from systemd; browser code never reads
that credential. Preserve schema-1 parsing and streamed operation progress through
the CLI; do not rewrite Cockpit to hold a writer bearer in JavaScript.

## 8. MCP, after the REST gate

Do not add MCP runtime dependencies, imports, endpoints, or tools before API-016
is completed with evidence. REST must be independently usable with MCP absent.

Use standalone FastMCP's Streamable HTTP application at `/mcp`. Mount its
`http_app` in FastAPI and compose both lifespan contexts; do not replace the REST
lifespan or start nested web servers/event loops. Validate the exact APIs against
the locked FastMCP version. Keep MCP disabled unless configured and provisioned.

Implement a production verifier using FastMCP's supported token-verification
extension and the shared credential-validation primitive. Restrict it to the MCP
reader credential. Do not ship the documentation's development-only static-token
verifier as a production shortcut. Authenticate each supported transport request
and test session/credential isolation. This is a pre-provisioned bearer deployment,
not an OAuth discovery/registration implementation; document which clients can
supply the configured bearer and do not claim universal OAuth-client compatibility.

### Initial explicit tool allowlist

- `get_archive_status`: local archive headline/state, with honest unknowns.
- `list_repositories`, `list_revisions`: bounded pages, including unmanaged data.
- `get_current_reference`: exact immutable publication locator and identity.
- `get_revision_manifest`: validated exact revision/publication metadata, with
  paginated file entries where needed; no arbitrary artifact-file reads.
- `list_run_reports`, `get_run_report`, `get_verification_report`: existing
  evidence with bounded projections/pages, never execute a run.
- `estimate_verification`: existing estimator only, no hashes or persisted result;
  bound concurrency because a large archive still requires metadata traversal.

Use a narrow read-service protocol with no command submission, writable storage
helper, credential resolver, or Hub client available to tool implementations.
Treat archive-sourced strings as untrusted data, not executable instructions.
Set appropriate `readOnlyHint`/`destructiveHint` annotations, but enforce the
allowlist structurally and at authorization boundaries; hints are not access
controls. Do not automatically expose the full FastAPI OpenAPI document and then
attempt to blacklist writes. Resources/prompts, if introduced, receive the same
review; no generic command/resource dispatcher or URL/path fetcher is allowed.

REST dry-run cleanup plans, candidate validation/Hub planning, and diagnostics can
remain REST-only. No MCP tool triggers job creation, verification persistence,
recovery, probes, or cache writes. Reads must not rebuild a missing catalog.
No-side-effect tests compare archive files and service operation state before and
after every tool (including failures); ordinary access logs are the explicit
non-archive operational exception.

Test both direct tool behavior and the actual mounted HTTP boundary, including
lifespan startup/shutdown, bearer failure, path prefixes, session identity,
streaming, disabled mode, unexpected tool names, and attempted mutation arguments.
Use the locked FastMCP version's streaming-capable test transport or a real
throwaway socket; an in-memory `Client(mcp)` test alone does not test HTTP auth.

## 9. Ordered phases and task records

Each row is one work package and one commit. A package can contain several related
implementation/test/documentation subtasks. Do not combine independent rows into
one commit or duplicate task status here. The task files own dependencies and
completion evidence. Execute sequentially; this plan does not authorize parallel
writers to the branch.

| Phase | Work package and task record | Depends on |
| --- | --- | --- |
| 0 — Contracts and activation | [API-001 — Activate the feature branch and specify the transport boundary](tasks/api-001-contract-and-activation.md) | None |
| 1 — Shared services | [API-002 — Extract transport-neutral query services and command results](tasks/api-002-extract-queries-and-results.md) | [API-001](tasks/api-001-contract-and-activation.md) |
| 1 — Shared services | [API-003 — Extract guarded command services and close verification lock gaps](tasks/api-003-extract-guarded-commands.md) | [API-002](tasks/api-002-extract-queries-and-results.md) |
| 1 — Shared services | [API-004 — Make correlation and offline execution safe for concurrent requests](tasks/api-004-isolate-execution-context.md) | [API-003](tasks/api-003-extract-guarded-commands.md) |
| 2 — REST implementation | [API-005 — Add server dependencies, strict configuration, and bearer capabilities](tasks/api-005-server-config-and-bearer-auth.md) | [API-004](tasks/api-004-isolate-execution-context.md) |
| 2 — REST implementation | [API-006 — Serve authenticated REST resources with a controlled lifespan](tasks/api-006-fastapi-lifecycle-and-reads.md) | [API-005](tasks/api-005-server-config-and-bearer-auth.md) |
| 2 — REST implementation | [API-007 — Persist bounded operation receipts and idempotent admission](tasks/api-007-operation-receipts-and-idempotency.md) | [API-006](tasks/api-006-fastapi-lifecycle-and-reads.md) |
| 2 — REST implementation | [API-008 — Run bounded operations and implement the private offline executor](tasks/api-008-bounded-runner-and-offline-executor.md) | [API-007](tasks/api-007-operation-receipts-and-idempotency.md) |
| 2 — REST implementation | [API-009 — Expose sync, verification, planning, diagnostics, and validation](tasks/api-009-sync-verification-and-diagnostics-api.md) | [API-008](tasks/api-008-bounded-runner-and-offline-executor.md) |
| 2 — REST implementation | [API-010 — Expose retention, recovery, repair, quarantine, and guarded initialization](tasks/api-010-guarded-maintenance-api.md) | [API-009](tasks/api-009-sync-verification-and-diagnostics-api.md) |
| 3 — CLI and REST integration | [API-011 — Build the typed API client and reader-only configuration](tasks/api-011-typed-client-and-client-config.md) | [API-010](tasks/api-010-guarded-maintenance-api.md) |
| 3 — CLI and REST integration | [API-012 — Move CLI reads and candidate validation/planning onto the API](tasks/api-012-migrate-read-cli-and-candidates.md) | [API-011](tasks/api-011-typed-client-and-client-config.md) |
| 3 — CLI and REST integration | [API-013 — Move CLI writes onto the API and preserve resumable observation](tasks/api-013-migrate-write-cli-and-operation-waiting.md) | [API-012](tasks/api-012-migrate-read-cli-and-candidates.md) |
| 3 — CLI and REST integration | [API-014 — Package the server, private worker, and API-backed scheduled services](tasks/api-014-systemd-and-deployment-integration.md) | [API-013](tasks/api-013-migrate-write-cli-and-operation-waiting.md) |
| 3 — CLI and REST integration | [API-015 — Preserve Cockpit operations, progress, and candidate configuration flow](tasks/api-015-cockpit-api-client-compatibility.md) | [API-014](tasks/api-014-systemd-and-deployment-integration.md) |
| 3 — CLI and REST integration | [API-016 — Prove complete REST and CLI parity before beginning MCP](tasks/api-016-rest-acceptance-gate.md) | [API-015](tasks/api-015-cockpit-api-client-compatibility.md) |
| 4 — Read-only MCP | [MCP-001 — Mount optional authenticated FastMCP after REST acceptance](tasks/mcp-001-mount-authenticated-fastmcp.md) | [API-016](tasks/api-016-rest-acceptance-gate.md) |
| 4 — Read-only MCP | [MCP-002 — Expose a curated, structurally read-only archive toolset](tasks/mcp-002-curated-read-only-tools.md) | [MCP-001](tasks/mcp-001-mount-authenticated-fastmcp.md) |
| 4 — Read-only MCP | [MCP-003 — Prove MCP cannot mutate through tools, auth, or transport bypasses](tasks/mcp-003-mcp-security-and-side-effect-tests.md) | [MCP-002](tasks/mcp-002-curated-read-only-tools.md) |
| 4 — Read-only MCP | [MCP-004 — Complete MCP client guidance and the read-only acceptance gate](tasks/mcp-004-mcp-client-docs-and-acceptance.md) | [MCP-003](tasks/mcp-003-mcp-security-and-side-effect-tests.md) |
| 5 — Closure | [API-017 — Close the plan with integrated evidence and an operator rollout handoff](tasks/api-017-final-integration-and-handoff.md) | [MCP-004](tasks/mcp-004-mcp-client-docs-and-acceptance.md) |

API-016 is a hard dependency boundary: finish the complete REST/client/deployment
implementation and its repository tests before beginning MCP-001. Operator-only
production acceptance is separately recorded as a deployment prerequisite, not
pretended complete and not a reason to alter live-host safety limits.

## 10. Documentation is part of every package

Create contracts before or alongside implementation in the same commit; never
publish a proposed API behavior as already implemented without an explicit status.

| Documentation surface | Required coverage and owning packages |
| --- | --- |
| New `docs/api.md` | Versioned schema, full command/role/effect matrix, errors, examples, pagination, jobs/idempotency, OpenAPI policy; API-001 and every affected REST package. |
| New `docs/server.md` | Process model, credentials, configuration, listeners, worker isolation, lifecycle, deployment/rollback; API-005/006/008/014. |
| New `docs/api-client.md` | Writer/reader setup, TLS, flags/precedence, migration, candidate semantics, polling/interruption; API-011/012/013. |
| New `docs/mcp.md` | Exact tools, authentication/client setup, bounds, limitations, read-only proof, disabled behavior; MCP-001 through MCP-004. |
| `docs/cli.md`, `README.md`, `CHANGELOG.md` | CLI-only assertion removal, new entry points/examples, stable envelopes/exits, Unreleased notes; update when behavior lands, not only at closure. |
| `docs/configuration.md`, examples under `packaging/` | Separate config domains, credential precedence, reload/fingerprint semantics; API-005/011/012/014. |
| `docs/architecture.md`, `docs/schemas.md`, `docs/security.md`, `docs/invariants.md` | New service/trust boundaries, receipt formats, concurrent verification, threats and controls; affected implementation package, not a final documentation batch. |
| `docs/operations.md`, `docs/recovery.md`, deployment and release docs | Service startup/drain, uncertain jobs, real executor termination, key expiry, rollout/rollback and hardening checks; API-007/008/013/014. |
| `docs/cockpit.md`, `docs/cockpit-plugin/`, relevant agent routing | API-backed units, credentials, candidate flow, operation progress and host limits; API-015 and related packages. |
| `docs/consumers.md` | Reader CLI without writer config/mount, whole-archive authorization, publication-relative locators; API-006/012 and MCP-004. |
| ADRs/index, progress, plan/task/current | Review and evidence in every package. Historical `docs/plan.md` gets dated attributed amendments where standing claims are superseded, not silent history rewrites. |

Maintain local links and stable anchors. Tests parse architecture checkpoint tables
and CLI contract text, so documentation-only edits still run the full gate. Add
deterministic OpenAPI/route-contract coverage and documentation-example checks;
do not generate a schema containing machine-specific URLs, secrets, or timestamps.

## 11. Autonomous execution and commit protocol

1. Read `AGENTS.md`, `git log --oneline -20`, `git status`, `current.md`, relevant
   progress/Decisions/Operator handoff, and agent workflow/environment. Reconcile
   the pinned baseline with the actual checkout. Do not discard unrelated changes.
   The imported draft/task files are expected uncommitted input, not an excuse to
   reset the tree.
2. When instructed to implement, create or safely resume `feat/rest-api-and-mcp`
   from the current agreed `main` baseline before implementation commits. Fetch the
   verified repository remote to check drift where available. Record the actual
   base SHA in API-001. Do not reset an existing feature branch or silently discard
   its work; inspect it and reconcile task evidence first.
3. Verify the proposed API/MCP package IDs and paths are unused. If `main` added
   conflicting IDs since this draft, allocate unused IDs within those families and
   update every link before activation. Existing completed IDs are never reused.
4. Activate this plan, populate task files, and update the sole current selector
   before implementation. If another plan is active, preserve it and record an
   authorized pause/supersession rather than silently replacing it. The user's
   implementation instruction authorizes this scope, not unrelated backlog.
5. Mark the next dependency-ready task `in_progress`. Read its linked contracts,
   affected invariants, and relevant ADRs. Implement its related subtasks, tests,
   and documentation together. On interruption, inspect uncommitted work before
   resuming; never infer completion from a summary or rerun completed mutations.
6. Run `scripts/check.sh` before each commit. Preserve the lock, format, lint,
   pyrefly, Python suite, build, and applicable Cockpit checks. Provision implemented
   extras explicitly. When Cockpit changes, a skipped plugin gate is not passing
   evidence. Run `scripts/check.sh --with-build` at REST and final acceptance.
   Use opt-in live/NFS/hardening tests only in an authorized safe environment.
7. Record actual acceptance and validation results, invariant/ADR review, docs
   changes, and operator handoff in the task. Add the completed linked progress
   entry in that same commit, using the package ID and `this commit`, not an
   invented hash. Set the next-task pointer. Commit as `<ID>: <summary>`; every
   package's task supplies a suggested message. Never make one giant end commit
   or squash away package boundaries.
8. Continue to the next ready task without asking for routine confirmation. If a
   real prerequisite is unavailable, mark that task blocked with an exact unblock
   condition and preserve evidence. Do not lower a safety control or claim an
   unrun check passed. Necessary in-scope package splits receive fresh IDs and
   linked plan amendments before execution.
9. No automated main-branch commits, merges, force-pushes, release tags, or pushes
   to either remote. The repository's maintainer main-push procedure does not
   apply to this feature-branch execution. Deliver the incremental local history
   for maintainer review; push only upon separate explicit instruction.
10. Close after all scoped implementation acceptance criteria pass. Preserve the
    plan/tasks at their original paths, record their dispositions, and clear this
    plan's active selection. Explicitly retain pending operator-only deployment
    checks as a no-deploy prerequisite; do not claim a production rollout happened.

Suggested activation selector (edit the real file after authorization; do not
ship this as an automatic overwrite):

```markdown
# Current plan

| Field | Value |
| --- | --- |
| Active plan | [REST API and MCP](2026-10-17-plan-rest-api-and-mcp.md) |
| Next task | [API-001](tasks/api-001-contract-and-activation.md) |
| Blockers | None |
```

## 12. Acceptance and validation

### REST gate — API-016

All existing command modes in §4 have typed services, authenticated REST coverage,
compatible API-backed CLI behavior, and tests. Reader credentials cannot perform
writer operations, and ordinary readers work without writer filesystem state.
Candidate validation/planning, systemd wrappers, Cockpit envelopes/progress, and
local version/help remain functional. MCP is still absent from this gate.

Tests prove: concurrent mutation exclusion across processes; verification locks
through persistence; no Hub in verification; ASGI responsiveness during heavy
work; admission/idempotency crash boundaries; uncertain-execution handling;
shutdown/worker lifecycle; no credential disclosure; root/ID/selector/path safety;
stale destructive scopes refused; unknown archive state preserved; corrupt/missing
catalog tolerance; stream/page behavior; correct domain envelopes/exits.

Run the complete offline gate and wheel-install checks with real API socket tests
on throwaway local fixtures. Do not invoke a production archive initialization or
mutation. Test unit files/protocols hermetically and rehearse real hardening only
in an authorized disposable or operator-approved environment. Record the
host-specific checks that still gate deployment separately.

### MCP gate — MCP-004

REST passes unchanged with MCP disabled and enabled. Mounted HTTP handshake,
authentication, streaming/session behavior, all allowlisted tools, and rejected
writer attempts pass. Successful, failed, malformed, and concurrent MCP reads
change no archive or operation state. Reader credentials never gain a write path
through REST, a hidden tool, a resource handler, or generic argument dispatch.
Documentation matches the actual registered tool schema and tested client setup.

### Final closure — API-017

Run `scripts/check.sh --with-build`, all implemented-extra tests, Cockpit gate,
local transport/integration suites, documentation links/examples, and the
old/new-format compatibility drill wherever a durable/config format changed.
Review commits for task evidence, contracts/ADRs/invariants, and documentation
updates. Produce an operator checklist covering credentials/TLS, service install,
worker egress, NFS/hardening acceptance, drain/rollback, and the still-disabled
verification timer. Mark any unperformed host check explicitly pending; production
deployment is not part of completion authorization.

## 13. Implementation references

Repository-relative links above refer to the reviewed source paths. The reviewed
public tree is [the pinned baseline](https://github.com/wtcross/hfcache/tree/86f6e8bbf78503497cb4c913c10b6612ee6b5aeb).
Official framework references consulted on 2026-10-17; recheck against locked
versions when implementing, especially FastMCP imports and test transports:

- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/).
- [FastAPI bearer security tools](https://fastapi.tiangolo.com/reference/security/).
- [FastMCP mounting and lifespan integration](https://gofastmcp.com/integrations/fastapi).
- [FastMCP token-verification extensions and limitations](https://gofastmcp.com/servers/auth/token-verification).
- [FastMCP HTTP deployment](https://gofastmcp.com/deployment/http).

## 14. Lifecycle and amendments

- 2026-10-17: Draft created from Tyler's requested REST-first, API-backed CLI,
  read-only MCP scope. Feature-branch name normalized to
  `feat/rest-api-and-mcp`. No implementation authorization, activation, repository
  commit, gate result, or production change is asserted by this draft.

- 2026-10-17: Activated by Tyler's implementation instruction, on
  `feat/rest-api-and-mcp` at base
  `86f6e8bbf78503497cb4c913c10b6612ee6b5aeb`. No other active plan or
  conflicting API/MCP package IDs; imported draft/tasks preserved.

- 2026-10-17 API-001: The complete [API matrix](../api.md) explicitly
  includes `POST /syncs` (writer/job), correcting the omission from §4's
  proposed route table without changing scope. API-002 will correct the
  characterized unmanaged status/list selector discrepancy to the CLI contract.

- 2026-10-17 API-004: Decision 111 replaces the shared-service offline environment
  toggle with structural no-Hub/no-credential verification and a startup-only
  initializer for the later dedicated executor. It also scopes correlation and
  distinguishes execution-host invocation mode from future receipt submitter
  metadata. API-008/014 still own the credential-free no-IP executor; no ASGI
  fallback, durable archive schema change, dependency or MCP work is introduced.

- 2026-10-17 API-005: Decision 112 records the actual Python 3.14 transport
  dependency lock, separate strict server configuration, fresh pinned archive
  snapshots and reusable fixed bearer capabilities. Existing HFCFG codes cover
  server validation; HFAPI001–004 classify authentication/capability/credential
  failures at exit 10. Framework-independent primitives and an optional FastAPI
  security adapter add no runtime endpoint/listener. API-006 owns route-level
  enforcement, API-007/008 own receipts/execution, and MCP remains gated.

- 2026-10-17 API-006: Decision 113 implements authenticated metadata HTTP and
  one foreground Unix/TCP bootstrap, with finite query/wire budgets, shared
  no-follow readers, content-bound cursor continuation and bounded evidence
  streams. HFAPI005/008/009/011 explicitly classify service safety failures at
  exit 20; other HFAPI request/auth/config failures remain 10. `serve` has no
  success stdout Envelope; its typed startup failures retain the normal JSON
  failure contract. Eight read matrix rows are implemented, while installed/
  candidate validation, jobs/writes, CLI-client migration and MCP remain pending.

- 2026-10-17 API-007: Decision 114 implements independent local receipt schemas,
  authoritative hashed-key binding, bounded events/results and authenticated
  observation. Fixed credential-class namespaces survive rotation; all REST
  readers share operation metadata/results, while key lookup is namespace-local.
  Count/space caps refuse admission rather than evicting unexpired terminal keys;
  interrupted/ambiguous/nonterminal history never expires. Startup never replays;
  explicit interruption waits for later exact-worker reconciliation. No heavy lane, command POST route or MCP work is
  added; API-008/009/010 retain execution/submission responsibilities.

- 2026-10-17 API-008: Decision 115 implements the bounded FIFO execution lane,
  one absolute queue/lock deadline and service-owned under-lock policy guard.
  The private verifier carries the same host-monotonic deadline across bounded
  peer-checked Unix IPC and reuses the independent operation-store schema for
  exact durable outcomes. Reconcile a surviving exact worker before interruption;
  never replay old work. Client disappearance is not writer termination.
  Public POST routes remain API-009/010; socket activation, credential-free/no-IP
  systemd enforcement and installed-host acceptance remain API-014. No new
  dependency, durable archive family or MCP work is introduced.
