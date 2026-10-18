# OPS-018: Deploy and accept the corrected listener locally

| Field | Value |
| --- | --- |
| Work package | `OPS-018` |
| Status | pending |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [REL-013](rel-013-container-worker-artifacts.md), committed |
| Scope | Guarded local host rollout and non-executing acceptance; no live NAS file I/O or jobs |

## Scope and acceptance

1. Record host/runtime/current identities and prove the permanent readonly
   guard, host NFS-ro mount, legacy writer masks, disabled verification calendar,
   actual executor quiescence and original lock inodes. Reuse existing protected
   credentials and TLS sources without printing values. No remote change.
2. Drain API before worker without force and stop the old rootless .socket unit.
   Account for its RemoveOnStop=false pathname: retain and move only the proven
   old socket under reviewed quiescence into protected local evidence before
   the new worker binds. Unknown paths or active/ambiguous listeners refuse;
   neither startup nor the installer gets generic stale-socket cleanup power.
3. Perform the reviewed installer switch to REL-013's exact 0.2.1 stage while
   holding the original noncreating lock and continuous NAS-ro/mask barriers.
   Preserve both stores, pending observers, all locks and old artifacts. Reclaim
   the permanent guard before application startup; it remains independent of
   current. Reload both managers and inspect effective fragments/drop-ins and
   nine bindings. Verify the rootless .socket is dormant and cannot be manually
   started, while the native profile's historical activation is preserved.
4. Start the corrected target after actual worker READY and prove the actual API
   container can perform the fixed framed private PROBE against the worker-created listener with
   expected peer UID, unchanged SELinux enforcement and no label/policy bypass.
   Prove PID1/internal FD3, actual no-IP/secret/mask/capability/cgroup/root/lock
   barriers and a clean target drain/restart with socket cleanup and retained
   stores/locks. No production verification or other command is submitted.
5. Repeat verified local TLS and bounded REST version/capabilities/OpenAPI,
   authentication/read-write denial, MCP initialize/tools-list and fixed client
   readiness checks without invoking archive-reading tools/routes. Preserve
   protocol negotiation rules and sanitized nonsecret evidence. Record exact
   deployed source/images, guard, effective units and the new peer acceptance.
6. Keep live NAS write/full-domain/NFS-workload, calendar and other-host holds
   explicit. Rollback to 0.2.0 must drain cleanly, preserve state and restore its
   activation arrangement deliberately; it reintroduces its known API-worker
   SELinux hold rather than claiming equivalent acceptance.

## Contracts, invariants, and ADRs

Review the accepted OPS-017 listener decision; decisions
[65](../../adr/decision-065.md), [115](../../adr/decision-115.md),
[121](../../adr/decision-121.md), [126](../../adr/decision-126.md),
[127](../../adr/decision-127.md); release/deployment/environment/containers
contracts; INV-002/003/005–007/010–016, AD-16/17/21 and FS/TX preservation.
No application, image, credential authority or durable schema change is part of
the rollout. An unexpected required source fix receives an explicit task and
fresh artifacts before deployment continues.

## Validation

Planned, not execution evidence: protected host before/after ledger; reviewed
guard handoff and guarded selector switch; effective manager/unit/binding checks;
actual API-container framed PROBE and isolation; TLS/REST/MCP metadata-free
acceptance; clean drain/restart and lock/store preservation; record/link audits
and full NAS-masked `scripts/check.sh --with-build`. Forbidden NAS workload
checks remain NOT RUN. Root alone executes privileged local actions.

## Execution notes and handoff

Draft task only. Wait for committed REL-013. No host change is made by this
record. Preserve old failed AVC/probe evidence alongside the corrected actual
container-origin proof, without relabeling a historical failure as passing.

## Completion evidence

Not started. Record actual commands/exits, source/image/index and deployed
unit/guard identities, peer/TLS/drain outcomes, retained evidence and remaining
holds, required gate exit and completed [progress audit](../../progress.md) in
this work-package commit.
