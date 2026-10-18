# Plan tasks

Follow [the current tracker](../current.md) to the active plan and selected
task. This directory retains task records after their plans complete, are
cancelled, or are superseded. It is not a
backlog to execute in filename order.

Use an existing work-package ID and lowercase descriptive filename, for
example `doc-010-planning-workflow.md`. One task is one work package and one
implementation commit; split larger work into separately identified tasks.
Every task links its parent dated plan, and that plan links its ordered tasks
and their dependencies.

The task file owns its current status, scope, acceptance criteria, relevant
contracts/invariants/ADRs, validation, blockers, and completion evidence. Do
not duplicate mutable task statuses in the plan or progress audit. Preserve
IDs and files when work finishes or changes direction.

See [the planning guide](../../planning.md) for task states, dependency
and parallel-work rules, lifecycle, and copyable templates. The normal
[work-package workflow](../../workflow.md) supplies the implementation,
gate, audit, and commit requirements.
