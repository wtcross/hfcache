# CPR-006: Move run-report browsing onto the existing REST routes

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-005 — Align manual operations and guarded host controls](cpr-005-rest-operations-and-host-controls.md) |
| Work package / commit | `CPR-006` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Add narrow typed read-only CLI `runs list` and `runs show RUN_ID` adapters over
existing GET /api/v1/runs and /api/v1/runs/{run_id}. These CLI subcommands are new;
freeze their exact output and pagination behavior first. Use ApiClient validation,
resource limits and identity checks, retain server Envelopes and error classifications,
and reject arbitrary path/URL/method input. No backend report route or artifact-byte
endpoint is needed unless a demonstrated defect in the existing read implementation
requires a narrowly scoped correction.

Change the plugin report adapter and report view to use those commands. Adapt
filenames/raw report assumptions to run metadata/ID and documented data shapes;
separate ReadResponse wrapper from terminal Envelope and report payload. Offer
bounded pagination/loading with explicit cursor/limit/refusal behavior. Do not
silently truncate or accumulate an unlimited report inventory.

Remove privileged direct report ls/cat under /srv/hfcache/runs after parity passes.
Retain an optional bounded, clearly host-local journal diagnostic with explicit
byte/line/time limits, literal validated run-ID correlation, and truncation state.
Journal unavailability must not prevent REST report reads and cannot define
execution outcome. Retire CP-09's report exception through an explicit amendment.

## Acceptance criteria

F08 is fixed: report listing/detail is authenticated REST-backed and works without
client-side archive access. Empty, paginated, corrupt, wrong-identity and missing
reports are distinguishable. Direct host archive report reads are absent from
production plugin code, and journal resource use is bounded and diagnostic-only.
No new arbitrary command/URL/path surface or browser token appears.

## Contracts, invariants and ADRs

Amend CP-01/09, ADR122, CLI/API client route mapping, Cockpit reports and
troubleshooting/installation docs. Preserve INV-005/006, exact report/run identity,
whole-archive authorization and the independent NFS artifact-byte path. Update CLI
help/schema/parity documentation in the same commit as the added commands.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

**Planned, not executed:** Cover V41–V45, V48 and V51. Exercise the actual CLI over temporary Unix sockets,
including multiple pages, stale cursors, oversized data, unexpected run UUID/ID,
invalid selectors, missing reports and no-local-archive-access assertions. Verify
report UI shapes and bounded journal failures. Run the full gate.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

Not started. On activation/resumption, record source drift, exact implementation
scope, relevant runtime cause evidence, and any blocker with its unblock condition.
Do not rewrite this section as completed merely because the plan was extracted.

## Completion evidence

Pending. Replace with the completion date, accepted test/fixture results, executed
gate evidence, invariant/ADR review outcome, changed docs, remaining operator
handoff, and the corresponding completed `docs/agents/progress.md` entry. Before
commit use `CPR-006, this commit`; after commit, record only actual git evidence.
