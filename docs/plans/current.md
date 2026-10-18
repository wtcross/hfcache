# Current plan

| Field | Value |
| --- | --- |
| State | Active |
| Active plan | [Local rootless rollout](2026-10-18-plan-local-rootless-rollout.md) |
| Next task | [OPS-016](tasks/ops-016-local-rootless-deployment.md) |
| Blockers | None; later tasks wait for committed predecessors |
| Updated | 2026-10-18 |

REL-012 is completed; OPS-016 remains pending until its evidence commit exists.
Clean artifacts identify committed REL-010 (`481fcc4`); production is not switched.
The NAS read-only mount, blocked legacy writers and held original lock remain
protected. Only reviewed local host/container work is authorized; no NAS content/
metadata writes, other-host changes or remote publication. Later tasks wait for
committed predecessors; completed REST/MCP evidence remains history.
