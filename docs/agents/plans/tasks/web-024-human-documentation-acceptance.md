# WEB-024: Complete the human operator and user documentation walkthrough

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P6 |
| Depends on | [WEB-023](web-023-compatibility-and-rollback-drill.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-024: complete human guides and workflow acceptance` |
| Model / effort | `gpt-6.1-sol` / medium |

## Execution approach

Apply the [shared bounded-testing policy](../support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort).
Effort rationale: The work is guide accuracy, representative installed walkthroughs and documentation edits.
Follow existing guides on the accepted fixture and reuse matching screenshots/results. Rerun changed or missing steps and required checks. Escalate to high for a concrete documentation/runtime mismatch affecting safe operation or necessary code diagnosis.

## Read before implementation

All human guides created in earlier packages; documentation-map.md; actual installed fixture screens and evidence; docs validator and script inventory.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Audit every user-visible workflow against real implemented behavior and guide wording: login, scopes/filters, publication/README, tag/config apply/conflict, operations and reconnect, verification/maintenance, host scheduling/denials and deployment/rollback. Fix inaccurate labels, undocumented side effects, missing stop conditions and assumptions about production permissions.

Finish human navigation from root README/docs index, cross-links to reference/runbooks, useful screenshot alt text and synthetic actual-UI screenshots. Keep technical references accurate without making users read agent plans. Document Basic credential lifetime, no app logout, whole-archive trust, blocked media, no automatic payload/Hub fetch, no job cancel, unknown history and current restricted-profile behavior.

Validate every new script is classified and every example is safe/contextual. Do not execute effectful snippets blindly. Documentation status distinguishes source availability, fixture acceptance and real deployment; no unchecked TODO or placeholder guide is published as completed. Prepare operator handoff checklist without checking production boxes.

## Unit and component validation

Run docs links/anchors/image/route/default/schema/helper inventory bad-fixture tests and safely parse operational examples without callbacks. Test documentation grep/audience rules do not exempt new human guides.

## Integration validation

Validate documented config/REST examples against actual strict parsers/routes and script help behavior. Independently compare docs matrices to actual routes and permissions, not just generated matching tables.

## Functional validation

Follow each representative human guide on the installed fixture, including an error/refusal and reconnect/conflict path. Record manual keyboard/screen-reader smoke and actual UI screenshots with fixture/version labels.

## Human documentation deliverables

This package completes and verifies documentation already delivered throughout WEB-001..023. Update README/docs navigation, all docs/web-ui guides, API/server/security/discovery/config/deployment/containers/development/script references and migration notices as affected.

## Acceptance

A human can operate and troubleshoot the UI from the guides without agent context; examples, routes, screenshots and safety statements match actual tested behavior and no production readiness is fabricated.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

2026-11-01: Activated after WEB-023/490694e. Review all human workflows against
retained actual installed observations and matching current implementation. The
finite review covers40 steps across ten guides,13 actual screenshots and19
inert code fences. Reuse existing accepted effects; no new job/Plan/Apply,
maintenance, schedule or observer action is needed. Root applies only concrete
prose/navigation/caption corrections and runs required current checks. Cockpit
maintenance/validation remains excluded by the user's latest instruction.

## Completion evidence

Final prose corrections are applied to root/docs navigation, Library/details,
configuration/card captions, web availability and Import/Observe troubleshooting.
Root reviews40 guide steps across ten guides and all13 actual published images,
keeping historical builds20/22/24/30/50, synthetic facts and mobile Files Loading
limits. Exact final document/review hashes are in
`.scratch/web-024-validation/human-guide-review3.json`.

The actual19-example check passes0 through private empty read-only NAS shadow:
`rtk proxy uv run --locked --extra server --extra mcp python .scratch/web-024-example-check1.py`.
Its source hash is `2ede4cd44edae023439608c97ef91b6c81efbe31b819d6e82a16222e7db5792d`,
result hash `63f2748d1eb71e1e0c8779065d935ffd32ba8e3f4662aa0629f01b2df34cbc42`.
Strict managed/refresh models and inert shell/TOML syntax pass with documented
placeholder handling; no effectful example is executed.

DOC01–04 complete with37 retained actual integration/installed guide-step
records and explicit unchanged-subsystem justification. Original failed exits,
named passing clauses, older-source qualifications, actual Orca/keyboard scope
and no-new-listening limits remain. No new product effect or legacy plugin
validation runs. The full web/backend/docs/build Gate1 passes before completion. All95 cases and minimum layers are retained.

The wider reference audit corrects five stale implementation-status statements
in API, security and deployment guidance: inert card rendering, recorded ACL
fixture acceptance, implemented fixed guarded writes and explicit indexed asset
staging. These describe already implemented/accepted boundaries; unreleased and
pending-production qualifications remain. The rationale is to correct stale
prose to the actual behavior, without changing authority or acceptance scope.

Reviewed INV001/002/018/019/020/021/022 and ADR140/143/145/146/152/153/154/155/156/158/159/160:
these corrections align prose with existing behavior. No runtime, durable format,
dependency, privilege, invariant or architectural choice changes; no new ADR is
needed. Production deployment-status and all actual host/NAS/remote limits remain.

Completed2026-11-01, WEB-024, this commit. Required Gate1 exits0/1625.790s:9650 backend/4051 unique combined web/16 wheel, three locked installs, two built-browser checks and real API read fixture;95.02% lines/90.13% branches. All1547 frozen files remain unchanged. Source freeze SHA `7ee51ea4aebcdec97730b0e5ab7774708a49577cbed4f442c5e9814d7592848b`, result SHA `73e2934a1e3f9445513de4333f192553f14cc746060bd12463d1829f23291c4c`, log SHA `9c5c6efa452a80c6105a0e2c1c369529ea6b4b7a79efd0a26b071f81bf52d878`. Outer shadow also exits0. No plugin commands execute.

The four DOC cases retain all three required layers, original raw results and exact source/profile reuse. All92 cases now completed; three later-owner cases remain pending. Post-gate changes are evidence/status/handoff documents only and receive focused docs/plan/diff checks. WEB-025 proportional deprecation is next; no production, NAS, remote or live-installation effect.

Post-adoption closure1 passes0:224 human documents/29 helpers, all9 plan tests
and git diff --check. Output `.scratch/web-024-validation/closure1-shadow.log`
SHA `bda6a6acda1a60c697d1cd9f8f8815819031b7e37a85edb15a9fb93db9b6f7a5`.
Only six documentation/evidence files differ from the successful source freeze;
runtime/build/gate code remains unchanged. Completed progress, operator handoff
and next-task selector are in this commit.
