# Decision 107 — Active plans and task records own execution

| Field | Value |
| --- | --- |
| Status | Amended |
| Date | 2026-10-17 |
| Work package | `DOC-010` |
| Provenance | User request and three confirmed planning choices; this commit; [progress decision 107](../progress.md#decisions) |
| Amends | Tracking/selection authority in [decision 82](decision-082.md) and [decision 106](decision-106.md) |

## Context

The legacy implementation plan and progress log combine architecture/history,
completed work, current backlog, and operator handoff. The user requested a
short active-plan tracker, dated individual plan files, and separate Markdown
tasks created when a plan is activated and decomposed. Progressive context
loading and the existing invariant/ADR upkeep requirements must carry forward.

Before implementation, the user confirmed that the new records own active
work, `progress.md` retains the audit history, implementation authorization
permits activation, and setup ends with no active plan or backlog migration.

## Decision

Use `docs/agents/plans/current.md` to select at most one active plan, its next task,
and blockers. Store each plan as `YYYY-MM-DD-plan-<slug>.md` with a stable
creation date/path, scope, authorization, lifecycle, ordered task links,
and plan acceptance criteria. Task files own dependency declarations; plan
tables may summarize prerequisite order. Create individual task files under
`docs/agents/plans/tasks/` before execution, using existing work-package IDs such as
`doc-010-planning-workflow.md`. A task is one work package and implementation
commit; it owns status, detailed acceptance, blockers, and evidence.

Maintain active records and completed progress evidence together in the
implementation commit. Preserve completed, cancelled, paused, and superseded
plans/tasks with explicit dispositions and replacement links. Do not duplicate
mutable task status in dated plan tables or the progress audit.

User authorization to implement is sufficient to activate; drafting alone
never authorizes execution. Small implementation packages use proportional
brief plans and one task. Read-only and draft-only work needs no activation.
The initial setup retains its completed plan/task and leaves current empty.
Existing backlog remains where recorded until explicitly selected within an
authorized implementation scope.

`docs/agents/progress.md` retains completed package evidence, Decisions, Operator
handoff, and unmigrated historical backlog. `docs/agents/history/plan.md` remains the original
contract/history reference. The [planning guide](../planning.md) defines
lifecycle and templates; the [router](../../../AGENTS.md) loads only current, the
selected plan/task, and relevant supporting context.

## Rationale and alternatives

Separate authority for selection, plan scope/order, task execution, and the
completed audit makes the next action discoverable without reading the entire
history. Existing work-package IDs avoid a second task numbering scheme.

Duplicating mutable task status across progress, plan tables, and task files
would permit conflicting completion claims. Drafts and old unchecked backlog
do not establish execution scope. Requiring a separate routine activation
approval would contradict the user's chosen authorization model. Deleting or
bulk-migrating history would discard provenance or activate work the user did
not select. These alternatives were rejected.

## Consequences

Every implementation, including documentation, creates or resumes a dated plan
and task before execution. One active selection remains explicit, no-active is
valid, and interruptions reconcile git evidence with task and plan state.
The current tracker remains short. Completing a task requires acceptance,
validation, invariant/ADR review, and audit evidence; completing a plan clears
its selection and preserves all records.

New task additions remain within the authorized outcome. Necessary
implementation steps do not require repeated activation approval; a material
scope expansion requires clarification before dependent work proceeds.

The former progress-only selection policy is superseded. Gate requirements,
work-package commit boundaries, host limits, and invariant/ADR upkeep continue.
`INV-011` documents the new repository workflow constraint. No application
format, runtime dependency, scheduler, or archive operation is introduced.

## Evidence and related records

- [Active selector](../plans/current.md),
  [retained setup plan](../plans/2026-10-17-plan-planning-workflow.md), and
  [DOC-010 task](../plans/tasks/doc-010-planning-workflow.md).
- [Planning lifecycle and templates](../planning.md),
  [implementation workflow](../workflow.md), and
  [conventions](../conventions.md#documentation).
- [INV-011 planning authority](../invariants.md).
- [Legacy plan amendment](../history/plan.md#7-project-layout) and
  [completed work-package audit](../progress.md#dated-plans-and-individual-tasks-doc-2026-10-17).
- The original decision is progress 107 in this work-package commit. Actual
  validation and completion evidence live in its task and completed progress
  entry rather than a pre-commit invented hash.

## Authority-path amendment (2026-10-18)

[Decision 130](decision-130.md) explicitly permits the one-time record
relocation and replaces historical paths with the agent namespace. Original
identity, rationale and completed evidence remain; no host authorization is
renewed. Current technical authority resides in human contracts.
