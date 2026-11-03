# OPS-027: Supported protected writer runtime, role mounts/startup/helper/SELinux changes, read-only defaults and reversible selection procedure

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | WEB-031 |
| Execution | `gpt-6.1-sol` / `high`; explicit task-agent setting required |

## Scope and acceptance

Supported protected writer runtime, role mounts/startup/helper/SELinux changes, read-only defaults and reversible selection procedure; qualify changed authority boundaries.

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

## Accepted immutable mode handoff

ADR165 requires manifest2 release_id exactly `<version>-<archive_mode>` and
immutable sibling release directories for guarded-readonly/manual-writer. Keep
package/UI version semver and source/app-image/UI bytes identical; bind distinct
rendered runtime/index hashes. Stage both through the existing installer; current,
physical-root, index and helper selector_target use exact release_id. Existing
schema1 version-only identities remain supported. OPS-028 runs the guarded
sibling. OPS-029 drains/selects the writer sibling while still NFS-ro, reprovisions
matching helper/policy, then performs the separate guarded mount transition.
Rollback selects a compatible guarded sibling without editing immutable files
or deleting dispositions. Add only these identity joins to existing machinery.
