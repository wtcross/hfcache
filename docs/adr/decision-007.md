# Decision 007: Python 3.14 pin confirmed; `hf-xet` is a required dependency, not an extra

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-24.
- Original work package: `BOOT-002`.
- Source: [decision 7 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §8.1 made the 3.14 pin "subject to final
compatibility validation" and §8.2 left open whether the Xet backend arrives
by default or via the `huggingface_hub[hf_xet]` extra. Both are now settled:
`huggingface-hub` 1.24.0 requires `hf-xet` directly, and `hf-xet` 1.5.2 ships
`cp38-abi3` manylinux wheels that install on CPython 3.14.6 with no source
build. The fallback to 3.13 is not needed. Plan §8.1 and §8.2 updated in this
commit.

Also verified against the locked version, since the plan's design depends on
them: `HfApi.{repo_info,model_info,dataset_info,list_repo_tree,whoami}`,
`snapshot_download`, `scan_cache_dir`, `HFCacheInfo.delete_revisions`, and the
`Cached{Repo,Revision,File}Info` types all exist. `snapshot_download` accepts
`dry_run`, which is what plan §13.2 step 3 needs for pre-download size
estimation — no separate estimation path is required.

## Later history and current interpretation

The library versions and compatibility probes describe the original lockfile
evaluation. The current dependency versions are those in `uv.lock`; this record
does not pin a second version set.

## Provenance and governing evidence

The source entry first appears in
[29a0435](https://github.com/wtcross/hfcache/commit/29a04359a261148c3daff535f9f433eb2e71a5d9)
(2026-07-24, `BOOT-002: pin Python 3.14 and create uv.lock`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/agents/conventions.md](../agents/conventions.md).

Implementation or shipped-artifact evidence:
[pyproject.toml](../../pyproject.toml), [uv.lock](../../uv.lock),
[.python-version](../../.python-version).

Relevant verification:
[tests/system/test_live_hub.py](../../tests/system/test_live_hub.py).
