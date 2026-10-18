> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 044: `projected_publication_bytes` is measured under the configured mode, not hypothetically under copy

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `HUB-004`.
- Source: [decision 44 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`docs/cli.md` §2 asked
`plan` for "the projected publication bytes in copy mode", which reads two
ways: the field means something only in copy mode, or the field always
reports what copy mode *would* cost. The second was rejected. `plan` is the
command the dataset quota is sized from, so the number it reports has to be
the number the archive will actually consume — and under the default
`hardlink` mode that is zero, because a hardlink points at a cache blob
already on the dataset (`AD-11`).

Nothing is lost by not reporting the hypothetical: copy mode's cost is
exactly `logical_bytes`, which is in the same payload. A deployment weighing
the switch reads it off the field beside it. `publication_mode` is reported
with it so the zero is explicable rather than looking like a missing
measurement. `docs/cli.md` §2 and §4.1 updated in this commit; §4.1 now names
every field of the payload rather than summarizing it, since automation keys
on them.

The cost model itself is `publication.projected_publication_bytes` rather
than a conditional at the call site, because plan §19 item 9 makes the same
number part of a sync's free-space gate. An estimate an operator reads and a
reserve a sync enforces that disagreed about what publication costs would be
a capacity failure discovered mid-download.

## Provenance and governing evidence

The source entry first appears in
[e7561d1](https://github.com/wtcross/hfcache/commit/e7561d152b0bf6e9f0bb724366f433eee4f7f7ff)
(2026-07-26, `HUB-004: retrieve the repository tree and cost a download without
one`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../../../../cli.md),
[docs/architecture.md](../../../../../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/publication.py](../../../../../../src/hfcache/publication.py),
[src/hfcache/cli.py](../../../../../../src/hfcache/cli.py).

Relevant verification:
[tests/unit/test_readonly_commands.py](../../../../../../tests/unit/test_readonly_commands.py).
