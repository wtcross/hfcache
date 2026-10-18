# API-013: Move CLI writes onto the API and preserve resumable observation

| Field | Value |
| --- | --- |
| Work package | `API-013` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-012](api-012-migrate-read-cli-and-candidates.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-013: migrate CLI writes and add operation observation` |

## Scope and acceptance

1. Migrate sync, all actual verification, default/probing doctor, apply maintenance, repair, and guarded init to typed operation submissions. No operational CLI command imports or executes a direct mutation backend. Keep initialization confirmation requirements and server maintenance refusal legible.
2. Wait for terminal results by default. Emit exactly one schema-1 command envelope on stdout and preserve domain exit codes, warning aggregation, quiet/verbose/no-color behavior, and report/run correlation. A 202 receipt is not the legacy command result.
3. Add `operations show`, `operations wait`, and authenticated `operations lookup`, plus an explicit detached-submission mode with its separately documented output. Print the nonsecret submission key to stderr before the initial mutation POST, including in quiet mode for safety correlation, and print the accepted operation identity before waiting. An explicit --idempotency-key supports a deliberate same-key retry. Poll bounded sanitized events for progress, preserving the parseable final envelope and not streaming token-bearing raw server logs.
4. On Ctrl-C, timeout, connection loss, or client process death, state that accepted work may continue and retain the operation/key for reconnection. An interrupted wait produces the documented client failure, never fabricated domain success or automatic cancellation/replay. Keep operation deadlines distinct from HTTP poll timeouts.

## Contracts, invariants, and ADRs

`INV-006`, `AD-16`/`AD-17`, `TX-07`; plan §§4–7.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update CLI/API-client examples for submit/wait/resume/detach, transport versus execution failures, event streams, Ctrl-C, and service-stop semantics. Update operations/recovery docs and change notes in this package.

## Validation

Planned checks, not execution evidence:

Each write command through a real temporary server with fake archive/Hub; successful and failed terminal envelopes; nonzero priorities; disconnect before receipt acknowledgement and recover by key lookup, disconnect after admission, retry same key, SIGINT waiting, operations wait later, event cursor resume, detached output, API down with no local fallback, and maintenance-disabled init. Run `scripts/check.sh`.

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
