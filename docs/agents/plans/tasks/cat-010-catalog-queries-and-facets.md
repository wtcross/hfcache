# CAT-010: Build shared tag and variant search with truthful coverage and facets

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 4 — REST and CLI |
| Depends on | [CAT-002](cat-002-configuration-tags-and-identities.md), [CAT-004](cat-004-metadata-records-and-storage.md), [CAT-005](cat-005-bounded-static-metadata-extraction.md), [CAT-006](cat-006-gguf-variants-and-shards.md), [CAT-007](cat-007-quantized-weight-config-variants.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-010: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

Proposed services/catalog_queries.py and catalog DTOs; safe metadata readers; services/queries.py read-only patterns; new query tests.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Implement CatalogQuery, repository hit/detail/variant/facet payloads and deterministic bounded projection over fresh config plus authoritative retained refs/manifests and selected adjunct records. Search neither scans payloads nor writes/rebuilds state. No stored aggregate index or database is needed.

Implement normalized tags_all/tags_any, literal q, tag-source provenance, configured/archived/all scope and current/retained selection. Current means its explicit ref, never greatest generation. Configured empty tags override history; unrecorded history is unknown. Surviving metadata cannot resurrect a purged repository or a retired publication.

Apply format/scheme/method/bits/max_variant_bytes to a single eligible complete primary variant in a single exact publication. Keep dataset format/declaration behavior typed and reject explicit dataset model-only filters. Use accurate matching counts and a labeled deterministic representative; provide a paged variant collection for full enumeration.

Implement conjunctive filtered facets counting unique repositories, not files/shards/revisions, and derive technical facet values from matching variants only. Preserve global selected coverage counts and warnings, including missing/partial/unsupported extraction; zero known matches with missing coverage is not proof of absence. Corrupt selected durable evidence fails; scan exhaustion never returns a truncated success.

Construct sanitized visible catalog identity for cursor binding while keeping old policy/evidence fingerprints unchanged. Keep exact publication/manifest joins and no-follow/aggregate bounds aligned with existing read services. Do not add new fields to old inventory outputs.

## Acceptance criteria

All filtering scopes, variants, counts and coverage are deterministic and shared by future transports. Adversarial cross-variant/current-history counterexamples fail correctly. Read-only spies show no locks, metadata writes, Hub calls or model payload opens.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V29, V30, V31, V32, V33, V34, V35

Focused search/facet/detail fixtures including two types with same ID, empty/disabled/unmanaged states, unknown tags, missing records and cross-variant limits; full gate.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Implemented strict pure query/payload models and one bounded lock-free reader.
Predicates bind a single supported complete primary variant. Current follows its
explicit retained ref; selected corruption and exhaustion refuse. Whole coverage
precedes predicates/pages. Facets count distinct matching repositories, and detail
keeps variants separately paged. DTO construction was delegated before resuming
serial root implementation; no later work package has been implemented.

Visible projection identity suppresses sensitive labels, values and whole member
bundles before matching/counts/hash. Opaque historical curation fingerprints are
withheld as nullable read fields, preserving durable fingerprints and old policy
identities. INV-018 and decision 133 are amended with this implementation detail.
Focused query/model/storage/refresh selection: 270 passed in 13.41s. Format/lint
and focused Pyrefly passed. No live or host actions.

## Completion evidence

Completed 2026-10-19 (CAT-010, this commit). V29-V35 focused query/model/storage/
refresh selection: 270 passed in 13.41s. `scripts/check.sh` exited 0: 4,839 passed,
40 deselected in 507.37s; wheel/sdist built, all three locked installation profiles
passed, and actual Cockpit lint/types/169 tests/production build passed. Reviewed
INV-018, FS-08/09/11/12/15, AD-12/15/17/18 and decision 133; no transaction,
confidence, dependency or existing inventory/MCP capability changes. Updated
human discovery/schema contracts, invariant and ADR enforcement links. Explicit
privacy projection detail preserves existing operational/curation hash formats.
[Progress](../../progress.md) records completion. Next is CAT-011; no deployment,
live workload, credential access or push is authorized or performed.
