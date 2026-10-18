> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 043: The recovery report is a run report

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-011`.
- Source: [decision 43 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

`docs/architecture.md` §7.7 requires `recover --apply` to record a
`recovery_report_written` checkpoint, but no document said what that report
is. Three options were considered. Reusing the §6 run report unchanged does
not fit — its body is per-repository sync results, and a recovery resolves
transactions rather than repositories. Treating the journal itself as the
report is a dodge: the journal is evidence of what happened, not a report an
operator reads. Inventing a separate location would put a third kind of file
somewhere `list` and `status` do not look.

So it is `RecoveryReport`, the §6 envelope with a `remediations[]` body,
written to the same `runs/` path — exactly the relationship the verification
report already has to the run report, and for the same reason: one operator
reads all three, so the shared part is one class rather than three that
drift. Documented as `docs/schemas.md` §12 in this commit.

`outcome: "pending"` is recorded for a remediation deliberately left alone —
staging too young to be certainly abandoned. That is a real answer and worth
persisting: an operator reading the report should see that recovery
considered the directory and chose to wait, not that it missed it.

## Provenance and governing evidence

The source entry first appears in
[95f8f81](https://github.com/wtcross/hfcache/commit/95f8f81e518324a4f0ea823771cf0144dd9764af)
(2026-07-25, `STO-011: implement dry-run and apply recovery planning`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/schemas.md](../../../../../schemas.md),
[docs/recovery.md](../../../../../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/recovery.py](../../../../../../src/hfcache/recovery.py),
[src/hfcache/models.py](../../../../../../src/hfcache/models.py).

Relevant verification:
[tests/unit/test_recovery.py](../../../../../../tests/unit/test_recovery.py).
