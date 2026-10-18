# Implementation plans

Start at [current.md](current.md), which selects the sole active plan and
points to its next task and blockers. Read only that plan and the task needed
for the work at hand. An empty active selection is valid; historical backlog
does not activate itself.

Individual plans use `YYYY-MM-DD-plan-<slug>.md`; their creation dates and paths
remain stable throughout their lifecycle. Activated plans link ordered
work-package files under [tasks](tasks/README.md). Task files own current task
status and execution evidence. [Progress](../progress.md) retains completed
package audit entries, Decisions, and Operator handoff.

Follow [the planning guide](../planning.md) for authorization,
activation, lifecycle, dependencies, templates, and completion rules. An
implementation instruction authorizes activation; drafting alone does not.
Small changes use proportionally brief plans and tasks. Preserve completed
and superseded records at their original paths.

The older [docs/agents/history/plan.md](../history/plan.md) remains a historical implementation plan
record; living human contracts own technical authority. It selects no work.
The one-time path migration is recorded in decision 130 and the planning guide.
