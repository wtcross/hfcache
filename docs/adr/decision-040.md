# Decision 040: `locking.py` added to the plan §7 module list

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-25.
- Original work package: `STO-004`.
- Source: [decision 40 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The lock is neither archive storage nor a `doctor` check: it lives on local
tmpfs under `/run/hfcache` (`AD-17`), it is never reported by `doctor` —
which does not mutate and must not take it — and it is *held* for the
duration of a command rather than checked once. `storage.py` is about
proving and writing the NFS mount and `preflight.py` is about the check
table, so it belongs in neither. Plan §7 updated in this commit.

Two implementation points are worth recording. `flock(2)` rather than a pid
file, because the lock lives on the open file description and the kernel
drops it when the process dies — including under `SIGKILL` or an OOM kill —
so a crashed sync cannot leave a lock that an operator has to clear by hand.
And the holder record inside the file is diagnostic only: nothing reads it
to decide anything, it exists so a command that gives up waiting can say
*who* it waited for. It is cleared on release so a later refusal never names
a process that has already finished.

## Provenance and governing evidence

The source entry first appears in
[0f643a8](https://github.com/wtcross/hfcache/commit/0f643a83a16b863b4cc4e9a5eaab8e762d76f1a0)
(2026-07-25, `STO-004: implement the local exclusive lock every mutating command
takes`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../docs/architecture.md),
[docs/security.md](../../docs/security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/locking.py](../../src/hfcache/locking.py).

Relevant verification:
[tests/unit/test_locking.py](../../tests/unit/test_locking.py).
