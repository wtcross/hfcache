# Bind fixed host effects to original intent and independently observable outcomes

- Decision identity: 156.
- Status: Amended; the original implementation in `84221bf` has scoped installed
  native and guarded-rootless API-contract acceptance. The credential-mount
  teardown amendment dated 2026-10-30 is implemented with the scoped native
  observer qualification recorded below.
  Full platform and production acceptance remain separate.
- Date: 2026-10-27.

## Recorded implementation scope (2026-11-01)

[Human acceptance](../web-ui/test-release-acceptance.md) records one matching
native observer Stop and independently observed completion of its accepted
backend work. Guarded rootless controls retain their denials. The original
failed outer aggregates remain failed; qualification did not replay Stop or
clear unknown original handles. The
[migration guide](../web-ui/migration-from-cockpit.md#compatibility-and-backups)
retains the separate installed rollback and unresolved-outcome limits. Earlier
implementation-status text remains historical; other-platform and production
acceptance remain separate.

## Context and decision

Decisions141/150/154 separate the privileged helper from the online API and
preserve durable original outcomes. The remaining fixed schedule, observer and
journal functions need precise effects and recovery. The single domain runner
cannot stop an observer while its accepted backend work continues: nonlocking
work still waits in that same FIFO. Systemd StopUnit also accepts a unit name,
not an expected-invocation compare-and-swap. Neither mechanism supplies the
required observer-stop behavior.

Reuse the operation store and runner for one additional, fixed-route host lane,
with one executing and at most one queued admission. Only sync-schedule changes
and sync-observer stops belong to it. Domain and host runners have disjoint route
ownership during admission, startup reconciliation and shutdown. Interrupted
host receipts remain interrupted without replay. Stop both admissions before
draining, keep the helper available until both lanes finish, then close stores
and helper transport. The archive/verification lane and original exclusive
archive flock remain single; host effects never acquire that flock or execute
archive work. Journal reads use neither effect lane.

## Fixed authority and exact observer process

Keep HostStatus schema1 unchanged. A separate strict sync-observer status carries
its authenticated HostBinding, the two effective schedule/observer grants and
reasons, and nullable original boot/invocation/MainPID/start-ticks tuple. Internal
inspection may faithfully capture finite activating/deactivating service states
needed by the shipped oneshot observer. The old public status reports its existing
facts-unavailable projection when those states cannot be represented; it never
normalizes activating into active or emits a new value in the old schema. New
host-action authorization uses the dedicated projection and fresh protected
policy. Guarded rootless schedule/observer grants remain false, without manager
substitution.

Before stop, prove the selected native scheduled-client unit, immutable argv and
executable, account, system-manager invocation, boot and process start identity.
Retain its pidfd and rejoin those facts before signaling. A fixed protected
stdlib child inherits only the owned pidfd and bounded private input, drops to
the indexed service UID/GID, rechecks original process identity and sends one
SIGTERM to that pidfd. It never signals a numeric PID, replacement invocation,
process group, executor, API, worker or target. The parent observes that original
process exit within the existing exchange budget. Missing or ambiguous proof
refuses; an acknowledged signal without observed exit remains unconfirmed.
No CAP_KILL, initial-USER ptrace or generic process API is introduced. Accepted
backend work and its pending observation handle are independent and survive.

Owned native acceptance on2026-10-27 found that neither the native installer nor
its default unit explicitly provisions the assumed observer domain. Journal
stream metadata reported `init_t`, but it does not attest the live process SID;
the original SDK had exited before a direct sample. The earlier assumed
`unconfined_service_t` therefore remained unproved. A type-wide signal
grant to `init_t`, or moving the test into an unconfined domain, is rejected.
Observer control therefore requires an optional, explicitly provisioned confined
sync-observer domain and one exact protected/indexed system-unit context fragment.
Its fixed scheduled-state label and ordinary delivered credential/Unix API access
are separate from archive, Hub and helper-private state. The base native units
and version1 read/configuration profiles remain usable without this opt-in.

Missing, altered or unproved observer provisioning denies observer authority
before admission, independently of schedule authority. Prove the exact effective
manager context and fixed fragment, then join the original process's full SELinux
context in both retained-pidfd capture and the permanently dropped-UID child
before advertising or signaling. The helper's process-signal permission targets
only that confined observer domain. No permissive domain, generic context/path
selector, capability increase, automatic relabel or runtime provisioning follows.

## Timer and durable helper outcomes

Calendar/timespan validation invokes only fixed systemd-analyze argv after strict
printable-ASCII, length and control/backslash checks, with a closed environment,
finite output and child deadline. Return bounded actual normalized values and
next-elapse description; no shell or caller executable/unit/path is accepted.

The only managed file remains
`/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf`. Replacement clears
OnCalendar before setting it. Pause/resume stop/start only the sync timer and
never change enablement. Replace/reset reload the manager and restart only a
previously active sync timer; an inactive timer remains inactive. Resume or a
restart may trigger Persistent catch-up. Verification scheduling and target/API/
worker actions remain absent. Exact opaque full-byte schedule revision is checked
under a separately provisioned original host-action lock before effect.

Root0700 `/etc/hfcache/.host-actions` holds independently HMAC-authenticated,
versioned outcomes; `.host-actions.lock` and `.host-actions.pending` are separate
from configuration guards. An authenticated original-ID/digest pending marker is
durable before any host effect or per-operation workspace. A maximum128 records
and8MiB aggregate history bound new admissions; uncertain records are never
removed for space. Repeated original ID/digest observes existing state only.
Public original-subject/key outcome GETs never send effects, repair records,
remove markers or infer nonexecution from missing history. API receipt certainty
and private helper certainty remain distinct.

Preserve old managed schedule inodes inside root0700
`/etc/systemd/system/hfcache-sync.timer.d/.hfcache-actions/<operation-id>` before
replacement/removal. This is inside the same writable bind, avoiding cross-mount
rename assumptions. Only that explicitly validated private directory and the
fixed managed file are accepted; other drop-ins refuse. Record exact old/new
content and stored-file outcome separately from reload/timer acknowledgement.
Participating web publishers share the host-action guard. The supported legacy
Cockpit inspector already denies schedule/observer actions; its old shell and
D-Bus operations do not participate in that guard. Native host-effect activation
therefore requires safely absent legacy policy or strict protected
`/etc/hfcache/cockpit-policy.json` with both legacy schedule/observer bits false.
Capture and revalidate that absence/content before grants and effects; never
rewrite or migrate it. Older already-authorized privileged calls must drain
before provisioning; policy bytes alone cannot prove that drainage. Keep legacy
read/configuration profiles unchanged. Independent root
administrative edits remain trusted external changes; bracketed revision/inode
checks detect observed drift, without claiming a filesystem compare-and-swap
against an uncooperative root writer. No automatic rollback follows uncertainty.

Post-effect validation rebases only the exact independently verified managed
schedule leaf and fixed timer/observer observations changed by that original
operation. Policy, release, peer, unrelated unit and guard checks remain active;
there is no generic bypass or mutable-authority adoption.

## Original observer credential-mount teardown amendment (2026-10-30)

Installed native observation found an original SDK exit followed by rejection of
the final mount-table comparison. A separate controlled systemd probe, using
only a known public dummy credential, proved that normal original-process exit
removes exactly its systemd credential mount while restoring the prior ordered
mount observations. Requiring that expected mount to survive exit prevents a
correct original observer stop from confirming its effect.

Before signaling, capture the exact fixed native SDK credential mount at
`/run/credentials/hfcache-sync.service`, including its full raw mount identity,
alongside the existing ordered mount observations. It must be a single mount
rooted at `/`, with filesystem and source `tmpfs` and options
`ro,nosuid,nodev,noexec`. A malformed, duplicate, writable or non-tmpfs target
supplies no exception. Optional flags such as `noswap` and `nosymfollow` need not
be present; retain any captured flags in the exact identity.
Only the trusted original-stop
flow, after its retained original pidfd proves exit, may permit that one captured
mount's disappearance in its post-effect capture. An unchanged table still
requires identical raw credential-mount identity; matching projected path,
filesystem and flags cannot authenticate a replacement. Every other ordered
captured mount observation must remain identical. Missing or ambiguous original
mount proof grants no delta; added, changed, replaced, duplicate or unrelated
removed mounts refuse. The original capture remains strict.

This is a narrow extension of the original-effect observation rule above, not a
generic mount-baseline refresh or credential-path exclusion. All protected
policy, release, peer, namespace/mask, unrelated-unit and guard checks and existing
budgets remain active. The helper gains no credential payload read, mount/unmount,
cleanup, capability or policy right. Rootless observer control remains denied. Original
SDK exit, backend completion, API receipt certainty and private Stop certainty
stay distinct; no pending handle is cleared, replayed or retrospectively repaired.
The controlled probe proves this mount lifecycle only. Fresh source regressions
and actual installed observer-control acceptance remain required.

## Finite journal diagnostics and confinement

Only sync-observer and verify-observer sources are accepted; no unit, manager,
path, grep expression or run-result selector is accepted. Return at most80 lines,
8KiB per line and64KiB displayed text, from at most256KiB raw output and a bounded
child window within the existing exchange deadline. At most two journal exchanges
may consume the helper's existing eight slots. Use a source/boot/archive/deployment-
bound authenticated opaque cursor of at most2048 ASCII characters, explicit gaps
for lost history and truncation for omitted data. Closed event/level/run-ID
projection removes free MESSAGE prose and all credential/exception/argv text.
Journal evidence never creates an operation result or authorizes work.

Add only the fixed timer drop-in writable bind; keep API nonroot and every
archive/credential/network mask and capability ceiling unchanged. Separate fixed
schedule directory/file, private host-state and sync-timer-unit labels permit
narrow creation and timer control. Provisioning labels the selected immutable
sync timer specifically; do not grant start/stop over generic systemd unit types.
Private history retains the old managed inode's label. Reuse distinct guard
semantics for the named host lock/pending objects. Journal access is explicitly
read-only to actual journal file types, and SIGTERM permission targets only the
supported native observer domain. Type-level permissions are not filename/PID
restrictions; protected fixed code and live identity proofs remain required.
A fresh installation receipt/index and actual Enforcing proof precede use.
Old read/configuration-only profiles remain valid; optional native host-effect
label provisioning cannot silently grant schedule/observer rights.

## Rationale, consequences and evidence

A second archive executor, broad writable systemd tree, generic D-Bus/command
surface, name-only StopUnit, numeric-PID kill, enlarged capabilities and replayed
writes are rejected. A bounded existing-runner instance with route ownership
solves concurrency without changing archive serialization. Same-bind predecessor
retention avoids a false same-device rename guarantee. A dedicated observer
projection preserves old closed wire schemas while describing real oneshot state.

This record amends decisions109/115/121/135/136/141/145/150/154 only for these fixed
host functions. INV003/013/014/020/021 and new INV022 apply; AD17 archive authority
is unchanged. Exact public models and routes are in [schemas](../schemas.md) and
[API](../api.md); helper paths, budgets and lock rules are in
[host administration](../host-administration.md). Unit/component, real helper/
filesystem/process integration, actual native positive and guarded-rootless denied
acceptance are required. Source design is not installed conformance or production
rollout permission. Original handles, unknown records, NAS and live Cockpit remain
protected.

## Implementation and presentation status (2026-10-27)

The implementation in `84221bf` supplies these fixed routes, private outcomes and
optional native observer confinement. It passed the strict source gate and
33 native/15 guarded-rootless cases across three browser engines, through the
actual shared Caddy and installed API/helper.
The native cases prove permitted fixed effects and exact observer stop while
accepted backend work continues. The rootless cases prove protected denial with
no admitted effect or user-manager substitution. The canonical client/controller
probe ran inside the authenticated built application; it did not establish
rendered Administration-form acceptance. Original failed collectors and startup
records remain retained, with separate explicitly qualified read-only closure.

This is owned `LOCAL_STORAGE_SIMULATION` evidence, not NAS, production rollout,
Cockpit retirement or the later full platform matrix. It does not change the
installed production release. The subsequent Administration composition uses the
existing ports under the same authority, outcome and no-replay rules; rendered
controls require their own source and actual user-workflow acceptance.
