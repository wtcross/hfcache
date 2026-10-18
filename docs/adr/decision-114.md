# Decision 114 — Persist non-resuming admission without discarding uncertainty

- Status: Accepted; implemented by API-007.
- Date: 2026-10-17.
- Work package: API-007, this commit.
- Source: [progress decision 114](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-007-operation-receipts-and-idempotency.md).

## Context and decision

An operation may outlive its acknowledgement and every observer. A queued item
or a secondary key index cannot be the authority for admission: a crash between
those writes would permit a retry to duplicate accepted work. The service-private
receipt itself binds the operation ID, coarse authenticated credential-class
principal, hashed idempotency key and canonical route/request digest. Commit that
single record durably before making work runnable or acknowledging admission.
Only in-memory indexes are rebuilt from receipts; archive journals never supply
missing submissions or instructions to resume execution.

Use independently versioned deterministic JSON under the local control-state
directory, with protected descriptor-pinned filesystem access and atomic
replacement/fsync. Keep bounded sequenced sanitized events and exact terminal
schema-1 Envelopes separate from archive evidence. Persist no raw bearer,
credential digest/source, idempotency key or candidate request body. The request
digest is a comparison value, not a replayable command. No new runtime dependency
or archive schema is needed.

Matching principal/key/request retries return the original receipt before a
fresh policy lookup, even after policy changes. A changed route or canonical
request under the same key is a visible conflict. The principal is the fixed
credential class, so rotation does not lose its namespace; it makes no individual
user attribution claim. Authenticated key lookup is non-submitting and searches
only that caller's namespace. All REST principals with read capability may inspect
operation metadata, events and results under the same whole-archive boundary as
run reports (AD-21). Knowing an operation ID never bypasses authentication.

Provide an explicit primitive to classify old nonterminal receipts interrupted
without executing them. API-007 startup opens the store without classification
or replay; API-008 must reconcile exact surviving workers before using that
primitive. Never infer completion from a released lock, PID, elapsed time or client loss.
Retain interrupted, ambiguous, malformed, unknown-version and nonterminal state;
unsafe or unexplained state fails new admission closed. Terminal success/failure
results and key bindings have a configurable retention period, default 30 days.
Count/byte caps refuse admission instead of evicting an unexpired binding.
Expired validated terminal state may be removed deliberately; an absent/expired
lookup does not prove that work never executed and must not trigger automatic
replay of an uncertain mutation.

## Rationale and alternatives

Separate authoritative receipt/key files require a transaction protocol to close
their crash window. One receipt carrying the binding keeps the durable decision
inspectable and makes derived indexes disposable. A broker, SQLite, resumable
graph or journal-driven normal execution adds a competing execution authority
without improving this fixed, single-writer design. This bounded registry records
admission and observation; it does not choose a domain checkpoint or implement a
general workflow engine.

Evicting the oldest retained key to satisfy a count cap silently shortens the
promised retry window. Deleting interrupted records by age erases uncertainty
without resolving it. Both alternatives can convert a retry into a second
mutation, so capacity exhaustion remains a visible refusal.

## Consequences and relationships

Implements the registry/observation part of [decision 109](decision-109.md)'s
narrow [FW-01/FW-02 amendment](fw-01.md). [AD-12](ad-12.md), AD-14, AD-16 and
archive journals retain their authority. The actual heavy lane, lock/fingerprint
revalidation and isolated verifier remain API-008; command submission routes
remain API-009/010. No status read runs work, no existing operation is replayed,
and no MCP dependency or endpoint is introduced.

[Durable schemas](../schemas.md#13-service-private-operation-control-state-api-007)
define the independent version and compatibility boundary. The
[API contract](../api.md#admission-idempotency-and-lifecycle) defines observation,
failure and retention semantics; [server configuration](../server.md) defines
the bounded local state. The [recovery runbook](../recovery.md#10-operation-history-and-uncertain-submissions)
keeps control-plane history loss separate from archive transaction recovery.
The task records the throwaway previous-binary compatibility drill and final gate.

Implementation: [operation models/store](../../src/hfcache/api/operations.py),
[shared atomic writer](../../src/hfcache/storage.py),
[HTTP observation](../../src/hfcache/api/app.py),
[public wire view](../../src/hfcache/api/models.py) and
[server limits](../../src/hfcache/server_config.py).
Evidence: [core lifecycle/idempotency tests](../../tests/unit/test_operations.py),
[fault/concurrent/retention tests](../../tests/unit/test_operation_store_adversarial.py),
[HTTP observation tests](../../tests/unit/test_api_operations.py), and
[durable golden model fixtures](../../tests/unit/test_models.py).
