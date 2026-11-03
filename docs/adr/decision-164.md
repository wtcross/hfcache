# Close original intent without inventing historical execution

- Decision identity: 164.
- Status: Server and browser source implementation; installed conformance pending.
- Date: 2026-11-03.
- Introducing change: accepted design at `60d086931dc03d8582751c6a3c9b17eeb6f93715`; server implementation amendment below.

## Context and decision

Missing receipts cannot prove nonexecution, but a rejected or historical key-only
browser record otherwise prevents distinct new work indefinitely. Preserve all
receipt schemas and introduce one bounded, separately versioned, permanent
disposition file under the same store flock. Fresh validated pre-admission
refusals close their keys durably. Generic registered Job adapters observe exact admitted receipts before a
later effect permission check. Fixed protected configuration/host-effect POSTs
retain independent fresh authorization; their original receipts and own-key
GET/outcome observations remain available. Every lane enforces permanent fences
and execution leases, and generic recovery cannot clear protected-effect
precautions. An explicit Basic-own-key retirement can close unknown
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

One preserving-entry file and the existing store flock avoid a second multi-file
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

## Historical refusal qualification (2026-11-03)

A later refused same-key transmission cannot prove that an earlier missing or
expired transmission never ran. Preserve the original refusal fields forever;
allow only its null review to gain one complete exclusive historical-retirement
proof. Project that reviewed key as retired unknown without deleting the refusal.
This narrowly amends the original blanket entry-immutability wording. A second
log, key revival or a special replay/dismiss command were rejected: the existing
single-file atomic transaction and full review already provide the needed
monotonic evidence. A saved browser disposition causally linked to its known new
submission can be freshly matched after reload; an older unknown without that
link must take the explicit review path even when a later refusal exists.

## Server implementation evidence

The [store](../../src/hfcache/api/operations.py),
[independent disposition/interlock models](../../src/hfcache/api/intents.py),
[authenticated routes](../../src/hfcache/api/intent_routes.py),
[offline activation](../../src/hfcache/api/intent_activation.py),
[runner](../../src/hfcache/api/runner.py) and private worker/helper implement
the server protocol. Focused source tests cover
[durability/previous reader](../../tests/unit/test_intent_dispositions.py),
[authenticated HTTP](../../tests/unit/test_api_intents.py) and
[exclusive review/handoff](../../tests/unit/test_intent_review.py).
The activation module uses the real selected-runtime validator; a weaker
handwritten predecessor reader is deliberately excluded. The protected runtime
renderer/installer must supply the fixed invocation/mounts/label after actual
previous-executor drain. Owned tests are neither installed helper confinement nor
browser/deployed retirement proof.

The server source gate25 passes9644 backend tests, three locked wheel profiles and
all required strict web/source-browser/real-API read checks with1276 source files
frozen unchanged. The executable exact0.3.1 c23abba reader drill refuses new-state
scans/admission while retaining compatible exact-ID reads. These source proofs
leave browser recovery, protected installer wiring/drain and installed workflow
conformance with their selected later packages.

## Browser implementation refinement (2026-11-03)

Closed export-only DTOs describe the existing raw readiness and intent wire
responses through the same audited generator. A single bounded readiness read
uses existing read coordination and response reservation. Its monotonic30-second
advisory lifetime does not turn unknown optional facts into denied permission.
Visible saved originals reconcile with authenticated GETs in the existing pools;
hide, authentication and cross-tab changes abort and fence their callbacks.
Late POST acknowledgement preserves handles without donating current proof.

Schema2 migration validates the complete preserving replacement before writing
once under the fixed storage key. Unverifiable post-commit readback retains the
exact validated original export and blocks submission; restoring it requires a
fresh equality read of this migration's own replacement, never a blind overwrite
of concurrent/unknown storage. Its original scope, handles, summaries and
32-record/64KiB/reserve limits remain. Causal refusal proof is created only for
a new current submission's typed closed response followed by its own-key GET;
a saved matching disposition ID requires fresh verification on restore. An older
unknown cannot borrow a later refusal. Explicit reviewed retirement remains a
separate confirmed action. Protected configuration/host-effect precautions remain
independent even after generic terminal or disposition evidence. These implement
the accepted protocol; no new architectural choice or dependency is introduced.

Reviewed retirement may preserve an original browser operation ID, receipt
identity and saved terminal summary when the current own-key intent is unknown.
These retained fields remain historical evidence; they are never overwritten by
closure or promoted to fresh outcome proof. A retained-ID Review action requires
fresh RAM-only own-key unknown evidence under the current authentication and
visibility context. Conflict remains blocked for operator review; a not-admitted
projection cannot contradict retained admission. Record-specific observation
authorizations bind the current disposition, and closure fences older callbacks
without clearing independent configuration or host-effect precautions.
