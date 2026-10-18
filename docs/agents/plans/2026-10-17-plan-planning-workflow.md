# Establish dated plans and individual task tracking

| Field | Value |
| --- | --- |
| Plan ID | `2026-10-17-plan-planning-workflow` |
| Status | completed |
| Created | 2026-10-17 |
| Updated | 2026-10-17 |
| Authorization | User requested this implementation and confirmed the authority split, activation policy, and initial state on 2026-10-17 |
| Decision | [Decision 107](../adr/decision-107.md) |

## Goal and acceptance

Establish an agent planning workflow with one active-plan selector, dated
plan records, and individual task files. Keep completed work-package evidence,
Decisions, and Operator handoff in the historical progress log. Preserve
progressive context loading and invariant/ADR upkeep.

Completion requires all of the following:

- `current.md`, dated plan records, and task files have defined authority,
  naming, lifecycle, and maintenance rules.
- The agent router loads current work progressively and the agent planning
  guide supplies copyable templates and activation/completion procedures.
- Living documentation and affected ADR status notes agree on the new
  authority split; historical plans, decisions, and backlog remain available.
- This setup plan and its task are retained as completed records. The current
  tracker finishes with no active plan and the existing backlog is not migrated.
- The repository gate and documentation link/consistency checks pass.

## Scope and constraints

Implement the documentation structure, agent guidance, authority amendments,
new planning invariant, and supporting decision record. Use `YYYY-MM-DD`
for plan dates and existing work-package IDs for task files. Authorization to
implement is sufficient for activation; drafting alone does not activate.

The existing `RET-011` backlog and operator handoff do not become active work.
The legacy `docs/agents/history/plan.md` remains a historical implementation contract, and
all new implementation still reviews applicable contracts, invariants, and
ADRs. Documentation changes do not imply authorization to operate the archive.

## Ordered tasks

1. [DOC-010 — Establish plan and task tracking](tasks/doc-010-planning-workflow.md).
   Dependencies: none. The task file owns execution status and evidence.

## Verification and completion

`scripts/check.sh` exited `0`: 1,750 Python tests, 45 Cockpit tests, lock,
format, lint, types, and package/plugin builds passed. Documentation links,
plan/task identity and state, and ADR coverage pass their checks. Invariant
and ADR review added `INV-011` and decision 107 and amended affected authority
notes. Full results are in the [completed task](tasks/doc-010-planning-workflow.md)
and [progress audit](../progress.md#dated-plans-and-individual-tasks-doc-2026-10-17).

## Amendments and outcome

2026-10-17: Activated from the user's implementation request and confirmed
preferences. No existing backlog was selected or migrated.

2026-10-17: Completed after the task acceptance, gate, invariant/ADR review,
and documentation checks passed. The task and this plan remain at their
original paths; `current.md` now selects no active plan. No follow-up scope
or operator handoff was introduced by this setup.
