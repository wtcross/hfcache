# Install exact managed configuration once and observe durable host outcomes

The superseded browser interface has been removed under
[decision 161](decision-161.md). Shared backend, host-helper and web rules below
remain governed by their current contracts.

- Decision identity: 154.
- Status: Accepted; amended as described below.
- Date: 2026-10-25.
- Record introduced: `ad3275ab30ee7e3ea02b553e21d0b3518747c624`.
- Amends [decision122](decision-122.md), [decision141](decision-141.md),
  [decision150](decision-150.md) and [decision153](decision-153.md).

## Deployment and compatibility prerequisites

Deployment requires independently protected profile bindings and validation.
The [migration guide](../web-ui/migration-and-rollback.md#compatibility-and-backups)
defines old-client/format refusals and compatible rollback. Preserve original
failed or unknown outcomes; rollback cannot erase uncertainty.

## Context and decision

A durable API receipt cannot prove whether a privileged configuration rename
occurred. An interrupted request must preserve its original identity and inspect
host evidence without executing that request again. The unprivileged API retains
its existing operation lane; the fixed peer-authenticated host helper owns only
the narrow configuration filesystem effect. It acquires no archive write or
network authority.

POST `/api/v1/config/applications` accepts `{managed, preview}` where `managed`
is the existing exact-base managed edit and `preview` contains the original
successful managed plan's `operation_id` and idempotency `key`. Every apply,
including empty-scope/tag/settings edits, requires a successful complete matching
assessment. The key is checked in the authenticated subject's existing namespace;
neither the preview nor its key grants permission. Admission and execution check
fresh configuration-write capability, independent protected host policy, all six
protected authority fields, exact base/candidate and required selection. Nonempty
selection additionally requires Hub permission. No helper/configuration/admission
lock is held during Hub work. Apply does not run another preview.

Canonical application admission uses the validated managed edit and preview
reference. Only its digest, safe original receipt and fixed transmission-intent
event are persisted in the generic operation store; raw configuration, keys,
credentials and helper diagnostics never enter receipts, results or events.
Admission is durable before helper transmission. A duplicate application key is
looked up before preparing a new base; matching duplicates return the original
receipt without transmitting another effect. Conflicting canonical data refuses.

The helper's fixed `config-apply` request binds operation ID, request digest,
managed edit, candidate revision, expected operational fingerprint, original
preview ID and exact required selectors. It reconstructs the candidate using the
decision153 renderer and independently checks all supplied identities. It mirrors
the application fingerprint's closed schema (including repository order/defaults,
excluding tags and `hub.credential_name`); parity tests guard this independent
standard-library implementation.

## Guarded effect and private state

Private schema1 state lives on the same filesystem at fixed root0700
`/etc/hfcache/.configuration-applications/<operation-id>/`. Files are bounded,
NOFOLLOW, single-link and root0600. Retained original predecessor/backup inodes
keep their exact0640 root:hfcache metadata inside the root0700 directory. A
separately domain-separated HMAC seals
canonical outcome metadata with the existing protected key, independent of the
*current* deployment/policy bytes. Records retain their original binding hashes,
archive, target, request and preview identity. A legitimate later upgrade must
not make authenticated historical outcomes unverifiable.

Under the common flock, refuse unknown candidates/backups/pending records and
enforce the fixed 64-operation/16MiB private quota before mutation. First publish
root0600 `/etc/hfcache/.configuration.pending` as authenticated minimal operation
intent (original operation ID and request digest), fsyncing its file and parent.
Only then create the operation workspace and persist exact private base/candidate
material and full outcome metadata. This order blocks legacy writers even if a
crash interrupts the first private material write. A partial marker stays blocking;
matching marker-only retries observe `unknown` with `pending=true` without creating
anything, and a different digest conflicts. No fixed candidate or backup changes
before full private intent/material are durable. Stages are `intent`, `staged`, `backup_ready`, `install_intent`,
`installed`, `confirmed`. Each metadata publication and file/parent durability
boundary is explicit. Stage the exact candidate as0640 root:hfcache; durably copy
the predecessor to the fixed backup; atomically exchange candidate and installed
files and retain the old original inode privately; fsync both parents. Re-read
exact installed bytes and expected logical fingerprint before recording confirmed
success. Confirm the replacement's exact inode/metadata and full SID against the
writer's descriptor capture, then revalidate every original nonconfiguration
binding in a private copy of the original authority capture. Keep its original
aggregate budget and leave the supplied capture unchanged; do not reload and
rehash the complete native runtime a second time. Only the intended configuration
leaf changes in that private recheck. Remove only the authenticated current pending marker after the confirmed
outcome is durable, fsync its parent, then acknowledge success.

An existing fixed backup may be moved NOREPLACE into the new private workspace
only when its exact inode, metadata and bytes match a previous authenticated
confirmed helper record. Arbitrary legacy backups refuse and require operator
review. Historical private predecessors are never overwritten. Legacy guarded
write/install/remove paths check the same pending marker under the same flock.

The helper gains narrowly labelled writes under `/etc/hfcache` and supplementary
membership in the existing hfcache group for owned0640 file creation, without
adding CAP_CHOWN or changing process credentials during threaded requests.
Dedicated directory/private-state/guard labels exclude generic etc writes.
The fixed configuration directory retains device/inode/owner/mode and full SID
across checks; its entry timestamps may change during the intended fixed-name
publication. All configuration leaves and unrelated captured objects retain
their existing exact metadata checks. Existing hardening, peer proof, protected credentials, no networking and archive
read restrictions remain. The new standard-library module is a fifth indexed,
protected bootstrap input, not a package import from the online application.

## Observation, interruption and retention

An already recorded operation ID is observe-only, including another identical
`config-apply` request; a differing request digest refuses. Fixed `config-outcome`
reads create no directory, lock, pending marker or file and perform no repair.
Safe schema1 outcomes expose original identity, opaque base/candidate revisions,
expected fingerprint, pending flag and one of `staged`, `unchanged`,
`installed_unconfirmed`, `confirmed`, `conflict`, `unknown`. Missing history is
unknown, never proof of nonexecution. Exact disk evidence may classify an
interrupted installation but cannot promote it to confirmed after the fact.
Authenticated confirmed history stays confirmed after later legitimate edits.

GET `/api/v1/config/applications/{operation_id}` requires configuration-read
capability and the original application key in `Idempotency-Key`; both must match
the original subject-scoped receipt. It reads the helper outcome without fresh
effect permission and never retries apply. This independent observation preserves
the generic receipt's monotonic interrupted state. Stored generic metadata remains
available through the existing operation routes. Startup interrupts unfinished
application receipts without helper effects; the original observation works after
the API is ready, avoiding a readiness/peer-proof dependency cycle.

Unresolved/corrupt/missing private history blocks new apply. A confirmed record
whose pending marker survived a crash also blocks writers until operator-reviewed
reconciliation; outcome reads never remove it. No replay, rollback, cleanup or
automatic uncertainty retirement exists. Configuration application receipts and
private outcomes are conservatively retained; quotas refuse new work rather than
discard originals. Operator reconciliation preserves evidence and uses the common
guard; there is no browser cleanup/rollback endpoint.

## Rationale and consequences

Keeping private outcomes beside the configuration permits atomic same-device
predecessor preservation and excludes protected document bytes from online API
storage. A separate observation projection avoids rewriting interrupted receipts
or inferring failure from a lost acknowledgement. Automatically resuming a phase,
rolling back, adopting a merely regular backup, or removing uncertain state would
discard evidence and could repeat an effect. Conservative refusal is deliberate.
Unit fault tests, actual local helper/API integration, shared legacy guard tests
and native/rootless installed Caddy/browser acceptance must establish conformance;
this decision alone establishes none.

## Browser application and recovery composition clarification (2026-10-26)

The structured editor retains the original successful complete preview and uses
a distinct original application key through the existing route-independent
controller. An accepted receipt is not installed success. The explicit browser
outcome action reads this operation with its original subject-scoped key and
configuration-read authority; generic operation polling does not replace it.
Fresh lookup and host-outcome evidence must bind the exact original application
and archive. With a verified terminal API receipt, `pending=false` and state
`confirmed` or `unchanged`, the browser may release only its current-session
submission precaution. Unchanged is known no-install. This proof is RAM-only;
stored recovery/receipt state is unchanged and reconnect requires fresh reads.
Unknown/staged/installed-unconfirmed or pending effects cannot release that block.
API interruption never clears `unknown` or `installed_unconfirmed` host effects,
and an interrupted receipt is not rewritten when host history confirms install.
No browser retry, rollback, marker removal or history cleanup is added. Drafts
and bodies stay out of persisted recovery metadata. See the
[configuration guide](../web-ui/configuration-and-tags.md).

## Fixed host-effect amendment (2026-10-27)

[Decision156](decision-156.md) adds a bounded fixed-route host-action lane,
original-process observer stop, independent durable outcomes and finite diagnostic
reads. It preserves archive serialization, original operation identity and this
record's unrelated requirements. Implementation and actual installed conformance
are separately required.

## Captured reconstruction inside guarded Apply (2026-10-30)

Installed rootless acceptance reached `backup_ready` and correctly retained its
original pending marker when repeated full guard observations exhausted the
unchanged15-second aggregate inspection budget. The locked Apply had nested the
read-only preparation opcode's entry and exit inspections in addition to its
own mutation-boundary inspections. Share only the pure reconstruction from the
same captured configuration; keep public `config-prepare` bracketed as required
by decision153. Under the original configuration flock, Apply still fully checks
the captured authority before its first pending write, before configuration
exchange and after installed confirmation. Preserve every bound, original
peer/capture check, history identity and uncertainty rule. No fresh snapshot,
cross-request cache, timeout extension or replay is introduced. Source tests and
fresh installed acceptance must establish the result separately.

## Manual draft replacement clarification (2026-11-02)

Manual installed-configuration reload requires an explicit accessible decision
for prepared or raw unsaved edits, bound to the reviewed draft/auth generation.
Cancellation preserves readiness and issues no read. Confirmation retires
validation/preview readiness but retains the original base, prepared intent and
mounted raw editor through pending and failed same-authority reads. Only a fully
decoded, scope-checked success replaces all three together, including same-base
responses. This prevents failed reads from losing admitted work without storing
drafts, merging edits or attaching a new base to old intent. Authentication loss,
disposal and newer generations fence stale decisions/responses. Original preview/
application handles and unknown-effect blocks survive independently; configuration
reads establish no protected outcome. Internal post-Apply reload retains its newer-
draft safeguard. See [configuration guidance](../web-ui/configuration-and-tags.md#compare-concurrent-changes-without-losing-intent).

## Original-intent and writer amendment (2026-11-03)

Amended by [decision 164](decision-164.md); Generic original-intent retirement cannot confirm or clear unknown configuration effects. Fresh reviewed retirement refuses pending/corrupt/unknown protected outcomes; original-key configuration outcome confirmation remains separate and never becomes automatic.
See the [executable recovery contract](../job-recovery.md). Original rationale
and unrelated requirements above remain in force.
