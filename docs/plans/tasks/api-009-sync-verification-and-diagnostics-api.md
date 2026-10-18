# API-009: Expose sync, verification, planning, diagnostics, and validation

| Field | Value |
| --- | --- |
| Work package | `API-009` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-008](api-008-bounded-runner-and-offline-executor.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-009: expose sync verification and diagnostic operations` |

## Scope and acceptance

1. Add typed routes for sync, all verification modes, installed-config planning, config validation, and explicit read-only/probing diagnostics. Route long work through the receipt/runner contract; read-only diagnostics and plan still have Hub/resource effects and are never silently treated as local metadata reads.
2. Enforce the route capability matrix: all actual verification and probing diagnostics need the writer bearer; installed planning/read-only diagnostics are available to REST readers. Admission receipts never imply command completion. Use correct terminal Envelope classifications on failures and partial results.
3. Preserve whole-run sync ordering, reconciliation before first Hub request, continuation/stop-on-error behavior, aggregate capacity admission, producer joins, new-content verification, report IDs, and automatic retention boundaries. All verification work delegates to the offline worker.
4. Implement current-config validation without remote arbitrary-path loading. Add candidate schema hooks and authority-compatible validation primitives for API-012, but never accept a request that can select a secret file or an unapproved credential-bearing Hub endpoint.

## Contracts, invariants, and ADRs

`AD-01`–`AD-03`, `AD-17`–`AD-19`, `TX-07`, `INV-004`/`INV-006`/`INV-007`; plan §§4–6.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Complete API examples and parity rows for these operations, clarify semantic read versus probe/report-writing effects, document 202/polling and scope/mode errors, and update CLI/operations reference notes and Unreleased changes.

## Validation

Planned checks, not execution evidence:

End-to-end route/service results with fake Hub, all mode/selector failures, no-bearer/wrong-role tests, full/new/revision verification delegation, offline service failure, sync failure aggregation, unknown transaction refusal before Hub, and client disconnect during a long operation. Run `scripts/check.sh`.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Not started. The draft does not authorize implementation. Record actual changes,
resolved design issues, scope amendments, and any blocker/unblock condition here.
Operator-only deployment checks remain explicit handoff items, not asserted passes.

## Completion evidence

Not executed. On completion record the date; acceptance results; exact commands
and outcomes; invariant/ADR review and amendments; documentation changes; a link
to this package's completed [progress audit](../../progress.md); and any operator
handoff. Then set Status to `completed` in the same commit as the work.
