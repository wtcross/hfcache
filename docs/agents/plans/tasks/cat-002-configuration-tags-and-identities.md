# CAT-002: Add strict configuration tags and separate curation identity

| Field | Value |
| --- | --- |
| Status | completed |
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
Tasks own execution status; completion evidence below records actual validation.

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

Implemented shared strict tag normalization, optional frozen field and separate
schema-1 canonical curation fingerprint. Preserved the old fingerprint enumeration
and pinned its prior hash before changing code. Shared frontend/backend grammar
fixture is `tests/fixtures/tags.json`. No old strict wrapper/payload fields changed.

Fingerprint caller audit: run/journal/bootstrap/server policy, API runner and
private verifier comparisons correctly retain operational identity. Candidate
PlanSubmission/OperationStore digests already bind full candidate text; a new real
admission regression proves tag-only requests conflict under one key. Six fixed
authority fields remain unchanged. Candidate diagnostics retain field location
without rejected contents. Cockpit privileged guard already compares full bytes;
its final policy-only confirmation needs strengthening in CAT-003. No config
installation authority or secret-bearing full-config hash was added.

Reviewed INV-001/002/005/018 and AD-12/17, decisions 119/122/133. The implemented
normalizer/identity follows the accepted contract; no new architectural choice or
runtime dependency. The full gate and focused checks passed; evidence follows.
When work starts, record any relevant newer-source reconciliation, implementation
choices, blockers and scope amendments here. Preserve prior completed evidence.

## Completion evidence

Completed 2026-10-19 (CAT-002, this commit). V01–V04 covered by
`tests/unit/test_tags.py`: shared normalization goldens, generated idempotence,
raw/canonical limits and strict rejection, useful safe error locations, pinned
pre-feature policy/curation hashes, disabled/empty/reordered entries and authority
exclusions. Candidate tests prove same-policy/different-tag content conflicts
under one key. Old wrappers and fixed authority comparisons remain unchanged.

Focused config/tag/candidate/docs selection: 193 passed; final tag/candidate
selection: 43 passed. `rtk proxy scripts/check.sh` exited 0: 4351 passed,
40 opt-in deselected in 480.08s; lock/format/lint/types/docs/build/three locked
installation profiles and actual Cockpit lint/types/135 tests/build all passed.
Final format/lint/whitespace checks passed after added golden assertions.
Reviewed INV-001/002/005/018, AD-12/17 and decisions 119/122/133: implementation
follows existing accepted boundaries; no new ADR or runtime dependency needed.
Updated configuration/discovery guides and fictional authoring example.
No live/credential/production/push work. CAT-003 owns the remaining Cockpit
confirmation/tag-authoring changes; later tasks own discovery interfaces.
