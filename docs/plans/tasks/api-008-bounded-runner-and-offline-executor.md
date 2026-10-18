# API-008: Run bounded operations and implement the private offline executor

| Field | Value |
| --- | --- |
| Work package | `API-008` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-007](api-007-operation-receipts-and-idempotency.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-008: add bounded execution and isolated verification protocol` |

## Scope and acceptance

1. Implement one heavyweight command lane, bounded FIFO admission, queue/lock deadlines, and a separate small read pool. Carry frozen config and correlation; stale fingerprint checks occur inside the command’s archive lock. Keep the lock independent of daemon admission and avoid nested flock acquisition.
2. Add the private verification-worker protocol and entry point. It accepts only verification mode/scope, exact operation ID, and expected installed-config fingerprint. Add protected Unix-socket/peer checks, bounded messages, durable terminal receipts, and status/reattach by exact operation identity. It loads no inbound API/Hub credentials and executes the shared fully guarded verification service.
3. Implement an injectable delegation adapter; the production API refuses verification if the isolated worker is unavailable. Do not create an insecure in-process production fallback, generic exec endpoint, or broad systemctl/sudo grant. Shipped hardening/unit integration is completed in API-014.
4. Stop admission before draining; join domain work before releasing safety ownership. Handle process death, incomplete receipts, a surviving verification worker, and dropped clients explicitly. Never automatically replay old queued/running mutations on startup; classify uncertain work as interrupted and preserve evidence.

## Contracts, invariants, and ADRs

`AD-17`/`AD-19`, `FS-19`, `TX-07`, `INV-002`/`INV-003`/`INV-007`; plan §§5–6.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Document execution state transitions, deadlines, no-replay semantics, worker trust boundary/protocol, standalone limitations, and drain/recovery procedures in server/API/operations docs. Add verification-isolation ADR amendments and relevant invariants.

## Validation

Planned checks, not execution evidence:

Bounded saturation, FIFO/deadline tests, cross-process lock contention, old-job restart/no-replay, crash after domain result before API receipt, surviving-worker reattachment, invalid peer/frame/mode, unavailable executor, and shutdown during sync producer activity. Assert lightweight reads stay responsive and no worker double-starts. Run `scripts/check.sh`.

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
