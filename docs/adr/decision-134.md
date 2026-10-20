# Preserve Cockpit failure evidence and original operation identity

- Decision identity: 134.
- Status: Accepted; boundary, candidate reconciliation and scoped recovery implemented; full-service/report amendments and installed acceptance remain separate.
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
This implements the boundary/lifecycle portion of the contract and proves no
installed PAM or launcher cause. The scoped recovery implementation below extends
this boundary without a new runtime dependency or host restriction change.

## Implemented candidate reconciliation

The candidate pipeline preserves failed request Envelopes without forcing them
through assessment parsing. Bounded stage evidence publishes validation before
sizing, retaining original classified causes after interruption. Application
memory holds exact captured draft/base before transmission and survives tab
unmount. This memory is never serialized into browser storage.
Required successful sizing must cover the exact captured selector/revision set,
canonical resolved commits and publication sizing; missing or inconsistent success
fields refuse readiness. Repository defaults agree with backend policy, so omitting
`enabled` cannot skip sizing and valid defaulted documents remain editable.

Guarded read-only inspection uses the existing original lock without creating
files and reports exact candidate/base/installed/backup matches or absent/changed/
unknown evidence. A missing or unsafe lock is unknown, never recreated by
inspection. Different pre-existing candidate bytes cannot be overwritten; exact
matches can be reused without replacing their inode. Lost write acknowledgement
permits only explicit matching revalidation without another write. Lost install
acknowledgement requires installed/backup proof, explicit successful API
confirmation and acknowledgement. Neither read/remount nor missing files prove
nonexecution. No replay, cleanup, rollback or new installation endpoint results.

This preserves CP-11/INV-006 and decision133's tag-only exact-byte boundary;
operational fingerprints never replace byte comparisons. Real installed/session
acceptance remains distinct from pure, guarded-filesystem and mounted UI tests.

## Implemented scoped operation recovery

An application-owned registry records a validated original key synchronously in
tab-scoped session storage before starting a keyed submission. It covers candidate
sizing, installed sizing, diagnostics, selected jobs and maintenance/repair client
submissions. Installed full sync/verification service controls remain the existing
explicit exception. Tab unmount and display abort cannot cancel the existing
observer or stop internal identity collection. Reload restores safe handles;
prepared records become uncertain rather than being replayed.
Restored terminal summaries are also unverified until authenticated original
observation confirms them. Otherwise a forged but well-shaped summary could
silently resolve uncertainty and enable another submission. Missing history and
contradictory summaries retain the original record and block that transition.

Storage contains at most 32 records/64 KiB of allowlisted action/route, original
key/ID, host/profile/endpoint/credential-class/archive authority and terminal
summary. It contains no request/result bodies, raw TOML, credentials or logs.
Missing access, corrupt/changed storage, failed persistence and capacity exhaustion
block new submissions. Learned identities remain in application memory if later
persistence fails. Unresolved records are preserved; only conclusive terminal
summaries may be evicted when capacity requires room. Original result identities
remain evidence when a later ID or terminal result conflicts.

The fixed authenticated `client describe` command reads capabilities/version and
emits only the independently versioned metadata allowlist. It does not open an
archive or submit work. Unknown archive UUID is truthful null and grants no job
or saved-observation authority. Public strings, including derived hashes, must
not equal or contain registered credentials: a collision refuses with fixed
`HFAPI017`, without emitting a redacted pin. Failed server metadata requests retain
their exact original Envelopes, independently of the local presentation command.

The browser binds records to its trusted transport host and selected client
scope. Each deliberate submission/lookup/wait first refreshes authenticated
authority. The same CLI process compares `--expected-client-scope` using its
selected settings, actual endpoint, credential class and confirmed archive UUID
before the target request. Browser storage never selects routing or credentials.
This is a same-process comparison, not an atomic HTTP precondition across server
reconfiguration; existing protected deployment/quiescence and server archive
identity checks remain necessary. A post-transmission mismatch remains uncertain.
The server instance is recorded, while an instance restart alone does not replace
otherwise matching authority or the original operation. Unknown/changed scope
refuses observation; missing/expired history preserves handles and uncertainty.
Recovery invokes only authenticated lookup of the original key and observation
of its original ID, with no POST replay, cancellation or replacement key.

Maintenance Apply consumes the preview before asynchronous work and blocks a
second Apply on submit/observation failure, even with an earlier successful dry
run and no applied Envelope. Preview readiness also requires its original scope
and connection generation; the same-process pin closes a later target change.
Configuration preparation, preview, install, confirmation and acknowledgement
require fresh captured authority, preserving uncertainty and original evidence
when it becomes stale. Copied recovery commands use the fixed service-identity
launcher/settings/socket, expected scope and quoted positional handles after
`--`, including safe option-like keys.

Evidence: [registry](../../cockpit/src/lib/operation-registry.ts),
[authority parser](../../cockpit/src/lib/operation-authority.ts),
[application adapter](../../cockpit/src/api/operations.ts),
[metadata command](../../src/hfcache/client_metadata.py),
[registry tests](../../cockpit/test/operation-registry.test.ts),
[authority tests](../../cockpit/test/operation-authority.test.ts),
[CLI/socket tests](../../tests/unit/test_cli_client_describe.py),
[credential collision regressions](../../tests/unit/test_client_metadata_redaction.py)
and [mounted application tests](../../cockpit/test/browser.fixture.tsx).
These source tests are distinct from actual disposable Cockpit/PAM acceptance.
An isolated older-artifact launcher/candidate test does not validate this new
registry/metadata implementation or establish the original installed symptom.
The historical CP-04 full-service and CP-01/09 direct-report exceptions, production workload
holds, root locks/guards/masks and deployment restrictions remain unchanged.

The required repository gate also reproduced a real owned Unix transport defect:
an empty HTTP end-of-message write could close an already-responded socket before
the response read, replacing it with EBADF/ReadError. The adapter now matches the
locked backend's empty-write no-op. [Decision119's amendment](decision-119.md#empty-unix-writes-amendment-2026-10-20)
records deterministic actual-socket red/green and repeated original-case proof.
This changes neither dependency versions nor replay policy and establishes no
causal claim about the original installed Cockpit bridge interruption.

## Manual full-job amendment (2026-10-20)

[Decision 135](decision-135.md) now replaces the CP-04 manual service-start
exception with keyed REST full jobs. The report exception remains current. Fresh
protected host-profile inspection gates effects; all operation recovery,
uncertainty, credential separation and deployment restrictions above remain.
