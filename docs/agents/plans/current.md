# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-004 — Basic administrator and permissions](tasks/web-004-basic-auth-and-permissions.md) |
| Blockers | None for the next task. Chromium is provisioned for preliminary local testing; the full three-engine/Caddy/installed dependency closure still needs proof in its owning tasks. Production browser/NAS/workload holds remain separate. |
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

WEB-002 adds the strict React workspace, required web gate, full locked license
inventory, retained per-run evidence and actual preliminary browser checks. Its
final strict gate passes 5337 Python, 572 Cockpit unit, 110 mounted Firefox,
45 web unit/50 combined component and 2 sandboxed Chromium tests. Coverage is
98.46% lines/98% branches. The source preview is disconnected; Caddy/API serving
and authentication remain unimplemented. All 95 feature cases remain pending.
An extra whitespace check found a generator-added trailing notice separator
after the unpublished commit. Its narrow correction passes the complete strict
gate again; that same work-package commit is amended before advancing.

WEB-003 completes authoritative route/mode projections, generated reconstructing
decoders, bounded exact numeric/Unicode validation and a same-origin client.
Its strict gate passes 5452 Python, retained 572/110 Cockpit, 2718 web unit/2744
combined component, two shell and 14 real-API React browser tests with no required
skip. Coverage is 95.85% lines/92.94% branches. This read fixture remains temporary
until WEB-005 and proves no Caddy/Basic/installed behavior. All 95 feature cases
remain pending. Next is WEB-004; known baseline prefix/header issues are recorded
for WEB-005's routing acceptance.

Scope permits source changes and owned local/disposable tests only. No merge,
push, tag, production deployment/Caddy reload, service/timer/credential/guard
change, NAS access or live Cockpit uninstall. Preserve the earlier operator
handoff and all original candidates, backups, locks, stores and handles.
