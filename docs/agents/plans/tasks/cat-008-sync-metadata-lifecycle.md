# CAT-008: Integrate supplemental metadata capture with existing sync and repair

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 3 — Writer lifecycle |
| Depends on | [CAT-004](cat-004-metadata-records-and-storage.md), [CAT-005](cat-005-bounded-static-metadata-extraction.md), [CAT-006](cat-006-gguf-variants-and-shards.md), [CAT-007](cat-007-quantized-weight-config-variants.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-008: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

src/hfcache/sync.py, publication.py, repair.py and shared command boundaries; observation writer; sync/repair offline fixtures.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Integrate metadata generation after an exact valid publication is durable, under the existing service-owned archive lock. Obtain safe current installed curation for tag snapshot capture without changing admitted operational policy/credentials. Record the actually observed curation identity/time.

Cover ordinary new publication, retained-SHA/no-new-publication paths, metadata-only config changes and repair with a new publication ID. A no-op archive sync may still refresh adjunct metadata without creating a new publication/generation or redownloading a retained model. Do not rewrite immutable trees/manifests or propagate old verification confidence.

Keep supplemental parser/storage errors safe and visible. An already valid publication must not be rolled back or called absent because enrichment failed; classify warnings and missing/failed coverage truthfully. Preserve existing domain failure/exit semantics and do not swallow unrelated archive failures. Reuse existing warnings/result extension points or explicitly version any necessary change.

Bound aggregate extraction work and preserve joined producer lifetime, common lock ownership, recovery/preflight, capacity and continue-on-repository-error behavior. Do not introduce callbacks that write metadata after lock release or daemon background threads without ownership. Metadata cannot trigger dependency downloads, partial sync or pruning.

## Acceptance criteria

Sync/repair tests show exact observation identity, original manifest bytes unchanged and no extra publication on tag edits. Failure injection preserves valid archive state and reports incomplete metadata. Producer/lock/capacity and retention regressions remain green.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V23, V24, V25

Focused synchronize/repair/retained-SHA and failure-injection tests; metadata write and Hub call counts; full gate. No live archive work.

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
commit exists cite `CAT-008, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
