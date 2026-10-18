# API-012: Move CLI reads and candidate validation/planning onto the API

| Field | Value |
| --- | --- |
| Work package | `API-012` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-011](api-011-typed-client-and-client-config.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-012: migrate CLI reads and candidate previews to REST` |

## Scope and acceptance

1. Migrate status/list/inspection/estimate, installed config validate, plan, read-only diagnostics, and report/reference reads to the typed client. Preserve names/selectors, existing schema-1 data semantics, warnings, human rendering, and one-envelope output. Walk API pages rather than silently truncating inventory.
2. Keep local version/help and add `version --server`. Implement explicit `config validate --local` for offline bootstrap without an API fallback. Distinguish local failures from server-reported domain failures while retaining the established exit classifications.
3. Implement explicit `--config` candidates for API validate/plan: read bounded local content, submit TOML content, and never send a path for server interpretation. Validate candidate syntax separately from running-writer compatibility. Require installed authority fields to match before Hub planning, resolve only installed credentials, and refuse credential/endpoint redirection.
4. Reject `--config` for other API runtime commands and reject legacy Hub `--token-file` for API operations with actionable migration messages. No reader command reads local archive data when the server is unavailable. Update shipped caller assumptions as the later integration tasks complete.

## Contracts, invariants, and ADRs

`INV-001`/`INV-002`/`INV-006`, `AD-21`, `CP-11`; plan §7.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update CLI option/command examples, candidate contract and intentional restrictions, API-client migration table, configuration docs, consumer setup, and README. Document `--local` as an explicit local bootstrap exception, not an alternate operating backend.

## Validation

Planned checks, not execution evidence:

CLI CliRunner tests backed by HTTP transport and throwaway server; legacy JSON/human snapshots; all selector/type/revisions modes; config missing on reader; all pages included; same candidate preview as installed-authority policy; malicious endpoint/root/credential candidate refusal before any Hub call; version/help offline. Run `scripts/check.sh`.

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

Implementation continues under Tyler's authorized active plan after API-011
completed in `0207dbd`; git, dependency and current selector were reconciled before
starting. API-012 is the sole task in progress. Collaborators share read CLI/
rendering/transport fixtures, candidate HTTP/services/client support, adversarial
reader/candidate tests and all Markdown contracts/records. Decision 119 was next
in the actual log; implementation/completion dates use 2026-10-18.

Contract-first choices preserve exact server Envelope identity/timestamps and one
terminal rendering, complete inventory/revision pagination and explicit consistency
refusal. Remote inspection needs no local path; optional `--archive-root` only
restates/checks the returned root, with legacy command `archive init`. Help/local
version and explicit `config validate --local` stay independent bootstrap paths,
never API fallbacks. Other API reads reject explicit legacy archive config and Hub
token overrides.

Candidate validation separates syntax/policy validity from compatibility; valid
incompatible candidates remain valid with false compatibility/fixed mismatch names
and no credential resolution. Candidate planning compares all six installed
authority fields, then runs candidate repository/policy intent with installed
credentials. Its key/receipt retains installed admitted fingerprint; adding an
optional candidate field must preserve the old installed-plan canonical digest.
No configuration install, MCP, production operation, deployment, push, merge or
tag. A required unavailable-local-API test exposed a failed Unix-connect socket
leak in already-locked HTTPCore 1.0.9. Decision 119 records the FW-04 rationale
for declaring it directly (`>=1.0.9,<2`) and using public HTTPX transport/HTTPCore
pool/network interfaces with explicit descriptor ownership. No new package or
version upgrade, private pool mutation, IP fallback, global patch or warning
suppression is allowed. Completed acceptance and definitive gate evidence follow.

The baseline has no separate report/reference/manifest CLI command families;
their existing authenticated typed-client reads and consumer discovery remain
available without inventing commands. This package migrates the actual baseline
reader modes, adding `version --server`, and retains explicit local validation.
Inspection's non-inspect missing-root usage error stays exit 2; remote inspection
is path-free. Inventory reconstruction bounds accumulated rows across base and
revision pages, preserves empty/unmanaged repositories and checks current SHA/
publication identity, membership, counts and ordering before rendering.

Source review covers INV-001/002/006/008/012–014, AD-21, CP-11 and FW-03/04.
Decision 119 amends 087/108/112/116/118, AD-21 and the framework record. Candidate
validation has explicit unknown compatibility when installed policy is invalid;
candidate planning rechecks all six fields after waiting, including credential
name excluded from fingerprints. Exact candidate text binds keys; explicit null
is refused while the absent field preserves historical installed-plan digests.
All 29 HTTP parity rows are implemented; mutating CLI/operation UX, installed
host/Cockpit integration and REST/MCP acceptance retain their later task gates.

Focused candidate command
`rtk uv run --locked --extra server pytest tests/unit/test_api_candidates.py tests/unit/test_api_candidates_adversarial.py -q`
passed 55 tests in 7.28 seconds (7 core, 48 adversarial), including malicious
authority proposals, explicit null, deep TOML recursion with safe HFCFG002 domain
Envelopes and old canonical-body compatibility. The released adversarial file
separately passed 48 in 6.58 seconds; explicit-local validation passed 25 in 0.84
and migrated read-only CLI tests passed 84 in 16.65. An earlier model/client/legacy
selection passed 284 in 13.48. Root transport/CLI integration and the definitive
gate were still pending at that focused checkpoint.

Root's final CLI integration selection passed 28 tests in 3.61 seconds, covering
all nine reader modes without local writer loaders, exact first-Envelope evidence,
complete pages/aggregate bounds, unmanaged/empty repositories, same-SHA changed
publication refusal, content-only candidates and unavailable API without fallback.
The unavailable Unix socket exposed the real dependency descriptor bug described
above; it was fixed through `unix_http.py`, not a warning filter. The released
transport selection passed 20 tests in 0.55 seconds, and existing real Unix/TCP/
TLS tests passed 3 in 2.14. Failed creation/option/connect/timeouts, connected
read/write failures and response completion/early exit/error release owned
resources even while exception tracebacks remain alive. Legacy read migration
checks reached 383 passes with two fixture-overlap assertions; control-state
placement and volatile free-space comparison were corrected, then all 13 query
cases passed. These were fixture corrections before the full gate, not archive
or production failures.

## Completion evidence

Completed 2026-10-18, this commit.

- Actual CLI reader modes now use the authenticated typed client: status/list,
  path-free inspection, estimate, installed/candidate validation, planning,
  read-only diagnostics and explicit server version. Reader setup requires no
  archive TOML/mount, writer service identity or Hub credential. API failure never
  falls back to a local archive. Help/local version and explicit local config
  validation remain independent bootstrap paths. Non-inspect missing root keeps
  usage exit 2; incompatible legacy flags refuse before candidate/file access.
- Remote output preserves exact server Envelope command/run ID, timestamps,
  warnings/errors/outcome/application exit and data. Complete page reconstruction
  retains first invocation metadata and finite aggregate bounds. Inventory joins
  preserve empty/unmanaged rows and refuse changed SHA/publication identity,
  missing membership, duplicate/count/order and policy inconsistencies. No new
  report/reference/manifest CLI families were invented; typed reads and consumer
  discovery retain their existing boundaries.
- Writer candidates are bounded content, never a server pathname. Validation
  separates syntax/policy validity from false or unknown installed compatibility,
  returns safe fixed mismatch names and resolves no credential/Hub/probe.
  Compatible candidate plans use installed credentials and admitted fingerprint
  after a fresh six-field authority check, including credential name excluded from
  fingerprints. Invalid/incompatible plans retain durable 202 admission followed
  by ordered safe classified terminal errors. Exact text binds keys; explicit
  null refuses while absent candidate preserves old installed-plan digests.
  Configuration installation/backups remain privileged host work.
- The required unavailable-local-API case exposed a real HTTPCore failed-connect
  socket leak before the full gate. The public Unix-only HTTPX/HTTPCore adapter
  owns failed/timed-out sockets, connected read/write failures and response-stream
  cleanup. Maintained HTTPCore still owns HTTP framing/pooling; TCP/TLS stays on
  HTTPX. Direct `httpcore>=1.0.9,<2` retains locked 1.0.9 with no new package or
  version upgrade. No private pool mutation, global patch, IP fallback or warning
  suppression. Warnings-as-errors remains enabled; failure tests retain tracebacks
  while proving descriptors close.
- Focused command:
  `rtk uv run --locked --extra server pytest tests/unit/test_api_candidates.py tests/unit/test_api_candidates_adversarial.py -q`
  passed 55 tests in 7.28 seconds (7 core, 48 adversarial). Released read-only CLI
  tests passed 84 in 16.65 seconds; explicit-local validation 25 in 0.84; root's
  final CLI integration 28 in 3.61; transport lifecycle 20 in 0.55; real Unix/TCP/
  TLS client 3 in 2.14. Prior model/client/legacy selection passed 284 in 13.48.
  Two legacy fixture-overlap assertions were corrected before the gate, followed
  by all 13 query tests passing; these do not hide a product or gate failure.
- Definitive command:
  `rtk proxy bash -c 'bash scripts/check.sh > .scratch/api-012-gate.log 2>&1'`
  exited 0 on the first full attempt. Lock check/server-extra sync passed;
  345 files were formatted, Ruff passed, Pyrefly reported 0 errors (11 suppressed,
  55 hidden warnings). Python passed 2,953 tests, 40 deselected, in 195.16 seconds.
  Version 0.1.10 source distribution/wheel built; locked isolated base/server
  installation/import/help/version checks passed. Cockpit eslint/stylelint/types,
  45 tests (0 failed/skipped) and production build passed. No full-gate failure,
  correction, retry or post-freeze source change.
- Reviewed INV-001/002/006/008/012–014, AD-21, CP-11 and FW-03/04. Decision 119,
  amendments 087/108/112/116/118, AD-21/framework records and affected CLI/client/
  API/configuration/security/server/architecture/invariant/consumer/Cockpit,
  README/plan/Unreleased contracts agree. Direct HTTPCore use has recorded FW-04
  correctness rationale; no durable archive/control-state schema, domain algorithm,
  writer authority or MCP change. All 29 HTTP parity rows are implemented.
- Final local-link/task-dependency/current/matrix, all 119 numbered decision/ADR
  records and whitespace audits pass. The completed
  [progress audit](../../progress.md) accompanies this task. Current selects
  API-013 pending; it cannot start before this commit exists. No production
  archive operation, deployment, push, merge or tag; live/NFS/installed-host and
  additional build-marker suites did not run. Installed caller/host proof and the
  full REST acceptance gate remain explicit later work.
