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
| `--verbose` / `-v` | off | Repeatable; raises log detail. Never enables secret logging |
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
`HFARG004`, except for `status`, `list`, `verify`, and `repair`, which may
legitimately address archived repositories that are no longer configured
(`AD-06`).

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
| `recover` | yes with `--apply` | Reconcile unfinished transactions |
| `repair` | yes | Reconstruct and republish a damaged known revision |
| `version` | no | Application and dependency versions |

### `config validate`

```text
hfcache [--config PATH] config validate
```

Performs exactly the validation every mutating command performs, and touches
nothing — no lock, no mount check, no network. Exits `0` or `10`.

### `archive init`

```text
hfcache [--config PATH] archive init --archive-root PATH --confirm [--archive-id UUID]
hfcache [--config PATH] archive init --archive-root PATH --inspect
```

| Option | Meaning |
| --- | --- |
| `--archive-root PATH` | Required, and must equal `storage.archive_root`. Stating it twice is deliberate: initialization is the one irreversible act, so it does not take its target from a file alone |
| `--confirm` | Required for mutation. Without it, the command explains what it would do and exits `10` |
| `--archive-id UUID` | Use a provisioned UUID instead of generating one |
| `--inspect` | Never mutates; reports whether the target matches the known-empty layout contract |

The command proves the target is the expected read/write NFS mount, refuses a
pre-existing sentinel or unknown content (`FS-22`), creates the directory
structure with the documented ownership and modes, fsyncs it, writes
`.hfcache-root` last (`FS-23`), and prints the UUID to copy into root-owned
configuration.

The one adoption exception is a single pre-existing **empty** `published/` whose
ownership and mode already match, because TrueNAS requires that directory to
exist before the consumer export can be defined.

`archive init` is never invoked by a timer, a sync, or a recovery path (`FS-21`).

### `doctor`

```text
hfcache [--config PATH] doctor [--read-only]
```

Proves, in order: configuration validity; archive root exists; it is a mount
point distinct from its parent; the filesystem type is NFS/NFSv4; the mount is
read/write; the sentinel exists and matches `storage.archive_id`; required
directories are **effectively writable** via a real create/fsync/rename/delete
probe under `.store/health/` (never by comparing `st_uid`); staging and
destination share a filesystem; a regular file can be hardlinked from the cache
area into a published test path with correct link count and contents; a directory
can be atomically renamed within the dataset; a small ref file can be atomically
replaced; free capacity exceeds the configured reserve; DNS resolves the Hub
endpoint; the endpoint is reachable over TLS; and, when `expected_account` is
set, that the resolved identity matches.

`--read-only` runs only the checks that mutate nothing, for use on a mount that
must not be touched. It cannot prove hardlink, rename, or ref-replacement
capability, and says so explicitly rather than reporting a pass.

Every probe artifact is removed before the command returns. Exits `0` or `20`
(or `10` for configuration problems).

### `plan`

```text
hfcache [--config PATH] plan [TYPE:ID ...]
```

Resolves each enabled repository's configured reference to a full commit SHA and
reports, per repository: the resolved SHA, whether it is already retained or
current, the repository's logical size, the estimated new bytes to download, and
the projected publication bytes in copy mode. Mutates nothing and takes no lock.

This is the command run before enabling a large repository, and its output is what
the dataset quota is sized from.

### `sync`

```text
hfcache [--config PATH] sync [TYPE:ID ...]
```

The scheduled command. With no selectors it processes every enabled repository in
deterministic configuration order; with selectors it restricts the run to those.

Sequence, locking and preflight first, then per repository: resolve, skip or move
the reference if the SHA is already retained, estimate and check capacity,
download, check completeness locally, hash new unique content, detect
dependencies, write the manifest, build staging, rename it into place, publish the
manifest, publish the per-SHA reference, replace `current.json`, rebuild the
catalog, apply retention.

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
| `--estimate` | No hashing. Reports unique bytes to read, measured throughput when known, estimated duration, repository and revision counts, and any detectable overlap with storage maintenance |

`--full` acquires the verification lock, which is mutually exclusive with sync,
prune, and repair. It runs with Hub networking disabled.

Exits `0` on a clean result and `40` on any integrity finding. A finding never
rewrites a manifest, prunes a revision, or re-downloads over the evidence.

### `prune`

```text
hfcache [--config PATH] prune --dry-run [TYPE:ID ...]
hfcache [--config PATH] prune --apply [TYPE:ID ...]
```

Exactly one of `--dry-run` / `--apply` is required. `--dry-run` prints the exact
`PrunePlan` that `--apply` would execute and mutates nothing.

Retention normally runs inside `sync`; this command exists to inspect the plan
and to complete retention deferred by an earlier failure.

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
| `outcome` | `success` \| `success_with_warnings` \| `failed`; always agrees with `exit_code` |
| `data` | Command-specific payload (§4.1) |
| `warnings`, `errors` | Arrays of `{ "code", "repository", "message", "context" }`; `repository` is `null` for archive-level entries |

The envelope is emitted even on failure, including for configuration errors, so
automation never has to parse human text to learn what went wrong.

Serialization follows the same deterministic rules as durable files
(`docs/schemas.md` §1): sorted keys, UTF-8, trailing newline.

### 4.1 `data` payloads

| Command | `data` contains |
| --- | --- |
| `config validate` | `config_fingerprint`, repository count, enabled count |
| `archive init` | `archive_id`, `archive_root`, created paths, `adopted_published` |
| `doctor` | `checks[]` of `{ name, outcome, detail }`, in execution order |
| `plan` | `repositories[]` of resolved SHA, retained/current state, logical size, estimated new bytes |
| `sync` | The `RunReport` body (`docs/schemas.md` §6) |
| `status` | Archive health block plus per-repository state |
| `list` | `repositories[]`, with `revisions[]` when `--revisions` is given |
| `verify` | The `VerificationReport` body (`docs/schemas.md` §7) |
| `prune` | The `PrunePlan`, plus applied results for `--apply` |
| `recover` | `findings[]`, `plan[]`, and applied results for `--apply` |
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
| `HFARG002` | Mutually exclusive options given together |
| `HFARG003` | A required option is missing, such as `archive init` without `--confirm` |
| `HFARG004` | Selector names a repository absent from configuration, for a command that requires one |
| `HFARG005` | `--token-file` is missing, unreadable, empty, or not a regular file |

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
| `HFHUB006` | Repository is private or gated; refused in schema version 1 |
| `HFHUB007` | Configured revision could not be resolved to a commit SHA |
| `HFHUB008` | Repository tree metadata missing or incomplete |
| `HFHUB009` | Snapshot download failed |
| `HFHUB010` | Rate limited after the configured retries |
| `HFSYN001` | Local-only completeness check failed after download |
| `HFSYN002` | Downloaded path set does not match Hub tree metadata |
| `HFSYN003` | File size does not match Hub metadata during ingestion |
| `HFSYN004` | Unsafe path rejected: traversal, escape, symlink, or non-regular file |
| `HFSYN005` | Staging tree construction failed |
| `HFSYN006` | Publication rename failed |
| `HFSYN007` | Reference publication failed |
| `HFSYN008` | Manifest write failed |

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
| `HFVER008` | Reference names a missing or inconsistent tree or manifest |

### 5.5 Retention, repair, and recovery — exit `50`

| Code | Condition |
| --- | --- |
| `HFRET001` | Prune plan invalid or refused by validation |
| `HFRET002` | Hub cache revision deletion failed |
| `HFRET003` | Tombstone rename into `.store/trash` failed |
| `HFRET004` | Catalog or reference update failed during prune |
| `HFRET005` | Pre-commit rollback failed; six revisions could not be restored |
| `HFRET006` | Repair download failed verification against the original manifest |
| `HFRET007` | Repair publication failed |
| `HFRET008` | Repair reference switch failed |
| `HFRET009` | Post-grace cleanup failed |
| `HFRET010` | `recover --apply` could not complete a validated plan |

### 5.6 Warnings — never change a `0` exit on their own

| Code | Condition |
| --- | --- |
| `HFDEP001` | An undeclared dependency was detected in repository metadata |
| `HFWRN001` | Temporary over-retention: a deferred prune left six revisions published |
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
  checkpoints rather than per-chunk progress.
- Absolute filesystem paths are printed for operator commands, but every path
  written into a durable artifact is archive-relative (`docs/schemas.md` §1).
