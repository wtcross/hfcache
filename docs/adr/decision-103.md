# Decision 103: Only resolved, proven redundant staging quarantine may be released

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-09-14.
- Original work package: `QUA-001`.
- Source: [decision 103 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The operator requested immediate cleanup of the
Overview's quarantine findings. The application now gains an explicit-ID,
dry-run/apply cleanup path; manual archive deletion remains prohibited.
A completed failed publication and its committed recovery checkpoint must
jointly prove each target's provenance. Empty directories carry no content;
remaining files must match the current retained manifest and freshly read
current file bytes before they can be discarded. The complete batch is
validated first, apply holds the writer lock, unresolved journals refuse
cleanup, symlinks and unexplained entries are preserved, and each deletion
rechecks its evidence. Original journals and published content remain intact.
This is a narrow `TX-01` exception: no second cleanup journal is needed for
monotonic removal of already resolved redundant data, since a crash leaves
a subset that the same command can prove again. No durable JSON shape or
checkpoint vocabulary changes. **Rejected:** blanket recursive deletion,
which can erase unique or unresolved evidence; an automatic age-based purge,
which treats age as deletion authority; and a new checkpoint format for
these redundant artifacts, which would introduce recovery and rollback
obligations without preserving additional content. Repair quarantine and
unvalidatable publication trees remain outside this command's scope.

## Later history and current interpretation

[Decision 104](decision-104.md) admits valid early failed-publication journals
with null publication identity when committed recovery proves provenance.
[Decision 105](decision-105.md) limits full checkpoint-order validation to
journals supplying deletion authority. Neither change permits deleting
unexplained or unresolved data.

## Provenance and governing evidence

The source entry first appears in
[1ad4181](https://github.com/wtcross/hfcache/commit/1ad41815d5d57ac5f0ca59513878b9d8a9a9d8f1)
(2026-09-14, `QUA-001: clean proven redundant recovered staging`). The decision
text above preserves the complete reasoning in the current historical log,
including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../docs/architecture.md),
[docs/cli.md](../../docs/cli.md), [docs/recovery.md](../../docs/recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/quarantine.py](../../src/hfcache/quarantine.py),
[src/hfcache/cli.py](../../src/hfcache/cli.py).

Relevant verification:
[tests/unit/test_quarantine.py](../../tests/unit/test_quarantine.py).
