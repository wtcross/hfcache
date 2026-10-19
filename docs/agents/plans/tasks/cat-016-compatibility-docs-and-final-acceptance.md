# CAT-016: Complete lifecycle compatibility drills, documentation and plan handoff

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 6 — Acceptance |
| Depends on | [CAT-008](cat-008-sync-metadata-lifecycle.md), [CAT-009](cat-009-offline-refresh-service.md), [CAT-015](cat-015-adversarial-and-parity-validation.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-016: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

All affected product guides and ADRs; schema/install compatibility fixtures; release handoff docs; all task evidence/current selector.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Run synthetic lifecycle coverage for config edit/disable/removal/re-add, sync no-op, refresh, repair, prune and purge. Inert supplemental files cannot override reference/manifests or revive removed inventory; verification confidence remains keyed to exact publication. Document last-observed capture limits, missing observations and metadata growth without inventing automatic cleanup.

Test old config and durable artifact goldens plus actual supported old-binary refusals around tags, new directory layout and new operation kinds. Preserve unsupported state, and document a guarded non-destructive operator rollback and backup procedure. Do not run it on production or make a universal compatibility claim solely because schema_version stayed 1.

Finish the human documentation matrix in the parent plan, with executable fictional examples, exact route/tool/CLI names, normalization, provenance/coverage, variant evidence limits, dataset declarations, auth, budgets, offline refresh and compatibility. Ensure docs outside agents contain no CAT package links or execution narration. Run the existing documentation checker rather than replacing it with an allow-all rule.

Run full offline, frontend, build and supported installation-profile gates. Verify base reader excludes optional frameworks and extraction runtimes, REST-only remains usable, and MCP profile has only authorized tools. State precisely which live/NFS/deployment acceptances were not run. No push/merge/tag/deploy/credential action is authorized.

Audit every matrix scenario and task acceptance against actual evidence/commits. Close the plan only when all scoped packages pass (or an explicitly authorized scope amendment disposes of canceled work), clear the active selector, keep completed files at original paths, update progress/decisions/handoff and commit the final package. Report branch and incremental commit summary with remaining operator prerequisites.

## Acceptance criteria

All sixteen work packages and plan acceptance criteria have actual evidence. scripts/check.sh --with-build passes and the frontend gate ran. Documentation/current selector/progress agree, old evidence stays intact and rollback limits are accurate. No unperformed production acceptance or undeclared scope omission is presented as complete.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V51, V52, V53, V54, V55

Run scripts/check.sh --with-build, verify frontend execution and install-profile results, run compatibility/lifecycle fixtures and documentation audit, inspect complete git diff/log/status and task graph.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Not started. No source changes, tests, commits or operator actions are recorded.
When work starts, record any relevant newer-source reconciliation, implementation
choices, blockers and scope amendments here. Preserve prior completed evidence.

## Completion evidence

Not completed. Replace this paragraph at completion with the local date, concrete
acceptance results, exact test/gate commands and outcomes, invariant/ADR review,
changed human docs, progress-entry link and remaining operator handoff. Before the
commit exists cite `CAT-016, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
