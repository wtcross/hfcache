# CAT-004: Implement bounded versioned tag snapshots and publication observations

| Field | Value |
| --- | --- |
| Status | completed |
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
Tasks own execution status; completion evidence below records actual validation.

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

Implemented independent strict schema-1 tag snapshots/publication observations,
centralized optional layout builders and a named initialized-only inspection
extension. Record parsing rejects duplicates/nonfinite JSON, unsupported/missing
versions, noncanonical shapes and over-budget depth/tokens before allocation.
No-follow reads retain shared counters and enforce a hard per-record limit even
with an unbounded supplied reader. Exact reference/manifest identity, raw manifest
digest, source digests/member sizes and scoped variant IDs are checked.

CatalogWriter requires the original caller-held live lock lifetime, complete
passing storage preflight (only explicit copy-mode hardlink skip allowed), matching
sentinel and allowed namespace/published siblings. Directory creation is descriptor
anchored, same-device and fsynced; per-file replacement validates prior canonical
records before the shared atomic primitive. Unknown/future/corrupt/symlink evidence
and ambiguous temporary siblings are preserved. No second lock, journal, index,
automatic GC, sentinel rewrite or payload read. Historical snapshots remain
separate from derived observations. New goldens join existing format inventory;
old goldens are unchanged.

Independent review found and fixed lifetime, skipped-proof, unknown-sibling and
unbounded-reader gaps; final review found no further material issue. Focused
518 tests, lint/types/docs/whitespace pass. Full gate passed; evidence follows. Reviewed
INV-001/005/018, AD-01/06/07/12/13/14/15/17/18, FS-01/02/03/05–12/15–17/19/21–23
and TX-01/07 against decision 133; no broader exception or new dependency.
Updated schema/discovery, invariant enforcement, ADR133, error-code description
and backup/compatibility guidance. CLI/transport and extraction remain pending.
When work starts, record any relevant newer-source reconciliation, implementation
choices, blockers and scope amendments here. Preserve prior completed evidence.

## Completion evidence

Completed 2026-10-19 (CAT-004, this commit). V08–V11 are exercised by
`tests/unit/test_catalog_storage.py` and the two new golden fixtures: strict
independent versions/shape/order, exact authority/source/member binding, prior
future/corrupt/unsafe record preservation, before/after-fsync/rename failures,
independent record progress, active original lock lifetime, missing/wrong sentinel,
local fallback, unknown published/metadata names, recognized temporary preservation,
copy-mode proof exception and hard read/JSON allocation bounds. Old fixture bytes
remain unchanged. The optional namespace never becomes an initial requirement.

Focused expanded suites: 518 passed in 23.80s. Full `rtk proxy scripts/check.sh`
exited 0: 4415 passed, 40 opt-in deselected in 483.69s; format/lint/types/docs,
build, three locked installation profiles and actual Cockpit lint/types/169 tests/
build passed. Complete local output is `.git/cat-004-check.log` (ignored gate log).
Final docs and whitespace checks passed. Independent review findings are fixed and
reviewed again with no remaining material concern. Reviewed INV-001/005/018,
AD-01/06/07/12/13/14/15/17/18, affected FS/TX requirements and decision 133; no new
architectural decision/dependency or broader transaction exception. Updated human
schema/discovery/error/backup contracts and invariant/ADR enforcement links.
No production, credential, live Hub/NFS, archive CLI initialization, service or push
operation. Storage is supported; extraction/lifecycle/query/transport remain pending.
