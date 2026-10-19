# CAT-013: Add typed API client and CLI discovery and refresh commands

| Field | Value |
| --- | --- |
| Status | pending |
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

Not started. No source changes, tests, commits or operator actions are recorded.
When work starts, record any relevant newer-source reconciliation, implementation
choices, blockers and scope amendments here. Preserve prior completed evidence.

## Completion evidence

Not completed. Replace this paragraph at completion with the local date, concrete
acceptance results, exact test/gate commands and outcomes, invariant/ADR review,
changed human docs, progress-entry link and remaining operator handoff. Before the
commit exists cite `CAT-013, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
