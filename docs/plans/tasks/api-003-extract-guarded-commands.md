# API-003: Extract guarded command services and close verification lock gaps

| Field | Value |
| --- | --- |
| Work package | `API-003` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-002](api-002-extract-queries-and-results.md) |
| Phase | 1 — Shared services |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-003: extract guarded commands and serialize verification persistence` |

## Scope and acceptance

1. Move sync/plan/doctor and prune/purge/recover/quarantine/repair/init command orchestration into typed services. Reuse existing domain functions and preserve command-specific ordering, refusal rules, exact run/result provenance, and partial failure payloads.
2. Preserve lock-before-preflight and reconciliation-before-Hub for commands that require it. Preserve quarantine’s different rule: validate selected evidence, refuse unfinished unrelated work, and never reconcile it implicitly. Make lock ownership explicit to prevent nested acquisitions.
3. Correct all non-estimate verification modes to acquire the common archive lock before resolving their scope and hold it through hashing, report write, and catalog read/merge/write. Remove or amend the persistence comment that atomic replacement justifies concurrent merges. Estimates remain non-persisting reads.
4. Add a reproducible interleaving regression test showing catalog updates cannot lose unrelated failures or verification state. Extend command guard tests to probing doctor and explicit initialization without changing their domain safety rules. Do not operate on the live archive.

## Contracts, invariants, and ADRs

`AD-13`–`AD-20`, `FS-19`, `TX-01`–`TX-07`, `INV-006`/`INV-007`; plan §§2, 4–6.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update CLI verification effect/lock tables, architecture/invariants, verification persistence contract, and offline-verification/related ADR amendments. Record the observed baseline protection gap and the chosen tighter boundary, not an unsupported claim of observed production corruption.

## Validation

Planned checks, not execution evidence:

Existing sync, verification, retention, purge, repair, recovery, quarantine, preflight, and initialization suites; new multi-process lock/interleaving tests using temp paths. Assert every non-estimate verification persistence call occurs while the archive lock is held. Test failure paths release locks only after child transfer work stops. Run `scripts/check.sh`.

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
