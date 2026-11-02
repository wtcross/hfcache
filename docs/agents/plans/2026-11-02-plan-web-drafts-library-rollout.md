# Publish and deploy the draft-safe Library update

| Field | Value |
| --- | --- |
| Status | completed |
| Created | 2026-11-02 |
| Authorization | User instruction on 2026-11-02: commit changes on main, push Forgejo/GitHub, then deploy this host |
| Tracker | [Current plan](current.md) |
| Starting source | main at `02f2827`; WEB-028/029/030 already separately committed and gated |

## Outcome and scope

Publish the approved main commits, prepare unused immutable0.3.1 source, then
replace the recorded local rootless0.3.0 deployment through the official guarded
installer. Build from clean committed detached source; keep source, artifacts and
operational evidence identities separate. Preserve root `node_modules/`, all
original configuration/candidates/backups/credentials, stores/handles, local
locks, predecessor releases, six permission flags and intentional inactive guard
setting. No archive/NAS content or metadata change, archive workload, calendar
activation, reboot, other-host work, privilege weakening, operation replay or
registry publication. Existing boot/NAS/consumer/confinement companion holds stay.

The new instruction supersedes the preceding source plan's no-push/no-deploy
boundary for this release alone. Initial branch pushes publish main only;
the preceding explicit no-tag instruction is not separately lifted by the new
request, so create/publish no tag. Record exact deployed source/artifact identities
as a user-scope exception to the normal release-tag rule, preserving all tags.

## Contracts and decisions

Review agent workflow/planning/release/environment, deployment Upgrade and drain /
Acceptance checklist, container/runtime and web deployment contracts. Review
INV001–003/018–022, FS19/21–23 and relevant ADR126–129/145–147/153–154/158–159/162.
No new architecture, dependency or durable API/archive/config/receipt format is
intended; no cross-format drill is triggered by these frontend changes. Verify
actualdiff rather than infer this from the version. No old rollout phase may be
replayed: old scripts are references for new reviewed, exclusively named outputs.

## Tasks

| Order | Work package | Depends on |
| --- | --- | --- |
| 1 | [REL-017: Publish and prepare0.3.1 source](tasks/rel-017-web-drafts-library-release.md) | None |
| 2 | [OPS-026: Replace the local rootless web release](tasks/ops-026-local-web-refresh.md) | REL-017 for build/stage/effects; read-only inventory/preparation may run in parallel |

## Acceptance

1. Existing WEB commits and new release/evidence commits are on main and verified
   on Forgejo/GitHub without force; preserve unrelated untracked files and tags.
2. Version0.3.1/lock project metadata, changelog/README and strict web/build gate
   pass, then REL-017 commit supplies immutable clean detached build source.
3. Canonical repeated full-web artifacts and rootless image have exact source,
   wheel/closure/UI/helper/protected index identities; no runtime resolution/pull.
4. Fresh protected backup/inventory and actual executor/helper/inspector drains,
   original noncreating-lock handoff, official stage/switch and matching helper
   index/policy binding precede startup. No security or permission relaxation.
5. Actual selected release/TLS/auth class/MCP/private worker/read-only original
   operation/state/confinement checks pass; original files/stores/handles/locks
   remain preserved. Genuine positive Basic/UI/helper reads use existing authorized
   human authentication, never a bearer, forged peer or copied password.
6. Restore the intentional inactive guard only at reviewed zero-executor handoff;
   helper READY before bridge/API. Keep automatic boot recovery unconfigured and
   all prior independent holds explicit. Never infer NAS/workload acceptance.
7. Record actual installed versus exact-bundle owned-fixture browser evidence
   separately, the explicit user no-tag exception, complete evidence /
   docs/progress, required gate before each commit and clear selector at completion.

## Lifecycle

- 2026-11-02: Activated by the user's new publication/local-deployment instruction;
  reconciled clean main `02f2827`, root `node_modules/` preserved, both remotes at
  `f7d1246`. Existing installed0.3.0 and all live-state holds require fresh proof.

- 2026-11-02: Review retains the earlier explicit no-tag restriction because the
  newer instruction authorizes main publication and deployment but does not
  mention tags. Proceed with authorized work; record exact deployed source and
  artifacts without changing the general future release-tag policy.

- 2026-11-02: REL-017 completes metadata, dependency/format review and the full
  strict source/web/build gate; this commit is the immutable build source.
  OPS-026 starts with fresh read-only host inventory and reviewed new recipes.
  Actual construction, deployment and installed acceptance remain pending.

- 2026-11-02: Canonical construction, owned runtime proofs, preserved guarded
  production deployment, final helper-first restart and complete installed
  inactive-state automated checks pass for clean source`c23abba`, image716/UIbca.
  The final strict web/build gate passes with1253 names/hashes unchanged. Original
  failures and scoped recovery/audit qualifications remain in the task evidence;
  no new application source, architecture, dependency or durable format changes.
  OPS-026 is blocked on the required genuine trusted-terminal administrator
  receipt: existing credentials are not available to the agent, no authentication
  is attempted, and the human `inactive1` output is absent. Keep this plan active
  and current selector at that prerequisite. The uncommitted OPS documentation
  package is preserved; no completed task/plan/OPS commit or new tag is inferred.
  All prior source commits are already separately published. Complete the
  remaining acceptance before package closure and final main publication.

- 2026-11-02: The user completes the protected administrator validator. The
  genuine eleven-GET receipt `b3622261` and HostStatus `010fc59d` pass verified
  TLS, indexed assets, stable session and actual helper/configuration reads with
  preserved grants. Independent protected review `b966c86d` confirms receipt and
  artifact bindings, unchanged running identities and original state without
  replaying authentication or services. The former blocker is resolved. All
  scoped acceptance and strict gates pass; this OPS-026 commit records completed
  evidence/progress and clears the active selector. Main-only publication is
  verified against both remotes in the retained publication receipt. Existing
  tags, predecessor releases, root node_modules and independent holds remain.
