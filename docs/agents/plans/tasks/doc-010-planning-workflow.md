# DOC-010 — Establish plan and task tracking

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `5b568472be0d289efa847ad3633be24ce739fd21ebdc1d86d052b86f351f1856`,
original content SHA-256 `b6c8e50e5ee7ad51c4bfce4f6ba72af4ffcb889c256d11d860218a3595876e23`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Work package | `DOC-010` |
| Plan | [Planning workflow](../2026-10-17-plan-planning-workflow.md) |
| Status | completed |
| Dependencies | None |
| Updated | 2026-10-17 |

## Scope

Create the dated-plan and task directories and current-plan selector. Document
lifecycle, proportional templates, existing work-package task IDs, authorization,
resume/closure, and progressive context loading. Reconcile agent and human
entry points with the active-tracking/historical-audit split. Record the new
planning invariant and decision while preserving existing history and backlog.

## Required context

- [Existing agent workflow](../../workflow.md) and
  [planning guide](../../planning.md).
- [Engineering invariants](../../../invariants.md#framework-and-engineering).
- [Router decision 81](../../adr/decision-081.md),
  [workflow decision 82](../../adr/decision-082.md), and
  [register decision 106](../../adr/decision-106.md).
- [Planning decision 107](../../adr/decision-107.md).

## Acceptance criteria

- [x] A dated plan and individual task records demonstrate the new conventions.
- [x] `current.md` selects no active plan when setup is complete; existing
      backlog and operator handoff remain in their original records.
- [x] Agent startup, planning guide, workflow, conventions, invariant register,
      ADR policy, and human documentation consistently define authority and upkeep.
- [x] Authorization to implement suffices to activate; draft plans do not
      authorize execution or require a separate routine activation confirmation.
- [x] The gate and documentation link/identity checks pass; evidence is recorded
      in this task and the completed `DOC-010` progress entry in the same commit.

## Validation and completion evidence

Completed 2026-10-17, `DOC-010`, this commit.

- All acceptance criteria are met. The setup plan is completed and retained;
  the current selector has no active plan or next task. Existing backlog,
  including `RET-011`, and Operator handoff were not migrated or activated.
- `scripts/check.sh` exited `0`: lock, format, lint, types, 1,750 Python tests
  passed (40 opt-in tests deselected), 45 historical frontend tests passed, wheel/sdist
  and production plugin builds passed.
- Documentation link/anchor, plan filename/backlink, task identity, active-plan
  consistency, ADR index/decision coverage, and whitespace checks pass.
- Invariant/ADR review added `INV-011` and decision 107. Prior decisions 82
  and 106 retain their reasoning with explicit tracking-authority amendments.
  Agent/human entry points and the legacy-plan/progress amendments agree on
  authority, activation, dependency ownership, scope, and retained history.
- Completed audit evidence is recorded in
  [the DOC-010 progress entry](../../progress.md#dated-plans-and-individual-tasks-doc-2026-10-17).

## Blockers and handoff

None. No pre-existing backlog item has been activated.
