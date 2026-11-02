# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Publish and deploy the draft-safe Library update](2026-11-02-plan-web-drafts-library-rollout.md) |
| Current task | [OPS-026](tasks/ops-026-local-web-refresh.md) |
| Last completed plan | [Protect unsaved configuration and streamline Library browsing](2026-11-02-plan-web-drafts-and-library.md) (completed 2026-11-02) |
| Last completed task | [REL-017](tasks/rel-017-web-drafts-library-release.md) (this commit) |
| Branch | main |
| Updated | 2026-11-02 |

Completed WEB-028 → WEB-029 → WEB-030 sequentially, each in its own gated
implementation commit. Draft retention, measured first-viewport Library browsing
and four-GET compatible pagination pass source/owned-fixture acceptance. The
completed plan and tasks retain exact evidence and earlier failed attempts.
The new user instruction authorizes publication and local replacement through
the selected release plan. Prior source-only restrictions remain historical;
archive/NAS workloads, calendars, replay, security weakening and other-host work
remain outside scope. No old backlog is selected.

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
IP/inode-alias companion holds. The newer instruction authorizes main publication
and local replacement only;
no old backlog, archive workload or release tag is activated. Do not replay
completed migration phases.

Release source 0.3.1 and its complete strict web/build gate pass. OPS-026 now
selects the clean artifact build and guarded local replacement. Both remotes
already contain the three approved WEB commits; existing tags remain preserved.
