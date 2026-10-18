# Decision 055: A crashed sync run journal closes; it does not stop the machine

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `SYNC-003`.
- Source: [decision 55 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Before this package nothing produced a `sync`
journal, and `recovery._remediation` fell through to its final refusal for
one: `HFTXN004`, blocked, operator decides. A test asserted exactly that.
Once `sync` actually opens the §7.6 journal, that behaviour becomes
unusable — every interrupted run would leave the archive refusing writes
until a person cleared a journal about which nothing is ambiguous, and
unattended operation is the point of the whole design (`AD-01`).

§7.6 already said why it is not ambiguous: "the per-repository journals are
the authority; the run journal exists to correlate them and to prove that
reconciliation happened before Hub contact." Every mutation a run made is
inside a publication or prune journal that has its own remedy. So the
resolution is `close_journal`, whatever checkpoint the run reached, and
`docs/architecture.md` §7.6 and §7.7 are amended in this commit to say so.

Recovery deliberately does **not** roll a run forward through checkpoint 5,
even though §7.7 permits rebuilding a catalog. Plan §13.1 step 10's rebuild
reads *configuration* to decide which repositories are managed (`AD-06`),
and recovery takes no configuration — rebuilding without it would mark every
configured repository unmanaged, turning a merely stale derived file
(`FS-16`) into an actively wrong one. The next sync rebuilds it correctly.
The replaced test now provokes the genuine no-resolution case instead: a
`recovery` transaction that itself crashed, which §7.7 gives no resolution
for and which is still `HFTXN004`.

Two smaller consequences, both load-bearing. The run journal excludes
*itself* from reconciliation — `TX-01` opens it before the run may act, so
it is unfinished for the whole run and a transaction cannot recover itself;
`plan_recovery` gained `exclude` for that one caller. And a crash inside a
run now leaves **two** open journals rather than one, which is what the
filesystem has always implied and what six recovery tests had to start
saying out loud: they now ask for the remedy of the operation they are about
rather than taking `remediations[0]`.

## Later history and current interpretation

The run journal remains correlation evidence; per-operation journals govern
recovery. [Decision 94](decision-094.md) later permits several downloaded
publication journals under that same run lock.

## Provenance and governing evidence

The source entry first appears in
[7327f9c](https://github.com/wtcross/hfcache/commit/7327f9c3e2aa80ef825b7d42560de9d1a234cfdc)
(2026-07-26, `SYNC-003: reconcile unfinished journals before a run reaches the
Hub`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../architecture.md),
[docs/recovery.md](../recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/sync.py](../../src/hfcache/sync.py),
[src/hfcache/recovery.py](../../src/hfcache/recovery.py).

Relevant verification:
[tests/unit/test_synchronize.py](../../tests/unit/test_synchronize.py),
[tests/unit/test_recovery.py](../../tests/unit/test_recovery.py).
