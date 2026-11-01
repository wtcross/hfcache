# Remove the obsolete interface

| Field | Value |
| --- | --- |
| Status | completed |
| Created | 2026-11-01 |
| Authorization | The user explicitly requests complete repository removal of the obsolete interface and its documentation, after completion of the web UI replacement. |
| Tracker | [Current plan](current.md) |

## Outcome and scope

Remove the obsolete frontend, its dedicated configuration, optional build/test
integration and dedicated documentation. Remove its references from current
human and agent documentation, including superseded historical snapshots. Keep
shared host/client safeguards required by the current web UI, applicable source
attribution, original operation recovery and unrelated untracked files. No host
uninstall, service/deployment change, archive access or history rewrite is
authorized. The user additionally authorizes a normal push of the completed
`feat/web-ui` branch to both `github` and `forgejo`; no other branch or tag is pushed.

The explicit removal instruction narrowly overrides earlier preservation of
obsolete repository material and stable historical document paths. Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4` retains the original snapshots and
execution invocations. Do not fabricate updated historical commands or hashes.
Retain relevant web acceptance evidence with honest historical provenance.

## Contracts and decisions

Review framework/dependency rules, current browser/host authority invariants,
shared runtime contracts and [technical record policy](../technical-record-policy.md).
[Decision 161](../../adr/decision-161.md) records the source-removal and historical
snapshot exception; obsolete interface-only constraints are retired, while
current web permission, confinement, original-handle and rollback rules stand.

## Tasks

| Order | Work package and task file | Depends on |
| --- | --- | --- |
| 1 | [WEB-027 — Remove obsolete interface source and documentation](tasks/web-027-remove-obsolete-interface.md) | None; replacement plan completed |

Independent source, human documentation and historical record edits may run in
parallel within this single work package. Root reconciles shared indexes,
contracts, validation and the local commit.

## Acceptance and validation

- No obsolete frontend implementation, dedicated package/configuration or build
  and test entrypoint remains in tracked source.
- No documentation content or pathname names the removed interface; dedicated
  obsolete guides and records are removed, shared current guidance remains usable.
- Shared web/client/host safeguards and necessary attribution remain intact.
- Documentation discovery, links, snapshots, the 95-case web evidence ledger and
  current plan agree; no historical result is invented.
- Focused affected checks and `scripts/check.sh --require-web --with-build` pass
  as the login user with a private empty read-only archive shadow.
- Record completion and handoff, clear the selector, commit, and push
  `feat/web-ui` normally to both authorized remotes after all required checks pass.

## Lifecycle

- 2026-11-01: Activated from the explicit repository-removal instruction.
- 2026-11-01: User explicitly includes plugin-specific tests in removal and
  authorizes committing and pushing the completed branch to both configured remotes.

## Completion (2026-11-01)

[WEB-027](tasks/web-027-remove-obsolete-interface.md) completes repository removal,
documentation/raster cleanup, current shared-safety preservation and strict
source/build acceptance. Gate3 passes 9,562 backend/4,051 unique web/16 wheel
checks, with all 1,227 tracked inputs unchanged. Original failed runs and exact
historical provenance remain explicit. The current selector clears; source branch
publication is the authorized final step after the local commit, with remote refs
verified separately rather than anticipated in stored evidence. No production,
service, archive, credential, calendar or tag/main-branch change follows.
