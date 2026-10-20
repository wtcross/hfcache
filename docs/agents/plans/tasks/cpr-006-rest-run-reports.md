# CPR-006: Move run-report browsing onto the existing REST routes

| Field | Value |
| --- | --- |
| Status | completed |
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

**Executed:** V41–V45 and report portions of V48/V51. Exercise the actual CLI over temporary Unix sockets,
including multiple pages, stale cursors, oversized data, unexpected run UUID/ID,
invalid selectors, missing reports and no-local-archive-access assertions. Verify
report UI shapes and bounded journal failures. Run the full gate.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

Started 2026-10-20 after committed CPR-005 `896003d` with clean source and its full
gate passed. Sole active package. Existing report GET routes and ApiClient
schema/pagination/identity behavior were revalidated. Repository-allocated
decision136 freezes one-page list/exact-ID detail, original Envelopes and a
separate bounded seven-field metadata notice before implementation. Actual
subprocess/private-UDS regressions pass with client archive/config opens denied;
missing-command and missing-schema red evidence is retained. Mounted report and
bounded independent journal regressions are being completed before removal of
the old privileged report-file APIs. Final mounted parity passes71/71 and the
old reader is removed; static regression changed from2fail to2pass. Repeated
row-click concurrency and an initial journal-view effect race were reproduced
and repaired. The first complete gate failed1/5234pass because the independent
REST parity reference still called the run routes SDK/HTTP-only. Additive CLI
semantic modes retain44HTTP rows and all old SDK evidence; focused167passed.
The corrected full gate passed with actual frontend execution. Next ready task
is CPR-007. Current-source real Cockpit/PAM V54 remains required for CPR-008;
no production/guest inspection or mutation occurred in this source package.
All prior operation/configuration/profile boundaries, host-local journal
independence and historical deployment holds remain.

## Completion evidence

Completed2026-10-20, CPR-006, this commit. [Gate evidence](../support/cockpit-rest-repair/gates/cpr-006.txt)
retains the initial failure and final exit0:5241passed/42deselected in683.23s,
three locked wheel profiles, actual frontend lint/style/types/495unit/71mounted
cases/build. Explicit make check also passed before the final detail latch;
the full final gate covers that repair. CLI/client168, parity167, report/runner90,
journal/static/events/stream30 and command10 focused cases pass. Real subprocess/
private Unix-socket runs deny client archive/config access, preserve exact success/
failure Envelopes and enforce identities/bounds without jobs. Actual mounted
baseline modules and static legacy-reader checks were observed red then green;
the final UI never reads archive files or relies on journals for report outcome.
Reviewed INV005/006, affected CPs and ADR122/134/135, accepted actual nextADR136;
amended index/status/CP01/09 and all CLI/API/client/schema/security/operator guides.
No dependency/durable/API/MCP authority change. [Acceptance](../support/cockpit-rest-repair/acceptance-record.md),
completed progress entry and Operator handoff27 retain V54/installed uncertainty.
Continue [CPR-007](cpr-007-read-results-and-diagnostics.md); plan stays active.
