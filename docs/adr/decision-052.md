# Decision 052: `storage.write_model` takes the caller's error class, not just its code

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `VER-005`.
- Source: [decision 52 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Decision 46 settled that an error's class and its
code's family must agree, because the exit comes from the class and the
`docs/cli.md` §5 classification comes from the family. `sha256_file` and
`read_model` were fixed to take `error=`; `write_model` was not, and always
raised `SafetyError`.

Every existing call site was therefore mismatched. A failed reference write
reported `HFSYN007` — documented as exit `30` — and exited `20`; a failed
prune audit record reported `HFRET004` and exited `20` rather than `50`.
Both send a scheduler to investigate the mount when the mount is fine and
the run is what failed. `tests/unit/test_publication.py` had pinned the old
behaviour with a comment explaining it, which is how it survived.

`write_model` now takes `error=` with `SafetyError` as the default, and all
nine call sites pair explicitly. `tests/unit/test_storage.py` parses the
call sites out of `src/` with `ast` and checks each pairing against
`taxonomy.classify`, so a new one is checked the moment it lands rather than
at exit time during an incident.

## Provenance and governing evidence

The source entry first appears in
[6c5389b](https://github.com/wtcross/hfcache/commit/6c5389bb95aa95380c13757cd7af9e26d21f2885)
(2026-07-26, `VER-005: persist verification reports and report current health`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/cli.md](../cli.md),
[docs/schemas.md](../schemas.md).

Implementation or shipped-artifact evidence:
[src/hfcache/storage.py](../../src/hfcache/storage.py).

Relevant verification:
[tests/unit/test_storage.py](../../tests/unit/test_storage.py).
