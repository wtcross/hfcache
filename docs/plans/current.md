# Current plan

| Field | Value |
| --- | --- |
| State | Active |
| Active plan | [Local rootless rollout](2026-10-18-plan-local-rootless-rollout.md) |
| Next task | [REL-010](tasks/rel-010-rootless-release-artifacts.md) |
| Blockers | None; later tasks wait for committed predecessors |
| Updated | 2026-10-18 |

OPS-015 is completed; REL-010 remains pending until the OPS-015 commit exists.
The NAS read-only mount, blocked legacy writers and held original lock remain
protected. Only reviewed local host/container work is authorized; no NAS content/
metadata writes, other-host changes or remote publication. Later tasks wait for
committed predecessors; completed REST/MCP evidence remains history.
