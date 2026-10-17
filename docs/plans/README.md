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

Follow [the planning guide](../agents/planning.md) for authorization,
activation, lifecycle, dependencies, templates, and completion rules. An
implementation instruction authorizes activation; drafting alone does not.
Small changes use proportionally brief plans and tasks. Preserve completed
and superseded records at their original paths.

The older [docs/plan.md](../plan.md) remains a historical implementation plan
and contract reference; it does not select current work.
