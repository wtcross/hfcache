# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Production web migration](2026-11-01-plan-production-web-migration.md) |
| Current task | [OPS-024](tasks/ops-024-production-web-migration.md) |
| Last completed plan | [Remove the obsolete interface](2026-11-01-plan-legacy-interface-removal.md) (completed 2026-11-01) |
| Last completed task | [OPS-025](tasks/ops-025-preserved-rootless-account-home.md) (this commit) |
| Branch | main |
| Updated | 2026-11-01 |

The user authorizes local replacement including web UI, REST, MCP and installed
plugin removal. Preserve configuration and NFS data; keep NFS read-only, writer
masks and disabled schedules. REL-016 prepares distinct version 0.3.0 and passes
the full strict gate. OPS-025's bounded account-home correction, 857 focused
checks, 16 actual previous/current parser observations and strict full web/build
gate pass. OPS-024 now builds from the clean completed source commit and owns
guarded installation, current-host guard reconciliation and acceptance.
No archive workload, remote publication or historical backlog is activated.

The protected administrator hash is still missing. The user has the corrected
trusted-terminal provisioning command; production startup of the enabled web
profile waits for that input. Existing services remain 0.2.2, NFS-ro/masks stand,
and the deliberately disabled independent guard setting is preserved by default
after temporary protection during the switch.
