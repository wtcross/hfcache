# API-014: Package the server, private worker, and API-backed scheduled services

| Field | Value |
| --- | --- |
| Work package | `API-014` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-013](api-013-migrate-write-cli-and-operation-waiting.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-014: package API services and preserve offline verification hardening` |

## Scope and acceptance

1. Add server and private verification socket/service units, configuration/credential examples, install/upgrade/rollback support, and a tested single-app Unix/TCP socket arrangement. Keep server and worker unprivileged with existing SELinux/systemd protections, safe writable paths, and shared runtime-lock lifetime.
2. Convert the existing sync/verify service commands into API-backed CLI clients using the local Unix socket and distinct API credentials. Preserve their names, schedules, terminal exit outcomes, disabled verify timer, and monitoring hooks. Verify-client IP deny policy can remain because HTTP uses AF_UNIX.
3. Place `IPAddressDeny=any`, process-wide offline flags, and no Hub/API/MCP credentials around the actual verification executor too. Validate socket activation, peer restrictions, expected fingerprint, reconnect/result handoff, and absence of generic privileged execution. Update hardening probes to measure the actual executing service, not just wrappers.
4. Update deployment draining/cancellation and supervised-recovery instructions: stopping a client service is not proof the writer stopped. Rehearse upgrade/rollback and orphan-worker handling on disposable fixtures. Preserve `hfcache.target`, lock files, filesystem mounts, NFS policies, and the QUA-003 evidence conditions. No production deploy is authorized by this task.

## Contracts, invariants, and ADRs

`INV-003`, `AD-17`, `FS-18`/`FS-19`, `CP-05`–`CP-08`/`CP-13`; systemd scheduling/offline ADRs; plan §6.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update server, CentOS Stream 10 deployment, operations, recovery, agent environment/release guidance, packaging examples, README, systemd scheduling/offline ADR amendments, and architecture §7.8.2 cancellation references. Mark operator-only host acceptance pending.

## Validation

Planned checks, not execution evidence:

Required repository checks: unit-file contract tests, credential/import assertions, installer smoke/dry runs, private-worker socket/protocol fixtures, and `scripts/check.sh`. Run systemd-analyze verify where supported and record its availability. Operator deployment prerequisites: real socket activation, cgroup no-IP/no-credential executor probes, and scripts/check-hardening.sh in an authorized disposable or operator-approved environment. When that environment is unavailable, record these as pending deployment holds; they are not substituted by hermetic tests and do not falsely become passed checks. Repository implementation completion does not assert production acceptance.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
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

Implementation continues under Tyler's authorized active plan after API-013
completed in `a01875c`; git, completed dependency and current selector were
reconciled before starting. API-014 was the sole task in progress. Collaborators
share socket activation/unit packaging, scheduled observation handles, installer/
hardening fixtures and all Markdown contracts/records. Decision 121 was allocated
after checking the actual log. No production archive operation, deployment, push,
merge or tag.
Repository acceptance is recorded below; real systemd socket/cgroup/no-IP/
no-credential/SELinux/NFS proof remains a deployment hold.

Contract-first choices preserve one app/lifespan across activated Unix/optional
TCP sockets and a dedicated offline/no-IP credential-free verification worker.
Both use unprivileged hfcache identity with account-resolved peer UID, never
systemd manager `%U`. Worker sandbox hides credential/source stores; arbitrary
custom development credential paths need explicit operator restrictions.
Existing service names/calendars, disabled verify timer, OnFailure/target/mount
and shared runtime-lock lifetime remain intact. Scheduled clients use only API
credentials and AF_UNIX, distinct from the daemon's Hub source.

Scheduled oneshots retain their multi-hour lifetime through repeated finite
observation windows. An independent strict schema-1 private handle binds fixed
sync/verify-full intent, endpoint, expected archive UUID and REST-writer namespace;
fsync its generated key before the sole POST and persist a known operation ID.
No bearer/digest/body/queue. Existing history permits lookup/observation only;
unknown/malformed/future/mismatched history is preserved with exit 20, never
replayed. Exact terminal result permits safe handle removal; same-class credential
rotation preserves recovery. Durable compatibility and disposable upgrade/drain/
rollback evidence are required, without installed-host claims.

Runtime source adopts exact named manager listeners from any detected activation
metadata, rejects partial/mismatched sets, checks optional pidfd identity, clears
activation variables and never rebinds/unlinks/shuts down manager sockets. Unix
UID/mode/group/parent and IPv6-only policies are validated. Worker descriptor audit
precedes NSS/shared imports; account/UID options are exclusive with euid default
and known credential spellings include HUGGINGFACE_HUB_TOKEN. Focused command:
`rtk uv run --locked --extra server pytest tests/unit/test_server_activation.py tests/unit/test_verification_worker_bootstrap.py tests/unit/test_server_bootstrap.py tests/unit/test_verification_executor.py -q -x`
passed 99 tests in 37.03 seconds (`.scratch/api-014-socket-tests.log`), with
Ruff/format/Pyrefly clean. Actual inherited FD3/4 process fixtures prove runtime
ABI/peer/drain behavior, not installed systemd/cgroup acceptance. API SIGTERM
drains before Uvicorn replays the signal (process return `-SIGTERM`); worker
SIGTERM exits 0. These focused checks preceded the definitive full gate below.

Scheduled source now has fixed `run_scheduled` / module entrypoint, typed
`ScheduledObservation`, pinned `ObservationFile`, and seven-field private schema1.
`pending.json` is bounded to 4096 bytes, private euid-owned single-link files and
retained `.lock`; unexplained temps block resumption. Golden builder
`tests/fixtures/examples.py::scheduled_observation` and independent private fixture
`tests/fixtures/schemas/private/scheduled-observation.json` remain separate from
archive `VersionedModel` / `SCHEMA_VERSION`. All absolute ancestors are protected
against links, unsafe ownership and nonsticky writable directories; vanished
pending state after inventory refuses instead of becoming fresh. The command
`rtk uv run pytest tests/unit/test_scheduled_client.py tests/unit/test_systemd_units.py tests/unit/test_models.py -q -x`
passed 247 tests in 3.76 seconds after final signal regressions; actual
authenticated fake-Hub observer crash/restart retains
one durable operation/download set. Exact terminal output/exit and safe stderr
handles are preserved. `systemd-analyze verify --no-pager` on all nine hfcache
unit files exited 0 with no diagnostics under systemd 257
(`257-31.el10-gf54be5a`); installed activation/cgroup/SELinux/NFS is still held.
Actual AF_UNIX subprocess SIGTERM and SIGINT cases preserve exact pending bytes
and exclusive ownership, send no POST, emit no terminal stdout, and return
HFAPI019 / exit 20 with handles/recovery notices. Only `main` temporarily installs
and restores signal handlers; library calls have no signal side effects. A stop
flag prevents a normalized transport interruption from being retried as another
observation window. Static checks remain clean.

The actual compatibility drill (`rtk uv run python .scratch/api-014-drill.py`,
exit 0) in `.scratch/api-014-compatibility/commands.log`
built/installed predecessor `a01875c` wheel 0.1.10 in a separate CPython 3.14.6
environment using locked offline dependencies. Its actual
`python -I -m hfcache.scheduled_client --client-config PATH --state-directory PATH sync`
invocations exit 1 for both schema1/future2 because the module is absent, preserving
pending bytes. Current `ObservationFile` reads 1; current actual module on 2 exits
20/HFAPI014 and preserves exact bytes. Result is
`.scratch/api-014-compatibility/result.json`; future fixture SHA-256 is
`77bcc750b8f8f834ad61a1d5c234afaae1cd88468c3c6d193520ce33358f6b4f`.
No archive operation or production installation. Absence of old support is not
old-reader success or proof of nonexecution; preserve handles/operation stores
and use compatible observation before any rollback/retry.

`rtk uv run pytest tests/unit/test_release_installer.py tests/unit/test_hardening_probe.py -q -x`
passed 63 tests in 14.56 seconds, with format/lint/types clean. The first focused
installed smoke exposed a string passed to `load_config` where `Path` was required;
that source bug was corrected before the 63-case pass. After safe policy-error
formatting, `rtk uv run pytest tests/unit/test_release_installer.py -q -k installed_smoke`
passed 2 cases, 32 deselected, in 6.73 seconds: required-Hub
policy parses without credential/archive access, synthetic disabled-token CLI
validation is explicit `--local`, and invalid policy refuses through safe
diagnostics. Dry run proves no root/tool/action requirement. Disposable two-tree
switch/rollback fixtures retain lock inode/evidence, refuse live observers,
executors and orphan holders, and hold the noncreating flock through switching.
Pre-gate review corrected the rollback scan to `/var/lib/hfcache/scheduled`,
rejected noncanonical archive aliases before service queries, and required empty
control-group evidence when task accounting is unavailable. Pending handles also
refuse targets without the actual observer module. Probe writable paths derive
from actual state/cache/runtime directories; bare Python probe refuses.
`rtk proxy bash -n scripts/install-release.sh scripts/release-functions.sh scripts/check-hardening.sh`
exited 0. These are repository findings and fixtures, not real systemd/cgroup/NFS
proof.

## Completion evidence

Completed 2026-10-18, this commit. One application adopts the exact named Unix/
optional TCP listener set, and the private worker validates inherited descriptors
before shared imports, resolves peer identity safely and retains its offline/
credential-free boundary. Existing sync/verify units observe fixed operations
through API-only credentials without changing calendars, target/mount hooks,
disabled verify timer or lock-inode lifetime. Strict independently versioned
scheduled handles retain lookup-only recovery through finite windows; signal
interruption preserves evidence and never cancels or replays accepted work.

Installer/probe fixtures, actual handle compatibility and focused runtime/observer
checks are recorded above. The first full gate exposed one stale shipped-example
assertion (`rest-writer` versus the new `hfcache.api` source name). It was
interrupted at exit 130 without a final Python count; evidence remains in
`.scratch/api-014-gate-first-interrupted.log`. An assertion-only correction passed
`rtk uv run --locked --extra server pytest tests/unit/test_server_config.py::test_shipped_example_matches_schema -q`
(1 passed in 0.27 seconds), with Ruff/format clean. No runtime change was needed
for that gate finding.

Definitive `rtk proxy bash scripts/check.sh > .scratch/api-014-gate.log 2>&1`
exited 0: lock/sync, 360 formatted Python files, Ruff and Pyrefly 0 errors
(11 suppressed, 57 warnings not shown); 3,223 Python tests passed, 40 deselected,
in 349.85 seconds; 0.1.10 source distribution/wheel built; actual isolated locked
base/server installation/import/help/version checks passed. Cockpit ESLint,
stylelint, TypeScript, 45 tests (0 failures) and production build passed. No
post-gate source change. Final record/link/current/dependency/parity, 121 unique
indexed decision/ADR and whitespace audits pass; all 29 API parity rows remain
implemented. See the completed [progress audit](../../progress.md).

Reviewed INV-003/006/010–015, AD-17, FS-18/19 and CP-05–08/13. Decision 121 and
amendments to scheduling/offline, AD-17, 061/065/115/120 and FW-01–04 distinguish
observer lifetime, executor ownership, retained evidence and private-format
compatibility. Server/client/API/schema/configuration/CLI/security contracts,
architecture §7.8.2, original plan, deployment/operations/recovery, agent guidance,
Cockpit baseline amendment, README and Unreleased agree. Archive/receipt schemas
and runtime dependencies are unchanged; no MCP work or production operation.

Operator handoff retains real named systemd socket activation, executor cgroup
no-IP/credential-source probes (including custom paths), installed hardening,
SELinux/NFS and full-duration verify/calendar acceptance. Repository fixtures and
unit verification do not pass those holds. Live/NFS and extra build-marker suites
were not run. Next selected task is API-015 pending, after this package's commit.
