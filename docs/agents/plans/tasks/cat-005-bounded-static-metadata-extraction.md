# CAT-005: Extract bounded static model and dataset declarations

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 2 — Metadata foundation |
| Depends on | [CAT-004](cat-004-metadata-records-and-storage.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-005: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

Proposed catalog_extractors.py or a small catalog extraction package; dependencies.py patterns; metadata readers; synthetic card/JSON fixtures.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Build a transport-neutral extractor interface with explicit version, actual-read/work limits, manifest-contained source paths, supported/partial/unsupported/failed states and safe diagnostics. Never import repository code, runtime model libraries or dataset loaders; never contact the Hub or follow source URLs.

Read selected model/dataset card front matter and known JSON declarations as untrusted data, with byte/count/depth/alias/Unicode/duplicate-key checks. Safe YAML constructors alone are not a resource bound. Extract only allowlisted useful fields with provenance; do not save or return raw arbitrary cards/config JSON.

Preserve upstream tags as attributed observations separate from the sole curated tags field; they never satisfy operator-tag filters. For datasets, distinguish observed file-format candidates from declared configurations/splits/features and do not infer physical availability, row counts or external payload completeness from a card.

Provide reusable safe file access and budgeting for GGUF/weight configuration extraction. Define exact absent-versus-failed behavior and warning classification. Retain dependency detection semantics and avoid unrelated parser rewrites unless necessary for the safety boundary.

## Acceptance criteria

Small offline model/dataset fixtures produce deterministic bounded observations. Hostile inputs cannot execute or allocate unbounded structures. Parser errors yield truthful partial/failed state, not guessed values. No network, dataset execution or payload-wide scanning occurs.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V12, V13, V14

Focused parser fixtures, alias/depth/count bombs, no-follow tests and import/network spies; full gate. No live Hub fixtures.

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
commit exists cite `CAT-005, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
