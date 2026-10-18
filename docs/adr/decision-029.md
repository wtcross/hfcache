# `archive init --inspect` exits `0` for an already-initialized archive

- Decision identity: 029.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

`docs/cli.md` fixed no exit code for `--inspect`.
Its two real uses both want a non-zero on a bad answer: confirming a target
is clean before initializing, and confirming a failed initialization left
only known partial paths so a retry is safe. But a healthy initialized
archive is also "not initializable", and exiting `20` there would make the
command useless as a routine check. So `--inspect` exits `0` when the target
is initializable **or** correctly initialized, and `20` when it is neither —
unknown content, symlinks, the wrong filesystem, or a malformed or
mismatched sentinel. Recorded in `docs/cli.md` §2.

## Provenance and governing evidence

The source entry first appears in
[5a6fa18](https://github.com/wtcross/hfcache/commit/5a6fa1816bedacf014f135468241f99ca42cca60)
(2026-07-25, `storage primitives: implement guarded one-time archive initialization and
inspection`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/archive.py](../../src/hfcache/archive.py).

Relevant verification:
[tests/unit/test_archive.py](../../tests/unit/test_archive.py),
[tests/unit/test_archive_init.py](../../tests/unit/test_archive_init.py).
