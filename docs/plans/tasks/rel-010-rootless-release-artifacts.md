# REL-010: Prepare identified locked release artifacts

| Field | Value |
| --- | --- |
| Work package | `REL-010` |
| Status | pending |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [OPS-015](ops-015-rootless-container-runtime.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Review/land the local implementation according to the authorized local review workflow, with no remote push or other-host action.
2. Deliberately select a release version, update source metadata/lock/changelog/README and build locked Python and container artifacts; record source commit and hashes/digests, tool versions and dependency profiles.
3. Run the full --with-build gate and relevant real disposable container/TLS/secret/peer/drain/read-only tests. Re-run actual installed/image compatibility against the real retained target; record unavailable readers distinctly from schema-aware refusal.
4. Stage immutable local artifacts and retain the previous runtime/units/state for guarded rollback. No NAS file or metadata writes and no premature deployed-release/tag claim.

## Contracts, invariants, and ADRs

Release policy, INV-005/010/011/014/015, decisions 65/75/79/121/126 and the OPS-015 rootless decision; independent service/scheduled-state schemas and source/artifact identity.

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
