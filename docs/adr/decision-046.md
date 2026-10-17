# Decision 046: A hashing failure's error class must match its code's family

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `HUB-007`.
- Source: [decision 46 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`sha256_file` took the caller's `code` and always raised
`IntegrityError`, so `publication.stage_file`'s three calls — which correctly
pass `HFSYN005` — would have exited `40` for a condition `docs/cli.md` §5.3
classifies as `30`. Nothing had surfaced it yet, because publication is not
reachable from a command until `HUB-009`; it would have arrived as an
operator being told the archive is corrupt when a download failed.

Two ways an exit is determined coexist in this codebase: `HfcacheError`
subclasses carry one as a class attribute, and `taxonomy.classify` derives
one from the code's family. They are not redundant — the first is what a
raise site produces and the second is what the published tables promise — so
they have to agree, and nothing was making them. `sha256_file` now takes
`error` alongside `code`, which is exactly the shape decision 19 settled for
reading a durable artifact, and `tests/unit/test_hashing.py` asserts
`caught.value.exit_code == classify(code)` for every pairing used in `src/`.

A single `error_for(code)` factory was considered and rejected: it would let
a raise site name a code from a family it has no business raising and get a
plausible-looking error back. Passing both makes the pairing visible at the
call site, which is where a mistake is legible.

## Provenance and governing evidence

The source entry first appears in
[45f1ccf](https://github.com/wtcross/hfcache/commit/45f1ccf55656760db38e5242f3ef827bd07ef6de)
(2026-07-26, `HUB-007: hash every newly introduced unique physical object`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../../docs/cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/hashing.py](../../src/hfcache/hashing.py),
[src/hfcache/taxonomy.py](../../src/hfcache/taxonomy.py).

Relevant verification:
[tests/unit/test_hashing.py](../../tests/unit/test_hashing.py),
[tests/unit/test_taxonomy.py](../../tests/unit/test_taxonomy.py).
