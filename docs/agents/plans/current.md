# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-023 — Compatibility and rollback drill](tasks/web-023-compatibility-and-rollback-drill.md) (**pending amendments**) |
| Branch / completed package | feat/web-ui / WEB-022 (this commit) |
| Last completed task | [WEB-022 — Installed functional acceptance](tasks/web-022-installed-functional-acceptance.md) (completed2026-11-01) |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-11-01 |

Accepted product-focused criteria retain all95 behaviors:85 owned through WEB-022
are reconciled, ten later-owner cases remain pending. Required Gate21 passes
9646 backend/4051 combined frontend/581 Cockpit/16 wheel checks,1545 inputs
unchanged. See [human acceptance](../../web-ui/test-release-acceptance.md) and
[WEB-022 evidence](tasks/web-022-installed-functional-acceptance.md#completion-evidence)
for exact installed/source scope and preserved failures/uncertainty.

After WEB-022's local commit and before WEB-023 implementation, refresh/apply all
related WEB-023–026 bounded-testing amendments against the accepted criteria.
Use GPT-6.1-sol efforts high/medium/high/medium. Do not restore superseded mandatory
85×18/95×18 runner requirements; optional diagnostics stay strict if invoked.
Continue sequential local work-package commits through final validation and plan
closure. Preserve production/NAS, live Cockpit, original locks/unknown operations,
credentials, user caches and disabled calendars; no merge/push/tag/deployment.

The [fresh-session prompt](support/web-ui/fresh-session-implementation.md) and
[goal](support/web-ui/fresh-session-goal.md) retain the earlier resumption scope.
Current task records and Git now own execution state; old pause checkpoints are
historical, not a renewed blocker or instruction to repeat accepted effects.
