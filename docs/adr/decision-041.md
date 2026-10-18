# Decision 041: The capability probes stay inside `.store/health/`

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-007`.
- Source: [decision 41 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §14.2 asks `doctor` to prove "a regular file can be
hardlinked between private and published test directories", which reads as
an instruction to create a test directory under `published/`. The probes do
not do that, for two reasons.

The first is that it does not match what publication actually does. A
hardlink is made from a cache blob into `.store/staging` (§14.1 step 4), and
what reaches `published/` is the *tree*, by rename (§13.2 step 15). Nothing
is ever hardlinked into `published/`, so a probe that linked into it would be
proving something the application never does.

The second is that `doctor` takes no lock. A transient probe directory under
`published/repos/` would be visible to a concurrent catalog rebuild or
`verify`, and would be reported by `archive init --inspect` as content the
application did not create. `docs/architecture.md` §5.1 designates exactly
one probe area — `.store/health/probe-<probe-id>/` — and every probe stays
inside it. Check 8 has already proven the whole layout is one filesystem, so
a hardlink and a rename demonstrated there hold for the dataset.

`_remove_probe` now removes the area with `rmtree` rather than entry by
entry, since the capability probes build subdirectories in it. That stays
inside `FS-19`: `probe-<16 random hex>` was created by this process moments
earlier and cannot contain anything the application did not put there.

## Provenance and governing evidence

The source entry first appears in
[9c9a2d1](https://github.com/wtcross/hfcache/commit/9c9a2d169ded11f064184c88e67344f1f94f3d99)
(2026-07-25, `STO-007: implement hardlink and copy publication, and doctor
checks 9-11`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/cli.md](../cli.md).

Implementation or shipped-artifact evidence:
[src/hfcache/publication.py](../../src/hfcache/publication.py),
[src/hfcache/preflight.py](../../src/hfcache/preflight.py).

Relevant verification:
[tests/unit/test_publication.py](../../tests/unit/test_publication.py),
[tests/system/test_live_mount.py](../../tests/system/test_live_mount.py).
