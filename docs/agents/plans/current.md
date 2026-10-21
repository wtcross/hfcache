# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](2026-10-20-plan-web-ui.md) |
| Next task | [WEB-006 — Guarded host adapter](tasks/web-006-guarded-host-adapter.md) |
| Blockers | No WEB-005 scoped prerequisite remains; WEB-006 is not started. |
| Last completed plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Updated | 2026-10-21 |

WEB-005 scoped serving/harness acceptance passes: host source14/gate14 and original
guest13/common21 all six normal generations, monitor0, independent closure and
separate compatibility receipt. Artifact4 keeps original source10 build provenance.
Measured306trusted+18untrusted browser checks pass; all131 recorded PID/start pairs,
40cgroups,18containers and26endpoints close. Exact commands/hashes/nodes and the
user pause/resumption remain in [task005](tasks/web-005-shared-caddy-spa-serving.md)
and [progress/handoff](../progress.md#operator-handoff).

ROUTE02pagination, ROUTE03exactdetails and ROUTE06cards remain pending under their
later tasks. RELEASE03/WEB021 clean release and full95-case acceptance remain
pending. Every older failed/UNKNOWN/HOLD record remains unchanged. No successor
implementation is claimed by this selector.

Scope remains source work and positively owned disposable tests. No merge, push,
tag, production deployment/Caddy reload, live credential/service/timer/guard
change, NAS access or live Cockpit uninstall is authorized. Preserve original
candidates, backups, locks, stores, handles and all historical evidence.
