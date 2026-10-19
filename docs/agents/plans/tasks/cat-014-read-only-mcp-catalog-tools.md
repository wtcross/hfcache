# CAT-014: Expose five explicit read-only MCP discovery tools

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 5 — MCP |
| Depends on | [CAT-013](cat-013-catalog-client-and-cli.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-014: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

mcp_tools.py; services/mcp_queries.py; api/mcp_reads.py and app-owned read adapter; MCP allowlist/server tests and docs/mcp.md.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Only after CAT-013 completion, add search_models, search_datasets, get_catalog_entry, list_model_variants and get_catalog_facets through the narrow async read capability. Share domain filtering, evidence, coverage and pagination with REST. Preserve all original nine tool semantics.

Update the exact allowlist and every enforcement/snapshot/capability/doc reference atomically. At the pinned baseline the supported set is fourteen. Reconcile any newer independently authorized tool additions without exposing arbitrary routes or deleting them to fit a numeric target. No automatic REST-to-MCP route generation.

Keep strict bounded schemas, canonical identity validation, safe descriptions, fixed masked errors, sanitization, shared work/wire limits, cursor identity and explicit partial-coverage qualifications. The dataset search signature omits model-only quantization knobs. Text and metadata remain untrusted data, not instructions.

Tools and adapters must not receive command services, an app/request object, credential resolver, Hub client, writable helper, arbitrary file/URL dispatcher or refresh capability. Read-only annotations are hints, not the security proof. No new prompt/resource/OAuth/background job interface is added.

Update human MCP connection/tool examples, security/consumer identity guidance and relevant ADR/invariant allowlist amendment in this package. REST/MCP credentials remain separate, and all readers still need authorization for the whole archive.

## Acceptance criteria

The exact reviewed tool set is enforced and read-only by construction. Equivalent REST/MCP queries match on domain identities/results/facets/coverage. No tool can install tags, refresh metadata, download or mutate the archive, even through malformed arguments or adapter leakage.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V44, V45, V46

MCP discovery/schema/allowlist and capability guard tests, equivalent REST/MCP fixture comparisons, hostile args/cursor/limit tests and import-boundary checks; full gate.

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
commit exists cite `CAT-014, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
