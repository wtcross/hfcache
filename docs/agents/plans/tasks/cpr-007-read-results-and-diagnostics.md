# CPR-007: Render every failed read and expose accurate readiness

| Field | Value |
| --- | --- |
| Status | completed |
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

Final `rtk proxy scripts/check.sh` exit0:5276Python passed/42deselected in693.88s,
all three locked wheel profiles, actual Cockpit lint/style/types/561unit tests
(0failures/0skips),104mounted Firefox cases and production build.
[Exact command, artifact identities and earlier gate outcomes](../support/cockpit-rest-repair/gates/cpr-007.txt).
The exact reviewed component source fails26behavioral comparisons; current
components pass104. Actual CLI/read/write/manual/report/socket focus142passes;
shared read parsers24, strict estimate12, inventory9, owned connection9,
build-info14 and exact authority-effect4cases pass. These are source/temporary
fixture checks, separate from real Cockpit/PAM V54 and installed-symptom proof.

## Execution notes and handoff

Started2026-10-20 from clean CPR-006 `f0a35c2`. Actual payloads and health semantics
were revalidated; ADR137 was allocated after repository ADR136 before source work.
Repairs preserve original Envelopes and operation identities, strict bounds,
complete status/list paging, fixed version --server, credential separation,
guarded filesystem and no-replay behavior. Read/model/refresh/host readiness,
queued handlers, modal opening identity and current-store passive invalidation
have actual regressions. Private build-input FIFO/ancestor escapes are repaired
with descriptor-anchored nonblocking reads and independent review.

The first full gate passed Python but failed mounted ownership freshness. A later
full gate passed104components but a separate run exposed inspection invalidation;
that finding was made deterministic and fixed, together with its sibling authority
invalidator. The final complete gate passed after those repairs. Preserve all
intermediate RED captures and their attribution in the support evidence.
No production, guest or NAS action occurred. V54 remains unpassed, and the original
installed cause remains unproven. Next ready task: CPR-008, current immutable
artifact plus actual installed-wheel/private-UDS and real disposable Cockpit/PAM
acceptance, with frontend skip prevention. No routine approval is needed.

## Completion evidence

Completed2026-10-20, `CPR-007, this commit`; see the [accepted gate and hashes](../support/cockpit-rest-repair/gates/cpr-007.txt),
[components](../support/cockpit-rest-repair/gates/cpr-007-components.txt),
[CLI](../support/cockpit-rest-repair/gates/cpr-007-cli.txt),
[owner/estimate](../support/cockpit-rest-repair/gates/cpr-007-owner.txt),
[build privacy](../support/cockpit-rest-repair/gates/cpr-007-build-info.txt) and
[acceptance record](../support/cockpit-rest-repair/acceptance-record.md).
INV006/CP02/08/10/13, server readiness and affected decisions reviewed; actual
ADR137, ADR122/134 status/amendments/index, invariant register and human Cockpit/
client/schema/operator guides updated together. No runtime dependency, durable
format, API/capability/MCP authority or workload permission was added. Completed
progress entry and Operator handoff28 are in [progress](../../progress.md).
Selector advances to CPR-008; required real-runtime and original installed
acceptance are explicitly separate and unpassed.
