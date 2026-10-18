# Decision 109 — Bounded non-resuming operation receipts

- Status: Accepted target contract; enforcement lands incrementally.
- Date: 2026-10-17.
- Work package: API-001, this commit.
- Source: [progress decision 109](../progress.md),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-001-contract-and-activation.md).

## Context and decision

Downloads and verification outlast HTTP connections. Permit one heavyweight
execution lane with a bounded FIFO and service-private atomic JSON receipts,
independent of archive journals. Authenticate admission/observation; bind each
side-effecting request's principal/key to its canonical digest and admitted
config fingerprint. Persist before acknowledging or executing. Retain the exact
terminal schema-1 Envelope and bounded sanitized events.

On restart never automatically replay queued/running commands. Reattach an
exactly identified surviving verification executor or mark interrupted. Missing
history, PID, a released lock, or disconnected client do not prove execution
outcome. Retain ambiguous records; expire validated terminal records after the
configured retention. No exactly-once claim across crashes.

## Rationale and alternatives

Synchronous requests lose observation on timeout; unsupervised background tasks
lose admission evidence. A broker, database, DAG, durable resume graph, or
journal-driven normal execution would create an unnecessary competing authority.
This registry reports a submission and never chooses the domain's next checkpoint.
It does not satisfy the FW-01 trigger for a general workflow engine.

## Consequences and relationships

Narrowly amends [FW-01](fw-01.md)'s task-queue exclusion to permit this bounded,
non-resuming lane. [AD-12](ad-12.md), FW-02 and all archive journals remain
unchanged. The local archive flock still guards actual mutations and verification,
never the daemon lifetime. One waiting budget covers queue and lock residence;
revalidate installed policy under lock before mutation. API-007/008 own enforcement
and crash tests. [API contract](../api.md) specifies errors, retention, shutdown,
idempotency and uncertainty; [server](../server.md) owns worker isolation.
