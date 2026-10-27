# Troubleshoot browser access and web reads

During isolated functional acceptance, a Playwright `Network.getResponseBody`
error can describe lost test-tool response bytes after navigation. It does not
establish an API outage or permission denial. Preserve the failed invocation,
original process handles, CIDs and sanitized diagnostic. A tooling correction
needs a fresh source gate and a new disposable fixture; do not replay the failed
invocation, weaken TLS, rotate live credentials or restart production services
because of this diagnostic. The host test reads its explicit status reply inside
the browser page after navigation and still checks the real interface state.

An untrusted-TLS test that reports WebKit navigation cancellation has not proved
certificate refusal. Preserve that failed run. The test settles its initial blank
page, then makes one HTTPS navigation and records the matching failed transport
request. Acceptance requires a specific certificate error and no HTTP response;
generic cancellation, timeout or connection failure remains a failure. A changed
test tool needs a fresh gate and disposable fixture, without replaying the old run.

## Administrator login

The optional administrator provider and authenticated asset routes are implemented
in unreleased source; installed systems retain their recorded release. See
[protected provisioning](deployment.md) and [interface availability](README.md)
first. `/ui/` requires explicit enablement with matching immutable assets.

| Problem | Meaning and safe next step |
| --- | --- |
| Repeated native sign-in dialog / HFAPI001 / HTTP 401 | The browser's cached pair or configured identity did not authenticate. Verify the intended HTTPS authority, username and reviewed credential delivery with the operator. Wrong username and wrong password deliberately have the same response. Do not share Authorization headers or substitute a bearer in the page. |
| HFAPI021 / HTTP 429 | The two verification workers/eight waiting slots or the global failed-attempt budget are occupied. Wait for accepted verification work and the 60-second failure window; repeated retries increase load. Bearer observation of an original operation remains separate. |
| HFAPI010 / HTTP 403 on a browser mutation | Verify the exact configured HTTPS Origin, JSON Content-Type and application request header. Foreign/missing/null Origins and simple forms are refused. Use the supported UI action; do not disable CSRF or widen allowlists. |
| HFAPI002 / HTTP 403 / exit 10 | The authenticated principal lacks the required permission. Administrator login grants no protected host policy; inspect effective grants and the intended action without changing a guard. |
| HFAPI003 during startup | Any enabled REST/MCP bearer or Basic source may be missing, unsafe, changed or malformed; the generic code identifies neither file nor cause. Inspect the intended service's delivery namespace, path, owner, mode, group/ACL metadata and ancestor search access without printing credential contents or hashes. Basic records also require supported schema/hash parameters. The loader uses directory handles without reading or listing parent contents; preserve protected labels and permissions. Restore reviewed provisioning; there is no source fallback. |
| HFAPI009 / unavailable during authentication | The authentication service is unavailable or draining. Keep original operation handles and investigate service readiness/drain; do not replay a mutation. |
| Certificate warning | Stop and correct trust, certificate chain/SAN or endpoint selection. Do not bypass TLS. |
| Old credentials remain after closing a tab | Basic authentication is browser-managed and has no reliable application logout. Close the dedicated profile/session; password rotation needs a new protected record and authorized drained restart. |

An administrator record's stable subject owns its original operation keys.
Keeping the subject during password rotation preserves that namespace. Changing
it separates the new identity; it never proves an old operation did not execute.
Do not delete receipts or resend a lost action to regain visibility.
Old Cockpit bearer keys use a separate namespace from Basic-subject keys. A
manual legacy key remains an unbound reference; a missing Basic lookup cannot
prove its nonexecution. ID-only observation does not prove the current reader
created the operation or owns its key.

Native systemd delivery can show a root-owned `0440` file while a named-user ACL
grants only the service UID read access. Group mode bits alone do not identify
its readers. The [credential contract](../server.md#credentials-and-capabilities)
defines the exact shape and implementation status. Preserve the delivered file
and inspect metadata in the intended service namespace; do not copy plaintext,
widen permissions, change groups or disable confinement to make startup pass.
An ordinary file with another readable group remains invalid.

## Protected host status

Keep the public `state`, `reason`, and `profile` from the original
`/v1/host/status` response with its request identity. A successful confined
`podman info` read does not prove that the helper’s fixed container inspection
succeeded; runtime warnings can be nonfatal. Correlate refusals with the failed
read and its result before changing provisioning. Do not grant service-start or
broader filesystem access from warning text or audit messages alone.

If rootless Administration shows unavailable while the API and helper are
running, inspect the exact helper mount, startup attestation and parent metadata.
The API needs directory search access, not a directory listing. An older client
can fail on an `O_RDONLY` directory open under the intended search-only SELinux
rules; corrected clients use no-follow `O_PATH` handles. Preserve the failed
invocation and apply a reviewed release; do not widen labels, modes or policy.

If transport checks pass, compare the original API init PID and full container
ID with its recorded cgroup. Supported stock Podman can put that init in the
`libpod-<CID>.scope/container` child. An older scope-only helper rejects this
layout. A corrected helper recognizes only that exact child or its exact CID
scope while retaining the other process and security checks. Preserve the
original failed evidence and upgrade through the reviewed release procedure.

If startup, Basic authentication and TLS succeed but rootless host status
remains unavailable, preserve the original sanitized browser result and
matching audit event identities. A helper-domain denial on the user
manager's `systemd/private` socket can mean an older observer selected the
private manager transport despite its explicit session-bus address. The
reviewed observer sets `SYSTEMCTL_FORCE_BUS=1` in its closed environment
for the indexed service account. Upgrade through the protected helper
procedure; do not grant broad socket access or relabel the user runtime
tree. An ordinary service-account systemctl query can compare manager
metadata, but it does not test the helper's SELinux confinement or prove
host authority.

If the fixed session bus is selected, distinguish its socket-file label,
peer-domain connection permission and message authorization. A matching
helper-domain `unix_stream_socket connectto` denial to `unconfined_dbusd_t`
identifies a connection refusal. After that boundary passes, an original
Enforcing helper-to-broker `dbus send_msg` denial identifies the separate
message boundary, including the broker's driver/fallback authorization. Use
only the reviewed rules in the
[isolation contract](../host-administration.md#mandatory-selinux-isolation).
Check bounded original broker service-journal SELinux records as well as
`USER_AVC`: without an audit-write channel the broker can log to stderr. Do not
infer permission from absent audit records, or identify the client PID/method
from the journal reporter alone. Keep existing endpoint labels, hardening,
fixed indexed UID/address and closed metadata argv; do not add generic message
dispatch, private-manager socket access or unrelated ioctl/certificate grants.
A revised CIL needs fresh installation evidence and selected index binding
before restart. Neither denial establishes a successful host-status result or
proves later manager, container or peer checks.

Administration distinguishes **supported**, **guarded**, **unknown** and
**unavailable** host evidence. Unknown or unavailable is not an inactive service
or a healthy/writable archive. Every effective permission is denied until the
required proof is available. A missing guard grants nothing. Rootless schedule
and observer permissions stay denied while their fixed bindings are unproved.

`HFAPI022`/HTTP503 on a new keyed action means protected host proof could not be
established; `HFAPI002`/HTTP403/exit10 means a known permission denial. Preserve
any original receipt/key before troubleshooting and reconcile it read-only. Failed
status never establishes that an accepted action did not run. Do not create a new
key, change a guard or remove evidence as a retry strategy.

Ask the host operator to check the exact selected release/index, independently
provisioned policy/key and `hfcache-host-helper.service`. The service must become
ready before the API pins its protected address. Restore reviewed ownership and
bindings through the deployment procedure; do not open permissions, substitute a
matching-UID socket, disable SELinux or expose a manager socket. Normal helper
leaf replacement within the pinned parent supports refresh. Parent, boot or
deployment identity changes require a reviewed API restart. See
[administration](administration.md) and
[helper deployment](deployment.md#install-the-protected-host-reader).

If the helper exits20 before readiness, inspect its exact systemd invocation
and matching audit events. A denied `getattr` on a `systemd_unit_file_t` symlink
can prevent verification of an otherwise valid installed binding. Compare the
fixed path, inode and literal indexed target before selecting the corrected
reviewed policy. Preserve the symlink and its label. Unrelated audit events do
not establish the failure cause; use the deployment procedure to refresh the
receipt/index/policy together after a reviewed correction.

## Private verification service

`HFAPI016` / HTTP 503 / exit 20 means the separate verification executor is
unavailable or untrusted. This can prevent startup reconciliation or refuse a
verification request even when administrator authentication and metadata reads
work. Preserve original operation handles; an unavailable worker is not evidence
that an earlier operation stopped.

For native system-manager activation, check two independent authorities:
`verification.expected_peer_uid = 0` identifies the listener's creator, and
`verification.expected_socket_owner_uid` must match the actual numeric service
account owning the socket. Measure that installation's account and effective
`SocketUser`; do not assume another host's UID. If the owner setting is omitted,
the expected owner remains the resolved expected peer UID. Setting peer `0`
alone therefore does not describe the ordinary service-owned native socket.
Follow [native verifier identity](../deployment-centos-stream-10.md#native-verifier-identity)
and the [server settings](../server.md#private-verifier-client-settings).

Rootless worker-created sockets retain their equal owner/peer configuration.
Keep the native named-FD3 and rootless notify/listener modes separate. Never
chown an existing node, relax permissions or SELinux, replace the acceptor, or
run a local verifier as a fallback. A corrected configuration takes effect only
through an authorized drained restart and actual API-to-worker validation.

## Interface startup and release changes

| Problem | Meaning and safe next step |
| --- | --- |
| `/ui/` returns an authenticated 404 | The selected installation may have web disabled, an older release or a different public prefix. Confirm the selected release and configured prefix. Building a local UI does not change an installed API. |
| Startup refuses with HFCFG005 and an enabled-asset diagnostic | The manifest, application/wire version, indexed bytes, protected ownership, local mount identity or disjointness proof failed. Compare the selected artifact and reviewed manifest hash. Preserve the failed release; restore a coherent artifact/configuration pair in a separately authorized rollout. Do not grant write permissions, follow symlinks or move assets into the archive. |
| **Starting hfcache** remains visible | The entry module, bootstrap read or build/context validation did not complete. The explanation and **Reload interface** link are inert HTML and remain usable if JavaScript never loads. Check the HTTPS authority, deployment prefix and matching release; share safe status/codes rather than raw bootstrap or credential data. |
| **Interface update required** | A loaded chunk failed or an explicit version check observed a changed artifact. Preserve original operation handles and unsaved work, then reload when ready. The interface never reloads or replays an action automatically. |
| API instance changed with the same compatible release | Explicitly reconnect to fresh authenticated context, retaining original handles. A new instance invalidates cached reads; it does not create a new operation or prove completion. Changed subject/archive/authority requires its own compatible scope, without silent rebinding. |
| **The interface version could not be checked** | The bounded bootstrap read did not produce a matching supported result. Keep the current operation handles. Investigate the selected release and connection; failure does not prove an operation stopped. |
| Missing `.js`/`.css` or an unknown navigation path returns JSON 404 | Only indexed assets, exact workspaces and validated type-aware repository routes are served. The API deliberately does not substitute HTML for a missing module or unrelated route. Compare the selected artifact/prefix; do not add a global history fallback in Caddy. |
| HTTP 503 / HFAPI009 while loading an asset | Static admission is full or draining. At most 16 UI bodies are active with no queue; each send has a 30-second deadline. Wait for the current requests or investigate an authorized service drain. Metadata and authentication use separate capacity. |
| Administration shows disabled actions | A known grant does not make an unimplemented or host-denied feature effective. The displayed reason is authoritative for that scope; signing in does not clear a guard, enable schedules or permit archive writes. |

Reload uses the same trusted URL and browser-managed credentials. Never paste a
bearer into page storage or use a certificate-bypass flag to get past startup.
The application captures assets once; changing files below the running process
does not update its captured release. An artifact transition requires a reviewed,
drained restart, not repeated mutation requests or manual receipt deletion.

## Foreground service shutdown

A completed application lifespan, vanished PID or refused connection does not
alone prove removal of an API-owned Unix socket. The foreground bootstrap defers
main-thread default SIGTERM in a non-PID1 process until its exact owned listener
cleanup finishes, then retains the original signal exit. Activated manager-owned
nodes, PID1 and custom/ignored handlers have separate unchanged lifetimes; follow
[foreground listener ownership](../server.md#foreground-listener-bootstrap).

If a stopped process leaves a socket pathname, preserve it and investigate the
selected version, actual signal/exit, exact device/inode ownership and complete
service drain. Forced termination has no cleanup guarantee. Do not unlink an
unknown node, chmod it or start another writer to make a readiness check pass.
Use the authorized [upgrade and drain procedure](../deployment-centos-stream-10.md#upgrade-and-drain).

## Read results

Check [interface availability](README.md) before using this guide. The shared
query, Library, repository details and original-operation observation state are
available in unreleased source, including bounded README rendering and
[supported jobs/history](operations.md). Installed production
services retain their recorded releases. A read result describes observed information, never
permission to modify an archive or proof that an accepted job has finished.

| Message | Meaning | Safe next step |
| --- | --- | --- |
| Loading server information | The current GET is pending. | Wait for this read or leave the view; aborting observation does not cancel a backend operation. |
| Server status / Server version / Server capabilities / Archive inspection | The expected response and its identity validated. | Interpret the displayed fields and warnings. Readiness alone does not prove writability or publication integrity. |
| Read failed | The server returned a valid failed domain Envelope, including its original error codes. HTTP 200 can carry this state. | Keep the codes and request/run identity. Follow the relevant operator procedure; any displayed partial information is informational. |
| Access refused | The API returned an access problem, such as 401 or 403. | Check the intended endpoint and provisioned access with the operator. Do not substitute another credential class or weaken transport controls. |
| API unavailable | The API returned a classified HTTP problem. | Keep its code and request identity. The service may be busy, draining or unable to load policy; this does not prove the archive is empty. |
| Unsupported response | A version, required field, identity, numeric value or response bound could not be validated. | Preserve the browser/backend versions and safe diagnostic code for the operator. Do not treat rejected content as data or edit it into an acceptable response. |
| Connection unavailable | The read did not yield a valid HTTP response. | Check the intended service connection. The last read is unavailable; its failure says nothing about an earlier job's execution. |
| Read unavailable | Observation was aborted before a validated result. | Start a new explicit GET when appropriate. Retain any original operation handle separately. |

**Refresh read** repeats only the selected GET. It does not retry a mutation,
initialize an archive, start a service or contact the Hub. A fresh response replaces
earlier read evidence; a failed refresh must not leave old capacity or health
values looking current. A malformed or incomplete inventory is unavailable, not
zero repositories. Large integers outside the browser's exact supported range
are unavailable rather than rounded.

For an uncertain operation, keep its original idempotency key and accepted ID.
Inspect that original operation using the established
[reconnect procedure](../api.md#reconnect-after-lost-acknowledgement). A missing
receipt or unavailable connection does not prove nonexecution and does not
authorize a replacement POST, rollback or cleanup. HTTP admission and domain
completion remain different facts.

Share only safe codes and validated identifiers when reporting a problem.
Passwords, bearer values, raw response bodies, configuration drafts and exception
text do not belong in screenshots or diagnostic reports. Operators should compare
the intended API authority, archive identity and supported source/artifact versions
before investigating [wire limits](../api.md#browser-wire-boundary). Changing a
browser limit is a reviewed software change, not an operator workaround.

## Jobs and reports

Follow [Operations](operations.md#choose-a-job-and-its-effects) for actual scopes
and permissions. An enabled control is not proof of writable storage or a fresh
protected grant. Never diagnose an uncertain submission by submitting again.

| Problem | Meaning and safe next step |
| --- | --- |
| HFAPI022 / helper unavailable | Basic job admission lacks fresh protected authority. Preserve any original handle; ask the operator to restore the genuine indexed helper/profile. Read-only metadata does not bypass that boundary. |
| HFAPI002 / permission refused | The action needs its own effective archive/Hub permission. Do not substitute a token, broaden policy or retry under another key. |
| Candidate file refused | Correct strict UTF-8, nonempty source and1MiB source/encoded-request bounds. Syntax validity does not establish compatible archive/Hub authority; the file is for sizing, not installation. |
| HFMNT010 / Busy | Another real executor holds the archive lock. This is not an integrity finding. Keep the original result/handles and inspect that executor; never unlink the lock or silently resubmit. |
| Verification findings / integrity exit | Preserve exact findings and the domain run report. A verification report never repairs or changes expected digests; follow authorized recovery rather than blind sync/prune. |
| Some repository entries failed | Keep all actual successful/failed entries and their codes. A partial result cannot become all-repository success or an empty list. |
| History page limit, expired cursor or event gap | Loaded pages/events are incomplete evidence. Explicitly restart a stale history read or narrow investigation; do not infer a complete audit or missing execution. |
| Report missing or unavailable | Keep the original operation result and distinct run ID. Not every command persists a report, and expired/missing evidence never proves nonexecution. |

**Clear local job input** releases only local intent. **Stop observing in this
browser** aborts only reads. Neither stops a worker, reverses a publication,
clears pending configuration or authorizes a new submission.

## Original-operation recovery

Use [Observe and recover original operations](operations.md) for the complete
procedure and finite browser-session limits. **Import original handle** and
**Observe original operation** perform reads; **Copy recovery handles** preserves
safe metadata. **Stop observing in this browser** does not cancel backend work.

| Problem | Safe next step |
| --- | --- |
| Lost acknowledgement or operation ID | Keep the original key and use authenticated original-key lookup. Do not create another key or replay the POST. |
| Prepared/terminal record reappears after reload | Treat it as unverified until authenticated original observation. A stored summary cannot establish success or nonexecution. |
| Missing/expired receipt or interrupted operation | Preserve handles and follow operator recovery. Missing API history cannot clear protected configuration outcomes or authorize cleanup. |
| Session storage unavailable, corrupt or full | Before transmission, submission is refused. After possible transmission, copy retained in-memory handles and keep the mutation block. Never clear unresolved records as a workaround. |
| Observation cycle, byte or time limit reached | Retain the original handle. Explicitly resume bounded reads when appropriate; reaching a limit says nothing about execution completion. |
| Event sequence gap | Preserve the reported gap and observed sequence. Missing retained progress is not an empty event history or a complete execution trace. |
| Old Cockpit key cannot be looked up as Basic | Keep it as an unbound legacy reference, or observe a known original operation ID. Current Basic lookup is a different namespace and proves no association. |
| Another tab reports activity | Treat the notice as advisory. It neither owns execution nor authorizes another submission, cancellation or automatic handle import. |

Only a provable fresh refusal before fetch can remove its own prepared record,
and only after the removal persists. **Not submitted** is a local memory-only
summary. It is never restored from storage or inferred from a missing receipt.

## Maintenance preview and effects

Follow [reviewed archive maintenance](maintenance.md). Preserve the original
preview and effect handles separately; confirmation never replaces fresh server
proof under the archive lock.

| Problem | Meaning and safe next step |
| --- | --- |
| Preview permission denied | Browser previews need REST read and genuine protected control permission. Apply and repair need REST write and archive permission. Read permission evidence deliberately; do not infer a grant from sign-in or require an unrelated host-read grant. |
| Preview accepted but Apply unavailable | A 202 is not a complete successful preview. Observe its original result. Failed, partial, malformed, stale or capacity-refused evidence cannot arm Apply; empty eligible scope needs no mutation. |
| Confirmation disappears after editing, navigation or reconnect | Expected: review belongs to that exact input and browser session. It is consumed by one submission attempt. Preserve uncertain original work and observe it before considering another deliberate operation. |
| Purge refuses a disabled repository | A configured entry remains managed even when disabled. Configuration removal and archive purge are separate explicit workflows; the browser never silently changes configuration to allow deletion. |
| Recovery reports blocked work | Preserve journals, trees, timestamps and audit. Any blocked entry prevents browser Apply. Do not rewrite checkpoints, move evidence or replay maintenance to force a resolution. |
| Quarantine cleanup refuses one ID | The complete named batch must pass fresh proof. Unknown, unique, changed, repair or unfinished content remains; do not drop refused IDs as an automatic retry or substitute paths. |
| Repair finding no longer matches the SHA reference | Stop. The publication changed or is unavailable. No latest/current fallback or blind SHA request is offered. Check the exact report and current retained evidence separately. |
| Repair's retired ID differs from the reviewed finding | Fresh reads were not atomic publication comparison. Keep the actual result and both identities; do not label the old finding repaired. The replacement needs its own integrity evidence. |
| Busy, partial or failed effect | Keep its actual exit code, diagnostics and any completed entries. A failure can leave committed or isolated evidence. Never infer no writes or resubmit with a fresh key to discover the old outcome. |

Maintenance exposes no archive initialization, evidence deletion, cancellation or
automatic retry. A vanished receipt does not prove nonexecution. Use the
[recovery runbook](../recovery.md) for unknown effects.

## Library search and pages

Follow the [Library guide](library.md) for scopes, tag provenance and same-variant
filter semantics. Search and pagination never refresh metadata, query the Hub or
submit a mutation.

| Problem | Meaning and safe next step |
| --- | --- |
| Zero known matches with incomplete coverage / HFWRN011 | Some relevant labels or observations are unknown, partial, unsupported, failed or missing. Preserve that qualification; do not read zero as proof of absence. Narrow or change the intended scope, or ask the operator about a separately authorized offline refresh. |
| Configured repository has no publication or size | Configuration is intent and includes disabled/unpublished entries. Do not invent an archived revision or count an unknown size as zero bytes. |
| Last-observed tags differ from expected curation | The repository is unmanaged and those labels are historical writer evidence. Current-only filtering excludes them without turning them into current tags. |
| Current publication differs from a retained match | Retained scope can match an older exact pair. Keep its technical facts separate from current inventory; do not mix current bytes/integrity with the older representative. |
| Dataset selection clears quantization/bits/maximum variant bytes | These are model-only predicates. The change is deliberate and visible; dataset formats remain eligible filters. |
| Stale page / HTTP409 | Relevant catalog state changed, possibly only tags. Discard the old continuation and follow the bounded restart. Repeated drift remains a visible refusal, not an endless background scan. |
| HFAPI005, HTTP413 or browser capacity refusal | A scan, projection, response or shared retention bound was exceeded. Narrow the scope. Smaller pages alone do not reduce every whole-query budget; do not raise a limit to conceal missing evidence. |
| Facet value is not shown | The facet may be paged. Check its loaded extent and use explicit Load more when offered; one loaded facet page is not the complete value set. |
| Saved `/ui/library?...` fails on reload | The authenticated shell rejects query strings. Use a supported filter bookmark after `#`, preserving the installation's public prefix. |
| Invalid or oversized filter bookmark | Unknown fields, duplicate scalar values and invalid bounds refuse visibly. Correct the filter input; rejected content must not become an arbitrary request or default empty table. |

An authentication, protocol or transport error follows the [read-result
classification](#read-results). Stale evidence is not current health or capacity.
Do not initialize an archive, weaken authentication or replay an operation to make
a Library read succeed.

## Configuration and tags

Follow the [configuration workflow](configuration-and-tags.md). Preserve the
original preview/application handles before reconnecting or discarding a draft.

| Problem | Meaning and safe next step |
| --- | --- |
| Configuration read/write denied while host status is available, or the reverse | Grants are independent. Review the requested configuration capability and protected policy; host-read is not an extra configuration prerequisite. An ordinary REST writer bearer cannot grant it. |
| Validation succeeded but Apply is unavailable | Validation does not size or assess an operation. Obtain the original successful complete preview for the unchanged reviewed draft and exact base. |
| A form change disables readiness | Every edit invalidates prior validation/preview. Review and validate the new intent, then explicitly prepare a new preview. Do not reattach an old operation ID. |
| Installed configuration changed / stale base / HTTP409 | Keep the draft. Compare the newly read editable projection with the original base and intended changes; reload/re-edit deliberately. Tag-only and formatting changes can conflict even when policy fingerprints match. |
| Another tab changed recovery history | Keep memory-only handles and the dirty draft. Advisory notices cannot merge drafts or settle results; reload saved recovery history before a new submission. |
| Sizing failed, incomplete or unavailable | Apply remains unavailable. Keep that original preview's diagnostic and handle; a transport failure or missing result does not authorize another POST with a new key. |
| Tags appear only as Last observed | They are historical labels for an unmanaged retained repository. Reconfigure explicitly to create current intent; do not overwrite the snapshot as if it were configuration. |
| Repository disabled/removed but still listed under Archived | Expected: configuration changes do not purge archived publications or immediately prune retained revisions. |
| Interrupted/failed receipt with unknown or installed_unconfirmed outcome | Read the original protected application outcome with its original key. Preserve pending/history evidence; never infer rollback or retry Apply to find out. |
| Supported JSON rejects a field | It accepts only the complete supported editable projection. No TOML, protected value, placeholder, path override or unknown field is accepted. Correct the draft without weakening server validation. |
| Private outcome limit or pending marker blocks Apply | Preserve all original evidence for privileged operator review. The browser has no cleanup, rollback or quota-reset action. |

The local intent diff is not a protected-file backup. Server reconstruction
preserves protected values but canonicalizes comments and formatting. Never share
draft JSON or raw configuration in diagnostics; safe codes and original handles
are enough to identify the failed boundary.

## Repository details

Follow [repository details](repository-details.md) for exact selection, evidence
classes and consumer locator bases. These reads neither recover a publication nor
start verification or refresh work.

| Problem | Meaning and safe next step |
| --- | --- |
| Exact publication unavailable / HTTP404 | The selected pair is not retained, including after prune, purge or same-SHA repair. Keep its full SHA and publication ID. Select current explicitly only if you intend to inspect different content; there is no latest fallback. |
| Current changed while an older publication is selected | The selected retained pair remains the publication-panel identity. Compare current separately or choose it explicitly. Do not attach its sizes, card or integrity to the older tree. |
| Manifest/files available but technical or card panel refuses | Authoritative metadata and supplemental evidence are separate. Preserve the classified panel error; malformed or unsafe adjuncts must not be repaired by a GET. Missing observations do not erase a valid manifest. |
| Manifest digest unavailable | Its exact card-read provenance was unavailable or refused. Do not hash browser-formatted or HTTP JSON and call that the immutable manifest-file digest. |
| Whole manifest too large / unsafe integer / HFAPI005 / HTTP413 | Local file-table paging does not reduce the whole-artifact read. Keep the explicit refusal and use existing bounded metadata/consumer procedures; never accept rounded sizes or a truncated manifest. |
| Integrity is unverified despite complete technical metadata | Observations and publication-time checks do not establish fresh offline verification. Use exact selected-publication evidence and the separately authorized verification workflow. |
| Invalid detail bookmark | Correct the type/namespace/name path and optional complete SHA/publication pair. Only six fixed tabs and bounded fragment fields are supported; query strings and arbitrary paths remain refused. |
| Activity has no matching loaded report | Its history is explicitly bounded and archive-wide. Absence from loaded history is not proof that no work occurred. Preserve original operation handles and use the recovery workflow if observing existing work. |

Reconnect invalidates old private evidence even if the new session has the same
subject or archive. A failed or superseded read cannot establish a new selection's
contents. Do not delete metadata or weaken authentication to make a detail page
appear available.

## Archived README display

Check the selected SHA/publication pair and capture state in Overview. A missing
capture differs from a captured absent README; unsafe, unsupported, oversize or
failed capture has no body. Reopening the view never captures data. Use the
[explicit writer refresh](readme-cards.md#refresh-existing-publications) only with
authority for a deliberately new operation, retaining its original key/handle.

If formatted rendering refuses its smaller work budget, **Sanitized source**
can still show the verified derivative within the existing card limit. It is not
the original README and cannot restore withheld unsafe text. A card failure is
local; other tabs and operation recovery remain usable. A pruned or repaired-away
selection stays unavailable rather than switching to current. Media placeholders
and blocked link targets are expected safety behavior; do not disable CSP, add
a proxy or loosen capture rules to make upstream HTML or images appear.

## Validation or Apply rejected with HFAPI010

Keep the draft and check that the browser's public origin matches the configured
Basic origin. The current UI preserves that Origin on same-origin JSON POSTs;
operators must serve the matching selected release's indexed assets. A stale
client can fail validation in Firefox even when reads work. Preserve any original
operation handle before reconnecting or reloading. Do not relax Origin checks,
add a Caddy authentication gate or resubmit an uncertain Apply. See
[configuration recovery](configuration-and-tags.md#observe-an-interrupted-application).

## Schedule, observer and journal diagnostics

| Problem | Meaning and safe next step |
| --- | --- |
| Schedule or observer denied on guarded rootless | Expected for the current unproved system-manager binding. Retain the denial; do not choose a user manager or operate on same-name user units. |
| Native host-effect labels or receipt unavailable | Keep existing read/configuration use. A host administrator must provision the exact optional version2 labels, original host-action lock and fresh receipt/index; a true policy bit alone cannot supply them. |
| Native schedule allowed but observer stop reports profile-unproved | Check the optional fixed `50-hfcache-observer.conf` binding, effective manager context and dedicated scheduled-state label. Default units and journal stream context cannot attest the live SDK domain; init_t is not a supported signal target. Preserve the real running/inactive fact and original handle; do not grant init_t signals, choose an unconfined context or relabel automatically. |
| Verification timer reports linked and inactive | Immutable unit symlinks can produce linked without calendar enablement. Preserve the exact installed state and verify no enablement links; do not remove unit links or enable the timer to alter the display. |
| Legacy schedule/observer exclusion refuses | Preserve the old policy and admitted handles. Activation needs a safely absent policy or both strict legacy host-control bits false, plus independently proven quiescence of older privileged calls. Do not rewrite old source/index provenance or bypass the gate. |
| Schedule revision changed | Read the installed schedule again and deliberately review a new change. Do not overwrite concurrent edits or treat an old preview as authority. |
| File changed but manager state unconfirmed | Observe the original keyed host outcome. Preserve backups and pending evidence; do not replay reload/restart, reset or a replacement POST automatically. |
| Original observer binding changed | The requested original process is no longer proved. Refuse stop rather than signal a replacement invocation or numeric PID. Observe accepted backend work by its own original handle. |
| Observer stopped but job still running | Expected: client observation and server execution have separate lifetimes. Stop observation never cancels accepted API/worker work. |
| Journal gap, truncation or expired cursor | Read a deliberately new bounded page if needed. Logs are incomplete diagnostics, never completion evidence or authority for a command. |
| Private host history quota or pending marker blocks effects | Preserve the complete records and original lock inode. No GET, UI reset or receipt expiry deletes uncertain evidence. |
