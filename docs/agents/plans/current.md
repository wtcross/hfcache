# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Job recovery and archive writes](2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Current task | [REL-018](tasks/rel-018-job-recovery-writer-release.md) |
| Blocker | None for REL-018. WEB-033 installed acceptance and strict gate12 pass; release artifacts/build gate next. Production deployment, genuine original-key recovery and scoped writer pilots/backfill remain OPS-028/029; production unchanged |
| Last completed plan | [Ignore root Node dependencies](2026-11-02-plan-root-node-ignore.md) |
| Branch | main |
| Updated | 2026-11-05 |

The user authorizes all eight packages including protected deployment and scoped
production jobs after the plan's safety prerequisites. Preserve archive identity,
original locks/state/handles/credentials, predecessor artifacts and hardening.
Schedules stay disabled and legacy writers masked. No pushes, tags, registry
publication, reboot, NFS disconnection, NAS changes or other-host work.
