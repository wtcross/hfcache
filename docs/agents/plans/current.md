# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Current task | [WEB-026 — Final validation and handoff](tasks/web-026-final-gate-and-handoff.md) (**pending**, ready) |
| Branch / completed package | feat/web-ui / WEB-025, this commit |
| Last completed task | [WEB-025 — Legacy deprecation](tasks/web-025-retire-cockpit-plugin.md) (completed 2026-11-01) |
| Updated | 2026-11-01 |

All93 completed cases retain minimum layers; RELEASE-09 and DOC-05 remain pending.
WEB-025 Gate1 passes9650 backend/4051 combined web/16 wheel checks with1547 inputs
unchanged. Deprecation notices and actual web/runtime independence are recorded,
without plugin code/test/dependency maintenance, validation, removal or uninstall.
Legacy source/history/licenses, shared helpers and live installed state remain.

WEB-024/1d53024 completes human guides; WEB-023/490694e completes actual old-client
and native/rootless78→77→78 compatibility, both fixtures restored78. Original
failures, known predecessor limitations and unknown handles remain preserved.
Continue final source gate, narrowly scoped read-only installed smoke and
unchanged deep-evidence reconciliation under the
[bounded-testing policy](support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort).
Do not restore mandatory runner cross-products or replay accepted effects.

Complete the final local commit and clear this selector only after all95 cases
and required gates/handoff pass. Preserve production/NAS, locks/stores/unknown
operations, credentials, caches, disabled calendars and remote holds. No
merge/push/tag/deployment or live plugin action. See
[human acceptance](../../web-ui/test-release-acceptance.md) for exact source/profile
scope. Current task evidence and Git own execution state.
