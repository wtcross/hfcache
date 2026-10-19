# CAT-003: Add tag authoring to the existing repository configuration workflow

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 1 — Foundation |
| Depends on | [CAT-002](cat-002-configuration-tags-and-identities.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-003: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

cockpit/src/lib/config.ts; configuration.tsx; config-pipeline.ts; candidate-guard.ts; UI/unit tests; docs/cockpit.md and cockpit-plugin guides.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Extend RepositoryEntry with tags and handle legacy entries with omitted tags without mutation surprises. Add one tag input control to repository creation/editing with existing configured-tag suggestions, not category/group controls or a mandatory registry. Follow current UI conventions and accessible labels.

Preserve canonical tags through form/text switching, serialization, toggling enabled, candidate validation, preview selection, backup/install and cancellation. Display normalization clearly and use backend validation as authority. Tags do not force sizing/download previews for an otherwise unchanged target.

Audit candidate/base equality and optimistic guards: a tag-only edit must not disappear because the backend policy fingerprint is unchanged. Preserve the existing full content/base guard; do not replace it with the curation fingerprint alone. Reject stale concurrent edits without overwriting operator changes.

Keep host installation privilege boundaries unchanged. Initial suggestions can use tags in the candidate/installed config; do not depend on unimplemented REST routes or make direct archive access a new UI requirement. Future discovery can use the API-backed CLI without changing installation authority.

## Acceptance criteria

Operators can add and edit tags at sync configuration time. Legacy rows render safely; values round-trip through all edit/install paths. Concurrent tag-only edits trigger the right conflict checks. UI help explains flat labels and normalizer behavior. Actual frontend tests/lint/build run and pass, not skip.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V05, V06, V07

Run the installed frontend gate (make -C cockpit check) and focused pipeline/guard tests, then scripts/check.sh with a genuinely executed Cockpit stage.

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
commit exists cite `CAT-003, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
