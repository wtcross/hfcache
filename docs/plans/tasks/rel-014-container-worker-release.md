# REL-014: Record the corrected local release and handoff

| Field | Value |
| --- | --- |
| Work package | `REL-014` |
| Status | pending |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [OPS-018](ops-018-container-worker-rollout.md), committed |
| Scope | Local release evidence, annotated tag and handoff; no remote publication or NAS action |

## Scope and acceptance

1. Reconcile the exact deployed 0.2.1 source/wheel/image/profile/index, local
   review history, actual API-origin worker peer acceptance and host change
   ledger. Preserve the older 0.2.0 SELinux failure as historical evidence.
2. Update release notes, README/status, contracts and operator handoff to state
   the corrected listener/peer acceptance precisely. It is still not live NAS
   verification, write/full-domain/NFS-hardening, calendar or other-host
   acceptance. Retain original NAS-ro/guard/mask and state-preservation limits.
3. After the actual required gate, create only the authorized local annotated
   0.2.1 tag identifying the reviewed release and its deployed artifact source.
   Do not move an existing tag or push/publish to a remote. Record its actual
   target and annotation, not a provisional command as success.
4. Complete the scoped plan and clear only its active selector once all five
   tasks' acceptance and commits exist. Retain all task, plan, failed attempt,
   rollback and partial release history; unrelated backlog stays unselected.

## Contracts, invariants, and ADRs

Review [release](../../agents/release.md), deployment/environment/containers,
the accepted listener decision and decisions
[65](../../adr/decision-065.md), [75](../../adr/decision-075.md),
[79](../../adr/decision-079.md), [115](../../adr/decision-115.md),
[121](../../adr/decision-121.md), [126](../../adr/decision-126.md),
[127](../../adr/decision-127.md). Preserve INV-010/011/014/015 and truthful
artifact, operation, rollback and remaining-host-hold evidence. No runtime or
schema change is intended in this closure package.

## Validation

Planned, not execution evidence: independent source/artifact/host-ledger and
commit/task/contract audits, local tag preconditions/result, record/link/parity/
whitespace checks and full NAS-masked `scripts/check.sh --with-build`. No host
workload, archive initialization, remote push or external issuance test runs.

## Execution notes and handoff

Draft task only. Wait for committed OPS-018 and its actual corrected peer
acceptance. Preserve rollback to 0.2.0 as a documented reduced-availability
option with its known SELinux hold; never infer that unchanged schema alone
proves equivalent operating behavior.

## Completion evidence

Not started. Record actual gate exit, reviewed local tag, deployed artifact
identity, independent audit, remaining holds and completed
[progress audit](../../progress.md) in this work-package commit.
