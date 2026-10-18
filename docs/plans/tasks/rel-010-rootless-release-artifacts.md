# REL-010: Review and commit 0.2.0 source

| Field | Value |
| --- | --- |
| Work package | `REL-010` |
| Status | completed |
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

Activated 2026-10-18 after committed OPS-015 (`edef480`). The local implementation review
fast-forwarded local `main` from `86f6e8b` to `edef480`, then returned to
`feat/rest-api-and-mcp`; no remote was changed. Source version preparation is
the only task in progress on activation. Root verifies no other worktrees and a clean starting
tree; normal switch/merge --ff-only/return commands all exit 0. Root owns only
pyproject/lock version metadata and the actual gate; Markdown has one owner.

OPS-015's handoff separates this source/version commit from REL-012's clean
artifact execution/evidence commit. Version 0.2.0 reflects the breaking API-only
operational CLI and rootless deployment contract. README/CHANGELOG describe
preparation, not deployment/tagging; working-tree builds remain previews.
Retain all previous artifacts and the
OPS-014 barriers; no remote publication is authorized.

INV-005/010/011/014/015 and decisions 65/75/79/126/127 are reviewed. Metadata and
release-status wording change no durable format, domain behavior, dependency
version or architecture; no new decision is needed.

Root changes only the hfcache project version 0.1.10→0.2.0 in pyproject.toml and
uv.lock. `rtk uv lock --offline` exits 0; parsed before/after comparisons show all
93 nonproject lock records identical (94 packages total). No runtime code changes.
README and CHANGELOG now explicitly say preparing 0.2.0, not deployed/tagged,
preserving historical feature/deployment evidence and local acceptance holds;
both are frozen before the gate's wheel stage.

The required NAS-masked `scripts/check.sh --with-build` gate ran in
.scratch/rel-010-gate.log, unit hfcache-rel010-gate, invocation
541f3e5c6dfe49dc8a7e0d5dd1319cbb, session 16776, with confirmed actual exit 0.
It passes 405 formatting checks, Ruff/whole types 0, 3,792 Python tests with
40 deselected in 461.15 seconds, 0.2.0 wheel/sdist and all three locked isolated
installation profiles. Cockpit lint/style/types, 135 tests in 2.273 seconds and
build 1,221 ms pass; four extra wheel smokes pass in 7.15 seconds. Unit runtime
is 8 minutes 34.329 seconds. Log SHA-256:
0ec960317ee6ec0b73c3ec72428c835edf6d4e66f888c4cfc330f767c1dd529f.

Working-tree preview wheel SHA-256:
4cd663dbdedc6edb10f989a18e5035c28de21d7e5db2da68efddc24582400e2b;
preview sdist SHA-256:
23ea664da8101d51b947fc3f2ca1e99080ec091b975bf5ff52e4f144ef114733.
These are not deployment artifacts. REL-012 must build final immutable artifacts
from clean committed source and record distinct artifact/source identities.

## Completion evidence

Completed 2026-10-18 in this work-package commit. Local implementation review/
fast-forward, project-only version preparation, unchanged 93 dependency records,
README/CHANGELOG readiness and required full --with-build gate pass as recorded.
INV-005/010/011/014/015 and 65/75/79/126/127 review needs no new decision or
format/behavior/dependency amendment. The [progress audit](../../progress.md),
plan/current, local links/dependencies and whitespace agree. REL-012 is next
pending until this source/version commit exists; no deployment/tag or final
clean-source artifact is claimed. NAS read-only/masked writers/held guard and
all installed/full-storage/other-host/remote-publication holds remain unchanged.
