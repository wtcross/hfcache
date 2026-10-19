# CAT-006: Detect GGUF formats, quantization schemes and complete variant sets

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 2 — Metadata foundation |
| Depends on | [CAT-005](cat-005-bounded-static-metadata-extraction.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-006: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

Proposed bounded GGUF extractor and variant grouping module; synthetic byte fixtures; discovery schema/evidence documentation.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Implement supported GGUF header versions with a pinned primary format mapping and explicit endian/type/count/length checks. Read header metadata only, never tensor bodies. Record GGUF as format and known GGML scheme as quantization; keep F16/F32 encoding and mixed/unknown nominal bit width honest.

Extract known general.file_type and shard identity/count/index fields. Unknown enums/versions or missing distinguishing metadata produce unsupported/candidate state; filenames cannot prove exact schemes or override a header. Do not infer Q4_K_M versus Q4_K_S from a single tensor type or a loose substring.

Group only exact, validated same-publication logical shard sets. Check missing/duplicate/count-conflicting shards, scope collisions, total member sizes and deterministic variant identity. Distinguish auxiliary projectors/adapters/unknown roles; do not advertise them as standalone primary models.

Validate offset/count arithmetic against file size and declared work bounds before reading or allocating; skipping unknown metadata must still respect bounds. Fail safely on hostile headers. Keep the module dependency-light and no execution/inference capability.

## Acceptance criteria

Known positive fixtures expose exact supported schemes and complete weight sets with source evidence. Float, ambiguous, auxiliary, unknown and incomplete cases are distinguished. Every grouping and byte total is publication-specific and deterministic. Hostile synthetic headers stay within configured bounds.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V15, V16, V17, V18, V19

Unit tests for all supported mappings, split sets and negative grouping; truncated/overflow/type/large-count fuzz-style fixtures; source-read spies prove no tensor body scans; full gate.

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
commit exists cite `CAT-006, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
