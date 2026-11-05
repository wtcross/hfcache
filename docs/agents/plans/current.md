# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Job recovery and archive writes](2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Current task | [OPS-028](tasks/ops-028-install-job-recovery-release.md) |
| Blocker | None for guarded deployment preparation. REL-018 strict release gate4 and source2d matching artifacts pass. Fresh production backup/drain/current-boot runtime provisioning and guarded installation next; genuine administrator recovery and OPS-029 writer pilots/backfill remain pending. Production unchanged |
| Last completed plan | [Ignore root Node dependencies](2026-11-02-plan-root-node-ignore.md) |
| Branch | main |
| Updated | 2026-11-05 |

The user authorizes all eight packages including protected deployment and scoped
production jobs after the plan's safety prerequisites. Preserve archive identity,
original locks/state/handles/credentials, predecessor artifacts and hardening.
Schedules stay disabled and legacy writers masked. No pushes, tags, registry
publication, reboot, NFS disconnection, NAS changes or other-host work.
