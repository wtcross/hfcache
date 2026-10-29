# WEB-021: Integrate web assets and the host adapter into native/rootless releases

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P5 |
| Depends on | [WEB-020](web-020-cross-browser-accessibility-and-load.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-021: package immutable native and rootless web releases`, this commit |

## Read before implementation

Existing build-container, native/container release installers/indexers and packaging templates; asset manifest contract; docs/containers.md and release workflow.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build a reproducible separately indexed UI artifact tied to source/UI schema/lock/toolchain/license identity. Extend clean release construction to require/verify this artifact, retain base uv build without Node, and stage immutable native assets or copy them into the rootless API image. Do not put frontend files in Caddy or add a Node service. Pin/bound startup asset verification and server web configuration; UI-disabled old deployment remains valid.

The user's 2026-10-20 clarification requires the appropriately streamlined UBI 10
image for the web UI. Ship its static assets in the existing API image, retaining
pinned UBI 10 micro for build/runtime FROM stages and the existing CA-only donor
boundary. No separate frontend image, Node, pnpm/npm, compiler or browser belongs
in runtime. Verify actual base ancestry with the foundation probe, inspect the
installed asset bytes and runtime tool absence, and record exact base/final image
identities and image size. Test-only browser images are separate unshipped inputs.

Update actual release artifact indexes, strict installer requirements, role/secret/socket definitions, service confinement and safe enablement examples for Basic hash and the narrow helper. Prove read-only policy-directory replacement visibility and that Caddy/worker cannot see helper/Basic secret. Keep existing Caddy instance/template routing/port/TLS and private-worker lifecycle. Packaging must not grant default host policies, unmask timers, enable UI implicitly in existing production, or pull images at runtime.

Build native and rootless artifacts from exact clean committed source using the established staged-build workflow. Keep dirty-fixture results distinguished. Validate fresh installation, enabled missing/mismatched UI refusal and backend-only installs, stable same-origin base/prefix and actual asset hashes. Any unavoidable runtime dependency/schema changes have reviewed ADR/index/lock updates.

## Unit and component validation

Test release manifest parsing, hashes/missing/extra assets, traversal/symlink input, enabled/disabled UI config, strict role metadata, safe help, no runtime Node and no secret/host socket added to wrong roles.

## Integration validation

Run base/server/server+MCP wheel installs without Node; stage verified UI artifact in native fixture and build rootless app image from pinned local inputs. Inspect installed bytes, permissions and role mount/secret separation; no dirty build masquerades as clean.

## Functional validation

Launch the actual staged native/rootless release behind the same Caddy fixture and repeat login/deep-link/asset/API/MCP/host-helper paths. Verify bad asset/index and missing hash provisioning fail visibly; no Vite dev server is present.

## Human documentation deliverables

Complete deployment.md for operator prerequisites, exact artifact selection, shared Caddy, Basic hash provisioning, native/rootless differences and no production effects. Update scripts, containers, server and release/install examples and license attribution.

## Acceptance

A complete immutable release carries matching SPA/backend/helper artifacts and runs with existing Caddy/no Node runtime; Python-only profiles remain supported; packaging preserves all role/policy safety boundaries.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

2026-10-29 gate6 is running with `/home/tyler/.g6` after both cheap validators
and the complete three-test socket preflight pass0. All1005 product files remain
frozen; only agent evidence/selector records are finalized during this run.
Primary log/result are `gate6.log` and `gate6-result.json`. Neither task closure
nor a local implementation commit is authorized by an unfinished gate.

2026-10-29 gate5 environment correction: the deliberately home-backed temporary
directory was too long for the real reader client's Unix socket path. Both
socket variants fail there; the same complete three-test file passes with its
normal shorter temporary directory, and the long-path failure reproduces
independently. Preserve `gate5-long-temp-reproduction.json`. Only the positively
identified host-side gate pytest897032/start18144057 receives graceful SIGINT;
gate5 ends2 after208.66s with no frozen product-file changes. No guest/service/
executor receives a signal. The full gate must rerun with a short home-backed
temporary path; this is an environment correction, not a passing gate or product
change. Native8's independent final audit exits0 and verifies961 source files,
16 UI/helper artifacts,119 modules per API/worker and exact running-role boundaries;
its initial overstrict inactive-socket assertion stays separately retained.

2026-10-29 final source8 acceptance checkpoint: native browser smoke1 exits0
on Chromium/Firefox/WebKit at both root and`/management`. All six contexts
verify clean source245f2eaa/UIcb22c40d, guarded native identity, supported helper
status and installed configuration, with zero mutations/pageerrors/5xx.
`native8-browser-final-state1.json` independently verifies browser exit0/PID0,
normal FinishedAt and twelve screenshots. Native worker9573 starts normally
through its original bound socket; both calendars remain inactive. Actual worker
and Caddy mount-namespace/DAC probes deny all four selected Basic/writer/helper
inputs; these probes do not inherit application SELinux/cgroup/seccomp contexts.
Both native REST aliases pass; MCP invokes14 tools with12 successes and2 absent-
report errors, explicitly leaving full positive report coverage to WEB-022.
Documentation221/29 and all9 existing evidence-validator tests pass. The final
`scripts/check.sh --require-web --require-cockpit --with-build` is running in
`gate5.log` against frozen product files. Final gate/role-audit completion and
the work-package commit remain pending; earlier checkpoints stay historical.

2026-10-29 recovered source8 checkpoint: owned guest recovery is complete on
boot`b2f9c836…`, with Enforcing policy and independently provisioned current-boot
archive lock inode1641. The prior kernel's inode1332 is historical, not preserved
across boot. Actual rootless tag-only preview`c9684584…` and Apply`9562cdac…`
complete; both API/worker read-only parent mounts observe the atomic configuration
replacement and API facets expose the new tag without executor restart. Original
configuration lock61244163, HMAC key61259513 and current-boot global1641 survive.
Live namespace/credential/network probes and independent83-file role audit pass;
normal bridge/helper drain proves original executors gone and cgroups empty.
Evidence is `rootless8-config-visibility2.json`, `rootless8-live-boundaries1.json`,
`rootless8-role-metadata.json` and `rootless8-graceful-drain-before-native8.json`.
This retains the failed pre-recovery SSH request and every earlier failure.

Rootless trees/stores/units and old native trees are retained by inode before an
explicit cold-fixture native reconstitution. Native source8 canonical stage2 and
guarded selection exit0; service UID983 verifies119 application modules and16
UI/helper files, plus Python3.14.6 with optional installers/build tools absent.
The first incomplete offline-cache stage and index-shape audit error remain
separate failures. Native helper8112 is READY in its required domain; API8198
and existing Caddy8204 start normally with both calendars inactive. All-three-
engine/both-alias browser acceptance and independent running-role metadata audit
are in progress. The final source8 package gate remains required; this checkpoint
does not complete WEB-021 or establish later full workflow acceptance.

2026-10-29 source8 checkpoint: clean auxiliary245f2eaa builds reproducible backend/
UI artifacts (index01f4df84,UIcb22c40d), actual API image072146b2 with verified
UBI10micro ancestry/runtime/tool absence/assets and19 fresh Node-free Python
profile commands. Canonical rootless stage/switch exit0. Enforcing policy
provisioning retains original archive lock inode1332 with the dedicated SID,
unchanged fifteen-role receipt, original key/configuration lock/history and
user-manager invocation. A mistaken hyphenated module installation and incorrect
new permission-policy mode are separately retained and corrected to the documented
underscore module/0600 policy before accepted startup. The helper runs in its
required domain; all three roles start through the normal bridge.
Actual trusted HTTPS now passes bootstrap, guarded rootless status and installed
configuration. Chromium/Firefox/WebKit smoke1 exits0 with deep links, navigation,
exact clean build/helper identity and zero mutations/pageerrors/5xx. REST credential
classes pass; all fourteen MCP tools run, twelve succeed and two absent report
queries remain explicit errors, not full positive MCP acceptance. The host's
before/after image-size accounting difference is retained; immutable OCI config
and all six layer hashes agree. No original failure is rewritten.
The disposable QEMU process subsequently ended; authoritative process/handle
checks confirm termination while its backing metadata remains unchanged. The
planned rootless configuration Apply encountered SSH connection refusal before
remote execution and was never transmitted. Preserve an exact pre-recovery
overlay copy and recover only that owned target, revalidating boot-specific
locks/labels/guard before further effects. Atomic replacement visibility, final
role checks and the final package gate remain required. Prior-boot acceptance
does not claim current liveness, production/NAS readiness or task completion.

2026-10-29 rootless checkpoint: source6 is selected with the independent original-
inode guard, helper and API/worker/Caddy running. The rootless TLS failure is an
IP-hostname default-SNI omission corrected in clean source7; canonical release,
API image, ancestry/runtime/asset checks and rendered rootless inputs pass on the
host. They do not establish installed source7 acceptance. The confined fixed
guard observer now has a concrete separate failure: `LOCK.lstat()` returns
EACCES because API/worker `:z` assigned `container_file_t` to original inode1332.
Valid stdin and the actual confined entrypoint reproduce it; earlier malformed
diagnostic input and unconfined successful predicates remain separate evidence.
Decision159 and INV020 amend the contract before implementation: independently
provision that existing lock's dedicated type, preserve it in both enabled
launchers and permit helper metadata only. No generic payload grant or lock
replacement is authorized. Native/disabled behavior and existing receipts remain
unchanged. Source8 construction, actual enforcing rootless checks and a final
gate remain necessary; no package completion is inferred.

2026-10-29: Activated by the user's WEB-021 through WEB-026 goal after startup
reconciliation at clean tracked baseline `c199c4af1d05356d56abe5a0b7b7c9b8f860ce48`.
The existing root `node_modules/` remains untracked. Native/rootless release
construction and installed isolated acceptance are authorized; production, NAS,
remote publication and live Cockpit removal remain excluded. WEB-020's completed
records and every unresolved fixture operation remain preserved.

Current implementation checkpoint (2026-10-29, uncommitted): explicit clean
constructor/native and rootless installer inputs, indexed helper/UI bytes,
standard-library bounded verification and expanded actual image probing are in
place. The existing uv build backend is pinned to0.11.32; repeated wheel/sdist/UI
construction passes from clean source183f16e5. Its index23cfdbac… and UIe4e261e2…
remain scoped historical artifacts after the subsequent helper integration fix.
Image07606b41… passes actual pinned-micro diffID ancestry,205684696-byte size,
read-only/no-IP/UID981 and no Node/package-manager/compiler/browser checks.
Base/server/server+MCP wheel installations pass with Node absent from PATH.

The first full gate exits1 after9206 passed/6 failed/52 opt-in deselections in
1137.02s. It exposed the rootless helper's captured-reader adapter missing the
installer's new `allow_empty` argument. The focused correction preserves ordinary
nonempty authority files, captures indexed UI bytes under existing aggregate
budgets and executes only captured verifier code;446 affected tests pass.
The completed native/rootless integration also captures the full native web
index and binary/empty UI members, preserving absence and original authority
rules; the expanded focused run passes567 tests before the next clean build.
This requires new clean artifacts and a final full gate; no earlier failure is
rewritten as success. Native install3 separately exits2 during uv's filesystem
reflink operation despite17GiB free; ordinary copying succeeds. Dependency
installation now explicitly copies rather than sharing/cloning cache files.
The partial native release and original log remain preserved, unselected.

An additional owned QEMU copy-on-write fixture (port46321, bootb7d4d5f6…) is
Enforcing with no NFS or application executors at startup. Its inherited release,
config and both stores were renamed with directory inode identity preserved;
the original guest on46261 and its backing/snapshots remain untouched. New
mutating acceptance uses this separate fixture and fresh stores. Installed
native/rootless functional acceptance remains unperformed. Evidence starts at
`/var/tmp/web-021-validation-4ibo9g0f` and
`.scratch/web-021-validation/`; `.scratch/web-021-evidence-location.json` routes
current exact sources, hashes, known exits and live tool handles. Two closed
failed build environments were relocated byte-for-byte to the home filesystem;
their inventory/relocation receipt preserves each file/link and source worktree.
The new guest now has a real read-only kernel NFSv4.2 mount from its own
`127.0.0.1:/` initialized fixture export at `/srv/hfcache`, with Enforcing policy,
nosuid/nodev/noexec and exact PID1 mount evidence in
`.scratch/web-021-fixture/nfs-loopback-result.json`. No archive initialization,
manual archive-tree writes, production or NAS connection was used.
Clean source4 (`e318bb4c…`) again reproduces all three artifacts. Native installation
and supported guarded selection both exit0; native asset/package audit verifies
six UI members plus manifest, nine helper artifacts and119 wheel package files
as readable by UID983. API imagee2c69f25…/205689300B and Caddyfa2a5634…/128643310B
have actual pinned ancestry and runtime absence/byte proofs; current wheel
5354bcc7… passes all three no-Node Python installation profiles. Evidence is in
`.scratch/web-021-validation/host-acceptance4.json` and `native-assets4/`.
The native audit's aggregate remains false: its selected managed interpreter
contains pip/ensurepip. Decision158 requires a fresh version/source runtime copy
with only optional installers omitted, leaving shared donors and older runtimes
unchanged. This is under implementation; no native absence or task completion is
claimed from source4, and new final artifacts/gate remain necessary.
The source4-era second gate command exits0:9229 backend tests/52 opt-in
deselections in1114.89s,3702 web unit/4029 combined frontend,95% lines/90.02%
branches, required Cockpit/wheel/build/browser/real HTTP/API checks. The mutable
worktree received later native-runtime delivery edits during that command, so
it is not final-source gate evidence. The independent runtime-copy implementation
now passes640 focused tests plus targeted copy/probe regressions and full
Pyrefly/Ruff; a new clean source/build and final gate are still required.
The actual installed provisioning helper also passes via a non-echoing TTY in
the new fixture, producing a private fresh Basic record; separate reader/MCP
encrypted credentials are API-only and the original writer credential is kept.
No application services or browser acceptance have started in this fixture.
Clean source5 (`2b2b3744…`) reproduces the artifacts and API image6ff74ccf… passes
actual micro/runtime/asset probing (`host-acceptance5.json`). Its native runtime
copy refuses before creating a destination because standard CPython terminfo
entries contain `+`. The dedicated runtime component grammar now permits that
character without widening source/UI grammars or link containment;207 focused
tests and full Pyrefly/Ruff pass. Source5's refusal remains known exit1 and its
donor/stages remain untouched. New source6 construction/installed proof and the
final gate remain necessary; no runtime absence or task completion is inferred.
The third full gate exits0:9250 backend tests/52 opt-in deselections in1103.32s,
3702 web unit/4029 combined frontend tests and16 wheel smoke tests; required
Cockpit, browser and actual HTTP checks pass. The final runtime name correction
arrived during that run, so this remains intermediate-source evidence. The next
gate runs against the frozen corrected source while installed checks proceed.
Clean source6 (`662b7bf2…`) reproduces all artifacts. Native install and guarded
selection exit0; UID983 verifies the16 UI/helper files and selected3.14.6 runtime
without pip/ensurepip/build executables. API image79ba66ca…/205689304B passes
actual ancestry, runtime and asset checks; `host-acceptance6.json` records exact
hashes and qualified unchanged Caddy/Python profile joins. The frozen corrected
implementation gate exits0:9261 backend tests/52 opt-in deselections in1272.62s,
3702 web unit/4029 combined frontend tests and16 wheel smoke tests, with all
required Cockpit/browser/actual HTTP checks. Later documentation/evidence edits
still require the final package gate before commit.
Native browser smoke3 exits0 on Chromium/Firefox/WebKit at both root and
`/management`, including clean bootstrap, navigation, supported helper status,
installed configuration and zero mutation requests. Smoke1 preserved an actual
fixed-peer refusal of API credential drop-ins; the supported protected file
sources restore the exact indexed API unit without changing Caddy's PID.
Smoke2 preserves a Chromium response-body instrumentation race; smoke3 uses
bounded page-context reads. Installed application lifespan rejects missing/hash-
mismatched/missing-member/changed-member inputs with HFCFG005; earlier unrelated
CLI instance-lock refusals remain separate. REST class checks pass both aliases;
all fourteen MCP tools are invoked, twelve succeed and two explicitly absent
report reads remain protocol errors. This is not full positive MCP acceptance.
Worker/Caddy namespace probes deny administrator/writer credentials, and actual
process privilege/SELinux/cgroup facts are retained. A separate root namespace
probe does not supply a helper-domain secret denial. Original unbounded network
test children were identified and terminated without touching application
executors; bounded probes show both actual no-IP cgroups block the otherwise
reachable Caddy endpoint. Rootless installed acceptance and the real upgrade
dirty-draft/original-handle check remain pending. A clean fixture-only0.2.70
projection changes exactly the two version fields; it is not a release claim.
The real native0.2.2→fixture0.2.70 upgrade now passes ROUTE-08 on all three
browsers: each old document holds its unsaved Tags text and one original admitted
Basic recovery record, detects the new clean build, presents the reload guard,
and retains exact draft/record/storage hashes after Stay, with zero mutation
requests or document navigation. The original tag-only preview/Apply succeeded
and is retained as operation9a80ba21…; no lost or uncertain earlier handle was
replayed. The supported installer stages/selects0.2.70 after exact original API,
worker, helper and Caddy drain, retaining both stores, key inode and permissions.
A first helper start correctly refuses the new version's `usr_t` unit targets;
provisioning only the nine indexed immutable targets as standard systemd unit
files restores READY/supported status with the kernel policy hash unchanged.
That native label prerequisite is now explicit in the human deployment guide.
Evidence: `native6-upgrade1.json`, `native70-stage.json`,
`native70-unit-label-provisioning.json`, and `native70-ready-and-marker.json` in
`.scratch/web-021-validation/`. Rootless installation remains the next check.
Rootless source6 now stages and switches through the canonical installer, with
the stock UID983 engine, exact images, fifteen-role receipt, original key,
READY guard/helper and active API/worker/Caddy. Native trees/stores/credentials,
prior engine state and runtime coordination objects are retained by original
inodes; same-device private retention handles the tmpfs boundaries. The first
IP-address HTTPS check fails TLS selection: the shipped Caddy template lacks
the canonical `default_sni` already present in the native fixture. The template
now binds that default to its existing hostname, preserving certificate and
Host/Origin checks. New clean source/artifacts and actual rootless TLS checks
are required; the active source6 stack and failed evidence remain preserved.

## Completion evidence

Completed2026-10-29, `WEB-021`, this commit. The auxiliary clean build
capture is `245f2eaaa02e0f7549d5e268e5ff27fb79837cd5`, source snapshot
`ecbf406e3e2f9c498fd88be45490186ceaddc9a03fcdc9fe32c15e8e14e281d0`.
It is not the final work-package commit. Exact primary artifacts are:

- release index `01f4df8446852a72857bafa5351a8320643dcb58622b5c5ba9c19d8ece28ba94`;
  UI manifest `cb22c40d78a038c1dd5615667445ff86e6810f0f6361589cfc5624229a3e3226`;
- wheel `0887b99a01418e5d3a4520544c2b28f8f2c24f7ad336f94f7d3ffdf7b75aaecb`;
  sdist `bc7628576950b6195c61ea942ea09b1070e065ae3d3c5576dba40a8519d8b7c7`;
- API image `sha256:072146b26e0df701e99806eedd53638fee3b9bd0df2dfc6af0308eeeda3c1a8c`;
  unchanged Caddy `sha256:fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10`.

`host-acceptance8.json` binds canonical reproducible build commands, pinned actual
UBI10micro ancestry/tool/asset probes, OCI config and all six layer digests,
rootless inputs and all19 fresh offline base/server/server+MCP commands, each0.
The API engine reports205690839B before export and206917079B after it; the
1226240B accounting difference remains unresolved, while immutable config/layer
identities agree. The initial size-equality assertion1 remains retained. Native
stage2/guarded selection0, actual service-UID audit0 and independent live role
audit0 establish961 source files,16 UI/helper artifacts,119 package modules per
API/worker and selected copied3.14.6 runtime without optional installers or named
Node/package-manager/compiler/browser tools. Complete donors and old releases
remain separate unchanged build/rollback inputs.

`native8-browser-smoke1.json` exits0 on Chromium/Firefox/WebKit at root and
`/management`; `native8-browser-final-state1.json` verifies normal exit0/PID0
and twelve screenshots. `rootless8-browser-smoke1.json` exits0 in the same three
engines at8443/root on the prior boot. Both check trusted TLS, exact installed
build/bootstrap, navigation, helper status and configuration, with zero mutation/
pageerror/5xx records. Recovered rootless boot separately verifies exact assets,
running roles and a real successful tag-only Apply with read-only API/worker
parent-directory replacement visibility and unchanged executor identities.
Current native role metadata/open-close probes and rootless actual container
probes establish worker/Caddy Basic/helper isolation; live capabilities, seccomp,
NNP, sockets, mounts, SIDs and cgroups are recorded without claiming a dedicated
native API/worker SELinux domain. The rootless normal drain proves original
executors gone/cgroups empty before cold-fixture native reconstitution. No
production cross-profile upgrade is claimed.

Historical native6 `native6-upgrade1.json` supplies actual ROUTE-08: all three
old documents retain exact dirty Tags drafts and original admitted recovery
records through fixture0.2.70 change detection and Reload/Stay, with zero replay/
mutation/navigation. `native6-negative-lifespan-corrected.json` supplies expected
HFCFG005/exit10 for missing hash, wrong hash, missing asset and changed asset.
Source6→8 wheel members differ only in host_policy/RECORD; actual API app/asset/
serving and UI session/editor/recovery source bytes are identical. These remain
explicitly historical checks, not new source8/rootless upgrade execution.

Exact commands, observed assertions, original artifact hashes and test mappings
are appended under ROUTE-08 and RELEASE-01/02/03 in the
[evidence ledger](../support/web-ui/acceptance-evidence.json). Primary files are
under `.scratch/web-021-validation/`; installer, helper, unit and drain records
are under `.scratch/web-021-fixture/`. Gate5's environment refusal/interruption2,
all earlier gates/failures and prior unknown observations remain preserved.
All9 existing ledger tests and documentation221human/29helpers pass before the
short-path final gate. Final gate6 exits0 in1516.98s with all1005 frozen product
files unchanged:9318 backend tests/52 opt-in deselections in1114.68s,3702 web
unit/4029 combined frontend,95% lines/90.02% branches, all required Cockpit,
browser/actual HTTP/API and16 wheel smoke checks. No required check is skipped.
Original log SHA256 is
`b696088557fbf9ef151f59f8921bb1dbd6d5c74931a8d4004aded24243c5fb6d`.
All four owned rows are completed; the final gate's source hash identifies the
canonical1005-file frozen map, separately from clean installed source8 artifacts.

Reviewed INV018/019/020/021/022 and ADR007/129/143/145/150/156 against release
and role changes. ADR158 records the copied native runtime and ADR159 the fixed
metadata-only rootless archive-lock type; affected indexes, invariants, prior
ADRs and living security/install/deployment/schema contracts are amended in this
package. Deployment guidance includes exact CIL module naming, original-inode
provisioning, native target labels, cold-boot helper parents, Basic provisioning
and explicit enablement. No runtime dependency, helper protocol/receipt format,
default policy grant, timer enablement or automatic production activation changes.

WEB-022 remains pending for the complete installed workflow matrix, positive
verification/maintenance/native controls and all14 positive MCP report calls.
Current REST credential classes pass; MCP smoke has12 positives and2 absent-
report errors/client1, not full positive MCP acceptance. Original lost/uncertain
Apply state remains unreplayed. Production/NAS, live Cockpit uninstall, merge,
push and tags are excluded. The completed
[progress entry and operator handoff](../../progress.md#operator-handoff) and
[current selector](../current.md) select WEB-022 next; this plan remains active.
