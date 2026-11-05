# Review and apply archive maintenance

Open **Maintenance** on the existing authenticated HTTPS interface. These controls
require an enabled interface with matching backend/assets. See [interface availability](README.md) and
[deployment](deployment.md). Opening the workspace starts no maintenance job.

Maintenance can remove archive content, resolve transactions or replace a damaged
publication. A preview is a real keyed job that creates operation history while
reading current evidence. It changes no archive data, and its result never grants
deletion authority. Apply is a separate, deliberately confirmed job. The service
reloads policy and proves scope and evidence under the archive lock; the preview
does not freeze what a later execution will find.
Prune, purge and repair can first reconcile known unfinished transactions. Their
effects are therefore not a promise to repeat only the displayed preview rows;
quarantine cleanup deliberately performs no unrelated reconciliation.

## Permissions and effects

Administrator sign-in alone grants no maintenance authority. A browser preview
needs REST read capability and the protected helper's **control** permission.
Apply and repair need REST write capability and its **archive** permission.
Repair uses installed Hub authority; it does not require an additional browser
Hub grant or accept credentials in the form. **Read maintenance permission
evidence** is an explicit status read, not a grant or a prerequisite host-read
capability for submitting an otherwise authorized action. The server checks fresh
authority at admission and execution.

Read-only storage and deployment restrictions still apply. A permission display
does not prove that an archive is healthy or writable. No maintenance control
initializes an archive, edits protected policy, changes confinement or cancels
accepted work.

## Preview, review and confirm

1. Choose a **Maintenance action** and enter its bounded scope as described below.
2. Choose **Preview maintenance**. Keep its original operation key and ID. HTTP
   202 means acceptance, not a successful plan.
3. Observe the original preview. Review its complete successful result, including
   identities, reasons, warnings, estimated bytes and blocked evidence. Loaded
   plan rows are paged; inspect the relevant pages rather than treating the first
   page as the whole plan.
4. Choose **Confirm reviewed maintenance**, then **Apply maintenance**. Apply
   submits the original typed scope, not the returned plan or a path from it.
5. Observe the new original application and its domain result. Keep successful,
   partial and failed entries distinct.

Only a complete successful preview for the unchanged input and current browser
session can enable confirmation. An empty prune or purge plan shows nothing
eligible; recovery also requires actionable work and no blocked entry. A failed,
partial, unavailable or malformed preview cannot enable Apply. Quarantine with
no remaining eligible content likewise needs no cleanup job.

Every attempted input edit retires readiness, including an invalid or refused
edit. A new preview, leaving the workspace or reconnecting also requires renewed
review. Confirmation is consumed by one Apply attempt; a local refusal does not
silently rearm it. **Clear maintenance input** clears local intent only. It does
not delete original handles, archive evidence or backend work.
Form input and reviewed evidence remain bounded local memory, not a persisted
replay body. Copy original recovery handles before closing or reloading.

### Prune retained revisions

Choose all configured repositories or enter whole selectors, one per line, such
as `model:organization/model`. A revision suffix such as `@SHA` is not accepted
by this form. Disabled configured repositories remain eligible for configured
retention; unmanaged repositories use purge instead.

Prune removes at most one eligible non-current revision per repository in a
round. Current is protected. Reducing the configured retention limit does not
immediately delete revisions; review each further round separately. Retention
defaults to three unique revisions, with five also supported. A plan's historical
reason text does not establish the installation's current retention setting.

### Purge unmanaged repositories

Choose explicit whole **Repository selectors (one per line)** or all unmanaged
repositories. The scopes are exclusive; a SHA is not a whole-repository selector.
Configured repositories remain managed even when disabled and cannot be purged.

Purge removes the selected unmanaged repository's retained revisions, including
its current reference. This differs from prune's protection of current. Unknown
layout refuses. Each repository has its own transaction, so an earlier completed
purge can remain committed if a later repository fails. All-unmanaged scope is
resolved again at execution; the preview is not an immutable deletion list.

Logical bytes and unique-byte estimates are not a promise of physically reclaimed
NAS space. Hardlinks, compression, deduplication and snapshots affect allocation.
Manifest and reason audit evidence survives supported deletion.

### Recover unfinished transactions

Recovery derives its scope from current journal evidence; there is no path or
transaction picker. Review actionable and blocked counts and their explanations.
Apply stays disabled when any entry is blocked or none is actionable.

Recovery resolves only explainable checkpoints and prefers preserving excess
content to guessing. Unknown or ambiguous journals, trees and audit records must
remain for operator investigation. Recovery can finish known committed work; it
does not initialize an archive or indiscriminately empty quarantine. See
[transaction refusals](../recovery.md#transaction-refusals).

### Clean proven quarantine

Enter complete 32-character lowercase hexadecimal **Quarantine transaction IDs
(one per line)** from known status or recovery evidence. A path, prefix, glob or
inferred ID is not accepted. Review the entire named batch, including entries
already absent.

Cleanup applies only to supported abandoned publication staging already rolled
back by recovery. Every named entry must be empty or redundant against freshly
verified matching content in the current retained publication. Changed bytes,
unique content, repair quarantine, unknown identities and unfinished work refuse;
the interface does not silently remove refused IDs from a batch. Cleanup retains
journals and does not authorize unrelated recovery. Follow
[grace and quarantine](../recovery.md#grace-and-quarantine) for the underlying
procedure.

## Repair from an integrity finding

Open an actual verification report and choose **Review repair from this finding**.
The report supplies archive and run attribution; the finding supplies repository,
full SHA, publication ID and its original expected/observed evidence. Missing
identity or an invalid reference/manifest finding cannot become a blind repair
request. There is no free-form repair SHA or archive path field.

1. Review the original finding and enter an optional bounded **Repair reason**.
   Repair concerns the whole publication, not just the named file.
2. Choose **Check repair evidence**. Existing bounded reads recheck that exact
   SHA reference and matching manifest. Their publication must still match the
   finding; generation comes from this fresh metadata, not an invented finding
   field. Changed, missing or refused evidence prevents confirmation, without
   falling forward to current or another publication.
3. Review the fresh publication identity and original expectations, then choose
   **Confirm reviewed repair** and **Repair reviewed revision**. Edits,
   navigation, reconnect and the first submission attempt retire confirmation.
4. Observe the original repair and retain the actual retired and replacement
   publication IDs, transaction, retirement record and grace deadline.

The existing repair request names a full SHA and reason. It carries no publication
ID comparison or atomic compare-and-swap condition. Fresh browser proof is not a
lock on that publication: the service independently resolves and verifies its
execution instance under the archive lock. If the actual retired ID differs from
the reviewed finding, preserve the result and investigate the changed instance;
do not claim that the original finding was repaired.

Repair downloads only the immutable SHA into isolated cache and verifies it
against the original path, size and digest expectations. It rechecks the new
publication before switching references, keeps the same SHA and generation and
assigns a new publication ID. It never changes expected hashes to match damaged
bytes. The old locator remains available for the configured grace period; it is
not immediately deleted. Upstream mismatch refuses replacement but may leave
isolated transaction, cache and control evidence. Preserve that evidence.

After repair, use an explicitly submitted full verification to establish fresh
integrity. A prior finding, current pointer or successful HTTP response cannot
donate confidence to a different publication. See
[integrity failure and repair](../recovery.md#integrity-failure-and-repair).

## Interrupted or refused work

Keep the original key and operation ID for every preview and effect. The existing
[original-operation recovery](operations.md#import-and-observe) controls
perform authenticated reads; they do not replay Apply or repair. **Stop observing
in this browser** stops only local reads. A missing receipt or interrupted API
operation does not prove that archive effects did not occur.

The displayed result preserves busy, partial, integrity and maintenance failures,
warnings, transaction IDs and any completed per-repository work. Do not turn a
partial result into success or a refusal into proof of no writes. Capacity,
history or observation limits require preserving original handles, not clearing
evidence or resubmitting with a fresh key. For unknown effects or blocked recovery,
stop and use the [recovery runbook](../recovery.md) and
[maintenance troubleshooting](troubleshooting.md#maintenance-preview-and-effects).
