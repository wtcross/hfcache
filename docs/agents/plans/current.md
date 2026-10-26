# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-015 — Configuration and tag management](tasks/web-015-configuration-and-tag-ui.md) |
| Branch / completed package | feat/web-ui / WEB-014 (this commit) |
| Blockers | WEB015–026 and final plan-wide acceptance remain. |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-26 |

WEB001–014 are complete. Bounded inert archived README rendering passes strict
gate4 and36 actual installed Caddy/API cases across Chromium, Firefox and WebKit,
with zero CSP events or mutation requests. Exact sanitized source, publication
provenance, immutable upstream links and local render refusal remain explicit.
CARD10–12 are complete. Configuration/tag editing is next, then jobs.
The shared API/UI image remains pinned UBI10micro without runtime Node.

No production/NAS/live Cockpit changes, rollout, merge, push or tag.
Detailed evidence: [task014](tasks/web-014-safe-markdown-rendering.md) and
[Operator handoff](../progress.md#operator-handoff).
