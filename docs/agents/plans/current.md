# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Job recovery and archive writes](2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Current task | [WEB-032](tasks/web-032-job-readiness-and-automatic-recovery.md) |
| Blocker | API-019 complete; WEB-032 ready. Installed prerequisites remain separate |
| Last completed plan | [Ignore root Node dependencies](2026-11-02-plan-root-node-ignore.md) |
| Branch | main |
| Updated | 2026-11-03 |

The user authorizes all eight packages including protected deployment and scoped
production jobs after the plan's safety prerequisites. Preserve archive identity,
original locks/state/handles/credentials, predecessor artifacts and hardening.
Schedules stay disabled and legacy writers masked. No pushes, tags, registry
publication, reboot, NFS disconnection, NAS changes or other-host work.
