# DOC-020: Ignore root Node dependencies

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Ignore local root Node dependencies](../2026-11-02-plan-root-node-ignore.md) |
| Depends on | None |

Add `/node_modules/` to the root `.gitignore`. Preserve all dependency contents,
the existing web ignore rule and unrelated nested fixture visibility. Commit on
main and push that exact commit to Forgejo and GitHub without tags or force.

## Contract and invariant review

The development guide and ADR143 already require dependency trees to stay out
of Git. FS-19/AD-16 require preserving the existing physical directory; INV-010
and ADR008 require the repository gate. FW-03/04 remain unchanged: no dependency,
runtime behavior or durable format changes. No new invariant or ADR is warranted.

## Validation

`git check-ignore --no-index -v` resolves the root probe to `.gitignore:8` and
`/node_modules/`; the web probe still uses `web/.gitignore:1`; an unrelated
nested fixture probe remains unignored. No dependency files are tracked.
The existing root directory retains device64770/inode14323967, mode0755 and
UID/GID1000 before and after validation; its contents are not written or deleted.

`rtk scripts/check.sh` passes in1286.43s:9594 backend tests, build and three
locked installation profiles. The login-user run uses an owned temporary root
and private empty read-only archive shadow;1255 frozen file names/hashes remain
unchanged. Log SHA256
`3f721433582fc73570348f5cea7143b566f86c9420de7f4e0abd4d2276597c9f`;
shadow log `22a4768746cd13c7e445d8ec2afa5a2ff4a1c6a8b8e58866b32f2fd80ebceb3b`.
Raw results and focused checks remain under `.scratch/doc020-validation/`.
No frontend/runtime/dependency or installed acceptance change is implied.

Post-gate completion records pass documentation alignment (213 human documents /
29 helpers), all69 focused documentation tests and raw Git whitespace checks.
Only the newly owned successful gate temporary directory is retired after a
complete159824-entry manifest, two stable inventories and fresh global no-owner
checks. Manifest75596597 and retirement receipt ebb37707 remain outside Git with
all raw logs; no existing dependency directory, cache or artifact is removed.

## Completion

This commit records completed progress and plan closure and clears the active
selector. Final exact main refs and unchanged tag maps are verified in
`.scratch/doc020-validation/publication.json`. No deployment or tag is included.
