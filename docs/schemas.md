# hfcache Durable Schemas

| Field | Value |
| --- | --- |
| Status | Normative contract for implementation |
| Derived from | `docs/plan.md` §6.3, §10, §15.2, §16, §18 |
| Work package | `ARC-004` |
| Schema version | All formats begin at `1` |

Every durable artifact `hfcache` writes is versioned JSON on the archive
filesystem. There is no database (`AD-12`). This document defines each format
precisely enough that a reader with no access to the source can validate an
archive, and that a future version can be recognised and refused rather than
misread.

## 1. Conventions

These apply to every file in this document.

| Rule | Requirement |
| --- | --- |
| Encoding | UTF-8, no BOM |
| Serialization | JSON with **sorted keys**, **2-space indentation**, `(",", ": ")` separators, `ensure_ascii=false`, and a single trailing newline. Durable files are indented because operators read and diff them during an incident; the `--json` envelope goes through the same serializer with indentation off, because it is one machine-read line on a pipe (`docs/cli.md` §4) |
| Determinism | Identical logical content produces byte-identical files. Arrays are sorted by a documented key, never by iteration order |
| Timestamps | RFC 3339 UTC with microsecond precision and a literal `Z`: `2026-07-24T20:57:31.123456Z`. Local time is never written |
| Durability | Written to a temporary sibling in the same directory, `fsync`ed, then `rename(2)`d into place; the parent directory is `fsync`ed afterwards |
| Paths | Every path field is relative POSIX, without a leading `/`, without `.` or `..` segments, and validated to stay under its root (`FS-09`). That root is the **archive root**, with one exception: the `tree` and `manifest` fields of a reference (§4) are relative to **`published/`**, because a consumer mounts that directory and no other base resolves for it |
| Digests | Lowercase hex |
| Commit SHAs | Full 40-character lowercase hex; abbreviations are never written |
| Absent values | `null` for a known-but-unset value; a key is never omitted from a written object |
| Byte counts | Logical bytes as reported by `st_size`, not on-disk allocation. Compression and deduplication make physical size a storage-layer property, reported separately and never mixed into these fields |

### 1.1 Version compatibility

Every file carries `schema_version` as its first meaningful field.

- A file whose `schema_version` is **less** than the running version is read
  through an explicit migration path, or the command stops and names the file.
- A file whose `schema_version` is **greater** than the running version is never
  read speculatively. The command stops, reports the file and both versions, and
  changes nothing (`AD-16`). This is what makes a rollback to a previous release
  safe: an older binary refuses newer state instead of misinterpreting it.
- Unknown keys inside a known version are preserved when a file is rewritten and
  reported as an anomaly. They are never silently dropped.

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

`invocation_mode` is `systemd` or `interactive`. `outcome` is `success`,
`success_with_warnings`, or `failed`, and always agrees with `exit_code`.
`success` carries no warnings and `success_with_warnings` carries at least one;
`failed` may also retain non-fatal warnings observed before or alongside the
error.

Per-repository `status` is one of:

| Status | Meaning |
| --- | --- |
| `skipped` | Resolved SHA is already current; nothing to do |
| `ref_moved_to_retained_revision` | Resolved SHA is already retained but was not current; `current.json` was atomically moved to it |
| `published` | A new revision was downloaded, verified, and published |
| `completed_with_warnings` | Published, with non-fatal warnings such as `HFDEP001` |
| `failed` | The repository operation did not complete; publication fields show if a new revision landed before a later retention failure; other repositories may have continued |
| `disabled` | Present in configuration with `enabled = false`; reported for completeness, not processed |

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
that would not parse (`VER-009`): a per-SHA reference carries its SHA in its
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

**RET-010 amendment (2026-09-14, decision 102).** The schema-version-1 reason
`sixth_unique_revision_published` is the legacy name for retention beyond the
configured limit, including the default of three and an explicit reduction from
five. It is preserved for existing readers; it does not assert that six
revisions were present. `retained` and `retained_after` record the actual counts.

`unique_bytes_released_estimate` is **logical** and excludes bytes still
hardlinked by another retained revision. It is explicitly an estimate of logical
release: ZFS snapshots may continue to reference the blocks, so physical pool
space may not change at all (`docs/plan.md` §15.3).

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

Every schema in this document is implemented as a versioned Pydantic model with
`extra="forbid"`, and every writer serializes through one shared deterministic
JSON function so the conventions in §1 cannot drift per call site. The unit suite
holds a golden fixture for each format; a serialization change that alters bytes
without a `schema_version` bump fails the suite.

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
