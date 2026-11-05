# Separate manual REST jobs from guarded host observers

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 135.
- Status: Accepted; amended as described below.
- Date: 2026-10-20.

## 2026-10-21 protected-reader amendment

[Decision150](decision-150.md) adds independent protected helper/category proof
for replacement Basic admissions and dispatch, outside metadata/store/domain
locks. Original bearer jobs, operation observation and fixed system-manager
observer semantics stand. Rootless schedule/observer remain denied; no automatic
migration of legacy grants or change to historical acceptance follows.

## Context and decision

At adoption, manual full sync and verification started legacy system services even
though the fixed authenticated client already admitted their REST jobs. Use that
same client for manual `sync` and `verify --full`, with pre-send original keys,
server receipts, bounded observation and exact terminal Envelopes. Scheduled
observers remain distinct host objects. Their active state, exit status and
journals never establish the outcome of a manually submitted operation.

Amend CP-04 only: manual full jobs use the shared transient observer; scheduled
services retain their existing lifecycle and private handles. Manual interface
actions submit keyed REST jobs instead of starting those services. Detaching a manual display never
closes its process, cancels work or stops API/worker. An optional stop of the
scheduled sync observer requires positive proof of its fixed observation-only
binding and explicit host permission. Never redirect to a user manager.

## Rationale and alternatives

Continuing service starts conflates manual work with scheduled observation and
does not solve operation recovery. Bypassing masks via same-named user units or
assuming an absent guard means approval would weaken existing holds. Browser
permission toggles, arbitrary executables/paths, API bearer entry and HTTP
forwarding are rejected. Reusing a narrow existing host helper avoids another
listener, execution backend or binding. Explicit administrator policy makes
approval independent of incidental host state.

## Consequences and limits

The guarded profile stays restricted. Metadata and synchronous
validation remain distinct from keyed sizing/diagnostics and archive execution.
Candidate file writes/install/discard retain the root configuration lock and
exact-byte guards, with their own explicit host permission. Sync schedule changes
remain fixed-system drop-ins; target actions and verification-timer mutation stay
forbidden. No automatic replay, cancellation, cleanup or guard transition results.
Submission permission is not proof of writable storage or workload readiness:
API authentication, policy, immutable identity, capacity, executor and archive
locks remain final. Existing read-only runtime mounts and hardening are unchanged.
Permitted component/CLI fixtures never establish production or NAS acceptance.

Capture command/candidate/authority options before asynchronous checks or display
callbacks; derive the action from that immutable intent. A closed plugin command
grammar refuses global-option prefixes, local/bootstrap modes and unsupported
commands instead of treating an unknown dispatch as a read. Host changes that
were acknowledged before a later failure preserve their original classified cause
and retain uncertainty across tab lifetimes. Explicit exact stored-file/unit
inspection and acknowledgement never replay reload/restart and do not establish
the loaded calendar or success of the interrupted manager operation.

## Relationships and evidence

The [server execution and drain contract](../server.md),
[protected host controls](../host-administration.md) and
[browser operation guide](../web-ui/operations.md) describe current jobs and
observer boundaries. The amendments below specialize their protected authority.

## Unit-specific manager properties (2026-10-20)

Real systemd timer properties omit `MainPID`. Inspect only the five common fixed
timer properties (`Id`, `LoadState`, `ActiveState`, `SubState`, `UnitFileState`)
for the two exact allowed timers. Services and the guard additionally require
their real numeric `MainPID`; missing service PID facts remain unavailable.
Normalize a known timer's internal PID to zero only after that exact field set
is validated. This does not infer service permissions from a missing property,
relax guard identity or change the strict public inspection response schema.

## Replacement UI design amendment (2026-10-20)

[Decision 141](decision-141.md) amends this record for the accepted
replacement design. The helper transport retains separate manual REST jobs, scheduled observation and protected host permission proof; supported native positive paths and rootless denials require distinct tests.

## Fixed host-effect amendment (2026-10-27)

[Decision156](decision-156.md) adds a bounded fixed-route host-action lane,
original-process observer stop, independent durable outcomes and finite diagnostic
reads. It preserves archive serialization, original operation identity and this
record's unrelated requirements. Implementation and actual installed conformance
are separately required.

The pre-removal record remains in Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4`; removed interface-only
instructions and source evidence are historical, not current operating steps.
