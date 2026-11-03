# OPS-027: Supported protected writer runtime, role mounts/startup/helper/SELinux changes, read-only defaults and reversible selection procedure

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | WEB-031 |
| Execution | `gpt-6.1-sol` / `high`; explicit task-agent setting required |

## Scope and acceptance

Supported protected writer runtime, role mounts/startup/helper/SELinux changes, read-only defaults and reversible selection procedure; qualify changed authority boundaries.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Reviewed FS-02/19/21–23, AD-09/16/17, INV-003/004/010/013/014/023 and workflow
INV-011; relevant ADR126/127/141/150/159/162/164/165 and release-format scope.
The existing accepted architecture is implemented, without a new architectural
choice or runtime dependency. INV-003, deployment/runtime/schema/security/host
and recovery contracts plus ADR165 and six prior amendment links are updated.
No archive or receipt format changes; independent deployment runtime/manifest2
have goldens and exact predecessor parser refusals. Actual installed format/profile
and Enforcing/NFS drills remain separately owned, never inferred from source.

## Validation

Finite changed-requirement/check/evidence matrix, recorded before source edits:

| Changed requirement | Smallest meaningful behavioral check | Required gate | Evidence/result |
| --- | --- | --- | --- |
| Closed mode and immutable sibling identity | Render/stage/select schema2 siblings; reject missing/unknown mode and cross-mode index/helper joins; preserve schema1 readers | scripts/check.sh | Owned source joins/goldens and exact c23abba parser refusal pass; gate19 passes9711 tests/build/three locked profiles |
| API/worker writer confinement and readonly default | Fixed command/mount tests, actual mount/guard fail-closed checks, dedicated-domain policy checks; client/Caddy without archive | scripts/check.sh | Fixed role/startup/mount/guard cases pass; candidate binary and28 current-active-boolean AV checks pass with explicit confinement limits; gate19 passes9711 tests/build/three locked profiles |
| Independent helper/process metadata authority | Exact runtime/index/mode/domain joins and guarded nfs-rw rejection; helper/observer payload and secret neverallows | scripts/check.sh | Exact independent helper sibling/mode and writer payload PID/domain source checks pass; original neverallows retained; installed enforcement remains later |
| Offline original-intent activation and companion lifecycle | Fixed selected-runtime offline command after drain/original flock; original stores/inodes and partial-state refusal; native/rootless companion mounts and labels | scripts/check.sh | Existing-only real-model/store backup, original flock/inodes, partial state and custom credential/mask/revision/native command cases pass; gate19 passes9711 tests/build/three locked profiles |
| Reversible current-boot selection/startup/rollback | Reviewed preserving procedure and existing owned installer/role fixtures; installed Enforcing/NFS proof handed to WEB-033/OPS-029 | scripts/check.sh | Preserving current-boot procedure/rollback and strict stage barrier reviewed; docs alignment passes; actual installed transition is later |

No web source is selected. Existing mandatory tests remain; the optional
instrumented functional runner is excluded. Installed production actions remain
with OPS-028/029.
Every commit requires `rtk scripts/check.sh`; web changes require `--require-web`;
release acceptance requires `--require-web --with-build`. Preserve raw failures.
Do not invoke the optional instrumented functional runner.

## Execution notes and handoff

Actual task-agent execution is `gpt-6.1-sol` / `high`, explicitly selected by
the coordinator. No model/effort escalation or further delegation.

Activated 2026-11-03 by the user's explicit end-to-end implementation instruction.
Protected deployment, controlled writable transition, selected Sync and refresh
pilots and bounded metadata backfill are authorized after the reviewed safety
prerequisites. Scope is this host/current boot with fail-closed manual startup
permitted; unattended boot acceptance remains separate.

## Scoped implementation evidence

Focused iterations1–4/7 under `.scratch/ops027-validation` use the existing
private empty read-only NAS shadow as UID1000/nice10. Their inherited filenames
contain `gate` and wrapper scope says default gate, but the actual retained inner
argv is focused pytest, not scripts/check.sh. Iteration4 passes855 and iteration7
passes864 checks; earlier failures remain in full logs. These scoped iterations
precede the normal full gates recorded below.
Original companion-path metadata omission and incomplete peer fixture were fixed.
The actual locked image/user mapping is981:981; no mapping change is introduced.

Owned offline policy copy uses `/var/tmp/hfcache-ops027-policy1`, exact module
`400 hfcache_host_helper`, no outward symlinks, UID1000 and `-N` in the private NAS
shadow. First failed attempt establishes semodule's `-p` prefix semantics; second
reaches the target policy but expand-check1 reports40 conflicts, including five
new writer constraints matching existing generic domain-map/container-search
conflict patterns. This is not a strict neverallow pass. Actual host config has
expand-check0; it is unchanged. Both failures/full payloads remain. Original host
policy/store/root metadata+contents and kernel SHA
`7c673c5f5fe3a0befc1217cd744440428004e66b28bc4321a39b0b52be26f27c`, Enforcing1,
remain exact after both attempts. The later baseline/binary/active-boolean evidence below narrows this source
qualification; actual owned Enforcing role proof remains WEB-033, actual NFS
writer proof OPS-029. No policy was installed
or reloaded on the host.

The concrete capacity blocker (root833,114,112B/home114,315,264B) was resolved by
root preserving complete focused3/4/7 payloads before fd-safe exact retirement.
The unchanged1.1GB gate floor remains. `/var/tmp/hfcache-ops027-focused{3,4,7}-retirement-evidence/`
retains full archives/manifests/log bindings and fresh338-process all-UID no-owner
proofs. Final receipt SHAs respectively `58adb8c5ac7f9724cd0f0523b02f83796aacb68158b896e3f9c6c34fdce3ec8d`,
`64c591181591d1b169b8a00e1924c0a0e5ef333539799856b957060b970bb799`,
`f206b09a7b728c64b8a43dd6325a44b51385840fb3829664cd4028709ac4f353`.
No historical cache/fixture or production object was removed. Later narrowed
checks use explicit owned `/var/tmp/.o27s` (38pass/3 reason-assertion failures,
retained) and `.o27t` (55pass/618deselected); generic error text is correctly
separated from the asserted `facts-unavailable` reason. Static typing required a
real inspection instance in that unit fixture; no product behavior changed.

Exact retained baseline CIL under expand-check1 fails33 clauses (20 local,
13 distribution); initial candidate fails40 (25/15). Five new writer constraints
match inherited map/search conflicts, while two new proc-target conflicts identify
missing stock exception markers subsequently retained in the stable attribute
closure. No strict-neverallow pass is claimed. The final current CIL
`0a5e65541c070d9e4affb08be2c25de072d994523214c01ffb5bd7c0df7b31c1`
compiles as UID1000 with exact copied host config SHA
`8ba0df9a109dd136f1e8827343806ced9a0652c670c2572b4dd8642c67c27734`
(expand-check0), binary SHA
`6f26d3ccaf46858aa2835ae6bfc466d7f236d294a8c6e5c8320c51cf7335b750`.
Full compile log SHA `df36104511fd3873c715d46fe00a0448bf6da361f6a6d21364f08f105d6789a3`;
all output targets stay inside the exclusive owned root. Unprivileged copied-root
ownership warnings remain in the successful log, not suppressed.

Existing setools/selinux bindings provide28 finite direct effective-AV checks,
SHA `a4d3601e1e27325ce63fb103786de7437932a6489a982514030c6e2a3a7f2334`.
Every relevant conditional uses fresh `security_get_boolean_active` values and
rechecks them at end: domain_can_mmap_files=false, virt_use_nfs=true,
container_use_devices=false, domain_can_write_kmsg=false. Helper/observer payload
rights remain denied; generic container archive vectors are unchanged. Writer
image/state/lock/secret/network/archive prerequisites pass. Writer proc_kcore/
proc_kmsg have only getattr/mounton versus stock's additional open/read/ioctl/lock;
kmsg_device vectors are both empty. These markers add no target rights beyond
stock. Original host store/root metadata+content/kernel7c673c5f/enforce1 remain
unchanged after compilation and after AV evaluation. This proves TE compatibility
at measured booleans, not MCS/DAC/namespace/seccomp/mount/workload enforcement.
The existing true NFS boolean already grants broader stock NFS permissions:
no generic grant/boolean changes or sole-systemwide-writer/effective symlink-rename
restriction claim follows. Actual installed qualification remains WEB-033/OPS-029.

Exact c23abba predecessor runtime/installer parsers preserve legacy schema1 and
refuse both schema2 modes without rewriting bytes. Protected descriptor/service
metadata is explicitly modeled; this is source-reader proof, not installed
rollback. `.scratch/ops027-validation/predecessor/result.json` binds exact source
hashes `01418c11...` / `c81b0664...`.

## Tooling incident and bounded correction

One edit heredoc used an inner delimiter matching its outer delimiter. Python
failed to parse before writing either intended source file; the login-UID1000
shell then attempted restorecon on the fixed protected companion and received
Permission denied before access, followed by a nonexistent executable path.
The complete tool input/output remains in the conversation transcript; exact
stdout is retained at `.scratch/ops027-validation/native-edit-error-stdout.txt`.
No privilege escalation or permission/label workaround followed. Root's bounded
read-only check proves all six original lock metadata/labels exactly unchanged,
companion absent, kernel7c673c5f/enforce1 unchanged. Fsynced receipt
`/var/tmp/hfcache-ops027-edit-error-check/read-only-check.json` SHA
`071f32d4c8244c6adc503a27c5171142c108ebbda0196c0f7665f892cacc88a6`.
Subsequent edits use distinct outer delimiters; shell syntax checks pass.

## Final native isolation qualification

Source review closes the native custom-source/runtime gap: actual effective
verifier masks reuse the existing canonical grammar; optional standard masks
cover absent standard stores and legacy cached tokens. Real Config/ServerConfig
models require the fixed native archive/config/control-store layout and covered
REST/MCP/Basic/TLS private-key files. Fixed packaged bytes, cached ExecStart and
credential delivery plus no API drop-ins exclude unmodelled Hub sources. Exact
config/unit/mask/account revisions are repeated before state effects and before
companion publication. Private runtime BindPaths hides original archive/API/
worker lock/socket sources, with worker instance/host-helper paths masked. Only
original store locks remain accessible to the real validator. Python uses -I/-B,
closed stdin and fixed token-free private-runtime HF_HOME/Xet plus offline flags.
Publication preserves the new inode without replacing any destination, fsyncs
both parents and verifies independently provisioned label/owner/mode.

Native source cases cover custom covered/uncovered credentials, absent optional
stores, unsupported unit/cached credentials/archive-root layouts, changed exact
revision, fixed private runtime/command/environment, original archive/store-lock
retention and preserved partial activation. All17 focused cases pass before the
final fixed-HF_HOME/legacy-cache addition; the two directly affected cases pass separately (2pass/686deselected). Earlier native fixture/argument failures remain in full
logs. Source mask/bind/argv checks establish definitions, not actual native
transient enforcement; WEB-033 must prove that in an owned installed fixture.

## Remaining installed clauses

- WEB-033: actual native/rootless preparation/drain/backups, companion ownership/
  label/restart/no-recreation, actual private runtime/secret masks/offline workers,
  Enforcing writer/MCS/helper/observer positive and negative workloads, original
  intent workflows and old/current format/rollback readers.
- OPS-028: protected guarded sibling selection/helper policy/receipt under actual
  drain/NFS-ro, existing Basic/UI key recovery without rewriting unknown history.
- OPS-029: actual nfs_t writable identity/ownership/capacity/reserve/preflight,
  current-boot original-lock/mount/guard transition and authorized pilots/backfill.
  No source proof or copied policy binary establishes these clauses or unattended
  boot. Preserve all original state, permissions, artifacts and deliberate guard
  setting until the separately reviewed later steps.

## Completion evidence

Mandatory full default gate19 passes after the preserved gate10 failure. It uses
`.scratch/ops027-validation/run-gate2-shadow.py ops027-gate19`, frozen
name/content manifest, loginUID1000/nice10, private empty read-only NAS shadow,
short owned TMP and unchanged1.1GB startup floor. Scoped
source checks are55pass/618deselected, native17pass/671deselected and final
cache/environment2pass/686deselected. Format938 files, lint, types0 errors and
alignment216 human documents/29 helpers pass. No web source/wire is changed;
strict browser proof is reused from WEB-032, with installed acceptance still
separate. All1281 frozen names/hashes remain unchanged through normal completion.
Source and unit tests alone do not establish installed acceptance.

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


### First normal frozen gate result

Gate10 completes normally with11failed/9700passed/52deselected in1308.714s,
inner log SHA `f1b16e9d04b9e40206b094f14f7961e53ad0219c96485efdf714a8c1047cd161`,
shadow SHA `ea067ad1c7d78677b1a696bfc8206435bfc1a3242b6d298018b3bee55c96fdf5`.
All1281 frozen names/hashes remain exact; no input changed while it ran. The
normal gate stops at failed pytest, so build/install phases have not passed yet.
Full log and failed TMP payload remain preserved. The complete summary identifies
three fixture assumptions: one protected-stage test still asserts zero manager
reads, four client-boundary tests supply only app_image, and six mandatory web
artifact cases omit runtime.schema_version. The stage assertion is tightened to
its exact two readonly observations; the other fixtures supply complete schema1
profiles. Original handle-forwarding, artifact and negative-damage assertions
remain unchanged. This is mandatory unit-fixture repair, never an invocation of
the optional instrumented functional runner. The exact11 repaired regressions pass in5.17s, shadow7.0557s SHA
`ebd62d2b0d58ad07802317eda8ce415f5a6f2d5b0bc3f24cf3408e1a3253a229`.
Format/lint for the three repaired files and alignment216/29 pass. Root preserves
the complete failed gate payload (164940 entries) before fd-safe retirement;
archive SHA `e581991cbda8cfae23ea7e9bd23ee49348819dd7b60301b9a49062c91712093e`,
full manifest SHA `d09d70d71dfac2738e018c5adc76daab81beae0896a1392f6187c2ec738e1bc4`,
receipt SHA `11a6bcacbafb9a9ae21d57b27673b746504d92da1fda49d338447a871032b776`
in `/var/tmp/hfcache-ops027-gate10-retirement-evidence/`. Source/log/policy
evidence remains retained. Capacity is restored; gate19 retries with the same
1.1GB floor and a fresh short task TMP, without extra broad focused runs.


### Passing normal frozen gate and source completion

Gate19 exits0:9711 passed/52 deselected in1264.92s; complete default gate1313.549s,
package source/wheel build and locked base/server/server-plus-MCP installation,
import/help/version checks pass. Full log SHA
`b6bf8d20a5ca987f1aa73144eca2641faaee621ab9bd65ca72a9c9617fe2f39f`,
shadow1314.326s SHA
`5badeaeaf7747d3d689f453ddb68b7ce927223273f5c8fab9ccbafbe8e14955c`.
All1281 frozen input names/hashes remain exact; no source edit occurred during
normal execution. Successful owned TMP `/var/tmp/.g27s` is retained when the gate exits;
the coordinator separately owns exact evidence-preserving retirement. No web source/wire changes; the default gate explicitly omits web UI
acceptance. WEB-032 strict browser evidence retains its original unchanged-code
scope; direct installed changed-boundary proof remains WEB-033.

Only task/progress/plan/current Markdown completion metadata changes after this
green gate. Focused documentation checks and alignment qualify that final delta.
OPS-027 source/profile/procedure acceptance is complete; no production service,
policy/kernel, mount, permission, lock/store, credential, artifact or writer state
was changed. WEB-033 is next. The finite installed clauses above remain open in
their owning tasks, including strict effective confinement and actual NFS pilots.


Completion-only Markdown passes69 focused documentation checks in9.02s and
standalone alignment216 human documents/29 helpers. Comparison to the gate19
snapshot confirms only the task/progress/dated-plan/current completion records
changed after the green frozen technical inputs; all implementation and contract
bytes remain gate-qualified. The staged diff passes whitespace validation.


Root retires only successful gate19 TMP `.g27s` (dev64768/inode4847844) after
matching full164940-entry/163584-inode inventories and a fresh all-UID471-process
zero-reference proof. Fsynced receipt
`/var/tmp/hfcache-ops027-gate19-retirement/gate-temp-retirement-result.json` SHA
`76c9858a7136e80cd366b345cbc44864440b6bdca007d427d2af099f026437ca`,
manifest gzip SHA `7963ae5af1828120bc0b4ef377527c56e0f23c97bc1278569da3bbbb2546b187`.
Source/log/report/failed-payload evidence remains. Root free1177649152B and
home90341376B; unchanged1.1GB floor restored without unrelated cleanup.
