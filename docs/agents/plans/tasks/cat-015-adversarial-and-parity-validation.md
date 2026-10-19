# CAT-015: Prove read-only, bounded and cross-transport discovery behavior

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 6 — Acceptance |
| Depends on | [CAT-003](cat-003-cockpit-tag-authoring.md), [CAT-008](cat-008-sync-metadata-lifecycle.md), [CAT-014](cat-014-read-only-mcp-catalog-tools.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-015: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

Catalog integration/adversarial suites; shared metadata offload/security/cursor tests; Cockpit display tests; relevant contracts as fixes require.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Complete matrix adversarial coverage across shared services, REST, CLI and MCP rather than relying only on unit happy paths. Use generated offline fixtures for hostile card/JSON/GGUF inputs, huge counts, ambiguous bundles, duplicate/shard identities, wrong-archive records and exact publication races.

Prove queries cannot open payloads, hash model bytes, contact the Hub, acquire archive mutation locks, persist tags/observations or schedule refresh. Validate cancellation/worker lease and wire/scan/serialization budgets, including a tiny page on a large source and one oversized variant row. Budget exhaustion must fail explicitly.

Exercise prompt-injection-like card content, hostile filenames/tags and terminal/browser rendering. Metadata is data, not executable advice; no URLs are followed or shell strings evaluated. Check known-secret sanitization before matching/facets/cursor hashing so redacted substitutions cannot be probed through output/count changes.

Prove REST/MCP normalized filter and full pagination parity, same-variant conjunction, distinct repository facets, disabled/unmanaged/current-history states and explicit missing coverage. Add regression tests for every defect found and update its current contract if an ambiguity was resolved. Do not weaken an invariant solely to make a test pass.

## Acceptance criteria

Adversarial matrix cases and cross-layer negative assertions pass with real enforcement evidence. Read-only annotations are not the sole proof. All identified fixes are in scope, documented and tested; unresolved failures are recorded as blockers, not waived acceptance.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V47, V48, V49, V50

Focused adversarial/integration suites with spies/fault injection, frontend safety/round-trip tests where changed, then full gate with Cockpit stage actually run.

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
commit exists cite `CAT-015, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
