# CAT-004: Implement bounded versioned tag snapshots and publication observations

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 2 — Metadata foundation |
| Depends on | [CAT-002](cat-002-configuration-tags-and-identities.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-004: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

Proposed catalog_models.py/catalog_storage.py; src/hfcache/paths.py, storage.py, metadata.py and layout/preflight callers; docs/schemas.md, architecture and rollback docs.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Implement the two strict schema-1 artifact families, no-follow readers, safe record paths, deterministic serialization and typed completeness/provenance fields from design sections 4–5. Centralize new namespace builders under ArchiveLayout and validate type/ID/archive/SHA/publication/manifest agreement. Treat tag snapshots as historical observation authority and technical observations as derived interpretation, never one undifferentiated cache.

Implement independently atomic per-file replacement with existing safe write/fsync/rename primitives under caller-owned lock and preflight. The CAT-001 narrow exception must be in force before these writes are used. Test the absence of a multi-file transaction promise; do not change existing journals/checkpoints or acquire the common lock a second time.

Refuse unsupported, corrupt or unsafe existing records instead of overwriting. Establish canonical temporary-name handling and preservation on ambiguous failure. Support creation of only the approved supplemental namespace in a valid initialized archive; keep missing sentinel, local fallback and unrelated unknown-layout refusals.

Do not add SQLite, a persisted aggregate index, automatic garbage collection, mutable manifest fields or runtime filesystem code keyed by tags. Define inert orphan observations after prune/purge and exclude them by authoritative joins in later readers. Record growth/backup and old-layout compatibility limitations.

## Acceptance criteria

Both record families have round-trip goldens, strict field/identity bounds and injected crash tests. Invalid archive state cannot be initialized as a side effect. Historical tags cannot be reconstructed falsely from a cache, and unknown evidence survives. Existing manifest/reference/report goldens remain unchanged.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V08, V09, V10, V11

Focused model/path/metadata storage tests and fault injection around fsync/replace; existing preflight/layout/schema suites; scripts/check.sh.

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
commit exists cite `CAT-004, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
