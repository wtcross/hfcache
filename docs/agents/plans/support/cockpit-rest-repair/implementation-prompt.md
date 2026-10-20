# Implementation / resume instruction

This is a prompt template for a later explicit implementation request. Its presence
in an extracted draft does not authorize any action by itself.

```text
Implement docs/agents/plans/2026-10-19-plan-cockpit-rest-repair.md using the project's
AGENTS.md, docs/agents/planning.md and docs/agents/workflow.md.

Start by checking git history/status, current.md, the selected plan (if any),
relevant progress/Decisions/Operator handoff, and source drift from the pinned
review. Recheck work-package IDs outside the imported bundle. Preserve unrelated
changes, completed records and all historical host restrictions. Reconcile another
active plan explicitly; do not silently replace it.

Create or safely resume fix/cockpit-rest-api-alignment. This instruction authorizes
scoped source implementation and plan activation, not production inspection,
deployment, host configuration/service changes, registry operations, pushing,
merging, tagging or live archive workloads. A disposable runtime must be explicitly
provisioned without NAS/live credentials; record a blocker when it is unavailable.

Activate the plan and execute CPR-001 through CPR-009 serially according to their
dependencies. Treat each task as one work package and one incremental commit named
<CPR-ID>: <summary>. Keep task status/evidence, progress audit, next-task pointer,
contracts, invariant/ADR review and human docs current in that same commit. Use
the repository's actual next ADR number if a new decision is needed.

Fix the reported validation/reconnect path and the audited integration gaps.
Preserve the existing API-backed fixed CLI launcher, bounded exact Envelopes,
credential separation, guarded host configuration installation and original
operation identity. Never make the UI work by bypassing API auth, archive gates,
NAS holds, SELinux, systemd hardening, unit masks, or the root configuration lock.
No automatic POST replay, cancellation, reinstall, rollback or cleanup after an
uncertain response. MCP stays read-only and is not the admin transport.

Add fail-before/pass-after regressions for each repaired behavior, including the
maintenance Apply predicate and tab-unmount handle loss. Execute scripts/check.sh
for every package with the Cockpit portion actually run; do not accept its optional
skip as frontend proof. Final validation includes make -C cockpit check and
scripts/check.sh --with-build, plus the required component, real CLI/socket and
provisioned disposable Cockpit/rootless tests in the matrix.

Record actual evidence and unresolved installed cause honestly. Do not claim that
a fixture or renamed message proves the production bug fixed. Leave production
installation, original-host symptom acceptance and NAS/workload acceptance as
separate operator handoff items. Never initialize an existing archive. A missing
required prerequisite blocks the relevant task; it is not replaced with a mocked
pass or an unauthorized host action.

On interruption, reconcile git and task evidence before resuming. On scoped
completion retain the plan/tasks, clear current.md, and do not select unrelated
historical backlog. Stop with the reviewed branch and incremental commits; no push,
merge, release tag or deployment is requested.
```
