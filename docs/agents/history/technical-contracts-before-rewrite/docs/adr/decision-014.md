> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 014: The repository-relative path grammar is published

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-003`.
- Source: [decision 14 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`docs/security.md` T-02 required every repository path to be "normalized and
validated to remain under the publication root" but never said against what
grammar, so the requirement could not be implemented twice the same way. Now
written out as a table in `docs/architecture.md` §5.3. The rule that generated
it: reject what can **escape**, allow what is merely awkward. A backslash is
rejected because it is a path separator on a consumer platform, where
`a\..\..\b` traverses; a trailing space or a name like `CON` is left alone,
because this application does not get to decide what a repository may call its
files. Sizes are measured in bytes rather than characters, since `NAME_MAX` is.

## Provenance and governing evidence

The source entry first appears in
[b7e2686](https://github.com/wtcross/hfcache/commit/b7e268626b7e9c5248a00cb437b8d0a2982bfc34)
(2026-07-25, `CFG-003: implement repository identity and safe path mapping`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../../../../architecture.md),
[docs/security.md](../../../../../security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/paths.py](../../../../../../src/hfcache/paths.py).

Relevant verification:
[tests/unit/test_paths.py](../../../../../../tests/unit/test_paths.py).
