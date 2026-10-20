# Preserve Cockpit failure evidence and original operation identity

- Decision identity: 134.
- Status: Accepted contract; corresponding interfaces require implementation.
- Date: 2026-10-19.

## Context and decision

The existing fixed rootless REST client is the application transport. Its browser
adapter loses structured bridge/process fields, mistakes general failed candidate
requests for incompatible assessments and stores operation handles in tabs that
unmount. Preserve error category/stage and validated diagnostics independently of
terminal Envelopes. Recover bounded read connections without repeating mutations.
Keep original scoped recovery handles before transmission and outside tab state.
Uncertain Apply blocks repeat submission. Candidate writes/installations reconcile
exact expected bytes under the existing root guard without automatic cleanup.

## Rationale and alternatives

A generic reconnect toast discards evidence and cannot identify an installed
launcher/session defect. Replaying a pipeline risks another write or admission.
Browser credentials, arbitrary HTTP forwarding and local execution fallback would
weaken the fixed launcher boundary. Persistent raw configuration/logs are rejected;
only bounded validated nonsecret session metadata may support lookup/observation.

## Consequences

Source tests, actual disposable Cockpit/rootless tests and installed acceptance
remain distinct. Unknown authority or history fails closed. Manual full REST jobs
and retiring direct report reads require their own explicit contract amendments
and tested adapters; the current documented exceptions remain until then. No
endpoint for install, schedules or cancellation is added. Existing rootless holds,
credentials, exact candidate bytes, lock/backup authority and MCP reads remain.
No new runtime dependency, release, production inspection or deployment is approved.

## Evidence and relationships

- Amends [decision 122](decision-122.md); preserves [127](decision-127.md),
  [118](decision-118.md), [119](decision-119.md), [120](decision-120.md).
- [Cockpit contract](../cockpit.md#integration-repair-requirements),
  [invariants](../invariants.md#cockpit-boundary), [deployment status](../deployment-status.md).
- Current [runner](../../cockpit/src/lib/runner.ts),
  [candidate pipeline](../../cockpit/src/lib/config-pipeline.ts),
  [polling and handles](../../cockpit/src/hooks.ts) establish the source boundaries.
  Regression evidence must accompany the corresponding implementations.

## Implemented boundary and connection behavior

The [failure model](../../cockpit/src/lib/failure.ts) retains only known bounded
problem/process/stage fields, preserving original classifications through safe
rewrapping. Unknown values and raw diagnostic prose are withheld, including from
activity feeds. Exact terminal Envelopes remain independent and authoritative.
The [owned connection](../../cockpit/src/lib/connection.ts) and
[application session](../../cockpit/src/api/connection.ts) dispose close/privilege
listeners, bound read reconnection and reject stale results without mutation replay.
[Mounted component tests](../../cockpit/test/browser.fixture.tsx) fail against the
reviewed source and exercise actual hooks/adapters in an isolated Firefox profile.
This implements the boundary/lifecycle portion of the contract, not complete
candidate reconciliation or operation persistence, and proves no installed PAM
or launcher cause. No new runtime dependency or host restriction changes.
