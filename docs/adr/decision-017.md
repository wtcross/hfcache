# Decision 017: `credentials.py` and `identity.py` added to the plan §7 module list

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-003`.
- Source: [decision 17 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Neither existed in the plan's source tree.
`credentials.py` should have been added by `CFG-002` and was missed;
`identity.py` is new here, splitting the *names* the archive uses from the
*paths* built out of them. The split has a purpose beyond tidiness: `paths.py`
joins identifiers straight into filesystem paths, so it needs a module whose
whole contract is that a value which came out of it is safe to join. Plan §7 is
updated in this commit.

## Provenance and governing evidence

The source entry first appears in
[b7e2686](https://github.com/wtcross/hfcache/commit/b7e268626b7e9c5248a00cb437b8d0a2982bfc34)
(2026-07-25, `CFG-003: implement repository identity and safe path mapping`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/configuration.md](../configuration.md).

Implementation or shipped-artifact evidence:
[src/hfcache/identity.py](../../src/hfcache/identity.py),
[src/hfcache/credentials.py](../../src/hfcache/credentials.py).

Relevant verification:
[tests/unit/test_identity.py](../../tests/unit/test_identity.py).
