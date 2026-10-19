# CAT-009: Add a typed writer-only offline catalog refresh service

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 3 — Writer lifecycle |
| Depends on | [CAT-004](cat-004-metadata-records-and-storage.md), [CAT-005](cat-005-bounded-static-metadata-extraction.md), [CAT-006](cat-006-gguf-variants-and-shards.md), [CAT-007](cat-007-quantized-weight-config-variants.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-009: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

services command/request layer; catalog refresh orchestrator; typed ServiceResult/Envelope/operation result compatibility; configuration snapshot providers.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Implement the explicit refresh domain service for canonical whole-repository selectors, current/retained revision scope, tags/technical flags and at least one enabled output. Scope is configured-plus-retained union; disabled and unarchived configured entries may have tags captured, while technical work without a publication is explicitly skipped.

Use fresh installed scope/authority after waiting, normal lock/preflight/recovery guards and safe record writes; do not double-acquire the lock. No Hub/network, model download, configuration write, integrity hashing, verification confidence change, repair or pruning. Do not silently fall back to a source path supplied by a caller.

Return exact typed per-repository progress/counts, warnings, failures, skipped states and recorded identity within bounded work/result budgets. Independent atomic records may partly succeed; overall classification must distinguish that from a complete refresh. An unsupported/corrupt existing record cannot be overwritten under the label refresh.

Capture last observed tags truthfully; never claim that a removed uncaptured edit was saved. Respect empty/re-added config precedence and keep unmanaged snapshots only as history. Prepare a new typed command kind for standard keyed admission without adding a new scheduler or changing existing verification worker authority.

## Acceptance criteria

Offline temporary fixtures can refresh current and retained observations and tag-only unarchived entries. All side effects stay in approved adjunct records and normal command evidence. Scoped failures are visible, no archive authority is broadened, and unsupported state is preserved.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V26, V27, V28

Service unit tests for scope/flags/lock/preflight, no-network/no-hash spies, capture/removal races, partial write results and version refusal; full gate.

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
commit exists cite `CAT-009, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
