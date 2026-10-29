# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-021 — Immutable UI release packaging](tasks/web-021-immutable-ui-release-packaging.md) (**pending; handoff only, not started**) |
| Branch / completed package | feat/web-ui / WEB-020, this commit |
| Last completed task | [WEB-020 — Cross-browser accessibility and bounded load](tasks/web-020-cross-browser-accessibility-and-load.md) (completed 2026-10-29) |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-29 |

WEB-020 completes in this commit, `WEB-020: harden browser recovery,
accessibility and bounded reads`. All six owned acceptance rows are completed.
The final required `scripts/check.sh --require-web --require-cockpit` exits0:
9039 backend tests,3702 web unit/4029 combined frontend,95% line/90.02% branch
coverage and all Cockpit, install/build, browser smoke and real HTTP/API checks
pass. The52 deselections are opt-in; backend duration is1067.78s. Task020 and the
[evidence ledger](support/web-ui/acceptance-evidence.json) retain exact final
source3f97731e, logs, actual installed Native68 and historical source-specific
measurements; no failed record or unknown worker exit was rewritten.

This router condenses its former running checkpoints because their exact history
remains in [task020](tasks/web-020-cross-browser-accessibility-and-load.md), the
[dated plan](2026-10-20-plan-web-ui.md) and [progress](../progress.md#operator-handoff).
They preserve the original interrupted configuration Apply/lost-key uncertainty,
local storage simulation, read/reader/performance limits and failed attempts.
No mutation replay, production/NAS rollout, merge/push/tag or Cockpit retirement
is implied by task completion.

The plan remains active. WEB-021 is the pending next handoff; no packaging or
release work for that task has started here. Read its existing task and affected
contracts before implementation; do not treat the completed WEB-020 evidence as
production deployment or final whole-plan acceptance.
