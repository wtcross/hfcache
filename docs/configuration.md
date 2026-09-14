# hfcache Configuration Contract

| Field | Value |
| --- | --- |
| Status | Normative contract for implementation |
| Derived from | `docs/plan.md` §9, §12, §22.6 |
| Work package | `ARC-003` |
| Schema version | `1` |
| Default location | `/etc/hfcache/config.toml` |

Configuration is TOML, parsed with `tomllib`, and validated into strict, frozen
Pydantic models. It is the complete statement of operator intent. Everything it
describes is validated **before** any network request or filesystem mutation, so
an invalid configuration can never partially apply.

## 1. Validation rules that apply to every field

- **Unknown keys are rejected.** Every model uses `extra="forbid"`. A typo is an
  error, never a silently ignored setting.
- **Types are strict.** Pydantic strict mode is enabled; `"4"` is not an integer
  and `1` is not a boolean. TOML already distinguishes these, so a type error
  always means the operator wrote the wrong thing.
- **Models are frozen.** Once loaded, configuration is immutable for the life of
  the process. No code path mutates it.
- **All filesystem paths are absolute** and are normalized before use.
- **No secret is ever a literal value.** There is no field anywhere in this schema
  that accepts a token. A token reaches the process only through a systemd
  credential or an explicit `--token-file` (§7).
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
error rather than an assumption. A future version bump is the only supported way
to change the meaning of any key below.

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

**RET-010 amendment (2026-09-14, decision 102).** Schema version 1 now accepts
`3` as well as the original `5`, and omission selects `3`. This deliberately
widens the configuration policy without changing archive JSON formats. Existing
files with an explicit `5` keep their policy; adopting the new default requires
setting `3` or removing that explicit value. Before rolling back to a pre-RET-010
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
| `declared_dependencies` | list[str] | `[]` | Each entry a valid two-segment repository id; no duplicates |

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
what a production run does (`docs/plan.md` §12).

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
| `HFCFG015` | Retired at `HUB-010`; earlier releases used it to reject `token_mode = "required"` |
| `HFCFG016` | `repair.retired_instance_grace_hours` below the seven-day floor |

All configuration failures exit `10` (§`docs/cli.md`), before any lock is taken,
any Hub request is made, or any path is mutated.

## 9. Configuration fingerprint

Run reports and transaction journals record a **configuration fingerprint** so an
archived artifact can be traced to the intent that produced it, without storing
the configuration itself.

The fingerprint is the lowercase hex SHA-256 of the canonical JSON serialization
of the loaded configuration — sorted keys, no insignificant whitespace, UTF-8 —
with these fields excluded: `hub.credential_name` and any resolved token or
credential path. It covers `schema_version`, all of `[storage]`, `[sync]`,
`[verification]`, `[repair]`, `hub.endpoint`, `hub.expected_account`,
`hub.token_mode`, and the full repository list including `enabled` flags and
declared dependencies.

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
