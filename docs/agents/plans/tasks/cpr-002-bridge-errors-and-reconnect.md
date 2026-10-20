# CPR-002: Classify bridge failures and repair connection lifecycle

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-001 — Freeze the baseline, reproduce failures, and amend contracts](cpr-001-baseline-and-contracts.md) |
| Work package / commit | `CPR-002` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Implement bounded structured error normalization at the Cockpit spawn and host
adapter boundaries. Validate both Error instances and plain rejection objects;
retain safe problem/exit/signal/stage metadata and existing recovery handles.
Do not echo candidates, bearer values, arbitrary exceptions or unbounded stderr.
Update QueryError to explain host access, launcher failure, API refusal and uncertain
observation separately. Keep the original safe code available alongside guidance.

Preserve the current nonzero-process/valid-Envelope behavior and strict terminal
collector; process failure is not automatically a malformed domain result.
Keep installed-confirmation postcheck semantics distinct. Display-only aborts and
callback failures must not call process.close or cancel execution.

Replace immortal cached D-Bus usage with an owned, close-aware connection lifecycle.
Use installed-version-supported Cockpit APIs, dispose listeners, bound read
reconnect/backoff and reject stale generation results. Poll failures become
unavailable/stale state, rather than disappearing. Administrative/connection
transitions disable dependent actions until fresh evidence arrives. Never replay
a unit mutation or candidate pipeline to recover a read connection.

Apply the same stage/category model to fixed host schedule and configuration
operations. Keep system-manager selection and unit allowlists intact. Correct
actual launcher/session faults demonstrated by CPR-001 without changing the fixed
engine, credential or hardening policies; record precise cause/evidence. A renamed
error string alone is not a complete repair.

## Acceptance criteria

F01 and F06 regressions pass for real Error and plain-object rejections, including
message/problem `reconnected`. The UI identifies the interrupted stage and keeps
usable diagnostic fields without asserting an API crash. A closed D-Bus client is
replaced for subsequent bounded reads; old callbacks cannot restore stale state.
No automatic mutation, local fallback, security weakening or cancellation occurs.

## Contracts, invariants and ADRs

Update Cockpit error/lifecycle documentation and troubleshooting in the same
commit. Review CP-02/03/05/08/10/13, INV-006 and decision 122; retain decision 127's
fixed runtime boundary. Record any new error model as a presentation contract,
not a fabricated backend HFAPI code.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

**Planned, not executed:** Add pure normalization/runner tests plus adapter lifecycle and component error
rendering tests. Cover V01–V08, V34, V49 and V51. Preserve existing runner, envelope,
event and UTF-8/size-limit regressions. Execute the full repository gate with
Cockpit coverage, not merely isolated TypeScript tests.

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
commit use `CPR-002, this commit`; after commit, record only actual git evidence.
