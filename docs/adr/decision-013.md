# Decision 013: A reference's paths are relative to `published/`, every other artifact's are archive-relative

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `CFG-003`.
- Source: [decision 13 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`docs/schemas.md` §1 said every path
field is archive-relative; §4.1 said a reference's `tree` and `manifest` are
relative to `published/`, and its worked example was written that way. Only one
can hold. `published/` wins, because it is not a stylistic choice: a consumer
mounts `published/` and nothing else, so an archive-relative `published/repos/…`
would resolve to `<mount>/published/repos/…`, which does not exist. The rule is
now stated once with its exception, in `docs/schemas.md` §1 and in `FS-09`, both
amended in this commit. `RepositoryLayout` exposes the two forms as separate
methods — `tree_reference` and `manifest_tree_field` — so the distinction is
made by the type of artifact being written rather than by a caller remembering
which base applies.

Extended at `CFG-004`: the prose was right and three *examples* were wrong.
The manifest (§3), prune plan (§8), and journal (§10) examples had all copied
the reference's published-relative form into fields their own prose calls
archive-relative, so every one of them was missing the `published/` prefix.
Corrected in the `CFG-004` commit. The rule that decides the base is narrow:
a field is published-relative only when a consumer has to resolve it, which
is true of exactly the reference's `tree` and `manifest`. Everything else is
archive-relative, including `catalog/verification.json`'s `report`, which
names a path under `runs/` that a consumer deliberately cannot follow.

## Later history and current interpretation

The source was extended by CFG-004 to correct durable-schema examples as well as
the original path-base rule. Both parts are preserved below.

## Provenance and governing evidence

The source entry first appears in
[b7e2686](https://github.com/wtcross/hfcache/commit/b7e268626b7e9c5248a00cb437b8d0a2982bfc34)
(2026-07-25, `CFG-003: implement repository identity and safe path mapping`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

The source entry was subsequently amended in
[2133496](https://github.com/wtcross/hfcache/commit/21334967781eef8ee37600ed63fad4e42e404180)
(2026-07-25, `CFG-004: implement the durable manifest and report models`); the
backfill retains the amended text rather than restoring superseded wording or
private environment values.

Current governing documents: [docs/schemas.md](../schemas.md),
[docs/architecture.md](../architecture.md).

Implementation or shipped-artifact evidence:
[src/hfcache/paths.py](../../src/hfcache/paths.py).

Relevant verification:
[tests/unit/test_paths.py](../../tests/unit/test_paths.py).
