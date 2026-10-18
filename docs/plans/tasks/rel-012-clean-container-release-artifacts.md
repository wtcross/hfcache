# REL-012: Build immutable artifacts from clean committed source

| Field | Value |
| --- | --- |
| Work package | `REL-012` |
| Status | pending |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | [REL-010](rel-010-rootless-release-artifacts.md) |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Start from REL-010's actual clean committed 0.2.0 source. Record commit,
   clean-state check, tools, lock and exact package/build inputs. Any necessary
   source correction receives its own completed package before a new clean build;
   do not relabel a dirty preview as the final artifact.
   Use an isolated clean detached worktree of committed REL-010 under ignored
   .scratch/rel012-source, with build outputs outside that checkout. Run the actual
   wheel/image builder and full gate from that clean checkout; main-workspace
   task/evidence edits must not contaminate its source_dirty provenance.
2. Build exact wheel/sdist and locked hashed server+MCP runtime images, including
   the pinned Caddy derivative. Record hashes, platform/base/build/runtime image
   identities and provenance. No runtime resolution, automatic pulls or remote
   publication; source versions/tags alone are not artifact identity.
3. Run actual installed/image compatibility against retained targets for archive,
   service, scheduled and new deployment records. Preserve bytes and distinguish
   unavailable old readers from schema-aware refusal. Complete meaningful actual
   local container/TLS/credential/peer/activation/drain proofs without a NAS bind.
4. Stage immutable identified local artifacts with retained rollback trees/state;
   do not select or activate production. Run the required full --with-build gate
   in the NAS-masked test environment. Commit only execution records/evidence,
   leaving package/build inputs identical to the clean source identified above.

## Contracts, invariants, and ADRs

[Release policy](../../agents/release.md), [rootless contract](../../containers.md),
[deployment](../../deployment-centos-stream-10.md), [schemas 15/16](../../schemas.md#15-rootless-runtime-deployment-profile-ops-015),
INV-005/010/011/014/015, decisions 65/75/79/121/126/127. Preserve workflow's one
work package per commit, exact source/artifact identity and all retained state.

## Validation

Planned, not execution evidence: `scripts/check.sh --with-build`, actual three
locked installation profiles, exact artifact/index/rendered binding checks,
compatibility and owned local container proofs, plus record/link/whitespace audit.
Use the empty read-only NAS shadow for repository collection. Forbidden real NAS
write/full-domain/hardening checks remain NOT RUN. Only root performs privileged
host actions and no secret values are printed.

## Execution notes and handoff

Not started. Added as an unused ID in OPS-015's 2026-10-18 handoff, within the
authorized rollout. REL-010 must be completed and committed before activation;
OPS-016 now waits for this task. Source/version preparation and artifact evidence
are deliberately separate commits. No production selection, service activation,
release tag or remote operation follows from this pending record.
The artifact's source identity is the REL-010 commit; the later REL-012 evidence
commit is distinct and does not retroactively become the build's source.

## Completion evidence

Not complete. Record actual source/tool/artifact identities, compatibility,
container/build gate outcomes, unchanged package inputs, retained-state/review
evidence and residual holds, then update the [progress audit](../../progress.md)
and selector in the same work-package commit.
