# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Current task | [WEB-024 — Human documentation acceptance](tasks/web-024-human-documentation-acceptance.md) (**pending**, ready) |
| Branch / completed package | feat/web-ui / WEB-023, this commit |
| Last completed task | [WEB-023 — Compatibility and rollback](tasks/web-023-compatibility-and-rollback-drill.md) (completed 2026-11-01) |
| Updated | 2026-11-01 |

All88 completed cases retain their minimum layers; seven later-owner cases remain
pending. WEB-023 Required Gate1 passes9650 backend/4051 combined web/16 wheel
checks with1547 frozen inputs unchanged. Actual old0.2.2 clients/copied-state
readers and owned native/rootless78→77→78 roundtrips are recorded in the task.
Both fixtures are restored78. Original failures, classified refusals, the known77
configuration-read limitation and unknown handles remain preserved.

Continue sequential local work-package commits through WEB-026 and plan closure.
The [bounded-testing policy](support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort)
retains all95 new-web behaviors and layers, scoped reuse and task-specific effort.
Do not restore mandatory runner cross-products or replay accepted effects.

The user's2026-11-01 direction excludes further Cockpit plugin maintenance and
validation. Required validation is strict web/backend/docs/build; WEB-025 is
proportional deprecation/handoff. Preserve legacy source/history/licenses, shared
runtime helpers and the live installation. No plugin cleanup, porting or uninstall.

Preserve production/NAS, original locks/stores/unknown operations, credentials,
user caches, disabled calendars and remote holds. No merge/push/tag/deployment.
See [human acceptance](../../web-ui/test-release-acceptance.md) and the completed
task for actual source/artifact/profile scope. The earlier fresh-session prompt
is historical; this selector, task evidence and Git own current state.
