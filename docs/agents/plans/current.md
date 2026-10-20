# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Cockpit repair local rollout](2026-10-20-plan-cockpit-rest-rollout.md) |
| Next task | [OPS-023: clean artifacts and local deployment](tasks/ops-023-cockpit-rest-host-rollout.md) |
| Blockers | REL015 strict extended source gate passes5299Python/16build/570unit/110mounted/3profiles under NAS shadow. Commit/publish source, then activate OPS023. No current blocker or production deployment effect yet. Preserve original failed Timestral result, candidate/backups/locks and all NAS/workload holds. |
| Last completed plan | [Cockpit REST repair](2026-10-19-plan-cockpit-rest-repair.md) |
| Updated | 2026-10-20 |

The new explicit user request authorizes merge/main publication (donecdc35a4)
then a guarded local replacement deployment. It supersedes the preceding no-merge/
no-deployment scope only for this new plan. No historical backlog is activated.

All nine repair tasks completed with required actual frontend/extended and disposable
acceptance. [Evidence](support/cockpit-rest-repair/acceptance-record.md) and
[operator handoff](support/cockpit-rest-repair/operator-handoff.md) retain exact
artifacts, five guests, original locks/handles/backups and unknown/unconfirmed
attempts. Production and NAS remain untouched; no historical backlog is activated.
Later user steering explicitly authorizes final green implementation-branch pushes
to Forgejo and GitHub after commit only, preserving all nine package boundaries.
The selected new plan owns current local release/deployment authority. No registry,
force push, NAS/live workload or unrelated tag publication is authorized.
