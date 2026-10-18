> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 039: `free_space` does not need an initialized archive

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-003`.
- Source: [decision 39 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`docs/cli.md` §2 put checks 6-12 behind an initialized archive in one
sentence covering a range. It is right for 6-11, which all read or write
archive-owned paths, and wrong for 12, which calls `statvfs` on the mount
point. Reporting it as `skipped` would withhold a real answer from the
operator most likely to want it — someone sizing the dataset *before*
running `archive init` — and would do so for no reason, since nothing about
the measurement depends on the layout existing. The sentence now reads 6-11,
with check 12 called out separately. `docs/cli.md` §2 updated in this commit.

## Provenance and governing evidence

The source entry first appears in
[5935ef8](https://github.com/wtcross/hfcache/commit/5935ef8268f37efbea4ed8a490a3ef961fee5630)
(2026-07-25, `STO-003: implement free-space measurement, the reserve, and doctor
check 12`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../../../../cli.md),
[docs/configuration.md](../../../../../configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/storage.py](../../../../../../src/hfcache/storage.py),
[src/hfcache/preflight.py](../../../../../../src/hfcache/preflight.py).

Relevant verification:
[tests/unit/test_storage.py](../../../../../../tests/unit/test_storage.py),
[tests/unit/test_preflight.py](../../../../../../tests/unit/test_preflight.py).
