# Separate privileged host administration from the unprivileged API

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 141.
- Status: Amended; implemented with scoped owned native/rootless fixture acceptance.
- Date: 2026-10-20.

## Recorded implementation scope (2026-11-01)

The fixed protected reader, managed configuration path and native host controls
are implemented. [Human acceptance](../web-ui/test-release-acceptance.md) records
actual native effects and guarded rootless refusals; the
[migration guide](../web-ui/migration-and-rollback.md#compatibility-and-backups)
records old-client, refusal and installed rollback limits. Earlier pending
statements retain the introducing design's historical scope. Original failures,
unknown durable outcomes and separate production/other-platform holds remain.
These observations do not claim an optional instrumented-runner pass.

## Read-only managed reconstruction amendment

[Decision153](decision-153.md) specifies full-byte-bound editable reads and
non-persisting managed validation/preview. That read-only reconstruction uses
descriptor-pinned capture and bracketed exact revalidation without taking or
creating a configuration lock. Persistent preparation and installation retain
this record's original-lock requirements. No installation or automatic replay
follows from a successful preview.

## 2026-10-21 protected-reader amendment

## Context and decision

Require explicit internal administration capabilities plus independently
provisioned protected host policy. Generic REST bearer write grants no
configuration or host-administration authority. Recheck protected selected-release
binding, profile, expected revisions, original guard/lock evidence and permissions
when work executes. Status is a safe bounded projection, separate from daemon
readiness. Missing/unsafe helper or unproved bindings means unavailable/denied,
never a fallback or permission inferred from an absent mask.

Expose fixed configuration read/application, host status, sync-calendar validation,
sync-schedule changes, scheduled sync-observer stop and bounded journal reads as
listed in the [API design](../api.md#web-ui-and-administration-design). A single
schedule action union is `pause`, `resume`, `replace`, `reset`. Only replacement
accepts calendar/delay values; every change requires the exact opaque schedule
revision. Validate calendars/timespans through bounded fixed systemd tools.
Stopping the scheduled observer requires its exact invocation identity and is
observation control, never domain job cancellation. Verification scheduling is
display-only; target/API/worker/socket/mount actions are absent.

Use the existing fixed installed/candidate/backup/configuration-lock paths and
original persistent lock inode. Read/inspection never creates a missing lock or
candidate. Read returns a strict nonsecret editable projection and an opaque
HMAC-bound revision over complete installed bytes, archive identity, target and
schema. Tags therefore invalidate the base even though policy fingerprints omit
them. Resolve typed managed edits server-side, preserving protected fields.
Never serialize redaction placeholders into replacement policy. Root/UUID/Hub
authority, credential sources and restart-only server policy remain manual.

Existing installed/literal candidate validation and planning retain exact shapes
and key canonicalization. The mutually exclusive managed form adds `base_revision`
and typed edits. A successful managed assessment binds exact candidate/base,
server-derived required scope/revisions and original preview operation. Apply
supplies that same edit/base and preview handle; the handle grants no authority
on its own. Managed preview requires omitted/empty caller selectors. Derive
the exact newly added, enabled or retargeted enabled repository set using the
existing preview rule; nonempty scope requires complete Hub sizing and explicit
Hub host permission. Tag/settings/removal-only and all-disabled changes preserve
the existing no-Hub exemption but still require an explicit successful bound
empty-scope managed assessment after validation. No new tag-only exemption is
added. Apply verifies exact required scope, complete sizing where required and
resolved revisions; legacy plan forms retain their selectors.

Capture exact base/candidate while briefly holding the configuration lock; release
it before validation/sizing and all Hub work. Reacquire the same lock, recheck base,
candidate/preview correspondence and fresh policy, fsync the predecessor backup,
atomically install `0640 root:hfcache`, fsync the parent, then confirm exact bytes
and operational fingerprint. Never hold helper/config locks across unbounded Hub
work. Release operation-store/admission locks before helper calls; helper protocol
and config lock paths never acquire those store locks or the archive flock.
Unknown legacy candidate/backup evidence is preserved and refuses application.
A prior fixed backup may be superseded only when tied to a confirmed helper
outcome and durably copied to per-operation private evidence first; this permits
later confirmed applications without deleting uncertain or unexplained history.

Persist keyed admission before effects and independently versioned private helper
outcome evidence at every crash boundary. Generic receipts/results contain no raw
configuration, secret values or executable request. Protected candidate material
has finite size/lifetime; uncertain evidence never expires or is evicted for space.
After interruption, original-key/ID read-only reconciliation classifies unchanged,
installed-unconfirmed, conflict or unknown. Never replay an uncertain write or
automatically roll back/delete its predecessor, candidate or original handle.

## Rationale and alternatives

The helper preserves a small privileged host boundary while the API keeps its
unprivileged archive/service confinement. Root API, writable `/etc`, broad D-Bus
or container-engine sockets would turn ordinary request handling into host
administration authority. A second config lock, policy-hash-only equality,
client-authored full replacement and automatic retry could lose exact-byte
concurrency or uncertainty evidence. None is accepted.

Keep host scheduling in systemd. Rootless schedule/observer permissions remain
false while their bindings are unproved; identical user-manager unit names do
not establish equivalence. Positive native paths must be implemented and proved
on a supported isolated installed profile. A restricted deployment is not a
reason to hide unimplemented supported-profile behavior.

## Evidence and relationships

At baseline `6b8fae2e0997403ae5c716a2e92148af0a972af9`, these REST/helper
surfaces do not exist. This commit accepts the design, with executable
conformance pending. Configuration-file, receipt/helper crash, peer/namespace,
native positive and rootless denied tests are required before availability claims.
Amends [119](decision-119.md), [122](decision-122.md),
[135](decision-135.md), [138](decision-138.md), [139](decision-139.md)
and [127](decision-127.md) only for the replacement transport; their current
guards and historical evidence remain. See [server](../server.md),
[security](../security.md#browser-administration-design),
[API](../api.md#web-ui-and-administration-design),
[schemas](../schemas.md#18-web-ui-and-administration-design-records),
[web UI status](../web-ui/README.md) and [authentication](decision-140.md).

## Guarded application amendment (2026-10-25)

[Decision154](decision-154.md) defines the narrow configuration writer, shared
legacy guard, durable private outcomes and original-handle read-only observation.
It supersedes earlier assumptions of a wholly read-only helper for this fixed
operation; all unrelated authority and original reasoning remain.

## Fixed host-effect amendment (2026-10-27)

[Decision156](decision-156.md) adds a bounded fixed-route host-action lane,
original-process observer stop, independent durable outcomes and finite diagnostic
reads. It preserves archive serialization, original operation identity and this
record's unrelated requirements. Implementation and actual installed conformance
are separately required.

## Original-intent and writer amendment (2026-11-03)

Accepted design in [decision 164](decision-164.md), [decision 165](decision-165.md); implementation and installed conformance remain
pending. One fixed read-only intent-review opcode observes detached helper cohorts and protected pending effects without effect-category or optional host-read grants. A separately protected manual-writer runtime is recognized only with matching mode/mount/guard proof; helper payload neverallows and fresh execution authorization remain.
See the [executable recovery contract](../job-recovery.md). Original rationale
and unrelated requirements above remain in force.


### Protected writer source implementation (2026-11-03)

[Decision165's implementation record](decision-165.md#source-implementation-and-qualification-2026-11-03)
now supplies the closed immutable sibling/mode, original-inode offline activation,
role/domain and preserving procedure source. The original rationale and unrelated
requirements remain. Source/binary/current-boolean checks establish no installed
Enforcing, actual NFS or unattended-boot acceptance; those scopes remain explicit.
