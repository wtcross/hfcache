# WEB-025: Deprecate legacy Cockpit and hand off the independent web UI

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P6 |
| Depends on | [WEB-024](web-024-human-documentation-acceptance.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-025: <completed outcome>` |
| Model / effort | `gpt-6.1-sol` / high |

## Execution approach

Apply the [shared bounded-testing policy](../support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort).
Latest user amendment (2026-11-01): “ignore the cockpit plugin moving forward”
and deprecate it once the new web UI is complete. This supersedes this task's
previous exhaustive retirement, plugin-testing and harness-porting scope.
Use existing actual new-web/release evidence for independence and a concise
deprecation handoff. Routine edits use low effort; investigate only a concrete
new-web dependency or safety contradiction. Add no replacement test framework.

## Read before implementation

Completed new-web parity, release and functional/compatibility evidence; migration
guide and existing human navigation. No new legacy plugin inventory is required.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Record Cockpit as deprecated legacy once the new web UI is complete. Preserve
its source, tests, history, licenses, old immutable artifacts and live installed
state. Preserve generic fixed CLI clients, runtime helpers, shared policy/lock
identities and all required new-web safety coverage.

Require the web/backend gate for new work; make obsolete plugin-gate handling
clear rather than silently skipping a requested check. Perform no further plugin
validation, exhaustive retirement inventory, harness ports, dependency cleanup,
source deletion or live uninstall. Preserve backend-only profiles and generic
clients. Required new-web behavior remains independently tested.

RELEASE-08 remains the new web UI's independence requirement at its existing
minimum layers. Reuse the actual indexed web artifacts, installed workflows and
matching source evidence; it does not require an uninstalled/absent legacy
package or another full browser matrix. A legacy link or future feature cannot
substitute for a required new screen/action or legitimate profile-specific denial.
Preserve original handles/candidates through safe lookup, never adoption/replay.

## Unit and component validation

Validate changed current gate/help behavior and the relevant independent web
source/build boundaries. Reuse matching existing new-web safety checks; do not
test or port the preserved legacy plugin.

## Integration validation

Use existing indexed artifact/import/runtime evidence that the web UI and generic
clients do not depend on the plugin. Required web/backend/doc/build checks remain;
no plugin removal or legacy dependency cleanup is part of validation.

## Functional validation

Adopt matching actual native/rootless web workflows and release evidence for
RELEASE-08 independence. Retain required profile denials, original-handle recovery
and compatibility proofs from the preceding tasks. Repeat only a concretely
changed or missing new-web assertion; never replay an accepted operation.

## Human documentation deliverables

Finalize accurate migration/navigation and deprecated-legacy annotations, current
gate help and operator handoff. State that preserved source/history/licenses and
the live installation remain; no uninstall or production migration is performed.

## Acceptance

The new web UI operates independently with evidenced required behaviors, while
Cockpit is explicitly deprecated and preserved as legacy material. No plugin
retirement inventory, validation, code/test port or live uninstall is required.

The task requires the current web/backend `scripts/check.sh` gate and scoped
independence evidence above. All95 underlying new-web behaviors and minimum
layers remain; this user amendment supplies no pass or fabricated execution.
Update mappings using actual checks or explicitly scoped retained evidence.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-025, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.
