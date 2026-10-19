# CAT-013: Add typed API client and CLI discovery and refresh commands

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 4 — REST and CLI |
| Depends on | [CAT-011](cat-011-rest-catalog-read-routes.md), [CAT-012](cat-012-rest-catalog-refresh-admission.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-013: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

client.py/client_models.py; cli.py/cli_client.py and command/request models; reader-only installation fixtures; CLI/API-client/quickstart docs.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Implement typed base-client methods for search, facets, entry, variants and refresh admission/observation. Add the proposed search/tags/catalog commands, aligned with current global JSON/quiet/color/credential/timeout/detach conventions. Search and list commands use only REST; no local archive fallback or optional server/MCP import.

Map --tag to all-tags and --any-tag to any-tags; default scopes match the server. Expose technical filters and tag-source provenance, with clear errors for dataset/model-only combinations. Human output distinguishes current versus historical tags, confirmed versus unknown coverage and representative versus full variant results.

Reuse complete paged collection with finite response/page/aggregate budgets and archive/policy/catalog identity checks. A stale cursor, inconsistent page, encoding budget or unfinished walk fails visibly, not a partial successful inventory. Preserve exact server Envelope/run identity in JSON and warnings/errors in quiet mode.

Refresh reuses existing idempotency and operation observation semantics, including handles under uncertainty and no automatic resubmission. Use protected selected REST credentials and verified transport; no bearer literals in example arguments. Coordinate capabilities and strict DTO compatibility without requiring extra runtime dependencies.

Update docs/discovery.md, CLI/client/quickstart examples and the safe script catalog only if a supported shipped script changes. Do not turn agent-only delivery files into public product tooling.

## Acceptance criteria

REST and the API-backed CLI support the full scoped discovery/refresh contract before MCP work starts. Base-reader install/import tests pass. Complete collection and human/JSON uncertainty behavior match existing safeguards. Tag-only configured discovery needs no archive mount or sync.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V41, V42, V43

Client transport fixtures, CLI invocation tests, page inconsistency/coverage rendering, operation uncertainty and base-profile import/install tests; scripts/check.sh.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Typed base-client search/facet/detail/variant methods retain exact responses with
validated pure payloads; explicit detail/publication identity cannot substitute.
Named complete iterators enforce stable archive/policy/catalog/coverage/totals,
strict order and uniqueness, page/aggregate bytes and unfinished-walk refusal.
Generic legacy page methods remain restricted to their old surfaces. Valid raw
Unicode query spelling survives casefold expansion on transport/continuation.

Refresh result DTOs moved into a pure module with unchanged fields, versions and
compatibility exports. Generic exact operation observation validates the new
payload, and catalog_refresh_result exposes typed evidence. No writer/framework
imports enter the client. CLI search/tags/show/variants/refresh use only REST;
complete assembly preserves first-server Envelope metadata and original evidence.
Human output qualifies provenance, coverage, representatives, diagnostics and
per-record refresh progress, escaping controls. Existing quiet/key/detach/timeout
and uncertainty handling remains shared. Independent REST parity now has 34 modes
with actual named CLI/HTTP evidence, preserving all 44 route/mode rows.

Broad client/CLI/query/refresh/REST regression selection: 583 passed in 43.74s.
After final typed-result additions, 340 focused tests passed in 23.45s; all-source
format/lint/types (zero errors) and documentation alignment pass. Cold subprocess
imports prove no writer/Hub/server/MCP/model runtime import. The final full gate includes actual isolated installation profiles and frontend execution.
Reviewed INV-006/012/014/015/018 and decisions 118-120/133; human CLI/client/API/
discovery/quickstart contracts and invariant/ADR links updated. No new runtime
dependency, script, durable format, production/live/credential/host/push action.

## Completion evidence

Completed 2026-10-19 (CAT-013, this commit). Full `scripts/check.sh` exited 0:
4956 passed/40 deselected in 552.27s; wheel/sdist, all three locked isolated
installation profiles, actual Cockpit lint/types/169 tests/build passed. Focused
post-fix selection: 326 passed in 17.94s; direct cold/client selection: 33 passed
in 5.31s. V41-V43 have actual client/CLI, complete collection, human/JSON, exact
refresh observation and uncertain-admission evidence. INV-006/012/014/015/018 and
decisions 118-120/133 reviewed; CLI/client/API/discovery/quickstart and enforcement
links updated. [Progress](../../progress.md#tags-and-discovery-2026-10-19) records
completion. No runtime dependency, production/live/credential/host/push action.
MCP remains the next serial task; no operator action is needed to continue.

The first full gate reported one existing client-only import-boundary failure:
4948 passed/40 deselected in 555.40s. Catalog UUID annotations still imported
application configuration despite the writer-free refactor. Added a canonical UUID
value type to the pure model layer and use it in both catalog record/result DTOs.
Existing client-only cold-import assertion remains unchanged; the new catalog
probe now checks this stronger boundary before importing the CLI's explicit local
bootstrap surface. No value constraints or serialized formats changed.

After the pure UUID fix, socket/client/record/storage/refresh/CLI/old-model selection
passed 326 tests in 17.94s, including unchanged client-only isolation. Canonical UUID
value tests preserve noncoercion and exact lowercase spelling. All-source lint/types
and document alignment pass; the updated full gate passed as recorded above.
