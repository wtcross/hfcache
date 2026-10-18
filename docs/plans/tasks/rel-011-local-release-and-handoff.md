# REL-011: Record the local release and preserve acceptance holds

| Field | Value |
| --- | --- |
| Work package | `REL-011` |
| Status | pending |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [OPS-016](ops-016-local-rootless-deployment.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Reconcile the actual deployed artifact/image/source identity, local review and commit history, host change ledger, no-NAS barriers and all required repository/runtime evidence.
2. Update release notes, README/deployment/progress and operator handoff with exact partial acceptance. Preserve open real NAS write/full-domain/NFS-hardening and other-host/calendar checks; leave sync stopped and verification scheduling disabled.
3. Create only the authorized local annotated tag for the artifact actually deployed, with no remote push/publication; record remaining rollback/state/credential/TLS constraints and no unearned 1.0/full-acceptance claim.
4. Complete this plan and clear only its selection after actual required gates and scoped acceptance. Preserve all task/history evidence and unrelated backlog.

## Contracts, invariants, and ADRs

Release/deployment policy and decision 126/OPS-015 architecture; INV-010/011/014/015, decisions 65/75/79/121, state/handle retention and deliberate artifact identity.

Read the [invariant register](../../invariants.md), [ADR index](../../adr/README.md),
[environment](../../agents/environment.md), [release](../../agents/release.md),
[planning](../../agents/planning.md) and [workflow](../../agents/workflow.md).
Record actual review/amendments with completion evidence; preserve historical
records rather than silently rewriting their earlier authority.

## Validation

Planned, not execution evidence: `scripts/check.sh` (plus `--with-build` at
release/container boundaries), meaningful scope-specific tests and local
record/link/decision/whitespace audits. Host tests must preserve the absolute
NAS-write ban. Record forbidden storage checks as NOT RUN, never passing.
Only root performs privileged host mutations and never prints secret values.

## Execution notes and handoff

Not started. Dependency completion and commit are required before activation.

## Completion evidence

Not complete. Record actual date/commands/outcomes, required gate exit, host
change ledger and residual holds, invariant/ADR/contract review and the completed
[progress audit](../../progress.md), then set completed in the same work-package
commit. Do not infer completion from a staged artifact or an unrun host check.
