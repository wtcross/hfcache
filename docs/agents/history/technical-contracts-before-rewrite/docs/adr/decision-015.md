> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 015: Collision folding is deliberately stricter than any one filesystem

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-003`.
- Source: [decision 15 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

T-02 requires rejecting two manifest entries that
"resolve to the same on-disk path — including via case or Unicode-normalization
collision" without fixing a fold. The fold is NFC plus `str.casefold`. Full case
folding also maps some ligatures, so `ﬁle` and `file` are reported as colliding
even though nothing would really merge them. That over-rejection is the intended
direction: refusing a pair of names is visible, explainable, and recoverable by
an operator, while publishing a tree in which two manifest entries resolve to
one file is silent and corrupts the thing being archived (`AD-16`). NFKC is not
applied — it folds superscripts and width variants that no consumer could
confuse, and would refuse legitimate names for nothing.

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
