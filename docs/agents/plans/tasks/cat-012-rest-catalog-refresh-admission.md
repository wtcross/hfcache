# CAT-012: Expose writer-only keyed offline refresh operations

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 4 — REST and CLI |
| Depends on | [CAT-009](cat-009-offline-refresh-service.md), [CAT-011](cat-011-rest-catalog-read-routes.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-012: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

api command DTOs/route/runner; operation receipts/events/results and client command-kind schemas; server capability matrix and operation tests.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Add POST /api/v1/catalog/refreshes using the standard typed command admission lane, installed authority, Idempotency-Key and existing operation observation routes. Map only validated selectors/scope/flags to the CAT-009 domain service. No config installation, path/URL overrides, candidate credential resolution or implicit refresh on read/startup is allowed.

Enforce REST-writer authorization; reader/MCP/Hub credentials refuse. Revalidate execution scope and authority after queue waiting. Keep bounded admission, result persistence, exact operation/run identity, safe events and no-replay behavior.

Define new command/receipt/result discriminants and their compatibility within existing independently versioned local control records. An old operation result stays exact; unknown new records are preserved/refused by old binaries rather than coerced. Do not change the private verifier worker into a catalog executor.

Test duplicate keys, conflicting same-key bodies, new-key recapture after tag edits, uncertain POST observation, observer disconnect and restart reconciliation. Client departure cannot cancel or replay accepted metadata work. Update route/effects/auth docs: refresh writes adjunct metadata and control evidence but neither model bytes nor integrity evidence.

## Acceptance criteria

Authorized keyed refreshes execute once through normal writer ownership; all existing status/result observation guarantees hold. Denied callers cannot reach writes. Every new durable/control compatibility implication is documented and tested; no separate task engine is introduced.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V39, V40

HTTP and operation-store fixtures for admission/idempotency/restart/queue wait/permissions; no-network and no-verifier-dispatch spies; full gate.

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
commit exists cite `CAT-012, this commit`; do not invent a future hash. Update
this task, parent/current pointers and completed progress evidence in the same
implementation commit. Never mark completion while a required gate is skipped or red.
