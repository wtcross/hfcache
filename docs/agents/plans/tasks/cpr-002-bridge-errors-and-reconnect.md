# CPR-002: Classify bridge failures and repair connection lifecycle

| Field | Value |
| --- | --- |
| Status | completed |
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

Executed normalization/runner/owned-connection and actual mounted component tests
for the boundary/lifecycle portions of V01–V08/V34/V49/V51. Existing stream,
Envelope, UTF-8 and no-cancel regressions pass. Scope qualifications, fail-before
results and final full/frontend gate counts appear in completion evidence below.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

Started after CPR-001 commit b40b443. Source baseline defects reproduced in
pure and mounted fixtures. Implement normalized failure/stage preservation and
owned connection/read lifecycle; no installed cause is yet established. Collaborating
agents share only this work package: runner/errors, browser regressions, and
connection/UI integration. No other CPR task is in progress.

## Completion evidence

2026-10-19, CPR-002, this commit: F01/F06 boundary and read-lifecycle repairs
complete. Full `rtk proxy scripts/check.sh` exit 0: 5008 passed/42 deselected
in 656.48s, three locked wheel profiles, actual frontend frozen install/lint/
style/types, 221 unit tests (0 failed/skipped), 12 mounted Firefox cases and build.
Explicit `rtk make -C cockpit check` also passed. Before/after failures and focused
63-test boundary results are recorded below. Documentation alignment passed.
Review CP-02/03/05/08/10/13, INV-006, decisions122/127/133/134; preserve all
CP-01–14 and existing host controls. Contracts/ADR134 and122 amended for safe
presentation, finite connections and negative confirmation evidence. No new
application dependency, durable schema or API authority. Runtime prep record
captures twelve authorized development RPM additions and isolated boot/SSH;
production hfcache and NAS remain unchanged. No original installed root cause
is claimed. [Acceptance record](../support/cockpit-rest-repair/acceptance-record.md),
[progress](../../progress.md). Next: CPR-003, including known higher pipeline gaps.

### Implementation evidence in progress

Bounded failure normalization preserves stage, known problem/status/signal and
original safe handles from Error/plain objects; raw diagnostics/unknown values
are withheld. Exact nonzero Envelopes still resolve unchanged. Application-owned
D-Bus clients close/dispose/invalidate and retry reads finitely. Sequential polls
clear stale state and reject old generations. Privilege transitions disable host
controls and candidate readiness without repeating mutations. Portal buttons have
individual privilege gates. Root config/schedule adapters now classify their stage;
schedule continuation checks the same session between effects.

`rtk make -C cockpit check` passed with actual mounted Firefox tests (9 cases),
pure failure/runner/connection tests, lint/style/typecheck and production build.
Exact reviewed baseline mounted harness: `rtk node cockpit/test/browser.mjs
dcc2c562b52304541d0cb85d20fc046072038e79` exited 1, 3 passed/6 failed; working
tree all 9 passed. Existing generation/no-replay behavior is retained, not claimed
new. The final full repository gate passed; see completion evidence.

Known next-package boundary: the higher configuration pipeline still wraps some
install errors and drops superseded preparation evidence; CPR-003 owns that repair.
The new boundary model itself preserves original classified facts. Persistent
operation registry and uncertain Apply remain CPR-004 scope. No installed cause
or real PAM proof is claimed by the mounted fixture.

The user-authorized local-host test environment preparation reached boot/SSH
in an independent KVM guest and is paused; production installation/credentials/NAS/guards are not
a test surface and remain unchanged. Exact prerequisite mutations and guest
identities are recorded in runtime-setup.md.


Final review repairs: ScheduleEditor now withholds old override evidence across
session transitions and requires a fresh successful read for controls; failed read
is explicitly unavailable. Expanded mounted harness failed 2 schedule cases before
that fix (10/12 passed), then passed all 12 including modal portal privilege loss.
D-Bus disposal failures cannot suppress invalidation. A new confirmation regression
failed before the runner change: valid HFAPI003 confirmation Envelope was replaced
by process-postcheck. It now remains exact failed evidence; apparent successful
stdout with a failed process still refuses. Focused runner/failure/connection:
63 passed. These source changes land in this boundary package; higher candidate
pipeline preservation remains the next package.

[Local diagnostic infrastructure](../support/cockpit-rest-repair/runtime-setup.md)
is now provisioned to boot/SSH only and paused. Twelve reviewed signed prerequisite
RPMs added, zero upgrades/removals; independent QEMU guest with synthetic credentials,
no default route/NAS, host loopback-only forwards, both SELinux enforcing. Existing
production app was neither removed nor changed. Guest Cockpit368/Podman6.1 are
preinstalled inputs, not proof of parity with recorded host364/6.0. V54 unpassed.
