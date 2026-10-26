# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-009 — Publication-pinned README capture](tasks/web-009-repository-card-capture.md) |
| Branch / completed package | `feat/web-ui` / WEB-008 (this commit; parent `7a86fc2`) |
| Blockers | None for WEB-009. WEB009–026 and final plan-wide acceptance remain. |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-25 |

WEB001–008 are complete. Guarded configuration application passes its strict
source gate and125 installed browser cases across ordinary native/rootless
workflows and representative crash/concurrency/policy/quota scenarios. CONFIG01–11
are complete; original failed outcomes remain retained. The shared API/UI image
remains pinned UBI10 micro without Node. Configuration editor UX is WEB-015.

No production/NAS/live Cockpit changes, rollout, merge, push or tag.
Detailed evidence: [task008](tasks/web-008-atomic-configuration-application.md) and
[Operator handoff](../progress.md#operator-handoff).
