# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Job recovery and archive writes](2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Current task | [OPS-029](tasks/ops-029-enable-manual-archive-jobs.md) |
| Blocker | None for next authorized step. REL-020 strict gate and matching0.3.4 artifacts pass. OPS-029 resumes fresh protected backup/drain/temporary RO stage+selection, matched writer startup/preflight, successful affected Sync/refresh and one bounded backfill. Production currently writer0.3.3/RW/Enforcing; original retired_unknown preserved |
| Last completed plan | [Ignore root Node dependencies](2026-11-02-plan-root-node-ignore.md) |
| Branch | main |
| Updated | 2026-11-05 |

The user authorizes all eight packages including protected deployment and scoped
production jobs after the plan's safety prerequisites. Preserve archive identity,
original locks/state/handles/credentials, predecessor artifacts and hardening.
Schedules stay disabled and legacy writers masked. No pushes, tags, registry
publication, reboot, NFS disconnection, NAS changes or other-host work.
