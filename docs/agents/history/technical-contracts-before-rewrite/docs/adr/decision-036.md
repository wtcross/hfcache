> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 036: `archive.py` split out of `storage.py`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-002`.
- Source: [decision 36 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The
`STO-001` sizing note said to do this before adding to a 973-line module,
and the cut turned out to be a real boundary rather than a line count.
`storage.py` is now what a command must *prove about the mount* and the
primitives that *act on it durably* — the mount table, atomic writes, the
write probe, the same-filesystem proof, and reading the sentinel.
`archive.py` is the one command that brings an archive into being: the
known-empty-layout walk, `published/` adoption, `--inspect`, and
`initialize_archive`. Each is now under 550 lines and neither imports the
other's concerns.

`_read_sentinel` became `storage.read_sentinel` in the move, because both
sides need it: `archive.py` to tell an initialized archive from unknown
content, and `preflight.py` for check 6. It reads the archive's identity off
the mount, which is a storage question; deciding what a mismatch *means* is
still the caller's. `tests/unit/test_storage.py` split the same way, into
`test_archive.py` for the module and `test_archive_init.py` — which already
existed — for the command. Plan §7 updated in this commit.

## Provenance and governing evidence

The source entry first appears in
[b8f11c1](https://github.com/wtcross/hfcache/commit/b8f11c120552febe4a75e420b7a7325c4b5eae99)
(2026-07-25, `STO-002: implement the sentinel check and split archive.py out of
storage.py`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../../../../architecture.md),
[docs/cli.md](../../../../../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/archive.py](../../../../../../src/hfcache/archive.py),
[src/hfcache/storage.py](../../../../../../src/hfcache/storage.py).

Relevant verification:
[tests/unit/test_archive.py](../../../../../../tests/unit/test_archive.py),
[tests/unit/test_storage.py](../../../../../../tests/unit/test_storage.py).
