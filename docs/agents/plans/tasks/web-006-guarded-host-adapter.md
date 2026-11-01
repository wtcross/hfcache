# WEB-006: Implement a narrowly privileged host adapter and safe status projection

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `7b578382a375c0505db9af5c014976b35136ef3123808fa4d6532ba5b7bce3f8`,
original content SHA-256 `bda979bfdb557d4c1f14800ae0ba2e8c32c71219e0306bb1784b220fc7ce1450`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-005](web-005-shared-caddy-spa-serving.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-006: add guarded host status and administration boundary` (this commit) |

## Read before implementation

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement a fixed-operation host-administration helper boundary with protected Unix transport, real peer verification, bounded strict requests and independently provisioned policy. Begin with config-base/status reads and host status; write grammar remains denied until its task. Keep all resource paths/service-manager/unit names fixed, no shell or generic filesystem/DBus/engine dispatch. API remains non-root and receives only the narrow helper socket; no helper access for Caddy or verifier.

Implement GET /host/status with explicit supported/guarded/unknown/unavailable state, safe release/policy binding, effective action permissions, fixed system services/timers and schedule view/revision. Preserve rootless denied schedule/observer semantics; lack of a guard is not permission. Reuse the existing proven profile inspection safely rather than ignoring its source/index checks. Generalize with explicit backward-compatible policy migration only if needed; do not auto-provision wider privileges.

Enforce fresh helper/policy proof at Basic human admission for archive/Hub/control actions as required by the former plugin's scope, while keeping domain guards final. Existing service bearer behavior and unknown authority remain explicit. Bound host inspection time/output and classify failures without claiming API/worker crashes.

## Unit and component validation

Test protocol unknown keys/version/commands/units/paths, malformed sizes and peer mismatch, protected policy no-follow/race checks, release drift, fixed-manager scoping and fail-closed permission computation.

## Integration validation

Exercise real Unix peer credentials from the intended unprivileged caller, helper unavailable/restart/timeouts and protected local config/status reads. Verify helper cannot access archive/Hub secrets; hostile local caller and header claims cannot manufacture authority.

## Functional validation

In an isolated systemd/rootless guest, prove actual container host UID mapping and socket separation, denied basic archive/Hub/control actions on the guarded policy, and visible UI denial reasons. Mocked unit outputs do not close the platform proof.

## Human documentation deliverables

Create administration guide and host-helper deployment/security sections. Document what permissions mean, supported profiles, independent policy provisioning and missing-helper troubleshooting. Update role/secret/socket matrices and script inventory.

## Acceptance

Authenticated host status is real, bounded and safe; helper isolation and peer identity are proven; no new general host authority exists; guarded rootless behavior is preserved and readable in the UI.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Started2026-10-21 after WEB-005 commit `07d10e0` and clean checkout.
Read the full kickoff, task/support contracts, invariant/ADR indexes, workflow,
environment and relevant protected profile/peer/policy code. Review AUTH-08 and
HOST-01–03. Contract-first protocol/policy/status and fresh admission/dispatch
implementation is selected; write opcodes remain denied until their owners.
Actual installed native/rootless proof is mandatory and pending.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
actually exited1 after989.91s, with7244Python passes, eight failures and52
opt-in deselections. Source1's1348file hashes/modes stayed unchanged. Failures
identify the missing independent host-route parity/security registry entries
and new host-model authorities/counts in the original-serializer corpus tests;
these checks are being corrected and rerun. This is a failed gate, not acceptance.
Original log/result `.scratch/web-006-gate1{.log,-result.json}` remain retained;
snapshot `7bd8b93e2448adb2ad43eb5daef5350aa2f9058c532d2e8eb23d4d3d9467ed39`.

Owned guest progress: the measured source1 transfer/extraction verified1348
ordinary-file hashes and modes in a fresh `/home/webfixture/hfcache-web006`.
The genuine983 stock rootless engine and user manager initialize successfully
with default overlay storage, without custom engine-root/runroot arguments,
application starts, source switching or image/profile acceptance. Original
receipt `/opt/hfcache-web006/rootless-prewarm-v1/prewarm.json`, SHA256
`9e55cc062ece443ae1600264871a6aaf529f3966bae7126e7572aaba02d03865`.
The helper's real namespace/Podman interaction remains under investigation;
neither its confinement nor rootless status is accepted from source checks.

The unchanged native installer was run twice with `--no-switch --with-mcp`:
attempt1 failed on the disposable guest's DNS; attempt2 failed because frozen
remote lock URLs do not use the supplied offline find-links directory. Both
failures leave the selector absent and no application service started. The
first incomplete tree and exact log/receipt remain retained separately; the
second tree is also retained pending a measured dedicated offline-cache retry.
These attempts establish no installed native acceptance. Public hash-locked
runtime wheels and a separately explicit build-only backend were downloaded
and authenticated without copying any ambient account cache or credentials.

Subsequent owned staging evidence: native attempt3 passed the unchanged
`install-release.sh --no-switch --with-mcp` in13.70s using a fresh dedicated
public locked uv cache; all108 installed package source leaves matched source1.
Both incomplete earlier trees and receipts remain retained. Selector remains
absent and no application/helper service has been started. Source2 changes
only four test/reference files; all108 native runtime source leaves match it,
without relabeling the original native installer receipt. Its original nine
units, config-only synthetic policy and new UI artifact are staged separately;
`/etc/hfcache/server.toml` is intentionally not active yet.

Source2 snapshot
`b793ac40d6c2075b7e7501060eec066b7dffd6c78ee52fdb3df2778c49d39e82`
retains1348files and all source1 before-bytes. Two independently run UI builds
were byte-identical, manifest SHA256
`3df4287d83ecf791d63b4ff9dd93badba7b5b60a246567ee8947625cdba04fea`;
wheel SHA256
`9db898c4145b683b58531e648b8ad5b834267a419a4d117c405c4dfd2ff9c951`.
A fresh actual API/UI image built successfully in29.03s with both original
pinned UBI10micro FROM stages, verified separate UI bytes, locked offline
wheels, network-none and pull-never. Image identity
`133e9f4852c36d4c768c12394a9f3242a87d4a5cda0b954c3ebd15b9d289d772`;
build receipt SHA256
`590734cd97af51d65d67638224a65bc5e5af3a0b62e61dfb02609d7c0ffcdfbd`.
The app/Caddy/genuine-base OCI exports and exact receipts transferred to the
owned guest. The first reviewed rootless load/audit actually exited1 at its
initial stock UID983 Podman info check, before any image load or container
creation. Its failed intent and execution receipt remain retained at
`.scratch/web-006-image-runtime-audit-v3-execution.{log,json}`; log SHA256
`49c83ad7d6720ed4110ce09fc813c32e78c960fcf9144ae8956166dd6eb2a83b`.
The failed command's environment required separate diagnosis; the successful
build/export/transfer alone established no installed image acceptance.
The subsequent fixed-CWD comparison recorded an inherited-directory refusal
and successful stock983 `info` from `/`, without changing engine configuration
or security. Original v3 CWD was not recorded and remains unknown.
Reviewed auditv4 then actually passed in43.98s, log SHA256
`8d4e8a219ef70e98677517d855e664d8496a9a707df008c1998beb4b08f1b19b`,
receipt `.scratch/web-006-image-runtime-audit-v4-execution.json`.
Its selected image has the genuine pinned micro base-layer prefix, all108
package files and six UI files match, and the explicitly enumerated Node,
uv/pip, compiler and package-manager PATH/import probes are absent. The
read-only/network-none/capless container mapped inner981 to host983, exited0,
and its recorded PID72871/start7043844 and cgroup closed; original container
`c3d17b82fd8573065ad77b7f89416737e7bd174a3c8b646001962563f89c60ea`
is retained. Guest Podman reports204709132bytes; build-host inspection reported
204709078bytes. Keep both observations rather than asserting identical size.
This establishes selected dirty-fixture image bytes/runtime properties only,
not installed application/helper-role or clean-release acceptance.
This is a dirty source fixture, not a shipped clean release or profile acceptance.

Source2 full gate actually exited1 after1002.64s:7256Python passes, two failures,
52opt-in deselections, no source hash/mode drift. Both failures were the
optional-MCP test's old assumption that every GET permits a REST bearer;
`/host/status` deliberately requires internal host-read. The new focused checks
pass22tests, zero skips,8.30s, retaining real plan/sync compatibility and proving
neither REST nor MCP bearer reaches the helper. Original gate2 and repair logs
remain retained. The next source/gate must include this additional test repair.

Actual confinement diagnostics are incomplete, not a Podman result: v1 failed
before worker exec with systemd STDOUT209; v2–v4 executed the confined worker
but failed before Podman. V4 records `EPERM` from child setup, all worker IDs0,
bounding capabilities0xc0 but effective/permitted0x40, NNP1 and seccomp2.
An additional canonical-confinement diagnostic reproduced that missing SETUID
in both Python `-I` and `-I -S` before any explicit import and through all five
recorded startup stages: P/E0x40, Bnd0xc0, I/A0, NNP1, seccomp2. Both workers
exited normally with empty cgroups; diagnostic generation
`3e0f2c1482464a6b8773e14eefb7f562`, root-only log
`/opt/hfcache-web006/python-capability-diagnosis-v2-execution.log`, SHA256
`2a6b0908af3f85f4007aad9c0417ef93be224fa960c940780163b4efd4974dfa`.
This identifies a launch-time capability problem, not Python import behavior.
No shipped capability/filter/mask has changed. Original probe units, root-only safe error records, before/
after engine-pause evidence and normal-stop/empty-cgroup observations remain
retained. Typed USER-only inspection has not been accepted.
The first ambient-SETUID/clear-before-exec candidate retained root P/E/Bnd0xc0
and cleared I/A to0 across its fixed exec; its full983 child had P/E/I/A0,
Bnd0xc0, NNP1 and seccomp2, and all three archive/Hub open probes were denied.
Actual stock Podman then exited1 with namespace-join refusal. The parent
diagnostic itself exited20 because systemd garbage-collected the fast worker's
exit fields; this is retained failure evidence, not a passing diagnostic.
Generation `cd8d5cd5e66b477eabbccceb17c10ea9`, runtime output SHA256
`eaebcb4301b37a49827a969f58c6046a724ca18c69f61a64f7842ec36018c688`;
both recorded worker/child identities and cgroup closed normally on stop.
The GC-safe original diagnosticv7 subsequently completed with actual worker
exit0 and the expected stock namespace-join refusal. Typedv7 refused the
kernel's USER-entry capability-bound reset; typedv8 explicitly dropped all
namespace capabilities but Podman aborted before producing JSON. Typedv9
retained protected bounded raw streams and reproduced that failure. Its exact
first diagnostic and pinned upstream Podman6.1 source identify the missing
effective namespace-local SYS_ADMIN gate in both rootless setup and storage
initialization; changing the completed-namespace environment marker cannot fix
it. Original safe observations remain at
`.scratch/web-006-cap-probes-v7-observations.jsonl` and
`.scratch/web-006-typed-cap-probe-v{8,9}-observations.jsonl`.
Typed9 generation `c03ea9ee7b01481790b68b7beffe9658` has result SHA256
`7f56c60aca5210387d75a402e69bbfc2f0b78a24edf7cd0b837a4d3053afe12a`
and drain SHA256
`a1f0533c937d3e97f1c4704736da80716ed31df9127434c0348f437aa84806af`;
both exact worker/child identities exited and its cgroup closed. The diagnostic
driver's exit0 records observations; Podman's SIGABRT remains a failed read.

The next reviewed experimental design retains only SYS_ADMIN in the already
verified engine USER namespace at fixed exec, with I/A0, while the root helper
keeps its original-host-USER SETUID/SETGID ceiling. Its original masked MNT must
be independently proved owned by initial USER, with actual forbidden MNT-entry/
creation and archive/Hub/INET negative probes. This explicitly revises the
capless proposal through contract-first amendments; it grants no public opcode
or generic engine selector. Further USER transitions can reset capability sets,
so a single-bit pre-exec observation is not a lifetime ceiling. Source review
alone establishes no successful Podman read or installed role acceptance.
Typed10 then retained the namespace-local SYS_ADMIN bit with I/A0 at both
pre-exec and actual Podman observations; original MNT/PID/NET, initial-USER
mount ownership, mask/INET and forbidden MNT-transition checks held. Podman
exited125 because overlay initialization attempted to make its storage mount
private. Generation `1bf2093f20204480b0b095b9bd9f541b`, result SHA256
`e1d6027b4bb62a8a30640f691e4492e38f7ab380f55bc3eab861c34b0d64ed68`,
drain SHA256
`677d77fa5f963e62567bf7d551d0f2685bfd8e13380cd156507cd8c3e10bf7d9`.
The actual store has a nonempty `overlay.mountopt=nodev` option. Pinned upstream
storage/Podman source shows `overlay.skip_mount_home=true` skips only that
mount housekeeping, but explicit CLI storage options replace the configured
list. The contract therefore requires preserving independently proved original
options or refusing an unsupported configuration, rather than dropping options.

Typed11 passed the genuine stock-engine read with exactly preserved `nodev`
plus `overlay.skip_mount_home=true`: Podman exit0,4894stdout bytes,0stderr,
original overlay/graphRoot/runRoot unchanged. The protected stock config's
identity/hash and absent override paths were proved unchanged before/after.
Actual post-exec capability and namespace observations, archive/Hub/INET and
MNT-transition denials held. Worker74172/start7386490 and child74174/start7386512
both exited; the owned cgroup is empty and the original pause process remains.
Generation `a5834014a66648b49777ec9f517f4fad`, result SHA256
`a578a6e686219ec2349e90557429b54f80a59a6a66840710cf5230e47a33bc34`,
drain SHA256
`0442481ee6ca5954355493c539a8b0359fb5a4459f16bd54d7bd03de9349f70d`.
Safe selected observations `.scratch/web-006-typed-cap-probe-v11-observations.json`,
SHA256 `d90de90aac3b7d068c65ff9eb3092213a5545c86c79a4e9031b02ee28adbd357`;
root execution log SHA256
`69ab2eb9891844254c67df0e503c0443640275f1b215d02c03f7d3cd16518727`.
Both source and independent reviews passed80tests without skips. The original
canonical unit and protected deployed source remain unchanged. This establishes
only the reviewed engine mechanism in the owned fixture, not installed role or
other operator storage-configuration compatibility. Minimal bound-module
integration and capability-startup repair are now authorized within this task;
no new public engine selector or INFO operation is introduced.

An additional owned-sentinel-only diagnostic12 exposed a real isolation gap:
before USER entry, the full service-account observer could open the positively
owned synthetic sentinel through the verified pause process's `/proc/.../root`
alias (72bytes, hash only retained). The same alias was denied with EACCES13
after USER entry/capability reduction. Direct masked paths stayed denied and
the fixed engine read exited0. This is not proof of exhaustive archive/secret
isolation; no real or dummy credential was read through that alias. Do not
weaken hardening or present the direct-path denials as closing this gap.
The fixed observer's engine-owner trust boundary and a narrow mitigation are
under independent review; installed isolation acceptance remains blocked on
resolving this finding. The independent root source check passed100tests,
zero skips,1.29s. Original generation
`a08a3fa3b4cf4e218b965a0a9cda5fb9`, result SHA256
`660e29ad9ab2fe557f876c48cc9ffffa211ea71c95aadbeeff3414675e925288`,
drain SHA256
`0cb832fb08c505037ba943a1e2906364945391b0ed37e70209a3bc0ab9ce9317`;
worker74364/start7443561 and child74367/start7443585 are gone, cgroup empty,
the original pause process and synthetic seed are unchanged. Safe observations
`.scratch/web-006-typed-cap-probe-v12-observations.json`, SHA256
`277c11b19d83d5bbeed3d1ec7bc895ee62656039fd6169ad1f7bf71219364208`.

Mandatory SELinux confinement is now contract-first source work under
[decision150](../../../adr/decision-150.md) and INV-020. The unit requires the
exact confined context; early startup verifies it and Enforcing before authority
module loading. A protected installation receipt binds the reviewed CIL and
fixed label roles into the independent deployment index. Its kernel digest and
masked-object labels attest root provisioning; runtime checks do not pretend to
read hidden labels through aliases. All helper children must retain the domain.
Initial SETUID/SETGID and namespace-only setup remain distinct; no initial
SYS_ADMIN, DAC or ptrace grant, permissive domain or transition escape is added.

Owned policy attempt1 with CIL SHA256
`925446f611bc7e7e7a7e004e59a9bc460bae3ef49c338ba495975d7f2ac1fe0d`
actually failed target compilation at an unavailable external type. Its kernel
policy and module list remained byte-identical; all source/logs are retained.
A fixed metadata survey proved the target's kernel SELinux objects are
`security_t`. Corrected CIL SHA256
`a6387ea7ce7659fc1632d852d173292430b037077a9844704c2fef0838803f06`
then compiled and installed at priority400 in8.06s while Enforcing remained on.
The loaded `hfcache_host_helper` module checksum matches that source. Result
`/opt/hfcache-web006/selinux-policy-install-v2/RESULT.json`, SHA256
`e023465a8599f3d475aadcfec6050e5f94c24af5a04fcfa2fecd57a8bda6f883`;
kernel policy SHA256
`bdff7805124ea41b978e999ef150c43e0e48e1dd209b2c4fbda4a26bc33e2485`.
This policy-loading step changed no labels, application services, selector,
protected helper source or original canonical guest unit. It is not actual
helper-domain, alias-denial, engine or installed profile acceptance. Those
measurements remain required next.

Subsequent policy/runtime attempts remain incomplete. Policyv3 added only the
measured manager append permission and policyv4 only its open permission; both
compiled under Enforcing. Exact diagnostic13 source stayed unchanged across
three generations. Attempts1/2 failed STDOUT209 before worker execution; attempt3
reached the mandatory helper domain but failed readiness with EACCES13 at the
fixed manager notify socket. Its worker75291 exited20; MainPID0 and empty
ControlGroup were observed after normal stop, with no engine child observed.
Generation `9dfc51f08d2740c0b0263b2cbd7a45fb`, drain SHA256
`15cab2f111660dc4c67c5f9f18b5a4337f27d255a1f00e22f1b7a5b907ff5428`;
safe observations `.scratch/web-006-probe13-attempt3-observations-v1.json`,
SHA256 `1042eed3dcc8f43c66ffef62aa653527678e081ef94cb56dcfacfc17207a1f00`.
The failure did not record the worker's start ticks in the drain; no positive
PID/start proof is inferred from its empty process list. Original output and
unit remain retained. The causal AVC is helper-domain to kernel_t datagram
sendto, not the nonfatal ioctl/certificate lookup probes. Reviewed policyv5
adds only that fixed readiness permission; archive/secret file denies stand.
Its first install wrapper refused a stale embedded source-hash assertion after
saving before-state, before semodule/install or label changes. Kernel/module
hashes stayed at policyv4. Empty local stdout and the observed89-byte stderr
count are recorded; that first wrapper did not preserve the stderr body.
The wrapper and incomplete guest work directory are retained, and a fresh
attempt uses an independently checked payload-hash binding. No successful
confined engine/alias/inode or installed application acceptance follows yet.

Policyv5 then compiled/installed successfully with the Enforcing kernel hash
`bf7caabdf760a6323bff19cd3ead049d00071d0f163ecbfe05a1f4be724c92b3`;
its root result SHA256 is
`56ea405611b7a85c855521bb16fb3402ae721535a72c81cdebde4ebb84df68b4`.
Diagnostic13 attempt4 reached readiness and both confined root/service-account
processes, but failed the required stock pause-file read. Its child75683/start
7836025 reported EACCES13 at the final nofollow open of the fixed pause.pid;
the actual AVC names inode29/tmpfs/user_tmp_t, matching the independently
surveyed existing 983:983/0600 file. The original pause70549/start6647855 and
its file remained unchanged. The diagnostic parent additionally raised KeyError
when it treated the child's error-shaped record as a successful entry record;
that harness failure is not an engine result or passing acceptance. Both exact
worker75681/start7835999 and child75683/start7836025 are gone and the owned
cgroup closed after normal stop. Generation
`250d54d4b8d846a19b951cd8d9667455`, drain SHA256
`d314d9473b913c945d443eef97678a0830537eeeec3f97d9d5e62db51e41bcc5`;
safe observations `.scratch/web-006-probe13-attempt4-observations-v1.json`,
SHA256 `945db9d0f4cd05622796e0d58493fdcf7f85f76026076187f9ad78cfd89508b9`.
The fixed pause-label survey is retained at
`.scratch/web-006-pause-selinux-metadata-v1.json`, SHA256
`cb354feb80207e31950b9df0474b56eb37080c7a230f518b08430a503cb2e93e`.
Required confined stock-engine, alias/inode and installed application proof is
still pending. No policy install or diagnostic changed the original canonical
guest unit, protected application source, selector, storage configuration or
production state.

Policyv6 (`6f898e16f953bfe829715d2289ac64bc21d0c94aa02fc827cc813ec2b9ea12a0`)
adds only stock keeper-file read permissions and compiled/installed under
Enforcing. Kernel SHA256
`dd8e1bd9efef036180c4f28e7af358de153c7cf396c54d5dc9f9315eb64e8106`;
root result SHA256
`1b55a5785880f93090436d199d12d021fa2979e8698969a08554c121743bc64a`.
Its first local preparation had an indentation error; the subsequent runner
refused the absent script locally before SSH. Empty stdout and stderr are
retained separately; there were no guest effects from that invocation. A fresh
AST-checked wrapper performed the actual successful installation.
The unchanged diagnostic13 attempt5 read the pause file, then failed at its
fixed live process stat read: helper-domain child75982/start7869706, EACCES13,
actual proc FILEopen AVC with container_runtime_t process SID. The parent again
refused the error-shaped child record; this is not a Podman execution result.
Generation `7149765a9021482daaf168c0eb78d5e9`, drain SHA256
`858f770eb3ec51e56614257219c5c7e3c59e2ae69bfe9ba692d8bbf2aec2d901`;
closed observations `.scratch/web-006-probe13-attempt5-closed-observations.json`,
SHA256 `5a86fa17be6b3561bcf23c41e8c851b15e4fa09076b7a952b20798a7c7aef0b2`.
Exact rootworker75980/start7869682 and child75982/start7869706 are gone,
cgroup closed and all original engine/storage/seed inputs preserved. Required
confined engine/alias/inode and installed browser conformance remain pending.

Policyv7 changes only the existing five process-metadata type rules to permit
ordinary getattr/open/read, retaining separate no-attach behavior. It compiled
and installed under Enforcing: source SHA256
`f6d35d89f63356e3f4de13c4a169805aa11433680eabd572d9a7665aae2ec9d1`,
kernel SHA256
`37aa9eb3a20e9abd906de7df0269c112140e9e759c896b2b75433c24244349ad`,
root result SHA256
`1147e6bd86eb7e3cf4fc7ac7ae2b9758d8c5c76d48b62816f054115f913c40f0`.
Unchanged diagnostic13 attempt6 progressed through the fixed pause file and
process stat/status but failed opening that process's USER namespace descriptor:
actual cap_userns.sys_ptrace AVC, while observer initial P/E/I/A remained zero
and bounding set0xc0. It did not run Podman. No initial SYS_PTRACE capability
was added. A scoped namespace-owner LSM permission with an explicit process
attach/memory prohibition requires contract-first review and actual negative
memory/FD-inode tests; it is not yet accepted. Generation
`44a70f89d3a6444ea987576d734b6403`, safe observations
`.scratch/web-006-probe13-attempt6-closed-observations.json`, SHA256
`74a13ad3bdda89f0b244bdfdd7b1df44448617905138bfcd96ee327cdc6f1ec5`,
drain SHA256
`eba51c8848c0c7d1de72f5c8a2734d6856bc132e7885e92e1b5310e4e5d5d565`.
Exact root76191/start7898915 and child76193/start7898939 are gone with the
owned cgroup closed. All failed generations/source/results remain preserved.

Independent staging preparation review found and fixed missing new source-parent
creation and evidence-locator replacement risks before those scripts executed.
Fresh unexecuted successors preserve old files/modes and all original scripts,
reserve exclusive locators/tags and drain/reap owned transport children through
setup/read/metadata failures. Root independent review passed68tests, zero skips,
2.57s; `.scratch/web-006-source3-preservation-root-review.json`, SHA256
`f619d9d7fcd9930ce326cdf758199074f406532de483b58e4aa4926b4c86f03e`.
No source3 capture, artifact build, source transfer or installed conformance is
inferred from these hermetic checks. Fixed-tag absence is a precondition, not
an atomic engine compare-and-swap.

Independent bounded review adopted namespace-owner `cap_userns.sys_ptrace`
mediation with an explicit helper-to-domain process-ptrace neverallow. This does
not add an initial-USER capability bit or promise universal memory secrecy:
READ-gated proc environment data remains accessible in qualifying contexts.
Contracts require actual attachment-class/inode denials plus installed role
credential delivery and environment/argument hygiene. Initial SYS_PTRACE,
archive/NFS/credential file grants and domain escape remain forbidden. A separate
source-only public-memory/environment probe is being independently checked; no
errno-only outcome is SELinux acceptance. The owned guest's read-only LSM survey
observed existing ptrace_scope0 and Enforcing; no sysctl was changed.

Concrete label review also separated shared read-only `config.toml` from private
helper authority and mutable Hub state from immutable credentials. Enabled API
Hub mounts preserve those labels without `:z`; default and other role argv stay
byte-identical. The receipt now has ten fixed roles. Root reader/preparer subset
passed222tests/zero skips/13.45s; container subset passed217/zero skips/12.71s,
with format/lint/types passing. These checks do not prove target label creation.

Policyv9 source
`f6e6aaa2f6ea13acdbc05b6b7d3dfd6ab101a4aef6680ef9261de56efaf0af57`
compiled/installed under Enforcing, kernel
`79d36801fbcf3296546d3ebe28ee913733ecfe6e3fcf014b9c89ecd71344d3b5`,
root result SHA256
`42b0314463ee2ef7c3c45d44f07fde2071126986eda1b1f81cd302d13e76c9df`.
It changed no original unit/protected source, labels, selector or app services.
Unchanged diagnostic13 attempt7 completed its harness, with both before/after
USER archive proc-root aliases EACCES13, original MNT and actual confined
post-exec namespace-local SYS_ADMIN/I-A0 observations. Podman INFO nevertheless
exited1, stdout0/stderr104, and is not accepted. Its causal fixed runtime chmod
failed with a user_tmp_t directory setattr AVC for inode21, matching original
`/run/user/983/libpod`. Closed stderr classification SHA256
`aa1f1eea591b34efbd2a53d3eac15ff6c1721698621bbbd5f38c7f9086a50575`;
raw stderr remains private. Generation `a0c1350871644bffbef361c356a2696d`,
result `1f8a8593775cc44af77789757384d032539690de35575e5c1dc668bd350ae5e4`,
drain `872668af3dfc427e3bed642a1c4da961277b526cadfcff828a357c6c92f60121`;
closed observations `.scratch/web-006-probe13-attempt7-closed-observations.json`,
SHA256 `6b396bfdc49e26addb6700e26ccc31b20806dc4dc905ce79b40cd7ba26fef26a`.
Root76427/start8023570 and child76430/start8023591 are gone, cgroup closed.
Archive alias directory denial alone is not a FILE-inode read proof. No installed
API/UI/native/rootless acceptance or final full-gate success follows from it.

The combined host/helper/container/docs subset first produced882passes and one
CLI-help failure in42.29s. Minimal action/status-to-help reproductions traced it
to the shared ASGI test fixture retaining process-global daemon logging state.
Test-only reset/teardown preserves the production logging guard unchanged;
the same subset subsequently passed883tests, zero skips,41.87s, retained log
`.scratch/web-006-host-selinux-combined-B-v2.log`. Receipt/label validation adds
38focused tests; the existing reader/preparer175tests also pass. These are source
checks, not the final full gate or installed MAC/browser acceptance.

Policyv10 added only the independently traced stock runtime directory metadata
permission, then compiled/installed under Enforcing. Source SHA256
`7820d22271710b31ce7c06d50ed17ae0f07995d8975f284ff710913bf88405f0`,
kernel `dabc653ef1db2b988c23a1b8d0128990e2cbdd84a0be8af50f9eea249e452373`,
root result `46adf5fb3f53e55a6da851286e22ecdf70eabdee511febee5297bc9ebfec1e69`.
Diagnostic13 attempt8 (`589edd957d8c4c64a71d3cfaaebb0b90`) completed its
harness but Podman INFO exited1. The fixed cgroup-mode statfs failed with an
attributed cgroup_t filesystem getattr AVC and matching private fatal marker.
Result `fb49fcc8f50f5885a3e4d792997880f3708dcacc36c41d492699f5fcdc13304f`,
drain `66b3516d32527c06a1db85a12abfb5c5f74f2874d40e646cf02857770fe5a8fe`;
root76742/start8074097 and child76744/start8074117 are gone, cgroup closed.

Policyv11 added only that filesystem getattr permission. Source SHA256
`fa97b9afb953fd3b65d9debd77edf335db278846bcbe9ebadc82695f5c7871c4`,
installed kernel `e4bb7eade1920b99615fafded4fddb09e15a0fbcdb8bd4669aec195e098ac5fe`,
root result `5d49724f7b189ab3684123347b3575cfd5fbe118f835e42103821c9d65895e65`.
Diagnostic13 attempt9 (`6e30a982ac4640619c75181b900a1e4c`) again completed
the harness, while Podman INFO exited125, stdout0/stderr289. Exact bounded
private-stderr classification confirms `could not find a working conmon binary`;
conmon_exec_t file getattr AVCs match the pinned Podman6.1 global runtime
selection source. Classification receipt
`.scratch/web-006-probe13-attempt9-stderr-classification-v1.json`, SHA256
`3b649a090ff7c9c162f2b0f0e44e592b7f1b89367ef27d9c34787efdd6260e27`.
Result `1fdcdcdb242e1c6692f463abab6215edbc1c22fdda450e3fc58144d643f300fd`,
drain `760074bff7846fa8662a47529475f2edbc3e8b75e8190cd4f56c7e7ca4f3d970`;
root77053/start8120405 and child77055/start8120426 are gone, cgroup closed.
Optional INFO runtime-version execution is outside the shipped inspect path;
the next diagnostic uses the retained owned audit container and fixed inspect.
No conmon execution permission follows from the failed INFO diagnostic.

Policyv12 added only conmon_exec_t file getattr for the traced global metadata
selection. Source SHA256
`cbc5bc61be4c07871bc455a57c7bba74d953a6f3e70548c3b98ac8bc94334b93`
compiled/installed under Enforcing; kernel
`2630ac567a2eb179d49c39609a753f9f43c181c1092cd0a4edd457b300ca779d`,
root result `5794610122bcbfd6eefdfee7634ffb7f2f8b7362d29584748ff23419238e6bb7`.
It adds no conmon open/read/map/execution or syslog-directory permission.
Actual libselinux `security_compute_av_flags_raw` queries then returned zero
requested allowed bits, full decided coverage, flags0 and the same sequence12
for six named process-ptrace contexts and four named file read/open contexts.
Enforcing and the exact policy/source/result bytes bracket the queries.
Receipt `.scratch/web-006-selinux-kernel-av-query-v2-execution.json`, SHA256
`40a02ad831344b3d5312ed5f05dc878d3f45998a4f1339bf2c8ab0357a3bb2c6`.
Named prospective role/object contexts are policy queries, not actual role or
inode observations; these queries establish no reload-atomicity guarantee.

The fresh unbound inode/memory package18 passed31 owned-process/source tests,
zero skips,1.99s in root's independent run. It retains partial environment-read
facts and closes unexpected FDs from three fixed attachment-class probes.
Independent review also passed31tests/zero skips/1.85s and checked every embedded
payload. A binding-only successor then actually executed successfully against
policy12, generation `aa2c5a36236a4ea987e3951d327f0608`; execution receipt SHA256
`274cc53465245cea96e45ee50950f12f57d1f646a7b9a7dbf5030f41eaca0206`.
Exact actor77396/start8212496 retained helper SID, UID/GID983, P/E/I/A0,
bounding0xc0, NNP1/seccomp2. Audit event23205 attributes denied file read on
owned archive inode118335703 to its openat257, exit-13. Events23208/23210/23212
attribute process-ptrace denials respectively to proc-memory openat257,
process_vm_readv310 targeting counterpart77311, and pidfd_getfd438 on the
authenticated counterpart pidfd/FD3. All permissions were enforced, with no
unexpected bytes/FDs returned. Exact event receipt
`.scratch/web-006-inode-memory19-event-attribution-v1.json`, SHA256
`76693833c06bf5db70bf0904d700e015c068525896e4e0a18eb3d8e8139cec10`.
The public same-initial-USER environment was actually readable:239bytes,
complete, known sentinel present. This is no general environment-secrecy or
descendant-USER mediation proof. Original root77380/start8212472, actor and
counterpart77311/start8212417 are gone, cgroup empty, sentinel unchanged;
drain SHA256 `faa5881ecf57e88eef85736e2d4858473312ec96a11b5ce3af36db195dd14d59`.
Actual installed role credential hygiene and fixed-engine/application/browser
acceptance remain pending.

Image wrapperv3 failed before context/build creation because root invoked the
ambient Python3.12 instead of the locked project interpreter; its exclusive
reserved locator remains unchanged. Fresh wrapperv4 used the locked interpreter
and successfully built/inspected image
`24798b11a82ebcfc1abef7de1d402973600a6dcff747d17b80dbb4bd711ebf2b`,
but then failed when a UI-file descriptor shadowed its locator descriptor.
Original wrapper/reservation/build records remain retained. The actual build
receipt has exit0, SHA256
`ea45f291b64dfa3baf3bcda98732a03961458f8100eedb9d0d7cb9150b4f8df3`;
it is distinct from successful wrapper completion. A separate read-only
provenance recovery and fresh exclusive locator are under review; no rebuild,
tag overwrite or historical success relabeling is performed.

The exact source3 image was independently exported/transferred and loaded into
the owned stock983 overlay engine. All seven load/inspection children reaped,
the original pause stayed continuous, all application roles stayed inactive,
and no container was started. The genuine pinned UBI10micro base-layer prefix
and981:981 runtime user match. Host image size204744407 and guest204744461 are
separate observations. Load receipt
`.scratch/web-006-load-source3-image-v1-execution.json`, SHA256
`db118a4287c971495d7798167e0c64f1e4ff4afdbd8cf2a03fefebdf36536ef0`.
This establishes immutable image staging, not installed runtime acceptance.
An additional active-policy query denies helper read/open on prospective
container_file_t delivered-secret objects; actual delivered inode labels and
credential isolation remain pending.

Actual fixed-INSPECT diagnosticv1 exited20 before worker/service start: its
storage guard rejected the stock vendor directories as unsupported overrides.
Generation `e1ddb0c8d9414877b6fe7952738e590c`, remote execution receipt SHA256
`4b6707d2d147995466d61826c48fa8e06f58a7c3e9733e6858e4ea35c135eeed`.
The generated unit is inactive/MainPID0, its cgroup physically absent, generation
directory empty and runtime output0bytes; original sources, unit and failed
outputs remain retained. This is a precondition failure, not a Podman result.
Bounded actual metadata/RPM inspection found the genuine containers-common
6.0-3.el10 package supplies two protected stock files:29-byte00-vendor.conf
selecting overlay and186-byte00-vendor-rootless.conf selecting nodev. Their
exact reviewed names, hashes, ownership/modes and directory inventories are
being supported without accepting arbitrary/changed/additional configuration.
Seven other override paths remain required absent. The source4 candidate passed
52focused owned-file/race/FD/budget checks and independent review. Tracked
source4 implementation/contracts and diagnosticv2 are in progress; installed
fixed-engine acceptance remains pending.

Source4 now contains the exact stock vendor-file compatibility fix, its unit
coverage, the repaired browser count and metadata-only policy13. Snapshot
`73e45eada3fc73d3c4be3feb49e85638f333a26786c6067d56255a810f511206`
captures1355files; its inventory SHA256 is
`2de2e4184143e62d2638db20b8e56ab8999e68d77fb94de8834461ca2d1db81a`.
The stock compatibility implementation passed304focused tests, zero skips,
plus Ruff, formatting and type checks. Its source freeze is
`.scratch/web-006-source4-host-peer-tracked-freeze-v1.json`.
Two source4 UI builds again match the six-file manifest. The wheel SHA256 is
`14b83e51fce71e79f4b6ae31fb114bececb86bdbb2f22732beaf583d6705a4b8`.
The fresh image wrapper completed successfully with image
`0b049aa3776ae1a35deba9f5537451369a46f61e594a3eb0222559fbfafe0629`,
build receipt SHA256
`728bf3b296d619bd7b930919bee0afa766d4b930db98624aede51698eab56152`.
Both service build stages remain on the pinned UBI10micro digest. Source4's
full strict gate passed0 at2026-10-21T18:50:20Z after1266.59s, with no source
hash/mode drift. It passed7544Python tests (52opt-in deselected),572historical frontend
unit checks, frontend2786unit/2846component checks, both startup browser checks
and14real API read-browser tests. Frontend line95.70%/branch92.93%; all required
checks in this command ran. Log SHA256
`dfc12c6343e6e808d6cf72b4a4ce382dbff50f77b7624e4448e3768a25ddd073`.
Installed native/rootless helper and Caddy acceptance remain separate and pending.

The original source3 image recovery completed separately and successfully:
`.scratch/web-006-image-v4-recovery-v1.json`, SHA256
`05841f6fb8d8220edf0cff7ed4da53deb29d7de93aa87431f9bc404a4178e19a`.
It verified retained build/source/artifact/live-image identities and wrote a
fresh locator without altering the failed original wrapper or reservation.

Actual fixed-INSPECTv2 under policy12 ran Podman and exited125. Its exact fatal
was the overlay backing-filesystem metadata check; a separate runroot W_OK
warning did not justify directory write permission. Policy13 added only
fs_t FILESYSTEM getattr. Its actual compiled kernel identity is
`f85ac61e63c28684306c6c8e7cb15e88023f99abf4e72540e24bc35bc2eef85a`;
install RESULT SHA256
`0934d56ee8cb27e8f2f21fdbe8bc3b6781dc9a1bd86cf543bc3b60b965bb05dc`.
No service, label, selector or hardening setting changed in that installation.

Actual fixed-INSPECTv3 under policy13 also exited125. Generation
`b0f39fa01c474762b99f7b00526e7480` is closed: all11recorded PID/start pairs
are absent and its cgroup empty. DRAIN SHA256
`f1227eff584709777c28987168ef5efb5c8c96ffb6d28f0d438213d6d2690c48`.
The prior filesystem denial disappeared. The new denials are metadata on the
existing overlay directory, container_ro_file_t inode77353036. A bounded
metadata-only survey confirms that inode and its existing l child; a private
Boolean classifier confirms the exact fatal mkdir-overlay EEXIST suffix,
not a missing directory or a fatal permission-denied suffix. Stderr279bytes,
SHA256 `8370b4d1d3277c5c8766e73dd9e1893dc2dda14a8835f34080b25ba7745eb1e1`;
classifier `.scratch/web-006-fixed-inspect-v3-stderr-classification-v4.json`,
SHA256 `c795898cf7b27abf71f5d29980ab2f319cc027f9b4d839d75dc648eab4fde05b`.
A scratch-only minimal metadata candidate is under review while tracked
source4 stays frozen for its gate. No installed helper/API/browser acceptance
is inferred from these diagnostic failures or from source tests.

The source4 wheel/assets/image were exported, transferred and loaded into the
owned stock983 engine successfully. Image load receipt
`.scratch/web-006-load-source4-image-v1-execution.json`, SHA256
`26bda983f13afc43a210e6103616fdbb26e863edf49caea25b66835ead60b124`;
all7children reaped, original pause continuous, no application/container start.

Scratch policy14b compiled/installed successfully, adding only observed
container_ro_file_t directory getattr/search. Its first staging attempt14
failed before compilation because root left the old payload assertion; all
three before-files and the unchanged13kernel were retained. Fresh14b corrected
that assertion and preserved the failed attempt explicitly. Active14b kernel
`3167b04e3180ead702f24a0aa24608160569f33ac0f99ecbe9ee9ffe5addff9f`,
RESULT SHA256 `4c61330a205bf9a01400ebd1db10efe39adcfd1f5ac95ccf7cf2b504316139b7`.
The actual14b kernel query still denies requested attachment and protected-file
rights in all11bound decisions, enforcing/nonpermissive; this remains a query,
not actual delivered-inode or role acceptance.

Fixed-INSPECTv4 under14b also exited125; generation
`620cbe9b4db248b29b800c54faee2d5f` has all11recorded pairs absent and cgroup
empty. DRAIN SHA256 `f3ed598569d39005358b7c19a39c454fbdd5e11a7db0173a97c7930743ffceca`.
It passed prior traversal/stat, then failed reading the overlay directory after
an unreadable existing public flag triggered a recursive fallback. An actual
bounded same-inode read confirms .has-mount-program inode77353037 is exactly
false (5bytes), container_ro_file_t. Primary source shows a valid flag read
avoids that fallback. A scratch15candidate adds only that type's FILEopen/read,
explicitly acknowledging access to other reachable image files of that type;
no directory-read or protected archive/credential/Hub file grant is proposed.
Categorical secret protection still requires actual new/delivered inode labels
and alias-denial proof. No universal image-payload secrecy is claimed.

The isolated Caddy source key inode9905766 was separately FD-bound relabelled
successfully to hfcache_host_helper_secret_t, with no key-body read, fcontext
change or service start. Exact original inode retained; all3commands reaped.
Actual root-private RESULT SHA256
`23219076b0c4d880753ab5020765dec951e6e4da266d7836d697e002658aceab`;
local metadata projection `.scratch/web-006-label-owned-caddy-key-v3-result-v2.json`.
Preparation templates for remaining labels/native/rootless staging/controller
are source-tested but still unbound/unexecuted. Required installed functional
acceptance remains pending.

Actual scratch15 and16 compiled successfully with all4installer children reaped
in each run. Policy15 kernel
`d13260c0afbf1fae166d048cb417643b636a18534133dfb34e21faec470d69de`,
RESULT `cb8050abb46717eadb67c6bca1e20cb9bf09d1ae386fc7137352328b397c71da`;
policy16 kernel `95299f2616a3491c2d10b7ed0f63575b7ce8170c132df36e32ba31d4b9aad812`,
RESULT `f9ad4aed62d8f3970c0640d298f2671257322800beb4cdfaafe926fe2d02bfda`.
Policy15 adds only image-type FILEopen/read;16 also allows directory listing,
with type-wide exposure explicitly documented in the proposed contracts.
Neither grants image-file or directory mutation. All11kernel protected-rights
queries under15 still deny requested permissions/nonpermissive; actual role
and delivered-inode acceptance remain separate.

Fixed-INSPECTv5 andv6 also failed125 and closed all recorded process pairs and
cgroups. V5 generation d956683baf38411f86d469036fe9fa5e DRAIN
`23955e435318052b8ff3e6e02537a803988f78f82449de01e955d75d8957b568`;
v6 generation3236a69459fd44dcafa3f369b74acb29 DRAIN
`7bc0a4151a574cab1ac2402a328e5cff5b17c839486b4b3f87d9c384a7341ece`.
V5's exact nested error and inode43039239 identify stock startup listing of
overlay/tempdirs. Primary source also shows optional cleanup attempts and
ignored lock errors: no universal effect-free or always-error-on-stale-data
claim is made. Source16's directory read support removes that denial.

V6 then failed opening the exact existing overlay-images/images.lock for
read/write. Metadata/Boolean receipt
`.scratch/web-006-engine-lock-metadata-v1.json`, SHA256
`1cd95a802b4c4e9b020a92698f0159f8c35f4a88b401337f11311b1b88006806`,
joins AVC inode34809131 to images.lock, container_ro_file_t. The existing
layers.lock inode59769524 has the same type; containers.lock is already
container_var_lib_t. All are983:9830644, single-link64-byte files; their bodies
were not read. Root explicitly rejected a type-wide image-file write grant
because it would also permit image-content mutation. A dedicated fixed engine
lock metadata type, independent provisioning, protected-source checks and
corresponding contracts/tests are being designed. No engine relabel occurred;
tracked policy13 remains unchanged pending the coherent reviewed update.

A read-only lifecycle review also found a concrete exceptional-output-drain
hang in the production mixed-credential observer. Its narrow correction and
real pipe-filling failure regression are in progress, with no new capabilities
or host opcodes. Source4's green gate remains historical; subsequent runtime
changes require a new captured source and gate.

Unblock: demonstrate the required confined child execution and genuine installed
native/rootless peer/status/isolation behavior, then complete real Caddy/browser
denial/restart/timeout/drain tests and a passing full gate before this commit.

Further in-progress evidence2026-10-21UTC: owned policy17 compiled with all four
children reaped. Kernel SHA256
`b6e4f868b2dd38f1ee62bc88ab174634ddc6c451047f88542b786031003c29a2`,
protected policy RESULT
`facc2a6eac32389454f48c56a5dbe99de0231e0dc5fb053b186ead39a64d9da4`.
The coherent policy/role/FD-check/contracts proposal was independently reviewed
and applied across12paths, patch SHA256
`dde0806d3a7127a2c9b981a1d68d4cdabec1e91dfeb1f4489ecc72b458d5d7d1`.
Its57focused tests pass with zero skips both independently and after application;
root XML `.scratch/web-006-source17-applied-root-v1.xml`.
The type-only receipt cannot detect a correctly labeled substitution predating
capture; the new checks detect drift during inspection. Native use has no
engine-lock prerequisite. No installed-role acceptance follows from these tests.

Owned archive preparation verified41fixed synthetic inodes and FD-bound labeled
the39previously untyped objects, without reading payload bodies. All43children
reaped, RESULT `9c6c16184ad8f41f840a9d159fda7c317d3ba622ab9afdfb91638937a4109c17`.
The first broad-label attempt refused at its archive precondition before effects;
it remains retained. Subsequent fixed-label preparation passed:15closed fcontext
rules,15FD-bound labels and three predefined directory creations,34children
reaped. RESULT `fca0f853decc1b1f82f4daff77e7ca026b273651afb41009e87a7b77af42a419`.
This covered staged helper code, Hub state, original credential sources and
runtime directories. Existing code/unit bytes stayed unchanged, and all
application/helper roles remained inactive. These are synthetic fixture facts,
with no live-NAS, delivered-credential or installed-role claim.

Exactly the two existing image/layer lock inodes were then FD-bound labeled
`hfcache_host_helper_engine_lock_t`, with two exact persistent contexts. Their
identities, ownership, mode, link count, size and mtime stayed unchanged; only
label/ctime changed. Eight commands reaped; no body read or service start.
Protected RESULT SHA256
`1800f886584b42a27165644060a82e9f012394f18756ca698e17e438547120d0`,
local projection `.scratch/web-006-engine-locks-v2-result.json`.
The next confined fixed-engine attempt remains pending. Earlier failures remain
failures; no storage repair, replacement lock or broad image-write grant occurred.

The production observer's pipe-filling exceptional-path hang has a narrow
correction and12real finite-child regressions; independent review also found
one interrupted-drainer-entry case which still needs correction. Preserve the
original first error while draining/reaping the actual child before slot release.
The final source capture/gate must include these changes. Source4's earlier
green gate is historical evidence, not acceptance of the updated source.

The interrupted-drainer-entry correction subsequently passes194focused cases,
with the independently reproduced original finite-child case passing again;
root independently runs15real drain cases, zero skips,1.94s. Only
`_observe_as_account` changed relative to the coherent17 candidate; the new
engine checks remain unchanged. Source5 captured1357files, but its strict gate
failed in6.88s on a new negative test's inferred string-only label map receiving
None. Explicit test-fixture typing fixes that error;31tests, lint and types pass.
Original failed gate5 has no source drift and remains retained. Source6 captures
the corrected1357files, snapshot
`82da19f69b729e70a8732f0413859285d4350e8579a1dec3ceffd15f4c717a2b`;
its strict gate started19:47:57UTC and remains pending. Two source6UI builds
are identical; wheel SHA256
`f249c4de6f511a1d682048f68008d8a7c77ec04178614ec61a5426d62263a65a`.
The source6micro image builds successfully in27.37s, image
`61e09c5f6446665bb1a3fba3f595e90f2e9b063a40156cc1d21699f2f50eb76d`.
No source6guest update, profile staging or role acceptance is claimed.

FixedINSPECTv7 actually failed before bootstrap/engine execution: systemd's
mandatory credential mask encountered an Enforcing init_t directory mounton
denial on the now correctly labeled secret directory. Unit startup status226,
generation205320ad545a44b7b76bf54c8db12d9b, DRAIN
`1e3b6fee4e48c1d9b98a2c7b0606f840c807fbb409ebe6b241a4d789a69a6f33`.
All three recorded PID/start pairs are gone, the physical cgroup is absent,
and MainPID0/empty ControlGroup are independently confirmed. Journal-observed
preexec PID80998 is absent; its historical start ticks were not observed and
are explicitly unknown. Closure projection
`.scratch/web-006-fixed-inspect-v7-closure-v1.json`, SHA256
`e8007db84a544a7adf586ae114fab255645c3678ab698cc146c04b9d905e91bc`.
This is a failed startup, not a result for engine-lock access.

Scratch policy18 adds exactly init_t directory mounton on the three custom
secret, Hub-state and synthetic-archive types used by mandatory masks. It adds
no helper permission, transition, capability or mask relaxation. Contract/test
proposal `.scratch/web-006-selinux-policy18-proposal-v2/proposal.patch` remains
unapplied while gate6 runs. The owned candidate compiled successfully in14.36s,
all four children reaped/gone; source
`ade6d285d8217ead9925669874214557d6913b7f714085fa11934c9ca72f5d4a`,
kernel `aca629b558faa7be49b8cedb56553b6c111d29440d8dc9bf5aa7b07fc2e734b8`,
RESULT `c04df82e5b899a49873a6bce450a12771f84dffaea5e9a8a5ebf9fc8ac2837ff`.
Fresh kernel queries confirm the three init_t mounton permissions and all11
protected helper attachment/file denials, flags0/sequence35. An initial parallel
query attempt hit SELinux's exclusive policy-open EBUSY; the failed output is
retained and a separate sequential read-only attempt passes. These queries are
not actual role/inode acceptance. The next fixed confined attempt is pending.

Source6's full strict gate subsequently passes, exit0,1301.82s, with no captured
file hash/mode drift. Actual command remains `historical gate invocation (original command SHA-256 `6a22211ef273d05d08c501759e7aa72d87f00c2f820395dfa51c01e1364b67fd`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`;7592Python tests pass,52opt-in deselected,572historical frontend tests,
2786web unit and2846component tests pass, plus required browser startup/read
fixtures, wheel installations and builds. Coverage:95.70%lines/92.93%branches.
Log `.scratch/web-006-gate6.log`, SHA256
`e038a7177d79b9d1e1e844059e1d4ceb98dbbed6f5c4b0c213799f25dd3e463b`;
result `.scratch/web-006-gate6-result.json`. Caller2756209/start408061910
reaped/gone. This accepts captured source6 only, not installed functional behavior.

FixedINSPECTv8 fails226before bootstrap on the required writable-runtime bind:
init_t lacks directory mounton for the newly labeled helper runtime directory.
Generation304dc3ddf28c4574b07e7b8c87a171d2, DRAIN
`f40c71582277d725521fa78f0eb6eb3a74d08e4dec4f6efad1d41f3b1cf09975`.
Fresh closure `.scratch/web-006-fixed-inspect-v8-closure-v1.json` verifies all
three recorded pairs gone and physical cgroup absent; preexec PID81467 has
unknown historical start ticks and is currently absent. Scratch19 adds only
that init_t directory mounton rule beyond18 and compiles successfully; all four
installer children reap. Source
`b4c313bbf0ea2e59de0933df04ec6f8041f147e60a886cee181997bc5c5f3c4a`,
kernel `f2c26ab3d3c244dbbe5d11e724881900225035b4205a9e457226e58a3ad5c7ca`,
RESULT `a7b1fe00f7eb4cdb3f45240d3e5ed3a414b445a4a57c69700d7c2b15e002113f`.
Fresh sequential kernel queries retain all11helper denials and confirm the four
manager mounton rights, flags0/sequence36.

FixedINSPECTv9 reaches the confined USER-only engine child but Podman exits125.
Generation425a77406ae54f868d03f809d041f3c4, DRAIN
`38a502886fcd4f404e3267c99a8983eb256b48266bfa8d3daac4f1c4cdc8bea2`;
all11recorded pairs are independently gone and physical cgroup absent, closure
`.scratch/web-006-fixed-inspect-v9-closure-v1.json`. Fixed Boolean stderr
classification identifies `mkdir` of the existing rootless-netns directory
returning file-exists. Metadata-only proof joins inode37 to the existing983:983
0700 `ifconfig_var_run_t` directory under the fixed original engine runroot.
Pinned stock source shows unconditional directory recognition during network
interface initialization, even for inspect. The denied directory getattr makes
Go's existing-directory test enter its mkdir fallback. No contents, emptiness,
successful networking or actual creation is inferred. Original directory/state
was preserved; no replacement or engine reconfiguration occurred.

Scratch20 adds only helper directory getattr for that type beyond19, with no
search, enumeration, creation, write, network/namespace/capability or image-file
metadata grant. It compiles successfully in11.26s with four children reaped:
source `b06862ad296bf9d819167a6d3f89919ba4d2f057d1783112387213660838c3d3`,
kernel `a0851c7e1ccc1ecb50cdba0634c5b3e18c3fad90b570383e53e181fb41941261`,
RESULT `d8109f49f10fe9cb6a89090a360172f42d0f4b674055ffded5beeb88a4227e79`.
After gate6 completed, root applied the coherent17-to20 policy/test/contract
patch `417609dda50e2f15295e6efaab32778b164e91f1155359c145df1cdafe8ea5d2`.
The33scratch checks and32production policy checks pass without skips; docs
alignment passes205human documents/27helpers. A fresh source capture/gate is
required for this update. The next confined attempt and final installed
native/rootless/credential/Caddy/browser acceptance remain pending.

FixedINSPECTv10 under20 passes the earlier directory-recognition barrier but
Podman still exits125, generation9e0bee62248c47318089018bcb1dd401. DRAIN22888B
SHA256 `46fe26841b118e38d83fd9a59a2feca5e14fbd443b673308bd4fc80165dd202e`;
all11original PID/start pairs are independently gone and the physical cgroup
is absent, closure `.scratch/web-006-fixed-inspect-v10-closure-v1.json`, SHA256
`4078e28df55e3ee34d09f108ab7f3b371ede72d19f98ad49ed8bf53bcadbddc2`.
The bounded private stderr classifier identifies the exact existing runtime
alive-lock open denial; no raw stream is published. Metadata-only O_PATH proof
joins AVC inode28 to `/run/user/983/libpod/tmp/alive.lck`,983:9830644, single
link, zero bytes, user_tmp_t. Classifier/metadata receipts respectively
`3731b353cd16b0dab9ab85f69273eceef99373c32fece68b98e57f6a3bb4df2b`
and `d8665a5523f612d8820a20ab90a97e32b896dac897da804b16f3487c3fead6a1`.
Pinned stock runtime source requires opening this coordination lock read/write,
even for inspect. Broad user_tmp_t file writes are rejected. The proposed narrow
extension independently labels and checks this third existing lock using the
existing lock type and eleven-role schema, with its distinct zero-byte size.
Its tmpfs lifecycle requires explicit fresh root provisioning after recreation;
no creation, automatic relabeling, generic transition or historical-inode claim
is introduced. Effective TmpDir can also be overridden by the engine database;
a default-leaf check alone does not prove every such override refuses. A fixed
same-default command binding is being checked against primary source before any
stronger claim or implementation. The next source capture remains pending.

The fixed same-default `--tmpdir` alternative was rejected after independent
pinned-source review: `WithTmpDir` assigns the configuration without setting
`TmpDirSet`, and database merge precedes validation, so the flag cannot guarantee
override refusal. Primary receipt
`.scratch/web-006-alive-tmpdir-primary-v1/REVIEW.json`, SHA256
`8d33c0c1b48430ab043ed010b75f1d189a6e56a50c9c2b52041401e6cdbabe0c`.
The reviewed three-lock proposal instead states its default configuration/database
epoch and trusted engine-account limits explicitly; no ineffective flag, SQLite
parser or new dependency is introduced.

Root then executed the independently reviewed one-inode alive-label recipe
`3fa7286089dd7699c6feff67608e5cb557bfc0a8e138007d648ccea4a3945c53`.
It passed in3.19s, six child commands and outer PID2784971 reaped. Exactly one
existing zero-byte inode45/28 was labeled through its held descriptor, with one
exact fcontext rule. All v10 identities/cgroup were freshly closed before/after;
no lock body, application start or installed acceptance was involved. Protected
`/opt/hfcache-web006/alive-lock-labels-v1/RESULT.json`, SHA256
`152471405443e813cb8c9cb304bd1e71dc7f94aba384c965714fae4fb6ebece4`;
local projection `.scratch/web-006-alive-lock-label-v1-result.json`, SHA256
`e6beffdb18db2ccf7d8833192f16b2f3682ea59b9a3d50bd03741bbb63f39d9e`.
The first read-only projection used atime-inclusive stat equality and refused;
its fresh v2 excluded read-induced atime, retained the failed source and passed.
The label mutation was not replayed. Source7 capture/gate and the next confined
INSPECT generation remain pending.

The independently reviewed three-lock peer/test/seven-contract patch
`a174f684d40185b12f848a337711bb11c8721b17bc0a67f5f279f727b29f35c0`
is applied;84focused production tests pass, zero skips,0.67s. Peer SHA256
`269a6751472ac72e986cedbe72287125bdc405673957535b2893fefcdd71a709`;
CIL20, eleven roles, fixed argv and observer drain remain unchanged. Fresh
sequential kernel20 queries confirm11protected helper denials and four manager
mounton permissions, flags0/sequence38. Results
`.scratch/web-006-selinux-kernel-av-query-v9-policy20.json` and
`.scratch/web-006-init-mounton-query-v5-policy20.json`; no actual-role/inode
acceptance is inferred.

Source7 captures1357files, snapshot
`a1fe53e423bd1351c357573d77b8d859ceab462f664a7d1f36951556ca040d5a`,
inventory SHA256
`0de044e97e6652a1bb1cfd6bcc5d85dddb21ebbce26178a9b1c4a1a729a7ccfa`.
Its strict gate started20:41:00UTC, original child2785937/start408380239, and
remains running. Two source7UI builds match the six-file asset manifest
`3df4287d83ecf791d63b4ff9dd93badba7b5b60a246567ee8947625cdba04fea`;
wheel `b19a9989218d84d9f6b476cc7a361c58e4190fd861edcc1b40062981e959c9dc`.
The pinned UBI10micro image builds successfully in31.23s, actual identity
`ec5852ce909d8929e4752835e757d89dd1744bb8c6d9b675361490994ba25274`.
Artifact summary `.scratch/web-006-artifacts-v7-hene_8c5/SUMMARY.json`, SHA256
`89ec5aabd1d5d46e4a7a9a2f2684ca88cf8fb82f7c833fae34324327c768259b`.

The reviewed corrected source7public updater passed in1.86s with its original
SSH child and both output channels drained/reaped. All1357guest hashes/modes
match source7;13changed paths and all oldsource4before-bytes/modes are preserved.
Receipt `.scratch/web-006-update-guest-source7-v1.json`, SHA256
`b0d37c8d88053d02d635d41efec208485c60a1dacc30873ddbb5d8927ec5d5d7`.
This is source update only, not image load, profile staging, role start or
functional acceptance. Fresh confined INSPECTv11 is under source review.

FixedINSPECTv11 also fails125 under20, generation
`fe7989de9d52400abf2fe2191f1df061`. Its24996B DRAIN SHA256
`0d2a0298557fe8693ac59fa8ce284ee952e700de0273b9a5d6f82bc25977a8b1`
records all12original PID/start pairs gone. Root independently confirms all12,
physical cgroup absence, MainPID0 and empty ControlGroup in fresh closure
`.scratch/web-006-fixed-inspect-v11-closure-v1.json`, SHA256
`ff1849637b7f6f008ca267be1da93824782b2460e7353d1763f367b3e3e5a9cf`.
All three preprovisioned locks, original inputs and audit container remain
unchanged. Actual private258B stderr is classified without raw publication:
`failed to open 2048 locks in /libpod_rootless_lock_983: permission denied`
boolean is true. Classifierv2 SHA256
`b3f10b0420085bb918613dd5224871290f14babd2e0d4677da3dbe92548ddc24`.

Fixed O_PATH-only metadata joins AVC inode3 to the existing stock shared segment
`/dev/shm/libpod_rootless_lock_983`, device25/inode3,983:9830600,single-link82488B,
`container_runtime_tmpfs_t`, without payload read, mapping or mutation. Metadata
receipt `.scratch/web-006-shm-lock-metadata-v1.json`, SHA256
`c3beb18dcb58838ff975891f2f5b788d3930c0d131d95ff7c7cc09858c17bb8d`.
Pinned primary source confirms mandatory runtime initialization opens this
segment read/write and maps shared writable pthread coordination state. Primary
receipt `.scratch/web-006-shm-lock-primary-v1/REVIEW.json`, SHA256
`cb5f8384b20cf2916c7ca85329a7386766976c909dd0f922b66682bed454b47d`.
Broad existing tmpfs-type read/write/map grants are rejected. A distinct
`hfcache_host_helper_engine_shm_t` type and twelfth `engine_shared_memory` role
are being reviewed, preserving ordinary-lock map denials. Exactly the fixed
root-owned01777 sticky `/dev/shm` ancestor requires a narrow exception; no
general writable-ancestor allowance, automatic segment creation/relabeling or
change to initial capabilities follows. Source7 remains frozen while its gate
runs. Final native/rootless staging is held until this prerequisite converges.

Source7artifact transfer passed, all10public/protected artifact hashes verified,
with no profile activation. OCI export7 passed in8.41s; no source7image guest
load is claimed. A native-stage binding naming nonexistent `SUMMARY.json` was
caught before execution; a fresh source-onlyv2 uses the transfer's actual
`local-artifact-summary.json` leaf and retains the unexecutedv1. Fifty-five
independent native/rootless binding/overlay checks pass, but both stages remain
unexecuted pending the final converged source.

The independently reviewed21scratch policy adds a separate shared-coordination
type and only FILEgetattr/open/read/write/map for helper and legitimate engine;
ordinary-lock map and protected-file denials remain intact. Owned compilation
passes13.67s, all four child processes and outer2797692 reaped/gone. Policy source
`4d454488bf05a7b96acf9ed5bcb47546caed59cb8c958594e414d6a63093ec49`,
kernel `1396378f4d4a449b47bcbb7dff14ba2b3d922d6a4a1f1e891cf1c7e3d69e288d`,
protected21RESULT SHA256
`1d59565d526b4d1d53ba940e399e8b1b879c7336c0cba463e5299532c4796563`.
The loader's embedded bytes and immediately following hash assertion were
independently executed in isolation before the actual owned load. Thirty-five
source checks pass. Fresh sequential kernel queries at flags0/sequence39 confirm
11protected helper denials, four manager mounton permissions, the five intended
SHM rights, and denials for SHM creation/mutation/execution, ordinary-lock map/
execution and broad tmpfs write/map. Four-row receipt
`.scratch/web-006-shm-kernel-av-query-v1-policy21.json`, SHA256
`f327e59bb98bfcda347d5c8eb9d54b86f9defc95f163f2cb633ef99d99f7b22a`.
These are kernel queries, not actual segment/role acceptance. No SHM label has
changed at this checkpoint; the one-inode recipe remains under independent review.

Before21installation, the read-only fixed authority-input survey passed, all
query children drained/reaped, without an engine call or secret body read.
Receipt `.scratch/web-006-authority-inputs-survey-v1-result.json`, SHA256
`8d664d870565a23fb1f17589669099ddc809a7f23d3ff173be5807e7114ec2d0`.
Its20policy checksum is historical, while original unit/tmpfiles contexts and
safe browser/server input hashes are usable preparation evidence. The survey's
v10closure scope is retained exactly; freshv11closure is a separate receipt.
An unbound authority3 draft retained a controller5 digest despite newcontroller6
paths; independent review caught it before execution. The original draft remains
on HOLD and a fresh correctedv2 is source-tested, still unbound/unexecuted.

Root then executed the independently reviewed SHMlabelv2 recipe, SHA256
`877d368a2949ba07c840fdfa0e4de9c7d5d98755e6b144d146dd958fc4f5ff37`.
It passes4.08s, six commands and outer2807618reaped, one existing inode only,
with no segment body read/mapping or role start. The unexecutedv1 is preserved:
review found its old-lock preservation claim excluded timestamps, and two new
negative regressions demonstrably fail againstv1 before thev2 correction.
All76v2checks pass independently, including both mtime/ctime drift refusals.
The actual label operation keeps all nine metadata fields on each of the three
old locks unchanged. Protected
`/opt/hfcache-web006/engine-shared-memory-labels-v1/RESULT.json`, SHA256
`781c3a30ed34b18e5459c78e97a2c2a323f75ed3fb0083eb6544ba4aa260c775`;
local projection `.scratch/web-006-shm-lock-label-v2-result-v2.json`, SHA256
`22986546d7c4c5d29c42299e68d1ae41154f9b2ca5e4ee6163b4d4ce848d4010`.
One exact fcontext was added; target device25/inode3 remains983:9830600,
single-link82488B, with only label/ctime changed. The first read-only projection
mistakenly expected BEFORE metadata in RESULT and refused; freshv2 follows the
actual schema, without replaying the successful mutation. Nextv12must establish
actual helper-mounted-view metadata and unchanged MNT continuity across USER
entry before claiming the engine's observed segment is the root-labeled inode.

After gate7 completed, root applied the independently reviewed coherent21v2
source/role/tests/seven-contract patch, SHA256
`f79b10ae9d54b2620384df1622de41ac6e93a7046c5c7964b2182964dabe2a74`.
It adds the separate twelfth shared-memory role and fixed metadata guard while
preserving the ordinary-lock functions, engine argv, native path and observer
drain. All1012host/prepare/container-helper/host-fixture tests pass, zero skips,
39.07s: `.scratch/web-006-coherent21-all-host-applied-root-v1.{log,xml}`.
Tracked peer SHA256
`888b4e26c417bd02b6d4a821f17a6b449ece97e3ae08cb7c96e5bc8cd75becc8`.
Source8capture/build/gate remain held until the new confined inspection proves
the actual mounted segment, avoiding premature installed-stage acceptance.

Before executing the next diagnostic, root found that its new shared snapshot
opened parent directories read-only. A freshv12-v2 changes only those new
ancestor opens to O_PATH, preserving receipt-body reads and segment metadata-only
access. Originalv12 remains unexecuted; the restrictive-directory regression
fails against it and passes in the347-check successor. Independent reviews
confirm unchanged argv, old lock functions, masks/capabilities and entry2.

Actualv12-v2 still fails125, generation
`8e50ed1533024e07a14878d7f65f4abd`, but proves the actual helper-mounted SHM
inode device25/inode3 and its exact independently installed type. Its worker,
entry-before-USER and entry-after-USER all report the same masked MNT inode
4026532309. The root worker emits this metadata before child creation; its
snapshot matches the independent root baseline. This closes that narrow view
question, not the overall inspection or installed acceptance. All old3lock and
SHM identities/labels remain unchanged. Exact24584B DRAIN SHA256
`0c76680f4706767b931ef16127ba694f0f57b553ea82390ccc9a66bb1dbeac89`;
fresh closure `.scratch/web-006-fixed-inspect-v12-v2-closure-v1.json`, SHA256
`53ee17f612caf351bcee33377b35e098b18d085d67cfe561449ebda1f5c94650`,
confirms all11recorded pairs gone and physical cgroup absent. Root outer2811742
is reaped after2.14s. No worker/API/Caddy/helper canonical role was started.

The new denial joins tmpfs inode46 to the existing fixed
`/run/user/983/containers/overlay-layers/mountpoints.lock`,983:9830644,
single-link64B, user_tmp_t. Its462B private stderr is classified using an exact
fixed error Boolean without raw output publication; true `open` denial receipt
`.scratch/web-006-fixed-inspect-v12-v2-stderr-classification-v2.json`, SHA256
`de96f62825e0f6eab25b7197f0d2f7cce740e9a9216fadbe1bb380f3cbf55d5c`.
O_PATH-only metadata receipt `.scratch/web-006-mountpoints-lock-metadata-v1.json`,
SHA256 `82b4c1ab29a986d3efa0539690858b5cf38f0179ec371c64dccc949e09f00ca6`.
Pinned source traces real inspect to lazy layer-store construction and this exact
runroot coordination lock's required read/write open. Cached-alive boot-ID writing
is not the observed cause. The proposed fourth ordinary lock uses the existing
engine_locks role/type/rights and unchanged21CIL/kernel, with its own independent
fixed-inode preparation receipt; no broad user_tmp_t write grant follows.
Source8 capture remains held pending this concrete prerequisite and next proof.

The independently reviewed fourth-lock peer/test/seven-contract patch is
applied, SHA256
`4d26527885c567af1d8db2100218426fc5b9f04f222bbc2db4ca5162cb45abb4`.
Only the fixed UID-derived path specification changes functional peer behavior;
all existing FD/ancestor/label/budget/argv/drain/SHM functions and21CIL/twelve
roles stay unchanged. Peer SHA256
`e9b63241664c9a04f2ac9e1e6245a63ea81c2c2af922a042701e87a5992718c0`.
The applied host/prepare/container-helper/fixture suite passes1029tests, zero
skips,35.44s, `.scratch/web-006-four-lock-all-host-applied-root-v1.{log,xml}`.

The exact one-inode mountpoints-label recipe
`8c60e6fd1f8515eebd06993abc45c006f97135dea053480dce476240d8ebce94`
passes90independent source/model checks and then actual root execution0 in3.19s.
All six children and outer2814568 are reaped. It adds one exact context and
labels device45/inode46 through its held descriptor; ownership/mode/link/size/
mtime remain unchanged. All nine metadata fields and full labels on the older
three ordinary locks and SHM segment stay unchanged. No body is read, no new
file is created and no canonical application role is started. Protected
`/opt/hfcache-web006/mountpoints-lock-labels-v1/RESULT.json`, SHA256
`72d6f18617823fed26268d3a0e823e90c4f40f3daeb6e6a57d0f64462107a296`;
local `.scratch/web-006-mountpoints-lock-label-v1-result.json`, SHA256
`b1f5fbb248bc7616f58822d2a457f6c107f1eab47c919ba79417f5f528b6d57b`.
The nextv13diagnostic retains worker SHM/mount continuity proof and adds only a
separate root metadata snapshot for this fourth ordinary lock. Its actual
inspection result, source8capture/gate and installed/Caddy/browser acceptance
remain pending. All prior failures and unexecuted drafts remain preserved.

Actualv13 fails125 at the engine and20 at the diagnostic boundary, generation
`89be3887c55a41a7b0ab0c877b3aca79`. Both owner and independent source suites
pass376checks, zero skips; the new root-only mountpoints proof preserves the
entry2/worker/SHM code and existing policy21. Actual execution2.10s reaps outer
2817230. Its retained25481B DRAIN SHA256
`6537f4fe1077158d268461d51c1f5e960659a7d0db54ecdbc4e20db2482b2188`
and fresh root closure
`.scratch/web-006-fixed-inspect-v13-closure-v1.json`, SHA256
`46a390f34ef182e2a1bd1cff8d6455217b78754646172e83d47cfbaa54c70ccc`,
confirm all11recorded PID/start pairs gone and physical cgroup absence. Canonical
source, retained audit container, stock storage, four locks and SHM identities/
labels remain unchanged. Independent root-only O_PATH captures before execution
and after actual wait/closure additionally compare all nine metadata fields and
full contexts on every ordinary lock: both stdout hashes are
`44f9d5066c87c21ac0c4876b9755a37fe95ce0e4586ff497deb5120ff5afe676`.
Recorder `.scratch/web-006-ordinary-lock-nine-v2.py` passes13independent checks;
its first unexecuted draft required an installed source path, so v2 removes that
requirement for the actual stdin execution without changing metadata predicates.
This is failed diagnostic evidence, not installed acceptance. The new denials
include image-layer metadata getattr; exact private-stderr classification and
fixed-path inode proof are pending before proposing any policy change. Source8
capture/gate and installed/Caddy/browser acceptance remain pending. The current
documentation checker passes205human documents and27helpers.

The private418B stderr classifier subsequently confirms the exact
`stat .../overlay-layers/layers.json: permission denied` marker, with no raw
output publication. Classification SHA256
`59c418a71b051129c9ad87e994c2ef107de56be818be872e4aa6c682fb59f8c0`;
O_PATH-only fixed-file metadata SHA256
`4b10644cc191761ed2b63b07be406e5bcfd56e0114e10e4651dddb8f02f070a5`
joins that operand to denied device64515/inode60046611,983:9830600,single-link,
8299B, container_ro_file_t. Pinned source requires stat before layer metadata
reload and treats that error as fatal. The narrowly reviewed22policy adds only
container_ro_file_t FILEgetattr to its existing open/read rights. No new role,
file write/map/execute right, or protected-file access is added.

Owned22compilation/loading passes0 in10.96s; all four children and outer2818813
are reaped/gone. Protected
`/opt/hfcache-web006/selinux-policy-install-v22/RESULT.json` SHA256
`aff11bbdfd8f6667c2295787c1e1b2edfc5a8857190a844664bdd64a8c0d70e4`,
source `05e47fed918aeba895ae9af9878f6788be12c436b72f00f415a1fa699d17f8e6`,
kernel `76340c0cad7db379ef89f6bd85a5ecdbd5708d8fcec22b9d0a92e8cac01038a8`.
Fresh protected receipt readback SHA256
`de0a6e4dc4e7de1a9033e22a926933f4da2426a6b2f657d3b06dca05a5189ef6`.
The coherent5path source/test/ADR/operator/security patchv2 is applied, SHA256
`0ad087ef9960c5abcad4dfc0d1f976521140e7fb4b6682832d03502cf7bca9aa`.
Its v1 missed a second exact-permission test assertion; the independent34pass/
1failure remains retained, and correctedv2passes35independent checks. All1029
applied host/prepare/container-helper/fixture tests pass, zero skips,41.55s,
`.scratch/web-006-policy22-all-host-applied-root-v1.xml`. No installed acceptance
follows. Fresh kernel queries and the reviewedv14diagnostic remain pending.

Fresh22kernel queries pass sequentially:11protected process/file denials,
four manager mounton permissions, four SHM allow/deny rows, and the new image
FILEgetattr permission; every decision flags0/sequence42. Results respectively
`fc6ac191a556eed49e1bb2fc30b0d7d3be7af16a2c5af8afe87f9129e91e269a`,
`0650b12205fc07b8e809e30005ac96d7d94e7bc0a1e216a035e0976cda2b3997`,
`40d3291cc6f28fee9af6a82e20fd77b5cf04e93e6854661cd87711c25591e347`,
`fc75ebd796570cc239ecb1a34368229380e2bfee01515823d395c01e4674fa06`.
These are exact-context kernel queries, not actual installed-role acceptance.

Actualv14fails125/20, generation`8a7c12f49de743dd9d3238d2a43e8460`, after
390owner checks and16independent targeted checks pass, zero required skips.
Outer2820193is reaped after2.10s. Its25482B DRAIN SHA256
`c80d7490588e2be56853de16af05252b51590de8c0ba90ef28f0c770fd6b8414`
and fresh root closure
`.scratch/web-006-fixed-inspect-v14-closure-v1.json`, SHA256
`796afd0f1d8b07b38ca0bc3741891c59575bce885cd7e69d99bc879f7bfdabda`,
confirm all11recorded PID/start pairs gone and physical cgroup absence. Full9
ordinary-lock metadata/context captures again match exactly, SHA256
`44f9d5066c87c21ac0c4876b9755a37fe95ce0e4586ff497deb5120ff5afe676`.
The first read-only diagnosis assumed the previous3596B log size; actual3597B
refused that guard. Freshv2uses the actual size and retains the failed projection;
the diagnostic itself was not replayed. Safe diagnosis SHA256
`0f1c2c3d4eeeb3c8010bbdcc0aeacf78a726d6e5c17d426e281b6c5f0face97b`.

The private437B stderr is classified without raw publication. Initial exact
`lower` and then expanded closed `lower-layers|lower` classifiers preserve all
earlier results. The final marker identifies only the fixed layer identifier
`35637560820c5e52b609350c4ce5a4a05ea3718e0846ad89297c0970be4a5522`
and `lower-layers` leaf, classification SHA256
`6f63ae59bb8d513f3f1039cd210a65bd22e8df5f0e908e8ba7f43a05a65d75f6`.
Root O_PATH-only full-ancestry/two-leaf survey SHA256
`eb8c3851b7b59de56eb163b80f7705b0bcccc02fdcbe387cd94184891b257fe8`
finds the layer directory device64515/inode72160880 owned165536:1655360700,
container_ro_file_t:s0. Both existing lower metadata leaves are983:9830644
with the same type. Other ancestors are root-owned searchable directories or
983-owned0700 directories. Pinned driver source opens lower-layers first and
falls back to lower only on ENOENT; a search refusal is fatal. The actual child
has only namespace SYS_ADMIN, with empty inheritable/ambient sets and unchanged
masked MNT. Current mapped ownership and actual SID kernel checks are being
completed before deciding how to support that keep-id directory safely. No DAC
capability, chmod, ACL or broader file-type permission has been introduced.
Unrelated DBus warnings/AVCs do not justify a DBus grant. Source8capture/gate and
installed/Caddy/browser acceptance remain pending.

Actual fixed-pause proof SHA256
`217430d2889cee9a8d950d9c228d2ae004bcceefcb8dc4df4f25f447904a33db`
pins live70549/start6647855, USER namespace4026532304/owner983, and UID/GID maps
0to983 and1to165536/65536IDs. Exact-context kernel22query SHA256
`3d9e27bea09c6f2e86cdc46f9d47393bd8987490b436572c85a68cf7c8a32dff`
allows the observed SID's directory search and file open/read, flags0/sequence42.
The mapped-owner0700 directory is therefore a genuine DAC traversal barrier.
Decision151 replaces only the earlier namespace SYS_ADMIN-only retention rule:
after verified USER entry retain exactly DAC_READ_SEARCH/SYS_ADMIN, bits2/21,
mask0x200004, with empty inheritable/ambient sets. Initial root/account ceilings,
original masked MNT, fixed argv, budgets and object/attachment denials remain.
SELinux explicitly denies namespace DAC_OVERRIDE. Read/search is mapped-inode
authority, not path-limited; temporary USER-entry capability reset and ancillary
syscall limits are explicit. No chmod/ACL, initial DAC or object-type widening.

Experimental23compile/load passes0 in11.09s, outer2824279and all four children
reaped/gone. Source
`f08958f30d5b6fbbc0716df8dd110f9e31aaddc82e17eb7ba55af5540cd601c2`,
protected RESULT
`5b7744c38f080cccc45fa6401ab1628cb79442b681a1072eec20d1d078c0c449`,
kernel`a823d7cfdf4efa56755a0d34b481361ccca3ae222ff9d00fdbeab1ea5cabee91`.
Root readback SHA256
`dbbca2b4f5b9b522363b6731714e3e6f121b3b0bc8cec7927c1765d0f2db2146`.
The independently reviewed10-document contract/ADR151 patchv2
`530a0d7912c130f2dfaeb8a8632e96c2692e30ab02dc6d7eabcbe59871096bdf`
is applied before the5-path peer/CIL/test patchv3
`adf1fb4ef417763ea9a7d6097c041edfa8a53bdb11bf4e1ed8eb92b3ba3da687`.
Retained earlier drafts document the stale second permission assertion, Ruff
assertion style and overbroad all-phases bit-absence wording; their corrected
successors preserve earlier history. Independent158focused checks and all1072
applied host/prepare/container-helper/fixture tests pass, zero skips,39.93s.
Actual documentation checker passes206human documents/27helpers. Six sequential
kernel23queries confirm26fixed rows, flags0/sequence43, including initial DAC
denials and namespace READ_SEARCH allow/OVERRIDE denial. These remain queries,
not inode-operation or installed-role acceptance.

Actual confined prototype15passes0 in2.29s, generation
`ee35e24804b5499cbeed64032c526c5a`, after411owner and18independent targeted
checks, zero required skips. New entry3 preserves the old entry2 bytes, fixed
engine argv, namespace/mount proofs and post-reduction archive/Hub/IP/alias
negative probes. Outer2826054is reaped. Its26018B DRAIN SHA256
`537202f525c4eb8d7228fffa9340cd04bc1d9ff4f5bd6543d9137f1004b2fff2`
records completed=true; fresh independent root closure
`.scratch/web-006-fixed-inspect-v15-closure-v1.json`, SHA256
`3c0b7247037297ca220d051d37fc2abb26a0f9764c4cc2f3c4419d0ad92cdc3d`,
confirms all12recorded pairs gone, physical cgroup absence, MainPID0/empty
ControlGroup and inactive/dead/success. All four ordinary locks retain all nine
metadata fields and full contexts, identical before/after hash
`44f9d5066c87c21ac0c4876b9755a37fe95ce0e4586ff497deb5120ff5afe676`.
Safe diagnosis SHA256
`1a29943850613196d18db10c94b0fe775b4af16278f50066f54b4a40ac9cf06c`.
It omits the successful RESULT body; a separate closed safe worker projection
is being prepared for direct independent review of actual masks/denials. No
diagnostic or source/build result establishes installed profile acceptance.

Source8captures1359files, adding ADR151and the SHM test since source7, snapshot
`541d63bfb41fd2b59d5957a015d6ea209a1fb7b18e2ac1f7f7a254c73bc55d20`,
inventory`993da546706fdfa4093fb5aaa945b21c4777c98c6ec981de28c945e16685f9d4`.
Its strict gate starts22:17:46.899UTC, original2826664/start408960874, and remains
running. Two UI builds match six-file manifest
`3df4287d83ecf791d63b4ff9dd93badba7b5b60a246567ee8947625cdba04fea`;
wheel`5a52465b108606d80387cf6daf0e2fcfa3cdadc07ae1e6f5ca04915bc224bf94`.
Actual pinned UBI10micro image11build passes27.51s, identity
`e3d2085fc1080bcf988a39487041de910ecce2e2e7411845246cfed916904ff3`,
receipt`bdd12165e3267eefb61da69f295a5fee8e303fb76d984cb08037b8ea0a91fae9`.
Guest public source8update passes1.42s, all1359hashes/modes verified and source7
original bytes/modes preserved, receipt
`2abe249f7a198660114cd889889c9935309b01eed59f890ee6026ec40c65cccf`.
No image8guest load, final native/rootless stage, canonical role start or real
installed/Caddy/browser acceptance has occurred at this checkpoint.

Further actual source8 checkpoint2026-10-21: safe successful prototype15 RESULT
projection SHA256 `ec04ab2dad3ffc3c3607b69cf630f9c28289cdc900ea6f57cb2334daf709f070`
and independent reviews confirm the root0xc0/account-zero/namespace0x200004
boundaries and recorded denial probes. Actual inode/ATTACH proof remains false.
Artifact8 transfer passes0; OCI export8 passes0 in8.02s and transfer in4.31s,
all original children reaped. The first export invocation omitted its required
phase and argparse refused before effects; that failure is retained separately.
Export receipt SHA256
`38838334dfa762dd13812b52c49488543cab99bf06f0799194bc17b3b2d0003b`.
Actual guest image8 load passes0 in7.45s, all seven command children reaped,
original pause continuous, user981:981 and genuine micro base-layer prefix
verified. Guest image size204759819bytes is its own observation. Runtime
absence/package/UI audit is still pending. No container/application was started
by this load. Local safe log SHA256
`9be2d1264768ddfb1332e1bcfb74f133b93f6b18d799fe4609ed103b9d075c61`.
Original native installer source8 staging passes0 in44.15s,108package leaves
verified. Full1359-file protected source is captured. Complete source1 is
preserved with NOREPLACE; relocated absolute venv paths are explicitly not a
runnable rollback claim. UV_LINK_MODE=copy; the source installer, not the wheel,
is the actual input. Selector remains absent and canonical helper unchanged.
Native stdout SHA256
`af6fb2394c9a4ea6a0f852d8b158fce03a7b4b717b87e6a95b5195ef375f4e37`
is not the protected canonical RESULT digest; fresh root readback is required.
Four rootless overlay files prepared locally from indexed source8 templates
pass, receipt SHA256
`d2ad139f59d98da5ff796eb2c2520f391a38ccc99a95009d9dd19dfb99b21472`;
transfer and rootless stage remain pending. Source8 strict gate remains running.
No canonical WEB006 application/helper/Caddy start or required installed/browser
acceptance is claimed; no production or NAS action occurred.

Source8 strict gate actually passes0 at2026-10-21T22:39:21.543973UTC in1294.645s:
`historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`. Original2826664/start408960874
normally reaped and proc absent. All1359captured hashes/modes remain identical,
no changed paths. Actual7729Python passes/52opt-in deselections,572historical frontend,
2786web unit and2846component passes, zero required frontend skips; builds,
locked base/server/server-plus-MCP install/import/help/version, two built startup
Chromium checks and real HTTP/API React read fixture pass. Result
`.scratch/web-006-gate8-result.json`, SHA256
`cf87fd5ac21a69533bf57fe1d8e10ef58b3131c9aec5304ec4d8160510e8ab7f`;
log SHA256`cd5d2c55071a04108d7ce578f19dac2f1b9f56066300f9cc68d5bb4d35ac871d`.
This is source-gate evidence, not installed/shared-Caddy acceptance.

Four prepared rootless inputs transfer0 in0.786s. Original rootless source8
stage/render passes0 in4.60s, outer2846966normally reaped, explicit unchanged
stage argv through a separately hash-pinned caller; no app start or bindings.
Fresh held-FD/full-nine-field/context root readback passes0 in0.766s, SHA256
`31d45898864d84a93505d6afa3c7f50a36ae549fd834b2e700037df91dbe7888`:
protected staged873B SHA256
`6cbf5411c4be2fb2a768085db36cc1c6fbfb019b18a71feac807f1bf70a1f431`,
provenance11339B SHA256
`e5f5592999919be6e93d2129bfb9722b58472223fadfa902949f1ca59ffc331e`.
Software0.2.2/deployment-fixture0.2.3 remain explicitly separate. Fresh protected
native/policy readback0 in0.899s, SHA256
`40fce4b12e1787bad7255034da5bed9d11bd4e76442d072f880a14c3b1680d88`,
confirms actual canonical native RESULT6913B SHA256
`0363773616eca029abe5cc4df63eb09da975b6e6fb8b5b701a0cb18cd0fb8bd9`.
Selected priority400 CIL module's actual retained listing checksum is
`f08958f30d5b6fbbc0716df8dd110f9e31aaddc82e17eb7ba55af5540cd601c2`;
source equality is observed rather than assumed. Kernel23digest brackets these
reads, Enforcing and owned read-only synthetic XFS archive mount verified.
Runtime image audit, canonical installation and required installed/browser/
isolation/fault/drain acceptance remain pending. No source change justifies a
repeat of the source8 strict gate yet; any subsequent source change will require
its own captured gate and artifact reconciliation.

Canonical helper publication attempt1 actually exits1 in0.944s; outer2849746
is normally reaped. Source042543d4bfe8bb9818bfc90805cdc741cde11c84d248a31a38e95d456093f9da
passes96 adapted source checks, but actual global_preflight refuses its first
retained-container inspection under UID983. The binding incorrectly combined
18 WEB005 containers from other engine accounts/backends with the UID983 image
audit container. Literal/AST/hash/count reviews missed this semantic ownership
error. Log SHA256
`3aace45c5ee3a01c41ebb0e32c858c881d28265bb673e9116b07eddfc7e55c0c`
is retained. Refusal occurs before WORK creation, any backups or source
publication; no helper/policy/index/key/selector/service changed. The fixed
command drainer waits/reaps before refusing, but this preflight failure did not
persist its in-memory individual command PID/start records. Those identities
remain unknown rather than reconstructed. Correct owner-qualified CID diagnosis
and a fresh all-target absence check are required before a new publication
attempt. Future caller must retain safe command metadata even on refusal.
Preliminary sourcecheck-v1 was written before its first test run's10 stale
invalid-fixture failures were inspected and is explicitly invalid evidence;
correct sourcecheck-v2 and96-pass XML retain that history. No source mutation
or acceptance is inferred from either source check.

Actual new image runtime audit source8 passes0 in41.715s, outer2850024reaped,
stdout/protected receipt22387B SHA256
`febd7eeebc1310f190e9454a1452ff9eac77aef253cf568d1d16c5c29e3cac38`.
All108Python files/sixUI files match; genuine pinned micro ancestry and35named
PATH tools/eightimport modules absent, read-only/network-none/capless/NNP,
inner981maps host983, no credentials. All17command children0/reaped. New retained
container66721b2f78d97a9a3af9f8b325ab91f5e4fdc712190bc58cbd1ffc4bd2c1d65a
exits0. Fresh independently authored closure passes0 in0.594s, SHA256
`7668fd06d4971ae02bae79e8c7f990827595210d6d1a874ef4cf0d8a57e4019d`:
all18guest PID/start identities gone, physical cgroup absent before/after,
original/new protected receipts unchanged; stopped container retained. Runtime
image proof does not establish installed roles or clean release acceptance.

Inert controller6/browser2 captures transfer0 in0.588s, original SSH2850863/
start409128727normally reaped. Local receipt SHA256
`7a0265d2fc755a67a8f8152852163276a16246ea14b5a0ff68a6e987de462fc3`;
protected /opt/hfcache-web006/fixture-source-captures-v1/RESULT.json1440B SHA256
`36061f4b8655c4b319bff86737fbb206a62e6ba5caafd04fe22f345321ce7a14`.
Controller90634f8e6ef7ff8f4beaaafbe0086f0fed1081a05bb61ab3aa329cb2b4db413c
and browser5278841d258c2ddfbe01088893e98c5f41c6b4e0c673853a1b2b651be02fefb8
are root-protected inert source copies only; no execution/authority installed.

Owner diagnostic1 collector exits0 in0.995s, SHA256
`50e00a6f29527fb34ae833b1ca5592492096bdd3447f0abf8ce09d6deab99683`.
Its wrong983/oldCID query returns125/no-such-container, confirming account
mismatch; both positive bulk queries fail125 on formatter evaluation. Collector
success is not inventory acceptance. Closed exact106B error projection0 in0.434s,
SHA256`9ed4a3b9a660ceeb3a1cbaba6d04cd57c147807dd050651730f93ce573150e31`,
identifies template/.Id field evaluation. Diagnostic2 tests exact same JSON
format individually for all20positive CIDs; all fail125 with identical106B
error hash0b30d9fd8d158b66ef4899de2451fb390621def4f2a9228eaf6499950f6a5a4a.
Collector exits1 in3.905s after retaining all21normal child reaps and proof
inventory_validated=false; SHA256
`6899e69fafacd08f8359fad5183cc0351e8a0a7596c8ffa82dce96becb625bb9`.
The earlier bulk-only inference was incorrect. Pinned Podman InspectNormalize
source atcade97a52ebdf9dbf9e81de8009015776837a074 rewrites only bare .Id to .ID;
it leaves json .Id invalid. All18old005 CIDs belong to the original UID1000
VFS browser engine, independently derived from original postverify source;
the two new image-audit CIDs belong to stock UID983. Scratch diagnostic,
canonical preflight and authority quiescence formatter correction is pending
actual proof. Production sources contain no affected JSON literal; source8 and
its green gate remain unchanged. No canonical publication retry has occurred.

Diagnostic3 changes only the JSON field literal to uppercase .ID and a fresh
WORK. Actual0 in3.911s; outer2853386reaped, all21original commands reaped,
20positive correct-owner retained containers stopped. Wrong983/old005CID
returns125/no-such-container. Exact-owner inventory is now validated; no
canonical WORK existed. Compact stdout SHA256
`a1c324af6cce2856f99e8b61b1875f8d8814dfe1bef6e0c3e385affca5e0eb57`.
Its distinct protected pretty RESULT32104B SHA256
`6228910c45a47650ab455d2d5e5c117d7b396cbbc702b093ad2b5577ee9cc49b`
is subsequently actually held-FD read/rejoined by the canonical caller before
publication. Separate historical1000/VFS CIDs remain preserved and proved;
only the two genuine983audit CIDs are passed to the stock983 engine.

Corrected canonical attempt2 source1a8d6705 changes only the preflight .ID
literal, fresh WORKv3,342 known prior pairs and correct twoCID selection.
All other installer functions remain identical.96source checks and21closed
caller checks pass, with independent source/owner review. Actual publication
passes0 in1.697s, outer2854463normally reaped. Safe caller stdout3482B SHA256
`1ed3a45103300e01772662c90bd46d83a14ca52a85a747eabcc8dea84775fc5d`;
all five command children0/reaped with known starts, schema complete/zero
unknown starts. Protected /opt/hfcache-web006/canonical-helper-source-install-v3/
RESULT.json10362B actually read/rejoined SHA256
`b4186ccadafe484f1c89cf1c2dd96d458587039a74e0a6b6d80344ad36075a7e`.
All seven helper source/unit/tmpfiles/CIL targets publish, six originals retained
as inode backups; own link/ctime transitions are recorded, not described as
unchanged metadata. No reload, tmpfiles invocation, selector, index/key/policy
installation or service start by this step. Independent seven-installed/six-old
inode/hash/context readback remains pending before authority provisioning.

Fresh read-only UID983 baseline passes0 in0.441s, before/after exact with held
pidfds, SHA256
`356e8fea0d462d8bc5facff4087119dce7852a24edf18de13097b7d2bec96c1c`.
Five persistent infrastructure processes are reviewed for preservation:
70491/6647766user manager,70493/6647772PAM child in the manager init.scope,
70549/6647855original pause,70559/6647880D-Bus launcher and70560/6647884broker in
the fixed dbus-broker.service cgroup. Parent relationships and original prewarm
epoch match; additional rows were explicitly reviewed rather than automatically
adopted. No other UID983 process exists in either scan. Source8 authority4
bundle remains inert/local pending independent publication readback and owned
upload; only fixture formatter case and actual source/input constants change.
Required real installed-role/isolation/Caddy/browser/fault/drain proof still
has not run and WEB-006 remains incomplete. No production/NAS changes.

Independent fixed installed/backup readback actually passes0 in0.492s,
outer2855562normally reaped. Safe10153B output SHA256
`8303357a006c1792f91af20b1d2a8aebf8fc2ffeedcc6e160ad33f043fc3020f`
confirms seven installed and six original-backup inodes, full current metadata,
contexts, source hashes and intentional1to2to1link/ctime transitions. All five
canonical command identities are gone. Selector/authority remain absent; no
writes or operations. Source8 authority bundle459a61d1/inputs dde9c732 binds
347 known prior pairs,25prior units, five reviewed live infrastructure pairs,
two stock983CIDs and separate original1000VFS closure. Four actual input/source
hash bindings and only the .ID fixture formatter change; no production source
change or installed acceptance is inferred.

Authority source/input upload1 actually passes0 in0.473s, outer2855988normally
reaped, log SHA256
`58dc98f60fa8a3ab99e67864bd7219e53c58d4eaae8d64678c75f155dabb5107`.
Root outer preflight independently pins original SSH90b18ee9/QEMUb7a2b69f
and archive4741e35d via no-follow regular-file/metadata/hash checks. Guest
identity/boot/Enforcing/no-external-filesystem guards and fixed two-file tar
hashes pass; both source/input files are published exclusively root0600 with
BEFORE/RESULT evidence, without executing authority or starting roles.
A later independent review places uploader052ec7cc on HOLD: it hashes transport
bytes then spec.loader reopens the pathname to execute, leaving an execution-
provenance gap; its inner argv reads also lack pins, partly mitigated by root's
outer checks. No swap is observed, but verified-executed-byte/full-nine-field
provenance is not claimed. Do not replay this upload or overwrite its files.
A separate readback-only successor must capture/execute exact held transport
bytes and pinned argv, then verify only the two already-created guest files and
upload receipts before authority execution. Preserve uploader1 and its actual
receipts. A finally-safe closed caller will also retain authority preflight
command metadata on refusal. No authority script or application role has run.

Safe readback-only recovery of upload1 actually passes0 in0.412s; outer2857489
is normally reaped. It executes precisely captured verified transport bytes,
holds/rejoins the SSH/QEMU/source/receipt identities and verifies the two
already-created root0600 guest input/source files without replay or overwrite.
Execution log SHA256
`0883e8446a96a11636210782f35b5471250ad591ed0b9f58cbf61ecac23f522a`.
This closes the prerequisite readback while preserving upload1's provenance HOLD.

Authority4 source459a61d1 with inputs dde9c732 then actually exits1 after7.831s;
outer2857575 is normally reaped. Closed caller stdout8630B SHA256
`cf129b423e17f22a94a7c408efa3d8e903965cef019d2d8dcd26a529e368ceb2`;
stderr975B SHA256
`b6db01d67c9bdaa3e705c396d985a0f4bc8c8381cc685cc2e7401056d65d06c2`.
All17 command children are reaped, with known starts and zero unknown starts.
The final child87088/start10201666 exits1 at the original unprivileged installed
manifest validator, after earlier provisioning effects and readonly bind setup.
Its1836B stderr digest is
`7459984776b75bf1c1d541ccc25632055816a2d7ce17537e8556bdec127dda30`;
the original drainer hashes/reaps then raises before raw-channel capture, so that
original stderr body is unavailable. Do not invent its error text. No authority
completion RESULT exists and no installed feature acceptance follows. Preserve
the generated key, proposals, bindings, controller, manifest and projection;
do not replay provisioning, reset partial state or blindly unmount. A separate
readonly diagnostic will run only the identical validator argv, retain bounded
channels privately after actual EOF/reap, and verify partial-state metadata and
role quiescence before/after. Root source review and14 diagnostic tests pass;
Independent source review also passes14tests/zero skips in1.53s, including
exact equality to the original459a validator argv. Diagnostic6839840f actually
passes its collection scope0 in1.038s, outer2859304/start409365124 normally
reaped; stdout9715B SHA256
`1bdce84025328c320faf6fac339110504bf475e2e8fb982960d47ede79cff705`,
stderr0B. All five guest commands and the original SSH child are reaped. The
validator87147/start10248759 itself again exits1; its1836B stderr is byte-identical
by digest to the original failed command and is now retained privately at
/opt/hfcache-web006/authority4-validator-diagnosis-v1/command-02-stderr. Collection
success is not validator success. Partial metadata is exactly preserved,
selector/policy/deployment remain absent, the projection remains readonly and
all fixed native/rootless/helper roles are inactive before and after. The key is
checked by lstat owner/mode only, with no body or digest read. A fixed readonly
closed traceback getter62e86560 then actually passes0 in0.431s;
outer2860128/start409380485 normally reaped, stdout4114B SHA256
`ca3a7191c62656305974708d40a2eedc540cf75b41e00d82b92832d032a511e4`.
Held metadata/context and all descriptors rejoin/close. The actual exception is
FunctionalRefusalError in unchanged scripts/check-web-functional.py path_input
line293: `functional .scratch must be private and current-user owned`. Only
allowlisted public frames and that fixed public contract diagnostic are exposed;
raw traceback/code lines remain private. This is a fixture prerequisite failure,
not an application isolation result. Exact current scratch ownership/mode is
being measured before a held-inode scoped correction and identical-validator
retry; no provisioning replay, key regeneration or original RESULT replacement.
Fixed five-directory metadata getter4bda7a27 actually passes0 in0.414s,
outer2860656/start409392383 normally reaped; stdout4317B SHA256
`f4bdadc7cc613b0e6b801b08a3a8baee7b2613a510072b86792972815d8cab21`.
The scratch directory is genuinely owned1000:1000 but mode0755, device64515,
inode27067813, links3, size26, mtime/ctime1792588588106000000 and context
unconfined_u:object_r:user_home_t:s0. All five ancestor/path/FD/full-metadata/context
joins pass and descriptors close. A scoped held-directory fchmod0700 is selected;
no chown/relabel or child-file/source changes are needed. The native API asset
root is under /opt/hfcache/ui, so this fixture-directory privacy correction does
not change the installed asset contract. Actual correction and unchanged
validator retry were then performed by finite recovery2d7051f3/guest b79369c4.
Recovery actually passes0 in2.178s, outer2861900/start409428104 normally reaped;
stdout11010B SHA256
`7014b39d8f34dd62a9d5d6787f38ae07af193140a321eafa4a78804eef9dd4f4`,
stderr0B. The identical original validator87252/start10311749 exits0, stdout140B
SHA256 `af239ee3d98ab0c0d308e22d7aafbb5e089d796bfb5bb6ae832dced6f78268b0`,
stderr0B. All five guest commands are reaped. Scratch remains the same
1000:1000 inode/context, mode0700; only its own mode/ctime change
(newctime1792625736257000000). Original captured controller load_control equality,
input/source bindings, readonly projection/all108 package leaves, kernel hash,
inactive roles and absent selector/policy/deployment pass. Actual control SHA256
`d94e8eb98ad99941f0881eb18be004c092af548520de96921640565c23a508e7`;
actual manifest SHA256
`25cf4880b08da1f217d276582a8f7c4adf8729347d737244a99c7fc9a6619609`.
Separate /opt/hfcache-web006/authority4-validation-completion-v1/RESULT.json is
written; the original failed authority RESULT remains absent. No role starts,
key regeneration, provisioning replay, relabel or original-receipt replacement
occurred. Installed feature acceptance remains pending.

Original installed functional runner will execute native first, unchanged, in a
fresh owned workspace. Rootless controller credentials deliberately require an
empty stock secret listing before creating six fixed synthetic secrets, and its
stop does not retire them. Repeated rootless generations therefore require an
explicit, separately reviewed fixture-secret archival/retirement procedure after
actual full drain; no blind reset/delete/replacement is inferred. Dedicated
actual inode/attachment proof remains mandatory and separately prepared.

Original native functional attempt1 was actually started through unchanged
runner/controller bytes, guest4f7beae5 and safe caller5814387c, with original
owned pipes and an1800s orchestration budget. Seven private caller checks,
Python3.12 AST/isolated Ruff E9,F and independent bound source review08629206
pass. Applying the repository's default style lint to these copied private
harnesses separately reports103 style diagnostics; that exit1 is retained,
and is not the shipped source8 strict gate or a claim of full harness style
compliance. Expected protected recovery/launcher pins are checked against actual
held guest files before effects; source8 runner checker7af9 is unchanged.

The actual attempt exits1 after4.701s. Outer2862485/start409443214 and original
SSH2862486/start409443220 are normally reaped. Local safe stdout2637B SHA256
`cbaecddd1723fc8be51a8978d148e9be1d2c711d5b2d29144612af42d1e6b2a7`;
stderr558B SHA256
`338d9c620cf8f42696fb7d583a71c3e865fd9b0ee080f9c590911f9e8e3ccbff`.
The SSH drainer records actual guest stdout5336B SHA256
`72f86e31f7d52f2fc7f4feea55482bd7e794a55c8cd2e4f011df4e8ae032f620`
and stderr335B SHA256
`e52e512c6f576e1fa63bd86fa77f1839024006f9fd795bd91c40337364e2394a`,
then refuses the nonzero status before returning raw channels to the local
caller. Original guest finally persists its separate
/opt/hfcache-web006/native-original-functional-v1/RESULT.json; readonly result,
original generation/public workspace and actual role/closure diagnosis is next.
No native/browser acceptance or completed service drain is inferred solely from
the caller's reap. Do not replay, clean up or reset the failed attempt.

Readonly first-result getterd58a5d27 actually passes0 in0.416s,
outer2863659/start409473417 normally reaped; stdout5265B SHA256
`67ca2e6d4d4ed65f42c1b9e01f22127b94732d6b82b45cfdb41e0ea39802246e`.
Actual protected native RESULT6964B SHA256
`1adb26fcb66b5bef1243babe187e10ee717fc8f4f9702fcac9059931ba5fc480`.
Original runner87291/start10326844 exits1 after4.003s. Native generation
e6a85c3d105b485cb53ddac6dd28f5cf has no ready result or browser modes.
Separate readonly generation/unit collectorc136c3ba passes0 in0.612s,
outer2864219/start409486970 normally reaped; stdout10908B SHA256
`5881ab94e2ac2d598dd7e5bc833ff63ecab9b0ddef8eb0bafd9f8d19a014b390`.
Its original generation state11211B SHA256
`a949f87eeca9263f3adb939ba2ac03a6f4441079bca0dca37f70891aee2333f6`
records started/stopped true, paused false, zero ready/cgroups/containers,
and all ten tracked original PID/start pairs numerically absent. Original
public RESULT1750B SHA256
`74ac11afccaf6d093c516e683c7204d4c1cbae46f00f49d8aca917313595ce5c`
retains cleanup_unknown true despite recorded stop evidence. Actual system
helper is failed/exit-code20, MainPID0/empty cgroup, invocation
ec38437451b74b07b2bc01d2db7b074d; all other five queried native roles/sockets and
three user roles are inactive. Preserve that failure and original uncertainty.

Readonly exact-invocation journal/AVC collector f8ef78e5 actually passes0
in0.529s, outer2865826/start409527459 normally reaped; stdout10193B SHA256
`f23c64777f302224798f56cad54978a248915837f3390cbf0b6e926e28a3fade`.
Journal identifies historical helper PID87375, now numerically absent; its
original start ticks were not captured and remain UNKNOWN_UNRECORDED.
Actual enforcing AVC30064 at1792625890687000microseconds denies lnk_file
getattr to inode18601131, target
unconfined_u:object_r:systemd_unit_file_t:s0, from exact helper domain.
The API parent remains empty, root:983/mode0750, with the required custom runtime
type and no socket/binding/unknown entries. Earlier ioctl/cert-directory AVCs
are separate observations; none justifies a grant without causal proof.
Subsequent readonly nine-binding metadata readback actually passes0 in0.420s,
outer2866974/start409557274 reaped. Stdout9886B SHA256
`e958c17afdf4fd5da785417d70dd6e04a9ff68f829d26ed3fa72bb8d44cf34aa`
joins inode18601131 uniquely to `/etc/systemd/system/hfcache.target`, raw target
`/opt/hfcache/current/packaging/systemd/hfcache.target`. All nine fixed bindings
are held/rejoined with complete metadata/context; target bodies are not read by
this metadata collector. This resolves the causal join without another role start.
No helper reset/restart or cleanup follows these readonly observations.
Documentation alignment passes206human documents/27helpers and whitespace passes
after these evidence updates; source8 runtime inputs remain unchanged.

Source9 frozen2026-10-22T00:00UTC:1359files, parent07d10e0, snapshot
`8fb2e713005e8d56877f6cce4cd79c4449b91faf58e0c4740f3049b5d2f98eab`,
inventory SHA256
`18882cb1e94edc9b7b988f3ccb6e3cc5c64097bfd3360792b513d99a0b20d1f8`.
Exactly eight captured files differ from source8: the CIL, its new regression
test and six contract documents; all runtime Python and web inputs are equal.
Contract-first ADR150/invariant020/human deployment/troubleshooting amendments
explain the type-wide lnk_file getattr/read scope and separate target mediation.
CIL24 SHA256
`32337b5b73984856c90c8e8c488c75295cca9a9395552c65cb1c289d67d6c691`
adds exactly that pair, with no other policy delta. The regression fails before
the fix; focused policy/authority/startup tests then pass299, zero skips,12.84s,
and independent35policy tests pass. Documentation alignment206/27 passes.
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
2026-10-22T00:00:08.482472Z as original2867773/start409575032; its outcome is
pending. Source9 artifacts and finite preserving fixture refresh are in progress.
The guest still has policy23; no source9 installed acceptance is claimed. Preserve
the existing key inode, complete old releases, selector, original authority4
failure/recovery/control/projection and native failed generation. Oldcontrol6
must be audited before changing its bound sources/CIL/receipt; no stop/provision
replay follows. Gate/artifact/fixture/profile/proof results remain distinct.

Fresh source9 artifacts actually pass: isolated captured-copy wheel and two UI
builds return0, all108package leaves and both six-file UI trees match; source1359
and prior source8 artifacts stay unchanged. Summary SHA256
`d26dc2c411dc2ddd3fb810a9d4bc55ca0a1836042f662cafd982a7661c1e3ad5`,
wheel5a52465b and UI manifest3df4287d retain identical prior bytes without
relabelling prior build receipts. Actual image12 wrapper fails before context/
Podman build because system Python3.12 cannot import the Python3.14 builder;
retain its reserved locator and failed receipt. Fresh image13 uses the pinned
project interpreter and actually returns0, outer2877716/start409640305 reaped,
17.407s overall/13.196s Podman build. Receipt SHA256
`e862d51ab69909b9c49657557d27b8578b85885eeb17b9cc5f701fd8857e1844`
binds source9 and pinned UBI10micro87a27d71. Immutable image remains
`e3d2085fc1080bcf988a39487041de910ecce2e2e7411845246cfed916904ff3`;
existing source8 guest runtime audit remains historical, pending explicit join.

Protected source9 transfer actually returns0 in0.950s, original2879073/
start409645258 reaped; stdout6086B SHA256
`dda7817738e4b928a11d25610cda2a6bc2a5d153765b475d15cc5cb786d1aad2`.
The complete archive/index/capture are exclusively staged in owned guest
`/opt/hfcache-web006/native-source9-transfer-v1`. All1359archive hashes/modes,
old stopped native generation and retained source8 evidence are checked.
`native-source9` remains absent and public source/selector/authority unchanged.
Independent transfer fault/drain tests pass10, zero skips,3.00s. Policy24 refresh
is source-only/inert until actual old-control audit and preservation receipts
are bound; its17source fault tests pass1.34s and independent review passes17.
No policy24 installation, fresh controller readiness or installed profile
acceptance follows from these local/build/transfer results. Current concise
checkpoint `.scratch/web-006-source9-current-state-v1.json`, SHA256
`5d0fde45e629a419c689477a4e98bd8b7dfb54513ddb74aed2d022dc07dd5291`.

Source9 strict gate actually completes0 at2026-10-22T00:21:04.706191UTC,
1256.224s, original2867773/start409575032 normally reaped/proc absent:
7730Python passes/52opt-in deselections,572historical frontend,2786web-unit and2846component
passes, builds, three locked wheel installation profiles, two startup Chromium
checks and real HTTP/API React read fixture. All1359captured hashes/modes remain
unchanged. Result814B SHA256
`717627154f41c8316852772bb0bbc619c0c4e732734edbfb5dfeac66b9cb0bec`;
log100807B SHA256
`011400cd34022ede9a013a81843a52a13e6dcd272c5168ee9183d484c1416365`.
This is strict source acceptance, not installed Caddy/helper/profile acceptance.

Independent oldcontrol6 audit actually passes0 in3.172s, outer2881969/
start409669037 normally reaped. Actual held/readback protected result9998B
`/opt/hfcache-web006/source8-pre-refresh-audit-v1/RESULT.json`, SHA256
`2d18a125333b082c08a58cd39d7e54264dc0a13ab2bd355005a0ab6c394eeb32`.
It verifies the original stopped generation/evidence,1359source8 inputs,
108same-inode readonly package leaves, unchanged original key78157344 metadata
only, selector60236146/raw releases/0.2.2, exact active native proposals,
13quiescent roles and six refused endpoints. Four child commands return0/reaped;
no stop, key-body read, state reset or authority replay occurs.

Artifact9 transfer subsequently passes0 in1.393s, outer2882546/start409678065
reaped, stdout15488B SHA256
`595388dd6d841db307e0f0bd0f3bdf8182637da7fc008710b209f94992ebbfd3`.
Fresh protected/public artifact9 paths contain measured108wheel/sixUI leaves,
inventory and image13 build evidence; no image/role is loaded or started.
Public source update then passes0 in1.203s, outer2890327/start409706662 reaped,
stdout9976B SHA256
`39b1314bab1b2a1981a647aa23bcb40885e6ad49141b6fa49178071fe8a24480`.
All1359source9 hashes/modes verify; eight source8 before-leaves and modes remain
in the new versioned backup. Original control6 is never called after the update.
Independent updater20fault/drain checks pass, zero skips,1.98s. Old source8
control/release/projection/failure receipts remain historical. Policy24 and
fresh installed native/rootless acceptance are still pending.

Preservation actually passes0 in31.636s, outer2893153/start409767758 reaped.
Actual held/readback protected result9720B, SHA256
`5262babfe97a57fb625c9cf41236edf11278fea621a71c3eafddb80149ac4d03`,
at owned guest `source9-stage-preservation-v1/RESULT.json`. All1359source9 files
are captured into `native-source9`. Both complete source8 release trees move
by NOREPLACE to new protected evidence, together with the selector and active
native proposal inodes. Key78157344 and original108-file readonly projection
remain unchanged; six commands return0/reaped. Original failed generations,
control/manifest, key and old source/staging evidence remain retained. No app,
installer, policy or label action occurs in this preservation step.

Separate original native installer actually passes0, outer2896200/
start409801756 reaped,29.753s. Its protected result6481B SHA256
`6a60a605ebddfa10449aa52f26f0e3f3b95bac065ae667e5c969630145826d7a`
is actually held/read back. Original installer87920/start10685978 returns0 and
all108installed package leaves match source9; the host wheel is a reference,
not its input. Five command children return0/reaped. Review identified original
restorecon's prefix scope before execution: historical selector60236146 is first
NOREPLACE-moved to protected `native-restage-source9-v1/source8-selector`,
retaining raw target/context and recording its own ctime change. Old release
trees and readonly projection stay unchanged. Current/active proposals and
rootless stage paths remain absent. Policy23 stays installed; no app starts.

Current-image audit v1 actually fails1 before acceptance: its sole original
image-inspect child returns0/reaped but the predicate requires an old aggregate
Size value. Closed readonly getters preserve/read the original failed result
d07fd024 and its private first stdout. Exact immutable ID, six layer diffIDs,
runtime User981:981 and UBI10micro base prefix all match; current aggregate Size
is205256971 versus old guest204759819. Podman's storage aggregate is a distinct
observation from OCI identity; no cause for that difference is asserted. Fresh
readonly audit v2 retains the failed v1 and both size values, preserves strict
ID/layer/user/base checks and bounded positive-integer Size validation, then
actually passes0 in0.817s, outer2897279/start409817191 reaped. Two inspect children
return0/reaped; all held input and original pause identities rejoin. Localstdout
9462B SHA256
`455421d8da75048c554e6c7504fe7451a5d3fb4d23aaddc6a48b109c280114c5`.
Expected protected RESULT6839B SHA256
`0592afe6985e4ff75a4de7204c4e56e18caba3463a1dcb2ff4acd9db569523a8`
is reconstructed from that actual emitted inner result and requires the next
held-FD check before use; no prior independent guest readback is claimed.
No image export/load, container or application action occurs. Required installed
role/credential/peer/inode/attachment/browser/fault/drain acceptance stays open.
Current concise checkpoint `.scratch/web-006-source9-current-state-v3.json`,
SHA256 `2526da521d173f9f751e1181ed0bc0c13742b744704d5ee978b0bb657524a89e`.

Original rootless9 input publication/staging actually passes0 in3.087s,
outer2898922/start409859756 reaped. Local stdout10124B SHA256
`7edb918129b948cae8e1a90217b97234d89047862d09a1c4a2c4a13055e98b83`;
actual held wrapper RESULT9212B SHA256
`a8a57df7c313f3a66d39f531d5ba9ea4cc94481e31f7ca7fffae2a07c0a6a2a6`.
The four exact renderer inputs are exclusively published under protected
`rootless-stage-inputs-v9`. Actual held receipts under
`rootless-stage-source9-v1` are staged.json4709B SHA256
`29dbd35f1c288c2c1525e480ef16f653fb1e3899f34d320fc0beacb239a17346`,
input-provenance.json11339B SHA256
`7ce9b8f7b1aef6c9390ae5156befc6e2bb7f96f21cca0d998b7c04b900b19829`
and refresh-closure.json5156B SHA256
`ca8f0853d5e19f880bb07e28edaa273914a2230b43a8cba34f3518f457e835ff`.
Staged.json is written inside the refresh context and does not claim its final
closure; the separate closure receipt records successful post-rejoin completion.
The previous image audit0592 is now actually held/hash-verified before use.
All13 original stopped-role fields, six endpoint refusals and original key78157344
metadata/context rejoin; no key body/digest, image load or app starts occur.
This establishes staging, not installed feature acceptance. Policy24 installation,
fresh authority and original functional/negative/browser/fault/drain proof remain
required. Independent rootless operational source checks14+11 pass, zero skips.

Policy24 canonical refresh actually passes0 in12.233s, outer2900116/
start409893585 reaped. Local stdout57883B SHA256
`09522f6d2503df91fd0bea65d1e2c912329bea382ededee9a4dca25d6f20d88c`.
Actual held protected RESULT41527B SHA256
`efd47099d740574240d0130044ce3249014d51baa7edf7e2782a3a901b79cec4`
and safe collection54821B SHA256
`5d74ef613f58ec4df47206db7db123de33aba6bd0373f323ebdba214406d7cc2`
record successful completion after all held inputs close. Seven known positive
PID/start pairs return0/reaped. Loaded CIL checksum is32337b5b; actual kernel
SHA256 `babb26bc72fabc4a970b9911a8ad153b46a051bbb28abae6063d64ef06fbd1b4`.
New12-role receipt1015B SHA256
`47f1d6259c9655572130b2c3b411440c57e52fff73af4d71afcb368d211c8af1`
has inode72117890; old receipt78157343 and old CIL inode/hash/context remain
preserved under same-parent policy23 backup names. Six unchanged canonical
files and original key78157344 metadata rejoin. No label-rule, selector, service
or credential action occurs. Independent91helper/24caller tests pass, zero skips;
independent actual-result/body/hash/inode/command closure audit passes. This is
policy installation proof, not actual installed feature acceptance.

Stock983 secret baseline actually passes0 in1.049s, outer2900274/
start409898059 reaped. Local stdout12346B SHA256
`5c8b028c6faf826ca1444cfc83581ce161e9a873faffbe4c564dcae65df455c1`.
The normal fixed-store secret listing is empty; all13 roles remain quiescent
and pause70549/start6647855 stays unchanged. The existing empty983-owned secret
directory inode3765270 gains only engine-created zero-byte secrets.lock
inode3765248; directory size/times change honestly, without an immutability claim.
No secret payload/body/digest is read, no secret is created/removed/replaced and
no ownership or retirement authority is inferred. Five command children return0
and are reaped. First rootless generation is still unstarted; later generations
require explicit exact-ID lifecycle proof rather than blind name removal.
Concise current checkpoint `.scratch/web-006-source9-current-state-v4.json`,
SHA256 `12c382382a06999b7900cda26a16aef276b07431e80fd23a2780fc4e9f7a99ba`,
retains all preceding failed records. A fresh local recheck finds no drift in
any of the1359 source9 file hashes or modes; human documentation alignment
passes206documents/27helpers and whitespace checks pass.

Fresh authority5 donor transfer actually passes0 in0.486s, outer2902456/
start409958454 reaped. Actual held protected donor RESULT1645B SHA256
`8f9f980266cfc702ee16bd9a43ecdefcc9523c71ccbc2973ccf03fd9d177f1df`;
local stdout4677B SHA256
`052696b35feead0e741095b67e52097d845be493045aac1e434479377523bb87`.
Only the reviewed authority source3ec2f169, controller7d43a644 and inputs44c6d911
are exclusively published0600 under protected root. Actual policy24/rootless
closure inputs rejoin before success publication. No authority execution,
service, selector, policy or label action occurs. Eleven adversarial archive/
held-inode/transport checks and two independent11-test runs pass, zero skips.
Fresh installed authority validation and functional acceptance remain pending.

AUTH-08/HOST-01–03 now map actual source unit/integration tests to gate9's
retained log/source identity in acceptance-evidence.json. Every case remains
pending, with no functional execution asserted. The real Unix exchange fixtures
and API route integration are explicitly distinguished from synthetic inspection
facts and unperformed installed native/rootless isolation. Focused plan/docs
checks47pass in6.17s, zero skips; human navigation206documents/27helpers passes.

Fresh source9 authority5 preparation actually passes0 in8.156s,
outer2903391/start409981326 reaped. Local stdout45171B SHA256
`5d454924a9b5480bcb956360d75f3b17134ec9c55676cb635851aac487bc2673`.
Actual held protected authority RESULT34250B SHA256
`d39e751fe411001e104b70b16dc6ddc5e266ae93244623ee61591ea8f4da7cd0`
and safe collection42067B SHA256
`58656df40ecb433e7f0b0540e65332c8c379e3687828fe47f1b03582741d76b6`
pass post-rejoin completion. Original installed validator88391/start10865495
returns0/reaped and reports the expected new readonly108-leaf package projection.
All29 command children are reaped. Exact controller7 equality, current restored
absent, original key, fixed bindings, old source8 authority/projection and fresh
SELinux receipt checks pass; no roles start and no key/receipt is reprovisioned.
Control7 SHA256
`dcdf47d63790d36162aac96a4503af2a505d5523a72fd6419f70018a5982209e`;
manifest5 SHA256
`0a595e1a401780cc3dc0903b83fb59e9e196490307ce9084a481b8f43c8b8be5`;
runner launcher SHA256
`e58182e5abf2cad6e0b413bb7699ec9907b37572acce46d239f6bb08400dab9a`.
Independent41authority/10safe-caller tests pass with no skips. The373 prior
process pairs are a bounded known diagnostic inventory; separately held original
receipts retain all other already-reaped query children. This is installed
metadata readiness only; original native/rootless functional and dedicated
negative isolation acceptance remain required.

Original native9 functional v2 actually fails1 in4.230s, outer2904477/
start410000633 reaped. Actual local stdout12680B SHA256
`1f46125acd2224c359c32d997d3d407b033e081f22550b1d3ac249d7f64e7b76`;
actual held private native RESULT8609B SHA256
`18fc3300866e0649fdad23eabc7460d71483cdc8c0f7d2fbf70dad259c744067`
and safe collection13398B SHA256
`1899ec8076d3f34a12c84496600ef13c0b6b7eebb474be0475cd7f3d0206776b`
retain the failure honestly. Original unchanged runner88452/start10884253
returns1/reaped in3.372s, before READY or summary. Its original stderr62B,
SHA256 `286fbc7a3c97c12aa102bf7b056769477b52344ed0a8c6be827511572b4eb350`,
remains private in command-03-stderr. Three pre-run queries and one post-run
system query return0/reaped; strict post-run inactivity then refuses. The
wrapper marks functional_passed=false and all_guest_inputs_rejoined_and_closed
false. No actual executor closure or installed acceptance is inferred from
wrapper/runner exit. Read-only invocation/generation/journal/audit diagnosis
must establish the next action; no reset, replay or new profile start occurs.

Read-only native9 failure getter v2 actually passes0 in0.781s,
outer2906156/start410046176 reaped. Local stdout23914B SHA256
`8e0fc67efcbc66ff93feafb8fa8c134fe0683f84e42acf908bc9b4af14a96b2a`.
New generation e3f5bf9813b443e5a2bf8f6af28809ec has started=false/stopped=true,
paused=false/ready0/cgroup0/container0; seven recorded PID/start pairs are
actually numerically absent. Exact state2698B SHA256
`b170031837f79b035ff5f8e0e2af9c9dbd9e09e1fe880634136df680ee2ff534`.
All eight other queried role/socket rows are inactive. Helper has MainPID0,
ControlPID0 and empty cgroup, with exactly the OLD ec384 invocation, ExecMainPID
87375 and original23:38 startup/exit timestamps. Returned AVC rows belong only
to that historical PID/invocation window. No fresh helper attempt or new CIL
failure is established. Original controller saves started=true before starting
the helper and never resets it; its preserved false value places this refusal
before helper start. The originals-before-helper private secret-label gate
requires strict inactive, whereas activate and the outer wrapper admit the
recorded prior failed helper. Confirm its exact gate record before the narrow
private-controller correction. Public cleanup_unknown and the failed run remain
unchanged; no whole-feature acceptance is promoted. Original control/result and
kernel rejoin; eight focused and eight independent getter checks pass, zero skips.

Exact prehelper gate-state readback actually passes0 in0.629s,
outer2907774/start410088997 reaped. Local stdout7344B SHA256
`b59b4df9c245451593e9bcf06f553a3a2d0c9654e3310ad897e76ff17416a12a`.
The sole originals-before-helper gate is refused/ValueError with zero objects,
kernel-beforebabb26bc and actual_inode_denial_proven=false. Started remains false;
fresh full10-property helper state exactly matches the old ec384 failure.
Control7, controller7, failed result, generation and kernel rejoin. This confirms
the private harness's strict-inactive prehelper refusal, rather than a fresh
helper/CIL failure. Reconstructed protected gate RESULT5834B SHA256
`c8201b8dbe4cae9cc404118155764f85e8b16b7ebc47ea7018a143077633afa4`
still requires actual held-file verification before a dependent effect. Eight
focused and eight independent checks pass. Earlier unexecuted caller v1's copied
schema-key mismatch remains retained; corrected v2 has a real classifier/schema
regression and alone was executed. Fresh private controller8's narrow exact-old-
failed-state prehelper admission passes79focused/independent checks; all other
phases and product source/CIL remain unchanged. Fresh authority6 and original
native/rootless functional runs are still pending. Native v3 inert caller42 and
rootless/ownership-observer successors124 local checks pass with no required
skips; these establish no installed feature acceptance. Current concise
checkpoint `.scratch/web-006-source9-current-state-v6.json`, SHA256
`89b0748623f9ab8a16b9367bf1210d5fd53775c688a5a6cf447453da61344bb7`.

In-progress source evidence2026-10-21: combined host/authentication/helper/docs
suite913passed, zero skips,140.03s, command `uv run --locked --extra server
--extra mcp pytest -q tests/unit/test_host*.py tests/unit/test_web_basic*.py
tests/unit/test_script_help.py tests/unit/test_docs_alignment.py
tests/unit/test_docs_config_contract.py tests/unit/test_docs_migration.py
--junitxml=.scratch/web-006-host-auth-docs-combined-v1.xml`.
This preceded later guarded-observer/wire changes and is historical focused
evidence, not the final gate or installed acceptance. Documentation checker
subsequently passed205human documents/26helpers. New functional helper will
require synchronized inventory and its own checks.

Owned guest prerequisite inventory confirmed no external/NFS/CIFS/shared mounts,
fixed native/rootless paths initially absent and Enforcing. New test account
`hfcache` UID/GID983/home `/var/lib/hfcache`, nonoverlapping sub-IDs and empty
protected `/opt/hfcache`, `/etc/hfcache` were created under the existing owned
guest/boot marker; no application services started. Exact intent/results:
`.scratch/web-006-account-prerequisites-v2.{py,json}`. V1 had a syntax error
before execution/effects; it remains retained. Donor survey V1 exceeded its
enumeration cap without effects; bounded V2 succeeded and is retained separately.
These setup facts establish no native/rootless/profile/UI acceptance.

Review corrections underway: charge observer bootstrap reads/time to the common
budget; execute native peer observer as root without namespace dereference or
SYS_PTRACE; read held-guard evidence through the original predicate in a fixed
mixed-credential child, preserving700lock directories and no new capabilities;
require configuration permission for private config-base reads. All required
actual manager/peer/namespace/SELinux/Caddy/browser/drain proof remains pending.

Record exact source/files, material decisions, additional test cases and any blocker with an unblock condition here. Do not change a dependency's completed evidence. Split oversized work into new work packages rather than silently making several implementation commits for this ID. No production effects, force resets, remote pushes or historical authorization reuse.

Owned continuation2026-10-21: fresh authority6/controller8 donor transfer
actually passes0 in0.546s; original outer PID2914712/start410227174 and SSH
PID2914714/start410227181 are normally reaped. Three exact root0600 donors
read back with hashes23a187e2(source),2a9075d5(controller),4206c1a2(inputs).
Protected donor receipt `/opt/hfcache-web006/fresh-authority6-donors-v1/RESULT.json`
has SHA256 `6eeca0ba2141f3059193462ed3a9cbb5548bd0836e09b7b641082067abeae6cb`.
Local original execution record `.scratch/web-006-authority6-donor-v1-execution.json`
retains both channels. Eleven owner and eleven independent donor checks pass.
This transfers metadata/code only; authority6 and all new functional runs remain
unexecuted at this checkpoint. The first logger invocation refused its malformed
local filename argument before creating a child or any output paths.

Human-guide review found its old account-switch sentence omitted the native
held-guard child. The first correction incorrectly described initial helper
effective capabilities as empty. Source inspection of `scripts/host-helper.py`
and independent review caught that error; source11 now documents only
SETUID/SETGID permitted/effective and cleared inheritable/ambient sets. The
running source10 gate must finish with its source-change refusal retained;
source11 needs a fresh strict gate. Source11 has1359files, snapshot
`44fadfa076abd0cbf657babdd45275e2a95dec32160f3929dce1da83d70b9684`;
the only source9 delta is `docs/host-administration.md`, with no mode changes.
The installed guest and artifacts remain honestly source9; a separate checked
compatibility receipt is required rather than relabeling or reinstalling them.

The optional fixed-link AV-query v1 actually failed1 before returning decisions.
Its source expected the protected source9 inventory0644, while the original
transfer receipt records0600. No kernel-policy denial is established. The failed
query and channels remain retained; a safe read-only diagnostic is being
reviewed before any corrected successor. It grants no feature acceptance.

That safe diagnostic actually completes0 in0.660s, retaining the query refusal
as data: `TypeError` at `captured_json`'s `with parent_fd(path)` before reading
the inventory. The generator `parent_fd` lacks its context-manager decorator;
the0644/0600 mismatch is a second source issue, not the observed first refusal.
Actual fixed inventory metadata confirms root0600. No command or AV decision
ran. Outer PID2917572/start410246801 is normally reaped; original local
diagnostic stdout SHA256
`2ba27f1741526c64447416472dadb88a42c82727a2c2c67696d81866af020de0`.
Raw522-byte stderr stays in the protected guest diagnostic directory. A fresh
successor must correct both setup issues and test the real parent context;
none of these probe failures establishes a product-policy defect.

The next two optional-query attempts retain additional setup refusals: v2's
relative-interpreter grammar incorrectly included `python/`, despite the
proposer storing a path relative to `PREFIX/python`; v3 incorrectly treated
all nine unit bindings as links, while the existing installed metadata records
one target link and eight regular units. Both refused before any AV query.
Their original safe diagnostic outputs remain retained, SHA2568a6fedc5(v2)
andca391a74(v3). These are failed test-tool assumptions, not product failures.
The final narrowed v4 actually passes0 in0.941s, outer PID2925066/start410307024
normally reaped. Its six held current/system-target/interpreter links all
return active-kernel `lnk_file getattr/read` allowed, flags0/sequence44 and
unchanged kernel24. Eight other unit paths are explicitly unqueried; no current
inode/type/hash claim is made for them. Local original stdout SHA256
`6459edc9dc719217ded4b7efefaac70a54b21ec5ba4ecf1ad6e5dc51847313b1`;
independent actual-result reviewc31bcc34 passes. No CIL change or installed
feature acceptance follows from these permission queries.

Fresh authority6's sole actual invocation fails1 after5.066s, before publishing
WORK/RESULT. Safe collection records `AttributeError`, resultnull and all donor
captures rejoined/closed; seven known-start read-command children exit0 and are
reaped. Outer PID2925129/start410308304 is also reaped. Original local stdout
SHA256 `487664cb34057747a3aff48fe60afa89c2ccdc79d8fbe82e22c0d354a32db922`;
protected safe collection SHA256
`890ebedb5912eed45eb2fa0599977b6f5eb291e699483c97fe955e73efb79cf6`.
The1163-byte raw stderr remains private. Independent exact-utility inspection
finds only one absent referenced attribute: `u.gone` at source line879; the
actual captured utility exports `process_identity` instead. A read-only closed
traceback check and corrected fresh authority remain required. Do not replay
authority6, promote readiness, or start native/rootless acceptance from this
failure. Existing key, selection, authority and failure evidence remain owned
prerequisites for the successor.

Source10's strict checks actually exit0 after1247.760s; the owning gate wrapper
exits1 because the operator-guide correction changed its captured source.
Original PID2912191/start410214538 is normally reaped and absent. Preserve
`.scratch/web-006-gate10-result.json` and log SHA256
`c41db5a749de731f0e965e9f27ee63d0b8daa4ffdc94ec3c37dbbfb4246a1f2b`;
this is a refused source gate, not final acceptance. Fresh source11 strict gate
starts2026-10-22T02:07:41.057352Z, original PID2933115/start410340290,
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
snapshot44fadfa0. Its result remains pending.

The closed authority6 readback actually passes0 in0.498s, original
PID2936863/start410359065 reaped. It confirms the missing `gone` frame at879,
no unknown traceback frames, and all six old WORK/preservation/control8/
generation8/public6/sudoers6 destinations absent. Local stdout SHA256
`3b1dd7e95dd8cf33bb23b4e0e9ca6b479c9023ac0a0992d852ca53eabe40dffe`.
Fresh authority7 uses a local absent-or-changed-start predicate through the
actual utility's `process_identity`, with real live/exited-PID and exact utility
interface/signature regressions. Frozen authority6 is not replayed.

Authority7's one-file source donor transfer actually passes0 in0.512s, original
PID2939904/start410386526 reaped. It holds the original input6/controller6
donor/failed6 receipt and transfers only sourcec9155188 to a fresh protected
directory; donor RESULT SHA256
`a462fd76821b7a23fde035896e975e1fa6b3da70ddaf49af4430d78c1e3b58cc`.
The sole authority7 invocation then passes0 in9.426s, original
PID2940109/start410387858 reaped. Actual held protected RESULT SHA256
`19b2ef309c08fac24196d28a8e619053bf197adb09ed74de2b2a2065e7faaa43`,
99751 bytes; safe collection706f8e5d/89850 bytes. Original installed manifest
validator PID89084/start11272106 exits0 and all29 command children are reaped.
The original key and both old readonly package projections remain unchanged.
Three fixed old selection leaves are retained as exact same-inode backups in
`/opt/hfcache-web006/authority5-before-authority7-v1`, with only their recorded
own rename/ctime transitions; current and active paths end absent. New control8
SHA256d9a71cc7, manifest7d0a46ba1, controller8 body2a9075d5 and runner0405ba18
are independently joined to the actual result. No application roles start
during authority readiness, and readiness alone is not feature acceptance.

The new original native functional v4 is bound only to those actual readiness
hashes and actually fails1 after6.860s before READY. Original runner
PID89144/start11284740 exits1 and is reaped; outer PID2941929/start410401121
is also reaped. Protected native RESULT SHA256
`92a9aa1fdd042c6d0bf34982307fb55954469978722838f9f3546348741a5ab5`,
8629 bytes; safe collection6f5dc6c4/13422 bytes. All five wrapper commands are
reaped, with statuses0/0/0/1/0. Strict post-run quiescence refuses and captured
guest-input closure remains false. Original raw channels stay private. Actual
generation/helper diagnosis is pending; do not infer another prehelper failure
or a new CIL defect yet, and do not replay nativev4. Rootless, separate negative
and supplemental protected-input/binding fault acceptance remain pending.
Concise current checkpoint `.scratch/web-006-source9-current-state-v8.json`,
SHA256 `a1577c32d38de54a3241fd5e5edc6ad1278999757c7967787cb31a8f09b2c467`.

Source11 strict gate actually passes0 in1237.241s with all1359 hashes/modes
unchanged. Original PID2933115/start410340290 is normally reaped and absent.
Result SHA256 `487c861ee89fac6347f1566a6da9900382611481a64a59461c029849448ef477`;
log SHA256 `42cc10fc65606eb442335890a425b1279853adacf81788616f85e969502055c4`.
Actual checks:7730 Python passes/52 opt-in deselections,572 historical frontend,
2786 strict web unit and2846 component passes, required builds, two Chromium
startup cases and real HTTP/API React read fixture. This is the corrected
source gate, not installed native/rootless acceptance.

Nativev4 read-only failure diagnosis actually passes0 in1.409s, original
PID2951246/start410448009 reaped, with unchanged kernel24 and original failed
result rejoined. Original stdout SHA256
`0e10b93b0997071b17345df12ca010c010b7f57343c61dcaea22928205e5da50`.
Generation `d211fea9015b434baa366c1d3acd433f` has started=true/stopped=true;
all eleven tracked PID/start pairs are numerically absent, with no READY,
cgroups or containers recorded. Protected state SHA256
`03038fc95df4b86f262dc2762be328d4632e2fb68fa9163aff9c37417f004847`.
The original source-secret gate passes all eight objects: read/open denied,
flags0/sequence44 and kernel before/after unchanged. The controller admits the
exact prior failed invocation as intended. A genuinely new helper invocation
`9f2f603b9598466f8d0859d68d02b400`, historical PID89229, then exits20 before
READY. Its exact historical start ticks remain unknown. All other queried
system/user application units are inactive; helper has MainPID/ControlPID0
and empty cgroup but retains failed state. Public cleanup_unknown remains true.
Audit31267–31276 includes ioctl and cert_t directory-search denials in that
invocation's window; occurrence alone does not identify the fatal prerequisite.
Do not add permissions from these rows. A fresh private diagnostic will execute
the original pre-bind startup prefix under exact canonical confinement and
emit only closed exception-frame facts, stopping before listener creation.
Current checkpointv9 SHA256
`a0fc6b103a8059b0a05ef68ce2c1e710f7bca1367f3e9ba50bbfe31a40a7274e`.

The bounded runtime-parent metadata getter actually passes0 in0.492s, original
PID2956777/start410559343 reaped and absent; its one SSH child is also reaped.
All local captures rejoin and close, and kernel24 remains unchanged.
Stdout SHA256 `005d0ba6e2d3ab3e9948bf6ad9cc7518a3ff0a16fa697d3d965905f56da5af61`.
The API parent inode10829 is root:983,0750, runtime_t and empty; helper.sock and
binding.json are absent. Outer runtime inode10828 is root:root,0755,runtime_t;
its bounded name enumeration overflows17, so no exact entry count is claimed.
No file bodies, unknown leaf names or leaves are opened/published, and no
source/service/policy changes occur. These metadata facts do not prove a fatal
startup cause or feature acceptance. The private startup-prefix worker and
coordinator independently pass79 focused checks with0 skips in2.36s; their
guest diagnostic has not run yet. Frozen worker b34982ca/12828 bytes and
coordinator ec221ace/47041 bytes preserve the canonical unit's hardening and
stop before HostDaemon/listener/binding/notify. Concise checkpointv10 SHA256
`7a6d317b0edbe6cccfd7b2204314d860d0eee38a48a196a3774d4d949a3e19e1`.

The fixed diagnostic-binding snapshot actually passes0 in0.590s, original
PID2959401/start410626995 reaped and absent. Both guest systemctl-show children
89408/start11510576 and89409/start11510580 exit0 and are reaped. All local and
guest input captures rejoin and close; the original key inode78157344 and its
full metadata/context are unchanged, without reading or hashing its body.
Active selector inode59784425 targets releases/0.2.2; active deployment5b790ce9
and policy2dcefe04 equal the authority7 proposals. The exact failed helper9f2f
state remains unchanged. Result SHA256
`3fa931bb9bfe8454fcea06f2012a2b544271e206d4478dfc24f4994905fa9d9b`;
stdout SHA256 `8cd54df0e311d69e6b75df17744e3fde50cf8696a4bc520b4347288e52bacdfb`.
Frozen getter7dd3fef1 and local callere2440dcf have17 independent focused
passes/0 skips in1.23s. A mistaken review suggestion about proposal permissions
was withdrawn before execution: exact captured publisher signature/callsite
tests confirm deployment0644 and private policy0600. No guest mode changes
occurred.

The confined prefix diagnostic actually completes its collection0 in2.434s,
original PID2961274/start410679341 reaped and absent. Exact bound coordinator
ec85b399/48620 bytes changes only19 data assignments from the reviewed template;
all functions/classes and other AST remain unchanged. Final caller21a6423b
changes only REMOTE/PIN from the reviewed template; its12 independent checks
pass with0 skips. Protected coordinator RESULT SHA256
`f2a78dd4ba2a09054c0a05e68799c69ed5c506e9738f0233aba2fc87e02a9a26`;
local safe result SHA256
`0c447f0374028411862e62809539201178150cd6af183b02ebe524aa2bfd5f02`;
stdout SHA256 `24a879299801ab4fc0d22e5b27bddfa40f7fcaee750ab087968ae9480e35817a`.
All seven command children exit0 and are reaped, root guards rejoin and close,
and the original failed9f2 helper/unit, key, selector, configuration, kernel24
and old generation remain unchanged. The fresh diagnostic unit is inactive,
with no PID/control PID/cgroup. Worker89533/start11563001 is gone and proves
helper_t, root:root, P/E/B192, I/A0, NNP1 and24 seccomp filters. Loaded unit
properties equal the canonical confinement; Type=oneshot is the explicit
diagnostic lifecycle difference. No HostDaemon/listener/binding/notify runs.

The original prefix itself fails as diagnostic data at inspect-authority,
after domain/capability/module bootstrap passes. Closed causal frames reach
host_policy._show line831, which requires the fixed guard-status command's
exit status to be0. The original exception chain has no errno; neither a
certificate denial nor ioctl denial is proved causal. Inspection and bootstrap
verification remain false, with input/daemon captures closed and zero raw
output. A separate confined fixed-query diagnostic must measure that command's
actual return code and closed properties/stderr classification. In particular,
an absent guard may legitimately produce a nonzero query exit; that hypothesis
has not yet been measured under confinement. Do not change permissions from
the earlier audit rows or claim feature acceptance from this diagnostic.

The separate fixed root guard query actually passes its collection0 in0.671s,
original PID2962569/start410717640 reaped/absent. Query child89615/start11601223
returns0 with128 stdout bytes, complete seven not-found/inactive/dead/PID0
properties and empty UnitFileState/InvocationID; stderr is empty. All held
inputs close and both original/private unit states stay unchanged. Local
result SHA256 `87749084195306166e9ae1f52e1264a982a8dd2dc688fb8336fc05d4ba56141a`;
stdout SHA256 `fe5448116be2d654cd8042230d4aa107bebd4b8959a89a0f1f1e94f129bbfa36`.
Eight independent focused checks pass/0 skips in1.22s. Missing guard alone is
therefore not the cause here; keep the product parser's strict zero-exit check.

The fresh confined fixed-query diagnostic actually completes its collection0
in1.770s, original PID2963352/start410738393 reaped/absent. Bound coordinator
ce9d0cee/51705 bytes, worker6e1826a8/24483 and callerda327e06/16206 preserve
the prior diagnostic's guards while using fresh v2 donor/runtime/unit/work
paths;93 independent worker/coordinator checks pass/0 skips in2.38s and caller
has13 owned passes. Protected RESULT SHA256
`082ecd55f4d7661fcef23b3c84d7116eea68858ebc102608be449f1d67801d6b`;
local safe result SHA256
`3e7e1e5c25d9d5148bb38ccd2026f256329fd6c2439428a17f7746fd2f2aed64`;
stdout SHA256 `bef6501c74ddb1c9ea156062b4cc4afe0350ab0a722812540608396fc1038a34`.
All local/root/input guards close, the original9f2 helper remains unchanged,
and the private unit is inactive/dead with no PIDs/cgroup. Worker89720/start
11622050 proves helper_t/root0xc0 P/E/B, I/A0, NNP1 and24 seccomp filters.
Its exact fixed query child89722/start11622080 exits1, is reaped and original
start is gone. Stdout is empty; bounded stderr is40 bytes with SHA256
`2cf898fa8e33fc572c230d472f2e09011431a8d38632bf682b04632e807d71b3`.
Only closed access-denied/failed-to-get-properties classifications match.
No original inspection/server/listener runs in this query diagnostic, so its
inspection/verification/feature acceptance flags deliberately remain false.
An exact bounded USER_AVC/AVC attribution must establish the permission and
target before a new CIL grant; no parser, certificate or ioctl change follows.

The bounded audit-window readback actually passes0 in0.687s, original
PID2965245/start410794589 reaped/absent. Exact getter a0a93939/30806 bytes and
local caller925a4ed2/7725 are independently reviewed; all local/guest inputs
close and the original/private unit states, key, selector and kernel remain
unchanged. Local result SHA256
`c4e0e9e7ea9459771b00ca235f27c023a784c4d9a972bee123e10164ec45c192`;
stdout SHA256 `2b203ed13631e7bdf272805714f61b391163a16eb568acf2b72db95328355ddc`.
The actual runtime output timestamp1792638839602000000 anchors UTC seconds
1792638836–42; ausearch reads AVC,USER_AVC,USER_SELINUX_ERR without a PID filter
and returns0. Nine bounded records are retained. USER_AVC31558 at
1792638839595000 reports helper_t to init_t, class system, denied status, with
PID1 reporter and mac_selinux_filter marker. Numeric requester PID, exact
command line and guard path are not present/matched; those attribution limits
remain explicit. The other eight records concern worker ioctl/cert-directory
search and do not justify additional permissions. Pinned systemd257 source
corroborates Properties.GetAll/status and missing-unit-context fallback to
PID1/system; authorization is typewide status, not seven-property MAC scope.
A fresh confined probe of GUARD plus the four fixed service/timer units is
being prepared to measure all supported status targets before one minimal CIL
correction. No new grant, parser relaxation or functional acceptance exists yet.

Source11 unit/integration evidence was appended to AUTH08/HOST01–03 while all
four acceptance statuses remain pending. The plan/evidence validator passes
all9 tests with0 skips in0.28s; no installed functional result is promoted.
After runtime-metadata bookkeeping, all9 tests pass again in0.33s, and the
documentation alignment check passes206 human documents and27 helpers.

The supplemental installed-fault coordinator remains inert. Its source-only
v2 suite passes55 checks, but independent owned-filesystem fault cases expose
unproved restoration after partial writes or a parent-directory substitution.
Two explicit ancestor-substitution regressions are red against that preserved
draft. It has not been installed or executed in the guest. A fresh successor
must preserve unknown state, join the absolute ancestor chain and record exact
own partial transitions before supplemental functional acceptance can run.

The fresh five-fixed-unit confined query collection actually passes0 in1.776s,
original PID2966378/start410821701 reaped/absent. Worker89900/start11705353
retains helper_t/root P/E/B192, I/A0, NNP1 and24 seccomp filters. All five exact
GUARD/sync/verify service/timer queries exit1, are reaped and gone, with stdout0
and the same40-byte closed AccessDenied classification. Protected RESULT
SHA256 `875ffcc5ba7b6468890fa62bae9731f230b61b594721325a5602e4e7b88b7b25`;
local result285df086 and stdout60c1b51e remain retained. All captures close,
the original9f2 helper remains unchanged and the private unit is inactive.
The worker/coordinator checks pass109 tests/0 skips; no feature acceptance follows.

The second bounded audit collection actually passes0 in0.696s, original
PID2967177/start410845932 reaped/absent; all inputs close. Local result SHA256
`276de3c376c3b6d0bbdcf3b90d52a171567edfb71da2095fc296b2f4d60e8607`;
stdout5d8ce4c0. Within the exact runtime-output window1792639669–75,
USER_AVC31667 denies helper_t to init_t system:status;31668–31671 deny helper_t
to systemd_unit_file_t service:status. All report PID1/mac_selinux_filter;
no direct requester-PID/command/unit-path joins are claimed. The other eight
ioctl/certificate records remain incidental and justify no grant. Official
pinned systemd257 source corroborates GetAll/status, unit-file service-context
selection and PID1/system fallback; authorization is typewide status, while
the fixed argv/output filter supplies the bounded property surface.

Reviewed source12 applies exactly those two status allow forms. New CIL SHA256
`fa3ebc3a12db3a7b00dfe9440ae8dd722fad9e022f8ee4459dff204e9f467a27`;
removing the exact comment and two added forms yields old32337 bytes exactly.
Tests close the entire helper system/service rule set to those forms and
forbid control permissions. Human host guide, security contract and decision150
are synchronized. Focused host-policy/startup suite passes255 tests/0 skips in
13.16s; human-doc alignment206/27, Ruff and diff checks pass. Capture12 passes
with1359 files, snapshot51b5bfca8857b5ce86c2a25a65e3e7f4af01e9cc2f37a7e4b477f986444ede1f,
inventory136db991 and archive2e1e5fae. Capture SHA256
`7e01aa95eb50fb2f81b41760c075eb283f8e6ed87ffeb670b9ee53efc5115330`.
Strict gate12 is running against that snapshot; no pass is claimed yet.
The guest still has policy24/kernelbabb26bc; policy25 is not installed yet.

Application-only compatibility actually passes0 in0.783s, original
PID2976616/start410936341 reaped/absent. Receipt SHA256
`9573986ec4a3252cb62a7091249f0c59fad368942a8b0d76cb164e8d4f4ac575`
(.scratch/web-006-source9-to-source12-application-compatibility-v1-result.json).
Both captured1359-file trees/archives and live source12 hashes/modes rejoin;
exact five changed paths are the three host/security/ADR documents, CIL and
policy regression test. All108 wheel leaves, two46-input/six-output UI builds,
81 image wheels and fixed recipe/lock inputs are unchanged. Original artifact9
and pinned UBI10micro image13 retain source9 provenance. Explicit host deployment
compatibility=false and fresh stages/authority-required flags prevent treating
this as host-policy or functional acceptance.31 focused refusal/identity/archive/
exact-policy-delta tests pass/0 skips in2.05s; isolated E9/F lint passes. A broad
repository-style scratch lint attempt reports232 annotation/style findings;
these temporary harness scripts are not product source or strict-gate inputs.
Independent consumer/source review accepts the actual app-only receipt.

Fresh read-only oldcontrol8 audit actually passes0 in2.366s, original
PID2978146/start410949741 reaped/absent. Protected RESULT SHA256
`aa89dcb30968ef83ed1ba3b66c24140685ee56026b940c827d5e6840456d90ca`,
11576 bytes, at /opt/hfcache-web006/source9-pre-refresh-audit-v1/RESULT.json;
local result757591d6 and stdoutf3011ee1 remain retained. All four read-command
children exit0 and are reaped; all held inputs close. It verifies public source9
all1359 files/modes, exact old authority7/control8/manifest7, same-inode108-file
readonly projection, unchanged key metadata/selector/configs, exact9f2 failed
helper, other12 roles inactive, six endpoint refusals and all eleven tracked
original PID/start pairs gone. Historical helper start ticks remain UNKNOWN.
This runs before the public checkout update, so old load_control joins remain
valid. No stop, reset, authority replay, key-body read or functional claim follows.
Fresh source12 protected transfer/preservation/native/rootless stages, then
policy25 and fresh authority, remain required. The new public-update source-only
suite passes21 tests/0 skips in2.38s, including a real1359-file captured clone,
retained original bytes/modes, unrelated-leaf preservation and original-child
EOF/reap under repeated entry interruptions. It has not executed in the guest.

Source12 strict gate actually passes0 in1260.080s, finishing
2026-10-22T03:58:08.206985Z. Original outer PID2968414/start410876979 and owning
caller2968415/start410876997 are normally reaped and absent. The1359 captured
hashes/modes remain unchanged. Command is
`historical gate invocation (original command SHA-256 `b9d97947112e6e5c5005002b465c3dd68f8bd158ca8c41cb5966f57422999103`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`. Result SHA256
`a3451093e6f706ed0af620bf057d0e401f634c61aef7aa69e4fdb51b318e3e4e`;
log SHA256 `c584a5f423ce890cdef7f4d41ce1c563aa5984fbed0fb5951b004b6cfb977358`.
Checks include7731 Python passes/52 explicit opt-in deselections, three locked
wheel installation profiles,572 historical frontend compatibility,2786 web-unit and2846
component passes, strict wire/types/lint/build, two Chromium startup cases,
and the real HTTP/API React read fixture. Installed native/rootless Caddy/
credential/peer/fault/drain acceptance remains separate and pending.

Protected source12 transfer actually passes0 in1.729s, original outer
PID2986657/start410989098 reaped/absent. Owned SSH2986660/start410989111 exits0,
is reaped, and all local captures rejoin/close. Local result SHA256
`316233053a0ffea1f407ecf3edb8a4fc4b60c3e47d6ef44092c7e7f4becf93e4`;
actual5816-byte guest result stdout SHA256
`0835d2fab9f709d7bdbb1268a50fa99e19ec842de82251d0f5fe48cf338f4b43`.
That success body is written as native-source12-transfer-v1/RESULT.json and
will be independently held/hash-checked by the next preservation action.
Exactly source archive/index/capture are protected staged members. The separate
application compatibility receipt9573986e is exclusively published root0600,
3353 bytes, inode43279568; native-source12 and the public checkout remain
unchanged/absent as specified. No selector, authority, key, service or policy
action occurs. Transfer source-only suite passes23 tests/0 skips in4.92s;
actual caller6d4eac25 and guest0adcb502 are exact captured-byte executions.
An earlier stale output-flag test failure and pre-pin-update SHA handoff remain
preserved and were corrected before this sole actual invocation.

The source12 preservation/public-update bound tools pass13 focused tests in
2.81s, and the new public-update caller has9 checks in1.90s. Preservation binds
only the actual old-audit aa89 and transfer0835 assignments; all function,
import and embedded-helper ASTs are unchanged from the frozen template.
The public guest similarly changes only those two assignments, with every
function/class/import AST unchanged; its local caller binds that exact33406-byte
sourcec58291fe. Historical e3f5 state is correctly under generations-v7; the
unexecuted policy25-v1 draft used generations-v8. A preserved v2 successor
corrects only that STOP_SPECS path, with97 tests/0 skips in3.419s including
original controller7/controller8 generation-root producer checks. No policy25
installation has occurred yet; stage-dependent pins remain unbound.

Source12 preservation actually passes0 in28.521s, original outer
PID2989146/start411006297 reaped/absent. Protected RESULT SHA256
`4e3eeb5fc39ef35807c138471e4f0e643a2544e091fb38ed67e1c71c2c4feeca`,
10843 bytes, independently held/read after all preservation captures close;
local result4931dcfb/stdout7e130611 remain retained. Six guest queries all exit0
and are reaped. Exactly the old selector, two active profile files and native/
rootless release trees are retained by no-replace rename with their original
inodes/contexts and recorded ctime transitions. The old read-only projection
retains all108 backing inodes and original key inode78157344 stays unchanged.
Protected native-source12 is extracted from the held complete captured archive;
all1359 source hashes/modes match. Active selector/profile/release paths end
absent. Canonical helper files, kernel24 and historical failure receipts remain
unchanged. Existing authority and stop are never replayed.

Public source12 update actually passes0 in1.371s, original
PID2989447/start411011577 reaped/absent. Local original stdout SHA256
`b7099dabfd54650531a20d1d6c9347f1c45edf95d771666e694f869fe8699a6f`;
actual6950-byte success body computes protected RESULT SHA256
`5fed76cd3a1b18d3d2fbfcda64e494517b1b606df384b3af7d7e5bd298d71d3e`
(the next consumer must independently hold/read it before relying on it).
The original UID1000 update child90130/start11895152 exits0 and is reaped;
all local and guest original input captures close. Exactly five old changed
leaves are backed up with their original bytes/modes, no directories are
created, and all1359 resulting public source hashes/modes match source12.
The new public inventory is .scratch/provisioning/source-inputs-v12.json,
SHA256136db991. No old controller is called after this source update.

Fresh original native staging actually passes0 in29.619s, original
PID2990515/start411034015 reaped/absent. Protected RESULT SHA256
`375a6efe979537b0009f8dac18a931fc88e7d59b8b59a37424327d240a7bab1a`,
8117 bytes, independently held/read after stage closure. Local result SHA256
`13f79f828e1ff161fff1e633a49f58107e7ba50b23891dc886ab4a0c5831ada9`;
stdout02b199c9. The unchanged original installer90179/start11918170 exits0 and
is reaped, with108 package files matched. All five stage command children
exit0/reaped; all captured inputs close. Thirteen roles stay quiet, endpoints
refuse, active profiles/selector stay absent, and the old projection and key
are unchanged. Before original restorecon, historical selector inode59784425
is moved intact to native-restage-source12-v1/source9-selector outside its
scope, retaining usr_t context; this is a recorded second own rename, not
rollback or selection. Artifact9 keeps source9 provenance under the separate
application compatibility receipt. No helper, policy25 or application role
starts. Stage source-only checks pass97 tests/0 skips; caller has four owned
checks plus four independent checks. Rootless stage and policy25 remain pending.

Source12 unit/integration executions are appended for AUTH-08/HOST-01–03 and
the exact status-only CIL regression. All four statuses remain pending.
The evidence validator passes9 tests/0 skips in0.31s and diff check passes.
An initial bookkeeping command used a nonexistent test-file path and ran no
tests; corrected tests/unit/test_web_plan.py passes before evidence publication.

Original rootless source12 staging actually passes0 in3.422s, outer
PID2991374/start411055593 reaped/absent. All local captured inputs rejoin/close;
local result SHA256 `e35ae95ea0eda5e2141951fb9cf6c2b29dde1e508aa06a0030bc8aa7e9f3b45f`.
The protected wrapper RESULT9cbcb0c4/10789 bytes holds/readbacks all three
fresh receipts: staged SHA256
`e91944797f72d1a220355c4fe51795b0b2a0426dafd498984d7ce5011fd7a658`
(5282 bytes), provenance
`eea55b9baec05215695f2027f8e3bc357935701aec4b49291a2a72feafa40a34`
(11964 bytes), and post-rejoin closure
`308ee2afa65fea397f9cd62899b06b10dce68239d82f81e60bf35e6dc20a17e1`
(5731 bytes). Source12 inventory136db is exclusively copied from its protected
transfer to root0600 source12/source-inputs-v12.json; four finite renderer
inputs are published before the original stage. Fresh release indexes include
the six helper copies, including changed CIL, before staging. Original image13
retains source9 build provenance under separate app-only compatibility; no
image load or application role starts. Native/old projection/key/selector
absence guards close. Stage source checks97 and bound wrapper/caller14 pass;
no required skip. Partial collisions refuse, and original owned-child EOF/reap
and safe failure-as-data behavior remain unchanged.

Policy25's sole actual installation passes0 in16.862s, outer
PID2991990/start411068615 reaped/absent. Local result SHA256
`2639b3970dd3653b1868a8c3fe2ac1dc69421149c845e9fafcce298a8c78070d`;
all local/guest captures close. Protected policy RESULT SHA256
`dcde1752f64ecda2fae4191b15bccf5010f67db93e5e00982731dc60c0375a20`,
47420 bytes, is actually held/read; safe private collectionf6257085 also stays
retained. Actual loaded module checksum is new CILfa3ebc3a, with new kernel
SHA256 `db2b822ad3d907ca2657119ec388ea934332ff7d4dbbd63c1ff6589c13a1cb20`.
Active1015-byte installation receipt SHA256
`95b66f4ca0dcee4283ea6979620f4bf7912d1891de9dc763e5023dfab0314df5`.
Exactly the old CIL inode78180921 and old receipt inode72117890 are retained at
their fixed policy24 backup paths, with only recorded own rename transitions.
New CIL and receipt are separate fresh leaves with their original required
types/modes. All nine policy command children exit0 and are reaped. The original
key and six other canonical files are unchanged; label rules, selector and
services remain unchanged/unstarted. Stage guards join actual native/rootless
receipts and both stopped historical generations; no old controller/load/stop
replay occurs. Product grants remain exactly the two status-only forms. Actual
helper startup and installed functional acceptance remain pending.

Fresh authority8/controller9 sources are frozen and independently reviewed;
only the new source12/current policy25 bindings differ from their preserved
historical authority/kernel/source rows. Completed B/C preservation is consumed
without another move, and selector/config descriptors plus three old108-file
projections stay held/rejoined. The new finite inputs use actual kernelDB2,
policy RESULTdcde/receipt95b and all measured stage receipts; safe donor transfer
and invocation remain pending. Source-only authority/preservation/controller
and safe-caller checks pass; none establishes installed readiness or feature
acceptance. Fresh rootless baseline source checks pass17 tests/0 skips in1.67s,
with exact original metadata/transport helper ASTs, real owned kernel-FD drift/
alias refusals and no leaked descriptors. That collector has not run yet.

Fresh stock983 baseline actually passes0 in1.079s, original
PID2993427/start411105219 reaped/absent. Local result SHA256
`a7a5a485f64ac42cab19b19a09cfa253c7d733a43d0ea9798c69f31747f55bed`;
all local captures close. The actual10403-byte guest success body computes
protected baseline RESULT SHA256
`ddb244bd516bcef229fe08441a89e57bac62f8645beaba3b8ab4e6563d199da5`,
which the watcher must hold/read before trusting. Stock secret listing has
count0/unknown0/rows[], and current kernelDB2B is unchanged before/after.
Only metadata is collected; no payload body/digest or retirement occurs.

Authority8's three-file donor transfer actually passes0 in0.455s, original
PID2993970/start411120026 reaped/absent. All held local/key/12 old-and-current
proof captures close. Actual protected donor RESULT SHA256
`92046b610ef5867c8981bdfccf3f1c611ea9762e6094f3670177fa88322f4a05`,
1665 bytes, readbacks exactly c7d9 authority source,2846 inputs andbb27 controller.
No provisioning or service action occurs during that transfer. Source-only
20 tests/0 skips and independent read review pass.

The sole authority8 invocation actually passes0 in8.781s, original outer
PID2994095/start411122884 reaped/absent. Protected authority RESULT SHA256
`14933ae6008d16ea17af3c1c40c68401db1d4098e8c0a322520c7fe3da645436`,
158284 bytes, held/read after success; safe collectione05f5d8a/132100 bytes and
local result03df12d3 remain retained. New control9 SHA256
`325283da498b7809eac47244115bb119696b240793267d603f180cc90583fc75`;
manifest8 SHA256
`444e564f9e3849829302bb9a6923f349965eec328f1454dd98308774ee677514`;
controller9bb27 and fixture UUID2f30acde-5333-445f-8c90-4a5f419485b9 are joined
to actual source and receipt. The original installed validator succeeds,
controller load equals the proposed manifest, all29 command children exit0/
reaped, all local/donor/authority input captures close and the original key/
three old readonly projections remain unchanged. Completed B/C preservation
is consumed with selection_moves_replayed=false; no application role starts.
Readiness is not installed feature acceptance. Authority source, caller and
actual data-only bindings are independently reviewed; original helper/transport
function ASTs remain unchanged except the recorded scoped historical/current
preservation changes.

The new original source12 native functional attempt then actually fails1 in
5.881s, original outer PID2994928/start411145420 reaped/absent. Original runner
PID90621/start12029004 exits1 in5.043s and is reaped. Five wrapper command
children are reaped with statuses0/0/0/1/0. Protected native RESULT SHA256
`a16d4cf66064422f00dcf582cf8e85d542258b2cf071ccb751db620807d8d2af`,
8645 bytes; protected safe collection SHA256
`5c3556b7c8c0369e3ccb67be70855ad2a341c6c083bfb19bcf7d6976897c72bf`,
13440 bytes. Local result SHA256
`e57a5a68f819382cf88b418d8895c3472864c3cb293312645f40a1e83e2e5fbd`;
original stdout27e505af and local stderr91376b67 remain retained. Original
runner stdout is empty;62-byte private stderr stays protected. The result
reports functional_passed=false, and strict post-run quiescence plus captured
guest-input closure refuse. No READY/browser/installed peer/credential proof
is established. A bounded read-only successor will discover this owned
workspace's exact generation and measure stopped state, original PID/start
closure, source-secret gate and full helper invocation before inferring any
cause. Rootless execution is held; this original run is never replayed/reset.

All eight source12 functional/watcher templates pass24 source-only checks and
independent review. Native final binding changes exactly five SHA assignments
and caller PINS, with all operational ASTs unchanged; actual authority/result/
control/manifest/runner/kernel joins are independently checked. Those green
source tests do not override the actual functional failure. Retirement-v1's
stale embedded support hash produces80 failures/3 passes before guest I/O;
that inert artifact and red report stay preserved. A corrected fresh v2 and
negative-cohort private actor lifecycle closure are required before retirement
can be bound or executed.

The bounded native12 failure readback actually passes0 in0.627s, original
PID2996273/start411182095 reaped/absent. Local result SHA256
`1d4a7a0bade7508fe95abcd367843bdf7f94c32f8c300d596ecce9a2961af055`;
original stdout9e3c7b0c. All local captures close, original failed result/control
rejoin, and kernelDB2B stays unchanged. Three fixed read-command children exit0
and are reaped. New generation136b86f08c514aa6a1a872007d750929 has started=true,
stopped=true, paused=false, READY0/cgroups0/containers0 and all13 tracked
PID/start pairs numerically absent. State SHA256
`81564c6b8f2e35f6fd34357c05b5ba3eff4681138ed7f98314550a43d799469d`,
12208 bytes. All eight original source-secret gates pass with denied read/open,
flags0/sequence45 and unchanged DB2B before/after. Public cleanup_unknown and
failed receipts remain preserved, and no installed acceptance follows.

The current helper is loaded/inactive/dead/success, MainPID/ControlPID0,
empty cgroup/InvocationID and ExecMainPID0. This current state does not establish
its historical startup outcome. The native API retains failed status239 and
invocation92d5e754122b4262a5a14183d40db0cd; Caddy retains failed status243 and
invocation4b5a75af187345d0ae92cf3660db7099. Both have MainPID0/empty cgroup.
Verification is inactive/success with SIGTERM; all three user roles are inactive.
This getter observes nine roles, not the full13. No journal or audit query runs
yet. Pinned official systemd257 commit70bae source maps239 to CACHE_DIRECTORY
and243 to CREDENTIALS, but status alone does not establish the actual branch,
errno, path, decryption error or MAC/DAC cause. Exact invocation journal/AVC
readback is required before another correction. Primary receipt4caca7d6 and
source-only failure-getter45 passing checks are retained.

Retirement source12-v2 corrects only the inert v1 embedded-source mismatch by
restoring the exact original17 metadata-helper bytes/hash and opaque-backup
helper. Its85 source-only checks and independent85-check review pass with no
skip. Actual generation/ownership/six IDs/stop/public-proof pins remain unbound;
no retirement has occurred. Dedicated negative-cohort retirement additionally
requires the actual private actor LIFECYCLE receipt and fresh PID/cgroup absence
proof; original generation stop alone cannot establish that separate drain.

The exact API/Caddy invocation journal collector actually passes0 in0.876s,
outer PID2999804/start411283642 reaped/absent. Local result SHA256
`bfae44c3c447f29f38c3e495850fb00160d0d7c24769b043bf958324e73e636f`,
52076 bytes; original safe stdout SHA256
`ee93429dc400a03a92190dbadaadd712eda7c4feffb3d38a9323a4287de06b8c`.
All captured original failure/control/state inputs rejoin and close; kernelDB2B
and both failed unit invocations stay unchanged. All nine fixed read-command
children exit0/reaped. Exact journal invocation joins establish API PID90725
failed special-execution-directory preparation with PermissionDenied at
CACHE_DIRECTORY, while Caddy PID90728 failed credential preparation. The
bounded audit includes32194, init_t denied setattr on hub_state_t directory
inode127585451 with API numeric PID90725, and32191, init_t denied read on
secret_t file inode9905766 with PID90732. The latter process is not yet joined
to the Caddy credential child; fixed inode/path and audit lineage readback is
required before any permission or fixture correction. No arbitrary journal
message/path, credential body or raw channel is published. Raw channels remain
root-private. All13 fixed role observations show API/Caddy failed and the
other11 inactive, with no executors or cgroups; these observations do not
establish successful strict quiescence or installed acceptance. Collector
source-only checks pass84 tests/0 skips; independent source read is clear.
No service, selection, label or policy change occurs, and rootless stays held.
Plan evidence checks pass9 tests/0 skips in0.28s; documentation alignment passes
206 human documents/27 helpers and diff check passes. A fresh no-follow
1359-file hash/mode comparison has zero mismatches against source12; the
bookkeeping updates do not invalidate its earlier green strict source gate.

The fixed inode/lineage followup actually passes0 in0.784s, outer
PID3001814/start411325908 reaped/absent. Local result SHA256
`da9ff3acc669fd56977d6a85895341229a3783359b848415c833eb7b0d636e17`,
44247 bytes; original stdout ea817619. Protected RESULT computes SHA256
`28ac224a22b2a518cab0219f24b52dac717e82906c4d7911a10e1016645fc309`,
27815 bytes. Held metadata proves cache device64515/inode127585451 has the
Hub-state type. Original event32194 joins API executor90725/PPID1, fixed
systemd-executor/x86_64, failed syscall452/errno13 and directory setattr denial.
TLS device64515/inode9905766 has the secret type; original event32191 joins
credential child90732/PPID90728 to the exact Caddy invocation, fixed executor/
x86_64, failed syscall257/errno13 and file-read denial. Both complete events
come from the held original audit channel; no additional audit query is needed.
Six fixed read-command children exit0/reaped; metadata-only source descriptors,
original result/channels, unit brackets and unchanged kernelDB2B all close.
No credential/application payload body is read. Source-only42 checks pass;
independent actual review14698c84 confirms these exact causal joins. Neither
query nor review establishes installed feature acceptance.

The reviewed five-file source13 correction is applied after those joins:
exactly init_t to Hub-state directory setattr and init_t to secret file read.
All helper allows/neverallows, object labels, service hardening and fixed
manager/control boundaries stay unchanged. Human/ADR/security text explains
the type-wide trusted-manager rights, including all secret-type files; the
protected units/root provisioning supply paths. Focused policy/provisioning
regressions pass259 tests/0 skips in14.65s; human documentation206/27 and diff
checks pass. Original source12 failures and diagnostics remain retained.

Fresh source13 capture passes0 in0.642s, outer3002167/start411334859 reaped/
absent. Capture SHA256
`c28a1aa9ac0290594860a83561b98187c033c865e625e94e02d196c92ed33074`;
1359-file snapshot
`6770cdb81e8fb63088fdd3906e230a145d9b1b2dd4edcc1147a13d54620b3120`;
inventory SHA256
`a22191d044a9034c1aa52f2702579e6abfdf0c9d49a14b471e305fc4ad85bb8d`;
archive SHA256
`a75082a6f9fd4e37d42548a8b719b4f694fac27e5f317f8f0d75dc4f6b9e47b4`,
17704960 bytes. Only the same five policy/docs/test paths differ from source12.
The strict source13 gate actually starts with original outer
PID3002354/start411338769 and is still running; no exit or pass is inferred.
Its runner d0bd90d0 has only epoch/capture substitutions from the original
owned gate12 runner, confirmed by whole-AST comparison and independent read.
The guest remains source12/kernel25; no new policy installation or role start
occurs. A plain systemctl stop of a failed unit may return success without
transitioning it inactive, as pinned systemd source confirms. Preparation
therefore requires exact preserved-failure admission rather than a stop/reset
or general allowance for failed units. Rootless remains held.

The source9-to13 application-only comparator actually passes0 in0.826s,
original PID3005951/start411356698 reaped/absent. Its actual3480-byte receipt
SHA256 `0a7fa0f9a4c893e19efa388c007d9932921f2eaab7837c92bcf11fa79edc5e36`
is copied byte-for-byte from the private original stdout, without reencoding.
It rechecks both archives/captures and all1359 current source hashes/modes,
exactly five changed paths and exactly four source9-to13 CIL allow forms,
all108 application wheel leaves, two46-input/six-output UI builds,81 image
context wheels and pinned UBI10micro recipe/locks. Artifact9/image13 retain
their original source9 provenance. Host compatibility remains false; fresh
host stages/policy/authority and installed functional proof are required.
The comparator's38 source-only checks pass, with no required skip. It performs
no guest, build or runtime effect. Source13 strict gate continues independently.

The preparatory preserved-failure helper is frozen at v2 SHA256
`cf3e07b8125bebebcc18ab246b973d2df5c66cc2b8f60ea1f6b9e6767b583bbd`,
18249 bytes, with93 focused checks passing/0 skips. It holds exact original
failed-result/state/control/journal records, compares both full17-property
failure snapshots, requires the other11 roles inactive and all13 recorded plus
three startup numeric PIDs absent, and retains owned query PID/start/reap proof.
The scoped old classifier adapter preserves its inventory/cardinality/ownership
checks, actual failed observations and PRIOR_UNITS; it restores the classifier
on exit. It is used only during preparation and closes before any application
start. Functional post-run quiescence remains strict. Inert v1/77-check evidence
is preserved: review found socket/timer properties may be absent; v2's two-line
correction allows that original schema while requiring service executor fields.
No guest execution or service-state normalization has occurred for this helper.

The first source12 pre-refresh audit for source13 actually refuses1 in1.095s,
outer PID3014899/start411435460 reaped/absent. Original safe stdout SHA256
`1f53952ae7ab4eff3cfa0eb6ed8a69f93b1593d62459e67afec4afa73a662e08`,
5644 bytes, and544-byte stderr aa58e3e3 remain retained. The safe guest result
has audit=null, ValueError, protected_result=null and
existing_fixture_state_mutated=false. Eight fixed metadata commands exit0 and
are reaped; no positive audit/closure, source transfer, staging, installation
or functional result is established. The refusal occurs inside the exact
failed-state bracket, before the later audit queries. Diagnose the actual
input/schema assumption and add bounded closed phase/function-line evidence
before a fresh v2; do not replay v1 or infer another policy defect. All source12
failed receipts/state and source13 templates remain preserved.

Source13 strict gate continues independently: backend7732 tests pass with52
explicit opt-in deselections in968.67s; frontend/install/build stages and the
final unchanged-source comparison remain pending. This partial stage result
does not establish a completed strict gate or installed acceptance.

Source13 strict gate subsequently passes0 in1242.215s,04:54:06.039154 through
05:14:48.253792UTC. Original outer3002354/start411338769 and gate owner
3002355/start411338788 are both reaped/absent. Result SHA256
`395c050b14d8a6aa34711e3c1ec01398367fe3a99e8ba9b029e2616c48d20521`,
816 bytes; log SHA256
`3d2d2035d252f4c812c7f4045fe4ab0e92f63c122dd912b28d850560a3b58165`,
100803 bytes. All1359 captured source hashes/modes remain unchanged, with no
capture error. Actual stages pass7732 Python/52 explicit opt-in deselections,
three locked wheel profiles,572 historical frontend,2786 web unit,2846 component, wire/
lint/types/build, two Chromium startup checks and the real HTTP/API React read
fixture. Required stages report no skipped checks. Installed Caddy/native/
rootless/host-negative/drain acceptance remains separate and incomplete.

Preparation review corrects a root assumption: selector/config absence before
the native12 attempt was not a measurement of their state after that attempt.
Controller start activates those leaves and stop does not remove them. Current
presence/absence must be measured directly; preserve the exact observed branch
before deciding whether real three-leaf preservation is required. No file is
removed or normalized based on the assumption. The failed v1 audit and all
inert successor templates remain preserved; v2 gains bounded phase/location
and fixed-leaf metadata observation before another read-only attempt.

Diagnostic caller-v2 refuses locally before SSH because its REMOTE still names
guest-v1 while its hash/size pins name guest-v2. Outer3023742/start411488835
is reaped/absent, exit1 in0.099s, with zero SSH records. Original stdout
a8925192/1501 bytes and stderr4215840b/1031 bytes remain retained. Fresh
caller-v3 changes only the remote pathname and its local result destination;
three checks actually capture/join the declared file and prove the stale path
refuses. Frozen guest-v2 remains unchanged, with18 source-only checks passing.

The sole guest-v2 invocation via caller-v3 then refuses1 in0.8265s, outer
PID3024055/start411499640 reaped/absent. Original safe stdout SHA256
`92db6f4bb57b993d05d8c0d1188faf89cea49dfae80110df874081c59691ab97`,
7245 bytes; stderr544 bytes aa58e3e3. Eight queries exit0/reaped; no existing
guest state changes and no positive audit is published. Bounded diagnostics
locate the failed assumption at selector-profile-absence, audit658 to
absent_paths885 to need85. Metadata-only fixed-leaf observations establish all
three leaves present: selector device64515/inode60239548, root-owned symlink,
14 bytes, usr_t, exact fixed native target; deployment inode77965616, root644,
47907 bytes, conf_t; policy inode77965617, root600,275 bytes, conf_t. All three
full metadata/context observations are stable, with no file-body/key read.
The next fresh audit must verify these actual present leaves against control9's
native bindings. Preservation then needs real three-leaf and two-release-tree
moves, with each original retained. Conditional authority9 supports that branch;
its future evidence pins remain unbound. No guard is relaxed on an assumption.

The present-state guest audit-v3 actually succeeds and publishes its original
protected RESULT at source12-pre-refresh-audit-v3/RESULT.json, SHA256
`bf4a2d95f1869d15576cd4b933c40363db45c53dfc2b4f307671b563864f6aab`,
28880 bytes, root600/usr_t/inode118436592. However, caller-v4 refuses its local
path classifier, which still expects audit-v2. Outer3024921/start411526853 is
reaped/absent, exit1 in2.261s; safe stdout SHA256
`85425643899e92a5eb50dfd44fb19fce3a73c217f29d1029b3ef4fb94535b9c9`,
33954 bytes, and stderr544 bytes dd44de12 remain retained. The returned guest
proof has error_class=null and safe_failure=null, verified native proposal
bindings and16 reaped queries; the local capture-closure flag remains false.
Do not promote that failed collection or replay the successful guest audit.
A fixed read-only getter must hold/rejoin the original exact protected result
and local sources/evidence before its actual hash can authorize preservation.
No application/policy/selector change has occurred.

The fixed saved-result getter/caller-v5 actually passes0 in0.496s, outer
PID3027225/start411586574 reaped/absent. Local result SHA256
`21169befb6ab21b38992ee431668a38e1a06e878b418bd2be2735f4c7f250828`,
57167 bytes; safe stdout a4f24682/36481 bytes, stderr empty. All held local
original guest/caller/collection and transport inputs rejoin and close. The
original protected bf4a2d95/28880 receipt is read through its exact root600
full metadata/context and canonical body; current three present leaves rejoin
by O_PATH metadata, with no key-body/digest read. Original sixteen query records
and closed historical failure admission remain unchanged. No audit replay,
guest mutation or installed acceptance is claimed. Getter source-only20 checks
pass with no skip. This closes collection of the one original guest audit;
the earlier failed local collections remain failed and preserved.

Native13 preparation source checks55 owner plus55 independent pass, and the
source13 rootless six-template/baseline package passes37+81 owner checks and
118 independent checks, without required skips. These are inert successor
templates with future authority/kernel/native-pass pins unbound. The native
historical failure admission closes before original runner startup; post-run
quiescence stays strict. Rootless's fresh empty baseline must hold actual
native13 PASS/strict closure before store access; no historical failed-state
exception applies to rootless functional or baseline acceptance.

The protected source13 transfer actually passes0 in0.947s, original outer
PID3027831/start411604490 reaped/absent. Safe stdout SHA256
`40e638a3ab2ddda1eb63d17cc735085b0adc467dad40adc07165e2d6d09b9d60`,
7723 bytes, and empty stderr are retained at
`.scratch/web-006-source13-protected-transfer-owned-v1.*`. All held local inputs
and six original guest records rejoin and close. The protected transfer RESULT
body is SHA256 `f750c36917432b66e3022fe0d5b2d4e9548e98df76df5859251975a9dacc72da`,
5068 bytes. Four fresh root600 staged files hold the exact source13 inventory,
archive, capture and previous-failure bridge; the separate application-only
compatibility receipt is transferred byte-exact as0a7fa0f9/3480 bytes. The
1359-file archive remains unextracted, public source12 unchanged and current
three active leaves present. No service, selector, policy, label or authority
change occurs. Transfer source checks25 pass without skips; this is transfer
evidence, not installed acceptance. The next preservation must retain the
actual three leaves and two old release trees before fresh staging.

The reviewed preservation caller-v2 actually passes0 in28.699s, outer
PID3029386/start411649197 reaped/absent. Local result
`.scratch/web-006-source13-preservation-v2-result.json` is SHA256
`874e8e1f1afa73b15ae7cf75cab278882f0bde1eda6ab608576aa57b77af6f07`,
50229 bytes; original protected source13-stage-preservation-v1/RESULT.json
is `38bca707bfd6351ab2dd203a3e7a74ae895a3cf24f2adad9289232c321bdc500`,
27875 bytes. Safe stdout9d30bc2a/32851 bytes and empty stderr are retained.
All local captures close and all owned queries exit0/reaped. The actual selector
inode60239548, deployment77965616 and policy77965617 are retained by separate
no-replace moves with durable receipts; native94380179 and rootless84675094
release trees retain their original inodes and verified inventories/contexts.
All five original names are now absent. The exact1359-file source13 archive is
extracted privately. Original key78157344 is checked metadata-only; canonical
files, loaded policy and prior failed state are unchanged. Historical failure
admission closes after input revalidation; no service starts/stops, old authority
or operation replay, reset, installation or feature acceptance occurs. Owner82
and independent82 source checks pass without skips. An initial local logger
invocation used a disallowed prefixed output name and refused before any child
or output creation; only the corrected bare-name invocation reaches the guest.
Next are the public fixture update and fresh native/rootless stages.

The public fixture source13 update actually passes0 in1.769s, outer
PID3030453/start411671378 reaped/absent. Local result
`.scratch/web-006-public-source13-update-v1-result.json` is SHA256
`9e8bcaa720426e6127819fb59251d7ee9d708fd8ae73ca2d90b6895f0c52d7e9`,
44724 bytes; safe stdoutada6dcf2/31036 bytes and empty stderr are retained.
All1359 source hashes/modes verify, and all five changed original leaves are
saved with their prior bytes/modes. All nine owned queries/updates exit0/reaped;
local inputs and historical failure admission rejoin/close. The guest writes
public-source13-update-v1/RESULT.json with canonical body SHA256
`81ad6a571ffd6f662294bf02f1ca7a8d6fdc981426800f68827931937ef43119`,
28388 bytes; a later consumer must capture that original protected file before
using it as an input. Loaded policy remainsDB2/policy25; no service, selector,
key, label or authority changes occur. Old control9 is not loaded after the
update. Source checks39 pass without skips, including a real1359-file owned
clone update, retained original leaves/unrelated work, two-pipe EOF/reap and
actual producer-path/caller classification. Fresh installed stages remain next;
no installed functional acceptance is established.

Independent local reviews of actual preservation and public update pass,
receipts59f8a288/1411 bytes and08289572/1112 bytes respectively. They rejoin
original metadata, saved canonical bodies, source inventories, query ownership
and closed failure admission without another guest action. Policy26's fresh
partial-binding template changes only four module assignments to the actual
audit-v3, preservation and application-only compatibility receipts; all function
and class ASTs remain unchanged. Its144 source checks pass0/no skip in1.92s,
Python3.12 parsing and selected Ruff syntax pass. Native-stage and rootless-closure
pins remain unbound and refuse before host access. No policy installation is
claimed. All1359 source13 hashes/modes are independently rechecked unchanged
after bookkeeping. Current checkpoint23 SHA256
`1c894b57efb3a18c0d8efdda268869c187e133ea5a4fc20434fd917a0d1cfaf5`
retains the prior checkpoint chain and these actual records.

Fresh native13 staging actually passes0 in30.990s, outer
PID3031556/start411697565 reaped/absent. Local result
`.scratch/web-006-native-source13-restage-v1-result.json` is SHA256
`49ba7ade5386a9d35d9a76185463ab2d98fa4d8eafb24bdfb6ba521c4e6d3f93`,
52967 bytes. Original protected native-restage-source13-v1/RESULT.json is
`bb0b1beeb70fec0e9652537f4e64d6743f37a19f25edb576fb0e8af66ec55554`,
24468 bytes, root600/usr_t/inode118443952. Original installer
PID91349/start12581840 exits0/reaped with108 installed package leaves verified;
all17 recorded queries/installer commands exit0/reaped. Source checks75 pass
without skips; embedded utility definitions are independently AST-equal to
the actual preserved-source donor, with its main excluded and never executed.
All held stage inputs and historical failure admission close. The old selector
inode60239548 is retained at native-restage-source13-v1/source12-selector,
outside the original installer's restorecon scope, with its raw target and
context unchanged. Old release trees/projection and protected configurations
remain preserved. Active selector/config names remain absent and no rootless
stage, policy provision or application startup occurs. This is original native
installation preparation, not installed functional acceptance.

Fresh rootless13 input publication/staging actually passes0 in3.513s, outer
PID3032203/start411717918 reaped/absent. Local result
`.scratch/web-006-rootless13-input-stage-v1-result.json` is SHA256
`ff16a74c29d744f89cb58bb636f615673aea1cacd518e7ceadb6b86cdbf04b27`,
44646 bytes. Protected wrapper RESULT is9decd573/36514 bytes. Original
rootless-stage-source13-v1 records are staged.json
`a8ccce364ceda347f32d58296df5f5e25ea5536b476b90a17326a536a718a31e`,
19592 bytes; input-provenance.json
`40347155bcdfba4e04186848b2b82be9c524b130f665e2c50de131e6fcfc9126`,
11964 bytes; refresh-closure.json
`047a3b28135f61a1d09e6f96a063d3790dbe6f95eaa0c8c33f4cddda38d115e2`,
31440 bytes. All three returned metadata records are root600/usr_t; their
bodies are not present in this local collection and the next guest consumer
must hold/verify the originals. Publication admission and local inputs close;
no image load, application starts, key read or feature acceptance occurs.
Source checks34 owner plus34 independent, and final binding10 pass without
skips; final fixed argument113304 bytes stays below120000. Independent actual
records-only reviewb232c7d2/3421 bytes passes with this body-availability limit
explicit. Policy26's fully bound guest/caller now pass178 focused checks without
skips in3.74s, selected Ruff/Python3.12 parsing and actual caller FD/source/argument
joins; fixed argument55224 bytes. Only exact actual receipt assignments change,
all functions remain unchanged. Policy installation is still pending at this
evidence point, followed by fresh authority and native functional acceptance.

Policy26 actually installs successfully in the owned disposable guest,
exit0 in12.431s, outer PID3032781/start411736978 reaped/absent. Local result
`.scratch/web-006-policy26-refresh-v1-result.json` is SHA256
`33666dc0b7e05bc1f07e247b25a4a70b40b55a3841a54318a1a9f6e6daae813e`,
188344 bytes. Original protected policy26-canonical-and-receipt-v1/RESULT.json
is `354a0336b347a130ec7e259d2fa7605eac415ea48ea9683339f67b9c49d5cf68`,
87229 bytes. All19 owned commands exit0/reaped; policy and local input captures,
original stage receipts and exact historical failure admission rejoin/close.
Loaded CIL matches0715354f/17688 bytes; new kernel policy SHA256
`fc512990f83f680ec365a36c4c8fc6ae78177e42e63362ba4f1238264587e461`
and installed receipt030aee64/1015 bytes are measured. The old policy25 CIL
inode77956150 and receipt77965606 retain their original bytes/modes/context
under separate fixed policy25-preserved names. Original key78157344 is unchanged
by metadata-only checks; six canonical helper files and label rules are unchanged.
No service starts, selector change, replay or installed functional acceptance
occurs. Fresh authority9 and native functional execution remain next.

Independent policy26 actual-result review844cdbb8/6365 bytes passes. It rejoins
the local original execution, protected policy/collection canonical bodies,
19 reaped commands,68 label records, preserved policy25 inodes, unchanged key
and closed input/admission proofs without guest action. On the subsequent
explicit user continuation, git remains07d10e0 on feat/web-ui with WEB-006 active;
all1359 frozen source13 hashes/modes and native-functional templates are unchanged.
Authority9 is still unexecuted. Review catches a source-only donor-v1 mismatch:
its controller tar member has a web-006 prefix while the caller and authority
hold fixed-controller-v10.py. Preserve the inert v1 packet and prepare a fresh
v2 tar/guest/caller with one consistent name; no guest attempt occurs on v1.
The authority source and inputs bind only measured stage/policy receipts;
397 original prior process pairs remain unchanged. New preparation command
ownership remains in each separately retained receipt. A bounded deterministic
gzip envelope carries the exact verified authority source, checking compressed
and plain hashes/lengths before compilation; measured argument37211 bytes stays
below the original120000 guard. No authority publication or functional proof is
claimed from these preparation checks.

Corrected authority9 donor-v2 transfer actually passes0 in0.510s, outer
PID3068349/start413430042 reaped/absent. Local result
`.scratch/web-006-authority9-donors-v2-result.json` is707cf79f/6133 bytes;
protected fresh-authority9-donors-v1/RESULT.json is7bb00b69/1667 bytes.
All three expected root600 donor files, including fixed-controller-v10.py,
verify and held inputs close. No authority or application execution occurs in
the transfer. Final packet checks60 owner and34 independent pass without skips;
independent reviewbe11661f/3787 bytes closes the corrected tar/name/schema,
source bindings and bounded compressed-source envelope.

The one original authority9 provisioning attempt then fails1 in8.018s, outer
PID3068480/start413433625 reaped/absent. Local result
`.scratch/web-006-authority9-source13-v1-result.json` is SHA256
`643519e01526ff6309781e4c962497ae269d645f4af3a5187c46577d533ee932`,
329417 bytes; original protected fixture-authority-v9/RESULT.json is
`712569dd00f5ef5ce8e6d6ee98eb4add3100af260d9930ea1e07b1cbd5c82cfb`,
255525 bytes. All36 recorded commands exit0/reaped and donor captures close,
but authority readiness and overall input closure do not pass. Validator,
controller and key flags remain their initial false values; these are not
measured negative findings, and missing returned publication fields do not
prove their paths absent. The saved failure is ValueError; no native functional invocation
or application role start occurs. Partial authority files and every original
receipt remain intact. Diagnose by a fresh bounded read-only getter of the
original private traceback and fixed metadata; do not replay provisioning,
reset states or infer readiness from earlier preparation passes. Native and
rootless functional acceptance remain held.

The exact original authority9 failure getter actually passes0 in0.453s,
outer PID3070247/start413476686 reaped/absent. Local result
`.scratch/web-006-authority9-failure-getter-v2-result.json` is SHA256
`cc588b36d2e2aed00a9319e12ac1e76fbc3d7c6c1e244c5fabf2686220395109`,
24623 bytes; safe stdout7b418067/17189 bytes and empty stderr are retained.
All eight held local inputs, the exact protected failed receipt/private stderr
and25 fixed metadata paths rejoin/close. No guest mutation or process action
occurs. Classified original frames locate publish_authority639 to controller
load_control1005, record291, read236 and need181. This confirms the input-loop
root-owned-ancestor predicate; authority9's producer included two historical
public receipts below the UID1000 home while the unchanged controller's input
reader requires root-owned ancestry. Raw traceback messages/code/locals are not
published. Actual metadata establishes the partial private/public proposals,
controller, control10, manifest9, generation directory, sudoers and read-only
projection exist; missing returned success fields did not imply their absence.
The active selector and both active configuration names remain absent.
Getter checks18 owner and18 independent pass without skips. The stale caller-v1
capture tuple is preserved inert; corrected caller-v2 exercises all eight actual
FD captures before its positive classifier. No authority replay occurs.
A fresh authority10 must retain the complete partial authority9/projection and
use protected exact-byte copies of the two historical receipts as controller
inputs while independently holding their originals. Controller access rules
stay unchanged; fresh paths/UUID and original-failure closure precede effects.

The read-only partial authority9 audit actually passes0 in1.154s, outer
PID3072367/start413529159 reaped/absent. Local result
`.scratch/web-006-authority9-partial-publication-audit-v4-result.json` is SHA256
`1a206f3e298c27aa30756db725cb72176e72401ee8b50a10fb413305be8a5304`,
81688 bytes. Original protected authority9-partial-publication-audit-v1/RESULT.json
is `97c8e7e80d0d9839139e5ea8a9e77ffa99c3fa67b0b026763548c6f110a955ea`,
50105 bytes. Control10 is2b7700a1/7991 bytes, manifest9 is351fba03/4466 bytes,
projection record7dd33de9/10670 bytes. The25 original metadata objects,32 ordered
control input records, eight private/public proposals, eight retained publication
records and108 source/projection leaf inode/hash/context pairs rejoin/close.
Projection remains read-only and all36 prior command PIDs are numerically absent.
Eight new read-only queries exit0/reaped; exact historical failure admission
closes, kernelFC5129 and original key metadata remain unchanged, active three
names remain absent. Only the new audit directory/receipt is created after
held-input closure. No copy, replay, service action, projection change or
installed acceptance occurs. Source checks12 owner plus seven independent pass
without skips, including producer-main-to-caller receipt joins, late closure
refusal and real owned108-file paired FD checks with explicit local ownership/
read-only modeling. Inert draft bugs (missing bytes field and errno import)
are corrected in preserved successor scripts before the one actual audit call.
Fresh authority10/control11/gen11 uses separate paths and fixture UUID
6c567df5-3947-4d80-a7a8-ea73f72399ca; it must hold this actual audit and retain
all partial9 files/projection while using two exact protected receipt copies.

Final authority10 preparation packet passes65 owner and65 independent focused
checks without skips. All seven file hashes/sizes/modes, three tar member names,
exact captured gzip source and39783-byte argument join; final source4393cf08
differs from reviewed template v3 only by the measured input SHA assignment.
The first source-only caller has a stale protected RESULT classifier path;
preserve it inert. Corrected caller-v2fc5ee7f7 verifies fixture-authority-v10,
both protected copies,108 projection rows and held-input closure before any
guest invocation. Independent packet receiptf84f3a99/4521 bytes records this
review; these checks alone establish no installed acceptance.

The one authority10 donor transfer actually passes0 in0.513s, outer
PID3075649/start413632395 reaped/absent. Local
`.scratch/web-006-authority10-donors-v1-result.json` retains the exact three
root600 donor records; protected fresh-authority10-donors-v1/RESULT.json is
8741b381/1676 bytes. No authority or application execution occurs in transfer.

The one original authority10 preparation then actually passes0 in9.747s,
outer PID3075707/start413637142 reaped/absent. Local
`.scratch/web-006-authority10-source13-v2-result.json` is SHA256
`b4fdea51532f5a756407fb28ede8fee1649be4afedd6a1bb720491368baf3236`,
580022 bytes. Protected fixture-authority-v10/RESULT.json is
`d81c7a12c36c91bf6f1c772ab5b7e349db591fb7aaffc2c18b0c6cb6f67b106a`,
469486 bytes; protected collection92cec675/353865 bytes closes donor inputs.
All45 recorded commands exit0/reaped; the original installed validator,
controller load, unchanged key metadata, full partial9 preservation and both
root600 exact-byte historical receipt copies pass. Original216 source/target
leaf FDs remain held through final closure; all108 projection pairs retain
their original metadata, contexts and hashes. Original public receipts and
all partial9 files/projection remain unchanged; failed outcomes are not
promoted. Control11 is2f069e9f and manifest10 is6de282e1.
Controller11 access/read semantics remain unchanged. No application/helper
roles start, no selection move is replayed, and installed feature acceptance
remains false. Bind fresh native13-v2 only to these actual receipts and
kernelFC5129. Rootless, negative/fault, exact-secret and strict drain proofs
remain pending. All1359 frozen source13 hashes/modes recheck unchanged.

Native13-v2 final binding checks pass63 owner and63 independent without skips;
all functions remain unchanged, with only five actual guest SHA assignments
and the caller's remote-source pin bound. Source checks e457de80/1653 bytes and
ef6c21aa/1977 bytes record this preparation; fixed SSH argument88759 bytes.
The preparation admission closes before the original1800-second runner begins.
The unchanged wrapper's strict post-run query covers nine fixed manager roles;
the later rootless baseline separately requires all13. Do not describe the
nine-row wrapper alone as a13-role proof.

The one original native13-v2 functional attempt then fails1 in6.674s, outer
PID3075984/start413658474 reaped/absent. Local
`.scratch/web-006-original-native-functional-source13-v2-result.json` is
`e1755ca8ea505d7056836f5e3d4893899f71fc47d2459afe005e141ae01f7936`,
75460 bytes. Protected native-source13-original-functional-v2/RESULT.json is
`6e6b13755e9a1e533d672150b11938cfa2e990f930f7d97d089188258d9a04ab`,
52142 bytes; collection5c36ec19/64561 bytes preserves the result without replay.
The original runner92422/start14542027 exits1/reaped after5.291s; its62-byte
stderr is the fixed generic refusal, not a causal diagnostic. The subsequent
strict wrapper query refuses and guest/local input closure does not pass.
No functional success or successful all-role drain is established. Preserve
the original generation and all private/public receipts. Read current fixed
manager/generation metadata and original failure evidence without rerunning,
resetting or promoting this attempt. Post-attempt selector/configuration and
role state require actual readback; the earlier absent-name/failed12 observations
must not be substituted for the new current state. Rootless and all later
dependent functional work remain held.

The bounded native13 failure readback actually passes0 in0.630s, outer
PID3076625/start413709785 reaped/absent. Local
`.scratch/web-006-native-source13-failure-readback-v3-result.json` is
`00fa8ee7943bdd469aac585732d7ce3d03c9c54b4a84aa27fd184984414c3f35`,
36540 bytes. Its eight local captures and original guest inputs rejoin/close;
two fixed read-only queries exit0/reaped and return all13 manager rows.
Source checks six owner plus six independent pass without skips. Draft
caller-variable/provenance and regex-warning defects are corrected before the
one guest call; all inert drafts remain preserved.

Actual generation63c4116da6284c4dacea6670fd01155f has started/stopped flags true,
no READY, no captured cgroups/containers and12 original PID/start pairs all
numerically absent. Root stateb16221ba/11646 bytes and original public failed
RESULTe077ccbd/1936 bytes remain held. The originals-before-helper label gate
passes on all eight source objects with kernelFC5129, enforcing sequence46
and helper read/open denials; delivered-role proof is not reached. Current API
and Caddy both have new failed243 invocations, respectively
9cf7fdfb7dad4507af99fa887256dbfc/PID92528 and
4ab296cb94b04087925c6560eea01168/PID92529. Both have MainPID/ControlPID0 and empty
cgroups; the other eleven roles are inactive. This establishes current bounded
manager/process observations, not successful strict all-role quiescence or the
cause of either credential-stage failure. Original helper startup remains
unattributed by its current inactive/empty-invocation row. Selector and both
active configurations are present; the selector points relatively to native
0.2.2. Original key78157344 retains its exact full metadata/context by O_PATH
checks, without a body or digest read. Next collect exact new invocation journals
and bounded audit inode/lineage evidence before any source-policy correction.
No replay, reset, role action, kernel-policy read or installed acceptance occurs
in this diagnostic. Rootless acceptance remains held.

The exact native13 API/Caddy invocation journal collector actually passes0 in
0.838s, outer PID3076941/start413740215 reaped/absent. Local
`.scratch/web-006-native-source13-role-failure-journal-v2-result.json` is
`31afba9adf2921e50a4f942be064166dea367d28c9c8c0505fe8b2e97b5d970b`,
52630 bytes. All nine read-only commands exit0/reaped, both full17-property
unit records rejoin before/after, kernelFC5129 is unchanged and original inputs
rejoin. Protected readbackc5b45309/29901 bytes is now actually held/verified,
after being only a locally derived expected hash previously. Source checks41
owner plus41 independent pass without skips. A source-only duplicate system/
user unit-name binding collision is caught and corrected in preserved v2
before the one guest call; system scope is explicit.

The exact new invocation journals classify both failures at credentials setup.
Bounded AVC records show33131/PID92536/file-open/inode9905766 at the known TLS
key source and33134/PID92542/file-open/inode10012070 at the encrypted API
credential. Both are enforcing init_t to the secret type. These remain candidate
causal events: neither reporter is the journal's service process, and original
event SYSCALL/parent lineage plus metadata-only target identity must be joined
before a permission correction. Unrelated helper ioctl/certificate-directory
denials in the same window do not justify helper access changes. No raw messages
or credential channels are published, and no service/reset/policy/selection
change or installed acceptance occurs. Exact inode/lineage collection is next.

The native13 identity/lineage collector actually passes0 in0.783s, outer
PID3079440/start413797060 reaped/absent. Local
`.scratch/web-006-native-source13-role-failure-identity-v2-result.json` is
`262f48d23370b37432262271e55ec06e3e977b8fefa8b3fdf26e552831306d31`,
51026 bytes. All six read-only queries exit0/reaped and all held inputs close;
protected journaldec932cb/46524 bytes is now actually verified. Source checks25
owner plus25 independent pass without skips; the inherited cache-directory
predicate is corrected for the encrypted credential's regular O_PATH file
before execution, with the inert draft retained.

Both current credential sources match their pre-helper original gate's full
nine metadata fields and SID. Exact AVC PID/inode/full source and target SID,
openat257 failure errno13, systemd-executor identity, PPID lineage and invocation
monotonic-window joins pass for both33131 and33134. The fixed init_t AV queries
on each held actual SID show read/getattr allowed and open denied, enforcing
flags0/sequence46 before and after. No broader manager right is justified.
However, the actual events contain AVC/SYSCALL/PROCTITLE only: no PATH records
exist, so fixed_PATH_inode_owner_match and combined all_measured_joins_proven
remain false. Preserve these measured flags. A separate bounded read-only
saved-AVC name/device check must establish the exact fixed path using the actual
AVC name field, without rewriting the earlier result or claiming nonexistent
PATH records. No credential body/digest, role action, policy change or feature
acceptance occurs. The minimal manager-open correction remains pending that
additional attribution review.

The separate saved-AVC name/device packet passes21 owner plus21 independent
source checks without skips. The local owned launcher first rejects the
uppercase AVC filename before starting a child. Preserve the original and
create a byte-identical lowercase caller copy with the same d7d7ac5a/8082 pin;
do not widen the launcher's filename grammar. The one resulting guest attempt
then fails1 in0.454s, outer PID3080755/start413841607 reaped/absent. Local
`.scratch/web-006-native-source13-AVC-name-device-v2-result.json` is
`c3345ecea6792cc95050c3f276f556e301c44fddda759bf73ee505d34a4ee290`,
3296 bytes. Sole SSH child3080756/start413841612 exits1/reaped with stdout0;
its297-byte stderr is retained only as hash82a34eac by the original transport,
not as a recoverable raw channel. The returned result is null and the remote
exception/phase remain unknown. No diagnostic or causal success may be inferred
from this attempt, and absence of the new guest WORK path is not established.
Preserve it; use a new definitions-only read-only phase/projection probe that
never invokes the original main or writes its WORK. Audit path-versus-name
formatting is a hypothesis until actually measured. Original false PATH flags
and all earlier receipts remain unchanged; the manager-open correction is still
pending. No role/reset/policy/credential-body action is introduced.

The new definitions-only probe returns0 in0.432s, outer
PID3082138/start413890222 reaped/absent. Local
`.scratch/web-006-native-source13-avc-field-probe-v3-result.json` is
`6f6bb3dfda793296b2173eefd8baf5d0bfc52c1e0300c3165d7eb35af77386fb`,
9139 bytes. Both events have exactly one quoted AVC `path=` equal to the fixed
source and no `name=` field. PID/inode/full source and target SID match; audit
devicevda3 matches fixed sysfs252:3 and held metadata st_dev64515. All opened FDs
rejoin/close, with no old main call, guest WORK/result creation or new role/audit/
policy query. Original name-only pure projection still returns the measured
ValueError at name_field; original WORK is actually absent before/after. This
identifies the supplemental diagnostic's refusal without replaying it or
rewriting earlier false PATH flags. Original protected identityd0b258e9/33816
bytes is now actually held/verified. Ten owner plus ten independent source
checks pass without skips; final v3 differs only by removing an unused import.

Independent composite review826081e4/11022 bytes joins this separate positive
path/device proof to the earlier exact metadata/SID, openat/PPID and invocation
evidence. It supports only the missing trusted-manager file open right;
getattr/read are already allowed. Source14 changes exactly five previously
captured files: CIL adds only open to init_t's existing secret-file read rule,
the closed manager-rights regression changes accordingly, and human host,
security and ADR150 contracts document type-wide opens/reads and safe243/audit
diagnosis with pinned primary references. Every helper grant/neverallow and
all other CIL bytes are unchanged; independent five-case policy review passes.
No new runtime dependency, API/wire change or domain invariant is introduced.

Source14 focused validation passes297 without skips in19.69s. Human documentation
validation passes206 documents and27 helpers. Capture actually passes0 in0.641s,
outer PID3083042/start413920945 reaped/absent. Capture
`.scratch/web-006-source14-capture.json` is28337a7a/684 bytes,1359 ordinary files,
snapshot `487a8a11243d9b20bfe9e5a77dae16c574975790a932d4a1792a5f44e9fe842d`;
inventory199c936c and archive26f5bb6c/17704960 bytes remain separately retained.
CIL is5e343f13/17693 bytes. Source13's before-bytes and strict gate remain
historical evidence. New full strict gate14 actually starts with outer
PID3083141/start413923617 using the captured f308bf51/6619-byte gate runner;
its completion is pending. Freeze all1359 inputs until it finishes; only the
five excluded bookkeeping files may change. Guest remains source13/policy26,
with the exact new native13 failures retained. A fresh source14 protected
transfer/metadata-preservation/staging/policy/authority chain and required
native/rootless/fault/secret/drain acceptance remain pending. Transfer the
actual local6f6bb9139-byte probe as a new protected exact-byte evidence copy;
the no-effect probe created no guest receipt. Do not invent one or replay it.

The local source9-to-source14 application-input comparison actually passes0 in
0.744s, outer PID3087817/start413953210 reaped/absent. Exact-byte result
`.scratch/web-006-source9-to-source14-application-compatibility-v1-result.json`
is `cda6feeaad787649f1c4d66bb2ac003c8407960d9129041876a0f5838f8577ec`,
3485 bytes. Independent actual review7f2bb9f0/6172 bytes joins all1359 file
hashes/modes,108 wheel leaves, both46-input/six-output UI builds,81 image-context
wheels and unchanged pinned UBI10micro recipes. Original source9 artifact9 and
image13 provenance remain intact. This proves application build-input
compatibility only: host deployment compatibility is false, fresh installed
host stages/authority are required, and no gate/functional/full acceptance is
claimed by that comparison. Full gate14 remains running, actual inner
PID3083144/start413923635; its command is
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
transfer is being prepared without entering a bridge scope that depends on its
not-yet-published sixth diagnostic record. No guest source14 change is claimed.

The initial protected source14 transfer then actually passes0 in1.940s, outer
PID3095274/start414021190 reaped/absent. Local
`.scratch/web-006-protected-source14-transfer-v1-result.json` is
`699436e7b77fc17029a6d36c892d75eef5c336ab0952692905fb9609ffb0184e`,
44715 bytes. Frozen guestb950b7b5/28261 bytes and callerf1d380d7/13193 bytes
pass26 owner and26 independent source checks without skips before execution.
All eight fixed metadata queries return0/reaped; current failed API/Caddy
invocations and other11 inactive roles remain exact. Five historical records,
authority10, current selector/configuration and the original key metadata all
rejoin through final FD closure. The actual6f6bb3df/9139-byte diagnostic copy is
now root600/usr_t at
`/opt/hfcache-web006/native-source14-transfer-v1/native13-avc-field-probe-v3-result.json`,
inode118451099, with measured full9/SID and exact-byte readback. The transfer
does not enter the six-record bridge scope before this publication. Guest
RESULT's expected bytes match the original captured SSH stdout
16bcff86/26700 bytes; a subsequent audit must actually capture that leaf before
using its protected identity. Source14 remains unextracted, public source13,
selector/configuration and policy26 remain unchanged; this is preparation only.

Full strict source14 gate then actually passes0 in1246.410743s:
`historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`. Inner
PID3083144/start413923635 and outer3083141/start413923617 are normally
reaped/absent. Exact result `.scratch/web-006-gate14-result.json` is
`ff7ce9883f6fad3bd93b69f11a347c0486c3f2ec45b63a8263f7eddb86af5c68`,
815 bytes; log `.scratch/web-006-gate14.log` is
`ff2c830a5f065711ff5a2c628469f63f4a0a52649f751654791655ca79812672`,
100799 bytes. All1359 captured hashes/modes remain exact. Actual validation:
7732 Python passes/52 explicitly opt-in deselections; all three locked wheel
profiles;572 historical frontend checks; frontend wire/lint/types,21 sandbox metadata and
nine functional-metadata checks;2786 unit and2846 component passes; production
build;two Chromium startup/fallback checks; and the real HTTP/API React read
fixture. Required selected checks are not skipped. These establish the source
gate and its stated local fixtures only. Installed native/rootless real-Caddy,
peer isolation, negatives/faults, credential lifecycle and drain remain pending.
Independent actual transfer reviewc214160b/9230 bytes also confirms the separate
protected source14 transfer; it does not claim installed acceptance. Continue
with the fresh read-only source13-state audit, then preservation and source14
staging/policy27/authority11 before a new original functional generation.

The fresh read-only pre-refresh audit actually passes0 in2.386s, outer
PID3103481/start414060779 reaped/absent. Local
`.scratch/web-006-source13-pre-refresh-audit-v2-result.json` is
`dcc8ea4d41192941dfce97fbcfae5a1472885c187a030132d2691ecd4eacb546`,
55621 bytes; actual protected
`/opt/hfcache-web006/source13-pre-refresh-audit-v2/RESULT.json` is
`e57bd509d26e7eed48dab9c224cf5d8305e26997243a1e7b1c20106830cc0367`,
30088 bytes, root600/usr_t inode127601456. Its initial capture now actually
holds/rejoins transfer RESULT16bcff86/26700 bytes, inode118451112. All16 fixed
queries return0/reaped, source13's1359 public inputs and authority10's108
same-inode read-only package leaves match, current selector/configuration and
key metadata rejoin, and the prep-only bridge closes before receipt publication.
The stopped generation has12 recorded state pairs; its original runner is
separately checked by the bridge's13-pair set. Neither this audit nor that
preparation bridge promotes failed native13 into functional acceptance or
strict post-functional quiescence. Frozen guest4f619f89/73489 bytes and
caller2dc884df/10390 bytes pass91 owner and91 independent source checks without
skips. Bind preservation only to this actual audit's protected record and
measured selector/configuration projection; no new role start has occurred.

The bound preservation actually passes0 in28.271515s, outer
PID3104428/start414090951 reaped/absent. Local
`.scratch/web-006-source14-preservation-v1-result.json` is
`2b730b370fcdf6828c022d0ff146b6f3f17ba2469ffae14386e73b52a12c34e4`,
51592 bytes; actual protected
`/opt/hfcache-web006/source14-stage-preservation-v1/RESULT.json` is
`8024aa1667a84d05f37dc9e5594118f3d1b5dff4faf26aff62267c949f78a92b`,
28731 bytes, root600/usr_t inode4126173. Frozen guest26184194/56265 bytes and
caller7de2a089/10849 bytes pass80 owner and80 independent source checks without
skips. All20 fixed queries return0/reaped; original held inputs, bridge and local
captures close. Source14's1359 ordinary files are extracted privately to
`/opt/hfcache-web006/native-source14`; public source remains13.

Five original names are now actually absent: the current selector, both active
helper configuration names and native/rootless release paths0.2.2/0.2.3. Their
original objects remain, using no-replace moves: selector inode60244071 at
`/opt/hfcache/current.web006-source13-before-source14-v1`; configuration
inodes77965602/77965603 at their `.web006-source13-before-source14-v1.json`
siblings; native inode4135729 and rootless inode127642802 at preservation
`native-source13-release` and `rootless-source13-release`. Bodies, raw selector
target, modes, ownership, labels, tree inventory and original leaf inodes remain
exact; only measured rename ctimes change. Authority10's108 same-inode read-only
package projection is verified after the move. Original helper key metadata,
canonical helper files and loaded policy26 remain unchanged. No installer,
service start, policy refresh, replay or installed acceptance occurs. Resume
from these actual moved objects; never replay preservation. Next is public
source14 update, fresh native/rootless staging, policy27 and authority11.

Public source14 update actually passes0 in1.609805s, outer
PID3105403/start414120431 reaped/absent. Local
`.scratch/web-006-public-source14-update-v1-result.json` is
`152d1eb951805cec8cd6f2d4ae7861720e2da586d046e0b58c3c4f6d7e027ce3`,
46036 bytes; expected protected RESULT8d442015/29317 bytes is reconstructed from
actual producer output, not yet separately held. All1359 public hashes/modes
match source14; all five changed source13 before-bytes/modes are retained.
Nine owned commands return0/reaped, including the UID1000 update child, and all
old held inputs and the prep bridge close. The v3 packet passes22 owner plus22
independent checks without skips. Two earlier inert filename-epoch mismatches
were found by the local full-source rehearsal and retained before guest execution.
No old controller load occurs after the public source change.

Fresh native14 staging then actually passes0 in30.000287s, outer
PID3105776/start414130683 reaped/absent. Local
`.scratch/web-006-native-source14-restage-v1-result.json` is
`0b02184723ed222d9f474827e0702fc691239c1e7160c57499eecba8e6934902`,
54349 bytes; actual protected
`/opt/hfcache-web006/native-restage-source14-v1/RESULT.json` is
`15bdb9b81613c56c06606f2213d9fbb411657ad80c78ebac02372ab7213c1bdb`,
25340 bytes, root600/usr_t inode109848836. Frozen guestf926e5d8/58267 bytes and
caller787dff21/11459 bytes pass75 owner plus75 root source checks without skips.
The original unchanged `install-release.sh --no-switch --with-mcp` child
PID93085/start15014807 returns0/reaped, with108 installed package leaves matching
captured source14. All17 owned commands return0/reaped and stage/bridge/local
input closures pass. Original source9 wheel/UI/image provenance remains intact.

The historical source13 selector now lives at
`/opt/hfcache-web006/native-restage-source14-v1/source13-selector`, still
inode60244071/usr_t/raw target `releases/0.2.2`, moved outside the installer's
original restorecon scope. Both old complete release trees and configuration
backups remain preserved, and authority10's108 read-only projected leaves still
join them. New native14 release is staged at0.2.2; rootless0.2.3, current selector
and active helper configuration names remain absent. Key/canonical helper files
and loaded policy26 remain unchanged. No service start or installed acceptance
is established. Next is rootless14 staging, policy27 and fresh authority11.

Rootless14 staging actually passes0 in3.570073s, outer
PID3107101/start414171662 reaped/absent. Local
`.scratch/web-006-rootless14-input-stage-v1-result.json` is
`dd8052070137e0aaf0473157f244d64e66e2b296a305ecfba94e69f1732bb12f`,
46078 bytes; actual protected wrapper RESULT is6dfb6ae1/37805 bytes,
root600/usr_t inode18632600. Before execution, root found one stale source13
label in the new rootless closure's scope. Fresh v2 changes only that scope to
source14 plus embedded-source/digest/path bindings; frozen v1 remains intact.
Final stage60b01180/75019 bytes, wrapper616e9ee8/112547 bytes and
caller6787283a/10149 bytes pass36 owner plus36 independent checks without skips.

Four fixed renderer inputs and the exact source14 manifest are published under
closed input guards. The original stage/renderer then succeeds, with no image
load or application service start. Wrapper actually captures/rejoins these
root600/usr_t records at `/opt/hfcache-web006/rootless-stage-source14-v1/`:
`staged.json` bfcbadaa/20878 bytes, `input-provenance.json`936f7341/11964 bytes,
and `refresh-closure.json`
`c38d4db3a12e734ef70ff3a0b760419ee4e16afb19f9fb18205c101dc43afdf8`,
32733 bytes. The closure is written after its original held input/key/endpoint
and exact failed-state checks close. Native14 and rootless14 are now staged;
current selector and active helper profile remain absent. Loaded policy26,
the original key and all previous failures/backups/projections remain intact.
Fresh policy27 and authority11 precede the next original functional run.

Policy27 actually passes0 in12.478084s, outer PID3107999/start414202125
reaped/absent. Final guestd0aa9cd0/40394 bytes and caller2da69de8/14590 bytes
pass47 focused binding/ABI/owner/failure checks without skips; root also verifies
their assignment-only final deltas against the independently tested templates.
Local `.scratch/web-006-policy27-refresh-v1-result.json` is
`901effb8ca1d4720c28265b813798ca19dd7ad21610844a1f1dce198471918aa`,
189930 bytes. Actual protected policy RESULT
`/opt/hfcache-web006/policy27-canonical-and-receipt-v1/RESULT.json` is
`9f451aa2507024f092499be4ae0b4fe290fbda65384cc103954e1e5dc7ac5097`,
88287 bytes, root600/usr_t inode60257211; protected collection33af7ba5/118064
bytes also retains the original private channels without replay. All19 commands
return0/reaped and original held inputs/key metadata/prep bridge close.

Loaded module source/checksum is captured CIL5e343f13/17693 bytes. Actual kernel
policy is now
`45bb34e8f897feb344c9b18e895a2d07f8a09a0dc5db41b78331276140a8167f`.
Installed SELinux receipt `/etc/hfcache/host-helper-selinux.json` is
`d0e28181e14ee3a1695e3aecd3788392d1d751bc0166f19ea1cbd7f844553a1e`,
1015 bytes, root644/conf_t inode78232543. Canonical CIL inode78220703 retains
code_t. Original policy26 CIL inode78191533 and receipt inode78204082 remain at
their `.web006-policy26-preserved-v1` sibling names with exact bodies, original
labels/modes/ownership and measured rename ctimes. Six other canonical files,
all label rules, original helper key and selector remain unchanged. No service
starts or failed-state resets occur. This proves policy preparation only;
fresh authority11 and original native/rootless/negative/fault/secret/drain
functional acceptance remain pending. Do not replay policy27 installation.

Authority11 donor transfer actually passes0 in0.510946s, outer
PID3109524/start414252148 reaped/absent. Local donor result iseb73f412/6141 bytes;
actual protected donor RESULT6d428ad8/1672 bytes holds the exact reviewed
32ed74cc source,029fb098 inputs and67ee3b5c controller. Final packet passes75
owner plus75 independent tests without skips before execution.

The one original authority11 preparation then fails1 in4.700765s, outer
PID3109669/start414257390 reaped/absent. Local
`.scratch/web-006-authority11-source14-v1-result.json` is
`bab2322f44833d14d3e783e2efa5cfc463c89097f63732ba6458d1cb744429ee`,
16396 bytes. Safe protected collection
`/opt/hfcache-web006/authority11-safe-caller-v1/RESULT.json` is
`f0d765b37146e9c743ea908f14fecc3f8d50cbebe16268adc31646444243b738`,
8558 bytes, root600/usr_t inode10018617. It records inner OSError, resultnull
and no authority result record. All17 original commands return0/reaped, donor
FDs close and no application roles start. Outer ValueError and failed local
closure flag are retained honestly; readiness and successful preparation are
not established. Exact private stderr3dbcd1ee/1816 bytes and stdoutc1339068/
6243 bytes remain captured at their original paths/inodes. Current partial
publication, exact errno and failure phase are unproved pending a fresh bounded
read-only getter. Preserve every partial object; do not replay authority11,
infer a cause from OSError alone or bind functional readiness to this failure.

The fresh read-only failure getter actually passes0 in0.447135s, outer
PID3112253/start414353688 reaped/absent. Local
`.scratch/web-006-authority11-failure-getter-v1-result.json` is
`a9535251501af0f8fcba8593801fc2b70be96d2f1996f3776f066d73fc45158c`,
17214 bytes. Frozen guest868d980b/24053 bytes and caller49701e41/10717 bytes
pass19 owner plus19 independent preparation checks without skips. Independent
preparation receipt5788a02b/2367 bytes records the full source review.

The closed retained stderr classifies errno24 (EMFILE). Its deepest authority
frame is `parent_fd` line134, reached through current-authority10 projection
line1612, capture line1795 and preparation line2037. This locates the failed
descriptor acquisition while preserving the original failure; the original
process's exact resource limits were not recorded and remain unknown. All28
fixed publication/selection/configuration paths are absent or have absent
ancestors, including authority11, controller12 control/generations, sudoers11,
public11, current and both active helper configuration names. No new readiness
or functional authority exists. The getter holds/rejoins/closes the original
collection, both private channels and all three donor records; all eight local
captures and the exact QEMU/SSH ownership checks also close. The one SSH child
PID3112254/start414353694 returns0/reaped. Original17 command records and
failed/null/no-role-start flags remain unchanged. No guest mutation, process
action, source replay, raw stderr publication or key-body/digest read occurs.

The next preparation must use a fresh scope and retain authority11's failure.
Inspect the current collector resource limits and review a finite evidence-
collection descriptor budget before changing the disposable harness. Do not
change application/helper/service hardening or infer successful installed
acceptance from that harness correction. Required native/rootless UI,
negative/fault, exact-ID secret lifecycle and strict drain proofs remain pending.

The separate read-only current-resource getter actually passes0 in0.420141s,
outer PID3114480/start414427456 reaped/absent. Local
`.scratch/web-006-authority11-current-resource-getter-v1-result.json` is
`f53d7693b82e5e7ad4d58ad72bbc4f767f64101cf2ab0eeee9e432c8d2b963c5`,
4413 bytes. Frozen guest55bbf4df/7732 bytes and callerc332a5b6/10088 bytes
pass54 owner,54 root and54 independent source checks without skips. The source
check2807bc1d/2942 bytes and actual independent review099430ca/3199 bytes are
retained. New sudo Python PID93555/start15310898 measures soft1024/hard524288,
rechecked unchanged; its descriptor observation lists4 entries, verifies3 open
and observes1 already closed enumeration entry. The snapshot is explicitly
non-atomic and reads no descriptor link targets. Numeric system ceilings are
nr_open1073741816 and file_max9223372036854775807. SSH child
PID3114481/start414427462 returns0/reaped, with all five local captures and exact
QEMU ownership checks closed. No limits, guest state or kernel policy change;
the failed authority11 process's limits and exact FD count remain unknown.

Independent source counts locate1099 retained authority descriptors before
WORK creation, plus eight collector descriptors; persistent peak is entry
baseline plus1121. Fresh12's additional failed11 guards fit a conservative
1280-descriptor reserve plus64 transient slots. Review9951150d/4659 bytes
records the ancestor-retention correction. The new disposable collector targets
a finite2048 soft limit within its unchanged existing hard ceiling, then checks
FD closure/reaping and restores its exact original tuple before reporting.
Only fixed preparation queries/validator children inherit that temporary limit;
application/helper/service limits and later functional callers are separate.
Fresh authority12/controller13 paths and locally generated planned UUID
5f414528-e498-4c42-b7fe-9d3302817d71 are being reviewed, not measured readiness.
Controller13 differs from12 in exactly the control/generation path assignments;
all function bodies remain unchanged. Prior failures, source14's1359 hashes/
modes and full strict source gate remain intact. Bookkeeping checks pass9/0
skips and diff whitespace checks pass. All installed feature acceptance remains
pending. These preparation checks do not complete WEB-006 or select its
successor.

Fresh authority12 donor transfer actually passes0 in0.488306s, outer
PID3116862/start414502289 reaped/absent. Local
`.scratch/web-006-authority12-donors-v1-result.json` is
`f06efaf70685432747f94f2dc897b315408582f8523ab7745cbbbcd50386ae8c`,
7331 bytes. Frozen guest2f6b3494/17400 bytes, calleree244083/10054 bytes and
tar6fc7786f/317440 bytes pass24 owner checks and independent full-source/binding
review. Actual protected donor RESULT935f02cd/2593 bytes is root600/usr_t
inode18634230. Four exact ordinary root600 members are source758a2a45/157875,
inputs6df11919/41437, controller23764d51/92521 and copied local actual failed11
readbacka9535251/17214 bytes; none is an invented original guest readback
receipt. Local captures and all held historical inputs/key metadata close.
Independent actual reviewbc055d2f/5376 bytes confirms the source-defined
classifier, exact protected receipt and owned SSH3116863/start414502295
return0/reaped. No authority or service execution occurs during this transfer.

The one original authority12 preparation then actually passes0 in10.438318s,
outer PID3116908/start414503578 reaped/absent. Local
`.scratch/web-006-authority12-source14-v1-result.json` is
`7d4b17b771f65329610d781f353662d4e8e6893386df1b1670271d9bfbbca75b`,
806669 bytes. Actual protected `/opt/hfcache-web006/fixture-authority-v12/RESULT.json`
is `eaa91a3a949fbd4d20322a1ddc250be4832030a847f9e8fc53b959f2f65d51bd`,
665202 bytes, root600/usr_t inode34930188. Safe protected collection1753376f/
501277 bytes is root600/usr_t inode27298060. Final source758a2a45 and safe
callerb346eb15/25005 bytes pass47 owner checks without skips; final source differs
from the reviewed template only in its input digest binding. Independent
final-packet reviewbbefbd66/3986 bytes and sourcecheck0d2f089a/5439 bytes remain
retained. One test-only missing import was corrected without packet changes;
the earlier failed test XML remains preserved.

All45 preparation commands return0/reaped. The unchanged original installed
validator PID93713/start15387720 passes, and controller load equality passes.
Actual UUID is5f414528-e498-4c42-b7fe-9d3302817d71; controller13 has only the two
reviewed control/generation path changes. Control13 digest is
129833cd8040d592b7c2e7abb7404118aa57049e7777253cd333487c60fecf9a;
public manifest12 is202e8d0c090ee0b289d7f9eb1fece33d1f6b462ca0859c10eaa1a4fefd6f970d;
runner launcher isaa432e9a7a2d2013d4e72d4742bbc0f2dde120f3f42299dfb93c9c1f5304251d.
Failed11's original report/channels/donors and copied local readback rejoin and
close; all28 failed11 publication/selection paths are absent before and after,
and its original17 owned PID/start pairs are gone. Prior successful/partial
authorities, projections, selector/configuration backups and key metadata are
preserved. Native13 BLOCKED's107 bytes and82a3192e digest are now actually
captured and copied to protected history, with its original inode left intact.

The collector measures baseline3/maxFD2 and soft1024/hard524288, uses soft2048
with the hard limit unchanged, then restores soft1024/hard524288 exactly after
all owned descriptors/children close. Descriptor identity set and reaping
checks pass; restoration has no error. All four donor closures and local
captures pass. No application/helper role starts, configuration selection or
installed feature acceptance is claimed. Native14 functional binding/review is
next, followed by rootless, negative/fault, exact-ID secret lifecycle and strict
drain proofs. Do not replay this successful preparation or the failed11 run.

The one original native14/authority12 functional attempt actually fails1 in
6.909970s, outer PID3117756/start414532306 reaped/absent. Local
`.scratch/web-006-original-native-functional-source14-authority12-v1-result.json`
is `d98054aae267548e5be48015a9ce8ae5b51c0aeb0434d97e8f28902066193c27`,
79704 bytes. Frozen guest6f72e6aa/77680 bytes and caller3c105e16/14967 bytes
pass9 focused binding/producer checks without skips, sourcecheckc6f28fb5/4272
bytes. Their functions are unchanged from the reviewed inert templates: only
four actual readiness digest assignments and the local remote-source pin bind.

Protected native RESULT is76948df14dc1ebd0a6f7642061e06fa174567cc6ad7bd6c5936e91b556a28121,
55322 bytes, root600/usr_t inode127648843. Safe protected collection is
cd5baee498a3a0cc5086909268ccbbdeb6ffb16b0f4bb145655dc5294e42f105,
68389 bytes, root600/usr_t inode118497357. Native inner error is null and guest
input closure passes, but functional_passed is false, original_summary_exists
is false and the runner PID93800/start15415837 returns1/reaped after5.313045s.
All17 commands are reaped; the other16 return0. The wrapper reports fixed roles
quiescent after execution, which does not establish functional acceptance or
the exact generation/role startup outcomes. The runner's original62-byte
stderr286fbc7a and empty stdout remain at protected command-14 channels.
Outer ValueError and failed local acceptance/closure flag are retained honestly.

Preserve this failure and do not replay its runner or infer the same cause as
native13. Its new generation, current selection/configuration state, actual
role invocations, readiness and failure cause await a fresh bounded read-only
getter. Historical native13 states embedded in the preparation proof are not
new native14 observations. Rootless, negatives/faults, exact-ID secret lifecycle
and strict drain acceptance remain pending; no WEB-006 completion or commit.

The new native14 read-only readback actually passes0 in0.709690s, outer
PID3118879/start414568031 reaped/absent. Local
`.scratch/web-006-native-source14-authority12-failure-readback-v1-result.json`
is `9af701b1c1e7d8f7d304ca75113e8a80a0a1e437fe13505e0255e40a9d361487`,
37132 bytes. Frozen guest12ab8060/29277 bytes and callerc4443de1/10515 bytes
pass8 owner plus8 independent tests without skips, sourcecheck0bc2b759/3296
and independent reviewb360ecf5/2550 bytes. Two fixed metadata query children
93997/start15451479 and93998/start15451495 return0/reaped; held original
receipts, projected state/public records and all eight local inputs close.

Actual generation is5dbe71c20b10433db292dec4ec3403f3. Protected state23c440ab/
11953 bytes at generations13 is root600/usr_t inode52243915. Started/stopped
are true, paused false, READY count0, recorded cgroup count1 and container
count0. All13 recorded PID/start pairs have numeric PIDs absent. The cgroup
count is historical ownership evidence, not a new observation of that directory's
closure. The only saved secret gate is originals-before-helper:8 objects pass
under kernel45bb34e8/sequence47 with actual_inode_denial_proven and
policy_reload_atomic still false. Delivered-before-bootstrap was not reached.
Public RESULTd28239e4/2125 bytes retains cleanup_unknown true, no READY and
no start response; stop responsee72dd2bf/2104 bytes remains. SUMMARY is absent
and BLOCKED107-byte metadata remains; no outcome is promoted to acceptance.

All13 current fixed system/user unit rows are inactive with zero Main/Control
PIDs, empty cgroups and empty invocation/ExecMainPID metadata. Those current
fields do not establish historical startup outcomes. The native relative
selector is present at inode60257212/usr_t; active deployment/policy files are
present at root-owned conf_t inodes78232550/78232551. Original helper key's full
metadata/SID remains unchanged at inode78157344; its body/digest is unread.
Preserve these selected/configuration objects. The readback writes only its
new owned diagnostic directory/channels/receipt and performs no role action,
controller call, replay or kernel-policy change. Its expected protected
RESULTc7da48dd/30387 bytes is reconstructed from actual producer output, not
yet separately held. A new bounded original-window journal diagnostic is next
to establish the failure phase/cause without inferring it from current unit
metadata. Required installed acceptance remains incomplete.

The first original-window journal diagnostic (v4 source) actually fails1 in
0.745298s, outer PID3121887/start414670068 reaped/absent. Local
`.scratch/web-006-native-source14-authority12-startup-journal-v4-result.json`
is `fd269e46a389c8b03410a402d923cdf1e6a2a16bb882624865d699cd92438665`,
10778 bytes. Frozen guest0e7016b8/49441 bytes and caller8bbb81bc/11506 bytes
pass18 owner checks, independent19 combined checks and the real combined-error
regression without skips. Sourcecheck7d582359/6778 bytes and independent
reviews9db8f568/2606 and59f60c7e/3607 bytes are retained. Earlier unexecuted
draft tests caught a missing ninth local capture and an error-ordering issue;
their failed XMLs and all draft files remain intact. Final ownership, source,
privacy, window and producer/consumer checks pass before the actual call.

The actual diagnostic records ValueError at journal-helper. Two current unit
queries94057/start15553514 and94058/start15553531 return0/reaped; the first
journal query94060/start15553536 returns1/reaped, stdout0 and stderr71 bytes
with digest15da4cd3561efa04d7d6a6b1d670d60fab8828442cb372b06a74b74ffc7c3f45.
All three children drain/reap. New raw channels are labeled/verified secret_t
before bytes, including the retained query error. The original WORK path
`/opt/hfcache-web006/native-source14-authority12-startup-journal-v1` now exists
and must not be replayed or reused. No original native/controller/service
action or kernel-policy change occurs. Failed local closure and diagnostic
held-input-finalization flags remain false. Native startup cause is still
unknown; classify the retained query error before a fresh bounded diagnostic.
Do not infer a journal argument error from its length or exit code alone.

Static classification subsequently establishes the diagnostic's CLI refusal:
the known public boot-descriptor error line is exactly71 bytes and its SHA256
equals15da4cd3. The pinned systemd257 parser expects32 hexadecimal characters;
the diagnostic supplied the same boot identity with hyphens. Primary-source
receiptsc27d60ae/1251 and96d3f5f0/2241 bytes are retained. This identifies only
the diagnostic error, not the native functional failure. Fresh v5 normalizes
only the journalctl argument to the compact form; its actual guest BOOT guard
keeps the original identity. It uses a fresh WORKv2 and holds/rejoins the failed
v1 receipt and protected stderr, preserving that false closure flag.

The fresh journal diagnostic actually passes0 in1.033527s, outer
PID3123136/start414713529 reaped/absent. Local
`.scratch/web-006-native-source14-authority12-startup-journal-v5-result.json`
is `4c31275cd98ef9e59ee7e2a817ff911a2c79e64108edb19a12dbf87bff786fb4`,
106957 bytes. Frozen guestb0059f7c/51031 bytes and caller06c05dc3/11642 bytes
pass21 owner,22 independent combined and21 additional independent checks
without skips. Sourcecheck44bc6a41/8583 and independent reviewsb66bf4cf/3249
and2c97a37e/2206 bytes remain. All nine query children94099,94100,94102–94108
return0/reaped with known positive start identities; all nine local captures
and held guest inputs close. Current13 fixed unit metadata stays equal before
and after. All new raw channels are verified secret_t before bytes.

Actual held prior diagnostic RESULT170edb6c/5002 bytes is root600/usr_t
inode10012033; actual71-byte error15da4cd3 is root600/secret_t inode10012032.
The earlier readback RESULTc7da48dd/30387 bytes is now actually held/rejoined at
root600/usr_t inode4187493. No original result, channel, key or selected
configuration is changed. The new journal captures6 helper and4 each API,
worker and Caddy manager events with original start/stop job-done records and
their exact invocation IDs. It captures no child error/traceback or original
API UID/GID. The sole saved cgroup is the API unit; it remains ownership
evidence, not a current-directory closure or sustained-health proof. Ten
helper-context AVC rows have no established causal join to the refusal and
retain false attribution flags; do not grant permissions from those rows.

The failure's exact cause remains unproved. Source ordering plus the observed
immediate API process inspection motivates reviewing a bounded observation
wait for native Type=simple setup, with every original principal/namespace/
isolation check retained and typed refused-attempt metadata added. The original
API UID/GID and failure outcome remain unknown/failed. Any future test uses a
fresh scope and preserves all original evidence; no native replay, product
policy/hardening change or installed acceptance follows this diagnostic pass.

Source-only follow-up at2026-10-22T14:44Z confirms a fresh minimal authority13
can reuse authority12's protected profile/input records and its original
read-only108-leaf package projection. Both runner and installed validator must
explicitly retain the old projection's PYTHONPATH; marker/browser/controller/
manifest/control identities are fresh. No release install, new mount layer,
application rebuild or policy change is required. Independent feasibility
receiptb57e862f/8749 bytes records the exact prerequisites. Planned UUID
2ba4133c-5d8f-4764-aadb-03eab554cab1 is locally generated preparation metadata,
not an observed guest identity. Current selection/configuration preservation
and fresh cgroup/endpoint drain proofs remain unperformed at this checkpoint.

Native-only principal-observation preflightv3 is frozen239e9ebe/7332 bytes,
with35 model checks passing without skips. It pins/tracks the first original
PID/start/invocation cohort, observes only startup-shaped root-to-fixed-account
transitions within a finite observation budget, then runs the unchanged full
cohort/security validator once and joins every original handle. It does not
retry failed security checks or establish the old failure's cause. Original
full-validation and owned drain budgets remain separate. Controller14's
candidate integration5c9eff4f/98835 bytes awaits its independent integrated
checks; neither method nor controller has run in the guest.

The new three-donor transfer and safe collector templates pass21 combined
owned-local-file tests, zero skips,2.56s, XML
`.scratch/web-006-authority13-caller-templates-owner-v1.xml`; source lint passes.
Independent donor10 checks also pass. Collectorv3's actual local ABI tests first
failed4/passed7 before any guest execution; the retained failed XML identified
an unadapted three-value donor capture. Fresh v4 fixes that site and passes11
local collector checks in1.41s. The final inert caller template isd61c3852/
22222 bytes. New raw channels receive verified secret_t before bytes, including
label-error descriptor closure. All old drafts/results remain retained. All1359
frozen source14 hashes/modes still match the passed strict gate. No installed
acceptance case is promoted and no WEB-006 commit is authorized by these passes.

Fresh13 core/controller/input bindings are now frozen and tested. Integrated
controller14 passes38 checks without skips,1.76s, independent receiptf8876902/
3132 bytes; the only original method change is the native delivered-gate call,
alongside the exact added preflight and CONTROL/GEN14 paths. Core template7f73f46c/
49572 bytes adds preserved fixed-host bindings and held canonical policy27
seven files/receipt;36 core checks pass without skips,2.66s, sourcecheckbf80828a/
3136 bytes. Final core01dbf210/49631 bytes binds only inputSHAf1d4000c/1858.
Final tar269c2c9d/153600 bytes, donorb37c4c15/17358, transfer0687ebee/9456 and
safe caller14004c5b/22340 pass14 owner plus14 independent actual local producer/
consumer checks without skips; independent receiptb199cb3f/4148 bytes. These
remain local models, distinct from the following actual guest results.

The one actual three-donor transfer passes0 in0.491357s, outer
PID3132355/start414966726 reaped/absent. Local
`.scratch/web-006-authority13-donors-v1-result.json` is37d58adcb6700d287ef3d5d07f67b50e5bf78e3b087e9a6db0531861f3392e3f,
6140 bytes; protected RESULT758624ae/1670 bytes is root600/usr_t inode27298065.
Source/controller/input bodies match actual held donor inodes27298064/27298063/
43341950. All local/guest closures pass; no authority executes during transfer.

The one actual fresh authority13 preparation then passes0 in4.882084s, outer
PID3132440/start414968685 reaped/absent. Local
`.scratch/web-006-authority13-source14-v1-result.json` isfbd80e75c905d4870a7b18c7d538abfd1064cb5d9e2d61afd1e17a82745344d4,
189443 bytes. Protected RESULT416e865edafdac39357c34c940c35c580813dabb41040a49029ab239f4816d19,
151590 bytes, is root600/usr_t inode43348869. Safe collection0a184ff0/117611
bytes is root600/usr_t inode34930192. All six fixed commands94217/15852276,
94218/15852292,94220/15852308,94221/15852318,94223/15852408 and94224/15852421
return0/reaped. Original installed validator and controller load equality pass;
all protected/local/donor captures close. Temporary collector soft2048 restores
exactly to1024 with hard524288 unchanged and descriptor identity set restored.

Actual UUID is2ba4133c-5d8f-4764-aadb-03eab554cab1; control14 is3ca5236658333cd1639ad8492dcb9c88c39fa0c55539ed45732361d57432b3a1,
manifest13 is50be66391fe7d25fcf3afa26580de211cf630a8dd0b8b2a178811b27bbe9b3be.
Runner's unchanged bytes retainaa432e9a at their new13 path with explicit old12
projection PYTHONPATH. Before/after13-unit/PID, original API cgroup and five
endpoint drain checks pass. Selector60257212 and config78232550/78232551 are
moved once without replacement to fixture-authority-v13/native14-{selector,
deployment.json,policy.json}; same inode/body/target/SID/mode is retained, with
measured owned rename ctime transitions. Their three canonical names are now
actually absent. Releases, old authorities, package projection, key, canonical
policy27/receipt, kernel45bb and fixed host bindings stay unchanged. No role
starts or feature acceptance follows. This successful preparation must not be
replayed; bind the fresh native run to its actual measured readiness hashes.

Fresh native authority13 templates e14e33a6/24953 and11763035/17123 pass41
local checks without skips, including actual dual-pipe drain/reap, label-entry
and duplicated-FD adoption failures. Historical native13 failed-state admission
is removed from the fresh scope; strict current preparation and schema2 replace
it. The first bound caller's local suite correctly fails2/passes41 because
REMOTE still names the inert template while its hash names the bound guest.
No guest call occurs. Preserve that caller8d50654f and failed XML; fresh caller
V2b050d9e1/17173 changes only REMOTE and its new local RESULT path. Guest
a3fd9825/25181 binds only four measured authority13 readiness constants. Its
43 bound checks pass without skips,2.29s, sourcecheck15778c7e/2897 bytes;
independent41 security plus3 actual bound-path/capture tests pass, review
c648bce4/3790 bytes. Original functional checker and strict postchecks remain.

The one actual fresh native13-authority run then fails1 in7.355184s, outer
PID3135129/start415008891 reaped/absent. Local
`.scratch/web-006-original-native-functional-source14-authority13-v2-result.json`
is104e6b9f019d9ab346f846757c49287fbcb4960eb1c80caca3465e36b406b5d5,
21799 bytes. Protected native RESULT3b9618fed2787407e11be67421442b40ee2c3d860623dafa9ff5ec168aa4088f,
11482 bytes, is root600/usr_t inode78232570. Safe collection347a485f/16474
bytes is root600/usr_t inode78232571. All five commands94271/15892330,
94272/15892343,94274/15892348,94420/15892984 and94421/15892997 reap; the original
runner94274 returns1 after6.348786s and the other four return0. Known fixed
62-byte refusal stderr286fbc7a remains protected secret_t; all new raw channels
were labeled before bytes. No raw body is published.

Inner native error is null and held-input closure is true, but functional_passed
is false and the original SUMMARY is absent. Original9-app-role postquiescence
passes; separate strict13-role/handle/cgroup/endpoint closure is not inferred.
The outer classifier records ValueError/local-closure false honestly. Preserve
this original failed runner and do not replay. Its actual GEN14 identity,
startup-preflight phase/observations, secret gates and current selection state
await a new bounded read-only getter. Neither the previous native14 cause nor
this new failure's cause is proved. Required installed acceptance remains open;
inert rootless prerequisites must reject this failed result as native readiness.

The fresh post-run getter passes30 owner plus30 independent local checks with
no skips. Review caught active-socket connect probes that could activate a
service; three local regression cases were red before the fix and remain
retained. Final0914b52f/38367-byte guest and0bcf1809/12912-byte caller only
probe endpoints after strict13-role/original-handle/fixed-cgroup closure. Known
live state produces typed deferred observations and false closure, never a
functional acceptance waiver. Sourcecheck890a65a6/3689 and review10f075ef/3776
bytes record the exact bindings, eight held local inputs and generated source.

The one actual readback passes0 in0.736605s, outer3138816/start415105332
reaped/absent. Local
`.scratch/web-006-native-source14-authority13-post-run-v1-result.json`
is02ba05a786edf7a861ceda58ecae55b3df5a204154263f9652192f93d6e62690,
42806 bytes. Query children94485/start15988766 and94486/start15988783 return0/
reaped. All eight local and protected guest captures close. Expected protected
RESULT is37117af656222bc9f3babeec4bf20cb8628a18c15f0772419e0c23b8aeff7dda,
35420 bytes at native-source14-authority13-post-run-v1/RESULT.json, derived from
the actual producer serializer; its inode/SID is not independently held yet.
Independent actual audit5fb00d21/1998 bytes passes without promoting the failure.

Actual generation is4fd7b1b48572405087661be462e749a6. State5c68cc8fe881e45b8ddf7bc1d27d482fc813aa8f3ab9cecdb51583124c2aeb5c,
20921 bytes, is root600/usr_t inode60275484. Started/stopped are true, paused
false, READY0 and container0. The new preflight passes all four exact original
principals without retry in418092886ns, including unchanged complete cohort
and final PID/start/invocation/cgroup joins. Original8-object and native
delivered2-object secret gates both pass under kernel45bb/sequence47. Their
actual_inode_denial_proven and policy_reload_atomic flags remain false. These
facts narrow the failure after the credential gates; they do not identify the
later refusing predicate or explain the earlier native14 failure.

All13 fixed units are inactive. All20 state-owned and five original wrapper
PID/start pairs have numeric PIDs absent; all four fixed cgroups are physically
absent, and all five endpoints explicitly refuse connections. Strict post-run
closure is true. The current native selector/configs are present at new inodes
60257213/78232562/78232563; metadata only is captured. Original key metadata/SID
remains exact. Preserve these new leaves before any later activation, alongside
all old native14 backups. No service action, controller call, policy change or
replay occurs. A separate narrow state/static-helper-unit supplement is next to
inspect saved bootstrap/security-stage metadata omitted by this projection;
current static unit settings alone are not original live-process evidence.

Supplemental saved-state/static-helper readback actually passes0 in0.568727s,
outer3142834/start415215381 reaped/absent. Local
`.scratch/web-006-native-source14-authority13-post-run-v2-result.json`
isc4b2af541e2bd2359b583530f10735d220e8d82cffd56eb1285c10c8a3fdc817,
15298 bytes. The sole fixed metadata query94555/start16098812 returns0/reaped;
all seven local and protected captures close. Prior postRESULT37117af6/35420 is
now actually held at root600/usr_t inode94391441. The new supplement's protected
RESULT863527f1/10337 remains serializer-derived expected-only until first held.
Independent actual/source review036f1930/7021 records the joins and limitations.

Saved instance_id is absent; helper-applied/namespace/peer/hygiene proof counts
are all zero. All seven current static helper settings match their contract;
these are not retrospective live-process proof. Guest /usr/bin/python3 is
CPython3.12.15 and HTTPSConnection lacks __enter__/__exit__; no connection is
created by that ABI observation. Controller14's exact bootstrap method locally
raises TypeError before a request on real Python3.12.13 and3.14.6. This identifies
a concrete harness defect consistent with the saved stage, without claiming the
original traceback was observed or explaining the older native14 failure.

Frozen controller15 is `.scratch/web-006-fixed-controller-v15.py`,
SHA4d1947d960cdf8eb2c1dabb528aabc9e2aee5262eb4700c314b5b6d0ee24b1ff,
99181 bytes. Only control/generation epoch paths and explicit bootstrap connection
ownership differ from14. TLS/auth/request/status/size/schema checks and principal
preflight remain exact. Primary exceptions survive close failures. All51 owner
integration checks and17 independent close checks pass without skips;
sourcecheckf12f4ed0/2734 records the complete delta. Fresh authority14 is being
prepared with controller15, unchanged protected profiles/RO108 installation and
same-inode preservation of current three native leaves. Neither that preparation
nor these local tests establish functional acceptance. Source14 remains frozen;
all failed scopes, original outcomes and inert rootless drafts are retained.

Fresh authority14 preparation actually passes0 in4.352056s, outer3146572/
start415341730 reaped/absent. Its preceding three-donor transfer passes0 in
0.480385s, outer3146174/start415329342 reaped/absent. Local donor receipt
`.scratch/web-006-authority14-donors-v1-result.json` is33fda5e4/6142 bytes;
protected transfer e78b8706/1672 is root600/usr_t inode109855912. Exactly core
91fccb5a/55858, inputf65816f6/2239 and controller4d1947d9/99181 are transferred.
All held input joins close. No authority or application runs during transfer.

Local preparation `.scratch/web-006-authority14-source14-v2-result.json` is
46a124afefbbe1c6e5e32e6c7bd44d0924112ceafc148949f929680ed162e25a,
202152 bytes. Protected authority RESULTa9ff0128c0ad4163167c775ff75a69fe0e65e6335e43823fc565314e0b064ccb,
162231 bytes, is root600/usr_t inode127648848. Safe collection7f0da459/125075
is inode118497361. Six commands94643/16225290,94644/16225305,94646/16225321,
94647/16225330,94649/16225413 and94650/16225427 return0/reaped. Original
installed validator94647 and exact controller load pass. Collector soft2048
restores to1024, hard524288 unchanged, with the exact descriptor set restored.

UUID is62a5ab9a-8812-4a57-9d5b-a12149e2d9cb. Control15 is864d706d916ad6f0045a8ac2f818c63a40ad7a2f7700603c8c4d54f4fad86cd1;
manifest14 isfdc6cc836687ae9db1886b295c8e7d88ff4c61ef33184d9a09bdc44b163e50b9.
Runneraa432e9a retains original bytes and explicit PUBLIC12/installed PYTHONPATH.
All58 original protected root records and the existing RO108 projection remain.
All three current native selector/configuration inodes60257213/78232562/78232563
are moved once without replacement to fixture-authority-v14/native14-authority13-
{selector,deployment.json,policy.json}; only measured owned rename ctimes change.
Canonical names are actually absent. Before/after strict13-role,20state+5wrapper
original-handle,4cgroup and5endpoint closure passes. Key, canonical policy27,
kernel45bb, release trees, image/source provenance and fixed bindings stay exact.
Prior supplement863527f1/10337 is now first actually held at inode101728634.
Independent actual review13a7836b/5987 records the complete joins.

Preparation core passes43 owner and60 independent local tests. Review's two
real108-file inode/mtime refusal regressions first failed and then pass after
requiring full historical row equality. Final packet passes26 owner plus21
independent tests; sourcechecke6a2726d/4750 and reviewf94965f8/4581 retain exact
bindings. A stale-draft controller-hash warning was withdrawn after all three
reviewers execute the frozen core's actual bound_configuration/validate_inputs;
both hashes were already correct, no V2 core or guest correction was needed.
Safe callerV272583fd4/22354 binds only the actual donor receipt and fresh local
RESULT path; independent three real-five-FD caller tests pass. Native functional
binding is next. This successful preparation must not be replayed and establishes
no feature acceptance; all earlier native failures and rootless holds remain.

Fresh native14 binding passes43 owner and43 independent tests without skips;
guest17f7f1a3/25204 changes only four measured preparation hashes and caller
94a8d7ca/17196 changes only its remote pin and explicit bound-guest path. The
first bound test copy has one stale manifest13 expectation (1failed/42passed),
preserved with its XML; the fresh test copy corrects that literal, no source
change. Independent binding review04db0c99/2147 records the exact joins.

The one actual native14 run fails1 in99.341861s, outer3147215/start415362045
reaped/absent. Local
`.scratch/web-006-original-native-functional-source14-authority14-v1-result.json`
isd238ae6445f6d2d495ba334fc43dfcc45ed3e3869b18c16217ee02b0b0d96ffb,
21823 bytes. Protected native RESULT64145353166c3b0995169ea874842d871553b1ef9e7afca548c3499a620a656b,
11505 bytes, is root600/usr_t inode18615185. Safe collection8195905c/16497 is
inode10010505. Original runner94687/start16245490 returns1/reaped after98.345710s;
the other four commands94684/16245472,94685/16245484,95052/16255325 and95053/
16255338 return0/reaped. The same known62-byte refusal remains protected, with
all raw channels labeled secret_t before bytes; no raw body is published.

Inner native error is null and held-input closure true. Functionalfalse/noSUMMARY
remain unchanged, original9-app-role quiescence passes, and the outer classifier
honestly records ValueError/localclosurefalse. The new generation/stage and
separate strict13-role/original-handle/cgroup/endpoint closure are unobserved
until the bounded read-only successor runs. No cause is inferred from elapsed
time or the earlier bootstrap fix. Preserve this failed scope without replay.
Fresh rootless14's57 passing source-only tests and privacy/actual-hygiene schema
review remain prototype evidence; all operational pins stay unbound and those
templates are now permanently inert against native14's failed prerequisite.
Native/rootless/adversarial/fault/secret acceptance and WEB006 completion remain
open; no successor work package is selected.

The fresh native14 post-readback passes0 in0.699658s, outer3149089/
start415416805 reaped/absent. Local
`.scratch/web-006-native-source14-authority14-post-run-v1-result.json`
is9d5fdafaf80ffcbc12f2bf50bdb1d60931d83799c5b8ad6c279e2aec554ff430,
44163 bytes. Queries95090/16300226 and95091/16300241 return0/reaped; all eight
local and protected input captures close. Bound guestcc43f38d/44076 and caller
ba2d95a3/18536 pass34 owner checks, Ruff and three independent actual producer/
consumer checks. A missing import re in the unfrozen caller draft produced13
local failures and is fixed before binding; those original failures remain.
Sourcecheck1134789e/8049 records the exact source, closed captures and limits.

Actual GEN15 is163cb2615903472cbfd9234ebfb5d224. Protected state91026ecc2a9da1cab7262acd1ea5c0a9420577980aa556eb1de77f17ac09f573,
20921 bytes, is root600/usr_t inode4187502. Principal preflight/cohort passes
all4 expected principals without retry in383116891ns. Original8 and native
delivered2 credential gates pass with kernel45bb unchanged. instance_id is absent;
READY0 and all helper-applied/namespace/peer/hygiene counts0 locate the saved
stage before bootstrap success, without proving the original exception or cause.
All13 units are inactive,20 state-owned plus5 wrapper numeric PIDs absent,
all4 cgroups physically absent and5 endpoints refused. Strict closure is true.
Key metadata stays exact. Current native selector/configuration leaves are now
inodes60257214/78232572/78232573; metadata only is captured, and they must be
preserved before any future activation. Expected new protected postRESULT is
105a3cb3f1c5b3479f4b4dc2ff9b26241a5b737bf9aa5ee8dcf8c7c590fa103c,
36581 bytes, serializer-derived until first actually held. A bounded original-
invocation journal query is next; no role action, policy change or replay occurs.

The one bounded original-invocation journal read passes0 in1.049749s, outer
3150751/start415469687 reaped/absent. Local
`.scratch/web-006-native-source14-authority14-startup-journal-v1-result.json`
is0e8e0faea8e867be6980134b6ed06349f14173385c44d453538ff07e22d021c3,
115814 bytes. Final guest70dc4d7c/53275 and caller11c71227/17655 pass16 owner
plus12 independent checks, all28 without skips. Sourcecheckddaa900d/5273 and
independent0a770098/8137 bind four original unit/invocation IDs, compact boot,
103s original UTC window and nine held local inputs. Earlier unfrozen missing-
errno and stale module-scope strings are fixed before execution, no feature change.

All eight command children95128/16353107,95129/16353126,95131/16353131,
95132/16353133,95133/16353136,95134/16353138,95135/16353140 and95136/16353156
return0/reaped. Sixteen raw channels have exact byte/hash joins and secret_t
labels before bytes. No audit query, kernel-policy read/change, role action or
runner/controller replay occurs. Before/after13-unit rows are equal; key and
three current leaves stay exact. Prior postRESULT105a3cb3/36581 is now actually
held at root600/usr_t inode78204035. The new journal RESULT35ec862b3e01763c7998f7a3a84a379b5e84585f4a0e82e21d557fd0882f954c,
104341 bytes, remains serializer-derived until first actual hold. Independent
actual review8c2f6570/4310 verifies the complete joins.

The actual API invocation includes its original PID94791, UID/GID983 actor row
and a subsequent manager exit status10,5.358977s after start JOB completion.
No HTTP status or exception class appears in the current closed projection;
this does not identify the configuration/credential reason. Helper/worker/Caddy
rows retain their original start/stop observations. A new narrow parser will
inspect only the already retained API raw channel through exact source-defined
error templates/codes, with unknown message text omitted. No journal or service
replay is needed. An independent local source API/Basic serializer to real TLS
to exact controller15 method test also passes, receipt1d9cb2e7/3462; it proves
local compatibility only, not the guest failure's cause or feature acceptance.

The one saved-API typed projection passes0 in0.486237s, outer3152618/
start415528331 reaped/absent. Local
`.scratch/web-006-native-source14-authority14-api-typed-journal-v1-result.json`
isba7ba36d8b2516d3e3718c7189e0d7b37b9cd35c734f0df3d816622f7b839b72,
7880 bytes. Guest554b011c/13953 and caller7b35a443/16027 pass33 owner plus19
independent tests,52 without skips. Sourcecheckea297483/3412 and independent
0acdb683/7622 include the actual eight-file caller and late-closure/raw-hash
refusal checks. The earlier test-only AST guard's benign BOOT.replace false
positive is corrected without runtime source changes; failed XML is retained.

Both held guest inputs and all eight local captures close. The parser performs
no journal query, guest write, role action, key/individual-secret read or replay.
It actually holds journalRESULT35ec862b/104341 at inode78204037 and retained
API raw365a7d3d/6288 at root600/secret_t inode78191543. The exact original
API94791/UID:GID983/IID364ec333 row matches the86-byte repository-defined
HFAPI003 credential_source_unavailable template, with same-invocation exit10.
No specific credential file or failure mode is identified by that generic
message. Independent actual review640b2df2/3301 verifies all joins and limitations.

Separately, the frozen two-flag local proposal498e474e/3662 changes only parent
directory O_RDONLY to O_PATH in credential_sources.py. Actual UID1000 under
search-only0100/0300 owned directories reproduces original HFAPI003/errno13
while the proposal reads the same53-byte synthetic credential. Leaf no-follow,
owner/group/mode/nlink/size/full9/race checks and bounded reads stay unchanged.
All38 focused and161 existing auth/Basic checks with compiled proposal aliases
pass without skips; review89630692/4504 records exact evidence. This is a local
bug reproduction, not proof of the original native failure's specific mechanism.
Product source14 remains frozen and unchanged. A fresh, fixed native-systemd
synthetic-credential comparison with actual parent metadata and normal lifecycle
closure is being prepared before any product correction or new activation.

The new synthetic native reader diagnostic v2 actually fails1 in6.896724s;
outer3157692/start415690290 is reaped/absent. Local
`.scratch/web-006-native-credential-reader-reproduction-v2-result.json`
is c7f2d4e313331b5bdb6611e87f449d44f06bfb6a086c79852d8f0a1ab75b0886,
78733 bytes. Frozen guest58077724/63962, caller44aee42f/14338,
worker904d94b4/7420 and unitb0c8bd5a/1057 passed24 owner and23 independent
source checks with no skips, including the corrected closed-result/READY race.
Sourcecheck7b43a150/10757 and independentdca0e2b0/3128 retain the exact packet;
unexecuted v1 remains preserved.

Original worker95328/start16573801, invocation459e5a557ed24faaa27dfce51a806eca,
starts then exits1 without READY/result. The collector retains TimeoutError;
outer ValueError/localclosurefalse and guestclosurefalse remain unchanged.
All13 command children return0/reaped; all13 raw-channel pairs have private
labels and joins. Normal stop is attempted once; original worker is gone and
its cgroup physically absent. The new unit remains failed/exit-code/status1;
it is not reset or described as inactive. Original13 rows,25 handles and4
cgroups rejoin, but post-endpoints are intentionally skipped/strictquietfalse
because the new unit is failed. Held revalidation failure list is empty.
Independent actual auditcf08fd2d/3398 rechecks all12 local captures and joins.

No credential-reader comparison was obtained. The source candidate is the
worker's attr/current .strip() retaining a trailing NUL; an original-invocation
journal read must establish its actual cause before any correction. The
application source14, key/policy and current3 leaves remain unchanged. No
product fix, native/rootless feature acceptance, failed-unit reset or replay
is claimed. Checkpoint56 preserves the complete original failure and next step.

The one original synthetic-probe journal read passes0 in1.142789s, outer3159711/
start415756674 reaped/absent. Local
`.scratch/web-006-native-credential-probe-original-journal-v2-result.json`
is0d54a1312666d41bda7b9561c1610834f9a65f49b288065041969a44c1943feb,
66751 bytes. Frozen guestf74e2209/41802 and caller4c5e8258/16282 passed14
owner and8 independent checks, zero skips; source84641b4a/7771 and independent
90cf19f7/6645 bind all8 actual local captures. The preceding v1 first-error
counterexample stays red/retained; v2 changes only the outer first-error guard.

All7 command children95388/16640089,95389/16640110,95391/16640115,
95392/16640119,95393/16640123,95394/16640139 and95396/16640144 return0/reaped.
All captures close and14 private raw channels join; held failures are empty.
The original failed RESULTfa83206b/67759 is first actually held at root600/usr_t
inode94391470. Original13 roles, failed diagnostic unit, key and current3 leaves
are unchanged. No service action, endpoint probe or credential body read occurs.
Original worker95328/UID:GID983/IID459e5a55 yields exact source frames
module129→main109→need26, ValueError and manager exit1. This measures failure
at the worker's context validation, before either credential reader. The raw
context is not retained by that traceback, so a trailing NUL is not uniquely
proved. A fresh native-v2 synthetic scope with strict normalized context and
raw-length/trailing-NUL booleans is prepared next; failed native-v1 is preserved.
Product source14 and every installed acceptance status remain unchanged.

The fresh native-v2 synthetic comparison v3 passes its diagnostic collection0
in2.273427s, outer3162518/start415839394 reaped/absent. Local
`.scratch/web-006-native-credential-reader-reproduction-v3-result.json`
is3b1fe8a359e9a416f9317ee7473b4aafdcbf34463bde4158ae1409bb880cf4a4,
112568 bytes. Bound guest14d8ad01/72251 and callerb44837c6/16852 derive only
the declared e948/remote data bindings from416aad66/72194 andb207f8de/16791.
Owner22 and independent25 checks pass, zero skips. Final independent
a98958f3/8341 rechecks all14 actual local captures; quoted SSH argument89327B.
All16 command children return0/reaped,32 private channels join, all local/guest
captures close, and held failures are empty. Old failed-v1 properties, files,
original handle and physically absent cgroup are preserved. Prior journal
e948b19e/58476 is now actually held root600/usr_t inode18615202.

Actual worker95508/start16722914/IIDbe5b358bad8e4be0a44ba70dba722894 observes
42-byte ownproc context ending NUL; strict normalization succeeds. Its actual
SID is unconfined_service_t. Original API init_t was a journal peer-context
field, not a direct ownproc measurement, so equal/different own-domain claims
are unsupported. All20 manager security properties equal the loaded API;
UID/GID983, zero capability sets, NNP1 and Seccomp2 are observed. Normal SIGTERM
and successful stopped report close its original process/cgroup; new unit is
inactive/success, and both5-endpoint observations refuse as required.

Both original and O_PATH readers reject HFAPI003 after all5 opens succeed.
The delivered synthetic leaf is root:root0440, single-link,53 bytes; groups
are[983]. Every other leaf check passes, so the existing group guard rejects
before credential bytes are read. This diagnostic does not support adopting
O_PATH for the native failure. Actual ACL bytes were not captured. Systemd257
write_credential applies owner-read then a named-UID read ACL, using ownership
only as fallback; that primary source motivates a strict ACL-aware proposal,
not a blanket group-check bypass or a changed permission. A fresh native-v3
scope must observe the synthetic ACL and compare the original reader against
the independently reviewed ACL-only prototype. Product source14, policy and
all feature acceptance remain unchanged. Checkpoint58 retains this outcome.

Contract-first ADR152 now accepts the precise ACL-only exception, with updates
to112/146, their index, INV-002, architecture, server/security and human startup
troubleshooting. It records implementation/installed proof pending, the exact
five-entry44B accepted value,64KiB stdlib retrieval ceiling, descriptor ACL/full9
ordering, unchanged ordinary group branch and no permission/dependency grant.
Current working docs now differ from historical source14:8 changed indexed
documents plus newADR152. Gate14 remains a historical pass, not a gate for these
edits. Product credential_sources.py remains original3cc767b6/3666, including
original directory flags. Source15 has not been captured or gated.

Frozen ACL-only proposal0fc4b568/4997 passes30 focused and231 unchanged
auth/Basic checks with zero skips; final review3b095eba/1915. Independent
reader30+worker19 source checks pass; combined revieweded408b69/3301.
Actual local ACL xattrs are exercised, but root UID/GID metadata is modeled in
the login-user tests. They do not establish actual delivered ACL or feature
acceptance. The fresh native-v3 comparison must measure those metadata and
prove reader success before product adoption. Checkpoint59 records this new
working-source state and preserves the previous both-reject result.

The fresh native-v3 synthetic ACL comparison v4 actually passes0 in2.461174s.
Local `.scratch/web-006-native-credential-reader-reproduction-v4-result.json`
is d40259cc94d5236cac2b7a27d923f169eb4b51c954044cc960f3fde53a585817,
131960 bytes. Worker95646/start16866969/IIDd25121e406424d359b2fbeadda4a0ae6
observes the exact five-entry canonical ACL on root:root0440/nlink1/53B delivery:
owner-read, named UID983-read, no base-group access, read mask, no other access.
Original3cc767b6 rejects HFAPI003; ACL-only prototype0fc4b568 reads the same53B.
Both use the original five O_RDONLY opens and the same20 manager hardening
properties, UID/GID983, zero capability sets, NNP1 and Seccomp2. All18 command
children return0/reap, all15 local/guest captures close, and36 private raw
channels join. Normal SIGTERM/STOPPED, inactive/success, original process gone,
physical cgroup absence and both5-endpoint observations pass. Both older scopes,
original13 roles/25 handles/4 cgroups, key/policy and current3 are preserved.
Independent actual audit061ac52f/5420 and pre-adoption closure01b7d971/8398
verify this positive diagnostic. It does not establish the original native14
failure's specific file/cause or installed application acceptance.

Canonical reader37acf7b8/4941 now implements the accepted descriptor ACL policy;
parent O_RDONLY flags remain unchanged. Permanent2621f5c3/8132 adds17 real-xattr
regressions. The combined actual product selection passes178 without skips in
3.48s; independent actual product17 pass without skips in0.29s. Full Ruff and
format checks pass after a retained first PLR2004 literal-mode failure was fixed
with one named constant. Independent canonical review43c6301f/2680 proves that
removing exactly that assignment and normalizing its one load makes the entire
reader AST equal native-tested0fc4. This is explicit compatibility evidence,
not byte equality or installed application acceptance. ADR152,112/146,
INV-002, architecture, server/security and human troubleshooting now describe
the implemented source policy with installed acceptance pending. Documentation
validation passes207 human documents and27 helpers.

Source15 is frozen at1361 files, parent07d10e0053f9f577a67fb513cdfebad40c314c8e,
label `WEB-006, this commit`. Capture1d6df56f/684 records inventory87eba268,
snapshot7eee22b20d968fc9b7a9c28cc714f4475ee9d80c1e6280ee0cf551c1b0e32e51
and archive5d15d8ae/17725440. At2026-10-22T17:55:11Z, bound runner881d325f/6619
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
gate3168832/start416025291 under owned caller3168829/start416025273. Its result
is pending; no final gate pass is claimed. Source14 gate remains historical.
Checkpoint60 preserves the bindings. Fresh canonical product0.2.2 artifacts
and a separately attributed exact-two-metadata-field fixture0.2.4 projection,
with rootless deployment0.2.5 and pinned UBI10micro API/UI image, are being
prepared; none is built or staged yet. Old native0.2.2/rootless0.2.3 trees and
source9/image13 are preserved. Required native/rootless application, negative,
fault, secret-lifecycle and drain acceptance remains pending.

Actual strict gate15 now passes0 in1227.329073s, finished2026-10-22T18:15:38Z.
Result `.scratch/web-006-gate15-result.json` is
aa4085c277781f8eb4a253bcf7a0dcf3a21fa70ba86caeac83ccf3ffb1b05b9d/816;
log9321f5933642131009231cef847f822338117c465c3d20665f6002ddf71c7161/100881.
All1361 source hashes/modes remain unchanged. Original gate3168832/start416025291
and owned wrapper3168829/start416025273 return0, normally reap and are absent.
Actual results:7749 Python passes/52 explicit opt-in deselections, all3 locked
wheel installation profiles,572 historical frontend tests plus mounted component coverage,
135 audited wire definitions,207 human documents/27 helpers,21 sandbox and9
functional-metadata checks,2786 web unit and2846 combined component checks,
production UI build,2 Chromium startup checks and real HTTP/API React read
fixture. No required executed check skips. Installed Caddy/native/rootless
feature acceptance is separate and pending. Independent source capture/gate
reviewadb6fa5f/5726 verifies1361 current/archive hashes/modes and exact source14
delta; overlay/controller source review457bd55c/2822 passes20 independent cases.

Root binds only the two actual gate/log records into overlayv4; bound854614ca/
21303 and bindingb865b5cf/1182 retain the rest of the entire module AST. The
actual owned projection passes0 in6.875730s, child3188206/start416150526 reaped/
absent. Report `.scratch/web-006-source15-fixture-projection-v1/projection.json`
is7b799c8cd21ebf2b4346a9215a6b518a184c5431568020b038f299c9cd05d5e8/260485;
fixture snapshot81ea52553a53962e3e4570ae0a312274fbd2df5404990c1737f626c0984e0e10
contains1361 leaves, with exactly the declared two TOML version fields changed
to0.2.4; all108 package source leaves equal canonical source15. All seven held
capture inputs close. Canonical product stays0.2.2, rootless deployment will be
0.2.5. No build, guest transfer/stage, installer or application start occurs in
this projection. Checkpoint61e13a1011/4346 records both actual passes, preserves
checkpoint60's original running start-event prefix after its owned log appended
the final result, and retains every older failure. Fresh artifact, transfer and
stage executors are being prepared; no installed acceptance or commit yet.

Fresh artifact pipeline actually passes. Canonical owned copy3189526/
start416197726 returns0/reaps/is absent in0.170741s; summarye3fc210c/12777
and wheel3a9b21b1/500286 retain source15/product0.2.2 provenance and all108
package hashes. Fixture builder3190315/start416222764 returns0/reaps/is absent
in21.617745s; summaryc7d681a9/269700 and actual0.2.4 wheel79f1d75a/500283
have the same108 package bytes. Its private installed Python reports0.2.4
and matches all108; two original UI builds are byte-identical, manifest
f09f904e6698090305d11498171e4ea53d8a1e84c9c9d92435a7897b7fd404c6.
Both metadata identities remain explicit: canonical7eee22b2 and fixture81ea5255.
All13 held fixture inputs close. Owner28 plus6 binding/late-closure checks pass;
root independent flow/AST review verifies the one canonical-summary binding.

The fresh API/UI image build also passes0, actual builder3192142/
start416256895 reaped/absent in23.183050s; owned caller3192081/start416256516
returns0/reaps/is absent in27.137109s. Buildafea3e9f/585688 records image
sha256:07bd818e882466d748b0089733b5877b78fbd754d7d5d3cf828d5d13511d3a34,
204760971 bytes measured on the build host. Both original FROM stages retain
pinned UBI10micro87a27d71; the only recipe changes are offline dependency
inputs, verified UI copy and explicit unshipped fixture metadata. All14 held
inputs close. Owner7 bound-image checks plus prior28 pass; root independent
review verifies only the two actual artifact-data bindings. Actual OCI export,
guest runtime ancestry/absence and installed application acceptance remain
pending. No runtime/image acceptance follows from labels or build success.

Before staging, the one actual read-only prefix-label preflight passes0 in
15.665766s, caller3191649/start416242799 reaped/absent. Local818050de/111957,
protectedaf5840f2/101598 inode18615230 and independent8aa74968/13939 retain
all11 child0/reap records, six local captures,13 original roles/28 original
handles/7 physical cgroups and both5-endpoint checks. Key/current3/seven
canonical inputs and both old release inventories remain exact. The positive
comparison64e276f4/116478 is first actually held at root600/usr_t inode94388053.
Owner21 and root independent21 checks pass without skips. The fixed command
is `restorecon -nRFv /opt/hfcache`, with no actual relabel/move/service effect.
It measures1 current-selector correction and52 old-rootless0.2.3 corrections;
native0.2.2/other/unclassified counts are0. This explicitly blocks the unchanged
installer's relabel step until preservation is complete.

Root selects a finite guarded NOREPLACE preservation after fresh transfers:
move the current selector/deployment/policy and old rootless0.2.3 outside the
installer prefix, retain every inode/label/body and all child full9 values,
and record only the owned renamed-root ctime transition. Native0.2.2 and all
old RO projections stay exact in place. New stages consume the completed
record; authority15 never replays those moves. No preservation or new stage
has yet run. A separate pre-execution review finds the source-transfer v1
fixture index missing parent_commit/dirty/label required by the original
functional consumers. Fresh unexecuted v2 successors add those truthful joins;
v1 remains preserved, and no invalid packet/guest transfer was attempted.
Checkpoint62 `.scratch/web-006-source15-current-state-v62.json`,
8216f0b6567f6671cd0483bffed6418e92b499136c5019b0f981808195b0a96f/20249,
records these actual results, exact artifact paths and next prerequisites.

Source15's corrected source-transfer packet actually passes. Packet assembler
3194911/start416307808 returns0/reaps/is absent in2.491422s; packet a46f4e39/
837468 and payload07a3acd5/36454400 contain exactly10 protected source/gate
members. The fixture index6bf59ac9/244492 adds truthful parent/dirty/label
consumer fields before execution. Original consumer identity/tool validation
and25 source checks pass without skips. Bound callerbde18c0b/16023 and
guest1bc414d1/53067 pass8 final source tests without skips before the one
actual transfer. Caller3196148/start416352486 then returns0/reaps/is absent
in13.297128s; local resultfcc6c57b/1936214 and independent1677bf45/2742
verify all16 captures,6 guest command0/reap records,10 protected members and
1361 full9/hash/mode public files in the fresh owned repository. The protected
RESULT's serialized bytes are verified; its first inode/context hold remains
pending. Current3/key/old releases,13 roles/28 old pairs/7 cgroups and both
five-endpoint observations remain unchanged. No stage/application start occurs.

The first actual local OCI exporter fails before Podman or EXPORT creation:
child3196804/start416371445 returns1/reaps/is absent after0.101197s;
stderr92883d94/398 records missing __file__ in the exact owned Python-c
namespace. Preserve this failure and frozen v1 source; do not replay it.
Fresh v2 explicitly pins its own source path. Its20 source tests now include
the actual namespace without __file__, real two-pipe drain and late closure,
all passing without skips. The actual v2 child3197390/start416388112 returns0/
reaps/is absent in6.386457s. Exportba5df85b/38685 closes all inputs and seven
normal0/reaped children. New app OCI623dcc29/66055168 contains image07bd818e;
base1a54690d/7851520 and Caddyef607155/26818048 retain their exact old bytes.
No guest load/runtime audit or installed acceptance follows from this export.

The complete artifact assembler3197389/start416388111 also returns0/reaps/
is absent in0.426750s. INDEX6ccf3741/6144 and payloadd9a8055a/2375680 contain
13 exact members: two summaries/wheels, six UI files, two UI evidence files
and image build. Root independently verifies all tar headers/modes/bodies,
source bytes, all three OCI archive hashes/lengths and all1361 current source
hashes/modes. Checkpoint63 `.scratch/web-006-source15-current-state-v63.json`,
947c53c4b6cdb4bee864330ddb2cac41d2ce155e65c343c0b5b7c0bb6a3a1441/9034,
records these actual results. Guest artifact transfer/load/runtime audit,
four-move preservation, native4/rootless5 stages, authority15 and required
application/negative/fault/secret/drain acceptance remain pending. No historical
failed generation is replayed and no production/remote action occurs.

The one actual full artifact transfer now passes0/1.528909s; child3199599/
start416456795 normally reaps/is absent. Local366b27aa/92073 and independent
d3828b24/1684 join22 held local inputs,13 protected files/package108/UI6 and
six normal0/reaped queries. First actual source RESULTf27/1835230 is measured
root600 inode27264410, SID `unconfined_u:object_r:usr_t:s0`; retain that actual
SID. Protected artifact RESULT7d99742f/75011 is verified from exact serialized
producer bytes, with inode/context first hold pending. All current3/key/old
release,13+3synthetic roles/28 old pairs/7 cgroup and endpoint guards pass.
Bound17 owner checks and root14+3 independent checks pass without skips.

The one actual OCI transfer then passes0/3.530740s; child3200927/
start416495574 normally reaps/is absent. Transferbbacf4e6/26831 closes all
archive/export/build/source/transport inputs and five normal0/reaped SSH
children. Four exclusive guest files retain actual UID1000:1000/mode0600,
SID `unconfined_u:object_r:user_home_t:s0`: app623dcc29/66055168 inode78205872,
Caddyef607155/26818048 inode78205873, base1a54690d/7851520 inode78205874 and
exportba5df85b/38685 inode78205875. No image is loaded, no container/service
starts and no existing file changes. Frozen sourceda05b336/28721, owner9 and
root independent9 checks pass without skips; root reads complete transfer/
receiver/FD rewind/QEMU guards before execution.

Source-only preservation19, caller13 and native-stage15 independent tests also
pass without skips; guest root ownership/SID/manager facts in those tests are
explicit models. Native/rootless staging remains unexecuted. Eight actual
source15 unit/integration records are appended to AUTH08/HOST01–03 while those
four cases stay pending; human documentation validation passes207 documents/
27 helpers. Checkpoint64 `.scratch/web-006-source15-current-state-v64.json`,
9d8a788cdfcf328b02922aa35a3b424a1271bc23306ced607d4228005043e613/9056,
records exact actual transfer evidence and fresh1361 hash/mode verification.
Required runtime ancestry/absence, four-move preservation, original native4/
rootless5 stages, authority15 and application/negative/fault/secret/drain
acceptance remain pending. No production/remote or replay action follows.

The one actual stock983 image-load attempt has distinct inner and outer
outcomes. Owned caller3203468/start416578745 returns1/reaps/is absent after
7.523069s; local `.scratch/web-006-source15-fixture024-image-load-v1-result.json`
4ff47d6a/89910 retains outerValueError/localclosurefalse. Its classifier requires
empty stderr even for Podman load; actual load stderr is667 bytes, SHA4ee8737a.
Original outer stderr5b490063/1120 and every failed result/source remain intact.

Inside that original run, loader96150/start17462239 returns0/reaps after
4.855874s and actual image07bd818e is loaded once. It was absent beforehand.
All12 children reap; only the intended pre-load `image exists` returns1.
Guest errornull/heldclosuretrue, no held failures, unchanged current3/key,
original strict13+3synthetic/28pairs/7cgroups, pause identity/namespaces and
archive3 full9/SIDs are recorded. App/base/Caddy immutable IDs/layers and pinned
micro layer prefix match. Guest app size204761025 and build-host204760971 remain
separate observations. No application container starts. The artifact RESULT
7d99742f/75011 is first actually held inode94388058/root600/unconfined_u:usr_t.

Raw load stdout96/stderr667 remain private secret_t channels; their contents
have not yet been read or classified as harmless. Root freshly rejoins all8
original local full9/hash captures without changing the failed outer flag.
The caller's final QEMU join after classification was not reached; do not
invent that observation. Prepare one bounded read-only channel/result getter
and separate explicit interpretation/closure receipt, then runtime audit.
Never rerun this completed load or its now-false image-absence precondition.
Frozen loader9881fae0/56677 and caller41c19d91/15351 had passed owner16,
root independent16/1.81s and C independent16/1.77s with explicit modeled guest
facts. Those model passes did not predict the real load's stderr behavior.

Fresh authority15 inert templatea4c4805c/90386 and input schema1805a7c4/4568
pass49 owner and49 C independent tests without skips. Exact codec round trip
uses22839 compressed bytes/41345 quoted argument bytes. Rootless stage11 and
native/rootless safe-caller16 independent tests pass without skips. Review
corrects the new rootless provenance consumer before execution: fixture6bf/
81ea and canonical87eb/7eee retain separate fields. C independent authority
review7b0cbaec/4172 verifies consumer joins, original validator, new private
namespace, seven-source historical policy compatibility and finite2048 budget.
All future stage/audit/input hashes remain unbound; no authority/staging effect
occurs. Source15's1361 hashes/modes remain unchanged.

Checkpoint65 `.scratch/web-006-source15-current-state-v65.json`,
4be95675f06ccb80d76e5606d6dcaa3757a6e1320cb5c225e302810c58c72d1e/16930,
records exact inner success, original outer failure, private-channel locators,
fresh local rejoin and pending no-replay interpretation/runtime/installed proof.
Preservation/native4/rootless5 stages/authority15 and required application,
negative/fault/secret/drain acceptance remain unexecuted or pending.

The separate saved-load interpretation actually passes0/0.677992s, child
3205416/start416643360 reaped/absent. Local6beffc40/11310 closes9 original local
inputs and all guest holds with fresh before/after QEMU joins. Original load
RESULTf6b2c8b1/80260 is first held inode27170024/root600/unconfined_u:usr_t;
actual stdout96 inode27170010 and stderr667 inode27170011 are root600/secret_t.
Both exactly equal the public templates reconstructed from actual app OCI
manifest862386dc: six exact blob digests, config07bd and manifest-write progress,
plus the exact loaded-image line. No extra output, broad stderr allowance,
engine/manager/journal/network call or load replay occurs. Original outer
4ff47d6a/ValueError/localclosurefalse stays unchanged. This is a separate
interpretation/closure receipt, not retrospective success of that caller.
Protected completion388bd2d3/5186 has exact serialized bytes; first inode/SID
hold remains pending. Owner8/root independent8 pass without skips; root and C
source-read exact templates/retention. Runtime/installed acceptance is pending.

The controller16-only donor transfer also passes0/1.195695s, child3205625/
start416648310 reaped/absent. Local08508125/107278 and independent81673d5b/2503
join all5 local captures, six normal0/reaped queries and unchanged original
13+3synthetic/28pair/7cgroup/current3/key guards. Actual protected controller
ba8808aa/99201 is root600/system_u:usr_t inode78207410; its new private directory
is root700 inode78207409. The controller is compiled but never executed; no
authority/input JSON or application is started. Protected donor RESULT324614ef/
97932 remains serialized-byte verified until first metadata hold. Owner8 and
root independent8 pass without skips; actual local controller mode0600 is
bound without changing any original permissions.

Checkpoint66 `.scratch/web-006-source15-current-state-v66.json`,
010cb121ba959a3edb67191e391ee865e67f863076f337f1193750a44533f02c/9351,
records both actual results, original failed caller preservation and1361 exact
source hashes/modes. Human documentation check again passes207 documents/
27 helpers. Runtime audit must now consume the actual loaded image and separate
interpretation receipt without reloading. Preservation/native4/rootless5
staging/authority15 and required installed application/negative/fault/secret/
drain acceptance remain pending. Supplemental source preparation is adding a
held original passing-native prerequisite and correct new private-channel
retention; no accepted-peer parser bypass or MAC attribution is inferred.

Checkpoint67 records the original source15 image runtime audit refusal. Owned
caller3209127/start416763356 returns1 after59.464459s, is reaped and absent;
local5b2183f4/99045 retains ValueError/localclosurefalse. Guest21 commands all
return0/reap and held-input failures are empty. The runtime probe passes all108
package and6UI bytes, UID mapping and named-tool/module checks and reaches the
final stopped/exit0 container inspect. Exact raw mount comparison then refuses:
the sole owned read-only gate bind's Mode changes from `Z` to empty after
startup; source/destination/options/RW and every other isolation field agree.
The new retained CIDfd3403de and original PID96550/start17652468/cgroup remain
recorded; fresh process/cgroup closure has not yet been measured.

Original failed protected RESULT6d5db5f1/87527 remains intact, with its first
inode/SID hold pending. Root freshly rejoins all10 original local full9/hash
inputs. The failed caller's final QEMU join after classification was not
reached. Separate read-only completion must hold the original saved inspect/
runtime channels, interpret only this exact mount transition, and freshly prove
stopped CID/original PID/cgroup and old fixture guards; never restart or repeat
the audit or image load. The load-completion RESULT388bd is now actually held
by this original audit. Owner29/root29/C29 source tests pass without skips;
native authority/readiness root86 also pass without skips. These modeled
checks do not establish installed acceptance.

Checkpoint `.scratch/web-006-source15-current-state-v67.json`,
7f932e3a03d68cf569c36933adec4541bd44a30010642ec5582a51a73769e500/13756,
records the actual failure and fresh1361 exact source hashes/modes. Four-move
preservation, native4/rootless5 stages, authority15 and required application/
negative/fault/secret/drain acceptance remain pending.

The separate read-only image completion actually passes0/2.090816s, child
3211960/start416845374 reaped/absent. Local2ddb74ca/106650 closes13 captured
inputs; all9 new queries return0/reap and original21 commands remain intact.
Exact saved runtime/inspect/history bytes join all108 package/6UI files and
35 named-tool/8 named-module absence checks. The exact retained CID is stopped0,
original PID96550/start17652468 is gone, and both original scope paths are
physically absent. Old2 retained containers/current3/key/pause/strict13+3roles/
28pairs/7cgroups match. Original audit6d5db5f1 is first held inode84707246/
root600/usr_t; its ValueError/false flag and the original load caller stay
unchanged. No restart/load/create/remove occurs. Independent actual review
6e60a695/11795 passes. Protected completionb2f90b47/92734 is then actually held
by preservation inode84709378/root600/unconfined_u:usr_t.

Four-move preservation actually passes0/26.796345s, child3212227/start416853344
reaped/absent. Local46ba113e/146868 and protected2a42de47/133594
inode94399855/root600/usr_t record all4 no-replace moves, no replay, exact old
inodes/bytes/modes/SIDs and only the owned root rename ctime transition.
Native0.2.2 and every rootless descendant remain unchanged. The selector,
deployment, policy and oldrootless0.2.3 names are absent; the final read-only
prefix label preflight returns0 with empty channels. All12 children return0/
reap; independent original classifier/full9 rejoin passes. These preserved
objects are evidence, not an assertion of a runnable rollback tree.

Original native4 staging actually passes0/52.799186s, child3212486/
start416862222 reaped/absent. Locala9b72c7a/163796 and plain protectede39e5b9e/
93448 inode101754720/root600/usr_t join all108 installed package files, six
verified UI assets and supported native server candidate6a827fce/1304, changing
only `web.asset_root` and `web.manifest_sha256`. Original installer96749/
start17747380 returns0/reaps in16.036312s; all15 children return0/reap. Source,
old trees, protected inputs and final callbacks rejoin. No selection/service/
policy action occurs. Independent original native classifier passes.

Original rootless5 stage/render also passes0/31.025010s, child3212753/
start416870605 reaped/absent. Local949619fe/293360 closes all inputs; all12
children return0/reap. Original protected staged3820df8c/65003 inode78456162,
input-provenance4f916a86/12203 inode78456163 and refresh-closure94b4a523/64477
inode78456164 remain root600/usr_t. Software0.2.4, deployment0.2.5, fixture81ea
and canonical7eee retain separate provenance. No application starts.

Actual stage receipts bind only core `PINS`/`INPUTS_SHA256` assignments into
authority source1d111d0b/90881 and input JSON72fe5c51/5006; all other AST stays
equal to the frozen core. Guard/schema checks pass. Binding8b84c231/15887
retains actual13 post-stage manager rows. Source/input donor transfer and
authority execution remain pending; controller16 is already transferred and
must not be transferred again. A fresh safe caller successor now additionally
requires a genuinely closed source/input transfer receipt before authority
execution; its predecessor remains inert.

Checkpoint68 `.scratch/web-006-source15-current-state-v68.json`,
ad927cac9366d0659dea39187e0d53159a52f30e56bcd13b12fbec6338e5b186/27098,
records these actual outcomes and1361 unchanged source hashes/modes. Additional
source-only root checks pass without skips: normal-rootless98, common
readiness21 and negative/supplemental27. Installed native/rootless application,
negative/fault/secret/drain acceptance remains pending; staging is not
functional acceptance. No production or remote action follows.

The two new protected source/input donors actually transfer successfully,
without replaying controller16: child3213818/start416902840 returns0/reaps/is
absent in1.289006s. Local1b488a39/121999 closes7 local inputs and all guest
holds; six queries return0/reap. Existing controller inode78207410/full9 stays
exact. Directory inode78207409 admits only the owned new source entry. New
source1d111d0b/90881 inode78456172 and input JSON72fe5c51/5006 inode43368103
are root600/system_u:usr_t. The original controller RESULT324614 is first held
inode78207417/root600/usr_t. Independent actual review1ba1d6ea/8283 passes.
No authority or application executes during transfer.

The one original authority15 preparation then fails1/12.134739s. Child3214767/
start416932396 reaps/is absent; localc2cf18f0/53785 retains ValueError/false
closure. Original protected authority RESULT1ec25418/35147 inode94416538/
root600/usr_t says successfalse/heldclosurefalse. All6 original queries return0/
reap; held failures and secondary observer failures are empty. Original donors
close, both finite descriptor budgets restore exactly (outer2048 to1024, hard
limit unchanged), original13+3roles/28pairs/7cgroups/endpoints close, and current3
names remain absent. No application starts. The caller's final QEMU join after
its failed classifier is not reached. Preserve both original failure records,
private stdout73256842/23703 and stderrd29933be/2482 at the recorded secret_t
inodes; obtain the exact stack through a bounded read-only getter. Publication
absence beyond current3 and the exact cause remain unmeasured.

All authority15-dependent native/rootless/normal/negative/supplemental15
templates are now inert: their passing prerequisite is unavailable. Never
repeat this authority invocation or reinterpret it as passing. Select a fresh
namespace only after actual diagnosis and publication/closure readback. The
source15 gate, image audit, four moves and both stages remain valid independent
evidence; no canonical source changes or installed acceptance follow.

The original bound-codec test's2PASS/1FAIL is also retained: it assumed exact
41949 quoted bytes across runtimes. CPython3.12 actually emits41949 and locked
3.14 emits41889; both verify exact packed/plain hashes and fit120000. A fresh
test checks that finite ceiling and exact held-core roundtrip/compilation with
the final authority call removed; root3PASS/zero skips1.40s. Root donor/safe42
and actual-bind2 checks pass without skips. Source bytes stay unchanged.

Checkpoint69 `.scratch/web-006-source15-current-state-v69.json`,
c656db80c797a4703a04d25811ce19e660789ee9c13fd33ace16cb216f58dc05/15293,
records the actual donor success, authority failure and1361 unchanged hashes/
modes. Installed application/negative/fault/secret/drain acceptance is pending.

The bounded failure getter actually passes0/0.596879s, child3217288/
start417014506 reaped/absent. Local949a89f4/26530 closes8 local and7 guest
captures, rejoins exact original failure/donors and measures18 publication
paths plus14 WORK children. It performs no manager/engine/process action,
guest write or replay. Exact2482B stderr is retained only in a new local0700
directory/0600 file; public output contains closed frames/classes/errno only.
Both interruption-before-raw-strip and local parent replacement were corrected
before this actual call; owner23/root23 pass without skips, and independent
real directory-swap tests leave foreign directories untouched.

The actual stack reaches authority15 `browser_inputs` line770, then unchanged
utility4 `file_record` line473/`read_file` line433. The former records the copied
Node executable; the latter applies its generic4MiB size bound. Exact copied
Node bytes/size still require a bounded read-only inventory; no unrelated API
or credential cause is inferred. Partial PUBLIC15 and existing public parents
remain present, as does generations16. Control16, manifest15, sudoers15,
controller copy, launchers and installed projection are actually absent.
Preserve the partial objects; do not restart or complete failed15 in place.

A fresh authority16/source15 intent is selected, UUID
`0e6d6ad6-6c12-4fb3-851a-4569f3c878be`, control/generations17. It will consume
the unchanged native4/rootless5 stages, last good authority14/control15 and
separate failed15 retention proof. The Node-specific bounded record and
disjoint browser/common copies under PUBLIC16 require explicit startup
`PROVISION` binding while preserving all launcher functions. Existing private
parents and partial trees require positive ownership/inode/SID/inventory joins
and only declared new-directory-entry transitions. All future node/partial
pins remain unbound until the next actual getter. No16 publication occurs.

Checkpoint70 `.scratch/web-006-source15-current-state-v70.json`,
582b3a5c7eaad03300e55e8a9c3e4c8205fdf7a29aca4a40031af382f5226349/21719,
records actual frames/publication state and1361 unchanged source hashes/modes.
All installed application/negative/fault/secret/drain acceptance is pending.

The next bounded read-only inventory actually passes0/1.590701s, child3220095/
start417106772 reaped/absent. Local7c554fd1/255893 closes9 local captures,
all original guest inputs and both complete inventory passes. Both original
and copied Node are123656816B with identical pinned digestf3432a45. This
confirms the generic4MiB recording refusal; Node remains test-only and absent
from the shipped pinned UBI10micro API/UI image. Six retained trees contain
263 ordinary nodes (210files/53directories), including183 browser files;
generations16 is actually empty. Both existing parent childsets and all4
shared support files are positively measured, with full9 identities, SIDs and
hashes. No bodies, key digest, guest writes, queries, process actions or replay
occur. Owner23/root23 pass without skips; source15's1361 hashes/modes remain
exact. Fresh16 input normalization and fresh3 donors are next; no new authority
or application starts. Installed acceptance remains pending.

Checkpoint71 `.scratch/web-006-source15-current-state-v71.json`,
d875d32de1eaaab9bb6719a49a95209af90e97486898a3eedf34ae1da0243eda/255379,
records the actual Node and partial-tree measurements. Two local real-FD
regressions identify parent-context-exit cleanup and post-hash identity rejoin
gaps in the unexecuted fresh16 harness draft; correct them before publication.

Fresh16's3 protected donors actually transfer0/2.852478s, child3221770/
start417150449 reaped/absent. Local42e3f608/134652 closes9 local captures,
all guest holds and original failed15 retention;6 queries return0/reap. New
root600/system_u:usr_t source6df62273/106256 inode127665316, input65949ca3/
214440 inode43368125 and controller2f5d330a/99201 inode127665317 are measured.
Fresh donor directory127665315/root700 admits exactly its2 own entries;
no prior donor, partial tree, stage or image is rewritten/replayed.

The sole original authority16 preparation then passes0/17.803688s, child3222217/
start417162082 reaped/absent. Local763f6df7/2688715 closes5 local captures and
original donors. Protected authority15ae9ff6/2318703 inode4219052/root600/usr_t
and safe collectionb6145aad/1793567 are measured. All16 original preparation
commands return0/reap; original installed validator/controller load pass,
all263 retained partial15 nodes and old shared files close, both finite2048
collector budgets restore their original soft/hard/descriptor sets, and
current3 names remain absent. Key/kernel/old releases stay unchanged. New
control17 isb759944c, manifest16a564de3b and runnerbe83a031. Existing provisioning
parent109908135 admits only PUBLIC16's new entry; scratch parent101754722 is
unchanged. Independent donor/preparation reviews pass. No application starts.

Root source checks pass0skip: core33, donor29, safe29, actualdonor2; exact
local9/5 captures and compile-only codec join the bound bytes. Checkpoint72
`.scratch/web-006-source15-current-state-v72.json`,
4a93c32e93ef73e52f7c5e49719c54257f426d86507b0ebabeeb8b25c00828ab/19042,
records actual preparation and1361 unchanged source hashes/modes. The larger
2318703B authority exceeds inherited2MiB functional-harness capture defaults;
this is caught before any native16 run. Fresh explicit authority-only4MiB
call sites/regressions must pass before native/post/readiness execution;
generic capture bounds remain unchanged. Installed native/rootless/negative/
fault/secret/drain acceptance remains pending, and WEB-006 stays open.

The first original native16 functional run actually fails1/98.331034s,
child3223776/start417204261 reaped/absent. Local63eb7a30/21906 retains
ValueError/false outer capture flag. Inner native result658089c1/11527 and
safe collectione32da866/16560 retain no inner exception and true input closure;
original runner97236/start18087659 returns1/reaps in97.265365s. Its five
commands return0,0,1,0,0/reap, original62B stderr remains protected secret_t,
and no SUMMARY/functional PASS exists. Preserve this failure without replay.
All native16-dependent normal/readiness/negative/supplemental publication
scopes are now inert; a corrected future attempt needs a fresh reviewed scope.

A separate strict read-only post-run getter then passes0/0.796594s, child3224710/
start417232634 reaped/absent. Local2ddd3fcd/44345 closes8 local and all guest
captures. It first measures generation530c0ffec2b84dbdbb9619d125654493 and exact
statecd5bdced/20941 inode18673560/root600/usr_t. All20 original state handles
and5 original command handles are gone, all13 roles are inactive,4 saved
cgroups are empty and5 guarded endpoints refuse connections. The original
four-role same-PID principal/cohort preflight passed without retry in0.408s;
READY/instance and subsequent API/peer/namespace/secret proof counts are absent.
This establishes closure, not startup acceptance or a cause. SUMMARY is absent;
BLOCKED/RESULT/stop response and current native0.2.4 selector/deployment/policy
are present and retained at their measured inodes. Key metadata is unchanged.

Checkpoint73 `.scratch/web-006-source15-current-state-v73.json`,
7d6c67b058205aa8db0de51d3a7d3679bfb54532f8f2f5740e78d096911f7ff0/49420,
records the actual failure, separate closure and1361 unchanged source hashes/
modes. Root86 native/post/size and13 actual-post-binder tests pass0skip before
their owned calls; independent original-failure and strict-post reviews pass.
Next is bounded exact-generation startup/journal classification with private
channels. Do not infer an API credential cause or API security domain from
older native14 evidence or manager-emitted journal entries. Installed native/
rootless/negative/fault/secret/drain acceptance remains pending.

The first bounded original-window journal collector fails before queries or WORK
creation, child3228076/start417334141 returning1/reaped/absent in0.590253s.
Localb78ca900/6249 retains ValueError/false closure and phase held-inputs. A
real symlink regression reproduces an inherited selector2/3 comparison against
the actual native4/rootless5 post schema. Preserve that failure; it diagnoses
the collector comparison, not the functional failure.

A separate fresh v2 collector corrects only those metadata literals, uses a new
WORK/result, and adds safe phase/function-line refusal localization. Root47
focused tests pass0skip8.34s and9 actual local FD captures rejoin/close; owner33
and independent19 also pass. Its one actual read-only call passes0/1.223924s,
child3229680/start417390467 reaped/absent. Local73bbf430/150444 closes all9 local
and all guest inputs; all9 queries return0/reap. Manager state is unchanged,
all new raw channels are secret_t before bytes, and original failures remain
unchanged. First held post RESULT inode101754742 and original62B stderr
inode60292854 are measured without inventing earlier observations.

The exact102s original-window journals contain helper6/API5/worker5 manager
rows and Caddy6 rows, including one own PID97343/UID982 unknown221B message.
No API own-sender error/code/frame is observed. Audit10 rows concern original
helper97322 ioctl/search; no API/Caddy causal or MAC attribution is established.
The source controller owns a90s HTTPS bootstrap retry loop which does not save
its caught reason. Trace retained readiness/log/response evidence next, without
replaying native16 or claiming a credential cause. Current native4 selection,
deployment/policy and all failed/inert scopes remain retained.

Checkpoint74 `.scratch/web-006-source15-current-state-v74.json`,
c06c284e93d667588cf338ceb06ae44511d83e2fc0e06f5296ea67ef9e56aa22/153691,
records both diagnostic outcomes and1361 unchanged source hashes/modes.
Installed native/rootless/negative/fault/secret/drain acceptance remains pending.

The one saved startup/static/workspace getter then passes0/1.374675s,
child3232960/start417476818 reaped/absent. Locald9fb05f2/46698 closes all10
local and all guest captures;4 readonly manager queries return0/reap and
manager/current3/key state stays unchanged. Root23 tests pass0skip5.00s plus10
actual FD preflight; independent actual reviewcf471bc0/14982 passes. Newly held
original journal RESULT inode109909779 and protected Caddy raw inode109909771
are measured. Public CA9758b5ee/1541 inode9905764 and server certificate
b4dcb6b5/1562 inode9905765 both fail validity-window inclusion for the exact
original native16 window. The server certificate has the127.0.0.1 SAN.

The Caddyfileddbecc09/340 and unit36c90604/1522 match their original source;
both fixed drop-in directories are absent. The221B own Caddy message is an
unknown JSON info record with no error field. Actual original workspace JSON
confirms20 processes/4 cgroups/5 endpoints stopped,0 containers/browser modes,
no READY/start response and the original cleanup_unknownTrue flag. No HTTP/TLS
exception, certificate validity endpoints/signature-chain verification or sole
functional cause is claimed. The original native16 failure stays failed.

Fresh derivative17 intent UUID11695e01-ab1c-40b1-ba98-c14306638e37 selects
control18/generations18 and new protected/public authority17 paths, without
publication or application start. Preserve all old PKI and the current16 three
objects through new guarded same-inode NOREPLACE moves; never repeat the older
four moves. Reuse source15/image/native4/rootless5 stages, the RO108 projection
and browser183/Node/toolchain/seccomp inputs. Separate valid owned test PKI,
public CA trust and explicit controller/Caddy/browser bindings must pass before
the fresh scope. No production credential, master-key, security or service
change is authorized. All16 success-dependent scopes remain inert.

The inert controller18 bootstrap diagnostic prototypeb48a949c/104265 preserves
the original90s checks and records bounded safe phase/class/errno/TLS verify/
HTTP status/validation booleans. Root24 tests pass0skip1.64s, including first
error preservation and diagnostic-write refusal. Its source/control paths stay
explicitly unbound; fresh PKI literal bindings require separate review. A
512-record model plus1MiB unrelated-state reservation remains below the existing
2MiB state bound. No credential/body/error-text output or functional proof follows.

Checkpoint75 `.scratch/web-006-source15-current-state-v75.json`,
da212b3a159a999d6d38d7c846dd622f1ea4cc65875237d17adfc9791cfe585a/49886,
records actual diagnosis, unpublished intent and1361 unchanged source hashes/
modes. Installed native/rootless/negative/fault/secret/drain acceptance is pending.

The original isolated PKI17 renewal now passes0/2.256894s,
child3237947/start417638809 reaped/absent. Localc8498152/89918 closes all11
local and guest captures; all8 fixed commands return0/reap. Fresh CA and leaf
have measured7-day validity and pass actual OpenSSL chain,127.0.0.1 IP and
server-purpose verification. Empty private-key nodes receive secret_t before
OpenSSL bytes; collectors read/hash neither private keys nor the master key.
The new public CA is1dbeeac8/1574. The replacement isolated Caddy unit
689501bc/1570 changes only two LoadCredential source paths; the old unit is
preserved at the same inode by NOREPLACE. Old PKI/config/current3/key/kernel
and all original failures remain retained. No daemon reload or service start
occurs. This is fixture preparation, not installed application acceptance.

Root19 renewal checks pass0skip7.61s; independent actual review5aa775fe/22698
passes. Controller18c11b1411/111880 adds a pre-start public-certificate guard
to the bounded diagnostic prototype. Root26 guard/actual-producer-consumer
checks pass0skip3.30s. Local derivative17 core7ca50d6a/91720 and inputs
c2ba0fbf/3176 bind exactly four data assignments, with all other AST unchanged;
configuration/input validation passes. Three-donor transfer, fresh authority17
preparation, original native17 functional run and strict post-run closure are
next. No authority17 control/manifest or application has been published/started.
The renewal protected RESULT is expectedf138b306/78319 from exact producer
encoding; its inode/context awaits a separate held read and is not invented.

Checkpoint76 `.scratch/web-006-source15-current-state-v76.json`,
3dc893b6005c28dd5e35e96c554f36812caea8d91826c6419c39c3298a2e997d/92525,
records the actual renewal and1361 unchanged source hashes/modes. Original16
success-dependent scopes remain inert; installed acceptance remains pending.

The original three-donor17 transfer passes0/2.123480s, child3240598/
start417717782 reaped/absent. Localfa918b8e/173473 closes13 local/all guest
captures;6 queries return0/reap. Exact source7ca50d6a/inputsc2ba0fbf/controller
c11b1411 are protected root0600/usr_t at inodes18673562/43376839/18673563.
The renewal RESULTf138b306/78319 is now actually held at inode127665341,
root0600/usr_t. Independent actual review568b406d/11450 passes. No authority
or application starts during transfer. Root17 checks pass0skip5.55s and the
exact275769B payload/49798B quoted code and13 retained input FDs validate.

The original authority17 preparation then fails1/7.061260s,
child3241378/start417736903 reaped/absent. Local83c0c015/9006 retains outer
ValueError/false capture closure. Inner collection records FileNotFoundError,
no authority RESULT and no roles started. The sole query97777/start18620673
returns0/reaps, with private_channel_failure_class FileNotFoundError. All3
donor holds close and the original descriptor set/limits restore. Protected
collection74c66d08/3650 and original stdout1876B/stderr3017B remain retained;
no authority preparation or functional run is replayed. Root28 safe checks
pass0skip4.02s plus5 actual held inputs/codec preflight. These model/source
checks did not establish the failing installed preparation path.

Read the exact protected traceback and collect fresh closure before attributing
or correcting the failure. The source order puts a query before WORK creation,
but original exception attribution awaits saved evidence. All17 success-dependent
native/rootless/negative/supplemental templates and binders remain inert.
Checkpoint77 `.scratch/web-006-source15-current-state-v77.json`,
fa8808a4ed8291ba9de86dbffc4395f1dc24771a9ec53e30641e0f1cb21d979e/185176,
records both actual outcomes and1361 unchanged source hashes/modes. Installed
acceptance remains pending; production is untouched.

The separate fixed saved failure getter17 passes0/1.242416s,
child3243545/start417799264 reaped/absent. Local4fd3e436/105306 closes8 local/
all guest captures; all6 readonly queries return0/reap. Root14 checks pass
0skip3.00s and8 actual held inputs/56275B quoted source validate. Actual13
closed traceback frames end at save_private_channel238 with errno2, through
retain_channels/finish_label/collect/manager_rows/strict_quiet/drain_proof.
The exact retained source puts drain before WORK creation. A real owned-child
regression reproduces the defect and passes with WORK first (root3/0skip1.67s).
Independent actual review4b5a0c93/13282 joins the original source and trace.
This diagnoses the preparation harness; no application startup occurred.

WORK17/public17/control18/generations18/sudoers17 and their success artifacts
are absent. Current3/key and13 role snapshots remain equal,53 historical pairs,
original query97777 and7 cgroups are gone. No endpoint connections or original
main replay occur in this getter. Its protected plain diagnostic RESULT is
expected83b8aa70/94141; inode/SID await first held read. Original17 failure,
outer false closure, private captures and all success-dependent inert scopes
are preserved.

Select fresh unpublished18 UUIDe281b43d-c297-4d13-b0d5-403ab1935c01,
control19/generations19. Move only the owned WORK/state/input initialization
before the first query, correct stale selector-version literals to4/5 and
retain exact failed17/readback evidence. Three new same-inode current16 moves
and public/controller publication still follow successful strict drain. Reuse
PKI17/image/stages/source15/RO108 projection/browser183 tools. No renewal,
reinstall, original scope replay or production change is selected. Inert native18
and typed post18 templates pass92 root checks0skip5.03s; future operational pins
remain unbound. Checkpoint78 `.scratch/web-006-source15-current-state-v78.json`,
3f3b4c938d535f6da16663daebed2e3372cc5472236ceb390406e03d3d0c4d76/108320,
records actual diagnosis/closure and1361 unchanged source hashes/modes.

Original donor18 transfer passes0/1.424621s, child3257159/start418430321
reaped/absent. Local0714aac6/200291 closes15 local/all guest captures and6
queries return0/reap. Exact protected donor source3433c968/98310,
inputsc89db31e/4324 and controller775e31c9/111880 are root0600/usr_t,
inodes84721763/43376840/84721764. Failed17 diagnostic83b8aa70/94141 is first
held at inode34987233/root0600/usr_t. Root17 donor checks pass0skip5.49s,
with15 actual FD preflight,286085B stdin and51381B quoted source. Existing
UID983 processes, current3/key, old failures and all dormant services remain.

Original preparation18 then fails1/6.731444s,
child3257750/start418450873 reaped/absent. Local29d875fc/62771 retains outer
ValueError/false closure and inner ValueError/failed result. Protected authority
RESULTb3e5acdc/43053 inode101765253 and collection3f9eefca/34478 inode94416553,
stdout28727B and stderr1868B remain. All6 queries return0/reap, donor holds and
original FD sets/limits close; final observers report no secondary/revalidation
errors. No roles start. Root51 core checks pass0skip5.47s,28 safe checks
0skip4.01s and5 actual FD/codec preflight; these did not establish installed
preparation acceptance. Earlier copied test namespace assertions are retained
as model failures, not guest results. Parallel agents reached their usage
limit; root continued from saved sources and test evidence.

The actual partial result records two completed NOREPLACE same-inode moves:
selector60292852 to WORK18/original-native16-selector and deployment78462608
to WORK18/original-native16-deployment.json. Only their owned ctimes change.
Original current/deployment paths are absent; policy78462609 remains present
and unchanged. The strict final13 roles/54 historical pairs/7 cgroups and5
endpoints close/refuse. Preserve both completed moves and the remaining policy;
never replay the preparation, recreate those current paths or repeat the moves.

Read the exact saved traceback and inventory partial WORK18 before correction
or a fresh namespace. Source audit identifies an enriched preservation mapping
passed to hold_record, whose whole-record equality expects its fixed capture
schema; original exception attribution awaits saved evidence. All18 success-
dependent native/rootless/post/negative/supplemental templates and binders remain
inert. Checkpoint79 `.scratch/web-006-source15-current-state-v79.json`,
553951b768104c82d3c187046b7cfdca2574aff0017c1a5e68add26f77c5099a/79863,
records both outcomes, partial moves and1361 unchanged source hashes/modes.
Installed acceptance remains pending; no production effect occurs.

The separate saved18 partial-failure getter passes0/1.129353s,
child3259550/start418523543 reaped/absent. Locald11003af/120700 closes8 local/
all guest captures;6 readonly queries return0/reap. Root15 checks pass0skip
2.91s,63414B quoted source/8 actual FD preflight and Ruff pass. Actual8 closed
frames reach preserve_selection1012/hold_record590/need94. Exact source and a
real owned-file regression establish the mapping-shape defect: enriched move
provenance was passed to a verifier expecting only the fixed capture schema.

The getter measures exactly16 retained WORK18 nodes: INPUTS/RESULT, twelve
private query channels and preserved selector/deployment. Both moved inode/
context/hash identities remain exact; current/deployment paths are absent and
policy/key metadata unchanged. Before/after strict13 roles/54 earlier pairs/
7 cgroups and all6 preparation-query identities close. Canonical staged units
exist and remain inactive; no application starts or18 public/control19/gen19/
sudoers18 publication occurs. Two child locators beneath the absent public18
parent retained v17 filenames; only their parent absence establishes absence
of all children, not an individual18-name query. No additional getter is needed
to infer that closed absent-parent fact.

Protected plain diagnostic RESULT is expected6a139b69/108557; no inode/SID is
invented before a separate held read. Checkpoint80
`.scratch/web-006-source15-current-state-v80.json`,
4cf40af65823848825854d7a03625d37ad64f21356fb4ba850dbff8a8c75848e/121060,
records actual trace/inventory/closure and1361 unchanged source hashes/modes.
Its phrase about installed roles means no roles started; the explicit
clarification `.scratch/web-006-source15-checkpoint80-clarification-v1.json`
retains the original checkpoint and distinguishes staged inactive units.

Next is a fresh reviewed namespace consuming both completed moves as immutable
history and preserving only the remaining policy after fresh strict drain.
No new authority is yet bound/published, no old move is replayed and all18
success-dependent scopes remain inert. Reuse PKI17/source15/image/stages/tools;
installed native/rootless/negative/fault/secret/drain acceptance remains pending.

The first19 donor validation fails1/0.837019s before publication or queries,
child3262346/start418639278 reaped/absent. Localdd72275c/9966 retains outer
ValueError/false closure and inner TypeError, commands[]/no work-created flag.
Source review and an added real-helper regression identify the new consumer's
tuple/record mismatch; no original traceback was saved for this TypeError.
The original receipt/source remain intact. Distinct v2 paths are used, with
explicit absence guards for v1 donors/input/work and unused authority19 paths.
This does not retry any completed move or application operation.

The v2 donor transfer passes0/1.387606s,
child3263086/start418669817 reaped/absent. Local3dc1ab63/241587 closes all17
local/guest captures;6 queries return0/reap. Exact protected donors are
source61929bee/106750 inode4219065, input6fb85287/5693 inode43376841 and
controller20 41a05137/111918 inode4219066, root0600/usr_t. All16 partial18
nodes remain retained. Saved18 diagnostic6a139b69/108557 is now actually held
at inode109909793/root0600/usr_t. Root45 checks pass0skip3.31s, including
real helper ABI, policy-only inode/collision, history and guard regressions;
17 actual FD/299213B payload/52857B quoted-code preflight and Ruff pass.

The first authority19 preparation passes0/7.847495s,
child3263605/start418690647 reaped/absent. Local9e767ec2/842522 closes all5
local captures, all3 donors and all held preparation inputs, restoring original
FD sets/limits. All8 commands return0/reap; installed validator and controller
load-equality pass. Protected authority3a989a11/710034 inode10079898 and
collection63f80bfa/534281 inode4219070 are measured root0600/usr_t. The only
new move is policy78462609 into WORK19; selector60292852/deployment78462608
remain under WORK18. One new move +two completed moves consumed gives three
preserved objects, with no replay and all current aliases absent. No roles start.

Fresh UUID2be9f2e1-f308-4799-883b-43fbaf791dc6 publishes control20
5253d158, manifest19 cf869fa2, controller20 41a05137 and runnerbe83a031.
Only these genuine readiness hashes may bind original native19 acceptance.
PKI17/image/stages/RO108 projection/browser183 tools, master key, kernel and
all old failures stay retained. Checkpoint81
`.scratch/web-006-source15-current-state-v81.json`,
d4e621c42e3c748cd170f55b2b211f467492c3440e8990e5d7d9c79672dc4b2a/907711,
records actual outcomes and1361 unchanged source hashes/modes. Original native19
has not run; all18 successors remain inert and installed acceptance is pending.

## Checkpoint82 — original native19 failure and independent closure

Original native19 actually exits1 after15.830631s, child3265786/start418775424
reaped/absent. Local323e8308/21865 retains outer ValueError/false closure;
inner inputs close, original runner98307/start19658754 exits1/reaps14.911079s,
no SUMMARY exists. All five commands0,0,1,0,0 reap. Protected original result
c5431fd0/11485 inode43376855 and collectionf95e329e/16518 inode34987237
remain root0600/usr_t. This is failed functional acceptance; no replay occurs.

Separate strict post19 passes0/0.759668s,
child3265967/start418780615 reaped/absent; local326c23fb/49107. Actual
fresh generation aa42bccc61844aaf82dad733aac11520/state0a4e74f1/36415
inode27220520 is first observed without invented pins. PKI17 prestart passes,
first authenticated TLS bootstrap200 validates exact assets/instance, and
native983/983/982/0 cohort identities pass. All28 generation pairs plus five
original commands are gone,13 roles inactive, four cgroups empty and five
endpoints refused. Original failure remains failed; startup proof is not full
feature acceptance.

Separate saved public readback passes0/1.425955s,
child3266964/start418816746 reaped/absent; local4ed01161/54599. Saved ready,
runtime and browser-input pure checks pass; original RESULT cleanup_unknown
is false, ready present, all browser modes absent. No normal browser intent,
proof, launcher receipt or report exists. Browser source c0a563ff/45557 and
checker7af9b0ba/33990 are held exactly. No engine or application is called.

Separate actual UID1000 file-input validation also passes0/1.966425s,
child3267432/start418834420 reaped/absent; local41b341db/57078. Its actual
unprivileged reader98637/start19717812 exits0/reaps0.601227s, no engine or
browser call. Root source/ownership checks pass102+12+8+8 tests, zero skips,
with actual4/8 FD preflights and exact codec checks. Initial stale model/count/
path assertions and a negative model that repinned modified bytes remain
retained in original XML; corrected models pass without changing product code.

Checkpoint82 `.scratch/web-006-source15-current-state-v82.json`,
052976b6cdda4504e33898d88652d7d664275b2bc48740a9fb9647266e4b60a9/206135,
records all actual results and1361 unchanged source hashes/modes. Diagnose the
remaining original browser-launch boundary with read-only checks; no original
browser exception/sole cause is claimed. All19 success-dependent scopes remain
inert; native/rootless/negative/fault/secret/drain acceptance remains incomplete.

Checkpoint82 phase-name correction2026-10-22: the collector checked `normal`,
while the actual checker starts with `baseline`. Its missing normal-named files
do not establish that no browser started or no baseline evidence exists. The
independent launch readback e86fb00d/58090 passes collection but its synthetic
normal request is rejected by input_bundle before an engine call. That is not
an original browser exception. Original native19 remains failed; corrected
baseline evidence/closure readback is next. Original receipts remain unchanged;
`.scratch/web-006-source15-checkpoint82-phase-clarification-v1.json` records
this interpretation correction. No functional acceptance or replay is claimed.

## Checkpoint83 — saved baseline create refusal and exact closure

The corrected baseline readback passes0/2.624919s,
child3269337/start418912492 reaped/absent; local068ee9a3/61038. Actual
baseline intent/proof exist, no report/launcher receipt exists. Original
creation fails at the create phase; saved proof retains drain_unknown. The
separate actual UID1000 full preflight with baseline reaches the pre-browser
boundary and verifies the trusted image, without creating a container.

Create-read v1/v2 refuse a new consumer passing a full process identity into
the strict two-field positive_pair helper. Original aa94dc61/49144 and
bfe9da0b/57716 remain failed, with children3269910/start418935648 and
3270218/start418945186 rc1/reaped/absent. V2 retains the exact safe failure
frames and partial readback. A new v3 projects only pid/start_ticks before
that unchanged helper; a full-record regression covers the actual shape.

Create-read v3 passes0/2.765034s,
child3270385/start418950625 reaped/absent; local33be2d1a/67751.
The retained credential-free create stderr is131B,
498d0af4c993c9589a1d14eee7bb584f5789ccee556e3b909851a6b75e5dbe84:
Podman6.1 rejects `--stop-timeout=-1` as an unsigned create argument, rc125.
Its original CID file is absent, original three Podman PID/start pairs are
gone, and a separate exact-container-name `exists` query returns1. Trusted
image inspection returns0; both read-only engine children reap, as does
actual reader98845/start19834014. No original browser invocation is replayed.
The original saved drain_unknown remains unchanged; fresh closure is distinct.

Root9 launch/15 baseline/13 final create checks pass0skip; actual eight-FD/
codec, documentation207human/27helper and whitespace checks pass. Initial
phase-name/model mistakes and readback failures remain retained. Checkpoint83
`.scratch/web-006-source15-current-state-v83.json`,
d4416a161d7420aa89c682a6fe5a4ee9b0fc7c416d387753c860c7a716645a97/268806,
records actual results, interpretation correction and1361 unchanged hashes/modes.

Fresh unpublished20/control21/generations21 intent UUID
8c193b89-824f-49c8-998f-4365912284e6 removes only the unsupported browser
create flag, retaining explicit `podman stop --time=-1`, security, EOF/reap and
original-handle semantics. It must preserve the three NEW native19 aliases
once and retain all older completed moves/failures separately. Controller21
fdac4740/111918 is locally derived by two global data bindings only; no method
or guard changes. No authority20 or application is published/started yet.
Installed native/rootless/negative/fault/secret/drain acceptance remains pending.

## Pending checkpoint84 — fresh20 first donor validation refusal

Reviewed fresh20 source aef103db/128392 passes64 tests0skip; browser binding
passes26 checks and native20/post20 inert templates102 plus independent review.
Controller21 fdac4740/111918 changes only two globals. Root data binding yields
source b58a66f4/128497 and inputs13efb9f0/7787, with only3assignments changed;
actual21-FD donor preflight75a56bdf/15053 closes all localinputs and codec limits.

The first fresh20 donor attempt actually exits1/0.976448s,
child3273641/start419052636 reaped/absent. Local
`.scratch/web-006-authority20-three-donors-v1-result.json`,
f4a8e6c3d5c023abc96da5c5e0ed308930fc51f18f58b65f90bec573907f34d9/12031,
retains outerValueError/falseclosure and innerValueError/commands[]; partial
contains held revalidation failures[] and no work-created flag. No donor or
application publication/start is recorded. Exact read-only consumer/identity
failure diagnosis is next, preserving this refusal. No validation failure is
promoted to acceptance. A separate static review also identifies a later core
PUBLIC19 manifest/protected-input filter mismatch; that does not establish the
first refusal's cause. A distinct unpublishedv2 source/input/donor correction
is being prepared; all native20 acceptance remains inert.

Fresh20 separate read-only diagnosticv3 exits1/0.993846s,
child3275583/start419116967 reaped/absent. Local
`.scratch/web-006-authority20-donor-readonly-diagnostic-v3-result.json`,
aaebc243b9241bd62a66d3f6be31fd2b6cee99285a1a72ee313eeb66f8f38436/16942,
records all32 pinned captures succeeded, then ValueError in native19 history
consumer. All held inputs rejoin/close; all8 unused future names remain absent;
no queries/publication/app effects. Its first_failure remains null because the
new projector assumed __file__ exists under actual python -c. The original
ValueError is retained; v4 adds a real code-mode regression and per-input
boundary observation. Static actual98-prefix review finds exactly one retained
17,725,440B tar above the new caller4MiB cap, a candidate not yet exact cause.
A separate real owned sparse-file capture regression proves the cap mechanism;
proposed per-record original-size checks retain the existing128MiB ceiling.
No generic limit, product source or original receipt is changed.

## Checkpoint84 — exact reproduced old-prefix size refusal

Separate read-only diagnosticv4 passes collection0/0.960287s,
child3276332/start419143473 reaped/absent. Local
`.scratch/web-006-authority20-donor-readonly-diagnostic-v4-result.json`,
ee7130cc625e9f838886148f7ddbf34a0b83c72a6130e4c3e3c8ffdba1085894/99023,
closes all21 local and guest inputs, preserving first ValueError as data.
All32 pinned captures pass; safe frames identify consume_native19_history1488,
hold_record588 and captured141. Last of95 instrumented holds is exactly the
original source-v15-fixture.tar, SHA51dcdf3bed2f80597f07f3b4cb6c2f11b41109fe1ae47bfa79ade7455319e9d2,
inode52243925/17,725,440B, requested at the new4MiB cap. The observer reads
no body, preserves the original request, restores the helper, and has no errors.
All8 unused future paths remain absent before/after; no queries, publications,
role actions or moves occur. Original first donor failure is not promoted, and
its own unsaved traceback is not claimed to have been recovered.

V4 fixes only diagnostic code-mode __file__ handling plus the observer; real
code-mode and boundary regressions pass15/0skip2.27s. Exact21-FD preflight
b4366d80/11887 passes with transparent ctypes runtime initialization before
baseline; no owned descriptor is closed or masked. Earlier donor/diagnostic
failures stay unchanged. Real owned17,725,440B sparse-file and actual98-prefix
regressions pass10/0skip1.70s; exactly one original input exceeds4MiB.

Checkpoint84 `.scratch/web-006-source15-current-state-v84.json`,
d4f8898add6cf558642c881bf04518ffd4f626dd0ddfaaa560020a92784d9394/145785,
records actual evidence and1361 unchanged source hashes/modes. Distinct20v2
source/input/donors will validate exact original98-prefix metadata/order and
use each fixed original size within the unchanged128MiB inherited ceiling;
new small inputs remain4MiB. It also excludes the two captured public manifest
records from protected control inputs while retaining provenance. No generic
bound, product source or security policy is widened. Fresh20 preparation and
native20/rootless/negative/fault/secret/drain acceptance remain unperformed.

## Checkpoint85 — genuine fresh20-v2 preparation

The distinct donor20-v2 transfer and first authority20 invocation pass0 in the
owned guest. Original donor20-v1/native19 failures remain unchanged. Donor
execution3278236/start419218310 closes in1.669892s; six fixed queries return0
and reap. Preparation3278404/start419223346 closes in8.058743s; eight commands
return0/reap, installed validator and controller load pass, all held inputs
rejoin/close and the original descriptor set/limits restore. Three new native19
selection/config/policy objects move once; all older completed moves stay
retained. No application/helper roles start and no feature acceptance follows.

Actual local preparation4e14af22/896142 pins protected authority2837f67a/754283,
control21 3867ddc9, manifest20 485d4ffa and unchanged controller21 fdac4740.
Protected collection81391404/563992 closes. All1361 frozen source hashes/modes
remain exact. Checkpoint85 `.scratch/web-006-source15-current-state-v85.json`
SHA2566da432ea5ecdbaa7cafc3644d8892cd8ddf86e02b705b9f6eb45cacadf0b0e70
records actual receipts and bindings. Focused core80 and transport38 tests have
zero skips; these are preparation checks. Next bind/run native20 once and collect
a separate strict post-run readback, then rootless/negative/fault/secret/drain
acceptance. WEB-006 remains incomplete; no production/NAS actions occurred.

## Checkpoint86 — original native20 failure and strict closure

Original native20 returns1 after23.335694s, runner99119/start20126227
returns1/reaps after22.410279s with no SUMMARY. Local45380e24/21861 retains
outer ValueError/false local-closure flag and inner inputsclosedTrue/errorNone;
no original failure is promoted. Protected original0944b673/11482 and
collection242a7397/16514 stay retained. The cause is not yet observed.

Separate strict post20 passes0/0.763647s (3279773/start419254972), local
bd597af2/49106. It observes generation3d834d0d061e460fbefcef642cb7aec0,
state51434c99/36415 inode52242142, protected post canonicalc1d6385b/41206.
PKI17 prestart guard, first authenticated TLS bootstrap200 and all four native
role principals pass. All28 generation handles and5 original commands are
gone;13 fixed roles inactive,4cgroups empty and5endpoints refuse. This is
closure evidence, not functional acceptance. New current native20 selector
inode60314828/deployment78462639/policy78462640 remain present; original key
metadata unchanged/no body or digest read. No replay or production change.

Checkpoint86 `.scratch/web-006-source15-current-state-v86.json`, SHA256
6f0a430b1f6565a8b364f883068b179550922d55d7e057e28c2614d19828e29e,
retains actual receipts/identities;1361 source hashes/modes remain exact.
Root126 focused checks and12 actual-source binder models pass0skip; docs207/27
pass. All20 success-dependent scopes remain inert. Read original saved baseline
intent/proof/report and credential-free bounded diagnostics next. WEB-006 and
its installed native/rootless/negative/fault/secret/drain acceptance remain open.

## Checkpoint87 — saved create success, browser drain still unknown

Separate saved20 reader passes0/1.436171s (3282222/start419326315), local
f5f7e639/63554. All8 local captures and held guest inputs rejoin/close; pure
saved ready/runtime/browser-input checks pass. Original baseline create returns0,
empty stderr, stdout65B and exact64B CIDfile. Original container ID is
`a43d3eef92e385ae2864ee7cffdb150a6847b7830a8c47a5dac0e1efa4fd2ae6`, name
`web006-ui-baseline-0278bbe952904d9db3e41615014fd143`. Its report and launcher
receipt are absent. Saved proof records start-attach ValueError at actual browser
line1123/reject74, drain_unknownTrue/container_drainedFalse/init_closedFalse.
Six original engine handles plus attachment99321/start20128271 are gone.
The application generation's cleanup_unknownFalse and the browser's separate
unknown proof are both retained; neither substitutes for container closure.

This reader makes no engine query or application/browser start and exports no
private browser messages/responses or credential body. Saved create stderr is
separately credential-free/bounded and empty. Actual container state and original
startup cause remain unobserved; no fresh preparation is authorized by this
collection pass. Next inspect only exact original CID with label/image joins,
retain raw inspection privately, and read pinned browser source to locate the
actual predicate. No start/stop/replay/secret retirement.16 focused models and
Ruff pass; source1361 remains exact. Checkpoint87
`.scratch/web-006-source15-current-state-v87.json` SHA256
b811253914ba71002d9b5bfefa59d117241dc686f902f84822980713fcc36037 retains
full actual evidence. WEB-006 installed acceptance remains incomplete.

## Checkpoint88 — exact original container inspection

Separate inspection20-v2 passes0/1.871089s (3284298/start419394741), local
0e8bbb21/131031. One exact original CID query under UID1000 returns0; the
reader99508/start20278137 and engine99510/start20278150 reap/are gone. Actual
CID/name/image/three ownership labels join. Current state is created, Running
false/PID0, no current init. Its312-character private OCI error projects only
permission-denied and SELinux categories; Config.Env and raw messages are never
exported. Raw30258B inspection stays in the labelled private40921B child channel.
The original saved final projection is also created/PID0; original drainUNKNOWN
is retained. No stop, start, replay, deletion or policy/security change occurs.

Actual public browser source45528B/de0748f9 is captured and locally pinned.
Its1123 rejection is the terminal drain predicate requiring exited/stopped and
an observed closed original init. That identifies the drain refusal, not the
SELinux startup action. Next parse only the existing private State.Error with
fixed vocabulary/context identifiers, without another engine query or credential
body read. All8 local/guest inputs close;38 focused tests/Ruff and207/27 docs
pass, source1361 unchanged. Checkpoint88
`.scratch/web-006-source15-current-state-v88.json` SHA256
e8a9f4ece42da358b9f8a048ac756fbaa2df84f2b2aecb3c195ae55726822cec records
actual evidence. Original20 native failure and browser unknown remain unchanged;
all20 success-dependent scopes remain inert and WEB-006 incomplete.

## Checkpoint89 — bounded private relabel-error projection

Separate error20-v2 reader passes0/1.434751s (3286188/start419461369), local
42f64e1d/66043. It holds the exact protected inspection/private wrapper, rejoins
CID/name/image/three labels before Error access, and captures no Config.Env or
arbitrary message/path output. The312-character error yields only fixed words
label/change/selinux and validated object context
system_u:object_r:container_file_t:s0. These are literal diagnostic matches,
not kernel-causation proof. No engine/UID child query, relabel, policy/permission
change, browser/application start or replay occurs; all held inputs close.

All1361 source hashes/modes remain exact.33 focused models/Ruff and8FD/codec
preflight pass; earlier unexecuted missing-import draft/RED test evidence is
retained and corrected v2's valid-wrapper path passes. Next join saved error
only to fixed original volume-source literals and metadata; do not let error
text select an arbitrary filesystem path. No startup correction is selected yet.
Checkpoint89 `.scratch/web-006-source15-current-state-v89.json` SHA256
a37da608abd5e20bc0c09549d604609eda62ded71f22ef19264683f3250d2094 records
actual evidence. Original native20 failure/browser drainUNKNOWN remain unchanged;
all20 successors inert and WEB-006 installed acceptance incomplete.

## Checkpoint90 — exact CA relabel target and isolated correction test

Saved error20-v3 reader passes0/1.429033s (3288107/start419526951), local
f9178fc3/70360. Exact captured producer/list AST reconstructs the original
45022af3 create argv; all11 volume entries join the pinned manifest/browser.
Only the public CA selector (indexes5/6) matches the retained error. Fixed words
include lsetxattr/operation/permitted/label/change/SELinux, target object context
system_u:object_r:container_file_t:s0. Matched CA is root:root0644, inode4219062,
1574B, unchanged unconfined_u:object_r:user_home_t:s0. Contents are not read or
copied by this reader, no arbitrary path/message is exported, and no engine
query, application/browser run, policy or label change occurs. Original failure
and drainUNKNOWN remain unchanged.

Select a separate public CA copy with identical pinned bytes/hash, root ownership
and0644, labelled container_file_t:s0 before bytes. Preserve the original CA and
all PKI/control/tool inputs unchanged. Then test only this new copy through a
uniquely named/labelled, gated UID1000 readonly/network-none/capless/NNP prototype
using the original trusted image/engine. Observe its original init before release,
read the public CA once, and prove EOF/reap/exitedPID0/cgroup closure. No existing
container is retried, stopped or removed; no label-disable/policy grant/ownership
weakening is selected. The prototype/publication have not run yet.

Podman6.1's [shared relabel source](https://github.com/containers/podman/blob/v6.1.0/vendor/github.com/opencontainers/selinux/go-selinux/label/label_linux.go#L112)
normalizes shared labels to s0; the [recursive labeller](https://github.com/containers/podman/blob/v6.1.0/vendor/github.com/opencontainers/selinux/go-selinux/selinux_linux.go#L1126)
skips an already matching full context. This supports the proposed primitive;
it does not establish actual fixture acceptance.59 focused models/Ruff and8FD
codec pass, source1361 exact, docs207/27 pass. Checkpoint90
`.scratch/web-006-source15-current-state-v90.json` SHA256
b93fad03828ca0e7d590f9d59a7da56286a4ee4c3408c665dfac798ef0c9e020 retains
actual evidence. Fresh21 and all installed application acceptance remain pending.

## Checkpoint91 — separate public CA publication passes

Separate public CA publisher guest-v3/caller-v4 passes0/0.778094s, original
child3292501/start419672541 reaped/absent, local e80fec08/54698. Exactly one
new public directory and CA are created: prototype-v3/ca.pem inode94423687,
root:root0644,1574B, SHA1dbeeac8, full context
system_u:object_r:container_file_t:s0 verified while size0 before writing.
Old CA inode4219062 full9/SID/bytes and all public PKI/unit files remain equal;
private keys are metadata-only and unchanged. Both manager queries return0/reap,
strict original application closure remains true, and all held/local captures
close. Observed provisioning-parent transition is recorded for the next scope.
No application/container starts, old object relabels or key body/digest reads.

The original native20 failure/browser drainUNKNOWN remain unchanged. A separately
named gated UID1000 read-only CA probe is next; its actual invocation and fresh21
application acceptance remain pending.16 local publisher tests and independent
16 tests pass0skip, including actual-producer classification, real8FD closure,
first-error preservation and umask077. All1361 source hashes/modes remain exact.
Checkpoint91 `.scratch/web-006-source15-current-state-v91.json` SHA256
2290ca106e4a10b75aff03b5a151c65a469cd512f88f866e8efea96691a8da10 retains the actual receipts. No production/NAS changes.

## Checkpoint92 — actual gated public CA-read primitive passes

Original new CA-read probe passes0/7.196839s, local3295174/start419753678
reaped/absent; local result5f4ec55a/65526, protected0964b704/56202.
UID1000 collector99724/start20636988 returns0/reaps. New container0cc347c7
has invocation03a3fbee and the exact trusted image. Original init99762/start20637539
is observed before GO with UID1000, cap0, NNP1, seccomp2 and full subject
system_u:system_r:container_t:s0:c341,c623. The natural cat reads exactly1574B,
SHA1dbeeac8, stderr0; attachment99741/start20637506 reaches both EOFs/reaps.
Container exits0/PID0, original init disappears and its exact cgroup scope is
absent. All5 engine CLI handles are reaped/closed; no late/overflow/interruption.
Old/new CA and public browser full9/SID/bytes remain equal; all held/local
captures close. Only the new workspace is added to .scratch, with its exact
parent transition retained. No auth input, stop, signal, historical CID action
or replay occurs.31 wrapper and56 strict-child local tests pass0skip, independently
repeated31/56; source1361 hashes/modes remain exact.

The wrapper's original application-role closure is explicitly BEFORE this new
probe. A separate finite public-mount/ROOT/provisioning/scratch inventory and
fresh strict post-probe application closure are next. Their completion, fresh21
publication and all installed UI acceptance remain pending. Original native20
failed/drainUNKNOWN stays unchanged; the primitive is no application success.
Checkpoint92 `.scratch/web-006-source15-current-state-v92.json` SHA256
39715cf9e382442351e6ebd8ca4ee597922313d8fb356b949844d6e987148aeb retains actual receipts. No production/NAS changes.

## Checkpoint93 — fresh post-probe closure and actual public inventory pass

Separate post-probe inventory passes0/1.272390s, root3298645/start419867956
reaped/absent; local e58ee3b7/347659, protected canonicalc977c895/322417.
Original executor stdout/source/completion joins pass before SSH. Both new
manager queries99839/start20751233 and99840/start20751253 return0/reap. Fresh
strict original20 closure is measured AFTER the completed CA probe:13roles
inactive,28generation+5command handles gone,4cgroups empty,5endpoints refuse.
All8 original probe handles are freshly gone and its exact scope is absent.

All230 finite old public-tool nodes are unchanged full9/SID:45directories and
185files, all root:root and unconfined_u:object_r:user_home_t:s0. The185 files
sum144525705B; canonical historical hashes exist but this inventory reads/hashes
no mount bodies. Old manifest20 is also root-owned/user_home_t. All3 fixed code
directories and7 files are UID/GID1000 (directories user_home_t/files usr_t).
Both CA metadata records, original20 output/gate and current ROOT/scratch/
provisioning inventories close/rejoin; ROOT records exactly its own WORK addition,
now467children.556additional FD bound fits soft1024, hard524288 unchanged.
No engine query or container action occurs.55 focused/inverse-binding models,
14 runtime+own caller+QEMU17FD preflight/codec87620 and independent bound review
pass; all1361 source hashes/modes stay exact.

Select byte-identical PUBLIC copies of185tool files/45directories into a new21
scope, with every new empty object prelabelled container_file_t:s0 before
bytes/entries; preserve old tools/CA/PKI/current objects and all historical
receipts. New manifest21 also needs empty-inode prelabel. Fresh21 current ROOT
transitions, aliases and all data bindings are under local preparation only;
no new tool copies, authority or application run have occurred. Native/rootless
installed acceptance remains pending and native20 failed/drainUNKNOWN unchanged.
Checkpoint93 `.scratch/web-006-source15-current-state-v93.json` SHA256
edcbe85722c6c036e6084a824211f7a62879549f073940cffc983c01a3830d22 retains actual receipts. No production/NAS changes.

Fixture-only source-preservation refinement2026-10-23: core20's
`verify_source_history` requires all1361 public and protected source files to
retain full9/hash/context. Mounting the original7 UID1000 codefiles with :z
would change those labels. Select7 identical prelabelled public code copies
and3 directories under the new tool scope, keep original source validation,
container targets and Node argv, and narrowly change only mount sources plus
copy validation. The new copies/authority remain unpublished and require
independent AST/model review and genuine preparation. No product source or
security policy changes; original source metadata stays an acceptance condition.

## Checkpoint94 — exact readonly raw inputs and closure pass

Original fixed-three read-only capture passes0/0.576135s: executor3307527/
start420145390 and SSH3307528/start420145397 return0/reap/are absent. Actual
local receiptc59272d7/116546 retains three private base64 bodies; no raw body is
printed to tools or copied into human docs/checkpoint. Exact control20=26900B,
manifest20=4940B and original generation20 state=36415B match recorded hashes,
full9 and full SID BEFORE reading, and rejoin before every descriptor closes.
The held ROOT full9/SID and467-child set remain unchanged. No guest workspace,
file publication, engine/manager query, controller call or service action occurs.
Original stderr is empty, original stdout275B is an explicit local summary,
and exact captured guest/caller/transport/owned-QEMU identity joins pass.

Root25 and independent25 fault/real-FD models pass0skip; lint and6FD/owned-QEMU
preflight/113447B fixed codec pass. Earlier local v1/v2 failures remain retained
and unexecuted. The final helper closes all FDs and preserves the first error
through body rejoin, later context failure, interrupted fstat/sleep recovery
and local writer construction/publication; remote failure classes remain data.
The full local adapteraddb9f23/4906 now verifies all25 intended input bodies
and actual original getter closure; future donor paths remain unpublished.
All1361 canonical source hashes/modes stay exact, source15's strict gate and
pinned UBI10 micro runtime image remain the applicable product evidence.

Fresh21 composed preparation/transport admission is being completed against
these actual bodies. Separate empty-inode-prelabelled public tool/code copies
and new manifest remain unpublished; no application is replayed or started.
Native20 stays failed/original browser drainUNKNOWN. Native/rootless installed
UI/helper and negative/fault/secret/drain acceptance remain pending. Checkpoint94
`.scratch/web-006-source15-current-state-v94.json` SHA256
13c7c307d9e98bc5f826b7bc9a66549755422fe928b5428414fd5132d1a2531d retains metadata/provenance only. No production/NAS changes.

## Checkpoint95 — original fresh21 donor transfer passes

Original fresh21 donor transfer passes0/1.674933s, executor3311064/
start420234458 reaped/absent and SSH3311067/start420234483 returns0/EOF/reap.
Local e124fa4f/447706 joins exact originalstdout08323197/287546 and empty
stderr; all15 local runtime inputs rejoin/close. Protected donated collection
`/opt/hfcache-web006/fresh-authority21-donors-v1/transport/RESULT.json` is
root0600/secret_t, inode78478720, SHAa0d13585/391940. All11 objects (core,
controller, inputs and8 helper/components) are admitted exact bytes/full9/SID.
The runtime ROOT observer records only DONORS467→468 then INPUTS468→469;
new transport WORK is nested inside DONORS. All6 fixed before/after queries
99989/21117760,99990/21117777,99992/21117782,99993/21117803,
99994/21117820,99996/21117826 return0/reap, fixed roles/current metadata stay
as recorded, key is metadata-only. No authority, application or helper starts.

Concrete local corea0cb38bb/43562 and inputsf48a9900/5835 changed only two
static assignments; runtime source/parent/component handoffs stay unbound
until actual owned caller admission. Full25actualbody core35 and composed162
checks pass. Independent transport32/channel-failure/prepared→safe→native
admission models pass0skip, separate safe-wrapper4 realchildren pass. Donor
binding changes only4 guest data constants/callerPINS; independent18FD/owned-
QEMU preflight closes exactly, payload485612 and quoted43856 stay bounded.
Core binding10checks pass after explicitly identifying the lockedPython3.14
ctypes runtime's one persistent self-interpreter FD (CLOEXECfalse, unchanged);
original9PASS1FAIL and local codec158856B failure stay retained/unexecuted.
No required real functional acceptance is supplied by these local models.

All1361 canonical source hashes/modes remain unchanged. Safe caller binding
now consumes this genuine original donor receipt/executor, before one original
preparation21 invocation. New public tool/code copies, authority21/control22
and application run remain unexecuted. Native20 failure/browser drainUNKNOWN
remain unchanged; native/rootless UI/helper/negative/fault/secret/drain proof
is still pending. Checkpoint95 `.scratch/web-006-source15-current-state-v95.json`
SHA256 5f21619d00a9c797d04f4b7e9c725d84ea70782cc89620e605c70f891b2cc441 records the actual evidence. No production/NAS changes.

## Checkpoint96 — original fresh21 preparation passes

Original owned safe caller/preparation21 passes0/14.772802s: executor3312353/
start420278430 and SSH3312354/start420278457 return0/reap/are absent. Exact
selfSHAac5c0cbc/124580 is captured and forwarded; local2ebc34eb/2152186 joins
originalstdoutd64f003a/1451758 and empty stderr. All local/guest captures and
both descriptor budgets close/rejoin/restore. Actual protected authority
`fixture-authority-v21/RESULT.json` SHA76091e01/1676853 inode94427202 and
private safe collection6b52e2b6/1444917 inode84866433 are retained separately.

The new50 directories and192 files contain185tool files/45dirs plus7code
files/3dirs/two roots,144525705+149087B. Every new object is labeled while empty
before bytes/entries; old tool/source/CA/PKI trees remain exact full9/hash/SID.
New manifest21 is prelabelled container_file_t:s0 before bytes. Browserde80d726
matches the independently reviewed49531B golden source, with copied mount
sources and original code targets/Node arguments. Source15 package/artifact
and pinnedUBI10micro runtime image bytes remain unchanged; no Node runtime or
second frontend server is introduced. New control22 SHA977a3ca9 and manifest21
SHA89adb78f load exactly with controller22; the original installed validator
passes. All8 commands100035/21161937,100036/21161953,100038/21161957,
100039/21162706,100040/21162742,100042/21162856,100043/21162874,
100045/21162880 return0/reap. Fixed role/kernel/source/projection/key checks
pass; no application or helper role starts.

Six older preserved moves remain held, and exactly the3 current native20
aliases are preserved once under WORK21 with same inode/allowed ctime change;
all current aliases are absent. Ordered136 protected parent inputs retain the
original98 prefix and128MiB recorded bound. Exact ROOT transitions account
for donors/input/safe/WORK/generations/control,467→473, and only2 new public
provisioning entries occur. No old native20 failure/UNKNOWN receipt is promoted.

Actual donor-bound safe codec116593/original120000 cap and16FD preflight pass;
separate full9/private0600 log completion closes the reviewer finding without
rebinding/replay. Root's first local complementary check used a relative path
and refused before effects; the corrected absolute-path full9 check passed
before the sole original call. Native21 binder-v2 independent27models and
actual four-receipt/source/executor/channel joins pass. Bound original native21
guest2c01aa63/26030 and callerd9cb447f/17716 remain unexecuted here; their source
binding receipt is0a99043a/9843. All1361 canonical source hashes/modes stay exact.
Checkpoint96 `.scratch/web-006-source15-current-state-v96.json` SHA256
eeb4a9619ba3eca357b84cff3a57e5f67e5cb2b382f94f1ddf98dae88d596e24 retains the actual evidence. Real native21 and strictpost21
are next; rootless/negative/fault/secret/drain acceptance remains pending.
No production/NAS actions occurred and WEB-006 remains uncommitted.

## Checkpoint97 — original native21 failure and strict post21 closure

Original native21 actually fails1/55.859822s: executor3313424/start420312313
reaped/absent; originalcaller d9cb447f/17716 and guest2c01aa63/26030 are held
and unchanged. Local865f7f38/21890 retains outer ValueError/false captureflag;
inner protected result ebcb7ba5/11501 inode118555017 has errornull/inputclosure
true. Its original runner100082/start21195603 returns1/reaps54.801902s, stderr62B,
stdout0, functionalfalse/noSUMMARY. The protected safe collection363fe45d/16543
inode109919804 and original private channels remain retained. No caller flag is
rewritten as passing and no replay occurs.

Separate actual strictpost21 passes0/0.773455s: executor3313999/start420327270
reaped/absent; local69987923/49187, protected canonical9cc9bbdf/41286. Twoqueries
101046/start21210534 and101047/start21210551 return0/reap; all local/guest
captures close. Exact generationf07593a444b147dca9d0bfae5e8508ea has state
8b60b445/36534 inode101772546 under generations-v22. All28 original application
processes and5 originalcommand handles are gone,13 fixedroles are inactive,
4 cgroups physically absent/empty and5 endpoints refuse. PKI17 guard explicitly
passes and the original authenticated bootstrap returns200 with asset/instance
checks; this does not establish UI/helper functional acceptance. Original browser
container evidence/drain and failure cause are unobserved pending savedreadback.

Current native21 selectors/configuration remain PRESENT and retained:
selectorinode60320036, deployment78478733, policy78478734. The earlier9 preserved
objects remain in their protected WORK18/19/20/21 destinations; do not replay
moves or assume currentaliases absent. All1361 canonicalsource hashes/modes stay
exact, with source15 strictgate/pinnedUBI10micro image stillapplicable. All21
success-dependent normal/rootless/negative/fault/retirement fields remain inert;
no fresh22 namespace/correction is selected or published. Concrete bounded saved
original21 diagnosis is next, without rawEnv/keybody reads or engine/service
replay. Checkpoint97 `.scratch/web-006-source15-current-state-v97.json` SHA256
81c02c021a6015f3d7699dd7f4ca3e7411ed41d36f601d9e42a95a455a248c70 records actualfailure and independent closure. WEB-006 remains
incomplete/uncommitted; no production/NAS changes or application acceptance.

## Checkpoint98 — saved21 diagnostic refuses structured JS failure

Original saved21 getter fails1/0.927157s: executor3315701/start420377950
reaped/absent. Local4c2804db/65864 retains outerValueError/falsecaptureflag and
innerdiagnosticValueError/falseinputclosureflag; protected canonicalba307c31/
57086 remains failed. Sourcegate25local+25independent, Ruff/system3.12/11FD/
codec89369 had passed; none establish actualcollectionsuccess. Twofixedqueries
101086/start21261214 and101087/start21261228 return0/reap; no engine/service
or browser action occurs.

Typed partial original evidence shows create0/stderr0, container`8cb515c5b7e7c99f029c94e9b9f942edf98d89c3897f112374c08116cffca995`,
invocation`0e0539917b55499e9461ae9e3ed828b9`. Originalproofbfa851f2/7728 reports container_drained,
init_closed and inputs_unchanged true, attachmentexit1/passedfalse and original
drain_or_evidence_unknown true. Originalinit100331/start21197567 andattach
client100309/start21197540 are freshly gone in the partialprojection, as are
six engineCLI handles. Report1e3f3422/71579 exists; launcherreceipt absent.
Savedfailurestagecopy-original-report/report_passedValueError remains data,
not a claimed primary UI failure cause or acceptance. BLOCKED marker107B and
originalcleanup_unknownfalse are retained; no rawcredential/Env/keybody is read.

The getter stops at project_saved_browser_report→project_js_failure expecting
text, while the exact source JS safeDiagnostic returns bounded{name,message}.
This is an observedcollector/producershape defect. A newv2collector is being
prepared against the actualsource shape, preserving allv1receipts and capturing
their exact source/completion before a separate readonly call. It will export
finiteerrorclasses/failedcaseIDs/counts, never rawmessage text or invented stack
frames. The original native21 failure remains unchanged; all dependent21
normal/rootless/negative/fault/retirement scopes stay inert and nofresh22 is
selected. All1361canonical source hashes/modes remain unchanged. Checkpoint98
`.scratch/web-006-source15-current-state-v98.json` SHA256
8ba65ed8d4f00afa22321650efa17d9a7dec1563623748e3099fcb37c12a46da records the failed diagnostic and partial evidence honestly.
WEB-006 remains incomplete/uncommitted; no production/NAS changes.

## Checkpoint99 — saved native21 facts identify driver exit mismatch

Corrected saved21v3 collection passes0/1.530224s, executor3319086/
start420482914 reaped/absent; local82db0b0a/80096, protected f9e27fac/65492
inode101774891. The originalfailedv1ba307c31/57086 inode94433382 is retained
as failed withfalsecaptureflags. V2candidate remains unexecuted. ActualNode
producer11 +25local/25independent projector tests,17FD/codec101798 andRuff/
systemPythoncompile pass; no rawdiagnosticmessage is exported.

After modelcapacity interruption and explicitcontinuation, a NEW original
readonly factsgetter passes0/0.842893s: executor3351402/start421976009 reaped/
absent, local0d8a2270/75929. Source41cddd5a/33173 andd6f73cc6/78199,17local+
17independent actualproducer checks,23FD/codec95734 andoriginalsource/stdout/
executor/SSH joins pass. Its fresh fixed2managerqueries/5endpointchecks andall
held local/guest inputs close. No application/browser/engine action occurs.

Firefox's original7cases have2passes:host-status-observed andhost-denial-ui-
reasons. The5 failures(basicHub/archive/control,forgedadminheaders,oldwriter)
each show exact finite actual10 versus expected2. ActualAPI AuthorizationError
and CLI§5.1 specify HTTP403/HFAPI002/exit10; driverassertProblem anditsfixture
incorrectly use2. Their source mapping identifies a testexpectation error;
production authorization/exitbehavior is preserved. Correct thedriver/fixture
and clarify thehuman API/troubleshooting references before a newsource gate.

Chromium has0cases, expectedversion156.0.8078.4 andverifiedsandbox,5trusted
network observations/noinvaliddestinations, but a236characterError beforehost-
statusassignment; cause remains unclassified. WebKit27.2 has0cases andoriginal
navigation/untrusted-certificate markers. Firefox157.0 passes hoststatus/UI.
All3 savedengines report browsers/descendantsclosed andnoforcedclose; namespace
PIDs are NOT joined as hostPIDs. The originalcontainerproof's UNKNOWN stays
unchanged. FreshoriginalCID-inspection/cgroupclosure remains pending. Source
trust audit shows imagebakedearlierCA, runtimecurrentNSS/Firefox CA, butno
system/GLib refresh; actualbakedstore/currentWebKitcause stillneedmeasurement.

The priorpure saved-browser-report check failed at importinghfcache.host_models
under guest systemPython without installedprofile prerequisites; it doesnot
prove reportinvalidity. Factsgetter labels that limitation explicitly. All1361
canonical source hashes/modes remain exact BEFORE theconfirmed harnesscorrection;
source15 strictgate/APIUIimage provenance remains original. All21dependent
normal/rootless/negative/fault/retirement scopes remain inert; nofresh22selected.
Checkpoint99 `.scratch/web-006-source15-current-state-v99.json` SHA256
c7fdbda4cc45377c25578098a4f213a79767125be656d6dfbab7a3da9fcbc84e retains actualevidence. WEB-006 remains incomplete/uncommitted;
production/NAS/livehistorical frontend untouched.

## Source16 candidate — correct the confirmed functional refusal expectation

The canonical host driver now requires documented `HFAPI002`/HTTP403/exit10
instead of2; its pure fixture uses10 and explicitly refuses the obsolete2.
The API and human troubleshooting references now state exit10 explicitly.
The actual five original Firefox10→2 comparisons and independent taxonomy
source audit established the trigger. API/service authorization behavior and
all108 Python package source leaves remain unchanged. `INV-006` and decisions113
and150 were reviewed; this restores their existing taxonomy contract, adding no
invariant, architectural decision or runtime dependency. Before-bytes/full9/hash
records for all4 edited files remain in
`.scratch/web-006-source16-harness-before-v1/RECORD.json`.

This is an unfrozen source16 candidate, not a passing new gate or installed
functional result. Source15's earlier strict gate/image retain their original
provenance. The two JavaScript files pass Prettier and documentation alignment
passes207human documents/27helpers; focused Node/backend/cross-language error
checks are running separately. Chromium setup and WebKit trust diagnosis plus
fresh original container closure continue from the saved native21 evidence.
No fresh fixture is selected, and the failed21 run/successors stay unchanged.

## Checkpoint100 — source16 freeze/gate and current original browser closure

Separate originalCID inspect21 passes0/1.251166s, executor3353991/start422055001
reaped/absent; local18d10522/130454. ExactoriginalCID/image/name/labels match;
currentState exited/exit1/PID0/OOMfalse. Originalrunner+init+attach+6engineCLI
identities are freshlygone; exactcontainer andnamedconmonsibling scopes are
physicallyabsent. Originalconmonhandle/location wasunrecorded and isnotinferred.
The originalbrowser failure/UNKNOWN remains unchanged. Readonlychild101532/
22938237 andengine101534/22938245 return0/reap; no start/stop/delete occurs.
76local/independentmodels,17FD/codec78479 andsamewhitelist AST checks pass.
Publicbrowser-source bytes are captured ashash-pinneddata only; no Env/private
key/unrestrictedinspectionerror is exported.

Separate facts-v2 passes0/0.891264s, executor3354632/start422073417 reaped/absent;
local6782b99d/79163. It confirms Chromium's original236-characterError is at
response-json, Network.getResponseBody, literal no-data-for-resource; the
navigationadvisory isgeneric and doesnotprovewhybodybecameunavailable. Actual
sandbox/version remainverified. 53local+53independent/source/capture23FD/
codec97878 checks pass. The originalreportfull9/hash andallfailedreceipts remain
retained, not replayed.

Canonicalsource16 fixes knownHFAPI002exit2→10 anditsfixture, adds old2rejection,
and captures the SAMEobserved response JSON immediatelyatdelivery beforeawaiting
navigation. Same response/body or response/exacterror is retained; status200
stillchecked, errorstillpropagated, no retry/newrequest is added. Two focused
lifetime/failure regressions accompany it; acceptance of a newChromiumrun remains
pending. Human API/troubleshooting/development docs clarify theexistingtaxonomy
and responseownership. `INV-006`/decisions113+150 reviewed; no invariant/ADR,
publicAPIbehavior or runtime dependency change. Beforebytes are preserved under
source16-harness-before-v1 andsource16-before-response-capture-v1.

IndependentNode12checks andactualPythonproblem→JSvalidator smoke pass, asdid2
existingASGIdenialchecks for the earlierexit-onlypatch; backendunchanged.
Prettier/diffcheck anddocumentation207human/27helper alignment pass. Exactly5
canonicalfiles differ fromsource15:2hostdriver/test files +API/development/
troubleshootingdocs. All108Python packagebytes andweb/src inputs are unchanged.
Source16 is FROZEN1361leaves: inventory21b55abf/244519, snapshot2da61616,
archivebb167d3c/17725440, capturec1f22118. Its actual strictcommand
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
PID3356374/start422134118, ownedwrapper3356373/start422134097; gate16.log and
pendinggate16-result retain evidence. NOgatePASS is claimedwhileitisrunning.
Onlythe5bookkeepingexclusions maychange untilcompletion. Originalsource15
strictgate/APIUIimage07bd provenance staysoriginal; no runtime isrelabeled.

PublicPKI17CA export and separateWebKittest-systemtrust measurement/build stages
are underlocalpreparation. Trustedtestimage updates mustpreserveoriginal and
untrustedprofiles andallTLS/confinement checks. NoactualCAexport/imagebuild or
fresh22 isclaimedhere. Allfailed21/normal/rootless/negative/fault scopes remain
inert. Checkpoint100 `.scratch/web-006-source16-current-state-v100.json` SHA256
79fcd443def544c411b71dc50cb9bf926351a33c05936640e37b6cb4bb84a3a5 records currentevidence. WEB-006 remainsincomplete/uncommitted;
no production/NAS/livehistorical frontend changes occurred.

## Checkpoint101 — strict source16 gate and public CA export pass

Separate original public-CA export21v3 passes0 in1.208270s. Its owned executor
3374598/start422255577 and SSH child close; both fixed queries return0/reap.
Local391cf60a/58978 and protected canonical9be1a5f1/44801 retain the actual
result. Exact full9/SID checks precede the1574 public certificate bytes; no private
key body or digest is read. New local public artifact
`.scratch/web-006-pki17-current-public-ca-v1.crt` is O_EXCL, SHA2561dbeeac8,
inode206423966, UID/GID1000, mode0644. Existing guest CA/source nodes and prior
failed/UNKNOWN evidence remain unchanged. Corrected helper26local/26independent
models and18FD/codec67056 preflights pass; unexecuted v1/v2 candidates and the
reproduced v2 stream-failure leak remain retained.

Actual browser-image Config.User and OS-store contents remain unobserved here;
the separate no-network measurement is under preparation. No image build,
functional rerun, new fixture selection or installed acceptance is claimed.
All21 success-dependent normal/rootless/negative/fault scopes stay inert.
Source15 API/UI image07bd retains its original pinnedUBI10micro provenance;
source16 changes only two host-driver files and three human references. A new
test tree/projection must bind those files without reinstalling existing0.2.4/
0.2.5 or relabelling old runtime evidence. Checkpoint101
`.scratch/web-006-source16-current-state-v101.json` SHA256b5afd8dfc3b76dccf3a3a0a8179d1a1cc6128dd459af8da632425619f009e3ba
records the current evidence. WEB-006 remains incomplete/uncommitted.
Production, NAS and installed predecessor interface remain untouched.

## Selector navigation reconciliation — 2026-10-23

The sole current selector is condensed to current task/blockers and links,
following the planning contract; duplicated older chronology stays in this task,
the dated plan and Operator handoff. Its exact before-bytes/full9 record is
retained in `.scratch/web-006-current-selector-navigation-trim-v1.json`, SHA256
428d370c9ac2c969d99a19a74e255fe9958c338603b17a97100139cb086b2a63. No plan, task disposition or historical
failure/UNKNOWN changes. The new source16 launcher must add a real same-current-
Caddy-certificate untrusted-profile rejection preflight before trusted browsers:
review found that seam absent from the original host launcher. Old auth testing
against a different untrusted endpoint and image store membership do not supply
that proof. Measurement and functional acceptance remain separate.

## Checkpoint102 — actual old test-image OS trust mismatch measured

The actual no-network browser-image measurement21v1 passes0 in7.692472s.
Root executor3378724/start422341306 is reaped/absent; local65274e2b/85778 and
protected canonicald42bffae/69524 retain the result. All held local/guest inputs
rejoin, strict original application closure passes, and no original container,
service, image, tag or private-key action occurs. The source16 strict gate remains
passed and all1361 current source hashes/modes match snapshot2da61616.

Both actual browser-image Config.User values are1000:1000. The original trusted
image OS bundle has122 certificates/183681bytes, SHA25680113ef7; it contains one
old baked fixture CA and zero current-CA DER matches. Old public CA9758b5ee/1541
expired2026-10-22T19:05:28Z; current CA1dbeeac8/1574 is different and valid through
2026-10-29T22:24:01Z. The five relevant trust overrides are absent. This proves
the current store mismatch; it does not prove the sole historical WebKit cause
or any actual browser TLS success. Package database8675ea4b/548503 and existing
updatere4c6e910/5446 are pinned for the separate descendant audit.

New measurement CID9204cf721d667aad2dc2e2a96628b17e259c7c09f193306cb6cf5d03e04e49b4
exits0/PID0. Init101745/start23225123 is gone and its exact container scope is
physically absent; UID1000 child101686/start23224531 returns0/reaps. Effective
capabilities0, NNP1, seccomp2 and read-only/network-none confinement are measured
before releasing its owned gate. All engine CLI handles close; actual finite
public report3023bytes fits the unchanged4096 bound. Independent67Python+18Node
models and real19FD/codec119980 preflight pass0skips; child-source32768 and quoted
command120000 caps remain intact. Only an inert loader label shortened locally.

Next is a distinct trusted-only test-image build/audit using the observed exact
parent User and current public CA. Originaldffe and untrusted01c0 images remain
preserved; no build is claimed here. Same-current-Caddy untrusted certificate
rejection must precede trusted browsers in the new owned launcher. New source16
test-tree/projection preparation retains original source15 API/UI artifact
provenance and never reinstalls/restages existing0.2.4/0.2.5. All21 successors
remain inert; no fresh22 is selected and installed acceptance remains pending.
Checkpoint102 `.scratch/web-006-source16-current-state-v102.json` SHA256
004bbfcf0e8dc366cedae0a424ce97cb95f090e8e69006cd07f6f22b5d7d92e8 records the actual evidence. WEB-006 remains
incomplete/uncommitted; production, NAS and installed predecessor interface remain untouched.

## Checkpoint103 — original new-image build audit fails; retain its IID

The original trusted-only browser-image build stage exits1 and remains failed.
Owned executor3382884/start422475800 reaps in22.650324s; local9910a2d8/102612 and
protected canonicala335896c/85285 retain the actual failure. Caller3247d84a,
guesta9757709 andchild178056df were captured exactly. Prior independent39child/
root+57parent/caller models and real20FD/codec119441 passed, but they did not
establish acceptance of the subsequent real build audit.

The actual build command returns0 with484stdout bytes/0stderr and creates retained
untagged IID053ce2018f6043859235c344300abf76b31952bf32dedeabb69378cd886a9b4e.
Its Config.User is1000:1000 and original lower layers are retained. The first
failure is exactly audit_changes line227's path predicate at image-diff. The
actual refused path remains unobserved: image_diff was assigned only after that
audit and therefore remains absent in the failed proof. No whitelist is widened and
no build replay is authorized by this diagnosis.

All9 recorded engine CLI commands return0/reap without budget/output overflow;
UID1000 child101848/start23359030 returns1/reaps in21.627238s. The retained IID
fileinode27386586/71bytes/SHA2563eb715e7 is rejoined after queries. Child held-input
and FD closure flags are true; original image metadata/tags and all97 pre-existing
container IDs compare equal before/after. Original root/caller passed/capture
flags remainfalse, with no held-release failure. Native/measurement original
handles/scopes were freshly absent before this stage; separate new read-only
closure after the failed stage is still required. No original outcome is promoted.

New image eligibility, post-build OS/package/updater audit, TLS and application
acceptance all remainfalse. Next is a separate read-only saved-build/diff/fresh-
closure collector for the exact retained IID, followed by specific path review
and the still-required OS/browser audits. Originaldffe/untrusted01c0 remain
unchanged. No source16 fixture is selected; all21 successors remain inert.

Local negative-preflight primitives pass31adversarial models; their runtime
admission remainsinert. The separate owned loopback TLS epoch integration passes
8tests, proving stable-leaf success and changed-leaf/unknown-CA refusal without
HTTP/auth requests. Initial synthetic-fixture subject/ticket failures remain
recorded; only those test fixtures changed, and strict verification stayed fixed.
These local tests do not supply real installed Caddy/browser acceptance. All1361
canonical source hashes/modes still match source16/2da61616 and its strict gate
remains passed. Checkpoint103
`.scratch/web-006-source16-current-state-v103.json` SHA256
8e2c075d4ea8936c6ebf857857f9bd1cae5040ca5f6093d5bdbbd3b460b22db1 records the actual evidence. WEB-006 remains
incomplete/uncommitted; production, NAS and installed predecessor interface remain untouched.

## Checkpoint104 — read-only diff identifies only the fixed image `/tmp`

The separate read-only retained-image diff collector passes0 in3.820167s.
Executor3386242/start422597026 reaps/absent; locald822be40/106595 and protected
canonical0708709c/88928 retain the result. Caller79619245/rootgueste6409fdf/
childcaa12ad1 were captured exactly. Independent49root/child+60root/completion/
caller models and real20FD/codec119557 pass0skips. UID1000 child102752/
start23480254 returns0/reaps in2.840068s; all query CLI handles close. Original
native, measurement and build-worker/nine-CLI identities are freshly gone,
named original scopes physically absent, all three context/IID records rejoin,
and current original/new metadata and97container IDs remain equal.

The fresh exact new053ce201-versus-originaldffe query returns347bytes/SHA256
b4b313e8, with10 changed paths and no added/deleted paths. Only `/tmp` lies
outside the original policy. All other entries are the current public CA,
regenerated bundle and their parent directories. The original raw diff bytes/
digest were not saved before failure; no original-byte identity join is claimed.
The new observation binds the same immutable IDs/metadata and fixed query argv.
Original first/secondary failures, absent diff members and false capture/build
flags remain unchanged. A successful diagnostic does not make the build pass.

Next prove the fixed original/new image `/tmp` type/ownership/permissions and
bounded contents, plus new CA/bundle and unchanged package/updater bytes. Podman
6.1 defaults to temporary filesystems under `--read-only`; those would hide
baked `/tmp`. New audit probes must explicitly disable that masking and prove
their actual mount view, retaining read-only/capless/NNP/seccomp/network-none
confinement. No directory or subtree whitelist is broadened from the diff alone.
The retained image remains ineligible, no build is replayed, and no functional
TLS/application acceptance or fresh fixture is claimed.

Independent local negative-preflight/epoch checks pass39tests (31adversarial
models+8owned loopback TLS integrations), with no Caddy/browser claim. Host-only
source16 two-TOML metadata projection preparation is independent of image
eligibility; it cannot select a guest or relabel old artifact provenance. All1361
canonical source hashes/modes remain source16/2da61616 and its strict gate stays
passed. Checkpoint104 `.scratch/web-006-source16-current-state-v104.json` SHA256
d4e4a4506cd49f26b32641234b053c4a381e5da815b47680f840246332cc740e records the actual evidence. WEB-006 remains
incomplete/uncommitted; production, NAS and installed predecessor interface remain untouched.

## Checkpoint105 — host-only source16 fixture metadata projection passes

The host-only source16 fixture metadata projection passes0 in6.009788s.
Owned executor3387156/start422634836 reaps/absent; report
`.scratch/web-006-source16-fixture-projection-v1/projection.json` SHA256d2c1c22c/
260485bytes records1361 files and snapshot706a11e4511e48dd76d999fbe489392e937ea674fa37f8f1e61ebc20f859e2d0.
Only the copied pyproject/lock self-version fields change to0.2.4. All other TOML
values, all108 API package files and27 frontend source files remain byte-equal;
all1361 projected hashes/modes and canonical before/after inventory verify.
Canonical product version remains0.2.2. All held captures close normally.

Independent reviewf5b4d7d0 verifies the two gate16/log assignment-only bindings,
actual gate source/outer/stdout/stderr/closure, full archive/current leaves and
eight gate fault refusals. Projection affects only a new host-local test tree:
no wheel/UI/image build, guest call, installation, restaging, authority selection
or original source15 artifact provenance relabel occurs. Local transfer data
preparation may proceed independently while the original failed browser-image
build and successful read-only `/tmp` diagnostic remain unchanged. The retained
new image is still ineligible pending unshadowed baked-directory and OS trust/
package/updater audits, then real same-Caddy negative/trusted browser acceptance.
All21 success-dependent scopes stay inert and no fresh22 is selected.

Checkpoint105 `.scratch/web-006-source16-current-state-v105.json` SHA256
b665cf4e259eae7d60f29db4cd32011fcedaaaa14decb5f799ae54ca8476d9e7 records this limited result. WEB-006 remains incomplete/
uncommitted; no installed acceptance, production/NAS or installed predecessor interface change.

WEB-006 checkpoint106 update2026-10-23: paired OS probes pass; comparison fails, image remains ineligible.

Actual paired audit executor3425945/start424484398 exited1/reaped/absent in
24.088822s. Local9d830598/202326bytes and protected97b867b6/179189bytes retain
all original false flags. Caller434af6d3/root263496f3/child2fe97338 ran once after
41Python+31Node models (zero skips), real21FD/QEMU preflight and lossless65352byte
SSH payload within the unchanged120000 cap. Prior local preparation failures
remain retained; no independent agent review was available after usage limits.

Both read-only, network-none probes actually pass0: original CIDa260a94d and new
CID14f0265c, original init103340/start25368378 and new103430/start25369525.
Both attachments and five CLI handles per probe close; both exact cgroups are
absent. New OS bundle34a04cee/183714bytes contains the current CA, while original
80113ef7 retains its old CA. Package/updater and GNU stat hashes match.
Actual unmasked /tmp is root0:0/mode1777, with one directory entry in BOTH images;
file SID is unconfined_u:object_r:container_file_t:s0 in BOTH. The original
comparison's empty-directory predicate fails; its per-init-MCS label assumption
also contradicts measured file labels and must not be treated as actual behavior.
No exception or image eligibility is accepted. A separate bounded read-only
retained-filesystem inspection must prove the existing child unchanged.

The final read-only image/diff query itself passes0, preserves image metadata/
tags and observes exactly99 retained IDs (old97 plus these2 probes). The saved
root after_query_error_class=ValueError arises from its subsequent non-null
comparison predicate; it is preserved without calling the query failed.
Original build9910a2d8 and native21 failure/UNKNOWN records stay unchanged;
no image build/native/functional replay, new fixture selection or acceptance.
Source16 gate/projection and UBI10micro API/UI provenance remain unchanged.

Checkpoint106 `.scratch/web-006-source16-current-state-v106.json` SHA256
0902df53ec3063a0b44fe85815d693fffc9fc24c723f234af27baa4cf6052270. AUTH-08/HOST-01–03 and WEB-006 remain incomplete/uncommitted;
no production/NAS/installed predecessor interface changes.

WEB-006 checkpoint107 update2026-10-23: retained rootfs diagnostic failures remain preserved.

Three separate readonly inspections remain failed: local6782c4dc/74668bytes
(executor3428315/start424575854,1.383641s),24738106/79031bytes
(3428813/start424594888,1.356713s),c58bf400/80748bytes
(3429570/start424624371,1.513559s). All exit1/reap/absent. Their protected
receipts are c2fe3d6c/53719,72d79467/57805 and
f627331f/59399bytes. Actual inspector children and two
readonly CLI commands per attempt return0/reap; both original probe CIDs remain
exited0/PID0. Fresh37 original audit handles are gone, plus prior inspection
handles when captured. No container starts/creates/builds/mounts or replay occur.

Finite diagnostics prove retained /tmp dev/inode/mode/nlink/size/mtime/ctime
match its original unmasked container measurement. Host UID/GID524288 equal the
retained rootfs root; observed file label remains container_file_t:s0. The prior
child-empty/same-label predicate failed. A bounded recursive comparison then
refused a directory wider than64 entries (walk line48); no complete subtree
comparison or file-byte equality has been proved. All false completion/eligibility
flags and prior errors remain unchanged. A larger explicitly bounded streaming
digest, with actual count/depth/bytes and finite report, is the next audit step.
The source fixture, runtime code, strict gate and UBI10micro ancestry are unchanged.
No functional acceptance is claimed; source16 local transfer preparation is
independently ready and no new guest fixture/authority is selected.

Checkpoint107 `.scratch/web-006-source16-current-state-v107.json` SHA256
9fd53bddcd4f21a64a49b09cfdb356dd5f5d0bf0a7b90f25503a1878d6935c8b. WEB-006 remains incomplete/uncommitted; AUTH-08/HOST-01–03
stay pending. Production/NAS/installed predecessor interface remain untouched.

WEB-006 checkpoint108 update2026-10-23: separate streaming audit and fixed fixture admission pass.

Actual streaming retained-rootfs inspection passes0 in1.932564s:
executor3431281/start424693937 reaps/absent; locale1785fb7/89737bytes and
protectedf567ee12/67953bytes. Caller56db8556/root31887e1b/inspect-childf37457fa
are exact captures.54local model tests pass/zero skips, expanded namespace lint
passes,25inputs/28FD/QEMU identity checks close, SSH77383<120000. UID1000
child103771/start25577095 returns0/reaps; two inspect CLIs103772/start25577103
and103780/start25577117 return0/reap. Fresh37 original audit handles plus15 prior
inspection handles are gone. Both original probe CIDs remain exited0/PID0;
no build/create/start/mount/replay or image tag/delete action occurs.

Both complete /tmp subtrees are identical:565entries (2directories,563files),
1419404regular-file bytes hashed, digest35a5349a486c7aa9d1ab992c65c924f53e3c1be56b1209a7d34edc0cad712195.
Observed maxima: depth2,width563,file90140bytes. Streaming limits are32768entries,
depth32,512MiB/file and1GiB total; actual usage is recorded. All directory/file
FDs rejoin/close, no entry names/file contents are exported and no symlink is
followed. Root-owned /tmp remains0:0/mode1777/unchanged container_file_t:s0 label.
Per-image inode/non-mapping full9 rejoin the original unmasked measurements;
cross-image inode/ctime equality is explicitly not inferred.

Separate LOCAL fixture admission passes0 in0.262344s, executor3431898/
start424717748 reaped/absent, source201d1649. Artifact
`.scratch/web-006-pki17-retained-browser-fixture-admission-v1.json`
SHA256ee24b95220ca8b59a1597c1593b2d79775f25c46dbf77ed6ccfa78755834886f (17368bytes)
permits only the changed /tmp DIRECTORY metadata for originaldffe5ada -> retained
053ce201 and this current publicCA1dbeeac8. It requires this exact unchanged
subtree, original lower layers/config/User, unchanged package/updater bytes and
current CA in new OS bundle; no added/deleted /tmp paths or future image/CA
changes are covered. The separate new admission makes053ce201 eligible for the
fresh test fixture. Original build9910a2d8, paired audit9d830598 and three retained
inspection failures remain FAILED with original false flags. None is promoted.
Real same-current-Caddy untrusted/trusted3engine acceptance remains required.
This test-tooling rule changes no product contract, invariant, ADR or privilege.

Independent HOSTONLY source16 packet preparation also passes0 in1.533753s,
executor3430358/start424656053 reaped/absent; source8870389f. Preparation
01f9f8f2/9992bytes in `.scratch/web-006-source16-transfer-packet-v2/` validates
13members and exact gate16 runner/executor/channels, rejoining1361canonical and
projected sources. Packet a56a5ce3/36464640bytes, codec3e7ce63f/12434bytes,
fixture inventoryc70000ea/244492bytes, snapshot706a11e4. Only copied project and
self-lock version fields become0.2.4; canonical0.2.2/API108/UI27 and source15
runtime0.2.4/0.2.5 artifacts/provenance remain unchanged. Original local builder
v1 __file__ failure and wrong-hash pre-execution refusal stay recorded.
No guest transfer/install/staging, fresh22 selection or functional run occurs.

Checkpoint108 `.scratch/web-006-source16-current-state-v108.json` SHA256
c0897b61e14d34c455d13b8cd90156c73336e06eac45f296c4a591f30c911357. Next: exact source16 transfer/RO package projection and EMPTY
prelabelled public inputs, actual same-Caddy negative TLS epoch/preflight, then
fresh native/rootless acceptance. All21 success-dependent scopes stay inert.
WEB-006/AUTH-08/HOST-01–03 remain incomplete; gate16 source2da61616 stays green.
Shared API/UI image07bd818e retains pinned UBI10micro ancestry; no separate
frontend image/server. Production/NAS/installed predecessor interface remain untouched.

WEB-006 checkpoint109 update2026-10-23: source16 transfer stops at readable-parent boundary.

Original source16 transfer exits1 in5.379002s, executor3436714/
start424924723 reaped/absent. Locala114877d/83489bytes and protected
4e7f4f0d/58048bytes retain rootOSError/capture flagsfalse. Caller c6fe5dfb
(bound filename,43458bytes) and rootc5adeb2b/103403bytes ran once after30local
models/zero skips, expanded lint and29input/33FD liveQEMU preflight.
SSH97460<120000; exact36464640byte packet was sealed with real Linux seals15.
This Python3.14 build omits named fcntl seal constants; verified LinuxUAPI values
and real EPERM write/grow/shrink tests preserve the same kernel enforcement.
The original missing-constant model failure and INERT-name wrapper refusal remain
retained; the refused name did not start a process or guest call.

The root actor wrote13protected packet members and the fixed browser admission,
then failed at transfer_snapshot line123, os.listdir on the inherited O_PATH
parent FD. PUBLIC mkdir was not reached; no public result member is present.
Both before/finally source15 scans verify all1361full9/hash/SID records unchanged.
All13fixed roles remain strictquiescent,4cgroups empty and5endpoints refused;
four manager queries103892/start25807991,103893/25808009,103895/25808199,
103896/25808214 return0/reap. Held release failures are empty. No service,
selector, policy, credential, installed version or source15 bytes changed.

Do not rerun original protected writes or promote this failure. Prepare a
separate completion scope that holds the failed receipt, revalidates all retained
13members/admission, proves PUBLIC absent and uses a readable directory FD for
the first public source copy. Source16 strict gate, packet and separate fixed
browser image admission remain valid. No package projection, fresh functional
authority or installed browser acceptance has occurred.

Checkpoint109 `.scratch/web-006-source16-current-state-v109.json` SHA256
a504a66cc61d982cb5dc14eef34bc91272e74fc01d62e414de0b8dd6f1fea63c. WEB-006/AUTH-08/HOST-01–03 remain incomplete; original failed
native/build/audits stay preserved. Production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint110 update2026-10-23: separate retained-data completion passes.

Actual first public-copy completion passes0 in18.105483s, executor3438623/
start425007296 reaped/absent. Local21fcee64/1044699bytes and protected
1352a435/970049bytes retain the result. Caller507f0df9/47293bytes and
rootee02a983/105697bytes are exact captures;38local models/zero skips and
expanded lint pass. Actual O_PATH/EBADF/readable duplicate, failure close and
no-protected-write-replay tests pass.35inputs/38FD/QEMU joins close; SSH98056
remains below120000. Completion stdin is DEVNULL; all13retained protected members
and browser admission revalidate/read only. Original failed a114877d/4e7f4f0d
and its false flags remain unchanged. Four original transfer handles are freshly
gone. The original protected bodies are not rewritten or retransferred.

Fresh public `/home/webfixture/hfcache-web006-source16-fixture-v1` contains exactly
1361source files with captured full9/hash/mode/SID records; no extra directories.
Root directory inode84887062,UID/GID1000,mode0755,user_home_t; ordinary files are
usr_t before bytes. Canonical snapshot2da61616 and fixture snapshot706a11e4 are
verified. Only copied TOML version metadata projects0.2.4; all108API/27UI source
bytes and source15 installed/staged artifacts keep their original provenance.
Source15 all1361full9/hash/SID records pass before/after/finally. Current/key
metadata rejoin, release failures[]; all13roles strictquiescent,4cgroups empty,
5endpoints refused after completion. Manager queries103937/start25890470,
103938/25890488,103940/25892056,103941/25892073 return0/reap.
No selector, service, timer, credential, policy, installed version or Caddy changes.

The source data is now available for a NEW read-only installed-package projection
and prelabelled public inputs. No package mount/projection, fresh functional
authority, native/rootless browser run or acceptance occurs in this phase.
Same-current-Caddy untrusted/trusted3engine proof, real host isolation/faults and
WEB-006 acceptance remain required. Source16 strict gate stays green; shipped
API/UI artifact07bd818e retains pinned UBI10micro base/no frontend server.

Checkpoint110 `.scratch/web-006-source16-current-state-v110.json` SHA256
8755819e19cf085a54f38102c194024cccc6f150ddb1b7f3bc5e4caab9a23743. All21success-dependent scopes stay inert. WEB-006/
AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint111 update2026-10-23: package projection bind fails; mount state unproved.

Original projection actor exits1 in3.792676s, executor3443018/start425200754
reaped/absent. Local513d3fae/96414bytes and protected
32346d60/60888bytes retain rootValueError/all-input flagsfalse.
Caller06042a4e/50729bytes and rootbbf55760/126893bytes are captured exactly;
30local models/zero skips, composed lint and41input/44FD/QEMU checks pass.
Base64 candidate exceeded the unchanged120000command cap by288bytes before
execution; lossless base85 yields112804bytes and native3.12 decode proves exact
source/hash. No cap increase or source substitution occurs.

Wheel79f1d75a and complete108package inventory match source16. Source16 all1361
full9/hash/SID records pass before/finally. A fresh .scratch/provisioning/
web006-source16-installed-v1/installed/hfcache target is created; intent records
underlying inode18978723/root0:0/mode0755. Bind command104037/start26084055
returns32/reaps, stderr158bytes/SHAa088589d; readonly remount/import/wheel copy
were not reached. `bind_may_be_present=true`, `readonly_proved=false` remain
unchanged. Exit32 is not proof of absence. All13roles strictquiescent,4cgroups
empty,5endpoints refused; release failures[]. No reinstall/staging, selector,
service, policy, timer, credential, production/NAS or installed predecessor interface changes.

Next is a separate readonly collection of the retained credential-free mount
error, actual mountinfo and target inode/emptiness before any new action.
Do not retry the mount, remove the target or clean up an unknown bind. Preserve
this original failure, intent and handles. No fresh functional authority or
installed browser acceptance is selected. Source16 gate/copy and browser fixture
admission remain valid; package projection remains incomplete.

Checkpoint111 `.scratch/web-006-source16-current-state-v111.json` SHA256
6419787fb1bc5c17044b90f96e7971a6606346be86e5b1f461332584f9c1eda6. WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted.

WEB-006 checkpoint112 update2026-10-23: separate readonly mount diagnostic passes.

Actual executor3445091/start425286736 returns0/reaps/absent in1.699454s.
Local15f3bb9d/98145bytes and protected77940f35/58847bytes preserve the
observations. All50held local descriptors rejoin/close;17local models pass
with zero skips. Saved credential-free mount stderr is classified missing-path,
with procFD239 referenced; raw error text is not exported. Actual target
inode18978723/full9/SID exactly matches the original underlying empty directory,
with zero entries, no exact mountinfo row and readonly=false. Mountinfo rejoins.
All5original projection process identities are freshly gone, and final13role/
4cgroup/5endpoint strict closure passes. No retry, cleanup or unmount occurred.
Original FAIL513d3fae/32346d60 and its false readonly/completion flags remain
unchanged. This observation clears only mount-state uncertainty.

Next is a separate direct mount(2) completion using held source/target directory
FDs, after fresh empty-target/mountinfo/inode guards. No installation/restaging,
fresh functional authority or browser acceptance is granted. Source16 gate and
fixed browser admission remain valid; production/NAS/installed predecessor interface untouched.
Checkpoint112 `.scratch/web-006-source16-current-state-v112.json` SHA256795cf39dfcf27252d96ae49aeb1bb0d9ffb45d75724da8a14855fd2fe0b4bfca.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted.

WEB-006 checkpoint113 update2026-10-23: separate readonly package completion passes.

Actual executor3446537/start425345409 returns0/reaps/absent in4.951319s.
Locald9d4e45b/181815bytes and protected39a660ce/135386bytes preserve the result.
Rootf181a65e/131171bytes and caller1d42abd2/58237bytes pass composed lint,
16local models/zero skips and53input/56FD/QEMU capture checks; SSH114297bytes
remains below120000. Fresh receipt/empty-target/full9/mountinfo guards precede
both effects. Direct owning-process mount(2) calls bind4096 and remount4129
return0/errno0; exact target mount row is readonly. All108package leaves share
installed full9/hash/SID and match wheel/source16. UID1000 import104145/
start26228706 resolves the new projection/version0.2.4; wrapper104144/
start26228705 returns0/reaps and both identities close. The original wheel
79f1d75a/500283bytes is copied once to the new installed-v1 scope, labelledusr_t
before bytes. Public source-root full9 remains unchanged in this completion.
All1361source16 files pass before/after/finally; held releases[], all5actual
CLIcommands close and final13roles/4cgroups/5endpoints are strictquiescent.

Original FAIL513d3fae/32346d60 and UNKNOWN-era receipt remain unchanged.
No reinstall/staging, selector/service/timer/policy/credential change or browser
acceptance occurred. Next: empty prelabelled shared public tool/code inputs,
new launcher with real same-current-Caddy untrusted/trusted epoch, then a fresh
native/rootless authority. Old21success-dependent scopes remain inert.
Checkpoint113 `.scratch/web-006-source16-current-state-v113.json` SHA256ad5c2fea0cd8daf8ecb7981c738033d32d169bd1ef85b0c15c7401d0bb08a4fc.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint114 update2026-10-23: new prelabelled public browser inputs pass.

Actual executor3447872/start425396209 returns0/reaps/absent in9.572909s.
Localcf54e1d6/325758bytes and protected5dba6bfe/274025bytes retain the result.
Root1228ef4b/117133bytes and callerf7cf5795/57499bytes pass composed lint,
13local models/zero skips and53input/56FD/QEMU preflight; SSH101664bytes
stays below120000. Model tests use owned repository scratch; the initial /tmp
model fixture refusal is preserved and corrected without relaxing parent guards.

New `/home/webfixture/hfcache-web006-source16-fixture-v1/.scratch/provisioning/web006-browser-inputs-source16-v1`
has194ordinary files/50directories, allroot0:0 with container_file_t:s0 set
while EMPTY before bytes/entries. The185tool files total144525705bytes;
seven source16 browser-test files, public currentCA1dbeeac8 and fixtureinventory
c70000ea are copied with exact hashes. Protected inventory0600 is copied to
new public0644; its original is unchanged. All old185file/45directory full9/
hash/SID records remain held and rejoin; corrected source16 seven-file records
also rejoin. New tree entries are exact, with no extra paths. Actual heldFD740
plus reserved32 remains below existing soft1024/hard524288; limits unchanged.
The108same-inode readonly package files pass before/after. All1361source16files
pass before/after/finally; held release failures[], final13roles/4cgroups/
5endpoints strictquiescent. No browser, selector, services, timers, credentials,
policy, reinstall/staging or production action occurs.

Next: a fresh launcher using modern EOF/reap ownership for BOTH untrusted and
trusted browser containers, shared protected code mounts without borrowed :z,
and actual same-current-Caddy CA/leaf epoch checks. Legacy005 forced-stop drain
must not be imported into the new phase. Old failed/UNKNOWN receipts remain
unchanged; no fresh functional authority or installed acceptance yet.
Checkpoint114 `.scratch/web-006-source16-current-state-v114.json` SHA25635674181cfc8d860666029ac3b775cc195d6627c41de80c44b30a3b8d00c2d95.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint115 update2026-10-23: readonly authority inputs pass; launcher draft stays inert.

Actual reader3449764/start425468239 returns0/reaps/absent in3.982534s.
Local0465e0b6/351279bytes and protected0ec8e997/294863bytes retain the result;
rootfb88d252/116843bytes and callerd45c0ef3/61344bytes pass composed lint and
59input/62FD/QEMU preflight. Quoted SSH107817 stays below120000. All194public
file/50directory full9/hash/SID inputs rejoin unchanged; source16 all1361files
pass before/after, releases[], final13role/4cgroup/5endpoint strict closure.
No services/selectors/credentials/policy/sudoers changed, no authority selected.
Static control22 and manifest21 reconstruct EXACT original bytes/hashes977a3ca9
(31471bytes) and89adb78f(5004bytes). Actual controller source is confirmed
2a2219d8/111918bytes. Tool inventory is an explicitly SEMANTIC projection:
183files/schema1; localf34dfeb1/24577bytes differs from original bytehashfb271905.
Do not claim a raw-byte join or original hash for that projection.

INERT launcher70b05f87/99007bytes and helper7caf2027 derive both phases from the
modern browser owner; legacy005 forced-stop drain is not imported. Negative
stdin is DEVNULL and receives no auth, fixtureCA/NSS/Firefox trust injection;
all194public files/50dirs plus original manifest/runtime are held/full9/hash/SID
rejoined across before/middle/after TLS-peer observations and negative/trusted
browsers. Borrowed mounts use :ro, new owned gate/phase/output only may relabel.
Per-mode negative workspaces preserve distinct original handles. Loopback/pure
models51PASS/zero skips and composed launcher lint pass. This is NOT guest
publication, a selected authority or real Caddy/browser/installed acceptance.
Model evidence6cea91b8/1498bytes retains the exact draft/adapter/builder/test hashes.

Next fresh22/controller23 preparation must also put assets and public deployment/
policy copies under the NEW source16 root because the installed fixture checker
refuses old-root inputs. The183file tool inventory may be reserialized only as
new data with its own hash/provenance. Preserve all161original control input
records as an ordered prefix, installed0.2.4/0.2.5/artifact provenance, old native21
aliases and original key metadata until fresh strict drain and explicit scoped
preservation. Validate the installed manifest before one fresh native run.
Checkpoint115 `.scratch/web-006-source16-current-state-v115.json` SHA256ec94700ec96c4df30944ee6ccf0548f1f94ae543890692d68776d136ad03f662.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint116 update2026-10-23: fresh22 public preparation/static validator passes.

Actual executor3452960/start425596323 returns0/reaps/absent in5.838016s.
Localed7f29c8/105752bytes and protectedd1917f35/88625bytes retain the result.
Rootef377c80/123160bytes, calleraecb8213/14035bytes,26local publication/document
models/zero skips and expanded lint pass. Preflight holds20inputs plus1361actual
canonical source files,1383FDs rejoined/closed, unchanged SSHcap107441/120000.
Gate16source2da61616/7749Python/fullrequiredstages still matches; complete
local source full9 ledger27ecae43/612049bytes is retained. Two owned localgit
commands and SSH finish normally; no automatic signals or source substitution.

Fresh authority22 UUID0a1ab232-4c2c-411b-b186-90df3c5b78b7 now has21newfiles:
4private artifacts and17public fixture files, all EMPTY-label-before-bytes.
Public tree includes unchanged six built0.2.4UI assets/f09f904e, four deployment/
policy copies with unchanged hashes, semantic toolinventoryf34dfeb1, marker,
modern browser launcher70b05f87, fixed native/rootless wrappers, private-wheel
runner and manifestf8faa1e9/5020bytes. All public paths are under source16 root;
new public labelscontainer_file_t:s0, private codeusr_t. The installed original
0.2.4validator runs asUID1000: actualpython104316/start26479609 and wrapper
104315/start26479608 both close, wrapper0/reaped, manifest/package identity pass.
No browser/service execution occurs. Controller23source8c160dee changes only
CONTROL/generation/repository path assignments from actual2a2219d8; retained
primitives88b4bf39/26980bytes are an exact AST dependency closure, no guard changes.

All194borrowed public files/50dirs full9/hash/SID rejoin; all33original native21
handles freshly gone; local/guest1361source files unchanged;108readonly package
files pass before/after, releases[], five CLIcommandsclose, final13roles/
4cgroups/5endpoints strictquiescent. Old current/deployment/policy/key metadata
remain unchanged. No control23/generations23/sudoers selection, install/staging,
credentials/timers/policy changes or functional acceptance. Existing API/UI
artifact07bd818e retains pinned UBI10micro provenance/no runtimefrontend server.

Next is SEPARATE selection preparation using original controller.lock inode,
fresh strict drain and original native21 alias preservation; do not repeat this
publication. Old native/build/paired-audit/UNKNOWN receipts stay unchanged. Then
one fresh native run plus strict postrun, followed by required rootless/fault/
retirement cohorts. Checkpoint116 `.scratch/web-006-source16-current-state-v116.json` SHA2564f737e3d2917f194835fd7e988af57947477a4deeafb244b5e58f54cd090cbe0.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint117 update2026-10-23: fresh22/controller23 preparation passes.

Actual executor3455114/start425681592 returns0/reaps/absent in4.671338s.
Local48f91582/82607bytes and protected183dd930/63270bytes retain the result.
Root02e82859/30556bytes and caller6dc1411a/17390bytes pass composed lint and
15local models/zero skips, including actual owned renameat2 regular/symlink/
EEXIST and real flock tests. Local login-user lock fixtures use the existing
public-parent resolver only for unit FD semantics; the actual guest retains the
root-only private-parent rule. The initial local private-parent refusal is
preserved; no guest guard was weakened. Preflight rejoined26inputs/1361canonical
sources/1389FDs, quotedSSH20439 below120000. Actual813FD+reserved32 remains
below unchanged soft1024. Source gate16 remains unchanged/green.

Under original NONCREATING controller.lock inode43335379, visudo passes;
control23=1c98b0c2/32738bytes and generationrootv23 are created, controller8c160dee
loads exactly matching manifestf8faa1e9. All161old control inputs remain an
ordered prefix, with7new protected receipts appended. Fresh before/preservation/
final13role/4cgroup/5endpoint closure passes. Three original native21 aliases
are atomically preserved via renameat2/RENAME_NOREPLACE/rc0, no replay: selector
inode60320036, deployment78478733 and policy78478734 now under
`/opt/hfcache-web006/fixture-authority-v22-selection-v1/`. Inode/mode/owner/size/
mtime/SID and selector stringreleases/0.2.4 are retained; only recorded rename
ctime advances. All3old alias names are absent; release trees are untouched.
New scoped sudoersv22=30ada05e/221bytes is0440 and inherits oldetc_t label while
EMPTY before bytes. This is entirely inside the positively owned disposable VM.

Master-key metadata inode78157344 remains held/rejoined, no keybody/hash read.
Original lock inode rejoined/closed, releases[], all7CLIcommands0/reaped;
all1361local/guest source files,194public files/50dirs,21publication files and
108readonly package files remain unchanged. No services/timers/credentials/kernel
policy, installed version or browser execution changes. Old failed/UNKNOWN
native/build/audits remain unchanged, all21success-dependent scopes inert.

Fresh22 UUID0a1ab232-4c2c-411b-b186-90df3c5b78b7 is now prepared; next is ONE new
native functional invocation using runnera36d43a9 and manifestf8faa1e9, with
strict postrun/original-handle collection prepared first. Do not repeat this
selection or publication and do not invoke oldnative21. Rootless/negative/fault/
retirement acceptance remains pending. Checkpoint117 `.scratch/web-006-source16-current-state-v117.json` SHA2564e86e6688f6a646bdb90889e5f6298e8f4f37511e052ebd1782a8693f11b7d2a.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint118 update2026-10-23: original native22 fails; real TLS/14baseline cases pass.

Original executor3457515/start425783437 returns1/reaps/absent in98.195719s.
Localf26079e1/52429bytes and protected33d92a5a/31550bytes retain the original
failure. Actual runner104429/start26666591 returns1/reaps in96.477470s; noSUMMARY.
Caller497c2111/22971bytes and root9ba8c437/38045bytes were captured exactly.
33inputs/1361canonical sources/1396FD preflight closes, quotedSSH20675; prepared
strict postrun template253348c2 and5local entry checks/zero skips/lint pass.
Native root/local inputs all rejoin/close; original native_functional_passed=false
is explicit. Root strict before/after13roles/4cgroups/5endpoints pass, kernel45bb
unchanged. No retry/forced signal or original native21/22 replay occurred.

Separate prepared postread25b4857d/53281bytes passes0 (protected d26e7b49/29324):
original runner/5CLIidentities gone, no summary, failed outcome unmodified.
Readonly partial059b11ac/74531bytes passes0 (protected5c40a943/49413), then exact
sanitized diagnostic8d4dc87c/96674bytes passes0 (protectede5b1a165/71200).
Generationc99d52bf50dd41aabede754686d794a6/profile cleanup_unknown=false.
Before/after-negative TLSpeer CA1dbee/leafDER2b5c7f9b are equal. All THREE real
untrusted engines pass one certificate-refusal attempt each; negativeCIDfeab1207
actuallyexited0/PID0. Trusted Firefox and WebKit each pass ALL7baseline host/UI/
denial cases. Trusted Chromium completes0cases with infrastructure_failed=true.
Its actual sanitized error remains response.json/Network.getResponseBody:
"No data found for resource with given identifier" despite eager capture.
TrustedCIDc03e56bc actuallyexited1/PID0; both init/client handles/descendants
closed, no OOM/forced browser close. Original drain_or_evidence_unknown=true
at report_passed is PRESERVED; separate current closure does not rewrite it.
Helper-down/restarted/timeout and all rootless/fault cohorts were not reached.

Next is a contract-first source17 harness correction: read the real JSON reply
in browser page execution after UI navigation, keep that GET's own status/
headers/body, retain actual UI state checks and all permission/timing assertions.
No route interception, mocks, TLS ignore, capability relaxation or failed-read
retry. The extra deliberate read is safe status observation, never operation
replay. Rerun a fresh strict source gate and use a NEW fixture/authority; do not
alter source16/native22 or republish existing installed artifacts. Invariant006/
ADR113/150 review: API/UI production behavior and dependency decisions unchanged;
only the functional observation mechanism changes. API/UI artifact07bd818e keeps
original source15/pinned UBI10micro provenance. Checkpoint118 `.scratch/web-006-source16-current-state-v118.json` SHA25609911c6183d123e30bdbb992d52c2ff878af42b3a969274c5fdbb250c60dc62c.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint119 update2026-10-23: source17 browser-page capture fix; strict gate RUNNING.

Contract-first host acceptance now performs one explicit same-origin real GET
inside the browser page after UI navigation, capturing its own status/headers/
JSON together. The UI's host-state/reason checks, native Basic cache, normal TLS,
passive network observer, deadline/permission assertions and no-retry behavior
remain. No Playwright response body lookup, route interception, synthetic reply,
Node-side request fallback or operation replay is introduced. Human development/
troubleshooting guidance explains the tooling failure and safe new-fixture path.
14Node checks pass/zero skips, including owned actualHTTP200/403 identity/body,
invalidJSON single-read failure and no Node fallback. ESLint/Prettier pass.
INV006/ADR113/150 review: no server behavior, UI source, invariant or dependency
change; known authorization exit10 stays intact. All108API/27UI bytes remain
unchanged from source16/15, so existing0.2.4/0.2.5 artifacts keep original
source15 provenance/pinned UBI10micro base; no rebuild/reinstall/restaging.

Frozen canonical source17 contains1361files/snapshot3b146543. Exactly four deltas
from source16: driver.mjs/driver.test.mjs and human development/troubleshooting
docs; modes/membership unchanged. Inventory0c87de18/244519bytes, tar54b3f82d/
17725440bytes, capture8a7f72f8/684bytes. Capture executor3461542/start425910035
returns0/reaps/absent; an earlier wrong-hash wrapper request refused before any
process/locator/artifact, then the observed exact source hash54b83d24 was used.
Original source16/native22 data are untouched. The new public GET is planned
observation; failure ends the invocation, with no subsequent failed-read retry.

Actual strict gate17 `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` is RUNNING:
outer3461656/start425913683, gate3461657/start425913701, session56166;
runnerdcb85031/6619bytes, start21:23:15.171660Z, log `.scratch/web-006-gate17.log`.
No PASS is claimed. Source17 fixture projection template9d6412b8 remains INERT
with gate/log pinsNone. Pure twoTOML model changes only copied pyproject/uv-lock
version0.2.2->0.2.4, predicts snapshotcb64ae60, revalidates all1361canonical bytes;
it is not a guest copy, installation or acceptance. Next: wait on THIS gate;
after actual PASS/unchanged source, bind projection, transfer NEW source17 and
prepare NEW authority23/control24. Native22 must never be rerun/promoted.
Current aliases were absent at fresh22 preparation; native22 activation has
since run. Fresh actual metadata is required before any new preservation.
Checkpoint119 `.scratch/web-006-source17-current-state-v119.json` SHA2564dbd6fa228925f650095670d522a4524fa05dbd35c04553e4c722d53c7fd4db3.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

## Checkpoint163 — corrected authority and baseline pass; original rootless29 running

Authority27/controller28 publication PASS: local0fa677a6/206998bytes,
protectedfa30d70e/79482bytes;3544774/start428445405 reaped/gone0 in5.799204s.
Corrected private controller6c276cb7 implements existing rootless Basic source
owner983/0400 and bounded read-only Type=exec readiness polling. Product guard,
policy, image and kernel unchanged. Control28 is002e0186/41546bytes; manifest27
3da80424/5019bytes, new fixture0e3ca585-f7b8-4f7d-b808-d5b724334851.
All209original immutable input rows including identical historical repeats are
preserved in order; only novel exact pins append.108installed package files and
1361source inputs unchanged. Current rootless aliases preserved NOREPLACE;
scoped sudoers/static validator/load_control/strict13role4cgroup5endpoint PASS.
No app role starts, profile reinstallation/restaging, key body/hash or policy
change. Actual descriptor782+32<1024 budget passes; soft/hard limits unchanged.
29local authority/controller/NFS tests PASS4.70s.

Fresh simple authority27 baseline PASS: localbf49803e/151283bytes, protected
COMPACT9e2837e4/19248bytes;3545993/start428492676 reaped/gone0 in1.501154s.
Actual empty0/unknown0/full store metadata unchanged; roles quiet and original
pause preserved. Original native23 prerequisites rejoin and close. No payload
read/hash, secret create/remove or app start. No normal lifecycle acceptance.

New observer162c15ae/runner-templateff00d2e1/coordinator55aa8986 binds actual
new authority27/control28/generations28 and baseline. Fresh normal-v1 WORK,
ARMED/workspace and future generation; old PUB23 wrapper with explicit new
manifest retained. Atomic ARMED/live original watcher, only2runtime assignments,
EOF/reap/no signals and1850/2050/2100budgets remain. Previous failed28 original
children must be freshly gone; original failures/UNKNOWN remain.34local
ownership/body/pin/EOF/overflow/NFS tests PASS3.99s and leaf lint PASS. Initial
local test-only stale suffix expectation failed; corrected to actual newv1,
all34pass before guest start. Held1361source239input preflight PASS48163bytes.
Original caller803471f5 now running as3546477/start428507192; outcome PENDING.
No second guest call until original EOF/reap. Required normal rootless browser,
strict postrun and dedicated isolation/fault/lifecycle acceptance still pending.
Source17 gate/native23 and pinned UBI10 micro shared API/UI image unchanged.
Checkpoint163 `.scratch/web-006-source17-current-state-v163.json` SHA25663196070dbce7ff273abc36907074d5eb3ca4c82031251686292f8617ebe573e.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

## Checkpoint164 — original rootless29 failure preserved; closed Basic fixture migration prepared

Original rootless29 FAIL5084e141/177791bytes, protected87129d4d/49048bytes;
3546477/start428507192 reaped/gone1 in5.409082s. Original watcher118696/
start29390235 and runner118697/start29390267 reaped/gone. Functional child
118701 returned1 in3.239385s before browser/SUMMARY. New generation62b29da3
stopped/startedFalse/containers empty, all5original pairs gone. Strict13roles/
4cgroups/5endpoints PASS. Observer ownershipFalse/payloadUNKNOWN preserved.
No application service started; certificate prestart guard PASS, failure during
credentials before secret label gates/engine secret creation.

Readonly startup channels/generation diagnostic PASS2b7237ba/149664bytes;
3546884/start428519573 reaped/gone0 in1.066791s. Functional error is deliberately
generic. Expanded read-only current control/Basic metadata PASS1ecda6cb/
197037bytes, protectedbed505f6/65876bytes;3547218/start428530567 reaped/gone0
in1.022365s. Actual218control input rows, full9Basic inode118606297/root:983/
0640 unchanged from original owner probe. No application/secret/policy action.

Source review locates two remaining private fixture guards: replace requires
existing leaf owner equal requested owner and hardcodes root0640 for every Basic
publication. Corrected inert controller2910cc0112 adds a closed Basic-only
metadata allowlist (native0:983/0640, rootless983:983/0400); other source rules and
old-owner check stay exact. Adds class/function/line-only startup diagnostics,
no exception text/locals. All Controller methods unchanged from28. New fixture
preparation preserves ONLY positively identified old Basic inode via metadata-only
RENAME_NOREPLACE into root700 owned work, no payload/hash/read/chmod/chown, before
future fresh credential creation. Current full218input prefix and all history
remain. This is owned test fixture preparation, not product guard relaxation.
Source17 strict gate/native23/UBI10 image unchanged. Dedicated acceptance pending.
Checkpoint164 `.scratch/web-006-source17-current-state-v164.json` SHA256c3805a3fc3f10377a72fb425e90da9dabb52a7019551228d8ba2d8cc40f3e582.
WEB006 remains incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

## Checkpoint165 — closed Basic fixture publication/baseline pass; original rootless30 running

Corrected authority28/controller29 preparation PASSf511510e/215365bytes,
protecteda6e30e82/81050bytes;3547744/start428548914 reaped/gone0 in6.922861s.
Controller10cc0112, control29/7e7fd6a7/42572bytes, manifest28/b0880fe7/5019bytes,
fixturec9c391c9-8829-495b-8aac-8981cfaeb147/generations29. Full218old control
input rows preserved, all unchanged profile/installed/source bytes reused.
Static validator/load_control/strict13role4cgroup5endpoint PASS, descriptor784+
32<1024 unchanged limits. ONLY oldBasic inode118606297 is metadata-only
RENAME_NOREPLACE preserved into private authority work; same owner0:983/mode0640/
size221/mtime/SID, only renamectime changes. No payload read/hash or overwrite;
source absent until new normal credential creation. Original intent/completion
records retained. Current rootless aliases also preserved NOREPLACE; no app,
secret creation/removal, kernel/policy or installed-byte change.40local fixture
metadata/controller/composition/NFS tests PASS6.74s. Docs207human/27helpers and
git diff --check PASS before this update.

Fresh authority28 baseline PASS459cef88/158048bytes, protectedCOMPACT2f1083fe/
19246bytes;3547910/start428552381 reaped/gone0 in1.503401s. Actual secret0/
unknown0/full metadata unchanged, roles quiet, original70549pause and native23
prerequisites preserved/rejoined/closed. No app/secret action or payload read.
New observer7c9a18d0/runner-template22001917/coordinator702ea27f binds actual
new authority/control/baseline/218prefix and new normal-v1 paths; original failed29
owner handles freshly gone. Atomic ARMED/original live watcher, exact2runtime
bindings, original EOF/reap/budgets1850/2050/2100 retained.34local ownership/
body/pin/EOF/overflow/NFS tests PASS4.26s and leaf lint PASS. Caller9056628a
held1361source252inputs preflight PASS48230bytes; original rootless30 executor
3548109/start428557899 RUNNING, outcome PENDING. No parallel guest calls.
Source17 strict gate/native23/pinned UBI10 micro shared API/UI image unchanged.
Required normal rootless browser/6ID3liveCID/delivered gates, strict postrun and
dedicated isolation/fault/lifecycle acceptance remain pending.
Checkpoint165 `.scratch/web-006-source17-current-state-v165.json` SHA256fe0b9f23360cb086cc2cb4b02d43f8c5358692e1875acc58d2610b706cfa87a9.
WEB006 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

## Checkpoint166 — real delivered/live-secret gates pass; API credential refusal and owned drain pending

Rootless30 original cohort FAIL3c97268f/171320bytes, protectede4e810cf/
36572bytes;3548109/start428557899 reaped/gone1 in105.090890s. Original watcher
118986/start29440939 and runner118987/start29440966 reaped/gone. Actual new
generationb5b504c3d77147aca9b54b9298c0085b startedTrue/stoppedFalse; original
statea4d99c61/176483bytes retained. All8original and5delivered secret gates PASS;
original live observer ownershipTrue/all sources closed/6ID3liveCID/no payload
reads PASS. These limited metadata/gate proofs do NOT establish normal browser
or retirement acceptance. Bootstrap280bounded GET observations returnHTTP502;
no application start replay, no browser/SUMMARY. Current API failed10/HFAPI003;
helper/worker/Caddy remain active because original stop load_control guard3
refused on2stock UID983 nsfs mounts BEFORE action dispatch. Strict closure FAIL.

Readonly diagnosticv1c6835d08 refuses exact unknown nsfs before further reads,
retains host/pause raw mount metadata. Exact2row read-only diagnosticv2 guard
passes9known/changed/foreign/missing namespace/FS tests1.79s, lint/preflight.
Actualv29477ba57/419775bytes, protectedf831c1c4/269739bytes PASS;
3548874/start428581174 reaped/gone0 in1.375803s. Two immutable NFS rows perview/
archive/70549pause/Enforcing unchanged. No general nsfs admission for mutations.
Readv3 first widened journal window refuses output budget357933bytes after real
EOF/reap; actual541f70d9/381235bytes FAIL retained. Readv4 bounds128lines and
ONLY exact API invocation668ca3c09502402b8af2dda1867e5631: PASS4e63cc94/
400863bytes, protectedc0e4b937/249809bytes;3549209/start428591744 reaped/gone0
in1.422442s. API actual119219/status10 printsHFAPI003; no credential value read.

Readv569cbcc8d/436303bytes, protected28e03a2a/282447bytes PASS;
3549646/start428606002 reaped/gone0 in1.826756s. Original live6ID/3CID ownership
receipt retained complete; actual same3cohort CIDs current. API59e56a52 is
stopped/PID0/exit10 with original finish time; worker a3798cec PID119194/
start29441567 and Caddy b5f4a4c0 PID119290/start29442046 are running. Both nsfs
mount paths exactly join original API and Caddy NetworkSettings.SandboxKey;
Caddy actual net4026532575 agrees. Other account containers ONLY3old audits.
Actual rootless server uses3/run/secrets credential paths and Basic fixed file.
No token/credential payload or digest read. Helper119151/invocationd41c4abb,
worker manager119191/d946e2d7 and Caddy manager119220/1ed613f5 unchanged.

Exact owned drain960d10a2 is prepared,9pin/unit/cohort/changed-authority/refusal/
namespace tests PASS1.91s and lint. Holds actual read/gen/authority and original
noncreating controller lock. Only fixed user stop Caddy/API/worker and system
stop helper; then rejoin all39original pairs gone, positively identify original
stopped API exit10 before exact nonforced CID removal. No restart/reset/secret
remove or original generation rewrite. Two positively joined nsfs may only
disappear; new/foreign entries refuse. Caller6f8c9954 held1361source264inputs,
preflight14866bytes. Original drain call now running; outcome PENDING. Initial
local test-only substring assertion matched false 'restarts' report label; fixed
to quoted command literal; all9pass before invoke. No production action.
Source17 strict gate/native23/UBI10 image unchanged. Normal browser, strict drain,
secret lifecycle and dedicated isolation/fault acceptance remain incomplete.
Checkpoint166 `.scratch/web-006-source17-current-state-v166.json` SHA256db6d3f3720ab91d4d2d9b0fec476b2353c05666851d6927aba1f2209367b8b73.
WEB006 uncommitted; production/NAS/installed predecessor interface untouched.

## Checkpoint167 — exact processes drained; actual metadata probe isolates unnecessary directory read

Exact original drain actual0a8e54a3/192718bytes, protectedc3880d36/50666bytes
PARTIAL FAIL1;3550499/start428638786 reaped/gone4.436222s. Both fixed original
user/system stop commands return0/reap. All39generation process pairs freshly
gone. Exact original stopped API59e56a52 nonforced removal0, exists1. Final strict
closure refuses retained original API failed10 state. Original drain remains
failed/unclosed; no service stop/removal replay. Worker/Caddy/helper are drained;
only original API failed unit state and6original secrets remain. No original
generation rewrite, secret deletion or kernel/policy change.

Same-image metadata-only Basic directory probe PASS73ee9217/184586bytes,
protected6cd0c632/42111bytes;3551017/start428656235 reaped/gone0 in3.232153s.
Actual keep-id API UID/GID981/groups981, Basic SAME inode118570589/221bytes/
owner981/0400. Direct O_RDONLY leaf open succeeds and verifies original inode
metadata without reading. O_RDONLY directory open for credential parent refuses
EACCES13. ORIGINAL read_protected_bytes then raisesHFAPI003 before0payload read
calls. Actual container_t domainc412,c843 recorded. This isolates unnecessary
read access requested on the parent directory, independently of now-correct leaf
ownership. Probe54b2cec0 exits0/PID0/noSecrets and exact nonforced retirement
passes; all original unit states/metadata remain unchanged. Initial whole-module
ruff reports dynamically exec-provided names; complete inert namespace/symtable
has no unknown globals, warnings/compile and actual probe leaf lint PASS.

Selected source correction: descriptor-pinned credential traversal should open
only directories with O_PATH|O_DIRECTORY, retaining NOFOLLOW/CLOEXEC and all
original leaf type/owner/mode/nlink/size/ACL/change checks and O_RDONLY payload
read. No directory listing/data read is needed; no SELinux grant/hardening
change follows. NOT yet implemented: first finish source17 owned exact6ID
metadata/opaque backup/failed-cohort cleanup and sole known API failed-state
reset so old callers close before a new source freeze/gate. Required new source
native/rootless installed/shared-Caddy acceptance will follow. Native23/gate17/
UBI10 image evidence stays historical/exact; no false new-source acceptance.
Checkpoint167 `.scratch/web-006-source17-current-state-v167.json` SHA256d6a14663618f0df621f716de2e02c8af07510fc003ca23f0b54f9e382f9263e5.
WEB006 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

## Checkpoint168 — failed cohort exact cleanup and strict closure pass before source correction

Current failed30 metadata PASS8c276568/418147bytes, protected7efadefd/
261130bytes;3551555/start428673263 reaped/gone0 in3.278548s. Actual6IDs/no
unknowns/full store before-after unchanged; original payload inode/gates match,
all39original pairs and2owners gone, account ONLY3old stopped secret-free audits.
Original live6ID3CID metadata ownership retained and joined, not full acceptance.

76local exact-ID/cohort/changed-input/backup-label-before-write/no-overwrite/
first-error tests PASS3.64s, lint; held1361source271input preflight23061bytes.
Cleanup115c5dde/231299bytes, protectedc548c927/83693bytes PASS0;
3551900/start428683720 reaped/gone4.850964s. Before any removal, unchanged
reviewed backup component f99d6f65 creates durable opaque whole-store tar20480B
and metadata2966B in root700 owned work; both0600root-owned leaves secret_t
labelled/rechecked BEFORE any bytes.4regular files/2dirs/8839source bytes,
source rejoined/output FDs closed, no individual payload/digest published.
All6exact-ID removals0, final empty0/unknown0; no force/all/ignore/name-only
delete or old operation replay. Failed-cohort cleanup supplies no normal browser
or complete lifecycle acceptance; original failed/unclosed receipts retained.

5actual pin/same-cohort/exact single reset checks PASS1.73s; held1361source
273input preflight16083bytes. Actual preparationdc507267/185624bytes,
protected53b3caac/39592bytes PASS0;3552280/start428696947 reaped/gone3.434807s.
Only original API668ca3c09502402b8af2dda1867e5631/Exec119219/status10 failed
unit state reset-failed. No start/restart/secret/policy action. Fresh strict
13roles inactive/PID0,4cgroups empty,5endpoints refused PASS; rootless8443 also
actually refused111. Original70549pause/NFS mounts/listener/kernel unchanged.
Source17/installed package/image and historical gate17/native23 remain exact.
All guest calls/sessions now closed; test lane quiet before canonical source edit.

Next amend credential traversal detail in existing contracts/decision152, retain
all leaf guards/ACL checks and use O_PATH directories to avoid parent read
permission. Add real owned search-only directory and adversarial regressions,
freeze new source/gate, then fresh installed native/rootless shared-Caddy proof.
No new SELinux grant/permission/hardening change. Required acceptance open.
Checkpoint168 `.scratch/web-006-source17-current-state-v168.json` SHA2569b68871176712a576635e1c70fb7a67ca4a1380ffe313445626cc7452824c963.
WEB006 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

## Checkpoint169 — narrow directory traversal correction frozen; original strict gate18 running

Contract-first correction now implemented in shared protected credential reader:
only directory opens change from O_RDONLY to O_PATH|O_DIRECTORY|O_NOFOLLOW|
O_CLOEXEC. Leaf remains readable/NOFOLLOW/nonblocking; original regular/owner/
mode/group/nlink/size/ACL/bounded-content/stable9field checks remain. Parent
search access suffices; no directory contents/listing or MAC/DAC/capability/
systemd/permission grant. Existing decision152 gains explicit refinement/rationale;
INV002/003, server/security and human deployment/troubleshooting align. This
implements existing protected source scope; no new architecture/dependency/ADR
identity is introduced. Existing140/146/150/152 reviewed; helper denials unchanged.

Real owned search-only parent regression passes, with unprivileged subject even
for a root test runner. Existing ACL FD test now requires O_PATH directories and
readable checked leaf.114ACL/adversarial tests PASS0.76s;150Basic-provider/
adversarial/real-socket/MCP acceptance tests PASS77.62s. Ruff lint/format,
207human/27helper docs and git diff --check PASS. Two initial local test commands
named absent test files and collected none; corrected exact existing nodes above
were actually run. No missing/skipped required test is acceptance.

New source18 exclusive capture PASS0.790019s, original3553486/start428724128
reaped/gone0. Capturea198f41c/684bytes;1361files/snapshotdc26fb57ae771e97a2bc29b1c59b73283088d8d7f48a1e9a577672435fc5e00a.
Inventory75c45b28/244519bytes under owned source18-local-v1-x50z8jga;
archive8c4fec54/17735680bytes. Exact8changes from17: credential reader, ACL
regression file, decision152, invariant/server/security/deployment/troubleshooting
contracts. No file additions/removals or unrelated changes. First local caller
checksum was mistyped and refused BEFORE child/output reservation; actual
captured source69f265f6 executed once on corrected exact hash, no replay.

Strict original gate18 runnerbd0cc794 now runs as3553603/start428727675:
historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`). Outcome PENDING;1361source
bytes frozen throughout. No further canonical edits during this gate; only
5excluded bookkeeping docs/ignored preparation. Source17 gate/native23/image
proof remains exact historical evidence, not new-source installed acceptance.
Guest lane is quiet after source17 cleanup/strict closure; no source18 installed
bytes or image have been built/staged/accepted. Next host-only0.2.6 fixture
metadata projection and owned prep, then actual fresh native/rootless same-Caddy
and dedicated isolation/fault/lifecycle acceptance after green gate.
Checkpoint169 `.scratch/web-006-source18-current-state-v169.json` SHA25603bb6fac3ae74e46314123540dc62752496d9f829a32aa7964267a1a921925c2.
WEB006 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

## Checkpoint170 — failed typecheck retained; source19 gate and host-only projection prepared

Actual strict gate18 FAIL1 after5.463161s at pyrefly: new test root-runner
branch used nonexistent Path.chown. Ruff passes; no tests/build or installed
acceptance inferred. Original gate3553606/start428727693 and outer3553603/
start428727675 reaped/gone. Source18 snapshot stayed unchanged; result/log
cbd0353b/775bytes retained. Corrected ONLY test branch to os.chown; runtime
O_PATH correction unchanged. Whole-project pyrefly0errors,18credential tests
PASS0.85s, lint/format PASS. No product/fixture permission or security change.

New source19 capture3880c6c8/684bytes PASS0.652808s;3554158/start428747374
reaped/gone0.1361files/snapshot586acd137b51a0d1df89e1e8abf7f5fa57c9a7df448e5231831054d8c2b9dbe5.
Inventory92f1a88b, archivee70a3d22/17735680bytes under owned source19-local-v1-
0cqr8rso. Only test os.chown difference from18; source17 exact8file delta stays.
New original strict gate19 runner6fdfd43d as3554230/start428748916 is RUNNING,
currently offline tests past49%, no failure observed. Outcome PENDING; no source
edit during it, only5excluded bookkeeping docs/ignored local prep. Failed gate18
is not relabelled. Original17/native23 remain historical, not19acceptance.

Owned HOSTONLY two-TOML source19 test projection actualfc7e6530/245248bytes
PASS0;3556608/start428762201 reaped/gone1.044672s. Source capture/archive/input
hashes/modes/1361names and canonical before/after verify. Only project.version
and hfcache self-package lock version change0.2.2->0.2.6 in new copied tree;
all other TOML/source values and all108package bytes equal frozen19. Canonical
version remains0.2.2. Fixture snapshot9daf2d5a; inputmanifeste1fab847,
archive4fc4f71d/17735680bytes. No guest/build/install/source switch/image effect
or gate acceptance. New extractor holds validated archive bytes in memory and
checks every member name/mode/hash before exclusive output; no archive-path
reopen race. New source19 preparation is independent of gate success and cannot
supply installed acceptance.

Private INERT guard4 prototype7caa096e prepares normal stock pasta namespaces:
keep exact2NFS rows perview, original archive counts/70549pause/owned listener
and unknown/external-FS refusal. Additionally at most2nsfs local NET handles in
ORIGINAL UID983 pause only, fixed /run/user/983/netns/netns-UUID grammar, net inode
root/dev0:4/rw/shared and original1015parent mount whose exact tmpfs UID983700
row must match. No host nsfs, arbitrary namespace/path/type, extra third handle
or unknown parent allowed. This admits local namespace metadata, not network
filesystem contents or an action grant; fixed generation/unit/CID authority
remains separate.30current-capture/foreign-path/parent/rights/extra-handle/old
NFS regressions PASS3.95s. Prototype is INERT/not guest-selected; no actual
runtime admission or security policy change. Actual future guest proof required.

Next new owned source19 transfer/environment/current controller bindings after
gate, fresh native/rootless shared-Caddy browsers, then dedicated isolation/
fault/lifecycle. Guest lane quiescent; original6secret cleanup/strict closure
stays. No source19 artifact is installed or accepted yet.
Checkpoint170 `.scratch/web-006-source19-current-state-v170.json` SHA256f97915e3ac43ccd310cb8048515346649885932f6673e56de9e078cd52f94c55.
WEB006 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

## Checkpoint171 — full strict gate19 and new guest source transfer pass

Actual strict gate19 PASS0 in1261.593647s, finished2026-10-24T05:36:49.093982Z.
Original gate3554231/start428748934 and outer3554230/start428748916 reaped/gone;
outer1261.795663s. Resultd88fb00f/816bytes, log535af71f/100881bytes.
All1361frozen source19 hashes/modes unchanged/snapshot586acd13.7750Python
passes/52opt-in deselections; locked base/server/server+MCP wheel install/import/
help/version checks, historical frontend checks,2786frontend units/2846components, strict
wire135definitions/lint/types/production build,2real sandboxed Chromium startup
checks and realHTTP/API React read fixture PASS. No required default skip;
installed/shared-Caddy/native/rootless/dedicated acceptance remains separate.
No rerun of unchanged full gate is needed without a new concern/source change.

New private controller30 prototypedde9de38/102941bytes INERT: source19/native
0.2.6/rootless0.2.7/control30/generations30 bindings and exact guard4 function;
all existing Controller methods retain identical AST after inverse version/
repository literals.13scope/AST/no-unknown-global/current guard tests PASS4.14s,
leaf lint PASS. Not installed/selected. Existing Basic metadata source rules
remain strict; per-profile prior Basic inode preservation is required before
switching native/rootless fixture credentials, no broad old-owner bypass.

Source19 public transfer codec prototype58b7d07 +11actual archive/name/version/
unbound-refusal tests PASS4.38s. Bound codec2d34b178/10507bytes and8member packet
95506b9a/36321280bytes prepared using ACTUAL closed gate19/channel/PID proofs,
canonical/archive/projection inputs all rejoined; host-only preparationb90310cd/
2948bytes PASS0,3573553/start428890575 reaped/gone1.396240s. No fake gate models
establish acceptance. Packet contains public source/metadata/gate data only,
no opaque secret backup, key or credential payload.

First local caller preflight refused obsolete hardcoded17snapshot BEFORE guest
execution; corrected only exact source19 snapshot admission, original refusal
retained. Root v1 entry-refusal review found it could collect into an existing
scope; unexecuted v2 rootadc48654 adds exclusive-creation/identity guards for
final collection/reporting.19actual full-packet/receipt/name/version/corrupt-
packet/no-effects-on-foreign-scope/namespace tests PASS4.17s, lint and held1361
source280input preflight PASS19474quotedSSHbytes. Original sealed memfd stdin,
fixed captured SSH/QEMU PIDfd, EOF/reap/no signals and2100budget retained.

Actual NEW source19 transferde0ed320/1094808bytes, protected8b12d83c/
901405bytes PASS0;3575050/start428954007 reaped/gone17.504837s. Fresh public
/home/webfixture/hfcache-web006-source19-fixture-v1 has1361exact fixture files,
snapshot9daf2d5a; canonical586acd13. Old SOURCE17 before/after/finally all1361
full9/hash/SID leaves preserved. Original current rootless aliases/key metadata
held/rejoined; no selector/service/policy/credential change or key body/hash.
Actual13role4cgroup5endpoint strict closure PASS before/after;39old generation
and2owner handles gone. Only new source/metadata files staged, no image/runtime
package build/install or source19 application acceptance. Guest lane idle/all
sessions closed. Next quiescent original-alias preservation/staging prerequisite
inspection, native006/new pinned UBI10 micro API+UI/rootless007 artifacts, then
fresh real same-Caddy browser and dedicated acceptance. No live rollout.
Checkpoint171 `.scratch/web-006-source19-current-state-v171.json` SHA25674a71affb4b25d4b7229a46e97449fe601d01b3246e1ff49a49092ed75453051.
WEB006 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

## Completion evidence

Completed2026-10-25, WEB-006, this commit. The final current-source strict gate,
installed artifacts, both-profile browser and isolation results, documentation
and invariant/ADR review are recorded in
[final acceptance](#final-web-006-acceptance-2026-10-25) below. Earlier failed,
incomplete and superseded evidence remains historical; no failed flag is changed.

WEB-006 checkpoint120 update2026-10-23: actual source17 strict gate and local preparation PASS.

Original gate17 exits0 after1246.827779s at21:44:01.999420Z:7749Python,
52opt-in deselections, three locked wheel profiles, preserved historical frontend checks,
2786frontend unit and2846component tests, production build, two sandboxed
Chromium startup checks and real React/API read fixture all pass. Required
frontend checks report no skips. Gate3461657/start425913701 and outer3461656/
start425913683 are reaped/absent. Gate resulte3100b94/816bytes, log4204e849/
100870bytes, wrapper5d1a3c37/738bytes. All1361frozen source hashes/modes remain
unchanged, snapshot3b146543; no installed host acceptance follows from this gate.

Bound source17 fixture metadata projectionfa1990dc/21291bytes executes ONCE,
3480555/start426043376, returns0/reaps/absent after5.419822s. Projection0a8f4d85/
260485bytes changes only copied pyproject.project.version and uv-lock self
version0.2.2->0.2.4; fixture snapshotcb64ae60/all1361files verified. Canonical
product0.2.2,108API/27UI sources and original artifact provenance stay unchanged.
Packet builder0cf7a0fd/8067bytes executes ONCE,3480679/start426046909,
returns0/reaps/absent after1.340060s; its13member packet and exact gate channels
validate locally. No source17 guest copy, build, install, authority selection
or real functional acceptance has run. Old source16/native22 failed/UNKNOWN
records and handles remain unchanged. Next: NEW source17 transfer and protected
preparation, then NEW authority23/control24 after fresh current-alias metadata.
Checkpoint120 `.scratch/web-006-source17-current-state-v120.json` SHA256917354a2b1d65cbc874e6d4a9772c504f66017f8cfef386a2a4fea906fb49825.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint121 update2026-10-23: source17 new guest tree copied and verified.

Original transfer769d860c/10299bytes FAIL1 remains preserved. Both status-query
processes106170/start26957817 and106171/start26957832 exit0/reap; saving private
channels failed before WORK creation. No public or protected packet member was
copied. Failure root JSON8d6cc21a/1634bytes is retained separately; its invocation
3481425/start426074594 returns1/reaps/absent. No original operation is replayed.
The corrected separate completion creates its NEW protected diagnostic scope
before any status query, saves the original failure unchanged, verifies both
original identities gone and uses the same held packet only for its first copy.
17local models/preflight PASS, E9/F821 PASS, all1361current source plus13inputs/
1376FDs rejoin; SSH18554bytes below120000. A malformed local hash argument refused
before process/locator creation; the exact observed64hex hash then executes.

Separate completionee425ff3/952452bytes PASS0, protected1213097d/897849bytes at
`/opt/hfcache-web006/source17-fixture-transfer-completion-v1/RESULT.json`.
Caller49c449e1/13942bytes, rootef6f84ba/53234bytes; actual3481712/start426082882
returns0/reaps/absent after19.027359s. All1361new source17 files verify full9/
hash/mode/SID, fixture snapshotcb64ae60, source snapshot3b146543. Files are labelled
usr_t while empty before bytes. All1361oldsource16 files retain full9/hash/SID
before/after/finally; current native22 aliases and metadata-only key are unchanged.
Strict13role/4cgroup/5endpoint closure and four queries0/reaped pass. The original
failed native22 remains failed. No build/install/restage/new authority/browser or
functional acceptance is claimed. Next: new readonly package projection and
prelabelled public browser inputs, then authority23/control24.
Checkpoint121 `.scratch/web-006-source17-current-state-v121.json` SHA25620209875415c4e2b8f443da7ffb4eee01034dab95ac66530e00ffab12575b728.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint122 update2026-10-23: new source17 environment and separate installed static validation PASS.

Environment8d9386ea/334987bytes PASS0, protected840fab68/310938bytes. Actual
3482454/start426110370 returns0/reaps/absent after9.119465s. Direct mount(2)
creates a NEW readonly projection preserving all108package inode/hash/SIDs,
UID1000 import passes.194new browser files/50dirs are labelled empty before
bytes;194old files/50dirs remain full9/hash/SID unchanged. Seven source17 code
files and inventorybc8787d4 selected, current CA1dbee retained. FD774+32<1024,
limits unchanged; all1361source17 files before/after/finally and strict closure
pass. Local environment models/preflight and E9/F821 pass.

Fresh23/controller24 public preparationc3eb8c13/101946bytes FAIL1 preserved,
protectedeb38c9f6/85639bytes. Actual3483129/start426132810 returns1/reaps/absent
after4.593230s;21new files published/manifest0ae5c2d2/5020bytes, static validator
returns1. All roles close; source17 unchanged, old selection unchanged. Saved
validator readf68d368e/40900bytes PASS0 (protectedbe00b339/30091): actual failure
is the fixture's .scratch mode0755 rather than required current-user-private0700.
No runtime/security contract is relaxed. Launcher8e97ea6d binds actual194/50
records/new driver; every launch/TLS/drain function AST is identical to source16.
Documents71a760b5 fixes the inert inventory lookup v16->v17 before publication;
all168control inputs remain preserved in pure models. Required guest proof is
still separate from these model passes.

Separate completion60b73cbe/51654bytes PASS0, protected925c9db1/40194bytes at
`/opt/hfcache-web006/fixture-authority-v23-completion-v1/RESULT.json`.
Actual3483966/start426161426 returns0/reaps/absent after5.447450s; caller0ba59805/
12328bytes, root2996fe09/35377bytes. Only owned .scratch mode0755->0700 and ctime
change; original inode/owner/SID/entries preserved. All21published files and
194browser files/50dirs stay unchanged. The installed UID1000 validator106392/
start27044658 passes, wrapper106391/start27044657 returns0/reaps, both identities
gone. All108readonly package files and1361source17 files remain unchanged;
FD815+32<1024, five queries/validator processes0/reaped and strict13/4/5closure
pass. Original publication remains FAILED; this is a new correction/validation
receipt, not its promotion or a publication replay. No control24/sudoers/selector
change or browser/app-service execution yet. Next: locked control24 preparation,
preserve fresh native22 aliases and prepare native23/strict postrun before run.
Checkpoint122 `.scratch/web-006-source17-current-state-v122.json` SHA256dfd20b6b49eece268ac03e32ddbe92e9e70c559b2f417cbb7659fe9d8ab730fa.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint123 update2026-10-23: control24 preparation PASS; ORIGINAL native23 RUNNING.

Selection30ffcff6/75417bytes PASS0 (protected2dabc4bd/60041bytes), actual3484814/
start426191646 returns0/reaps/absent after4.887578s. Control24 SHA256e27358e6/
34151bytes inode43477818 preserves all168prior inputs plus8new protected records
(total176). Controller24 actual load_control equality and visudo pass; scoped
sudoers v23 and generations24 prepared. Original noncreating lock43335379 and
metadata-only key78157344 stay unchanged. Three native22 aliases are preserved
with renameat2 NOREPLACE under fixture-authority-v23-selection-v1/native22-*:
selector60372219, deployment78518898, policy78518899, all original SID/inodes/
mtime preserved; only ctime advances. Seven CLI processes0/reaped, strict13/4/5
closure,108readonly package and1361source17/borrowed public files unchanged.
FD815+32<1024. Fifteen actual local rename/lock/refusal tests PASS, E9/F821 PASS.
First local preflight fails its FD count because ctypes initializes after the
baseline; no guest call/selector action. New preflight initializes library first,
then all held sources/FDs rejoin/close and passes; original failure retained.

New native23 rootf88566e4/38747bytes binds authority23/control24/manifest0ae5c2d2,
unchanged checker7af9b0ba and runner9a5e43f7. New callerbbdeb6b8/14732bytes and
strict post template3849e61f/21144bytes are bound BEFORE execution. Post remains
NATIVE_PIN=None until actual receipt, correctly targets generations24; earlier
unused v1draft stays INERT. Six local runner/post tests PASS and held preflight
passes1361current source files+20inputs, actual prior wrapper/channels/protected
selection hash, unchanged source gate17 and exact QEMU/SSH identity. No failed
native21/22 invocation is retried or promoted.

ORIGINAL native23 starts ONCE:3485500/start426215529, session56962, stem
`.scratch/web-006-original-native-functional-source17-authority23-v1-execution`.
It is RUNNING; no PASS/result/functional acceptance claimed. Root runner budget
1800s, owned SSH budget2100s, original EOF/reap/no automatic kill preserved.
Only this original invocation owns the guest lane until exit. Current aliases
were absent after selection preparation; native23 may activate NEW aliases, so
fresh actual metadata is required later. Next: wait on THIS session, preserve
actual outcome, bind prepared strict postrun to its exact receipt. Native/rootless
isolation, remaining faults/retirement acceptance stay incomplete.
Checkpoint123 `.scratch/web-006-source17-current-state-v123.json` SHA25681c36c38f4ff31d6d35746033a0bc111535acd52383f1a785a46b0a6b629e258.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint124 update2026-10-23: ORIGINAL native23 and strict postrun PASS.

Native23e14ab38f/45644bytes PASS0, protectedb4ffc5c7/31543bytes. Actual3485500/
start426215529 returns0/reaps/absent after331.488119s; runner106479/start27098665
returns0/reaps after329.706514s. Original checker7af9b0ba and fixture0.2.4 installed
API execute built UI -> SAME real Caddy with current trusted TLS. All four modes
baseline/helper-down/restarted/timeout complete; SUMMARY exists, no required
skips/retries. Native21/22 failures and UNKNOWNs remain unchanged; no replay.

Prepared strict postrun binds ONLY this actual receipt: rootbce1020f/21328bytes,
caller11621499/11967bytes. Held1361source/14input preflight and E9/F821 PASS.
Actual3486717/start426258619 returns0/reaps/absent after2.633729s; collection
 a365464c/86696bytes PASS0, protected7dc92b2a/72974bytes. Generation
`ece999e6efd342a3882aba73b3e45574`, stateb6fcec6c/58016bytes under generations24;
SUMMARY110d414f/383168bytes. All THREE engines pass7baseline+2helper-down+
1restart+1timeout cases (33host/UI assertions total), one attempt each. Every
mode's three untrusted engines also refuse the SAME Caddy/current CA once
(12certificate refusals total), and before/middle/after TLS epochs agree.
No TLS ignore, mock, failed-read retry or forced browser close is used.

All8exact trusted/untrusted CIDs actually inspect as exited0/PID0/notOOM;
original init/client identities closed. All43generation application processes,
original runner and5top-level CLI identities are gone; strict13role/4cgroup/
5endpoint closure passes. Original summary/profile cleanup_unknown=false;
no required skip or retry. This establishes the native23 browser cohort only.
Rootless, dedicated peer/role/secret isolation, supplemental faults, exact secret
ownership/retirement and full WEB006 acceptance remain pending. Current aliases
can now reflect native23 activation; use fresh actual state before later changes.

Inert normal23 prerequisiteaf8f71fa/16917bytes was derived locally from reviewed
normal21 code with actual selection schema/source17 paths; future generation/
record pins remain UNBOUND until this PASS is adopted. Old21 successor templates
remain permanently inert and unmodified. Next: bind actual native23 normal
proof, then rootless baseline/live ownership watcher/one original rootless run,
followed by required isolation/fault/lifecycle cohorts. The shared API/UI image
keeps original source15/pinned UBI10micro provenance; no rebuild/reinstall/restage.
Checkpoint124 `.scratch/web-006-source17-current-state-v124.json` SHA256752bfa44bae411bb625927f0fb272aa38b588442d2ffd0933de22b52bd03908e.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint125 update2026-10-23: native23 normal prerequisite and EMPTY stock983 baseline PASS.

Normal publicatione0afb9a0/55700bytes PASS0, protected598fe2b0/43329bytes.
Actual3487932/start426307931 returns0/reaps/absent after3.987100s; root6251a9ec/
52077bytes, caller64747ee5/12832bytes. Bound common code9c67021d/18099bytes
is private root0600/usr_t at private-normal-code-source17-authority23-v1/
normal-readiness.py (inode78600735), labelled empty before bytes. It revalidates
actual seven native result/SUMMARY/generation/control/authority/manifest/checker
records,33browser cases and protected delivery/hygiene metadata. Public SAFE
projection2e587711/5167bytes is container_file_t:s0, labelled before bytes.
All48native app/CLI identities are freshly gone,1361source17 files unchanged
before/after/finally, four status queries0/reaped and strict13/4/5closure pass.
Eight local binding models/held1361source15input preflight and lint PASS. Old21
successors remain inert; existing source15 runtime artifacts keep provenance.

NEW rootless23 metadata baseline5c92dbcd/31883bytes PASS0, protecteddabc9574/
15832bytes at rootless-secret-baseline-source17-authority23-normal-v1/RESULT.json.
Its protected serialization is COMPACT sort_keys JSON+newline, not indent2.
Actual3488631/start426334160 returns0/reaps/absent after1.414381s; caller0d118511/
13030bytes, rooteef9f963/40744bytes. The native parser now accepts EXACTLY its
actual two additional strict pre/post guard fields and independently verifies
13inactive units,4empty cgroups,5refused endpoints for each; no field is dropped
or inferred. Eight local actual-receipt/hostile guard/pause tests and held1361
source15input preflight/lint PASS before execution.

Stock UID983 secret listing is EMPTY: count0/unknown0/no rows, complete safe
store metadata before==after, no new/missing/changed paths or engine-created
store. Pause70549/start6647855/UIDGID983 remains user:[4026532304]/mnt:[4026532305].
All13roles are quiescent before/after; five metadata/status CLI children return0/
reap, kernel45bb unchanged. No payload body/digest, key or credential is read;
no explicit secret creation/removal/replacement/store write, ownership grant,
retirement or application start occurs. The next required step is a NEW live
ownership watcher armed before ONE original rootless generation. Actual six-ID/
three-CID ownership, rootless browsers, strict postrun, dedicated isolation/fault
and exact-ID retirement remain unaccepted. Native23 acceptance stays preserved.
Checkpoint125 `.scratch/web-006-source17-current-state-v125.json` SHA256142c2594df1550c2f4b1acd036a5da43c173aff13eb691f539bf5063cddb0eb3.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint126 update2026-10-23: NEW original paired rootless23 coordinator RUNNING.

New observerb5da1ead/52075bytes adapts actual selection23/control24/empty compact
baseline dabc9574 and pause70549. Protected ARMEd metadata is fully written and
fsynced before atomic renameat2 NOREPLACE publishes ARMED.json; four real local
filesystem tests PASS for complete inode-preserving handoff, existing/missing
source/destination and non-directory refusal. No existing file is overwritten.
Earlier unused observer0381a389 remains inert. Original runner templateeae39529/
37482bytes preserves its methods except explicit current authority schema/path/
source bindings; ARMED_SHA256/WATCHER_SHA stay UNBOUND until actual live handoff.

Coordinatoraa1a4f26/129948bytes owns BOTH original children under one guest call.
It requires actual native23 PASS and empty baseline, starts the metadata-only
observer, holds/verifies live PID/start/source hash and atomic ARMED record, then
binds exactly two runner assignments and starts ONE original rootless runner.
Both children use captured verified code; no file-loader reopen, credential
payload collection, replay, automatic signal or secret retirement. Primary errors
survive cleanup; real EOF/reap of both children precedes publication on every
entry path. Eight local coordinator tests PASS: actual child early-EOF/late-exit,
overflow drained/reaped without signals, first entry error retained while the
same child drains, and exact two-field/runtime-pin validation. Lint PASS.

Prepared readonly postrund8c25d0f/91397bytes remains COORDINATOR_PIN=None until
actual result. It checks all4modes/3engines,8exact browser CIDs,3live-owned app
CIDs,6original secret IDs, original process/pause closure and strict13/4/5guards;
no app start/secret body/digest/retirement. Current native23 acceptance stays
preserved; dedicated isolation/fault/exact-ID lifecycle acceptance stays pending.

Caller e4340ac0/14475bytes captures current1361source files plus18pinned inputs,
actual compact baseline/executor/channels, observer/runner templates and prepared
postrun. Local preflight0df73814 PASS0/reaped/closed, four binding checks, guest0;
all prior source/gate/QEMU/SSH proofs rejoin. Owned SSH budget2100s; runner1850s/
watcher2050s owners retain original EOF/reap, without automatic kill.
ORIGINAL paired invocation starts ONCE:3492279/start426492665, session92181,
stem `.scratch/web-006-rootless23-coordinator-v1-execution`. It is RUNNING;
no rootless functional PASS/result/acceptance claimed. Only this coordinator
owns the guest lane until all original children close. Next: wait on THIS session,
preserve outcome and bind its prepared strict postrun; never rerun the cohort.
Checkpoint126 `.scratch/web-006-source17-current-state-v126.json` SHA2566c0084b36350eb34b1169db85a9bff98dccdfa24ae43a5656c5404a58a3ef021.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint127 update2026-10-23: first coordinator setup FAIL preserved; corrected setup RUNNING.

Original coordinator-v1e99a3df9/43706bytes FAIL1, protected7feac8d4/30579bytes.
Actual3492279/start426492665 returns1/reaps/absent after1.433398s. Observer111937/
start27375775 exits1/reaps; no original_runner entry, ARMED or application launch.
Five original children are gone, strict13/4/5closure passes. Saved observer
stderr93587b23/722bytes is retained. Separate readonly diagnostic355c5f6d/
41209bytes PASS0, protectedd44a924b/30304bytes;3492874/start426515637 returns0/
reaps/absent after1.199847s. It confirms missing path fixture-authority-v23/
RESULT.json: the actual authority is fixture-authority-v23-selection-v1/RESULT.json.
Observer work/ARMED and original rootless runner work are actually ABSENT.
No rootless application operation was invoked, no failed invocation is replayed.

New observer65b3d375/52084bytes and runner28f35c3d/37491bytes bind the authority
path by AST assignment to the actual receipt, replacing fragile literal matching.
New coordinator781a7db3/131044bytes pins original failure+diagnostic and requires
that failed setup had no runner and diagnostic observed absent scopes before
proceeding. Old v1 and its handles/false flags stay unchanged. Nine corrected
local lifecycle/path tests PASS, including both paths/hashes against actual
selected receipt; previous four real atomic handoff tests remain PASS. Lint PASS.
Prepared post636a5fd0/91408bytes stays unbound for coordinator-v2 only.

Caller60a1fd83/17927bytes pins28inputs/current1361files, actual empty compact
baseline, failed setup and saved diagnostic execution/channels/protected hashes,
new observer/runner and prepared post. Preflightb7eca9ed PASS0/reaped/closed,
no guest call; all held source/gate/QEMU/SSH and fields rejoin. Corrected setup
starts ONCE as3493718/start426548196, session50231, stem
`.scratch/web-006-rootless23-coordinator-v2-execution`; currently RUNNING.
No corrected result/rootless PASS/acceptance or secret retirement is claimed.
Only this call owns the guest lane until both original children close. It can
launch the FIRST actual rootless23 application invocation only after a valid
live atomic ARMED handoff. Next: wait on THIS invocation, preserve outcome,
bind the already prepared strict postrun to its actual result. Required dedicated
isolation/fault/exact-ID lifecycle evidence remains pending; native23 stays accepted.
Checkpoint127 `.scratch/web-006-source17-current-state-v127.json` SHA2561f64a73d90d33962a5859905eb3d092248a95ca431e6a782c445c2406deea3d1.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint128 update2026-10-23: corrected coordinator and FIRST rootless run FAIL; closed diagnostics isolate a fixture empty-list parser defect.

Original corrected coordinator-v2 local68298c55/67485bytes, protectedf5b9b8de/
48201bytes FAIL1;3493718/start426548196 returns1/reaps/absent after5.790317s.
Atomic ARMED99fd55eb succeeded with live watcher112027/start27431305, then
FIRST rootless driver112028/start27431325 and functional child112032/
start27431352 returned1/reaped. No invocation is replayed. Generation41b7055e
is stopped=true/started=false/containers=[], six tracked processes gone.
Observer exited0 but explicitly records successful_ownership_proof=false,
all_sources_closed=false/error_class=ValueError; payload-read/digest field UNKNOWN
is retained. No ownership or secret retirement is inferred from its exit code.
The missing SUMMARY caused a secondary FileNotFoundError; primary startup refusal
is preserved independently. All coordinator/driver children are gone and strict
13role/4cgroup/5endpoint closure passes.

Separate readonly original-run diagnostic269ea27c/protectedd1287fe0 PASS0.
Boundary read e15ecaa6/43385bytes/protectedc0c5ba68/32340bytes PASS0;
3495076/start426604772 returns0/reaps/absent after1.268161s. Certificate
prestart phase=passed, public inputs closed, more than515708seconds remaining;
no expired-TLS failure. No service-start or secret-label gate was reached.
Six original generation PIDs freshly gone; workspace filename metadata retained.

A NEW readonly exact engine-list probe54f978a5/43504bytes/protected0349e321/
31452bytes FAILs with JSONDecodeError after actual metadata child112266/
start27523599 returns0/reaps with stdout ZERO bytes and empty stderr. Its
execve UID/GID983, empty supplementary groups, cwd / and environment match the
executed controller. This reproduces the fixture's unconditional json.loads on
empty stock Podman secret-list output. Outer3496008/start426640503 returns1/
reaps/absent after1.371944s; strict closure still passes. Empty output alone is
not a complete current ownership/store proof. No payload body/digest or secret
retirement occurred. Original failure remains failed. A local builder syntax
error and malformed wrapper arguments were refused before any guest action;
corrected finite reader artifacts are separately preserved.

Next: guarded correction in a NEW controller/authority scope, actual empty-store
metadata proof, fresh live ownership watcher, ONE new rootless generation and
its strict postrun; required dedicated isolation/fault/exact-ID lifecycle proof
remains pending. Source17 canonical1361files/gate17 and native23 PASS remain
unchanged. All earlier failures/UNKNOWNs/handles are retained. Shared shipped
API/UI image remains pinned UBI10micro. No production/NAS/installed predecessor interface changes.
Checkpoint128 `.scratch/web-006-source17-current-state-v128.json` SHA256f2b71a1e9f3476d7ac84e25015d64cdc74e8e19828965ba080d261cefa91b5b5.
WEB-006/AUTH-08/HOST-01–03 remain incomplete/uncommitted.

WEB-006 checkpoint129 update2026-10-23: fixture controller25 corrected; NEW authority24/current baseline PASS; rootless24 RUNNING ONCE.

Controller99bfb5ee/112373bytes adds bounded require_empty_secret_listing:
only actual zero-byte successful stdout or explicit JSON [] is empty; malformed,
null/object/nonempty output remains refused before creation. Only credential
parse and control25/generations25 assignments differ; original start/stop,
bootstrap, permissions and bounded process ownership are unchanged. Eighteen
regression tests PASS. New launcher0410b08c/98829bytes changes only manifest path.
No canonical product source/runtime byte changes, rebuild/reinstall/restage or
policy/security relaxation. All1361source17files remain frozen/gate17 PASS.

New authority24 first preparationa502d304/82592bytes FAIL1 (3497095/
start426678468/reaped/gone4.795255s), protected145ae862/65322bytes.
Actual installed static validator and controller load pass; a missing DOCUMENTS
reference stops before the first preservation intent/rename or sudoers activation.
Original failure stays failed. Separate completion actually completes preservation
of all3rootless23 aliases by NOREPLACE, same inodes/SIDs/mtime (ctime only),
new fixed sudoers and full8published-record/194public-file/50directory/108ROpackage
proof, used778+32FDs<1024, strict closure. Protected completion57106dba/60192bytes
PASS; outer3497427/start426688956 exits1/reaped/gone5.544738s because the local
classifier wrongly requires an absent error_class key. Its local KeyError/false
flags remain unchanged. No completed action is replayed.

Separate readonly admission2b26c631/50111bytes/protectedd708f95e/32780bytes PASS0:
3497820/start426701252/reaped/gone1.400888s. It rejoins all8published inodes,
new control25c2b3d244/35384bytes, controller/manifestaa1c02f5/5019bytes, original
noncreating lock and key METADATA ONLY; controller load equals captured documents,
original176control inputs preserved in order, generations25 empty, aliases absent
and preserved identities exact, all completion processes gone and strict13/4/5
closure. This independent admission establishes new readiness, never promotes
original failed preparation or local classifier. Fixture UUID749bc2aa-bd29-41c4-
9e33-18c5940cda71. No application service/container or secret payload operation.

NEW stock983 baselineaf147ae0/33173bytes/protectedaa4bc19b/16058bytes PASS0:
3498010/start426706785/reaped/gone1.452087s. EMPTY0secrets/unknown0, complete safe
store metadata unchanged/no created paths, same pause70549/start6647855/userns
4026532304/mntns4026532305, all13roles quiescent. Original native23 prerequisites
remain independently bound; fresh authority24 admission also held/closed. No
payload body/digest, key, credentials, ownership/retirement or application start.
Protected baseline serialization is compact sort_keys JSON+newline.

New observer906d3d6d/45883bytes and runnerd593dbd9/34624bytes bind new authority,
workspace, baseline/control/controller and UUID; exact atomic ARMED and original
EOF/reap lifetimes remain. Runner borrows unchanged old public run-host-fixture-v1
wrapper while passing explicit NEW manifest; no nonexistent new wrapper assumed.
Coordinatorv1 local tests found stale absolute receipt paths; preflight found an
old execution basename. Both were refused before guest action and remain inert.
New coordinatorv2defe919e/52126bytes binds all exact current paths. Twenty-eight
local parser/child lifetime/runtime-pin/current-receipt tests PASS3.85s; lint and
held1361source/30input preflight PASS (quoted SSH42699bytes<120000). Prepared
post203e30d0 remains unbound/inert and still needs full current-field review.

Original NEW rootless24 coordinator starts ONCE as3498897/start426734374,
session83865, callerc3b5a8e6/18534bytes; currently RUNNING. Only this call owns
the guest lane. Fresh live atomic ARMED precedes ONE new generation; two runtime
pins only, no replay of original23 operations, no automatic signals/retirement.
Next: wait on THIS invocation, preserve outcome and bind/review strict postrun;
dedicated isolation/fault/exact-ID lifecycle acceptance remains pending.
Checkpoint129 `.scratch/web-006-source17-current-state-v129.json` SHA256437d8573246b0f6c581e698f95a0ba4dbbe7d9df5399643ff5fa223cea5c5132.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint130 update2026-10-23: rootless24 FAIL; real installed mount prerequisite identified. Checkpoint129 RUNNING wording was already stale when saved; this corrects that bookkeeping error.

Original coordinator3f7c902c/57261bytes/protected36590fa0/37552bytes FAIL1;
3498897/start426734374 returns1/reaps/absent8.509060s. Atomic ARMED735e87e3
was live and matched fresh empty baseline, watcher112488/start27617477/runner
112489/start27617499 and original functional child112493/start27617530 all
closed. New generatione5ce5fef49254d1791ede5ca5eedb207/control25 started=true,
stopped=true, containers=[], all17recorded processes freshly gone. Its original
prestart secret gate PASSED8actual inode/kernel read-open denials, kernel45bb
unchanged, sequence47. No delivered gate/browser/feature acceptance follows.
Observer ownership=false/all_sources_closed=false/ValueError; payload-read/hash
UNKNOWN remains UNKNOWN. Six created fixture secrets remain preserved; no
retirement is authorized by a matching name or this failed observer.

Separate readonly failure diagnosticd80a0ea1/67918bytes/protected306e3bed/
48609bytes PASS0;3499681/start426759829/reaped/gone1.204860s. All original
coordinator identities and17generation PIDs gone. Worker/caddy user units remain
FAILED (MainPID=ControlPID0, no active cgroups), so strict13role/4cgroup/5endpoint
closure does NOT PASS. No reset-failed/stop replay or hidden acceptance. Worker
InvocationID6f4f288c41ed48098dc8c3a6f66c9a93/ExecMainPID112647/status20;
Caddy4181e0ce36dc493191411cdaeb7eb8f3/112649/status125. Generationdceba6fa/
14636bytes and original stop evidence preserve all17gone, empty recordedgroups/
containers and four refused rootless helper/API/worker/TLS endpoints.

Readonly saved journal+fixed-container queryf0af7ae6/61857bytes/protectedaf6f99d0/
41974bytes PASS0;3500166/start426776007/reaped/gone1.411618s. No fixed app
containers exist. Bounded UID983 original startup window: worker reports fixed
container-boundary refusal; API dependency fails; Caddy then reports missing
/run/hfcache/api and exits125. Raw channels were privately labelled before bytes;
public projection suppresses private-key/password markers and long/authorization
values. Failed first readerTypeError (unsupported collect keyword) and earlier
inert/missing-entry/shadowed-scope/refused-argument diagnostic attempts remain
preserved; no application invocation was replayed by any read.

Actual captured INSTALLED0.2.5 container-service.py8a692faa/47743bytes was run
through read-only preflight at UIDGID983: profile load and exact worker command
construction PASS; archive_readonly() raises RuntimeError with the exact known
read-only NAS mount barrier unavailable message. No prepare_start, container
exec/start/drain, service action, archive content or secret access occurs.
Receiptb5e63156/50738bytes/protected386f2ccd/30478bytes PASS0;3500768/
start426796800/reaped/gone1.289944s. rpc.nfsd and exportfs already exist; no NFS
client/server filesystem registered, and no package/module/mount action occurred.
This confirms XFS synthetic storage cannot satisfy the unchanged production
worker's real read-only NFS prerequisite. Bypassing that guard would be invalid.

Next authorized environment work: prepare a separately recorded owned LOOPBACK
NFS export of synthetic guest data, without accessing any external NAS or
weakening the product mount guard/SELinux/systemd constraints. Before effects,
prove exact existing mount/server/listener/process/secret ownership and preserve
all old fixture inputs/evidence. New private fixture guards may admit ONLY that
proved localhost export/mount and continue refusing every external/unknown
network/shared mount. Do not reinterpret earlier XFS/native evidence as NFS or
production acceptance. Preserve the original pause and namespaces; verify both
host and pause mount views before any future application generation. The six
failed-cohort secret IDs need separate conservative ownership review before any
retirement. No old run/stop/start is replayed, no service reset silently clears
failed evidence, and no current rootless normal/negative/lifecycle PASS exists.
Checkpoint130 `.scratch/web-006-source17-current-state-v130.json` SHA256cf92501042317220218c73335591b43318e0a0819f1b1c53cb565f040d97db50.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; source17/native23 PASS retained; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint131 update2026-10-23: owned loopback NFS prerequisites measured; no server/export/mount/module effect yet.

Readonly inventory4e1080b2/53157bytes/protected75a314bf/31818bytes PASS0,
3501850/start426834691/reaped/gone1.215379s. Matching kernel6.12.0-275 modules
nfs.ko.xz and nfsd.ko.xz exist. NFS-server/mountd/rpcbind service/socket are
inactive with zero processes/cgroups; ports111/2049/20048/32048/32049 unused.
/etc/exports is the original empty inode16908571; etab/rmtab/state are absent.
Installed utility help is captured; exportfs does not support --help and its
usage refusal is retained, not silently treated as a successful help option.
First two inventory readers refused an assumed read-only pause mount; their
failed receipts remain. Corrected observational reader preserves raw mount rows.

Host /srv/hfcache is XFS535/shared:1 on the owned archive-seed, flags
ro,nosuid,nodev,noexec. Original pause70549/start6647855/mnt:[4026532305] sees
XFS536/master:1 with RW,relatime. This second real fixture defect is not accepted
as rootless read-only archive proof. Do not repeat a bind-then-remount sequence
that can propagate a writable initial mount; require read-only NFS at creation
and actual proof in BOTH host and original pause namespaces before any app run.
The original XFS inodes/views remain preserved and no archive contents were read.

Readonly label/tool preflightacf6a4c6/26021bytes/protectedd52ab871/5193bytes
PASS0,3502284/start426850413/reaped/gone0.783961s. Existing SELinux booleans
nfs_export_all_ro=on/nfs_export_all_rw=on are measured, NOT changed. No SELinux
boolean/type/policy relaxation is authorized. Original synthetic seed root
inode118335700/root0:0/0755/hfcache_archive_t is unchanged. Four actual installed
NFS utility binaries have full9/hash/SID pins; no package install is needed.

Next private fixture preparation may load those existing vendor NFS modules,
create ONE explicitly localhost-only read-only export of the owned synthetic
seed, run separately named owned NFS test-tool units and mount its NFSv4 view
with read-only/nosuid/nodev/noexec flags at creation. Require original export/
listener absence, utility/source/namespace identity, exact localhost endpoint,
unchanged kernel policy/booleans and original borrowed inputs. Preserve the old
XFS mount and all failed application/unit/secret evidence. Probe a NEW owned
client mount before selecting /srv/hfcache; require actual host+pause NFS-ro
views and bounded UID983 denial. Do not start any application or change/reset
its failed units or retire secrets in that preparation. All external/unknown
NAS/shared mounts remain refused; no synthetic result establishes production
NAS acceptance. Record every effect/handle and partial failure without replay.
Checkpoint131 `.scratch/web-006-source17-current-state-v131.json` SHA256fa697e734e096284e9a0d5c58b837e0925bcbedf113c8faa0cebac8c5b6f761c.
WEB-006/AUTH-08/HOST-01–03 incomplete; source17/native23 PASS retained; no production/NAS/installed predecessor interface changes.

WEB-006 checkpoint132 update2026-10-23: localhost NFS preparation failed with partial owned effects; exact original export independently reconciled, no replay.

Vendor unit read3a9b1aba/29527bytes/protectedbc9175cc/8589bytes PASS0;
3502874/start426873086/reaped/gone0.784624s. Default root NFS service security
properties are retained; new independently named test tools will compare all
security fields against the actual vendor units, with no removal of confinement.
Nineteen export-client/RO/squash/unknown-state/actual failed-unit preservation
tests PASS1.62s; lint and held1361source39input preflight PASS. An initial local
preflight expected37inputs and refused before guest action; corrected count39.

Actual original server preparation066f3845/70554bytes/protectedd8f523ac/
45778bytes FAIL1:3503743/start426906169/reaped/gone3.044682s. Exact vendor
modules nfsd/nfs loaded successfully and NFSD control mount created (three0
children); original exportfs returns1. The recipe stops before any mountd/NFSD
unit, client mount, archive projection, app/unit reset or secret action. All
phase/intent/channel records retained under /opt/hfcache-web006/loopback-nfs-v1.
Original failure remains failed; never rerun these effects on an empty-baseline
assumption. No app/source/image/SELinux/boolean or hardening change occurs.

Separate readonly diagnosticaa99e4ea/44030bytes/protected85fcc83c/19693bytes
PASS0,3504029/start426915997/reaped/gone1.045603s, all original CLI identities
gone. Saved export stderr says it could not open previously absent etab for
reading. Despite return1, the original effect DID publish exactly one export:
owned archive-seed ->127.0.0.1, ro/sync/secure/root_squash/no_subtree_check/fsid0.
Do NOT replay it. New etab inode10403883/root0644/var_lib_nfs_t/229bytes is
captured as metadata; original empty /etc/exports inode16908571 unchanged,
rmtab/state still absent. NFSD threads0; control mount760/0:55/shared621 at
/proc/fs/nfsd. Kernel policy45bb unchanged. Application failed states/secrets
remain retained and no NFS client mount exists.

Next: separately versioned completion must hold original failure+readonly
reconciliation, verify the exact current export/etab/control/module/source/
namespace/security inputs, and adopt ONLY that already observed original effect.
It may start the first separately named mountd/NFSD tools with bounded exact
localhost listener proof; no export replay, app action, client mount or secret
retirement. Subsequent client/host/pause RO validation and fresh authority,
rootless browser/isolation/fault/lifecycle acceptance remain necessary.
Checkpoint132 `.scratch/web-006-source17-current-state-v132.json` SHA2569e83833cc57cdc9921ef3ebcd139ab5d79558715d4e6518b97df48e7ed6203e1.
WEB-006/AUTH-08/HOST-01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint133 update2026-10-23: first owned mountd is live; separate completion metadata parser FAIL preserved, NFSD/client mount not started.

Twenty-nine local export/adoption/original-failure preservation tests PASS3.06s;
lint and held1361source43input preflight PASS. Separate completion6e1e309d/
75130bytes/protected55061cac/48071bytes FAIL1,3504636/start426937929 returns1/
reaps/gone2.566078s. It adopts the independently observed original localhost
RO export without reloading modules, remounting control or replaying exportfs.
First ONLY tool effect start-owned-mountd returns0. Actual independently named
unit web006-loopback-mountd-v1.service is active/running, MainPID113311/
start27821165, InvocationID27440f83be924c72981e70e1158edda3, fixed cgroup,
exact original foreground argv. No restart/replay/automatic signal occurs.

Original raw recorded SELinux context is system_u:system_r:nfsd_t:s0 followed by
NUL. The parser used text.strip(), which does not remove that terminator, and
refuses before vendor-security comparison or NFSD startup. This is an observed
private metadata encoding issue, not a domain transition failure. Original raw
context/false flags/outcome stay unchanged. No policy/type/boolean/hardening
change. NFSD threads remain0 (not yet freshly recollected after this refusal),
NFSD unit/client mounts/app/failure-reset/secret retirement were not invoked.

Next completion must use a bounded exact raw-context decoder preserving all raw
bytes, adopt ONLY the SAME live mountd PID/start/unit invocation/executable/argv/
cgroup and verify vendor security properties. Never start mountd again or
promote the old completion. Then the FIRST NFSD tool start may proceed, with
exact localhost listener/version/thread proof. Client/host/pause read-only
NFS validation and rootless real browsers/isolation/lifecycle remain pending.
Checkpoint133 `.scratch/web-006-source17-current-state-v133.json` SHA256a25aca7f076f2b9a7161652d2246c8ad4e1c3dd9b08290a73c366e278c34353a.
WEB-006/AUTH-08/HOST-01–03 incomplete; original app failures and6secrets retained; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint134 update2026-10-23: SAME live mountd/context/security validated; FIRST NFSD tool invocation FAIL on unsupported NFSv2 option.

Closed proc-context decoder preserves actual raw hex/length/hash and permits
only the observed terminal-NUL nfsd_t representation; embedded/extra terminators,
other domains/MCS/whitespace/types refuse. Thirty-nine local guard/adoption/raw
context/no-replayed-effect tests PASS4.74s; lint and held1361source46input
preflight PASS. Original mountd-start completion remains failed/unmodified.
New completiona9c4da96/78372bytes/protectedc452b5b2/49641bytes FAIL1;
3505444/start426968241/reaped/gone2.618132s. It verifies SAME mountd113311/
start27821165/invocation27440f83be924c72981e70e1158edda3, exact argv/cgroup,
host user/mount namespaces, live pidfd and canonical observed nfsd_t context.
All vendor security properties match. No mountd/module/export/control replay.

FIRST NFSD unit invocation web006-loopback-nfsd-v1 is attempted once and fails.
Separate readonly diagnosticc154f429/60747bytes/protected657f64fe/32100bytes
PASS0;3505789/start426980953/reaped/gone1.228446s. Exact saved unit is failed,
MainPID=ControlPID0/empty cgroup, ExecMainPID113363/status1,
InvocationIDec12afcf7e114d598c90af2ef7884f5a. Journal's exact reason:
2: Unsupported version. Current supported tokens are +3 +4 +4.1 +4.2;
NFSv2 is absent and this installed utility rejects even the disable-v2 option.
No NFS listener, threads0, no client mount; original localhost-only RO export
still matches. Kernel45bb and original export booleans unchanged. Mountd remains
SAME live process with vendor security equality. App failures/6secrets unchanged.

Next new completion must pin both old NFSD failure and its closed readback,
preserve that failed unit without resetting/restarting it, rejoin SAME mountd,
and admit only the known zero-thread/no-listener state. A separately named
web006-loopback-nfsd-v2 tool may omit unsupported v2, disable supported v3,
enable v4 and use the standard localhost2049 port, already observed unused.
Retain raw version tokens; do not invent a -2 token or infer a port/SELinux
failure that was never observed. No port label/boolean/policy/hardening change.
Original modules/control/export/mountd are adopted, not replayed. Only after
actual localhost listener/vendor security proof may client and host/pause
read-only NFS validation proceed. Required real rootless acceptance stays pending.
Checkpoint134 `.scratch/web-006-source17-current-state-v134.json` SHA2566964d1de93adaba17e7ed8a37a7b1524a578b9b43129ccb78fd04721dd322d75.
WEB-006/AUTH-08/HOST-01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint135 update2026-10-23: owned localhost NFS server readiness PASS; no client/archive/app mount change yet.

A new completion-v3 phase label included uppercase NFSD and was correctly
refused by its bounded owner grammar BEFORE any effect; original1902972c/
80311bytes/protected8a22c7c5/48959bytes FAIL,3506559/start427009437/reaped/
gone2.384564s. No NFSD-v2 start occurred. Corrected separate scope v4 pins this
failure, normalizes only its NEW phase label and retains the old record. Added
static phase/effect grammar regression;49local guards/adoption/context/version/
no-replay tests PASS7.34s. Lint and held1361source54input preflight PASS,
quoted15898bytes<120000. Original failed NFSD-v1 remains unmodified.

Actual completion-v4 local813ef83e/112069bytes/protected6a2037c2/77461bytes
PASS0:3506975/start427024162 returns0/reaps/gone5.031139s. It adopts only
reconciled original module/control/export and SAME mountd113311/start27821165/
invocation27440f83be924c72981e70e1158edda3, live pidfd/argv/cgroup/host
namespaces/raw nfsd_t context. All vendor security properties match. Its ONE
new effect is the FIRST NFSD-v2 start, return0; no old start/export/module/mount
operation is replayed and no failed unit is reset.

web006-loopback-nfsd-v2.service is active/exited success, MainPID=ControlPID0/
empty cgroup, ExecMainPID113507/status0,
InvocationID5006567266d949d2bcb45fd79652ee53. Two kernel NFSD threads are
observed. The ONLY monitored NFS listener is actual tcp127.0.0.1:2049,
kernel inode709143/state0A. Raw versions are -3 +4 +4.1 +4.2; no invented
v2 token. Export remains exact owned synthetic seed to127.0.0.1, ro/secure/
root_squash/fsid0. Original unsupported-v2 unit/status1 is preserved separately.
Mountd/NFSD service security equals installed vendor defaults; kernel45bb,
existing booleans, original utility/unit/seed metadata and all1361source full9/
hashes/SIDs before/after unchanged. Original app failed states/6secrets retained.

This establishes TEST SERVER readiness only. No NFS client mount exists and no
archive contents, app role, failed-unit reset or secret retirement occurred.
Next a NEW owned client mount must use exact localhost NFS4.2/TCP2049 and
ro/nosuid/nodev/noexec at creation, prove live server/export binding, actual
UID983 EROFS and unchanged source/security. A new private fixture guard may
admit only that exact owned NFS mount and reject every external/unknown mount.
Then host+original pause archive views require actual NFS-ro proof, followed by
new authority, conservative exact-ID secret lifecycle and one fresh rootless
normal cohort/required isolation/fault checks. No rootless feature acceptance.
Checkpoint135 `.scratch/web-006-source17-current-state-v135.json` SHA2560195f20790fd050b089b88384f3ca7f623f1082358ff6c0f3bcbb70b46c9ced4.
WEB-006/AUTH-08/HOST-01–03 incomplete/uncommitted; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint136 update2026-10-23: actual owned NFS4.2-ro client and UID983 EROFS PASS; archive namespace projection still pending.

Thirty-two private mount/network guards PASS1.70s: wrong target/IP/filesystem/
version/port, writable/missing-hardening/soft mounts, duplicate/unknown shared
mounts, changed/wildcard listener and external client refuse. Raw permitted
loopback TCP transition rows are retained beside a required established client;
they are never substituted for the listening socket or actual NFS mount proof.
Lint and held1361source57input preflight PASS; both actual mount executable and
hash-pinned installed mount.nfs are held through the original invocation.

Original client receipt7346a4d7/91820bytes/protectedf4cace9c/56890bytes PASS0;
3508511/start427085701 returns0/reaps/gone3.836264s. ONE original mount child
113577/start27968900 returns0/reaps0.332182s with empty streams. New client
mount766/dev0:58/shared624, nfs4 127.0.0.1:/, ro/nosuid/nodev/noexec/relatime,
vers4.2/hard/TCP/sec=sys/clientaddr127.0.0.1/addr127.0.0.1. Kernel omits its
default port field; explicit original argv requests2049 and independent actual
loopback TCP tuples bind it to the SAME listening inode709143 at127.0.0.1:2049.
No alias/default-port inference alone establishes that conjunction.

Actual dropped UIDGID983 probe uses only the NEW client root FD: statvfs RO,
exclusive write-open returns errno30/EROFS, no file created. EACCES/EEXIST or
other errors do not count as RO. No source payload, archive contents or secret
value read/hash. All1361source full9/hashes/SIDs, owned server/export/PID/
namespace/security/booleans, old failed application states and6secrets unchanged.
Only the new client mount was targeted. Its no-pause-change flag describes no
explicit pause-target command; it does not establish shared-mount propagation
or a read-only archive view in that namespace. Those remain to be inspected.

Next project the same proved NFS-ro view into host and ORIGINAL pause archive
views, after fresh exact mount/source/namespace ownership proof. Preserve all
old XFS inodes/mount evidence; isolate only the owned shared bind's propagation
where necessary to avoid overmounting the protected export source through a
shared peer. This isolation tightens mount propagation, never relaxes SELinux/
systemd or readonly flags. Pin the original pause namespace FD/PID/start and
use only fixed mount targets/source handles; retain each original effect and
partial failure without replay. Require actual NFS-ro and UID983 EROFS in BOTH
views, unchanged export source, before any fresh app generation. No app/reset/
secret retirement is authorized by this client-readiness result. Every future
guest tool must admit ONLY the exact proved owned localhost mount(s), refusing
all external/unknown NAS/shared filesystems; old no-NFS templates remain inert.
Checkpoint136 `.scratch/web-006-source17-current-state-v136.json` SHA256f960870068e15b13562b4755b672cae457ac9657a48d9bb7a6cf65850620da27.
WEB-006/AUTH-08/HOST-01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint137 update2026-10-23: independent exact archive/namespace read PASS; projection intent bounded before effects.

Readonly views receipt c6a082da/66503bytes, protected1a4dc82a/31959bytes PASS0;
3510139/start427156252 reaped/gone1.249155s. ORIGINAL pause70549/start6647855
and pinned namespace inode4026532305 remain alive. Client766/767 is already
NFS4.2-ro in host AND pause through observed shared propagation; archive535
is original XFS-ro/shared1, pause536 original XFS-rw/master1. Protected export
source inode118335700/full9/SID unchanged and not overmounted. All actual
filesystem kinds and namespace links recorded. No mount/app/secret effect.

Next isolate ONLY owned host archive535 propagation with make-private before
NFS bind, preventing shared-peer overmount of export source. Bind SAME proven
RO client into fixed host and ORIGINAL pinned pause archive targets. Preserve
lower XFS identities/raw evidence. Require source/export/security/source1361
unchanged plus actual UID983 EROFS and installed readonly preflight in BOTH.
No application start, failed-unit reset, secret retirement or effect replay.
Checkpoint137 `.scratch/web-006-source17-current-state-v137.json` SHA256f534449768e64ba8c1518f8937ede9598d2b22109f4854f988db842f35c2fec6.
WEB006/AUTH08/HOST01–03 pending; native23/gate17 unchanged.

WEB-006 checkpoint138 update2026-10-23: actual host+ORIGINAL pause NFS-ro projection and installed UID983 preflight PASS.

First projection14cc8317/protectedcd16b528 FAIL before effects: namespace full9
timestamps changed. Independent readonly read0b4e4b33/protected251d68b1 PASS,
3512232/start427236320 reaped/gone1.200263s; exact views unchanged. Original
namespace dev4/inode4026532305/first7 fields/PID70549/start6647855 match; only
mtime=ctime differs between opens. Original failure stays failed, effects empty.
New tool compares semantic namespace identity to history and verifies its
CURRENT full9 for the retained FD lifetime, with original PID/start and pidfd.
29local regressions PASS1.72s; lint and held1361source67input preflight PASS.

New projection9a900a77/132704bytes, protected1be000bd/90356bytes PASS0;
3512455/start427243391 reaped/gone3.905217s. Exactly three original effects
return0/reap: make ONLY host archive535 private; bind SAME proved NFS-ro client
to host archive765; bind to ORIGINAL pinned pause namespace archive780.
Lower original XFS535/536 retained. Protected physical export inode118335700/
full9/SID unchanged, no source overmount. Exact listener709143/export/server
security/kernel45bb/booleans and1361source full9/hash/SIDs before+after unchanged.

BOTH actual UIDGID983 probes return EROFS30/statvfsRO/no created file; BOTH
unchanged installed0.2.5 load_profile/fixed-worker-command/archive_readonly()
preflights PASS. NFS mount is4.2/TCP/localhost/ro/nosuid/nodev/noexec/hard/sec=sys.
No app start, failed-unit reset, secret read/retirement or old effect replay.
Original failed worker/Caddy states and observer UNKNOWN remain; strict role
closure and rootless/browser/isolation/fault/lifecycle acceptance still pending.
Old no-NFS tools remain inert. Next conservative failed-cohort6secret exact-ID
ownership review, fresh NFS-aware authority, explicit exact failed-state prep,
then ONE fresh rootless normal cohort and dedicated required checks.
Checkpoint138 `.scratch/web-006-source17-current-state-v138.json` SHA25630d2f78bb8f3b2e99d1a86831a232b1dcb775358dc63cf8b3b5f9b09fcda8b8f.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint139 update2026-10-23: conservative failed-cohort secret metadata read PASS; no deletion yet.

Readonly receipt d723dc2b/115681bytes, protectedf8cce47f/73130bytes PASS0;
3513052/start427263281 reaped/gone1.779062s. Exactly6fixed file-driver secret
IDs, no unknowns, stock inspect metadata only/NO SecretData requested. All six
CreatedAt=UpdatedAt in original23:39:57 create order/window after original empty
baseline and before stopped generation. Original payload inode127749655/full9/
SID matches recorded passed prestart gate; complete safe store before/after
unchanged. Original17PIDs gone. Projection/server/app failures unchanged.
Podman secret events EMPTY and journal metadata has NO Podman creation events;
these establish NO event-based ownership proof. Observer UNKNOWN preserved.

Separately scoped FAILED-BEFORE-CONTAINER cleanup may explain only these exact
6IDs using pinned original empty baseline + sealed controller's completed6create
stage before passed prestart gate + stopped original generation + matching live
inspect/creation order/window/store inode metadata. No name-only/unknown delete.
Require noncreating original controller lock, zero account containers, fresh exact
IDs/inspect/store equality, per-ID original intent/result and empty final list.
No collector payload body/hash; stock engine removal may internally read/rewrite
its own store. This branch NEVER supplies normal6ID/3liveCID secret lifecycle
acceptance, promotes observer failure, resets a failed unit or replays any app.
Fresh successful normal+dedicated lifecycle cohorts remain mandatory.
Checkpoint139 `.scratch/web-006-source17-current-state-v139.json` SHA256d18112f9e7234ac3ecd4ad76a6c86e91371ae77730eb7f190c71b0940c6d3891.
WEB006/AUTH08/HOST01–03 pending. Production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint140 update2026-10-23: failed-before-container exact6ID cleanup PASS; normal lifecycle acceptance still pending.

Cleanup-v1 FAIL6f688bf1/protected0be55c75 before any removal: raw secret-list
order differs. Separate completion retains raw278bytes/hash6d999e3c, verifies
complete metadata equality keyed by exact ID; no field/unknown-ID relaxation.
Cleanup-v2 FAIL1e194ef7/protectedf7d55e09 before removal: account contains THREE
retained image-audit fixtures, not zero. Original claims/receipts stay failed.
Reference reader-v1 template field Id refused125 before modification; readonly
v2 PASS165b4fc6/protected00d44ba2,3514293/start427304683 reaped1.572013s. Exact
3audit CIDs are exited0/PID0/notOOM/noSecrets, finishedOct21/22 before cohort.
No unknown/live/secret-using container is admitted and no audit is removed.

36adversarial ownership/retained-container tests PASS1.70s, lint and held1361
source80input preflight PASS. New cleanup-v3 local77999054/126678bytes and
protectedf8368711/78493bytes PASS0;3514499/start427310202 reaped/gone4.535258s.
Original empty baseline/completed6create stage/passed prestart gate/17gone and
creation order/window + current original payload inode/full9/SID/complete store/
exact6IDs/inspect equality are joined under original noncreating controller lock.
Only6original per-ID Podman removals return0, each with intent/result and exact
remaining set; final list empty0/unknown0. Original2unit failures unchanged.
Three old exact exited/secret-free audit containers rechecked and preserved.
No collector payload body/hash; engine performs its own normal store rewrite.
This is FAILED-FIXTURE cleanup only: observer UNKNOWN and failed cohorts remain
unmodified, normal6ID/3liveCID lifecycle and rootless acceptance NOT supplied.

Next explicit separate prep may reset-failed ONLY exact known worker invocation
6f4f288c/status20 and Caddy4181e0ce/status125 after preserving before/journal/
original gone/cgroups/no app proof. No unit start/restart, no unknown reset or
old application replay. Require all13fixed roles inactive,4cgroups empty,5
endpoints refused before fresh NFS-aware authority/cohort. No production change.
Checkpoint140 `.scratch/web-006-source17-current-state-v140.json` SHA256b54e6a8de8a5381ca041b03fc67ac780475416911aabb87c98a2b9d33dc9f30b.
WEB006/AUTH08/HOST01–03 pending; gate17/native23/source1361 unchanged.

WEB-006 checkpoint141 update2026-10-23: explicit known failed-unit preparation PASS; actual strict fixture closure restored, no app replay.

Local unexecuted preparation-v1 syntax typo was caught before guest admission;
invalid draft/caller retained. Separate reviewed-v2 lint/held1361source82input
preflight PASS. Actual3d6c2ab0/81752bytes, protected2231c982/35105bytes PASS0;
3514922/start427322979 reaped/gone3.280696s. Holds original journalaf6f99d0,
failed generationdceba6fa/17gone, exact6ID cleanupf8368711/finalempty, original
noncreating controller lock, original pause70549/start6647855/pidfd and current
namespace FD/full9. Before requires ONLY exact worker6f4f288c/status20 and Caddy
4181e0ce/status125 failed, no app PIDs/cgroups. ONE reset-failed child returns0
for ONLY those2user units, no start/restart or replay. Original receipts unchanged.
After all13fixed roles inactive/PID0,4fixed cgroups empty,5endpoints refused:
strict closure PASS. NFS host/pause projection and source1361 full9/hash/SIDs
before+after unchanged, original pause alive. New acceptance not yet attempted.
Next fresh NFS-aware private authority/controller, fresh empty baseline/live
watcher, ONE new rootless normal cohort plus required isolation/fault/lifecycle.
Checkpoint141 `.scratch/web-006-source17-current-state-v141.json` SHA25697b0f92cd3ed5defe70fb68f8e4e6cde447dac05c315de91e960bdcb94a5ea16.
WEB006/AUTH08/HOST01–03 pending; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint142 update2026-10-23: NFS container policy prerequisites PASS; new authority25 static marker mismatch FAIL preserved before activation.

Readonly NFS policy read e7bfa085/protectedbe943a76 PASS0;3515486/start427343201
reaped/gone1.358621s. Actual target nfs_t:s0; existing virt_use_nfs ON; active
kernel seq47 permits requested container_t dir getattr/search/read/open and file
getattr/open/read. Kernel45bb unchanged before/after, Enforcing; no boolean/label/
policy/hardening change, archive content read or application start. Strict closure
PASS. This is prerequisite evidence only, never actual container I/O acceptance.

New private controller26 changes ONLY control/generation paths and closed owned
NFS fixture guard; original Controller class/all application methods AST unchanged.
Exact host765/766 and original pause767/780 NFS rows/socket709143/PID bindings;
unknown/external filesystems refuse; only owned default rootless engine overlay
paths may be admitted.19local adversarial/AST tests PASS1.79s; composed-root
name/entrypoint/work audit, lint, held1361source92input preflight PASS;55688<120000.

Actual authority25 prep facf2a0a/98631bytes, protected725f2c5f/46170bytes FAIL1;
3516640/start427387562 reaped/gone4.204449s. SIX new files published exactly once
(controller26,launcher,2profile launchers,marker,manifest); original metadata/SIDs
retained in failed receipt. Static validator refuses marker scope text introduced
by this tooling; exact required scope is owned isolated WEB006 only. No control26,
generation26 directory, sudoers25, alias preservation, activation or app start.
Original current rootless24 selector/deployment/policy remain, strict closure PASS.

Next new completion must pin original failure and all6published full9/hash/SIDs,
never rewrite/relabel/replay them. Create only new marker/launcher/manifest v2
filenames with exact reviewed marker scope, validate actual installed package,
then publish control26/preserve original aliases NOREPLACE/install only scoped
fixture sudoers. Keep fresh fixture UUID949ea0af-c6fd-40f0-8d3e-b99f0cb6e989,
source17/runtime/package/image unchanged. No rootless acceptance inferred.
Checkpoint142 `.scratch/web-006-source17-current-state-v142.json` SHA256062ef390589db318a59f29f6f518ebafc12dbbe0ed633f1ce9fc1b3851339f85.
WEB006/AUTH08/HOST01–03 pending; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint143 update2026-10-23: separate authority25/controller26 completion PASS, no old publication rewrite or application start.

Composed name/marker/entrypoint/adoption audit and held1361source96input preflight
PASS;55969<120000. Original authority25 marker refusal stays failed. All6original
published full9/hash/SIDs held/rejoined unchanged. Only NEW marker-v2, browser
launcher-v2 and manifest-final-v2 files are created, with exact reviewed scope.
Actual installed validator asUID1000 PASS against same readonly108file0.2.4
package projection. Original6files/oldsource/publications not rewritten/relabelled.

Actual completion c818d908/131388bytes, protectedbc7397c5/75143bytes PASS0;
3517256/start427410577 reaped/gone5.474649s. New fixture949ea0af-c6fd-40f0-8d3e-
b99f0cb6e989; controller26 hash8d968403/116310bytes, control26 hash7144c1e0/
37141bytes; all183old control inputs preserved in order plus10explicit inputs.
New manifest4900f165/5025bytes at authority-v25/...v25-final-v2.json; browser
launcher254f25b3/98832bytes. Controller load equality and exact owned NFS guard
PASS. Original rootless24 selector/deployment/policy preserved by3NOREPLACE
renames to completion scope, with intent/result/current inode/SID evidence;
current aliases absent until NEW controller selection. Only new scoped sudoers25
installed after visudo PASS. No services/timers/credentials/kernel changes or
old run replay. Source1361/full9/hash/SIDs before/after/finally and readonly
package108files unchanged. Strict13role/4cgroup/5endpoint closure PASS. Actual
FDused780/soft1024/reserve32, unchanged limits. No normal rootless acceptance.

Next fresh authority25 empty secret baseline and newly bound NFS-aware live
observer/runner/coordinator, then ONE new rootless normal functional cohort.
Old no-NFS templates remain inert. Original native23/gate17 retained; required
rootless and dedicated isolation/fault/lifecycle acceptance remains pending.
Checkpoint143 `.scratch/web-006-source17-current-state-v143.json` SHA256f89dfc4266d47bb178e08c8f379a4e6d83731373e3a9fb26b11758f715e3c181.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint144 update2026-10-23: authority25 fresh empty baseline PASS; ONE new normal rootless coordinator prepared, not yet invoked.

Baseline42673de3/80292bytes, COMPACT protected9e8ccb8f/19258bytes PASS0;
3517707/start427426660 reaped/gone1.405445s. Actual stock983 empty0/unknown0,
complete safe store before/after unchanged; original pause identity retained,
strict role closure PASS. Original native23 prerequisite/authority25 completion
held/closed. Only exact owned NFS guard differs from old no-NFS baseline; no
secret payload, app role or old run replay. This baseline is historical once
NEW credentials are created; never assume current emptiness later.

New authority25 observer89fde507/49863bytes and runnerb7e8f892/38599bytes bind
actual control26/manifest-v2/controller26/completion/baseline hashes and original
70549namespace. Normal6ID/3liveCID ownership and delivered gates remain mandatory.
Coordinator4c9d43c7/57288bytes preserves original paired-child EOF/reap, atomic
ARMED/source-command hash and ONLY2runtime assignments. Latest failed24 children
are freshly proved gone, never replayed/promoted. Stronger all183input prefix
proof replaces older168field check; new completion explicitly preserves183.
Borrowed original authority23 runner wrapper unchanged; new manifest passed
explicitly.29real-child/binding/mount guards PASS3.63s, leaf lint and composed
dependency audit PASS. Local caller-v1 preflight missing ast import refused
BEFORE guest call; invalid draft/failure record retained. New caller-v2 preflight
PASS held1361source104inputs;47766<120000, original SSH EOF budget2100s, no auto
signals/retry. Ready to invoke ONCE; no rootless acceptance inferred yet.
Checkpoint144 `.scratch/web-006-source17-current-state-v144.json` SHA256fbad984929b650f71852b966d6387be60b6019700581e3424b641d28388feba1.
WEB006/AUTH08/HOST01–03 pending; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint145 update2026-10-23: first authority25 coordinator refuses stale embedded-body scalar pins BEFORE children/app; strict closure PASS.

Original c5a9c466/87648bytes, protected33a4d656/29927bytes FAIL1;
3518774/start427465234 reaped/gone1.277407s. New embedded observer/runner bytes
were correct; their separate scalar SHA assignments retained old values because
a textual replacement assumed spacing. Refusal occurs at body checksum check,
BEFORE watcher, ARMED, runner, secrets or application generation. Original
latest failed24 children freshly gone, source/authority/baseline held, final
strict13role/4cgroup/5endpoint closure PASS. No app operation admitted/replayed.

New coordinator scope rootless25-coordinator-v2 pins that original failed
setup record and requires its no-child/strict-closure facts. AST assignment
updates actual observer89fde507 and runnerb7e8f892 scalar pins. Added direct
exact-body SHA regression;30local real-child/binding/mount tests PASS3.77s.
New rootbd8ea3c5; caller-v3 preflight held1361source107inputs PASS,47849<120000
and2100s original SSH EOF budget. Ready for FIRST normal app cohort under new
scope; old setup failure remains failed, never replayed/promoted. Documentation
alignment PASS207human/27helpers. No rootless acceptance yet.
Checkpoint145 `.scratch/web-006-source17-current-state-v145.json` SHA2569a5c7ea9af0764079417c511e674bfbc8a7a76f3fd12b4a471beba2e93506043.
WEB006/AUTH08/HOST01–03 pending; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint146 update2026-10-23: actual authority25 normal run FAIL at protected helper startup; original generation/journals retained, no browser acceptance.

Actual coordinator beb19c36/96109bytes, protectedea4b0b4b/36571bytes FAIL1;
3519284/start427482943 reaped/gone7.221447s. Live watcher114592/start28366019
ARMED6dd4df59 matched fresh authority/baseline before runner114593/start28366041.
Original functional child114597/start28366069 returns1/reaps5.263804s. No SUMMARY
or browser cases. Original failed scopes remain failed; no replay or acceptance.

Readonly startup diagnostic986b28c7/protected549e3f59 PASS0;3519834/start427502414
reaped/gone1.361900s. Generation0a14f7465cfc4f0185d5e463ff682dc8/efd6d888 is
started+stopped, no containers/ready;16original PIDs and watcher/runner freshgone.
Original8input prestart gate PASS; six fixture secrets created, NOT retired.
Observer394d13cc ownershipFalse/payload-read UNKNOWN/all_sources_closedFalse
retained. ONLY system helper failed/invocation98906cde7f484316b3045068b5df2615/
status20, PID0/empty cgroup; user API/worker/Caddy remain inactive/unstarted.
Journal shows protected helper fixed generic startup refusal. Strict closure is
NOT accepted while helper failed; no reset/restart performed.

Known fixture defect: host /srv has BOTH original lower535XFS-ro and upper765
NFS-ro rows. Unchanged _inspection_archive_mount requires one non-autofs row
and refuses this ambiguity. Worker mount barrier itself passed earlier; do not
weaken the host inspector to accept a synthetic stack. Next correct ONLY owned
guest mount topology under exact zero-executor/lock/PID namespace proof: tighten
guest root71 shared propagation to private (mount moves under shared ancestor
are unsupported), move SAME765 NFS-ro to owned private parking, move original
535 XFS-ro to owned preserved parking, then move SAME765 back as sole host
archive row. Original source inode/RO client/server and original pause536/780
remain; no unmount, payload read/write, app/reset/secret action or old-effect
replay. Intermediate host availability is explicitly unaccepted; actual apps
stay stopped and physical RO NFS client/export never become writable. Require
all source/security/server/mount IDs and actual983EROFS host+pause before new
authority/failed-secret cleanup/fresh cohort. Production is outside this scope.
Checkpoint146 `.scratch/web-006-source17-current-state-v146.json` SHA256f39cffcbcebf01642226109cdb28e87425ab7fffd62a55f6e631eb712eac34b4.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint147 update2026-10-23: actual sole host NFS-ro archive view and unchanged installed inspector PASS; original mounts preserved.

18local stage/identity/flag/namespace/effect allowlist tests PASS1.68s; lint and
held1361source112input preflight PASS18511<120000. Actual27192336/175927bytes,
protected953da425/109874bytes PASS0;3521619/start427577374 reaped/gone4.066254s.
Original source/server/PID/namespace/zero-executor/lock proofs held. Exactly4
first effects return0/reap: make guest root71 propagation PRIVATE (nonrecursive);
move SAME765NFS-ro to owned parking; move SAME535XFS-ro to preserved-original-XFS
parking; move SAME765 back to /srv as ONLY host archive row, now parent71. No
unmount or mount-ID replacement. Temporary uncovered host path proved empty,
root-owned/local/no group/other write; intermediate availability NOT accepted.
No app executor can run: original controller lock held, all13fixed roles PID0/
empty cgroups (only known helper98906cde failed),4cgroups empty,5endpoints refused.

Original physical export inode118335700/full9/SID unchanged, original NFS client/
server/export/socket709143 and original pause mount rows unchanged. SAME original
70549namespace FD/pidfd and mountd remain live. Existing RO flags never changed.
Actual UIDGID983 in HOST+PAUSE receives EROFS30/statvfsRO/no probe file and both
unchanged installed worker readonly preflights PASS. Most importantly unchanged
installed _inspection_archive_mount now returns nfs-ro against actual HOST rows.
No host-inspector guard relaxation, app/reset/secret operation or replay.
Source1361/full9/hash/SIDs and server/security/kernel45bb/booleans unchanged.
Old XFS535 retained RO at /opt/hfcache-web006/host-archive-single-view-v1/
preserved-original-XFS; original pause536/780 retained. Old guards pinned to
765parent535 are INERT now. New exact guard must bind actual765parent71 and
unchanged client766/pause767/780, refusing every other NFS/external filesystem.

Next failed25 exact6ID metadata/lifecycle review (current secrets not read or
removed here), known helper failed-state preparation, fresh authority26/controller27
and ONE fresh normal cohort. Original failed25/observer UNKNOWN remain. Native23
and gate17 unchanged; full rootless/isolation/fault/lifecycle acceptance pending.
Checkpoint147 `.scratch/web-006-source17-current-state-v147.json` SHA2569ecead5bb4351ea0cdbbdefcbae1df956f9d1da66c7071eb277e44a0e0a34de3.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint148 update2026-10-23: installed rootless readonly stage/bindings PASS and failed25 six-ID metadata PASS; new NFS receipt/index preparation required.

Actual installed-profile3e1bc66d/protecteda49c2fde PASS0;3522592/start427613484
reaped/gone1.489325s. Exact installed host_policy602767a6 performs original
rootless stage/index/rendered policy/binding verifier and single-host archive
classifier:74files/799588bytes, nfs-ro. CONFIGURATION and REVISION_KEY are NOT
read; key/config buffers remain empty. No daemon/domain acceptance or payload
read implied. Current helper still failed98906cde/status20. Guard-v2 local
mutation test found duplicate NON-NFS mount IDs were not refused; no mutation
used it. Readonly profile probe used actual unique kernel rows. New guard-v3
adds closed unique mount IDs, exact archive counts (host765only; pause536/780),
keeps exact4NFS rows and old-private external-fs refusal;20tests PASS1.75s.

Failed25 metadata41ab6138/133849bytes, protected3b37aee0/65196bytes PASS0;
3523516/start427649569 reaped/gone3.166091s. Exactly6known file-driver IDs, no
unknowns; default inspect has NO SecretData. Complete store before/after same;
original payload inode/full9/SID matches original passed prestart gate. Original
generation0a14f746/16PIDs freshlygone. No payload body/digest, retirement, unit
reset or source/policy change. Original observer ownershipFalse/UNKNOWN retained.
Readonly semodule --list-modules=full --checksum succeeds: loaded helper CIL
priority400 SHA2565e343f13ff66a591350c6db582eb1debd7746b784f263d552704f602184fac3e.

Actual NFS archive type is nfs_t; existing provisioning receipt still attests
old local hfcache_archive_t. Host-administration/security contracts explicitly
require fresh receipt/index on administrative label change. Do not ignore this
or weaken policy. Root-owned next fixture preparation must preserve original
fixed receipt inode/bytes, create new receipt differing ONLY archive label and
current verified provisioning facts, rebind NEW protected native/rootless
deployment/policy descriptors (same versions/artifacts and configuration-only
grants), no CIL/module/boolean/permission changes. Fixed receipt is NOT among
old193control inputs, so historical prefix can remain unchanged. Original
control/receipts/profiles and failed cohorts stay preserved and inert.

Next separately reviewed failed25 exact6ID cleanup under original empty baseline/
completed create stage/passed gate/creation window and original lock, preserving
only3known exited0/no-secret image audits; then ONLY exact helper failed reset,
new receipt/index prep and strict closure before fresh authority26/controller27.
No normal6ID/3liveCID lifecycle acceptance or app replay inferred.
Checkpoint148 `.scratch/web-006-source17-current-state-v148.json` SHA256750c263ed2d5ec431d81973f38b5d9643d11f9253bf26a31112334cf53a04678.
WEB006/AUTH08/HOST01–03 pending; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint149 update2026-10-23: failed25 exact6ID fixture cleanup PASS; original observer failure/UNKNOWN not promoted.

29local cohort/timestamp/ownership/exact-removal tests PASS1.74s, lint and held
1361source124input preflight PASS17576<120000. Actual0bff17cf/147453bytes and
protected53df5c49/76656bytes PASS0;3525184/start427720443 reaped/gone4.495850s.
Original empty9e8ccb8f baseline, failed generationefd6d888/16freshgone, original
watcher+runner freshgone, sealed controller8d968403 and passed prestart6create
stage are joined with exact6live IDs/inspect metadata, creation order/window
and original store payload inode/full9/SID under original noncreating lock.
Only3historical exact exited0/PID0/noSecrets audits are admitted and preserved.
All6first per-ID removals return0, exact remaining set checked after each; final
empty0/unknown0, complete safe store. No force/all/ignore/name-only or unknown
secret deletion. Collector does not open/read/hash payload; stock engine performs
its own store removal. Original known helper failure98906cde/status20 remains
unchanged, no reset/start/replay. Normal6ID/3liveCID lifecycle acceptance remains
FALSE, original observer394d13cc ownershipFalse/payloadUNKNOWN preserved.

Next prepare new nfs_t installation receipt and NEW native/rootless protected
descriptor/policy copies with unchanged versions/assets/config-only grants.
Preserve original fixed receipt inode/bytes by explicit NOREPLACE moves; verify
actual current nfs_t/loaded module checksum/kernel and no source/policy change.
Then ONLY exact known helper reset and strict closure, fresh authority26/controller27
and new cohort. No prior app acceptance or operation replay is inferred.
Checkpoint149 `.scratch/web-006-source17-current-state-v149.json` SHA256ded608f30db07fc3f2f0eca83151f3a6df9e0d1db0ce44032414c85497d755ef.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint150 update2026-10-23: fresh actual-NFS label receipt and NEW descriptor/policy copies PASS, no policy/grant/service change.

15local receipt/type/module/index/exact-byte policy-link/non-broadening/atomic
preservation tests PASS1.67s, lint and held1361source127input preflight PASS
15666<120000. Actual6d8eeacf/110475bytes, protected62d52b6a/40430bytes PASS0;
3526379/start427771288 reaped/gone2.626308s. Actual current nfs_t, loaded CIL
checksum5e343f13, installed source CIL and kernel45bb join original old receipt.
Product closed schema validates complete new candidates BEFORE fixed-path change.

Original receipt inode78232543/bodyd0e28181 preserved NOREPLACE at
/opt/hfcache-web006/nfs-label-receipt-v1/preserved-original-host-helper-selinux.json.
NEW prelabelled receipt moves NOREPLACE to fixed /etc/hfcache/host-helper-selinux.json,
inode78601867/SHA79f3db35/1091bytes/root0644/ConfSID. Parsed receipt changes ONLY
archive role hfcache_archive_t→nfs_t; every other label/module/kernel field stays.
Existing kernel/source/module/booleans/permissions unchanged, no policy reload.
Master-key inode78157344/full9/SID held metadata ONLY; body/digest never read.

NEW protected files under same owned receipt scope: native deployment831af976/
policycbad31d5; rootless deploymentae50d0f7/policyc1ce5ca4. Only descriptor's
selinux_installation_sha256 and its policy deployment_sha256 change; original
versions0.2.4/0.2.5, exact artifacts/assets and configuration-only grants remain.
All original profile files preserved. Candidate labels established while empty,
original controller lock held through data-only provisioning. Original helper
failed98906cde/status20 and all13role PID0/cgroup state unchanged; no reset/start,
secret operation, old-effect replay or source/artifact rewrite. Current OLD
deployment intentionally refers to old receipt until NEW controller selection;
old controllers are inert and no availability is accepted from this preparation.

Next ONLY exact helper failed reset with original journal/gen/cleanup/receipt
proof and strict13role/4cgroup/5endpoint closure; fresh authority26/controller27
uses NEW profiles/receipt and exact NFS guard3. Fresh baseline/live normal cohort
and required isolation/fault/lifecycle remain pending.
Checkpoint150 `.scratch/web-006-source17-current-state-v150.json` SHA256da3ec46d5ae98ebe5628466cb2e2f7a25462ff847cd5519be7bb5f3f0794fb38.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint151 update2026-10-23: ONLY known helper failed-state preparation PASS; strict fixture closure restored without startup.

Lint/held1361source129input preflight PASS12969<120000. Actuald7344a83/103581bytes,
protectedf9044f0b/32851bytes PASS0;3527039/start427797697 reaped/gone1.294537s.
Original failed25 diagnostic/gen/observer/runner freshgone, exact6ID cleanup and
new NFS receipt prep are held/rejoined. Current fixed receipt79f3db35/nfs_t held.
Before requires ONLY exact failed helper98906cde7f484316b3045068b5df2615/status20/
PID0; all other fixed roles inactive/PID0. Under original noncreating controller
lock ONE system reset-failed hfcache-host-helper.service returns0/reaps. No app
start/restart, secret/policy/receipt operation or old app replay. After all13fixed
roles inactive,4cgroups empty,5endpoints refused: actual strict closure PASS.
Original70549pause and exact NFS guard3 still match. Original failures unchanged.
Next fresh authority26/controller27 with nfs_t receipt/new protected profile
indexes; old controls are inert. New baseline/live paired normal cohort and
required dedicated isolation/fault/lifecycle acceptance remain pending.
Checkpoint151 `.scratch/web-006-source17-current-state-v151.json` SHA25630f88b960bfc6f23aa1bfc59577ccef5c3ad99bd778ee19b638efcb06d8c91c3.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint152 update2026-10-23: new authority26 preparation stopped before control installation or application startup.

Pre-invocation review corrected stale browser profile pins;26local tests and
held1361source137input preflight PASS. Actual cc45d93a/119615bytes, protected
8ff3f59d/44092bytes FAIL ValueError at saved/captured record-shape comparison;
3529692/start427909643 returns1/reaped/gone3.927596s. Five exact controller/
launcher/marker files are preserved. No new profile copies, manifest, control,
sudoers, selection preservation or app generation was installed. Final actual
13role/4cgroup/5endpoint strict closure PASS, source17 unchanged.

Separate completion holds the original failed receipt and all5file full9/hash/
SIDs, reuses their original inodes without republishing, and joins captured
metadata plus actual length/hash explicitly. New public profile copies bind
exact protected new-receipt descriptors/policies BEFORE installed validation;
original193control inputs preserved.28local regressions PASS3.38s; completion
held1361source140input preflight PASS57060bytes. Completion is prepared only,
not yet invoked. No old failure or UNKNOWN result is promoted.
Checkpoint152 `.scratch/web-006-source17-current-state-v152.json` SHA256b6c494f3ea888f18005f38dd5e2103f845cf0a57910394aaa61b484a965da198.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint153 update2026-10-23: new NFS-aware authority26/controller27 preparation PASS; applications remain unstarted.

Separate completion-v1 ba091012/protected64271929 FAIL index uniqueness check
after actual installed manifest validator PASS, before control/selection/apps.
Original193inputs contain4identical historical repeated pins; preserve their
exact order and require equality for every repeated path. Completion-v2 afce381c/
protected1b02b4c3 FAIL at candidate record's known empty-label attestation field;
only new result scope created, all original files intact. These failures remain.
New comparison explicitly admits only exact capture fields, byte count and the
known true label attestation; unknown fields/conflicting hashes refuse.

31local regressions PASS3.52s; held1361source146input preflight PASS57591bytes.
Actual completion-v3 30c1628d/163619bytes, protected95cbabf5/81296bytes PASS0;
3530744/start427941918 returns0/reaped/gone5.547205s. All11original partial files
and empty generations directory are adopted at exact original full9/hash/SIDs.
Installed static validator, controller load equality and scoped visudo PASS.
Control27 SHA790913da/39950bytes, manifestc67348b5/5019bytes, controllerd6ac6e16.
UUID84387eb1-9863-45be-83b0-92b6d1013ab6. New protected/public profile hashes
match new nfs_t receipt79f3db35. Original193input prefix including4identical
repeats is preserved; existing NFS policy pin rejoined without duplication.

Original rootless25 selector/deployment/policy preserved NOREPLACE in new
completion-v3 scope; current aliases absent until a NEW controller selection.
Only scoped sudoers26 installed, no services started or image/source restaged.
Actual final13role/4cgroup/5endpoint strict closure PASS.809FD+32reserve<1024,
limits unchanged. Source1361/readonly108package/originalpause/kernel unchanged.
Next fresh authority26 baseline/live paired rootless normal cohort; dedicated
isolation/fault/lifecycle still pending. Native23/gate17 unchanged.
Checkpoint153 `.scratch/web-006-source17-current-state-v153.json` SHA256cd67e4500d59a4f0c17f6e918d5cd35b5f193a6b48d80afa32badc8b7c955952.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint154 update2026-10-23: fresh authority26 stock983 empty baseline PASS; new live paired cohort prepared.

21baseline/guard tests PASS3.07s and lint PASS. Caller-v2 held1361source149inputs
preflight PASS15646bytes. Initial outer wrapper refused a mistyped SHA BEFORE
spawning any child or guest call; corrected exact pin used a separate execution
stem. Actual baseline2b33c7b6/106508bytes, protected COMPACTf304e156/19258bytes
PASS0;3531137/start427952526 returns0/reaped/gone1.467806s. Empty0/unknown0,
complete store full9/SIDs unchanged;13fixed roles quiescent, original70549pause
and unchanged native23 prerequisite/current authority26 held and rejoined.
No secret payload/hash, secret mutation, application start or retirement.

New observerb11bea1f/runner-templateec73aed2/coordinator96f1b9eb bind actual
control27/manifest26/receipt and baseline; exact guard3/single host NFS retained.
Original PUB23 functional wrapper remains unchanged with explicit NEW manifest.
Historical failed25 runner/watcher must be freshgone. Atomic live ARMED then
only2runtime pins; original child EOF/reap ownership and1850/2050/2100budgets
retained. Offline stale embedded-body assertions corrected before invocation;
34local binding/EOF/overflow/unknown-global regressions PASS5.29s, leaf lint PASS.
Caller1051f5f4 held1361source154inputs preflight PASS48299<120000; cohort is
PREPARED ONLY. Next invoke once; required normal ownership/live3CID/6ID, built
UI all3engines/shared Caddy and strict postrun remain unperformed, as do dedicated
isolation/fault/lifecycle checks. No previous failure/UNKNOWN promoted.
Checkpoint154 `.scratch/web-006-source17-current-state-v154.json` SHA2564e98cb2b19cc429ee94d472f41dcc77091635e72ebc69354007b233631f8060d.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint155 update2026-10-23: actual rootless26 normal cohort FAIL at missing local container bind sources, before browser cases.

Actual d51aacc7/122241bytes, protected29186321/38425bytes FAIL1;3531700/
start427970737 returns1/reaped/gone9.742520s. Live ARMED3300e70d matched new
authority/baseline; watcher115595/start28853795 and runner115596/start28853823
are reaped/gone. Original functional child115600/start28853850 returns1/reaped
7.374257s. Generation54d52dc79ca34ab98696eb554aa0fe3e is started/stopped,
containers/ready empty; all17original process pairs now gone. Original8inode
label gate passed; delivered gate/browser SUMMARY absent. Observer ownership
False/payload-read UNKNOWN preserved. Six NEW fixture secrets are retained;
historical empty baseline is NOT evidence of current emptiness.

Readonly diagnostic-v1 65f391fe/protected9824d1ba collected current generation/
manager/helper journals, but its original-failure path still selected failed25
and --user-unit as root omitted983journal entries. It is NOT failed26-child
closure evidence. Corrected literal-bound read-v2 90a0085a/152402bytes, protected
48857012/65546bytes PASS0;3532157/start427983776 reaped/gone1.319766s; binds
actual failed26 receipt and both correct original children freshgone. Exact
UID983/user-unit matches reveal worker115755/fadc568e/status125: missing
/run/hfcache/verification; Caddy115778/9ef8f21c/status125: missing
/var/lib/hfcache/caddy-config. Both MainPID/ControlPID0/cgroup empty. System
helper actually STARTED and STOPPED normally; no helper startup refusal here.
Strict13role closure remains unaccepted because two user units are failed.

Readonly bind metadata c77c96a2/172113bytes, protectedfa1cfd79/82117bytes PASS0;
3532631/start427998116 reaped/gone1.249645s. Both HOST and ORIGINAL pause70549
see identical paths/inodes: /run/hfcache/api, /run/hfcache/verification,
/run/hfcache/hfcache.lock and /var/lib/hfcache/caddy-data/caddy-config absent.
Existing api.lock inode17356 and verification.instance.lock52246781 are retained.
No file payload/hash, mount/secret/reset/start action. Next inspect/reconcile
failed26 secret metadata, scoped fixed missing-directory provisioning and original
lock history before creating any absent lock; ONLY known user failures reset,
fresh authority/baseline/cohort afterward. Do not replay failed26 or mutate
security policy to bypass it. Required dedicated checks remain pending.

Documentation alignment PASS207human/27helpers; git diff --check PASS. Current
selector condensed to navigation/current state; detailed checkpoint history remains
in this task, dated plan and progress, with prior selector bytes retained privately.
Checkpoint155 `.scratch/web-006-source17-current-state-v155.json` SHA256655beccfcc6506e639eeadfdcd16366f76d820a8485898a6f7995518292283f2.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint156 update2026-10-23: failed26 exact secret cleanup and missing fixed bind sources provisioned; strict fixture closure restored.

Readonly metadata40f74602/156066bytes, protected3e6a30e6/65727bytes PASS0;
3533070/start428012740 reaped/gone3.036645s. Six exact metadata IDs joined
original empty baseline/completed create sequence/17gone generation/passed
8inode gate/full unchanged store; no collector payload read/hash.
36local failed-cohort/identity/known-state regressions PASS1.83s, lint and held
1361source166input preflight PASS17625bytes. Actual cleanup432f1723/169513bytes,
protectedc10487e5/77052bytes PASS0;3533351/start428021253 reaped/gone4.489122s.
All6exact-ID removes return0; final empty0/unknown0;3historical audit containers
remain exited0/PID0/secret-free and unchanged. This supplies NO normal lifecycle
acceptance; observer False/payload UNKNOWN stays recorded.

13local exact-missing-set/unknown-input/real-exclusive-no-overwrite tests PASS
1.76s. Held1361source169input preflight PASS16725bytes. Bind preparation
3a39a660/244879bytes, protectedd9e03f39/145897bytes PASS0;3533855/start428039645
reaped/gone1.376418s. Original noncreating controller lock retained; scan finds
NO live/open/deleted /run/hfcache/hfcache.lock handle before new creation. ONLY
5proved-absent fixed paths created exclusively, empty, uidgid983: api20435,
verification20437 and hfcache.lock20436 under /run/hfcache; caddy-config4487064
and caddy-data4487065 under /var/lib/hfcache. Dirs0700/file0600; ordinary
var_run_t/var_lib_t label set while empty, no security/policy relaxation.
Host+originalpause see identical new inodes/SIDs. Existing api.lock17356 and
verification.instance.lock52246781 full9/SIDs preserved. No app/reset/secret
action, no existing leaf overwritten.

5exact receipt/cohort/reset-argv checks PASS1.65s; held1361source172inputs
preflight PASS15713bytes. Known-state prep5ba64c45/128918bytes, protecteda07ab2b7/
35818bytes PASS0;3534216/start428051464 reaped/gone3.487550s. ONLY exact user
fadc568e/9ef8f21c failed states reset-failed in one fixed command after all
17generation/two original child pairs freshgone, empty listing and repair proof.
Actual13role/4cgroup/5endpoint strict closure PASS. Source1361/guard3/kernel/
original70549pause/installed artifacts unchanged. No start/restart/replay.

Next fresh baseline/observer/runner/workspace-v2 and a new generation on SAME
validated authority26/control27. Reuse is deliberate: no installed source, UI,
protected descriptor/policy, kernel or control input changed; new repair/cleanup/
closure receipts are additional held admission prerequisites. Avoid redundant
controller/asset publication. A new generation/ARMED/workspace never replays the
failed original handles. Required rootless normal browser/lifecycle and dedicated
isolation/fault acceptance remain pending; WEB006 cannot be committed yet.
Checkpoint156 `.scratch/web-006-source17-current-state-v156.json` SHA2560c37476592aef44c77a4798c526923b7b0b07937c99147db6fca30df9e842939.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint157 update2026-10-23: repaired baseline PASS; fresh rootless27 normal cohort FAIL before browser on missing nested mount placeholders.

Fresh baseline-v2 2c1c08ec/120335bytes, COMPACTde34edf1/19917bytes PASS0;
3534673/start428067868 reaped/gone1.523837s. Current repair/cleanup/strict closure
receipts held;5new sources matched exact current full9/SIDs before engine start.
Empty0/unknown0/complete store unchanged. Same authority26/control27 reused
explicitly; fresh normal-v2 observer/runner/workspace and new generation.35local
coordinator/current-proof/EOF/guard tests PASS3.93s; lint and held1361source179
input preflight PASS48808bytes. Actual b47d9c9d/137374bytes, protected3a7611ba/
40426bytes FAIL1;3535032/start428079814 reaped/gone13.386461s. ARMED951d02cf
matched; watcher116415/start28962874 and runner116416/start28962900 reaped/gone.
Functional child116420/start28962932 returns1/reaped11.224781s. No SUMMARY or
browser cases. Generation40c64cd7a7e542e88cc998b3689c8581 stopped/containers/
ready empty; all17original process pairs gone.8original inode gate PASS; no
delivered gate. Observer False/payload UNKNOWN preserved;6new secrets retained.

Readonly diagnostics37b2ca79/protected04091ffc and exact-invocation journal
93f19958/171003bytes, protected54e9e90e/70809bytes PASS0. Latest3535654/
start428099897 reaped/gone1.307061s. Old generation54d52dc7/shaac4c27a5
preserved unchanged beside new176a8f06/14636bytes. System helper starts/stops
normally. Worker116574/invocation964a4b5a84d24c4ca7ff6d3aed1ee151/status126
refuses OCI mkdir /etc/hfcache/containers: permission denied under read-only
parent bind. Caddy116611/invocation63a6976a1a7249f6a8a2343d5cdb130b/status1
occurs during immediate stop after worker failure; no separate Caddy cause
established. Both PID0/cgroups empty; strict13role closure NOT accepted.

Metadata proves /etc/hfcache/containers AND /etc/hfcache/client.toml absent.
Standing containers contract requires root-owned real placeholders; fixture
provisioning omitted them. Existing credentials directory inode118329700/0750/
root:983/secret_t is preserved; no permission widening is selected. Next only
exclusive empty root-owned placeholders, after exact failed27 secret cleanup.
No image/source/profile/security change or new publication is needed. Existing
5new runtime/state inodes and original locks remain; future current metadata
must account for legitimate engine :z labels/ctime rather than reuse prestart
full9 after an actual attempt.

Readonly secret metadata6415d2a3/168219bytes, protected03097f39/65899bytes PASS0;
3535885/start428106984 reaped/gone3.239455s.6exact IDs/unknown0/complete store
unchanged/original payload inode gate match.36local failed27 cleanup witness/
identity/known-state checks PASS1.81s, lint and held1361source189input preflight
PASS17638bytes. Cleanup9fc15d05/caller448e2391 is PREPARED, NOT invoked.
Next invoke once; reset only exact two known closed failed unit states afterward.
Docs alignment207human/27helpers and git diff --check PASS; source1361/gate17/
native23 unchanged. Required normal/dedicated acceptance remains incomplete.
Checkpoint157 `.scratch/web-006-source17-current-state-v157.json` SHA2561fbc189006f548046555cbcfd44f6c8ad7b2ca58cbceb43da205d9735c066ad7.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint158 update2026-10-23: exact retained created-container and six-secret failed27 cleanup PASS; no app restart or acceptance.

Initial secret cleanup-v1 bf497e29/130178bytes, protected81f165c2/28608bytes
FAIL before removals: account inventory correctly finds2new retained containers
in addition to3historical audits.3536268/start428120734 reaped/gone1.618312s;
removals[]/no secret change. Original failure stays retained. Readonly container
metadata-v1 a941bc6b/protectedb5cbd0d7 FAIL bounded Go-template inspection before
any result/container action;3536718/start428134439 reaped/gone1.347474s.
Separate default-inspection metadata projection-v2 1b337446/160848bytes,
protected2b787a54/55803bytes PASS0;3536910/start428140982 reaped/gone2.277219s.
Only whitelisted metadata is published; raw diagnostic stays root/private.

Worker6d34f753fe226ec95905f312350ae8e60640fcc3078ac00b676d21cfd6a18192 and
Caddy6420cd4cde7c85273f5b52dd3a6552c05e9d84ef540c767a0a351fa09dd3dc23
are CREATED/never started, PID0/RunningFalse/zero StartedAt/FinishedAt, no matching
cgroups in408scanned entries. Original17generation/runner/watcher remain gone.
Actual creation times, protected deployment image identities, rootless role labels,
fixed command/worker invocation and Caddy's2exact current secret IDs match this
failed cohort; worker has no secrets. No live3CID proof is inferred.

16local forged-identity/live-state/creation-window/secret/cgroup/no-force tests
PASS1.68s; held1361source196inputs preflight PASS18058bytes. Actual exact-ID
container retirementa9131457/166630bytes, protectedd4c76220/59695bytes PASS0;
3537507/start428163615 reaped/gone3.371165s. Both original nonforced per-CID
removes return0/reap, exact exists returns1. Original metadata retained;3old
audit CID/name/complete stopped-state/no-secret checks passed before effects
and remaining3IDs/names preserved. No secret/service/policy action.

36local failed-secret tests PASS1.72s, lint and held1361source199inputs preflight
PASS17925bytes. Separate cleanup-v2 2a6b8d04/187904bytes, protectedf827b20c/
78149bytes PASS0;3537726/start428169624 reaped/gone4.501268s. Holds original
pre-removal refusal and exact created-container retirement; original secret
store/IDs still match metadata witness. All6per-ID removals return0, final
empty0/unknown0. No force/all/ignore/name-only deletion or normal lifecycle
acceptance; original observer False/payload UNKNOWN remains.

Next provision ONLY absent /etc/hfcache/containers root0755 and empty client.toml
root0644 real mount placeholders; preserve existing credential directory/modes
and original lock identities. Then ONLY exact worker964a4b5a/status126 and
Caddy63a6976a/status1 failed states reset, fresh metadata/baseline/cohort.
Installed bytes/control27/source1361/gate17/native23 unchanged. Strict13role
closure remains NOT accepted until separate known-state prep; no app replay.
Checkpoint158 `.scratch/web-006-source17-current-state-v158.json` SHA256905e55d9970c5486facf153c3a5b8993193ee8c33aa5de8ee80af4335ce8f43e.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint159 update2026-10-23: ONLY two missing empty root-owned placeholders provisioned; exact failed user-state prep restores strict fixture closure.

13local plan/closed grammar/real-exclusive-no-overwrite checks PASS5.88s after
unit input normalization from metadata-only absence to traversal-record format.
Inert compile/warnings/one-entrypoint/unknown-global audit PASS. Held1361source
202inputs preflight PASS16761bytes. Actual placeholder prepa8783fda/286894bytes,
protected05669f45/169120bytes PASS0;3538455/start428198362 reaped/gone1.361200s.
Exactly two exclusive effects: empty client.toml inode78602581/root:root0644 and
empty containers directory101851392/root:root0755, ordinary inherited etc_t SID.
Host and ORIGINAL pause see identical new inodes. All18fixed source metadata
remeasured; existing3locks and credential directory full9/SIDs unchanged. No
existing leaf overwritten, credential permission broadened, service/reset/secret
or kernel action. Runtime :z metadata from actual prior attempt is measured as
current; earlier full9 remains historical.

5actual pin/cohort/exact-argv checks PASS1.69s; held1361source205input preflight
PASS16003bytes. Actual known-state prepfa4284a5/146288bytes, protected181e7dc9/
35937bytes PASS0;3538875/start428213082 reaped/gone3.328279s. Holds original
failed27 generation/journal/17gone children, exact6ID cleanup and current2target
provisioning. ONLY exact user964a4b5a/worker126 and63a6976a/Caddy1 failed states
reset-failed in one fixed command. No start/restart/replay. Actual13fixed roles
inactive/PID0,4cgroups empty,5endpoints refused PASS. Additional rootless Caddy
127.0.0.1:8443 also actually refuses ECONNREFUSED111. Source1361 unchanged.

Next fresh baseline normal-v3 binds current18path metadata plus exact new
cleanup/placeholder/closure receipts; same authority26/control27/source17 and
installed image/package retained. New observer/runner/workspace-v3 and new
generation, no old handles replay. Required rootless normal browser/lifecycle
and dedicated isolation/fault checks remain pending. Native23/gate17 unchanged.
Checkpoint159 `.scratch/web-006-source17-current-state-v159.json` SHA256b8b387f111f794317aeb38e17064db6f0ef100cfe7d3d9f499577b8a6dc74e20.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint160 update2026-10-23: fresh current18path baseline normal-v3 PASS; new rootless28 paired cohort prepared.

Baseline rootd02a4196 retains native23 and authority26/control27 prerequisites,
adds exact current cleanup/placeholder/closure pins and remeasures all18path
full9/SIDs after prior legitimate engine :z effects. Lint and held1361source
207input preflight PASS16459bytes. Actuald46d35b0/137568bytes, protectedCOMPACT
b0f1d98c/19915bytes PASS0;3539200/start428223521 reaped/gone1.579389s. Actual
empty0/unknown0/complete store unchanged, roles quiet, all held current repair
records/native prerequisites rejoined/closed. No app/secret action or acceptance.

New observerd3319844/runner-template6a00eefd/coordinator92a216e7 binds new
baseline, current3repair records and original failed27 handles freshgone. Same
authority26/control27/manifestc67348b5 and unchanged installed artifacts reused;
normal-v3 WORK/ARMED/workspace and future generation are new. Original PUB23
functional wrapper remains with explicit current manifest; original observer
atomic ARMED and2runtime bindings/EOF/reap ownership remain.35local exact
receipt/body pin/unknown-global/EOF/overflow/guard regressions PASS3.98s, leaf
lint PASS. Callerc3aaa8be held1361source212inputs preflight PASS48835bytes,
2100s original SSH EOF budget retained. PREPARED ONLY, not yet invoked.
Next invoke exactly once; built UI through shared Caddy/all3engines,6ID/3liveCID
normal ownership, strict postrun and dedicated isolation/fault/lifecycle remain
pending. No old failed generation/observer/operation replay.
Checkpoint160 `.scratch/web-006-source17-current-state-v160.json` SHA25648eeaabb29f8098fc09c510c8920dcfef2658bb7e8ddf23ff4e5ea60c72dc813.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint161 update2026-10-24: worker actually starts/notifies ready; fresh rootless28 cohort FAIL at API protected credential source. Exact namespace metadata verifies fixture ownership error without payload read.

Actual rootless28 2662f2c6/154606bytes, protected3a59aa67/40424bytes FAIL1;
3539614/start428237250 reaped/gone24.594826s. Original watcher117566/
start29120302 and runner117567/start29120327 reaped/gone. No SUMMARY/browser
cases. New generation627c7a836d2f4d399c830ae9e530ebf0 stopped/containers/ready
empty; all20original process pairs now gone.8original inode gate PASS; no
delivered gate. Observer False/payload UNKNOWN preserved;6NEW secrets retained.

Readonly diagnostic25c047d3/195268bytes, protectedaae4638c/78421bytes PASS0;
3539932/start428247858 reaped/gone1.335145s. Both earlier generation records
remain exact. Actual worker98448c116cd749978305f063ec5c470f starts/notifies READY
and stops normally. API117783/invocation89549069449940bb8eb195d8aa8f53fd/status10
prints HFAPI003. Caddy117784/invocation7345d69ffe324acea168fb0d5a4d8a9b/status2
occurs during early cleanup. Pasta emits no-nameserver warning; independent
Caddy cause remains unproved. Both current failed units PID0/cgroups empty;
strict13role closure NOT accepted. Fixed real placeholders now exist.

Current docs explicitly require rootless Basic record0400/0600 owned by the
actual service identity mapped to API981 (web-ui/deployment.md97). Fixture
controller instead writes host-root0640. New actual unchanged-image/keep-id
metadata probe uses no network/secrets, capless/NNP/read-only /etc/hfcache bind,
O_PATH plus readable-open metadata and the ORIGINAL installed credential reader.
Its os.read guard forbids payload reads; original reader raises HFAPI003 before
any payload call. Actual3b8038dd/155593bytes, protectedb3583462/38823bytes PASS0;
3541264/start428301751 reaped/gone3.198363s. Inside EUID/GID981/groups[981],
SAME inode118606297/221bytes/0640 has UID65534/GID981.0payload reads. Passed
probe CID35127297145ffa96149e5f1f05ac005d11ef735d7a9a0d5b28fa857ffed17bac
exits0/PID0/no secrets; original metadata retained and exact nonforced retirement
passes. No actual application role restarted, credential file read/changed,
policy/SELinux change or product guard bypass. All failed28 resources remain.

Next private fixture controller writes ONLY rootless Basic record as actual
mapped hostUID983/0400 per existing contract; native remains root0640. Its
original label/active-kernel helper-denial gate stays. Source review also finds
Type=exec API/Caddy are inspected immediately; bounded read-only cohort polling
will precede delivered-secret gate without any service-start replay. These are
fixture corrections, not a relaxed product credential guard/new runtime source.
Before new authority, reconcile failed28 current container/secret metadata and
perform only positively owned exact-ID cleanup/known-state prep. Required normal
and dedicated acceptance remains pending; source1361/gate17/native23 unchanged.
Docs alignment207human/27helpers and git diff --check PASS.
Checkpoint161 `.scratch/web-006-source17-current-state-v161.json` SHA256dc083a10fc791f3a84b09f4bd1d8c4f4db93c3270215772c5909ffba581b165f.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

WEB-006 checkpoint162 update2026-10-24: failed28 exact6ID cleanup and known-state prep PASS; corrected private controller28 remains inert/unpublished.

Readonly metadataa58d570d/187042bytes, protectedd485c90e/66887bytes PASS0;
3541968/start428329571 reaped/gone2.863852s. Actual6IDs/unknown0/complete store
unchanged/original payload inode gate match. Account inventory has ONLY3known
historical audits; application containers from failed28 are already absent.
36local failed28 identity/time-window/known API10+Caddy2 tests PASS1.74s, lint
and held1361source225inputs preflight PASS17653bytes. Actual cleanupab4084c4/
200921bytes, protecteda455e570/77668bytes PASS0;3542895/start428365669 reaped/
gone4.508848s. All6exact per-ID removals0, final empty0/unknown0; original3
stopped/secret-free audits preserved. No normal6ID/3liveCID acceptance supplied.
Observer False/payload UNKNOWN remains, all20original generation pairs gone.

5pin/cohort/exact-argv tests PASS1.69s; held1361source228input preflight
PASS16118bytes. Actual known-state prepc68521bf/159388bytes, protecteda58f046e/
36999bytes PASS0;3543549/start428392308 reaped/gone3.289065s. Holds failed28
generation/diagnostic/cleanup, actual passed owner-map probe and standing
placeholder receipt. ONLY exact API89549069/status10 and Caddy7345d69f/status2
user failed states reset-failed. No start/restart/policy/credential action.
Actual13role/4cgroup/5endpoint strict closure PASS; rootless8443 also refused111.
Original70549pause/NFS guard3/source1361 unchanged.

Private controller28 prototype6c276cb7 prepares mapped rootless Basic file
UID983/0400 per existing guide; native remains UID0/0640. Original secret label/
active-kernel helper-denial gate uses corresponding Basic owner; other7original
source checks remain. Added bounded90second read-only initial rootless cohort
polling for existing Type=exec starts; failed units refuse, first timeout error
is retained, no service start/restart replay.5local metadata/native-preservation/
read-poll/failed-unit/budget/method-delta tests PASS1.84s, lint PASS. AST confirms
ONLY credentials, secret_label_gate and start methods change, plus one new read
wait and pure metadata helper; source/API/product guard/image/policy unchanged.
Prototype is INERT, not published/installed/accepted. First formatting-dependent
local edit refused before writing; AST-selected prototype and tests pass.

Next authority27/control28/generations28, preserving209old immutable inputs and
current rootless aliases; only new private controller/marker/launchers/manifest/
scoped sudoers, reuse existing public profile records and installed bytes.
Hold actual owner-probe/cleanup/closure/placeholder proof, then fresh baseline/
live paired normal cohort. No old failed app/proof replay or required test skip.
Normal rootless and dedicated isolation/fault/lifecycle acceptance still pending.
Checkpoint162 `.scratch/web-006-source17-current-state-v162.json` SHA2565dede164aa6c028a9da1b622b7e405aeb77aac535388ba449687a84efa1bbf99.
WEB006/AUTH08/HOST01–03 incomplete; production/NAS/installed predecessor interface untouched.

Checkpoint172 (2026-10-24): SOURCE19 remains frozen at1361files/snapshot586acd13;
no canonical edit after green gate19. Canonical artifact06496e45 and explicit
fixture0.2.6 artifact4867a0a7 actually build PASS16.57s/17.19s, each with two
byte-identical UI builds. Fixture wheel0dd17b83/500326B, manifest0144a394;
measured fixture Python reports0.2.6/all108package leaves match frozen19.
Canonical product version remains0.2.2. Shared API/UI image build actually PASS
27.70s, image dedf864e4c3e0892f1af1f7509d1041f39c4a042a925b96c9f8ec9f545792744,
receipt a254127e. Both FROM stages remain pinned UBI10micro87a27d71. No separate
frontend image/server or runtime Node introduced; runtime absence/installed
image audit remains pending. Actual OCI export ebbdbea7 PASS5.32s, original
base/Caddy archives reused exactly; original bounded OCI transfer is running,
not yet accepted. No guest image load/application start inferred from export.

Actual quiescent staging readiness9efcc49e/protected64f221ea PASS6.02s preserves
all3original selectors and mapped Basic inode118570589 with metadata-only
RENAME_NOREPLACE; no secret/master-key body/hash read. Actual control29 has224
immutable input rows. Strict13role/4cgroup/5endpoint closure and empty secret
store hold.9local actual rename/collision/metadata checks PASS1.82s.
Native preparation1 ce6074a0/79d2a881 FAIL before installer on the pinned old
17,725,440B source archive exceeding8MiB; preparation2 1efc17be/8d019f87 FAIL
before installer on restorecon-nRFv7058B. Both partial scopes/receipts retained.
Readonly label diagnosis383eda0c/642bfad0 PASS1.37s proves52differences limited
to old stopped0.2.5 release SELinux user unconfined_u->system_u, identical
object_r/usr_t/s0; target0.2.6 absent, captured source19 retained.

Native attempt3 original unchanged install-release.sh --no-switch --with-mcp
ACTUALLY returns0 in16.63s, PID121406/start30006482. Collector223b8b74/a596faac
then FAILS its process-record shape check before post-install verification;
that receipt remains failed. Installer is NOT replayed. Separate read-only
completion0a0693e1/protected05700295 PASS5.38s verifies original child gone,
installed0.2.6/all108package leaves match frozen19, all224old inputs and old
readonly108package full9/hash/SIDs preserved, captured1361/private and public
source unchanged. Exact52standard SELinux user normalizations preserve43regular
file hashes and all bytes/UID/GID/mode/inode/mtime/nlink; only allowed SID-user/
ctime change. No further label correction remains; kernel45bb34e8/Enforcing
and owned NFS identities unchanged. Native UI/server candidate, image runtime,
new native/rootless browser and dedicated isolation/fault/lifecycle acceptance
remain pending. All application roles stopped; original selectors/Basic absent
and preserved, stock rootless secret store empty.10new preparation guard tests
PASS1.88s;7OCI destination/network-mount fault tests PASS1.73s. These tooling
checks do not replace installed functional acceptance. WEB006 in progress/
uncommitted; AUTH-08/HOST-01–03 pending, WEB007–026 not started. Production
unchanged. Checkpoint172 ignored state records exact current artifact identities.

Checkpoint173 (2026-10-24): actual OCI transfer4f374b0c PASS3.35s/all4home
files full9/hash/SID rejoined; all original copy children reaped/gone. Fresh
SOURCE19 UI packet837769b1/1,269,760B has8fixed members, bound codecbafa3ddc;
9actual duplicate/foreign-header/corruption/version guard tests PASS1.75s.
Native UI staging8f363c78/protectedf943f8b7 publishes6exact UI files plus
native server candidatebd9f1415 (ONLY web.asset_root/manifest_sha256 changed)
then FAILS the readonly asset inspector: original installed source_path raises
HFAPI003 because the inspector omitted CREDENTIALS_DIRECTORY. Original receipt
remains failed; no UI/config/installer restaging, application or Caddy start.
Separate readonly completiona32df7a2/protected8052120b PASS3.34s with exact native
credential-directory SPELLING only, no credential contents loaded. Actual
installed0.2.6 capture validates manifest0144a394,5members/1configured prefix
shell and wire891b5b45. All6UI and108package full9/hash/SIDs stay exact; candidate
is not installed/selected. Strict closure, empty secrets, preserved aliases and
master-key metadata hold.

Original stock UID983 image load PID121892/start30123477 actually returns0 in
3.83s. The surrounding collector7c874a2f/protected640bbf9b FAILS on667B nonempty
stderr before image inspection; failed receipt remains. Separate readonly
completion6e161f2f/protected040c7b70 PASS2.84s proves all9stderr lines are known
image-copy progress prefixes, original load PID gone, exact appdedf864e/Caddy
fa2a5634/base34f13727 and genuine pinned micro layer prefix, archive4full9/
hashes/SIDs,3old stopped audit containers, empty secret store, exact original
NFS/kernel/Enforcing and13role4cgroup5endpoint closure. The image load is NOT
replayed; Caddy/base not reloaded, no container/service started. Keep both
observed image sizes: build-host204760968B, guest204761022B. Runtime tool/module
absence and actual package/UI/UID mapping audit remain pending, as do new
native/rootless shared-Caddy browser and dedicated isolation/fault/lifecycle
acceptance. No partial proof closes AUTH-08/HOST-01–03; WEB006 remains in
progress/uncommitted, WEB007–026 pending. All guest lanes idle/closed here;
production unchanged. Checkpoint173 ignored state owns exact current identities.

Checkpoint174 (2026-10-24): NEW source19 image runtime audit original attached
process122213/start30175964 exits0, actual container outer122237/start30175989
runsPID1/inner981 mappinghost983, all108package+6UI hashes match,35named tools
and8modules absent (including Node/npm/pnpm, compilers, rpm/dnf and pip/uv).
Actual E/P/I/A/Bnd capabilities0, NNP1/seccomp2, immutable root/network-none,
only owned readonly gate/private tmpfs and no credential mounts. Original probe
f3f99a7d/12188B retained. Original collectorc7555247/protected12502aa6 FAILS when
Podman normalizes ONLY Mounts[0].Mode Z->empty at start; all substantive mount
fields/RO/source/options/propagation identical. Do not promote that receipt.
Separate completiondc3f88f1/protectedf18770c9 actually PASS3.37s, verifies raw
original probe/attach0, all108/6/35/8 and real UID/capability evidence, exact
Mode-only normalization, original attach/outer gone and cgroup closed. It then
retires ONLY original positively stopped/exit0/noSecrets audit CIDec8cc5bf with
nonforced exact-ID rm, proves absence1, original3stopped audit CIDs unchanged,
secretstoreempty, selectors/Basic absent/preserved, kernel45bb34e8/Enforcing,
owned NFS and strict13role4cgroup5endpoint closure. No audit, image load or
native installer is replayed. Actual shared API/UI image dedf864e now has
fresh runtime ancestry/absence proof on pinned UBI10micro; browser Debian/Node
tooling remains unshipped and separate. This is not installed helper/API/worker
role, new native/rootless shared-Caddy browser or dedicated isolation/fault/
secret-lifecycle acceptance; those remain mandatory and pending. WEB006 stays
in_progress/uncommitted; AUTH-08/HOST-01–03 pending and WEB007–026 not started.
All guest calls closed, app lane quiescent; production untouched. Next source19
browser/readonly package environment, rootless007 and authority29/controller30.

Checkpoint175 (2026-10-24): actual SOURCE19 environment6ab3f878/protected4767d314
PASS9.55s. Fresh descriptor-anchored bind/remount exposes the installed native006
package at new source19 provisioning path, statvfs/mountinfo readonly and same
108inodes/full9/hashes/SIDs; original source is root-owned and unchanged. Actual
UID1000 import resolves exactly that target and reports0.2.6 (PID122429/start
30241508 exited). Explicit0.2.6 wheel0dd17b83 copied/hash-verified.194public browser
files/50directories freshly staged/prelabelled/rejoined from unchanged original
browser tooling plus7captured source19 drivers and new fixture inventory. All
1361frozen source19 tracked leaves unchanged; only intended .scratch direct-entry
root transition. All old sources preserved, helper-key metadata only, exactNFS/
kernel/Enforcing, empty secret store, selector/Basic absence and strict13/4/5
closure. All original executor handles reaped/gone. No browser, API/helper/worker
or Caddy service started; this is environment staging only, not new normal or
dedicated functional acceptance. Next rootless007 original stage/render with
auditeddedf864e, then authority29/controller30, retaining224old rows. WEB006
in_progress/uncommitted and AUTH-08/HOST-01–03 pending; WEB007–026 pending.
Production remains unchanged. Checkpoint175 ignored state owns current identities.

Checkpoint176 (2026-10-24): actual rootless007 original stage/render03366bda/
protectedb507acaf PASS5.61s. New /opt/hfcache/releases/0.2.7 has28captured input
files, complete6helper copies/explicit host-helper opt-in, exact supported Basic/
web tables and test TLS default-SNI overlay. Original stage() and _verify_stage()
execute unchanged; index3879aa56/runtimeb3563b3a/server759807c5 bind host983,
audited shared API/UIdedf864e, unchanged Caddyfa2a5634 and UI0144a394/software006.
Actual full image-build receipt remains locally bound by FD/hasha254127e; a
precisely checked1215B selected-field document is published in guest with that
explicit provenance, not labelled as the full receipt. Native108readonly package
FDs,1361public source bytes/full9, selector/Basic absence, empty secrets, kernel/
Enforcing/NFS and strict13/4/5 closure preserved. No image load/audit/native
installer replay, application/Caddy start or policy/credential grant. Independent
new profile bindings and authority29/controller30 remain required before actual
application/browser tests. All calls closed. WEB006 in_progress/uncommitted;
AUTH-08/HOST-01–03 pending, WEB007–026 pending; production untouched.

Checkpoint177 (2026-10-24): original protected index preparer actually PASS
44c9920c/protected072904f1 in3.16s against new native006/rootless007 files.
Native indexf1774770 (222actual authority files)/policy8fd0496b; rootless index
bf09c14d (43files)/policyed6fa6f4. Index source snapshot9daf2d5a truthfully names
the actual two-field006fixture build, with genuine parent07d10e0/dirtytrue;
canonical gate19 snapshot586acd13 remains separately recorded. SELinux receipt
79f3db35/kernel45bb34e8 unchanged, no module/type/permission grant. Both policy
documents preserve EXACT old6bits: configurationtrue, all otherfalse. Each
exclusive own temporary selector is fully verified over original preparation
and preserved via exact inode/target/SID RENAME_NOREPLACE; both selectors kept
as evidence, current absent again. No global deployment/policy/credential
installation, application start or key/secret payload/hash read. Native readonly
108package retained, strict13/4/5 closure and empty secret store PASS. All actual
child handles closed; production unchanged. Next authority29/controller30
publication/manifest using actualsource19environment/profiles while preserving
224old control rows, then new installed native/rootless/shared-Caddy and
dedicated isolation/fault/lifecycle acceptance. WEB006 in_progress/uncommitted;
AUTH-08/HOST-01–03 and WEB007–026 still pending. Checkpoint177 records exact pins.

Checkpoint178 (2026-10-24): actual separate readonly source19 authority29
completion PASS cb644dc5/protectede37b3297 in3.70s.
Original preparation OSError and subsequent 8MiB tool-size refusal remain failed;
separate streaming two-FD anchors retain full9/hash/SID checks without changing
RLIMIT. Publication then actually succeeds, but its final ancestor guard refuses
the intentional own .scratch0755->0700 narrowing; that original receipt stays
failed. No publication replay: readonly completion rechecks the exact recorded
mode/ctime-only transition,108native package/194browser files/50directories,
all21published files, master-key metadata only, actual installed validator and
visudo. Control30 4a6068e0 has240rows with all224old rows preserved in order;
manifest2e5f9473, wrappera9a552e2, controllerdde9de38 and launcher672262b4 remain
exact. Actual834FDs/1024soft/32reserve, no limit change. Current/global bindings/
Basic absent, secrets empty, strict13role4cgroup5endpoint closure/kernel/NFS/
Enforcing preserved. All original executors closed; no application/Caddy/browser
start or new normal/dedicated acceptance. Next fresh native24/rootless31 through
real shared Caddy, then required dedicated isolation/fault/secret-lifecycle tests.
WEB006 in_progress/uncommitted; AUTH-08/HOST-01–03 and WEB007–026 pending.
Production untouched; no historical frontend retirement. Ignored checkpoint178 owns full pins.

Checkpoint179 (2026-10-24): actual native24 original checker122866/start30584912
returns1 after168.49s; wrapper3596590 closed170.69s. Original failed protected
receipt3d24dac1 and generation3e3ebc4e10464f3ab7eb87e3693fa60d retained unchanged,
no SUMMARY/no acceptance. Baseline and helper-down actual3engines PASS24host
assertions, same-Caddy trusted/untrusted pairs retain their own proofs; original
helper restart preserves API/worker/Caddy before the next browser phase. In
restarted untrusted phase Chromium/Firefox prove certificate refusal, but WebKit
returns ambiguous navigation cancellation rather than a certificate signature.
The strict validator correctly refuses it; no cancellation is accepted as TLS
proof. All3browser engines/that CID drain, original generation stopped/pausedfalse,
all recorded application PID/start pairs gone,13role4cgroup5endpoint closure and
empty secretstore PASS. Readonly diagnoses preserve raw report and metadata;
Basic remains root:983/0640 inode118619972/secret_t, payload/hash unread. No replay,
production changes or case completion. Next strengthen explicit blank-page
readiness and single-navigation transport evidence, preserving certificate-
specific requirement/no response/no auth/no retry, then fresh source gate/fixture.
Native24 failure remains historical; new native/rootless and dedicated/lifecycle
acceptance are still mandatory. WEB006 in_progress/uncommitted; WEB007–026 pending.

Checkpoint180 (2026-10-24): narrowed native24 failure to real WebKit untrusted
navigation cancellation after baseline/helper-down pass; no ambiguity accepted.
Source20 changes ONLY functional driver, its guard tests and human troubleshooting.
It settles the initial blank frame before one HTTPS navigation, records the exact
failed main navigation transport, and requires an actual certificate signature
with no HTTP response. Navigation and transport diagnostics stay distinct and
sanitized; no retry, TLS bypass or generic cancellation category.10focused driver
metadata tests, full web lint/format, docs207/27 and diffcheck PASS. No new runtime
dependency, permission or architectural grant; original certificate-specific
contract retained. Frozen1361source20 snapshot3c50c138/capture55a41976, only these
3changes from19; all108runtime package source and UI build inputs unchanged.
Explicit two-field006fixture projection11a82a1a/snapshot5c3c8e44 PASS, canonical
version002 unchanged. Actual strict gate20 started outer3598949/start429776482,
runnerc847585e, original retained command historical gate invocation (original command SHA-256 `6a22211ef273d05d08c501759e7aa72d87f00c2f820395dfa51c01e1364b67fd`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`); still RUNNING/no outcome inferred. No source changes after20
freeze. Gate19 remains historical PASS. No source20 guest transfer or application
acceptance yet; source19 native24 FAIL remains unchanged. Next actual gate20
closure, new source20 disposable source/browser bindings, native25/rootless31
shared-Caddy and dedicated isolation/fault/secret-lifecycle acceptance. Basic
native root:983/0640 must be preserved metadata-only before rootless owner change.
WEB006 in_progress/uncommitted, AUTH-08/HOST-01–03/WEB007–026 pending; production
untouched. Full ignored checkpoint180 owns current receipts and execution handles.

Actual new guest transfer 26f57ab1/protected122f7832 PASS19.77s:
all1361new source20 files/hash/full9/SIDs verified, oldsource17 and oldsource19
all1361each preserved. Original failed native24 receipt/generation and all its
closed PID/start handles rejoined; current native006/Basic metadata only untouched.
Actual readiness 8eeabc18/089ef727 PASS4.33s: original
Basic inode118619972 root:983/0640 and3native aliases preserved NOREPLACE, stable
identity/bytes-size/SID except rename ctime. Payload/hash unread, no owner guard
bypass, absent current/deployment/policy/Basic and empty secrets/strict closure.
Actual environment 9bae0908/protected65c81843 PASS8.31s:
fresh readonly same-inode native006 package108leaves and UID1000 import;194browser
files/50directories including current source20 drivers, private0700scratch from
creation. Runtime comparison3d5097bd is actually checked against new1361source,
108package/46UI consumed inputs and installed UI0144a394, while preserving genuine
source19 build9daf2d5a/profile/artifact provenance. No reinstall/image rebuild or
service/Caddy start.776FDs/1024soft/32reserve, no limit change; source1361/keymeta/
kernel/NFS/Enforcing/originalpreservedBasic/strict13role4cgroup5endpoint closure
and empty secrets PASS. All original calls closed; production untouched.

Next bind new launcher from actual environment metadata and publish authority30/
controller31 preserving all240old control rows and exact old source19-built profile
bytes. Then fresh native25/rootless31 through real shared Caddy and dedicated
isolation/fault/secret-lifecycle acceptance. Native24 remains FAIL/no SUMMARY;
AUTH-08/HOST-01–03 pending, WEB006 in_progress/uncommitted and WEB007–026 pending.
Checkpoint182 owns full pins; no historical frontend retirement or production rollout accepted.

Checkpoint183 (2026-10-24): actual source20 authority30 publication PASS
69ff8293 in4.03s, original3619589/start429963632 reaped/gone. Controller31f8e9fbfc,
launcher1a671909, manifestcdc9a068 and wrapperc84c1c8f pass actual installed static
validation/visudo/controller load.247control inputs preserve all240prior rows in
order; unchanged genuine source19 build9daf2d5a/profiles retained separately from
source20 test fixture5c3c8e44.810FDs/1024soft/32reserve, no limit change. New scratch
0700 already set before holding child inputs; no ancestor mode mutation or late
rejoin exception. Key metadata only, preserved originals/emptysecrets/strict
13role4cgroup5endpoint closure/kernel/NFS/Enforcing preserved. No application
acceptance inferred from publication.

Fresh native25 original functional checker now RUNNING through source20 wrapper,
caller3e182f2f/root401f1318, original outer3620035/start429981414, session97406.
No result inferred; no parallel guest call while it owns the lane. It uses new
source20 TLS driver and source20 readonly package/browser inputs, original same
Caddy/native006 artifacts with correct build provenance. Original native24 FAIL
and all its handles/receipts remain untouched. Next close this original executor,
then actual postrun/normal-readiness and metadata-only preservation of its new
Basic inode before rootless31. Rootless and dedicated isolation/fault/secret-
lifecycle acceptance remains mandatory and pending. WEB006 in_progress/uncommitted;
AUTH-08/HOST-01–03 and WEB007–026 pending. Production unchanged.

Checkpoint184 (2026-10-24): source20 native25 actually PASS local0a22f1e8/
protected78d91d68; checker126591/start30864451 returns0 in325.75s, original outer
3620035 reaped/gone328.56s. Fresh SUMMARYa0b39391/generation9b05fac47df94fc896ead1e8ace427b1
contains4modes/3engines/33host assertions,0required retries/skips, actual normal
stop/cleanup_unknownfalse. Separate readonly postrun68187fbc PASS1.91s rechecks
all4same-Caddy trusted/untrusted pairs/12certificate-specific refusals, exact
single navigation/noHTTPresponse, all browser CIDs/init handles gone, original
application generation handles gone,8original/2delivered secret-label gates,
normal hygiene and same-instance API/worker/Caddy across helper loss/restart/
timeout. Normal-readiness codef9be35ef/18567B is bound from actual7records and
passes all held full9/hash/SID checks. No rootless or dedicated acceptance inferred.

Native25 original Basic inode118634654 root:983/0640/secret_t and3current bindings
actually NOREPLACE preserved09f60fc9; payload/digest unread, no owner override.
Fresh actual rootless baseline279799d2 PASS1.54s: metadata-only complete safe store,
zero IDs/unknown names, original pause70549 and normal native/authority30 proofs
rejoined. Rootless31 fresh paired watcher/original runner now RUNNING via original
coordinator3653559/start431059534/session25994; no outcome inferred/no parallel
guest call. Watcher9c9e2c5b,runnerb05afdf5,coordinator387722ce; actual source20/
authority30/control31 and genuine unchanged006/007runtime profiles retained.
All preparation compile/schema/binding/global audits pass before effects. Next
close original coordinator/children, reconcile real normal/TLS/live six-ID/three-
CID ownership/delivery/drain, opaque prelabelled backup and exact-ID retirement.
Dedicated native/rootless isolation/fault/secret-lifecycle proof still required.
WEB006 in_progress/uncommitted; AUTH-08/HOST-01–03 and WEB007–026 pending.
Production untouched; native24 failed run remains unchanged, no replay/promotion.

Checkpoint185 (2026-10-24): rootless31 actually FAIL de897ddd after75.04s;
original checker132293/start31942550 returns1/72.89s. API/worker/Caddy readiness,
8original/5delivered secret-label gates, real6ID/3liveCID ownership and3browser
untrusted-TLS refusal PASS as partial proofs. Baseline host status is unavailable
in all3trusted engines, no cases/SUMMARY accepted. Original generation2ad128d4
remains startedtrue/stoppedfalse; never promote/replay it. Readonly00bf4ff5 and
metadataebf25e38 prove all62original app PID/start pairs and coordinator/watcher/
runner gone,13role4cgroup5endpoint closure, only3old stopped audit CIDs with no
secret references. Separate exact-ID retirement24120791 PASS4.57s uses genuine
live ownership, complete opaque whole-store backup labelled secret_t BEFORE
bytes,6exact removals and final empty store. No blanket/name-only deletion,
production action or original generation rewrite. AVC query finds no owned AVC;
absence of an AVC is not permission proof.

Actual same UBI10micro image metadata probe under real container_t PASS4.13s:
original helper parent inode10829/runtime_t projects65534:981/0750. Readable
O_RDONLY directory open and original EndpointBinding._open_parent both fail
EACCES13, while O_PATH succeeds on EXACT same inode. No payload/binding read or
helper request; all metadata unchanged. Original passed diagnostic CIDe9ff4a8a
is positively stopped exit0/noSecrets, retired nonforced by exact ID and absent.
This narrows the rootless host-status cause without a permission grant.

Contract-first decision150/host administration/security/invariants/deployment/
troubleshooting align. Source21 changes client directory handles ONLY to
O_PATH|DIRECTORY|NOFOLLOW|CLOEXEC, preserving all ancestor/owner/group/mode,
attestation/binding-leaf/peer/lifetime checks.2new search-only regression cases
actually fail original client; corrected helper-client/protocol/status108tests
PASS8.12s. Lint/format/docs207/27/diffcheck PASS. No SELinux/MAC/DAC/capability/
systemd grant or runtime dependency. Frozen1361source21 snapshot827c1047/capture
e223625e has exactly8changes from20; no edits after freeze. Original strict
gate21 RUNNING, outer3655978/start431132735/session88837, codeea81b220; no outcome
inferred. Explicit two-field008fixture projectionba3012ea/snapshotdc1d3ff5 PASS;
canonical002 unchanged, new native008/rootless009 artifacts must carry corrected
client. Source20 native25 PASS remains historical, not new21 acceptance.

Next close gate21, new source21 artifact/image/guest staging, then fresh actual
native/rootless shared-Caddy browser and dedicated isolation/fault/secret-lifecycle
acceptance. WEB006 remains in_progress/uncommitted; AUTH-08/HOST-01–03 and
WEB007–026 pending. Guest app lane quiescent/secretstoreempty; production
unchanged. Full original handles/pins and blockers are in ignored checkpoint185.

New canonical artifact710d9e07 and explicit008 fixtureda8738eb built; shared
API/UI image92c09797 retains both pinned UBI10micro FROM stages. Source21
transfer950426db and original rootless31 Basic/3alias preservation54c4c33f PASS.
Original native008 actor FAIL66c9add9 at readonly restorecon preflight BEFORE
installer, retains private1361source. Wrong-command readonly diagnostic stays
FAIL; corrected8cb5af24 identifies52old0.2.7 paths with only SELinux User
unconfined_u->system_u, same role/type/range/mode/owner. Exact52metadata-only
normalizationdf0cce03 PASS, no policy/permission grant. Separate first installer
actually PASS87fdfb20/24.70s, original3680671 reaped/gone, measured008/108package
files. No recopy/replay or failed-receipt promotion. UI local-v1 preflight refuses
stale snapshot before guest; corrected actual-v2 PASSb052b7d0/5.41s, six assets,
installed capture and native candidate only; original3680980 reaped/gone.

Actual OCI exportfad25c7f and prelabelled exclusive guest transfer PASS. Full
build95a9f77a/585688B separately uploaded/held for genuine rootless provenance.
Original image loadPASS7.59s, runtime auditPASSac7f6066/34.43s:108package/6UI,
35tools/8modules absent, real981->983 mapping,capless/NNP/seccomp/readonly/noNet/
noSecrets; actual micro ancestry. ProbeCIDf8598dc6 retired exact-ID/nonforced,
originalouter135702 gone/cgroupclosed,3oldstoppedaudits/emptysecrets preserved.
No source21 native/rootless application/browser or dedicated acceptance yet.

New environment projection original3681622/start431366568/session3616 RUNNING;
no outcome inferred/no concurrent guest call. Next close it, rootless009 staging,
new genuine profiles/authority31/controller32, fresh native26/rootless32 normal
and dedicated isolation/fault/secret-lifecycle tests. WEB006 in_progress and
uncommitted; AUTH-08/HOST-01–03 and WEB007–026 pending. Source20native25 PASS
remains historical; rootless31FAIL/stoppedfalse and all original failures remain.
Production/NAS/livehistorical frontend untouched. Full actual pins and original handles:
`.scratch/web-006-source21-current-state-v186.json` SHA256 833acc11e33a3f42176916ee1a371fae33059cfabbb660330f07d9a3de1f9271.

Checkpoint187 (2026-10-24): new source21 environment actual PASSa7e06dc0/
17.13s, original3681622 reaped/gone. Same-inode readonly108package projection,
realUID1000 installed008 import,194browser files/50dirs and all old source
1361full9/hash/SID records rejoin. Rootless009 actual stage/render PASSa18ce1d4/
6.39s, original3682269 reaped/gone; actual uploaded full585688B build receipt
95a9f77a is held with inode/hash/selectedfields. No app starts or selector switch.
Actual protected proposals PASS5.62s, original3682582 reaped/gone: genuinely
new native008/rootless009 build snapshotdc1d3ff5, original configuration-only
permissions retained, temporary own selectors preserved and current absent.

Before authority publication, static review identifies rootless31 stop-harness
failure: it inspects containers after real services auto-remove them. No absence
can prove exit0. New controller32v2 is being prepared/reviewed to arm exact
original-CID wait observers while live, then perform one normal stop and retain
actual exit statuses/reaped handles, originalPID/cgroup drain and exactabsence.
No product runtime/unit/permission or canonical source change. V1f0 retained;
v2/authority31 not yet published or executed, no outcome inferred. Existing
rootless31FAIL/stoppedfalse is never rewritten. Guest app lane is quiescent,
secrets empty; native26/rootless32 and dedicated isolation/fault/lifecycle proof
still required before WEB006 commit. Source21 gate remains green/frozen, all
required cases pending; production untouched. Full actual pins/handles:
`.scratch/web-006-source21-current-state-v187.json` SHA256 2e1e1d21cf48779b012652d1ca394849027c3be9ae4f264f5c5f6cb2cb9f4de0.

Checkpoint188 (2026-10-24): reviewed controller32v2 8adfaaa7/117990B is
actually published and loaded. Six real local child/pipe tests PASS0.607s,
separate review confirms fixed grammar/no force/replay/payload reads. Exact
original3CID waiters arm whilelive, original normalstop happens once, real
waitstdout0/CLI0, exactCIDabsence1 and originalPID/cgroup drain are required;
collector preserves firstfailure and retains pipes until actualEOF/reap.
Actual stock Podman/rootless normal acceptance remains pending.

First authority actor FAILb478a93b before any PUBLIC/controller/control/
generation/sudoers publication: newWORK only, error-directory parentSID check
did not exempt exact protected existing ROOT unconfined_u:usr_t. Original
failed scope/5evidencefiles retained. New independent preparation-v2 validates
that failure and alltargetabsence; exact ROOT fd/full9/owner/mode/SID guard,
labels only the NEW EMPTY error directory. No parent relabel or product change.
Actual authorityv2 PASS3.75s, original3686158/start431529295 reaped/gone:
264control inputs preserve all247old rows in order; installed validator,
controllerload/visudo, fullpackage/browser/source/label/kernel/NFS/strict
closure pass. Newprotectedreceipt
`/opt/hfcache-web006/fixture-authority-v31-preparation-v2/RESULT.json`.

Fresh source21 native26 original functional run NOW RUNNING through real
installed008/sharedCaddy/3browser tooling. Original outer3686310/
start431533207/session49414, actor de238f20/caller03528b81; no result inferred
and no concurrent guest call. On completion collect actualpostrun/normal proof,
preserve its actual Basic/aliases, then rootless32 with actual armed ownership
watcher. Dedicated isolation/fault/secret-lifecycle proof is still mandatory.
WEB006 in_progress/uncommitted, AUTH-08/HOST-01–03 and WEB007–026 pending;
source21 strictgate remains green/frozen. All old failures and rootless31
startedtrue/stoppedfalse stay. Production/NAS/livehistorical frontend untouched.
Exact current pins/handles: `.scratch/web-006-source21-current-state-v188.json`
SHA256 d0b683736c81dff62a0e5f9863ab1eef99b650044b93e8b4455d83b51a804042.

Checkpoint189 (2026-10-24): fresh source21 native26 ACTUAL PASS95167582/
338.50s; original3686310/start431533207 reaped/gone. Checker136100/
start32416193 returns0/335.69s. Generation401b22ff37074827b2efab9911bcd2c2,
SUMMARY47d9e60a/385049B has4modes/3engines/33host assertions and12same-Caddy
certificate-specific TLS refusals,0requiredretries/skips/normalstop. Actual
readonly postrunc8b01ae7 PASS1.81s;8record normal adapter880156ee/19238B,
all original handles gone, real TLS/noHTTP-response/secret gates rejoined.
Native actual Basic inode118708497/root:983/0640 and3aliases NOREPLACE-preserved
4cbe3bae PASS1.84s, no payload/digest read. Fresh rootless emptybaselinef9909fa6
PASS1.51s, original3687804 reaped/gone.

Rootless32 actual original coordinator FAILdecaafbe/82.26s, outer3688017/
start431587685 reaped/gone. Watcher141571/start32470630 andrunner141572/
start32470656 gone. Original checker141576/start32470682 returns1/80.14s:
all3trusted engines baseline hoststatus unavailable versus supported;0accepted
cases/noSUMMARY. Original runner additionally tries missingSUMMARY and records
secondary FileNotFoundError; that does not replace original checker failure.
New inert future error collectors preserve both and always collect the watcher;
executed32 bytes/failure remain unchanged. No replay or acceptance promotion.

Readonly diagnosisdac1c78c PASS1.846s, original3689465 reaped/gone: generation
ea614316bb6a462c8458971e239cd8fe startedTRUE/stoppedTRUE. Controller32v2 drain
fix ACTUALLY passes stockengine:3original exactCID waits return0/stdout0newline,
3exactCIDexists return1,6observers EOF/reaped/no lostFD/unknown,69original
generation PID/start pairs gone, no controller errors. Actual3liveCID/6ID
ownership passes as a separate partial proof; untrusted3browser TLS refusals
pass, but hoststatus/normal acceptance does not. Basic inode118729990/983:983/
0400/secret_t read metadataonly. Original rootless31FAIL/stoppedFALSE unchanged.

Failed32 separate exact-ID cleanup ACTUAL PASS5.117s, original3691144/
start431702236 reaped/gone: genuine liveownership/emptybaseline/failed receipts
and actual independent drain held; whole-store opaque backup labelledsecret_t
BEFOREbytes;6original creation-bound IDs each get durable intent/nonforced
removal, finalempty/3oldstoppedaudits/noRefs/strict13role4cgroup5endpoint closure.
No successful-normal proof fabricated, no current Basic/alias switch or service
replay. Next a new helper-only sameimage metadata/client-stage probe to identify
remaining refusal; not started, no authpayload or host-status acceptance implied.
Source21 strictgate remains green/frozen. WEB006 and AUTH-08/HOST-01–03 remain
pending/uncommitted, WEB007–026 pending. Production/NAS/livehistorical frontend untouched.
Full current pins/handles: `.scratch/web-006-source21-current-state-v189.json`
SHA256 ffb40d7d5d09838ca183784c151c4a44c87ca6bd6e8755d3fb3bf5fa9f6cb5e6.

Checkpoint190 (2026-10-24): first helper-only diagnostic FAIL5275cc64/
3.196s, outer3692658 reaped/gone: missing outer select import atline641,
before any probeCID or image stage. Helper143896/start32642462 started/stopped
normally and gone; strictclosure/secrets-empty verified. Originalfailure stays.
New v2scope holds that actual closed failure; importsselect, composednamespace
audit resolves allglobals before effects. Actor41911cba/caller7ee9ddf0.

Actual helper-only v2 probe PASS6.887s, original3693242/start431780291 reaped/
gone. Real canonical container-service projection runs asUID983 from current.9;
actualsame UBI10micro image92c09797 undercontainer_t,981:981/noSecrets/noNet/
caps0/NNP/ROhelpermount. ALL measured stages pass:O_PATH parent, nonsecretbinding
read,actualEndpointBinding.from_startup/_runtime_binding, realSO_PEERCRED
(pid0,uid65534,gid65534),SO_PEERPIDFD(fdinfoPid0/NSpid0/livepoll), actual
binding.connect. No auth/protocolpayload/status request. Original helper143992/
start32663253 stayslive across samples, stopsnormally/drains; exactdiagnostic
CID exited0/noSecrets and retirednonforced, strict13role4cgroup5endpoint and
emptysecrets restored. No functional/rootless hoststatus acceptance inferred.

Remaining refusal is AFTER the proven transport. Next narrow actual fixed
peer-observer/request path, using retained facts first and a NEW diagnostic
API cohort only with original confinement, watcher-before-secrets, preserved
Basic/aliases and fixed safe tracing. Newcohort/trace being prepared, notrun.
No productcode change or policygrant byguess; source21 remainsfrozen/strictgate
green. Native26PASS retained; rootless32FAIL/0acceptedcases remains unchanged,
its genuine3wait0/3exists1/drain and6IDretirement are partialproofs only.
WEB006 and requiredAUTH/HOST cases remain pending/uncommitted. Production,
NAS/livehistorical frontend untouched. Full exactpins/handles:
`.scratch/web-006-source21-current-state-v190.json` SHA256 e7c61dc1dc4dc7df8fc0cb11f84dc339e15c22f7abcb62fcdb90eb4e3fb9acff.

Checkpoint191 (2026-10-24): rootless32 retained original API PID141854/exact
CID402337246bc1602c61488f1d8c93756a2b22606c34f842ca33ae10c95fed3865
has actualcgroup .../libpod-<FULLCID>.scope/container. Source21's scope-only
host_peer._container predicate1825 evaluates FALSE on these measured joined
facts. Independent review confirms this is a demonstrated compatibility refusal;
innerPID1/UID/GIDmaps/manager distinction and adjacent exportedfacts pass. No
second mismatch is claimed; complete vendor JSON stillneeds retained-data review.

Contract-first hostadmin/ADR150/INV020/humantroubleshooting refinement: allowonly
exact full inspectedCID scope or its SINGLE fixed container child. Original raw
cgroup staysinproof. Every PID/pidfd/manager/image/argv/env/map/mount/namespace/
security check remains. No privilege/SELinux/capability/dependency change.
New regression actually FAILS originalcode (1fail/1pass); correction plus
206peer/protocol/client/status tests PASS13.73s, lint/format/docs207/27/diffcheck
pass.21 independent security mutations cover BOTHlayouts; foreign64CID/shortCID/
nonlibpod/scopex/containerx/nested/arbitrary/trailingSlash paths refuse. Independent
source review passes, not installed acceptance. No new peer33diagnostic activated.

Frozen source22 1361files snapshot6496929e, capture04e0e36b/684B, exactly6changed
files from21. No canonical edits aftercapture. Canonical002unchanged; explicit
two-TOML-field fixture010 projectionb6d3491c/245249B/snapshot04c9aa85 preserves
all108source22 package bytes. Rootlessdeployment011. Newartifacts/image/staging
remain unbuilt/unexecuted; preparation only while original strict gate22 RUNNING
outer3696772/start431918922/session11188, runnerbbaf74be. No outcome inferred.
No new service/container/install activation before actual green gate22.

Source21 native26 PASS remains genuine historical evidence, not source22
acceptance. Rootless32 FAIL/0cases and original69handle/3wait0/3exists1 drain,
6IDcleanup/emptysecrets/transportprobePASS remain preserved separately. All app
rolesinactive; no guest executoractive. WEB006 in_progress/uncommitted,
AUTH-08/HOST-01–03 and WEB007–026 pending. Production/NAS/livehistorical frontend unchanged.
Exact current pins/handles: `.scratch/web-006-source22-current-state-v191.json`
SHA256 535692f8b8b44b8c354a064607428dbabe0da3dd2d07daa5bc46d2474f18248d.

Checkpoint192 (2026-10-24): source22 strict gate ACTUALLY PASSED, original
outer3696772/start431918922 reaped and gone, rc0,1254.87s. Command:
`historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`. All1361 frozen inputs
unchanged;7782 Python tests passed (52 explicit opt-in deselections),572 historical frontend,
2786 web unit,2846 component,21 sandbox/10 driver checks, locked base/server/MCP
wheel profiles, strict wire/lint/types/build and real HTTP/API React fixture
passed. Required selected tests had no skips; installed Caddy/host acceptance is
separate. Log SHA2569c9f095e91d17bebe4e7a04882f067a4925637a8bd9d7ce3c948f4fff9917c9b/100877B.

One dedicated READ-ONLY collection rejoined the original protected source21
67372B container-inspect capture and closed its exact QEMU/boot/SSH/input
handles. All19 pre-process metadata predicates and the original mount verifier
pass. The only demonstrated mismatch remains the old scope-only cgroup check
versus the original exactCID .scope/container path. No live PID, new source22
runtime or functional acceptance is inferred; no service/container/credential
or protocol request occurred. Reader outer3714943/start432040077 rc0,0.78s,
reaped/gone; independent result review agrees.

Fresh source22 build/staging is underway. An initial host-only packet preparer
refused in overlay_versions before publishing a packet or contacting the guest;
its failure is retained and the ignored fixture codec is being corrected.
Source22 remains frozen; no product-code change or repeated full gate is needed
for that fixture-only correction. WEB006 remains in_progress/uncommitted;
AUTH-08/HOST-01–03 remain pending. New010/011 installed native/rootless browser,
dedicated isolation/fault and secret lifecycle acceptance are still required.
Previous source21 native26 PASS/rootless32 FAIL and all original evidence remain
distinct. Production/NAS/installed predecessor interface remain untouched.
Current pins: `.scratch/web-006-source22-current-state-v192.json`
SHA256ad616f7c24a8242f4c3c2ce7864d7bbcffd77ac5e73b4ce67f69f16ce452128d.

Checkpoint193 (2026-10-24): canonical and explicit010 fixture artifacts,
shared API/UI image, transfer, readiness, native010 first installation/UI,
OCI export/transfer/full receipt upload, guest load and runtime audit ACTUALLY
PASS with original executors reaped/gone. Compact independent evidence index:
`.scratch/web-006-source22-build-staging-EVIDENCE-v1.json`,
SHA256a2eaadd7d41da41106bd3531eaee5265bfd13c845acb4f890febb666bc9c0dec. Gate22 remains green on unchanged source22.
Image ccb43a3e has actual pinned UBI10 micro ancestry,108 backend/6 UI leaves,
35 absent tools/8 absent modules, capless/NNP/read-only/no-secret confinement;
its one audit CID exited0, drained and was retired without force.

Readiness preserved previous Basic inode118729990 and three aliases without
replacement or payload inspection. Exactly52 old009 SELinux User corrections
preserved type/role/range/mode/owner/bytes, and all264 prior control inputs were
rejoined. Original native installer144380/start32963213 ran once, rc0/reaped,
17.06s; outer3719599 closed in38.19s. UI outer3720229 passed in5.55s.

Environment-v1 FAIL47dfa431 was a fixture clone allowlist omission, before any
public copy. New environment-v2 also corrected the borrowed inventory name,
held the original failure/work and ACTUALLY PASSED19.16s, outer3722316 reaped/
gone. It proves the new108-leaf read-only package projection and194 browser
files/50 directories, preserving all old17/19/20/21 source trees. Rootless011
stage/render ACTUALLY PASSED5.46s, original3722484 reaped/gone; no activation.

Profile-proposals-v1 ACTUALLY FAILED3.74s, original3722690/start432161324 reaped/
gone. Canonical prepare() correctly refused a protected bootstrap binding hash
at host_policy.bindings1048. No profile/policy proposals were published; its
temporary native selector inode60996809 was preserved with NOREPLACE, and
strict role/cgroup/endpoint closure passes. The new peer module still needs its
separate protected bootstrap installation in the owned guest. A narrow guarded
refresh and NEW profile-v2 scope are being prepared, preserving original files,
failure/work/selector and security policy. No product code or gate replay.

Native27 must be followed by native isolation/fault acceptance while its Basic
file still has native ownership, before preservation and rootless33 acceptance.
All this remains pending. Source21 native26 PASS and rootless32 FAIL remain
historical, distinct evidence. WEB006 in_progress/uncommitted; AUTH-08/HOST-01–03
pending; WEB007–026 pending. Production/NAS/installed predecessor interface remain untouched.
Exact current pins: `.scratch/web-006-source22-current-state-v193.json`
SHA2569348617f94f10fad55af9771422da3602751733cfbd34d899d1f8799daafbff9.

Checkpoint194 (2026-10-24): source22 staging is complete through ACTUAL successful
authority32 publication. Independent compact evidence indexv5,
SHA2563c4c788bcfdb37cf2bcc901480c356a2b830da9005387a82bf2a33545b2a1d4f/33424B, verifies18 successful original
stages/observations and retains seven original failures without promotion.
Gate22 remains green/frozen; no product-source edit or repeated build/install.

Bootstrap-refresh-v1 failed on a missing contextmanager decorator before target
access. Refresh-v2 refused a guessed SELinux User before candidate/intent/mutation.
The first metadata collector also retained its WORK-lifetime failure; corrected
metadata-v2 ACTUALLY PASSED1.58s and measured old peer inode78157341/dev64515,
SHA2803c60e, unconfined_u:object_r:hfcache_host_helper_code_t:s0. New refresh-v3
ACTUALLY PASSED2.09s, original3726222/start432278040 reaped/gone: old exact inode,
hash and SID preserved with NOREPLACE; empty candidate labelled with that SAME
SID before bytes; source22 becb6ddb peer published without overwrite. Kernel,
policy, units, roles, credentials and selectors unchanged. No bootstrap replay.

New profile-v2 ACTUALLY PASSED4.75s, original3726418/start432283464 reaped/gone,
holding the original failed proposal/work/selector. Native222/rootless43 authority
files and original permission bits agree. Authority32 ACTUALLY PASSED3.99s,
original3726704/start432292903 reaped/gone: control33 has280 actual inputs with
all264 previous rows preserved in order; new fixturebf27/controller13d9 and
installed validator/visudo joins pass. No application acceptance from staging.

Original native27 real same-Caddy/browser run outer3726922/start432298258/
session22968 is RUNNING; no outcome inferred. Preserve this exact run; do not replay it. After
positive postrun, native isolation/fault checks must run BEFORE preserving its
Basic file and crossing to rootless33. Rootless normal, dedicated isolation/fault
and exact-ID secret lifecycle acceptance still remain required. WEB006 remains
in_progress/uncommitted; AUTH-08/HOST-01–03 and WEB007–026 remain pending.
Production/NAS/installed predecessor interface are untouched. Current original handles/pins:
`.scratch/web-006-source22-current-state-v194.json` SHA2569d1bb43de1b4e555e1b8c13db6643659109beac3accfb68fb0da39bcb1edef6a.

Checkpoint195 (2026-10-24): source22 native27 ACTUALLY PASSED333.16s, original
outer3726922/start432298258 reaped/gone, checker145762/start33181217 rc0/reaped
in330.27s. Real production-built UI -> same actual Caddy/trusted TLS -> installed
native010 API, four modes/three engines/33 host assertions and12 negative TLS
checks; no required retry/skip. Independent postrun ACTUALLY PASSED1.70s,
outer3728181/start432341444 reaped/gone: all8 original records close, generation
b0accf80979942e5bbaf1fe55c9a56e7 stoppedTRUE, all original handles gone, same
Caddy/TLS joins retained. Protected normal code e85e132e/18777B is held directly.

Native Basic inode118755357/root0:GID983/0640/secret_t remains current, metadata
only. Native fault source publication ACTUALLY PASSED1.77s, original3728713/
start432359350 reaped/gone; no fault entry or normal source was executed or
republished by publication. This is preparation, not dedicated acceptance.
Next acquire actual helper filter/unit/sentinel metadata, then native dedicated
isolation/fault cohorts BEFORE Basic preservation/rootless33. New collectors and
rootless generation-specific exact-ID cleanup adapters are being prepared inertly.

Human operator audit found two upgrade/rollback gaps: explicit protected fixed
bootstrap refresh before index prepare, and retention/restoration of matching
bootstrap bytes/inodes/labels alongside selector rollback. Initial copy/label
instructions and independent policy boundaries are correct. A docs-only patch
is being drafted without changing frozen source22; it must land with validated
final documentation before this work-package commit. Runtime fixtures will
retain their actual source22 identity. WEB006 is still in_progress/uncommitted;
AUTH-08/HOST-01–03/rootless33/dedicated/lifecycle acceptance remain pending.
Production/NAS/installed predecessor interface remain untouched. Exact pins/original handles:
`.scratch/web-006-source22-current-state-v195.json` SHA25697f0a1868759021d727249677640524bc878b1adab2897d2c37a3080dd6876e6.

Checkpoint196 (2026-10-24): native isolation-input metadata ACTUALLY PASSED3.96s,
outer3729611/start432392172 reaped/gone. One helper151199/start33275101 started,
measured root/helper-domain/NNP/seccomp with24 filters, then normally stopped and
drained. Actual unit79d491f8/policy27 receipt9f451aa2 and owned NFS sentinel
dev58/inode118335703/nfs_t/full9 were captured metadata-only; no protocol or
container. This is metadata preparation, not dedicated acceptance.

First native fault collector ACTUALLY FAILED2.72s, outer3730013/start432404701
reaped/gone; bootstrap151300/start33287686 rc1/reaped after0.42s. Original
stderr683a429a/1619B is retained. Safe original read-only traceback/errno
collection ACTUALLY PASSED (latest3732060/start432479069,0.80s): OSError errno24,
EMFILE at parent_descriptor90 while the preloader held108 package leaves with
duplicated ancestor FDs. Fault main, generation and RESULT were not reached;
the collector's missing-RESULT failure remains a secondary failure. All roles
are inactive; original current Basic was unchanged. New bounded-FD preloader
and fresh collector scope are being prepared without raising limits or replay.

Initial native27 preservation ACTUALLY PASSED1.70s, original3731972/
start432476839 reaped/gone. Basic inode118755357 and three original native
aliases were preserved with NOREPLACE before a new cohort can regenerate owned
fixture credentials. They are now absent. Native fault/isolation collectors
must join this actual preservation for their first absent-start preflight.
An inter-native preservation and final-native adapter will retain later actual
cohort credentials; rootless transition still requires BOTH native dedicated
passes. Frozen source22/gate22/native27 normal/postrun remain valid. Required
AUTH-08/HOST-01–03, rootless33, dedicated/lifecycle and human doc corrections
remain pending; WEB006 is uncommitted. Production/NAS/installed predecessor interface untouched.
Current pins: `.scratch/web-006-source22-current-state-v196.json`
SHA2564a565bc9106ccae450b599cbd1f419538e746c3e2fb55bdbc71716045aaa4941.

Checkpoint197 (2026-10-24): corrected bounded-FD preload actually verified108
leaves/11 shared directory handles with137 open FDs, unchanged soft1024/hard524288,
and closed at8 FDs. It reached fault main. Native fault-v2 still FAILED before
generation: canonical manifest validation was invoked as root while unchanged
validator requires the fixture owner UID1000. Original safe diagnosis PASS0.76s,
outer3750661/start433317546 reaped/gone, confirms exact path_input284 frames.
No validators or ownership rules were relaxed.

New private fault source dd8ad806/63395B changes only the two validator invocations
to finite owned UID1000 children and gives new result/workspace names. New source/
preloader publication ACTUALLY PASSED1.85s, original3753351/start433423685 reaped/
gone; original sources/results and both old budget records are held unchanged.
Actual local stem is publication-v3-final; earlier reserved v3 caller was never
executed. Corrected native fault-v3 ACTUALLY FAILED22.57s, outer3753692/
start433435502 reaped/gone; child151883/start34318448 rc20/reaped in20.55s,
stderr0/stdout633B. All13 roles/4 cgroups/5 endpoints close. Its original saved
state must be diagnosed before another cohort; no failure or missing result is
promoted. Current selector/Basic metadata is pending that read-only diagnosis.

Native27 normal/browser33 assertions/12 TLS checks and independent normal8
postrun remain passed. Native isolation sources are published, not executed.
Initial Basic/aliases remain retained in their preservation scope. Required
native dedicated, rootless33 and lifecycle acceptance remain pending; WEB006
is in_progress/uncommitted. Revised scratch-only human operator patch5a3e51ff/
8005B passes apply-check and clarifies preserve-before-replace, upgrade permission/
key retention and helper-aware rollback. It remains unapplied while source22 is
frozen; final human docs/gates remain required. Production/NAS/installed predecessor interface
untouched. Exact current pins:
`.scratch/web-006-source22-current-state-v197.json` SHA256d38db3f9218f872c5f59cff69cab6b2cefbbc153aa0cb32b045878e47bcc28fb.

### Checkpoint198 — native denial confirmed; fixture failures retained (2026-10-24)

Source22 remains frozen at canonical source snapshot
`6496929e8cbf8031993c0fd335f8621d5b0b73057599dcc21cbf4391f919e88d`.
The following are actual original executions. Read-only diagnosis and source
publication establish their stated collection/preparation scopes only.

| Original local result stem under `.scratch/` | Actual original outer PID / start | Outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-fault-native-v3` | 3753692 / 433435502 | FAILED, rc1, reaped/gone, 22.5733s | `9de6ccad5aeb0db88313048510440972c293a7c932c708621a68dd1fc3911e51` |
| `web-006-source22-native-fault-v3-safe-diagnosis-v1` | 3755252 / 433496354 | Collection PASS, rc0, reaped/gone, 0.7679s | `3f1e493b91f3ff754c4a12ded9be64adfcfc29e55783d4c95d812357dc4cfc26` |
| `web-006-source22-native-failed3-preservation-v1` | 3757110 / 433561558 | Preservation PASS, rc0, reaped/gone, 1.7527s | `60d9802ec8ca253652b2f7ceeea35a4bf94bfb63c635720dc80363eac103d088` |
| `web-006-source22-native-fault-preloader-publication-v4` | 3757297 / 433565820 | Publication PASS, rc0, reaped/gone, 1.8783s | `742bc3d49b60a7e1ebf1da89c814c74ecf8d1953bad39e688b5e3fe0c057d9fd` |
| `web-006-source22-fault-native-v4` | 3757436 / 433568462 | FAILED, rc1, reaped/gone, 2.1576s | `5d54fdb2c326279c958aa27e7d3094baeb8877ca6335afabe69144c5f568104a` |
| `web-006-source22-native-fault-v4-original-stderr-read-v1` | 3757838 / 433578627 | Collection PASS, rc0, reaped/gone, 0.7418s | `e329a58f48f46880af59ebaa9337b4f7fd2c8b5da61975701e9d4d74f9b27a2f` |

The failed3 child 151883 / start 34318448 returned rc20, reaped in 20.5518s,
with empty stderr and 633B stdout. Its original fault RESULT remains failed:
`/opt/hfcache-web006/installed-host-faults-source22-authority32-v2-native/RESULT.json`,
SHA256 `b657b57c69b6f2380d592410f946e2c3301816cb7974898f0eb6879a3a787803`,
19676B. Safe diagnosis identifies ValueError at `observe:845` →
`assert_post_refused:619` → `need:63`. The observed product refusal was HTTP 403 /
HFAPI002 / CLI exit 10, matching the existing contract; the private assertion
expected exit 2. No observed mutation phases or unknown input restorations exist.
Generation `852e90dfed034076a82e623fcbe0906e` has started/stopped/stop-attempted
true and all 29 original process handles gone. Its original protected generation
record is SHA256 `1bea20d435ec50a1d3f729ce4432118c6fd9f77241cf8af91224217479b32188`,
37052B. No denial result, partial assertion or cleanup is promoted to acceptance.

Failed3 preservation retained Basic inode 118779523 (root:983, 0640, secret_t)
and native aliases `/opt/hfcache/current`,
`/etc/hfcache/host-helper-deployment.json`,
`/etc/hfcache/host-helper-policy.json` with NOREPLACE, without reading Basic
payload or digest. All four paths were absent at preservation completion and
again in fault4's pre-cohort metadata. Their retained metadata identities and
contexts, unchanged historical normal8 and original failed3 result are joined
by the protected preservation RESULT:
`/opt/hfcache-web006/source22-native-failed3-preservation-v1/RESULT.json`,
SHA256 `8006f3f5ab39f8c0b9d5625816bd44bc0842ef545a82762c83a6d31f56b2e100`,
59891B. This records those instants; it does not infer later current state.

Publication4 created new NOREPLACE private source and preloader names and kept
all prior sources, results and budget records unchanged. The source is
`/opt/hfcache-web006/private-fault-code-source22-authority32-native-v3/faults.py`,
SHA256 `e250db80bda929103a8700913799d7e93cb6968587dfc1fe2e94d34a4770cb73`,
63396B. It changes the stale expected CLI exit to 10. Its new
`bootstrap-fd-budget-v4.py` is SHA256
`32f13b87fa571a922e39c9f2f2f7b99742f6c0dae26dcb74a7dbfc9a7c2c20e7`,
12110B. The protected publication RESULT is
`/opt/hfcache-web006/source22-native-fault-preloader-publication-v4/RESULT.json`,
SHA256 `e07733a5df6d1201d92146970dd0aec467b2205104475710250fe4cbdf1955b6`,
64802B. Publication did not execute fault main or create a generation.

Fault4 child 152349 / start 34451406 returned rc1, reaped in 0.1087s, stdout0,
stderr1147B. The collector retained the original child failure before attempting
acceptance validation; all 13 roles, 4 cgroups and 5 endpoints closed. Read-only
original stderr diagnosis reports only safe frames/classes: ValueError,
`<module>:204` → `main:171` → `load_fault:138` → `need:18`, no chained exception
or errno. The preloader's dynamic old private-v2 guard refuses actual private-v3.
The known main-v3 RESULT is absent; no fault main, new application generation or
mutation phase was reached. Protected original stderr
`/opt/hfcache-web006/source22-fault-native-v4/command-03-stderr` is SHA256
`dda1eec118af3cfea0e7febd1385bdbc1afcf0e8b206486a52aec4138bb8159d`,
1147B. The reader performed no service, container, credential or protocol action,
published no messages/arguments/locals/payload, and claims functional_acceptance
false. The original failed collector stays false. A fresh preloader5/collector5
is being prepared with the exact private-v3 guard and unchanged source e250;
it has no accepted functional result at this checkpoint.

Native27 normal/browser (33 assertions and 12 TLS checks) and independent
normal8 postrun remain passed. All 1361 canonical source22 inputs and gate22
remain unchanged by these ignored fixture packaging corrections. Native dedicated
fault/isolation, rootless33, lifecycle and AUTH-08/HOST-01–03 remain pending.
WEB006 is in_progress/uncommitted; WEB007–026 stay pending in dependency order.
Revised human operator patch v2 (`5a3e51ff` / 8005B) is scratch-only and unapplied;
human documentation and final strict gates remain required. The shared API/UI
image retains pinned UBI10 micro. Production/NAS/installed predecessor interface are untouched;
rollout, merge, push and tag remain unauthorized. No original operation was replayed.

### Checkpoint199 — native supplemental faults and inter-native preservation pass (2026-10-24)

Native fault5 ACTUALLY PASSED as a supplemental installed-fault cohort. Original
outer 3758671 / start 433603274 returned rc0, reaped/gone in 99.9185963003s;
original fault runner 152476 / start 34486208 returned rc0/reaped in 97.2586326580s,
empty stderr and 633B stdout. The collector invoked it once. Local actual result
`.scratch/web-006-source22-fault-native-v5-result.json` is SHA256
`4c3a72f8e6f161df452b9909f2cccaea0bd2fb41ce467bb6e772b5b8e2374367`,
378981B; its original executor receipt is
`.scratch/web-006-source22-fault-native-v5-execution.json`.

The five observed phases were `asserted_user_denied`, `unsafe_policy`,
`indexed_release_drift`, `peer_first` and `unproved_deployment`. The four applicable
phases retained original operation handles and unchanged fixed role identities.
The unproved-deployment fault used source-snapshot drift and kept the original
helper active; real Chromium, Firefox and WebKit browser checks passed through
Caddy. Its helper-down browser container exited0, init identity drained, with
unchanged inputs; report SHA256
`187c73eca057a3204243d2dad3ceac15a11349d5240b2d54dce8d0f811c5c57a`.
The peer-first sibling refused a real valid frame, while installed parser reach
remains false and the real Unix parser/source tests remain required.

`functional_passed`, `inputs_restored` and `restored_original_cohort` are true;
`cleanup_unknown` is false and `first_error_class` is null. Policy, indexed release
metadata and deployment inputs each have restoration_unknown false. Generation
`16f5664de755463380b65d14b4169aab` started, stopped and recorded the original stop
attempt; all 46 original PID/start identities are gone. All 13 roles, 4 cgroups
and 5 endpoints closed. Protected original fault RESULT:
`/opt/hfcache-web006/installed-host-faults-source22-authority32-v3-native/RESULT.json`,
SHA256 `5297f764f66bf64381eadb1944e63207311126de1450a959f291f0b01de311e2`,
43562B. Protected generation record:
`/opt/hfcache-web006/generations-v33/16f5664de755463380b65d14b4169aab.json`,
SHA256 `01e37b5170f1b06beb1c820b9ebc934d5fe514f758835037afcc1242abb0557c`,
49955B. Full feature and required-profile acceptance remain false by design.

The original bounded preloader measured 108 readonly package leaves / 11 shared
directory FDs / 137 total FDs, unchanged soft1024/hard524288 limits, and 8 FDs
after all 108 leaves and unique ancestors rejoined/closed. The corrected private
source remains e250db80/63396B. Original failures through fault4, their sources,
results and budget records remain retained; the successful fresh cohort does not
change their original outcomes or replay their handles.

Inter-native preservation ACTUALLY PASSED: original 3759171 / start 433616954,
rc0/reaped/gone in 1.8969367919s. Local actual result
`.scratch/web-006-source22-native-fault-preservation-v1-result.json` is SHA256
`9449e4a13176ae815ef18b5b7b1fe5b45580f1bf8f8527becbf2369d8068d542`,
206614B; original executor receipt is
`.scratch/web-006-source22-native-fault-preservation-v1-execution.json`.
It held the actual passed fault5 generation and unchanged historical normal8,
then retained Basic inode118708498 (root:983, 0640, secret_t) with NOREPLACE at
`/opt/hfcache-web006/source22-native-fault-preservation-v1/preserved-original-ui-administrator.json`,
without reading its payload or digest. `/opt/hfcache/current`,
`/etc/hfcache/host-helper-deployment.json` and
`/etc/hfcache/host-helper-policy.json` were also retained with NOREPLACE.
All four active paths were absent at completion, with strict closure true;
this is an observed completion state, not a claim about future cohorts.
No application/installer, permission, kernel, service or timer change was made
by preservation; it does not infer native isolation or rootless acceptance.

Canonical source22 snapshot
`6496929e8cbf8031993c0fd335f8621d5b0b73057599dcc21cbf4391f919e88d`,
gate22 and native27 normal/postrun remain stable. Native isolation coordinator-v2
is being prepared and is not published/executed at this checkpoint. Native
isolation, rootless33, dedicated isolation/lifecycle, human documentation and
final strict gates remain required. AUTH-08/HOST-01–03 stay pending; their new
positive functional ledger entry is scoped to these supplemental native fault
observations only. WEB006 remains in_progress/uncommitted and WEB007–026 pending.
Human operator patch v2 stays scratch-only/unapplied; canonical runtime/human docs
remain frozen. Shared API/UI runtime remains pinned UBI10 micro. No production,
NAS or installed predecessor interface changes; rollout, merge, push and tag remain unauthorized.

### Checkpoint200 — native isolation start failed; original cause unresolved (2026-10-24)

Native isolation ACTUALLY FAILED. Original outer 3760638 / start 433669933
returned rc1, reaped/gone in 9.2522897208s. Original coordinator 154201 /
start 34552870 returned rc1/reaped in 7.1453159910s, stdout0 and stderr3159B.
The collector preserved its original child failure before acceptance validation;
all 13 roles, 4 cgroups and 5 endpoints closed. Protected original collector RESULT
`/opt/hfcache-web006/source22-negative-native-v1/RESULT.json` is SHA256
`a655fed159361961f8b4361a01c5a94c2abe0bd884f984d10dbbc4f5ef2123ea`,
114971B. Its original stderr `/opt/hfcache-web006/source22-negative-native-v1/command-03-stderr`
is SHA256 `123a8a8583e45d67c8d09105f962698cb9021dc206f01696f2d31a12b07bf317`,
3159B. No failure is promoted to acceptance.

| Actual local result stem under `.scratch/` | Original outer PID / start | Original outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-negative-native-v1` | 3760638 / 433669933 | FAILED rc1, reaped/gone, 9.2523s | `390cb9b2a266465ff4359ae145c692e4c161fac623b7bc2177f198607fbee110` |
| `web-006-source22-native-isolation-v1-safe-diagnosis-v1` | 3761300 / 433693825 | FAILED rc1, reaped/gone, 0.8121s | `67680b55ffea648b8c53ed3b3261dd0b0617962fa9fa4ece9804c35db14a4dfb` |
| `web-006-source22-native-isolation-v1-safe-diagnosis-v2` | 3761744 / 433708204 | Collection REFUSED rc1, reaped/gone, 0.8243s | `0d41b1b709897f53cff02e5da56eead28f85fe359868602820d7c356ddaba124` |
| `web-006-source22-native-isolation-v1-saved-metadata-v1` | 3762094 / 433717981 | Read-only collection PASS rc0, reaped/gone, 0.7586s | `fca3b37bf283a9f6bcb6b7225aa29670786c5e14dcb9284f513d4d0ace50e7a9` |
| `web-006-source22-native-isolation-v1-safe-diagnosis-v3` | 3762194 / 433720464 | Read-only collection PASS rc0, reaped/gone, 0.7464s | `08f22637186a52dad8e2e250031e2cde492b7b7c8b348c0af0deb7f55c73175e` |

Saved metadata collection confirms generation
`1f600631b89c4a229e0c63512037461a`, started/stopped/stop-attempted true, paused
false and all 20 original generation PID/start identities gone. Its protected
record `/opt/hfcache-web006/generations-v33/1f600631b89c4a229e0c63512037461a.json`
is SHA256 `780fd470c8dde51c51b158f28d5875696fd1de0ec16d2ddf1ccbe188e1d0cfa8`,
23264B. The fixed owned public target is
`.scratch/web-host-fixture-negative-source22-authority32-v1-native/native-1f600631b89c4a229e0c63512037461a`
in the disposable source22 repository. Its actual RESULT is SHA256
`e9d3cbb4dd0764c5dd4d0303a28e619ce4e304c9c44dd13d4bb27fe67bdfe880`,
365B; stop.json is SHA256
`8d632440af49563c582320393175492f90301eb50dd2cc732939384459afa952`,
2590B. The original RESULT records failure_stage=start, observations_recorded
false, private_proof_cleanup_unknown false and required_profile_acceptance false.
Original cleanup_unknown and cohort_cleanup_unknown remain true because no
ready response was retained. Public stop separately proves inputs_unchanged,
recorded all20 gone and freshly observed all20 gone. This evidence does not
rewrite the original uncertainty or claim private-proof execution.

Diagnostic1 produced no guest output (its SSH child rc0/reaped with both channels
empty); the local wrapper retained JSONDecodeError/result-null. The existing
captured_guest_main calls main but swallows BaseException, so empty output does
not identify the isolation cause. Original executed reader bytes and caller are
retained. Diagnostic2 safely reports its own ValueError at `project_traceback:61`
while requiring recognized frames/classes. Neither failed diagnostic establishes
a cause or acceptance. Diagnostic3 changes only safe format parsing; it reports
format_recognized true, 38 lines, no errno or chained exception, a closed
other_exception_class_omitted enum and safe frames ending `control:172` →
`command:588` → `exchange:575` → `need:79` → `refuse:84`. These identify the
unchanged checker's nonzero-child-return refusal, not the underlying startup
error. Separate read-only collection of this original generation's
fixed_start_failure is pending; no guessed product, fixture or permission change
is justified by this trace.

The saved collection observed current Basic inode118788081 (root:983, 0640,
secret_t), current symlink inode61024785, deployment inode76316272 and policy
inode76316273, all present. This was O_PATH/full9/SID metadata only, with no Basic
payload or digest read. These are observed instants, not a future-state claim.
They await a separate guarded NOREPLACE preservation after the failure cause is
established. No credential or alias removal/rotation is authorized by diagnosis.

Native fault5's supplemental pass and native27 normal/postrun remain unchanged,
as do all previous failed results and receipts. AUTH-08/HOST-01–03 remain pending;
native isolation, rootless33, dedicated isolation/lifecycle, human documentation
and final strict gates remain required. WEB006 is in_progress/uncommitted and
WEB007–026 stay pending. Canonical source22/gate22 remain frozen/green; human
operator patch v2 is still scratch-only/unapplied. Shared API/UI runtime retains
pinned UBI10 micro. Read-only collectors made no service/container/protocol or
permission changes and inferred no functional acceptance. Production/NAS/live
historical frontend untouched; rollout, merge, push and tag remain unauthorized.

### Checkpoint201 — retained startup frames, current open probe and preservation (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual scoped outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-native-isolation-v1-start-failure-read-v1` | 3762965 / 433746206 | Read-only collection PASS rc0/reaped/gone, 0.7679797197s | `c532dd41554143d18ed344bfbfe12f60218811933d5081cc80e611e15d529616` |
| `web-006-source22-current-policy-simultaneous-open-v1` | 3763814 / 433776310 | Current behavior probe PASS rc0/reaped/gone, 0.9453317672s | `4189818241484e18985585760eeb9239ce1ecdccec593824017f8bc5d8d67945` |
| `web-006-source22-native-isolation1-preservation-v1` | 3764843 / 433813466 | Preservation PASS rc0/reaped/gone, 1.8434069520s | `ae081dede54a4816620c5c714c56166efe05bfb4da1d4ff8f748463b4715f8fa` |

The original saved generation `1f600631b89c4a229e0c63512037461a` records OSError
at `main:1848` → `start:1138` → `secret_label_gate:864` →
`secret_kernel_marker:359`, opening SELinux policy. The original errno was not
recorded, and the unchanged canonical checker discarded the launcher's stderr.
This narrows the original failing operation without establishing its cause.

The separate current-state probe held one open policy descriptor and observed
the second open fail with errno16/EBUSY. It did not replay the failed operation,
write/export policy bytes or change services, cohorts or security configuration.
Both kernel hashes remain
`45bb34e8f897feb344c9b18e895a2d07f8a09a0dc5db41b78331276140a8167f`;
the first descriptor and all observed descriptors closed. Its explicit
original_failure_errno_inferred and original_failure_root_cause_established
flags are false. The current EBUSY observation must not be reported as the
original errno or root cause.

Preservation joined the unchanged original failed RESULT and stopped generation
record SHA256 `780fd470c8dde51c51b158f28d5875696fd1de0ec16d2ddf1ccbe188e1d0cfa8`
with all20 original PID/start identities freshly gone. Original failure_stage
remains start, observations_recorded false, private_proof_cleanup_unknown false,
required_profile_acceptance false, cleanup_unknown/cohort_cleanup_unknown true.
These original flags were not rewritten based on the later drain evidence.
Basic inode118788081, current symlink61024785, deployment76316272 and policy76316273
were each retained metadata-only with renameat2/RENAME_NOREPLACE, rc0/completed;
Basic payload/digest was not read. The preserved Basic is
`/opt/hfcache-web006/source22-native-isolation1-preservation-v1/preserved-original-ui-administrator.json`.
All four original active paths were absent at preservation completion, with
historical normal8 unchanged and strict closure true. No application/installer,
permission, kernel, service or timer change was made by preservation.

A new scratch coordinator-v3 is being prepared solely to retain bounded stderr
for the four existing fixed launcher phases, concurrently drain both channels,
and preserve original child status. It uses fresh base
`web-host-fixture-negative-source22-authority32-v1-attempt2-native`; the future
collector revision is v6. This is fixture observability preparation, not a
controller, policy or canonical product change. No new cohort has executed at
this checkpoint. Original failed isolation and failed diagnostics stay retained.

Native27 normal/postrun and native fault5 supplemental passes remain unchanged.
Canonical source22/gate22 stay frozen/green; human patch v2 remains unapplied.
Native isolation, rootless33, dedicated/lifecycle, human docs and final strict
gates remain required; AUTH-08/HOST-01–03 stay pending. The existing functional
ledger remains unchanged at this checkpoint because these new records are
read-only diagnosis/current-behavior/preservation evidence, not new functional
acceptance. WEB006 stays in_progress/uncommitted; WEB007–026 remain pending.
Shared API/UI runtime retains pinned UBI10 micro. Production/NAS/installed predecessor interface
untouched; rollout, merge, push and tag remain unauthorized.

### Checkpoint202 — isolation2 private-proof failure; inner cause/lifecycle pending (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-negative-native-v2` | 3766361 / 433867300 | FAILED rc1/reaped/gone, 17.7940492360s | `fa8efcfea3caba3b0c6356913e2ace7c8dddea122011c5da48e1a7972c38be71` |
| `web-006-source22-native-isolation-v2-safe-diagnosis-v1` | 3767370 / 433901752 | Read-only combined collection PASS rc0/reaped/gone, 0.7898618048s | `dcd33b2f35e2d3c299bd4ed6ac49dc1832a5443c98576125b6e16c10eeb51f01` |

The original coordinator 154750 / start 34750237 returned rc1/reaped in
15.7017621690s, stdout0, stderr3023B/SHA256
`69cd8476bf882a8245149ee6b7cd23c1b0f26933a01c56bad79d09b36f0b718d`.
Protected original collector RESULT
`/opt/hfcache-web006/source22-negative-native-v2/RESULT.json` is SHA256
`19e9cd847c112b42174fe96d897688eaf8b7b3ef5549d448bec6eac059a440ff`,
118534B, with passed/all_inputs_rejoined_and_closed false, RuntimeError and
strict13-role/4-cgroup/5-endpoint closure true. Original isolation1 failure and
its cleanup flags remain retained. No failed outcome is promoted.

The combined reader holds the original saved public RESULT and exact failed
phase stderr path/hash/bytes/full9. Its unchanged safe parser accepts qualified
class names and indentation, records format_recognized without requiring frames,
and exports only function/line/class/numeric errno, not messages or payload.
Actual launcher rows are:

| Phase | Original PID / start | Exit | Original observed closure |
| --- | --- | --- | --- |
| start | 154752 / 34750319 | 0 | Both channel EOFs; reaped, original identity gone |
| private-proof | 154929 / 34751489 | 1 | Both channel EOFs; reaped, original identity gone |
| stop | 155016 / 34751668 | 0 | Both channel EOFs; reaped, original identity gone |

All three show no deadline, interruption, overflow, signals or replay. The
failed private-proof stderr is 2667B/SHA256
`43f7f68551805020a39ae32e163b643e991c3e8faee7282110aaa57234476658`
at the owned attempt2 target's `launcher-private-proof-stderr.bin`. Safe frames
end `perform:820` → `owned_setup:445` → `need:41`; upstream frames include
`coordinate:854` and `retained_operation:723/731`. No errno or chained exception
is recorded. Reached source line445 checks the child record state equals
complete after the child returncode0/reaped/timely/no-overflow checks have passed.
The actual inner error_class/record has not been joined, so these frames alone
do not establish that first failure.

Generation `dcdd4d59179f483f84b77b44598f88ef` has started/stopped/stop-attempted
true, paused false and all37 original recorded application PID/start identities
gone. Protected generation record is SHA256
`49388b70127f3d9625bc1c479a45b44af5bf3eef0a668f0bf27c17f52db6ee36`,
38060B. The owned public RESULT is SHA256
`f25b00b06e24ee2ea0de30adedfff969a30b35fc301b83b88fd4cfc2c5596e66`,
6063B; public stop.json is SHA256
`1be9d61642928bf7a22c24621e73138c85fe55312c32375c95e54cf23e55b0f0`,
4018B, recording unchanged inputs and all37 gone, freshly rechecked by diagnosis.
Original failure_stage is private-proof, observations_recorded/required-profile
acceptance false, cohort_cleanup_unknown false, private_proof_cleanup_unknown
and cleanup_unknown true. These flags remain unchanged. A separate custom-unit
LIFECYCLE diagnosis is pending; app-role closure and launcher reap do not prove
all private-proof children closed.

Independent static review confirmed a fixture contradiction: projection
`mount_rows:85` rejects NFS, while the required owned archive-inode bind retains
its NFS filesystem type. A minimal fixture correction is being prepared UNBOUND,
preserving readonly, exact mount-delta and metadata checks without security or
canonical product changes. This is a static finding; it must not be identified
as this original child's first failure until the actual child record is joined.
No new source/cohort/permission action is established by diagnosis.

Current Basic inode118779524, current symlink61030266, deployment76316275 and
policy76316276 were observed present metadata-only. No Basic body or digest was
read. Original results/handles are retained. Native27 normal/postrun, native
fault5 supplemental pass and frozen canonical source22/gate22 remain unchanged.
AUTH-08/HOST-01–03 stay pending; native isolation, rootless33, dedicated/lifecycle,
human docs and final strict gates remain required. One scoped failed isolation2
functional ledger record is added per case; read-only diagnosis is not a separate
functional test or acceptance. Human patch v2 remains unapplied; WEB006 stays
in_progress/uncommitted and WEB007–026 pending. Shared API/UI remains pinned
UBI10 micro. Production/NAS/installed predecessor interface untouched; rollout, merge, push and tag
remain unauthorized.

### Checkpoint203 — private lifecycle joined; failed/fresh preservation retained (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual scoped outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-native-isolation2-private-lifecycle-read-v2` | 3769347 / 433976374 | Read-only collection PASS rc0/reaped/gone, 0.8089915123s | `6e9f8d509fbd51ecd233a64fe5577acddd5df19189963db0478ad962dc8e75b7` |
| `web-006-source22-native-isolation2-preservation-v1` | 3770436 / 434019258 | FAILED rc1/reaped/gone, 1.3647615723s | `2a6f9bf7769246dcb3b5b6bfc832ff761376837fb02f7b99e8a8b12cec9e79eb` |
| `web-006-source22-native-isolation2-preservation-v2` | 3771223 / 434050188 | Preservation PASS rc0/reaped/gone, 1.9577131169s | `04121c44d80e9673d8717cea8ab4b4ba639fe280a40730ffbc3dcefa7efada98` |

Read-only lifecycle collection confirms custom unit
`hfcache-web006-negative-native-dcdd4d59179f483f84b77b44598f88ef.service`
is inactive/dead, MainPID/ControlPID0, with its physical cgroup absent/empty.
The retained root155004/start34751602 and setup155007/start34751640 are freshly
gone, as are all37 original recorded application handles. The original lifecycle
still records owned_children_reaped=false. The original coordinator's
private_proof_cleanup_unknown/cleanup_unknown=true, failure_stage=private-proof
and observations_recorded=false are unchanged. Current known-handle drain does
not rewrite original reap/cleanup uncertainty or establish feature acceptance.

The setup record retained wait_status0/reaped/timely/no-overflow/no-broken-pipe,
44 observed/prefix bytes and SHA256
`36af17c29094d663e5f8a553d2512b41626fd749ba43f9fae1bd1fea0e5a126c`.
Exactly one of69 closed canonical refusal candidates matches that length/hash:
class Refused. No raw setup body or unknown values were exported; no original frames or errno
were recovered. original_errno_or_root_cause_inferred=false remains explicit.
The independently confirmed NFS mount-row fixture contradiction needs a bounded
correction, but cannot be named as this original child's first failed guard.

Preserver-v1 failed with JSONDecodeError at `main:381` → `readiness:303` while
decoding raw private-unit bytes as JSON. Its original protected RESULT is
SHA256 `c594184bae9bb425eac09ff56989e4f73a273e34b6173cde0115966e22c52863`,
35798B, under `/opt/hfcache-web006/source22-native-isolation2-preservation-v1/`.
Only that new owned WORK was created. Fresh v2 evidence joins the original
failed result/channels and confirms all four original rename intents absent;
no original alias/Basic mutation or replay occurred. Strict closure remained
true; the original v1 failure stays false.

Fresh preserver-v2 correctly distinguishes two raw records and12 JSON records.
It holds the original failed isolation/lifecycle and unchanged normal8/fault5
proofs, rechecks current private unit/cgroup and known PID/start drain, then
retains the actual Basic inode118779524 and current symlink61030266,
deployment76316275 and policy76316276 with renameat2/RENAME_NOREPLACE. All four
operations completed rc0 without Basic payload/digest reads, preserving original
metadata/SIDs apart from expected rename ctime. Preserved Basic destination:
`/opt/hfcache-web006/source22-native-isolation2-preservation-v2/preserved-original-ui-administrator.json`.
All four active paths were absent at completion. Original failure flags and
owned_children_reaped=false remain unchanged; separate current private known
handles drained=true is recorded independently. No application/installer,
permission, kernel, service or timer changes were made by preservation.

Frozen projection candidate256ee20b/27476B received independent read-only review
and local parser/child checks. These are source readiness, not an actual mounted
or functional pass. New private publication2/coordinator4 are still being
prepared at this checkpoint. Canonical source22/gate22, native27 normal/postrun
and native fault5 supplemental passes remain unchanged; all old failed results
and original operation handles remain retained. AUTH-08/HOST-01–03 stay pending;
native isolation, rootless33, dedicated/lifecycle, human docs and final strict
gates remain required. Human patch v2 stays unapplied; WEB006 is
in_progress/uncommitted and WEB007–026 pending. The functional ledger is unchanged:
these are diagnostic/preservation records, not new functional acceptance.
Shared API/UI runtime retains pinned UBI10 micro. Production/NAS/installed predecessor interface
untouched; rollout, merge, push and tag remain unauthorized.

### Checkpoint204 — direct shared-mount refusal; isolation3 preserved (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual scoped outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-native-isolation-projection-publication-v2` | 3772060 / 434079367 | Source publication PASS rc0/reaped/gone, 2.1122674020s | `28115a98e33477716ff0c1bef14b950c1e197eac8d5cb207d1b305fa50ac5afd` |
| `web-006-source22-negative-native-v3` | 3772984 / 434117147 | FAILED rc1/reaped/gone, 17.7128619934s | `0c764d966ee0d2f2f9a154a9a0010705e649829293949171a65188664fd3fa16` |
| `web-006-source22-native-isolation-v3-safe-diagnosis-v1` | 3773463 / 434135626 | Read-only collection PASS rc0/reaped/gone, 0.8032892067s | `5a1ce02b0d7e99695a17f270ad44089e9519b056b42e3e9638c8f45700f8bbb2` |
| `web-006-source22-native-isolation3-private-lifecycle-read-v1` | 3774106 / 434160624 | Read-only collection PASS rc0/reaped/gone, 0.8109578686s | `9976e72c8da6de03a3563e5b896aa6ffec1aadd4a04c3701ac2e18605483c811` |
| `web-006-source22-native-isolation3-preservation-v1` | 3775576 / 434221076 | Preservation PASS rc0/reaped/gone, 1.9993482893s | `38ea3b7eee7642c64a1025e8ca26da0c644d34fc223c9f64088201b9e4350837` |

Publication2 created the reviewed new fixed private projection/live proof/entry,
launcher, sudoers and coordinator resources while retaining old sources. It did
not run application/isolation main or establish functional acceptance; kernel
before/after45bb34e8 is unchanged. Original coordinator155341/start35000078 then
returned rc1/reaped in15.5428397791s, stdout0/stderr3023B/SHA256
`21204ae2ae07d14b1a4577e0a9dadf3ae6b77a3d10dff6bdf3c00bdfee6cb5d8`.
The failed collector RESULT remains passed/all-inputs false with RuntimeError,
strict13-role/4-cgroup/5-endpoint closure true. Its protected canonical RESULT is
SHA256 `0056d64684d9513990e9a5e3587457a15898ea5d6b08923575be148d9477f7fe`,
124986B, at `/opt/hfcache-web006/source22-negative-native-v3/RESULT.json`.

Combined collection joins generation `5e59ee4a2fb64882ba6d6ae34dffa328`:
started/stopped/stop-attempted true, paused false and all37 recorded application
PID/start identities freshly gone. Protected generation SHA256
`c85fae26ca619779aee602c683fe2dff840af9d75bc1b5cbfe45846c5cc1cd37`,
38060B. Public RESULT is SHA256
`899aa475d5cc0d67748cae229cea624f621d5cedab1332da1c27cb324e12e06d`,
6064B; stop.json is SHA256
`1d263b75bedf63793486535a7a42e47ab803b8abcc0290c909b9aa720407440e`,
4018B, recording unchanged inputs and all37 gone. Original START155343/
start35000168 rc0, private-proof155519/start35001316 rc1 and STOP155605/
start35001493 rc0 have both EOFs/reap/gone. Private-proof cleanup_unknown and
overall cleanup_unknown remain true, cohort_cleanup_unknown false and
observations_recorded/required_profile_acceptance false.

Lifecycle3 now directly retains the setup child's safe refusal, not a digest
inference: Refused, errno null, frames `owned_setup:474` → `<lambda>:821` →
`project_in_child:265` → `mount_rows:120` → `need:43`. This is the BEFORE
mount-table shared-tag rejection; NFS-row admission and alias bind operations
were not reached. Setup155597/start35001465 records wait_status0/reaped, EOF,
closed descriptor, no late/overflow/broken pipe and310B prefix SHA256
`4a342fcb0bf9328c6def9395979ee03b6ee5271ad9cf1a6f56f09b91375163d0`.
Its private custom unit is currently inactive/dead, cgroup physically absent,
root155594/start35001431 and setup155597 freshly gone. Original lifecycle
owned_children_reaped=false and cleanup uncertainty remain unchanged; separate
current known-handle drain does not rewrite them. Neither these direct frames
nor the earlier static NFS contradiction establish isolation1's original
OSError/errno or isolation2's actual first guard.

Preservation3 held the actual failed results/lifecycle and separate fresh drain,
then retained Basic inode118788486 (root:983, 0640, secret_t), current symlink
61030267, deployment76316274 and policy76316278 with renameat2/RENAME_NOREPLACE,
all rc0/completed. Basic payload/digest was not read. All four active paths were
absent at completion. Original failed flags and recorded private reap=false
remain unchanged; historical normal8/fault5 and strict closure are retained.

The next private3 fixture candidate remains preparation only. It must prove the
trusted setup child is inside a disposable root-unit MNT distinct from the host
and actual helper and owned by initial USER, reject initial unbindable mounts
before effects, strengthen that MNT with recursive PRIVATE before aliases, and
make each new file bind PRIVATE because a shared source can create a shared
bind clone. Preserve strict no-shared/NFS/readonly/identity checks and exact
non-propagation mount-table/delta proofs. Parent must prove the actual helper
MNT and host guarded NFS rows unchanged. No application, policy, permissions,
SELinux or systemd hardening change is proposed; no new private3 cohort has
executed at this checkpoint. New setup evidence remains outside success DTO.

Source22/gate22, native27 normal/postrun and native fault5 supplemental pass
remain unchanged. Original failures/operation handles stay retained. One scoped
failed isolation3 functional ledger entry is added per case; publication,
diagnosis and preservation are not separate functional acceptance entries.
AUTH-08/HOST-01–03 stay pending, as do native isolation, rootless33,
dedicated/lifecycle, human docs and final strict gates. Human patch v2 is
unapplied; WEB006 stays in_progress/uncommitted, WEB007–026 pending. Shared API/UI
runtime retains pinned UBI10 micro. Production/NAS/installed predecessor interface untouched;
rollout, merge, push and tag remain unauthorized.

### Checkpoint205 — publication3 passed; isolation4 START errno remains unavailable (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual scoped outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-native-isolation-projection-publication-v3` | 3779837 / 434398029 | Source publication PASS rc0/reaped/gone, 2.2663252894s | `8dfd3fe9a9450bb15ee1a7581d80e30a8fb2af80d89a992dd260644380b06c60` |
| `web-006-source22-negative-native-v4` | 3780250 / 434413339 | FAILED rc1/reaped/gone, 9.6111971699s | `8c432a6cc0af1c66d26d899b874f94791d4c113a992d2f7feada2f62dbbed965` |
| `web-006-source22-native-isolation-v4-safe-diagnosis-v1` | 3780715 / 434430590 | Read-only collection PASS rc0/reaped/gone, 0.8187910570s | `050f54f7f607c2687c089d35406bdd6264251fcbec8e893a531c1d175cc2de29` |

Publication3 created the six fresh fixed owned resources with old private/shared
sources retained. Inputs rejoined/closed; no application or isolation main ran,
no host-helper policy/permissions/canonical validator changed, and kernel
before/after45bb34e8 is unchanged. This source publication is not acceptance.
The following isolation4 original coordinator155888/start35296274 returned
rc1/reaped in7.2491964930s, stdout0/stderr3257B/SHA256
`05fffaf22725bb2cdb335114b7332329d96604bd8065b38d037368646d36c53a`.
Protected failed collector RESULT at
`/opt/hfcache-web006/source22-negative-native-v4/RESULT.json` is SHA256
`22aa26bb2c17a3d4f2834bad132c992874fbdee46c07b09c7a5c78deb6c1d772`,
128073B. Passed/all-inputs remain false with RuntimeError, original child
failure retained, and strict13-role/4-cgroup/5-endpoint closure true.

The passed combined4 reader clones the previously passed reader and adds only
typed projection of the already-read generation fixed_start_failure. Actual
START155890/start35296373 returned20, STOP156014/start35296875 returned0;
both have actual channel EOFs, original reap/gone, no deadline/overflow/signals
or replay. START retained71B stderr/SHA256
`56d36dd18964014bd15c8ffd6bed6f3cbf886afd8fd8cfc8ea5db6826e301a1c`,
a fixed generic footer with no recognized frames/classes/errno. No private-proof
launcher was invoked. Original generation fixed_start_failure records OSError,
frames `main:1848` → `start:1138` → `secret_label_gate:810` →
`secret_kernel_marker:359`: the BEFORE gate opens SELinux policy. The original
errno was not retained. Current read-only simultaneous-open behavior does not
establish this original cause. No private3 namespace-preparation code ran;
its candidate remains unaccepted and no regression is established by this run.

Generation `457300722bc848df85fe9afe9f4ee375` has started/stopped/stop-attempted
true, paused false, and all18 recorded application PID/start identities freshly
gone. Protected generation SHA256
`f514eccd5d1006760741a3491f27951802f03e1131f121b78e8cb0fce8b1db0b`,
18188B. Owned public RESULT SHA256
`2b644ff949dd948a5c1073302d72bbfdafa08cb2e4cb3b9a470b85f1bfe5207b`,
4098B; public stop SHA256
`a1ce801db51f54a2a8ada56eef7b5f069234aa10c7a723d1c5edc3ecb9b32dfd`,
2422B, records unchanged inputs and all18 gone. Original failure_stage=start,
observations_recorded/required_profile_acceptance false,
private_proof_cleanup_unknown false, cohort_cleanup_unknown/cleanup_unknown true
remain unchanged. Fresh drain evidence does not rewrite original uncertainty.

Basic inode118788082, current symlink61030271, deployment76316128 and
policy76316129 were observed present metadata-only; no Basic payload/hash read.
Environment preparation of a separate failed4 guarded preserver is pending.
An explicit pinned native-only observer adapter is being designed to call the
unchanged controller.main exactly once and retain numeric errno separately.
It must not retry, monkeypatch methods, change policy/permissions/hardening or
runtime source. No observer execution/acceptance or actual errno is claimed
at this checkpoint. Original failures and operation handles remain retained.

Source22/gate22, native27 normal/postrun and native fault5 supplemental passes
remain unchanged. One scoped failed isolation4 functional ledger entry per case
records the actual run; publication/diagnosis are not functional acceptance
entries. AUTH-08/HOST-01–03 stay pending, as do native isolation, rootless33,
dedicated/lifecycle, human docs and final strict gates. Human patch v2 remains
unapplied; WEB006 in_progress/uncommitted, WEB007–026 pending. Shared API/UI keeps
pinned UBI10 micro behind existing Caddy. Production/NAS/installed predecessor interface untouched;
rollout, merge, push and tag remain unauthorized.

### Checkpoint206 — original isolation5 PID1 fixture refusal; private4 published (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual scoped outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-native-isolation4-preservation-v1` | 3782499 / 434505548 | Preservation PASS rc0/reaped/gone, 1.9295549104s | `90232a7123da4a37f777cdb64179b46d9c4265fc7a513bfec88026c708f1605d` |
| `web-006-source22-native-controller33-observer-publication-v1` | 3785178 / 434608961 | Source publication PASS rc0/reaped/gone, 1.9033260001s | `3d4df075364e704834daa2d64dfa38e316cea2b39e345b0c15853c16e4dfe331` |
| `web-006-source22-native-isolation-coordinator-publication-v6` | 3786081 / 434635202 | Source publication PASS rc0/reaped/gone, 2.0699111642s | `601e5451340cf1ec2a336442135fc8b92325730e649edabd7bfbecf71ac45f56` |
| `web-006-source22-negative-native-v5` | 3786240 / 434638312 | FAILED rc1/reaped/gone, 18.2118312912s | `2e1738c5b4d5a4e5e21211e80820f5defea9d1ef21f19cef30528bc6e7a083e3` |
| `web-006-source22-native-isolation-v5-safe-diagnosis-v1` | 3786495 / 434645971 | Read-only collection PASS rc0/reaped/gone, 0.7951557096s | `ce15d6f3ebf8b18d1f00ce09ee51cc1def55b4c080b9f233990781fcdfcc679d` |
| `web-006-source22-native-isolation5-private-lifecycle-read-v1` | 3787177 / 434667256 | Read-only collection PASS rc0/reaped/gone, 0.8406583499s | `08d2ed8d7ad25df7245d0c1e8f3f9eea05bd95b89f51d824cd44f77ea11ccc24` |
| `web-006-source22-native-isolation5-preservation-v1` | 3787405 / 434673792 | Preservation PASS rc0/reaped/gone, 2.1138132745s | `01bcca70aa6aad4278b9cb98a26ba3daf3678079ee058fcb9327828c4eab6cec` |
| `web-006-source22-native-isolation-projection-publication-v4` | 3787879 / 434687004 | Source publication PASS rc0/reaped/gone, 2.1836988712s | `e9b6d0738770e3fdb67e5f97b549098ec78a8b94133308821ff387d23509dc02` |

Preservation4 retained the original failed4 Basic inode118788082 and three aliases
metadata-only/NOREPLACE with active paths absent and original failure flags
unchanged. Observer publication then installed the explicit fixed native-only
adapter source7c1d60d9/11077B, launcher69b9522d/165B and fixed sudoers, plus an
empty root0700 records directory whose child entries are expected to change.
No controller, observer or application main was executed by publication.
Protected observer publication RESULT is SHA256
`9fba9780b3f0c90627ee659a3f8b4beddd8c7fe3efd7e92ab2e3e1f6fe4d670b`,
58604B. The adapter executes the exact unchanged controller13d9 full footer
once with native argv and preserves the same original exit; separate direct
exception-context class/frames/errno retention does not read/hash stdin or
monkeypatch controller methods. No original isolation4 errno was recovered by
publication or retroactively inferred.

Coordinator6 publication created only a fresh fixed coordinator, source297bd123/
28610B, with native observer wiring and unchanged private3 proof. Its protected
RESULT is SHA256
`dedb17c21795e4832350b4ef8b72843cc3d9a616d1ad96fefc72f468be0e2461`,
63768B. Old sources/coordinator5 and receipts were held unchanged; no application
or isolation main ran and kernel45bb34e8 stayed unchanged.

Native isolation5's original coordinator156346/start35521244 returned rc1/reaped
in15.8473515210s, stdout0/stderr3023B/SHA256
`6ab9a45c8a5d38a4f6ddac08a88f5752de02af85436d7230e7c3a3eeb52bc243`.
Protected failed collector RESULT is SHA256
`8e04dec3d87285238e82b9341ec0d811c4a545dd1f0795804afb385972229fbe`,
130870B, with passed/all-inputs false, RuntimeError and strict fixed-role closure
true. START156348/start35521333 rc0, private-proof156523/start35522518 rc1 and
STOP156608/start35522695 rc0 reached EOF/reap/gone. Combined5 directly retains
ValueError frames ending `perform:905` → `_owned_projection_setup:823` →
`_projection_parent_snapshot:798` → `pair:290` → `proc_start:276` → `need:82`.
The parent fixture called unchanged controller.pair(1), while that generic helper
requires pid>1. This is a concrete fixture call-site incompatibility before
setup, not a namespace operation failure or a reason to change the generic guard.

Generation `5cf5ddae35c94fca91bdcf35123db590` is started/stopped, all37 recorded
application handles freshly gone, with unchanged public-stop inputs. Protected
generation SHA256
`5693a48bf4f242fc22091cf0a91ce84e885095c5c9975311854061c5f047cdb8`,
38060B. Lifecycle5 has setup_records=[] and proves no setup child was created
before the PID1 parent guard. The original private worker156598/start35522635
is currently gone; its custom unit is inactive/dead and cgroup absent/empty.
Original owned_children_reaped=false, cleanup_unknown/private-proof-unknown=true,
cohort_cleanup_unknown=false and observations_recorded=false remain unchanged.
No original startup errno or earlier first cause is inferred.

Preservation5 held those original failures/lifecycle and separate current drain,
then retained actual Basic118779525 and three aliases metadata-only with
NOREPLACE, all four active paths absent at completion. Basic payload/hash was
not read. Protected preservation RESULT is SHA256
`30b045dba77229cc0f721c26697da88efe258e615e5df88fb39db9ef3f4b9010`,
75807B. Original failure/cleanup flags and no-setup fact remain unchanged.

Private4 source publication added a fixed, bounded `/proc/1/stat` helper
permitting start_ticks>=0 and replaced exactly two controller.pair(1) calls in
the parent snapshot. Generic PID/role/auth/runtime/namespace checks remain
unchanged. Published source pins are projection ebb783d0/38603B (byte-identical),
live c6d19ab6/60102B, entry c49c2993/5033B, wrapper39361b5a/206B,
sudoers75cad6ed/236B and coordinator7e1230b9b/28610B. The six resources are fresh;
all old private3/source/observer/coordinator6 artifacts remain held unchanged.
Protected private4 publication RESULT is SHA256
`1cd3205e21be0c6c1047db32f3dbf6a3501ad97485e16d78186b3c922ec843fd`,
79430B. Publication did not execute application/isolation main or establish
functional acceptance. Private4 remains unaccepted; native6 collector is bound
and its next result has not been observed at this checkpoint.

Source22/gate22, native27 normal/postrun and native fault5 supplemental passes
remain unchanged. One scoped failed isolation5 functional ledger entry is added
per case; publication, diagnosis and preservation are not functional entries.
AUTH-08/HOST-01–03 stay pending, as do native isolation, rootless33,
dedicated/lifecycle, human docs and final strict gates. Human patch v2 remains
unapplied; WEB006 in_progress/uncommitted, WEB007–026 pending. Shared API/UI keeps
pinned UBI10 micro behind existing Caddy. Production/NAS/installed predecessor interface untouched;
rollout, merge, push and tag remain unauthorized.

### Checkpoint207 — original isolation6 bind errno22; current state preserved (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual scoped outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-negative-native-v6` | 3788112 / 434691704 | FAILED rc1/reaped/gone, 18.4707342703s | `749baeeb6a6297608a0248c69bb4c1de41518ba5d022d68a5b7952da3a2f911c` |
| `web-006-source22-native-isolation-v6-safe-diagnosis-v1` | 3788360 / 434698706 | Read-only collection PASS rc0/reaped/gone, 0.8227964668s | `a372040a68d8489158ef2d017726ab48fa4dd119db3d01047eec3d233ef28c47` |
| `web-006-source22-native-isolation6-private-lifecycle-read-v1` | 3788747 / 434709738 | Read-only collection PASS rc0/reaped/gone, 0.8210531892s | `35cc95e807f85a6c61556e10f28df87b28a3752b1a2f09d1926fa1a922619929` |
| `web-006-source22-native-isolation6-preservation-v1` | 3789410 / 434732189 | Preservation PASS rc0/reaped/gone, 1.9557865709s | `5fbd8dad778f697f7b6184ee3e30485b55e86c3b10ccc858be990208221216a1` |
| `web-006-source22-native-isolation6-propagation-adjunct-read-v1` | 3789799 / 434745826 | Read-only metadata PASS rc0/reaped/gone, 0.7817066330s | `7e5f558be91ea716a4d0ee71dafc875e75b9f6149f848ebf358408124d4f2525` |

Native isolation6 is one actual failed functional execution. Its original
coordinator156844/start35574621 returned rc1/reaped in16.2773431330s,
stdout0/stderr3023B/SHA256
`5b8ab22323538fcc396a30cc943e069682f3b03961194e4384636fe74505b4c1`.
Protected failed collector RESULT at
`/opt/hfcache-web006/source22-negative-native-v6/RESULT.json` is SHA256
`2a2e4b638dcec4a4bf098d7857cdcb8e1eede64f42f75ff784cbf751a002f522`,
134299B. Passed/all-inputs remain false with RuntimeError and the original
child failure retained; strict13-role/4-cgroup/5-endpoint closure is true.

Combined6 records START156846/start35574731 rc0, private-proof157021/
start35575913 rc1 and STOP157107/start35576103 rc0, all original EOF/reap/gone
without deadline, overflow, signal or replay. Generation
`b211d8dc47c64d198eb82203933fcf79` is started/stopped/stop-attempted, paused false,
with all37 application PID/start identities freshly gone. Protected generation
SHA256 `bd0a6005f7204b812f249eb153ae3f64a3ac77782e1ebefe24697ea656012b42`,
38060B; public RESULT SHA256
`85b9ee5db05967936e8ace4d05c00647925192718ed61c9ed3dbbddded171846`,
6060B; public stop SHA256
`c59165299b62b27b8cf1c34175e45b5a935cb041d55846cc66844aac2ff00854`,
4018B, retains unchanged inputs and all37 gone.

The read-only lifecycle reader holds original LIFECYCLE SHA256
`50d4408bc46972c9d03ba5b9b74d5c10bca94c69750dd6554ef862ce0d62eb25`,
10132B. Its one setup record directly retains OSError errno22, frames
`owned_setup:579` → `<lambda>:840` → `project_in_child:376` → `mount_call:238`.
This is the first MS_BIND call, not an inferred error from stderr/digest.
Original worker157096/start35576040 and setup157099/start35576075 are freshly
gone. Setup wait_status0/reaped/EOF/descriptor-closed are true; its refusal DTO
is not worker success. The custom unit is inactive/dead and its cgroup absent.
Original owned_children_reaped=false remains unchanged. Separate current known
private-handle drain is true. Public cleanup_unknown/private-proof-unknown=true,
cohort_cleanup_unknown=false, observations_recorded/required_profile_acceptance
false and failure_stage=private-proof remain unchanged.

A separate read-only adjunct holds the same complete lifecycle and projects only
closed metadata. It confirms stage=alias_bind, active_alias=source-basic,
recursive_private_completed=true, all_nonpropagation_fields_unchanged=true,
alias_splits_count=0 and final_strict_no_shared=false. No alias bind completed.
All six outside host/parent/API/worker/Caddy/helper mount-table hashes and full
before/after boundary records are equal; boundary.unchanged=true. The12 required
denial cases were not executed. Private4 remains unaccepted; this fixture failure
does not establish a product isolation failure or alter canonical guards.

Preservation6 holds the original full lifecycle and compares the setup core,
excluding exactly the two explicitly omitted metadata fields. It brackets fresh
worker/setup/unit/cgroup drain, then retains actual Basic inode118788497 and
three aliases using metadata-only NOREPLACE. All four active paths are absent;
no Basic payload or digest was read. Protected preservation RESULT SHA256
`65e3344f43d50a609a69b1efbad2aa334b922656f9bac54e762a01d4351ddcaf`,
76819B, preserves the original false/unknown flags and old operation handles.
All inputs rejoined/closed; no application/installer/security changes occurred.

A detached-clone fixture5 remains design/preparation only. No new publication,
cohort or denial acceptance is claimed here. Source22/gate22, native27
normal/postrun and native fault5 supplemental passes are unchanged. Exactly one
scoped failed isolation6 functional ledger entry is added per required case;
diagnosis, adjunct and preservation are not functional executions. AUTH-08/
HOST-01–03 remain pending, with native isolation, rootless33, dedicated/lifecycle,
human documentation and final strict gates required. Human patch v2 is unapplied;
WEB006 remains in_progress/uncommitted and WEB007–026 pending. Shared API/UI
continues on pinned UBI10 micro behind existing Caddy. Production/NAS/live
historical frontend are untouched; rollout, merge, push and tag remain unauthorized.

### Checkpoint208 — detached import reaches NFS formatter guard; state preserved (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual scoped outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-private5-detached-kernel-preflight-v2` | 3792292 / 434838853 | Kernel mechanics PASS rc0/reaped/gone, 0.8589288974s | `23ae13ad684ce796b04d1dcde4cf8974997753e2640178b4670eecf27986a119` |
| `web-006-source22-native-isolation-projection-publication-v5` | 3793654 / 434886772 | Source publication PASS rc0/reaped/gone, 2.3186452510s | `ce1a8a07a14198c1c8f0a5e1d7b75cb3b41c5b37b18b1dcc7cf4aef1b2b63692` |
| `web-006-source22-negative-native-v7` | 3794385 / 434912479 | FAILED rc1/reaped/gone, 18.5877615092s | `8622375bf635fd36a7f550b7853973300c6a64102f89400ca85cc8a78c451188` |
| `web-006-source22-native-isolation-v7-safe-diagnosis-v1` | 3794603 / 434920454 | Read-only collection PASS rc0/reaped/gone, 0.8062011218s | `6fb7d0e5ddc6c7d6c720cf2c9a0411cec7cf7c8bd81e90852fe4cb2e01ea6dda` |
| `web-006-source22-native-isolation7-private-lifecycle-read-v1` | 3795149 / 434939236 | Read-only collection PASS rc0/reaped/gone, 0.8287304556s | `0c7c2e611ebb13efcbddddb312e90afdf5af1d49c617773e5564c687b26dfb40` |
| `web-006-source22-private5-detached-kernel-preflight-v3` | 3795890 / 434965885 | Owned-NFS metadata mechanics PASS rc0/reaped/gone, 0.8696506033s | `006d484e2be7b9336856fb16951638f318efc81e79dfe70dd3d5eee369aa2247` |
| `web-006-source22-native-isolation7-preservation-v1` | 3796203 / 434971676 | Preservation PASS rc0/reaped/gone, 2.0433141906s | `f153780a2cf20369dbea052e2ec7cc06b9a4b8f9e8ac0428b28d88684647e6d6` |
| `web-006-source22-native-isolation-projection-publication-v6` | 3796805 / 434989959 | Source publication PASS rc0/reaped/gone, 2.3090397259s | `8d8bab256c266fd376330d50a76cc53ee01962ee7aaabd3f03f155d5446ae1fc` |

The first synthetic prototype caller SHA256
`eb2ee4e62e4a4f4c984e4a4c1b703dc8089247c74adb48588ab9f5b60117bcce`,
69956B, was built but never executed. A missing exact sha helper was caught in
host-only dependency checks before guest execution. The agent temporarily edited
source1 after caller capture, then restored its bytes to captured SHA256
`fb5220dc9288bf22fbffa07cd5b5980776d63e53afc686e7c6f1b244eb3b4eec`,
30332B; local file metadata changed. The original caller is retained as never
executed. A fresh v2 actor/WORK/caller was used instead; no
failed guest run, operation replay or functional ledger entry is invented.

Actual synthetic prototype2 has child157333/start35721664 rc0/reaped/gone,
stdout1032B and empty stderr, both EOF/closed, no deadline/overflow/signals/replay.
Two fresh child-private mount namespaces and a retained first-namespace FD prove
legacy foreign O_PATH bind errno22, followed by open_tree clone/mount_setattr/
move_mount success with exact inode/SID and RO/nosuid/nodev/noexec flags.
Host/parent mount-table hashes remain unchanged. Protected RESULT SHA256
`fe032c165678a8521a60decc3303a566a2b068b638da65ebb0e1518a7afd66b4`,
4778B. This uses only two owned empty synthetic files and proves kernel mechanics,
not protected-object, application or denial acceptance.

Private5 source publication held those actual mechanics and old failures, then
published only fresh fixture resources. Protected RESULT SHA256
`658fae2cc16d029f8ad1d1f2c3b4c4816924d162a632631bc8bc3408984c2eeb`,
86100B. Source5 pins are projectiond865ddf9/51814B, live5323b8ef/60994B and
entry241cf55c/5033B; original runtime/controller13d9/policy/permissions are
unchanged. No app/isolation main ran in publication. Source-only review initially
suggested descriptor pressure; exact recount found only20 added prelaunch FDs,
so no cache, descriptor-limit increase or guard relaxation was introduced.

Native isolation7 is one actual failed functional execution. Its original
coordinator157449/start35795398 returned rc1/reaped in16.3069857310s,
stdout0/stderr3023B/SHA256
`fbed44da1197a9b177c599484851e2099b272d05444200c9168f01c9aeaf9507`.
Actual prelaunch descriptor usage is934, soft1024/hard524288 unchanged; the
original used+64<soft fail-closed guard passed. Protected failed collector RESULT
SHA256 `b9af3e365b90de3fa5c9aec064cb2a9833d4427b524c53d4bc83977428049c11`,
137721B, retains RuntimeError/passed=false/all-inputs=false and strict fixed-role
closure true. START157451/start35795486 rc0, private-proof157627/start35796697
rc1 and STOP157712/start35796883 rc0 all have original EOF/reap/gone.

Generation `0d6156c4c0db487dbf4cb6a990a2c372` is started/stopped with all36
application PID/start identities freshly gone and unchanged stop inputs.
Generation SHA256
`03861e3aa21c1d24f99d20d797f531b3cc46852f84cfc1f13efdaa1fa1bf3998`,
38708B; public RESULT SHA256
`039f24029b60e2fe0b85c9bff16eac37ffb9b4e70bfda98be38a091035759638`,
6066B; public stop SHA256
`0fef48d91005d95b5b6c96201f929d8b3e8276ce2a15fb527e249ef86173bec4`,
3934B. Original private worker157702/start35796817 and setup157705/
start35796854 are freshly gone; setup wait0/EOF/descriptor-closed/reaped,
custom unit inactive/dead and cgroup absent. Separate current drain is true.

Lifecycle7 holds original LIFECYCLE SHA256
`2aa02431cb9ec451167de5d504de8c46ccebba488341ee239b44211269490c81`,
19895B. Its safe refusal is Refused/errno=null, frames `owned_setup:730` →
`<lambda>:840` → `project_in_child:531` → `_prepare_private_alias:312` →
`_preparation_rows:276` → `need:47`. Actual BEFORE aliases are11 unique fixed
names matching capture groups. All11 detached clones were prepared with private/
readonly attrs and closed; nine parent-owned aliases attached before the archive
NFS row guard refused. API delivered-writer and Caddy delivered-tls-key remained
unattached. Import stage=attach, original_metadata_verified_before=true,
all_clones_prepared_before_attach/all_clone_fds_closed=true, but
original_metadata_rejoined_after=false remain exactly as recorded. Propagation
stage=alias_bind/active_alias=archive-sentinel, recursive PRIVATE completed,
nonpropagation fields unchanged, final_strict_no_shared=false. These partial
facts do not establish all alias verification or any of the12 required denials.
Original owned_children_reaped=false, cleanup_unknown/private-proof-unknown=true,
cohort_cleanup_unknown=false, observations_recorded/required_profile_acceptance
false remain unchanged; private5 is unaccepted.

Owned-loopback NFS prototype3 opens only the fixed sentinel O_PATH with actual
full9 dev58/inode118335703/nfs_t and no payload read/hash. Its child157841/
start35848691 rc0/reaped/gone has both EOFs/closed descriptors, no deadline/
overflow/signals/replay; original proof FDs close and host/parent tables match.
The exact alias mount has device `0:58`, root `/`, filesystem `nfs4`, source
`127.0.0.1:/WEB006_OWNED_SENTINEL`, options
`ro,nosuid,nodev,noexec,relatime` and no optional propagation fields.
Superoptions remain the exact owned-loopback host NFS superoptions, including
vers4.2/clientaddr127.0.0.1/addr127.0.0.1. Protected prototype RESULT SHA256
`377c688924846d70faaa83a263bc4aeda32ac80e4bee7e062102702c38456a14`,
5086B. This confirms the fixture's root/source formatter assumption is wrong;
it does not execute workers/denials or change canonical mount/security contracts.

Preservation7 holds the full original lifecycle and compares setup core while
omitting exactly three explicitly projected metadata fields. It preserves the
original false/unknown import/reap/cleanup flags beside fresh drain, then retains
Basic inode118788083 and three aliases metadata-only using NOREPLACE. Current
four paths are absent; no Basic payload/hash read or application start occurred.
Protected RESULT SHA256
`defde8bf2f25c78994a9534a79971ce7dac527d036d65337973e18827d2581f9`,
81039B. Original source/prototype1/caller, failures and handles remain retained.

Source6's narrow formatter row-map publication6 ACTUALLY PASSED in2.3090397259s,
original3796805/start434989959 rc0/reaped/gone. Protected RESULT SHA256
`4baae33c39078e2c6e69ee01c48f70d731f2e9a3706162b8b966885fb13f2b4d`,
92770B. Fresh projection0a85f66e/51839B, liveddfacddd/60994B and
entryc3eeadf8/5033B preserve old files and original failures. No application or
isolation main ran; policy, permission and runtime contracts remain unchanged.
Publication establishes no feature acceptance. Native8 original3797028/
start434994051 is running under collector12 source15befb81/103235B; no observed
outcome, successful denial or functional ledger entry is inferred. Source22/
gate22, native27 normal/postrun and native fault5 supplemental passes stand;
exactly one failed native7 functional ledger entry is appended per required case.
Prototypes, publication, read-only diagnosis and preservation are not functional
runs. AUTH-08/HOST-01–03 remain pending with native isolation, rootless33,
dedicated/lifecycle, human docs and final strict gates required. Human patch v2
remains unapplied; WEB006 in_progress/uncommitted, WEB007–026 pending. Actual
pinned UBI10 micro/shared-Caddy audit stands. Production/NAS/installed predecessor interface are
untouched; rollout, merge, push and tag remain unauthorized.

### Checkpoint209 — original native8 isolation revalidated; final native preservation passed (2026-10-24)

| Actual local result stem under `.scratch/` | Original outer PID / start | Actual scoped outcome | Local result SHA256 |
| --- | --- | --- | --- |
| `web-006-source22-negative-native-v8` | 3797028 / 434994051 | Outer FAILED; original cohort rc0; rc1/reaped/gone, 22.9467380410s | `0ad81ee27c9b269d8d3dd62d8775f7d2d9387a652f534e84ee054121e7b55cd9` |
| `web-006-source22-native-isolation8-case-phases-read-v1` | 3797904 / 435022769 | Read-only DTO collection PASS; rc0/reaped/gone, 0.7954975646s | `f01945c64affbc36f9269c22acfebe090b6bc0b79116c922595fa53f4cddc518` |
| `web-006-source22-native8-revalidation-v1` | 3799225 / 435070987 | Full read-only original-proof revalidation PASS; rc0/reaped/gone, 2.8478538794s | `6ce0106d7a3164528ee07efe16c5f3db76071e75682fd2b923ed69449dfa479c` |
| `web-006-source22-native27-final-preservation-v3` | 3799556 / 435081556 | Final BOTH native preservation PASS; rc0/reaped/gone, 1.8076734515s | `10e6b434baf46a81e539f672bb56b51a2d1c77a1ee4e4e873161fb5083099bad` |

Native8 is one actual functional cohort, whose original runner157986/
start35876980 returned rc0/reaped in20.2616905460s, stdout66B/SHA256
`16bc0faefc11f314280404574d8ae3d2363d03c0342cf162df50bd1996538c8f`,
stderr0. All four original launcher phases returned0 with both channel EOFs,
no overflow/deadline/signals/replay and exact original identities gone:
START157988/start35877112, private-proof158165/start35878299,
INSPECT158254/start35878527 and STOP158313/start35878784.
Prelaunch FD usage954/soft1024/hard524288 leaves the unchanged reserve guard;
no cache or descriptor-limit change occurred.

The outer collector returned1 only at `validate_isolation:478` → `need:30`,
after collecting all original positive preparation/import/generation proof. Its
fixed three-phase set and count12 expectation disagrees with the pinned source's
conditional Caddy admission and per-alias observations. Original protected RESULT
SHA256 `51344cebb3eac6a21e9c887766641a008d49142f1d30aa934b98351b86b36642`,
242239B, retains passed=false/all-inputs=false/ValueError unchanged. Its source,
operation handles and failed outer execution are not overwritten or replayed.

The actual DTO reader holds original observed SHA256
`b994cc431a7b8001aa17c0dfa22ebf5877b83804813f61555ae94ec2deb01e7b`,
10054B, and original INPUT SHA256
`d32b39a981a0748a3e1f97ddc531351c13ed07f0e6ed20e0dc6aaa41c3ad3b75`,
5694B. It preserves repeated credential-category observations. Actual fixed
source admission yields the following exact19 attempted/denied case rows:

| Actual phase | Credential | Hub state | Archive | Attachment | Total |
| --- | --- | --- | --- | --- | --- |
| root | 9 | 0 | 1 | 1 | 11 |
| account | 5 | 1 | 1 | 1 | 8 |

The original delivered TLS source has UID/GID0:0/mode0440, so the pinned
ordinary-read/admitted_phases grammar does not admit Caddy-owner982. No Caddy
phase or four-category-per-phase requirement is invented. Each attachment case
retains the original three syscall denial checks; the count is per source case
observation, not a new command/run count.

Fresh full read-only revalidation holds the original failed collector and
rejoins all original authority/controller/control/manifest/old264-prefix,
readonly108-package/public sources, native27 normal8, fault5, selected private6
resources and all original positive four-phase/private/stop evidence. It executes
no launcher, retries no operation, and creates only its separate evidence WORK.
Pinned objects SHA256
`4839ecf2c8b95b938665a1181c762c5c26d2b8de79580953f4e2fba96891fe03`
independently recomputes admitted_phases from every actual INPUT alias metadata.
The exact Counter includes all alias multiplicities and one attachment per
required phase; expected and observed seven-row counts match19, every actual
attempt/denial true. There is no arbitrary minimum/count-only relaxation.

Protected read-only revalidation RESULT at
`/opt/hfcache-web006/source22-negative-native-v8-revalidation-v1/RESULT.json`
is SHA256
`d48988b8b0129c640a14695bf9bf6affa2f8193999d2477bf3966fd2a362b788`,
257263B. It passes with all local/guest inputs rejoined/closed and strict closure,
while explicitly retaining original_collector_passed=false and
original_operations_replayed=false. Native isolation evidence is accepted from
this original-run/read-only pair; the original outer result remains failed.

Generation `967763173c3b4125a1d8fc0512b8bb9b` is stopped with all47 original
PID/start identities gone. Generation SHA256
`23246efcdcfc356284f631020b30017640ba12fa594beedfca4d8d97fedd0efe`,
49756B; original public RESULT SHA256
`a533d91205061d4a9bd1d56922672c82c162fa09b5bbdf6e3733d85959d2a278`,
8000B. Private setup158243/start35878460 has wait0/reaped/EOF/descriptor-closed;
its actual setup/import stage is complete. All11 source clones have exact full9/
SID, private+readonly flags, attachment/reopened-alias checks and FD closure.
Import peak32 descriptors from before19 under soft1024/hard524288 unchanged.
All11 private alias splits and all six outside host/parent/API/worker/Caddy/helper
mount tables are verified unchanged; strict no-shared and final source rejoin
pass. Original public observations_recorded=true and all cleanup-unknown flags
false are measured success, distinct from earlier retained failed generations.

Final BOTH native preservation v3 holds exact six PINS: native27 postrun,
native27 functional, control33, this read-only isolation proof, fault5 and final
isolation. Its pure binder and guest guard independently enforce the actual
19-row phase-counter contract, original collector false/no replay and exact
source/input pins, plus original successful runner, generation/stop/key/Basic/
alias checks. It retains historical normal8/fault5 unchanged, then preserves
actual Basic inode118788084 and three native aliases metadata-only/NOREPLACE.
All four current paths are absent; no Basic payload/hash or app/installer start.
Protected preservation RESULT SHA256
`a32b6c249457e83ab0635f71da4fa46d67379cedaa81d243daf24ec6542287f9`,
65424B, all inputs rejoined/closed/strict closure true. It is preservation evidence,
not an additional functional cohort.

Exactly one original native8 functional ledger entry is added per required case,
with its actual outer exit1 retained and the later full read-only acceptance pair
identified in the assertion. DTO/revalidation/preservation do not add functional
runs. AUTH-08/HOST-01–03 remain globally pending for required rootless33 and
lifecycle work, human documentation and final strict gates. Rootless33 baseline
is next, without an inferred outcome. WEB006 remains in_progress/uncommitted;
WEB007–026 pending, source22/gate22/native27/fault5 stable. Human patch v2 is
unapplied and the actual pinned UBI10 micro/shared-Caddy audit stands. Production/
NAS/installed predecessor interface are untouched; rollout, merge, push and tag remain unauthorized.

### Checkpoint210 — rootless33 starts, then trusted baseline refuses unavailable host status (2026-10-24)

The first source22/rootless33 normal cohort ACTUALLY FAILED: outer3800116/
start435096763 rc1/reaped/gone84.499981s; original runner158556/start35979620
rc1/reaped82.814934s, checker158560/start35979648 rc1/reaped82.300211s.
Original protected coordinator RESULT SHA256
`865f296ee9bf3bc4b92ba53aa21e1d680b8e11296edf2173d845f08e3ad00331`,
68006B, retains passed/all-inputs/original-functional false. Ownership/ARMED and
all-source closure succeeded; no secret retirement or recovery replay occurred.
Baseline had independently passed with zero secrets; its protected RESULT is
`c753cd7257d07061874fdb230022484105422df10b0d04467b58f5495a30a5c6`,
19616B (compact sorted JSON serialization).

Read-only original startup collection PASSED0.784164s: initial cohort ready,
both label gates passed, final bootstrap HTTP200 with correct assets/instance.
It corrects the initial startup-failure hypothesis. Three-browser untrusted TLS
refusal passed; each trusted engine launched and closed normally, navigated the
built Administration UI through real Caddy and received host-status HTTP200.
The producer-redacted diagnostic independently read in0.763668s is the same for
all three engines: actual state `unavailable`, expected `supported`. Each engine
has infrastructure_failed=true and zero case rows; no host assertions are claimed
as passed. Original trusted report SHA256
`cb835de3bbfed46307708963befcca15cee6b929ae1f26b4396578244b23849a`,
67912B. The earlier stop reader looked for browser-available names; those absence
flags were a diagnostic filename error, corrected by the baseline-name reader.
No original report, runner result, false flag or handle was overwritten.

Generation `895df0bbb7ca447d9c7f76a2df4d4b1b` is stopped; the passed read-only
stop collection0.878618s proves all69 original PID/start pairs gone and each of
three exact application CIDs has original wait0/exists1, exited0/PID0 and complete
observer drain. Generation SHA256
`1b4097f8b71a33d9b5c9eaa2087b3fc85722b08328ee3815241b908df7997572`,
73359B. Original watcher/runner are gone. The six exact owned Podman secret IDs
remain retained; current Basic inode118788498 UID/GID983:983/mode0400 and three
selection aliases remain present. Key inode78157344 is unchanged metadata-only.
No fresh cohort is authorized by this drain alone: exact-ID nonforce retirement,
opaque backup/intents and four-path NOREPLACE preservation are still required.

Two bounded read-only AVC collections ACTUALLY PASSED0.850760s and0.835211s,
outer3806220/start435311960 and3806549/start435318528, both rc0/reaped/gone.
They read only the owned guest's bounded audit window1792882390–1792882510,
exporting no raw log or credential payload/hash. Seven enforcing denials show
helper_t write to user_tmp_t sock_file, name `private`, tmpfs inode17. Fixed
observer `_show` runs before container checks. Upstream systemd257's BUS_MANAGER
path bypasses DBUS_SESSION_BUS_ADDRESS for local `systemctl --user show`; its
explicit SYSTEMCTL_FORCE_BUS flag selects the existing fixed session bus.
Exact fixed-endpoint metadata/expected label confirmation and a narrow source
fix are in progress; there is no broad user_tmp_t socket allow or SELinux change.
These diagnostics are stdout-only local receipts, not protected RESULT pins or
new functional cohorts. All original failed evidence remains retained.

Source22/gate22/native27/fault5/native8 revalidation and pinned UBI10 micro audit
remain historical measured passes. Human documentation patch v2 is unapplied.
AUTH-08/HOST-01–03 remain pending; WEB006 is uncommitted and WEB007–026 pending.
Production/NAS/installed predecessor interface are untouched; rollout/merge/push/tag unauthorized.

### Checkpoint211 — failed33 preserved; narrow source23 transport correction under strict gate (2026-10-24)

The metadata-only endpoint collection ACTUALLY PASSED0.843574s, original3807963/
start435353305 rc0/reaped/gone. `/run/user/983/bus` is dev45/inode18,
UID/GID983, session_dbusd_tmp_t and exactly matches libselinux matchpathcon.
`/run/user/983/systemd/private` is dev45/inode17, UID/GID983, user_tmp_t,
matching the seven original enforcing AVCs. Its vendor context lookup returns
ENOENT; this is retained and is not evidence of mislabeling. No socket connection,
payload read, relabel or policy change occurred. Systemd257's fixed manager
transport behavior plus these actual facts justify selecting the existing bus.

Initial cleanup1 ACTUALLY FAILED before any retirement: outer3807545/
start435343878 rc1/reaped/gone1.165480s, protected RESULT
`3a371ff5c4a98252d7feaea5ae2647e37b5b9dbeee13f5e25bf07dd7a0b5f370`,
19609B. A new guard compared ARMED's PID/start watcher record to the coordinator's
larger record containing code hashes. Actual identities match; removals=[] and no
backup/removal intent exists. Original false receipt and directory remain held.
Fresh cleanup2 projects the exact PID/start pair and separately joins the watcher
source SHA, holds cleanup1/no-effects evidence and retains all other ownership,
timestamps, drain, backup and exact-ID checks. It ACTUALLY PASSED5.602566s,
outer3808154/start435357628 rc0/reaped/gone. All six original exact IDs were
removed once, nonforce, after durable opaque whole-store backup and individual
intents; each returned0 and was reaped, shrinking listings matched exactly.
Final secret count0/unknown0, complete safe traversal and strict closure pass.
Protected RESULT `56e244f5173417e0faacf0a9b35577b3de6c02a8862cac4d5cf0ce2a5a166ecd`,
120568B. Cleanup does not promote the failed rootless functional result.

Subsequent four-path preservation ACTUALLY PASSED1.901975s, outer3808326/
start435360837 rc0/reaped/gone. It holds the failed original cohort, stopped
69-handle generation, successful cleanup and key metadata, then retains original
Basic983:9830400 and three selection aliases using unchanged NOREPLACE helpers.
Current four paths are absent; secret count0 and all fixed roles quiescent.
Protected RESULT `9fb5529765788d1428c71b21dee6d302af6de692ef7300bf382f34a63d08aa30`,
56950B. No app start, credential payload/hash or original operation replay.
This ends the source22 guest phase without erasing its failed run or native passes.

Applied reviewed transport patch8440cb93 and operator-bootstrap patch5a3e51ff
only after preservation. Rootless `_environment` now fixes SYSTEMCTL_FORCE_BUS=1;
native UID0 environment is unchanged. The configured fixed user-session address,
closed environment, indexed manager/process/container and original socket-pidfd
proofs remain mandatory. There is no new SELinux allow or private socket mount.
Contracts/invariant/ADR150/human troubleshooting explain this boundary. Deployment
procedures now explicitly refresh and preserve fixed bootstrap files before index
preparation and describe compatible rollback. One long test signature was formatted.
Targeted host-peer/policy tests ACTUALLY PASSED137; Ruff passes; documentation
alignment passes207 human documents/27 helpers. These are source checks, not new
installed acceptance.

Fresh source23 capture ACTUALLY PASSED: snapshot
`310e2c9b59e226fe1f717c13f44faad48f6d3d15559887a4bbd6625d2482a4a1`,
1361files, inventorye0f6a558, tar4bec063f/17756160B. Nine changed leaves against
source22 are seven documents, one test and host_peer.py; all96 web source leaves
are unchanged. Runtime host_peer SHA256
`e0cb0ed3bdc2e7053541b89877757d6931a67864a02d119508579e4e9f757760`.
Source22 receipts are historical and do not establish source23 installed proof.
Fresh local fixture projection ACTUALLY PASSED: only two TOML version fields
0.2.2→0.2.12; all108 package leaves equal canonical source23. Projection snapshot
`81766c901626fa2e6a97a373f0dc5b1f44106fdec39fc30e10cc46fe839064fc`,
receipt74950fd0/245249B. This is local preparation, not a new installed run.

Gate23 is RUNNING under captured wrapper5612caf9/7212B and original outer3808881/
start435371644. Command `historical gate invocation (original command SHA-256 `b9d97947112e6e5c5005002b465c3dd68f8bd158ca8c41cb5966f57422999103`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`;
no final outcome inferred. Frozen source23 admits only the five bookkeeping
exclusions. Fresh native/rootless images/installations, functional cases,
isolation/fault/lifecycle, final gates and WEB006 commit remain required.
Shared API/UI retains pinned UBI10 micro; no frontend server/image is introduced.
WEB007–026 pending; production/NAS/installed predecessor interface untouched, no rollout/merge/push/tag.

### Checkpoint212 — source23 strict gate and fresh artifact/image builds pass (2026-10-24)

Canonical artifact attempt1 ACTUALLY FAILED0.179113s, original3829350/
start435504263 rc1/reaped/gone. An embedded reader demanded v22 capture filenames;
no build or application ran. Its reserved canonical-v1 locator and stderr
bc563eba/459B are retained. Fresh template-v2 readers now execute full actual
load_capture+verify_capture before publication; independent read-only preflight
verified all1361 captured/current members for all three templates. No runtime
source change or gate rerun was needed.

Fresh canonical-v2 build ACTUALLY PASSED17.532919s, original3829852/
start435516560 rc0/reaped/gone, all held inputs closed. Canonical software0.2.2
wheel SHA256 `089ca3ce6e147f676a94479b72919faa4f9f12a1c53de831bd75f60d36f73a20`,
500437B. SUMMARY SHA256
`d0cfa7367b63b87b963dd8e9ad587ed204962398479543de8a3914b5e40c34d1`;
its inherited temporary-directory prefix says fixture0212, but the actual
software_version is0.2.2 and the separate canonical-v2 locator owns it.

Fixture0.2.12 build ACTUALLY PASSED17.479160s, original3830791/
start435521349 rc0/reaped/gone. Actual wheel SHA256
`a36904702b19f033a54a0c41064c5b691df1e8613b8266fb4b0248477f89ba49`,
500453B; SUMMARY SHA256
`7a6b6213c8ccb9d2ace80d5f32703025753be6f07c4d198fce199c275e2106a9`.
Both canonical and fixture builds each independently built the UI twice with
identical resulting trees. Fixture has six assets, manifest SHA256
`5e3d34632741a50bf0aefb25e9694f2f2464276beccbbe63215ec7ded7cac70e`;
application version0.2.12 and all108 package leaves match the projected source23.

Shared API/UI image build ACTUALLY PASSED28.562591s, original3831288/
start435525112 rc0/reaped/gone. Image
`sha256:410c627e860a23cc207f4a5cb82bb905f077c36fd8584ad4164ec7f34889af0a`,
204760975B, build receipt SHA256
`87f42fd86c491ae957d6ef4f28b30d66155745b80db5fdf3dd986006c8fd158a`.
Both build/runtime FROM use pinned UBI10 micro digest87a27d71; the approved
CA-data-only donor boundary remains. Actual fresh installed ancestry/absence
and asset audit is still pending; the build receipt explicitly retains that flag.
There is no frontend image/server or runtime Node added.

Packet preparation1 then refused a consumer-field mismatch before publication
or any source23 guest call: codec expected gate23_outcome_not_inferred while the
frozen projection74950fd0 carries legacy gate22_outcome_not_inferred=True.
Projection bytes remain unchanged because artifact receipts hold them. A fresh
codec will require that actual legacy field while retaining the separate actual
gate23 proof; complete real-member bundle/payload validation precedes publication.
This is test-tooling recovery, not another application/functional cohort.

### Checkpoint213 — source23 staging transfers pass; native installer preflight preserves old labels (2026-10-24)

Corrected source packet2 publication ACTUALLY PASSED full bundle/payload checks:
packet143cf1e0/36362240B, codec71aca7bd/10766B, PREPARATIONe0652eac/2949B.
The frozen projection74950fd0 was not rewritten. Source transfer ACTUALLY PASSED
29.570860s, outer3833584/start435554382 rc0/reaped/gone, all local/guest inputs
closed. Fresh readiness ACTUALLY PASSED4.100556s, outer3833934/start435563718
rc0/reaped/gone: all280 predecessor inputs, source23 records, preserved failed33
Basic/aliases, unchanged key metadata, empty secret list and strict role closure.
No source23 application/helper was started.

UI packet1 preparation refused stale canonical/fixture snapshot constants after
writing its partial packet. Files remain preserved; corrected codec2 validates
actual310e2c9b/81766c90, all108 wheel leaves and six UI assets before publication.
Independent full in-memory payload validation passed. Actual UI packet2 is
f47a9a2c/1269760B, bound codec3e641add/5024B; it is not installed yet.

The completed image wrapper used actual original image-build-v1.json, while a
consumer expected -execution.json. No image was rebuilt and no alias was made;
fresh binder2 explicitly joins that original record, source and channels.
OCI export ACTUALLY PASSED5.234319s, original3835232/start435601453
rc0/reaped/gone; export receipt8f243398/38717B. Exact OCI transfer PASSED3.711716s,
original3835712/start435616642 rc0/reaped/gone, all inputs rejoined/closed;
image410c627e retained, no load/application start. Full build-receipt transfer
PASSED0.748085s, original3835802/start435619027 rc0/reaped/gone. These are staging
receipts, not installed runtime ancestry/absence or functional acceptance.

First native012 stage ACTUALLY FAILED21.049086s, original3834231/
start435570607 rc1/reaped/gone; protected RESULT
97e7de1b5c638e7dcc385791e0e94e74cfa709b06f609b333245a65ad3f21b42/181326B.
It copied a fresh protected source tree but DID NOT CALL THE INSTALLER.
The original dry-run restorecon command returned0/reaped with7110B output where
the preservation guard requires empty output. No service, selector, policy or
credential change occurred; final strict closure and kernel revalidation pass.

Bounded read-only original-label collection PASSED0.793137s, original3834881/
start435588987 rc0/reaped/gone. It holds the failed RESULT and exact dry-run
stdout85d567ef/7110B; every would-relabel row is solely in the inert retained
/opt/hfcache/releases/0.2.11 rootless fixture. Each is unconfined_u:usr_t→
system_u:usr_t: the SELinux user changes, not the type. The original native
installer intentionally restorecon -RFs the whole prefix. Skipping that guard
or normalizing old recorded labels would invalidate retained evidence.

A fixture-only private-MNT pilot is being prepared/reviewed, not yet executed.
Only that inactive old rootless sibling will be shadowed by an empty root-owned,
expected-label read-only/private directory inside a child; parent/host views
and original tree hashes/full9/SID remain unchanged. Native source/current/new
.12 target checks remain real, and the new release writes through the actual
host filesystem. Original dry-run and first installer invocation must share
the same child MNT; no USER/PID/NET unshare or namespace FD at exec. Normal native
API acceptance runs outside the installation namespace. All roles are stopped,
so actual host/parent/pause tables and explicit absent-role states are evidence;
no six live role tables are fabricated. This validates fresh native installation,
not mixed-history upgrade compatibility. Source review confirms --no-switch
native classification does not scan unrelated release siblings. No core source,
SELinux grant or systemd hardening change is proposed; source23/gate23 stay frozen.

Future native-v2 consumers remain UNBOUND until actual successful installation;
failed native-v1 flags, captured source and logs stay retained. Source23 image
load/runtime audit, real native28/rootless34, isolation/fault/lifecycle and package
completion remain pending. WEB006 uncommitted; WEB007–026 pending. Shared API/UI
uses pinned UBI10 micro, same existing Caddy. Production/NAS/installed predecessor interface untouched;
no rollout, merge, push or tag.

Exact protected transfer/readiness serialization joins:

- `web-006-source23-transfer-v1`: passed=true, SHA256 `f2a86c0b9fc974c4c9e4fc6ce59451a827091ed641a3feab294d0eab12103003`, 909380B.
- `web-006-source23-readiness-v1`: passed=true, SHA256 `692e4e72d48f2c1786a27211f2a05cade38fd0ce81fddf3ae67def9968539753`, 251175B.

### Checkpoint214 — isolated pilot and first actual native installation pass (2026-10-24)

Pilot actor-v1/caller were NEVER EXECUTED. Local preflight caught that the general
selection_new_directory helper admits only WORK/GENERATIONS and would reject the
new child log directory. Fresh pilot-v2 uses a dedicated fixed namespace-execution
creator without widening that helper; it also checks the actual pause namespace
and global .12 absence. Root's O_PATH fstatvfs concern was withdrawn after a real
local probe succeeded; no unsupported EBADF claim changes the fixture.

Pilot-v2 ACTUALLY PASSED3.908489s, original3837903/start435692642 rc0/reaped/gone.
Its local stem is web-006-source23-native012-shadow-pilot-v2, while first actual
protected WORK remains source23-native012-shadow-pilot-v1. Protected RESULT
`d19fd9930d6ee9f558265b6212976d084bc35dae6d0a0c1dc45475407e24af70`,
149984B. Child161570/start36575468 returned0/reaped/gone2.056611s; original dry-run
restorecon returned0 with empty channels. Only MNT changed, root propagation became
private, and exactly one empty root-owned expected-label RO/private alias covered
inactive .11. USER/PID/NET were unchanged, descriptors closed before commands.
Old .11 full9/SID/index-bound hashes and actual host/parent/pause mount tables and
namespace identities are unchanged; stopped-role absence is recorded explicitly.
Global .12 remained absent before/after; no installer or application ran.

Fresh native-install-v2 bound sourceca027145/122555B to actual failed97e7,
pilotd19f, readiness/transfer and unchanged core/parent. Actual read-only binder
predicates and independent source/global/footer review passed before execution.
It copies a new protected source-v2 and preserves failed-v1's complete1361-file
source inventory. Original copy, package, installer and lock helpers remain
unchanged; only child-private fixture isolation surrounds dry-run and installer.

Native-install-v2 ACTUALLY PASSED40.810021s, original3838578/start435716505
rc0/reaped/gone. Protected RESULT
`bc5063cd36d8665c0698abf6d0f0ff1b7fa275b7e812fe804d7ee05e7f9a6083`,
372634B. Child161630/start36600907 returned0/reaped/gone19.703306s. FIRST ACTUAL
original installer161635/start36601097 returned0/reaped/gone17.508698s; stdout618B,
stderr2039B retained (normal installer/uv diagnostics), no forced termination.
Original global preflight failure remains failed; no installer was replayed.

The new /opt/hfcache/releases/0.2.12 is actual host-backed storage and was measured
from the parent outside the installation namespace: version0.2.12, all108 package
source leaves match frozen source23. Native runtime acceptance must also run
outside that namespace. The original old .11 tree full9/SID/hash, failed source1's
1361 records and host/parent/pause tables remain unchanged. All280 prior inputs,
key metadata, empty secrets and strict role closure rejoin/close. Current selection
is absent; no app/helper service, timer, policy or credential action occurred.
This is fresh-native installation evidence, not mixed-history upgrade acceptance.

### Checkpoint215 — UI/runtime/environment/rootless staging pass; bootstrap guard refuses before mutation (2026-10-24)

Native UI stage ACTUALLY PASSED5.587448s, original3840094/start435774977
rc0/reaped/gone, protected05c4819a/55652B. Sealed caller7f9a0190/75704B passed
full source1361/input287/packet and memfd-seal15 checks, independently repeated.
Six native assets match actual build; all108 installed package FDs stayed held.
The wheel was evidence, not installer input. No API or Caddy started. A dispatch
delay occurred because plain messages to an idle agent did not resume its turn;
an explicit followup corrected this. No guest outcome was inferred while idle.

Image load PASSED8.292331s, original3840300/start435781929 rc0/reaped/gone.
Runtime audit PASSED57.979890s, original3840556/start435788693 rc0/reaped/gone,
protected0ed42a99/82544B. Actual image410c627e proves pinned UBI10 micro ancestry,
108package/6UI hashes,35 named tools and eight modules absent. No runtime Node
or frontend server was introduced. Actual inner981 maps host983; CapEff/CapBnd0,
NoNewPrivs1, seccomp2, read-only/no-network/no-secret audit isolation pass. Original
audit CID d19c717ff3f5b24750a406d98bab9f55e131b7e9ee600458df04da95effb1ab9
exited and was retired without force; exact absence returned1. Original audit
process/cgroup closed, three older stopped audits unchanged. This is image/runtime
evidence, not host-helper/UI functional acceptance. A mistyped binder mode audit
refused before effects; runtime was subsequently bound/executed exactly once.

Environment preparation PASSED21.967225s, original3841131/start435807383
rc0/reaped/gone, protected4d50b854/335943B. Installed source23 package projection
is read-only; genuine browser/UI inputs prelabelled/copied and all original sources
rejoined. Empty secrets, key metadata, absent selectors and strict roles remain.
No old sources were written or relabelled; no application service was started.

Bootstrap refresh1 FAILED1.640569s, original3841521/start435819268 rc1/reaped/gone.
empty_candidate230 admitted only host_peer-source22-candidate.py, but its caller
supplied source23-candidate. It refused BEFORE candidate creation, intent or rename.
Live BECB peer stayed unchanged and its FD rejoined; final strict closure passed.
Original false RESULT/WORK retained. Fresh script-v3/protected refresh-v2 will
correct only that exact path and independently check all mutation helper scopes.
No code, policy, permission or security-contract change requires a new source gate.

Independent rootless release staging PASSED5.468002s, original3841884/
start435831571 rc0/reaped/gone. Deployment0.2.13 explicitly uses software/image
0.2.12; this is fixture metadata, not product version or deployment acceptance.
No service, selector, policy or credential action occurred. Profiles await actual
bootstrap refresh success, then fresh native28/rootless34 real Caddy/browser,
helper/isolation/fault/lifecycle acceptance. Required cases remain pending.

Exact protected RESULT serialization joins:

- `web-006-source23-native012-ui-v1`: passed=true, SHA256 `05c4819a57e2c8e08649e16eb3b3e086a07d4a3c4820c30cbd36e6da093cfda7`, 55652B.
- `web-006-source23-image-load-v1`: passed=true, SHA256 `2161b851df23735f68c9dffbd4d91baa2e59ff6ad8ed5558220fda0c9992a61c`, 73690B.
- `web-006-source23-runtime-audit-v1`: passed=true, SHA256 `0ed42a994761b36a8ffcbf9a7cea2a301ca79e1bc943a5914076310e043f1211`, 82544B.
- `web-006-source23-environment-v1`: passed=true, SHA256 `4d50b8541385074a29d81f1565efb0d14af5ba7814e8d70908c6b85e21334f2b`, 335943B.
- `web-006-source23-bootstrap-peer-refresh-v1`: passed=false, SHA256 `184eb7b42da9617622e5a9294f21105f58fdc0c8437314bfabf78d97f54bb3e8`, 35874B.
- `web-006-source23-rootless013-stage-v1`: passed=true, SHA256 `3b9ca628be2c19d5ca42f3939ae223d016bc4f02f83cd4c25372a94efa620d79`, 85199B.

### Checkpoint216 — prepared authority passes; first source23 native functional run fails (2026-10-24)

Helper refresh2 ACTUALLY PASSED2.040604s, original3842500/start435850969 rc0/reaped/gone. Protected RESULT1b500056/57845B. New fixed bootstrap peer is E0CB/82936B; old BECB/82769B inode is preserved by two NOREPLACE renames. Key, policy, permissions, labels and services were not changed. Failed refresh1 remains false.

Profile proposal1 FAILED3.105896s before selector/intent creation because a stale exact pair admitted .10/.11 instead of .12/.13. Original3842753/start435859152 rc1/reaped/gone, protected03b77543/36159B. Fresh proposals2 ACTUALLY PASSED5.079745s, original3844424/start435921824 rc0/reaped/gone, protected98442375/127112B. Both fixed profile pairs, all six permission bits, exact configuration labels and temporary selector NOREPLACE preservation pass. No permission is broadened.

Authority33/controller34 publication ACTUALLY PASSED4.033082s, original3844913/start435940559 rc0/reaped/gone, protectedbc5f08d5/87953B. New control-v34 SHA256bddbee43437d1ac8253703cd859be8c3dd34310319460bd4e2f453997355c46d pins298 inputs while preserving the prior280 in order. Manifest e7c9c731/5027B binds actual installed .12/native and .13/rootless source23 artifacts. Preparation alone starts no application services and adds no functional acceptance.

First source23 native28 functional runner ACTUALLY FAILED: outer3845328/start435956485 rc1/reaped/gone16.774427s; original runner162696/start36839323 rc1/reaped14.662615s, stdout0B, generic stderr62B (286fbc7a). No SUMMARY exists. The outer failure main330/prepare_authority320/need30 is only the final failed-run guard; actual startup cause remains unproved until original public/generation/controller records are inspected. Default application_services_started=false is not startup-stage evidence.

Protected failed native28 RESULT is SHA2563fd5d98f2127d6813a89c8df4b751dc363c760c8c59e019b4545d21041f40658/50352B. Original runner was invoked exactly once; no replay. Final strict closure actually proves all13 fixed roles, four cgroups and five endpoints closed, key metadata unchanged and exact secret listing empty. New Basic credential is metadata-only inode118816437/dev64515/root:983/0640/221B/secret_t; no body or digest was read. Original workspace is .scratch/web-host-fixture-source23-authority33-native28-v1 in the owned guest; generation-v34/controller34-error evidence is retained. A bounded read-only diagnosis and exact Basic/three-alias preservation are required before any fresh cohort. Do not infer API/worker crash, helper denial or browser results from the footer.

### Checkpoint217 — native startup passes; actual launcher format defect identified (2026-10-24)

Three bounded read-only original-record actors ACTUALLY PASSED; these emit stdout-only diagnostics, not protected RESULT files or new functional cohorts. Startup reader3846966/start436013382 rc0/reaped/gone0.812339s; browser baseline reader3847392/start436023391 rc0/reaped/gone0.783596s; format reader3848039/start436041096 rc0/reaped/gone0.809919s. Local result artifacts are respectively b90ed589/155441B, aebee264/151235B and7db9cdb7/146822B; exact .scratch/web-006-source23-native28-{startup-read,browser-baseline-read,launcher-format-read}-v1-result.json paths retain them. All held inputs rejoined/closed.

Original native28 generation f74cd611d68f4625ae5b2c3b5ca4b77e state05271528/37158B and public RESULT42178dd1/8563B prove actual started/ready/stopped=true, both original/delivered secret gates passed, initial native process-principal cohort passed, bootstrap authenticated Caddy HTTP200, matching manifest/instance/kind, no fixed-start or stop failure, all28 original process identities gone. Public cleanup_unknown=false, ready/stopped evidence present and all mode rows absent. Thus checkpoint216's unknown startup cause is resolved: application startup succeeded, while complete functional acceptance still failed.

Only RESULT/runtime/start-response/stop-response files exist. There is no baseline proof/report, same-Caddy directory or TLS pair record. Actual published browser launcher db2cb667/199779B full9/SID/hash/root0755 rejoin proves its first line is the known docstring and starts_with_shebang=false. Historical source22 executable began #!/usr/bin/python3. Ignored fixture emitter prepare-source23-functional-v1.py:29 used ast.unparse without preserving that line, then emitted the launcher at37–40. Product functional command() directly invokes the executable path. This fixture format defect prevents browser launch before artifacts. Original failed errno was not recorded and is not claimed as observed; a separate harmless owned inert executable reproduced ENOEXEC8, and its shebang control exited0 with empty output. The actual failed launcher was never reexecuted.

The unused UID1000 preflight draft remains unexecuted. No raw auth/log/exception text, service start, network request or credential read occurred in these three readers. Exact Basic/three-alias NOREPLACE preservation and a new authority34/controller35 with explicit executable-prefix regression are being prepared. Existing failed original/workspace/authority remain immutable. No core source/runtime or source23 gate/build change is required. Fresh actual native/rootless/browser/isolation/fault/lifecycle acceptance remains mandatory; no WEB006 case is completed from startup or diagnostics. No production/NAS/installed predecessor interface or publication action occurred.

### Checkpoint218 — failed28 preserved; corrected authority passes; native29 running (2026-10-24)

Failed28 preservation ACTUALLY PASSED1.970268s, original3848486/start436051478 rc0/reaped/gone. Protected source23-native28-failed-preservation-v1/RESULT.json SHA256c3bf96d32994f080478acaf6374464416123f353ed3df36d506de36d4d8d3925/78699B. Original failed collector/gen/public five records held and unchanged, all28 original handles freshly gone, strict closure/empty secrets/key metadata rechecked. Basic inode118816437 and all three exact native.12 aliases preserved by four unchanged NOREPLACE helpers; four current paths absent afterward. Basic body/digest never read, original false acceptance flags remain false.

Fresh authority34/controller35 ACTUALLY PASSED4.112842s, original3849279/start436073676 rc0/reaped/gone. Protected fixture-authority-v34/RESULT.json SHA256cbc87b407f8668029f50fb74203eb4b8c6039151a94c3399714457add29d534e/106985B. New fixture901db2d9-7ce5-4eaa-902b-b9a28a5aeb6a, control-v35 SHA256fa4e137154376f1259ca2882f99fc42657df0ea46f82272756ddf88dfbc8052c/56593B pins303 inputs preserving the original298 prefix in order. All21 prior authority33 published file records were held/rejoined unchanged. Manifest e76e81402bb67d598c2b6a14299be71393c4ab2c4057d70b2521c43852f87827/5027B. Corrected browser launcher0f81f161/199798B retains #!/usr/bin/python3; controller354a83f9d1/118954B changes only three fixed fixture paths.

Four directly executed role bodies (browser/native/rootless/functional) pass exact interpreter-header checks before publication; four malformed/missing-header regressions reject. Full actual-data binder prefix passes; independent reviews find no blocker. New captured authority caller dc90dbde/70963B passes278-input/1361-source/117697-byte SSH cap, unchanged120000 limit. Final strict closure passes with four current paths absent and no service start. No product/source change or image rebuild was necessary.

Fresh native29 functional actor b05dd802/37298B and caller ff93328a/70535B bind actual new authority, actual failed28 preservation, environment and303 control inputs. Captured preflight passes276 local inputs/1361 sources, SSH22500B. Original3849481/start436078128 is running in fresh workspace web-host-fixture-source23-authority34-native29-v1; no outcome, case pass or stop evidence is inferred while running. Root is the sole serial guest executor. Fresh rootless34 and native/rootless fault/isolation/lifecycle acceptance remain mandatory. Source23/gate23 and actual UBI10 micro runtime proof remain unchanged.

### Checkpoint219 — fresh native29 normal pass; rootless34 original running (2026-10-24)

Native29 ACTUALLY PASSED: outer3849481/start436078128 rc0/reaped/gone341.595649s; original runner163175/start36960964 rc0/reaped338.720135s, stdout77B/stderr0. Protected source23-native29-functional-v1/RESULT.json SHA256f7d294e72fc70ede75611c41e09e39e281323b94687a1b5339de21fecb2c3b88/446408B. New generation4b5a11800aba49a3ad9d201276ef60e7 executes exactly once. SUMMARY a0e831aa/379436B covers baseline/helper-down/restarted/timeout, Chromium156.0.8078.4/Firefox157.0/WebKit27.2,33 actual browser host assertions, all12 untrusted-CA refusals, zero required skips/retries. Original failed28 is retained without promotion. All held inputs rejoin/close and final13-role/four-cgroup/five-endpoint strict closure passes, secrets0.

Postrun ACTUALLY PASSED1.737289s, original3850928/start436114628 rc0/reaped/gone. Protected source23-native29-postrun-v1/RESULT.json SHA25658a71fd6b2285593df5a58a7d1c5a9518efd16790223212b3b695e743243ed2d/129948B. Independent exact eight-record normal-readiness ABI binds current35 versus previous34/298 and validates actual original SUMMARY/generation. All original generation handles gone. Four same-Caddy TLS epochs join trusted/untrusted captures for all three engines. This is native normal acceptance only; no rootless or dedicated negative pass is inferred.

Ordinary native29 preservation ACTUALLY PASSED1.828014s, original3851040/start436117221 rc0/reaped/gone. Protected source23-native29-preservation-v1/RESULT.json SHA256516cb3d37b68e7792f9ffb27d8e1499b432268cb8c6aaf4d3b6a3b353ee44b7b/55619B. Exact metadata-only native Basic inode118788490/root:9830640 and three aliases preserved by unchanged NOREPLACE helpers after fresh strict/empty-secret checks. All four current paths absent at completion, key unchanged; no credential body/digest read.

Fresh rootless34 baseline ACTUALLY PASSED1.549561s, original3851180/start436120241 rc0/reaped/gone. Original baseline protected serialization is compact sorted JSON+newline (not pretty serialization); local file web-006-source23-rootless34-baseline-v1-result.json retains exact proof. Fresh inventory proves empty stock secret store and complete/traversal-safe before/after metadata, with actual native29 prerequisite rejoined. No explicit secret create/remove/replace, store payload read or retirement occurred.

Rootless34 coordinator fb6fa2b7/131279B, observerfd155e21/51891B and runner-template987090cd/41506B bind actual authority34/control35303/native29 pass/postrun/preservation/baseline. Captured caller947d063b/70979B passes278 inputs/1361 sources/SSH48651B. Original3851372/start436125756 is running; no functional outcome, stop or secret-ownership result is inferred while active. Only root executes the serial guest lane. Rootless normal is deliberately first feedback before the still-required native/rootless dedicated fault and isolation/lifecycle cohorts.

Four WEB006 cases retain pending status until all required profiles/layers pass. Native normal pass is added once to the ledger, no diagnostic/staging cohort added. Source23/gate23 and image410c627e pinned UBI10 micro remain unchanged. WEB006 uncommitted, WEB007–026 pending. No production/NAS/installed predecessor interface action, rollout, merge, push or tag.

### Checkpoint220 — original rootless34 functional failure retained (2026-10-24)

Rootless34 ACTUALLY FAILED83.579333s, outer3851372/start436125756 rc1/reaped/gone. Protected source23-rootless34-coordinator-v1/RESULT.json SHA256d114ed04b2dc11ee64fb09303abe34da8c216f22277b5ba51f83c3fbc9e7a90e/68009B; local610bf55b/217950B. Original runner168642/start37008580 rc1/reaped81.894778s, checker168646/start37008607 rc1/reaped81.392275s, generic stderr62B/286fbc7a and stdout0. No SUMMARY. Original watcher168641/start37008553 rc0/reaped82.178578s. Coordinator final fixed-role closure actually passes, held release failure classes empty; original watcher/runner fresh identities gone. Original all-input/feature acceptance flags remain false and are not promoted.

Watcher successful_ownership_proof=true/all_sources_rejoined_and_closed=true records exact six secret IDs and actual worker/API/Caddy role mapping for generation71c1fb6a0a2a4d8e96a52b8ecaae496b. Original containers are22f497413d35bb61e19f99844e6314e94a78860658d3d1bf477202b2cef2ecf1,8271a1e7323f4647593018a6910478e2f60a11afd9c751a9faf96f4210154013 and99e6da3cf61f746d4f9daeccf0e53be793d2fb0895b5421f21c7695985441d22. Actual stop/generation/CID evidence still requires bounded read-only inspection before retirement. Six owned secrets and current Basic/aliases remain retained; no secret payload/digest, uncertain deletion or replay.

Independent source/provenance audit confirms SYSTEMCTL_FORCE_BUS=1 reaches the actual closed UID983 _command environment without later reset, and fixed bootstrap/profile/source bindings require E0CB/82936. This excludes a stale bootstrap as an explanation; it does not establish the actual failure cause or a new policy defect. Bounded original browser/report/generation diagnostic is being prepared; no product/security change is justified until actual evidence identifies the boundary. Failure-only exact-ID retirement and four-path preservation drafts retain original false flags and wait for actual drain/Basic proof.

### Checkpoint221 — failed34 safely preserved; session-broker connection denial observed (2026-10-24)

Combined original metadata reader ACTUALLY PASSED0.835468s, original3852270/start436153216 rc0/reaped/gone. Local .scratch/web-006-source23-rootless34-failure-metadata-read-v1-result.json SHA25615aec6ef/188262B is stdout-only evidence, not a new protected RESULT. Exact generation f63e098cd1507f6ee7aaa41044b02509e88a71f42a24d36912e6fa9d2f4c8456/73360B and public f502decd/16341B establish started/ready/stopped, cleanup_unknown=false, all69 original process pairs gone, three exact CIDs exited0/PID0, original wait0/exists1 observers EOF/reaped/closed, cgroups empty/endpoints refused, inputs unchanged.

Baseline report0a87dec4/67912B shows all three engines reach built UI then fail pre-case assertion HostStatus unavailable vs supported; zero case rows. Browsers/descendants close normally/exit0. Trusted baseline container exit1 is drained and inputs unchanged; report rejection is not a passing report or an API crash. Untrusted TLS refusal passes all3engines. Stored sanitized assertion diagnostics only were read; no auth/raw logs.

Failed34 six-ID retirement ACTUALLY PASSED5.206118s, original3852677/start436165515 rc0/reaped/gone, protected source23-rootless34-failed-secret-retirement-v1/RESULT.json SHA256f2f35bac1a9391d89e428fe59a395a8d3472e0b553837aaa5e8d187921232406/121385B. Fresh actual ownership/69handle/3CID/6observer checks precede durable opaque whole-store backup and six individual nonforce exact-ID removals/intents/rechecks. Final known/unknown secret counts0. Failed34 and original31/32/33 false flags remain false; this is cleanup only, no normal lifecycle or functional pass.

Four-path preservation ACTUALLY PASSED1.830460s, original3852936/start436172413 rc0/reaped/gone, protected source23-rootless34-failed-preservation-v1/RESULT.json SHA2566c8974c38275b3fec62eeaae5e2b0ac122a444d60a5a112794cd9c3348366692/56962B. Original Basic inode118858722/983:9830400/secret_t, selector.13 and exact deployment/policy aliases are preserved with NOREPLACE. Four current paths absent afterward; final strict closure/key metadata pass. All original failures/records retained, no secret body/digest exported, no replay. Independent destructive-boundary reviews pass.

Bounded original AVC reader ACTUALLY PASSED0.921700s, original3853039/start436175572 rc0/reaped/gone, .scratch/web-006-source23-rootless34-avc-metadata-read-v1-result.json stdout-only evidence. Exact original coordinator/gen/report hashes and secret-gate sequence47 rejoin; Enforcing kernel45bb unchanged before/after. Window1792892704..1792892786 exports only45 typed audit events:7 helper_t connectto denials to unix_stream_socket target unconfined_dbusd_t;24 exec_t-file ioctl,6 init_t-socket ioctl,8 cert_t-dir search events are separate and not assumed causal. No raw audit bytes/paths/argv/messages or payload hashes exported.

The session-bus source23 fix reaches closed UID983 _command environment and actual E0CB installed code. Recorded connectto denial exposes a candidate session-broker process-type compatibility gap; precise original SYSCALL/fixed-systemctl/broker metadata attribution is being prepared before selecting a fix. No audit2allow, blanket permission, IOCTL/certificate grant, SELinux relabel/disable or security weakening is authorized or applied. Any necessary scoped source/contract change requires fresh capture/gates/artifacts and actual functional evidence; source23 frozen evidence is never relabelled as a newer pass.

### Checkpoint222 — measured broker compatibility correction applied; fresh gate pending (2026-10-24)

Exact paired original AVC/SYSCALL reader ACTUALLY PASSED0.913445s, original3854070/start436204975 rc0/reaped/gone, .scratch/web-006-source23-rootless34-syscall-broker-read-v2-result.json stdout-only. All7 exact original audit serials56952/56967/56968/56975/56980/56985/56990 pair fixed-systemctl exe/comm booleans with syscall42/connect, success=false, exit-13/EACCES. Their numeric PIDs are absent now; original child start ticks were not saved and are not invented. Current fixed broker70560/start6647884 UID/GID983 has exactly the recorded unconfined_dbusd_t peer context; bus dev45/inode18 remains session_dbusd_tmp_t, O_PATH metadata only. Historical broker PID-to-AVC-peer attribution remains explicitly unclaimed. No connect, request, replay, raw audit/argv/PATH/proctitle or payload export occurred.

Two independent reviews and primary Linux6.12/dbus-broker source support exactly one compatibility allow: helper_t to unconfined_dbusd_t unix_stream_socket connectto. Its extent is type-wide IPC; fixed UID/address/closed metadata argv and protected peer/process/container proofs continue as application constraints. No dbus-send, ioctl, certificate, payload, capability or transition right is added. DRAFT-v1 peer-matrix/primary-anchor issues were caught before application and fixed in DRAFT-v2 SHA256742d4d90f1e0f726b34ae34e5a47ea92ec5ea3da5e493aac4e576c164e22c7e7/8898B. In-memory candidate regression rejects the old policy and eight widened-policy mutations; final independent assessment2a1ec80e/13014B has no blocker.

Root APPLIED only reviewed patch-v2, updating INV020/ADR150, human host/security/troubleshooting contracts, singleton CIL rule and exact peer-rights regression. Source23 freeze ends here; every old receipt/source remains retained. Ruff format leaves test file unchanged; Ruff check and git diff --check pass. Actual command rtk proxy uv run --locked --extra server --extra mcp pytest -q tests/unit/test_host_selinux_policy.py tests/unit/test_host_peer.py exits0,138pass/6.60s; documentation alignment exits0,207human documents/27helpers.

Canonical delta against source23 explicitly proves exactly7 changed files: docs/invariants.md,docs/adr/decision-150.md,docs/host-administration.md,docs/security.md,docs/web-ui/troubleshooting.md,packaging/selinux/hfcache-host-helper.cil,tests/unit/test_host_selinux_policy.py. All108 Python package leaves and96 web source inputs remain unchanged. New full source24 capture, strict gate, actual source24 artifacts/installations/policy receipt and native/rootless/browser/isolation/fault/lifecycle tests remain required. No source23 pass is relabelled as source24 acceptance. Gate23 and native29 normal pass stand for their exact historical snapshot only.

### Checkpoint223 — fresh source24 captured; strict gate24 running (2026-10-24)

Root ACTUALLY captured source24 using c3192c49/17559B script after full readonly before-write preflight. Capture .scratch/web-006-source24-capture.json SHA2568d2fc91845d1a2ecffc50d8cf87f1fc71538a410998cdef33a1722bbddc6ad4a/684B; canonical snapshot71cdbc2b7246aa5fff181c29e8caaedfac2beb02b66bbc883cd4ff5e3edbd8b6,1361ordinary files, exact5bookkeeping exclusions and CLAUDE symlink preserved. Inventory a568175f/ source24-local-v1-j9m16dgb/source-inputs-v24.json and tar402f86322d33a93efc3b5f331f170be58999877c87e9bb405578f9a71ee8ebca/17756160B are validated against full members/current bytes/modes/HEAD. Exact7 reviewed canonical changes; all108Python/96Web inputs unchanged from source23. Freeze24 now active; only five bookkeeping files may change.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

Disposable metadata projection ACTUALLY PASSED full tar/member/mode/hash/current checks. .scratch/web-006-source24-fixture-projection-v1/projection.json SHA256edfbabe73554eb791f7312da45ca6bb4c53af06e8541371195f82c8b759b9edf/245249B; projected snapshot826613a03943b24c9f97c9587a06b6999f799ab8577a5afbce334f4abc83cec9. Only pyproject/uv.lock selfversion0.2.2→0.2.14; canonical product version stays0.2.2. Projected input inventory92a6cdd083802d36e548fa3258e03f2c0a994eb522dc1e34ae2762c2eb3c7b85; tarf89650ecc6583ba1db3530efd1001df7b3510a853926d4c42cef64e11498c9ba/17756160B. Literal legacy gate22_outcome_not_inferred retained intentionally, separate actual gate24 receipt required. No build, guest installer or acceptance inferred.

Three inert artifact builders pass full actual capture24 load_capture/verify_capture before any future publication. Actual local immutable-receipt reconstruction using captured merge functions reproduces prior280→298→303 ordered control rows/counts/load_equal; no direct global /etc/hfcache or bootstrap policy/receipt path occurs among303 inputs. Reconstruction report4adbb47c/56883B is not a new guest observation. Historical release input preservation still requires actual .14/.15 staging proof. New source24 artifacts/shared pinned UBI10 micro audit, legitimate owned policy installation receipt, native/rootless and dedicated acceptance remain pending.

Guest remains quiescent after failed34 preservation, original kernel/key unchanged; no source24 guest policy or services changed. Source23 gate/native normal/failed34 diagnostics remain exact historical evidence only. WEB006 uncommitted, all4feature cases and WEB007–026 pending. Production/NAS/installed predecessor interface untouched; no rollout/merge/push/tag.

### Checkpoint224 — measured readonly assessment and private-MNT pilot pass (2026-10-24)

Source24 readonly preinstall label assessment ACTUALLY PASSED8.669986s, original3860519/start436290573 rc0/reaped/gone. Protected source24-native014-preinstall-label-assessment-v1/RESULT.json SHA256a396c5e788ca433762399ca5bb2d21ee087d1124daf3ab2c2d102d731f1f22bc/258296B. Original restorecon -nRFv /opt/hfcache process171059/start37173475 rc0/reaped5.299334s, stdout14220B. Exactly104 rows: retained rootless.11=52,.13=52,native.12=0,outside those releases0; every row changes only SELinux user unconfined_u→system_u with usr_t type retained. Both rootless full9/SID/hash snapshots and all108 native.12 source leaves remain unchanged; four selectors absent, secrets0, strict closure pass. No installer, application, policy, permission, timer or label changed.

Bounded caller3cfdf52b/71616B admits only exact assessment38733fdc/24008B and source24 full1361 hashes/modes/QEMU/FD/SSH guards. Historical gate23 is explicitly historical; gate24 outcome is not inferred. This lane supports only the named readonly diagnostic, no arbitrary root pipeline actor.

Two-shadow pilot ACTUALLY PASSED6.184479s, original3864033/start436321580 rc0/reaped/gone. Protected source24-native014-shadow-pilot-v1/RESULT.json SHA25675763428755502f06897fb01164549cf444cd9cb6490396b096a99a68b82ff35/281753B. Actual104-row assessment selects exactly old.11 and.13; nine pure mutation/closed-subset tests reject malformed, duplicate, outside, native.12 and type/SID mismatches. Root actor087a6c0a/72198B and exact specific caller43fa42ef/71554B were independently reviewed; full preflight1361/277inputs/SSH32898 passes.

Original child uses only private MNT isolation, recursivePRIVATE propagation and readonly private shadows over the two measured inert old roots. The native.12 tree stays visible and all108 full9/SID/hashes rejoin. Child restorecon dryrun passes; original child closes/gone and host/parent/pause mount tables/namespace identities stay unchanged. Native.14 remains absent before/after; original_installer_called=false, no policy or application start. This is fixture pilot evidence only, not installed application/host acceptance or mixed-history upgrade proof.

Gate24 remains actually running under original3855791/start436260069 and gate3855792/start436260088; Python phase reached85% at02:20:57Z. Source24 source freeze remains1361 files with5bookkeeping exclusions. Future .14/.15 artifacts, actual owned policy installation/new receipt/kernel, release indexes, native30/rootless35 and dedicated fault/isolation/lifecycle acceptance remain pending. No source23 pass or unfinished gate is promoted. No production/NAS/installed predecessor interface or rollout/merge/push/tag.

### Checkpoint225 — full source24 gate and fresh artifact/image builds pass (2026-10-24)

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

Actual source layers:7785Python pass/52 documented opt-in deselections;572historical frontend pass/0skip;2786webunit/2846component;21sandbox metadata and2built startup Chromium checks/0requiredskip; real HTTP/API React read fixture, format/lint/types/docs/build/install-profile checks pass. This is source gate evidence, not real installed Caddy/helper/native/rootless acceptance. Final plan gate with --with-build --with-web-functional remains required after all tasks.

Canonical artifact build ACTUALLY PASSED16.618995s, original3875482/start436395493 rc0/reaped/gone. Locator web-006-artifacts-source24-canonical-v1-locator.json retains actual SUMMARYa51c4d9b/ software0.2.2, wheel089ca3ce6e147f676a94479b72919faa4f9f12a1c53de831bd75f60d36f73a20/500437B. Temporary dirname fixture0214 is cosmetic; canonical software remains0.2.2. Fixture build ACTUALLY PASSED17.197000s, original3876220/start436400103 rc0/reaped/gone, SUMMARY17861284, wheel5f7f8921dd0205d222bf07e33cf8376d6e7155523eb828770d665acf5bf090cc/500452B,software0.2.14. In both builds two UI trees/manifests are byte-identical; canonical manifest3df4287d,fixturemanifestaf0010361904fc2741b44535d8a98e0189c8d8e42efc7f3a0e87ac2699e6cc0d. All prerequisite FDs rejoin/close.

Shared API/UI image ACTUALLY built: original3877000/start436409267 rc0/reaped/gone28.106456s; build command23.931465s. Image SHA25640a751be2eced246ee57533f0ee7fa94b2e2c8028dd1cb699820316218a36539/204760974B, localhost/hfcache:web006-source24-software0214-fixture-v1. Build receipt09eaebe7/585697B. Both FROM bases retain registry.access.redhat.com/ubi10/ubi-micro@sha256:87a27d7189dbae57f63db332a11de17f7ed6be91cdc956731c30141af2e8dc49. Approved CA-data-only donor retained; no separate frontend image/server. Actual ancestry/Node-package-manager absence audit is still pending, not inferred from build labels. Exact original execution path web-006-source24-image-build-v1-execution.json is bound explicitly.

OCI export ACTUALLY PASSED5.037485s, original3878645/start436420302 rc0/reaped/gone. Source packet full in-memory codec/actual gate executor+channels/current source/projection preflight passes before output creation: packet4e5af70a9ca8849571b96f6eb254a369e0d2b2318a14dba1b9748da344ea0d8d/36362240B, boundcodec2cf9bb30/10770B,PREPARATION18ef6bb3/2949B. UI packet likewise passes full codec before publication: df0b04882ffc6111651e6ca812ec63fc8d2d21e4dbc7d6b835e6388067c8e91b/1269760B,codec7db431f9/5024B. No packet receipt is an installed result.

Full source24 pipeline caller ebc2d083/70974B is locally bound from actual gate24; specific step callers still require exact root actor/input capture. Transfer binder first omitted required gate-script argument and refused line18 before writes; corrected actual argument passes and publishes only local actor2b2bae5d/65878B. Specialized sealed-stdin source transfer caller is being prepared; no guest transfer is yet claimed. Guest remains quiescent after prior readonly pilot, no new policy installed.

### Checkpoint226 — source24 source transfer passes; fresh readiness fixture correction (2026-10-24)

Actual sealed source transfer PASSED32.765922s, original3879941/start436456577 rc0/reaped/gone. Protected source24-fixture-transfer-v1/RESULT.json SHA256cddfc2454d458c39ed2f3d223e6d769cb28bed5fc84a00a935a3796405f66c18/909950B. All1361 canonical/projected source records rejoin; public source24 fixture is published, all_inputs_rejoined_and_closed=true,error_class=null,final strict closure passes. Canonical snapshot71cdbc2b/projected826613a0 remain exact; prior sources are preserved. A first local uppercase caller filename was refused by the unchanged owned-executor filename guard before spawn/output; a fresh lowercase caller5a89d1a9 passed full preflight and executed once.

Original staging-readiness-v1 FAILED1.440826s, original3880271/start436465305 rc1/reaped/gone. Protected source24-staging-readiness-v1/RESULT.json SHA25644bfea066fd64bd5e08561c541878226d77ccc3116e477450914b77606a79cde/31814B remains false. The exact KeyError was stale fixture values aliases transfer23/control33/authority32/retirement33/preservation33, while actual pinned inputs are transfer24/control35/authority34/retirement34/preservation34/environment23. Only the evidence WORK was created; installer/application/policy/key/secret effects remain false and final strict closure passes. No canonical source change or functional cohort replay occurred. Fresh readiness-v2 uses a new WORK/local stem and validates all six actual DTOs before filesystem checks; its outcome remains pending.

Fixed control35 readonly DTO export ACTUALLY PASSED0.780635s, original3881761/start436513248 rc0/reaped/gone. Exact root0600 full9/SID/hash control35 fa4e1371/56593B and303 fixed path/hash input rows rejoin; local stdout channel eaeb8fd4dbd92dfe1be5e0c1114ae901e5096374c05265cefe171882acdece00/165894B retains the observation. No key/credential/secretstore/archive payload was read and no command/network/service/replay was performed in the guest actor. This is readonly fixture DTO validation, not functional acceptance.

### Checkpoint227 — readiness/native014 pass; UI publication retained after local collection error (2026-10-24)

Readiness-v2 ACTUALLY PASSED4.004387s, original3882306/start436528149 rc0/reaped/gone, specific caller4764290c/70947B. Protected source24-staging-readiness-v2/RESULT.json SHA256b36a644ab42bad14c8a6b19ea2e393ff2fbe290ba37353b8450f28819909c166/268114B. All6 real DTO guards,303 retained control inputs, empty known/unknown secret counts, four aliases absent and final strict closure pass. Failed readiness-v1 remains immutable/false; this is fresh staging evidence, not browser acceptance.

First source24 native014 installation ACTUALLY PASSED38.981780s, original3882387/start436529874 rc0/reaped/gone, actor8484301c/111338B and caller609f539c/70964B. Protected source24-native014-install-v1/RESULT.json SHA256aa08e20d0722de64b8cc8d7834b8ad08e3a1b3a46eb3c2b37643f473625db407/512600B. Original installer ran once within the exact measured two-shadow private-MNT parent; all108 installed package leaves match projected source24 software0.2.14. Both inert old rootless full9/SID/hashes, native012's108 records and outside host/parent/pause mount tables/namespace inodes remain unchanged. Namespace child closed/gone; strict closure and all input joins pass. No functional application/Caddy start or new policy is inferred.

UI staging original3882564/start436535371 is rc1/reaped/gone5.870972s. The actual guest RESULT PASSED/all_inputs_rejoined_and_closed=true/error_class=null/final strict closure=true, publishing6 UI files and3 protected metadata files. Exact canonical protected RESULT SHA256d038e027f6c5140b9c0ceb82ef67a2591ad7f42ab2625f20e1154c9ec567406b/55647B; local stdoutf731bd34/157624B, stderrfd75cfbd/856B. The local collector then failed KeyError held_release_failure_classes in classify_publication line42 because that field does not exist in the UI DTO. Original local all_local_inputs_rejoined_and_closed=false/error_class=KeyError and outerrc1 stay unchanged. Application_or_Caddy_started=false, credentials_or_policy_changed=false,installer_replayed=false,new_browser_or_installed_application_acceptance=false. Do not replay publication or installation: a fresh readonly completion must join the original result/assets, original process closure and exact local source capture before image consumers can accept it.

### Checkpoint228 — readonly UI completion and actual UBI10 micro runtime audit pass (2026-10-24)

Fresh readonly UI completion ACTUALLY PASSED1.892484s, original3883607/start436565070 rc0/reaped/gone. Protected source24-native014-ui-completion-v1/RESULT.json SHA256ec53f9ea4633f98a67e898185283b80971dba8c7fe9782012dcba49192a5f4ba/114545B. Actual original guest UI proofd038 remains successful; original local collector rc1/false/KeyError remains immutable and is explicitly held separately. All6 UI files,3 published metadata files,108 installed package leaves and original8 command identities rejoin/are gone; key metadata, old45bb kernel, empty secrets, absent selectors and final strict closure pass. Only a new completion evidence WORK/RESULT is written; no installer/UI/asset publication or application/Caddy replay.

Independent OCI full actual prepublication prefix review3f1e4d6b/5306B identifies/fixes stale source23 snapshot constants in fresh v2 consumers/binder-v3. First actual source24 OCI handoff PASSES3.363801s, original3883115/start436551692 rc0/reaped/gone, actordcfb0fb8/36304B; local stdout53b6f86f/59427B,4 exact transfers. First build-receipt handoff PASSES0.758604s, original3883194/start436553386 rc0/reaped/gone, actor5c91a941/35676B; stdoutb43a64ee/22572B,1 exact transfer. Both all_inputs_rejoined_and_closed=true with actual image40a751be and software0.2.14/deployment0.2.15. No prior failed local binder was run against the guest.

Image load ACTUALLY PASSED7.946330s, original3883691/start436567140 rc0/reaped/gone; protected source24-image-load-v1/RESULT.json SHA2562be76289c40befeec88c2a795fc42c7100fbcdb8c9cb4867b0cf7b00a0bb273c. Actual shared micro base-layer prefix and bounded original OCI progress/exit/reap pass. Runtime audit ACTUALLY PASSED35.005082s, original3883785/start436569206 rc0/reaped/gone, actor51e4a1e4/66156B/caller6aa475a0/70951B. Protected source24-runtime-audit-v1/RESULT.json SHA256e7f2a8f1d2767c5efdc3ec4450fbc37fa932cb44ab4d59edc9c167a85477d144/80852B; stdoutf3105b27/174982B. Image40a751be is the shared API/UI image using the pinned genuine UBI10 micro base, not a separate frontend. All108 package/6 UI files match;35 named tools and8 modules are absent. Actual status has CapBnd=CapEff=0,NoNewPrivs=1,Seccomp=2; inner981:981 maps to host983:983, network=none, readonly_rootfs=true,privileged=false,secrets0 and only owned gate/private tmpfs mounts. Exact audit CID3d685d0ea6b6661a4366e43cf1c1d71eef3b1f49978f5aec6b0285e8a95cfe9e was stopped/drained and removed without force; original3 inert audit CIDs preserved. Final strict/key/old45bb checks pass. This before-policy image proof establishes no native/rootless browser/helper acceptance.

Policy original v1 FAILED2.200853s, outer3884003/start436575329 rc1/reaped/gone. Protected source24-selinux-policy-installation-v1/RESULT.json SHA25692d06e0262a82925262e2d8322863cfdec38cfca5b5a82d0af5f03c59066f3d6/160375B; stdoutdd144dae/234068B,stderr948aa152/965B. It fails install_policy line212 before kernel_before is populated: OLD_KERNEL is malformed63-character literal missing d from actual ...0dc5db41.... Actual immediately preceding runtime/native/UI observations all equal the correct64-character45bb34e8f897feb344c9b18e895a2d07f8a09a0dc5db41b78331276140a8167f. effects=[]; no module invocation, CIL replacement, receipt replacement or policy change occurs; final strict closure passes. This is a local constant transcription defect, not observed kernel drift. Original failed flags remain false. Fresh policy-v2 must derive actual digest, validate every digest shape before effects and use a fresh scope.

### Checkpoint229 — actual policy-v2 and new-policy environment pass (2026-10-24)

Fresh policy-v2 ACTUALLY PASSED14.843177s, original3885286/start436613198 rc0/reaped/gone, actorf23cf030/75159B/caller1d1103c0/70993B. Protected source24-selinux-policy-installation-v2/RESULT.json SHA256f59ced9828edb00877e1dfc4a4da13f31dd9b701618019696a854f1b53336ec8/228190B; stdoutac8f777f/284772B. Correct64 old digest joins actual runtime; all digest constants/pins reject malformed lengths before effects. Failedv1/no-effects remains held unchanged. Original semodule invocation succeeds once with exact singleton CIL delta; kernel before45bb34e8f897feb344c9b18e895a2d07f8a09a0dc5db41b78331276140a8167f, after2416555967f0018a7b35551122806c6d55540cda8c0098d993a108ca78653915.

Installed CIL1d9d7f3165dbaf1c416022a02dffd7a97b04f572ed014b226cb6689512bc8cd3/17860B is root0644/code_t inode75873752. Installed /etc/hfcache/host-helper-selinux.json SHA256725f5a0cf7e3d07404a5a05a4a452a91791e3145940579b29efaadb7693e246d/1091B is root0644/conf_t inode75873480; archive=nfs_t is derived from exact actual original owned-NFS metadata. Old global CIL+receipt are preserved through fresh v2 NOREPLACE names with original inodes/bytes/SIDs. All other module checksums and boolean values remain unchanged; services/timers/credentials/fcontexts unchanged. All local/guest inputs rejoin/close; key metadata and final strict closure pass. No new policy/source broadening or production action occurred. Future consumers require actual new receipt/kernel; before-policy image evidence remains explicitly historical before-policy proof.

New-policy environment ACTUALLY PASSED27.620952s, original3886096/start436636003 rc0/reaped/gone, actorf4ea57f5/54488B/caller4221f275/70945B. Protected source24-environment-preparation-v1/RESULT.json SHA256fa731880fe52fa752e9b22d1bdcd3d3b2ef617bf433ccb44204e1cf65f0a3837/338328B; stdout44c5a24b/389086B. Actual policy-v2, UI completion-v1, readiness-v2 and source24 proofs join before staging. All108 installed package leaves are held in a proven readonly projection; exact194 browser files/50 directories and inherited preserved source records match. Actual kernel24165559/receipt725f current, selectors remain absent, no application start, final strict closure and all input joins pass.

Optional post-policy bus-probe-v1 was locally bound but never executed: root review caught its fictional loaded user-unit expectation before any guest call. Fresh v2 derives actual fixed five-property row from policy-v2 user-manager proof: hfcache-api.service/not-found/inactive/dead/MainPID0; no artificial unit is loaded. Its original execution FAILED1.579793s, original3886292/start436640617 rc1/reaped/gone. Protected source24-postpolicy-bus-probe-v2/RESULT.json SHA256a12a0bf5b6ee04953ae4c1c660540da393060222b0e1e2abcfa1dd75717b0792/32193B; stdout5d1ab6df/138431B. It holds actual new policy/global records/kernel and reaches initial owned-unit show, then KeyError at probe_command line530 because actual collect() row has no proc_absent key. Failure precedes owned-unit creation/start/worker/effects. Final fixed-role closure passes; original guest false/KeyError and outer/local failure remain preserved. Fresh v3 must use actual original PID/start identity closure and real collect-row schema; no unit/browser/operation replay. This optional probe establishes no API/peer/functional acceptance.

### Checkpoint230 — rootless staging/profile proposals pass; fresh authority correction required (2026-10-24)

Rootless015 first stage ACTUALLY PASSED5.646191s, original3886957/start436658429 rc0/reaped/gone, actord95833a6/61904B/caller2776db83/70963B. Protected source24-rootless015-stage-v1/RESULT.json SHA2567640f2efc700df6d07b8b53481d3480a26a21c357ec3ee907c3769665e45e8bf/86848B; stdoutd0c8f480/181585B. Actual full image-build receipt09eaebe7/585697B and its original upload executor, UIcompletion ec53, policy-v2 f59/new2416 and ENVfa7318 join. Original stage/render checks pass for software0.2.14/deployment0.2.15; no application start, selector switch or installed host acceptance inferred. All input joins/final strict closure pass.

Both new-policy profile proposals ACTUALLY PASSED5.454994s, original3887202/start436664302 rc0/reaped/gone, actor53a96daa/48075B/callere191d5db/70963B. Protected source24-profile-proposals-v1/RESULT.json SHA256a2a60456380c8d1c8b014dfba350d68a8a57c889152f9964b33042b9f1750d03/128193B; stdout956b811b/210485B. Exact native0.2.14/rootless0.2.15 pairs, current kernel2416/receipt725f, unchanged E0CB bootstrap, previous303 control inputs, original six permission bits and old failed profile03b77543 are verified. Temporary selectors are preserved with NOREPLACE/absent afterward; all input joins/strict closure pass. No application service, global policy or credential is installed by proposals.

Optional bus-probe-v3 original3886770/start436653524 FAILED1.766958s, rc1/reaped/gone. Protected source24-postpolicy-bus-probe-v3/RESULT.json SHA256e6893bd4bf36de9e2db42c880445972197f51e60523dbdc58554fac03197eaf2/48357B; stdoutd398f727/151094B. Actual collect-row closure is corrected using exact PID/start and prior-v2 failure is retained. The new owned unit is submitted once, but ExecMainCode1/ExecMainStatus203 means the isolated interpreter never executes the worker or fixed user-manager show. Worker result remains0B; JSONDecodeError is collection of that absence, not a bus result. Unit MainPID0, original numeric PID172501 absent, owned cgroup physically absent/empty; original normal stop and reset-failed are observed and fixed-role strict closure passes. No API/peer/functional acceptance follows. The optional diagnostic's false result is retained and further probe repair ends; no policy/hardening grant or production behavior changes are justified by this different interpreter/unit setup. Required installed-helper browser/fault/isolation/lifecycle tests still must run.

Authority35 first execution FAILED3.485406s, original3887557/start436674722 rc1/reaped/gone, actor1656963a/412625B/callere70cc299/70946B. Protected fixture-authority-v35/RESULT.json SHA256cc285ad54e4d326719db962144d91cc5f3d9e4bb11108992bdcbf575c3b53ce8/103875B; stdout6022cbe2/196982B. Full local preflight1361/278inputs/SSH119904 stays below unchanged120000 cap. A first caller-builder lookup of nonexistent v1 basename refused read-only; corrected actual v4 basename executed once. Actual new manifest/launcher/controller36/control36 files are partly published with empty-before-label-before-bytes proof. Original controller load_control fails selinux_records line253: control=deepcopy(old) retained old control.selinux hashes despite actual new CIL1d9/receipt725f held by the actor. An initial review suspected a second archive-label mismatch; exact frozen controller36 audit corrects that suspicion: its map already has archive=nfs_t, so controller37 keeps it unchanged. The proven failure is the copied old control.selinux pins. No application service or sudoers admission is reached, no global policy/credential change occurs, strict closure passes; original false flags/partial files remain unchanged.

### Checkpoint231 — corrected authority36 passes; native30 real functional run active (2026-10-24)

Fresh authority36 binderb064189e/28300B full actual prepublication prefix and independent review pass. Exact new receipt reconstructs to actual725f/1091B; unchanged controller37 selinux_records and both deployment_selinux validators run against actual saved root metadata before output. All11 constructed-control fields are accounted for; only intended7 change, original schema/kind/guest/base_processes and ordered303 prefix are retained. Proven correction is copied control.selinux pins; exact controller36 already used nfs_t, so that map is unchanged. Expected control508c2898/manifestb5beaeff match actual publication.

The source24 actor130aad236c7b190a340c5e1d36e8ac450f58cb46df805b9a74a0f54fdb7dc53d/416640B would exceed the original SSH cap with zlib9. A fresh lossless BZ2+b85 caller preserves every byte and the existing length/SHA checks, namespace/compile/exec/try-main suffix, stdin and closure. Base24d4edf7/71613B differs from ebc2d083 only by added codec callback/one callsite; exact actor decode-only roundtrip and wrong-actor rejection pass, independent AST/envelope review passes. Specific callerc7b8e57c3cb7f5d6741236a3a4b9eaf99222b69f7a4aa4859c5bb6f769929e31/71585B passes1361-source/278-input/QEMU/FD preflight, quotedSSH102483 below unchanged120000. No acceptance, source substitution, cap relaxation or replay follows from compression.

Authority36 ACTUALLY PASSED4.543562s, original3890123/start436768583 rc0/reaped/gone. Protected fixture-authority-v36/RESULT.json SHA25696b66a266ac4bb25b2738b0944a6970a59d6e80b1e573b002da036b9b5b55cf0/138071B; stdout0f1244ed/222873B. Fixture UUID94afc4f4-5077-42c6-aae0-2ca491f3c5d0 is test authority identity, not an archive publication replacement. Controller37 SHA25698e67de000eaf297c33ebb77210840a5b4aa6a045c7505be619f7f797db035c3/118954B; launcher76be5c4b/199793B. Control /opt/hfcache-web006/control-v37.json SHA256508c2898434dfe4fcbbfa62e340bbc52ad8761f4f5f734c1ae69c92ab301968d/60642B, inode43344824/root0600/usr_t, has326 actual input rows preserving original303 order. All19 partial35 published rows/control36 and failedcc285 proof are separately held unchanged; none is promoted to the oldbase. All21 fresh files are labelled while empty; executable role headers, actual current globals/deployments before publication, controller_load_equal, visudo, budget, selectors absent, secret0, kernel2416/key metadata, all input joins and strict closure pass. No application start/host functional acceptance is inferred.

Native30 authority36 binder615b5592/11282B actual prefix and independent source/scope review pass; standalone normaled7ca479 is byte-identical to its postrun embedding, exact manifest36/errors37/proposal/14+15/currentkernel2416. Bound functional actor7a7e8fa1c13242020d8a019640a5da895f4ad52200c3b63db2d3aa42e0ab5068/37390B and callerbfc22e96d50c5ce84c720c6f5293f5c1681806b0a83533f52c79b67b2faf7fdb/70981B pass1361/278inputs/SSH22543 preflight. ORIGINAL real functional execution is RUNNING3890447/start436775404, local stem web-006-source24-native30-functional-v1, exec session34059. It must normal-wait/reap/drain; no pass or original child outcome is inferred from start. This exercises built UI through real trusted-TLS Caddy and installed API/helper; required browsers/modes and denial assertions remain pending until actual result/postrun evidence closes.

### Checkpoint232 — native30 real normal acceptance passes; rootless35 original run active (2026-10-24)

Source24 native30 ACTUALLY PASSED342.416869s, originalouter3890447/start436775404 rc0/reaped/gone, originalrunner172816/start37658220 rc0/reaped339.599722s. Protected source24-native30-functional-v1/RESULT.json SHA2562c634c1b45d03b6e8edfde3bee7f10114051c27ad78cc4089ebeed6f9bc3bfc1/448395B; stdoutd10eaff8/386355B. Actual SUMMARYaa72ec20a54ef64a9f4e108d9f18ff9ee8ce2d5cda2d5a217023fd547b81dc05/381308B under owned source24 authority36 native30 workspace records4 modes/3 engines,33 passed host assertions (baseline7/helper-down2/restarted1/timeout1 per engine),12 actual untrusted-CA refusals, all attempts1,0 required skips/retries. Baseline/restarted supported, helper-down refused/timeout unavailable as expected; all browsers/descendants exit0/close without forced close. Actual native normal acceptance true; rootless/dedicated acceptance false/pending. Fresh current kernel2416/newreceipt725f, original303 prefix, key metadata and all input/fixed-role closure checks pass.

Postrun ACTUALLY PASSED1.763926s, original3891575/start436812278 rc0/reaped/gone, actorda9b61f6/54578B/callera4984286/70972B. Protected source24-native30-postrun-v1/RESULT.json SHA256c4bc0c48f8b0f3b403531f9a03c9dbe56045f6bfd75e6341d9ebc5abfa7d9143/130509B; stdoute93706e6/204357B. All8 normal records/four TLS epochs and original handles revalidate/close, all local/guest inputs join. No original runner was replayed.

Native30 ordinary preservation ACTUALLY PASSED1.881608s, original3891786/start436817893 rc0/reaped/gone, actora431e7a9/34052B/caller0a681b97/71005B. Protected source24-native30-preservation-v1/RESULT.json SHA25663345a0861f86a5dbf21b14323344806b28821d6917631b47ba985fc6cc84bc2/55615B; stdout9f0e026b/155437B. Actual Basic inode118491253 and three original selectors are preserved with NOREPLACE after original cohort drain checks; four current paths absent afterward, strict/key/empty-secret checks pass. Exact local stem web-006-source24-native30-ordinary-preservation-v1 differs intentionally from protected scope and is supplied explicitly to follow-on binders. An initial invalid phase name preservation was rejected by argparse before reads/output; correct preserve phase executed once.

Rootless35 secret baseline ACTUALLY PASSED1.560221s, original3892082/start436827146 rc0/reaped/gone, actorcf16f13c/40090B/callerd4549720/70983B. Protected rootless-secret-baseline-source24-authority36-normal-v1/RESULT.json SHA256e15cbe553440ace15f2427cc37ab28af045a2d9b783c9d20727db7291707020e/19617B, using original producer's sorted JSON serialization with default separators/newline. Local stem web-006-source24-rootless35-secret-baseline-v1 is used directly, never aliased/re-serialized. Actual native/postrun/preservation, authority96b/current326, source24 and key/newkernel facts join; no secret payload/digest, explicit secret creation/removal or application start establishes acceptance here. Stock secret-ls metadata/lock initialization remains explicitly recorded.

Full actual rootless35 coordinator preparation and independent scope/27 historical DTO checks pass. Binder-v5 1bea26ca/13851B binds exact actual chosen preservation/baseline stems; root actorb012000e/131517B embeds observerc47d48d0/51891B and runner82959e65/41739B. Specific caller578406e839a5bd6dc5eb96a259a837e41c8852d39652cf0fb8f1cce6dca33051/70979B passes1361-source/278-input/QEMU/FD/SSH48757 preflight. ORIGINAL real rootless35 normal coordinator is RUNNING3892604/start436841476, local stem web-006-source24-rootless35-coordinator-v1, exec session46480. Its checked sequence must obtain actual ARMED/watcher hashes before the original runner; those runtime pins are not invented. No current runner/watcher/browser outcome is inferred. Root is sole serial guest executor until original normal wait/reap/drain.

Checkpoint232 continuing source audit: the still-running rootless35 fixture has stale source23 inventory5d968b60 comparisons/producer values despite current source24 inventory92a6cdd0. Exact actual-manifest audit b12b8d18/13264B scans39 active modules and decoded embedded source:5 direct sites (normal read/public projection, observer ARMED, runner check/public projection) plus2 embedded normal copies, no other active old inventory/snapshot/canonical literals. This source finding does not invent a runtime outcome or no-effect claim; original3892604 remains owned/running and will finish/drain normally. Corrected unbound templates and seven actual-manifest predicate/producer tests pass (report48311e06/4320B); originals are untouched. A fresh cohort/scope will be chosen only after original failure/drain/state is actually observed. No source/gate change or replay is authorized by the fixture correction.

Four actual source24 native30 ordinary-functional rows are now appended to AUTH08/HOST01–03 ledger cases, artifact local-result SHA256db00d52405ca07a8361bc1f9502bc5b58ba032f06fb479e5c235b6dcab009d61. Each explicitly limits its coverage to native ordinary behavior; all4 case statuses remain pending for valid current rootless, both-profile dedicated isolation/fault, applicable fresh MAC attribution and exact lifecycle/cleanup. Errno-only denial is not current SELinux attribution. Required fresh seccomp-filter-count helper metadata is being prepared after genuine normal drain/retirement using the canonical installed helper unit, not the failed optional interpreter probe.

### Checkpoint233 — original failed35 closed; fresh failed-state proof pending (2026-10-24)

Original rootless35 coordinator FAILED601.597356s, outer3892604/start436841476 rc1/reaped/gone. Protected source24-rootless35-coordinator-v1/RESULT.json SHA256581a07b4c1377ffbed281bb0d6c6473a3bf4a540211b1e91812965e9e7d25d93/39565B; stdoutf6ae4f52/144451B,stderr948aa152/965B. Runner178324/start37724278 rc1/reaped0.096582s with stdout0/EmptyOutput/no runner JSON, original stderr848B/SHA0cbe7887 retained privately. Watcher178323/start37724250 rc0/reaped600.197731s; its successful_ownership_proof=false/all_sources_rejoined_and_closed=false/error_class=ValueError/ownership=null remain false, notwithstanding zero process exit. Both original PID/start identities are freshly gone/numeric absent. Coordinator final strict fixed-role closure passes and held_release_failure_classes=[], while original feature/all-input/outer/local failure flags remain false. No normal rootless acceptance is inferred.

Exact source audit shows execute line382 rejects actual manifest inventory92a6 against old5d, before WORK.mkdir385/result-state386 and checker/controller-start dispatch391. All7 stale direct/embedded guards/producers are covered by actual-manifest tests48311e06/4320B and active39-file auditb12b8d18/13264B; corrected candidates remain unbound and originals untouched. Fresh readonly failed35 readiness will join original protected failure/ARMED/private stderr hash and export only bounded traceback frames/class, then measure runner WORK/output absence, exact control37/generation state, four current paths, known/unknown secrets, key/newpolicy/kernel and strict closure. Those live observations remain pending; source reasoning alone is not promoted into fresh no-effect/state acceptance.

### Checkpoint234 — failed35 state/traceback proof passes; fresh rootless36 selected (2026-10-25)

Fresh readonly failed35 readiness ACTUALLY PASSED2.437954s, original3895785/start436950556 rc0/reaped/gone, actored97f967/68230B/callerc07937ae/70993B, full1361/278/SSH30764 preflight. Protected source24-rootless35-failed-readiness-v1/RESULT.json SHA256f77878c7018a8a24bcbef56d615defb0f16ce351df49c0d0237245b2c18ab3f2/224729B; stdoutfe6f9d15/288143B. Full actual DTO prefix and independent review pass; root separately tests all later authority/postrun/failure DTO key guards before execution. Original848B stderrSHA0cbe7887ad3a43d269520feeff961b00f685a36702a811f0a379d9e2e0b1c172 is held/rejoined; only class/function/line projections are exported. Actual traceback ValueError execute382/need35 confirms the original pre-WORK inventory check, with main433/442 and bootstrap6. No raw message, authentication, argv, payload or audit body is exported.

Original failed581a/39565B and wrong-inventory ARMED/runner source remain unchanged and false; both exact original PID/start pairs are gone. Actual source24-rootless35-functional-v1 runner directory and public browser workspace are absent; RESULT/SUMMARY absence follows their actually absent parents without creating them. Controller37 generation directory contains only the exact retained native30 stopped generation. Known and unknown secret counts are0, current selector/deployment/policy/Basic paths all absent, all326 control files held full9/SID/hash and unchanged, key metadata matches native30/authority36, actual policy/kernel2416/receipt725f and strict before/after/final closure pass. Only the new evidence WORK/receipt is written, no role/helper/installer start, service/policy/credential modification or secret payload read/hash. No original cohort is replayed or promoted.

Root now selects fresh rootless36 while retaining the same correct authority36/controller37/control37/UUID94afc4f4-5077-42c6-aae0-2ca491f3c5d0, native0.2.14/rootless0.2.15/current source24 policy. New normal baseline and ownership use authority36-normal-v2; workspace source24-authority36-rootless36-v1 and protected source24-rootless36-functional-v1/coordinator-v1 are unused new scopes. Actual failed-state proof f778 is a required preserved prerequisite. All seven current inventory predicates/producers, including embedded normal, must use actual92a6cdd0;826613a0 snapshot/71cdbc2b canonical remain exact. Corrected templates pass seven actual-manifest checks; no source/gate change follows. Future normal/cleanup/isolation/fault selectors are being ported to actual new scope, with positive pins still UNBOUND.

### Checkpoint235 — fresh rootless36 baseline passes; original real cohort active (2026-10-25)

Fresh rootless36 baseline ACTUALLY PASSED1.581804s, original3896436/start436972901 rc0/reaped/gone, actor49861d0a/42539B/caller3297aa6a/70983B. Protected rootless-secret-baseline-source24-authority36-normal-v2/RESULT.json SHA256089eef0af9203859d017b008261cba0c2533c223363f678c545213f54859fd43/20215B; stdout40ed46a8/135805B. Exact f778 failed35 recovery is required/held, including original false/None ownership flags and actual execute382 traceback. Actual current326/native30/key/kernel/secret0/native-only generation facts join. Original baseline/ARMED/runner/coordinator35 remain untouched; the new normal-v2 store has no original-cohort replay. Local actual stem web-006-source24-rootless36-secret-baseline-v1 is used directly by fresh binders.

Full ACTUAL coordinator preparation8f58182e/8277B and independent eight-model scope/manifest audit pass all seven current92a inventory guards/producers, including observer ARMED and normal public projection/embedded normal; projected8266/canonical71cd remain exact. No active old5d, rootless35 workspace/postrun or normal-v1 selector survives; failed35 history is retained only through explicit failure prerequisites. Same authority36/control37/UUID94af/native.14/rootless.15 are reused under their actual successful receipts, with new rootless36 WORK/workspace/ownership normal-v2 scopes.

Bound coordinator0a08db455c8b625f6772861f25ef8f0b521b9642e349392b1d7e75a16979b409/131517B embeds observerc51d6bd8/51891B and runner1b0c17a4/41739B. Specific callere109254a93c646eaf1ba4cf221b78c8247d2c1d68a009d9f949016100170cacf/70979B passes1361-source/278-input/QEMU/FD/SSH48766 preflight. ORIGINAL real rootless36 coordinator is RUNNING3896941/start436990914, local stem web-006-source24-rootless36-coordinator-v1, exec session58232. Its original checked ownership/watcher/ARMED sequence and actual runner result must close before any acceptance/cleanup claim; no current ARMED or browser result is inferred. Root is sole serial guest executor.

Required follow-on selectors are ported to unused rootless36 normal preservation/postrun while staged native fault model/publisher bytes stay unchanged. Both dedicated collectors retain unchanged64-FD reserve and original limits with observed category deltas before cold start; control326 rows are read/closed sequentially, not presumed326 retained descriptor pairs. No unmeasured cache/budget relaxation is introduced. MAC attribution remains a separate bounded original-event observer after actual positive isolation, with exact actor/window/PID/inode/type/permission joins, conditional operation-local metadata when captured and explicit absent/ambiguous fields; no secret/log-body export or probe replay. Canonical helper seccomp-filter observation is prepared for after genuine successful rootless drain/exact retirement, before ordinary alias preservation. All future positive pins remain UNBOUND until actual results exist.

### Checkpoint236 — fresh rootless36 real run failed; bounded original diagnosis pending (2026-10-25)

Fresh original rootless36 coordinator FAILED83.559951s, outer3896941/start436990914 rc1/reaped/gone. Protected source24-rootless36-coordinator-v1/RESULT.json SHA256681e0035436231d9a361ca23b3cf5473def2898967c87b87a7b92b0a8dd557f1/68006B; stdouta90a463a/165326B,stderr948aa152/965B. Original runner178503/start37873708 rc1/reaped81.854208s; original watcher178502/start37873681 rc0/reaped82.142592s. Both exact original PID/start identities are gone/numeric absent, held_release_failure_classes=[], final strict fixed-role closure true. Watcher successful_ownership_proof=true/all_sources_rejoined_and_closed=true/error_class=null establishes exact six secret/container/process ownership. Original runner result all_guest_inputs_rejoined_and_closed=false/error_class=ValueError with rootless_start_or_secret_retirement=true/secret_retirement=false; coordinator/feature/all-input failure flags remain false. Corrected source92a pre-create predicates passed and actual application start occurred; no source25/product-policy defect is inferred before actual saved diagnostics.

The actual new generation is40303bab46424eddba4165dc0dd23238 under controller37. Browser/startup/generation/CID drain/Basic metadata and bounded original AVC+SYSCALL diagnostic actors are being prepared from passed failed34 readers with exact failed681e/currentauthority36/control37/normal-v2/kernel2416/CIL1d9/receipt725f pins. Only safe typed metadata is exported; no raw authentication/argv/EXECVE/proctitle/secret/log bodies or speculative audit2allow/grant changes. Browser diagnosis will be stdout-only, not an invented protected RESULT. Failure-only six-ID retirement/opaque preservation/four-path NOREPLACE cleanup waits actual original drain and credential metadata; no force, replay or normal lifecycle acceptance is inferred. Current secret/current-alias state remains retained until measured.

### Checkpoint237 — failed36 exact cleanup passes; broker journal attribution pending (2026-10-25)

Bounded original metadata reader ACTUALLY PASSED0.950090s, original3898317/start437037468 rc0/reaped/gone, actorcfbfd818/27858B/caller44152517/71002B. Local web-006-source24-rootless36-failure-metadata-read-v1-result.json SHA2566ffef927582361eba7515d43430d34158c95ceb36edca4122b1c5375be11f359/189518B is stdout-only, not a new protected RESULT. Startup is ready/bootstrap200/read_polls1/secret label gates passed; actual baseline report0fea9be23eec3d101eb93b8caf25288f9c73c4dec38a06e1cb3c0e86c8921723/69365B shows all3 engines unavailable vs supported before case rows (0cases), all browsers/descendants closed/exit0 without force; all3 untrusted TLS refusals pass. Trusted container exit1 is drained; report rejection does not establish an API/worker crash. Original generic62B checker footer retains no exception errno/cause.

Original gen40303 stopped recordbe6bc0bc/73360B and public RESULT05b8e94b/16341B prove ready/stopped/cleanup_unknown=false, all69 original process pairs gone, exact3 CIDs6346da2d9e2562603f938ab92bf958aee55a84cb98cf8e7cceaed5e64c66557d,cf3eace537e409ca454ab76fcc19cbc0e850047179481a3da83c6ab9761e23b3,cc012adc046bf20c5f974d5636e637dae5252c6518682a7d12d3748c90b80f89 exited0/PID0. All6 original wait0/exists1 observer handles are EOF/reaped/gone without unknown drain; cgroups empty/endpoints refused/inputs unchanged. Original Basic inode118903461/dev64515 UID/GID983:9830400/secret_t is captured metadata-only; key metadata/currentkernel2416 stable.

Bounded AVC+SYSCALL reader-v1 ACTUALLY PASSED0.852084s, original3898546/start437042752 rc0/reaped/gone, actor717edbbd/15549B/callerdde67d63/71014B. Stdouteca7ec96/149375B and local result remain stdout-only. Exact window1792901355..1792901437 lies fully within retained audit extent; original secret gate decisions are48/48 and actualkernel2416 remains unchanged. All38 kernel helper-domain events have exact full timestamp/eventID/PID joins:24 exec_t file ioctl/syscall16,6 init_t socket ioctl16,8 cert_t directory search/openat257,all enforcing/EACCES. Zero fixed-systemctl or connectto events occur. These optional ioctl/certificate events are not assumed causal and justify no grant. Historical start ticks/unit attribution are not invented.

Fresh USER_AVC reader-v3 ACTUALLY PASSED0.890076s, original3899612/start437072757 rc0/reaped/gone, actor41c1c234/19877B/callere40c441f/71014B. Stdout9548e46b/149600B; same38 kernel rows and0 USER_AVC records/matches. Frozen unexecuted v2 remains retained; v3 only corrects reporter-PID wording so absent subject PID is never invented or equated. No userspace SYSCALL pairing is required or asserted. Pinned upstream dbus-broker-v36 source confirms SELinux send_msg checker uses NULL auditdata and fallback receiver context, broker reporting uses its own UID, and util/audit may choose AUDIT_USER_AVC or stderr depending on actual effective CAP_AUDIT_WRITE. Independent primary assessment84ee6a71/6497B records exact source bytes/anchors and pre-driver/Hello extent as source inference only. Zero audit-file records does not prove send_msg allowed. Current broker70560/start6647884 capability and exact original-window fixed-broker journal projection are being prepared, no request/cohort replay or policy patch.

Failure-only exact6ID retirement ACTUALLY PASSED5.411976s, original3899104/start437058609 rc0/reaped/gone, actora3149078/99166B/caller8a39ca29/71017B. Protected source24-rootless36-failed-secret-retirement-v1/RESULT.json SHA25666dd3700a350c279f1d4f610eacef63a376fdae494174f23d8339dcfe9f6472c/125477B; stdout927aefae/209589B. Fresh actual69-handle/3CID/6observer/exact-owner checks precede durable opaque whole-store backup and six individual nonforce ID removals/intents/rechecks. Final known/unknown lists0; no name-only/unknown deletion, individual payload read/hash/export, replay, helper/service reset or policy action. Original failed31–36 false flags remain unchanged; failed_cohort_exact_ID_retirement_completed=true but normal_owned_six_ID_retirement_completed=false and normal_secret_lifecycle_acceptance=false.

Four-path failed36 preservation ACTUALLY PASSED1.992778s, original3899922/start437082093 rc0/reaped/gone, actor7ac14ad4/42881B/caller53d63153/71002B. Protected source24-rootless36-failed-preservation-v1/RESULT.json SHA2563a7f382e3677ac5882e3344bed5a9fb382428722febc102164a2f19aa1b8b966/59341B; stdout4b0b5c33/158662B. Original Basic118903461 plus selector.15/deployment/policy aliases preserve inode/bytes/SID through NOREPLACE; current four paths absent afterward, secret0/key2416/strict closure pass. A local faulty preservation binder-v1 prepare wrote only ignored BINDING metadata before returning None; no actor/guest/alias effect occurred. Fresh binder-v2 b70f2bfe has verified pure prepare and publishes actual7ac/BINDINGb5eae941 once. Original metadata-only report retained; never treated as guest evidence.

### Checkpoint238 — measured broker-message correction applied; source25 captured/full gate active (2026-10-25)

Exact original fixed-broker journal reader ACTUALLY PASSED0.910336s, original3901108/start437115229 rc0/reaped/gone, actor77433fdb/21338B/caller5560d5c6/70996B. Local web-006-source24-rootless36-broker-journal-read-v1-result.json is stdout-only; stdout9f5c7dd9/123727B, no protected diagnosis RESULT invented. One fixed boot/PID70560/UID983/window1792901355..1437 readonly journal query records7 Enforcing helper_t→unconfined_dbusd_t:dbus send_msg denials. Exact current broker70560/start6647884 context matches target; CapEff/CapPrm0 and current CAP_AUDIT_WRITE=false explain possible stderr routing, with no historical capability claim. The reporter PID does not establish client PID or method/Hello. All held failed36/gen/policy/currentCIL/receipt/kernel2416 facts rejoin; query actual PID/start, EOF/closed/wait/reap/original gone proofs pass. No request/replay/service/label/credential/policy action or raw MESSAGE/argv/path/payload export occurs.

Source-only primary evidence supports driver authorization with NULL receiver/fallback context and auditdata=NULL, and USER_AVC or stderr routing. Draft-v3 .scratch/web-006-source25-session-broker-message-DRAFT-v3.patch SHA256e8abfcb4df108315beed5f4707365f9238eff74badd3e39fa1c84f592e6ddca2/15307B passes44 mirrored policy tests/6mutants, independent38 previous cases/9 additional mutations, Ruff/applycheck; preflightcb2208bf/5647B and independent875df565/5575B retain exact primary bytes and threat review. Root verified all1361 frozen source24 hashes/modes/HEAD immediately before applying exact reviewed patch. Source24 freeze ends at application; all its receipts remain exact historical evidence, not relabelled.

Exactly7 canonical files change: INV020,ADR150,host/security/troubleshooting contracts,CIL and strict policy tests. CIL SHA256a051f2541f0a5c8719a9e8d0c8ee36ce26ac0d3c4e94415cec847fec05188d8f adds only one forward helper-to-unconfined_dbusd_t dbus(send_msg) form; no other policy form, peer, reverse,acquire_svc,certificate/ioctl/private-socket/payload/capability/transition grant. Contracts explicitly state type-wide IPC authority and fixed UID/address/closed argv/parser/original peer/manager checks as application restrictions, not MAC method filters. Actual method/client PID remains unclaimed. Actual focused command rtk proxy uv run --locked --extra server --extra mcp pytest -q tests/unit/test_host_selinux_policy.py tests/unit/test_host_peer.py PASSES144/5.40s. Ruff check/format-check,docs207human/27helpers,git diff --check pass. All108 Python package/96 Web source bytes remain unchanged; canonical product version0.2.2 remains.

Actual capture25 script43673381f6467dff7f89411d4939c07564b01b4fa87e42f39d7bf5a42a4f3b94/17681B passes full previous24/current preflight before reserve/write. .scratch/web-006-source25-capture.json SHA2564e191197123d998c1b1f2f721df812d197ada1ebb75afec2ce6186c2e2336e99/684B captures1361ordinary files, HEAD07d10e0 and snapshot59f78c03a543b59014cc10d8208e361e841934a8ca4f4616e2473bb0eea15139. Inventory .scratch/web-006-source25-local-v1-7w8aro_l/source-inputs-v25.json ddf963bf2d5eadb0e269a036c231027061d8bca4bcde0f33d1a18c33030fa3b5; tarbe609c8fcc38a4da6328070dd6018f2e98159a5c393a418910b1d68b5ec731a4/17766400B. Full members/hashes/modes/current checks pass with exactly7reviewed changes. Freeze25 is now active; only5bookkeeping exclusions may change.

Two-field projection script ecc142fd/6452B ACTUALLY PASSES before/after archive/member/current checks. Projectionf7fcdaeaf5f68b18d90688f998b8fb9f3fe503df287c3001d0225f77dc93e919/245249B gives snapshot753a53343918772182b3cf518b3264ddc77b5ab687806ceffd2808a88a10bbc1. Only pyproject/uv.lock selfversion0.2.2→0.2.16 change; all other TOML/source bytes unchanged. Input09cd3fc54db333b1c9de65f6a5fc3548b99fa5518f8e5c1fea7524082c3cdbd7; projected tarc1860f3bf8ae1d0c23b491700c59daa37e2324031f4c1648181a6ddf6f51efbe/17766400B. Literal legacy gate22_outcome_not_inferred is intentionally retained; actual gate25 proof is separate. Future native.16/rootless.17 artifact/install identities remain UNBOUND until real builds/receipts.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

Concurrent exact readonly assessment admission explicitly uses historical gate24, not gate25 acceptance. V1 exactcaller53ba6110/72333B ACTUALLY FAILS1.452713s, original3905479/start437202541 rc1/reaped/gone. Result is stdout-only createdFalse: source16_quiet collected before evidence WORK existed, private-channel publication raises FileNotFoundError. Original readonly manager query180892/start38085307 rc0/reaped0.244626s is recorded BEFORE retention failure. No restorecon/installer/application/label action occurs. Fresh v2 fixes creation order and exact admissionff16f07f/72333B passes1361/281/SSH19546; actual execution3910037/start437239175 FAILS1.544946s beforeWORK/commands at retained_control_inputs138 because it wrongly rejects duplicate immutable paths. Actual326 source records preserve policy27RESULTx2/browsertemplatex2/provisionauthor-v4x3 with identical hashes. A second preflight finding is the specific retained source15tar17725440B exceeding the generic16MiB bound; corrected guard must preserve the complete326 ordered rows, reject conflicting duplicates and use the same exact historical path/SHA/size exception as passed f778, not broaden application limits. Original v1/v2 stdout failures remain unchanged; neither has a protected assessment RESULT. Freshv3 actual-row/size/call-order tests and new WORK/admission are being prepared. No native.16 installer or assessment restorecon has run.

### Checkpoint239 — source25 strict gate and measured preservation pilot pass (2026-10-25)

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

Fresh readonly assessment3 actorc5e9778f/callerffcc2912 PASSES8.631137533s, original3913907/start437272046 rc0/reaped/gone. Protected source25-native016-preinstall-label-assessment-v3/RESULT.json SHA72269fffd02d978543748435a243f0c246ac8168a34272af9d4423cd406bc2d8/571968B. Original restorecon180991/start38154941 rc0/reaped4.576600536s measures exactly156 SELinux-user-only rows (52 each .11/.13/.15;0 .12/.14/outside). Actual326 ordered control rows intentionally preserve duplicate paths with matching hashes; only exact retained source15tar uses the historical size exception. Both earlier failed assessments retained; no installer executes.

Measured private-MNT pilot actorb13774dc/caller954253d2 PASSES10.615112162s, original3916610/start437300771 rc0/reaped/gone. Original child181053/start38183757 rc0/reaped3.884938322s. Child-only MNT/root-private read-only/nosuid/nodev/noexec shadows cover only measured old rootless releases. All216 native package leaves, all retained rootless leaves, all326 control inputs and outside host/parent/pause mount tables/namespaces remain unchanged. Key metadata/old kernel2416/CIL1d9/receipt725f unchanged; four current paths absent, secrets0. Installer disabled, native.16 absent before/after, functional_acceptance=false. This pilot is preservation evidence, not an installation or MAC/feature acceptance.

### Checkpoint240 — actual artifacts and source transfer pass; readiness-v1 fails before installation (2026-10-25)

Canonical artifacts SUMMARYa77a3874, wheel089ca3ce6e147f676a94479b72919faa4f9f12a1c53de831bd75f60d36f73a20/500437B; fixture SUMMARY7036fc6addb00434072585414e75ddf5824085c5d38c0b2d6a215898d020273e, wheelf5c68dd5e6234d2b1bc2c7acbcf22a3fc2e329e4f4e17fe52fb209eb1bde151c/500451B. Fixture original3925523/start437351838 rc0/reaped/gone17.564987s. Both UI independent builds match within their own source/version scopes.

Shared API/UI image original3926098/start437356020 rc0/reaped/gone30.478866s, builddd590e9e3b8309cc742f42720a5605bfe1d2e347373eae40e1dc79829c0f97f5/585697B, exact image sha256:04725627d282cc67c500243f3d778640f8212399bd2b608ad5980422a14f7b81. Both FROM stages are registry.access.redhat.com/ubi10/ubi-micro@sha256:87a27d7189dbae57f63db332a11de17f7ed6be91cdc956731c30141af2e8dc49, CA-data-only donor unchanged. Genuine guest ancestry/absence/confinement audit remains pending. OCI export original3927465/start437360583 rc0/reaped/gone5.665714s.

Source transfer original3927597/start437361476 rc0/reaped/gone35.505506s. Protected source25-fixture-transfer-v1/RESULT.json SHA256bd6dcc24d162df0454cf141322000c70aa00166d2735528cf9bdbdcdbf15a6cd; localcfb730de3a5c899f5820027f309eac73031292a242c23b9619463f3027647780/1108044B, stdout044244d0e6d97a30040a96b2d26c092f78da658ffec0c6ff6ede9cc922216801/817594B. Passed/all-input closure true; packet648df6fe/36382720B; old sources not written/relabelled, no service/selector/policy/credential action, no original failure promoted/replayed. Earlier sealed-caller-v1 local builder refused generic size bound before publication; freshv2 reads only exact authenticated packet bytes<=64MiB, preserves other caps, full actual1361/286/SSH22838/seals preflight passes. UI packet5904dfe80f5ab718859803015d33505140a36e147d5b38e265b3ab9c1e9a74b4/1269760B published locally, not yet staged.

Readiness binder-v1 locally refused a 3-key preservation pin/full4-key row comparison before publication. Fresh binder-v2 fixes only actual record projection and full actual prefix passes; actor48713ef2/callerca78858a published. Original readiness-v1 execution3927939/start437371024 FAILS1.428380s rc1/reaped/gone: guestFileNotFoundError at readiness301/captured.parent_fd after five prerequisite records, before the sixth retained environment24 record. Its configured source24-environment-v1/RESULT.json is obsolete; actual original producer uses source24-environment-preparation-v1/RESULT.json with same protected proof hash. Evidence WORK was created; application_or_installer_started=false, kernel_service_timer_or_permission_change=false, finalstrictclosure=true. Failure/partial WORK remain retained; fresh readiness-v2 and exact downstream selectors are required, not replay/overwrite. Premature OCI-transfer binder invocation also locally refused missing readiness before publication; no OCI guest transfer occurred.

### Checkpoint241 — actual native/UI staging and shared micro image runtime pass (2026-10-25)

Corrected readiness actor83587884/caller39f2371c ACTUALLY PASSES3.976258760s, original3928549/start437392132 rc0/reaped/gone. Protected source25-staging-readiness-v2/RESULT.json SHA5548e28a4d15cfdd21f85d3ae32be4c9f94a9f4081bf5a5f8a58f57d5106486f; local91b09107/448940B, stdoutd9979992/339702B. All326 inputs/failedreadinessv1 preserved; current aliases absent/secrets0/strictclosure true. Actual original ENV24 producer path corrected to source24-environment-preparation-v1. No application/installer/policy action in this readiness run.

First native016 actorf07e88ff/caller795aede9 ACTUALLY PASSES41.645655009s, original3928681/start437395178 rc0/reaped/gone. Protected source25-native016-install-v1/RESULT.json SHA561a2ca953c3c8b33988bf4ea27ee0f6c49582855a1b9c8bba13c6fb7d05f9c2; stdout0f219613/734426B. Both old native216 leaves, all old rootless leaves and326 control inputs full9/SID/hash unchanged; child closed/gone and outside mount tables/namespaces unchanged. New108 leaves/version.16 verified; selection/policy unchanged, no application service start. Installed functional acceptance remains false.

Ordinary UI actor04f03121/sealedcallera19fff46 ACTUALLY PASSES5.608731375s, original3928989/start437401990 rc0/reaped/gone. Protected source25-native016-ui-staging-v1/RESULT.json SHA282c3c9924a5bee961f4f67a7021a5e7166e3620e25c2bfe6d6732ba6f5859bb; localbfb511a9/209052B, stdoute0fca66c/158756B. Six immutable UI files and all108 installed package descriptors held/rejoined/closed; original installer not replayed, no Caddy/app/credential/policy effects. Both transfer and ordinary generic classifiers accept the actual DTO without a recovery replay.

Original OCI transfer3928890/start437400765 rc0/reaped/gone3.704053s; full image-build receipt transfer3928956/start437401554 rc0/reaped/gone0.785501s (actual local stem web-006-source25-image-build-receipt-transfer-v1). Image load actor aed86a5d/caller12a3077d ACTUALLY PASSES7.819856340s, original3929068/start437403411 rc0/reaped/gone. Protected load ebc60188b19b85f37ed0feac211c49ff070570bfd49be6c5a085e5655097e47f, local1d5fc2e5/226142B/stdout0e944834/170988B.

Actual image runtime actor1daa29d1/callerd7bd0f73 PASSES57.477611816s, original3929143/start437404959 rc0/reaped/gone; stdout8e8976d1/177804B. Genuine pinned UBI10 micro ancestry,108package/6UI hashes,35 absent tools/8 absent modules and original UID mapping/confinement pass. Runtime probe SHA f33d2c1090bd510e866a45bcdae7f7bb8f01feefb7389a87a85508e6814a6b26. Exact audit CID998b84885083faeec9782345bc74e25752d6fc1a807f6c53d82b173785ef7d27 is retired nonforce; original outer/cgroup gone, old3 stopped audit containers preserved. No application services/selector/policy/credentials change, no payload/key-body/digest read. Runtime kernel2416 is explicitly BEFORE policy25, never proof of the later state. Source25 normal/dedicated installed browser acceptance remains false.

Reviewed policy25 full actual pureprepare/hostbinding passes, actor0921f647/77186B/callerfe00edc4/72123B. Original owned policy installation is running; actual new kernel/receipt is not predicted or claimed. All fresh downstream ENV/rootless017/profile/authority/normal/fault/isolation/MAC/lifecycle gates remain mandatory.

### Checkpoint242 — actual new policy and native/rootless profile staging pass (2026-10-25)

Policy25 actor0921f647/callerfe00edc4 ACTUALLY PASSES15.336597623s, original3929505/start437417026 rc0/reaped/gone, stdout9a08d3e3/357837B. Protected source25-selinux-policy-installation-v1/RESULT.json SHA47392501aac44e8ed1e6f6eda74e09f93aa2686c9f726a0ac19e410bae7eb6c1/322051B. Actual kernelAfter fdd7528001ed0733389dbd452961073ef6f0aeb0becf2582c36622e3561d0028; previous kernel2416 is retained BEFORE evidence only. Installed global CILa051f2541f0a5c8719a9e8d0c8ee36ce26ac0d3c4e94415cec847fec05188d8f/17927B inode79816422/root0644/code_t/unconfined_u. Current independent receipt0d2bdb1d16d4271a2750aa2afc4b4f65a6c559a2e68150e15e4f291bbd32fb4d/1091B inode79816854/root0644/conf_t/system_u, archive type nfs_t derived from actual fixed owned metadata. Four fresh candidate/backup NOREPLACE pairs verified; old globals and all five retained releases unchanged. All other modules/boolean values/fixed labels/metadata unchanged; no service/timer/credential/fcontext/boolean action or key/secret body/digest read. Functional acceptance remains false.

Fresh ENV actor4ca325ec/caller935f290e ACTUALLY PASSES29.831424452s, original3929826/start437425238 rc0/reaped/gone; stdout70411940/391226B. Protected source25-environment-preparation-v1/RESULT.json SHA7beee46edf30d65158c537c3ae3a389735071b6cb61c5ff31372c5f1fa1936cc/339089B (local collector stem environment-v1). Real current newpolicy/receipt/kernel,108 native package leaves and194 borrowed browser files/50 directories rejoin. Independent full actual prefix1db6fa2b passes. Old sources not written/relabelled; no services/selector/policy/credential change, strict closure and secrets0.

Rootless017 stage actor aff82fe9/callerb9cbc832 ACTUALLY PASSES5.513632393s, original3930023/start437431231 rc0/reaped/gone; stdout29fbc52d/183115B. Actual uploaded full-build dd590e9e/585697B at fixture0216 path joins; all108 readonly native leaves match source25. Original stage/render attempted once and verified, no image/native installer/audit replay or application service start. Current source25 native.16/rootless.17 profile proposals actorbf4d7a43/callerff6be150 ACTUALLY PASS5.392126785s, original3930124/start437433895 rc0/reaped/gone; stdout2e20a9ce/212027B. Actual four proposal/create/cleanup/two-rename prefixes and previous failed profile retention pass; permissions unchanged, no deployment policy/credential installation or service start. Current aliases remain absent. These are staging proofs only.

Authority37 proposedUUID85da1326-ddc7-4c62-843a-862609e221da/controller38d53cc41f remain source preparation until actual complete current11-field/control326-prefix/SELinux producer validation and guest publication. Native31/rootless37 and dedicated isolation/fault/MAC/helper-filter/lifecycle/cleanup remain required. No prior failed run is promoted/replayed.

### Checkpoint243 — authority37 fixture publication failure retained; no browser run (2026-10-25)

Final authority37 binder d9b90fbf/31639 and independent full actual constructor review c1c5c6fc/13931 pass source-level checks of all11 control fields, actual new fdd/a051/0d2 SELinux records, both real .16/.17 deployments and exact old326 ordered input prefix. Predicted control348/manifest hashes are source projection only, not published authority evidence. Actor86b66dcd/420779 and launcher230b85fe/199818 are published locally once. Exact BZ2 caller e6be29b6459746b52f2db48794810e90d6876fd7ae2123002c631e6615777cd8/88303B passes1361/345/QEMU/FD/SSH103438<unchanged120000 and exact decoded SHA/length/footer guards; no wrapper cap or original actor bytes changed.

Original authority37 execution3931416/start437479197 ACTUALLY FAILS2.431100781s rc1/reaped/gone; stdout8fc821751647efa827793b69b742b72e44d1605ed53cae028fb0759291e04411/238124B, stderr77bcbc36/965B. Local result 7d136507b398ec9bcdd75568abf51d1f1b158399935170bd785504eda88564f4/309432B. Error class OSError, frames main870→prepare_authority809→publication_file395→source16_readable_parent453→publication_owner424→parent_fd50. Failure occurs publishing rootless/policy.json after rootless/deployment.json. Exact errno is not recorded; descriptor exhaustion is a source-inspection hypothesis, not observed historical errno or established cause. Saved ENV actual descriptor budget is soft1024/hard524288/used820/reserve32/limit_changed=false; this does not measure the extinct authority process. No RLIMIT/hardening raise is authorized to bypass the failure.

Actual partial37 has14 files and7 directories: protected fixed-controller-v38.py; public same-Caddy launcher/native+rootless shims/tool inventory/six UI assets/native deployment+policy/rootless deployment. Full9/SID/hash rows are retained in the original failed result. Four original queries182343/start38361948,182344/start38361967,182346/start38362051,182347/start38362067 all rc0/reaped. Final strict closure true; application_services_started=false/global_policy_or_credentials_changed=false/key-body-or-digest-read=false. all_inputs_rejoined_and_closed=false and passed=false are preserved. No control38/positive authority37 or browser acceptance is inferred from locally predicted source data.

Static/transfer inspect original hold lifetimes/path handling and actual failed37 records; fresh authority38/controller39/proposedUUID and subsequent normal scope ports must preserve failed37/14 partial files without replay/overwrite. Any bounded descriptor correction retains exact source hash/mode/SID and before/after validation under original noncreating lock, without limits/security changes. Native31/rootless37 never started; unexecuted candidates remain retained. Unit/integration gate25 rows are now recorded against actual current source25 log for all4cases; installed functional statuses remain pending.

### Checkpoint244 — bounded fresh authority38 passes; native31 functional run active (2026-10-25)

Failed37 exact protected RESULT SHAe6bd49d3/121092B and14published/7directory partial state are retained; manifest84962aaa/30652B lists actual original execution/channels/full9/SID/hash data. Its errno remains UNKNOWN. Source inspection confirms retained historical published-file descriptors plus current inputs leave inadequate reserve: prior authority36 actual FDused968/soft1024/reserve32, adding21 held authority36 files alone costs42FD. This does not prove original errno24. Source25 authority38 bounds those history groups with exact before/after full9/SID/hash snapshots, no persistent old-history FDs, while current108 package/194browserfile/50directory holdings remain unchanged. Original selection_lock is outer and ExitStack inner, ensuring historical final snapshots after currentFDclose and before originalflock release on pass/failure. Original errors survive secondary history rejoin failures; typed errno and actual FD observations added for fresh failures.

Exact helper5274b9db REAL local tests PASS15:2048 files/32nested64-row groups use baseline6/peak8/after6FD (+2constant), metadata/same-size content/hash/SID-shape mutations reject, original exception survives independent rejoin failure, and independent original-inode flock gets EAGAIN in both before/after callbacks then succeeds only after lock release. No FD/RLIMIT change. Report47be3fe0/2271B/scriptb8a1df09/7994B. SID adapter is local unit data; no guest/MAC or historical errno acceptance inferred.

Fresh proposaldf385e60 UUID5e0e095c-dd85-4370-9416-2425e36bd3a0/controller39ad399d4f20c3333957a20e84560c84a7f29bc74febbff9fe515a27b3820e4a4b/118954B; template57e29753/88595B/binderfa47c32a/33208B, independent fullactual34b83ff3/15011B. Bound actor226a537f4acd3c685dc9a1ab58bbad59f94ff5ba0ac650a0154535e90a677b54/425192B and launcher4ec97be5184c579319384b2e7d7cbef6d61a659a7cb3aec7b4768e3c261af170/199818B; exact BZ2 caller328a93ef960a800b9e604d4d87e87a46dca767a0fb286f4353b07a271e8047c4/89544B passes1361/350/fullsource/QEMU/FD/SSH104613<unchanged120000. No original actor bytes or wrapper cap raised.

Original authority38 execution3933783/start437573181 ACTUALLY PASSES4.162722738s rc0/reaped/gone, stdout606150418e616fab3f75c8d9ef5b5b0f47b82c1aaccd2d72d30aa94936ebcd10/363507B, no stderr. Protected fixture-authority-v38/RESULT.json SHAee9d791c9f914c3a965013bb195ac711692b8bbf01f30b52bdec3df6cc8eb062/289996B. Actual control39 /opt/hfcache-web006/control-v39.json SHA f7a1061679cd1d60814266a3abdfeec468fe8f822c55e2d2d0de9d26f27ee1a4/64728B inode43822818/root0600/usr_t; actual349 inputs preserve original326 ordered prefix, no predicted count promotion. Manifestb8b9d9142f2e36dd5728dcaa0677bc40220f867917c6394dd2a5ecfffc322ce3. Actual new current SELinux fdd/a051/0d2 and both .16/.17 deployments validate before publication; controller load/header/visudo checks pass. FDused862/reserve64/soft1024/hard524288/limit_changed=false. All input/history/partial37 joins close; strict closure true, secrets0/current selectors absent. No app/global policy/credential action; new_installed_application_acceptance=false.

Native31 authority38 binder7e0d1d55/11928 and independent fullactuald0682839/4168 pass actual349/currentcontroller/source09cd/profiles/failed36 predicates. Exact bound actor8ff37af472190272728277ff11cfea4f8255dbbf2dc9bdddde31baef0601b775/37398B; captured caller4cabfc07377815bd256d5be2844f8a63aa3029fe1e5de5e0b31a07831998fb48/72111B passes1361/282/SSH22543. Original native31 execution3934078/start437580447 is RUNNING; local stem web-006-source25-native31-functional-v1, protected WORK source25-native31-functional-v1. No native result is inferred. Rootless37 baseline/coordinator plus all both-profile dedicated acceptance remain future/unproved. All required scopes use authority38; old unexecuted authority37 normal/fault candidates retained, never promoted.

### Checkpoint245 — source25 native31 ordinary functional acceptance passes; rootless37 running (2026-10-25)

Original native31 execution3934078/start437580447 ACTUALLY PASSES350.399652583s rc0/reaped/gone, stdoutf591dc4c20d3e3a48af54dcebb0a6e5eb6378b59dc4f1e09a7bf0578b7d206ca/387108B. Protected source25-native31-functional-v1/RESULT.json SHAb95c40a33775906da4d8c3c5249543b22e5cd406829a9ddb794d92277cf931f8/446438B. Original runner182455/start38463236 rc0/reaped347.303333598s; invocations1, kernel fdd, all inputs rejoined/closed. Actual generationbb29e15d8a7646ef878624edadfc1b5a and SUMMARYe2716cf7f9e49dacb77cd02717812bef635c7d7ccf1823a4b782c4da23e5a1c2/379447B. Four modes baseline/helper-down/restarted/timeout, three engines each,33 actual one-attempt passed host assertions,0requiredskip/retry; every browser/descendant closes without force. Twelve actual same-Caddy untrusted-TLS refusals are validated in the original adapter/postrun records. Native supported/guard-absent status, guarded Basic archive/Hub/control403, forged-header/old-writer403, helper-unavailable503, real timeout and same-parent restart pass. No rootless, dedicated isolation, MAC or full case completion follows from native normal.

Readonly postrun actorfc52bc9d/caller430f693c ACTUALLY PASSES1.764231915s, original3935536/start437619336 rc0/reaped/gone. Protected source25-native31-postrun-v1/RESULT.json SHA43ce6426723129ff8e3268d6c680ff2a839d63c809695f3596694c950bbd3638/130227B, stdout856f3e28/205727B. Actual eight-record normal adapter f9807d6d is available for dedicated guards; original processes, closure, live source/asset/policy/UID mappings rejoin. Ordinary preservation actor0a716757/caller772a0bed PASSES1.822340051s, original3935612/start437621085 rc0/reaped/gone. Local stem web-006-source25-native31-ordinary-preservation-v1, protected source25-native31-preservation-v1/RESULT.json SHA9c8852b8163332f86e74c428d80c8f3c196c5b70eb727d5bc669488e30b87560/55626B. Original Basic and3selector paths NOREPLACE-preserved; four current paths absent, no payload/key-body/digest read.

Rootless37 baseline actordf32d502/callere4a79776 PASSES1.543812212s, original3935685/start437622600 rc0/reaped/gone; stdoutc942ce7b/137769B. Exact local stem web-006-source25-rootless37-secret-baseline-v1, protected rootless-secret-baseline-source25-authority38-normal-v1. Normal coordinator source eb2363e4fed96191dc94840e01ee86a62add359ae2f99ce6b14a5f7fe4a6eaac/131517B, observer1d746b9f/51891B, runner9dd52777/41739B. Captured caller781be7347f2cf9de10923a66e1fe8478927a5664e325eb30044712b2c4023bf5/72543B passes1361/284(including actual observer+runner)/SSH48765. Original rootless37 coordinator3935832/start437626116 is RUNNING, local stem web-006-source25-rootless37-coordinator-v1. No outcome inferred. If normal succeeds: postrun→six-owned-ID normal retirement→canonical helper Seccomp_filters metadata observation→ordinary four-path preservation, then both-profile dedicated acceptance. If it fails, diagnose/drain/preserve original before fresh work, never replay/promote.

Required source-only preparations are separate: normal/fault/lifecycle manifests preserve actual authority38/controller39/349; isolation/MAC PREPARATION3a0f7c33/4702 has12 actual-manifest joins/45Counter/26MAC checks, unchanged current-input holds and used+64 budget; no actual dedicated prelaunch FD/denial/attribution acceptance yet. The canonical-helper observation future proof hashes remain UNBOUND. All four case statuses remain pending despite four new actual native normal rows in acceptance ledger.

### Checkpoint246 — source25 rootless37 original normal fails; diagnosis and failure-only cleanup pending (2026-10-25)

Original rootless37 coordinator3935832/start437626116 ACTUALLY FAILS86.239233548s rc1/reaped/gone. Stdoute6df7bdede6db8f048f5e73078ab2fe5192415d905c9ba06a42821fe210598d2/167673B, stderrf91a7498/965B; local result ac54f8344de4eb94d9c2fb5555b1d43a702b4a9b373369dd92582ba2b620a252/220935B. Original runner187915/start38508897 rc1/reaped84.499810175s and watcher187914/start38508867 rc0/reaped84.806543112s, both original identities gone/numeric PID absent. Exact ownership successful_ownership_proof=true/all_sources_rejoined_and_closed=true/error_class=null; secret payload requested/read/hashed=false. Final strict_fixed_role_closure=true, held_release_failure_classes=[]. Runner all_guest_inputs_rejoined_and_closed=false/error_class=ValueError, no secret retirement; coordinator original_rootless_functional_passed=false/all_inputs_rejoined_and_closed=false/full_WEB006_acceptance=false, main173 need guard. Original runner codeSHAa82cf37147467781dc1be22d9746b4a7ccf714dde7761939e8aff20dacb782fc is retained. These original false flags are not promoted by successful watcher/drain.

The current source25 fdd/a051/0d2 broker message-rule change is installed and native31 actually passes; rootless failure cause remains unproved. No new policy permission, API crash, browser result, current generation/CID drain or secret cleanup outcome is inferred from the top-level ValueError. Required next evidence is the bounded original saved browser/startup/generation/CID/Basic metadata reader, followed by exact original broker/kernel-window reads only when that window is measured. Parity owns typed reader; static owns original broker/AVC provenance with reporter PID distinct from client and no raw MESSAGE/argv/EXECVE/proctitle/path/payload export. Transfer prepares failure-only exact-six-ID opaque durable backup/nonforce retirement and four-path NOREPLACE preservation, gated on original full drain and credential metadata. No replay, normal lifecycle or rootless positive postrun/retirement/helper-probe binding is allowed from this failure.

Six owned credentials/current Basic and selectors remain retained until measured; the original controller/normal/watcher/generation/source receipts are preserved. Native31 ordinary normal/postrun/preservation remain valid. Canonical-helper observation and dedicated both-profile isolation/fault/MAC/lifecycle/cleanup are future/unproved. All four required case statuses remain pending; four actual failed37 functional observations are recorded without suggesting required skips or cause.

### Checkpoint247 — original failed37 diagnosis and exact cleanup pass; fixed bus diagnostic prepared (2026-10-25)

Readonly metadata actord63b48f9/caller725ee48b ACTUALLY PASSES0.957948525s, original3936992/start437662896 rc0/reaped/gone; stdoutbbbbc112ce69df268802fd3e759d25a5b247ffa2ce2cad13121ab38bc7c36723/147901B. Local result2d4233cb/192429B is stdout-only, not an invented protected diagnosis. Original generation16ac8aa4bee14f60948a075058c660a8, record4f893aaed14ef286aa896cabe5695329d40dcc0e6c2824d51471da5e2663e646/73364B under generations-v39, is stopped. All69 pairs gone,3exact CIDs exited0/PID0 and6original wait0/exists1 observers drain. All3 baseline report engines unavailable vs supported before any cases (0), every browser/descendant exit0/drained/no force; reportdbcde51e/67909B. Startup eventually bootstrap200/valid manifest; all3untrusted TLS refusals pass. Actual peer-probe sameUID/otherTGID refused; applied helper188058/start38509418 helper_t/CapBnd-Eff-Prm0xc0/Inh-Amb0/NNP1/Seccomp2, nowgone. This does not recover Seccomp_filters or reason/phase. Driver assigns host_status only after its full acceptance assertion, so original typed reason/profile was not retained. DEVNULL observer stderr and erased PeerError stage cannot be reconstructed; no new failure cause inferred.

Original Basicinode118921830/983:983/0400/221B/secret_t and3current.17 aliases are metadata-only preserved. Failure-only retirement template-v1/footer order was caught before publication; v2 d63e9eb1/96858B moves the execution footer after all definitions, binder1082e6ff/14161B and independent89c1d83f/4020B pass actual flags/ARMED/hash/69+3CID+6observer/Basic/source/policy guards. Bound actorb2793fb1/101671B/callerdea6e2f7 ACTUALLY PASSES5.604971420s, original3938020/start437695957 rc0/reaped/gone, stdout67a164d0/211128B. Protected source25-rootless37-failed-secret-retirement-v1/RESULT.json SHA6b14e9808a41d8193cfa2329c11c83f7407d34732d2e0a5a9c9dcb9feb956839/125478B. Whole store opaque durable backup, six individual exact IDs removed nonforce with intents; final known/unknown0, originalfalse flags retained, normal_lifecycle=false. The retained scope-description string says old source24/failed36; actual current enforced paths/pins/GEN/ID metadata and source bytes are source25/failed37 as above. No body/digest collector read or application/helper reset/policy action.

Four-path preservationv2 binder476a351a/actorc3c55bf0/44588B/callercd509e9a ACTUALLY PASSES1.864468262s, original3938422/start437707920 rc0/reaped/gone, stdoutfba496ca/160194B. Protected source25-rootless37-failed-preservation-v1/RESULT.json SHAe7c7f9af538734a20dd96f9a4bc4bc7a85d3389386dfab5619ecff3672893d05/59336B. Original Basic118921830 and3aliases NOREPLACE moves retain full9/SID; current4absent/secrets0/strictclosure/key/current fdd/a051/0d2 unchanged. Its old textual scope description is likewise retained, not mistaken for actual selected scope. This is failed-cohort cleanup only, not normal lifecycle acceptance.

Original broker reader-v1 dc30aabf/callerb3f981b3 FAILS0.906899542s after a closed readonly journal query189937/start38566577 rc0/reaped0.025913455s/7398B; outer3937630/start437683856 rc1/reaped/gone. Source port left obsolete --since1792901355/--until1792901437.999999 literals while WINDOW changed, and project_journal297 timeguard rejects before causal metadata. Original false/stdout57493d3e/117966B retained; no raw MESSAGE export/hash, no current-cause inference. Freshv2 actor1650163b/22461B derives journal_argv from WINDOW; two-window/four-invalid-bound tests581f70ec and independent615ec52d pass. Caller12ec3b86 ACTUALLY PASSES0.859486636s, original3938146/start437699913 rc0/reaped/gone, stdout90f12e29/121768B. Query190193/start38582630 rc0/reaped/EOF/closed0.011386566s/0stdout, exact original ARMED→stopped-GEN window1792907707..1792907791, broker70560/UID983/boot pinned. Matching journal/SELinux mentions0 does not prove send_msg allowed or justify another grant. No client/method/historical capability claim.

Original AVC+SYSCALL+USER readeradf6fca9/caller84843600 ACTUALLY PASSES0.910695575s, original3938352/start437706474 rc0/reaped/gone, stdout8dc91435/151138B. It reads bounded retained audit1931326B and uses actual window for both parsers. Exactly38 kernel AVC/SYSCALL full timestamp/event/PID joins:6init_t socket ioctl/syscall16,24exec_t file ioctl/16,8cert_t dirsearch/openat257; allEACCES,0fixed-systemctl/Podman executable flags,0comm_is_systemctl,0USER_AVC. Six socket/3exec/1cert on original applied helper188058 UID0; remaining21exec/7cert on seven UID983 observers. Secret gate decision sequences49/49. These previously optional patterns do not establish cause or justify extra permissions. Reporter PID is never implicitly subject/client; no historical start ticks/unit mapping/raw logs/paths/argv/EXECVE/proctitle/payload exported.

Next bounded diagnostic is a NEW fixed read-only UID983 session-bus five-property systemctl show of hfcache-api.service under exact helper_exec_t/-I entry, canonical unit hardening, helper_t/caps/drop setup, typed phase/errno/rc, original process/EOF/wait and normal-stop closure. No API/container/protocol/credential/grant change or original-normal replay; query success proves only stopped-role bus access. This is source preparation only, no diagnostic unit executed yet. Optional driver-only patch0be5442d/4237B remains UNAPPLIED in scratch,23meaningful local tests pass; it retains only validated state/reason/profile before unchanged acceptance assertion for future failures. Canonical source25 remains frozen.

### Checkpoint248 — real confined fixed bus query refuses AccessDenied; all original diagnostic processes close (2026-10-25)

Source-preserving NEW owned bus-only diagnostic is independent of failed37 normal and does not establish UI/host acceptance. Canonical28 unit security properties match pinned original79d; exact -I helper_exec_t root0755 entry and runtime_t root0600 inherited output/error FDs, no broader RW scope. Worker c6bce45c/13603B and8 real local harmless collection unitsff360206/3057B (overflow/read/close/error and actual child/pidfd/wait/FD closure) pass; parent/child privilege and exact environment/five-property show reviewed by parity. Final actor dc1698cdcde72e8b13bcdb487b8d7fa029093f8b4502d770a68050fa716e90d1/77882B, own actual preflight7a1de3aa/1997B and independent4b3e2400/1536B. Captured caller8ec2ccc4a455e25d18691186e989ead483cbfaec7c131e0cdf536fd723da5e60/72132B passes1361/282/SSH35131. Type=exec+RemainAfterExit has no READY fiction; expected exit/metadata ownership is explicit.

Original new diagnostic execution3941691/start437822806 ACTUALLY FAILS2.093794789s rc1/reaped/gone, stdoutc1436c44ec6559e402dccf760a4e6ca9bd479f6a9ea6346a840cb723e8550ba4/171849B, genericstderrf91a7498/965B. Protected source25-rootless37-bus-only-diagnostic-v1/RESULT.json SHA2723efdd2e8abac7c2927d37bc44a3b5a2beb48a9d4083fd1d9162bebf5b86f7/74325B; localb41e97f4e5926e403ed653fe8a138015f5d640d03cf8c1f742fc51d00c9c1c73/226913B. Worker190339/start38705565 gone; worker stage child_collect sees child query_returncode rejection, preserving ValueError/errno null and passed/all-input false. This is actual refusal data, not an execution-prefix/203 failure.

Owned child190342/start38705581 before-drop rootUID/GID0/groups[]/helper_t/P-E-B192/I-A0/NNP1/Seccomp2/Seccomp_filters24; after-drop UID/GID983/groups[]/samehelper_t/P-E-I-A0/B192/NNP1/Seccomp2/24filters. Real fixed systemctl query190343/start38705582 executes, returncode1 in0.012895686s, stdout0/stderr40B; only safe marker access_denied=true, failed_to_connect/no_such_file/not_permitted/permission_denied=false. Both streams EOF/closed, no overflow/timeout, original query waited/reaped/pidfd-ready/gone. Child exit1 waited/reaped/pidfd-ready/gone, result EOF/nooverflow. These24filters are from the copied diagnostic unit, not the still-required genuine canonical-helper Seccomp_filters observation.

Unit submission190338 rc0; normal stop190348/start38705588 rc0/0.020624596s, owned MainPID0/ControlGroupempty and physicalcgroup absent; original worker gone. Failed state from query exit1 retained, then only owned reset-failed190350/start38705595 rc0/reaped/gone0.020744776s. Final strict fixed-role closure true. No canonical unit/policy/permissions/key/credential changes, no API/container/Podman/protocol start or original-normal replay; kernel fdd unchanged. New entry/unit/runtime/evidence remain owned retained artifacts. Source-proven copied confinement plus real query refusal narrows the boundary but does not identify a permission/class/target or original exact method.

Next is a bounded original user-manager70491/start6647766/UID983 journal reader, two separate exact windows: failed37 original1792907707..7791 and diagnostic UNIT-START-INTENT→worker-output original mtimes (same-second duration permitted). Hold/rejoin current manager identity/context, distinguish current from historical facts and reporter from client/subject, parse only bounded SELinux contexts/permissions/classes/outcomes. No raw MESSAGE/path/argv/hash or permission addition. Parity owns reader, transfer independent producer/parser/receipt review; static reviews primary systemd257 SELinux status-check source/contracts. This remains preparation, no manager query executed yet.

Version hypothesis was checked and not substantiated:11 actual-held DTO/pure original predicates8371d93b pass software.16/deployment.17 image/runtime/source/UI bindings; startup HostDaemon policy inspection completes before listener/notify READY, which original37 reached. This is source-order/saved-readiness inference, not proof later peer/manager/engine observation passed. Driver-only typed observation patch remains UNAPPLIED; original-module exception-chain recorder proposal468555ad/2991 remains unused pending bus/journal evidence.

### Checkpoint249 — original manager denial and exact immutable fragment provenance confirm label prerequisite defect (2026-10-25)

Fresh manager journal sourcev4 8d2d2ce57ead08f2421389e397571a9a86f0f67e7795250182463c16d7bcb507/25562B and independent48ad66fa/1628B pass33 actual-window/parser/metadata/F821 checks. Quoted/unquoted discarded path/cmdline text cannot promote forged fields; v1–3 and their unused caller retained. Captured callere60fa4b0/72129B passes1361/282/SSH10441. Original reader3943953/start437904424 ACTUALLY PASSES0.944871371s rc0/reaped/gone, stdout02983fb39a8ff2796cfd10bca48f8115aad891ff6eb5def66af526371ad68e3d/127636B, no stderr. Stdout-only, no protected diagnosis invented.

Exact failed37 window1792907707..7791 has69 fixed manager entries/7SELinuxmentions and7 enforcing AVC decisions: subject system_u:system_r:hfcache_host_helper_t:s0, target unconfined_u:object_r:usr_t:s0, class service, permission status, permissive0. Separate new bus-only1792909674..9674 has8manager entries/1SELinuxmention: same subject, target unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023, class system/status/permissive0. Reporter70491/UID983 is NOT asserted as subject/client. Current manager70491/start6647766/contextunconfined_t/AUDIT_WRITEeffective+permitted=false is PIDfd/stat held/rejoined current evidence only, not historical capabilities. Queries190431/start38787137 rc0/reaped/EOF0.023924141s/33556B and190432/start38787141 rc0/reaped/EOF0.021480024s/4123B, original identities gone/nooverflow/tail limit. No raw MESSAGE/path/cmdline/argv/export/hash; no request/activation/replay.

Official systemd257 raw sources (receipt877d72c6/2530B) confirm Get/GetAll→status; loaded fragment access context→service, absent fragment→manager context/system. Physical GitHub anchors retained in interpretation5aea426c/3095B; callback audit-fd CAP_AUDIT_WRITE fallback source c7d4981f/1221B is separate primary evidence. Systemctl --property filters printed results AFTER GetAll, not MAC/wire properties. Original host_peer only shows fixed loaded API user-unit twice; system legacy/guard queries use --system. Absent-API diagnostic SYSTEM(status)/unconfined_t branch is not established as required for normal loaded API peer proof; it does not justify an extra right.

Fixed fragment reader d34da0bb2ff715fe9f5229f90821bd71edd769fb1bec62cfcd0daf7db6ea9eb3/14596B; independent actual profile2767/deploymentbfc1/indexf4b7/source3196 predicate checks pass after unusedv1 capture-row projection fix. Captured callerd875b24f/72153B passes1361/282/SSH6701. Original3945473/start437960543 ACTUALLY PASSES0.884498741s rc0/reaped/gone, stdoute8a0bd85b30040531b904372d09fad96f47ceeb517874f5f7357bea620864c58/123776B. Exact indexed /opt/hfcache/releases/0.2.17/rendered/hfcache-api.service inode11038094 and packaging/containers/hfcache-api.service inode94846180 are root0644,565B,SHA3196a07a5aed4a354aabee364af1e6fc3d0e0c58adba36507fdb0bc11028e808, contextunconfined_u:object_r:usr_t:s0. Both ctimes precede original ARMED; bytes join original artifact index, deployment and ready fixed API user-manager proof. Container-release73bf65f4/3493B likewise immutable. Fixed /etc/systemd/user/hfcache-api.service inode9984600/root symlink contextetc_t, target matches fixed current/rendered spelling; no unknown link followed/exported. Symlink context is not substituted for fragment context; no AVC inode was exported/claimed. Independent full review3bda6cbb/7107B agrees.

Existing docs/containers.md515–525 requires persistent narrowly scoped systemd_unit_file_t for both system/user fragments, targets/bridge and proper bindings; host-administration.md299–312/CIL already grant that service/status class. The observed usr_t targets and etc_t binding are omitted owned-fixture provisioning, not grounds for broader usr_t:service/status or etc_t link rights. Controller39 only selects/reloads, creates no generation fragment copies. Preserve immutable17 and all old7 release full9/SIDs, preserve original fixed binding inodes/SIDs via guarded NOREPLACE, then provision fresh rootless018 indexed fragments/targets and same-spelling fresh bindings with reviewed persistent fcontexts/restorecon-F before authenticated profiles and manager reload. No retained17 relabel or kernel allow change.

Transfer confirms unchanged original installer independently binds deployment version/image/source/wheel and can stage18 using genuine shared image04725627/software16; original dd590 build receipt and its rootless_deployment_version17 fixture field remain BYTE-EXACT, explicitly distinguished from new stage target18. No rebuilt18/image-origin claim and no canonical projection edit. Static owns exact label/binding actor, transfer freshstage18/profiles, parity fresh authority39/controller40/native32/rootless38 scope ports. ProposedUUID8f3a2d11-e5ec-4807-8d60-d2cb667b471e/proposalb5443793/controller40 0134b47c/118954B; source25/nativePython16, newrootless18, predecessoractualcontrol39/349. All new-stage/labels/profile/authority/normal proof hashes remain UNBOUND until actual execution. Source25 stays frozen; driver observation patch remains unapplied.

### Execution checkpoint250 (2026-10-25)

| Step | Original PID / start | Seconds / rc | Protected RESULT SHA256 / bytes |
| --- | --- | --- | --- |
| stage18 | 3948882 / 438096221 | 8.071190 / 0 | `7e07c3daa486541ea0085f79cd9d246cb58f64245f369e77ecb52f7a7d74934f` / 1170263 |
| label_readiness | 3950284 / 438152492 | 3.647956 / 0 | `d321a75280580b84b977bae825053abb839a713085efe2dcf4444b809899dfab` / 1178143 |
| partial_provision_false | 3952971 / 438246160 | 21.281743 / 1 | `78ccb7f7de33b9a0ecb657c9b2cab5cf9d07ba058496dc8b85e3853be3d3733a` / 1292812 |
| recovery_readiness | 3954730 / 438303493 | 3.428643 / 0 | `e697f6153f6567f2a93950449283fe116e22dfb2f4dd451d74dcf1cf59111722` / 1160201 |
| label_completion | 3955767 / 438337808 | 10.837278 / 0 | `bf94796f96977b715b08fe7e37ae8cae7f2a6b4975c788b87620a36f7d2b0cea` / 1831858 |
| profiles18 | 3956359 / 438354178 | 6.007334 / 0 | `2bb9c35f8f5a46501ded3e3a7b3f386536e62552369b5cd144235b06591b398e` / 130624 |
| authority39 | 3957617 / 438395704 | 5.152946 / 0 | `d8a0b019e3ca65947eb6b56823661c81312aec448d3f501e65e2491c3620d717` / 362620 |

Each executor above is actually reaped and its original identity absent. Protected paths, local result and execution full pins, stdout/stderr hashes are in the companion EVIDENCE JSON. The original partial provision retains both local and protected false flags, its198-byte hashed equivalence error and seven preserved originals. The completion does not promote that original result.

Stage18 retains indexed13 BEFORE unit records; completion supplies13 AFTER records allowing only SID/ctime changes, exact7 new bindings and7 original NOREPLACE backup records. Original .17 and all seven old releases/ordered349 control inputs are unchanged. No executable launchers are relabelled. The global CIL a051, installation receipt0d2 and kernel fdd remain unchanged. Persistence uses `semanage fcontext -N`; exact nonrecursive restorecon runs only on the13 new18 files and7 new fixed links.

Profiles18 binds actual completion bf94796f and original partial78ccb7f7 separately, permits the13 intended label transitions, and verifies the new7 bindings plus original7 backups. Native/rootless bits remain configuration=true and archive/control/hub/observer/schedule=false. No application service, deployment policy, credentials or permission/kernel grant is installed by this profile-preparation step; its two owned selectors are preserved and four current aliases absent at return.

Authority39 publishes21 files and control40 `c7cf53f0c449bfaa873dc10216be0333ba762cf009e3db81ef3f444d1ae72f37` /67364B /363 ordered inputs, keeping all349 predecessor rows in order. Controller load equals construction; label/profiles/current-policy, visudo and final strict closure checks pass. No application services/global policy/credentials or new installed application acceptance is claimed by publication.

Exact local/executor/channel pins: `.scratch/web-006-source25-checkpoint250-EVIDENCE-v1.json` (SHA256 `f45d83b0a2809cf6442d06bf78e0eb276dd50f2af59544d68a966e5f83f22a82`, 22967 bytes). Corrected exactly12 malformed source25 ledger source hashes to the original captured64-character snapshot; commands, artifacts, original outcomes and pending statuses are unchanged.

### Execution checkpoint251 (2026-10-25)

| Step | Original PID / start | Seconds / rc | Protected RESULT SHA256 / bytes |
| --- | --- | --- | --- |
| native32 | 3957799 / 438399552 | 340.545725 / 0 | `e588a1f2199102c81490ccb0c33ef3c2066cb4daef583169f69017daeb08b880` / 450890 |
| postrun | 3958925 / 438438070 | 1.833743 / 0 | `ac6ff22dc6bae291498961e57699b4b6113667d89069a5ac16f52316694c3812` / 130523 |
| preservation | 3959019 / 438440249 | 1.921970 / 0 | `a9eb867a8fbf184a3a650fed067f4891c622f21df84ae0d24327208526d46bb5` / 55618 |
| rootless38_failed | 3959326 / 438448331 | 90.248917 / 1 | `8e36b8d50b689a32c5519023087df31e8fd6e4a808efc1a2425576464f8faeb6` / 68003 |
| rootless_baseline | 3959117 / 438442666 | 1.661575 / 0 | `7305693d04ab31397908a86caa67ad6f1c36e47832b41844eac9d6de23215395` / 21074 |

Native32 actual SUMMARY `0413b309b92afb86916cd5df00dee3df85d8efcbcf242523e6081d381a527bde` /383165B, generation0023b5159a374ff1900ae793b4806a72, closes all original handles. Postrun retains8 native normal records. Ordinary preservation keeps Basic inode118921755 root:983/0640 and three aliases via NOREPLACE, with known/unknown secrets0 and four aliases absent. The baseline protected JSON uses its actual compact serializer; no guessed pretty-print pin is substituted.

Original rootless38 protected result8e36b8d5 remains false despite successful ownership/fresh original process closure. Its actual driver result is not reconstructed before the bounded reader; no helper-unavailable reason, method, errno or permission is inferred. AUTH-08/HOST-01–03 each receive a case-specific native32 functional row and a separate failed rootless38 row, preserving all earlier records and pending status. Source-only strict-gate rows remain unchanged. Exact executor/stdout/stderr/local/protected pins and node mappings: `.scratch/web-006-source25-checkpoint251-EVIDENCE-v1.json`, SHA256b58528c28f584d88f8d582e8a9e04acc245f710167952413d4bc852282756af6.

### Execution checkpoint252 (2026-10-25)

| Original step | PID / start | Seconds / rc | Actual evidence |
| --- | --- | --- | --- |
| kernel_USER | 3961676 / 438517515 | 0.962106 / 0 | Stdout-only `1ef34d5a42b0fb4cb8423db14c8ee859e501ba5d6b245061d53a439724bd2299` /250328B; no protected RESULT invented |
| manager | 3961443 / 438510324 | 0.884887 / 0 | Stdout-only `6af1f3dfa4db90bf6b0988a7a977ed2df6773a25eb61c868a097c72a87cfe21a` /134686B; no protected RESULT invented |
| metadata | 3960590 / 438486148 | 0.895367 / 0 | Stdout-only `2a2343e2122ecb42c1bec86ff606db271eba2a0f8fe85b0835f46006136b3b67` /148218B; no protected RESULT invented |
| preservation | 3961157 / 438502325 | 1.964831 / 0 | Protected RESULT `bef197cb5e708b9f9383da0b479127eb7050a3c13ef73a89d3f9f7264807ce37` /59330B |
| retirement | 3960950 / 438496162 | 5.415156 / 0 | Protected RESULT `f37dd27b720e82d4b98696e4d119636c6f82e6015b453543cffa059f11f16a91` /125489B |

All five original outer readers/collectors returned0, were reaped and their original identities are absent. Three diagnostic reads are stdout-only, with no protected receipt fabricated. Original failed coordinator8e36b8d5/68003 and generationcdfcc6a5/72825 remain unchanged. The manager reader holds the exact ARMED→coordinator interval1792915929..1792916018; the final generation mtime is one second earlier and is not substituted. Reporter70491/UID983 and system-broker reporter803 are not client PID/method proof; current manager context/capability observations are not historical identity/capability claims.

Existing service/usr_t refusals are absent from this manager window. Current SYSTEM(start/status), logind send_msg and fixed-Podman filesystem refusals are retained as observations; neither temporal agreement nor the executable flag establishes the fatal stderr path. No optional start/status/logind/search/write/ioctl grant follows. The exact fixed inspect stderr/phase diagnostic is preparation, not a repeated normal run or acceptance.

Failure-only retirement preserves opaque originals and removes exactly the original six owned IDs; four-path preservation keeps Basic/selector/deployment/policy inodes/SIDs with NOREPLACE. Known/unknown secret counts0, current four aliases absent, strict role closure and unchanged fdd are actual proof flags. Original scope strings and false flags remain byte-exact; no retag or acceptance promotion occurs. The acceptance ledger is byte-identical and all four required cases remain pending. Companion exact pins: `.scratch/web-006-source25-checkpoint252-EVIDENCE-v1.json`, SHA2563e7e7e3ef31b4b9e6993b51a2a391b8d769b1e861b956bce0cf364960545e7ce.

### Application development continuation (2026-10-25)

2026-10-25 development continuation: source25 capture, gate, artifacts and original outcomes remain retained. Native32 acceptance passed; rootless38 failed and is drained, retired and preserved. The corrected INFO diagnostic succeeds under existing confinement; it does not establish full container-inspection acceptance. Following the user instruction to cut orchestration overhead and refocus application development, source25 is unfrozen for targeted application diagnostics and the rootless fix. Use existing fixtures and concise test evidence; required source/native/rootless/isolation/fault gates remain mandatory before WEB006 completion. All four cases remain pending. No production, NAS, merge, push, tag or rollout actions.

The protected entry now logs bounded exception classes, errno and protected
code-frame aliases to the operator journal, including suppressed context; it
never logs exception text, paths, payloads or third-party command output. The
parent retains that diagnostic stream. Focused host-peer/daemon checks pass
(186 tests); typed browser-driver reason checks pass (25 tests). The public
fixture checker admits fixed named disposable guests (53 tests pass).

Fresh owned development guest `web-006-source26-a4df9de51e0f477c90da6980b5653076`
uses actual loopback read-only NFS, SELinux Enforcing and default rootless
Podman 6.1.0. The unchanged native installer passed for 0.2.2 with server/MCP and
no switch. The current wheel/UI build and shared API/UI image build pass;
image `346914fa425c085956018d33a0c8a968e58679bd4b7d95e6195f7e714b7b024d`
retains pinned UBI 10 micro and passed package/UI hash and absent-build-tool
checks. That image and pinned Caddy 2.11.7 are loaded in the new guest. These
are development prerequisites, not installed host-status acceptance; the
current-source strict gate and all four required cases remain pending.
Development logs/artifacts are under
`/var/tmp/web-006-source26-guest-_nxq5wnb/`; earlier guest/evidence are retained.

Current native trusted-TLS status GET passes through installed Caddy/API/helper:
HTTP200, supported/native, configuration permitted and other actions denied.
The owned native services then stopped with zero MainPIDs and empty cgroups.
After provisioning the documented rootless runtime directories and mount
placeholders, the installed rootless API serves its built-UI bootstrap. Its
status GET returns unavailable/helper-refused. The new protected journal
diagnostic identifies final peer revalidation at `observe_peer` → `_process`
→ `_read` → `_Budget.consume`: the initial size-zero charge exceeds the file
counter after full container inspection has succeeded. This is actual file-work
budget exhaustion, not a new byte charge or evidence for another SELinux grant.
See `evidence/rootless-running-get.log`. All rootless roles and the helper then
stopped normally, with zero MainPIDs and empty cgroups. The bounded aggregate
work fix preserves each read/revalidation and retains separate structural
cardinality, byte, time and concurrency limits; validation is in progress.

The aggregate fix passes 333 focused tests and eight boundary checks. A real
child and repeated parent reads reproduce refusal at the old ceiling and
success/reap at the new ceiling; structural overflow still refuses. The fresh
helper-only development deployment returns HTTP200 supported/rootless through
real Caddy, with configuration permission only and no helper error. This proves
the fix against the unchanged API image, not final current-source acceptance;
see `evidence/rootless-budget-fix-get.log`. Its services stopped normally and
the development VM powered off with disk/evidence retained.

Current-source wheel `f35dd55818e605f8fd406bf2971314d495baa835a22978d4e2de36a1d770e527`
and image `590b1a60af055569e2eda36faf9e2d134f1ed64834461ef6dcb0bd08b4334f1f`
build/audit pass: all 108 package and six UI files match; actual pinned UBI 10
micro ancestry and absent Node/pnpm/uv are checked. Artifacts are retained at
`/var/tmp/web-006-budget-fixed-dev-fgroli0q/`. Strict gate attempts one and two
stopped at test-only Ruff/type errors; both are corrected. Gate three is running
with 1,361 non-bookkeeping source files checked for drift. All four acceptance
cases and current-source installed functional gates remain pending.

Current strict gate three passes in 1,397.506 seconds:
`historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`, 7,806 Python tests,
52 documented opt-in deselections, strict frontend/historical frontend checks, locked
wheel installations and the real API React read fixture. All 1,361 checked
non-bookkeeping file hashes/modes stayed unchanged; snapshot
`608b20539218d081c6dacc3056e7707cd5bf7c1e19242cbb98b07cceee0c9044`.
Actual log/result: development workspace
`evidence/current-strict-gate-v3{.log,-result.json}`.

The clean acceptance installation is at
`/var/tmp/web-006-acceptance-guest-3eulcblc/`: current native0.2.2 and
rootless0.2.3 use the audited current-source artifacts. Before any application
setup, its test marker was provisioned as
`web-006-source27-4c21ae3eba1f4c68affc66fc8af48e29`; the initial cloud/QEMU
acceptance name, seed and original marker bytes remain retained explicitly.
Native installation, real loopback NFS/PKI, helper provisioning, both authority
proposals and trusted browser-image build pass. No required functional outcome
is inferred from this setup. Ordinary browser and dedicated isolation/fault
acceptance remain pending.

Current native ordinary functional acceptance passes in 254.802 seconds,
all four modes across Chromium/Firefox/WebKit, 33 host assertions and no
required skip or internal retry. `SUMMARY.json` is
`c90444c1178d952100f7fa4ca0b9f5eb57036dfd102f7b3a8295994dc1a9ea3f`
(384,229 bytes), under the clean guest's
`.scratch/web-host-fixture-native-current2/`. Original service/process/container
and endpoint drain checks pass; its Basic inode is preserved. The first native
attempt failed before browser creation on an unsupported fixture-only
`--stop-timeout=-1`; its failed proof is retained, and the separate explicit
indefinite normal-stop behavior is unchanged.

The first rootless ordinary run remains failed (845.265 seconds): its worker
took 52.751 seconds, exceeding the fixture's 45-second manager-start wait.
The early stop encountered a Caddy container still being created. Recovery
verified its original CID/image/role, normally stopped that exact container,
then released only the deliberately held stop wrapper through its original
pidfd after the executor was already exited/PID0. Independent checks establish
all role MainPIDs0 and no running containers. One remaining stopped original
CID was retired without force; only the six original creation IDs were removed
after a synchronized opaque backup, with credential inodes retained. No failed
outcome was promoted. A fresh rootless run is active with the manager-start
wait aligned to the existing 300-second unit allowance. Application code and
the green source gate remain unchanged; all four final case statuses still
await the remaining rootless and dedicated acceptance.

The second rootless run passed all four browser modes and all original three
container wait/absence checks, but its final ownership check failed because
the fixture's empty baseline incorrectly included the pre-existing user manager,
PAM helper, engine pause and two session-bus processes as application children.
Those five processes were left alive. After verified application quiescence,
their exact PID/start pairs were captured in the existing control baseline;
the original failed result was retained and its six test-secret IDs retired
after a durable opaque backup.

Current rootless ordinary acceptance then passes in 271.252 seconds, with all
four modes/three browsers and complete normal process/cgroup/container/endpoint
closure. `SUMMARY.json` is
`89f031107610e7f1f455a60f11ef61cd23fdc82d1f267701898604dc8ae55d71`
(400,494 bytes), under `.scratch/web-host-fixture-rootless-current3/` in the
clean guest. There are no required skips or internal retries. Its six original
test-secret IDs were retired after synchronized opaque backup; credential inodes
were retained and all five infrastructure processes remain alive. The dedicated
rootless fault/MAC/alias/namespace/attachment/lifecycle cohort is now running;
the corresponding native cohort remains required. No case is marked complete
from ordinary browser evidence alone.

The first current dedicated rootless cohort (`1f007b3171db414bb55295d2c47d6718`)
failed in 209.104 seconds in the private test worker before READY: its context
validator rejected a genuine `container_file_t:s0:c175,c591` MCS label. The three
unsafe-policy/release/deployment fault transitions and forged-header denial had
completed. This is a fixture failure, not accepted isolation evidence. The
original result remains false; normal application/probe-unit drain, unchanged
mount tables and all five infrastructure process identities pass. The six
original test-secret IDs were retired after synchronized opaque backup, with
credential inodes preserved. Only the private test parser is being corrected;
the green application source and security policy remain unchanged. Logs:
`/var/tmp/web-006-acceptance-guest-3eulcblc/evidence/rootless-dedicated*`.

The second dedicated rootless cohort (`1b9ac8f06bce41feaf481f9a3fadaaf6`)
completed all three real isolation phases and their negative operations, then
failed the fixture's redundant stop assertion after the transient probe unit
had already exited successfully and been collected (stop5, MainPID0/inactive,
original worker gone, mount tables unchanged). Application drain and exact-ID
retirement pass. Retained MAC analysis is incomplete: millisecond kernel audit
timestamps precede precise userspace timestamps, and consecutive same-inode
spellings share a millisecond. The next measurement uses the kernel coarse
clock and spaces probes so each denial has one unambiguous event. Prior false
outcomes remain intact; application source and confinement are unchanged.

Current dedicated rootless acceptance passes in 60.886 seconds, generation
`0e0cb5bb499642daa2536c703a4847f0`: root/account/engine phases complete,
all105 actual file/attachment denials have unique enforcing AVC/SYSCALL joins,
valid-MNT-FD typed/zero setns and AF_INET refusals pass, and original process,
mount, input and six-secret lifecycle closure passes. Protected RESULT is
`e82bc83fcafb49cf1538f26424734ce4f5db617a979e6a87603ce1627075d19f`
(137,584 bytes), retained also in host `evidence/rootless-dedicated3-RESULT.json`.
The coarse-clock measurement and20ms separation resolve audit ambiguity without
changing denial/classification requirements or application security policy.

The first native dedicated run failed in192.035 seconds before probe READY:
the fixture unconditionally required an extra Caddy-UID982 helper phase even
though the actual delivered TLS credential is0:0/0440 and admits only the root
DAC phase. Caddy982 is not a helper execution phase. The coordinator now tests
all actual native helper phases (root/account), with every DAC-eligible inode
alias retained. No file owner/mode, policy, grant or application code changed.
The failed outcome is retained; application/input/mount/baseline closure and
credential-inode preservation pass. Native counterpart acceptance is running.

### Final WEB-006 acceptance (2026-10-25)

Implemented the fixed read-only protected helper, real peer/release/policy
binding, fresh Basic action admission, GET host status, typed React status and
explicit guarded/unavailable states. All write opcodes remain refused. The
actual rootless bug was cumulative read-budget exhaustion: cardinality remains
1,024 entries and cumulative charged work is bounded separately at4,096 reads.
No capability, SELinux policy or authentication weakening accompanied that fix.

The final strict source gate `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`
passes:7,806 Python tests,52 documented opt-in deselections, three wheel profiles,
strict web/historical frontend, production UI build and real API React fixture. Actual log and
result are `/var/tmp/web-006-source26-guest-_nxq5wnb/evidence/current-strict-gate-v3*`.
All1,361 non-bookkeeping hashes/modes remained unchanged through acceptance;
final ADR acceptance-status edits and execution records are documentation only.
Wheel `f35dd55818e605f8fd406bf2971314d495baa835a22978d4e2de36a1d770e527`
and API/UI image `590b1a60af055569e2eda36faf9e2d134f1ed64834461ef6dcb0bd08b4334f1f`
match all108 package/six UI files. Actual pinned UBI10 micro ancestry and absent
Node/pnpm/uv were audited; no separate frontend runtime is shipped.

Clean guest `web-006-source27-4c21ae3eba1f4c68affc66fc8af48e29`:

- Native full browser acceptance passes254.802s, SUMMARY `c90444c1178d952100f7fa4ca0b9f5eb57036dfd102f7b3a8295994dc1a9ea3f`.
- Rootless full browser acceptance passes271.252s, SUMMARY `89f031107610e7f1f455a60f11ef61cd23fdc82d1f267701898604dc8ae55d71`.
- Both use real trusted-TLS shared Caddy, installed API/helper, production-built UI,
  Chromium/Firefox/WebKit and all four baseline/down/restarted/timeout modes;
 33 host assertions/profile, zero required skip or internal retry.
- Rootless dedicated acceptance passes60.886s, generation `0e0cb5bb499642daa2536c703a4847f0`, RESULT `e82bc83fcafb49cf1538f26424734ce4f5db617a979e6a87603ce1627075d19f`.
- Native dedicated acceptance passes42.487s, generation `ceb6f9d9877e4b5fae8c5f71ec297d84`, RESULT `37753e5316040dd860483c7b161de56452cc9047da764659c0a60ff61f6a08a5`.
- All105 rootless/57 native file-and-attachment operations have unique actual
  enforcing AVC/SYSCALL joins. All actual helper phases preserve exact namespaces,
  capabilities, filter count and masks; valid MNT-FD typed/zero setns, MNT-unshare
  and AF_INET negatives pass. No secret bytes are probed.
- Unsafe policy, selected release drift and deployment drift refuse before effects;
  forged-user headers/direct POST and sibling peers cannot gain authority.
  All original operation handles, application inputs and protected source bytes
  stay unchanged. Original process/cgroup/container/endpoint/mount closure passes;
  five pre-existing infrastructure processes remain alive. Six rootless test-secret
  IDs are retired only after synchronized opaque backup; credential inodes persist.

Host evidence is `/var/tmp/web-006-acceptance-guest-3eulcblc/evidence/`:
`native-functional2*`, `rootless-functional3*`, `rootless-dedicated3*` and
`native-dedicated2*`; private original cohorts remain in the retained guest.
The earlier context-parser, timing, collected-unit and optional-Caddy-phase
fixture failures remain false and preserved; none is presented as passing.
AUTH-08/HOST-01–03 now have actual unit/integration/functional coverage.

Final record checks pass:78 existing plan/documentation tests (9.07s),
documentation alignment207 human documents/27 helpers, and `git diff --check`.
Only acceptance-status wording in ADR151/152, INV020 and the administration
introduction changed after platform acceptance; no runtime or behavioral
contract changed. The remaining1,357 implementation/contract file hashes and
modes match the passing strict gate. These final wording/evidence edits receive
fresh documentation/record validation; unchanged application tests/builds are not
repeated solely for recording their successful outcomes.
