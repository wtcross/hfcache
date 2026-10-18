# Plans and task records

This document defines planning for implementation. Read it when creating,
activating, changing, closing, or resuming a plan; ordinary sessions start at
[the current tracker](plans/current.md) and load only the selected plan and
task. The [work-package workflow](workflow.md) still governs implementation,
validation, commits, decisions, and handoff.

## Authority and scope

- `docs/agents/plans/current.md` selects the sole active plan and points to its next
  task and blockers. It is a short navigation surface, not another task log.
- Each dated plan owns its scope, lifecycle, ordered task links, and plan
  acceptance criteria. Each task file owns its dependency declarations,
  current status, detailed requirements, implementation notes, and validation
  evidence. Plan tables may summarize prerequisite order; task files remain
  the authority when a dependency changes.
- `docs/agents/progress.md` retains completed work-package evidence, the chronological
  Decisions log, and Operator handoff. It is not the scheduler for active work.
  A completed package's entry links its plan and task.
- Area contracts and `docs/invariants.md` define required behaviour; ADRs
  explain decisions. A plan cannot silently override them. Keep them current
  in the same work package when implementation changes their requirements.
- `docs/agents/history/plan.md` retains historical implementation evidence. Living human contracts own
  all current technical requirements. Its old package lists do not select today's work.

Every implementation work package has a dated plan and task file, including
documentation changes. Keep the detail proportional: a small, authorized
change can have a brief single-task plan. Read-only questions, investigations,
reviews, and drafting alone do not require activation or implementation tasks.
An unchecked historical item, including existing progress backlog or Operator
handoff, does not authorize or activate a new implementation plan.

## Files and identifiers

**One-time authority migration (2026-10-18, DOC-011, decision 130).** The
user authorized implementation of the REST/MCP documentation alignment plan.
Before relocating records, this amendment permits moving the original
`docs/plans/` records per file into `docs/agents/plans/`, the progress audit
into `docs/agents/progress.md`, and the historical plan into
`docs/agents/history/plan.md`. Destination collisions must refuse the move;
the supplied alignment plan and task records must remain intact. A migration
manifest records original paths and SHA-256 hashes. This is the sole exception
to stable paths below; identities, dates, completed evidence and restrictions
remain unchanged. After migration only `docs/agents/plans/current.md` selects
work. The historical plan becomes evidence; living human contracts own all
normative technical requirements. No historical host authorization is renewed.

Plans use `docs/agents/plans/YYYY-MM-DD-plan-<slug>.md`, with a lowercase descriptive
slug and the creation date. The date and path remain stable after activation,
rescheduling, or completion; record later events inside the file. Dates use
the session's stated local date. Do not rename an older plan to make it look
new or reuse its path for different work.

Activated plans link task files under `docs/agents/plans/tasks/`. Use the existing
work-package ID, lowercased, followed by a descriptive slug, for example
`doc-010-planning-workflow.md`. The task's heading and metadata retain the
canonical uppercase ID, such as `DOC-010`. Do not introduce a second task ID
sequence or reuse a completed work-package ID. One task is one work package
and one implementation commit. Split work that needs several packages into
several tasks with new IDs, preserving dependencies and acceptance criteria.

Every task links its parent plan; the plan links every task in execution
order. Declare dependencies by work-package ID and link their task records.
Do not copy mutable task
statuses into the plan or progress log. The current tracker may summarize the
next step and blockers, but the linked task remains the status authority.

## Activation and execution

1. Review git history and the working tree, the current tracker, and the
   relevant progress history and handoff, following [workflow](workflow.md).
   Read the active plan and selected task before choosing implementation work.
2. Establish scope from the user's instruction. An instruction to implement
   is sufficient authorization to activate its plan; do not add a separate
   activation permission step. A request to draft or review a plan authorizes
   that work alone. Resolve a material scope ambiguity before depending on it.
3. Write the dated plan with the intended outcome, scope, authorization,
   relevant contracts/invariants/ADRs, ordered tasks and dependencies,
   acceptance criteria, and validation. Review the affected invariant sections
   and relevant ADRs before implementation, preserving progressive loading.
4. Before implementing, activate the plan, create its task files, and update
   `current.md`. Only one plan may be active. If another plan is selected,
   reconcile that selection with the user's instruction and record the reason
   for any pause, cancellation, or supersession; do not silently abandon it.
5. Select a pending task whose dependencies are complete. Mark it
   `in_progress`, with any useful implementation notes. Normally only one task
   is in progress. Parallel independent tasks require authorization in the
   user's instruction or the active plan, with explicit scopes and ownership.
   Agents collaborating on one task share its work-package boundary.
6. Follow the contract-first implementation and gate loop in
   [workflow](workflow.md). Update the task as work progresses. If blocked,
   state the missing prerequisite and unblock condition; never work around a
   dependency by pretending it is complete. Another ready task may proceed
   within the authorized plan. If none is ready, keep the plan active and
   point `current.md` to the blocker.
7. Complete the task only after its acceptance criteria and required gate
   pass. Record validation results, invariant and ADR review, relevant changes
   or explicit lack of impact, and any operator handoff. Add the completed
   work-package audit entry and any new Decisions/ADRs in the same commit.
   Update the current tracker to the next ready task or plan completion.
8. Complete the plan after its acceptance criteria are met and every task is
   completed or explicitly cancelled with its scope disposition recorded.
   Clear the active selection in `current.md`; leave the completed plan and
   tasks at their original paths. Do not migrate unrelated backlog merely
   because the current selection is empty.

Before resuming after an interruption, reconcile git evidence, task status,
plan lifecycle, and `current.md`. Correct a stale summary before proceeding;
do not rerun completed work or infer completion from an unchecked summary.
Uncommitted implementation may exist after interruption, so inspect it before
changing a task's status or discarding work.

## Lifecycle and changes

| Plan status | Meaning |
| --- | --- |
| `draft` | Proposed scope; implementation has not been activated. |
| `active` | Authorized implementation selected by `current.md`. |
| `paused` | Work deliberately deferred, with reason and resumption condition. |
| `completed` | Plan acceptance met; task dispositions and evidence recorded. |
| `cancelled` | Work stopped, with reason and remaining scope recorded. |
| `superseded` | Replaced by a linked plan that records the remaining scope. |

The normal lifecycle is `draft` → `active` → `completed`. An active plan may
instead be paused, cancelled, or superseded. A paused plan returns to active
when its recorded resumption condition and authorization permit it. A draft
may be cancelled or superseded without activation. Record dated transitions
and their reasons; changing the active selection must leave plan metadata and
the current tracker consistent. No active plan is a valid state.

| Task status | Meaning |
| --- | --- |
| `pending` | Not started; dependencies may still be incomplete. |
| `in_progress` | The task is being implemented. |
| `blocked` | Cannot proceed until the documented condition changes. |
| `completed` | Acceptance and required validation passed; evidence recorded. |
| `cancelled` | Removed from scope with its disposition and reason recorded. |

Blocked tasks may return to pending or in progress after their unblock
condition is met. An interrupted task may remain in progress; inspect the
actual work before resuming it. Preserve completed acceptance and validation
evidence; follow-up work receives a new work-package ID. Cancelling a plan
does not erase its completed tasks or silently resolve its blocked tasks.

Record scope changes and task additions in the plan. Keep dependency links
and the next-task pointer consistent. Keep additions within the authorized
outcome: necessary implementation steps may proceed without another approval,
while a material expansion of scope needs clarification before dependent work.
New requirements must receive the same
contract, invariant, and ADR review as the original plan; plan acceptance does
not exempt implementation from that review. Preserve completed, cancelled,
paused, and superseded files, IDs, and meaningful history. Link replacements
in both directions rather than deleting or renumbering historical records.

## Templates

These templates show required information, not a minimum document length.
Replace path placeholders with real links when writing a record. A small
single-task plan can express the same information in a few short sections.

Plan:

```markdown
# <Outcome>

| Field | Value |
| --- | --- |
| Status | draft |
| Created | YYYY-MM-DD |
| Authorization | <instruction and its date, or draft-only> |
| Tracker | `docs/agents/plans/current.md` |

## Outcome and scope

<Required result, boundaries, and constraints.>

## Contracts and decisions

<Affected contract sections, invariant IDs, ADR links, and intended changes.>

## Tasks

| Order | Work package and task file | Depends on |
| --- | --- | --- |
| 1 | `<ID>` — `docs/agents/plans/tasks/<id>-<slug>.md` | None |

## Acceptance and validation

<Observable completion criteria and required checks, including the gate.>

## Lifecycle and amendments

- YYYY-MM-DD: Draft created; <authorization or remaining scope question>.
```

Task:

```markdown
# <ID>: <Outcome>

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | `docs/agents/plans/YYYY-MM-DD-plan-<slug>.md` |
| Depends on | None |

## Scope and acceptance

<Work to perform and observable acceptance criteria.>

## Contracts, invariants, and ADRs

<Relevant links and IDs; record the review and any required updates.>

## Validation

<Required checks. Replace planned checks with their results on completion.>

## Execution notes and handoff

<Material changes, blocker/unblock condition, scope disposition, or handoff.>

## Completion evidence

<Date, acceptance results, gate evidence, invariant/ADR review outcome, and
progress entry link. An uncommitted result cites this work package and
"this commit"; do not invent a commit hash.>
```

Current tracker:

```markdown
# Current plan

| Field | Value |
| --- | --- |
| Active plan | None, or `docs/agents/plans/YYYY-MM-DD-plan-<slug>.md` |
| Next task | None, or `docs/agents/plans/tasks/<id>-<slug>.md` |
| Blockers | None, or a brief description and task link |

<When no plan is active, say so explicitly. Keep completed implementation
evidence in the task and progress audit rather than growing this tracker.>
```
