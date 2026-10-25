# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-007 — Configuration read and managed preview](tasks/web-007-configuration-read-and-preview.md) |
| Branch / completed package | `feat/web-ui` / WEB-006 (this commit) |
| Blockers | None for WEB-007. Final plan-wide acceptance and WEB-007–026 remain. |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-25 |

WEB001–006 are complete. WEB006 passes its strict source gate, both-profile
real-Caddy browser suites and native/rootless isolation/fault acceptance.
AUTH-08/HOST-01–03 are complete. The rootless read-work budget fix preserves
all security checks; shipped UI assets remain in the pinned UBI10 micro API image.
Earlier failed outcomes and original artifacts remain retained.

Next implement safe installed configuration read and exact managed-edit preview.
No production/NAS/live Cockpit changes, rollout, merge, push or tag.
Detailed evidence: [task006](tasks/web-006-guarded-host-adapter.md) and
[Operator handoff](../progress.md#operator-handoff).
