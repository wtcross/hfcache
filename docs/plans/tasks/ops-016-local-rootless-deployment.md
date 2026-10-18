# OPS-016: Deploy the local runtime with read-only acceptance

| Field | Value |
| --- | --- |
| Work package | `OPS-016` |
| Status | pending |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [REL-010](rel-010-rootless-release-artifacts.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Recheck the committed guardrails, NAS read-only mount, paused/blocked writers and actual executor quiescence before host-local deployment. Preserve local backups and retain the noncreating shared lock across any runtime switch.
2. Root installs reviewed local account/user-manager/container/proxy/config/credential/unit changes and switches only to the identified staged artifacts. Start the reviewed target so Caddy and API run rootless; verify the private worker and runtime client container boundaries.
3. Prove actual local TLS/Unix/proxy/auth/registry, no-IP/no-credential worker, rootless UID/cgroup/activation/drain and non-NAS writable paths using bounded local checks and disposable local fixtures. Do not test NAS write denial by attempting a NAS mutation.
4. Keep all sync work stopped and verify scheduling disabled; no archive init, sync, non-estimate verification, mutation/probing jobs, write-bearing NFS tests or real archive hardening workload. No ACME issuance, remote push, other-host trust/config changes or NAS administration.
5. Record actual deployed identity, every successful/failed/not-run check and guarded rollback constraints. Deployment is partial data-preserving acceptance, never a falsely green full storage rollout.

## Contracts, invariants, and ADRs

Decision 126 and OPS-015 architecture; INV-002/003/005–007/010–016, FS/TX preservation, environment/release/deployment rules, credential whole-archive scope and actual executor/observer separation.

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
