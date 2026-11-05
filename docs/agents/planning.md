# Planning authorized work

For coding agents scoping and coordinating implementation. The user's request
defines authority. An instruction to implement authorizes work within that scope;
a request to draft or review does not authorize implementation or deployment.

Before editing, identify the outcome, boundaries, affected contracts and decisions,
dependencies, file ownership, acceptance criteria and validation. Keep the plan
proportional: a small correction needs only a brief execution-system note.
Do not activate unrelated historical backlog.

Keep short-lived coordination in the execution system. Preserve repository
implementation plans, task records, selectors, progress logs, reviews, inventories
and historical snapshots under `docs/agents/`. These records may retain their
execution status and evidence; they must not be deleted as part of human-document
cleanup. Removing them requires explicit user authorization.

When repository planning records are used, the selector points to the relevant
plan and task; task records own their recorded execution status. Historical
backlog and old authorizations do not activate new work. Durable product
requirements belong in human contracts, and design rationale belongs in ADRs;
human guides do not depend on agent execution records.

For parallel work, assign exact files and independent outcomes. Use isolated
worktrees for concurrent writers; in a shared checkout allow one writer at a
time. Review each batch before integration. Resume from Git and the actual
working tree, reconciling external notes rather than overwriting newer work.

Acceptance needs observed results. Distinguish source inspection, hermetic tests,
build checks and actual installed acceptance. Report failures and missing
environment-dependent checks truthfully. Follow [workflow](workflow.md) for
validation and commits, and [environment](environment.md) for host restrictions.
