# Ignore local root Node dependencies

| Field | Value |
| --- | --- |
| Status | completed |
| Created | 2026-11-02 |
| Authorization | User requests ignoring node_modules, committing and pushing main to Forgejo and GitHub |

Add the root-only `/node_modules/` rule to `.gitignore`, preserving the existing
directory and nested ignore behavior. This implements the existing development
contract against committing dependency trees. No runtime, release, deployment,
archive or dependency change is included.

| Order | Work package |
| --- | --- |
| 1 | [DOC-020: Ignore root Node dependencies](tasks/doc-020-root-node-ignore.md) |

Acceptance: root dependencies are ignored; unrelated nested paths remain visible;
the physical directory is preserved; `rtk scripts/check.sh` passes; one commit on
main is verified on both remotes without force or tags. Complete the task and
progress record and clear the active selector in that commit.

Review FS-19/AD-16, INV-010, FW-03/04 and ADR008/143. Existing contracts cover
this repository hygiene fix; no new invariant, architecture or ADR is needed.

## Lifecycle

- 2026-11-02: Activated directly by the user's implementation/publication request.
- 2026-11-02: Root-only matching, unchanged web/nested behavior and physical
  directory preservation pass. The default repository gate passes; this commit
  completes DOC-020, records evidence and clears the selector. Main publication
  is verified on both remotes with existing tags preserved.
