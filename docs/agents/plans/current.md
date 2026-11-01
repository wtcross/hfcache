# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Current task | [WEB-025 — Legacy deprecation and independent web handoff](tasks/web-025-retire-cockpit-plugin.md) (**pending**, ready) |
| Branch / completed package | feat/web-ui / WEB-024, this commit |
| Last completed task | [WEB-024 — Human documentation acceptance](tasks/web-024-human-documentation-acceptance.md) (completed 2026-11-01) |
| Updated | 2026-11-01 |

All92 completed cases retain their minimum layers; three later-owner cases remain
pending. WEB-024 Gate1 passes9650 backend/4051 combined web/16 wheel checks with1547
inputs unchanged. Final guides,40 retained workflow steps,13 historical synthetic
screenshots and19 inert/strict-model examples are reviewed. No accepted effect
or manual reader listening is repeated. WEB-023/490694e preserves actual old-client
and native/rootless78→77→78 compatibility, both fixtures restored78, original
failures and unknown handles.

Continue WEB-025 then WEB-026 as sequential local commits and close the plan.
The [bounded-testing policy](support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort)
retains all95 new-web behaviors/layers and scoped reuse. The user's latest
instruction excludes further Cockpit maintenance/validation: WEB-025 records
proportional deprecation, preserving legacy source/history/licenses, shared
helpers and live state. No plugin inventory/ports/cleanup or uninstall project.

Preserve production/NAS, original locks/stores/unknown operations, credentials,
user caches, disabled calendars and remote holds. No merge/push/tag/deployment.
See [human acceptance](../../web-ui/test-release-acceptance.md) and completed tasks
for exact source/artifact/profile scope. Current task evidence and Git own state.
