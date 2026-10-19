# CAT-014: Expose five explicit read-only MCP discovery tools

| Field | Value |
| --- | --- |
| Status | complete |
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

CAT-013 is committed with a green full gate. Implementing exactly five explicit
additional tools over a separate narrow catalog read port, sharing CatalogQueries
and the existing pool/lease/wire/auth boundary. Original nine methods and semantics
remain unchanged. No newer independently authorized tools exist. Reviewed INV-016/018
and decisions 124/125/133; allowlist amendments and contracts precede implementation.

The optional registry now installs the five explicit catalog tools through
CatalogReadPort/CatalogReadAdapter. It receives only a trusted async executor;
no public generic dispatcher, app/request/command/Hub/credential/writable helper
is exposed. The original nine read methods and wrappers remain unchanged.
REST/MCP use one bounded CatalogQueries factory and the original shared worker
pool/leases; tool-specific cursors cannot cross tools/routes. Strict schemas omit
model-only dataset knobs; intent construction runs inside fixed classified error
masking. Independent mounted schemas/names, mutation-field sweeps and actual
success/failure filesystem/control snapshots now cover all fourteen tools.

Focused mounted catalog/registry/security/transport/REST acceptance selection:
165 passed in 63.33s. Direct REST/MCP comparisons cover normalized labels, same-
variant predicates/size, dataset formats, facets, exact entry/variants and coverage;
explicit complete variant pages and stale intent/tool/curation cursors are tested.
Early focused failures caught an incorrect identity constructor and an incorrect
UTF-8 byte-limit test assumption (the shared contract is 256 characters); both
were corrected before the passing selection. All-source lint/types (zero errors)
and documentation alignment pass. Full gate passed as recorded below; no runtime dependencies,
production/live/credential/host/push action.

## Completion evidence

Completed 2026-10-19 (CAT-014, this commit). `scripts/check.sh` exited 0:
4988 passed/40 deselected in 579.39s; wheel/sdist, all three locked isolated
profiles, actual Cockpit lint/types/169 tests/build passed. Focused mounted suite:
165 passed in 63.33s; corrected example suite: 6 passed in 11.61s. V44-V46 have
actual registry/schema, capability/side-effect and REST/MCP evidence. Reviewed
INV-016/018, AD-10/15/21, FW-01 and decisions 124/125/133; affected current
contracts, ADR amendments, router, documentation navigation and installation-
checker catalog are updated. [Progress](../../progress.md#tags-and-discovery-2026-10-19)
records completion. No runtime dependency, production/live/credential/host/push
operation. Prior failed gate remains documented below; no failure was waived.

First full gate failed one documentation-example assertion: 4987 passed/40
deselected in 582.80s. Its parser selected the guide's first JSON block, which is
now the new search input example. The check now anchors the original program
output section and still compares its complete subprocess JSON. All six actual
example tests (TLS and modern/legacy negotiation included) pass in 11.61s.
The failed log is retained locally; a corrected full gate is required.
