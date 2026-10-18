# Python 3.14 pin confirmed; `hf-xet` is a required dependency, not an extra

- Decision identity: 007.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.

## Decision, context, and consequences

The original interpreter/dependency evaluation made the 3.14 pin "subject to final
compatibility validation" and left open whether the Xet backend arrives
by default or via the `huggingface_hub[hf_xet]` extra. Both are now settled:
`huggingface-hub` 1.24.0 requires `hf-xet` directly, and `hf-xet` 1.5.2 ships
`cp38-abi3` manylinux wheels that install on CPython 3.14.6 with no source
build. The fallback to 3.13 was not needed.

Also verified against the locked version, because the transport contract depends on
them: `HfApi.{repo_info,model_info,dataset_info,list_repo_tree,whoami}`,
`snapshot_download`, `scan_cache_dir`, `HFCacheInfo.delete_revisions`, and the
`Cached{Repo,Revision,File}Info` types all exist. `snapshot_download` accepts
`dry_run`, which is what the sync transaction contract needs for pre-download size
estimation — no separate estimation path is required.

## Later history and current interpretation

The library versions and compatibility probes describe the original lockfile
evaluation. The current dependency versions are those in `uv.lock`; this record
does not pin a second version set.

## Provenance and governing evidence

The source entry first appears in
[29a0435](https://github.com/wtcross/hfcache/commit/29a04359a261148c3daff535f9f433eb2e71a5d9)
(2026-07-24, `project bootstrap: pin Python 3.14 and create uv.lock`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[recorded deployment scope](../deployment-status.md).

Implementation or shipped-artifact evidence:
[pyproject.toml](../../pyproject.toml), [uv.lock](../../uv.lock),
[.python-version](../../.python-version).

Relevant verification:
[tests/system/test_live_hub.py](../../tests/system/test_live_hub.py).
