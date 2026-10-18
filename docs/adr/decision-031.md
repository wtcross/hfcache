# `published/` adoption compares ownership against the archive root

- Decision identity: 031.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.

## Decision, context, and consequences

Initialization and `FS-22` adopt a pre-existing `published/` only when its
ownership and mode match the storage contract. NAS identity mapping rules out
the obvious local-account comparison: the Mapall writer export presents NAS-side ids
(`3001:3002`) that have no local account, so there is nothing local to
compare `st_uid` with. "The same identity owns `published/` as owns the
archive root" is the same rule in a form the writer can evaluate, and it
fails exactly when the intended one would. The policy takes two
`os.stat_result` values rather than two paths, which is what lets it be
tested for identities this host cannot create — `<operator>` cannot `chown` to
3001. `docs/architecture.md` `FS-22` updated.

## Provenance and governing evidence

The source entry first appears in
[5a6fa18](https://github.com/wtcross/hfcache/commit/5a6fa1816bedacf014f135468241f99ca42cca60)
(2026-07-25, `storage primitives: implement guarded one-time archive initialization and
inspection`). The decision retains its rationale, alternatives and consequences.

The source entry was subsequently amended in
[a0bcee4](https://github.com/wtcross/hfcache/commit/a0bcee4f3facf69c12f3f3d61f70a50417b5c2be)
(2026-07-28, `documentation maintenance: scrub environment specifics into placeholders`); the
backfill retains the amended text rather than restoring superseded wording or
private environment values.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/archive.py](../../src/hfcache/archive.py).

Relevant verification:
[tests/unit/test_archive.py](../../tests/unit/test_archive.py),
[tests/unit/test_archive_init.py](../../tests/unit/test_archive_init.py).
