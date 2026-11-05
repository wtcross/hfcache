# Contribution workflow

For coding agents making an authorized repository change. Human contributor
setup and checks are in [development](../development.md).

## Start from the repository

Read `git log --oneline -20` and `git status`. Preserve unrelated uncommitted
changes. Establish scope from the user's request, then load the relevant
contracts through `AGENTS.md`. Read [environment](environment.md) before any
operation outside the repository; a checkout may be on the production writer.

Plan work before implementing, with detail proportional to the change. Keep
mutable plans, assignments, inventories, check results and handoffs in the
execution system outside versioned documentation. Resume against Git and the
actual working tree. Historical instructions do not authorize new operations.
Preserve existing repository plans, task records, selectors, progress logs and
snapshots under `docs/agents/`; documentation cleanup does not authorize their
removal. Agent records remain separate from maintained human guides.
See [planning](planning.md).

## Implement and validate

1. Review affected invariants and relevant ADRs. Change contracts with the
   implementation when behavior changes. For documentation drift, establish
   which behavior is authoritative and explain the correction in the change
   description. Follow [technical-record policy](technical-record-policy.md).
2. Implement a bounded, reviewable change following [conventions](conventions.md).
   Keep application behavior outside a documentation-only change.
3. Run affected checks and `scripts/check.sh` before committing. Use live,
   NFS, installed-host or build checks only when relevant and authorized.
   A stopped check or a source fixture is not installed acceptance.
4. Review the diff and local links. Record changes, reasons, checks actually
   run and limitations in the commit/change description and external execution
   record or the appropriate agent record. Preserve existing checked-in
   selectors, task records and progress logs.
5. Commit one coherent change with a concise descriptive subject. Existing
   technical identifiers remain stable; no task identifier is required.

## Publication

Contributors stop at a proposed change. Maintainers with publication authority
push reviewed, green commits to both `github` (public repository) and `forgejo`
(lab mirror). Never force-push. Deployments, image publication and release tags
require their own scope; implementation alone does not authorize them.
Follow [release instructions](release.md) for a release.

Git history supplements the retained agent records; it does not replace them.
Keep technical rationale in ADRs and current requirements in human contracts.
Removing agent plans or execution history requires explicit user authorization.
