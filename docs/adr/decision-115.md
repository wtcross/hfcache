# Execute one bounded lane and reconcile the exact verifier

- Decision identity: 115.

- Status: Accepted; current scope includes the amendments referenced below.
- Command-route integration: [decision 116](decision-116.md), command routes.
- Activated-service/observer packaging: [decision 121](decision-121.md), scheduled observation.
- Date: 2026-10-17.


## Context, decision and rationale

Use one bounded in-process heavy lane and a separately confined verification
executor. Ordinary typed services still own their archive flock and fresh policy
comparison. Queue residence and remaining lock wait share one absolute deadline.
There is no in-process verification fallback, HTTP-triggered process spawn or
execution replay from receipts/journals. Verification in the HTTP process would
inherit unrelated network/credential authority. Fixed peer-checked verification
IPC has a smaller authority surface than generic subprocess/systemctl execution.

Private IPC is a strict bounded length-prefixed verification-only protocol over
protected Unix sockets with kernel peer identity. It preserves exact API operation,
archive/fingerprint, scope and durable result digest, without credentials,
arbitrary commands/candidates/paths or estimate authority. Check fresh availability
before new verification admission; matching retries observe existing work.

Restart reconciles exact live or terminal worker evidence before interruption;
unavailable/mismatched status preserves the active API barrier across restarts.
A restarted worker cannot be its previous live instance and marks unresolved private
receipts interrupted. Keep verifier handoff available during API drain, then join
worker work before releasing ownership. A queue or socket disconnect cannot replace
this proof. Native named FD3 activation and rootless worker-created notify listener
are separate bootstrap modes. Recorded 0.2.1 peer connectivity does not establish
outstanding NAS/domain/isolation acceptance; 0.2.0 rollback retains its limitation.

## Relationships and technical evidence

- [decision 116](decision-116.md)
- [decision 121](decision-121.md)
- [109](decision-109.md)
- [114](decision-114.md)
- [110](decision-110.md)
- [111](decision-111.md)
- [AD-17](ad-17.md)
- [AD-19](ad-19.md)
- [offline verification](offline-verification.md)
- [server](../server.md)
- [API lifecycle](../api.md#admission-idempotency-and-lifecycle)
- [operations](../operations.md)
- [recovery](../recovery.md)
- [bounded runner](../../src/hfcache/api/runner.py)
- [context-scoped service lock hooks](../../src/hfcache/locking.py)
- [private protocol/client](../../src/hfcache/verification_protocol.py)
- [executor runtime](../../src/hfcache/verification_executor.py)
- [startup entry point](../../src/hfcache/verification_worker.py)
- [application lifespan](../../src/hfcache/api/app.py)
- [runner tests](../../tests/unit/test_runner.py)
- [adversarial execution/restart tests](../../tests/unit/test_execution_adversarial.py)
- [private executor/protocol tests](../../tests/unit/test_verification_executor.py)
- [sync producer tests](../../tests/unit/test_synchronize.py)
- [shared command lock tests](../../tests/unit/test_command_locking.py)
- [Decision 128](decision-128.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).
