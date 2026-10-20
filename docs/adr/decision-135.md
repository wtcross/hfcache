# Separate manual REST jobs from guarded host observers

- Decision identity: 135.
- Status: Accepted; source and temporary fixture acceptance passed. Fixed-manager inspection is qualified below; disposable and installed acceptance remain separate.
- Date: 2026-10-20.

## Context and decision

Manual full sync and verification currently start legacy system services even
though the fixed authenticated client already admits their REST jobs. Use that
same client for manual `sync` and `verify --full`, with pre-send original keys,
server receipts, bounded observation and exact terminal Envelopes. Scheduled
observers remain distinct host objects. Their active state, exit status and
journals never establish the outcome of a manually submitted operation.

Amend CP-04 only: manual full jobs use the shared transient observer; scheduled
services retain their existing lifecycle and private handles. The plugin no
longer starts sync or verification services. Detaching a manual display never
closes its process, cancels work or stops API/worker. An optional stop of the
scheduled sync observer requires positive proof of its fixed observation-only
binding and explicit host permission. Never redirect to a user manager.

Add an exact root-only `inspect-cockpit` role to the existing fixed container
helper. It is read-only, accepts no paths/arguments, starts no container and reads
no archive contents or credential values. Validate the selected immutable
release/index, original helper/client bindings and guarded host facts. Read only
bounded host mount/lock accounting and fixed system-manager properties. Never
acquire, recreate, replace or remove the original domain lock to inspect it.

The administrator may provision a protected, bounded, strict
`/etc/hfcache/cockpit-policy.json` pinned to the selected release/index. Explicit
permissions distinguish archive jobs, Hub-capable jobs, other control jobs,
configuration changes, sync scheduling and stopping a proven scheduled observer.
The application never creates or edits that policy. Missing, unsafe, unknown,
mixed or drifted evidence denies effects. An absent guard or mask never grants
permission. A held or unconfirmed guard cannot permit archive jobs. Known masked
or unavailable units deny schedule/observer changes before any file or D-Bus
mutation. Fresh adapter checks enforce these boundaries; cached UI state is
explanatory and cannot authorize an effect.

## Rationale and alternatives

Continuing service starts conflates manual work with scheduled observation and
does not solve operation recovery. Bypassing masks via same-named user units or
assuming an absent guard means approval would weaken existing holds. Browser
permission toggles, arbitrary executables/paths, API bearer entry and HTTP
forwarding are rejected. Reusing a narrow existing host helper avoids another
listener, execution backend or binding. Explicit administrator policy makes
approval independent of incidental host state.

## Consequences and limits

The selected guarded installation stays restricted. Metadata and synchronous
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

Amends [decision122](decision-122.md), [decision89](decision-089.md) and CP-04 in
the [Cockpit contract](../cockpit.md). Preserves [decision127](decision-127.md)
and [decision134](decision-134.md), credential separation, all original guards,
the read-only report exception pending its own replacement, and fourteen MCP
read tools. [Invariant register](../invariants.md#cockpit-boundary),
[fixed helper](../../scripts/container-service.py),
[operation registry](../../cockpit/src/lib/operation-registry.ts),
[sync](../../cockpit/src/sync.tsx), [verification](../../cockpit/src/verify.tsx)
and [system interface](../../cockpit/src/api/systemd.ts) define the affected
boundaries. Regression and required gate evidence accompany the implementation;
current-source disposable Cockpit/PAM and installed acceptance remain separate.

## Unit-specific manager properties (2026-10-20)

Real systemd timer properties omit `MainPID`. Inspect only the five common fixed
timer properties (`Id`, `LoadState`, `ActiveState`, `SubState`, `UnitFileState`)
for the two exact allowed timers. Services and the guard additionally require
their real numeric `MainPID`; missing service PID facts remain unavailable.
Normalize a known timer's internal PID to zero only after that exact field set
is validated. This does not infer service permissions from a missing property,
relax guard identity or change the strict public inspection response schema.
