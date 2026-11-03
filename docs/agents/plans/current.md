# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Job recovery and archive writes](2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Current task | [API-019](tasks/api-019-original-intent-dispositions.md) |
| Blocker | WEB-031 complete; no known source blocker. Production prerequisites need fresh proof |
| Last completed plan | [Ignore root Node dependencies](2026-11-02-plan-root-node-ignore.md) |
| Branch | main |
| Updated | 2026-11-03 |

The user authorizes all eight packages including protected deployment and scoped
production jobs after the plan's safety prerequisites. Preserve archive identity,
original locks/state/handles/credentials, predecessor artifacts and hardening.
Schedules stay disabled and legacy writers masked. No pushes, tags, registry
publication, reboot, NFS disconnection, NAS changes or other-host work.
