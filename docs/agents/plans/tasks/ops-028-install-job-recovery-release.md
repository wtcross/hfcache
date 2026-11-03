# OPS-028: Guarded local installation while NFS stays read-only

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | REL-018 |
| Execution | `gpt-6.1-sol` / `high`; explicit task-agent setting required |

## Scope and acceptance

Guarded local installation while NFS stays read-only; actual Basic/UI/helper negative-permission behavior and reviewed recovery of the reported key.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Review the parent plan's affected contract and decision list progressively.
Record exact reviewed IDs, amendments and any new decision before completion.

## Validation

Before implementation, replace this placeholder with a finite table of changed
requirements, smallest meaningful checks, required gate and observed results.
Every commit requires `rtk scripts/check.sh`; web changes require `--require-web`;
release acceptance requires `--require-web --with-build`. Preserve raw failures.
Do not invoke the optional instrumented functional runner.

## Execution notes and handoff

Activated 2026-11-03 by the user's explicit end-to-end implementation instruction.
Protected deployment, controlled writable transition, selected Sync and refresh
pilots and bounded metadata backfill are authorized after the reviewed safety
prerequisites. Scope is this host/current boot with fail-closed manual startup
permitted; unattended boot acceptance remains separate.

## Completion evidence

Pending. Source and unit tests alone do not establish installed acceptance.
