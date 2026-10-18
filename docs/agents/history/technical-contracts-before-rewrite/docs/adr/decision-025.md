> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 025: The taxonomy is checked against the documents that define it, in both directions

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-007`.
- Source: [decision 25 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

A table of codes in a document and a table
of codes in a module drift the moment someone edits one. `test_taxonomy.py`
therefore parses `docs/cli.md` §5 and `docs/configuration.md` §8 and asserts
that every documented code classifies as its own section header says, that
every family the code knows about appears in the documents, and that the
`HFCFG` range has no gaps. It reads only the leading cell of a table row:
§5.3's prose cross-references `HFVER002` while explaining how it differs from
`HFSYN003`, and a mention is not a claim about which section a code belongs
to. Classification is by family prefix rather than by a per-code table,
because a code's family already determines its exit and a second table would
be a second thing to keep in sync.

## Provenance and governing evidence

The source entry first appears in
[49e61af](https://github.com/wtcross/hfcache/commit/49e61af233c9cca40a3e2ec09d69086eca31e011)
(2026-07-25, `CFG-007: implement the error taxonomy and the typed JSON
envelope`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../../../../cli.md),
[docs/configuration.md](../../../../../configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/taxonomy.py](../../../../../../src/hfcache/taxonomy.py).

Relevant verification:
[tests/unit/test_taxonomy.py](../../../../../../tests/unit/test_taxonomy.py).
