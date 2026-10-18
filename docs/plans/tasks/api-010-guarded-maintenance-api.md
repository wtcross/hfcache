# API-010: Expose retention, recovery, repair, quarantine, and guarded initialization

| Field | Value |
| --- | --- |
| Work package | `API-010` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-009](api-009-sync-verification-and-diagnostics-api.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-010: expose guarded maintenance and initialization operations` |

## Scope and acceptance

1. Add separate typed preview/apply routes for prune, purge, recovery, and quarantine, plus repair and initialization. Do not expose a generic command string or bool whose omitted default silently applies changes.
2. For every side effect, check writer capability and idempotency, then revalidate admitted config fingerprint, explicit scope, guards, and applicable reconciliation under the archive lock. Dry-run output grants no future deletion authority. Preserve the one-round prune limit, unmanaged-only purge, batch quarantine proof, and recovery ambiguity refusals.
3. Preserve exact-manifest repair, publication/generation identity, grace periods, original audits, cache API deletion boundary, and unknown evidence. Return domain failures and partial diagnostic payloads without replacing their classifications with generic HTTP success.
4. Initialization is an explicit disabled-by-default maintenance capability on the configured archive only, requiring confirmation plus restated root/UUID. Startup, health, recovery, and missing-sentinel requests must never call init. Do not exercise init or any destructive route against production during implementation.

## Contracts, invariants, and ADRs

`AD-06`, `AD-13`–`AD-17`, `AD-20`, `FS-14`/`FS-19`/`FS-21`–`FS-23`, `TX-06`/`TX-07`; plan §4.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Finish all existing-operation parity rows and destructive-action examples in API/CLI docs. Update security threat/control coverage, server maintenance-gate instructions, recovery/operations guidance, and any affected invariants/ADR notes.

## Validation

Planned checks, not execution evidence:

Adversarial role/mode/scope tests; candidate/scope stale while queued; target newly configured before purge; altered preview; unknown files/repair quarantine; repeat idempotency; pre/post-commit crash fixtures; fake-root initialization confirm/refusal tests and no implicit init. Run all domain regression suites and `scripts/check.sh`.

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
