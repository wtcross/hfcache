# CAT-002: Add strict configuration tags and separate curation identity

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 1 — Foundation |
| Depends on | [CAT-001](cat-001-contracts-and-activation.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-002: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

src/hfcache/config.py; services/candidates.py and bootstrap/client config-validation callers; relevant tests and configuration examples.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Implement optional direct repository tags using one pure normalizer and the exact input/canonical limits in design section 2. Preserve strict frozen models, unknown-key rejection and existing dependency rules. Omitted and empty tags mean no curated labels; do not add metadata/categories/groups/use_cases/expected_variants.

Keep the operational config fingerprint byte-for-byte compatible for pre-existing inputs and exclude tags. Add a separate canonical curation fingerprint. Review every config fingerprint caller, candidate normalization, validation payload and request digest to identify places that need full-document equality versus policy equality. Do not accidentally expose secret-bearing full config hashes or repurpose evidence identity.

Retain the fixed six-field authority comparison and no-network candidate validation. Ensure tags error locations are useful but no rejected value or secret escapes through candidate diagnostics. Assess strict old client DTOs before any validation payload additions; use versioned/new shapes where necessary rather than breaking old routes gratuitously.

Add safe fictional repository examples and explain normalization, limits, rollback to binaries that reject tags, and label-only behavior in configuration/discovery docs. Test identities and tag ordering with golden cases shared with the frontend.

## Acceptance criteria

Existing configs and fingerprint goldens pass. Canonical tags have deterministic values and errors. A tag edit changes only the new curation identity and relevant catalog state, not archive policy or verification identity. Candidate validation cannot acquire new authority. No forbidden organizational fields are introduced.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V01, V02, V03, V04

Focused config/fingerprint/candidate tests with secret-redaction cases, then full gate. Inspect all fingerprint references rather than testing only RepositoryConfig.

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
commit exists cite `CAT-002, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
