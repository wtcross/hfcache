# API-013: Move CLI writes onto the API and preserve resumable observation

| Field | Value |
| --- | --- |
| Work package | `API-013` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-012](api-012-migrate-read-cli-and-candidates.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-013: migrate CLI writes and add operation observation` |

## Scope and acceptance

1. Migrate sync, all actual verification, default/probing doctor, apply maintenance, repair, and guarded init to typed operation submissions. No operational CLI command imports or executes a direct mutation backend. Keep initialization confirmation requirements and server maintenance refusal legible.
2. Wait for terminal results by default. Emit exactly one schema-1 command envelope on stdout and preserve domain exit codes, warning aggregation, quiet/verbose/no-color behavior, and report/run correlation. A 202 receipt is not the legacy command result.
3. Add `operations show`, `operations wait`, and authenticated `operations lookup`, plus an explicit detached-submission mode with its separately documented output. Print the nonsecret submission key to stderr before the initial mutation POST, including in quiet mode for safety correlation, and print the accepted operation identity before waiting. An explicit --idempotency-key supports a deliberate same-key retry. Poll bounded sanitized events for progress, preserving the parseable final envelope and not streaming token-bearing raw server logs.
4. On Ctrl-C, timeout, connection loss, or client process death, state that accepted work may continue and retain the operation/key for reconnection. An interrupted wait produces the documented client failure, never fabricated domain success or automatic cancellation/replay. Keep operation deadlines distinct from HTTP poll timeouts.

## Contracts, invariants, and ADRs

`INV-006`, `AD-16`/`AD-17`, `TX-07`; plan §§4–7.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update CLI/API-client examples for submit/wait/resume/detach, transport versus execution failures, event streams, Ctrl-C, and service-stop semantics. Update operations/recovery docs and change notes in this package.

## Validation

Planned checks, not execution evidence:

Each write command through a real temporary server with fake archive/Hub; successful and failed terminal envelopes; nonzero priorities; disconnect before receipt acknowledgement and recover by key lookup, disconnect after admission, retry same key, SIGINT waiting, operations wait later, event cursor resume, detached output, API down with no local fallback, and maintenance-disabled init. Run `scripts/check.sh`.

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

Implementation continues under Tyler's authorized active plan after API-012
completed in `df0af60`; git, completed dependency and current selector were
reconciled before starting. API-013 was the sole task in progress. Collaborators
share CLI wiring/initialization compatibility, pure request and operation helpers,
authenticated writer fixtures and interruption/idempotency/security tests, with
one owner for all Markdown contracts/records. Decision 120 was next in the actual
log. No MCP, runtime dependency, production archive operation, deployment, push,
merge or tag is authorized by this work package. Completed acceptance and the
definitive green gate are recorded below.

Contract-first choices retain the exact terminal server Envelope by default.
Explicit detach returns a separately identified admission object, never a
fabricated terminal success. Print validated nonsecret key before POST and
accepted operation ID before waiting, including quiet mode. One observation
deadline covers bounded sanitized events/status/result reads; timeout/SIGINT
preserves handles and says accepted work may continue without replay/cancellation.
Initialization keeps restated root and explicit confirmation. An omitted optional
UUID comes only from authenticated inspection; a supplied UUID must match.
No-confirm inspection/refusal never submits or reads local archive policy.

Decision 120 is allocated with exact detach kind `operation_admission`:
schema 1, original `idempotency_key` and validated server `acceptance`, without
fabricated outcome/exit. Show/lookup preserve existing metadata Envelopes via
`operation_response` / `lookup_response`, and default command/wait output remains
the exact terminal domain Envelope. Job-only flags on non-submitting reads/
bootstrap refuse; operations wait accepts finite `(0,86400]` timeout and event
cursor. SIGINT before usable acknowledgement remains uncertain HFAPI020; after
acceptance or during observation it is HFAPI019/20 with retained handles. Other
classified errors retain their taxonomy and original validated key/op/route.

Pure request dataclasses/mode constants now live in `services/requests.py`, with
compatibility reexports from existing services; pure version/validation descriptions
live in `services/bootstrap.py`. Operational CLI has no mutation/archive/Hub/
storage import or execution backend. `cli_client` owns option guards,
`submit_job`, `observe_operation` and `admission_payload`; the typed client exposes
exact metadata responses and deadline-aware events/observation while keeping
existing poll compatible without mandatory event fetching.

No-confirm initialization preserves failed inspection exactly, otherwise emits
a local refusal Envelope with local metadata and unchanged inspection data plus
`configured_archive_id` / `config_fingerprint`. Confirmed omitted UUID comes
from that authenticated wrapper, with explicit root/confirmation still required.
Disabled maintenance explicitly refuses HFAPI002 before submission; the server
repeats its unchanged gate/strict DTO. No production initialization is performed.

Focused helper/client selection passed 148 tests in 1.73 seconds, including 21
new helper cases. Ruff and types passed. Root CLI/private-worker fixtures and
adversarial writer migration were still in progress at that focused checkpoint.

Root's writer route/flag/cold-import/no-local-fallback selection passed 44 tests
in 11.60 seconds. Shared service/locking/query/preflight extraction checks passed
87 in 8.38. Final renderer safeguards preserve validated retained-key 5xx taxonomy
while explicitly warning work may continue, and escape nonprintable/control text
for one plain stderr line per event. Further adversarial/migrated checks and the
definitive full gate were still pending at that checkpoint.

The final legacy writer compatibility sweep found generic wire shape taxonomy
for missing/malformed verification revision scope. Pure
`VerificationRequest.validate_scope()` now checks full revision/run ID grammar
before credentials/network while retaining HFARG001 and server-owned HFARG004
membership. Four added regressions pass; helper cases total 25. This is a
compatibility fix before the full gate, not an architectural or domain change.
Read-only/init/quarantine migration checks passed 173 cases; eight new adversarial
observation cases passed in 5.70 seconds, with the strengthened newline/ESC cursor
resume case passing separately in 2.10.

Quarantine's pure scope validator also retains malformed transaction-ID HFARG001
before connection, without duplicating storage proof or changing mode ordering.
The final helper/request file passed 26 tests in 1.13 seconds with Ruff/format/
Pyrefly clean. An injected actual private-verifier crash is now observed through
HFAPI015/20 and its operation handle rather than a Python exception escaping the
local runner; existing archive/catalog/report preservation and later verification
assertions remain. This is the expected remote execution boundary, not a claim
of installed OS isolation or permission to rerun uncertain work.

## Completion evidence

Completed 2026-10-18, this commit.

- All operational CLI modes use fixed typed API resources without direct mutation
  backend imports or local archive fallback. Pure request/bootstrap extraction
  retains service compatibility exports and existing domain mode/order semantics.
  Cold CLI imports load no archive/Hub/storage executors. Default job output
  preserves exact terminal server command/run identity, timestamps, warnings/
  errors, payload, partial results and domain exit priority. Show/lookup preserve
  exact server metadata Envelopes; wait returns the stored command result.
- Global detach/key/wait flags are explicit and refuse on unrelated reads/
  bootstrap; wait timeout is finite `(0,86400]`. A validated nonsecret key prints
  before POST and accepted operation ID before waiting, including quiet mode.
  Explicit detach emits schema-1 `operation_admission`, original key and validated
  acceptance, never a fabricated terminal outcome/exit. Sequenced bounded
  sanitized events report gaps; progress escapes nonprintable/control text for
  one plain stderr line and quiet suppresses it without hiding safety handles.
- Status/event/result reads and retries share one absolute observation deadline.
  Timeout/SIGINT after acceptance retains key/op/route and HFAPI019/20; unusable
  acknowledgement or interruption before it is established retains HFAPI020 and
  the original key/route. Other classified errors retain taxonomy/handles, and
  validated retained-key 5xx explicitly warns work may continue. Lookup/show/wait
  never submit, cancel or replay. Missing/interrupted history remains uncertainty.
- Initialization uses authenticated configured-target inspection, retaining the
  user-restated root and explicit confirmation. Omitted optional UUID comes only
  from the wrapper; explicit ID must match. No-confirm performs no POST, preserves
  failed server inspection exactly, or returns local HFARG003/HFMNT014 refusal
  with unchanged inspection data, `configured_archive_id`, `config_fingerprint`
  and local invocation metadata. Disabled maintenance explicitly refuses before
  POST and the server repeats its unchanged gate/strict DTO.
- Legacy compatibility review corrected local verification revision/run and
  quarantine transaction-ID grammar to retain HFARG001 before credentials/network;
  archive membership/proof stays server-owned. Four verification regressions and
  the quarantine case remain covered. A private-worker crash now yields observed
  HFAPI015/20 plus operation handle rather than a local escaping exception;
  archive/catalog/report preservation and later verification checks remain.
- Focused command:
  `rtk uv run --locked --extra server pytest tests/unit/test_cli_operation_helpers.py -q`
  passed 26 tests in 1.13 seconds. Earlier helper/client selection passed 148 in
  1.73; shared service/locking/query/preflight checks passed 87 in 8.38. Root's
  write route/flag/cold-import/no-fallback cases passed 44 in 11.60. Released
  verification/crash/services checks passed 159 in 71.56; readonly/init/quarantine
  173 in 64.68; CLI reader/no-fallback 28 in 4.69; operation adversarial 8 in 5.70,
  with the strengthened cursor/newline/ESC case separately 1 in 2.10. The fixture
  exercises real peer-checked framed Unix IPC and guarded verification services
  in a threaded test worker; it is not installed cgroup/no-IP proof.
- Definitive command:
  `rtk proxy bash -c 'bash scripts/check.sh > .scratch/api-013-gate.log 2>&1'`
  exited 0 on its first full attempt. Lock check/server-extra sync passed;
  351 files were formatted, Ruff passed, Pyrefly reported 0 errors (11 suppressed,
  55 hidden warnings). Python passed 3,031 tests, 40 deselected, in 303.11 seconds.
  Version 0.1.10 sdist/wheel built; actual locked isolated base/server wheel
  installation/import/help/version checks passed. Cockpit eslint/stylelint/types,
  45 tests (0 failures/skips) and production build passed. No gate failure,
  correction, retry or post-freeze source change.
- Reviewed INV-006/012–015, AD-16/17, TX-07 and existing output/credential/lock/
  recovery/offline contracts. Decision 120 and amendments AD-16/17, 114/117/118/
  119, original plan §11, CLI/client/API/server/security/configuration/architecture/
  invariant/operations/recovery, README and Unreleased agree. Archive algorithms,
  durable shapes, dependencies, whole-archive roles and MCP gate are unchanged.
- Final local links/task dependencies/current/parity, all 120 unique indexed
  decision/ADR records and whitespace audits pass. All 29 HTTP parity rows retain
  explicit source/test evidence. The completed [progress audit](../../progress.md)
  accompanies this task. Current selects API-014 pending, which cannot start
  before this commit exists. No production archive operation, deployment, push,
  merge or tag; live/NFS/installed-host and additional build-marker suites did not
  run. Actual unit/cgroup/credential/no-IP proof, shipped caller integration and
  full REST acceptance remain later explicit work.
