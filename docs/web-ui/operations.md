# Run, observe and recover operations

The unreleased Operations workspace submits supported jobs through the existing
API and observes their original receipts, results, events and run reports.
Opening Operations performs no job submission; history and estimates are explicit
reads. [API and CLI submissions](../api-client.md#submission-and-observation)
retain their own credential and authorization requirements. Check the installed
release and [access guidance](README.md) before following these procedures.

## Choose a job and its effects

In **Jobs**, choose **Job**, review **Selected job effects**, then choose
**Submit job** only for the intended scope. The currently installed behavior
offers an optional **Read job permission evidence** read in **Job permissions**
when host-read is available. It shows the
observed effective archive/Hub permissions, refusal reasons and guard state;
opening the workspace does not yet read it automatically. The accepted
[readiness changes below](#accepted-readiness-and-recovery-changes) replace that
optional-only behavior when implemented and accepted. That cached observation
is informational, never authorization or an extra prerequisite for a job. The displayed REST capability is an
explanation, not a grant: Basic jobs also require a fresh protected host binding
and the relevant permission at admission and again before execution. An
unavailable helper, held guard or changed scope can refuse a request even when
read-only metadata is available. Do not switch credentials or repeat a request
to work around a refusal.

| Job | Scope and actual effects |
| --- | --- |
| Installed sizing | Installed configured repositories or explicit selectors. Contacts the configured Hub for metadata and sizing; creates an operation receipt, without downloading model content, changing configuration or writing archive data. Requires Hub permission. |
| Candidate file sizing | Repositories in the selected candidate file or explicit selectors, using compatible installed archive/Hub authority. Sizing does not install that file or grant Apply readiness. Requires write capability and Hub permission. |
| Sync | Installed full or selected configured scope. May download, publish immutable revisions, refresh metadata and enforce installed retention policy. Requires archive permission and real storage/lock checks. |
| Verification | The private offline worker hashes the selected archive scope and persists verification reports/catalog evidence. No Hub, repair, pruning or automatic healing. Requires archive permission. |
| Diagnostics: Read-only checks | Contacts the Hub and reports checks that can be established without archive-write probes or the common archive lock. It remains a keyed job and requires Hub permission. Skipped probes are not proved successful. |
| Diagnostics: Temporary archive probes | Contacts the Hub and performs bounded temporary health probes under the existing archive lock; it does not synchronize repositories. Requires Hub and archive permissions. |
| Refresh offline metadata | Writes supplemental tags/technical observations/cards for the selected current or retained publications, without Hub downloads, payload verification, repair or purge. Full scope includes configured and archived identities. Requires archive permission. |

For Installed sizing or Sync, choose **All configured repositories** or
**Selected repositories**. Candidate file sizing instead offers **All candidate
repositories**; full refresh offers **All configured and archived repositories**.
Enter exact selectors in **Repository selectors (one per line)**, for example
`model:example/model-name` and `dataset:example/dataset-name`. These are synthetic
syntax examples, not recommendations or existing archive facts. The browser
accepts at most100 selectors of at most256 characters and a1MiB encoded JSON
request. Changing action or scope never submits work. Empty selected scope is
invalid; it does not silently become a whole-archive job.

**Candidate TOML file for sizing** reads a file into RAM, at most1MiB of strict
UTF-8, with the entire encoded JSON request also at most1MiB. Escaping/selectors
can make a source-sized file exceed the request ceiling. The page shows only its
filename and byte count, never its contents. It neither edits, exports, installs
nor saves the file in browser storage. Use **Clear selected file** to release it.
A syntactically valid file may still be incompatible with installed protected
authority. **Plan configuration draft** instead opens the existing
[managed configuration editor](configuration-and-tags.md); no uploaded candidate
is copied into that draft.

### Verification and metadata scope

For **Verification**, choose exactly one mode:

- **New publications** uses **Original sync run ID (optional)**, a32-character
  domain run ID from a real sync result. It is not the operation or request ID.
  Leaving it empty uses the server's existing new-publication selection.
- **All retained publications** checks every retained revision in the archive,
  including unmanaged repositories.
- **Exact revision** uses **Exact revision (TYPE:namespace/name@SHA)** with the
  full40-character immutable commit SHA. It selects a retained revision, not an
  arbitrary filesystem path.

**Read verification estimate** is a GET: no job admission, hash read, archive
lock or verification finding. Unknown throughput/duration stays **Unknown**;
logical unique-byte counts are not physical allocation or progress percentages.
The estimate does not establish writability or the absence of storage maintenance.

For **Refresh offline metadata**, choose **Current publications** or
**Retained publications**, and at least one of **Refresh configured tags** and
**Refresh technical metadata**. Technical capture can read bounded manifest-bound
metadata and README source; it does not load a model/dataset or raise integrity
confidence. Unpublished, partial, unsupported and failed records remain explicit.
See [refresh semantics](../discovery.md#transport-and-refresh-boundary).

## Inspect operation results and run reports

A202 means durable admission. Use the original handle below to observe execution;
**Latest original job** does not turn admission into completion. Clearing local
job input, changing workspace, reloading or stopping observation never cancels
backend work or creates another POST. There is no executor Cancel control.

In **Operation and run history**, choose **Read history**. **Operation receipts**
and **Archive run reports** are separate bounded collections. Use **Inspect
operation** for the exact receipt/result and **Read run report** for the selected
domain run. **Read domain run report** also follows a validated result's run ID.
Some commands create a run identity without a durable archive report; a missing
report does not rewrite the original operation result.

Each operation/run page has at most25 rows, with **Previous operations**/**Next
operations** and **Previous runs**/**Next runs**. The browser keeps at most32
cursor positions; it does not scan the whole store. A stale cursor requires an
explicit **Read history** restart, not a hidden all-page retry. Loaded extent is
not a complete archive or repository audit, and selecting a receipt does not
establish ownership of its submission key.
Visible ready rows and the loaded extent describe the same page. A loading view
does not establish an empty archive or a complete history count.

**Validated event page** and **Next events** expose bounded diagnostic events.
Sequence gaps/dropped prefixes remain visible; events and host journals never
substitute for the exact command result. A report's repository/findings lists
page locally25 rows at a time; this does not extend the server history walk.
Report identity and historical policy remain attached to their domain run, even
when current configuration has changed.

| Result | Interpretation and safe action |
| --- | --- |
| Queued / waiting_lock / running | Authenticated execution states, without a terminal outcome. Observe the original operation within its finite read budget. |
| Success / success with warnings | Keep the actual result, warnings and per-repository outcomes. A successful read or admission alone is insufficient. |
| Busy / HFMNT010 | The common archive lock was not acquired in time. This is a benign busy refusal, not an integrity finding. Identify the real executor; never unlink a lock or automatically retry the job. |
| Partial / repository failure | Preserve successful and failed repository entries and their codes. Partial information is useful evidence, not successful completion of omitted work. |
| Integrity finding | Review the exact revision, file, expected/observed evidence and report. Do not infer healing or blindly sync, prune or repair; use the authorized [integrity/recovery procedures](../recovery.md). |
| Interrupted / missing / unavailable | Keep original handles and use the recovery procedure below. No replacement submission, inferred rollback or empty success follows. |

No byte percentage is invented from elapsed time, file count or an incomplete
event stream. A valid failed domain Envelope can arrive over HTTP200; its original
exit code, errors, warnings and validated partial data remain visible.

## Keep the original handle

An idempotency key identifies one original submission in its credential namespace.
An operation ID identifies its admitted API operation. A request ID correlates a
single HTTP exchange; a domain run or report ID identifies separate result
evidence. Do not substitute one for another.

The browser saves a fresh original key before it can transmit a supported keyed
action. If an acknowledgement is lost or unusable, retain that key even when no
operation ID is known. A timeout, failed read, stopped browser or missing receipt
does not prove that execution never began. Never create another key to repeat
uncertain work.

Use **Copy recovery handles** to retain the validated, nonsecret recovery
metadata outside the tab. The copy contains handles and their scope, without
passwords, bearer tokens, request bodies, configuration text or results. Keep it
with the relevant operator evidence. Browser local storage can be unavailable or
cleared by the profile or administrator; it is not an execution ledger. Closing
a tab does not delete its saved recovery handles or cancel backend work.

## Import and observe

**Handle type** presents three radio choices. Use Tab to focus the selected
choice and arrow keys to change it. A legacy key also exposes **Original
credential class** radio choices. Changing either choice preserves the typed
handle; it performs no lookup or submission. Credential classes describe the
original handle's namespace and do not grant authority.

1. Confirm the intended HTTPS authority, public prefix, configured archive and
   administrator identity.
2. In **Import original handle**, choose the handle type, enter its exact value
   and choose **Save original handle**. This saves local recovery metadata and
   sends no API request.
3. Choose **Observe original operation**. Key lookup uses the current
   credential's original-key namespace; ID observation reads the exact original
   operation. Preserve any validated ID learned from the response.
4. Interpret admission, execution and domain result separately. A 202 is durable
   admission, not completion. A terminal domain failure retains its original
   exit, errors and validated partial evidence.

A rejected handle is reported as an error alert; a successful local save uses a
polite status announcement. Focus stays on the current control. This feedback
neither submits an operation nor starts a lookup: observation is the separate
explicit action above.

Imported handles have an unknown original creator. An operation visible to the
current reader was not necessarily created by that reader. ID-only observation
does not prove ownership of an idempotency key or grant protected configuration
outcome access. It cannot resolve a different uncertain key-only record.

Administrator Basic keys are scoped to the stable administrator subject. Password
rotation with that same subject retains the namespace; a different subject does
not. Previously retained bearer keys use a different namespace. Keep a manually
imported legacy key as an unbound reference; do not associate it with the current Basic
session or claim that a missing Basic lookup proves nonexecution. Its presence
alone does not permanently block unrelated actions in the current namespace.
An original operation ID can still be observed with the current authorized
reader. See [API recovery](../api.md#reconnect-after-lost-acknowledgement).

## Reconnect without replay

An API restart can change the API instance while leaving the original authority,
archive and administrator subject unchanged. Explicit reconnect obtains fresh
authenticated context, clears private cached reads and permits new observation
of the same original handles. It does not rewrite their admitted scope or
resubmit their requests. A local authentication-generation change clears private
caches even if the returned scope has identical values.

Changed origin, prefix, archive or subject pauses incompatible observation.
Retain the original handle and reconnect to its intended authority rather than
silently rebinding it. An authentication failure likewise clears private evidence
without discarding unresolved safe handles. A changed interface build or wire
contract requires **Reload interface** after preserving handles and unsaved work;
the interface never reloads or replays an operation automatically.

**Stop observing in this browser** stops this browser's polling and pending read
requests. It does not cancel, stop, roll back or clean up an accepted backend
operation. Navigation and view unmounting do not replace the route-independent
original-operation controller. To observe again, use the original handle.

## Uncertainty and storage failures

| Observation | Meaning and next step |
| --- | --- |
| Queued, waiting or running | These are authenticated API operation states, not terminal domain results. Continue bounded observation of the original operation. |
| Failed domain result | Preserve the original Envelope and its classification. Do not turn partial evidence into success. |
| Interrupted API operation | The API cannot resume that admitted execution. This says nothing about separate protected host outcome history. |
| Missing or expired history | The result is unknown. Keep the original key/ID and operator evidence; do not submit again or remove evidence. |
| Observation stopped, unavailable or limited | Only local observation ended. Work may continue. Keep the original handles and explicitly resume a bounded read when appropriate. |
| Restored prepared or terminal record | Saved metadata is unverified until an authenticated original lookup/read establishes its current meaning. A stored terminal summary is not backend success. |
| Submit job stays disabled after reload despite Allowed job permission evidence | A saved host action may still need fresh protected outcome evidence. In its recovery record, choose **Observe original host outcome** and check **Protected host outcome** and **Pending protected work**. Permission evidence or a generic receipt alone cannot release this precaution. |
| Storage failed before submission | The browser refuses transmission because it cannot durably retain the original key. Correct storage availability without deleting unresolved handles. |
| Storage failed after possible transmission | Preserve the learned handles in memory and copy them. Further conflicting submissions remain blocked; absence of a saved acknowledgement does not prove nonexecution. |

Only a provable current-session refusal before any fetch can remove its own fresh
prepared record. That removal must persist before its mutation block is released.
The local **Not submitted** summary is memory-only, not a saved terminal outcome.
If removal cannot persist, the original key and block remain. Restored records
cannot assert this exception, and a missing receipt never triggers automatic
registry cleanup.

For a saved schedule change or observer Stop, follow
[Recover an original host action](administration.md#recover-an-original-host-action).
A matching fresh `confirmed` or `unchanged` outcome with pending work **No** can
resolve the browser's precaution. Preserve the original handle and history;
never repeat Stop or delete recovery records to enable a new job.

For configuration application, **unknown** and **installed_unconfirmed** remain
separate host effects. A generic failed/interrupted API receipt cannot clear
them. After **Observe original operation** establishes the original application's
route and receipt, **Observe original configuration outcome** explicitly reads
its protected history. It also works for a restored/imported original Basic key
after the editable draft is gone. The editor labels its corresponding action
**Observe original application outcome**. This read is separate from generic
receipt polling and requires configuration-read authority under the original
subject. An imported ID does not supply the missing original key. Use the
[original configuration outcome](configuration-and-tags.md#observe-an-interrupted-application);
do not replay Apply, delete pending state or infer rollback. Draft validation and
preview readiness are not restored from saved recovery metadata.

Only a fresh original-key lookup and matching protected outcome can establish
current-session configuration knowledge: the exact original application/archive
must match a verified terminal API receipt, with `pending=false` and state
`confirmed` or `unchanged`. That RAM-only proof can release the browser's
submission precaution; `unchanged` means no installation. The persisted record
and generic receipt remain unchanged. Reload/reconnect clears the proof, so a
saved terminal summary cannot release the precaution on its own.

Cross-tab notices are advisory. They neither lock execution nor prove another
tab's identity, result or authority. They cannot authorize a new POST, cancel
work or import another tab's state automatically. Server idempotency and original
execution locks remain authoritative.
After a notice that another tab changed recovery history, copy any memory-only
handles and reload to read the saved history before submitting new work. Reconnect
alone does not merge another tab's records or clear that precaution.

## Finite observation

When the page becomes hidden, the browser pauses active operation polling and
its pending retry delays. It also stops in-flight original configuration and
host-outcome reads. Original keys and accepted jobs remain unchanged; backend
work continues. A late response cannot establish a new outcome after that pause.

Returning to the page does not restart observation. Choose **Observe original
operation**, **Observe original configuration outcome** or **Observe original
host outcome** deliberately for the corresponding original handle. This also
applies when admission completes while the page is hidden: the acknowledged
handle is retained without automatic polling. Never submit a new job to resume
observation.

| Bound | Browser behavior |
| --- | --- |
| Recovery metadata | At most 32 records and 64 KiB of encoded session metadata; unresolved handles are never evicted to make room. |
| Retained read evidence | One shared 32 MiB budget for encoded logical evidence. This is not an exact JavaScript heap or process-memory limit. |
| Each observation response | At most 8 MiB, further limited by its route ceiling: ordinary 16 MiB, artifact 64 MiB, card 2 MiB. This is not a cumulative traffic allowance. |
| Concurrent observation reads | At most two globally and one per handle. |
| Read retries | At most three eligible retries after the initial GET, delayed 1, 2 and 4 seconds. POST is never retried. |
| Observation session | At most 120 cycles or five minutes, whichever ends first; progress does not renew that budget. |
| Retained events | At most 32 events and 64 KiB per handle; truncation and sequence gaps remain visible. |

Reaching a limit is an explicit unavailable or stopped observation, never a
fabricated empty result or permission to repeat the action. Rejected bodies and
raw logs are not retained as evidence. Authentication, protocol and scope
refusals remain distinct from retryable read failures.

The browser manages Basic credentials and has no reliable application logout.
Use a dedicated trusted profile and follow [access guidance](README.md). Closing
the profile is not backend cancellation. For a problem, share safe codes and
validated handles; never share Authorization headers, tokens or configuration
contents. See [troubleshooting](troubleshooting.md#original-operation-recovery).

## Accepted readiness and recovery changes

The [original-intent contract](../job-recovery.md) specifies the next behavior;
this section supersedes the optional-only permission read and deliberate-only
restored-job observation above once that behavior is installed and accepted.
Jobs reads bounded advisory action readiness on entry/change and offers Recheck.
Known archive denial or read-only storage explains an unavailable Sync/refresh
beside its disabled button. Unknown readiness is labelled unknown, and optional
host-read denial cannot become an extra job permission. Every submission still
receives fresh server authorization.

Visible authenticated pages reconcile original jobs with bounded GETs only.
Hidden pages stop reads and reject late proof. Ordinary labels distinguish
Submitted, Running, Completed, Failed, Not admitted and Needs review. A durable
Not admitted result stays visible without becoming a phantom running job. For
a missing original key, the explicit Review original request action explains
historical uncertainty and asks the server for reviewed retirement. If proof
is unavailable, keep the original handle and follow its concrete operator step.
A confirmed retirement says Historical outcome unknown; request retired. A new
job is a separate deliberate action; recovery never repeats the old request.
Keys, JSON and raw receipt states stay in advanced diagnostics. Schema-1 handles
are preserved by atomic versioned migration. Configuration/host unknown effects
retain their independent original-key confirmation rules.
