# Close original intent without inventing historical execution

- Decision identity: 164.
- Status: Server and browser source implementation; installed conformance pending.
- Date: 2026-11-03.
- Introducing change: accepted design at `60d086931dc03d8582751c6a3c9b17eeb6f93715`; server implementation amendment below.

## Context and decision

Missing receipts cannot prove nonexecution, but a rejected or historical key-only
browser record otherwise prevents distinct new work indefinitely. Preserve all
receipt schemas and introduce one bounded, separately versioned, permanent
disposition file under the same store flock. Fresh validated pre-admission
refusals close their keys durably. Generic registered Job adapters observe exact admitted receipts before a
later effect permission check. Fixed protected configuration/host-effect POSTs
retain independent fresh authorization; their original receipts and own-key
GET/outcome observations remain available. Every lane enforces permanent fences
and execution leases, and generic recovery cannot clear protected-effect
precautions. An explicit Basic-own-key retirement can close unknown
historical intent only after actual execution and protected-effect review.

[The executable protocol](../job-recovery.md) fixes a shared admission/executor
companion flock, independent open descriptions and overlapping queue/worker
leases. Exclusive review ownership spans fresh worker/helper proof, original
archive-lock acquisition and final store rescan/publication. Helper exchanges
occur outside store, runner, archive and configuration locks. A reviewed old key
is permanently fenced while its historical outcome remains unknown. Previous
uninterlocked executors require an independently proved deployment drain.

Visible authenticated browser recovery may automatically GET original evidence
within existing budgets. This narrowly supersedes deliberate-only observation
after restore/reconnect/visibility return. Hidden pages still abort reads and
fence late responses. No job POST, retirement, retry or protected-outcome
confirmation becomes automatic. Schema 2 preserves schema-1 handles atomically.

## Rationale and alternatives

One preserving-entry file and the existing store flock avoid a second multi-file
transaction. No compaction/expiry makes non-revival directly testable. A retained
fixed unknown filename deliberately makes the exact 0.3.1 predecessor refuse
admission while preserving compatible exact-ID reads. Deleting browser evidence,
inferring nonexecution from 403/404/free flock, using a process mutex alone,
reviving keys after retention or adding a resumable workflow engine were rejected.

## Consequences and relationships

Capacity refuses new work instead of deleting fences. Review requires fresh
whole-worker and protected-effect evidence, not only missing receipts. Existing
configuration/host outcome rules remain independent. No new runtime dependency
or public receipt state is added. A rollback retains compatible recovery/admission
authority; older backends cannot regain admission by removing new state.

Amends [114](decision-114.md), [115](decision-115.md), [118](decision-118.md),
[141](decision-141.md), [145](decision-145.md), [146](decision-146.md),
[150](decision-150.md) and [154](decision-154.md) only as identified above.
See [schemas](../schemas.md#133-original-intent-dispositions-schema-1),
[API](../api.md#original-intent-dispositions-and-readiness),
[invariants](../invariants.md#original-intent-closure).
Design and predecessor source inspection are evidence of the chosen protocol;
they are not executable race/crash or installed acceptance.

## Historical refusal qualification (2026-11-03)

A later refused same-key transmission cannot prove that an earlier missing or
expired transmission never ran. Preserve the original refusal fields forever;
allow only its null review to gain one complete exclusive historical-retirement
proof. Project that reviewed key as retired unknown without deleting the refusal.
This narrowly amends the original blanket entry-immutability wording. A second
log, key revival or a special replay/dismiss command were rejected: the existing
single-file atomic transaction and full review already provide the needed
monotonic evidence. A saved browser disposition causally linked to its known new
submission can be freshly matched after reload; an older unknown without that
link must take the explicit review path even when a later refusal exists.

## Server implementation evidence

The [store](../../src/hfcache/api/operations.py),
[independent disposition/interlock models](../../src/hfcache/api/intents.py),
[authenticated routes](../../src/hfcache/api/intent_routes.py),
[offline activation](../../src/hfcache/api/intent_activation.py),
[runner](../../src/hfcache/api/runner.py) and private worker/helper implement
the server protocol. Focused source tests cover
[durability/previous reader](../../tests/unit/test_intent_dispositions.py),
[authenticated HTTP](../../tests/unit/test_api_intents.py) and
[exclusive review/handoff](../../tests/unit/test_intent_review.py).
The activation module uses the real selected-runtime validator; a weaker
handwritten predecessor reader is deliberately excluded. The protected runtime
renderer/installer must supply the fixed invocation/mounts/label after actual
previous-executor drain. Owned tests are neither installed helper confinement nor
browser/deployed retirement proof.

The server source gate25 passes9644 backend tests, three locked wheel profiles and
all required strict web/source-browser/real-API read checks with1276 source files
frozen unchanged. The executable exact0.3.1 c23abba reader drill refuses new-state
scans/admission while retaining compatible exact-ID reads. These source proofs
leave browser recovery, protected installer wiring/drain and installed workflow
conformance with their selected later packages.

## Browser implementation refinement (2026-11-03)

Closed export-only DTOs describe the existing raw readiness and intent wire
responses through the same audited generator. A single bounded readiness read
uses existing read coordination and response reservation. Its monotonic30-second
advisory lifetime does not turn unknown optional facts into denied permission.
Visible saved originals reconcile with authenticated GETs in the existing pools;
hide, authentication and cross-tab changes abort and fence their callbacks.
Late POST acknowledgement preserves handles without donating current proof.

Schema2 migration validates the complete preserving replacement before writing
once under the fixed storage key. Unverifiable post-commit readback retains the
exact validated original export and blocks submission; restoring it requires a
fresh equality read of this migration's own replacement, never a blind overwrite
of concurrent/unknown storage. Its original scope, handles, summaries and
32-record/64KiB/reserve limits remain. Causal refusal proof is created only for
a new current submission's typed closed response followed by its own-key GET;
a saved matching disposition ID requires fresh verification on restore. An older
unknown cannot borrow a later refusal. Explicit reviewed retirement remains a
separate confirmed action. Protected configuration/host-effect precautions remain
independent even after generic terminal or disposition evidence. These implement
the accepted protocol; no new architectural choice or dependency is introduced.

Reviewed retirement may preserve an original browser operation ID, receipt
identity and saved terminal summary when the current own-key intent is unknown.
These retained fields remain historical evidence; they are never overwritten by
closure or promoted to fresh outcome proof. A retained-ID Review action requires
fresh RAM-only own-key unknown evidence under the current authentication and
visibility context. Conflict remains blocked for operator review; a not-admitted
projection cannot contradict retained admission. Record-specific observation
authorizations bind the current disposition, and closure fences older callbacks
without clearing independent configuration or host-effect precautions.

## Coordination metadata child refinement (2026-11-04)

Installed native retirement returned503 because the confined root
helper, limited to SETUID/SETGID, cannot directly traverse the service-owned0700
runtime directory. Its generic label reader also requires root ownership,
whereas the companion must remain service-owned. Use the existing bounded
protected metadata-child launch for a separate fixed `observe-intent-locks`
role. Only that child changes effective credentials, derives the principal from
the independently loaded matching deployment/account and inspects both existing
coordination inodes without opening or locking their bodies. It never requires
or claims an active read-only guard for manual current-boot operation.

The daemon retains its threaded credentials, validates the closed typed reply
and actual work/deadline against its captured deployment, independently reads
the authenticated API PID's exclusive companion flock from `/proc/locks`, and
pins complete lock metadata/SELinux contexts plus runtime-parent identity
across review. The child brackets inspection with captured-authority and lock
revalidation. Expired children retain their existing actual-exit drainage.
Changing runtime permissions, adding DAC capabilities, switching credentials
inside the daemon, weakening labels or pretending the guard is held were
rejected. This is a conformance repair within the accepted helper boundary,
with no dependency, public operation, grant or architectural decision added.
Owned source tests model SELinux labels separately from their actual Linux
USER-namespace DAC/capability proof. Matching installed Enforcing retirement and
the new final strict source gate remain independently required.

## Whole-host UID review refinement (2026-11-04)

Installed retirement then exposed the whole-host peer observer's missing
proc-state read authority at the kernel process directory. The
[decision150 refinement](decision-150.md#whole-host-proc-state-classification-refinement-2026-11-04)
uses search-only no-follow ancestor handles and the necessary read-only
process-domain metadata permissions, preserving every existing neverallow and
the helper's domain/capability/namespace limits. Exactly four UID fields and
coherent process identity remain required. Failed, vanished or unknown process
evidence never permits skipping a possible executor. Type-wide proc-file rights
and their environment/read-gate limits are explicit; they are not new archive,
Hub or credential object rights. Matching policy installation and fresh actual
Enforcing metadata and payload-denial evidence remain required.


## Rootless vendor-broker review refinement (2026-11-04)

The first installed guarded rootless retirement reaches complete executor review
but refuses the fixed user broker's specialized unit-file status check. The
[decision150 refinement](decision-150.md#fixed-rootless-broker-metadata-refinement-2026-11-04)
adds only that metadata type's read/status rights, retaining the closed broker
selector and full process proof. Unknown/failed executor evidence still refuses
retirement. Preserve the original request key and uncertainty, all failed
responses and every existing disposition/receipt. No job replay, skipped broker,
new control permission or historical nonexecution inference is authorized.
Matching gated/installed conformance remains required.

## Notify-worker executor identity refinement (2026-11-04)

Installed rootless retirement reached whole-executor review after the fixed
broker metadata repair, but compared every unit MainPID to a Podman run command.
The indexed verification service is Type=notify with container-origin readiness;
its measured MainPID is conmon, while the exact foreground Podman and payload
remain separate live processes. Distinguish these identities instead of changing
the unit or accepting an executable name. Keep all-running inventory, add only
fixed-name verification inspection to the existing bounded engine child, and
join inspected ConmonPid/MainPID, payload/CID/image/CreateCommand, exact unique
foreground Podman command, credentials, cgroups and coherent births. Revalidate
manager invocation and process identities before returning proof. Exec API/Caddy
semantics, unknown-process refusal, budgets and every privilege boundary remain
unchanged. This is source conformance; fresh installed review remains required.

## Inert executable metadata refinement (2026-11-04)

Installed source7 retirement passes the notify-worker join, then refuses an
unused body read of an inert manager/broker executable. Those bytes never enter
classification. Replace only this body read with fixed-path protected metadata:
no-follow O_PATH ancestors and executable leaf, full inode identity/rejoin and
unchanged exact process/argv/label/parent/cgroup/credential/birth checks. Bracket
classification with executable-link, metadata and process revalidation, joining
stat of the exact kernel exe link to the retained fixed leaf before and after.
Unknown
paths and failed or changing observations still refuse under unchanged budgets.
Do not add init_exec_t/dbusd_exec_t body reads or a generic executable exception.
Actual loaded target-policy queries then establish that `init_exec_t` and
`dbusd_exec_t` lack even file-getattr rights. Add only those two metadata grants;
their type-wide scope is not a pathname restriction. Keep every neverallow and
conmon's existing getattr-only rule unchanged; no body open/read/map/execute or
control right follows. This changes no capability, unit, dependency or operation.
Source and copied-policy checks cannot substitute for fresh actual confined
installed retirement qualification.

## Non-dumpable PAM lineage refinement (2026-11-04)

Installed source8 review authenticates the other inert executables, but the
stock non-dumpable PAM child denies the ordinary UID observer's kernel exe link.
Kernel ptrace read gates remain independent of SELinux file-getattr rights.
Recognize only the exact `(sd-pam)` candidate through a separate protected stock
user-manager/PAM lineage proof, before any link read. Bind the loaded vendor
unit/PAMName/User/type/invocation, manager PID/birth, direct parent/init.scope,
exact init_t:s0, principal credentials, initial maps, own process IDs, no groups/
tracer/active or inherited capabilities, sleeping/no-pending status and coherent
no-follow proc objects. Revalidate child/status/context/parent and manager unit.
The directory remains service-owned and the kernel exe symlink root-owned; the
latter alone is insufficient. Do not follow it or claim executable-image proof.
Remove the old generic PAM image clause; the other four inert roles retain full
protected executable/inode proof. This narrowly relies on the existing trusted
root stock manager/PAM boundary; it adds no error fallback, skip, capability,
policy permission, PAM/process change or dependency. Unreadable, unknown, extra
and changed observations refuse. Actual confined component and installed
retirement qualification remain independent of modeled source regressions.

## Detached authenticated keeper refinement (2026-11-04)

Installed source9 review passes the closed PAM proof, then refuses the exact
already engine-authenticated catatonit pause keeper solely because it is adopted
by PID1 instead of parented by the active user manager. Cgroup placement does
not establish parentage. Accept only those two specific parent identities, while
joining captured process UID/GID arrays and maps to the existing prepared
keeper. Preserve the fixed protected record, PID/birth, namespace owner/maps,
exact pause argv/domain and protected executable/inode proof, with parent and
process revalidation. Unknown or duplicate actors, arbitrary parents and changed
observations still refuse. This adds no read, privilege, policy/unit change or
dependency; actual five-inert component and installed review remain independent
of focused source regressions.

## Fixed broker process-context metadata refinement (2026-11-04)

The finite actual helper-domain five-inert component reaches the fixed broker
context read and records an Enforcing process-getattr denial against
unconfined_dbusd_t. A separate bounded same-domain/UID diagnostic on both fixed
brokers proves exe readlink and follow-stat need only lnk_file read, not getattr.
Add exactly those two helper-to-broker metadata forms. They are type-wide, not
PID/path-scoped; link read includes following other same-type links, subject to
independent target-file permissions and kernel read gates. Retain the fixed
manager/PID/birth/parent, argv, protected image/inode and exact context checks.
No link-getattr, file-body, ptrace, signal, transition, terminal-ioctl or
manager-control permission is added.
Every existing neverallow and capability/namespace limit remains unchanged.
The failed component and original API refusal remain evidence; metadata-component
success, copied policy compatibility and full installed retirement are distinct.
