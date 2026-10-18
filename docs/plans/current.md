# Current plan

| Field | Value |
| --- | --- |
| State | Active |
| Active plan | [Local rootless rollout](2026-10-18-plan-local-rootless-rollout.md) |
| Next task | [REL-011](tasks/rel-011-local-release-and-handoff.md) |
| Blockers | None; later tasks wait for committed predecessors |
| Updated | 2026-10-18 |

OPS-016 completed partial local deployment/acceptance; REL-011 remains pending
until that package is committed. Clean artifacts identify REL-010 (`481fcc4`);
current selects 0.2.0 and the permanent guard holds the original inode. Caddy/API
run with TLS/metadata/isolation/drain acceptance. API-to-worker SELinux access
remains an explicit release hold, not end-to-end verification acceptance.
The NAS read-only mount, blocked legacy writers and held original lock remain
protected. Only reviewed local host/container work is authorized; no NAS content/
metadata writes, other-host changes or remote publication. Later tasks wait for
committed predecessors; completed REST/MCP evidence remains history.
