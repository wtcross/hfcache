# Persist non-resuming admission without discarding uncertainty

- Decision identity: 114.

- Status: Accepted; current scope includes the amendments referenced below.
- Execution/reconciliation extension: [decision 115](decision-115.md), bounded runner and private verifier.
- Public CLI observation clarification: [decision 120](decision-120.md), CLI operation observation.
- Date: 2026-10-17.


## Context, decision and rationale

A receipt durably binds one authenticated credential class/key/route/body digest
to one operation and admitted policy before 202. Raw keys, tokens, credential
sources and replayable request bodies are not stored in API receipts. Exact-ID
history is whole-archive reader-visible; key lookup is class-scoped and survives
rotation without claiming individual attribution. Store/result files are protected
local no-follow single-link data with bounded bytes/count/events and fsync/rename.

Write the exact sanitized terminal Envelope before its digest/byte-bound result
reference. Validate identity, state, run ID and digest on fetch. Malformed, future,
unsafe, orphan, interrupted and nonterminal state remains preserved; only validated
succeeded/failed history expires. Capacity refusal cannot evict unexpired bindings.
One authoritative receipt binds key and operation together; separate key/receipt
files would require another transaction protocol and crash window. In-memory
indexes remain disposable. Store opening itself never replays or classifies jobs. The runner reconciles exact
surviving worker evidence first; unreachable status preserves active evidence and
closes execution admission. Missing history never proves nonexecution. A durable
resume graph or reconstruction from archive journals would introduce false replay
authority and is explicitly excluded.

## Relationships and technical evidence

- [decision 115](decision-115.md)
- [decision 120](decision-120.md)
- [decision 109](decision-109.md)
- [FW-01/FW-02 amendment](fw-01.md)
- [AD-12](ad-12.md)
- [Durable schemas](../schemas.md#13-service-private-operation-control-state)
- [API contract](../api.md#admission-idempotency-and-lifecycle)
- [server configuration](../server.md)
- [recovery runbook](../recovery.md#preserve-four-kinds-of-authority)
- [operation models/store](../../src/hfcache/api/operations.py)
- [shared atomic writer](../../src/hfcache/storage.py)
- [HTTP observation](../../src/hfcache/api/app.py)
- [public wire view](../../src/hfcache/api/models.py)
- [server limits](../../src/hfcache/server_config.py)
- [core lifecycle/idempotency tests](../../tests/unit/test_operations.py)
- [fault/concurrent/retention tests](../../tests/unit/test_operation_store_adversarial.py)
- [HTTP observation tests](../../tests/unit/test_api_operations.py)
- [durable golden model fixtures](../../tests/unit/test_models.py)
- [Decision 118](decision-118.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
