# API-001: Activate the feature branch and specify the transport boundary

| Field | Value |
| --- | --- |
| Work package | `API-001` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | None |
| Phase | 0 — Contracts and activation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-001: activate REST and MCP plan and define interface contracts` |

## Scope and acceptance

1. Reconcile the reviewed SHA with current git history, current-plan selection, task IDs, and operator handoff. Recognize the imported draft records as intended input; preserve unrelated work. Create or resume `feat/rest-api-and-mcp` safely and record its actual base SHA. Activate only after an implementation instruction.
2. Establish the initial `docs/api.md` operation/role/effect matrix for every command and mode in plan §4, plus service/server architecture contracts. Mark future features as planned, not deployed. Preserve the CLI-only historical text with dated amendments where required.
3. Record numbered decisions for the transport/service boundary, incremental dependency additions, and the narrow bounded submission registry. Explicitly amend the closed-runtime/framework boundary rather than hiding a new home-built workflow system beneath HTTP.
4. Review FS/TX, credential, output, consumer, Cockpit, and planning invariants. Identify new constraints and their later enforcing packages; do not label an unimplemented constraint as proven. Import all pending task records and select this task before implementing subsequent packages.

## Contracts, invariants, and ADRs

`FW-01`–`FW-04`, `INV-011`; planning/workflow and ADR maintenance; plan §§1–4, 9–12.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Create the API contract skeleton and planned server documentation. Update affected architecture/FW ADR notes, ADR index, plan metadata, current selector, and progress. Keep all later task statuses pending.

## Validation

Planned checks, not execution evidence:

Baseline `scripts/check.sh`; verify plan/task links, unused IDs, branch identity, and no implementation files or unrelated backlog activated. Record unavailable optional toolchains accurately. Check all 14 existing top-level command families and their modes are represented, including `archive init`, doctor probes, and quarantine.

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

Activated on the requested feature branch at base
`86f6e8bbf78503497cb4c913c10b6612ee6b5aeb`; `git fetch github` confirms
`github/main` matches that base. Only the intended draft records were untracked.
No conflicting IDs or other active plan. All later tasks remain pending.

Reviewed FS/TX, INV-001–011, FW and AD-17/21, consumer and Cockpit boundaries.
Decisions 108/109 amend the transport/dependency and narrow receipt boundary;
INV-012–016 label target constraints with their later enforcement owners.
The parity table covers all 14 legacy families/modes, explicitly adding sync
omitted by the draft route table. Future enforcement is labelled planned.
API-002 records the unmanaged-selector mismatch for deliberate correction.
Operator-only deployment checks remain explicit handoff items, not asserted passes.

## Completion evidence

2026-10-17, API-001, this commit. Activation and 29-row/11-column parity
contract complete, all 14 command families covered. New API/server docs and
decisions 108/109 label future implementation explicitly; invariant and ADR
review described above complete. All 27 new plan/task/contract local-link
checks pass; git diff whitespace check passes. Baseline `scripts/check.sh`
exited 0 (1,750 Python, 45 Cockpit tests). Post-change `scripts/check.sh`
exited 0: lock, format, lint, types, 1,750 Python tests, 45 Cockpit tests,
wheel/sdist and production plugin builds. No optional host/live tests run;
no implementation files, dependencies, production state or unrelated backlog
changed. [Progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17).
