# API-007: Persist bounded operation receipts and idempotent admission

| Field | Value |
| --- | --- |
| Work package | `API-007` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-006](api-006-fastapi-lifecycle-and-reads.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-007: persist operation receipts and idempotent admission` |

## Scope and acceptance

1. Implement versioned service-private JSON operation receipts, result references, and bounded sequenced events under an injectable local state directory. Reuse deterministic atomic write/fsync primitives and protect permissions; never place this control state in publication trees.
2. Persist admission before work becomes runnable and before returning 202. Make a receipt the authoritative key binding so a crash cannot leave an accepted operation without deduplication. Rebuild only derived indexes; do not introduce SQLite, a broker, or journal-driven execution.
3. Bind each Idempotency-Key uniquely within the authenticated principal namespace and compare its stored canonical route/request digest. Same request/key returns its original operation despite a later config change; mismatched reuse, including another route, returns 409. Add a non-submitting authenticated key lookup for lost acknowledgements. Enforce unique concurrent admission and require keys for side effects.
4. Define queued/waiting/running/terminal/interrupted transitions, current/result/events APIs, key/result retention, oversized/full storage refusal, and malformed/unknown-version record preservation. Never delete unfinished or unexplained receipts. Expose no raw credentials/candidate secrets. A status fetch must never run an operation.

## Contracts, invariants, and ADRs

`AD-12`, `AD-14`/`AD-16`, `FW-01`/`FW-02`, `INV-002`, `INV-005`; plan §5.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Add receipt/result/event schemas and compatibility rules to schemas/API docs, idempotency examples, retention/expiry/uncertain-state runbook, and the bounded-registry decision with explicit FW scope amendment. Update security and recovery docs.

## Validation

Planned checks, not execution evidence:

Fault injection before/after each fsync/rename/admission step, simultaneous duplicate POSTs, conflicting keys/routes, lost-acknowledgement key lookup, reconstruction of indexes, unknown record versions, full disk, safe retention, and inaccessible results. Verify no mutation executes without a durable key binding. Run schema fixtures/compatibility tests and `scripts/check.sh`.

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
