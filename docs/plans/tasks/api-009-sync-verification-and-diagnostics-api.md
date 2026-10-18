# API-009: Expose sync, verification, planning, diagnostics, and validation

| Field | Value |
| --- | --- |
| Work package | `API-009` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-008](api-008-bounded-runner-and-offline-executor.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-009: expose sync verification and diagnostic operations` |

## Scope and acceptance

1. Add typed routes for sync, all verification modes, installed-config planning, config validation, and explicit read-only/probing diagnostics. Route long work through the receipt/runner contract; read-only diagnostics and plan still have Hub/resource effects and are never silently treated as local metadata reads.
2. Enforce the route capability matrix: all actual verification and probing diagnostics need the writer bearer; installed planning/read-only diagnostics are available to REST readers. Admission receipts never imply command completion. Use correct terminal Envelope classifications on failures and partial results.
3. Preserve whole-run sync ordering, reconciliation before first Hub request, continuation/stop-on-error behavior, aggregate capacity admission, producer joins, new-content verification, report IDs, and automatic retention boundaries. All verification work delegates to the offline worker.
4. Implement current-config validation without remote arbitrary-path loading. Add candidate schema hooks and authority-compatible validation primitives for API-012, but never accept a request that can select a secret file or an unapproved credential-bearing Hub endpoint.

## Contracts, invariants, and ADRs

`AD-01`–`AD-03`, `AD-17`–`AD-19`, `TX-07`, `INV-004`/`INV-006`/`INV-007`; plan §§4–6.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Complete API examples and parity rows for these operations, clarify semantic read versus probe/report-writing effects, document 202/polling and scope/mode errors, and update CLI/operations reference notes and Unreleased changes.

## Validation

Completed checks cover end-to-end shared-service sync with fake Hub, all
mode/selector failures, no-bearer/wrong-role refusal, every actual verification
mode delegated to the private executor, unavailable executor refusal, partial
sync failure/exit priority, unknown journal refusal before Hub, and lost HTTP
acknowledgement during real sync. Full gate evidence follows below.

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

Implementation continues under Tyler's authorized active plan after API-008
completed in `fac9a8d`; git and the current selector were reconciled before
starting. API-009 is the sole task in progress. Collaborators share this package:
typed command routes/models/service adapters and candidate authority primitives;
bounded authenticated POST handling and end-to-end service tests; adversarial
HTTP tests; and all Markdown contracts/records. Decision 116 records this command admission boundary in the actual progress
log and ADR index.

Contract-first review covers the affected AD-01–03/17–19, TX-07, INV-001/002/
004/006/007/012–015 and decisions 108–115. Sync still reconciles under its own
lock before Hub work, verification delegates to the private worker, and accepted
receipts never imply domain completion. Candidate hooks cannot select server
paths, credential sources or a credential-bearing endpoint outside installed
authority; the complete client candidate pipeline remains API-012. No new runtime
dependency, MCP, production archive/listener/host operation, deployment, push,
merge or tag is authorized. Completion evidence remains pending the actual gate.

Contract/model review settled strict typed bodies, installed configuration order,
canonical sorted/deduplicated `TYPE:ID` selection (valid unused SHA suffixes do not
override configured revisions), explicit diagnostic mode and private verification.
Eight matrix rows now have HTTP evidence (17 implemented / 12 planned). Shared
grammar errors retain HFARG001/422; generic type/shape failures use HFAPI006/422.
Candidate HTTP remains reader 403 / writer unknown-field 422; the pure hooks
perform bounded syntax validation and six fixed authority comparisons only.
Trusted startup `--hub-token-file` is separate from global CLI/API bearer input.
Strict primitive selector validation was corrected during focused work. Fixture
and expectation corrections retained the existing domain code/exit contracts,
including HFARG001 grammar refusals and partial integrity priority. Source/docs
then froze before the first full gate; no gate attempt failed or required a fix.

## Completion evidence

Completed 2026-10-17, this commit.

- Typed strict models and explicit routes implement sync, installed plans,
  explicit read-only/probing diagnostics, installed validation and new/full/
  revision verification. Static writer authorization precedes body reception;
  mixed-route capability precedes DTO validation. Strict bounded media, encoding,
  Unicode, duplicate-key, depth, shape and chunked-byte handling never echoes input.
- Four job routes require durable canonical keys and return admission-only 202
  with prefixed Location/status/result/event links. Sixteen simultaneous equivalent
  retries admit/probe/execute once; matching retries precede changed policy or
  unavailable verifier checks. Selector sets normalize without changing installed
  revision/configuration execution order. All readers share history, while key
  lookup remains credential-class scoped.
- Real fake-Hub sync publishes and reobserves without another download; unknown
  journals refuse before Hub contact. Partial results retain domain exit priority.
  Lost HTTP acknowledgement keeps the real sync producer/flock joined, permits
  key lookup and yields one exact result/publication/download. All actual verify
  modes use the private executor with unchanged exact Envelope classification;
  absent execution isolation refuses without an in-process fallback.
- Installed validation is a bounded immediate query, preserving classified
  policy/credential failure Envelopes without Hub/probes. Trusted startup
  `--hub-token-file` or the installed systemd source is the only Hub authority.
  Candidate hooks perform pure bounded TOML/schema validation and six authority
  comparisons; current candidate HTTP remains reader 403 / writer 422. Candidate
  CLI/Cockpit integration remains API-012.
- Focused command:
  `rtk uv run --locked --extra server pytest tests/unit/test_command_models.py tests/unit/test_runner.py -q`
  passed 55 tests in 2.04 seconds. The released adversarial HTTP suite passed
  109 tests in 9.40 seconds; root's real HTTP/domain/bootstrap selection passed
  19 tests in 3.42 seconds. These checks precede and are included in the gate.
- Definitive command:
  `rtk proxy bash scripts/check.sh > .scratch/api-009-gate.log 2>&1`
  exited 0 on its first full attempt. Lock check/server-extra sync passed;
  321 files were formatted, Ruff passed, Pyrefly reported 0 errors (11 suppressed,
  54 hidden warnings); Python passed 2,473 tests, 40 deselected, in 137.10 seconds.
  Version 0.1.10 sdist/wheel built; locked isolated base/server wheel installation,
  imports, help and version passed. Cockpit eslint/stylelint/types, 45 tests
  (0 failures/skips) and the production build passed. No gate-cycle fix or rerun.
- Reviewed AD-01–03/17–19, TX-07 and INV-001/002/004/006/007/012–015: immutable
  complete observations, pre-Hub reconciliation, aggregate capacity, retention,
  continuation, joined producer lifetime, exact report identity and classified
  results remain unchanged. Decision 116 and amendments to 108/112/115 record
  the HTTP/credential/candidate boundary; invariant enforcement links, architecture,
  API/server/configuration/security/CLI/operator contracts, README, plan and
  Unreleased agree. No durable shape or dependency changed; no additional
  compatibility drill was needed for wire-only DTOs/pure hooks.
- Final local-link/dependency/current/matrix, all 116 numbered decision/ADR and
  whitespace audits pass. Matrix: 17 implemented / 12 planned. The completed
  [progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17)
  records the package; current selects API-010 pending. Live/NFS/installed-host
  and extra build-marker checks did not run. No production listener/archive
  operation, deployment, push, merge or tag; no new operator action is required.
