# Decision 033: The check runner is its own module, `preflight.py`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-001`.
- Source: [decision 33 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §7's module list has no home for it, and neither of the two
obvious ones works. `cli.py` is wrong because the runner is not the CLI's:
a mutating command's hard gate uses the identical checks in the identical
order, and a scheduled `sync` must not have to route through the command
surface to reach them. `storage.py` is wrong because the table includes
`configuration`, `credential`, and the four `hub_*` checks, which are not
storage — and because `storage.py` is at 973 lines, near the point where one
module carries everything. So the *primitives* stay in `storage.py`
(`probe_writability`, `same_filesystem_problems`, `is_initialized`) and the
*ordering, outcomes, and gate* are `preflight.py`, which is also where the
normative `docs/cli.md` §2 table lives as `CHECK_ORDER`. Plan §7 updated in
this commit.

Sizing note for the next package: `storage.py` is now 973 lines and
`STO-002` adds to it. The §36 protocol's instruction stands — split
`archive init`/`--inspect` into `archive.py` at that point, with its own
decision and plan §7 amendment. It is not done here because it would mix a
large move into the commit that implements the preflight.

## Later history and current interpretation

The sizing note was acted on in [decision 36](decision-036.md), which separates
archive initialization from storage primitives.

## Provenance and governing evidence

The source entry first appears in
[c8ac36a](https://github.com/wtcross/hfcache/commit/c8ac36a48c216fb9f3535e496c28c83d2a0a6e8b)
(2026-07-25, `STO-001: implement the shared storage preflight and doctor's mount
checks`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../docs/cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/preflight.py](../../src/hfcache/preflight.py),
[src/hfcache/storage.py](../../src/hfcache/storage.py).

Relevant verification:
[tests/unit/test_preflight.py](../../tests/unit/test_preflight.py).
