# Decision 035: A skipped check has three meanings, and the gate reads them differently

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-001`.
- Source: [decision 35 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`docs/cli.md` §2 described `skipped` for two
situations — `--read-only`, and an archive that is not initialized — and
plan §19 requires the same checks to be a *hard* preflight for every
mutating command. Those two cannot both be satisfied by one boolean: an
uninitialized archive is a fine answer for `doctor`, which reports it and
exits `0`, and an impossible one for a command that is about to write.

A third case appeared while implementing rows 2–5. `mount_problems`
short-circuits, so with an absent root nothing is known about its filesystem
type; reporting `pass` there would be the one wrong answer, and reporting
`fail` would invent a failure that was never observed.

So a check carries the reason it did not run, and only the "not initialized"
reason blocks a mutating command — as `HFMNT008`, which `docs/cli.md` §5.2
already defines as a required directory being missing, which is exactly the
condition. A precondition skip adds nothing, because the failure that caused
it is already its own entry in the same report; restating it three times
would make a single missing directory look like four problems.
`require_storage_safety` deliberately takes no `--read-only` option: a
command about to write has no business asking for one, and an option that
silences a check is an option that lets one through. `docs/cli.md` §2
updated in this commit.

## Later history and current interpretation

[Decision 37](decision-037.md) refines the uninitialized-archive result: the
sentinel check owns `HFMNT005` and later checks skip without duplicating it. The
earlier `HFMNT008` attribution in this historical explanation is not the current
gate mapping.

## Provenance and governing evidence

The source entry first appears in
[c8ac36a](https://github.com/wtcross/hfcache/commit/c8ac36a48c216fb9f3535e496c28c83d2a0a6e8b)
(2026-07-25, `STO-001: implement the shared storage preflight and doctor's mount
checks`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/preflight.py](../../src/hfcache/preflight.py),
[src/hfcache/storage.py](../../src/hfcache/storage.py).

Relevant verification:
[tests/unit/test_preflight.py](../../tests/unit/test_preflight.py).
