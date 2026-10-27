# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-018 — Schedule, observer and journal](tasks/web-018-schedule-observer-and-journal.md) (pending) |
| Branch / completed package | feat/web-ui / WEB-017 (this commit) |
| Blockers | None; WEB-018 is ready after the WEB-017 commit. |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-27 |

WEB001–017 are complete. [Task017](tasks/web-017-maintenance-ui.md) records the
strict S2 gate, all 39 current installed browser cases, separate repair collector
qualification and preserved original failures. The owned guest, existing shared
Caddy and browser engine remain available for later scoped tests.

The shared API/UI image remains pinned UBI 10 micro without runtime Node.
Production, NAS, live Cockpit, rollout, merge, push and Git tags remain outside
this authorization. Preserve all pending handles, unknown journals, damaged
predecessors and prior fixture evidence; observation never authorizes replay.
