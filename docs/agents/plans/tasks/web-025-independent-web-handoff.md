# WEB-025: Record independent web handoff

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `317a2be4f2c743a4adc0126d77c83220687cd139c5172e436655a7edf70ed433`,
original content SHA-256 `57d6ff7a9f7b05223f8bd58407081413177a073c080e67b7b2beb4c785a2af24`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P6 |
| Depends on | [WEB-024](web-024-human-documentation-acceptance.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-025: deprecate legacy UI and record web independence` |
| Model / effort | `gpt-6.1-sol` / high |

## Execution approach

## Read before implementation

Completed new-web parity, release and functional/compatibility evidence; migration
guide and existing human navigation. No new legacy plugin inventory is required.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

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

The task requires the current web/backend `scripts/check.sh` gate and scoped
independence evidence above. All95 underlying new-web behaviors and minimum
layers remain; this user amendment supplies no pass or fabricated execution.
Update mappings using actual checks or explicitly scoped retained evidence.

## Execution notes and blockers

2026-11-01: Activated after WEB-024/1d53024. Apply only proportional deprecation
notices and adopt existing actual independent web/release evidence. The earlier
exhaustive retirement preparation is superseded by the user's explicit direction.
No plugin code/test/dependency change, validation, inventory/port or uninstall.
All95 new-web behaviors/layers remain. Root preserves live state and shared
helpers/history/licenses; the required gate is strict web/backend/docs/build.

## Completion evidence

Deprecation notices are implemented in root/web navigation, the migration guide
and only the legacy guide entrypoint header. Legacy plugin code/tests/dependencies,
licenses/history, shared runtime helpers and live installation are unchanged.
README now identifies the independent web source tree. Dated ADR144/160 notes
record this accepted user-selected implementation; no new architecture is chosen.

RELEASE-08 completes at its unchanged unit/integration/functional minimum
layers. Current source/artifact join `.scratch/web-025-validation/current-source-artifact-join1.json`
SHA `58ec1d28280f2283f98dd3e85476fcb255b861a990aab673bead40da9cb7843e`
checks nine public web/build/runtime/notice sources equal installed cleanf829.
Native indexa251b77e/UI57828b50 and rootless indexf8b03759 retain19/68 actual
payload members; no plugin payload or extra frontend server/image/Node runtime.
Whole-source provenance can retain107 legacy paths; it is not a runtime/build
execution dependency. Generic clients/helpers and attribution remain.

The actual clean source16 build evidence has SHA
`8c4f8dc6c821607c4d1db66146448cb5a88b7846efb6917b8f4c94b19751e7e1`,
source snapshotd86e9638, backend/UI reproducibility true. Its original construction
is not rerun and unretained outer argv is not reconstructed. Actual restored78
native/rootless trusted-TLS Library/reload/original-subject browser records
`47226e81…`/`55b7f0de…` are reused for independent direct API/static operation,
with original source/profile/closure and failed-script qualifications retained.
No absent/uninstalled-plugin proof or new browser matrix is claimed.

Required current Gate1 supplies passing fresh unit/integration default-gate/release-stage assertions before completion. Real bindings include native exact shipped/index
source, original schema/member capture, role matrix, actual bounded staging and
web-only runtime/authentication, backend-only install, and default omission/help
control fixtures. These last fixtures invoke fake tools, never the plugin.

Reviewed CP boundary and INV019/020/021 with ADR088/140/143/144/160. Existing
source and profile safety constraints remain; only already authorized deprecation
status changes. No runtime, durable format, dependency or privilege change follows.
All92 earlier completed cases stay intact; this case completes and two final cases remain pending. Strict web/backend/docs/build Gate1 passes before final adoption.
Production/NAS/guard/credential/calendar/unknown-handle/remote holds are unchanged.

Completed2026-11-01, WEB-025, this commit. Required Gate1 exits0/1631.925s:9650 backend/4051 combined web/16 wheel, three locked profiles, two built browsers and real API fixture;95.02% lines/90.13% branches. All1547 frozen inputs unchanged. Freeze SHA `5e8a998fa928f040c081731044319f3362726f30dd093549d81bb6617928ceb3`, result SHA `e4d19966c6cf8a18fb63e27e798662b5da346b7a7603fba8e23c07572fd3c5de`, log SHA `66126a01187ab3a47577a28c3f96cd41c143c8bff5995a0746964d87624af1a9`. Outer shadow also0; no actual legacy plugin command.

All93 completed cases retain minimum layers; final RELEASE-09/DOC-05 remain pending. Post-gate adoption changes only evidence/status/handoff documents, checked again with current docs/plan/diff validators. WEB-026 final validation and closure is next. No production/NAS/remote or live-plugin action.

Post-adoption closure1 passes0:224 human documents/29 helpers, all9 plan tests
and git diff --check. Output `.scratch/web-025-validation/closure1-shadow.log`
SHA `101e19fe620adf76e755ce173fae2cefcc5ab5881cac1e37a5da33f51e1f1294`.
Only six evidence/status/handoff documents differ from the successful source
freeze; runtime/build/gate code is unchanged. Completed progress, operator
handoff and the next-task selector are recorded in this commit.
