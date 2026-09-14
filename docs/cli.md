# hfcache Command-Line Contract

| Field | Value |
| --- | --- |
| Status | Normative contract for implementation |
| Derived from | `docs/plan.md` §11, §22.2, §24 |
| Work package | `ARC-005` |
| Entry point | `hfcache = "hfcache.cli:app"` |
| JSON envelope version | `1` |

The CLI is the only interface to the application. Scheduled runs use exactly the
same commands an operator types, so a behaviour that cannot be reproduced by hand
does not exist.

## 1. Invocation shape

```text
hfcache [GLOBAL OPTIONS] COMMAND [SUBCOMMAND] [ARGUMENTS] [OPTIONS]
```

Global options are placed **before** the command, matching the systemd
invocation:

```text
/opt/hfcache/current/.venv/bin/hfcache --config /etc/hfcache/config.toml sync
```

| Global option | Default | Meaning |
| --- | --- | --- |
| `--config PATH` | `/etc/hfcache/config.toml` | Configuration file |
| `--json` | off | Emit the machine-readable envelope (§4) on stdout and nothing else |
| `--verbose` / `-v` | off | Adds the `hfcache.logging.DEBUG_EVENTS` detail to the §24 event log. Repeatable, and repeats beyond the first are currently equivalent to one, because the vocabulary bottoms out at `DEBUG`. Never enables secret logging |
| `--quiet` / `-q` | off | Suppress progress and informational output; warnings and errors still print |
| `--no-color` | auto | Force plain output; also implied when stdout is not a terminal |
| `--token-file PATH` | none | Read a token from this file for an operator-run command (§`docs/configuration.md` §7) |

`--json` and `--quiet` are compatible. `--json` and `--verbose` are compatible;
verbosity affects stderr logging, never the stdout envelope.

Progress rendering is disabled automatically when stdout is not a terminal, so
journald never receives progress spam.

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

| Command | Mutates | Purpose |
| --- | --- | --- |
| `config validate` | no | Parse and fully validate configuration |
| `archive init` | yes | One-time guarded archive creation |
| `archive init --inspect` | no | Describe a partial or existing initialization |
| `doctor` | probe only | Prove mount, sentinel, permissions, capabilities, capacity, DNS, Hub reachability |
| `plan` | no | Resolve configured revisions and report expected work |
| `sync` | yes | Synchronize all or selected repositories |
| `status` | no | Configured, retained, current, warning, and verification state |
| `list` | no | Archived repositories and revisions |
| `verify` | no | Integrity verification in one of four modes |
| `prune` | yes with `--apply` | Retention cleanup |
| `purge` | yes with `--apply` | Permanently remove unmanaged repositories |
| `recover` | yes with `--apply` | Reconcile unfinished transactions |
| `quarantine` | yes with `--apply` | Remove explicitly selected, proven redundant recovered staging |
| `repair` | yes | Reconstruct and republish a damaged known revision |
| `version` | no | Application and dependency versions |

### `config validate`

```text
hfcache [--config PATH] config validate
```

Performs exactly the validation every mutating command performs, and touches
nothing — no lock, no mount check, no network. Exits `0` or `10`.

This includes resolving the credential, so `--token-file` and an installed
systemd credential are checked here rather than first failing during a scheduled
run. `token_source` reports which source won — `token-file`,
`systemd-credential`, or `none` — and never the value (`docs/security.md` T-07).
Under `token_mode = "required"`, resolving to `none` is `HFARG008`; a green
validation therefore proves the credential needed for restricted scope is
present, though `doctor` is what proves its Hub identity and network validity.

### `archive init`

```text
hfcache [--config PATH] archive init --archive-root PATH --confirm [--archive-id UUID]
hfcache [--config PATH] archive init --archive-root PATH --inspect
```

| Option | Meaning |
| --- | --- |
| `--archive-root PATH` | Required, and must equal `storage.archive_root`. Stating it twice is deliberate: initialization is the one irreversible act, so it does not take its target from a file alone |
| `--confirm` | Required for mutation. Without it, the command explains what it would do and exits `10` |
| `--archive-id UUID` | Restates the provisioned `storage.archive_id`, for the same reason `--archive-root` restates the root. It must agree with configuration (`HFARG002`) |
| `--inspect` | Never mutates; reports whether the target matches the known-empty layout contract. Mutually exclusive with `--confirm` (`HFARG002`) |

The command proves the target is the expected read/write NFS mount, refuses a
pre-existing sentinel or unknown content (`FS-22`), creates the directory
structure with the documented ownership and modes, fsyncs it, writes
`.hfcache-root` last (`FS-23`), and prints the UUID it wrote so the operator can
confirm that configuration and sentinel agree.

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
hfcache [--config PATH] doctor [--read-only]
```

`checks[]` is emitted in this order. The names are normative — automation keys on
them and `status` quotes them — and a check is **absent** until the package that
performs it lands, rather than being reported as skipped or passed
(`docs/progress.md` decision 24).

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
never ran would have passed. Every problem found is reported at once
(`docs/plan.md` §19).

Writability is proven only by the check-7 probe, never by comparing `st_uid`
against the local service uid — under the Mapall writer export the owner has no
local account (`docs/plan.md` §35.3).

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
hfcache [--config PATH] plan [TYPE:ID ...]
```

Resolves each enabled repository's configured reference to a full commit SHA and
reports, per repository: the resolved SHA, whether it is already retained or
current, the repository's logical size, the estimated new bytes to download, and
the publication bytes projected under the configured `publication_mode`. Mutates
nothing and takes no lock.

Three Hub reads per repository, in the order §13.2 of `docs/plan.md` puts them:
resolve the reference, enumerate the revision's tree, then cost the download with
a `snapshot_download` dry run against the same private cache a sync would write
to. The dry run creates nothing — not even the cache directory — so this command
answers against an archive that has not been initialized yet, which is exactly
who is asking. A failure at any of the three leaves the fields below it `null`
rather than guessed, and the repository's `upstream_state` records what was
observed.

`projected_publication_bytes` is `0` under `publication_mode = "hardlink"`, since
a hardlink points at a cache blob already on the dataset; under `"copy"` it is the
logical size, because copy mode writes a second physical copy of every byte
(`AD-11`). The mode is reported beside it so the zero is explicable, and a
deployment weighing the switch reads the copy-mode figure off `logical_bytes`.

This is the command run before enabling a large repository, and its output is what
the dataset quota is sized from.

### `sync`

```text
hfcache [--config PATH] sync [TYPE:ID ...]
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
hfcache [--config PATH] status [TYPE:ID ...]
```

Per repository: configured or unmanaged, enabled state, current SHA and
generation, retained revision count and generations, upstream state, outstanding
warnings, last run status, and verification state. Also reports archive-level
health: free space against reserve, outstanding verification failures, unfinished
transactions, over-retention, and deferred cleanup.

`status` is the command an operator runs first, so it never fails merely because
the Hub is unreachable — it reports local truth and marks upstream state
`unknown`.

### `list`

```text
hfcache [--config PATH] list [--type model|dataset] [--revisions] [TYPE:ID ...]
```

Archived repositories, and with `--revisions` every retained revision with its
generation, publication ID, size, publication timestamp, and verification state.
Reads only manifests and references, so it works on an archive whose catalog is
missing or corrupt.

### `verify`

```text
hfcache [--config PATH] verify --new [--run-id ID]
hfcache [--config PATH] verify --full
hfcache [--config PATH] verify --revision TYPE:ID@SHA
hfcache [--config PATH] verify --estimate
```

Exactly one mode option is required; two is `HFARG002`.

| Mode | Scope |
| --- | --- |
| `--new` | Content introduced by one run. Defaults to the most recent run report in `runs/`; `--run-id` selects another |
| `--full` | Every retained revision reachable from `refs/revisions/<sha>.json`. The quarterly job |
| `--revision` | One retained revision |
| `--estimate` | No hashing. Reports unique bytes to read, measured throughput when known, estimated duration, repository and revision counts, and any detectable overlap with storage maintenance. Takes no lock and always exits `0`: nothing was read, so nothing can have been found wrong |

`--full` acquires the verification lock, which is mutually exclusive with sync,
prune, purge, and repair. It runs with Hub networking disabled.

Exits `0` on a clean result and `40` on any integrity finding. A finding never
rewrites a manifest, prunes a revision, or re-downloads over the evidence.

### `prune`

```text
hfcache [--config PATH] prune --dry-run [TYPE:ID ...]
hfcache [--config PATH] prune --apply [TYPE:ID ...]
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
hfcache [--config PATH] purge --dry-run TYPE:ID [TYPE:ID ...]
hfcache [--config PATH] purge --apply TYPE:ID [TYPE:ID ...]
hfcache [--config PATH] purge --dry-run --all-unmanaged
hfcache [--config PATH] purge --apply --all-unmanaged
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
hfcache [--config PATH] recover --dry-run
hfcache [--config PATH] recover --apply
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
hfcache [--config PATH] quarantine --dry-run TRANSACTION_ID ...
hfcache [--config PATH] quarantine --apply TRANSACTION_ID ...
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
hfcache [--config PATH] repair TYPE:ID@SHA [--reason TEXT]
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
hfcache version
```

Application version, Python version, `huggingface_hub` version, and the resolved
transfer backend. Never reads configuration or touches the archive, so it works on
a broken deployment.

## 3. Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success, including non-fatal dependency warnings |
| `10` | Invalid configuration or invocation precondition |
| `20` | Mount, sentinel, permission, capacity, lock, or unresolvable-transaction safety failure |
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
so systemd records the unit as failed (`docs/plan.md` §11.2).

## 4. JSON output

`--json` writes exactly one envelope to stdout. Human-readable text goes to
stdout only without `--json`; logs and progress always go to stderr. This means
`hfcache --json sync | jq` is always safe.

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
| `config validate` | `config_fingerprint`, `repositories`, `enabled_repositories`, `token_source` |
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
| `HFVER007` | Manifest fails schema validation or internal consistency |
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

`HFDEP001` marks the repository `completed_with_warnings`, is written to the
manifest and the run report, is surfaced by `status`, and leaves the exit code at
`0` when nothing else failed (`AD-07`).

## 6. Output discipline

- Tokens, `Authorization` headers, signed URLs, and credential file contents are
  never printed, logged, or written to any durable artifact — at any verbosity.
- Error messages name the *shape* of a secret problem, never the value: a token
  found in configuration is reported by key path, not by content.
- Log events are structured, carry the `run_id`, use stable event names
  (`run.started`, `repository.resolved`, `download.completed`,
  `dependency.undeclared`, `publication.completed`, `retention.pruned`,
  `run.completed`, and the rest of `docs/plan.md` §24), and record durable
  checkpoints rather than per-chunk progress. The vocabulary is closed:
  `hfcache.logging.EVENTS` is the whole of it, and emitting a name outside it
  raises rather than writing a line no filter will match.
- The format is logfmt on **stderr** — `event=… level=… run_id=… key=value`,
  keys sorted after the first three, values quoted only when they would
  otherwise be ambiguous. Under systemd each line carries a `<N>` syslog prefix,
  which journald turns into `PRIORITY`, so `journalctl -p err -u
  hfcache-sync.service` selects failures; run by hand there is no prefix.
- Levels follow the options: `--quiet` is `WARNING`, the default is `INFO`, and
  `-v` is `DEBUG`. The §24 families are emitted at the default level rather than
  behind a flag, because they are the record an unattended run leaves and the
  systemd units pass no flags.
- Absolute filesystem paths are printed for operator commands, but every path
  written into a durable artifact is archive-relative (`docs/schemas.md` §1).
