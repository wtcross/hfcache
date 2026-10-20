# WEB-008: Implement guarded atomic configuration application and recovery

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-007](web-007-configuration-read-and-preview.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-008: <completed outcome>` |

## Read before implementation

Existing persistent root configuration lock/candidate scripts; operation store/runner; config application contract; host private protocol; config crash cases.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement keyed POST /config/applications and the helper's fixed apply operation. Revalidate internal capability, independent host policy, exact base/candidate, compatible authority and required successful matching preview at execution. Persist safe admission before transmission to the helper and preserve unresolved outcome evidence. No TOML/credentials/raw logs in generic receipts, events, browser registry or public results.

Use the original common config flock inode and defined lock order. Durably retain predecessor, atomically install exact candidate with existing ownership/modes, fsync parent, then confirm exact installed bytes and expected operational fingerprint. Preserve current candidate/backup state and refuse conflicts rather than overwrite unknown evidence. Concurrent CLI/Cockpit/config UI writes must share guards. A tag-only edit still compares exact bytes. New policy affects future admissions; queued stale domain mutations retain existing refusals.

Implement read-only original-operation reconciliation after API/helper crash or lost response. Capture staged/installed/confirmed/unknown evidence in independently versioned private state. No auto-replay, automatic rollback or cleanup after ambiguity; another Apply is blocked until authenticated reconciliation resolves it. Bounded private candidate retention cannot delete unresolved work when full. The helper cannot redirect target/source/path or acquire broader archive rights.

## Unit and component validation

Exhaustively test apply state transitions and failures at candidate stage, backup/fsync, rename, parent fsync, confirmation and result persistence. Check lock inode, mode/owner, base/preview mismatch, permission drift and redaction.

## Integration validation

Use real local helper/API operation stores with injected process/socket failures and racing legacy/new clients. Verify exact on-disk candidate/base/predecessor outcomes, no stale queued execution and only read reconciliation after restart.

## Functional validation

In isolated guest through browser/Caddy, apply a valid edit, observe actual installed bytes, induce response loss after install and reconnect to the original operation without another apply. Exercise failed preview, stale tag edit, quota and helper-denied cases.

## Human documentation deliverables

Document full apply workflow, expected confirmations, backup retention, conflicts, interrupted apply and safe operator reconciliation. Update security/config/schema/API contracts and relevant ADR amendments in the same package.

## Acceptance

A successful UI apply means exact installed confirmation, not only a 202 or valid syntax. Every interruption class preserves evidence and blocks unsafe replay; legacy/shared lock and file permissions are retained.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-008, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
