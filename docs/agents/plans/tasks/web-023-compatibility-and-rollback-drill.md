# WEB-023: Verify old clients, durable formats and evidence-preserving rollback

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P5 |
| Depends on | [WEB-022](web-022-installed-functional-acceptance.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-023: <completed outcome>` |

## Read before implementation

docs/agents/release.md format drill; old retained Git source/install targets; new cards/helper/config receipts; migration-and-compatibility.md.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build/install exact supported old clients from retained Git objects with locked offline closure, then exercise new server's unchanged routes and schemas through Caddy for reader/writer/MCP. Verify old literal config validate/plan, no-Origin bearer auth, operation public fields/canonical idempotency and fourteen-tool behavior. Do not 'fix' compatibility by allowing unknown unsafe schema fields globally.

Drill old binaries against copied fixture state containing new card directories/private helper application kinds and curation records. Determine real compatibility/refusal; record target-specific backup/config/observation requirements. Preserve all unknown/new records and original handles. Test UI-disabled backend-only operation and browser schema/version drift.

Rehearse native/rootless/frontend/application rollback using immutable indexed artifacts on disposable targets only. Prove actual executor drain, common locks, candidate/backup/store retention, coherent UI/backend selection, password/subject continuity and original-op observation. A target unable to observe unresolved state blocks rollback; no force kill, record deletion, auto-replay or overwrite of old artifacts/tags.

## Unit and component validation

Tests cover strict legacy response fixtures, unknown new formats, missing asset behavior, compatibility metadata and rollback refusal paths with preserved state.

## Integration validation

Execute actual old installed clients/binaries, not only serializers, against new server/state fixture copies. Record source/wheel hashes and exact success/refusal classifications.

## Functional validation

In disposable installed targets complete upgrade/open-browser/rollback/reconnect scenarios through Caddy, prove REST/MCP and safe original handles still usable where compatible, and verify incompatible target refuses without data loss.

## Human documentation deliverables

Write human migration/rollback compatibility tables, prerequisites and stop conditions in migration-from-cockpit.md, deployment.md, schemas/discovery/release notes. No production deployment-status claim.

## Acceptance

Compatibility is observed with real target artifacts; rollback either safely works under documented preconditions or explicitly refuses preserving evidence. New durable state is never deleted to manufacture compatibility.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-023, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
