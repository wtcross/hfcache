# Decision 085: The storage contract becomes server-agnostic, and evaluation gets a first run

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-28.
- Original work package: `DOC-006`.
- Source: [decision 85 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

The NAS half of the system existed
only as plan §20's TrueNAS 25.10.5 steps plus the deliberately unwritten
`docs/truenas.md` — right for the lab, nothing for anyone else, and the
largest finding of the 2026-07-28 portability review. Two documents
rather than one, because the audiences differ: `storage-requirements.md`
is a contract a storage administrator reads standalone (any NFSv4.2
server; TrueNAS "Mapall" stated beside its Linux `all_squash` equivalent;
the numeric ids explicitly the server's choice), while `quickstart.md` is
a procedure for someone with a laptop and an hour. The quickstart
promotes recovery §6's loopback archive rather than inventing a new
path, because §6 was exercised at `REL-004` and an exercised recipe
beats an invented one; the checkout adaptation states its deltas (own
identity, hand-made `/run/hfcache`, reduced free-space reserve) and
redirects deployed hosts back to §6. The alternative rejected: relaxing
`FS-02` to allow a local archive root for evaluation. The mount check is
load-bearing — a missing mount must fail rather than silently land on
the VM's root filesystem — and a loopback export meets the requirement
honestly on one machine, so the requirement stands.

## Later history and current interpretation

The mount requirement remains NFS/NFS4; server-agnostic requirements do not
authorize a local-filesystem bypass. The quickstart and recovery recipe govern
their respective evaluation and deployed-host audiences.

## Provenance and governing evidence

The source entry first appears in
[6476c9b](https://github.com/wtcross/hfcache/commit/6476c9b8f85bc4c2fdfd0ccef8bb2711322adadd)
(2026-07-28, `DOC-006: storage requirements, quickstart, and README
requirements`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents:
[docs/storage-requirements.md](../../docs/storage-requirements.md),
[docs/quickstart.md](../../docs/quickstart.md),
[docs/recovery.md](../../docs/recovery.md).

Implementation or shipped-artifact evidence:
[src/hfcache/storage.py](../../src/hfcache/storage.py),
[src/hfcache/preflight.py](../../src/hfcache/preflight.py).

Relevant verification:
[tests/unit/test_preflight.py](../../tests/unit/test_preflight.py),
[tests/system/test_live_mount.py](../../tests/system/test_live_mount.py).
