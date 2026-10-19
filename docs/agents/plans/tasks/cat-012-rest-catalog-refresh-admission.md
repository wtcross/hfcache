# CAT-012: Expose writer-only keyed offline refresh operations

| Field | Value |
| --- | --- |
| Status | complete |
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
The status above and completion evidence below own execution truth.

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

Strict writer-only refresh admission now uses the existing typed receipt lane,
original guarded service and fresh installed curation callback. Canonical route
and Envelope command identify the new kind; receipt/result-reference/Envelope
fields and schema versions remain unchanged. The base operation allowlist accepts
its observation, with no new typed discovery/CLI methods yet. Independent REST
security/reference/schema inventories include the new writer method.

HTTP fixtures cover exact replay, canonical duplicate selectors, conflict, a new
key after tag-only edits, strict bodies/roles/keys, current policy revalidation and
fresh curation after lock wait, default/unpublished skips, real GGUF technical-only
capture, lost acknowledgement while an actual write is held open, and abandoned
restart interruption without replay. Credential/Hub/network/hash/verifier dispatch
spies deny those capabilities during refresh. The initial test helper named the
verifier method incorrectly; corrected to the actual execute/reconcile methods.
Expanded domain/HTTP/REST/model/client selection: 223 passed in 21.55s. Ruff and
Pyrefly pass (zero errors), documentation alignment passes; full gate passed as recorded below.
Reviewed INV-012/014/015/018, TX-07/AD-12/14/17 and decisions 114-117/133. No new
runtime dependency, private verifier kind or existing durable-format change. No
production/live/credential/host/push action performed.

## Completion evidence

Completed 2026-10-19 (CAT-012, this commit). V39-V40 expanded HTTP/domain/REST/
model/client selection: 223 passed in 21.55s; Ruff/Pyrefly/document alignment pass.
`scripts/check.sh` exited 0: 4899 passed, 40 deselected in 544.62s; wheel/sdist,
all three locked installation profiles and actual Cockpit lint/types/169 tests/
production build passed. Exact replay/conflict/new-key recapture, policy and
curation after waiting, held active writer after lost acknowledgement and preserved
interrupted restart are observed with real services and synthetic archives.
Reviewed INV-012/014/015/018, relevant TX/FS/AD and decisions 114-117/133; API,
server/discovery/schema contracts and invariant/ADR enforcement links are current.
No new receipt fields/version, private verifier kind, runtime dependency, host,
production/live workload, credential access or push. [Progress](../../progress.md)
records completion; CAT-013 is next.
