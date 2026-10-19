# hfcache Configuration Contract

| Field | Value |
| --- | --- |
| Status | Normative contract for implementation |
| Schema version | `1` |
| Default location | `/etc/hfcache/config.toml` |

Configuration is TOML, parsed with `tomllib`, and validated into strict, frozen
Pydantic models. It is the complete statement of operator intent. Everything it
describes is validated **before** any network request or filesystem mutation, so
an invalid configuration can never partially apply.

Archive policy determines repository/storage intent. Server TOML separately
owns restart-only transport, credential classes and budgets; client TOML owns
independent endpoints, trust and REST sources. The protected rendered rootless
runtime/release profile is a fourth domain, not extra archive policy keys.
Candidate syntax validity and installed-authority compatibility remain distinct.
See [server](server.md), [client](api-client.md) and [runtime](containers.md).

## 1. Validation rules that apply to every field

- **Unknown keys are rejected.** Every model uses `extra="forbid"`. A typo is an
  error, never a silently ignored setting.
- **Types are strict.** Pydantic strict mode is enabled; `"4"` is not an integer
  and `1` is not a boolean. TOML already distinguishes these, so a type error
  always means the operator wrote the wrong thing.
- **Models are frozen.** Each loaded configuration snapshot is immutable; no
  code path mutates it. Explicit local validation keeps one snapshot for its invocation.
  A long-lived server freezes archive policy afresh for each request/admission,
  while server transport/auth settings require restart (§11).
- **All filesystem paths are absolute** and are normalized before use.
- **No secret is ever a literal value.** There is no field anywhere in this schema
  that accepts a token. A token reaches the process only through a systemd
  credential or an explicit executor-local file (§7). Public API clients use
  separate REST settings and cannot forward a Hub `--token-file`.
- **Validation is total.** `hfcache config validate` performs exactly the same
  validation the mutating commands do, and mutates nothing.

Validation errors are reported with a stable code, the TOML path of the offending
key, and the reason. The full error taxonomy lives in `docs/cli.md`; the
configuration family is `HFCFG###` and is enumerated in §8 below.

## 2. Top level

```toml
schema_version = 1
```

| Key | Type | Required | Default | Constraint |
| --- | --- | --- | --- | --- |
| `schema_version` | int | yes | — | Must equal `1` |

`schema_version` is mandatory and has no default, so an unversioned file is an
error rather than an assumption. Unsupported versions refuse. Compatible extensions can retain version 1 only
with explicit validation/rollback rules. Version 1 permits retention 3 or 5,
defaulting to 3; older readers require explicit 5 and validation before rollback.
Changing policy alone never prunes data.

Permitted tables: `[hub]`, `[storage]`, `[sync]`, `[verification]`, `[repair]`,
and the `[[repositories]]` array. Any other table is `HFCFG003`.

## 3. `[hub]`

```toml
[hub]
endpoint = "https://huggingface.co"
expected_account = ""
token_mode = "optional"
credential_name = "hf-token"
```

| Key | Type | Default | Constraint |
| --- | --- | --- | --- |
| `endpoint` | str | `"https://huggingface.co"` | Absolute `https://` URL, host required, no path, no query, no trailing `/` |
| `expected_account` | str | `""` | Empty, or a Hub username/organization matching `[A-Za-z0-9][A-Za-z0-9._-]{0,95}` |
| `token_mode` | str | `"optional"` | `"disabled"` \| `"optional"` \| `"required"` |
| `credential_name` | str | `"hf-token"` | `[A-Za-z0-9._-]{1,64}`, and not `.` or `..` |

`endpoint` must be `https://`. A plaintext endpoint is `HFCFG014`: TLS
verification is not optional, and an archive whose provenance came over an
unauthenticated channel is not worth verifying afterwards.

`expected_account` empty means no identity check. That is normal for anonymous
public access; authenticated deployments should set it so `doctor` proves the
credential belongs to the intended Hub account before a sync is enabled. When it
is set, a resolved identity from `whoami` must match exactly (`HFHUB003`).

`token_mode` semantics:

| Value | Meaning |
| --- | --- |
| `"disabled"` | No credential is read or used. Hub calls always pass `token=False` |
| `"optional"` | A credential is used if present for identity and rate limits. Its absence is not an error; repository scope remains public-only |
| `"required"` | A credential must resolve or the command fails with `HFARG008`; private and gated repository scope is enabled (`AD-21`) |

`required` is deliberately both an availability requirement and the restricted-
content opt-in. A token found under `optional` never widens repository scope:
metadata marked private or gated remains `HFHUB006`. This prevents installing a
rate-limit or identity credential from silently changing what the archive may
retain. Under `required`, readable private and gated repositories proceed through
the same complete-revision pipeline as public repositories. Every consumer of
the publication export must be authorized to receive that content (`AD-21`).

Losing upstream access does not remove a local revision. Future Hub calls fail,
while existing publications remain until the operator removes the repository
from configuration and explicitly applies `purge` (`AD-06`, `AD-20`).

## 4. `[storage]`

```toml
[storage]
archive_root = "/srv/hfcache"
archive_id = "replace-with-provisioned-uuid"
publication_mode = "hardlink"
minimum_free_space_gib = 100
minimum_free_space_percent = 10
maximum_revisions = 3
```

| Key | Type | Default | Constraint |
| --- | --- | --- | --- |
| `archive_root` | str | — (required) | Absolute, normalized POSIX path; no `..`, no trailing `/` |
| `archive_id` | str | — (required) | Canonical lowercase UUID string |
| `publication_mode` | str | `"hardlink"` | `"hardlink"` \| `"copy"` |
| `minimum_free_space_gib` | int | `100` | `0 <= n <= 1048576` |
| `minimum_free_space_percent` | int | `10` | `0 <= n <= 100` |
| `maximum_revisions` | int | `3` | `3` or `5` |

`archive_id` must equal the UUID inside `.hfcache-root` at the archive root
(`FS-01`, `FS-03`). It is the interlock that stops a misconfigured or remounted
path from being written as though it were the archive. A mismatch is fatal and is
never auto-repaired.

`publication_mode = "copy"` doubles the stored bytes for every published revision.
It exists for the documented two-dataset export fallback where hardlinks cannot
cross a dataset boundary. It is never selected automatically: if hardlinks turn
out to be unavailable while `"hardlink"` is configured, sync fails **before**
downloading rather than quietly consuming twice the planned space (`AD-11`).

The **effective free-space reserve** is the greater of `minimum_free_space_gib`
and `minimum_free_space_percent` of the dataset's quota, or of its capacity when
no quota is set. Preflight requires free capacity to exceed the estimated
download bytes, plus the publication bytes when copy mode is enabled, plus that
reserve.

`maximum_revisions` defaults to `3`; an explicit `5` remains supported
(`HFCFG011`). These are the only accepted values. Retention orders revisions by
immutable publication generation, never timestamps (`AD-04`, `AD-05`), and
always protects the current revision.

**retention amendment (2026-09-14, decision 102).** Schema version 1 now accepts
`3` as well as the original `5`, and omission selects `3`. This deliberately
widens the configuration policy without changing archive JSON formats. Existing
files with an explicit `5` keep their policy; adopting the new default requires
setting `3` or removing that explicit value. Before rolling back to a pre-retention
binary, explicitly set `maximum_revisions = 5` and validate with that binary.
Changing the value does not itself delete revisions: review and apply `prune`
repeatedly until no eligible excess remains (`docs/operations.md` §6). A new sync
publication adds one revision and removes one, so it cannot by itself reduce an
existing over-retained history to the lower limit.

## 5. `[sync]`, `[verification]`, `[repair]`

```toml
[sync]
max_workers = 4
lock_wait_seconds = 3600
continue_on_repository_error = true
dependency_policy = "warn"
stale_staging_age_hours = 24

[verification]
algorithm = "sha256"
hash_new_content = true
lock_wait_seconds = 86400

[repair]
retired_instance_grace_hours = 168
```

| Key | Type | Default | Constraint |
| --- | --- | --- | --- |
| `sync.max_workers` | int | `4` | `1 <= n <= 32` |
| `sync.lock_wait_seconds` | int | `3600` | `0 <= n <= 86400` |
| `sync.continue_on_repository_error` | bool | `true` | — |
| `sync.dependency_policy` | str | `"warn"` | `"warn"` only; `"ignore"` and `"fail"` are reserved |
| `sync.stale_staging_age_hours` | int | `24` | `1 <= n <= 8760` |
| `verification.algorithm` | str | `"sha256"` | `"sha256"` only |
| `verification.hash_new_content` | bool | `true` | Must be `true` |
| `verification.lock_wait_seconds` | int | `86400` | `0 <= n <= 604800` |
| `repair.retired_instance_grace_hours` | int | `168` | `168 <= n <= 8760` |

`sync.max_workers` is the file-worker budget passed to the one active Hub
repository transfer. Sync never multiplies it by downloading two repositories
at once. With `continue_on_repository_error = true`, that one producer may
download later admitted repositories while the main thread hashes and publishes
an earlier one. With `false`, repositories remain fully serial so a failure
cannot contact or mutate a later repository before the command stops. Copy-mode
staging temporarily pauses cache transfers because both allocate dataset space;
hardlink staging does not.

The two `lock_wait_seconds` values are deliberately asymmetric. A scheduled sync
waits one hour and then gives up, because the next timer firing is cheap. A
quarterly verification waits 24 hours, because a legitimately long sync should
delay verification rather than race it or skip a quarter.

`continue_on_repository_error = true` means one repository's failure does not
abandon the rest of the run. It never changes the aggregate exit code: a run with
any repository failure still exits non-zero so systemd records it as failed.

`verification.hash_new_content` must remain `true`. It is a named field because
the manifest records which policy produced it, not because publishing unhashed
content is a supported mode (`AD-18`).

`sync.stale_staging_age_hours` is the minimum age a `.store/staging`,
`.store/trash`, `.store/quarantine`, or `.store/repair` entry must reach before
reconciliation will act on it — and age is only one of three conditions, alongside
a name matching the transaction-ID grammar and an existing journal
(`docs/architecture.md` §7.8). The delay exists so a concurrent operator command
cannot have its working directory reclaimed underneath it. Quarantined repair
evidence is exempt: it is released only by explicit operator action.

`repair.retired_instance_grace_hours` has a hard floor of `168` (seven days).
A superseded repair instance stays readable at its original locator for that long
so an in-flight consumer copy can finish (`AD-13`). Lowering the floor requires
measured consumer-copy timings and a deliberate schema-version change, not an
edit to this file.

## 6. `[[repositories]]`

```toml
[[repositories]]
id = "organization/model-name"
type = "model"
revision = "main"
enabled = true
declared_dependencies = []
```

| Key | Type | Default | Constraint |
| --- | --- | --- | --- |
| `id` | str | — (required) | Exactly two segments `<org>/<repo>`; each `[A-Za-z0-9][A-Za-z0-9._-]*`, not `.` or `..`, at most 96 characters |
| `type` | str | — (required) | `"model"` \| `"dataset"` |
| `revision` | str | `"main"` | A branch name, a tag name, or a full 40-character lowercase commit SHA |
| `enabled` | bool | `true` | — |
| `tags` | list[str] | `[]` | At most 64 raw strings; canonical label grammar below |
| `declared_dependencies` | list[str] | `[]` | Each entry a valid two-segment repository id; no duplicates |

`tags` is the only operator-managed organizational field. The backend trims outer
ASCII spaces, lowercases ASCII letters, deduplicates and sorts byte-wise. Each raw
string is at most 128 characters and its canonical value must match
`[a-z0-9][a-z0-9._:/-]{0,63}`. Reject nonstrings, empty values, controls, internal
whitespace and non-ASCII text; limits apply before deduplication. For example,
`tags = ["Coding", " coding ", "project:assistant", "vision/ocr"]` becomes
`["coding", "project:assistant", "vision/ocr"]`. Slashes and colons are literal,
with no hierarchy, wildcard or filesystem meaning. Omitted and empty tags agree;
disabled entries retain tags. Tags never change authorization, retention, file
selection, scheduling or policy fingerprints. Keep credentials out of labels.

Tag syntax is supported by local/candidate validation. Discovery interfaces are
specified separately in [discovery](discovery.md). Existing configuration without
tags remains valid. Older binaries reject the new key: preserve configuration
backups and restore a tag-free compatible document before guarded rollback.

Single-segment canonical identifiers such as `gpt2` are rejected (`HFCFG008`).
Every canonical Hub repository now has a namespaced form — `openai-community/gpt2`,
`google-bert/bert-base-uncased` — and requiring it keeps the on-disk layout
unambiguous.

`revision` accepts a moving reference on purpose: the configured reference is
resolved to an immutable SHA on every run, and it is the resolved SHA that is
downloaded, published, and retained (`AD-01`). A `revision` that is already a full
SHA simply resolves to itself and will never produce a second revision.
Abbreviated SHAs are rejected — they are ambiguous and are never written to disk.

Reference-name grammar: `[A-Za-z0-9._/-]+`, no leading or trailing `/`, no `//`,
no `..`, no leading `-`, no trailing `.lock`, at most 255 characters.

`declared_dependencies` suppresses the undeclared-dependency warning
(`HFDEP001`) for the identifiers it lists. Matching is **exact and
case-sensitive**: a near-miss should produce a visible warning rather than
silently suppress one. The CLI prints the detected identifier verbatim so the
operator can paste it in. Declaring a dependency does not archive it — archiving
it means adding its own `[[repositories]]` entry (`AD-07`).

Duplicate `(type, id)` pairs are rejected (`HFCFG007`). `enabled = false` keeps an
entry in the file, and its archived data untouched, while excluding it from runs.

Removing a repository from configuration never deletes its archive (`AD-06`).
Its published revisions remain, and `status` reports them as unmanaged.

An empty repository list is valid. It is how an operator disables all
synchronization without discarding the rest of the configuration; `sync` reports
that it had nothing to do and exits `0`.

## 7. Credentials

No token is ever written in this file. There is no key that accepts one, so a
token in TOML is `HFCFG010` — reported by shape without echoing the value.

Resolution order, first match wins:

1. `--token-file PATH` when explicitly passed to an operator-run command. The file
   is read as UTF-8, stripped of a single trailing newline, and never logged.
2. `${CREDENTIALS_DIRECTORY}/<credential_name>` when systemd supplies it.
3. No token — Hub calls pass `token=False` in `disabled` or `optional`; `required`
   instead fails with `HFARG008` before any Hub request.

Ambient discovery is disabled in every case: `HF_TOKEN`, `HUGGING_FACE_HUB_TOKEN`,
`~/.cache/huggingface/token`, and any other implicit source is ignored. Hub calls
pass an explicit `token=False` or an explicit token string, never `token=None`,
so a developer's or service account's cached credential cannot silently change
what a production run does (the architecture contract).

A token is never written to the archive, a manifest, a run report, a log line, or
a journal entry.

### 7.1 What a credential file must contain

A credential file holds the token alone, with at most one trailing newline. After
that newline is removed the remainder must be non-empty printable ASCII with no
whitespace, and the file must be a regular file of at most 4096 bytes.

Anything else is a malformed credential rather than a token to be repaired on the
way through: a token becomes an `Authorization` header, so forwarding a value
containing a stray carriage return, tab, or second newline would put whitespace
into a header. Every rejection names the file and the defect, never the content.

### 7.2 When each source fails

| Situation | Outcome |
| --- | --- |
| `--token-file` given and unusable | `HFARG005` |
| `--token-file` given with `token_mode = "disabled"` | `HFARG002` |
| `$CREDENTIALS_DIRECTORY` unset or empty | No token; not an error |
| Credential named by `credential_name` absent from that directory under `optional` | No token; not an error |
| That credential's name exists but is unusable | `HFARG006` |
| `$CREDENTIALS_DIRECTORY` set to a relative path | `HFARG006` |
| No explicit or systemd credential resolves while `token_mode = "required"` | `HFARG008` |

The asymmetry in the middle rows is deliberate. `token_mode = "optional"` means a
*missing* credential is normal, so absence resolves to anonymous access. A
credential that was installed and is then unreadable, empty, or malformed is a
different event: continuing anonymously would report success for a run the
operator believes was authenticated, so it fails at exit `10` instead.

`--token-file` together with `token_mode = "disabled"` is a contradiction, not a
preference. Honouring the flag would violate the configured mode; ignoring it
would let an operator believe a run was authenticated when it was not. Neither is
silently chosen.

## 8. Configuration error codes

| Code | Condition |
| --- | --- |
| `HFCFG001` | Configuration file missing, unreadable, or not a regular file |
| `HFCFG002` | Malformed TOML |
| `HFCFG003` | Unknown key or unknown table |
| `HFCFG004` | Missing or unsupported `schema_version` |
| `HFCFG005` | Type error or constraint violation on a known key |
| `HFCFG006` | Filesystem path is not absolute or not normalized |
| `HFCFG007` | Duplicate `(type, id)` repository entry |
| `HFCFG008` | Invalid repository identifier grammar |
| `HFCFG009` | Invalid revision or reference-name grammar |
| `HFCFG010` | A literal secret appears in configuration |
| `HFCFG011` | `maximum_revisions` is neither `3` nor `5` |
| `HFCFG012` | `archive_id` is not a canonical UUID |
| `HFCFG013` | `credential_name` grammar is invalid |
| `HFCFG014` | `hub.endpoint` is not a valid `https://` URL |
| `HFCFG015` | Retired at `Hub access`; earlier releases used it to reject `token_mode = "required"` |
| `HFCFG016` | `repair.retired_instance_grace_hours` below the seven-day floor |

All configuration failures exit `10` (§`docs/cli.md`), before any lock is taken,
any Hub request is made, or any path is mutated.

## 9. Configuration fingerprint

Run reports and transaction journals record a **configuration fingerprint** so an
archived artifact can be traced to the intent that produced it, without storing
The configuration itself.

The fingerprint is the lowercase hex SHA-256 of the canonical JSON serialization
of the loaded configuration — sorted keys, no insignificant whitespace, UTF-8 —
with these fields excluded: `hub.credential_name` and any resolved token or
credential path. It covers `schema_version`, all of `[storage]`, `[sync]`,
`[verification]`, `[repair]`, `hub.endpoint`, `hub.expected_account`,
`hub.token_mode`, and the repository operational fields: `type`, `id`, `revision`, `enabled`
and `declared_dependencies`. Operator tags are excluded; adding tags must preserve
all existing policy fingerprint values. A separate versioned curation digest
identifies canonical `(type, id, tags)` for all entries, including disabled and
empty-tag entries; see the [discovery contract](discovery.md). Its canonical JSON
object has `schema_version=1` and `repositories` sorted by `(type, id)`, each with
only `type`, `id`, and canonical `tags`. Use the same sorted-key, compact UTF-8
serialization and SHA-256. It includes no credential, operational path or enabled
flag; disabled entries remain included. No existing response wrapper gains fields.

Two runs with byte-identical intent produce an identical fingerprint; any change
to what is archived, how much is retained, or where it is stored produces a
different one.

## 10. Worked example

```toml
# /etc/hfcache/config.toml — owner root:hfcache, mode 0640
schema_version = 1

[hub]
endpoint = "https://huggingface.co"
expected_account = ""          # anonymous public access
token_mode = "optional"        # no credential installed; token=False is passed
credential_name = "hf-token"

[storage]
archive_root = "/srv/hfcache"
archive_id = "00000000-0000-0000-0000-000000000000"   # must match .hfcache-root
publication_mode = "hardlink"
minimum_free_space_gib = 100
minimum_free_space_percent = 10
maximum_revisions = 3

[sync]
max_workers = 4
lock_wait_seconds = 3600
continue_on_repository_error = true
dependency_policy = "warn"
stale_staging_age_hours = 24

[verification]
algorithm = "sha256"
hash_new_content = true
lock_wait_seconds = 86400

[repair]
retired_instance_grace_hours = 168

[[repositories]]
id = "organization/model-name"
type = "model"
revision = "main"
enabled = true
declared_dependencies = []

[[repositories]]
id = "organization/dataset-name"
type = "dataset"
revision = "main"
enabled = true
declared_dependencies = []
```

A runnable version of this file, with the two small public test repositories
chosen at implementation time, ships as `examples/config.toml`.

## 11. Separate server and client configuration

The archive-policy schema above remains `ApplicationConfig`. Server configuration
is a separate strict, frozen, schema-1 `ServerConfig`, defaulting to
`/etc/hfcache/server.toml`; its keys, example and credential rules are in the
[server contract](server.md). Do not put listeners, API credentials, admission
limits or maintenance gates into the archive TOML. API credentials and Hub
credentials have separate sources and authority. Independent client configuration
contains only connection/authentication settings and never grants archive access
on the client host.

Server transport and authentication are loaded at startup and change only after
operator replacement and restart. Archive policy is loaded and validated afresh
for each query or operation admission, yielding one immutable snapshot and its
existing nonsecret fingerprint. Already-running work keeps its snapshot. A
changed archive root or UUID requires a server restart and cannot hot-switch the
server to another archive. Invalid updated policy fails new archive work closed;
version/health remain able to diagnose invalid updated policy without repair.

The API runner reloads policy under the service-owned archive lock
and compares it with the admitted fingerprint before mutation. A changed policy refuses stale
queued work; it does not quietly execute against new scope. Policy loading does
not install a candidate or change `/etc/hfcache`, and candidate-selected paths or
Hub endpoints cannot redirect the installed credential. Server configuration pins authority; the HTTP boundary and runner enforce it
for requests and queued execution. [Decision 112](adr/decision-112.md) records the boundary.

The receipt store uses restart-only `state_directory` and operation-storage limits to the
server domain, documented in [server resource settings](server.md#resource-settings).
The default local directory is `/var/lib/hfcache/api`; it is independent of
archive policy, publication/export trees and archive UUID changes. Never use it
as a candidate-selected path. Its independently versioned receipts bind admitted
archive UUID/fingerprint without storing an archive root, credential or candidate
body. Retention defaults to 30 days for validated succeeded/failed history;
unexpired bindings cannot be evicted for count caps, and interrupted/ambiguous/
nonterminal state never ages out. Storage exhaustion refuses admission. See
[decision 114](adr/decision-114.md) and [schema §13](schemas.md#13-service-private-operation-control-state).

bounded runner and private verifier's separate `[verification]` table configures only the protected private
Unix-socket client, expected peer UID and bounded exchange/poll/frame policy.
The socket defaults to `/run/hfcache/verification.sock`; omission of the peer UID
uses the API process's effective UID. These settings require restart and cannot
be overridden by an inbound request. They grant no process-launch, arbitrary
configuration path or credential-forwarding authority. The dedicated worker's
trusted service startup supplies its fixed archive config and separate private
state root. scheduled observation packages socket/identity/no-IP policy; installed enforcement
remains operator acceptance. See
[server verifier settings](server.md#private-verifier-client-settings)
and [decision 115](adr/decision-115.md).

optional MCP transport uses the existing restart-only `mcp_enabled` and
`credentials.mcp_reader` fields, without a schema change. Disabled mode loads no
MCP package or credential; enabled mode requires both optional dependencies and
a protected distinct source. Do not reuse a REST/Hub secret or add a literal
token to TOML. optional MCP transport activates transport; curated metadata tools registers nine narrow
metadata tools without another setting or schema change.
See [MCP enablement](mcp.md#deployment-profiles) and
[decision 124](adr/decision-124.md).

## 12. Candidate authority validation and planning

[`services.candidates`](../src/hfcache/services/candidates.py) validates bounded
candidate TOML content without loading a server-selected file. The pure command routes
hooks now support API-backed reader CLI validation/planning; an explicit CLI `--config` for those
commands reads at most 1 MiB of nonempty regular UTF-8 content on the CLI host,
checks stable descriptor metadata and uploads text. It never sends a pathname
for the server to open. The total JSON request cap may refuse escaping/overhead
independently. Other migrated API reads reject archive-config/Hub-token overrides.

Syntax/policy validity and installed authority compatibility are separate. Candidate
validation uses no credential/Hub/probe and reports `token_source=not-resolved`.
Valid incompatible policy remains valid with compatibility false and ordered
mismatch field names. A valid candidate can also be syntax-validated while installed
policy is broken/unavailable: compatibility is null and `installed_policy_valid`
is false, not permission to plan. Validity proves no credential availability or
Hub/account/network identity. Invalid policy retains safe ordered classified errors.

`authority_mismatches` compares these fields in fixed order and returns only
field names, never proposed/installed values:

| Authority field | Why it must match installed policy for candidate planning |
| --- | --- |
| `storage.archive_root` | Prevent switching filesystem authority |
| `storage.archive_id` | Preserve archive identity |
| `hub.endpoint` | Prevent redirecting the installed credential |
| `hub.token_mode` | Preserve public/restricted authorization policy |
| `hub.credential_name` | Prevent selecting another protected source |
| `hub.expected_account` | Preserve the expected Hub account |

Only compatible candidates can enter credential-bearing planning, using installed
authorized credentials with candidate repository/retention/worker intent. Proposed
authority changes can be validated but require privileged operator installation
before planning; startup-pinned root/UUID changes also require restart. A candidate plan is a keyed writer job, retains the
installed admitted fingerprint and cannot authorize apply. All six authority
fields are checked again after queue waiting before Hub work, including the
credential name deliberately excluded from the policy fingerprint. The startup-only
`serve --hub-token-file` remains installed server authority, never request input.

Only an absent candidate means installed intent; explicit null is refused. The
absent optional field is omitted from plan canonical bodies, preserving existing
installed-plan key digests.
Candidate exact text binds a new request; no raw candidate body is durable control
state. REST cannot install policy or backups. Cockpit's CP-11 pipeline now guards
exact candidate/base bytes under the retained root config flock, requires valid
compatible assessment and any required successful preview, then preserves atomic
backup/install and confirms the exact expected installed fingerprint. Edits
invalidate readiness; incompatible/unknown authority blocks plugin install with
manual operator guidance. API-only clients never receive Hub authority. See
[decision 122](adr/decision-122.md), [Cockpit pipeline](cockpit.md#6-configuration-editing)
and [decision 119](adr/decision-119.md)
and [candidate wire contract](api.md#candidate-content-and-installed-authority).

## 13. Independent reader/client configuration

[Client configuration](api-client.md) is a separate strict schema-1 TOML domain,
implemented by `ClientConfig` / `resolve_client_config`. It contains API endpoint,
explicit API credential source, optional CA/expected archive UUID and finite
transport/observation budgets. It contains no archive storage policy, Hub token,
server listener or literal bearer. Reader setup needs no archive TOML/mount or
writer service identity. The API client does not load `ApplicationConfig`.

Explicit URL/socket selection replaces the configured endpoint as one mutually
exclusive group. Explicit API token file overrides configured token file, then
only the named systemd API credential is considered. The optional installed
`/etc/hfcache/client.toml` is read when no explicit client path is supplied; a
missing default permits local-socket defaults, while installed unusable or explicit
missing settings refuse. A selected unusable credential never falls back anonymously.
No Hub/ambient bearer/proxy discovery or local archive fallback is permitted.

The [client contract](api-client.md#client-configuration-and-setup) records exact
fields/defaults/ranges and safe file/URL rules. Settings/selection failures use
HFAPI017; protected credential failures retain HFAPI003. Separate client settings
never enter archive-policy fingerprints or receipts. API-backed reader CLI uses the stored
global choices for reader/candidate modes; CLI operation observation completes operational CLI and
explicit observation through the same authority. See
[decision 118](adr/decision-118.md).

scheduled observation's [scheduled-client example](../packaging/scheduled-client.example.toml)
uses this same client schema and the API-only named credential `hfcache.api`.
Scheduled sync/verify-full requires an explicit `expected_archive_id` before any
HTTP or private state allocation; replace the example UUID with the installed
archive UUID. Its `wait_timeout` bounds each observation window, while the
scheduled oneshot repeats windows through exact terminal output. The private
[observation handle](schemas.md#14-scheduled-client-observation-handle)
binds endpoint/UUID/REST-writer class across restarts and token rotation; it never
contains a bearer, credential digest or archive policy. It is not another client
configuration or execution queue. See [decision 121](adr/decision-121.md).


MCP client guidance uses an explicit protected MCP-reader file and canonical
HTTP endpoint, not archive TOML, the REST client's credential or a new config
schema. See [the runnable setup example](mcp.md#connect)
and [resource limits](mcp.md#resource-costs-and-troubleshooting). Credential/source
settings remain startup-only; rotation requires the normal API drain/restart and
new clients. Disabled mode requires neither optional package nor MCP source.


## Rootless deployment selector

The selected container release adds independent protected rendered/runtime.json,
not archive/server/client TOML fields. The helper pins its physical release tree;
the selected rendered directory is mounted read-only at /etc/hfcache/containers
and selected client.toml at /etc/hfcache/client.toml inside containers. No static
/etc runtime-profile copy bypasses the atomic current selector.
[Runtime profile contract](containers.md#protected-runtime-profile) and
[schema 15](schemas.md#15-rootless-runtime-deployment-profile) define the
strict five-field integer schema 1, matching host service identity and immutable
image IDs. Fixed role paths and named secrets remain trusted helper policy,
not request-supplied configuration. Read-only directory binds expose atomic
installed policy replacements to fresh admissions while preserving admitted
fingerprints. Source-store masks, secret separation and the no-NAS-write guard
remain; see [decision 127](adr/decision-127.md). The selected rootless profile and its recorded acceptance limits are described
in [deployment status](deployment-status.md). Native and rootless delivery differ.
