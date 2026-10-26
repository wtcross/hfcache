# WEB-015: Implement repository configuration and tag management workflows

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-014](web-014-safe-markdown-rendering.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-015: <completed outcome>` |

## Read before implementation

Config read/validate/plans/applications; typed managed edits; detail/Library selections; original-operation controller; tag normalization.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build structured global/repository forms and a safe supported advanced view from the server editable projection. Add model/dataset entries, change supported settings, enable/disable/remove configuration and edit tags from detail or Administration. Display canonical tag normalization/suggestions and limits. Historical unmanaged tags are not directly editable; explain reconfiguration. No separate annotations store or tag CRUD endpoint.

Use one dirty draft, reviewed diff, exact base revision, validation and required sizing preview before Apply. Invalidate readiness on every edit and stale server revision. Preserve protected fields through server managed edits; never serialize redaction markers as real values. Removing/disabling config is not purge; changing retention is not immediate deletion. Distinguish authority changes requiring manual provision/restart from invalid syntax.

Integrate application receipt/confirmation and read-only uncertainty reconciliation. Concurrent tabs/config writers get an actionable compare/reload/re-edit conflict; do not auto-merge silently or overwrite unseen tags. Navigation warns about unsaved draft; no persistent TOML storage by default. Error codes map to fields where safe and remain visible independently of transport failures.

## Unit and component validation

React tests cover add/edit/remove forms, tag normalization/duplicates/max, hidden protected values, dirty navigation, validation invalidation, preview/apply button gates, failed Envelopes and historical-tag read-only behavior.

## Integration validation

Run the UI client against actual helper/config endpoints for ordinary/tag-only/global edits, wrong permissions, missing preview, stale base and install-unconfirmed states. Validate final exact configuration with backend models.

## Functional validation

Three-browser Caddy workflows add model/dataset with tags, preview/apply and verify detail/facet updates; concurrently edit tags in two tabs; preserve conflict and unknown apply; disable/remove a repository and prove archived bytes remain.

## Human documentation deliverables

Complete configuration-and-tags.md with step-by-step flows, conflict examples, exact success criteria, side effects and manual authority-change limits. Update troubleshooting and UI guide screenshots.

## Acceptance

Tags and configuration are genuinely manageable through the SPA with the same guarded apply pipeline, correct provenance and no lost protected data or false install success.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Not started. Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

## Completion evidence

Not executed; no acceptance is claimed by this draft. On completion, replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-015, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.

## Browser-control compatibility input

Prior renderer diagnostics prove that native `select` creation in the owned
WebKit27.2 engine attempts inline style under the application CSP (diagnostic
/var/tmp/web-014-validation-xowemz0k/csp-diagnostic1-evidence.json). Recovery
choice groups are corrected with radios in the preceding package. Configuration
and Library editing must use CSP-compatible choice controls and exercise actual
CSP observations; review the five existing Library selectors during this scope.
Do not relax CSP or manufacture permissions/readiness to accommodate a control.
