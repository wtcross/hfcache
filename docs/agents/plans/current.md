# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-011 — Query and operation state](tasks/web-011-query-and-operation-state.md) |
| Branch / completed package | `feat/web-ui` / WEB-010 (this commit) |
| Blockers | WEB011–026 and final plan-wide acceptance remain. No current prerequisite blocker. |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-26 |

WEB001–010 are complete. Exact card reads pass strict source gate3 and installed
application acceptance, with no payload/network/write effects or current fallback.
CARD01–09 are complete; README rendering remains WEB-014. The shared API/UI image
remains pinned UBI10 micro without runtime Node.

No production/NAS/live Cockpit changes, rollout, merge, push or tag.
Detailed evidence: [task010](tasks/web-010-repository-card-read-api.md) and
[Operator handoff](../progress.md#operator-handoff).
