# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-022 — Installed functional acceptance](tasks/web-022-installed-functional-acceptance.md) (**pending**) |
| Branch / completed package | feat/web-ui / WEB-021, this commit |
| Last completed task | [WEB-021 — Immutable UI release packaging](tasks/web-021-immutable-ui-release-packaging.md) (completed 2026-10-29) |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-29 |

WEB-021 completes with clean source8 artifacts, actual native/rootless packaging
acceptance and final gate6 exit0. The task/ledger retain exact source, artifact,
role, browser and gate evidence, all failed attempts and boot-specific limits.

The user's WEB-021 through WEB-026 goal authorizes continuing directly into
WEB-022. Its full workflow, positive verification/MCP report/native-control and
functional-gate requirements remain pending; packaging smoke does not close them.
Original lost/uncertain Apply state is preserved without replay. Production/NAS,
merge/push/tags and live Cockpit removal remain excluded.
