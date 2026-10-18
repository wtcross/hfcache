# Current plan

| Field | Value |
| --- | --- |
| State | Active |
| Active plan | [Container worker listener](2026-10-18-plan-container-worker-listener.md) |
| Next task | [REL-013](tasks/rel-013-container-worker-artifacts.md) |
| Blockers | None; REL-013 stays pending until completed OPS-019 commits |
| Updated | 2026-10-18 |

OPS-019 is completed in this package with accepted UBI source and actual dirty
preview/full-gate evidence. No task is in progress until its commit permits
REL-013 activation. That task must build both clean UBI images and repeat clean
acceptance; superseded Debian evidence and stopped/failed attempts stay preserved.
Deployed/tagged 0.2.0 and hold22 remain unchanged. Preserve the original lock
guard, read-only NAS, writer masks, secrets/state and hardening; no NAS file I/O/
jobs, other-host changes or remote publication are authorized.
