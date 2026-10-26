# Observe and recover original operations

The unreleased interface supports read-only observation and recovery of original
operation handles. Full job forms and the complete Operations workspace remain
under development. Existing [API and CLI submission](../api-client.md#submission-and-observation)
procedures retain their own authorization requirements. Opening this guide or
importing a handle submits no work.

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

Imported handles have an unknown original creator. An operation visible to the
current reader was not necessarily created by that reader. ID-only observation
does not prove ownership of an idempotency key or grant protected configuration
outcome access. It cannot resolve a different uncertain key-only record.

Administrator Basic keys are scoped to the stable administrator subject. Password
rotation with that same subject retains the namespace; a different subject does
not. Old Cockpit bearer keys use a different namespace. Keep a manually imported
legacy key as an unbound reference; do not associate it with the current Basic
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
| Storage failed before submission | The browser refuses transmission because it cannot durably retain the original key. Correct storage availability without deleting unresolved handles. |
| Storage failed after possible transmission | Preserve the learned handles in memory and copy them. Further conflicting submissions remain blocked; absence of a saved acknowledgement does not prove nonexecution. |

Only a provable current-session refusal before any fetch can remove its own fresh
prepared record. That removal must persist before its mutation block is released.
The local **Not submitted** summary is memory-only, not a saved terminal outcome.
If removal cannot persist, the original key and block remain. Restored records
cannot assert this exception, and a missing receipt never triggers automatic
registry cleanup.

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
