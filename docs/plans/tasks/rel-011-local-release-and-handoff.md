# REL-011: Record the local release and preserve acceptance holds

| Field | Value |
| --- | --- |
| Work package | `REL-011` |
| Status | completed |
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

Activated after OPS-016 committed as `11ddd55`. The deployed 0.2.0 application
artifacts remain clean-source `481fcc4`; the reviewed tag target also contains
the separately installed fixed host guard/bridge policy. This is an evidence-only
local release closure: no application, image, profile or host change is planned.
The API-to-worker SELinux hold, NAS-ro/original lock/writer masks and forbidden
storage tests remain explicit. The release gate and actual local annotated tag
must complete before this task closes; no remote publication is authorized.

Root's clean detached reviewed worktree is /var/tmp/hfcache-rel011-reviewed at
11ddd55. It anchors the annotated tag's source precondition while
this evidence-only closure is prepared elsewhere. Tagging remained provisional
until the actual required gate and root's tag command completed, as recorded
below. Closure cannot alter an image/profile, replace the
deployed artifact identity or silently move an existing tag.

The actual deployed application source is
481fcc4e8f9b3c1975d33d6683290076b455087f, source_dirty=false, version 0.2.0.
REL-012 retains the clean-source build and compatibility provenance:

| Artifact | SHA256 identity |
| --- | --- |
| Wheel | 4cd663dbdedc6edb10f989a18e5035c28de21d7e5db2da68efddc24582400e2b |
| Source distribution | 23ea664da8101d51b947fc3f2ca1e99080ec091b975bf5ff52e4f144ef114733 |
| App image | 869da6ef2fe68756472e8a476ee45c8d8fbccd2ac91ae3d45190359996962fd3 |
| Caddy image | b6112cfbb3ea8dbbb41a9a7910301ecf548ccc9fde9455f5b386d76005459bc6 |
| Indexed 0.2.0 stage | 2a6b8218051fb2909862953017524ecbb01a5c081b507b5c0b7e865a26ba355e |

Image identities use the sha256: prefix in runtime configuration. The reviewed
11ddd55 tree adds separately installed host guard/bridge policy and evidence;
it is not the application artifact build commit. The explicit independent guard
boot binding and final host-state record belong to committed OPS-016. Protected
Podman file-driver secret storage is not claimed encrypted; no secret value or
ad hoc plaintext credential file belongs in release notes or build artifacts.

Rollback must drain actual containers/libpod cgroups without force, preserve
both operation stores, pending observer handles, original lock inodes and old
artifacts, and retain the fixed host readonly guard across app selection. Reload
both managers and inspect effective unit bindings/drop-ins before activation.
The old native 0.1.10 tree is retained evidence, not an automatic compatible
rootless rollback target. Missing old readers never prove nonexecution; disable
MCP deliberately before a server-only/pre-MCP runtime and preserve all state.
Keep NAS ro, all four legacy units masked/inactive and verification scheduling
disabled. API-to-worker SELinux connectivity remains operator hold 22; no allow,
changed container label or host execution bypass is approved. NAS write/full-domain/
NFS workload, other-host and calendar acceptance remain unrun or separately held.

The final NAS-masked --with-build gate runs under invocation
b8ad2b5332294db7b45fd4d491723fa7. No host/runtime/source change is part of REL-011.

## Completion evidence

Completed 2026-10-18. The actual NAS-masked `scripts/check.sh --with-build`
pipeline exits 0: 407 formatted files, Ruff clean, whole Pyrefly 0 (11 suppressed,
59 warnings not shown); 3,827 Python passed/40 deselected in 455.86 seconds;
0.2.0 wheel/sdist and all three locked isolated installation profiles;
Cockpit lint/style/types, 135 tests in 2,274.672993 ms/build 1,126 ms; four extra
wheel smokes in 6.99 seconds. Unit elapsed time is 8m28.285s. Gate log SHA256:
7cd3e0f7bb2eed7ec3c85df8013ecca671e7eb2257af58b8876b0177a29fb0ba.

Root creates actual local annotated v0.2.0 from the clean reviewed worktree.
Verified object d7ad2f180c5faeb289fe90ec9fff59fdaa0ebd4d has type tag and peels to
11ddd55dcb9e7b7be38fdfd076e54e2eadb460a3. The full note at
.scratch/v0.2.0-tag.txt has SHA256
9aec7e2e0a458fbefb777b86f57d9892dc271bcbba2ab8d0f21bf570da7bbe51 and states
artifact provenance, partial acceptance, worker/storage holds, no NAS changes
and no remote publication. App/host sources and deployed images are unchanged.
The closure evidence commit is distinct from both tag target and artifact source;
root plans the final local main fast-forward after this commit, not before it.

Reviewed INV-010/011/014/015 and decisions 65/75/79/121/126/127. Evidence-only
source-precondition wording, release notes and state-retaining rollback remain
consistent; no new invariant, ADR, dependency or durable format is introduced.
The completed [progress audit](../../progress.md) and final links/records/
whitespace checks accompany this commit. All six plan tasks are complete under
explicit partial acceptance; clear only this plan's selection. Worker hold 22 and
all forbidden NAS/full-domain/other-host/calendar checks remain unaccepted.
Follow-up design is separate unactivated work, not completion of this hold.
