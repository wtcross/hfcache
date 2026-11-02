# Current plan

| Field | Value |
| --- | --- |
| State | inactive |
| Active plan | None |
| Current task | None |
| Last completed plan | [Production web migration](2026-11-01-plan-production-web-migration.md) (completed 2026-11-02) |
| Last completed task | [OPS-024](tasks/ops-024-production-web-migration.md) (this commit) |
| Branch | main |
| Updated | 2026-11-02 |

The authorized migration selects 0.3.0 from exact clean source `3d6670d`, with
local annotated `v0.3.0`. Web UI, REST, MCP and confined helper read acceptance
pass, including trusted-terminal configuration reads and final post-restart
automated checks. All165 model selections, original files/stores/handles/secrets
and lock inodes remain preserved. The old public Cockpit entrypoint is retired
with its original inode/assets retained. NFS-ro, writer/calendar masks and the
user's deliberate inactive guard setting remain. Full strict gate passes.

Current-boot operation and the reviewed restart are accepted. Automatic boot
recovery remains unconfigured: independent root runtime-object provisioning and
helper READY before bridge/API are required after reboot/recreation. Preserve
remaining NAS/workload, browser-JavaScript/Apply, other-host and new-host all-phase
IP/inode-alias companion holds. No old backlog, archive workload or remote
publication is activated. Do not replay completed migration phases.
