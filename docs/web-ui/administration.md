# Administration

Open **Administration** to inspect the archive, API readiness, software identities
and protected host permissions; edit configuration; run explicit diagnostics; and
use the fixed schedule, observer and journal controls supported by the installed
profile. Opening or refreshing a read panel never submits a job or changes a
timer. The interface remains unreleased source until installed through the
[deployment procedure](deployment.md). Keep the recorded installed release until
replacement acceptance and migration are complete.

The human administrator signs in with the configured browser Basic account.
That account is separate from service bearer credentials and host policy. Login
lets you view the interface; it cannot grant archive, Hub or host authority.

## Read the permission evidence

**Host administration** displays the selected deployment, independent host-policy
proof and six effective categories: archive jobs, Hub sizing/diagnostics,
control-state previews, configuration, schedules and scheduled-observer control.
An explicit denial reason is part of each category. Rootless schedule and
observer controls stay denied while their fixed system-manager bindings are
unproved; no same-name user-manager unit substitutes for them.

Supported means the helper could verify the selected installed profile. Guarded
means the original read-only guard is held and archive actions are denied.
Unknown means required facts or binding could not be proved. Unavailable means
the helper cannot currently provide an authenticated bounded observation. Neither
unknown nor unavailable grants actions, implies an inactive service, or proves
an API/worker crash. A known absent guard grants nothing by itself.

**Refresh host status** performs another bounded read; it never submits or retries
an operation. **Denied** carries the reason for a known refusal; **Unavailable**
means required authority could not be observed. **Allowed** describes an
independently verified policy category, not proof that a write would succeed.
Domain locks, storage guards, configured scope and fresh execution checks remain
final. The verification timer is display-only.

## Read archive and readiness observations

**Refresh administration status** reads the current **Archive health**,
**API readiness**, **Verification health** and **Software identities** panels.
These observations answer different questions:

| Observation | How to use it |
| --- | --- |
| API readiness | The daemon can answer its readiness check. This does not establish valid archive policy, archive reachability, free capacity, verification or write permission. |
| Archive health | Read observed available capacity, configured reserve and headroom together with unfinished transactions, deferred cleanup, unknown entries and quarantined bytes. An unreachable archive has unavailable values, not zero usage or a clean state. |
| Verification health | Outstanding failures and the last observed full verification are independent of readiness and metadata coverage. **No full verification has been observed** means no such evidence is available, even when the degraded flag is false. Use exact publication integrity or an original verification report for a particular revision. |
| Software identities | UI/bootstrap build, API version and available protected host-release binding are separate identities. A matching version does not prove a production deployment, healthy archive or successful job. |

A read is a snapshot, not a reservation of disk space or execution authority.
Failed, stale or unavailable evidence must be read again before it is treated as
current. Do not turn a missing value into zero or interpret a complete metadata
catalog as proof that archive bytes have been verified. Findings and warning
lists show finite local pages of 25 rows; loaded extent is not an archive total.

Warnings provide guidance, never an automatic cleanup or repair action. The
[operator warning runbook](../operations.md#warnings) and
[supplemental metadata contract](../discovery.md) remain authoritative.

| Code | Safe next step |
| --- | --- |
| `HFDEP001` | Review declared dependencies in Configuration. Dependencies are never downloaded implicitly. |
| `HFWRN001` | Review recovery and a separate prune preview for temporary over-retention. |
| `HFWRN002` | Logical removal already committed; inspect recovery for outstanding physical trash cleanup. |
| `HFWRN003` | Preserve unknown entries and identify them before any removal. |
| `HFWRN004` | Diagnose stale staging and inspect a recovery preview. |
| `HFWRN005` | Review capacity and reserve. ZFS snapshots can retain blocks after application pruning. |
| `HFWRN006` | Preserve local revisions while upstream is unreachable; this does not trigger pruning. |
| `HFWRN007` | Confirm that the repository is intentionally unmanaged before reviewing a purge preview. |
| `HFWRN008` | Inspect recovery for an expired repair predecessor; grace and quarantine rules still apply. |
| `HFWRN009` | Check the writer-local Xet cache; its advisory ceiling is separate from archive capacity. |
| `HFWRN010` | Review overlap with storage maintenance. Verification scheduling is not editable here. |
| `HFWRN011` | Supplemental metadata or README capture is incomplete or failed. Keep affected fields unknown and the valid publication retained; this does not imply an integrity failure. Review the explicit metadata-refresh workflow in Operations. A GET never refreshes metadata. |

An unfamiliar warning keeps its code and generic guidance. A workflow link only
navigates; any preview, job or effect still requires its own explicit action and
fresh authority.

## Configuration and diagnostics

**Configuration and tags** uses its independent configuration-read/write grants;
host-read is not an additional gate. Follow the
[configuration workflow](configuration-and-tags.md) for one in-memory draft,
exact-base review, validation, sizing preview and original-outcome recovery. A
visible **Allowed** status does not bypass fresh request/execution checks.

The **Diagnostics** panel submits explicit [Operations jobs](operations.md), using
the same original receipts and classified results:

- **Run read-only diagnostics** can contact the Hub and creates an operation
  receipt, but does not perform archive-write probes.
- **Run temporary archive probes** also performs temporary archive writes under
  the archive lock and needs archive authority. First review and select **I
  understand these probes can write temporary archive data.**

Neither runs merely because Administration is opened or refreshed. Inspect
**Original diagnostic job** and its **Diagnostic checks**, retaining failed,
partial and skipped results. A skipped check is not a pass. Use that exact result
and its codes, rather than API readiness or journal activity, to judge the run.

For example, `HFHUB003` can report that the Hub identity is `anonymous` while
`hub.expected_account` names an account. Browser sign-in and granted Hub
permission do not authenticate a Hub account. Preserve that failed diagnostic
and ask the operator to review the installed [Hub configuration](../configuration.md)
and protected credential delivery. Do not paste a Hub token or REST bearer into
this page. A failed identity check can appear alongside successful DNS/TLS checks
and useful storage checks; retain each check's actual outcome.

## Schedule, observer and diagnostic APIs

These rendered controls use the existing fixed host API and its protected policy.
The browser never talks directly to a host manager, file or shell.

### Change the sync schedule

The controls operate only on the fixed system sync timer. First choose **Read
schedule and observer** to obtain current protected permissions, the installed
schedule revision and actual observer evidence. The dedicated observer response
can preserve a real running fact even when the older host-status panel cannot
represent an intermediate oneshot state. A failed read supplies no control
readiness.

For a replacement:

1. Open **Edit sync schedule**, enter an **OnCalendar expression** and optionally
   a **Randomized delay (optional)** value, then choose **Validate schedule**.
2. Read **Normalized calendar**, **Normalized randomized delay** and **Next event
   (server/systemd)**. These values use the server/systemd timezone interpretation,
   including any timezone in the returned text. They are not converted to your
   browser's local time; no separate API timezone field is implied.
3. Choose **Review replacement**, check the intended action and exact revision,
   then select **Confirm reviewed schedule change**. Choose **Apply reviewed schedule**
   once to submit that reviewed intent.

Validation performs no schedule write. Editing any raw input, including an
invalid edit or one that normalizes to the same value, retires the old review.
Refresh, reconnect or leaving the view also requires fresh review. Confirmation
is consumed on the first apply attempt, including refusal or a lost reply; it is
never a retry permission. A revision conflict requires an explicit fresh read
and a new review rather than overwriting another change.

**Review reset** followed by confirmation and **Reset to shipped schedule**
removes the managed override. **Review pause** or **Review resume**, confirmation,
then **Pause sync timer** or **Resume sync timer** stops or starts that timer.
Pause/resume never changes enablement. Replacement/reset reload the manager and
restart only a previously active timer; an inactive timer remains inactive.
Resume or a restart can trigger Persistent catch-up and start the scheduled
observer. These controls do not change the verification timer, stop the
application target, API or worker, or create another scheduler.

The [fixed host API](../api.md#fixed-host-actions-and-original-outcomes) records
stored-file state separately from manager acknowledgement. A terminal API receipt
alone is not proof that both are confirmed. Use the original host outcome below
when any part remains pending or unconfirmed.

On a narrow screen, leaving an edited schedule requires **Stay** or explicit
discard. Discard retires its local review and preserves original operations.

### Stop only the original scheduled observer

After a fresh read, **Review original observer** identifies the exact original
boot, service invocation and process. Review that evidence, select **Confirm
original observer**, then **Stop original sync observer**. The action sends
SIGTERM only to the retained original process; a changed binding requires a new
read and review, never a numeric-PID or replacement-invocation stop.

Accepted backend work and the observer's pending handle survive independently.
Stopping the observer does not cancel, fail or complete its backend job. Follow
that job's original operation/report in [Operations](operations.md). **Stop
observing in this browser** only stops local reads and is separate from this
explicit host action.

Native observer stop needs the separately provisioned confined observer profile.
An ordinary native installation can expose the real observer identity and allow
schedule changes while correctly denying stop with `profile-unproved`. A host
administrator must install and verify the fixed context fragment and dedicated
scheduled-state label; granting a policy bit alone is insufficient. An inactive
timer may be reported as `linked` when installed by an immutable unit symlink.
That state is not calendar enablement; retain the actual unit state and check its
enablement links independently.

### Recover an original host action

Original-operation recovery remains available in Administration. After a lost
reply, preserve the original key and any accepted operation ID. **Observe
original operation** reads the API receipt. **Observe original host outcome**
reads the independent fixed-host facts; the controller verifies the original
authenticated key before that exact outcome read. These reads do not require a
new write grant and never resend the action.

Keep API receipt state separate from host certainty: a stored schedule does not
prove manager reload succeeded, and an acknowledged signal without observed exit
is unconfirmed. Known unchanged means no effect, not successful application.
Missing history, pending, conflict or unconfirmed evidence remains unresolved.
Never submit a replacement key to discover what happened, remove a private
marker or use reset as rollback. Preserve private outcomes, backups and pending
handles for the host operator. Reconnect requires fresh authenticated observation;
saved browser metadata alone is not proof of an outcome.

### Read bounded diagnostic journals

Choose **Sync observer** or **Verification observer**, then **Read diagnostic
journal**. **Previous journal page** and **Next journal page** navigate explicit
bounded pages, retaining at most 32 positions and displaying 25 entries at a time.
They do not follow an unbounded stream or scan all history. Pages are newest-first
and expose only closed event, level and run-ID fields, with explicit gap and
truncation information. Source changes or an expired cursor require a deliberate
new read.

Available history can differ between sources and between reads. An empty
verification journal is an empty observation, including when its timer is
disabled. **Next journal page** stays disabled when the response has no next
cursor. Reading the journal never enables a timer or submits a job to populate
history.

Logs are diagnostic evidence. An empty page, a gap, a run-ID mention or a stopped
observer establishes no operation outcome. Use the original operation result and
exact run report for completion. No journal text is a command or raw exception/
credential source. See [native provisioning](deployment.md#optional-native-schedule-and-observer-provisioning)
and [troubleshooting](troubleshooting.md#schedule-observer-and-journal-diagnostics).

## Provision policy independently

A host administrator installs the selected immutable application/helper and
verifies their exact index before provisioning the independent policy. Keep the
historical interface policy separate. Do not copy true permissions into a new policy
without reviewing their intended scope. Begin with all categories denied, or a
reviewed configuration-only policy on a restricted host.

The policy, deployment index and revision key have fixed protected paths and
strict ownership/modes. The API cannot create or repair them. Follow the
[host contract](../host-administration.md) and
[deployment guide](deployment.md); the helper needs only its API-only Unix
directory mount, never a manager/engine socket or writable /etc mount.
Install the exact reviewed helper unit and entry together. Startup's bounded
ambient SETUID is temporary: the entry must clear all ambient/inheritable bits
before threads or children. Fixed read-only engine observation uses a separate
USER-only child with only namespace-local DAC_READ_SEARCH and SYS_ADMIN at
the fixed engine execution boundary (effective/permitted/bounding mask0x200004),
empty inheritable/ambient sets and locked securebits0xCE.
[Decision151](../adr/decision-151.md) supersedes the earlier SYS_ADMIN-only rule.
Read/search DAC bypass covers all reachable mapped-UID-and-GID inodes, not just
one metadata path; it grants no write or regular-file execute bypass and does
not replace SELinux. The daemon's initial-USER ceiling stays SETUID/SETGID; add
no initial-USER DAC. SELinux must never authorize DAC_OVERRIDE; require its bit
absent at verified steady/fixed-exec boundaries. Prove the masked MNT belongs
to initial USER and MNT-entry/unshare plus archive/Hub/IP and required inode/FD-alias
denials hold under the revised bits. The host observer
keeps initial USER and its original masked MNT view. Do not remove hardening or
substitute a broad Podman command when status is unavailable. A prototype info
result is not installed helper/API acceptance.

The host reader additionally requires the separately installed, enforcing
`hfcache_host_helper_t` SELinux policy from first exec, inherited by every helper
child. Install the exact selected CIL and fixed object labels, then independently
record the actual loaded module/kernel-policy and label facts in root-owned
`/etc/hfcache/host-helper-selinux.json`; the neutral index pins that receipt.
Archive/Hub/credential/container-secret object types must deny helper reads through
aliases as well as direct paths. Retain all masks, capability/namespace limits and
NoNewPrivileges. No policy/label installation or permission grant occurs on a
status read. Unsupported or stale policy/labels refuse. See the
[mandatory SELinux contract](../host-administration.md#mandatory-selinux-isolation).
Owned nonsecret alias-denial and full installed API/helper proof remain required;
earlier source/INFO checks alone do not close this requirement.

## Recover when status is unavailable

Refresh the bounded status read after the host administrator restores the exact
selected helper, policy and protected address binding. A normal helper restart
can replace its socket inside the existing protected parent. Replacing that
parent or changing deployment/boot identity requires restarting the API under
the reviewed deployment procedure. Do not relax ownership, disable SELinux or
substitute an endpoint with a matching UID.

Login, ordinary reads and original operation key/ID/result observation remain
available when host proof is down. A failed observation does not cancel accepted
work. Retain its original handle and reconcile read-only; do not submit another
operation to test whether the first one ran. See
[troubleshooting](troubleshooting.md) and [API recovery](../api.md#reconnect-after-lost-acknowledgement).
