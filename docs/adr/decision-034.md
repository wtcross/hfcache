# `archive_root` reports `HFMNT015` as well as `HFMNT001`

- Decision identity: 034.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

`docs/cli.md` §2 row 2 proved "the archive root exists" and named
only `HFMNT001`. A symlink exists, and so does a regular file; neither is an
archive root, and `mount_problems` already reports both as `HFMNT015`.
Putting that under a later check was considered and rejected: `mount_point`
would then fail for a path whose problem is not its mount, and the check
that actually looked at the root would have reported `pass`. Row 2 is now
"exists and is a directory" with both codes, which is what it always
verified. `docs/cli.md` §2 updated.

## Provenance and governing evidence

The source entry first appears in
[c8ac36a](https://github.com/wtcross/hfcache/commit/c8ac36a48c216fb9f3535e496c28c83d2a0a6e8b)
(2026-07-25, `storage primitives: implement the shared storage preflight and doctor's mount
checks`). The decision retains its rationale, alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/preflight.py](../../src/hfcache/preflight.py),
[src/hfcache/storage.py](../../src/hfcache/storage.py).

Relevant verification:
[tests/unit/test_preflight.py](../../tests/unit/test_preflight.py).
