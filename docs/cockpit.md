# hfcache Cockpit Plugin Contract

| Field | Value |
| --- | --- |
| Status | Normative contract for implementation |
| Derived from | `docs/cli.md`, `docs/configuration.md`, `docs/operations.md`, `docs/security.md`, `docs/agents/environment.md`, `packaging/systemd/` |
| Work package | `CPT-001` |
| Source tree | `cockpit/` in this repository |
| Installed package | `/usr/share/cockpit/hfcache`; `~/.local/share/cockpit/hfcache` for development |
| Requirement IDs | `CP-01`–`CP-14` (citable, same convention as `AD-nn`/`FS-nn`) |

The plugin is a Cockpit package — `manifest.json` plus static HTML, JS, and
CSS — that gives the operator a browser UI over one deployed writer. It is a
*client* of the contracts this repository already has: the CLI's JSON
envelope, the configuration schema, and the shipped systemd units are its
entire API. The application remains CLI-only (`docs/cli.md` §1's own claim);
nothing the plugin does is anything an operator could not reproduce by hand
with the commands in `docs/operations.md`, and the UI displays the underlying
command wherever practical so the plugin teaches the runbook rather than
hiding it.

## 1. Rules

| ID | Rule |
| --- | --- |
| `CP-01` | The plugin invokes the installed CLI and systemd; it never reads or writes archive state directly and never re-implements resolution, validation, verification, or retention logic. One read-only exception: §4's run-report browsing |
| `CP-02` | Every CLI invocation passes `--json`; the envelope is the only parsed surface. An envelope `schema_version` other than `1` is refused with an upgrade message, never guessed at. Stderr is display-only |
| `CP-03` | Mutating actions require Cockpit administrative access. The CLI runs as the service identity, never as root |
| `CP-04` | A full sync and a full verification run only through `hfcache-sync.service` and `hfcache-verify.service` — never as page-spawned processes |
| `CP-05` | Pausing or resuming the schedule operates on `hfcache-sync.timer` only. The plugin never stops, starts, enables, or disables `hfcache.target` — stopping it unmounts `/srv/hfcache` (`docs/operations.md` §9) |
| `CP-06` | The plugin never enables `hfcache-verify.timer`. It displays the timer's state and the reason it is disabled (operator handoff item 8). Enabling and disabling `hfcache-sync.timer` is permitted |
| `CP-07` | `archive init`, in any form including `--inspect`, is outside the plugin's surface (`FS-21`; `docs/agents/environment.md`) |
| `CP-08` | No credential surface: the plugin never reads `$CREDENTIALS_DIRECTORY` or a token file, never offers token entry, and renders only the `token_source` string from envelopes (`docs/security.md` T-07) |
| `CP-09` | The plugin never writes under `/srv/hfcache`. Its only direct read there is `runs/*.json`, performed as the service identity; every other statement about the archive comes from a CLI envelope |
| `CP-10` | One mutating command at a time (`AD-17`). `HFMNT010` renders as a benign busy state naming the holder, never as a failure; the plugin never removes or bypasses the lock |
| `CP-11` | Configuration changes go only through the §6 pipeline: candidate file, `config validate` exit `0`, atomic install preserving `0640 root:hfcache`, predecessor retained |
| `CP-12` | Timer schedule changes are drop-ins under `/etc/systemd/system/hfcache-sync.timer.d/` (§7); shipped unit files are never edited, and calendar expressions are validated with `systemd-analyze calendar` before anything is written |
| `CP-13` | The plugin never weakens systemd hardening or SELinux and never advises doing so; a denial is fixed per `docs/plan.md` §23 or reported |
| `CP-14` | The node toolchain is build-time only. The plugin ships as static files; the application's closed runtime dependency set (`FW-03`) is untouched, and `cockpit/node_modules/` and `cockpit/dist/` are never committed |

## 2. Privilege and identity

Cockpit authenticates against the host (PAM); the plugin performs privileged
work through Cockpit's superuser bridge, which an administrative session
escalates to root. This sits inside the existing trust model: root and the
operator are already the boundary (`docs/security.md` §6), and the plugin
adds no listener, daemon, or state of its own beyond the files §6 and §7
name.

From the root bridge, CLI invocations drop to the service identity:

```text
runuser -u hfcache -- /opt/hfcache/current/.venv/bin/hfcache \
    --config /etc/hfcache/config.toml --json <command>
```

Never root (`CP-03`): anything a command publishes must carry the service
identity, and `/etc/hfcache/config.toml` is `0640 root:hfcache` — the same
invocation shape as `docs/operations.md`'s `$H`, reached from root instead of
from an operator login. systemd operations (units, timers, drop-ins,
`daemon-reload`) and journal reads run as root via the bridge.

Without administrative access the page presents read-only systemd state and
says why everything else is locked. There is no degraded data path: the
configuration is unreadable to an ordinary user by design, and inventing a
side channel would violate `CP-01`.

## 3. Operation surface

| UI operation | Mechanism | Contract |
| --- | --- | --- |
| Health dashboard | `status --json` — the six archive-health fields, free space against reserve, per-repository state | `docs/operations.md` §1 |
| Archived repositories and revisions | `list --revisions --json`, including `managed: false` entries | `docs/cli.md` §2 |
| Sizing preview | `plan --json`, optionally against a candidate configuration (§6) | `docs/operations.md` §3 |
| Sync now (all repositories) | `systemctl start hfcache-sync.service` | `CP-04`; `docs/operations.md` §4 |
| Sync selected repositories | Page-spawned CLI `sync TYPE:ID …` (§5) | decision 89 |
| Stop a running sync | `systemctl stop hfcache-sync.service`, behind a consequence-stating confirmation | §5 |
| Pause / resume schedule | `systemctl stop` / `systemctl start` on `hfcache-sync.timer` | `CP-05` |
| Live sync activity | Journal stream of the unit, §24 event vocabulary | §5 |
| Verify — estimate | CLI `verify --estimate` | `docs/cli.md` §2 |
| Verify — one revision | CLI `verify --revision TYPE:ID@SHA` | `docs/cli.md` §2 |
| Verify — full | `systemctl start hfcache-verify.service` | `CP-04` |
| Verification timer | Display state and reason only | `CP-06` |
| Doctor | CLI `doctor` / `doctor --read-only`, 17 named checks rendered in order | `docs/cli.md` §2 |
| Retention | CLI `prune --dry-run`, then `--apply` behind confirmation | `docs/cli.md` §2 |
| Recovery | CLI `recover --dry-run`, then `--apply`; blocked states shown with their `HFTXN` codes | `docs/operations.md` §6 |
| Repair | CLI `repair TYPE:ID@SHA --reason TEXT`, launched from a verification finding | `docs/cli.md` §2 |
| Version | CLI `version` | `docs/cli.md` §2 |
| Configuration | §6 pipeline | `docs/configuration.md` |
| Sync schedule | §7 drop-in | `packaging/systemd/hfcache-sync.timer` |
| Run reports | List and read `runs/*.json` as the service identity | `CP-09`; `docs/schemas.md` §6 |
| Warnings | `status` findings, each `HFWRN` code paired with its §8 runbook response as inline guidance | `docs/operations.md` §8 |

There is no publish operation, because the application has none: publication
is an atomic stage inside `sync`, and `repair` is the only command that
republishes (decision 89). The UI presents "Sync now" and renders published
state — publication ID, generation, timestamp, verification state — from
`list --revisions`.

## 4. Envelope and error handling

Exit codes map to UI states, not to a generic error toast:

| Exit | UI state |
| --- | --- |
| `0` | Success; render `data`, surface `warnings[]` |
| `10` | Invocation or configuration problem; map `HFCFG`/`HFARG` codes onto the offending form fields where the UI owns the input |
| `20` | Safety refusal; nothing changed. `HFMNT010` is the benign busy case (`CP-10`); the rest render `doctor`'s vocabulary |
| `30` | Partial failure; per-repository outcomes from the `RunReport` payload |
| `40` | Integrity finding: prominent, persistent, linking the repair flow; the UI never offers to sync or prune from this state (`docs/operations.md` §7) |
| `50` | Retention/repair failure; the UI surfaces `recover --dry-run` |

The envelope is emitted even on failure, so the plugin never diagnoses by
parsing human text (`CP-02`). `warnings[]` and `errors[]` render with their
stable codes; the codes are the join key to the runbook guidance the UI
carries. Raw stderr is available in a collapsed log pane for the operator who
wants it, and is never interpreted.

## 5. Long-running operations and concurrency

Work spawned from a browser page dies with the page — Cockpit's own guidance,
and the reason for `CP-04`. The units also carry what a bare spawn would
lose: the §22.5 sandbox, `MemoryHigh=`, the journal identity, and systemd's
merge semantics for a timer elapse during a run.

**Selector-restricted sync** is the deliberate exception (decision 89): it
runs as a page-spawned CLI process, accepting that a closed tab interrupts
it, because interruption is a crash shape the application is designed for —
per-repository transactions, resumable cache partials (`AD-09`), and
reconciliation (`docs/operations.md` §9). The UI states this before starting
one, and after any interrupted mutating operation it surfaces
`recover --dry-run`. A templated unit carrying selectors under the full
hardening is the recorded follow-up seam, not part of version 1.

**Stopping a running sync** is `systemctl stop` (SIGTERM). The confirmation
states the consequences plainly: everything already published stays
published, partial downloads resume from the cache on the next run, and
reconciliation handles the rest.

**Live activity** comes from the unit's journal: `ActiveState` plus the
structured `event=` lines. The vocabulary is closed (`docs/plan.md` §24;
`hfcache.logging.EVENTS`), so the UI keys only on documented event names —
`run.started`, `repository.resolved`, `repository.skipped`,
`publication.completed`, `run.completed`, and peers — and ignores names it
does not know rather than failing on them. Progress is checkpoint-grained by
design; the UI does not invent percentages the events do not carry.

Before offering any mutating action the UI reads `is-active` for both
services and reflects the single-writer reality (`CP-10`); it never polls the
lock file itself.

## 6. Configuration editing

The pipeline, in order, all steps mandatory (`CP-11`):

1. **Candidate.** The edited document is written to
   `/etc/hfcache/.candidate.toml`, `0640 root:hfcache` — same directory as
   the target, so the final rename is atomic and the service identity can
   read it.
2. **Validate.** `hfcache --config /etc/hfcache/.candidate.toml --json
   config validate`, as the service identity. Exit `0` is required;
   `HFCFG`/`HFARG` codes map back onto the form (`docs/configuration.md`
   §8).
3. **Preview, when the change adds or retargets a repository.**
   `hfcache --config /etc/hfcache/.candidate.toml --json plan TYPE:ID` — the
   runbook's mandatory sizing step, run against the candidate before it is
   installed. `plan` takes no lock and mutates nothing, so a candidate is a
   legitimate target.
4. **Install.** The current file is copied to `/etc/hfcache/config.toml.bak`
   (one predecessor, `0640 root:hfcache`), then the candidate is fsynced and
   renamed over `/etc/hfcache/config.toml`.
5. **Confirm.** `config validate` once more against the installed path, and
   the reported `config_fingerprint` is displayed — the value run reports
   will carry.

Two editing modes, one pipeline. **Form mode** renders the schema as
controls — per-repository `id`, `type`, `revision`, `enabled`,
`declared_dependencies`, and the `[hub]`/`[storage]`/`[sync]`/
`[verification]`/`[repair]` tables — with each key's documented constraint
enforced client-side and re-enforced by step 2. Form mode serializes
canonically and **does not preserve operator comments**; the UI says so, and
the generated header comment names the plugin and the write time. **Text
mode** edits the document verbatim for the operator who keeps comments. The
editor writes only schema-version-1 keys; there is no token field to offer
(`CP-08`, `HFCFG010`).

The add-repository wizard is this pipeline with steps 3 and an optional
selector sync (§5) attached — entry, validate, sizing preview, install, and
only then, offer to sync.

Removing a repository never deletes archived data (`AD-06`); the UI states
beside the removal control that revisions remain and will appear as
unmanaged (`HFWRN007`).

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
`docs/operations.md` §9): the calendar is site-local time deliberately;
`Persistent=true` replays an elapse missed while the host was down; an elapse
that arrives mid-run merges into the running sync and the day is skipped —
designed observation semantics (`AD-02`/`AD-03`), not a fault. Removing the
drop-in restores the shipped schedule; the UI offers that as "reset to
default".

## 8. Toolchain, layout, and gate

`cockpit/` is derived from the Cockpit starter kit: esbuild via `build.js`,
PatternFly, `src/` compiled to `cockpit/dist/`, a `Makefile` for install and
development targets, and the starter kit's lint set. Deviations from the
starter kit as shipped:

- **pnpm, not npm** (decision 88). `cockpit/pnpm-lock.yaml` is committed;
  installs are `pnpm install --frozen-lockfile`; no `package-lock.json`
  exists. The node version is pinned in-repo at scaffold time so builds are
  reproducible; node and pnpm live in the operator's `PNPM_HOME`
  (`~/.local/share/pnpm` by default) and are build-time only (`CP-14`).
- **Development loop** targets this deployment: `cockpit/dist` symlinked as
  `~/.local/share/cockpit/hfcache`, verified with
  `cockpit-bridge --packages`, browser refresh after rebuild.
- **Install** is `make -C cockpit install` to `/usr/share/cockpit/hfcache`,
  root-owned, as a deployment step beside — not inside — the application's
  release procedure. The deployment runbook gains its section at `CPT-011`.

The package registers one entry named `hfcache`; menu placement is decided
at scaffold time (`CPT-002`).

**Gate.** `scripts/check.sh` runs the plugin gate — frozen install, ESLint,
Stylelint, production build — when `cockpit/` exists and `pnpm` resolves
(via `PATH`, falling back to `$PNPM_HOME/bin`). When the toolchain is
absent the gate skips the plugin steps with a loud printed notice and stays
green: the Python gate must keep meaning what it means on hosts without
node. The discipline that closes the hole: a `CPT` package lands only from a
host where the plugin gate actually ran, and its tracker entry says so. The
wiring lands at `CPT-002`.

## 9. Testing

Logic that does not need a browser — envelope parsing and the
`schema_version` gate, exit-code and taxonomy mapping, selector grammar,
calendar-expression handling, configuration form ↔ TOML mapping — lives in
plain modules and is unit-tested under pnpm; the runner is chosen at
`CPT-002` and runs inside the plugin gate. Cockpit's Chrome-DevTools-based
integration tests are **deferred**: they require disposable test VMs, and
the writer is not a test-VM host (`docs/agents/environment.md`). The
deferral is a stated limit of version 1, revisited if the plugin grows
beyond an operator tool.

The Python suite is unaffected by plugin packages, but the gate is the gate:
every `CPT` commit runs `scripts/check.sh` like every other commit.

## 10. Version 1 non-goals

- Consumer-side views, and anything on the NAS: exports, snapshots, quotas,
  scrubs are operator work outside this host (`docs/agents/environment.md`).
- `archive init` (`CP-07`), enabling `hfcache-verify.timer` (`CP-06`), any
  credential handling (`CP-08`).
- Multi-writer or multi-host management (`NG-10`): the plugin administers
  the one deployed writer it is installed on.
- Translations: the starter kit's gettext scaffolding may remain in place,
  but no translated catalog ships.
- Browser integration tests (§9).

`docs/security.md` gains its reconciliation — a threat-model row for the
management surface — at `CPT-011`, when what ships is fixed rather than
planned.
