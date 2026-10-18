# REL-010: Review and commit 0.2.0 source

| Field | Value |
| --- | --- |
| Work package | `REL-010` |
| Status | pending |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [OPS-015](ops-015-rootless-container-runtime.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Review/land the local implementation according to the authorized local review workflow, with no remote push or other-host action.
2. Introduce version 0.2.0 in source metadata/lock/CHANGELOG/README for the breaking API-only operational CLI and explicit container deployment contract. Preserve existing dependency versions. Record review and tool/profile evidence; working-tree wheel/image builds are previews, never deployable artifacts.
3. Run the full --with-build gate and meaningful affected tests, then commit source/version and same-package evidence once. No NAS file/metadata writes, production stage/switch or premature deployed-release/tag claim.
4. Hand the clean committed source to [REL-012](rel-012-clean-container-release-artifacts.md) for final wheel/sdist/images, compatibility and immutable staging. This split avoids a dirty source/evidence circularity without a second commit for this work package.

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

OPS-015's handoff separates this source/version commit from REL-012's clean
artifact execution/evidence commit. No 0.2.0 metadata change or release build is
performed by creating this pending record. Retain all previous artifacts and the
OPS-014 barriers; no remote publication is authorized.

## Completion evidence

Not complete. Record actual date/commands/outcomes, required gate exit, host
change ledger and residual holds, invariant/ADR/contract review and the completed
[progress audit](../../progress.md), then set completed in the same work-package
commit. Do not infer completion from a staged artifact or an unrun host check.
