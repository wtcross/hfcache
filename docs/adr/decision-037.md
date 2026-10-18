# The `sentinel` check owns "the archive is not initialized"

- Decision identity: 037.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

`docs/cli.md` §2 puts checks 6-12 behind an initialized archive
and has each report `skipped` with that as the reason, which is right for
`doctor`. It is not enough for the gate: `storage primitives` had checks 7 and 8 each
carry `HFMNT008` for the condition, so a mutating command against an
uninitialized archive would have reported two problems, and every later
package would have added another.

Check 6 is the one that actually observes it — the sentinel's absence *is*
the condition, and the sentinel is written last, so nothing below it can be
said either (`FS-23`). It therefore carries `HFMNT005` for the gate and the
checks beneath it skip silently. One missing archive is one problem, with
the code `docs/cli.md` §5.2 already assigns to exactly that condition.

## Later history and current interpretation

This refines [decision 35](decision-035.md): an uninitialized archive is
attributed once to the sentinel check as `HFMNT005`; later dependent checks skip
silently rather than duplicate the earlier `HFMNT008` gate result.

## Provenance and governing evidence

The source entry first appears in
[b8f11c1](https://github.com/wtcross/hfcache/commit/b8f11c120552febe4a75e420b7a7325c4b5eae99)
(2026-07-25, `storage primitives: implement the sentinel check and split archive.py out of
storage.py`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md),
[docs/architecture.md](../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/preflight.py](../../src/hfcache/preflight.py).

Relevant verification:
[tests/unit/test_preflight.py](../../tests/unit/test_preflight.py).
