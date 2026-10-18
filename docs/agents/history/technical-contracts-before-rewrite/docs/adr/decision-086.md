> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 086: Guest memory is bounded in the units, not trusted to the host

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-29.
- Original work package: `SYS-003`.
- Source: [decision 86 in the append-only Decisions log](../../../../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

At 02:03:55 on 2026-07-29 the hypervisor
OOM-killed the writer VM mid-way through the 1.5 TB
`moonshotai/Kimi-K3` download. The guest-side evidence: the previous
boot's journal ends abruptly in routine activity with no shutdown
sequence and no wtmp shutdown record; every XFS filesystem replayed its
log on the next boot; kdump was armed yet left no vmcore, ruling out a
guest panic; no OOM or shutdown command inside the guest. The mechanism:
`snapshot_download` streams every byte through the page cache, an
unbounded cache makes the guest touch all of its RAM, and a guest page
once touched is host memory committed for good — the balloon device
negotiates only `STATS_VQ`, so nothing ever returns. The morning
catch-up sync confirmed it directly: 18.3 GiB peak on a 23 GiB guest in
26 minutes. **Decided:** `MemoryHigh=4G` on both service units plus
absolute dirty-page sysctls (`packaging/sysctl.d/hfcache.conf`), so a
run's footprint is a fixed working set regardless of repository size —
validated live at ~4.0 GiB steady while streaming a 209 GB repository.
**Rejected:** `MemoryMax=`, because it kills at the limit and would
trade the host's OOM for one of our own — above `high` the kernel
throttles and reclaims, and a slow sync beats a dead one; per-file cache
hints (`posix_fadvise`) in the application, because the write path
belongs to `huggingface_hub`/`hf_xet`, not to this code, and a cgroup
bound covers both it and the xet chunk cache without a dependency on
library internals; and fixing it host-side only, because the units
should be safe guests on any hypervisor, not just a correctly configured
one. The host retains its half — returning reclaimed pages or not
overcommitting — as handoff item 12. This adds a resource control and
weakens no §22.5 hardening; `check-hardening.sh` passed 23/23 on both
units after the change.

## Later history and current interpretation

[Decision 92](../../../../../adr/decision-092.md) extends the same memory bound to Cockpit-spawned
transient commands. [Decision 94](../../../../../adr/decision-094.md) preserves that working-set
model with one bounded download producer.

## Provenance and governing evidence

The source entry first appears in
[2a2ee59](https://github.com/wtcross/hfcache/commit/2a2ee59df0621b9de0bf58fc75e07ea3a5d71e13)
(2026-07-29, `SYS-003: bound sync and verify page cache; absolute dirty-page
limits`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/security.md](../../../../../security.md),
[docs/deployment-centos-stream-10.md](../../../../../deployment-centos-stream-10.md).

Implementation or shipped-artifact evidence:
[packaging/systemd/hfcache-sync.service](../../../../../../packaging/systemd/hfcache-sync.service),
[packaging/systemd/hfcache-verify.service](../../../../../../packaging/systemd/hfcache-verify.service),
[packaging/sysctl.d/hfcache.conf](../../../../../../packaging/sysctl.d/hfcache.conf).

Relevant verification:
[scripts/check-hardening.sh](../../../../../../scripts/check-hardening.sh).
