# Bounded non-resuming operation receipts

- Decision identity: 109.

- Status: Accepted; current scope includes the amendments referenced below.
- Date: 2026-10-17.

## Context, decision and rationale

Downloads and verification outlast an HTTP connection. Retain one bounded FIFO
heavy lane and service-private atomic JSON receipts independent of archive
journals. Bind authenticated credential class/key/route/canonical digest and
admitted archive policy, persist before acknowledgement/execution, and retain the
exact terminal Envelope plus bounded sanitized events. One absolute waiting
budget covers queue residence and archive-lock wait; services revalidate policy
inside their own flock.

Synchronous connections alone lose observation; detached tasks without admission
evidence lose authority. A broker/database/DAG would create a competing state
system. Receipts report submissions and never choose the domain's next checkpoint.
Restart never requeues existing work: reconcile exact surviving verifier state
before interruption. Unknown history, PID, free lock and client loss prove no
outcome. Preserve uncertainty; expire only validated terminal history within the
configured retention. There is no crash-proof exactly-once claim.

## Relationships and technical evidence

- [FW-01](fw-01.md)
- [AD-12](ad-12.md)
- [API contract](../api.md)
- [server](../server.md)
- [Decision 114](decision-114.md)
- [Decision 115](decision-115.md)

Deployment prerequisites are defined in the
[deployment guide](../deployment-centos-stream-10.md).

## Fixed host-effect amendment (2026-10-27)

[Decision156](decision-156.md) adds a bounded fixed-route host-action lane,
original-process observer stop, independent durable outcomes and finite diagnostic
reads. It preserves archive serialization, original operation identity and this
record's unrelated requirements. Implementation and actual installed conformance
are separately required.
