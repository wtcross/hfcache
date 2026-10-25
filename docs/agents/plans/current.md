# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-008 — Guarded atomic configuration application](tasks/web-008-atomic-configuration-application.md) |
| Branch / completed package | `feat/web-ui` / WEB-007 (this commit) |
| Blockers | None for WEB-008. WEB-008–026 and final plan-wide acceptance remain. |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-25 |

WEB001–007 are complete. WEB007 passes its strict source gate and both installed
native/rootless real-Caddy configuration suites:36 cases/three browsers per
profile. CONFIG01–05 are complete; earlier failed outcomes remain retained.
The shared API/UI image remains pinned UBI10 micro, without a Node runtime.

Next is guarded configuration application and read-only crash reconciliation.
No production/NAS/live Cockpit changes, rollout, merge, push or tag.
Detailed evidence: [task007](tasks/web-007-configuration-read-and-preview.md) and
[Operator handoff](../progress.md#operator-handoff).
