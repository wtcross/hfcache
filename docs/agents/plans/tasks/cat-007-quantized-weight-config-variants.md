# CAT-007: Detect scoped AWQ/GPTQ weight-bundle declarations

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 2 — Metadata foundation |
| Depends on | [CAT-005](cat-005-bounded-static-metadata-extraction.md), [CAT-006](cat-006-gguf-variants-and-shards.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-007: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

Static config/weight-index extractors; variant evidence types; known producer schemas and synthetic directory fixtures.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Verify supported AWQ/GPTQ static fields against current primary source/docs and record exact producer/schema assumptions. Implement quantization_config method/bits/group_size extraction without importing those runtimes. Separate format, quantization method and nominal bits; missing declaration is unknown, not unquantized.

Associate declarations with an unambiguous weight bundle in the same logical directory scope. Parse recognized weight-index maps with safe bounded JSON, require every referenced member in the manifest and keep unrelated quantized subdirectories separate. Do not apply a root configuration indiscriminately to all weights.

Identify configured-only and obvious pointer/incomplete cases as non-available or unknown. Do not unpickle .bin files or scan safetensors bodies; technical claims remain attributed static declarations plus known member sets, not runtime/tensor proof. Include exact member paths, role, known bytes and completeness in variant observations.

Resolve contradictions through explicit evidence state/diagnostics, never arbitrary merging. Preserve malformed input evidence within sanitized limits. Document which layouts are supported and where a future extractor is needed.

## Acceptance criteria

At least representative supported AWQ and GPTQ fixtures work without runtime imports. Conflicting/missing/escaping members and ambiguous scopes cannot produce false available variants. Size/method predicates are representable on a single variant. Technical metadata remains distinct from curated tags.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V20, V21, V22

Known config/index fixtures plus cross-directory, pointer, missing-member, duplicate, traversal and mixed-format counterexamples; full gate.

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
commit exists cite `CAT-007, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
