# REL-017: Publish and prepare0.3.1 source

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Publish and deploy the draft-safe Library update](../2026-11-02-plan-web-drafts-library-rollout.md) |
| Depends on | None |

## Scope and acceptance

Publish existing reviewed main02f2827 to both named remotes, verify exact refs.
Assign unused0.3.1 in pyproject and project-only uv.lock metadata; update changelog
and README candidate/installed status. Preserve all runtime dependency pins,
archive/config/API/operation formats and untracked root `node_modules/`.
Review relevant invariants/ADRs and release contracts, run strict
`rtk scripts/check.sh --require-web --with-build` as login user with private empty
read-only archive shadow and immutable source freeze, then commit one REL-017
package and push main to both. No deployed-ready claim, tag, service or archive
mutation occurs in this source package. Source commit is the later detached
artifact target; OPS evidence must not silently change that target.

## Validation and evidence

Main02f2827d4ffbc04571716d702b6a2b7969c1077b is pushed and independently verified
on Forgejo/GitHub from f7d1246, branch-only. Receipt:
`.scratch/rel017-validation/initial-main-publication.json`. Existing tags and
untracked root `node_modules/` remain untouched.

Contract-first README/changelog distinguish source0.3.1 candidate from unchanged
installed0.3.0. pyproject/uv.lock change only projectversion; semantic TOML checks
prove all94 locked packages/runtime pins unchanged. No backend/helper/container/
SELinux/wire/config/archive/receipt source change occurs versus deployed3d6670d
apart from gate tooling and the three approved browser packages; no cross-format
drill is triggered. INV001–003/018–022, FS19/21–23 and applicable existing release/
helper/browser ADRs reviewed; no new invariant or architecture is introduced.
Focused offline lock/docs/whitespace checks pass. Initial system-Python docs
attempt lacked markdown_it; the existing project environment passes213human/
29helper checks without dependency changes. Strict release gate passes.
Prior WEB028–030 gates remain separate historical acceptance for02f2827.

Completed strict `rtk scripts/check.sh --require-web --with-build` passes as
login UID1000/nice10 with a private empty read-only tmpfs archive shadow:
9,594 backend tests, 4,115 combined web tests (3,757 unit), 16 wheel smoke tests,
three locked installation profiles, 11 built Chromium workflows, actual 200%
Library zoom and the real HTTP/API React fixture. Coverage is 95.17% lines /
90.15% branches. All 1,252 frozen input names and hashes remain unchanged.
Inner elapsed time 1,607.577 seconds; raw gate log SHA256
`a75e865acda3979de99234ad12b00771f56a9ceb92c9402a5e55531c5f9a2683`.
Result: `.scratch/rel017-validation/rel017-gate1-result.json`; private-shadow
log SHA256 `c77e9ec240a21a583f94b4078b41ed26f0ca7b165c71cc5646cd5f04aec4e84a`.
The no-tag instruction remains a narrow user-scope exception to normal release
policy (progress decision 163); no architecture or invariant changes.
This commit supplies the clean detached artifact source; protected build,
installed acceptance and guard restoration remain the next task's work.

Only the exact successful owned temporary root `/var/tmp/.r17a` is retired after
complete verified inventory (179,583 entries / 596,031,014 regular-file bytes),
no-mount/no-live-owner proofs and repeated original device/inode checks.
Compressed manifest SHA256
`f5338fca1548329e15710c5bee3d8b7080abe613500368ca6fc3a0131f98f7eb`;
receipts in `.scratch/rel017-gate1-success-temporary-retirement/`. Raw logs,
browser reports, all failed evidence, old artifacts/caches and root
`node_modules/` remain. Final documentation alignment passes 213 human documents
and 29 helpers; local links and raw whitespace checks pass.
