# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Production web migration](2026-11-01-plan-production-web-migration.md) |
| Current task | [OPS-024](tasks/ops-024-production-web-migration.md) — independent preflight; build blocked on account-home compatibility |
| Last completed plan | [Remove the obsolete interface](2026-11-01-plan-legacy-interface-removal.md) (completed 2026-11-01) |
| Last completed task | [REL-016](tasks/rel-016-web-release-source.md) (this commit) |
| Branch | main |
| Updated | 2026-11-01 |

The user authorizes local replacement including web UI, REST, MCP and installed
plugin removal. Preserve configuration and NFS data; keep NFS read-only, writer
masks and disabled schedules. REL-016 prepares distinct version 0.3.0 and passes
the full strict gate. OPS-024's preflight found the host's preserved account home
requires a narrowly reviewed helper compatibility correction before the immutable
build. That source task is activated after the REL-016 commit. OPS-024 owns
guarded installation, current-host guard reconciliation and acceptance.
No archive workload, remote publication or historical backlog is activated.
