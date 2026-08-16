# Using the Cockpit plugin

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
| `20` | Refused as unsafe; nothing changed |
| `30` | Sync completed with per-repository failures; read the run report |
| `40` | Integrity finding — prominent and persistent, linking the repair flow |
| `50` | Retention or repair failed; the UI points at `recover --dry-run` |

**"Busy" is not a failure.** One mutating command runs at a time across the
whole archive — sync, verify, prune, purge, repair, and recover share a single
lock. `HFMNT010` renders as a plain busy notice naming the holder. Wait it
out (a first sync of a large repository legitimately takes hours); never
remove the lock.

**Unit runs versus page-spawned runs.** A full sync and a full verification
run as the shipped units and survive your browser (`CP-04`). Three
operations are spawned from the page as transient systemd units
(docs/cockpit.md §2): closing the tab detaches your view — the run itself
continues, and a mutating run's outcome lands in its run report — but the
final result envelope is lost to the page, so the UI states the consequence
before starting each and surfaces reconciliation after a detach:

| Page-spawned run | Why a closed tab is safe |
| --- | --- |
| Sync selected repositories | The run continues without the page; if it does stop early, interruption is a designed crash shape — per-repository transactions, resumable downloads — and reconciliation surfaces afterwards |
| Verify one revision | Read-only; an interrupted read changes nothing |
| Repair | Its transaction reconciles like any other; `recover` describes it |

## Overview

The archive's health from `status --json`, with a Refresh button:

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
  probes); the named checks render in order with pass/fail/skipped
  outcomes.
- **Version** — application, Python, `huggingface_hub`, transfer backend.

## Sync

**Synchronization** shows live state for `hfcache-sync.service` (with its
last result and exit status) and `hfcache-sync.timer` (scheduled or paused,
next and last elapse), polled every few seconds.

- **Sync now** starts `hfcache-sync.service` — the production unit, same
  sandbox, identity, and journal as the nightly timer. While a run is
  active the button is disabled: starting the unit again merges into the
  running sync rather than queueing a second one (a timer elapse mid-run
  does the same, by design).
- **Stop running sync** is `systemctl stop` behind a confirmation that
  states the consequences: everything already published stays published,
  partial downloads resume from the cache on the next run, and a
  **Reconciliation** card appears afterwards running `recover --dry-run` —
  applying an actionable plan lives on the Maintenance tab.
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

**Sync selected repositories** offers the enabled, managed repositories as
checkboxes and runs `sync TYPE:ID …` as a page-spawned transient unit —
keep the tab open to see the result; the confirmation states the
consequence. Output streams live, and the result envelope renders at the
end; after a detach or interruption the UI surfaces reconciliation.

**Live activity** during unit runs follows the journal: the latest event
per repository from the closed event vocabulary, plus the raw tail.
Progress is checkpoint-grained by design — the plugin does not invent
percentages the events do not carry.

## Repositories

`list --revisions --json`: every archived repository — including
**unmanaged** ones no longer in the configuration — with its current
commit, retained count, and current-revision size. Expanding a row lists
every retained revision: generation (current marked), the full 40-character
commit SHA (displayed in full precisely so it can be copied into the
verification and repair forms), file count, size, publication timestamp,
and per-revision verification state.

## Configuration

Two editing modes over one pipeline (`CP-11`), against
`/etc/hfcache/config.toml`:

- **Form mode** renders the schema: repository rows (id, type, revision —
  validated live, with abbreviated commit SHAs rejected just as the CLI
  would — enabled, declared dependencies, add/remove) and every global key
  with its documented constraint as the hint. Form mode serializes
  canonically and **does not preserve comments**; the generated header says
  when and by what the file was written.
- **Text mode** edits the document verbatim, for the operator who keeps
  comments.

**Validate candidate** writes the edited document to
`/etc/hfcache/.candidate.toml` (`0640 root:hfcache`, same directory as the
target so the final rename is atomic) and runs `config validate` against it
as the service identity. Validation errors map back onto the form fields
where they can, and always render verbatim. When the change adds or
retargets an enabled repository, a **sizing preview** runs `plan` against
the candidate — no lock taken, nothing mutated — and renders the resolved
commit, file count, and logical/new/publication bytes: the runbook's
mandatory step before enabling a repository, because the storage quota is
sized from these numbers.

**Install validated candidate** copies the current file to
`config.toml.bak` (the one retained predecessor), renames the candidate
into place atomically, re-validates the installed file, and displays the
configuration fingerprint — the value subsequent run reports carry.
**Discard candidate** abandons the attempt.

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
  reads no object bytes, always safe.
- **Full verification** — only through `hfcache-verify.service` (`CP-04`),
  behind a dialog noting that it shares the single application lock and
  will wait behind a legitimately long sync. Live journal activity renders
  while it runs; the last result and exit status are shown. Exit `40`
  means the archive may be corrupt — the UI links the repair flow and
  never offers to sync or prune from that state.
- **Verify one revision** — `verify --revision TYPE:ID@SHA` with the full
  40-character SHA enforced as you type; copy the SHA from the
  Repositories tab. Runs as a page-spawned transient unit; it is
  read-only, so an interrupted read changes nothing.
- **Quarterly timer** — display only (`CP-06`): the plugin shows
  `hfcache-verify.timer`'s state and why it ships disabled (its calendar
  must not overlap storage-side maintenance windows — an operator
  decision). There is no enable control; evaluate a calendar and enable it
  deliberately from a shell.

## Runs

The durable run reports under the archive's `runs/` directory, newest 50,
read as the service identity. Selecting one renders the report: command,
outcome, exit code, invocation mode, per-repository outcomes (status,
resolved commit, downloaded/reused/hashed bytes, publication generation),
and totals, with the raw JSON behind an expander. **Show journal trail**
joins the report's `run_id` to the persistent journal — the report is the
authority for what a run did; the journal says what happened along the way.

## Maintenance

**Retention (prune)** and **Recovery (recover)** share one shape: **Dry
run** first, always safe; **Apply** stays disabled until a dry run in this
session came back clean, and its confirmation states the operation's own
guarantee — a failed prune leaves more data rather than less; recovery is
idempotent, never guesses, and never deletes data it cannot explain.
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
