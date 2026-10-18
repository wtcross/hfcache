# Current plan

| Field | Value |
| --- | --- |
| State | Active |
| Active plan | [Local rootless rollout](2026-10-18-plan-local-rootless-rollout.md) |
| Next task | [REL-012](tasks/rel-012-clean-container-release-artifacts.md) |
| Blockers | None; later tasks wait for committed predecessors |
| Updated | 2026-10-18 |

REL-010 is completed; REL-012 remains pending until its source/version commit exists.
Clean final artifacts must come from that committed source, not preview builds.
The NAS read-only mount, blocked legacy writers and held original lock remain
protected. Only reviewed local host/container work is authorized; no NAS content/
metadata writes, other-host changes or remote publication. Later tasks wait for
committed predecessors; completed REST/MCP evidence remains history.
