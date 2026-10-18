# API-002: Extract transport-neutral query services and command results

| Field | Value |
| --- | --- |
| Work package | `API-002` |
| Status | completed |
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

Shared `ExecutionContext`, `ServiceResult`, `RepositoryQuery` and
`PublicationQuery` records are immutable. `MetadataQueries`/`LocalQueries`
provide local reads; CLI delegates and retains rendering. Credential resolution
remains at the trusted adapter boundary, outside the read protocol. New
identity-based report readers support sync, recovery and verification reports;
no-follow anchored opens reject symlink artifacts/parents. Reference/manifest
identity, generation and canonical locators are checked, including current
versus retained-reference agreement. Exact vanished instances never substitute.

Corrected the characterized unmanaged selector/status omission to the existing
contract. Configuration order is preserved; unmanaged entries append in canonical
order. Existing catalog tolerance, envelope shapes and offline local version
are retained. No durable format or storage algorithm change.
Operator-only deployment checks remain explicit handoff items, not asserted passes.

## Completion evidence

2026-10-17, API-002, this commit.

Extracted immutable execution/request/result records and local query services;
CLI delegation preserves schema-1 envelopes/rendering. Fixed documented
unmanaged status/list selectors and configured-plus-unmanaged status ordering.
ID-based existing report/reference/manifest reads validate canonical identity,
locators/generation and no-follow containment; exact vanished instances fail.
Reviewed FS-08–12/16, AD-06/10/17, INV-005–008/012 and decisions 51/62/108:
existing contracts preserved; no new ADR or durable format required. Updated
architecture, CLI, API, consumer, invariant and Unreleased documentation.
336 existing targeted tests and 47 new query/evidence tests pass. Initial gate
stopped on two deliberate immutable-mutation test type errors; targeted test
annotations corrected. Final `scripts/check.sh` exits 0: lock, format, lint,
types, 1,797 Python tests, 45 Cockpit tests, wheel/sdist and plugin builds.
Changed documentation links, parity-table structure and git whitespace pass.
No host/live checks or production operations. HTTP traversal review/pagination
and bounds remain API-006 scope; runtime HTTP routes remain planned.

[Progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17).
