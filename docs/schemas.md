# hfcache Durable Schemas

| Field | Value |
| --- | --- |
| Status | Normative contract for implementation |
| Schema version | All formats begin at `1` |

Durable archive and operation evidence is versioned JSON. Policy and rendered
TOML are distinct configuration domains. Archive formats live
on the archive filesystem; independent operation control state (§13) and scheduled observation handles (§14) live in private local storage.
There is no database (`AD-12`). This document defines each format
precisely enough that a reader with no access to the source can validate an
archive, and that a future version can be recognised and refused rather than
misread.

## 1. Conventions

These are the archive-model serialization conventions; independent control,
handle and deployment families explicitly identify their own validators and any
family-specific representation below.

| Rule | Requirement |
| --- | --- |
| Encoding | UTF-8, no BOM |
| Serialization | JSON with **sorted keys**, **2-space indentation**, `(",", ": ")` separators, `ensure_ascii=false`, and a single trailing newline. Durable files are indented because operators read and diff them during an incident; the `--json` envelope goes through the same serializer with indentation off, because it is one machine-read line on a pipe (`docs/cli.md` §4) |
| Determinism | Identical logical content produces byte-identical files. Arrays are sorted by a documented key, never by iteration order |
| Timestamps | RFC 3339 UTC with microsecond precision and a literal `Z`: `2026-07-24T20:57:31.123456Z`. Local time is never written |
| Durability | Written to a temporary sibling in the same directory, `fsync`ed, then `rename(2)`d into place; the parent directory is `fsync`ed afterwards |
| Paths | Archive path fields are relative POSIX, without a leading `/`, without `.` or `..` segments, and validated to stay under their root (`FS-09`). Archive paths use the **archive root**, except `tree`/`manifest` in a reference (§4), which are relative to **`published/`** for consumer mounts. API control-state names (§13) use a separate local directory. §14's endpoint is an explicit management authority (`unix:` plus absolute socket path or normalized API URL), not an archive locator |
| Digests | Lowercase hex |
| Commit SHAs | Full 40-character lowercase hex; abbreviations are never written |
| Absent values | `null` for a known-but-unset value; a key is never omitted from a written object |
| Byte counts | Logical bytes as reported by `st_size`, not on-disk allocation. Compression and deduplication make physical size a storage-layer property, reported separately and never mixed into these fields |

### 1.1 Version compatibility

Every file requires explicit version metadata. JSON key order does not make
`schema_version` the first serialized key: keys remain sorted. A mandatory
version field is distinct from optional model defaults.

- A file whose `schema_version` is **less** than the running version is read
  through an explicit migration path, or the command stops and names the file.
- A file whose `schema_version` is **greater** than the running version is never
  read speculatively. The command stops, reports the file and both versions, and
  changes nothing (`AD-16`). This is what makes a rollback to a previous release
  safe: an older binary refuses newer state instead of misinterpreting it.
- Known-version models reject unknown keys and report their locations; they
  never silently drop them. The journal reader is the explicit exception:
  it retains unknown top-level fields separately and preserves them on a
  rewrite. Preservation does not authorize recovery or deletion when that
  command requires supported, unambiguous evidence.

The journal-only preservation rule is enforced by `transactions.read_journal`
and `JournalFile.dump` (decision 20); it does not widen strict model authority.

MCP `MetadataRead` and paged manifest/report projections are transport
objects, not durable formats or a schema widening. Artifact projections are
explicitly marked `projection=true` and omit collections from original headers. Header totals
and report provenance still describe complete validated source evidence. Reassemble
all required pages/collections and validate before treating them as the original
manifest/report; never feed a partial header/page to a durable model or consumer
verification as complete. Exact identity/locator bases remain unchanged. See
[MCP output/pages](mcp.md#metadata-output-and-pages), [decision 125](adr/decision-125.md).

Durable schema migrations must be backward-aware. They must never rewrite all
manifests without both a backup and an explicit migration command. Ordinary
startup, reads and recovery do not authorize such a migration.

## 2. Archive sentinel — `.hfcache-root`

Written exactly once by `archive init`, last in the sequence, after the directory
structure is durable (`FS-23`). Never rewritten.

```json
{
  "archive_id": "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
  "created_at": "2026-07-24T20:57:31.123456Z",
  "created_by": {
    "application_version": "1.0.0",
    "hostname": "hfcachewriter.lab.example.com"
  },
  "layout_version": 1,
  "schema_version": 1
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `archive_id` | UUID string | Must equal `storage.archive_id`; the interlock against writing to the wrong mount (`FS-01`, `FS-03`) |
| `created_at` | timestamp | When initialization completed |
| `created_by` | object | Provenance of the initialization |
| `layout_version` | int | Version of the directory layout in `docs/architecture.md` §5.1 |
| `schema_version` | int | `1` |

## 3. Revision manifest

Path: `published/manifests/<type>/<org>/<repo>/<sha>/<publication-id>.json`

The manifest is the archive's evidence. It is immutable once published (`FS-06`):
its expected sizes and digests are never rewritten to match a later observation,
including by `repair` (`AD-13`, `AD-18`).

```json
{
  "application_version": "1.0.0",
  "commit_sha": "0123456789abcdef0123456789abcdef01234567",
  "dependencies": [
    {
      "confidence": "high",
      "declared": false,
      "detected_id": "meta-llama/Llama-3.1-8B",
      "managed": false,
      "source_field": "base_model",
      "source_file": "README.md"
    }
  ],
  "download_completed_at": "2026-07-24T20:41:02.556000Z",
  "download_started_at": "2026-07-24T20:38:17.004000Z",
  "file_count": 14,
  "files": [
    {
      "path": "config.json",
      "provenance": {
        "cache_root": "canonical",
        "hash_reused_from": null,
        "hashed": true,
        "source": "hub_download"
      },
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size": 812,
      "upstream": {
        "git_oid": "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0",
        "lfs_sha256": null,
        "xet_hash": null
      }
    }
  ],
  "first_observed_at": "2026-07-24T20:38:11.882000Z",
  "hub_endpoint": "https://huggingface.co",
  "huggingface_hub_version": "0.36.0",
  "publication_generation": 1,
  "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
  "publication_mode": "hardlink",
  "published_at": "2026-07-24T20:41:44.310000Z",
  "python_version": "3.14.6",
  "repair": null,
  "repository_id": "organization/model-name",
  "repository_type": "model",
  "requested_revision": "main",
  "schema_version": 1,
  "total_bytes": 486123904,
  "tree": "published/repos/models/organization/model-name/revisions/0123456789abcdef0123456789abcdef01234567/9f14c0b7a2d4423fa0e6b1c8d95e3f27",
  "verification": {
    "algorithm": "sha256",
    "completeness_checked": true,
    "hashed_bytes": 486123904,
    "hashed_objects": 14,
    "outcome": "verified",
    "reused_digests": 0,
    "verified_at": "2026-07-24T20:41:39.771000Z"
  },
  "verified_at": "2026-07-24T20:41:39.771000Z"
}
```

### 3.1 Top-level fields

| Field | Type | Notes |
| --- | --- | --- |
| `schema_version` | int | `1` |
| `repository_id`, `repository_type` | str | `<org>/<repo>` and `model` \| `dataset` |
| `requested_revision` | str | The configured reference, as written by the operator |
| `commit_sha` | str | The resolved immutable SHA that was actually downloaded |
| `publication_id` | str | 32 hex; identifies this materialization |
| `publication_generation` | int | Immutable per-repository ordering key (`AD-05`, `FS-20`) |
| `tree` | str | Archive-relative path of the immutable publication directory |
| `hub_endpoint` | str | Endpoint the content came from |
| `first_observed_at` | timestamp | When this SHA was first resolved for this repository |
| `download_started_at`, `download_completed_at` | timestamp | Bounds of the snapshot download |
| `verified_at` | timestamp | When ingestion hashing completed |
| `published_at` | timestamp | When the instance directory was renamed into place |
| `application_version`, `python_version`, `huggingface_hub_version` | str | The stack that produced this manifest |
| `file_count`, `total_bytes` | int | Must equal `len(files)` and `sum(f.size)` |
| `files` | array | Sorted byte-wise ascending by `path`; see §3.2 |
| `dependencies` | array | Sorted by `(source_file, source_field, detected_id)`; see §3.3 |
| `verification` | object | See §3.4 |
| `publication_mode` | str | `hardlink` \| `copy` |
| `repair` | object \| null | Non-null only when this instance replaces a damaged one; see §3.5 |

### 3.2 `files[]`

| Field | Type | Notes |
| --- | --- | --- |
| `path` | str | Repository-relative POSIX path, spelling and case preserved exactly |
| `size` | int | Logical size in bytes |
| `sha256` | str | Locally computed digest of the bytes as published |
| `upstream` | object | `git_oid`, `lfs_sha256`, `xet_hash`, each `null` when the Hub does not supply it |
| `provenance` | object | How these bytes were obtained; see below |

`upstream` values are **comparison values only**. They are recorded because they
help explain a discrepancy later, never because they substitute for reading the
bytes (`AD-18`).

`provenance`:

| Field | Type | Notes |
| --- | --- | --- |
| `source` | str | `hub_download` \| `cache_reuse` \| `repair_download` |
| `cache_root` | str | `canonical` (`.store/hub`) \| `repair` (`.store/repair/<txn>/hub`) |
| `hashed` | bool | Whether this object was read and hashed during this operation |
| `hash_reused_from` | object \| null | When `hashed` is false: `{ "commit_sha": ..., "publication_id": ... }` naming the verified retained publication whose inode was proven identical |

`hashed = false` is permitted **only** with a non-null `hash_reused_from`
identifying a retained, already-verified publication proven to be the same
physical inode with the same size. Every other case must hash.

### 3.3 `dependencies[]`

| Field | Type | Notes |
| --- | --- | --- |
| `detected_id` | str | Repository or model identifier as written upstream, verbatim |
| `source_file` | str | Repository-relative file the observation came from |
| `source_field` | str | Metadata field, e.g. `base_model`, `base_model_name_or_path` |
| `confidence` | str | `high` \| `medium` \| `low` |
| `declared` | bool | Whether `detected_id` appears in `declared_dependencies` |
| `managed` | bool | Whether `detected_id` is itself a configured repository |

Detection reads static metadata only and never executes repository content
(`AD-07`, `AD-15`). Unparseable or ambiguous metadata is recorded with `low`
confidence rather than guessed at or skipped silently.

### 3.4 `verification`

| Field | Type | Notes |
| --- | --- | --- |
| `algorithm` | str | `sha256` |
| `outcome` | str | `verified` — a manifest is only published after ingestion verification succeeds |
| `verified_at` | timestamp | Completion of ingestion hashing |
| `hashed_objects`, `hashed_bytes` | int | What this operation actually read |
| `reused_digests` | int | Count of `files[]` entries with `hashed = false` |
| `completeness_checked` | bool | Whether the local-only completeness check passed |

### 3.5 `repair`

`null` for an ordinary publication. For a repair instance:

| Field | Type | Notes |
| --- | --- | --- |
| `repair_of` | str | Publication ID of the instance being replaced |
| `repair_of_manifest` | str | Archive-relative path of the original manifest, preserved byte-for-byte |
| `transaction_id` | str | The repair transaction |
| `reason` | str | Stable code plus operator-supplied context |
| `repaired_at` | timestamp | When the replacement instance was published |

A repair manifest copies the original's `files[]` expected `path`, `size`, and
`sha256` set exactly, and preserves `publication_generation`. Only
`publication_id`, `tree`, `provenance`, timestamps, and this block differ.

## 4. References

### 4.1 `refs/current.json`

Path: `published/repos/<type>/<org>/<repo>/refs/current.json`

The one file a consumer must read. Replaced by atomic rename, never edited
(`FS-08`), and written only when the target actually changes.

```json
{
  "commit_sha": "0123456789abcdef0123456789abcdef01234567",
  "manifest": "manifests/models/organization/model-name/0123456789abcdef0123456789abcdef01234567/9f14c0b7a2d4423fa0e6b1c8d95e3f27.json",
  "publication_generation": 1,
  "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
  "repository_id": "organization/model-name",
  "repository_type": "model",
  "schema_version": 1,
  "tree": "repos/models/organization/model-name/revisions/0123456789abcdef0123456789abcdef01234567/9f14c0b7a2d4423fa0e6b1c8d95e3f27",
  "updated_at": "2026-07-24T20:41:44.902000Z"
}
```

`tree` and `manifest` are relative to the **`published/` directory**, which is the
consumer's mount point — not to the archive root. A consumer therefore joins them
directly onto its mount path, and validates that the result stays under it.

### 4.2 `refs/revisions/<sha>.json`

Path: `published/repos/<type>/<org>/<repo>/refs/revisions/<sha>.json`

Identical field set to `current.json`. One exists for exactly the set of retained
SHAs (`FS-11`); it names which publication instance of that SHA is active, which
is what makes a repair a single atomic reference switch rather than a rewrite.

`current.json` always names a SHA that also has a `refs/revisions/<sha>.json`, and
both must agree on `publication_id`.

## 5. Catalog

Derived state (`FS-16`, `AD-12`). Both files are rebuilt from immutable manifests
and references, and are never treated as authoritative.

### 5.1 `catalog/repositories.json`

```json
{
  "archive_id": "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
  "generated_at": "2026-07-24T20:41:45.010000Z",
  "repositories": [
    {
      "current": {
        "commit_sha": "0123456789abcdef0123456789abcdef01234567",
        "publication_generation": 1,
        "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27"
      },
      "enabled": true,
      "first_published_at": "2026-07-24T20:41:44.310000Z",
      "last_published_at": "2026-07-24T20:41:44.310000Z",
      "last_run_status": "published",
      "last_seen_at": "2026-07-24T20:41:44.310000Z",
      "managed": true,
      "repository_id": "organization/model-name",
      "repository_type": "model",
      "requested_revision": "main",
      "revisions": [
        {
          "commit_sha": "0123456789abcdef0123456789abcdef01234567",
          "file_count": 14,
          "publication_generation": 1,
          "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
          "published_at": "2026-07-24T20:41:44.310000Z",
          "total_bytes": 486123904,
          "verification_state": "verified"
        }
      ],
      "upstream_state": "ok",
      "warnings": ["HFDEP001"]
    }
  ],
  "schema_version": 1
}
```

| Field | Notes |
| --- | --- |
| `repositories` | Sorted by `(repository_type, repository_id)` |
| `managed` | Whether the repository is present in the current configuration. A repository removed from configuration keeps its data and appears with `managed: false` (`AD-06`) |
| `enabled` | The configured `enabled` flag; `null` when `managed` is false |
| `current` | `null` if nothing has been published yet |
| `revisions` | Sorted ascending by `publication_generation` — the retention order (`AD-05`) |
| `verification_state` | `verified` \| `unverified` \| `failed` |
| `upstream_state` | `ok` \| `not_found` \| `forbidden` \| `unreachable` \| `unknown`. Never a reason to delete anything (`AD-06`) |
| `last_run_status` | The per-repository status from the most recent run touching it |
| `warnings` | Stable warning codes currently outstanding |

### 5.2 `catalog/verification.json`

```json
{
  "archive_id": "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
  "generated_at": "2026-07-24T21:10:03.400000Z",
  "last_full_verification": {
    "completed_at": "2026-07-24T21:09:58.220000Z",
    "duration_seconds": 612.4,
    "outcome": "clean",
    "report": "runs/20260724T205931Z-4c1e8a55b0d24f1e9a3c7d2b6f80e114.json",
    "started_at": "2026-07-24T20:59:45.800000Z",
    "throughput_bytes_per_second": 794000000.0,
    "unique_bytes": 486123904,
    "unique_objects": 14
  },
  "outstanding_failures": [],
  "repositories": [
    {
      "repository_id": "organization/model-name",
      "repository_type": "model",
      "revisions": [
        {
          "commit_sha": "0123456789abcdef0123456789abcdef01234567",
          "outcome": "clean",
          "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
          "verified_at": "2026-07-24T21:09:58.220000Z"
        }
      ]
    }
  ],
  "schema_version": 1
}
```

`last_full_verification.report` is archive-relative like every field outside a
reference, so it names a path under `runs/` that a consumer cannot resolve from
its own mount. That is intended: it is provenance for the operator, not something
a consumer is expected to follow.

`outstanding_failures` is the archive's health headline: a non-empty array means
`hfcache status` reports the archive as degraded until an operator resolves it.
Entries are never cleared by a later run that simply does not re-check the same
object; they are cleared only by a verification that re-reads it successfully,
by a completed repair, or by the revision ceasing to be retained — a pruned
revision does not exist, and an archive reported permanently degraded over
content it no longer holds carries a signal nobody can clear.

`publication_id` is nullable in both `outstanding_failures[]` and
`repositories[].revisions[]`, for the single case §7 gives: a reference that
would not parse names no publication instance. `commit_sha` is additionally
nullable in `outstanding_failures[]` — and only there, never in
`repositories[].revisions[]` — for §7's single case of a `current.json` that
would not parse, which names no revision either. The clearing rule for such an
entry follows from what re-reads the reference: only `--full` does, so a
narrower run carries the entry forward untouched, a `--full` clears it — or
re-adds it with `first_seen_at` preserved while the reference is still
unreadable — and it leaves with its repository if the repository leaves
`published/`.

`repositories[].revisions[]` is sorted ascending by `commit_sha` and holds at
most one entry per revision — it records the *most recent* outcome, not a
history. The run reports under `runs/` are the history.

Verification writes its durable report before publishing the catalog that names
it. Every non-estimate verification holds the common archive lock from target
resolution through hashing, report write and the entire catalog read/merge/write
(decision 110). Atomic replacement alone cannot preserve unrelated updates when
two writers merge the same old catalog. Persistence helpers require existing
caller ownership and never take a nested lock. This changes no schema-1 field,
format, confidence key or finding-clearing rule.

Both catalogs are derived (`FS-16`). A `verification.json` that is absent or
unreadable means every revision reads `unverified`: derived state may lower the
confidence this application reports and may never raise it.

A revision entry is keyed by `(repository_type, repository_id, commit_sha,
publication_id)`, and the publication id is part of the key rather than
decoration (decision 62). A verification re-reads the bytes of one published
*instance*, and two instances of one SHA are different bytes in different places
— a repair replaces one, and a prune followed by a later republication of the
same SHA produces another. An entry whose `publication_id` is null therefore
raises nobody's confidence: it cannot be attributed to anything on disk, so every
instance reads `unverified` against it.

## 6. Run report

Path: `runs/<YYYYMMDD>T<HHMMSS>Z-<run-id>.json`, one per invocation of a mutating
or reporting command.

```json
{
  "application_version": "1.0.0",
  "archive_id": "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
  "command": "sync",
  "completed_at": "2026-07-24T20:41:46.002000Z",
  "config_fingerprint": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
  "errors": [],
  "exit_code": 0,
  "hostname": "hfcachewriter.lab.example.com",
  "huggingface_hub_version": "0.36.0",
  "invocation_mode": "systemd",
  "outcome": "success",
  "python_version": "3.14.6",
  "repositories": [
    {
      "downloaded_bytes": 486123904,
      "duration_seconds": 207.3,
      "errors": [],
      "file_count": 14,
      "hashed_bytes": 486123904,
      "publication_generation": 1,
      "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
      "pruned": null,
      "repository_id": "organization/model-name",
      "repository_type": "model",
      "requested_revision": "main",
      "resolved_commit_sha": "0123456789abcdef0123456789abcdef01234567",
      "reused_bytes": 0,
      "status": "published",
      "warnings": []
    }
  ],
  "run_id": "4c1e8a55b0d24f1e9a3c7d2b6f80e114",
  "schema_version": 1,
  "started_at": "2026-07-24T20:38:11.500000Z",
  "totals": {
    "downloaded_bytes": 486123904,
    "hashed_bytes": 486123904,
    "published_bytes": 486123904,
    "pruned_logical_bytes": 0,
    "reused_bytes": 0,
    "xet_cache_peak_bytes": 12884901888
  },
  "warnings": []
}
```

`invocation_mode` is `systemd` or `interactive`, describing whether the executing
host process has systemd's `INVOCATION_ID`. It is not proof that a timer, rather
than a manual client, submitted work. A systemd-hosted daemon retains `systemd`
for its domain reports; authenticated submitter and request/operation relationships
belong to separate API receipt metadata, not a new run-report enum or field
([decision 111](adr/decision-111.md)). No durable schema changes here.

`outcome` is `success`,
`success_with_warnings`, or `failed`, and always agrees with `exit_code`.
`success` carries no warnings and `success_with_warnings` carries at least one;
`failed` may also retain non-fatal warnings observed before or alongside the
error.

Per-repository `status` is one of:

| Status | Meaning |
| --- | --- |
| `skipped` | Resolved SHA is already current; no revision download or publication |
| `ref_moved_to_retained_revision` | Resolved SHA is already retained but was not current; `current.json` was atomically moved to it |
| `published` | A new revision was downloaded, verified, and published |
| `completed_with_warnings` | Published, with non-fatal warnings such as `HFDEP001` or supplemental `HFWRN011` |
| `failed` | The repository operation did not complete; publication fields show if a new revision landed before a later retention failure; other repositories may have continued |
| `disabled` | Present in configuration with `enabled = false`; no revision processing |

Supplemental tag/observation capture can refresh independently of revision
processing. Existing statuses and domain exit codes remain unchanged; their
`warnings` can include incomplete capture without implying an absent publication.

A failed result retains planning and completed-transfer facts known before the
failure: its resolved SHA, estimate file count, cache reuse, and
`downloaded_bytes` when the Hub transfer completed before hashing or publication
failed. Run totals sum those per-repository counters across every final status;
downloaded queue-ahead content is therefore reported even when it was not
published in this run.

`pruned` is `null` or `{ "commit_sha", "publication_generation", "logical_bytes" }`
describing the revision this repository's successful publication rotated out.

`xet_cache_peak_bytes` is the observed peak of the writer-local Xet transfer
cache. It is a **local disk** measurement, reported because that cache is bounded
by the writer's root filesystem rather than by the archive dataset.

## 7. Verification report

Path: `runs/<YYYYMMDD>T<HHMMSS>Z-<run-id>.json`, written by `verify` with
`command` set accordingly. Verification reports carry the run-report envelope
fields plus:

```json
{
  "findings": [
    {
      "commit_sha": "0123456789abcdef0123456789abcdef01234567",
      "expected": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "kind": "digest_mismatch",
      "observed": "5f2c8a1d0b7e4936ac5182d4e7f0913b6c8d5a2f1e0b9c8d7a6f5e4d3c2b1a09",
      "path": "model.safetensors",
      "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
      "repository_id": "organization/model-name",
      "repository_type": "model"
    }
  ],
  "mode": "full",
  "scope": {
    "repositories": 2,
    "revisions": 7,
    "unique_bytes_read": 486123904,
    "unique_objects_read": 14
  },
  "throughput_bytes_per_second": 794000000.0,
  "verification_outcome": "failed"
}
```

`mode` is `new`, `full`, or `revision`. `finding.kind` is one of:

| Kind | Meaning |
| --- | --- |
| `missing` | A manifest path has no file in the publication tree |
| `extra` | The publication tree contains a path the manifest does not list |
| `size_mismatch` | Present, but `st_size` differs from the manifest |
| `digest_mismatch` | Present and correctly sized, but the bytes hash differently |
| `not_regular` | The path exists but is a directory, symlink, device, socket, or FIFO |
| `unreadable` | I/O error reading the object |
| `ref_invalid` | A reference names a missing or inconsistent tree or manifest |
| `manifest_invalid` | A manifest fails schema validation or internal consistency |

Two finding fields are nullable, each for exactly one case.
`finding.publication_id` is `null` only for a `ref_invalid` finding about a
reference that would not parse: such a reference names no publication instance,
so there is none to record, and naming whichever instance the filesystem happens
to hold would assert precisely what the unreadable reference failed to say.
`finding.commit_sha` is `null` only for the narrower case of a `current.json`
that would not parse: a per-SHA reference carries its SHA in its
filename, so even unreadable it still names a revision, but `current.json` names
nothing at all. Such a finding carries `commit_sha: null`,
`publication_id: null`, and no `path`, and the model refuses a null `commit_sha`
in any other shape. Every other finding names the revision and the publication
instance it is about.

A verification failure **never** rewrites the manifest, prunes the revision, or
re-downloads over the evidence (`AD-13`, `AD-18`). It records findings, updates
`catalog/verification.json`, and exits `40`.

Full verification builds its read set from unique `(device, inode)` identity with
`samefile` confirmation, so a blob hardlinked into several revisions is read once.
In copy mode every file is read, because identical expected digests in different
trees are different physical objects.

## 8. Prune plan

Produced by `prune --dry-run` and persisted inside the prune transaction before
any mutation.

```json
{
  "cache_revisions_to_delete": ["0123456789abcdef0123456789abcdef01234567"],
  "current": {
    "commit_sha": "fedcba9876543210fedcba9876543210fedcba98",
    "publication_generation": 6
  },
  "generated_at": "2026-07-24T21:20:00.000000Z",
  "plan_id": "b71d0e4a3c8f42d190a6c5b3e7f18d24",
  "reason": "sixth_unique_revision_published",
  "repository_id": "organization/model-name",
  "repository_type": "model",
  "retained": [
    {"commit_sha": "0123...4567", "publication_generation": 1},
    {"commit_sha": "1234...5678", "publication_generation": 2},
    {"commit_sha": "2345...6789", "publication_generation": 3},
    {"commit_sha": "3456...789a", "publication_generation": 4},
    {"commit_sha": "4567...89ab", "publication_generation": 5},
    {"commit_sha": "fedc...ba98", "publication_generation": 6}
  ],
  "schema_version": 1,
  "selected": {
    "commit_sha": "0123456789abcdef0123456789abcdef01234567",
    "file_count": 14,
    "logical_bytes": 486123904,
    "manifest": "published/manifests/models/organization/model-name/0123.../9f14....json",
    "publication_generation": 1,
    "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
    "tree": "published/repos/models/organization/model-name/revisions/0123.../9f14..."
  },
  "unique_bytes_released_estimate": 486123904
}
```

A plan is valid only if `selected` is the lowest `publication_generation` in
`retained`, is not `current`, and `len(retained)` exceeds
`storage.maximum_revisions`. A plan failing any of these is refused, and all
revisions are retained.

**retention amendment (2026-09-14, decision 102).** The schema-version-1 reason
`sixth_unique_revision_published` is the legacy name for retention beyond the
configured limit, including the default of three and an explicit reduction from
five. It is preserved for existing readers; it does not assert that six
revisions were present. `retained` and `retained_after` record the actual counts.

`unique_bytes_released_estimate` is **logical** and excludes bytes still
hardlinked by another retained revision. It is explicitly an estimate of logical
release: ZFS snapshots may continue to reference the blocks, so physical pool
space may not change at all (the architecture contract).

### 8.1 Repository purge plan

Produced by `purge --dry-run` and persisted in a prune journal before mutation:

```json
{
  "cache_revisions_to_delete": [
    "0123456789abcdef0123456789abcdef01234567"
  ],
  "current": {
    "commit_sha": "0123456789abcdef0123456789abcdef01234567",
    "publication_generation": 1
  },
  "generated_at": "2026-08-15T21:00:00.000000Z",
  "plan_id": "b71d0e4a3c8f42d190a6c5b3e7f18d24",
  "reason": "operator_requested_repository_purge",
  "repository_id": "organization/model-name",
  "repository_type": "model",
  "revisions": [
    {
      "commit_sha": "0123456789abcdef0123456789abcdef01234567",
      "file_count": 2,
      "logical_bytes": 486123904,
      "manifest": "published/manifests/models/organization/model-name/0123.../9f14....json",
      "publication_generation": 1,
      "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
      "tree": "published/repos/models/organization/model-name/revisions/0123.../9f14..."
    }
  ],
  "schema_version": 1,
  "unique_bytes_released_estimate": 486123904
}
```

`revisions` is non-empty, sorted by distinct `publication_generation`, contains
`current` exactly once, and corresponds exactly to
`cache_revisions_to_delete`. The logical estimate equals the sum of selected
revision sizes; hardlinks, compression, and ZFS snapshots make physical space
release deliberately unknowable here. The plan's repository must be absent from
configuration when both dry-run and apply resolve their scope (`AD-20`).

## 9. Audit records

### 9.1 Pruned revision — `audit/pruned/<type>/<org>/<repo>/<sha>/<pid>.prune.json`

Written alongside `<pid>.manifest.json`, which is the pruned revision's original
manifest preserved byte-for-byte. Together they are what remains of a revision
after its bytes are gone: enough to prove what was there and why it went.

| Field | Notes |
| --- | --- |
| `schema_version`, `transaction_id`, `plan_id` | Provenance |
| `repository_id`, `repository_type`, `commit_sha` | Identity |
| `publication_generation`, `publication_id`, `tree` | The instance removed |
| `file_count`, `logical_bytes` | What it contained |
| `pruned_at`, `manifest_archived_at` | Timing |
| `retained_after` | The pairs left after one retention removal, or `[]` after repository purge |
| `reason` | `sixth_unique_revision_published` \| `operator_requested_repository_purge` |

### 9.2 Repair retirement — `audit/repairs/<type>/<org>/<repo>/<sha>/<pid>.retirement.json`

| Field | Notes |
| --- | --- |
| `schema_version`, `transaction_id` | Provenance |
| `repository_id`, `repository_type`, `commit_sha`, `publication_generation` | Identity; the generation is unchanged by repair |
| `retired_publication_id`, `retired_tree` | The instance being replaced |
| `replacement_publication_id`, `replacement_tree` | The verified instance now referenced |
| `retired_at`, `grace_expires_at` | `grace_expires_at = retired_at + repair.retired_instance_grace_hours` |
| `reason` | Stable code plus operator context |
| `evidence` | The findings that justified the repair, copied from the verification report |
| `cleanup` | `{ "state": "pending" \| "completed", "completed_at": ..., "quarantine_path": ... }` |

The retired tree and its original manifest stay at their original locators until
`grace_expires_at`, so an in-flight consumer copy can finish (`AD-13`). After
that, a checkpointed cleanup moves the tree to `.store/quarantine/<txn>/` and the
original manifest here.

## 10. Transaction journal

Path: `.store/transactions/<transaction-id>.json`

The journal records what **has already happened and is durable** — never what the
process intends to do. That is what makes recovery a matter of reading evidence
rather than replaying intentions (`AD-14`).

```json
{
  "archive_id": "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
  "checkpoints": [
    {
      "evidence": {
        "path": "published/repos/models/organization/model-name/revisions/0123.../9f14...",
        "file_count": 14
      },
      "name": "revision_tree_renamed",
      "recorded_at": "2026-07-24T20:41:44.310000Z",
      "sequence": 1
    },
    {
      "evidence": {
        "path": "published/manifests/models/organization/model-name/0123.../9f14....json",
        "sha256": "7d2b6f80e1144c1e8a55b0d24f1e9a3c7d2b6f80e1144c1e8a55b0d24f1e9a3c"
      },
      "name": "manifest_published",
      "recorded_at": "2026-07-24T20:41:44.610000Z",
      "sequence": 2
    }
  ],
  "commit_sha": "0123456789abcdef0123456789abcdef01234567",
  "completed_at": null,
  "config_fingerprint": "a1b2c3d4e5f6...",
  "created_at": "2026-07-24T20:38:11.600000Z",
  "error": null,
  "last_checkpoint_at": "2026-07-24T20:41:44.610000Z",
  "operation": "publication",
  "publication_id": "9f14c0b7a2d4423fa0e6b1c8d95e3f27",
  "repository_id": "organization/model-name",
  "repository_type": "model",
  "run_id": "4c1e8a55b0d24f1e9a3c7d2b6f80e114",
  "schema_version": 1,
  "state": "open",
  "transaction_id": "e5f60718293a4b5c6d7e8f90a1b2c3d4"
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `operation` | str | `sync` \| `publication` \| `prune` \| `repair` \| `recovery` |
| `state` | str | `open` \| `committed` \| `failed` \| `needs_operator` |
| `checkpoints` | array | Append-only, `sequence` strictly increasing from 1 |
| `checkpoints[].name` | str | A named boundary from `docs/architecture.md` §7 |
| `checkpoints[].evidence` | object | Archive-relative paths and durable facts that can be re-observed to confirm the checkpoint |
| `error` | object \| null | `{ "code", "message", "at" }`; message is redacted of any secret |

Checkpoint records are **idempotent**: re-recording a checkpoint whose evidence
already holds is a no-op, which is what allows `recover --apply` to be run
repeatedly without harm.

`state = "needs_operator"` is reachable from an unknown journal `schema_version`,
a checkpoint combination that cannot arise from any valid execution, or evidence
that contradicts the filesystem. In that state, automatic recovery stops and
changes nothing (`AD-16`).

## 11. Validation summary

Archive/report models use strict versioned Pydantic validation and the shared
deterministic serializer. Operation receipts/events/result references, scheduled
handles and runtime/release records have independent strict validators and version
checks; runtime/release records are not all VersionedModel subclasses. The
journal-only unknown-top-level-field preservation exception remains explicit.
Golden fixtures detect changed bytes; they do not prove old-reader compatibility.
A shape or validator change requires a deliberate compatibility assessment even
when its version remains 1.

Archive JSON/layout, archive TOML, server/client TOML, HTTP ReadResponse/Envelope,
MCP wire negotiation, MCP metadata projections, API receipt state, scheduled
handles and runtime/release manifests evolve independently. Equal version numbers
do not equate their schemas. Preserve receipts/handles across rollback; absent
old readers cannot prove nonexecution or permit replay. Partial MCP projections
must be fully reconstructed and validated before use as durable artifacts.

The [CLI run-read metadata notice](cli.md#runs-list-and-runs-show) also has an
independent schema. It carries bounded read identity and one opaque page cursor
beside the exact server Envelope; it is neither a durable report nor an operation
receipt. The historical report's policy fingerprint may differ from the current
read wrapper's policy fingerprint.

The [browser build metadata](adr/decision-137.md) has its own strict schema-1
four-field identity: source commit, working-copy state and public build-input
digest. It is an advisory build snapshot, separate from the actual bundle
checksum, protected release index, API identity and all durable archive records.

The [browser wire registry](adr/decision-145.md) is a separate generated build
contract, not a new durable archive version. It reuses public models and precise
projections of the current serializers; stable REST/CLI/MCP bytes are unchanged.
Its audited IR preserves numeric bounds as decimal strings, explicit nullable
unions, required serialized fields, tuple bounds and named semantic checks.
Unsupported schema features or changed unaudited validators fail regeneration.
Generated declarations alone do not validate input: reconstructing runtime
decoders check unknown network data before presentation. Raw integer tokens are
checked before numeric conversion; values outside JavaScript's safe range refuse
without rounding. A domain failure retains its original Envelope and only
separately validated partial payloads. The [API boundary](api.md#browser-wire-boundary)
defines byte/work limits and distinct unavailable/failed/malformed states.

## 12. Recovery report

Path: `runs/<YYYYMMDD>T<HHMMSS>Z-<run-id>.json`, written by `recover --apply`.

The §6 run-report envelope with recovery-specific fields, for the same reason a
verification report is: all three are written to `runs/` and read by the same
operator, so the shared part is one shape.

```json
{
  "application_version": "1.0.0",
  "archive_id": "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
  "command": "recover --apply",
  "completed_at": "2026-07-25T09:14:02.113000Z",
  "config_fingerprint": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
  "errors": [],
  "exit_code": 0,
  "hostname": "hfcachewriter.lab.example.com",
  "huggingface_hub_version": "0.36.0",
  "invocation_mode": "interactive",
  "outcome": "success",
  "python_version": "3.14.6",
  "remediations": [
    {
      "evidence": {
        "quarantine_path": ".store/quarantine/7c1e8a55b0d24f1e9a3c7d2b6f80e114",
        "staging_absent": ".store/staging/7c1e8a55b0d24f1e9a3c7d2b6f80e114"
      },
      "outcome": "applied",
      "reason": "the publication stopped before anything was published, so it rolls back",
      "remedy": "quarantine_staging",
      "transaction_id": "7c1e8a55b0d24f1e9a3c7d2b6f80e114"
    }
  ],
  "run_id": "4c1e8a55b0d24f1e9a3c7d2b6f80e114",
  "schema_version": 1,
  "started_at": "2026-07-25T09:14:01.882000Z",
  "warnings": []
}
```

| Field | Notes |
| --- | --- |
| `remediations[].remedy` | What recovery proposed: `quarantine_staging`, `close_journal`, `wait`, or `operator` |
| `remediations[].outcome` | `applied` when performed, `pending` when deliberately left alone, `blocked` when recovery refused to resolve it |
| `remediations[].evidence` | Re-observable facts, under the §10 key convention: `_path` exists, `_absent` does not |
| `remediations[].transaction_id` | The transaction this entry resolved |

A transaction appears at most once, and the array is sorted by `transaction_id`,
so two runs that did the same work produce the same bytes.

`blocked` is not a failure of recovery. It is recovery correctly refusing to
resolve a state that two valid executions could both have produced
(`docs/architecture.md` §7.9); the run exits `20` and changes nothing.

## 13. Service-private operation control state

This is an independent schema-version-1 control-state family under the configured
local API state directory, default `/var/lib/hfcache/api/`. It is never stored in
`published/`, an archive journal or a derived archive catalog. Its version does
not widen any archive JSON model. The §1 serialization/fsync conventions apply;
the base for its local result references is the service-private state directory.

A receipt is the authoritative admission and idempotency binding. Durable
admission precedes both making work runnable and returning 202. Its principal
is the fixed authenticated credential class, not a token-derived identifier or
individual identity. Only a digest of the idempotency key and a canonical
route/request digest are retained; a raw key, bearer, credential digest/path,
candidate body or replayable command is never written. The admitted archive
UUID/fingerprint and server-generated correlation identify the frozen admission
without changing domain run/report/transaction identities.

### 13.1 Receipt, event and result models

The local files are `<operation_id>.json` for the receipt,
`<operation_id>.result.json` for the terminal Envelope, and a retained `.lock`
inode for control-state serialization. These are flat service-private names;
callers never supply an arbitrary relative path. Every operation ID is a
server-minted 32-character lowercase hexadecimal value independent of domain IDs.
The root directory is owned by the effective service user, mode `0700`; files
are regular single-link service-owned inodes, mode `0600`. Parent directories
must already exist. Components are opened without following symlinks and reads
stay on checked descriptors with bounded bytes and stable inode metadata.

All three models below carry independent `schema_version: 1`, reject unknown
fields and use §1's strict timestamp/digest conventions. The file decoder
requires an explicit integer version, rejects duplicate JSON keys and refuses
unsupported versions rather than guessing from model defaults.

| `OperationReceipt` field | Meaning |
| --- | --- |
| `operation_id` | Server-generated receipt identity and file stem |
| `principal` | Coarse credential class; independent of token value/rotation |
| `key_digest` | Private comparison digest: bearer retains SHA-256 of the validated ASCII key; Basic hashes its versioned stable-subject/key preimage from the [API contract](api.md#admission-idempotency-and-lifecycle). Never exposed by HTTP |
| `request_digest` | SHA-256 of deterministic JSON containing canonical route and validated request mapping |
| `route` | Canonical `/api/v1/` operation route; no query or arbitrary filesystem path |
| `archive_id` | Admitted installed archive UUID |
| `config_fingerprint` | Admitted archive-policy fingerprint; no credentials |
| `state` | Lifecycle state below |
| `created_at`, `updated_at` | Admission and latest durable update times |
| `completed_at` | Null while nonterminal; completion/classification time for succeeded, failed or interrupted |
| `domain_run_id` | Null or existing domain Envelope/run identity; once bound it cannot change, and never becomes the operation ID |
| `transaction_ids` | Distinct domain transaction IDs in reported domain order, initially empty; later updates preserve the existing ordered prefix |
| `result` | Null until succeeded/failed; then the exact `ResultReference` below |
| `events` | Bounded retained suffix of sequenced sanitized events, initially empty |
| `next_event_sequence` | Next monotonically increasing sequence, initially `1` |

`OperationEvent` contains `sequence` (positive integer), `at` (UTC timestamp),
`kind` (bounded lowercase application identifier) and sanitized `message`.
Sequences are contiguous within the retained suffix; dropping its oldest entry
never renumbers the remainder. The complete serialized event, including its
metadata, must fit the configured byte ceiling. An oversized event is refused,
not silently truncated into misleading evidence.

`ResultReference` contains `operation_id`, lowercase `sha256` and positive
`bytes`, binding one result file to the same receipt. Write/fsync the sanitized
exact schema-1 Envelope before replacing the receipt with terminal state and its
reference. The result's run ID must equal `domain_run_id`; zero exit belongs to
`succeeded`, nonzero to `failed`. Fetch verifies identity, byte count, digest and
Envelope coherence before returning it. A result without its corresponding valid
receipt is unexplained state, never proof of completion or deletion authority.

### 13.2 Lifecycle and retention

States are `queued`, `waiting_lock`, `running`, `succeeded`, `failed` and
`interrupted`. A terminal success/failure retains the exact schema-1 Envelope;
an interrupted operation has uncertain execution outcome and must not fabricate
one. Sequenced bounded events are sanitized application evidence, never raw
journald output. Reading any of this state cannot execute a domain command.

| Current state | Permitted next states |
| --- | --- |
| `queued` | `waiting_lock`, `running`, `failed`, `interrupted` |
| `waiting_lock` | `running`, `failed`, `interrupted` |
| `running` | `succeeded`, `failed`, `interrupted` |
| `succeeded`, `failed`, `interrupted` | None |

A failed pre-execution admission may therefore become `failed` with its exact
failure Envelope without claiming domain work ran. Completion timestamps and
result presence must agree with state; invalid transitions are refused. The
receipt is observation authority, not an executable state-machine graph.

Known-version models reject unknown fields. Unknown-version, malformed, unsafe
and unexplained records are preserved and block new admission; healthy records
can still be observed by validated ID. In-memory indexes are derived only from
receipts, never from archive journals. Restart does not make an existing queued/running record runnable. Store opening itself performs no replay/classification. The runner first
reconciles exact surviving verifier state and durable outcome, then explicitly
classifies unresolved nonterminal records interrupted. A retained `running` label alone is not proof of liveness.

**bounded runner and private verifier execution amendment (2026-10-17, decision 115).** The runner now owns
reconcile-before-interruption without replay. Its queue deadline and callable
work remain in memory; no executable request or restart queue is added to this
schema. The separate verifier uses the same receipt/event/reference family under
its own private local root. Its trusted internal admission preserves the exact
API operation ID and uses that ID for private deduplication; the original client
key is never forwarded. Its service-principal class is internal execution
metadata, while the API receipt retains the authenticated submitter class.
Exact terminal Envelopes bridge daemon observation loss without changing domain
report identity. No field, enum or archive schema is widened by this reuse.
Unavailable or unsafe private status leaves an active API receipt intact and
execution admission closed across restarts. Only trusted missing/interrupted
worker evidence permits parent interruption; a transport failure is never proof
that the executor ended. This keeps uncertainty visible without adding a new
durable state enum or weakening the retained-history rule.

Configuration application receipts and private outcomes are conservatively
retained; they do not expire or get evicted to make room. For other operations,
only validated application-owned terminal success/failure history may expire
after the configured retention period (default 30 days). Unexpired bindings
cannot be evicted to satisfy a count cap. Nonterminal, interrupted, malformed,
unknown-version and ambiguous records never expire automatically. Full count or
byte budgets refuse admission; history loss is uncertainty, not nonexecution.

Compatibility is independent of archive format compatibility: a binary predating
this family has no operation-history reader and must not be used to decide a
lost submission's outcome. Preserve the state directory through rollback and
consult it with a compatible server before retrying. Absent predecessor commands/readers are not successful old-format reads or proof
of nonexecution. See [rollback](deployment-centos-stream-10.md#rollback-compatibility)
and [receipt rationale](adr/decision-114.md).

## 14. Scheduled client observation handle

This private local format is independent of archive schemas, API receipts and
client TOML. It preserves observation across scheduled-client restarts, never
queued execution intent. Only fixed `sync` or `verify-full` is permitted; there
is no arbitrary route, request body, credential, token digest, policy fingerprint
or stored domain result. [Decision 121](adr/decision-121.md) records the reason.

| Field | Strict schema-1 value |
| --- | --- |
| `schema_version` | Explicit integer `1`; reject omission, bool/coercion and future versions |
| `command` | `sync` or `verify-full` |
| `endpoint` | `unix:` plus canonical absolute selected socket path, or normalized configured API URL without trailing slash and with prefix retained |
| `archive_id` | Explicit expected canonical archive UUID from scheduled client configuration |
| `principal` | Fixed `rest-writer` namespace; no token/digest binding |
| `idempotency_key` | Generated safe 32-character lowercase hexadecimal key |
| `operation_id` | Null before usable admission, otherwise exact 32-character lowercase hexadecimal ID |

All absolute state-path components are opened without following links, owned by
root or the effective UID, and refuse writable ancestors unless sticky. The final
state-directory component is euid-owned `0700`.
`pending.json` is an euid-owned `0600` regular single-link file, at most 4096
bytes; strict bounded JSON rejects unknown/duplicate fields and unsafe/racing
files. Persist through exclusive `.pending-<32hex>.tmp`, file fsync, atomic rename
and directory fsync. Unexplained temporary evidence remains and blocks resumption.
If a pending file vanishes after inventory, refuse instead of treating the
invocation as fresh.
The retained `.lock` is an euid-owned `0600` empty single-link regular inode;
nonblocking flock covers observation through exact result and completion fsync.
Never remove the lock. No key is transmitted until its handle is durable.
Persist a validated acknowledged operation ID before further observation.

A fresh invocation without a handle may persist one key and send one fixed POST.
Any existing handle permits only authenticated lookup or exact-ID observation,
even after a crash between key fsync and POST. Do not infer nonexecution from
missing remote history, absent ID or expired receipts. Unknown/malformed/future/
mismatched local state is preserved with HFAPI014 / exit 20. Missing explicit
expected archive UUID is also HFAPI014 before HTTP or state allocation. Connectivity and
uncertain POST retain HFAPI019/020, and remote missing/interrupted outcomes retain
HFAPI013/015. No automatic POST replay or new key after uncertainty.

Repeated finite observation windows keep the oneshot active until the exact
terminal Envelope/exit is available. Only that validated terminal evidence permits
owned pending-handle unlink and directory fsync. Same-class token rotation can
recover; changing endpoint/archive/class refuses. Preserve unresolved state on
upgrade/rollback. The compatibility drill must use actual old/current binaries
on throwaway handles; unsupported old behavior never proves nonexecution.

Golden evidence: [scheduled-observation.json](../tests/fixtures/schemas/private/scheduled-observation.json)
and [private handle tests](../tests/unit/test_scheduled_client.py). The format's
version is independent of archive `SCHEMA_VERSION` / `VersionedModel`.
Older releases without scheduled observer support cannot resolve retained handles.
Current readers accept supported schema 1 and refuse future versions without
changing their bytes; retain compatible observation before deliberate retry.

## 15. Rootless runtime deployment profile

The selected release's rendered/runtime.json is independent schema 1, separate
from archive JSON, API receipts and scheduled observation state. The helper pins
its physical release root; inside containers the same selected rendered tree is
read-only at /etc/hfcache/containers. No static /etc profile overrides selection.
[Rootless profile](containers.md#protected-runtime-profile) and
[decision 127](adr/decision-127.md) require exactly schema_version,
service_uid, service_gid, app_image and caddy_image: explicit integer version 1,
positive matching host IDs and exact immutable sha256 image IDs. Fixed helper
role paths/options/secret references are not manifest-supplied execution authority.
The non-secret profile is staged root-owned 0644; the loader requires root
ownership, no group/other writes, a bounded single-link regular no-follow
descriptor, duplicate-free JSON and stable metadata. Caller/runtime-directory
checks fail closed. Release artifact identity has a separate protected manifest;
its settled format/compatibility evidence is recorded with the implementation.
No archive durable format or operation replay rule changes. Installed acceptance
is separately scoped by [deployment status](deployment-status.md).


## 16. Rootless release manifest and artifact index

These independent schema-1 deployment records are separate from runtime.json,
archive JSON and service receipts. [Installer](../scripts/install-container-release.py)
uses duplicate-free/nonfinite-refusing bounded JSON and descriptor-pinned local
no-follow reads with stable metadata excluding access time. Root-protected input
must be a single-link regular file, at most 1 MiB; copied artifacts are bounded
to 16 MiB each. Invalid/future/unknown data refuses without cleanup or activation.

container-release.json has exactly these fields:

| Field | Requirement |
| --- | --- |
| schema_version | Explicit integer 1 |
| version | Three decimal components separated by dots |
| hostname | Bounded ASCII letters/digits/dots/hyphens, first/last alphanumeric |
| service_uid, service_gid | Positive integer host IDs |
| app_image, caddy_image | Exact sha256: plus 64 lowercase hex image IDs |
| source_commit | 40 lowercase hex source commit |
| wheel_sha256 | 64 lowercase hex exact wheel hash |
| files | Required source path→SHA-256 map, at most 1,000 entries |

Source paths are canonical relative POSIX paths, without escape/control/backslash/
symlink or reserved rendered/index/release destinations. The required helper/unit/
template set and fixed renderer remain installer policy; no executable/engine
options or secret values come from arbitrary manifest fields.

artifact-index.json has exactly schema_version (integer 1) and files (relative
path→64-lowercase-hex SHA-256). Its exhaustive map covers copied sources,
container-release.json and rendered units/config/runtime/default+derived seccomp/
provenance, excluding only the index itself. Unknown files, links or directories
are retained and refuse selection. Stage fsyncs files/directories before atomic
rename and parent fsync. Switch revalidates original source hashes, the entire
index and recomputed rendering under the held original local flock, then atomically
changes current and fsyncs its parent. If rename succeeded but directory fsync
fails, exit 20 preserves the new selector and both trees; inspect before retry,
without automatic rollback/cleanup or a false unchanged-state claim. A hash is
artifact identity, not credentials or proof of domain outcome. No automatic cleanup, runtime activation, NAS write or archive schema
migration follows from these formats.

Fixed root-owned libexec/system/user-unit links must point through current to
indexed files; missing, copied or drifted bindings refuse selection. Provisioning
and both-manager reload remain separate guarded operations. The selected physical
rendered profile/config/worker policy and helper must govern actual execution
together; changing a symlink while retaining an unrelated runtime copy is invalid.

## 17. Supplemental discovery records

Independently versioned schema-1 families use the existing strict JSON,
ordering, timestamp, digest and atomic-file conventions. See [discovery](discovery.md)
for field bounds, exact identity, historical authority, coverage and query payloads.
`RepositoryTagSnapshot` contains `kind`, `schema_version`, `archive_id`,
`repository_type`, `repository_id`, `tags`, `observed_at`, `curation_fingerprint`
and `source=installed_config`. `PublicationObservation` contains exact repository,
SHA/publication/generation, manifest locator/digest, extractor identity/time/status,
attributed sources, model variants/dataset declarations and diagnostics. They do
not widen any existing manifest/ref/report/catalog or read-wrapper schema.

The optional `published/metadata/` namespace may be added after initialized writer
preflight. Every record is an independent atomic replacement (decision 133), never
a multi-file transaction. Prior malformed, future-version or unsafe canonical files
are preserved and refuse replacement. Missing metadata means unknown coverage;
selected corrupt metadata refuses. Only `<canonical-name>.tmp-<16 lowercase hex digits>` siblings are ignored by
reads and preserved; unknown sibling names are refused. Historical labels require backup; observations
are rebuildable without changing old evidence. New config/layout/operation kinds
require actual old-binary compatibility drills before claiming rollback support.

### 17.1 Exact record fields and bounds

All objects reject extra fields and coercions. Existing canonical UUID/SHA/digest,
repository type/ID, publication ID, positive generation and UTC timestamp types
apply. All array limits apply before duplicate elimination. Records are bounded
by 16 MiB encoded JSON, depth 32 and 100,000 structural tokens/nodes before
untrusted container allocation; no individual source metadata file can exceed the
extractor limits in discovery. Nullable fields are explicit nulls, never omitted.

| Object | Exact fields |
| --- | --- |
| Tag snapshot | `schema_version: 1`, `kind: repository_tag_snapshot`, `archive_id: UUID`, `repository_type: model / dataset`, `repository_id: ID`, `tags: canonical tag[0..64]`, `observed_at: timestamp`, `curation_fingerprint: SHA256`, `source: installed_config` |
| Publication observation | `schema_version: 1`, `kind: publication_observation`, `archive_id: UUID`, `repository_type: model / dataset`, `repository_id: ID`, `commit_sha: SHA`, `publication_id: ID`, `publication_generation: positive integer`, `manifest_path: archive-relative locator`, `manifest_digest: SHA256`, `extractor_version: bounded identifier`, `observed_at: timestamp`, `status: complete / partial / unsupported / failed`, `sources: Source[0..4096]`, `variants: Variant[0..4096]`, `dataset_formats: identifier[0..64]`, `diagnostics: safe string[0..64]` |
| Source | `path: manifest member`, `sha256: manifest expected SHA256`, `field: task / language / license / base_model / upstream_tags / dataset_config / dataset_split / dataset_feature / format`, `values: string[0..64]`, `evidence: declaration / header / filename` |
| Variant member | `path: manifest member`, `size_bytes: nonnegative integer` |
| Variant | `variant_id: SHA256`, `format: identifier`, `encoding: nullable identifier`, `quantization: nullable identifier`, `quantization_method: nullable identifier`, `bits: nullable integer 1..64`, `group_size: nullable positive integer`, `role: primary / adapter / projector / auxiliary / unknown`, `members: member[1..4096]`, `total_bytes: nullable nonnegative integer`, `completeness: complete / incomplete / unknown`, `evidence: header / declaration / filename`, `source_paths: manifest member[1..64]`, `diagnostics: safe string[0..64]` |

Scoped AWQ/GPTQ observations use declaration evidence, independent
`safetensors`/`pytorch_bin` format and nullable scheme/encoding. Per-column producer
`group_size=-1` becomes null with diagnostic `per_column_group_size`; missing group
size remains null with `group_size_unknown`. No runtime defaults or unquantized
claim are inferred from absence. See [supported layouts](discovery.md#supported-scoped-weight-declarations).

Identifiers are ASCII strings of at most 64 characters; safe diagnostic strings
are at most 512 characters; source scalar values are at most 2048 characters.
Manifest member paths use the existing safe relative repository path grammar.
Sources order by `(path, field, evidence)`; variants by variant ID; members and
source paths by path; dataset formats/diagnostics/values are sorted unique arrays.
Model observations have no dataset formats. Dataset observations have no variants.
Variant IDs hash compact sorted-key UTF-8 JSON with `extractor_version` and
`members` (path/size objects sorted by path), using SHA-256. They are scoped by
exact publication identity in their enclosing observation. All source/member
paths and expected sizes/digests must agree with the authoritative
manifest. Every read also checks archive/repository/SHA/publication/generation and
manifest identity. A total member-work ceiling applies across variants.

### 17.2 Catalog payloads

New strict schema-1 payloads fit inside existing unmodified result/read wrappers.
Every payload includes `schema_version: 1`, `catalog_identity: SHA256`, and
`coverage`. Coverage contains nonnegative counts `repositories`, `tags_known`,
`tags_unknown`, `publications`, `usable`, `partial`, `unsupported`, `failed`,
`missing`, and boolean `technical_required`, `incomplete`; publication states sum
to publication count. Counts cover the scoped candidate set before pagination.

Search adds `total_matches` and bounded `entries`. Each entry has
`repository_type`, `repository_id`, `tags`, `tag_origin` (configured, last_observed,
unknown), nullable `tag_observed_at`, nullable `curation_fingerprint`, booleans
`configured`, nullable boolean `enabled` (unmanaged is null), `archived`,
`matching_variant_count`, nullable
`representative_variant`, and `dataset_formats`. A publication-qualified variant
wraps `commit_sha`, `publication_id`, `publication_generation` and `variant`.
Detail adds one `entry` and bounded `observations` (at most 64), with no nested
variant collection. Each observation summary contains `commit_sha`,
`publication_id`, `publication_generation`, `extractor_version`, `observed_at`,
`status`, `sources`, `dataset_formats` and `diagnostics`, with record bounds above.
Exact selectors constrain these summaries too; missing observations are coverage,
never fabricated summaries. Aggregate source/wire bounds refuse oversized detail
rather than silently omitting declarations. Variant pages add
`total_matches` and bounded publication-qualified `entries`. Facet pages add
`facet`, `total_matches` and bounded entries with `value` and `repository_count`.
Collection limits and cursors stay in the transport's existing page contract;
new payload identity binds all relevant visible rows and coverage. Opaque source
curation fingerprints are withheld as null in read projections; durable snapshots
retain them. Identity hashes only the sanitized visible policy and projection,
never a raw digest derived from suppressed labels or membership. Incomplete
coverage is explicit even when known `total_matches` is zero. No new fields are
added to old inventory payloads or strict read wrappers.

### 17.3 Offline refresh result

The typed `catalog refresh` service payload uses independent strict schema 1
inside the existing Envelope. Writer-only keyed REST admission uses
`/api/v1/catalog/refreshes`, with command `catalog refresh`. The canonical route
discriminates this operation kind without changing existing receipt, result
reference or Envelope fields/versions. Explicit older client route allowlists may
refuse it; preserve control evidence and drain executors before rollback.
Fields are `schema_version`, `archive_id`, `state`, `revision_scope`, `tags`,
`technical`, `curation_fingerprint`, `curation_observed_at`, `counts` and
`repositories`. The curation identity/time describe the actual installed source
read under the lock, even when tag output is disabled. They do not claim that a
failed write persisted a snapshot.

`state` is `complete` when all requested work completed or was intentionally
skipped without warning/error; `partial` when warnings/errors coexist with at
least one written record; otherwise `failed`. Complete processing of an
unpublished repository can explicitly skip technical work without claiming
technical availability. Every count agrees with the per-record rows.

Repository rows are unique and sorted by `(repository_type, repository_id)`, with
`tag_status` (captured, not_requested, skipped_unconfigured, failed),
`technical_status` (complete, incomplete, failed, not_requested,
skipped_unpublished), `publications`, and sorted unique `warnings`/`errors` code
arrays (at most eight codes each). Technical attempts sort by generation/SHA.
Each includes `commit_sha`, `publication_id`, `publication_generation`,
`write_status` (written or failed), nullable `observation_status`, `observed_at`,
`manifest_digest`, and `error_code`. A written record requires exact observation
identity and no error; a failed write has an error and no claimed recorded
observation. Written partial/unsupported/failed observations are successful record
writes with incomplete interpretation and `HFWRN011`.

Counts are `repositories`, `snapshots_written`, `observations_written`,
`records_failed`, `technical_incomplete` and `technical_skipped`.
`technical_incomplete` counts attempted publications without a written complete
observation, including failed writes. Limits are 256 repositories, 512 publication
attempts and 1 MiB serialized result, reserved before the first mutation using
bounded identifiers, fixed statuses/codes and actual generation widths. Aggregate
scope/result exhaustion refuses; it never returns a truncated success. Ordinary
classified failure envelopes remain valid when scope cannot be established.

`technical=true` additionally captures independent §18.1 cards. These fields and
counts retain their original observation/snapshot meanings: card writes and
failures add no publication rows, observation writes or failed-record counts.
Card failures add bounded `HFWRN011`; the aggregate state uses the same rule
above, based on the existing observation/snapshot write counts. A complete
structured observation can coexist with a card warning and partial refresh.

### Observed compatibility of supplemental records

The two supplemental record families have independent schema-1 versions; no old
manifest, reference, report, journal, receipt or wrapper version changes. Actual
installed pre-feature targets parse all 17 unchanged old goldens. Their strict
config/client allowlists can still refuse the new tags field and refresh route.
The old initialization inspector flags the optional directory, while ordinary
inventory and generic stored terminal Envelopes remain readable. Preserve records
and control history, validate actual target behavior and follow
[discovery rollback](discovery.md#guarded-rollback-and-backup); a stable version
number alone does not establish compatibility.

## 18. Web UI and administration design records

**RepositoryCard writer capture §18.1, protected status/configuration
reconstruction and outcomes §18.2, static manifest/bootstrap §18.3,
administrator record §18.4 and managed projections §18.5 are implemented in
unreleased source.** Current archive durable formats above remain unchanged;
source implementation is not installed compatibility or release acceptance.
The card read projection and browser renderer remain later work; capture adds
no card endpoint or browser view.
The independent card/helper/static/bootstrap
families below must each validate their own strict integer version, reject
unknown fields/duplicate JSON keys/coercions, enforce bounds before allocation
and preserve unsupported/unsafe existing evidence. Design alone is not migration
or installed compatibility proof. See decisions [140](adr/decision-140.md),
[141](adr/decision-141.md), [142](adr/decision-142.md),
[143](adr/decision-143.md) and [UI availability](web-ui/README.md).

### 18.1 RepositoryCard schema 1

Path: `published/metadata/cards/<type>/<namespace>/<name>/<sha>/<publication_id>.json`.
Type uses plural `models`/`datasets`; identities use existing grammars.
`source_path` is a repository-relative manifest member key, distinct from the
archive-relative `manifest_path`; neither grants a browser payload locator.
Serialization follows §1 and never modifies old manifests, references or observations.

| Field | Type/constraint |
| --- | --- |
| `schema_version`, `kind` | Integer `1`; literal `repository_card` |
| `archive_id` | Canonical archive UUID |
| `repository_type`, `repository_id` | `model`/`dataset` and validated namespace/name |
| `commit_sha`, `publication_id`, `publication_generation` | Exact full lowercase SHA, 32-hex publication and existing generation grammar |
| `manifest_path`, `manifest_digest` | Canonical archive-relative manifest locator and SHA-256 of exact manifest bytes |
| `source_path`, `expected_source_sha256` | `README.md` and manifest-expected source digest; both null only for absent README |
| `captured_at` | UTC microsecond timestamp |
| `presentation_version` | Literal `markdown-1` |
| `state` | `present`, `absent`, `unsupported`, `oversize`, `unsafe`, `failed` |
| `markdown`, `presentation_sha256` | Sanitized inert source and SHA-256 of its UTF-8 bytes only when present; otherwise both null |
| `diagnostics` | Sorted unique fixed codes below, no rejected source fragments or raw exceptions |

Diagnostic vocabulary: `readme_absent`, `source_oversize`, `presentation_oversize`,
`source_digest_mismatch`, `source_changed`, `invalid_utf8`, `unsupported_markdown`,
`unsafe_content`, `secret_suppressed`, `work_limit`, `read_failed`. At most eleven
diagnostics fit one record. Present requires Markdown (including valid empty
text) and its matching digest; every non-present state withholds both. Absent
requires null source identity; other states bind the manifest-listed README even
when capture fails. All identities/generation/manifest/source digests must agree
with authoritative retained metadata before a card is served or replaced.

Raw source is at most 1 MiB. Presentation UTF-8 bytes and its serialized JSON
string, including its quotes and JSON escaping, are each at most 1 MiB; the
canonical whole record is at most 2 MiB. Encoding uses UTF-8 and the JSON-string
bound uses `ensure_ascii=False`. Shared writer limits remain 64 MiB actual reads,
eight million work steps, 4096 record attempts and 128 MiB aggregate serialized
writes. Failed source reads and capture/write attempts consume these budgets.
Bounded source SHA comparison is README provenance only, never a
verification result. Writer no-follow identity checks and atomic replace/fsync
follow the existing supplemental boundary; unknown/unsafe evidence remains.
Present bodies also revalidate the same `markdown-1` grammar and current
registered/recognized secret absence before read or replacement, under the shared
work budget. A matching presentation digest alone does not make active or unsafe
source acceptable. Revalidation must leave the sanitized source unchanged.

The planned card read projection is independently schema 1 and adds state
`not_captured` for an absent adjunct of an otherwise authorized exact retained
publication. It does not write a synthetic record. Missing exact publication is HTTP 404, not a card
state or fallback. Invalid records remain classified errors. No unsanitized raw
payload or HTML representation is authorized. This projection is separate from
the implemented writer capture. See [discovery](discovery.md#repository-card-design)
and the [capture guide](web-ui/readme-cards.md).

### 18.2 Private helper protocol and outcomes

Protected `status`, editable `config-read` and read-only `config-prepare` are
implemented in unreleased source, together with fixed `config-apply` and
read-only `config-outcome`. Other opcodes remain reserved and denied. Protocol1 exact framing,
kernel credentials/original peer pidfd, protected address binding, independent
deployment/policy schemas and inspection budgets are specified in the
[host contract](host-administration.md). The revision key is a separately
provisioned fixed32-byte root-owned0600 file, never created by a read. Current
`config-read` returns the strict nonsecret editable projection described below
with its configured `archive_id` and opaque full-byte `base_revision`.
`config-prepare` is also implemented as read-only reconstruction: its body is
exactly `{base_revision,edits}`; its private response is `{schema_version,
archive_id,base_revision,candidate_revision,candidate,editable,required_selectors}`.
Candidate text stays private to the API/helper exchange and never enters public
responses or generic receipts. `candidate_revision` is a domain-separated HMAC
over the exact base identity and reconstructed bytes. Stale bases yield the closed
`config-conflict` denial; unknown/mixed/coercive edits refuse. Other opcodes remain
reserved. Non-persisting preparation uses pinned capture and bracketed exact
revalidation; persistent staging/application retains the original configuration
lock. See [decision153](adr/decision-153.md) and [decision154](adr/decision-154.md).

Protocol schema 1 is length-prefixed UTF-8 JSON, at most 2 MiB per encoded frame,
one request per connection, finite deadline and no descriptor passing. Request
fields are `schema_version`, `request_id`, `operation`, strict operation-specific
`body`; response binds the same identity and closed outcome. Operations are
`status`, `config-read`, `config-prepare`, `config-apply`, `config-outcome`,
`schedule-validate`, `schedule-change`, `observer-stop`, `journal-read`.
No operation accepts caller-selected path/command/unit/manager/UID/credential.
Preparation sends managed edits and opaque base token, never a maximal raw
base/candidate pair; helper reconstructs privately. Every encoded response is
independently bounded even when its candidate text satisfies the 1 MiB raw limit.

Private configuration application schema1 state is independent of archive JSON
and generic API receipts. Fixed same-filesystem
`/etc/hfcache/.configuration-applications/<operation-id>/` directories are
root0700; bounded new metadata/material files are root0600, NOFOLLOW and
single-link. Only the retained original predecessor/previous-backup inodes keep
exact0640 root:hfcache metadata and full SID inside the private directory.
A separate HMAC domain with the existing protected key authenticates canonical
state independently of current policy/deployment. Each record retains original
binding hashes, archive/target, request/preview and exact material identities.
No key or TOML document enters a public or generic operation record.

Under the original `.configuration.lock` inode/flock, enforce64 retained
operations/16MiB before mutation. First durably publish root0600
`.configuration.pending` as authenticated minimal original-ID/request-digest
intent. Only then create the operation workspace and persist full private intent
and base/candidate, before fixed candidate/backup effects. Even a crash during
the first private write therefore blocks legacy writers. Matching marker-only
history reads `unknown`/`pending=true`; neither a partial marker nor a missing
workspace permits replay, repair or cleanup.
Phases are `intent`, `staged`, `backup_ready`, `install_intent`, `installed`,
`confirmed`, with explicit file/parent fsync boundaries. Preserve previous known
confirmed backups and the exchanged original predecessor with NOREPLACE moves;
unknown candidate/backup evidence refuses. Remove only the authenticated current
pending marker after durable confirmed state and parent fsync. No reader clears
it or repairs, replays, rolls back or evicts uncertainty. A surviving marker
blocks new writers even if its record is confirmed.

The public schema1 `ConfigApplicationOutcome` has exactly nine required fields:
`schema_version`, `archive_id`, `operation_id`, `request_digest`, `base_revision`,
`candidate_revision`, `config_fingerprint`, `state`, `pending`. The three revision/
fingerprint identities are nullable together, and mandatory for every state
except `unknown`. Its states are `staged`, `unchanged`, `installed_unconfirmed`,
`confirmed`, `conflict`, `unknown`; `pending` is a strict boolean. Missing history
is `unknown`, never proof of nonexecution. Exact disk evidence can classify an
interruption but cannot promote it to confirmed. Authenticated historical
confirmation survives later legitimate edits. See the
[API application contract](api.md#guarded-configuration-application-and-original-outcomes).

### 18.3 Web release manifest and UI bootstrap

The artifact and bootstrap each have independent required schema 1, validated by
strict frozen `Ui*` models. Every declared field is required, including explicit
`null`; unknown fields, boolean/string version coercion and unsupported versions
refuse. They use §1's canonical JSON serialization. Their
[manifest golden](../tests/fixtures/schemas/ui-asset-manifest.json) and
[bootstrap golden](../tests/fixtures/schemas/ui-bootstrap.json) are inert schema
examples, not release artifacts or evidence of a connected archive.

The release `manifest.json` has exactly these fields:

| Field | Contract |
| --- | --- |
| `schema_version` / `kind` | Integer `1` / `hfcache_web_assets` |
| `build` | Required build metadata described below |
| `entrypoint` | `index.html` |
| `meta_identity` | Exactly `ui_base`, `bootstrap_path`, `asset_fingerprint`, `ui_contract`, bound to `__HFCACHE_UI_BASE_V1__`, `__HFCACHE_UI_BOOTSTRAP_V1__`, `__HFCACHE_UI_FINGERPRINT_V1__`, `__HFCACHE_UI_CONTRACT_V1__` respectively |
| `members` | At most4096 complete records, unique and sorted by `path`; required root members `index.html`, `licenses.json`, `THIRD_PARTY_NOTICES.txt` |

Each member has exactly `path`, `bytes`, `sha256`, `mime`. Paths are canonical
relative ASCII, at most 1024 bytes/eight components/255 bytes per component, with
an alphanumeric first character and only alphanumeric, period, underscore or
hyphen thereafter. Assets other than the three required root members belong
under `assets/`. HTML is only `index.html`; plain text is only
`THIRD_PARTY_NOTICES.txt`. Extension/MIME pairs are `.html`/`text/html`,
`.css`/`text/css`, `.js`/`text/javascript`, `.json`/`application/json`,
`.png`/`image/png`, `.webp`/`image/webp`, `.woff2`/`font/woff2` and that single
`.txt`/`text/plain` exception. Reject SVG, source maps, unindexed entries,
symlinks, hardlinked members and special files. Limits are 64 MiB aggregate,
8 MiB/member and 2 MiB manifest; HTML is nonempty. The manifest's SHA-256 is its
external fingerprint, never a recursive field inside itself.

`build` contains exactly `application_version`, `source_commit` (actual 40-hex
parent), `source_snapshot_sha256`, `source_dirty` (strict boolean),
`ui_contract_version` and `rest_api_schema_version` (integer `1`),
`wire_source_digest`, `pnpm_lock_sha256`, `toolchain`, `toolchain_sha256`,
`licenses_sha256`, `notices_sha256`. All digests are lowercase SHA-256.
`toolchain` has exactly `node`, `pnpm`, `typescript`, `vite`, each nonempty
bounded printable ASCII. License and notice digests equal their member records.
Platform cryptographic libraries independently verify toolchain/captured member
bytes at build, startup and browser context boundaries; shape validation does
not pretend to establish file contents. The source inventory is computed before
bundling from actual consumed inputs; no generated self-hash is checked into
source. The installed backend's authoritative wire digest must agree before
assets are accepted. Enabled missing/mismatched assets fail startup. The separate
asset artifact does not add React, Node or frontend requirements to reader wheels.

`GET <effective-prefix>/ui/bootstrap.json` returns a plain object, outside the
REST `Envelope` and strict `/capabilities` contract:

| Field | Contract |
| --- | --- |
| `schema_version` / `kind` | Integer `1` / `hfcache_ui_bootstrap` |
| `ui_contract_version` / `rest_api_schema_version` | Integer `1`, agreeing with `build.metadata` |
| `wire_source_digest` | Installed backend authority, agreeing with `build.metadata` |
| `instance_id` / `authority_epoch` | Same current 32-lowercase-hex process-lifespan identity |
| `configured_archive_id` | Canonical UUID from installed configuration, with no sentinel/health probe |
| `archive_identity_source` | `installed_policy` |
| `config_fingerprint` | Explicit `null` until an implemented authoritative configuration feature supplies a versioned contract |
| `configured_origin` | Canonical ASCII HTTPS origin, at most 4096bytes; no userinfo, path, query or fragment |
| `paths` | Required `public_prefix`, `effective_prefix`, `ui_base`, `bootstrap`, `api_base`, `mcp_base` |
| `user` | Safe exact subject/display and internal permission projection below |
| `build` | Exactly `asset_manifest_sha256` and `metadata` (the manifest's build object) |

Raw prefixes are canonical and at most 1024 UTF-8 bytes. The effective prefix equals
the public prefix, or is empty for a native Unix request. `ui_base`, `bootstrap`,
`api_base` and nonnull `mcp_base` are URI-encoded local paths to the fixed `/ui/`,
`/ui/bootstrap.json`, `/api/v1`, `/mcp/` endpoints; `mcp_base` is `null` when that
transport is unavailable. Never accept a foreign origin or infer paths from a
request header. The browser enforces 32768 bytes, depth 16, 2048 tokens and 128 keys.

`user` has exactly `subject`, `display_name` (equal to stable subject),
`authentication_method`=`basic`, `credential_class`=`rest-writer`,
`rest_capabilities`=`["read","write"]`, and `admin_permissions`. The latter
contains five records sorted by capability: `config-read`, `config-write`,
`host-read`, `observer-stop`, `schedule-write`. Each has exactly `capability`,
`granted`, `effective`, `reason`; effective requires granted. The reason is
`allowed` when effective, `feature_unavailable` when granted but unavailable,
otherwise `not_granted`. An authentication grant alone does not implement a host
or configuration feature. No password/hash, bearer, Hub source, executable
request, live health claim or original operation key belongs in bootstrap.

The implemented host-status read makes `host-read` effective when its internal
capability is granted. This means the endpoint is available, without contacting
the helper at bootstrap. Its separately fetched typed status establishes current
host permissions or an explicit unavailable observation. Configuration/schedule/
observer workflows retain `feature_unavailable` until individually implemented.

Bootstrap is authenticated and `no-store`; it adds no user-management API or
receipt fields. Original operation receipts retain their strict public class
identity and handles without retrospective human attribution. See
[server serving/lifecycle](server.md), [API reference](api.md) and
[artifact/bootstrap decision](adr/decision-147.md).

### 18.4 Protected administrator record schema 1

This restart-only credential is independent of archive JSON and is never a REST,
MCP, bootstrap or operation response. [Server configuration](server.md) selects
exactly one protected file or named systemd credential. Read at most8192bytes,
pin protected descriptors and reject duplicate/unknown fields, coercion, symlinks,
unsafe ownership/modes, multiple links, races or unsupported content before any
password verification. Disabled Basic reads no record. See
[decision146](adr/decision-146.md) and [protected provisioning](web-ui/deployment.md).

| Field | Type/constraint |
| --- | --- |
| `schema_version` | Explicit integer `1`, not boolean/string |
| `subject` | Stable ASCII identifier matching `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`; retained across password rotation |
| `username` | Nonempty printable UTF-8, at most128bytes, no colon |
| `password_hash` | ASCII PHC string, exact `argon2id`, version19, ordered `m=65536,t=3,p=1`, canonical unpadded standard Base64 salt16bytes and output32bytes |

Only those four fields exist. The fixed hash profile is checked before invoking
the maintained verifier, so record parameters cannot select arbitrary resource
work. Provisioning creates a fresh random salt and exclusive mode0600 file; no
plaintext password is serialized. Its serializer follows §1's sorted keys,
two-space indentation, UTF-8 without BOM and single final newline. The independent
[protected-administrator golden](../tests/fixtures/schemas/protected-administrator.json)
freezes those bytes with an inert all-zero salt/output, not a provisioned credential.

Creation differs from archive replacement: exclusively create the new record
without following symlinks, fsync its pinned file and then its parent, and never
overwrite an existing path. A failed creation retains any created file for
inspection; it does not rename, remove or restore credential evidence. Installing
the new record and restarting a service remain separate deployment actions.
Filesystem permissions protect the hash itself
against offline guessing and replacement. The record never includes a bearer,
Hub source, Origin, operation key or host permission. A version/parameter change
needs a reviewed credential migration rather than silent coercion.

Existing operation receipts retain their exact strict class labels and schema.
Basic subject ownership changes only the private original-key digest preimage;
it adds no receipt field or historical attribution record. Keep original handles
through rotation/restart and never replay to reconstruct missing history.

### 18.5 Host status schema 1

`HostStatus` is a strict frozen public observation with required integer
`schema_version: 1`. Every field below is required, including explicit nulls;
unknown keys, bool-as-version, coercions and unsupported versions refuse. The
[golden example](../tests/fixtures/schemas/host-status.json) is illustrative data,
not an installed deployment or a permission grant.

| Field | Contract |
| --- | --- |
| `state` | `supported`, `guarded`, `unknown` or `unavailable` |
| `reason` | Null for supported/guarded; otherwise a closed safe reason from the host model |
| `profile` | `native` or `rootless` for known authority; otherwise null |
| `binding` | Known authority has exact deployment/policy SHA256, bounded release version, source commit/snapshot/dirty, configured archive UUID and literal `/srv/hfcache`; otherwise null |
| `permissions` | Exactly six strict booleans: archive, hub, control, schedule, configuration, observer |
| `permission_reasons` | The same six keys, each `granted`, `policy-denied`, `guard-held`, `profile-unproved`, `authority-unknown` or `helper-unavailable` |
| `facts` | Known authority has guard, archive_mount, units and sync_schedule; otherwise null |

A true permission requires exactly `granted`; unknown/unavailable cannot contain
any true permission or partial binding/facts. Rootless schedule and observer are
always false. `guarded` is equivalent to a held original guard, which also denies
archive actions. `absent` and `inactive` are distinct known guard observations.
Archive mount is `nfs-ro`, `nfs-rw`, `local-ro`, `local-rw` or `absent`; local
fixture evidence never proves live NAS acceptance.

`units` contains exactly `hfcache-sync.service`, `hfcache-verify.service`,
`hfcache-sync.timer`, `hfcache-verify.timer`. Each has required closed `load`,
`active`, `unit_file` values. These are observations, never generic unit selectors.
`sync_schedule` has exactly `state`, `reason`, `revision`, `source`, `on_calendar`,
`randomized_delay_sec`. An `observed` schedule requires null reason, opaque HMAC
SHA256 revision, source `default` or `managed`, and nonempty printable-ASCII
calendar of at most4096 characters; optional delay is printable ASCII of
length1..256. `unavailable` requires `profile-unproved` or `facts-unavailable` and
null revision/source/calendar/delay. Verification scheduling remains display-only.

The normal read wrapper binds the configured archive UUID and command `host status`.
Permission/status observation grants no future action lease, validates no new
calendar, and changes neither archive nor durable operation formats. Independent
private policy/deployment/address records are specified in
[protected host administration](host-administration.md).

The new protected deployment index additionally requires
`selinux_installation_sha256` and the fixed `helper_selinux_policy` source
binding. Its independently installed schema1 SELinux receipt has exactly
`schema_version`, `module`, `domain`, `kernel_policy_sha256` and `labels`.
The module identifies the reviewed source and loaded module at provisioning;
the twelve label roles contain fixed type names and no caller-selected paths.
`engine_locks` has the one fixed type `hfcache_host_helper_engine_lock_t` for
exactly the two existing rootless64B persistent image/layer locks, the fixed
zero-byte stock runtime alive lock and the fixed64B runtime
`/run/user/<protected host UID>/containers/overlay-layers/mountpoints.lock`.
These four ordinary leaves share that role; no additional receipt role or
caller-selected path is introduced.
Runtime checks
use fixed paths and no-follow inode/label metadata; the receipt adds no path
selector or historical inode identity. Current inspection brackets inode/ancestor
identity; it detects no prior otherwise-valid same-type replacement. Absent or
wrong/default-type-recreated locks require independent root provisioning,
including runtime lock recreation after reboot. The role is not a database
`LibpodTmp` attestation; independent default-runtime/configuration/database-epoch
proof and engine-account trust remain required. This role imposes no Podman or
lock-path prerequisite on native-only use.
The separate `engine_shared_memory` role requires only
`hfcache_host_helper_engine_shm_t` for the one existing fixed UID-derived stock
shared-memory segment. It accepts no path/size/lock-count selector or historical
inode identity. Rootless metadata checks require ordinary single-link0600/82488B
account-owned stock state and exact root:root01777 sticky `/dev/shm`; no other
writable ancestry is accepted. Within each capture full metadata rejoins;
command comparison excludes coordination timestamp changes while binding stable
inode/label/principal/mode/link/size/ancestor identity. This attests no shared
contents integrity. Recreation/reboot requires independent root provisioning;
native-only use has no corresponding engine prerequisite.
`application_config` covers shared application-readable configuration leaves,
including helper-owned candidate/backup and retained original predecessor/backup
inodes; only the fixed guarded helper may write them. `configuration_directory`,
`application_state` and `configuration_guard` bind the distinct directory, private
state and lock/pending types. `configuration` retains the separate private helper
authority type. The fixed
`hub_home` and `hub_cache` roles cover writable Hub state, including the mounted
`/var/cache/hfcache` parent and its descendants, with a distinct type that the
helper cannot read. Immutable credential roles retain their separate type.
The authenticated opt-in container path preserves these labels instead of
recursively relabeling the two Hub mounts; root provisioning must prove actual
existing and newly created leaf labels.
The kernel digest and hidden-object labels attest root provisioning. Runtime
checks separately require Enforcing, the exact helper domain and the visible
fixed labels; they do not pretend to rehash the kernel policy or inspect through
masked paths. See the [mandatory SELinux contract](host-administration.md#mandatory-selinux-isolation)
for exact constants, bounds and required installed evidence. These are new
helper-only records, with no change to existing archive/operation formats or
public REST/MCP credential schemas.

### 18.5 Managed configuration projections schema 1

These public DTOs are independent of legacy literal/installed validation and plan
payloads. Every field is required, versions are integer1, unknown/coercive fields
refuse, and identities use existing archive/selector grammars.

| Projection | Required fields |
| --- | --- |
| Configuration read | `schema_version`, `archive_id`, opaque `base_revision`, `editable`, `editable_fields`, `protected_fields` |
| Managed validation | `schema_version`, `archive_id`, opaque `base_revision`, opaque `candidate_revision`, exact `required_selectors`, `valid=true` |
| Managed assessment | `schema_version`, `archive_id`, opaque `base_revision`, opaque `candidate_revision`, exact `required_selectors`, `complete`, nullable `sizing` |

Editable configuration has eleven settings under the existing storage/sync/
verification/repair tables plus complete repository configurations; protected
fields never appear as replacement placeholders. Fixed field metadata has safe
names/descriptions only. Empty scope requires null sizing. Nonempty complete
assessment requires exactly all derived enabled repositories, available upstream
state, resolved immutable SHAs and all numeric sizing facts. Partial/refused sizing
cannot be a complete preview. Public projections contain no candidate text or
secret-dependent full-document hash. See [managed API](api.md#managed-configuration-read-and-assessment-responses).
