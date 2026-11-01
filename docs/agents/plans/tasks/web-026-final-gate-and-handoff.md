# WEB-026: Close the implementation with complete evidence and an operator handoff

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P6 |
| Depends on | [WEB-025](web-025-retire-cockpit-plugin.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-026: complete final validation and operator handoff` |
| Model / effort | `gpt-6.1-sol` / medium |

## Execution approach

Apply the [shared bounded-testing policy](../support/web-ui/testing-strategy.md#web-023026-bounded-product-testing-and-effort).
Effort rationale: The work reconciles concrete evidence, runs required final checks and prepares an accurate handoff.
Reconcile matching evidence before final-source gates and fresh installed acceptance. Rerun other checks only for a concrete gap, change or failure. Escalate to high for conflicting evidence, a safety contradiction or an actual final-gate diagnosis.

## Read before implementation

All task evidence; current selector; acceptance/test mappings; clean branch/source artifact identity; docs, compatibility and legacy-deprecation records.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Audit every acceptance case and task dependency against actual passing test node IDs and artifacts. No unresolved blocker, silent skip, mocked-only host parity, placeholder endpoint, unsupported browser or deferred human documentation may be relabelled complete. Reconcile current plan/task/progress/ADR/invariant state with git. If needed split additional bounded tasks, allocate fresh work-package IDs and keep this task blocked until their evidence exists.

Run the strict web/backend gate and final clean installed functional/compatibility smoke using the final source/artifacts. Per the user's2026-11-01 instruction to ignore and deprecate Cockpit, preserve its legacy source/history/licenses/live installation; no plugin removal or further plugin validation is a prerequisite. Record source, build/runtime hashes, dependency/license inventory, browser/profile matrix, unit/integration/functional counts, docs gate and honest residual production/NAS limitations. Keep raw secret-free evidence locators outside normal source as appropriate.

Provide a human operator handoff with how to build/install/validate through the existing Caddy, configure the one Basic user, preserve original handles/candidates, understand restricted profile controls, and perform a compatible rollback only when separately authorized. Set plan completed and clear current selector only when all scoped acceptance is met. Commit this work package on feat/web-ui; leave merge/push/tag/deploy for explicit later instruction.

## Unit and component validation

Run all unit/component/coverage/type/lint/doc checks and validate no critical acceptance case lacks executable coverage. Record actual results, not intended commands.

## Integration validation

Run all integration/private-worker/CLI/MCP/strict install/format compatibility suites on final source and artifact indexes. Verify required new-web/backend gates remain strict through the legacy-deprecation amendment.

## Functional validation

Run `scripts/check.sh --require-web --with-build` after final changes and separate direct installed final acceptance under the adopted product-focused criteria: actual same-Caddy Chromium/Firefox/WebKit at both prefixes on native/rootless, REST/MCP, supported native/guarded-rootless controls, negative security and interrupted-operation/config behavior at the relevant boundary. Account for all95 scenarios without required skips. Reuse unchanged deep proofs with explicit justification. The existing `--with-web-functional` runner is optional and remains strict if invoked; never claim it passed from direct checks.

## Human documentation deliverables

Update release notes as unreleased/source-ready, human handoff and actual fixture acceptance summary; preserve current production deployment-status facts. Complete task/progress/ADR/invariant review and plan/current records in this commit.

## Acceptance

All requested new-web source features, unit/integration/functional testing,
documentation and legacy deprecation handoff are complete and evidenced on a
clean feature branch. All95 new-web behaviors and minimum layers remain;
production rollout/remote publication and live plugin uninstall are unperformed.

The task also requires the existing strict web/backend `scripts/check.sh` gate
and functional checks described above. The latest user amendment requires no
further legacy Cockpit checks. New capabilities are not completed solely by
adding test descriptions. Update actual test-to-case mappings and run them.
Documentation and relevant contract/invariant/ADR updates land with the behavior.

## Execution notes and blockers

2026-11-01: Activated after WEB-025/6fdc7e0. All 93 predecessor cases retain
minimum layers; final RELEASE-09/DOC-05 remain. Reconcile exact retained evidence,
complete human handoff/status/release notes, then required full source gate and
fresh narrow read-only installed observations on the retained coherent 0.2.78/f829
candidate. Production runtime/packaging/web bytes remain unchanged; package 0.2.2
metadata and test/dev-gate differences remain explicitly separate from fixture 0.2.78.
No new release build/install, browser matrix, job/Plan/Apply, PKI, service drain,
credential change or mutation replay is indicated. Root alone executes reviewed
owned guest effects after the final gate. No plugin maintenance/validation.


## Completion evidence

Completed 2026-11-01, WEB-026, this commit. All 95 scenarios retain every required
minimum layer. Twenty-five predecessor commits include human docs in the same
commit; this package adds the final human handoff/changelog/status corrections.
No new framework, proof schema, runtime dependency, durable format or privilege
is introduced. Reviewed INV001/002/011/017/018/019/020/021/022, FW03/FW04 and
relevant ADR140–160; current status fields and dated acceptance notes align with
actual source/owned-fixture scope. Earlier reasoning/failures and platform holds
remain. Decision160's user-directed deprecation is preserved without plugin work.

### Final required source gate

`rtk proxy scripts/check.sh --require-web --with-build` exits 0 in 1,640.827 seconds:
9,650 backend tests, 4,051 unique combined web tests, 16 wheel tests, three locked
installation profiles, two built-browser checks and actual React/API read fixture.
Coverage: 95.02% lines/90.13% branches; zero required skips. The 52 live/NFS/build marker
deselections in the default suite remain opt-in; all 16 required build tests run
separately. All 1,547 frozen inputs stay unchanged. Freeze SHA
`f26faa360c08882c88721a8a027488a379aaa2dffcab5132bdc60c1618ce712d`,
result SHA `8d255165b8226d21cb99562f5814c7d11b659c13d1bd227a6726d9651911b101`,
log SHA `8a3e3ebfeeb6511aa032482c23b8d9f63deba79fd73a91ad060f0974b34e9305`.
Outer private empty read-only NAS shadow/login UID 1000 gate also exits 0. Raw records:
`.scratch/web-026-validation/`. No actual plugin command executes and the
optional `--with-web-functional` runner is not claimed passed.

### Fresh final owned installed observations

Root verifies host boot/QEMU PID/start/argv before/after each SSH observation.
Fresh application and stopped-browser captures seal the exact existing CIDs,
profiles, public renewed CA and matching 0.2.78/f829/UI57828 identity. Normal Basic
authentication privately verifies the retained donor against the actual protected
record; stable subject matches the original accepted browser. No new rootfs,
PKI, artifact build/install, service drain/restart, job, Plan, new key or replay.

- Native fresh capture/seal and reviewed controller pass with exit 0. Source SHA
  `f6b8cf1f85ebf3bf7f406df04b9857f87b1e04477bc417ed2f6bccfefca244be`,
  result `.scratch/web-026-final-fresh1/native/result.json` SHA
  `d4a1940d3f5c6517b184989e025c2e39d88d495fa1938ee55f3f4560ef9fa117`.
- Rootless equivalent passes with exit 0. Source SHA
  `1e4066235da42152c710780d75ec94725aa3382d302ae3e9e021fce6a6544396`,
  result `.scratch/web-026-final-fresh1/rootless/result.json` SHA
  `083e5c5f8967366d2b26b465cd2c4fbeb693155f9b2f029c5ad4c6d27f445c99`.
- Both actual Chromium/root reports prove trusted TLS, current build/manifest,
  settled Library before/after reload, stable subject, sandbox and normal actual
  context/browser/container/cgroup closure. NonGET/external/page errors/request
  failures/5xx remain zero. Existing exact read-cancellation rules are unchanged.
- `rtk proxy python3 .scratch/web-026-old-original-lookups78-1.prepared.py`
  passes both original GETs with old 1c68501/0.2.2 wheel b88ffd0f. Native 0dcbe97e
  stays succeeded, rootless f302dad7 stays failed; whole original operation objects
  match. Both exact owned forwards close normally/-15. Result
  `.scratch/web-026-old-original-lookups78-1/result.json` SHA
  `025b0b4f29246f7a04d55b5436937ce21e31d8f47ffa5d4a9ad65f792bee3405`.

Private crypto/credential/hash/secret-store bodies are metadata-only except normal
authorized authentication. Explicit public source/config/CA and approved native
pending hashes stand; original public operation bodies are GET-joined separately.
This is metadata continuity, not new private-payload byte proof. Native original
SDK pending inode 95048553 stays unknown/preserved. Rootless guard/RO mount,
original state, masks and disabled calendars remain. The final host wrapper's
rootless settled-result field mismatch is corrected BEFORE execution; original
prepared source/review receipt remains, with no failed browser replay.

The coherent clean 0.2.78/f829 artifacts are reused because current production
Python/packaging/web bytes and normalized dependencies match. Main self-version 0.2.2,
dev gate/test/documentation differences remain distinct; no new final 0.2.2 install
or newly repeated three-engine/two-prefix matrix/Firefox/WebKit trust claim. Earlier
matching deep observations retain their actual source/profile and qualifications.

### Human handoff, evidence and closure

Human handoff links build/stage/provision, same Caddy TLS, Basic lifetime,
independent permission/readiness, original handles/candidates/stores/locks,
rootless denials and compatible rollback. All six production boxes remain
unchecked. Unreleased source-ready changelog text makes no version/tag/deploy claim.
Actual 25-commit continuity/runtime receipt SHA
`e68c6e5c07159817d704c46cb2b9ba95126db50cfb5caa3cd650500f892f0c82`,
dependency/licence inventory SHA
`423d6e1b7f1acbabbe7bf2f56c1d85a9364aa1d3101deb6f77e88e658d606022`.
Final review `.scratch/web-026-validation/final-human-handoff-review1.json` SHA
`b9799d1b3d7a47604e30bc86bab6504aefc4bf462ccc7d6d883341c71e3ac07d`
joins actual source/browser/old-client results with completed 40-step/13-image/
19-example guide review and existing scoped keyboard/Orca observations. No new
human-reader listening or universal accessibility claim.

All original failed aggregates, historical locator corrections, unknown handles
and Library/Firefox/formBasic/unsupported-instrumentation limits remain. All 95
case rows preserve their exact minimum layers and actual commands/hashes/scopes.
Post-gate changes are evidence/status/closure documents only; focused docs/plan/
diff checks pass before local commit. Parent plan completes and current selector
clears, with completed progress/operator handoff in this commit. No production/NAS,
merge/push/tag/publication, live-plugin uninstall or unknown cache/data cleanup.

Post-adoption closure1 passes with exit 0: 224 human documents/29 helpers, all 9 plan tests
(including all 95 completed rows/minimum layers) and git diff --check. Output
`.scratch/web-026-validation/closure1-shadow.log` SHA
`566b1d31b77efe93bc1f3f65b77fe2b1c9db08533a541b5d280fb331dc021461`.
Only ten documentation/evidence/status files differ from the successful full
source freeze; runtime/build/gate code is unchanged. Completed task/plan/current,
progress and operator handoff are in this local commit. Exact successful Gate26
generated TMP is inventoried with no live references/contained hardlinks; all gate
logs/manifests and 13 finite outputs remain, and public frontend reports are
byte-verified behind canonical paths. No unknown cache/data or guest cleanup.
