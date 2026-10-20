# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-002 — strict frontend and gates](tasks/web-002-strict-frontend-and-gates.md) |
| Blockers | None for the next task; browser/installed dependency closure still needs provisioning and proof in its owning tasks. Production browser/NAS/workload holds remain separate. |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-20 |

The explicit implementation instruction activates the extracted web UI plan on
`feat/web-ui`. HEAD matched its reviewed baseline `6b8fae2` exactly; the prior
selector was inactive. The bundle is intended new planning material. No older
plan or historical backlog is activated or abandoned.

WEB-001 completed the contract/ADR/acceptance/prerequisite audit and fixed a
reproduced baseline Bash frame-reader wait defect. Its corrected strict gate
passes 5308 Python/572 Cockpit unit/110 mounted Firefox tests. All 95 web feature
cases remain pending. The exact original baseline and failed evidence remain.

Scope permits source changes and owned local/disposable tests only. No merge,
push, tag, production deployment/Caddy reload, service/timer/credential/guard
change, NAS access or live Cockpit uninstall. Preserve the earlier operator
handoff and all original candidates, backups, locks, stores and handles.
