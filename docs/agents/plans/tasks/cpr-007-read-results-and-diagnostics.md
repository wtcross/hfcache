# CPR-007: Render every failed read and expose accurate readiness

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-006 — Move run-report browsing onto the existing REST routes](cpr-006-rest-run-reports.md) |
| Work package / commit | `CPR-007` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Audit and repair every read/result consumer without changing runHfcache's
successful-resolution contract for valid nonzero Envelopes. Add the missing
EnvelopeAlert/error state in verification EstimateCard and dashboard VersionCard.
Retain version --server, which is already correct, and fix its stale documentation
table. Preserve status/list domain errors and safe partial results.

Introduce shared result-state helpers where useful: loading, unavailable,
classified failure, valid empty, valid data and explicitly stale last-known data.
Validate success-only fields before dereferencing them. A failed refresh must not
leave healthy-looking data current or allow an action from stale evidence. Align
button readiness with CPR-002/005 connection/profile states, while keeping actual
CLI capability negotiation and server authorization authoritative.

Present safe deployment/connection diagnostics sufficient to identify source vs
installed bundle/launcher/profile/API skew. Do not infer backend version from a
local executable or package version alone, and do not infer writability from
health.ready. Use existing typed client metadata; any minimal additional read-only
presentation must have a documented strict schema and no arbitrary routing.
Do not add fields to the strict existing REST capabilities object casually.

Update remaining Cockpit help/error prose so code examples use the actual profile,
operation uncertainty is contextual, schedules are host-local, and estimates /
validation / metadata reads are not presented as workload acceptance.

## Acceptance criteria

F09 and remaining result-state inconsistencies are repaired across all reviewed
surfaces. API/terminal failures remain visible with stable codes and do not become
dashes, zero values or empty-success captions. Freshness and profile restrictions
are explicit. Already-correct server version, status/list paging, tag editing and
terminal Envelope behavior remain unchanged.

## Contracts, invariants and ADRs

Update Cockpit overview/verification/installation/troubleshooting, CLI client
guidance and source-to-deployment diagnostics. Review INV-006, CP-02/08/10/13 and
server health/capability semantics. No new dependency or metadata field is added
without the normal contract/ADR review.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

**Planned, not executed:** Cover V46–V51 and regression cases for every read surface. Feed exact successful,
failed, partial, malformed and unknown-schema fixtures through rendered components.
Test stale-generation refreshes and no-data vs unavailable labels. Run CLI output
parity and the complete repository/frontend gate.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

Not started. On activation/resumption, record source drift, exact implementation
scope, relevant runtime cause evidence, and any blocker with its unblock condition.
Do not rewrite this section as completed merely because the plan was extracted.

## Completion evidence

Pending. Replace with the completion date, accepted test/fixture results, executed
gate evidence, invariant/ADR review outcome, changed docs, remaining operator
handoff, and the corresponding completed `docs/agents/progress.md` entry. Before
commit use `CPR-007, this commit`; after commit, record only actual git evidence.
