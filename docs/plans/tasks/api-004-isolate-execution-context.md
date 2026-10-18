# API-004: Make correlation and offline execution safe for concurrent requests

| Field | Value |
| --- | --- |
| Work package | `API-004` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-003](api-003-extract-guarded-commands.md) |
| Phase | 1 — Shared services |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-004: isolate request context and preserve offline execution boundaries` |

## Scope and acceptance

1. Replace process-global run correlation with context-scoped or explicitly passed execution data. Configure logging once per daemon startup, not per request, while retaining the CLI’s isolated startup behavior.
2. Define request ID, operation ID, domain run ID, and transaction ID relationships. Generate authoritative IDs server-side and correlate them without replacing existing run/report identities. Propagate context deliberately into service threads and the existing sync producer; restore context after success and exceptions.
3. Keep per-request quiet/verbose behavior in client rendering/event selection rather than changing the server logger’s global level. Extend secret redaction to arbitrary opaque API tokens and sanitize exception/problem contexts.
4. Remove any requirement to toggle `HF_HUB_OFFLINE` in an ASGI process. Verification service must structurally construct no Hub client/credential. Retain process-scoped offline initialization for the isolated executor added later. Preserve the existing durable invocation-mode vocabulary; distinguish authenticated submitter metadata in operation receipts instead of claiming every daemon request is a timer.

## Contracts, invariants, and ADRs

`AD-19`, `INV-002`, `INV-005`/`INV-006`; logging/security and offline-verification contracts; plan §§2, 5–6.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update logging/event and provenance contracts, API correlation fields, security redaction requirements, and architecture concurrency notes. Amend affected ADR rationale where process-per-CLI assumptions no longer hold.

## Validation

Planned checks, not execution evidence:

Interleave two reads and a long operation with distinct IDs, including worker-thread logs, sync producer events, failures, and subsequent requests. Assert no cross-request ID/verbosity leakage, duplicate handlers, stdout logging, or environment mutation. Run existing logging/Hub/CLI suites and `scripts/check.sh`.

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
