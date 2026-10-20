# Command line reference

`hfcache` uses the authenticated REST API for operational commands. The writer
owns archive policy, Hub credentials, locks, publication and recovery. Clients
never fall back to local archive execution or start a daemon after a connection
failure. Read results are complete within explicit bounds or fail; there is no
unbounded local operational mode.

Local exceptions are help, ordinary `version`, explicit `config validate --local`
and foreground `serve`. `version --server` and ordinary `config validate` use
HTTP. Local validation reads policy and resolves a Hub credential source without
network, mount checks or archive writes. `serve` starts the actual writer and
opens its local control state.

Planning and maintenance previews preserve archived content but are keyed jobs
that write operation receipts. Planning and both diagnostic modes contact the
Hub; `doctor --read-only` skips archive-write probes and the archive lock. Actual
verification runs in the private offline worker and writes reports/catalog state.
See [API routes](api.md), [client settings](api-client.md) and
[deployment profiles](scripts.md).

The entrypoint is `hfcache = "hfcache.cli:app"`. Terminal JSON results use schema
1. Explicit detach is a separately typed admission receipt; acceptance alone does
not establish completion. Client timeout or interruption stops observation while
accepted work may continue. Preserve the original key and accepted operation ID.

## 1. Invocation shape

```text
hfcache [GLOBAL OPTIONS] COMMAND [SUBCOMMAND] [ARGUMENTS] [OPTIONS]
```

Global options are placed **before** the command:

```text
hfcache --client-config /etc/hfcache/client.toml --json status
```

| Global option | Default | Meaning |
| --- | --- | --- |
| `--config PATH` | `/etc/hfcache/config.toml` | Local policy only for explicit bootstrap validation; an explicit flag means candidate content only for API validate/plan and is rejected by other operational modes |
| `--json` | off | Emit the machine-readable envelope (§4) on stdout and nothing else |
| `--verbose` / `-v` | off | Raises client-local logging to DEBUG; repeatable counts have the same effective level. Does not change server logs, event vocabulary or secret redaction |
| `--quiet` / `-q` | off | Suppress progress and informational output; warnings/errors and safety handles remain on stderr, including with `--json` |
| `--no-color` | auto | Force plain help and human output, including explicit help and forced-color environments; ordinary automatic color follows the terminal |
| `--token-file PATH` | none | Read a Hub token only for `config validate --local`; operational commands use the separate API bearer source |
| `--client-config PATH` | optional `/etc/hfcache/client.toml` | Separate strict API client settings for migrated commands |
| `--api-url URL` | none | Explicit API URL, mutually exclusive with `--api-socket`; overrides the configured endpoint group |
| `--api-socket PATH` | none | Explicit API Unix socket; overrides the configured endpoint group |
| `--api-token-file PATH` | none | Explicit API credential source, distinct from the Hub `--token-file` |
| `--detach` | off | Return separately identified admission after a keyed job's 202 rather than waiting for its terminal result |
| `--idempotency-key KEY` | generated before POST | Deliberate same-route/body retry using an existing nonsecret key; no automatic new-key replay |
| `--wait-timeout SECONDS` | client `wait_timeout` | Finite total observation budget for a submitted job or `operations wait`, not server cancellation or its queue/lock deadline |
| `--expected-client-scope SHA256` | none | Compare-only 64 lowercase hex authority pin before a keyed job, remote `config validate` or `operations lookup/show/wait`; grants no routing, credential or execution authority |

Job-only flags are refused on non-submitting reads/bootstrap; `operations wait`
accepts the wait budget and its own `--after` cursor, while show/lookup submit
nothing. Explicit wait timeout must be finite and in `(0, 86400]` seconds.

`--json` and `--quiet` are compatible. `--json` and `--verbose` are compatible;
verbosity affects stderr logging, never the stdout envelope.

For operational API modes, the default archive configuration path is never loaded.
An explicit `--config` is accepted only for candidate validate/plan, including
when its value happens to equal the legacy default path. Other operational modes
refuse it with an actionable configuration error. Legacy Hub `--token-file` is refused
for every API operation; select `--api-token-file` or client settings instead.
Explicit `config validate --local` remains the Hub-token/bootstrap exception.
Endpoint/source precedence follows [client configuration](api-client.md).


Ordinary event progress is rendered only when both stdout and stderr are terminals
and quiet is off. Event-history gaps, warnings/errors and retained safety handles
remain on stderr on pipes and in quiet mode. Scheduled observation has a separate
bounded notice/terminal-result stream; client verbosity does not change server events.

### 1.1 Selector grammar

Commands that operate on specific repositories accept repeated selectors:

```text
TYPE:ID          model:organization/model-name
TYPE:ID@SHA      model:organization/model-name@0123456789abcdef0123456789abcdef01234567
```

`TYPE` is `model` or `dataset`. `ID` is a two-segment repository identifier.
`SHA` is a full 40-character lowercase commit SHA. Abbreviated SHAs are rejected
(`HFARG001`). A selector naming a repository absent from configuration is
`HFARG004`, except for `status`, `list`, `verify`, `repair`, and `purge`, which
may legitimately address archived repositories no longer configured. `purge`
goes further and refuses a repository that remains configured (`AD-20`).

## 2. Commands

| Command | Archive effects | Purpose |
| --- | --- | --- |
| `serve` | none at startup; admitted jobs can mutate | Foreground server opens private runtime/control state |
| `config validate` | no | Parse and fully validate configuration |
| `archive init` | yes | One-time guarded archive creation |
| `archive init --inspect` | no | Describe a partial or existing initialization |
| `doctor` | temporary health probes; none with `--read-only` | Prove mount, sentinel, permissions, capabilities, capacity, DNS, Hub reachability |
| `plan` | no | Resolve configured revisions and report expected work |
| `sync` | yes | Synchronize all or selected repositories |
| `status` | no | Configured, retained, current, warning, and verification state |
| `list` | no | Archived repositories and revisions |
| `runs list`, `runs show` | no | One authenticated inventory page or one exact durable run report |
| `verify` | report/catalog except `--estimate` | Integrity verification in one of four modes |
| `prune` | yes with `--apply` | Retention cleanup |
| `purge` | yes with `--apply` | Permanently remove unmanaged repositories |
| `recover` | yes with `--apply` | Reconcile unfinished transactions |
| `quarantine` | yes with `--apply` | Remove explicitly selected, proven redundant recovered staging |
| `repair` | yes | Reconstruct and republish a damaged known revision |
| `version` | no | Local or explicit server application/dependency versions |
| `client describe` | no | Validated nonsecret selected client authority through authenticated capability/version reads |
| `operations show`, `operations lookup`, `operations wait` | no | Authenticated observation of existing receipts/results; never submission |

Keyed sync/plan/diagnostic/verification/maintenance jobs write private operation
receipts even when the archive-effects column says no. Planning and both doctor
modes contact the Hub. Metadata reads, synchronous validation, initialization
inspection and verification estimates submit no job. Local exceptions and
remote execution are described above; apply always retains writer-side guards.

### `client describe`

```text
hfcache [CLIENT OPTIONS] client describe
```

This fixed read-only command authenticates to the selected API and requests only
capabilities and version. It creates no operation, reads no client archive or
Hub credential, and exposes no credential file/name/bytes or full settings.
Its successful standard Envelope has command `client describe` and exactly the
metadata fields listed in §4.1. `endpoint` is the canonical selected `unix:`
socket or validated HTTPS URL; an already supported loopback HTTP endpoint is
also represented accurately. Userinfo, query strings and fragments are refused
by client configuration validation. No browser-supplied endpoint is introduced.

`profile_fingerprint` is SHA-256 of canonical sorted compact JSON containing
metadata schema version, canonical endpoint, selected absolute client-settings
path (the default when none was selected), expected archive UUID or null,
authenticated REST credential class, and selected CA-file path or null. These
allowlisted settings distinguish client authority without exposing settings/CA
paths or hashing a whole configuration or any credential source. Actual archive UUID
comes from the validated version response wrapper, or is null when unavailable;
`instance_id` and credential class come from validated authenticated capabilities.
`authority_fingerprint` is SHA-256 of canonical sorted compact JSON containing
`metadata_schema_version`, `profile_fingerprint`, `endpoint`, `credential_class`
and `archive_id`; it excludes `instance_id` so a restart serving the same known
archive can be observed. A caller can supply this fingerprint as the global
`--expected-client-scope` before a keyed submission, remote `config validate`, or
operations lookup/show/wait.
That invocation validates the actual resolved authority using its own same client
before sending the original key/ID or POST. A mismatch or unknown archive UUID
is `HFAPI017` before any target request. A failed metadata response retains its
original Envelope. Other reads, local commands and `client describe` refuse
this option before settings/credential access. Lookup/show still reject an
explicit wait timeout. The pin compares authority; it adds no routing selector,
capability, automatic lookup or replay.
Remote installed/candidate validation stays synchronous, with no idempotency key
or job receipt; `config validate --local` refuses the pin before policy or
credential access.
This metadata describes the selected client authority, not the container image
or Cockpit host; callers must scope those separately.

Job flags and legacy policy/Hub-token options are refused before opening settings
or credentials. Nonzero API Envelopes retain their original command, problems,
identity and classification; transport/authentication/protocol errors retain the
existing client codes. A missing UUID never becomes an inferred archive identity.

### `serve`

```text
hfcache serve [--server-config PATH] [--hub-token-file PATH]
```

Foreground server bootstrap, requiring the `server` installation extra.
`--server-config` defaults to `/etc/hfcache/server.toml`; that separate policy
selects archive configuration, credentials and listeners. A nondefault global
`--config` or any `--token-file` is `HFARG002` before import/bind. Missing server
packages are `HFCFG005`; missing/unreadable server TOML is `HFCFG001`.
The [server contract](server.md) defines startup checks, one application across
Unix/TCP, TLS, locking and shutdown. No Hub access or archive initialization is
performed by startup. Daemon logging uses server policy, not request verbosity.
`--hub-token-file` supplies an explicit server-local Hub credential for development
or a deliberate startup choice, under the installed token-mode/account rules.
It is separate from the rejected global `--token-file` and API bearer sources;
requests cannot select or override it. Without this option, shared commands use
only the installed systemd Hub source or the existing anonymous policy. The
private verification worker receives neither source nor token.

Normal daemon execution writes no success Envelope or other stdout. With
`--json`, classified startup failures retain the schema-1 failure Envelope.
This foreground bootstrap is the narrow exception to operational commands'
one-terminal-envelope discipline; it is outside remote operation parity.

### `config validate`

```text
hfcache [CLIENT OPTIONS] config validate
hfcache [CLIENT OPTIONS] --config CANDIDATE_PATH config validate
hfcache [--config PATH] [--token-file PATH] config validate --local
```

Without explicit archive `--config`, validate installed writer policy through the
API, including its selected installed Hub credential source. It takes no archive
lock/probe or Hub request. The four legacy payload fields stay `config_fingerprint`,
`repositories`, `enabled_repositories` and `token_source`; installed failures retain
the exact classified server Envelope.

An explicit `--config` uploads bounded local TOML content with writer API capability.
Candidate validation resolves no credential and reports `token_source=not-resolved`,
syntax/policy validity separately from authority compatibility, and only mismatch
field names. Valid but incompatible content exits 0 with compatibility false;
valid content with unavailable/invalid installed policy remains valid with unknown
(null) compatibility and `installed_policy_valid=false`. It does not prove Hub
credential availability/account/network validity or authorize planning/install.
Malformed candidate policy retains its classified errors and exit 10.

`--local` is an explicit offline/bootstrap mode that loads local archive TOML and
resolves its explicit Hub token file/systemd source under existing rules. It makes
no API/Hub request, mount check, lock or mutation and is never an automatic fallback.
Local `token_source` remains `token-file`, `systemd-credential` or `none`; required
mode with no credential remains HFARG008. It can validate the writer's bootstrap
policy without an API, but ordinary reader commands never need that file.

### `archive init`

```text
hfcache [CLIENT OPTIONS] archive init --archive-root PATH --confirm [--archive-id UUID]
hfcache [CLIENT OPTIONS] archive init --inspect [--archive-root PATH]
```

| Option | Meaning |
| --- | --- |
| `--archive-root PATH` | Required unless `--inspect` and must equal `storage.archive_root` for initialization; optional inspection restatement only checks the returned writer root |
| `--confirm` | Required for mutation. Without it, authenticated inspection is returned with refusal and no submission |
| `--archive-id UUID` | Optional restatement of the configured writer UUID; must match authenticated inspection (`HFARG002`). When omitted, use only that inspected UUID |
| `--inspect` | API read of the configured writer target; no client archive path is required. Optional `--archive-root` checks the returned root. Mutually exclusive with `--confirm` (`HFARG002`) |

Inspection uses `GET /archive/inspection` and retains the legacy Envelope command
`archive init`. It never stats/opens/probes the client host's archive path. Optional
`--archive-root` is a redundant comparison against the returned root, not a server
path selector. `--inspect` refuses `--confirm` or `--archive-id`; only optional
root restatement is accepted. Explicit archive `--config` and Hub `--token-file`
are refused.
Without `--inspect`, omitting `--archive-root` retains the usage-error exit `2`;
the missing required option does not become a domain exit `10`.
Confirmed initialization uses the fixed API resource with strict root/UUID/
confirmation and the server's disabled-by-default maintenance gate. The CLI obtains
an omitted optional UUID from authenticated inspection; it never invents one or
loads local archive configuration. Without `--confirm`, inspection data is retained
with HFARG003 refusal (or HFMNT014 for an already initialized target), without a
POST. None of this authorizes initializing an existing production archive.
If authenticated inspection itself fails, preserve its exact server Envelope.
Otherwise the no-confirm refusal is a local argument Envelope with local invocation
metadata plus unchanged inspection data, `configured_archive_id` and
`config_fingerprint`; it is not
represented as a server execution result.
Confirmed initialization explicitly refuses a disabled writer maintenance setting
with HFAPI002 before submission. This client precheck does not replace the
server's repeated gate; other missing negotiated capabilities remain HFAPI018.

The confirmed initialization command proves the target is the expected read/write NFS mount, refuses a
pre-existing sentinel or unknown content (`FS-22`), creates the directory
structure with the documented ownership and modes, fsyncs it, writes
`.hfcache-root` last (`FS-23`), and prints the UUID it wrote so the operator can
confirm that configuration and sentinel agree. With `--confirm`, it holds the
common archive lock before a fresh inspection and through creation. It uses its
own initialization checks, without requiring a pre-existing sentinel. Inspection
and no-confirm invocations take no lock (decision 110).

The UUID comes from `storage.archive_id`, which configuration already has to
carry for any command to load. Initialization does not mint a second one:
a sentinel that disagrees with configuration is fatal and never repaired
(`FS-03`), so generating one would deliberately create that state.

The one adoption exception is a single pre-existing **empty** `published/` whose
ownership and mode already match, because TrueNAS requires that directory to
exist before the consumer export can be defined. Ownership is checked against the
archive root's owner rather than against a local uid, because the Mapall writer
export presents NAS-side ids with no local account.

A refusal still reports the target it found, so one invocation answers both why
it stopped and what is there now.

**Exit codes.** `0` on success; `10` for a configuration or option problem,
including the missing `--confirm`; `20` for a mount, content, sentinel, or write
failure. `--inspect` exits `0` when the target is either initializable *or*
already correctly initialized — both are healthy answers — and `20` when it is
neither.

`archive init` is never invoked by a timer, a sync, or a recovery path (`FS-21`).

### `doctor`

```text
hfcache [CLIENT OPTIONS] doctor [--read-only]
```

Probe-enabled diagnostics hold the common archive lock for their checks, using
`sync.lock_wait_seconds`; they do not require a valid sentinel as an entry
precondition. Every diagnostic row remains reportable against uninitialized
storage. `--read-only` takes no lock and runs no write probes (decision 110).

`checks[]` is emitted in this order. The names are normative — automation keys on
them and `status` quotes them — and every current check is reported as pass, fail or skipped for an explicit
prerequisite. Missing prerequisites never certify a capability.

| # | `name` | Proves | Writes | Code on failure |
| --- | --- | --- | --- | --- |
| 1 | `configuration` | Configuration parses and fully validates | no | `HFCFG###` |
| 2 | `archive_root` | The archive root exists and is a directory | no | `HFMNT001`, `HFMNT015` |
| 3 | `mount_point` | It is a mount point distinct from its parent | no | `HFMNT002` |
| 4 | `filesystem_type` | The filesystem is NFS/NFSv4 | no | `HFMNT003` |
| 5 | `mount_writable` | The mount is not read-only | no | `HFMNT004` |
| 6 | `sentinel` | `.hfcache-root` exists and matches `storage.archive_id` | no | `HFMNT005`–`HFMNT007` |
| 7 | `directory_writability` | Create, fsync, rename, and delete succeed under `.store/health/` | **yes** | `HFMNT008` |
| 8 | `staging_filesystem` | Staging and every publication destination share a filesystem | no | `HFMNT009` |
| 9 | `hardlink_capability` | A cache file hardlinks into a published path with the right link count and contents | **yes** | `HFMNT012` |
| 10 | `atomic_directory_rename` | A directory renames atomically within the dataset | **yes** | `HFMNT013` |
| 11 | `reference_replacement` | A small reference file is replaced atomically | **yes** | `HFMNT013` |
| 12 | `free_space` | Free capacity exceeds the configured reserve | no | `HFMNT011` |
| 13 | `credential` | The credential resolved, and from which source | no | `HFARG005`, `HFARG006` |
| 14 | `hub_endpoint` | The endpoint is a well-formed `https://` URL | no | `HFCFG014` |
| 15 | `hub_dns` | The endpoint host resolves | no | `HFHUB001` |
| 16 | `hub_tls` | The endpoint is reachable and its certificate verifies | no | `HFHUB002` |
| 17 | `hub_identity` | The resolved identity matches `expected_account`, when set | no | `HFHUB003` |

Checks 6–11 need an initialized archive. Against a target that has none they
report `skipped` with that as the reason, which is operator state rather than
development state; `archive init` is what changes it. Check 6 is the one that
reports the condition, since the sentinel's absence *is* the condition; the rest
skip on it silently, so one uninitialized archive is one problem rather than six.

Check 12 is deliberately not in that set: `statvfs` on a proven mount answers it,
and an operator sizing a dataset before initializing is exactly who wants the
answer. It also raises `HFWRN005` when capacity clears the reserve but not by
much, which leaves the exit code at `0` (§5.6).

A check whose precondition failed is also `skipped`, with that as its reason:
nothing can be said about the filesystem type of a path that does not exist, and
`pass` is the one answer that would be wrong. The failure that caused it is
already reported as its own check, so it is never restated.

The same ordered checks are what a mutating command's preflight runs, and it
reads a skip differently: `doctor` reports one and still exits `0`, while a
command that is about to write refuses, because it may not assume a check it
never ran would have passed. Every problem found is reported at once.

Writability is proven only by the check-7 probe, never by comparing `st_uid`
against the local service uid — under the Mapall writer export the owner has no
local account. See [storage requirements](storage-requirements.md).

`--read-only` runs only the checks that mutate nothing — every row above whose
`Writes` column is `no` — for use on a mount that must not be touched. It cannot
prove effective writability, hardlink, rename, or ref-replacement capability, and
reports those four as `skipped` with that reason rather than as a pass. Each is a
capability that only performing it demonstrates, so on a mount that must not be
touched they are unknown, and saying so is the honest answer.

Every probe artifact is removed before the command returns, including after a
failed probe. Exits `0` when every check that ran passed, `20` when any check
failed, and `10` for a configuration problem, which stops the command before any
check runs.

### `plan`

```text
hfcache [CLIENT OPTIONS] [--config CANDIDATE_PATH] plan [TYPE:ID ...]
```

Resolves each enabled repository's configured reference to a full commit SHA and
reports, per repository: the resolved SHA, whether it is already retained or
current, the repository's logical size, the estimated new bytes to download, and
the publication bytes projected under the configured `publication_mode`. Takes
no archive lock and changes no archive content; its keyed job writes control receipts.

Three Hub reads per repository run in order:
resolve the reference, enumerate the revision's tree, then cost the download with
a `snapshot_download` dry run against the same private cache a sync would write
to. The dry run creates nothing — not even the cache directory — so this command
answers against an archive that has not been initialized yet, which is exactly
who is asking. A failure at any of the three leaves the fields below it `null`
rather than guessed, and the repository's `upstream_state` records what was
observed.

`projected_publication_bytes` is `0` under `publication_mode = "hardlink"`, since
a hardlink points at a cache blob already on the dataset; under `"copy"` it is the
logical size, because copy mode writes another ordinary-file copy (`AD-11`).
Physical allocation still depends on filesystem compression/deduplication. The mode is reported beside it so the zero is explicable, and a
deployment weighing the switch reads the copy-mode figure off `logical_bytes`.

This is the command run before enabling a large repository, and its output is what
the dataset quota is sized from.

### `sync`

```text
hfcache [CLIENT OPTIONS] sync [TYPE:ID ...]
```

The scheduled command. With no selectors it processes every enabled repository in
deterministic configuration order; with selectors it restricts the run to those.

Sequence, locking and preflight first, then the run journal and reconciliation,
then per repository: resolve, skip or move the reference if the SHA is already
retained, estimate and check capacity, download, check completeness locally, hash
new unique content, detect dependencies, write the manifest, build staging, rename
it into place, publish the manifest, publish the per-SHA reference, replace
`current.json`, rebuild the catalog, apply retention.

With repository-error continuation enabled, resolution, estimation, and an
aggregate capacity gate cover the selected queue before its first download.
One background repository transfer may then run ahead while the main thread
hashes and publishes earlier completed snapshots; both transfer and publication
remain in configuration order, and the command drains the producer before
returning. Retention is applied after every downloaded snapshot has been
consumed, so its whole-cache scan cannot remove a queued revision with the same
commit SHA in another repository. Stop-on-error mode retains the fully serial
sequence.

Reconciliation happens under the lock and **before the first Hub request**
(`TX-07`): unfinished transaction journals are resolved, and one that asked for an
operator stops the run at `20` with nothing downloaded and nothing changed. The
same applies to `prune --apply`, `purge --apply`, and `repair`, which are mutating
commands too.
`status`, `list`, `verify`, and `recover --dry-run` still answer in that state.

Exits `0`, `10`, `20`, `30`, `40`, or `50` per §3.

### `status`

```text
hfcache [CLIENT OPTIONS] status [TYPE:ID ...]
```

Per repository: configured or unmanaged, enabled state, current SHA and
generation, retained revision count and generations, upstream state, outstanding
warnings, last run status, and verification state. Also reports archive-level
health: free space against reserve, outstanding verification failures, unfinished
transactions, over-retention, and deferred cleanup.

`status` is the command an operator runs first, so it never fails merely because
the Hub is unreachable — it reports local truth and marks upstream state
`unknown`.

Status emits configured repositories in configuration order, then unmanaged
published repositories in canonical `(type, id)` order. An explicit selector
restricts the configured/published union; one absent from both is `HFARG004`.
For an unmanaged status row, `managed` is false and configuration-only values
are null.

### `list`

```text
hfcache [CLIENT OPTIONS] list [--type model|dataset] [--revisions] [TYPE:ID ...]
```

Archived repositories, and with `--revisions` every retained revision with its
generation, publication ID, size, publication timestamp, and verification state.
Reads only manifests and references, so it works on an archive whose catalog is
missing or corrupt.

### `runs list` and `runs show`

Read durable run reports through authenticated REST without a client archive
mount. `runs list [--limit N] [--cursor TOKEN]` requests exactly one page of
run IDs; default min(100, authenticated server page limit), range 1–10,000,
further bounded by server/client limits.
`runs show [--] RUN_ID` reads one exact 32-character lowercase hexadecimal domain
run ID. IDs are neither
filenames nor operation handles. No argument is a path, URL or method. These
commands create no receipt, acquire no archive lock and accept no job/candidate/
local-bootstrap mode. Missing/corrupt reports, stale cursors, identity and resource
refusals retain classified errors; no empty-success or local fallback follows.

Under `--json`, stdout is the exact original server schema-1 Envelope. List
command is `runs`, with `data.runs` containing IDs; detail is `runs read`, with
`data.report` containing the durable report and Envelope.run_id matching it.
Historical report policy identity remains historical.

Before each successful read's Envelope, stderr emits exactly one compact line
`Run read metadata: JSON`, even in quiet mode. The complete prefixed line is at most
2 KiB (excluding its newline) and JSON has exactly
`schema_version:1`, `command`, `run_id`, `request_id`, `archive_id`,
`config_fingerprint`, `next_cursor`. It contains validated wrapper identity and
the opaque next cursor (null on the last page and all detail reads). It grants no
execution authority and is not an operation receipt. Preserve the cursor exactly
for an explicit next-page request; do not infer total inventory or silently
restart a stale cursor. Successful reads require nonnull archive/policy identity.
Failures need no metadata line and preserve their original Envelope. Unknown,
unsafe or secret-bearing metadata refuses before output.

### `verify`

```text
hfcache [CLIENT OPTIONS] verify --new [--run-id ID]
hfcache [CLIENT OPTIONS] verify --full
hfcache [CLIENT OPTIONS] verify --revision TYPE:ID@SHA
hfcache [CLIENT OPTIONS] verify --estimate
```

Exactly one mode option is required; two is `HFARG002`.

| Mode | Scope |
| --- | --- |
| `--new` | Content introduced by one run. Defaults to the most recent run report in `runs/`; `--run-id` selects another |
| `--full` | Every retained revision reachable from `refs/revisions/<sha>.json`. The quarterly job |
| `--revision` | One retained revision |
| `--estimate` | No hashing. Reports unique bytes to read, measured throughput when known, estimated duration, repository and revision counts, and any detectable overlap with storage maintenance. Takes no lock; the estimate itself makes no integrity finding. Transport/configuration/metadata refusals can still fail |

Every non-estimate mode acquires the common archive lock, using
`verification.lock_wait_seconds`, then passes storage mount/sentinel/capability
preflight before resolving its target scope. It holds ownership through hashing,
report write and the catalog read/merge/write. It is mutually exclusive with all
archive writers; a storage-preflight refusal exits `20` before report creation.
Target reference/manifest damage still produces verification findings. Estimates
take no lock, hash nothing and persist nothing. Every mode structurally constructs
no Hub client or credential and makes no process-environment change. The shipped
verification unit additionally supplies `HF_HUB_OFFLINE=1` and denies IP sockets;
the shared service alone does not claim an operating-system egress restriction.
See [decision 110](adr/decision-110.md) and the
[offline isolation rationale](adr/decision-111.md). The private REST executor
owns hashing and persistence under its native/rootless confinement; installed
enforcement requires actual executor acceptance.
The shared service must not toggle the ASGI process's offline flag.

Exits `0` on a clean result and `40` on any integrity finding. A finding never
rewrites a manifest, prunes a revision, or re-downloads over the evidence.

### `prune`

```text
hfcache [CLIENT OPTIONS] prune --dry-run [TYPE:ID ...]
hfcache [CLIENT OPTIONS] prune --apply [TYPE:ID ...]
```

Exactly one of `--dry-run` / `--apply` is required. `--dry-run` prints the exact
`PrunePlan` that `--apply` would execute and mutates nothing.

Retention normally runs inside `sync`; this command also inspects the plan,
completes retention deferred by an earlier failure, and applies a lower
`storage.maximum_revisions`. Each invocation removes at most one eligible
revision per selected repository; after lowering a limit, review and repeat
until no eligible excess remains.

### `purge`

```text
hfcache [CLIENT OPTIONS] purge --dry-run TYPE:ID [TYPE:ID ...]
hfcache [CLIENT OPTIONS] purge --apply TYPE:ID [TYPE:ID ...]
hfcache [CLIENT OPTIONS] purge --dry-run --all-unmanaged
hfcache [CLIENT OPTIONS] purge --apply --all-unmanaged
```

Exactly one of `--dry-run` / `--apply` is required, and scope must be either one
or more whole-repository selectors or `--all-unmanaged`, never both. No scope is
`HFARG003`; a revision-qualified selector is `HFARG001`; a target still present
in configuration is `HFARG007`. `--dry-run` prints the exact `PurgePlan` and
logical-byte estimate without taking the writer lock. `--apply` re-resolves the
scope and plan under the exclusive lock after recovery, then removes one
repository transaction at a time. It never contacts the Hub and never deletes a
cache path directly (`FS-14`).

Purge validates every shallow entry under the repository's `refs/`,
`revisions/`, and manifest directories. Anything not explained by active
references and immutable manifests refuses that repository with `HFRET001` and
is preserved (`FS-19`). A completed purge removes publication content and cache
revisions but retains byte-for-byte manifests and reason records under
`audit/pruned/`. ZFS snapshots may continue holding physical blocks after the
command succeeds.

### `recover`

```text
hfcache [CLIENT OPTIONS] recover --dry-run
hfcache [CLIENT OPTIONS] recover --apply
```

Reconciles unfinished transaction journals: abandoned staging, a renamed tree not
yet in the catalog, a missing or corrupt catalog, a reference repairable from
unambiguous evidence, an interrupted prune rolled back or forward from its
tombstone, and an interrupted repair finished at its reference switch.

`--dry-run` mutates nothing and exits `0` when it can describe a complete plan,
or `20` when it finds state that requires an operator. `--apply` executes only a
fully validated plan and is idempotent — running it twice is harmless.

Recovery is roll-forward oriented. It never replaces an expected digest, chooses a
revision by modification time, or deletes unknown data (`AD-16`).

### `quarantine`

```text
hfcache [CLIENT OPTIONS] quarantine --dry-run TRANSACTION_ID ...
hfcache [CLIENT OPTIONS] quarantine --apply TRANSACTION_ID ...
```

Exactly one mode and at least one explicit 32-character lowercase hexadecimal
transaction ID are required. These arguments identify quarantine entries rather
than repositories. There is no implicit all-entries mode.

Only staging quarantined by a completed recovery of a failed, unpublished
publication is eligible (`docs/architecture.md` §7.8.1). Empty directories may
be removed. Files may be removed only after both they and their same-path current
published copies verify against the current retained manifest. Repair quarantine,
unique content, unknown entries, symlinks, inconsistent evidence, or unfinished
transactions refuse the operation. Plans validate the complete requested set
before any removal; apply revalidates under the writer lock. An interrupted
cleanup is safely repeatable, and original transaction journals and published
content are preserved. No Hub request is made.

### `repair`

```text
hfcache [CLIENT OPTIONS] repair TYPE:ID@SHA [--reason TEXT]
```

Downloads the exact SHA into an isolated `.store/repair/<transaction-id>/hub`,
verifies every file against the **original** manifest, publishes a replacement
instance with a new publication ID and the SHA's original generation, reverifies
the new tree, and only then switches `refs/revisions/<sha>.json` and, if
applicable, `refs/current.json`. The superseded instance stays readable at its
original locator for the configured grace period.

If any expected digest differs from the original manifest, the command stops
without changing the published revision (`AD-13`).

### `version`

```text
hfcache [CLIENT OPTIONS] version [--server]
```

Without `--server`, report local application, Python, `huggingface_hub` and
resolved transfer-backend versions without reading configuration or accessing the
archive/API. This remains usable on a broken deployment. `--server` instead
authenticates to the selected API and preserves the writer's exact version
Envelope, including its invocation identity and timestamps.

### `operations`

```text
hfcache [CLIENT OPTIONS] operations show OPERATION_ID
hfcache [CLIENT OPTIONS] operations lookup -- 'IDEMPOTENCY_KEY'
hfcache [CLIENT OPTIONS] [--wait-timeout SECONDS] operations wait [--after N] -- 'OPERATION_ID'
```

These commands authenticate and observe existing work; they never POST, cancel
or replay it. `show` and `lookup` render the exact server schema-1 metadata
Envelopes, with canonical commands `operations show` / `operations lookup` and
typed `data.operation`. A receipt's state is metadata, not a new domain result.
All REST readers/writers may inspect operation IDs, while key lookup searches
only the caller's credential-class namespace. Credential rotation preserves that
coarse namespace; switching classes does not. Missing/expired HFAPI013 history
does not prove nonexecution.

Keep the positional `--` before a copied key. Both fixed rootless launcher hops
honor that delimiter: `--help`/`-h` after it are literal lookup keys, while help
before it remains static and requires no installed profile or credentials.

`wait` observes bounded sanitized sequenced events, status and result under one
absolute finite deadline. `--after N` resumes event observation after that sequence;
retention gaps are explicit, never invented events. Event observation omits a
fixed requested page limit so the server chooses its adaptive default, including
small configured page/event caps. Drain consecutive retained pages through the
final empty page under the same observation deadline; that empty page counts
toward the drain's max_pages. Explicit library event limits retain their
validation. No new capability request, replay or cancellation is introduced. On a terminal result, emit
the exact stored command Envelope and its application exit, including partial
failure. On known unfinished/interrupted work with no terminal Envelope, preserve
HFAPI015 rather than fabricate an execution result.

Keyed jobs wait by default, including planning, diagnostics and maintenance
previews. Before their first POST, validate/generate the nonsecret key and print
it to stderr; after a validated 202 print operation ID before waiting. Both
messages are mandatory even in quiet mode. Sanitized event progress stays on
stderr and requires both streams to be terminals with quiet off; no raw journald
output is forwarded. Gap notices and safety handles are diagnostics in every mode. Distinct
request/operation/domain IDs retain their separate meanings.
Event rendering escapes nonprintable characters, including newline/ESC, so each
event stays one plain stderr line. Quiet and nonterminal output suppress ordinary progress rendering.

Explicit global `--detach` stops after admission. In JSON mode it emits exactly
one object with these fields, separately from the terminal Envelope family:

| Field | Detached submission value |
| --- | --- |
| `schema_version` | Integer `1` |
| `kind` | `operation_admission` |
| `idempotency_key` | Validated original nonsecret key |
| `acceptance` | Exact validated server `AcceptanceResponse`, including operation and same-operation observation links |

It has no fabricated `outcome` or `exit_code`; successful detachment means only
durable admission. Human detach output likewise identifies admission and its
handles. `--idempotency-key` supports a deliberate identical request retry; it
does not bypass current authentication or the initialization maintenance gate.
Keys use 1–128 ASCII letters/digits or `._~+-`; values recognized as secrets or
containing a registered credential are refused before they can become handles.

Observation timeout or Ctrl-C while waiting is HFAPI019 / exit 20 and retains original key,
operation ID and route when known. Lost/unusable POST acknowledgement remains
HFAPI020 / exit 20 with the original key/route, including interruption before
acknowledgement is established. Other validated transport/protocol/
remote refusals retain their taxonomy and known handles. State that accepted work
may continue and reconnect through lookup/show/wait; never automatically replay,
cancel, change keys or render observer failure as a terminal server result.
Validated 5xx refusals with a retained key also say work may continue; a usable
error acknowledgement can still follow durable admission.
The observation deadline differs from HTTP connect/read limits and the server's
queue/lock budget. Stopping a client process/service stops observation only.
See [recovery](recovery.md#preserve-four-kinds-of-authority) and
[decision 120](adr/decision-120.md).

**Scheduled observation:** the fixed internal
`python -m hfcache.scheduled_client` entrypoint repeats finite observations for
multi-hour systemd oneshots. It retains a strict private key/operation handle;
existing history only permits lookup/observation and never POST replay. This does
not make ordinary CLI waits unbounded or add a public execution route. See
[scheduled service contract](api-client.md#scheduled-service-observation),
[schema§14](schemas.md) and
[decision 121](adr/decision-121.md).

## 3. Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success, including non-fatal dependency warnings |
| `10` | Invalid configuration or invocation precondition |
| `20` | Mount, sentinel, permission, capacity, lock, unresolvable transaction, or unavailable/internal management-service safety failure |
| `30` | One or more repository sync failures |
| `40` | Integrity verification failure |
| `50` | Prune, repair, or recovery-apply failure |

These deliberately avoid `1` and `2`, which Typer uses for usage errors, so a
scheduler can distinguish a malformed command line from an application outcome.

**Aggregation.** Codes `10` and `20` abort before per-repository work begins, so
they never co-occur with the others. Among `30`, `40`, and `50`, which can all
arise in one run, the reported code is the first of `40`, `50`, `30` that
occurred — ordered by operator urgency: possible data corruption, then degraded
retention, then stale content. Every classification encountered is listed in the
envelope's `errors` array regardless of which one becomes the exit code, so
nothing is hidden by aggregation.

A run that continues past an individual repository failure still exits non-zero,
so systemd records the unit as failed.

## 4. JSON output

`--json` writes exactly one envelope to stdout. Human-readable text goes to
stdout only without `--json`; logs and progress always go to stderr. This means
`hfcache --json sync | jq` is always safe.
Explicit `--detach` is a separate output contract: one identified admission object
as specified above, with no terminal command-success claim. It must be selected
deliberately; default command and operation-wait output remain exact Envelopes.
The long-lived `serve` bootstrap writes no terminal success envelope; only its
classified startup failure is rendered under `--json`, as specified above.

```json
{
  "command": "sync",
  "completed_at": "2026-07-24T20:41:46.002000Z",
  "data": {},
  "errors": [],
  "exit_code": 0,
  "outcome": "success",
  "run_id": "4c1e8a55b0d24f1e9a3c7d2b6f80e114",
  "schema_version": 1,
  "started_at": "2026-07-24T20:38:11.500000Z",
  "warnings": []
}
```

| Field | Notes |
| --- | --- |
| `schema_version` | `1`; independent of the durable schema versions in `docs/schemas.md` |
| `command` | Full command path, e.g. `sync`, `archive init`, `verify --full` |
| `run_id` | Correlates the envelope with the durable run report and every log line |
| `outcome` | `success` \| `success_with_warnings` \| `failed`; always agrees with `exit_code`; a failed envelope may also retain warnings |
| `data` | Command-specific payload (§4.1) |
| `warnings`, `errors` | Arrays of `{ "code", "repository", "message", "context" }`; `repository` is `null` for archive-level entries |

The envelope is emitted even on failure, including for configuration errors, so
automation never has to parse human text to learn what went wrong.

Serialization follows the same deterministic rules as durable files
(`docs/schemas.md` §1): sorted keys, UTF-8, trailing newline.

### 4.1 `data` payloads

| Command | `data` contains |
| --- | --- |
| `config validate` | Installed/local: `config_fingerprint`, `repositories`, `enabled_repositories`, `token_source`. Candidate: validity/compatibility flags and safe mismatch names as specified above; valid candidates also retain the four legacy fields with `token_source="not-resolved"` |
| `archive init` | `archive_id`, `archive_root`, `created_directories`, `removed_temporaries`, `sentinel`, `adopted_published`. With `--inspect`, or on a refusal: `state`, `initializable`, `mount`, `existing_directories`, `missing_directories`, `unknown_entries`, `unknown_entry_count`, `leftover_temporaries`, `adopted_published`, `archive_id`, `archive_root` |
| `doctor` | `checks[]` of `{ name, outcome, detail }`, in execution order |
| `plan` | `repositories[]` of `enabled`, `repository_type`, `repository_id`, `requested_revision`, `resolved_commit_sha`, `upstream_state`, `file_count`, `logical_bytes`, `estimated_new_bytes`, `projected_publication_bytes`, `publication_mode`, plus retained/current state |
| `sync` | The `RunReport` body (`docs/schemas.md` §6) |
| `status` | Archive health block plus per-repository state |
| `list` | `repositories[]`, with `revisions[]` when `--revisions` is given |
| `verify` | The `VerificationReport` body (`docs/schemas.md` §7). For `--estimate`, which produces no report because it verifies nothing: `mode`, `repositories`, `revisions`, `unique_objects`, `unique_bytes`, `unreadable_objects`, `measured_throughput_bytes_per_second`, `estimated_duration_seconds`, `storage_maintenance` |
| `prune` | The `PrunePlan`, plus applied results for `--apply` |
| `purge` | `plans[]` of `PurgePlan`, plus `applied[]` audit records for `--apply` |
| `recover` | `findings[]`, `plan[]`, and applied results for `--apply` |
| `quarantine` | Explicit transaction cleanup plans and applied results; published content and original journals remain unchanged |
| `repair` | Transaction ID, old and new publication IDs, verification result, grace expiry |
| `version` | `application`, `python`, `huggingface_hub`, `transfer_backend` |
| `client describe` | Exactly `metadata_schema_version=1`, `profile_fingerprint` and `authority_fingerprint` (64 lowercase hex each), canonical `endpoint`, authenticated `credential_class` (`rest-reader` or `rest-writer`), `archive_id` (canonical UUID or null), `instance_id` (32 lowercase hex) |
| `operations show`, `operations lookup` | `operation`: validated metadata receipt, without internal digests or raw key; command remains the server metadata command |

## 5. Error and warning taxonomy

Codes are stable across releases. A code is never reused for a different
condition; a retired condition retires its code.

### 5.1 Configuration and invocation — exit `10`

`HFCFG001`–`HFCFG016` are enumerated in `docs/configuration.md` §8.

| Code | Condition |
| --- | --- |
| `HFARG001` | Malformed selector, or an abbreviated commit SHA |
| `HFARG002` | Mutually exclusive options given together, or an option that contradicts configuration — `--token-file` with `hub.token_mode = "disabled"` |
| `HFARG003` | A required option is missing, such as `archive init` without `--confirm` |
| `HFARG004` | An argument names something the archive does not hold, for a command that requires it: a repository absent from configuration, a revision that is not retained, or a run id with no report |
| `HFARG005` | `--token-file` is missing, unreadable, empty, not a regular file, or does not hold a single well-formed token |
| `HFARG006` | The systemd credential named by `hub.credential_name` is present but unusable, or `$CREDENTIALS_DIRECTORY` is not an absolute path |
| `HFARG007` | A `purge` target remains in configuration; remove it from configuration before archive deletion |
| `HFARG008` | `hub.token_mode = "required"` resolved neither an explicit token file nor the named systemd credential |
| `HFAPI001` | API bearer is missing, malformed, invalid or belongs to the wrong interface; HTTP 401 with a Bearer challenge |
| `HFAPI002` | An authenticated API principal lacks the required capability; HTTP 403 |
| `HFAPI003` | A configured API credential source is missing, unsafe, changes while read or contains a malformed token |
| `HFAPI004` | The same API credential value is assigned to more than one capability class |
| `HFAPI006` | Invalid API request or exceeded request/response bound; HTTP 422 or 413 |
| `HFAPI007` | API resource/method is absent (HTTP 404/405), a page cursor is stale (HTTP 409), or admitted policy changed before execution |
| `HFAPI010` | API Host/Origin/TLS/proxy security policy refuses a request; HTTP 400 or 403 |
| `HFAPI012` | An idempotency key conflicts with its previously admitted route/request; HTTP 409 |
| `HFAPI017` | Client configuration or endpoint/source selection is invalid |
| `HFAPI018` | API response/protocol, identity, capability or version is unsupported/inconsistent |

The `HFAPI` family defaults to exit `10`; the explicit safety codes below exit
`20` ([decisions 113](adr/decision-113.md), [114](adr/decision-114.md) and
[118](adr/decision-118.md)). HTTP status describes the transport
result and does not override a domain Envelope's application exit classification.

### 5.2 Storage and transaction safety — exit `20`

| Code | Condition |
| --- | --- |
| `HFMNT001` | Archive root does not exist |
| `HFMNT002` | Archive root is not a mount point distinct from its parent |
| `HFMNT003` | Filesystem type is not NFS/NFSv4 |
| `HFMNT004` | Mount is read-only |
| `HFMNT005` | Sentinel `.hfcache-root` missing |
| `HFMNT006` | Sentinel malformed or of an unsupported schema version |
| `HFMNT007` | Sentinel `archive_id` does not match configuration |
| `HFMNT008` | A required directory is missing or failed the effective-write probe |
| `HFMNT009` | Staging and destination are on different filesystems |
| `HFMNT010` | Exclusive lock not acquired within `lock_wait_seconds` |
| `HFMNT011` | Free capacity below estimated need plus reserve |
| `HFMNT012` | Hardlink capability unavailable while `publication_mode = "hardlink"` |
| `HFMNT013` | Atomic directory rename or atomic ref replacement unavailable |
| `HFMNT014` | Initialization target already initialized, non-empty, or unknown |
| `HFMNT015` | Symlink or unexpected file type at an application-owned path |
| `HFTXN001` | Transaction journal of an unknown schema version |
| `HFTXN002` | Checkpoint combination that no valid execution can produce |
| `HFTXN003` | Journal evidence contradicts the filesystem |
| `HFTXN004` | Recovery state is ambiguous; an operator must decide |
| `HFAPI005` | Metadata query cannot complete within its configured work/byte budget; HTTP 503 |
| `HFAPI008` | Unexpected internal API failure, with sanitized diagnostics; HTTP 500 |
| `HFAPI009` | Metadata service is full, draining or unavailable; HTTP 503 |
| `HFAPI011` | Daemon instance lock is unsafe, unavailable or already held; HTTP 503 classification |
| `HFAPI013` | Operation history/result is missing or expired; execution outcome remains unknown; HTTP 404 |
| `HFAPI014` | Operation control storage or scheduled observation handle is unsafe, full, unavailable, unsupported, mismatched or unexplained; HTTP storage refusal 503, local handle refusal exit 20 |
| `HFAPI015` | Operation state/transition or result availability is invalid or uncertain; HTTP 409 |
| `HFAPI016` | Isolated verification executor is unavailable, unsafe or fails protocol/peer validation; HTTP 503 |
| `HFAPI019` | API connectivity or bounded observation cannot complete |
| `HFAPI020` | Submission outcome is uncertain; retain the original key and do not replay under a new key |

### 5.3 Hub and synchronization — exit `30`

| Code | Condition |
| --- | --- |
| `HFHUB001` | Endpoint unreachable or DNS failure |
| `HFHUB002` | TLS verification failure |
| `HFHUB003` | Resolved identity does not match `expected_account` |
| `HFHUB004` | Repository not found (`404`) |
| `HFHUB005` | Access forbidden (`403`) |
| `HFHUB006` | Repository is private or gated while `token_mode` is `disabled` or `optional`; restricted scope was not explicitly enabled |
| `HFHUB007` | Configured revision could not be resolved to a commit SHA |
| `HFHUB008` | Repository tree metadata missing or incomplete |
| `HFHUB009` | Snapshot download failed |
| `HFHUB010` | Rate limited after the built-in retry budget was exhausted |
| `HFSYN001` | Local-only completeness check failed after download |
| `HFSYN002` | Downloaded path set does not match Hub tree metadata |
| `HFSYN003` | File size does not match Hub metadata during ingestion |
| `HFSYN004` | Unsafe path rejected: traversal, escape, symlink, or non-regular file |
| `HFSYN005` | Staging tree construction failed |
| `HFSYN006` | Publication rename failed |
| `HFSYN007` | Reference publication failed |
| `HFSYN008` | Manifest write failed |
| `HFSYN009` | Newly introduced content could not be read for hashing |

`HFHUB004`, `HFHUB005`, and `HFHUB001` mark the repository's `upstream_state` and
preserve every local revision. They never trigger a prune (`AD-06`).

`HFSYN003` is an ingestion-time size mismatch and prevents publication, so it is a
sync failure. The same physical symptom found later by `verify` is `HFVER002`, an
integrity failure — the distinction is whether the bytes ever became a published
revision.

### 5.4 Integrity — exit `40`

| Code | Condition |
| --- | --- |
| `HFVER001` | SHA-256 digest mismatch against the manifest |
| `HFVER002` | Size mismatch against the manifest |
| `HFVER003` | Manifest path missing from the publication tree |
| `HFVER004` | Publication tree contains a path the manifest does not list |
| `HFVER005` | Manifest path is not a regular file |
| `HFVER006` | Object could not be read |
| `HFVER007` | Manifest or selected supplemental metadata fails schema, identity or internal consistency validation |
| `HFVER008` | Reference names a missing or inconsistent tree or manifest, or a current reference that cannot be read |

### 5.5 Retention, purge, repair, and recovery — exit `50`

| Code | Condition |
| --- | --- |
| `HFRET001` | A retention or purge plan is invalid or refused by validation |
| `HFRET002` | Hub cache revision deletion failed |
| `HFRET003` | Tombstone rename into `.store/trash` failed |
| `HFRET004` | Catalog or reference update failed during prune |
| `HFRET005` | Pre-commit rollback failed; removed revision content could not be restored |
| `HFRET006` | Repair download failed verification against the original manifest |
| `HFRET007` | Repair publication failed |
| `HFRET008` | Repair reference switch failed |
| `HFRET009` | Post-grace cleanup failed |
| `HFRET010` | Post-commit audit cleanup, recovery, or explicit quarantine cleanup could not validate or complete its plan |

### 5.6 Warnings — never change a `0` exit on their own

| Code | Condition |
| --- | --- |
| `HFDEP001` | An undeclared dependency was detected in repository metadata |
| `HFWRN001` | Temporary over-retention: published revisions exceed the configured limit |
| `HFWRN002` | Deferred physical cleanup: logical prune committed, trash removal outstanding |
| `HFWRN003` | Unknown files present in an application-owned area; preserved, not deleted |
| `HFWRN004` | Stale staging directory detected |
| `HFWRN005` | Free space approaching the configured reserve |
| `HFWRN006` | Upstream repository unreachable; all local revisions preserved |
| `HFWRN007` | Archived repository is not present in configuration |
| `HFWRN008` | A retired repair instance is past its grace period and awaits cleanup |
| `HFWRN009` | Local Xet transfer cache exceeded its advisory ceiling |
| `HFWRN010` | Verification window may overlap detected storage maintenance |
| `HFWRN011` | Supplemental discovery extraction is partial, unsupported or failed; publication integrity is unchanged |

`HFDEP001` marks the repository `completed_with_warnings`, is written to the
manifest and the run report, is surfaced by `status`, and leaves the exit code at
`0` when nothing else failed (`AD-07`).

## 6. Output discipline

- Tokens, `Authorization` headers, signed URLs, and credential file contents are
  never printed, logged, or written to any durable artifact — at any verbosity.
- Error messages name the *shape* of a secret problem, never the value: a token
  found in configuration is reported by key path, not by content.
- Credential loaders register accepted secret values before use, including
  opaque values without an `hf_` prefix. Shared diagnostic sanitization covers
  nested keys/values, `Problem` output and exception string/repr paths; output
  sanitizes again if a secret was registered after a problem was constructed.
- Log events are structured, carry the `run_id`, use stable event names
  (`run.started`, `repository.resolved`, `download.completed`,
  `dependency.undeclared`, `publication.completed`, `retention.pruned`,
  `run.completed`, and the closed event vocabulary below), and record durable
  checkpoints rather than per-chunk progress. The vocabulary is closed:
  `hfcache.logging.EVENTS` is the whole of it, and emitting a name outside it
  raises rather than writing a line no filter will match. The stable
  warning `mcp.diagnostic` records bounded sanitized SDK warning/error diagnostics;
  lower SDK levels are suppressed, `sdk_level` retains original severity and
  `sdk_logger` is bounded/sanitized. Diagnostic text is fixed; SDK messages,
  arguments and exceptions are never formatted into it. It is operational evidence, not a domain
  checkpoint/outcome; [decision 124](adr/decision-124.md) amends decision 64.
- The format is logfmt on **stderr** — `event=… level=… run_id=… key=value`,
  keys sorted after the first three, values quoted only when they would
  otherwise be ambiguous. Under systemd each line carries a `<N>` syslog prefix,
  which journald turns into `PRIORITY`, so `journalctl -p err -u
  hfcache-sync.service` selects failures; run by hand there is no prefix.
- Run correlation is scoped to execution contexts and captured when an event
  is emitted. Optional server-generated request/operation IDs join the run ID;
  call-site fields cannot override them. Worker submissions explicitly copy
  their context, including the sync download producer, and restore the worker's
  previous scope on return or failure. See [decision 111](adr/decision-111.md).
- Levels follow the options: `--quiet` is `WARNING`, the default is `INFO`, and
  `-v` is `DEBUG`. The §24 families are emitted at the default level rather than
  behind a flag, because they are the record an unattended run leaves and the
  systemd units pass no flags.
- That per-invocation configuration is for the isolated CLI. A daemon configures
  its handler and level once at startup; a client's quiet/verbose preference
  affects rendering/event selection and cannot reconfigure the server logger.
- Absolute filesystem paths are printed for operator commands, but every path
  written into a durable artifact is archive-relative (`docs/schemas.md` §1).

### Closed operational event vocabulary

Default INFO logging records durable progress without per-chunk noise. Events
carry the domain run ID, with context-scoped request/operation correlation when
available. Operational totals include downloaded, logical, reused and newly
stored bytes, hash throughput and retention results; warnings are visible in
status. The stable event names are:

`run.started`, `preflight.failed`, `repository.resolved`, `repository.skipped`,
`repository.queued`, `download.started`, `download.completed`, `hash.started`,
`hash.completed`, `verification.completed`,
`dependency.undeclared`, `publication.completed`, `retention.pruned`,
`retention.deferred`, `quarantine.cleaned`, `repository.failed`, `run.completed`,
`mcp.diagnostic`, `catalog.capture_incomplete`.

`catalog.capture_incomplete` emits the bounded `HFWRN011` warning after optional
supplemental capture fails or produces incomplete evidence. Successful
publication and repair integrity outcomes remain authoritative.

The MCP diagnostic bridge emits only sanitized bounded warning/error provenance,
never SDK message arguments, raw exceptions or tracebacks. Debug-only events are
separate and may evolve. Never log secrets, bearer headers or signed URLs.

## Catalog discovery

`search [filters]` reads repository hits; `tags [filters]` lists the tag facet.
Both use only REST and collect every bounded page before rendering. Filters are
`--type model|dataset`, `--query TEXT`, repeated `--tag TAG` (ALL), repeated
`--any-tag TAG` (ANY), `--tag-source current_or_last_observed|current_only`,
`--scope archived|configured|all`, `--revision-scope current|retained`, `--format`,
`--quantization`, `--quantization-method`, `--bits`, `--max-variant-bytes` and
`--page-size`. Defaults match the [catalog contract](discovery.md). Model-only
predicates cannot be combined with explicit dataset type. Cursors are SDK-only;
the CLI requires complete collection and fails on an unfinished or stale walk.

`catalog show TYPE:ID` reads detail; `catalog variants TYPE:ID` collects the full
model variant set. Revision scope defaults current, with optional paired
`--commit-sha` and `--publication-id` selecting an exact retained publication.
Variants also accepts `--page-size`. Human output labels current/historical/unknown
tags, incomplete coverage and the representative's exact publication. Dataset
summaries show observed formats and declarations without inventing model variants.
Nonprintable archive text is escaped; it never executes or becomes terminal control.

`catalog refresh [TYPE:ID ...]` is a writer-only keyed offline operation. Optional
`--tags-only` and `--technical-only` are mutually exclusive; default refreshes both.
Revision scope defaults retained. Existing global `--idempotency-key`, `--detach`
and `--wait-timeout` semantics apply. A new capture needs a new key; observation
never resubmits. JSON retains exact server Envelopes and evidence; complete page
assembly changes only entries, retaining the first Envelope's identity/times.
Quiet retains warnings, errors and uncertainty handles. API unavailability never
falls back to an archive mount, local Hub source or model runtime.
