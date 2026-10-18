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
entire API. The plugin keeps the CLI/systemd boundary while the CLI uses the writer API;
nothing the plugin does is anything an operator could not reproduce by hand
with the commands in `docs/operations.md`, and the UI displays the underlying
command wherever practical so the plugin teaches the runbook rather than
hiding it.

Operator-facing installation and usage documentation is
`docs/cockpit-plugin/` (`CPT-012`), written against this contract; where
they disagree, this document wins and the operator pages are corrected.

**API-014 deployment amendment (2026-10-18, [decision 121](adr/decision-121.md)).**
The shipped sync/verify service names now observe API operations through private
AF_UNIX clients. Their names, calendars, disabled verification timer, OnFailure
hooks and target/mount boundary stay intact (CP-05/06/13). Stopping an observer
does not stop accepted execution or prove a free archive; preserve its pending
handle and use the [executor drain procedure](deployment-centos-stream-10.md#13-upgrade-plan-30).
The actual API/private worker owns archive/Hub authority. A browser/transient
client must not receive a Hub credential; API credentials remain systemd-managed
and never enter the page (CP-08). Decision 122 below governs the plugin's API
integration; this API-014 amendment records its earlier scope, without claiming
deployment. Installed hardening/SELinux/NFS acceptance remains pending.

**Historical native-profile API-015 amendment (2026-10-18, [decision 122](adr/decision-122.md)).**
The selected rootless profile below and [decision 127](adr/decision-127.md)
supersede its inner executable, socket and host credential-import mechanism.
Transient commands use fixed `--client-config /etc/hfcache/client.toml
--api-socket /run/hfcache/api.sock --json`, service UID/GID, `UMask=0027`,
`MemoryHigh=4G` and `ImportCredential=hfcache.api`. Omit ordinary archive
`--config` and Hub environment/credential imports; only explicit candidate
validate/plan adds `/etc/hfcache/.candidate.toml`. The browser never handles a
bearer. This supersedes the historical direct Hub execution and stop/recover
mechanisms retained in decisions 087/089/092.

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
preview success and exact installed fingerprint confirmation are separate gates;
incompatible/unknown authority blocks plugin installation and explains the manual
operator install/restart/compatible-preview sequence. Failed preview/confirmation
cannot render success. Preserve atomic backup/install, service identity and
`0640 root:hfcache`. New policy changes future admissions, never an admitted
snapshot; the server refuses stale queued mutations.

## 1. Rules

| ID | Rule |
| --- | --- |
| `CP-01` | The plugin invokes the installed CLI and systemd; it never reads or writes archive state directly and never re-implements resolution, validation, verification, or retention logic. One read-only exception: §4's run-report browsing |
| `CP-02` | Every CLI invocation passes `--json`; command outcomes require a bounded strict schema-1 Envelope. Refuse unknown versions. Separately validated bounded progress and recovery handles may render/reconnect; stderr never grants domain authority or fabricates outcome/checkpoints/percentages |
| `CP-03` | Mutating actions require Cockpit administrative access. The CLI runs as the service identity inside a transient systemd unit (§2), never as root |
| `CP-04` | A full sync and a full verification run only through `hfcache-sync.service` and `hfcache-verify.service` — never as page-spawned processes |
| `CP-05` | Pausing or resuming the schedule operates on `hfcache-sync.timer` only. The plugin never stops, starts, enables, or disables `hfcache.target` — stopping it unmounts `/srv/hfcache` (`docs/operations.md` §9) |
| `CP-06` | The plugin never enables `hfcache-verify.timer`. It displays the timer's state and the reason it is disabled (operator handoff item 8). Enabling and disabling `hfcache-sync.timer` is permitted |
| `CP-07` | `archive init`, in any form including `--inspect`, is outside the plugin's surface (`FS-21`; `docs/agents/environment.md`) |
| `CP-08` | No credential surface: the page never reads credentials or accepts tokens. Transient clients receive only named API `hfcache.api` inside the fixed rootless client, never Hub authority or browser/environment/argument bearers. Only safe source descriptions render (`docs/security.md` T-07) |
| `CP-09` | The plugin never writes under `/srv/hfcache`. Its only direct read there is `runs/*.json`, performed as the service identity; every other statement about the archive comes from a CLI envelope |
| `CP-10` | One mutating command at a time (`AD-17`). `HFMNT010` renders as a benign busy state naming the holder, never as a failure; the plugin never removes or bypasses the lock |
| `CP-11` | Configuration changes use §6's root config flock and exact candidate/base guards, syntax-valid compatible server assessment, required successful preview, atomic install with `0640 root:hfcache` and predecessor retained, then exact expected installed fingerprint confirmation. Incompatible/unknown authority blocks plugin install |
| `CP-12` | Timer schedule changes are drop-ins under `/etc/systemd/system/hfcache-sync.timer.d/` (§7); shipped unit files are never edited, and calendar expressions are validated with `systemd-analyze calendar` before anything is written |
| `CP-13` | The plugin never weakens systemd hardening or SELinux and never advises doing so; a denial is fixed per `docs/agents/history/plan.md` §23 or reported |
| `CP-14` | The node toolchain is build-time only. The plugin ships as static files; the application's closed runtime dependency set (`FW-03`) is untouched, and `cockpit/node_modules/` and `cockpit/dist/` are never committed |

Current [data-preserving rollout](agents/plans/2026-10-18-plan-local-rootless-rollout.md)
keeps legacy system-bus sync/verify/timer units masked. Normal CP-04–06 controls
must refuse rather than redirect to user units or re-enable NAS writes. This is
an explicit current restriction, not successful installed browser acceptance.

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
uses direct reads as the service identity (`CP-09`), without Hub/config access.
Without administrative access the page presents permitted read-only systemd state
and explains why privileged actions are locked. It invents no archive side channel.

## 3. Operation surface

| UI operation | Mechanism | Contract |
| --- | --- | --- |
| Health dashboard | `status --json` — the six archive-health fields, free space against reserve, per-repository state | `docs/operations.md` §1 |
| Archived repositories and revisions | `list --revisions --json`, including `managed: false` entries; repository names link to their type-aware Hugging Face pages | `docs/cli.md` §2 |
| Sizing preview | `plan --json`, optionally against a candidate configuration (§6) | `docs/operations.md` §3 |
| Sync now (all repositories) | `systemctl start hfcache-sync.service` | `CP-04`; `docs/operations.md` §4 |
| Sync selected repositories | Page-spawned CLI `sync TYPE:ID …` (§5) | decision 89 |
| Stop sync observation | `systemctl stop hfcache-sync.service`; accepted server work may continue | §5 |
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
| `40` | Integrity finding: prominent, persistent, linking the repair flow; the UI never offers to sync or prune from this state (`docs/operations.md` §7) |
| `50` | Retention/repair failure; use retained evidence and the supervised recovery runbook |

The envelope is emitted even on failure, so the plugin never diagnoses by
parsing human text (`CP-02`). `warnings[]` and `errors[]` render with their
stable codes; the codes are the join key to the runbook guidance the UI
carries. Bounded stderr is available for diagnostics. Only documented strictly validated
progress/recovery notices are interpreted for display/reconnection; domain
outcomes still require the terminal Envelope. HFAPI013/015/019/020 or
`data.work_may_continue=true` render as uncertain observation with retained handles,
never a claim of cancellation, nonexecution or automatic recovery authority.

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

Reject malformed notices; unknown lines remain bounded diagnostics. Keep validated
key/ID independently of log eviction. Reconnect commands keep handles as arguments,
not executable text, use `--` before positional values and quote copied keys so
even valid leading `-`/`~` characters remain data. Display
abort/callback failure detaches view updates without
closing the spawned process or cancelling server work.

## 5. Long-running operations and concurrency

Full sync/full verification start the existing installed services (`CP-04`). Their
API-backed scheduled observers retain private recovery handles and stay active
through repeated finite observation windows; timer elapses merge into the same
active oneshot. Selected sync, single-revision verification, repair and other
explicit CLI jobs use §2's transient observer. The server owns accepted work;
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
   strict Envelope and the exact expected candidate fingerprint. Only then display
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


## Rootless client profile amendment (OPS-015)

[Decision 127](adr/decision-127.md) governs the selected local rootless profile.
Preserve outer systemd-run User/Group=hfcache, UMask=0027, MemoryHigh=4G and
root candidate/base flock/atomic install guards. Replace only the inner host
Python CLI with fixed /usr/local/libexec/hfcache-client and the explicit client
settings/API socket /run/hfcache/api/api.sock. Remove host ImportCredential: the
fixed Podman launcher delivers API-only mounted authority to its rootless client.
The browser and host transient unit never need credential bytes or Hub authority.
No generic image/executable/Podman argv and no bare-host fallback is added.

Strict bounded terminal/progress/handles, exact server Envelope identity, no
cancellation/replay and candidate syntax/authority/preview/confirmation remain.
System-bus legacy sync/verify/timer controls remain masked/blocked by decision 126;
do not silently redirect them to identically spelled user-manager units. Rootless
service lifecycle belongs to the reviewed target bridge, not a new browser API.
This supersedes selected-profile argv in the API-015 amendment above while keeping
historical native packaging explicit. OPS-015 actual fixtures bind no NAS and
perform no production switch; installed browser/runtime acceptance remains later.
