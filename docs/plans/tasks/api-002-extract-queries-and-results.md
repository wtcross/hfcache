# API-002: Extract transport-neutral query services and command results

| Field | Value |
| --- | --- |
| Work package | `API-002` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-001](api-001-contract-and-activation.md) |
| Phase | 1 — Shared services |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-002: extract shared query services and deterministic results` |

## Scope and acceptance

1. Characterize existing status/list/version/inspection/verification-estimate/config-validation results, selector handling, warnings, and error envelopes using deterministic fixtures. Check documentation versus code instead of silently preserving discrepancies.
2. Introduce typed immutable request/execution/result structures and query services under `services/`. Move orchestration out of Typer callbacks while leaving human/JSON rendering in CLI adapters. Existing CLI behavior stays available during the staged refactor.
3. Preserve refs/manifests as inventory authority, unmanaged repositories, corrupt/missing catalog behavior, local-only status, unknown verification confidence, and exact publication identity. Do not execute Hub work from these local metadata queries.
4. Introduce reusable ID-based report/reference/manifest reads for the REST/MCP metadata surface, with containment and identity validation. Separate this read interface from commands and credential resolution. Keep schema-1 Envelope serialization deterministic; do not widen durable schemas gratuitously.

## Contracts, invariants, and ADRs

`FS-08`–`FS-12`, `FS-16`, `AD-06`, `INV-005`–`INV-008`; CLI and schema contracts; plan §§2–4.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update architecture module/service boundaries, CLI behavior notes, API response definitions, and consumer locator explanations in the same commit. Amend any characterized selector mismatch explicitly.

## Validation

Planned checks, not execution evidence:

Query-service unit tests plus existing CLI, models/reporting, status/list, archive-inspection, and verification-estimate suites. Assert no Typer/FastAPI/FastMCP dependencies in service interfaces, no Hub construction for local reads, and no writes/lock acquisition for metadata queries. Compare legacy envelopes and ordering after normalizing timestamps/IDs. Run `scripts/check.sh`.

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

API-001 read-only review identified a pre-existing discrepancy: status/list
call `_select`, rejecting unmanaged selectors although the CLI contract permits
them; unfiltered status only enumerates configured repositories. Resolve during
extraction against the documented contract with regression evidence.

Not started. Record actual changes,
resolved design issues, scope amendments, and any blocker/unblock condition here.
Operator-only deployment checks remain explicit handoff items, not asserted passes.

## Completion evidence

Not executed. On completion record the date; acceptance results; exact commands
and outcomes; invariant/ADR review and amendments; documentation changes; a link
to this package's completed [progress audit](../../progress.md); and any operator
handoff. Then set Status to `completed` in the same commit as the work.
