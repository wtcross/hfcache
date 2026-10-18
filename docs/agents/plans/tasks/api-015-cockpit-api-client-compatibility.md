# API-015: Preserve Cockpit operations, progress, and candidate configuration flow

| Field | Value |
| --- | --- |
| Work package | `API-015` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-014](api-014-systemd-and-deployment-integration.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-015: preserve Cockpit workflows through the API-backed CLI` |

## Scope and acceptance

1. Update Cockpit’s command/transient-unit construction to invoke the API-backed CLI with client configuration/socket and a systemd-imported API credential. Ordinary runtime calls no longer pass archive --config. The browser never reads, stores, or submits a bearer token.
2. Keep full sync/verification attached to their installed service names and preserve schema-1 failure parsing. Preserve selected sync and operation progress through the CLI’s bounded event stream and terminal envelope. Explain that closing a view or stopping a client does not cancel accepted server work.
3. Preserve candidate creation, CLI server-side validation/preview, atomic privileged install/backup, and installed fingerprint confirmation. Show authority-change preview restrictions explicitly. A newly installed policy affects future operations, not an admitted snapshot; stale queued mutations fail safely.
4. Preserve root/admin/service-identity separation, lock/busy reporting, schedule-only sync timer controls, and no archive-init UI. Existing direct run-report browsing may remain its documented exception; do not add new direct archive writes or an in-browser REST credential backend.

## Contracts, invariants, and ADRs

`CP-01`–`CP-14`, `INV-002`/`INV-003`/`INV-006`; plan §§6–7.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update `docs/cockpit.md`, relevant `docs/cockpit-plugin/` install/usage/acceptance pages, API-client integration examples, security/Cockpit invariant notes, and changed command/credential ADR statuses. Preserve all CP controls or amend their precise mechanism explicitly.

## Validation

Planned checks, not execution evidence:

Cockpit command/envelope/config/schedule tests plus integration fixtures for candidate preview/install, API auth failure, busy/stale operation, streaming failure envelope, and page closure. Search built/source UI for bearer/Hub-secret handling. Run the full `make -C cockpit check` stage and `scripts/check.sh`; skipped plugin coverage blocks completion.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Activated 2026-10-18 under Tyler's authorized implementation of the selected
REST-first plan after completed dependency API-014 committed as `c2eff85`.
Git/current/dependency evidence was reconciled with a clean tree; API-015 is the
sole task in progress at activation. Collaborators share Cockpit API command/progress adapters,
candidate-install authority and adversarial tests; all Markdown belongs to this
task. Decision 122 follows the actual log. No MCP or production operation,
deployment, push, merge or tag. Repository acceptance is recorded below;
installed-host acceptance remains an operator hold.

Contract-first amendments preserve root/admin/service separation and CP-01–14
while replacing transient Hub authority with named API-only `hfcache.api` and
local client configuration/socket. Terminal domain decisions require a strict
bounded schema-1 Envelope; documented validated safety handles and bounded
progress may render without inventing outcomes or percentages. Closing a page or
stopping a client stops observation, never cancels accepted execution or proves
recovery safe. Candidate exact content and installed base are guarded under the
privileged config flock; syntax validity, authority compatibility, preview
readiness and installed confirmation are distinct requirements. Unknown or
incompatible authority blocks plugin installation and presents a manual operator
sequence. No preview/confirmation failure may render install success. Source/API
details and acceptance evidence follow.

Transient invocation is fixed to the service identity, API-only
`ImportCredential=hfcache.api`, `/etc/hfcache/client.toml` and
`/run/hfcache/api.sock`; the shipped `packaging/cockpit-client.toml` validates as
`ClientConfig` and contains no Hub settings or token file. New pure runner/framing
modules bound UTF-8 terminal JSON to 16 MiB, progress line to 8 KiB, retained
diagnostics to 64 KiB and each display push to 256 lines. Handle inspection occurs
before display suppression; terminal collection is independent, including split
surrogate-pair accounting. Abort/callback failure detaches display, never closes
the process or cancels execution. Core command/event/stream/runner tests:
`rtk proxy node --test test/command.test.ts test/events.test.ts test/stream.test.ts test/runner.test.ts`
from `cockpit/` passed a final 35 tests in 1.031 seconds; scoped ESLint and whole
TypeScript passed. Retained UI feeds additionally cap at 200 whole lines/64 KiB,
independently of handles; terminal assembly uses finite blocks for tiny chunks.
Unknown terminal schema preserves safe fixed upgrade guidance and handles without
echoing an untrusted schema value. These focused checks preceded full acceptance.

Root's strict complete/coherent terminal parsing, uncertainty/handle guidance and
unit-action allowlist passed 19 envelope/systemd cases in 226.7 ms, with scoped
ESLint clean. Review corrected reconnect command generation for valid leading
`-` and `~` keys using `--` and shell-quoted keys, and the dashboard now requests
`version --server`. All activity/journal feeds use whole-line UTF-8/64 KiB bounds,
with newest invocation key/ID retained separately. Candidate integration/read
guards and the definitive full gate are recorded below.

Candidate owner released `candidate-guard.ts` / `config-pipeline.ts` with actual
disposable Bash/flock/cmp/fsync/rename fixtures, faking only the systemd-run leaf.
`rtk pnpm --dir cockpit exec node --test test/candidate-guard.test.ts test/config-pipeline.test.ts test/config.test.ts`
passed 59 tests; whole Cockpit TypeScript, owned ESLint and whitespace passed.
Fixed installed reads take the config flock and enforce bounded no-follow,
root/group/mode/single-link checks. Install/confirmation failure invalidates
readiness and requires reload because installation may have completed. Final
read-only ADR/contract review found no material contradiction. No host service or
archive operation was performed. Standalone complete Cockpit and full project
gate evidence follow.

## Completion evidence

Completed 2026-10-18, this commit. Cockpit uses the installed API-backed CLI with
fixed local client settings/socket and named API-only `hfcache.api`, preserving
root/admin/service separation without browser/Hub bearer authority. Strict bounded
schema-1 terminal parsing preserves classified failures; independent progress/
handle framing, bounded activity feeds and view detachment retain observation
safety. Client stop/page closure never cancels accepted work, triggers automatic
recovery or proves nothing changed. Unit/action guards preserve installed full
sync/verification, sync-timer-only controls and no target/init UI.

Exact candidate/base guards under a retained root config flock protect bounded
no-follow editor reads, assessment/required preview and atomic backup/install.
Validity/authority/readiness/confirmation stay separate; incompatible/unknown
authority blocks plugin install. Install/confirmation errors clear readiness and
require reload, without fabricated success or rollback claims. New policy affects
future admissions, never admitted snapshots or fresh server lock proof.

Standalone `rtk proxy make -C cockpit check PNPM=/home/tyler/.local/share/pnpm/bin/pnpm > .scratch/api-015-cockpit.log 2>&1`
exited 0: ESLint, Stylelint, TypeScript, 127 tests in 2.035 seconds and production
build in 1,188 ms. Source/production security scan
`rtk rg -l -- 'Authorization|Bearer|api_token_file|HF_TOKEN|hf-token|HF_HOME|HF_XET|--token-file' cockpit/src cockpit/dist`
found none (expected exit 1). Python gzip-decompression of
`cockpit/dist/index.js.gz` found the same forbidden literal patterns absent and
asserted the expected API credential name, local socket and client path present.
The decompressed production scan passed again after the final build.

First-attempt `rtk proxy bash scripts/check.sh > .scratch/api-015-gate.log 2>&1`
exited 0: lock/sync, 361 formatted files, Ruff clean, Pyrefly 0 errors
(11 suppressed, 57 warnings not shown); 3,223 Python tests passed, 40 deselected,
in 352.53 seconds; 0.1.10 source distribution/wheel built; actual locked isolated
base/server installation/import/help/version checks passed. Cockpit lint/style/
types, 127 tests in 2.093 seconds and production build in 1,171 ms passed. No
gate correction/restart or post-gate source change. Focused 35 runner, 19
envelope/unit and 59 candidate cases are recorded above. Final links/current/
dependencies, 29 implemented parity rows, 122 unique indexed decision/ADR records
and whitespace pass; see the completed [progress audit](../../progress.md).

Reviewed CP-01–14 and INV-002/003/006. Decision 122 and amendments to
087/089/091/092/119/120/121, Cockpit/operator pages, API-client/configuration/
security/invariants, deployment, README and Unreleased agree. Existing route,
domain/lock/recovery/receipt/archive contracts remain; no new durable JSON or
runtime dependency. The retained root config lock is not an execution journal.

Actual browser/PAM bridge, deployed named credential delivery, executor
hardening/cgroup/custom masks, SELinux/NFS, drain and verify-calendar acceptance
remain operator holds. No browser-host/service/archive operation, installation,
deployment, push/merge/tag or MCP work occurred. Live/NFS and extra build-marker
suites were not run. Current selects API-016 pending after this commit; REST
acceptance must complete before any MCP implementation.
