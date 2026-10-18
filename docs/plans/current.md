# Current plan

| Field | Value |
| --- | --- |
| State | Active |
| Active plan | [Container worker listener](2026-10-18-plan-container-worker-listener.md) |
| Next task | [REL-013](tasks/rel-013-container-worker-artifacts.md) |
| Blockers | None; REL-013 activation waits for the completed OPS-017 commit |
| Updated | 2026-10-18 |

OPS-017 completed the confined worker-owned listener, source/dirty-preview proof
and full build gate. REL-013 remains pending until its source predecessor commits;
it will build clean 0.2.1 artifacts and prove their actual fixture behavior.
Existing 0.2.0 partial-release evidence and local tag remain history. Later tasks
wait for committed predecessors. Preserve the original lock guard, read-only
NAS, writer masks, secrets/state and hardening; no NAS file I/O/jobs, other-host
changes or remote publication are authorized.
