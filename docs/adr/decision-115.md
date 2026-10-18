# Decision 115 — Execute one bounded lane and reconcile the exact verifier

- Status: Accepted; implemented by API-008.
- Command-route integration: [decision 116](decision-116.md), API-009.
- Activated-service/observer packaging: [decision 121](decision-121.md), API-014.
- Date: 2026-10-17.
- Work package: API-008, this commit.
- Source: [progress decision 115](../agents/progress.md#decisions),
  [active plan](../agents/plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../agents/plans/tasks/api-008-bounded-runner-and-offline-executor.md).

## Context and decision

Durable admission alone does not serialize expensive execution or prove what
happened after a daemon crash. Execute newly admitted work through one bounded
FIFO lane, separate from metadata workers and from the cross-process archive
lock. Admission captures one absolute waiting deadline; queue residence and
archive-lock acquisition consume that same budget. Expired work refuses before
domain invocation. Matching idempotent retries return the old receipt without
queuing it again.

Keep lock ownership in the command service. The runner passes deadline and
installed-policy validation hooks instead of taking a second flock. Immediately
after lock acquisition and before any mutation, reload installed policy and
compare the admitted fingerprint. A changed authority or policy fails closed;
never apply a preview against silently changed scope. The sync producer remains
inside that same lock until it is joined, including failures and drain.

Delegate every non-estimate verification to a narrow private Unix-socket
executor. Authenticate local peers, bound and strictly validate framed messages,
accept only verification scope plus server operation identity and expected policy
fingerprint, and retain exact operation-correlated durable outcomes. No arbitrary
command, client-selected config/path, credential forwarding or network-enabled
ASGI-process fallback exists. The executor calls the shared verification service,
owning the common flock through target resolution, hashing, report persistence
and catalog merge.

Startup never replays old queued/running work. First ask the configured executor
about the exact operation: reattach or await a verifiably still-running match,
or recover its exact durable terminal Envelope. Only then classify unresolved
work interrupted. A worker PID, released lock, elapsed timeout, disconnected
observer or retained `running` label cannot establish completion. If domain work
finished but the API terminal receipt was not written, executor evidence can
close that observation gap without running verification a second time.

Unavailable, unsafe or mismatched executor status preserves the active API
receipt and closes the execution lane across subsequent restarts; metadata and
healthy exact-ID history remain available. Only trusted missing/interrupted
worker evidence permits parent interruption. Marking an unreachable worker's
parent interrupted immediately would make a later restart skip that receipt and
silently reopen the lane while its worker might survive. Reject that shortcut;
restored exact status must resolve the barrier. Active delegation losing trusted
status likewise preserves its active receipt and halts the lane.
Private status must prove a live owned thread for its exact nonterminal operation;
the durable label by itself is insufficient. Trusted private running/domain-run
progress updates the parent API receipt without granting caller identity control.
Check the pinned archive UUID before progress, and verify the exact serialized
Envelope hash/bytes against its durable reference before importing a result.
Repeated lifespan task cancellation cannot release store/instance ownership
before runner and metadata drain join.
Validate activation, credential environment and inherited descriptors before
shared runtime imports can open their own files. This preserves the strict
descriptor boundary without rejecting library-owned descriptors as inherited
secrets; actual activated-process success/refusal tests cover that ordering.

Drain closes admission before joining accepted work and its producers. Losing
an HTTP/CLI observer does not cancel accepted execution. Forced termination
retains receipts and archive journals for diagnosis; it does not turn them into
instructions to resume. Never unlink a potentially held lock inode.

## Rationale and alternatives

One lane bounds contention while the existing flock excludes other local
processes. Resetting the lock timeout after queue residence doubles the intended
waiting budget; a runner-owned lock around a service-owned lock can deadlock.
Checking policy only at admission allows queued purge or retention work to act
on stale authority, so the decisive comparison belongs inside the actual lock.

Running verification in the HTTP process gives it network/credential authority
unrelated to its task. A separate peer-checked verification-only protocol has a
smaller authority surface than generic subprocess execution or broad systemctl
privileges. Replaying receipts or archive journals after restart risks duplicate
mutations; exact executor identity/outcomes support observation without replay.

## Consequences and relationships

Implements the lane/reconciliation portion of [109](decision-109.md) and
[114](decision-114.md), preserving their bounded non-resuming FW-01 exception
and FW-02's journal rule. Extends [110](decision-110.md)'s service-owned complete
lock and [111](decision-111.md)'s copied correlation/process boundaries.
[AD-17](ad-17.md), [AD-19](ad-19.md), [offline verification](offline-verification.md),
INV-014/015 and the supervised-cancellation runbooks identify the actual executor
rather than a client process. FS/TX, archive formats and systemd scheduling remain.

API-008 implements protocol/process primitives and hermetic tests. API-014 still
owns socket-activated units, credential-free environment provisioning,
`IPAddressDeny=any`, installed permissions/hardening and host acceptance. Calling
the startup-only offline initializer sets a library flag; it does not deny IP
sockets. Standalone development execution cannot claim that missing OS sandbox.
No new dependency, public command POST route, MCP work or production rollout is
introduced. Exact interfaces, bounds and runbooks are specified in
[server](../server.md), [API lifecycle](../api.md#admission-idempotency-and-lifecycle),
[operations](../operations.md) and [recovery](../recovery.md).

Implementation: [bounded runner](../../src/hfcache/api/runner.py),
[context-scoped service lock hooks](../../src/hfcache/locking.py),
[private protocol/client](../../src/hfcache/verification_protocol.py),
[executor runtime](../../src/hfcache/verification_executor.py),
[startup entry point](../../src/hfcache/verification_worker.py) and
[application lifespan](../../src/hfcache/api/app.py).
Evidence: [runner tests](../../tests/unit/test_runner.py),
[adversarial execution/restart tests](../../tests/unit/test_execution_adversarial.py),
[private executor/protocol tests](../../tests/unit/test_verification_executor.py),
[sync producer tests](../../tests/unit/test_synchronize.py) and
[shared command lock tests](../../tests/unit/test_command_locking.py).

## API-014 activation and executor policy (2026-10-18)

[Decision 121](decision-121.md) packages named Unix/optional TCP activation into
one API lifespan and a separate actual verification service with offline/no-IP/
credential-source masking. Account/euid peer checks replace manager-UID guesses;
the worker imports no Hub/API/MCP credential. Existing pending scheduled handles
permit observation only. Actual server/worker drain and retained locks, not stopped
client wrappers, govern upgrades/recovery. Repository inherited-FD/unit/protocol
rehearsals do not prove installed cgroup/SELinux/NFS enforcement; those remain
operator holds. Archive execution and exact surviving-worker reconciliation stand.

## Rootless listener ownership amendment (OPS-017, 2026-10-18)

[Decision 128](decision-128.md) adds explicit PID1 --container-listener startup
without weakening native named-FD3 activation. Owned mode audits inheritance
before resources/imports, pins a protected parent, refuses existing socket paths
and holds the worker instance through joined runtime/exact-inode cleanup. The
listener is created by the confined worker, not the host user manager. Private
frames, peers, durable reconciliation and no replay remain unchanged. Container
READY follows listener/store/worker initialization; actual API-container peer
access remains unaccepted until dependent rollout proof. No in-process fallback,
credential source, domain algorithm or durable format is added.
