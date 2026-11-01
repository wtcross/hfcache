# Preserve authority through the API client and guarded candidates

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 122.

- Status: Amended; see [decision 133](decision-133.md), [decision 135](decision-135.md), [decision 136](decision-136.md), [decision 137](decision-137.md), [decision 138](decision-138.md), [decision 139](decision-139.md) and the amendments below.
- Replacement design: see the 2026-10-20 amendment below; executable conformance remains pending.
- Date: 2026-10-18.
Native Unix/public-prefix routing is amended by [decision 123](decision-123.md).

## 2026-10-21 protected-reader amendment

## Context, decision and rationale

Require strict bounded schema-1 terminal Envelopes, separately bounded diagnostics/
progress and independently retained validated handles. Closure/timeout stops
observation without cancellation, automatic recovery or replay. Host-local report
browsing through privileged runuser/ls/cat and journal access remains an explicit
exception, not a remote REST client.

The persistent root configuration flock guards exact candidate and installed-base
bytes across syntax/compatibility/required preview, atomic backup/install and exact
installed fingerprint confirmation. Edits invalidate readiness; unknown/incompatible
authority blocks installation. Failed confirmation preserves uncertainty/backup,
clears readiness and requires reloading installed state. Giving the browser secrets,
trusting a posted preview or silently rolling back would discard these boundaries.

## Relationships and technical evidence

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).

## Supplemental discovery amendment (2026-10-19)

[Decision 133](decision-133.md) defines proposed tag/curation identities, the narrow
independent-atomic adjunct exception and protected read capabilities. Existing
archive, candidate-byte, whole-archive authorization and registered MCP boundaries
remain in force until corresponding additive implementation is accepted. Tags do
not change operational policy identity or grant installation/write authority.

### Exact installed-content confirmation

## Presentation and recovery amendment (2026-10-19)

[Decision 134](decision-134.md) requires preservation of classified errors,
finite read-connection recovery, stage-aware candidate reconciliation and scoped
operation handles outside tab lifetimes. Current implementation gaps are not
installed proof. The full-service and direct-report exceptions remain until
explicit amendments with tested replacements. Fixed rootless credentials, exact
config guards and all guarded workload/deployment restrictions remain unchanged.

The implemented [bounded presentation](decision-134.md#implemented-boundary-and-connection-behavior)
retains original safe stage/problem/process facts and exact failed terminal
Envelopes. Read reconnection is finite; session transitions invalidate stale
evidence without replaying host or API mutations. Raw rejection diagnostics are
withheld. The [candidate reconciliation amendment](decision-134.md#implemented-candidate-reconciliation)
retains original stage evidence, uses read-only exact inspection and requires
explicit confirmation/acknowledgement after uncertain installation. Persistent
operation recovery is now implemented by the
[scoped registry amendment](decision-134.md#implemented-scoped-operation-recovery):
persist the original key before transmission, scope saved handles to authenticated
client authority, and compare that authority in the same CLI process before
submission/lookup/wait. Unknown archive identity, stale preview/confirmation and
corrupt or unavailable recovery storage fail closed. Only bounded nonsecret
metadata survives tab/reload; no request/configuration bodies, tokens or logs are
stored. Lookup/wait follows the original identity without replay or cancellation.
No installed acceptance follows from these tests, and the full-service and
direct-report exceptions remain current.

### Negative confirmation evidence (2026-10-19)

The successful-completion requirement above governs accepting installation as
confirmed. A valid nonzero confirmation Envelope is retained as original failed
request/domain evidence even when the process exits nonzero. It grants no
installation success or readiness. Apparent success with failed process/postcheck
still refuses; missing/malformed output still preserves uncertainty. The guarded
helper emits results only after exact byte postchecks. This clarifies classification
without weakening exact-content or successful-confirmation requirements.

## Manual jobs and host permission amendment (2026-10-20)

[Decision 135](decision-135.md) replaces the full-service exception with manual
full jobs through the same fixed REST-backed client and scoped operation registry.
The direct-report exception remains pending its separate replacement. Host effects
require fresh root-only selected-release inspection and explicit protected policy;
missing, mixed, unsafe or drifted evidence fails closed. Scheduled observer state
and journal text cannot substitute for manual operation results. No user-manager,
mask, guard, original lock, API policy or credential boundary is weakened.

## REST report browsing amendment (2026-10-20)

## Read presentation and identity diagnostics amendment (2026-10-20)

[Decision 137](decision-137.md) validates all read-card payloads before display,
keeps failed Envelopes and informational partial results distinct from empty
success, and invalidates old host/session evidence. Advisory browser build-input,
selected physical release and authenticated API identities remain separate facts;
no package-version, health-readiness or selected-binding claim proves writability
or a running payload. No new transport, capability or credential authority follows.

## Replacement UI design amendment (2026-10-20)

## Guarded application amendment (2026-10-25)

[Decision154](decision-154.md) defines the narrow configuration writer, shared
legacy guard, durable private outcomes and original-handle read-only observation.
It supersedes earlier assumptions of a wholly read-only helper for this fixed
operation; all unrelated authority and original reasoning remain.

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
