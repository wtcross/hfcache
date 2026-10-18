# Agent workflow invariants

- **`INV-011` — Active work has one plan and explicit task authority.**
  `docs/agents/plans/current.md` selects at most one active dated plan. Each
  implementation work package has an individual task file before execution;
  the task owns status, dependencies, acceptance criteria, and evidence. The
  dated plan owns scope and task order; current is a short selector and next-
  task pointer. User authorization to implement permits activation, while a
  draft or an old backlog item alone does not. Preserve plan/task identities
  and completed or superseded records. Keep active records and completed
  progress evidence consistent in the implementation commit. The historical
  progress log retains completed work packages, Decisions, Operator handoff,
  and unmigrated backlog, without duplicating the active queue.


Planning evidence: [current selector](plans/current.md),
[retained setup plan](plans/2026-10-17-plan-planning-workflow.md), and
[DOC-010 task](plans/tasks/doc-010-planning-workflow.md).
`INV-011` is a repository workflow requirement reviewed through these records
and git; the application test suite does not enforce planning lifecycle.


INV-011 moved intact from the technical register on 2026-10-18 under
DOC-011 and decision 130. Its identity is reserved and never reused.
The planning guide defines the one-time path exception.
