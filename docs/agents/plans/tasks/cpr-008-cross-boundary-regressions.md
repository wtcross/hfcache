# CPR-008: Prove the browser, launcher, CLI, and API boundaries

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-007 — Render every failed read and expose accurate readiness](cpr-007-read-results-and-diagnostics.md) |
| Work package / commit | `CPR-008` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Complete the layered test harness, using existing project test conventions and
only recorded build/test dependencies. Layer one is pure error/Envelope/state
logic. Layer two mounts actual React surfaces with controllable documented Cockpit
promise/stream/close behavior. Layer three launches the actual installed CLI wheel
against a temporary Unix-socket API with deterministic synthetic backend fixtures.
Layer four proves the real Cockpit privilege bridge -> transient systemd -> fixed
rootless launcher -> CLI -> API chain in a provisioned disposable environment.

Exercise candidate write/validate/conditional sizing/install/confirm, including
connection transitions at each boundary, escaped large TOML and negative API
Envelopes. Use temporary configuration/state and synthetic credentials only.
Exercise tab unmount and reload during all representative jobs, especially
maintenance Apply, and assert exactly one original submission per deliberate action.
Verify preserved output bounds, credentials separation, exact identity and
no-cancellation behavior under split/truncated streams.

For the disposable real-runtime layer, bind no NAS/live archive and do not reuse
production credentials, unit names in the production manager, mounts or protected
release paths. Use a disposable host/containerized system environment with explicit
fixture ownership. Record supported Cockpit/systemd/Podman/toolchain versions and
physical release/image identities. This layer must not be described as production
acceptance. An unavailable environment is an explicit blocker, not a reason to
substitute a fake and label it PAM proof.

Add gate wiring so this plan's frontend checks cannot silently skip. Keep routine
offline tests deterministic; clearly mark/environment-gate real disposable runtime
checks separately. No live/nfs workloads are invoked in this task.

## Acceptance criteria

Every mandatory V01–V59 automated expectation has concrete test/evidence references;
UI lifecycle, actual CLI/socket and disposable real-runtime proof are distinguished.
The synthetic failure matching the reported symptom has a passing correction test.
Any deployed-cause claim is limited to evidence actually obtained. Skipped or
unavailable required checks block the corresponding acceptance rather than count
as passes.

## Contracts, invariants and ADRs

Review docs/development.md, Cockpit test/acceptance contract, CP-02/03/08/11/13/14,
INV-006, fixed container boundaries and relevant existing integration tests.
Record any test-only dependency decision and update development instructions.
Never loosen a production contract for test convenience.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

**Planned, not executed:** Run the full matrix and existing suites under pinned Node/pnpm and locked Python
server+MCP profiles. Capture exact commands, counts, versions and fixture identities.
Run scripts/check.sh with actual Cockpit stage and make -C cockpit check. Preserve
old durable fixture compatibility. Run the disposable real Cockpit chain when
provisioned, otherwise retain its blocked evidence and do not mark this task complete.

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
commit use `CPR-008, this commit`; after commit, record only actual git evidence.
