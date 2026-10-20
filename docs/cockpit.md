# Cockpit administration contract

The plugin is a static Cockpit package for a writer host. Its fixed launcher uses
`/usr/local/libexec/hfcache-client`, `/etc/hfcache/client.toml` and the rootless
API socket `/run/hfcache/api/api.sock`. It is a browser client of strict CLI
Envelopes and host systemd/configuration interfaces, with one explicit host-local
archive report-reading exception. It adds no daemon or application dependency.
See [installation and usage](cockpit-plugin/README.md).

The selected installation remains [guarded/read-only](deployment-status.md).
Legacy sync/verify/timer controls use the system bus and remain masked; they must
refuse, never redirect to same-named user units. CLI-based jobs remain subject to
the retained guard and NAS restrictions. No installed browser/PAM acceptance is
implied by repository tests. Native services are separately supported, but this
shipped plugin has no native launcher selector or host ImportCredential path.

Require bounded strict schema-1 terminal Envelopes. Separately validated bounded
CLI progress and safety handles may render and support reconnection, never
inventing domain outcome/checkpoint/byte percentage. Page closure/client stop
ends observation; it does not cancel accepted work or prove recovery safe.
HFAPI013/015/019/020 or `work_may_continue` retain uncertainty and offer exact
lookup/wait, without automatic recover or replay.
Bound terminal JSON to 16 MiB, a partial progress line to 8 KiB and retained
diagnostics/progress to 64 KiB. Explicitly drop oversized progress while preserving
independent validated handles and the terminal collector. Oversized terminal
output refuses observation without cancelling accepted work.
Each display push is bounded to 256 lines, and retained activity feeds additionally
cap at 200 whole lines within 64 KiB. UTF-8 counting handles split surrogate pairs;
display truncation never turns a partial line into a plausible handle/event.

Under persistent root-owned `0600` `/etc/hfcache/.configuration.lock`, compare
exact candidate content and the installed base bytes through validation/required
preview and before installation. Candidate bytes are bounded inert stdin, never
shell code. Edits invalidate readiness. Syntax validity, compatible authority,
preview success and exact installed content and operational fingerprint confirmation are separate gates;
incompatible/unknown authority blocks plugin installation and explains the manual
operator install/restart/compatible-preview sequence. Failed preview/confirmation
cannot render success. Preserve atomic backup/install, service identity and
`0640 root:hfcache`. New policy changes future admissions, never an admitted
snapshot; the server refuses stale queued mutations.

## Integration repair requirements

The following requirements amend the presentation and recovery contract. Existing
implementation gaps require correction before source acceptance; they do not
establish installed browser/PAM acceptance. See [decision 134](adr/decision-134.md).

Preserve classified terminal Envelopes independently of bridge/process errors.
Missing terminal output must retain validated Cockpit problem, process status or
signal, interrupted stage and original operation handles. Never diagnose an API
crash from the word `reconnected`. General failed validation Envelopes remain
original request failures; they need not contain a candidate assessment.

Read connections must recover finitely after close, reject stale generations and
mark failed refreshes unavailable. Connection recovery never repeats a host write,
unit mutation, candidate pipeline or job submission. Retain uncertain candidate
write/install evidence and use only guarded exact-content read reconciliation.

Keep operation handles outside unmounted tabs. Capture a validated original key
before transmission; store only bounded nonsecret, authority-scoped session
recovery metadata. Unresolved submission or Apply blocks another submission.
Before starting any keyed client process, record the generated original key in a
bounded validated session registry outside Tabs, then pass it with the existing
global CLI option. Storage failure/corruption or any unresolved operation on the
same host refuses another submission. Keep at most 32 records in 64 KiB, evicting
only terminal metadata; unresolved records cannot be evicted to make room.
Retain only safe action/route, key/ID, timestamps, state and validated
host/fixed-client-profile/endpoint/credential-class/archive scope metadata; never
TOML, tokens, raw logs, arbitrary argv or response bodies. Explicit client authority
metadata derives from validated management settings and authenticated read
responses, not a browser-selected endpoint. Unknown/changed authority cannot
resume saved observations or silently rebind an unresolved record.

The fixed client exposes `client describe`, an authenticated read-only seven-field
metadata Envelope. It supplies public fingerprints, endpoint, credential class,
archive UUID (possibly unconfirmed) and diagnostic server instance identity.
Every submission and original-handle lookup refreshes this evidence; the actual
CLI invocation compares the original `--expected-client-scope` fingerprint using
its own freshly authenticated settings/capability/version observations before
POST or handle GET. The option compares authority; it never selects a target or
credential. Server restart alone does not change an otherwise identical scope.
Unknown archive UUID blocks jobs and saved recovery. Plain validation remains a
synchronous read and creates no operation record.

Capture command, candidate and authority options before asynchronous proof or
display callbacks. Dispatch accepts only the plugin's closed command/argument
forms; an unrecognized command is never inferred to be a safe read. Global CLI
option prefixes, local/bootstrap validation and out-of-scope mutations refuse
before a client process starts. This does not change the CLI's own surface.

Recover through authenticated lookup/wait of the original operation; missing
history does not prove nonexecution. No replay, cancel or cleanup follows an
uncertain response.
Restored summaries are metadata, never terminal result bodies, configuration
proposals or Apply readiness. A restored terminal summary is unverified: only
authenticated original observation can confirm it and unblock another submission.
Missing history keeps that uncertainty; valid-looking browser metadata alone
cannot resolve an operation. The root recovery panel survives tab unmounts.
Browser-session storage may disappear when the session ends; keep the displayed
original handles for operator review. A quota failure after transmission retains
the known key/ID in application memory and visibly blocks further submissions.

Manual full jobs follow [decision135](adr/decision-135.md)'s shared REST client
path and explicit trusted host permissions. REST report browsing still requires
the separately implemented CP-01/09 amendment; its exception below remains current.
Neither amendment permits workloads on guarded/unknown profiles,
changes to host guards or schedules during source implementation, or a
user-manager fallback. All failed read
Envelopes must render their codes before success-only fields are accessed.

## 1. Rules

| ID | Rule |
| --- | --- |
| `CP-01` | The plugin invokes the installed CLI and systemd; it never reads or writes archive state directly and never re-implements resolution, validation, verification, or retention logic. One read-only exception: §4's run-report browsing |
| `CP-02` | Every CLI invocation passes `--json`; command outcomes require a bounded strict schema-1 Envelope. Refuse unknown versions. Separately validated bounded progress and recovery handles may render/reconnect; stderr never grants domain authority or fabricates outcome/checkpoints/percentages |
| `CP-03` | Mutating actions require Cockpit administrative access. The CLI runs as the service identity inside a transient systemd unit (§2), never as root |
| `CP-04` | Manual full sync and verification use fixed REST-backed CLI `sync` / `verify --full`, with original keyed receipts/results and explicit permitted-profile checks. Scheduled observers remain separate host services; their exit state is not manual operation outcome. The page never starts sync/verify services |
| `CP-05` | Pausing or resuming the schedule operates on `hfcache-sync.timer` only. The plugin never stops, starts, enables, or disables `hfcache.target` — stopping it unmounts `/srv/hfcache` ([scheduling](operations.md#scheduling-and-capacity)) |
| `CP-06` | The plugin never enables `hfcache-verify.timer`. It displays the timer's state and the reason it is disabled (deployment calendar approval). Sync timer controls use only the fixed system manager; the selected profile blocks them |
| `CP-07` | `archive init`, including inspection, is outside the plugin surface (`FS-21`); an existing archive must never be initialized again |
| `CP-08` | No credential surface: the page never reads credentials or accepts tokens. Transient clients receive only named API `hfcache.api` inside the fixed rootless client, never Hub authority or browser/environment/argument bearers. Only safe source descriptions render (`docs/security.md` T-07) |
| `CP-09` | The plugin never writes under `/srv/hfcache`. Its only direct read there is `runs/*.json`, performed as the service identity; every other statement about the archive comes from a CLI envelope |
| `CP-10` | One mutating command at a time (`AD-17`). `HFMNT010` renders as a benign busy state naming the holder, never as a failure; the plugin never removes or bypasses the lock |
| `CP-11` | Configuration changes use §6's root config flock and exact candidate/base guards, syntax-valid compatible server assessment, required successful preview, atomic install with `0640 root:hfcache` and predecessor retained, then exact installed-content and expected operational-fingerprint confirmation. Incompatible/unknown authority blocks plugin install |
| `CP-12` | Timer schedule changes are drop-ins under `/etc/systemd/system/hfcache-sync.timer.d/` (§7); shipped unit files are never edited, and calendar expressions are validated with `systemd-analyze calendar` before anything is written |
| `CP-13` | The plugin never weakens systemd hardening or SELinux and never advises doing so; a denial is diagnosed under the security contract or reported; safeguards remain enforced |
| `CP-14` | The node toolchain is build-time only. The plugin ships as static files; the application's closed runtime dependency set (`FW-03`) is untouched, and `cockpit/node_modules/` and `cockpit/dist/` are never committed |

Host schedule/observer controls remain fixed system-manager operations. The
selected rootless masks/guards prevent workload or schedule approval; moving a
manual action to REST cannot bypass them. Administrative access alone does not
lift these restrictions. Fresh read-only proof from the fixed helper and explicit
protected host policy gate effects at both adapter and UI boundaries. Missing,
unsafe, unknown or drifted proof refuses; absence of a guard/mask is not approval.

## 2. Privilege and identity

Cockpit authenticates against the host (PAM). Administrative sessions use its
superuser bridge for systemd/configuration work; the installed CLI runs as the
unprivileged `hfcache` service identity. The plugin adds no listener or credential
backend. API execution stays in the daemon/private worker, with the existing
archive, policy, lock and credential authority.

The selected rootless profile's fixed transient invocation is:

```text
systemd-run --quiet --wait --pipe --collect \
    --property=User=hfcache --property=Group=hfcache \
    --property=UMask=0027 --property=MemoryHigh=4G \
    -- /usr/local/libexec/hfcache-client \
    --client-config /etc/hfcache/client.toml \
    --api-socket /run/hfcache/api/api.sock --json <command>
```

The fixed launcher selects the protected immutable rootless client image and
mounts API-only named Podman authority; the page and host transient unit never
receive its bytes. Provision `hfcache.api` for the REST writer class, distinct
from daemon Hub `hf-token`, and install the separate client TOML pointing to its
mounted protected file. No host ImportCredential prerequisite remains. An absent/
unusable source fails closed; there is no anonymous Hub fallback. Never pass a
literal bearer, ambient token environment or token-file override through browser/
argv. The helper owns image/engine/secret policy, not the page.
Ordinary commands omit archive `--config`; candidate validate/plan alone adds the
fixed `/etc/hfcache/.candidate.toml` path for bounded local content upload (§6).

`UMask=0027` and `MemoryHigh=4G` bound the transient observer; they do not prove
that it executes or hardens archive work. The actual API/private-worker units own
that work. `--wait --pipe` retains CLI output and exit status, including classified
failure Envelopes; `--collect` avoids accumulating completed transient units.

Root bridge work is limited to installed unit/timer/drop-in control, journal
reads and the guarded configuration pipeline. The run-report browsing exception
uses `runuser -u hfcache -- ls` / `cat` through the privileged bridge for
`/srv/hfcache/runs/*.json` (`CP-09`). It requires this writer host and its archive
mount; it is not REST report browsing or a remote-reader path. Journal browsing
is also host-local. No Hub credential is involved.
Without administrative access the page presents permitted read-only systemd state
and explains why privileged actions are locked. It invents no archive side channel.

## 3. Operation surface

| UI operation | Mechanism | Contract |
| --- | --- | --- |
| Health dashboard | `--json status` — the six archive-health fields, free space against reserve, per-repository state | [status](operations.md#read-status-and-inventory) |
| Archived repositories and revisions | `--json list --revisions`, including `managed: false` entries; repository names link to their type-aware Hugging Face pages | `docs/cli.md` §2 |
| Sizing preview | `--json plan`, optionally against a candidate configuration (§6) | [planning](operations.md#plan-diagnose-and-synchronize) |
| Sync now (all repositories) | Fixed REST-backed CLI `sync`, one original key | `CP-04`; [sync](operations.md#plan-diagnose-and-synchronize) |
| Sync selected repositories | Page-spawned CLI `sync TYPE:ID …` (§5) | decision 89 |
| Detach manual observation | Detach display only; original registry remains | §5 |
| Stop scheduled sync observer | Fixed system `hfcache-sync.service` stop only with explicit permission and proven observer binding; accepted work may continue | §5 |
| Pause / resume schedule | `systemctl stop` / `systemctl start` on `hfcache-sync.timer` | `CP-05` |
| Live sync activity | Journal stream of the unit, §24 event vocabulary | §5 |
| Verify — estimate | CLI `verify --estimate` | `docs/cli.md` §2 |
| Verify — one revision | CLI `verify --revision TYPE:ID@SHA` | `docs/cli.md` §2 |
| Verify — full | Fixed REST-backed CLI `verify --full`, one original key | `CP-04` |
| Verification timer | Display state and reason only | `CP-06` |
| Doctor | CLI `doctor` / `doctor --read-only`, 17 named checks rendered in order | `docs/cli.md` §2 |
| Retention | CLI `prune --dry-run`, then `--apply` behind confirmation | `docs/cli.md` §2 |
| Recovery | CLI `recover --dry-run`, then `--apply`; blocked states shown with their `HFTXN` codes | [maintenance](operations.md#preview-and-apply-maintenance) |
| Repair | CLI `repair TYPE:ID@SHA --reason TEXT`, launched from a verification finding | `docs/cli.md` §2 |
| Version | CLI `version` | `docs/cli.md` §2 |
| Configuration | §6 pipeline | `docs/configuration.md` |
| Sync schedule | §7 drop-in | `packaging/systemd/hfcache-sync.timer` |
| Run reports | List and read `runs/*.json` as the service identity | `CP-09`; `docs/schemas.md` §6 |
| Warnings | `status` findings, each `HFWRN` code paired with its §8 runbook response as inline guidance | [warnings](operations.md#warnings) |

There is no publish operation, because the application has none: publication
is an atomic stage inside `sync`, and `repair` is the only command that
republishes (decision 89). The UI presents "Sync now" and renders published
state — publication ID, generation, timestamp, verification state — from
`list --revisions`.

Repository links are browser-only navigation to the canonical
`https://huggingface.co` web origin: models use `/<owner>/<name>` and datasets
use `/datasets/<owner>/<name>`. Each identifier segment is percent-encoded, and
the link opens in a new tab with no opener or referrer relationship. It carries
no Hub credential (`CP-08`) and remains available for unmanaged repositories,
whose configuration entry no longer exists (`AD-06`).

## 4. Envelope and error handling

Exit codes map to UI states, not to a generic error toast:

| Exit | UI state |
| --- | --- |
| `0` | Success; render `data`, surface `warnings[]` |
| `10` | Invocation or configuration problem; map `HFCFG`/`HFARG` codes onto the offending form fields where the UI owns the input |
| `20` | Safety/storage/observation refusal; inspect classified evidence. `HFMNT010` is benign busy; uncertainty never proves nothing changed |
| `30` | Partial failure; per-repository outcomes from the `RunReport` payload |
| `40` | Integrity finding: prominent, persistent, linking the repair flow; the UI never offers to sync or prune from this state ([failure handling](operations.md#diagnose-failures)) |
| `50` | Retention/repair failure; use retained evidence and the supervised recovery runbook |

The envelope is emitted even on failure, so the plugin never diagnoses by
parsing human text (`CP-02`). `warnings[]` and `errors[]` render with their
stable codes; the codes are the join key to the runbook guidance the UI
carries. Raw host stderr and rejection prose are withheld from browser display.
Only documented strictly validated
progress/recovery notices are interpreted for display/reconnection; domain
outcomes still require the terminal Envelope. HFAPI013/015/019/020 or
`data.work_may_continue=true` render as uncertain observation with retained handles,
never a claim of cancellation, nonexecution or automatic recovery authority.

Host-boundary failures use a bounded presentation model, separate from backend
HFAPI/domain codes. Preserve the known stage, allowlisted Cockpit `problem`,
validated process exit status/signal and original safe handles for both Error
instances and plain rejection objects. An unrecognized problem is identified as
unknown with its contents withheld. Do not invoke getters or stringify exceptions,
expose raw stderr, or infer API failure from `reconnected`. A valid nonzero terminal
Envelope remains the exact classified result even when its process rejects.
Successful installed confirmation additionally requires successful process/
postchecks and an unchanged administrative session. A valid negative confirmation
Envelope remains original failure evidence; it cannot confirm installation. Pre-transmission privilege refusal does not
invent a host change or job receipt; lost host-change acknowledgement remains
uncertain. Synchronous validation has no operation receipt.

D-Bus connections belong to the application lifetime. Close and supported
`superuser.changed`/`reconnect` transitions dispose listeners and invalidate the
cached client. A read makes at most two attempts with one 100 ms delay; each D-Bus
call has a 5 s timeout. Polls run sequentially, scheduling their next interval after
completion. Failed refreshes expose unavailable state and discard prior healthy
evidence. Old generations cannot restore it or enable controls. Privilege changes
invalidate candidate readiness while retaining the draft and existing failure
evidence. Mutations and entire candidate pipelines are never retried by connection
recovery. Multi-stage schedule changes stop at a session transition; they never
repeat writes or claim that a missing acknowledgement means nothing changed.

These CLI stderr forms alone become typed operation notices, after the 8 KiB
UTF-8 line bound and control-character checks. They are separate from journal
logfmt and never a terminal result:

| Line form | Typed display/reconnection value |
| --- | --- |
| `Idempotency key: KEY` or `Original idempotency key: KEY` | Safe nonsecret key, 1–128 ASCII characters from letters/digits/`._~+-` |
| `Operation: ID` with optional `; accepted work may continue` suffix | Exact 32-character lowercase hexadecimal operation ID |
| `[N] KIND: MESSAGE` | Positive safe-integer sequence; kind starts lowercase and uses at most 64 lowercase/digit/`_.-` characters; message remains plain text |
| `Event history gap; retained events start at N` | Positive safe-integer retained sequence, not invented missing events |
| `Accepted work may continue; reconnect using the retained handles` | Observation-continuation notice, never a domain outcome |

Reject malformed notices; unrecognized lines and terminal bodies are withheld
from activity display. Only validated notices/progress and fixed truncation
markers render; terminal collection remains independent. Keep validated
key/ID independently of log eviction. Reconnect commands keep handles as arguments,
not executable text, use `--` before positional values and quote copied keys so
even valid leading `-`/`~` characters remain data. Display
abort/callback failure detaches view updates without
closing the spawned process or cancelling server work.

## 5. Long-running operations and concurrency

Manual full sync/full verification use the same keyed transient REST observer as
selected sync and revision verification (`CP-04`). Exact server receipts/results
and events describe manual execution. Separately labeled scheduled services retain
their private handles through finite observation windows; timer elapses merge
into their active oneshot. Service state/journals describe only those observers.
The server owns accepted work;
closing a tab or stopping an observer never cancels it.

Before a keyed POST, the CLI prints its validated key; after acceptance it prints
the operation ID. The plugin retains those independently of bounded display logs
and offers authenticated `operations lookup -- KEY` / `operations wait -- ID` guidance.
A lost result, timeout, page closure or stopped client is uncertain observation,
not proof of execution failure/nonexecution. Never automatically submit another
key, invoke recovery, or infer that an archive lock is free. Use exact operation
history and the [executor drain/recovery runbook](recovery.md#preserve-four-kinds-of-authority).

The sync stop control stops only `hfcache-sync.service`'s observation. Its dialog
states that accepted server work may continue and that the pending handle is
preserved for lookup/observation. The UI must not promise cancellation, resumable
partial-download behavior or safe automatic recovery from this action. It never
stops the API/private verifier or lifecycle target on the user's behalf.

Progress is only the bounded validated sequence/kind/message emitted by the CLI,
with explicit event-retention gaps and mandatory safety handles. Do not infer
per-repository phases, checkpoint completion or byte percentages absent from that
stream. Installed-unit journal views remain bounded diagnostics, never authority
for a terminal result. Unknown progress lines are display-only and cannot change
an operation's outcome. The 8 KiB line/64 KiB retained-log bounds do not discard
validated recovery handles or prevent collection of the independent terminal
Envelope (maximum 16 MiB).

`is-active` for sync/verify services remains a useful observation hint, not the
single-writer authority. The server's bounded lane and archive flock decide
admission/execution. Busy/stale/error classifications remain visible; the plugin
never probes, removes or bypasses the lock. Full service drain and supervised
recovery remain operator procedures.

## 6. Configuration editing

Retain exact captured draft/base, stage acknowledgements and classified results
independently of installation readiness, in application memory only. A general
failed validation request need not contain assessment fields: render its original
Envelope without synthetic assessment or installation proposal. Strict successful
and recognized negative assessments retain their separate compatibility rules.
Publish validation evidence before starting any required keyed preview.
Required successful preview data must cover the exact requested repository set,
captured revisions and publication policy with valid resolved identities and
nonnegative sizing. Missing or inconsistent successful fields grant no proposal;
retain failed partial preview Envelopes separately. Omitted TOML repository fields
follow the backend defaults (`enabled = true`, `revision = "main"`, empty declared
dependencies) when rendering and deciding whether sizing is required.

Lost candidate-write or installation acknowledgement blocks another preparation,
installation or discard. Reconnect can perform only read-only fixed-path
inspection under the original configuration lock, comparing exact bytes without
overwriting/removing files or creating comparison artifacts. Matching, absent,
changed and unsafe/unknown observations remain distinct. A matching staged write
can be explicitly revalidated without writing it again. Lost install evidence
retains the expected bytes and predecessor; only exact guarded API confirmation
and explicit acknowledgement can confirm it. Fingerprint equality alone cannot.
A simple installed read or component remount never clears uncertainty. Full page
reload does not adopt a pre-existing candidate merely from its filename.


Candidate validation/planning upload bounded exact TOML text through the API;
the server never opens the candidate pathname or installs it. Root owns the
fixed candidate/install/backup paths on the Cockpit host. Candidate syntax/policy
validity does not prove installed-authority compatibility, credential availability
or preview readiness ([decision 119](adr/decision-119.md)).

Every pipeline command takes the persistent root-owned `0600`
`/etc/hfcache/.configuration.lock` flock. Compare the expected candidate and
loaded installed-base bytes while holding it; refuse changed content rather than
borrow earlier validation/preview. Hold the lock through that command and its
atomic changes. Each candidate/base document is at most 1 MiB of complete UTF-8
without NUL. Payloads travel as bounded inert stdin, never shell interpolation or
generic executable/path input. Retain the lock inode. The config directory is
root-owned and not group/world writable; installed/candidate/backup files must be
root-owned `0640 root:hfcache`, regular, single-link and not symlinks. The retained
lock is root-owned `0600`, regular, single-link and inode-checked after flock.
External root edits remain the trusted operator boundary; the flock serializes
cooperating plugin commands.
The fixed installed-config read uses the same flock/metadata/1 MiB checks and
no-follow file access before returning editor content.
Editing either form or text invalidates the browser's prior readiness.

The pipeline, in order (`CP-11`):

1. **Candidate.** Write exact edited content to `/etc/hfcache/.candidate.toml`,
   `0640 root:hfcache`, in the target directory. Retain the loaded installed bytes
   as the expected base; an external edit requires reload/revalidation.
2. **Assess.** As the service identity, run API-backed `config validate` with the
   fixed candidate path. Require strict schema-1 output, syntax validity and
   `authority_compatible=true` with valid installed policy. Report ordered
   mismatch field names without credential values. Valid incompatible/unknown
   authority remains valid syntax but blocks plugin installation.
3. **Preview when required.** Added/retargeted enabled repositories require a
   successful API-backed candidate `plan` under the same exact-content/base guard.
   Planning uses installed authority/credentials, cannot install policy and grants
   no later apply authority. Failed/malformed/uncertain preview leaves install
   disabled; edits invalidate a prior preview.
4. **Install.** Recheck exact candidate/base and readiness under the root flock.
   Preserve the predecessor at `/etc/hfcache/config.toml.bak`, `0640 root:hfcache`,
   fsync and atomically rename the candidate over `/etc/hfcache/config.toml`.
5. **Confirm.** Validate installed policy through the API, require a successful
   strict Envelope and the exact expected operational fingerprint. Under the retained
   root config flock, compare installed bytes with the validated candidate before
   and after API validation, without requiring the consumed candidate pathname.
   Withhold the bounded CLI response until byte postchecks pass and require
   successful completion of this confirmation process. Equal policy fingerprints
   alone never establish tag/document equality. Only then display
   success. Failed confirmation reports installed state as unconfirmed, preserves
   evidence and never claims the old file remains or silently rolls back.
   Install/confirmation errors remove readiness and require reloading the installed
   configuration before another candidate validation; installation may have
   completed even when its observer failed.

Authority changes require a privileged manual sequence: review mismatch fields,
install/backup the proposal outside this plugin, restart the daemon when startup
root/UUID authority changes (and any affected service settings), then obtain a
compatible validated preview before credential-bearing work. With broken installed
policy, candidate syntax may validate with unknown compatibility; that does not
unlock install/plan. The plugin never rewrites authority fields to match silently.

Form mode serializes canonical TOML and states that comments are not preserved;
text mode edits verbatim. Only schema-1 keys are offered, with no token field.
Repository rows offer a comma-separated `tags` control and existing configured-tag
suggestions (up to 64 sorted suggestions), with free entry and no registry. Form
serialization uses the backend's ASCII normalization grammar: outer spaces trim,
ASCII lowercase, sorted unique values, at most 64 raw entries and 128 characters
per raw value, with canonical length at most 64. Labels are flat and never change
file selection, retention or authorization; see [configuration](configuration.md#6-repositories).
Legacy omitted tags render as empty; toggling/removing/editing and form/text
switching preserve the current draft. Text-to-form parses the edited document;
form-to-text serializes that draft. Invalid tags block form serialization and
text candidates remain subject to backend validation. Tag-only edits need no sizing
preview. The server remains authoritative; direct malformed candidates refuse.

`maximum_revisions` supports 3/5 and default 3 without rewriting an explicit 5.
`token_mode=required` remains the explicit restricted-scope opt-in; candidate
syntax validation resolves no credential, while compatible planning/installed
validation use daemon-owned credentials. The transient client never imports Hub
credentials. AD-21's whole-archive authorization and expected-account checks remain.

The add-repository wizard uses the same assess → required preview → guarded
install → confirmation pipeline, then may offer selected sync. Removing a
repository never deletes its archive; retained publications become unmanaged.
Installed policy governs future admissions. Already-admitted operations keep their
fingerprint/snapshot, and stale queued mutations refuse under the server lock;
installation neither cancels work nor changes its receipt.

## 7. Sync schedule

Schedule changes are a drop-in, never an edit to the shipped unit
(`CP-12`):

```text
/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf
```

containing a `[Timer]` section that first clears the list-valued directive
and then sets the replacement (`OnCalendar=` on its own line, then
`OnCalendar=<expression>`), plus `RandomizedDelaySec=` when the operator
changes it. Before writing, the expression is validated with
`systemd-analyze calendar` and its normalized form and next elapse are shown.
After writing: `daemon-reload`, then a restart of the timer when it was
active. The UI warns before applying that a `Persistent=true` timer whose
calendar elapsed while it was stopped will fire on start.

The shipped timer's semantics are surfaced beside the editor, because they
are the contract the schedule lives in (`packaging/systemd/hfcache-sync.timer`;
[scheduling](operations.md#scheduling-and-capacity)): the calendar is site-local time deliberately;
`Persistent=true` replays an elapse missed while the host was down; an elapse
that arrives mid-run merges into the running sync and the day is skipped —
designed observation semantics (`AD-02`/`AD-03`), not a fault. Removing the
drop-in restores the shipped schedule; the UI offers that as "reset to
default".

## 8. Toolchain, layout, and gate

`cockpit/` uses the Cockpit starter kit, esbuild `build.js`, PatternFly and a
Makefile. Node and pnpm are build-time only. `package.json` pins the supported
Node/pnpm versions; the committed pnpm lock is installed frozen. The Makefile
finds pnpm on PATH or `$PNPM_HOME/bin` and places its Node beside it on PATH.
Source compiles into `cockpit/dist`; generated bundles and node_modules are not
committed. Static installation is root-owned `/usr/share/cockpit/hfcache`,
independent of the Python release. A development symlink under
`~/.local/share/cockpit/hfcache` shadows the installed copy for that user.

`scripts/check.sh` runs frozen install, ESLint, Stylelint, TypeScript, unit tests
and production build when the plugin toolchain is available. The plugin test
command also runs mounted React lifecycle tests in `/usr/bin/firefox`, using a
fresh isolated profile and owned loopback fixtures. Missing Firefox fails this
frontend gate; it is a development test prerequisite, not a shipped dependency. A loud skip on a
host without that toolchain is not plugin validation. Changes to this surface
require an actually executed plugin gate. See [development](development.md).

## 9. Testing

Plain modules test strict Envelopes, taxonomy/exit mapping, selectors, bounded
streams/recovery handles, fixed command/manager allowlists, calendar expressions,
TOML mapping and exact candidate/base/flock/confirmation behavior. Injected
process/filesystem adapters use disposable state, not installed units or NAS.
Mounted Firefox tests execute actual React components, hooks, error rendering and
API adapters with controlled Cockpit process/D-Bus/privilege boundaries. They cover
closed-client recovery, stale generations and session transitions. They do not
provide real Cockpit/PAM, rootless launcher or API acceptance.
Browser/PAM, privileged bridge, actual secret delivery, deployed candidate install,
SELinux/NFS and real drain/rollback require a separately authorized environment.
Repository tests do not assert that acceptance. The writer/archive is not a
corruption or browser-test fixture.

## 10. Version 1 non-goals

- Consumer/NAS administration, exports, snapshots, quotas or scrubs.
- Archive initialization, verification-calendar enablement or credential entry.
- Multiple writers/hosts or arbitrary executable/unit/tool dispatch.
- A translated catalog or bundled Cockpit/PAM/virtual-machine test environment.

## Deployment boundary

The fixed rootless launcher, file-mounted API-only secret and independent host
guard are the supported local integration. The server owns Hub and archive
execution; the private verifier owns actual offline verification. Host-local
reports/journal and system-bus controls retain their explicit limits above.
[Recorded acceptance](deployment-status.md) separates repository behavior from
unperformed browser/PAM, live NAS, other-host and workload checks.
