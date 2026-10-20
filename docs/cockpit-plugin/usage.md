# Using the Cockpit plugin

The selected rootless deployment remains [guarded/read-only](../deployment-status.md).
System-bus writer/timer controls are masked and must refuse, even with administrative
access; no user-manager redirect exists. API-based workload controls remain subject
to the host guard and live-storage acceptance. The fixed rootless client receives
its API-only Podman secret as a file; the browser and host transient unit receive
no bearer or Hub source.

## Opening it, and what access means

Log in to Cockpit and open **Tools → hfcache**. Mutating anything requires
**administrative access** — the toggle in Cockpit's top bar. With it, the
plugin performs privileged work through Cockpit's superuser bridge and runs
every CLI command as the `hfcache` service identity, never as root
(`CP-03`). Without it the page is read-only: the configuration is
`0640 root:hfcache` and unreadable by design, and the plugin has no side
channel — controls fail closed and say why.

## How to read the plugin

**Every action is a runbook command.** Buttons start the shipped systemd
units or run the installed CLI with `--json`; dialogs and captions name the
exact command or unit, so anything the plugin does you can reproduce — and
script — from a shell ([`operations.md`](../operations.md)).

**Alerts carry the CLI's exit code**, and each code means one thing:

| Exit | Meaning in the UI |
| --- | --- |
| `0` | Success; warnings, if any, listed with their codes and runbook guidance |
| `10` | Invalid input or configuration; errors map onto the offending form fields |
| `20` | Safety/storage/observation refusal; inspect classified evidence and any retained handles, never assume nothing changed |
| `30` | Sync completed with per-repository failures; read the run report |
| `40` | Integrity finding — prominent and persistent, linking the repair flow |
| `50` | Retention or repair failed; inspect exact evidence and the supervised recovery runbook |

**"Busy" is not a failure.** One mutating command runs at a time across the
whole archive — sync, verify, prune, purge, repair, and recover share a single
lock. `HFMNT010` renders as a plain busy notice naming the holder. A legitimate active sync can take hours. The permanent read-only guard may
also intentionally hold the lock; waiting does not grant authority to release it.
Never remove the lock.

**Manual jobs and scheduled observers.** Full and selected jobs use the same
service-identity transient REST client, with original operation recovery.
The server owns accepted work. Closing a tab or stopping its client ends the view,
not execution. Keep the displayed idempotency key and operation ID: use
`operations lookup -- KEY` / `operations wait -- ID` through the same API authority to
reconnect. Timeout, missing history and interrupted execution are distinct
classified uncertainty; never submit a new key or run recovery automatically.

**Original operations** stays above the tabs. For keyed commands submitted through
the page's API client, it records the original key in this browser tab's session
storage before starting the submit process. Tab changes and reloads preserve
validated records; closing the browser session or clearing storage can lose them.
An unresolved record blocks another keyed submission on that host. Use **Look up
original key**, then **Observe original operation** when its ID is known. These
controls authenticate and observe the original work; neither resubmits nor cancels
it. Missing or expired history preserves uncertainty and the original handles.
After reload, retained terminal summaries are unverified metadata. Observe the
original authenticated result before another submission; a stored success label
alone cannot resolve uncertainty or restore Apply readiness.

Recovery records are limited to 32 records and 64 KiB of safe metadata: action,
key/ID, authority scope and a terminal summary. They contain no tokens, raw
configuration, request bodies or logs. Corrupt, unavailable or full storage blocks
submissions. Unresolved records are never evicted; only conclusive terminal
summaries can leave storage when capacity requires room. If a later storage write
fails, retain the identities still displayed in memory before closing the page.

The authority display comes from authenticated `client describe`, not a browser
endpoint setting. It shows the selected profile fingerprint, endpoint, credential
class, archive UUID and current server instance. An unconfirmed UUID stays
unconfirmed and blocks job submission and saved observation. A changed host,
profile, endpoint, credential class or archive identity blocks following old
handles. The client rechecks the expected authority in the same process before
submission or lookup/wait. A server restart alone does not replace an original
operation's identity when its validated authority still matches.

Copy recovery commands from **Original operations** on the recorded host. They
use the fixed rootless launcher, service identity, selected client settings/socket
and `--expected-client-scope`; quoted handles follow `--`, so a leading `-` or `~`
remains argument data. Do not replace a failed lookup with a new submission key.
The installed full-service controls above remain separate from this page's keyed
client registry.

Progress is bounded sequenced operation information, not invented checkpoint or
byte completion. A strict terminal Envelope determines the outcome. The page
retains validated recovery handles independently of dropped display lines and
reports event gaps. Oversized/malformed terminal output is an observation failure,
not a fabricated successful result.

## Overview

The archive's health from `--json status`, with a Refresh button:

- **Warnings** — any coded warnings on the envelope, each with its runbook
  response inline.
- **Archive health** — reachability, free space against the configured
  reserve, unfinished transactions (with a pointer to Maintenance),
  verification degradation, last full verification, deferred cleanup, and
  unknown entries (preserved, never deleted), plus the archive identity and
  root.
- **Findings** — staging and quarantine observations with age and
  staleness.
- **Repositories** — everything configured or archived: type,
  enabled/disabled and unmanaged markers, current commit (full SHA on
  hover), retained revision count, last run status, verification state.
- **Doctor** — on demand, read-only or full (the full run includes write
  probes); both modes can contact the Hub and persist control receipts. Full
  probing needs writer/storage approval; the named checks render in order with pass/fail/skipped
  outcomes.
- **Version** — application, Python, `huggingface_hub`, transfer backend.

## Sync

These service/schedule controls use the fixed system manager. They remain blocked
on the selected rootless installation; the following describes their mechanism,
not permission to unmask/enable them or redirect to the user manager.

**Scheduled sync observer** shows live state for `hfcache-sync.service` and
`hfcache-sync.timer`, polled every few seconds. Their exit status and journals
describe scheduled observation, never the outcome of a manual job.

- **Sync now** submits REST-backed CLI `sync` after fresh protected host permission
  checks. It retains the original key/receipt and displays server events/results.
  **Detach display** ends display updates; original operation recovery remains
  above the tabs. It never cancels execution or permits uncertain resubmission.
- **Stop scheduled sync observation** requires explicit permission and positive
  proof of the fixed observation-only service binding. It stops only that client. Its
  confirmation says accepted server work may continue and the pending recovery
  handle is preserved. It neither cancels execution nor starts recovery; reconnect
  through operation lookup/wait. Actual executor drain remains an operator action.
- **Pause / Resume schedule** stops or starts the timer only —
  `hfcache.target` and the archive mount are untouched (`CP-05`). A
  `Persistent=true` timer whose calendar elapsed while paused fires once on
  resume; the dialog says so.

**Schedule** edits the timer's calendar as a managed drop-in
(`50-cockpit.conf`) — the shipped unit file is never edited (`CP-12`). The
card shows the shipped schedule (`02:00` local with a randomized delay),
whether an override is active, and the timer's semantics. Enter an
`OnCalendar=` expression (and optionally `RandomizedDelaySec=`), then
**Check calendar** — `systemd-analyze calendar` renders the normalized form
and next elapse, and editing the expression invalidates the check. **Apply
override** is enabled only after a successful check; it writes the drop-in,
reloads systemd, and restarts the timer if it was active. **Reset to
shipped schedule** removes the override the same way.

If a file change completes before a later manager failure, preserve the original
error and use **Inspect changed schedule**, then **Acknowledge inspected schedule**
only after the captured stored bytes and fixed timer match. Tab changes retain
that uncertainty. Inspection and acknowledgement perform no reload or restart and
do not prove the effective calendar; resolve manager application through the
operator runbook before claiming the earlier schedule change succeeded.

**Sync selected repositories** offers the enabled, managed repositories as
checkboxes and runs `sync TYPE:ID …` as a page-spawned transient unit —
keep the tab open to see the result; the confirmation states the
consequence. Output streams live, and the result envelope renders at the
end. If observation is lost, retain the displayed handles and reconnect; do not
infer execution stopped or automatically reconcile.

**Host restrictions** above the tabs reports fresh trusted deployment evidence.
Missing or unsafe administrator policy, mixed artifacts or unknown host facts
deny effects. Archive, Hub-capable/control jobs, configuration, schedule and
observer permissions are separate; absence of a guard or mask grants none.
Both Doctor modes contact the Hub and write receipts; full Doctor also performs
archive write probes. Ordinary metadata and synchronous validation remain
distinct. Source fixtures do not establish installed workload acceptance.

**Live activity** displays bounded CLI operation events and unit journal
diagnostics. It reports only emitted sequence/kind/message and retention gaps;
it does not invent per-repository phases, checkpoints or byte percentages. Unit
active state and log lines are observation hints, not terminal results.

## Repositories

`--json list --revisions`: every archived repository — including
**unmanaged** ones no longer in the configuration — with its current
commit, retained count, and current-revision size. The repository name opens
its type-aware Hugging Face page in a new tab; this browser link carries no
archive credential. Expanding a row lists every retained revision: generation
(current marked), the full 40-character commit SHA (displayed in full precisely
so it can be copied into the verification and repair forms), file count, size,
publication timestamp, and per-revision verification state.

## Configuration

Two editing modes over one pipeline (`CP-11`), against
`/etc/hfcache/config.toml`:

For private/gated scope, `hub.token_mode="required"` remains the explicit
opt-in. Candidate syntax validation resolves no credential and separately reports
installed-authority compatibility. Compatible planning/installed validation use
the daemon's authorized Hub source; the transient client receives only the named
API credential `hfcache.api`. Install/rotate Hub credentials through the operator
runbook, never through this page. Candidate planning can contact the Hub and
creates receipt history; candidate syntax validation resolves no Hub credential
and creates no receipt. API credentials are separate and never enter
browser state or command arguments.

- **Form mode** renders the schema: repository rows (id, type, revision —
  validated live, with abbreviated commit SHAs rejected just as the CLI
  would — enabled, tags, declared dependencies, add/remove) and every global key
  with its documented constraint as the hint. Form mode serializes
  canonically and **does not preserve comments**; the generated header says
  when and by what the file was written.
- **Text mode** edits the document verbatim, for the operator who keeps
  comments.

Enter comma-separated tags in repository rows or add suggestions from existing
configured labels. The list is optional, applies to models and datasets, and has
no hierarchy or download/retention effect. Form serialization trims outer ASCII
spaces, lowercases ASCII letters, deduplicates and sorts labels. The backend
validates the same grammar and limits. Tags survive enable/disable and form/text
switching; a tag-only edit needs no sizing preview. See [tag rules](../configuration.md#6-repositories).

**Validate candidate** writes exact content to the fixed candidate path with
`0640 root:hfcache`, then invokes the service-identity API client. Every pipeline
command takes the retained root configuration flock and compares exact candidate
and loaded installed-base bytes. An external edit requires reload/revalidation;
form/text changes invalidate earlier readiness. Server validity, installed
compatibility and required preview success are displayed separately.

Added/retargeted enabled repositories require a successful compatible candidate
sizing preview before installation. Failed/malformed/uncertain preview does not
unlock install. Syntax-valid incompatible or unknown authority also blocks
plugin install: review the mismatch field names and use the manual privileged
install/backup, required daemon restart and compatible-preview procedure. The
page never redirects daemon credentials to proposed authority.

**Install validated candidate** rechecks exact candidate/base content and
readiness under the config flock, preserves `config.toml.bak`, fsyncs and atomically
renames. It then validates installed policy through the API and requires the exact
expected operational fingerprint plus exact installed bytes under the retained
config lock before showing success. A tag-only change has the same policy hash
but still fails exact-content confirmation. A confirmation failure means the
installed state is unconfirmed; it does not prove the old file remains or trigger
a silent rollback. **Discard candidate** abandons that proposal, never deletes
operation evidence or the retained config lock.
The editor retains its captured draft/base, stage results and original cause in
application memory across tab changes. A valid failed API result displays its
original code even when it has no candidate assessment. Installation readiness
never follows from a failed request.

A lost write/install acknowledgement disables Validate, Install and Discard.
**Inspect captured configuration** compares the four fixed files under the
original lock without creating files. Matching staged candidate and installed
base permit explicit **Revalidate captured candidate**, which skips the write.
An uncertain install requires matching installed candidate and predecessor,
**Confirm captured installation**, then **Acknowledge confirmed installation**.
The original failure remains available during reconciliation. Absent, changed or
unknown files require operator review; inspection never installs, rolls back or
cleans up. A full page reload does not adopt a pre-existing candidate by its name.
A fresh installed-file read alone cannot resolve uncertainty.
Loading the editor itself takes the root config flock and checks bounded no-follow
file access and ownership/mode; it never reads a credential source.
Candidate readiness, confirmation and acknowledgement also require the captured
client authority and administrative session to remain current. A changed or
unavailable authority invalidates readiness while preserving the draft, original
preview handle and uncertainty; it does not adopt a result from another endpoint.

New policy affects future admissions. Existing operations retain their admitted
snapshot/fingerprint; stale queued mutations refuse safely under the server lock.
Installing a config does not cancel accepted work.

To add a repository: form mode → **Add repository** → fill in
`organization/name`, type, and revision → **Validate candidate** → review
the sizing preview → **Install** → optionally sync just that repository
from the Sync tab. Removing a repository never deletes its archive: the
revisions remain and report as unmanaged.

## Verification

Ordered by escalation, and the estimate comes first deliberately:

- **Estimate** — `verify --estimate`: repositories, revisions, unique
  objects and bytes, estimated duration at the measured throughput, and
  whether the window would overlap storage maintenance. Takes no lock,
  reads no payload bytes and persists no report/receipt. It is a bounded metadata
  read under the installation's access restrictions, not an integrity check.
- **Full verification** — REST-backed CLI `verify --full` (`CP-04`),
  with the same original-key recovery as sync and fresh archive permission.
  The server's private offline verifier holds the single application lock.
  Bounded events and the exact terminal Envelope describe its outcome. Exit `40`
  means the archive may be corrupt — the UI links the repair flow and
  never offers to sync or prune from that state.
- **Verify one revision** — `verify --revision TYPE:ID@SHA` with the full
  40-character SHA enforced as you type; copy the SHA from the
  Repositories tab. Its transient client observes the isolated server verifier,
  which locks hashing and report/catalog persistence. Stopping observation does
  not cancel that work or prove it changed nothing.
- **Quarterly timer** — display only (`CP-06`): the plugin shows
  `hfcache-verify.timer`'s state and why it ships disabled (its calendar
  must not overlap storage-side maintenance windows — an operator
  decision). There is no enable control; evaluate a calendar and enable it
  only after separate calendar/workload approval; the selected deployment keeps it
  disabled.

## Runs

The durable run reports under the archive's `runs/` directory, newest 50,
read through privileged `runuser -u hfcache -- ls`/`cat` on
`/srv/hfcache/runs`. This host-local exception requires the writer archive mount;
it is not a remote API report reader. Journal browsing is also local. Selecting
one renders the report: command,
outcome, exit code, invocation mode, per-repository outcomes (status,
resolved commit, downloaded/reused/hashed bytes, publication generation),
and totals, with the raw JSON behind an expander. **Show journal trail**
joins the report's `run_id` to the persistent journal — the report is the
authority for what a run did; the journal says what happened along the way.

## Maintenance

**Retention (prune)** and **Recovery (recover)** share one shape: **Dry
run** first: previews read archive metadata and persist API receipt/event/result
history. They remain subject to access/acceptance restrictions and grant no later
apply authority. **Apply** stays disabled until a dry run in this
session came back clean under the same current client authority and connection;
it still resolves fresh locked domain proof, and its confirmation states the operation's own
guarantee — a failed prune leaves more data rather than less; recovery is
idempotent, never guesses, and never deletes data it cannot explain.
Confirming Apply consumes that preview synchronously. A submit/observation error
blocks a second Apply even when no applied Envelope arrived and the old dry run
was successful. Preserve the original record and observe it before another
deliberate submission; switching tabs does not clear this registry restriction.
Blocked recovery states render with their `HFTXN` codes; they stop every
mutating command until resolved.

**Repair a damaged revision** is the one explicit republish, for a revision
a verification found damaged: `repair TYPE:ID@SHA` (full SHA enforced;
copy it from the verification finding) with an optional reason recorded to
the audit trail. The revision is re-downloaded in isolation and verified
against the *original* manifest — if any expected digest differs, repair
stops without switching, and the superseded instance stays readable through
the grace period. It runs as a page-spawned transient unit and shares the
single archive lock.
