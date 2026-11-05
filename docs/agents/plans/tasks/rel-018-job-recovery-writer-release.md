# REL-018: Clean committed source and reproducible immutable matching backend/UI/image/helper artifacts

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | WEB-033 |
| Execution | `gpt-6.1-sol` / `medium`; explicit task-agent setting required |

## Scope and acceptance

Clean committed source and reproducible immutable matching backend/UI/image/helper artifacts; documented rollback compatibility using existing release tooling.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Review the parent plan's affected contract and decision list progressively.
Record exact reviewed IDs, amendments and any new decision before completion.

## Validation

| Changed requirement | Smallest meaningful check | Required gate | Evidence/result |
| --- | --- | --- | --- |
| Release version and source identity | Project-only0.3.2 version change; all locked dependency records unchanged; clean committed detached source | `scripts/check.sh --require-web --with-build` | Gate4 passes; source2d4c9cc clean, only project version changes across94 locked packages |
| Matching backend/UI/helper release | Existing clean-source builder repeats wheel/sdist/UI bytes and validates canonical source index | Same gate | Repeated backend/UI build passes; wheelc207/UI4156/index5084/full snapshotc425 |
| Immutable protected mode siblings | Existing app/Caddy builders and renderer; same version/source/image/UI, distinct guarded/manual release_id/runtime/index | Same gate plus existing artifact verification | Actual final-image foundation and mode-specific manifests/renders pass; unchanged worker/Caddy proof explicitly reused; protected staging remains OPS-028 |
| Preserving compatible rollback | Reuse exact predecessor/current durable/browser and actual source11 guarded rollback evidence from WEB-033; preserve all original state/fences | Same gate | WEB-033 compatible guarded rollback and exact c23abba refusal retained; matching0.3.2 siblings prepared, no old-reader revival |

Reviewed INV-001/003/007/020/021/023, FS-19/21–23 and ADR121/150/164/165.
Version/provenance changes do not alter qualified application behavior. Existing
contracts retain permanent fences and explicit guarded/manual mode identities;
no new invariant, architectural decision or dependency is introduced.
Every commit requires `rtk scripts/check.sh`; web changes require `--require-web`;
release acceptance requires `--require-web --with-build`. Preserve raw failures.
Do not invoke the optional instrumented functional runner.

## Execution notes and handoff

Activated 2026-11-03 by the user's explicit end-to-end implementation instruction.
Protected deployment, controlled writable transition, selected Sync and refresh
pilots and bounded metadata backfill are authorized after the reviewed safety
prerequisites. Scope is this host/current boot with fail-closed manual startup
permitted; unattended boot acceptance remains separate.

## Completion evidence

Release acceptance completes below. Actual production deployment/recovery/pilots/backfill remain OPS-028/029; source acceptance is not promoted to production evidence.

## Accepted immutable mode handoff

ADR165 requires manifest2 release_id exactly `<version>-<archive_mode>` and
immutable sibling release directories for guarded-readonly/manual-writer. Keep
package/UI version semver and source/app-image/UI bytes identical; bind distinct
rendered runtime/index hashes. Stage both through the existing installer; current,
physical-root, index and helper selector_target use exact release_id. Existing
schema1 version-only identities remain supported. OPS-028 runs the guarded
sibling. OPS-029 drains/selects the writer sibling while still NFS-ro, reprovisions
matching helper/policy, then performs the separate guarded mount transition.
Rollback selects a compatible guarded sibling without editing immutable files
or deleting dispositions. Add only these identity joins to existing machinery.

2026-11-05: Begin after WEB-033 commit7df95c5. Use version0.3.2, retain
installed production0.3.1/sourcec23abba and all predecessor artifacts. Required
release gate is a new release boundary, not a replay of installed WEB-033
acceptance. Existing direct format/profile evidence is reused with exact scope.
No optional functional runner, remote publication or tag. Build/gate as login
user with private empty RO archive shadow. Root filesystem17GB/home66GB free
before preparation; preserve original logs and fixtures without cleanup.

The first release gate stops at documentation alignment before backend tests:
README linked an internal agent execution tracker, forbidden by the human-doc
contract. Replace that link with deployment status; retain original gate1 log
and result. No product behavior or completed installed check changes. Gate2
is the required corrected release-input validation, not a repeated harness drill.


Gate2 retains an actual failing prerequisite:9928 backend checks pass and the
exact predecessor test fails because source-only sys.path selection takes the
current0.3.2 installed distribution metadata while asserting0.3.1. Preserve the
version assertion and all refusal/exact-read checks; build/extract the pinned
c23abba wheel offline so metadata and reader come from the same predecessor.
The current installed binary compatibility evidence remains unchanged.

Final-image CLI worker probe first refuses before workspace because the private
launch omitted the existing login bus/runtime environment. Corrected launch
reaches user_notify, then actual worker exits20: its old fixture has no mandatory
intent companion. A narrow direct final-image workflow with that supported bind
passes all original assertions in8.779s (logd9b1ff48). Preserve both original
failures. Repair the existing fixture only by creating/mounting its own0600
companion; add no framework, synthetic authority or weakened assertion. This
source repair requires one fresh gate and clean rebuilt artifact provenance.
The unpromoted source02b1479/artifacts/image09c2 and every proof remain retained;
no production selection or effect has occurred. No completed WEB-033 matrix is
repeated. These are two named reproduced prerequisite defects, not new scope.

Focused validation of those two repairs passes86 existing checks in3.25s,
with private NAS-shadow launch4.718s/logbf05a820. Ruff formatting/lint pass.
The predecessor assertion still requires0.3.1 and exercises the same exact
terminal reads/refusal cases, now from its actual pinned wheel and metadata.
The worker fixture adds only its own0600 companion and one fixed bind. No
application/runtime behavior, permission or dependency changes. Final gate3
uses these corrected inputs; retain failed gate2 and its full original payload.


Gate3 passes9929 backend checks/52 deselected in1218.54s, package/three locked
profiles,179 wire definitions, strict web/16 built-browser/zoom/real API stages.
Its final wheel stage has14 passes and2 failures: installed old-runtime catalog
probe imports tests.intent_fixtures, absent under isolated -I. Restore its actual
installed hfcache OperationStore import. The catalog-only fixture now creates a
fresh private legacy-shaped store without intent activation, explicitly asserting
no disposition file; it never removes existing authority. Keep every original
catalog/queued restart/result/golden/MCP assertion. New intent refusal remains
covered separately by exact c23abba and actual installed WEB-033 evidence.
Original gate3/old environments/log729df4ea remain failed and retained. Focus only
the two failed installed catalog cases before the required corrected full gate;
no application code, dependency, permissions or completed installed matrix changes.

The two actual installed catalog compatibility cases now pass in14.74s,
private-shadow16.359s/log5aeea63e. All original17 golden,9 old MCP tools,
config rejection, exact terminal-result, queued interruption/no-replay and
archive nonmutation assertions remain. No intent file is removed or fabricated;
this fresh catalog-only fixture is explicitly unactivated. The actual upgraded
public-store refusal has its own capable/c23abba evidence. Ruff passes.
Run the corrected mandatory full release gate4 once, with no further acceptance
matrix expansion. All prior candidate bundles/proofs remain preserved; only
fixture/test source and evidence changed since source36a, not runtime behavior.


## Final release evidence — 2026-11-05

Required `scripts/check.sh --require-web --with-build` gate4 PASSES in1526.120s:
9929 backend/52 deselected (1173.68s),216 human documents/29 helpers,
package build and three locked base/server/server+MCP profiles,179 wire
definitions,3809 web unit/4169 combined checks,16 built-browser checks, actual
200% zoom/320CSS, real HTTP/API React reads, and all16 wheel smoke cases
(41.83s). All1283 frozen names/hashes remain unchanged. Inner raw-log SHA256
`77ab2645ecf36fbe83c828d8fd7fe774d2b5c5e1d37b5f0dfeee76c4ebfb1e68`;
outer shadow loge949a5db. Original failed gates1–3 and full payloads remain;
none is relabelled as passing. No optional instrumented runner is invoked.

Clean committed artifact source is `2d4c9cc0b279601e5519a09e563cd40804cdc4d4`,
tree `a76e9f1ea920ca790bb75b13e14b3ca498218840`, retained detached at
`/var/tmp/hfcache-rel018-source3`. The later main evidence commit does not
replace this artifact source. Repeated wheel/sdist/UI bytes agree. Canonical
bundle `/var/tmp/hfcache-rel018-artifacts3` has index
`5084cf0fbb2cb4c160620c8edb2c6517ad85744091fa92d9a3a579306e7881ec`,
full source snapshot `c425eba50b7ef197ecba80ba7088029cd8c494a6280e613da80380e5c22db413`,
wheel `c207cc372430ae46cba615dd87157dd8d70f2defc9cb958e05479dd484f21da7`
and UI manifest `4156b2d90db0d0462189aed60d2c0e57e789ee36fd2d708bc37d6f8bb5cf3a80`.
Builds run as loginUID1000/nice10 under a private empty RO NAS shadow.

Matching app image is
`sha256:ef3cb2e7b20c8116b128fdd7dc14603b8090b6a6965842b0b1f4f1a21d0e52a9`.
Actual final-image foundation PASSES14.580s/log762a79a6. Caddy remains unchanged
`sha256:fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10`;
its original provenance and actual source02b reuse proof88e119f1 remain, with
all five relevant recipe/foundation inputs byte-identical. No Caddy rebuild.

Actual repaired standard CLI worker proof on source36a/image61a PASSES24.801s,
loge8b092d7: notify READY, API-container private PROBE, PID1/internalFD3,
capabilities/NNP/seccomp, no-IP/credential denials, original lock contention,
protected reader, empty operation history and clean joined drain. Reuse retains
that exact image scope. `worker-proof-reuse3.json` proves candidate2d has the
identical wheel/dependency/base/recipe/runtime config, all non-UI rootfs layers,
worker launcher/unit/probe source and all UI member bytes. The only changed UI
manifest field is build.source_commit. It is not a claim that the worker probe
ran on imageef3; actual production API-worker/confinement proof remains OPS-028.
No completed WEB-033 browser/recovery/lost-ack/native/format/job matrix is rerun.

Local OCI `/var/tmp/hfcache-rel018-app3.oci.tar`,66333184B, SHA256
`348314885c98e3254979c6773fff859f50117b92830b9e039b12b127c6350106`,
exports once with stable image IDs/names/digests/parents/sizes/readonly metadata.
Original source36a export controller failed its concurrent whole-image-list
postcondition; the same successful-save OCI was independently qualified by all
config/layer digests, without reexport or relabelling the failed controller.
All superseded source02b/source36a bundles/images/exports/proofs remain retained.

Immutable sibling inputs `/var/tmp/hfcache-rel018-container-input3` share0.3.2,
source2d, app image, wheel/UI and all33 source members. Only archive_mode and
release_id differ. Official pure validation/render passes both modes:

| Mode | Manifest SHA256 | Rendered runtime SHA256 | Expected official stage index SHA256 |
| --- | --- | --- | --- |
| guarded-readonly | f1358eaae8b6fce8bbb379b936d407452296c3f38c8d70d299bacb0b39a72dec | fef7c2129d07bb19d19d9ea8fd64cde6cc4095f34adc38033c2f77b880ea51db | c74a08796867095391ddcc88932fdf84e63fb6504955baf37c2dc8de6dba6cda |
| manual-writer | f860a5c47c13d79ecfd61667ff578e7241a0c552c3082a47384c4427745ac912 | 922e28f671ef22efb67f8788d1aa2ecef05962d0ca8aec9f4d6c610691fc6a19 | e6aea3b0d5e33b952758a03ad61eb4333dffff5d19856857209269c8d7a5cb08 |

The47-file indexes are deterministic EXPECTATIONS from authenticated source,
actual render bytes and the official canonical encoder, not protected staging
observations. OPS-028 must measure and match actual stages under full drain/
original-lock/NFS-ro guards. Hostname, empty public prefix, UID/GID981 and actual
service home remain production-specific; fixture allfalse permissions are not
copied. Prepared handoff3 SHA256
`bcba1e975af3597c5f72d1bc64fb6982403e99e26b9ffcd2c3377aca8159f585`
retains candidate wording; promotion authority comes from this passing gate,
committed release and the subsequent reviewed OPS-028 prerequisites.

Final INV-001/003/007/020/021/023, FS-19/21–23 and ADR121/150/164/165 review
confirms unchanged runtime behavior and existing capable guarded rollback rules.
The fixture fixes restore conformance with those contracts, with no new
invariant/ADR/dependency. Preserve permanent dispositions and original stores/
handles/credentials/lock inodes; old c23abba cannot resume new authority.
No production service/mount/policy/permission/archive change, remote push,
release tag or image publication occurs in REL-018. OPS-028 is next.

Factual closeout passes the existing focused documentation checks in8.381s,
shadow log68cbb3a1be613936ade9c84307c3d8488dfeb165167a0091a8f69bd7646c443b.
Direct freeze comparison permits only task/plan/current/progress evidence edits
after gate4; all technical inputs remain exact.
