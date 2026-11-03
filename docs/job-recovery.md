# Job readiness and original-intent recovery

This contract specifies the next recovery and rootless writer behavior. It is
implemented server protocol with source validation; the installed release's capabilities and deployment checkpoint
remain authoritative until implementation and installed acceptance complete.
Existing operation receipts, domain journals and protected outcomes retain their
independent meanings. [Decision 164](adr/decision-164.md) explains recovery;
[decision 165](adr/decision-165.md) explains writer authority.

## Readiness and ordinary states

Jobs obtains one bounded authenticated `GET /api/v1/jobs/readiness` on entry,
action/context change and explicit Recheck. It returns only schema version 1,
configured archive UUID/fingerprint, nullable effective `archive`, `hub` and
`control` grants, nullable `archive_writable` and nullable
`verification_available`. Null means unknown. The API obtains action evidence
through its existing independently authenticated helper, without requiring the
optional host-read grant or exposing host identity, units or private policy.
The endpoint requires REST read capability; Basic obtains its own action grants,
whereas bearer capability remains distinct from protected Basic policy.
Missing helper proof yields unknown facts, never permission denied or allowed.
This read does not open payloads, acquire the archive lock or run write probes.

Browser evidence is advisory for at most 30 monotonic seconds and is invalidated
on authentication generation, subject, authority, archive, fingerprint or action
change. Hidden pages abort their reads and fence late callbacks. Recheck is
available after failure. Known denied action or read-only required storage
disables submission and explains the observed fact beside the button using an
accessible description. Unknown facts say Checking or Readiness unavailable;
they never invent denial. Unknown advisory evidence alone is not an additional
authorization prerequisite: the administrator can explicitly submit for fresh
server checks if no known refusal or unresolved original intent blocks it.
An active original local job, unavailable verifier and request needing review
have distinct explanations. Do not claim all execution is idle from this GET.

Ordinary labels are Checking, Unavailable, Submitted, Running, Completed,
Failed and Needs review. Submitted proves admission only. A failed admitted
operation retains its original result, even when execution failed before archive
work. A durable refusal below is Not admitted, never Running or a failed admitted
job. Keys, receipt enums and raw JSON belong in advanced diagnostics; nonsecret
handle export remains available.

## Durable key closure

Add one fixed `intent-dispositions.json` in the public API's existing protected
local operation store. Its independent schema and quotas are defined in
[schemas](schemas.md#133-original-intent-dispositions-schema-1). It is the sole
authority for permanently closed keys. No request body, raw key, password,
bearer or credential-derived digest is stored. Existing Basic-subject and bearer
key digest preimages remain byte-identical. A binding is archive UUID,
credential class and existing namespaced key digest. Closure covers every route
under that key; a supplied route cannot weaken the fence.

First activation is an explicit offline `prepare-intent-state` step in the
existing release installer, with actual executors drained, original store and
archive flocks retained, coordinated backup and a validated predecessor store.
It provisions only the local companion inode and initially empty disposition
file with exact service ownership; it never initializes the archive. Refuse
unexplained files, prior activation or partial provisioning for operator review.
Normal effect readiness requires the file, including an empty one; application
startup never creates or recreates it. A safely opened, pinned store with missing,
corrupt or future disposition authority starts observation-only: admission and
retirement stay closed while authenticated compatible exact-ID receipt/result
reads bypass scans. An unsafe parent or original store-lock inode that prevents
safe store opening refuses startup and requires protected operator review.
Durably publish the initial file under the original
store flock, using file fsync, atomic rename and directory fsync. Every admission,
rejection and reviewed retirement reads it under that same flock. Unknown,
unsafe, missing-after-activation, duplicate, future, contradictory or corrupt
state preserves evidence and closes admission/review; healthy exact-ID receipt
and result reads remain possible. Store opening does not replay any operation.
An activation marker is not recreated over uncertain existing state.

For an authenticated, keyed, fully validated request to a generic registered Job
adapter (including installed/candidate `/plans`), first look for its existing receipt and fence under the store flock. An exact receipt is the
original admitted operation; changed route/body conflicts. Fresh denial cannot
redefine prior admission. Observe existing acceptance without new enqueue or
effect authorization; authenticated namespace/read capability still applies.
Managed configuration previews/applications and fixed protected host-effect POSTs
retain their independent fresh authorization and outcome-confirmation rules.
Their existing receipts remain unchanged and observable through original-key
GET/outcome reads; a refused duplicate POST does not redefine their admission.
All admission lanes still enforce permanent key fences and hold execution leases.
Generic intent recovery never clears unresolved protected-effect precautions.
If no binding exists, release the store flock and perform fresh action/policy/
capacity/readiness checks. Protected exchanges never run under a store lock.
Reacquire the store flock and recheck both authorities before either receipt
publication or closure. Concurrent admission wins as an original receipt;
concurrent closure wins as an immutable fence. Never publish both for one key.

Only an explicit server refusal before durable admission can publish
`not_admitted`. Retain canonical route/request digest and a closed reason
`permission_denied`, `storage_read_only`, `executor_unavailable`,
`admission_unavailable` or `invalid_policy`. Authentication failure, malformed
body/key, arbitrary middleware failure and unpersisted errors cannot assert
closure. A failed fence write/fsync makes the response uncertain and runs no
work. If rename succeeded before a crash, a later validated read can recover
the durable fence; an error response alone cannot do so.

A `not_admitted` fence proves only its validated refused transmission, never
that an earlier transmission with missing/expired history did not execute. The
browser persists the verified disposition for its known newly-created submission
after that submission's closed response and authenticated intent GET; reload
requires a fresh matching-ID GET. Restored older unknown records without this
causal saved disposition require explicit historical review even if a later
refusal has closed their key.

No fence expires or is deleted. At 1024 entries or 1 MiB encoded state, refuse
fresh admission and closure rather than discard a fence. Existing observations
remain available. No compaction, online quota increase or key-revival procedure
is introduced. This finite conservative limit is deliberate; a later migration
needs a separate preserving design. Receipt expiration cannot remove the file
or its entries. Admitted receipt retention remains unchanged.

## Wire surfaces and authorization

Keep existing lookup, receipt, acceptance, result and problem schemas unchanged.
Add these closed surfaces, each obeying existing prefix, authentication, Origin,
body, metadata-pool and response bounds:

| Request | Meaning |
| --- | --- |
| `GET /api/v1/operations/intent`, original `Idempotency-Key` header | Read the caller's namespace. Schema-1 response has `archive_id`, `state` and exactly one of nullable `operation` and `disposition`; states are `admitted`, `not_admitted`, `retired_unknown`, `unknown`. Unknown has both null. It is never nonexecution proof. |
| Fresh refused keyed job POST | Standard existing problem plus header `Hfcache-Intent: closed` only after fence durability. This header is a hint to GET the original intent, never browser closure proof. Older clients retain their conservative uncertainty behavior. |
| `POST /api/v1/operations/intent/retire`, original key header, body `{schema_version:1,confirm:"retire_unknown"}` | Explicit reviewed closure of an original Basic-own-key intent. Returns the same intent projection; it cannot submit or replay a command. |

The intent GET requires REST read capability. The retirement POST requires the
configured Basic administrator and same stable-subject namespace, verified TLS/
Origin/JSON/request header, plus the fixed helper's independent recovery proof.
It requires none of archive, control, configuration-write, schedule, observer or
host-read grants and grants none of them. Bearer retirement, ID-only retirement,
client assertions of ownership, arbitrary routes and imported foreign-subject
keys refuse. The caller presents the key it owns; the server derives its digest.
Retirement is key-wide; the browser's job name/route is diagnostic context only.
Existing receipt takes precedence and is returned unchanged, including failed
or interrupted admission; this route does not retire admitted work.

Disposition projections contain their server-minted ID, state, archive UUID,
canonical route or null, creation time, refusal reason or null and review
evidence digest or null. Never expose key/request digests or private evidence.
Every response is freshly authenticated and strictly decoded. Missing history,
ordinary 403/404/503, closure header, malformed JSON or cached saved state never
releases the browser's uncertainty block.

## Execution interlock and legacy retirement

Use one retained local companion inode at the configured original archive lock
path plus `.intent` (production `/run/hfcache/hfcache.lock.intent`). API and
private worker share this exact inode through fixed role mounts. Independently
provision it with service ownership, mode 0600, single link and the existing
coordination label; startup refuses absent, replaced, unsafe or mismatched state.
It grants the helper metadata inspection only. It is not a second archive-writer
lock and never substitutes for the original archive flock.

Every new admission and every actual executor holds a shared companion flock.
Open a fresh no-follow open-file description for each lease: never upgrade or
unlock a shared common descriptor. Acquire before entering runner/store locks.
An admission lease lasts through durable receipt creation, queue residence and
exact execution/result completion, including failed-enqueue terminalization.
Transfer ownership to the queue without closing it; delegated worker acquires
its own shared lease before accepting work, overlapping the parent's lease.
Parent crash cannot release the worker's independent lease. Both API lanes,
direct private-worker dispatch and restart reconciliation obey this interlock.
No gap may exist between admitted runnable work and its executor's lease.
No persisted request is made runnable after restart. Before the first review,
the approved upgrade must independently drain all previous-release executors,
which did not participate in this interlock; new lock ownership alone cannot
prove those old processes ended. Runtime companion recreation after reboot
requires the same independently reviewed quiescence and root provisioning.

Review runs off the event loop with one finite 30-second deadline. Stop local
new submissions during review; obtain an exclusive companion lease without
runner/store/domain/config locks held. Existing shared leases must actually
finish; timeout says Needs review and does not kill them. Other processes cannot
admit or dispatch while exclusive ownership is retained. Lock ordering is
companion, brief runner/store locks, then service-owned archive lock; no thread
waits for companion while holding the latter locks. Store-lock sections never
include helper IPC, worker waits or archive-lock acquisition.

Under exclusive ownership, check the original namespace's receipt/fence first;
then release the store flock. Obtain fresh actual private-worker status covering
its whole bounded private store, current instance and pending executors, not
just a queried missing ID. Unavailable/mismatched/unresolved evidence refuses.
The fixed helper gains only a read-only `intent-review` opcode. It authenticates
the actual API peer and current selected runtime, proves no detached/active
protected-effect cohort except this review, and checks both configuration and
fixed host-effect pending/history under their original short guards. Pending,
corrupt, unknown or unclassifiable protected effects refuse. It also verifies
legacy writers masked, calendars inactive and no unknown selected-role/process/
cgroup/libpod executor. This review uses existing bounded inspection machinery
and outcome stores; no generic commands, paths, effect or cleanup is admitted.

Keep the exclusive lease while collecting proof. After helper/worker exchanges
finish, acquire the noncreating original archive flock and freshly validate its
identity. Unfinished/needs-operator archive journals refuse without recovery.
Final store rescan under its flock rechecks binding, archive and reviewed
receipt-set digest. The helper proof is valid only within this original review,
same API/worker/helper instances, runtime/policy/archive identity and deadline.
No cached certificate or browser token can donate freshness. Holding exclusive
intent ownership prevents new API/helper effects; any outstanding helper cohort
or pending marker prevents proof even after its caller exits. No exchange takes
place while the archive/config/store flock is held. Failures release owned locks,
preserve all state and identify the unproved executor, pending effect, worker
status or journal as the concrete operator next step.

Only then atomically append `retired_unknown` with server-minted ID, review time,
archive, namespace binding and digest of bounded nonsecret review evidence.
The evidence binds companion/original lock device/inode, actual API/worker/helper
instance identities, selected deployment/policy, receipt-set and protected
outcome observations; retain the evidence in the bounded entry, not a separate
transaction file. For an existing refusal without a review, preserve every original refusal
field and atomically fill its null `review` exactly once. This monotonic evidence
enrichment has the same complete proof requirements as unknown retirement. Its
public projection uses `retired_unknown`, the review ID/time/digest and null
route/reason, while the original refusal remains intact in durable state. A
review already present is immutable. A prior refusal alone cannot short-circuit
historical review.

The projected state means **Historical outcome unknown; request retired**.
It says neither success nor nonexecution and changes no journal, receipt,
configuration or protected outcome. Release locks only after durable publication.
Future old-key requests can observe this disposition but cannot execute.

## Browser reconciliation and compatibility

A visible freshly authenticated page automatically reconciles saved compatible
original keys using bounded GETs only, on initial mount, explicit reconnect and
return to visibility. Reuse existing finite query/operation concurrency, retry,
time, byte, event and cycle budgets; no additional background retry owner.
Hidden pages abort GETs and retire generations. A late acknowledgement may save
handles but cannot provide fresh evidence or restart hidden polling. A fresh
terminal receipt or durable disposition releases only its own job precaution.
Unknown configuration/host effects retain their independent original-key
confirmation rules, including after terminal API receipts. GET never retires a
key, cancels work, changes policy or sends an implicit job POST.

For a key-only missing record, offer one contextual **Review original request**
action. Explain historical uncertainty and explicit retirement before its sole
retire POST. After fresh server proof, retain the original record/handles and
show **Historical outcome unknown; request retired. You may start a new job.**
New intent is a separately reviewed user action with a new key, never an
automatic retry. Ambiguity keeps Needs review with the server's concrete next
step. Durable Not admitted likewise stays visible across reconnect and permits
distinct new intent only after fresh GET verification.

Browser schema 2 migrates schema 1 atomically under the same fixed storage key;
preserve every original field/handle/scope/summary, add nullable disposition and
set only format versions. No restored evidence is initially fresh. Existing
32-record/64KiB/growth-reserve limits remain: inability to persist the complete
migration preserves old bytes and blocks submission. Cross-tab changes and
storage failure invalidate proof and require fresh reconciliation. A predecessor
schema-1 reader must refuse schema 2 without rewriting it; advanced export
preserves either format. Raw credentials, bodies and drafts remain forbidden.

The exact previous server/browser is release 0.3.1, source
`c23abba45f8967d058983043b96843bef62e899a`. Its store `_scan()` rejects the fixed
unknown `intent-dispositions.json` name even when empty, preventing lookup/list/
admission and expiry. Exact-ID `get`/result reads bypass that scan and remain
available for compatible receipts. Test these exact behaviors against that
source, including after all expirable receipts are gone. Do not delete or move
the file to make rollback runnable. A compatible recovery/admission binary must
remain selected; an older UI can be used only with its actual fail-closed limits.
If an older backend is retained for diagnostics, stop its admission externally
and retain a matching compatible reader. A rollback cannot erase fences or
restore write authority to a binary unable to enforce them.

## Offline source entrypoint and deployment boundary

The internal [activation module](../src/hfcache/api/intent_activation.py) runs
only in the selected immutable application runtime after the protected installer
has independently drained actual executors and retained the original archive
flock. Its fixed invocation has no network, credential or archive mount, and
exposes only archive UUID and a new local backup destination. It validates and
backs up both predecessor stores under their original flocks, then durably
provisions the service-owned companion and initial public disposition authority.
Partial or prior activation refuses without overwriting evidence.

The protected installer/runtime renderer must supply that exact fixed invocation,
original/companion mounts and coordination label before installed activation.
This source module is not startup auto-provisioning or an installed acceptance
claim. Recreated runtime objects still require independently reviewed quiescence.
