# Close original intent without inventing historical execution

- Decision identity: 164.
- Status: Accepted design; executable and installed conformance pending.
- Date: 2026-11-03.
- Introducing change: this commit.

## Context and decision

Missing receipts cannot prove nonexecution, but a rejected or historical key-only
browser record otherwise prevents distinct new work indefinitely. Preserve all
receipt schemas and introduce one bounded, separately versioned, permanent
disposition file under the same store flock. Fresh validated pre-admission
refusals close their keys durably. Exact admitted receipts always win over a
later permission denial. An explicit Basic-own-key retirement can close unknown
historical intent only after actual execution and protected-effect review.

[The executable protocol](../job-recovery.md) fixes a shared admission/executor
companion flock, independent open descriptions and overlapping queue/worker
leases. Exclusive review ownership spans fresh worker/helper proof, original
archive-lock acquisition and final store rescan/publication. Helper exchanges
occur outside store, runner, archive and configuration locks. A reviewed old key
is permanently fenced while its historical outcome remains unknown. Previous
uninterlocked executors require an independently proved deployment drain.

Visible authenticated browser recovery may automatically GET original evidence
within existing budgets. This narrowly supersedes deliberate-only observation
after restore/reconnect/visibility return. Hidden pages still abort reads and
fence late responses. No job POST, retirement, retry or protected-outcome
confirmation becomes automatic. Schema 2 preserves schema-1 handles atomically.

## Rationale and alternatives

One immutable-entry file and the existing store flock avoid a second multi-file
transaction. No compaction/expiry makes non-revival directly testable. A retained
fixed unknown filename deliberately makes the exact 0.3.1 predecessor refuse
admission while preserving compatible exact-ID reads. Deleting browser evidence,
inferring nonexecution from 403/404/free flock, using a process mutex alone,
reviving keys after retention or adding a resumable workflow engine were rejected.

## Consequences and relationships

Capacity refuses new work instead of deleting fences. Review requires fresh
whole-worker and protected-effect evidence, not only missing receipts. Existing
configuration/host outcome rules remain independent. No new runtime dependency
or public receipt state is added. A rollback retains compatible recovery/admission
authority; older backends cannot regain admission by removing new state.

Amends [114](decision-114.md), [115](decision-115.md), [118](decision-118.md),
[141](decision-141.md), [145](decision-145.md), [146](decision-146.md),
[150](decision-150.md) and [154](decision-154.md) only as identified above.
See [schemas](../schemas.md#133-original-intent-dispositions-schema-1),
[API](../api.md#original-intent-dispositions-and-readiness),
[invariants](../invariants.md#original-intent-closure).
Design and predecessor source inspection are evidence of the chosen protocol;
they are not executable race/crash or installed acceptance.
